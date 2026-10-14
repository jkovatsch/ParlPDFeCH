//! Native tests of the core functions.
//!
//! The record tests read the three sample records from the folder that the
//! environment variable PARLPDFECH_TEST_RECORDS names (one sub-folder for each
//! document id, with <doc>.gesamt.trig, manifest.json and validation.json).
//! Without the variable they print a message and pass with no check.

use std::path::{Path, PathBuf};

use parlpdfech_rdfcheck::core::{examples, Checker};
use serde_json::Value;

const DOCS: [&str; 3] = ["26171", "879163", "714840"];

fn clock() -> f64 {
    use std::sync::OnceLock;
    use std::time::Instant;
    static START: OnceLock<Instant> = OnceLock::new();
    START.get_or_init(Instant::now).elapsed().as_secs_f64() * 1000.0
}

fn records() -> Option<PathBuf> {
    match std::env::var("PARLPDFECH_TEST_RECORDS") {
        Ok(v) if !v.is_empty() => Some(PathBuf::from(v)),
        _ => {
            eprintln!("SKIPPED: PARLPDFECH_TEST_RECORDS is not set; no sample record was read.");
            None
        }
    }
}

fn read(root: &Path, doc: &str, name: &str) -> Vec<u8> {
    let path = root.join(doc).join(name);
    std::fs::read(&path).unwrap_or_else(|e| panic!("cannot read {}: {e}", path.display()))
}

fn json(root: &Path, doc: &str, name: &str) -> Value {
    serde_json::from_slice(&read(root, doc, name)).expect("JSON")
}

const SMALL: &str = r#"@prefix plb: <https://schema.parlpdfech.example/labels/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
<urn:test:g1> {
  <urn:test:l1> a plb:LabelAssertion ; rdf:object "title" ; plb:labelSource plb:rule ;
      plb:probability 0.9 ; plb:valueStatus plb:certain ; plb:inSample true .
  <urn:test:l2> a plb:LabelAssertion ; rdf:object "none" ; plb:labelSource plb:export .
}
<urn:test:g2> {
  <urn:test:b1> a plb:PdfBlock ; plb:position 1 .
  <urn:test:l1> a plb:LabelAssertion .
}
"#;

#[test]
fn small_file_summary() {
    let c = Checker::load(SMALL.as_bytes()).expect("parse");
    let s = c.summary().expect("summary");
    assert_eq!(s.statements, 12);
    // <urn:test:l1> a plb:LabelAssertion is in two graphs: 12 statements, 11 distinct triples.
    assert_eq!(s.triples_distinct, 11);
    assert_eq!(s.subjects_distinct, 3);
    assert_eq!(s.graphs.len(), 2);
    assert_eq!(s.graphs[0].iri.as_deref(), Some("urn:test:g1"));
    assert_eq!(s.graphs[0].statements, 9);
    assert_eq!(s.graphs[1].statements, 3);
    assert_eq!(s.label_assertions, 2);
    assert_eq!(s.labels_with_probability, 1);
    assert_eq!(s.by_value_status.get("certain"), Some(&1));
    assert_eq!(s.by_value_status.get("none"), Some(&1));
    assert_eq!(s.by_source.get("rule"), Some(&1));
    assert_eq!(s.by_source.get("export"), Some(&1));
    assert_eq!(s.by_in_sample.get("true"), Some(&1));
    assert_eq!(s.blocks, 1);
}

#[test]
fn parse_error_has_line_and_column() {
    let bad = "@prefix ex: <urn:ex:> .\n<urn:g> {\n  ex:a ex:b ;;; \"x\" \"y\" .\n}\n";
    let e = Checker::load(bad.as_bytes()).err().expect("an error");
    assert_eq!(e.code, "parse");
    assert_eq!(e.line, Some(3), "{e:?}");
    assert!(e.column.is_some(), "{e:?}");
    assert!(!e.message.is_empty());
}

#[test]
fn compare_reports_equal_and_different() {
    let c = Checker::load(SMALL.as_bytes()).expect("parse");
    let manifest = r#"{
      "rdf": {"named_graphs": {"a": "urn:test:g1", "b": "urn:test:g2"},
              "triples": {"a": 9, "b": 4, "union": 11}},
      "counts": {"label_assertions": 2, "label_assertions_by_source": {"rule": 1, "copy": 1},
                 "certain_labels": 1, "unsure_labels": 0, "blocks": 1}
    }"#;
    let rows = c.compare(manifest).expect("compare");
    let get = |n: &str| {
        rows.iter()
            .find(|r| r.name == n)
            .unwrap_or_else(|| panic!("row {n}"))
    };
    assert!(get("rdf.triples.a").equal);
    assert!(!get("rdf.triples.b").equal);
    assert_eq!(get("rdf.triples.b").in_file, Some(3));
    assert_eq!(get("rdf.triples.b").in_manifest, Some(4));
    assert!(get("rdf.triples.union").equal);
    assert!(get("counts.label_assertions").equal);
    assert!(get("counts.label_assertions_by_source.rule").equal);
    // in the manifest only: file count 0
    assert!(!get("counts.label_assertions_by_source.copy").equal);
    assert_eq!(
        get("counts.label_assertions_by_source.copy").in_file,
        Some(0)
    );
    // in the file only: no manifest count
    assert!(!get("counts.label_assertions_by_source.export").equal);
    assert_eq!(
        get("counts.label_assertions_by_source.export").in_manifest,
        None
    );
    assert!(get("counts.certain_labels").equal);
    assert!(get("counts.unsure_labels").equal);
    assert!(get("counts.blocks").equal);
    assert!(c.compare("{ not json").is_err());
    // a manifest with no count gives no row
    assert!(c.compare("{}").expect("compare").is_empty());
}

#[test]
fn query_forms() {
    let c = Checker::load(SMALL.as_bytes()).expect("parse");
    // prefixes of the files are known with no PREFIX line; the default graph is the union
    let r = c
        .query(
            "SELECT ?l WHERE { ?l a plb:LabelAssertion } ORDER BY ?l",
            100,
            5000.0,
            &clock,
        )
        .expect("select");
    assert_eq!(r.kind, "select");
    assert_eq!(r.variables, vec!["l"]);
    // The union does not remove a triple that is in two named graphs: l1 comes two times.
    assert_eq!(r.rows.len(), 3);
    assert!(!r.truncated && !r.timed_out);
    let d = c
        .query(
            "SELECT DISTINCT ?l WHERE { ?l a plb:LabelAssertion }",
            100,
            5000.0,
            &clock,
        )
        .expect("select distinct");
    assert_eq!(d.rows.len(), 2);
    let first = r.rows[0][0].as_ref().expect("bound");
    assert_eq!(first.kind, "iri");
    assert_eq!(first.value, "urn:test:l1");

    let r = c
        .query(
            "ASK { ?l plb:valueStatus plb:certain }",
            100,
            5000.0,
            &clock,
        )
        .expect("ask");
    assert_eq!(r.kind, "ask");
    assert_eq!(r.boolean, Some(true));

    // GRAPH still selects one named graph
    let r = c
        .query(
            "SELECT ?s WHERE { GRAPH <urn:test:g2> { ?s ?p ?o } }",
            100,
            5000.0,
            &clock,
        )
        .expect("graph");
    assert_eq!(r.rows.len(), 3);

    // row limit
    let r = c
        .query("SELECT * WHERE { ?s ?p ?o }", 4, 5000.0, &clock)
        .expect("limit");
    assert_eq!(r.rows.len(), 4);
    assert!(r.truncated);
    // exactly as many rows as the limit: not truncated
    let r = c
        .query("SELECT * WHERE { ?s ?p ?o }", 12, 5000.0, &clock)
        .expect("limit");
    assert_eq!(r.rows.len(), 12);
    assert!(!r.truncated);

    // time limit: a clock that jumps 10 s at each call stops the output after the first row
    let ticks = std::cell::Cell::new(0.0);
    let fast = || {
        ticks.set(ticks.get() + 10_000.0);
        ticks.get()
    };
    let r = c
        .query("SELECT * WHERE { ?s ?p ?o }", 100, 5000.0, &fast)
        .expect("time");
    assert!(r.timed_out);
    assert_eq!(r.rows.len(), 1);

    let e = c
        .query("SELECT ?s WHERE { ?s ?p }", 10, 5000.0, &clock)
        .expect_err("syntax");
    assert_eq!(e.code, "syntax");
    assert!(!e.message.is_empty());

    for update in [
        "INSERT DATA { <urn:a> <urn:b> <urn:c> }",
        "DELETE WHERE { ?s ?p ?o }",
        "CLEAR ALL",
        "DROP GRAPH <urn:test:g1>",
    ] {
        let e = c.query(update, 10, 5000.0, &clock).expect_err("refused");
        assert_eq!(e.code, "update_refused", "{update}");
    }
    for form in [
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
        "DESCRIBE <urn:test:l1>",
    ] {
        let e = c.query(form, 10, 5000.0, &clock).expect_err("refused");
        assert_eq!(e.code, "form_refused", "{form}");
    }
    // nothing changed
    assert_eq!(c.summary().expect("summary").statements, 12);

    // a SERVICE call to another host does not run
    let r = c.query(
        "SELECT * WHERE { SERVICE <https://example.org/sparql> { ?s ?p ?o } }",
        10,
        5000.0,
        &clock,
    );
    assert_eq!(r.expect_err("no service").code, "evaluation");
}

#[test]
fn examples_are_select_queries() {
    let c = Checker::load(SMALL.as_bytes()).expect("parse");
    let list = examples();
    assert!((3..=5).contains(&list.len()));
    for ex in list {
        assert!(!ex.title_en.is_empty() && !ex.title_de.is_empty());
        let r = c
            .query(ex.sparql, 100, 5000.0, &clock)
            .unwrap_or_else(|e| panic!("{}: {e:?}", ex.id));
        assert_eq!(r.kind, "select");
    }
}

#[test]
fn sample_records_agree_with_manifest_and_validation() {
    let Some(root) = records() else { return };
    for doc in DOCS {
        let trig = read(&root, doc, &format!("{doc}.gesamt.trig"));
        let c = Checker::load(&trig).unwrap_or_else(|e| panic!("{doc}: {e:?}"));
        let s = c.summary().expect("summary");
        let manifest = json(&root, doc, "manifest.json");
        let validation = json(&root, doc, "validation.json");

        // triples count of validation.json (C2_parse, written with rdflib)
        let expected = validation["C2_parse"]["results"]
            .as_array()
            .expect("C2_parse.results")
            .iter()
            .find(|r| r["file"] == format!("{doc}.gesamt.trig"))
            .and_then(|r| r["triples"].as_u64())
            .expect("triples of the TriG file");
        assert_eq!(
            s.triples_distinct as u64, expected,
            "{doc}: triples_distinct"
        );
        assert_eq!(s.statements as u64, expected, "{doc}: statements");

        // the named graphs are the 4 graphs of the manifest
        let mut from_manifest: Vec<String> = manifest["named_graphs"]
            .as_object()
            .expect("named_graphs")
            .values()
            .map(|v| v.as_str().expect("IRI").to_string())
            .collect();
        from_manifest.sort();
        let from_file: Vec<String> = s
            .graphs
            .iter()
            .map(|g| g.iri.clone().expect("named"))
            .collect();
        assert_eq!(from_file, from_manifest, "{doc}: named graphs");

        // each count that the comparison knows is equal
        let rows = c.compare(&manifest.to_string()).expect("compare");
        for row in &rows {
            assert!(row.equal, "{doc}: {row:?}");
        }
        for name in [
            "rdf.triples.ech-0295",
            "rdf.triples.provenance",
            "rdf.triples.atoms",
            "rdf.triples.labels",
            "rdf.triples.union",
            "counts.label_assertions",
            "counts.label_assertions_by_source.apertus_head",
            "counts.certain_labels",
            "counts.unsure_labels",
            "counts.blocks",
        ] {
            // a record of the mode rules has no label of the source apertus_head
            if name == "counts.label_assertions_by_source.apertus_head"
                && manifest["counts"]["label_assertions_by_source"]
                    .get("apertus_head")
                    .is_none()
            {
                continue;
            }
            assert!(
                rows.iter().any(|r| r.name == name),
                "{doc}: row {name} is absent"
            );
        }
        let status_sum: usize = s.by_value_status.values().sum();
        assert_eq!(status_sum, s.label_assertions, "{doc}: status groups");
        let source_sum: usize = s.by_source.values().sum();
        assert_eq!(source_sum, s.label_assertions, "{doc}: source groups");
        assert!(
            !s.by_source.contains_key("none"),
            "{doc}: a label has no source"
        );
        eprintln!(
            "{doc}: statements {} subjects {} labels {} (with probability {}) status {:?} source {:?} in_sample {:?} blocks {} atoms {} rows compared {}",
            s.statements, s.subjects_distinct, s.label_assertions, s.labels_with_probability,
            s.by_value_status, s.by_source, s.by_in_sample, s.blocks, s.atoms, rows.len()
        );
    }
}

#[test]
fn examples_give_rows_on_the_sample_records() {
    let Some(root) = records() else { return };
    for doc in DOCS {
        let trig = read(&root, doc, &format!("{doc}.gesamt.trig"));
        let c = Checker::load(&trig).expect("parse");
        let s = c.summary().expect("summary");
        for ex in examples() {
            let r = c
                .query(ex.sparql, 500, 5000.0, &clock)
                .unwrap_or_else(|e| panic!("{doc} {}: {e:?}", ex.id));
            assert!(!r.rows.is_empty(), "{doc}: example {} gave no row", ex.id);
            assert!(!r.truncated && !r.timed_out, "{doc}: example {}", ex.id);
            match ex.id {
                "labels" => assert_eq!(r.rows.len(), s.label_assertions, "{doc}: labels"),
                "unsure" => assert_eq!(
                    r.rows.len(),
                    *s.by_value_status.get("unsure").unwrap_or(&0),
                    "{doc}: unsure"
                ),
                // one row for each text line (atom) of a block that has a label
                "block_text" => assert_eq!(r.rows.len(), s.atoms, "{doc}: block_text"),
                _ => {}
            }
            eprintln!(
                "{doc}: example {} rows {} in {:.1} ms",
                ex.id,
                r.rows.len(),
                r.elapsed_ms
            );
        }
    }
}

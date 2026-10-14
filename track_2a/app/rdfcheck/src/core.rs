//! Core of the RDF check. No browser type is used here, so the same code
//! runs in the native tests and in WebAssembly.

use std::collections::{BTreeMap, HashMap, HashSet};

use oxigraph::io::{RdfFormat, RdfParser};
use oxigraph::model::{GraphName, NamedOrBlankNode, Quad, Term};
use oxigraph::sparql::{QueryResults, SparqlEvaluator};
use oxigraph::store::Store;
use serde::Serialize;
use serde_json::Value;
use spargebra::{Query, SparqlParser};

/// Namespace of the label vocabulary (prefix `plb` in src/m10_label_schema.yaml).
pub const PLB: &str = "https://schema.parlpdfech.example/labels/";
/// Namespace of the profile vocabulary (prefix `ppx`).
pub const PPX: &str = "https://schema.parlpdfech.example/profile/";
const RDF_TYPE: &str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";

/// The prefixes of the TriG files. A query can use them with no PREFIX line.
pub const PREFIXES: [(&str, &str); 8] = [
    ("aff", "https://ch.paf.link/schema/affairs/"),
    ("mcm", "https://ld.ech.ch/schema/0292/meta-common/"),
    ("plb", PLB),
    ("ppx", PPX),
    ("prov", "http://www.w3.org/ns/prov#"),
    ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    ("skos", "http://www.w3.org/2004/02/skos/core#"),
    ("xsd", "http://www.w3.org/2001/XMLSchema#"),
];

/// Default limit of result rows.
pub const DEFAULT_MAX_ROWS: usize = 500;
/// Default time limit of one query in milliseconds.
pub const DEFAULT_MAX_MS: f64 = 5000.0;

/// A syntax error of the TriG file. Line and column start at 1.
#[derive(Debug, Clone, Serialize)]
pub struct ParseError {
    pub code: &'static str,
    pub message: String,
    pub line: Option<u64>,
    pub column: Option<u64>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct GraphCount {
    /// IRI of the named graph; `None` is the default graph.
    pub iri: Option<String>,
    pub statements: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct Summary {
    /// Statements (quads) in the file.
    pub statements: usize,
    /// Distinct triples when the graph name is ignored (the "union" count).
    pub triples_distinct: usize,
    pub subjects_distinct: usize,
    pub graphs: Vec<GraphCount>,
    /// Subjects with the type plb:LabelAssertion.
    pub label_assertions: usize,
    /// Label assertions that have plb:probability.
    pub labels_with_probability: usize,
    /// Count by plb:valueStatus; the key `none` holds the labels with no status.
    pub by_value_status: BTreeMap<String, usize>,
    /// Count by plb:labelSource.
    pub by_source: BTreeMap<String, usize>,
    /// Count by plb:labelKind.
    pub by_kind: BTreeMap<String, usize>,
    /// Count by plb:inSample (`true`, `false`); the key `none` holds the labels with no flag.
    pub by_in_sample: BTreeMap<String, usize>,
    /// Subjects with the type plb:PdfBlock.
    pub blocks: usize,
    /// Subjects with the type plb:PdfAtom.
    pub atoms: usize,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct CompareRow {
    pub name: String,
    pub in_file: Option<i64>,
    pub in_manifest: Option<i64>,
    pub equal: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct Example {
    pub id: &'static str,
    pub title_en: &'static str,
    pub title_de: &'static str,
    pub sparql: &'static str,
}

#[derive(Debug, Clone, Serialize)]
pub struct Cell {
    /// `iri`, `literal` or `bnode`.
    #[serde(rename = "type")]
    pub kind: &'static str,
    pub value: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub datatype: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lang: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct QueryOutput {
    /// `select` or `ask`.
    pub kind: &'static str,
    pub variables: Vec<String>,
    pub rows: Vec<Vec<Option<Cell>>>,
    /// Answer of an ASK query.
    pub boolean: Option<bool>,
    /// True if the row limit stopped the output and one more row exists.
    pub truncated: bool,
    /// True if the time limit stopped the output.
    pub timed_out: bool,
    pub max_rows: usize,
    pub max_ms: f64,
    pub elapsed_ms: f64,
}

/// Error of a query. `code` is one of `syntax`, `update_refused`,
/// `form_refused`, `evaluation`.
#[derive(Debug, Clone, Serialize)]
pub struct QueryError {
    pub code: &'static str,
    pub message: String,
}

/// The parsed file in an in-memory store.
pub struct Checker {
    store: Store,
}

fn local_name(term: &Term) -> String {
    match term {
        Term::NamedNode(n) => n
            .as_str()
            .strip_prefix(PLB)
            .unwrap_or(n.as_str())
            .to_string(),
        Term::Literal(l) => l.value().to_string(),
        other => other.to_string(),
    }
}

fn subject_key(s: &NamedOrBlankNode) -> String {
    s.to_string()
}

impl Checker {
    /// Parses TriG bytes into a new store.
    pub fn load(trig: &[u8]) -> Result<Self, ParseError> {
        let mut quads: Vec<Quad> = Vec::new();
        for item in RdfParser::from_format(RdfFormat::TriG).for_slice(trig) {
            match item {
                Ok(q) => quads.push(q),
                Err(e) => {
                    let (line, column) = match e.location() {
                        Some(range) => (Some(range.start.line + 1), Some(range.start.column + 1)),
                        None => (None, None),
                    };
                    return Err(ParseError {
                        code: "parse",
                        message: e.to_string(),
                        line,
                        column,
                    });
                }
            }
        }
        let store = Store::new().map_err(|e| ParseError {
            code: "store",
            message: e.to_string(),
            line: None,
            column: None,
        })?;
        store.extend(quads).map_err(|e| ParseError {
            code: "store",
            message: e.to_string(),
            line: None,
            column: None,
        })?;
        Ok(Self { store })
    }

    /// Counts of the file. One pass over all statements.
    pub fn summary(&self) -> Result<Summary, String> {
        let type_label = format!("{PLB}LabelAssertion");
        let type_block = format!("{PLB}PdfBlock");
        let type_atom = format!("{PLB}PdfAtom");
        let p_status = format!("{PLB}valueStatus");
        let p_source = format!("{PLB}labelSource");
        let p_kind = format!("{PLB}labelKind");
        let p_in_sample = format!("{PLB}inSample");
        let p_probability = format!("{PLB}probability");

        let mut statements = 0usize;
        let mut graphs: BTreeMap<Option<String>, usize> = BTreeMap::new();
        let mut subjects: HashSet<String> = HashSet::new();
        let mut triples: HashSet<(String, String, String)> = HashSet::new();
        let mut labels: HashSet<String> = HashSet::new();
        let mut blocks: HashSet<String> = HashSet::new();
        let mut atoms: HashSet<String> = HashSet::new();
        let mut status: HashMap<String, String> = HashMap::new();
        let mut source: HashMap<String, String> = HashMap::new();
        let mut kind: HashMap<String, String> = HashMap::new();
        let mut in_sample: HashMap<String, String> = HashMap::new();
        let mut with_probability: HashSet<String> = HashSet::new();

        for quad in self.store.iter() {
            let quad = quad.map_err(|e| e.to_string())?;
            statements += 1;
            let graph = match &quad.graph_name {
                GraphName::DefaultGraph => None,
                GraphName::NamedNode(n) => Some(n.as_str().to_string()),
                GraphName::BlankNode(b) => Some(b.to_string()),
            };
            *graphs.entry(graph).or_insert(0) += 1;
            let s = subject_key(&quad.subject);
            let p = quad.predicate.as_str();
            if p == RDF_TYPE {
                if let Term::NamedNode(t) = &quad.object {
                    let t = t.as_str();
                    if t == type_label {
                        labels.insert(s.clone());
                    } else if t == type_block {
                        blocks.insert(s.clone());
                    } else if t == type_atom {
                        atoms.insert(s.clone());
                    }
                }
            } else if p == p_status {
                status.insert(s.clone(), local_name(&quad.object));
            } else if p == p_source {
                source.insert(s.clone(), local_name(&quad.object));
            } else if p == p_kind {
                kind.insert(s.clone(), local_name(&quad.object));
            } else if p == p_in_sample {
                in_sample.insert(s.clone(), local_name(&quad.object));
            } else if p == p_probability {
                with_probability.insert(s.clone());
            }
            triples.insert((s.clone(), p.to_string(), quad.object.to_string()));
            subjects.insert(s);
        }

        let group = |map: &HashMap<String, String>| -> BTreeMap<String, usize> {
            let mut out: BTreeMap<String, usize> = BTreeMap::new();
            for label in &labels {
                let key = map
                    .get(label)
                    .cloned()
                    .unwrap_or_else(|| "none".to_string());
                *out.entry(key).or_insert(0) += 1;
            }
            out
        };

        Ok(Summary {
            statements,
            triples_distinct: triples.len(),
            subjects_distinct: subjects.len(),
            graphs: graphs
                .into_iter()
                .map(|(iri, statements)| GraphCount { iri, statements })
                .collect(),
            label_assertions: labels.len(),
            labels_with_probability: labels
                .iter()
                .filter(|l| with_probability.contains(*l))
                .count(),
            by_value_status: group(&status),
            by_source: group(&source),
            by_kind: group(&kind),
            by_in_sample: group(&in_sample),
            blocks: blocks.len(),
            atoms: atoms.len(),
        })
    }

    /// Compares the counts of the file with the counts that manifest.json holds.
    /// A count that the manifest does not hold gives no row, with one exception:
    /// a named graph or a label source that only the file holds gives a row with
    /// `in_manifest: null`.
    pub fn compare(&self, manifest_json: &str) -> Result<Vec<CompareRow>, String> {
        let manifest: Value =
            serde_json::from_str(manifest_json).map_err(|e| format!("manifest.json: {e}"))?;
        let summary = self.summary()?;
        let mut rows: Vec<CompareRow> = Vec::new();
        let mut push = |name: String, in_file: Option<i64>, in_manifest: Option<i64>| {
            rows.push(CompareRow {
                name,
                in_file,
                in_manifest,
                equal: in_file.is_some() && in_file == in_manifest,
            });
        };

        let graph_names = manifest
            .pointer("/rdf/named_graphs")
            .or_else(|| manifest.pointer("/named_graphs"))
            .and_then(Value::as_object);
        let triples = manifest.pointer("/rdf/triples").and_then(Value::as_object);
        let mut seen_graphs: HashSet<String> = HashSet::new();
        if let Some(triples) = triples {
            for (key, value) in triples {
                let Some(expected) = value.as_i64() else {
                    continue;
                };
                if key == "union" {
                    continue;
                }
                let iri = graph_names
                    .and_then(|g| g.get(key))
                    .and_then(Value::as_str)
                    .map(str::to_string);
                let in_file = iri.as_ref().map(|iri| {
                    seen_graphs.insert(iri.clone());
                    summary
                        .graphs
                        .iter()
                        .find(|g| g.iri.as_deref() == Some(iri.as_str()))
                        .map_or(0, |g| g.statements as i64)
                });
                push(format!("rdf.triples.{key}"), in_file, Some(expected));
            }
            for g in &summary.graphs {
                let known = g.iri.as_ref().is_some_and(|iri| seen_graphs.contains(iri));
                if !known {
                    let name = g.iri.clone().unwrap_or_else(|| "default graph".to_string());
                    push(
                        format!("rdf.triples.<{name}>"),
                        Some(g.statements as i64),
                        None,
                    );
                }
            }
            if let Some(expected) = triples.get("union").and_then(Value::as_i64) {
                push(
                    "rdf.triples.union".to_string(),
                    Some(summary.triples_distinct as i64),
                    Some(expected),
                );
            }
        }

        if let Some(expected) = manifest
            .pointer("/counts/label_assertions")
            .and_then(Value::as_i64)
        {
            push(
                "counts.label_assertions".to_string(),
                Some(summary.label_assertions as i64),
                Some(expected),
            );
        }
        if let Some(by_source) = manifest
            .pointer("/counts/label_assertions_by_source")
            .and_then(Value::as_object)
        {
            let mut keys: Vec<String> = by_source.keys().cloned().collect();
            for key in summary.by_source.keys() {
                if !keys.contains(key) {
                    keys.push(key.clone());
                }
            }
            keys.sort();
            for key in keys {
                let expected = by_source.get(&key).and_then(Value::as_i64);
                let in_file = summary.by_source.get(&key).map_or(0, |n| *n as i64);
                push(
                    format!("counts.label_assertions_by_source.{key}"),
                    Some(in_file),
                    expected,
                );
            }
        }
        for (key, status) in [("certain_labels", "certain"), ("unsure_labels", "unsure")] {
            if let Some(expected) = manifest
                .pointer(&format!("/counts/{key}"))
                .and_then(Value::as_i64)
            {
                let in_file = summary.by_value_status.get(status).map_or(0, |n| *n as i64);
                push(format!("counts.{key}"), Some(in_file), Some(expected));
            }
        }
        if let Some(expected) = manifest.pointer("/counts/blocks").and_then(Value::as_i64) {
            push(
                "counts.blocks".to_string(),
                Some(summary.blocks as i64),
                Some(expected),
            );
        }
        Ok(rows)
    }

    /// Runs one SELECT or ASK query. `now` gives a clock in milliseconds.
    /// The default graph of the query is the union of all named graphs if the
    /// query has no FROM clause. The time limit is tested between result rows.
    pub fn query(
        &self,
        sparql: &str,
        max_rows: usize,
        max_ms: f64,
        now: &dyn Fn() -> f64,
    ) -> Result<QueryOutput, QueryError> {
        let start = now();
        let mut parser = SparqlParser::new();
        let mut evaluator = SparqlEvaluator::new();
        for (prefix, iri) in PREFIXES {
            parser = parser.with_prefix(prefix, iri).map_err(|e| QueryError {
                code: "evaluation",
                message: e.to_string(),
            })?;
            evaluator = evaluator.with_prefix(prefix, iri).map_err(|e| QueryError {
                code: "evaluation",
                message: e.to_string(),
            })?;
        }
        match parser.clone().parse_query(sparql) {
            Ok(Query::Select { .. }) | Ok(Query::Ask { .. }) => {}
            Ok(_) => {
                return Err(QueryError {
                    code: "form_refused",
                    message:
                        "Only SELECT and ASK queries run here. CONSTRUCT and DESCRIBE are refused."
                            .to_string(),
                })
            }
            Err(e) => {
                if parser.parse_update(sparql).is_ok() {
                    return Err(QueryError {
                        code: "update_refused",
                        message: "Only SELECT and ASK queries run here. An update is refused; the data is read-only."
                            .to_string(),
                    });
                }
                return Err(QueryError {
                    code: "syntax",
                    message: e.to_string(),
                });
            }
        }
        let mut prepared = evaluator.parse_query(sparql).map_err(|e| QueryError {
            code: "syntax",
            message: e.to_string(),
        })?;
        if prepared.dataset().is_default_dataset() {
            prepared.dataset_mut().set_default_graph_as_union();
        }
        let eval_error = |e: &dyn std::fmt::Display| QueryError {
            code: "evaluation",
            message: e.to_string(),
        };
        let results = prepared
            .on_store(&self.store)
            .execute()
            .map_err(|e| eval_error(&e))?;
        let mut out = QueryOutput {
            kind: "select",
            variables: Vec::new(),
            rows: Vec::new(),
            boolean: None,
            truncated: false,
            timed_out: false,
            max_rows,
            max_ms,
            elapsed_ms: 0.0,
        };
        match results {
            QueryResults::Boolean(b) => {
                out.kind = "ask";
                out.boolean = Some(b);
            }
            QueryResults::Solutions(solutions) => {
                out.variables = solutions
                    .variables()
                    .iter()
                    .map(|v| v.as_str().to_string())
                    .collect();
                for solution in solutions {
                    if out.rows.len() >= max_rows {
                        out.truncated = true;
                        break;
                    }
                    let solution = solution.map_err(|e| eval_error(&e))?;
                    out.rows.push(
                        solution
                            .values()
                            .iter()
                            .map(|t| t.as_ref().map(cell))
                            .collect(),
                    );
                    if now() - start > max_ms {
                        out.timed_out = true;
                        break;
                    }
                }
            }
            QueryResults::Graph(_) => {
                return Err(QueryError {
                    code: "form_refused",
                    message: "Only SELECT and ASK queries run here.".to_string(),
                })
            }
        }
        out.elapsed_ms = now() - start;
        Ok(out)
    }
}

fn cell(term: &Term) -> Cell {
    match term {
        Term::NamedNode(n) => Cell {
            kind: "iri",
            value: n.as_str().to_string(),
            datatype: None,
            lang: None,
        },
        Term::BlankNode(b) => Cell {
            kind: "bnode",
            value: b.as_str().to_string(),
            datatype: None,
            lang: None,
        },
        Term::Literal(l) => Cell {
            kind: "literal",
            value: l.value().to_string(),
            datatype: Some(l.datatype().as_str().to_string()),
            lang: l.language().map(str::to_string),
        },
        #[allow(unreachable_patterns)]
        other => Cell {
            kind: "literal",
            value: other.to_string(),
            datatype: None,
            lang: None,
        },
    }
}

/// The fixed example queries. Each query names its prefixes, so it also runs in another SPARQL tool.
pub fn examples() -> Vec<Example> {
    vec![
        Example {
            id: "labels",
            title_en: "All labels with their probability and page",
            title_de: "Alle Labels mit Wahrscheinlichkeit und Seite",
            sparql: "PREFIX plb: <https://schema.parlpdfech.example/labels/>\n\
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n\
SELECT ?label ?value ?probability ?status ?page WHERE {\n\
  ?label a plb:LabelAssertion ;\n\
         rdf:object ?value .\n\
  OPTIONAL { ?label plb:probability ?probability }\n\
  OPTIONAL { ?label plb:valueStatus ?status }\n\
  OPTIONAL { ?label plb:page ?page }\n\
}\n\
ORDER BY ?page ?label",
        },
        Example {
            id: "unsure",
            title_en: "Labels with the status unsure",
            title_de: "Labels mit dem Status unsicher",
            sparql: "PREFIX plb: <https://schema.parlpdfech.example/labels/>\n\
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n\
SELECT ?label ?value ?probability ?page WHERE {\n\
  ?label a plb:LabelAssertion ;\n\
         plb:valueStatus plb:unsure ;\n\
         rdf:object ?value ;\n\
         plb:probability ?probability .\n\
  OPTIONAL { ?label plb:page ?page }\n\
}\n\
ORDER BY ?probability",
        },
        Example {
            id: "sources",
            title_en: "Who decided each label (count by source and kind)",
            title_de: "Wer jedes Label entschieden hat (Anzahl nach Quelle und Art)",
            sparql: "PREFIX plb: <https://schema.parlpdfech.example/labels/>\n\
SELECT ?source ?kind (COUNT(?label) AS ?labels) WHERE {\n\
  ?label a plb:LabelAssertion ;\n\
         plb:labelSource ?source ;\n\
         plb:labelKind ?kind .\n\
}\n\
GROUP BY ?source ?kind\n\
ORDER BY ?source ?kind",
        },
        Example {
            id: "block_text",
            title_en: "The text lines of each block with the label of the block",
            title_de: "Die Textzeilen jedes Blocks mit dem Label des Blocks",
            sparql: "PREFIX plb: <https://schema.parlpdfech.example/labels/>\n\
PREFIX ppx: <https://schema.parlpdfech.example/profile/>\n\
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n\
SELECT ?position ?value ?probability ?text WHERE {\n\
  ?block a plb:PdfBlock ;\n\
         plb:position ?position ;\n\
         plb:atom ?atom .\n\
  ?atom ppx:charStart ?start .\n\
  OPTIONAL { ?atom plb:atomText ?text }\n\
  ?label a plb:LabelAssertion ;\n\
         rdf:subject ?block ;\n\
         rdf:object ?value .\n\
  OPTIONAL { ?label plb:probability ?probability }\n\
}\n\
ORDER BY ?position ?start",
        },
        Example {
            id: "ech_head",
            title_en: "The eCH-0295 head values (short values of the eCH graph)",
            title_de: "Die eCH-0295-Kopfwerte (kurze Werte des eCH-Graphen)",
            sparql: "SELECT ?subject ?property ?value WHERE {\n\
  GRAPH ?g { ?subject ?property ?value }\n\
  FILTER(STRENDS(STR(?g), \"/ech-0295\"))\n\
  FILTER(isLiteral(?value) && STRLEN(STR(?value)) < 200)\n\
}\n\
ORDER BY ?subject ?property",
        },
    ]
}

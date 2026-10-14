// Runs the built WebAssembly module outside the browser (node 18 or later).
// Use: node rdfcheck/tools/check_wasm.mjs <records folder> [doc id ...]
// The records folder holds one sub-folder for each document id with
// <doc>.gesamt.trig and manifest.json. Exit code 0: all checks passed.
// The tool knows the two record forms of the package by manifest.json:
// 1. The record with head values read from the PDF (schema
//    parlpdfech-pdf-values-record/1; conformance i95 or i95_with_recorded_gaps).
//    It has one affair, also for a PDF with no export record (folder and file
//    prefix "local"). The example ech_head must give 1 or more rows, if the record
//    holds a value that is read or a text block in its eCH-0295 part (manifest key
//    counts); a record with none of them (for example body text only in a document
//    of the kind other) gives 0 rows: its affair has an address only. The eCH-0295
//    graph must hold no address of the register. A value that the manifest names
//    as not written (key value_floor.not_written, a weak candidate) must be a
//    label, and its slot must have 0 statements in the eCH-0295 graph. The same
//    applies to the slot of each recorded gap.
//    The cascade of the record (manifest key cascade, record form version 3): the
//    manifest names the kind of the document and, for each of the 7 values, if the
//    rules search it. A value that is not searched has no statement in the eCH-0295
//    graph. A document of the kind proposal or executive_proposal has no response
//    step in that graph; the body that its text addresses (key addressee_candidates)
//    is a label only. A value that is read (a slot with the state read_from_pdf and
//    a label) is a label of the labels graph. The probability of each value comes
//    from all folds of the calibration file (key value_calibration.probability_from).
//    For a PDF with no export record no label may have the statement plb:inSample.
// 2. The earlier record form (PARLPDFECH_VALUES=off). A record of a PDF with no
//    export record (conformance pdf_only_with_recorded_gaps) has no eCH-0295 head
//    values: for it the example ech_head must give 0 rows, and no label may have
//    the statement plb:inSample.
// The tool also searches the two files of ui/pkg for paths of a build host
// (the start of a home folder on macOS, the start /home/ and the home folder
// of this user).
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const pkg = resolve(here, "..", "..", "ui", "pkg");
const records = process.argv[2];
const docs = process.argv.slice(3);
if (!records || docs.length === 0) {
  console.error("use: node check_wasm.mjs <records folder> <doc id> [doc id ...]");
  process.exit(2);
}

const glue = await import(join(pkg, "parlpdfech_rdfcheck.js"));
glue.initSync({ module: readFileSync(join(pkg, "parlpdfech_rdfcheck_bg.wasm")) });

const VALUES_RECORD = "parlpdfech-pdf-values-record/1";
const VALUES_CONFORMANCE = ["i95", "i95_with_recorded_gaps"];
const EARLIER_CONFORMANCE = ["i95", "i95_with_recorded_gaps", "pdf_only_with_recorded_gaps"];
// the predicate of each head slot that can be a gap or a weak candidate
const SLOT_IRI = {
  affair_type: "https://ch.paf.link/schema/affairs/affairType",
  affair_number: "https://ch.paf.link/schema/affairs/affairNumber",
  title: "https://ch.paf.link/schema/affairs/title",
  submission_date: "https://ch.paf.link/schema/affairs/submissionDate",
  responder: "https://ch.paf.link/schema/affairs/responder",
  sponsor: "https://ch.paf.link/schema/affairs/sponsorship",
};

let failed = 0;
function check(condition, text) {
  if (!condition) {
    failed += 1;
    console.error("FAILED: " + text);
  }
}

// no path of a build host in the module and in the glue script (byte search)
let hostPaths = 0;
for (const name of ["parlpdfech_rdfcheck_bg.wasm", "parlpdfech_rdfcheck.js"]) {
  const bytes = readFileSync(join(pkg, name));
  for (const needle of ["/" + "Users/", "/home/", homedir() + "/"]) {
    let at = -1;
    while ((at = bytes.indexOf(needle, at + 1)) !== -1) hostPaths += 1;
  }
}
check(hostPaths === 0, "no path of a build host in ui/pkg (" + hostPaths + " found)");
console.log("paths of a build host in ui/pkg: " + hostPaths);

console.log("version " + glue.version());
const examples = JSON.parse(glue.examples()).examples;
check(examples.length >= 3 && examples.length <= 5, "3 to 5 examples");

for (const doc of docs) {
  const trig = readFileSync(join(records, doc, doc + ".gesamt.trig"));
  const manifest = readFileSync(join(records, doc, "manifest.json"), "utf8");
  const rdf = new glue.RdfCheck();
  const t0 = performance.now();
  const loaded = JSON.parse(rdf.load(trig));
  const t1 = performance.now();
  check(loaded.ok, doc + ": load");
  const summary = JSON.parse(rdf.summary()).summary;
  const man = JSON.parse(manifest);
  const pdfOnly = man.conformance === "pdf_only_with_recorded_gaps";
  const fromPdf = man.schema === VALUES_RECORD;
  if (fromPdf) {
    check(VALUES_CONFORMANCE.includes(man.conformance), doc + ": conformance of the record with values from the PDF (" + man.conformance + ")");
    check((man.conformance === "i95") === ((man.i95_gaps || []).length === 0), doc + ": the conformance name agrees with the recorded gaps");
  } else {
    check(EARLIER_CONFORMANCE.includes(man.conformance), doc + ": conformance of the earlier record form (" + man.conformance + ")");
  }
  const compared = JSON.parse(rdf.compare(manifest));
  check(compared.ok && compared.all_equal, doc + ": all counts equal");
  const parts = [];
  const notes = [];
  for (const ex of examples) {
    const q0 = performance.now();
    const out = JSON.parse(rdf.query(ex.sparql, 0, 0));
    if (pdfOnly && ex.id === "ech_head") {
      // the eCH-0295 graph of such a record holds one statement (a container with no affair)
      check(out.ok && out.result.rows.length === 0, doc + ": example ech_head gives 0 rows for a record with no export record");
    } else if (fromPdf && ex.id === "ech_head") {
      // rows only if the eCH-0295 part holds a value that is read or a text block
      const c = man.counts || {};
      const by = c.textblocks_by_slot || {};
      const content = ((c.values || {}).read_from_pdf || 0) + (by.submission || 0) + (by.response || 0);
      check(out.ok && (out.result.rows.length > 0) === (content > 0), doc + ": example ech_head gives rows only for a record with a value or a text block in the eCH-0295 part (" + content + ")");
    } else {
      check(out.ok && out.result.rows.length > 0, doc + ": example " + ex.id);
    }
    parts.push(ex.id + " " + (out.ok ? out.result.rows.length : "error") + " rows " + (performance.now() - q0).toFixed(1) + " ms");
  }
  const ask = JSON.parse(rdf.query("ASK { ?l a plb:LabelAssertion }", 0, 0));
  check(ask.ok && ask.result.kind === "ask" && ask.result.boolean === true, doc + ": ASK");
  const limited = JSON.parse(rdf.query("SELECT * WHERE { ?s ?p ?o }", 7, 0));
  check(limited.ok && limited.result.rows.length === 7 && limited.result.truncated, doc + ": row limit");
  const syntax = JSON.parse(rdf.query("SELECT ?s WHERE { ?s ?p }", 0, 0));
  check(!syntax.ok && syntax.error.code === "syntax", doc + ": syntax error");
  const update = JSON.parse(rdf.query("DELETE WHERE { ?s ?p ?o }", 0, 0));
  check(!update.ok && update.error.code === "update_refused", doc + ": update refused");
  const construct = JSON.parse(rdf.query("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }", 0, 0));
  check(!construct.ok && construct.error.code === "form_refused", doc + ": CONSTRUCT refused");
  check(JSON.parse(rdf.summary()).summary.statements === summary.statements, doc + ": store not changed");
  const flags = summary.by_in_sample || {};
  const noExport = pdfOnly || (fromPdf && man.has_export === false);
  if (noExport) {
    check(!flags["true"] && !flags["false"], doc + ": no label of a record with no export record has plb:inSample");
  }
  if (fromPdf) {
    const ech = 'FILTER(STRENDS(STR(?g), "/ech-0295"))';
    const affairs = JSON.parse(rdf.query("SELECT DISTINCT ?a WHERE { GRAPH ?g { ?a a <https://ch.paf.link/schema/affairs/Affair> } " + ech + " }", 0, 0));
    check(affairs.ok && affairs.result.rows.length === 1, doc + ": the eCH-0295 graph has one affair");
    const register = JSON.parse(rdf.query("ASK { GRAPH ?g { ?s ?p ?o } " + ech + ' FILTER(CONTAINS(STR(?s), "openparldata.ch") || CONTAINS(STR(?o), "openparldata.ch")) }', 0, 0));
    check(register.ok && register.result.boolean === false, doc + ": no address of the register in the eCH-0295 graph");
    // a recorded gap and a weak candidate: the slot has no statement in the eCH-0295 graph
    const absent = new Set((man.i95_gaps || []).map((g) => g.slot));
    for (const w of (man.value_floor || {}).not_written || []) absent.add(w.field);
    for (const slot of absent) {
      const iri = SLOT_IRI[slot];
      if (!iri) continue;
      const q = JSON.parse(rdf.query("ASK { GRAPH ?g { ?s <" + iri + "> ?o } " + ech + " }", 0, 0));
      check(q.ok && q.result.boolean === false, doc + ": the slot " + slot + " (gap or weak candidate) has no statement in the eCH-0295 graph");
    }
    for (const w of (man.value_floor || {}).not_written || []) {
      const q = JSON.parse(rdf.query('ASK { ?l a plb:LabelAssertion FILTER(STRENDS(STR(?l), "/label/' + w.label_id + '")) }', 0, 0));
      check(q.ok && q.result.boolean === true, doc + ": the weak candidate " + w.label_id + " is a label");
    }
    // the cascade of the record
    const casc = man.cascade || {};
    const selection = casc.selection || {};
    check(typeof casc.version === "string" && Object.keys(selection).length === 7, doc + ": the manifest has the cascade with the 7 values");
    check((man.value_calibration || {}).probability_from === "all folds", doc + ": the probabilities come from all folds of the calibration file");
    const cut = Object.keys(selection).filter((f) => selection[f].searched === false).sort();
    const responseStep = JSON.parse(rdf.query("ASK { GRAPH ?g { ?o a <https://ch.paf.link/schema/affairs/ResponseStep> } " + ech + " }", 0, 0));
    const submission = JSON.parse(rdf.query("ASK { GRAPH ?g { ?a <https://ch.paf.link/schema/affairs/submission> ?o } " + ech + " }", 0, 0));
    const steps = casc.steps || {};
    if (steps.response && steps.response.applies === false) {
      check(responseStep.ok && responseStep.result.boolean === false, doc + ": no response step in the eCH-0295 graph (the kind " + casc.kind + " cannot state it)");
    }
    if (["proposal", "executive_proposal"].includes(casc.kind)) {
      check(cut.includes("responder") && cut.includes("response_date"), doc + ": the kind " + casc.kind + " searches no responder and no response date");
    }
    for (const f of cut) {
      const iri = SLOT_IRI[f];
      if (!iri && f !== "response_date") continue;
      // the response date is the end date of a response step (the predicate is common to each step class)
      const pattern = f === "response_date"
        ? "?s a <https://ch.paf.link/schema/affairs/ResponseStep> ; <https://ld.ech.ch/schema/0292/meta-common/dateEndActual> ?o"
        : "?s <" + iri + "> ?o";
      const q = JSON.parse(rdf.query("ASK { GRAPH ?g { " + pattern + " } " + ech + " }", 0, 0));
      check(q.ok && q.result.boolean === false, doc + ": the value " + f + " (not searched in the kind " + casc.kind + ") has no statement in the eCH-0295 graph");
    }
    for (const c of man.addressee_candidates || []) {
      const q = JSON.parse(rdf.query('ASK { ?l a plb:LabelAssertion FILTER(STRENDS(STR(?l), "/label/' + c.label_id + '")) }', 0, 0));
      check(q.ok && q.result.boolean === true && cut.includes(c.field), doc + ": the addressed body " + c.label_id + " is a label and not a value of the record");
    }
    let read = 0;
    for (const s of man.slots || []) {
      if (s.state === "read_from_pdf" && s.field && s.label_id) {
        read += 1;
        const q = JSON.parse(rdf.query('ASK { ?l a plb:LabelAssertion FILTER(STRENDS(STR(?l), "/label/' + s.label_id + '")) }', 0, 0));
        check(q.ok && q.result.boolean === true && selection[s.field] && selection[s.field].searched === true, doc + ": the value " + s.field + " is a label, and the cascade searches it");
      }
      if (s.field && s.state === "not_in_this_document_type") {
        check(s.result === "not searched in this kind of document" && s.kind === casc.kind && (s.cascade_rules || []).length > 0, doc + ": the slot of " + s.field + " names the kind and the cascade rules");
      }
    }
    notes.push("cascade " + casc.version + ", kind " + casc.kind + ", type " + casc.affair_type_of_the_cascade + ", values read " + read +
      ", not searched " + JSON.stringify(cut) + ", submission step " + (submission.ok && submission.result.boolean) + ", response step " + (responseStep.ok && responseStep.result.boolean));
    notes.push("values from the PDF, conformance " + man.conformance + ", gaps " + JSON.stringify([...absent]));
  }
  console.log(
    doc + ": load " + (t1 - t0).toFixed(1) + " ms, statements " + summary.statements +
      ", labels " + summary.label_assertions + ", rows compared " + compared.rows.length +
      ", all equal " + compared.all_equal + ", inSample " + JSON.stringify(flags) +
      (noExport ? ", record with no export record" : "") + (notes.length ? ", " + notes.join(", ") : "") + "; " + parts.join("; ")
  );
  rdf.free();
}

const broken = new glue.RdfCheck();
const bad = JSON.parse(broken.load(new TextEncoder().encode("<urn:g> {\n  <urn:a> <urn:b> ;;; .\n}\n")));
check(!bad.ok && bad.error.code === "parse" && bad.error.line === 2 && bad.error.column > 0, "parse error with line and column");
console.log("parse error: line " + bad.error?.line + ", column " + bad.error?.column + ": " + bad.error?.message);
check(JSON.parse(broken.summary()).error?.code === "no_data", "summary with no file");

console.log(failed === 0 ? "ALL CHECKS PASSED" : failed + " CHECK(S) FAILED");
process.exit(failed === 0 ? 0 : 1);

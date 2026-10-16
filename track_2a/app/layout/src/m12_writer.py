#!/usr/bin/env python3
"""Writer of the eCH-0295 record whose head values are read from the PDF (plan `plan-ech-from-pdf.md`, task T15).

Version m12-writer-1 (16.10.2026): a copy of src/m11_writer.py (m11-writer-6, SHA-256
8a70b0f5574f6781e6415f8eafc86725cc27f89cce51f5f6e12e45dbbda8e6d1) with the edits W1 to W5 of the Apertus spec of
15.10.2026 (scratchpad apertus-build/SPEC.md, chapter 4.3). It writes the records of the Apertus mode of the package:
the values of the combined reader (rules, then the 2 Apertus tiers apertus_q1 and apertus_q2_sponsor_hi; module
src/m12_apertus_values.py) with the calibration file of the Apertus mode (constant CALIBRATION_REL). The frozen file
src/m11_writer.py does not change; the rules-only path of the package uses it.
  W1  this header, VERSION, SCRIPT, CALIBRATION_REL, APERTUS_ORIGIN (the origin sentence of the 2 Apertus tiers: in
      their calibration nodes and in the manifest; a node of a rule tier keeps the text of the rules path), import
      of m12_apertus_values
  W2  the rule id of a value with an Apertus tier: m12_apertus_values.rule_id_of (q1_place or read_q2)
  W3  a value label with an Apertus tier has the label source apertus_head. Its note starts with the Apertus note
      (decision, head, layer, backend, head probability, near mark); the comparison note of the reader stays the
      end of the note (check C20)
  W4  the rule text of the value record (provenance file) of an Apertus value names the Apertus decision and the
      backend. The derivation stays extracted_from_pdf_by_rule: code reads the value from the wording at the span;
      only the choice is by Apertus
  W5  write_record(..., apertus=...): the input apertus_heads (the heads output of the document), the manifest
      key apertus_values, and the note of the manifest key apertus_note
Status of the copy: EXCEPTION, NOT RELEASED. No human checked it.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: EXCEPTION (process rule 10), NOT RELEASED. No human checked this file. The reference of the record
form is `daten/gj_values/record_form.md` (chapters 2 to 6 and 8). This file changes no existing file.

1 Task
  The writer builds the record of ONE document from the block file (interface 2), the rule file of the rule chain,
  the block decisions (interface 7: rules mode or a decisions file of the Apertus candidate), the results of the
  CASCADE READER (`src/m11_values_cascade.py`, on the value readers of `src/m11_values_base.py`) and a value
  calibration file (form of `src/m11_value_cal.py`, command open). An export record is optional. It gives the cross-check only. No value of the eCH-0295 part comes from
  the export. A value that the rules do not find is absent, and the record gives the state and the reason.

  The value of a field in the eCH-0295 part (record form chapter 2.3; decisions W-1 and W-4 of 13.10.2026):
  the responder and the first author are the printed wording at the span on one line (m11_values_base.norm_text).
  The title and the affair number are the printed wording in the one-line form of the reader. The affair type is
  the list value of the printed type word. A date is the ISO day of the printed date. The comparison value of
  the reader (the folded family name, the table form of the body) is for the cross-check and the calibration
  only. It is not a value of the eCH-0295 part.
  The label selection (decision D1 of 13.10.2026): the kind of the document selects the values that are searched
  (`m11_cascade.labels_for(kind, affair_type)`; the kind comes from the rule chain, or from the argument kind).
  A value that the cascade does not search has the slot state not_in_this_document_type with the result text
  "not searched in this kind of document", the kind and the ids of the cascade rules. Only the selection of the
  cascade gives this state. A value that the cascade searches and whose rule gives its own reason
  not_in_document_type is a result of a search: state not_found_in_pdf with the reason reader_scope (finding
  S3-01 of 13.10.2026).
  The kind (rule V5 of the cascade reader): a document with the S1 rule id D0 gets its kind from 2 facts of the
  PDF. The manifest key cascade.kind_source holds the kind of the rule chain and the 2 facts (key v5).
  The text blocks (decision of 13.10.2026, after the decisions W-5 and D3): a text block is written to the
  eCH-0295 part only if the cascade gives its text slot to the kind of the document. Each other text block
  stays a TextBlockRecord of the provenance file with its text and a not-mapped reason. Its block labels stay
  in the label file.
  The author rule (decision D2): the first author and the submission date are searched for the kinds proposal,
  executive_proposal, response and combined (rule R30 of the cascade). A response document that prints them gets
  a submission step with the sponsorship and the date and with no text block.
  No response step in a proposal (decision D3): the kinds proposal and executive_proposal get no response step.
  The body that the text addresses is a candidate label only (label id candidate-responder).
  The probability (decision D4): the probability of a value label is the stored value of its rule tier over all
  folds (p_all_folds), for each document. A fold value is not shown.
  The floor (decision W-3): a value of a tier whose stored probability of all folds is below 0.5 is not written
  to the eCH-0295 part. It stays in the label file as a candidate, and the slot has the state not_found_in_pdf
  with the reason weak_candidate_only. The floor uses the number that the record shows.

2 Outputs (record folder; the file prefix is the document number, or the word local)
  <prefix>.ech.yaml         the I95 Container with one affair (minted IRI)
  <prefix>.provenance.yaml  the provenance file (profile 0.2.0, class ExtractionRecord)
  <prefix>.labels.yaml      the label file (`src/m11_label_schema.yaml` 0.2.0, class LabelRecord)
  manifest.json             schema parlpdfech-pdf-values-record/1
  The function rdf_step adds <prefix>.gesamt.trig (4 named graphs), <prefix>.gesamt.rdf.xml, <prefix>.ech.ttl and
  <prefix>.ech.rdf.xml. These are the file names of the frozen writer.
  Since m11-writer-5 rdf_step also writes <prefix>.values.ttl (function values_graph; form parlpdfech-values-ttl/2
  since m11-writer-6): one node for each value of the eCH-0295 part with the resource and the property of eCH-0295
  (the pair is a statement of <prefix>.ech.ttl), the entity whose name holds the value if it is another resource
  (sponsor and responder: the actor), the value, the printed wording, the probability, the value status, the rule
  tier, the page and the character span. The facts come from the label file. Vocabulary:
  https://schema.parlpdfech.example/values/ (prefix pvl; the same placeholder domain as the label schema).

3 Reuse by import (no frozen file changes)
  m10_writer (input checks, author runs, constants), m06_converter (wording of a text block, check E19),
  m06_ech_ausgabe (V values, YAML writer, evidence forms), m10_gaps (absent required slots, gap methods),
  m10_rdf (graph functions), m10_calibrate (as_written, cal_id, floor lookup), m10_cascade (floor decisions),
  m11_value_norm and m11_value_reference (comparison and reference of the cross-check), m02_ech_regeln (typ_ech).

4 The data root
  The frozen wording functions read the atom file through `m03_iso_paths.iso_path`. The argument `root` names the
  folder that holds `daten/iso/atome/<prefix>.json` and `daten/iso/docling/<prefix>.json`. If `root` is not the
  folder of the code files, the writer sets 5 module constants in memory for the time of one call (data_root):
  the two folders of m03_iso_paths, and the root, the cache folder and the word counts of m03_gold_record. Then the
  word counts for a line-end hyphen come from the atom files below `root` only. This is the scope of the package.
  The command line makes such a root for one development document (item 6).

5 Closed parliaments
  If `daten/gj_values/folds.json` is below the code root or below `root`, the writer refuses a document of the
  closed part, and a block file with the key of a closed parliament. It stops with ClosedParliament if
  `daten/gj_values/opening.json` is absent. The check comes before the block file is used for a value.

6 Usage (from the project folder; one command on one line)
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m11_writer.py --doc DOC --out DIR
      [--decisions FILE] [--block-calibrations FILE] [--calibration FILE] [--export FILE | --no-export]
      [--base IRI] [--root DIR] [--print-ech]
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m11_writer.py --block-file F --rule-file F
      --pdf-sha256 H --out DIR [--decisions FILE] [--block-calibrations FILE] [--calibration FILE] [--root DIR]
  --doc         a development document. Block file daten/gj/docs/DOC.json. Rule file: DOC.json in the folder
                m11_values_base.RULES_DIR (the rule files that are made from the PDF alone).
                With no --root the command copies the atom file and the Docling file of the document to
                DIR/inputs/root and uses that folder as the data root (item 4).
  --block-file  a file with no project data (doc_id local or null). The root must hold the atom file local.json.
  --decisions   a decisions file (interface 7). With no such file: rules mode. The command makes the floor
                decisions from the rule file (m10_cascade.floor_decisions) and writes them to DIR/inputs/.
  --calibration the value calibration file. Default: the file of the product (constant CALIBRATION_REL,
                decision D5), below the data root or below the code root. Its numbers come from the development
                documents of 44 parliaments that the rule authors read (constant CALIBRATION_ORIGIN). If that
                file does not exist, the command stops. The STAND-IN file of the record examples is used only
                if this option names it.
  --kind        the kind of the document (a key of the kinds of the cascade). Default: from the rule chain.
  --export      the export record of the document. Default for --doc: the stored record of the development run,
                if it exists. The export gives the cross-check only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_record as gr  # noqa: E402  (frozen: signatures of check E19, word counts)
import m03_iso_paths as ip  # noqa: E402  (frozen: the two folders of the atom files, set in memory by data_root)
import m03_iso_v4 as v4  # noqa: E402  (frozen: fixed answers)
import m06_converter as mc  # noqa: E402  (frozen: wording, E19, atom evidence)
import m06_ech_ausgabe as ea  # noqa: E402  (frozen: V values, YAML writer, evidence forms)
import m10_calibrate as cal  # noqa: E402  (frozen: as_written, cal_id, floor lookup)
import m10_gaps as gp  # noqa: E402  (frozen: I95 gap methods)
import m10_rdf as rdf  # noqa: E402  (frozen: graph functions)
import m10_writer as fw  # noqa: E402  (frozen writer: input checks, author runs, constants)
import m11_cascade as casc  # noqa: E402  (the cascade of the standard: labels_for)
import m11_value_norm as vn  # noqa: E402  (comparison of the cross-check)
import m11_values_base as vb  # noqa: E402  (interface of the value readers)
import m11_values_cascade as vcr  # noqa: E402  (the cascade reader: read_document, selection, kind_of)
import m11_values_title as mt  # noqa: E402  (FIXED rule module: norm_title, the one-line form of a title)
import m12_apertus_values as av  # noqa: E402  (W1: the Apertus tiers, their rule ids and their notes)

V = ea.V
VERSION = "m12-writer-1"
SCRIPT = "src/m12_writer.py"
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LABEL_SCHEMA = SRC / "m11_label_schema.yaml"
RECORD_SCHEMA = "parlpdfech-pdf-values-record/1"
DEFAULT_BASE = "https://parlpdfech.ansv.ch/id/"
LOCAL = "local"
IRI_PREFIX = "urn:parlpdfech:local:sha256:"
GRAPHS = rdf.GRAPHS
FOLDS_REL = "daten/gj_values/folds.json"
OPENING_REL = "daten/gj_values/opening.json"
CALIBRATION_REL = "daten/gj_values/apertus/calibration_values_apertus.json"     # W1: the file of the Apertus mode
# decision D5: the text of each place that names the origin of the calibration file (4 sentences). Text of
# 14.10.2026: each number is a display value of public/track_2a/numbers.json (made 14.10.2026 11:01), ids
# values.last_run.rules_only.all.documents, values.last_run.parliaments.all,
# values.last_run.rules_only.all.<affair_number|submission_date>.share_correct (the one fixed run of 13.10.2026, reader
# with rules only, reference: the export) and values.last_run.contact.read_by_ai_agents.lower_limit.
# m11_writer_test.py compares them with that file.
CALIBRATION_ORIGIN = ("Development documents of 44 parliaments that the rule authors read; the rule files of the reader "
                      "are made from the PDF alone. The one fixed run of 13.10.2026 used 872 documents of 26 other "
                      "parliaments. There the share correct (correct / documents with an export value) was 0.2214 for "
                      "the affair number and 0.2729 for the submission date. Before the run, AI agents had read 116 or "
                      "more of these documents in earlier work.")
# W1: the origin of the 2 Apertus tiers of the calibration file of the Apertus mode (calibration nodes of these tiers
# and the manifest; a node of a rule tier keeps the text of the rules path)
APERTUS_ORIGIN = ("The 2 Apertus tiers (apertus_q1, apertus_q2_sponsor_hi) come from "
                  "daten/gj_values/heads2/calibration_dev_combined.json: out-of-fold heads on the development documents "
                  "(fit of 13.10.2026).")
# finding S3-09: the sentence of the calibration file that decision D4 made false, and the sentence of the record
FOLD_SENTENCE = "A document of fold f gets the value without fold f. Other documents get the value of all folds."
ALL_FOLDS_SENTENCE = "The record shows the value of all folds for each document (decision D4)."
FOLD_PARAMETER = "jeffreys_mean_without_fold_"       # the 5 fold values of a pair: a detail of the measurement
PROBABILITY_FROM = "all folds"           # decision D4: p_all_folds of the rule tier, for each document
STANDIN_REL = "daten/gj_values/record_examples/STANDIN_calibration_values.json"
DEV_EXPORT_REL = "daten/gj/fullrun_b1s_dev/{d}/export/{d}.json"
FLOOR_REL = "daten/gj/calibration/floor_v1.json"
BODIES_FILE = "daten/roh/exports/bodies.ndjson.gz"
CONTRIBUTORS_FILE = "daten/roh/exports/contributors.ndjson.gz"
FIELDS = tuple(vb.FIELDS)
# field -> (entity, I95 slot of the label predicate, slot name of the manifest, normalisation rule, gap slot)
FIELD_TABLE = {
    "affair_type": ("affair", "affair_type", "Affair.affair_type", "type_word_to_list_value"),
    "title": ("affair", "title", "Affair.title", "norm_text_one_line"),
    "affair_number": ("affair", "affair_number", "Affair.affair_number", "norm_text"),
    "submission_date": ("submission", "submission_date", "Submission.submission_date", "date_to_iso_day"),
    "response_date": ("response", "date_end_actual", "ResponseStep.date_end_actual", "date_to_iso_day"),
    "responder": ("response", "responder", "ResponseStep.responder", "printed_wording_one_line"),
    "sponsor": ("submission", "sponsorship", "Submission.sponsorship", "printed_wording_one_line"),
}
# decisions W-1 and W-4: the record value of these fields is the printed wording on one line, not the value of the reader
PRINTED_FIELDS = ("responder", "sponsor")
COMPARISON_NOTE = "comparison value of the reader (for the cross-check and the calibration only; not a value of the record): "
# decision W-3: the floor
FLOOR_P = 0.5
WEAK_REASON = "weak_candidate_only"
WEAK_MARK = "not written: the tier is more often different from the reference than equal"
CANDIDATE_GAP_REASON = "candidate_not_valid"       # the reason code of the label schema 0.2.0 for a candidate that is not written
# decision D1: the label selection of the cascade
NOT_SEARCHED = vcr.NOT_SEARCHED                    # "not searched in this kind of document"
NOT_IN_TYPE = "not_in_this_document_type"
# finding S3-01: a value that the cascade searches and whose rule gives the reader reason not_in_document_type
SCOPE_REASON = "reader_scope"                      # the reason of the manifest slot (state not_found_in_pdf)
SCOPE_GAP_REASON = "no_candidate"                  # the reason code of the label schema 0.2.0 for this gap record
SCOPE_MARK = "searched, no value: the rule of this value does not read this document"
TEXT_SLOT = {"submission": ("Submission", "submission"), "response": ("ResponseStep", "executive_response")}
# decision D3: the body that a proposal addresses is a candidate label only
ADDRESSEE_MARK = ("not written: the body that the text of the proposal addresses; the rules search no response step in "
                  "a document of this kind")
CANDIDATE_KINDS = ("weak", "addressee")
FIELD_OF_SLOT = {v[2]: k for k, v in FIELD_TABLE.items()}
CALIBRATION_FIELD = {"responder": "responder_name", "sponsor": "first_author"}
PRIMARY_ROLE_FIELDS = ("response_date", "responder")
PRIMARY_ROLES = ("response", "combined")
PDF_DERIVATIONS = ("identifier_minted", "fixed_by_schema", "detected_by_rule", "extracted_from_pdf",
                   "extracted_from_pdf_by_rule")                       # rule T of the record form
STATES = ("read_from_pdf", "not_found_in_pdf", "not_in_this_document_type", "register_only")
EXPORT_CHECKS = ("equal_to_export", "differs_from_export", "no_export_value", "not_compared")
CONSISTENCY = {"equal_to_export": "confirmed", "differs_from_export": "metadata_differs",
               "no_export_value": "not_checked", "not_compared": "not_checked"}
# reason of a reader -> (slot state, gap reason); record form chapter 3.3
GAP_OF_REASON = {"no_text": ("not_found_in_pdf", "no_text"), "no_pattern": ("not_found_in_pdf", "no_candidate"),
                 "no_cue": ("not_found_in_pdf", "no_candidate"), "ambiguous": ("not_found_in_pdf", "ambiguous_candidates"),
                 "no_response_block": ("not_found_in_pdf", "no_block_of_role"),
                 "no_rule_file": ("not_found_in_pdf", "no_block_of_role"),
                 "not_in_document_type": ("not_in_this_document_type", "not_in_this_document_type")}
NOT_READ_OF_REASON = {"no_reader": "no_rule_searched", "reader_error": "reader_error"}
NOT_READ_REASONS = ("field_not_measured", "reader_error", "no_rule_searched")
GAP_CAUSE = {"affair_type": "the rules found no value of the I95 AffairTypeEnum in this PDF",
             "affair_number": "the rules found no affair number in this PDF"}
# the cause of a recorded gap whose field has a candidate of a weak tier (decision W-3)
GAP_CAUSE_WEAK = {"affair_type": "the rules found only a weak candidate of the affair type in this PDF",
                  "affair_number": "the rules found only a weak candidate of the affair number in this PDF"}
# slots of Affair, Submission and ResponseStep with a fixed state (record form chapter 6)
REGISTER_ONLY = ("local_id", "wikidata_uri", "date_created", "datetime_created", "date_modified", "datetime_modified",
                 "current_state", "procedure_states", "withdrawn_date")
OTHER_STEPS = ("submission_validation_steps", "assignment_steps", "committee_deliberation_steps", "plenary_debates")
NO_RULE = ("linked_affairs", "lifecycle_flags", "recommendation", "reasoning_in_council", "remark", "date_begin_actual",
           "datetime_begin_actual", "date_begin_planned", "datetime_begin_planned", "date_end_actual",
           "datetime_end_actual", "date_end_planned", "datetime_end_planned")
RX_DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
RX_SHA = re.compile(r"[0-9a-f]{64}\Z")
# texts of worker/pdf_only.py of the package for a PDF with no document number (record form chapter 6)
REFERENCE_TEXT = "reference labels of the development documents, made by a language model and not checked by a human"
NOT_KNOWN = ("The package holds the SHA-256 of its samples only. It cannot tell if this PDF is one of the "
             "development documents that the probabilities were fitted on.")
NOT_CHECKED = "The probabilities of this record were not checked on other documents. No value of a report applies."


class WriterStop(SystemExit):
    """An input that the writer refuses."""


# ------------------------------------------------------------------ small helpers
def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def path_text(p: Path, root: Path, out_dir: Path | None = None) -> str:
    """The path below the data root, else `record:` plus the path below the record folder, else the path below
    the code root, else the absolute path."""
    p = Path(p).resolve()
    for base, pre in ((root, ""), (out_dir, "record:"), (ROOT, "")):
        if base is not None and p.is_relative_to(Path(base).resolve()):
            return pre + p.relative_to(Path(base).resolve()).as_posix()
    return str(p)


def path_of(text: str, root: Path, out_dir: Path) -> Path:
    """The file of a path text of the manifest (the reverse of path_text)."""
    if text.startswith("record:"):
        return Path(out_dir) / text[len("record:"):]
    p = Path(text)
    if p.is_absolute():
        return p
    return Path(root) / p if (Path(root) / p).exists() else ROOT / p


def file_info(p: Path, root: Path, out_dir: Path | None = None) -> dict:
    return {"path": path_text(p, root, out_dir), "sha256": sha256(p), "abs": Path(p).resolve()}


@contextlib.contextmanager
def data_root(root: Path):
    """Docstring item 4: the frozen wording functions read below `root` for the time of one call."""
    root = Path(root).resolve()
    if root == ROOT:
        yield
        return
    old = (ip.DEV, ip.TEST, gr.ROOT, gr.GOLD, gr._VOCAB)
    ip.DEV, ip.TEST = root / "daten/iso", root / "daten/gold/test"
    gr.ROOT, gr.GOLD, gr._VOCAB = root, root / "daten/gold", None
    try:
        yield
    finally:
        ip.DEV, ip.TEST, gr.ROOT, gr.GOLD, gr._VOCAB = old


def closed_guard(doc_id, parliament, roots) -> None:
    """Docstring item 5. `roots`: the folders that can hold daten/gj_values/folds.json."""
    seen = set()
    for r in roots:
        r = Path(r).resolve()
        if r in seen or not (r / FOLDS_REL).is_file():
            continue
        seen.add(r)
        if (r / OPENING_REL).is_file():
            continue
        docs = read_json(r / FOLDS_REL)["documents"]
        entry = docs.get(str(doc_id)) if doc_id is not None else None
        closed = {v["parliament"] for v in docs.values() if v["part"] != "open"}
        if (entry is not None and entry["part"] != "open") or (parliament is not None and str(parliament) in closed):
            raise vb.ClosedParliament(f"{doc_id}: the document is in a closed parliament, and {OPENING_REL} does "
                                      f"not exist: the writer makes no record")


def accept_urn(*schemas: Path) -> None:
    """The LinkML dumper reads an IRI with no "//" as a CURIE. This function adds the prefix urn to the prefix map
    of the schema views in memory (the method of worker/pdf_only.py of the package). No schema file changes."""
    for schema in schemas:
        sv, _, _ = rdf.bundle(schema)
        with rdf.in_src():
            ns = sv.namespaces()
            if "urn" not in ns:
                ns["urn"] = "urn:"
            if str(sv.namespaces().get("urn")) != "urn:":
                raise WriterStop("the prefix map of a schema view does not keep the prefix urn")


def i95_slots() -> list[str]:
    """The slots of the classes Affair, Submission and ResponseStep of I95, read from the schema."""
    sv, _, _ = rdf.bundle(rdf.WRAPPER)
    with rdf.in_src():
        return [f"{c}.{s.name}" for c in ("Affair", "Submission", "ResponseStep") for s in sv.class_induced_slots(c)]


# ------------------------------------------------------------------ interface: values
def read_values(block_file, rule_file=None, strict: bool = True, kind: str | None = "from_rule_chain") -> dict:
    """{field: record of the cascade reader} of one block file (decision D1). A record is the to_json form of a
    reader result with the key cascade, or the record "not searched in this kind of document". `kind`: a key of
    the kinds of the cascade, None (not known: each field is searched) or "from_rule_chain". It needs no project
    file."""
    head = read_json(block_file)
    closed_guard(head.get("doc_id"), head.get("parliament"), [ROOT])
    vb.load_rule_modules()
    doc = vb.load_from_block_file(block_file, rule_file)
    return vcr.read_document(doc, kind=kind, strict=strict)["fields"]


def cascade_state(vdoc: "vb.Doc", values: dict, kind: str | None = "from_rule_chain") -> dict:
    """The label selection of one document (decision D1). Keys: kind, kind_source, affair_type_of_the_cascade,
    selection ({field: {searched, rules, slot, note}}, m11_values_cascade.selection), texts ({family: {applies,
    rules, slot, note, cut}}: the state of Submission.texts and ResponseStep.texts; cut is true if the cascade
    does not give the text slot to the kind) and steps ({family: {applies, rules, note}}). The kind source of a
    document with the S1 rule id D0 has the key v5 (rule V5 of the cascade reader). It stops if a record of
    `values` is not a record of the cascade reader for this selection."""
    if kind == "from_rule_chain":
        kind, source = vcr.kind_of(vdoc)
    else:
        if kind is not None and kind not in vcr.kinds():
            raise WriterStop(f"unknown kind {kind!r}; the kinds are {list(vcr.kinds())}")
        source = {"from": "argument", "rule": "V1" if kind is None else "argument"}
    t = values["affair_type"]
    t = t if isinstance(t, dict) else t.to_json()
    types = casc.cascade()["affair_types"]
    a_type = t["normalised"] if t.get("found") and t.get("normalised") in types and t["normalised"] != "none" else "none"
    sel = vcr.selection(kind, a_type)
    for f in FIELDS:
        c = values[f].get("cascade") if isinstance(values[f], dict) else None
        if not isinstance(c, dict) or bool(c.get("searched")) != sel[f]["searched"] or list(c.get("rules") or []) != sel[f]["rules"]:
            raise WriterStop(f"{f}: the value is not a record of the cascade reader for the kind {kind} and the type "
                             f"{a_type} (decision D1: read the values with read_values)")
        if not sel[f]["searched"] and (values[f].get("found") or values[f].get("reason") != "not_in_document_type"):
            raise WriterStop(f"{f}: the cascade does not search the field for the kind {kind}, but the record has a result")
    texts, steps = {}, {}
    if kind is None:
        for fam, (cls, _) in TEXT_SLOT.items():
            texts[fam] = {"applies": True, "rules": ["V1"], "slot": f"{cls}.texts", "note": "the kind is not known: no selection"}
            steps[fam] = {"applies": True, "rules": ["V1"], "note": "the kind is not known: no selection"}
    else:
        lab = casc.labels_for(kind, a_type)
        live = {(n["class"], n["slot"]): n for n in reversed(lab["affair"]["slots"] + [n for st in lab["steps"].values()
                                                                                         for n in st["slots"]])}
        cut = {x["path"].split("/")[-1]: x for x in lab["not_applicable"]}
        for fam, (cls, step) in TEXT_SLOT.items():
            st = lab["steps"][step]
            head_rules = [st["rules"][0], "R25"] + (["R31"] if step == "executive_response" and not st["applies"] else [])
            steps[fam] = {"applies": bool(st["applies"]), "rules": head_rules,
                          "note": "the step applies" if st["applies"] else f"the step {step} does not apply: {st['reason']}"}
            full = f"{cls}.texts"
            if (cls, "texts") in live:
                texts[fam] = {"applies": True, "rules": vcr._uniq(head_rules + list(live[(cls, "texts")]["rules"])),
                              "slot": full, "note": "the slot applies"}
            elif not st["applies"]:
                texts[fam] = {"applies": False, "rules": head_rules, "slot": full, "note": steps[fam]["note"]}
            elif full in cut:
                texts[fam] = {"applies": False, "rules": vcr._uniq(cut[full]["rules"]), "slot": full,
                              "note": f"the cascade cuts the slot for this {cut[full]['reason']}"}
            else:
                raise WriterStop(f"the cascade gives no state for the slot {full} at ({kind}, {a_type})")
    for fam in texts:
        # a text block is a part of the eCH-0295 instance only if the cascade gives its text slot to the kind
        # (decision of 13.10.2026; it includes decision D3 and replaces decision W-5)
        texts[fam]["cut"] = not texts[fam]["applies"]
    return {"kind": kind, "kind_source": source, "affair_type_of_the_cascade": a_type,
            "selection": {f: dict(sel[f]) for f in FIELDS}, "texts": texts, "steps": steps}


def value_form(doc: "vb.Doc", field: str, res) -> dict:
    """One result of a reader, or its to_json form, as a plain record. A candidate is made again with
    Doc.candidate, so that check_result examines the span, the page and the block."""
    if not isinstance(res, dict):
        vb.check_result(doc, field, res)
        res = res.to_json()
    if res.get("field") != field:
        raise vb.BadResult(f"{field}: the result is for the field {res.get('field')}")
    def found_form(x: dict) -> dict:
        c = doc.candidate(field, int(x["char_start"]), int(x["char_end"]), x["normalised"], x["tier"])
        if c.value != x["value"]:
            raise vb.BadResult(f"{field}: the document text at the span is not the wording of the result")
        return {"found": True, "value": c.value, "normalised": c.normalised,
                "record": record_value(field, c.value, c.normalised), "tier": c.tier, "page": c.page,
                "last_page": doc.locate(c.char_end - 1).page, "block": c.block, "char_start": c.char_start,
                "char_end": c.char_end}

    if not res.get("found"):
        if res.get("reason") not in vb.REASONS:
            raise vb.BadResult(f"{field}: unknown reason code {res.get('reason')!r}")
        out = {"found": False, "reason": res["reason"], "detail": str(res.get("detail") or ""),
               "others": len(res.get("others") or [])}
        # decision D3 (rule V3 of the cascade reader): the first addressee candidate of a proposal
        kept = [x for x in res.get("others") or [] if isinstance(x, dict) and x.get("tier") in vcr.ADDRESSEE_TIERS]
        if field == "responder" and res["reason"] == "not_in_document_type" and kept:
            out["addressee"] = found_form(kept[0])
        return out
    return found_form(res)


RX_COMPOUND_BREAK = re.compile(r"(?<=[a-zà-ÿ])-[ \t]*\n[ \t]*(?=[A-ZÀ-Ý][a-zà-ÿ])")


def title_one_line(wording: str, normalised: str) -> str:
    """The printed title on one line. It is norm_title of the title reader, with one more line-end case: a hyphen
    at a line end between a lower-case letter and a word with an upper-case first letter is a compound of two
    words, and the line end is not a space ("Basel-" + line end + "Stadt" gives "Basel-Stadt"; the reader gives
    "Basel- Stadt"). The result is used only if its comparison form (m11_value_norm.fold) is that of the reader
    value. Thus the calibration of the reader applies to it with no change."""
    v = mt.norm_title(RX_COMPOUND_BREAK.sub("-", wording))
    return v if vn.fold(v) == vn.fold(normalised) else normalised


def record_value(field: str, wording: str, normalised: str) -> str:
    """The value of a field in the eCH-0295 part (decisions W-1 and W-4). Responder and first author: the printed
    wording on one line (m11_values_base.norm_text: NFKC, no soft hyphen, a hyphen at a line end joined, each run
    of white space as one space; case and accents stay). Title: the printed wording on one line (title_one_line).
    Each other field: the value of the reader. It is the list value of the printed type word, the printed number
    with no space at a separator, or the ISO day of the printed date."""
    if field in PRINTED_FIELDS:
        return vb.norm_text(wording)
    if field == "title":
        return title_one_line(wording, normalised)
    return normalised


def tier_probability(field: str, tier: str, calibration: dict) -> float:
    """The stored probability of the calibration file for the pair (field, tier): p_all_folds of the tier, or the
    value of a tier with no unit. It is the same for each document. The floor uses it (decision W-3)."""
    look = calibration["lookup"][CALIBRATION_FIELD.get(field, field)]
    t = (look.get("tiers") or {}).get(tier)
    return float(t["p_all_folds"] if t else look["p_of_a_tier_with_no_unit"])


def weak_tier(field: str, tier: str, calibration: dict) -> bool:
    """Decision W-3: True if the stored probability of the pair is below FLOOR_P. Such a value is not written."""
    return tier_probability(field, tier, calibration) < FLOOR_P


# ------------------------------------------------------------------ interface: cross-check (record form chapter 4)
def _evidence(raw: list, export_record: dict) -> list[dict]:
    """The export fields of a reference as MetadataEvidence (m06_ech_ausgabe.beleg_meta)."""
    when = export_record.get("export_retrieved_utc") or ""
    affair, body = export_record.get("affair") or {}, export_record.get("body") or {}
    out = []
    for r in raw:
        src, value = str(r.get("source") or ""), r.get("value")
        if value is None or str(value).strip() == "":
            continue
        if src.startswith("affairs."):
            out.append(ea.beleg_meta(mc.AFFAIRS_FILE, "affair", affair.get("id"), src[len("affairs."):], value, when))
        elif src.startswith("events.date"):
            out.append(ea.beleg_meta(mc.EVENTS_FILE, "event", r.get("event_id"), "date", value, when))
        elif src.startswith("bodies."):
            out.append(ea.beleg_meta(BODIES_FILE, "body", body.get("id"), src[len("bodies."):], value, when))
        elif src.startswith("contributors."):
            out.append(ea.beleg_meta(CONTRIBUTORS_FILE, "contributor", r.get("row_id"), "lastname", value, when))
    return out


def reference(field: str, export_record: dict, language) -> dict | None:
    """The reference of one field (rule G2) through the functions ref_* of src/m11_value_reference.py, and the
    export values as the export states them. None: the field has no comparison (no contributor rows)."""
    import m02_ech_regeln as er  # noqa: PLC0415
    import m11_value_reference as vr  # noqa: PLC0415
    affair = export_record.get("affair") or {}
    events, body = export_record.get("events") or [], export_record.get("body") or {}
    if field == "affair_type":
        e = vr.ref_affair_type(affair, er.typ_ech)
        stated = [r["value"] for r in e["raw"] if r["source"] == "m02_ech_regeln.typ_ech" and r["value"]]
    elif field == "title":
        e = vr.ref_title(affair, language)
        stated = [r["value"] for r in e["raw"] if vr.not_empty(r["value"])]
    elif field == "affair_number":
        e = vr.ref_affair_number(affair)
        stated = [r["value"] for r in e["raw"] if r["used"]]
    elif field == "submission_date":
        e = vr.ref_submission_date(affair, events)
        stated = list(e["values"])
    elif field == "response_date":
        e = vr.ref_response_date(events)
        stated = list(e["values"])
    elif field == "responder":
        e = vr.ref_responder(body)
        stated = [r["value"] for r in e["raw"] if r["normalised"]]
    elif field == "sponsor":
        if "contributors" not in export_record:
            return None
        e = vr.ref_first_author(export_record.get("contributors") or [])
        stated = [r["value"] for r in e["raw"] if r["normalised"]]
    else:
        raise ValueError(f"unknown field {field}")
    return {"entry": e, "stated": [str(s) for s in dict.fromkeys(stated)]}


def cross_check(field: str, record_value, export_record, language) -> dict:
    """Record form chapter 4. The result for one field of one record: export_check (None if record_value is
    None), export_value (the export value as the export states it, or None), has_reference (None with no
    comparison), evidence (MetadataEvidence of the export fields) and detail. It changes no value."""
    check = None if record_value is None else "not_compared"
    if export_record is None:
        return {"export_check": check, "export_value": None, "has_reference": None, "evidence": [],
                "detail": {"reason": "no_export_record"}}
    ref = reference(field, export_record, language)
    if ref is None:
        return {"export_check": check, "export_value": None, "has_reference": None, "evidence": [],
                "detail": {"reason": "no_contributor_rows_in_the_export_record"}}
    e = ref["entry"]
    has = bool(e["values"])
    if record_value is None or not has:
        return {"export_check": None if record_value is None else "no_export_value", "export_value": None,
                "has_reference": has, "evidence": [], "detail": {"reason": e.get("reason")}}
    res = vn.compare(field, record_value, e["values"])
    return {"export_check": "equal_to_export" if res["equal"] else "differs_from_export",
            "export_value": " | ".join(ref["stated"]), "has_reference": True, "evidence": _evidence(e["raw"], export_record),
            "detail": {k: v for k, v in res.items() if k != "equal"}}


def evidence_problems(evidence: list[dict], export_record: dict) -> list[str]:
    """Each MetadataEvidence entry against the export record (the value must be the value of the export)."""
    affair, body = export_record.get("affair") or {}, export_record.get("body") or {}
    bad = []
    for ev in evidence:
        kind, rid, name = ev["record_type"], ev["record_id"], ev["field_name"]
        if kind == "affair":
            rows = [affair] if str(affair.get("id")) == rid else []
        elif kind == "body":
            rows = [body] if str(body.get("id")) == rid else []
        elif kind == "event":
            rows = [x for x in export_record.get("events") or [] if str(x.get("id")) == rid]
        else:
            rows = [x for x in export_record.get("contributors") or [] if str(x.get("id")) == rid]
        if len(rows) != 1 or str(rows[0].get(name)) != ev["source_value"]:
            bad.append(f"metadata evidence {kind} {rid} {name}: the export record does not give this value")
    return bad


# ------------------------------------------------------------------ interface: probability (record form chapter 3.2)
def probability(field: str, tier: str, calibration: dict, doc_id, s1_rule_role) -> dict:
    """The lookup rule of record form chapter 3.2 (decision D4): the stored value of the rule tier over all folds,
    for each document, also for a development document. The fold value of a development document is a detail of
    the measurement and is not used. Keys: left_out (rule G7 item 6), p (as written), status, id (calibration
    id), source ("all folds" or "no unit of the pair") and in_sample (True: the document is a unit of the pair in
    the calibration file, so the number of the tier counts this document)."""
    f = CALIBRATION_FIELD.get(field, field)
    look = calibration["lookup"][f]
    if look["entry"] == "left_out_not_measured":
        return {"left_out": True}
    t = (look.get("tiers") or {}).get(tier)
    stored = ((calibration.get("documents") or {}).get(str(doc_id)) or {}).get(f) if doc_id is not None else None
    in_sample = bool(stored and stored.get("tier") == tier and stored.get("outcome") in ("equal", "different"))
    p = t["p_all_folds"] if t else look["p_of_a_tier_with_no_unit"]
    primary = field not in PRIMARY_ROLE_FIELDS or s1_rule_role in PRIMARY_ROLES
    certain = (look["entry"] == "written_with_status" and primary and look["a"] is not None and t is not None
               and p >= look["a"] and t["enough_units"] and t["certain_tier"])
    return {"left_out": False, "p": cal.as_written(p), "status": "certain" if certain else "unsure",
            "id": cal.cal_id("value", f, tier), "source": PROBABILITY_FROM if t else "no unit of the pair",
            "in_sample": in_sample}


def calibration_record(cid: str, field: str, tier: str, calibration: dict, predicate: str, p: float,
                       in_sample: bool = False) -> dict:
    """The Calibration node of one pair (field, tier): the record of the file, or a record of the writer for a
    pair with no unit (record form chapter 3.2, rules 10 and 11). `in_sample`: the document of the record is a
    unit of the pair (decision D4: the shown number is the value of all folds, so it counts this document). The
    node does not get the 5 fold values of the file (parameters jeffreys_mean_without_fold_0 to _4): they are a
    detail of the measurement, the record does not show them and no reader of the record uses them (finding
    S3-09). The sentence of the file about the fold value of a document is replaced by the sentence of decision
    D4. The note of the node gets the origin text of the calibration file (decision D5), if the file is not a
    stand-in."""
    c = (calibration.get("calibrations") or {}).get(cid)
    if c is not None:
        out = dict(c) | {"calibrated_slot": predicate, "in_sample": bool(in_sample)}
        if "calibration_parameters" in c:
            out["calibration_parameters"] = [x for x in c["calibration_parameters"]
                                             if not str(x.get("parameter_name")).startswith(FOLD_PARAMETER)]
        note = str(c.get("calibration_note") or "")
        note = note.replace(FOLD_SENTENCE, ALL_FOLDS_SENTENCE) if FOLD_SENTENCE in note else f"{note} {ALL_FOLDS_SENTENCE}"
        if not str(calibration.get("label") or "").startswith("STAND-IN"):
            note = f"{note} Origin: {CALIBRATION_ORIGIN}" + (f" {APERTUS_ORIGIN}" if av.is_apertus_tier(tier) else "")
        out["calibration_note"] = note.strip()
        return out
    f = CALIBRATION_FIELD.get(field, field)
    values = ((calibration.get("inputs") or {}).get("values")) or {}
    out = {"calibration_method": "jeffreys_tier_precision", "calibrated_kind": "pdf_value", "calibrated_slot": predicate,
           "calibrated_tier": tier}
    if values.get("path"):
        out |= {"fit_set_file": values["path"], "fit_set_digest": values.get("sha256") or ""}
    out["fit_n"] = 0
    if calibration.get("reference"):
        out["reference_source"] = str(calibration["reference"])
    out |= {"in_sample": False, "target_status": "not_measured",
            "calibration_parameters": [{"parameter_name": "jeffreys_mean_all_folds", "parameter_value": float(p)},
                                       {"parameter_name": "k", "parameter_value": 0.0},
                                       {"parameter_name": "n", "parameter_value": 0.0}],
            "calibration_note": f"The calibration file has no unit of the pair ({f}, {tier}): Jeffreys mean of 0 of 0. "
                                f"Each value of the pair is unsure."}
    return out


# ------------------------------------------------------------------ rules mode: the floor decisions of one rule file
def rules_mode_decisions(rule_file, out_file, floor_file=None, root=None) -> Path:
    """Rules mode: the decisions file (interface 7) of one rule file through m10_cascade.floor_decisions with the
    floor calibration file (the steps of m10_pipeline.load_floor and checked). Writes out_file."""
    import m10_cascade as cascade  # noqa: PLC0415
    root = Path(root or ROOT).resolve()
    p = Path(floor_file or root / FLOOR_REL).resolve()
    if not p.is_file():
        raise WriterStop(f"no floor calibration file {p}")
    calib = read_json(p)
    if "floor_lookup" not in calib or "calibrations" not in calib:
        raise WriterStop(f"{p.name} has no key floor_lookup or calibrations")
    fit_p = next((b / calib["fit_set"]["path"] for b in (root, ROOT) if (b / calib["fit_set"]["path"]).is_file()), None)
    if fit_p is None or sha256(fit_p) != calib["fit_set"]["sha256"]:
        raise WriterStop("the fit set file of the floor calibration file is absent or has another SHA-256")
    fit_docs = {str(x) for x in read_json(fit_p)["documents"]}
    rules = read_json(rule_file)
    info = {"path": path_text(p, root), "sha256": sha256(p), "version": calib.get("version")}
    dec = cascade.floor_decisions(rules, cal.FloorLookup(calib), str(rules["doc_id"]) in fit_docs, info)
    bad = cascade.check_decisions(dec, rules)
    if bad:
        raise WriterStop(f"decisions check of src/m10_cascade.py failed: {bad[:5]}")
    write_json(out_file, dec)
    return Path(out_file)


# ------------------------------------------------------------------ the record
def record_iris(doc_id: str | None, base: str | None, pdf_sha256: str) -> dict:
    """Record form chapter 2.1. Each IRI of the record is below the record IRI."""
    if base is not None and doc_id is not None:
        source = f"{ea.OPD}docs/{doc_id}"
        rec = f"{base}gj/record/doc-{doc_id}"
    else:
        if not RX_SHA.match(pdf_sha256 or ""):
            raise WriterStop("pdf_sha256 is not a SHA-256")
        source = IRI_PREFIX + pdf_sha256
        rec = f"{source}/record"
    return {"source": source, "record": rec, "container": f"{rec}/i95", "affair": f"{rec}/affair",
            "submission": f"{rec}/affair/step/submission", "response": f"{rec}/affair/step/response",
            "responder": f"{rec}/actor/responder", "sponsor": f"{rec}/actor/sponsor-1", "extraction": f"{rec}/extraction",
            "label_record": f"{rec}/label-record", "run": f"{rec}/run",
            "named_graphs": {g: f"{rec}/{g}" for g in GRAPHS}}


def minted(what: str) -> dict:
    return {"derivation": "identifier_minted",
            "rule": f"<record IRI>/{what} (deterministic; record_form.md chapter 2.1; {SCRIPT})"}


def span_evidence(lines: list[dict], text: str, start: int, end: int) -> list[dict]:
    """Record form chapter 5, items 4 and 5: one AtomEvidence for each line of the atom file that the span
    touches. The key zeichen of a line is its range in the document text."""
    out = []
    for a in lines:
        z0, z1 = a["zeichen"]
        if z1 <= start or z0 >= end or not (a.get("text") or ""):
            continue
        if text[z0:z1] != a["text"]:
            raise WriterStop(f"line {a['id']}: the document text at its range is not the line text")
        out.append(ea.atom_beleg(a, (max(start, z0) - z0, min(end, z1) - z0)))
    if not out:
        raise WriterStop(f"the span {start}:{end} touches no line of the atom file")
    return out


def slot_list(names: list[str], fstate: dict, cstate: dict, texts: dict, written: dict) -> list[dict]:
    """The key slots of the manifest (record form chapter 6): one entry for each slot of the 3 classes. An entry
    with the state not_in_this_document_type that comes from the cascade has 3 more keys (decision D1): result
    ("not searched in this kind of document"), kind and cascade_rules."""
    out = []

    def texts_entry(family: str) -> tuple[str, str, list | None]:
        if texts[family]:
            return "read_from_pdf", "text_blocks", None
        if not cstate["texts"][family]["applies"]:
            return NOT_IN_TYPE, NOT_IN_TYPE, cstate["texts"][family]["rules"]
        return "not_found_in_pdf", "no_block_of_role", None

    def step_entry(family: str) -> tuple[str, str, list | None]:
        if written[family]:
            return "read_from_pdf", "step_written", None
        if not cstate["steps"][family]["applies"]:
            return NOT_IN_TYPE, NOT_IN_TYPE, cstate["steps"][family]["rules"]
        return "not_found_in_pdf", "no_value_of_the_step", None

    for full in names:
        cls, slot = full.split(".", 1)
        family = {"Submission": "submission", "ResponseStep": "response"}.get(cls)
        field = FIELD_OF_SLOT.get(full)
        label_id = gap_id = rules = None
        if field is not None:
            st = fstate[field]
            state, reason = st["state"], st["reason"]
            label_id = {"value": f"pdf-{field}", "weak": f"candidate-{field}",
                        "addressee": f"candidate-{field}"}.get(st["kind"])
            gap_id = field if st["kind"] in ("gap", *CANDIDATE_KINDS) else None
            if not cstate["selection"][field]["searched"]:
                rules = cstate["selection"][field]["rules"]
        elif slot == "texts" and family:
            state, reason, rules = texts_entry(family)
        elif full in ("Affair.submission", "Affair.response_steps"):
            state, reason, rules = step_entry("submission" if slot == "submission" else "response")
        elif slot == "global_uri":
            state, reason = "register_only", "minted_iri"
        elif slot in REGISTER_ONLY:
            state, reason = "register_only", "register_only"
        elif cls == "Affair" and slot in OTHER_STEPS:
            state, reason = "not_in_this_document_type", "not_in_this_document_type"
        elif slot in NO_RULE:
            state, reason = "not_found_in_pdf", "no_rule_searched"
        else:
            raise WriterStop(f"slot {full} of I95 has no rule in the slot table of the record form (chapter 6)")
        entry = {"slot": full, "state": state, "reason": reason, "field": field, "label_id": label_id, "gap_id": gap_id}
        if rules is not None:
            entry |= {"result": NOT_SEARCHED, "kind": cstate["kind"], "cascade_rules": list(rules)}
        out.append(entry)
    return out


def build(d: str, known: bool, doc: dict, vdoc, rules: dict | None, dec: dict, values: dict, calibration: dict,
          exp: dict | None, cals: dict, base: str | None, calibration_base: str, files: dict, root: Path,
          kind: str | None = "from_rule_chain", apertus_backend: str | None = None) -> dict:
    """The instance, the provenance file, the label file and the manifest parts of one document.
    apertus_backend (W3, W4): the backend name that the Apertus provider gives (mlx, cuda, mps, cpu, stored,
    remote:<backend>); the notes of the Apertus values name it."""
    cstate = cascade_state(vdoc, values, kind)
    kind = cstate["kind"]
    iri = record_iris(d if known else None, base if known else None, doc["pdf_sha256"])
    record, doc_iri, run_iri = iri["record"], iri["source"], iri["run"]
    atoms_file = read_json(files["atoms"]["abs"])
    atoms_list = atoms_file["atome"]
    by_id = {a["id"]: a for a in atoms_list}
    lines = [dict(a, ocr=mc.from_ocr(a)) for a in atoms_list]
    fixed = v4.fixed_answers(d)
    blocks, decided = doc["blocks"], dec["blocks"]
    options = [b["option"] for b in decided]
    text = vdoc.text
    lang = doc.get("language") if doc.get("language") in ea.SPRACHEN else None
    lang_h = {"derivation": "detected_by_rule", "rule": "language of the block file (rule of the converter; no export field)"}
    s1_role = ((rules or {}).get("document") or {}).get("s1", {}).get("rule_role")
    iri_of = rdf.slot_iris(rdf.WRAPPER)
    predicate = {f: iri_of[row[1]] for f, row in FIELD_TABLE.items()}
    rule_id = {f: f"{vb.REGISTRY[f].__module__}.read_{f}" if f in vb.REGISTRY else "no reader" for f in FIELDS}
    type_values = ea.enum_werte("i95", "AffairTypeEnum")
    problems: list[str] = []
    notes: list[str] = []
    not_mapped: list[dict] = []

    # ---------------------------------------------------------------- probabilities of the block labels
    def status(p: float, cid: str) -> str:
        t = cals[cid].get("certain_threshold")
        return "certain" if t is not None and p >= float(t) else "unsure"

    r2 = dec.get("r2")
    has_response = any(fw.FAMILY.get(o) == "response" for o in options)
    r2_agree = None if r2 is None else (r2["p"] >= 0.5) == has_response
    unsure_by_r2 = {i for i, o in enumerate(options) if fw.FAMILY.get(o) == "response"} if r2_agree is False else set()
    block_status = {}
    for i, b in enumerate(decided):
        block_status[i] = "unsure" if i in unsure_by_r2 else status(fw.clip(b["probs"][b["option"]]), b["calibration"])

    # ---------------------------------------------------------------- author blocks (as src/m10_writer.py, item 3)
    runs = fw.author_runs(options)
    tb_records: list[dict] = []
    texts: dict[str, list] = {"submission": [], "response": []}
    e19 = {"text_blocks": 0, "characters": 0, "hyphens": 0, "markers": 0, "problems": []}
    run_of_block: dict[int, dict] = {}
    for k, (opt, idx) in enumerate(runs, 1):
        ids = [a for i in idx for a in blocks[i]["atoms"] if a not in fixed]
        r = {"k": k, "option": opt, "blocks": [blocks[i]["block"] for i in idx], "idx": idx, "ids": ids,
             "global_uri": f"{record}/textblock/{k}", "mapping_status": "profile_only"}
        for i in idx:
            run_of_block[i] = r
        if not any((by_id[a].get("text") or "").strip() for a in ids):
            r["not_mapped_reason"] = "The blocks of the author block have no text atom (all atoms are fixed or empty)"
            r["text"], r["tc"] = "", {"hyphens_removed": [], "list_markers_removed": [], "empty_atoms": list(ids),
                                      "nfc_changed": False}
            tb_records.append(r)
            continue
        wording, ch = mc.block_text(d, ids)
        tc = mc.profile_changes(ch)
        bad = mc.e19_problems(d, by_id, ids, wording, tc)
        tsel = cstate["texts"][fw.FAMILY[opt]]
        if tsel["cut"]:
            # the cascade gives the text slot of this block not to the kind of the document: the text block stays
            # a TextBlockRecord of the provenance file and is not a part of the eCH-0295 instance
            e19["problems"] += [f"author block {k}: {b}" for b in bad]
            r |= {"text": wording, "tc": tc, "cut_by_cascade": True,
                  "not_mapped_reason": f"{NOT_SEARCHED}: the kind {kind} cannot state the slot {tsel['slot']} "
                                       f"({tsel['note']}; cascade rules {', '.join(tsel['rules'])})"}
            tb_records.append(r)
            continue
        e19["text_blocks"] += 1
        e19["characters"] += len(gr.signature_text(wording))
        e19["hyphens"] += len(tc["hyphens_removed"])
        e19["markers"] += len(tc["list_markers_removed"])
        e19["problems"] += [f"author block {k}: {b}" for b in bad]
        r |= {"text": wording, "tc": tc}
        tb_records.append(r)
        label_iris = ", ".join(f"{record}/label/{blocks[i]['block']}-slot" for i in idx)
        new = {"text": V(wording, {"derivation": "extracted_from_pdf", "_record": r,
                                   "rule": f"author block {k} (option {opt}; Docling blocks {', '.join(r['blocks'])}): wording "
                                           f"of its lines without fixed lines with m03_gold_record.richtext (G19, without "
                                           f"G20a), as src/m10_writer.py; evidence in the TextBlockRecord {r['global_uri']}"})}
        if lang:
            new["text_language"] = V(lang, dict(lang_h))
        new["text_type"] = V(opt, {"derivation": "fixed_by_schema",
                                   "rule": f"text type of the author block = option {opt} of its blocks in the decisions "
                                           f"file (mode {dec['mode']}); the probabilities are in the label graph: "
                                           f"{label_iris}"})
        r["mapping_status"] = "in_ech_instance"
        r["family"] = fw.FAMILY[opt]
        texts[fw.FAMILY[opt]].append(new)

    # ---------------------------------------------------------------- the 7 fields: value, gap record or not read
    fstate: dict[str, dict] = {}
    for f in FIELDS:
        v = value_form(vdoc, f, values[f])
        st: dict = {"field": f, "rule_id": (av.rule_id_of(v.get("tier")) or rule_id[f]) if v["found"] else rule_id[f]}
        if not v["found"]:
            if v["reason"] in NOT_READ_OF_REASON:
                st |= {"kind": "not_read", "state": "not_found_in_pdf", "reason": NOT_READ_OF_REASON[v["reason"]],
                       "note": f"reader reason {v['reason']}: {v['detail']}".rstrip(": ")}
            else:
                state, reason = GAP_OF_REASON[v["reason"]]
                st |= {"kind": "gap", "state": state, "reason": reason, "candidates": v["others"],
                       "note": f"reader reason {v['reason']}: {v['detail']}".rstrip(": ")}
                if v["reason"] == "not_in_document_type" and cstate["selection"][f]["searched"]:
                    # finding S3-01: the cascade searches the value; the reason of the rule is a result of a search
                    st |= {"state": "not_found_in_pdf", "reason": SCOPE_REASON, "gap_reason": SCOPE_GAP_REASON,
                           "note": f"{SCOPE_MARK} (reader reason {v['reason']}): {v['detail']}".rstrip(": ")}
                elif v["reason"] == "not_in_document_type":
                    st["note"] = f"{NOT_SEARCHED}: {v['detail']}"
                    if v.get("addressee"):
                        # decision D3: the addressed body is a candidate label; no response step is written
                        a = v["addressee"]
                        pr = probability(f, a["tier"], calibration, d if known else None, s1_role)
                        if not pr["left_out"] and lang is not None and vn.body_word(a["record"]) is not None:
                            st |= {"kind": "addressee", "v": a, "pr": pr, "candidates": 1,
                                   "note": f"{NOT_SEARCHED}: {v['detail']}; {ADDRESSEE_MARK}; the candidate is the "
                                           f"label candidate-{f}"}
            fstate[f] = st
            continue
        pr = probability(f, v["tier"], calibration, d if known else None, s1_role)
        why = None
        if f == "affair_type" and v["normalised"] not in type_values:
            why = "the type value of the reader is not in the AffairTypeEnum of I95"
        elif f in ("responder", "sponsor") and lang is None:
            why = "the block file has no language, and I95 requires text_language for a name"
        elif f in ("submission_date", "response_date") and not RX_DAY.match(v["normalised"]):
            why = "the date of the reader does not have the form YYYY-MM-DD"
        elif f == "responder" and vn.body_word(v["record"]) is None:
            why = "the printed wording at the span has no body word of table 3 of addendum G"
        if pr["left_out"]:
            st |= {"kind": "not_read", "state": "not_found_in_pdf", "reason": "field_not_measured",
                   "note": "the calibration file leaves the field out (rule G7 item 6): no value is written"}
        elif why:
            st |= {"kind": "gap", "state": "not_found_in_pdf", "reason": "candidate_not_valid", "candidates": 1,
                   "note": f"writer: {why}"}
        elif weak_tier(f, v["tier"], calibration):
            # decision W-3: the candidate stays in the label file; the eCH-0295 part does not get it
            st |= {"kind": "weak", "state": "not_found_in_pdf", "reason": WEAK_REASON, "candidates": 1,
                   "v": v, "pr": pr, "tier_p": tier_probability(f, v["tier"], calibration),
                   "note": f"{WEAK_MARK} (tier {v['tier']}: stored probability "
                           f"{tier_probability(f, v['tier'], calibration):.4f}, below {FLOOR_P}); the candidate is the "
                           f"label candidate-{f}"}
        else:
            st |= {"kind": "value", "state": "read_from_pdf", "reason": "value_read", "v": v, "pr": pr}
        fstate[f] = st
    for f, st in fstate.items():
        cc = cross_check(f, st["v"]["normalised"] if st["kind"] == "value" else None, exp, lang)
        st["cc"] = cc
        if exp is not None:
            problems += evidence_problems(cc["evidence"], exp)
    has = {f: fstate[f]["kind"] == "value" for f in FIELDS}

    def field_v(f: str, extra: dict | None = None) -> V:
        st = fstate[f]
        v, cc = st["v"], st["cc"]
        h = {"derivation": "extracted_from_pdf_by_rule", "_field": f,
             "rule": f"{st['rule_id']}, tier {v['tier']}; normalisation {FIELD_TABLE[f][3]}"
                     + (f"; {av.apertus_note(f, values[f], apertus_backend)}" if av.is_apertus_tier(v["tier"]) else "")
                     + (f"; comparison value of the reader {v['normalised']!r} (cross-check and calibration only)"
                        if f in PRINTED_FIELDS or v["normalised"] != v["record"] else ""),
             "match": "exact" if f == "affair_type" else "not_applicable",
             "pdf_evidence": span_evidence(lines, text, v["char_start"], v["char_end"]),
             "konsistenz": CONSISTENCY[cc["export_check"]]}
        if cc["export_check"] in ("equal_to_export", "differs_from_export"):
            h["metadata_evidence"] = cc["evidence"]
        if cc["export_check"] == "differs_from_export":
            h["alternativen"] = [{"alternative_value": cc["export_value"],
                                  "alternative_source": "OpenParlData export, " + ", ".join(
                                      dict.fromkeys(f"{e['record_type']}.{e['field_name']}" for e in cc["evidence"])),
                                  "alternative_note": "cross-check value of the export; not a value of the record"}]
        return V(v["record"], h | (extra or {}))

    # ---------------------------------------------------------------- instance (I95 Container, one affair)
    type_value = fstate["affair_type"]["v"]["normalised"] if has["affair_type"] else None
    affair: dict = {"__entity__": (iri["affair"], ea.I95_KLASSE.get(type_value, "Affair")),
                    "global_uri": V(iri["affair"], minted("affair"))}
    if exp is not None and (exp.get("affair") or {}).get("id") is not None:
        aid = exp["affair"]["id"]
        register = f"{ea.OPD}affairs/{aid}"
        ev = [ea.beleg_meta(mc.AFFAIRS_FILE, "affair", aid, "id", aid, exp.get("export_retrieved_utc") or "")]
        problems += evidence_problems(ev, exp)
        affair["global_uri"].herkunft |= {
            "metadata_evidence": ev,
            "alternativen": [{"alternative_value": register,
                              "alternative_source": "OpenParlData export, affairs.id (register address of the affair)",
                              "alternative_note": "cross-check value; not an identifier that is read from the PDF"}]}
    else:
        register = None
    if has["affair_number"]:
        affair["affair_number"] = field_v("affair_number")
    if has["affair_type"]:
        affair["affair_type"] = field_v("affair_type")
    if has["title"]:
        t = {"text": field_v("title")}
        if lang:
            t["text_language"] = V(lang, dict(lang_h))
        t["text_type"] = V("title", {"derivation": "fixed_by_schema", "rule": "the title of the affair -> TextTypeEnum title"})
        affair["title"] = [t]
    written = {"submission": has["submission_date"] or has["sponsor"] or bool(texts["submission"]),
               "response": has["response_date"] or has["responder"] or bool(texts["response"])}
    if written["submission"]:
        sub: dict = {"__entity__": (iri["submission"], mc.STEP_CLASS["submission"]),
                     "global_uri": V(iri["submission"], minted("affair/step/submission"))}
        if has["submission_date"]:
            sub["submission_date"] = field_v("submission_date")
        if has["sponsor"]:
            sub["sponsorship"] = [{
                "actor": {"__entity__": (iri["sponsor"], "Actor"),
                          "global_uri": V(iri["sponsor"], minted("actor/sponsor-1")),
                          "name": [{"text": field_v("sponsor"), "text_language": V(lang, dict(lang_h))}]},
                "sponsor_role": V("sponsor", {"derivation": "fixed_by_schema",
                                              "rule": "the first author of the affair -> SponsorRoleEnum sponsor"})}]
        if texts["submission"]:
            sub["texts"] = texts["submission"]
        affair["submission"] = sub
    if written["response"]:
        resp: dict = {"__entity__": (iri["response"], mc.STEP_CLASS["response"]),
                      "global_uri": V(iri["response"], minted("affair/step/response"))}
        if has["response_date"]:
            resp["date_end_actual"] = field_v("response_date")
        if has["responder"]:
            resp["responder"] = {"__entity__": (iri["responder"], "Organization"),
                                 "global_uri": V(iri["responder"], minted("actor/responder")),
                                 "name": [{"text": field_v("responder"), "text_language": V(lang, dict(lang_h))}]}
        if texts["response"]:
            resp["texts"] = texts["response"]
        affair["response_steps"] = [resp]
    container = {"__entity__": (iri["container"], "Container"), "global_uri": V(iri["container"], minted("i95")),
                 "affairs": [affair]}
    entries, without = [], []
    instance = ea.entpacken(container, eintraege=entries, ohne=without)
    entity_iri = {"affair": iri["affair"], "submission": iri["submission"] if written["submission"] else None,
                  "response": iri["response"] if written["response"] else None}
    for path, ent, _, v in entries:
        if v.herkunft["derivation"] == "extracted_from_pdf":
            r = v.herkunft["_record"]
            r["instance_path"], r["about_entity"] = ea.pfad_text(path[:-1]), ent
        elif v.herkunft["derivation"] == "extracted_from_pdf_by_rule":
            st = fstate[v.herkunft["_field"]]
            st["instance_path"], st["about_entity"] = ea.pfad_text(path), ent
        if v.herkunft["derivation"] not in PDF_DERIVATIONS:
            problems.append(f"{ea.pfad_text(path)}: derivation {v.herkunft['derivation']} is not permitted (rule T)")
    problems += [f"{p}: leaf value with no provenance" for p in without]

    # ---------------------------------------------------------------- not-mapped records and the I95 gaps
    for f in FIELDS:
        st = fstate[f]
        if st["kind"] == "value":
            continue
        item = FIELD_TABLE[f][2]
        reason = f"{st['state']} ({st['reason']}); the slot stays empty"
        if st["kind"] == "weak":
            reason += f"; {WEAK_MARK}; the candidate is in the label file"
        elif st["state"] == NOT_IN_TYPE:
            reason = (f"{NOT_SEARCHED} (kind {kind}; cascade rules {', '.join(cstate['selection'][f]['rules'])}); the "
                      f"slot stays empty" + (f"; {ADDRESSEE_MARK}; the candidate is in the label file"
                                             if st["kind"] == "addressee" else ""))
        if f in GAP_CAUSE:
            cause = (GAP_CAUSE_WEAK if st["kind"] == "weak" else GAP_CAUSE)[f]
            reason = f"{cause} ({st['state']}, {st['reason']}); the slot stays empty (addendum A, rule A1)"
        not_mapped.append({"not_mapped_item": item, "not_mapped_reason": reason,
                           "candidate_source": f"value reader {st['rule_id']}"})
    gaps, gap_problems = gp.writer_gaps(instance, not_mapped, None)
    gaps = [{"slot": g["slot"], "cause": (GAP_CAUSE_WEAK if fstate[g["slot"]]["kind"] == "weak" else GAP_CAUSE)[g["slot"]],
             "local_value": None} for g in gaps]
    problems += gap_problems
    not_mapped.append({"not_mapped_item": "Document (FRBR work, expression, manifestation)", "not_mapped_reason":
                       "eCH-0295 has no slot for the source document of this record; the provenance file gives it",
                       "candidate_value": doc_iri, "candidate_source": "block file"})
    not_mapped.append({"not_mapped_item": "Sponsorships", "not_mapped_reason":
                       "The record holds the first author only, and only if the cascade searches it for the kind of "
                       "the document and a rule reads the name from the PDF (field sponsor). No rule reads the other "
                       "authors and the co-signatories.",
                       "candidate_source": f"value reader {rule_id['sponsor']}"})
    for b in decided:
        if b["option"] == "title":
            not_mapped.append({"not_mapped_item": f"Title block {b['block']}", "not_mapped_reason":
                               "A title block from the PDF goes to the label graph only; Affair.title comes from the "
                               "title reader (field title), not from the block option",
                               "candidate_value": f"{record}/block/{b['block']}",
                               "candidate_source": f"label {record}/label/{b['block']}-slot"})
    for r in tb_records:
        if r["mapping_status"] == "profile_only":
            not_mapped.append({"not_mapped_item": f"TextBlock of author block {r['k']} ({r['option']})",
                               "not_mapped_reason": r["not_mapped_reason"], "candidate_value": r["global_uri"],
                               "candidate_source": "TextBlockRecord"})

    # ---------------------------------------------------------------- provenance file (profile 0.2.0)
    fp = hashlib.sha256(json.dumps([[a["id"], a["zeichen"]] for a in atoms_list], separators=(",", ":"))
                        .encode("utf-8")).hexdigest()
    export_text = (f"export record {files['export']['path']} (SHA-256 {files['export']['sha256']}), for the cross-check "
                   f"only") if exp is not None else "no export record"
    pipeline_run = {
        "script_name": SCRIPT,
        "decomposition_source": f"block options of the decisions file {files['decisions']['path']} (SHA-256 "
                                f"{files['decisions']['sha256']}, mode {dec['mode']}); blocks {files['docs']['path']} "
                                f"(SHA-256 {files['docs']['sha256']}); head values of the value readers "
                                f"(src/m11_values_base.py); {export_text}"
                                + (f"; the choice of the Apertus values from the heads output {files['apertus_heads']['path']} "
                                   f"(SHA-256 {files['apertus_heads']['sha256']}; src/m12_apertus_values.py)"
                                   if "apertus_heads" in files else ""),
        "decomposition_accepted": False,
        "taxonomy_version": "record_form.md version 4: head values from the PDF by rule tiers; author blocks from the "
                            "options of the Docling blocks (the rule of m10_writer.author_runs)",
        "atom_version": f"{atoms_file.get('version', '')} {atoms_file.get('erzeugt_utc', '')}".strip(),
        "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": fw.utc_now()}
    src: dict = {"global_uri": doc_iri}
    if known:
        src["local_id"] = d
    edoc = (exp or {}).get("doc") or {}
    if edoc.get("url_oparl"):
        src["manifestation_url"] = ea.as_uri(edoc["url_oparl"])
    if (edoc.get("url") or "").startswith("http"):
        src["publisher_url"] = ea.as_uri(edoc["url"])
    src["file_sha256"] = doc["pdf_sha256"]
    if edoc.get("hash"):
        src["export_hash"] = edoc["hash"]
    src |= {"docling_json_sha256": atoms_file.get("quelle_sha256") or "", "atom_fingerprint": fp,
            "page_count": len(read_json(files["docling"]["abs"])["seiten"])}
    if lang:
        src["document_language"] = lang
        src["document_language_source"] = f"language of the block file {files['docs']['path']} (interface 2)"
    else:
        src["document_language_source"] = f"no language: the block file {files['docs']['path']} gives no language"
    src["document_kind"] = (f"{'development document' if known else 'PDF with no document number'}, mode {dec['mode']}, "
                            f"D1 option {dec['document']['d1']['option']} "
                            f"({fw.D1_OPTIONS[dec['document']['d1']['option']]}), S1 rule role {s1_role}")
    tbr = []
    for r in tb_records:
        x = {"global_uri": r["global_uri"]}
        if r["mapping_status"] == "in_ech_instance":
            x |= {"about_entity": r["about_entity"], "instance_path": r["instance_path"],
                  "ech_slot": f"{mc.STEP_CLASS[r['family']]}.texts", "ech_text_type": r["option"]}
        else:
            x["about_entity"] = iri["affair"]
        x |= {"section_key": r["option"], "mapping_status": r["mapping_status"]}
        if r.get("not_mapped_reason"):
            x["not_mapped_reason"] = r["not_mapped_reason"]
        x["extent_value_status"] = "certain" if all(block_status[i] == "certain" for i in r["idx"]) else "unsure"
        x["text_form"] = "richtext"
        if r["mapping_status"] == "profile_only":
            x["text_content"] = r["text"]
        x |= {"char_count": len(r["text"]), "source_document": doc_iri,
              "units": [{"unit_id": blocks[i]["block"], "unit_type": r["option"],
                         "atom_evidence": [mc.atom_ev(by_id[a]) for a in blocks[i]["atoms"] if a not in fixed]}
                        for i in r["idx"]],
              "text_changes": r["tc"]}
        x["units"] = [u for u in x["units"] if u["atom_evidence"]] or x["units"][:1]
        tbr.append(x)
    value_records, n_meta = [], 0
    for path, ent, slot, v in entries:
        h, w = v.herkunft, v.wert
        vr = {"about_entity": ent, "instance_path": ea.pfad_text(path), "ech_slot": slot,
              "recorded_value": f"sha256:{sha256_text(w)}" if h["derivation"] == "extracted_from_pdf" else str(w),
              "derivation": h["derivation"]}
        if h.get("rule"):
            vr["rule_applied"] = h["rule"]
        vr["mapping_match"] = h.get("match", "not_applicable")
        if h.get("metadata_evidence"):
            vr["metadata_evidence"] = h["metadata_evidence"]
            n_meta += len(h["metadata_evidence"])
        if h.get("pdf_evidence"):
            vr["pdf_evidence"] = h["pdf_evidence"]
        vr["pdf_consistency"] = h.get("konsistenz", "not_checked")
        if h.get("alternativen"):
            vr["alternatives"] = h["alternativen"]
        value_records.append(vr)
    check_passed = not problems and not e19["problems"]
    prov = {"global_uri": iri["extraction"], "describes_delivery": iri["container"],
            "ech_schema_version": ea.FASSUNG_TEXT["i95"], "pipeline_run": pipeline_run, "source_documents": [src],
            "text_block_records": tbr, "value_records": value_records, "not_mapped_records": not_mapped,
            "verbatim_check": {
                "check_method": "Each leaf value needs a ValueRecord with a derivation that is not from the export. Each "
                                "head value: the document text at its span is its wording, and each line of the span "
                                "is in pdf_evidence. Each author block: its letters (no markup, no white space) are the "
                                "letters of the Docling wording of its lines (without fixed lines) after the recorded "
                                "changes only (line-end hyphens, list markers at the line start, empty lines, NFC). "
                                "Each metadata_evidence entry of the cross-check against the export record.",
                "text_blocks_checked": e19["text_blocks"], "characters_checked": e19["characters"],
                "hyphens_removed_count": e19["hyphens"], "list_markers_removed_count": e19["markers"],
                "metadata_values_checked": n_meta, "leaves_without_provenance": len(without),
                "check_passed": check_passed}}

    # ---------------------------------------------------------------- label file (label schema 0.2.0)
    pages = [b["page"] for b in blocks]
    whole = {"page": min(pages), "last_page": max(pages), "span_start": min(b["char_start"] for b in blocks),
             "span_end": max(b["char_end"] for b in blocks)}

    def prob_label(gid, subject, pred, obj, kind, x, probs, extra) -> dict:
        p = fw.clip(probs[obj])
        cid = str(x["calibration"])
        la = {"global_uri": gid, "label_subject": subject, "label_predicate": pred, "label_object": obj,
              "label_kind": kind, "label_source": fw.SOURCE[x.get("source", "apertus_head")], "label_probability": p,
              "option_probabilities": [{"option_value": k, "label_probability": fw.clip(v)} for k, v in probs.items()],
              "value_status": status(p, cid), "calibration": f"{calibration_base}calibration/{cid}", "model_run": run_iri}
        return la | extra

    labels = []
    d1 = dec["document"]["d1"]
    d1_label = prob_label(f"{record}/label/d1", doc_iri, f"{fw.PLB}documentTextParts", d1["option"],
                          "document_text_parts", d1, d1["probs"], {})
    if d1.get("rule_id"):
        d1_label["rule_id"] = str(d1["rule_id"])
    d1_label |= whole
    if r2_agree is False:
        d1_label["value_status"] = "unsure"
        d1_label["label_note"] = "unsure: the final check R2 does not agree with the block path"
    labels.append(d1_label)
    if r2 is not None:
        yes = r2["p"] >= 0.5
        r2_label = prob_label(f"{record}/label/r2", doc_iri, f"{fw.PLB}executiveResponse", "yes" if yes else "no",
                              "executive_response", {"calibration": r2["calibration"], "source": "apertus_head"},
                              {"yes": r2["p"], "no": 1 - r2["p"]}, whole)
        r2_label["label_note"] = ("final check R2 (frozen head H): the document holds a response of the executive"
                                  + ("; it agrees with the block path" if r2_agree else
                                     "; it does not agree with the block path"))
        labels.append(r2_label)
    for i, (b, x) in enumerate(zip(blocks, decided, strict=True)):
        extra = {"page": b["page"], "span_start": b["char_start"], "span_end": b["char_end"]}
        if x.get("tier"):
            extra["tier"] = str(x["tier"])
        if known and isinstance(x.get("in_sample"), bool):
            extra["in_sample"] = x["in_sample"]
        r = run_of_block.get(i)
        if r is not None and r.get("instance_path") and x["option"] == r["option"]:
            extra |= {"about_entity": r["about_entity"], "instance_path": r["instance_path"]}
        la = prob_label(f"{record}/label/{b['block']}-slot", f"{record}/block/{b['block']}", f"{fw.AFF}textType",
                        x["option"], "block_slot", x, x["probs"], extra)
        if i in unsure_by_r2:
            la["value_status"] = "unsure"
            la["label_note"] = "unsure: the final check R2 does not agree with the block path"
        labels.append(la)
    pos = {b["block"]: i for i, b in enumerate(blocks)}
    boundary_source = "code" if dec["mode"] == "cascade" else "rule"
    for x in dec.get("boundaries") or []:
        i = pos[x["after_block"]]
        a, n = blocks[i], blocks[i + 1]
        labels.append(prob_label(f"{record}/label/switch-after-{a['block']}", f"{record}/boundary/after-{a['block']}",
                                 f"{fw.PLB}authorSwitch", "switch", "author_switch",
                                 x | {"source": x.get("source", boundary_source)},
                                 {"switch": x["p"], "no_switch": 1 - x["p"]},
                                 {"page": n["page"], "last_page": max(a["page"], n["page"]),
                                  "span_start": min(a["char_end"], n["char_start"]),
                                  "span_end": max(a["char_end"], n["char_start"]),
                                  "label_note": f"switch between block {a['block']} and block {n['block']}"}))
    value_cals: dict[str, dict] = {}
    for path, ent, _, v in entries:
        h = v.herkunft
        name = next(x for x in reversed(path) if isinstance(x, str))
        ptext = ea.pfad_text(path)
        if h["derivation"] == "extracted_from_pdf":
            r = h["_record"]
            bl = [blocks[i] for i in r["idx"]]
            labels.append({"global_uri": f"{record}/label/textblock-{r['k']}-text", "label_subject": r["global_uri"],
                           "label_predicate": iri_of["text"], "label_object": f"sha256:{sha256_text(v.wert)}",
                           "label_kind": "text_wording", "label_source": "copy", "model_run": run_iri,
                           "page": min(b["page"] for b in bl), "last_page": max(b["page"] for b in bl),
                           "span_start": min(b["char_start"] for b in bl), "span_end": max(b["char_end"] for b in bl),
                           "about_entity": ent, "instance_path": ptext,
                           "label_note": "verbatim copy of the lines of the author block (check E19); the text changes "
                                         "are in the TextBlockRecord"})
        elif h["derivation"] == "extracted_from_pdf_by_rule":
            f = h["_field"]
            st = fstate[f]
            val, pr, cc = st["v"], st["pr"], st["cc"]
            cid = pr["id"]
            value_cals[cid] = calibration_record(cid, f, val["tier"], calibration, predicate[f], pr["p"], pr["in_sample"])
            la = {"global_uri": f"{record}/label/pdf-{f}", "label_subject": entity_iri[FIELD_TABLE[f][0]],
                  "label_predicate": predicate[f], "label_object": val["record"], "label_kind": "pdf_value",
                  "label_source": "apertus_head" if av.is_apertus_tier(val["tier"]) else "rule",
                  "label_probability": pr["p"], "value_status": pr["status"],
                  "calibration": f"{calibration_base}calibration/{cid}", "model_run": run_iri,
                  "rule_id": st["rule_id"], "tier": val["tier"], "page": val["page"], "last_page": val["last_page"],
                  "span_start": val["char_start"], "span_end": val["char_end"], "about_entity": ent,
                  "instance_path": ptext, "value_wording": val["value"], "normalisation_rule": FIELD_TABLE[f][3],
                  "export_check": cc["export_check"]}
            if cc["export_check"] in ("equal_to_export", "differs_from_export"):
                la["export_value"] = cc["export_value"]
            notes = []
            if av.is_apertus_tier(val["tier"]):
                notes.append(av.apertus_note(f, values[f], apertus_backend))      # W3: before the comparison note
            if f in PRINTED_FIELDS or val["normalised"] != val["record"]:
                notes.append(COMPARISON_NOTE + val["normalised"])
            if notes:
                la["label_note"] = "; ".join(notes)
            labels.append(la)
        elif h["derivation"] == "identifier_minted" or (h["derivation"] == "fixed_by_schema" and ".texts[" not in ptext):
            gid = f"{record}/label/value-{re.sub(r'[^A-Za-z0-9_]+', '-', ptext).strip('-')}"
            labels.append({"global_uri": gid, "label_subject": str(v.wert) if name == "global_uri" else ent,
                           "label_predicate": iri_of.get(name, f"{fw.AFF}{name}"), "label_object": str(v.wert),
                           "label_kind": "constant_value", "label_source": "constant", "model_run": run_iri,
                           "about_entity": ent, "instance_path": ptext,
                           "label_note": f"derivation {h['derivation']} (ValueRecord of the provenance file)"})
    # decisions W-3 and D3: the candidate of a weak tier and the addressee of a proposal are labels with no instance
    # path; the eCH-0295 part has no value for them
    for f in FIELDS:
        st = fstate[f]
        if st["kind"] not in CANDIDATE_KINDS:
            continue
        val, pr = st["v"], st["pr"]
        cid = pr["id"]
        value_cals[cid] = calibration_record(cid, f, val["tier"], calibration, predicate[f], pr["p"], pr["in_sample"])
        mark = (f"{WEAK_MARK} (stored probability of the tier: {st['tier_p']:.4f}, below {FLOOR_P})" if st["kind"] == "weak"
                else f"{ADDRESSEE_MARK} (kind {kind}; cascade rules {', '.join(cstate['selection'][f]['rules'])}); the "
                     f"probability is the number of the tier for a responder and does not say that this body gave a response")
        note = mark + (f"; {COMPARISON_NOTE}{val['normalised']}" if f in PRINTED_FIELDS or val["normalised"] != val["record"] else "")
        labels.append({"global_uri": f"{record}/label/candidate-{f}",
                       "label_subject": entity_iri[FIELD_TABLE[f][0]] or record, "label_predicate": predicate[f],
                       "label_object": val["record"], "label_kind": "pdf_value",
                       "label_source": "apertus_head" if av.is_apertus_tier(val["tier"]) else "rule",
                       "label_probability": pr["p"], "value_status": "unsure",
                       "calibration": f"{calibration_base}calibration/{cid}", "model_run": run_iri,
                       "rule_id": st["rule_id"], "tier": val["tier"], "page": val["page"], "last_page": val["last_page"],
                       "span_start": val["char_start"], "span_end": val["char_end"], "label_note": note,
                       "value_wording": val["value"], "normalisation_rule": FIELD_TABLE[f][3],
                       "export_check": "not_compared"})
    last_page = max(pages)
    gap_records = []
    for f in FIELDS:
        st = fstate[f]
        if st["kind"] not in ("gap", *CANDIDATE_KINDS):
            continue
        g = {"global_uri": f"{record}/gap/{f}", "gap_subject": entity_iri[FIELD_TABLE[f][0]] or record,
             "gap_slot": predicate[f], "slot_state": st["state"],
             "gap_reason": CANDIDATE_GAP_REASON if st["kind"] == "weak" else st.get("gap_reason", st["reason"]),
             "candidates_found": int(st["candidates"])}
        if cstate["selection"][f]["searched"]:
            g |= {"rules_tried": [st["rule_id"]], "searched_first_page": 1, "searched_last_page": last_page}
        if st["cc"]["has_reference"] is not None:
            g["export_has_value"] = bool(st["cc"]["has_reference"])
        g |= {"model_run": run_iri, "label_note": st["note"][:400]}
        gap_records.append(g)
    used = sorted({la["calibration"].rsplit("/", 1)[1] for la in labels
                   if "calibration" in la and la["label_kind"] != "pdf_value"})
    stand_in = str(calibration.get("label") or "").startswith("STAND-IN")
    synthetic = stand_in or any(cals[c]["calibration_method"] == fw.SYNTHETIC for c in used)
    label_run = {"global_uri": run_iri, "script_name": SCRIPT, "run_mode": dec["mode"],
                 "process_status": (fw.PROCESS_STATUS + "; synthetic values for a code check: not a result") if synthetic
                 else fw.PROCESS_STATUS,
                 "input_files": [{"file_role": k, "file_path": f["path"], "file_digest": f["sha256"]}
                                 for k, f in files.items()],
                 "ech_commit": ea.ECH_COMMIT, "linkml_version": ea.LINKML, "datetime_generated": fw.utc_now()}

    def block_cal(c: str) -> dict:
        x = dict(cals[c])
        if not known:                    # as worker/pdf_only.py: no statement about this PDF, no project numbers
            x.pop("in_sample", None)
            if "reference_source" in x:
                x["reference_source"] = REFERENCE_TEXT
        return {"global_uri": f"{calibration_base}calibration/{c}"} | x

    def value_cal(c: str) -> dict:
        x = dict(value_cals[c])
        if not known:
            x.pop("in_sample", None)
        return {"global_uri": f"{calibration_base}calibration/{c}"} | x

    label_rec = {"global_uri": iri["label_record"], "describes_record": record, "ech_delivery": iri["container"],
                 "source_document": doc_iri, "label_run": label_run, "label_assertions": labels}
    if gap_records:
        label_rec["pdf_value_gaps"] = gap_records
    label_rec["calibrations"] = [block_cal(c) for c in used] + [value_cal(c) for c in sorted(value_cals)]

    # ---------------------------------------------------------------- manifest parts
    slots = slot_list(i95_slots(), fstate, cstate, texts, written)
    pdf_labels = [la for la in labels if la["label_kind"] == "pdf_value" and "instance_path" in la]
    weak = [f for f in FIELDS if fstate[f]["kind"] == "weak"]
    addressee = [f for f in FIELDS if fstate[f]["kind"] == "addressee"]
    sources = {f: fstate[f]["pr"]["source"] for f in FIELDS if has[f]}
    switches = fw.path_switches(options)
    covered = {pos[x["after_block"]] for x in dec.get("boundaries") or []}
    counts = {
        "blocks": len(blocks), "block_options": {o: options.count(o) for o in fw.OPTIONS if o in options},
        "author_blocks": len(runs), "textblocks_by_slot": {s: len(texts[s]) for s in texts},
        "textblock_records_profile_only": sum(1 for r in tb_records if r["mapping_status"] == "profile_only"),
        "path_switch_points": len(switches),
        "path_switch_points_without_boundary_label": sum(1 for a, b in switches if not any(a <= c < b for c in covered)),
        "boundary_labels": len(dec.get("boundaries") or []), "label_assertions": len(labels),
        "label_assertions_by_source": {s: sum(1 for la in labels if la["label_source"] == s)
                                       for s in sorted({la["label_source"] for la in labels})},
        "label_assertions_by_kind": {s: sum(1 for la in labels if la["label_kind"] == s)
                                     for s in sorted({la["label_kind"] for la in labels})},
        "pdf_value_gaps": len(gap_records),
        "certain_labels": sum(1 for la in labels if la.get("value_status") == "certain"),
        "unsure_labels": sum(1 for la in labels if la.get("value_status") == "unsure"),
        "r2_agrees_with_block_path": r2_agree, "d1_option": d1["option"], "leaf_values": len(entries),
        "value_records": len(value_records),
        "e19": {"text_blocks": e19["text_blocks"], "characters": e19["characters"], "hyphens_removed": e19["hyphens"],
                "list_markers_removed": e19["markers"], "problems": len(e19["problems"])},
        "metadata_check": {"values_checked": n_meta, "problems": sum(1 for p in problems if p.startswith("metadata evidence")),
                           "leaves_without_provenance": len(without)},
        "slots": {s: sum(1 for x in slots if x["state"] == s) for s in STATES},
        "slots_no_rule_searched": sum(1 for x in slots if x["reason"] == "no_rule_searched"),
        "values": {"fields": len(FIELDS), "read_from_pdf": len(pdf_labels),
                   "not_found_in_pdf": sum(1 for f in FIELDS if not has[f] and fstate[f]["state"] == "not_found_in_pdf"),
                   "not_in_this_document_type": sum(1 for f in FIELDS if fstate[f]["state"] == "not_in_this_document_type"),
                   "weak_candidates": len(weak), "addressee_candidates": len(addressee),
                   "certain": sum(1 for la in pdf_labels if la["value_status"] == "certain"),
                   "unsure": sum(1 for la in pdf_labels if la["value_status"] == "unsure"),
                   "export_check": {k: sum(1 for la in pdf_labels if la["export_check"] == k) for k in EXPORT_CHECKS}}}
    return {"instance": instance, "provenance": prov, "labels": label_rec, "iri": iri, "register": register,
            "i95_gaps": gaps, "conformance": gp.conformance(gaps), "synthetic": synthetic, "stand_in": stand_in,
            "calibrations": used + sorted(value_cals), "check_passed": check_passed,
            "problems": problems + e19["problems"], "notes": notes, "counts": counts, "slots": slots,
            "s1_rule_role": s1_role, "sources": sources,
            "comparison_values": {f: fstate[f]["v"]["normalised"] for f in FIELDS
                                  if fstate[f]["kind"] in ("value", *CANDIDATE_KINDS)},
            "cascade": {"version": casc.cascade()["version"], "reader": vcr.VERSION, "result_text": NOT_SEARCHED,
                        "kind": kind, "kind_source": cstate["kind_source"],
                        "affair_type_of_the_cascade": cstate["affair_type_of_the_cascade"],
                        "selection": cstate["selection"], "texts": cstate["texts"], "steps": cstate["steps"],
                        "text_blocks_not_written": [{"author_block": r["k"], "option": r["option"],
                                                     "slot": cstate["texts"][fw.FAMILY[r["option"]]]["slot"],
                                                     "cascade_rules": cstate["texts"][fw.FAMILY[r["option"]]]["rules"]}
                                                    for r in tb_records if r.get("cut_by_cascade")]},
            "value_floor": {"threshold": FLOOR_P,
                            "rule": "a value of a pair (field, tier) whose stored probability of all folds is below the "
                                    "threshold is not written to the eCH-0295 part; it is a candidate label. The "
                                    "probability of a label is this same number (decision D4)",
                            "not_written": [{"field": f, "tier": fstate[f]["v"]["tier"], "tier_probability": fstate[f]["tier_p"],
                                             "label_id": f"candidate-{f}", "mark": WEAK_MARK} for f in weak]},
            "addressee_candidates": [{"field": f, "tier": fstate[f]["v"]["tier"], "label_id": f"candidate-{f}",
                                      "mark": ADDRESSEE_MARK} for f in addressee],
            "author_rule": {"rule": "the first author is searched if the cascade gives Submission.sponsorship to the "
                                    "kind of the document (rule R30: proposal, executive_proposal, response, combined)",
                            "kind": kind, "searched": bool(cstate["selection"]["sponsor"]["searched"]),
                            "cascade_rules": cstate["selection"]["sponsor"]["rules"],
                            "submitted_text": bool(texts["submission"])},
            "fields_not_read": [{"field": f, "reason": fstate[f]["reason"]} for f in FIELDS
                                if fstate[f]["kind"] == "not_read"],
            "hyphen_word_counts": {"scope": "the atom files below the data root",
                                   "atom_files": len(list((gr.ROOT / "daten/iso/atome").glob("*.json")))}}


def write_record(block_file, rule_file, decisions, values, calibration, export_record, out_dir, base, *,
                 block_calibrations, root=None, calibration_base=None, kind: str | None = "from_rule_chain",
                 apertus: dict | None = None) -> dict:
    """Writes <prefix>.ech.yaml, <prefix>.provenance.yaml, <prefix>.labels.yaml and manifest.json of one document
    to the record folder out_dir. Returns the manifest. Arguments: record form chapter 8.1. `values`: the records
    of the cascade reader (read_values) for the same `kind`, or the records of the combined reader of
    m12_apertus_values.combined_values (Apertus mode).
    `apertus` (W5): None (no Apertus value read-out), or the facts of the Apertus step: key heads_json (path of the
    heads output of the document; input apertus_heads), key entry_json (the entry file of the heads; input
    apertus_entry), key backend (the backend name of the provider) and the facts for the manifest key
    apertus_values (numbers, classes, tiers and block ids; no path of the user)."""
    t0 = time.perf_counter()
    root = Path(root or ROOT).resolve()
    out_dir = Path(out_dir).resolve()
    block_file, decisions = Path(block_file).resolve(), Path(decisions).resolve()
    doc = read_json(block_file)
    raw_id = doc.get("doc_id")
    known = base is not None and re.fullmatch(r"\d+", str(raw_id or "")) is not None
    d = str(raw_id) if known else LOCAL
    closed_guard(raw_id, doc.get("parliament"), [ROOT, root])
    if known:
        fw.check_base(base)
        fw.guard_docs([d])
    calibration_base = fw.check_base(calibration_base or (base if known else None) or DEFAULT_BASE)
    atoms_p, docling_p = root / "daten/iso/atome" / f"{d}.json", root / "daten/iso/docling" / f"{d}.json"
    for what, p in (("atom", atoms_p), ("Docling", docling_p)):
        if not p.is_file():
            raise WriterStop(f"{d}: no {what} file {p.name} below the data root (daten/iso/)")
    vb.load_rule_modules()
    vdoc = vb.load_from_block_file(block_file, rule_file)
    if set(values) != set(FIELDS):
        raise WriterStop(f"the values do not have exactly the fields {list(FIELDS)}")
    rules = read_json(rule_file) if rule_file is not None else None
    dec = read_json(decisions)
    cals, cal_file = fw.load_calibrations(Path(block_calibrations).resolve())
    calib = read_json(calibration)
    if calib.get("schema") != "parlpdfech-value-calibration" or "lookup" not in calib:
        raise WriterStop("the value calibration file does not have the form of src/m11_value_cal.py (command open)")
    atoms = read_json(atoms_p)["atome"]
    check_doc = doc if known else doc | {"doc_id": d}
    bad = [x for x in fw.check_doc_file(d, check_doc, atoms) if known or not x.startswith("split ")]
    bad += fw.check_decisions(d, check_doc, dec | ({} if known else {"doc_id": d}), cals)
    for path, digest in (doc.get("source_files") or {}).items():
        if path.startswith("daten/iso/") and (root / path).is_file() and sha256(root / path) != digest:
            bad.append(f"source file {path} below the data root has another SHA-256")
    if rules is not None and [b["block"] for b in rules["blocks"]] != [b["block"] for b in doc["blocks"]]:
        bad.append("the blocks of the rule file are not the blocks of the block file")
    if export_record is not None and (not known or str(export_record.get("doc_id")) != d):
        bad.append("the export record is for another document, or the PDF has no document number")
    if bad:
        raise WriterStop(f"{d}: input check failed: {bad[:8]}")
    files = {"docs": file_info(block_file, root, out_dir), "decisions": file_info(decisions, root, out_dir),
             "atoms": file_info(atoms_p, root, out_dir), "docling": file_info(docling_p, root, out_dir),
             "calibrations": file_info(block_calibrations, root, out_dir),
             "value_calibration": file_info(calibration, root, out_dir)}
    if rule_file is not None:
        files["rules"] = file_info(rule_file, root, out_dir)
    if export_record is not None:
        exp_p = out_dir / "export" / f"{d}.json"
        write_json(exp_p, export_record)
        files["export"] = file_info(exp_p, root, out_dir)
    backend = None
    if apertus is not None:                            # W5: the heads output is an input of the record
        files["apertus_heads"] = file_info(Path(apertus["heads_json"]), root, out_dir)
        files["apertus_entry"] = file_info(Path(apertus["entry_json"]), root, out_dir)
        backend = str(apertus.get("backend") or "") or None
    elif any(av.is_apertus_tier((values[f] or {}).get("tier")) for f in values if isinstance(values[f], dict)):
        raise WriterStop("a value has an Apertus tier, and the call gives no facts of the Apertus step (W5)")
    with data_root(root):
        b = build(d, known, doc, vdoc, rules, dec, values, calib, export_record, cals, base, calibration_base, files, root,
                  kind, backend)
    outs = {"ech_yaml": out_dir / f"{d}.ech.yaml", "provenance_yaml": out_dir / f"{d}.provenance.yaml",
            "labels_yaml": out_dir / f"{d}.labels.yaml"}
    note = " Synthetic values for a code check: not a result." if b["synthetic"] else ""
    what = f"document {d}" if known else "a PDF with no document number"
    ea.schreibe_yaml(outs["ech_yaml"], b["instance"],
                     f"# eCH-0295 instance (I95, root class Container), {SCRIPT} ({VERSION}), {what}\n"
                     f"# Head values read from the PDF by code rules"
                     f"{'; the choice of some values by Apertus heads (labels with the source apertus_head)' if apertus is not None else ''}"
                     f"; no value of the export. Status EXCEPTION, NOT "
                     f"RELEASED.{note}\n# Side files: {d}.provenance.yaml, {d}.labels.yaml\n")
    ea.schreibe_yaml(outs["provenance_yaml"], b["provenance"],
                     f"# Provenance side file (src/m06_ech_profil.yaml version 0.2.0) of {d}.ech.yaml\n")
    ea.schreibe_yaml(outs["labels_yaml"], b["labels"],
                     f"# Label file (src/m11_label_schema.yaml version 0.2.0, class LabelRecord) of {d}.ech.yaml.{note}\n")
    iri = b["iri"]
    reused = ("m10_writer.py", "m06_converter.py", "m06_ech_ausgabe.py", "m03_gold_record.py", "m03_iso_v4.py",
              "m03_iso_paths.py", "m10_gaps.py", "m10_rdf.py", "m10_calibrate.py", "m11_values_base.py",
              "m11_value_norm.py", "m11_value_reference.py", "m11_values_cascade.py", "m11_cascade.py", "m11_cascade.yaml")
    readers = sorted({vb.REGISTRY[f].__module__ for f in vb.REGISTRY})
    src = Path(__file__).resolve().parent
    man = {"schema": RECORD_SCHEMA, "doc_id": d, "status": fw.PROCESS_STATUS, "synthetic_values": b["synthetic"],
           "mode": dec["mode"], "split": doc.get("split"), "has_export": export_record is not None,
           "base_iri": base if known else None, "calibration_base_iri": calibration_base,
           "source_iri": iri["source"], "pdf_sha256": doc["pdf_sha256"], "record_iri": iri["record"],
           "container_iri": iri["container"], "affair_iri": iri["affair"], "register_affair_iri": b["register"],
           "named_graphs": iri["named_graphs"], "s1_rule_role": b["s1_rule_role"],
           "writer": {"path": SCRIPT, "version": VERSION, "sha256": sha256(Path(__file__)), "run_date": fw.clock()},
           "reused_files": {f"src/{n}": sha256(src / n) for n in reused},
           "value_readers": {"interface": vb.VERSION, "modules": {f"src/{n}.py": sha256(src / f"{n}.py") for n in readers}},
           "schemas": {"i95": {"path": rdf.rel(gp.I95), "sha256": sha256(gp.I95)},
                       "wrapper": {"path": rdf.rel(rdf.WRAPPER), "sha256": sha256(rdf.WRAPPER)},
                       "profile": {"path": rdf.rel(rdf.PROFILE), "sha256": sha256(rdf.PROFILE), "version": "0.2.0"},
                       "labels": {"path": rdf.rel(LABEL_SCHEMA), "sha256": sha256(LABEL_SCHEMA), "version": "0.2.0"}},
           "inputs": {k: {"path": f["path"], "sha256": f["sha256"]} for k, f in files.items()},
           "data_root": "the folder of the code files" if root == ROOT else "a data root apart from the code files",
           "hyphen_word_counts": b["hyphen_word_counts"],
           "model": {k: dec[k] for k in ("model", "template", "template_sha256", "heads", "calibration") if k in dec}
                    or "the decisions file (interface 7) names no model, template or head",
           "calibration_ids": b["calibrations"],
           "value_calibration": {"path": files["value_calibration"]["path"], "sha256": files["value_calibration"]["sha256"],
                                 "stand_in": b["stand_in"], "probability_from": PROBABILITY_FROM,
                                 "probability_rule": "the probability of a value label is the stored value of its rule "
                                                     "tier over all folds, for each document (decision D4)",
                                 "origin": None if b["stand_in"] else f"{CALIBRATION_ORIGIN} {APERTUS_ORIGIN}"},
           "value_probability_sources": b["sources"], "comparison_values": b["comparison_values"],
           "cascade": b["cascade"], "value_floor": b["value_floor"], "addressee_candidates": b["addressee_candidates"],
           "author_rule": b["author_rule"],
           "conformance": b["conformance"], "i95_gaps": b["i95_gaps"], "fields_not_read": b["fields_not_read"],
           "slots": b["slots"], "check_passed": b["check_passed"], "problems": b["problems"], "notes": b["notes"],
           "counts": b["counts"]}
    if apertus is not None:                            # W5: the facts of the Apertus step (no path of the user)
        man["apertus_values"] = {k: v for k, v in apertus.items() if k not in ("heads_json", "entry_json")} | {
            "values_from_apertus": sorted(f for f in FIELDS if isinstance(values[f], dict) and values[f].get("found")
                                          and av.is_apertus_tier(values[f].get("tier"))),
            "module": {"path": av.SCRIPT, "version": av.VERSION, "sha256": sha256(Path(av.__file__))}}
    if not known:
        if apertus is not None:
            fields_ap = man["apertus_values"]["values_from_apertus"]
            where = ("Stored states of " + av.MODEL_NAME + " (layer " + str(av.LAYER) + ", made before for this block "
                     "file) gave the value read-outs; no model ran for this record" if backend == "stored" else
                     av.MODEL_NAME + " ran on a remote GPU for the value read-outs (backend " + str(backend) + ", bf16, "
                     "layer " + str(av.LAYER) + ")" if str(backend or "").startswith("remote") else
                     av.MODEL_NAME + " ran on this computer for the value read-outs (backend " + str(backend or "not named")
                     + ", bf16, layer " + str(av.LAYER) + ")")
            apertus_note = (f"{where}. Values from an Apertus head: {', '.join(fields_ap) or 'none'}. The block labels "
                            "come from " + ("the floor decisions of the rules." if dec["mode"] == "floor" else
                                            "a decisions file of the mode cascade."))
        else:
            apertus_note = ("No Apertus state was read and no model ran. No label of this record is from Apertus."
                            if dec["mode"] == "floor" else "The block labels come from a decisions file of the mode cascade.")
        man |= {"apertus": "none" if dec["mode"] == "floor" else "decisions file",
                "apertus_note": apertus_note,
                "sample_of_the_package": False, "development_document": None, "development_document_note": NOT_KNOWN,
                "probabilities_checked_on_other_documents": False, "probabilities_note": NOT_CHECKED,
                "calibration_reference_source": {"replaced": True, "text": REFERENCE_TEXT,
                                                 "why": "the text of the calibration file of the block labels names "
                                                        "document numbers and folders of the project"},
                "calibration_in_sample": {"left_out": True,
                                          "why": "the slot is a constant of the calibration file; it says nothing "
                                                 "about this PDF"}}
    man |= {"outputs": {k: {"path": p.name, "sha256": sha256(p), "bytes": p.stat().st_size} for k, p in outs.items()},
            "seconds": {"write": round(time.perf_counter() - t0, 3)}}
    write_json(out_dir / "manifest.json", man)
    return man


# ------------------------------------------------------------------ RDF step
def record_paths(out_dir: Path, d: str) -> dict[str, Path]:
    return rdf.record_paths(Path(out_dir), d)


def part_graphs(out_dir, *, root=None) -> tuple[dict, dict]:
    """The 4 graphs of the record from its YAML files, the block file and the atom file of the manifest. The label
    graph and the atom graph use the label schema 0.2.0. The eCH graph gets the recorded gap slots."""
    import rdflib  # noqa: PLC0415
    out_dir, root = Path(out_dir).resolve(), Path(root or ROOT).resolve()
    man = read_json(out_dir / "manifest.json")
    d = man["doc_id"]
    paths = record_paths(out_dir, d)
    labels = rdf.load_yaml(paths["labels_yaml"])
    record_iri = man["record_iri"]
    if labels["describes_record"] != record_iri:
        raise WriterStop("the label file and the manifest name different records")
    doc_p = path_of(man["inputs"]["docs"]["path"], root, out_dir)
    atoms_p = path_of(man["inputs"]["atoms"]["path"], root, out_dir)
    if sha256(doc_p) != man["inputs"]["docs"]["sha256"] or sha256(atoms_p) != man["inputs"]["atoms"]["sha256"]:
        raise WriterStop("the block file or the atom file differs from the file that the writer read")
    doc = read_json(doc_p)
    layout = rdf.layout_record(doc, read_json(atoms_p), record_iri, labels["source_document"])
    ech = rdf.load_yaml(paths["ech_yaml"])
    gaps = gp.ordered(g["slot"] for g in man["i95_gaps"])
    if man["conformance"] != gp.conformance(gaps):
        raise WriterStop("the manifest keys conformance and i95_gaps do not agree")
    bad = gp.instance_gap_problems(ech, gaps) if gaps else []
    if bad:
        raise WriterStop("; ".join(bad))
    if record_iri.startswith("urn:"):
        accept_urn(rdf.WRAPPER, rdf.PROFILE, LABEL_SCHEMA)
    graphs = {"ech-0295": rdf.to_graph(rdf.WRAPPER, "Container", ech, gaps),
              "provenance": rdf.to_graph(rdf.PROFILE, "ExtractionRecord", rdf.load_yaml(paths["provenance_yaml"])),
              "atoms": rdf.to_graph(LABEL_SCHEMA, "PdfLayout", layout),
              "labels": rdf.to_graph(LABEL_SCHEMA, "LabelRecord", labels)}
    iris = rdf.slot_iris(rdf.WRAPPER)
    for slot in gaps:
        if any(graphs["ech-0295"].triples((None, rdflib.URIRef(iris[slot]), None))):
            raise WriterStop(f"the eCH graph has a triple for the gap slot {slot}")
    return graphs, {"manifest": man, "layout": layout, "record_iri": record_iri, "i95_gaps": list(gaps), "doc": doc,
                    "paths": paths}


VALUES_NS = "https://schema.parlpdfech.example/values/"
VALUES_SCHEMA = "parlpdfech-values-ttl/2"


def written_value_labels(labels: dict) -> list[dict]:
    """The labels of the values that are in the eCH-0295 part: kind pdf_value and a path of the record (a candidate
    has none), in the sequence of the label file."""
    return [x for x in labels.get("label_assertions") or []
            if x.get("label_kind") == "pdf_value" and x.get("instance_path")]


def values_graph(labels: dict, man: dict):
    """The compact graph of the values with their probabilities (file <prefix>.values.ttl, form VALUES_SCHEMA).
    One node <record IRI>/value/<field> for each written value. The node links the eCH-0295 resource and its
    property (label_subject and label_predicate: the pair is a statement of the eCH-0295 graph) to the value, the
    printed wording, the probability, the value status, the rule tier, the page (and the last page if it is
    another page), the character span, the label and the calibration record. If the value is the name of another
    resource (about_entity: the actor of a sponsor or of a responder), pvl:entity names it (form 2; form 1 gave
    about_entity as pvl:resource, finding F1 of 14.10.2026). All facts come from the label file."""
    import rdflib  # noqa: PLC0415
    from decimal import Decimal  # noqa: PLC0415
    from rdflib.namespace import RDF, XSD  # noqa: PLC0415
    pv = rdflib.Namespace(VALUES_NS)
    g = rdflib.Graph()
    g.bind("pvl", pv)
    g.bind("aff", "https://ch.paf.link/schema/affairs/")
    g.bind("xsd", XSD)
    record = rdflib.URIRef(man["record_iri"])
    g.add((record, RDF.type, pv.ValueSet))
    g.add((record, pv.document, rdflib.URIRef(man["source_iri"])))
    g.add((record, pv.form, rdflib.Literal(VALUES_SCHEMA)))
    for x in written_value_labels(labels):
        field = str(x["global_uri"]).rsplit("/", 1)[-1].removeprefix("pdf-")
        node = rdflib.URIRef(f"{man['record_iri']}/value/{field}")
        g.add((record, pv.reading, node))
        g.add((node, RDF.type, pv.ValueReading))
        g.add((node, pv.field, rdflib.Literal(field)))
        g.add((node, pv.resource, rdflib.URIRef(x["label_subject"])))
        g.add((node, pv.property, rdflib.URIRef(x["label_predicate"])))
        if x.get("about_entity") and x["about_entity"] != x["label_subject"]:
            g.add((node, pv.entity, rdflib.URIRef(x["about_entity"])))
        g.add((node, pv.value, rdflib.Literal(str(x["label_object"]))))
        if x.get("value_wording") is not None:
            g.add((node, pv.printed, rdflib.Literal(str(x["value_wording"]))))
        g.add((node, pv.probability, rdflib.Literal(Decimal(str(x["label_probability"])), datatype=XSD.decimal)))
        g.add((node, pv.status, rdflib.Literal(str(x["value_status"]))))
        g.add((node, pv.tier, rdflib.Literal(str(x["tier"]))))
        for key, pred in (("page", pv.page), ("last_page", pv.lastPage), ("span_start", pv.charStart),
                          ("span_end", pv.charEnd)):
            if x.get(key) is not None and not (key == "last_page" and x.get("last_page") == x.get("page")):
                g.add((node, pred, rdflib.Literal(int(x[key]))))
        g.add((node, pv.label, rdflib.URIRef(x["global_uri"])))
        if x.get("calibration"):
            g.add((node, pv.calibration, rdflib.URIRef(x["calibration"])))
    return g


def rdf_step(out_dir, *, root=None) -> dict:
    """Writes the 4 RDF files of one record and adds them to its manifest (the route of m10_rdf.convert_record).
    It also writes <prefix>.values.ttl (function values_graph; manifest keys outputs.values_ttl and
    rdf.values_ttl). Returns the key rdf of the manifest."""
    import rdflib  # noqa: PLC0415
    t0 = time.perf_counter()
    out_dir = Path(out_dir).resolve()
    graphs, info = part_graphs(out_dir, root=root)
    man, record_iri, paths = info["manifest"], info["record_iri"], info["paths"]
    union = rdflib.Graph()
    rdf.bind(union)
    for name in GRAPHS:
        for t in graphs[name]:
            union.add(t)
    text = rdf.trig_text(graphs, record_iri)
    if text is None:
        raise WriterStop("two graphs bind one prefix to two IRIs")
    paths["gesamt_trig"].write_text(text, encoding="utf-8")
    union.serialize(paths["gesamt_rdfxml"], format="pretty-xml")
    graphs["ech-0295"].serialize(paths["ech_ttl"], format="turtle")
    graphs["ech-0295"].serialize(paths["ech_rdfxml"], format="pretty-xml")
    paths["values_ttl"] = out_dir / f"{man['doc_id']}.values.ttl"
    values = values_graph(rdf.load_yaml(paths["labels_yaml"]), man)
    paths["values_ttl"].write_text(
        f"# The values of {man['doc_id']}.ech.ttl with their probability, page and place in the text "
        f"(form {VALUES_SCHEMA}).\n"
        f"# pvl:resource and pvl:property give the statement of the eCH-0295 record. pvl:entity is the actor whose "
        f"name holds the value.\n"
        f"# pvl:probability comes from the development documents in which the same tier (a rule tier, or an Apertus "
        f"tier of the combined reader) gave a value: "
        f"(equal to OpenParlData + 0.5) / (documents + 1). Each value can be wrong.\n"
        f"# The prefix pvl is a vocabulary of this project. Its domain is a placeholder: the vocabulary is not "
        f"published.\n"
        + values.serialize(format="turtle"), encoding="utf-8")
    out = {k: {"path": paths[k].name, "sha256": sha256(paths[k]), "bytes": paths[k].stat().st_size}
           for k in ("gesamt_trig", "gesamt_rdfxml", "ech_ttl", "ech_rdfxml", "values_ttl")}
    result = {"script": {"path": SCRIPT, "sha256": sha256(Path(__file__)),
                         "functions_of": {"path": rdf.SCRIPT, "sha256": sha256(Path(rdf.__file__))}},
              "tools": rdf.linkml_versions(),
              "schemas": {rdf.rel(s): sha256(s) for s in (rdf.WRAPPER, rdf.PROFILE, LABEL_SCHEMA)},
              "i95_gap_slots_not_required": info["i95_gaps"],
              "named_graphs": {name: f"{record_iri}/{name}" for name in GRAPHS},
              "triples": {name: len(graphs[name]) for name in GRAPHS} | {"union": len(union)},
              "values_ttl": {"form": VALUES_SCHEMA, "namespace": VALUES_NS, "triples": len(values),
                             "readings": len(written_value_labels(rdf.load_yaml(paths["labels_yaml"])))},
              "files": out, "seconds": round(time.perf_counter() - t0, 3)}
    man["rdf"] = result
    man["outputs"] |= out
    man.pop("validation", None)
    man["seconds"].pop("validate", None)
    man["seconds"]["rdf"] = result["seconds"]
    write_json(out_dir / "manifest.json", man)
    return result


# ------------------------------------------------------------------ command line
def document_root(d: str, out_dir: Path) -> Path:
    """Docstring item 4: a data root with the atom file and the Docling file of one development document."""
    new = out_dir / "inputs" / "root"
    for kind in ("atome", "docling"):
        src = ROOT / "daten/iso" / kind / f"{d}.json"
        if not src.is_file():
            raise WriterStop(f"{d}: no file daten/iso/{kind}/{d}.json")
        (new / "daten/iso" / kind).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, new / "daten/iso" / kind / f"{d}.json")
    return new


def run(a) -> int:
    out_dir = Path(a.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.doc:
        d = str(a.doc)
        if not re.fullmatch(r"\d+", d):
            raise WriterStop("--doc: a document number has digits only")
        closed_guard(d, None, [ROOT])                      # before a file of the document is opened
        if not (ROOT / FOLDS_REL).is_file() or d not in read_json(ROOT / FOLDS_REL)["documents"]:
            raise WriterStop(f"{d}: not a development document of {FOLDS_REL}")
        block_file, rule_file = ROOT / "daten/gj/docs" / f"{d}.json", vb.RULES_DIR / f"{d}.json"
        base = fw.check_base(a.base)
        root = Path(a.root).resolve() if a.root else document_root(d, out_dir)
        export = None
        exp_p = Path(a.export) if a.export else ROOT / DEV_EXPORT_REL.format(d=d)
        if not a.no_export and (a.export or exp_p.is_file()):
            export = read_json(exp_p)
    else:
        if not (a.block_file and a.rule_file and a.pdf_sha256):
            raise WriterStop("give --doc, or --block-file with --rule-file and --pdf-sha256")
        block_file, rule_file, base, export = Path(a.block_file), Path(a.rule_file), None, None
        root = Path(a.root).resolve() if a.root else ROOT
        if read_json(block_file).get("pdf_sha256") != a.pdf_sha256:
            raise WriterStop("the block file names another PDF than --pdf-sha256")
    floor = Path(a.block_calibrations) if a.block_calibrations else next(
        (b / FLOOR_REL for b in (root, ROOT) if (b / FLOOR_REL).is_file()), ROOT / FLOOR_REL)
    if a.decisions:
        decisions = Path(a.decisions)
    else:
        prefix = str(a.doc) if a.doc else LOCAL
        decisions = rules_mode_decisions(rule_file, out_dir / "inputs" / f"{prefix}.decisions.json", floor, root)
    if a.calibration:
        calibration = Path(a.calibration)
    else:
        calibration = next((b / CALIBRATION_REL for b in (root, ROOT) if (b / CALIBRATION_REL).is_file()), None)
        if calibration is None:                           # decision P-1: no stand-in in a record that a user sees
            raise WriterStop(f"no value calibration file {CALIBRATION_REL} below the data root or the code root. The "
                             f"writer uses no stand-in. Give the file with --calibration.")
    kind = a.kind if a.kind else "from_rule_chain"
    values = read_values(block_file, rule_file, strict=not a.not_strict, kind=kind)
    man = write_record(block_file, rule_file, decisions, values, calibration, export, out_dir, base,
                       block_calibrations=floor, root=root, kind=kind)
    res = rdf_step(out_dir, root=root)
    d = man["doc_id"]
    print(json.dumps({"doc_id": d, "record_folder": str(out_dir), "conformance": man["conformance"],
                      "i95_gaps": [g["slot"] for g in man["i95_gaps"]], "check_passed": man["check_passed"],
                      "kind": man["cascade"]["kind"], "values": man["counts"]["values"],
                      "fields_not_read": man["fields_not_read"],
                      "labels": man["counts"]["label_assertions"], "triples": res["triples"],
                      "synthetic_values": man["synthetic_values"], "has_export": man["has_export"]}, indent=1))
    if a.print_ech:
        print((out_dir / f"{d}.ech.yaml").read_text(encoding="utf-8"))
    return 0 if man["check_passed"] else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="writer of the eCH-0295 record with head values that are read from the PDF")
    ap.add_argument("--doc", help="a development document (digits)")
    ap.add_argument("--block-file", help="the block file of a PDF with no project data")
    ap.add_argument("--rule-file", help="the rule file of --block-file (form of src/m10_rules.py)")
    ap.add_argument("--pdf-sha256", help="the SHA-256 of the PDF of --block-file")
    ap.add_argument("--out", required=True, help="the record folder")
    ap.add_argument("--decisions", help="a decisions file (interface 7); default: rules mode")
    ap.add_argument("--block-calibrations", help=f"calibration file of the block labels (default {FLOOR_REL})")
    ap.add_argument("--calibration", help=f"value calibration file (default {CALIBRATION_REL}; no stand-in)")
    ap.add_argument("--export", help="the export record (JSON) for the cross-check")
    ap.add_argument("--no-export", action="store_true", help="make the record with no cross-check")
    ap.add_argument("--base", default=DEFAULT_BASE, help="base IRI of a development document")
    ap.add_argument("--root", help="the data root (docstring item 4)")
    ap.add_argument("--kind", help="the kind of the document (a key of the kinds of the cascade); default: from the rule chain")
    ap.add_argument("--not-strict", action="store_true", help="an error of a reader gives the reason reader_error")
    ap.add_argument("--print-ech", action="store_true", help="print the eCH-0295 YAML file")
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())

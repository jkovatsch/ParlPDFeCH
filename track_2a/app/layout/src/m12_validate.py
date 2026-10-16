#!/usr/bin/env python3
"""Checks of one eCH-0295 record whose head values are read from the PDF (daten/gj_values/record_form.md).

Version m12-validate-1 (16.10.2026): a copy of src/m11_validate.py (m11-validate-7, SHA-256
9a2f3327ecf269479e6e82247d61dfa967243832e4355d6cfb83d0afc0a76d63) with the edits V1 to V4 of the Apertus spec of
15.10.2026 (scratchpad apertus-build/SPEC.md, chapter 4.5). It checks the records of src/m12_writer.py (Apertus mode
of the package). The frozen file src/m11_validate.py does not change; the rules-only path of the package uses it.
  V1  this header, VERSION, SCRIPT, CALIBRATION_REL (the calibration file of the Apertus mode, made by
      m12_apertus_values.write_merged below the scratch root), imports of m12_apertus_values and m11_values_combined
  V2  check C14 compares with the function cross_check of src/m12_writer.py
  V3  validate_record: if the manifest names the input apertus_heads (the heads output of the document), the
      reading of checks C15, C17, C21 and C22 is the combined reader of m12_apertus_values.reading_for_validator on
      that heads output, with the entry file of the manifest input apertus_entry (SHA-256 checked) and the weak
      tiers of the product file of the rules (SHA-256 pinned). A changed heads output or a changed value fails
      check C22
  V4  check C12: a value label with an Apertus tier has the label source apertus_head and the rule id of
      m12_apertus_values.rule_id_of; each other value label keeps the old rule (source rule, rule id
      m11_values_<module>.read_<field>)
  V5  (16.10.2026, step of the terminal table) check C3 gets the key values_ttl_suggestions_from_the_heads
      (function suggestion_problems, rules S1 to S7) if the values file has a node of the class pvl:Suggestion, the
      manifest key apertus_suggestions has an item, or the reading of V3 gives a suggestion below the entry limit
      (m12_apertus_values.suggestions). A wrong suggestion fails C3. The text of the table CHECKS and all other
      checks do not change
Status of the copy: EXCEPTION, NOT RELEASED. No human checked it.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), task T16
of crisp-dm/04-modeling/plan-ech-from-pdf.md, for the main agent. Status EXCEPTION (process rule 10), NOT RELEASED.
No human checked this file. This file changes no existing file. It imports the frozen files and does not
change them.

1 Input
  Full record (function validate_record, option --out): the folder that src/m11_writer.py wrote. The manifest also
  names the rule file (key inputs.rules); check C22 reads it. Files:
  <prefix>.ech.yaml, <prefix>.provenance.yaml, <prefix>.labels.yaml, manifest.json and the 4 RDF files of the RDF
  step. <prefix> is the document number, or `local` for an unknown PDF. The manifest names the block file and
  the atom file (keys inputs.docs and inputs.atoms, paths below the root).
  Head part (function validate_example, option --example): the files <name>.ech.yaml, <name>.labels.yaml,
  <name>.provenance_part.yaml, <name>.manifest_part.json and, for a PDF with no project files,
  <name>.blocks.json (the examples of daten/gj_values/record_examples/). A head part has no block labels, no
  TextBlockRecords and no RDF files. Thus the checks C2 to C5 and C7 to C10 have the status "not_run" for it.

2 Checks
  The ids C1 to C10 are the ids of the frozen validator src/m10_validate.py. The ids C11 to C21 are new. The
  ids V1 to V7 of record_form.md chapter 7 are the ids C11 to C17 here, V8 is C20 and V9 is C21 (table CHECKS).
  Each check has a plain description in the result (key description).
  C1  LinkML validation. The provenance file against the profile 0.2.0 (m10_validate.linkml_check). The label
      file and the atom layout against the label schema 0.2.0 (src/m11_label_schema.yaml). The eCH file against
      I95 (m10_gaps.linkml_messages): with no change, or, for a record with recorded gaps, by check C17.
      Difference from record_form.md chapter 7: m10_validate.linkml_check stops for the label schema 0.2.0,
      because m10_validate.validator starts each schema that is not its own label schema with the class of
      another schema. Thus the function schema_messages of this file does the same steps (Validator with the
      plugin JsonschemaValidationPlugin, closed=True) for the label schema 0.2.0.
  C2  rdflib parses the 4 RDF files.
  C3, C4  m10_validate.same_graph: the union of the TriG graphs and the RDF/XML file; the eCH files; each named
      graph and its part, made again from the YAML files, the block file and the atom file.
  C5  m10_validate.leaf_coverage with the label schema 0.2.0.
  C6  m10_validate.RX_SCHEME: each IRI has a scheme.
  C7, C8  m10_validate.label_checks.
  C9  m10_validate.e19_checks.
  C10 m10_validate.shacl_shapes and shacl_results with the label schema 0.2.0. Information only.
  C11 to C21: table CHECKS and the functions check_c11 to check_c21.
  C20 (decision V-1 of 13.10.2026) makes each value again from the document text at its span, with the functions
      of the value readers and of m11_values_base (function remake). It needs no export record. A record whose
      value does not follow from its wording fails.
  C21 (decision W-3) is the floor: no value of a tier with a stored probability below 0.5 is in the eCH-0295
      part; such a value is a candidate label with a gap record.
  C22 (decision D6 of 13.10.2026, finding F-1) runs the readers again: the cascade reader
      (m11_values_cascade.read_document) on the block file and the rule file of the record. It compares each of
      the 7 fields with the record: the value, the span, the tier and the state of the slot. A record whose span
      or tier does not come from the readers fails. A value that the cascade does not search for the kind of the
      document fails. The check needs no export record. The kind and its source (manifest key
      cascade.kind_source, with the key v5 of rule V5 for a document with the S1 rule id D0) are made again and
      compared. A value that the cascade searches cannot have the state not_in_this_document_type (finding
      S3-01): the reason of its rule gives the state not_found_in_pdf with the reason reader_scope.
  The probability of a value label (decision D4) is the stored value of its rule tier over all folds, for each
  document. C16 and C21 use this one number.
  The calibration file (finding S3-02): the validator does not use the file that the manifest names. It uses
  the file of the product (constant CALIBRATION_REL below the code root; below the root of the caller only if the
  code root has no such file) and fails check C16 if the manifest names another path or another SHA-256. Check
  C16 also fails if the root of the caller holds another file at the product path (finding V4-02). Another file is used only if the caller gives it
  (--calibration). Then the result says so (key calibration_file, and the same key in check C16).
  The text blocks: a text block is in the eCH-0295 part only if the cascade gives its text slot to the kind of
  the document (C19).
  The key passed uses each check that ran, without C10.

3 Rules of this file
  1. A document of a closed parliament is refused before a file of its record is read (folds.json below the
     root; no opening.json). The file prefix gives the document number.
  2. The cross-check function of this file (cross_check) is a second calculation of record_form.md chapter 4. It
     uses the functions ref_* of src/m11_value_reference.py and m11_value_norm.compare by import. It is for ONE
     record. This file calculates no agreement value for a set of documents.
  3. If src/m11_writer.py can be imported, check C14 also compares the result of its function cross_check.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m11_validate.py --out <record folder>
      [--root DIR] [--calibration FILE] [--export FILE] [--kind KIND]
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m11_validate.py --example
      daten/gj_values/record_examples/known_879163 [--calibration FILE] [--export FILE] [--write FILE]
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_record as gr  # noqa: E402  (frozen: the root and the word counts of the wording functions)
import m03_iso_paths as ip  # noqa: E402  (frozen: the two folders of the atom files)
import m10_calibrate as cal  # noqa: E402  (frozen: as_written, cal_id)
import m10_gaps as gp  # noqa: E402  (frozen: I95 validation and the lower gap functions)
import m10_rdf as rdf  # noqa: E402  (frozen: to_graph, layout_record, slot_iris, bundle)
import m10_validate as mv  # noqa: E402  (frozen: the checks C1 to C10 that apply)
import m11_cascade as casc  # noqa: E402  (the cascade of the standard: labels_for)
import m11_value_norm as vn  # noqa: E402  (compare, body_word)
import m11_value_reference as vr  # noqa: E402  (the functions ref_*)
import m11_values_base as vb  # noqa: E402  (document text of a block file; ClosedParliament; norm_text, find_dates)
import m11_values_cascade as vcr  # noqa: E402  (the cascade reader: read_document, selection, kind_of)
import m11_values_dates_responder as dr  # noqa: E402  (FIXED rule module: body_key, the table form of a body)
import m11_values_title as mt  # noqa: E402  (FIXED rule module: norm_title)
import m11_values_type_number as tn  # noqa: E402  (FIXED rule module: _type_value, normal_number, MM_RX, PREFIX_NR_RX)
import m11_values_combined as cmb  # noqa: E402  (V1: the weak tiers of the combined reader)
import m12_apertus_values as av  # noqa: E402  (V1: the reading of the Apertus mode)

ROOT = rdf.ROOT
SCRIPT = "src/m12_validate.py"
VERSION = "m12-validate-1"
LABEL_SCHEMA = rdf.SRC / "m11_label_schema.yaml"          # version 0.2.0
PROFILE, WRAPPER, I95 = rdf.PROFILE, rdf.WRAPPER, gp.I95
MANIFEST_SCHEMA = "parlpdfech-pdf-values-record/1"
# finding S3-02: the one calibration file of the product (decision D5). The validator does not import this path
# from the writer and does not read it from the manifest.
CALIBRATION_REL = av.MERGED_REL                  # V1: daten/gj_values/apertus/calibration_values_apertus.json
PRODUCT_RULES_REL = av.PRODUCT_REL               # V3: the weak tiers of the rules (as the fixed run)
RULES_REL = vb.RULES_DIR.relative_to(vb.ROOT).as_posix()      # the rule files that are made from the PDF alone
AFF = "https://ch.paf.link/schema/affairs/"
MCM = "https://ld.ech.ch/schema/0292/meta-common/"
SOURCE_KNOWN = "https://api.openparldata.ch/v1/docs/"
REGISTER_AFFAIR = "https://api.openparldata.ch/v1/affairs/"
RX_URN_SOURCE = re.compile(r"urn:parlpdfech:local:sha256:([0-9a-f]{64})\Z")
RX_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
P_MIN, P_MAX = mv.P_MIN, mv.P_MAX
LANGUAGES = ("de", "fr", "it", "rm", "en")
FIELDS = tuple(vb.FIELDS)

# field -> (entity, predicate of the label, instance path of the value); record_form.md chapter 2.2
FIELD_TABLE = {
    "affair_type": ("affair", AFF + "affairType", "affairs[0].affair_type"),
    "title": ("affair", AFF + "title", "affairs[0].title[0].text"),
    "affair_number": ("affair", AFF + "affairNumber", "affairs[0].affair_number"),
    "submission_date": ("submission", AFF + "submissionDate", "affairs[0].submission.submission_date"),
    "sponsor": ("submission", AFF + "sponsorship", "affairs[0].submission.sponsorship[0].actor.name[0].text"),
    "response_date": ("response", MCM + "dateEndActual", "affairs[0].response_steps[0].date_end_actual"),
    "responder": ("response", AFF + "responder", "affairs[0].response_steps[0].responder.name[0].text"),
}
# the entity that the value record of the field describes (about_entity)
ABOUT = {"affair_type": "affair", "title": "affair", "affair_number": "affair", "submission_date": "submission",
         "sponsor": "sponsor_actor", "response_date": "response", "responder": "responder_actor"}
FIELD_OF_SLOT = {"Affair.affair_type": "affair_type", "Affair.title": "title", "Affair.affair_number": "affair_number",
                 "Submission.submission_date": "submission_date", "Submission.sponsorship": "sponsor",
                 "ResponseStep.date_end_actual": "response_date", "ResponseStep.responder": "responder"}
SLOT_OF_FIELD = {f: s for s, f in FIELD_OF_SLOT.items()}
NORMALISATION = {"affair_type": "type_word_to_list_value", "title": "norm_text_one_line", "affair_number": "norm_text",
                 "submission_date": "date_to_iso_day", "response_date": "date_to_iso_day",
                 "responder": "printed_wording_one_line", "sponsor": "printed_wording_one_line"}
# decisions W-1 and W-4: the record value of these fields is the printed wording on one line
PRINTED_FIELDS = ("responder", "sponsor")
COMPARISON_NOTE = "comparison value of the reader (for the cross-check and the calibration only; not a value of the record): "
# decision W-3: the floor
FLOOR_P = 0.5
WEAK_REASON = "weak_candidate_only"
WEAK_MARK = "not written: the tier is more often different from the reference than equal"
CANDIDATE_GAP = ("not_found_in_pdf", "candidate_not_valid")
# decision D1: a value that the cascade does not search for the kind of the document
NOT_SEARCHED = "not searched in this kind of document"
NOT_IN_TYPE = ("not_in_this_document_type", "not_in_this_document_type")
# finding S3-01: a value that the cascade searches and whose rule gives the reader reason not_in_document_type
SCOPE_READER_REASON = "not_in_document_type"
SCOPE_GAP = ("not_found_in_pdf", "no_candidate")              # the gap record (reason code of the label schema)
SCOPE_SLOT = ("not_found_in_pdf", "reader_scope")             # the slot entry of the manifest
SCOPE_MARK = "searched, no value: the rule of this value does not read this document"
# decision D3: the body that a proposal addresses is a candidate label only
ADDRESSEE_MARK = ("not written: the body that the text of the proposal addresses; the rules search no response step in "
                  "a document of this kind")
TEXT_SLOT = {"Submission.texts": "submission", "ResponseStep.texts": "executive_response"}
STEP_NAME = {"Affair.submission": "submission", "Affair.response_steps": "executive_response"}
# reason of a reader -> (slot state, gap reason); record_form.md chapter 3.3
GAP_OF_REASON = {"no_text": ("not_found_in_pdf", "no_text"), "no_pattern": ("not_found_in_pdf", "no_candidate"),
                 "no_cue": ("not_found_in_pdf", "no_candidate"), "ambiguous": ("not_found_in_pdf", "ambiguous_candidates"),
                 "no_response_block": ("not_found_in_pdf", "no_block_of_role"),
                 "no_rule_file": ("not_found_in_pdf", "no_block_of_role"), "not_in_document_type": NOT_IN_TYPE}
NOT_READ_OF_REASON = {"no_reader": "no_rule_searched", "reader_error": "reader_error"}
PROBABILITY_FROM = "all folds"
TIER_P_PARAMETER = "jeffreys_mean_all_folds"
CALIBRATION_FIELD = {"responder": "responder_name", "sponsor": "first_author"}
PRIMARY_ROLE_FIELDS = ("response_date", "responder")
PRIMARY_ROLES = ("response", "combined")
STATES = ("read_from_pdf", "not_found_in_pdf", "not_in_this_document_type", "register_only")
NOT_READ_REASONS = ("field_not_measured", "reader_error", "no_rule_searched")
GAP_PAIRS = {("not_found_in_pdf", "no_text"), ("not_found_in_pdf", "no_candidate"),
             ("not_found_in_pdf", "ambiguous_candidates"), ("not_found_in_pdf", "no_block_of_role"),
             ("not_found_in_pdf", "candidate_not_valid"), ("not_in_this_document_type", "not_in_this_document_type")}
CONSISTENCY = {"equal_to_export": "confirmed", "differs_from_export": "metadata_differs",
               "no_export_value": "not_checked", "not_compared": "not_checked"}
RULE_T = {"identifier_minted", "fixed_by_schema", "detected_by_rule", "extracted_from_pdf",
          "extracted_from_pdf_by_rule"}
BY_RULE = "extracted_from_pdf_by_rule"
PDF_GAP_CAUSE = {"affair_type": "the rules found no value of the I95 AffairTypeEnum in this PDF",
                 "affair_number": "the rules found no affair number in this PDF"}
PDF_GAP_CAUSE_WEAK = {"affair_type": "the rules found only a weak candidate of the affair type in this PDF",
                      "affair_number": "the rules found only a weak candidate of the affair number in this PDF"}
REGISTER_SLOTS = {"local_id", "wikidata_uri", "date_created", "datetime_created", "date_modified",
                  "datetime_modified", "current_state", "procedure_states", "withdrawn_date"}
OTHER_STEP_SLOTS = {"submission_validation_steps", "assignment_steps", "committee_deliberation_steps",
                    "plenary_debates"}
STEP_OF = {"Affair.submission": "Submission", "Affair.response_steps": "ResponseStep"}
STEP_PARTS = {"Submission": ("Submission.submission_date", "Submission.sponsorship", "Submission.texts"),
              "ResponseStep": ("ResponseStep.date_end_actual", "ResponseStep.responder", "ResponseStep.texts")}
REGISTER_ALTERNATIVE_SOURCE = "OpenParlData export, affairs.id (register address of the affair)"

# id -> (key of the result, id of record_form.md chapter 7, plain description)
CHECKS = {
    "C1": ("C1_linkml", None, "Each YAML file obeys its schema: the eCH-0295 file obeys I95, the provenance file "
           "obeys the profile 0.2.0, and the label file and the atom layout obey the label schema 0.2.0."),
    "C2": ("C2_parse", None, "A standard RDF library reads each of the 4 RDF files with no error (and the file "
           "of the values, if the record has it)."),
    "C3": ("C3_isomorphism", None, "The RDF files of one record hold the same statements in each format. The file "
           "of the values, if the record has it, gives each value label with its probability, page and span."),
    "C4": ("C4_parts", None, "Each named graph is the same as the graph that the YAML files give again."),
    "C5": ("C5_leaf_values", None, "Each value of each YAML file is in its graph."),
    "C6": ("C6_iri_scheme", None, "Each IRI of the record has a scheme."),
    "C7": ("C7_C8_labels", None, "Each label from the PDF has one probability in the permitted range, a "
           "calibration record, a value status, a page and a span. Each block has one block label."),
    "C9": ("C9_e19", None, "Each text block of the record is the wording of the PDF lines of its blocks."),
    "C10": ("C10_shacl", None, "SHACL shapes of the schemas (information only; it does not decide the result)."),
    "C11": ("C11_wording_at_span", "V1", "The document text at the page and the span of each value label is "
            "exactly the wording that the label gives."),
    "C12": ("C12_one_label_for_each_pdf_value", "V2", "Each value that is read from the PDF has exactly one "
            "label, and each such label has its value. The label, the record and the provenance file give the "
            "same value."),
    "C13": ("C13_no_export_value_in_the_record", "V3", "Each value of the eCH-0295 part has one provenance entry. "
            "No value comes from the export, and no slot that only the register knows has a value."),
    "C14": ("C14_cross_check", "V4", "The comparison with the export is consistent in the label and in the "
            "provenance file. With the export record at hand, a second calculation gives the stored result "
            "and the stored export value again."),
    "C15": ("C15_slot_states", "V5", "The manifest gives one of the 4 states for each slot of Affair, Submission "
            "and ResponseStep, and each state agrees with the record. Each of the 7 fields has a label, or a gap "
            "record, or an entry in the list of the fields that were not read, and only one of them."),
    "C16": ("C16_probability_and_calibration", "V6", "Each value label has a probability from 0.005 to 0.995 and "
            "a calibration record for its rule tier. The probability and the value status are the values that "
            "the calibration file of the product gives. A record that names another calibration file fails, "
            "if the caller of the check did not give that file."),
    "C17": ("C17_recorded_gaps", "V7", "A required slot of I95 with no value (affair type, affair number) is a "
            "recorded gap: the manifest, the provenance file and the label file each state it, and no other "
            "required slot is absent."),
    "C18": ("C18_minted_iris", None, "Each IRI of the record is below the record IRI. The address of the affair "
            "in the register is not an IRI of the eCH-0295 part and not an IRI of a label."),
    "C19": ("C19_value_forms", None, "Each value has the form of its slot: a type of the I95 list, a date that "
            "is a calendar day, and a responder that names a body (not only a person). A head value, a step "
            "and a text block are in the record only if a document of this kind can state them. A proposal has "
            "no response step, and no value that is not searched in this kind of document."),
    "C20": ("C20_value_follows_from_wording", "V8", "Each value from the PDF is made again from the document text "
            "at its span: the list value of the printed type word, the printed title and number on one line, the "
            "day of the printed date, the printed name of the body and of the first author. A value that the PDF "
            "does not print at its span fails. This check needs no export record."),
    "C21": ("C21_floor", "V9", "No value of a rule tier that is more often different from the reference than "
            "equal (stored probability below 0.5) is in the eCH-0295 part. Such a value is a candidate in the "
            "label file, with a gap record and the slot state not found in the PDF."),
    "C22": ("C22_values_from_the_readers", "V10", "The reading rules run again on the text of the PDF. Each of "
            "the 7 entries of the record is what the rules give: the same value, the same place in the PDF, the same "
            "rule tier and the same state. A value that the rules do not give, a place that the rules did not "
            "select, and a value that is not searched in this kind of document fail. This check needs no export "
            "record."),
}
HEAD_PART_CHECKS = ("C1", "C6", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22")


# ------------------------------------------------------------------ helpers
def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def value_at(obj, path: str):
    for name, idx in re.findall(r"([A-Za-z_]+)|\[(\d+)\]", path):
        obj = obj[name] if name else obj[int(idx)]
    return obj


def value_exists(obj, path: str) -> bool:
    try:
        return value_at(obj, path) is not None
    except (KeyError, IndexError, TypeError):
        return False


def leaf_paths(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaf_paths(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaf_paths(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def last_part(iri) -> str:
    return str(iri).rsplit("/", 1)[-1]


def result(check: str, problems: list, **extra) -> dict:
    key, form_id, text = CHECKS[check]
    out = {"passed": not problems, "description": text}
    if form_id:
        out["record_form_id"] = form_id
    return out | extra | {"problems": [str(p)[:400] for p in problems[:50]]}


def not_run(check: str, reason: str) -> dict:
    key, form_id, text = CHECKS[check]
    return {"status": "not_run", "description": text, "reason": reason}


def accept_urn() -> None:
    """The prefix urn for the LinkML dumper (the method of package/worker/pdf_only.py, function accept_urn): the
    prefix map of the schema views in memory gets urn = "urn:". No schema file changes."""
    for schema in (WRAPPER, PROFILE, LABEL_SCHEMA):
        sv, _, _ = rdf.bundle(schema)
        with rdf.in_src():
            ns = sv.namespaces()
            if "urn" not in ns:
                ns["urn"] = "urn:"


@lru_cache(maxsize=None)
def schema_validator(schema: Path, cls: str):
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin
    with rdf.in_src():
        v = Validator(str(schema), validation_plugins=[JsonschemaValidationPlugin(closed=True)])
        list(v.iter_results({}, cls))            # compile once in src/
    return v


def schema_messages(schema: Path, cls: str, data: dict) -> list[str]:
    """The method of check C1 of src/m10_validate.py for a schema that m10_validate.validator cannot start."""
    with rdf.in_src():
        return [r.message for r in schema_validator(schema, cls).iter_results(data, cls)]


def schema_check(schema: Path, cls: str, data: dict, name: str) -> dict:
    msgs = schema_messages(schema, cls, data)
    return {"file": name, "schema": rdf.rel(schema), "class": cls, "valid": not msgs, "errors": len(msgs),
            "messages": [m[:400] for m in msgs[:10]]}


@lru_cache(maxsize=None)
def i95_slots() -> tuple[str, ...]:
    sv, _, _ = rdf.bundle(WRAPPER)
    with rdf.in_src():
        return tuple(f"{c}.{s.name}" for c in ("Affair", "Submission", "ResponseStep")
                     for s in sv.class_induced_slots(c))


@lru_cache(maxsize=None)
def affair_types() -> frozenset:
    sv, _, _ = rdf.bundle(WRAPPER)
    with rdf.in_src():
        return frozenset(sv.get_enum("AffairTypeEnum").permissible_values)


def guard(doc_id, root: Path) -> None:
    """Rule 1 of chapter 3: a document of a closed parliament is refused if the opening file is absent."""
    d = str(doc_id)
    for base in dict.fromkeys((Path(root), ROOT)):
        folds = base / "daten/gj_values/folds.json"
        if not folds.is_file():
            continue
        entry = (read_json(folds).get("documents") or {}).get(d)
        if entry and entry.get("part") != "open" and not (base / "daten/gj_values/opening.json").is_file():
            raise vb.ClosedParliament(f"{d}: the document is in a closed parliament; the main agent did not "
                                      "write daten/gj_values/opening.json")


# ------------------------------------------------------------------ the record in memory
@dataclass
class Record:
    ech: dict
    labels: dict
    prov: dict
    man: dict
    doc: object                 # m11_values_base.Doc of the block file
    block_file: dict            # the block file as it is stored (interface 2)
    full: bool                  # True: a full record of the writer; False: a head part (the examples)
    atoms: list | None = None   # the lines of the atom file (full record), for the PDF evidence of check C11
    rule_file: bool = False     # True: the document text was loaded with the rule file of the record
    kind_arg: str | None = "from_rule_chain"    # the kind that the caller of the validator gives (not the manifest)
    _reading: dict | None = None

    def reading(self) -> dict:
        """The result of the cascade reader on the block file and the rule file of the record (decision D6). Keys:
        kind, kind_source, affair_type_of_the_cascade, fields, and kind_from ("rule chain", "rule V5 of the cascade
        reader", "argument of the validator" or "no rule file"). The kind comes from m11_values_cascade.kind_of
        (the S1 rule role of the rule file; rule V5 for the S1 rule id D0), or from the caller of the validator. The kind of the manifest is never used: it is a part of the record that the
        check examines. With no rule file the kind is not known, and each field is searched (rule V1)."""
        if self._reading is None:
            vb.load_rule_modules()
            if self.kind_arg != "from_rule_chain":
                kind, kind_from, source = self.kind_arg, "argument of the validator", None
            else:
                kind, source = vcr.kind_of(self.doc)
                kind_from = ("no rule file" if self.doc.s1_role is None else
                             "rule V5 of the cascade reader" if source.get("rule") == "V5" else "rule chain")
            res = vcr.read_document(self.doc, kind=kind, strict=False)
            if source is not None:           # the source of the rule chain or of rule V5, not the word "argument"
                res["kind_source"] = source
            self._reading = res | {"kind_from": kind_from}
        return self._reading

    def cascade(self) -> dict:
        """The label selection of the record, made again (m11_values_cascade.selection and m11_cascade.labels_for):
        kind, type, selection of the 7 fields, and the state of the two text slots and of the two steps."""
        rd = self.reading()
        return cascade_state(rd["kind"], rd["affair_type_of_the_cascade"])

    @property
    def rec(self) -> str:
        return self.man["record_iri"]

    @property
    def affair(self) -> dict:
        a = self.ech.get("affairs")
        return a[0] if isinstance(a, list) and a and isinstance(a[0], dict) else {}

    @property
    def language(self):
        lang = self.block_file.get("language")
        return lang if lang in LANGUAGES else None

    def value_labels(self) -> list[dict]:
        """Each label of the kind pdf_value: the written values and the candidates of a weak tier."""
        return [la for la in self.labels.get("label_assertions") or [] if la.get("label_kind") == "pdf_value"]

    def pdf_labels(self) -> list[dict]:
        """The labels of the values that are written to the eCH-0295 part (label id pdf-<field>)."""
        return [la for la in self.value_labels() if not last_part(la.get("global_uri", "")).startswith("candidate-")]

    def candidates(self) -> dict:
        """{field: label} of the candidates of a weak tier (label id candidate-<field>; decision W-3)."""
        out = {}
        for la in self.value_labels():
            name = last_part(la.get("global_uri", ""))
            if name.startswith("candidate-"):
                out[name[len("candidate-"):]] = la
        return out

    def comparison(self, la: dict):
        """The value of a label for the cross-check: the comparison value of the reader for the responder and the
        first author (manifest key comparison_values; check C20 examines it), else the value of the label."""
        f = field_of_label(la)
        comp = self.man.get("comparison_values") or {}
        if f in PRINTED_FIELDS or f in comp:
            return comp.get(f)
        return la.get("label_object")

    def gaps(self) -> dict:
        return {last_part(g["global_uri"]): g for g in self.labels.get("pdf_value_gaps") or []}

    def value_records(self) -> list[dict]:
        return self.prov.get("value_records") or []

    def entities(self) -> dict:
        a = self.affair
        sub = a.get("submission") or {}
        steps = a.get("response_steps") or [{}]
        resp = steps[0] if isinstance(steps[0], dict) else {}
        spons = sub.get("sponsorship") or [{}]
        return {"affair": a.get("global_uri"), "submission": sub.get("global_uri"), "response": resp.get("global_uri"),
                "responder_actor": (resp.get("responder") or {}).get("global_uri"),
                "sponsor_actor": ((spons[0] or {}).get("actor") or {}).get("global_uri")}


@lru_cache(maxsize=None)
def cascade_state(kind, a_type: str) -> dict:
    """{kind, type, selection: {field: {...}}, texts: {slot: (applies, rules)}, steps: {holder slot: (applies,
    rules)}} for a kind and an affair type. Kind None (not known): each slot applies (rule V1)."""
    sel = vcr.selection(kind, a_type)
    texts, steps = {}, {}
    if kind is None:
        texts = {s: (True, ["V1"]) for s in TEXT_SLOT}
        steps = {s: (True, ["V1"]) for s in STEP_NAME}
    else:
        lab = casc.labels_for(kind, a_type)
        live = {(n["class"], n["slot"]) for n in lab["affair"]["slots"] + [n for st in lab["steps"].values()
                                                                             for n in st["slots"]]}
        cut = {x["path"].split("/")[-1]: x for x in lab["not_applicable"]}
        for holder, step in STEP_NAME.items():
            st = lab["steps"][step]
            rules = [st["rules"][0], "R25"] + (["R31"] if step == "executive_response" and not st["applies"] else [])
            steps[holder] = (bool(st["applies"]), rules)
        for slot, step in TEXT_SLOT.items():
            cls = slot.split(".")[0]
            holder = next(h for h, s in STEP_NAME.items() if s == step)
            if (cls, "texts") in live:
                texts[slot] = (True, steps[holder][1])
            elif not steps[holder][0]:
                texts[slot] = (False, steps[holder][1])
            else:
                texts[slot] = (False, list(dict.fromkeys(cut[slot]["rules"])))
    return {"kind": kind, "type": a_type, "selection": sel, "texts": texts, "steps": steps}


def calibration_choice(man: dict, root: Path, given=None) -> tuple[dict | None, dict]:
    """Finding S3-02: (the calibration file as a dict or None, the facts of the choice). With no file of the
    caller the validator uses the file of the product (CALIBRATION_REL below the code root; below the root of the
    caller only if the code root has no such file). A file at the product path below the root of the caller with
    another SHA-256 than the file of the code root is a problem (finding V4-02). The path of the manifest key
    value_calibration is never opened. The key problems of the facts is a part of
    check C16: the manifest must name the product file with its SHA-256, or the file that the caller gives."""
    # finding V4-02: the code root is first. A file at the product path below the root of the caller is compared
    # with it and is never the file that the validator opens if the code root has the file.
    cands = [b / CALIBRATION_REL for b in dict.fromkeys((ROOT, Path(root).resolve())) if (b / CALIBRATION_REL).is_file()]
    product = cands[0] if cands else None
    root_differs = len(cands) == 2 and sha256(cands[0]) != sha256(cands[1])
    vc = man.get("value_calibration") or {}
    named = str(vc.get("path") or "")
    info = {"product_file": CALIBRATION_REL, "product_file_at_hand": product is not None, "source": None, "path": None,
            "sha256": None, "is_product_file": False, "manifest_names": {"path": vc.get("path"), "sha256": vc.get("sha256")},
            "problems": []}
    if root_differs:
        info["problems"].append("the root of the caller holds another file at the product path than the code root "
                                f"({CALIBRATION_REL}); the validator uses the file of the code root")
    if given is not None:
        p = Path(given).resolve()
        digest = sha256(p)
        same = product is not None and digest == sha256(product)
        info |= {"source": "the product file, given by the caller" if same else
                 "NOT the product file: another file, given by the caller of the validator",
                 "path": str(p), "sha256": digest, "is_product_file": same}
        if vc.get("sha256") != digest:
            info["problems"].append("the manifest names a calibration file with another SHA-256 than the file that "
                                    "the caller of the validator gives")
        return read_json(p), info
    if product is None:
        info |= {"source": "no calibration file"}
        info["problems"].append(f"the calibration file of the product ({CALIBRATION_REL}) is not below the root or the "
                                "code root, and the caller gives no file: the probabilities cannot be examined")
        return None, info
    digest = sha256(product)
    info |= {"source": "the product file", "path": str(product), "sha256": digest, "is_product_file": True}
    if vc.get("sha256") != digest or not (named == CALIBRATION_REL or named.replace("\\", "/").endswith("/" + CALIBRATION_REL)):
        info["problems"].append(f"the manifest names the calibration file {named!r} (SHA-256 "
                                f"{str(vc.get('sha256'))[:16]}); the validator accepts only the file of the product "
                                f"{CALIBRATION_REL} (SHA-256 {digest[:16]}) if the caller gives no other file")
    return read_json(product), info


def scope_fields(r: "Record") -> set:
    """Finding S3-01: the fields that the cascade searches and whose rule gives the reader reason
    not_in_document_type. Their gap record is SCOPE_GAP and their slot entry is SCOPE_SLOT."""
    rd = r.reading()
    return {f for f, rec in rd["fields"].items() if rec["cascade"]["searched"] and not rec["found"]
            and rec.get("reason") == SCOPE_READER_REASON}


def field_of_label(la: dict) -> str | None:
    name = last_part(la.get("global_uri", ""))
    for pre in ("pdf-", "candidate-"):
        if name.startswith(pre) and name[len(pre):] in FIELD_TABLE:
            return name[len(pre):]
    return None


def tier_probability(field: str, tier: str, calib: dict) -> float | None:
    """The stored probability of the calibration file for the pair (field, tier): p_all_folds of the tier, or
    the value of a tier with no unit. The floor uses it (record_form.md chapter 3.5)."""
    look = (calib.get("lookup") or {}).get(CALIBRATION_FIELD.get(field, field))
    if look is None:
        return None
    t = (look.get("tiers") or {}).get(tier)
    return float(t["p_all_folds"] if t else look["p_of_a_tier_with_no_unit"])


def node_tier_probability(node: dict | None) -> float | None:
    """The same probability from the calibration node of the label file (parameter jeffreys_mean_all_folds)."""
    for x in (node or {}).get("calibration_parameters") or []:
        if x.get("parameter_name") == TIER_P_PARAMETER:
            return float(x["parameter_value"])
    return None


def recorded_gap_slots(man: dict) -> tuple[list[str], list[str]]:
    """(slots, problems) of the manifest key i95_gaps in the form of record_form.md chapter 2.4. This is the
    function of m10_gaps.manifest_gaps for the cause texts of a record with values from the PDF."""
    gaps = man.get("i95_gaps")
    if not isinstance(gaps, list):
        return [], ["the manifest has no list i95_gaps"]
    bad, slots = [], []
    for g in gaps:
        if not isinstance(g, dict) or set(g) != gp.GAP_KEYS:
            bad.append(f"i95_gaps: an entry does not have exactly the keys {sorted(gp.GAP_KEYS)}")
            continue
        s = g["slot"]
        if s not in gp.GAP_SLOTS:
            bad.append(f"i95_gaps: {s!r} is not a permitted gap slot")
            continue
        weak = any(x.get("field") == s for x in (man.get("value_floor") or {}).get("not_written") or [])
        want = (PDF_GAP_CAUSE_WEAK if weak else PDF_GAP_CAUSE)[s]
        if g["cause"] != want:
            bad.append(f"i95_gaps: the cause of {s} is not {want!r}")
        if g["local_value"] is not None:
            bad.append(f"i95_gaps: {s} has a local value; a record with values from the PDF has none")
        slots.append(s)
    if slots != [s for s in gp.GAP_SLOTS if s in slots]:
        bad.append("i95_gaps: the slots are not in the sequence affair_type, affair_number, each one time")
    return slots, bad


# ------------------------------------------------------------------ the cross-check (second calculation)
def cross_check(field: str, record_value, export_record: dict | None, language) -> dict:
    """record_form.md chapter 4 for one field of one record. The reference comes from the functions ref_* of
    src/m11_value_reference.py; the comparison is m11_value_norm.compare. The function changes no value."""
    out = {"export_check": "not_compared", "export_value": None, "has_reference": None, "evidence": [], "detail": ""}
    if export_record is None:
        return out | {"detail": "no export record"}
    affair = export_record.get("affair") or {}
    events = export_record.get("events") or []
    if field == "affair_type":
        import m02_ech_regeln as er  # noqa: PLC0415  (frozen: the term rule typ_ech)
        e = vr.ref_affair_type(affair, er.typ_ech)
        stated = [e["raw"][2]["value"]]
    elif field == "title":
        e = vr.ref_title(affair, language)
        stated = [r["value"] for r in e["raw"]]
    elif field == "affair_number":
        e = vr.ref_affair_number(affair)
        stated = [r["value"] for r in e["raw"] if r.get("used")]
    elif field == "submission_date":
        e = vr.ref_submission_date(affair, events)
        stated = list(e["values"])
    elif field == "response_date":
        e = vr.ref_response_date(events)
        stated = list(e["values"])
    elif field == "responder":
        e = vr.ref_responder(export_record.get("body") or {})
        stated = [r["value"] for r in e["raw"] if r.get("normalised")]
    elif field == "sponsor":
        if "contributors" not in export_record:
            return out | {"detail": "the export record has no key contributors"}
        e = vr.ref_first_author(export_record.get("contributors") or [])
        stated = [r["value"] for r in e["raw"] if r.get("normalised")]
    else:
        raise ValueError(f"unknown field {field}")
    out["evidence"] = e["raw"]
    out["has_reference"] = bool(e["values"])
    if not e["values"]:
        return out | {"export_check": "no_export_value", "detail": str(e.get("reason"))}
    if record_value is None:
        return out | {"detail": "the record has no value"}
    cmp = vn.compare(field, record_value, e["values"])
    stated = list(dict.fromkeys(str(s) for s in stated if s is not None))
    return out | {"export_check": "equal_to_export" if cmp["equal"] else "differs_from_export",
                  "export_value": " | ".join(stated), "detail": json.dumps(cmp, ensure_ascii=False)}


# ------------------------------------------------------------------ C11 (V1)
def span_lines(atoms: list, start: int, end: int) -> set:
    """The parts of the lines of the atom file that a span touches: (line id, start in the line, end in the line,
    text of the part). The key zeichen of a line is its range in the document text."""
    out = set()
    for a in atoms:
        z0, z1 = a["zeichen"]
        if z1 <= start or z0 >= end or not (a.get("text") or ""):
            continue
        m0, m1 = max(start, z0) - z0, min(end, z1) - z0
        out.add((a["id"], m0, m1, a["text"][m0:m1]))
    return out


def check_c11(r: Record) -> dict:
    bad = []
    text = r.doc.text
    rec_of = {v.get("instance_path"): v for v in r.value_records()}
    n_evidence = 0
    for la in r.value_labels():
        name = last_part(la["global_uri"])
        s, e = la.get("span_start"), la.get("span_end")
        if not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text)):
            bad.append(f"{name}: the span {s} to {e} is empty or outside the document text")
            continue
        if text[s:e] != la.get("value_wording"):
            bad.append(f"{name}: the document text at {s} to {e} is {text[s:e][:80]!r}, the label gives "
                       f"{str(la.get('value_wording'))[:80]!r}")
        if la.get("page") != r.doc.locate(s).page:
            bad.append(f"{name}: page {la.get('page')}, the block of the span start is on page {r.doc.locate(s).page}")
        if la.get("last_page") != r.doc.locate(e - 1).page:
            bad.append(f"{name}: last_page {la.get('last_page')}, the block of the span end is on page "
                       f"{r.doc.locate(e - 1).page}")
        if r.atoms is not None and la.get("instance_path") in rec_of:
            # the PDF evidence of the value record is exactly the lines of the atom file that the span touches
            n_evidence += 1
            got = {(x.get("atom_id"), x.get("match_start"), x.get("match_end"), x.get("matched_text"))
                   for x in rec_of[la["instance_path"]].get("pdf_evidence") or []}
            if got != span_lines(r.atoms, s, e):
                bad.append(f"{name}: the PDF evidence of the value record is not the lines of the PDF at the span "
                           f"{s} to {e}")
    return result("C11", bad, labels=len(r.value_labels()), pdf_evidence_compared=n_evidence)


# ------------------------------------------------------------------ C12 (V2)
def check_c12(r: Record) -> dict:
    bad = []
    labels = r.pdf_labels()
    by_path = Counter(la.get("instance_path") for la in labels)
    records = [v for v in r.value_records() if v.get("derivation") == BY_RULE]
    rec_by_path = Counter(v.get("instance_path") for v in records)
    path_field = {v[2]: f for f, v in FIELD_TABLE.items()}
    ent = r.entities()
    for p, n in by_path.items():
        if n != 1:
            bad.append(f"{p}: {n} value labels")
        if p not in rec_by_path:
            bad.append(f"{p}: a value label with no value record of the derivation {BY_RULE} (a label with no value)")
    for p, n in rec_by_path.items():
        if n != 1:
            bad.append(f"{p}: {n} value records of the derivation {BY_RULE}")
        if p not in by_path:
            bad.append(f"{p}: a value from the PDF with no value label")
    for f, (_, _, p) in FIELD_TABLE.items():
        if value_exists(r.ech, p) and p not in by_path:
            bad.append(f"{p}: the instance has a value of the field {f} and the record has no value label for it")
        if p in by_path and not value_exists(r.ech, p):
            bad.append(f"{p}: a value label of the field {f} and no value in the instance (a label with no value)")
    for la in r.value_labels():
        if field_of_label(la) is None:
            bad.append(f"{last_part(la.get('global_uri', ''))}: the id of a value label is not pdf-<field> or "
                       "candidate-<field>")
    for la in labels:
        p = la.get("instance_path")
        f = path_field.get(p)
        if f is None:
            bad.append(f"{last_part(la['global_uri'])}: {p} is not an instance path of the field table")
            continue
        if field_of_label(la) != f:
            bad.append(f"{p}: the label id is {last_part(la['global_uri'])}, not pdf-{f}")
        entity, pred, _ = FIELD_TABLE[f]
        want_source = "apertus_head" if av.is_apertus_tier(la.get("tier")) else "rule"     # V4
        if la.get("label_source") != want_source:
            bad.append(f"{p}: label source {la.get('label_source')}, not {want_source}")
        if want_source == "apertus_head":
            if la.get("rule_id") != av.rule_id_of(la.get("tier")):
                bad.append(f"{p}: rule id {la.get('rule_id')!r} is not {av.rule_id_of(la.get('tier'))!r} of the tier "
                           f"{la.get('tier')}")
        elif not re.fullmatch(rf"m11_values_[a-z_]+\.read_{f}", str(la.get("rule_id"))):
            bad.append(f"{p}: rule id {la.get('rule_id')!r} is not <module>.read_{f}")
        if la.get("normalisation_rule") != NORMALISATION[f]:
            bad.append(f"{p}: normalisation rule {la.get('normalisation_rule')!r}, not {NORMALISATION[f]}")
        if la.get("label_subject") != ent[entity] or la.get("label_predicate") != pred:
            bad.append(f"{p}: the subject or the predicate differs from the field table")
        if la.get("about_entity") != ent[ABOUT[f]]:
            bad.append(f"{p}: about_entity is not the IRI of the entity that holds the value")
        if "option_probabilities" in la or "in_sample" in la:
            bad.append(f"{p}: a value label has option probabilities or the key in_sample")
        vrec = next((v for v in records if v.get("instance_path") == p), None)
        inst = str(value_at(r.ech, p)) if value_exists(r.ech, p) else None
        if vrec is not None and inst is not None:
            if not (la.get("label_object") == inst == vrec.get("recorded_value")):
                bad.append(f"{p}: the label gives {str(la.get('label_object'))[:60]!r}, the instance "
                           f"{inst[:60]!r} and the value record {str(vrec.get('recorded_value'))[:60]!r}")
            if vrec.get("about_entity") != la.get("about_entity"):
                bad.append(f"{p}: about_entity of the label and of the value record differ")
            if not vrec.get("pdf_evidence"):
                bad.append(f"{p}: the value record has no PDF evidence")
    return result("C12", bad, value_labels=len(labels), value_records_by_rule=len(records))


# ------------------------------------------------------------------ C13 (V3)
def check_c13(r: Record) -> dict:
    bad = []
    leaves = Counter(p for p, v in leaf_paths(r.ech) if v is not None)
    recs = Counter(v.get("instance_path") for v in r.value_records())
    for p in sorted(set(leaves) | set(recs)):
        if leaves.get(p, 0) != 1 or recs.get(p, 0) != 1:
            bad.append(f"{p}: {leaves.get(p, 0)} leaf of the instance and {recs.get(p, 0)} value records")
    for v in r.value_records():
        if v.get("derivation") not in RULE_T:
            bad.append(f"{v.get('instance_path')}: derivation {v.get('derivation')} is not one of rule T")
        if v.get("derivation") == BY_RULE and v.get("instance_path") not in {x[2] for x in FIELD_TABLE.values()}:
            bad.append(f"{v.get('instance_path')}: derivation {BY_RULE} for a path that is not in the field table")
    for p, _ in leaf_paths(r.ech):
        last = re.sub(r"\[\d+\]", "", p).rsplit(".", 1)[-1]
        if last in REGISTER_SLOTS or last == "document_url":
            bad.append(f"{p}: a slot that only the register knows has a value")
    for la in r.labels.get("label_assertions") or []:
        if la.get("label_kind") == "export_value" or la.get("label_source") == "export":
            bad.append(f"{last_part(la['global_uri'])}: a label from the export")
    return result("C13", bad, leaves=sum(leaves.values()), value_records=sum(recs.values()))


# ------------------------------------------------------------------ C14 (V4)
def check_c14(r: Record, export_record: dict | None) -> dict:
    bad = []
    has_export = bool(r.man.get("has_export"))
    rec_of = {v.get("instance_path"): v for v in r.value_records()}
    labels = r.pdf_labels()
    for la in labels:
        p, ec = la.get("instance_path"), la.get("export_check")
        v = rec_of.get(p) or {}
        alt = [a.get("alternative_value") for a in v.get("alternatives") or []]
        if ec not in CONSISTENCY:
            bad.append(f"{p}: export_check {ec!r}")
            continue
        if v.get("pdf_consistency") != CONSISTENCY[ec]:
            bad.append(f"{p}: pdf_consistency {v.get('pdf_consistency')} with {ec}")
        if ec == "differs_from_export" and alt != [la.get("export_value")]:
            bad.append(f"{p}: the alternative of the value record is not the export value of the label")
        if ec != "differs_from_export" and alt:
            bad.append(f"{p}: an alternative with {ec}")
        if ec in ("no_export_value", "not_compared") and ("export_value" in la or v.get("metadata_evidence")):
            bad.append(f"{p}: an export value or metadata evidence with {ec}")
        if ec in ("equal_to_export", "differs_from_export") and not (la.get("export_value") and v.get("metadata_evidence")):
            bad.append(f"{p}: no export value or no metadata evidence with {ec}")
        if not has_export and ec != "not_compared":
            bad.append(f"{p}: {ec} in a record with no export record")
    for name, g in r.gaps().items():
        if "export_has_value" in g and not has_export:
            bad.append(f"gap {name}: export_has_value in a record with no export record")
        if "export_value" in g:
            bad.append(f"gap {name}: a gap record holds an export value")
    field_paths = {x[2] for x in FIELD_TABLE.values()}
    for v in r.value_records():
        p = v.get("instance_path")
        if p in field_paths:
            continue
        if p == "affairs[0].global_uri":
            alt = v.get("alternatives") or []
            reg = r.man.get("register_affair_iri")
            if has_export:
                if not (isinstance(reg, str) and re.fullmatch(re.escape(REGISTER_AFFAIR) + r"\d+", reg)):
                    bad.append("register_affair_iri is not the register address of an affair")
                if [a.get("alternative_value") for a in alt] != [reg] or not v.get("metadata_evidence") \
                        or any(a.get("alternative_source") != REGISTER_ALTERNATIVE_SOURCE for a in alt):
                    bad.append("the value record of the affair IRI does not give the register address as its one "
                               "alternative with metadata evidence")
            elif alt or v.get("metadata_evidence") or reg is not None:
                bad.append("a register address of the affair in a record with no export record")
        elif v.get("metadata_evidence") or v.get("alternatives"):
            bad.append(f"{p}: export evidence for a value that is not compared with the export")
    recalculated = False
    writer_checked = False
    if has_export and export_record is not None:
        recalculated = True
        aid = (export_record.get("affair") or {}).get("id")
        if r.man.get("register_affair_iri") != f"{REGISTER_AFFAIR}{aid}":
            bad.append("register_affair_iri is not the address of the affair of the export record")
        try:
            import m12_writer as wr  # noqa: PLC0415  (optional: rule 3 of chapter 3; V2)
            writer_cc = getattr(wr, "cross_check", None)
        except ImportError:
            writer_cc = None
        for la in labels:
            f = field_of_label(la)
            if f is None:
                continue
            want = cross_check(f, r.comparison(la), export_record, r.language)
            if (la.get("export_check"), la.get("export_value")) != (want["export_check"], want["export_value"]):
                bad.append(f"{f}: the label stores {la.get('export_check')} with the export value "
                           f"{str(la.get('export_value'))[:60]!r}; the export record gives {want['export_check']} "
                           f"with {str(want['export_value'])[:60]!r}")
            if writer_cc is not None:
                writer_checked = True
                w = writer_cc(f, r.comparison(la), export_record, r.language)
                if (w.get("export_check"), w.get("export_value")) != (want["export_check"], want["export_value"]):
                    bad.append(f"{f}: m12_writer.cross_check and the second calculation of this file differ")
        for name, g in r.gaps().items():
            if name not in FIELD_TABLE:
                continue
            want = cross_check(name, None, export_record, r.language)["has_reference"]
            if g.get("export_has_value") != want:
                bad.append(f"gap {name}: export_has_value {g.get('export_has_value')}, the export record gives {want}")
    if not has_export and export_record is not None:
        bad.append("an export record was given for a record whose manifest says has_export false")
    return result("C14", bad, has_export=has_export, recalculated_from_the_export_record=recalculated,
                  compared_with_m11_writer_cross_check=writer_checked)


# ------------------------------------------------------------------ C15 (V5)
def expected_slots(r: Record) -> dict:
    """{slot: (state, reason, cascade rules or None)} by the table of record_form.md chapter 6, made from the
    record and from the label selection of the cascade (made again). The third part is a list for a slot that
    the cascade does not give to the kind of the document."""
    label_fields = {field_of_label(la) for la in r.pdf_labels()}
    gaps = r.gaps()
    weak = r.candidates()
    not_read = {x.get("field"): x.get("reason") for x in r.man.get("fields_not_read") or []}
    cs = r.cascade()
    scope = scope_fields(r)
    a = r.affair
    sub = a.get("submission") or {}
    resp = (a.get("response_steps") or [{}])[0] or {}
    texts = {"Submission.texts": bool(sub.get("texts")), "ResponseStep.texts": bool(resp.get("texts"))}
    written = {"Submission": "submission" in a, "ResponseStep": bool(a.get("response_steps"))}
    out: dict = {}
    for slot in i95_slots():
        cls, name = slot.split(".", 1)
        f = FIELD_OF_SLOT.get(slot)
        if f:
            rules = None if cs["selection"][f]["searched"] else list(cs["selection"][f]["rules"])
            if f in label_fields:
                out[slot] = ("read_from_pdf", "value_read", rules)
            elif f in gaps and f in weak and rules is None:
                # decision W-3: the gap record has the reason code of the label schema, the manifest the reason of the floor
                out[slot] = (("not_found_in_pdf", WEAK_REASON) if (gaps[f].get("slot_state"), gaps[f].get("gap_reason"))
                             == CANDIDATE_GAP else (gaps[f].get("slot_state"), gaps[f].get("gap_reason"))) + (None,)
            elif f in gaps and f in scope and (gaps[f].get("slot_state"), gaps[f].get("gap_reason")) == SCOPE_GAP:
                # finding S3-01: the gap record has the reason code of the label schema, the manifest the reason reader_scope
                out[slot] = SCOPE_SLOT + (None,)
            elif f in gaps:
                out[slot] = (gaps[f].get("slot_state"), gaps[f].get("gap_reason"), rules)
            else:
                out[slot] = ("not_found_in_pdf", not_read.get(f, "?"), rules)
        elif slot in texts:
            if texts[slot]:
                out[slot] = ("read_from_pdf", "text_blocks", None)
            elif not cs["texts"][slot][0]:
                out[slot] = NOT_IN_TYPE + (list(cs["texts"][slot][1]),)
            else:
                out[slot] = ("not_found_in_pdf", "no_block_of_role", None)
        elif name == "global_uri":
            out[slot] = ("register_only", "minted_iri", None)
        elif name in REGISTER_SLOTS:
            out[slot] = ("register_only", "register_only", None)
        elif name in OTHER_STEP_SLOTS:
            out[slot] = NOT_IN_TYPE + (None,)
        elif slot not in STEP_OF:
            out[slot] = ("not_found_in_pdf", "no_rule_searched", None)
    for slot, cls in STEP_OF.items():
        if written[cls]:
            out[slot] = ("read_from_pdf", "step_written", None)
        elif not cs["steps"][slot][0]:
            out[slot] = NOT_IN_TYPE + (list(cs["steps"][slot][1]),)
        else:
            out[slot] = ("not_found_in_pdf", "no_value_of_the_step", None)
    return out


def check_c15(r: Record, ech_graph=None) -> dict:
    bad = []
    slots = r.man.get("slots")
    if not isinstance(slots, list):
        return result("C15", ["the manifest has no list slots"])
    names = Counter(s.get("slot") for s in slots)
    want_names = i95_slots()
    for n in sorted(set(names) | set(want_names), key=str):
        if names.get(n, 0) != 1 or n not in want_names:
            bad.append(f"{n}: {names.get(n, 0)} entries in the list slots; I95 has "
                       f"{'this slot' if n in want_names else 'no such slot'}")
    labels = r.pdf_labels()
    label_fields = Counter(field_of_label(la) for la in labels)
    gaps = r.gaps()
    weak = r.candidates()
    for f in weak:
        if f not in gaps or label_fields.get(f):
            bad.append(f"{f}: a candidate label needs a gap record, and the field has no written value")
    not_read = Counter(x.get("field") for x in r.man.get("fields_not_read") or [])
    for x in r.man.get("fields_not_read") or []:
        if x.get("field") not in FIELD_TABLE or x.get("reason") not in NOT_READ_REASONS:
            bad.append(f"fields_not_read: {x} is not a field with one of the reasons {NOT_READ_REASONS}")
    for f in FIELDS:
        n = (label_fields.get(f, 0), int(f in gaps), not_read.get(f, 0))
        if sum(n) != 1:
            bad.append(f"{f}: {n[0]} value labels, {n[1]} gap records and {n[2]} entries in fields_not_read; "
                       "exactly one of them is necessary")
    for name, g in gaps.items():
        if name not in FIELD_TABLE:
            bad.append(f"gap {name}: not a field")
            continue
        if (g.get("slot_state"), g.get("gap_reason")) not in GAP_PAIRS:
            bad.append(f"gap {name}: state {g.get('slot_state')} with the reason {g.get('gap_reason')}")
        if g.get("gap_slot") != FIELD_TABLE[name][1]:
            bad.append(f"gap {name}: gap_slot is not the predicate of the field")
        if value_exists(r.ech, FIELD_TABLE[name][2]):
            bad.append(f"{name}: a gap record and a value in the instance")
        if ech_graph is not None:
            import rdflib  # noqa: PLC0415
            n = sum(1 for _ in ech_graph.triples((None, rdflib.URIRef(FIELD_TABLE[name][1]), None)))
            if n:
                bad.append(f"{name}: a gap record and {n} statements with its predicate in the eCH-0295 graph")
    want = expected_slots(r)
    kind = r.cascade()["kind"]
    selection = r.cascade()["selection"]
    for f in FIELDS:
        # finding S3-01: only the selection of the cascade gives the state "not searched in this kind of document"
        if selection[f]["searched"] and f in gaps and gaps[f].get("slot_state") == NOT_IN_TYPE[0]:
            bad.append(f"{f}: the gap record has the state {NOT_IN_TYPE[0]}, but the cascade searches this value in a "
                       f"document of the kind {kind} (cascade rules {', '.join(selection[f]['rules'])})")
    for s in slots:
        slot = s.get("slot")
        if slot not in want:
            continue
        sf = FIELD_OF_SLOT.get(slot)
        if sf and selection[sf]["searched"] and s.get("state") == NOT_IN_TYPE[0]:
            bad.append(f"{slot}: the manifest gives the state {NOT_IN_TYPE[0]}, but the cascade searches this value "
                       f"in a document of the kind {kind}: a searched value is read, or it is not found in the PDF")
        if s.get("reason") == SCOPE_SLOT[1] and (sf is None or sf not in scope_fields(r)):
            bad.append(f"{slot}: the reason {SCOPE_SLOT[1]} is only for a searched value whose rule gives the reason "
                       f"{SCOPE_READER_REASON}")
        if s.get("state") not in STATES or not s.get("reason"):
            bad.append(f"{slot}: state {s.get('state')!r} is not one of the 4 states, or the reason is absent")
        if (s.get("state"), s.get("reason")) != want[slot][:2]:
            bad.append(f"{slot}: the manifest gives {s.get('state')} ({s.get('reason')}); the record gives "
                       f"{want[slot][0]} ({want[slot][1]})")
        rules = want[slot][2]
        if rules is not None and s.get("state") == NOT_IN_TYPE[0]:
            # decision D1: the state "not searched in this kind of document" with the kind and the cascade rule ids
            if (s.get("result"), s.get("kind"), s.get("cascade_rules")) != (NOT_SEARCHED, kind, rules):
                bad.append(f"{slot}: the entry does not give the result {NOT_SEARCHED!r} with the kind {kind} and the "
                           f"cascade rules {rules}")
        elif any(k in s for k in ("result", "kind", "cascade_rules")):
            bad.append(f"{slot}: the entry has the keys of a slot that the cascade does not search, but the cascade "
                       f"gives the slot to the kind {kind}")
        f = FIELD_OF_SLOT.get(slot)
        if s.get("field") != f:
            bad.append(f"{slot}: key field {s.get('field')!r}, not {f!r}")
        want_label = f"pdf-{f}" if f and label_fields.get(f) else f"candidate-{f}" if f and f in weak else None
        want_gap = f if f and f in gaps else None
        if s.get("label_id") != want_label or s.get("gap_id") != want_gap:
            bad.append(f"{slot}: label_id or gap_id does not name the label or the gap record of the field")
    counts = r.man.get("counts") or {}
    by_state = {st: sum(1 for s in slots if s.get("state") == st) for st in STATES}
    if counts.get("slots") != by_state:
        bad.append(f"counts.slots {counts.get('slots')} differs from the list {by_state}")
    n_no_rule = sum(1 for s in slots if s.get("reason") == "no_rule_searched")
    if counts.get("slots_no_rule_searched") != n_no_rule:
        bad.append(f"counts.slots_no_rule_searched {counts.get('slots_no_rule_searched')} differs from {n_no_rule}")
    state_of = {s.get("slot"): s.get("state") for s in slots}
    field_states = Counter(state_of.get(SLOT_OF_FIELD[f]) for f in FIELDS)
    want_cv = {"fields": len(FIELDS), "read_from_pdf": field_states.get("read_from_pdf", 0),
               "not_found_in_pdf": field_states.get("not_found_in_pdf", 0),
               "not_in_this_document_type": field_states.get("not_in_this_document_type", 0),
               "weak_candidates": sum(1 for f in weak if r.cascade()["selection"][f]["searched"]),
               "addressee_candidates": sum(1 for f in weak if not r.cascade()["selection"][f]["searched"]),
               "certain": sum(1 for la in labels if la.get("value_status") == "certain"),
               "unsure": sum(1 for la in labels if la.get("value_status") == "unsure"),
               "export_check": {k: sum(1 for la in labels if la.get("export_check") == k) for k in CONSISTENCY}}
    cv = counts.get("values") or {}
    if {k: cv.get(k) for k in want_cv} != want_cv:
        bad.append(f"counts.values {cv} differs from the record {want_cv}")
    if r.man.get("schema") != MANIFEST_SCHEMA:
        bad.append(f"the manifest schema is {r.man.get('schema')!r}, not {MANIFEST_SCHEMA}")
    return result("C15", bad, slots=len(slots), by_state=by_state, gap_records=len(gaps))


# ------------------------------------------------------------------ C16 (V6)
def expected_probability(field: str, tier: str, doc_id, s1_role, calib: dict) -> dict | None:
    """The lookup rule of record_form.md chapter 3.2. None: the calibration file has no entry of the field."""
    f = CALIBRATION_FIELD.get(field, field)
    look = (calib.get("lookup") or {}).get(f)
    if look is None:
        return None
    t = (look.get("tiers") or {}).get(tier)
    # decision D4: the value of the tier over all folds, for each document; the fold value is not used
    stored = ((calib.get("documents") or {}).get(str(doc_id)) or {}).get(f)
    in_sample = bool(stored and stored.get("tier") == tier and stored.get("outcome") in ("equal", "different"))
    p = t["p_all_folds"] if t else look["p_of_a_tier_with_no_unit"]
    primary = field not in PRIMARY_ROLE_FIELDS or s1_role in PRIMARY_ROLES
    certain = bool(look.get("entry") == "written_with_status" and primary and look.get("a") is not None
                   and t is not None and p >= look["a"] and t.get("enough_units") and t.get("certain_tier"))
    return {"p": cal.as_written(p), "status": "certain" if certain else "unsure",
            "cid": cal.cal_id("value", f, tier), "from": PROBABILITY_FROM if t else "no unit of the pair",
            "entry": look.get("entry"), "in_sample": in_sample}


def check_c16(r: Record, calib: dict | None, info: dict | None = None) -> dict:
    """`info`: the facts of calibration_choice (finding S3-02). Its problems are problems of this check."""
    info = info or {"source": "a calibration file as a dict, given by the caller" if calib is not None else
                    "no calibration file (the caller gave none)", "problems": []}
    bad = list(info.get("problems") or [])
    cals = {c.get("global_uri"): c for c in r.labels.get("calibrations") or []}
    for la in r.value_labels():
        f = field_of_label(la)
        name = last_part(la["global_uri"])
        p = la.get("label_probability")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not P_MIN <= p <= P_MAX:
            bad.append(f"{name}: probability {p!r} is not a number from {P_MIN} to {P_MAX}")
        elif cal.as_written(p) != p:
            bad.append(f"{name}: probability {p!r} is not written with 4 decimals after the clip")
        if la.get("value_status") not in ("certain", "unsure"):
            bad.append(f"{name}: value status {la.get('value_status')!r}")
        if not vb.TIER_RX.match(str(la.get("tier"))):
            bad.append(f"{name}: tier {la.get('tier')!r} does not have the form of a tier name")
            continue
        c = cals.get(la.get("calibration"))
        if c is None:
            bad.append(f"{name}: the label file has no calibration record {la.get('calibration')}")
        elif f is not None:
            want_id = cal.cal_id("value", CALIBRATION_FIELD.get(f, f), la["tier"])
            if last_part(c["global_uri"]) != want_id or c.get("calibrated_kind") != "pdf_value" \
                    or c.get("calibrated_tier") != la["tier"] or c.get("calibrated_slot") != la.get("label_predicate"):
                bad.append(f"{name}: the calibration record is not the record {want_id} of the kind pdf_value "
                           "with the tier and the predicate of the label")
        if calib is not None and f is not None:
            want = expected_probability(f, la["tier"], r.man.get("doc_id"), r.man.get("s1_rule_role"), calib)
            if want is None:
                bad.append(f"{name}: the calibration file has no lookup entry of the field")
            elif want["entry"] == "left_out_not_measured":
                bad.append(f"{name}: the calibration file leaves the field out (rule G7), but the record has a label")
            elif (p, la.get("value_status")) != (want["p"], "unsure" if name.startswith("candidate-") else want["status"]):
                bad.append(f"{name}: probability {p} and status {la.get('value_status')}; the calibration file "
                           f"gives {want['p']} and {want['status']} ({want['from']}: the value of the rule tier)")
            elif c is not None and "in_sample" in c and str(r.man.get("doc_id")).isdigit() \
                    and c.get("in_sample") != want["in_sample"]:
                bad.append(f"{name}: the calibration record says in_sample {c.get('in_sample')}; the calibration file "
                           f"gives {want['in_sample']} for this document and this tier")
    vc = r.man.get("value_calibration") or {}
    if vc.get("probability_from") != PROBABILITY_FROM:
        bad.append(f"the manifest key value_calibration.probability_from is {vc.get('probability_from')!r}, not "
                   f"{PROBABILITY_FROM!r} (the probability of a label is the value of its rule tier)")
    return result("C16", bad, labels=len(r.value_labels()), calibration_file_at_hand=calib is not None,
                  calibration_file={k: v for k, v in info.items() if k != "problems"},
                  probability_from=PROBABILITY_FROM)


# ------------------------------------------------------------------ C17 (V7)
def check_c17(r: Record) -> dict:
    slots, bad = recorded_gap_slots(r.man)
    gaps = tuple(slots)
    want = sorted(gp.gap_path(s) for s in gaps)
    strict = gp.linkml_messages(r.ech)
    absent = gp.absent_required(r.ech)
    precedent = gp.precedent_paths(r.ech)
    relaxed = None
    if absent != want or precedent != want:
        bad.append(f"the absent required slots of I95 are {absent} (second method: {precedent}); the recorded gaps "
                   f"are {want}")
    if r.man.get("conformance") != gp.conformance(gaps):
        bad.append(f"conformance {r.man.get('conformance')!r}, not {gp.conformance(gaps)}")
    if gaps:
        if not strict:
            bad.append("I95 with no change accepts the record, but the manifest records a gap")
        relaxed = gp.linkml_messages(r.ech, gaps)
        if relaxed:
            bad.append(f"I95 with the recorded gap slots not required gives {len(relaxed)} messages: {relaxed[0][:200]}")
        bad += gp.instance_gap_problems(r.ech, gaps)
        notes = r.prov.get("not_mapped_records") or []
        pdf_gaps = r.gaps()
        not_read = {x.get("field") for x in r.man.get("fields_not_read") or []}
        for s in gaps:
            mine = [n for n in notes if n.get("not_mapped_item") == gp.NOT_MAPPED_ITEM[s]]
            if len(mine) != 1:
                bad.append(f"{s}: {len(mine)} NotMappedRecords with the item {gp.NOT_MAPPED_ITEM[s]} (1 is necessary)")
            elif "candidate_value" in mine[0]:
                bad.append(f"{s}: the NotMappedRecord of the gap holds a candidate value")
            if s not in pdf_gaps and s not in not_read:
                bad.append(f"{s}: the label file has no gap record for the recorded gap")
    elif strict:
        bad.append(f"I95 with no change gives {len(strict)} messages for a record with no recorded gap: {strict[0][:200]}")
    return result("C17", bad, conformance=gp.conformance(gaps), i95_gaps=list(gaps),
                  i95_messages_with_no_change=len(strict),
                  i95_messages_with_the_gap_slots_not_required=None if relaxed is None else len(relaxed),
                  absent_required=absent)


# ------------------------------------------------------------------ C18
def check_c18(r: Record, graphs: dict | None = None) -> dict:
    bad = []
    rec = r.man.get("record_iri") or ""
    src = r.man.get("source_iri") or ""
    urn = RX_URN_SOURCE.match(src)
    if urn:
        if rec != src + "/record":
            bad.append("the record IRI of an unknown PDF is not <source document>/record")
        sha = r.block_file.get("pdf_sha256")
        if sha and sha != urn.group(1):
            bad.append("the hash in the source IRI is not the pdf_sha256 of the block file")
    elif src.startswith(SOURCE_KNOWN) and src[len(SOURCE_KNOWN):].isdigit():
        d = src[len(SOURCE_KNOWN):]
        if not re.fullmatch(r"https?://[^\s<>\"{}|\\^`]+/gj/record/doc-" + d, rec):
            bad.append(f"the record IRI of document {d} is not <base>gj/record/doc-{d}")
        if str(r.man.get("doc_id")) != d:
            bad.append("doc_id of the manifest is not the document of the source IRI")
    else:
        bad.append(f"the source IRI {src[:80]!r} has no permitted form")
    a = r.ech.get("affairs")
    if not isinstance(a, list) or len(a) != 1:
        bad.append("the record does not have exactly one affair")
    if len(r.affair.get("response_steps") or []) > 1:
        bad.append("the record has 2 or more response steps")
    want = {"global_uri": f"{rec}/i95", "affairs[0].global_uri": f"{rec}/affair",
            "affairs[0].submission.global_uri": f"{rec}/affair/step/submission",
            "affairs[0].response_steps[0].global_uri": f"{rec}/affair/step/response",
            "affairs[0].response_steps[0].responder.global_uri": f"{rec}/actor/responder",
            "affairs[0].submission.sponsorship[0].actor.global_uri": f"{rec}/actor/sponsor-1"}
    for p, v in leaf_paths(r.ech):
        if p.endswith("global_uri") and want.get(p) != v:
            bad.append(f"{p}: {str(v)[:100]!r} is not the minted IRI {want.get(p, 'of a known path')!r}")
        if isinstance(v, str) and v.startswith(REGISTER_AFFAIR):
            bad.append(f"{p}: the register address of an affair is a value of the eCH-0295 part")
    for key, w in (("container_iri", f"{rec}/i95"), ("affair_iri", f"{rec}/affair")):
        if r.man.get(key) != w:
            bad.append(f"manifest key {key} is not {w}")
    if r.man.get("named_graphs") != {g: f"{rec}/{g}" for g in rdf.GRAPHS}:
        bad.append("the named graphs of the manifest are not <record IRI>/<graph name>")
    for key, w in (("describes_record", rec), ("ech_delivery", f"{rec}/i95"), ("source_document", src)):
        if r.labels.get(key) != w:
            bad.append(f"label file key {key} is not {w}")
    for la in r.labels.get("label_assertions") or []:
        name = last_part(la.get("global_uri", ""))
        if not str(la.get("global_uri", "")).startswith(f"{rec}/label/"):
            bad.append(f"label {name}: its IRI is not below <record IRI>/label/")
        for k in ("label_subject", "label_object", "about_entity"):
            if str(la.get(k, "")).startswith(REGISTER_AFFAIR):
                bad.append(f"label {name}: {k} is the register address of an affair")
        if la.get("label_kind") == "pdf_value":
            candidate = name.startswith("candidate-")      # a candidate has no entity in the eCH-0295 part
            for k in ("label_subject", "model_run") if candidate else ("label_subject", "about_entity", "model_run"):
                v = str(la.get(k, ""))
                if not (v.startswith(rec + "/") or (candidate and k == "label_subject" and v == rec)):
                    bad.append(f"label {name}: {k} is not below the record IRI")
    for name, g in r.gaps().items():
        if g.get("global_uri") != f"{rec}/gap/{name}":
            bad.append(f"gap {name}: its IRI is not <record IRI>/gap/<field>")
        subj = str(g.get("gap_subject", ""))
        if not (subj == rec or subj.startswith(rec + "/")):
            bad.append(f"gap {name}: gap_subject is not the record IRI or an IRI below it")
    for v in r.value_records():
        if v.get("derivation") == "identifier_minted" and not str(v.get("recorded_value", "")).startswith(rec + "/"):
            bad.append(f"{v.get('instance_path')}: a minted identifier is not below the record IRI")
    n_graph = 0
    if graphs:
        import rdflib  # noqa: PLC0415
        for gname in ("ech-0295", "labels"):
            for t in graphs.get(gname) or ():
                for x in (t[0], t[2]):
                    if isinstance(x, rdflib.URIRef) and str(x).startswith(REGISTER_AFFAIR):
                        n_graph += 1
        if n_graph:
            bad.append(f"{n_graph} IRIs of the register address of an affair in the eCH-0295 graph or the label graph")
    return result("C18", bad, record_iri=rec, known_document=not urn)


# ------------------------------------------------------------------ C19
def calendar_day(v) -> bool:
    if not isinstance(v, str) or not RX_DAY.match(v):
        return False
    try:
        dt.date.fromisoformat(v)
    except ValueError:
        return False
    return True


def check_c19(r: Record) -> dict:
    bad, info = [], []
    a = r.affair
    lang = r.language

    def get(field):
        p = FIELD_TABLE[field][2]
        return value_at(r.ech, p) if value_exists(r.ech, p) else None

    t = get("affair_type")
    if t is not None and t not in affair_types():
        bad.append(f"affair_type {t!r} is not a value of the AffairTypeEnum of I95")
    for f in ("submission_date", "response_date"):
        v = get(f)
        if v is not None and not calendar_day(v):
            bad.append(f"{f} {v!r} is not a calendar day in the form YYYY-MM-DD")
    for f in ("title", "affair_number", "sponsor", "responder"):
        v = get(f)
        if v is not None and (not isinstance(v, str) or not v.strip() or v != v.strip() or "\n" in v):
            bad.append(f"{f}: the value is empty, or it has a line end or a space at its start or end")
    v = get("responder")
    if isinstance(v, str) and vn.body_word(v) is None:
        bad.append(f"responder {v[:80]!r} has no body word of table 3 of addendum G (a person name is not a responder)")
    # decisions D1, D2 and D3: a step, a text block and a head value only if a document of this kind can state it
    cs = r.cascade()
    kind = cs["kind"]
    sub = a.get("submission") or {}
    resp = (a.get("response_steps") or [{}])[0] or {}
    # a step and a text block only if the cascade gives them to the kind (it includes decision D3: no response
    # step in a proposal; it replaces decision W-5)
    for holder, step, name in (("Affair.submission", sub, "submission"), ("Affair.response_steps", resp, "response")):
        if step and not cs["steps"][holder][0]:
            bad.append(f"a {name} step in a document of the kind {kind}: a document of this kind gets no {name} step "
                       f"(cascade rules {', '.join(cs['steps'][holder][1])})")
    for slot, step in (("Submission.texts", sub), ("ResponseStep.texts", resp)):
        if step.get("texts") and not cs["texts"][slot][0]:
            bad.append(f"{len(step['texts'])} text blocks in the slot {slot} of a document of the kind {kind}: the "
                       f"cascade does not give this slot to the kind (cascade rules {', '.join(cs['texts'][slot][1])}); "
                       f"such a text block stays a TextBlockRecord of the provenance file")
    for name, holder, fields in (("submission", sub, ("submission_date", "sponsor")),
                                 ("response", resp, ("response_date", "responder"))):
        if holder and not holder.get("texts") and not any(get(f) is not None for f in fields):
            bad.append(f"a {name} step with no value and no text block")
    for f in FIELDS:
        if get(f) is not None and not cs["selection"][f]["searched"]:
            bad.append(f"{f}: a value in a document of the kind {kind}; the cascade does not search this value for "
                       f"the kind (cascade rules {', '.join(cs['selection'][f]['rules'])})")
    if get("sponsor") is not None:
        sp = ((a.get("submission") or {}).get("sponsorship") or [{}])[0]
        if sp.get("sponsor_role") != "sponsor":
            bad.append("the sponsorship of the first author does not have the role sponsor")
    for p, v in leaf_paths(r.ech):
        if p.endswith("text_language") and (v not in LANGUAGES or v != lang):
            bad.append(f"{p}: {v!r} is not the language of the block file ({lang!r})")
    for p in ("affairs[0].response_steps[0].responder.name[0]", "affairs[0].submission.sponsorship[0].actor.name[0]"):
        if value_exists(r.ech, p) and not value_at(r.ech, p).get("text_language"):
            bad.append(f"{p}: a name with no language")
    return result("C19", bad, information=info, kind=kind)


# ------------------------------------------------------------------ C20 (V8): the value follows from the wording
def one_line(wording: str) -> str:
    """The printed wording on one line (rule printed_wording_one_line): m11_values_base.norm_text."""
    return vb.norm_text(wording)


RX_COMPOUND_BREAK = re.compile(r"(?<=[a-zà-ÿ])-[ \t]*\n[ \t]*(?=[A-ZÀ-Ý][a-zà-ÿ])")


def title_value(wording: str) -> str:
    """The printed title on one line (record_form.md chapter 2.3, rule 2b): norm_title of the title reader; a
    hyphen at a line end between a lower-case letter and a word with an upper-case first letter keeps the two
    words as one compound ("Basel-" + line end + "Stadt" gives "Basel-Stadt"), if the comparison form does not
    change."""
    reader = mt.norm_title(wording)
    v = mt.norm_title(RX_COMPOUND_BREAK.sub("-", wording))
    return v if vn.fold(v) == vn.fold(reader) else reader


def remake(field: str, text: str, start: int, end: int, tier: str) -> dict:
    """The values that follow from the document text at a span by the stated rule of the field (record_form.md
    chapter 2.3). Keys: values (the permitted record values; empty: the wording gives no value of the field),
    rule (the rule in words) and, for the responder, comparison (the table form of the body).
    The functions are those of the FIXED rule modules and of m11_values_base. No export value is used."""
    w = text[start:end]
    if field == "affair_type":
        v = tn._type_value(w)
        values = {v} if v else set()
        m = tn.MM_RX.match(text, start)
        if m and m.end() == end:
            values.add("draft_decree")                   # tier type_government_head: "MM N. 91/2019"
        return {"values": values, "rule": "the list value of the printed type word (term list typ_lokal); the short "
                                          "form MM before a number (Messaggio municipale) gives draft_decree"}
    if field == "title":
        return {"values": {title_value(w)}, "comparison": mt.norm_title(w),
                "rule": "the printed wording on one line (norm_title of the title reader; a compound over a line end "
                        "stays one word)"}
    if field == "affair_number":
        values = {tn.normal_number(w)}
        m = tn.PREFIX_NR_RX.match(w)
        if m and m.span(1) == (0, len(w)):
            values.add(m.group(2) + " " + tn.normal_number(m.group(3)))     # "MM N. 91/2019" gives "MM 91/2019"
        return {"values": values, "rule": "the printed number with no space at a separator; in the form <letters> "
                                          "N. <number>/<year> the cue N. is left out"}
    if field in ("submission_date", "response_date"):
        hits = vb.find_dates(w)
        ok = len(hits) == 1 and (hits[0].start, hits[0].end) == (0, len(w))
        return {"values": {hits[0].iso} if ok else set(), "rule": "the ISO day of the printed date (find_dates)"}
    if field == "responder":
        key = dr.body_key(vb.fold(one_line(w)))
        return {"values": {one_line(w)}, "comparison": key[1] if key else None,
                "rule": "the printed wording on one line; the comparison value is the table form of the body word"}
    if field == "sponsor":
        return {"values": {one_line(w)}, "rule": "the printed wording on one line; the comparison value is a run of "
                                                 "the folded words of the printed name"}
    raise ValueError(f"unknown field {field}")


def token_run(short: list, long: list) -> bool:
    n = len(short)
    return n > 0 and any(long[i:i + n] == short for i in range(len(long) - n + 1))


def check_c20(r: Record) -> dict:
    bad = []
    text = r.doc.text
    labels = r.value_labels()
    comp = r.man.get("comparison_values")
    if not isinstance(comp, dict):
        bad.append("the manifest has no key comparison_values")
        comp = {}
    fields = {field_of_label(la) for la in labels}
    if set(comp) != fields - {None}:
        bad.append(f"comparison_values names the fields {sorted(comp)}; the value labels are for {sorted(f for f in fields if f)}")
    made = 0
    for la in labels:
        f = field_of_label(la)
        name = last_part(la.get("global_uri", ""))
        s, e = la.get("span_start"), la.get("span_end")
        if f is None or not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text)):
            bad.append(f"{name}: no field or no span: the value cannot be made again")
            continue
        value = la.get("label_object")
        got = remake(f, text, s, e, str(la.get("tier")))
        made += 1
        if value not in got["values"]:
            bad.append(f"{name}: the record gives {str(value)[:70]!r}; the document text at {s} to {e} is "
                       f"{text[s:e][:70]!r} and gives {sorted(got['values']) or 'no value'} (rule: {got['rule']})")
        p = la.get("instance_path")
        if p and value_exists(r.ech, p) and str(value_at(r.ech, p)) not in got["values"]:
            bad.append(f"{name}: the eCH-0295 part gives {str(value_at(r.ech, p))[:70]!r} at {p}; the wording at the span "
                       f"gives {sorted(got['values']) or 'no value'}")
        c = comp.get(f)
        note = str(la.get("label_note") or "")
        if f == "responder":
            if c is None or c != got["comparison"]:
                bad.append(f"{name}: the comparison value {c!r} is not the table form {got['comparison']!r} of the printed body word")
            if vn.body_word(str(value)) is None or vn.body_word(str(value)) != vn.body_word(c):
                bad.append(f"{name}: the printed name and the comparison value do not give the same body word")
        elif f == "sponsor":
            ct = vn.token_list(c)
            if not c or " ".join(ct) != c or not token_run(ct, vn.token_list(text[s:e])):
                bad.append(f"{name}: the comparison value {c!r} is not a run of the folded words of the printed name "
                           f"{text[s:e][:70]!r}")
        elif f == "title":
            if c != got["comparison"]:
                bad.append(f"{name}: the comparison value {str(c)[:70]!r} is not the one-line form of the title reader")
        elif c != value:
            bad.append(f"{name}: the comparison value {c!r} is not the value of the label")
        if (f in PRINTED_FIELDS or c != value) and not note.endswith(COMPARISON_NOTE + str(c)):
            bad.append(f"{name}: the note of the label does not give the comparison value of the reader")
    return result("C20", bad, values_made_again=made, export_record_used=False)


# ------------------------------------------------------------------ C21 (V9): the floor
def check_c21(r: Record, calib: dict | None) -> dict:
    bad = []
    cals = {c.get("global_uri"): c for c in r.labels.get("calibrations") or []}
    weak = r.candidates()
    gaps = r.gaps()
    slot_of = {s.get("field"): s for s in r.man.get("slots") or [] if s.get("field")}

    def stored(la: dict, name: str) -> list:
        """The stored probabilities of the pair of a label: from its calibration node and from the file."""
        out = []
        node = node_tier_probability(cals.get(la.get("calibration")))
        if node is None:
            bad.append(f"{name}: the calibration node has no parameter {TIER_P_PARAMETER}")
        else:
            out.append(node)
        f = field_of_label(la)
        if calib is not None and f is not None:
            p = tier_probability(f, str(la.get("tier")), calib)
            if p is None:
                bad.append(f"{name}: the calibration file has no lookup entry of the field")
            else:
                out.append(p)
                if node is not None and abs(node - p) > 1e-6 and (calib.get("calibrations") or {}).get(
                        cal.cal_id("value", CALIBRATION_FIELD.get(f, f), str(la.get("tier")))) is not None:
                    bad.append(f"{name}: the calibration node gives {node}, the calibration file {p}")
        return out

    for la in r.pdf_labels():
        name = last_part(la.get("global_uri", ""))
        ps = stored(la, name)
        if any(p < FLOOR_P for p in ps):
            bad.append(f"{name}: a value of the tier {la.get('tier')} is in the eCH-0295 part, and the stored "
                       f"probability of the tier is {min(ps)} (below {FLOOR_P}): the floor does not permit it")
    sel = r.cascade()["selection"]
    addressee = sorted(f for f in weak if not sel[f]["searched"])        # decision D3: not a candidate of the floor
    floor_fields = sorted(f for f in weak if sel[f]["searched"])
    for f, la in weak.items():
        name = last_part(la.get("global_uri", ""))
        ps = stored(la, name)
        is_addressee = f in addressee
        if is_addressee:
            if f != "responder" or r.cascade()["kind"] not in vcr.ADDRESSEE_KINDS or la.get("tier") not in vcr.ADDRESSEE_TIERS:
                bad.append(f"{name}: a candidate of a value that the cascade does not search; only the addressed body "
                           f"of a proposal (tier {', '.join(vcr.ADDRESSEE_TIERS)}) can be such a candidate")
        elif ps and not all(p < FLOOR_P for p in ps):
            bad.append(f"{name}: a candidate of a tier with the stored probability {max(ps)} (not below {FLOOR_P})")
        if "instance_path" in la or "about_entity" in la or value_exists(r.ech, FIELD_TABLE[f][2]):
            bad.append(f"{name}: a candidate has an instance path, or the eCH-0295 part has a value of the field")
        mark = ADDRESSEE_MARK if is_addressee else WEAK_MARK
        if la.get("value_status") != "unsure" or not str(la.get("label_note") or "").startswith(mark):
            bad.append(f"{name}: a candidate does not have the status unsure and the mark {mark!r}")
        if la.get("export_check") != "not_compared" or "export_value" in la:
            bad.append(f"{name}: a candidate has a cross-check result or an export value")
        g = gaps.get(f) or {}
        want_gap = NOT_IN_TYPE if is_addressee else CANDIDATE_GAP
        if (g.get("slot_state"), g.get("gap_reason")) != want_gap:
            bad.append(f"{name}: the field has no gap record with {want_gap}")
        sl = slot_of.get(f) or {}
        want_slot = NOT_IN_TYPE if is_addressee else ("not_found_in_pdf", WEAK_REASON)
        if (sl.get("state"), sl.get("reason")) != want_slot:
            bad.append(f"{name}: the slot of the manifest does not have the state {want_slot[0]} with the reason {want_slot[1]}")
    for f, sl in slot_of.items():
        if sl.get("reason") == WEAK_REASON and f not in floor_fields:
            bad.append(f"{f}: the manifest gives the reason {WEAK_REASON}, and the label file has no candidate")
    floor = r.man.get("value_floor") or {}
    if floor.get("threshold") != FLOOR_P or sorted(x.get("field") for x in floor.get("not_written") or []) != floor_fields:
        bad.append("the manifest key value_floor does not give the threshold and the fields of the candidates")
    if sorted(x.get("field") for x in r.man.get("addressee_candidates") or []) != addressee:
        bad.append("the manifest key addressee_candidates does not give the fields of the addressee candidates")
    return result("C21", bad, threshold=FLOOR_P, candidates=floor_fields, addressee_candidates=addressee,
                  calibration_file_at_hand=calib is not None)


# ------------------------------------------------------------------ C22 (V10): the values come from the readers
def check_c22(r: Record, calib: dict | None) -> dict:
    """Decision D6 (finding F-1): the cascade reader runs again on the block file and the rule file. Each field of
    the record must be the result of the readers: value, span, tier and slot state."""
    bad = []
    rd = r.reading()
    bad += list(rd.get("apertus_problems") or [])          # V3: the facts of the Apertus reading
    cs = r.cascade()
    kind, lang = rd["kind"], r.language
    pdf = {field_of_label(la): la for la in r.pdf_labels()}
    cand = r.candidates()
    gaps = r.gaps()
    not_read = {x.get("field"): x.get("reason") for x in r.man.get("fields_not_read") or []}
    comp = r.man.get("comparison_values") or {}
    cals = {c.get("global_uri"): c for c in r.labels.get("calibrations") or []}
    mc = r.man.get("cascade")
    if not isinstance(mc, dict):
        bad.append("the manifest has no key cascade (the label selection of the record)")
        mc = {}
    if mc.get("kind") != kind:
        bad.append(f"the manifest gives the kind {mc.get('kind')!r}; the {rd['kind_from']} gives {kind!r}")
    if mc.get("kind_source") != rd["kind_source"]:
        # rule V5: the kind of the rule chain and the 2 facts of the PDF (key v5) are a part of the comparison
        bad.append(f"the manifest gives the kind source {json.dumps(mc.get('kind_source'), ensure_ascii=False)[:160]}; "
                   f"the {rd['kind_from']} gives {json.dumps(rd['kind_source'], ensure_ascii=False)[:160]}")
    if mc.get("reader") != vcr.VERSION:
        bad.append(f"the record was made with the cascade reader {mc.get('reader')!r}; the reader of now is {vcr.VERSION!r}")
    slot_of = {s.get("field"): s for s in r.man.get("slots") or [] if s.get("field")}
    if mc.get("affair_type_of_the_cascade") != rd["affair_type_of_the_cascade"]:
        bad.append(f"the manifest gives the type {mc.get('affair_type_of_the_cascade')!r} for the cascade; the type "
                   f"reader gives {rd['affair_type_of_the_cascade']!r}")
    if mc.get("version") != casc.cascade()["version"]:
        bad.append(f"the record was made with the cascade {mc.get('version')!r}; the cascade file of now is "
                   f"{casc.cascade()['version']!r}")
    for f in FIELDS:
        want = {k: cs["selection"][f][k] for k in ("searched", "rules")}
        got = (mc.get("selection") or {}).get(f) or {}
        if {k: got.get(k) for k in ("searched", "rules")} != want:
            bad.append(f"{f}: the selection of the manifest is not the selection of the cascade for the kind {kind} "
                       f"(searched {want['searched']}, rules {want['rules']})")

    def same_place(f: str, la: dict, x: dict, what: str) -> None:
        name = last_part(la.get("global_uri", ""))
        if (la.get("span_start"), la.get("span_end")) != (x["char_start"], x["char_end"]):
            bad.append(f"{name}: the span {la.get('span_start')} to {la.get('span_end')} is not the span of the {what} "
                       f"of the readers ({x['char_start']} to {x['char_end']}, wording {str(x['value'])[:60]!r})")
        if la.get("tier") != x["tier"]:
            bad.append(f"{name}: the tier {la.get('tier')!r} is not the tier of the {what} of the readers ({x['tier']!r})")
        if la.get("value_wording") != x["value"]:
            bad.append(f"{name}: the wording is not the wording of the {what} of the readers")
        if comp.get(f) != x["normalised"]:
            bad.append(f"{name}: the comparison value {str(comp.get(f))[:60]!r} is not the value of the readers "
                       f"({str(x['normalised'])[:60]!r})")
        if la.get("label_object") not in remake(f, r.doc.text, x["char_start"], x["char_end"], x["tier"])["values"]:
            bad.append(f"{name}: the value {str(la.get('label_object'))[:60]!r} does not follow from the wording that "
                       f"the readers selected")

    def tier_p(f: str, tier: str, la: dict | None):
        if calib is not None:
            return tier_probability(f, tier, calib)
        return node_tier_probability(cals.get((la or {}).get("calibration")))

    states = {}
    information = []
    for f in FIELDS:
        rec = rd["fields"][f]
        gap = gaps.get(f)
        gap_pair = (gap.get("slot_state"), gap.get("gap_reason")) if gap else None
        if not rec["cascade"]["searched"]:
            states[f] = "not searched"
            rules = ", ".join(rec["cascade"]["rules"])
            if f in pdf:
                bad.append(f"{f}: the record has a value, but the cascade does not search this value in a document of "
                           f"the kind {kind} (cascade rules {rules})")
            if gap_pair != NOT_IN_TYPE:
                bad.append(f"{f}: no gap record with the state not_in_this_document_type for a value that is not "
                           f"searched in a document of the kind {kind}")
            elif not str(gap.get("label_note") or "").startswith(NOT_SEARCHED):
                bad.append(f"{f}: the gap record does not start with the text {NOT_SEARCHED!r}")
            others = [x for x in rec.get("others") or [] if x.get("tier") in vcr.ADDRESSEE_TIERS]
            if f in cand:
                if not others:
                    bad.append(f"{f}: a candidate label, but the readers keep no candidate for a value that is not searched")
                else:
                    same_place(f, cand[f], others[0], "addressee candidate")
            elif others and lang is not None and vn.body_word(one_line(others[0]["value"])) is not None \
                    and (calib is None or (calib.get("lookup") or {}).get(CALIBRATION_FIELD.get(f, f), {}).get("entry")
                         != "left_out_not_measured"):
                bad.append(f"{f}: the readers keep the addressed body {others[0]['value'][:60]!r} as a candidate, and "
                           f"the record has no candidate label")
            continue
        if not rec["found"]:
            states[f] = f"not found ({rec['reason']})"
            if f in pdf or f in cand:
                bad.append(f"{f}: the record has a value label, but the readers find no value in this PDF (reason "
                           f"{rec['reason']})")
            if rec["reason"] in NOT_READ_OF_REASON:
                if not_read.get(f) != NOT_READ_OF_REASON[rec["reason"]]:
                    bad.append(f"{f}: the readers give the reason {rec['reason']}; the record does not list the field "
                               f"as not read with the reason {NOT_READ_OF_REASON[rec['reason']]}")
            elif rec["reason"] == SCOPE_READER_REASON:
                # finding S3-01: the cascade searches the value; the reason of its rule is a result of the search
                sl = slot_of.get(f) or {}
                if gap_pair != SCOPE_GAP or (sl.get("state"), sl.get("reason")) != SCOPE_SLOT:
                    bad.append(f"{f}: the cascade searches the value and its rule gives the reason {rec['reason']}; the "
                               f"record must have the gap record {SCOPE_GAP} and the slot entry {SCOPE_SLOT}, not "
                               f"{gap_pair} and {(sl.get('state'), sl.get('reason'))}")
                elif not str(gap.get("label_note") or "").startswith(SCOPE_MARK):
                    bad.append(f"{f}: the note of the gap record does not start with the text {SCOPE_MARK!r}")
            elif gap_pair != GAP_OF_REASON[rec["reason"]]:
                bad.append(f"{f}: the readers give the reason {rec['reason']}; the gap record of the field is "
                           f"{gap_pair}, not {GAP_OF_REASON[rec['reason']]}")
            if gap and str(gap.get("label_note") or "").startswith(NOT_SEARCHED):
                bad.append(f"{f}: the note of the gap record starts with the text {NOT_SEARCHED!r}, but the cascade "
                           f"searches this value in a document of the kind {kind}")
            continue
        states[f] = f"found ({rec['tier']})"
        look = ((calib or {}).get("lookup") or {}).get(CALIBRATION_FIELD.get(f, f)) or {}
        wording_value = one_line(rec["value"]) if f in PRINTED_FIELDS else rec["normalised"]
        invalid = (f == "affair_type" and rec["normalised"] not in affair_types()) \
            or (f in PRINTED_FIELDS and lang is None) \
            or (f in ("submission_date", "response_date") and not RX_DAY.match(str(rec["normalised"]))) \
            or (f == "responder" and vn.body_word(wording_value) is None)
        if look.get("entry") == "left_out_not_measured":
            if f in pdf or f in cand or not_read.get(f) != "field_not_measured":
                bad.append(f"{f}: the calibration file leaves the field out; the record must list it as not read")
            continue
        if invalid:
            if f in pdf or f in cand or gap_pair != CANDIDATE_GAP:
                bad.append(f"{f}: the value of the readers does not have the form of its slot; the record must have a "
                           f"gap record {CANDIDATE_GAP} and no label")
            continue
        la = pdf.get(f) or cand.get(f)
        if la is None:
            bad.append(f"{f}: the readers find {str(rec['value'])[:60]!r} (tier {rec['tier']}), and the record has no "
                       f"label of the field")
            continue
        same_place(f, la, rec, "value")
        if f == "responder" and f in pdf and rec["tier"] in vcr.ADDRESSEE_TIERS:
            # finding V4-05 (information, no problem): possible only for a record with no known kind (rule V1)
            information.append(f"responder: the written value {str(rec['value'])[:60]!r} has the tier {rec['tier']}: it is "
                               "the body that the text addresses. The kind of the document is "
                               f"{'not known' if kind is None else kind}, so the reader keeps it as a value. It can be "
                               "the addressed body of a proposal and not a responding body")
        p = tier_p(f, rec["tier"], la)
        if p is not None:
            weak = p < FLOOR_P
            if weak and f in pdf:
                bad.append(f"{f}: the tier {rec['tier']} of the readers has the stored probability {p} (below "
                           f"{FLOOR_P}): the value must be a candidate, but it is written")
            if not weak and f in cand:
                bad.append(f"{f}: the tier {rec['tier']} of the readers has the stored probability {p} (not below "
                           f"{FLOOR_P}): the value must be written, but it is a candidate")
    # the text blocks that the cascade does not give to the kind (full record: the provenance file has them)
    cut = [x for x in mc.get("text_blocks_not_written") or [] if isinstance(x, dict)]
    for x in cut:
        slot = str(x.get("slot"))
        if slot not in cs["texts"] or cs["texts"][slot][0]:
            bad.append(f"the manifest lists a text block as not written for the slot {slot}, but the cascade gives "
                       f"this slot to the kind {kind}")
    if r.full:
        kept = [t for t in r.prov.get("text_block_records") or [] if t.get("mapping_status") == "profile_only"
                and str(t.get("not_mapped_reason") or "").startswith(NOT_SEARCHED)]
        if len(kept) != len(cut) or any(not t.get("text_content") for t in kept):
            bad.append(f"the manifest lists {len(cut)} text blocks that the cascade does not give to the kind; the "
                       f"provenance file has {len(kept)} such TextBlockRecords, each must hold its text")
    return result("C22", bad, kind=kind, kind_from=rd["kind_from"], kind_source=rd["kind_source"],
                  rule_file_at_hand=r.rule_file,
                  reading="combined reader on the heads output of the record (m12_apertus_values)"
                  if "apertus" in rd else "cascade reader of the rules",
                  affair_type_of_the_cascade=rd["affair_type_of_the_cascade"], readers=states,
                  information=information, export_record_used=False)


# ------------------------------------------------------------------ the head checks of one record
def head_checks(r: Record, calib: dict | None, export_record: dict | None, graphs: dict | None = None,
                calibration_info: dict | None = None) -> dict:
    """The checks C11 to C22. `graphs`: the part graphs of the record, if they exist. `calibration_info`: the
    facts of calibration_choice."""
    out = {}
    calls = (("C11", lambda: check_c11(r)), ("C12", lambda: check_c12(r)), ("C13", lambda: check_c13(r)),
             ("C14", lambda: check_c14(r, export_record)),
             ("C15", lambda: check_c15(r, (graphs or {}).get("ech-0295"))),
             ("C16", lambda: check_c16(r, calib, calibration_info)), ("C17", lambda: check_c17(r)),
             ("C18", lambda: check_c18(r, graphs)), ("C19", lambda: check_c19(r)), ("C20", lambda: check_c20(r)),
             ("C21", lambda: check_c21(r, calib)), ("C22", lambda: check_c22(r, calib)))
    for cid, fn in calls:
        try:
            out[CHECKS[cid][0]] = fn()
        except (KeyError, IndexError, TypeError, AttributeError, ValueError, casc.CascadeError) as e:
            # a record that does not have the form of record_form.md fails the check; it does not stop the run
            out[CHECKS[cid][0]] = result(cid, [f"the record does not have the form that the check reads: "
                                               f"{type(e).__name__}: {str(e)[:200]}"])
    return out


def c1_ech(r: Record, c17: dict, name: str) -> dict:
    """The C1 entry of the eCH file. With no recorded gap: I95 with no change. Else: the result of check C17."""
    if c17["i95_gaps"]:
        n = c17["i95_messages_with_the_gap_slots_not_required"]
        return {"file": name, "schema": rdf.rel(I95), "class": "Container", "valid": bool(c17["passed"]),
                "errors": n if n else (0 if c17["passed"] else len(c17["problems"])), "messages": c17["problems"][:10],
                "i95_slots_not_required": c17["i95_gaps"]}
    msgs = gp.linkml_messages(r.ech)
    return {"file": name, "schema": rdf.rel(I95), "class": "Container", "valid": not msgs, "errors": len(msgs),
            "messages": [m[:400] for m in msgs[:10]]}


def summary(res: dict, t0: float) -> dict:
    keys = [k for k in res if re.match(r"C\d+_", k) and k != "C10_shacl" and "passed" in res[k]]
    res["passed"] = bool(keys) and all(res[k]["passed"] for k in keys)
    res["checks_failed"] = [k for k in keys if not res[k]["passed"]]
    res["checks_not_run"] = [k for k in res if re.match(r"C\d+_", k) and res[k].get("status") == "not_run"]
    res["shacl_information_only"] = True
    res["seconds"] = round(time.perf_counter() - t0, 3)
    return res


def head(doc_id, mode: str, r: Record | None = None) -> dict:
    gaps = (r.man.get("i95_gaps") if r else None) or []
    slots = [g.get("slot") for g in gaps if isinstance(g, dict)]
    return {"doc_id": doc_id, "mode": mode, "script": {"path": SCRIPT, "version": VERSION, "sha256": sha256(Path(__file__))},
            "tools": rdf.linkml_versions(), "record_form": "daten/gj_values/record_form.md",
            "conformance": gp.conformance(tuple(s for s in slots if s in gp.GAP_SLOTS)), "i95_gaps": gaps,
            "check_ids": {cid: {"key": k, "record_form_id": v, "description": text} for cid, (k, v, text) in CHECKS.items()}}


# ------------------------------------------------------------------ a head part (the examples)
def validate_parts(ech: dict, labels: dict, prov: dict, man: dict, block_path: Path, *, calibration: dict | None = None,
                   export_record: dict | None = None, rule_path: Path | None = None,
                   kind: str | None = "from_rule_chain", calibration_info: dict | None = None) -> dict:
    """The checks that apply to a head part: C1 (the parts), C6 and C11 to C22. The 4 dicts can be copies with a
    defect (src/m11_validate_test.py). `rule_path`: the rule file of the block file (check C22 and the kind).
    `calibration`: the calibration file as a dict, given by the caller (None: no file at hand, fewer comparisons).
    `calibration_info`: the facts of calibration_choice, if the caller made the choice with that function."""
    t0 = time.perf_counter()
    block_file = read_json(block_path)
    r = Record(ech, labels, prov, man, vb.load_from_block_file(block_path, rule_path), block_file, full=False,
               rule_file=rule_path is not None, kind_arg=kind)
    res = head(man.get("doc_id"), "head_part", r)
    accept_urn()
    graphs, build_errors = {}, []
    slots, _ = recorded_gap_slots(man)
    for name, schema, cls, data, gaps in (("ech-0295", WRAPPER, "Container", ech, tuple(slots)),
                                          ("labels", LABEL_SCHEMA, "LabelRecord", labels, ())):
        try:
            graphs[name] = rdf.to_graph(schema, cls, data, gaps)
        except Exception as e:  # noqa: BLE001  (each error of the LinkML loader is a finding of check C1)
            build_errors.append(f"the graph {name} does not build: {type(e).__name__}: {str(e)[:200]}")
    hc = head_checks(r, calibration, export_record, graphs, calibration_info)
    res["calibration_file"] = hc[CHECKS["C16"][0]].get("calibration_file")
    c1 = [c1_ech(r, hc[CHECKS["C17"][0]], "eCH-0295 part") if "i95_gaps" in hc[CHECKS["C17"][0]] else
          {"file": "eCH-0295 part", "valid": False, "errors": 1, "messages": hc[CHECKS["C17"][0]]["problems"][:3]},
          schema_check(LABEL_SCHEMA, "LabelRecord", labels, "label part")]
    msgs = [m for v in prov.get("value_records") or [] for m in schema_messages(PROFILE, "ValueRecord", v)]
    msgs += [m for v in prov.get("not_mapped_records") or [] for m in schema_messages(PROFILE, "NotMappedRecord", v)]
    c1.append({"file": "provenance part (value records and not-mapped records)", "schema": rdf.rel(PROFILE),
               "class": "ValueRecord, NotMappedRecord", "valid": not msgs, "errors": len(msgs),
               "messages": [m[:400] for m in msgs[:10]]})
    res["C1_linkml"] = {"passed": all(x["valid"] for x in c1) and not build_errors, "description": CHECKS["C1"][2],
                        "results": c1, "problems": build_errors}
    for cid in ("C2", "C3", "C4", "C5"):
        res[CHECKS[cid][0]] = not_run(cid, "a head part has no RDF files and no full provenance file")
    import rdflib  # noqa: PLC0415
    no_scheme = sorted({str(x) for g in graphs.values() for t in g for x in t
                        if isinstance(x, rdflib.URIRef) and not mv.RX_SCHEME.match(str(x))})
    res["C6_iri_scheme"] = {"passed": not no_scheme, "description": CHECKS["C6"][2], "iris_without_scheme": no_scheme[:20],
                            "graphs": sorted(graphs)}
    for cid in ("C7", "C9", "C10"):
        res[CHECKS[cid][0]] = not_run(cid, "a head part has no block labels, no TextBlockRecords and no atom graph")
    res |= hc
    return summary(res, t0)


def example_block_path(prefix: Path, man: dict, root: Path) -> Path:
    p = Path(str(prefix) + ".blocks.json")
    if p.is_file():
        return p
    d = str(man.get("doc_id"))
    if not d.isdigit():
        raise SystemExit(f"{prefix}: no file {p.name}, and the manifest part names no document number")
    guard(d, root)
    return Path(root) / "daten/gj/docs" / f"{d}.json"


def example_rule_path(prefix: Path, man: dict, root: Path) -> Path | None:
    """The rule file of a head part: <name>.rules.json, or the rule file of the development document."""
    p = Path(str(prefix) + ".rules.json")
    if p.is_file():
        return p
    d = str(man.get("doc_id"))
    p = Path(root) / RULES_REL / f"{d}.json"
    return p if d.isdigit() and p.is_file() else None


def load_example(prefix: Path, root: Path | None = None) -> tuple[dict, dict, dict, dict, Path]:
    prefix = Path(prefix)
    root = Path(root) if root else ROOT
    m = re.match(r"known_(\d+)\Z", prefix.name)
    if m:
        guard(m.group(1), root)                 # before a file of the example is read
    man = read_json(Path(str(prefix) + ".manifest_part.json"))
    if str(man.get("doc_id")).isdigit():
        guard(man["doc_id"], root)
    block_path = example_block_path(prefix, man, root)
    return (rdf.load_yaml(Path(str(prefix) + ".ech.yaml")), rdf.load_yaml(Path(str(prefix) + ".labels.yaml")),
            rdf.load_yaml(Path(str(prefix) + ".provenance_part.yaml")), man, block_path)


def validate_example(prefix: Path, *, root: Path | None = None, calibration: Path | None = None,
                     export_record: dict | None = None) -> dict:
    """A head part. The calibration file: the file of the product, or the file that the caller gives (finding
    S3-02, function calibration_choice)."""
    ech, labels, prov, man, block_path = load_example(prefix, root)
    calib, info = calibration_choice(man, Path(root) if root else ROOT, calibration)
    return validate_parts(ech, labels, prov, man, block_path, calibration=calib, export_record=export_record,
                          rule_path=example_rule_path(Path(prefix), man, Path(root) if root else ROOT),
                          calibration_info=info)


# ------------------------------------------------------------------ a full record of the writer
def find_prefix(folder: Path) -> str:
    names = sorted(p.name[:-len(".ech.yaml")] for p in folder.glob("*.ech.yaml"))
    if len(names) != 1:
        raise SystemExit(f"{folder}: {len(names)} files *.ech.yaml (1 is necessary)")
    return names[0]


def input_path(man: dict, key: str, root: Path, folder: Path) -> Path | None:
    info = (man.get("inputs") or {}).get(key)
    if not info or not info.get("path"):
        return None
    p = Path(info["path"])
    for c in ([p] if p.is_absolute() else [Path(root) / p, ROOT / p, folder / p]):
        if c.is_file():
            if info.get("sha256") and sha256(c) != info["sha256"]:
                raise SystemExit(f"{c}: the file differs from the file that the writer read (manifest key inputs.{key})")
            return c
    return None


@contextlib.contextmanager
def atoms_below(root: Path):
    """m10_validate.e19_checks reads the atom file with m10_rdf.explicit_atoms and with the frozen wording
    functions (m03_iso_paths, m03_gold_record). For the time of the call, these modules read below the root of
    this run (the method of m11_writer.data_root). No file changes."""
    root = Path(root).resolve()
    old = (rdf.ATOMS_DIR, ip.DEV, ip.TEST, gr.ROOT, gr.GOLD, gr._VOCAB)
    rdf.ATOMS_DIR = root / "daten/iso/atome"
    if root != ROOT:
        ip.DEV, ip.TEST = root / "daten/iso", root / "daten/gold/test"
        gr.ROOT, gr.GOLD, gr._VOCAB = root, root / "daten/gold", None
    try:
        yield
    finally:
        rdf.ATOMS_DIR, ip.DEV, ip.TEST, gr.ROOT, gr.GOLD, gr._VOCAB = old


def shacl_information(graphs: dict) -> dict:
    """C10 with the shapes of the label schema 0.2.0 (m10_validate.shacl_shapes and shacl_results by import)."""
    try:
        import pyshacl
    except ImportError:
        return {"status": "skipped", "reason": "pyshacl is not importable (the command has no --with pyshacl)"}
    schemas = {"ech-0295": WRAPPER, "provenance": PROFILE, "labels": LABEL_SCHEMA, "atoms": LABEL_SCHEMA}
    out = {}
    for name, schema in schemas.items():
        shapes, facts = mv.shacl_shapes(schema)
        conforms, rg, _ = pyshacl.validate(graphs[name], shacl_graph=shapes, inference="none", abort_on_first=False,
                                           allow_infos=False, allow_warnings=False, advanced=False)
        groups = mv.shacl_results(rg, shapes, graphs[name])
        out[name] = {"conforms": bool(conforms), "shapes": facts["schema"], "triples": len(graphs[name]),
                     "results": sum(g["count"] for g in groups), "groups": groups[:mv.SHACL_GROUPS]}
    return {"status": "run", "passed": all(x["conforms"] for x in out.values()), "graphs": out}


VALUES_NS = "https://schema.parlpdfech.example/values/"


def values_ttl_problems(g, labels: dict, man: dict, ech=None) -> list[str]:
    """Part of C3 for a record of m11-writer-5 or later: the file <prefix>.values.ttl holds one node for each value
    label of the eCH-0295 part (kind pdf_value with a path of the record), and each node gives the facts of its
    label: the resource (label_subject), the property (label_predicate), the entity (about_entity, only if it is
    another resource), the value, the probability, the value status, the tier, the page and the span. The file has
    no other node of the class ValueReading. If `ech` (the parsed eCH-0295 graph) is given, the pair resource and
    property of each node must be the subject and the predicate of a statement of that graph (finding F1 of
    14.10.2026: form 1 of m11-writer-5 named the actor as the resource of a sponsor and of a responder)."""
    import rdflib
    from decimal import Decimal
    from rdflib.namespace import RDF
    pv = rdflib.Namespace(VALUES_NS)
    problems = []
    written = [x for x in labels.get("label_assertions") or []
               if x.get("label_kind") == "pdf_value" and x.get("instance_path")]
    nodes = set(g.subjects(RDF.type, pv.ValueReading))
    if len(nodes) != len(written):
        problems.append(f"{len(nodes)} nodes of the class ValueReading, {len(written)} value labels of the record")
    for x in written:
        field = str(x["global_uri"]).rsplit("/", 1)[-1].removeprefix("pdf-")
        node = rdflib.URIRef(f"{man['record_iri']}/value/{field}")

        def one(pred):
            vals = list(g.objects(node, pred))
            return vals[0] if len(vals) == 1 else None

        entity = x.get("about_entity") if x.get("about_entity") != x["label_subject"] else None
        want = {"label": rdflib.URIRef(x["global_uri"]), "property": rdflib.URIRef(x["label_predicate"]),
                "resource": rdflib.URIRef(x["label_subject"]),
                "entity": rdflib.URIRef(entity) if entity else None}
        for key, value in want.items():
            if one(pv[key]) != value or (value is None and any(g.objects(node, pv[key]))):
                problems.append(f"{field}: {key} differs from the label")
        if ech is not None and not any(ech.triples((want["resource"], want["property"], None))):
            problems.append(f"{field}: the resource and the property are not a statement of the eCH-0295 graph")
        for key, value in (("value", x["label_object"]), ("status", x["value_status"]), ("tier", x["tier"])):
            if one(pv[key]) is None or str(one(pv[key])) != str(value):
                problems.append(f"{field}: {key} differs from the label")
        p = one(pv.probability)
        if p is None or Decimal(str(p)) != Decimal(str(x["label_probability"])):
            problems.append(f"{field}: probability differs from the label")
        for key, pred in (("page", "page"), ("span_start", "charStart"), ("span_end", "charEnd")):
            v = one(pv[pred])
            if x.get(key) is not None and (v is None or int(v) != int(x[key])):
                problems.append(f"{field}: {key} differs from the label")
    return problems


# V5: the predicates of a node of the class pvl:Suggestion (m12_writer, edit W6): (key of the item, local name, kind)
SUGGESTION_PREDICATES = (("field", "field", "text"), ("status", "status", "text"), ("value", "value", "text"),
                         ("printed", "printed", "text"), ("tier", "tier", "text"), ("band", "band", "text"),
                         ("called_because", "calledBecause", "text"), ("block", "block", "text"),
                         ("probability", "probability", "decimal"), ("head_probability", "headProbability", "decimal"),
                         ("k", "tierEqual", "int"), ("n", "tierUnits", "int"), ("page", "page", "int"),
                         ("char_start", "charStart", "int"), ("char_end", "charEnd", "int"),
                         ("near", "near", "bool"), ("in_record", "inRecord", "bool"))
NOT_ON_SUGGESTION = ("resource", "property", "entity", "label", "calibration", "reading")


def _same_item(a: dict, b: dict) -> bool:
    """Two suggestion items with the same keys and values (numbers after round(x, 4))."""
    def norm(x: dict) -> dict:
        return {k: (round(float(v), 4) if isinstance(v, float) else v) for k, v in x.items()}
    return norm(a) == norm(b)


def suggestion_problems(g, man: dict, labels: dict, reading: dict | None, doc, entry: dict | None) -> list[str] | None:
    """V5, part of C3: the Apertus suggestions below the entry limit of the values file (rules S1 to S7). None (not
    applied): the file has no node of the class pvl:Suggestion, the manifest has no item and the reading gives no
    suggestion. `reading`: the reading of V3 (None for a record with no Apertus step: then no node is permitted).
      S1  the fields of the nodes are the fields of the reading; one node for each field, the node
          <record>/suggestion/<field>; each node is the object of <record> pvl:suggestion and of no pvl:reading
      S2  the items of the manifest key apertus_suggestions are the items of the reading; its key entry_sha256 is
          the SHA-256 of the manifest input apertus_entry
      S3  each node has exactly one value of each predicate of m12_writer (W6), equal to the item of the reading
          (pvl:lastPage only if the last page is another page)
      S4  pvl:printed is the document text at the span; pvl:value is m12_writer.record_value of that wording
      S5  the tier is the tier of the entry file for the field and the band (m12_apertus_values.entry_tier), the tier
          did not enter, pvl:tierEqual and pvl:tierUnits are its units, and pvl:probability is
          m12_apertus_values.suggestion_probability of these units
      S6  no pvl:resource, pvl:property, pvl:entity, pvl:label, pvl:calibration on the node; pvl:status is
          below_entry_limit and pvl:inRecord is false
      S7  the field has no written value label and no node of the class pvl:ValueReading"""
    import rdflib
    from decimal import Decimal
    from rdflib.namespace import RDF
    pv = rdflib.Namespace(VALUES_NS)
    nodes = set(g.subjects(RDF.type, pv.Suggestion))
    key = man.get("apertus_suggestions")
    items_man = list((key or {}).get("items") or [])
    items_read = list(((reading or {}).get("apertus") or {}).get("suggestions") or [])
    if not nodes and not items_man and not items_read:
        return None
    problems = []
    record = rdflib.URIRef(man["record_iri"])
    want = {x["field"]: x for x in items_read}
    # S1
    if reading is None and nodes:
        problems.append("the values file has suggestion nodes, but the record has no reading of the Apertus heads")
    by_field = {}
    for nd in nodes:
        fs = [str(o) for o in g.objects(nd, pv.field)]
        if len(fs) != 1:
            problems.append(f"the suggestion node {nd} has {len(fs)} values of pvl:field")
            continue
        if fs[0] in by_field:
            problems.append(f"{fs[0]}: two suggestion nodes")
        by_field[fs[0]] = nd
    if sorted(by_field) != sorted(want):
        problems.append(f"the suggestion nodes name the fields {sorted(by_field)}; the combined reader gives "
                        f"{sorted(want)}")
    linked = set(g.objects(record, pv.suggestion))
    if linked != nodes:
        problems.append("the objects of pvl:suggestion of the record are not the suggestion nodes")
    for f, nd in sorted(by_field.items()):
        if nd != rdflib.URIRef(f"{man['record_iri']}/suggestion/{f}"):
            problems.append(f"{f}: the suggestion node is not <record>/suggestion/{f}")
        if set(g.subjects(pv.suggestion, nd)) != {record}:
            problems.append(f"{f}: the suggestion node is not linked from the record only")
        if any(g.subjects(pv.reading, nd)) or (nd, RDF.type, pv.ValueReading) in g:
            problems.append(f"{f}: the suggestion node is also a reading")
    # S2
    if len(items_man) != len(items_read) or not all(_same_item(a, b) for a, b in zip(items_man, items_read)):
        problems.append("the items of the manifest key apertus_suggestions are not the suggestions of the combined "
                        "reader")
    if key is not None:
        entry_sha = ((man.get("inputs") or {}).get("apertus_entry") or {}).get("sha256")
        if key.get("entry_sha256") != entry_sha:
            problems.append("the key entry_sha256 of apertus_suggestions is not the SHA-256 of the input apertus_entry")
        if key.get("form") != av.SUGGESTION_FORM or key.get("status") != av.SUGGESTION_STATUS:
            problems.append("the manifest key apertus_suggestions has another form or status")
    elif items_read:
        problems.append("the manifest has no key apertus_suggestions, but the combined reader gives suggestions")
    written = {str(x["global_uri"]).rsplit("/", 1)[-1].removeprefix("pdf-")
               for x in labels.get("label_assertions") or []
               if x.get("label_kind") == "pdf_value" and x.get("instance_path")}
    import m12_writer as w12  # noqa: PLC0415  (record_value: the rule of the value of the eCH-0295 part)
    for f, nd in sorted(by_field.items()):
        def vals(name, nd=nd):
            return list(g.objects(nd, pv[name]))
        # S6
        for name in NOT_ON_SUGGESTION:
            if vals(name):
                problems.append(f"{f}: the suggestion node has pvl:{name}")
        if [str(o) for o in vals("status")] != [av.SUGGESTION_STATUS] or \
                [o.toPython() for o in vals("inRecord")] != [False]:
            problems.append(f"{f}: pvl:status or pvl:inRecord of the suggestion node is wrong")
        # S7
        if f in written or (rdflib.URIRef(f"{man['record_iri']}/value/{f}"), RDF.type, pv.ValueReading) in g:
            problems.append(f"{f}: a suggestion below the entry limit for a field with a written value")
        x = want.get(f)
        if x is None:
            continue                                  # S1 gave the problem
        # S3
        for k, name, kind in SUGGESTION_PREDICATES:
            got = vals(name)
            if len(got) != 1:
                problems.append(f"{f}: the suggestion node has {len(got)} values of pvl:{name}")
                continue
            o = got[0]
            ok = (str(o) == str(x[k]) if kind == "text" else
                  Decimal(str(o)) == Decimal(str(x[k])) if kind == "decimal" else
                  int(o) == int(x[k]) if kind == "int" else o.toPython() is bool(x[k]))
            if not ok:
                problems.append(f"{f}: pvl:{name} of the suggestion node differs from the combined reader")
        last = vals("lastPage")
        if (x.get("last_page") == x.get("page") and last) or (x.get("last_page") != x.get("page") and
                                                             [int(o) for o in last] != [int(x["last_page"])]):
            problems.append(f"{f}: pvl:lastPage of the suggestion node differs from the combined reader")
        # S4
        s, e = x.get("char_start"), x.get("char_end")
        printed = doc.text[s:e] if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(doc.text) else None
        if printed is None or [str(o) for o in vals("printed")] != [printed]:
            problems.append(f"{f}: pvl:printed is not the document text at the span")
        elif [str(o) for o in vals("value")] != [w12.record_value(f, printed, x.get("normalised"))]:
            problems.append(f"{f}: pvl:value is not the value of the wording at the span (m12_writer.record_value)")
        # S5
        et = av.entry_tier(entry or {}, f, x.get("band"))
        if et is None or et[0] != x.get("tier") or et[1].get("entered") is not False:
            problems.append(f"{f}: the tier {x.get('tier')!r} is not a tier of the entry file that did not enter")
        else:
            equal, units = int(et[1]["equal"]), int(et[1]["equal"]) + int(et[1]["different"])
            if [int(o) for o in vals("tierEqual")] != [equal] or [int(o) for o in vals("tierUnits")] != [units]:
                problems.append(f"{f}: pvl:tierEqual or pvl:tierUnits are not the units of the tier in the entry file")
            p = vals("probability")
            if len(p) != 1 or Decimal(str(p[0])) != Decimal(str(av.suggestion_probability(equal, units))):
                problems.append(f"{f}: pvl:probability is not (equal + 0.5) / (units + 1) of the tier")
    return problems


def product_rules_file(root: Path) -> Path | None:
    """V3: the product file of the rules (weak tiers of the combined reader) below the code root, else below the
    root of the caller. Its SHA-256 must be the pinned value of m12_apertus_values (the file of the fixed run)."""
    for b in dict.fromkeys((ROOT, Path(root).resolve())):
        p = b / PRODUCT_RULES_REL
        if p.is_file():
            return p
    return None


def apertus_reading(man: dict, root: Path, folder: Path, doc, kind) -> dict | None:
    """V3: the reading of a record of the Apertus mode (manifest input apertus_heads), else None (the reading of
    the rules, Record.reading). The heads output and the entry file are inputs of the manifest (SHA-256 checked by
    input_path). A fact that does not agree is a problem of check C22 (key apertus_problems of the reading)."""
    inputs = man.get("inputs") or {}
    if "apertus_heads" not in inputs:
        return None
    if kind != "from_rule_chain":
        raise SystemExit("a record of the Apertus mode is checked with the kind of the rule chain only")
    problems = []
    hp = input_path(man, "apertus_heads", root, folder)
    ep = input_path(man, "apertus_entry", root, folder)
    pp = product_rules_file(root)
    if hp is None:
        raise SystemExit("the heads output of the manifest key inputs.apertus_heads was not found")
    if ep is None:
        raise SystemExit("the entry file of the manifest key inputs.apertus_entry was not found")
    if pp is None:
        raise SystemExit(f"the product file of the rules {PRODUCT_RULES_REL} is not below the root or the code root")
    if sha256(pp) != av.PRODUCT_SHA256:
        problems.append(f"the product file of the rules {PRODUCT_RULES_REL} has another SHA-256 than the file of the "
                        "fixed run: the weak tiers of the combined reader can differ")
    ho = read_json(hp)
    facts = man.get("apertus_values") or {}
    if (ho.get("model") or "") != av.FINAL_NAME:
        problems.append(f"the heads output is of the model {ho.get('model')!r}, not of the final head")
    res = av.reading_for_validator(doc, ho, read_json(ep), cmb.weak_tiers(pp), facts.get("backend"))
    got = sorted(res["apertus"]["values"])
    if sorted(facts.get("values_from_apertus") or []) != got:
        problems.append(f"the manifest key apertus_values.values_from_apertus gives "
                        f"{sorted(facts.get('values_from_apertus') or [])}; the combined reader gives {got}")
    return res | {"apertus_problems": problems}


def validate_record(out_dir, *, root=None, calibration=None, export_record=None,
                    kind: str | None = "from_rule_chain") -> dict:
    """The checks C1 to C22 of one record folder of src/m11_writer.py. Writes <out_dir>/validation.json and the
    key validation of manifest.json. `calibration`: path of a value calibration file that the caller gives. Default:
    the file of the product (CALIBRATION_REL below the root or the code root; the path of the manifest is not
    used, finding S3-02). The result key calibration_file says which file was used. `export_record`: the export record as a dict or a path
    (default: the file of the manifest key inputs.export, if the manifest says has_export). `kind`: the kind of the
    document, if the caller knows it from another source than the rule chain (default: from the rule chain)."""
    import rdflib
    t0 = time.perf_counter()
    folder = Path(out_dir).resolve()
    root = Path(root).resolve() if root else ROOT
    d = find_prefix(folder)
    if d.isdigit():
        guard(d, root)                           # before a file of the record is read
    paths = rdf.record_paths(folder, d)
    man = read_json(paths["manifest"])
    ech, prov, labels = (rdf.load_yaml(paths[k]) for k in ("ech_yaml", "provenance_yaml", "labels_yaml"))
    block_path = input_path(man, "docs", root, folder)
    atoms_path = input_path(man, "atoms", root, folder)
    if block_path is None:
        raise SystemExit(f"{d}: the block file of the manifest key inputs.docs was not found")
    block_file = read_json(block_path)
    rule_path = input_path(man, "rules", root, folder)
    vdoc = vb.load_from_block_file(block_path, rule_path)
    reading = apertus_reading(man, root, folder, vdoc, kind)            # V3: None for a record with no Apertus step
    r = Record(ech, labels, prov, man, vdoc, block_file, full=True,
               atoms=read_json(atoms_path)["atome"] if atoms_path else None, rule_file=rule_path is not None,
               kind_arg=kind, _reading=reading)
    calib, calibration_info = calibration_choice(man, root, calibration)
    if export_record is None and man.get("has_export"):
        export_record = input_path(man, "export", root, folder)
    if isinstance(export_record, (str, Path)):
        export_record = read_json(export_record)
    res = head(man.get("doc_id"), "full_record", r)
    res["inputs"] = {"block_file": str(block_path), "rule_file": str(rule_path) if rule_path else None,
                     "atom_file": str(atoms_path) if atoms_path else None,
                     "calibration_file": calibration_info["path"], "calibration_source": calibration_info["source"],
                     "export_record_at_hand": export_record is not None}
    res["calibration_file"] = {k: v for k, v in calibration_info.items() if k != "problems"}
    accept_urn()
    slots, _ = recorded_gap_slots(man)
    # the part graphs (the steps of m10_rdf.part_graphs with the label schema 0.2.0)
    parts, layout, part_errors = {}, None, []
    try:
        if atoms_path is None:
            raise FileNotFoundError("the atom file of the manifest key inputs.atoms was not found")
        layout = rdf.layout_record(block_file, read_json(atoms_path), man["record_iri"], labels["source_document"])
        parts = {"ech-0295": rdf.to_graph(WRAPPER, "Container", ech, tuple(slots)),
                 "provenance": rdf.to_graph(PROFILE, "ExtractionRecord", prov),
                 "atoms": rdf.to_graph(LABEL_SCHEMA, "PdfLayout", layout),
                 "labels": rdf.to_graph(LABEL_SCHEMA, "LabelRecord", labels)}
    except Exception as e:  # noqa: BLE001  (each error of the LinkML loader is a finding)
        part_errors.append(f"the part graphs do not build: {type(e).__name__}: {str(e)[:300]}")
    hc = head_checks(r, calib, export_record, parts or None, calibration_info)
    c17 = hc[CHECKS["C17"][0]]
    # C1
    c1 = [c1_ech(r, c17, paths["ech_yaml"].name) if "i95_gaps" in c17 else
          {"file": paths["ech_yaml"].name, "valid": False, "errors": 1, "messages": c17["problems"][:3]},
          mv.linkml_check(PROFILE, "ExtractionRecord", prov, paths["provenance_yaml"].name),
          schema_check(LABEL_SCHEMA, "LabelRecord", labels, paths["labels_yaml"].name)]
    if layout is not None:
        c1.append(schema_check(LABEL_SCHEMA, "PdfLayout", layout, "atom layout (in memory)"))
    res["C1_linkml"] = {"passed": all(x["valid"] for x in c1) and layout is not None, "description": CHECKS["C1"][2],
                        "results": c1, "problems": part_errors}
    # C2
    parsed, c2 = {}, []
    rdf_files = [("gesamt_trig", "trig"), ("gesamt_rdfxml", "xml"), ("ech_ttl", "turtle"), ("ech_rdfxml", "xml")]
    if "values_ttl" in (man.get("outputs") or {}):          # m11-writer-5 or later: the file of the values
        paths = dict(paths, values_ttl=folder / f"{d}.values.ttl")
        rdf_files.append(("values_ttl", "turtle"))
    for key, fmt in rdf_files:
        try:
            parsed[key] = (rdflib.Dataset() if fmt == "trig" else rdflib.Graph()).parse(paths[key], format=fmt)
            c2.append({"file": paths[key].name, "parsed": True, "triples": len(parsed[key])})
        except Exception as e:  # noqa: BLE001  (each parse error is a finding)
            c2.append({"file": paths[key].name, "parsed": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
    res["C2_parse"] = {"passed": all(x["parsed"] for x in c2), "description": CHECKS["C2"][2], "results": c2}
    if res["C2_parse"]["passed"] and parts:
        record = man["record_iri"]
        named = {str(g.identifier): g for g in parsed["gesamt_trig"].graphs() if len(g)}
        trig = {name: named.get(f"{record}/{name}") for name in rdf.GRAPHS}
        union = rdflib.Graph()
        for g in named.values():
            for t in g:
                union.add(t)
        # C3
        c3 = {"union_equals_gesamt_rdfxml": mv.same_graph(union, parsed["gesamt_rdfxml"]),
              "ech_ttl_equals_ech_rdfxml": mv.same_graph(parsed["ech_ttl"], parsed["ech_rdfxml"]),
              "ech_ttl_equals_trig_graph": trig["ech-0295"] is not None and mv.same_graph(parsed["ech_ttl"], trig["ech-0295"])}
        values_problems = sugg_problems = None
        if "values_ttl" in parsed:
            values_problems = values_ttl_problems(parsed["values_ttl"], labels, man, ech=parsed.get("ech_ttl"))
            c3["values_ttl_equals_label_file"] = not values_problems
            # V5: the suggestions below the entry limit (only if the record has one or the reading gives one)
            entry_p = input_path(man, "apertus_entry", root, folder) if reading is not None else None
            sugg_problems = suggestion_problems(parsed["values_ttl"], man, labels, reading, vdoc,
                                                read_json(entry_p) if entry_p else None)
            if sugg_problems is not None:
                c3["values_ttl_suggestions_from_the_heads"] = not sugg_problems
        res["C3_isomorphism"] = {"passed": all(c3.values()), "description": CHECKS["C3"][2], **c3}
        if values_problems:
            res["C3_isomorphism"]["problems"] = values_problems[:20]
        if sugg_problems:
            res["C3_isomorphism"]["suggestion_problems"] = sugg_problems[:20]
        # C4
        c4 = {name: trig[name] is not None and mv.same_graph(trig[name], parts[name]) for name in rdf.GRAPHS}
        extra = sorted(set(named) - {f"{record}/{n}" for n in rdf.GRAPHS})
        res["C4_parts"] = {"passed": all(c4.values()) and not extra, "description": CHECKS["C4"][2], "graphs": c4,
                           "other_graphs": extra, "triples": {n: len(parts[n]) for n in rdf.GRAPHS}}
        # C5
        c5 = {"ech_yaml": mv.leaf_coverage(ech, parts["ech-0295"], WRAPPER),
              "provenance_yaml": mv.leaf_coverage(prov, parts["provenance"], PROFILE),
              "labels_yaml": mv.leaf_coverage(labels, parts["labels"], LABEL_SCHEMA),
              "atom_layout": mv.leaf_coverage(layout, parts["atoms"], LABEL_SCHEMA)}
        res["C5_leaf_values"] = {"passed": not any(c5.values()), "description": CHECKS["C5"][2],
                                 "missing": {k: v[:20] for k, v in c5.items()}}
        # C6
        no_scheme = sorted({str(x) for g in parts.values() for t in g for x in t
                            if isinstance(x, rdflib.URIRef) and not mv.RX_SCHEME.match(str(x))})
        res["C6_iri_scheme"] = {"passed": not no_scheme, "description": CHECKS["C6"][2],
                                "iris_without_scheme": no_scheme[:20]}
        # C7, C8, C9: the frozen functions; an error of a frozen function is a finding of its check
        for cid, fn in (("C7", lambda: mv.label_checks(parts, block_file)),
                        ("C9", lambda: mv.e19_checks(d, ech, prov, labels, block_file))):
            try:
                with atoms_below(root):
                    res[CHECKS[cid][0]] = {"description": CHECKS[cid][2]} | fn()
            except (Exception, SystemExit) as e:  # noqa: BLE001
                res[CHECKS[cid][0]] = {"passed": False, "description": CHECKS[cid][2],
                                       "problems": [f"the frozen check stopped: {type(e).__name__}: {str(e)[:300]}"]}
        # C10 (information only)
        try:
            c10 = shacl_information(parts)
        except Exception as e:  # noqa: BLE001  (the key passed does not use C10)
            c10 = {"status": "error", "error_type": type(e).__name__, "reason": f"{type(e).__name__}: {str(e)[:200]}"}
        res["C10_shacl"] = {"description": CHECKS["C10"][2]} | c10 | {"information_only": True}
    else:
        why = "the RDF files do not parse" if not res["C2_parse"]["passed"] else "the part graphs do not build"
        for cid in ("C3", "C4", "C5", "C6", "C7", "C9"):
            res[CHECKS[cid][0]] = {"passed": False, "description": CHECKS[cid][2], "problems": [why]}
        res["C10_shacl"] = {"description": CHECKS["C10"][2], "status": "skipped", "reason": why, "information_only": True}
    res |= hc
    summary(res, t0)
    # output: validation.json and the key validation of the manifest (the form of m10_validate.finish)
    p = folder / "validation.json"
    rdf.write_json(p, res)
    keys = [k for k in res if re.match(r"C\d+_", k) and k != "C10_shacl"]
    shacl = res.get("C10_shacl") or {}
    man["validation"] = {"passed": res["passed"], "conformance": res["conformance"],
                         "checks": {k: res[k].get("passed") for k in keys},
                         "shacl": shacl.get("status"), "shacl_passed": shacl.get("passed"),
                         "shacl_information_only": True, "validator": {"path": SCRIPT, "version": VERSION},
                         "calibration_file": {k: calibration_info[k] for k in ("source", "is_product_file", "sha256")},
                         "file": rdf.rel(p), "sha256": sha256(p)}
    if isinstance(man.get("seconds"), dict):
        man["seconds"]["validate"] = res["seconds"]
    rdf.write_json(paths["manifest"], man)
    return res


# ------------------------------------------------------------------ command line
def show(res: dict) -> str:
    parts = []
    for k, v in res.items():
        if re.match(r"C\d+_", k):
            parts.append(f"{k.split('_')[0]} {v.get('passed', v.get('status'))}")
    return f"{res['doc_id']}: passed {res['passed']} ({', '.join(parts)}), conformance {res['conformance']}, {res['seconds']} s"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="record folder of src/m11_writer.py")
    ap.add_argument("--example", help="path prefix of a head part, for example "
                                      "daten/gj_values/record_examples/known_879163")
    ap.add_argument("--root", help="folder with daten/iso/atome and the block file (default: the project root)")
    ap.add_argument("--calibration", help="another value calibration file than the file of the product "
                                          f"({CALIBRATION_REL}); the result then says so")
    ap.add_argument("--export", help="export record of the document (JSON, form of m06_converter export)")
    ap.add_argument("--write", help="with --example: path of the result file (default: no file)")
    ap.add_argument("--kind", help="with --out: the kind of the document (default: from the rule chain of the rule file)")
    a = ap.parse_args()
    if bool(a.out) == bool(a.example):
        ap.error("give --out or --example")
    if a.out:
        res = validate_record(a.out, root=a.root, calibration=a.calibration, export_record=a.export,
                              kind=a.kind if a.kind else "from_rule_chain")
    else:
        res = validate_example(Path(a.example), root=a.root, calibration=Path(a.calibration) if a.calibration else None,
                               export_record=read_json(a.export) if a.export else None)
        if a.write:
            rdf.write_json(Path(a.write), res)
    print(show(res))
    cf = res.get("calibration_file") or {}
    if not cf.get("is_product_file"):
        print(f"  calibration file: {cf.get('source')}")
    for k in res["checks_failed"]:
        for p in res[k].get("problems") or res[k].get("results") or []:
            print(f"  {k}: {p if isinstance(p, str) else json.dumps(p, ensure_ascii=False)[:300]}")
    return 0 if res["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

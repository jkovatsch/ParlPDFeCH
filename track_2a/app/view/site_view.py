"""The view function of the package: one record folder of the converter -> the view `parlpdfech-site-view/3`.

Contract: CONTRACT.md chapter 4.5, chapter 6, chapter 16 (the values that are read from the PDF), chapter 17
(the value as the document prints it, the weak candidate, the remake check), chapter 18 (the cascade),
chapter 19 (rule V5, the reason reader_scope, the signs of a response) and chapter 25 (the Apertus suggestions
below the entry limit, key apertus_suggestions); schema: contract/view.schema.json.

    import site_view
    view = site_view.make_view(record_dir, inputs_dir, run_info)

Command line:

    python site_view.py --record DIR --inputs DIR [--run-info FILE] --out FILE

The function reads only the two folders. It writes no file. It uses the standard library and PyYAML.
It does not read the TriG file or an RDF/XML file: each value of the view is in another file.
The view holds codes and values. The texts of the notices are in the strings file of the UI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import yaml

try:  # the C loader is about 10 times faster; the result is equal
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

SCHEMA = "parlpdfech-site-view/3"
STATUS = "EXCEPTION, NOT RELEASED"
VERSION = "site-view-3"

RECORD_ID = re.compile(r"^(s-[0-9]+|u-[0-9a-f]{16})(-rules)?$")
RUN_INFO_VALUES = {"origin": ("stored", "new"), "mode": ("auto", "rules"), "apertus": ("none", "stored"),
                   "profile": ("slim", "full", "native")}
# optional key of run_info (stage P0b): the OCR engine of a new conversion. apple = Apple OCR ran for the
# pages that need it; none = no OCR engine ran.
OCR_VALUES = ("apple", "none")
# optional key of run_info: the record path of the worker (worker/values_record.py). pdf: the head values are
# read from the PDF. off: the switch PARLPDFECH_VALUES=off. held: worker/values_hold.json names the document
# (that list is empty).
VALUES_STATES = ("pdf", "off", "held")
VALUES_RECORD = "parlpdfech-pdf-values-record/1"     # manifest.json key schema of a record of src/m11_writer.py
# label id of a value: pdf-<field> (the value is in the eCH-0295 part) or candidate-<field> (NOT in the eCH-0295
# part). A candidate is a weak candidate (the value of a rule tier whose stored probability is below the floor) or
# the body that a proposal addresses (the cascade searches no response step in that kind of document).
FIELD_ID = re.compile(r"^(pdf|candidate)-([a-z_]+)$")
# values[].value_form: how the value of the record follows from the printed wording (labels file key
# normalisation_rule). printed: the wording on one line. list_value: the value of the eCH-0295 list for the
# printed type word. iso_day: the printed date as a calendar day (ISO 8601).
VALUE_FORMS = {"type_word_to_list_value": "list_value", "date_to_iso_day": "iso_day"}
WEAK_REASON = "weak_candidate_only"
WEAK_MARK = "not written: the tier is more often different from the reference than equal"
ADDRESSEE_MARK = "not written: the body that the text of the proposal addresses"
NOT_SEARCHED = "not searched in this kind of document"       # manifest: slots[].result and cascade.result_text
# the cascade of the record (manifest key cascade): the kind of the document selects which values are searched
KINDS = ("proposal", "response", "combined", "executive_proposal", "committee_report", "minutes", "other")
KIND_FROM = {"rule chain (S1 rule role and rule id)": "rule_chain", "argument": "argument", "none": "none",
             # rule V5 of the cascade reader: the rule chain made no decision (rule id D0); the type word and a
             # response cue of the PDF decide the kind
             "rule V5 (type word and response cue of the PDF; the rule chain made no decision)": "rule_v5"}
SCOPE_REASON = "reader_scope"      # manifest slot reason: searched, and the rule of the value does not read this document
PROPOSAL_KINDS = ("proposal", "executive_proposal")
ADDRESSEE_TIER = "rsp_addressee_cue"   # tier of the responder rule: the body that a proposal addresses (no response cue)
# rule V5 of the cascade reader since version 4: only this tier is a response cue (a heading or a phrase of the
# first lines says that the executive answers). Alone it gives the kind response.
RESPONSE_CUE_TIER = "rsp_response_cue"
# a response phrase in the running text: no cue and no sign for rule V5
WEAK_RESPONSE_TIER = "rsp_response_text"
CASCADE_FIELDS = ("affair_type", "title", "affair_number", "submission_date", "sponsor", "response_date", "responder")
FIELD_GROUP = {"affair_type": "affair", "title": "affair", "affair_number": "affair", "submission_date": "submission",
               "sponsor": "submission", "response_date": "response", "responder": "response"}
# head_values.cascade.entries[].state: the state of one of the 7 values in this record
ENTRY_STATES = ("read_from_pdf", "not_found_in_pdf", "reader_scope", "weak_candidate", "not_searched",
                "addressee_candidate")
COMPARISON_NOTE = re.compile(r"comparison value of the reader \(for the cross-check and the calibration only; not a value "
                             r"of the record\): .*", re.S)
SLOT_STATES = ("read_from_pdf", "not_found_in_pdf", "not_in_this_document_type", "register_only")
EXPORT_CHECKS = ("equal_to_export", "differs_from_export", "no_export_value", "not_compared")
# The Apertus suggestions below the entry limit (manifest key apertus_suggestions of src/m12_writer.py, edit W6 of
# 16.10.2026; CONTRACT.md chapter 25): an Apertus value of a Q2 tier that did not enter. It is NOT in the eCH-0295
# part; the values file (.values.ttl) has it as a pvl:Suggestion node. Its probability is the Jeffreys mean
# (k + 0.5) / (n + 1) of its tier on the development documents, with the limits 0.005 and 0.995 and 4 decimals.
SUGGESTION_STATUS = "below_entry_limit"
SUGGESTION_FORM = "parlpdfech-apertus-suggestions/1"
P_LOW, P_HIGH = 0.005, 0.995

INPUT_FILES = {"docling": "docling.json", "atoms": "atoms.json", "blocks": "blocks.json"}
DECISIONS_FILE = "decisions.json"
EXPORT_FILE = "export.json"

MEDIA = ((".trig", "application/trig"), (".ttl", "text/turtle"), (".rdf.xml", "application/rdf+xml"),
         (".yaml", "application/yaml"), (".json", "application/json"), (".pdf", "application/pdf"),
         (".png", "image/png"))
RX_PAGE_IMAGE = re.compile(r"page-([1-9][0-9]{0,2})\.png")
# provenance file, value_records[].derivation -> source group of view 1
ORIGIN = {"extracted_from_pdf": "pdf_copy", "copied_from_metadata": "export", "normalized_from_metadata": "export",
          "mapped_from_metadata": "export", "identifier_from_metadata": "export", "detected_by_rule": "code_rule",
          "identifier_minted": "identifier", "fixed_by_schema": "schema", "extracted_from_pdf_by_rule": "pdf_rule"}
TEXT_SOURCE = {"pdf": "pdf", "ocr": "ocr", "gemischt": "mixed", "mixed": "mixed"}
TARGET_TYPE = {"block_slot": "block", "author_switch": "block", "document_text_parts": "document",
               "executive_response": "document", "text_wording": "text_block"}
VALUE_KINDS = ("export_value", "constant_value", "pdf_value")
CHECKS = ("C1_linkml", "C2_parse", "C3_isomorphism", "C4_parts", "C5_leaf_values", "C6_iri_scheme", "C7_C8_labels",
          "C9_e19")
# the checks of src/m11_validate.py for a record whose head values are read from the PDF
VALUE_CHECKS = ("C11_wording_at_span", "C12_one_label_for_each_pdf_value", "C13_no_export_value_in_the_record",
                "C14_cross_check", "C15_slot_states", "C16_probability_and_calibration", "C17_recorded_gaps",
                "C18_minted_iris", "C19_value_forms", "C20_value_follows_from_wording", "C21_floor",
                "C22_values_from_the_readers")
# The note of a label (labels file key label_note) is an English working text of the converter. The view does
# not pass it on as it is. A known note becomes a code with its values (the page has a text for each code in
# its strings file). A note that no pattern knows goes to the key note after the filter _clean_note.
NOTE_PATTERNS = (
    (re.compile(r"switch between block (B\d+) and block (B\d+)"), "switch_between_blocks", ("before", "after")),
    (re.compile(r"derivation (\w+) \(ValueRecord of the provenance (?:side )?file\)"), "value_derivation",
     ("derivation",)),
    (re.compile(r"verbatim copy of the atoms of the author block \(check E19\); the (?:text and the )?text changes "
                r"are in the TextBlockRecord(?: of the provenance graph)?"), "wording_copy", ()),
    (re.compile(r"final check R2 \(frozen head H\): the document holds a response of the executive; it (agrees|does "
                r"not agree) with the block path"), "final_check", ("agrees",)),
    (re.compile(r"unsure: the final check R2 does not agree with the block path"), "unsure_final_check_differs", ()),
    # a weak candidate (values[].written false): the numbers are in values[].tier_probability and head_values.floor
    (re.compile(re.escape(WEAK_MARK) + r".*", re.S), "weak_candidate", ()),
    # the body that a proposal addresses (values[].candidate addressee): a candidate label, never a responder
    (re.compile(re.escape(ADDRESSEE_MARK) + r".*", re.S), "addressee_candidate", ()),
    # a value that is read from the PDF: the comparison value of the reader is in values[].comparison_value
    (COMPARISON_NOTE, "comparison_value", ()),
)
NOTE_CODES = tuple(code for _, code, _ in NOTE_PATTERNS)
# filter of a note that no pattern knows: paths, document numbers and working words of the project are removed
_NOTE_PATH = re.compile(r"(?:file://)?(?:[A-Za-z]:)?(?:[~.]{0,2}/)?(?:[\w.\-]+/)+[\w.\-]*|\b[\w\-]+\.(?:py|json|yaml|yml|csv|"
                        r"npz|pdf|md|txt|trig|ttl|xml)\b")
_NOTE_NUMBER = re.compile(r"(?<![\w.])\d{5,}(?![\w.])")
_NOTE_WORDS = re.compile(
    r"\b(?:[A-Z]\d{1,2}[a-z]?(?:-[A-Z]\d?)?(?:\.\d+)*|addendum(?: [A-Z])?|cascade|floor|tier|gate|candidate|frozen|"
    r"head [A-Z]|criteria(?: \d+(?:\.\d+)*)?(?: item \d+)?|plan chapter \d+(?:\.\d+)*|process rule \d+|"
    r"pilot overrides?|ref41|pool_ref41|AI reference|m\d\d_\w+)\b", re.IGNORECASE)
REMOVED = "[…]"
# calibrations[].reference_code: the reference that the probabilities are about, as a code. The text of the
# calibration record names folders of the project and document numbers; the view does not pass it on.
REFERENCE_CODES = ("model_labels_not_human_checked", "export_register_value", "other")
FILE_ROLES = ("gesamt_trig", "ech_ttl", "gesamt_rdfxml", "ech_rdfxml", "ech_yaml", "labels_yaml", "provenance_yaml")


class ViewError(ValueError):
    """A file is absent, or a link between the files is broken. The text is short and holds no path."""


# ---------------------------------------------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------------------------------------------

def _read_json(path: Path, optional: bool = False):
    if not path.is_file():
        if optional:
            return None
        raise ViewError(f"file absent: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        raise ViewError(f"file is not JSON: {path.name}") from None


def _read_yaml(path: Path):
    if not path.is_file():
        raise ViewError(f"file absent: {path.name}")
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)
    except yaml.YAMLError:
        raise ViewError(f"file is not YAML: {path.name}") from None
    if not isinstance(data, dict):
        raise ViewError(f"file has no mapping at the top: {path.name}")
    return data


def read_inputs(inputs_dir: Path) -> dict:
    """The stored inputs of one document: the ONE place that knows the form of the inputs folder.

    Form (CONTRACT.md chapter 4.5): docling.json, atoms.json, blocks.json (required), decisions.json and
    export.json (optional; the export record of a sample gives the name of the parliament).
    """
    inputs_dir = Path(inputs_dir)
    out = {key: _read_json(inputs_dir / name) for key, name in INPUT_FILES.items()}
    out["decisions"] = _read_json(inputs_dir / DECISIONS_FILE, optional=True)
    out["export"] = _read_json(inputs_dir / EXPORT_FILE, optional=True)
    return out


def parliament_name(export) -> str | None:
    """The name of the body of the export record (key body.name), or None. No table of names is in the code."""
    body = (export or {}).get("body") if isinstance(export, dict) else None
    name = body.get("name") if isinstance(body, dict) else None
    return name.strip() if isinstance(name, str) and name.strip() else None


# ---------------------------------------------------------------------------------------------------------------
# small tools
# ---------------------------------------------------------------------------------------------------------------

def _last(iri):
    """Last part of an IRI (after the last slash or hash)."""
    return None if not iri else re.split(r"[/#]", iri)[-1]


def _text(value) -> str:
    """A record value as a string. A YAML boolean keeps its YAML form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _resolve(obj, path: str):
    """The value of the eCH-0295 record at an instance path, for example affairs[0].title[0].text."""
    try:
        for part in re.sub(r"\[(\d+)\]", r".\1", path).split("."):
            obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    except (KeyError, IndexError, ValueError, TypeError):
        raise ViewError(f"no value in the eCH file at {path}") from None
    return obj


def _media_type(name: str) -> str:
    for end, media in MEDIA:
        if name.endswith(end):
            return media
    return "application/octet-stream"


APERTUS_VALUE_TIER = re.compile(r"apertus_q[0-9a-z_]*\Z")    # the value tiers of the Apertus step (m12 writer)


def _group(source: str, apertus: str, tier=None) -> str:
    """Plain class of the source. A code step counts as a read-out only if Apertus states were used. A value of an
    Apertus value head ('make convert' with the Apertus step: tier apertus_q1 or apertus_q2_<field>) has the group
    apertus_values: its states were made for this PDF, not stored (fix step of 16.10.2026)."""
    if source == "apertus_head" and APERTUS_VALUE_TIER.match(str(tier or "")):
        return "apertus_values"
    if source == "apertus_head":
        return "apertus_readout"
    if source == "code_step":
        return "apertus_readout" if apertus == "stored" else "rule"
    return source


def _clean_note(text: str) -> str:
    """A converter note with no path, no document number and no working word of the project."""
    text = _NOTE_PATH.sub(REMOVED, text)
    text = _NOTE_NUMBER.sub(REMOVED, text)
    text = _NOTE_WORDS.sub(REMOVED, text)
    return re.sub(r"\[…\](?:[\s,;:]*\[…\])+", REMOVED, text).strip()


def note_of(text) -> tuple[str | None, dict, str | None]:
    """(note_code, note_params, note) of one label note. A known note: the code and its values, note is None.
    An unknown note: code None and the filtered text. No note: (None, {}, None)."""
    if not isinstance(text, str) or not text.strip():
        return None, {}, None
    for pattern, code, names in NOTE_PATTERNS:
        m = pattern.fullmatch(text.strip())
        if m:
            params = dict(zip(names, m.groups(), strict=True))
            if "agrees" in params:
                params["agrees"] = params["agrees"] == "agrees"
            return code, params, None
    return None, {}, _clean_note(text)


def reference_code(text) -> str | None:
    if not isinstance(text, str) or not text.strip():
        return None
    if text.startswith("OpenParlData export"):
        return "export_register_value"
    return "model_labels_not_human_checked" if text.startswith(("AI reference", "reference labels of the development "
                                                                "documents, made by a language model")) else "other"


def _count(items) -> dict:
    out: dict = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return out


def _check_run_info(run_info: dict) -> None:
    if not isinstance(run_info, dict):
        raise ViewError("run_info is not a mapping")
    rid = run_info.get("record_id")
    if not isinstance(rid, str) or not RECORD_ID.match(rid):
        raise ViewError("run_info.record_id has not the form of a record id")
    for key, values in RUN_INFO_VALUES.items():
        if run_info.get(key) not in values:
            raise ViewError(f"run_info.{key} is not one of {', '.join(values)}")
    if run_info.get("ocr") is not None and run_info["ocr"] not in OCR_VALUES:
        raise ViewError(f"run_info.ocr is not one of {', '.join(OCR_VALUES)}")
    if run_info.get("values") is not None and run_info["values"] not in VALUES_STATES:
        raise ViewError(f"run_info.values is not one of {', '.join(VALUES_STATES)}")
    # optional key of run_info: the tiers of the candidates that the responder rule finds in a document of the kind
    # proposal or executive_proposal and that are not the tier of an addressed body (worker/values_record.py)
    signs = run_info.get("response_signs")
    if signs is not None and not (isinstance(signs, dict) and isinstance(signs.get("responder_tiers"), list)
                                  and all(isinstance(x, str) for x in signs["responder_tiers"])):
        raise ViewError("run_info.response_signs has not the known form")


# ---------------------------------------------------------------------------------------------------------------
# parts of the view
# ---------------------------------------------------------------------------------------------------------------

def _pages(docling: dict, atoms_file: dict) -> list:
    pages, by_number = [], {}
    for p in docling["seiten"]:
        source = TEXT_SOURCE.get(p["textquelle"])
        if source is None:
            raise ViewError(f"page {p['seite']}: unknown text source")
        page = {"number": p["seite"], "width": p["breite"], "height": p["hoehe"], "text_source": source,
                "lines": []}
        pages.append(page)
        by_number[p["seite"]] = page
    for a in atoms_file["atome"]:
        page = by_number.get(a["seite"])
        if page is None:
            raise ViewError(f"line {a['id']}: its page is not in the Docling output")
        page["lines"].append({
            "atom_id": a["id"], "block_id": a["block"], "frame": a["zeilenrahmen"] or a["rahmen"],
            "frame_source": a["zeilenrahmen_quelle"] or "block", "text": a["text"],
            "char_start": a["zeichen"][0], "char_end": a["zeichen"][1],
            "from_ocr": any(m[0] == "ocr" for m in a["merkmale"])})
    return pages


def _labels(lab: dict, blocks_file: dict, text_blocks: dict, decisions: dict, apertus: str, atom_ids: set,
            origin: str = "stored", value_atoms: dict | None = None, measured: bool = True):
    """labels[] plus the maps block -> label, instance path -> label and text block IRI -> copy label.
    origin new (a PDF that is not a sample): in_sample of each label is None (not known). The package cannot
    tell if such a PDF is one of the development documents.
    value_atoms: label id -> the lines of a value that is read from the PDF (provenance file, pdf_evidence; for
    a weak candidate: the lines of the atoms file that its span touches).
    measured is always true: the view function refuses a record with stand-in numbers."""
    value_atoms = value_atoms or {}
    method_of = {c["global_uri"]: c.get("calibration_method") for c in lab.get("calibrations") or []}
    block_atoms = {b["block"]: b["atoms"] for b in blocks_file["blocks"]}
    block_order = [b["block"] for b in blocks_file["blocks"]]
    dec_d1 = (decisions.get("document") or {}).get("d1") or {}
    dec_r2 = decisions.get("r2") or {}
    has_b1s = "b1_s" in decisions
    labels, of_block, of_path, of_subject, seen = [], {}, {}, {}, set()
    for a in lab["label_assertions"]:
        lid = _last(a["global_uri"])
        if lid in seen:
            raise ViewError(f"label {lid}: the id occurs 2 times")
        seen.add(lid)
        kind, source, subject = a["label_kind"], a["label_source"], a["label_subject"]
        ttype = TARGET_TYPE.get(kind, "value")
        block_id = _last(subject) if "/block/" in subject else None
        if kind == "author_switch":
            # the subject is a boundary IRI (.../boundary/after-B<n>), not a block IRI: block_id stays null.
            # The lines of the label are the last line before the boundary and the first line after it.
            before = (_last(subject) or "").removeprefix("after-")
            if before not in block_atoms or before == block_order[-1]:
                raise ViewError(f"label {lid}: its boundary is not after a block of the block file")
            after = block_order[block_order.index(before) + 1]
            atoms = block_atoms[before][-1:] + block_atoms[after][:1]
        elif ttype == "block":
            if block_id not in block_atoms:
                raise ViewError(f"label {lid}: its block is not in the block file")
            atoms = list(block_atoms[block_id])
        elif ttype == "text_block":
            if subject not in text_blocks:
                raise ViewError(f"label {lid}: its text block is not in the provenance file")
            atoms = list(text_blocks[subject]["atom_ids"])
        elif kind == "pdf_value":
            atoms = list(value_atoms.get(lid) or [])
            block_id = _block_at(blocks_file, a.get("span_start"))
        else:
            atoms = []
        for atom in atoms:
            if atom not in atom_ids:
                raise ViewError(f"label {lid}: line {atom} is not in the atoms file")

        probability = a.get("label_probability")
        options = [{"value": _text(o["option_value"]), "probability": o["label_probability"]}
                   for o in a.get("option_probabilities") or []]
        value = _text(a["label_object"])
        if kind == "pdf_value" and not measured:
            probability = None
        if probability is None:
            status, is_top, top_option = "none", None, None
            options = []
        elif kind == "pdf_value":
            # a value reader gives one value and no options
            status, is_top, top_option = a.get("value_status"), None, None
            if status not in ("certain", "unsure"):
                raise ViewError(f"label {lid}: a probability with no value status")
        else:
            status = a.get("value_status")
            if status not in ("certain", "unsure"):
                raise ViewError(f"label {lid}: a probability with no value status")
            if not options:
                raise ViewError(f"label {lid}: a probability with no options")
            top = max(options, key=lambda o: o["probability"])  # the first one of equal values
            is_top = not any(o["probability"] > probability for o in options)
            top_option = None if is_top else dict(top)

        in_sample = a.get("in_sample")
        if in_sample is None and kind == "document_text_parts":
            in_sample = dec_d1.get("in_sample")
        if in_sample is None and kind == "executive_response":
            in_sample = dec_r2.get("in_sample")
        if origin == "new":
            in_sample = None
        note_code, note_params, note = note_of(a.get("label_note"))

        head = None
        if kind == "executive_response" and source == "apertus_head":
            head = "R2"
        elif kind == "block_slot" and source == "code_step" and has_b1s:
            head = "B1"
        elif kind == "document_text_parts" and source == "apertus_head":
            head = "D1"
        elif kind == "document_text_parts" and source == "rule" and method_of.get(a.get("calibration")) == "verifier_platt":
            # a code rule selects the answer; the number is the value of the read-out head D1 for that answer
            head = "D1"

        labels.append({
            "id": lid, "iri": a["global_uri"], "kind": kind, "slot": _last(a["label_predicate"]),
            "predicate": a["label_predicate"], "subject": subject,
            "target": {"type": ttype, "block_id": block_id, "atom_ids": atoms, "page": a.get("page"),
                       "last_page": a.get("last_page"), "char_start": a.get("span_start"),
                       "char_end": a.get("span_end"), "instance_path": a.get("instance_path"),
                       "about_entity": a.get("about_entity")},
            "value": value, "options": options, "probability": probability, "value_status": status,
            "chosen_is_top": is_top, "top_option": top_option,
            "source": {"kind": source, "group": _group(source, apertus, a.get("tier")), "tier": a.get("tier"),
                       "rule_id": a.get("rule_id"), "head": head},
            "calibration_id": _last(a.get("calibration")), "in_sample": in_sample,
            "note_code": note_code, "note_params": note_params, "note": note,
        })
        if kind == "block_slot":
            of_block[block_id] = lid
        path = a.get("instance_path")
        if path and kind in VALUE_KINDS:
            of_path[path] = lid
        if path and kind == "text_wording":
            of_path[path + ".text"] = lid
        if kind == "text_wording":
            of_subject[subject] = lid
    return labels, of_block, of_path, of_subject


def _block_at(blocks_file: dict, position) -> str | None:
    """The block of the block file that holds a position of the document text."""
    if not isinstance(position, int):
        return None
    for b in blocks_file["blocks"]:
        if b["char_start"] <= position < b["char_end"]:
            return b["block"]
    return None


def _span_parts(atoms_file: dict, start, end) -> list:
    """The parts of the lines of the atoms file that a span of the document text touches (the key zeichen of a
    line is its range in the document text): atom id, start and end in the text of the line."""
    out = []
    if not (isinstance(start, int) and isinstance(end, int)):
        return out
    for a in atoms_file["atome"]:
        z0, z1 = a["zeichen"]
        if z1 <= start or z0 >= end or not (a.get("text") or ""):
            continue
        out.append({"atom_id": a["id"], "start": max(start, z0) - z0, "end": min(end, z1) - z0})
    return out


def _one_line(text) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _calibrations(lab: dict, measured: bool = True) -> list:
    """One entry for each calibration record of the labels file. measured is always true (see _make_view)."""
    out = []
    for c in lab.get("calibrations") or []:
        par = {x["parameter_name"]: x["parameter_value"] for x in c.get("calibration_parameters") or []}
        is_value = c.get("calibrated_kind") == "pdf_value"
        if is_value and not measured:
            out.append({"id": _last(c["global_uri"]), "iri": c["global_uri"], "method": c["calibration_method"],
                        "kind": c["calibrated_kind"], "fit_n": None, "in_sample": None,
                        "target_status": "not_measured", "certain_threshold": None, "basis": None,
                        "reference_code": reference_code(c.get("reference_source")), "measure_sets": [],
                        "note": None, "tier": c.get("calibrated_tier"), "measured": False})
            continue
        # the counts that the number of a rule comes from. The records hold them under 3 forms of names:
        # dev_blocks and dev_correct (floor, block labels); blocks and precision (tier records of the cascade);
        # dev_correct and dev_documents with no block count (floor, document label: n is null).
        basis = None
        documents = par.get("dev_documents", par.get("documents"))
        documents = int(documents) if documents is not None else None
        if "dev_blocks" in par and "dev_correct" in par:
            basis = {"n": int(par["dev_blocks"]), "agreed": int(par["dev_correct"]), "documents": documents}
        elif "blocks" in par and "precision" in par:
            basis = {"n": int(par["blocks"]), "agreed": int(round(float(par["precision"]) * float(par["blocks"]))),
                     "documents": documents}
        elif "dev_correct" in par and documents is not None:
            basis = {"n": None, "agreed": int(par["dev_correct"]), "documents": documents}
        elif is_value and "k" in par and "n" in par:
            # a rule tier of a value reader: n documents with a value of the tier, k equal to the export value
            basis = {"n": int(par["n"]), "agreed": int(par["k"]), "documents": int(par["n"])}
        out.append({
            "id": _last(c["global_uri"]), "iri": c["global_uri"], "method": c["calibration_method"],
            "kind": c["calibrated_kind"], "fit_n": c.get("fit_n"), "in_sample": c.get("in_sample"),
            "target_status": c["target_status"], "certain_threshold": c.get("certain_threshold"),
            "basis": basis, "reference_code": reference_code(c.get("reference_source")),
            "measure_sets": [{"name": m["set_name"], "n": m.get("set_n"), "ece": m.get("ece"),
                              "ece_low": m.get("ece_low"), "ece_high": m.get("ece_high"),
                              "brier": m.get("brier"), "nll": m.get("nll")} for m in c.get("measure_sets") or []],
            # the note of a value calibration record is a working text with names of the project: not passed on
            "note": None if is_value else c.get("calibration_note"), "tier": c.get("calibrated_tier"),
            "measured": True})
    return out


def _cascade(man: dict, values: list, slots: list, text_blocks: list) -> dict:
    """head_values.cascade: the cascade of ONE record (manifest key cascade, written by src/m11_writer.py from the
    cascade reader). The view holds codes, rule ids and counts; the page has the texts."""
    mc = man.get("cascade")
    if not isinstance(mc, dict) or not isinstance(mc.get("selection"), dict):
        raise ViewError("the manifest has no cascade (the label selection of the record)")
    kind = mc.get("kind")
    if kind is not None and kind not in KINDS:
        raise ViewError("the manifest gives an unknown kind of document")
    source = mc.get("kind_source") or {}
    kind_from = KIND_FROM.get(source.get("from"))
    if kind_from is None or (kind is None) != (kind_from == "none"):
        raise ViewError("the manifest does not say where the kind of the document comes from")
    if set(mc["selection"]) != set(CASCADE_FIELDS):
        raise ViewError("the cascade of the manifest has not the 7 values")
    of_field = {x["field"]: x for x in slots if x.get("field")}
    value_of = {x["field"]: x for x in values}
    entries = []
    for f in CASCADE_FIELDS:
        sel, s, x = mc["selection"][f], of_field.get(f), value_of.get(f)
        if s is None or s["slot"] != sel.get("slot"):
            raise ViewError(f"value {f}: the slot of the cascade is not the slot of the record")
        searched = bool(sel.get("searched"))
        if searched == (s["state"] == "not_in_this_document_type"):
            raise ViewError(f"value {f}: the selection of the cascade and the state of the slot do not agree")
        if not searched:
            state = "addressee_candidate" if x is not None and x["candidate"] == "addressee" else "not_searched"
        elif x is not None:
            state = "read_from_pdf" if x["written"] else "weak_candidate"
        else:
            # reader_scope: the cascade searches the value, and the rule of the value does not read this document
            state = "reader_scope" if s["reason"] == SCOPE_REASON else "not_found_in_pdf"
        if (x is not None) != (state in ("read_from_pdf", "weak_candidate", "addressee_candidate")):
            raise ViewError(f"value {f}: a value with a state that has no value")
        entries.append({"field": f, "slot": s["slot"], "group": FIELD_GROUP[f], "state": state, "searched": searched,
                        "rules": [str(r) for r in sel.get("rules") or []], "reason": s["reason"],
                        "label_id": s.get("label_id")})
    steps, texts = [], []
    not_written = [str(x.get("slot")) for x in mc.get("text_blocks_not_written") or []]
    for fam in ("submission", "response"):
        st, tx = (mc.get("steps") or {}).get(fam) or {}, (mc.get("texts") or {}).get(fam) or {}
        steps.append({"step": fam, "applies": bool(st.get("applies")), "rules": [str(r) for r in st.get("rules") or []]})
        slot = tx.get("slot")
        texts.append({"step": fam, "slot": slot, "applies": bool(tx.get("applies")), "cut": bool(tx.get("cut")),
                      "rules": [str(r) for r in tx.get("rules") or []],
                      "blocks": sum(1 for t in text_blocks if slot and t["ech_slot"] == slot),
                      # text blocks of this family that are not written to the eCH-0295 part (provenance file only)
                      "not_written": sum(1 for x in not_written if slot and x == slot)})
    # rule V5: a document with no decision of the rule chain (rule id D0). The 2 facts of the PDF that decide the kind.
    v5 = source.get("v5")
    if (kind_from == "rule_v5") != (isinstance(v5, dict) and v5.get("changed") is True):
        raise ViewError("the kind source of the manifest and the facts of rule V5 do not agree")
    kind_facts = None
    if isinstance(v5, dict):
        a_type, tier = v5.get("affair_type_read"), v5.get("responder_tier_read")
        if v5.get("kind_of_the_rule_chain") not in KINDS:
            raise ViewError("the facts of rule V5 have no kind of the rule chain")
        kind_facts = {"kind_of_the_rule_chain": v5["kind_of_the_rule_chain"],
                      "type_word": a_type if a_type not in (None, "none") else None,
                      # the explicit response cue: with no type word it gives the kind response
                      "response_cue": tier == RESPONSE_CUE_TIER,
                      # another sign of the executive (a signature, the head of minutes, a decision): with a type
                      # word it gives the kind combined; alone it changes nothing
                      "response_sign": tier is not None and tier not in (ADDRESSEE_TIER, WEAK_RESPONSE_TIER,
                                                                         RESPONSE_CUE_TIER),
                      "changed": bool(v5.get("changed"))}
    return {"version": mc.get("version"), "reader": mc.get("reader"), "kind": kind, "kind_from": kind_from,
            "kind_rule": source.get("rule"), "rule_chain_id": source.get("s1_rule_id"), "kind_facts": kind_facts,
            "affair_type": mc.get("affair_type_of_the_cascade"), "steps": steps, "entries": entries, "texts": texts,
            "text_blocks_not_written": len(mc.get("text_blocks_not_written") or []),
            "register_only": sum(1 for x in slots if x["state"] == "register_only")}


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _suggestions(man: dict, inputs: dict, page_numbers: set, values: list) -> list:
    """apertus_suggestions[] (CONTRACT.md chapter 25): one entry for each item of the manifest key
    apertus_suggestions, in the sequence of the manifest. A suggestion is not a value of the record: the field has
    no written value. spans: the parts of the lines that its span touches (as for a weak candidate)."""
    ms = man.get("apertus_suggestions")
    if not isinstance(ms, dict) or not isinstance(ms.get("items"), list) or ms.get("status") != SUGGESTION_STATUS \
            or ms.get("form") != SUGGESTION_FORM:
        raise ViewError("the manifest key apertus_suggestions has not the known form")
    written = {x["field"] for x in values if x["written"]}
    block_ids = {b["block"] for b in inputs["blocks"]["blocks"]}
    out, seen = [], set()
    for x in ms["items"]:
        f = x.get("field") if isinstance(x, dict) else None
        if f not in CASCADE_FIELDS:
            raise ViewError("an Apertus suggestion has an unknown field")
        if f in seen:
            raise ViewError(f"suggestion {f}: the field occurs 2 times")
        seen.add(f)
        if f in written:
            raise ViewError(f"suggestion {f}: the field has a value in the record")
        if x.get("status") != SUGGESTION_STATUS or x.get("in_record") is not False:
            raise ViewError(f"suggestion {f}: the status is not below the entry limit, or it is in the record")
        page, last = x.get("page"), x.get("last_page")
        if page not in page_numbers or (last is not None and last not in page_numbers):
            raise ViewError(f"suggestion {f}: its page is not a page of the PDF")
        p, k, n = x.get("probability"), x.get("k"), x.get("n")
        if not (_is_number(p) and P_LOW <= p <= P_HIGH):
            raise ViewError(f"suggestion {f}: the probability is not in the range 0.005 to 0.995")
        if not (_is_int(k) and _is_int(n) and 0 <= k <= n):
            raise ViewError(f"suggestion {f}: the counts of its tier are not 0 <= k <= n")
        start, end = x.get("char_start"), x.get("char_end")
        if not (_is_int(start) and _is_int(end) and 0 <= start < end):
            raise ViewError(f"suggestion {f}: its span is not a range of the document text")
        block_id = x.get("block")
        if block_id is not None and block_id not in block_ids:
            raise ViewError(f"suggestion {f}: its block is not in the block file")
        tier, value, printed = x.get("tier"), x.get("value"), x.get("printed")
        if not (isinstance(tier, str) and tier.startswith("apertus_q2_") and APERTUS_VALUE_TIER.match(tier)):
            raise ViewError(f"suggestion {f}: its tier is not a Q2 tier of the Apertus step")
        if not (isinstance(value, str) and isinstance(printed, str) and value.strip() and printed.strip()):
            raise ViewError(f"suggestion {f}: it has no value or no wording")
        hp = x.get("head_probability")
        spans = _span_parts(inputs["atoms"], start, end)
        out.append({
            "field": f, "value": value, "value_printed": printed,
            "probability": p, "k": k, "n": n, "tier": tier, "band": x.get("band"),
            "head_probability": hp if _is_number(hp) else None, "near": x.get("near") is True,
            "page": page, "last_page": last, "char_start": start, "char_end": end, "block_id": block_id,
            "atom_ids": [e["atom_id"] for e in spans], "spans": spans,
            "status": SUGGESTION_STATUS, "in_record": False, "called_because": x.get("called_because")})
    return out


def _checks(man: dict, val: dict) -> list:
    out = [{"id": "writer_check", "state": "passed" if man.get("check_passed") else "failed", "reason": None}]
    for cid in CHECKS + (VALUE_CHECKS if man.get("schema") == VALUES_RECORD else ()):
        entry = val.get(cid)
        if not isinstance(entry, dict) or "passed" not in entry:
            # the validator stops after a failed parse check: the later checks did not run
            out.append({"id": cid, "state": "skipped", "reason": "earlier_check_failed"})
            continue
        out.append({"id": cid, "state": "passed" if entry.get("passed") else "failed", "reason": None})
    state = (val.get("C10_shacl") or {}).get("status")
    if man.get("schema") == VALUES_RECORD and state == "run" and "passed" in val["C10_shacl"]:   # src/m11_validate.py
        out.append({"id": "C10_shacl", "state": "passed" if val["C10_shacl"]["passed"] else "failed", "reason": None})
    elif state in ("passed", "failed"):
        out.append({"id": "C10_shacl", "state": state, "reason": None})
    else:
        out.append({"id": "C10_shacl", "state": "skipped", "reason": "shacl_tool_absent"})
    return out


def _rdfxml_not_readable(val: dict) -> list:
    """The RDF/XML files that the parse check of validation.json did not read (a character that XML 1.0 cannot hold)."""
    results = (val.get("C2_parse") or {}).get("results") or []
    return [r.get("file") for r in results
            if isinstance(r, dict) and r.get("parsed") is False and str(r.get("file", "")).endswith(".rdf.xml")]


def _files(record: Path, man: dict, record_id: str) -> list:
    out = []
    for role in FILE_ROLES:
        entry = (man.get("outputs") or {}).get(role)
        if not entry:
            raise ViewError(f"manifest.json names no output of the role {role}")
        name = Path(entry["path"]).name
        if not (record / name).is_file():
            raise ViewError(f"file absent: {name}")
        out.append({"name": name, "role": role, "media_type": _media_type(name), "bytes": entry["bytes"],
                    "sha256": entry["sha256"], "url": f"/api/records/{record_id}/files/{name}"})
    for name, role in (("manifest.json", "manifest"), ("validation.json", "validation")):
        data = (record / name).read_bytes()
        out.append({"name": name, "role": role, "media_type": "application/json", "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(), "url": f"/api/records/{record_id}/files/{name}"})
    # the optional files of a record with values from the PDF (14.10.2026): the values with their probabilities
    # (writer m11-writer-5 or later), the PDF and one image of each page. A record of the earlier form has none of them.
    entry = (man.get("outputs") or {}).get("values_ttl")
    if entry:
        name = Path(entry["path"]).name
        if not (record / name).is_file():
            raise ViewError(f"file absent: {name}")
        out.append({"name": name, "role": "values_ttl", "media_type": _media_type(name), "bytes": entry["bytes"],
                    "sha256": entry["sha256"], "url": f"/api/records/{record_id}/files/{name}"})
    extra = [("source.pdf", "source_pdf")] + [(n, "page_image") for n in page_images(record)]
    for name, role in extra:
        if (record / name).is_file():
            data = (record / name).read_bytes()
            out.append({"name": name, "role": role, "media_type": _media_type(name), "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(), "url": f"/api/records/{record_id}/files/{name}"})
    return out


def page_images(record: Path) -> list:
    """The names page-<n>.png of the record folder, by page number."""
    found = [(int(m.group(1)), x.name) for x in record.iterdir() if (m := RX_PAGE_IMAGE.fullmatch(x.name))]
    return [name for _, name in sorted(found)]


# ---------------------------------------------------------------------------------------------------------------
# the view
# ---------------------------------------------------------------------------------------------------------------

def _make_view(record: Path, inputs_dir: Path, run_info: dict) -> dict:
    _check_run_info(run_info)
    record_id, apertus = run_info["record_id"], run_info["apertus"]
    man = _read_json(record / "manifest.json")
    val = _read_json(record / "validation.json")
    prefix = man["doc_id"]
    inst = _read_yaml(record / f"{prefix}.ech.yaml")
    prov = _read_yaml(record / f"{prefix}.provenance.yaml")
    lab = _read_yaml(record / f"{prefix}.labels.yaml")
    inputs = read_inputs(inputs_dir)
    blocks_file, decisions = inputs["blocks"], inputs["decisions"] or {}

    pages = _pages(inputs["docling"], inputs["atoms"])
    atom_ids = {ln["atom_id"] for p in pages for ln in p["lines"]}
    block_ids = {b["block"] for b in blocks_file["blocks"]}

    # the author blocks of the provenance file, by IRI
    tb_records = prov.get("text_block_records") or []
    tb_parts = {t["global_uri"]: {"block_ids": [u["unit_id"] for u in t["units"]],
                                  "atom_ids": [e["atom_id"] for u in t["units"] for e in u["atom_evidence"]]}
                for t in tb_records}

    # a record of src/m11_writer.py: the head values are read from the PDF
    from_pdf = man.get("schema") == VALUES_RECORD
    if from_pdf and ((man.get("value_calibration") or {}).get("stand_in") or man.get("synthetic_values")):
        # decision P-1: no stand-in number in a record that a user sees
        raise ViewError("the record holds stand-in numbers for its values: the package gives no view of it")
    measured = True
    by_rule = {rec["instance_path"]: rec for rec in prov.get("value_records") or []
               if rec.get("derivation") == "extracted_from_pdf_by_rule"}
    # the lines and the line parts of each value label: the PDF evidence of its value record; a weak candidate
    # has no value record (it is not in the eCH-0295 part), so its lines come from its span
    value_parts = {}
    for a in lab["label_assertions"] if from_pdf else ():
        if a["label_kind"] != "pdf_value":
            continue
        rec = by_rule.get(a.get("instance_path")) if a.get("instance_path") else None
        if rec is not None:
            parts = [{"atom_id": e["atom_id"], "start": e.get("match_start"), "end": e.get("match_end")}
                     for e in rec.get("pdf_evidence") or []]
        else:
            parts = _span_parts(inputs["atoms"], a.get("span_start"), a.get("span_end"))
        value_parts[_last(a["global_uri"])] = parts
    value_atoms = {lid: [x["atom_id"] for x in parts] for lid, parts in value_parts.items()}

    labels, label_of_block, label_of_path, label_of_text_block = _labels(
        lab, blocks_file, tb_parts, decisions, apertus, atom_ids, run_info["origin"], value_atoms, measured)

    blocks = []
    for b in blocks_file["blocks"]:
        for atom in b["atoms"]:
            if atom not in atom_ids:
                raise ViewError(f"block {b['block']}: line {atom} is not in the atoms file")
        blocks.append({"id": b["block"], "page": b["page"], "docling_label": b["docling_label"],
                       "char_start": b["char_start"], "char_end": b["char_end"], "atom_ids": list(b["atoms"]),
                       "text": b["text"], "label_id": label_of_block.get(b["block"])})

    head = []
    for rec in prov.get("value_records") or []:
        path, derivation = rec["instance_path"], rec["derivation"]
        if derivation not in ORIGIN:
            raise ViewError(f"head value {path}: unknown derivation")
        head.append({"instance_path": path, "ech_slot": rec["ech_slot"], "value": _text(_resolve(inst, path)),
                     "derivation": derivation, "origin": ORIGIN[derivation],
                     "pdf_consistency": rec.get("pdf_consistency"), "mapping_match": rec.get("mapping_match"),
                     "atom_ids": [e["atom_id"] for e in rec.get("pdf_evidence") or []],
                     "label_id": label_of_path.get(path)})

    text_blocks = []
    for n, t in enumerate(tb_records, 1):
        parts = tb_parts[t["global_uri"]]
        for unit in parts["block_ids"]:
            if unit not in block_ids:
                raise ViewError(f"text block {n}: block {unit} is not in the block file")
        if t["mapping_status"] == "in_ech_instance":
            slot, text_type, path = t["ech_slot"], t["ech_text_type"], t["instance_path"]
            label_id = label_of_path.get(path + ".text")
        else:
            # a text block that is in the provenance file only (a PDF with no export record): it has no slot and
            # no path of the eCH-0295 record. The two values are empty strings. The text type is the section key.
            slot, text_type, path = "", t["section_key"], ""
            label_id = label_of_text_block.get(t["global_uri"])
        text_blocks.append({"id": f"textblock-{n}", "iri": t["global_uri"], "ech_slot": slot,
                            "text_type": text_type, "instance_path": path,
                            "block_ids": parts["block_ids"], "atom_ids": parts["atom_ids"],
                            "char_count": t["char_count"], "extent_value_status": t["extent_value_status"],
                            "label_id": label_id})

    def first(end: str):
        return next((h["value"] for h in head if h["ech_slot"].endswith(end)), None)

    sources = prov.get("source_documents") or []
    if not sources:
        raise ViewError("the provenance file names no source document")
    sd = sources[0]
    has_export = bool(man.get("has_export")) if from_pdf else (
        any(h["origin"] == "export" for h in head) or any(x["source"]["kind"] == "export" for x in labels))

    # values[] and slots[] (CONTRACT.md chapter 16): one entry for each value that is read from the PDF, and one
    # entry for each slot of Affair, Submission and ResponseStep with its state
    values, slots = [], []
    floor = (man.get("value_floor") or {}) if from_pdf else {}
    if from_pdf:
        slot_of_label = {x.get("label_id"): x for x in man.get("slots") or [] if x.get("label_id")}
        by_id = {x["id"]: x for x in labels}
        all_folds = {_last(c["global_uri"]): next((x["parameter_value"] for x in c.get("calibration_parameters") or []
                                                   if x["parameter_name"] == "jeffreys_mean_all_folds"), None)
                     for c in lab.get("calibrations") or []}
        comparison = man.get("comparison_values") or {}
        sources = man.get("value_probability_sources") or {}
        addressee = {x.get("field") for x in man.get("addressee_candidates") or []}
        cal_in_sample = {_last(c["global_uri"]): c.get("in_sample") for c in lab.get("calibrations") or []}
        if any(v not in ("all folds", "no unit of the pair") for v in sources.values()) or \
                (man.get("value_calibration") or {}).get("probability_from") != "all folds":
            # decision D4: one number for each document, the value of the rule tier over all folds
            raise ViewError("the record has a probability that is not the value of the rule tier over all folds")
        for a in lab["label_assertions"]:
            if a["label_kind"] != "pdf_value":
                continue
            lid = _last(a["global_uri"])
            m = FIELD_ID.match(lid)
            if not m or lid not in slot_of_label:
                raise ViewError(f"label {lid}: the manifest names no slot for it")
            written, field, mslot = m.group(1) == "pdf", m.group(2), slot_of_label[lid]
            # a candidate: weak (the slot was searched, reason weak_candidate_only) or the addressed body of a
            # proposal (the slot is not searched in this kind of document)
            candidate = None if written else ("weak" if mslot.get("reason") == WEAK_REASON else (
                "addressee" if mslot.get("state") == "not_in_this_document_type" and field in addressee else None))
            if written != (mslot.get("state") == "read_from_pdf") or (not written and candidate is None):
                raise ViewError(f"label {lid}: the state of its slot does not agree with the label")
            if candidate == "addressee" and not str(a.get("label_note") or "").startswith(ADDRESSEE_MARK):
                raise ViewError(f"label {lid}: the candidate of a slot that is not searched has not the mark of an "
                                "addressed body")
            if written != bool(a.get("instance_path")):
                raise ViewError(f"label {lid}: a written value has a path of the record, a weak candidate has none")
            check = a.get("export_check") or "not_compared"
            if check not in EXPORT_CHECKS:
                raise ViewError(f"label {lid}: unknown result of the cross-check")
            x = by_id[lid]
            printed, value = _text(a.get("value_wording")), _text(a["label_object"])
            export_value = _text(a["export_value"]) if a.get("export_value") is not None else None
            tier_p = all_folds.get(_last(a.get("calibration")))
            source = sources.get(field)
            values.append({
                "field": field, "slot": mslot["slot"], "name_key": f"value.{field}",
                "written": written, "candidate": candidate,
                "value_printed": printed, "value": value,
                "value_form": VALUE_FORMS.get(a.get("normalisation_rule"), "printed"),
                "differs_from_printed": _one_line(printed) != _one_line(value),
                "comparison_value": _text(comparison[field]) if comparison.get(field) is not None else None,
                "probability": x["probability"], "value_status": x["value_status"], "measured": measured,
                "tier_probability": float(tier_p) if isinstance(tier_p, (int, float)) else None,
                # all_folds: p_all_folds of the rule tier. no_unit: the calibration file has no unit of the pair
                # (field, tier); the number is its stored value for such a tier.
                "probability_source": None if not written else ("all_folds" if source == "all folds" else "no_unit"),
                # true: this document is one of the development documents that the number counts
                "in_sample": cal_in_sample.get(_last(a.get("calibration")))
                if isinstance(cal_in_sample.get(_last(a.get("calibration"))), bool) else None,
                "tier": a.get("tier"), "rule_id": a.get("rule_id"), "normalisation_rule": a.get("normalisation_rule"),
                "page": a.get("page"), "last_page": a.get("last_page"), "char_start": a.get("span_start"),
                "char_end": a.get("span_end"), "block_id": x["target"]["block_id"], "atom_ids": list(x["target"]["atom_ids"]),
                "spans": [e for e in value_parts.get(lid) or []
                          if isinstance(e.get("start"), int) and isinstance(e.get("end"), int)],
                # the export value stands in the comparison only: it is never a value of the record
                "export_check": check, "export_value": export_value,
                # exact: the export string is the value of the record. after_normalisation: equal by the
                # comparison rule (case, accents, white space, the table of the bodies), with another wording
                "export_match": None if check != "equal_to_export" else (
                    "exact" if export_value is not None and _one_line(export_value) == _one_line(value)
                    else "after_normalisation"),
                "label_id": lid, "calibration_id": _last(a.get("calibration")), "instance_path": a.get("instance_path")})
        gaps = {_last(g["global_uri"]): g for g in lab.get("pdf_value_gaps") or []}
        for x in man.get("slots") or []:
            if x.get("state") not in SLOT_STATES:
                raise ViewError(f"slot {x.get('slot')}: unknown state")
            # export_has_value: true or false if the export record was compared for a value that the rules did not
            # find (the value of the export is not in the view); null with no export record or no comparison
            has_value = (gaps.get(x.get("gap_id")) or {}).get("export_has_value") if x.get("gap_id") else None
            if x.get("result") not in (None, NOT_SEARCHED) or (x.get("result") == NOT_SEARCHED and (
                    x["state"] != "not_in_this_document_type" or x.get("kind") not in KINDS or not x.get("cascade_rules"))):
                raise ViewError(f"slot {x.get('slot')}: the result of the cascade has not the known form")
            if x.get("field") and x["state"] == "not_in_this_document_type" and x.get("result") != NOT_SEARCHED:
                raise ViewError(f"slot {x.get('slot')}: a value that is not searched has no kind and no cascade rule")
            slots.append({"slot": x["slot"], "state": x["state"], "reason": x["reason"], "field": x.get("field"),
                          # the cascade does not search the slot in this kind of document (decision D1)
                          "result": "not_searched" if x.get("result") == NOT_SEARCHED else None,
                          "kind": x.get("kind"), "cascade_rules": list(x.get("cascade_rules") or []),
                          "label_id": x.get("label_id"), "gap_id": x.get("gap_id"),
                          "export_has_value": has_value if isinstance(has_value, bool) else None,
                          "name_key": f"pslot.{x['slot']}"})
    cascade = _cascade(man, values, slots, text_blocks) if from_pdf else None
    # the Apertus suggestions below the entry limit (CONTRACT.md chapter 25): only a record of the Apertus step of
    # 'make convert' has the manifest key. A record with no such key gets no view key (its view does not change).
    suggestions = None
    if "apertus_suggestions" in man:
        if not from_pdf:
            raise ViewError("the manifest has Apertus suggestions, but the values of the record are not read from "
                            "the PDF")
        suggestions = _suggestions(man, inputs, {p["number"] for p in pages}, values)
    # finding S3-03: signs of a response in a document of the kind proposal or executive_proposal. The kind does not
    # change. responder_candidates: candidates of the responder rule with a tier that is not the tier of an addressed
    # body (run_info, from the worker; null if the worker gave none). text_blocks: text blocks with a label of a
    # response that are not written to the eCH-0295 part.
    response_signs = None
    if from_pdf and cascade["kind"] in PROPOSAL_KINDS:
        tiers = (run_info.get("response_signs") or {}).get("responder_tiers")
        n_blocks = next(t["not_written"] for t in cascade["texts"] if t["step"] == "response")
        response_signs = {"responder_candidates": len(tiers) if tiers is not None else None,
                          "responder_tiers": list(tiers) if tiers is not None else [], "text_blocks": n_blocks}
    values_state = run_info.get("values") or ("pdf" if from_pdf else "off")
    if (values_state == "pdf") != from_pdf:
        raise ViewError("run_info.values and the form of the record do not agree")
    head_values = {
        "source": "pdf" if from_pdf else ("export" if has_export else "none"), "state": values_state,
        "cross_check": bool(from_pdf and has_export),
        "probabilities_measured": measured if from_pdf else None,
        # the kind of the document (stage 0 of the cascade; manifest key cascade.kind). The kind selects which
        # values are searched. null: the kind is not known (each value is searched), or source is not pdf.
        "document_kind": cascade["kind"] if from_pdf else None,
        # the cascade of this record: the kind, the affair type, the steps and the state of each of the 7 values
        "cascade": cascade,
        # the floor: a value of a rule tier with a stored probability below the threshold is not written
        "floor": {"threshold": floor.get("threshold"),
                  "not_written": [x["field"] for x in values if x["candidate"] == "weak"]} if from_pdf else None,
        # the body that a proposal addresses: a candidate label, never a responder (decision D3)
        "addressee_candidates": [x["field"] for x in values if x["candidate"] == "addressee"] if from_pdf else [],
        "response_signs": response_signs,
        "i95_gaps": [g["slot"] for g in man.get("i95_gaps") or []] if from_pdf else [],
        "fields_not_read": [{"field": x["field"], "reason": x["reason"]} for x in man.get("fields_not_read") or []]
        if from_pdf else [],
        "counts": (man.get("counts") or {}).get("values") if from_pdf else None,
        "slot_counts": (man.get("counts") or {}).get("slots") if from_pdf else None,
    }
    document = {
        "source_iri": sd["global_uri"], "record_iri": man["record_iri"], "container_iri": man.get("container_iri"),
        "named_graphs": man["named_graphs"], "pdf_sha256": sd["file_sha256"], "page_count": sd["page_count"],
        "language": sd.get("document_language"), "parliament": blocks_file.get("parliament"),
        "parliament_name": parliament_name(inputs.get("export")),
        "title": first(".title.text"), "affair_number": first(".affair_number"), "affair_type": first(".affair_type"),
        "has_export": has_export, "conformance": man.get("conformance"), "head": head, "text_blocks": text_blocks,
    }

    label_counts = {
        "total": len(labels),
        "with_probability": sum(x["probability"] is not None for x in labels),
        "certain": sum(x["value_status"] == "certain" for x in labels),
        "unsure": sum(x["value_status"] == "unsure" for x in labels),
        "none": sum(x["value_status"] == "none" for x in labels),
        "chosen_not_top": sum(x["chosen_is_top"] is False for x in labels),
        "by_source": _count(x["source"]["kind"] for x in labels),
        "by_group": _count(x["source"]["group"] for x in labels),
        "by_kind": _count(x["kind"] for x in labels),
    }
    counts = {"pages": len(pages), "lines": len(atom_ids), "blocks": len(blocks), "labels": label_counts,
              "triples": man["rdf"]["triples"], "record": man["counts"]}

    checks = _checks(man, val)
    files = _files(record, man, record_id)
    # a page with an image of the record gets the key image (the address of the image); no other page has the key
    for f in files:
        if f["role"] == "page_image":
            number = int(RX_PAGE_IMAGE.fullmatch(f["name"]).group(1))
            for page in pages:
                if page["number"] == number:
                    page["image"] = f["url"]

    flags = [x["in_sample"] for x in labels]
    in_sample = True if any(f is True for f in flags) else (False if any(f is False for f in flags) else None)
    valid = bool((man.get("validation") or {}).get("passed"))
    run = {
        "origin": run_info["origin"], "mode": run_info["mode"], "converter_mode": man["mode"], "apertus": apertus,
        "profile": run_info["profile"], "status": STATUS, "record_status": man["status"], "human_checked": False,
        "in_sample": in_sample, "valid": valid, "generated_at": lab["label_run"]["datetime_generated"],
        "seconds": run_info.get("seconds") or man.get("seconds") or {},
        "candidate": decisions.get("candidate"), "model": (man.get("model") or {}).get("model"),
    }

    def notice(code: str, **params):
        return {"code": code, "params": params}

    notices = [notice("proposal"), notice("no_human_check")]
    if in_sample is True:
        notices.append(notice("in_sample_heads" if apertus == "stored" else "in_sample_rules"))
    # the values of Apertus value heads ('make convert' with the Apertus step): their own notice, and the notice
    # no_apertus only for a record with no label from Apertus (fix step of 16.10.2026)
    n_values = sum(x["source"]["group"] == "apertus_values" for x in labels)
    if apertus == "stored":
        notices.append(notice("stored_apertus"))
    elif not n_values:
        notices.append(notice("no_apertus"))
    if n_values:
        notices.append(notice("apertus_values", n=n_values))
    if from_pdf:
        notices.append(notice("values_from_pdf" if has_export else "values_from_pdf_no_check"))
        notices.append(notice("values_measured"))
        notices.append(notice("cascade_selection"))
        if head_values["addressee_candidates"]:
            notices.append(notice("addressee_candidate"))
        if response_signs and (response_signs["responder_candidates"] or response_signs["text_blocks"]):
            notices.append(notice("response_signs", candidates=response_signs["responder_candidates"] or 0,
                                  blocks=response_signs["text_blocks"]))
        if head_values["floor"]["not_written"]:
            notices.append(notice("weak_candidates", n=len(head_values["floor"]["not_written"])))
        if head_values["i95_gaps"]:
            notices.append(notice("recorded_gaps", n=len(head_values["i95_gaps"])))
    elif has_export:
        notices.append(notice("head_from_export"))
    if label_counts["chosen_not_top"]:
        notices.append(notice("chosen_not_top", n=label_counts["chosen_not_top"]))
    if not text_blocks:
        notices.append(notice("no_text_block"))
    if not has_export and not from_pdf:
        notices.append(notice("no_export"))
    if run_info["origin"] == "new":
        notices.append(notice("not_a_sample"))
        notices.append(notice("not_examined_pipeline"))
        if run_info.get("ocr") in OCR_VALUES:
            notices.append(notice("ocr_" + run_info["ocr"]))
    if any(c["id"] == "C10_shacl" and c["state"] == "skipped" for c in checks):
        notices.append(notice("shacl_not_run"))
    if not valid:
        notices.append(notice("not_valid"))
    bad_xml = _rdfxml_not_readable(val)
    if bad_xml:
        notices.append(notice("rdfxml_not_readable", n=len(bad_xml)))

    view = {"schema": SCHEMA, "record_id": record_id, "doc_id": prefix if str(prefix).isdigit() else None,
            "run": run, "notices": notices, "head_values": head_values, "values": values}
    if suggestions is not None:
        view["apertus_suggestions"] = suggestions
    view.update({"slots": slots, "document": document, "pages": pages, "blocks": blocks,
                 "labels": labels, "calibrations": _calibrations(lab, measured), "counts": counts, "checks": checks,
                 "files": files})
    return view


def make_view(record_dir, inputs_dir, run_info: dict) -> dict:
    """The view of one record. Raises ViewError if a file is absent or a link between the files is broken."""
    try:
        return _make_view(Path(record_dir), Path(inputs_dir), run_info)
    except ViewError:
        raise
    except KeyError as e:
        raise ViewError(f"a file of the record or of the inputs has no key {e.args[0]!r}") from None
    except (TypeError, IndexError, AttributeError) as e:
        raise ViewError(f"a file of the record or of the inputs has not the known form ({type(e).__name__})") from None


# ---------------------------------------------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------------------------------------------

def default_run_info(record_dir, inputs_dir) -> dict:
    """run_info for a call with no --run-info file: read from the record and the inputs, not from a list."""
    man = _read_json(Path(record_dir) / "manifest.json")
    decisions = _read_json(Path(inputs_dir) / DECISIONS_FILE, optional=True) or {}
    rules = man.get("mode") == "floor"
    if not str(man.get("doc_id")).isdigit():          # a PDF with no document number (stage P0b)
        return {"record_id": f"u-{str(man.get('pdf_sha256'))[:16]}", "origin": "new", "mode": "auto",
                "apertus": "none", "profile": "native"}
    return {"record_id": f"s-{man.get('doc_id')}" + ("-rules" if rules else ""), "origin": "stored",
            "mode": "rules" if rules else "auto", "apertus": "stored" if decisions.get("states") else "none",
            "profile": "native"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Writes the view parlpdfech-site-view/3 of one record folder.")
    ap.add_argument("--record", required=True, help="folder with the 9 converter files")
    ap.add_argument("--inputs", required=True, help="folder with docling.json, atoms.json, blocks.json")
    ap.add_argument("--run-info", help="JSON file with the run_info object; default: read from the record")
    ap.add_argument("--out", required=True, help="the view file to write")
    a = ap.parse_args(argv)
    start = time.perf_counter()
    try:
        run_info = _read_json(Path(a.run_info)) if a.run_info else default_run_info(a.record, a.inputs)
        view = make_view(Path(a.record), Path(a.inputs), run_info)
    except ViewError as e:
        print(json.dumps({"error": "view", "text": str(e)}), file=sys.stderr)
        return 1
    seconds = time.perf_counter() - start
    Path(a.out).write_text(json.dumps(view, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = view["counts"]["labels"]
    print(json.dumps({"record_id": view["record_id"], "labels": c["total"], "certain": c["certain"],
                      "unsure": c["unsure"], "none": c["none"], "lines": view["counts"]["lines"],
                      "notices": [n["code"] for n in view["notices"]], "seconds": round(seconds, 3)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

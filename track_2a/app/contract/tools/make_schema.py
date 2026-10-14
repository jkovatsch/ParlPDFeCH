"""Throw-away tool of the contract: writes contract/view.schema.json (JSON Schema, draft 2020-12).

Use: python package/contract/tools/make_schema.py package/contract/view.schema.json
The schema file is the contract. This tool only keeps it short to write.
"""
import json
import sys

N = {"type": "null"}
S = {"type": "string"}
I = {"type": "integer"}
NUM = {"type": "number"}
B = {"type": "boolean"}
P = {"type": "number", "minimum": 0, "maximum": 1}


def opt(x):
    return {"anyOf": [x, N]}


def obj(props, optional=(), extra=False, desc=None):
    o = {"type": "object", "properties": props, "required": [k for k in props if k not in optional],
         "additionalProperties": extra}
    if desc:
        o["description"] = desc
    return o


def arr(x, desc=None):
    a = {"type": "array", "items": x}
    if desc:
        a["description"] = desc
    return a


def enum(*v, desc=None):
    e = {"enum": list(v)}
    if desc:
        e["description"] = desc
    return e


SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
RECORD_ID = {"type": "string", "pattern": "^(s-[0-9]+|u-[0-9a-f]{16})(-rules)?$"}
IDS = arr(S)
OPTION = obj({"value": S, "probability": P})
NOTE_CODES = ["switch_between_blocks", "value_derivation", "wording_copy", "final_check", "unsure_final_check_differs",
              "comparison_value", "weak_candidate", "addressee_candidate"]
REFERENCE_CODES = ["model_labels_not_human_checked", "export_register_value", "other"]
NOTICE_CODES = ["proposal", "no_human_check", "in_sample_heads", "in_sample_rules", "stored_apertus", "no_apertus",
                "chosen_not_top", "no_text_block", "no_export", "not_a_sample", "not_examined_pipeline",
                "ocr_apple", "ocr_none", "shacl_not_run", "not_valid", "rdfxml_not_readable",
                "values_from_pdf", "values_from_pdf_no_check", "values_measured", "weak_candidates",
                "cascade_selection", "addressee_candidate", "response_signs",
                "recorded_gaps", "head_from_export"]
FIELDS = ["affair_type", "title", "affair_number", "submission_date", "response_date", "responder", "sponsor"]
SLOT_STATES = ["read_from_pdf", "not_found_in_pdf", "not_in_this_document_type", "register_only"]
KINDS = ["proposal", "response", "combined", "executive_proposal", "committee_report", "minutes", "other"]
ENTRY_STATES = ["read_from_pdf", "not_found_in_pdf", "reader_scope", "weak_candidate", "not_searched",
                "addressee_candidate"]
EXPORT_CHECKS = ["equal_to_export", "differs_from_export", "no_export_value", "not_compared"]

run = obj({
    "origin": enum("stored", "new", desc="stored: the inputs (Docling output, lines, export record, states) come "
               "from the package. new: Docling ran on this computer (stage P0b)."),
    "mode": enum("auto", "rules", desc="The mode of the request."),
    "converter_mode": enum("cascade", "floor", desc="manifest.json key mode."),
    "apertus": enum("none", "stored", desc="stored: decisions from stored Apertus states. none: code rules only."),
    "profile": enum("slim", "full", "native"),
    "status": {"const": "EXCEPTION, NOT RELEASED", "description": "Machine field. The pages do not show it."},
    "record_status": {**S, "description": "manifest.json key status, not changed."},
    "human_checked": {"const": False},
    "in_sample": opt({**B, "description": "Three states. true: 1 or more labels of the record have in_sample "
                      "true. false: no label has true, and 1 or more have false. null: not known. For origin "
                      "new the value is null: the package knows the SHA-256 of its samples only and cannot "
                      "tell if another PDF is one of the development documents."}),
    "valid": {**B, "description": "manifest.json key validation.passed."},
    "generated_at": {**S, "description": "labels file key label_run.datetime_generated (UTC)."},
    "seconds": {"type": "object", "additionalProperties": NUM,
                "description": "Seconds of each step. Keys of the worker: one for each stage id, and total."},
    "candidate": opt(S), "model": opt(S),
}, optional=("candidate", "model"))

notice = obj({"code": enum(*NOTICE_CODES), "params": {"type": "object"}},
             desc="The text is the string notice.<code> of ui/strings.json. params fills its placeholders.")

head = obj({
    "instance_path": S, "ech_slot": S, "value": S,
    "derivation": {**S, "description": "provenance file key value_records[].derivation, not changed."},
    "origin": enum("export", "pdf_copy", "pdf_rule", "code_rule", "identifier", "schema",
                   desc="Source of the value, as view 1 groups the derivations. pdf_rule: a value reader (a code "
                        "rule) read the value from the PDF (derivation extracted_from_pdf_by_rule)."),
    "pdf_consistency": opt(S), "mapping_match": opt(S), "atom_ids": IDS, "label_id": opt(S),
})
text_block = obj({
    "id": S, "iri": S, "ech_slot": S, "text_type": S, "instance_path": S, "block_ids": IDS, "atom_ids": IDS,
    "char_count": I, "extent_value_status": enum("certain", "unsure"), "label_id": opt(S),
})
document = obj({
    "source_iri": S, "record_iri": S, "container_iri": opt(S),
    "named_graphs": {"type": "object", "additionalProperties": S},
    "pdf_sha256": SHA, "page_count": I, "language": opt(S),
    "parliament": {**opt(S), "description": "The key of the body (block file key parliament)."},
    "parliament_name": {**opt(S), "description": "The name of the body (export record key body.name); null "
                                                  "for a PDF with no export record."},
    "title": {**opt(S), "description": "The value of the record. With head_values.source pdf it is the value "
                                       "that a rule read from the PDF and that is in the record, or null if "
                                       "the rules found no value or only a weak candidate."},
    "affair_number": opt(S), "affair_type": opt(S),
    "has_export": {**B, "description": "false for a PDF with no export record (stage P0b). With "
                                       "head_values.source pdf the export record gives the cross-check only."},
    "conformance": opt(S),
    "head": arr(head, "One entry for each leaf value of the eCH-0295 record (provenance file, value_records)."),
    "text_blocks": arr(text_block, "The author blocks of the eCH-0295 record (provenance file, text_block_records)."),
})

line = obj({
    "atom_id": S, "block_id": S,
    "frame": {"type": "array", "items": NUM, "minItems": 4, "maxItems": 4,
              "description": "[left, top, right, bottom] in PDF points, origin top left."},
    "frame_source": S, "text": S, "char_start": I, "char_end": I, "from_ocr": B,
})
page = obj({"number": I, "width": NUM, "height": NUM, "text_source": enum("pdf", "ocr", "mixed"), "lines": arr(line)})
# 14.10.2026: the address of the image of the page (a record with values from the PDF and a page image); optional key
page["properties"]["image"] = {"type": "string", "description": "Address of the PNG image of the page below "
                                                                "/api/records/<record_id>/files/. Only a page with an "
                                                                "image has this key."}
block = obj({"id": S, "page": I, "docling_label": S, "char_start": I, "char_end": I, "atom_ids": IDS, "text": S,
             "label_id": opt(S)})

label = obj({
    "id": {**S, "description": "Last part of the label IRI. One of a kind in the record."},
    "iri": S,
    "kind": enum("document_text_parts", "block_slot", "author_switch", "executive_response", "text_wording",
                 "export_value", "constant_value", "pdf_value", desc="labels file key label_kind. pdf_value: a "
                 "value that a code rule read from the PDF (it has no options)."),
    "slot": {**S, "description": "Local name of the predicate IRI."},
    "predicate": S, "subject": S,
    "target": obj({
        "type": enum("document", "block", "text_block", "value"),
        "block_id": opt(S), "atom_ids": IDS, "page": opt(I), "last_page": opt(I),
        "char_start": opt(I), "char_end": opt(I), "instance_path": opt(S), "about_entity": opt(S)}),
    "value": {**S, "description": "The selected option (labels file key label_object)."},
    "options": arr(OPTION, "All options in the sequence of the record, each with its stored number. Each stored "
                           "number has the limits 0.005 and 0.995, so the numbers of one label can sum to more "
                           "than 1. Empty for a label with no probability."),
    "probability": opt(P),
    "value_status": enum("certain", "unsure", "none", desc="none: the label has no probability."),
    "chosen_is_top": opt({**B, "description": "false if another option has a higher probability."}),
    "top_option": opt(OPTION),
    "source": obj({
        "kind": enum("rule", "apertus_head", "code_step", "export", "constant", "copy",
                     desc="labels file key label_source, not changed."),
        "group": enum("rule", "apertus_readout", "export", "constant", "copy",
                      desc="Group for the page. apertus_head gives apertus_readout. code_step gives "
                           "apertus_readout if run.apertus is stored, else rule."),
        "tier": opt(S), "rule_id": opt(S),
        "head": opt(enum("D1", "B1", "R2", desc="Read-out head whose values the label uses, if known."))}),
    "calibration_id": opt(S),
    "in_sample": opt({**B, "description": "null: the record does not say it, or origin is new (not known)."}),
    "note_code": opt(enum(*NOTE_CODES, desc="The note of the label (labels file key label_note) as a code, if the "
                          "view function knows the note. The page has the text note.<code> in its strings file.")),
    "note_params": {"type": "object", "description": "The values of the note: before and after (block ids) for "
                    "switch_between_blocks; derivation for value_derivation; agrees (boolean) for final_check."},
    "note": {**opt(S), "description": "A note that the view function does not know, in English, after a filter "
             "that removes paths, document numbers and working words of the project (mark […]). null if "
             "note_code is set or the label has no note. Only for the technical details of the page."},
})

calibration = obj({
    "id": S, "iri": S, "method": S, "kind": S, "fit_n": opt(I), "in_sample": opt(B),
    "target_status": enum("target_met", "target_not_met", "not_met_on_unseen_parliaments", "not_measured"),
    "certain_threshold": opt(NUM),
    "basis": opt(obj({"n": opt(I), "agreed": I, "documents": opt(I)},
                     desc="The counts behind the number of a rule, if the calibration record holds them: n blocks "
                          "(null if the record counts documents only), agreed, documents.")),
    "reference_code": opt(enum(*REFERENCE_CODES, desc="The reference that the probability is about, as a code. "
                               "model_labels_not_human_checked: reference labels of the development documents, "
                               "made by a language model and not checked by a human. other: the record names "
                               "another reference. The text of the calibration record (key reference_source of "
                               "the labels file) is not in the view.")),
    "measure_sets": arr(obj({"name": S, "n": opt(I), "ece": opt(NUM), "ece_low": opt(NUM), "ece_high": opt(NUM),
                             "brier": opt(NUM), "nll": opt(NUM)})),
    "note": {**opt(S), "description": "calibration_note of the labels file, not changed: an English working text "
             "of the converter. The pages do not show it. null for a record of the kind pdf_value."},
    "tier": {**opt(S), "description": "The rule tier of a record of the kind pdf_value, else null."},
    "measured": {**B, "description": "Always true. The view function refuses a record with stand-in numbers."},
})

value = obj({
    "field": enum(*FIELDS), "slot": {**S, "description": "<Class>.<slot> of eCH-0295, for example Affair.title."},
    "name_key": {**S, "description": "The string key value.<field> of ui/strings.json."},
    "written": {**B, "description": "true: the value is in the eCH-0295 part of the record (label id pdf-<field>). "
                "false: a candidate (label id candidate-<field>): the value is NOT in the eCH-0295 part "
                "(key candidate)."},
    "candidate": opt(enum("weak", "addressee", desc="null for written true. weak: the stored probability of the rule "
                          "tier is below head_values.floor.threshold; the slot has the state not_found_in_pdf with "
                          "the reason weak_candidate_only. addressee: the body that the text of a proposal "
                          "addresses; the cascade searches no response step in a document of the kind proposal or "
                          "executive_proposal, so the slot has the state not_in_this_document_type and the body is "
                          "never a responder of the record.")),
    "value_printed": {**S, "description": "The wording of the PDF at the span, with no change (labels file key "
                                          "value_wording)."},
    "value": {**S, "description": "The value of the label (labels file key label_object). For written true it is "
                                  "the value in the eCH-0295 record: the printed wording on one line, or a list "
                                  "value or a calendar day that follows from the printed wording (value_form)."},
    "value_form": enum("printed", "list_value", "iso_day", desc="How value follows from value_printed. printed: "
                       "the wording on one line (white space as one space; a hyphen at a line end joined). "
                       "list_value: the value of the eCH-0295 list for the printed type word. iso_day: the "
                       "printed date as a calendar day."),
    "differs_from_printed": {**B, "description": "true: value and value_printed differ after each run of white "
                             "space is one space. The page then shows the two strings."},
    "comparison_value": {**opt(S), "description": "The comparison value of the value reader (manifest key "
                         "comparison_values): the folded form for the cross-check and the calibration. It is "
                         "not a value of the record. null if the manifest gives none."},
    "probability": {**P, "description": "The stored decimal of the label: the share of the development documents "
                    "in which a value of this rule tier was equal to the OpenParlData value (Jeffreys mean, "
                    "limits 0.005 and 0.995): the value of the rule tier over all folds, for each document, "
                    "also a development document."},
    "value_status": enum("certain", "unsure", desc="The stored word of the label."),
    "measured": {**B, "description": "Always true. The view function refuses a record with stand-in numbers."},
    "tier_probability": {**opt(P), "description": "The stored probability of the rule tier from all development "
                         "documents (calibration parameter jeffreys_mean_all_folds). The floor uses this number."},
    "probability_source": opt(enum("all_folds", "no_unit", desc="Where probability comes from. all_folds: the "
                                   "value of the rule tier over all folds of the calibration file (all development "
                                   "documents). no_unit: the calibration file has no document for this pair of "
                                   "field and tier; the number is its stored value for such a tier. No fold value "
                                   "is shown. null for a candidate.")),
    "in_sample": {**opt(B), "description": "true: this document is one of the development documents that the number "
                  "of the rule tier counts. false: it is not. null: the record does not say."},
    "tier": opt(S), "rule_id": opt(S), "normalisation_rule": opt(S),
    "page": opt(I), "last_page": opt(I),
    "char_start": {**opt(I), "description": "Start of the span in the document text."}, "char_end": opt(I),
    "block_id": opt(S), "atom_ids": IDS,
    "spans": arr(obj({"atom_id": S, "start": I, "end": I}),
                 "The part of each line that holds the value: positions in the text of the line."),
    "export_check": enum(*EXPORT_CHECKS, desc="The cross-check with the OpenParlData export record. not_compared: "
                         "no export record, or no comparison for the field (always for a weak candidate)."),
    "export_value": {**opt(S), "description": "The value of the export for equal_to_export and "
                     "differs_from_export, else null. It stands in the comparison only: it is never a value of "
                     "the record."},
    "export_match": opt(enum("exact", "after_normalisation", desc="For equal_to_export only, else null. exact: the "
                             "export string is the value of the record. after_normalisation: equal by the "
                             "comparison rule (case, accents, white space, punctuation, the table of the "
                             "bodies), but the two strings differ.")),
    "label_id": S, "calibration_id": opt(S),
    "instance_path": {**opt(S), "description": "The path in the eCH-0295 file; null for a weak candidate."},
})
slot = obj({
    "slot": S, "state": enum(*SLOT_STATES), "reason": {**S, "description": "The string key slot_reason.<reason>. "
               "weak_candidate_only: the rules found only a value of a tier below the floor; label_id names the "
               "candidate label. reader_scope (state not_found_in_pdf): the cascade searches the value, and the "
               "rule of the value does not read this document (for example a printed type word that has no value "
               "in the eCH-0295 list, or a response with no author in its head)."},
    "result": opt(enum("not_searched", desc="not_searched: the cascade does not search the slot in a document of "
                       "this kind (state not_in_this_document_type; kind and cascade_rules say why). null: each "
                       "other slot.")),
    "kind": opt(enum(*KINDS, desc="For result not_searched: the kind of the document. Else null.")),
    "cascade_rules": arr(S, "For result not_searched: the ids of the cascade rules that cut the slot. Else empty."),
    "field": opt(enum(*FIELDS)), "label_id": opt(S), "gap_id": opt(S),
    "export_has_value": {**opt(B), "description": "For a field with no value in the record: true or false if the "
                         "export record was compared (the value of the export is not in the view). null with no "
                         "export record, with no comparison, and for each other slot."},
    "name_key": {**S, "description": "The string key pslot.<Class>.<slot> of ui/strings.json."},
})
head_values = obj({
    "source": enum("pdf", "export", "none", desc="Where the head values of the record come from. pdf: code rules "
                   "read them from the PDF (manifest schema parlpdfech-pdf-values-record/1). export: the earlier "
                   "record form of a sample (PARLPDFECH_VALUES=off). none: the earlier record form of a PDF with "
                   "no export record."),
    "state": enum("pdf", "off", "held", desc="The record path of the worker: pdf, the switch PARLPDFECH_VALUES=off, "
                  "or a sample of worker/values_hold.json (that list is empty)."),
    "cross_check": {**B, "description": "true: an export record was compared with the values (source pdf only)."},
    "probabilities_measured": opt({**B, "description": "true: source pdf (the calibration file of the product). "
                                   "null: source is not pdf. Never false."}),
    "document_kind": opt(enum(*KINDS, desc="The kind of the document: stage 0 of the cascade (manifest key "
                              "cascade.kind). The kind selects which values are searched. null: source is not pdf, "
                              "or the kind is not known (then each value is searched).")),
    "cascade": opt(obj({
        "version": opt(S), "reader": opt(S),
        "kind": opt(enum(*KINDS)),
        "kind_from": enum("rule_chain", "rule_v5", "argument", "none", desc="Where the kind comes from. rule_chain: "
                          "code rules (the rule role and the rule id of the rule file). rule_v5: the rule chain "
                          "made no decision (rule id D0); the type word and a response cue of the PDF decide "
                          "(rule V5 of the cascade reader; kind_facts has the 2 facts). none: not known."),
        "kind_rule": opt(S), "rule_chain_id": opt(S),
        "kind_facts": opt(obj({
            "kind_of_the_rule_chain": enum(*KINDS), "type_word": opt(S), "response_cue": B, "response_sign": B,
            "changed": B},
            desc="For a document with no decision of the rule chain (rule id D0): the 2 facts of the PDF that rule "
                 "V5 uses. type_word: the list value of the type word that the type rule read, or null. "
                 "response_cue: true if the responder rule found a responding body by the tier of an explicit "
                 "response cue (a heading or a phrase of the first lines says that the executive answers). "
                 "response_sign: true if the responder rule found the body by another tier that is not the tier "
                 "of an addressed body and not the tier of a response phrase in the running text (for example a "
                 "signature of the executive or the head of minutes). A type word with a cue or a sign gives "
                 "the kind combined. A type word alone gives proposal. A cue alone gives response. A sign alone "
                 "changes nothing. Not more than one of response_cue and response_sign is true. changed: true if "
                 "the facts gave another kind than the kind of the rule chain (then kind_from is rule_v5). A type "
                 "word draft_decree changes nothing. null: the rule chain made a decision.")),
        "affair_type": {**opt(S), "description": "The affair type of stage 1: a value of the eCH-0295 list, or none "
                        "(the type reader found no type that is used for the selection)."},
        "steps": arr(obj({"step": enum("submission", "response"), "applies": B, "rules": arr(S)}),
                     "The two steps of the record: applies true if a document of this kind can state the step."),
        "entries": arr(obj({"field": enum(*FIELDS), "slot": S, "group": enum("affair", "submission", "response"),
                            "state": enum(*ENTRY_STATES), "searched": B, "rules": arr(S), "reason": S,
                            "label_id": opt(S)}),
                       "The 7 values, each with its state in this record. read_from_pdf: written, with a label "
                       "pdf-<field>. not_found_in_pdf: searched, no value. reader_scope: searched, no value; the "
                       "rule of the value does not read this document (slot reason reader_scope). weak_candidate: "
                       "searched, a candidate "
                       "that is not written. not_searched: the cascade does not search it in this kind of "
                       "document. addressee_candidate: not searched; the body that the proposal addresses is a "
                       "candidate that is not written."),
        "texts": arr(obj({"step": enum("submission", "response"), "slot": opt(S), "applies": B, "cut": B,
                          "rules": arr(S), "blocks": I, "not_written": I}),
                     "The text slot of each step. cut true: the cascade does not give the text slot to this kind "
                     "of document; a text block of this family is then not written to the eCH-0295 part. blocks: "
                     "the text blocks of the family in the eCH-0295 part. not_written: the text blocks of the "
                     "family that are in the provenance file only."),
        "text_blocks_not_written": I,
        "register_only": {**I, "description": "The count of slots[] with the state register_only."},
    }, desc="The cascade of this record: an earlier decision (the kind, then the affair type) selects which entries "
            "are searched. null: source is not pdf.")),
    "floor": opt(obj({"threshold": opt(NUM), "not_written": arr(enum(*FIELDS))},
                     desc="The floor of the values: a value of a rule tier whose stored probability is below "
                          "threshold is not written. not_written: the fields with such a weak candidate. null: "
                          "source is not pdf.")),
    "addressee_candidates": arr(enum(*FIELDS), "The fields with a candidate of the kind addressee."),
    "response_signs": opt(obj({
        "responder_candidates": {**opt(I), "description": "The count of candidates of the responder rule with a "
                                 "rule tier that is not the tier of an addressed body. null: the worker gave no "
                                 "count."},
        "responder_tiers": arr(S, "The rule tiers of these candidates."),
        "text_blocks": {**I, "description": "The count of text blocks with a label of a response that are not "
                        "written to the eCH-0295 part."}},
        desc="Signs of a response in a document of the kind proposal or executive_proposal. The kind does not "
             "change; the view has the notice response_signs if one of the 2 counts is above 0. null: another "
             "kind, or source is not pdf.")),
    "i95_gaps": arr(S, "The required slots of eCH-0295 for which the rules found no value that is written "
                       "(recorded gaps)."),
    "fields_not_read": arr(obj({"field": S, "reason": S})),
    "counts": opt({"type": "object", "description": "manifest.json key counts.values."}),
    "slot_counts": opt({"type": "object", "description": "manifest.json key counts.slots."}),
})

counts = obj({
    "pages": I, "lines": I, "blocks": I,
    "labels": obj({"total": I, "with_probability": I, "certain": I, "unsure": I, "none": I, "chosen_not_top": I,
                   "by_source": {"type": "object", "additionalProperties": I},
                   "by_group": {"type": "object", "additionalProperties": I},
                   "by_kind": {"type": "object", "additionalProperties": I}}),
    "triples": {"type": "object", "additionalProperties": I,
                "description": "manifest.json key rdf.triples: one count for each named graph, and union."},
    "record": {"type": "object", "description": "manifest.json key counts, not changed."},
})
check = obj({"id": S, "state": enum("passed", "failed", "skipped",
                                    desc="skipped: the check did not run (reason shacl_tool_absent or "
                                         "earlier_check_failed)."), "reason": opt(S)})
file_ = obj({"name": S, "role": S, "media_type": S, "bytes": I, "sha256": SHA, "url": S})

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:parlpdfech:schema:site-view:3",
    "title": "parlpdfech-site-view/3",
    "description": "The data of one record for the pages of the package (CONTRACT.md chapters 6, 16 and 17).",
    **obj({
        "schema": {"const": "parlpdfech-site-view/3"}, "record_id": RECORD_ID,
        "doc_id": opt({"type": "string", "pattern": "^[0-9]+$"}),
        "run": run, "notices": arr(notice), "head_values": head_values,
        "values": arr(value, "One entry for each value that a code rule read from the PDF, in the sequence of the "
                             "labels file: the values of the record (written true) and the weak candidates "
                             "(written false). Empty if head_values.source is not pdf."),
        "slots": arr(slot, "One entry for each slot of the classes Affair, Submission and ResponseStep of eCH-0295 "
                           "with one of 4 states. Empty if head_values.source is not pdf."),
        "document": document, "pages": arr(page), "blocks": arr(block),
        "labels": arr(label), "calibrations": arr(calibration), "counts": counts, "checks": arr(check),
        "files": arr(file_),
    }),
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=1)
    f.write("\n")

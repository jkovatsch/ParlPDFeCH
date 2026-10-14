"""Validates a view file against contract/view.schema.json and checks the links between its parts.

Use: python package/contract/tools/validate_view.py package/contract/view.schema.json VIEW.json [VIEW.json ...]
Exit code 0: each file is valid. Exit code 1: one or more files are not valid.
"""
import json
import re
import sys

import jsonschema


def links(v: dict) -> list[str]:
    bad = []
    atoms = {ln["atom_id"] for p in v["pages"] for ln in p["lines"]}
    blocks = {b["id"] for b in v["blocks"]}
    labels = {x["id"] for x in v["labels"]}
    cals = {c["id"] for c in v["calibrations"]}
    if len(labels) != len(v["labels"]):
        bad.append("a label id occurs 2 times")
    for x in v["labels"]:
        t = x["target"]
        bad += [f"label {x['id']}: unknown atom {a}" for a in t["atom_ids"] if a not in atoms]
        if t["block_id"] and t["block_id"] not in blocks:
            bad.append(f"label {x['id']}: unknown block {t['block_id']}")
        if x["calibration_id"] and x["calibration_id"] not in cals:
            bad.append(f"label {x['id']}: unknown calibration {x['calibration_id']}")
        if (x["probability"] is None) != (x["value_status"] == "none"):
            bad.append(f"label {x['id']}: probability and value_status do not agree")
        if x["probability"] is not None and x["kind"] == "pdf_value":
            if x["options"] or x["chosen_is_top"] is not None:
                bad.append(f"label {x['id']}: a value read from the PDF has options")
        elif x["probability"] is not None:
            sel = [o["probability"] for o in x["options"] if o["value"] == x["value"]]
            if sel != [x["probability"]]:
                bad.append(f"label {x['id']}: the selected option is not in options with the same probability")
            top = max(o["probability"] for o in x["options"])
            if x["chosen_is_top"] != (x["probability"] >= top):
                bad.append(f"label {x['id']}: chosen_is_top is wrong")
    for b in v["blocks"]:
        bad += [f"block {b['id']}: unknown atom {a}" for a in b["atom_ids"] if a not in atoms]
        if b["label_id"] and b["label_id"] not in labels:
            bad.append(f"block {b['id']}: unknown label {b['label_id']}")
    for h in v["document"]["head"]:
        if h["label_id"] and h["label_id"] not in labels:
            bad.append(f"head {h['instance_path']}: unknown label {h['label_id']}")
    for x in v["labels"]:
        if x.get("note_code") and x.get("note"):
            bad.append(f"label {x['id']}: note_code and note are both set")
    if v["run"]["origin"] == "new":
        # a PDF that is not a sample: the package does not know if it is a development document
        if v["run"]["in_sample"] is not None or any(x["in_sample"] is not None for x in v["labels"]):
            bad.append("origin new: in_sample is not null")
    texts = [x.get("note") or "" for x in v["labels"]] + [c.get("note") or "" for c in v["calibrations"]]
    if any("/" in t and re.search(r"[\w.\-]+/[\w.\-]+/", t) for t in texts):
        bad.append("a note holds a path")
    bad += value_links(v, atoms, blocks, cals)
    c = v["counts"]["labels"]
    if c["total"] != len(v["labels"]) or c["certain"] + c["unsure"] + c["none"] != c["total"]:
        bad.append("counts.labels does not agree with labels")
    if v["counts"]["lines"] != len(atoms) or v["counts"]["blocks"] != len(blocks):
        bad.append("counts.lines or counts.blocks does not agree")
    return bad


def cascade_links(hv: dict, values: list, of_slot: dict) -> list[str]:
    """The links of head_values.cascade: the 7 entries against values[] and slots[]."""
    bad, c = [], hv.get("cascade")
    if not isinstance(c, dict):
        return ["head_values.source pdf with no cascade"]
    if c["kind"] != hv["document_kind"] or (c["kind"] is None) != (c["kind_from"] == "none"):
        bad.append("cascade: the kind and document_kind do not agree")
    fields = [e["field"] for e in c["entries"]]
    if sorted(fields) != sorted(["affair_type", "title", "affair_number", "submission_date", "response_date",
                                 "responder", "sponsor"]):
        bad.append("cascade: entries[] has not each of the 7 values one time")
    value_of = {x["field"]: x for x in values}
    step_of = {s["step"]: s for s in c["steps"]}
    for e in c["entries"]:
        s, x = of_slot.get(e["slot"]), value_of.get(e["field"])
        want = None
        if s is None or s["field"] != e["field"]:
            bad.append(f"cascade entry {e['field']}: its slot is not a slot of the view")
            continue
        if x is not None:
            want = "read_from_pdf" if x["written"] else x["candidate"] + "_candidate"
        elif s["state"] == "not_in_this_document_type":
            want = "not_searched"
        elif s["state"] == "not_found_in_pdf":
            want = "reader_scope" if s["reason"] == "reader_scope" else "not_found_in_pdf"
        if e["state"] != want:
            bad.append(f"cascade entry {e['field']}: the state {e['state']} does not agree with values[] and slots[]")
        if e["searched"] == (e["state"] in ("not_searched", "addressee_candidate")):
            bad.append(f"cascade entry {e['field']}: searched does not agree with the state")
        if not e["searched"] and (s["result"] != "not_searched" or s["cascade_rules"] != e["rules"]):
            bad.append(f"cascade entry {e['field']}: the slot has not the cascade rules of the entry")
        if e["label_id"] != s["label_id"]:
            bad.append(f"cascade entry {e['field']}: the label of the entry is not the label of the slot")
        if e["group"] != "affair" and e["searched"] and not (step_of.get(e["group"]) or {}).get("applies"):
            bad.append(f"cascade entry {e['field']}: searched in a step that does not apply")
    if c["kind"] in ("proposal", "executive_proposal") and (step_of.get("response") or {}).get("applies"):
        bad.append("cascade: a response step in a document of the kind proposal or executive_proposal")
    # rule V5: the kind of a document with no decision of the rule chain follows from the 2 facts of the PDF
    kf = c["kind_facts"]
    if (c["kind_from"] == "rule_v5") != (kf is not None and kf["changed"]):
        bad.append("cascade: kind_from rule_v5 and kind_facts.changed do not agree")
    if kf is not None:
        sub = kf["type_word"] in ("motion", "postulate", "motion_and_postulate", "motion_then_postulate",
                                  "interpellation", "request", "question", "parliamentary_initiative")
        want_kind = kf["kind_of_the_rule_chain"] if kf["type_word"] == "draft_decree" else (
            "combined" if sub and (kf["response_cue"] or kf["response_sign"]) else "proposal" if sub
            else "response" if kf["response_cue"] else kf["kind_of_the_rule_chain"])
        if kf["response_cue"] and kf["response_sign"]:
            bad.append("cascade: kind_facts has a response cue and a response sign (one responder tier gives one of them)")
        if c["kind"] != want_kind or kf["changed"] != (c["kind"] != kf["kind_of_the_rule_chain"]) or c["rule_chain_id"] != "D0":
            bad.append("cascade: the kind does not follow from the 2 facts of rule V5")
    for tx in c["texts"]:
        if tx["cut"] and tx["blocks"]:
            bad.append(f"cascade text slot {tx['step']}: a text block in a slot that the cascade does not give to the kind")
    if sum(tx["not_written"] for tx in c["texts"]) != c["text_blocks_not_written"]:
        bad.append("cascade: the counts of the text blocks that are not written do not agree")
    # finding S3-03: signs of a response in a document of the kind proposal or executive_proposal
    rs = hv["response_signs"]
    if (rs is not None) != (c["kind"] in ("proposal", "executive_proposal")):
        bad.append("head_values.response_signs: not null only for the kinds proposal and executive_proposal")
    if rs is not None:
        if rs["text_blocks"] != next(tx["not_written"] for tx in c["texts"] if tx["step"] == "response"):
            bad.append("head_values.response_signs.text_blocks is not the count of the cascade")
        if (rs["responder_candidates"] or 0) != len(rs["responder_tiers"]) or "rsp_addressee_cue" in rs["responder_tiers"]:
            bad.append("head_values.response_signs: the candidates and their tiers do not agree")
    return bad


def value_links(v: dict, atoms: set, blocks: set, cals: set) -> list[str]:
    """The links of head_values, values[] and slots[] (CONTRACT.md chapter 16)."""
    bad = []
    hv, values, slots = v["head_values"], v["values"], v["slots"]
    by_id = {x["id"]: x for x in v["labels"]}
    if hv["source"] != "pdf":
        if values or slots or hv["cross_check"] or hv["probabilities_measured"] is not None:
            bad.append("head_values.source is not pdf, but the view has values, slots or a cross-check")
        if any(x["kind"] == "pdf_value" for x in v["labels"]):
            bad.append("head_values.source is not pdf, but a label has the kind pdf_value")
        if (hv["state"] == "pdf"):
            bad.append("head_values.state pdf with another source")
        return bad
    if hv["state"] != "pdf":
        bad.append("head_values.source pdf with another state")
    if hv["cross_check"] != v["document"]["has_export"]:
        bad.append("head_values.cross_check and document.has_export do not agree")
    if any(h["origin"] == "export" for h in v["document"]["head"]) or any(x["kind"] == "export_value" for x in v["labels"]):
        bad.append("head_values.source pdf, but a value of the record comes from the export")
    names = [s["slot"] for s in slots]
    if len(set(names)) != len(names) or not slots:
        bad.append("slots[] is empty, or a slot occurs 2 times")
    of_slot = {s["slot"]: s for s in slots}
    pdf_labels = {x["id"] for x in v["labels"] if x["kind"] == "pdf_value"}
    if {x["label_id"] for x in values} != pdf_labels or len(values) != len(pdf_labels):
        bad.append("values[] and the labels of the kind pdf_value do not agree")
    for x in values:
        lab = by_id.get(x["label_id"])
        s = of_slot.get(x["slot"])
        if lab is None or s is None:
            bad.append(f"value {x['field']}: unknown label or slot")
            continue
        if s["label_id"] != x["label_id"] or s["field"] != x["field"]:
            bad.append(f"value {x['field']}: its slot does not name this label")
        if x["written"] and s["state"] != "read_from_pdf":
            bad.append(f"value {x['field']}: a written value, but its slot has not the state read_from_pdf")
        if x["written"] != (x["candidate"] is None):
            bad.append(f"value {x['field']}: written and candidate do not agree")
        if x["written"] and x["probability_source"] not in ("all_folds", "no_unit"):
            bad.append(f"value {x['field']}: a written value whose probability is not the value over all folds")
        if x["candidate"] == "addressee":
            # the body that a proposal addresses: not in the eCH-0295 part, the slot is not searched
            if s["state"] != "not_in_this_document_type" or s["result"] != "not_searched":
                bad.append(f"value {x['field']}: an addressed body, but its slot has not the result not_searched")
            if x["instance_path"] is not None or not x["label_id"].startswith("candidate-"):
                bad.append(f"value {x['field']}: an addressed body with a path of the record")
            if x["field"] != "responder" or hv["document_kind"] not in ("proposal", "executive_proposal"):
                bad.append(f"value {x['field']}: an addressed body outside a proposal")
            if x["field"] not in hv["addressee_candidates"]:
                bad.append(f"value {x['field']}: an addressed body that head_values does not name")
            if any(h["label_id"] == x["label_id"] for h in v["document"]["head"]):
                bad.append(f"value {x['field']}: an addressed body is a value of the record")
        elif not x["written"]:
            # a weak candidate: not in the eCH-0295 part
            if s["state"] != "not_found_in_pdf" or s["reason"] != "weak_candidate_only":
                bad.append(f"value {x['field']}: a weak candidate, but its slot has not the reason weak_candidate_only")
            if x["instance_path"] is not None or not x["label_id"].startswith("candidate-"):
                bad.append(f"value {x['field']}: a weak candidate with a path of the record")
            thr = (hv.get("floor") or {}).get("threshold")
            if x["tier_probability"] is None or thr is None or not x["tier_probability"] < thr:
                bad.append(f"value {x['field']}: a weak candidate whose tier probability is not below the floor")
            if x["field"] not in hv["floor"]["not_written"]:
                bad.append(f"value {x['field']}: a weak candidate that head_values.floor does not name")
            if any(h["label_id"] == x["label_id"] for h in v["document"]["head"]):
                bad.append(f"value {x['field']}: a weak candidate is a value of the record")
        elif x["instance_path"] is None or not x["label_id"].startswith("pdf-"):
            bad.append(f"value {x['field']}: a written value with no path of the record")
        elif x["tier_probability"] is not None and (hv.get("floor") or {}).get("threshold") is not None \
                and x["tier_probability"] < hv["floor"]["threshold"]:
            bad.append(f"value {x['field']}: a written value of a tier below the floor")
        if x["differs_from_printed"] != (" ".join(x["value_printed"].split()) != " ".join(x["value"].split())):
            bad.append(f"value {x['field']}: differs_from_printed does not agree with the two strings")
        if (x["export_match"] is not None) != (x["export_check"] == "equal_to_export"):
            bad.append(f"value {x['field']}: export_match and export_check do not agree")
        if (lab["value"], lab["probability"], lab["value_status"]) != (x["value"], x["probability"], x["value_status"]):
            bad.append(f"value {x['field']}: value, probability or value status differs from its label")
        if x["measured"] != hv["probabilities_measured"]:
            bad.append(f"value {x['field']}: measured differs from head_values.probabilities_measured")
        if not x["measured"] and (x["probability"] is not None or x["value_status"] != "none"):
            bad.append(f"value {x['field']}: a number with no measurement")
        if x["measured"] and (x["probability"] is None or x["value_status"] not in ("certain", "unsure")):
            bad.append(f"value {x['field']}: measured, but no probability or no value status")
        bad += [f"value {x['field']}: unknown atom {a}" for a in x["atom_ids"] + [p["atom_id"] for p in x["spans"]]
                if a not in atoms]
        if x["block_id"] and x["block_id"] not in blocks:
            bad.append(f"value {x['field']}: unknown block")
        if x["calibration_id"] and x["calibration_id"] not in cals:
            bad.append(f"value {x['field']}: unknown calibration")
        if (x["export_value"] is not None) != (x["export_check"] in ("equal_to_export", "differs_from_export")):
            bad.append(f"value {x['field']}: export_value and export_check do not agree")
        if not hv["cross_check"] and x["export_check"] != "not_compared":
            bad.append(f"value {x['field']}: a cross-check result with no export record")
    with_label = [s for s in slots if s["label_id"]]
    if len(with_label) != len(values):
        bad.append("the slots with a label and values[] do not agree")
    for s in slots:
        if s["state"] == "read_from_pdf" and s["field"] and not s["label_id"]:
            bad.append(f"slot {s['slot']}: read from the PDF with no label")
        if s["state"] != "read_from_pdf" and s["label_id"] and s["reason"] != "weak_candidate_only" \
                and s["result"] != "not_searched":
            bad.append(f"slot {s['slot']}: a label with another state than read_from_pdf")
        if s["reason"] == "weak_candidate_only" and not s["label_id"]:
            bad.append(f"slot {s['slot']}: the reason weak_candidate_only with no candidate label")
        if (s["result"] == "not_searched") != (bool(s["cascade_rules"]) and s["kind"] is not None) or \
                (s["result"] == "not_searched" and (s["state"] != "not_in_this_document_type" or s["kind"] != hv["document_kind"])):
            bad.append(f"slot {s['slot']}: result, kind and cascade_rules do not agree")
        if s["field"] and s["state"] == "not_in_this_document_type" and s["result"] != "not_searched":
            bad.append(f"slot {s['slot']}: a value that is not searched with no kind and no cascade rule")
    bad += cascade_links(hv, values, of_slot)
    if hv["probabilities_measured"] is not True:
        bad.append("head_values.source pdf with no measured calibration file: the package makes no such record")
    if any(c["kind"] == "pdf_value" and not c["measured"] for c in v["calibrations"]):
        bad.append("a calibration record of a value is not measured")
    codes = [n["code"] for n in v["notices"]]
    if ("weak_candidates" in codes) != bool(hv["floor"]["not_written"]):
        bad.append("the notice weak_candidates and head_values.floor.not_written do not agree")
    if ("addressee_candidate" in codes) != bool(hv["addressee_candidates"]):
        bad.append("the notice addressee_candidate and head_values.addressee_candidates do not agree")
    rs = hv["response_signs"]
    if ("response_signs" in codes) != bool(rs and (rs["responder_candidates"] or rs["text_blocks"])):
        bad.append("the notice response_signs and head_values.response_signs do not agree")
    want = "values_measured"
    if want not in codes or "cascade_selection" not in codes or ("values_from_pdf" if hv["cross_check"] else "values_from_pdf_no_check") not in codes:
        bad.append("a notice of the values is absent")
    for gap in hv["i95_gaps"]:
        s = of_slot.get(f"Affair.{gap}")
        if s is None or s["state"] == "read_from_pdf":
            bad.append(f"recorded gap {gap}: its slot has a value")
    doc = v["document"]
    for key, field in (("title", "title"), ("affair_number", "affair_number"), ("affair_type", "affair_type")):
        val = next((x["value"] for x in values if x["field"] == field and x["written"]), None)
        if doc[key] != val:
            bad.append(f"document.{key} is not the value that was read from the PDF")
    return bad


def main() -> int:
    schema = json.load(open(sys.argv[1], encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    val = jsonschema.Draft202012Validator(schema)
    code = 0
    for p in sys.argv[2:]:
        v = json.load(open(p, encoding="utf-8"))
        errs = [f"{'/'.join(map(str, e.absolute_path))}: {e.message[:160]}" for e in val.iter_errors(v)]
        if not errs:
            errs = links(v)
        print(json.dumps({"file": p, "valid": not errs, "errors": errs[:20]}))
        code = code or (1 if errs else 0)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

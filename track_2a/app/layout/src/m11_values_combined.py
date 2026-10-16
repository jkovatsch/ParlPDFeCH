"""The combined reader of addendum I: the cascade reader of the rules, and the Apertus tiers after it.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: PROPOSED, NOT RELEASED. No human checked this file. This file changes no existing file.
Rules: `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md`, chapters 6 to 8 (rules I5 to I7).

1 Task
  `read_document_combined(doc, heads_output)` calls the cascade reader `m11_values_cascade.read_document`.
  It then adds the answers of the heads in the order of rule I5. This file registers no reader.
  With no heads output the result is exactly the result of the cascade reader.
  The import of this file by `m11_values_base.load_rule_modules` has no effect on a result.

2 The heads output of one document (made by `src/m11_value_heads2.py`, function `apply_document`)
  {"q0": {"class", "probability", "given"}, "q1": {"class", "probability", "given"},
   "q2": {registry id: record}}
  A `Q2` record is the JSON form of `ValueCandidate` or `NotFound` of the base module.
  A record with a value has the key `detail` with the keys `head_probability` and `band` (`hi` or `lo`).

3 The entry record (file `entry.json` of the design tool; chapters 7 and 8)
  {"q0": {"entered": bool}, "q1": {"entered": bool},
   "q2": {registry id: {"mode": "bands" | "one" | "design", "entered": {"hi": bool, "lo": bool} | bool}}}
  The mode `design` gives each value of each band with the band id. Only the design tool uses it.

4 Order for one document (rule I5)
  stage 0  If the `Q0` head entered, its kind replaces the rule kind where rule I7 permits it.
  stage 1  The type reader of the rules runs. If it finds no type and the `Q1` tier entered, that tier gives the type.
           Where the rules give a type, a `Q1` class with a probability of 0.80 or more is compared with it.
           A difference gives the mark `q1_differs` in the key `detail`. The value does not change.
  stage 3  For each field that the cascade searches: a rule value of a tier that is not weak stays.
           The Apertus tier is called if the rules found no value, or if the rule value has a weak tier.
           An Apertus value replaces a weak rule value. The rule value then goes into the list `others`.

5 Extra keys of the result
  `kind_source` gets the keys `rule_kind`, `q0_class`, `q0_probability`, `used` and `replaced` (rule I7, item 13).
  If the `Q0` head replaces the kind, the keys `from` and `rule` name the head. The keys `s1_role`, `s1_rule_id`,
  `s1_export_condition` and `v5` of the rule chain stay.
  `heads` holds the answers to `Q0` and `Q1`, and for each `Q2` field why the tier was called and what it gave.
  The measurement tools do not read these keys.

Usage: this file has no command. The design tool `src/m11_value_heads2.py` calls it.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_values_base as vb  # noqa: E402
import m11_values_cascade as cvc  # noqa: E402  (not changed; only public names are used)

VERSION = "m11-values-combined-1"
ROOT = vb.ROOT
CALIBRATION_RULES = ROOT / "daten/gj_values/round4/calibration_dev_all.json"      # rule I5, items 10 and 11
ENTRY_FILE = ROOT / "daten/gj_values/heads2/entry.json"
Q2_FIELDS = ("affair_number", "title", "submission_date", "sponsor", "response_date", "responder")
MEASURE_ID = {"sponsor": "first_author", "responder": "responder_name"}
WEAK_BELOW = 0.5                      # rule I5, item 9 (the floor of the writer, decision W-3)
CLASS_MIN = 0.80                      # table 1: lowest class probability of a `Q1` value and of a `Q0` kind
KIND_OF_CLASS = {"A": "proposal", "B": "response", "C": "combined"}                # rule I7, items 9 and 10
CLASS_OF_KIND = {"proposal": "A", "response": "B", "combined": "C"}                # rule I7, item 3
NEVER_REPLACED = ("executive_proposal",)                                           # rule I7, item 11
Q1_TIER = "apertus_q1"
Q1_EVIDENCE = "answer of the model to question Q1 on the whole document"
BANDS = ("hi", "lo")
DESIGN_ENTRY_Q2 = {f: {"mode": "design", "entered": {"hi": True, "lo": True}} for f in Q2_FIELDS}


def q2_tier(field: str, band: str | None = None) -> str:
    """The tier id of a `Q2` value (rule I5, item 15)."""
    return f"apertus_q2_{field}" + (f"_{band}" if band else "")


def weak_tiers(calibration: dict | Path | str | None = None) -> dict:
    """{registry id: set of weak rule tiers} from the key `lookup` of a calibration file (rule I5, items 9, 10).
    A weak tier has a stored probability of all folds below 0.5. A tier with no entry is not weak."""
    if calibration is None:
        calibration = CALIBRATION_RULES
    if not isinstance(calibration, dict):
        calibration = json.loads(Path(calibration).read_text(encoding="utf-8"))
    lookup = calibration["lookup"]
    out = {}
    for f in vb.FIELDS:
        tiers = (lookup.get(MEASURE_ID.get(f, f)) or {}).get("tiers") or {}
        out[f] = {t for t, v in tiers.items() if v["p_all_folds"] < WEAK_BELOW}
    return out


def rule_class(kind: str | None) -> str | None:
    """The rule class of rule I7, items 3 and 4. None = no rule role."""
    if kind is None:
        return None
    return CLASS_OF_KIND.get(kind, "D")


def as_json(rec) -> dict:
    """A record of the heads output as a dict (an object of the base module, or a dict already)."""
    return rec if isinstance(rec, dict) else rec.to_json()


def not_searched_record(field: str, kind: str, sel: dict, others: list) -> dict:
    """The record of a field that the cascade does not search, in the form of the cascade reader."""
    return {"field": field, "found": False, "result": cvc.NOT_SEARCHED, "reason": "not_in_document_type",
            "detail": f"kind {kind}: {sel['note']} (cascade rules {', '.join(sel['rules'])})",
            "others": others, "cascade": dict(sel)}


def _addressee(doc: vb.Doc, strict: bool, registry: dict | None) -> list:
    res = vb.read_field(doc, "responder", strict, registry)
    cands = ([res] if res.found else []) + list(res.others)
    return [dict(c.to_json(False), kept_as="addressee of the proposal (rule V3); not a responder")
            for c in cands if c.tier in cvc.ADDRESSEE_TIERS]


def q1_record(value: str, probability: float, sel: dict) -> dict:
    """The type record of the `Q1` tier (rule I5, items 16 and 20 to 22): no page and no span."""
    return {"field": "affair_type", "found": True, "value": value, "normalised": value, "tier": Q1_TIER,
            "page": None, "block": None, "char_start": None, "char_end": None, "evidence": Q1_EVIDENCE,
            "detail": {"q1_probability": probability,
                       "limit": "a model answer on the whole document; not a span of the PDF"},
            "others": [], "cascade": dict(sel)}


def _stage0(rule_kind: str | None, q0: dict | None, entry: dict) -> tuple[str | None, dict]:
    info = {"rule_kind": rule_kind, "q0_class": None, "q0_probability": None, "q0_given": False,
            "q0_entered": bool((entry.get("q0") or {}).get("entered")), "used": "rule_chain", "replaced": False}
    if q0 is None:
        return rule_kind, info
    info.update(q0_class=q0["class"], q0_probability=q0["probability"],
                q0_given=bool(q0["probability"] >= CLASS_MIN))
    if not (info["q0_entered"] and info["q0_given"] and q0["class"] in KIND_OF_CLASS):
        return rule_kind, info                         # class D, or no given class, or the head did not enter
    if rule_kind in NEVER_REPLACED:
        return rule_kind, info
    kind = KIND_OF_CLASS[q0["class"]]
    info.update(used="q0_head", replaced=kind != rule_kind)
    return kind, info


def read_document_combined(doc: vb.Doc, heads_output: dict | None = None, entry: dict | None = None,
                           weak: dict | None = None, strict: bool = True, registry: dict | None = None,
                           rule_result: dict | None = None) -> dict:
    """The 7 records of a document by rule I5. `heads_output`: chapter 2 of the file header, or None.
    `entry`: the entry record (default: the file `entry.json`). `weak`: the result of `weak_tiers` (default: the
    calibration file of the reader with rules only). `rule_result`: the result of the cascade reader for this
    document with the kind of the rule chain, if the caller has it already. It is not changed."""
    if heads_output is None:
        return rule_result if rule_result is not None else cvc.read_document(doc, strict=strict, registry=registry)
    if entry is None:
        if not ENTRY_FILE.is_file():
            raise FileNotFoundError("daten/gj_values/heads2/entry.json does not exist: no entry decision was made")
        entry = json.loads(ENTRY_FILE.read_text(encoding="utf-8"))
    if weak is None:
        weak = weak_tiers()
    if rule_result is not None:                        # the kind and its source come from the same reader calls
        rule_kind, rule_source = rule_result["kind"], rule_result["kind_source"]
    else:
        rule_kind, rule_source = cvc.kind_of(doc, strict, registry)
    q0, q1 = heads_output.get("q0"), heads_output.get("q1")

    # stage 0
    kind, info = _stage0(rule_kind, q0, entry)
    if kind == rule_kind:
        base = rule_result if rule_result is not None else cvc.read_document(doc, strict=strict, registry=registry)
    else:
        base = cvc.read_document(doc, kind=kind, strict=strict, registry=registry)
    res = copy.deepcopy(base)
    if kind == rule_kind:
        res["kind_source"] = dict(res["kind_source"], **info)
    else:                                              # the facts of the rule chain and of rule V5 stay in the record
        res["kind_source"] = dict(copy.deepcopy(rule_source), **{"from": "Q0 head (rule I7)", "rule": "I7"}, **info)
    fields = res["fields"]
    heads = {"q0": q0, "q1": q1, "q1_used": False, "q1_differs": False, "q2": {}}

    # stage 1
    t = fields["affair_type"]
    q1_given = q1 is not None and q1["probability"] >= CLASS_MIN
    if t["found"]:
        if q1_given and q1["class"] != t["normalised"]:
            t["detail"] = dict(t.get("detail") or {}, q1_differs={"q1_class": q1["class"],
                                                                  "q1_probability": q1["probability"]})
            heads["q1_differs"] = True
    elif (entry.get("q1") or {}).get("entered") and q1_given and q1["class"] != "none":
        a_type = q1["class"]
        sel = cvc.selection(kind, a_type)
        for f in vb.FIELDS:
            was = fields[f]["cascade"]["searched"]
            if f == "affair_type":
                fields[f] = q1_record(a_type, q1["probability"], sel[f])
            elif sel[f]["searched"] and not was:
                fields[f] = dict(vb.read_field(doc, f, strict, registry).to_json(), cascade=dict(sel[f]))
            elif was and not sel[f]["searched"]:
                others = _addressee(doc, strict, registry) if (f == "responder" and kind in cvc.ADDRESSEE_KINDS) else []
                fields[f] = not_searched_record(f, kind, sel[f], others)
            else:
                fields[f]["cascade"] = dict(sel[f])
        res["affair_type_of_the_cascade"] = a_type
        heads["q1_used"] = True

    # stage 3
    q2 = heads_output.get("q2") or {}
    for f in Q2_FIELDS:
        rec = fields[f]
        if not rec["cascade"]["searched"]:
            continue                                   # rule I5, item 14
        is_weak = bool(rec["found"] and rec["tier"] in weak.get(f, ()))
        if rec["found"] and not is_weak:
            continue                                   # rule I5, item 7
        call = {"called_because": "weak_rule_tier" if is_weak else "rules_found_no_value", "gave": None}
        heads["q2"][f] = call
        if f not in q2:
            continue
        cand = as_json(q2[f])
        if not cand["found"]:
            call["gave"] = {"found": False, "reason": cand.get("reason"), "detail": cand.get("detail")}
            continue
        band = cand["detail"]["band"]
        e = (entry.get("q2") or {}).get(f) or {"mode": "none"}
        if e["mode"] == "design":
            tier = q2_tier(f, band)
        elif e["mode"] == "bands":
            tier = q2_tier(f, band) if e["entered"].get(band) else None
        elif e["mode"] == "one":
            tier = q2_tier(f) if e["entered"] else None
        else:
            tier = None
        call["gave"] = {"found": True, "band": band, "tier": tier, "head_probability": cand["detail"]["head_probability"]}
        if tier is None:
            continue                                   # the tier, or the band, did not enter: the rule result stays
        new = {k: v for k, v in cand.items() if k not in ("others", "cascade")}
        new["tier"] = tier
        others = list(rec.get("others") or [])
        if is_weak:                                    # rule I5, item 12
            others = [{k: v for k, v in rec.items() if k not in ("others", "cascade")}] + others
        new["others"] = others
        new["cascade"] = rec["cascade"]
        fields[f] = new
    res["heads"] = heads
    return res

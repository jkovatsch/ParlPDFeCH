# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""Measurement and calibration of the eCH-0295 values that are read from the PDF (plan-ech-from-pdf.md, task <id>).

Rules: crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md, VERSION 2, rules G3 to G7.
This is the first tool. The second calculation is src/m11_second_calc.py (a different author).

Commands
  open    measures and calibration of the open part (5 folds grouped by parliament).
  closed  measures of the closed part. It stops unless the opening file exists (daten/gj_values/opening.json).
          It uses the calibration file of the command `open` (the counts of all 5 folds); it fits nothing.

Inputs
  values file     ONE form (chapter 5.4): {"documents": {doc_id: {"language": .., "s1_role": .., "fields": {..}}}}.
                  `fields` has one record for each of the 7 registry ids: affair_type, title, affair_number,
                  submission_date, response_date, responder (= responder_name), sponsor (= first_author).
                  A record is ValueCandidate.to_json() or NotFound.to_json() of src/m11_values_base.py.
                  Keys used: found, normalised, tier, value (information count only) and reason (count of the
                  records with the reason reader_error). More keys at the top of the file are permitted.
                  The file of a part holds the documents of that part only, and each of them.
  reference file  the output of src/m11_value_reference.py (reference_open.json or reference_closed.json):
                  {"documents": {doc_id: {"language", "s1_role", "fields": {field: {"values": [normal forms],
                  "raw": [..]}}}}}. An empty list = no reference. An empty normal form in the list is no reference
                  value (chapter 4.9). Optional key "printed" of an entry (chapter 5.2, item 6).
  folds file      daten/gj_values/folds.json (src/m11_value_folds.py): parliament, part and fold of each document.
  opening file    daten/gj_values/opening.json (chapter 6.5). One accepted form:
                  {"time": "..", "files": {"src/m11_values_type_number.py": "<SHA-256>", .. 6 files ..}}.
                  The tool finds a SHA-256 by the path or the file name at each depth of the object.
  second file     optional; the output of the second calculation: lists `cells` and `pairs` with the keys
                  field, part, base, dimension, level and counts (rule G7, condition 1).

The run STOPS and writes no file (chapters 5.1 and 5.4) if
  an id of the values file or of the reference file is not in the folds file,
  a file holds a record of the other part,
  a document of the part has no record, or one of the 7 fields of a document has no record,
  the key `fields` is absent (no other name is accepted) or it has a key that is no registry id,
  a record with a value has no string `normalised` that is not empty, or no tier id [a-z][a-z0-9_]{1,39},
  the language or the S1 rule role of a values record differs from the copy in the reference record,
  the opening file exists and does not hold the SHA-256 of each of the 6 files.
The tool tests each document id against the folds file BEFORE it reads the record of the document.

Comparison (chapter 4.8): the compared string is the key `normalised`, for each of the 7 fields. The tool calls
src/m11_value_norm.py: compare(field, string, normal forms of the reference). It uses no normal form, key or class
of a rule module (no key below `detail`). For the title, the affair number, the responder and the first author it
also calculates the outcome with the key `value` and gives the count of the documents where the two outcomes
differ (information; not in condition 1).

Cells (list `cells` of the measures file; each cell has field, part, base, dimension, level, counts):
  base       primary = the primary set of the field (rule G1); all = all documents of the part (information).
  dimension  none (level all; both bases), language (de, fr, it, other; both bases), role (6 roles and none; both
             bases), fold (open part, base primary, folds 0 to 4), number_class (affair number, base primary:
             documents with one or more reference values that match [0-9]{1,4} on the stripped export string).
Pairs (list `pairs`): dimension tier, base primary; units = given values of the tier with the outcome equal or
different in the primary set.
Rule G7 condition 1 (chapter 8, item 2) compares the 4 outcome counts of each cell of the two bases (dimensions
none, language, role), of the fold cells and of the cell number_class, and the units equal and different of each
pair. An absent cell is a cell with 0 in each count.

Rounding (chapter 5.5): counts are whole numbers. A file holds a measure, a bound or a probability with 6
decimals. Each comparison with a limit uses the value before the rounding. Precision >= 0.95 is 20e >= 19(e + d);
coverage >= 0.50 is 2 x (units with p >= a) >= units.

Each measures file holds the SHA-256 of the values file, of folds.json, of the addendum and of the 6 files of the
opening. If the opening file exists and one of the 6 values differs, the tool writes the mark "after the opening".

Reused by import from the frozen file src/m10_calibrate.py: jeffreys_mean, jeffreys_interval, bootstrap_draws,
clip, as_written, bin_index, ece_equal_width, ece_equal_mass, reliability_table, cal_id, r6, sha256, rel,
read_json, write_json, A_GRID.
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_calibrate as cal  # noqa: E402  (frozen file: import only)

VERSION = "m11-value-cal-2"
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
OUT_DIR = ROOT / "daten/gj_values"
FOLDS_FILE = OUT_DIR / "folds.json"
OPENING_FILE = OUT_DIR / "opening.json"
ADDENDUM = ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md"
ADDENDUM_VERSION = "addendum G, version 2 (13.10.2026)"
STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
REFERENCE = "OpenParlData export (official register value; no human of the project examined it; addendum G, rule G2)"

FIELDS = ("affair_type", "title", "affair_number", "submission_date", "response_date", "responder_name",
          "first_author")
# chapter 5.4, items 6 and 7: the 7 registry ids of the values file and their field ids
REGISTRY_IDS = ("affair_type", "title", "affair_number", "submission_date", "response_date", "responder", "sponsor")
FIELD_OF = dict(zip(REGISTRY_IDS, FIELDS))
REGISTRY_OF = dict(zip(FIELDS, REGISTRY_IDS))
FIELD_ALIAS = {"responder": "responder_name", "sponsor": "first_author"}
ECH_SLOT = {"affair_type": "Affair.affair_type", "title": "Affair.title", "affair_number": "Affair.affair_number",
            "submission_date": "Submission.submission_date", "response_date": "ResponseStep.date_end_actual",
            "responder_name": "ResponseStep.responder.name", "first_author": "Submission.sponsorship (role sponsor)"}
RESPONSE_FIELDS = ("response_date", "responder_name")
PRIMARY_ROLES = ("response", "combined")
DATE_FIELDS = ("submission_date", "response_date")
VALUE_KEY_FIELDS = ("title", "affair_number", "responder_name", "first_author")     # chapter 4.8, item 12
LANGUAGES = ("de", "fr", "it", "other")
ROLES = ("proposal", "response", "combined", "committee", "minutes", "other", "none")
TIER_RX = re.compile(r"[a-z][a-z0-9_]{1,39}")      # chapter 5.4, item 11 (the whole string must match)
SHA_RX = re.compile(r"[0-9a-f]{64}")
MIN_UNITS = 30              # rule G6 item 14, rule G7 item 4
MIN_PARLIAMENT_VALUES = 10  # chapter 5.2 item 5
OUTCOMES = ("equal", "different", "not_found", "no_reference")
EQ, DIFF, NF, NR_GIVEN, NR_NONE = 0, 1, 2, 3, 4
OUTCOME_NAME = ("equal", "different", "not_found", "no_reference", "no_reference")
# chapter 6.5, items 3 and 4: the 6 files of the opening
OPENING_SIX = ("src/m11_values_type_number.py", "src/m11_values_title.py", "src/m11_values_dates_responder.py",
               "src/m11_values_sponsor.py", "src/m11_values_base.py", "src/m11_value_norm.py")
MARK = "after the opening"
JEFFREYS_NOTE = "Jeffreys interval (5 % and 95 %); it does not include the effect of the parliaments"
BOOT_NOTE = ("bootstrap by parliament, 2,000 draws, numpy.random.default_rng(20261013) made again for each cell, "
             "parliaments with one or more documents in the cell sorted by key, 5 % and 95 % quantiles of the used "
             "draws (addendum G, chapter 5.3)")


class Refused(Exception):
    """The run is not permitted or an input has a wrong form. No file is written."""


def load_norm():
    """The normalisation file of addendum G. No other normalisation exists in this tool."""
    mod = importlib.import_module("m11_value_norm")
    for name in ("compare", "norm", "number_is_short_digits"):
        if not callable(getattr(mod, name, None)):
            raise Refused(f"src/m11_value_norm.py has no function {name}()")
    return mod


# ------------------------------------------------------------------ inputs
def load_folds(path: Path) -> dict:
    data = cal.read_json(path)
    docs = {str(d): {"parliament": str(v["parliament"]), "part": v["part"],
                     "fold": None if v.get("fold") is None else str(v["fold"])}
            for d, v in data["documents"].items()}
    for d, v in docs.items():
        if v["part"] not in ("open", "closed") or (v["part"] == "open") != (v["fold"] is not None):
            raise Refused(f"folds file: document {d} has a wrong part or fold")
    by_parl = defaultdict(set)
    for v in docs.values():
        by_parl[v["parliament"]].add((v["part"], v["fold"]))
    if any(len(s) != 1 for s in by_parl.values()):
        raise Refused("folds file: a parliament is in two parts or two folds")
    return docs


def documents_of(data, folds: dict, part: str, what: str) -> dict:
    """The key `documents` of a file of one part. The ids are tested before a record is read (chapter 5.4, items 3
    and 14): an id that is not in the folds file, a record of the other part and an absent document stop the run."""
    if not isinstance(data, dict) or not isinstance(data.get("documents"), dict):
        raise Refused(f"{what}: the file must be one JSON object with the key documents (an object); no other form "
                      "is permitted (addendum G, chapter 5.4)")
    ids = [str(d) for d in data["documents"]]
    unknown = sorted(d for d in ids if d not in folds)
    if unknown:
        raise Refused(f"{what}: {len(unknown)} ids are not in the folds file (first: {unknown[:3]})")
    other = sum(1 for d in ids if folds[d]["part"] != part)
    if other:
        raise Refused(f"{what}: {other} records are of the other part; the file of the part {part} must hold the "
                      "documents of that part only (chapter 5.4, item 14). No record was read.")
    have = set(ids)
    absent = sum(1 for d, v in folds.items() if v["part"] == part and d not in have)
    if absent:
        raise Refused(f"{what}: {absent} documents of the part {part} have no record (chapter 5.1, item 6)")
    return {str(d): v for d, v in data["documents"].items()}


def language_cell(lang) -> str:
    return lang if lang in ("de", "fr", "it") else "other"


def role_cell(role) -> str:
    return "none" if role is None else role


def record_problem(rec) -> str | None:
    """Chapter 5.4, items 8, 9 and 11: the cause why a record stops the run (None = the record is accepted)."""
    if not isinstance(rec, dict) or not isinstance(rec.get("found"), bool):
        return "record_is_no_object_with_the_key_found_true_or_false"
    if not rec["found"]:
        return None
    if not isinstance(rec.get("normalised"), str) or rec["normalised"] == "":
        return "value_record_with_no_string_normalised_that_is_not_empty"
    if not isinstance(rec.get("tier"), str) or not TIER_RX.fullmatch(rec["tier"]):
        return "value_record_with_no_tier_id_of_the_form"
    return None


def reference_forms(norm, entry) -> tuple[list, bool | None, bool]:
    """(normal forms of the reference, printed flag, cell number_class). An empty list = no reference.
    A normal form that is empty is no reference value (chapter 4.9, item 3). The flag of the cell number_class is
    made from the stripped export strings of the used reference values (chapter 3.3, item 8); the flag
    short_digits_only of the reference file is not used."""
    raw = [r for r in entry.get("raw") or [] if isinstance(r, dict) and r.get("used")]
    small = any(norm.number_is_short_digits(r.get("value")) for r in raw if isinstance(r.get("value"), str))
    forms = [v for v in entry["values"] if v not in (None, "", [])]
    return forms, entry.get("printed"), bool(small and forms)


def outcome_of(norm, field: str, cand: dict, refs: list) -> dict:
    """The outcome of one document and one field (chapter 5.1) with the second counts of rule G3.
    The compared string is the key `normalised` (chapter 4.8, item 4). `code_value` is the outcome with the key
    `value` for the 4 fields of chapter 4.8, item 12 (information)."""
    problem = record_problem(cand)
    if problem:
        raise Refused(f"field {field}: {problem} (addendum G, chapter 5.4, item 11)")
    given = cand["found"]
    out = {"given": given, "tier": cand["tier"] if given else None, "within": False, "exact": False,
           "bad_day": False, "reader_error": bool(not given and cand.get("reason") == "reader_error")}
    if not refs:
        out["code"] = NR_GIVEN if given else NR_NONE
    elif not given:
        out["code"] = NF
    else:
        res = norm.compare(field, cand["normalised"], refs)
        out["code"] = EQ if res["equal"] else DIFF   # a string with no normal form is different (chapters 4.6, 4.9)
        out["exact"] = bool(res.get("exact"))
        out["within"] = bool(res.get("within_7_days"))
        out["bad_day"] = field in DATE_FIELDS and not res.get("reader_is_a_day", True)
    out["code_value"] = out["code"]
    if given and refs and field in VALUE_KEY_FIELDS:
        v = cand.get("value")
        out["code_value"] = EQ if (isinstance(v, str) and norm.compare(field, v, refs)["equal"]) else DIFF
    return out


def build_units(norm, values: dict, reference: dict, folds: dict, part: str) -> tuple[dict, dict]:
    """{field: list of unit records} of the part, and the record of the input counts. The form of each record is
    examined first; one or more wrong records stop the run before an outcome is calculated."""
    ids = sorted(values)
    problems, first = Counter(), {}

    def note(kind: str, d: str) -> None:
        problems[kind] += 1
        first.setdefault(kind, d)
    for d in ids:
        rec, ref_doc = values[d], reference[d]
        if not isinstance(ref_doc, dict) or not isinstance(ref_doc.get("fields"), dict) or any(
                not isinstance(ref_doc["fields"].get(f), dict) or not isinstance(ref_doc["fields"][f].get("values"), list)
                for f in FIELDS):
            note("reference_record_with_no_entry_for_each_of_the_7_fields", d)
            continue
        if not isinstance(rec, dict) or any(k not in rec for k in ("language", "s1_role", "fields")):
            note("values_record_with_no_key_language_s1_role_or_fields", d)
            continue
        if not isinstance(rec["fields"], dict):
            note("values_record_fields_is_no_object", d)
            continue
        if rec["s1_role"] is not None and rec["s1_role"] not in ROLES[:-1]:
            note("s1_role_is_no_rule_role", d)
        for k in ("language", "s1_role"):
            if k not in ref_doc or rec[k] != ref_doc[k]:
                note(f"{k}_differs_from_the_stored_value_in_the_reference_record", d)
        for k in rec["fields"]:
            if k not in REGISTRY_IDS:
                note("fields_key_that_is_no_registry_id", d)
        for k in REGISTRY_IDS:
            if k not in rec["fields"] or rec["fields"][k] is None:
                note("field_with_no_record", d)
            elif record_problem(rec["fields"][k]):
                note(record_problem(rec["fields"][k]), d)
    if problems:
        where = "" if part == "closed" else "; first document of each cause: " + ", ".join(
            f"{k} {first[k]}" for k in sorted(first))
        raise Refused(f"values file of the part {part}: {sum(problems.values())} errors of the input "
                      f"({dict(sorted(problems.items()))}){where}. No measures file is written "
                      "(addendum G, chapters 5.1 and 5.4).")
    units = {f: [] for f in FIELDS}
    for d in ids:
        rec, ref_doc, fold = values[d], reference[d], folds[d]
        role, lang = role_cell(rec["s1_role"]), language_cell(rec["language"])
        for f in FIELDS:
            refs, printed, small = reference_forms(norm, ref_doc["fields"][f])
            u = outcome_of(norm, f, rec["fields"][REGISTRY_OF[f]], refs)
            u.update(doc=d, parliament=fold["parliament"], fold=fold["fold"], role=role, printed=printed,
                     language=lang, small=small and f == "affair_number",
                     primary=(role in PRIMARY_ROLES) if f in RESPONSE_FIELDS else True)
            units[f].append(u)
    info = {"documents_of_the_part_in_folds_file": sum(1 for v in folds.values() if v["part"] == part),
            "documents_in_values_file": len(values), "documents_in_reference_file": len(reference),
            "records_of_the_other_part": 0, "documents_with_no_record": 0, "fields_with_no_record": 0,
            "records_with_the_reason_reader_error": {f: sum(1 for u in units[f] if u["reader_error"]) for f in FIELDS}}
    return units, info


# ------------------------------------------------------------------ measures (rule G4)
def ratio(a: int, b: int):
    return cal.r6(a / b) if b else None


def jeffreys(k: int, n: int):
    """Chapter 5.3, item 11: 5 % and 95 % quantile of Beta(k + 0.5, n - k + 0.5); n = 0 gives no interval."""
    if not n:
        return None
    lo, hi = cal.jeffreys_interval(k, n)
    return [cal.r6(lo), cal.r6(hi)]


def cell(units: list[dict], field: str, ident: dict, bootstrap: bool = False) -> dict:
    """Counts and measures of one cell (chapters 5.2 and 5.5), with the Jeffreys intervals and, for a cell of the
    dimension none, the bootstrap by parliament."""
    c = Counter(u["code"] for u in units)
    e, d, m = c[EQ], c[DIFF], c[NF]
    n_ref = e + d + m
    counts = {"documents": len(units), "n_ref": n_ref, "equal": e, "different": d, "not_found": m,
              "no_reference": c[NR_GIVEN] + c[NR_NONE], "no_reference_value_given": c[NR_GIVEN],
              "no_reference_no_value": c[NR_NONE]}
    if field == "title":
        counts["equal_exact_form"] = sum(1 for u in units if u["code"] == EQ and u["exact"])
    if field in DATE_FIELDS:
        counts["within_7_days"] = sum(1 for u in units if u["code"] == EQ or (u["code"] == DIFF and u["within"]))
        counts["reader_string_is_no_day"] = sum(1 for u in units if u["code"] == DIFF and u["bad_day"])
    out = {"field": field} | ident | {
        "counts": counts, "coverage": ratio(e + d, n_ref), "precision": ratio(e, e + d), "recall": ratio(e, n_ref),
        # chapter 5.3 item 11: coverage k = e + d, n = n_ref; precision k = e, n = e + d; recall k = e, n = n_ref
        "jeffreys": {"coverage": jeffreys(e + d, n_ref), "precision": jeffreys(e, e + d),
                     "recall": jeffreys(e, n_ref), "remark": JEFFREYS_NOTE}}
    if bootstrap:
        out["bootstrap_by_parliament"] = parliament_bootstrap(units)
        out["parliaments_with_10_given"] = parliament_information(units)
        out["reference_printed"] = presence_information(units)
    return out


def parliament_bootstrap(units: list[dict]) -> dict:
    """Chapter 5.3, items 6 to 10. P = the parliaments with one or more documents in the cell (a parliament with no
    reference in the cell is in P). The call of the generator is made again for each cell; the 3 measures of the
    cell use the same draws. A draw with a divisor of 0 is not used for that measure only."""
    keys = sorted({u["parliament"] for u in units})
    if not keys:
        return {"parliaments": 0, "method": BOOT_NOTE}
    pos = {k: i for i, k in enumerate(keys)}
    mat = np.zeros((len(keys), 3), dtype=np.int64)
    for u in units:
        if u["code"] in (EQ, DIFF, NF):
            mat[pos[u["parliament"]], u["code"]] += 1
    draws = cal.bootstrap_draws(len(keys))       # numpy.random.default_rng(20261013).integers(0, P, size=(2000, P))
    s = mat[draws].sum(axis=1)
    e, d, m = s[:, EQ].astype(float), s[:, DIFF].astype(float), s[:, NF].astype(float)
    out = {"parliaments": len(keys), "draws": int(len(draws)), "method": BOOT_NOTE}
    for name, num, den in (("coverage", e + d, e + d + m), ("precision", e, e + d), ("recall", e, e + d + m)):
        ok = den > 0
        vals = num[ok] / den[ok]
        out[name] = {"low": cal.r6(np.quantile(vals, 0.05)) if len(vals) else None,
                     "high": cal.r6(np.quantile(vals, 0.95)) if len(vals) else None, "draws_used": int(ok.sum())}
    return out


def parliament_information(units: list[dict]) -> dict:
    """Chapter 5.2, item 5: a parliament counts if its sum e + d in the cell is 10 or more. The median of an even
    number of values is the mean of the two middle values."""
    by = defaultdict(lambda: [0, 0])
    for u in units:
        if u["code"] in (EQ, DIFF):
            by[u["parliament"]][0] += u["code"] == EQ
            by[u["parliament"]][1] += 1
    vals = sorted(k / n for k, n in by.values() if n >= MIN_PARLIAMENT_VALUES)
    median = None
    if vals:
        h = len(vals) // 2
        median = vals[h] if len(vals) % 2 else (vals[h - 1] + vals[h]) / 2
    return {"count": len(vals), "lowest_precision": cal.r6(vals[0]) if vals else None,
            "median_precision": cal.r6(median)}


def presence_information(units: list[dict]) -> dict | None:
    """Plan chapter 4.3: measures on the documents where the reference stands in the PDF (key `printed`)."""
    known = [u for u in units if u["printed"] is not None and u["code"] in (EQ, DIFF, NF)]
    if not known:
        return None
    printed = [u for u in known if u["printed"]]
    nf = [u for u in known if u["code"] == NF]
    e = sum(1 for u in printed if u["code"] == EQ)
    return {"documents_with_the_flag": len(known), "printed": len(printed), "printed_and_equal": e,
            "recall_on_printed": ratio(e, len(printed)), "no_value": len(nf),
            "no_value_and_not_printed": sum(1 for u in nf if not u["printed"]),
            "share_of_no_value_where_not_printed": ratio(sum(1 for u in nf if not u["printed"]), len(nf)),
            "remark": "information; not part of the second calculation (addendum G, chapter 5.2 item 7)"}


def value_key_information(units: list[dict]) -> dict:
    """Chapter 4.8, items 12 to 14: the count of the documents where the outcome with the key `value` differs from
    the outcome with the key `normalised`. Information; not a part of condition 1."""
    def count(sel):
        a = sum(1 for u in sel if u["code"] == EQ and u["code_value"] == DIFF)
        b = sum(1 for u in sel if u["code"] == DIFF and u["code_value"] == EQ)
        return {"documents_where_the_two_outcomes_differ": a + b, "normalised_equal_and_value_different": a,
                "normalised_different_and_value_equal": b,
                "equal_with_the_key_value": sum(1 for u in sel if u["code_value"] == EQ),
                "different_with_the_key_value": sum(1 for u in sel if u["code_value"] == DIFF)}
    return {"all_documents_of_the_part": count(units), "primary_set": count([u for u in units if u["primary"]]),
            "remark": "information (addendum G, chapter 4.8, items 12 to 14); it changes no outcome"}


def field_cells(units: list[dict], field: str, part: str, fold_keys: list[str]) -> tuple[list[dict], list[dict], dict]:
    """(cells, pairs, information of the field)."""
    cells, pairs = [], []
    prim = [u for u in units if u["primary"]]
    for base, sel in (("primary", prim), ("all", units)):
        ident = {"part": part, "base": base}
        cells.append(cell(sel, field, ident | {"dimension": "none", "level": "all"}, bootstrap=True))
        for k in LANGUAGES:
            cells.append(cell([u for u in sel if u["language"] == k], field, ident | {"dimension": "language", "level": k}))
        for k in ROLES:
            cells.append(cell([u for u in sel if u["role"] == k], field, ident | {"dimension": "role", "level": k}))
    if field == "affair_number":
        cells.append(cell([u for u in prim if u["small"]], field,
                          {"part": part, "base": "primary", "dimension": "number_class", "level": "digits_1_to_4"}))
    info = {"ech_slot": ECH_SLOT[field],
            "primary_set": "S1 rule role response or combined" if field in RESPONSE_FIELDS else "all documents",
            "records_with_the_reason_reader_error": {"all_documents_of_the_part": sum(1 for u in units if u["reader_error"]),
                                                     "primary_set": sum(1 for u in prim if u["reader_error"])}}
    if field in VALUE_KEY_FIELDS:
        info["outcome_with_the_key_value"] = value_key_information(units)
    if part == "open":
        fc = [cell([u for u in prim if u["fold"] == f], field,
                   {"part": part, "base": "primary", "dimension": "fold", "level": f}) for f in fold_keys]
        cells += fc
        names = ("documents", "equal", "different", "not_found", "no_reference")
        info["fold_sums_equal_totals"] = all(sum(c["counts"][k] for c in fc) == cells[0]["counts"][k] for k in names)
        pr = [c["precision"] for c in fc if c["precision"] is not None]
        info["fold_precision_lowest_highest"] = [min(pr), max(pr)] if pr else None
    for t in sorted({u["tier"] for u in units if u["given"]}):
        tu = [u for u in prim if u["tier"] == t]
        k, n = sum(1 for u in tu if u["code"] == EQ), sum(1 for u in tu if u["code"] in (EQ, DIFF))
        pairs.append({"field": field, "tier": t, "part": part, "base": "primary", "dimension": "tier", "level": t,
                      "counts": {"units": n, "equal": k, "different": n - k}, "precision": ratio(k, n),
                      "jeffreys": {"precision": jeffreys(k, n), "remark": JEFFREYS_NOTE},
                      "values_given": {"primary_set": len(tu),
                                       "primary_no_reference": sum(1 for u in tu if u["code"] == NR_GIVEN),
                                       "outside_primary_set": sum(1 for u in units if u["tier"] == t and not u["primary"])}})
    return cells, pairs, info


def cell_key(c: dict) -> tuple:
    """(field, part, base, dimension, level). The dimensions none and number_class have one cell: their level is
    not a part of the key."""
    dim = c.get("dimension", "none")
    # <id> (13.10.2026): the second calculation names the level of a cell with the key `class` (the word of chapter
    # 5.5, items 5 and 6). Before this change its language and role cells all got the level "all" here.
    level = c.get("level", c.get("class", c.get("tier", "all")))
    if dim in ("none", "number_class"):
        level = "all"
    return (FIELD_ALIAS.get(c.get("field"), c.get("field")), c.get("part", "open"), c.get("base", "primary"),
            dim, str(level))


def find_cell(items: list[dict], *key) -> dict | None:
    """One cell or pair of a list by (field, part, base, dimension, level)."""
    key = cell_key(dict(zip(("field", "part", "base", "dimension", "level"), key)))
    return next((c for c in items if cell_key(c) == key), None)


# ------------------------------------------------------------------ calibration (rule G6)
def p_of(k: int, n: int) -> float:
    """Jeffreys posterior mean (k + 0.5) / (n + 1) in double precision, clipped to 0.005 .. 0.995 (rule G6 items 4
    and 5; chapter 5.5, item 18). 0 of 0 gives 0.5."""
    return float(cal.clip(cal.jeffreys_mean(k, n)))


def certain_tier(k: int, n: int) -> bool:
    """Rule G7 item 4: 30 or more units and a precision of 0.95 or more: 20 x e >= 19 x (e + d)."""
    return n >= MIN_UNITS and 20 * k >= 19 * n


def threshold_rule(p, equal, grid=cal.A_GRID) -> dict:
    """Rule G6 items 10 to 13 and 19: the smallest a of the grid with an accuracy of 0.95 or more and a coverage
    of 0.50 or more on the units with p >= a. Whole-number comparisons (chapter 5.5, item 17). p is the clipped
    fold value with no rounding. No unit with p >= a: the condition is not met."""
    p, equal = np.asarray(p, dtype=float), np.asarray(equal, dtype=bool)
    n = len(p)
    rows, chosen = [], None
    for a in grid:
        m = p >= a
        cnt, eq = int(m.sum()), int(equal[m].sum())
        meets = bool(cnt > 0 and 20 * eq >= 19 * cnt and 2 * cnt >= n)
        rows.append({"a": a, "n": cnt, "equal": eq, "coverage": ratio(cnt, n), "accuracy": ratio(eq, cnt), "meets": meets})
        if meets and chosen is None:
            chosen = a
    return {"a": chosen, "n": n, "grid": rows,
            "rule": "smallest a with 20 x equal >= 19 x n and 2 x n >= units (accuracy >= 0.95, coverage >= 0.50; "
                    "criteria 8.6; addendum G, rule G6 items 10 to 13 and 19)"}


def tier_record(k: int, n: int, by_fold: dict, fold_keys: list[str]) -> dict:
    return {"k": k, "n": n, "precision": ratio(k, n), "precision_jeffreys": jeffreys(k, n),
            "p_all_folds": p_of(k, n),
            "p_without_fold": {f: p_of(k - by_fold[f]["k"], n - by_fold[f]["n"]) for f in fold_keys},
            "by_fold": {f: dict(by_fold[f]) for f in fold_keys},
            "enough_units": n >= MIN_UNITS, "certain_tier": certain_tier(k, n)}


def fit_field(units: list[dict], fold_keys: list[str]) -> dict:
    """Pair counts, fold values, threshold a and tier status of one field from the units of the open part."""
    fit_units = [u for u in units if u["primary"] and u["code"] in (EQ, DIFF)]
    kn = defaultdict(lambda: {f: {"k": 0, "n": 0} for f in fold_keys})
    for u in fit_units:
        kn[u["tier"]][u["fold"]]["k"] += int(u["code"] == EQ)
        kn[u["tier"]][u["fold"]]["n"] += 1
    for u in units:
        if u["given"]:
            kn[u["tier"]]                 # a tier with no unit gets a record too (n = 0, probability 0.5)
    tiers = {t: tier_record(sum(v["k"] for v in bf.values()), sum(v["n"] for v in bf.values()), bf, fold_keys)
             for t, bf in sorted(kn.items())}
    p = np.array([tiers[u["tier"]]["p_without_fold"][u["fold"]] for u in fit_units], dtype=float)
    ok = np.array([u["code"] == EQ for u in fit_units], dtype=bool)
    thr = threshold_rule(p, ok)
    quality = quality_of(p, ok, "fold values (the counts of the 4 other folds), clipped, no rounding")
    return {"units": len(fit_units), "threshold": thr, "a": thr["a"], "tiers": tiers, "quality": quality,
            "certain_tiers": sorted(t for t, v in tiers.items() if v["certain_tier"])}


def status_of(p: float, tier: str | None, fit: dict, primary: bool, entry: str) -> str:
    """Rule G6 items 9 and 13 to 16 and 20 with rule G7 items 7 and 8. p is the clipped value with no rounding."""
    t = fit["tiers"].get(tier)
    if entry != "written_with_status" or not primary or fit["a"] is None or t is None:
        return "unsure"
    return "certain" if (p >= fit["a"] and t["enough_units"] and t["certain_tier"]) else "unsure"


def second_counts(c: dict | None, names) -> dict:
    """The compared counts of a cell or a pair. An absent cell is a cell with 0 in each count (5.5, item 13)."""
    c = (c or {}).get("counts", c or {})
    out = {}
    for o in names:
        if o == "no_reference" and "no_reference" not in c:
            out[o] = int(c.get("no_reference_value_given", 0)) + int(c.get("no_reference_no_value", 0))
        else:
            out[o] = int(c.get(o, 0))
    return out


def compared(key: tuple) -> bool:
    """Chapter 8, item 2: the cells and pairs of condition 1."""
    _, part, base, dim, _ = key
    if dim in ("none", "language", "role"):
        return base in ("primary", "all")
    if dim == "fold":
        return base == "primary" and part == "open"
    return dim in ("number_class", "tier") and base == "primary"


def compare_second(cells: list[dict], pairs: list[dict], second: dict | None, field: str, part: str) -> dict:
    """Rule G7 condition 1 (chapter 8, item 2): the same 4 outcome counts in each cell of the two bases (dimensions
    none, language, role), in the fold cells and in the cell number_class, and the same units equal and different
    in each pair. Chapter 3.5, item 10 (the stored affair type) is a part of condition 1: this tool takes the type
    reference from the reference file, so a difference of the two sources is a difference of the counts here."""
    if second is None:
        return {"exists": False, "equal": None, "cells": 0, "differences": [], "number_of_differences": 0}
    if not isinstance(second.get("cells"), list) or not isinstance(second.get("pairs"), list):
        raise Refused("second file: the lists cells and pairs are absent")

    def table(items):
        out = {}
        for c in items:
            k = cell_key(c)
            if k[0] == field and k[1] == part and compared(k):
                out[k] = c
        return out
    mine, other = table(cells + pairs), table(second["cells"] + second["pairs"])
    diff, n, by_group = [], 0, Counter()
    for k in sorted(set(mine) | set(other)):
        names = ("equal", "different") if k[3] == "tier" else OUTCOMES
        a, b = second_counts(mine.get(k), names), second_counts(other.get(k), names)
        n += 1
        by_group[f"{k[2]}/{k[3]}"] += 1
        if a != b:
            diff.append({"cell": list(k), "names": list(names),      # lists: no second cell form in this record
                         "this_tool": [a[o] for o in names] if k in mine else None,
                         "second_calculation": [b[o] for o in names] if k in other else None})
    here = bool(other)
    return {"exists": here, "equal": (not diff) if here else None, "cells": n, "cells_by_base_and_dimension": dict(by_group),
            "differences": diff[:50], "number_of_differences": len(diff),
            "rule": "addendum G, chapter 8, item 2: the two bases, the fold cells, the cell number_class, the pairs"}


def entry_of(fit: dict, second: dict) -> dict:
    """Rule G7: the entry of a field into the record."""
    c1, c2 = bool(second["exists"] and second["equal"]), bool(fit["certain_tiers"])
    entry = "left_out_not_measured" if not c1 else ("written_with_status" if c2 else "written_all_unsure")
    return {"condition_1_second_calculation_equal": c1, "condition_2_certain_tier": c2, "entry": entry,
            "entry_if_condition_1_is_met": "written_with_status" if c2 else "written_all_unsure",
            "second_calculation": second}


def calibration_records(field: str, fit: dict, fit_file: dict, fold_keys: list[str], entry: str) -> dict:
    """One record of the class Calibration (label schema 0.2.0) for each pair. The writer adds global_uri and
    calibrated_slot (the IRI of the slot)."""
    out = {}
    q = fit["quality"] or {}
    for t, v in fit["tiers"].items():
        cid = cal.cal_id("value", field, t)
        params = [("jeffreys_mean_all_folds", v["p_all_folds"]), ("k", v["k"]), ("n", v["n"])]
        params += [(f"jeffreys_mean_without_fold_{f}", v["p_without_fold"][f]) for f in fold_keys]
        rec = {"calibration_method": "jeffreys_tier_precision", "calibrated_kind": "pdf_value",
               "calibrated_tier": t, "fit_set_file": fit_file["path"], "fit_set_digest": fit_file["sha256"],
               "fit_n": int(v["n"]), "reference_source": REFERENCE, "in_sample": False,
               "target_status": "not_measured",
               "calibration_parameters": [{"parameter_name": k, "parameter_value": cal.r6(x)} for k, x in params],
               "measure_sets": [{"set_name": f"dev, open part, fold values, all tiers of the field {field}",
                                 "set_n": int(q.get("units", 0)), "ece": q.get("calibration_error"),
                                 "ece_equal_mass": q.get("ece_equal_mass"), "brier": q.get("brier"),
                                 "interval_method": "no interval"}],
               "calibration_note": ("Jeffreys mean of the pair (field, tier) against the export, clipped. A document "
                                    "of fold f gets the value without fold f. Other documents get the value of all "
                                    f"folds. Tier: {v['n']} units, certain tier: {str(v['certain_tier']).lower()}. "
                                    f"Entry of the field: {entry}.")}
        if entry == "written_with_status" and fit["a"] is not None and v["certain_tier"]:
            rec["certain_threshold"] = fit["a"]
        out[cid] = rec
    return out


def document_values(units: dict, fits: dict, entries: dict, part: str) -> dict:
    """{doc: {field: probability, value status, calibration id, outcome}} of each given value. The value status is
    decided with the probability before the rounding (chapter 5.5, items 16 to 19)."""
    docs = defaultdict(dict)
    for f, us in units.items():
        fit, entry = fits[f], entries[f]["entry"]
        for u in us:
            if not u["given"]:
                continue
            t = fit["tiers"].get(u["tier"])
            if t is None:
                p, cid = p_of(0, 0), None
            else:
                p = t["p_without_fold"][u["fold"]] if part == "open" else t["p_all_folds"]
                cid = cal.cal_id("value", f, u["tier"])
            docs[u["doc"]][f] = {"tier": u["tier"], "probability": cal.r6(p), "probability_written": cal.as_written(p),
                                 "value_status": status_of(p, u["tier"], fit, u["primary"], entry),
                                 "calibration": cid, "in_primary_set": u["primary"],
                                 "probability_from": (f"folds without {u['fold']}" if part == "open" and t else
                                                      "all folds" if t else "no unit of the pair: Jeffreys mean of 0/0"),
                                 "outcome": OUTCOME_NAME[u["code"]]}
    return dict(docs)


def certain_summary(units: dict, docs: dict) -> dict:
    out = {}
    for f, us in units.items():
        sel = [u for u in us if u["code"] in (EQ, DIFF) and docs.get(u["doc"], {}).get(f, {}).get("value_status") == "certain"]
        k, n = sum(1 for u in sel if u["code"] == EQ), len(sel)
        given = sum(1 for u in us if u["given"])
        out[f] = {"given_values": given,
                  "certain_values": sum(1 for u in us if u["given"] and docs[u["doc"]][f]["value_status"] == "certain"),
                  "certain_with_reference": n, "certain_equal": k, "precision_of_certain": ratio(k, n),
                  "precision_of_certain_jeffreys": jeffreys(k, n), "jeffreys_note": JEFFREYS_NOTE}
    return out


def quality_of(p, ok, what: str) -> dict | None:
    """Rule G6 items 17 and 22 to 25. Main Brier value: the mean of (p - y)^2. Main calibration error: 10 bins of
    p with equal width (the last bin holds 1.0), the sum of (units of the bin / all units) x |share equal - mean p|.
    The other forms are information."""
    p, ok = np.asarray(p, dtype=float), np.asarray(ok, dtype=bool)
    if not len(p):
        return None
    brier = float(((p - ok.astype(float)) ** 2).mean())
    return {"units": int(len(p)), "units_equal": int(ok.sum()), "mean_p": cal.r6(p.mean()),
            "brier": cal.r6(brier), "calibration_error": cal.r6(cal.ece_equal_width(p, ok)),
            "main_forms": "brier = mean (p - y)^2; calibration_error = 10 bins of equal width, last bin holds 1.0 "
                          "(addendum G, rule G6 items 22 to 24)",
            "information": {"ece_equal_mass": cal.r6(cal.ece_equal_mass(p, ok)), "brier_two_options": cal.r6(2 * brier),
                            "reliability": cal.reliability_table(p, ok)},
            "probabilities": what}


# ------------------------------------------------------------------ checksums and the opening (chapter 6.5)
def file_record(p: Path) -> dict:
    return {"path": cal.rel(p), "sha256": cal.sha256(p)}


def hashes_in(obj, names: dict, found: dict) -> None:
    """Find the SHA-256 of named files at each depth of the opening object. Accepted: {path or file name: sha},
    {path or file name: {"sha256": sha}} and {"path": .., "sha256": sha}."""
    if isinstance(obj, dict):
        p, s = obj.get("path", obj.get("file")), obj.get("sha256")
        if isinstance(p, str) and isinstance(s, str) and Path(p).name in names and SHA_RX.fullmatch(s):
            found.setdefault(names[Path(p).name], s)
        for k, v in obj.items():
            if isinstance(k, str) and Path(k).name in names:
                s = v.get("sha256") if isinstance(v, dict) else v
                if isinstance(s, str) and SHA_RX.fullmatch(s):
                    found.setdefault(names[Path(k).name], s)
            hashes_in(v, names, found)
    elif isinstance(obj, list):
        for v in obj:
            hashes_in(v, names, found)


def opening_state(opening: Path) -> dict:
    """Chapter 6.5, items 12 to 15, and chapter 5.5, item 22: the SHA-256 of the 6 files now, the values of the
    opening file (if it exists) and the mark. The tool writes the mark; no argument sets it."""
    now = {f: cal.sha256(ROOT / f) for f in OPENING_SIX}
    out = {"opening_file": cal.rel(opening), "opening_file_exists": Path(opening).is_file(), "files_now": now,
           "files_at_the_opening": None, "files_that_differ": [], "mark": None,
           "rule": "addendum G, chapter 6.5, items 12 to 15"}
    if not out["opening_file_exists"]:
        out["remark"] = "no opening file: the run is before the opening"
        return out
    data = cal.read_json(opening)
    stored: dict = {}
    hashes_in(data, {Path(f).name: f for f in OPENING_SIX}, stored)
    absent = [f for f in OPENING_SIX if f not in stored]
    if absent:
        raise Refused(f"opening file {cal.rel(opening)}: no SHA-256 for {len(absent)} of the 6 files ({absent}); "
                      "the tool cannot decide the mark (addendum G, chapter 6.5, items 3 and 15)")
    add: dict = {}
    hashes_in(data, {ADDENDUM.name: "addendum"}, add)
    out["opening_file_sha256"] = cal.sha256(opening)
    out["opening_time"] = next((data[k] for k in ("time", "opened", "opening_time", "made") if isinstance(data, dict) and k in data), None)
    out["files_at_the_opening"] = {f: stored[f] for f in OPENING_SIX}
    out["files_that_differ"] = [f for f in OPENING_SIX if stored[f] != now[f]]
    out["addendum_at_the_opening"] = add.get("addendum")
    out["addendum_differs"] = None if "addendum" not in add else add["addendum"] != cal.sha256(ADDENDUM)
    if out["files_that_differ"] or out["addendum_differs"]:
        out["mark"] = MARK
    out["remark"] = ("A change of chapter 3 or 4 of the addendum also gives the mark (item 12). The tool sees it "
                     "only if the opening file holds the SHA-256 of the addendum file; it then marks each change of "
                     "that file.")
    return out


def header(args, mode: str, norm, inputs: dict, opening: dict) -> dict:
    return {"schema": "parlpdfech-value-measures", "version": VERSION, "mode": mode, "part": mode, "status": STATUS,
            "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "label": args.label, "mark": opening["mark"],
            "rules": ADDENDUM_VERSION + ", rules G3 to G7 (" + cal.rel(ADDENDUM) + ")",
            "checksums": {"values_file": inputs["values"]["sha256"], "folds_file": inputs["folds"]["sha256"],
                          "addendum": cal.sha256(ADDENDUM), "files_of_the_opening": opening["files_now"],
                          "reference_file": inputs["reference"]["sha256"],
                          "rule": "addendum G, chapter 5.5, item 22"},
            "opening": opening,
            "script": file_record(SCRIPT), "frozen_import": file_record(Path(cal.__file__)),
            "normalisation": {"module": norm.__name__, "version": getattr(norm, "VERSION", None),
                              "file": file_record(Path(norm.__file__))},
            "compared_string": "the key normalised of each value record (addendum G, chapter 4.8, item 4)",
            "rounding": "counts are whole numbers; measures, bounds and probabilities have 6 decimals; each comparison "
                        "with a limit uses the value before the rounding (addendum G, chapter 5.5)",
            "inputs": inputs, "reference": REFERENCE}


def read_inputs(args, part: str, norm):
    folds = load_folds(args.folds)
    values = documents_of(cal.read_json(args.values), folds, part, "values file")
    reference = documents_of(cal.read_json(args.reference), folds, part, "reference file")
    units, info = build_units(norm, values, reference, folds, part)
    inputs = {"values": file_record(args.values), "reference": file_record(args.reference),
              "folds": file_record(args.folds), "counts": info}
    return folds, units, inputs


def reader_errors(units: dict) -> dict:
    """Chapter 5.1, item 11: the count of the records with the reason reader_error for each field of the part."""
    return {f: sum(1 for u in units[f] if u["reader_error"]) for f in FIELDS}


# ------------------------------------------------------------------ commands
def run_open(args, norm=None) -> dict:
    norm = norm or load_norm()
    opening = opening_state(args.opening)
    folds, units, inputs = read_inputs(args, "open", norm)
    fold_keys = sorted({v["fold"] for v in folds.values() if v["part"] == "open"})
    second = cal.read_json(args.second) if args.second else None
    inputs["second"] = file_record(args.second) if args.second else None
    cells, pairs, fields, fits, entries, cals = [], [], {}, {}, {}, {}
    for f in FIELDS:
        c, p, fields[f] = field_cells(units[f], f, "open", fold_keys)
        fits[f] = fit_field(units[f], fold_keys)
        for row in p:                      # the calibration values of the pair stand in the pair row
            t = fits[f]["tiers"].get(row["tier"])
            if t:
                row.update(probability_all_folds=cal.r6(t["p_all_folds"]),
                           probability_fold_value={k: cal.r6(v) for k, v in t["p_without_fold"].items()},
                           units_30_or_more=t["enough_units"], certain_tier=t["certain_tier"],
                           calibration=cal.cal_id("value", f, row["tier"]))
        cells += c
        pairs += p
    for f in FIELDS:
        entries[f] = entry_of(fits[f], compare_second(cells, pairs, second, f, "open"))
        cals |= calibration_records(f, fits[f], inputs["values"], fold_keys, entries[f]["entry"])
        fields[f]["calibration"] = {k: fits[f][k] for k in ("units", "a", "threshold", "certain_tiers", "quality")}
        fields[f]["entry"] = entries[f]
    docs = document_values(units, fits, entries, "open")
    summary = certain_summary(units, docs)
    for f in FIELDS:
        fields[f]["certain_values"] = summary[f]
    head = header(args, "open", norm, inputs, opening)
    m_out = head | {"folds": fold_keys, "records_with_the_reason_reader_error": reader_errors(units),
                    "cells": cells, "pairs": pairs, "fields": fields}
    c_out = head | {"schema": "parlpdfech-value-calibration", "folds": fold_keys, "calibrations": cals,
                    "lookup": {f: {"ech_slot": ECH_SLOT[f], "a": fits[f]["a"], "entry": entries[f]["entry"],
                                   "certain_tiers": fits[f]["certain_tiers"], "units": fits[f]["units"],
                                   "p_of_a_tier_with_no_unit": p_of(0, 0),
                                   "tiers": {t: {"k": v["k"], "n": v["n"], "by_fold": v["by_fold"],
                                                 "p_all_folds": cal.r6(v["p_all_folds"]),
                                                 "p_without_fold": {k: cal.r6(x) for k, x in v["p_without_fold"].items()},
                                                 "enough_units": v["enough_units"], "certain_tier": v["certain_tier"],
                                                 "calibration": cal.cal_id("value", f, t)}
                                             for t, v in fits[f]["tiers"].items()}} for f in FIELDS},
                    "lookup_remark": "A tool that decides a value status makes the probability again from k and n "
                                     "((k + 0.5) / (n + 1), clipped); the probabilities of this file have 6 decimals.",
                    "documents": docs}
    cal.write_json(args.out_measures, m_out)
    cal.write_json(args.out_calibration, c_out)
    return {"measures": m_out, "calibration": c_out}


def run_closed(args, norm=None) -> dict:
    if not Path(args.opening).is_file():
        raise Refused(f"the closed part stays closed: the file {args.opening} does not exist "
                      "(the AI agent writes it at the one opening; addendum G, chapter 6.5)")
    norm = norm or load_norm()
    opening = opening_state(args.opening)
    cfile = cal.read_json(args.calibration)
    if cfile.get("schema") != "parlpdfech-value-calibration" or cfile.get("mode") != "open":
        raise Refused("the calibration file is not an output of the command open")
    folds, units, inputs = read_inputs(args, "closed", norm)
    inputs |= {"calibration": file_record(args.calibration), "opening": file_record(Path(args.opening))}
    second = cal.read_json(args.second) if getattr(args, "second", None) else None
    inputs["second"] = file_record(args.second) if second is not None else None
    fold_keys = list(cfile["folds"])
    # the probabilities are made again from the counts k and n of the open part (no rounded value is compared)
    fits = {f: {"a": cfile["lookup"][f]["a"],
                "tiers": {t: tier_record(v["k"], v["n"], v["by_fold"], fold_keys)
                          for t, v in cfile["lookup"][f]["tiers"].items()}} for f in FIELDS}
    entries = {f: {"entry": cfile["lookup"][f]["entry"]} for f in FIELDS}
    docs = document_values(units, fits, entries, "closed")
    summary = certain_summary(units, docs)
    cells, pairs, fields = [], [], {}
    for f in FIELDS:
        c, p, fields[f] = field_cells(units[f], f, "closed", [])
        for row in p:
            t = fits[f]["tiers"].get(row["tier"])
            row["probability_all_folds"] = cal.r6(t["p_all_folds"] if t else p_of(0, 0))
        cells += c
        pairs += p
    for f in FIELDS:
        us = [u for u in units[f] if u["primary"] and u["code"] in (EQ, DIFF)]
        t_of = fits[f]["tiers"]
        fields[f]["calibration"] = {"a": fits[f]["a"], "entry": entries[f]["entry"], "units": len(us), "quality": quality_of(
            [t_of[u["tier"]]["p_all_folds"] if u["tier"] in t_of else p_of(0, 0) for u in us],
            [u["code"] == EQ for u in us], "values of all 5 folds of the open part, clipped, no rounding (information: "
            "the main forms of rule G6 item 25 use the open part)")}
        fields[f]["certain_values"] = summary[f]
        fields[f]["second_calculation_information"] = compare_second(cells, pairs, second, f, "closed")
    out = header(args, "closed", norm, inputs, opening) | {
        "records_with_the_reason_reader_error": reader_errors(units),
        "cells": cells, "pairs": pairs, "fields": fields, "documents": docs}
    cal.write_json(args.out_measures, out)
    return {"measures": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("open", "closed"):
        p = sub.add_parser(name)
        p.add_argument("--values", type=Path, required=True)
        p.add_argument("--reference", type=Path, required=True)
        p.add_argument("--folds", type=Path, default=FOLDS_FILE)
        p.add_argument("--out-measures", type=Path, required=True)
        p.add_argument("--opening", type=Path, default=OPENING_FILE)
        p.add_argument("--second", type=Path, default=None, help="file of the second calculation")
        p.add_argument("--label", default="", help="a name of the run, for example the role tier of the readers")
    sub.choices["open"].add_argument("--out-calibration", type=Path, required=True)
    sub.choices["closed"].add_argument("--calibration", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        res = run_open(args) if args.cmd == "open" else run_closed(args)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    m = res["measures"]
    for c in m["cells"]:
        if c["base"] == "primary" and c["dimension"] == "none":
            n = c["counts"]
            print(f"{c['field']}: documents {n['documents']}, equal {n['equal']}, different {n['different']}, "
                  f"not found {n['not_found']}, no reference {n['no_reference']}")
    print(f"records with the reason reader_error: {m['records_with_the_reason_reader_error']}")
    print(f"mark: {m['mark']}")
    print(f"written: {cal.rel(args.out_measures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

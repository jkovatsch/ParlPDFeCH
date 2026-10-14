# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""m11_value_reference: the reference table of addendum G (rule G2) for the development documents.

For each development document the tool writes the reference value of each field of addendum G, table 1:
the raw export value, the normal form (made by src/m11_value_norm.py only), or the class "no reference"
with its reason. It also writes the language of the block file and the S1 rule role.

Outputs (the part of a document comes from daten/gj_values/folds.json):
  daten/gj_values/reference_open.json      documents of the open parliaments
  daten/gj_values/reference_closed.json    documents of the closed parliaments

The tool prints COUNTS only. It never prints and never returns a value of the closed part. The command `show`
refuses a document of a closed parliament. The tool reads no PDF text and it calculates no agreement value:
it reads the export only. A value reader must not read these files (addendum G, chapter 3.1, item 9).

Inputs:
  daten/gj_values/folds.json                           ids, parliament, part, fold
  src/m10_guard.py                                     each id is tested (split dev) before a file is opened
  daten/gj/fullrun_b1s_dev/<doc>/export/<doc>.json     export record: parts affair, body, events
  daten/gj/docs/<doc>.json                             keys split, parliament, language only
  daten/gj/rules_pdf/<doc>.json                        key document.s1.rule_role only (rule files from the PDF
                                                       alone, src/m11_rules_pdf.py; round 4, 13.10.2026)
  daten/roh/exports/contributors.ndjson.gz             rows of ALL splits; filtered reader, see contributor_rows()
  src/m02_ech_regeln.py                                typ_ech (term list of the affair type), by import

Commands:
  python src/m11_value_reference.py build       write the two files, print counts
  python src/m11_value_reference.py check       read the files again, test them, print counts (the file of the
                                                closed part only after the opening: daten/gj_values/opening.json)
  python src/m11_value_reference.py show <id>   one document of an OPEN parliament (for a unit case)
  python src/m11_value_reference.py selftest    unit cases of the reference rules on hand-made records
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))

import m11_value_norm as vn  # noqa: E402

VERSION = "m11-value-reference-2"
SCHEMA = "parlpdfech-value-reference"
FOLDS_FILE = ROOT / "daten/gj_values/folds.json"
OPENING_FILE = ROOT / "daten/gj_values/opening.json"   # addendum G version 2, chapter 6.5: the file is the opening
OUT = {"open": ROOT / "daten/gj_values/reference_open.json", "closed": ROOT / "daten/gj_values/reference_closed.json"}
EXPORT_DIR = ROOT / "daten/gj/fullrun_b1s_dev"
DOCS_DIR = ROOT / "daten/gj/docs"
RULES_DIR = ROOT / "daten/gj/rules_pdf"
CONTRIBUTORS = ROOT / "daten/roh/exports/contributors.ndjson.gz"
EXPORT_TIME_FILE = ROOT / "daten/roh/exports/abgerufen_utc.txt"

FIELDS = vn.FIELDS
PRIMARY_ROLES = ("response", "combined")              # addendum G, table 1
ROLE_PRIMARY_FIELDS = ("response_date", "responder_name")
TITLE_LANGUAGES = ("de", "fr", "it")
NO_POSITION = 99                                      # addendum G, chapter 3.4, item 4

# Counts of probe 2 (and of probe 3 and the plan where the addendum names them) for the whole dev split.
# key -> (expected count, source)
PROBE = {
    "documents": (1793, "probe 2, summary"),
    "affairs": (1702, "probe 2, summary"),
    "parliaments": (44, "probe 2, summary"),
    "affair_type.reference": (1657, "probe 2, table 1"),
    "affair_type.no_reference": (136, "probe 2, facts"),
    "title.reference": (1772, "probe 2, table 1"),
    "title.no_reference": (21, "addendum G, table 2"),
    "affair_number.number_not_empty": (1793, "probe 2, table 1"),
    "affair_number.alternative_not_empty": (140, "probe 2, table 1"),
    "affair_number.number_class_S1": (173, "probe 2, table 2"),
    "affair_number.number_class_S2": (36, "probe 2, table 2"),
    "affair_number.number_short_digits": (62, "probe 2, table 2"),
    "submission_date.reference": (1771, "probe 2, table 1"),
    "submission_date.documents_with_event_1": (1595, "probe 2, facts"),
    "submission_date.documents_with_2_or_more_events_1": (150, "probe 2, summary (c)"),
    "response_date.reference": (616, "probe 2, table 1"),
    "response_date.documents_with_event_6": (650, "probe 2, facts"),
    "response_date.documents_with_2_or_more_events_6": (35, "probe 2, summary (c)"),
    "response_date.reference_in_primary_set": (218, "addendum G, table 2 (probe 3: 108 and 110)"),
    "responder_name.name_not_empty": (1548, "probe 2, table 1"),
    "first_author.contributor_rows": (6166, "probe 2, facts"),
    "first_author.documents_with_person_author_or_primary": (1226, "probe 2, table 1 (person)"),
    "first_author.documents_with_person_author": (1164, "probe 2, table 3"),
    "first_author.documents_with_person_primary": (62, "probe 2, table 3"),
    "language.de": (1230, "probe 2, facts"),
    "language.fr": (293, "probe 2, facts"),
    "language.it": (254, "probe 2, facts"),
    "language.none": (15, "probe 2, facts"),
    "language.en": (1, "probe 2, facts"),
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def not_empty(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


# ------------------------------------------------------------------ the reference rules (one function per field)

def entry(values: list, raw: list, reason: str | None, **extra) -> dict:
    """One field of one document. `values` = the normal forms of the reference (empty = no reference)."""
    return {"status": "reference" if values else "no reference", "reason": None if values else reason,
            "values": values, "raw": raw, **extra}


def ref_affair_type(affair: dict, typ_ech) -> dict:
    """Addendum G, chapter 3.2, item 1: first part of typ_ech(type_harmonized_id, local type name);
    local type name = the first value that is not empty of type_name_de, _fr, _it."""
    source = next((k for k in ("type_name_de", "type_name_fr", "type_name_it") if affair.get(k)), None)
    local = affair.get(source) if source else None
    value, kind, category, origin = typ_ech(affair.get("type_harmonized_id"), local)
    norm = vn.norm_affair_type(value)
    raw = [{"source": "affairs.type_harmonized_id", "value": affair.get("type_harmonized_id")},
           {"source": f"affairs.{source}" if source else "affairs.type_name_de/fr/it", "value": local},
           {"source": "m02_ech_regeln.typ_ech", "value": value or None, "match": kind, "category": category or None,
            "origin": origin}]
    reason = "no_type_in_export" if (local is None and affair.get("type_harmonized_id") is None) else "no_list_value"
    return entry([norm] if norm else [], raw, reason)


def ref_title(affair: dict, language: str | None) -> dict:
    """Chapter 3.2, items 2 and 3: affairs.title_<language of the block file>; a different language value or an
    empty title in that language = no reference."""
    if language not in TITLE_LANGUAGES:
        return entry([], [], "pdf_language_not_de_fr_it", language=language)
    source = f"affairs.title_{language}"
    value = affair.get(f"title_{language}")
    norm = vn.norm_title(value) if not_empty(value) else None
    raw = [{"source": source, "value": value}]
    if norm is None:
        return entry([], raw, "no_title_in_pdf_language", language=language)
    return entry([norm], raw, None, language=language)


def ref_affair_number(affair: dict) -> dict:
    """Chapter 3.3: affairs.number and affairs.external_alternative_id, one by one. A value of class S1 or S2 is
    no reference value. A value of 1 to 4 digits stays a reference value (flag short_digits)."""
    raw, values = [], []
    for key in ("number", "external_alternative_id"):
        v = affair.get(key)
        item = {"source": f"affairs.{key}", "value": v, "class": None, "used": False, "normalised": None}
        if not_empty(v):
            item["class"] = vn.number_class(v)
            norm = vn.norm_number(v)
            if item["class"] is None and norm is not None:
                item["used"] = True
                item["normalised"] = norm
                item["short_digits"] = vn.number_is_short_digits(v)
                if norm not in values:
                    values.append(norm)
            elif item["class"] is None:
                item["class"] = "empty_normal_form"
        raw.append(item)
    present = [i for i in raw if not_empty(i["value"])]
    if not present:
        reason = "no_number_in_export"
    elif all(i["class"] in ("S1", "S2") for i in present):
        reason = "system_identifier"
    else:
        reason = "system_identifier_or_empty_normal_form"
    return entry(values, raw, reason, short_digits_only=bool(values) and all(i.get("short_digits") for i in raw if i["used"]))


def _event_days(events: list, harmonized_id: int) -> tuple[list[str], list[dict]]:
    days, raw = [], []
    for e in events or []:
        if e.get("title_harmonized_id") != harmonized_id:
            continue
        day = vn.norm_day(e.get("date"))
        raw.append({"source": f"events.date (title_harmonized_id {harmonized_id})", "event_id": e.get("id"),
                    "value": e.get("date"), "normalised": day, "not_used": vn.day_reason(e.get("date"))})
        if day and day not in days:
            days.append(day)
    return sorted(days), raw


def ref_submission_date(affair: dict, events: list) -> dict:
    """Chapter 3.2: the set of the days of all events with title_harmonized_id 1; if no such event gives a day,
    affairs.begin_date. First 10 characters; a day that starts with 1900 is no reference."""
    days, raw = _event_days(events, 1)
    n_events = len(raw)
    origin = "event_1" if days else None
    if not days:
        b = affair.get("begin_date")
        day = vn.norm_day(b)
        raw.append({"source": "affairs.begin_date", "value": b, "normalised": day, "not_used": vn.day_reason(b)})
        if day:
            days, origin = [day], "begin_date"
    reason = "no_event_1_and_no_begin_date" if not n_events else "event_1_with_no_day_and_no_begin_date"
    if not days and any(r.get("not_used") == "day_1900" for r in raw):
        reason = "day_1900"
    return entry(days, raw, reason, origin=origin, events=n_events)


def ref_response_date(events: list) -> dict:
    """Chapter 3.2: the set of the days of all events with title_harmonized_id 6 and a date."""
    days, raw = _event_days(events, 6)
    reason = "no_event_6" if not raw else "event_6_with_no_day"
    if raw and not days and any(r.get("not_used") == "day_1900" for r in raw):
        reason = "day_1900"
    return entry(days, raw, reason, events=len(raw))


def ref_responder(body: dict) -> dict:
    """Chapter 3.2, item 8 and chapter 4.6: the set of the body words (table 3) of bodies.executive_name_de,
    _fr and _it. A name with no body word of the table gives no reference value."""
    raw, values = [], []
    for lang in TITLE_LANGUAGES:
        v = body.get(f"executive_name_{lang}")
        word = vn.body_word(v) if not_empty(v) else None
        raw.append({"source": f"bodies.executive_name_{lang}", "value": v, "normalised": word})
        if word and word not in values:
            values.append(word)
    reason = "no_body_word_in_name" if any(not_empty(r["value"]) for r in raw) else "no_executive_name"
    return entry(sorted(values), raw, reason)


def position_number(row: dict):
    """Chapter 3.4, item 4 (addendum G, version 2): the position as a number. No position and a position that is
    not a number count as 99. A string is not a number."""
    v = row.get("position")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        return NO_POSITION
    return v


def ref_first_author(rows: list[dict]) -> dict:
    """Chapter 3.4: person rows with a family name; role primary if one or more exist; else role author with the
    lowest position (no position or a position that is not a number = 99; the positions are compared as numbers).
    The reference is the set of the family names (token lists)."""
    persons = [r for r in rows if r.get("type") == "person" and not_empty(r.get("lastname"))]
    primary = [r for r in persons if r.get("role_harmonized") == "primary"]
    authors = [r for r in persons if r.get("role_harmonized") == "author"]
    if primary:
        chosen, origin = primary, "primary"
    elif authors:
        low = min(position_number(r) for r in authors)
        chosen = [r for r in authors if position_number(r) == low]
        origin = "author_lowest_position"
    else:
        chosen, origin = [], None
    raw, values = [], []
    for r in sorted(chosen, key=lambda r: r.get("id") or 0):
        norm = vn.norm_author(r.get("lastname"))
        raw.append({"source": "contributors.lastname", "row_id": r.get("id"), "role_harmonized": r.get("role_harmonized"),
                    "position": r.get("position"), "value": r.get("lastname"), "normalised": norm})
        if norm and norm not in values:
            values.append(norm)
    if not rows:
        reason = "no_contributor_row"
    elif not persons:
        reason = "no_person_row_with_family_name"
    elif not chosen:
        reason = "no_person_row_with_role_primary_or_author"
    else:
        reason = "family_name_with_empty_normal_form"
    return entry(sorted(values), raw, reason, origin=origin, rows_of_affair=len(rows), person_rows=len(persons))


# ------------------------------------------------------------------ the filtered reader of the contributors file

_RX_AFFAIR = re.compile(rb'"affair_id":\s*(\d+)')
CONTRIBUTOR_KEYS = ("id", "affair_id", "type", "role_harmonized", "lastname", "position")


def contributor_rows(dev_affairs: set[int]) -> tuple[dict[int, list[dict]], dict]:
    """The raw file holds rows of all splits. Each line stays raw bytes until its affair id is tested: a byte
    pattern takes the number after the key "affair_id", and the line is parsed only if that number is the id of
    an affair of a development document. After the parse the affair id is tested again, and only 6 keys of the
    row are kept. No other line is decoded, parsed, kept or shown."""
    by: dict[int, list[dict]] = {}
    lines = kept = second_refusal = 0
    with gzip.open(CONTRIBUTORS, "rb") as fh:
        for line in fh:
            lines += 1
            m = _RX_AFFAIR.search(line)
            if not m or int(m.group(1)) not in dev_affairs:
                continue
            row = json.loads(line)
            if row.get("affair_id") not in dev_affairs:
                second_refusal += 1
                continue
            kept += 1
            by.setdefault(row["affair_id"], []).append({k: row.get(k) for k in CONTRIBUTOR_KEYS})
    return by, {"lines": lines, "rows_kept": kept, "rows_refused_after_parse": second_refusal,
                "affairs_with_rows": len(by)}


# ------------------------------------------------------------------ build

def dev_documents() -> tuple[dict, dict]:
    """The ids of folds.json, each tested by m10_guard (split dev) before a file of a document is opened."""
    import m10_guard as guard  # noqa: PLC0415

    folds = read_json(FOLDS_FILE)
    docs = folds["documents"]
    ids = sorted(docs, key=int)
    g = guard.assert_allowed(ids, ("dev",))
    bad = [d for d in ids if g["split_of"][d] != "dev" or g["parliament_of"][d] != docs[d]["parliament"]]
    if bad:
        raise SystemExit(f"guard and folds.json do not agree for {len(bad)} ids")
    return folds, {"items": g["items"], "by_split": g["by_split"], "refused": g["refused"]}


def build_document(doc_id: str, fold_entry: dict, rows_by_affair: dict, typ_ech) -> tuple[dict, dict]:
    """The reference of one document and its counter keys (no value in the counter keys)."""
    rec = read_json(EXPORT_DIR / doc_id / "export" / f"{doc_id}.json")
    if str(rec.get("doc_id")) != doc_id or rec.get("body_key") != fold_entry["parliament"]:
        raise SystemExit(f"{doc_id}: the export record does not agree with folds.json")
    block_file = read_json(DOCS_DIR / f"{doc_id}.json")
    if block_file.get("split") != "dev" or block_file.get("parliament") != fold_entry["parliament"]:
        raise SystemExit(f"{doc_id}: the block file does not agree with folds.json")
    language = block_file.get("language")
    del block_file                                   # no block text is used
    s1_role = (read_json(RULES_DIR / f"{doc_id}.json").get("document") or {}).get("s1", {}).get("rule_role")
    affair, body, events = rec["affair"], rec["body"], rec.get("events") or []
    rows = rows_by_affair.get(affair["id"], [])
    fields = {
        "affair_type": ref_affair_type(affair, typ_ech),
        "title": ref_title(affair, language),
        "affair_number": ref_affair_number(affair),
        "submission_date": ref_submission_date(affair, events),
        "response_date": ref_response_date(events),
        "responder_name": ref_responder(body),
        "first_author": ref_first_author(rows),
    }
    in_role_set = s1_role in PRIMARY_ROLES
    for f, e in fields.items():
        e["primary_set"] = in_role_set if f in ROLE_PRIMARY_FIELDS else True
    doc = {"parliament": fold_entry["parliament"], "part": fold_entry["part"], "fold": fold_entry["fold"],
           "language": language, "s1_role": s1_role, "affair_id": affair["id"], "fields": fields}

    c = Counter()
    lang_key = language if language in TITLE_LANGUAGES else ("none" if language is None else str(language))
    c[f"language.{lang_key}"] += 1
    c[f"s1_role.{s1_role}"] += 1
    for f, e in fields.items():
        st = "reference" if e["values"] else "no_reference"
        c[f"{f}.{st}"] += 1
        if not e["values"]:
            c[f"{f}.no_reference.{e['reason']}"] += 1
        c[f"{f}.{st}.language.{lang_key}"] += 1
        c[f"{f}.{st}.s1_role.{s1_role}"] += 1
        if e["primary_set"]:
            c[f"{f}.primary_set"] += 1
            c[f"{f}.{st}_in_primary_set"] += 1
        if len(e["values"]) > 1:
            c[f"{f}.reference_with_2_or_more_values"] += 1
    num = {r["source"]: r for r in fields["affair_number"]["raw"]}
    n, a = num["affairs.number"], num["affairs.external_alternative_id"]
    c["affair_number.number_not_empty"] += not_empty(n["value"])
    c["affair_number.alternative_not_empty"] += not_empty(a["value"])
    for key, item in (("number", n), ("alternative", a)):
        if item["class"]:
            c[f"affair_number.{key}_class_{item['class']}"] += 1
        c[f"affair_number.{key}_used"] += item["used"]
        c[f"affair_number.{key}_short_digits"] += bool(item.get("short_digits"))
    c["affair_number.number_in_class_and_alternative_used"] += bool(n["class"] in ("S1", "S2") and a["used"])
    c["affair_number.reference_short_digits_only"] += fields["affair_number"]["short_digits_only"]
    sub = fields["submission_date"]
    c["submission_date.documents_with_event_1"] += sub["events"] > 0
    c["submission_date.documents_with_2_or_more_events_1"] += sub["events"] > 1
    c[f"submission_date.origin.{sub['origin']}"] += 1
    c["submission_date.event_1_with_no_day_then_begin_date"] += bool(sub["events"] and sub["origin"] == "begin_date")
    c["submission_date.day_1900_values"] += sum(r.get("not_used") == "day_1900" for r in sub["raw"])
    c["submission_date.bad_form_values"] += sum(r.get("not_used") == "bad_form" for r in sub["raw"])
    resp = fields["response_date"]
    c["response_date.documents_with_event_6"] += resp["events"] > 0
    c["response_date.documents_with_2_or_more_events_6"] += resp["events"] > 1
    c["response_date.day_1900_values"] += sum(r.get("not_used") == "day_1900" for r in resp["raw"])
    c["response_date.bad_form_values"] += sum(r.get("not_used") == "bad_form" for r in resp["raw"])
    c["responder_name.name_not_empty"] += any(not_empty(r["value"]) for r in fields["responder_name"]["raw"])
    fa = fields["first_author"]
    c["first_author.contributor_rows"] += 0          # rows are counted by affair, see build()
    c[f"first_author.origin.{fa['origin']}"] += 1
    persons_all = [r for r in rows if r.get("type") == "person"]
    c["first_author.documents_with_contributor_rows"] += bool(rows)
    c["first_author.documents_with_person_author_or_primary"] += any(
        r.get("role_harmonized") in ("author", "primary") for r in persons_all)
    c["first_author.documents_with_person_author"] += any(r.get("role_harmonized") == "author" for r in persons_all)
    c["first_author.documents_with_person_primary"] += any(r.get("role_harmonized") == "primary" for r in persons_all)
    c["first_author.documents_person_author_or_primary_no_family_name"] += bool(
        any(r.get("role_harmonized") in ("author", "primary") for r in persons_all) and not fa["values"])
    c["first_author.author_rows_with_no_position_used"] += sum(r["position"] is None for r in fa["raw"])
    c["first_author.author_rows_with_a_position_that_is_not_a_number_used"] += sum(
        r["position"] is not None and (isinstance(r["position"], bool) or not isinstance(r["position"], (int, float)))
        for r in fa["raw"])
    return doc, c


def build() -> int:
    import m02_ech_regeln as er  # noqa: PLC0415

    folds, guard_record = dev_documents()
    docs = folds["documents"]
    ids = sorted(docs, key=int)
    # pass 1: the affair id of each development document (key affair.id of the export record only)
    affair_of = {d: read_json(EXPORT_DIR / d / "export" / f"{d}.json")["affair"]["id"] for d in ids}
    dev_affairs = set(affair_of.values())
    rows_by_affair, reader_record = contributor_rows(dev_affairs)

    parts = {"open": {}, "closed": {}}
    counts = {"open": Counter(), "closed": Counter()}
    for d in ids:
        doc, c = build_document(d, docs[d], rows_by_affair, er.typ_ech)
        parts[doc["part"]][d] = doc
        counts[doc["part"]].update(c)
    affairs_part = {p: {doc["affair_id"] for doc in parts[p].values()} for p in parts}
    if affairs_part["open"] & affairs_part["closed"]:
        raise SystemExit("an affair has documents in the open part and in the closed part")
    for p in parts:
        counts[p]["documents"] = len(parts[p])
        counts[p]["affairs"] = len(affairs_part[p])
        counts[p]["parliaments"] = len({doc["parliament"] for doc in parts[p].values()})
        counts[p]["first_author.contributor_rows"] = sum(len(rows_by_affair.get(a, [])) for a in affairs_part[p])
    dev = Counter()
    for p in parts:
        dev.update(counts[p])
    probe = probe_check(dev)

    made = datetime.now().astimezone().isoformat(timespec="seconds")
    common = {
        "what": "Reference values of addendum G (rule G2) from the OpenParlData export for the development documents.",
        "use_rule": "Only the measurement tools read this file. A value reader never reads it. Until the AI agent "
                    "orders the one opening, no agent reads the file of the closed part.",
        "addendum": "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md",
        "addendum_sha256": sha256_file(ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md"),
        "export_retrieved_utc": EXPORT_TIME_FILE.read_text(encoding="utf-8").strip() if EXPORT_TIME_FILE.is_file() else None,
        "fields": list(FIELDS),
        "field_aliases_of_the_reader_registry": vn.FIELD_ALIASES,
        "normalisation_rule": vn.NORMALISATION_RULE,
        "entry_form": {
            "status": "reference | no reference",
            "reason": "reason code of 'no reference' (null with a reference)",
            "values": "the normal forms of the reference; the comparison is m11_value_norm.compare(field, reader value, values)",
            "raw": "each export value that was examined, with its source, and its normal form or the cause why it is not used",
            "primary_set": "true if the document is in the primary set of the field (table 1 of the addendum)",
        },
        "scripts": {rel(SCRIPT): sha256_file(SCRIPT), "src/m11_value_norm.py": sha256_file(SCRIPT.parent / "m11_value_norm.py"),
                    "src/m02_ech_regeln.py": sha256_file(SCRIPT.parent / "m02_ech_regeln.py")},
        "norm_version": vn.VERSION,
        "folds_file": {"path": rel(FOLDS_FILE), "sha256": sha256_file(FOLDS_FILE)},
        "guard": guard_record,
        "contributors_reader": {"file": rel(CONTRIBUTORS), "sha256": sha256_file(CONTRIBUTORS), **reader_record,
                                "rule": "a line is parsed only if the number after the key affair_id is the id of an "
                                        "affair of a development document; 6 keys of the row are kept",
                                "kept_keys": list(CONTRIBUTOR_KEYS)},
        "limits": [
            "The export is a register value. No human of this project examined it.",
            "The export describes the affair. It does not say which values this PDF prints.",
            "The first author has a weak reference: the role author also holds co-signatories and rapporteurs.",
            "The S1 rule role of the stored rule files got 3 export fields of the document (see folds.json, limits).",
        ],
        "notes": NOTES,
        "counts_dev": dict(sorted(dev.items())),
        "probe_check": probe,
    }
    for p in ("open", "closed"):
        out = {"schema": SCHEMA, "version": VERSION, "status": "PROPOSED, NOT RELEASED", "made": made,
               "actor": "AI agent (Claude Opus 5.5), task <id>; no human checked this file",
               "part": p, "header": common, "counts": dict(sorted(counts[p].items())),
               "documents": parts[p]}
        OUT[p].parent.mkdir(parents=True, exist_ok=True)
        OUT[p].write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report(counts, dev, probe)
    return 0 if all(r["equal"] or r["cause_known"] for r in probe) else 1


# Differences to a probe count that have a known cause (key -> cause). Each one is printed.
KNOWN_CAUSES: dict[str, str] = {}

# Counts that differ from a number in the plan or the addendum text, with the cause (measured by this tool).
NOTES = [
    "first_author: 1,164 documents have a reference. The plan gives 1,226 documents with a person row of the role "
    "author or primary. The 62 documents with a person row of the role primary have no family name in the row, "
    "and chapter 3.4 uses rows with a family name only.",
    "affair_number: 157 documents have no reference. Probe 2 gives 209 documents with a system identifier in "
    "affairs.number (173 and 36). For 52 of them affairs.external_alternative_id is a reference value "
    "(chapter 3.3, item 6).",
    "responder_name: each of the 1,548 documents with an executive name has one or more body words of table 3.",
    "submission_date: no document has an event 1 with no day; the two readings of 'if none' give the same result.",
    "The file names are reference_open.json and reference_closed.json (addendum G version 2, chapter 3.1, item 2). "
    "The part of a document is the part of folds.json.",
    "Version 2 of the tool: a position that is not a number counts as 99 (chapter 3.4, item 4). The normal forms "
    "come from src/m11_value_norm.py version 2; its functions for a reference value did not change.",
]


def probe_check(dev: Counter) -> list[dict]:
    out = []
    for key, (expected, source) in PROBE.items():
        got = dev.get(key, 0)
        out.append({"key": key, "expected": expected, "got": got, "equal": got == expected, "source": source,
                    "cause_known": key in KNOWN_CAUSES, "cause": KNOWN_CAUSES.get(key) if got != expected else None})
    return out


def report(counts: dict, dev: Counter, probe: list[dict]) -> None:
    """Counts only. No value of a document is printed."""
    print(f"{VERSION}: documents open {counts['open']['documents']}, closed {counts['closed']['documents']}")
    print("field | reference: dev open closed | no reference: dev open closed | in primary set with reference: open closed")
    for f in FIELDS:
        print(f"  {f:16s} | {dev[f + '.reference']:5d} {counts['open'][f + '.reference']:5d} {counts['closed'][f + '.reference']:4d}"
              f" | {dev[f + '.no_reference']:5d} {counts['open'][f + '.no_reference']:5d} {counts['closed'][f + '.no_reference']:4d}"
              f" | {counts['open'][f + '.reference_in_primary_set']:5d} {counts['closed'][f + '.reference_in_primary_set']:4d}")
    print("probe check (whole dev split):")
    for r in probe:
        mark = "equal" if r["equal"] else "DIFFERENT"
        print(f"  {mark:9s} {r['key']}: expected {r['expected']}, got {r['got']} ({r['source']})"
              + (f" CAUSE: {r['cause']}" if r["cause"] else ""))
    print("other counts, dev open closed:")
    for k in sorted(dev):
        if ".language." in k or ".s1_role." in k:
            continue
        print(f"  {k}: {dev[k]} {counts['open'].get(k, 0)} {counts['closed'].get(k, 0)}")


# ------------------------------------------------------------------ check

def check() -> int:
    """Read the files again. Test: ids against folds.json, each normal form made again by m11_value_norm from
    the raw value, status and reason, primary set, counts. Prints counts only.
    Addendum G version 2, chapter 3.1, item 10: no tool reads reference_closed.json before the opening. Thus the
    file of the closed part is read only if daten/gj_values/opening.json exists."""
    folds = read_json(FOLDS_FILE)
    errors: list[str] = []
    total = Counter()
    seen: set[str] = set()
    parts = ("open", "closed") if OPENING_FILE.is_file() else ("open",)
    if parts == ("open",):
        print("closed: not read (no opening file; addendum G, chapter 3.1, item 10)")
    n_parts = sum(1 for v in folds["documents"].values() if v["part"] in parts)
    for p in parts:
        data = read_json(OUT[p])
        docs = data["documents"]
        want_ids = {d for d, v in folds["documents"].items() if v["part"] == p}
        if set(docs) != want_ids:
            errors.append(f"{p}: the ids are not the ids of folds.json")
        seen |= set(docs)
        c = Counter()
        for d, doc in docs.items():
            fe = folds["documents"][d]
            if (doc["parliament"], doc["part"], doc["fold"]) != (fe["parliament"], fe["part"], fe["fold"]):
                errors.append(f"{p}: document {d}: parliament, part or fold")
            if set(doc["fields"]) != set(FIELDS):
                errors.append(f"{p}: document {d}: field list")
            for f, e in doc["fields"].items():
                again = []
                for r in e["raw"]:
                    if f == "affair_type":
                        n = vn.norm(f, r["value"]) if r["source"] == "m02_ech_regeln.typ_ech" else None
                    elif f == "affair_number":
                        n = vn.norm(f, r["value"]) if (isinstance(r["value"], str) and vn.number_class(r["value"]) is None) else None
                        if (n is not None) != r["used"]:
                            errors.append(f"{p}: document {d}: {f}: flag used")
                    else:
                        n = vn.norm(f, r["value"]) if isinstance(r["value"], str) and r["value"].strip() else None
                    if n is not None and n not in again:
                        again.append(n)
                if f == "submission_date" and e.get("origin") == "event_1":
                    again = [n for n in again if n in e["values"]]      # begin_date is not examined when an event gives a day
                if sorted(map(json.dumps, again)) != sorted(map(json.dumps, e["values"])):
                    errors.append(f"{p}: document {d}: {f}: the normal forms are not made again")
                if (e["status"] == "reference") != bool(e["values"]) or (e["reason"] is None) != bool(e["values"]):
                    errors.append(f"{p}: document {d}: {f}: status or reason")
                prim = doc["s1_role"] in PRIMARY_ROLES if f in ROLE_PRIMARY_FIELDS else True
                if e["primary_set"] != prim:
                    errors.append(f"{p}: document {d}: {f}: primary set")
                c[f"{f}.{'reference' if e['values'] else 'no_reference'}"] += 1
        for k, v in c.items():
            if data["counts"].get(k) != v:
                errors.append(f"{p}: count {k}: file {data['counts'].get(k)}, counted again {v}")
        if data["counts"]["documents"] != len(docs):
            errors.append(f"{p}: document count")
        total.update(c)
        print(f"{p}: documents {len(docs)}, sha256 {sha256_file(OUT[p])}")
        print("   " + ", ".join(f"{f} {c[f + '.reference']}/{c[f + '.no_reference']}" for f in FIELDS))
        if data["header"]["scripts"]["src/m11_value_norm.py"] != sha256_file(SCRIPT.parent / "m11_value_norm.py"):
            errors.append(f"{p}: src/m11_value_norm.py changed after the build")
    if len(seen) != n_parts:
        errors.append("the files do not hold each development document of the examined parts one time")
    for f in FIELDS:
        if total[f + ".reference"] + total[f + ".no_reference"] != n_parts:
            errors.append(f"{f}: reference + no reference is not the document count")
    for e in errors[:30]:
        print("ERROR", e)
    print(f"check: errors {len(errors)}")
    return 1 if errors else 0


# ------------------------------------------------------------------ show (open part only)

def show(doc_id: str) -> int:
    folds = read_json(FOLDS_FILE)
    fe = folds["documents"].get(str(doc_id))
    if fe is None:
        print("not a development document of folds.json")
        return 2
    if fe["part"] != "open":
        print("refused: the document is in a closed parliament")
        return 2
    doc = read_json(OUT["open"])["documents"][str(doc_id)]
    print(json.dumps(doc, ensure_ascii=False, indent=1))
    return 0


# ------------------------------------------------------------------ unit cases of the reference rules

def selftest() -> int:
    """Hand-made records (no document is read). They test the rules of chapters 3.2 to 3.4."""
    cases = []

    def want(name, got, expected):
        cases.append((name, got, expected))

    def fake(h, local):                      # a stand-in for typ_ech in the unit cases only
        return ("motion", "exakt", "", "lokal") if local == "Motion" else ("", "unbestimmt", "", "keine")

    e = ref_affair_type({"type_name_de": None, "type_name_fr": "Motion", "type_harmonized_id": 2}, fake)
    want("type first non-empty local name", (e["values"], e["raw"][1]["source"]), (["motion"], "affairs.type_name_fr"))
    e = ref_affair_type({"type_name_de": "Petition", "type_harmonized_id": None}, fake)
    want("type no list value", (e["status"], e["reason"]), ("no reference", "no_list_value"))
    e = ref_affair_type({}, fake)
    want("type no type", e["reason"], "no_type_in_export")

    a = {"title_de": "Ein Titel!", "title_fr": "", "title_it": None}
    want("title in the PDF language", ref_title(a, "de")["values"], ["ein titel"])
    want("title empty in the PDF language", ref_title(a, "fr")["reason"], "no_title_in_pdf_language")
    want("title language en", ref_title(a, "en")["reason"], "pdf_language_not_de_fr_it")
    want("title language none", ref_title(a, None)["reason"], "pdf_language_not_de_fr_it")

    e = ref_affair_number({"number": "2015.RRGR.334", "external_alternative_id": "107-2015"})
    want("number two values", e["values"], [["2015", "rrgr", "334"], ["107", "2015"]])
    e = ref_affair_number({"number": "123456", "external_alternative_id": None})
    want("number S1", (e["status"], e["reason"], e["raw"][0]["class"]), ("no reference", "system_identifier", "S1"))
    e = ref_affair_number({"number": "1db218b5", "external_alternative_id": "IP 12"})
    want("number S2 with a usable alternative", (e["values"], e["raw"][0]["used"]), ([["ip", "12"]], False))
    e = ref_affair_number({"number": "0042", "external_alternative_id": ""})
    want("number short digits stays", (e["values"], e["short_digits_only"]), ([["42"]], True))
    e = ref_affair_number({"number": " ", "external_alternative_id": None})
    want("number empty", e["reason"], "no_number_in_export")

    ev = [{"id": 1, "title_harmonized_id": 1, "date": "2013-01-21T00:00:00"},
          {"id": 2, "title_harmonized_id": 1, "date": "2013-01-17T09:30:00"},
          {"id": 3, "title_harmonized_id": 1, "date": "2013-01-21T00:00:00"},
          {"id": 4, "title_harmonized_id": 6, "date": None},
          {"id": 5, "title_harmonized_id": 40, "date": "2013-09-09T00:00:00"}]
    e = ref_submission_date({"begin_date": "2013-01-01T00:00:00"}, ev)
    want("submission set of event days", (e["values"], e["origin"], e["events"]), (["2013-01-17", "2013-01-21"], "event_1", 3))
    e = ref_submission_date({"begin_date": "2013-01-01T12:00:00"}, ev[3:])
    want("submission begin_date", (e["values"], e["origin"]), (["2013-01-01"], "begin_date"))
    e = ref_submission_date({"begin_date": "1900-01-01T00:00:00"}, [])
    want("submission 1900", (e["status"], e["reason"]), ("no reference", "day_1900"))
    e = ref_submission_date({"begin_date": None}, [])
    want("submission none", e["reason"], "no_event_1_and_no_begin_date")
    want("response event with no date", (ref_response_date(ev)["status"], ref_response_date(ev)["reason"]),
         ("no reference", "event_6_with_no_day"))
    want("response no event", ref_response_date(ev[:3])["reason"], "no_event_6")
    want("response day", ref_response_date([{"id": 9, "title_harmonized_id": 6, "date": "2014-02-03T00:00:00"}])["values"],
         ["2014-02-03"])

    e = ref_responder({"executive_name_de": "Regierungsrat", "executive_name_fr": "Conseil-exécutif",
                       "executive_name_it": "Consiglio esecutivo"})
    want("responder set of body words", e["values"], ["conseil_executif", "regierungsrat"])
    want("responder no name", ref_responder({})["reason"], "no_executive_name")
    want("responder no body word", ref_responder({"executive_name_de": "Landammann"})["reason"], "no_body_word_in_name")

    rows = [{"id": 1, "type": "person", "role_harmonized": "author", "lastname": "Linder", "position": 3},
            {"id": 2, "type": "person", "role_harmonized": "author", "lastname": "Enea", "position": 1},
            {"id": 3, "type": "group", "role_harmonized": "author", "lastname": "Regierungsrat", "position": 1},
            {"id": 4, "type": "person", "role_harmonized": "author", "lastname": "Mühlheim", "position": None},
            {"id": 5, "type": "person", "role_harmonized": "co-signer", "lastname": "Meier", "position": 0}]
    e = ref_first_author(rows)
    want("author lowest position", (e["values"], e["origin"]), ([["enea"]], "author_lowest_position"))
    e = ref_first_author(rows + [{"id": 6, "type": "person", "role_harmonized": "primary", "lastname": "von Arx", "position": 9}])
    want("author primary wins", (e["values"], e["origin"]), ([["von", "arx"]], "primary"))
    e = ref_first_author([rows[3], {**rows[0], "position": None}])
    want("author no position = 99, set", e["values"], [["linder"], ["muhlheim"]])
    e = ref_first_author([{**rows[0], "position": "1"}, {**rows[1], "position": 7}, {**rows[3], "position": True}])
    want("author position that is not a number = 99; numbers are compared as numbers", e["values"], [["enea"]])
    want("author group only", ref_first_author([rows[2]])["reason"], "no_person_row_with_family_name")
    want("author co-signer only", ref_first_author([rows[4]])["reason"], "no_person_row_with_role_primary_or_author")
    want("author no row", ref_first_author([])["reason"], "no_contributor_row")

    failed = [(n, g, x) for n, g, x in cases if g != x]
    for f in failed:
        print("FAILED", f)
    norm = vn.selftest()
    print(f"{VERSION}: unit cases {len(cases)}, failed {len(failed)}; {norm['version']}: unit cases {norm['cases']}, "
          f"failed {len(norm['failed'])}")
    return 1 if failed or norm["failed"] else 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        return build()
    if cmd == "check":
        return check()
    if cmd == "show" and len(sys.argv) == 3:
        return show(sys.argv[2])
    if cmd == "selftest":
        return selftest()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

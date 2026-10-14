# SPDX-License-Identifier: Apache-2.0
"""Recorded I95 gaps of the gate GJ records: the rules A1 and A2 of addendum A to the criteria.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream G of
wave 4, for the AI agent. Gate GJ (OPEN), status EXCEPTION (process rule 10), NOT RELEASED. No human checked this
file. Rules: `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-a.md` (a working draft of the AI agent) and
decision M6 of the protocol entry of 13.10.2026, 00:02.

1 Gap (rule A1)
  1. I95 requires the slots affair_type and affair_number of an affair. The export gives no value for some
     affairs. The frozen `src/m06_converter.py` then writes no slot and one NotMappedRecord (`Affair.affair_type`
     or `Affair.affair_number`).
  2. A gap is such a slot of the one affair of a record (path `affairs[0]`). The permitted gap slots are GAP_SLOTS.
     Each other required I95 slot without a value is an error.
  3. No value is invented. This file changes no schema file and no frozen file.

2 Interface: the keys of manifest.json (written by `src/m10_writer.py`)
  "i95_gaps": a list in the sequence of GAP_SLOTS; the list is empty for a record without a gap. Each item is
      {"slot": "affair_type" | "affair_number", "cause": GAP_CAUSE[slot], "local_value": <text> | null}.
      local_value is the local type name of the export (type_name_de, else type_name_fr, else type_name_it). It is
      null if the export gives no local value. It is always null for affair_number.
  "conformance": "i95" for an empty list, else "i95_with_recorded_gaps".
  A manifest without the two keys is a record of the writer before addendum A. It has no recorded gap.

3 Method
  1. Absent required slots (absent_required): the JSON schema of the I95 file without a change, made by the
     LinkML generator as the plugin JsonschemaValidationPlugin(closed=True) of linkml-validate makes it. The
     function collects each error of the keyword `required`, in each alternative of a range. A valid record gives
     an empty list.
  2. I95 with gaps (i95_view): a copy of the I95 schema definition in memory. In the copy, `required` is false
     only for the given gap slots of the class Affair (relax_required). The function compares the JSON schema of
     the copy with the JSON schema of I95: only the `required` lists of Affair and of its subclasses can differ,
     and only by the gap slots (and the type of a gap slot can get the value null).
  3. Rule A2 (gap_rule): a record with recorded gaps passes only if (a) its absent required slots in I95 are
     exactly its recorded gaps, (b) I95 without a change refuses it, (c) I95 with exactly these gaps accepts it
     with 0 errors, and (d) the provenance side file has one NotMappedRecord of the converter for each gap.
  4. `src/m03_gold_record.py` (frozen, import only) has the precedent `missing_required`. It is the second method
     for a record with a gap. The writer records a gap only if this function gives the gap path too. In gap_rule,
     the paths of this function must be exactly the recorded gaps. It does not read the slots of mixins.
  5. A record without a gap gets no other check from this file: writer_gaps returns no gap and no problem.

Check script: `src/m10_gaps_test.py`.
"""

from __future__ import annotations

import contextlib
import copy
import difflib
import os
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

SCRIPT = "src/m10_gaps.py"
I95 = ROOT / "quellen/political-affairs-ech-group/ech-0295_affairs/input/schema.yaml"
ADDENDUM = ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-a.md"
ROOT_CLASS = "Container"
AFFAIR_CLASS = "Affair"
AFFAIR_PATH = "affairs[0]"
GAP_SLOTS = ("affair_type", "affair_number")
GAP_CAUSE = {"affair_type": "the export gives no value of the I95 AffairTypeEnum",
             "affair_number": "the export gives no affair number"}
NOT_MAPPED_ITEM = {"affair_type": "Affair.affair_type", "affair_number": "Affair.affair_number"}
LOCAL_FIELDS = {"affair_type": ("type_name_de", "type_name_fr", "type_name_it"), "affair_number": ()}
I95_CONFORMANT = "i95"
WITH_GAPS = "i95_with_recorded_gaps"
CONFORMANCE = (I95_CONFORMANT, WITH_GAPS)
GAP_KEYS = {"slot", "cause", "local_value"}
GENERATED_AT = "# Generation date:"          # the one line of a generated Python module that holds the run time


@contextlib.contextmanager
def in_src():
    """The LinkML generators find an import relative to the working folder (as src/m10_rdf.py in_src)."""
    old = os.getcwd()
    os.chdir(SRC)
    try:
        yield
    finally:
        os.chdir(old)


def conformance(gaps) -> str:
    """The conformance name of a record with these gaps (rule A2, item 5)."""
    return WITH_GAPS if gaps else I95_CONFORMANT


def gap_path(slot: str) -> str:
    return f"{AFFAIR_PATH}.{slot}"


def ordered(slots) -> tuple[str, ...]:
    """The gap slots in the sequence of GAP_SLOTS. A slot that is not a permitted gap slot stops the function."""
    given = set(slots)
    extra = sorted(given - set(GAP_SLOTS))
    if extra:
        raise ValueError(f"{extra} are not permitted gap slots (permitted: {list(GAP_SLOTS)})")
    return tuple(s for s in GAP_SLOTS if s in given)


def path_text(parts) -> str:
    """A JSON path as text: ['affairs', 0, 'title', 1] gives affairs[0].title[1]."""
    out = ""
    for p in parts:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out


# ------------------------------------------------------------------ I95 in memory with gap slots that are not required
def is_affair(schema, name: str | None) -> bool:
    """True if the class is Affair or a class below Affair (is_a) in the schema definition."""
    seen = set()
    while name and name not in seen:
        if name == AFFAIR_CLASS:
            return True
        seen.add(name)
        name = schema.classes[name].is_a if name in schema.classes else None
    return False


def relax_required(schema, slots) -> list[str]:
    """Sets `required` to false for the given gap slots of the class Affair, in a schema definition in memory.
    The schema is the I95 file as loaded, or the resolved schema of a LinkML generator. No file changes.
    Returns the names of the changed elements. A slot that another class uses stops the function."""
    changed = []
    for slot in ordered(slots):
        derived = f"{AFFAIR_CLASS}_{slot}"          # the slot that the LinkML loader makes from a slot_usage
        users = [c.name for c in schema.classes.values() if slot in (c.slots or []) or derived in (c.slots or [])]
        other = sorted(u for u in users if not is_affair(schema, u))
        if other or AFFAIR_CLASS not in users:
            raise ValueError(f"slot {slot}: used by {other or users}; it must be a slot of the class {AFFAIR_CLASS} only")
        hits = []
        usage = (schema.classes[AFFAIR_CLASS].slot_usage or {}).get(slot)
        if usage is not None and usage.required:
            usage.required = False
            hits.append(f"classes.{AFFAIR_CLASS}.slot_usage.{slot}")
        for name in (slot, derived):
            s = schema.slots.get(name)
            if s is not None and s.required:
                s.required = False
                hits.append(f"slots.{name}")
        if not hits:
            raise ValueError(f"slot {slot}: the schema does not require it; no change is possible")
        changed += hits
    return changed


def json_schema_change_problems(strict: dict, relaxed: dict, slots) -> list[str]:
    """The problems of the JSON schema of a relaxed I95. It can differ from the JSON schema of I95 only in Affair
    and in the classes below it: the `required` list loses the given slots, and the type of such a slot can get
    the value null (the LinkML generator permits null for a slot that is not required)."""
    bad = []
    if {k: v for k, v in strict.items() if k != "$defs"} != {k: v for k, v in relaxed.items() if k != "$defs"}:
        bad.append("the JSON schemas differ outside $defs")
    if set(strict["$defs"]) != set(relaxed["$defs"]):
        bad.append("the JSON schemas have different definitions")
        return bad
    lost = set()
    for name, a in strict["$defs"].items():
        b = relaxed["$defs"][name]
        if a == b:
            continue
        pa, pb = a.get("properties") or {}, b.get("properties") or {}
        rest_a, rest_b = ({k: v for k, v in x.items() if k not in ("required", "properties")} for x in (a, b))
        want = [s for s in a.get("required") or [] if s not in slots]
        if rest_a != rest_b or set(pa) != set(pb) or (b.get("required") or []) != want:
            bad.append(f"definition {name}: a change that is not the removal of {list(slots)} from `required`")
            continue
        for k in pa:
            if pa[k] == pb[k]:
                continue
            same = {x: y for x, y in pa[k].items() if x != "type"} == {x: y for x, y in pb[k].items() if x != "type"}
            if k not in slots or not same or pb[k].get("type") != [pa[k].get("type"), "null"]:
                bad.append(f"definition {name}: the property {k} has a change that is not the type null of a gap slot")
        lost |= set(a.get("required") or []) - set(b.get("required") or [])
        if not all(s in pa for s in slots):
            bad.append(f"definition {name}: changed, but it does not have the slots {list(slots)}")
    if lost != set(slots):
        bad.append(f"`required` lost {sorted(lost)}, wanted {sorted(slots)}")
    return bad


def module_change_problems(strict_text: str, relaxed_text: str, slots) -> list[str]:
    """The problems of the Python module of a relaxed schema (src/m10_rdf.py): each line that differs from the
    module of the schema without a change must name a relaxed slot, and each relaxed slot must lose its check.
    The comment line with the generation date is not compared."""
    a, b = ([z for z in x.splitlines() if not z.startswith(GENERATED_AT)] for x in (strict_text, relaxed_text))
    changed = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            changed += a[i1:i2] + b[j1:j2]
    bad = [f"changed line without a relaxed slot: {line.strip()[:120]!r}" for line in changed
           if line.strip() and not any(s in line for s in slots)]
    for s in GAP_SLOTS:
        check = f'self.MissingRequiredField("{s}")'
        want = 0 if s in slots else 1
        if strict_text.count(check) != 1 or relaxed_text.count(check) != want:
            bad.append(f"slot {s}: {strict_text.count(check)} required checks in the module without a change and "
                       f"{relaxed_text.count(check)} in the relaxed module (wanted 1 and {want})")
    return bad


def i95_view(slots=()) -> dict:
    """I95 for the LinkML JSON-schema validation, one time for each gap set in a process. `slots` are the gap slots
    that are not required; no slot gives I95 without a change. Keys: plugin, context, json (the JSON-schema
    validator), changed (the changed schema elements)."""
    return _i95_view(ordered(slots))


@lru_cache(maxsize=None)
def _i95_view(slots: tuple[str, ...]) -> dict:
    from linkml.validator.plugins import JsonschemaValidationPlugin
    from linkml.validator.validation_context import ValidationContext
    from linkml_runtime.linkml_model import SchemaDefinition
    from linkml_runtime.loaders import yaml_loader
    plugin = JsonschemaValidationPlugin(closed=True)
    with in_src():
        schema = yaml_loader.load(str(I95), SchemaDefinition)
        schema.source_file = str(I95)                 # as linkml.validator.Validator does for a file path
        changed = relax_required(schema, slots)
        context = ValidationContext(schema, ROOT_CLASS)
        # the arguments of the plugin, so that the plugin uses this validator object (cache of the context)
        js = context.json_schema_validator(closed=plugin.closed,
                                           include_range_class_descendants=plugin.include_range_class_descendants,
                                           path_override=plugin.json_schema_path)
    if slots:
        bad = json_schema_change_problems(i95_view()["json"].schema, js.schema, slots)
        if bad:
            raise RuntimeError(f"I95 with the gap slots {list(slots)} not required: {bad[:5]}")
    return {"plugin": plugin, "context": context, "json": js, "changed": changed}


def linkml_messages(instance: dict, slots=()) -> list[str]:
    """The error messages of the LinkML JSON-schema validation of an instance against I95 (class Container), with
    the given gap slots not required. The empty tuple gives the check against I95 without a change."""
    view = i95_view(slots)
    with in_src():
        return [r.message for r in view["plugin"].process(instance, view["context"])]


def absent_required(instance: dict) -> list[str]:
    """The paths of the required I95 slots without a value, for example affairs[0].affair_type. Source: each error
    of the keyword `required` of the JSON schema of I95 without a change, in each alternative of a range."""
    out = set()

    def walk(e) -> None:
        if e.validator == "required" and isinstance(e.instance, dict):
            base = path_text(e.absolute_path)
            out.update(f"{base}.{name}" if base else name for name in e.validator_value if name not in e.instance)
        for c in e.context or []:
            walk(c)

    for e in i95_view()["json"].iter_errors(instance):
        walk(e)
    return sorted(out)


def precedent_paths(instance: dict) -> list[str]:
    """Second method (frozen precedent, import only): m03_gold_record.missing_required. It reads the slots and the
    slot_usage of a class and of its is_a parents in the I95 file. It does not read the slots of mixins."""
    import m03_gold_record as gr
    if gr.I95.resolve() != I95.resolve():
        raise RuntimeError("m03_gold_record.I95 is not the I95 file of this script")
    return sorted(gr.missing_required(instance))


# ------------------------------------------------------------------ rule A1: the writer
def local_value(slot: str, affair: dict | None) -> str | None:
    """The local value of the export for a gap slot, or None. For affair_type: the first local type name."""
    for f in LOCAL_FIELDS[slot]:
        v = (affair or {}).get(f)
        if v:
            return str(v)
    return None


def writer_gaps(instance: dict, not_mapped: list[dict], affair: dict | None) -> tuple[list[dict], list[str]]:
    """Rule A1 for the writer: (the gap items of the manifest, the problems). A gap is a permitted gap slot that
    is absent in the instance and that the converter recorded with one NotMappedRecord. Each other absent required
    slot, and each difference between the instance and the NotMappedRecords, is a problem. For a record with no
    absent required slot and no such NotMappedRecord, the function makes no other check."""
    absent = absent_required(instance)
    notes = {s: [n for n in not_mapped if n.get("not_mapped_item") == NOT_MAPPED_ITEM[s]] for s in GAP_SLOTS}
    if not absent and not any(notes.values()):
        return [], []
    precedent = precedent_paths(instance)
    gaps, bad = [], []
    for slot in GAP_SLOTS:
        if gap_path(slot) not in absent:
            if notes[slot]:
                bad.append(f"I95 gap check: a NotMappedRecord {NOT_MAPPED_ITEM[slot]}, but the instance has the slot")
            continue
        local = local_value(slot, affair)
        if len(notes[slot]) != 1:
            bad.append(f"required I95 slot {gap_path(slot)} has no value, and the converter wrote {len(notes[slot])} "
                       f"NotMappedRecords {NOT_MAPPED_ITEM[slot]} (wanted 1): not a recorded gap")
        elif (notes[slot][0].get("candidate_value") or None) != local:
            bad.append(f"I95 gap check: the NotMappedRecord {NOT_MAPPED_ITEM[slot]} does not have the local value of "
                       f"the export")
        elif gap_path(slot) not in precedent:
            bad.append(f"I95 gap check: m03_gold_record.missing_required does not give {gap_path(slot)}")
        else:
            gaps.append({"slot": slot, "cause": GAP_CAUSE[slot], "local_value": local})
    permitted = {gap_path(s) for s in GAP_SLOTS}
    bad += [f"required I95 slot {p} has no value; it is not a permitted gap slot" for p in absent if p not in permitted]
    if gaps:
        bad += [f"I95 gap check: {x}" for x in instance_gap_problems(instance, [g["slot"] for g in gaps])]
    return gaps, bad


# ------------------------------------------------------------------ the keys of the manifest
def manifest_gaps(man: dict) -> tuple[list[dict], list[str]]:
    """(The recorded gaps of a manifest, the problems of the keys i95_gaps and conformance). A manifest without
    the two keys has no recorded gap (a record of the writer before addendum A)."""
    if "i95_gaps" not in man and "conformance" not in man:
        return [], []
    gaps = man.get("i95_gaps")
    if not isinstance(gaps, list):
        return [], ["manifest: the key i95_gaps is not a list"]
    bad, seen = [], []
    for g in gaps:
        if not isinstance(g, dict) or set(g) != GAP_KEYS:
            bad.append(f"manifest: a gap item does not have exactly the keys {sorted(GAP_KEYS)}")
            continue
        if g["slot"] not in GAP_SLOTS or g["slot"] in seen:
            bad.append(f"manifest: gap slot {g['slot']!r} is not permitted or is there two times")
            continue
        seen.append(g["slot"])
        if g["cause"] != GAP_CAUSE[g["slot"]]:
            bad.append(f"manifest: gap {g['slot']}: the cause is not the fixed text")
        if g["local_value"] is not None and (not isinstance(g["local_value"], str) or not g["local_value"]):
            bad.append(f"manifest: gap {g['slot']}: local_value is not a text or null")
    if seen != list(ordered(seen)):
        bad.append(f"manifest: the gaps are not in the sequence {list(GAP_SLOTS)}")
    if man.get("conformance") != conformance(seen):
        bad.append(f"manifest: conformance {man.get('conformance')!r} does not agree with {len(seen)} recorded gaps")
    return gaps, bad


def gap_slots(man: dict) -> tuple[str, ...]:
    """The recorded gap slots of a manifest in the sequence of GAP_SLOTS. A problem of the keys stops the function."""
    gaps, bad = manifest_gaps(man)
    if bad:
        raise ValueError("; ".join(bad))
    return ordered(g["slot"] for g in gaps)


def instance_gap_problems(instance: dict, slots) -> list[str]:
    """A record with recorded gaps has one affair, and the affair has no value in each gap slot (rule A1, item 2)."""
    affairs = instance.get("affairs")
    if not isinstance(affairs, list) or len(affairs) != 1 or not isinstance(affairs[0], dict):
        return ["a record with a recorded gap must have one affair"]
    return [f"{gap_path(s)}: the manifest records a gap, but the instance has the key" for s in slots if s in affairs[0]]


# ------------------------------------------------------------------ rule A2: the validator
def gap_rule(instance: dict, man: dict, not_mapped: list[dict]) -> dict:
    """Rule A2 for one record with recorded gaps in its manifest. Returns the result for check C1 of
    src/m10_validate.py: passed, the recorded gaps, the absent required slots in I95, the result of I95 without a
    change (the record must fail) and the result of I95 with exactly the recorded gaps not required (0 errors)."""
    gaps, bad = manifest_gaps(man)
    slots = tuple(dict.fromkeys(g["slot"] for g in gaps if isinstance(g, dict) and g.get("slot") in GAP_SLOTS))
    want = sorted(gap_path(s) for s in slots)
    absent = absent_required(instance)
    precedent = precedent_paths(instance)
    if not slots:
        bad.append("gap rule: the manifest has no recorded gap")
    if absent != want:
        bad.append(f"gap rule: the absent required slots in I95 are {absent}; the recorded gaps are {want}")
    if precedent != want:
        bad.append(f"gap rule: m03_gold_record.missing_required gives {precedent}; the recorded gaps are {want}")
    if slots:
        bad += [f"gap rule: {x}" for x in instance_gap_problems(instance, slots)]
    for s in GAP_SLOTS:
        notes = [n for n in not_mapped if n.get("not_mapped_item") == NOT_MAPPED_ITEM[s]]
        g = next((g for g in gaps if isinstance(g, dict) and g.get("slot") == s), None)
        if g is None:
            if notes:
                bad.append(f"gap rule: a NotMappedRecord {NOT_MAPPED_ITEM[s]} without a recorded gap")
        elif len(notes) != 1:
            bad.append(f"gap rule: {len(notes)} NotMappedRecords {NOT_MAPPED_ITEM[s]} in the provenance side file "
                       f"(wanted 1)")
        elif (notes[0].get("candidate_value") or None) != g.get("local_value"):
            bad.append(f"gap rule: local_value of the gap {s} differs from the NotMappedRecord")
    strict = linkml_messages(instance)
    if not strict:
        bad.append("gap rule: I95 without a change accepts the record; a record with a gap must fail")
    relaxed, changed = None, []
    try:
        changed = list(i95_view(slots)["changed"])
        relaxed = linkml_messages(instance, slots)
    except (ValueError, RuntimeError) as e:
        bad.append(f"gap rule: no I95 with the recorded gaps: {e}")
    if relaxed:
        bad.append(f"gap rule: I95 with the gap slots {list(slots)} not required gives {len(relaxed)} errors")
    return {"passed": not bad, "conformance": conformance(slots), "recorded_gaps": copy.deepcopy(gaps),
            "absent_required_slots_i95": absent, "absent_required_slots_second_method": precedent,
            "i95_without_change": {"valid": not strict, "errors": len(strict), "messages": [m[:400] for m in strict[:10]]},
            "i95_with_recorded_gaps": {"slots_not_required": list(slots), "schema_elements_changed": changed,
                                       "valid": relaxed == [], "errors": None if relaxed is None else len(relaxed),
                                       "messages": [m[:400] for m in (relaxed or [])[:10]]},
            "problems": bad[:50],
            "method": f"{SCRIPT}: JSON schema of I95 (LinkML generator, closed); the recorded gap slots of the class "
                      f"{AFFAIR_CLASS} are not required in a copy of the schema in memory; no schema file changes"}

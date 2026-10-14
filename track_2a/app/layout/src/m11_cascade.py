#!/usr/bin/env python3
"""The cascade of eCH-0295: which labels apply for a document kind and an affair type.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent, 13.10.2026. Status: PROPOSED, NOT RELEASED. No human checked this file. This file changes no existing file.
Document: `crisp-dm/04-modeling/ech-cascade.md`. Machine form: `src/m11_cascade.yaml`.

1 Task
  The cascade has 5 stages: 0 the kind of the document, 1 the affair type, 2 the process steps, 3 the slots, 4 the
  values. An earlier decision changes the label selection of a later stage. `src/m11_cascade.yaml` holds the options,
  the rules R1 to R53 with their sources, and one entry for each slot of each class of the schema I95.
  This module reads the schema files at run time: the requirement of a slot, its range and the values of a value
  list come from the schema, not from the YAML file.

2 Interface
  labels_for(kind, affair_type) -> dict
      kind         one key of `kinds` of the YAML file
      affair_type  one value of AffairTypeEnum of I95, or "none" (recorded gap, rule R6)
      The result has: `steps` (each of the 9 step types: applies or not, the rules, the slots that apply),
      `affair` (the slots of the affair that are not part of a step), `not_applicable` (slots that a rule cuts),
      `block_options` (the options of the block question for this path), `questions`, `counts` (against the 87
      slots of I95). A slot entry has: path, class, slot, requirement (required or optional, from the schema),
      origin, today, ask, range, values (for a value list), rules.
  self_check() -> list of (name, ok, detail)
  path_counts() -> counts of the development documents for each path (aggregate counts only)

3 Commands (from the project folder)
  uv run --offline --frozen --no-sync python src/m11_cascade.py check
  uv run --offline --frozen --no-sync python src/m11_cascade.py labels --kind combined --type motion [--json]
  uv run --offline --frozen --no-sync python src/m11_cascade.py paths [--top 18]
  uv run --offline --frozen --no-sync python src/m11_cascade.py tables
  The command check ends with the exit code 1 if a check fails.

4 Limits
  The command paths reads only the rule role and the list value of the affair type of the development documents
  (`daten/gj_values/reference_open.json`, `reference_closed.json`) and the rule id of `daten/gj/rules/<doc>.json`.
  It prints counts. It reads no block text and no value of another field.
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CASCADE = Path(__file__).resolve().with_name("m11_cascade.yaml")
ORIGINS = ("pdf_block", "derived", "minted", "register", "structure", "no_holder")
BASES = ("standard", "project_rule", "project_choice")
EXPECTED = {"classes": 35, "slots": 87, "enums": 20}       # the I95 file that the cascade was made for
RULE_ROLES = ("proposal", "response", "combined", "committee", "minutes", "other")
REFERENCE_FILES = ("daten/gj_values/reference_open.json", "daten/gj_values/reference_closed.json")


class CascadeError(ValueError):
    pass


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ schema
class Schema:
    """One LinkML schema file with its imported common file. Only what the cascade needs."""

    def __init__(self, main: Path, common: Path | None = None):
        self.path = main
        self.doc = _yaml(main)
        self.common = _yaml(common) if common else {"classes": {}, "slots": {}, "enums": {}}
        self.classes = dict(self.common.get("classes") or {})
        self.classes.update(self.doc.get("classes") or {})
        self.own_slots = self.doc.get("slots") or {}
        self.slot_defs = dict(self.common.get("slots") or {})
        self.slot_defs.update(self.own_slots)
        self.enums = self.doc.get("enums") or {}

    def chain(self, cls: str) -> list[str]:
        """The class, its mixins and its parents (each with their mixins), the class first."""
        out, todo = [], [cls]
        while todo:
            c = todo.pop(0)
            if c in out or c not in self.classes:
                continue
            out.append(c)
            d = self.classes[c] or {}
            todo += list(d.get("mixins") or [])
            if d.get("is_a"):
                todo.append(d["is_a"])
        return out

    def parents(self, cls: str) -> list[str]:
        out, c = [], cls
        while c in self.classes:
            out.append(c)
            c = (self.classes[c] or {}).get("is_a")
        return out

    def slots_of(self, cls: str) -> list[tuple[str, str]]:
        """(slot, the class or mixin that names it), own slots first, no slot twice."""
        out, seen = [], set()
        for c in self.chain(cls):
            for s in (self.classes[c] or {}).get("slots") or []:
                if s not in seen:
                    seen.add(s)
                    out.append((s, c))
        return out

    def slot(self, cls: str, slot: str) -> dict:
        d = dict(self.slot_defs.get(slot) or {})
        for c in reversed(self.chain(cls)):
            d.update(((self.classes[c] or {}).get("slot_usage") or {}).get(slot) or {})
        return d

    def required(self, cls: str, slot: str) -> bool:
        d = self.slot(cls, slot)
        return bool(d.get("required") or d.get("identifier"))

    def range_of(self, cls: str, slot: str) -> str:
        return self.slot(cls, slot).get("range") or self.doc.get("default_range") or "string"

    def enum_values(self, name: str) -> list[str]:
        return [str(v) for v in ((self.enums.get(name) or {}).get("permissible_values") or {})]

    def is_mixin(self, cls: str) -> bool:
        return bool((self.classes.get(cls) or {}).get("mixin"))


_CACHE: dict = {}


def cascade() -> dict:
    if "cascade" not in _CACHE:
        _CACHE["cascade"] = _yaml(CASCADE)
    return _CACHE["cascade"]


def source_path(ref: str) -> Path:
    return ROOT / cascade()["sources"][ref]["file"]


def i95() -> Schema:
    if "i95" not in _CACHE:
        _CACHE["i95"] = Schema(source_path("I95"), source_path("C92"))
    return _CACHE["i95"]


def k95() -> Schema:
    if "k95" not in _CACHE:
        _CACHE["k95"] = Schema(source_path("K95"), source_path("C92"))
    return _CACHE["k95"]


def profile_steps(ref: str, cls: str) -> list[str]:
    """The annotation allowed_step_types of a profile, read at run time."""
    usage = _yaml(source_path(ref))["classes"][cls]["slot_usage"]
    return str(usage["procedure_steps"]["annotations"]["allowed_step_types"]).split()


def profile_type(ref: str, cls: str) -> str:
    return _yaml(source_path(ref))["classes"][cls]["slot_usage"]["affair_type"]["equals_string"]


# ------------------------------------------------------------------------------------------------ the map of slots
def entry_of(cls: str, slot: str) -> tuple[dict, str]:
    """The entry of a slot at a class: the class, then its parents, then the common slots. -> (entry, key)."""
    c = cascade()
    for p in i95().parents(cls):
        key = f"{p}.{slot}"
        if key in c["slots"]:
            return c["slots"][key], key
    if slot in c["common_slots"]:
        return c["common_slots"][slot], f"*.{slot}"
    raise CascadeError(f"the cascade file has no entry for the slot {cls}.{slot}")


def values_for(path: str, cls: str, slot: str, affair_type: str) -> dict | None:
    """Stage 4: the values of the value list at this place, after the rules by type."""
    s = i95()
    enum = s.range_of(cls, slot)
    if enum not in s.enums:
        return None
    all_values = s.enum_values(enum)
    out = {"list": enum, "values": all_values, "rules": []}
    tail = "/".join(path.split("/")[-2:])
    own = f"{cls}.{slot}"
    for p in s.parents(cls):
        own_p = f"{p}.{slot}"
        for key, v in cascade()["values"].items():
            if key in (tail, own, own_p) or tail.endswith(key):
                vals = list(v["values"])
                rules = [v["rule"]]
                if affair_type in (v.get("by_type") or {}):
                    vals = list(v["by_type"][affair_type])
                    rules.append(v["by_type_rule"])
                out = {"list": enum, "values": vals, "rules": sorted(set(rules))}
                if v.get("register_values"):
                    out["register_values"] = list(v["register_values"])
                return out
    return out


def _walk(cls: str, path: str, kind: str, affair_type: str, step: str | None, gate: tuple[bool, object],
          nodes: list, cut: list, depth: int = 0) -> None:
    """All slots of a class at one place. gate = (today of the holder, ask of the holder)."""
    s = i95()
    if depth > 8:
        raise CascadeError(f"the class tree is too deep at {path}")
    for slot, _owner in s.slots_of(cls):
        e, key = entry_of(cls, slot)
        here = f"{path}/{cls}.{slot}" if path else f"{cls}.{slot}"
        other = e.get("step")
        if other and other != step:
            continue                       # this slot is part of another step; that step adds it
        if e.get("kinds") and kind not in e["kinds"]:
            cut.append({"path": here, "slot": slot, "reason": "kind", "rules": list(e.get("rules") or [])})
            continue
        if e.get("types") and affair_type not in e["types"]:
            cut.append({"path": here, "slot": slot, "reason": "affair_type", "rules": list(e.get("rules") or [])})
            continue
        today = bool(e.get("today")) and gate[0]
        ask = e.get("ask")
        if ask == "inherit":
            ask = gate[1]
        elif not gate[1]:
            ask = None
        rng = s.range_of(cls, slot)
        node = {"path": here, "class": cls, "slot": slot, "entry": key,
                "requirement": "required" if s.required(cls, slot) else "optional",
                "origin": e["origin"], "today": today, "ask": ask or None, "range": rng,
                "multivalued": bool(s.slot(cls, slot).get("multivalued")),
                "in_87": slot in s.own_slots, "step": step, "rules": list(e.get("rules") or [])}
        if e.get("derivation"):
            node["derivation"] = e["derivation"]
        v = values_for(here, cls, slot, affair_type)
        if v:
            of_step = (cascade()["steps"].get(step or "") or {"i95": {}})["i95"].get("values") or {}
            if v["list"] in of_step and cls == cascade()["steps"][step]["i95"]["class"]:
                v = dict(v, values=list(of_step[v["list"]]), rules=sorted(set(v["rules"]) | {"R10"}))
            node["values"] = v
        nodes.append(node)
        if rng in s.classes and not s.is_mixin(rng):
            _walk(rng, here, kind, affair_type, step, (today, ask), nodes, cut, depth + 1)


def step_state(kind: str, affair_type: str) -> dict:
    """Stage 2: for each of the 9 step types, whether it applies for this path, and the rules."""
    c = cascade()
    t = c["affair_types"][affair_type]
    of_type = set(c["type_steps"][t["steps"]]["steps"])
    of_kind = set(c["kind_steps"][kind]["steps"])
    out = {}
    for name, st in c["steps"].items():
        cond = (c["type_step_conditions"].get(affair_type) or {}).get(name)
        rules = [c["kind_steps"][kind]["rule"], *c["type_step_rules"][affair_type], "R25"]
        if name in of_kind and name in of_type:
            why = "applies"
        elif name not in of_kind and name not in of_type:
            why = "the kind cannot state it and the type does not have it"
        elif name not in of_kind:
            why = "a document of this kind cannot state it"
        else:
            why = "the type does not have it"
        out[name] = {"applies": why == "applies", "reason": why, "rules": rules, "built": bool(st["built"]),
                     "k95_class": st["k95_class"], "i95_holder": st["i95"]["holder"], "i95_class": st["i95"]["class"],
                     "condition": cond["condition"] if cond else None,
                     "values": st["i95"].get("values") or {}}
    return out


def labels_for(kind: str, affair_type: str) -> dict:
    """The steps and slots that apply for a document kind and an affair type (see the module text, item 2)."""
    c, s = cascade(), i95()
    if kind not in c["kinds"]:
        raise CascadeError(f"unknown kind {kind!r}; the kinds are {sorted(c['kinds'])}")
    if affair_type not in c["affair_types"]:
        raise CascadeError(f"unknown affair type {affair_type!r}; the types are {sorted(c['affair_types'])}")
    steps = step_state(kind, affair_type)
    cut: list = []
    holder_of = {st["i95"]["holder"]: [] for st in c["steps"].values() if st["i95"]["holder"]}
    for name, st in c["steps"].items():
        if st["i95"]["holder"]:
            holder_of[st["i95"]["holder"]].append(name)
    # the affair: own slots; a holder slot of a step is in if 1 or more of its steps apply
    affair_nodes: list = []
    root_gate = (True, "root")
    e_aff, _ = entry_of("Container", "affairs")
    affair_nodes.append({"path": "Container.affairs", "class": "Container", "slot": "affairs", "entry": "Container.affairs",
                         "requirement": "optional", "origin": e_aff["origin"], "today": True, "ask": None,
                         "range": "Affair", "multivalued": True, "in_87": True, "step": None,
                         "rules": list(e_aff.get("rules") or [])})
    for name in steps:
        steps[name]["slots"] = []
    extra_in_submission = {}       # step -> slots of the class Submission that are part of that step
    for name, st in c["steps"].items():
        for full in st["i95"].get("slots") or []:
            extra_in_submission.setdefault(name, []).append(full)
    for slot, _owner in s.slots_of("Affair"):
        e, key = entry_of("Affair", slot)
        here = f"Affair.{slot}"
        full = f"Affair.{slot}"
        users = holder_of.get(full)
        if users is not None:
            live = [u for u in users if steps[u]["applies"]]
            # the class Submission also holds slots of the steps withdrawal and plenary_debate
            if full == "Affair.submission":
                live += [u for u in extra_in_submission if steps[u]["applies"] and u not in live]
            if not live:
                cut.append({"path": here, "slot": slot, "reason": "step", "rules": steps[users[0]]["rules"]})
                continue
        if e.get("kinds") and kind not in e["kinds"]:
            cut.append({"path": here, "slot": slot, "reason": "kind", "rules": list(e.get("rules") or [])})
            continue
        today, ask = bool(e.get("today")), e.get("ask")
        rng = s.range_of("Affair", slot)
        node = {"path": here, "class": "Affair", "slot": slot, "entry": key,
                "requirement": "required" if s.required("Affair", slot) else "optional", "origin": e["origin"],
                "today": today, "ask": ask or None, "range": rng,
                "multivalued": bool(s.slot("Affair", slot).get("multivalued")), "in_87": slot in s.own_slots,
                "step": None, "rules": list(e.get("rules") or [])}
        if e.get("derivation"):
            node["derivation"] = e["derivation"]
        v = values_for(here, "Affair", slot, affair_type)
        if v:
            node["values"] = v
        if users is None:
            affair_nodes.append(node)
            if rng in s.classes and not s.is_mixin(rng):
                _walk(rng, here, kind, affair_type, None, (today, ask), affair_nodes, cut)
            continue
        for u in users:
            if not steps[u]["applies"]:
                continue
            own = today and steps[u]["built"]
            n2 = dict(node, step=u, today=own, ask=ask if steps[u]["built"] else None)
            steps[u]["slots"].append(n2)
            _walk(rng, here, kind, affair_type, u, (own, n2["ask"]), steps[u]["slots"], cut)
        if full == "Affair.submission":
            for u, fulls in extra_in_submission.items():
                if not steps[u]["applies"]:
                    continue
                # the object of the class Submission that holds the slot, with its required identifier (R27)
                steps[u]["slots"].append(dict(node, step=u, today=False, ask=None))
                e3, k3 = entry_of("Submission", "global_uri")
                steps[u]["slots"].append({
                    "path": f"{here}/Submission.global_uri", "class": "Submission", "slot": "global_uri", "entry": k3,
                    "requirement": "required", "origin": e3["origin"], "today": False, "ask": None,
                    "range": s.range_of("Submission", "global_uri"), "multivalued": False, "in_87": False,
                    "step": u, "rules": list(e3.get("rules") or [])})
                for f in fulls:
                    cls, sl = f.split(".")
                    e2, k2 = entry_of(cls, sl)
                    p2 = f"{here}/{f}"
                    r2 = s.range_of(cls, sl)
                    steps[u]["slots"].append({
                        "path": p2, "class": cls, "slot": sl, "entry": k2,
                        "requirement": "required" if s.required(cls, sl) else "optional", "origin": e2["origin"],
                        "today": False, "ask": None, "range": r2,
                        "multivalued": bool(s.slot(cls, sl).get("multivalued")), "in_87": sl in s.own_slots,
                        "step": u, "rules": list(e2.get("rules") or [])})
                    if r2 in s.classes and not s.is_mixin(r2):
                        _walk(r2, p2, kind, affair_type, u, (False, None), steps[u]["slots"], cut)
    for name, st in steps.items():
        if not st["applies"]:
            st["slots"] = []
    all_nodes = affair_nodes + [n for st in steps.values() for n in st["slots"]]
    # block options and questions of this path
    live_paths = {n["path"].split("/")[-1] for n in all_nodes} | {
        "/".join(n["path"].split("/")[-1:]) for n in all_nodes}
    live_cs = {f"{n['class']}.{n['slot']}" for n in all_nodes}
    options = [k for k, o in c["block_options"].items() if not o["slots"] or any(x in live_cs for x in o["slots"])]
    questions = ["Q0", "Q1", "QB"] + (["QR"] if "ResponseStep.recommendation" in live_cs else []) + (
        ["B1"] if any(n["ask"] == "B1" for n in all_nodes) else [])
    t = c["affair_types"][affair_type]
    return {"kind": kind, "affair_type": affair_type, "i95_class": t["i95_class"], "profile": t["profile"],
            "steps": steps, "affair": {"slots": affair_nodes}, "not_applicable": cut,
            "block_options": options, "questions": questions, "counts": counts_of(all_nodes),
            "cascade_version": c["version"]}


def counts_of(nodes: list) -> dict:
    """Counts against the 87 slot names of I95, and the counts of the common slots (C92)."""
    by = collections.defaultdict(list)
    for n in nodes:
        by[(n["slot"], n["in_87"])].append(n)
    out = {k: [] for k in ("apply", "today", "today_pdf_block", "ask", "design_only", "register_only")}
    common = {k: [] for k in ("apply", "today", "ask")}
    for (slot, in87), ns in sorted(by.items()):
        today = any(n["today"] for n in ns)
        ask = any(n["ask"] for n in ns)
        if not in87:
            common["apply"].append(slot)
            if today:
                common["today"].append(slot)
            if ask:
                common["ask"].append(slot)
            continue
        out["apply"].append(slot)
        if today:
            out["today"].append(slot)
        if any(n["today"] and n["origin"] == "pdf_block" for n in ns):
            out["today_pdf_block"].append(slot)
        if ask:
            out["ask"].append(slot)
        if not today and not ask:
            if all(n["origin"] == "register" for n in ns):
                out["register_only"].append(slot)
            else:
                out["design_only"].append(slot)
    total = len(i95().own_slots)
    return {"of": total, **{k: len(v) for k, v in out.items()}, "not_applicable": total - len(out["apply"]),
            "slots": out, "common_slots": {k: len(v) for k, v in common.items()}, "common": common}


# ------------------------------------------------------------------------------------------------ the self-check
def _dict_literal(path: Path, name: str) -> dict:
    """A dict literal `name = {...}` of a module, read with ast (the module is not imported)."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise CascadeError(f"{path.name} has no literal {name}")


def self_check() -> list[tuple[str, bool, str]]:
    c, s, k = cascade(), i95(), k95()
    res: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        res.append((name, bool(ok), detail))

    rule_ids = [r["id"] for r in c["rules"]]
    rules = {r["id"]: r for r in c["rules"]}
    # 1 the schema file is the one that the cascade was made for
    got = {"classes": len(s.doc["classes"]), "slots": len(s.own_slots), "enums": len(s.enums)}
    add("01 I95 has 35 classes, 87 slots, 20 value lists", got == EXPECTED, json.dumps(got))
    # 2 sources
    missing = [r for r, v in c["sources"].items() if not (ROOT / v["file"]).is_file()]
    add("02 each source file exists", not missing, ", ".join(missing))
    # 3 rules
    want = [f"R{i}" for i in range(1, len(rule_ids) + 1)]
    add("03 rule ids are R1 to Rn with no gap and no double", rule_ids == want, f"{len(rule_ids)} rules")
    bad = [r["id"] for r in c["rules"] if r.get("basis") not in BASES or r.get("stage") not in (0, 1, 2, 3, 4)
           or not r.get("if") or not r.get("then") or not r.get("source")]
    add("04 each rule has a stage, a basis, a condition, a result and a source", not bad, ", ".join(bad))
    bad = [f"{r['id']}:{x.get('ref')}" for r in c["rules"] for x in r["source"]
           if x.get("ref") not in c["sources"] or not x.get("where")]
    add("05 each source of a rule names a known file and a place", not bad, ", ".join(bad))
    bad = [r["id"] for r in c["rules"]
           if r["basis"] == "standard" and not any(x["ref"] in ("I95", "C92", "K95", "PM", "PI") or
                                                    x["ref"].startswith(("EX_", "G_")) for x in r["source"])]
    add("06 each rule with the basis standard names a file of the standard", not bad, ", ".join(bad))
    bad = [r["id"] for r in c["rules"] if r["basis"] == "project_rule"
           and not any(x["ref"].startswith("P_") for x in r["source"])]
    add("07 each rule with the basis project_rule names a file of the project", not bad, ", ".join(bad))
    bad = [r["id"] for r in c["rules"] if r["basis"] == "project_choice"
           and "project choice" not in (r.get("note") or "")]
    add("08 each rule with the basis project_choice says so in its note", not bad, ", ".join(bad))
    # 4 affair types
    enum = s.enum_values("AffairTypeEnum")
    add("09 the affair types are the values of AffairTypeEnum of I95 plus none",
        sorted(c["affair_types"]) == sorted(enum + ["none"]), ", ".join(enum))
    bad = [t for t, v in c["affair_types"].items()
           if v["i95_class"] and (v["i95_class"] not in s.classes or "Affair" not in s.parents(v["i95_class"]))]
    add("10 each class of an affair type is a subclass of Affair in I95", not bad, ", ".join(bad))
    sub = sorted(x for x in s.doc["classes"] if (s.classes[x] or {}).get("is_a") == "Affair")
    add("11 each subclass of Affair has one affair type",
        sub == sorted(v["i95_class"] for v in c["affair_types"].values() if v["i95_class"]), ", ".join(sub))
    bad = []
    for t, v in c["affair_types"].items():
        if v["profile"]:
            if profile_type(v["profile"], v["i95_class"]) != t:
                bad.append(f"{t}: type of the profile")
            if sorted(profile_steps(v["profile"], v["i95_class"])) != sorted(c["type_steps"][v["steps"]]["steps"]):
                bad.append(f"{t}: steps of the profile")
        if v["steps"] not in c["type_steps"]:
            bad.append(f"{t}: step set")
    add("12 the two profiles give the type and the step types of the cascade (read at run time)", not bad,
        "; ".join(bad))
    # 5 steps
    kenum = k.enum_values("StepTypeEnum")
    add("13 the steps are the values of StepTypeEnum of the kernel", list(c["steps"]) == kenum, ", ".join(kenum))
    bad = []
    for name, st in c["steps"].items():
        meaning = (k.enums["StepTypeEnum"]["permissible_values"][name] or {}).get("meaning", "")
        if meaning != f"aff:{st['k95_class']}" or st["k95_class"] not in k.classes:
            bad.append(f"{name}: kernel class")
        h, cls = st["i95"]["holder"], st["i95"]["class"]
        if (h is None) != (cls is None):
            bad.append(f"{name}: holder and class")
        if h:
            hc, hs = h.split(".")
            if hs not in dict(s.slots_of(hc)) or s.range_of(hc, hs) != cls:
                bad.append(f"{name}: the range of {h} is not {cls}")
        for full in st["i95"].get("slots") or []:
            cl, sl = full.split(".")
            if cl not in s.classes or sl not in dict(s.slots_of(cl)):
                bad.append(f"{name}: slot {full}")
            elif (c["slots"].get(full) or {}).get("step") != name:
                bad.append(f"{name}: the entry of {full} does not name the step")
        for en, vals in (st["i95"].get("values") or {}).items():
            if en not in s.enums or not set(vals) <= set(s.enum_values(en)):
                bad.append(f"{name}: values of {en}")
    add("14 each step names classes, slots and values that the schema files have", not bad, "; ".join(bad))
    bad = [f"{g}:{x}" for g, v in c["type_steps"].items() for x in v["steps"] if x not in c["steps"]]
    bad += [f"{kd}:{x}" for kd, v in c["kind_steps"].items() for x in v["steps"] if x not in c["steps"]]
    bad += [kd for kd in c["kinds"] if kd not in c["kind_steps"]] + [kd for kd in c["kind_steps"] if kd not in c["kinds"]]
    bad += [t for t in c["affair_types"] if t not in c["type_step_rules"]]
    bad += [f"{t}.{x}" for t, v in c["type_step_conditions"].items() for x in v
            if t not in c["affair_types"] or x not in c["steps"]]
    add("15 the step sets of the kinds and of the types name known steps, kinds and types", not bad, ", ".join(bad))
    # 6 kinds
    d1 = _dict_literal(source_path("P_D1"), "D1_OF_ROLE")
    role_text = source_path("P_ROLE").read_text(encoding="utf-8")
    roles_in_code = set(re.findall(r'out\("([a-z]+)", "([A-Z]\d)"\)', role_text))
    bad = []
    for kd, v in c["kinds"].items():
        for r in v["rule_roles"]:
            if r not in RULE_ROLES or r not in d1:
                bad.append(f"{kd}: rule role {r}")
            elif "rule_ids" not in v and d1[r] != v["d1"]:
                bad.append(f"{kd}: D1 answer")
        for rid in v.get("rule_ids") or []:
            if not any((r, rid) in roles_in_code for r in v["rule_roles"]):
                bad.append(f"{kd}: rule id {rid}")
    add("16 the kinds agree with the rule roles and the D1 answers of the project code", not bad, "; ".join(bad))
    add("17 each rule role of the project code has a kind",
        {r for r, _ in roles_in_code} == {r for v in c["kinds"].values() for r in v["rule_roles"]} == set(RULE_ROLES),
        ", ".join(sorted({r for r, _ in roles_in_code})))
    # 7 the map of the slots
    pairs = {f"{cls}.{sl}" for cls, d in s.doc["classes"].items() for sl in (d or {}).get("slots") or []
             if sl in s.own_slots}
    keys = set(c["slots"])
    overrides = {x for x in keys - pairs}
    bad = sorted(pairs - keys)
    add("18 each slot of each class of I95 has an entry", not bad, ", ".join(bad))
    bad = []
    for full in sorted(overrides):
        cls, sl = full.split(".")
        if cls not in s.doc["classes"] or sl not in dict(s.slots_of(cls)) or sl not in c["common_slots"]:
            bad.append(full)
    add("19 no entry names a slot that the schema does not have", not bad, ", ".join(bad))
    used_common = {sl for cls in s.doc["classes"] for sl, _ in s.slots_of(cls) if sl not in s.own_slots}
    add("20 the common slots are the mixin slots that the classes of I95 use",
        used_common == set(c["common_slots"]), ", ".join(sorted(used_common ^ set(c["common_slots"]))))
    add("21 the 87 slot names are the slot names of the entries",
        {x.split(".")[1] for x in pairs} == set(s.own_slots), f"{len(pairs)} pairs of class and slot")
    asks = set(c["questions"]) | set(c["block_options"]) | {"inherit"}
    bad = []
    for full, e in list(c["slots"].items()) + [(f"*.{x}", v) for x, v in c["common_slots"].items()]:
        if e.get("origin") not in ORIGINS:
            bad.append(f"{full}: origin")
        if not e.get("rules") or any(r not in rules for r in e["rules"]):
            bad.append(f"{full}: rules")
        if any(x not in c["kinds"] for x in e.get("kinds") or []):
            bad.append(f"{full}: kinds")
        if any(x not in c["affair_types"] for x in e.get("types") or []):
            bad.append(f"{full}: types")
        if e.get("step") and e["step"] not in c["steps"]:
            bad.append(f"{full}: step")
        if e.get("ask") and e["ask"] not in asks:
            bad.append(f"{full}: ask")
        if e.get("origin") == "structure" and not full.startswith("*"):
            cls, sl = full.split(".")
            if s.range_of(cls, sl) not in s.classes:
                bad.append(f"{full}: origin structure, but the range is no class")
    add("22 each entry has a known origin, known rules, kinds, types, steps and options", not bad, "; ".join(bad))
    # 8 required slots
    req = set()
    for cls, d in s.doc["classes"].items():
        for sl, _ in s.slots_of(cls):
            if s.required(cls, sl):
                owner = next((p for p in s.parents(cls) if sl in ((s.classes[p] or {}).get("slots") or [])
                              or sl in ((s.classes[p] or {}).get("slot_usage") or {})), cls)
                req.add("*.global_uri" if sl == "global_uri" else f"{owner}.{sl}")
    named = {x for r in c["rules"] for x in r.get("requires") or []}
    add("23 the rules R26 to R28 name exactly the required slots of I95 (read at run time)", req == named,
        ", ".join(sorted(req ^ named)))
    kreq = sorted(sl for sl, d in k.own_slots.items() if (d or {}).get("required"))
    add("24 the rule R29 names exactly the required slots of the kernel (read at run time)",
        kreq == sorted(rules["R29"]["k95_required"]), ", ".join(kreq))
    # 9 values
    bad = []
    for key, v in c["values"].items():
        cls, sl = key.split("/")[-1].split(".")
        if cls not in s.classes or sl not in dict(s.slots_of(cls)):
            bad.append(f"{key}: slot")
            continue
        en = s.range_of(cls, sl)
        allv = set(s.enum_values(en))
        lists = [v["values"], v.get("register_values") or [], *(v.get("by_type") or {}).values()]
        if en not in s.enums or any(not set(x) <= allv for x in lists):
            bad.append(f"{key}: a value is not in {en}")
        if any(t not in c["affair_types"] for t in v.get("by_type") or {}):
            bad.append(f"{key}: type")
        if v["rule"] not in rules or (v.get("by_type") and v.get("by_type_rule") not in rules):
            bad.append(f"{key}: rule")
        if "/" in key:
            hc, hs = key.split("/")[0].split(".")
            if hs not in dict(s.slots_of(hc)) or s.range_of(hc, hs) != cls:
                bad.append(f"{key}: holder")
    add("25 each value of stage 4 is a value of the value list of its slot in I95", not bad, "; ".join(bad))
    dv = c["derived_values"]
    stages, phases, decisions = (set(s.enum_values(x)) for x in
                                 ("ProcedureStageEnum", "ProcedurePhaseEnum", "ProcedureDecisionEnum"))
    ok = set(dv["phase_of_stage"]["map"]) == stages and all(
        v is None or v in phases for v in dv["phase_of_stage"]["map"].values())
    ok = ok and set(dv["decisions_of_stage"]["map"]) <= stages and all(
        set(v) <= decisions for v in dv["decisions_of_stage"]["map"].values())
    add("26 the derived values name stages, phases and decisions of I95", ok)
    # 10 questions and block options
    bad = [f"{o}:{x}" for o, v in c["block_options"].items() for x in v["slots"]
           if x.split(".")[0] not in s.classes or x.split(".")[1] not in dict(s.slots_of(x.split(".")[0]))]
    bad += [q for q, v in c["questions"].items() if v["stage"] not in (0, 1, 2, 3, 4)]
    add("27 each block option names slots of the schema", not bad, ", ".join(bad))
    # 11 all paths, reach of the slots
    reach, errors, reg_names = set(), [], collections.defaultdict(set)
    n_paths = 0
    for kd in c["kinds"]:
        for t in c["affair_types"]:
            n_paths += 1
            try:
                r = labels_for(kd, t)
            except Exception as e:                       # noqa: BLE001  (the check reports each failure)
                errors.append(f"{kd} x {t}: {e}")
                continue
            for n in r["affair"]["slots"] + [x for st in r["steps"].values() for x in st["slots"]]:
                if n["in_87"]:
                    reach.add(n["slot"])
                    reg_names[n["slot"]].add(n["origin"])
                if n["requirement"] == "required" and n["slot"] not in s.own_slots and n["slot"] != "global_uri":
                    errors.append(f"{kd} x {t}: required common slot {n['slot']}")
            cnt = r["counts"]
            if cnt["apply"] + cnt["not_applicable"] != cnt["of"]:
                errors.append(f"{kd} x {t}: counts")
    add(f"28 labels_for gives a result for each of the {n_paths} paths", not errors, "; ".join(errors[:5]))
    no_holder = set(c["no_holder_slots"])
    add("29 each of the 87 slots is on a path, or it is in the list of the slots with no holder",
        reach | no_holder == set(s.own_slots) and not (reach & no_holder),
        ", ".join(sorted(set(s.own_slots) - reach - no_holder)))
    held = {s.range_of(cls, sl) for cls in s.doc["classes"] for sl, _ in s.slots_of(cls)}
    lonely = {cls for cls in s.doc["classes"] if cls not in held and cls != "Container"
              and not any(p in held for p in s.parents(cls)) and not (s.classes[cls] or {}).get("abstract")
              and not any(cls in s.parents(x) and x != cls for x in s.doc["classes"])}
    lonely_slots = {sl for cls in lonely for sl in (s.classes[cls] or {}).get("slots") or [] if sl in s.own_slots
                    and not any(sl in ((d or {}).get("slots") or []) for o, d in s.doc["classes"].items()
                                if o not in lonely)}
    add("30 the slots with no holder are the slots of a class that no slot of I95 has as its range",
        lonely_slots == no_holder, f"classes: {', '.join(sorted(lonely))}")
    reg = {sl for sl, o in reg_names.items() if o == {"register"}}
    add("31 the list of the register-only slots is equal to the entries", reg == set(c["register_only_slots"]),
        ", ".join(sorted(reg ^ set(c["register_only_slots"]))))
    linked = {r for e in list(c["slots"].values()) + list(c["common_slots"].values()) for r in e.get("rules") or []}
    linked |= {v["rule"] for v in c["values"].values()} | {v.get("by_type_rule") for v in c["values"].values()}
    linked |= {v["rule"] for v in c["kind_steps"].values()} | {x for v in c["type_step_rules"].values() for x in v}
    linked |= {v["rule"] for v in dv.values()} | {x["rule"] for v in c["type_step_conditions"].values()
                                                 for x in v.values()}
    text_only = sorted(set(rules) - linked - {None}, key=lambda x: int(x[1:]))
    add("32 information: rules with no link to a slot, a step or a value (text rules)", True, ", ".join(text_only))
    return res


# ------------------------------------------------------------------------------------------------ paths
def kind_of_role(role: str, rule_id: str | None) -> str:
    """Rule R2: the kind that stands for a rule role in the counts."""
    for kd, v in cascade()["kinds"].items():
        if role in v["rule_roles"] and rule_id in (v.get("rule_ids") or []):
            return kd
    for kd, v in cascade()["kinds"].items():
        if role in v["rule_roles"] and not v.get("rule_ids"):
            return kd
    raise CascadeError(f"no kind for the rule role {role}")


def path_counts() -> dict:
    """Counts of the development documents by kind and affair type. Aggregate counts only."""
    counts: collections.Counter = collections.Counter()
    n = 0
    for rel in REFERENCE_FILES:
        docs = json.loads((ROOT / rel).read_text(encoding="utf-8"))["documents"]
        for doc_id, e in docs.items():
            n += 1
            f = e["fields"]["affair_type"]
            vals = f.get("values") or []
            t = vals[0] if f.get("status") == "reference" and vals else "none"
            s1 = (json.loads((ROOT / "daten/gj/rules" / f"{doc_id}.json").read_text(encoding="utf-8"))
                  .get("document") or {}).get("s1") or {}
            if s1.get("rule_role") != e["s1_role"]:
                raise CascadeError("the rule role of the reference file and of the rule file are not equal")
            counts[(kind_of_role(e["s1_role"], s1.get("rule_id")), t)] += 1
    return {"documents": n, "paths": counts}


def paths_table(top: int) -> str:
    pc = path_counts()
    rows = ["| Path (kind x type) | Documents | Steps that apply | Slots that apply (of 87) | Written today "
            "(from a PDF block) | Asked by the new Apertus questions | Design only | Register only | Not applicable |",
            "|---|---|---|---|---|---|---|---|---|"]
    shown = 0
    for (kd, t), n in sorted(pc["paths"].items(), key=lambda x: (-x[1], x[0]))[:top]:
        r = labels_for(kd, t)
        c = r["counts"]
        st = [k for k, v in r["steps"].items() if v["applies"]]
        steps = ", ".join(f"`{x}`" for x in st) if st else "none"
        rows.append(f"| `{kd}` x `{t}` | {n:,} | {steps} | {c['apply']} | {c['today']} ({c['today_pdf_block']}) | "
                    f"{c['ask']} | {c['design_only']} | {c['register_only']} | {c['not_applicable']} |")
        shown += n
    rows.append(f"\nDocuments: {pc['documents']:,}. Paths with 1 or more documents: {len(pc['paths'])}. "
                f"The {min(top, len(pc['paths']))} rows hold {shown:,} documents.")
    return "\n".join(rows)


# ------------------------------------------------------------------------------------------------ tables for the document
def tables() -> str:
    c = cascade()
    out = []
    kinds, types = list(c["kinds"]), list(c["affair_types"])
    out.append("### steps by kind\n")
    out.append("| Step | " + " | ".join(f"`{x}`" for x in kinds) + " |")
    out.append("|---|" + "---|" * len(kinds))
    for st in c["steps"]:
        out.append(f"| `{st}` | " + " | ".join("yes" if st in c["kind_steps"][x]["steps"] else "no" for x in kinds) + " |")
    out.append("\n### steps by type\n")
    out.append("| Step | " + " | ".join(f"`{x}`" for x in types) + " |")
    out.append("|---|" + "---|" * len(types))
    for st in c["steps"]:
        cells = []
        for t in types:
            ok = st in c["type_steps"][c["affair_types"][t]["steps"]]["steps"]
            cond = (c["type_step_conditions"].get(t) or {}).get(st)
            cells.append("condition" if cond else ("yes" if ok else "no"))
        out.append(f"| `{st}` | " + " | ".join(cells) + " |")
    out.append("\n### counts of all paths\n")
    out.append("| Kind | " + " | ".join(f"`{x}`" for x in types) + " |")
    out.append("|---|" + "---|" * len(types))
    for kd in kinds:
        out.append(f"| `{kd}` | " + " | ".join(str(labels_for(kd, t)["counts"]["apply"]) for t in types) + " |")
    by = collections.Counter(r["basis"] for r in c["rules"])
    out.append(f"\nrules: {len(c['rules'])}; " + ", ".join(f"{k} {by[k]}" for k in BASES))
    return "\n".join(out)


def print_labels(r: dict) -> None:
    c = r["counts"]
    print(f"path: {r['kind']} x {r['affair_type']} (class {r['i95_class']}, profile {r['profile']})")
    print(f"slots of the 87: apply {c['apply']}, written today {c['today']} (from a PDF block {c['today_pdf_block']}), "
          f"asked {c['ask']}, design only {c['design_only']}, register only {c['register_only']}, "
          f"not applicable {c['not_applicable']}")
    print(f"questions: {', '.join(r['questions'])}; block options: {', '.join(r['block_options'])}")

    def show(nodes: list) -> None:
        for n in nodes:
            flags = ("today " if n["today"] else "") + (f"ask={n['ask']} " if n["ask"] else "")
            vals = f" values={','.join(n['values']['values'])}" if n.get("values") else ""
            print(f"    {n['path']}  [{n['requirement']}; {n['origin']}; {flags.strip() or 'design or register'}]"
                  f" {','.join(n['rules'])}{vals}")

    print("affair:")
    show(r["affair"]["slots"])
    for name, st in r["steps"].items():
        cond = f"; condition: {st['condition']}" if st["condition"] else ""
        state = "built" if st["built"] else "design only"
        print(f"step {name}: {st['reason']} ({', '.join(st['rules'])}; {state}{cond})")
        show(st["slots"])
    if r["not_applicable"]:
        print("cut by a rule:")
        for x in r["not_applicable"]:
            print(f"    {x['path']}  ({x['reason']}; {','.join(x['rules'])})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("labels")
    p.add_argument("--kind", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("paths")
    p.add_argument("--top", type=int, default=18)
    sub.add_parser("tables")
    args = ap.parse_args()
    if args.cmd == "check":
        res = self_check()
        for name, ok, detail in res:
            print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
        sha = hashlib.sha256(source_path("I95").read_bytes()).hexdigest()
        bad = sum(1 for _, ok, _ in res if not ok)
        print(f"I95 SHA-256: {sha}")
        print(f"cascade file SHA-256: {hashlib.sha256(CASCADE.read_bytes()).hexdigest()}")
        print(f"checks: {len(res)}, failed: {bad}")
        return 1 if bad else 0
    if args.cmd == "labels":
        r = labels_for(args.kind, args.type)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            print_labels(r)
        return 0
    if args.cmd == "paths":
        print(paths_table(args.top))
        return 0
    print(tables())
    return 0


if __name__ == "__main__":
    sys.exit(main())

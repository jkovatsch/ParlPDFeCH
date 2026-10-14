"""The cascade reader: the 7 head values of a document, read after the LABEL SELECTION of the cascade of eCH-0295.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent, 13.10.2026 (round 3). Status: EXCEPTION, NOT RELEASED. No human checked this file. This file changes no
existing file. It registers no reader. The import of this file by `m11_values_base.load_rule_modules` has no effect
on a result.

1 Task
  The rule modules read each of the 7 fields from each document. The cascade (`crisp-dm/04-modeling/ech-cascade.md`,
  `src/m11_cascade.yaml`, `src/m11_cascade.py`) says which slots a document of a kind can state. This reader
  applies that selection:
    stage 0  the kind of the document. For now the kind comes from the rule chain: the S1 rule role and the S1
             rule id of the rule file, mapped by `m11_cascade.kind_of_role` (rule R2, key `kinds` of the YAML
             file). The functions take the kind as an argument. Thus a model answer can replace it later.
    stage 1  the affair type: the result of the type reader. A type that is not found gives the type `none`
             (rule R6) for the stages 2 and 3.
    stage 3  for each of the 7 fields: `m11_cascade.labels_for(kind, type)` says if the slot of the field applies.
             If it applies, the field reader runs. If it does not apply, the record is "not searched in this kind
             of document" with the ids of the cascade rules.

2 Slot of each field
  affair_type      Affair.affair_type                 affair_number  Affair.affair_number
  title            Affair.title                       submission_date  Submission.submission_date
  sponsor          Submission.sponsorship             response_date  ResponseStep.date_end_actual
  responder        ResponseStep.responder

3 Rules of this reader (ids V1 to V5; the ids R1 to R53 are those of the cascade)
  V1  The kind is not known (a document with no rule file and no kind argument). Then the reader makes no
      selection: each field is searched.
  V2  NOT IN USE since version 2 of this reader (13.10.2026, decision D2 of the main agent). V2 was decision (a)
      of round 3: the slot Submission.sponsorship applies to the kind `response`, because the head of a response
      document can state the author of the proposal ("Interpellation von X"). Rule R30 of the cascade
      (`m11-cascade-2`) now gives this slot to the kind `response`. Thus the selection is the same, and the rule
      ids of the record are those of the cascade (R19, R25, R30, R38). Submission.texts stays not applicable for
      the kind `response`. The values, the tiers and the spans of each record did not change.
  V3  DECISION (b) of round 3. For the kinds `proposal` and `executive_proposal` the executive response step does
      not apply (R18, R21, R25, R31). Thus the responder is not searched, and the body that a proposal addresses is
      not written as a responder. The responder reader runs one time for these kinds only to keep the addressee:
      each candidate of the reader with a tier of ADDRESSEE_TIERS goes into the list `others` of the record
      "not searched". No other candidate of that call is kept.
  V5  DECISION of the main agent, 13.10.2026 (version 3 of this reader). The S1 rule id D0 says that no rule of
      the rule chain decided the role. The kind is then `other` only by default. Since the rule files come from
      the PDF alone (`daten/gj/rules_pdf`, no export field), 280 of the 1,793 development documents have the id
      D0. For a document with the id D0 the kind comes from 2 facts that the readers find in the PDF:
        sub  the type reader gives a type of a proposal of a member (each list value but `draft_decree`);
        rsp  the responder reader gives a value with a tier that is not a tier of ADDRESSEE_TIERS and not a
             tier of V5_WEAK_TIERS (`rsp_response_text`: a phrase that can refer to a different answer).
      sub and rsp: `combined`. Only sub: `proposal`. Only rsp, and the tier is a tier of V5_RESPONSE_TIERS (an
      explicit response cue, `rsp_response_cue`): `response`. Else the kind stays `other`.
      A type `draft_decree` changes nothing: the kind stays `other`. The function is `v5_kind`. The key
      `kind_source` holds the kind of the rule chain and the 2 facts. Cause: a kind by default must not stop the
      search of the submission step and of the response step. V5 reads no export field.
      Version 4 of this reader (13.10.2026, 21:00) made the kind `response` narrower. In version 3 each responder
      tier but the addressee tier gave it. A skeptic and an examiner found that a signature or a minutes cue of
      the executive is also printed in a decision of the executive that answers no proposal: of the 40 development
      documents with the kind `response` by version 3, the reference type was `draft_decree` for 22.
  The cascade gives no submission step to the kinds `committee_report`, `minutes` and `other` (R22, R23, R24).
  Thus the submission date and the first author are not searched there. The 3 slots of the affair are searched
  for each kind.

4 Output of `read_document` and form of the values file (addendum G version 2, chapter 5.4)
  {"header": {...}, "documents": {"<doc id>": {"language", "s1_role", "kind", "kind_source", "affair_type_of_the_cascade",
  "fields": {<registry id>: record}}}}
  A record is the `to_json` form of the base module with ONE more key, `cascade`:
    {"searched": true | false, "rules": [ids], "slot": "<class>.<slot>", "note": "..."}
  A record that was not searched is: {"field", "found": false, "result": "not searched in this kind of document",
  "reason": "not_in_document_type", "detail", "others", "cascade"}.
  The two measurement tools read the keys found, normalised, tier, value and reason of a record. They do not read
  the key `cascade` and they do not read the key `result`. For them a record that was not searched is a record
  with no value (outcome not found or no reference). The table of round 3 gives the count "not searched" apart.
  The extraction tool `src/m11_values_run.py` has a strict key check (`form_check`). It is not used for this file.

5 Limits
  The S1 rule ids O1, O2, P2 and R1 have a condition on 3 fields that the stored rule files took from the export.
  The rule files of this reader (`daten/gj/rules_pdf`, tool `src/m11_rules_pdf.py`) give the S1 rule empty fields,
  as the package does. P2 and R1 cannot occur then. O1 and O2 come from a heading of the PDF. The run record
  counts the documents with `Doc.s1_export_condition`.
  Rule V5 gives a kind to a document with the id D0. It does not change the block roles of the rule file. A
  document with the kind `response` by V5 can have text blocks with the rule role `submitted`.
  The rule role is a rule result. A wrong rule role gives a wrong selection (for example a combined document that
  the rule chain calls a proposal: its responder is then not searched).

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_cascade.py selftest
  uv run --offline --frozen --no-sync python src/m11_values_cascade.py table
  uv run --offline --frozen --no-sync python src/m11_values_cascade.py run --out daten/gj_values/round3/values_dev_all.json
  uv run --offline --frozen --no-sync python src/m11_values_cascade.py run --out FILE --no-selection   (diagnosis)
The command run reads the 1,793 development documents only (guard `m10_guard`, split dev). It reads no export
record and no reference file. It calculates no agreement value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_cascade as casc  # noqa: E402
import m11_values_base as vb  # noqa: E402

VERSION = "m11-values-cascade-4"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
STATUS = "EXCEPTION, NOT RELEASED"
OPENING_FILE = ROOT / "daten/gj_values/opening.json"
OPENING_SIX = ("src/m11_values_type_number.py", "src/m11_values_title.py", "src/m11_values_dates_responder.py",
               "src/m11_values_sponsor.py", "src/m11_values_base.py", "src/m11_value_norm.py")
RULE_MODULES = ("m11_values_dates_responder", "m11_values_sponsor", "m11_values_title", "m11_values_type_number")
MARK = "after the opening"
N_DEV = 1793

# registry id -> (class, slot) of the cascade
FIELD_SLOT = {"affair_type": ("Affair", "affair_type"), "title": ("Affair", "title"),
              "affair_number": ("Affair", "affair_number"), "submission_date": ("Submission", "submission_date"),
              "response_date": ("ResponseStep", "date_end_actual"), "responder": ("ResponseStep", "responder"),
              "sponsor": ("Submission", "sponsorship")}
FIELD_STEP = {"submission_date": "submission", "sponsor": "submission", "response_date": "executive_response",
              "responder": "executive_response"}
NOT_SEARCHED = "not searched in this kind of document"
ADDRESSEE_TIERS = ("rsp_addressee_cue",)          # tier of the responder reader: the body that a proposal addresses
ADDRESSEE_KINDS = ("proposal", "executive_proposal")
V5_RULE_IDS = ("D0",)                             # S1 rule ids with no decision of the rule chain (rule V5)
V5_PROPOSAL_TYPES = ("motion", "postulate", "motion_and_postulate", "motion_then_postulate", "interpellation",
                     "request", "question", "parliamentary_initiative")
V5_NO_CHANGE_TYPES = ("draft_decree",)
V5_RESPONSE_TIERS = ("rsp_response_cue",)         # explicit response cue: alone it gives the kind `response`
V5_WEAK_TIERS = ("rsp_response_text",)            # a phrase that can refer to a different answer: no response cue

_SELECTION: dict = {}


def kinds() -> tuple[str, ...]:
    return tuple(casc.cascade()["kinds"])


def v5_kind(kind: str, affair_type: str, response_tier: str | None) -> str:
    """Rule V5 as a pure function: the kind of a document with no decision of the rule chain, from the type of
    the type reader (`cascade_type`) and the tier of the responder reader (None: no value)."""
    if affair_type in V5_NO_CHANGE_TYPES:
        return kind
    sub = affair_type in V5_PROPOSAL_TYPES
    rsp = (response_tier is not None and response_tier not in ADDRESSEE_TIERS
           and response_tier not in V5_WEAK_TIERS)
    if sub and rsp:
        return "combined"
    if sub:
        return "proposal"
    if rsp and response_tier in V5_RESPONSE_TIERS:
        return "response"
    return kind


def kind_of(doc: vb.Doc, strict: bool = False, registry: dict | None = None) -> tuple[str | None, dict]:
    """Stage 0: (kind, source). No rule file gives (None, ...): rule V1. Else the kind of the rule chain (rule R2),
    and for a document with a rule id of V5_RULE_IDS the kind of rule V5 (2 reads of the PDF, no export field)."""
    if doc.s1_role is None:
        return None, {"from": "none", "s1_role": None, "s1_rule_id": doc.s1_rule_id, "rule": "V1"}
    kind = casc.kind_of_role(doc.s1_role, doc.s1_rule_id)
    source = {"from": "rule chain (S1 rule role and rule id)", "s1_role": doc.s1_role, "s1_rule_id": doc.s1_rule_id,
              "s1_export_condition": doc.s1_export_condition, "rule": "R2"}
    if doc.s1_rule_id not in V5_RULE_IDS:
        return kind, source
    a_type = cascade_type(vb.read_field(doc, "affair_type", strict, registry))
    rsp = vb.read_field(doc, "responder", strict, registry)
    tier = rsp.tier if getattr(rsp, "found", False) else None
    new = v5_kind(kind, a_type, tier)
    source["v5"] = {"kind_of_the_rule_chain": kind, "affair_type_read": a_type, "responder_tier_read": tier,
                    "changed": new != kind}
    if new != kind:
        source["from"] = "rule V5 (type word and response cue of the PDF; the rule chain made no decision)"
        source["rule"] = "V5"
    return new, source


def cascade_type(type_record) -> str:
    """Stage 1: the list value of the type reader, or `none` (rule R6)."""
    v = type_record.normalised if getattr(type_record, "found", False) else None
    return v if v in casc.cascade()["affair_types"] and v != "none" else "none"


def selection(kind: str | None, affair_type: str) -> dict:
    """{registry id: {"searched", "rules", "slot", "note"}} for a kind and an affair type (stages 2 and 3)."""
    key = (kind, affair_type)
    if key in _SELECTION:
        return _SELECTION[key]
    out = {}
    if kind is None:
        for f, (cls, slot) in FIELD_SLOT.items():
            out[f] = {"searched": True, "rules": ["V1"], "slot": f"{cls}.{slot}",
                      "note": "the kind is not known: no selection"}
        _SELECTION[key] = out
        return out
    lab = casc.labels_for(kind, affair_type)
    live = {}
    for n in lab["affair"]["slots"] + [n for st in lab["steps"].values() for n in st["slots"]]:
        live.setdefault((n["class"], n["slot"]), n)
    cut = {x["path"].split("/")[-1]: x for x in lab["not_applicable"]}
    for f, (cls, slot) in FIELD_SLOT.items():
        full = f"{cls}.{slot}"
        step = FIELD_STEP.get(f)
        if (cls, slot) in live:
            rules = list(live[(cls, slot)]["rules"])
            if step:
                rules = [lab["steps"][step]["rules"][0], "R25", *rules]
            out[f] = {"searched": True, "rules": _uniq(rules), "slot": full, "note": "the slot applies"}
        elif step and not lab["steps"][step]["applies"]:
            st = lab["steps"][step]
            rules = [st["rules"][0], "R25"] + (["R31"] if step == "executive_response" else [])
            out[f] = {"searched": False, "rules": _uniq(rules), "slot": full,
                      "note": f"the step {step} does not apply: {st['reason']}"}
        elif full in cut:
            out[f] = {"searched": False, "rules": _uniq(cut[full]["rules"]), "slot": full,
                      "note": f"the cascade cuts the slot for this {cut[full]['reason']}"}
        else:
            raise casc.CascadeError(f"the cascade gives no state for the slot {full} at ({kind}, {affair_type})")
    if kind in ADDRESSEE_KINDS and not out["responder"]["searched"]:
        out["responder"] = dict(out["responder"], rules=_uniq(out["responder"]["rules"] + ["V3"]),
                                note=out["responder"]["note"] + "; decision (b) of round 3: the addressed body is "
                                "kept as a candidate in the list others, it is not a responder")
    _SELECTION[key] = out
    return out


def _uniq(xs: list) -> list:
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


def _not_searched(field: str, kind: str, sel: dict, others: list) -> dict:
    return {"field": field, "found": False, "result": NOT_SEARCHED, "reason": "not_in_document_type",
            "detail": f"kind {kind}: {sel['note']} (cascade rules {', '.join(sel['rules'])})",
            "others": others, "cascade": dict(sel)}


def _addressee(doc: vb.Doc, strict: bool, registry: dict | None) -> list:
    """Rule V3: the candidates of the responder reader with a tier of ADDRESSEE_TIERS (JSON form, best first)."""
    res = vb.read_field(doc, "responder", strict, registry)
    cands = ([res] if res.found else []) + list(res.others)
    return [dict(c.to_json(False), kept_as="addressee of the proposal (rule V3); not a responder")
            for c in cands if c.tier in ADDRESSEE_TIERS]


def read_document(doc: vb.Doc, kind: str | None = "from_rule_chain", strict: bool = True, select: bool = True,
                  registry: dict | None = None) -> dict:
    """The 7 records of a document after the label selection. `kind`: one key of the kinds of the cascade, None
    (not known: rule V1) or "from_rule_chain" (default: stage 0 from the S1 rule role). `select=False` searches
    each field (diagnosis only). The result has no agreement value."""
    if kind == "from_rule_chain":
        kind, source = kind_of(doc, strict, registry)
    else:
        if kind is not None and kind not in kinds():
            raise casc.CascadeError(f"unknown kind {kind!r}; the kinds are {list(kinds())}")
        source = {"from": "argument", "rule": "V1" if kind is None else "argument"}
    t_res = vb.read_field(doc, "affair_type", strict, registry)
    a_type = cascade_type(t_res)
    sel = selection(kind if select else None, a_type)
    fields = {}
    for f in vb.FIELDS:
        s = sel[f]
        if s["searched"]:
            res = t_res if f == "affair_type" else vb.read_field(doc, f, strict, registry)
            rec = res.to_json()
            rec["cascade"] = dict(s)
        else:
            others = _addressee(doc, strict, registry) if (f == "responder" and kind in ADDRESSEE_KINDS) else []
            rec = _not_searched(f, kind, s, others)
        fields[f] = rec
    return {"kind": kind, "kind_source": source, "affair_type_of_the_cascade": a_type, "fields": fields}


def selection_table() -> dict:
    """{kind: {registry id: searched}} for the type motion and the note if a type changes a row."""
    types = [t for t in casc.cascade()["affair_types"]]
    out, by_type = {}, []
    for k in kinds():
        base = {f: v["searched"] for f, v in selection(k, "motion").items()}
        out[k] = {f: {"searched": v["searched"], "rules": v["rules"]} for f, v in selection(k, "motion").items()}
        for t in types:
            if {f: v["searched"] for f, v in selection(k, t).items()} != base:
                by_type.append([k, t])
    return {"by_kind": out, "pairs_of_kind_and_type_that_differ_from_the_type_motion": by_type}


# ------------------------------------------------------------------ the run on the development documents

def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def opening_mark() -> dict:
    """The mark of chapter 6.5 of addendum G: the 6 files of the opening against daten/gj_values/opening.json."""
    now = {f: sha256(ROOT / f) for f in OPENING_SIX}
    if not OPENING_FILE.is_file():
        return {"opening_file_exists": False, "mark": None, "files_now": now, "changed": []}
    then = json.loads(OPENING_FILE.read_text(encoding="utf-8")).get("files") or {}
    changed = [f for f in OPENING_SIX if then.get(f) != now[f]]
    return {"opening_file_exists": True, "mark": MARK if changed else None, "files_now": now, "changed": changed,
            "opening_time": json.loads(OPENING_FILE.read_text(encoding="utf-8")).get("time")}


def run(out: Path, select: bool) -> int:
    t_all = time.perf_counter()
    names = vb.load_rule_modules()
    if not set(RULE_MODULES) <= set(names) or set(vb.REGISTRY) != set(vb.FIELDS):
        raise SystemExit(f"rule modules {names}: not one reader for each of the 7 fields")
    for f in vb.FIELDS:
        if vb.REGISTRY[f].__module__ not in RULE_MODULES:
            raise SystemExit(f"{f}: the reader is not a reader of a rule module")
    part_of = {d: v["part"] for d, v in vb.folds()["documents"].items()}
    ids = sorted(part_of, key=int)
    if len(ids) != N_DEV:
        raise SystemExit(f"folds.json: {len(ids)} documents, expected {N_DEV}")
    guard = vb.guard_check(ids)
    if guard["refused"] or guard["by_split"].get("dev") != N_DEV:
        raise SystemExit(f"guard: {guard}")
    opening = opening_mark()
    if not opening["opening_file_exists"]:
        raise SystemExit("daten/gj_values/opening.json does not exist: the closed part stays closed")
    documents, failures = {}, []
    by_kind, searched, export_cond, addressee = Counter(), {f: Counter() for f in vb.FIELDS}, Counter(), 0
    v5_counts = Counter()
    for d in ids:
        doc = vb.load_doc(d, apertus_roles=False, allow_closed=True)
        raw = json.loads((vb.DOCS_DIR / f"{d}.json").read_text(encoding="utf-8"))
        try:
            res = read_document(doc, strict=True, select=select)
        except Exception as e:  # noqa: BLE001
            failures.append({"doc": d, "error": f"{type(e).__name__}: {e}"[:200]})
            continue
        for f, rec in res["fields"].items():
            if rec["found"] and rec["tier"].startswith("apertus"):
                failures.append({"doc": d, "error": f"{f}: a result of an Apertus tier in the rules mode"})
            searched[f]["searched" if rec["cascade"]["searched"] else "not_searched"] += 1
        addressee += bool(res["fields"]["responder"]["others"]) and not res["fields"]["responder"]["cascade"]["searched"]
        by_kind[str(res["kind"])] += 1
        export_cond[str(res["kind"])] += bool(doc.s1_export_condition)
        if "v5" in res["kind_source"]:
            v5_counts[f"{res['kind_source']['v5']['kind_of_the_rule_chain']} -> {res['kind']}"] += 1
        documents[d] = {"language": raw["language"] if "language" in raw else None, "s1_role": doc.s1_role,
                        "kind": res["kind"], "kind_source": res["kind_source"],
                        "affair_type_of_the_cascade": res["affair_type_of_the_cascade"], "fields": res["fields"]}
    src = SCRIPT.parent
    header = {"version": VERSION, "base_version": vb.VERSION, "status": STATUS, "mark": opening["mark"],
              "part": "all development documents (the 36 parliaments of the open part and the 8 parliaments that "
                      "were closed until the opening)",
              "documents": len(documents), "form": "addendum G version 2, chapter 5.4, with the key cascade in each "
              "record and the keys kind, kind_source and affair_type_of_the_cascade in each document",
              "mode": "rules only, strict; label selection of the cascade " + ("ON" if select else "OFF (diagnosis)"),
              "kind": "from the rule chain (S1 rule role and rule id; m11_cascade.kind_of_role); for a document "
                      "with the S1 rule id D0 from rule V5 (type word and response cue of the PDF)",
              "rule_files": str(vb.RULES_DIR.relative_to(ROOT)),
              "cascade_version": casc.cascade()["version"],
              "rules_of_the_reader": {"V1": "kind not known: no selection",
                                      "V2": "not in use: rule R30 of the cascade gives Submission.sponsorship to "
                                            "the kind response (decision D2)",
                                      "V3": "kinds proposal and executive_proposal: the responder is not searched; "
                                            "the addressed body is kept in the list others (decision b)",
                                      "V5": "S1 rule id D0 (no decision of the rule chain): the kind comes from "
                                            "the type word and a response cue of the PDF; the kind response only "
                                            "for an explicit response cue (version 4)"},
              "selection": selection_table() if select else None,
              "sha256": {"src/m11_values_cascade.py": sha256(SCRIPT), "src/m11_cascade.py": sha256(src / "m11_cascade.py"),
                         "src/m11_cascade.yaml": sha256(src / "m11_cascade.yaml"),
                         "daten/gj_values/folds.json": sha256(vb.FOLDS_FILE),
                         **{f"src/{n}.py": sha256(src / f"{n}.py") for n in RULE_MODULES}},
              "opening": opening,
              "counts": {"by_kind": dict(sorted(by_kind.items())),
                         "documents_whose_s1_rule_id_has_a_condition_on_export_fields_by_kind": dict(sorted(export_cond.items())),
                         "records_by_field": {f: dict(sorted(c.items())) for f, c in searched.items()},
                         "responder_records_not_searched_with_an_addressee_candidate": addressee,
                         "documents_of_rule_v5_by_kind_change": dict(sorted(v5_counts.items())),
                         "strict_failures": len(failures)}}
    if failures:
        print(json.dumps({"strict_failures": failures[:20], "count": len(failures)}, ensure_ascii=False, indent=1))
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps({"header": header, "documents": documents}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    tmp.replace(out)
    print(json.dumps({"out": str(out), "sha256": sha256(out), "documents": len(documents), "mark": opening["mark"],
                      "files_changed_after_the_opening": opening["changed"], "counts": header["counts"],
                      "time_s": round(time.perf_counter() - t_all, 1)}, ensure_ascii=False, indent=1))
    return 0


# ------------------------------------------------------------------ self-test

EXPECTED_SEARCH = {     # kind -> the registry ids that are NOT searched
    "proposal": {"response_date", "responder"}, "executive_proposal": {"response_date", "responder"},
    "response": set(), "combined": set(),
    "committee_report": {"submission_date", "sponsor", "response_date", "responder"},
    "minutes": {"submission_date", "sponsor", "response_date", "responder"},
    "other": {"submission_date", "sponsor", "response_date", "responder"},
}
SELFTEST_DOCS = ("22700", "684152")     # open development documents of the base self-test: a proposal, a combined


def selftest() -> dict:
    bad: list[str] = []

    def want(name, got, expected):
        if got != expected:
            bad.append(f"{name}: got {got!r}, expected {expected!r}")

    want("kinds", set(kinds()), set(EXPECTED_SEARCH))
    for k, off in EXPECTED_SEARCH.items():
        for t in casc.cascade()["affair_types"]:
            sel = selection(k, t)
            want(f"selection({k},{t})", {f for f, v in sel.items() if not v["searched"]}, off)
            for f, v in sel.items():
                if not v["rules"]:
                    bad.append(f"selection({k},{t}).{f}: no rule id")
    want("R30.response", selection("response", "motion")["sponsor"]["rules"], ["R19", "R25", "R30", "R38"])
    want("R30.combined", selection("combined", "motion")["sponsor"]["rules"], ["R20", "R25", "R30", "R38"])
    want("V2.not_in_use", [k for k in kinds() for f, v in selection(k, "motion").items() if "V2" in v["rules"]], [])
    want("V3", "V3" in selection("proposal", "none")["responder"]["rules"], True)
    want("V1", {v["searched"] for v in selection(None, "none").values()}, {True})
    want("V5.types", set(V5_PROPOSAL_TYPES) | set(V5_NO_CHANGE_TYPES) | {"none"}, set(casc.cascade()["affair_types"]))
    want("V5.cases", [v5_kind("other", t, r) for t, r in (
        ("motion", None), ("motion", "rsp_signature"), ("none", "rsp_response_cue"), ("none", "rsp_addressee_cue"),
        ("interpellation", "rsp_addressee_cue"), ("draft_decree", "rsp_signature"), ("none", None),
        ("none", "rsp_signature"), ("none", "rsp_minute_cue"), ("none", "rsp_response_text"),
        ("draft_decree", "rsp_response_cue"), ("motion", "rsp_response_text"), ("postulate", "rsp_response_cue"))],
         ["proposal", "combined", "response", "other", "proposal", "other", "other",
          "other", "other", "other", "other", "proposal", "combined"])
    want("V5.kinds", {v5_kind("other", t, r) for t in casc.cascade()["affair_types"]
                      for r in (None, "rsp_signature")} <= set(kinds()), True)
    want("kind_of_role", [casc.kind_of_role(r, i) for r, i in (("proposal", "P1"), ("proposal", "E1"), ("response", "A2"),
                                                              ("combined", "A1"), ("committee", "C1"),
                                                              ("minutes", "M1"), ("other", "D0"))],
         ["proposal", "executive_proposal", "response", "combined", "committee_report", "minutes", "other"])
    vb.load_rule_modules()
    docs = {}
    for d in SELFTEST_DOCS:
        doc = vb.load_doc(d)
        res = read_document(doc)
        full = read_document(doc, select=False)
        k = res["kind"]
        want(f"{d}.fields", list(res["fields"]), list(vb.FIELDS))
        for f, rec in res["fields"].items():
            if rec["cascade"]["searched"]:
                plain = vb.read_field(doc, f).to_json()
                want(f"{d}.{f}.same_as_the_reader", {x: y for x, y in rec.items() if x != "cascade"}, plain)
            else:
                want(f"{d}.{f}.form", (rec["found"], rec["result"], rec["reason"] in vb.REASONS), (False, NOT_SEARCHED, True))
                if f not in EXPECTED_SEARCH[k]:
                    bad.append(f"{d}.{f}: not searched, but the kind {k} has the slot")
            want(f"{d}.{f}.full", full["fields"][f]["cascade"]["searched"], True)
        # the kind as an argument (a model answer can replace the rule chain)
        as_other = read_document(doc, kind="other")
        want(f"{d}.kind_argument", {f for f, r in as_other["fields"].items() if not r["cascade"]["searched"]},
             EXPECTED_SEARCH["other"])
        as_resp = read_document(doc, kind="response")
        want(f"{d}.kind_response", {f for f, r in as_resp["fields"].items() if not r["cascade"]["searched"]}, set())
        docs[d] = {"kind": k, "affair_type_of_the_cascade": res["affair_type_of_the_cascade"],
                   "not_searched": sorted(f for f, r in res["fields"].items() if not r["cascade"]["searched"]),
                   "addressee_candidates": len(res["fields"]["responder"]["others"])
                   if not res["fields"]["responder"]["cascade"]["searched"] else None}
    want("22700.kind", docs["22700"]["kind"], "proposal")
    want("684152.kind", docs["684152"]["kind"], "combined")
    for d in SELFTEST_DOCS:      # rule V5 applies only to the rule id D0: these 2 documents have another rule id
        k5, s5 = kind_of(vb.load_doc(d))
        want(f"{d}.V5.not_applied", ("v5" in s5, s5["rule"]), (False, "R2"))
    try:
        read_document(vb.load_doc("22700"), kind="no_such_kind")
        bad.append("an unknown kind was accepted")
    except casc.CascadeError:
        pass
    return {"version": VERSION, "selection": {k: sorted(v) for k, v in EXPECTED_SEARCH.items()}, "documents": docs,
            "registered_readers_of_this_module": sorted(f for f, fn in vb.REGISTRY.items() if fn.__module__ == __name__),
            "failed": bad, "result": "all cases as expected" if not bad else f"{len(bad)} cases NOT AS EXPECTED"}


def main() -> int:
    ap = argparse.ArgumentParser(description="the cascade reader of the 7 head values (round 3)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("table")
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--no-selection", action="store_true", help="search each field (diagnosis only)")
    a = ap.parse_args()
    if a.cmd == "run":
        return run(a.out.resolve(), not a.no_selection)
    if a.cmd == "table":
        print(json.dumps(selection_table(), ensure_ascii=False, indent=1))
        return 0
    res = selftest()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 1 if res["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())

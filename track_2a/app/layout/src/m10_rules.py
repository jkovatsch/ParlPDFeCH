"""Rules without CSCS for gate GJ: the frozen nos4 chain on each Docling document that is not a test document, with a
rule option and a rule tier for each Docling block.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream F
of the plan `crisp-dm/00-cross-cutting/plan-full-conversion.md` (chapter 4 items 2 to 4, chapter 5.2 item 3).
Phase 4 (modeling) and phase 6 (deployment), gate GJ (OPEN). Status: EXCEPTION (process rule 10). This file gives
no gate result and no quality value.

1 Chain (each step calls the stored function by import; no file of another step is changed)
  The chain of `m05_iso_runner.run_document` (frozen runner `iso-runner-1`):
  1. Atoms and fixed answers (rules R1, R3, R4, R5): `m05_iso_runner.runner_doc`.
  2. S1 rule: `m03_sub_s1_role.rule` on the atoms and the 3 export fields of the PDF index row.
  3. S1 combined: the rule role when the rule id is in `SURE_IDS` (all rule ids except R1). For the rule id R1
     the frozen runner asks Apertus on CSCS. This file sends no CSCS request: the document gets the flag
     `needs_apertus` (step D1 of the plan decides it), and the chain uses the rule role as a provisional
     combined role. The output also gives the chain for each D1 option (`by_d1`), so the cascade can take the
     variant of the D1 decision.
  4. S2 rule: `m03_sub_s2_switch.rule_predict`.
  5. S3 "text" for each atom, no S4 (method nos4).
  6. S5 rule and composition: `m03_sub_assemble.assemble` with `CHOSEN_OPTION` (s4_over_s3 and s1_start).
  7. Collapse map, block form and scope rules L8 and L9: `m03_ladder.converter_view`.
  The S5 paragraphs (rule and sure flag) come from a second call of `m03_sub_s5_type.predict_rule` on the same
  composed answers; the composition with these S5 types must give the nos4 answers again (else stop).

2 Output for each document (`daten/gj/rules/<doc>.json`, no text of the document)
  document  the S1 rule role, the S1 rule id, the combined role and its source (rule | rule_provisional |
            stored_apertus), `needs_apertus`; the D1 option of the rule role (proposal A, response B,
            combined C, minutes, committee and other D); the D1 option of the composed answers (families
            `SPONSOR` and `EXECUTIVE`, `m10_score.d1_of_answers`); the S2 runs and the start reason; the claim
            flags of L8 and L9 with the abstention reason.
  blocks    for each Docling block in reading order: `option` (one of the 6 options of interface 4, by the
            majority rule of `m10_score.block_option` over the nos4 answers of its atoms), `mixed`, `tier`,
            `tier_detail`, the count of atoms, the count of each E20 answer, `claimed` (the L9 claim flag of the
            document).
  atoms     the atom ids, the nos4 answers and the L9 answers (map SLOT_NOTITLE and block form).
  by_d1     only for `needs_apertus`: for each D1 option (A proposal, B response, C combined, D other) the
            option of each block, the L9 claim flag and the SHA-256 of the nos4 answers.

3 Tier of a block
  The atoms that carry the option of the block decide the tier:
  fixed:<ids>                all these atoms have a fixed answer; ids = the fixed rules (R1, R3, R4, R5)
  s2_switch:<kind>           the S2 run of the first such atom starts at a strong cue after the start
                             (kind: answer_label, answer_announce, sponsor_label, speaker, decision)
  s2_start_cue:<kind>        the start run, and its family comes from the first strong cue
  s2_start_sponsor_evidence  the start run is `SPONSOR` because sponsor evidence comes before the first cue
  s2_start_head_labels       the start run is `SPONSOR` because only answer labels of the head exist
  s2_start_default           the start run is the default `SPONSOR` (no strong cue), S1 did not change it
  s1_start:<S1 rule id>      the start run has the family of the S1 combined role (assembly option s1_start)
  `tier_detail` gives the parts: the family source, the S2 candidate atom and its kinds, the S1 rule id, the S5
  rule and sure flag of the paragraph, the fixed rules of the block.

4 Guards (process rule 6) and admission
  1. Each document passes `m10_score.split_of`: the atom file and the Docling file exist in `daten/iso`
     (explicit paths, so the fallbacks of `m03_iso_paths` are never reached), the id is in no list of test documents,
     the parliament is a Training or Validierung parliament of `split.csv`. The split is dev, validation or
     group7 (a group 7 parliament). The 8 documents of the final group 7 of gate 3a version 3 (`gruppen.csv`
     group 7) need `--allow-final-group7`.
  2. A document of `m03_sub_common.load()` is admitted as in the runner ("known"). For each other document,
     the context `admitted` widens the guard `m03_sub_common._check_allowed_doc` only for its id and only
     during its run ("loader"). During each run, the record of the document has no reference answers, and the
     CSCS functions and the prompt text are blocked (`sc.ask`, `sc._env`, `sc.prompt_ids`,
     `sc.document_text` stop the run).

5 Identity check (command `identity`)
  On the 205 dev and eval documents of the frozen runner (`daten/gold/final_v4/runner_identity.json`), pass A
  (no CSCS) compares with the stored values as the runner does: nos4 answers, L9 answers, claim flags L8 and L9,
  S1 rule role and rule id, S1 combined role and source, S2 runs and start flag, export fields. Differences are
  allowed only on documents with the S1 rule id R1 (the CSCS documents); the output lists them. Pass B gives the
  R1 documents the stored Apertus role (`daten/iso/sub/s1_role/apertus_<split>.json`, field role; no request)
  and must give 0 differences on all 205 documents. Output: `daten/gj/runs/m10_rules_identity.json`.

6 Run (command `run`)
  Refused when the identity record is missing, not MET, or made by another version of this file. Writes
  `daten/gj/rules/<doc>.json` and the run record `daten/gj/runs/m10_rules_run.json` (counts, SHA-256 of each
  output and of the imported source files, the FROZEN_FILES check of `m05_gate3a_v4_measure.py`).

Usage (from the project folder):
  `uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python src/m10_rules.py identity`
  `(same uv options) python src/m10_rules.py run --all [--allow-final-group7]`
  `(same uv options) python src/m10_rules.py run --doc <id> ...`
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import json
import re
import sys
import time
from bisect import bisect_right
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
import m05_iso_runner as runner  # noqa: E402  (frozen; imports m03_ladder, m03_sub_common and the sub-tasks)
import m03_ladder as lad  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
import m03_sub_common as sc  # noqa: E402
import m03_sub_s1_role as s1m  # noqa: E402
import m03_sub_s2_switch as s2m  # noqa: E402
import m03_sub_s5_type as s5m  # noqa: E402
import m03_sub_assemble as asm  # noqa: E402
import m03_iso_hilfe as hf  # noqa: E402
import m10_score as ms  # noqa: E402  (options of interface 4, block majority rule, guard split_of)

RULES_VERSION = "m10-rules-1"
RULES_PATH = Path(__file__).resolve()
GJ = ROOT_DIR / "daten/gj"
OUT_DIR = GJ / "rules"
RUNS = GJ / "runs"
IDENTITY_OUT = RUNS / "m10_rules_identity.json"
RUN_OUT = RUNS / "m10_rules_run.json"
STORED_IDENTITY = ROOT_DIR / "daten/gold/final_v4/runner_identity.json"
MEASURE_SCRIPT = ROOT_DIR / "src/m05_gate3a_v4_measure.py"
D1_OF_ROLE = {"proposal": "A", "response": "B", "combined": "C", "minutes": "D", "committee": "D", "other": "D"}
ROLE_OF_D1 = {"A": "proposal", "B": "response", "C": "combined", "D": "other"}
STRONG_KINDS = ("answer_label", "answer_announce", "sponsor_label", "speaker", "decision")
FIXED_RULES = ("R1", "R3", "R4", "R5")


class NoCSCS(RuntimeError):
    """A step tried to use CSCS or the prompt text (refused by this file)."""


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


# ------------------------------------------------------------------ admission (chapter 4)
@contextlib.contextmanager
def admitted(d: str, doc: sc.Doc, known: bool):
    """Copy of the context m05_iso_runner.admitted with two changes: a document outside m03_sub_common.load()
    passes _check_allowed_doc for its own id after the guard of this file; the CSCS functions and the prompt
    text are blocked for all documents."""
    docs = sc.load()
    had, saved_doc = d in docs, docs.get(d)
    if had != known:
        raise SystemExit(f"{d}: admission kind does not agree with m03_sub_common.load()")
    names = ("_check_allowed_doc", "ask", "_env", "prompt_ids", "document_text")
    orig = {n: getattr(sc, n) for n in names}

    def check(x: str) -> None:
        x = str(x)
        if x == d:
            return
        orig["_check_allowed_doc"](x)

    def blocked(*_a, **_k):
        raise NoCSCS("m10_rules sends no CSCS request and reads no prompt text")

    docs[d] = doc
    if not known:
        sc._check_allowed_doc = check
    sc.ask = sc._env = sc.prompt_ids = sc.document_text = blocked
    try:
        yield
    finally:
        for n, f in orig.items():
            setattr(sc, n, f)
        if had:
            docs[d] = saved_doc
        else:
            docs.pop(d, None)


def free_caches() -> None:
    """The speed caches of m03_ladder hold the atoms of each document; clear them after a loader document."""
    clear = getattr(v4.atoms_of, "cache_clear", None)
    if clear:
        clear()
    cache = getattr(lad, "_CARRIED_CACHE", None)
    if isinstance(cache, dict):
        cache.clear()


# ------------------------------------------------------------------ one document
def chain(d: str, doc: sc.Doc, combined_role: str, s2_runs: list, weak: bool, rule_role: str) -> dict:
    """Steps 5 to 7 of chapter 1 for one combined role (inside `admitted`)."""
    lab = {"s1": combined_role, "s2": s2_runs, "s3": {a: "text" for a in doc.ids}, "s4": [], "s2_start_weak": weak}
    nos4 = asm.assemble(d, lab, "rule", dict(runner.NOS4_OPTION))
    s1_start = combined_role in asm.ROLE_FAMILY and len(s2_runs) == 1 and weak
    s2p = [(s2_runs[0][0], asm.ROLE_FAMILY[combined_role])] if s1_start else list(s2_runs)
    base = sc.compose(d, combined_role, s2p, lab["s3"], [], {})
    s5 = s5m.predict_rule(d, base)
    if sc.compose(d, combined_role, s2p, lab["s3"], [], s5["s5"]) != nos4:
        raise SystemExit(f"{d}: the S5 paragraphs do not give the nos4 answers again")
    with runner.runner_signals(d, rule_role, combined_role):
        c8, h8, z8 = lad.converter_view(runner.LEVEL_DEFS["L8"], d, nos4)
        c9, h9, z9 = lad.converter_view(runner.LEVEL_DEFS["L9"], d, nos4)
        conv_role = lad.role(nos4)
    if z8 or z9 or h8 != h9:
        raise SystemExit(f"{d}: L8 and L9 must have no zone and the same answers")
    claims = {}
    for lid, flag in (("L8", c8), ("L9", c9)):
        scope = runner.LEVEL_DEFS[lid]["scope"]
        why = runner.abstain_reason(conv_role, rule_role, combined_role, scope)
        if (why is None) != bool(flag):
            raise SystemExit(f"{d}: abstention reason and claim flag of {lid} do not agree")
        claims[lid] = {"claimed": bool(flag), "scope": scope, "abstention_reason": why}
    return {"nos4": nos4, "l9": h9, "claims": claims, "conv_role": conv_role, "s1_start": bool(s1_start),
            "s5_paragraphs": s5["paragraphs"]}


def start_tier(r2: dict, s1_start: bool, rule_id: str, dec_by_id: dict) -> tuple[str, dict]:
    why = r2["start_reason"]
    if s1_start:
        return f"s1_start:{rule_id}", {"family_source": "s1_start"}
    if why.startswith("no strong cue"):
        return "s2_start_default", {"family_source": "s2_start_default"}
    if why.startswith("only head labels"):
        return "s2_start_head_labels", {"family_source": "s2_start_head_labels"}
    if why.startswith("sponsor evidence"):
        return "s2_start_sponsor_evidence", {"family_source": "s2_start_sponsor_evidence"}
    m = re.match(r"first strong cue (\S+) \(", why)
    if m:
        dec = dec_by_id.get(m.group(1)) or {}
        kind = next((k for k in dec.get("kinds", []) if k in STRONG_KINDS), "unknown")
        return f"s2_start_cue:{kind}", {"family_source": "s2_start_cue", "s2_candidate": m.group(1),
                                        "s2_kinds": dec.get("kinds", [])}
    return "s2_start_other", {"family_source": "s2_start_other", "start_reason": why}


def atom_tiers(ids: list[str], r2: dict, s1_start: bool, rule_id: str) -> list[tuple[str, dict]]:
    """The family tier of each atom position (chapter 3), from the S2 runs and the S2 decisions."""
    pos = {a: i for i, a in enumerate(ids)}
    runs = sorted(((pos[a], f) for a, f in r2["s2"]), key=lambda t: t[0])
    starts = [p for p, _ in runs]
    dec_by_id = {x["id"]: x for x in r2["decisions"]}
    tiers = []
    for p, _ in runs:
        if p == starts[0]:
            tiers.append(start_tier(r2, s1_start, rule_id, dec_by_id))
            continue
        dec = dec_by_id[ids[p]]
        kind = next((k for k in dec["kinds"] if k in STRONG_KINDS), "unknown")
        tiers.append((f"s2_switch:{kind}", {"family_source": "s2_switch", "s2_candidate": ids[p],
                                            "s2_kinds": dec["kinds"]}))
    return [tiers[max(bisect_right(starts, i) - 1, 0)] for i in range(len(ids))]


def block_rows(doc: sc.Doc, atoms: list[dict], res: dict, r2: dict, rule_id: str, fixed_rule: dict) -> list[dict]:
    nos4 = res["nos4"]
    tiers = atom_tiers(doc.ids, r2, res["s1_start"], rule_id)
    s5_of = {}
    for p in res["s5_paragraphs"]:
        for a in p["atoms"]:
            s5_of[a] = (p["rule"], bool(p["sure"]))
    idx: dict[str, list[int]] = {}
    for i, a in enumerate(atoms):
        idx.setdefault(a["block"], []).append(i)
    rows = []
    for b, ii in idx.items():
        opts = [ms.OPTION_OF_ANSWER[nos4[i]] for i in ii]
        option, mixed = ms.block_option([nos4[i] for i in ii], [len(atoms[i].get("text") or "") for i in ii])
        carriers = [i for i, o in zip(ii, opts) if o == option]
        rules_here = sorted({fixed_rule[doc.ids[i]] for i in ii if doc.ids[i] in fixed_rule})
        first_free = next((i for i in carriers if doc.ids[i] not in doc.fixed), None)
        if first_free is None:
            ids_ = sorted({fixed_rule[doc.ids[i]] for i in carriers})
            tier, detail = "fixed:" + "+".join(ids_), {"family_source": "fixed"}
        else:
            tier, detail = tiers[first_free]
            detail = dict(detail)
            s5r = s5_of.get(doc.ids[first_free])
            detail.update(s5_rule=s5r[0] if s5r else None, s5_sure=s5r[1] if s5r else None)
        detail.update(s1_rule_id=rule_id, fixed_rules=rules_here)
        rows.append({"block": b, "option": option, "mixed": mixed, "tier": tier, "tier_detail": detail,
                     "atoms": len(ii), "e20": dict(Counter(nos4[i] for i in ii)),
                     "claimed": res["claims"]["L9"]["claimed"]})
    return rows


def input_files(d: str) -> dict:
    """The atom file and the Docling file of daten/iso (explicit paths; no fallback of m03_iso_paths)."""
    out = {}
    for kind in ("atome", "docling"):
        p = ROOT_DIR / "daten/iso" / kind / f"{d}.json"
        if not p.exists():
            raise ms.Refused(f"{d}: no {kind} file in daten/iso")
        out[kind] = {"path": runner.rel(p), "sha256": runner.sha256(p)}
    return out


def run_document(d: str, export: dict, admission: str, split: str, stored_apertus_role: str | None = None) -> dict:
    """The chain of chapter 1 for one admitted document, without CSCS."""
    files = input_files(d)
    known = admission == "known"
    triage = sc.triage().get(d, "") if known else ""
    doc = runner.runner_doc(d, triage, export["body_key"])
    if known:
        x = sc.load()[d]
        if x.ids != doc.ids or x.fixed != doc.fixed:
            raise SystemExit(f"{d}: atom ids or fixed answers differ from m03_sub_common.load")
    atoms = v4.atoms_of(d)
    fixed_rule = {a: rule.split()[0] for a, (_, rule) in hf.fixed_roles(d, atoms)[0].items()
                  if rule.startswith(FIXED_RULES)}
    if set(fixed_rule) != set(doc.fixed):
        raise SystemExit(f"{d}: the fixed rules do not give the fixed answers")
    with admitted(d, doc, known):
        r1 = s1m.rule(d, {d: {k: export[k] for k in runner.EXPORT_FIELDS}})
        rule_role, rule_id = r1["role"], r1["reason"]
        needs = rule_id not in runner.SURE_IDS
        if not needs:
            combined, source = rule_role, "rule"
        elif stored_apertus_role is not None:
            combined, source = stored_apertus_role, "stored_apertus"
        else:
            combined, source = rule_role, "rule_provisional"
        r2 = s2m.rule_predict(d)
        s2_runs = [tuple(e) for e in r2["s2"]]
        weak = r2["start_reason"].startswith("no strong cue")
        res = chain(d, doc, combined, s2_runs, weak, rule_role)
        rows = block_rows(doc, atoms, res, r2, rule_id, fixed_rule)
        by_d1 = None
        if needs:
            by_d1 = {}
            for opt, role in ROLE_OF_D1.items():
                alt = res if role == combined else chain(d, doc, role, s2_runs, weak, rule_role)
                alt_rows = block_rows(doc, atoms, alt, r2, rule_id, fixed_rule)
                by_d1[opt] = {"s1_combined_role": role, "options": [r["option"] for r in alt_rows],
                              "tiers": [r["tier"] for r in alt_rows], "claim_L9": alt["claims"]["L9"]["claimed"],
                              "nos4_sha256": runner.canonical_sha(alt["nos4"])}
    if admission != "known":
        free_caches()
    return {"doc_id": d, "schema": "parlpdfech-gj-rules/1", "version": RULES_VERSION,
            "status": "EXCEPTION (NOT RELEASED)", "split": split, "admission": admission,
            "body_key": export["body_key"], "inputs": files,
            "export_record": {"source": runner.rel(s1m.PDF_INDEX), "found": export["found"],
                              "fields_sha256": runner.canonical_sha({k: export[k] for k in runner.EXPORT_FIELDS})},
            "document": {
                "d1": {"option": D1_OF_ROLE[combined if source == "stored_apertus" else rule_role],
                       "from": "S1 combined role (stored Apertus)" if source == "stored_apertus" else "S1 rule role",
                       "needs_apertus": needs, "decided_by": "D1" if needs else "S1 rule"},
                "d1_of_answers": ms.d1_of_answers(res["nos4"]),
                "s1": {"rule_role": rule_role, "rule_id": rule_id, "combined_role": combined, "source": source,
                       "sure_ids": list(runner.SURE_IDS)},
                "s2": {"runs": [list(e) for e in s2_runs], "start": r2["start"], "start_reason": r2["start_reason"],
                       "start_weak": weak, "s1_start_applied": res["s1_start"],
                       "strong_cues": sum(1 for x in r2["decisions"] if x["strong"]),
                       "candidates": len(r2["decisions"])},
                "converter_role": res["conv_role"], "claims": res["claims"]},
            "blocks": rows, "by_d1": by_d1,
            "atoms": {"ids": doc.ids, "nos4": res["nos4"], "l9": res["l9"]}}


def core(rec: dict) -> dict:
    """The values that the identity check compares (as m05_iso_runner.core)."""
    doc = rec["document"]
    return {"nos4": rec["atoms"]["nos4"], "l9": rec["atoms"]["l9"],
            "claims": {k: v["claimed"] for k, v in doc["claims"].items()},
            "s1": [doc["s1"]["rule_role"], doc["s1"]["rule_id"], doc["s1"]["combined_role"]]}


# ------------------------------------------------------------------ admission of a document list
def admission_of(d: str, allow_final: bool) -> str:
    if d in runner.GROUP7:
        if not allow_final:
            raise ms.Refused(f"{d}: document of the final group 7 of gate 3a version 3: only with --allow-final-group7")
        return "final_group7"
    return "known" if d in sc.load() else "loader"


def admit_all(ids: list[str], allow_final: bool) -> tuple[dict, dict, dict]:
    exports = runner.export_records(ids)
    split, kind = {}, {}
    for d in ids:
        if not exports[d]["found"]:
            raise ms.Refused(f"{d}: no row in the PDF index")
        split[d] = ms.split_of(d, exports[d]["body_key"], allow_group7=True)
        kind[d] = admission_of(d, allow_final)
        if runner.is_test(d, exports[d]["body_key"]):
            raise ms.Refused(f"{d}: test document (process rule 6): refused")
    return exports, split, kind


# ------------------------------------------------------------------ frozen files
def frozen_files() -> dict:
    """FROZEN_FILES of m05_gate3a_v4_measure.py (read as text, no import) against the files now."""
    tree = ast.parse(MEASURE_SCRIPT.read_text(encoding="utf-8"))
    consts, frozen = {}, {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("RUNNER_FILE", "I95_FILE"):
                consts[name] = ast.literal_eval(node.value)
            if name == "FROZEN_FILES":
                for k, v in zip(node.value.keys, node.value.values):
                    frozen[consts[k.id] if isinstance(k, ast.Name) else ast.literal_eval(k)] = ast.literal_eval(v)
    diff = sorted(p for p, h in frozen.items() if not (ROOT_DIR / p).exists() or runner.sha256(ROOT_DIR / p) != h)
    return {"source": runner.rel(MEASURE_SCRIPT), "files": len(frozen), "different": diff}


# ------------------------------------------------------------------ identity check (chapter 5)
def identity() -> int:
    started = clock()
    frozen = runner.check_frozen_method()
    sp = sc.splits()
    order = [(s, d) for s in ("dev", "eval") for d in sp[s]]
    ids = [d for _, d in order]
    stored_id = json.loads(STORED_IDENTITY.read_text(encoding="utf-8"))
    if stored_id["documents"]["total"] != len(ids) or stored_id["status"] != "MET":
        raise SystemExit("the stored runner identity record does not give 205 documents with the status MET")
    exports, split, kind = admit_all(ids, allow_final=False)
    nos4 = {s: json.loads((runner.LADDER_SCRATCH / f"err_recompose_nos4_{s}.json").read_text(encoding="utf-8"))
            for s in ("dev", "eval")}
    results = json.loads(runner.RESULTS_JSON.read_text(encoding="utf-8"))
    claimed = {(lid, s): set(results["levels"][lid]["methods"]["nos4"][s]["claimed_documents"])
               for lid in ("L8", "L9") for s in ("dev", "eval")}
    st = {name: {s: runner.stored_documents(runner.S1_DIR / f"{name}_{s}.json") for s in ("dev", "eval")}
          for name in ("rule", "combined", "apertus")}
    s2_rule = {s: runner.stored_documents(runner.S2_DIR / f"rule_{s}.json") for s in ("dev", "eval")}
    meta = json.loads((runner.S1_DIR / "export_meta.json").read_text(encoding="utf-8"))

    def compare(recs: dict, apertus_source: str) -> dict:
        keys = ("nos4_answers", "l9_answers", "claim_L8", "claim_L9", "s1_rule", "s1_combined", "s2_rule",
                "export_fields", "export_record_found")
        cmp = {k: {"documents": 0, "documents_different": 0, "differences": []} for k in keys}
        atoms = Counter()

        def diff(key: str, d: str, same: bool, what: str = "") -> None:
            cmp[key]["documents"] += 1
            if not same:
                cmp[key]["documents_different"] += 1
                cmp[key]["differences"].append(f"{d}{': ' + what if what else ''}")

        for s, d in order:
            r = recs[d]
            doc = r["document"]
            a_st = nos4[s][d]
            n_diff = sum(1 for x, y in zip(r["atoms"]["nos4"], a_st) if x != y) + abs(len(r["atoms"]["nos4"]) - len(a_st))
            atoms["nos4_atoms"] += len(a_st)
            atoms["nos4_atoms_different"] += n_diff
            diff("nos4_answers", d, n_diff == 0, f"{n_diff} atoms")
            _, h9, _ = lad.converter_view(runner.LEVEL_DEFS["L9"], d, a_st)      # stored answers, stored S1 signals
            l9_diff = sum(1 for x, y in zip(r["atoms"]["l9"], h9) if x != y)
            atoms["l9_atoms"] += len(h9)
            atoms["l9_atoms_different"] += l9_diff
            diff("l9_answers", d, l9_diff == 0, f"{l9_diff} atoms")
            for lid in ("L8", "L9"):
                mine = doc["claims"][lid]["claimed"]
                diff(f"claim_{lid}", d, mine == (d in claimed[(lid, s)]), f"m10 {mine}, stored {d in claimed[(lid, s)]}")
            sr, sco = st["rule"][s][d], st["combined"][s][d]
            diff("s1_rule", d, (doc["s1"]["rule_role"], doc["s1"]["rule_id"]) == (sr["role"], sr["reason"]))
            src = "apertus" if doc["s1"]["source"] == apertus_source else doc["s1"]["source"]
            diff("s1_combined", d, (doc["s1"]["combined_role"], src) == (sco["role"], sco["source"]),
                 f"m10 {doc['s1']['combined_role']} ({doc['s1']['source']}), stored {sco['role']} ({sco['source']})")
            s2s = s2_rule[s][d]
            diff("s2_rule", d, (doc["s2"]["runs"], doc["s2"]["start_weak"]) ==
                 (s2s["s2"], s2s["start_reason"].startswith("no strong cue")))
            ex = exports[d]
            diff("export_fields", d, all(ex[k] == meta[d][k] for k in runner.EXPORT_FIELDS))
            diff("export_record_found", d, ex["found"])
        return {"comparisons": cmp, "atoms": dict(atoms),
                "differences_total": sum(v["documents_different"] for v in cmp.values()),
                "documents_with_a_difference": sorted({x.split(":")[0] for v in cmp.values() for x in v["differences"]},
                                                      key=int)}

    t0 = time.perf_counter()
    recs_a = {d: run_document(d, exports[d], kind[d], split[d]) for _, d in order}
    seconds_a = time.perf_counter() - t0
    r1_docs = sorted((d for d, r in recs_a.items() if r["document"]["s1"]["source"] == "rule_provisional"), key=int)
    a = compare(recs_a, "stored_apertus")
    split_of_doc = {d: s for s, d in order}
    stored_ap = {d: st["apertus"][split_of_doc[d]][d]["role"] for d in r1_docs}
    recs_b = dict(recs_a)
    for d in r1_docs:
        recs_b[d] = run_document(d, exports[d], kind[d], split[d], stored_apertus_role=stored_ap[d])
    b = compare(recs_b, "stored_apertus")
    outside = [d for d in a["documents_with_a_difference"] if d not in r1_docs]
    per_r1 = {}
    for d in r1_docs:
        ra, rb = recs_a[d], recs_b[d]
        per_r1[d] = {"split": split_of_doc[d], "s1_rule_role": ra["document"]["s1"]["rule_role"],
                     "stored_apertus_role": stored_ap[d],
                     "nos4_atoms_different_no_cscs": sum(1 for x, y in zip(ra["atoms"]["nos4"], rb["atoms"]["nos4"]) if x != y),
                     "claim_L9_no_cscs": ra["document"]["claims"]["L9"]["claimed"],
                     "claim_L9_stored": rb["document"]["claims"]["L9"]["claimed"],
                     "block_options_different": sum(1 for x, y in zip(ra["blocks"], rb["blocks"]) if x["option"] != y["option"]),
                     "by_d1_variants_equal_to_stored": [o for o, v in ra["by_d1"].items()
                                                        if v["nos4_sha256"] == runner.canonical_sha(rb["atoms"]["nos4"])
                                                        and v["claim_L9"] == rb["document"]["claims"]["L9"]["claimed"]]}
    cscs_stored = stored_id["cscs"]["documents"]
    ok = (not outside and b["differences_total"] == 0 and sorted(r1_docs, key=int) == sorted(cscs_stored, key=int)
          and len(recs_a) == 205 and all(x["by_d1_variants_equal_to_stored"] for x in per_r1.values()))
    out = {
        "schema": "parlpdfech-gj-rules-identity/1", "status": "MET" if ok else "NOT MET",
        "run_date": started, "finished": clock(),
        "actor": "workflow sub-agent (Claude Opus 5.5), stream F of plan gate GJ",
        "gate": "GJ (OPEN); status of the work: EXCEPTION (process rule 10)",
        "rules": {"path": runner.rel(RULES_PATH), "sha256": runner.sha256(RULES_PATH), "version": RULES_VERSION},
        "frozen_runner": {"path": runner.rel(runner.RUNNER_PATH), "sha256": runner.sha256(runner.RUNNER_PATH),
                          "version": runner.RUNNER_VERSION},
        "stored_identity": {"path": runner.rel(STORED_IDENTITY), "sha256": runner.sha256(STORED_IDENTITY)},
        "frozen_method": frozen,
        "documents": {"dev": len(sp["dev"]), "eval": len(sp["eval"]), "total": len(order)},
        "cscs_documents": {"m10_needs_apertus": r1_docs, "stored_runner_identity": cscs_stored,
                           "equal": sorted(r1_docs, key=int) == sorted(cscs_stored, key=int)},
        "pass_a_no_cscs": {**a, "differences_outside_r1_documents": outside, "seconds": round(seconds_a, 1),
                           "note": "R1 documents use the S1 rule role as a provisional combined role"},
        "pass_b_stored_apertus_role": {**b, "note": "R1 documents use the stored Apertus role of "
                                                    "daten/iso/sub/s1_role/apertus_<split>.json (no request)"},
        "r1_documents": per_r1,
        "outputs_sha256_pass_b": runner.canonical_sha({d: core(r) for d, r in recs_b.items()}),
        "stored_runner_outputs_sha256": stored_id["runner_outputs_sha256"],
        "outputs_equal_to_stored_runner_outputs": runner.canonical_sha(
            {d: core(r) for d, r in recs_b.items()}) == stored_id["runner_outputs_sha256"],
        "frozen_files": frozen_files(),
        "limits": ["Identity is not accuracy: the stored values are the dev in-sample and eval values of the rules.",
                   "No CSCS request, no reference answers in the runner records, no test document."],
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    IDENTITY_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": out["status"], "documents": out["documents"],
                      "pass_a_differences_total": a["differences_total"],
                      "pass_a_documents_with_a_difference": a["documents_with_a_difference"],
                      "pass_a_differences_outside_r1": outside,
                      "pass_b_differences_total": b["differences_total"],
                      "outputs_equal_to_stored_runner_outputs": out["outputs_equal_to_stored_runner_outputs"],
                      "r1_documents": per_r1, "frozen_files_different": out["frozen_files"]["different"],
                      "file": runner.rel(IDENTITY_OUT), "sha256": runner.sha256(IDENTITY_OUT)}, indent=1))
    return 0 if ok else 2


# ------------------------------------------------------------------ run (chapter 6)
def check_identity_record() -> dict:
    if not IDENTITY_OUT.exists():
        raise SystemExit("no identity record: run the command identity first")
    rec = json.loads(IDENTITY_OUT.read_text(encoding="utf-8"))
    if rec.get("status") != "MET":
        raise SystemExit("the identity record is not MET")
    if (rec.get("rules") or {}).get("sha256") != runner.sha256(RULES_PATH):
        raise SystemExit("m10_rules.py changed after the identity check: run the command identity again")
    return {"path": runner.rel(IDENTITY_OUT), "sha256": runner.sha256(IDENTITY_OUT)}


def run(args) -> int:
    started = clock()
    ident = check_identity_record()
    frozen = runner.check_frozen_method()
    if args.all:
        ids = sorted((p.stem for p in (ROOT_DIR / "daten/iso/docling").glob("*.json")), key=int)
    else:
        ids = [str(d) for d in (args.doc or [])]
    if not ids:
        raise SystemExit("no document: give --all or --doc")
    if len(set(ids)) != len(ids):
        raise SystemExit("a document id occurs more than once")
    finals = [d for d in ids if d in runner.GROUP7]
    if finals and not args.allow_final_group7:
        if args.all:
            ids = [d for d in ids if d not in runner.GROUP7]
        else:
            raise ms.Refused("documents of the final group 7 need --allow-final-group7")
    exports, split, kind = admit_all(ids, allow_final=args.allow_final_group7)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    files, counts = {}, Counter()
    tiers, options = Counter(), Counter()
    for n, d in enumerate(ids, 1):
        rec = run_document(d, exports[d], kind[d], split[d])
        p = OUT_DIR / f"{d}.json"
        p.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        files[runner.rel(p)] = runner.sha256(p)
        doc = rec["document"]
        counts[f"split {split[d]}"] += 1
        counts[f"admission {kind[d]}"] += 1
        counts["needs_apertus"] += doc["d1"]["needs_apertus"]
        counts["claimed_L9"] += doc["claims"]["L9"]["claimed"]
        counts["blocks"] += len(rec["blocks"])
        counts["mixed_blocks"] += sum(b["mixed"] for b in rec["blocks"])
        tiers.update(b["tier"] for b in rec["blocks"])
        options.update(b["option"] for b in rec["blocks"])
        if n % 250 == 0:
            print(f"{n}/{len(ids)} documents", flush=True)
    seconds = time.perf_counter() - t0
    summary = {"schema": "parlpdfech-gj-rules-run/1", "status": "EXCEPTION (NOT RELEASED)", "run_date": started,
               "finished": clock(), "actor": "workflow sub-agent (Claude Opus 5.5), stream F of plan gate GJ",
               "rules": {"path": runner.rel(RULES_PATH), "sha256": runner.sha256(RULES_PATH), "version": RULES_VERSION},
               "identity_record": ident, "frozen_method": frozen, "cscs": "no request (rule id R1: needs_apertus)",
               "documents": len(ids), "final_group7_included": bool(args.allow_final_group7 and finals),
               "final_group7_left_out": [] if args.allow_final_group7 else sorted(finals, key=int),
               "counts": dict(counts), "tiers": dict(tiers.most_common()), "options": dict(options.most_common()),
               "seconds": round(seconds, 1), "outputs_sha256_canonical": runner.canonical_sha(files),
               "outputs": files, "source_files": runner.source_files(), "data_files": runner.data_files(),
               "packages": runner.packages(), "frozen_files": frozen_files(),
               "limits": ["Counts of rule outputs only: no reference was read, no quality value was computed."]}
    RUNS.mkdir(parents=True, exist_ok=True)
    RUN_OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"documents": len(ids), "counts": dict(counts), "seconds": round(seconds, 1),
                      "final_group7_included": summary["final_group7_included"],
                      "frozen_files_different": summary["frozen_files"]["different"],
                      "run_json": runner.rel(RUN_OUT), "sha256": runner.sha256(RUN_OUT)}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="rules without CSCS for gate GJ (nos4 chain, block options and tiers)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("identity")
    r = sub.add_parser("run")
    r.add_argument("--all", action="store_true")
    r.add_argument("--doc", nargs="*")
    r.add_argument("--allow-final-group7", action="store_true")
    a = ap.parse_args()
    try:
        code = identity() if a.cmd == "identity" else run(a)
    except (ms.Refused, runner.Refused, NoCSCS, ValueError) as ex:
        print(f"stopped ({type(ex).__name__}): {ex}", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()

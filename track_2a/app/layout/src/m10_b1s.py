"""Gate GJ (status EXCEPTION), addendum D to the criteria (candidate B1-S): the dev design of B1-S and its one
validation run.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) of workflow
wf_2174cdd4-f5f, for the main agent. No human checked this file. This file changes no existing file. Status of
each output: EXCEPTION (process rule 10), NOT RELEASED. This file is an addition after the design freeze (criteria
chapter 10.2 item 2; addendum D).

B1-S (addendum D, rule D1): the block posteriors of the FROZEN B1 head with its frozen temperature, and one B2
form of addendum C. B1-S has no training and no new first temperature. This file imports the examined functions:
src/m10_b2x.py (B2 forms, forms_table, select_form), src/m10_design.py (frozen design), src/m10_lora_design.py
(lora_decisions, decide_gate, lora_calibration_file), src/m10_lora_validation.py (checks, measures) and
src/m10_validation_run.py (records, GJ.12). It holds no copy of a B2 form, of a selection rule or of a measure.

0 Order of the records (GJ.2; addendum D, rule D2 item 1)
  design    The command writes the SHA-256 of this file into <out>/design_b1s.json and into the event log
            <out>/design_b1s.events.jsonl before it reads the first out-of-fold value.
  validate  The command writes the SHA-256 of this file and of each imported m10 module into <out>/run.json and
            into <out>/run.events.jsonl before the first value. Events: script_sha256, checks_passed, first_value.

1 Command design (dev out-of-fold values only; addendum D, rule D1)
  Input: the stored dev out-of-fold posteriors of the frozen design (daten/gj/design/oof/b1_oof.npz, key
  probs_after_t, and d1_oof.npz; m10_b2x.load_head_oof). These are the values of addendum C, chapter 7. The
  command compares their SHA-256 with addendum C, chapter 9.
  1.1 First temperature: the frozen temperature of the B1 head (heads/b1_head.npz). No fit. The command refuses
      if the temperature of the stored posteriors is not equal to it.
  1.2 B2 forms: m10_b2x.forms_table with the fold rule and the strength rule (addendum C, rules C1 and C2).
  1.3 B2 form of B1-S: m10_b2x.select_form (addendum C, rule C3) on the rows of 1.2.
  1.4 Second temperature (criteria 8.3 item 2; rule C4 item 2): m10_design.fit_temperature on ln of the
      out-of-fold block marginals of the selected form; m10_design.temper.
  1.5 Verifier map (criteria 8.4 item 5): m10_design.fit_platt on the marginal after T2 of the rule option; fit
      set: the non-certain blocks of dev_out_of_design. Only the information variant uses it (the rule option
      decides and B1-S gives the probability).
  1.6 Threshold a (criteria 8.6): m10_design.written_values and m10_design.p17, for the label kinds block_slot
      and author_switch. The kind document_text_parts keeps the thresholds of the frozen design.
  1.7 Value of addendum D, rule D2 item 3: the 6-option accuracy on the non-certain dev blocks of the selected
      form (written path, out-of-fold). The main agent compares it with the value of B1-L.
  Outputs (<out>, default daten/gj/design_b1s/): design_b1s.json (run record, choices, dev table, SHA-256 of each
  input and output), design_b1s.events.jsonl, design_b1s_dev.md, calibration_records.json (the form of
  daten/gj/design/calibration_records.json), oof/b1s_oof.npz (all values, for a second calculation).
  Second run: refused if design_b1s.json holds a finished design. A record that is not finished does not block:
  it is moved to design_b1s.unfinished-<time>.json.

2 Command validate (the ONE validation run of B1-S; addendum D, rule D2)
  Documents: the key validation of daten/gj/sets.json, in the order of the numeric doc id.
  Block posteriors of a document: m10_design.head_logits and m10_design.head_probs of the frozen B1 head on the
  GPU-1 states of the document, at the layer of the head. These are the posteriors of
  m10_design.cascade_decisions. The command checks softmax(logits / T) == head_probs for each document.
  Decisions (interface 7): m10_lora_design.lora_decisions with these logits, the frozen temperature T, the form,
  the strength and T2 of design_b1s.json, and the HMM of the frozen design. The function relabel_decisions then
  gives the calibration ids and the keys of B1-S. A certain block keeps the rule option. The D1 label comes from
  m10_design.cascade_decisions with --entry-d1 (no: the S1 rule decides the document option).
  Variants: d1<y|n>_b1sy (B1-S decides the non-certain blocks) and d1<y|n>_b1sn (the rule option decides, B1-S
  gives the verifier probability; information).
  Checks before the first value: guard and m00_pruefe_testset, record packages, the design freeze file
  (add6fdad...) and each frozen file (m10_lora_validation.freeze_checks: head files, code, FROZEN_FILES,
  template, scorer reproduction), the GPU-1 states against outputs.json, addenda B, C and D, the design of B1-S
  (--design-b1s-sha256: the value of the protocol), the R2 files, the bootstrap draws, the D1 entry value of the
  run of the heads (only the keys entry.d1_enters and entry.b1_b2_enter of daten/gj/validation/measures.json).
  Measures (m10_lora_validation.phase_measures; the function b1s_measures gives the names of B1-S):
    entry    the 3 conditions of criteria 7.2 with B1-S in place of B1 and B2 (addendum D, rule D2 item 2).
             Baseline: the rule option of criteria 6.1 item 10. Cut: criteria 7.3 item 4 (rule D2 item 5).
    bootstrap  numpy.random.default_rng(20261013).integers(0, D, size=(2000, D)), documents in the order of the
             numeric doc id (criteria 6.3; m10_lora_validation.draws_check).
    GJ.13    the written block labels of the variant b1sy. GJ.21: the block measures of both variants.
  Records (GJ.12): m10_validation_run.phase_records (writer, RDF, validator), base IRI
  https://parlpdfech.ansv.ch/id/. R2: --r2 and --r2-calibrations (the files of the run of the heads).
  One-run rule (criteria 10.3): a second run is refused when <out>/run.json exists. State refused (stop before
  the first value): a new start is possible; the record stays as run.refused-<time>.json. State stopped (stop
  after the first value): only --continue-missing continues, for the outputs that do not exist.
  Outputs (<out>, default daten/gj/validation_b1s/): run.json, run.events.jsonl, run.log, decisions/<variant>/,
  decisions_records/ (the variant b1sy with the calibration file of the records), measures.json, result.json,
  result.md, records/. The console shows counts, aggregate values, paths and SHA-256 values only.
  Check run (--check-run): the same chain on dev documents (--docs) with the design of a check run
  (--design-b1s) into --work (outside daten/gj). It refuses each document that is not a dev document.

3 Process constants
  The validate command sets two constants of imported modules in its process and records them in run.json:
  m10_lora_validation.NEW_MODULES (the list of the additions after the design freeze, with this file) and
  m10_lora_design.VALIDATION_SCRIPT (the script whose started run record opens the gate for validation
  documents: this file). No file changes.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync python src/m10_b1s.py design
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_b1s.py validate --entry-d1 no
      --design-b1s-sha256 SHA --r2 daten/gj/r2/validation_r2.json
      --r2-calibrations daten/gj/r2/validation_r2_calibrations.json [--continue-missing]
  Check script (dev documents only): uv run --offline --frozen --no-sync --with linkml==1.11.1 python
      src/m10_b1s_test.py
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import re
import sys
import time
import types
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)
import m10_design as md  # noqa: E402  (frozen design; not changed)
import m10_calibrate as cal  # noqa: E402  (document loader with SHA-256 checks; not changed)
import m10_cascade as casc  # noqa: E402  (floor mode, check_decisions; not changed)
import m10_validation_run as vr  # noqa: E402  (run record, records, GJ.12; not changed)
import m10_b2x as bx  # noqa: E402  (B2 forms and the selection rule of addendum C)
import m10_lora_design as ld  # noqa: E402  (decisions with a B2 form of addendum C)
import m10_lora_validation as lv  # noqa: E402  (checks and measures of a later run of the block step)

VERSION = "m10-b1s-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = md.GJ
OUT_DESIGN = GJ / "design_b1s"
OUT_RUN = GJ / "validation_b1s"
STATUS = md.STATUS
ACTOR = "workflow sub-agent (Claude Opus 5.5) of workflow wf_2174cdd4-f5f, for the main agent"
CANDIDATE = "B1-S"
ADDENDUM_D = (ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-d.md",
              "43e8414dd3f00fbf9111fa167c22a3c09617651d47540b8c9f1ee187f31bad10")      # protocol 13.10.2026, 05:03
TIE_B1S = 0.005                                          # addendum D, rule D2 item 3: "0.005 or less gives B1-S"
CAL_S = {"b2_marginal": "gj1-b1s-b2-marginal-temperature", "b2_verifier": "gj1-b1s-b2-verifier-platt",
         "b2_switch": "gj1-b1s-b2-switch-forward-backward"}
DESIGN_OUTPUTS = ("calibration_records.json", "oof/b1s_oof.npz", "design_b1s_dev.md")
NEW_MODULES = ("m10_b1s", *lv.NEW_MODULES)               # additions after the design freeze that this run loads
ADDENDUM_C_FILES = ("oof/b1_oof.npz", "oof/d1_oof.npz", "tier_table.json", "folds.json")
TABLE_KEYS = ("non_certain_blocks", "non_certain_correct", "accuracy_non_certain", "l9_exact", "switch_documents",
              "switch_exact", "labelled_boundary_f1", "written_switch_boundaries",
              "written_switch_boundaries_correct")

RunRefusal = vr.RunRefusal
sha, rel, now = ld.sha, ld.rel, md.now
read_json, write_json, r6, say = md.read_json, md.write_json, md.r6, vr.say
_f = vr._f


class B1sRefusal(RunRefusal):
    """A run, a file or a document was refused (GJ.10, process rule 6, criteria chapters 3 and 10.3, addendum D)."""


def _log(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


# ---------------------------------------------------------------- records of the criteria

def criteria_check() -> dict:
    """The criteria and the addenda B and C (m10_lora_design.addenda_check, with the SHA-256 of src/m10_b2x.py of
    addendum C chapter 9), and addendum D with the SHA-256 of ADDENDUM_D."""
    try:
        out = ld.addenda_check()
    except ld.LoraRefusal as e:
        raise B1sRefusal(str(e)) from None
    p, want = ADDENDUM_D
    if not p.is_file() or sha(p) != want:
        raise B1sRefusal(f"addendum D ({rel(p)}) does not have the SHA-256 {want[:12]}... of {rel(SCRIPT)}")
    out["files"][rel(p)] = want
    return out


def code_record() -> dict:
    import m10_score as ms  # noqa: PLC0415  (frozen scorer; m10_b2x uses it)
    return {rel(p): sha(p) for p in (SCRIPT, bx.SCRIPT, md.SCRIPT, ld.SCRIPT, Path(guard.__file__),
                                     Path(ms.__file__))}


def fixed_design() -> dict:
    return {"candidate": CANDIDATE, "rule": "addendum D, rule D1",
            "first_temperature": "the frozen temperature of the B1 head (heads/b1_head.npz); no fit",
            "forms": list(bx.FORMS), "strength_grid": {k: list(v) for k, v in bx.STRENGTH_GRID.items()},
            "selection": {"rule": "addendum C, rule C3 (m10_b2x.select_form)", "margin": bx.ENTRY_MARGIN,
                          "tie_accuracy": bx.TIE_ACCURACY},
            "temperature_bounds": [md.T_MIN, md.T_MAX], "a_grid": list(md.A_GRID), "p17": [md.P17_ACC, md.P17_COV],
            "clip": [md.CLIP_LO, md.CLIP_HI], "platt_bound": md.PLATT_BOUND,
            "choice_d2_item_3": {"tie": TIE_B1S, "tie_gives": "B1-S"}, "calibration_ids": dict(CAL_S),
            "units": "each block of each dev document; 5 folds by parliament (the folds of the frozen design)"}


# ---------------------------------------------------------------- command design (chapter 1)

def addendum_c_files(design_dir: Path) -> dict:
    """The SHA-256 of the files of ADDENDUM_C_FILES against the table of addendum C, chapter 9."""
    text = ld.ADDENDA["C"][0].read_text(encoding="utf-8")
    out = {}
    for f in ADDENDUM_C_FILES:
        p = design_dir / f
        m = re.search(r"`" + re.escape(rel(p)) + r"`\s*\|\s*`([0-9a-f]{64})`", text)
        out[rel(p)] = {"sha256": sha(p), "equal_to_addendum_c_chapter_9": bool(m and m.group(1) == sha(p))}
    return out


def choice_value(row: dict) -> dict:
    """The value of addendum D, rule D2 item 3, for the selected form. The choice needs the value of B1-L too."""
    n, k = int(row["non_certain_blocks"]), int(row["non_certain_correct"])
    return {"rule": "addendum D, rule D2 item 3: used only if B1-S and B1-L both enter; the higher 6-option accuracy "
                    "on the non-certain dev blocks (out-of-fold) wins; a difference of 0.005 or less gives B1-S",
            "non_certain_blocks": n, "correct_b1_s": k, "accuracy_b1_s": r6(k / n) if n else None, "tie": TIE_B1S,
            "tie_gives": "B1-S",
            "integer_rule": "B1-L wins only if (correct_b1_l - correct_b1_s) * 1000 > 5 * non_certain_blocks, on "
                            "the same set of non-certain blocks",
            "choice": "not made by this script: the main agent compares this value with the dev value of B1-L"}


def stored_table_check(tab: dict) -> dict | None:
    """The rows of this run against the stored rows of m10_b2x.py dev-heads (the same head values)."""
    if not ld.HEAD_TABLE.is_file():
        return None
    x = read_json(ld.HEAD_TABLE)
    rows = {"rules": (tab["rules"], x["rules"]), **{f: (tab["forms"][f], x["forms"].get(f) or {}) for f in tab["forms"]}}
    diff = {name: [k for k in TABLE_KEYS if a.get(k) != b.get(k)] for name, (a, b) in rows.items()}
    st, st2 = tab["strength"].get("switch_soft") or {}, (x.get("strength") or {}).get("switch_soft") or {}
    same_st = st.get("by_fold") == st2.get("by_fold") and st.get("final") == st2.get("final")
    return {"file": {"path": rel(ld.HEAD_TABLE), "sha256": sha(ld.HEAD_TABLE)}, "keys": list(TABLE_KEYS),
            "rows_compared": len(rows), "different_keys": {k: v for k, v in diff.items() if v},
            "strength_equal": same_st, "selection_equal": tab["selection"]["form"] == x["selection_information"]["form"]
            and tab["selection"]["permitted"] == x["selection_information"]["permitted"],
            "equal": not any(diff.values()) and same_st}


def calibration_records(out: Path, frozen_records: dict, thresholds: dict, info: dict, ver_b2: dict, t1: dict,
                        t2: dict, form: str, strength, n_blocks: int, outputs: dict, check_run: bool) -> dict:
    """The calibration records of B1-S in the form of the frozen design (m10_design.calibration_records). The D1
    records and the tier records are the records of the frozen design, without a change. The 3 records of the
    heads for blocks and switch boundaries are replaced by the 3 records of B1-S."""
    oof = rel(out / "oof/b1s_oof.npz")
    fit = {"fit_set_file": oof, "fit_set_digest": outputs[oof]}
    note = "check run in a temp folder: not the design of record. " if check_run else ""
    par = {"temperature_b1": t1["T"], "temperature_b2": t2["T"]}
    if strength is not None:
        par["strength"] = float(strength)
    old = {md.CAL["b2_marginal"], md.CAL["b2_verifier"], md.CAL["b2_switch"]}
    rec = {k: v for k, v in frozen_records["records"].items() if k not in old}
    kind = {k: v for k, v in frozen_records["kind_of"].items() if k not in old}
    rec[CAL_S["b2_marginal"]] = {
        "calibration_method": "forward_backward_temperature", "calibrated_kind": "block_slot", **fit,
        "fit_n": n_blocks, "reference_source": md.REFERENCE, "in_sample": False, "target_status": "not_measured",
        "calibration_parameters": md._params(**par),
        "measure_sets": md._ms("dev out-of-fold", info["b2_marginals_after_t2"]),
        "calibration_note": note + f"B1-S (addendum D): the frozen B1 head with its frozen temperature; B2 block "
                                   f"marginal of the form {form} (addendum C) after one B2 temperature"}
    rec[CAL_S["b2_verifier"]] = {
        "calibration_method": "verifier_platt", "calibrated_kind": "block_slot", **fit, "fit_n": ver_b2["n"],
        "reference_source": md.REFERENCE, "in_sample": False, "target_status": "not_measured",
        "calibration_parameters": md._params(alpha=ver_b2["alpha"], beta=ver_b2["beta"]),
        "measure_sets": md._ms("non-certain blocks of dev_out_of_design, in-sample", info["verifier_b2_in_sample"]),
        "calibration_note": note + "B1-S: Platt map of the B2 marginal of the rule option; fit set: the non-certain "
                                   "blocks of dev_out_of_design"}
    rec[CAL_S["b2_switch"]] = {
        "calibration_method": "forward_backward_temperature", "calibrated_kind": "author_switch", **fit,
        "fit_n": int(info["switch_all_gaps"]["n"]), "reference_source": md.REFERENCE, "in_sample": False,
        "target_status": "not_measured", "calibration_parameters": md._params(temperature_b1=t1["T"]),
        "measure_sets": md._ms("dev out-of-fold, all gaps", info["switch_all_gaps"]),
        "calibration_note": note + f"B1-S: pairwise forward-backward probability of a switch at the gap in the form "
                                   f"{form}, with the frozen B1 temperature; the B2 temperature is not applied"}
    kind.update({CAL_S["b2_marginal"]: "block_slot", CAL_S["b2_verifier"]: "block_slot",
                 CAL_S["b2_switch"]: "author_switch"})
    th = {"document_text_parts": dict(frozen_records["thresholds"]["document_text_parts"]),
          "block_slot": {v: thresholds["block_slot"][v]["a"] for v in ("b12_entered", "b12_not_entered")},
          "author_switch": {v: thresholds["author_switch"][v]["a"] for v in ("b12_entered", "b12_not_entered")}}
    return {"version": VERSION, "synthetic": False, "check_run": check_run, "status": STATUS, "records": rec,
            "kind_of": kind, "thresholds": th, "variant_keys": frozen_records["variant_keys"],
            "variant_note": "b12_entered and b12_not_entered mean here: B1-S (the frozen B1 head with its B2 form of "
                            "addendum C) entered or not"}


def run_design(out: Path = OUT_DESIGN, design_dir: Path = md.DESIGN, check_run: bool = False,
               quiet: bool = False) -> dict:
    """Chapter 1 on the stored dev out-of-fold posteriors of the frozen B1 head. Writes the outputs to out."""
    log = (lambda m: None) if quiet else _log
    t_start = time.perf_counter()
    out, design_dir = Path(out).resolve(), Path(design_dir).resolve()
    if design_dir != md.DESIGN.resolve():
        raise B1sRefusal("the design of B1-S uses the frozen design daten/gj/design only")
    if not check_run and out != OUT_DESIGN.resolve():
        raise B1sRefusal("the real design writes to daten/gj/design_b1s; another folder needs --check-run")
    if check_run and (out == OUT_DESIGN.resolve() or GJ.resolve() in out.parents):
        raise B1sRefusal("a check run never writes below daten/gj")
    rp, evp = out / "design_b1s.json", out / "design_b1s.events.jsonl"
    earlier: list = []
    if rp.exists():
        try:
            old = read_json(rp)
        except json.JSONDecodeError:
            old = {}
        if old.get("state") == "finished":
            raise B1sRefusal(f"{rel(out)} holds a finished design of B1-S (design_b1s.json): the records stay")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        keep = out / f"design_b1s.unfinished-{stamp}.json"
        rp.rename(keep)
        if evp.exists():
            evp.rename(out / f"design_b1s.events.unfinished-{stamp}.jsonl")
        earlier = list(old.get("earlier_unfinished_runs") or []) + [rel(keep)]
    out.mkdir(parents=True, exist_ok=True)
    # ---- run record and SHA-256 before the first out-of-fold value (GJ.2)
    ev = md.Events(evp)
    script_sha = sha(SCRIPT)
    rec = {"schema": "parlpdfech-gj-design-b1s/1", "version": VERSION, "status": STATUS, "actor": ACTOR,
           "candidate": "B1-S (addendum D, rule D1)", "check_run": check_run, "started": now(),
           "script": {"path": rel(SCRIPT), "sha256": script_sha}, "code": code_record(),
           "fixed_design": fixed_design(), "earlier_unfinished_runs": earlier,
           "state": "the script SHA-256 is recorded; no out-of-fold value was read"}
    write_json(rp, rec)
    rec["script_sha256_recorded"] = ev.add("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    write_json(rp, rec)
    log(f"script SHA-256 {script_sha} recorded in {rel(rp)}")
    try:
        return _design(out, design_dir, check_run, rec, ev, log, t_start)
    except BaseException as e:
        refusal = isinstance(e, (RunRefusal, ld.LoraRefusal, md.DesignRefusal))
        rec["state"] = "refused" if refusal else "stopped"
        rec["stop"] = {"time": ev.add("stopped", kind="refusal" if refusal else type(e).__name__),
                       "reason": (str(e) if refusal else f"{type(e).__name__}: {e}")[:2000],
                       "text": "this record does not block a new start (it is moved at the next start)"}
        write_json(rp, rec)
        raise


def _design(out: Path, design_dir: Path, check_run: bool, rec: dict, ev: md.Events, log, t_start: float) -> dict:
    rp = out / "design_b1s.json"
    # ---- records of the criteria, guard, frozen design (no out-of-fold value is read)
    rec["criteria"] = criteria_check()
    sets = md.load_sets()
    all_dev = sorted({str(d) for d in sets["dev"]}, key=int)
    rec["guard"] = md.assert_fit_ids(all_dev, sets)             # GJ.10 before any file of a document
    fr_sha = sha(md.FREEZE_FILE) if md.FREEZE_FILE.is_file() else None
    if fr_sha != ld.FREEZE_SHA:
        raise B1sRefusal(f"{rel(md.FREEZE_FILE)} does not have the SHA-256 {ld.FREEZE_SHA[:12]}... of the protocol")
    frozen = md.load_frozen(design_dir, md.FREEZE_FILE)         # each design file has the SHA-256 of the freeze
    if frozen.synthetic:
        raise B1sRefusal("the frozen design is synthetic")
    frozen_design = read_json(design_dir / "design.json")
    frozen_records = read_json(design_dir / "calibration_records.json")
    oof_files = {rel(design_dir / "oof" / f"{n}_oof.npz"): sha(design_dir / "oof" / f"{n}_oof.npz")
                 for n in ("b1", "b2", "d1")}
    ac = addendum_c_files(design_dir)
    if not all(v["equal_to_addendum_c_chapter_9"] for v in ac.values()):
        raise B1sRefusal("a file of the out-of-fold values does not have the SHA-256 of addendum C, chapter 9")
    rec.update({"inputs": {rel(md.FREEZE_FILE): fr_sha, **oof_files,
                           **{rel(design_dir / f): h for f, h in frozen.files.items()}},
                "inputs_of_addendum_c_chapter_9": ac,
                "state": "the inputs have their SHA-256 values; no out-of-fold value was read"})
    write_json(rp, rec)
    # ---- first out-of-fold value: the stored posteriors of the frozen design
    rec["first_out_of_fold_value"] = ev.add("first_out_of_fold_value",
                                            what="stored dev out-of-fold posteriors of the frozen B1 head")
    write_json(rp, rec)
    Q, pd1, hinfo = bx.load_head_oof(design_dir)
    if hinfo["files"] != oof_files:
        raise B1sRefusal("a file of the out-of-fold values changed during the design run")
    # ---- 1.1 first temperature: the frozen temperature, no fit (addendum D, rule D1 item 1)
    with np.load(design_dir / "oof/b1_oof.npz", allow_pickle=False) as z:
        t_oof = float(z["T"])
    t_head = float(frozen.b1["T"])
    if not (t_oof == t_head == float(frozen_design["b1"]["T"])):
        raise B1sRefusal("the temperature of the stored out-of-fold posteriors is not the frozen temperature of the "
                         "B1 head")
    t1 = {"T": t_head, "fit": False, "source": "heads/b1_head.npz of the frozen design (key T)",
          "equal_to_the_temperature_of_b1_oof_npz": True, "layer": int(frozen.b1["layer"]), "C": float(frozen.b1["C"]),
          "nll_before": frozen_design["b1"]["nll_before"], "nll_after": frozen_design["b1"]["nll_after"],
          "text": "addendum D, rule D1 item 1: the head keeps its frozen temperature; this script fits no first "
                  "temperature"}
    # ---- 1.2 and 1.3: the 5 forms with the fold rule and the selection rule of addendum C
    tab = bx.forms_table(Q, pd1, design_dir, log=log)
    dev, _sc = tab.pop("_dev"), tab.pop("_scorer")
    ids = dev.ids
    if ids != all_dev:
        raise B1sRefusal("the dev documents of the frozen design are not the dev documents of sets.json")
    ood = {str(d) for d in sets["dev_out_of_design"]} & set(ids)
    sel = tab["selection"]
    form = sel["form"]
    st = tab["strength"].get(form)
    strength = None if st is None else float(st["final"])
    log(f"B2 form by addendum C, rule C3: {form} (permitted {sel['permitted']}; strength {strength})")
    # ---- 1.4 second temperature on the marginals of the selected form
    offsets, a = {}, 0
    for d in ids:
        offsets[d] = (a, a + len(Q[d]))
        a += len(Q[d])
    Q_all = np.concatenate([Q[d] for d in ids])
    y = np.array([md.OPTIONS.index(o) for d in ids for o in dev.refs[d]])
    bdoc = np.concatenate([np.full(len(Q[d]), i) for i, d in enumerate(ids)])
    fold_blk = np.concatenate([np.full(len(Q[d]), dev.fold[d]) for d in ids])
    marg = np.concatenate([tab["marginals"][form][d] for d in ids])
    t2 = md.fit_temperature(np.log(np.maximum(marg, md.P_FLOOR)), y)
    marg2 = md.temper(marg, t2["T"])
    # ---- 1.5 verifier map (fit set: non-certain blocks of dev_out_of_design)
    pb, ybv = [], []
    for d in ids:
        if d not in ood:
            continue
        a0 = offsets[d][0]
        for j, o in enumerate(dev.view[d][0]):
            if not dev.certain[d][j]:
                pb.append(marg2[a0 + j, md.OPTIONS.index(o)])
                ybv.append(o == dev.refs[d][j])
    ver_b2 = md.fit_platt(np.array(pb), np.array(ybv))
    # ---- 1.6 written values and the threshold a (the functions of the frozen design)
    tt = read_json(design_dir / "tier_table.json")
    jeff = {(r["tier"], r["option"]): r["jeffreys_mean"] for r in tt["pairs"]}
    pd1_arr = np.stack([pd1[d] for d in ids])
    data = types.SimpleNamespace(ids=ids, offsets=offsets)
    b2f = {d: {"path": tab["written"][form][d], "switch": tab["switch"][form][d]} for d in ids}
    wv = md.written_values(data, ids, dev.rules, dev.refs, dev.ref_d1, pd1_arr, marg2, b2f, dev.view, dev.certain,
                           jeff, frozen.verifiers["d1"], ver_b2, ood)
    thresholds = {kind: {var: md.p17(v["p"], v["correct"]) for var, v in vs.items()}
                  for kind, vs in wv["p17"].items()}
    d1_same = {var: thresholds["document_text_parts"][var]["a"] == frozen_records["thresholds"][
        "document_text_parts"][var] for var in ("d1_entered", "d1_not_entered")}
    grp_b = np.array(ids)[bdoc]
    info = {"b1_after_t": md.measures(Q_all, y, grp_b, boot=True),
            "b2_marginals_before_t2": md.measures(marg, y),
            "b2_marginals_after_t2": md.measures(marg2, y, grp_b, boot=True),
            "switch_all_gaps": md.measures(md.binary(wv["gaps"]["p"]), np.where(wv["gaps"]["ref"], 0, 1),
                                           wv["gaps"]["doc"], boot=True),
            "written": {k: md.written_measures(v["p"], v["correct"], v["doc"]) for k, v in wv["written"].items()
                        if k.startswith(("block_", "switch_"))},
            "accuracy": {k: v for k, v in wv["accuracy"].items() if not k.startswith("d1_")},
            "verifier_b2_in_sample": md.written_measures(md.platt(np.array(pb), ver_b2), np.array(ybv)) if pb else None,
            "b1_argmax_accuracy_all_blocks": r6((Q_all.argmax(1) == y).mean())}
    row = tab["forms"][form]
    if int(row["non_certain_correct"]) != int(round(wv["accuracy"]["noncertain_b2_viterbi"]
                                                    * wv["accuracy"]["noncertain_blocks"])):
        raise B1sRefusal("m10_b2x.forms_table and m10_design.written_values give another count of correct blocks")
    # ---- outputs
    outputs = {}
    outputs[rel(out / "oof/b1s_oof.npz")] = md.write_npz(
        out / "oof/b1s_oof.npz", doc_ids=np.array(ids), block_doc=bdoc,
        block_ids=np.array([b["block"] for d in ids for b in dev.rules[d]["blocks"]]), fold=fold_blk, y=y,
        T=np.float64(t_head), probs_after_t=Q_all, form=np.array(form),
        strength_by_fold=np.array([np.nan if st is None else float(st["by_fold"][str(k)])
                                   for k in range(1, md.N_FOLDS + 1)]),
        strength_final=np.float64(np.nan if strength is None else strength),
        marg=marg, T2=np.float64(t2["T"]), marg_after_t2=marg2,
        written=np.array([o for d in ids for o in tab["written"][form][d]]),
        certain=np.concatenate([dev.certain[d] for d in ids]),
        rule_option=np.array([o for d in ids for o in dev.view[d][0]]),
        gap_doc=wv["gaps"]["doc"], gap_after=wv["gaps"]["after"], gap_p=wv["gaps"]["p"], gap_ref=wv["gaps"]["ref"],
        **{f"marg_{f}": np.concatenate([tab["marginals"][f][d] for d in ids]) for f in tab["forms"]},
        **{f"written_{f}": np.array([o for d in ids for o in tab["written"][f][d]]) for f in tab["forms"]})
    cal_rec = calibration_records(out, frozen_records, thresholds, info, ver_b2, t1, t2, form, strength, len(y),
                                  outputs, check_run)
    outputs[rel(out / "calibration_records.json")] = write_json(out / "calibration_records.json", cal_rec)
    choices = {
        "b1": t1,
        "b2": {"form": form, "selection": sel, "strength": None if st is None else
               {k: st[k] for k in ("grid", "by_fold", "final", "rule")},
               "strength_final": strength, **{f"t2_{k}": v for k, v in t2.items()},
               "hmm": {"file": rel(design_dir / "b2_hmm.json"), "sha256": frozen.files["b2_hmm.json"],
                       "text": "start, transitions and priors of all dev documents (frozen design); out-of-fold "
                               "values use the HMM of the training folds"}},
        "verifier_b2": {**ver_b2, "input": "out-of-fold B2 marginal after T2 of the rule option (non-certain blocks)",
                        "fit_set": "non-certain blocks of dev_out_of_design",
                        "use": "only the information variant in which the rule option decides"},
        "thresholds": cal_rec["thresholds"],
        "thresholds_tables": {k: thresholds[k] for k in ("block_slot", "author_switch")},
        "threshold_document_text_parts_equal_frozen_design": d1_same,
        "certain_pairs": tt["certain_pairs"], "calibration_ids": dict(CAL_S),
        "choice_d2_item_3": choice_value(row)}
    table = {"rules": tab["rules"], "forms": tab["forms"], "strength_tables": tab["strength"],
             "counts": tab["counts"], "stored_table_of_the_head_values": stored_table_check(tab),
             "b1_heads_design_json": {
                 "accuracy": frozen_design["measures_information"]["accuracy"],
                 "ece_b2_marginals_after_t2": frozen_design["measures_information"]["b2_marginals_after_t2"]["ece"],
                 "written": {k: {x: v.get(x) for x in ("n", "accuracy", "ece", "ece_high")}
                             for k, v in frozen_design["measures_information"]["written"].items()
                             if k.startswith(("block_", "switch_"))},
                 "b2_form": frozen_design["b2"]["form"], "thresholds": frozen_design["thresholds"]}}
    rec["inputs"].update(dev.inputs)
    rec.update({"documents": {"dev": len(ids), "dev_out_of_design": len(ood), "blocks": int(len(y))},
                "choices": choices, "dev_table": table, "measures_information": info})
    mdp = out / "design_b1s_dev.md"
    mdp.write_text(design_markdown(rec, choices, table, info), encoding="utf-8")
    outputs[rel(mdp)] = sha(mdp)
    if code_record() != rec["code"]:
        raise B1sRefusal("a script changed during the design run")
    rec.update({"finished": ev.add("finished"), "seconds": round(time.perf_counter() - t_start, 1),
                "state": "finished", "outputs": outputs})
    h = write_json(rp, rec)
    log(f"design of B1-S finished in {rec['seconds']} s; {rel(rp)} SHA-256 {h}")
    return rec


def design_markdown(rec: dict, ch: dict, table: dict, info: dict) -> str:
    L = []
    add = L.append
    b2, sel = ch["b2"], ch["b2"]["selection"]
    form = b2["form"]
    rules, hd = table["rules"], table["b1_heads_design_json"]
    add("# Gate GJ: design of B1-S on `dev` (B2 form, second temperature, threshold a)")
    add("")
    add(f"Run of {rec['started']} (time from the clock). Script `{rec['script']['path']}`, SHA-256 "
        f"`{rec['script']['sha256']}`. Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: "
        "workflow sub-agent (Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    add("B1-S is the candidate of addendum D to the criteria: the block posteriors of the frozen B1 head with its "
        "frozen temperature, and one B2 form of addendum C.")
    add("")
    if rec["check_run"]:
        add("This file is the output of a check run in a temp folder. It is not the design of record.")
        add("")
    add("## 1 Order of the records")
    add("")
    add(f"1. The script wrote its SHA-256 into `design_b1s.json` at {rec['script_sha256_recorded']}.")
    add(f"2. The script read the first out-of-fold value at {rec.get('first_out_of_fold_value')}.")
    add("3. All values of this file are `dev` out-of-fold values. They are information. Each choice uses them only.")
    add("4. This file holds no value of a validation document and no value of a group-7 document.")
    add("5. The posteriors are the stored out-of-fold values of the frozen design (`daten/gj/design/oof/`). They are "
        "the values of addendum C, chapter 7. Each file has the SHA-256 of addendum C, chapter 9.")
    add(f"6. Documents: {rec['documents']['dev']}. Blocks: {rec['documents']['blocks']}. Documents of "
        f"`dev_out_of_design`: {rec['documents']['dev_out_of_design']}.")
    add("")
    add("## 2 Choices")
    add("")
    add(f"1. First temperature (addendum D, rule D1, item 1): T = {_f(ch['b1']['T'])}. This is the frozen "
        "temperature of the B1 head. The script fitted no first temperature.")
    add(f"2. B2 form (addendum C, rule C3): `{form}`. Permitted forms: "
        f"{', '.join(f'`{x}`' for x in sel['permitted']) or 'none'}. Limits: {sel['limits']['switch_exact']} switch "
        f"documents exact and {sel['limits']['l9_exact']} L9 exact documents.")
    add(f"3. Forms with an accuracy of 0.005 or less below the highest value: "
        f"{', '.join(f'`{x}`' for x in sel['equal_within_0.005'])}. Reason of the pool: {sel['reason']}.")
    if b2["strength"] is not None:
        add(f"4. Strength of `switch_soft` (addendum C, rule C2): for each held-out fold "
            f"{', '.join(f'{k}: {_f(v, 0)}' for k, v in b2['strength']['by_fold'].items())}. Value for a document "
            f"of the validation run: {_f(b2['strength_final'], 0)}.")
    else:
        add("4. The selected form has no strength value.")
    add(f"5. Second temperature (criteria 8.3, item 2): T2 = {_f(b2['t2_T'])}. NLL before T2: "
        f"{_f(b2['t2_nll_before'])}. NLL after T2: {_f(b2['t2_nll_after'])}.")
    v = ch["verifier_b2"]
    add(f"6. Verifier map (criteria 8.4): alpha {_f(v['alpha'])}, beta {_f(v['beta'])}, fitted on {v['n']} "
        "non-certain blocks of `dev_out_of_design`. Only the information variant uses it.")
    th = ch["thresholds"]
    add(f"7. Threshold a (criteria 8.6). Block labels: {_f(th['block_slot']['b12_entered'])} if B1-S decides, "
        f"{_f(th['block_slot']['b12_not_entered'])} if the rules decide. Switch boundaries: "
        f"{_f(th['author_switch']['b12_entered'])} and {_f(th['author_switch']['b12_not_entered'])}. The sign – "
        "means: no value of the grid meets the conditions, and each label of the kind is unsure.")
    c = ch["choice_d2_item_3"]
    add(f"8. Value of addendum D, rule D2, item 3: the accuracy of the selected form on the "
        f"{c['non_certain_blocks']} non-certain blocks is {_f(c['accuracy_b1_s'], 6)} ({c['correct_b1_s']} correct "
        "blocks). If B1-S and B1-L both enter, the higher value wins. A difference of 0.005 or less gives B1-S. "
        "This script does not make that choice.")
    add("")
    add("## 3 Values on `dev` (out-of-fold) of the rules and of the 5 forms")
    add("")
    add("| Method | 6-option accuracy on the non-certain blocks | L9 exact documents | Switch documents exact | "
        "Labelled boundary F1 | Written switch boundaries correct | ECE of the block marginals after the second "
        "temperature |")
    add("|---|---|---|---|---|---|---|")

    def line(name: str, r: dict, ece) -> None:
        add(f"| {name} | {_f(r['accuracy_non_certain'])} | {r['l9_exact']} | {r['switch_exact']} of "
            f"{r['switch_documents']} | {_f(r['labelled_boundary_f1'])} | {r['written_switch_boundaries_correct']} of "
            f"{r['written_switch_boundaries']} | {_f(ece)} |")
    line("rules", rules, None)
    for f, r in table["forms"].items():
        ece = info["b2_marginals_after_t2"]["ece"] if f == form else r.get("ece_block_marginals_after_t2_information")
        line(f"B1 head, `{f}`" + (" (selected: B1-S)" if f == form else "")
             + (" (frozen design)" if f == hd["b2_form"] else ""), r, ece)
    add("")
    add(f"1. Documents: {rules['documents']}. Non-certain blocks: {rules['non_certain_blocks']}. Switch documents: "
        f"{rules['switch_documents']}.")
    add("2. The ECE of each form uses a pooled second temperature of that form. For a form that is not selected, "
        "the value is information.")
    add("3. The L9 values and the switch counts come from `src/m10_score.py`, on all documents without abstention.")
    s = table["stored_table_of_the_head_values"]
    if s:
        add(f"4. The stored table `{s['file']['path']}` has the same head values. Rows compared: "
            f"{s['rows_compared']}. Equal: {_f(s['equal'])}. Selection equal: {_f(s['selection_equal'])}.")
    else:
        add("4. The stored table of the head values does not exist. The script made no comparison.")
    add("")
    add("## 4 Calibration of the written labels on `dev`")
    add("")
    add("| Label set | B1-S: n | B1-S: accuracy | B1-S: ECE | B1-S: 95 % bound | Frozen design: accuracy | Frozen "
        "design: ECE |")
    add("|---|---|---|---|---|---|---|")
    names = {"block_b12_entered": "all blocks, the method decides", "block_b2_noncertain": "non-certain blocks, "
             "the method decides", "block_b12_not_entered": "all blocks, the rules decide (verifier probability)",
             "block_verifier_noncertain": "non-certain blocks, the rules decide", "block_certain_tier":
             "certain blocks (rule tier)", "switch_b12_entered": "switch boundaries, the method decides",
             "switch_b12_not_entered": "switch boundaries of the rules"}
    for k, text in names.items():
        m, h = info["written"].get(k) or {}, hd["written"].get(k) or {}
        add(f"| {text} | {_f(m.get('n'))} | {_f(m.get('accuracy'))} | {_f(m.get('ece'))} | {_f(m.get('ece_high'))} | "
            f"{_f(h.get('accuracy'))} | {_f(h.get('ece'))} |")
    add("")
    m = info["b2_marginals_after_t2"]
    add(f"1. Block marginals of B1-S after T2, all blocks: ECE {_f(m['ece'])}, 95 % bound {_f(m.get('ece_high'))}, "
        f"Brier score {_f(m['brier'])}, NLL {_f(m['nll'])}. Frozen design (free form): ECE "
        f"{_f(hd['ece_b2_marginals_after_t2'])}.")
    m = info["b1_after_t"]
    add(f"2. Posterior of the B1 head after T, all blocks: accuracy {_f(m['accuracy'])}, ECE {_f(m['ece'])}, NLL "
        f"{_f(m['nll'])}.")
    add("3. The limit of GJ.13 is an ECE of 0.05 or less on validation. The values of this chapter are `dev` values.")
    add("")
    add("## 5 Limits")
    add("")
    add("1. The reference is an AI reference without a human acceptance.")
    add("2. B1-S was designed after the aggregate result of the validation run of the heads was known (addendum D, "
        "limit 1).")
    add("3. The 3 new forms were designed after the `dev` switch analysis of the same posteriors (addendum C, "
        "chapter 8). Thus their `dev` values are too good.")
    add("4. The form, the strength, the second temperature and a come from the same `dev` out-of-fold values.")
    add("5. The strength of a fold uses posteriors of heads that saw the labels of that fold (addendum C, limit 11).")
    add("6. The rules saw 145 of the 193 `dev` documents in their design. This favours each form with rule gaps.")
    add("7. The switch counts are small. A difference of 1 or 2 documents is not a sure difference.")
    add("8. Jonathan did not accept the criteria or the addenda B, C and D. All values have the status EXCEPTION.")
    add("")
    add("## 6 Inputs")
    add("")
    add("| File or digest | SHA-256 |")
    add("|---|---|")
    for k, h in {**rec["inputs"], **rec["criteria"]["files"]}.items():
        add(f"| `{k}` | `{h}` |")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- the finished design and the decisions

def load_design_b1s(design_dir: Path, frozen: md.Frozen, real: bool = True) -> ld.LoraDesign:
    """The finished design of B1-S as the design object of m10_lora_design (T: the frozen temperature of the B1
    head). Each output file must have the SHA-256 of design_b1s.json. The frozen design files must be the files
    that the design of B1-S used. real: refuses the design of a check run and another folder."""
    design_dir = Path(design_dir).resolve()
    p = design_dir / "design_b1s.json"
    if not p.is_file():
        raise B1sRefusal(f"no design of B1-S: {rel(p)} does not exist")
    rec = read_json(p)
    if rec.get("state") != "finished":
        raise B1sRefusal(f"{rel(p)}: the design run is not finished")
    if real and (rec.get("check_run") or design_dir != OUT_DESIGN.resolve()):
        raise B1sRefusal("a held-out document needs the real design of B1-S in daten/gj/design_b1s (not a check run)")
    files = {}
    for name in DESIGN_OUTPUTS:
        q = design_dir / name
        want = (rec.get("outputs") or {}).get(rel(q))
        if not q.is_file() or want is None or sha(q) != want:
            raise B1sRefusal(f"{rel(q)} does not have the SHA-256 of design_b1s.json")
        files[rel(q)] = want
    for f, h in frozen.files.items():
        if (rec.get("inputs") or {}).get(rel(frozen.design_dir / f)) != h:
            raise B1sRefusal(f"the design of B1-S used another file {f} of the frozen design")
    ch = rec["choices"]
    if ch["b1"].get("fit") is not False or float(ch["b1"]["T"]) != float(frozen.b1["T"]):
        raise B1sRefusal("the first temperature of the design of B1-S is not the frozen temperature of the B1 head")
    form = ch["b2"]["form"]
    if form not in bx.FORMS:
        raise B1sRefusal(f"unknown B2 form {form!r}")
    strength = ch["b2"]["strength_final"]
    if (form in bx.STRENGTH_GRID) != (strength is not None):
        raise B1sRefusal("the strength value does not agree with the form")
    return ld.LoraDesign(design_dir, rec, float(frozen.b1["T"]), form, None if strength is None else float(strength),
                         float(ch["b2"]["t2_T"]), ch["verifier_b2"], read_json(design_dir / "calibration_records.json"),
                         sha(p), files, bool(rec.get("check_run")))


def head_logits_of(d: str, frozen: md.Frozen, states_dir: Path, block_ids: list[str]) -> tuple[np.ndarray, dict]:
    """The logits [n, 6] of the frozen B1 head for the blocks of one document, from its GPU-1 states file, by the
    functions of the frozen design. softmax(logits / T) must be m10_design.head_probs: the block posterior that
    m10_design.cascade_decisions uses."""
    p = md.npz_path(states_dir, d)
    s = md.read_states(p, d, block_ids)
    if s["meta"].get("template_sha256") != frozen.template_sha256:
        raise B1sRefusal(f"{d}: the template SHA-256 of the states is not the frozen template")
    ib = md.layer_index(s["layers"], (frozen.b1["layer"],))[0]
    X = s["states"][1:, ib].astype(np.float64)
    S = md.head_logits(frozen.b1, np.atleast_2d(X))
    if not np.array_equal(md.softmax(S / float(frozen.b1["T"])), md.head_probs(frozen.b1, X)):
        raise B1sRefusal(f"{d}: softmax(logits / T) is not m10_design.head_probs")
    return S, {"source": "frozen B1 head (heads/b1_head.npz) with its frozen temperature on the GPU-1 states",
               "states_file": rel(p), "sha256": sha(p), "layer": int(frozen.b1["layer"]),
               "equal_to_m10_design_head_probs": True}


def relabel_decisions(dec: dict, des: ld.LoraDesign, entry_b1s: bool) -> dict:
    """The decisions of m10_lora_design.lora_decisions with the names of B1-S: the 3 calibration ids of CAL_S, the
    entry key b1_s and the key b1_s in place of b1_l. No option and no probability changes."""
    ids = {ld.CAL_L[k]: CAL_S[k] for k in CAL_S}
    out = dict(dec)
    out["blocks"] = [{**b, "calibration": ids.get(b["calibration"], b["calibration"])} for b in dec["blocks"]]
    out["boundaries"] = [{**x, "calibration": ids.get(x["calibration"], x["calibration"])} for x in dec["boundaries"]]
    x = out.pop("b1_l")
    out["entry"] = {"d1": bool(dec["entry"]["d1"]), "b1_b2": False, "b1_s": bool(entry_b1s)}
    out["candidate"] = "B1-S (addendum D)"
    out["b1_s"] = {"design": {"path": rel(des.dir / "design_b1s.json"), "sha256": des.sha256,
                              "check_run": des.check_run},
                   "temperature_b1": des.T, "form": des.form, "strength": des.strength, "temperature_b2": des.T2,
                   "posteriors": x["logits"], "script": {"path": rel(SCRIPT), "sha256": sha(SCRIPT), "version": VERSION},
                   "decision_function": {"name": "m10_lora_design.lora_decisions", **x["script"]},
                   "m10_b2x": x["m10_b2x"]}
    return out


def b1s_decisions(d: str, gate: ld.Gate, frozen: md.Frozen, des: ld.LoraDesign, states_dir: Path, entry_d1: bool,
                  entry_b1s: bool, r2: dict | None = None, dev_ids: set[str] | None = None) -> dict | None:
    """Interface 7 (mode cascade) of B1-S for one document. None: the document has no states file. A ValueError
    of the B2 form (no path with a weight above 0) goes to the caller."""
    d = str(d)
    if d not in gate.ids:
        raise B1sRefusal(f"{d}: the document did not pass the gate of the decisions")
    if not md.npz_path(states_dir, d).is_file():
        return None
    S, info = head_logits_of(d, frozen, Path(states_dir), [b["block"] for b in md.load_doc(d)["blocks"]])
    dec = ld.lora_decisions(d, gate, frozen, des, S, Path(states_dir), bool(entry_d1), bool(entry_b1s), r2, dev_ids,
                            info)
    return None if dec is None else relabel_decisions(dec, des, entry_b1s)


# ---------------------------------------------------------------- command validate: configuration and run record

@dataclass
class Config:
    real: bool
    ids: list[str]
    split: str
    out: Path
    decisions_out: Path
    design_b1s: Path
    entry_d1: bool
    head_states: Path = vr.STATES
    design_b1s_sha: str | None = None
    r2: Path | None = None
    r2_cal: Path | None = None
    no_r2: bool = False
    continue_missing: bool = False
    records: bool = True

    def vcfg(self) -> vr.Config:
        """The configuration of the frozen runner for its functions (guard, states check, records, GJ.12)."""
        return vr.Config(real=self.real, ids=self.ids, split=self.split, freeze=vr.FREEZE, out=self.out,
                         decisions_out=self.decisions_out, floor_out=self.out / "floor_not_used",
                         records_out=self.out / "records", states=self.head_states, r2=self.r2, r2_cal=self.r2_cal,
                         continue_missing=self.continue_missing, records=self.records)

    def variants(self) -> tuple[str, str]:
        e = "y" if self.entry_d1 else "n"
        return f"d1{e}_b1sy", f"d1{e}_b1sn"


def set_process_constants() -> dict:
    """Chapter 3: the two constants of imported modules that this run sets in its process. No file changes."""
    lv.NEW_MODULES = NEW_MODULES
    ld.VALIDATION_SCRIPT = SCRIPT
    return {"m10_lora_validation.NEW_MODULES": list(NEW_MODULES),
            "m10_lora_design.VALIDATION_SCRIPT": rel(SCRIPT),
            "text": "set in the process of this run only: the additions after the design freeze include this file, "
                    "and the gate of m10_lora_design.decide_gate accepts the started run record of this file"}


def options_record(cfg: Config) -> dict:
    def entry(f) -> dict | None:
        return None if f is None else {"path": rel(f), "sha256": sha(f) if Path(f).is_file() else "absent"}
    return {"entry_d1": cfg.entry_d1, "r2": entry(cfg.r2), "r2_calibrations": entry(cfg.r2_cal), "no_r2": cfg.no_r2,
            "design_b1s": entry(cfg.design_b1s / "design_b1s.json"), "head_states": rel(cfg.head_states),
            "records": bool(cfg.records)}


def start_record(cfg: Config, constants: dict) -> vr.Record:
    """The run record with the SHA-256 of this file before the first value, and the one-run rule (the rule of
    m10_lora_validation.start_record)."""
    cfg.out.mkdir(parents=True, exist_ok=True)
    r = vr.Record(cfg.vcfg())
    script_sha = sha(SCRIPT)
    opts = options_record(cfg)
    earlier = []
    if r.path.exists():
        old = read_json(r.path)
        if old.get("state") == "refused" and not old.get("first_value") and not cfg.continue_missing:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            keep = cfg.out / f"run.refused-{stamp}.json"
            r.path.rename(keep)
            if r.ev.exists():
                r.ev.rename(cfg.out / f"run.events.refused-{stamp}.jsonl")
            earlier = list(old.get("earlier_refused_runs") or []) + [rel(keep)]
    if r.path.exists():
        old = read_json(r.path)
        if not cfg.continue_missing:
            raise B1sRefusal(f"one-run rule (criteria 10.3; addendum D, rule D2 item 1): {rel(r.path)} exists (state "
                             f"{old.get('state')}); only --continue-missing after a technical stop")
        if old.get("state") == "finished":
            raise B1sRefusal(f"one-run rule (criteria 10.3): the run of {rel(r.path)} is finished")
        if (old.get("script") or {}).get("sha256") != script_sha or old.get("modules") != lv.module_sha():
            raise B1sRefusal("--continue-missing: this file or a module differs from the run record")
        if old.get("documents") != cfg.ids or old.get("options") != opts:
            raise B1sRefusal("--continue-missing: the documents or the options differ from the first start")
        r.rec = old
        r.rec["state"] = "started"
        r.rec.setdefault("continued", []).append(r.event("continued", sha256=script_sha))
        r.save()
        return r
    if cfg.continue_missing:
        raise B1sRefusal("--continue-missing needs the run record of a run with a technical stop")
    r.ev.write_text("", encoding="utf-8")
    r.rec = {"schema": "parlpdfech-gj-validation-b1s-run/1", "version": VERSION, "status": STATUS, "actor": ACTOR,
             "gate": "GJ (OPEN)", "candidate": "B1-S (addendum D)", "check_run": not cfg.real,
             "kind": "validation run of B1-S (addendum D, rule D2 item 1; criteria 10.3)" if cfg.real else
             "check run on dev documents (not a measurement of a held-out set)",
             "started": now(), "script": {"path": rel(SCRIPT), "sha256": script_sha}, "modules": lv.module_sha(),
             "process_constants": constants,
             "freeze": {"path": rel(vr.FREEZE), "sha256": sha(vr.FREEZE) if vr.FREEZE.is_file() else None},
             "split": cfg.split, "documents": cfg.ids, "options": opts, "state": "started",
             "state_text": "the script SHA-256 is recorded; no value exists", "earlier_refused_runs": earlier}
    r.save()
    r.rec["script_sha256_recorded"] = r.event("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    r.save()
    return r


# ---------------------------------------------------------------- checks before the first value

def design_check(cfg: Config, frozen: md.Frozen) -> tuple[ld.LoraDesign, dict]:
    crit = criteria_check()
    des = load_design_b1s(cfg.design_b1s, frozen, real=cfg.real)
    if cfg.real and cfg.design_b1s_sha != des.sha256:
        raise B1sRefusal("the SHA-256 of design_b1s.json is not the value of --design-b1s-sha256 (the value of the "
                         "protocol)")
    code = des.record.get("code") or {}
    changed = [p for p in (rel(bx.SCRIPT), rel(md.SCRIPT), rel(ld.SCRIPT)) if code.get(p) != sha(ROOT / p)]
    if changed:
        raise B1sRefusal(f"files changed after the design of B1-S: {changed}")
    ch = des.record["choices"]
    return des, {"criteria": crit, "design_b1s_json": {"path": rel(des.dir / "design_b1s.json"), "sha256": des.sha256},
                 "output_files": des.files, "check_run": des.check_run, "form": des.form, "strength": des.strength,
                 "temperature_b1": des.T, "temperature_b1_is_the_frozen_temperature": des.T == float(frozen.b1["T"]),
                 "temperature_b2": des.T2, "thresholds": ch["thresholds"],
                 "dev_accuracy_b1_s": ch["choice_d2_item_3"]["accuracy_b1_s"],
                 "design_finished": des.record.get("finished"),
                 "design_script_sha256": (des.record.get("script") or {}).get("sha256"),
                 "this_file_equal_to_the_design_script": (des.record.get("script") or {}).get("sha256") == sha(SCRIPT)}


# ---------------------------------------------------------------- phase A: decisions

def phase_decisions(cfg: Config, r: vr.Record, frozen: md.Frozen, des: ld.LoraDesign, docs_in: dict, floor: dict,
                    r2: dict, r2_cals: dict, sets: dict) -> dict:
    import m10_writer as w  # noqa: PLC0415
    name_y, name_n = cfg.variants()
    dev_ids = {str(d) for d in sets["dev"]}
    try:
        gate = ld.decide_gate(cfg.ids, sets, r.path if cfg.real else None)
    except ld.LoraRefusal as e:
        raise B1sRefusal(f"gate of the decisions: {e}") from None
    cal_v = {name: ld.lora_calibration_file(frozen, des, cfg.entry_d1, e)["calibrations"] | r2_cals
             for name, e in ((name_y, True), (name_n, False))}
    fallback = dict(r.rec.get("fallback_documents") or {})
    problems, counts, first = [], Counter(), True
    for d in cfg.ids:
        rule = docs_in[d]["rules"]
        doc = md.load_doc(d)
        out_files = {name: lv.variant_dir(cfg, name) / f"{d}.json" for name in (name_y, name_n)}
        if all(r.have(p) for p in out_files.values()):
            counts["documents_kept"] += 1
            continue
        if first:
            r.rec["first_value"] = r.rec.get("first_value") or r.event(
                "first_value", what="first block posterior of the frozen B1 head on a document of the run")
            r.save()
            first = False
        why, decs = None, {}
        try:
            for name, e in ((name_y, True), (name_n, False)):
                decs[name] = b1s_decisions(d, gate, frozen, des, cfg.head_states, cfg.entry_d1, e, r2.get(d), dev_ids)
            if any(v is None for v in decs.values()):
                why = "no states file"
            else:
                counts["posteriors_equal_to_m10_design_head_probs"] += 1
        except (ld.LoraRefusal, md.DesignRefusal) as e:
            raise B1sRefusal(f"decisions of B1-S: {e}") from None
        except ValueError as e:
            why = f"B2 form without a path ({str(e)[:80]})"
        if why is not None:
            fl = casc.floor_decisions(rule, floor["lookup"], d in floor["fit_docs"], floor["info"])
            decs = {name: vr.floor_fallback(fl, cfg.entry_d1, False) for name in (name_y, name_n)}
            fallback[d] = why
        bad = []
        for name, dec in decs.items():
            cals = cal_v[name] | (floor["records_without_threshold"] if d in fallback else {})
            bad += [f"{name}: {x}" for x in casc.check_decisions(dec, rule)]
            bad += [f"{name}: {x}" for x in w.check_decisions(d, doc, dec, cals)]
        if bad:
            problems += [f"{d}: {x}" for x in bad]
            for name, dec in decs.items():
                write_json(cfg.out / "decisions_failed" / name / f"{d}.json", dec)
            continue
        for name, dec in decs.items():
            r.output(out_files[name], write_json(out_files[name], dec))
        r.rec["fallback_documents"] = fallback
        r.save()
        counts["documents_made"] += 1
    if problems:
        r.rec.setdefault("decision_check_stops", []).append({"time": now(), "checks_failed": len(problems),
                                                             "problems": problems[:200]})
        r.save()
        raise B1sRefusal(f"{len(problems)} decisions checks failed: the problems are in {rel(r.path)} (key "
                         "decision_check_stops)")
    for name, e in ((name_y, True), (name_n, False)):
        c = cal_v[name] | (floor["records_without_threshold"] if fallback else {})
        p = lv.variant_dir(cfg, name) / "calibrations.json"
        r.output(p, write_json(p, {"calibrations": c, "variant": name, "candidate": "B1-S (addendum D)",
                                   "entry": {"d1": cfg.entry_d1, "b1_s": e}, "status": STATUS}))
    r.rec.setdefault("phase_decisions", []).append({
        "documents": len(cfg.ids), **dict(counts), "variants": [name_y, name_n],
        "decision_checks": "each file of each document passed",
        "documents_with_floor_fallback": len(fallback),
        "fallback_reasons": dict(Counter(v.split(" (")[0] for v in fallback.values())), "finished": now()})
    r.save()
    return {"fallback": fallback}


# ---------------------------------------------------------------- phase B: measures with the names of B1-S

def b1s_measures(m: dict, cfg: Config, des: ld.LoraDesign) -> dict:
    """The measures of m10_lora_validation.phase_measures with the names of B1-S. No value changes. The choice of
    criteria 7.3 item 5 is not a rule of B1-S: the value of addendum D, rule D2 item 3 takes its place."""
    name_y, _ = cfg.variants()
    e = m["entry"]
    g = dict(e["GJ.17"])
    enters = bool(e["b1_l_enters"])
    g.update({"criterion": "addendum D, rule D2 items 2 and 5: the 3 conditions of criteria 7.2 with B1-S in place "
                           "of B1 and B2; cut of criteria 7.3 item 4",
              "method": f"written path of B1-S (frozen B1 head with its frozen temperature, B2 form {des.form}) on "
                        f"the non-certain blocks (variant {name_y})",
              "status": "B1-S enters" if enters else "B1-S does not enter"})
    head = e["run_of_the_heads"]
    c = des.record["choices"]["choice_d2_item_3"]
    choice = {"rule": "addendum D, rule D2 items 3 and 4 (dev out-of-fold values only; design_b1s.json)",
              "dev_non_certain_blocks": c["non_certain_blocks"], "dev_correct_b1_s": c["correct_b1_s"],
              "dev_accuracy_b1_s": c["accuracy_b1_s"], "tie": c["tie"], "tie_gives": c["tie_gives"],
              "b1_s_enters": enters,
              "b1_and_b2_entered_in_the_run_of_the_heads": None if head is None else head.get("b1_b2_enter"),
              "block_step": "not decided by this script: it depends on the validation run of B1-L (rule D2 items 3 "
                            "and 4); the main agent records the choice"}
    g21 = m["GJ.21"]
    l9 = g21["l9"]
    return {"schema": "parlpdfech-gj-validation-b1s-measures/1", "status": m["status"], "candidate": "B1-S (addendum D)",
            "made": m["made"], "documents": m["documents"], "split": m["split"],
            "counts_against_criteria_chapter_3": m["counts_against_criteria_chapter_3"],
            "documents_with_floor_fallback": m["documents_with_floor_fallback"],
            "entry": {"B1-S": g, "variant": e["variant"], "d1_enters_by_option": e["d1_enters_by_option"],
                      "b1_s_enters": enters, "choice_d2": choice, "run_of_the_heads": head},
            "GJ.13": m["GJ.13"],
            "GJ.21": {"variant": g21["variant"], "variant_measures": g21["variant_measures"],
                      "variant_b1s_not_entered_information": g21["variant_b1l_not_entered_information"],
                      "l9": {"rules_nos4": l9["rules_nos4"], "b1s_entered": l9["b1l_entered"],
                             "b1s_not_entered": l9["b1l_not_entered"]},
                      "reference_sources_of_l9": g21["reference_sources_of_l9"],
                      "note": "the D1 label of each variant is the D1 label of the frozen design (B1-S does not "
                              "change D1)"},
            "variants_information": m["variants_information"],
            "calibration_ids_of_the_variant_blocks": m["calibration_ids_of_the_variant_blocks"],
            "measure_functions": "m10_lora_validation.phase_measures (bootstrap, entry conditions, GJ.13, GJ.21); "
                                 "names by m10_b1s.b1s_measures"}


def phase_measures(cfg: Config, frozen: md.Frozen, des: ld.LoraDesign, docs_in: dict, floor: dict, cnt: np.ndarray,
                   fallback: dict, head: dict | None) -> dict:
    """m10_lora_validation.phase_measures on the decisions of B1-S, then the names of B1-S. That function reads
    the key choice_7_3_item_5 of a design of B1-L: it gets an empty entry, and b1s_measures does not keep it."""
    shim = dataclasses.replace(des, record={**des.record, "choices": {
        **des.record["choices"], "choice_7_3_item_5": {"choice": None, "accuracy_b1_l": None, "accuracy_b1": None}}})
    return b1s_measures(lv.phase_measures(cfg, frozen, shim, docs_in, floor, cnt, fallback, head), cfg, des)


# ---------------------------------------------------------------- result.md (English STE)

def result_markdown(res: dict) -> str:
    m, run = res["measures"], res["run"]
    e = m["entry"]
    gs, g13, g21 = e["B1-S"], m["GJ.13"], m["GJ.21"]
    g = gs["accuracy_gain_non_certain"]
    ds = res["checks"]["design_b1s"]
    L = []
    add = L.append
    kind = "the one validation run of B1-S" if run["real"] else "a check run on dev documents (not a held-out run)"
    add("# Gate GJ: result of the validation run of B1-S (addendum D)")
    add("")
    add(f"Run of {run['started']} to {run['finished']} (time from the clock). This file is the result of {kind}. "
        f"Script `src/m10_b1s.py`, SHA-256 `{run['script_sha256']}`.")
    add("")
    add("Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: workflow sub-agent "
        "(Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    add("B1-S is the candidate of addendum D to the criteria: the block posteriors of the frozen B1 head with its "
        f"frozen temperature, and the B2 form `{gs['b2_form']}` of addendum C. B1-S has no training.")
    add("")
    add("## 1 Order of the records and checks")
    add("")
    add(f"1. The script wrote its SHA-256 into `run.json` at {run['script_sha256_recorded']}.")
    add(f"2. The checks passed at {run['checks_passed']}. The first value came at {run['first_value']}.")
    add(f"3. Freeze file: `{run['freeze']['path']}`, SHA-256 `{run['freeze']['sha256']}`. The head files and each "
        "other design file have the SHA-256 of the freeze file.")
    add(f"4. Design of B1-S: `{ds['design_b1s_json']['path']}`, SHA-256 `{ds['design_b1s_json']['sha256']}`. B2 "
        f"form: `{gs['b2_form']}`. Strength: {_f(gs['strength'], 0)}. First temperature: {_f(ds['temperature_b1'])} "
        f"(the frozen temperature of the B1 head). Second temperature: {_f(ds['temperature_b2'])}.")
    add(f"5. Documents: {m['documents']} of the set `{m['split']}`. Documents with the floor labels (no states or no "
        f"path of the form): {len(m['documents_with_floor_fallback'])}.")
    add(f"6. Block posteriors: the frozen B1 head on the GPU-1 states of each document. Documents for which "
        f"softmax(logits / T) was equal to `m10_design.head_probs`: {res['posterior_checks']}.")
    add("7. Checks before the first value: guard and `m00_pruefe_testset.py` (0 test documents), freeze file, frozen "
        "code (0 changes), FROZEN_FILES (0 changes), template items (equal), scorer reproduction (MET), GPU-1 states "
        "(equal), criteria and addenda B, C and D (equal), design of B1-S (equal).")
    add("8. This file is equal to the script of the design of B1-S: "
        f"{_f(ds['this_file_equal_to_the_design_script'])}. The design choices are fixed by the SHA-256 of "
        "`design_b1s.json`.")
    if m.get("counts_against_criteria_chapter_3"):
        cc = m["counts_against_criteria_chapter_3"]
        add(f"9. Counts against criteria chapter 3: documents {_f(cc['documents'])}, switch documents "
            f"{_f(cc['switch_documents'])}.")
    add("")
    add("## 2 Entry decision of B1-S (addendum D, rule D2)")
    add("")
    add("| Value | B1-S |")
    add("|---|---|")
    add(f"| Units | {g['units']} non-certain blocks |")
    add(f"| Accuracy of the method | {_f(g['method'])} |")
    add(f"| Accuracy of the baseline | {_f(g['baseline'])} |")
    add(f"| Gain | {_f(g['gain'])} |")
    add(f"| 5 % quantile of the gain | {_f(g['low_5'])} |")
    add(f"| 95 % quantile of the gain | {_f(g['high_95'])} |")
    add(f"| Condition 1: 5 % quantile more than 0 | {_f(gs['condition_1_lower_bound_above_0'])} |")
    add(f"| Condition 2 | L9 exact: method {gs['l9_exact_method']}, rules {gs['l9_exact_rules']}: "
        f"{_f(gs['condition_2_l9'])} |")
    add(f"| Condition 3 | switch documents {gs['switch_documents']}: method {gs['switch_exact_method']}, rules "
        f"{gs['switch_exact_rules']}: {_f(gs['condition_3_switch'])} |")
    add(f"| Value before the cut of 14.10.2026, 08:00 | {_f(gs['cut']['before_the_cut'])} |")
    add(f"| Enters | {_f(gs['enters'])} |")
    add("")
    add(f"1. Result: {gs['status']}. Certain blocks: {gs['certain_blocks']}. Non-certain blocks: "
        f"{gs['non_certain_blocks']}.")
    add("2. The baseline is the rule option of each block from `src/m10_rules.py` (criteria 6.1, item 10). The L9 "
        "counts of the rules use the same rule output.")
    i = gs["information"]
    add(f"3. Information: accuracy on all blocks {_f(i['accuracy_all_blocks_method'])} against "
        f"{_f(i['accuracy_all_blocks_rules'])} for the rules. Macro F1 of the 6 options: "
        f"{_f(i['macro_f1_6_all_blocks_method'])} against {_f(i['macro_f1_6_all_blocks_rules'])}.")
    c = e["choice_d2"]
    add(f"4. Value of addendum D, rule D2, item 3 (`dev` only): the accuracy of B1-S on the "
        f"{c['dev_non_certain_blocks']} non-certain `dev` blocks is {_f(c['dev_accuracy_b1_s'], 6)}. If B1-S and "
        "B1-L both enter, the higher `dev` value wins. A difference of 0.005 or less gives B1-S.")
    add("5. This script does not make the choice between B1-S and B1-L. It depends on the validation run of B1-L "
        "(rule D2, items 3 and 4).")
    add("6. The bootstrap uses 2,000 resamples of the documents with the seed 20261013 (criteria 6.3).")
    if c.get("b1_and_b2_entered_in_the_run_of_the_heads") is not None:
        add(f"7. B1 and B2 entered in the run of the heads: {_f(c['b1_and_b2_entered_in_the_run_of_the_heads'])}.")
    add("")
    add("## 3 Calibration of the written block labels (GJ.13)")
    add("")
    add("| Variant | Blocks | Accuracy | ECE | 95 % bound | Brier (6 options) | NLL (6 options) | Result |")
    add("|---|---|---|---|---|---|---|---|")
    add(f"| `{g13['variant']}` | {g13['blocks']} | {_f(g13['accuracy_written'])} | {_f(g13['ece'])} | "
        f"{_f(g13['ece_bootstrap']['high_95'])} | {_f(g13['brier_6_options'])} | {_f(g13['nll_6_options'])} | "
        f"{g13['status']} |")
    add("")
    add("1. The limits are ECE 0.05 or less and a 95 % bound of 0.08 or less. The bins use p of the written option.")
    add(f"2. The variant `{g13['variant']}` is the variant in which B1-S decides the non-certain blocks.")
    add("")
    add("## 4 Measures of the block labels (GJ.21)")
    add("")
    add("| Label kind | n | Accuracy of the top label | ECE | Class-wise ECE | Brier | NLL |")
    add("|---|---|---|---|---|---|---|")
    vm = g21["variant_measures"]
    for key, text in (("block_slot", "block option, all blocks"), ("block_slot_non_certain", "block option, "
                      "non-certain blocks"), ("author_switch_all_gaps", "switch boundary, all gaps")):
        x = vm[key]
        add(f"| {text} | {_f(x.get('n'))} | {_f(x.get('accuracy_top_label'))} | {_f(x.get('ece'))} | "
            f"{_f(x.get('classwise_ece'))} | {_f(x.get('brier'))} | {_f(x.get('nll'))} |")
    add("")
    add("| Answer set | L9 exact documents | Switch documents exact | Labelled boundary F1 | Text intrusion | "
        "6-option accuracy (all blocks) | Macro F1 (6 options) |")
    add("|---|---|---|---|---|---|---|")
    for key, text in (("rules_nos4", "rules"), ("b1s_entered", "B1-S decides"), ("b1s_not_entered", "rules with the "
                      "rule view of the cascade")):
        a, bl = g21["l9"][key]["all_documents"], g21["l9"][key]["blocks_6"]
        add(f"| {text} | {a['exact']} of {a['documents']} | {a['switch_sr']['exact']} of {a['switch_sr']['documents']} "
            f"| {_f(a['labelled_f1'])} | {_f(a['text_intrusion'])} | {_f(bl['accuracy_6'])} | {_f(bl['macro_f1_6'])} |")
    add("")
    for k, (name, v) in enumerate(m["variants_information"].items(), 1):
        add(f"{k}. Value status of the variant `{name}`: {vr._kv(v['value_status'])}. Written switch labels: "
            f"{v['switch_labels']}.")
    add("")
    g12 = res.get("GJ.12")
    add("## 5 Records (GJ.12, part validation of B1-S)")
    add("")
    if g12 is None:
        add("The run made no records (check run with the option `--no-records`).")
    else:
        add(f"1. GJ.12: {g12['status']}. Valid documents: {g12['documents_valid']} of {g12['documents']}. Documents "
            f"with all files: {g12['documents_with_all_files']}. Failed documents: {g12['failed_documents']}.")
        add(f"2. linkml errors: {g12['linkml_errors']}. Documents with a recorded gap (addendum A): "
            f"{g12['documents_with_recorded_gaps']}. Gap slots: {vr._kv(g12['recorded_gap_slots'])}.")
        add(f"3. Checks passed (documents): {vr._kv(g12['checks_passed'])}.")
        add(f"4. The records hold the labels of the variant `{g13['variant']}`. Folder: `{g12['records']}`. Base IRI: "
            f"`{g12['base_iri']}`. Check C10 (SHACL) is information (addendum A, rule A3): {vr._kv(g12['c10_shacl'])}.")
    add("")
    add("## 6 Limits")
    add("")
    add("1. This is the second validation run for the block step on these 44 documents. The run of the heads (B1 "
        "with B2) came first. A run of B1-L can follow (addendum D, limit 2).")
    add("2. Thus a value of B1-S on these documents is too good as an estimate for new documents. By criteria "
        "chapter 10.3, item 5, a strict reader takes the values of this run as information only.")
    add("3. B1-S and the B2 forms of addendum C were designed after the aggregate result of the run of the heads "
        "was known. That run showed the weakness at the switch. The same weakness was recorded on `dev` before it.")
    add("4. No value of a validation document was used for a choice of B1-S. Each choice uses `dev` out-of-fold "
        "values only.")
    add("5. The reference is an AI reference without a human acceptance.")
    add("6. The set is small: 44 documents and 10 switch documents. The intervals are wide.")
    add("7. The rules saw 42 of the 44 validation documents. This favours the rules and each form with rule gaps.")
    add("8. Group 7 has no run yet. It is the check on documents that no choice used.")
    add("9. A value of this file is not a value of gate GJ before the second calculation (GJ.19).")
    add("10. Jonathan did not accept the criteria or the addenda B, C and D. All values have the status EXCEPTION.")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- run

def run(cfg: Config) -> dict:
    t0 = time.perf_counter()
    dj = cfg.design_b1s / "design_b1s.json"
    if cfg.real and not cfg.records:
        raise B1sRefusal("the validation run of B1-S always writes the records (GJ.12): --no-records is only for a "
                         "check run; the run writes no file")
    if cfg.real and not dj.is_file():
        raise B1sRefusal(f"no design of B1-S in {rel(cfg.design_b1s)}: the run writes no file")
    if cfg.real and sha(dj) != cfg.design_b1s_sha:
        raise B1sRefusal("the SHA-256 of design_b1s.json is not the value of --design-b1s-sha256 (the value of the "
                         "protocol): the run writes no file")
    constants = set_process_constants()
    r = start_record(cfg, constants)
    log = open(cfg.out / "run.log", "a", encoding="utf-8")
    vr.SAY = sys.stdout
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            return _run(cfg, r, t0)
    except BaseException as e:
        refusal = isinstance(e, RunRefusal)
        reason = str(e) if refusal else f"{type(e).__name__}: {str(e)[:1500]}"
        r.rec["state"] = "stopped" if r.rec.get("first_value") else "refused"
        r.rec["state_text"] = ("stopped after the first value: only --continue-missing continues the run"
                               if r.rec.get("first_value") else
                               "stopped before the first value: no value exists; a new start is possible")
        r.rec["stop"] = {"time": r.event("stopped", reason=reason[:500] if refusal else type(e).__name__),
                         "reason": reason[:2000], "kind": "refusal" if refusal else "error"}
        r.save()
        raise
    finally:
        log.close()


def _run(cfg: Config, r: vr.Record, t0: float) -> dict:
    sets = md.load_sets()
    vcfg = cfg.vcfg()
    checks = {"guard": vr.guard_ids(vcfg, sets)}
    say(f"guard: {len(cfg.ids)} documents of the split {cfg.split}, 0 test documents")
    if cfg.records:
        checks["record_phase"] = vr.record_phase_check()
    frozen, _fz, fc = lv.freeze_checks(cfg, sets)
    checks["freeze"] = fc
    checks["states"] = vr.states_check(vcfg)
    des, checks["design_b1s"] = design_check(cfg, frozen)
    if cfg.real and not cfg.no_r2 and (cfg.r2 is None or cfg.r2_cal is None):
        raise B1sRefusal("the real run needs --r2 and --r2-calibrations (the files of the run of the heads), or the "
                         "option --no-r2")
    r2 = vr.load_r2(cfg.r2)
    r2_cals = vr.load_calibration_records(cfg.r2_cal)
    if cfg.r2 is not None:
        without = [d for d in cfg.ids if d not in r2]
        missing = sorted({v["calibration"] for v in r2.values()} - set(r2_cals))
        if (cfg.real and without) or missing:
            raise B1sRefusal(f"R2: {len(without)} documents without a value, calibration ids without a record: "
                             f"{missing}")
    checks["r2"] = {"documents_with_r2": sum(1 for d in cfg.ids if d in r2), "options": r.rec["options"]["r2"]}
    floor = vr.floor_inputs()
    docs_in = cal.load_documents(cfg.ids, with_labels=True)
    cnt = lv.draws_check(len(cfg.ids))
    checks["bootstrap"] = {"resamples": lv.N_BOOT, "seed": lv.SEED, "equal_to_m10_calibrate": True}
    head = lv.head_run_values(cfg)
    checks["run_of_the_heads"] = head
    if r.rec.get("checks"):
        r.rec.setdefault("checks_of_the_continuations", []).append(checks)
    else:
        r.rec["checks"] = checks
        r.rec["checks_passed"] = r.event("checks_passed")
    r.save()
    say(f"checks passed: freeze {fc['sha256'][:12]}..., design of B1-S {des.sha256[:12]}... (form {des.form}), "
        f"states files {checks['states']['with_states']} of {len(cfg.ids)} with the SHA-256 of outputs.json")
    # ---- phase A
    pa = phase_decisions(cfg, r, frozen, des, docs_in, floor, r2, r2_cals, sets)
    say(f"decisions: {len(cfg.ids)} documents, 2 variants; documents with the floor labels: {len(pa['fallback'])}")
    # ---- phase B
    mp = cfg.out / "measures.json"
    if r.have(mp):
        meas = read_json(mp)
    else:
        meas = phase_measures(cfg, frozen, des, docs_in, floor, cnt, pa["fallback"], head)
        r.output(mp, write_json(mp, meas))
        r.rec["measures_made"] = r.event("measures_made")
        r.save()
    gs, g13 = meas["entry"]["B1-S"], meas["GJ.13"]
    say(f"entry of B1-S: {gs['status']}; GJ.13 {g13['status']}")
    # ---- phase C
    g12 = None
    if cfg.records:
        g12 = vr.phase_records(vcfg, r, meas)
        say(f"GJ.12 (part {cfg.split}, B1-S): {g12['status']}, valid documents {g12['documents_valid']} of "
            f"{g12['documents']}, failed {g12['failed_documents']}, with recorded I95 gaps "
            f"{g12['documents_with_recorded_gaps']}")
    meas = vr.gj21_gap_count(vcfg, r, meas, g12)
    # ---- end checks
    ff = md.frozen_files()
    if lv.module_sha() != r.rec["modules"]:
        raise B1sRefusal("a script changed during the run")
    if ff["different"]:
        raise B1sRefusal(f"GJ.4: FROZEN_FILES changed during the run: {ff['different']}")
    if sha(vr.FREEZE) != ld.FREEZE_SHA or sha(des.dir / "design_b1s.json") != des.sha256:
        raise B1sRefusal("the freeze file or design_b1s.json changed during the run")
    r.rec["finished"] = r.event("finished")
    made = sum(int(x.get("posteriors_equal_to_m10_design_head_probs") or 0) for x in r.rec.get("phase_decisions") or [])
    run_info = {"real": cfg.real, "started": r.rec["started"], "finished": r.rec["finished"],
                "script_sha256": r.rec["script"]["sha256"], "script_sha256_recorded": r.rec["script_sha256_recorded"],
                "checks_passed": r.rec["checks_passed"], "first_value": r.rec.get("first_value"),
                "freeze": r.rec["freeze"], "continued": r.rec.get("continued") or [],
                "process_constants": r.rec["process_constants"], "seconds": round(time.perf_counter() - t0, 1)}
    res = {"schema": "parlpdfech-gj-validation-b1s-result/1", "status": STATUS, "candidate": "B1-S (addendum D)",
           "run": run_info, "checks": checks, "posterior_checks": made, "measures": meas, "GJ.12": g12,
           "frozen_files_at_the_end": {"files": ff["files"], "different": ff["different"]}}
    rp = cfg.out / "result.json"
    r.output(rp, write_json(rp, res))
    mdp = cfg.out / "result.md"
    mdp.write_text(result_markdown(res), encoding="utf-8")
    r.output(mdp)
    r.rec["state"] = "finished"
    r.rec["state_text"] = "the run is finished (one run: criteria 10.3)"
    r.rec["seconds"] = run_info["seconds"]
    r.save()
    g = gs["accuracy_gain_non_certain"]
    return {"run": rel(r.path), "result_json": {"path": rel(rp), "sha256": sha(rp)},
            "result_md": {"path": rel(mdp), "sha256": sha(mdp)},
            "entry_b1_s": {"status": gs["status"], "enters": gs["enters"], "units": g["units"],
                           "method": r6(g["method"]), "baseline": r6(g["baseline"]), "gain": r6(g["gain"]),
                           "low_5": r6(g["low_5"]), "l9_method": gs["l9_exact_method"],
                           "l9_rules": gs["l9_exact_rules"], "switch_method": gs["switch_exact_method"],
                           "switch_rules": gs["switch_exact_rules"],
                           "conditions": [gs["condition_1_lower_bound_above_0"], gs["condition_2_l9"],
                                          gs["condition_3_switch"]], "before_the_cut": gs["cut"]["before_the_cut"]},
            "b2_form": gs["b2_form"], "variant": meas["entry"]["variant"],
            "GJ.13": {"status": g13["status"], "accuracy_written": g13["accuracy_written"], "ece": r6(g13["ece"]),
                      "high_95": r6(g13["ece_bootstrap"]["high_95"])},
            "GJ.12": None if g12 is None else {k: g12[k] for k in ("status", "documents", "documents_valid",
                                                                    "documents_with_recorded_gaps")},
            "documents_with_floor_fallback": len(meas["documents_with_floor_fallback"]),
            "dev_accuracy_b1_s": meas["entry"]["choice_d2"]["dev_accuracy_b1_s"], "seconds": run_info["seconds"]}


# ---------------------------------------------------------------- command line

def config_of(args) -> Config:
    yes = {"yes": True, "no": False}
    r2 = Path(args.r2).resolve() if args.r2 else None
    r2c = Path(args.r2_calibrations).resolve() if args.r2_calibrations else None
    if not args.check_run:
        if args.docs or args.work or args.design_b1s or args.no_records:
            raise B1sRefusal("--docs, --work, --design-b1s and --no-records are only for --check-run")
        if not args.design_b1s_sha256:
            raise B1sRefusal("the real run needs --design-b1s-sha256 (the SHA-256 of design_b1s.json of the protocol)")
        sets = md.load_sets()
        return Config(real=True, ids=vr.by_id(sets["validation"]), split="validation", out=OUT_RUN,
                      decisions_out=OUT_RUN / "decisions_records", design_b1s=OUT_DESIGN, entry_d1=yes[args.entry_d1],
                      design_b1s_sha=args.design_b1s_sha256, r2=r2, r2_cal=r2c, no_r2=args.no_r2,
                      continue_missing=args.continue_missing, records=True)
    if not (args.docs and args.work and args.design_b1s):
        raise B1sRefusal("--check-run needs --docs, --work and --design-b1s")
    work = Path(args.work).resolve()
    if work.is_relative_to(GJ.resolve()):
        raise B1sRefusal("the check run never writes to daten/gj")
    guard.check_path(work)
    ids = vr.by_id(i for a in args.docs for i in guard.read_items(a))
    return Config(real=False, ids=ids, split="dev", out=work / "validation_b1s",
                  decisions_out=work / "validation_b1s" / "decisions_records",
                  design_b1s=Path(args.design_b1s).resolve(), entry_d1=yes[args.entry_d1], r2=r2, r2_cal=r2c,
                  no_r2=True, continue_missing=args.continue_missing, records=not args.no_records)


def cmd_design(args) -> int:
    out = Path(args.out)
    rec = run_design(out, check_run=args.check_run)
    ch, tab = rec["choices"], rec["dev_table"]
    form = ch["b2"]["form"]
    row, rules = tab["forms"][form], tab["rules"]
    keys = ("accuracy_non_certain", "l9_exact", "switch_exact", "labelled_boundary_f1")
    print(json.dumps({
        "design_b1s_json": {"path": rel(out.resolve() / "design_b1s.json"),
                            "sha256": sha(out.resolve() / "design_b1s.json")},
        "T_frozen": r6(ch["b1"]["T"]), "form": form, "permitted": ch["b2"]["selection"]["permitted"],
        "strength_by_fold": None if ch["b2"]["strength"] is None else ch["b2"]["strength"]["by_fold"],
        "strength_final": ch["b2"]["strength_final"], "T2": r6(ch["b2"]["t2_T"]), "thresholds": ch["thresholds"],
        "dev_out_of_fold": {**{k: row[k] for k in keys},
                            "ece_b2_marginals": rec["measures_information"]["b2_marginals_after_t2"]["ece"]},
        "rules": {k: rules[k] for k in keys},
        "table": {f: {**{k: r[k] for k in keys}, "ece_after_t2": r["ece_block_marginals_after_t2_information"]}
                  for f, r in tab["forms"].items()},
        "d2_item_3_dev_accuracy_b1_s": ch["choice_d2_item_3"]["accuracy_b1_s"],
        "stored_table_equal": (tab["stored_table_of_the_head_values"] or {}).get("equal"),
        "outputs": rec["outputs"]}, ensure_ascii=False, indent=1))
    return 0


def cmd_validate(args) -> int:
    summary = run(config_of(args))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("design", help="the dev design of B1-S from the stored out-of-fold posteriors of the B1 head")
    d.add_argument("--out", default=str(OUT_DESIGN))
    d.add_argument("--check-run", action="store_true", help="another output folder outside daten/gj (check script)")
    d.set_defaults(func=cmd_design)
    v = sub.add_parser("validate", help="the one validation run of B1-S (only the main agent starts the real run)")
    v.add_argument("--entry-d1", choices=("yes", "no"), required=True,
                   help="the entry decision GJ.15 of the validation run of the heads (D1 label of the records)")
    v.add_argument("--design-b1s-sha256", help="real run: the SHA-256 of design_b1s.json of the protocol")
    v.add_argument("--r2")
    v.add_argument("--r2-calibrations")
    v.add_argument("--no-r2", action="store_true", help="real run without R2 labels in the records")
    v.add_argument("--continue-missing", action="store_true")
    v.add_argument("--check-run", action="store_true")
    v.add_argument("--docs", nargs="*")
    v.add_argument("--work")
    v.add_argument("--design-b1s")
    v.add_argument("--no-records", action="store_true", help="check run only: no record phase (no GJ.12)")
    v.set_defaults(func=cmd_validate)
    args = ap.parse_args()
    try:
        return args.func(args)
    except (RunRefusal, ld.LoraRefusal, md.DesignRefusal) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

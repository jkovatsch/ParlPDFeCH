"""Gate GJ (status EXCEPTION), criteria chapters 6, 7.3, 9 and 10.3, addenda A, B and C: the one validation run of
B1-L and the entry decision GJ.17.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream D2,
for the main agent. No human checked this file. This file changes no existing file. It imports the frozen
functions of src/m10_validation_run.py, src/m10_design.py, src/m10_calibrate.py, src/m10_cascade.py and
src/m10_score.py, and the design of B1-L (src/m10_lora_design.py, src/m10_b2x.py). Status of each output:
EXCEPTION (process rule 10), NOT RELEASED. The main agent runs the real run. This file is an addition after the
design freeze (criteria chapter 10.2 item 2; addendum B, rule B2 item 3).

0 Order of the records (GJ.2) and the one-run rule (criteria 10.3; addendum B, rule B2 item 3)
  The run record <out>/run.json gets the SHA-256 of this file and of each imported m10 module before the first
  value. The event log <out>/run.events.jsonl gives the clock time of each event: script_sha256, checks_passed,
  first_value. A second run is refused when <out>/run.json exists. State refused: the run stopped before the first
  value; a new start is possible, and the record stays as run.refused-<time>.json. State stopped: the run stopped
  after the first value; only --continue-missing continues it, with the same script, the same design of B1-L, the
  same documents and the same options. It makes only the outputs that do not exist with the SHA-256 of the record.

1 Inputs (explicit paths)
  documents    the key validation of daten/gj/sets.json (44 documents), in the order of the numeric doc id.
  freeze       daten/gj/design_freeze.json with the SHA-256 add6fdad... (m10_lora_design.FREEZE_SHA); the frozen
               design daten/gj/design/ and the GPU-1 states (D1 posterior, rule view of an R1 document).
  design B1-L  daten/gj/design_lora/design_lora.json (finished, not a check run) and its output files with the
               SHA-256 of that record. The real run needs --design-lora-sha256: the SHA-256 of design_lora.json
               of the protocol.
  logits       daten/gj/states/lora_b1/final/logits/<doc>.npz with the SHA-256 of final/run.json. The folder also
               holds the files of the group-7 documents: the run never opens them (no method freeze).
  addenda      the addenda B and C with the SHA-256 of m10_lora_design.ADDENDA; addendum A by the freeze file.
  rules, labels  as src/m10_validation_run.py (m10_calibrate.load_documents with the SHA-256 checks).
  R2           --r2 FILE and --r2-calibrations FILE (the files of the validation run of the heads). The real run
               needs them or the option --no-r2 (then the records hold no R2 label).
  D1           --entry-d1 yes|no: the entry decision GJ.15 of the validation run of the heads (protocol). It sets
               only the D1 label of the records. The block labels do not depend on it. If
               daten/gj/validation/measures.json exists, its key entry.d1_enters must agree (only the keys
               entry.d1_enters and entry.b1_b2_enter of that file are read).

2 Checks before the first value (a failed check refuses the run; nothing is measured)
  guard (m10_guard, m00_pruefe_testset), addenda and criteria, freeze file and frozen code (GJ.11: each frozen
  file that this run uses is unchanged; the new files are listed as additions), GJ.11 inputs, FROZEN_FILES
  (GJ.4), template (GJ.8), scorer reproduction (GJ.6), GPU-1 states against outputs.json, design of B1-L,
  job folder and logits files against run.json (no logit is read), packages of the record phase, R2 files,
  bootstrap draws, the D1 entry value.

3 Decisions (phase A)
  Variants: d1<y|n>_b1ly (B1-L and its B2 form decide the non-certain blocks) and d1<y|n>_b1ln (the rule option
  decides, B1-L gives the verifier probability; information). d1<y|n> is the value of --entry-d1.
  m10_lora_design.lora_decisions makes each file; each file passes check_decisions of src/m10_cascade.py and of
  src/m10_writer.py before it is an output. A document without a states file, without a logits file or without a
  path of the B2 form gets the floor decisions with the value status unsure (criteria 4 item 7). The run record
  lists such documents.

4 Measures and the entry decision (phase B; <out>/measures.json)
  bootstrap  numpy.random.default_rng(20261013).integers(0, D, size=(2000, D)), documents in the order of the
             numeric doc id; 5 % and 95 % quantiles; paired: method minus baseline (criteria 6.3).
  GJ.17      criteria 7.3 item 3 = the 3 conditions of criteria 7.2 with B1-L and its B2 form in place of B1 and
             B2 (function entry_blocks of src/m10_validation_run.py). Units: the non-certain blocks. Method: the
             option of the block in the variant b1ly. Baseline: the rule option of src/m10_rules.py (criteria 6.1
             item 10; decision M7). Conditions 2 and 3: L9 exact documents and switch-document exact (key
             switch_sr) through m10_score.score_set on all documents, method not lower than the rules minus 1.
             Cut (criteria 7.3 item 4): the value must exist before 14.10.2026, 08:00.
  GJ.13      the written block labels of the variant b1ly on all blocks: ECE of p of the written option and the
             95 % bound of the document bootstrap. MET if ECE <= 0.05 and the bound <= 0.08.
  GJ.21      the measures of criteria 6.2 for the variant b1ly (m10_validation_run.kind_measures) and, as
             information, for the variant b1ln; the L9 values of the rules and of both variants.
  The choice of criteria 7.3 item 5 comes from design_lora.json (dev values only). It is reported.

5 Records (phase C, GJ.12; addendum A)
  The decisions of the variant b1ly go to daten/gj/decisions_validation_lora/ with calibrations.json. Then
  m10_validation_run.phase_records: writer, RDF and validator into <out>/records/<doc>/, base IRI
  https://parlpdfech.ansv.ch/id/. GJ.12 is the function gj12 of src/m10_validation_run.py.

6 Outputs and console
  <out>/run.json, run.events.jsonl, run.log, decisions/<variant>/<doc>.json, measures.json, result.json,
  result.md, records/. Default <out>: daten/gj/validation_lora/. The console shows only counts, aggregate values,
  file paths and SHA-256 values: no value of one document.

7 Check run (--check-run; for src/m10_lora_validation_test.py)
  The same chain on dev documents (--docs) with the design of a check run (--design-lora) and stand-in logits
  (--states-lora) into --work (outside daten/gj). It refuses each document that is not a dev document before a
  file of the document is read. It never writes to daten/gj. A dev document reads the logits of its fold run.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_lora_validation.py --entry-d1 no
      --design-lora-sha256 SHA --r2 FILE --r2-calibrations FILE [--continue-missing]
  uv run --offline --frozen --no-sync --with linkml==1.11.1 python src/m10_lora_validation.py --check-run
      --docs ID [ID ...] --work DIR --design-lora DIR --states-lora DIR --entry-d1 no [--no-records]
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard of process rule 6)
import m10_design as md  # noqa: E402  (frozen design; not changed)
import m10_calibrate as cal  # noqa: E402  (measures, bootstrap, floor lookup; not changed)
import m10_cascade as casc  # noqa: E402  (floor mode, check_decisions; not changed)
import m10_score as ms  # noqa: E402  (scorer of L9 and of the blocks; not changed)
import m10_validation_run as vr  # noqa: E402  (the frozen runner: its functions by import; not changed)
import m10_b2x as bx  # noqa: E402  (B2 forms of addendum C)
import m10_lora_design as ld  # noqa: E402  (design of B1-L and its decisions)

VERSION = "m10-lora-validation-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = md.GJ
OUT = GJ / "validation_lora"
DECISIONS_OUT = GJ / "decisions_validation_lora"
HEAD_MEASURES = GJ / "validation/measures.json"
STATUS = vr.STATUS
ACTOR = "workflow sub-agent (Claude Opus 5.5), stream D2, for the main agent"
N_BOOT, SEED = 2000, 20261013
GJ13_ECE, GJ13_HIGH = vr.GJ13_ECE, vr.GJ13_HIGH
CUT = dt.datetime(2026, 10, 14, 8, 0, tzinfo=dt.timezone(dt.timedelta(hours=2)))   # criteria 7.3 item 4 (CEST)
EXPECTED = {"documents": 44, "switch_documents": 10}                                # criteria chapter 3
NEW_MODULES = ("m10_lora_validation", "m10_lora_design", "m10_b2x")
OPTIONS = md.OPTIONS

RunRefusal = vr.RunRefusal
sha, rel, read_json, write_json, r6, say, now = vr.sha, vr.rel, vr.read_json, vr.write_json, vr.r6, vr.say, vr.now


@dataclass
class Config:
    real: bool
    ids: list[str]
    split: str
    out: Path
    decisions_out: Path
    design_lora: Path
    states_lora: Path
    job: Path
    entry_d1: bool
    head_states: Path = vr.STATES
    design_lora_sha: str | None = None
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
        return f"d1{e}_b1ly", f"d1{e}_b1ln"


def variant_dir(cfg: Config, name: str) -> Path:
    return cfg.out / "decisions" / name


# ---------------------------------------------------------------- run record (GJ.2, one-run rule)

def module_sha() -> dict:
    names = (*NEW_MODULES, "m10_validation_run", *vr.MODULES)
    out = {}
    for n in names:
        p = ROOT / "src" / f"{n}.py"
        if p.is_file():
            out[rel(p)] = sha(p)
    return out


def options_record(cfg: Config) -> dict:
    def entry(f) -> dict | None:
        return None if f is None else {"path": rel(f), "sha256": sha(f) if Path(f).is_file() else "absent"}
    dj = cfg.design_lora / "design_lora.json"
    return {"entry_d1": cfg.entry_d1, "r2": entry(cfg.r2), "r2_calibrations": entry(cfg.r2_cal), "no_r2": cfg.no_r2,
            "design_lora": entry(dj), "states_lora": rel(cfg.states_lora), "job": rel(cfg.job),
            "records": bool(cfg.records)}


def start_record(cfg: Config) -> vr.Record:
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
            raise RunRefusal(f"one-run rule (criteria 10.3; addendum B): {rel(r.path)} exists (state "
                             f"{old.get('state')}); only --continue-missing after a technical stop")
        if old.get("state") == "finished":
            raise RunRefusal(f"one-run rule (criteria 10.3): the run of {rel(r.path)} is finished")
        if (old.get("script") or {}).get("sha256") != script_sha or old.get("modules") != module_sha():
            raise RunRefusal("--continue-missing: this file or a module differs from the run record")
        if old.get("documents") != cfg.ids or old.get("options") != opts:
            raise RunRefusal("--continue-missing: the documents or the options differ from the first start")
        r.rec = old
        r.rec["state"] = "started"
        r.rec.setdefault("continued", []).append(r.event("continued", sha256=script_sha))
        r.save()
        return r
    if cfg.continue_missing:
        raise RunRefusal("--continue-missing needs the run record of a run with a technical stop")
    r.ev.write_text("", encoding="utf-8")
    r.rec = {"schema": "parlpdfech-gj-validation-lora-run/1", "version": VERSION, "status": STATUS, "actor": ACTOR,
             "gate": "GJ (OPEN)", "check_run": not cfg.real,
             "kind": "validation run of B1-L (criteria 10.3 item 1; addendum B, rule B2 item 3)" if cfg.real else
             "check run on dev documents (not a measurement of a held-out set)",
             "started": now(), "script": {"path": rel(SCRIPT), "sha256": script_sha}, "modules": module_sha(),
             "freeze": {"path": rel(vr.FREEZE), "sha256": sha(vr.FREEZE) if vr.FREEZE.is_file() else None},
             "split": cfg.split, "documents": cfg.ids, "options": opts, "state": "started",
             "state_text": "the script SHA-256 is recorded; no value exists", "earlier_refused_runs": earlier}
    r.save()
    r.rec["script_sha256_recorded"] = r.event("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    r.save()
    return r


# ---------------------------------------------------------------- checks before the first value (chapter 2)

def freeze_checks(cfg: Config, sets: dict) -> tuple[md.Frozen, dict, dict]:
    """The design freeze is unchanged and each frozen file that this run uses is unchanged (GJ.11). The new files
    of B1-L are additions after the design freeze (criteria 10.2 item 2): the record lists them."""
    if not vr.FREEZE.is_file() or sha(vr.FREEZE) != ld.FREEZE_SHA:
        raise RunRefusal(f"{rel(vr.FREEZE)} does not have the SHA-256 {ld.FREEZE_SHA[:12]}... of the protocol")
    fz = read_json(vr.FREEZE)
    if fz.get("dry_run") or fz.get("problems"):
        raise RunRefusal("the design freeze file is a dry run or has problems")
    try:
        frozen = md.load_frozen(vr.DESIGN, vr.FREEZE)
    except md.DesignRefusal as e:
        raise RunRefusal(f"m10_design.load_frozen: {e}") from None
    frozen.freeze["_sha256"] = sha(vr.FREEZE)
    if frozen.synthetic:
        raise RunRefusal("the design is synthetic")
    res: dict = {"file": rel(vr.FREEZE), "sha256": sha(vr.FREEZE), "load_frozen": "accepted"}
    code = fz.get("code") or {}
    used = {rel(vr.SCRIPT), "src/m10_label_schema.yaml"} | {f"src/{m}.py" for m in vr.MODULES}
    changed = sorted(p for p in used if (ROOT / p).is_file() and code.get(p) != sha(ROOT / p))
    if changed:
        raise RunRefusal(f"GJ.11: frozen files that this run uses changed or are not in the freeze file: {changed}")
    loaded = sorted(rel(Path(m.__file__)) for n, m in sys.modules.items()
                    if n.startswith("m10_") and getattr(m, "__file__", None))
    new = {f"src/{m}.py" for m in NEW_MODULES}
    other = [p for p in loaded if p not in new and code.get(p) != sha(ROOT / p)
             and not (not cfg.real and p.endswith("_test.py"))]        # a check script is loaded in a check run only
    if other:
        raise RunRefusal(f"GJ.11: imported modules that are not frozen and not a file of B1-L: {other}")
    res["code_unchanged"] = {"frozen_files_used": len(used), "changed": 0, "imported_m10_modules": loaded}
    res["additions_after_the_design_freeze"] = {p: sha(ROOT / p) for p in sorted(new)}
    res["gj11_inputs"] = vr.gj11_inputs_check(fz)
    if cfg.real:
        try:
            res["m10_calibrate_freeze_check"] = cal.freeze_check("validation", cal.FLOOR_FILE)
        except SystemExit as e:
            raise RunRefusal(f"m10_calibrate.freeze_check: {e}") from None
        import m10_convert as conv  # noqa: PLC0415
        try:
            conv.held_out_check("validation", "stored")
            res["m10_convert_held_out_check"] = "accepted"
        except conv.Stop as e:
            raise RunRefusal(f"m10_convert.held_out_check: {e}") from None
    try:
        res["assert_apply_allowed"] = md.assert_apply_allowed(cfg.ids, frozen, sets)
    except md.DesignRefusal as e:
        raise RunRefusal(f"m10_design.assert_apply_allowed: {e}") from None
    ff = md.frozen_files()
    if ff["different"]:
        raise RunRefusal(f"GJ.4: FROZEN_FILES changed: {ff['different']}")
    res["frozen_files"] = {"files": ff["files"], "different": ff["different"], "source_sha256": ff["source_sha256"]}
    res["template"] = vr.template_check(fz)
    try:
        res["scorer_reproduction"] = ms.check_reproduction()
    except SystemExit as e:
        raise RunRefusal(f"GJ.6: {e}") from None
    res["freeze_made"] = (fz.get("additions") or {}).get("made") or fz.get("made")
    res["lora_trigger_of_the_freeze"] = (fz.get("choices") or {}).get("lora_trigger")
    return frozen, fz, res


def design_lora_check(cfg: Config, frozen: md.Frozen) -> tuple[ld.LoraDesign, dict]:
    try:
        crit = ld.addenda_check()
        des = ld.load_design_lora(cfg.design_lora, frozen, real=cfg.real)
    except ld.LoraRefusal as e:
        raise RunRefusal(f"design of B1-L: {e}") from None
    if cfg.real and cfg.design_lora_sha != des.sha256:
        raise RunRefusal("the SHA-256 of design_lora.json is not the value of --design-lora-sha256 (the value of "
                         "the protocol)")
    code = des.record.get("code") or {}
    changed = [p for p in (rel(ld.SCRIPT), rel(bx.SCRIPT), rel(md.SCRIPT)) if code.get(p) != sha(ROOT / p)]
    if changed:
        raise RunRefusal(f"files changed after the design of B1-L: {changed}")
    ch = des.record["choices"]
    return des, {"criteria": crit, "design_lora_json": {"path": rel(des.dir / "design_lora.json"),
                                                        "sha256": des.sha256},
                 "output_files": des.files, "check_run": des.check_run, "form": des.form, "strength": des.strength,
                 "thresholds": ch["thresholds"], "choice_7_3_item_5": ch["choice_7_3_item_5"]["choice"],
                 "design_finished": des.record.get("finished")}


def logits_check(cfg: Config, sets: dict) -> tuple[dict, dict, dict]:
    """The job folder and the logits files against the run record of each run. No logit is read. Real run: the
    run final only; the files of other documents in its folder (group 7) are counted and never opened. Check
    run: the fold run of each dev document. Returns (job, {doc: (path, run name)}, record)."""
    try:
        job = ld.read_job(cfg.job)
        if cfg.real:
            run_of = {d: ld.FINAL_RUN for d in cfg.ids}
        else:
            folds = read_json(vr.DESIGN / "folds.json")["fold_of_doc"]
            run_of = {d: ld.FOLD_RUNS[int(folds[d]) - 1] for d in cfg.ids}
        want_set = cfg.split
        bad = [d for d in cfg.ids if (job["docs"].get(d) or {}).get("set") != want_set]
        if bad:
            raise RunRefusal(f"{len(bad)} documents are not {want_set} documents of the job folder")
        folders, files = {}, {}
        for name in sorted(set(run_of.values())):
            want = [d for d in cfg.ids if run_of[d] == name]
            f = ld.run_folder(cfg.states_lora, name, want, job, other_is_refusal=False)
            if cfg.real and not (f["script_sha256_equal_job_manifest"] and all(f["job_files_equal"].values())
                                 and f["plan_equal"]):
                raise RunRefusal(f"the run {name} does not have the trainer, the job files or the plan of the job "
                                 "manifest")
            folders[name] = {k: v for k, v in f.items() if k not in ("files", "files_sha256")}
            files.update({d: (p, name) for d, p in f["files"].items()})
    except ld.LoraRefusal as e:
        raise RunRefusal(f"logits of B1-L: {e}") from None
    fc = cfg.job / "fetch_check.json"
    fetch = None
    if fc.is_file():
        x = read_json(fc)
        fetch = {"path": rel(fc), "sha256": sha(fc), "scope": x.get("scope"), "result": x.get("result")}
        if cfg.real and x.get("result") != "PASS":
            raise RunRefusal(f"{rel(fc)}: the fetch check of src/m10_lora_job.py did not pass")
    return job, files, {"job": {rel(cfg.job / n): h for n, h in job["files"].items()}, "runs": folders,
                        "documents_with_logits": len(files),
                        "documents_without_logits": [d for d in cfg.ids if d not in files], "fetch_check": fetch}


def draws_check(n: int) -> np.ndarray:
    """Criteria 6.3: the draws of the task text; they must be the draws of m10_calibrate.bootstrap_draws."""
    draws = np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))
    if (vr.N_BOOT, vr.SEED) != (N_BOOT, SEED) or not np.array_equal(draws, cal.bootstrap_draws(n, N_BOOT, SEED)):
        raise RunRefusal("the bootstrap draws differ from m10_calibrate.bootstrap_draws")
    cnt = np.zeros((N_BOOT, n))
    for i, row in enumerate(draws):
        cnt[i] = np.bincount(row, minlength=n)
    if not np.array_equal(cnt, vr.draw_counts(n)):
        raise RunRefusal("the bootstrap counts differ from m10_validation_run.draw_counts")
    return cnt


def head_run_values(cfg: Config) -> dict | None:
    """Real run: the two entry decisions of the validation run of the heads (only these 2 keys are read)."""
    if not cfg.real or not HEAD_MEASURES.is_file():
        return None
    e = read_json(HEAD_MEASURES).get("entry") or {}
    out = {"path": rel(HEAD_MEASURES), "sha256": sha(HEAD_MEASURES), "d1_enters": e.get("d1_enters"),
           "b1_b2_enter": e.get("b1_b2_enter")}
    if out["d1_enters"] is not None and bool(out["d1_enters"]) != cfg.entry_d1:
        raise RunRefusal("--entry-d1 differs from the entry decision GJ.15 of daten/gj/validation/measures.json")
    return out


# ---------------------------------------------------------------- phase A: decisions

def phase_decisions(cfg: Config, r: vr.Record, frozen: md.Frozen, des: ld.LoraDesign, job: dict, files: dict,
                    docs_in: dict, floor: dict, r2: dict, r2_cals: dict, sets: dict) -> dict:
    import m10_writer as w  # noqa: PLC0415
    name_y, name_n = cfg.variants()
    dev_ids = {str(d) for d in sets["dev"]}
    try:
        gate = ld.decide_gate(cfg.ids, sets, r.path if cfg.real else None)
    except ld.LoraRefusal as e:
        raise RunRefusal(f"gate of the decisions: {e}") from None
    cal_v = {name: ld.lora_calibration_file(frozen, des, cfg.entry_d1, e)["calibrations"] | r2_cals
             for name, e in ((name_y, True), (name_n, False))}
    fallback = dict(r.rec.get("fallback_documents") or {})
    problems, counts, first = [], Counter(), True
    for d in cfg.ids:
        rule = docs_in[d]["rules"]
        doc = md.load_doc(d)
        out_files = {name: variant_dir(cfg, name) / f"{d}.json" for name in (name_y, name_n)}
        if all(r.have(p) for p in out_files.values()):
            counts["documents_kept"] += 1
            continue
        if first:
            r.rec["first_value"] = r.rec.get("first_value") or r.event("first_value", what="first logits file")
            r.save()
            first = False
        why, decs = None, {}
        if d not in files:
            why = "no logits file"
        else:
            p, run = files[d]
            try:
                S = ld.read_logits(p, d, job["docs"][d], run, [b["block"] for b in doc["blocks"]])
                info = {"file": rel(p), "sha256": sha(p), "run": run}
                for name, e in ((name_y, True), (name_n, False)):
                    decs[name] = ld.lora_decisions(d, gate, frozen, des, S, cfg.head_states, cfg.entry_d1, e,
                                                   r2.get(d), dev_ids, info)
                if any(v is None for v in decs.values()):
                    why = "no states file"
            except ld.LoraRefusal as e:
                raise RunRefusal(f"decisions of B1-L: {e}") from None
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
        raise RunRefusal(f"{len(problems)} decisions checks failed: the problems are in {rel(r.path)} (key "
                         "decision_check_stops)")
    for name, e in ((name_y, True), (name_n, False)):
        c = cal_v[name] | (floor["records_without_threshold"] if fallback else {})
        p = variant_dir(cfg, name) / "calibrations.json"
        r.output(p, write_json(p, {"calibrations": c, "variant": name,
                                   "entry": {"d1": cfg.entry_d1, "b1_l": e}, "status": STATUS}))
    r.rec.setdefault("phase_decisions", []).append({
        "documents": len(cfg.ids), **dict(counts), "variants": [name_y, name_n],
        "decision_checks": "each file of each document passed",
        "documents_with_floor_fallback": len(fallback),
        "fallback_reasons": dict(Counter(v.split(" (")[0] for v in fallback.values())), "finished": now()})
    r.save()
    return {"fallback": fallback}


# ---------------------------------------------------------------- phase B: measures

def score_sets(cfg: Config) -> dict:
    """L9 and the 6 block options through src/m10_score.py (criteria 6.1 items 6 to 9), as score_sets of the
    frozen runner: the rules (plain rule output of daten/gj/rules) and the two variants of B1-L."""
    ids = cfg.ids
    name_y, name_n = cfg.variants()
    bodies = ms.parliaments(ids)
    if any(ms.split_of(d, bodies.get(d), allow_group7=False) != cfg.split for d in ids):
        raise RunRefusal(f"m10_score.split_of gives another split than {cfg.split}")
    table = {d: ms.doc_entry(d) for d in ids}
    atom_ref, block_ref, d1_ref, src = {}, {}, {}, Counter()
    for d in ids:
        atom_ref[d], s, _ = ms.atom_reference(table[d], pilots=True)
        src[s] += 1
        block_ref[d], d1, _ = ms.block_reference(table[d], "labels", vr.LABELS, atom_ref[d])
        if d1:
            d1_ref[d] = d1
    out = {"reference_sources": dict(src)}
    for name, kind, folder in (("rules_nos4", "rules", vr.RULES),
                               ("b1l_entered", "decisions", variant_dir(cfg, name_y)),
                               ("b1l_not_entered", "decisions", variant_dir(cfg, name_n))):
        aset, shas = ms.load_answer_set(kind, folder, ids, table)
        vals = ms.score_set(ids, aset, table, atom_ref, block_ref, d1_ref)
        out[name] = vr.l9_compact(vals) | {"answer_files_sha256_canonical": ms.canonical_sha(shas)}
    return out


def phase_measures(cfg: Config, frozen: md.Frozen, des: ld.LoraDesign, docs_in: dict, floor: dict, cnt: np.ndarray,
                   fallback: dict, head: dict | None) -> dict:
    ids, n = cfg.ids, len(cfg.ids)
    name_y, name_n = cfg.variants()
    var = {name: {d: read_json(variant_dir(cfg, name) / f"{d}.json") for d in ids} for name in (name_y, name_n)}
    labels = {d: docs_in[d]["labels"] for d in ids}
    rules = {d: docs_in[d]["rules"] for d in ids}
    meta = {}
    for d in ids:
        doc = md.load_doc(d)
        meta[d] = {"parliament": doc.get("parliament"), "language": doc.get("language") or "unknown"}
    # ---- GJ.17 (criteria 7.3 item 3 = criteria 7.2 with B1-L): km method, kr rule option (decision M7)
    km, kr, kv, nn = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    cert_same, cert_plain = True, 0
    for i, d in enumerate(ids):
        yv, nv = var[name_y][d], var[name_n][d]
        rb = [b["option"] for b in labels[d]["blocks"]]
        if [b["block"] for b in rules[d]["blocks"]] != [b["block"] for b in yv["blocks"]]:
            raise RunRefusal(f"{d}: the blocks of the rule file and of a decisions file differ")
        ro = [b["option"] for b in rules[d]["blocks"]]
        flags = [bool(b.get("certain_pair")) for b in yv["blocks"]]
        cert_same &= [bool(b.get("certain_pair")) for b in nv["blocks"]] == flags
        cert_plain += sum(f != ((b["tier"], b["option"]) in frozen.certain) for f, b in zip(flags, rules[d]["blocks"]))
        for j, b in enumerate(yv["blocks"]):
            if flags[j]:
                continue
            nn[i] += 1
            km[i] += b["option"] == rb[j]
            kr[i] += ro[j] == rb[j]
            kv[i] += nv["blocks"][j]["option"] == rb[j]
    if not cert_same:
        raise RunRefusal("the set of certain blocks differs between the variants (criteria 6.1 item 5)")
    sc = score_sets(cfg)
    am, ar = sc["b1l_entered"]["all_documents"], sc["rules_nos4"]["all_documents"]
    dec = vr.entry_blocks(cnt, km, kr, nn, am["exact"], ar["exact"], am["switch_sr"]["exact"],
                          ar["switch_sr"]["exact"])
    made = dt.datetime.now().astimezone()
    before_cut = made < CUT
    enters = bool(dec["enters"] and (before_cut or not cfg.real))
    all_ref = [b["option"] for d in ids for b in labels[d]["blocks"]]
    opt = lambda name: [b["option"] for d in ids for b in var[name][d]["blocks"]]  # noqa: E731
    ch = des.record["choices"]
    gj17 = {"criterion": "criteria 7.3 items 3 and 4: the 3 conditions of criteria 7.2 with B1-L and its B2 form in "
                         "place of B1 and B2 (decision M7 for the baseline); addenda B and C",
            "documents": n, "method": f"written path of B1-L with the B2 form {des.form} on the non-certain blocks "
                                      f"(variant {name_y})",
            "baseline": "the rule option of each block as src/m10_rules.py gives it (criteria 6.1 item 10); the nos4 "
                        "answers of daten/gj/rules through src/m10_score.py for the 2 count conditions",
            "blocks": len(all_ref), "certain_blocks": int(len(all_ref) - nn.sum()), "non_certain_blocks": int(nn.sum()),
            "certain_set_equal_in_each_variant": cert_same, **dec,
            "switch_documents": ar["switch_sr"]["documents"],
            "cut": {"rule": "criteria 7.3 item 4", "time": CUT.isoformat(), "value_made": made.isoformat(
                timespec="seconds"), "before_the_cut": before_cut},
            "enters_by_the_3_conditions": bool(dec["enters"]), "enters": enters,
            "status": "B1-L enters" if enters else "B1-L does not enter",
            "b2_form": des.form, "strength": des.strength,
            "documents_with_floor_fallback": len(fallback),
            "information": {
                "macro_f1_6_all_blocks_method": r6(vr.macro_f1(all_ref, opt(name_y), OPTIONS)),
                "macro_f1_6_all_blocks_rules": r6(vr.macro_f1(
                    all_ref, [b["option"] for d in ids for b in rules[d]["blocks"]], OPTIONS)),
                "accuracy_all_blocks_method": r6(np.mean([a == b for a, b in zip(opt(name_y), all_ref)])),
                "accuracy_all_blocks_rules": r6(np.mean([b["option"] == a for a, b in zip(
                    all_ref, [b for d in ids for b in rules[d]["blocks"]])])),
                "accuracy_gain_non_certain_against_the_rule_view": vr.paired(cnt, km, kv, nn) | {"decides": False},
                "blocks_with_another_certain_flag_for_the_plain_rule_output": int(cert_plain)}}
    both = None if head is None or head.get("b1_b2_enter") is None else bool(head["b1_b2_enter"]) and enters
    choice = {"rule": "criteria 7.3 item 5 (dev out-of-fold values only; design_lora.json)",
              "dev_choice_if_both_enter": ch["choice_7_3_item_5"]["choice"],
              "dev_accuracy_b1_l": ch["choice_7_3_item_5"]["accuracy_b1_l"],
              "dev_accuracy_b1": ch["choice_7_3_item_5"]["accuracy_b1"],
              "b1_and_b2_entered_in_the_run_of_the_heads": None if head is None else head.get("b1_b2_enter"),
              "both_enter": both,
              "block_step": None if head is None or head.get("b1_b2_enter") is None else (
                  (ch["choice_7_3_item_5"]["choice"] if both else "B1-L") if enters else
                  ("B1 and B2" if head["b1_b2_enter"] else "rule option with a verifier probability"))}
    # ---- GJ.13 on the written block labels of the variant in which B1-L decides
    pg = floor["p_gap_without_label"]
    u = vr.units(ids, var[name_y], labels, meta, pg)
    b = u["blocks"]
    ece = cal.ece_equal_width(b["pw"], b["ok"])
    bs = vr.ece_bootstrap(cnt, b["pw"], b["ok"], b["g"], n)
    m_all = cal.measures(b["Q"], b["y"], None, False, b["pw"], b["ok"])
    met13 = ece <= GJ13_ECE and bs["high_95"] <= GJ13_HIGH
    gj13 = {"criterion": "GJ.13: ECE <= 0.05 and the 95 % bound of the document bootstrap <= 0.08", "variant": name_y,
            "blocks": int(len(b["y"])), "documents": n, "accuracy_written": r6(b["ok"].mean()), "ece": ece,
            "ece_bootstrap": bs, "ece_equal_mass": r6(cal.ece_equal_mass(b["pw"], b["ok"])),
            "brier_6_options": m_all["brier"], "nll_6_options": m_all["nll"], "classwise_ece": m_all["classwise_ece"],
            "reliability_written_option": cal.reliability_table(b["pw"], b["ok"]),
            "status": "MET" if met13 else "NOT MET"}
    un = vr.units(ids, var[name_n], labels, meta, pg)
    gj21 = {"variant": name_y, "variant_measures": vr.kind_measures(u),
            "variant_b1l_not_entered_information": vr.kind_measures(un),
            "l9": {k: sc[k] for k in ("rules_nos4", "b1l_entered", "b1l_not_entered")},
            "reference_sources_of_l9": sc["reference_sources"],
            "note": "the D1 label of each variant is the D1 label of the frozen design (B1-L does not change D1)"}
    variants = {}
    for name, uv in ((name_y, u), (name_n, un)):
        cv = read_json(variant_dir(cfg, name) / "calibrations.json")["calibrations"]
        variants[name] = {"block_accuracy": r6(uv["blocks"]["ok"].mean()),
                          "block_written_ece": r6(cal.ece_equal_width(uv["blocks"]["pw"], uv["blocks"]["ok"])),
                          "switch_labels": int(len(uv["switch"]["pw"])),
                          "value_status": vr.value_status(var[name], cv)}
    counts_check = None
    if cfg.real:
        counts_check = {"documents": n == EXPECTED["documents"],
                        "switch_documents": ar["switch_sr"]["documents"] == EXPECTED["switch_documents"]}
    return {"schema": "parlpdfech-gj-validation-lora-measures/1", "status": STATUS, "made": now(), "documents": n,
            "split": cfg.split, "counts_against_criteria_chapter_3": counts_check,
            "documents_with_floor_fallback": sorted(fallback, key=int),
            "entry": {"GJ.17": gj17, "variant": name_y, "d1_enters_by_option": cfg.entry_d1, "b1_l_enters": enters,
                      "choice_7_3_item_5": choice, "run_of_the_heads": head},
            "GJ.13": gj13, "GJ.21": gj21, "variants_information": variants,
            "calibration_ids_of_the_variant_blocks": sorted(set(b["cal"]))}


# ---------------------------------------------------------------- result.md (English STE)

_f = vr._f


def result_markdown(res: dict) -> str:
    m, run = res["measures"], res["run"]
    e = m["entry"]
    g17, g13, g21 = e["GJ.17"], m["GJ.13"], m["GJ.21"]
    g = g17["accuracy_gain_non_certain"]
    L = []
    add = L.append
    kind = "the one validation run of B1-L" if run["real"] else "a check run on dev documents (not a held-out run)"
    add("# Gate GJ: result of the validation run of B1-L")
    add("")
    add(f"Run of {run['started']} to {run['finished']} (time from the clock). This file is the result of {kind}. "
        f"Script `src/m10_lora_validation.py`, SHA-256 `{run['script_sha256']}`.")
    add("")
    add("Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: workflow sub-agent "
        "(Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    add("## 1 Order of the records and checks")
    add("")
    add(f"1. The script wrote its SHA-256 into `run.json` at {run['script_sha256_recorded']}.")
    add(f"2. The checks passed at {run['checks_passed']}. The first value came at {run['first_value']}.")
    add(f"3. Freeze file: `{run['freeze']['path']}`, SHA-256 `{run['freeze']['sha256']}`.")
    dl = res["checks"]["design_lora"]
    add(f"4. Design of B1-L: `{dl['design_lora_json']['path']}`, SHA-256 `{dl['design_lora_json']['sha256']}`. B2 "
        f"form: `{g17['b2_form']}`. Strength: {_f(g17['strength'], 0)}.")
    add(f"5. Documents: {m['documents']} of the set `{m['split']}`. Documents with the floor labels (no states, no "
        f"logits or no path of the form): {len(m['documents_with_floor_fallback'])}.")
    runs = res["checks"]["logits"]["runs"]
    add(f"6. Logits: {res['checks']['logits']['documents_with_logits']} files of {len(runs)} runs "
        f"({', '.join(f'`{x}`' for x in runs)}), each with the SHA-256 of the run record of its run. Files of other "
        f"documents in these folders that the run did not open: "
        f"{sum(f['other_files_not_opened'] for f in runs.values())}.")
    add("7. Checks before the first value: guard and `m00_pruefe_testset.py` (0 test documents), freeze file, frozen "
        "code (0 changes), FROZEN_FILES (0 changes), template items (equal), scorer reproduction (MET), GPU-1 states "
        "(equal), addenda B and C (equal), logits files (SHA-256 of the run record).")
    add("8. This is the second validation run of the block step (criteria 7.3, item 6; addendum B, rule B2). The run "
        "of the heads came first.")
    if m.get("counts_against_criteria_chapter_3"):
        cc = m["counts_against_criteria_chapter_3"]
        add(f"9. Counts against criteria chapter 3: documents {_f(cc['documents'])}, switch documents "
            f"{_f(cc['switch_documents'])}.")
    add("")
    add("| Run record of the logits | SHA-256 |")
    add("|---|---|")
    for f in runs.values():
        add(f"| `{f['run_json']['path']}` | `{f['run_json']['sha256']}` |")
    add("")
    add("## 2 Entry decision GJ.17 (criteria 7.3)")
    add("")
    add("| Value | GJ.17 B1-L |")
    add("|---|---|")
    add(f"| Units | {g['units']} non-certain blocks |")
    add(f"| Accuracy of the method | {_f(g['method'])} |")
    add(f"| Accuracy of the baseline | {_f(g['baseline'])} |")
    add(f"| Gain | {_f(g['gain'])} |")
    add(f"| 5 % quantile of the gain | {_f(g['low_5'])} |")
    add(f"| 95 % quantile of the gain | {_f(g['high_95'])} |")
    add(f"| Condition 1: 5 % quantile more than 0 | {_f(g17['condition_1_lower_bound_above_0'])} |")
    add(f"| Condition 2 | L9 exact: method {g17['l9_exact_method']}, rules {g17['l9_exact_rules']}: "
        f"{_f(g17['condition_2_l9'])} |")
    add(f"| Condition 3 | switch documents {g17['switch_documents']}: method {g17['switch_exact_method']}, rules "
        f"{g17['switch_exact_rules']}: {_f(g17['condition_3_switch'])} |")
    add(f"| Value before the cut of 14.10.2026, 08:00 | {_f(g17['cut']['before_the_cut'])} |")
    add(f"| Enters | {_f(g17['enters'])} |")
    add("")
    add(f"1. GJ.17: {g17['status']}. Certain blocks: {g17['certain_blocks']}. Non-certain blocks: "
        f"{g17['non_certain_blocks']}.")
    add("2. The baseline is the rule option of each block from `src/m10_rules.py` (criteria 6.1, item 10). The L9 "
        "counts of the rules use the same rule output.")
    i = g17["information"]
    add(f"3. Information: accuracy on all blocks {_f(i['accuracy_all_blocks_method'])} against "
        f"{_f(i['accuracy_all_blocks_rules'])} for the rules. Macro F1 of the 6 options: "
        f"{_f(i['macro_f1_6_all_blocks_method'])} against {_f(i['macro_f1_6_all_blocks_rules'])}.")
    c = e["choice_7_3_item_5"]
    add(f"4. Choice of criteria 7.3, item 5 (`dev` values only): {c['dev_choice_if_both_enter']} if both enter. "
        f"`dev` accuracy on the non-certain blocks: B1-L {_f(c['dev_accuracy_b1_l'])}, B1 {_f(c['dev_accuracy_b1'])}.")
    add("5. The bootstrap uses 2,000 resamples of the documents with the seed 20261013 (criteria 6.3).")
    if c.get("block_step") is not None:
        add(f"6. B1 and B2 entered in the run of the heads: {_f(c['b1_and_b2_entered_in_the_run_of_the_heads'])}. "
            f"Thus the block step is: {c['block_step']}.")
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
    add(f"2. The variant `{g13['variant']}` is the variant in which B1-L decides the non-certain blocks.")
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
    for key, text in (("rules_nos4", "rules"), ("b1l_entered", "B1-L decides"), ("b1l_not_entered", "rules with the "
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
    add("## 5 Records (GJ.12, part validation of B1-L)")
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
    add("1. The reference is an AI reference without a human acceptance.")
    add("2. The set is small: 44 documents and 10 switch documents. The intervals are wide.")
    add("3. The rules saw 42 of the 44 validation documents. This favours the rules and each form with rule gaps.")
    add("4. The B2 forms of addendum C were designed after the aggregate result of the run of the heads was known.")
    add("5. A value of this file is not a value of gate GJ before the second calculation (GJ.19).")
    add("6. Jonathan did not accept the criteria, addendum B or addendum C. All values have the status EXCEPTION.")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- run

def run(cfg: Config) -> dict:
    t0 = time.perf_counter()
    if cfg.real and not cfg.records:
        raise RunRefusal("the validation run of B1-L always writes the records (GJ.12): --no-records is only for a "
                         "check run; the run writes no file")
    if cfg.real and not (cfg.design_lora / "design_lora.json").is_file():
        raise RunRefusal(f"no design of B1-L in {rel(cfg.design_lora)}: the run writes no file")
    r = start_record(cfg)
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
    frozen, fz, fc = freeze_checks(cfg, sets)
    checks["freeze"] = fc
    checks["states"] = vr.states_check(vcfg)
    des, checks["design_lora"] = design_lora_check(cfg, frozen)
    job, files, checks["logits"] = logits_check(cfg, sets)
    if cfg.real and not cfg.no_r2 and (cfg.r2 is None or cfg.r2_cal is None):
        raise RunRefusal("the real run needs --r2 and --r2-calibrations (the files of the run of the heads), or the "
                         "option --no-r2")
    r2 = vr.load_r2(cfg.r2)
    r2_cals = vr.load_calibration_records(cfg.r2_cal)
    if cfg.r2 is not None:
        without = [d for d in cfg.ids if d not in r2]
        missing = sorted({v["calibration"] for v in r2.values()} - set(r2_cals))
        if (cfg.real and without) or missing:
            raise RunRefusal(f"R2: {len(without)} documents without a value, calibration ids without a record: "
                             f"{missing}")
    checks["r2"] = {"documents_with_r2": sum(1 for d in cfg.ids if d in r2), "options": r.rec["options"]["r2"]}
    floor = vr.floor_inputs()
    docs_in = cal.load_documents(cfg.ids, with_labels=True)
    cnt = draws_check(len(cfg.ids))
    checks["bootstrap"] = {"resamples": N_BOOT, "seed": SEED, "equal_to_m10_calibrate": True}
    head = head_run_values(cfg)
    checks["run_of_the_heads"] = head
    if r.rec.get("checks"):
        r.rec.setdefault("checks_of_the_continuations", []).append(checks)
    else:
        r.rec["checks"] = checks
        r.rec["checks_passed"] = r.event("checks_passed")
    r.save()
    say(f"checks passed: freeze {fc['sha256'][:12]}..., design of B1-L {des.sha256[:12]}... (form {des.form}), "
        f"logits files {checks['logits']['documents_with_logits']} of {len(cfg.ids)} with the SHA-256 of run.json")
    # ---- phase A
    pa = phase_decisions(cfg, r, frozen, des, job, files, docs_in, floor, r2, r2_cals, sets)
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
    g17, g13 = meas["entry"]["GJ.17"], meas["GJ.13"]
    say(f"GJ.17: {g17['status']}; GJ.13 {g13['status']}")
    # ---- phase C
    g12 = None
    if cfg.records:
        g12 = vr.phase_records(vcfg, r, meas)
        say(f"GJ.12 (part {cfg.split}, B1-L): {g12['status']}, valid documents {g12['documents_valid']} of "
            f"{g12['documents']}, failed {g12['failed_documents']}, with recorded I95 gaps "
            f"{g12['documents_with_recorded_gaps']}")
    meas = vr.gj21_gap_count(vcfg, r, meas, g12)
    # ---- end checks
    ff = md.frozen_files()
    if module_sha() != r.rec["modules"]:
        raise RunRefusal("a script changed during the run")
    if ff["different"]:
        raise RunRefusal(f"GJ.4: FROZEN_FILES changed during the run: {ff['different']}")
    if sha(vr.FREEZE) != ld.FREEZE_SHA or sha(des.dir / "design_lora.json") != des.sha256:
        raise RunRefusal("the freeze file or design_lora.json changed during the run")
    r.rec["finished"] = r.event("finished")
    run_info = {"real": cfg.real, "started": r.rec["started"], "finished": r.rec["finished"],
                "script_sha256": r.rec["script"]["sha256"], "script_sha256_recorded": r.rec["script_sha256_recorded"],
                "checks_passed": r.rec["checks_passed"], "first_value": r.rec.get("first_value"),
                "freeze": r.rec["freeze"], "continued": r.rec.get("continued") or [],
                "seconds": round(time.perf_counter() - t0, 1)}
    res = {"schema": "parlpdfech-gj-validation-lora-result/1", "status": STATUS, "run": run_info, "checks": checks,
           "measures": meas, "GJ.12": g12,
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
    g = g17["accuracy_gain_non_certain"]
    return {"run": rel(r.path), "result_json": {"path": rel(rp), "sha256": sha(rp)},
            "result_md": {"path": rel(mdp), "sha256": sha(mdp)},
            "GJ.17": {"status": g17["status"], "enters": g17["enters"], "units": g["units"], "method": r6(g["method"]),
                      "baseline": r6(g["baseline"]), "gain": r6(g["gain"]), "low_5": r6(g["low_5"]),
                      "l9_method": g17["l9_exact_method"], "l9_rules": g17["l9_exact_rules"],
                      "switch_method": g17["switch_exact_method"], "switch_rules": g17["switch_exact_rules"],
                      "conditions": [g17["condition_1_lower_bound_above_0"], g17["condition_2_l9"],
                                     g17["condition_3_switch"]], "before_the_cut": g17["cut"]["before_the_cut"]},
            "b2_form": g17["b2_form"], "variant": meas["entry"]["variant"],
            "GJ.13": {"status": g13["status"], "accuracy_written": g13["accuracy_written"], "ece": r6(g13["ece"]),
                      "high_95": r6(g13["ece_bootstrap"]["high_95"])},
            "GJ.12": None if g12 is None else {k: g12[k] for k in ("status", "documents", "documents_valid",
                                                                    "documents_with_recorded_gaps")},
            "documents_with_floor_fallback": len(meas["documents_with_floor_fallback"]),
            "choice_7_3_item_5": meas["entry"]["choice_7_3_item_5"], "seconds": run_info["seconds"]}


# ---------------------------------------------------------------- command line

def config_of(args) -> Config:
    yes = {"yes": True, "no": False}
    r2 = Path(args.r2).resolve() if args.r2 else None
    r2c = Path(args.r2_calibrations).resolve() if args.r2_calibrations else None
    if not args.check_run:
        if args.docs or args.work or args.design_lora or args.states_lora or args.job or args.no_records:
            raise RunRefusal("--docs, --work, --design-lora, --states-lora, --job and --no-records are only for "
                             "--check-run")
        if not args.design_lora_sha256:
            raise RunRefusal("the real run needs --design-lora-sha256 (the SHA-256 of design_lora.json of the "
                             "protocol)")
        sets = md.load_sets()
        return Config(real=True, ids=vr.by_id(sets["validation"]), split="validation", out=OUT,
                      decisions_out=DECISIONS_OUT, design_lora=ld.OUT, states_lora=ld.STATES, job=ld.JOB,
                      entry_d1=yes[args.entry_d1], design_lora_sha=args.design_lora_sha256, r2=r2, r2_cal=r2c,
                      no_r2=args.no_r2, continue_missing=args.continue_missing, records=True)
    if not (args.docs and args.work and args.design_lora and args.states_lora):
        raise RunRefusal("--check-run needs --docs, --work, --design-lora and --states-lora")
    work = Path(args.work).resolve()
    if work.is_relative_to(GJ.resolve()) or Path(args.states_lora).resolve() == ld.STATES.resolve():
        raise RunRefusal("the check run never writes to daten/gj and never reads daten/gj/states/lora_b1")
    guard.check_path(work)
    ids = vr.by_id(i for a in args.docs for i in guard.read_items(a))
    return Config(real=False, ids=ids, split="dev", out=work / "validation_lora",
                  decisions_out=work / "decisions_validation_lora", design_lora=Path(args.design_lora).resolve(),
                  states_lora=Path(args.states_lora).resolve(), job=Path(args.job).resolve() if args.job else ld.JOB,
                  entry_d1=yes[args.entry_d1], r2=r2, r2_cal=r2c, no_r2=True,
                  continue_missing=args.continue_missing, records=not args.no_records)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--entry-d1", choices=("yes", "no"), required=True,
                    help="the entry decision GJ.15 of the validation run of the heads (D1 label of the records)")
    ap.add_argument("--design-lora-sha256", help="real run: the SHA-256 of design_lora.json of the protocol")
    ap.add_argument("--r2")
    ap.add_argument("--r2-calibrations")
    ap.add_argument("--no-r2", action="store_true", help="real run without R2 labels in the records")
    ap.add_argument("--continue-missing", action="store_true")
    ap.add_argument("--check-run", action="store_true")
    ap.add_argument("--docs", nargs="*")
    ap.add_argument("--work")
    ap.add_argument("--design-lora")
    ap.add_argument("--states-lora")
    ap.add_argument("--job")
    ap.add_argument("--no-records", action="store_true", help="check run only: no record phase (no GJ.12)")
    args = ap.parse_args()
    try:
        summary = run(config_of(args))
    except RunRefusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

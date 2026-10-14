"""Gate GJ (status EXCEPTION), step B1-L (criteria chapters 5, 7.3, 8.3, 8.6 and 8.8; addenda B and C): the dev
design of B1-L from the out-of-fold logits of the 5 fold runs, and the decisions of B1-L for one document.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream D2,
for the main agent. No human checked this file. This file changes no existing file. It imports the frozen
functions of src/m10_design.py and the B2 forms of src/m10_b2x.py. Status of all outputs: EXCEPTION (process rule
10), NOT RELEASED. This file is an addition after the design freeze (criteria chapter 10.2 item 2; addendum B).

0 Order of the records (GJ.2; addendum B, rule B1 items 4 and 5; addendum C, rule C3 item 12)
  The command run writes the SHA-256 of this file into <out>/design_lora.json and into the event log
  <out>/design_lora.events.jsonl before it reads the first logit. Each rule of the design is a constant or a
  function of this file, of src/m10_b2x.py or of src/m10_design.py: the temperature fit, the 5 B2 forms, the
  strength rule, the selection rule of addendum C, the B2 temperature, the verifier map, the threshold a and the
  choice of criteria 7.3 item 5. The record names the SHA-256 of each of these files. The addenda B and C must have
  the SHA-256 values of the constants ADDENDA. src/m10_b2x.py must have the SHA-256 of addendum C, chapter 9.

1 Inputs (explicit paths)
  job      daten/gj/jobs/lora_b1/: docs.jsonl (doc_id, set, fold, prefix_sha256, suffixes with suffix_id and
           kind), plan.json and manifest.json (src/m10_lora_job.py). Only the keys named here are used.
  logits   daten/gj/states/lora_b1/<run>/logits/<doc_id>.npz and <run>/run.json (src/m10_lora_blocks.py):
           suffix_ids (the b1 suffix ids = the block ids of the document in reading order), logits float32
           [n, 6] in the class order submitted, reasoning, response, recommendation, title, none, prefix_sha256,
           n_prefix_tokens, run and script_sha256. The SHA-256 of each file must be the value of run.json.
  frozen   daten/gj/design/ (not changed): folds.json, tier_table.json, b2_hmm.json, verifiers.json,
           calibration_records.json, design.json, and the stored out-of-fold D1 posteriors oof/d1_oof.npz.
  labels, rules, sets: as src/m10_design.py (dev documents only).

2 Guards of the command run (process rule 6, GJ.10, criteria chapter 3)
  Each document of the design is in the key dev of daten/gj/sets.json, and src/m10_guard.py allows it with the
  split dev only (m10_design.assert_fit_ids). This check comes before a file of a document is read. The command
  reads only the folders of the runs fold1 to fold5. Each logits file must be the file of a dev document of the
  held-out fold of its run: the file name, the key run of the file and the fold of the job and of the frozen
  folds must agree. A file of another document (validation, group 7, another fold) refuses the command before a
  logit is read. The command never opens the folder of the run final. Each dev document needs a logits file.
  Each run record must be finished and must name the trainer, the job files and the plan of the job manifest.
  If fetch_check.json of src/m10_lora_job.py exists, its result must be PASS.

3 Design (all values are dev out-of-fold values)
  3.1 B1-L temperature (criteria 8.3 item 1): one T on the pooled out-of-fold logits of the 5 fold runs,
      m10_design.fit_temperature. Posterior of a block: softmax(logits / T).
  3.2 B2 forms (addendum C, rules C1 and C2): m10_b2x.forms_table with the fold rule. The HMM of a document is
      fitted on the reference sequences of the other folds. The strength of switch_soft comes from the other
      folds. A document with the S1 rule id R1 gets the rule variant of the stored out-of-fold D1 posterior.
  3.3 B2 form (addendum C, rule C3): m10_b2x.select_form on the rows of 3.2.
  3.4 B2 temperature (criteria 8.3 item 2; addendum C, rule C4 item 2): one T2 on the out-of-fold block marginals
      of the selected form, m10_design.fit_temperature on ln q and m10_design.temper.
  3.5 Verifier map of B1-L (criteria 8.4 item 5): Platt map of the B2 marginal after T2 of the rule option, fit
      set: the non-certain blocks of dev_out_of_design (m10_design.fit_platt). It is used only in the variant
      in which the rule option decides and B1-L gives the probability.
  3.6 Threshold a (criteria 8.6, P17): m10_design.written_values and m10_design.p17 on the written probabilities,
      for the label kinds block_slot and author_switch and for both variants. The kind document_text_parts
      keeps the thresholds of the frozen design (B1-L does not change D1).
  3.7 Choice of criteria 7.3 item 5 (used only if B1-L and B1 both enter): the 6-option accuracy on the
      non-certain dev blocks of B1-L (selected form, written path) against the stored value of B1 and B2 of
      daten/gj/design/design.json. B1-L wins only if its accuracy is more than 0.005 higher. Else B1.
  3.8 Final values for a document of the final run: T, the selected form, T2, the verifier map, the HMM of the
      frozen design (daten/gj/design/b2_hmm.json: all dev documents), and for switch_soft the strength value of
      all dev out-of-fold results (addendum C, rule C2 item 7).

4 Outputs of the command run (<out>, default daten/gj/design_lora/)
  design_lora.json           run record and choices: script SHA-256 before the first value, input SHA-256 values,
                             choices, measures (information), SHA-256 of each other output
  design_lora.events.jsonl   clock time of each event
  design_lora_dev.md         dev out-of-fold values beside the rule output and the stored values of the B1 heads
  calibration_records.json   the form of daten/gj/design/calibration_records.json (keys records, kind_of,
                             thresholds, variant_keys), for m10_design.calibration_file and src/m10_writer.py.
                             The variant keys b12_entered and b12_not_entered mean here: B1-L and its B2 form
                             entered or not.
  oof/b1l_oof.npz            all out-of-fold values (for the recalculation of GJ.19)
  The command refuses an output folder that holds design_lora.json.

5 Decisions of B1-L (function lora_decisions; command decide)
  Interface 7 (mode cascade) for one document from one logits file. The D1 label, the rule view, the certain
  blocks and the form of the file come from m10_design.cascade_decisions (frozen design and GPU-1 states). The
  block labels and the switch boundaries come from B1-L: softmax(logits / T), the selected form with the frozen
  HMM (m10_b2x.b2x_document), T2. A certain block keeps the rule option with the Jeffreys mean. If B1-L decides,
  a non-certain block gets the written path with the B2 marginals after T2 (source code). Else it gets the rule
  option with the verifier probability of B1-L (source rule). Boundaries: the switch gaps of the written path
  with the switch probability of the gap. Each probability is clipped to [0.005, 0.995] with 4 decimals.
  A document without a states file or without a logits file gives None (the caller uses the floor converter F1).
  Gate (function decide_gate): a test document is refused by src/m10_guard.py. A group-7 document is always
  refused (no method freeze exists). A validation document is refused unless the caller gives the run record of
  src/m10_lora_validation.py: state started, the SHA-256 of that script now, and the document in its list.
  The command decide has no option for that record. Thus it makes decisions for dev documents only. For a dev
  document it reads the logits of the fold run of the document: the LoRA model did not see the document, but T,
  T2 and the HMM saw it (in_sample true).

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync python src/m10_lora_design.py run
  uv run --offline --frozen --no-sync python src/m10_lora_design.py decide --set ID|LIST [ID|LIST ...] --out DIR
      [--entry-d1 yes|no] [--entry-b1l yes|no]
  Check script on dev stand-in logits: uv run --offline --frozen --no-sync python src/m10_lora_design_test.py
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import re
import sys
import time
import types
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard, process rule 6)
import m10_design as md  # noqa: E402  (frozen design functions; not changed)
import m10_b2x as bx  # noqa: E402  (B2 forms and the selection rule of addendum C)

VERSION = "m10-lora-design-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = md.GJ
OUT = GJ / "design_lora"
STATES = GJ / "states/lora_b1"
JOB = GJ / "jobs/lora_b1"
HEAD_STATES = GJ / "states/gpu1_labelled"
HEAD_TABLE = OUT / "b2_forms_dev_heads.json"            # stream D1: the 5 forms with the posteriors of the B1 head
VALIDATION_SCRIPT = ROOT / "src/m10_lora_validation.py"
STATUS = md.STATUS
ACTOR = "workflow sub-agent (Claude Opus 5.5), stream D2, for the main agent"
FOLD_RUNS = tuple(f"fold{k}" for k in range(1, md.N_FOLDS + 1))
FINAL_RUN = "final"
CLASSES = md.OPTIONS                                     # class order of the logits
NPZ_KEYS = ("suffix_ids", "logits", "prefix_sha256", "n_prefix_tokens", "run", "script_sha256")
RUN_DONE = "done"
TIE_B1 = 0.005                                           # criteria 7.3 item 5: "0.005 or less gives B1"
FREEZE_SHA = "add6fdad843cf24c08c0cf69992d610c0017cb8f77ae7e28f6c1aef0770e5e52"     # protocol 13.10.2026, 04:02
ADDENDA = {
    "B": (ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-b.md",
          "af77c2ac8573ee1c08bba9c75cd7e46739c8850f5988d066b3254a557153d651"),
    "C": (ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-c.md",
          "264a3810d7637aa3c6c6e39fbab82068d9c15f59ca4f6b88a820b7cc2cc41d5c"),
}
CAL_L = {"b2_marginal": "gj1-b1l-b2-marginal-temperature", "b2_verifier": "gj1-b1l-b2-verifier-platt",
         "b2_switch": "gj1-b1l-b2-switch-forward-backward"}
OUTPUT_FILES = ("calibration_records.json", "oof/b1l_oof.npz", "design_lora_dev.md")
RX_RUN = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


class LoraRefusal(Exception):
    """A document, a file or a run was refused (GJ.10, process rule 6, criteria chapter 3, addenda B and C)."""


def now() -> str:
    return md.now()


def rel(p) -> str:
    try:
        return md.rel(p)
    except ValueError:
        return str(p)


def sha(p) -> str:
    return md.sha256_file(p)


def _log(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


# ---------------------------------------------------------------- records of the criteria (chapter 0)

def addenda_check() -> dict:
    """The addenda B and C have the SHA-256 of ADDENDA. src/m10_b2x.py has the SHA-256 of addendum C chapter 9."""
    out = {}
    for name, (p, want) in ADDENDA.items():
        if not p.is_file() or sha(p) != want:
            raise LoraRefusal(f"addendum {name} ({rel(p)}) does not have the SHA-256 {want[:12]}... of {rel(SCRIPT)}")
        out[rel(p)] = want
    crit = sha(md.CRITERIA)
    if crit != md.CRITERIA_SHA:
        raise LoraRefusal("the criteria file differs from the protocol value")
    out[rel(md.CRITERIA)] = crit
    text = ADDENDA["C"][0].read_text(encoding="utf-8")
    m = re.search(r"`src/m10_b2x\.py`\s*\|\s*`([0-9a-f]{64})`", text)
    b2x = sha(bx.SCRIPT)
    if not m or m.group(1) != b2x:
        raise LoraRefusal("src/m10_b2x.py does not have the SHA-256 of addendum C, chapter 9")
    return {"files": out, "m10_b2x_sha256_equal_addendum_c": True}


def code_record() -> dict:
    import m10_score as ms  # noqa: PLC0415  (frozen scorer; m10_b2x uses it)
    return {rel(p): sha(p) for p in (SCRIPT, bx.SCRIPT, md.SCRIPT, Path(guard.__file__), Path(ms.__file__))}


def fixed_design() -> dict:
    return {"fold_runs": list(FOLD_RUNS), "classes": list(CLASSES), "temperature_bounds": [md.T_MIN, md.T_MAX],
            "forms": list(bx.FORMS), "strength_grid": {k: list(v) for k, v in bx.STRENGTH_GRID.items()},
            "selection": {"rule": "addendum C, rule C3 (m10_b2x.select_form)", "margin": bx.ENTRY_MARGIN,
                          "tie_accuracy": bx.TIE_ACCURACY},
            "a_grid": list(md.A_GRID), "p17": [md.P17_ACC, md.P17_COV], "clip": [md.CLIP_LO, md.CLIP_HI],
            "platt_bound": md.PLATT_BOUND, "choice_7_3_item_5": {"tie": TIE_B1, "tie_gives": "B1"},
            "calibration_ids": dict(CAL_L),
            "units": "each block of each dev document (the b1 suffix of the block); 5 folds by parliament"}


# ---------------------------------------------------------------- job folder and logits files (chapter 1)

def read_job(job_dir: Path) -> dict:
    """The job folder: for each document the set, the fold, the b1 suffix ids and the prefix SHA-256 (no text is
    kept), the plan and the SHA-256 of the files. With a manifest: the 3 job files must have its SHA-256."""
    job_dir = Path(job_dir)
    files = {n: sha(job_dir / n) for n in ("docs.jsonl", "plan.json")}
    man = md.read_json(job_dir / "manifest.json") if (job_dir / "manifest.json").is_file() else None
    if man is not None:
        files["manifest.json"] = sha(job_dir / "manifest.json")
        diff = [n for n in ("docs.jsonl", "plan.json") if (man.get("files") or {}).get(n) != files[n]]
        if diff:
            raise LoraRefusal(f"{rel(job_dir)}: {diff} differ from manifest.json")
    docs = {}
    with open(job_dir / "docs.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            x = json.loads(line)
            d = str(x["doc_id"])
            if d in docs:
                raise LoraRefusal(f"{rel(job_dir / 'docs.jsonl')}: a doc id occurs two times")
            docs[d] = {"set": x["set"], "fold": x["fold"], "prefix_sha256": x["prefix_sha256"],
                       "b1": [s["suffix_id"] for s in x["suffixes"] if s["kind"] == "b1"]}
    plan = md.read_json(job_dir / "plan.json")
    if tuple(plan.get("classes") or ()) != CLASSES:
        raise LoraRefusal("plan.json has another class order than m10_design.OPTIONS")
    runs = {r["name"]: r for r in plan["runs"]}
    for k, name in enumerate(FOLD_RUNS, 1):
        r = runs.get(name) or {}
        if (r.get("eval") or {}).get("sets") != ["dev"] or (r.get("eval") or {}).get("folds") != [k] \
                or k in (r.get("train_folds") or [k]):
            raise LoraRefusal(f"plan.json: the run {name} is not the run with the held-out fold {k}")
    return {"dir": job_dir, "docs": docs, "plan": plan, "manifest": man, "files": files,
            "trainer_sha256": ((man or {}).get("code_sha256") or {}).get("src/m10_lora_blocks.py")}


def logits_sha_map(run: dict) -> dict:
    """{doc_id: SHA-256} of the logits files in a run.json of the trainer (key eval, then each entry of eval_more)."""
    out: dict = {}
    for ev in [run.get("eval") or {}, *(run.get("eval_more") or [])]:
        out.update(ev.get("files_sha256") or {})
    return {str(k): v for k, v in out.items()}


def run_folder(states_dir: Path, name: str, want: list[str], job: dict, other_is_refusal: bool = True) -> dict:
    """The folder of one run without a logit: the run record, the names of the logits files and their SHA-256.
    want: the documents that the caller can read from this run. A logits file of another document is a refusal
    (other_is_refusal) or it is counted and not opened. Returns {"files": {doc: path}, "missing": [...], ...}."""
    if not RX_RUN.match(name):
        raise LoraRefusal(f"run name {name!r} is not a safe folder name")
    folder = Path(states_dir) / name
    rp = folder / "run.json"
    if not rp.is_file():
        raise LoraRefusal(f"no run record {rel(rp)}: fetch the run first")
    run = md.read_json(rp)
    if run.get("run") != name or run.get("state") != RUN_DONE or run.get("logits_complete") is not True:
        raise LoraRefusal(f"{rel(rp)}: not the finished run {name} (state {run.get('state')!r}, logits_complete "
                          f"{run.get('logits_complete')!r})")
    want_set = set(want)
    have = sorted(p.stem for p in (folder / "logits").glob("*.npz")) if (folder / "logits").is_dir() else []
    other = [d for d in have if d not in want_set]
    if other and other_is_refusal:
        kinds = Counter((job["docs"].get(d) or {}).get("set") or "not in the job" for d in other)
        raise LoraRefusal(f"{rel(folder / 'logits')}: {len(other)} logits files of documents that this command does "
                          f"not read from the run {name} (sets: {dict(kinds)}): refused before a logit is read")
    want_sha = logits_sha_map(run)
    files, shas, missing, diff = {}, {}, [], []
    for d in want:
        p = folder / "logits" / f"{d}.npz"
        if not p.is_file():
            missing.append(d)
            continue
        h = sha(p)
        if want_sha.get(d) != h:
            diff.append(d)
        files[d], shas[rel(p)] = p, h
    if diff:
        raise LoraRefusal(f"{rel(folder)}: {len(diff)} logits files do not have the SHA-256 of run.json")
    trainer = job.get("trainer_sha256")
    return {"run": name, "folder": rel(folder), "run_json": {"path": rel(rp), "sha256": sha(rp)},
            "script_sha256": run.get("script_sha256"),
            "script_sha256_equal_job_manifest": None if trainer is None else run.get("script_sha256") == trainer,
            "job_files_equal": {n: (run.get("data_files_sha256") or {}).get(n) == job["files"][n]
                                for n in ("docs.jsonl", "plan.json")},
            "plan_equal": run.get("plan") == job["plan"],
            "files": files, "files_sha256": shas, "files_digest": md.digest_lines(shas), "missing": missing,
            "other_files_not_opened": len(other)}


def read_logits(p: Path, d: str, meta: dict, run: str, block_ids: list[str]) -> np.ndarray:
    """The logits [n, 6] of one document (float64). The suffix ids must be the b1 suffix ids of the job and the
    block ids of the document in reading order (m10_prompts.item: the id of a b1 suffix is the block id)."""
    with np.load(p, allow_pickle=False) as z:
        if not set(NPZ_KEYS) <= set(z.files):
            raise LoraRefusal(f"{d}: the logits file does not have the keys {NPZ_KEYS}")
        if str(z["run"]) != run:
            raise LoraRefusal(f"{d}: the logits file is of the run {str(z['run'])!r}, not of {run!r}")
        sid = [str(s) for s in z["suffix_ids"].tolist()]
        if sid != list(meta["b1"]) or sid != list(block_ids):
            raise LoraRefusal(f"{d}: the suffix ids are not the b1 suffixes of the job and the blocks of the document")
        if str(z["prefix_sha256"]) != meta["prefix_sha256"]:
            raise LoraRefusal(f"{d}: the prefix SHA-256 of the logits file is not the value of the job")
        lg = z["logits"]
        if lg.dtype != np.float32 or lg.shape != (len(sid), len(CLASSES)):
            raise LoraRefusal(f"{d}: the logits have the wrong type or shape")
        S = np.array(lg, dtype=np.float64)
    if not np.isfinite(S).all():
        raise LoraRefusal(f"{d}: the logits are not finite")
    return S


def collect_oof(states_dir: Path, job: dict, dev: bx.Dev, on_first_value=None,
                strict: bool = False) -> tuple[dict, dict]:
    """The out-of-fold logits of all dev documents from the 5 fold runs (chapter 2). No logit is read before each
    folder passed its checks. strict (real run): each run record must name the trainer, the job files and the plan
    of the job manifest. Returns ({doc: logits [n, 6]}, record)."""
    ids = dev.ids
    for d in ids:
        m = job["docs"].get(d)
        if m is None or m["set"] != "dev" or m["fold"] != dev.fold[d]:
            raise LoraRefusal("the job folder has another set or another fold than the frozen design for a dev "
                              "document")
    if sum(1 for m in job["docs"].values() if m["set"] == "dev") != len(ids):
        raise LoraRefusal("the dev documents of the job folder are not the dev documents of daten/gj/sets.json")
    folders = {}
    for k, name in enumerate(FOLD_RUNS, 1):
        want = [d for d in ids if dev.fold[d] == k]
        folders[name] = run_folder(states_dir, name, want, job)
    if strict:
        bad = [n for n, f in folders.items() if not (f["script_sha256_equal_job_manifest"] and f["plan_equal"]
                                                     and all(f["job_files_equal"].values()))]
        if bad:
            raise LoraRefusal(f"the runs {bad} do not have the trainer, the job files or the plan of the job manifest")
    missing = [d for f in folders.values() for d in f["missing"]]
    if missing:
        raise LoraRefusal(f"{len(missing)} dev documents have no logits file: the design needs each dev document "
                          "(the forms and the scores use all 193 documents)")
    if on_first_value:
        on_first_value()
    S = {}
    for d in ids:
        name = FOLD_RUNS[dev.fold[d] - 1]
        S[d] = read_logits(folders[name]["files"][d], d, job["docs"][d], name, [b["block"] for b in
                                                                                  dev.rules[d]["blocks"]])
        if len(S[d]) != len(dev.refs[d]):
            raise LoraRefusal(f"{d}: the logits and the label file have another block count")
    rec = {name: {k: v for k, v in f.items() if k not in ("files", "files_sha256")} for name, f in folders.items()}
    return S, {"folder": rel(states_dir), "runs": rec, "documents": len(S),
               "blocks": int(sum(len(x) for x in S.values()))}


# ---------------------------------------------------------------- design (chapter 3)

def head_rows() -> tuple[dict | None, dict | None]:
    """The stored dev rows of the 5 forms with the posteriors of the B1 head (stream D1), if the file exists."""
    if not HEAD_TABLE.is_file():
        return None, None
    x = md.read_json(HEAD_TABLE)
    return x, {"path": rel(HEAD_TABLE), "sha256": sha(HEAD_TABLE)}


def choice_b1l_or_b1(row_l: dict, frozen_design: dict) -> dict:
    """Criteria 7.3 item 5 (proposal P5): the higher 6-option accuracy on the non-certain dev blocks wins; a
    difference of 0.005 or less gives B1. Integer rule: B1-L wins if (k_L - k_B1) * 1000 > 5 * n."""
    acc = frozen_design["measures_information"]["accuracy"]
    n, n_b1 = int(row_l["non_certain_blocks"]), int(acc["noncertain_blocks"])
    k_l = int(row_l["non_certain_correct"])
    k_b1 = int(round(float(acc["noncertain_b2_viterbi"]) * n_b1))
    same = n == n_b1
    wins = same and (k_l - k_b1) * 1000 > int(TIE_B1 * 1000) * n
    return {"rule": "criteria 7.3 item 5: used only if B1-L and B1 both enter", "non_certain_blocks": n,
            "non_certain_blocks_b1": n_b1, "same_set_of_non_certain_blocks": same,
            "correct_b1_l": k_l, "correct_b1": k_b1, "accuracy_b1_l": md.r6(k_l / n) if n else None,
            "accuracy_b1": md.r6(k_b1 / n_b1) if n_b1 else None,
            "difference": md.r6(k_l / n - k_b1 / n_b1) if n and n_b1 else None, "tie": TIE_B1,
            "choice": "B1-L" if wins else "B1",
            "source_b1": "daten/gj/design/design.json, key measures_information.accuracy (B1 head and the frozen "
                         "free form of B2, out-of-fold)"}


def calibration_records(out: Path, frozen_records: dict, thresholds: dict, info: dict, ver_b2: dict, t1: dict,
                        t2: dict, form: str, strength, n_blocks: int, outputs: dict, check_run: bool) -> dict:
    """The calibration records of B1-L in the form of the frozen design (m10_design.calibration_records). The D1
    records and the tier records are the records of the frozen design, without a change. The 3 records of the
    heads for blocks and switch boundaries are replaced by the 3 records of B1-L."""
    oof = rel(out / "oof/b1l_oof.npz")
    fit = {"fit_set_file": oof, "fit_set_digest": outputs[oof]}
    note = "check run with stand-in logits: not a result. " if check_run else ""
    par = {"temperature_b1l": t1["T"], "temperature_b2": t2["T"]}
    if strength is not None:
        par["strength"] = float(strength)
    old = {md.CAL["b2_marginal"], md.CAL["b2_verifier"], md.CAL["b2_switch"]}
    rec = {k: v for k, v in frozen_records["records"].items() if k not in old}
    kind = {k: v for k, v in frozen_records["kind_of"].items() if k not in old}
    rec[CAL_L["b2_marginal"]] = {
        "calibration_method": "forward_backward_temperature", "calibrated_kind": "block_slot", **fit,
        "fit_n": n_blocks, "reference_source": md.REFERENCE, "in_sample": False, "target_status": "not_measured",
        "calibration_parameters": md._params(**par),
        "measure_sets": md._ms("dev out-of-fold", info["b2_marginals_after_t2"]),
        "calibration_note": note + f"B1-L (LoRA on Apertus with a linear head): B2 block marginal of the form {form} "
                                   "(addendum C) after the B1-L temperature and one B2 temperature"}
    rec[CAL_L["b2_verifier"]] = {
        "calibration_method": "verifier_platt", "calibrated_kind": "block_slot", **fit, "fit_n": ver_b2["n"],
        "reference_source": md.REFERENCE, "in_sample": False, "target_status": "not_measured",
        "calibration_parameters": md._params(alpha=ver_b2["alpha"], beta=ver_b2["beta"]),
        "measure_sets": md._ms("non-certain blocks of dev_out_of_design, in-sample", info["verifier_b2_in_sample"]),
        "calibration_note": note + "B1-L: Platt map of the B2 marginal of the rule option; fit set: the non-certain "
                                   "blocks of dev_out_of_design"}
    rec[CAL_L["b2_switch"]] = {
        "calibration_method": "forward_backward_temperature", "calibrated_kind": "author_switch", **fit,
        "fit_n": int(info["switch_all_gaps"]["n"]), "reference_source": md.REFERENCE, "in_sample": False,
        "target_status": "not_measured", "calibration_parameters": md._params(temperature_b1l=t1["T"]),
        "measure_sets": md._ms("dev out-of-fold, all gaps", info["switch_all_gaps"]),
        "calibration_note": note + f"B1-L: pairwise forward-backward probability of a switch at the gap in the form "
                                   f"{form}, with the B1-L temperature; the B2 temperature is not applied"}
    kind.update({CAL_L["b2_marginal"]: "block_slot", CAL_L["b2_verifier"]: "block_slot",
                 CAL_L["b2_switch"]: "author_switch"})
    th = {"document_text_parts": dict(frozen_records["thresholds"]["document_text_parts"]),
          "block_slot": {v: thresholds["block_slot"][v]["a"] for v in ("b12_entered", "b12_not_entered")},
          "author_switch": {v: thresholds["author_switch"][v]["a"] for v in ("b12_entered", "b12_not_entered")}}
    return {"version": VERSION, "synthetic": False, "check_run": check_run, "status": STATUS, "records": rec,
            "kind_of": kind, "thresholds": th, "variant_keys": frozen_records["variant_keys"],
            "variant_note": "b12_entered and b12_not_entered mean here: B1-L and its B2 form entered or not"}


def run_design(states_dir: Path = STATES, job_dir: Path = JOB, out: Path = OUT, design_dir: Path = md.DESIGN,
               check_run: bool = False, quiet: bool = False) -> dict:
    """Chapter 3 on the dev out-of-fold logits. Writes the outputs of chapter 4 to out."""
    log = (lambda m: None) if quiet else _log
    t_start = time.perf_counter()
    states_dir, job_dir, out, design_dir = (Path(x).resolve() for x in (states_dir, job_dir, out, design_dir))
    real_paths = (states_dir, job_dir, out) == (STATES.resolve(), JOB.resolve(), OUT.resolve())
    if not check_run and not real_paths:
        raise LoraRefusal("the real design uses daten/gj/states/lora_b1, daten/gj/jobs/lora_b1 and "
                          "daten/gj/design_lora; other folders need --check-run")
    if check_run and (out == OUT.resolve() or GJ.resolve() in out.parents or states_dir == STATES.resolve()):
        raise LoraRefusal("a check run never reads daten/gj/states/lora_b1 and never writes below daten/gj")
    if (out / "design_lora.json").exists():
        raise LoraRefusal(f"{rel(out)} holds an earlier design run of B1-L (design_lora.json): the records stay")
    out.mkdir(parents=True, exist_ok=True)
    # ---- run record and SHA-256 before the first out-of-fold value (GJ.2)
    ev = md.Events(out / "design_lora.events.jsonl")
    script_sha = sha(SCRIPT)
    rec = {"schema": "parlpdfech-gj-design-lora/1", "version": VERSION, "status": STATUS, "actor": ACTOR,
           "check_run": check_run, "started": now(), "script": {"path": rel(SCRIPT), "sha256": script_sha},
           "code": code_record(), "fixed_design": fixed_design(),
           "state": "the script SHA-256 is recorded; no out-of-fold value of B1-L exists"}
    md.write_json(out / "design_lora.json", rec)
    rec["script_sha256_recorded"] = ev.add("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    md.write_json(out / "design_lora.json", rec)
    log(f"script SHA-256 {script_sha} recorded in {rel(out / 'design_lora.json')}")
    # ---- records of the criteria, guard, frozen design, job (no logit is read)
    rec["criteria"] = addenda_check()
    sets = md.load_sets()
    all_dev = sorted({str(d) for d in sets["dev"]}, key=int)
    rec["guard"] = md.assert_fit_ids(all_dev, sets)             # GJ.10 before any file of a document
    frozen = md.load_frozen(design_dir, md.FREEZE_FILE if md.FREEZE_FILE.is_file() else None)
    if frozen.synthetic:
        raise LoraRefusal("the frozen design is synthetic")
    fr_sha = sha(md.FREEZE_FILE) if md.FREEZE_FILE.is_file() else None
    if fr_sha != FREEZE_SHA:
        raise LoraRefusal(f"{rel(md.FREEZE_FILE)} does not have the SHA-256 {FREEZE_SHA[:12]}... of the protocol")
    frozen_design = md.read_json(design_dir / "design.json")
    frozen_records = md.read_json(design_dir / "calibration_records.json")
    Qh, pd1, hinfo = bx.load_head_oof(design_dir)                # stored D1 posteriors of the frozen design
    del Qh
    dev = bx.load_dev(pd1, design_dir)
    if dev.ids != all_dev:
        raise LoraRefusal("the dev documents of the frozen design are not the dev documents of sets.json")
    job = read_job(job_dir)
    ood = {str(d) for d in sets["dev_out_of_design"]} & set(dev.ids)
    rec.update({"inputs": {**dev.inputs, **hinfo["files"],
                           rel(md.FREEZE_FILE): fr_sha,
                           **{rel(design_dir / f): h for f, h in frozen.files.items()},
                           **{rel(job_dir / n): h for n, h in job["files"].items()}},
                "documents": {"dev": len(dev.ids), "dev_out_of_design": len(ood),
                              "blocks": int(sum(len(dev.refs[d]) for d in dev.ids))}})
    md.write_json(out / "design_lora.json", rec)

    def first_value() -> None:
        rec["first_out_of_fold_value"] = ev.add("first_out_of_fold_value", what="logits of the fold runs")
        md.write_json(out / "design_lora.json", rec)

    fc = job_dir / "fetch_check.json"
    if fc.is_file():
        x = md.read_json(fc)
        rec["fetch_check"] = {"path": rel(fc), "sha256": sha(fc), "scope": x.get("scope"), "result": x.get("result")}
        if not check_run and x.get("result") != "PASS":
            raise LoraRefusal(f"{rel(fc)}: the fetch check of src/m10_lora_job.py did not pass")
    S, lrec = collect_oof(states_dir, job, dev, first_value, strict=not check_run)
    rec["logits"] = lrec
    md.write_json(out / "design_lora.json", rec)
    log(f"logits: {lrec['documents']} dev documents, {lrec['blocks']} blocks, 5 fold runs")
    # ---- 3.1 temperature of B1-L
    ids = dev.ids
    offsets, a = {}, 0
    for d in ids:
        offsets[d] = (a, a + len(S[d]))
        a += len(S[d])
    S_all = np.concatenate([S[d] for d in ids])
    y = np.array([md.OPTIONS.index(o) for d in ids for o in dev.refs[d]])
    bdoc = np.concatenate([np.full(len(S[d]), i) for i, d in enumerate(ids)])
    fold_blk = np.concatenate([np.full(len(S[d]), dev.fold[d]) for d in ids])
    t1 = md.fit_temperature(S_all, y)
    Q_all = md.softmax(S_all / t1["T"])
    Q = {d: Q_all[offsets[d][0]:offsets[d][1]] for d in ids}
    log(f"B1-L temperature T {t1['T']:.4f} (NLL {t1['nll_before']:.4f} -> {t1['nll_after']:.4f})")
    # ---- 3.2 and 3.3: the 5 forms with the fold rule and the selection rule of addendum C
    tab = bx.forms_table(Q, pd1, design_dir, log=log)
    dev2, sc = tab.pop("_dev"), tab.pop("_scorer")
    if dev2.ids != ids or any(dev2.view[d] != dev.view[d] for d in ids):
        raise LoraRefusal("m10_b2x.forms_table used another rule view than this script")
    sel = tab["selection"]
    form = sel["form"]
    st = tab["strength"].get(form)
    strength = None if st is None else float(st["final"])
    log(f"B2 form by addendum C: {form} (permitted {sel['permitted']}; strength {strength})")
    # ---- 3.4 B2 temperature on the marginals of the selected form
    marg = np.concatenate([tab["marginals"][form][d] for d in ids])
    t2 = md.fit_temperature(np.log(np.maximum(marg, md.P_FLOOR)), y)
    marg2 = md.temper(marg, t2["T"])
    # ---- 3.5 verifier map of B1-L (fit set: non-certain blocks of dev_out_of_design)
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
    # ---- 3.6 written values and the threshold a (the functions of the frozen design)
    tt = md.read_json(design_dir / "tier_table.json")
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
    info = {"b1l_before_t": md.measures(md.softmax(S_all), y),
            "b1l_after_t": md.measures(Q_all, y, grp_b, boot=True),
            "b2_marginals_before_t2": md.measures(marg, y),
            "b2_marginals_after_t2": md.measures(marg2, y, grp_b, boot=True),
            "switch_all_gaps": md.measures(md.binary(wv["gaps"]["p"]), np.where(wv["gaps"]["ref"], 0, 1),
                                           wv["gaps"]["doc"], boot=True),
            "written": {k: md.written_measures(v["p"], v["correct"], v["doc"]) for k, v in wv["written"].items()
                        if k.startswith(("block_", "switch_"))},
            "accuracy": {k: v for k, v in wv["accuracy"].items() if not k.startswith("d1_")},
            "verifier_b2_in_sample": md.written_measures(md.platt(np.array(pb), ver_b2), np.array(ybv)) if pb else None,
            "b1l_argmax_accuracy_all_blocks": md.r6((Q_all.argmax(1) == y).mean())}
    # ---- 3.7 choice between B1-L and B1 on dev
    row = tab["forms"][form]
    choice = choice_b1l_or_b1(row, frozen_design)
    # ---- outputs
    outputs = {}
    outputs[rel(out / "oof/b1l_oof.npz")] = md.write_npz(
        out / "oof/b1l_oof.npz", doc_ids=np.array(ids), block_doc=bdoc,
        block_ids=np.array([b["block"] for d in ids for b in dev.rules[d]["blocks"]]), fold=fold_blk, y=y,
        logits=S_all, T=np.float64(t1["T"]), probs_after_t=Q_all, form=np.array(form),
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
    outputs[rel(out / "calibration_records.json")] = md.write_json(out / "calibration_records.json", cal_rec)
    heads, heads_file = head_rows()
    choices = {
        "b1l": {**t1, "units": int(len(y)), "source": "pooled out-of-fold logits of the runs fold1 to fold5"},
        "b2": {"form": form, "selection": sel, "strength": None if st is None else
               {k: st[k] for k in ("grid", "by_fold", "final", "rule")},
               "strength_final": strength, **{f"t2_{k}": v for k, v in t2.items()},
               "hmm": {"file": rel(design_dir / "b2_hmm.json"), "sha256": frozen.files["b2_hmm.json"],
                       "text": "start, transitions and priors of all dev documents (frozen design); out-of-fold "
                               "values use the HMM of the training folds"}},
        "verifier_b2": {**ver_b2, "input": "out-of-fold B2 marginal after T2 of the rule option (non-certain blocks)",
                        "fit_set": "non-certain blocks of dev_out_of_design"},
        "thresholds": cal_rec["thresholds"],
        "thresholds_tables": {k: thresholds[k] for k in ("block_slot", "author_switch")},
        "threshold_document_text_parts_equal_frozen_design": d1_same,
        "certain_pairs": tt["certain_pairs"], "calibration_ids": dict(CAL_L),
        "choice_7_3_item_5": choice}
    table = {"rules": tab["rules"], "forms": tab["forms"], "strength_tables": tab["strength"],
             "counts": tab["counts"],
             "b1_heads_stored": None if heads is None else {"file": heads_file, "rules": heads["rules"],
                                                            "forms": heads["forms"]},
             "b1_heads_design_json": {
                 "accuracy": frozen_design["measures_information"]["accuracy"],
                 "ece_b2_marginals_after_t2": frozen_design["measures_information"]["b2_marginals_after_t2"]["ece"],
                 "written": {k: {x: v.get(x) for x in ("n", "accuracy", "ece", "ece_high")}
                             for k, v in frozen_design["measures_information"]["written"].items()
                             if k.startswith(("block_", "switch_"))},
                 "b2_form": frozen_design["b2"]["form"], "thresholds": frozen_design["thresholds"]}}
    rec.update({"choices": choices, "dev_table": table, "measures_information": info})
    mdp = out / "design_lora_dev.md"
    mdp.write_text(design_markdown(rec, choices, table, info), encoding="utf-8")
    outputs[rel(mdp)] = sha(mdp)
    if code_record() != rec["code"]:
        raise LoraRefusal("a script changed during the design run")
    rec.update({"finished": ev.add("finished"), "seconds": round(time.perf_counter() - t_start, 1),
                "state": "finished", "outputs": outputs})
    h = md.write_json(out / "design_lora.json", rec)
    log(f"design of B1-L finished in {rec['seconds']} s; {rel(out / 'design_lora.json')} SHA-256 {h}")
    return rec


# ---------------------------------------------------------------- design_lora_dev.md (English STE)

def _f(x, n=4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{n}f}"
    return str(x)


def design_markdown(rec: dict, ch: dict, table: dict, info: dict) -> str:
    L = []
    add = L.append
    b2, sel = ch["b2"], ch["b2"]["selection"]
    form = b2["form"]
    row, rules = table["forms"][form], table["rules"]
    hs = table["b1_heads_stored"]
    hd = table["b1_heads_design_json"]
    add("# Gate GJ: design of B1-L on `dev` (temperature, B2 form, threshold a, choice against B1)")
    add("")
    add(f"Run of {rec['started']} (time from the clock). Script `{rec['script']['path']}`, SHA-256 "
        f"`{rec['script']['sha256']}`. Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: "
        "workflow sub-agent (Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    if rec["check_run"]:
        add("This file is the output of a check run with stand-in logits. It is not a result of B1-L.")
        add("")
    add("## 1 Order of the records")
    add("")
    add(f"1. The script wrote its SHA-256 into `design_lora.json` at {rec['script_sha256_recorded']}.")
    add(f"2. The first out-of-fold value of B1-L was read at {rec.get('first_out_of_fold_value')}.")
    add("3. All values of this file are `dev` out-of-fold values. They are information. Each choice uses them only.")
    add("4. This file holds no value of a validation document and no value of a group-7 document.")
    add("5. The script read only the logits of the runs `fold1` to `fold5`. It did not open the run `final`.")
    add(f"6. Documents: {rec['documents']['dev']}. Blocks: {rec['documents']['blocks']}. Documents of "
        f"`dev_out_of_design`: {rec['documents']['dev_out_of_design']}.")
    add("")
    add("## 2 Choices")
    add("")
    add(f"1. B1-L temperature (criteria 8.3): T = {_f(ch['b1l']['T'])}. NLL before T: "
        f"{_f(ch['b1l']['nll_before'])}. NLL after T: {_f(ch['b1l']['nll_after'])}.")
    add(f"2. B2 form (addendum C, rule C3): `{form}`. Permitted forms: "
        f"{', '.join(f'`{x}`' for x in sel['permitted']) or 'none'}. Limits: {sel['limits']['switch_exact']} switch "
        f"documents exact and {sel['limits']['l9_exact']} L9 exact documents.")
    add(f"3. Forms with an accuracy of 0.005 or less below the highest value: "
        f"{', '.join(f'`{x}`' for x in sel['equal_within_0.005'])}. Reason of the pool: {sel['reason']}.")
    if b2["strength"] is not None:
        add(f"4. Strength of `switch_soft` (addendum C, rule C2): for each held-out fold "
            f"{', '.join(f'{k}: {_f(v, 0)}' for k, v in b2['strength']['by_fold'].items())}. Value of the final "
            f"model: {_f(b2['strength_final'], 0)}.")
    else:
        add("4. The selected form has no strength value.")
    add(f"5. B2 temperature (criteria 8.3): T2 = {_f(b2['t2_T'])}. NLL before T2: {_f(b2['t2_nll_before'])}. NLL "
        f"after T2: {_f(b2['t2_nll_after'])}.")
    v = ch["verifier_b2"]
    add(f"6. Verifier map of B1-L (criteria 8.4): alpha {_f(v['alpha'])}, beta {_f(v['beta'])}, fitted on "
        f"{v['n']} non-certain blocks of `dev_out_of_design`.")
    th = ch["thresholds"]
    add(f"7. Threshold a (criteria 8.6). Block labels: {_f(th['block_slot']['b12_entered'])} if B1-L decides, "
        f"{_f(th['block_slot']['b12_not_entered'])} if the rules decide. Switch boundaries: "
        f"{_f(th['author_switch']['b12_entered'])} and {_f(th['author_switch']['b12_not_entered'])}. The sign – "
        "means: no value of the grid meets the conditions, and each label of the kind is unsure.")
    c = ch["choice_7_3_item_5"]
    add(f"8. Choice of criteria 7.3, item 5: {c['choice']}. Accuracy on the {c['non_certain_blocks']} non-certain "
        f"blocks: B1-L {_f(c['accuracy_b1_l'])}, B1 {_f(c['accuracy_b1'])}, difference {_f(c['difference'])}. A "
        "difference of 0.005 or less gives B1. This choice applies only if B1-L and B1 both enter.")
    add("")
    add("## 3 Values on `dev` beside the rules and the B1 heads")
    add("")
    add("| Method | 6-option accuracy on the non-certain blocks | L9 exact documents | Switch documents exact | "
        "Labelled boundary F1 | Written switch boundaries correct | ECE of the block marginals |")
    add("|---|---|---|---|---|---|---|")

    def line(name: str, r: dict, ece) -> None:
        add(f"| {name} | {_f(r['accuracy_non_certain'])} | {r['l9_exact']} | {r['switch_exact']} of "
            f"{r['switch_documents']} | {_f(r['labelled_boundary_f1'])} | {r['written_switch_boundaries_correct']} of "
            f"{r['written_switch_boundaries']} | {_f(ece)} |")
    line("rules", rules, None)
    if hs:
        for f in hs["forms"]:
            line(f"B1 head, `{f}`" + (" (frozen design)" if f == hd["b2_form"] else ""), hs["forms"][f],
                 hs["forms"][f].get("ece_block_marginals_after_t2_information"))
    for f, r in table["forms"].items():
        ece = info["b2_marginals_after_t2"]["ece"] if f == form else r.get("ece_block_marginals_after_t2_information")
        line(f"B1-L, `{f}`" + (" (selected)" if f == form else ""), r, ece)
    add("")
    add(f"1. Documents: {rules['documents']}. Non-certain blocks: {rules['non_certain_blocks']}. Switch documents: "
        f"{rules['switch_documents']}.")
    add("2. The ECE of a form that is not selected uses a pooled B2 temperature of that form (information).")
    if hs:
        add(f"3. The rows of the B1 head come from `{hs['file']['path']}` (stream D1). They are stored values.")
    else:
        add("3. The file with the rows of the B1 head does not exist. The frozen design gives these stored values: "
            f"accuracy on the non-certain blocks {_f(hd['accuracy']['noncertain_b2_viterbi'])}, ECE of the B2 "
            f"marginals {_f(hd['ece_b2_marginals_after_t2'])}.")
    add("")
    add("## 4 Calibration of the written labels on `dev`")
    add("")
    add("| Label set | B1-L: n | B1-L: accuracy | B1-L: ECE | B1-L: 95 % bound | B1 heads: accuracy | B1 heads: ECE |")
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
    add(f"1. B2 block marginals of B1-L after T2, all blocks: ECE {_f(m['ece'])}, 95 % bound {_f(m.get('ece_high'))}, "
        f"Brier score {_f(m['brier'])}, NLL {_f(m['nll'])}. B1 heads: ECE {_f(hd['ece_b2_marginals_after_t2'])}.")
    m = info["b1l_after_t"]
    add(f"2. B1-L posterior after T, all blocks: accuracy {_f(m['accuracy'])}, ECE {_f(m['ece'])}, NLL {_f(m['nll'])}.")
    add("3. The limit of GJ.13 is an ECE of 0.05 or less on validation. The values of this chapter are `dev` values.")
    add("")
    add("## 5 Limits")
    add("")
    add("1. The reference is an AI reference without a human acceptance.")
    add("2. The temperatures, the form, the strength and a come from the same `dev` out-of-fold values. Thus the "
        "`dev` values are a little too good.")
    add("3. The 3 new forms were designed after the `dev` switch analysis of the heads (addendum C, chapter 8).")
    add("4. The strength of a fold uses posteriors of a model that saw the labels of that fold (addendum C, limit 11).")
    add("5. The rules saw 145 of the 193 `dev` documents in their design.")
    add("6. The switch counts are small. A difference of 1 or 2 documents is not a sure difference.")
    add("7. Jonathan did not accept the criteria, addendum B or addendum C. All values have the status EXCEPTION.")
    add("")
    add("## 6 Inputs")
    add("")
    add("| File | SHA-256 |")
    add("|---|---|")
    for k, h in rec["inputs"].items():
        add(f"| `{k}` | `{h}` |")
    for k, h in rec["criteria"]["files"].items():
        add(f"| `{k}` | `{h}` |")
    for name, f in rec["logits"]["runs"].items():
        add(f"| `{f['run_json']['path']}` | `{f['run_json']['sha256']}` |")
        add(f"| logits files of `{name}` (digest of the sorted path and SHA-256 lines) | `{f['files_digest']}` |")
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- frozen B1-L design and decisions (chapter 5)

@dataclass
class LoraDesign:
    dir: Path
    record: dict
    T: float
    form: str
    strength: float | None
    T2: float
    verifier: dict
    records: dict          # calibration_records.json
    sha256: str            # of design_lora.json
    files: dict
    check_run: bool


def load_design_lora(design_dir: Path, frozen: md.Frozen, real: bool = True) -> LoraDesign:
    """The finished design of B1-L. Each output file must have the SHA-256 of design_lora.json. The frozen design
    files must be the files that the design of B1-L used. real: refuses the design of a check run."""
    design_dir = Path(design_dir).resolve()
    p = design_dir / "design_lora.json"
    if not p.is_file():
        raise LoraRefusal(f"no design of B1-L: {rel(p)} does not exist")
    rec = md.read_json(p)
    if rec.get("state") != "finished":
        raise LoraRefusal(f"{rel(p)}: the design run is not finished")
    if real and (rec.get("check_run") or design_dir != OUT.resolve()):
        raise LoraRefusal("a held-out document needs the real design of B1-L in daten/gj/design_lora (not a check run)")
    files = {}
    for name in OUTPUT_FILES:
        q = design_dir / name
        want = (rec.get("outputs") or {}).get(rel(q))
        if not q.is_file() or want is None or sha(q) != want:
            raise LoraRefusal(f"{rel(q)} does not have the SHA-256 of design_lora.json")
        files[rel(q)] = want
    for f, h in frozen.files.items():
        if (rec.get("inputs") or {}).get(rel(frozen.design_dir / f)) != h:
            raise LoraRefusal(f"the design of B1-L used another file {f} of the frozen design")
    ch = rec["choices"]
    form = ch["b2"]["form"]
    if form not in bx.FORMS:
        raise LoraRefusal(f"unknown B2 form {form!r}")
    strength = ch["b2"]["strength_final"]
    if (form in bx.STRENGTH_GRID) != (strength is not None):
        raise LoraRefusal("the strength value does not agree with the form")
    return LoraDesign(design_dir, rec, float(ch["b1l"]["T"]), form, None if strength is None else float(strength),
                      float(ch["b2"]["t2_T"]), ch["verifier_b2"], md.read_json(design_dir / "calibration_records.json"),
                      sha(p), files, bool(rec.get("check_run")))


def lora_calibration_file(frozen: md.Frozen, ld: LoraDesign, entry_d1: bool, entry_b1l: bool) -> dict:
    """The calibration file of src/m10_writer.py for one variant: m10_design.calibration_file on the records of
    B1-L (the D1 records and the tier records are the records of the frozen design)."""
    return md.calibration_file(dataclasses.replace(frozen, records=ld.records), bool(entry_d1), bool(entry_b1l))


@dataclass(frozen=True)
class Gate:
    ids: frozenset
    counts: dict


def decide_gate(ids, sets: dict | None = None, validation_run: Path | None = None) -> Gate:
    """Chapter 5, gate. Test documents: refused by src/m10_guard.py. Group-7 documents: always refused. Validation
    documents: only with the started run record of src/m10_lora_validation.py that lists them."""
    sets = sets or md.load_sets()
    ids = [str(d) for d in ids]
    try:
        guard.assert_allowed(ids)
    except guard.GuardRefusal as e:
        raise LoraRefusal(str(e)) from None
    dev = {str(d) for d in sets["dev"]}
    val = {str(d) for d in sets["validation"]}
    g7 = {str(d) for d in sets["group7"]}
    n_val, n_g7 = sum(d in val for d in ids), sum(d in g7 for d in ids)
    other = [d for d in ids if d not in dev and d not in val and d not in g7]
    if n_g7:
        raise LoraRefusal(f"{n_g7} group-7 documents: refused (no method freeze exists; criteria chapters 3 and 10.5)")
    if other:
        raise LoraRefusal(f"{len(other)} documents are not in the sets dev or validation of daten/gj/sets.json")
    if n_val:
        if validation_run is None:
            raise LoraRefusal(f"{n_val} validation documents: only the validation script of B1-L makes their "
                              "decisions (criteria chapter 3, rule 2; one run: criteria 10.3)")
        vr = md.read_json(validation_run)
        if vr.get("state") != "started" or (vr.get("script") or {}).get("sha256") != sha(VALIDATION_SCRIPT) \
                or (vr.get("script") or {}).get("path") != rel(VALIDATION_SCRIPT) or vr.get("check_run") is not False:
            raise LoraRefusal("validation documents: the run record is not a started real run of "
                              "src/m10_lora_validation.py with its SHA-256 now")
        listed = {str(d) for d in vr.get("documents") or []}
        if any(d in val and d not in listed for d in ids):
            raise LoraRefusal("validation documents: a document is not in the list of the validation run record")
    return Gate(frozenset(ids), {"documents": len(ids), "dev": sum(d in dev for d in ids), "validation": n_val,
                                 "group7": 0})


def d1_posterior(d: str, frozen: md.Frozen, states_dir: Path, block_ids: list[str]) -> np.ndarray:
    """The calibrated D1 posterior of the frozen D1 head, as m10_design.cascade_decisions calculates it."""
    s = md.read_states(md.npz_path(states_dir, d), d, block_ids)
    i1 = md.layer_index(s["layers"], (frozen.d1["layer"],))[0]
    return md.head_probs(frozen.d1, s["states"][0, i1].astype(np.float64))[0]


def lora_decisions(d: str, gate: Gate, frozen: md.Frozen, ld: LoraDesign, logits: np.ndarray | None,
                   states_dir: Path, entry_d1: bool, entry_b1l: bool, r2: dict | None = None,
                   dev_ids: set[str] | None = None, logits_info: dict | None = None) -> dict | None:
    """Interface 7 (mode cascade) of B1-L for one document (chapter 5). None: no states file or no logits. A
    ValueError of the B2 form (no path with a weight above 0) goes to the caller."""
    d = str(d)
    if d not in gate.ids:
        raise LoraRefusal(f"{d}: the document did not pass the gate of the decisions")
    if logits is None:
        return None
    base = md.cascade_decisions(d, frozen, Path(states_dir), bool(entry_d1), False, r2, dev_ids)
    if base is None:
        return None
    rule = md.load_rule(d)
    bids = [b["block"] for b in base["blocks"]]
    S = np.asarray(logits, dtype=np.float64)
    if S.shape != (len(bids), len(CLASSES)):
        raise LoraRefusal(f"{d}: the logits do not have one row for each block")
    pd1 = d1_posterior(d, frozen, Path(states_dir), bids)
    r1 = bool(rule["document"]["d1"].get("needs_apertus"))
    ropt, rtier = md.rule_view(rule, md.D1_OPTIONS[int(pd1.argmax())] if r1 else None)
    certain = np.array([(t, o) in frozen.certain for o, t in zip(ropt, rtier)], dtype=bool)
    if [bool(b.get("certain_pair")) for b in base["blocks"]] != certain.tolist() \
            or [b["tier"] for b in base["blocks"]] != list(rtier):
        raise LoraRefusal(f"{d}: the rule view differs from the rule view of m10_design.cascade_decisions")
    Q = md.softmax(S / ld.T)
    b2 = bx.b2x_document(Q, frozen.hmm, ld.form, pd1 if ld.form == "joint" else None, ropt, certain, ld.strength)
    marg2 = md.temper(b2["marg"], ld.T2)
    in_dev = d in (dev_ids or set())
    blocks = []
    for j, bid in enumerate(bids):
        o_r, t_r = ropt[j], rtier[j]
        if certain[j]:
            jm, cid = frozen.certain[(t_r, o_r)]
            blocks.append({"block": bid, "option": o_r, "probs": md.spread(o_r, jm, marg2[j], md.OPTIONS),
                           "source": "rule", "tier": t_r, "calibration": cid, "in_sample": True, "certain_pair": True})
        elif entry_b1l:
            o = b2["written"][j]
            blocks.append({"block": bid, "option": o,
                           "probs": {x: md.as_written(marg2[j, i]) for i, x in enumerate(md.OPTIONS)},
                           "source": "code", "tier": t_r, "calibration": CAL_L["b2_marginal"], "in_sample": in_dev,
                           "certain_pair": False})
        else:
            pv = float(md.platt(marg2[j, md.OPTIONS.index(o_r)], ld.verifier))
            blocks.append({"block": bid, "option": o_r, "probs": md.spread(o_r, pv, marg2[j], md.OPTIONS),
                           "source": "rule", "tier": t_r, "calibration": CAL_L["b2_verifier"], "in_sample": in_dev,
                           "certain_pair": False})
    written = [b["option"] for b in blocks]
    boundaries = [{"after_block": bids[t], "kind": "switch", "p": md.as_written(b2["switch"][t]),
                   "calibration": CAL_L["b2_switch"], "source": "code"} for t in md.switch_gaps(written)]
    dec = dict(base)
    dec.update({"blocks": blocks, "boundaries": boundaries,
                "entry": {"d1": bool(entry_d1), "b1_b2": False, "b1_l": bool(entry_b1l)},
                "b2_form": ld.form,
                "gap_switch_probabilities": [{"after_block": bids[t], "p": md.r6(b2["switch"][t])}
                                             for t in range(len(bids) - 1)],
                "b1_l": {"design": {"path": rel(ld.dir / "design_lora.json"), "sha256": ld.sha256,
                                    "check_run": ld.check_run},
                         "temperature": ld.T, "form": ld.form, "strength": ld.strength, "temperature_b2": ld.T2,
                         "logits": logits_info, "script": {"path": rel(SCRIPT), "sha256": sha(SCRIPT),
                                                           "version": VERSION},
                         "m10_b2x": {"path": rel(bx.SCRIPT), "sha256": sha(bx.SCRIPT), "version": bx.VERSION}}})
    return dec


def decide_documents(ids: list[str], out: Path, design_dir: Path = OUT, states_dir: Path = STATES,
                     job_dir: Path = JOB, head_states: Path = HEAD_STATES, entry_d1: bool = False,
                     entry_b1l: bool = True, frozen_dir: Path = md.DESIGN) -> dict:
    """The command decide: decisions of B1-L for dev documents from the logits of the fold run of each document.
    Each file passes check_decisions of src/m10_cascade.py and of src/m10_writer.py before it is written."""
    import m10_cascade as casc  # noqa: PLC0415  (frozen; check of interface 7)
    import m10_writer as w  # noqa: PLC0415  (frozen; check of interface 7)
    out = Path(out).resolve()
    sets = md.load_sets()
    ids = sorted({str(d) for d in ids}, key=int)
    gate = decide_gate(ids, sets, None)                        # refuses validation and group-7 documents
    addenda_check()
    frozen = md.load_frozen(frozen_dir, md.FREEZE_FILE if md.FREEZE_FILE.is_file() else None)
    if frozen.freeze is not None:
        frozen.freeze["_sha256"] = sha(md.FREEZE_FILE)
    ld = load_design_lora(design_dir, frozen, real=Path(design_dir).resolve() == OUT.resolve())
    job = read_job(job_dir)
    folds = md.read_json(frozen.design_dir / "folds.json")["fold_of_doc"]
    dev_ids = {str(x) for x in sets["dev"]}
    cals = {e: lora_calibration_file(frozen, ld, entry_d1, e)["calibrations"] for e in (True, False)}
    by_run: dict[str, list[str]] = {}
    for d in ids:
        by_run.setdefault(FOLD_RUNS[int(folds[d]) - 1], []).append(d)
    folders = {name: run_folder(states_dir, name, [x for x in dev_ids if int(folds[x]) == FOLD_RUNS.index(name) + 1],
                                job) for name in by_run}
    out.mkdir(parents=True, exist_ok=True)
    outputs, without = {}, []
    for d in ids:
        name = FOLD_RUNS[int(folds[d]) - 1]
        p = folders[name]["files"].get(d)
        doc, rule = md.load_doc(d), md.load_rule(d)
        S = None if p is None else read_logits(p, d, job["docs"][d], name, [b["block"] for b in doc["blocks"]])
        info = None if p is None else {"file": rel(p), "sha256": sha(p), "run": name}
        dec = lora_decisions(d, gate, frozen, ld, S, head_states, entry_d1, entry_b1l, None, dev_ids, info)
        if dec is None:
            without.append(d)
            continue
        bad = casc.check_decisions(dec, rule) + w.check_decisions(d, doc, dec, cals[bool(entry_b1l)])
        if bad:
            raise LoraRefusal(f"{d}: the decisions do not pass the checks of interface 7: {bad[:5]}")
        outputs[rel(out / f"{d}.json")] = md.write_json(out / f"{d}.json", dec)
    cp = out / "calibrations.json"
    outputs[rel(cp)] = md.write_json(cp, {**lora_calibration_file(frozen, ld, entry_d1, entry_b1l),
                                          "entry": {"d1": bool(entry_d1), "b1_l": bool(entry_b1l)}, "status": STATUS})
    rec = {"version": VERSION, "status": STATUS, "made": now(), "script": {"path": rel(SCRIPT), "sha256": sha(SCRIPT)},
           "design_lora": {"path": rel(ld.dir / "design_lora.json"), "sha256": ld.sha256, "check_run": ld.check_run},
           "entry": {"d1": bool(entry_d1), "b1_l": bool(entry_b1l)}, "documents": gate.counts,
           "without_states_or_logits": without, "outputs": outputs,
           "note": "dev documents: logits of the fold run of the document; T, T2 and the HMM saw the document"}
    md.write_json(out / "decide_run.json", rec)
    return rec


# ---------------------------------------------------------------- command line

def cmd_run(args) -> int:
    rec = run_design(Path(args.states), Path(args.job), Path(args.out), check_run=args.check_run)
    ch = rec["choices"]
    form = ch["b2"]["form"]
    row, rules = rec["dev_table"]["forms"][form], rec["dev_table"]["rules"]
    print(json.dumps({
        "design_lora_json": {"path": rel(Path(args.out) / "design_lora.json"),
                             "sha256": sha(Path(args.out) / "design_lora.json")},
        "T": md.r6(ch["b1l"]["T"]), "form": form, "permitted": ch["b2"]["selection"]["permitted"],
        "strength_final": ch["b2"]["strength_final"], "T2": md.r6(ch["b2"]["t2_T"]),
        "thresholds": ch["thresholds"],
        "dev_out_of_fold": {"accuracy_non_certain": row["accuracy_non_certain"], "l9_exact": row["l9_exact"],
                            "switch_exact": row["switch_exact"], "labelled_boundary_f1": row["labelled_boundary_f1"],
                            "ece_b2_marginals": rec["measures_information"]["b2_marginals_after_t2"]["ece"]},
        "rules": {k: rules[k] for k in ("accuracy_non_certain", "l9_exact", "switch_exact", "labelled_boundary_f1")},
        "choice_7_3_item_5": ch["choice_7_3_item_5"]["choice"], "outputs": rec["outputs"]}, ensure_ascii=False))
    return 0


def cmd_decide(args) -> int:
    ids = [i for a in args.set for i in guard.read_items(a)]
    yes = {"yes": True, "no": False}
    rec = decide_documents(ids, Path(args.out), Path(args.design), Path(args.states), Path(args.job),
                           Path(args.head_states), yes[args.entry_d1], yes[args.entry_b1l])
    print(json.dumps({"documents": rec["documents"], "decisions_files": len(rec["outputs"]) - 1,
                      "without_states_or_logits": len(rec["without_states_or_logits"]),
                      "run_record": rel(Path(args.out) / "decide_run.json")}, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="the dev design of B1-L from the out-of-fold logits of the 5 fold runs")
    r.add_argument("--states", default=str(STATES))
    r.add_argument("--job", default=str(JOB))
    r.add_argument("--out", default=str(OUT))
    r.add_argument("--check-run", action="store_true", help="stand-in logits in other folders (check script only)")
    r.set_defaults(func=cmd_run)
    d = sub.add_parser("decide", help="decisions of B1-L for dev documents (interface 7)")
    d.add_argument("--set", nargs="+", required=True, help="doc ids or list files (m10_guard.read_items)")
    d.add_argument("--out", required=True)
    d.add_argument("--design", default=str(OUT))
    d.add_argument("--states", default=str(STATES))
    d.add_argument("--job", default=str(JOB))
    d.add_argument("--head-states", default=str(HEAD_STATES))
    d.add_argument("--entry-d1", choices=("yes", "no"), default="no")
    d.add_argument("--entry-b1l", choices=("yes", "no"), default="yes")
    d.set_defaults(func=cmd_decide)
    args = ap.parse_args()
    try:
        return args.func(args)
    except (LoraRefusal, md.DesignRefusal) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Gate GJ (status EXCEPTION), criteria chapters 5, 7.3 item 1, 8.1 to 8.4, 8.6 and 10.1, plan chapters 3.3 and 3.4:
the dev design of D1, B1 and B2, the threshold a, the verifier maps, the LoRA trigger, the content of the design
freeze file, and the cascade mode with Apertus states.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream
DESIGN of workflow wf_0befda9d-e60, for the main agent. No human checked this file. This file does not change an
existing file. Status of all outputs: EXCEPTION (process rule 10), NOT RELEASED.

0 Order of the records (GJ.2, criteria chapter 5 item 6)
  The command run writes the SHA-256 of this file into the run record <out>/run_design.json and into the event log
  <out>/run_design.events.jsonl before it calculates the first out-of-fold value. The folds, the seeds, the grids,
  the training units and each selection rule are constants and functions of this file (chapter 2). Thus the
  SHA-256 of this file records them. The event log gives the clock time of each event in the order of the events.

1 Inputs (explicit paths; never a fallback of src/m03_iso_paths.py)
  states       <states>/states/<doc_id>.npz of GPU-1 (src/m10_vm_states.py, interface 6): suffix_ids (D1, then
               B<n> in reading order), layers (int16), states float16 [n_suffix, n_layers, hidden]. If
               <states>/outputs.json exists, the SHA-256 of each file must be equal to it.
  labels       daten/gj/labels/<doc_id>.json (interface 4): d1 and the option of each block (dev documents only).
  sets         daten/gj/sets.json (interface 3): dev, dev_out_of_design, validation, group7.
  rules        daten/gj/rules/<doc_id>.json (src/m10_rules.py): rule option and tier of each block, the S1 rule id,
               needs_apertus and the variants by_d1.
  docs         daten/gj/docs/<doc_id>.json (interface 2): the block ids in reading order.
  parliaments  the key body_key of daten/iso/pool.csv and daten/iso/gruppen.csv (criteria chapter 3 item 2).
  template     daten/gj/jobs/gpu1_labelled/template.json: each states file must have its template SHA-256.

2 Fixed design (before the first out-of-fold value)
  2.1 Folds (criteria chapter 5 items 2 to 4, proposal P8). Sort the parliaments of the dev documents by their
      count of dev documents, high to low; equal counts: body_key in string order. Put each parliament into the
      fold with the fewest documents; equal counts: the lower fold number (1 to 5). All units of a document are
      in the fold of its parliament. D1, B1, B2, the temperatures, P17 and the LoRA trigger use these folds.
  2.2 Heads (criteria chapter 5 items 7 to 9, chapter 8.1). D1: K = 4 (A, B, C, D), one unit for each dev
      document with states (the D1 suffix). B1: K = 6 (submitted, reasoning, response, recommendation, title,
      none), one unit for each block of a dev document with states (the B1 suffix of the block; each dev block
      has a label, criteria chapter 2.3). Reference: the label files (AI reference with the pilot overrides).
      Model: L2 multinomial logistic regression with natural priors (no class weights). Minimize
      0.5 * ||W||^2 + C * sum_i CE_i (the intercept has no penalty), from zero, scipy.optimize.minimize L-BFGS-B,
      maxiter 1000, the other options at the scipy defaults, float64. This is the objective of scikit-learn
      LogisticRegression (lbfgs, multinomial). The project environment holds numpy and scipy, but not
      scikit-learn, and uv --offline cannot resolve scikit-learn 1.9.0 of the uv archive (12.10.2026). Thus this
      file uses numpy and scipy. src/m10_design_test.py compares the two when sklearn can be imported.
      Features: the state after decoder layer k at the last suffix token, z-score with the mean and the standard
      deviation (ddof 0) of the training rows; a standard deviation below 1e-6 becomes 1.
      Grid: k in LAYERS, C in C_GRID. For each (k, C) and each fold: fit on the other folds, logits of the fold.
      Choice: the lowest pooled out-of-fold NLL (mean of -ln q(reference option), softmax of the logits, no
      clip). Each (k, C) with an NLL less than TIE_NLL above the lowest NLL is equal to it; of these, the smallest
      C wins, then the lower k (criteria chapter 5 item 8). The final head: the same fit on all dev units.
  2.3 Temperature (criteria chapter 8.3). One T for D1 and one T for B1: minimize the NLL of softmax(z / T) on the
      pooled out-of-fold logits of the chosen (k, C). Bounded scalar search over ln T in [ln 0.05, ln 20]
      (scipy minimize_scalar, method bounded, xatol 1e-10).
  2.4 Code step B2 (criteria chapter 5 items 11 and 12, plan chapter 3.4 item 5). Hidden state = (option, last
      text family), 10 states (STATES). The last text family is the family of the last block with a Submission
      option (S) or a Response option (R); title and none blocks keep it. A transition to a title or none state
      must keep the family; a transition to a text state is always permitted. Transitions and start values:
      add-one counts over the permitted transitions of the reference state sequences of the training folds
      (final file: all dev documents). Prior: the share of each option among the reference blocks of the
      training folds (an option with 0 blocks gets 0.5 / n blocks; the run record lists such cases).
      Emission of state s at block t: q_t(option of s) / prior(option of s), with q_t = the B1 posterior after the
      B1 temperature (out-of-fold for the design).
      Free form: the HMM over the 10 states.
      Joint form: for each D1 option k, the states that k permits: the states with no last family, and the states
      whose last family is a family of k (A: S; B: R; C: S and R; D: none). The transitions are not normalized
      again, thus a path has the weight P_free(path) * prod(emissions) * sum of P(k) over each k that permits the
      path (the D1 option permits the states of its families, it does not require them; criteria chapter 2.4).
      Document weights w_k proportional to P(k) * L_k (L_k: forward sum on the states of k); block marginals and
      switch probabilities = the sum of w_k times the values of k. P(k): the D1 posterior after the D1 temperature.
      Choice of the form: the lower out-of-fold NLL of the block options (no clip); a difference below TIE_NLL
      gives the free form (proposal P10).
      Path: Viterbi (exact MAP path of the form; joint: the Viterbi path of each k, scored with the weight above).
      Switch probability of the gap after block t: the pairwise forward-backward probability that block t has a
      last family S or R and block t + 1 has a text option of the other family (criteria chapter 2.5 item 2).
      B2 temperature: one T2 on the out-of-fold block marginals of the chosen form: q' proportional to q^(1/T2)
      (the same search as 2.3 on ln q). The switch probability has no other temperature.
  2.5 Rule tiers (criteria chapter 8.7). Pairs (rule tier, rule option) of the plain rule output of each dev
      block (the key blocks of the rule file; daten/gj/rules). Certain: precision 0.99 or more on the dev blocks
      and 30 or more dev documents, and precision 0.99 or more on the blocks in the 48 documents of
      dev_out_of_design (no such block: not certain, proposal P9). Probability: Jeffreys posterior mean
      (k + 0.5) / (n + 1) on the dev blocks, in-sample flag. In the design and in the cascade, a block is certain
      if its (tier, option) of the rule view is a certain pair. Rule view: the plain rule output; for a document
      with needs_apertus (S1 rule id R1), the variant by_d1 of the D1 decision of the head (criteria chapter 7.1
      item 5).
  2.6 Verifier maps (criteria chapter 8.4 items 1, 4 and 5). Platt: p' = 1 / (1 + exp(-(alpha * logit(p) +
      beta))), minimize the NLL, L-BFGS-B from (1, 0), |alpha| and |beta| at most 100, p clipped to
      [1e-6, 1 - 1e-6] before the logit. D1 verifier: p = the calibrated out-of-fold D1 probability of the S1 rule
      option (key document.d1.option of the rule file); y = the S1 rule option is the reference D1; fit set: the
      documents of dev_out_of_design with states. B2 verifier: p = the out-of-fold B2 marginal after T2 of the
      rule option of each non-certain block; y = the rule option is the reference option; fit set: the
      non-certain blocks of the documents of dev_out_of_design with states.
  2.7 Threshold a (criteria chapter 8.6, P17). For each label kind and each variant of the entry decisions: the
      smallest a in A_GRID such that the labels with p >= a have an accuracy of 0.95 or more and a coverage of
      0.50 or more. p is the written probability after the clip to [0.005, 0.995]. Units: the dev documents and
      blocks with states. Apertus and code values are out-of-fold; rule and verifier values are in-sample.
      document_text_parts, D1 enters: the D1 head on each document. D1 does not enter: the D1 verifier on each
      document without the S1 rule id R1, the D1 head on the R1 documents.
      block_slot, B1 and B2 enter: certain blocks with the tier probability; other blocks with the Viterbi option
      and its B2 marginal after T2. B1 and B2 do not enter: certain blocks as before; other blocks with the rule
      option and the B2 verifier probability.
      author_switch: the switch gaps of the written block path (B1 and B2 enter: the Viterbi path with the
      certain blocks; else the rule view), with the switch probability of the gap.
      If no a meets the conditions, a is null and each label of the kind is unsure.
  2.8 LoRA trigger (criteria chapter 7.3 item 1). B1-L starts if (1) on the non-certain blocks of the documents
      of dev_out_of_design, the accuracy of the Viterbi options (B1 and B2) is not more than the accuracy of the
      rule view; or (2) the ECE (criteria chapter 6.2 item 1, after the clip) of the B2 block marginals after T2
      on all dev blocks with states is more than 0.05.
  2.9 Measures (criteria chapter 6.2; information): ECE with 10 bins of equal width of max q (the last bin holds
      1.0), ECE with equal mass, class-wise ECE, Brier score, NLL, reliability table, coverage against error,
      wrong labels with max q >= 0.99, all after the clip without a new sum. Document bootstrap of the ECE:
      2,000 resamples, seed 20261013 (numpy default_rng, one call integers(0, n, size=(2000, n))), 5 % and 95 %
      quantiles. A binary kind has q = (p, 1 - p).

3 Guards (process rule 6, GJ.10, criteria chapter 3)
  Before a states file is opened for a fit, each document must be in the key dev of daten/gj/sets.json and
  src/m10_guard.py must allow it with the allowed split dev only. Else DesignRefusal (no file is read).
  The command run reads only dev documents. It prints only dev values. The option --docs-file needs --synthetic.
  The cascade mode (apply) reads the states of a validation document only with the real design freeze file
  daten/gj/design_freeze.json (not a dry run, no problems) whose SHA-256 values are equal to the design files and
  to this file, and the states of a group-7 document only if the method freeze manifest
  daten/gj/freeze_manifest.json also exists. A test document is refused by src/m10_guard.py. The
  command apply prints only counts and SHA-256 values.

4 Outputs of the command run (<out>, default daten/gj/design/)
  folds.json, folds.csv; run_design.json, run_design.events.jsonl; heads/d1_head.npz, heads/b1_head.npz;
  b2_hmm.json; verifiers.json; tier_table.json; thresholds.json; lora_trigger.json; calibration_records.json;
  oof/d1_oof.npz, oof/b1_oof.npz, oof/b2_oof.npz (all out-of-fold values, for the recalculation of GJ.19);
  design.json (all choices and the SHA-256 of each output); design_dev.md (English STE). The command refuses an
  output folder that holds an earlier design run (design.json or run_design.events.jsonl).

5 Cascade mode (command apply; function cascade_decisions for src/m10_cascade.py)
  Input: the frozen design folder, the states of a document, the entry decisions (D1 entered or not; B1 and B2
  entered or not) and an optional R2 file {doc_id: {"p", "calibration"}}. Output: daten/gj/decisions/<doc>.json
  (interface 7, mode cascade) and a calibration file {"calibrations": {id: {...}}} for src/m10_writer.py.
  D1: if D1 entered or the S1 rule id is R1: the option of the highest calibrated D1 probability, probs = the 4
  calibrated probabilities, source apertus_head. Else: the S1 rule option with the D1 verifier probability p,
  source rule.
  Blocks: a certain block: the rule option with the Jeffreys mean p, source rule, in_sample true. Else, if B1 and
  B2 entered: the Viterbi option of the frozen form, probs = the 6 B2 marginals after T2, source code. Else: the
  rule option with the B2 verifier probability p, source rule. in_sample of a head or code label: true only for
  a dev document (the final heads saw all dev documents).
  A rule label with p: the other options share 1 - p in proportion to the calibrated Apertus distribution (D1
  posterior or B2 marginals). Each probability is clipped to [0.005, 0.995] and rounded to 4 decimals (as the
  writer; proposal P7), so the output passes check_decisions of src/m10_cascade.py.
  Boundaries: the switch gaps of the written block path, p = the switch probability of the gap, source code.
  The key gap_switch_probabilities gives the switch probability of each gap (information for the measures).
  A document without a states file gives None: the caller uses the floor converter F1 (criteria chapter 4 item 7).

6 Design freeze (command freeze; criteria chapter 10.1, proposal P12)
  The content of daten/gj/design_freeze.json: the SHA-256 of the template, of each src/m10_* file, of the criteria
  file, of daten/gj/sets.json and of the label files; each file of the design folder with its SHA-256 and the
  choices (layer k and C, temperatures, HMM, B2 form, Platt maps, certain pairs, values a, LoRA trigger); the
  FROZEN_FILES check of src/m05_gate3a_v4_measure.py and the model fingerprint. --dry-run writes to --out (not to
  daten/gj/design_freeze.json). The command refuses a synthetic design without --dry-run, a changed criteria file,
  a changed FROZEN_FILE and a freeze file that exists.

Usage (from the project folder; one command on one line):
  uv run --offline --frozen --no-sync python src/m10_design.py folds
  uv run --offline --frozen --no-sync python src/m10_design.py run --states daten/gj/states/gpu1_labelled
  uv run --offline --frozen --no-sync python src/m10_design.py freeze [--dry-run --out FILE] [--design DIR]
  uv run --offline --frozen --no-sync python src/m10_design.py apply --design daten/gj/design
      --states daten/gj/states/gpu1_labelled --entry-d1 yes|no --entry-b12 yes|no --out daten/gj/decisions
      --calibrations-out FILE [--r2 FILE] [--freeze daten/gj/design_freeze.json] DOC|LIST ...
  Check script on synthetic states: uv run --offline --frozen --no-sync python src/m10_design_test.py
"""

from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_docs as docs  # noqa: E402  (interface 2, stream B)
import m10_guard as guard  # noqa: E402  (split guard, process rule 6)

VERSION = "m10-design-1"
SCRIPT = Path(__file__).resolve()
ROOT = guard.ROOT
GJ = ROOT / "daten/gj"
SETS = GJ / "sets.json"
LABELS = GJ / "labels"
RULES = GJ / "rules"
DESIGN = GJ / "design"
DECISIONS = GJ / "decisions"
STATES_GPU1 = GJ / "states/gpu1_labelled"
JOB_TEMPLATE = GJ / "jobs/gpu1_labelled/template.json"
POOL_CSV = ROOT / "daten/iso/pool.csv"
GROUPS_CSV = ROOT / "daten/iso/gruppen.csv"
CRITERIA = ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria.md"
CRITERIA_SHA = "6f6d15c0562cba2070995c302080a9aaedfe665f8d746ed5b0fdd9248bc20bfe"   # protocol 12.10.2026, 20:26
T0 = "72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c"            # criteria chapter 16 item 4
FREEZE_FILE = GJ / "design_freeze.json"
METHOD_FREEZE = GJ / "freeze_manifest.json"
MEASURE_SCRIPT = ROOT / "src/m05_gate3a_v4_measure.py"
FLOOR_CERTAINTY = GJ / "calibration/certainty_dev.json"     # tier table of src/m10_calibrate.py (information)
STATUS = "EXCEPTION (process rule 10, gate GJ); NOT RELEASED"
REFERENCE = "AI reference E20 v4.1 (daten/iso/v4/ref41, daten/iso/v4/pool_ref41) with the 3 pilot overrides"

# ---------------------------------------------------------------- fixed design (chapter 2 of the docstring)
N_FOLDS = 5
LAYERS = (8, 12, 16, 20, 24, 28, 32)
C_GRID = (1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0)
TIE_NLL = 1e-4
LBFGS_MAXITER = 1000
STD_FLOOR = 1e-6
T_MIN, T_MAX = 0.05, 20.0
T_XATOL = 1e-10
PLATT_BOUND = 100.0
PLATT_EPS = 1e-6
PRIOR_ZERO = 0.5
A_GRID = (0.6, 0.7, 0.8, 0.9, 0.95, 0.99)
P17_ACC, P17_COV = 0.95, 0.50
CERTAIN_PREC, CERTAIN_DOCS = 0.99, 30
LORA_ECE = 0.05
ECE_BINS = 10
BOOT_N, BOOT_SEED = 2000, 20261013
CLIP_LO, CLIP_HI = 0.005, 0.995
P_FLOOR = 1e-300

D1_OPTIONS = ("A", "B", "C", "D")
OPTIONS = ("submitted", "reasoning", "response", "recommendation", "title", "none")
FAMILY = {"submitted": "S", "reasoning": "S", "response": "R", "recommendation": "R"}
D1_FAMILIES = {"A": frozenset({"S"}), "B": frozenset({"R"}), "C": frozenset({"S", "R"}), "D": frozenset()}
STATES = (("submitted", "S"), ("reasoning", "S"), ("response", "R"), ("recommendation", "R"),
          ("title", ""), ("title", "S"), ("title", "R"), ("none", ""), ("none", "S"), ("none", "R"))
S_OPT = np.array([OPTIONS.index(o) for o, _ in STATES])
S_LF = tuple(lf for _, lf in STATES)
ALLOWED_T = np.array([[(o2 in FAMILY) or (lf2 == lf1) for (o2, lf2) in STATES] for (_, lf1) in STATES])
ALLOWED_START = np.array([(o in FAMILY) or lf == "" for o, lf in STATES])
D1_MASK = {k: np.array([lf == "" or lf in fam for _, lf in STATES]) for k, fam in D1_FAMILIES.items()}
SWITCH_PAIR = np.array([[lf1 in ("S", "R") and o2 in FAMILY and FAMILY[o2] != lf1 for (o2, _) in STATES]
                        for (_, lf1) in STATES])
OPT_OF_STATE = np.zeros((len(STATES), len(OPTIONS)))
OPT_OF_STATE[np.arange(len(STATES)), S_OPT] = 1.0

CAL = {"d1_head": "gj1-d1-head-temperature", "d1_verifier": "gj1-d1-verifier-platt",
       "b2_marginal": "gj1-b2-marginal-temperature", "b2_verifier": "gj1-b2-verifier-platt",
       "b2_switch": "gj1-b2-switch-forward-backward"}
TIER_CAL_PREFIX = "gj1-tier-"


class DesignRefusal(Exception):
    """A document or a file was refused (GJ.10, process rule 6, criteria chapter 3)."""


# ---------------------------------------------------------------- helpers

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p) -> str:
    return guard.sha256_file(Path(p))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel(p) -> str:
    return guard.rel(Path(p))


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p, x) -> str:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(x, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    p.write_bytes(raw)
    return sha256_bytes(raw)


def write_npz(p, **arrays) -> str:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        np.savez(f, **arrays)
    return sha256_file(p)


def r6(x):
    return None if x is None else round(float(x), 6)


def digest_lines(pairs: dict) -> str:
    return sha256_bytes("\n".join(f"{k} {v}" for k, v in sorted(pairs.items())).encode())


def clip(p):
    return np.clip(p, CLIP_LO, CLIP_HI)


def lse(S: np.ndarray) -> np.ndarray:
    m = S.max(1, keepdims=True)
    return m + np.log(np.exp(S - m).sum(1, keepdims=True))


def softmax(S: np.ndarray) -> np.ndarray:
    e = np.exp(S - S.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def nll_logits(S: np.ndarray, y: np.ndarray) -> float:
    lp = S - lse(S)
    return float(-lp[np.arange(len(y)), y].mean())


def nll_probs(P: np.ndarray, y: np.ndarray) -> float:
    return float(-np.log(np.maximum(P[np.arange(len(y)), y], P_FLOOR)).mean())


def logit(p):
    p = np.clip(np.asarray(p, dtype=np.float64), PLATT_EPS, 1 - PLATT_EPS)
    return np.log(p) - np.log1p(-p)


def expit(z):
    from scipy.special import expit as _e
    return _e(z)


class Events:
    """Append-only event log with clock times (GJ.2)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        self.times: dict[str, str] = {}

    def add(self, event: str, **kw) -> str:
        t = now()
        self.times.setdefault(event, t)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": event, "time": t, **kw}, ensure_ascii=False) + "\n")
            f.flush()
        return t


# ---------------------------------------------------------------- sets, guard, folds

def load_sets() -> dict:
    return read_json(SETS)


def assert_fit_ids(ids, sets: dict | None = None) -> dict:
    """GJ.10: each document of a fit is a dev document (sets.json key dev) and src/m10_guard.py allows it with the
    allowed split dev only. No file of the documents is read before this check."""
    sets = sets or load_sets()
    ids = [str(d) for d in ids]
    dev = {str(d) for d in sets["dev"]}
    other = {str(d) for k in ("validation", "group7") for d in sets.get(k) or []}
    bad = [d for d in ids if d not in dev]
    if bad:
        kinds = Counter("validation or group 7" if d in other else "not a dev document" for d in bad)
        raise DesignRefusal(f"GJ.10: {len(bad)} documents of a fit are refused ({dict(kinds)})")
    try:
        g = guard.assert_allowed(ids, ("dev",))
    except guard.GuardRefusal as e:
        raise DesignRefusal(f"GJ.10: {e}") from None
    return {k: v for k, v in g.items() if k not in ("split_of", "parliament_of")}


def body_keys(ids) -> dict[str, str]:
    """doc_id -> body_key from daten/iso/pool.csv and daten/iso/gruppen.csv (criteria chapter 3 item 2)."""
    want = {str(d) for d in ids}
    out: dict[str, str] = {}
    for p in (POOL_CSV, GROUPS_CSV):
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = r["doc_id"]
                if d in want:
                    if d in out and out[d] != r["body_key"]:
                        raise ValueError(f"{d}: two body keys in pool.csv and gruppen.csv")
                    out[d] = r["body_key"]
    miss = want - set(out)
    if miss:
        raise ValueError(f"{len(miss)} documents have no body_key in pool.csv or gruppen.csv")
    return out


def make_folds(ids, bk: dict[str, str], n_folds: int = N_FOLDS) -> dict:
    """Chapter 2.1: greedy folds by parliament (criteria chapter 5 items 2 to 4, proposal P8)."""
    ids = sorted({str(d) for d in ids}, key=int)
    count = Counter(bk[d] for d in ids)
    order = sorted(count, key=lambda b: (-count[b], b))
    size = [0] * n_folds
    fold_of: dict[str, int] = {}
    for b in order:
        f = min(range(n_folds), key=lambda i: (size[i], i))
        fold_of[b] = f + 1
        size[f] += count[b]
    return {"rule": "parliaments sorted by dev document count (high to low), then body_key (string order); each "
                    "parliament into the fold with the fewest documents, equal counts: the lower fold number",
            "n_folds": n_folds, "documents": len(ids), "parliaments": len(order),
            "documents_by_fold": {str(i + 1): size[i] for i in range(n_folds)},
            "parliament_order": [{"body_key": b, "documents": count[b], "fold": fold_of[b]} for b in order],
            "fold_of_doc": {d: fold_of[bk[d]] for d in ids},
            "body_key_of_doc": {d: bk[d] for d in ids}}


def write_folds(folds: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    h1 = write_json(out / "folds.json", folds)
    lines = ["doc_id,body_key,fold"] + [f"{d},{folds['body_key_of_doc'][d]},{f}" for d, f in folds["fold_of_doc"].items()]
    raw = ("\n".join(lines) + "\n").encode("utf-8")
    (out / "folds.csv").write_bytes(raw)
    return {rel(out / "folds.json"): h1, rel(out / "folds.csv"): sha256_bytes(raw)}


# ---------------------------------------------------------------- documents, labels, rules, states

def load_label(d: str) -> dict:
    x = read_json(LABELS / f"{d}.json")
    if str(x.get("doc_id")) != d:
        raise ValueError(f"{d}: label file of another document")
    return x


def load_rule(d: str) -> dict:
    x = read_json(RULES / f"{d}.json")
    if str(x.get("doc_id")) != d:
        raise ValueError(f"{d}: rule file of another document")
    return x


def load_doc(d: str) -> dict:
    x = read_json(docs.doc_path(d))
    if str(x.get("doc_id")) != d:
        raise ValueError(f"{d}: doc file of another document")
    return x


def npz_path(states_dir, d: str) -> Path:
    return Path(states_dir) / "states" / f"{d}.npz"


def read_states(path: Path, d: str, block_ids: list[str]) -> dict:
    """One states file of interface 6. The suffix ids must be D1 and then the blocks of the doc file in order."""
    with np.load(path, allow_pickle=False) as z:
        if str(z["doc_id"]) != d:
            raise ValueError(f"{d}: states file of another document")
        sid = [str(s) for s in z["suffix_ids"].tolist()]
        if sid != ["D1"] + list(block_ids):
            raise ValueError(f"{d}: suffix ids are not D1 and the blocks of the doc file in reading order")
        layers = tuple(int(k) for k in z["layers"])
        st = z["states"]
        if st.dtype != np.float16 or st.ndim != 3 or st.shape[:2] != (len(sid), len(layers)):
            raise ValueError(f"{d}: states have the wrong type or shape")
        states = np.array(st)
        meta = {k: str(z[k]) for k in ("template_sha256", "model_fingerprint", "code_sha256", "dtype", "version")
                if k in z.files}
        meta["synthetic"] = bool(z["synthetic"]) if "synthetic" in z.files else False
    if not np.isfinite(states).all():
        raise ValueError(f"{d}: states are not finite")
    return {"layers": layers, "states": states, "meta": meta}


def layer_index(layers: tuple[int, ...], want) -> list[int]:
    miss = [k for k in want if k not in layers]
    if miss:
        raise ValueError(f"the states have no layer {miss}")
    return [layers.index(k) for k in want]


def outputs_check(states_dir: Path) -> dict | None:
    p = Path(states_dir) / "outputs.json"
    if not p.is_file():
        return None
    x = read_json(p)
    files = x.get("files", x) if isinstance(x, dict) else {}
    return {str(k): str(v) for k, v in files.items() if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)}


@dataclass
class DevData:
    ids: list[str]                      # dev documents with states (id order)
    missing: list[str]                  # dev documents without a states file
    hidden: int
    xd: np.ndarray                      # float16 [n_docs, len(LAYERS), hidden]
    yd: np.ndarray                      # D1 index [n_docs]
    xb: np.ndarray                      # float16 [n_blocks, len(LAYERS), hidden]
    yb: np.ndarray                      # option index [n_blocks]
    bdoc: np.ndarray                    # document index of each block [n_blocks]
    block_ids: dict[str, list[str]]
    offsets: dict[str, tuple[int, int]]
    meta: dict = field(default_factory=dict)


def assemble(states_dir: Path, ids: list[str], sets: dict, expect_template: str) -> DevData:
    """Read the dev states for the fits. GJ.10 first (no file is read before it)."""
    g = assert_fit_ids(ids, sets)
    outs = outputs_check(states_dir)
    xd, yd, xb, yb, bdoc = [], [], [], [], []
    have, missing, block_ids, offsets = [], [], {}, {}
    file_sha, templates, fingerprints, synthetic, hidden = {}, Counter(), Counter(), Counter(), set()
    sha_diff = []
    pos = 0
    for d in sorted(ids, key=int):
        doc = load_doc(d)
        lab = load_label(d)
        bids = [b["block"] for b in doc["blocks"]]
        if [b["block"] for b in lab["blocks"]] != bids:
            raise ValueError(f"{d}: label blocks differ from the doc file")
        p = npz_path(states_dir, d)
        if not p.is_file():
            missing.append(d)
            continue
        h = sha256_file(p)
        file_sha[rel(p)] = h
        if outs is not None and outs.get(f"states/{d}.npz") not in (None, h):
            sha_diff.append(d)
        s = read_states(p, d, bids)
        li = layer_index(s["layers"], LAYERS)
        st = s["states"][:, li, :]
        templates[s["meta"].get("template_sha256", "absent")] += 1
        fingerprints[s["meta"].get("model_fingerprint", "absent")] += 1
        synthetic[s["meta"]["synthetic"]] += 1
        hidden.add(st.shape[2])
        xd.append(st[0])
        yd.append(D1_OPTIONS.index(lab["d1"]))
        xb.append(st[1:])
        yb.extend(OPTIONS.index(b["option"]) for b in lab["blocks"])
        bdoc.extend([len(have)] * len(bids))
        offsets[d] = (pos, pos + len(bids))
        pos += len(bids)
        block_ids[d] = bids
        have.append(d)
    if sha_diff:
        raise ValueError(f"{len(sha_diff)} states files differ from outputs.json")
    if len(hidden) > 1:
        raise ValueError("states with different hidden sizes")
    if not have:
        raise ValueError("no dev document has a states file")
    bad_t = [t for t in templates if t != expect_template]
    if bad_t:
        raise ValueError(f"template SHA-256 of the states is not {expect_template}: {sorted(bad_t)}")
    meta = {"guard": g, "states_files": file_sha, "states_files_digest": digest_lines(file_sha),
            "outputs_json": None if outs is None else {"checked": len(file_sha), "different": 0},
            "template_sha256": dict(templates), "model_fingerprint": dict(fingerprints),
            "synthetic": {str(k): v for k, v in synthetic.items()}}
    return DevData(have, missing, hidden.pop(), np.stack(xd), np.array(yd), np.concatenate(xb), np.array(yb),
                   np.array(bdoc), block_ids, offsets, meta)


# ---------------------------------------------------------------- heads (chapter 2.2)

def zscore_fit(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu = X.mean(0)
    sd = X.std(0)
    return mu, np.where(sd < STD_FLOOR, 1.0, sd)


def fit_lr(Z: np.ndarray, y: np.ndarray, K: int, C: float) -> dict:
    """L2 multinomial logistic regression: minimize 0.5 * ||W||^2 + C * sum_i CE_i; intercept without penalty."""
    from scipy.optimize import minimize
    n, d = Z.shape
    Y = np.zeros((n, K))
    Y[np.arange(n), y] = 1.0

    def f(th):
        W = th[:d * K].reshape(d, K)
        b = th[d * K:]
        S = Z @ W + b
        lp = S - lse(S)
        loss = 0.5 * float(np.sum(W * W)) + C * float(-(Y * lp).sum())
        G = C * (np.exp(lp) - Y)
        return loss, np.concatenate([(Z.T @ G + W).ravel(), G.sum(0)])

    r = minimize(f, np.zeros(d * K + K), jac=True, method="L-BFGS-B", options={"maxiter": LBFGS_MAXITER})
    return {"W": r.x[:d * K].reshape(d, K), "b": r.x[d * K:], "nit": int(r.nit), "converged": bool(r.success),
            "objective": float(r.fun)}


def cv_grid(x16: np.ndarray, y: np.ndarray, K: int, fold: np.ndarray, name: str, log) -> dict:
    """Out-of-fold logits for each (k, C) of the grid. x16: float16 [n, len(LAYERS), hidden]."""
    n = len(y)
    oof = np.zeros((len(LAYERS), len(C_GRID), n, K))
    fits = []
    folds = sorted(set(int(f) for f in fold))
    for li, k in enumerate(LAYERS):
        X = x16[:, li, :].astype(np.float64)
        for f in folds:
            te = fold == f
            tr = ~te
            mu, sd = zscore_fit(X[tr])
            Ztr = (X[tr] - mu) / sd
            Zte = (X[te] - mu) / sd
            for ci, C in enumerate(C_GRID):
                t0 = time.perf_counter()
                h = fit_lr(Ztr, y[tr], K, C)
                oof[li, ci][te] = Zte @ h["W"] + h["b"]
                fits.append({"layer": k, "C": C, "fold": f, "n_train": int(tr.sum()), "n_out": int(te.sum()),
                             "classes_in_train": int(len(set(y[tr].tolist()))), "nit": h["nit"],
                             "converged": h["converged"], "seconds": round(time.perf_counter() - t0, 3)})
        log(f"{name}: layer {k} done")
    nll = np.array([[nll_logits(oof[li, ci], y) for ci in range(len(C_GRID))] for li in range(len(LAYERS))])
    return {"oof": oof, "nll": nll, "fits": fits}


def choose(nll: np.ndarray) -> tuple[int, int]:
    """Criteria chapter 5 item 8: the lowest NLL; within TIE_NLL of it: the smallest C, then the lower k."""
    best = float(nll.min())
    cand = sorted((C_GRID[ci], LAYERS[li], li, ci) for li in range(len(LAYERS)) for ci in range(len(C_GRID))
                  if nll[li, ci] < best + TIE_NLL)
    return cand[0][2], cand[0][3]


def fit_temperature(S: np.ndarray, y: np.ndarray) -> dict:
    from scipy.optimize import minimize_scalar

    def f(lt):
        return nll_logits(S / math.exp(lt), y)
    r = minimize_scalar(f, bounds=(math.log(T_MIN), math.log(T_MAX)), method="bounded", options={"xatol": T_XATOL})
    T = math.exp(float(r.x))
    return {"T": T, "nll_before": f(0.0), "nll_after": float(f(float(r.x))),
            "at_bound": bool(abs(float(r.x) - math.log(T_MIN)) < 1e-6 or abs(float(r.x) - math.log(T_MAX)) < 1e-6)}


def final_head(x16: np.ndarray, y: np.ndarray, K: int, li: int, C: float) -> dict:
    X = x16[:, li, :].astype(np.float64)
    mu, sd = zscore_fit(X)
    h = fit_lr((X - mu) / sd, y, K, C)
    return {"mu": mu, "sd": sd, "W": h["W"], "b": h["b"], "nit": h["nit"], "converged": h["converged"]}


def head_logits(head: dict, X: np.ndarray) -> np.ndarray:
    Z = (np.asarray(X, dtype=np.float64) - head["mu"]) / head["sd"]
    return Z @ head["W"] + head["b"]


# ---------------------------------------------------------------- code step B2 (chapter 2.4)

def state_path(options) -> list[int]:
    lf = ""
    out = []
    for o in options:
        if o in FAMILY:
            lf = FAMILY[o]
        out.append(STATES.index((o, lf)))
    return out


def hmm_fit(seqs) -> dict:
    nS = len(STATES)
    tc = np.zeros((nS, nS))
    sc = np.zeros(nS)
    oc = np.zeros(len(OPTIONS))
    for opts in seqs:
        sp = state_path(opts)
        if not sp:
            continue
        if not ALLOWED_START[sp[0]] or any(not ALLOWED_T[a, b] for a, b in zip(sp, sp[1:])):
            raise ValueError("a reference sequence has a transition that the state space does not permit")
        sc[sp[0]] += 1
        for a, b in zip(sp, sp[1:]):
            tc[a, b] += 1
        for o in opts:
            oc[OPTIONS.index(o)] += 1
    trans = np.where(ALLOWED_T, tc + 1.0, 0.0)
    trans /= trans.sum(1, keepdims=True)
    start = np.where(ALLOWED_START, sc + 1.0, 0.0)
    start /= start.sum()
    n = oc.sum()
    zero = [OPTIONS[i] for i in range(len(OPTIONS)) if oc[i] == 0]
    prior = np.where(oc > 0, oc, PRIOR_ZERO) / n
    return {"trans": trans, "start": start, "prior": prior, "trans_counts": tc, "start_counts": sc,
            "option_counts": oc, "zero_prior_options": zero, "sequences": len(seqs)}


def forward_backward(E: np.ndarray, start: np.ndarray, trans: np.ndarray, mask=None) -> dict:
    """Scaled forward-backward. E [n, S] >= 0. Returns gamma [n, S], switch [n - 1] and the log likelihood."""
    if mask is not None:
        E = E * mask
    n, nS = E.shape
    alpha = np.zeros((n, nS))
    c = np.zeros(n)
    a = start * E[0]
    c[0] = a.sum()
    if not c[0] > 0:
        return {"gamma": np.zeros((n, nS)), "switch": np.zeros(max(n - 1, 0)), "loglik": -math.inf}
    alpha[0] = a / c[0]
    for t in range(1, n):
        a = (alpha[t - 1] @ trans) * E[t]
        c[t] = a.sum()
        if not c[t] > 0:
            return {"gamma": np.zeros((n, nS)), "switch": np.zeros(n - 1), "loglik": -math.inf}
        alpha[t] = a / c[t]
    beta = np.ones((n, nS))
    for t in range(n - 2, -1, -1):
        beta[t] = trans @ (E[t + 1] * beta[t + 1]) / c[t + 1]
    gamma = alpha * beta
    gamma /= gamma.sum(1, keepdims=True)
    sw = np.zeros(max(n - 1, 0))
    tsw = trans * SWITCH_PAIR
    for t in range(n - 1):
        sw[t] = float(alpha[t] @ tsw @ (E[t + 1] * beta[t + 1])) / c[t + 1]
    return {"gamma": gamma, "switch": np.clip(sw, 0.0, 1.0), "loglik": float(np.log(c).sum())}


def viterbi(logE: np.ndarray, logstart: np.ndarray, logtrans: np.ndarray, mask=None) -> tuple[list[int], float]:
    if mask is not None:
        logE = np.where(mask, logE, -np.inf)
    n, nS = logE.shape
    delta = logstart + logE[0]
    back = np.zeros((n, nS), dtype=np.int64)
    for t in range(1, n):
        cand = delta[:, None] + logtrans
        back[t] = cand.argmax(0)
        delta = cand.max(0) + logE[t]
    s = int(delta.argmax())
    score = float(delta[s])
    path = [s]
    for t in range(n - 1, 0, -1):
        s = int(back[t, s])
        path.append(s)
    return path[::-1], score


def _log0(x):
    with np.errstate(divide="ignore"):
        return np.log(x)


def b2_document(Q: np.ndarray, hmm: dict, form: str, pd1: np.ndarray | None) -> dict:
    """B2 on one document. Q [n, 6]: the B1 posterior after the B1 temperature. pd1 [4]: the D1 posterior after the
    D1 temperature (joint form). Returns the option marginals [n, 6], the switch probability of each gap, the
    Viterbi options and the document weights."""
    E = np.maximum(Q, P_FLOOR)[:, S_OPT] / hmm["prior"][S_OPT]
    start, trans = hmm["start"], hmm["trans"]
    logE, ls, lt = np.log(E), _log0(start), _log0(trans)
    if form == "free":
        r = forward_backward(E, start, trans)
        path, _ = viterbi(logE, ls, lt)
        return {"marg": r["gamma"] @ OPT_OF_STATE, "switch": r["switch"], "path": [OPTIONS[S_OPT[s]] for s in path],
                "weights": None, "loglik": r["loglik"]}
    res = {k: forward_backward(E, start, trans, D1_MASK[k]) for k in D1_OPTIONS}
    lw = np.array([math.log(max(float(pd1[i]), P_FLOOR)) + res[k]["loglik"] for i, k in enumerate(D1_OPTIONS)])
    if not np.isfinite(lw).any():
        raise ValueError("B2 joint form: no D1 option gives a finite likelihood")
    w = np.exp(lw - lw.max())
    w /= w.sum()
    gamma = sum(w[i] * res[k]["gamma"] for i, k in enumerate(D1_OPTIONS))
    sw = sum(w[i] * res[k]["switch"] for i, k in enumerate(D1_OPTIONS))
    best, best_path = -math.inf, None
    for i, k in enumerate(D1_OPTIONS):
        path, v = viterbi(logE, ls, lt, D1_MASK[k])
        if not math.isfinite(v):
            continue
        fams = {S_LF[s] for s in path if S_LF[s]}
        mult = sum(float(pd1[j]) for j, k2 in enumerate(D1_OPTIONS) if fams <= D1_FAMILIES[k2])
        score = v + math.log(max(mult, P_FLOOR))
        if score > best:
            best, best_path = score, path
    return {"marg": gamma @ OPT_OF_STATE, "switch": np.clip(sw, 0.0, 1.0),
            "path": [OPTIONS[S_OPT[s]] for s in best_path], "weights": w, "loglik": float(lw.max() + math.log(
                np.exp(lw - lw.max()).sum()))}


def temper(P: np.ndarray, T: float) -> np.ndarray:
    L = np.log(np.maximum(P, P_FLOOR)) / T
    return softmax(L)


def switch_gaps(options) -> list[int]:
    """Criteria chapter 2.5: the gap directly before the first block of the new family (gap t = after block t)."""
    lf, out = None, []
    for i, o in enumerate(options):
        f = FAMILY.get(o)
        if f is None:
            continue
        if lf is not None and f != lf:
            out.append(i - 1)
        lf = f
    return out


# ---------------------------------------------------------------- rule view, tiers, verifiers, P17

def rule_view(rule: dict, d1: str | None) -> tuple[list[str], list[str]]:
    """(rule options, rule tiers) of the blocks. For a document with needs_apertus, the variant by_d1 of the D1
    decision d1 (criteria chapter 7.1 item 5); without d1, the plain rule output."""
    if rule["document"]["d1"].get("needs_apertus") and rule.get("by_d1") and d1 is not None:
        v = rule["by_d1"][d1]
        return list(v["options"]), list(v["tiers"])
    return [b["option"] for b in rule["blocks"]], [b["tier"] for b in rule["blocks"]]


def tier_table(ids, rules: dict, refs: dict, ood: set[str]) -> dict:
    """Chapter 2.5 (criteria chapter 8.7): precision of each (tier, option) pair of the plain rule output."""
    pairs: dict[tuple[str, str], dict] = {}
    for d in ids:
        opts, tiers = rule_view(rules[d], None)
        for o, t, r in zip(opts, tiers, refs[d], strict=True):
            p = pairs.setdefault((t, o), {"n": 0, "k": 0, "docs": set(), "n_ood": 0, "k_ood": 0})
            p["n"] += 1
            p["k"] += o == r
            p["docs"].add(d)
            if d in ood:
                p["n_ood"] += 1
                p["k_ood"] += o == r
    rows = []
    for (t, o), p in sorted(pairs.items()):
        prec = p["k"] / p["n"]
        prec_ood = p["k_ood"] / p["n_ood"] if p["n_ood"] else None
        c1 = prec >= CERTAIN_PREC and len(p["docs"]) >= CERTAIN_DOCS
        c2 = prec_ood is not None and prec_ood >= CERTAIN_PREC
        rows.append({"tier": t, "option": o, "blocks": p["n"], "correct": p["k"], "documents": len(p["docs"]),
                     "precision": r6(prec), "blocks_out_of_design": p["n_ood"], "correct_out_of_design": p["k_ood"],
                     "precision_out_of_design": r6(prec_ood), "jeffreys_mean": r6((p["k"] + 0.5) / (p["n"] + 1)),
                     "condition_1": c1, "condition_2": c2, "certain": c1 and c2,
                     "calibration_id": tier_cal_id(t, o)})
    return {"rule": "criteria chapter 8.7; plain rule output of daten/gj/rules", "documents": len(list(ids)),
            "pairs": rows, "certain_pairs": [[r["tier"], r["option"]] for r in rows if r["certain"]]}


def floor_table_check(tiers: dict) -> dict:
    """Information: the tier table of the floor converter (src/m10_calibrate.py, certainty_dev.json) against this
    table. Equal only for a run on all dev documents."""
    if not FLOOR_CERTAINTY.is_file():
        return {"file": None}
    x = read_json(FLOOR_CERTAINTY)
    rows = {f"{r['tier']}|{r['option']}": r for r in x.get("certainty_table") or []}
    diff = []
    for r in tiers["pairs"]:
        o = rows.get(f"{r['tier']}|{r['option']}") or {}
        if tuple(o.get(k) for k in ("dev_blocks", "dev_correct", "dev_documents", "ood_blocks", "ood_correct",
                                    "certain")) != (r["blocks"], r["correct"], r["documents"], r["blocks_out_of_design"],
                                                    r["correct_out_of_design"], r["certain"]):
            diff.append(f"{r['tier']}|{r['option']}")
    mine = sorted(f"{a}|{b}" for a, b in tiers["certain_pairs"])
    return {"file": rel(FLOOR_CERTAINTY), "sha256": sha256_file(FLOOR_CERTAINTY),
            "pairs_equal": not diff and len(rows) == len(tiers["pairs"]),
            "certain_pairs_equal": mine == sorted(x.get("certain_pairs") or []), "different_pairs": diff[:20]}


def tier_cal_id(tier: str, option: str) -> str:
    return TIER_CAL_PREFIX + re.sub(r"[^A-Za-z0-9._-]+", "-", f"{tier}-{option}").strip("-")


def fit_platt(p: np.ndarray, y: np.ndarray) -> dict:
    from scipy.optimize import minimize
    x = logit(p)
    yy = np.asarray(y, dtype=np.float64)

    def f(th):
        z = th[0] * x + th[1]
        g = expit(z) - yy
        return float(np.sum(np.logaddexp(0.0, z) - yy * z)), np.array([float(np.sum(g * x)), float(np.sum(g))])

    if len(x) == 0:
        return {"alpha": 1.0, "beta": 0.0, "n": 0, "positives": 0, "fitted": False}
    r = minimize(f, np.array([1.0, 0.0]), jac=True, method="L-BFGS-B", bounds=[(-PLATT_BOUND, PLATT_BOUND)] * 2)
    a, b = float(r.x[0]), float(r.x[1])
    return {"alpha": a, "beta": b, "n": int(len(x)), "positives": int(yy.sum()), "fitted": True,
            "nll_mean": float(r.fun) / len(x), "converged": bool(r.success),
            "bound_active": bool(max(abs(a), abs(b)) >= PLATT_BOUND - 1e-9)}


def platt(p, par: dict):
    return expit(par["alpha"] * logit(p) + par["beta"])


def p17(p: np.ndarray, correct: np.ndarray) -> dict:
    """Criteria chapter 8.6 (P17) on the written probabilities after the clip."""
    p = clip(np.asarray(p, dtype=np.float64))
    correct = np.asarray(correct, dtype=bool)
    N = len(p)
    rows, a_ok = [], None
    for a in A_GRID:
        m = p >= a
        n = int(m.sum())
        cov = n / N if N else 0.0
        acc = float(correct[m].mean()) if n else None
        ok = acc is not None and acc >= P17_ACC and cov >= P17_COV
        rows.append({"a": a, "n": n, "coverage": r6(cov), "accuracy": r6(acc), "meets": ok})
        if ok and a_ok is None:
            a_ok = a
    return {"a": a_ok, "units": N, "rows": rows}


# ---------------------------------------------------------------- measures (criteria chapter 6.2; information)

def _bins(conf: np.ndarray) -> np.ndarray:
    return np.minimum((conf * ECE_BINS).astype(np.int64), ECE_BINS - 1)


def ece_top(conf: np.ndarray, corr: np.ndarray) -> float:
    if not len(conf):
        return float("nan")
    b = _bins(conf)
    n = np.bincount(b, minlength=ECE_BINS)
    sc = np.bincount(b, weights=corr.astype(np.float64), minlength=ECE_BINS)
    sq = np.bincount(b, weights=conf, minlength=ECE_BINS)
    return float(np.abs(sc - sq).sum() / len(conf))


def measures(P: np.ndarray, y: np.ndarray, groups: np.ndarray | None = None, boot: bool = False) -> dict:
    """All values after the clip to [0.005, 0.995] without a new sum (criteria chapters 6.2 and 8.5)."""
    P = clip(np.asarray(P, dtype=np.float64))
    y = np.asarray(y, dtype=np.int64)
    N, K = P.shape
    if N == 0:
        return {"n": 0}
    top = P.argmax(1)
    conf = P[np.arange(N), top]
    corr = top == y
    Y = np.zeros_like(P)
    Y[np.arange(N), y] = 1.0
    order = np.argsort(conf, kind="mergesort")
    em = 0.0
    for part in np.array_split(order, ECE_BINS):
        if len(part):
            em += len(part) / N * abs(float(corr[part].mean()) - float(conf[part].mean()))
    cw = []
    for c in range(K):
        q = P[:, c]
        b = _bins(q)
        n = np.bincount(b, minlength=ECE_BINS)
        s = np.bincount(b, weights=Y[:, c], minlength=ECE_BINS)
        m = np.bincount(b, weights=q, minlength=ECE_BINS)
        cw.append(float(np.abs(s - m).sum() / N))
    b = _bins(conf)
    rel_rows = []
    for i in range(ECE_BINS):
        m = b == i
        if m.any():
            rel_rows.append({"bin": i + 1, "n": int(m.sum()), "mean_max_q": r6(conf[m].mean()),
                             "accuracy": r6(corr[m].mean())})
    cov = []
    for a in A_GRID:
        m = conf >= a
        cov.append({"a": a, "coverage": r6(m.mean()), "error": r6(1 - corr[m].mean()) if m.any() else None})
    out = {"n": int(N), "accuracy": r6(corr.mean()), "ece": r6(ece_top(conf, corr)), "ece_equal_mass": r6(em),
           "classwise_ece": r6(np.mean(cw)), "brier": r6(((P - Y) ** 2).sum(1).mean()),
           "nll": r6(-np.log(P[np.arange(N), y]).mean()), "wrong_with_max_q_0_99": int(((conf >= 0.99) & ~corr).sum()),
           "reliability": rel_rows, "coverage_error": cov}
    if boot and groups is not None:
        out.update(boot_ece(conf, corr, groups))
    return out


def boot_ece(conf: np.ndarray, corr: np.ndarray, groups: np.ndarray) -> dict:
    """Document bootstrap of the ECE (criteria chapter 6.3): 2,000 resamples, seed 20261013."""
    g = np.unique(groups, return_inverse=True)[1]
    G = int(g.max()) + 1
    b = _bins(conf)
    cell = g * ECE_BINS + b
    n = np.bincount(cell, minlength=G * ECE_BINS).reshape(G, ECE_BINS)
    sc = np.bincount(cell, weights=corr.astype(np.float64), minlength=G * ECE_BINS).reshape(G, ECE_BINS)
    sq = np.bincount(cell, weights=conf, minlength=G * ECE_BINS).reshape(G, ECE_BINS)
    rng = np.random.default_rng(BOOT_SEED)
    draw = rng.integers(0, G, size=(BOOT_N, G))
    cnt = np.zeros((BOOT_N, G))
    for i in range(BOOT_N):
        cnt[i] = np.bincount(draw[i], minlength=G)
    N = cnt @ n
    vals = np.abs(cnt @ sc - cnt @ sq).sum(1) / N.sum(1)
    return {"ece_low": r6(np.quantile(vals, 0.05)), "ece_high": r6(np.quantile(vals, 0.95)),
            "interval_method": f"document bootstrap, {BOOT_N} resamples, seed {BOOT_SEED}, 5 % and 95 % quantiles"}


def binary(p) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    return np.stack([p, 1 - p], 1)


def written_measures(p: np.ndarray, correct: np.ndarray, groups=None) -> dict:
    """Calibration of the written labels (as GJ.13): the bins use p of the written option (not the top label of
    (p, 1 - p)); a unit is correct if the written option is the reference option. Brier and NLL of q = (p, 1 - p)."""
    p = clip(np.asarray(p, dtype=np.float64))
    c = np.asarray(correct, dtype=bool)
    N = len(p)
    if N == 0:
        return {"n": 0}
    cf = c.astype(np.float64)
    order = np.argsort(p, kind="mergesort")
    em = sum(len(part) / N * abs(float(cf[part].mean()) - float(p[part].mean()))
             for part in np.array_split(order, ECE_BINS) if len(part))
    b = _bins(p)
    rel_rows = [{"bin": i + 1, "n": int((b == i).sum()), "mean_p": r6(p[b == i].mean()),
                 "accuracy": r6(cf[b == i].mean())} for i in range(ECE_BINS) if (b == i).any()]
    cov = [{"a": a, "coverage": r6((p >= a).mean()), "error": r6(1 - cf[p >= a].mean()) if (p >= a).any() else None}
           for a in A_GRID]
    out = {"n": int(N), "accuracy": r6(cf.mean()), "ece": r6(ece_top(p, c)), "ece_equal_mass": r6(em),
           "brier": r6((2 * (p - cf) ** 2).mean()), "nll": r6(-(cf * np.log(p) + (1 - cf) * np.log(1 - p)).mean()),
           "wrong_with_p_0_99": int(((p >= 0.99) & ~c).sum()), "reliability": rel_rows, "coverage_error": cov,
           "bins": "p of the written option"}
    if groups is not None:
        out.update(boot_ece(p, c, np.asarray(groups)))
    return out


# ---------------------------------------------------------------- frozen files, code

def frozen_files() -> dict:
    """FROZEN_FILES of src/m05_gate3a_v4_measure.py (read as text, no import) against the files now."""
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
    now_sha = {p: (sha256_file(ROOT / p) if (ROOT / p).exists() else None) for p in frozen}
    diff = sorted(p for p, h in frozen.items() if now_sha[p] != h)
    return {"source": rel(MEASURE_SCRIPT), "source_sha256": sha256_file(MEASURE_SCRIPT), "files": len(frozen),
            "different": diff, "sha256": now_sha}


def m10_code() -> dict:
    return {rel(p): sha256_file(p) for p in sorted((ROOT / "src").glob("m10_*")) if p.is_file()}


# ---------------------------------------------------------------- the design run

def _log(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


def run_design(states_dir: Path, out: Path, ids: list[str] | None = None, synthetic: bool = False,
               expect_template: str | None = None, quiet: bool = False) -> dict:
    """Chapter 2 on the dev documents. Writes the outputs of chapter 4 to out."""
    log = (lambda m: None) if quiet else _log
    t_start = time.perf_counter()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sets = load_sets()
    all_dev = [str(d) for d in sets["dev"]]
    if ids is None:
        ids = all_dev
    elif not synthetic:
        raise DesignRefusal("a subset of the dev documents needs --synthetic (the real design uses all dev documents)")
    ids = sorted({str(d) for d in ids}, key=int)
    assert_fit_ids(ids, sets)                      # GJ.10 before any other read
    if (out / "design.json").exists() or (out / "run_design.events.jsonl").exists():
        raise DesignRefusal(f"{rel(out)} holds an earlier design run; use a new --out folder (the records stay)")
    tpl = read_json(JOB_TEMPLATE)
    expect_template = expect_template or tpl["sha256"]
    # ---- run record and SHA-256 before the first out-of-fold value (GJ.2)
    ev = Events(out / "run_design.events.jsonl")
    script_sha = sha256_file(SCRIPT)
    rec = {"version": VERSION, "status": STATUS, "synthetic": synthetic, "started": now(),
           "script": {"path": rel(SCRIPT), "sha256": script_sha},
           "modules": {rel(Path(guard.__file__)): sha256_file(guard.__file__),
                       rel(Path(docs.__file__)): sha256_file(docs.__file__)},
           "fixed_design": fixed_design(), "state": "the script SHA-256 is recorded; no out-of-fold value exists"}
    write_json(out / "run_design.json", rec)
    rec["script_sha256_recorded"] = ev.add("script_sha256", sha256=script_sha, path=rel(SCRIPT))
    write_json(out / "run_design.json", rec)
    log(f"script SHA-256 {script_sha} recorded in {rel(out / 'run_design.json')}")
    # ---- inputs, guard, folds
    ood = {str(d) for d in sets["dev_out_of_design"]} & set(ids)
    bk = body_keys(ids)
    folds = make_folds(ids, bk)
    fold_files = write_folds(folds, out)
    data = assemble(states_dir, ids, sets, expect_template)
    labels = {d: load_label(d) for d in ids}
    rules = {d: load_rule(d) for d in ids}
    for d in ids:
        if len(rules[d]["blocks"]) != len(labels[d]["blocks"]):
            raise ValueError(f"{d}: the rule file and the label file have another block count")
    refs = {d: [b["option"] for b in labels[d]["blocks"]] for d in ids}
    ref_d1 = {d: labels[d]["d1"] for d in ids}
    inputs = {rel(SETS): sha256_file(SETS), rel(POOL_CSV): sha256_file(POOL_CSV),
              rel(GROUPS_CSV): sha256_file(GROUPS_CSV), rel(JOB_TEMPLATE): sha256_file(JOB_TEMPLATE),
              rel(CRITERIA): sha256_file(CRITERIA)}
    lab_sha = {rel(LABELS / f"{d}.json"): sha256_file(LABELS / f"{d}.json") for d in ids}
    rule_sha = {rel(RULES / f"{d}.json"): sha256_file(RULES / f"{d}.json") for d in ids}
    doc_sha = {rel(docs.doc_path(d)): sha256_file(docs.doc_path(d)) for d in ids}
    rec.update({"states": {"folder": rel(states_dir), **{k: v for k, v in data.meta.items() if k != "guard"},
                           "documents_with_states": len(data.ids), "documents_without_states": data.missing},
                "guard": data.meta["guard"], "inputs": inputs,
                "inputs_digest": {"labels": digest_lines(lab_sha), "rules": digest_lines(rule_sha),
                                  "docs": digest_lines(doc_sha)},
                "input_files": {**lab_sha, **rule_sha, **doc_sha},
                "criteria_sha256_equal": inputs[rel(CRITERIA)] == CRITERIA_SHA,
                "template": {"expected": expect_template, "T0": T0, "job_template_sha256_value": tpl["sha256"]},
                "documents": {"dev": len(ids), "dev_out_of_design": len(ood), "with_states": len(data.ids)}})
    write_json(out / "run_design.json", rec)
    fold_doc = np.array([folds["fold_of_doc"][d] for d in data.ids])
    fold_blk = fold_doc[data.bdoc]
    # ---- D1 head (first out-of-fold value)
    ev.add("first_out_of_fold_value", what="D1 grid")
    rec["first_out_of_fold_value"] = ev.times["first_out_of_fold_value"]
    log(f"D1 grid: {len(data.ids)} documents, {len(LAYERS)} layers x {len(C_GRID)} values of C")
    g1 = cv_grid(data.xd, data.yd, 4, fold_doc, "D1", log)
    li1, ci1 = choose(g1["nll"])
    t1 = fit_temperature(g1["oof"][li1, ci1], data.yd)
    pd1_oof = softmax(g1["oof"][li1, ci1] / t1["T"])
    log(f"D1 choice: layer {LAYERS[li1]}, C {C_GRID[ci1]}, T {t1['T']:.4f}")
    # ---- B1 head
    log(f"B1 grid: {len(data.yb)} blocks")
    gb = cv_grid(data.xb, data.yb, 6, fold_blk, "B1", log)
    lib, cib = choose(gb["nll"])
    tb = fit_temperature(gb["oof"][lib, cib], data.yb)
    qb_oof = softmax(gb["oof"][lib, cib] / tb["T"])
    log(f"B1 choice: layer {LAYERS[lib]}, C {C_GRID[cib]}, T {tb['T']:.4f}")
    # ---- B2 out-of-fold
    fold_hmm = {}
    for f in sorted(set(fold_doc.tolist())):
        train_docs = [d for d in ids if folds["fold_of_doc"][d] != f]
        fold_hmm[f] = hmm_fit([refs[d] for d in train_docs])
    b2 = {"free": {}, "joint": {}}
    for i, d in enumerate(data.ids):
        a, e = data.offsets[d]
        h = fold_hmm[int(fold_doc[i])]
        for form in ("free", "joint"):
            b2[form][d] = b2_document(qb_oof[a:e], h, form, pd1_oof[i])
    nll_form = {form: nll_probs(np.concatenate([b2[form][d]["marg"] for d in data.ids]), data.yb)
                for form in ("free", "joint")}
    form = "joint" if nll_form["joint"] < nll_form["free"] - TIE_NLL else "free"
    marg_oof = np.concatenate([b2[form][d]["marg"] for d in data.ids])
    t2 = fit_temperature(np.log(np.maximum(marg_oof, P_FLOOR)), data.yb)
    marg2_oof = temper(marg_oof, t2["T"])
    log(f"B2 form: {form} (NLL free {nll_form['free']:.4f}, joint {nll_form['joint']:.4f}), T2 {t2['T']:.4f}")
    # ---- final fits on all dev units
    hd1 = final_head(data.xd, data.yd, 4, li1, C_GRID[ci1])
    hb1 = final_head(data.xb, data.yb, 6, lib, C_GRID[cib])
    hmm_all = hmm_fit([refs[d] for d in ids])
    # ---- rule tiers, views, certain blocks
    tiers = tier_table(ids, rules, refs, ood)
    tiers["floor_table_check"] = floor_table_check(tiers)
    certain = {tuple(x) for x in tiers["certain_pairs"]}
    jeff = {(r["tier"], r["option"]): r["jeffreys_mean"] for r in tiers["pairs"]}
    view, cert_mask = {}, {}
    for i, d in enumerate(data.ids):
        d1_head = D1_OPTIONS[int(pd1_oof[i].argmax())]
        r1 = bool(rules[d]["document"]["d1"].get("needs_apertus"))
        view[d] = rule_view(rules[d], d1_head if r1 else None)
        cert_mask[d] = np.array([(t, o) in certain for o, t in zip(*view[d])], dtype=bool)
    # ---- verifiers (fit set: dev_out_of_design with states)
    ood_have = [i for i, d in enumerate(data.ids) if d in ood]
    s1_opt = {d: rules[d]["document"]["d1"]["option"] for d in ids}
    pv = np.array([pd1_oof[i][D1_OPTIONS.index(s1_opt[data.ids[i]])] for i in ood_have])
    yv = np.array([s1_opt[data.ids[i]] == ref_d1[data.ids[i]] for i in ood_have])
    ver_d1 = fit_platt(pv, yv)
    pb, ybv = [], []
    for i in ood_have:
        d = data.ids[i]
        a, _ = data.offsets[d]
        for j, (o, _t) in enumerate(zip(*view[d])):
            if not cert_mask[d][j]:
                pb.append(marg2_oof[a + j, OPTIONS.index(o)])
                ybv.append(o == refs[d][j])
    ver_b2 = fit_platt(np.array(pb), np.array(ybv))
    # ---- written values of each variant (P17, LoRA trigger, measures)
    wv = written_values(data, ids, rules, refs, ref_d1, pd1_oof, marg2_oof, b2[form], view, cert_mask, jeff,
                        ver_d1, ver_b2, ood)
    thresholds = {kind: {var: p17(v["p"], v["correct"]) for var, v in vs.items()} for kind, vs in wv["p17"].items()}
    ece_b2 = measures(marg2_oof, data.yb)["ece"]
    acc_b2_ood = wv["lora"]["b2_correct"].mean() if len(wv["lora"]["b2_correct"]) else None
    acc_rule_ood = wv["lora"]["rule_correct"].mean() if len(wv["lora"]["rule_correct"]) else None
    c1 = acc_b2_ood is not None and acc_rule_ood is not None and acc_b2_ood <= acc_rule_ood
    c2 = ece_b2 is not None and ece_b2 > LORA_ECE
    lora = {"rule": "criteria chapter 7.3 item 1", "made": now(),
            "condition_1": {"units": int(len(wv["lora"]["b2_correct"])), "accuracy_b1_b2": r6(acc_b2_ood),
                            "accuracy_rules": r6(acc_rule_ood), "met": bool(c1),
                            "text": "non-certain blocks of dev_out_of_design: B1 and B2 not more than the rules"},
            "condition_2": {"units": int(len(data.yb)), "ece_b2_after_temperature": ece_b2, "limit": LORA_ECE,
                            "met": bool(c2), "text": "ECE of the B2 block marginals after T2 on all dev blocks > 0.05"},
            "b1_l_starts": bool(c1 or c2)}
    # ---- measures (information)
    grp_b = np.array(data.ids)[data.bdoc]
    grp_d = np.array(data.ids)
    info = {
        "d1_head_before_t": measures(softmax(g1["oof"][li1, ci1]), data.yd),
        "d1_head_after_t": measures(pd1_oof, data.yd, grp_d, boot=True),
        "b1_head_before_t": measures(softmax(gb["oof"][lib, cib]), data.yb),
        "b1_head_after_t": measures(qb_oof, data.yb, grp_b, boot=True),
        "b2_marginals_before_t2": measures(marg_oof, data.yb),
        "b2_marginals_after_t2": measures(marg2_oof, data.yb, grp_b, boot=True),
        "b2_other_form_before_t2": measures(np.concatenate([b2["joint" if form == "free" else "free"][d]["marg"]
                                                            for d in data.ids]), data.yb),
        "switch_all_gaps": measures(binary(wv["gaps"]["p"]), np.where(wv["gaps"]["ref"], 0, 1), wv["gaps"]["doc"],
                                    boot=True),
        "written": {k: written_measures(v["p"], v["correct"], v["doc"]) for k, v in wv["written"].items()},
        "accuracy": wv["accuracy"],
        "verifier_d1_in_sample": written_measures(platt(pv, ver_d1), yv) if len(pv) else None,
        "verifier_b2_in_sample": written_measures(platt(np.array(pb), ver_b2), np.array(ybv)) if pb else None,
    }
    # ---- write the outputs
    outputs = dict(fold_files)
    heads = out / "heads"
    outputs[rel(heads / "d1_head.npz")] = write_npz(
        heads / "d1_head.npz", classes=np.array(D1_OPTIONS), layer=np.int64(LAYERS[li1]), C=np.float64(C_GRID[ci1]),
        T=np.float64(t1["T"]), mu=hd1["mu"], sd=hd1["sd"], W=hd1["W"], b=hd1["b"], n_train=np.int64(len(data.yd)),
        template_sha256=np.array(expect_template), version=np.array(VERSION), synthetic=np.bool_(synthetic))
    outputs[rel(heads / "b1_head.npz")] = write_npz(
        heads / "b1_head.npz", classes=np.array(OPTIONS), layer=np.int64(LAYERS[lib]), C=np.float64(C_GRID[cib]),
        T=np.float64(tb["T"]), mu=hb1["mu"], sd=hb1["sd"], W=hb1["W"], b=hb1["b"], n_train=np.int64(len(data.yb)),
        template_sha256=np.array(expect_template), version=np.array(VERSION), synthetic=np.bool_(synthetic))
    hmm_doc = {"version": VERSION, "synthetic": synthetic, "form": form, "T2": t2["T"],
               "states": [list(s) for s in STATES], "options": list(OPTIONS),
               "start": hmm_all["start"].tolist(), "trans": hmm_all["trans"].tolist(), "prior": hmm_all["prior"].tolist(),
               "start_counts": hmm_all["start_counts"].tolist(), "trans_counts": hmm_all["trans_counts"].tolist(),
               "option_counts": hmm_all["option_counts"].tolist(), "zero_prior_options": hmm_all["zero_prior_options"],
               "sequences": hmm_all["sequences"], "d1_families": {k: sorted(v) for k, v in D1_FAMILIES.items()},
               "nll_out_of_fold": {k: r6(v) for k, v in nll_form.items()},
               "zero_prior_options_by_fold": {str(f): h["zero_prior_options"] for f, h in fold_hmm.items()}}
    outputs[rel(out / "b2_hmm.json")] = write_json(out / "b2_hmm.json", hmm_doc)
    verif = {"version": VERSION, "synthetic": synthetic,
             "d1": {**ver_d1, "input": "calibrated out-of-fold D1 probability of the S1 rule option",
                    "fit_set": "dev_out_of_design with states", "documents": [data.ids[i] for i in ood_have]},
             "b2": {**ver_b2, "input": "out-of-fold B2 marginal after T2 of the rule option (non-certain blocks)",
                    "fit_set": "non-certain blocks of dev_out_of_design with states"}}
    outputs[rel(out / "verifiers.json")] = write_json(out / "verifiers.json", verif)
    outputs[rel(out / "tier_table.json")] = write_json(out / "tier_table.json", {"version": VERSION, **tiers})
    thr = {"version": VERSION, "synthetic": synthetic, "rule": "criteria chapter 8.6 (P17)", "grid": list(A_GRID),
           "kinds": thresholds}
    outputs[rel(out / "thresholds.json")] = write_json(out / "thresholds.json", thr)
    outputs[rel(out / "lora_trigger.json")] = write_json(out / "lora_trigger.json", {"version": VERSION,
                                                                                     "synthetic": synthetic, **lora})
    oof = out / "oof"
    outputs[rel(oof / "d1_oof.npz")] = write_npz(
        oof / "d1_oof.npz", doc_ids=np.array(data.ids), fold=fold_doc, y=data.yd, layers=np.array(LAYERS),
        C_grid=np.array(C_GRID), logits=g1["oof"], nll=g1["nll"], chosen=np.array([li1, ci1]), T=np.float64(t1["T"]),
        probs_after_t=pd1_oof)
    outputs[rel(oof / "b1_oof.npz")] = write_npz(
        oof / "b1_oof.npz", doc_ids=np.array(data.ids), block_doc=data.bdoc,
        block_ids=np.array([b for d in data.ids for b in data.block_ids[d]]), fold=fold_blk, y=data.yb,
        layers=np.array(LAYERS), C_grid=np.array(C_GRID), logits=gb["oof"], nll=gb["nll"], chosen=np.array([lib, cib]),
        T=np.float64(tb["T"]), probs_after_t=qb_oof)
    outputs[rel(oof / "b2_oof.npz")] = write_npz(
        oof / "b2_oof.npz", doc_ids=np.array(data.ids), block_doc=data.bdoc,
        marg_free=np.concatenate([b2["free"][d]["marg"] for d in data.ids]),
        marg_joint=np.concatenate([b2["joint"][d]["marg"] for d in data.ids]), form=np.array(form),
        T2=np.float64(t2["T"]), marg_after_t2=marg2_oof,
        viterbi=np.array([o for d in data.ids for o in b2[form][d]["path"]]),
        gap_doc=wv["gaps"]["doc"], gap_after=wv["gaps"]["after"], gap_p=wv["gaps"]["p"], gap_ref=wv["gaps"]["ref"])
    cal_records = calibration_records(out, tiers, thresholds, info, ver_d1, ver_b2, t1, tb, t2, form,
                                      (LAYERS[li1], C_GRID[ci1]), (LAYERS[lib], C_GRID[cib]), len(data.ids),
                                      len(data.yb), synthetic, outputs)
    outputs[rel(out / "calibration_records.json")] = write_json(out / "calibration_records.json", cal_records)
    design = {
        "version": VERSION, "status": STATUS, "synthetic": synthetic, "made": now(),
        "script": {"path": rel(SCRIPT), "sha256": script_sha},
        "template_sha256": expect_template,
        "model_fingerprint": data.meta["model_fingerprint"],
        "documents": {"dev": len(ids), "with_states": len(data.ids), "without_states": data.missing,
                      "dev_out_of_design": len(ood), "dev_out_of_design_with_states": len(ood_have),
                      "blocks_with_states": int(len(data.yb))},
        "folds": {k: folds[k] for k in ("n_folds", "documents", "parliaments", "documents_by_fold")},
        "d1": {"layer": LAYERS[li1], "C": C_GRID[ci1], "nll_grid": g1["nll"].round(6).tolist(), **t1,
               "final_fit": {"nit": hd1["nit"], "converged": hd1["converged"]},
               "grid_fits_not_converged": sum(1 for x in g1["fits"] if not x["converged"])},
        "b1": {"layer": LAYERS[lib], "C": C_GRID[cib], "nll_grid": gb["nll"].round(6).tolist(), **tb,
               "final_fit": {"nit": hb1["nit"], "converged": hb1["converged"]},
               "grid_fits_not_converged": sum(1 for x in gb["fits"] if not x["converged"])},
        "b2": {"form": form, "nll_out_of_fold": {k: r6(v) for k, v in nll_form.items()}, **{f"t2_{k}": v
                                                                                             for k, v in t2.items()}},
        "verifiers": {"d1": ver_d1, "b2": ver_b2},
        "certain_pairs": tiers["certain_pairs"], "floor_table_check": tiers["floor_table_check"],
        "thresholds": {kind: {var: v["a"] for var, v in vs.items()} for kind, vs in thresholds.items()},
        "lora_trigger": lora,
        "measures_information": info,
        "grid_fit_seconds": {"d1": round(sum(x["seconds"] for x in g1["fits"]), 1),
                             "b1": round(sum(x["seconds"] for x in gb["fits"]), 1)},
    }
    outputs[rel(out / "design.json")] = write_json(out / "design.json", design)
    md = design_markdown(design, rec, folds, data, tiers, thresholds, hmm_doc, verif, inputs)
    (out / "design_dev.md").write_text(md, encoding="utf-8")
    outputs[rel(out / "design_dev.md")] = sha256_file(out / "design_dev.md")
    rec.update({"finished": ev.add("finished"), "seconds": round(time.perf_counter() - t_start, 1),
                "state": "finished", "outputs": outputs,
                "grid_fits": {"d1": g1["fits"], "b1": gb["fits"]}})
    write_json(out / "run_design.json", rec)
    log(f"design finished in {rec['seconds']} s; outputs in {rel(out)}")
    return design


def fixed_design() -> dict:
    return {"n_folds": N_FOLDS, "layers": list(LAYERS), "C_grid": list(C_GRID), "tie_nll": TIE_NLL,
            "lbfgs_maxiter": LBFGS_MAXITER, "std_floor": STD_FLOOR, "temperature_bounds": [T_MIN, T_MAX],
            "platt_bound": PLATT_BOUND, "a_grid": list(A_GRID), "p17": [P17_ACC, P17_COV],
            "certain": [CERTAIN_PREC, CERTAIN_DOCS], "lora_ece": LORA_ECE, "ece_bins": ECE_BINS,
            "bootstrap": [BOOT_N, BOOT_SEED], "clip": [CLIP_LO, CLIP_HI], "states": [list(s) for s in STATES],
            "units": {"d1": "the D1 suffix of each dev document with states",
                      "b1": "the B1 suffix of each block of each dev document with states (each block has a label)"}}


def written_values(data: DevData, ids, rules, refs, ref_d1, pd1, marg2, b2f, view, cert_mask, jeff, ver_d1,
                   ver_b2, ood) -> dict:
    """The written probability and the correctness of each label of each variant (chapter 2.7)."""
    p17v = {"document_text_parts": {"d1_entered": {"p": [], "correct": []},
                                    "d1_not_entered": {"p": [], "correct": []}},
            "block_slot": {"b12_entered": {"p": [], "correct": []}, "b12_not_entered": {"p": [], "correct": []}},
            "author_switch": {"b12_entered": {"p": [], "correct": []}, "b12_not_entered": {"p": [], "correct": []}}}
    written = {k: {"p": [], "correct": [], "doc": []} for k in
               ("d1_head", "d1_verifier", "block_b12_entered", "block_b12_not_entered",
                "block_b2_noncertain", "block_verifier_noncertain", "block_certain_tier",
                "switch_b12_entered", "switch_b12_not_entered")}
    gaps = {"doc": [], "after": [], "p": [], "ref": []}
    lora = {"b2_correct": [], "rule_correct": []}
    acc = Counter()
    for i, d in enumerate(data.ids):
        a, _ = data.offsets[d]
        r1 = bool(rules[d]["document"]["d1"].get("needs_apertus"))
        k = int(pd1[i].argmax())
        ph, ch = float(pd1[i][k]), D1_OPTIONS[k] == ref_d1[d]
        s1 = rules[d]["document"]["d1"]["option"]
        pv, cv = float(platt(pd1[i][D1_OPTIONS.index(s1)], ver_d1)), s1 == ref_d1[d]
        p17v["document_text_parts"]["d1_entered"]["p"].append(ph)
        p17v["document_text_parts"]["d1_entered"]["correct"].append(ch)
        p17v["document_text_parts"]["d1_not_entered"]["p"].append(ph if r1 else pv)
        p17v["document_text_parts"]["d1_not_entered"]["correct"].append(ch if r1 else cv)
        for key, p, c in (("d1_head", ph, ch), ("d1_verifier", pv, cv)):
            if key == "d1_head" or not r1:
                written[key]["p"].append(p)
                written[key]["correct"].append(c)
                written[key]["doc"].append(d)
        acc["d1_head_correct"] += ch
        acc["d1_s1_rule_correct"] += cv
        acc["d1_documents"] += 1
        ropt, _rt = view[d]
        path = b2f[d]["path"]
        ref = refs[d]
        cm = cert_mask[d]
        dec_b12, dec_rule = [], []
        for j in range(len(ref)):
            o_r = ropt[j]
            if cm[j]:
                p = float(jeff[(view[d][1][j], o_r)])
                for key in ("b12_entered", "b12_not_entered"):
                    p17v["block_slot"][key]["p"].append(p)
                    p17v["block_slot"][key]["correct"].append(o_r == ref[j])
                for key in ("block_b12_entered", "block_b12_not_entered", "block_certain_tier"):
                    written[key]["p"].append(p)
                    written[key]["correct"].append(o_r == ref[j])
                    written[key]["doc"].append(d)
                dec_b12.append(o_r)
                dec_rule.append(o_r)
                acc["certain_blocks"] += 1
                acc["certain_correct"] += o_r == ref[j]
                continue
            o_v = path[j]
            p_v = float(marg2[a + j, OPTIONS.index(o_v)])
            p_r = float(platt(marg2[a + j, OPTIONS.index(o_r)], ver_b2))
            for key, p, c in (("b12_entered", p_v, o_v == ref[j]), ("b12_not_entered", p_r, o_r == ref[j])):
                p17v["block_slot"][key]["p"].append(p)
                p17v["block_slot"][key]["correct"].append(c)
            for key, p, c in (("block_b12_entered", p_v, o_v == ref[j]), ("block_b2_noncertain", p_v, o_v == ref[j]),
                              ("block_b12_not_entered", p_r, o_r == ref[j]),
                              ("block_verifier_noncertain", p_r, o_r == ref[j])):
                written[key]["p"].append(p)
                written[key]["correct"].append(c)
                written[key]["doc"].append(d)
            acc["noncertain_blocks"] += 1
            acc["noncertain_b2_correct"] += o_v == ref[j]
            acc["noncertain_rule_correct"] += o_r == ref[j]
            acc["noncertain_marginal_argmax_correct"] += int(np.argmax(marg2[a + j])) == OPTIONS.index(ref[j])
            if d in ood:
                lora["b2_correct"].append(o_v == ref[j])
                lora["rule_correct"].append(o_r == ref[j])
            dec_b12.append(o_v)
            dec_rule.append(o_r)
        sw = b2f[d]["switch"]
        ref_gaps = set(switch_gaps(ref))
        for t in range(len(ref) - 1):
            gaps["doc"].append(d)
            gaps["after"].append(t)
            gaps["p"].append(float(sw[t]))
            gaps["ref"].append(t in ref_gaps)
        for key, dec in (("b12_entered", dec_b12), ("b12_not_entered", dec_rule)):
            for t in switch_gaps(dec):
                p17v["author_switch"][key]["p"].append(float(sw[t]))
                p17v["author_switch"][key]["correct"].append(t in ref_gaps)
                written[f"switch_{key}"]["p"].append(float(sw[t]))
                written[f"switch_{key}"]["correct"].append(t in ref_gaps)
                written[f"switch_{key}"]["doc"].append(d)
    for kind in p17v.values():
        for v in kind.values():
            v["p"], v["correct"] = np.array(v["p"], dtype=np.float64), np.array(v["correct"], dtype=bool)
    for v in written.values():
        v["p"], v["correct"], v["doc"] = (np.array(v["p"], dtype=np.float64), np.array(v["correct"], dtype=bool),
                                          np.array(v["doc"]))
    accuracy = {"d1_head": r6(acc["d1_head_correct"] / max(acc["d1_documents"], 1)),
                "d1_s1_rule": r6(acc["d1_s1_rule_correct"] / max(acc["d1_documents"], 1)),
                "documents": acc["d1_documents"], "certain_blocks": acc["certain_blocks"],
                "certain_precision": r6(acc["certain_correct"] / acc["certain_blocks"]) if acc["certain_blocks"] else None,
                "noncertain_blocks": acc["noncertain_blocks"],
                "noncertain_b2_viterbi": r6(acc["noncertain_b2_correct"] / max(acc["noncertain_blocks"], 1)),
                "noncertain_b2_marginal_argmax": r6(acc["noncertain_marginal_argmax_correct"]
                                                    / max(acc["noncertain_blocks"], 1)),
                "noncertain_rule_view": r6(acc["noncertain_rule_correct"] / max(acc["noncertain_blocks"], 1))}
    return {"p17": p17v, "written": written, "accuracy": accuracy,
            "gaps": {"doc": np.array(gaps["doc"]), "after": np.array(gaps["after"], dtype=np.int64),
                     "p": np.array(gaps["p"], dtype=np.float64), "ref": np.array(gaps["ref"], dtype=bool)},
            "lora": {k: np.array(v, dtype=bool) for k, v in lora.items()}}


# ---------------------------------------------------------------- calibration records (label schema class Calibration)

def _ms(name: str, m: dict | None) -> list[dict]:
    if not m or not m.get("n"):
        return []
    x = {"set_name": name, "set_n": m["n"]}
    for k in ("ece", "ece_equal_mass", "classwise_ece", "brier", "nll", "ece_low", "ece_high", "interval_method"):
        if m.get(k) is not None:
            x[k] = m[k]
    return [x]


def _params(**kw) -> list[dict]:
    return [{"parameter_name": k, "parameter_value": float(v)} for k, v in kw.items()]


def calibration_records(out: Path, tiers: dict, thresholds: dict, info: dict, ver_d1: dict, ver_b2: dict, t1: dict,
                        tb: dict, t2: dict, form: str, d1_choice, b1_choice, n_docs: int, n_blocks: int,
                        synthetic: bool, outputs: dict) -> dict:
    """Templates of the calibration records; certain_threshold for each variant (apply chooses one variant)."""
    def fit(p: str) -> dict:
        return {"fit_set_file": p, "fit_set_digest": outputs[p]}
    o = rel(out / "oof")
    note = "synthetic states for a code check: not a result. " if synthetic else ""
    th = {kind: {var: v["a"] for var, v in vs.items()} for kind, vs in thresholds.items()}
    rec = {
        CAL["d1_head"]: {"calibration_method": "temperature_scaling", "calibrated_kind": "document_text_parts",
                         **fit(f"{o}/d1_oof.npz"), "fit_n": n_docs, "reference_source": REFERENCE,
                         "in_sample": False, "target_status": "not_measured",
                         "calibration_parameters": _params(temperature=t1["T"], layer=d1_choice[0], C=d1_choice[1]),
                         "measure_sets": _ms("dev out-of-fold", info["d1_head_after_t"]),
                         "calibration_note": note + "D1 head (L2 multinomial logistic regression), one temperature "
                                                    "on the pooled out-of-fold logits of dev"},
        CAL["d1_verifier"]: {"calibration_method": "verifier_platt", "calibrated_kind": "document_text_parts",
                             **fit(rel(out / "verifiers.json")), "fit_n": ver_d1["n"], "reference_source": REFERENCE,
                             "in_sample": False, "target_status": "not_measured",
                             "calibration_parameters": _params(alpha=ver_d1["alpha"], beta=ver_d1["beta"]),
                             "measure_sets": _ms("dev_out_of_design, in-sample", info["verifier_d1_in_sample"]),
                             "calibration_note": note + "Platt map of the calibrated D1 probability of the S1 rule "
                                                        "option; fit set dev_out_of_design"},
        CAL["b2_marginal"]: {"calibration_method": "forward_backward_temperature", "calibrated_kind": "block_slot",
                             **fit(f"{o}/b2_oof.npz"), "fit_n": n_blocks, "reference_source": REFERENCE,
                             "in_sample": False, "target_status": "not_measured",
                             "calibration_parameters": _params(temperature_b2=t2["T"], temperature_b1=tb["T"],
                                                               layer=b1_choice[0], C=b1_choice[1]),
                             "measure_sets": _ms("dev out-of-fold", info["b2_marginals_after_t2"]),
                             "calibration_note": note + f"B2 block marginal of the {form} form (b2_hmm.json) "
                                                        "after the B1 temperature and one B2 temperature"},
        CAL["b2_verifier"]: {"calibration_method": "verifier_platt", "calibrated_kind": "block_slot",
                             **fit(rel(out / "verifiers.json")), "fit_n": ver_b2["n"], "reference_source": REFERENCE,
                             "in_sample": False, "target_status": "not_measured",
                             "calibration_parameters": _params(alpha=ver_b2["alpha"], beta=ver_b2["beta"]),
                             "measure_sets": _ms("non-certain blocks of dev_out_of_design, in-sample",
                                                 info["verifier_b2_in_sample"]),
                             "calibration_note": note + "Platt map of the B2 marginal of the rule option; fit set: "
                                                        "the non-certain blocks of dev_out_of_design"},
        CAL["b2_switch"]: {"calibration_method": "forward_backward_temperature", "calibrated_kind": "author_switch",
                           **fit(f"{o}/b2_oof.npz"), "fit_n": int(info["switch_all_gaps"]["n"]),
                           "reference_source": REFERENCE, "in_sample": False, "target_status": "not_measured",
                           "calibration_parameters": _params(temperature_b1=tb["T"]),
                           "measure_sets": _ms("dev out-of-fold, all gaps", info["switch_all_gaps"]),
                           "calibration_note": note + "pairwise forward-backward probability of a switch at the gap, "
                                                      "with the B1 temperature; the B2 temperature is not applied"},
    }
    for r in tiers["pairs"]:
        if not r["certain"]:
            continue
        rec[r["calibration_id"]] = {
            "calibration_method": "jeffreys_tier_precision", "calibrated_kind": "block_slot",
            **fit(rel(out / "tier_table.json")), "fit_n": r["blocks"], "reference_source": REFERENCE,
            "in_sample": True, "target_status": "not_measured",
            "calibration_parameters": _params(jeffreys_mean=r["jeffreys_mean"], precision=r["precision"],
                                              blocks=r["blocks"], documents=r["documents"]),
            "calibration_note": note + f"rule tier {r['tier']} with the option {r['option']}: Jeffreys posterior "
                                       "mean of the dev precision (criteria chapter 8.7)"}
    kind_of = {CAL["d1_head"]: "document_text_parts", CAL["d1_verifier"]: "document_text_parts",
               CAL["b2_marginal"]: "block_slot", CAL["b2_verifier"]: "block_slot", CAL["b2_switch"]: "author_switch"}
    kind_of.update({r["calibration_id"]: "block_slot" for r in tiers["pairs"] if r["certain"]})
    return {"version": VERSION, "synthetic": synthetic, "status": STATUS, "records": rec, "kind_of": kind_of,
            "thresholds": th,
            "variant_keys": {"document_text_parts": {"yes": "d1_entered", "no": "d1_not_entered"},
                             "block_slot": {"yes": "b12_entered", "no": "b12_not_entered"},
                             "author_switch": {"yes": "b12_entered", "no": "b12_not_entered"}}}


def calibration_file(frozen: "Frozen", entry_d1: bool, entry_b12: bool) -> dict:
    """The calibration file of src/m10_writer.py for one variant of the entry decisions."""
    cr = frozen.records
    out = {}
    for cid, x in cr["records"].items():
        kind = cr["kind_of"][cid]
        entered = entry_d1 if kind == "document_text_parts" else entry_b12
        var = cr["variant_keys"][kind]["yes" if entered else "no"]
        a = cr["thresholds"][kind][var]
        y = dict(x)
        if a is not None:
            y["certain_threshold"] = a
        y["calibration_note"] = (x.get("calibration_note", "") + f". Variant {var}; threshold a by P17 on dev").strip()
        out[cid] = y
    return {"calibrations": out}


# ---------------------------------------------------------------- design_dev.md (English STE)

def _f(x, n=4) -> str:
    if x is None:
        return "–"
    if isinstance(x, float) and math.isnan(x):
        return "–"
    return f"{x + 0.0:.{n}f}".replace("-0.0000", "0.0000") if isinstance(x, float) else str(x)


def _c(x) -> str:
    return f"{x:g}"


def design_markdown(design: dict, rec: dict, folds: dict, data: DevData, tiers: dict, thresholds: dict,
                    hmm_doc: dict, verif: dict, inputs: dict) -> str:
    syn = design["synthetic"]
    L = []
    add = L.append
    add("# Gate GJ: design on `dev` (D1, B1, B2, threshold a, verifier maps, LoRA trigger)")
    add("")
    add(f"Run of {design['made']} (time from the clock). Script `src/m10_design.py`, SHA-256 "
        f"`{design['script']['sha256']}`. Status: EXCEPTION, NOT RELEASED. Actor: workflow sub-agent "
        f"(Claude Opus 5.5), for the main agent. No human checked the content of this file.")
    add("")
    add("Written in English to the STE rules (ASD-STE100, Issue 9).")
    add("")
    if syn:
        add("> Synthetic states for a code check. This file holds no result and no measurement.")
        add("")
    add("## 1 Order of the records")
    add("")
    add(f"1. The script wrote its SHA-256 into `run_design.json` at {rec['script_sha256_recorded']}.")
    add(f"2. The first out-of-fold value came at {rec['first_out_of_fold_value']}.")
    add("3. All values of this file are `dev` values. They are information. Each choice uses out-of-fold values.")
    add("4. This file holds no value of a validation document and no value of a group-7 document.")
    add("5. The folds, the grids, the seeds and the selection rules are constants of the script.")
    add("")
    add("## 2 Inputs")
    add("")
    add("| File | SHA-256 |")
    add("|---|---|")
    for p, h in inputs.items():
        add(f"| `{p}` | `{h}` |")
    for k, v in rec["inputs_digest"].items():
        add(f"| {k} files (digest of the sorted path and SHA-256 lines) | `{v}` |")
    add(f"| states files (digest) | `{rec['states']['states_files_digest']}` |")
    add("")
    st = design["documents"]
    add(f"1. `dev` documents: {st['dev']}. With states: {st['with_states']}. Without states: "
        f"{len(st['without_states'])}.")
    add(f"2. Blocks with states: {st['blocks_with_states']}. Documents of `dev_out_of_design` with states: "
        f"{st['dev_out_of_design_with_states']}.")
    add(f"3. Template SHA-256 of the states: `{design['template_sha256']}`.")
    add(f"4. Criteria file SHA-256 equal to the protocol value: {str(rec['criteria_sha256_equal']).lower()}.")
    add("")
    add("## 3 Folds (criteria chapter 5, items 2 to 4)")
    add("")
    add("| Fold | Parliaments | Documents | Blocks with states |")
    add("|---|---|---|---|")
    fb = Counter()
    for d in data.ids:
        fb[folds["fold_of_doc"][d]] += len(data.block_ids[d])
    for f in range(1, folds["n_folds"] + 1):
        parl = [x["body_key"] for x in folds["parliament_order"] if x["fold"] == f]
        add(f"| {f} | {len(parl)} | {folds['documents_by_fold'][str(f)]} | {fb[f]} |")
    add("")
    add("The file `folds.csv` gives the fold of each document.")
    add("")
    for key, title, K in (("d1", "D1 head", 4), ("b1", "B1 head", 6)):
        h = design[key]
        add(f"## {4 if key == 'd1' else 5} {title} (K = {K})")
        add("")
        add(f"1. Choice: layer {h['layer']}, C {_c(h['C'])}. The pooled out-of-fold NLL is "
            f"{_f(min(min(r) for r in h['nll_grid']))}.")
        add(f"2. Temperature T = {_f(h['T'])}. NLL before T: {_f(h['nll_before'])}. NLL after T: {_f(h['nll_after'])}.")
        add(f"3. Grid fits that did not converge in {LBFGS_MAXITER} iterations: {h['grid_fits_not_converged']}.")
        add("")
        add("Out-of-fold NLL for each layer (rows) and each C (columns):")
        add("")
        add("| Layer | " + " | ".join(_c(c) for c in C_GRID) + " |")
        add("|---|" + "---|" * len(C_GRID))
        for k, row in zip(LAYERS, h["nll_grid"]):
            add(f"| {k} | " + " | ".join(_f(v) for v in row) + " |")
        add("")
        mi = design["measures_information"]
        add(measure_table([("before T", mi[f"{key}_head_before_t"]), ("after T", mi[f"{key}_head_after_t"])]))
        add("")
    b2 = design["b2"]
    add("## 6 Code step B2")
    add("")
    add(f"1. Out-of-fold NLL of the block options: free form {_f(b2['nll_out_of_fold']['free'])}, joint form "
        f"{_f(b2['nll_out_of_fold']['joint'])}.")
    add(f"2. Choice: the {b2['form']} form (proposal P10).")
    add(f"3. B2 temperature T2 = {_f(b2['t2_T'])}. NLL before T2: {_f(b2['t2_nll_before'])}. NLL after T2: "
        f"{_f(b2['t2_nll_after'])}.")
    zp = hmm_doc["zero_prior_options"]
    add(f"4. Options with 0 reference blocks in the prior of the final file: {', '.join(zp) if zp else 'none'}.")
    add("")
    mi = design["measures_information"]
    add(measure_table([("B2 marginals before T2", mi["b2_marginals_before_t2"]),
                       ("B2 marginals after T2", mi["b2_marginals_after_t2"]),
                       ("switch probability, all gaps", mi["switch_all_gaps"])]))
    add("")
    acc = mi["accuracy"]
    add("Accuracy (out-of-fold for the heads and B2; the rule view is the rule output):")
    add("")
    add("| Value | Units | Accuracy |")
    add("|---|---|---|")
    add(f"| D1 head | {acc['documents']} | {_f(acc['d1_head'])} |")
    add(f"| S1 rule option (D1 baseline, information) | {acc['documents']} | {_f(acc['d1_s1_rule'])} |")
    add(f"| Certain blocks (rule tier) | {acc['certain_blocks']} | {_f(acc['certain_precision'])} |")
    add(f"| Non-certain blocks, Viterbi option of B2 | {acc['noncertain_blocks']} | {_f(acc['noncertain_b2_viterbi'])} |")
    add(f"| Non-certain blocks, highest B2 marginal | {acc['noncertain_blocks']} | "
        f"{_f(acc['noncertain_b2_marginal_argmax'])} |")
    add(f"| Non-certain blocks, rule view | {acc['noncertain_blocks']} | {_f(acc['noncertain_rule_view'])} |")
    add("")
    add("Written labels of each variant (the bins use p of the written option, as GJ.13):")
    add("")
    names = {"d1_head": "D1, head", "d1_verifier": "D1, verifier (no R1 documents)",
             "block_b12_entered": "blocks, B1 and B2 enter", "block_b12_not_entered": "blocks, B1 and B2 do not enter",
             "block_b2_noncertain": "non-certain blocks, B2", "block_verifier_noncertain": "non-certain blocks, verifier",
             "block_certain_tier": "certain blocks, rule tier", "switch_b12_entered": "switch, B1 and B2 enter",
             "switch_b12_not_entered": "switch, B1 and B2 do not enter"}
    add(measure_table([(names[k], v) for k, v in mi["written"].items()]))
    add("")
    add("## 7 Rule tiers (criteria chapter 8.7)")
    add("")
    add(f"1. Pairs of rule tier and rule option: {len(tiers['pairs'])}. Certain pairs: {len(tiers['certain_pairs'])}.")
    add("2. The file `tier_table.json` gives each pair with its precision, its document count and its Jeffreys mean.")
    fc = tiers.get("floor_table_check") or {}
    if fc.get("file"):
        add(f"3. Equal to the tier table of the floor converter (`{fc['file']}`): pairs "
            f"{str(fc['pairs_equal']).lower()}, certain pairs {str(fc['certain_pairs_equal']).lower()}.")
    add("")
    if tiers["certain_pairs"]:
        add("| Tier | Option | Blocks | Documents | Precision | Precision out of design | Jeffreys mean |")
        add("|---|---|---|---|---|---|---|")
        for r in tiers["pairs"]:
            if r["certain"]:
                add(f"| `{r['tier']}` | `{r['option']}` | {r['blocks']} | {r['documents']} | {_f(r['precision'])} | "
                    f"{_f(r['precision_out_of_design'])} | {_f(r['jeffreys_mean'])} |")
        add("")
    add("## 8 Verifier maps (criteria chapter 8.4, items 4 and 5)")
    add("")
    add("| Map | Units | Positive units | alpha | beta | A bound is active |")
    add("|---|---|---|---|---|---|")
    for k in ("d1", "b2"):
        v = verif[k]
        add(f"| {k.upper()} verifier | {v['n']} | {v.get('positives', 0)} | {_f(v['alpha'])} | {_f(v['beta'])} | "
            f"{str(v.get('bound_active', False)).lower()} |")
    add("")
    add("## 9 Threshold a (criteria chapter 8.6)")
    add("")
    add("| Label kind | Variant | Units | a |")
    add("|---|---|---|---|")
    for kind, vs in thresholds.items():
        for var, v in vs.items():
            a = "none: each label is unsure" if v["a"] is None else _c(v["a"])
            add(f"| `{kind}` | `{var}` | {v['units']} | {a} |")
    add("")
    add("The file `thresholds.json` gives the coverage and the accuracy for each a.")
    add("")
    lt = design["lora_trigger"]
    add("## 10 LoRA trigger (criteria chapter 7.3, item 1)")
    add("")
    c1, c2 = lt["condition_1"], lt["condition_2"]
    add(f"1. Condition 1: {c1['units']} non-certain blocks of `dev_out_of_design`. B1 and B2 accuracy "
        f"{_f(c1['accuracy_b1_b2'])}, rule accuracy {_f(c1['accuracy_rules'])}. Met: {str(c1['met']).lower()}.")
    add(f"2. Condition 2: ECE of the B2 marginals after T2 on {c2['units']} blocks: {_f(c2['ece_b2_after_temperature'])}. "
        f"Limit: {c2['limit']}. Met: {str(c2['met']).lower()}.")
    add(f"3. Result: B1-L starts: {'yes' if lt['b1_l_starts'] else 'no'}.")
    add("")
    add("## 11 Limits")
    add("")
    add("1. The temperatures, the values a and the choices use the same `dev` out-of-fold values. Thus the `dev` "
        "values are a little too good.")
    add("2. Rule values and verifier values are in-sample values.")
    add("3. The reference is the AI reference. It has no human acceptance.")
    add("4. The switch probability has no temperature of its own.")
    add("")
    return "\n".join(L)


def measure_table(rows) -> str:
    out = ["| Values | n | Accuracy | ECE | ECE 5 % | ECE 95 % | ECE equal mass | Class-wise ECE | Brier | NLL |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for name, m in rows:
        out.append(f"| {name} | {m['n']} | {_f(m.get('accuracy'))} | {_f(m.get('ece'))} | {_f(m.get('ece_low'))} | "
                   f"{_f(m.get('ece_high'))} | {_f(m.get('ece_equal_mass'))} | {_f(m.get('classwise_ece'))} | "
                   f"{_f(m.get('brier'))} | {_f(m.get('nll'))} |")
    return "\n".join(out)


# ---------------------------------------------------------------- frozen design and the cascade mode (apply)

DESIGN_FILES = ("heads/d1_head.npz", "heads/b1_head.npz", "b2_hmm.json", "verifiers.json", "tier_table.json",
                "thresholds.json", "lora_trigger.json", "calibration_records.json", "design.json")


@dataclass
class Frozen:
    design_dir: Path
    d1: dict
    b1: dict
    hmm: dict
    verifiers: dict
    certain: dict          # (tier, option) -> (jeffreys mean, calibration id)
    records: dict
    template_sha256: str
    synthetic: bool
    files: dict
    freeze: dict | None = None
    freeze_path: Path | None = None


def _head(p: Path) -> dict:
    with np.load(p, allow_pickle=False) as z:
        return {"classes": [str(c) for c in z["classes"]], "layer": int(z["layer"]), "C": float(z["C"]),
                "T": float(z["T"]), "mu": np.array(z["mu"]), "sd": np.array(z["sd"]), "W": np.array(z["W"]),
                "b": np.array(z["b"]), "template_sha256": str(z["template_sha256"]), "synthetic": bool(z["synthetic"])}


def load_frozen(design_dir: Path = DESIGN, freeze_file: Path | None = None) -> Frozen:
    design_dir = Path(design_dir)
    files = {f: sha256_file(design_dir / f) for f in DESIGN_FILES}
    fr = None
    if freeze_file is not None:
        fr = read_json(freeze_file)
        if (fr.get("code") or {}).get(rel(SCRIPT)) != sha256_file(SCRIPT):
            raise DesignRefusal(f"src/m10_design.py differs from the code of the freeze file {rel(freeze_file)}")
        want = {Path(k).relative_to(rel(design_dir)).as_posix() if k.startswith(rel(design_dir) + "/") else k: v
                for k, v in (fr.get("design_files") or {}).items()}
        diff = [f for f in DESIGN_FILES if want.get(f) != files[f]]
        if diff:
            raise DesignRefusal(f"the design files differ from the freeze file {rel(freeze_file)}: {diff}")
    d1, b1 = _head(design_dir / "heads/d1_head.npz"), _head(design_dir / "heads/b1_head.npz")
    if d1["classes"] != list(D1_OPTIONS) or b1["classes"] != list(OPTIONS):
        raise ValueError("head classes differ")
    h = read_json(design_dir / "b2_hmm.json")
    if [tuple(s) for s in h["states"]] != list(STATES):
        raise ValueError("HMM states differ")
    hmm = {"start": np.array(h["start"]), "trans": np.array(h["trans"]), "prior": np.array(h["prior"]),
           "form": h["form"], "T2": float(h["T2"])}
    tt = read_json(design_dir / "tier_table.json")
    certain = {(r["tier"], r["option"]): (r["jeffreys_mean"], r["calibration_id"]) for r in tt["pairs"] if r["certain"]}
    return Frozen(design_dir, d1, b1, hmm, read_json(design_dir / "verifiers.json"), certain,
                  read_json(design_dir / "calibration_records.json"), d1["template_sha256"],
                  bool(d1["synthetic"] or h.get("synthetic")), files, fr,
                  None if freeze_file is None else Path(freeze_file).resolve())


def assert_apply_allowed(ids, frozen: Frozen, sets: dict | None = None) -> dict:
    """Chapter 3 of the docstring: the states of a validation document only after a verified design freeze, of a
    group-7 document only with the method freeze manifest. src/m10_guard.py refuses test documents."""
    sets = sets or load_sets()
    ids = [str(d) for d in ids]
    try:
        g = guard.assert_allowed(ids)
    except guard.GuardRefusal as e:
        raise DesignRefusal(str(e)) from None
    val = {str(d) for d in sets["validation"]}
    g7 = {str(d) for d in sets["group7"]}
    dev = {str(d) for d in sets["dev"]}
    n_val = sum(d in val for d in ids)
    n_g7 = sum(d in g7 for d in ids)
    if (n_val or n_g7) and frozen.freeze is None:
        raise DesignRefusal(f"{n_val} validation and {n_g7} group-7 documents: no verified design freeze file "
                            "(criteria chapter 3, rules 2 and 3)")
    if (n_val or n_g7) and (frozen.freeze_path != FREEZE_FILE.resolve() or frozen.freeze.get("dry_run")
                            or frozen.freeze.get("problems")):
        raise DesignRefusal("validation and group-7 documents need the real design freeze file "
                            f"{rel(FREEZE_FILE)} (not a dry run, no problems)")
    if (n_val or n_g7) and frozen.synthetic:
        raise DesignRefusal("a synthetic design is never applied to validation or group-7 documents")
    if n_g7 and not METHOD_FREEZE.is_file():
        raise DesignRefusal(f"{n_g7} group-7 documents: no method freeze manifest (criteria chapter 10.5)")
    return {"documents": len(ids), "dev": sum(d in dev for d in ids), "validation": n_val, "group7": n_g7,
            "other": len(ids) - sum(d in dev for d in ids) - n_val - n_g7}


def head_probs(head: dict, X: np.ndarray) -> np.ndarray:
    return softmax(head_logits(head, np.atleast_2d(X)) / head["T"])


def as_written(x: float) -> float:
    """Clip to [0.005, 0.995] and 4 decimals, as src/m10_writer.py writes a probability (criteria chapter 8.5)."""
    return round(min(max(float(x), CLIP_LO), CLIP_HI), 4)


def spread(chosen: str, p: float, weights, options) -> dict:
    """The option distribution of a label with probability p for the chosen option: the other options share 1 - p
    in proportion to the calibrated Apertus distribution (weights). Then the clip and 4 decimals (proposal P7)."""
    w = {o: max(float(weights[i]), P_FLOOR) for i, o in enumerate(options)}
    rest = sum(w[o] for o in options if o != chosen)
    return {o: as_written(p if o == chosen else (1 - p) * w[o] / rest) for o in options}


def cascade_decisions(d: str, frozen: Frozen, states_dir: Path, entry_d1: bool, entry_b12: bool,
                      r2: dict | None = None, dev_ids: set[str] | None = None) -> dict | None:
    """Interface 7 (mode cascade) for one document; None if the document has no states file. The caller must call
    assert_apply_allowed first. Each probability is written as src/m10_writer.py writes it (clip and 4 decimals);
    each label has the full option distribution (check_decisions of src/m10_cascade.py)."""
    d = str(d)
    doc = load_doc(d)
    rule = load_rule(d)
    bids = [b["block"] for b in doc["blocks"]]
    if [b["block"] for b in rule["blocks"]] != bids:
        raise ValueError(f"{d}: the rule file and the doc file have other blocks")
    p = npz_path(states_dir, d)
    if not p.is_file():
        return None
    s = read_states(p, d, bids)
    if s["meta"].get("template_sha256") != frozen.template_sha256:
        raise DesignRefusal(f"{d}: the template SHA-256 of the states is not the frozen template")
    st = s["states"]
    i1 = layer_index(s["layers"], (frozen.d1["layer"],))[0]
    ib = layer_index(s["layers"], (frozen.b1["layer"],))[0]
    pd1 = head_probs(frozen.d1, st[0, i1].astype(np.float64))[0]
    Q = head_probs(frozen.b1, st[1:, ib].astype(np.float64))
    b2 = b2_document(Q, frozen.hmm, frozen.hmm["form"], pd1)
    marg2 = temper(b2["marg"], frozen.hmm["T2"])
    in_dev = d in (dev_ids or set())
    dd = rule["document"]
    r1 = bool(dd["d1"].get("needs_apertus"))
    rule_id = (dd.get("s1") or {}).get("rule_id")
    k = int(pd1.argmax())
    if entry_d1 or r1:
        d1 = {"option": D1_OPTIONS[k], "probs": {o: as_written(pd1[i]) for i, o in enumerate(D1_OPTIONS)},
              "source": "apertus_head", "calibration": CAL["d1_head"]}
    else:
        o = dd["d1"]["option"]
        pv = float(platt(pd1[D1_OPTIONS.index(o)], frozen.verifiers["d1"]))
        d1 = {"option": o, "probs": spread(o, pv, pd1, D1_OPTIONS), "source": "rule", "calibration": CAL["d1_verifier"]}
    if rule_id:
        d1["rule_id"] = str(rule_id)
    d1 |= {"in_sample": in_dev, "needs_apertus": r1}
    ropt, rtier = rule_view(rule, D1_OPTIONS[k] if r1 else None)
    blocks, written = [], []
    for j, bid in enumerate(bids):
        o_r, t_r = ropt[j], rtier[j]
        if (t_r, o_r) in frozen.certain:
            jm, cid = frozen.certain[(t_r, o_r)]
            blocks.append({"block": bid, "option": o_r, "probs": spread(o_r, jm, marg2[j], OPTIONS), "source": "rule",
                           "tier": t_r, "calibration": cid, "in_sample": True, "certain_pair": True})
        elif entry_b12:
            o = b2["path"][j]
            blocks.append({"block": bid, "option": o, "probs": {x: as_written(marg2[j, i]) for i, x in enumerate(OPTIONS)},
                           "source": "code", "tier": t_r, "calibration": CAL["b2_marginal"], "in_sample": in_dev,
                           "certain_pair": False})
        else:
            pv = float(platt(marg2[j, OPTIONS.index(o_r)], frozen.verifiers["b2"]))
            blocks.append({"block": bid, "option": o_r, "probs": spread(o_r, pv, marg2[j], OPTIONS), "source": "rule",
                           "tier": t_r, "calibration": CAL["b2_verifier"], "in_sample": in_dev, "certain_pair": False})
        written.append(blocks[-1]["option"])
    boundaries = [{"after_block": bids[t], "kind": "switch", "p": as_written(b2["switch"][t]),
                   "calibration": CAL["b2_switch"], "source": "code"} for t in switch_gaps(written)]
    return {"doc_id": d, "mode": "cascade", "document": {"d1": d1}, "blocks": blocks, "boundaries": boundaries,
            "r2": r2,
            "schema": "parlpdfech-gj-decisions/1", "status": STATUS, "split": rule.get("split"),
            "entry": {"d1": bool(entry_d1), "b1_b2": bool(entry_b12)},
            "heads": {f: h for f, h in frozen.files.items()},
            "template_sha256": frozen.template_sha256,
            "model": s["meta"].get("model_fingerprint"),
            "b2_form": frozen.hmm["form"],
            "gap_switch_probabilities": [{"after_block": bids[t], "p": r6(b2["switch"][t])}
                                         for t in range(len(bids) - 1)],
            "design": {"path": rel(SCRIPT), "sha256": sha256_file(SCRIPT), "version": VERSION},
            "design_freeze_sha256": None if frozen.freeze is None else frozen.freeze.get("_sha256"),
            "synthetic": frozen.synthetic}


def cmd_apply(args) -> int:
    freeze = Path(args.freeze) if args.freeze else None
    frozen = load_frozen(Path(args.design), freeze)
    if frozen.freeze is not None:
        frozen.freeze["_sha256"] = sha256_file(freeze)
    ids = [i for a in args.items for i in guard.read_items(a)]
    sets = load_sets()
    allowed = assert_apply_allowed(ids, frozen, sets)
    yes = {"yes": True, "no": False}
    e1, e2 = yes[args.entry_d1], yes[args.entry_b12]
    r2_all = read_json(args.r2) if args.r2 else {}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dev = {str(d) for d in sets["dev"]}
    outputs, no_states = {}, []
    for d in ids:
        dec = cascade_decisions(d, frozen, Path(args.states), e1, e2, r2_all.get(d), dev)
        if dec is None:
            no_states.append(d)
            continue
        outputs[rel(out / f"{d}.json")] = write_json(out / f"{d}.json", dec)
    cal = calibration_file(frozen, e1, e2)
    outputs[rel(args.calibrations_out)] = write_json(args.calibrations_out, cal)
    rec = {"version": VERSION, "status": STATUS, "made": now(), "script": {"path": rel(SCRIPT),
                                                                         "sha256": sha256_file(SCRIPT)},
           "design": {"folder": rel(args.design), "files": frozen.files, "synthetic": frozen.synthetic},
           "freeze": None if freeze is None else {"path": rel(freeze), "sha256": sha256_file(freeze)},
           "entry": {"d1": e1, "b1_b2": e2}, "documents": allowed, "without_states": no_states,
           "outputs": outputs}
    write_json(out / "apply_run.json", rec)
    print(json.dumps({"documents": allowed, "decisions_files": len(outputs) - 1, "without_states": len(no_states),
                      "run_record": rel(out / "apply_run.json")}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- design freeze (criteria chapter 10.1)

def freeze_content(design_dir: Path, dry_run: bool) -> dict:
    design_dir = Path(design_dir)
    des = read_json(design_dir / "design.json")
    run = read_json(design_dir / "run_design.json")
    problems = []
    if des.get("synthetic") and not dry_run:
        problems.append("the design is synthetic")
    crit = sha256_file(CRITERIA)
    if crit != CRITERIA_SHA:
        problems.append("the criteria file differs from the protocol value")
    tpl = read_json(JOB_TEMPLATE)
    if des["template_sha256"] != tpl["sha256"]:
        problems.append("the template SHA-256 of the design differs from the job template")
    ff = frozen_files()
    if ff["different"]:
        problems.append(f"FROZEN_FILES changed: {ff['different']}")
    if run.get("script", {}).get("sha256") != sha256_file(SCRIPT) and not dry_run:
        problems.append("src/m10_design.py differs from the script of the design run")
    lab = {rel(p): sha256_file(p) for p in sorted(LABELS.glob("*.json"))}
    files = {rel(p): sha256_file(p) for p in sorted(design_dir.rglob("*")) if p.is_file()}
    dfiles = {f: sha256_file(design_dir / f) for f in DESIGN_FILES}
    content = {
        "schema": "parlpdfech-gj-design-freeze/1", "version": VERSION, "status": STATUS, "made": now(),
        "dry_run": dry_run, "synthetic_design": bool(des.get("synthetic")), "problems": problems,
        "criteria": {"path": rel(CRITERIA), "sha256": crit, "protocol_value": CRITERIA_SHA},
        "template": {"job_template": {"path": rel(JOB_TEMPLATE), "sha256": sha256_file(JOB_TEMPLATE)},
                     "template_sha256": tpl["sha256"], "T0": T0, "is_T0": tpl["sha256"] == T0,
                     "states_template_sha256": des["template_sha256"]},
        "code": m10_code(),
        "sets": {"path": rel(SETS), "sha256": sha256_file(SETS)},
        "labels": {"files": len(lab), "digest": digest_lines(lab), "sha256": lab},
        "design_files": {f"{rel(design_dir)}/{f}": h for f, h in dfiles.items()},
        "design_folder": files,
        "design_run": {"path": rel(design_dir / "run_design.json"), "sha256": sha256_file(design_dir / "run_design.json"),
                       "script_sha256": run.get("script", {}).get("sha256"),
                       "script_sha256_recorded": run.get("script_sha256_recorded"),
                       "first_out_of_fold_value": run.get("first_out_of_fold_value")},
        "choices": {"d1": {k: des["d1"][k] for k in ("layer", "C", "T")},
                    "b1": {k: des["b1"][k] for k in ("layer", "C", "T")},
                    "b2": {"form": des["b2"]["form"], "T2": des["b2"]["t2_T"]},
                    "hmm": {"path": f"{rel(design_dir)}/b2_hmm.json", "sha256": dfiles["b2_hmm.json"]},
                    "platt": {k: {x: des["verifiers"][k][x] for x in ("alpha", "beta", "n")} for k in ("d1", "b2")},
                    "certain_pairs": des["certain_pairs"], "thresholds": des["thresholds"],
                    "lora_trigger": des["lora_trigger"]["b1_l_starts"]},
        "frozen_files": ff,
        "model_fingerprint": des["model_fingerprint"],
    }
    return content


def cmd_freeze(args) -> int:
    content = freeze_content(Path(args.design), args.dry_run)
    if args.dry_run:
        if not args.out or Path(args.out).resolve() == FREEZE_FILE.resolve():
            print("usage error: --dry-run needs --out with another path than daten/gj/design_freeze.json",
                  file=sys.stderr)
            return 2
        write_json(Path(args.out), content)
        print(json.dumps({"dry_run": True, "out": rel(args.out), "problems": content["problems"]}, ensure_ascii=False))
        return 0
    if content["problems"]:
        print(json.dumps({"refused": content["problems"]}, ensure_ascii=False))
        return 1
    if FREEZE_FILE.exists():
        print(f"refused: {rel(FREEZE_FILE)} exists (one design freeze)", file=sys.stderr)
        return 1
    h = write_json(FREEZE_FILE, content)
    print(json.dumps({"written": rel(FREEZE_FILE), "sha256": h}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- command line

def cmd_folds(args) -> int:
    sets = load_sets()
    ids = [str(d) for d in sets["dev"]]
    g = assert_fit_ids(ids, sets)
    folds = make_folds(ids, body_keys(ids))
    out = Path(args.out)
    files = write_folds(folds, out)
    rec = {"version": VERSION, "status": STATUS, "made": now(), "script": {"path": rel(SCRIPT),
                                                                         "sha256": sha256_file(SCRIPT)},
           "guard": g, "inputs": {rel(p): sha256_file(p) for p in (SETS, POOL_CSV, GROUPS_CSV)},
           "documents_by_fold": folds["documents_by_fold"], "parliaments": folds["parliaments"], "outputs": files,
           "note": "folds only: no model output and no out-of-fold value"}
    write_json(out / "folds_run.json", rec)
    print(json.dumps({"documents_by_fold": folds["documents_by_fold"], "parliaments": folds["parliaments"],
                      "files": files}, ensure_ascii=False))
    return 0


def cmd_run(args) -> int:
    ids = None
    if args.docs_file:
        if not args.synthetic:
            print("usage error: --docs-file needs --synthetic", file=sys.stderr)
            return 2
        ids = guard.read_items(args.docs_file)
    design = run_design(Path(args.states), Path(args.out), ids, args.synthetic, args.template_sha)
    print(json.dumps({"d1": {k: design["d1"][k] for k in ("layer", "C", "T")},
                      "b1": {k: design["b1"][k] for k in ("layer", "C", "T")},
                      "b2": {"form": design["b2"]["form"], "T2": design["b2"]["t2_T"]},
                      "thresholds": design["thresholds"], "lora_trigger": design["lora_trigger"]["b1_l_starts"],
                      "synthetic": design["synthetic"]}, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("folds")
    f.add_argument("--out", default=str(DESIGN))
    r = sub.add_parser("run")
    r.add_argument("--states", default=str(STATES_GPU1))
    r.add_argument("--out", default=str(DESIGN))
    r.add_argument("--synthetic", action="store_true")
    r.add_argument("--docs-file", default=None)
    r.add_argument("--template-sha", default=None)
    z = sub.add_parser("freeze")
    z.add_argument("--design", default=str(DESIGN))
    z.add_argument("--dry-run", action="store_true")
    z.add_argument("--out", default=None)
    a = sub.add_parser("apply")
    a.add_argument("--design", default=str(DESIGN))
    a.add_argument("--states", default=str(STATES_GPU1))
    a.add_argument("--entry-d1", choices=("yes", "no"), required=True)
    a.add_argument("--entry-b12", choices=("yes", "no"), required=True)
    a.add_argument("--out", default=str(DECISIONS))
    a.add_argument("--calibrations-out", required=True)
    a.add_argument("--r2", default=None)
    a.add_argument("--freeze", default=None)
    a.add_argument("items", nargs="+")
    args = ap.parse_args()
    try:
        return {"folds": cmd_folds, "run": cmd_run, "freeze": cmd_freeze, "apply": cmd_apply}[args.cmd](args)
    except DesignRefusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

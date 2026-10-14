"""Calibration library of gate GJ and the fit of the floor converter F1 on dev.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream D of
workflow wf_0befda9d-e60, for the main agent; the clip of the gaps (chapter 1): stream D of workflow
wf_d5120f1f-fd4 (wave 3). Phase 4 (modeling) and phase 6 (deployment), gate GJ (OPEN). Status:
EXCEPTION (process rule 10), NOT RELEASED. Criteria: `crisp-dm/04-modeling/gate-jev-cascade-criteria.md` (SHA-256
6f6d15c0...), chapters 6.2, 6.3, 7.4 and 8.4 to 8.8. Plan: `crisp-dm/00-cross-cutting/plan-full-conversion.md`,
chapters 2, 4 and 5.2. This file changes no existing file.

1 Measures (criteria 6.2). Q is a matrix (units x options) of the probabilities as written (after the clip of item
  3); y is the index of the reference option of each unit.
  top label      the option with the highest q; for equal values, the first option in the option order. max q is
                 its probability. "correct" = the top label is the reference option.
  ece            10 bins of equal width of max q on [0, 1]: bin b holds b/10 <= max q < (b+1)/10; the last bin
                 holds 1.0. ECE = sum over the bins of (n_b / N) x |accuracy_b - mean max q_b|.
  ece_equal_mass the units sorted by max q (stable sort), then 10 bins with sizes that differ by 1 or less
                 (numpy.array_split; the first bins are the larger ones). Information.
  classwise_ece  for each option c: 10 bins of equal width of q_c over all units; ECE_c = sum over the bins of
                 (n_b / N) x |s_b - m_b| (s_b: share of the units with the reference option c; m_b: mean q_c). The
                 value is the mean of ECE_c over all options of the label kind.
  brier          mean over the units of the sum over the options of (q_c - y_c)^2.
  nll            mean over the units of -ln q(reference option).
  reliability    n, mean max q and accuracy for each bin of equal width.
  coverage_vs_error  for each a of {0.6, 0.7, 0.8, 0.9, 0.95, 0.99}: share and error of the units with max q >= a.
  wrong_at_0_99  count of the units with max q >= 0.99 whose top label is not the reference option.
  A binary label kind has q = (p, 1 - p).
  Gaps (switch boundary, all gaps between two blocks; criteria 6.2 item 11): a gap with a switch label has the p of
  the label; another gap has the switch probability of the gap in the decisions file (key
  gap_switch_probabilities, mode cascade) or else p_gap_without_label of the floor calibration file. Each gap
  value is clipped to [0.005, 0.995] (criteria 8.5 item 3), as each written probability.
  The written-option values (information, as criterion GJ.13): p of the written option, correct = the written
  option is the reference option, ECE with 10 bins of equal width, and the count of the units where another
  option has a higher q than the written option (written_option_below_max_q).

2 Intervals (criteria 6.3, proposal P4)
  Jeffreys interval: the 5 % and 95 % quantiles of Beta(k + 0.5, n - k + 0.5) (scipy.special.betaincinv).
  Jeffreys posterior mean: (k + 0.5) / (n + 1).
  Document bootstrap: the documents in the order of their numeric doc id get the indices 0 to D - 1. The draws are
  numpy.random.default_rng(20261013).integers(0, D, size=(2000, D)): one row for each resample. A resample takes
  all units of each drawn document (a document drawn two times counts two times) and calculates the value again.
  The bounds are numpy.quantile(values, 0.05) and numpy.quantile(values, 0.95) (method "linear").
  Paired bootstrap: the two methods use the same rows; the value is method minus baseline.

3 Calibration maps (criteria 8.3 to 8.6)
  temperature    one T > 0 for each head: the minimum of the NLL of softmax(z / T) over the pooled out-of-fold
                 logits (scipy.optimize.minimize_scalar, method "bounded", on ln T in [ln 0.05, ln 20]). On
                 probabilities (the B2 marginals): z = ln q.
  platt          p' = 1 / (1 + exp(-(alpha x logit(p) + beta))), the minimum of the NLL (Newton steps with step
                 halving). Before the logit, p is limited to [1e-7, 1 - 1e-7], so that logit(p) is finite.
  clip           each probability to [0.005, 0.995]; the values of an option distribution are not divided by their
                 sum again (proposal P7). as_written() also rounds to 4 decimals, as src/m10_writer.py does.
  threshold a    (P17) the smallest a of {0.6, 0.7, 0.8, 0.9, 0.95, 0.99} where the labels with p >= a have an
                 accuracy of 0.95 or more and a coverage of 0.50 or more. Else no a: each label of the kind is
                 unsure.

4 Floor converter F1 (criteria 7.4 and 8.7; command floor-fit). Fit set: the 193 dev documents of
  daten/gj/sets.json, the rule files daten/gj/rules/<doc>.json (src/m10_rules.py) and the label files
  daten/gj/labels/<doc>.json (src/m10_labels.py, AI reference E20 v4.1 with the pilot overrides). Each file must
  have the SHA-256 of the run record of its stream. All values are in-sample.
  (tier, option) pair   the rule tier and the rule option of a block. Precision = blocks of the pair with the
                 reference option of the pair, divided by the blocks of the pair. certain = (dev precision >= 0.99
                 and 30 or more dev documents) and (precision >= 0.99 on the blocks of the pair in the 48
                 documents of dev_out_of_design; no such block = not certain, P9). The table is GJ.20.
  block label    p = the Jeffreys posterior mean of the pair. The other 5 options share 1 - p in proportion to the
                 dev confusion row of the pair (the reference options of the blocks of the pair) plus 1 for each
                 option (add-one). Then the clip.
  backoff        a pair without a dev block (only possible on other sets) uses, in this order: the pair (tier
                 kind, option) with the tier kind = the part of the tier before ":"; the rule option alone; all
                 dev blocks. Each step has its own calibration record. A backoff label is never certain.
  D1 label       the S1 rule role with the map of proposal P3 (proposal A, response B, combined C; minutes,
                 committee and other D). p = the Jeffreys posterior mean of the S1 rule id on dev (the D1 of the
                 rule is the reference D1). The other 3 options share 1 - p as for a block, with the confusion row
                 of the S1 rule id. A rule id without a dev document uses the pooled value of all dev documents.
                 The S1 rule id R1 (needs_apertus) gives the provisional rule role: its calibration record has no
                 threshold a, so its value status is always unsure.
  switch boundary the gaps where the family of the rule block path changes between Submission (submitted,
                 reasoning) and Response (response, recommendation); title and none do not change the family; the
                 gap is directly before the first block of the new family (criteria 2.5). p = the Jeffreys
                 posterior mean of the precision of these gaps on the dev reference switch boundaries. A gap
                 without a switch label has the switch probability of the record parameter
                 p_gap_without_label (Jeffreys mean of the reference switch boundaries among these gaps), clipped
                 to [0.005, 0.995] in the measures (criteria 8.5 item 3). The measures of the switch boundary use
                 all gaps (criteria 6.2 item 11).
  Value status: each record has the threshold a of its label kind (P17 on the dev in-sample values of the written
  labels). Calibration records: one for each pair (block_slot), one for each S1 rule id (document_text_parts),
  one for the switch boundary (author_switch), and the backoff records. Format: the class Calibration of
  src/m10_label_schema.yaml in the file format of src/m10_writer.py ({"calibrations": {id: {...}}}). The key
  floor_lookup of the same file gives src/m10_cascade.py the values of each pair, rule id and the switch
  boundary. target_status is not_measured (the target of GJ.13 is on validation).

5 Commands (from the project folder)
  uv run --offline --frozen --no-sync python src/m10_calibrate.py floor-fit
      Writes daten/gj/calibration/floor_v1.json, certainty_dev.json, floor_v1_fitset.json and the run record
      daten/gj/calibration/runs/floor_fit_v1.json. The run record gets the SHA-256 of this file before the
      first value (GJ.2).
  uv run --offline --frozen --no-sync python src/m10_calibrate.py measure --decisions daten/gj/decisions_floor
      --set dev [--calibrations daten/gj/calibration/floor_v1.json] [--out <file>]
      The measures of a decisions folder (interface 7) against the label files. validation and group7 only for
      the one held-out run: the freeze file (daten/gj/design_freeze.json, group 7: daten/gj/freeze_manifest.json)
      must exist and name the SHA-256 of this file, of src/m10_cascade.py and of the calibration file.

6 Process rule 6 and the criteria rules: each document passes src/m10_guard.py before a file of it is read
  (floor-fit: dev only). No file of a test document, no model output and no value of a validation or group-7
  document is read before the freeze. The FROZEN_FILES of src/m05_gate3a_v4_measure.py are checked at the end.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402  (split guard of process rule 6, stream B)

VERSION = "m10-calibrate-1"
FLOOR_VERSION = "floor-v1"
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
GJ = ROOT / "daten/gj"
SETS_FILE = GJ / "sets.json"
RULES_DIR = GJ / "rules"
LABELS_DIR = GJ / "labels"
RULES_RUN = GJ / "runs/m10_rules_run.json"
LABELS_BUILD = GJ / "labels_build.json"
CAL_DIR = GJ / "calibration"
CAL_RUNS = CAL_DIR / "runs"
FLOOR_FILE = CAL_DIR / "floor_v1.json"
CERTAINTY_FILE = CAL_DIR / "certainty_dev.json"
FITSET_FILE = CAL_DIR / "floor_v1_fitset.json"
FIT_RUN = CAL_RUNS / "floor_fit_v1.json"
DESIGN_FREEZE = GJ / "design_freeze.json"
FREEZE_MANIFEST = GJ / "freeze_manifest.json"
CASCADE_SCRIPT = ROOT / "src/m10_cascade.py"
MEASURE_SCRIPT = ROOT / "src/m05_gate3a_v4_measure.py"
CRITERIA = ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria.md"
CRITERIA_SHA = "6f6d15c0562cba2070995c302080a9aaedfe665f8d746ed5b0fdd9248bc20bfe"

OPTIONS = ("submitted", "reasoning", "response", "recommendation", "title", "none")
D1_OPTIONS = ("A", "B", "C", "D")
SWITCH_OPTIONS = ("switch", "no_switch")
FAMILY = {"submitted": "S", "reasoning": "S", "response": "R", "recommendation": "R"}
D1_OF_ROLE = {"proposal": "A", "response": "B", "combined": "C", "minutes": "D", "committee": "D", "other": "D"}  # P3
NEEDS_APERTUS_ID = "R1"
P_MIN, P_MAX, P_DIGITS = 0.005, 0.995, 4
A_GRID = (0.6, 0.7, 0.8, 0.9, 0.95, 0.99)
P17_ACCURACY, P17_COVERAGE = 0.95, 0.50
CERTAIN_PRECISION, CERTAIN_DOCUMENTS = 0.99, 30
N_BINS = 10
N_BOOT = 2000
SEED = 20261013
WRONG_AT = 0.99
LOGIT_EPS = 1e-7
REFERENCE = ("AI reference E20 v4.1 (daten/iso/v4/ref41 and daten/iso/v4/pool_ref41, mapped to the options of "
             "criteria 2.2) with the pilot overrides of 879163, 375917 and 549658")
STATUS = "EXCEPTION (process rule 10); NOT RELEASED"
ACTOR = "workflow sub-agent (Claude Opus 5.5), stream D of workflow wf_0befda9d-e60, for the main agent"
KIND_OF = {"block": "block_slot", "d1": "document_text_parts", "switch": "author_switch"}


# ------------------------------------------------------------------ small helpers
def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)


def clock() -> str:
    return time.strftime("%d.%m.%Y, %H:%M:%S %Z")


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj, compact: bool = False) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else \
        json.dumps(obj, ensure_ascii=False, indent=1)
    p.write_text(text + "\n", encoding="utf-8")


def r6(x):
    """Round a value of a record to 6 decimals (None stays None)."""
    return None if x is None else round(float(x), 6)


# ------------------------------------------------------------------ clip (criteria 8.5)
def clip(x):
    """Each probability to [0.005, 0.995]; no new division by the sum (proposal P7)."""
    return np.clip(np.asarray(x, dtype=float), P_MIN, P_MAX)


def as_written(x: float) -> float:
    """The value that src/m10_writer.py writes: the clip, then 4 decimals."""
    return round(min(max(float(x), P_MIN), P_MAX), P_DIGITS)


# ------------------------------------------------------------------ measures (criteria 6.2)
def bin_index(x) -> np.ndarray:
    """Bin of equal width: b/10 <= x < (b+1)/10; the last bin holds 1.0."""
    edges = np.arange(1, N_BINS) / N_BINS
    return np.searchsorted(edges, np.asarray(x, dtype=float), side="right")


def top_label(Q) -> tuple[np.ndarray, np.ndarray]:
    """(index of the top label, max q). Equal values: the first option in the option order."""
    Q = np.asarray(Q, dtype=float)
    return np.argmax(Q, axis=1), Q.max(axis=1)


def ece_equal_width(conf, correct) -> float:
    conf, correct = np.asarray(conf, dtype=float), np.asarray(correct, dtype=float)
    n = len(conf)
    if not n:
        return float("nan")
    b = bin_index(conf)
    s_conf = np.bincount(b, weights=conf, minlength=N_BINS)
    s_ok = np.bincount(b, weights=correct, minlength=N_BINS)
    return float(np.abs(s_ok - s_conf).sum() / n)


def ece_equal_mass(conf, correct) -> float:
    conf, correct = np.asarray(conf, dtype=float), np.asarray(correct, dtype=float)
    n = len(conf)
    if not n:
        return float("nan")
    order = np.argsort(conf, kind="stable")
    return float(sum(abs(correct[part].sum() - conf[part].sum()) for part in np.array_split(order, N_BINS)
                     if len(part)) / n)


def classwise_ece(Q, y) -> float:
    Q, y = np.asarray(Q, dtype=float), np.asarray(y)
    n, k = Q.shape
    if not n:
        return float("nan")
    vals = []
    for c in range(k):
        q = Q[:, c]
        b = bin_index(q)
        s_q = np.bincount(b, weights=q, minlength=N_BINS)
        s_y = np.bincount(b, weights=(y == c).astype(float), minlength=N_BINS)
        vals.append(np.abs(s_y - s_q).sum() / n)
    return float(np.mean(vals))


def brier(Q, y) -> float:
    Q, y = np.asarray(Q, dtype=float), np.asarray(y)
    Y = np.zeros_like(Q)
    Y[np.arange(len(y)), y] = 1.0
    return float(((Q - Y) ** 2).sum(axis=1).mean())


def nll(Q, y) -> float:
    Q, y = np.asarray(Q, dtype=float), np.asarray(y)
    return float(-np.log(Q[np.arange(len(y)), y]).mean())


def reliability_table(conf, correct) -> list[dict]:
    conf, correct = np.asarray(conf, dtype=float), np.asarray(correct, dtype=float)
    b = bin_index(conf)
    out = []
    for i in range(N_BINS):
        m = b == i
        n = int(m.sum())
        out.append({"bin": [i / N_BINS, (i + 1) / N_BINS], "n": n,
                    "mean_max_q": r6(conf[m].mean()) if n else None,
                    "accuracy": r6(correct[m].mean()) if n else None})
    return out


def coverage_vs_error(conf, correct, grid=A_GRID) -> list[dict]:
    conf, correct = np.asarray(conf, dtype=float), np.asarray(correct, dtype=bool)
    n = len(conf)
    out = []
    for a in grid:
        m = conf >= a
        k = int(m.sum())
        out.append({"a": a, "n": k, "coverage": r6(k / n) if n else None,
                    "error": r6(1 - correct[m].mean()) if k else None})
    return out


def wrong_at(conf, correct, at: float = WRONG_AT) -> int:
    conf, correct = np.asarray(conf, dtype=float), np.asarray(correct, dtype=bool)
    return int(((conf >= at) & ~correct).sum())


def binary_q(p) -> np.ndarray:
    """q = (p, 1 - p) of a binary label kind (criteria 6.2 item 10)."""
    p = np.asarray(p, dtype=float)
    return np.stack([p, 1 - p], axis=1)


# ------------------------------------------------------------------ intervals (criteria 6.3)
def jeffreys_mean(k: int, n: int) -> float:
    return (k + 0.5) / (n + 1)


def jeffreys_interval(k: int, n: int, low: float = 0.05, high: float = 0.95) -> tuple[float, float]:
    from scipy.special import betaincinv

    return float(betaincinv(k + 0.5, n - k + 0.5, low)), float(betaincinv(k + 0.5, n - k + 0.5, high))


def bootstrap_draws(n_groups: int, n_boot: int = N_BOOT, seed: int = SEED) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n_groups, size=(n_boot, n_groups))


def group_units(groups) -> list[np.ndarray]:
    """The unit indices of each group 0 .. G-1 (groups: the group index of each unit)."""
    groups = np.asarray(groups)
    g = int(groups.max()) + 1 if len(groups) else 0
    order = np.argsort(groups, kind="stable")
    cuts = np.searchsorted(groups[order], np.arange(g + 1))
    return [order[cuts[i]:cuts[i + 1]] for i in range(g)]


def doc_bootstrap(groups, stats: dict, n_boot: int = N_BOOT, seed: int = SEED, draws=None) -> dict:
    """{name: {"low": 5 % quantile, "high": 95 % quantile}} of each stat(unit indices) over the resamples."""
    units = group_units(groups)
    draws = bootstrap_draws(len(units), n_boot, seed) if draws is None else draws
    vals = {k: np.empty(len(draws)) for k in stats}
    for r, row in enumerate(draws):
        idx = np.concatenate([units[g] for g in row])
        for k, f in stats.items():
            vals[k][r] = f(idx)
    return {k: {"low": float(np.quantile(v, 0.05)), "high": float(np.quantile(v, 0.95))} for k, v in vals.items()}


def paired_bootstrap(groups, stat_method, stat_baseline, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Method minus baseline on the same resamples: the value, the 5 % and the 95 % quantile."""
    units = group_units(groups)
    all_idx = np.concatenate(units) if units else np.array([], dtype=int)
    diff = []
    for row in bootstrap_draws(len(units), n_boot, seed):
        idx = np.concatenate([units[g] for g in row])
        diff.append(stat_method(idx) - stat_baseline(idx))
    return {"value": float(stat_method(all_idx) - stat_baseline(all_idx)),
            "low": float(np.quantile(diff, 0.05)), "high": float(np.quantile(diff, 0.95))}


# ------------------------------------------------------------------ calibration maps (criteria 8.3, 8.4, 8.6)
def softmax(Z) -> np.ndarray:
    Z = np.asarray(Z, dtype=float)
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)


def nll_logits(Z, y, T: float = 1.0) -> float:
    Z = np.asarray(Z, dtype=float) / T
    Z = Z - Z.max(axis=1, keepdims=True)
    lse = np.log(np.exp(Z).sum(axis=1))
    return float((lse - Z[np.arange(len(y)), np.asarray(y)]).mean())


def fit_temperature(Z, y, bounds: tuple[float, float] = (0.05, 20.0)) -> dict:
    """One temperature T > 0: the minimum of the NLL of softmax(Z / T) (criteria 8.3)."""
    from scipy.optimize import minimize_scalar

    lo, hi = math.log(bounds[0]), math.log(bounds[1])
    res = minimize_scalar(lambda t: nll_logits(Z, y, math.exp(t)), bounds=(lo, hi), method="bounded",
                          options={"xatol": 1e-10, "maxiter": 500})
    t = float(math.exp(res.x))
    return {"T": t, "nll_before": nll_logits(Z, y, 1.0), "nll_after": nll_logits(Z, y, t),
            "at_bound": bool(abs(res.x - lo) < 1e-6 or abs(res.x - hi) < 1e-6), "n": int(len(y))}


def fit_temperature_probs(Q, y, bounds: tuple[float, float] = (0.05, 20.0)) -> dict:
    """Temperature on probabilities (B2 marginals): z = ln q."""
    return fit_temperature(np.log(np.clip(np.asarray(Q, dtype=float), 1e-12, 1.0)), y, bounds)


def apply_temperature(Z, T: float) -> np.ndarray:
    return softmax(np.asarray(Z, dtype=float) / T)


def logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), LOGIT_EPS, 1 - LOGIT_EPS)
    return np.log(p / (1 - p))


def _sigmoid(x) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def platt_nll(p, y, alpha: float, beta: float) -> float:
    x = logit(p)
    s = alpha * x + beta
    yv = np.asarray(y, dtype=float)
    return float((np.logaddexp(0, s) - yv * s).mean())


def fit_platt(p, y, max_iter: int = 200) -> dict:
    """Platt map p' = 1 / (1 + exp(-(alpha logit(p) + beta))): the minimum of the NLL (criteria 8.4)."""
    x, yv = logit(p), np.asarray(y, dtype=float)
    a, b = 1.0, 0.0
    cur = platt_nll(p, yv, a, b)
    start = cur
    converged = False
    for it in range(max_iter):
        s = _sigmoid(a * x + b)
        g = np.array([((s - yv) * x).sum(), (s - yv).sum()]) / len(x)
        w = s * (1 - s)
        H = np.array([[(w * x * x).sum(), (w * x).sum()], [(w * x).sum(), w.sum()]]) / len(x)
        step = np.linalg.lstsq(H + 1e-12 * np.eye(2), g, rcond=None)[0]
        t = 1.0
        while t > 1e-10:
            na, nb = a - t * step[0], b - t * step[1]
            new = platt_nll(p, yv, na, nb)
            if new <= cur:
                break
            t /= 2
        if t <= 1e-10:
            converged = True
            break
        a, b, change = na, nb, cur - new
        cur = new
        if np.abs(t * step).max() < 1e-10 or change < 1e-15:
            converged = True
            break
    return {"alpha": float(a), "beta": float(b), "nll_before": start, "nll_after": cur, "iterations": it + 1,
            "converged": converged, "n": int(len(x))}


def apply_platt(p, alpha: float, beta: float) -> np.ndarray:
    return _sigmoid(alpha * logit(p) + beta)


def threshold_a(p, correct, grid=A_GRID) -> dict:
    """P17: the smallest a of the grid with accuracy >= 0.95 and coverage >= 0.50 of the labels with p >= a."""
    p, correct = np.asarray(p, dtype=float), np.asarray(correct, dtype=bool)
    n = len(p)
    rows, chosen = [], None
    for a in grid:
        m = p >= a
        k = int(m.sum())
        acc = float(correct[m].mean()) if k else None
        cov = k / n if n else 0.0
        ok = acc is not None and acc >= P17_ACCURACY and cov >= P17_COVERAGE
        rows.append({"a": a, "n": k, "coverage": r6(cov), "accuracy": r6(acc), "meets": ok})
        if ok and chosen is None:
            chosen = a
    return {"a": chosen, "n": n, "grid": rows,
            "rule": "smallest a with accuracy >= 0.95 and coverage >= 0.50 (criteria 8.6, P17)"}


# ------------------------------------------------------------------ measure sets
def written_values(p_written, correct_written) -> dict:
    p, ok = np.asarray(p_written, dtype=float), np.asarray(correct_written, dtype=bool)
    k, n = int(ok.sum()), len(ok)
    lo, hi = jeffreys_interval(k, n)
    return {"n": n, "correct": k, "accuracy": r6(k / n) if n else None, "accuracy_jeffreys_5": r6(lo),
            "accuracy_jeffreys_95": r6(hi), "mean_p": r6(p.mean()) if n else None,
            "ece_written_option": r6(ece_equal_width(p, ok)) if n else None}


def measures(Q, y, groups=None, bootstrap: bool = True, p_written=None, correct_written=None) -> dict:
    """All measures of criteria 6.2 on one set; bootstrap bounds (criteria 6.3) of ECE, Brier and NLL."""
    Q, y = np.asarray(Q, dtype=float), np.asarray(y)
    if not len(y):
        return {"n": 0}
    pred, conf = top_label(Q)
    ok = pred == y
    out = {"n": int(len(y)), "accuracy_top_label": r6(ok.mean()),
           "ece": r6(ece_equal_width(conf, ok)), "ece_equal_mass": r6(ece_equal_mass(conf, ok)),
           "classwise_ece": r6(classwise_ece(Q, y)), "brier": r6(brier(Q, y)), "nll": r6(nll(Q, y)),
           "wrong_at_0_99": wrong_at(conf, ok), "reliability": reliability_table(conf, ok),
           "coverage_vs_error": coverage_vs_error(conf, ok)}
    if bootstrap and groups is not None:
        stats = {"ece": lambda i: ece_equal_width(conf[i], ok[i]), "brier": lambda i: brier(Q[i], y[i]),
                 "nll": lambda i: nll(Q[i], y[i])}
        bs = doc_bootstrap(groups, stats)
        out["bootstrap"] = {k: {"low": r6(v["low"]), "high": r6(v["high"])} for k, v in bs.items()}
        out["bootstrap"]["method"] = (f"document bootstrap, {N_BOOT} resamples, seed {SEED}, 5 % and 95 % quantiles "
                                      f"(criteria 6.3)")
        out["bootstrap"]["documents"] = len(group_units(groups))
    if p_written is not None:
        out["written_option"] = written_values(p_written, correct_written)
        # units where another option has a higher q than the written option (information)
        out["written_option"]["written_option_below_max_q"] = int((np.asarray(p_written, dtype=float) < conf).sum())
    return out


def measure_set_record(name: str, m: dict) -> dict:
    """A MeasureSet of src/m10_label_schema.yaml from the output of measures()."""
    rec = {"set_name": name, "set_n": m["n"], "ece": m["ece"], "ece_equal_mass": m["ece_equal_mass"],
           "classwise_ece": m["classwise_ece"], "brier": m["brier"], "nll": m["nll"]}
    if m.get("bootstrap"):
        rec |= {"ece_low": m["bootstrap"]["ece"]["low"], "ece_high": m["bootstrap"]["ece"]["high"],
                "interval_method": m["bootstrap"]["method"]}
    return rec


# ------------------------------------------------------------------ switch boundaries and floor distributions
def switch_gaps(options: list[str]) -> list[int]:
    """Indices i of the gaps after block i that are switch boundaries (criteria 2.5): the gap directly before the
    first block of the new family. title and none do not change the family."""
    out, last = [], None
    for i, o in enumerate(options):
        f = FAMILY.get(o)
        if f is None:
            continue
        if last is not None and f != last:
            out.append(i - 1)
        last = f
    return out


def spread(chosen: str, p: float, weights: dict, options) -> dict:
    """The option distribution of a floor label: p for the chosen option, 1 - p for the other options in proportion
    to their weights (dev confusion counts plus 1); then the clip and 4 decimals (as written)."""
    rest = [o for o in options if o != chosen]
    total = sum(float(weights[o]) for o in rest)
    return {o: as_written(p if o == chosen else (1 - p) * float(weights[o]) / total) for o in options}


def tier_kind(tier: str) -> str:
    return str(tier).split(":", 1)[0]


def pair_key(tier: str, option: str) -> str:
    return f"{tier}|{option}"


def cal_id(*parts: str) -> str:
    """Calibration id from parts: ':' -> '.', '+' -> '_' (letters, digits, '.', '_' and '-' only)."""
    s = ".".join(str(p).replace(":", ".").replace("+", "_") for p in parts)
    if not all(c.isalnum() or c in "._-" for c in s) or not s[0].isalnum():
        raise ValueError(f"calibration id {s!r} has a character that is not permitted")
    return s


class FloorLookup:
    """The values of the floor converter from the key floor_lookup of a calibration file."""

    def __init__(self, cal: dict):
        self.cal = cal
        self.lk = cal["floor_lookup"]

    def block(self, tier: str, option: str) -> dict:
        b = self.lk["block"]
        for level, table, key in (("pair", b["pairs"], pair_key(tier, option)),
                                  ("tier_kind", b["kinds"], pair_key(tier_kind(tier), option)),
                                  ("option", b["options"], option)):
            if key in table:
                return dict(table[key], level=level)
        return dict(b["all"], level="all")

    def d1(self, rule_id: str) -> dict:
        t = self.lk["d1"]
        if rule_id in t["rule_ids"]:
            return dict(t["rule_ids"][rule_id], level="rule_id")
        return dict(t["all"], level="all")

    def switch(self) -> dict:
        return dict(self.lk["switch"])


# ------------------------------------------------------------------ inputs of the fit
def checked_file(p: Path, digests: dict, what: str) -> dict:
    """Read a JSON file after the path guard; its SHA-256 must be the value of the run record of its stream."""
    guard.check_path(p)
    raw = Path(p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    want = digests.get(rel(p))
    if want != h:
        raise SystemExit(f"{rel(p)}: SHA-256 {h[:12]}... is not the value of the run record of {what}")
    return json.loads(raw.decode("utf-8"))


def stream_digests() -> tuple[dict, dict, dict]:
    rules_run, labels_build = read_json(RULES_RUN), read_json(LABELS_BUILD)
    return (rules_run["outputs"], labels_build["outputs"],
            {rel(RULES_RUN): sha256(RULES_RUN), rel(LABELS_BUILD): sha256(LABELS_BUILD), rel(SETS_FILE): sha256(SETS_FILE)})


def load_set(name: str, allowed: tuple[str, ...]) -> list[str]:
    sets = read_json(SETS_FILE)
    ids = sorted((str(d) for d in sets[name]), key=int)
    split = "group7" if name == "group7" else "validation" if name == "validation" else "dev"
    if split not in allowed:
        raise SystemExit(f"set {name}: the split {split} is not allowed here")
    g = guard.assert_allowed(ids, (split,))
    if g["test_documents"]:
        raise SystemExit("the guard found test documents")
    return ids


def load_documents(ids: list[str], with_labels: bool = True, rules_dir: Path = RULES_DIR,
                   labels_dir: Path = LABELS_DIR) -> dict:
    """{doc: {"rules": ..., "labels": ...}} with the SHA-256 checks of chapter 4."""
    rules_d, labels_d, _ = stream_digests()
    out = {}
    for d in ids:
        r = checked_file(Path(rules_dir) / f"{d}.json", rules_d, "src/m10_rules.py")
        x = {"rules": r}
        if with_labels:
            lab = checked_file(Path(labels_dir) / f"{d}.json", labels_d, "src/m10_labels.py")
            if [b["block"] for b in lab["blocks"]] != [b["block"] for b in r["blocks"]]:
                raise SystemExit(f"{d}: the blocks of the label file and of the rule file differ")
            x["labels"] = lab
        out[d] = x
    return out


def d1_of_rule(rules: dict) -> tuple[str, str, str]:
    """(D1 option, S1 rule role, S1 rule id) of the S1 rule role with the map of P3."""
    s1 = rules["document"]["s1"]
    opt = D1_OF_ROLE[s1["rule_role"]]
    if opt != rules["document"]["d1"]["option"]:
        raise SystemExit(f"{rules['doc_id']}: the D1 option of the rule file is not the P3 map of the S1 rule role")
    return opt, s1["rule_role"], s1["rule_id"]


# ------------------------------------------------------------------ tables (GJ.20, D1, switch)
def certainty_table(units: list[dict], ood: set[str]) -> list[dict]:
    """units: [{doc, tier, option, ref}]. One row for each (tier, option) pair (criteria 8.7)."""
    pairs: dict[tuple, dict] = {}
    for u in units:
        x = pairs.setdefault((u["tier"], u["option"]), {"n": 0, "k": 0, "docs": set(), "ood_n": 0, "ood_k": 0,
                                                         "confusion": Counter()})
        ok = u["ref"] == u["option"]
        x["n"] += 1
        x["k"] += ok
        x["docs"].add(u["doc"])
        x["confusion"][u["ref"]] += 1
        if u["doc"] in ood:
            x["ood_n"] += 1
            x["ood_k"] += ok
    rows = []
    for (tier, option), x in sorted(pairs.items()):
        prec = x["k"] / x["n"]
        ood_prec = x["ood_k"] / x["ood_n"] if x["ood_n"] else None
        c1 = prec >= CERTAIN_PRECISION and len(x["docs"]) >= CERTAIN_DOCUMENTS
        c2 = ood_prec is not None and ood_prec >= CERTAIN_PRECISION
        lo, hi = jeffreys_interval(x["k"], x["n"])
        rows.append({"tier": tier, "option": option, "dev_blocks": x["n"], "dev_correct": x["k"],
                     "dev_precision": r6(prec), "dev_documents": len(x["docs"]),
                     "ood_blocks": x["ood_n"], "ood_correct": x["ood_k"], "ood_precision": r6(ood_prec),
                     "ood_documents": len(x["docs"] & ood),
                     "jeffreys_mean": r6(jeffreys_mean(x["k"], x["n"])), "jeffreys_5": r6(lo), "jeffreys_95": r6(hi),
                     "condition_1": c1, "condition_2": c2, "certain": bool(c1 and c2),
                     "confusion": {o: x["confusion"].get(o, 0) for o in OPTIONS}})
    return rows


def pooled_rows(units: list[dict], key) -> dict:
    """Pooled precision and confusion for the backoff keys of chapter 4."""
    out: dict = {}
    for u in units:
        x = out.setdefault(key(u), {"n": 0, "k": 0, "confusion": Counter(), "docs": set()})
        x["n"] += 1
        x["k"] += u["ref"] == u["option"]
        x["confusion"][u["ref"]] += 1
        x["docs"].add(u["doc"])
    return out


def s1_table(docs: list[dict], ood: set[str]) -> list[dict]:
    """docs: [{doc, rule_id, rule_role, option, ref}]. One row for each S1 rule id (D1 by P3)."""
    by: dict[str, list[dict]] = {}
    for x in docs:
        by.setdefault(x["rule_id"], []).append(x)
    rows = []
    for rid, xs in sorted(by.items()):
        n, k = len(xs), sum(x["option"] == x["ref"] for x in xs)
        on = [x for x in xs if x["doc"] in ood]
        lo, hi = jeffreys_interval(k, n)
        rows.append({"rule_id": rid, "dev_documents": n, "dev_correct": k, "dev_precision": r6(k / n),
                     "ood_documents": len(on), "ood_correct": sum(x["option"] == x["ref"] for x in on),
                     "jeffreys_mean": r6(jeffreys_mean(k, n)), "jeffreys_5": r6(lo), "jeffreys_95": r6(hi),
                     "rule_roles": dict(Counter(x["rule_role"] for x in xs)),
                     "d1_of_rule": dict(Counter(x["option"] for x in xs)),
                     "confusion": {o: sum(x["ref"] == o for x in xs) for o in D1_OPTIONS},
                     "needs_apertus": rid == NEEDS_APERTUS_ID,
                     "certain": bool(k / n >= CERTAIN_PRECISION and n >= CERTAIN_DOCUMENTS
                                     and on and sum(x["option"] == x["ref"] for x in on) / len(on) >= CERTAIN_PRECISION)})
    return rows


def switch_table(gaps: list[dict]) -> dict:
    """gaps: [{doc, gap, pred, ref}] over all gaps of all documents."""
    pred = [g for g in gaps if g["pred"]]
    rest = [g for g in gaps if not g["pred"]]
    k = sum(g["ref"] for g in pred)
    k0 = sum(g["ref"] for g in rest)
    lo, hi = jeffreys_interval(k, len(pred))
    ref_total = sum(g["ref"] for g in gaps)
    return {"gaps": len(gaps), "rule_switch_boundaries": len(pred), "correct": k,
            "precision": r6(k / len(pred)) if pred else None, "jeffreys_mean": r6(jeffreys_mean(k, len(pred))),
            "jeffreys_5": r6(lo), "jeffreys_95": r6(hi), "reference_switch_boundaries": ref_total,
            "recall": r6(k / ref_total) if ref_total else None,
            "gaps_without_label": len(rest), "reference_switch_boundaries_among_them": k0,
            "p_gap_without_label": r6(jeffreys_mean(k0, len(rest))),
            "documents_with_rule_switch": len({g["doc"] for g in pred}),
            "documents_with_reference_switch": len({g["doc"] for g in gaps if g["ref"]})}


# ------------------------------------------------------------------ units of a decisions set (measures)
def units_of(decisions: dict, labels: dict, lookup: FloorLookup | None) -> dict:
    """The measure units of a set: blocks (6 options), D1 (4 options), switch labels (written) and all gaps
    (binary). decisions, labels: {doc: file content}. The documents in the order of their numeric id."""
    docs = sorted(decisions, key=int)
    B = {"Q": [], "y": [], "g": [], "pw": [], "okw": [], "certain": [], "source": []}
    D = {"Q": [], "y": [], "g": [], "pw": [], "okw": [], "source": []}
    S = {"pw": [], "okw": [], "g": []}
    G = {"q": [], "y": [], "g": []}
    p_gap = None
    for gi, d in enumerate(docs):
        dec, lab = decisions[d], labels[d]
        ref = {b["block"]: b["option"] for b in lab["blocks"]}
        if [b["block"] for b in dec["blocks"]] != [b["block"] for b in lab["blocks"]]:
            raise SystemExit(f"{d}: the blocks of the decisions file and of the label file differ")
        for b in dec["blocks"]:
            B["Q"].append([b["probs"].get(o, 0.0) for o in OPTIONS])
            B["y"].append(OPTIONS.index(ref[b["block"]]))
            B["g"].append(gi)
            B["pw"].append(b["probs"][b["option"]])
            B["okw"].append(b["option"] == ref[b["block"]])
            B["certain"].append(bool(b.get("certain_pair")))
            B["source"].append(lab.get("reference"))
        d1 = dec["document"]["d1"]
        D["Q"].append([d1["probs"].get(o, 0.0) for o in D1_OPTIONS])
        D["y"].append(D1_OPTIONS.index(lab["d1"]))
        D["g"].append(gi)
        D["pw"].append(d1["probs"][d1["option"]])
        D["okw"].append(d1["option"] == lab["d1"])
        D["source"].append(lab.get("reference"))
        ref_gaps = set(switch_gaps([b["option"] for b in lab["blocks"]]))
        pos = {b["block"]: i for i, b in enumerate(dec["blocks"])}
        labelled = {pos[x["after_block"]]: x["p"] for x in dec.get("boundaries") or []}
        for i, p in labelled.items():
            S["pw"].append(p)
            S["okw"].append(i in ref_gaps)
            S["g"].append(gi)
        if lookup is not None:
            p_gap = lookup.switch()["p_gap_without_label"]
        # mode cascade: the switch probability of each gap; mode floor: p_gap_without_label (chapter 1, gaps)
        gap_p = {pos[x["after_block"]]: x["p"] for x in dec.get("gap_switch_probabilities") or []}
        for i in range(len(dec["blocks"]) - 1):
            q = labelled.get(i, gap_p.get(i, p_gap))
            if q is None:
                raise SystemExit("a gap without a switch label needs the calibration file (p_gap_without_label)")
            G["q"].append(min(max(float(q), P_MIN), P_MAX))       # the clip of criteria 8.5 item 3
            G["y"].append(0 if i in ref_gaps else 1)
            G["g"].append(gi)
    arr = lambda x, t=float: np.asarray(x, dtype=t)  # noqa: E731
    return {"docs": docs,
            "blocks": {"Q": arr(B["Q"]), "y": arr(B["y"], int), "g": arr(B["g"], int), "pw": arr(B["pw"]),
                       "okw": arr(B["okw"], bool), "certain": arr(B["certain"], bool), "source": B["source"]},
            "d1": {"Q": arr(D["Q"]), "y": arr(D["y"], int), "g": arr(D["g"], int), "pw": arr(D["pw"]),
                   "okw": arr(D["okw"], bool), "source": D["source"]},
            "switch_labels": {"pw": arr(S["pw"]), "okw": arr(S["okw"], bool), "g": arr(S["g"], int)},
            "gaps": {"Q": binary_q(arr(G["q"])), "y": arr(G["y"], int), "g": arr(G["g"], int)}}


def subset(u: dict, mask) -> dict:
    mask = np.asarray(mask, dtype=bool)
    return {k: (v[mask] if isinstance(v, np.ndarray) else [x for x, m in zip(v, mask) if m]) for k, v in u.items()}


def kind_measures(u: dict, ood_docs: set[str] | None = None, bootstrap: bool = True) -> dict:
    """The measures of each label kind of a set, with the written-option values; also on the documents of
    dev_out_of_design, on the non-certain blocks and for each reference source (information)."""
    docs = u["docs"]
    b, d, s, g = u["blocks"], u["d1"], u["switch_labels"], u["gaps"]
    out = {
        "block_slot": measures(b["Q"], b["y"], b["g"], bootstrap, b["pw"], b["okw"]),
        "document_text_parts": measures(d["Q"], d["y"], d["g"], bootstrap, d["pw"], d["okw"]),
        "author_switch_all_gaps": measures(g["Q"], g["y"], g["g"], bootstrap),
        "author_switch_written_labels": written_values(s["pw"], s["okw"]),
    }
    nc = subset(b, ~b["certain"])
    out["block_slot_non_certain"] = measures(nc["Q"], nc["y"], nc["g"], False, nc["pw"], nc["okw"])
    by_src = {}
    for src in sorted({x for x in b["source"] if x}):
        m = subset(b, [x == src for x in b["source"]])
        by_src[src] = measures(m["Q"], m["y"], None, False, m["pw"], m["okw"])
        by_src[src].pop("reliability", None)
        by_src[src].pop("coverage_vs_error", None)
    out["block_slot_by_reference_source"] = by_src
    if ood_docs:
        idx = {i for i, x in enumerate(docs) if x in ood_docs}
        mb = subset(b, [x in idx for x in b["g"]])
        md = subset(d, [x in idx for x in d["g"]])
        out["block_slot_dev_out_of_design"] = measures(mb["Q"], mb["y"], None, False, mb["pw"], mb["okw"])
        out["document_text_parts_dev_out_of_design"] = measures(md["Q"], md["y"], None, False, md["pw"], md["okw"])
    return out


# ------------------------------------------------------------------ frozen files and run records
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
    diff = sorted(p for p, h in frozen.items() if not (ROOT / p).exists() or sha256(ROOT / p) != h)
    return {"source": rel(MEASURE_SCRIPT), "source_sha256": sha256(MEASURE_SCRIPT), "files": len(frozen),
            "different": diff}


def start_run_record(path: Path, what: str, scripts: list[Path]) -> dict:
    """GJ.2: the run record holds the SHA-256 of the script before the first value."""
    rec = {"schema": "parlpdfech-gj-run/1", "what": what, "status": "STARTED (no value yet)", "process_status": STATUS,
           "actor": ACTOR, "gate": "GJ (OPEN)", "started": clock(),
           "scripts": {rel(p): sha256(p) for p in scripts},
           "criteria": {"path": rel(CRITERIA), "sha256": sha256(CRITERIA), "expected": CRITERIA_SHA}}
    if rec["criteria"]["sha256"] != CRITERIA_SHA:
        raise SystemExit("the criteria file has another SHA-256 than the value of the protocol")
    write_json(path, rec)
    rec["script_sha256_recorded"] = rec["started"]
    return rec


def finish_run_record(path: Path, rec: dict, scripts: list[Path]) -> dict:
    now = {rel(p): sha256(p) for p in scripts}
    if now != rec["scripts"]:
        raise SystemExit("a script changed during the run")
    rec["finished"] = clock()
    rec["status"] = "DONE"
    rec["frozen_files"] = frozen_files()
    write_json(path, rec)
    return rec


def freeze_check(set_name: str, cal_file: Path) -> dict:
    """The one held-out run (validation after the design freeze, group 7 after the method freeze)."""
    f = DESIGN_FREEZE if set_name == "validation" else FREEZE_MANIFEST
    if not f.exists():
        raise SystemExit(f"set {set_name}: no freeze file {rel(f)}: no run before the freeze (criteria 10)")
    text = f.read_text(encoding="utf-8")
    need = {rel(SCRIPT): sha256(SCRIPT), rel(CASCADE_SCRIPT): sha256(CASCADE_SCRIPT), rel(cal_file): sha256(cal_file)}
    missing = [p for p, h in need.items() if h not in text]
    if missing:
        raise SystemExit(f"the freeze file {rel(f)} does not name the SHA-256 of {missing}")
    return {"freeze_file": rel(f), "sha256": sha256(f), "named": need}


# ------------------------------------------------------------------ command floor-fit
def build_fit(docs: dict, ood: set[str]) -> dict:
    """The tables and the calibration records of chapter 4 (without the threshold a and the measures)."""
    bunits, dunits, gaps = [], [], []
    for d in sorted(docs, key=int):
        r, lab = docs[d]["rules"], docs[d]["labels"]
        if r.get("split") != "dev":
            raise SystemExit(f"{d}: the rule file does not give the split dev: no fit (GJ.10)")
        ref = [b["option"] for b in lab["blocks"]]
        for b, o in zip(r["blocks"], ref, strict=True):
            bunits.append({"doc": d, "tier": b["tier"], "option": b["option"], "ref": o})
        opt, role, rid = d1_of_rule(r)
        dunits.append({"doc": d, "rule_id": rid, "rule_role": role, "option": opt, "ref": lab["d1"]})
        pred = set(switch_gaps([b["option"] for b in r["blocks"]]))
        refg = set(switch_gaps(ref))
        for i in range(len(ref) - 1):
            gaps.append({"doc": d, "gap": i, "pred": i in pred, "ref": i in refg})
    table = certainty_table(bunits, ood)
    s1 = s1_table(dunits, ood)
    sw = switch_table(gaps)
    return {"block_units": bunits, "d1_units": dunits, "gap_units": gaps, "certainty": table, "s1": s1, "switch": sw}


def base_record(kind: str, fit: dict, fit_n: int, params: list[tuple[str, float]], note: str) -> dict:
    return {"calibration_method": "jeffreys_tier_precision", "calibrated_kind": KIND_OF[kind],
            "fit_set_file": fit["path"], "fit_set_digest": fit["sha256"], "fit_n": int(fit_n),
            "reference_source": REFERENCE, "in_sample": True, "target_status": "not_measured",
            "calibration_parameters": [{"parameter_name": k, "parameter_value": r6(v)} for k, v in params],
            "calibration_note": note}


def entry_of(cid: str, k: int, n: int, confusion: dict, options, certain: bool = False) -> dict:
    return {"calibration": cid, "p": r6(jeffreys_mean(k, n)), "k": k, "n": n,
            "weights": {o: int(confusion.get(o, 0)) + 1 for o in options}, "certain": bool(certain)}


def build_calibrations(tabs: dict, fit: dict) -> tuple[dict, dict]:
    """(calibration records, floor_lookup)."""
    cals, lk = {}, {"version": FLOOR_VERSION,
                    "block": {"pairs": {}, "kinds": {}, "options": {}, "all": None},
                    "d1": {"rule_ids": {}, "all": None, "unsure_rule_ids": [NEEDS_APERTUS_ID]},
                    "switch": None,
                    "distribution": "p for the rule option; 1 - p for the other options in proportion to the dev "
                                    "confusion counts plus 1 (add-one); clip to [0.005, 0.995]; 4 decimals"}
    for row in tabs["certainty"]:
        cid = cal_id(FLOOR_VERSION, "block", row["tier"], row["option"])
        if cid in cals:
            raise SystemExit(f"two pairs give the calibration id {cid}")
        e = entry_of(cid, row["dev_correct"], row["dev_blocks"], row["confusion"], OPTIONS, row["certain"])
        lk["block"]["pairs"][pair_key(row["tier"], row["option"])] = e
        cals[cid] = base_record(
            "block", fit, row["dev_blocks"],
            [("jeffreys_posterior_mean", e["p"]), ("dev_correct", row["dev_correct"]), ("dev_blocks", row["dev_blocks"]),
             ("dev_documents", row["dev_documents"]), ("ood_correct", row["ood_correct"]),
             ("ood_blocks", row["ood_blocks"]), ("certain_pair", int(row["certain"]))]
            + [(f"weight_{o}", e["weights"][o]) for o in OPTIONS if o != row["option"]],
            f"rule tier {row['tier']}, rule option {row['option']}: Jeffreys posterior mean of the dev precision "
            f"(criteria 8.7 item 5); certain pair (criteria 8.7 item 2): {'yes' if row['certain'] else 'no'}")
    for level, key_fn, table in (("tier_kind", lambda u: (tier_kind(u["tier"]), u["option"]), "kinds"),
                                 ("option", lambda u: u["option"], "options"),
                                 ("all", lambda u: "all", "all")):
        for key, x in sorted(pooled_rows(tabs["block_units"], key_fn).items()):
            parts = key if isinstance(key, tuple) else (key,)
            cid = cal_id(FLOOR_VERSION, "block", "backoff", level, *([] if level == "all" else parts))
            # the backoff of all blocks has no rule option: its weights are the confusion counts plus 1
            opt = parts[-1] if level != "all" else None
            e = entry_of(cid, x["k"], x["n"], x["confusion"], OPTIONS)
            cals[cid] = base_record(
                "block", fit, x["n"],
                [("jeffreys_posterior_mean", e["p"]), ("dev_correct", x["k"]), ("dev_blocks", x["n"]),
                 ("dev_documents", len(x["docs"]))] + [(f"weight_{o}", e["weights"][o]) for o in OPTIONS if o != opt],
                f"backoff {level} {'/'.join(parts) if level != 'all' else '(all dev blocks)'}: only for a pair without "
                f"a dev block; never certain")
            if level == "all":
                lk["block"]["all"] = e
            else:
                lk["block"][table][pair_key(*parts) if level == "tier_kind" else parts[0]] = e
    for row in tabs["s1"]:
        cid = cal_id(FLOOR_VERSION, "d1", "s1", row["rule_id"])
        e = entry_of(cid, row["dev_correct"], row["dev_documents"], row["confusion"], D1_OPTIONS)
        lk["d1"]["rule_ids"][row["rule_id"]] = e
        note = (f"S1 rule id {row['rule_id']}: D1 option of the S1 rule role (map P3); Jeffreys posterior mean of the "
                f"dev precision against the reference D1")
        if row["needs_apertus"]:
            note += ("; the rule id R1 needs the D1 step: in floor mode the provisional rule role decides and the "
                     "value status is always unsure (no threshold a)")
        cals[cid] = base_record("d1", fit, row["dev_documents"],
                                [("jeffreys_posterior_mean", e["p"]), ("dev_correct", row["dev_correct"]),
                                 ("dev_documents", row["dev_documents"])]
                                + [(f"confusion_{o}", row["confusion"][o]) for o in D1_OPTIONS], note)
    k = sum(r["dev_correct"] for r in tabs["s1"])
    n = sum(r["dev_documents"] for r in tabs["s1"])
    conf = {o: sum(r["confusion"][o] for r in tabs["s1"]) for o in D1_OPTIONS}
    cid = cal_id(FLOOR_VERSION, "d1", "s1", "backoff", "all")
    lk["d1"]["all"] = entry_of(cid, k, n, conf, D1_OPTIONS)
    cals[cid] = base_record("d1", fit, n, [("jeffreys_posterior_mean", lk["d1"]["all"]["p"]), ("dev_correct", k),
                                           ("dev_documents", n)],
                            "backoff: S1 rule id without a dev document; pooled value of all dev documents")
    sw = tabs["switch"]
    cid = cal_id(FLOOR_VERSION, "switch", "rule_path")
    lk["switch"] = {"calibration": cid, "p": sw["jeffreys_mean"], "k": sw["correct"], "n": sw["rule_switch_boundaries"],
                    "p_gap_without_label": sw["p_gap_without_label"]}
    cals[cid] = base_record("switch", fit, sw["rule_switch_boundaries"],
                            [("jeffreys_posterior_mean", sw["jeffreys_mean"]), ("dev_correct", sw["correct"]),
                             ("dev_rule_switch_boundaries", sw["rule_switch_boundaries"]),
                             ("p_gap_without_label", sw["p_gap_without_label"]), ("dev_gaps", sw["gaps"])],
                            "switch boundary of the rule block path (criteria 2.5): Jeffreys posterior mean of the "
                            "precision on the dev reference switch boundaries; a gap without a switch label has the "
                            "switch probability p_gap_without_label in the measures (criteria 6.2 item 11)")
    return cals, lk


def floor_fit(args) -> int:
    scripts = [SCRIPT, CASCADE_SCRIPT, Path(guard.__file__).resolve()]
    rec = start_run_record(FIT_RUN, "floor converter F1: fit of the rule-tier probabilities on dev (in-sample)",
                           scripts)
    t0 = time.perf_counter()
    sets = read_json(SETS_FILE)
    ids = load_set("dev", ("dev",))
    ood = {str(d) for d in sets["dev_out_of_design"]}
    if not ood <= set(ids) or len(ood) != 48 or len(ids) != 193:
        raise SystemExit("the sets are not dev 193 and dev_out_of_design 48 (criteria 3)")
    docs = load_documents(ids)
    rules_d, labels_d, meta_d = stream_digests()
    fitset = {"schema": "parlpdfech-gj-fitset/1", "what": "fit set of the floor converter F1 (criteria 7.4, 8.7)",
              "set": "dev", "documents": ids, "dev_out_of_design": sorted(ood, key=int),
              "rule_files": {f"daten/gj/rules/{d}.json": rules_d[f"daten/gj/rules/{d}.json"] for d in ids},
              "label_files": {f"daten/gj/labels/{d}.json": labels_d[f"daten/gj/labels/{d}.json"] for d in ids},
              "run_records": meta_d, "reference": REFERENCE}
    write_json(FITSET_FILE, fitset)
    fit = {"path": rel(FITSET_FILE), "sha256": sha256(FITSET_FILE)}
    tabs = build_fit(docs, ood)
    cals, lk = build_calibrations(tabs, fit)
    cal = {"schema": "parlpdfech-gj-calibrations/1", "version": FLOOR_VERSION, "status": STATUS,
           "script": {"path": rel(SCRIPT), "sha256": sha256(SCRIPT), "version": VERSION},
           "fit_set": fit, "calibrations": cals, "floor_lookup": lk}
    # the floor values of each dev unit with the same function as src/m10_cascade.py
    import m10_cascade as cascade

    lookup = FloorLookup(cal)
    decs = {d: cascade.floor_decisions(docs[d]["rules"], lookup, in_sample=True, cal_info=None) for d in ids}
    labels = {d: docs[d]["labels"] for d in ids}
    u = units_of(decs, labels, lookup)
    thr = {"block_slot": threshold_a(u["blocks"]["pw"], u["blocks"]["okw"]),
           "document_text_parts": threshold_a(u["d1"]["pw"], u["d1"]["okw"]),
           "author_switch": threshold_a(u["switch_labels"]["pw"], u["switch_labels"]["okw"])}
    meas = kind_measures(u, ood)
    sets_of_kind = {"block_slot": ("block_slot", "dev in-sample (193 documents): all block labels of the floor F1"),
                    "document_text_parts": ("document_text_parts", "dev in-sample (193 documents): D1 labels of the "
                                                                   "floor F1"),
                    "author_switch": ("author_switch_all_gaps", "dev in-sample (193 documents): all gaps between two "
                                                                "blocks, switch probability of the floor F1")}
    for cid, c in cals.items():
        kind = c["calibrated_kind"]
        a = thr[kind]["a"]
        if a is not None and not (kind == "document_text_parts" and cid.endswith(f".s1.{NEEDS_APERTUS_ID}")):
            c["certain_threshold"] = a
        key, name = sets_of_kind[kind]
        c["measure_sets"] = [measure_set_record(name, meas[key])]
    cal["thresholds"] = {k: v["a"] for k, v in thr.items()}
    write_json(FLOOR_FILE, cal)
    certainty = {"schema": "parlpdfech-gj-certainty/1", "status": STATUS,
                 "what": "GJ.20 rule certainty table (criteria 8.7) on dev blocks; D1 values of the S1 rule ids; "
                         "switch-boundary precision of the rule block path; P17 thresholds; dev in-sample measures of "
                         "the floor F1 (information)",
                 "script": {"path": rel(SCRIPT), "sha256": sha256(SCRIPT)}, "fit_set": fit,
                 "conditions": {"precision": CERTAIN_PRECISION, "dev_documents": CERTAIN_DOCUMENTS,
                                "ood_precision": CERTAIN_PRECISION,
                                "ood_set": "dev_out_of_design (48 documents); no block = not certain (P9)"},
                 "certainty_table": tabs["certainty"],
                 "certain_pairs": [pair_key(r["tier"], r["option"]) for r in tabs["certainty"] if r["certain"]],
                 "s1_rule_ids_d1": tabs["s1"], "switch_boundary": tabs["switch"], "thresholds_a": thr,
                 "floor_measures_dev_in_sample": meas}
    write_json(CERTAINTY_FILE, certainty)
    outs = [FITSET_FILE, FLOOR_FILE, CERTAINTY_FILE]
    rec.update({"inputs": {**meta_d, "rule_files_and_label_files": fit},
                "outputs": {rel(p): sha256(p) for p in outs}, "seconds": round(time.perf_counter() - t0, 2),
                "summary": {"pairs": len(tabs["certainty"]), "certain_pairs": certainty["certain_pairs"],
                            "thresholds_a": cal["thresholds"], "calibration_records": len(cals),
                            "switch": {k: tabs["switch"][k] for k in ("rule_switch_boundaries", "correct",
                                                                      "jeffreys_mean", "p_gap_without_label")}},
                "limits": ["All values are dev in-sample values (criteria 8.6 item 4, 8.7 item 5): information only.",
                           "The reference is the AI reference, not a human reference (criteria 2.1)."]})
    finish_run_record(FIT_RUN, rec, scripts)
    print(json.dumps({"certain_pairs": certainty["certain_pairs"], "thresholds_a": cal["thresholds"],
                      "pairs": len(tabs["certainty"]), "records": len(cals),
                      "floor_v1": {"path": rel(FLOOR_FILE), "sha256": sha256(FLOOR_FILE)},
                      "certainty": {"path": rel(CERTAINTY_FILE), "sha256": sha256(CERTAINTY_FILE)},
                      "run": {"path": rel(FIT_RUN), "sha256": sha256(FIT_RUN)},
                      "frozen_files_different": rec["frozen_files"]["different"]}, indent=1))
    return 0


# ------------------------------------------------------------------ command measure
def measure_cmd(args) -> int:
    cal_file = Path(args.calibrations).resolve()
    scripts = [SCRIPT, CASCADE_SCRIPT]
    held = None
    if args.set in ("validation", "group7"):
        held = freeze_check(args.set, cal_file)
    out = Path(args.out) if args.out else CAL_RUNS / f"measure_{Path(args.decisions).name}_{args.set}.json"
    if not out.resolve().is_relative_to(GJ.resolve()):
        raise SystemExit("the output must be inside daten/gj")
    if held and out.exists():
        raise SystemExit(f"one-run rule (criteria 10.3): {rel(out)} exists")
    rec = start_run_record(out, f"measures of the decisions folder {rel(Path(args.decisions))} on the set {args.set}",
                           scripts)
    t0 = time.perf_counter()
    sets = read_json(SETS_FILE)
    ids = load_set(args.set, ("dev", "validation", "group7"))
    cal = read_json(cal_file)
    lookup = FloorLookup(cal) if "floor_lookup" in cal else None
    docs = load_documents(ids)
    decs, dec_sha = {}, {}
    for d in ids:
        p = guard.check_path(Path(args.decisions) / f"{d}.json")
        if not p.exists():
            raise SystemExit(f"{rel(p)}: missing decisions file")
        dec_sha[rel(p)] = sha256(p)
        decs[d] = read_json(p)
    u = units_of(decs, {d: docs[d]["labels"] for d in ids}, lookup)
    ood = {str(x) for x in sets["dev_out_of_design"]} if args.set == "dev" else None
    meas = kind_measures(u, ood)
    status = Counter()
    for d in ids:
        for b in decs[d]["blocks"]:
            t = cal["calibrations"][b["calibration"]].get("certain_threshold")
            status["block certain" if t is not None and as_written(b["probs"][b["option"]]) >= t else "block unsure"] += 1
    rec.update({"inputs": {"decisions_sha256_canonical": hashlib.sha256(json.dumps(dec_sha, sort_keys=True).encode())
                           .hexdigest(), "decisions_files": len(dec_sha),
                           rel(cal_file): sha256(cal_file), rel(SETS_FILE): sha256(SETS_FILE)},
                "held_out_run": held, "set": args.set, "documents": len(ids), "measures": meas,
                "value_status_of_block_labels": dict(status), "seconds": round(time.perf_counter() - t0, 2)})
    finish_run_record(out, rec, scripts)
    b, d1, g = meas["block_slot"], meas["document_text_parts"], meas["author_switch_all_gaps"]
    print(json.dumps({"set": args.set, "documents": len(ids),
                      "block_slot": {k: b[k] for k in ("n", "ece", "ece_equal_mass", "classwise_ece", "brier", "nll",
                                                       "wrong_at_0_99", "bootstrap")},
                      "d1": {k: d1[k] for k in ("n", "ece", "brier", "nll", "accuracy_top_label")},
                      "switch_gaps": {k: g[k] for k in ("n", "ece", "brier", "nll")},
                      "out": {"path": rel(out), "sha256": sha256(out)}}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="calibration library of gate GJ and the fit of the floor converter F1")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("floor-fit")
    m = sub.add_parser("measure")
    m.add_argument("--decisions", required=True)
    m.add_argument("--set", required=True, choices=["dev", "validation", "group7"])
    m.add_argument("--calibrations", default=str(FLOOR_FILE))
    m.add_argument("--out")
    a = ap.parse_args()
    try:
        code = floor_fit(a) if a.cmd == "floor-fit" else measure_cmd(a)
    except guard.GuardRefusal as ex:
        print(f"stopped (GuardRefusal): {ex}", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()

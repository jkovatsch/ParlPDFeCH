# SPDX-License-Identifier: Apache-2.0
"""Path 2 iteration 2 (E35), step 1: trained heads on the stored hidden states of Apertus-v1.5-8B (R1, R2).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5).
This file does not change an existing file. It only appends records to
daten/cls/it2/runs.jsonl. It runs no model: it reads the hidden states that src/m05_cls_it2_states.py stored
for dev documents and for the counterfactual pairs (bf16 forward pass, all 32 decoder layers).
Criteria: crisp-dm/04-modeling/gate-apertus-classification-criteria-v2.md (chapter 1.4) and addendum L
(gate-apertus-classification-criteria-v2-addendum-lora.md, chapter 4: partition P, values of the frozen recipe).

1 Inputs (dev only)
  daten/cls/it2/train_r1.csv             R1 rows (use, role, pool; fold = parliament)
  daten/cls/it2/pairs_r1.csv             254 pairs (pair_split train or heldout); texts in pairs_text/
  daten/cls/it2/extract_r2_sample.csv    the 800 R2 rows with stored states
  daten/cls/it2/states/r1|r2/<doc_id>.npz and states_pairs/r1/<pair_id>.npz
  daten/cls/text/<doc_id>.txt            model input text (rules and text SHA-256 check only)
  Before the first state is read, m05_cls_data.assert_allowed(ids, ("dev",)) examines each document id and
  each pair source. Each state file must have the frozen prompt variant, the template SHA-256 (GC.4
  definition of frozen_candidate.json), one model fingerprint, the layers 2 to 32 and the SHA-256 of its text.

2 Heads (the weights of the model do not change)
  Feature set: the stored state of one decoder layer (8, 12, 16, 20, 24, 28 or 32) at the last prompt token,
  or the concatenation of the layers 16, 24 and 32. Z-score with the mean and the standard deviation of the
  training rows of the fit. No other feature goes into a head: no length, no parliament, no language.
  Head lr:  softmax regression; minimize 0.5 * ||W||^2 + C * sum_i(w_i * CE_i); L-BFGS from zero.
  Head mlp: one hidden layer of 64 ReLU units (float32); minimize mean_i(w_i * CE_i) + lam * (||W1||^2 +
            ||W2||^2); L-BFGS (400 iterations); start values from numpy default_rng(20261011).
  w_i: class weights "balanced" of the training rows (mean 1). A pair has the same weight as a document.
  q: softmax of the head output. 2 options: the first option if q(first option) >= t (t = 0.5).
  3 options: the option with the highest q (equal values: the first in the option order).

3 Cross-validation on dev (design)
  Leave one parliament out: each fold holds one parliament with all its documents and all its pairs.
  R1 design rows: use = 1 and role = train (515 rows). The 62 rows with role = diag_heldout and their 62
  pairs (pair_split = heldout) never go into a design head: flip diagnosis only (data_it2.md 5.5).
  R1 option sets: H2 (recommended_for, recommended_against) trains on the labelled rows only; H3 also has
  the option none. Pair use: "nopairs", or "pairs" (the train pairs of the other parliaments go into the fit).
  R2 rows: the 800 rows of extract_r2_sample.csv (no R2 pairs exist).
  Grid: 8 feature sets x 6 heads (lr C = 0.001, 0.01, 0.1, 1; mlp lam = 0.01, 0.001); R1 also x 2 option
  sets x 2 pair uses. R1: 192 variants; R2: 48 variants.
  Diagnosis head ("design-all"): each R1 variant trained on all design rows (and the train pairs), for the
  62 held-out pairs (parliament known, both texts new) and the 63 rows with use = 0.
  Baselines on the same rows and folds: keyword (RX_REC), keyword_v2, keyword or none and keyword_v2 or none
  (no match gives none), heading, s1_answer, the iteration-1 zero-shot readout (stored probs, t = 0.5),
  and a length control (lr on log prompt tokens with the same folds; information only).

4 Selection rules: SELECTION_RULES below. The command register writes the SHA-256 of this file and the
  rules to daten/cls/it2/runs.jsonl. The command design refuses to start without such a record with the
  SHA-256 of this file (criteria v2, chapter 1.4, item 3; GC.23).

5 Freeze: the chosen variant of each task, trained once on all dev rows of the task (P18): R1 rows with use
  = 1 (577; H2: the 279 labelled rows) and all 254 pairs if the variant uses pairs; R2: the 800 rows.
  Output: daten/cls/it2/heads/<task>_head.npz and daten/cls/it2/frozen_it2.json (SHA-256 of the code, the
  states extractor, the engine, the head weights, the layers, t, a and the template).

6 Comparison values of addendum L (command compare, after the freeze): the frozen recipe trained again for
  each fold of partition P. Values on C1 (279 rows), F1 (254 pairs) and C2 (800 rows) with 6 decimals.
  Output: daten/cls/it2/compare_p_h.json, compare_p_h_r1.csv, compare_p_h_r2.csv.

Usage (from the project folder):
  .venv/bin/python src/m05_cls_it2_head.py selftest     synthetic data only (no state file, no label)
  .venv/bin/python src/m05_cls_it2_head.py register     record the SHA-256 and the rules in runs.jsonl
  .venv/bin/python src/m05_cls_it2_head.py design       grouped cross-validation, selection (dev)
  .venv/bin/python src/m05_cls_it2_head.py freeze       frozen heads and frozen_it2.json
  .venv/bin/python src/m05_cls_it2_head.py compare      values of the frozen recipe on partition P
  .venv/bin/python src/m05_cls_it2_head.py predict --task r1|r2 --states DIR --out FILE [--allow-validation]
         (values of the frozen head for stored state files; the validation run only after the freeze)
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m05_cls_data as cd  # noqa: E402
import m05_cls_apertus as ap  # noqa: E402
import m05_cls_verify_critic_counts as vcc  # noqa: E402

ROOT = cd.ROOT
IT2 = cd.OUT / "it2"
VERSION = "cls-it2-head-1"
SEED = 20261011
BOOT_SEED = 20261013
BOOT_N = 10000

CRITERIA = ROOT / "crisp-dm/04-modeling/gate-apertus-classification-criteria-v2.md"
CRITERIA_SHA = "82891c653633f98ef5fde2d44bba442d9372d1d774fc13e2ec213246c3316ef0"
ADDENDUM_L = ROOT / "crisp-dm/04-modeling/gate-apertus-classification-criteria-v2-addendum-lora.md"
ADDENDUM_C = ROOT / "crisp-dm/04-modeling/gate-apertus-classification-criteria-v2-addendum-cascade.md"
TRAIN_R1 = IT2 / "train_r1.csv"
TRAIN_R2 = IT2 / "train_r2.csv"
PAIRS = IT2 / "pairs_r1.csv"
PAIRS_TEXT = IT2 / "pairs_text"
R2_SAMPLE = IT2 / "extract_r2_sample.csv"
STATES = IT2 / "states"
STATES_PAIRS = IT2 / "states_pairs"
STATES_CODE = ROOT / "src/m05_cls_it2_states.py"
RUNS = IT2 / "runs.jsonl"
DESIGN_JSON = IT2 / "design_it2.json"
OOF_CSV = {"r1": IT2 / "design_oof_r1.csv", "r2": IT2 / "design_oof_r2.csv"}
HEADS_DIR = IT2 / "heads"
FROZEN = IT2 / "frozen_it2.json"
P_JSON = IT2 / "compare_p_h.json"
P_CSV = {"r1": IT2 / "compare_p_h_r1.csv", "r2": IT2 / "compare_p_h_r2.csv"}

VARIANT = {"r1": "r1_v1_i95_de", "r2": "r2_v1_de"}
TEMPLATE_SHA = {"r1": "1f507fa222971beff705bc3c76dce8082fd6f5c7dd9153621e6328ce15847547",
                "r2": "2a48e04bb8996dd331df38c79fa3121db63420b9c2e3eb5c8afaf053b8e5872e"}
STATE_LAYERS = tuple(range(2, 33, 2))
ZS_OPTIONS = {"r1": ("recommended_for", "recommended_against"), "r2": ("yes", "no")}

FEATURE_SETS = {"L8": (8,), "L12": (12,), "L16": (16,), "L20": (20,), "L24": (24,), "L28": (28,), "L32": (32,),
                "L16+L24+L32": (16, 24, 32)}
HEADS = (("lr", 0.001), ("lr", 0.01), ("lr", 0.1), ("lr", 1.0), ("mlp", 0.01), ("mlp", 0.001))
MLP_HIDDEN = 64
MLP_MAXITER = 400
LR_MAXITER = 3000
OPTION_SETS = {"H2": ("recommended_for", "recommended_against"),
               "H3": ("recommended_for", "recommended_against", "none")}
R1_EVAL = ("recommended_for", "recommended_against")
R2_OPTIONS = ("yes", "no")
PAIR_USES = ("pairs", "nopairs")
T = 0.5
A_GRID = (0.6, 0.7, 0.8, 0.9, 0.95, 0.99)
A_MIN = 0.95
A_COV = 0.50
R1_BAND = 0.02
R2_BAND = 0.01
NONE_N2_MIN = 0.80
NONE_N1_TOL = 0.02
NONE_RULE_POOLS = ("none_same_affair_proposal", "none_proposal_other")
ECE_BINS = 10
LENGTH_C = 1.0
# addendum L, chapter 4.2 (the script makes P again from its rules and compares)
P_FOLDS = {"r1": {"R1-1": ("1059",), "R1-2": ("261",), "R1-3": ("121", "4001", "BE")},
           "r2": {"R2-1": ("TI", "6421"), "R2-2": ("BE", "2581"), "R2-3": ("351", "743", "NW"),
                  "R2-4": ("5254", "2703", "4401"), "R2-5": ("230", "1059", "GL")}}

SELECTION_RULES = {
    "r1_measure": "S1 = out-of-fold macro F1 on the labelled R1 design rows (use 1, role train, label "
                  "recommended_for or recommended_against); a none decision is a false negative of the source option",
    "r1_steps": [
        "1. For each option set (H2, H3) separately: the band holds the variants with S1 >= max(S1) - 0.02 "
        "(values rounded to 6 decimals).",
        "2. In the band: the highest flip rate on the train pairs (out-of-fold: the head of the fold that holds "
        "the parliament of the pair; flipped = decision on the source is its label and decision on the copy is "
        "the pair label).",
        "3. Equal values: the higher out-of-fold accuracy on the labelled design rows; then the simpler variant "
        "(lr before mlp; 1 layer before 3 layers; stronger L2 first; lower layer first; pairs before nopairs).",
        "4. Option set (criteria v2, chapter 1.4, item 10): H3 if N2(H3) >= 0.80 and N1(H3) >= N1(H2) - 0.02, "
        "else H2. N1 = out-of-fold accuracy on the labelled design rows. N2 = out-of-fold share of none "
        "decisions on the none design rows of the pools none_same_affair_proposal and none_proposal_other "
        "(submitted texts of motions and postulates, criteria v2, chapter 1.4, item 7)."],
    "r2_measure": "S2 = out-of-fold balanced accuracy on the 800 R2 rows",
    "r2_steps": [
        "1. The band holds the variants with S2 >= max(S2) - 0.01 (values rounded to 6 decimals).",
        "2. In the band: the highest min(balanced accuracy of German rows, balanced accuracy of French rows), "
        "out-of-fold.",
        "3. Equal values: the higher out-of-fold macro F1; then the simpler variant (same order as R1)."],
    "t": "0.5 for 2 options (criteria v2, chapter 1.4, item 5); 3 options: the option with the highest q",
    "a": "criteria v2, chapter 1.4, item 6 (P17), on the out-of-fold values of the chosen variant: the smallest "
         "a of 0.6, 0.7, 0.8, 0.9, 0.95, 0.99 with (R1) accuracy >= 0.95 of the labelled design rows with "
         "max(q) >= a and coverage >= 0.50, (R2) balanced accuracy >= 0.95 of the rows with max(q) >= a and "
         "coverage >= 0.50 in each class. If no a meets the conditions: a = null (each value unsure).",
    "freeze": "the chosen variant trained once on all dev rows of the task: R1 rows with use 1 (H2: the "
              "labelled rows only) and all 254 pairs if the variant uses pairs; R2 the 800 rows",
    "comparison_p": "addendum L, chapter 4: the frozen recipe trained again for each fold of partition P; "
                    "values on C1 (279 rows), F1 (254 pairs) and C2 (800 rows), 6 decimals",
    "information_only": "baselines, bootstrap, length control, design-all diagnosis, per-fold values, "
                        "in-sample values",
}


# ---------------------------------------------------------------- helpers

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def sha256_dir(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(Path(d).iterdir()):
        h.update(p.name.encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def code_sha() -> str:
    return sha256_file(Path(__file__))


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def r6(x):
    return None if x is None else round(float(x), 6)


def read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(p: Path, rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def append_run(rec: dict) -> None:
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_npz(p: Path) -> dict:
    with np.load(p, allow_pickle=False) as z:
        return {k: (z[k].item() if z[k].ndim == 0 else z[k]) for k in z.files}


def log(msg: str) -> None:
    print(f"{dt.datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)


# ---------------------------------------------------------------- rules (baselines)

def rx_rec(t: str) -> str | None:
    """Last match of m05_cls_data.RX_REC (key keyword_answered of m05_cls_apertus.baseline_preds)."""
    ms = list(cd.RX_REC.finditer(t))
    return None if not ms else ("recommended_against" if ms[-1].group("against") else "recommended_for")


def kw2_answered(t: str) -> str | None:
    """keyword_v2 (m05_cls_verify_critic_counts.kw2) without the fallback: None if no sentence matches."""
    last = None
    for s in re.split(r"(?<=[.!?:])\s+|\n\s*\n", t):
        if vcc.KW2_AGAINST.search(s):
            last = "recommended_against"
        elif vcc.KW2_FOR.search(s):
            last = "recommended_for"
    return last


def r1_rules(t: str) -> dict:
    k1, k2 = rx_rec(t), kw2_answered(t)
    out = {"keyword": k1 or "recommended_against", "keyword_v2": k2 or "recommended_against",
           "keyword_or_none": k1 or "none", "keyword_v2_or_none": k2 or "none"}
    assert out["keyword_v2"] == vcc.kw2(t), "kw2_answered differs from kw2"
    return out


# ---------------------------------------------------------------- data

class Data:
    """Items (documents and pairs), features of the needed layers, zero-shot probs, prompt tokens, rules."""

    def __init__(self, task: str, items: list[dict], feats: dict, zs, ntok, rules: dict, meta: dict):
        self.task, self.items, self.F, self.zs, self.ntok, self.rules, self.meta = \
            task, items, feats, zs, ntok, rules, meta
        self.ix = {it["sid"]: i for i, it in enumerate(items)}
        assert len(self.ix) == len(items), "repeated item id"

    def X(self, fs: str, idx) -> np.ndarray:
        idx = np.asarray(idx, dtype=int)
        return np.hstack([self.F[k][idx] for k in FEATURE_SETS[fs]])


def needed_layers() -> tuple[int, ...]:
    return tuple(sorted({k for v in FEATURE_SETS.values() for k in v}))


def read_states(task: str, items: list[dict], texts: list[str]) -> tuple[dict, np.ndarray, np.ndarray, dict]:
    lays = needed_layers()
    n = len(items)
    F = {k: np.zeros((n, 4096), dtype=np.float32) for k in lays}
    zs = np.zeros((n, 2))
    ntok = np.zeros(n, dtype=np.int64)
    seen = collections.defaultdict(collections.Counter)
    for i, (it, t) in enumerate(zip(items, texts)):
        p = (STATES if it["kind"] == "doc" else STATES_PAIRS) / task / f"{it['sid']}.npz"
        z = load_npz(p)
        assert z["state_id"] == it["sid"] and z["doc_id"] == it["doc_id"] and z["task"] == task, p
        assert z["variant"] == VARIANT[task] and z["template_sha256"] == TEMPLATE_SHA[task], p
        assert tuple(int(x) for x in z["layers"]) == STATE_LAYERS and z["states"].shape == (16, 4096), p
        assert z["text_sha256"] == sha256_text(t), f"{p}: text SHA-256 differs from the text file"
        for k in lays:
            F[k][i] = z["states"][STATE_LAYERS.index(k)].astype(np.float32)
        zs[i] = z["probs"]
        ntok[i] = int(z["n_prompt_tokens"])
        for key in ("model_fingerprint", "code_sha256", "engine_code_sha256", "model"):
            seen[key][z[key]] += 1
    meta = {k: dict(v) for k, v in seen.items()}
    assert all(len(v) == 1 for v in meta.values()), f"more than one value: {meta}"
    for k in lays:
        assert np.isfinite(F[k]).all(), k
    return F, zs, ntok, {k: next(iter(v)) for k, v in meta.items()}


def load_r1() -> Data:
    rows = read_csv(TRAIN_R1)
    pairs = read_csv(PAIRS)
    ids = [r["doc_id"] for r in rows]
    assert len(ids) == len(set(ids))
    by = {r["doc_id"]: r for r in rows}
    assert {p["source_doc_id"] for p in pairs} <= set(ids), "pair source not in train_r1.csv"
    cd.assert_allowed(sorted(set(ids)), ("dev",))
    items, texts = [], []
    for r in rows:
        assert r["split"] == "dev" and r["fold"] == r["body_key"], r["doc_id"]
        items.append({"sid": r["doc_id"], "doc_id": r["doc_id"], "kind": "doc", "fold": r["fold"],
                      "label": r["label"], "use": int(r["use"]), "role": r["role"], "pool": r["pool"],
                      "language": r["language"], "length_class": r["length_class"], "split": ""})
        texts.append(cd.text(r["doc_id"]))
    other = {"recommended_for": "recommended_against", "recommended_against": "recommended_for"}
    for p in pairs:
        s = by[p["source_doc_id"]]
        assert s["label"] == p["source_label"] and p["pair_label"] == other[p["source_label"]], p["pair_id"]
        assert p["fold"] == s["fold"] and int(s["use"]) == 1, p["pair_id"]
        assert (p["pair_split"] == "heldout") == (s["role"] == "diag_heldout"), p["pair_id"]
        tp = (ROOT / p["pair_text_path"]).resolve()
        assert PAIRS_TEXT.resolve() in tp.parents, tp
        items.append({"sid": p["pair_id"], "doc_id": p["source_doc_id"], "kind": "pair", "fold": p["fold"],
                      "label": p["pair_label"], "source_label": p["source_label"], "use": 1, "role": "pair",
                      "pool": "pair", "language": p["language"], "length_class": s["length_class"],
                      "split": p["pair_split"]})
        texts.append(tp.read_text(encoding="utf-8"))
    F, zs, ntok, meta = read_states("r1", items, texts)
    rules = {it["sid"]: r1_rules(t) for it, t in zip(items, texts)}
    base = ap.baseline_preds("r1", [{"doc_id": r["doc_id"]} for r in rows])
    assert all(base["keyword"][d] == rules[d]["keyword"] for d in ids), "keyword rule differs from iteration 1"
    meta["inputs"] = {rel(TRAIN_R1): sha256_file(TRAIN_R1), rel(PAIRS): sha256_file(PAIRS),
                      rel(PAIRS_TEXT) + "/ (names and bytes)": sha256_dir(PAIRS_TEXT)}
    return Data("r1", items, F, zs, ntok, rules, meta)


def load_r2() -> Data:
    rows = read_csv(R2_SAMPLE)
    ids = [r["doc_id"] for r in rows]
    assert len(ids) == len(set(ids)) == 800
    cd.assert_allowed(ids, ("dev",))
    src = {r["doc_id"]: r for r in cd.rows("r2")}
    tr2 = {r["doc_id"]: r for r in read_csv(TRAIN_R2)}
    items, texts = [], []
    for r in rows:
        s = src[r["doc_id"]]
        assert s["split"] == "dev" and s["label"] == r["label"] and s["body_key"] == r["body_key"], r["doc_id"]
        assert tr2[r["doc_id"]]["label"] == r["label"], r["doc_id"]
        items.append({"sid": r["doc_id"], "doc_id": r["doc_id"], "kind": "doc", "fold": r["body_key"],
                      "label": r["label"], "use": 1, "role": "train", "pool": "", "language": r["language"],
                      "length_class": s["length_class"], "split": ""})
        texts.append(cd.text(r["doc_id"]))
    F, zs, ntok, meta = read_states("r2", items, texts)
    base = ap.baseline_preds("r2", [{"doc_id": d} for d in ids])
    rules = {d: {"heading": base["heading"][d], "s1_answer": base["s1_answer"][d]} for d in ids}
    meta["inputs"] = {rel(R2_SAMPLE): sha256_file(R2_SAMPLE), rel(TRAIN_R2): sha256_file(TRAIN_R2)}
    return Data("r2", items, F, zs, ntok, rules, meta)


# ---------------------------------------------------------------- heads

def lse(S: np.ndarray) -> np.ndarray:
    m = S.max(1, keepdims=True)
    return m + np.log(np.exp(S - m).sum(1, keepdims=True))


def class_weights(y: np.ndarray, K: int) -> np.ndarray:
    cnt = np.bincount(y, minlength=K)
    present = int((cnt > 0).sum())
    wc = np.where(cnt > 0, len(y) / (present * np.maximum(cnt, 1)), 0.0)
    return wc[y]


def _lr_obj(Z, Y, w, C):
    n, d = Z.shape
    K = Y.shape[1]

    def f(th):
        W = th[:d * K].reshape(d, K)
        b = th[d * K:]
        S = Z @ W + b
        lp = S - lse(S)
        loss = 0.5 * np.sum(W * W) + C * np.sum(w * -(Y * lp).sum(1))
        G = C * w[:, None] * (np.exp(lp) - Y)
        return float(loss), np.concatenate([(Z.T @ G + W).ravel(), G.sum(0)])
    return f


def _mlp_unpack(th, d, h, K):
    i = 0
    W1 = th[i:i + d * h].reshape(d, h)
    i += d * h
    b1 = th[i:i + h]
    i += h
    W2 = th[i:i + h * K].reshape(h, K)
    i += h * K
    return W1, b1, W2, th[i:]


def _mlp_obj(Z32, Y, w, lam):
    n, d = Z32.shape
    K = Y.shape[1]
    h = MLP_HIDDEN
    Yf, wf = Y.astype(np.float32), w.astype(np.float32)

    def f(th):
        W1, b1, W2, b2 = _mlp_unpack(th.astype(np.float32), d, h, K)
        A = Z32 @ W1 + b1
        H = np.maximum(A, 0)
        S = H @ W2 + b2
        lp = S - lse(S)
        loss = np.sum(wf * -(Yf * lp).sum(1)) / n + lam * (np.sum(W1 * W1) + np.sum(W2 * W2))
        G = wf[:, None] * (np.exp(lp) - Yf) / n
        gW2 = H.T @ G + 2 * lam * W2
        GH = (G @ W2.T) * (A > 0)
        gW1 = Z32.T @ GH + 2 * lam * W1
        return float(loss), np.concatenate([gW1.ravel(), GH.sum(0), gW2.ravel(), G.sum(0)]).astype(np.float64)
    return f


def _mlp_start(d: int, K: int) -> np.ndarray:
    h = MLP_HIDDEN
    rng = np.random.default_rng(SEED)
    l1, l2 = math.sqrt(6 / (d + h)), math.sqrt(6 / (h + K))
    return np.concatenate([rng.uniform(-l1, l1, d * h), np.zeros(h), rng.uniform(-l2, l2, h * K), np.zeros(K)])


def fit(kind: str, reg: float, X: np.ndarray, y: np.ndarray, K: int) -> dict:
    from scipy.optimize import minimize
    X = X.astype(np.float64)
    mu = X.mean(0)
    sd = X.std(0)
    sd = np.where(sd < 1e-6, 1.0, sd)
    Z = (X - mu) / sd
    w = class_weights(y, K)
    Y = np.eye(K)[y]
    d = Z.shape[1]
    if kind == "lr":
        r = minimize(_lr_obj(Z, Y, w, reg), np.zeros(d * K + K), jac=True, method="L-BFGS-B",
                     options={"maxiter": LR_MAXITER})
        par = {"W": r.x[:d * K].reshape(d, K), "b": r.x[d * K:]}
    else:
        r = minimize(_mlp_obj(Z.astype(np.float32), Y, w, reg), _mlp_start(d, K), jac=True, method="L-BFGS-B",
                     options={"maxiter": MLP_MAXITER})
        W1, b1, W2, b2 = _mlp_unpack(r.x.astype(np.float32), d, MLP_HIDDEN, K)
        par = {"W1": W1, "b1": b1, "W2": W2, "b2": b2}
    return {"kind": kind, "reg": reg, "K": K, "mu": mu, "sd": sd, **par, "nit": int(r.nit),
            "converged": bool(r.success), "fun": float(r.fun)}


def predict(head: dict, X: np.ndarray) -> np.ndarray:
    Z = (X.astype(np.float64) - head["mu"]) / head["sd"]
    if head["kind"] == "lr":
        S = Z @ head["W"] + head["b"]
    else:
        H = np.maximum(Z.astype(np.float32) @ head["W1"] + head["b1"], 0)
        S = (H @ head["W2"] + head["b2"]).astype(np.float64)
    return np.exp(S - lse(S))


def decide(q, opts: tuple[str, ...]) -> str:
    if len(opts) == 2:
        return opts[0] if q[0] >= T else opts[1]
    return opts[int(np.argmax(q))]


# ---------------------------------------------------------------- measures

def ece(conf: np.ndarray, correct: np.ndarray) -> float | None:
    """Top-label calibration error, 10 bins of equal width on max(q)."""
    if len(conf) == 0:
        return None
    b = np.minimum((conf * ECE_BINS).astype(int), ECE_BINS - 1)
    tot = 0.0
    for k in range(ECE_BINS):
        g = b == k
        if g.any():
            tot += g.mean() * abs(conf[g].mean() - correct[g].mean())
    return tot


def cls_metrics(y: list[str], yh: list[str], conf, opts: tuple[str, ...], mode: str) -> dict:
    """Values of decisions yh against labels y. opts: the source options; another decision (none) is a false
    negative. mode r1 or r2 selects the a rule. conf: max(q) for each row or None (rules)."""
    n = len(y)
    ya, yha = np.array(y, dtype=object), np.array(yh, dtype=object)
    corr = (ya == yha)
    m = {"n": n, "correct": int(corr.sum()), "accuracy": r6(corr.mean()) if n else None}
    f1s, recs = [], []
    for o in opts:
        tp = int(((ya == o) & (yha == o)).sum())
        n_o = int((ya == o).sum())
        pp = int((yha == o).sum())
        rec = tp / n_o if n_o else None
        prec = tp / pp if pp else None
        f1 = ((2 * prec * rec / (prec + rec) if prec and rec else 0.0) if n_o else None)
        m[f"n_{o}"], m[f"recall_{o}"], m[f"precision_{o}"], m[f"f1_{o}"] = n_o, r6(rec), r6(prec), r6(f1)
        if f1 is not None:
            f1s.append(f1)
        if rec is not None:
            recs.append(rec)
    m["macro_f1"] = r6(sum(f1s) / len(f1s)) if len(f1s) == len(opts) else None
    m["balanced_accuracy"] = r6(sum(recs) / len(recs)) if len(recs) == len(opts) else None
    m["other_decisions"] = sum(b not in opts for b in yh)
    if conf is None or n == 0:
        return m
    conf = np.asarray(conf, dtype=float)
    m["ece"] = r6(ece(conf, corr.astype(float)))
    tab = {}
    a_star = None
    for a in A_GRID:
        c = conf >= a
        cov = float(c.mean())
        acc_c = float(corr[c].mean()) if c.any() else None
        rc = [float(corr[c & (ya == o)].mean()) if (c & (ya == o)).any() else None for o in opts]
        ba_c = (sum(rc) / len(rc)) if all(x is not None for x in rc) else None
        cov_o = [float((c & (ya == o)).sum() / (ya == o).sum()) if (ya == o).any() else None for o in opts]
        if mode == "r1":
            ok = acc_c is not None and acc_c >= A_MIN and cov >= A_COV
        else:
            ok = ba_c is not None and ba_c >= A_MIN and all(x is not None and x >= A_COV for x in cov_o)
        tab[str(a)] = {"coverage": r6(cov), "certain_n": int(c.sum()), "certain_accuracy": r6(acc_c),
                       "certain_balanced_accuracy": r6(ba_c),
                       **{f"coverage_{o}": r6(x) for o, x in zip(opts, cov_o)}, "meets_rule": ok}
        if ok and a_star is None:
            a_star = a
    m["a_table"] = tab
    m["a_star"] = a_star
    return m


def flip_stats(pairs: list[dict], dec: dict) -> dict:
    n = len(pairs)
    if n == 0:
        return {"n": 0}
    src_ok = [dec[p["doc_id"]] == p["source_label"] for p in pairs]
    cp_ok = [dec[p["sid"]] == p["label"] for p in pairs]
    both = sum(a and b for a, b in zip(src_ok, cp_ok))
    same = sum(dec[p["doc_id"]] == dec[p["sid"]] for p in pairs)
    return {"n": n, "flipped": both, "flip_rate": r6(both / n), "unchanged": same, "unchanged_share": r6(same / n),
            "source_accuracy": r6(sum(src_ok) / n), "copy_accuracy": r6(sum(cp_ok) / n)}


def by_group(items: list[dict], dec: dict, key: str, opts: tuple[str, ...]) -> dict:
    g = collections.defaultdict(list)
    for it in items:
        g[it[key]].append(it)
    out = {}
    for k, v in sorted(g.items()):
        m = cls_metrics([x["label"] for x in v], [dec[x["sid"]] for x in v], None, opts, "r1")
        out[k] = {x: m[x] for x in ("n", "correct", "accuracy", "balanced_accuracy")}
    return out


def boot_gain(c_m: np.ndarray, c_rules: list[np.ndarray], y: np.ndarray | None) -> dict:
    """Paired bootstrap of (value of the method) - (highest value of the rules), the best rule chosen again in
    each resample (criteria v2, chapter 4.1, item 15). y None: accuracy; else balanced accuracy (y = 1 for the
    first option)."""
    n = len(c_m)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, n, size=(BOOT_N, n))

    def val(c, ii):
        cc = c[ii]
        if y is None:
            return cc.mean(-1)
        yy = y[ii]
        r1 = (cc * yy).sum(-1) / np.maximum(yy.sum(-1), 1)
        r0 = (cc * (1 - yy)).sum(-1) / np.maximum((1 - yy).sum(-1), 1)
        return (r1 + r0) / 2
    full = np.arange(n)
    point = val(c_m, full) - max(val(c, full) for c in c_rules)
    d = val(c_m, idx) - np.max(np.stack([val(c, idx) for c in c_rules]), axis=0)
    return {"point": r6(point), "bound_5pct": r6(np.quantile(d, 0.05)), "resamples": BOOT_N, "seed": BOOT_SEED}


# ---------------------------------------------------------------- variants

def variant_id(task, oset, pairs, fs, kind, reg) -> str:
    return f"{task}|{oset}|{pairs}|{fs}|{kind}|{reg:g}"


def parse_variant(vid: str) -> dict:
    task, oset, pairs, fs, kind, reg = vid.split("|")
    return {"task": task, "oset": oset, "pairs": pairs, "fs": fs, "kind": kind, "reg": float(reg)}


def simplicity(vid: str) -> tuple:
    v = parse_variant(vid)
    return (0 if v["kind"] == "lr" else 1, len(FEATURE_SETS[v["fs"]]),
            v["reg"] if v["kind"] == "lr" else -v["reg"], FEATURE_SETS[v["fs"]][0],
            0 if v["pairs"] in ("pairs", "-") else 1)


def options_of(vid: str) -> tuple[str, ...]:
    v = parse_variant(vid)
    return OPTION_SETS[v["oset"]] if v["task"] == "r1" else R2_OPTIONS


# ---------------------------------------------------------------- R1 design

def r1_sets(D: Data) -> dict:
    it = D.items
    s = {
        "D1": [i for i, x in enumerate(it) if x["kind"] == "doc" and x["use"] == 1 and x["role"] == "train"],
        "DH": [i for i, x in enumerate(it) if x["kind"] == "doc" and x["use"] == 1 and x["role"] == "diag_heldout"],
        "U0": [i for i, x in enumerate(it) if x["kind"] == "doc" and x["use"] == 0],
        "PT": [i for i, x in enumerate(it) if x["kind"] == "pair" and x["split"] == "train"],
        "PH": [i for i, x in enumerate(it) if x["kind"] == "pair" and x["split"] == "heldout"],
    }
    s["D1L"] = [i for i in s["D1"] if it[i]["label"] in R1_EVAL]
    s["D1N"] = [i for i in s["D1"] if it[i]["label"] == "none"]
    s["folds"] = sorted({it[i]["fold"] for i in s["D1"]})
    return s


def r1_fit_predict(D: Data, vid: str, train_idx: list[int], eval_idx: list[int]) -> tuple[dict, dict]:
    v = parse_variant(vid)
    opts = OPTION_SETS[v["oset"]]
    y = np.array([opts.index(D.items[i]["label"]) for i in train_idx])
    head = fit(v["kind"], v["reg"], D.X(v["fs"], train_idx), y, len(opts))
    q = predict(head, D.X(v["fs"], eval_idx))
    return {D.items[i]["sid"]: q[j] for j, i in enumerate(eval_idx)}, head


def r1_train_rows(D: Data, S: dict, vid: str, keep) -> list[int]:
    """Design training rows of a variant: design rows (H2: labelled only) and, with pairs, the train pairs,
    restricted to the items for which keep(item) is true."""
    v = parse_variant(vid)
    opts = OPTION_SETS[v["oset"]]
    tr = [i for i in S["D1"] if D.items[i]["label"] in opts and keep(D.items[i])]
    if v["pairs"] == "pairs":
        tr += [i for i in S["PT"] if keep(D.items[i])]
    return tr


def r1_oof(D: Data, S: dict, vid: str) -> tuple[dict, dict, dict]:
    """Out-of-fold q (leave one parliament out) for the design rows, the diag_heldout rows and all pairs;
    q of the design-all head for the diag_heldout rows, the held-out pairs and the use-0 rows."""
    q, info = {}, {"nit": [], "not_converged": 0}
    ev_all = S["D1"] + S["DH"] + S["PT"] + S["PH"]
    for P in S["folds"]:
        tr = r1_train_rows(D, S, vid, lambda x: x["fold"] != P)
        ev = [i for i in ev_all if D.items[i]["fold"] == P]
        qq, head = r1_fit_predict(D, vid, tr, ev)
        q.update(qq)
        info["nit"].append(head["nit"])
        info["not_converged"] += int(not head["converged"])
    tr = r1_train_rows(D, S, vid, lambda x: True)
    q_all, head = r1_fit_predict(D, vid, tr, S["DH"] + S["PH"] + S["U0"])
    info["nit_all"] = head["nit"]
    info["not_converged"] += int(not head["converged"])
    return q, q_all, info


def r1_eval(D: Data, S: dict, dec: dict, conf: dict | None, dec_all: dict | None) -> dict:
    """Values of R1 decisions. dec: out-of-fold decisions (design rows, diag_heldout rows, pairs).
    dec_all: decisions of the design-all head (diag_heldout rows, held-out pairs, use-0 rows) or None."""
    it = D.items
    L = [it[i] for i in S["D1L"]]
    cf = None if conf is None else [conf[x["sid"]] for x in L]
    m = {"main": cls_metrics([x["label"] for x in L], [dec[x["sid"]] for x in L], cf, R1_EVAL, "r1")}
    nn = [it[i] for i in S["D1N"]]
    rule_none = [x for x in nn if x["pool"] in NONE_RULE_POOLS]
    m["N1"] = m["main"]["accuracy"]
    m["N2"] = r6(sum(dec[x["sid"]] == "none" for x in rule_none) / len(rule_none))
    m["N2_n"] = len(rule_none)
    m["N2_all_none_rows"] = r6(sum(dec[x["sid"]] == "none" for x in nn) / len(nn))
    pools = collections.defaultdict(list)
    for x in nn:
        pools[x["pool"]].append(x)
    m["none_by_pool"] = {p: {"n": len(v), "none_decisions": sum(dec[x["sid"]] == "none" for x in v)}
                         for p, v in sorted(pools.items())}
    all3 = [it[i] for i in S["D1"]]
    m["accuracy_3_options_all_design_rows"] = r6(sum(dec[x["sid"]] == x["label"] for x in all3) / len(all3))
    m["per_fold"] = by_group(L, dec, "fold", R1_EVAL)
    m["per_length_class"] = by_group(L, dec, "length_class", R1_EVAL)
    pt = [it[i] for i in S["PT"]]
    ph = [it[i] for i in S["PH"]]
    m["flip_train_pairs_oof"] = flip_stats(pt, dec)
    m["flip_heldout_pairs_oof"] = flip_stats(ph, dec)
    m["flip_all_pairs_oof"] = flip_stats(pt + ph, dec)
    dh = [it[i] for i in S["DH"]]
    m["diag_heldout_rows_oof"] = {k: v for k, v in cls_metrics([x["label"] for x in dh], [dec[x["sid"]] for x in dh],
                                                                None, R1_EVAL, "r1").items()
                                  if k in ("n", "correct", "accuracy", "macro_f1", "other_decisions")}
    if dec_all is not None:
        m["flip_heldout_pairs_design_all_head"] = flip_stats(ph, dec_all)
        u0 = [it[i] for i in S["U0"]]
        m["use0_rows_design_all_head"] = {
            "n": len(u0), "decisions": dict(collections.Counter(dec_all[x["sid"]] for x in u0)),
            "none_rows_other_language": {
                "n": sum(x["label"] == "none" for x in u0),
                "none_decisions": sum(x["label"] == "none" and dec_all[x["sid"]] == "none" for x in u0)}}
    return m


def r1_baselines(D: Data, S: dict) -> dict:
    out = {}
    sids = [x["sid"] for x in D.items]
    for name in ("keyword", "keyword_v2", "keyword_or_none", "keyword_v2_or_none"):
        dec = {s: D.rules[s][name] for s in sids}
        out[name] = r1_eval(D, S, dec, None, dec)
    zq = {x["sid"]: D.zs[i] for i, x in enumerate(D.items)}
    dec = {s: decide(q, ZS_OPTIONS["r1"]) for s, q in zq.items()}
    conf = {s: float(max(q)) for s, q in zq.items()}
    out["zero_shot_it1"] = r1_eval(D, S, dec, conf, dec)
    for oset in ("H2", "H3"):
        opts = OPTION_SETS[oset]
        dec, conf = {}, {}
        Xl = np.log(D.ntok.astype(float))[:, None]
        ev_all = S["D1"] + S["DH"] + S["PT"] + S["PH"]
        for P in S["folds"]:
            tr = [i for i in S["D1"] if D.items[i]["label"] in opts and D.items[i]["fold"] != P]
            ev = [i for i in ev_all if D.items[i]["fold"] == P]
            h = fit("lr", LENGTH_C, Xl[tr], np.array([opts.index(D.items[i]["label"]) for i in tr]), len(opts))
            qq = predict(h, Xl[ev])
            for j, i in enumerate(ev):
                dec[D.items[i]["sid"]], conf[D.items[i]["sid"]] = decide(qq[j], opts), float(qq[j].max())
        out[f"length_control_{oset}"] = r1_eval(D, S, dec, conf, None)
    return out


def compact(m: dict) -> dict:
    """Short view of one variant for the variant table."""
    mm = m["main"]
    a = mm.get("a_star")
    at = mm["a_table"][str(a)] if a is not None else (mm.get("a_table") or {}).get("0.9")
    return {"accuracy": mm["accuracy"], "macro_f1": mm["macro_f1"], "balanced_accuracy": mm["balanced_accuracy"],
            "ece": mm.get("ece"), "a_star": a, "coverage_at_a": at and at["coverage"],
            "certain_accuracy_at_a": at and at["certain_accuracy"],
            "certain_balanced_accuracy_at_a": at and at["certain_balanced_accuracy"]}


def select_r1(res: dict) -> dict:
    out = {}
    for oset in ("H2", "H3"):
        vs = [v for v in res if parse_variant(v)["oset"] == oset]
        best = max(res[v]["main"]["macro_f1"] for v in vs)
        band = [v for v in vs if res[v]["main"]["macro_f1"] >= round(best - R1_BAND, 6)]
        key = lambda v: (-res[v]["flip_train_pairs_oof"]["flip_rate"], -res[v]["main"]["accuracy"],  # noqa: E731
                         simplicity(v))
        band.sort(key=key)
        out[oset] = {"best_S1": best, "band_limit": r6(best - R1_BAND), "band_size": len(band),
                     "band": [{"variant": v, "S1": res[v]["main"]["macro_f1"],
                               "flip_train": res[v]["flip_train_pairs_oof"]["flip_rate"],
                               "accuracy": res[v]["main"]["accuracy"]} for v in band[:12]],
                     "chosen": band[0]}
    h2, h3 = out["H2"]["chosen"], out["H3"]["chosen"]
    n1_2, n1_3, n2_3 = res[h2]["N1"], res[h3]["N1"], res[h3]["N2"]
    take3 = n2_3 >= NONE_N2_MIN and n1_3 >= round(n1_2 - NONE_N1_TOL, 6)
    out["none_rule"] = {"N1_H2": n1_2, "N1_H3": n1_3, "N2_H3": n2_3, "N2_n": res[h3]["N2_n"],
                        "condition_N2": n2_3 >= NONE_N2_MIN, "condition_N1": n1_3 >= round(n1_2 - NONE_N1_TOL, 6),
                        "option_set": "H3" if take3 else "H2"}
    out["chosen"] = h3 if take3 else h2
    return out


def design_r1(D: Data, feature_sets=None, heads=None) -> tuple[dict, dict]:
    S = r1_sets(D)
    fsets = feature_sets or list(FEATURE_SETS)
    hs = heads or list(HEADS)
    res, store = {}, {}
    t0 = time.time()
    vids = [variant_id("r1", o, p, fs, k, r) for o in OPTION_SETS for p in PAIR_USES for fs in fsets for k, r in hs]
    for j, vid in enumerate(vids, 1):
        opts = options_of(vid)
        q, q_all, info = r1_oof(D, S, vid)
        dec = {s: decide(x, opts) for s, x in q.items()}
        conf = {s: float(x.max()) for s, x in q.items()}
        dec_all = {s: decide(x, opts) for s, x in q_all.items()}
        res[vid] = r1_eval(D, S, dec, conf, dec_all)
        res[vid]["fit"] = {"nit_max": max(info["nit"]), "nit_all": info["nit_all"],
                           "not_converged": info["not_converged"]}
        store[vid] = (q, q_all)
        if j % 8 == 0 or j == len(vids):
            log(f"r1 {j}/{len(vids)} variants, {round(time.time() - t0)} s")
    sel = select_r1(res)
    base = r1_baselines(D, S)
    out = {"counts": {k: len(v) for k, v in S.items() if k != "folds"}, "folds": S["folds"],
           "variants": {v: {**compact(m), "N1": m["N1"], "N2": m["N2"],
                            "flip_train_pairs": m["flip_train_pairs_oof"]["flip_rate"],
                            "flip_heldout_pairs_oof": m["flip_heldout_pairs_oof"]["flip_rate"],
                            "flip_heldout_pairs_design_all": m["flip_heldout_pairs_design_all_head"]["flip_rate"],
                            "fit": m["fit"]} for v, m in res.items()},
           "selection": sel, "chosen": sel["chosen"],
           "chosen_values": res[sel["chosen"]],
           "chosen_H2_values": res[sel["H2"]["chosen"]], "chosen_H3_values": res[sel["H3"]["chosen"]],
           "baselines": base, "seconds": round(time.time() - t0, 1)}
    ch = sel["chosen"]
    out["a"] = res[ch]["main"]["a_star"]
    # information: bootstrap of the gain over the best rule and over the zero-shot readout (labelled design rows)
    L = [D.items[i] for i in S["D1L"]]
    q = store[ch][0]
    opts = options_of(ch)
    cm = np.array([decide(q[x["sid"]], opts) == x["label"] for x in L], dtype=float)
    cr = [np.array([D.rules[x["sid"]][r] == x["label"] for x in L], dtype=float) for r in ("keyword", "keyword_v2")]
    cz = np.array([decide(D.zs[D.ix[x["sid"]]], ZS_OPTIONS["r1"]) == x["label"] for x in L], dtype=float)
    out["bootstrap_accuracy"] = {"gain_over_best_rule": boot_gain(cm, cr, None),
                                 "gain_over_zero_shot_it1": boot_gain(cm, [cz], None)}
    # selection spread (information)
    s1 = sorted(m["main"]["macro_f1"] for m in res.values())
    out["spread_S1"] = {"min": s1[0], "median": s1[len(s1) // 2], "max": s1[-1]}
    return out, store


# ---------------------------------------------------------------- R2 design

def r2_eval(D: Data, dec: dict, conf: dict | None, idx=None) -> dict:
    items = [D.items[i] for i in (idx if idx is not None else range(len(D.items)))]
    cf = None if conf is None else [conf[x["sid"]] for x in items]
    m = {"main": cls_metrics([x["label"] for x in items], [dec[x["sid"]] for x in items], cf, R2_OPTIONS, "r2")}
    lang = collections.defaultdict(list)
    for x in items:
        lang[x["language"]].append(x)
    m["per_language"] = {k: {kk: vv for kk, vv in cls_metrics([x["label"] for x in v], [dec[x["sid"]] for x in v],
                                                              None, R2_OPTIONS, "r2").items()
                             if kk in ("n", "correct", "accuracy", "balanced_accuracy", "recall_yes", "recall_no")}
                         for k, v in sorted(lang.items())}
    m["min_ba_de_fr"] = min(m["per_language"].get(k, {}).get("balanced_accuracy") or 0.0 for k in ("de", "fr"))
    folds = collections.defaultdict(list)
    for x in items:
        folds[x["fold"]].append(x)
    m["per_fold"] = {k: {kk: vv for kk, vv in cls_metrics([x["label"] for x in v], [dec[x["sid"]] for x in v],
                                                          None, R2_OPTIONS, "r2").items()
                         if kk in ("n", "correct", "accuracy", "recall_yes", "recall_no")}
                     for k, v in sorted(folds.items())}
    m["per_length_class"] = by_group(items, dec, "length_class", R2_OPTIONS)
    return m


def r2_oof(D: Data, vid: str) -> tuple[dict, dict]:
    v = parse_variant(vid)
    folds = sorted({x["fold"] for x in D.items})
    q, info = {}, {"nit": [], "not_converged": 0}
    for P in folds:
        tr = [i for i, x in enumerate(D.items) if x["fold"] != P]
        ev = [i for i, x in enumerate(D.items) if x["fold"] == P]
        y = np.array([R2_OPTIONS.index(D.items[i]["label"]) for i in tr])
        head = fit(v["kind"], v["reg"], D.X(v["fs"], tr), y, 2)
        qq = predict(head, D.X(v["fs"], ev))
        q.update({D.items[i]["sid"]: qq[j] for j, i in enumerate(ev)})
        info["nit"].append(head["nit"])
        info["not_converged"] += int(not head["converged"])
    return q, info


def select_r2(res: dict) -> dict:
    vs = list(res)
    best = max(res[v]["main"]["balanced_accuracy"] for v in vs)
    band = [v for v in vs if res[v]["main"]["balanced_accuracy"] >= round(best - R2_BAND, 6)]
    band.sort(key=lambda v: (-res[v]["min_ba_de_fr"], -res[v]["main"]["macro_f1"], simplicity(v)))
    return {"best_S2": best, "band_limit": r6(best - R2_BAND), "band_size": len(band),
            "band": [{"variant": v, "S2": res[v]["main"]["balanced_accuracy"], "min_ba_de_fr": res[v]["min_ba_de_fr"],
                      "macro_f1": res[v]["main"]["macro_f1"]} for v in band[:12]],
            "chosen": band[0]}


def r2_baselines(D: Data) -> dict:
    out = {}
    for name in ("heading", "s1_answer"):
        out[name] = r2_eval(D, {s: D.rules[s][name] for s in D.rules}, None)
    zq = {x["sid"]: D.zs[i] for i, x in enumerate(D.items)}
    out["zero_shot_it1"] = r2_eval(D, {s: decide(q, R2_OPTIONS) for s, q in zq.items()},
                                   {s: float(max(q)) for s, q in zq.items()})
    Xl = np.log(D.ntok.astype(float))[:, None]
    dec, conf = {}, {}
    for P in sorted({x["fold"] for x in D.items}):
        tr = [i for i, x in enumerate(D.items) if x["fold"] != P]
        ev = [i for i, x in enumerate(D.items) if x["fold"] == P]
        h = fit("lr", LENGTH_C, Xl[tr], np.array([R2_OPTIONS.index(D.items[i]["label"]) for i in tr]), 2)
        qq = predict(h, Xl[ev])
        for j, i in enumerate(ev):
            dec[D.items[i]["sid"]], conf[D.items[i]["sid"]] = decide(qq[j], R2_OPTIONS), float(qq[j].max())
    out["length_control"] = r2_eval(D, dec, conf)
    return out


def design_r2(D: Data, feature_sets=None, heads=None) -> tuple[dict, dict]:
    fsets = feature_sets or list(FEATURE_SETS)
    hs = heads or list(HEADS)
    res, store = {}, {}
    t0 = time.time()
    vids = [variant_id("r2", "-", "-", fs, k, r) for fs in fsets for k, r in hs]
    for j, vid in enumerate(vids, 1):
        q, info = r2_oof(D, vid)
        res[vid] = r2_eval(D, {s: decide(x, R2_OPTIONS) for s, x in q.items()}, {s: float(x.max()) for s, x in q.items()})
        res[vid]["fit"] = {"nit_max": max(info["nit"]), "not_converged": info["not_converged"]}
        store[vid] = q
        if j % 6 == 0 or j == len(vids):
            log(f"r2 {j}/{len(vids)} variants, {round(time.time() - t0)} s")
    sel = select_r2(res)
    ch = sel["chosen"]
    out = {"counts": {"rows": len(D.items), **dict(collections.Counter(x["label"] for x in D.items))},
           "folds": sorted({x["fold"] for x in D.items}),
           "variants": {v: {**compact(m), "min_ba_de_fr": m["min_ba_de_fr"],
                            "ba_de": m["per_language"].get("de", {}).get("balanced_accuracy"),
                            "ba_fr": m["per_language"].get("fr", {}).get("balanced_accuracy"),
                            "ba_it": m["per_language"].get("it", {}).get("balanced_accuracy"),
                            "fit": m["fit"]} for v, m in res.items()},
           "selection": sel, "chosen": ch, "chosen_values": res[ch], "baselines": r2_baselines(D),
           "a": res[ch]["main"]["a_star"], "seconds": round(time.time() - t0, 1)}
    y = np.array([1.0 if x["label"] == "yes" else 0.0 for x in D.items])
    q = store[ch]
    cm = np.array([decide(q[x["sid"]], R2_OPTIONS) == x["label"] for x in D.items], dtype=float)
    cr = [np.array([D.rules[x["sid"]][r] == x["label"] for x in D.items], dtype=float) for r in ("heading", "s1_answer")]
    cz = np.array([decide(D.zs[i], R2_OPTIONS) == x["label"] for i, x in enumerate(D.items)], dtype=float)
    out["bootstrap_balanced_accuracy"] = {"gain_over_best_rule": boot_gain(cm, cr, y),
                                          "gain_over_zero_shot_it1": boot_gain(cm, [cz], y)}
    s2 = sorted(m["main"]["balanced_accuracy"] for m in res.values())
    out["spread_S2"] = {"min": s2[0], "median": s2[len(s2) // 2], "max": s2[-1]}
    return out, store


# ---------------------------------------------------------------- outputs of the design

def oof_rows_r1(D: Data, out: dict, store: dict) -> list[dict]:
    S = r1_sets(D)
    h2, h3 = out["selection"]["H2"]["chosen"], out["selection"]["H3"]["chosen"]
    rows = []
    for i in S["D1"] + S["DH"] + S["PT"] + S["PH"] + S["U0"]:
        x = D.items[i]
        s = x["sid"]
        rec = {"sid": s, "kind": x["kind"], "doc_id": x["doc_id"], "fold": x["fold"], "role": x["role"],
               "pair_split": x["split"], "pool": x["pool"], "use": x["use"], "label": x["label"]}
        for name, vid in (("h2", h2), ("h3", h3)):
            q, q_all = store[vid]
            qq = q.get(s)
            qa = q_all.get(s)
            opts = options_of(vid)
            for k, o in enumerate(opts):
                rec[f"{name}_oof_q_{o}"] = r6(qq[k]) if qq is not None else ""
            rec[f"{name}_oof_decision"] = decide(qq, opts) if qq is not None else ""
            rec[f"{name}_design_all_decision"] = decide(qa, opts) if qa is not None else ""
        rec["zero_shot_it1_p_for"] = r6(D.zs[i][0])
        for r in ("keyword", "keyword_v2", "keyword_or_none", "keyword_v2_or_none"):
            rec[r] = D.rules[s][r]
        rows.append(rec)
    return rows


def oof_rows_r2(D: Data, out: dict, store: dict) -> list[dict]:
    q = store[out["chosen"]]
    rows = []
    for i, x in enumerate(D.items):
        s = x["sid"]
        rows.append({"sid": s, "fold": x["fold"], "language": x["language"], "label": x["label"],
                     "oof_q_yes": r6(q[s][0]), "oof_decision": decide(q[s], R2_OPTIONS),
                     "zero_shot_it1_p_yes": r6(D.zs[i][0]), "heading": D.rules[s]["heading"],
                     "s1_answer": D.rules[s]["s1_answer"]})
    return rows


def last_register() -> dict | None:
    rec = None
    if RUNS.exists():
        for line in RUNS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                if x.get("step") == "head-design-rules":
                    rec = x
    return rec


def cmd_register() -> None:
    assert sha256_file(CRITERIA) == CRITERIA_SHA, "criteria v2 changed"
    if DESIGN_JSON.exists():
        raise SystemExit(f"{rel(DESIGN_JSON)} exists: the design ran already")
    rec = {"run": f"head-design-rules-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}", "step": "head-design-rules",
           "model_run": False, "purpose": "SHA-256 of the head design script with its selection rules, before the "
                                          "first out-of-fold value (criteria v2, chapter 1.4, item 3; GC.23)",
           "start": now(), "end": now(), "script": rel(Path(__file__)), "code_sha256": code_sha(),
           "version": VERSION, "criteria_file": rel(CRITERIA), "criteria_sha256": CRITERIA_SHA,
           "addendum_l_sha256": sha256_file(ADDENDUM_L), "addendum_c_sha256": sha256_file(ADDENDUM_C),
           "folds": "leave one parliament out (R1: parliaments of the design rows; R2: 13 parliaments)",
           "partition_p": P_FOLDS, "seed": SEED, "bootstrap_seed": BOOT_SEED,
           "grid": {"feature_sets": {k: list(v) for k, v in FEATURE_SETS.items()},
                    "heads": [list(h) for h in HEADS], "r1_option_sets": list(OPTION_SETS), "r1_pair_uses": list(PAIR_USES),
                    "mlp_hidden": MLP_HIDDEN, "mlp_maxiter": MLP_MAXITER, "lr_maxiter": LR_MAXITER},
           "selection_rules": SELECTION_RULES,
           "inputs": {rel(p): sha256_file(p) for p in (TRAIN_R1, PAIRS, R2_SAMPLE, TRAIN_R2)}}
    append_run(rec)
    print(json.dumps({k: rec[k] for k in ("run", "start", "code_sha256", "criteria_sha256")}, indent=1))


def cmd_design() -> None:
    reg = last_register()
    if not reg or reg["code_sha256"] != code_sha():
        raise SystemExit("no register record with the SHA-256 of this file in runs.jsonl: run the command register")
    if DESIGN_JSON.exists():
        raise SystemExit(f"{rel(DESIGN_JSON)} exists")
    t0 = time.time()
    start = now()
    log("load R1 and R2 states (dev)")
    D1 = load_r1()
    D2 = load_r2()
    assert D1.meta["model_fingerprint"] == D2.meta["model_fingerprint"]
    assert D1.meta["code_sha256"] == D2.meta["code_sha256"] == sha256_file(STATES_CODE), "states code changed"
    log("R1 design")
    o1, st1 = design_r1(D1)
    log("R2 design")
    o2, st2 = design_r2(D2)
    write_csv(OOF_CSV["r1"], oof_rows_r1(D1, o1, st1))
    write_csv(OOF_CSV["r2"], oof_rows_r2(D2, o2, st2))
    res = {"made": now(), "start": start, "version": VERSION, "status": "design on dev; not frozen",
           "code_sha256": code_sha(), "register_record": {k: reg[k] for k in ("run", "start", "code_sha256")},
           "criteria_sha256": CRITERIA_SHA, "states_code_sha256": D1.meta["code_sha256"],
           "engine_code_sha256": D1.meta["engine_code_sha256"], "model_fingerprint": D1.meta["model_fingerprint"],
           "model": D1.meta["model"], "template_sha256": TEMPLATE_SHA, "variant": VARIANT,
           "inputs": {**D1.meta["inputs"], **D2.meta["inputs"]}, "selection_rules": SELECTION_RULES,
           "grid": {"feature_sets": {k: list(v) for k, v in FEATURE_SETS.items()}, "heads": [list(h) for h in HEADS]},
           "r1": o1, "r2": o2, "oof_files": {t: {"file": rel(p), "sha256": sha256_file(p)} for t, p in OOF_CSV.items()},
           "seconds": round(time.time() - t0, 1)}
    DESIGN_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    append_run({"run": f"head-design-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}", "step": "head-design",
                "model_run": False, "purpose": "grouped cross-validation of the heads on stored dev states, selection",
                "start": start, "end": now(), "code_sha256": code_sha(), "output": rel(DESIGN_JSON),
                "output_sha256": sha256_file(DESIGN_JSON), "r1_chosen": o1["chosen"], "r2_chosen": o2["chosen"],
                "seconds": res["seconds"]})
    log(f"written {rel(DESIGN_JSON)}; R1 {o1['chosen']} a={o1['a']}; R2 {o2['chosen']} a={o2['a']}")


# ---------------------------------------------------------------- freeze and prediction

def save_head(p: Path, head: dict, meta: dict) -> None:
    arrays = {k: np.asarray(v) for k, v in head.items() if isinstance(v, np.ndarray)}
    arrays["meta_json"] = np.array(json.dumps(meta, sort_keys=True))
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez(p, **arrays)


def load_head(p: Path) -> tuple[dict, dict]:
    z = load_npz(p)
    meta = json.loads(z.pop("meta_json"))
    head = {**z, "kind": meta["kind"], "reg": meta["reg"], "K": len(meta["options"])}
    return head, meta


def features_from_state(z: dict, layers: tuple[int, ...]) -> np.ndarray:
    lay = tuple(int(x) for x in z["layers"])
    return np.concatenate([np.asarray(z["states"][lay.index(k)], dtype=np.float32) for k in layers])[None, :]


def predict_state(task: str, path: Path, frozen: dict, head: dict) -> dict:
    """Value of the frozen head for one stored state file (no model run)."""
    f = frozen["tasks"][task]
    z = load_npz(path)
    assert z["task"] == task and z["variant"] == f["prompt_variant"] and z["template_sha256"] == f["template_sha256"], path
    assert z["model_fingerprint"] == frozen["model_fingerprint"], path
    q = predict(head, features_from_state(z, tuple(f["layers"])))[0]
    opts = tuple(f["options"])
    a = f["a"]
    return {"state_id": z["state_id"], "doc_id": z["doc_id"], "q": {o: float(q[k]) for k, o in enumerate(opts)},
            "decision": decide(q, opts), "max_q": float(q.max()), "max_q_ge_a": bool(a is not None and q.max() >= a),
            "zero_shot_p_first": float(z["probs"][0]), "prompt_sha256": z["prompt_sha256"],
            "n_prompt_tokens": int(z["n_prompt_tokens"])}


def final_train_rows(D: Data, vid: str) -> list[int]:
    v = parse_variant(vid)
    if v["task"] == "r2":
        return list(range(len(D.items)))
    opts = OPTION_SETS[v["oset"]]
    tr = [i for i, x in enumerate(D.items) if x["kind"] == "doc" and x["use"] == 1 and x["label"] in opts]
    if v["pairs"] == "pairs":
        tr += [i for i, x in enumerate(D.items) if x["kind"] == "pair"]
    return tr


def cmd_freeze() -> None:
    des = json.loads(DESIGN_JSON.read_text(encoding="utf-8"))
    if des["code_sha256"] != code_sha():
        raise SystemExit("design_it2.json comes from another version of this file")
    if FROZEN.exists():
        raise SystemExit(f"{rel(FROZEN)} exists")
    start = now()
    data = {"r1": load_r1(), "r2": load_r2()}
    tasks = {}
    for task, D in data.items():
        vid = des[task]["chosen"]
        v = parse_variant(vid)
        opts = options_of(vid)
        tr = final_train_rows(D, vid)
        y = np.array([opts.index(D.items[i]["label"]) for i in tr])
        head = fit(v["kind"], v["reg"], D.X(v["fs"], tr), y, len(opts))
        a = des[task]["a"]
        ids = sorted(D.items[i]["sid"] for i in tr)
        meta = {"task": task, "variant_id": vid, "kind": v["kind"], "reg": v["reg"], "options": list(opts),
                "layers": list(FEATURE_SETS[v["fs"]]), "feature_set": v["fs"], "t": T, "a": a,
                "train_rows": len(tr), "train_ids_sha256": sha256_text("\n".join(ids)), "version": VERSION,
                "code_sha256": code_sha()}
        p = HEADS_DIR / f"{task}_head.npz"
        save_head(p, head, meta)
        h2, m2 = load_head(p)
        q_mem = predict(head, D.X(v["fs"], tr))
        q_file = predict(h2, D.X(v["fs"], tr))
        assert np.array_equal(q_mem, q_file), "head file gives other values"
        # the prediction path from the stored state files gives the same values (first 25 rows)
        fz_probe = {"tasks": {task: {"prompt_variant": VARIANT[task], "template_sha256": TEMPLATE_SHA[task],
                                     "layers": meta["layers"], "options": list(opts), "a": a}},
                    "model_fingerprint": D.meta["model_fingerprint"]}
        diff = 0.0
        for j, i in enumerate(tr[:25]):
            it = D.items[i]
            sp = (STATES if it["kind"] == "doc" else STATES_PAIRS) / task / f"{it['sid']}.npz"
            r = predict_state(task, sp, fz_probe, h2)
            diff = max(diff, max(abs(r["q"][o] - q_mem[j][k]) for k, o in enumerate(opts)))
        assert diff == 0.0, f"state-file path differs: {diff}"
        dec = [decide(x, opts) for x in q_mem]
        ins = cls_metrics([D.items[i]["label"] for i in tr], dec, q_mem.max(1), opts, task)
        kinds = collections.Counter(D.items[i]["kind"] for i in tr)
        tasks[task] = {
            "variant_id": vid, "prompt_variant": VARIANT[task], "template_sha256": TEMPLATE_SHA[task],
            "options": list(opts), "option_set": v["oset"] if task == "r1" else "yes/no",
            "pairs_used": v["pairs"] == "pairs" if task == "r1" else False,
            "feature_set": v["fs"], "layers": list(FEATURE_SETS[v["fs"]]),
            "feature_rule": "stored residual-stream state at the last prompt token (output of the decoder layer, before "
                            "the final norm), float16 file value as float32; layers concatenated in this order; z-score "
                            "with mu and sd of the head file",
            "head": {"kind": v["kind"], "reg": v["reg"], "mlp_hidden": MLP_HIDDEN if v["kind"] == "mlp" else None,
                     "iterations": head["nit"], "converged": head["converged"]},
            "t": T, "a": a, "a_table_oof": des[task]["chosen_values"]["main"]["a_table"],
            "decision_rule": "2 options: first option if q(first) >= t; 3 options: highest q",
            "value_status_rule": "certain only if max(q) >= a and GC.14 (R1) or GC.17 (R2) is MET; else unsure",
            "training": {"rows": len(tr), "documents": kinds.get("doc", 0), "pairs": kinds.get("pair", 0),
                         "by_label": dict(collections.Counter(D.items[i]["label"] for i in tr)),
                         "ids_sha256": meta["train_ids_sha256"]},
            "weights_file": rel(p), "weights_sha256": sha256_file(p),
            "in_sample_information": {k: ins[k] for k in ("n", "accuracy", "macro_f1", "balanced_accuracy", "ece")},
            "oof_values": compact(des[task]["chosen_values"]),
            "check_state_file_path_max_abs_diff_q": diff}
    fr = {"made": now(), "start": start, "version": VERSION,
          "status": "frozen recipe and heads of candidate H (design on dev only). GC.1 is OPEN. Not RELEASED.",
          "code": {rel(Path(__file__)): code_sha(), rel(STATES_CODE): sha256_file(STATES_CODE),
                   "src/m05_cls_apertus.py": sha256_file(ROOT / "src/m05_cls_apertus.py"),
                   "src/m05_cls_data.py": sha256_file(ROOT / "src/m05_cls_data.py")},
          "states_code_sha256_in_state_files": des["states_code_sha256"],
          "engine_code_sha256_in_state_files": des["engine_code_sha256"],
          "model": des["model"], "model_fingerprint": des["model_fingerprint"], "precision": "bf16",
          "all_decoder_layers_run": 32, "prefill_chunk": ap.PREFILL_CHUNK, "max_text_tokens": ap.MAX_TEXT_TOKENS,
          "prefill_rule": "m05_cls_it2_states.StateEngine.pass_one: prefill of ids[:-1] in chunks of 2048 tokens from "
                          "position 0 (one prompt for each pass), then the last prompt token alone, layer by layer",
          "template_sha256_definition": "template_sha256 of m05_cls_apertus.build() (GC.4 definition of "
                                        "frozen_candidate.json)",
          "criteria": {rel(CRITERIA): CRITERIA_SHA, rel(ADDENDUM_L): sha256_file(ADDENDUM_L),
                       rel(ADDENDUM_C): sha256_file(ADDENDUM_C)},
          "design": {"file": rel(DESIGN_JSON), "sha256": sha256_file(DESIGN_JSON),
                     "register_record": des["register_record"],
                     "oof_files": des["oof_files"]},
          "inputs": des["inputs"], "tasks": tasks,
          "apply": "src/m05_cls_it2_head.py predict --task <task> --states <dir of state files> --out <file>; "
                   "the state files come from src/m05_cls_it2_states.py (same variant, template and layers)"}
    FROZEN.write_text(json.dumps(fr, indent=1, ensure_ascii=False), encoding="utf-8")
    append_run({"run": f"head-freeze-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}", "step": "head-freeze",
                "model_run": False, "purpose": "frozen heads of candidate H on all dev rows", "start": start,
                "end": now(), "code_sha256": code_sha(), "output": rel(FROZEN), "output_sha256": sha256_file(FROZEN),
                "weights_sha256": {t: tasks[t]["weights_sha256"] for t in tasks}})
    log(f"written {rel(FROZEN)}")


# ---------------------------------------------------------------- comparison values on partition P (addendum L)

def partition_p(D: Data, task: str) -> dict:
    """Make P again from the rules of addendum L, chapter 4.2, and compare with P_FOLDS."""
    if task == "r1":
        c1 = collections.Counter(x["fold"] for x in D.items if x["kind"] == "doc" and x["use"] == 1
                                 and x["label"] in R1_EVAL)
        big = sorted(f for f, n in c1.items() if n >= 20)
        small = tuple(sorted(f for f, n in c1.items() if n < 20))
        made = {f"R1-{j + 1}": (f,) for j, f in enumerate(sorted(big, key=lambda f: -c1[f]))}
        made[f"R1-{len(big) + 1}"] = small
    else:
        c2 = collections.Counter(x["fold"] for x in D.items)
        made = {f"R2-{j}": [] for j in range(1, 6)}
        size = {k: 0 for k in made}
        for f in sorted(c2, key=lambda f: (-c2[f], f)):
            k = min(size, key=lambda k: (size[k], int(k.split("-")[1])))
            made[k].append(f)
            size[k] += c2[f]
        made = {k: tuple(v) for k, v in made.items()}
    want = {k: tuple(v) for k, v in P_FOLDS[task].items()}
    if task == "r1":   # the rule of addendum L gives the folds, the table of addendum L gives their names
        same = sorted(tuple(sorted(v)) for v in made.values()) == sorted(tuple(sorted(v)) for v in want.values())
    else:
        same = {k: tuple(sorted(v)) for k, v in made.items()} == {k: tuple(sorted(v)) for k, v in want.items()}
    assert same, f"partition P differs: {made}"
    return want


def cmd_compare() -> None:
    fr = json.loads(FROZEN.read_text(encoding="utf-8"))
    if fr["code"][rel(Path(__file__))] != code_sha():
        raise SystemExit("frozen_it2.json comes from another version of this file")
    start = now()
    out = {"made": None, "start": start, "version": VERSION, "code_sha256": code_sha(),
           "frozen_file": rel(FROZEN), "frozen_sha256": sha256_file(FROZEN), "candidate": "H",
           "rule": SELECTION_RULES["comparison_p"], "partition_p": P_FOLDS, "tasks": {}}
    for task in ("r1", "r2"):
        D = load_r1() if task == "r1" else load_r2()
        P = partition_p(D, task)
        f = fr["tasks"][task]
        vid = f["variant_id"]
        v = parse_variant(vid)
        opts = tuple(f["options"])
        q, fold_of, fits = {}, {}, {}
        for fold, parls in P.items():
            held = set(parls)
            tr = [i for i in final_train_rows(D, vid) if D.items[i]["fold"] not in held]
            ev = [i for i, x in enumerate(D.items) if x["fold"] in held and x["use"] == 1]
            y = np.array([opts.index(D.items[i]["label"]) for i in tr])
            head = fit(v["kind"], v["reg"], D.X(v["fs"], tr), y, len(opts))
            qq = predict(head, D.X(v["fs"], ev))
            for j, i in enumerate(ev):
                q[D.items[i]["sid"]] = qq[j]
                fold_of[D.items[i]["sid"]] = fold
            fits[fold] = {"train_rows": len(tr), "held_out_rows": len(ev), "iterations": head["nit"],
                          "converged": head["converged"]}
        dec = {s: decide(x, opts) for s, x in q.items()}
        rows, vals = [], {"fits": fits}
        if task == "r1":
            c1 = [x for x in D.items if x["kind"] == "doc" and x["use"] == 1 and x["label"] in R1_EVAL]
            f1 = [x for x in D.items if x["kind"] == "pair"]
            nn = [x for x in D.items if x["kind"] == "doc" and x["use"] == 1 and x["label"] == "none" and x["sid"] in q]

            def r1_vals(c1s, f1s, nns):
                m = cls_metrics([x["label"] for x in c1s], [dec[x["sid"]] for x in c1s],
                                [float(q[x["sid"]].max()) for x in c1s], R1_EVAL, "r1")
                fl = flip_stats(f1s, dec)
                rule = [x for x in nns if x["pool"] in NONE_RULE_POOLS]
                return {"n_C1": len(c1s), "M_R1_macro_f1": m["macro_f1"], "accuracy": m["accuracy"], "N1": m["accuracy"],
                        "balanced_accuracy": m["balanced_accuracy"], "recall_recommended_for": m["recall_recommended_for"],
                        "recall_recommended_against": m["recall_recommended_against"],
                        "none_decisions_on_C1": m["other_decisions"], "n_F1": fl["n"],
                        "FR_flip_rate": fl.get("flip_rate"), "flipped": fl.get("flipped"),
                        "unchanged_share": fl.get("unchanged_share"),
                        "n_none_rows_held_out": len(nns),
                        "N2_all_held_out_none_rows": r6(sum(dec[x["sid"]] == "none" for x in nns) / len(nns)) if nns else None,
                        "N2_rule_pools": r6(sum(dec[x["sid"]] == "none" for x in rule) / len(rule)) if rule else None,
                        "n_rule_pool_rows": len(rule), "ece": m.get("ece")}
            vals["all"] = r1_vals(c1, f1, nn)
            assert vals["all"]["n_C1"] == 279 and vals["all"]["n_F1"] == 254, vals["all"]
            vals["all"]["FR_flip_rate_over_254"] = r6(vals["all"]["flipped"] / 254)
            vals["per_fold"] = {fd: r1_vals([x for x in c1 if fold_of[x["sid"]] == fd],
                                            [x for x in f1 if fold_of[x["sid"]] == fd],
                                            [x for x in nn if fold_of[x["sid"]] == fd]) for fd in P}
            vals["pairs_heldout_split_information"] = flip_stats([x for x in f1 if x["split"] == "heldout"], dec)
            base = {}
            for name in ("keyword", "keyword_v2"):
                bd = {x["sid"]: D.rules[x["sid"]][name] for x in D.items}
                mb = cls_metrics([x["label"] for x in c1], [bd[x["sid"]] for x in c1], None, R1_EVAL, "r1")
                base[name] = {"M_R1_macro_f1": mb["macro_f1"], "accuracy": mb["accuracy"],
                              "FR_flip_rate": flip_stats(f1, bd)["flip_rate"]}
            zd = {x["sid"]: decide(D.zs[i], ZS_OPTIONS["r1"]) for i, x in enumerate(D.items)}
            mz = cls_metrics([x["label"] for x in c1], [zd[x["sid"]] for x in c1], None, R1_EVAL, "r1")
            base["zero_shot_it1"] = {"M_R1_macro_f1": mz["macro_f1"], "accuracy": mz["accuracy"],
                                     "FR_flip_rate": flip_stats(f1, zd)["flip_rate"]}
            vals["baselines_information"] = base
            for x in D.items:
                if x["sid"] not in q:
                    continue
                i = D.ix[x["sid"]]
                rec = {"sid": x["sid"], "kind": x["kind"], "doc_id": x["doc_id"], "parliament": x["fold"],
                       "fold_p": fold_of[x["sid"]], "pool": x["pool"], "pair_split": x["split"], "label": x["label"]}
                rec.update({f"q_{o}": r6(q[x["sid"]][k]) for k, o in enumerate(opts)})
                rec["decision"] = dec[x["sid"]]
                rec["zero_shot_it1_p_for"] = r6(D.zs[i][0])
                rec.update({r: D.rules[x["sid"]][r] for r in ("keyword", "keyword_v2")})
                rows.append(rec)
        else:
            c2 = D.items

            def r2_vals(items):
                m = cls_metrics([x["label"] for x in items], [dec[x["sid"]] for x in items],
                                [float(q[x["sid"]].max()) for x in items], R2_OPTIONS, "r2")
                return {"n_C2": len(items), "M_R2_balanced_accuracy": m["balanced_accuracy"],
                        "recall_yes": m["recall_yes"], "recall_no": m["recall_no"], "accuracy": m["accuracy"],
                        "macro_f1": m["macro_f1"], "ece": m.get("ece")}
            vals["all"] = r2_vals(c2)
            assert vals["all"]["n_C2"] == 800
            vals["per_fold"] = {fd: r2_vals([x for x in c2 if fold_of[x["sid"]] == fd]) for fd in P}
            base = {}
            for name in ("heading", "s1_answer"):
                mb = cls_metrics([x["label"] for x in c2], [D.rules[x["sid"]][name] for x in c2], None, R2_OPTIONS, "r2")
                base[name] = {"M_R2_balanced_accuracy": mb["balanced_accuracy"], "recall_yes": mb["recall_yes"],
                              "recall_no": mb["recall_no"]}
            mz = cls_metrics([x["label"] for x in c2], [decide(D.zs[i], R2_OPTIONS) for i, x in enumerate(c2)],
                             None, R2_OPTIONS, "r2")
            base["zero_shot_it1"] = {"M_R2_balanced_accuracy": mz["balanced_accuracy"], "recall_yes": mz["recall_yes"],
                                     "recall_no": mz["recall_no"]}
            vals["baselines_information"] = base
            for i, x in enumerate(c2):
                rows.append({"sid": x["sid"], "parliament": x["fold"], "fold_p": fold_of[x["sid"]],
                             "language": x["language"], "label": x["label"], "q_yes": r6(q[x["sid"]][0]),
                             "decision": dec[x["sid"]], "zero_shot_it1_p_yes": r6(D.zs[i][0]),
                             "heading": D.rules[x["sid"]]["heading"], "s1_answer": D.rules[x["sid"]]["s1_answer"]})
        write_csv(P_CSV[task], rows)
        out["tasks"][task] = {"variant_id": vid, "options": list(opts), "t": T, **vals,
                              "rows_file": rel(P_CSV[task]), "rows_sha256": sha256_file(P_CSV[task])}
    out["made"] = now()
    P_JSON.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    append_run({"run": f"head-compare-p-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}", "step": "head-compare-p",
                "model_run": False, "purpose": "values of the frozen H recipe on partition P (addendum L, chapter 4)",
                "start": start, "end": now(), "code_sha256": code_sha(), "output": rel(P_JSON),
                "output_sha256": sha256_file(P_JSON)})
    log(f"written {rel(P_JSON)}")


def cmd_predict(task: str, states_dir: str, out_file: str, allow_validation: bool) -> None:
    fr = json.loads(FROZEN.read_text(encoding="utf-8"))
    head, meta = load_head(ROOT / fr["tasks"][task]["weights_file"])
    assert sha256_file(ROOT / fr["tasks"][task]["weights_file"]) == fr["tasks"][task]["weights_sha256"]
    assert fr["code"][rel(Path(__file__))] == code_sha(), "head code differs from the frozen code"
    files = sorted(Path(states_dir).glob("*.npz"))
    docs = sorted({str(load_npz(p)["doc_id"]) for p in files})
    cd.assert_allowed(docs, ("dev", "validation") if allow_validation else ("dev",))
    op = Path(out_file)
    if op.exists():
        raise SystemExit(f"{op} exists")
    with open(op, "w", encoding="utf-8") as f:
        for p in files:
            f.write(json.dumps(predict_state(task, p, fr, head), ensure_ascii=False) + "\n")
    print(f"{len(files)} values written to {op}")


# ---------------------------------------------------------------- self-test (synthetic data only)

def synthetic(task: str, seed: int = 7) -> Data:
    rng = np.random.default_rng(seed)
    items = []
    if task == "r1":
        folds = ["A", "B", "C", "D"]
        for f in folds:
            for j in range(30):
                lab = ("recommended_for", "recommended_against", "none")[j % 3]
                role = "diag_heldout" if (j < 3 and lab != "none") else "train"
                pool = NONE_RULE_POOLS[j % 2] if lab == "none" else "r1_source_label"
                items.append({"sid": f"{f}{j}", "doc_id": f"{f}{j}", "kind": "doc", "fold": f, "label": lab, "use": 1,
                              "role": role, "pool": pool, "language": "de", "length_class": "le8192", "split": ""})
        items.append({"sid": "U1", "doc_id": "U1", "kind": "doc", "fold": "A", "label": "none", "use": 0,
                      "role": "train", "pool": "x", "language": "fr", "length_class": "le8192", "split": ""})
        src = [x for x in items if x["label"] in R1_EVAL and x["use"] == 1]
        for x in src[::2]:
            other = "recommended_for" if x["label"] == "recommended_against" else "recommended_against"
            items.append({"sid": "p" + x["sid"], "doc_id": x["sid"], "kind": "pair", "fold": x["fold"], "label": other,
                          "source_label": x["label"], "use": 1, "role": "pair", "pool": "pair", "language": "de",
                          "length_class": "le8192", "split": "heldout" if x["role"] == "diag_heldout" else "train"})
        cls = {"recommended_for": 0, "recommended_against": 1, "none": 2}
    else:
        for f in ["A", "B", "C", "D", "E"]:
            for j in range(40):
                items.append({"sid": f"{f}{j}", "doc_id": f"{f}{j}", "kind": "doc", "fold": f,
                              "label": R2_OPTIONS[j % 2], "use": 1, "role": "train", "pool": "",
                              "language": ("de", "fr", "it")[j % 3], "length_class": "le8192", "split": ""})
        cls = {"yes": 0, "no": 1}
    n = len(items)
    dirs = rng.standard_normal((3, 4096))
    F = {}
    for k in needed_layers():
        base = rng.standard_normal((n, 4096)).astype(np.float32)
        sig = np.stack([dirs[cls[x["label"]]] for x in items]) * (0.05 * k / 32)
        F[k] = (base + sig).astype(np.float32)
    zs = rng.dirichlet([1, 1], n)
    ntok = rng.integers(100, 5000, n)
    if task == "r1":
        rules = {x["sid"]: {"keyword": "recommended_against", "keyword_v2": x["label"] if x["label"] != "none"
                            else "recommended_against", "keyword_or_none": "none", "keyword_v2_or_none": x["label"]}
                 for x in items}
    else:
        rules = {x["sid"]: {"heading": "yes", "s1_answer": x["label"]} for x in items}
    return Data(task, items, F, zs, ntok, rules, {"inputs": {}})


def grad_check() -> dict:
    rng = np.random.default_rng(3)
    Z = rng.standard_normal((20, 7))
    Y = np.eye(3)[rng.integers(0, 3, 20)]
    w = rng.uniform(0.5, 1.5, 20)
    out = {}
    for name, f, th in (("lr", _lr_obj(Z, Y, w, 0.7), rng.standard_normal(7 * 3 + 3) * 0.1),):
        _, g = f(th)
        num = np.array([(f(th + e)[0] - f(th - e)[0]) / 2e-6 for e in np.eye(len(th)) * 1e-6])
        out[name] = float(np.abs(num - g).max())
    old = globals()["MLP_HIDDEN"]
    globals()["MLP_HIDDEN"] = 5
    try:
        f = _mlp_obj(Z.astype(np.float32), Y, w, 0.01)
        th = rng.standard_normal(7 * 5 + 5 + 5 * 3 + 3) * 0.5
        _, g = f(th)
        num = np.array([(f(th + e)[0] - f(th - e)[0]) / 2e-3 for e in np.eye(len(th)) * 1e-3])
        out["mlp"] = float(np.abs(num - g).max())
    finally:
        globals()["MLP_HIDDEN"] = old
    return out


def cmd_selftest() -> None:
    gc = grad_check()
    print("gradient check (max abs difference):", gc)
    assert gc["lr"] < 1e-4 and gc["mlp"] < 5e-2, gc
    fs, hs = ["L16", "L16+L24+L32"], [("lr", 0.01), ("mlp", 0.01)]
    D1 = synthetic("r1")
    o1, st1 = design_r1(D1, fs, hs)
    o1b, _ = design_r1(D1, fs, hs)
    assert json.dumps(o1["variants"], sort_keys=True) == json.dumps(o1b["variants"], sort_keys=True), "not deterministic"
    D2 = synthetic("r2")
    o2, st2 = design_r2(D2, fs, hs)
    json.dumps({"r1": o1, "r2": o2})
    rows = oof_rows_r1(D1, o1, st1) + []
    assert rows and oof_rows_r2(D2, o2, st2)
    print("R1 chosen", o1["chosen"], "a", o1["a"], "none rule", o1["selection"]["none_rule"])
    print("R1 chosen values", compact(o1["chosen_values"]), o1["chosen_values"]["flip_train_pairs_oof"])
    print("R2 chosen", o2["chosen"], "a", o2["a"], compact(o2["chosen_values"]))
    # head file round trip and the state-file path
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        for task, D, out in (("r1", D1, o1), ("r2", D2, o2)):
            vid = out["chosen"]
            v = parse_variant(vid)
            opts = options_of(vid)
            tr = final_train_rows(D, vid)
            head = fit(v["kind"], v["reg"], D.X(v["fs"], tr), np.array([opts.index(D.items[i]["label"]) for i in tr]),
                       len(opts))
            p = Path(td) / f"{task}.npz"
            save_head(p, head, {"kind": v["kind"], "reg": v["reg"], "options": list(opts)})
            h2, _ = load_head(p)
            assert np.array_equal(predict(head, D.X(v["fs"], tr)), predict(h2, D.X(v["fs"], tr)))
            i = tr[0]
            sp = Path(td) / "state.npz"
            np.savez(sp, states=np.stack([D.F.get(k, np.zeros((len(D.items), 4096), np.float32))[i]
                                          for k in STATE_LAYERS]).astype(np.float32),
                     layers=np.array(STATE_LAYERS, dtype=np.int16), task=np.array(task), variant=np.array(VARIANT[task]),
                     template_sha256=np.array(TEMPLATE_SHA[task]), model_fingerprint=np.array("m"),
                     state_id=np.array("s"), doc_id=np.array("d"), probs=np.array([0.5, 0.5]),
                     prompt_sha256=np.array("x"), n_prompt_tokens=np.int64(10))
            fz = {"tasks": {task: {"prompt_variant": VARIANT[task], "template_sha256": TEMPLATE_SHA[task],
                                   "layers": list(FEATURE_SETS[v["fs"]]), "options": list(opts), "a": 0.9}},
                  "model_fingerprint": "m"}
            r = predict_state(task, sp, fz, h2)
            qm = predict(head, D.X(v["fs"], [i]))[0]
            assert max(abs(r["q"][o] - qm[k]) for k, o in enumerate(opts)) == 0.0
    print("selftest OK (synthetic data only)")


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["selftest", "register", "design", "freeze", "compare", "predict"])
    a.add_argument("--task", choices=["r1", "r2"])
    a.add_argument("--states")
    a.add_argument("--out")
    a.add_argument("--allow-validation", action="store_true")
    x = a.parse_args()
    if x.cmd == "selftest":
        cmd_selftest()
    elif x.cmd == "register":
        cmd_register()
    elif x.cmd == "design":
        cmd_design()
    elif x.cmd == "freeze":
        cmd_freeze()
    elif x.cmd == "compare":
        cmd_compare()
    else:
        if not (x.task and x.states and x.out):
            raise SystemExit("--task, --states and --out are necessary")
        cmd_predict(x.task, x.states, x.out, x.allow_validation)


if __name__ == "__main__":
    main()

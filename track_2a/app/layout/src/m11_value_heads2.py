"""The design tool of addendum I: Apertus heads on the questions `Q0`, `Q1` and `Q2` of the template `gj_values_v1_de`.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: PROPOSED, NOT RELEASED. No human checked this file. This file changes no existing file.
Rules: `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md` (rules I1 to I7, and chapter 10.2).

1 What a head is (rule I3)
  A head is a logistic regression with an L2 penalty on the state of layer 20 (4,096 values).
  `Q0` has 4 classes and `Q1` has 7 classes (softmax form). Each of the 6 `Q2` heads has 2 classes.
  A head gives a probability. Code then reads the value from one block (rule I4). The head reads no value.

2 Commands
  fit-oof     Fit the 5 fold heads of each of the 8 heads and write the out-of-fold probabilities.
              Inputs: the folder of `src/m11_value_heads2_data.py`. Outputs: `heads2_folds.npz`, `oof.npz`, `fit.json`.
  table       Make the entry decisions of rules I6 and I7 one time, and the measures of the two readers.
              Outputs: `entry.json`, `values_dev_combined.json`, `measures_dev.json`, `table_dev.md`.
  final       Fit the final head of each of the 8 heads on all documents of the fit.
              Outputs: `heads2.npz` (5 fold heads and the final head) and `heads2.json` (SHA-256 of each input).
  apply       Read a states folder and block files. Give the answers of the heads for each document.
              The output has the `ValueCandidate` / `NotFound` form of `src/m11_values_base.py` for each `Q2` field.
              With `--values-out` it also writes the values file of the combined reader.
  last-run-ids  Write the ids file of the 872 documents of the last run. The ids come from the file names of
              the block files and from the guard. No file of a document is opened. It prints counts only.
  fix-record  Write `last_run_fix.json` (chapter 10.2, item 1). It hashes files. It parses the ids file.
              Of the manifest of the job `values_last` it reads the key `doc_ids_sha256` only.
              It also holds the ids file, the set and the parliament of each id, and the SHA-256 of each block file
              and each rule file of the documents of the last run. The folder of the rule files must be
              `daten/gj/rules_pdf`. The build record of the sealed build of `src/m11_rules_pdf.py` must exist.
              The command stops if a document has no rule file (option `--permit-no-rule-file`: chapter 9 below).

3 Order of the commands for the development documents
  data tool, `fit-oof`, `table`, `final`. Then `src/m11_value_cal.py` on `values_dev_combined.json` (rule I6, 7.3).
  The converter `src/m11_heads2_convert.py` gives the files that the second tool `src/m11_second_heads2.py` reads.
  Time and memory of `fit-oof`: about 2 minutes on synthetic arrays of the full size with 4 threads.
  Real states can use each of the 100 iterations: up to 20 minutes. The peak memory is about 8 GB.
  Do not run a second heavy job on a Mac with 16 GB at the same time.

4 The fit in detail (rule I3; each number is that of table 1 of the addendum)
  Rows of a `Q2` fit: each positive block and 30 negative blocks at most of a document of the fit (items 11, 12).
  States go to float32. Mean and standard deviation (population form) come from the fit rows of that head.
  Loss: mean log loss + lambda / 2 x squared norm of the weights. The bias has no penalty.
  Solver: `torch.optim.LBFGS` on the CPU, start at zero, `max_iter` 100, `strong_wolfe`, other settings as given by torch.
  The head of fold f sees no document of fold f. Lambda comes from the inner fold (f + 1) modulo 5 (items 15 to 17).
  A probability is calculated in float64: z = x . (w / sd) + (b - (mu / sd) . w), for one document at a time.

5 Sealed paths and marks
  Each command refuses the sealed paths of chapter 10.2 unless `--last-run` is given (`refuse_sealed`).
  `fit-oof` and `table` stop if their output exists. Each record of the two commands has the mark of chapter 1,
  item 8, with or without `--overwrite` (constant `MARK_FROM_VERSION_3`; addendum I, chapter 14.2, item 3).
  `fit-oof`, `table` and `final` stop if the data tables were made with another reference file, another folds
  file or another folder of rule files than the present ones. Then run the data tool again.
  A data folder with the key `synthetic` cannot write below `daten/`.
  `fit-oof` and `table` stop on a data folder that is not complete (key `complete` of `data_record.json`).
  `table` stops if the calibration file of the rules is not the fixed file of chapter 6, item 10.

6 Errors of a span (rule I4, item 20)
  A span that `Doc.candidate` refuses (`BadResult`) gives no value in the command `table`. The reason code is
  `reader_error`. `entry.json` and `measures_dev.json` hold the count and the list. Each other error stops `table`.
  In the last run (`apply --last-run`) and with `--non-strict`, each error of a reader gives `reader_error`.

7 The one last run (`apply --last-run`; chapter 10)
  The command stops unless: the ids are the 872 ids of the fix record; the files `--heads`, `--entry` and the
  calibration files are files of the fix record; each block file and rule file has the SHA-256 of the fix record;
  the model fingerprint and the template of the job `values_last` are those of the job `values_dev`;
  no output file exists. A document whose suffix ids differ from its block file gets no head value.
  The folder `--rules` must be `daten/gj/rules_pdf`. The 2 calibration files must be in the roles of the fix record.
  A states file that cannot be read gives no head value for its document (list `documents_with_a_states_error`).
  A block file that cannot be read gives the reason `reader_error` for each field of its document.

8 The ids file (`last-run-ids`)
  One id for each line, in number order. The guard must give 804 ids of the split `validation` and 68 of `group7`.
  The command `fix-record` compares the ids with the key `doc_ids_sha256` of the manifest of the job.

9 Rule files of the last run (`fix-record`)
  The sealed build of `src/m11_rules_pdf.py` must run first. Its record must give 872 documents.
  If the build failed for N documents, `--permit-no-rule-file N` permits exactly these N documents.
  Such a document has no rule role: rule V1 of the reader applies, and it is outside the primary set.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_value_heads2.py fit-oof
  uv run --offline --frozen --no-sync python src/m11_value_heads2.py table
  uv run --offline --frozen --no-sync python src/m11_value_heads2.py final
  uv run --offline --frozen --no-sync python src/m11_value_heads2.py apply --states `folder` --out `file`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402
import m11_value_heads as vh  # noqa: E402  (the 4 span functions of table 2; not changed)
import m11_value_heads2_data as hd  # noqa: E402
import m11_value_norm as vn  # noqa: E402
import m11_values_base as vb  # noqa: E402
import m11_values_cascade as cvc  # noqa: E402
import m11_values_combined as cmb  # noqa: E402
import m11_values_dates_responder as dr  # noqa: E402

VERSION = "m11-value-heads2-1"
ROOT = vb.ROOT
OUT_DIR = hd.OUT_DEFAULT
MARK = "after the design values of addendum I"
# Addendum I, chapter 14.2, item 3: the files `oof.npz` and `fit.json` of a first fit existed before version 3.
# Thus each later value has the mark, with or without the flag `--overwrite`.
MARK_FROM_VERSION_3 = True
RULES_BUILD_RECORD_LAST = vb.ROOT / "daten/gj_values/round4/rules_pdf_build_last_run.json"   # src/m11_rules_pdf.py
LAST_RUN_IDS = hd.OUT_DEFAULT / "last_run_ids.txt"
# ---- table 1 of addendum I (fixed; no agent changes a number to make a tier enter)
LAYER = 20
LAMBDAS = (0.001, 0.01, 0.1)
MAX_NEGATIVES = 30
SEED_BASE = 20261013
P_VALUE_MIN = 0.50
P_BAND_HI = 0.80
MIN_UNITS = 20
CLASS_MIN = cmb.CLASS_MIN            # 0.80
# chapter 6, item 10: the one calibration file of the reader with rules only (20 weak tiers).
# Addendum I version 3: the file of round 4 (rule files from the PDF alone, cascade reader version 3).
CALIBRATION_RULES_SHA256 = "e48e7a8d8efdd1e10b68071df85275dc0c5b69e004bb8051b2aecd2a1d4229d7"
LAST_RUN_SETS = {"validation": 804, "group7": 68}      # chapter 10.1, item 2: 872 documents
LAST_RUN_DOCUMENTS = sum(LAST_RUN_SETS.values())
LAST_RUN_JOB = vb.ROOT / "daten/gj/jobs/values_last"
DEV_MANIFEST = vb.ROOT / "daten/gj/jobs/values_dev/manifest.json"
Q0_MIN_DOCUMENTS = 50
MAX_ITER = 100
SD_MIN = 1e-6
FOLDS = hd.FOLDS
FINAL = FOLDS                        # index of the final head in `heads2.npz`
Q2_FIELDS = hd.Q2_FIELDS
Q1_CLASSES = hd.Q1_CLASSES
Q0_CLASSES = hd.Q0_CLASSES
MEASURE_ID = hd.MEASURE_ID
HEAD_NAMES = ("q0", "q1") + tuple(f"q2_{f}" for f in Q2_FIELDS)
RULE_MODULES = ("m11_values_dates_responder", "m11_values_sponsor", "m11_values_title", "m11_values_type_number")
B_RX = re.compile(dr.B)
sha256_file, rel, write_json, now = hd.sha256_file, hd.rel, hd.write_json, hd.now


# ------------------------------------------------------------------ the stored heads and the probabilities

def _affine(w, b, mu, sd):
    u = np.asarray(w, dtype=np.float64) / np.asarray(sd, dtype=np.float64)
    c = np.asarray(b, dtype=np.float64) - (np.asarray(mu, dtype=np.float64) * u).sum(-1)
    return u, c


def binary_prob(x: np.ndarray, w, b, mu, sd) -> np.ndarray:
    """float64 [n]: the probability of the positive class for the states x [n, 4096]."""
    u, c = _affine(w, b, mu, sd)
    z = np.asarray(x, dtype=np.float64) @ u + c
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def softmax_prob(x: np.ndarray, w, b, mu, sd) -> np.ndarray:
    """float64 [n, classes] for the states x [n, 4096]; w [classes, 4096], b [classes]."""
    u, c = _affine(w, b, mu[None, :], sd[None, :])
    z = np.asarray(x, dtype=np.float64) @ u.T + c
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class Heads2:
    """The stored heads. Model 0 to 4: the fold heads. Model 5: the final head (only in `heads2.npz`)."""

    def __init__(self, arrays: dict):
        self.a = arrays
        self.layer = int(arrays["layer"])
        self.models = int(arrays["q0__w"].shape[0])
        if [str(c) for c in arrays["q1_classes"]] != list(Q1_CLASSES) or \
                [str(c) for c in arrays["q0_classes"]] != list(Q0_CLASSES):
            raise ValueError("the heads file has other classes than addendum I")

    @classmethod
    def load(cls, path: Path | str) -> "Heads2":
        with np.load(Path(path), allow_pickle=False) as z:
            return cls({k: z[k] for k in z.files})

    def _part(self, name: str, model: int):
        if not 0 <= model < self.models:
            raise ValueError(f"the heads file has no model {model}")
        return (self.a[f"{name}__{k}"][model] for k in ("w", "b", "mu", "sd"))

    def q0(self, x: np.ndarray, model: int) -> np.ndarray:
        return softmax_prob(x, *self._part("q0", model))

    def q1(self, x: np.ndarray, model: int) -> np.ndarray:
        return softmax_prob(x, *self._part("q1", model))

    def q2(self, field: str, x: np.ndarray, model: int) -> np.ndarray:
        return binary_prob(x, *self._part(f"q2_{field}", model))


# ------------------------------------------------------------------ rule I4: from the block to the value

def response_date_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    """Table 2, items 9 and 10: the latest day of the block; a tie goes to the first hit in reading order."""
    hits = vb.find_dates(b.text, b.char_start)
    if not hits:
        return []
    latest = max(h.iso for h in hits)
    h = next(h for h in hits if h.iso == latest)
    return [{"start": h.start, "end": h.end, "normalised": h.iso}]


def responder_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    """Table 2, items 11 to 13: the first match of the pattern `B` (a body word as a full token) in the folded
    block text. The span is that of the group `body`. `normalised` is the base wording of `body_key`."""
    f = vb.fold_map(b.text, b.char_start)
    for m in B_RX.finditer(f.text):
        got = dr.body_key(m.group("body"))
        if got is None:
            continue
        s, e = f.match_span(m, "body")
        return [{"start": s, "end": e, "normalised": got[1], "body_key": got[0]}]
    return []


def _pick(values: list[dict], option: str) -> list[dict]:
    return [v for v in values if option in v["options"]][:1]


SPAN = {    # registry id -> (name of the span function, option, function)
    "affair_number": ("_number_values", "structured_only", lambda d, b: _pick(vh._number_values(d, b), "structured_only")),
    "title": ("_title_values", "quote_then_block", lambda d, b: _pick(vh._title_values(d, b), "quote_then_block")),
    "sponsor": ("_author_values", "known_first_name", lambda d, b: _pick(vh._author_values(d, b), "known_first_name")),
    "submission_date": ("_date_values", "first_date", lambda d, b: _pick(vh._date_values(d, b), "first_date")),
    "response_date": ("response_date_values", None, response_date_values),
    "responder": ("responder_values", None, responder_values),
}


def band_of(p: float) -> str:
    return "hi" if p >= P_BAND_HI else "lo"


def top_block(doc: vb.Doc, p: np.ndarray) -> int | None:
    """Index of the block with text that has the highest probability; a tie goes to the first block (item 1)."""
    idx = [i for i, b in enumerate(doc.blocks) if b.text]
    if not idx:
        return None
    return idx[int(np.argmax(np.asarray(p, dtype=np.float64)[idx]))]


def read_q2(field: str, doc: vb.Doc, p: np.ndarray, strict: bool = True, model: str = "",
            catch_all: bool = False) -> vb.ValueCandidate | vb.NotFound:
    """The Apertus tier of one field for one document: p [blocks] is the head probability of each block.
    strict: each error stops. Not strict: a span that `Doc.candidate` refuses (`BadResult`) gives the reason
    `reader_error` (rule I4, item 20). Not strict with `catch_all`: each error of the span function gives it."""
    if len(p) != len(doc.blocks):
        raise ValueError(f"{doc.doc_id}: {len(p)} probabilities for {len(doc.blocks)} blocks")
    i = top_block(doc, p)
    if i is None or not doc.text.strip():
        return doc.not_found(field, "no_text")
    b, pt = doc.blocks[i], float(p[i])
    if pt < P_VALUE_MIN:
        return doc.not_found(field, "no_cue", f"head probability {pt!r} of the top block {b.block} is below {P_VALUE_MIN}")
    name, option, fn = SPAN[field]
    try:
        vals = fn(doc, b)
        if not vals:
            return doc.not_found(field, "no_pattern", f"the span function {name} finds no value in the top block "
                                                      f"{b.block} (head probability {pt!r})")
        v = vals[0]
        return doc.candidate(field, v["start"], v["end"], v["normalised"], cmb.q2_tier(field, band_of(pt)),
                             detail={"head_probability": pt, "band": band_of(pt), "top_block": b.block,
                                     "layer": LAYER, "span_function": name, "option": option, "model": model})
    except vb.BadResult as e:
        if strict:
            raise
        return vb.NotFound(field, "reader_error", f"{type(e).__name__}: top block {b.block}: {e}"[:200])
    except Exception as e:  # noqa: BLE001
        if strict or not catch_all:
            raise
        return vb.NotFound(field, "reader_error", f"{type(e).__name__}: top block {b.block}: {e}"[:200])


def _class_answer(classes, p: np.ndarray) -> dict:
    p = np.asarray(p, dtype=np.float64)
    k = int(np.argmax(p))
    return {"classes": list(classes), "probabilities": [float(v) for v in p], "class": classes[k],
            "probability": float(p[k]), "given": bool(p[k] >= CLASS_MIN)}


def output_from_probabilities(doc: vb.Doc, q0p, q1p, q2p: dict, strict: bool = True, model: str = "",
                              catch_all: bool = False) -> dict:
    """The heads output of one document (form: header of `src/m11_values_combined.py`, chapter 2)."""
    q1 = _class_answer(Q1_CLASSES, q1p)
    q1["type"] = q1["class"] if (q1["given"] and q1["class"] != "none") else None
    return {"q0": _class_answer(Q0_CLASSES, q0p), "q1": q1, "model": model,
            "q2": {f: read_q2(f, doc, q2p[f], strict, model, catch_all) for f in Q2_FIELDS}}


OtherSuffixIds = hd.OtherSuffixIds        # the suffix ids are not those of the block file (rule I1, item 7)


def apply_document(doc: vb.Doc, states: hd.States, heads: Heads2, model: int = FINAL, strict: bool = True,
                   catch_all: bool = False) -> dict:
    """The answers of the heads for one document. The block ids of the states must be those of the document."""
    if states.block_ids != [b.block for b in doc.blocks]:
        raise OtherSuffixIds(f"{doc.doc_id}: the suffix ids are not Q0, Q1 and Q2.B<n> for each block (rule I1, item 7)")
    name = "final" if model == FINAL else f"fold_{model}"
    x2 = states.q2(heads.layer)
    return output_from_probabilities(
        doc, heads.q0(states.q0(heads.layer)[None, :], model)[0], heads.q1(states.q1(heads.layer)[None, :], model)[0],
        {f: heads.q2(f, x2, model) for f in Q2_FIELDS}, strict, name, catch_all)


def output_to_json(out: dict) -> dict:
    return {"q0": out["q0"], "q1": out["q1"], "model": out.get("model"),
            "q2": {f: cmb.as_json(r) for f, r in out["q2"].items()}}


def value_probability(lookup: dict, field: str, tier: str, fold: int | None = None) -> float | None:
    """Rule I6, chapter 7.3: the stored probability of a tier from the key `lookup` of the calibration of the
    combined values file. fold = None: all 5 folds. Else the value of the 4 other folds."""
    t = ((lookup.get(MEASURE_ID.get(field, field)) or {}).get("tiers") or {}).get(tier)
    if t is None:
        return None
    return t["p_all_folds"] if fold is None else t["p_without_fold"][str(fold)]


# ------------------------------------------------------------------ rule I3: the fit

def _lbfgs(params, closure) -> dict:
    import torch  # noqa: PLC0415

    opt = torch.optim.LBFGS(params, lr=1.0, max_iter=MAX_ITER, line_search_fn="strong_wolfe")
    opt.step(closure)
    st = opt.state[opt._params[0]]
    return {"iterations": int(st["n_iter"]), "evaluations": int(st["func_evals"])}


def fit_head(kind: str, x: np.ndarray, y: np.ndarray, lam: float, classes: int = 2) -> dict:
    """One head. kind: `binary` or `softmax`. x: float32 [rows, 4096] (raw states; a copy is standardised).
    y: bool [rows] or class index [rows]. Returns w, b, mu, sd (float32) and the record of the fit."""
    import torch  # noqa: PLC0415

    t0 = time.time()
    if x.shape[0] == 0:
        raise SystemExit("a fit has no row")
    xt = torch.from_numpy(np.array(x, dtype=np.float32, copy=True))
    n = xt.shape[0]
    mu = xt.mean(0, dtype=torch.float64)
    var = ((xt * xt).mean(0, dtype=torch.float64) - mu * mu).clamp_min(0.0)
    sd = var.sqrt()
    sd = torch.where(sd < SD_MIN, torch.ones_like(sd), sd)
    mu32, sd32 = mu.float(), sd.float()
    xt.sub_(mu32).div_(sd32)
    if kind == "binary":
        yt = torch.from_numpy(np.asarray(y, dtype=np.float32))
        w = torch.nn.Parameter(torch.zeros(xt.shape[1]))
        b = torch.nn.Parameter(torch.zeros(1))

        def closure():
            with torch.no_grad():
                z = xt @ w + b
                loss = torch.nn.functional.binary_cross_entropy_with_logits(z, yt) + 0.5 * lam * (w @ w)
                g = (torch.sigmoid(z) - yt) / n
                w.grad = xt.T @ g + lam * w
                b.grad = g.sum().reshape(1)
            return loss
    elif kind == "softmax":
        yi = torch.from_numpy(np.asarray(y, dtype=np.int64))
        onehot = torch.nn.functional.one_hot(yi, classes).float()
        w = torch.nn.Parameter(torch.zeros(classes, xt.shape[1]))
        b = torch.nn.Parameter(torch.zeros(classes))

        def closure():
            with torch.no_grad():
                z = xt @ w.T + b
                loss = torch.nn.functional.cross_entropy(z, yi) + 0.5 * lam * (w * w).sum()
                g = (torch.softmax(z, 1) - onehot) / n
                w.grad = g.T @ xt + lam * w
                b.grad = g.sum(0)
            return loss
    else:
        raise ValueError(kind)
    info = _lbfgs([w, b], closure)
    info.update(loss=float(closure()), rows=int(n), seconds=round(time.time() - t0, 2))
    info["lambda"] = lam
    bb = b.detach().numpy().astype(np.float32)
    return {"kind": kind, "w": w.detach().numpy().astype(np.float32), "b": bb if kind == "softmax" else bb[0],
            "mu": mu32.numpy(), "sd": sd32.numpy(), "info": info}


def log_loss(head: dict, x: np.ndarray, y: np.ndarray) -> float:
    """The mean log loss of a head on rows (float64)."""
    if x.shape[0] == 0:
        raise SystemExit("the inner fold of a lambda selection has no row")
    if head["kind"] == "binary":
        p = binary_prob(x, head["w"], head["b"], head["mu"], head["sd"])
        yy = np.asarray(y, dtype=bool)
        q = np.where(yy, p, 1.0 - p)
    else:
        p = softmax_prob(x, head["w"], head["b"], head["mu"], head["sd"])
        q = p[np.arange(len(y)), np.asarray(y, dtype=np.int64)]
    return float(-np.log(np.clip(q, 1e-300, None)).mean())


def choose_lambda(losses: list[float]) -> float:
    """The lambda with the lowest loss; a tie goes to the larger lambda (rule I3, item 17)."""
    best = 0
    for i in range(1, len(LAMBDAS)):
        if losses[i] <= losses[best]:
            best = i
    return LAMBDAS[best]


def fit_folds(kind: str, x: np.ndarray, y: np.ndarray, fold: np.ndarray, classes: int = 2, say=None) -> dict:
    """The 5 fold heads of one head with the nested choice of lambda (rule I3, items 14 to 18)."""
    models, record = [], []
    for f in range(FOLDS):
        g = (f + 1) % FOLDS
        inner = (fold != f) & (fold != g)
        val = fold == g
        outer = fold != f
        losses, fits = [], []
        for lam in LAMBDAS:
            h = fit_head(kind, x[inner], y[inner], lam, classes)
            losses.append(log_loss(h, x[val], y[val]))
            fits.append(h["info"])
        lam = choose_lambda(losses)
        h = fit_head(kind, x[outer], y[outer], lam, classes)
        models.append(h)
        rec = {"fold": f, "inner_fold": g, "inner_log_loss": dict(zip((str(v) for v in LAMBDAS), losses)),
               "lambda": lam, "inner_fits": fits, "fit": h["info"], "rows_of_the_inner_fold": int(val.sum())}
        record.append(rec)
        if say:
            say({"fold": f, "lambda": lam, "inner_log_loss": [round(v, 6) for v in losses], "fit": h["info"]})
    return {"models": models, "folds": record, "lambdas": [r["lambda"] for r in record]}


def final_lambda(selected: list[float]) -> float:
    """The middle value of the 5 selected values in sorted order (rule I3, item 21)."""
    if len(selected) != FOLDS:
        raise ValueError("5 selected values are necessary")
    return sorted(selected)[FOLDS // 2]


def q2_fit_rows(meta: list, label: np.ndarray, has_text: np.ndarray, field: str) -> tuple[np.ndarray, dict]:
    """The rows of the fit of one `Q2` field (rule I2, items 16 to 22; rule I3, items 11 and 12), in row order."""
    rows, c = [], Counter()
    for e in meta:
        if not e["has_states"]:
            continue
        if not e["has_reference"][field]:
            c["documents_with_no_reference"] += 1
            continue
        if field in hd.PRIMARY_ONLY_FIT and not e["primary_set"][field]:
            c["documents_outside_the_primary_set"] += 1
            continue
        s = e["row_start"]
        text, lab = has_text[s:s + e["blocks"]], label[s:s + e["blocks"]]
        pos = np.flatnonzero(lab & text)
        neg = np.flatnonzero(~lab & text)
        c["negative_blocks_with_text"] += len(neg)
        if len(neg) > MAX_NEGATIVES:
            pick = np.random.default_rng(SEED_BASE + int(e["doc_id"])).choice(len(neg), MAX_NEGATIVES, replace=False)
            neg = neg[np.sort(pick)]
            c["documents_with_more_than_30_negative_blocks"] += 1
        rows.append(s + np.sort(np.concatenate([pos, neg])))
        c["documents_of_the_fit"] += 1
        c["documents_with_no_positive_block"] += len(pos) == 0
        c["positive_blocks"] += len(pos)
        c["negative_blocks_in_the_fit"] += len(neg)
        c["all_blocks"] += e["blocks"]
    idx = np.concatenate(rows).astype(np.int64) if rows else np.zeros(0, dtype=np.int64)
    keys = ("documents_of_the_fit", "documents_with_no_reference", "documents_outside_the_primary_set",
            "documents_with_no_positive_block", "positive_blocks", "negative_blocks_with_text",
            "negative_blocks_in_the_fit", "documents_with_more_than_30_negative_blocks", "all_blocks")
    return idx, {k: int(c[k]) for k in keys}


class Data:
    """The folder of the data tool, and the fit rows of each of the 8 heads."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.record = json.loads((self.folder / "data_record.json").read_text(encoding="utf-8"))
        if LAYER not in self.record["layers"]:
            raise SystemExit(f"the data folder has no file of layer {LAYER}")
        if self.record["q1_classes"] != list(Q1_CLASSES) or self.record["q2_fields"] != list(Q2_FIELDS):
            raise SystemExit("the data folder has other classes or fields than addendum I")
        self.meta = json.loads((self.folder / "docs.json").read_text(encoding="utf-8"))
        self.rows = np.load(self.folder / "rows.npz")
        self.has_text = self.rows["row_has_text"]
        self.q2 = np.load(self.folder / f"q2_L{LAYER}.npy", mmap_mode="r")
        self.q0 = np.load(self.folder / f"q0_L{LAYER}.npy")
        self.q1 = np.load(self.folder / f"q1_L{LAYER}.npy")
        self.with_states = [e for e in self.meta if e["has_states"]]
        if self.q2.shape != (len(self.has_text), hd.HIDDEN) or self.q0.shape[0] != len(self.with_states):
            raise SystemExit("the array files do not agree with rows.npz and docs.json")
        self.doc_fold = np.array([e["fold"] for e in self.with_states], dtype=np.int64)

    @property
    def synthetic(self) -> bool:
        return bool(self.record.get("synthetic"))

    def fit_set(self, head: str):
        """(kind, x float32, y, fold of each row, classes, counts) for one head."""
        if head == "q0":
            keep = np.array([e["q0_label"] is not None for e in self.with_states])
            y = np.array([Q0_CLASSES.index(e["q0_label"]) for e in self.with_states if e["q0_label"] is not None])
            counts = {"documents_of_the_fit": int(keep.sum()),
                      "documents_by_class": {c: int((y == i).sum()) for i, c in enumerate(Q0_CLASSES)}}
            return "softmax", self.q0[keep].astype(np.float32), y, self.doc_fold[keep], len(Q0_CLASSES), counts
        if head == "q1":
            keep = np.array([e["q1_class"] is not None for e in self.with_states])
            y = np.array([Q1_CLASSES.index(e["q1_class"]) for e in self.with_states if e["q1_class"] is not None])
            counts = {"documents_of_the_fit": int(keep.sum()), "documents_with_a_value_that_is_not_a_class": int((~keep).sum()),
                      "documents_by_class": {c: int((y == i).sum()) for i, c in enumerate(Q1_CLASSES)}}
            return "softmax", self.q1[keep].astype(np.float32), y, self.doc_fold[keep], len(Q1_CLASSES), counts
        field = head[3:]
        label = self.rows[f"label__{field}"]
        idx, counts = q2_fit_rows(self.meta, label, self.has_text, field)
        x = np.asarray(self.q2[idx], dtype=np.float32) if len(idx) else np.zeros((0, hd.HIDDEN), dtype=np.float32)
        return "binary", x, label[idx], self.doc_fold[self.rows["row_doc"][idx]], 2, counts

    def input_hashes(self) -> dict:
        names = ["data_record.json", "rows.npz", "docs.json"] + [f"{q}_L{LAYER}.npy" for q in ("q0", "q1", "q2")]
        return {n: sha256_file(self.folder / n) for n in names}


def _stack(models: list[dict]) -> dict:
    return {k: np.stack([np.asarray(m[k]) for m in models]) for k in ("w", "b", "mu", "sd")}


def _save_heads(path: Path, per_head: dict) -> None:
    arrays = {"layer": np.int64(LAYER), "q1_classes": np.array(Q1_CLASSES), "q0_classes": np.array(Q0_CLASSES),
              "q2_fields": np.array(Q2_FIELDS)}
    for name, models in per_head.items():
        for k, v in _stack(models).items():
            arrays[f"{name}__{k}"] = v
        arrays[f"{name}__lambda"] = np.array([m["info"]["lambda"] for m in models], dtype=np.float64)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **arrays)


def _no_synthetic_below_daten(data: Data, out: Path) -> None:
    if data.synthetic and (ROOT / "daten") in out.resolve().parents:
        raise SystemExit("a synthetic data folder cannot write below daten/")


def mark_of(overwrite: bool) -> str | None:
    """The mark of chapter 1, item 8, for a record of `fit-oof` or `table`."""
    return MARK if (overwrite or MARK_FROM_VERSION_3) else None


def stale_inputs(data: Data) -> list[str]:
    """The inputs of the data tables that are not the present inputs: the reference file, the folds file and the
    folder of the rule files. An empty list for a synthetic data folder."""
    if data.synthetic:
        return []
    rec = data.record.get("inputs_sha256") or {}
    bad = [rel(q) for q in (hd.REFERENCE, hd.FOLDS_ALL) if not q.is_file() or rec.get(rel(q)) != sha256_file(q)]
    if data.record.get("rule_files") != rel(vb.RULES_DIR):
        bad.append(f"rule files: {data.record.get('rule_files')!r}, not {rel(vb.RULES_DIR)!r}")
    return bad


def _present_inputs_or_stop(data: Data) -> None:
    bad = stale_inputs(data)
    if bad:
        raise SystemExit(f"{rel(data.folder)}: the data tables were made with another reference, folds file or rule "
                         f"file folder ({'; '.join(bad)}): run src/m11_value_heads2_data.py again")


def _complete_or_stop(data: Data) -> None:
    """A data folder of real documents must hold each document of the job (key `complete` of the data record)."""
    if not data.synthetic and data.record.get("complete") is not True:
        raise SystemExit(f"{rel(data.folder)}: the data folder is not complete (key complete of data_record.json): "
                         "the first full out-of-fold run needs each document of the job (rule I6, 7.1, item 9)")


def _threads(n: int | None) -> int:
    import torch  # noqa: PLC0415

    if n:
        torch.set_num_threads(n)
    return torch.get_num_threads()


def cmd_fit_oof(a) -> int:
    import torch  # noqa: PLC0415

    t0 = time.time()
    data, out = Data(a.data), Path(a.out)
    _no_synthetic_below_daten(data, out)
    _complete_or_stop(data)
    _present_inputs_or_stop(data)
    if (out / "oof.npz").exists() and not a.overwrite:
        raise SystemExit(f"{rel(out / 'oof.npz')} exists: the first full out-of-fold run was made (rule I6, 7.1, item 9)")
    threads = _threads(a.threads)
    per_head, fits = {}, {}
    for name in HEAD_NAMES:
        t1 = time.time()
        kind, x, y, fold, classes, counts = data.fit_set(name)
        res = fit_folds(kind, x, y, fold, classes, say=lambda r, n=name: print(json.dumps({"head": n, **r}), flush=True))
        per_head[name] = res["models"]
        fits[name] = {"kind": kind, "rows_of_the_fit": int(len(y)), "label_counts": counts, "lambdas": res["lambdas"],
                      "lambda_of_the_final_head": final_lambda(res["lambdas"]), "folds": res["folds"],
                      "seconds": round(time.time() - t1, 1)}
        del x
    out.mkdir(parents=True, exist_ok=True)
    _save_heads(out / "heads2_folds.npz", per_head)
    heads = Heads2.load(out / "heads2_folds.npz")
    # out-of-fold: a document of fold f is read with the head of fold f, one document at a time (item 19)
    n_docs, n_rows = len(data.with_states), len(data.has_text)
    oof0 = np.zeros((n_docs, len(Q0_CLASSES)))
    oof1 = np.zeros((n_docs, len(Q1_CLASSES)))
    oof2 = np.zeros((n_rows, len(Q2_FIELDS)))
    for i, e in enumerate(data.with_states):
        f = e["fold"]
        oof0[i] = heads.q0(data.q0[i][None, :], f)[0]
        oof1[i] = heads.q1(data.q1[i][None, :], f)[0]
        x = np.asarray(data.q2[e["row_start"]:e["row_start"] + e["blocks"]])
        for j, field in enumerate(Q2_FIELDS):
            oof2[e["row_start"]:e["row_start"] + e["blocks"], j] = heads.q2(field, x, f)
    np.savez(out / "oof.npz", doc_ids=np.array([e["doc_id"] for e in data.with_states]), fold=data.doc_fold,
             q0=oof0, q1=oof1, q2=oof2, row_doc=data.rows["row_doc"], row_block=data.rows["row_block"],
             q0_classes=np.array(Q0_CLASSES), q1_classes=np.array(Q1_CLASSES), q2_fields=np.array(Q2_FIELDS))
    rec = {
        "version": VERSION, "made": now(), "status": hd.STATUS, "actor": hd.ACTOR,
        "mark": mark_of(a.overwrite), "rules": "addendum I, rule I3", "synthetic": data.synthetic,
        "addendum_sha256": sha256_file(hd.ADDENDUM),
        "model": "logistic regression with an L2 penalty on the state of one layer; float32; mean and population "
                 "standard deviation of each dimension from the fit rows of the head (below 0.000001: 1); loss = "
                 "mean log loss + lambda / 2 x squared norm of the weights; no penalty on the bias",
        "solver": {"name": "torch.optim.LBFGS", "device": "cpu", "start": "zero", "max_iter": MAX_ITER,
                   "line_search_fn": "strong_wolfe", "lr": 1.0, "other_settings": "as given by torch",
                   "torch": torch.__version__, "threads": threads},
        "layer": LAYER, "lambda_grid": list(LAMBDAS), "max_negative_blocks_of_one_document": MAX_NEGATIVES,
        "negative_rule": f"numpy.random.default_rng({SEED_BASE} + int(doc id)).choice(n, {MAX_NEGATIVES}, replace=False) "
                         "on the negative blocks with text in reading order",
        "lambda_rule": "inner fold g = (f + 1) modulo 5; fit on the 3 folds that are not f and not g; the lowest mean "
                       "log loss on the fit rows of fold g; a tie goes to the larger lambda",
        "probability": "float64: z = x . (w / sd) + (b - (mu / sd) . w), one document at a time",
        "documents_of_the_job": len(data.meta), "documents_with_states": n_docs,
        "documents_with_no_states_file": len(data.meta) - n_docs, "rows": n_rows,
        "heads": fits, "data_folder": {"path": rel(data.folder), "sha256": data.input_hashes()},
        "outputs_sha256": {n: sha256_file(out / n) for n in ("heads2_folds.npz", "oof.npz")},
        "code_sha256": {rel(Path(__file__)): sha256_file(Path(__file__)),
                        rel(Path(hd.__file__)): sha256_file(Path(hd.__file__))},
        "seconds": round(time.time() - t0, 1),
    }
    write_json(out / "fit.json", rec)
    print(json.dumps({"heads": {n: {"rows": v["rows_of_the_fit"], "lambdas": v["lambdas"], "seconds": v["seconds"]}
                                for n, v in fits.items()}, "seconds": rec["seconds"], "threads": threads}, indent=1))
    return 0


def cmd_final(a) -> int:
    t0 = time.time()
    data, out = Data(a.data), Path(a.out)
    _no_synthetic_below_daten(data, out)
    _present_inputs_or_stop(data)
    fit = json.loads((out / "fit.json").read_text(encoding="utf-8"))
    if fit["data_folder"]["sha256"] != data.input_hashes():
        raise SystemExit("the data folder changed after the command fit-oof")
    if fit["outputs_sha256"]["heads2_folds.npz"] != sha256_file(out / "heads2_folds.npz"):
        raise SystemExit("heads2_folds.npz changed after the command fit-oof")
    threads = _threads(a.threads)
    folds = Heads2.load(out / "heads2_folds.npz")
    per_head, record = {}, {}
    for name in HEAD_NAMES:
        kind, x, y, _fold, classes, counts = data.fit_set(name)
        lam = final_lambda(fit["heads"][name]["lambdas"])
        h = fit_head(kind, x, y, lam, classes)
        models = [{k: folds.a[f"{name}__{k}"][m] for k in ("w", "b", "mu", "sd")} |
                  {"info": {"lambda": float(folds.a[f"{name}__lambda"][m])}} for m in range(FOLDS)]
        per_head[name] = models + [h]
        record[name] = {"lambda": lam, "selected_lambdas_of_the_folds": fit["heads"][name]["lambdas"],
                        "label_counts": counts, "fit": h["info"]}
        print(json.dumps({"head": name, "lambda": lam, "fit": h["info"]}), flush=True)
        del x
    _save_heads(out / "heads2.npz", per_head)
    inputs = {f"{rel(data.folder)}/{n}": s for n, s in data.input_hashes().items()}
    for n in ("fit.json", "oof.npz", "heads2_folds.npz", "entry.json"):
        if (out / n).is_file():
            inputs[rel(out / n)] = sha256_file(out / n)
    for p in (hd.REFERENCE, hd.FOLDS_ALL, hd.SETS, hd.ADDENDUM, Path(__file__), Path(hd.__file__),
              Path(vh.__file__), Path(cmb.__file__)):
        inputs[rel(p)] = sha256_file(p)
    write_json(out / "heads2.json", {
        "version": VERSION, "made": now(), "status": hd.STATUS, "actor": hd.ACTOR, "synthetic": data.synthetic,
        "rules": "addendum I, rule I3, items 21 to 23",
        "what": "heads2.npz: for each of the 8 heads the models 0 to 4 (fold heads) and the model 5 (final head, "
                "fitted on all documents of the fit). The final head read no development document for a table.",
        "keys": "<head>__w, __b, __mu, __sd (float32) and __lambda; heads: " + ", ".join(HEAD_NAMES),
        "layer": LAYER, "heads": record, "threads": threads,
        "heads2_npz_sha256": sha256_file(out / "heads2.npz"), "inputs_sha256": inputs,
        "data_inputs_sha256": data.record.get("inputs_sha256"), "seconds": round(time.time() - t0, 1)})
    print(json.dumps({"out": rel(out / "heads2.npz"), "sha256": sha256_file(out / "heads2.npz"),
                      "seconds": round(time.time() - t0, 1)}))
    return 0


# ------------------------------------------------------------------ rules I6 and I7: the entry rules

def tier_enters(e: int, d: int, num: int = 1, den: int = 2) -> bool:
    """A tier enters with 20 or more units and a precision of `num` / `den` or more, in whole numbers."""
    return (e + d) >= MIN_UNITS and den * e >= num * (e + d)


def q2_entry(field: str, hi: tuple[int, int], lo: tuple[int, int]) -> dict:
    """Rule I6, chapter 7.1, items 4 to 8. hi and lo: (equal units, different units) of each band."""
    (eh, dh), (el, dl) = hi, lo
    if eh + dh >= MIN_UNITS and el + dl >= MIN_UNITS:
        ent = {"hi": tier_enters(eh, dh), "lo": tier_enters(el, dl)}
        tiers = {cmb.q2_tier(field, "hi"): {"equal": eh, "different": dh, "entered": ent["hi"]},
                 cmb.q2_tier(field, "lo"): {"equal": el, "different": dl, "entered": ent["lo"]}}
        return {"mode": "bands", "entered": ent, "tiers": tiers, "any_tier_entered": any(ent.values())}
    e, d = eh + el, dh + dl
    ok = tier_enters(e, d)
    return {"mode": "one", "entered": ok, "tiers": {cmb.q2_tier(field): {"equal": e, "different": d, "entered": ok}},
            "any_tier_entered": ok, "units_by_band": {"hi": {"equal": eh, "different": dh},
                                                      "lo": {"equal": el, "different": dl}}}


def q1_entry(e: int, d: int) -> dict:
    """Rule I6, chapter 7.2, item 5: 20 or more units and a precision of 0.80 or more."""
    return {"equal": e, "different": d, "entered": tier_enters(e, d, 4, 5)}


def q0_entry(given: int, head_correct: int, rule_correct: int) -> dict:
    """Rule I7, items 5 to 8: the 3 conditions on the set G of the labelled documents with a given class."""
    a = given >= Q0_MIN_DOCUMENTS
    b = 10 * head_correct >= 9 * given
    c = head_correct >= rule_correct
    return {"documents_of_g": given, "head_correct": head_correct, "rule_correct": rule_correct,
            "condition_a": a, "condition_b": b, "condition_c": c, "entered": bool(a and b and c)}


def outcome(field: str, rec: dict, ref_entry: dict) -> str:
    """equal, different, not_found or no_reference for one record (addendum G, chapter 5.1)."""
    forms = hd.reference_forms(ref_entry)
    if not forms:
        return "no_reference"
    if not rec["found"]:
        return "not_found"
    return "equal" if vn.compare(MEASURE_ID.get(field, field), rec["normalised"], forms)["equal"] else "different"


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 6) if b else None


def cmd_table(a) -> int:
    t0 = time.time()
    data, out = Data(a.data), Path(a.out)
    if data.synthetic:
        raise SystemExit("the command table reads documents: it does not run on a synthetic data folder")
    _complete_or_stop(data)
    _present_inputs_or_stop(data)
    if (out / "entry.json").exists() and not a.overwrite:
        raise SystemExit(f"{rel(out / 'entry.json')} exists: the entry decision was made (rule I6, 7.1, item 9)")
    if sha256_file(Path(a.calibration_rules)) != CALIBRATION_RULES_SHA256:
        raise SystemExit(f"{rel(Path(a.calibration_rules))}: this is not the fixed calibration file of the reader with "
                         "rules only (addendum I, chapter 6, item 10)")
    code_sha = design_code_sha256()
    fit = json.loads((out / "fit.json").read_text(encoding="utf-8"))
    if fit["outputs_sha256"]["oof.npz"] != sha256_file(out / "oof.npz"):
        raise SystemExit("oof.npz is not the file of fit.json")
    if fit["data_folder"]["sha256"] != data.input_hashes():
        raise SystemExit("the data folder changed after the command fit-oof: run fit-oof again")
    oof = np.load(out / "oof.npz")
    ids = [e["doc_id"] for e in data.meta]
    if [str(d) for d in oof["doc_ids"]] != [e["doc_id"] for e in data.with_states]:
        raise SystemExit("oof.npz and docs.json do not have the same documents")
    g = hd.dev_guard(ids)
    names = vb.load_rule_modules()
    if not set(RULE_MODULES) <= set(names) or any(vb.REGISTRY[f].__module__ not in RULE_MODULES for f in vb.FIELDS):
        raise SystemExit("the registry does not hold one reader of a rule module for each of the 7 fields")
    reference = json.loads(hd.REFERENCE.read_text(encoding="utf-8"))["documents"]
    weak = cmb.weak_tiers(Path(a.calibration_rules))

    # each document one time: the rule result and the out-of-fold answers of the heads
    docs = {}
    for e in data.meta:
        d = e["doc_id"]
        doc = vb.load_doc(d, allow_closed=True)
        raw = json.loads((vb.DOCS_DIR / f"{d}.json").read_text(encoding="utf-8"))
        rule = cvc.read_document(doc, strict=True)
        ho = None
        if e["has_states"]:
            i, s = e["state_index"], e["row_start"]
            ho = output_to_json(output_from_probabilities(
                doc, oof["q0"][i], oof["q1"][i],
                {f: oof["q2"][s:s + e["blocks"], j] for j, f in enumerate(Q2_FIELDS)}, False, f"fold_{e['fold']}"))
        docs[d] = (e, doc, raw.get("language"), rule, ho)
    # rule I4, item 20: a span that `Doc.candidate` refuses gives no value; it is counted and listed
    reader_errors = {f: [] for f in Q2_FIELDS}
    for d, v in docs.items():
        for f in Q2_FIELDS:
            rec = (v[4] or {"q2": {}})["q2"].get(f)
            if rec is not None and not rec["found"] and rec.get("reason") == "reader_error":
                reader_errors[f].append({"doc": d, "detail": rec.get("detail")})

    def ref_of(d, field):
        return reference[d]["fields"][MEASURE_ID.get(field, field)]

    # rule I7: the entry of the Q0 head
    n_g = hc = rc = labelled = 0
    confusion = Counter()
    for d, (e, doc, _lang, rule, ho) in docs.items():
        if e["q0_label"] is None or ho is None:
            continue
        labelled += 1
        if not ho["q0"]["given"]:
            continue
        n_g += 1
        hc += ho["q0"]["class"] == e["q0_label"]
        rc += cmb.rule_class(rule["kind"]) == e["q0_label"]
        confusion[f"label {e['q0_label']} / head {ho['q0']['class']}"] += 1
    q0 = q0_entry(n_g, hc, rc)
    q0.update(labelled_documents_with_states=labelled, label_against_head_class_in_g=dict(sorted(confusion.items())))

    # rule I6, chapter 7.2: the entry of the Q1 tier
    e1 = d1 = design1 = given_no_ref = acc_n = acc_k = 0
    for d, (e, doc, _lang, rule, ho) in docs.items():
        if ho is None:
            continue
        forms = hd.reference_forms(ref_of(d, "affair_type"))
        if forms:                          # chapter 7.2, item 7: the class with no limit against the one reference value
            acc_n += 1
            acc_k += ho["q1"]["class"] == forms[0]
        if rule["fields"]["affair_type"]["found"]:
            continue
        design1 += 1
        if ho["q1"]["type"] is None:
            continue
        if not forms:
            given_no_ref += 1
        elif vn.compare("affair_type", ho["q1"]["type"], forms)["equal"]:
            e1 += 1
        else:
            d1 += 1
    q1 = q1_entry(e1, d1)
    q1.update(documents_of_the_design_set=design1, given_types_with_no_reference=given_no_ref,
              information={"documents_with_states_and_a_reference": acc_n, "head_class_equal_to_the_reference": acc_k,
                           "accuracy": _ratio(acc_k, acc_n)})

    # rule I6, chapter 7.1: the design run with each band open, then the entry of each Q2 tier
    def run(entry):
        return {d: cmb.read_document_combined(doc, ho, entry, weak, True, None, rule)
                for d, (e, doc, _lang, rule, ho) in docs.items()}

    design_entry = {"q0": {"entered": q0["entered"]}, "q1": {"entered": q1["entered"]}, "q2": cmb.DESIGN_ENTRY_Q2}
    design = run(design_entry)
    q2 = {}
    for f in Q2_FIELDS:
        units = {b: [0, 0] for b in cmb.BANDS}
        called = Counter()
        for d, res in design.items():
            if docs[d][4] is None:
                continue
            call = res["heads"]["q2"].get(f)
            if call is None:
                continue
            called[call["called_because"]] += 1
            rec = res["fields"][f]
            if not (rec["found"] and rec["tier"].startswith("apertus_q2_")):
                continue
            if not ref_of(d, f).get("primary_set"):
                called["values_outside_the_primary_set"] += 1
                continue
            o = outcome(f, rec, ref_of(d, f))
            if o in ("equal", "different"):
                units[rec["detail"]["band"]][o == "different"] += 1
            else:
                called["values_with_no_reference"] += 1
        q2[f] = q2_entry(f, tuple(units["hi"]), tuple(units["lo"]))
        q2[f]["documents_of_the_design_set"] = dict(sorted(called.items()))
    entry = {"schema": "parlpdfech-heads2-entry/1", "version": VERSION, "made": now(), "status": hd.STATUS,
             "actor": hd.ACTOR, "mark": mark_of(a.overwrite),
             "rules": "addendum I, rules I6 (chapters 7.1 and 7.2) and I7; each value is out-of-fold",
             "fixed_numbers": {"lowest_units": MIN_UNITS, "q2_precision": "2 x equal >= units",
                               "q1_precision": "5 x equal >= 4 x units", "class_probability": CLASS_MIN,
                               "q2_value": P_VALUE_MIN, "band_limit": P_BAND_HI,
                               "q0": "50 or more documents; 10 x correct >= 9 x documents; head correct >= rule correct"},
             "order": "the entry of Q0, then the entry of Q1, then the design run of Q2 with these two decisions "
                      "(rule I6, chapter 7.1, item 13)",
             "q0": q0, "q1": q1, "q2": q2,
             "reader_error": {"rule": "addendum I, rule I4, item 20: a span that Doc.candidate refuses gives no value",
                              "count_by_field": {f: len(v) for f, v in reader_errors.items()},
                              "list": reader_errors},
             "code_sha256": code_sha,
             "inputs_sha256": {rel(out / "oof.npz"): sha256_file(out / "oof.npz"),
                               rel(out / "fit.json"): sha256_file(out / "fit.json"),
                               rel(hd.REFERENCE): sha256_file(hd.REFERENCE),
                               rel(Path(a.calibration_rules)): sha256_file(Path(a.calibration_rules)),
                               rel(hd.ADDENDUM): sha256_file(hd.ADDENDUM)}}
    write_json(out / "entry.json", entry)

    # the combined values file with the entry decisions, and the measures of the two readers
    final = run(entry)
    documents = {}
    for d, (e, doc, lang, rule, ho) in docs.items():
        r = final[d]
        documents[d] = {"language": lang, "s1_role": doc.s1_role, "kind": r["kind"], "kind_source": r["kind_source"],
                        "affair_type_of_the_cascade": r["affair_type_of_the_cascade"], "fields": r["fields"],
                        "heads": r.get("heads")}
    if design_code_sha256() != code_sha:
        raise SystemExit("a rule file, a cascade file or a reader file changed in the run of the command table")
    header = {"version": VERSION, "base_version": vb.VERSION, "status": hd.STATUS, "actor": hd.ACTOR,
              "mark": "after the opening" + ("; " + MARK if mark_of(a.overwrite) else ""),
              "part": "all development documents", "documents": len(documents),
              "form": "addendum G version 2, chapter 5.4, with the keys of the cascade reader and the key heads",
              "mode": "combined reader of addendum I; each head value is out-of-fold",
              "entry_sha256": sha256_file(out / "entry.json"),
              "sha256": code_sha}
    write_json(out / "values_dev_combined.json", {"header": header, "documents": documents})
    measures = dev_measures(docs, final, reference, entry, fit, g)
    measures["records_with_the_reason_reader_error_of_a_q2_head"] = {f: len(v) for f, v in reader_errors.items()}
    measures["seconds"] = round(time.time() - t0, 1)
    measures["outputs_sha256"] = {n: sha256_file(out / n) for n in ("entry.json", "values_dev_combined.json")}
    write_json(out / "measures_dev.json", measures)
    (out / "table_dev.md").write_text(table_md(measures, entry), encoding="utf-8")
    print(json.dumps({"q0_entered": q0["entered"], "q1_entered": q1["entered"],
                      "q2": {f: {"mode": v["mode"], "entered": v["entered"]} for f, v in q2.items()},
                      "out": rel(out), "seconds": measures["seconds"]}, indent=1))
    return 0


def design_code_sha256() -> dict:
    """The SHA-256 of each rule file, cascade file and reader file of the design run (chapter 7.1, item 14)."""
    src = Path(__file__).resolve().parent
    return {f"src/{n}.py": sha256_file(src / f"{n}.py") for n in (
        "m11_value_heads2", "m11_value_heads2_data", "m11_values_combined", "m11_values_cascade",
        "m11_cascade", "m11_value_heads", "m11_value_heads_data", "m11_values_base", "m11_value_norm",
        "m11_rules_pdf", *RULE_MODULES)} | {"src/m11_cascade.yaml": sha256_file(src / "m11_cascade.yaml")}


def dev_measures(docs: dict, final: dict, reference: dict, entry: dict, fit: dict, g: dict) -> dict:
    """Counts of the two readers on the primary set of each field, and the units of each Apertus tier."""
    fields = {}
    tiers: dict = {}
    replaced = differs = q1_used = 0
    for d, res in final.items():
        replaced += bool(res.get("kind_source", {}).get("replaced"))
        differs += bool((res.get("heads") or {}).get("q1_differs"))
        q1_used += bool((res.get("heads") or {}).get("q1_used"))
    for f in vb.FIELDS:
        m = MEASURE_ID.get(f, f)
        c = {"rules": Counter(), "combined": Counter()}
        for d, (e, doc, _lang, rule, ho) in docs.items():
            ref = reference[d]["fields"][m]
            if not ref.get("primary_set"):
                continue
            for name, rec in (("rules", rule["fields"][f]), ("combined", final[d]["fields"][f])):
                o = outcome(f, rec, ref)
                c[name][o] += 1
                c[name]["documents"] += 1
                if name == "combined" and rec["found"] and rec["tier"].startswith("apertus_") and o in ("equal", "different"):
                    t = tiers.setdefault((f, rec["tier"]), Counter())
                    t[o] += 1
        row = {}
        for name, k in c.items():
            n_ref = k["equal"] + k["different"] + k["not_found"]
            row[name] = {"documents": k["documents"], "equal": k["equal"], "different": k["different"],
                         "not_found": k["not_found"], "no_reference": k["no_reference"],
                         "precision": _ratio(k["equal"], k["equal"] + k["different"]),
                         "found_rate": _ratio(k["equal"] + k["different"], n_ref)}
        fields[f] = row
    return {"version": VERSION, "made": now(), "status": hd.STATUS, "actor": hd.ACTOR,
            "what": "counts on the primary set of each field; the reader with rules only and the combined reader; "
                    "each head value is out-of-fold; the first tool src/m11_value_cal.py gives the intervals",
            "outcome_names": {"equal": "correct", "different": "wrong", "not_found": "not found"},
            "guard": g, "documents": len(docs), "documents_with_no_states_file": sum(1 for v in docs.values() if v[4] is None),
            "label_counts": {n: v["label_counts"] for n, v in fit["heads"].items()},
            "lambdas": {n: v["lambdas"] for n, v in fit["heads"].items()},
            "fields": fields,
            "apertus_tiers": [{"field": f, "tier": t, "equal": k["equal"], "different": k["different"],
                               "precision": _ratio(k["equal"], k["equal"] + k["different"])}
                              for (f, t), k in sorted(tiers.items())],
            "documents_with_a_replaced_kind": replaced, "marks_q1_differs": differs, "types_from_q1": q1_used,
            "entry": {"q0": entry["q0"]["entered"], "q1": entry["q1"]["entered"],
                      "q2": {f: {"mode": v["mode"], "entered": v["entered"]} for f, v in entry["q2"].items()}}}


def table_md(m: dict, entry: dict) -> str:
    def yes(v) -> str:
        return "yes" if v else "no"

    def num(v) -> str:
        return "none" if v is None else f"{v:.3f}"

    L = ["# Gate GJ: the Apertus heads of addendum I on the development documents", "",
         f"Made on {m['made']} by `src/m11_value_heads2.py`. Status: PROPOSED, NOT RELEASED. "
         "Actor: workflow sub-agent (Claude Opus 5.5). No human checked this file.", "",
         "Written in English to the STE rules (ASD-STE100, Issue 9).", "",
         "Each head value is out-of-fold. The rule values have the mark \"after the opening\". "
         "The development values of an entered tier are optimistic (addendum I, chapter 13, item 4).", "",
         f"The job has {m['documents']} documents. {m['documents_with_no_states_file']} documents have no states file.", "",
         "## 1 Entry decisions", "", "Table 1: the `Q0` head (rule I7).", "",
         "| Documents of G | Head correct | Rule correct | Condition a | Condition b | Condition c | Entered |",
         "|---|---|---|---|---|---|---|"]
    q0 = entry["q0"]
    L.append(f"| {q0['documents_of_g']} | {q0['head_correct']} | {q0['rule_correct']} | {yes(q0['condition_a'])} | "
             f"{yes(q0['condition_b'])} | {yes(q0['condition_c'])} | {yes(q0['entered'])} |")
    q1 = entry["q1"]
    L += ["", "Table 2: the tier `apertus_q1` (rule I6, chapter 7.2).", "",
          "| Design set | Equal units | Different units | Entered | Accuracy on all documents with a reference |",
          "|---|---|---|---|---|",
          f"| {q1['documents_of_the_design_set']} | {q1['equal']} | {q1['different']} | {yes(q1['entered'])} | "
          f"{num(q1['information']['accuracy'])} |",
          "", "Table 3: the `Q2` tiers (rule I6, chapter 7.1).", "",
          "| Field | Tier | Equal units | Different units | Entered |", "|---|---|---|---|---|"]
    for f, v in entry["q2"].items():
        for t, k in v["tiers"].items():
            L.append(f"| `{f}` | `{t}` | {k['equal']} | {k['different']} | {yes(k['entered'])} |")
    L += ["", "## 2 The two readers on the primary set of each field", "",
          "Table 4: counts and measures. Precision is correct / (correct + wrong).", "",
          "| Field | Reader | Correct | Wrong | Not found | No reference | Precision | Found rate |",
          "|---|---|---|---|---|---|---|---|"]
    for f, row in m["fields"].items():
        for name in ("rules", "combined"):
            k = row[name]
            L.append(f"| `{f}` | {name} | {k['equal']} | {k['different']} | {k['not_found']} | {k['no_reference']} | "
                     f"{num(k['precision'])} | {num(k['found_rate'])} |")
    L += ["", "Table 5: the units of each Apertus tier in the combined values file.", "",
          "| Field | Tier | Correct | Wrong | Precision |", "|---|---|---|---|---|"]
    for t in m["apertus_tiers"]:
        L.append(f"| `{t['field']}` | `{t['tier']}` | {t['equal']} | {t['different']} | {num(t['precision'])} |")
    L += ["", f"Documents with a replaced kind: {m['documents_with_a_replaced_kind']}. "
              f"Marks `q1_differs`: {m['marks_q1_differs']}. Types from `Q1`: {m['types_from_q1']}.", "",
          "## 3 Labels of the fit", "",
          "Table 6: the label counts of each `Q2` head (addendum I, chapter 3.2, item 23).", "",
          "| Field | Documents of the fit | No reference | No positive block | Positive blocks | All blocks |",
          "|---|---|---|---|---|---|"]
    for f in Q2_FIELDS:
        k = m["label_counts"][f"q2_{f}"]
        L.append(f"| `{f}` | {k['documents_of_the_fit']} | {k['documents_with_no_reference']} | "
                 f"{k['documents_with_no_positive_block']} | {k['positive_blocks']} | {k['all_blocks']} |")
    err = m.get("records_with_the_reason_reader_error_of_a_q2_head") or {}
    L += ["", "Records of a `Q2` head with the reason `reader_error` (addendum I, rule I4, item 20): "
              + ", ".join(f"`{f}` {n}" for f, n in err.items()) + ".",
          "", "The interval of each measure comes from `src/m11_value_cal.py` on `values_dev_combined.json`.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ command apply

def _ids_arg(arg: str | None, states_dir: Path) -> list[str]:
    if arg is None:
        return sorted((p.stem for p in states_dir.glob("*.npz")), key=lambda s: (not s.isdigit(), int(s) if s.isdigit() else 0, s))
    if Path(arg).is_file():
        return [x for x in Path(arg).read_text(encoding="utf-8").split() if x]
    return [x for x in arg.split(",") if x]


def _key(p: Path | str) -> str:
    """The key of a file in the fix record: the path from the project folder, or the full path."""
    return rel(Path(p).resolve())


def ids_sha256(ids) -> str:
    """The definition of the key `doc_ids_sha256` of a job manifest (`src/m10_job.py`)."""
    import hashlib  # noqa: PLC0415

    return hashlib.sha256(json.dumps(sorted(str(d) for d in ids)).encode()).hexdigest()


def rules_folder_or_stop(rules: Path | str | None) -> None:
    """The one last run reads the rule files from the PDF alone (addendum I, chapter 10.3, item 18)."""
    if rules is None or Path(rules).resolve() != vb.RULES_DIR.resolve():
        raise SystemExit(f"--rules must be {rel(vb.RULES_DIR)} in the last run: the rule files from the PDF alone "
                         "(addendum I, chapter 10.3, item 18)")


def error_records(detail: str) -> dict:
    """The 7 records of a document whose block file cannot be read (chapter 10.1, item 14): no value, reason
    `reader_error`. The kind is not known: the selection is that of rule V1."""
    sel = cvc.selection(None, "none")
    return {f: dict(vb.NotFound(f, "reader_error", detail).to_json(), cascade=dict(sel[f])) for f in vb.FIELDS}


def last_run_checks(rec: dict, ids: list[str], ids_path: Path | None, fixed: dict, needed: dict, outputs: list,
                    split_of: dict, manifest_last: dict, manifest_dev: dict, expected: dict | None = None) -> None:
    """The checks of `apply --last-run` before a document is read (chapter 10; one event, fixed inputs).
    fixed: {argument: path} that must be a file of the fix record. needed: {argument: path} that must be given.
    outputs: paths that must not exist. A problem stops the command. No output is written."""
    expected = LAST_RUN_SETS if expected is None else expected
    bad = []
    if ids_path is None:
        bad.append("--ids must be the ids file of the fix record")
    elif rec["files"].get(_key(ids_path)) != sha256_file(ids_path) or rec.get("ids_file") != _key(ids_path):
        bad.append("the file --ids is not the ids file of the fix record")
    sets = rec.get("document_sets") or {}
    if len(ids) != sum(expected.values()) or len(set(ids)) != len(ids):
        bad.append(f"{len(ids)} ids ({len(set(ids))} different); the last run has {sum(expected.values())} documents")
    if set(ids) != set(sets):
        bad.append("the ids are not the ids of the fix record")
    if any(split_of.get(d) != (sets.get(d) or {}).get("set") for d in ids):
        bad.append("the set of an id differs from the fix record")
    count = Counter(split_of.get(d) for d in ids)
    if {k: count[k] for k in expected} != dict(expected):
        bad.append(f"documents of each set: {dict(count)}; expected {dict(expected)}")
    for name, p in {**fixed, **needed}.items():
        if p is None:
            bad.append(f"--{name} is necessary in the last run")
    for name, p in fixed.items():
        if p is not None and (not Path(p).is_file() or _key(p) not in rec["files"]):
            bad.append(f"--{name}: {_key(p)} is not a file of the fix record")
    for name, key in (("calibration-rules", "calibration_rules_only"), ("calibration-combined", "calibration_combined")):
        if fixed.get(name) is not None and rec.get(key) != _key(fixed[name]):
            bad.append(f"--{name}: the calibration files are not in the roles of the fix record (key {key})")
    if manifest_last.get("doc_ids_sha256") not in (None, ids_sha256(ids)):
        bad.append("the ids are not the ids of the manifest of the job values_last (key doc_ids_sha256)")
    for p in outputs:
        if p is not None and Path(p).exists():
            bad.append(f"{_key(p)} exists: a second call of the last run does not write it again (chapter 10.1, item 12)")
    fp = rec.get("model_fingerprint_of_the_development_job")
    if not fp or manifest_dev.get("model_fingerprint") != fp or manifest_last.get("model_fingerprint") != fp:
        bad.append("the model fingerprint of the job values_last is not that of the job values_dev")
    if manifest_last.get("template_sha256") != hd.TEMPLATE_SHA256 or manifest_last.get("template_id") != hd.TEMPLATE_ID:
        bad.append("the job values_last does not have the template of addendum I (rule I1, item 1)")
    if bad:
        raise SystemExit("the last run is refused: " + "; ".join(bad))


def cmd_apply(a) -> int:
    t0 = time.time()
    states_dir, out = Path(a.states), Path(a.out)
    ids_path = Path(a.ids) if a.ids and Path(a.ids).is_file() else None
    paths = [states_dir, out, a.docs, a.rules, a.heads, a.values_out, a.rules_values_out, a.entry,
             a.calibration_rules, a.calibration_combined, ids_path] + ([a.job] if a.last_run else [])
    access = hd.refuse_sealed(paths, a.last_run, "src/m11_value_heads2.py apply")
    if a.ids is None and a.values_out is not None:
        raise SystemExit("give --ids: a document with no states file must be in the values file")
    ids = _ids_arg(a.ids, states_dir)
    allowed = ("validation", "group7") if a.last_run else ("dev",)
    gd = guard.assert_allowed(ids, allowed)                 # a test document is refused in each mode (rule 6)
    if gd["refused"] or sum(gd["by_split"][s] for s in allowed) != len(ids):
        raise SystemExit(f"the guard refused ids: {gd['refused']} of {len(ids)} (allowed splits: {allowed})")
    rec = None
    strict = not (a.non_strict or a.last_run)               # the last run must end with a result (chapter 10.1)
    if a.last_run:
        rec = hd.check_fix_record()
        last_run_checks(
            rec, ids, ids_path,
            {"heads": a.heads, "entry": a.entry, "calibration-rules": a.calibration_rules,
             "calibration-combined": a.calibration_combined},
            {"docs": a.docs, "rules": a.rules, "values-out": a.values_out, "rules-values-out": a.rules_values_out},
            [out, a.values_out, a.rules_values_out], gd["split_of"],
            json.loads((Path(a.job) / "manifest.json").read_text(encoding="utf-8")),
            json.loads(DEV_MANIFEST.read_text(encoding="utf-8")))
        if a.model != "final":
            raise SystemExit("the last run uses the final head (rule I3, item 22)")
        rules_folder_or_stop(a.rules)
    fixed_no_rule = set((rec or {}).get("documents_with_no_rule_file") or [])

    def fixed_file(p: Path) -> Path:
        """In the last run a block file or a rule file must have the SHA-256 of the fix record."""
        if rec is not None and (rec.get("document_files") or {}).get(_key(p)) != sha256_file(p):
            raise SystemExit(f"{_key(p)}: the file differs from the fix record (chapter 10.2, item 3)")
        return p

    heads = Heads2.load(a.heads)
    if a.model == "final" and heads.models <= FINAL:
        raise SystemExit("the heads file has no final head: run the command final")
    folds_all = json.loads(hd.FOLDS_ALL.read_text(encoding="utf-8"))["documents"] if a.model == "oof" else {}
    want_values = a.values_out is not None
    entry = weak = None
    if want_values:
        entry = json.loads(Path(a.entry).read_text(encoding="utf-8"))
        weak = cmb.weak_tiers(Path(a.calibration_rules))
        vb.load_rule_modules()
    lookup = json.loads(Path(a.calibration_combined).read_text(encoding="utf-8"))["lookup"] if a.calibration_combined else None
    documents, combined, rules_only, no_states, other_suffix, no_rule_file = {}, {}, {}, [], [], []
    states_error, block_error = [], []
    counts = Counter()
    for d in ids:
        if a.docs:
            block_file = fixed_file(Path(a.docs) / f"{d}.json")
            rule_file = Path(a.rules) / f"{d}.json" if a.rules else None
            if rule_file is not None and rule_file.is_file():
                fixed_file(rule_file)
            else:
                if a.last_run and d not in fixed_no_rule:
                    raise SystemExit("a rule file of the fix record does not exist (chapter 10.2, item 3)")
                rule_file = None
                no_rule_file.append(d)
            try:
                doc = vb.load_from_block_file(block_file, rule_file)
                if doc.doc_id is not None and doc.doc_id != d:
                    raise ValueError("the block file has another doc id")
                raw = json.loads(block_file.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                if not a.last_run:
                    raise SystemExit(f"{d}: {type(e).__name__}: {e}") from None
                # chapter 10.1, item 14: the run must end with a result; this document gets no value
                block_error.append(d)
                counts[f"block_file_error_{type(e).__name__}"] += 1
                if want_values:
                    top = {"language": None, "s1_role": None, "kind": None,
                           "kind_source": {"from": "none", "rule": "V1", "error": "the block file cannot be read"},
                           "affair_type_of_the_cascade": "none"}
                    detail = f"{type(e).__name__}: the block file or the rule file cannot be read"
                    combined[d] = dict(top, fields=error_records(detail), heads=None)
                    rules_only[d] = dict(top, fields=error_records(detail))
                    counts["combined_reader_error"] += len(vb.FIELDS)
                continue
        else:
            doc = vb.load_doc(d, allow_closed=True)
            raw = json.loads((vb.DOCS_DIR / f"{d}.json").read_text(encoding="utf-8"))
        sp = states_dir / f"{d}.npz"
        ho = None
        if sp.is_file():
            model = FINAL if a.model == "final" else int(folds_all[d]["fold"])
            try:
                ho = output_to_json(apply_document(doc, hd.read_states(sp, d), heads, model, strict, not strict))
            except OtherSuffixIds:
                if not a.last_run:
                    raise
                other_suffix.append(d)          # chapter 10.1, item 13: no head value for this document
            except Exception as e:  # noqa: BLE001
                if not a.last_run:
                    raise
                states_error.append(d)          # chapter 10.1, item 13: no head value for this document
                counts[f"states_error_{type(e).__name__}"] += 1
        else:
            no_states.append(d)
        if ho is not None:
            for f, rec_ in ho["q2"].items():
                counts[f"q2_{f}_{'value' if rec_['found'] else rec_['reason']}"] += 1
            counts[f"q0_{ho['q0']['class'] if ho['q0']['given'] else 'no_given_class'}"] += 1
            counts[f"q1_{ho['q1']['class'] if ho['q1']['given'] else 'no_given_class'}"] += 1
            documents[d] = ho
        if want_values:
            rule = cvc.read_document(doc, strict=strict)
            res = cmb.read_document_combined(doc, ho, entry, weak, strict, None, rule)
            top = {"language": raw.get("language"), "s1_role": doc.s1_role}
            combined[d] = dict(top, kind=res["kind"], kind_source=res["kind_source"],
                               affair_type_of_the_cascade=res["affair_type_of_the_cascade"], fields=res["fields"],
                               heads=res.get("heads"))
            rules_only[d] = dict(top, kind=rule["kind"], kind_source=rule["kind_source"],
                                 affair_type_of_the_cascade=rule["affair_type_of_the_cascade"], fields=rule["fields"])
            for f, r in res["fields"].items():
                counts["combined_reader_error"] += bool(not r["found"] and r.get("reason") == "reader_error")
                if r["found"] and r["tier"].startswith("apertus_"):
                    counts[f"combined_{r['tier']}"] += 1
                    if lookup is not None:              # rule I6, chapter 7.3 (information; the writer has its own)
                        fold = None if a.model == "final" else int(folds_all[d]["fold"])
                        r["detail"] = dict(r.get("detail") or {},
                                           value_probability=value_probability(lookup, f, r["tier"], fold))
    header = {"version": VERSION, "made": now(), "status": hd.STATUS, "actor": hd.ACTOR, "states": rel(states_dir),
              "model": "the final head" if a.model == "final" else "out-of-fold: the head of the fold of each document",
              "heads_sha256": sha256_file(Path(a.heads)), "layer": heads.layer, "last_run": bool(a.last_run),
              "last_run_access": access, "fix_record_sha256": sha256_file(hd.FIX_RECORD) if a.last_run else None,
              "strict": strict, "documents": len(ids), "documents_with_no_states_file": no_states,
              "documents_with_other_suffix_ids": other_suffix, "documents_with_no_rule_file": no_rule_file,
              "documents_with_a_states_error": states_error, "documents_with_a_block_file_error": block_error,
              "rule_files": rel(Path(a.rules)) if a.rules else rel(vb.RULES_DIR),
              "guard": {"by_split": gd["by_split"], "refused": gd["refused"], "allowed": list(allowed)},
              "form": "q2: the JSON form of ValueCandidate or NotFound of src/m11_values_base.py; the tier id is the "
                      "band id; the combined reader gives the tier id of the entry record"}
    write_json(out, {"header": header, "documents": documents})
    if want_values:
        vh_ = dict(header, form="addendum G version 2, chapter 5.4, with the keys of the cascade reader",
                   entry_sha256=sha256_file(Path(a.entry)))
        write_json(Path(a.values_out), {"header": dict(vh_, mode="combined reader of addendum I"), "documents": combined})
        if a.rules_values_out:
            write_json(Path(a.rules_values_out), {"header": dict(vh_, mode="rules only"), "documents": rules_only})
    print(json.dumps({"documents": len(ids), "documents_with_no_states_file": len(no_states),
                      "documents_with_other_suffix_ids": len(other_suffix),
                      "documents_with_a_states_error": len(states_error),
                      "documents_with_a_block_file_error": len(block_error),
                      "documents_with_no_rule_file": len(no_rule_file),
                      "counts": dict(sorted(counts.items())), "out": rel(out), "seconds": round(time.time() - t0, 1)}, indent=1))
    return 0


# ------------------------------------------------------------------ command fix-record (chapter 10.2)

FIX_FILES = (
    "src/m11_values_type_number.py", "src/m11_values_title.py", "src/m11_values_dates_responder.py",
    "src/m11_values_sponsor.py", "src/m11_values_base.py", "src/m11_value_norm.py",
    "src/m11_cascade.py", "src/m11_cascade.yaml", "src/m11_values_cascade.py", "src/m11_values_combined.py",
    "src/m11_rules_pdf.py",
    "src/m11_value_heads2.py", "src/m11_value_heads2_data.py", "src/m11_value_heads.py", "src/m11_value_heads_data.py",
    "daten/gj_values/heads2/heads2.npz", "daten/gj_values/heads2/fit.json", "daten/gj_values/heads2/oof.npz",
    "daten/gj_values/heads2/entry.json",
    "src/m11_value_reference.py", "src/m02_ech_regeln.py",
    "src/m11_value_cal.py", "src/m11_second_calc.py", "src/m10_calibrate.py", "src/m11_second_heads2.py",
    "src/m11_heads2_convert.py", "src/m11_heads2_last_measures.py",
    "daten/gj/jobs/values_dev/template.json", "daten/gj/jobs/values_dev/manifest.json",
    "src/m11_prompts_values.py", "src/m10_prompts.py", "src/m10_vm_states.py",
    "src/m10_guard.py", "daten/gj_values/folds_all.json",
    "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md",
    "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md",
)


def design_inputs_problems(design: Path) -> list[str]:
    """Chapter 7.1, item 14: each file that the command `table` recorded must be the present file.
    The sources are `entry.json` (keys `inputs_sha256` and `code_sha256`) and the header of the combined values."""
    bad = []
    entry_file, comb_file = design / "entry.json", design / "values_dev_combined.json"
    for q in (entry_file, comb_file):
        if not q.is_file():
            return [f"{_key(q)} does not exist"]
    entry = json.loads(entry_file.read_text(encoding="utf-8"))
    header = json.loads(comb_file.read_text(encoding="utf-8"))["header"]
    if not entry.get("code_sha256") or not entry.get("inputs_sha256") or not header.get("sha256"):
        bad.append("entry.json or the combined values file has no record of its input files")
    if header.get("entry_sha256") != sha256_file(entry_file):
        bad.append("the combined values file was not made with this entry.json")
    recorded = [("entry.json", k, v) for name in ("inputs_sha256", "code_sha256") for k, v in (entry.get(name) or {}).items()]
    recorded += [("values_dev_combined.json", k, v) for k, v in (header.get("sha256") or {}).items()]
    for where, path, digest in recorded:
        q = ROOT / path
        if not q.is_file() or sha256_file(q) != digest:
            bad.append(f"{path} differs from the record in {where}")
    return sorted(set(bad))


def document_files(ids: list[str], docs: Path, rules: Path) -> tuple[dict, list[str], list[str]]:
    """({path: SHA-256} of each block file and rule file, ids with no block file, ids with no rule file).
    The files are hashed only. No file is parsed."""
    out, no_block, no_rule = {}, [], []
    for d in ids:
        b, r = Path(docs) / f"{d}.json", Path(rules) / f"{d}.json"
        if b.is_file():
            out[_key(b)] = sha256_file(b)
        else:
            no_block.append(d)
        if r.is_file():
            out[_key(r)] = sha256_file(r)
        else:
            no_rule.append(d)
    return out, no_block, no_rule


def fix_record_object(files: list[Path], ids_path: Path, ids: list[str], split_of: dict, parliament_of: dict,
                      doc_files: dict, no_rule: list[str], calibration_rules: Path, calibration_combined: Path,
                      manifest_dev: dict, guard_sources: dict | None = None, more: dict | None = None) -> dict:
    return {**(more or {}), "schema": "parlpdfech-heads2-last-run-fix/2", "version": VERSION, "time": now(), "status": hd.STATUS,
            "actor": hd.ACTOR, "rule": "addendum I, chapter 10.2, items 1 and 2",
            "model_fingerprint_of_the_development_job": manifest_dev.get("model_fingerprint"),
            "calibration_rules_only": _key(calibration_rules), "calibration_combined": _key(calibration_combined),
            "ids_file": _key(ids_path), "documents": len(ids),
            "documents_by_set": dict(sorted(Counter(split_of[d] for d in ids).items())),
            "document_sets": {d: {"set": split_of[d], "parliament": parliament_of.get(d)} for d in ids},
            "documents_with_no_rule_file": no_rule,
            "document_files": doc_files, "guard_sources_sha256": guard_sources,
            "files": {_key(p): sha256_file(p) for p in files}}


def rules_build_problems(build: dict, documents: int, no_rule: int, tool_sha256: str) -> list[str]:
    """The record of the sealed build of `src/m11_rules_pdf.py` against the ids file. Counts only."""
    bad = []
    if build.get("sealed_build") is not True or sorted(build.get("splits") or []) != sorted(LAST_RUN_SETS):
        bad.append("it is not the record of a sealed build of the sets validation and group7")
    if build.get("documents") != documents:
        bad.append(f"it has {build.get('documents')} documents; the ids file has {documents}")
    if build.get("failures") != no_rule or build.get("files_written") != documents - no_rule:
        bad.append(f"it has {build.get('files_written')} files and {build.get('failures')} failures; the ids file "
                   f"has {no_rule} documents with no rule file")
    if build.get("files_in_output_folder_of_these_ids") != build.get("files_written"):
        bad.append("the output folder holds a file of an id that the build did not write")
    if (build.get("tool") or {}).get("sha256") != tool_sha256:
        bad.append("src/m11_rules_pdf.py changed after the sealed build")
    if (build.get("export_fields_given") or {}).get("found") is not False:
        bad.append("the build did not give the empty export fields")
    return bad


def guard_ids(names: list[str], splits: tuple[str, ...], expected: dict) -> tuple[list[str], dict]:
    """(ids in number order, count of each split) of the names that the guard gives one of the splits.
    A test document, a refusal that is not the split, or another count stops. The message has counts only."""
    ver = guard.check(names, splits)
    test = [v for v in ver if v["split"] == "test" or any(r.split(" ", 1)[0] in ("G5", "G6", "G7") for r in v["refused"])]
    if test:
        raise SystemExit(f"guard: {len(test)} test documents in the names: refused (process rule 6)")
    other = [v for v in ver if v["refused"] and not all(r.startswith("G9") for r in v["refused"])]
    if other:
        raise SystemExit(f"guard: {len(other)} names with a refusal that is not the split: refused")
    take = sorted((v["doc_id"] for v in ver if not v["refused"]), key=int)
    split_of = {v["doc_id"]: v["split"] for v in ver if not v["refused"]}
    count = dict(sorted(Counter(split_of[d] for d in take).items()))
    if count != dict(sorted(expected.items())) or len(set(take)) != len(take):
        raise SystemExit(f"the guard gives {count}; expected {dict(expected)}")
    return take, count


def cmd_last_run_ids(a) -> int:
    """Write the ids file of the last run from file names and the guard. No file of a document is opened."""
    out = Path(a.out)
    hd.refuse_sealed((a.docs, out), False, "src/m11_value_heads2.py last-run-ids")
    if out.name.startswith(("id_", ".env")):
        raise SystemExit("the name of the ids file must not start with id_ or .env (the second tool refuses it)")
    if out.exists():
        raise SystemExit(f"{rel(out)} exists: the ids file was written")
    names = sorted((q.stem for q in Path(a.docs).glob("*.json") if q.stem.isdigit()), key=int)
    ids, count = guard_ids(names, tuple(LAST_RUN_SETS), LAST_RUN_SETS)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ids) + "\n", encoding="utf-8")
    print(json.dumps({"out": rel(out), "sha256": sha256_file(out), "names": len(names), "ids": len(ids),
                      "ids_by_set": count, "doc_ids_sha256": ids_sha256(ids)}))
    return 0


def cmd_fix_record(a) -> int:
    fix = hd.FIX_RECORD if a.out is None else Path(a.out)
    if fix.exists():
        raise SystemExit(f"{rel(fix)} exists: the fix record was written")
    real = bool(a.last_run) or fix.resolve() == hd.FIX_RECORD.resolve()     # else: a rehearsal with --out
    if real:
        rules_folder_or_stop(a.rules)
        if a.rules_build_record is None:
            a.rules_build_record = RULES_BUILD_RECORD_LAST
    named = [a.calibration_rules, a.calibration_combined, *a.extra, a.manifest, a.ids, a.docs, a.rules, a.design, fix,
             a.rules_build_record]
    named = [q for q in named if q is not None]
    hd.refuse_test_paths(named)
    sealed = [Path(p).resolve() for p in named if hd.is_sealed(p)]
    if sealed and not a.last_run:
        raise hd.Sealed(f"sealed until the one last run: {[rel(p) for p in sealed]}. Give the flag --last-run. "
                        "The command hashes these files. It parses the ids file only.")
    files = [ROOT / f for f in FIX_FILES] + [Path(p).resolve() for p in (a.calibration_rules, a.calibration_combined)]
    files += [Path(p).resolve() for p in a.extra] + [Path(a.manifest).resolve(), Path(a.ids).resolve()]
    if a.rules_build_record is not None:
        files.append(Path(a.rules_build_record).resolve())
    missing = [rel(p) for p in files if not p.is_file()]
    if missing:
        raise SystemExit(f"files of the fix record that do not exist: {missing}")
    if sha256_file(Path(a.calibration_rules)) != CALIBRATION_RULES_SHA256:
        raise SystemExit("--calibration-rules is not the fixed calibration file of the reader with rules only "
                         "(addendum I, chapter 6, item 10)")
    bad = design_inputs_problems(Path(a.design))
    if bad:
        raise SystemExit("a file changed after the command table (addendum I, chapter 7.1, item 14): " + "; ".join(bad))
    ids = [x for x in Path(a.ids).read_text(encoding="utf-8").split() if x]
    g = guard.assert_allowed(ids, tuple(LAST_RUN_SETS))
    count = {k: g["by_split"][k] for k in LAST_RUN_SETS}
    if g["refused"] or count != LAST_RUN_SETS or len(set(ids)) != LAST_RUN_DOCUMENTS:
        raise SystemExit(f"the ids file has {len(ids)} ids by set {count}; the last run has {LAST_RUN_SETS}")
    doc_files, no_block, no_rule = document_files(ids, Path(a.docs), Path(a.rules))
    if no_block:
        raise SystemExit(f"{len(no_block)} documents of the ids file have no block file in {rel(Path(a.docs))}")
    if len(no_rule) != a.permit_no_rule_file:
        raise SystemExit(f"{len(no_rule)} documents of the ids file have no rule file in {rel(Path(a.rules))}: run the "
                         "sealed build of src/m11_rules_pdf.py. The option --permit-no-rule-file N permits exactly N "
                         "documents: the failure count of the record of that build.")
    more = {"rule_files_folder": rel(Path(a.rules)), "rules_build_record": None, "ids_equal_to_the_manifest_of_the_job": None}
    if a.rules_build_record is not None:
        build = json.loads(Path(a.rules_build_record).read_text(encoding="utf-8"))
        bad = rules_build_problems(build, len(ids), len(no_rule), sha256_file(ROOT / "src/m11_rules_pdf.py"))
        if bad:
            raise SystemExit(f"{rel(Path(a.rules_build_record))}: " + "; ".join(bad))
        more["rules_build_record"] = {"path": _key(a.rules_build_record), "files_written": build["files_written"],
                                      "failures": build["failures"],
                                      "outputs_sha256_canonical": build.get("outputs_sha256_canonical")}
    if real:                                # one key of the manifest of the job; no other key is used
        want = json.loads(Path(a.manifest).read_text(encoding="utf-8")).get("doc_ids_sha256")
        if want is not None and want != ids_sha256(ids):
            raise SystemExit("the ids file does not hold the ids of the manifest of the job (key doc_ids_sha256)")
        more["ids_equal_to_the_manifest_of_the_job"] = True if want is not None else None
    rec = fix_record_object(files, Path(a.ids), ids, g["split_of"], g["parliament_of"], doc_files, no_rule,
                            Path(a.calibration_rules), Path(a.calibration_combined),
                            json.loads(DEV_MANIFEST.read_text(encoding="utf-8")), dict(guard.tables().sources), more)
    write_json(fix, rec)
    if a.last_run:
        hd.refuse_sealed(sealed, True, "src/m11_value_heads2.py fix-record", fix)
    print(json.dumps({"out": rel(fix), "sha256": sha256_file(fix), "files": len(rec["files"]),
                      "documents": len(ids), "document_files": len(doc_files),
                      "documents_with_no_rule_file": len(no_rule)}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="the Apertus heads of addendum I")
    ap.add_argument("--last-run", action="store_true", help="open the sealed paths; needs the fix record")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fit-oof", "table", "final"):
        p = sub.add_parser(name)
        p.add_argument("--data", type=Path, default=OUT_DIR, help="folder of src/m11_value_heads2_data.py")
        p.add_argument("--out", type=Path, default=OUT_DIR)
        p.add_argument("--threads", type=int, default=0)
        if name != "final":
            p.add_argument("--overwrite", action="store_true", help="a second run; the record gets the mark")
    sub.choices["table"].add_argument("--calibration-rules", type=Path, default=cmb.CALIBRATION_RULES)
    p = sub.add_parser("apply")
    p.add_argument("--states", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True, help="the heads output (JSON)")
    p.add_argument("--heads", type=Path, default=OUT_DIR / "heads2.npz")
    p.add_argument("--ids", default=None, help="ids with commas, or a file with ids; default: each file of --states")
    p.add_argument("--docs", type=Path, default=None, help="folder with block files <id>.json; default: the project loader")
    p.add_argument("--rules", type=Path, default=None, help="folder with rule files <id>.json (with --docs)")
    p.add_argument("--model", choices=("final", "oof"), default="final")
    p.add_argument("--entry", type=Path, default=cmb.ENTRY_FILE)
    p.add_argument("--calibration-rules", type=Path, default=cmb.CALIBRATION_RULES)
    p.add_argument("--calibration-combined", type=Path, default=None)
    p.add_argument("--values-out", type=Path, default=None, help="also write the values file of the combined reader")
    p.add_argument("--rules-values-out", type=Path, default=None, help="also write the values file of the rules")
    p.add_argument("--non-strict", action="store_true", help="an error of a reader gives the reason reader_error")
    p.add_argument("--job", type=Path, default=LAST_RUN_JOB, help="the job folder of the last run (with --last-run only)")
    p = sub.add_parser("fix-record")
    p.add_argument("--calibration-rules", type=Path, required=True)
    p.add_argument("--calibration-combined", type=Path, required=True)
    p.add_argument("--manifest", type=Path, default=LAST_RUN_JOB / "manifest.json")
    p.add_argument("--ids", type=Path, required=True, help="the ids file of the 872 documents of the last run")
    p.add_argument("--docs", type=Path, required=True, help="folder with the block files <id>.json of the last run")
    p.add_argument("--rules", type=Path, required=True, help="folder with the rule files <id>.json of the last run")
    p.add_argument("--design", type=Path, default=OUT_DIR, help="folder with entry.json and values_dev_combined.json")
    p.add_argument("--extra", type=Path, nargs="*", default=[])
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--rules-build-record", type=Path, default=None,
                   help="the record of the sealed build of src/m11_rules_pdf.py (default in the last run: "
                        "daten/gj_values/round4/rules_pdf_build_last_run.json)")
    p.add_argument("--permit-no-rule-file", type=int, default=0,
                   help="exactly N documents have no rule file: the failure count of the sealed build")
    p = sub.add_parser("last-run-ids")
    p.add_argument("--docs", type=Path, default=vb.DOCS_DIR, help="folder with the block files <id>.json")
    p.add_argument("--out", type=Path, default=LAST_RUN_IDS)
    a = ap.parse_args()
    if a.cmd in ("fit-oof", "table", "final"):
        hd.refuse_sealed((a.data, a.out, getattr(a, "calibration_rules", None)), a.last_run,
                         f"src/m11_value_heads2.py {a.cmd}")
        if a.last_run:
            raise SystemExit(f"the command {a.cmd} reads development documents only; it has no last-run mode")
    return {"fit-oof": cmd_fit_oof, "table": cmd_table, "final": cmd_final, "apply": cmd_apply,
            "fix-record": cmd_fix_record, "last-run-ids": cmd_last_run_ids}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

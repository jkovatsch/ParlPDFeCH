"""The Apertus tier of the value readers: linear read-out heads on the stored block states of Apertus-v1.5-8B.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: PROPOSED, NOT RELEASED. No human checked this file. This file changes no existing file.
Rules: crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-h.md (PROPOSED).

1 What the tier is
  A head is one L2-regularised logistic regression on the stored state of a block (one layer, 4096 values). It
  gives each block of a document a probability "this block holds the value of the field". Code then takes the
  value out of the block with a general pattern. The head finds the block. It reads no value.
  Fields (registry ids of src/m11_values_base.py): title, affair_number, sponsor, submission_date.
  Tier ids: apertus_head_title, apertus_head_number, apertus_head_author, apertus_head_date.

2 The stored states (src/m10_vm_states.py)
  One file for each document: key `states` float16 [suffixes, layers, 4096], keys `layers` and `suffix_ids`.
  The suffix "D1" is the document question. The suffix "B<n>" is the block "B<n>" of the block file.
  A new PDF has no stored states. Thus the tier needs one Apertus forward pass (a GPU) for a new PDF.

3 Weak labels of the fit (made by src/m11_value_heads_data.py; open part only)
  Source a: the block holds the reference value after the normalisation of src/m11_value_norm.py.
  Source b: the block of the rule value, if the tier of that value has a precision of 0.9 or more on the open part.
  Positive = a or b. Negative = each other block of a document that has one or more positive blocks.

4 Selection (open part only; 5 folds grouped by parliament, daten/gj_values/folds.json)
  Layer (16, 20, 24) and lambda (0.0001, 0.001, 0.01, 0.1): the lowest out-of-fold log loss of the block label.
  Threshold, the number of blocks that are tried and the pattern option: command `choose` (rule in CHOICE_RULE).
  The final head of a field is fitted on all open documents. The 5 fold heads are stored with it.
  Out-of-fold: a document of fold k is read with the head that was fitted on the 4 other folds.

5 Value patterns (general; no cue word and no position rule)
  submission_date  the first date of the block (find_dates of the base module)
  affair_number    a number token of the block: the token form `_NUM` of src/m11_values_type_number.py, with the
                   exclusions `refuse` of that module. A token with a separator or with letters comes first.
  sponsor          a person name of the block: `_name_at` of src/m11_values_sponsor.py. Options: the first name of
                   2 or more words with a known first name; the first name with a party mark after it.
                   normalised = the family name tokens.
  title            the block text, cleaned as the title module does it (`_try_type`, `_run_from`, `_result`).
                   Option: one text in quotation marks in the block is the title.
  The command choose selects one option for each field (key OPTIONS).

6 The combined reader
  read_<field>_combined: the rule reader first. The Apertus tier only if the rule reader returns not found and
  the field is in the key `combined_fields` of heads.json. A rule value is never replaced.
  No precision limit closes a tier. `run --fields` reads with a part of the fields only (no file changes).

7 Commands
  fit           fit the heads (needs the data folder of src/m11_value_heads_data.py); writes heads.npz, fit.json
  candidates    out-of-fold: the 3 blocks with the highest probability and their values, for each open document
  choose        the curves and the choices; writes curve_open.json and heads.json
  run           the combined reader on a part; writes a values file in the form of addendum G, chapter 5.4
  compare       the measures of two measures files side by side; writes compare_open.json
  closed-check  write closed_check.json (SHA-256 values only). `run --part closed` stops without it.
  Only `run --part closed` reads documents of the closed part. No other command reads them.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_value_heads.py fit --data SCRATCH/probe/data
  uv run --offline --frozen --no-sync python src/m11_value_heads.py candidates --out SCRATCH/design/candidates.json
  uv run --offline --frozen --no-sync python src/m11_value_heads.py choose --candidates SCRATCH/design/candidates.json
  uv run --offline --frozen --no-sync python src/m11_value_heads.py run --part open
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402
import m11_values_base as vb  # noqa: E402
import m11_values_dates_responder as dr  # noqa: E402,F401  (registers its readers)
import m11_values_sponsor as sp  # noqa: E402
import m11_values_title as tt  # noqa: E402
import m11_values_type_number as tn  # noqa: E402

VERSION = "m11-value-heads-1"
ROOT = vb.ROOT
OUT_DIR = ROOT / "daten/gj_values/heads"
HEADS_NPZ = OUT_DIR / "heads.npz"
HEADS_JSON = OUT_DIR / "heads.json"
FIT_JSON = OUT_DIR / "fit.json"
CURVE_JSON = OUT_DIR / "curve_open.json"
CLOSED_CHECK = OUT_DIR / "closed_check.json"
OPENING = ROOT / "daten/gj_values/opening.json"
RUN_RECORD = ROOT / "daten/gj/fullrun_b1s_dev/runs/run_1.json"
REFERENCE_OPEN = ROOT / "daten/gj_values/reference_open.json"
VALUES_OPEN = ROOT / "daten/gj_values/values_open.json"
FIELDS = ("title", "affair_number", "sponsor", "submission_date")         # registry ids
MEASURE_ID = {"title": "title", "affair_number": "affair_number", "sponsor": "first_author",
              "submission_date": "submission_date"}
TIER = {"title": "apertus_head_title", "affair_number": "apertus_head_number", "sponsor": "apertus_head_author",
        "submission_date": "apertus_head_date"}
LAYERS = (16, 20, 24)
LAMBDAS = (1e-4, 1e-3, 1e-2, 1e-1)
FOLDS = 5
FINAL = FOLDS                 # index of the head that was fitted on all open documents
HIDDEN = 4096
MAX_ITER = 100
TOP_K_MAX = 3
THRESHOLDS = tuple(round(0.05 * i, 2) for i in range(1, 20)) + (0.975, 0.99)
OPTIONS = {"title": ("block", "quote_then_block"), "affair_number": ("structured_first", "structured_only"),
           "sponsor": ("known_first_name", "party_then_known", "two_words"), "submission_date": ("first_date", "one_day_only")}
NEGATIVES = "positive_documents"      # documents of the fit (command fit, option --negatives)
MIN_UNITS = 30                # addendum G, chapter 7, item 14: a tier with fewer units gives the status unsure
INFO_PRECISION = 0.8          # information only: heads.json says if the tier of a field has this precision
CHOICE_RULE = (
    "Set: the open documents with a reference for which the rule reader returned not found; values out-of-fold. "
    "A setting is (pattern option, number of blocks 1 or 3, threshold of the grid). Permitted settings have "
    f"{MIN_UNITS} or more units (equal + different). The chosen setting has the highest precision; then the most "
    "equal values; then 1 block before 3; then the lower threshold; then the first option. "
    "A field with a chosen setting is in the key combined_fields: no precision limit closes a tier. "
    f"heads.json says for each field if the chosen setting has a precision of {INFO_PRECISION} or more "
    "(whole numbers: 5 x equal >= 4 x units). This is information for the decision of the main agent.")
NUM_TOKEN_RX = re.compile(r"(?<![\w.,/-])(" + tn._NUM + r")" + tn._END)
WORD_START_RX = re.compile(r"(?<![^\W\d_])[A-ZÀ-ÖØ-Þ]")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ states

class DocStates:
    """The stored states of one document. `block_states(layer)` gives float32 [blocks, 4096] in reading order."""

    def __init__(self, layers, suffix_ids, states):
        self.layers = [int(k) for k in layers]
        self.suffix_ids = [str(s) for s in suffix_ids]
        self.states = states                              # float16 [suffixes, layers, 4096]
        if self.suffix_ids[:1] != ["D1"]:
            raise ValueError("the first suffix of a states file must be D1")
        if states.shape != (len(self.suffix_ids), len(self.layers), HIDDEN):
            raise ValueError("the states do not have the form [suffixes, layers, 4096]")

    @property
    def block_ids(self) -> list[str]:
        return self.suffix_ids[1:]

    def block_states(self, layer: int) -> np.ndarray:
        return np.asarray(self.states[1:, self.layers.index(int(layer)), :], dtype=np.float32)


def read_states_file(path: str | Path) -> DocStates:
    """A states file in the form of src/m10_vm_states.py. No project path is used (for a PDF of the package)."""
    with np.load(Path(path), allow_pickle=False) as z:
        return DocStates(z["layers"], z["suffix_ids"], z["states"])


_RUN: dict | None = None


def load_states(doc_id: str | int, allow_closed: bool = False) -> DocStates | None:
    """The stored states of a development document, or None if the document has no states file. The id passes
    src/m10_guard.py (split dev) and the part test of folds.json BEFORE a file of the document is opened."""
    global _RUN
    d = str(doc_id)
    g = guard.assert_allowed([d], ("dev",))
    if g["refused"] or g["by_split"]["dev"] != 1:
        raise vb.NotADevDocument(f"{d}: the guard refused the id")
    entry = vb.folds()["documents"].get(d)
    if entry is None:
        raise vb.NotADevDocument(f"{d}: not a development document of daten/gj_values/folds.json")
    if entry["part"] != "open" and not allow_closed:
        raise vb.ClosedParliament(f"{d}: the document is in a closed parliament")
    if _RUN is None:
        _RUN = json.loads(RUN_RECORD.read_text(encoding="utf-8"))["results"]
    st = (_RUN.get(d) or {}).get("states")
    if not st or not st.get("file") or not (ROOT / st["file"]).is_file():
        return None
    with np.load(ROOT / st["file"], allow_pickle=False) as z:
        if str(z["doc_id"]) != d:
            raise ValueError(f"{d}: the states file has another doc id")
        return DocStates(z["layers"], z["suffix_ids"], z["states"])


# ------------------------------------------------------------------ heads

class Heads:
    """The stored heads: for each field 6 weight vectors (fold heads 0 to 4, final head 5) and the choices."""

    def __init__(self, npz: Path | None = None, record: Path | None = None, choices: dict | None = None):
        npz, record = npz or HEADS_NPZ, record or HEADS_JSON
        with np.load(npz, allow_pickle=False) as z:
            self.u = {f: z[f"{f}__u"] for f in FIELDS}          # [6, 4096]: weights on the raw state
            self.c = {f: z[f"{f}__c"] for f in FIELDS}          # [6]
            self.layer = {f: int(z[f"{f}__layer"]) for f in FIELDS}
        if choices is None:
            choices = json.loads(Path(record).read_text(encoding="utf-8")) if Path(record).is_file() else {}
        self.choices = choices.get("fields", {})
        self.combined_fields = tuple(choices.get("combined_fields", ()))

    def probabilities(self, field: str, states: DocStates, model: int = FINAL) -> np.ndarray:
        x = states.block_states(self.layer[field]).astype(np.float64)
        z = x @ self.u[field][model].astype(np.float64) + float(self.c[field][model])
        return 1.0 / (1.0 + np.exp(-z))


_HEADS: Heads | None = None


def default_heads() -> Heads:
    global _HEADS
    if _HEADS is None:
        _HEADS = Heads()
    return _HEADS


# ------------------------------------------------------------------ value patterns

def _date_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    hits = vb.find_dates(b.text, b.char_start)
    days = {h.iso for h in hits}
    return [{"start": h.start, "end": h.end, "normalised": h.iso,
             "options": ["first_date"] + (["one_day_only"] if len(days) == 1 else [])} for h in hits[:1]]


def _number_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    """The number tokens of the block in reading order; a token with a separator or with letters comes first."""
    structured, plain = [], []
    for ln in b.lines:
        t = ln.text
        for m in NUM_TOKEN_RX.finditer(t):
            s, e = tn._strip_council(t, m.start(1), m.end(1))
            e = tn._extend_tail(t, s, e)
            val = t[s:e]
            if tn.refuse(t, s, e, False) or tn._month_year(val) or (val.isdigit() and len(val) > 7):
                continue
            item = {"start": ln.char_start + s, "end": ln.char_start + e, "normalised": tn.normal_number(val)}
            if val.isdigit():
                if len(val) >= 2:
                    plain.append({**item, "options": ["structured_first"]})
            else:
                structured.append({**item, "options": ["structured_first", "structured_only"]})
    return (structured or plain)[:1]


def _author_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    """The person names of the block in reading order (`_name_at` of the sponsor module), and one name for each
    option. known_first_name: the first name of 2 or more words with a known first name (at the start, or at the
    end of a name of 2 words). two_words: the first name of 2 or more words. party_then_known: the first name
    with a party mark directly after it (`_party_after`; 1 word is sufficient); if no such name, known_first_name."""
    orig = sp._flat(b.text)
    picks: dict[str, dict] = {}
    pos = n = 0
    for m in WORD_START_RX.finditer(orig):
        if m.start() < pos:
            continue
        name = sp._name_at(orig, m.start())
        if name is None:
            continue
        pos = name.end
        norm = sp._normalise(name.split()[1])
        if not norm:
            continue
        item = {"start": b.char_start + name.start, "end": b.char_start + name.end, "normalised": norm}
        two = len(name.words) >= 2
        if two:
            picks.setdefault("two_words", item)
            if name.first_known or sp.first_last_known(name):
                picks.setdefault("known_first_name", item)
        if sp._party_after(orig, name.end) is not None:
            picks.setdefault("party", item)
        n += 1
        if n >= 40 or ("party" in picks and "known_first_name" in picks):
            break
    chosen = {"known_first_name": picks.get("known_first_name"), "two_words": picks.get("two_words"),
              "party_then_known": picks.get("party") or picks.get("known_first_name")}
    out: list[dict] = []
    for option, item in chosen.items():
        if item is None:
            continue
        same = next((x for x in out if (x["start"], x["end"]) == (item["start"], item["end"])), None)
        if same is None:
            out.append({**item, "options": [option]})
        else:
            same["options"].append(option)
    return out


QUOTE_RX = re.compile(r"[«\"“„]\s*([^«»\"“”„]{3,400}?)\s*[»\"”“]")


def _title_values(doc: vb.Doc, b: vb.Block) -> list[dict]:
    """Option block: the block text as a title. If the block starts with a type word, the title module cuts it
    (`_try_type`), and the result counts only if its span is in this block. Else the lines of the block
    (`_run_from`), cleaned by `_result`. Option quote_then_block: if the block holds exactly one text in quotation
    marks and other text outside the marks, the text in the marks is the title; else as the option block."""
    if not b.lines:
        return []
    head = tt._head(doc)
    k = next((i for i, ln in enumerate(head) if ln.block_index == b.index), None)
    if k is None:                                           # the block is not in the head of the title module
        head, k = list(b.lines), 0
    r = None
    try:
        r, _ = tt._try_type(doc, head, k)
    except Exception:  # noqa: BLE001  (a helper of the title module that does not expect this block)
        r = None
    if r is not None and not (isinstance(r, tuple) and len(r) == 4 and b.char_start <= r[0] < r[1] <= b.char_end):
        r = None
    if r is None:
        run = tt._run_from(doc, head, k)
        if run is None or not (b.char_start <= run[0] < run[1] <= b.char_end):
            run = (b.char_start, b.char_end)
        reg = tt._Reg(doc, *run)
        r = tt._result(reg, 0, len(reg.t), tt.APERTUS_TIER, b.label, {})
    out = []
    quotes = list(QUOTE_RX.finditer(b.text))
    if len(quotes) == 1 and len(b.text) - len(quotes[0].group(0)) >= 3:
        reg = tt._Reg(doc, b.char_start + quotes[0].start(1), b.char_start + quotes[0].end(1))
        q = tt._result(reg, 0, len(reg.t), tt.APERTUS_TIER, b.label, {"quote_first": True}, cut=False)
        if q is not None:
            out.append({"start": q[0], "end": q[1], "normalised": tt.norm_title(doc.text[q[0]:q[1]]),
                        "options": ["quote_then_block"]})
    if r is not None:
        s, e = r[0], r[1]
        out.append({"start": s, "end": e, "normalised": tt.norm_title(doc.text[s:e]),
                    "options": ["block"] if out else ["block", "quote_then_block"]})
    return out


PATTERN = {"title": _title_values, "affair_number": _number_values, "sponsor": _author_values,
           "submission_date": _date_values}


def ranked_values(field: str, doc: vb.Doc, states: DocStates, heads: Heads, model: int = FINAL,
                  k: int = TOP_K_MAX) -> list[dict]:
    """The k blocks with the highest probability (blocks with text only), each with the values of its pattern."""
    if states.block_ids != [b.block for b in doc.blocks]:
        raise ValueError(f"{doc.doc_id}: the suffix ids are not D1 + the block ids in reading order")
    p = heads.probabilities(field, states, model)
    idx = [i for i in np.argsort(-p, kind="stable") if doc.blocks[i].text][:k]
    out = []
    for rank, i in enumerate(idx, 1):
        b = doc.blocks[i]
        out.append({"rank": rank, "block": b.block, "probability": float(p[i]), "values": PATTERN[field](doc, b)})
    return out


def read_apertus(field: str, doc: vb.Doc, states: DocStates | None, heads: Heads | None = None,
                 model: int = FINAL) -> vb.ValueCandidate | vb.NotFound:
    """The Apertus tier of one field: the head selects the block, the pattern takes the value."""
    heads = heads or default_heads()
    ch = heads.choices.get(field)
    if ch is None:
        raise ValueError(f"{field}: heads.json holds no choice; run the command choose")
    if not doc.text.strip():
        return doc.not_found(field, "no_text")
    if states is None:
        return doc.not_found(field, "no_pattern", "the document has no stored Apertus states")
    ranked = ranked_values(field, doc, states, heads, model, ch["blocks"])
    over = [r for r in ranked if r["probability"] >= ch["threshold"]]
    if not over:
        top = f"{ranked[0]['probability']:.4f}" if ranked else "none"
        return doc.not_found(field, "no_cue", f"head probability of the top block {top} is below {ch['threshold']}")
    for r in over:
        for v in r["values"]:
            if ch["option"] in v["options"]:
                return doc.candidate(field, v["start"], v["end"], v["normalised"], TIER[field],
                                     detail={"head_probability": round(r["probability"], 4), "block_rank": r["rank"],
                                             "layer": heads.layer[field], "pattern": ch["option"]})
    return doc.not_found(field, "no_pattern", f"{len(over)} block(s) above the threshold hold no value of the pattern")


def read_combined(field: str, doc: vb.Doc, states: DocStates | None, heads: Heads | None = None,
                  model: int = FINAL) -> vb.ValueCandidate | vb.NotFound:
    """Rules first. The Apertus tier only for a field of `combined_fields` and only if the rules found nothing."""
    heads = heads or default_heads()
    r = vb.read_field(doc, field, strict=True)
    if r.found or field not in heads.combined_fields:
        return r
    a = read_apertus(field, doc, states, heads, model)
    vb.check_result(doc, field, a)
    return a if a.found else r


def read_title_apertus(doc, states, heads=None, model=FINAL):
    return read_apertus("title", doc, states, heads, model)


def read_affair_number_apertus(doc, states, heads=None, model=FINAL):
    return read_apertus("affair_number", doc, states, heads, model)


def read_sponsor_apertus(doc, states, heads=None, model=FINAL):
    return read_apertus("sponsor", doc, states, heads, model)


def read_submission_date_apertus(doc, states, heads=None, model=FINAL):
    return read_apertus("submission_date", doc, states, heads, model)


def read_title_combined(doc, states, heads=None, model=FINAL):
    return read_combined("title", doc, states, heads, model)


def read_affair_number_combined(doc, states, heads=None, model=FINAL):
    return read_combined("affair_number", doc, states, heads, model)


def read_sponsor_combined(doc, states, heads=None, model=FINAL):
    return read_combined("sponsor", doc, states, heads, model)


def read_submission_date_combined(doc, states, heads=None, model=FINAL):
    return read_combined("submission_date", doc, states, heads, model)


# ------------------------------------------------------------------ command fit

def cmd_fit(a) -> int:
    import resource  # noqa: PLC0415
    import torch  # noqa: PLC0415

    data = Path(a.data)
    rec = json.loads((data / "data_record.json").read_text(encoding="utf-8"))
    for path, digest in rec["inputs_sha256"].items():
        if sha256_file(ROOT / path) != digest:
            raise SystemExit(f"{path}: the file changed after the data step")
    meta = json.loads((data / "docs.json").read_text(encoding="utf-8"))
    part = vb.folds()["documents"]
    if any(part[m["doc_id"]]["part"] != "open" for m in meta):
        raise SystemExit("the data folder holds a document that is not in the open part")
    rows = np.load(data / "rows.npz")
    n_rows = int(rec["rows"])
    row_fold = np.zeros(n_rows, dtype=np.int64)
    for m in meta:
        row_fold[m["row_start"]:m["row_start"] + m["blocks"]] = m["fold"]
    t0 = time.time()
    labels, eligible, counts = {}, {}, {}
    for f in FIELDS:
        mf = MEASURE_ID[f]
        y = rows[f"{mf}__a"] | rows[f"{mf}__b"]
        el = np.zeros(n_rows, dtype=bool)
        docs_a = docs_b_only = docs_neg = 0
        for m in meta:
            sl = slice(m["row_start"], m["row_start"] + m["blocks"])
            if y[sl].any():
                el[sl] = True
                has_a = bool(rows[f"{mf}__a"][sl].any())
                docs_a += has_a
                docs_b_only += not has_a
            elif a.negatives == "reference_documents" and m["has_reference"][mf]:
                el[sl] = True                               # a reference and no positive block: all blocks negative
                docs_neg += 1
        labels[f], eligible[f] = y, el
        counts[f] = {"documents": docs_a + docs_b_only + docs_neg, "documents_with_a_positive_block": docs_a + docs_b_only,
                     "documents_with_a_reference_and_no_positive_block": docs_neg,
                     "documents_with_a_block_of_source_a": docs_a,
                     "documents_with_source_b_only": docs_b_only, "positive_blocks": int(y.sum()),
                     "positive_blocks_source_a": int(rows[f"{mf}__a"].sum()),
                     "positive_blocks_source_b_and_not_a": int((rows[f"{mf}__b"] & ~rows[f"{mf}__a"]).sum()),
                     "blocks": int(el.sum())}
    runs, best = [], {}
    for layer in LAYERS:
        x_all = torch.from_numpy(np.load(data / f"block_L{layer}.npy").astype(np.float32))
        for f in FIELDS:
            el = eligible[f]
            x = x_all[torch.from_numpy(el)]
            y = torch.from_numpy(labels[f][el].astype(np.float32))
            fold = torch.from_numpy(row_fold[el])
            masks = torch.stack([(fold != k).float() for k in range(FOLDS)] + [torch.ones(len(y))], 1)
            n = masks.sum(0)
            s = x.T @ masks
            q = torch.zeros(HIDDEN, FOLDS + 1)
            for i in range(0, x.shape[0], 8192):
                q += (x[i:i + 8192] ** 2).T @ masks[i:i + 8192]
            mu = s / n
            sd = (q / n - mu * mu).clamp_min(0).sqrt() + 1e-4
            pos = (masks * y[:, None]).sum(0)
            yy = y[:, None].expand(-1, FOLDS + 1)
            for lam in LAMBDAS:
                t1 = time.time()
                w = torch.zeros(HIDDEN, FOLDS + 1, requires_grad=True)
                b = torch.log(pos / (n - pos)).clone().requires_grad_(True)
                opt = torch.optim.LBFGS([w, b], lr=1.0, max_iter=MAX_ITER, history_size=10,
                                        line_search_fn="strong_wolfe", tolerance_grad=1e-6, tolerance_change=1e-9)

                def logits():
                    u = w / sd
                    return x @ u - (mu * u).sum(0)[None, :] + b[None, :]

                def closure():
                    opt.zero_grad()
                    z = logits()
                    loss = (torch.nn.functional.binary_cross_entropy_with_logits(z, yy, reduction="none")
                            * masks).sum(0) / n
                    total = loss.sum() + 0.5 * lam * (w * w).sum()
                    total.backward()
                    return total

                opt.step(closure)
                with torch.no_grad():
                    z = logits()
                    oof = z.gather(1, fold[:, None]).squeeze(1)          # the score of the fold head of each row
                    ll = float(torch.nn.functional.binary_cross_entropy_with_logits(oof, y))
                    u = (w / sd).T.contiguous().numpy().astype(np.float32)        # [6, 4096]
                    c = (b - (mu * (w / sd)).sum(0)).numpy().astype(np.float32)
                    zo = oof.numpy()
                # top-1 of the out-of-fold score (information; not used for the selection)
                top1 = docs = 0
                yn, r = labels[f][el], 0
                for m in meta:
                    sl_all = slice(m["row_start"], m["row_start"] + m["blocks"])
                    if not el[sl_all].any():
                        continue
                    k = m["blocks"]
                    if yn[r:r + k].any():
                        top1 += bool(yn[r:r + k][int(np.argmax(zo[r:r + k]))])
                        docs += 1
                    r += k
                run = {"field": f, "layer": layer, "lambda": lam, "out_of_fold_log_loss": round(ll, 6),
                       "out_of_fold_top1": top1, "documents_with_a_positive_block": docs, "seconds": round(time.time() - t1, 1)}
                runs.append(run)
                print(json.dumps(run), flush=True)
                if f not in best or ll < best[f][0]:
                    best[f] = (ll, layer, lam, u, c, run)
            del x
        del x_all
    arrays = {}
    for f in FIELDS:
        _, layer, lam, u, c, _ = best[f]
        arrays[f"{f}__u"], arrays[f"{f}__c"], arrays[f"{f}__layer"] = u, c, np.int64(layer)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(HEADS_NPZ, **arrays)
    write_json(FIT_JSON, {
        "version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "PROPOSED, NOT RELEASED", "part": "open",
        "model": "L2-regularised logistic regression on the block state of one layer; mean and standard deviation "
                 "of each dimension from the training rows of each head; loss = mean log loss + lambda / 2 x |w|^2; "
                 "solver torch.optim.LBFGS (CPU, float32, at most 100 iterations); 5 fold heads and the final head "
                 "in one run",
        "labels": "positive = source a or source b (src/m11_value_heads_data.py); negative = each other block of the "
                  "documents of the fit",
        "documents_of_the_fit": a.negatives,
        "selection": "the lowest out-of-fold log loss of the block label over the grid",
        "grid": {"layers": list(LAYERS), "lambdas": list(LAMBDAS)},
        "label_counts": counts,
        "chosen": {f: best[f][5] for f in FIELDS},
        "runs": runs,
        "heads_npz": {"path": rel(HEADS_NPZ), "sha256": sha256_file(HEADS_NPZ),
                      "keys": "<field>__u float32 [6, 4096] (heads of the folds 0 to 4, then the final head; weights "
                              "on the raw state), <field>__c float32 [6], <field>__layer"},
        "data_folder": {"path": str(data), "data_record_code_sha256": rec["code_sha256"],
                        "inputs_sha256": rec["inputs_sha256"], "documents": rec["documents_used"], "rows": n_rows,
                        "documents_with_no_states_file": rec["documents_with_no_states_file"]},
        "code_sha256": sha256_file(Path(__file__)),
        "seconds": round(time.time() - t0, 1),
        "peak_memory_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1 << 30), 2),
    })
    print(json.dumps({f: best[f][5] for f in FIELDS}, indent=1))
    return 0


# ------------------------------------------------------------------ command candidates (open part, out-of-fold)

def open_ids_checked() -> list[str]:
    ids = vb.dev_ids("open")
    g = guard.assert_allowed(ids, ("dev",))
    if g["refused"] or g["by_split"]["dev"] != len(ids):
        raise SystemExit("the guard refused one or more ids")
    return ids


def cmd_candidates(a) -> int:
    heads = Heads(choices={})
    stored = json.loads(VALUES_OPEN.read_text(encoding="utf-8"))["documents"]
    out, diff, no_states = {}, 0, []
    t0 = time.time()
    for d in open_ids_checked():
        doc = vb.load_doc(d)
        st = load_states(d)
        if st is None:
            no_states.append(d)
        fold = vb.fold_of(d)
        e = {"fold": fold, "fields": {}}
        for f in FIELDS:
            r = vb.read_field(doc, f, strict=True)
            if r.to_json() != stored[d]["fields"][f]:
                diff += 1
            ranked = ranked_values(f, doc, st, heads, fold) if st is not None and doc.text.strip() else []
            e["fields"][f] = {"rule": {"found": r.found, "tier": r.tier if r.found else None,
                                       "block": r.block if r.found else None,
                                       "normalised": r.normalised if r.found else None},
                              "ranked": [{"rank": x["rank"], "block": x["block"],
                                          "probability": round(x["probability"], 6),
                                          "values": [{"normalised": v["normalised"], "options": v["options"]}
                                                     for v in x["values"]]} for x in ranked]}
        out[d] = e
    write_json(Path(a.out), {"version": VERSION, "part": "open", "out_of_fold": True, "documents": out,
                             "rule_records_that_differ_from_values_open": diff,
                             "documents_with_no_states_file": no_states,
                             "heads_npz_sha256": sha256_file(HEADS_NPZ), "seconds": round(time.time() - t0, 1)})
    print(json.dumps({"documents": len(out), "rule_records_that_differ_from_values_open": diff,
                      "documents_with_no_states_file": no_states, "seconds": round(time.time() - t0, 1)}))
    return 0 if diff == 0 else 1


# ------------------------------------------------------------------ command choose

def tier_value(entry: dict, option: str, blocks: int, threshold: float):
    """The value that the tier gives with one setting (the same order as read_apertus), or None."""
    for r in entry["ranked"][:blocks]:
        if r["probability"] < threshold:
            break
        for v in r["values"]:
            if option in v["options"]:
                return v["normalised"]
    return None


def cmd_choose(a) -> int:
    import m11_value_norm as vn  # noqa: PLC0415

    cand = json.loads(Path(a.candidates).read_text(encoding="utf-8"))
    if cand["part"] != "open" or cand["heads_npz_sha256"] != sha256_file(HEADS_NPZ):
        raise SystemExit("the candidates file is not that of the open part and of the stored heads")
    ref = json.loads(REFERENCE_OPEN.read_text(encoding="utf-8"))
    if ref["part"] != "open":
        raise SystemExit("the reference file is not the file of the open part")
    ref = ref["documents"]
    fit = json.loads(FIT_JSON.read_text(encoding="utf-8"))
    curves, fields = {}, {}
    for f in FIELDS:
        mf = MEASURE_ID[f]
        sets = {"rules_found_nothing": [], "all": []}
        for d, e in cand["documents"].items():
            rf = ref[d]["fields"][mf]
            if rf["status"] != "reference":
                continue
            x = e["fields"][f]
            sets["all"].append((x, rf["values"]))
            if not x["rule"]["found"]:
                sets["rules_found_nothing"].append((x, rf["values"]))
        rows = []
        for name, items in sets.items():
            for option in OPTIONS[f]:
                for blocks in (1, 3):
                    for th in THRESHOLDS:
                        eq = df = 0
                        for x, values in items:
                            v = tier_value(x, option, blocks, th)
                            if v is None:
                                continue
                            if vn.compare(mf, v, values)["equal"]:
                                eq += 1
                            else:
                                df += 1
                        rows.append({"set": name, "option": option, "blocks": blocks, "threshold": th,
                                     "documents_with_reference": len(items), "equal": eq, "different": df,
                                     "not_found": len(items) - eq - df,
                                     "coverage": round((eq + df) / len(items), 6) if items else None,
                                     "precision": round(eq / (eq + df), 6) if eq + df else None})
        curves[f] = rows
        ok = [r for r in rows if r["set"] == "rules_found_nothing" and r["equal"] + r["different"] >= MIN_UNITS]
        if ok:
            ok.sort(key=lambda r: (-r["equal"] / (r["equal"] + r["different"]), -r["equal"], r["blocks"],
                                   r["threshold"], OPTIONS[f].index(r["option"])))
            c = ok[0]
            enter = True
        else:                                               # no setting has 30 units: the most units, not combined
            c = max((r for r in rows if r["set"] == "rules_found_nothing"),
                    key=lambda r: (r["equal"] + r["different"], r["equal"]))
            enter = False
        fields[f] = {"measure_field": mf, "tier": TIER[f], "layer": fit["chosen"][f]["layer"],
                     "lambda": fit["chosen"][f]["lambda"], "option": c["option"], "blocks": c["blocks"],
                     "threshold": c["threshold"], "enters_the_combined_reader": bool(enter),
                     "precision_0_8_or_more": 5 * c["equal"] >= 4 * (c["equal"] + c["different"]),
                     "open_out_of_fold_on_rules_found_nothing": {k: c[k] for k in (
                         "documents_with_reference", "equal", "different", "not_found", "coverage", "precision")}}
    combined = [f for f in FIELDS if fields[f]["enters_the_combined_reader"]]
    write_json(CURVE_JSON, {"version": VERSION, "part": "open", "out_of_fold": True, "thresholds": list(THRESHOLDS),
                            "options": {f: list(v) for f, v in OPTIONS.items()}, "curves": curves,
                            "candidates_sha256": sha256_file(Path(a.candidates)),
                            "reference_sha256": sha256_file(REFERENCE_OPEN)})
    write_json(HEADS_JSON, {
        "version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "PROPOSED, NOT RELEASED", "designed_on": "open part only (36 parliaments, 5 folds by parliament)",
        "choice_rule": CHOICE_RULE, "combination": "rules first; the Apertus tier only if the rule reader returns "
                                                   "not found; a rule value is never replaced",
        "fields": fields, "combined_fields": combined,
        "heads_npz_sha256": sha256_file(HEADS_NPZ), "fit_json_sha256": sha256_file(FIT_JSON),
        "curve_json_sha256": sha256_file(CURVE_JSON)})
    print(json.dumps({"fields": fields, "combined_fields": combined}, indent=1))
    return 0


# ------------------------------------------------------------------ command run

OPENING_FILES = ("src/m11_values_type_number.py", "src/m11_values_title.py", "src/m11_values_dates_responder.py",
                 "src/m11_values_sponsor.py", "src/m11_values_base.py", "src/m11_value_norm.py")


def fixed_files() -> dict:
    return {rel(p): sha256_file(p) for p in (Path(__file__), HEADS_NPZ, HEADS_JSON, *(ROOT / f for f in OPENING_FILES))}


def cmd_closed_check(a) -> int:
    """Write the SHA-256 record BEFORE the first value of the closed part is read. It reads no closed document."""
    if CLOSED_CHECK.exists():
        raise SystemExit("closed_check.json exists already: the one check of the closed part was recorded")
    opening = json.loads(OPENING.read_text(encoding="utf-8"))["files"]
    files = fixed_files()
    bad = [f for f in OPENING_FILES if files[f] != opening[f]]
    if bad:
        raise SystemExit(f"files of the opening changed: {bad}")
    write_json(CLOSED_CHECK, {"schema": "parlpdfech-value-heads-closed-check/1", "version": VERSION,
                              "time": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                              "what": "The one check of the Apertus tier on the closed part (addendum H). This "
                                      "record was written before the first closed value was read.",
                              "files": files, "opening_time": json.loads(OPENING.read_text(encoding="utf-8"))["time"]})
    print(json.dumps(files, indent=1))
    return 0


def cmd_run(a) -> int:
    closed = a.part == "closed"
    if closed:
        if not CLOSED_CHECK.is_file():
            raise SystemExit("closed_check.json does not exist: run the command closed-check first")
        if json.loads(CLOSED_CHECK.read_text(encoding="utf-8"))["files"] != fixed_files():
            raise SystemExit("a fixed file changed after closed_check.json was written")
        ids = vb.dev_ids("closed")
        g = guard.assert_allowed(ids, ("dev",))
        if g["refused"] or g["by_split"]["dev"] != len(ids):
            raise SystemExit("the guard refused one or more ids")
    else:
        ids = open_ids_checked()
    heads = Heads()
    if a.fields is not None:                                # a part of the fields of heads.json; no file changes
        want = tuple(f for f in a.fields.split(",") if f)
        if set(want) - set(heads.combined_fields):
            raise SystemExit(f"--fields: not in combined_fields of heads.json: {sorted(set(want) - set(heads.combined_fields))}")
        heads.combined_fields = want
    out = Path(a.out) if a.out else OUT_DIR / f"values_{a.part}_combined.json"
    documents, tiers, no_states, t0 = {}, Counter(), 0, time.time()
    for d in ids:
        doc = vb.load_doc(d, allow_closed=closed)
        st = load_states(d, allow_closed=closed)
        no_states += st is None
        model = FINAL if closed else vb.fold_of(d)           # open part: the head of the 4 other folds
        raw = json.loads((vb.DOCS_DIR / f"{d}.json").read_text(encoding="utf-8"))
        fields = {}
        for f in vb.FIELDS:
            r = read_combined(f, doc, st, heads, model) if f in FIELDS else vb.read_field(doc, f, strict=True)
            fields[f] = r.to_json()
            if r.found and r.tier.startswith("apertus_"):
                tiers[r.tier] += 1
        documents[d] = {"language": raw.get("language"), "s1_role": doc.s1_role, "fields": fields}
    header = {"version": VERSION, "base_version": vb.VERSION, "part": a.part, "documents": len(documents),
              "form": "addendum G version 2, chapter 5.4",
              "mode": "rules first, strict; the Apertus tier for not found (addendum H, PROPOSED)",
              "heads": "the final head" if closed else "out-of-fold: the head of the 4 other folds",
              "combined_fields": list(heads.combined_fields), "choices": heads.choices,
              "files_sha256": fixed_files(), "folds_sha256": sha256_file(vb.FOLDS_FILE)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"header": header, "documents": documents}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    msg = {"part": a.part, "documents": len(documents), "documents_with_no_states_file": int(no_states),
           "seconds": round(time.time() - t0, 1), "out": rel(out)}
    if not closed:                                          # no count of a closed value is printed here
        msg["values_of_the_apertus_tiers"] = dict(tiers)
    print(json.dumps(msg))
    return 0


# ------------------------------------------------------------------ command compare

def cmd_compare(a) -> int:
    base = json.loads(Path(a.rules).read_text(encoding="utf-8"))
    comb = json.loads(Path(a.combined).read_text(encoding="utf-8"))
    if base["part"] != comb["part"]:
        raise SystemExit("the two measures files are not of the same part")

    def cell(m: dict, field: str) -> dict:
        c = next(x for x in m["cells"] if x["field"] == field and x["base"] == "primary" and x["dimension"] == "none")
        k = c["counts"]
        e, d, n = k["equal"], k["different"], k["n_ref"]
        return {"documents": k["documents"], "n_ref": n, "equal": e, "different": d, "not_found": k["not_found"],
                "coverage": round((e + d) / n, 6) if n else None, "precision": round(e / (e + d), 6) if e + d else None,
                "recall": round(e / n, 6) if n else None}

    rows = []
    for field in ("affair_type", "title", "affair_number", "submission_date", "response_date", "responder_name",
                  "first_author"):
        r, c = cell(base, field), cell(comb, field)
        ap = [p for p in comb["pairs"] if p["field"] == field and p["tier"].startswith("apertus_")]
        rows.append({"field": field, "rules": r, "combined": c, "gain_equal_documents": c["equal"] - r["equal"],
                     "more_different_documents": c["different"] - r["different"],
                     "apertus_tiers": [{"tier": p["tier"], **p["counts"], "precision": p["precision"]} for p in ap]})
    out = {"version": VERSION, "part": base["part"], "rules_measures": {"path": rel(Path(a.rules)), "sha256": sha256_file(Path(a.rules))},
           "combined_measures": {"path": rel(Path(a.combined)), "sha256": sha256_file(Path(a.combined))},
           "cell": "base primary, dimension none", "fields": rows}
    write_json(Path(a.out), out)
    print(json.dumps(rows, indent=1))
    return 0


def set_dir(d: str | None) -> None:
    """Another folder for heads.npz, heads.json, fit.json and curve_open.json (design variants in a scratch folder)."""
    global OUT_DIR, HEADS_NPZ, HEADS_JSON, FIT_JSON, CURVE_JSON
    if d:
        OUT_DIR = Path(d)
        HEADS_NPZ, HEADS_JSON, FIT_JSON, CURVE_JSON = (OUT_DIR / n for n in (
            "heads.npz", "heads.json", "fit.json", "curve_open.json"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="folder of the head files (default daten/gj_values/heads)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fit")
    p.add_argument("--data", required=True)
    p.add_argument("--negatives", choices=("positive_documents", "reference_documents"), default=NEGATIVES)
    p = sub.add_parser("candidates")
    p.add_argument("--out", required=True)
    p = sub.add_parser("choose")
    p.add_argument("--candidates", required=True)
    p = sub.add_parser("run")
    p.add_argument("--part", choices=("open", "closed"), required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--fields", default=None, help="registry ids with a comma; default: combined_fields of heads.json")
    p = sub.add_parser("compare")
    p.add_argument("--rules", required=True)
    p.add_argument("--combined", required=True)
    p.add_argument("--out", required=True)
    sub.add_parser("closed-check")
    a = ap.parse_args()
    set_dir(a.dir)
    return {"fit": cmd_fit, "candidates": cmd_candidates, "choose": cmd_choose, "run": cmd_run,
            "compare": cmd_compare, "closed-check": cmd_closed_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

"""Probe of the value heads, step 1: weak block labels and the stacked Apertus states of the OPEN part.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: PROBE, NOT RELEASED. No human checked this file. This file changes no existing file.

1 Scope
  Only the 1,486 development documents of the 36 open parliaments (daten/gj_values/folds.json, part open).
  Each id passes src/m10_guard.py for the split dev BEFORE a block file, a rule file or a states file is opened.
  The file reads: folds.json, reference_open.json, values_open.json, measures_open.json (key pairs), the block
  file and the rule file of each document (m11_values_base.load_doc), the conversion record
  daten/gj/fullrun_b1s_dev/runs/run_1.json (the path of the states file of each document) and the states files.
  It reads no file of the closed part, no validation, group-7 or test file.

2 Row order
  One row for each block of each document, documents in number order, blocks in reading order. The suffix id
  "D1" of a states file is the document state. The suffix id "B<n>" is the state of the block "B<n>". The file
  stops if the suffix ids of a states file are not "D1" + the block ids of the block file in reading order.

3 Label kinds (a block is positive if it holds the value)
  a        the block holds the reference value after the normalisation of src/m11_value_norm.py:
           affair_number   the run list of a reference value is a part with no gap of norm_number(block text)
           title           the fold form of a reference value is in fold(block text) at token limits, or
                           title_compare(block text) is equal, or title_compare(one line of the block) is equal
           first_author    the token list of a reference value is a part with no gap of token_list(block text)
           dates           a date of find_dates(block text) is a day of the reference set
  a_near   dates only: the block prints a day 1 to 7 days BEFORE a reference day (and it is not positive by a)
  b        the block of the reader value, if the tier of the value has a measured precision of 0.9 or more on the
           open part (measures_open.json, key pairs)
  reader   the block of the reader value of each tier (the block that the rule reader used)
  shape    the block holds a token of the right shape (the baseline with no model):
           dates: find_dates gives a hit; affair_number: a token with 2 or more digits outside each date span;
           first_author: two capitalised words side by side; title: Docling label section_header or title
  affair_type is a value of the document: reference list values, reader value, reader tier.

4 Outputs (scratch folder; states are float16)
  rows.npz            doc index and block index of each row, the label kinds as bool arrays
  docs.json           for each document: id, parliament, fold, language, S1 role, blocks, reader records
  block_L<k>.npy      float16 [rows, 4096], one file for each layer k
  doc_states.npy      float16 [documents, layers, 4096]
  data_record.json    counts, times, sizes, SHA-256 of the inputs

Usage:
  uv run --offline --frozen --no-sync python src/m11_value_heads_data.py --out SCRATCH_DIR
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402
import m11_value_norm as vn  # noqa: E402
import m11_values_base as vb  # noqa: E402

VERSION = "m11-value-heads-data-1"
ROOT = vb.ROOT
REFERENCE = ROOT / "daten/gj_values/reference_open.json"
VALUES = ROOT / "daten/gj_values/values_open.json"
MEASURES = ROOT / "daten/gj_values/measures_open.json"
RUN = ROOT / "daten/gj/fullrun_b1s_dev/runs/run_1.json"
BLOCK_FIELDS = ("affair_number", "title", "submission_date", "response_date", "first_author")
READER_ID = {"affair_number": "affair_number", "title": "title", "submission_date": "submission_date",
             "response_date": "response_date", "first_author": "sponsor", "affair_type": "affair_type"}
PRECISION_MIN = 0.9
NEAR_DAYS = 7
HIDDEN = 4096
RX_NUMBER_TOKEN = re.compile(r"\S*\d\S*\d\S*")
RX_NAME_PAIR = re.compile(r"(?<![^\W\d_])[A-ZÀ-ÖØ-Ý][a-zß-öø-ÿ]+(?:-[A-ZÀ-ÖØ-Ý][a-zß-öø-ÿ]+)? "
                          r"[A-ZÀ-ÖØ-Ý][a-zß-öø-ÿ]+(?![^\W\d_])")
TITLE_LABELS = ("section_header", "title")
SHAPE_RULE = {
    "submission_date": "m11_values_base.find_dates(block text) gives one or more dates",
    "response_date": "m11_values_base.find_dates(block text) gives one or more dates",
    "affair_number": "a token (no space) with 2 or more digits, after each date span was replaced by spaces",
    "first_author": "two capitalised words side by side (regular expression RX_NAME_PAIR)",
    "title": "Docling label section_header or title (no token shape exists for a title)",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def has_part(short: list[str], long_text: str) -> bool:
    return bool(short) and (" " + " ".join(short) + " ") in long_text


def block_labels(block, refs: dict) -> dict:
    """The label kinds a, a_near and shape of one block. refs: field -> list of normal forms (may be empty)."""
    t = block.text or ""
    out = {}
    dates = vb.find_dates(t) if t else []
    days = {h.iso for h in dates}
    for f in ("submission_date", "response_date"):
        ref_days = [d for d in refs[f] if d]
        out[f, "a"] = bool(days & set(ref_days))
        near = False
        if not out[f, "a"]:
            for r in ref_days:
                rd = dt.date.fromisoformat(r)
                if any(1 <= (rd - dt.date.fromisoformat(d)).days <= NEAR_DAYS for d in days):
                    near = True
        out[f, "a_near"] = near
        out[f, "shape"] = bool(dates)
    runs = " " + " ".join(vn.norm_number(t) or []) + " "
    out["affair_number", "a"] = any(has_part(list(r), runs) for r in refs["affair_number"])
    masked = list(t)
    for h in dates:
        for i in range(h.start, h.end):
            masked[i] = " "
    out["affair_number", "shape"] = bool(RX_NUMBER_TOKEN.search("".join(masked)))
    toks = " " + vn.fold(t) + " "
    out["first_author", "a"] = any(has_part(list(r), toks) for r in refs["first_author"])
    out["first_author", "shape"] = bool(RX_NAME_PAIR.search(t))
    pos = False
    if refs["title"] and t:
        if any((" " + r + " ") in toks for r in refs["title"]) or vn.title_compare(t, refs["title"])["equal"]:
            pos = True
        elif any(vn.title_compare(ln.text, refs["title"])["equal"] for ln in block.lines):
            pos = True
    out["title", "a"] = pos
    out["title", "shape"] = block.label in TITLE_LABELS
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="first N documents only (smoke)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ids = vb.dev_ids("open")
    g = guard.assert_allowed(ids, ("dev",))
    if g["refused"] or g["by_split"]["dev"] != len(ids):
        raise SystemExit("the guard refused one or more ids")
    if a.limit:
        ids = ids[:a.limit]
    folds = vb.folds()["documents"]
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    if ref["part"] != "open":
        raise SystemExit("the reference file is not the file of the open part")
    ref = ref["documents"]
    val = json.loads(VALUES.read_text(encoding="utf-8"))
    if val["header"]["part"] != "open":
        raise SystemExit("the values file is not the file of the open part")
    val = val["documents"]
    pairs = json.loads(MEASURES.read_text(encoding="utf-8"))["pairs"]
    tier_precision = {(p["field"], p["tier"]): (p["precision"], p["counts"]["units"]) for p in pairs}
    run = json.loads(RUN.read_text(encoding="utf-8"))["results"]

    docs, no_states = [], []
    n_rows = 0
    for d in ids:
        st = (run.get(d) or {}).get("states")
        if not st or not st.get("file") or not (ROOT / st["file"]).is_file():
            no_states.append(d)
            continue
        doc = vb.load_doc(d)
        docs.append((d, doc, ROOT / st["file"]))
        n_rows += len(doc.blocks)
    t_docs = time.time() - t0

    # layers of the first states file
    with np.load(docs[0][2], allow_pickle=False) as z:
        layers = [int(k) for k in z["layers"]]
    mm = {k: np.lib.format.open_memmap(out / f"block_L{k}.npy", mode="w+", dtype=np.float16, shape=(n_rows, HIDDEN))
          for k in layers}
    doc_states = np.zeros((len(docs), len(layers), HIDDEN), dtype=np.float16)
    kinds = [(f, k) for f in BLOCK_FIELDS for k in ("a", "shape", "reader", "b")]
    kinds += [(f, "a_near") for f in ("submission_date", "response_date")]
    lab = {fk: np.zeros(n_rows, dtype=bool) for fk in kinds}
    row_doc = np.zeros(n_rows, dtype=np.int32)
    row_block = np.zeros(n_rows, dtype=np.int32)
    row_has_text = np.zeros(n_rows, dtype=bool)
    meta = []
    row = 0
    t_load = t_label = 0.0
    bytes_states = 0
    for i, (d, doc, sp) in enumerate(docs):
        t1 = time.time()
        with np.load(sp, allow_pickle=False) as z:
            if str(z["doc_id"]) != d:
                raise SystemExit(f"{d}: the states file has another doc id")
            sids = [str(s) for s in z["suffix_ids"]]
            if sids != ["D1"] + [b.block for b in doc.blocks]:
                raise SystemExit(f"{d}: the suffix ids are not D1 + the block ids in reading order")
            if [int(k) for k in z["layers"]] != layers:
                raise SystemExit(f"{d}: other layers")
            s = z["states"]
            if s.dtype != np.float16 or s.shape != (len(sids), len(layers), HIDDEN):
                raise SystemExit(f"{d}: other form of the states")
        bytes_states += sp.stat().st_size
        n = len(doc.blocks)
        doc_states[i] = s[0]
        for j, k in enumerate(layers):
            mm[k][row:row + n] = s[1:, j, :]
        t_load += time.time() - t1
        t1 = time.time()
        rf = ref[d]["fields"]
        refs = {f: (rf[f]["values"] if rf[f]["status"] == "reference" else []) for f in BLOCK_FIELDS}
        vf = val[d]["fields"]
        index = {b.block: b.index for b in doc.blocks}
        readers = {}
        for f in (*BLOCK_FIELDS, "affair_type"):
            x = vf[READER_ID[f]]
            if x.get("found"):
                p = tier_precision.get((f, x["tier"]), (None, 0))[0]
                readers[f] = {"block": x["block"], "tier": x["tier"], "normalised": x["normalised"],
                              "tier_precision": p, "b": p is not None and p >= PRECISION_MIN}
                if f != "affair_type":
                    r = row + index[x["block"]]
                    lab[f, "reader"][r] = True
                    lab[f, "b"][r] = readers[f]["b"]
            else:
                readers[f] = None
        for b in doc.blocks:
            r = row + b.index
            row_doc[r], row_block[r], row_has_text[r] = i, b.index, bool(b.text)
            for fk, v in block_labels(b, refs).items():
                lab[fk][r] = v
        e = folds[d]
        meta.append({"doc_id": d, "parliament": e["parliament"], "fold": e["fold"], "language": doc.language,
                     "s1_role": doc.s1_role, "blocks": n, "row_start": row, "readers": readers,
                     "has_reference": {f: rf[f]["status"] == "reference" for f in (*BLOCK_FIELDS, "affair_type")},
                     "primary_set": {f: bool(rf[f].get("primary_set")) for f in (*BLOCK_FIELDS, "affair_type")},
                     "affair_type_reference": rf["affair_type"]["values"] if rf["affair_type"]["status"] == "reference" else [],
                     "affair_number_short_digits_only": bool(rf["affair_number"].get("short_digits_only"))})
        row += n
        t_label += time.time() - t1
    for m in mm.values():
        m.flush()
    np.save(out / "doc_states.npy", doc_states)
    np.savez(out / "rows.npz", row_doc=row_doc, row_block=row_block, row_has_text=row_has_text,
             **{f"{f}__{k}": v for (f, k), v in lab.items()})
    (out / "docs.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    rec = {
        "version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "guard": {"items": g["items"], "by_split": g["by_split"], "refused": g["refused"]},
        "open_documents": len(vb.dev_ids("open")), "documents_used": len(docs),
        "documents_with_no_states_file": no_states, "rows": int(n_rows), "layers": layers, "hidden": HIDDEN,
        "states_dtype_on_disk": "float16",
        "states_files": {"count": len(docs), "bytes": bytes_states,
                         "by_job": {j: sum(1 for _, _, p in docs if j in str(p)) for j in ("gpu1_labelled", "gpu2_bulk")}},
        "bytes_of_one_layer": {"float16": int(n_rows) * HIDDEN * 2, "float32": int(n_rows) * HIDDEN * 4},
        "bytes_of_the_document_states_of_one_layer_float16": len(docs) * HIDDEN * 2,
        "seconds": {"guard_and_block_files": round(t_docs, 2), "read_states_files_all_layers": round(t_load, 2),
                    "labels": round(t_label, 2), "total": round(time.time() - t0, 2)},
        "shape_rule": SHAPE_RULE, "precision_min_of_label_source_b": PRECISION_MIN,
        "tiers_of_label_source_b": {f: sorted(t for (ff, t), (p, n) in tier_precision.items()
                                              if ff == f and p is not None and p >= PRECISION_MIN)
                                    for f in (*BLOCK_FIELDS, "affair_type")},
        "inputs_sha256": {guard.rel(p): sha256_file(p) for p in (REFERENCE, VALUES, MEASURES, RUN, vb.FOLDS_FILE)},
        "code_sha256": sha256_file(Path(__file__)),
    }
    (out / "data_record.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("documents_used", "documents_with_no_states_file", "rows", "layers",
                                          "seconds", "bytes_of_one_layer")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

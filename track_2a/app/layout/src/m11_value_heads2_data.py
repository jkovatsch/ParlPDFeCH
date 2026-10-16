"""Heads on the questions `Q0`, `Q1` and `Q2`, step 1: the state tables and the label tables of addendum I.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: PROPOSED, NOT RELEASED. No human checked this file. This file changes no existing file.
Rules: `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md` (chapters 2, 3 and 10.2).

1 Task
  The tool reads a job folder and a states folder of the template `gj_values_v1_de`. It writes the tables that
  the fit tool `src/m11_value_heads2.py` reads. It fits nothing and it calculates no outcome of a value.

2 Inputs
  job folder      `items.jsonl` (one line for each document: `doc_id` and the suffix ids) and `manifest.json`.
                  The job tool deletes `items.jsonl` after the fetch. Then the key `by_doc` of `build.json` is used.
                  It holds the count and the SHA-256 of the suffix ids of each document.
  states folder   one file `<doc>.npz` for each document (form of `src/m10_vm_states.py`).
  block files     `m11_values_base.load_doc` gives the block text, the page and the block id of each block.
  reference       `daten/gj_values/round4/reference_dev_all.json` (rule I1, item 14).
  folds           `daten/gj_values/folds_all.json` (5 folds by parliament).
  `Q0` labels     the key `d1` of `daten/gj/labels/<doc>.json`, for the ids of the key `dev` of `daten/gj/sets.json`.

3 Checks (the tool stops at the first difference)
  Each id passes `src/m10_guard.py` for the split `dev` before a file of the document is opened.
  The suffix ids of a document must be `Q0`, `Q1` and then `Q2.B<n>` for each block in reading order.
  This holds for `items.jsonl`, for the states file and for the block file of the document.
  The key `states` must have the form [suffixes, 7, 4096] in float16 with the layers 8 to 32.
  The template SHA-256 of a states file must be that of the manifest and that of addendum I.

4 Row order
  One `Q2` row for each block of each document with a states file. Documents are in number order.
  Blocks are in reading order. One `Q0` row and one `Q1` row for each document with a states file.

5 Outputs (folder `--out`)
  `q0_L<k>.npy`, `q1_L<k>.npy`   float16 [documents with states, 4096], one file for each layer k
  `q2_L<k>.npy`                  float16 [rows, 4096], one file for each layer k (written as a memory map)
  `rows.npz`                     `row_doc`, `row_block`, `row_has_text` and one label array for each `Q2` field
  `docs.json`                    one entry for each document of the job (also for a document with no states file)
  `data_record.json`             counts, label tables, times and the SHA-256 of each input
                                 The key `rule_files` names the folder of the rule files of the loader.
                                 The fit tool stops if the reference, the folds file or this folder changed.

6 Sealed paths (addendum I, chapter 10.2)
  The function `refuse_sealed` stops a call that names a sealed path. The flag `--last-run` opens these paths.
  The flag needs the fix record. Each call with the flag adds one entry to the access record.
  This tool reads development documents only. Thus it has the check, but the flag opens no document for it.
  The comparison of a path is in folded case: the file system of the Mac does not separate letter cases.
  The function `refuse_test_paths` refuses a path of a test document in each mode (process rule 6).

7 Complete states folder
  The file `skips.jsonl` beside the states folder lists each document that the job did not read.
  The tool stops if the documents with no states file are not exactly the documents of that list.
  The options `--limit` and `--part` permit a part. Then the key `complete` of `data_record.json` is false.
  The command `fit-oof` of the fit tool stops on a data folder that is not complete.

8 Layers
  The tool writes layer 20 only, if `--layers` is not given (addendum I, rule I3, item 2).
  One layer of the full job needs about 0.8 GB on the disk.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_value_heads2_data.py --states daten/gj/states/values_dev/states
      --job daten/gj/jobs/values_dev --out daten/gj_values/heads2
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402
import m11_value_heads_data as vhd  # noqa: E402  (the function block_labels; addendum I, chapter 3.2, item 6)
import m11_value_norm as vn  # noqa: E402
import m11_values_base as vb  # noqa: E402

VERSION = "m11-value-heads2-data-1"
ACTOR = "workflow sub-agent (Claude Opus 5.5); no human checked this file"
STATUS = "PROPOSED, NOT RELEASED"
ROOT = vb.ROOT
ADDENDUM = ROOT / "crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md"
TEMPLATE_ID = "gj_values_v1_de"
TEMPLATE_SHA256 = "54abf49ab788b2779b7bd00d8ebfb99abb3daf0fbe076e274fec30851dca81f6"     # rule I1, item 1
REFERENCE = ROOT / "daten/gj_values/round4/reference_dev_all.json"
FOLDS_ALL = ROOT / "daten/gj_values/folds_all.json"
SETS = ROOT / "daten/gj/sets.json"
LABELS_DIR = ROOT / "daten/gj/labels"
OUT_DEFAULT = ROOT / "daten/gj_values/heads2"
LAYERS = (8, 12, 16, 20, 24, 28, 32)
LAYER_DEFAULT = "20"                              # rule I3, item 2: no other layer is fitted before the last run
HIDDEN = 4096
FOLDS = 5
# the 6 fields of `Q2` (registry ids, rule I2, chapter 3.2, item 2) and their ids in the reference file
Q2_FIELDS = ("affair_number", "title", "submission_date", "sponsor", "response_date", "responder")
MEASURE_ID = {"affair_number": "affair_number", "title": "title", "submission_date": "submission_date",
              "sponsor": "first_author", "response_date": "response_date", "responder": "responder_name",
              "affair_type": "affair_type"}
PRIMARY_ONLY_FIT = ("responder",)                 # chapter 3.2, item 18
# the 7 classes of `Q1` (chapter 3.1, items 3 to 5): each list value with 10 or more documents, and `none`
Q1_CLASSES = ("interpellation", "request", "draft_decree", "motion", "postulate", "parliamentary_initiative", "none")
Q1_MIN_DOCUMENTS = 10
Q0_CLASSES = ("A", "B", "C", "D")
# sealed until the one last run (chapter 10.2, item 4); patterns on the path from the project folder
SEALED = ("daten/gj/jobs/values_last", "daten/gj/states/values_last", "daten/gj/validation*",
          "daten/gj/decisions_validation*")
# process rule 6: the folders of the test documents; refused in each mode
RULE6 = ("daten/gold", "daten/score26", "daten/gj/sealed", "daten/pdf/test_dokumente")
FIX_RECORD = OUT_DEFAULT / "last_run_fix.json"
ACCESS_RECORD = OUT_DEFAULT / "last_run_access.json"


class Sealed(SystemExit):
    """A call named a sealed path with no permit."""


class OtherSuffixIds(ValueError):
    """The suffix ids of a states file are not those of rule I1, item 6, or not those of the block file."""


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path | str) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(p: Path, obj, indent: int | None = 1) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    tmp.replace(p)


# ------------------------------------------------------------------ sealed paths (chapter 10.2)

def _parts_below_root(p: Path | str) -> list[tuple[str, ...]]:
    """The parts of the path below the project folder, in folded case: for the path as given and for the path
    after each link is followed. The file system of the Mac does not separate letter cases."""
    root = [x.casefold() for x in ROOT.parts]
    out = []
    for q in {Path(p).absolute(), Path(p).resolve()}:
        parts = [x.casefold() for x in q.parts]
        if parts[:len(root)] == root:
            out.append(tuple(parts[len(root):]))
    return out


def is_sealed(p: Path | str) -> bool:
    """True if the path, or the path after each link is followed, is a sealed path or is below one."""
    for parts in _parts_below_root(p):
        for n in range(1, len(parts) + 1):
            head = "/".join(parts[:n])
            if any(fnmatch.fnmatchcase(head, pat.casefold()) for pat in SEALED):
                return True
    return False


def is_test_path(p: Path | str) -> bool:
    """True if the path is a folder of the test documents or is below one (process rule 6)."""
    for parts in _parts_below_root(p):
        r = "/".join(parts)
        if any(r == x or r.startswith(x + "/") for x in RULE6):
            return True
    return False


def refuse_test_paths(paths) -> None:
    """Stop if a path is a path of a test document. This check has no flag: it applies in each mode.
    A path in the project folder also goes through `check_path` of `src/m10_guard.py`."""
    for p in paths:
        if p is None:
            continue
        if is_test_path(p):
            raise Sealed(f"path {p}: a path of a test document is always refused (process rule 6)")
        if _parts_below_root(p):
            try:
                guard.check_path(Path(p))
            except guard.GuardRefusal as e:
                raise Sealed(str(e)) from None


def check_fix_record(fix: Path | None = None) -> dict:
    """Compare each file of the fix record with its SHA-256 (chapter 10.2, item 3). A difference stops the tool."""
    fix = fix or FIX_RECORD
    if not fix.is_file():
        raise Sealed(f"the flag --last-run needs the fix record {rel(fix)} (addendum I, chapter 10.2, item 5)")
    rec = json.loads(fix.read_text(encoding="utf-8"))
    bad = []
    for path, digest in rec["files"].items():
        q = ROOT / path
        if not q.is_file() or sha256_file(q) != digest:
            bad.append(path)
    if bad:
        raise Sealed(f"files differ from the fix record: {bad}")
    return rec


def refuse_sealed(paths, last_run: bool, tool: str, fix: Path | None = None, access: Path | None = None) -> dict | None:
    """Stop if a path is sealed and the flag is not given. With the flag: examine the fix record and add one entry
    to the access record (time, tool, command, SHA-256 of the fix record). Returns the entry, or None."""
    fix, access = fix or FIX_RECORD, access or ACCESS_RECORD
    refuse_test_paths(paths)
    sealed = [str(p) for p in paths if p is not None and is_sealed(p)]
    if not last_run:
        if sealed:
            raise Sealed(f"sealed until the one last run: {sealed}. The flag --last-run opens these paths "
                         "(addendum I, chapter 10.2).")
        return None
    check_fix_record(fix)
    entry = {"time": now(), "tool": tool, "command": list(sys.argv), "sealed_paths_named": sealed,
             "fix_record_sha256": sha256_file(fix)}
    log = json.loads(access.read_text(encoding="utf-8")) if access.is_file() else {
        "schema": "parlpdfech-heads2-last-run-access/1", "rule": "addendum I, chapter 10.2, item 6", "entries": []}
    log["entries"].append(entry)
    write_json(access, log)
    return entry


# ------------------------------------------------------------------ states files and job folder

class States:
    """The states of one document: `Q0`, `Q1` and one `Q2` state for each block (float16, 7 layers)."""

    def __init__(self, doc_id: str, suffix_ids, layers, states, template_sha256: str | None = None):
        self.doc_id = str(doc_id)
        self.suffix_ids = [str(s) for s in suffix_ids]
        self.layers = [int(k) for k in layers]
        self.states = states
        self.template_sha256 = template_sha256
        if self.suffix_ids[:2] != ["Q0", "Q1"] or any(not s.startswith("Q2.B") for s in self.suffix_ids[2:]):
            raise OtherSuffixIds(f"{self.doc_id}: the suffix ids are not Q0, Q1 and then Q2.B<n> (rule I1, item 6)")
        if self.layers != list(LAYERS):
            raise ValueError(f"{self.doc_id}: the layers are {self.layers}, not {list(LAYERS)}")
        if states.dtype != np.float16 or states.shape != (len(self.suffix_ids), len(LAYERS), HIDDEN):
            raise ValueError(f"{self.doc_id}: the states do not have the form [suffixes, 7, 4096] in float16")

    @property
    def block_ids(self) -> list[str]:
        return [s[3:] for s in self.suffix_ids[2:]]

    def q0(self, layer: int) -> np.ndarray:
        return self.states[0, self.layers.index(int(layer)), :]

    def q1(self, layer: int) -> np.ndarray:
        return self.states[1, self.layers.index(int(layer)), :]

    def q2(self, layer: int) -> np.ndarray:
        return self.states[2:, self.layers.index(int(layer)), :]


def read_states(path: Path | str, doc_id: str | None = None, template_sha256: str | None = TEMPLATE_SHA256) -> States:
    """Read one states file. The call does not examine the path: the caller applies the guard and `refuse_sealed`."""
    with np.load(Path(path), allow_pickle=False) as z:
        d = str(z["doc_id"])
        tsha = str(z["template_sha256"]) if "template_sha256" in z.files else None
        st = States(d, z["suffix_ids"], z["layers"], z["states"], tsha)
    if doc_id is not None and d != str(doc_id):
        raise ValueError(f"{doc_id}: the states file has the doc id {d}")
    if template_sha256 is not None and tsha != template_sha256:
        raise ValueError(f"{d}: the states file has another template SHA-256")
    return st


def expected_suffix_ids(doc: vb.Doc) -> list[str]:
    return ["Q0", "Q1"] + [f"Q2.{b.block}" for b in doc.blocks]


def sha256_json(x) -> str:
    """The same definition as `m10_prompts.sha256_json` (the job tool uses it for the suffix ids)."""
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_job(job: Path) -> tuple[dict, dict]:
    """({doc id: {"n_suffix", "suffix_ids_sha256"}}, manifest) of a job folder. The source is `items.jsonl`.
    The job tool deletes that file after the fetch. Then the source is the key `by_doc` of `build.json`.
    The text of an item is not kept."""
    manifest = json.loads((job / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("template_id") != TEMPLATE_ID or manifest.get("template_sha256") != TEMPLATE_SHA256:
        raise SystemExit(f"{rel(job)}: the manifest does not have the template of addendum I (rule I1, item 1)")
    items = {}
    if (job / "items.jsonl").is_file():
        with open(job / "items.jsonl", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                it = json.loads(line)
                d = str(it["doc_id"])
                if d in items:
                    raise SystemExit(f"{d}: two items in the job folder")
                sids = [str(s["id"]) for s in it["suffixes"]]
                items[d] = {"n_suffix": len(sids), "suffix_ids_sha256": sha256_json(sids)}
        manifest["_job_source"] = "items.jsonl"
    else:
        rec = json.loads((job / "build.json").read_text(encoding="utf-8"))
        if rec.get("template_sha256") != TEMPLATE_SHA256 or sorted(rec["by_doc"]) != sorted(str(d) for d in rec["doc_ids"]):
            raise SystemExit(f"{rel(job)}: build.json does not have the template of addendum I or one row for each document")
        items = {str(d): {"n_suffix": int(v["n_suffix"]), "suffix_ids_sha256": v["suffix_ids_sha256"]}
                 for d, v in rec["by_doc"].items()}
        manifest["_job_source"] = "build.json (key by_doc; items.jsonl is deleted after the fetch)"
    return items, manifest


def job_agrees(item: dict, suffix_ids: list[str]) -> bool:
    return item["n_suffix"] == len(suffix_ids) and item["suffix_ids_sha256"] == sha256_json(suffix_ids)


def dev_guard(ids) -> dict:
    """Each id must be a development document for the guard (rule I1, item 17). No document file is opened here."""
    ids = [str(i) for i in ids]
    g = guard.assert_allowed(ids, ("dev",))
    if g["refused"] or g["by_split"]["dev"] != len(ids):
        raise SystemExit(f"the guard refused one or more ids: {g['refused']} refused of {len(ids)}")
    return {"items": g["items"], "by_split": g["by_split"], "refused": g["refused"]}


# ------------------------------------------------------------------ labels (rule I2)

def reference_forms(entry: dict) -> list:
    """The normal forms of one reference entry. An empty list = no reference (addendum G, chapter 4.9)."""
    if entry.get("status") != "reference":
        return []
    return [v for v in entry.get("values") or [] if v not in (None, "", [])]


def responder_label(text: str, keys) -> bool:
    """Chapter 3.2, items 13 to 15: one pattern of a key of the reference set matches in `fold(block text)`."""
    keys = set(keys)
    if not text or not keys:
        return False
    f = vn.fold(text)
    return any(rx.search(f) is not None for key, _pat, rx in vn._BODY_RX if key in keys)


def q2_labels(block: vb.Block, refs: dict) -> dict:
    """{registry id: bool} for the 6 fields of `Q2`. refs: {registry id: normal forms of the reference}.
    A block with no text has no positive label. Only the reference is used (chapter 3.2, item 4)."""
    if not block.text:
        return {f: False for f in Q2_FIELDS}
    five = {MEASURE_ID[f]: refs[f] for f in Q2_FIELDS if f != "responder"}
    got = vhd.block_labels(block, five)
    out = {f: bool(got[MEASURE_ID[f], "a"]) for f in Q2_FIELDS if f != "responder"}
    out["responder"] = responder_label(block.text, refs["responder"])
    return out


def q1_classes_of(reference: dict) -> tuple[tuple[str, ...], dict]:
    """The classes of the `Q1` head from the counts of the reference (chapter 3.1, item 3), and the counts."""
    counts = Counter()
    for e in reference.values():
        forms = reference_forms(e["fields"]["affair_type"])
        counts[forms[0] if forms else "none"] += 1
    classes = tuple(c for c in Q1_CLASSES if c != "none" and counts[c] >= Q1_MIN_DOCUMENTS)
    more = sorted(c for c, n in counts.items() if c not in Q1_CLASSES and n >= Q1_MIN_DOCUMENTS)
    return classes + tuple(more) + ("none",), dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def q1_target(entry: dict) -> tuple[str | None, str | None]:
    """(class of the fit or None, reference value or None). A value that is not a class gives no class."""
    forms = reference_forms(entry["fields"]["affair_type"])
    if not forms:
        return "none", None
    v = forms[0]
    return (v if v in Q1_CLASSES else None), v


def q0_labels(ids) -> dict:
    """{doc id: `A`, `B`, `C` or `D`} for the ids that are in the key `dev` of `daten/gj/sets.json` (chapter 3.3).
    The caller applied the guard to each id."""
    labelled = set(json.loads(SETS.read_text(encoding="utf-8"))["dev"])
    out = {}
    for d in ids:
        if d not in labelled:
            continue
        lab = json.loads((LABELS_DIR / f"{d}.json").read_text(encoding="utf-8"))
        if str(lab.get("doc_id")) != d or lab.get("d1") not in Q0_CLASSES:
            raise SystemExit(f"{d}: the label file has another doc id or no key d1 of {Q0_CLASSES}")
        out[d] = lab["d1"]
    return out


# ------------------------------------------------------------------ main

def read_skips(states_dir: Path) -> tuple[list[str] | None, Path]:
    """The doc ids of the file `skips.jsonl` beside the states folder (None: the file does not exist)."""
    p = states_dir.parent / "skips.jsonl"
    if not p.is_file():
        return None, p
    ids = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                ids.append(str(json.loads(line)["doc_id"]))
    return ids, p


def complete_check(no_states: list[str], skips: list[str] | None) -> tuple[bool, str]:
    """(complete, text). Complete: the documents with no states file are exactly the documents of `skips.jsonl`.
    With no file `skips.jsonl` each document must have a states file."""
    want = set(skips or [])
    if set(no_states) == want:
        return True, "each document of the job has a states file or a row in skips.jsonl"
    return False, (f"{len(set(no_states) - want)} documents have no states file and no row in skips.jsonl; "
                   f"{len(want - set(no_states))} documents of skips.jsonl have a states file or are not in the job")


def build(states_dir: Path, job: Path, out: Path, layers=(int(LAYER_DEFAULT),), limit: int = 0,
          part: bool = False) -> dict:
    t0 = time.time()
    items, manifest = read_job(job)
    ids = sorted(items, key=int)
    if limit:
        ids = ids[:limit]
    g = dev_guard(ids)                                   # before a file of a document is opened
    folds_all = json.loads(FOLDS_ALL.read_text(encoding="utf-8"))["documents"]
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))["documents"]
    missing = [d for d in ids if d not in folds_all or d not in reference]
    if missing:
        raise SystemExit(f"ids with no fold or no reference record: {missing[:10]}")
    classes, type_counts = q1_classes_of(reference)
    if classes != Q1_CLASSES:
        raise SystemExit(f"the classes of Q1 from the reference are {classes}, not those of addendum I: {Q1_CLASSES}")
    q0 = q0_labels(ids)

    docs, with_states, n_rows = [], [], 0
    for d in ids:
        doc = vb.load_doc(d, allow_closed=True)
        if not job_agrees(items[d], expected_suffix_ids(doc)):
            raise SystemExit(f"{d}: the suffix ids of the job are not Q0, Q1 and Q2.B<n> for each block (rule I1)")
        sp = states_dir / f"{d}.npz"
        has = sp.is_file()
        docs.append((d, doc, sp if has else None))
        if has:
            with_states.append(d)
            n_rows += len(doc.blocks)
    if not with_states:
        raise SystemExit(f"{rel(states_dir)}: no states file for a document of the job")
    skips, skips_path = read_skips(states_dir)
    complete, complete_text = complete_check([d for d, _doc, sp in docs if sp is None], skips)
    if limit:
        complete, complete_text = False, "the option --limit was given: a part of the job"
    if not complete and not (limit or part):
        raise SystemExit(f"{rel(states_dir)}: the states folder is not complete: {complete_text}. "
                         "Give --part for a trial on a part of the documents.")
    out.mkdir(parents=True, exist_ok=True)
    t_docs = time.time() - t0
    layers = [int(k) for k in layers]
    mm = {k: np.lib.format.open_memmap(out / f"q2_L{k}.npy", mode="w+", dtype=np.float16, shape=(n_rows, HIDDEN))
          for k in layers}
    q0_arr = {k: np.zeros((len(with_states), HIDDEN), dtype=np.float16) for k in layers}
    q1_arr = {k: np.zeros((len(with_states), HIDDEN), dtype=np.float16) for k in layers}
    lab = {f: np.zeros(n_rows, dtype=bool) for f in Q2_FIELDS}
    row_doc = np.zeros(n_rows, dtype=np.int32)
    row_block = np.zeros(n_rows, dtype=np.int32)
    row_has_text = np.zeros(n_rows, dtype=bool)
    meta, row, si, t_load, t_label, n_bytes = [], 0, 0, 0.0, 0.0, 0
    for d, doc, sp in docs:
        rf = reference[d]["fields"]
        refs = {f: reference_forms(rf[MEASURE_ID[f]]) for f in Q2_FIELDS}
        target, type_value = q1_target(reference[d])
        e = {"doc_id": d, "parliament": folds_all[d]["parliament"], "fold": int(folds_all[d]["fold"]),
             "language": doc.language, "s1_role": doc.s1_role, "blocks": len(doc.blocks),
             "blocks_with_text": sum(1 for b in doc.blocks if b.text), "has_states": sp is not None,
             "state_index": None, "row_start": None,
             "has_reference": {f: bool(refs[f]) for f in Q2_FIELDS},
             "primary_set": {f: bool(rf[MEASURE_ID[f]].get("primary_set")) for f in Q2_FIELDS},
             "q1_class": target, "q1_reference": type_value, "q0_label": q0.get(d)}
        meta.append(e)
        if sp is None:
            continue
        t1 = time.time()
        st = read_states(sp, d, manifest["template_sha256"])
        if st.suffix_ids != expected_suffix_ids(doc):
            raise SystemExit(f"{d}: the suffix ids of the states file differ from rule I1, item 6")
        n = len(doc.blocks)
        for k in layers:
            q0_arr[k][si] = st.q0(k)
            q1_arr[k][si] = st.q1(k)
            mm[k][row:row + n] = st.q2(k)
        n_bytes += sp.stat().st_size
        t_load += time.time() - t1
        t1 = time.time()
        for b in doc.blocks:
            r = row + b.index
            row_doc[r], row_block[r], row_has_text[r] = si, b.index, bool(b.text)
            for f, v in q2_labels(b, refs).items():
                lab[f][r] = v
        e["state_index"], e["row_start"] = si, row
        row += n
        si += 1
        t_label += time.time() - t1
    for k in layers:
        mm[k].flush()
        np.save(out / f"q0_L{k}.npy", q0_arr[k])
        np.save(out / f"q1_L{k}.npy", q1_arr[k])
    del mm
    np.savez(out / "rows.npz", row_doc=row_doc, row_block=row_block, row_has_text=row_has_text,
             **{f"label__{f}": v for f, v in lab.items()})
    write_json(out / "docs.json", meta, indent=None)
    tables = label_tables(meta, {f: lab[f] for f in Q2_FIELDS}, row_has_text)
    rec = {
        "version": VERSION, "made": now(), "status": STATUS, "actor": ACTOR, "synthetic": False,
        "rules": "addendum I, chapters 2 and 3", "addendum_sha256": sha256_file(ADDENDUM),
        "guard": g, "job": rel(job), "job_source": manifest["_job_source"], "states": rel(states_dir),
        "template_sha256": manifest["template_sha256"], "rule_files": rel(vb.RULES_DIR),
        "documents_of_the_job": len(ids), "documents_with_states": len(with_states),
        "documents_with_no_states_file": [e["doc_id"] for e in meta if not e["has_states"]],
        "complete": bool(complete), "complete_text": complete_text,
        "skips_file": rel(skips_path) if skips is not None else None,
        "documents_of_the_skips_file": len(skips) if skips is not None else None,
        "rows": int(n_rows), "layers": layers, "hidden": HIDDEN, "limit": limit,
        "q1_classes": list(Q1_CLASSES), "q0_classes": list(Q0_CLASSES), "q2_fields": list(Q2_FIELDS),
        "reference_type_counts_all_documents": type_counts, "labels": tables,
        "bytes_of_one_layer_float16": int(n_rows) * HIDDEN * 2, "bytes_of_the_states_files": n_bytes,
        "seconds": {"guard_and_block_files": round(t_docs, 2), "states_files": round(t_load, 2),
                    "labels": round(t_label, 2), "total": round(time.time() - t0, 2)},
        "inputs_sha256": {rel(p): sha256_file(p) for p in (REFERENCE, FOLDS_ALL, SETS, job / "manifest.json",
                                                           job / "build.json", job / "items.jsonl") if p.is_file()},
        "code_sha256": {rel(Path(__file__)): sha256_file(Path(__file__)),
                        rel(Path(vhd.__file__)): sha256_file(Path(vhd.__file__)),
                        rel(Path(vn.__file__)): sha256_file(Path(vn.__file__)),
                        rel(Path(vb.__file__)): sha256_file(Path(vb.__file__))},
    }
    rec["outputs_sha256"] = {n: sha256_file(out / n) for n in ("rows.npz", "docs.json")}
    write_json(out / "data_record.json", rec)
    return rec


def label_tables(meta: list, lab: dict, row_has_text: np.ndarray) -> dict:
    """The counts of chapter 3.2, item 23, and the counts of the targets of `Q0` and `Q1` (documents with states)."""
    with_states = [e for e in meta if e["has_states"]]
    q2 = {}
    for f in Q2_FIELDS:
        c = Counter()
        for e in with_states:
            sl = slice(e["row_start"], e["row_start"] + e["blocks"])
            in_fit = e["has_reference"][f] and (f not in PRIMARY_ONLY_FIT or e["primary_set"][f])
            c["documents_with_no_reference"] += not e["has_reference"][f]
            c["documents_with_a_reference_outside_the_primary_set_not_in_the_fit"] += e["has_reference"][f] and not in_fit
            if not in_fit:
                continue
            pos = int(lab[f][sl].sum())
            c["documents_of_the_fit"] += 1
            c["documents_with_a_positive_block"] += pos > 0
            c["documents_with_no_positive_block"] += pos == 0
            c["positive_blocks"] += pos
            c["blocks_with_text"] += int(row_has_text[sl].sum())
            c["all_blocks"] += e["blocks"]
        q2[f] = {k: int(c[k]) for k in (
            "documents_of_the_fit", "documents_with_no_reference",
            "documents_with_a_reference_outside_the_primary_set_not_in_the_fit", "documents_with_a_positive_block",
            "documents_with_no_positive_block", "positive_blocks", "blocks_with_text", "all_blocks")}
    q1 = Counter(e["q1_class"] if e["q1_class"] is not None else "not_a_class" for e in with_states)
    q0 = Counter(e["q0_label"] if e["q0_label"] is not None else "no_label" for e in with_states)
    return {"q2": q2, "q1_documents_by_class": dict(sorted(q1.items())),
            "q1_documents_of_the_fit": sum(n for k, n in q1.items() if k != "not_a_class"),
            "q0_documents_by_label": dict(sorted(q0.items())),
            "q0_documents_of_the_fit": sum(n for k, n in q0.items() if k != "no_label")}


def main() -> int:
    ap = argparse.ArgumentParser(description="state tables and label tables of the heads of addendum I")
    ap.add_argument("--states", type=Path, required=True, help="folder with one <doc>.npz for each document")
    ap.add_argument("--job", type=Path, required=True, help="job folder with items.jsonl and manifest.json")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--layers", default=LAYER_DEFAULT,
                    help="layers to write, with commas; default: layer 20 only (rule I3, item 2)")
    ap.add_argument("--limit", type=int, default=0, help="the first N documents only (a trial)")
    ap.add_argument("--part", action="store_true",
                    help="permit a states folder that is not complete; the fit tool then refuses the data folder")
    ap.add_argument("--last-run", action="store_true", help="open the sealed paths; needs the fix record")
    a = ap.parse_args()
    refuse_sealed((a.states, a.job, a.out), a.last_run, "src/m11_value_heads2_data.py")
    if a.last_run:
        raise SystemExit("this tool makes the tables of the development documents only; it has no last-run mode")
    layers = [int(k) for k in a.layers.split(",") if k]
    if set(layers) - set(LAYERS):
        raise SystemExit(f"--layers: not layers of the states files: {sorted(set(layers) - set(LAYERS))}")
    rec = build(a.states.resolve(), a.job.resolve(), a.out.resolve(), layers, a.limit, a.part)
    print(json.dumps({k: rec[k] for k in ("documents_of_the_job", "documents_with_states", "complete", "rows", "layers",
                                          "labels", "seconds", "bytes_of_one_layer_float16")}, indent=1))
    print(json.dumps({"documents_with_no_states_file": len(rec["documents_with_no_states_file"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# SPDX-License-Identifier: Apache-2.0
"""Data bundle for the isolation readout on a rented GPU (step 3.9, `m04_iso_torch.py`).

The bundle contains token ids only: the same sequences as the local MLX path (`m03_iso_jev.py`,
local tokenizer and chat template), so that both paths train and read the same input. It contains
only documents with triage PASS (`<data>/iso/triage.csv`: examination for personal data of third
parties before a document goes to a rented GPU), and never a document of group 6 or of the test
set. Group 7 is the final group: the bundle v4b does not contain its documents; the bundle of the
final group (--final-group) contains only them, without references and without targets.

Current schema: v4b (E20 version 4.1, 12 answers, layout hints). The schemas v31 and v4 are the
superseded formats of E20 version 3.1 and 4.0; they stay for the conversion and for comparison.

Contents of the schemas v31 and v4 (<data>/iso/bundle/<name>/):
  train.jsonl    one line per training document: doc_id, home (pool: the group of its parliament or
                 "free"; group document: "g<group>"), part (T, V or G), seq, pos, target
  readout.jsonl  one line per document of groups 1 to 5: doc_id, group, ids (atom ids), prefix,
                 lines (tokens of "<atom id>:" for each atom), fixed ({atom index: answer index})
  meta.json      answer ids, newline id, answers, versions, counts, SHA-256 of the two files

Usage:  uv run python src/m04_iso_bundle.py --name v4b
        uv run python src/m04_iso_bundle.py --name v4b_g7 --final-group
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_hilfe as hf  # noqa: E402
import m03_iso_jev as jev  # noqa: E402
import m03_iso_mass as ms  # noqa: E402
from m03_iso_paths import DATA, rel  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--pool-ref", default=None,
                    help="reference folder of the pool, relative to the data root. Default: v4b iso/v4/pool_ref41, "
                         "v31 iso/pool_ref. The schema v4 does not use it (it reads iso/v4/pool_ref).")
    ap.add_argument("--group-ref", default=None,
                    help="reference folder of the groups, relative to the data root. Default: v4b iso/v4/ref41, "
                         "v31 iso/ref. The schema v4 does not use it (it reads iso/v4/ref).")
    ap.add_argument("--max-length", type=int, default=16384)
    ap.add_argument("--schema", choices=["v31", "v4", "v4b"], default="v4b",
                    help="v4: answers of E20 version 4 (m03_iso_jev4, references <data>/iso/v4/...), format v3; "
                         "v4b: 12 answers, layout hints, one file docs.jsonl (see main_v4b)")
    ap.add_argument("--final-group", action="store_true",
                    help="v4b only: bundle of the final group for the final readout (no references, no targets)")
    ap.add_argument("--format", choices=["v1", "v2", "v3"], default="v1",
                    help="v1: lines with the answers (the reference answer of each earlier atom); v2: lines without answers; "
                         "v3: each atom line again in full, without answers")
    args = ap.parse_args()
    default_refs = {"v31": ("iso/pool_ref", "iso/ref"), "v4": ("iso/v4/pool_ref", "iso/v4/ref"),
                    "v4b": ("iso/v4/pool_ref41", "iso/v4/ref41")}[args.schema]
    args.pool_ref = args.pool_ref or default_refs[0]
    args.group_ref = args.group_ref or default_refs[1]

    from mlx_lm.utils import load_tokenizer

    if args.schema == "v4":
        main_v4(args, load_tokenizer(jev.MODEL))
        return
    if args.schema == "v4b":
        main_v4b(args, load_tokenizer(jev.MODEL))
        return
    tk = jev.Tokens(load_tokenizer(jev.MODEL))
    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        allowed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    with open(DATA / "iso/pool.csv", newline="", encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        groups = [r for r in csv.DictReader(f) if r["group"] != "6"]
    out = DATA / "iso/bundle" / args.name
    out.mkdir(parents=True, exist_ok=True)
    left = {"triage": [], "no_reference": [], "too_long": []}

    n_train = 0
    with open(out / "train.jsonl", "w", encoding="utf-8") as f:
        items = [(r["doc_id"], r["home"], r["part"], DATA / args.pool_ref) for r in pool]
        items += [(r["doc_id"], "g" + r["group"], "G", DATA / args.group_ref) for r in groups]
        for doc_id, home, part, ref in items:
            if doc_id not in allowed:
                left["triage"].append(doc_id)
                continue
            if not (ref / f"{doc_id}.json").exists():
                left["no_reference"].append(doc_id)
                continue
            ids, answers = jev.reference(ref, doc_id)
            seq, pos = (tk.sequence(doc_id, ids, answers) if args.format == "v1" else
                        tk.pointer_sequence(doc_id, ids) if args.format == "v2" else tk.repeat_sequence(doc_id, ids))
            if len(seq) > args.max_length:
                left["too_long"].append({"doc_id": doc_id, "tokens": len(seq)})
                continue
            f.write(json.dumps({"doc_id": doc_id, "home": home, "part": part, "seq": seq, "pos": pos,
                                "target": [jev.ANSWERS.index(x) for x in answers]}) + "\n")
            n_train += 1

    n_read = 0
    with open(out / "readout.jsonl", "w", encoding="utf-8") as f:
        for r in groups:
            d = r["doc_id"]
            if d not in allowed:
                left["triage"].append(d)
                continue
            ids = ms.atom_ids(d)
            fixed = hf.fixed_roles(d)[0]
            pseq, ppos = tk.pointer_sequence(d, ids) if args.format != "v3" else tk.repeat_sequence(d, ids)
            f.write(json.dumps({"doc_id": d, "group": r["group"], "ids": ids, "prefix": tk.prefix(d),
                                "lines": [tk.line(a) for a in ids], "pointer_seq": pseq, "pointer_pos": ppos,
                                "fixed": {i: jev.ANSWERS.index(fixed[a][0]) for i, a in enumerate(ids) if a in fixed}})
                    + "\n")
            n_read += 1

    meta = {"name": args.name, "task": jev.VERSION, "format": args.format, "fixed_roles": hf.VERSION, "answers": list(jev.ANSWERS),
            "answer_ids": tk.answer_ids, "nl": tk.nl, "max_length": args.max_length,
            "train_documents": n_train, "readout_documents": n_read, "left_out": left,
            "sha256": {"train.jsonl": sha(out / "train.jsonl"), "readout.jsonl": sha(out / "readout.jsonl")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "left_out"}, indent=1))
    print("left out:", {k: len(v) for k, v in left.items()})


def main_v4(args, tok) -> None:
    import m03_iso_jev4 as j4

    tk = j4.Tokens(tok)
    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        allowed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    with open(DATA / "iso/pool.csv", newline="", encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        groups = [r for r in csv.DictReader(f) if r["group"] != "6"]
    out = DATA / "iso/bundle" / args.name
    out.mkdir(parents=True, exist_ok=True)
    left = {"triage": [], "no_reference": [], "too_long": []}
    n_train = 0
    with open(out / "train.jsonl", "w", encoding="utf-8") as f:
        items = [(r["doc_id"], r["home"], r["part"], DATA / "iso/v4/pool_ref") for r in pool]
        items += [(r["doc_id"], "g" + r["group"], "G", DATA / "iso/v4/ref") for r in groups]
        for doc_id, home, part, ref in items:
            if doc_id not in allowed:
                left["triage"].append(doc_id)
                continue
            if not (ref / f"{doc_id}.json").exists():
                left["no_reference"].append(doc_id)
                continue
            ids, answers = j4.reference(ref, doc_id)
            seq, pos = tk.repeat_sequence(doc_id, ids)
            if len(seq) > args.max_length:
                left["too_long"].append({"doc_id": doc_id, "tokens": len(seq)})
                continue
            f.write(json.dumps({"doc_id": doc_id, "home": home, "part": part, "seq": seq, "pos": pos,
                                "target": [j4.ANSWERS.index(x) for x in answers]}) + "\n")
            n_train += 1
    n_read = 0
    with open(out / "readout.jsonl", "w", encoding="utf-8") as f:
        for r in groups:
            d = r["doc_id"]
            if d not in allowed:
                left["triage"].append(d)
                continue
            ids = ms.atom_ids(d)
            fixed = j4.fixed_answers(d)
            pseq, ppos = tk.repeat_sequence(d, ids)
            f.write(json.dumps({"doc_id": d, "group": r["group"], "ids": ids, "pointer_seq": pseq,
                                "pointer_pos": ppos, "prefix": [], "lines": [],
                                "fixed": {i: j4.ANSWERS.index(fixed[a]) for i, a in enumerate(ids) if a in fixed}}) + "\n")
            n_read += 1
    meta = {"name": args.name, "task": j4.VERSION, "schema": "e20-v4", "format": "v3", "answers": list(j4.ANSWERS),
            "answer_ids": tk.answer_ids, "nl": tk.nl, "max_length": args.max_length,
            "train_documents": n_train, "readout_documents": n_read, "left_out": left,
            "sha256": {"train.jsonl": sha(out / "train.jsonl"), "readout.jsonl": sha(out / "readout.jsonl")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k not in ("left_out", "answer_ids")}, indent=1))
    print("left out:", {k: len(v) for k, v in left.items()})


def main_v4b(args, tok) -> None:
    """Bundle v4b: one file docs.jsonl; the trainer selects train, monitor and readout documents.

    docs.jsonl, one line per document: doc_id, body_key, home (pool: home of pool.csv; group
    document: "g<group>"), part (T, V; group document: G), group, ids, seq, pos (readout position
    of each atom), fixed (atom indices with a fixed answer), target (index in the 12 answers; -1 at
    a fixed atom: no loss), learn (false for a document of a parliament of the final groups: never
    for training, monitor, transitions or CRF; only readout for the measurement of a fold; rule of the
    project: no method learns from a document of a parliament of the final group). Not in the
    bundle: triage FAIL, no reference, groups 6 and 7.
    Never cut (E18): a document longer than --max-length stops the script.
    """
    import m03_iso_jev4 as j4
    import m03_iso_v4 as v4

    tk = j4.Tokens(tok, v2=True)
    titles = json.loads((DATA / "iso/titles.json").read_text(encoding="utf-8"))
    final_parl = v4.final_parliaments()
    if args.final_group:
        final_bundle(args, tk, titles)
        return
    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        allowed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    with open(DATA / "iso/pool.csv", newline="", encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        groups = [r for r in csv.DictReader(f) if r["group"] not in {"6"} | v4.FINAL_GROUPS]
    items = [(r["doc_id"], r["body_key"], r["home"], r["part"], "", DATA / args.pool_ref) for r in pool]
    items += [(r["doc_id"], r["body_key"], "g" + r["group"], "G", r["group"], DATA / args.group_ref) for r in groups]
    out = DATA / "iso/bundle" / args.name
    out.mkdir(parents=True, exist_ok=True)
    left = {"triage": [], "no_reference": [], "final_parliament": [], "too_long": []}
    n = 0
    with open(out / "docs.jsonl", "w", encoding="utf-8") as f:
        for doc_id, body, home, part, group, ref in items:
            learn = body not in final_parl
            if not learn:
                left["final_parliament"].append(doc_id)
            if doc_id not in allowed:
                left["triage"].append(doc_id)
                continue
            if not (ref / f"{doc_id}.json").exists():
                left["no_reference"].append(doc_id)
                continue
            ids, answers = j4.reference(ref, doc_id)
            fixed = j4.fixed_answers(doc_id)
            bad = [a for a, y in zip(ids, answers) if (y == "furniture") != (fixed.get(a) == "furniture")]
            if bad:
                raise SystemExit(f"{doc_id}: furniture differs from the fixed answers at {bad[:5]} (run validate4)")
            seq, pos = tk.repeat_sequence(doc_id, ids, j4.hints_v2(doc_id, titles))
            if len(seq) > args.max_length:
                left["too_long"].append({"doc_id": doc_id, "tokens": len(seq)})
                continue
            fix = [i for i, a in enumerate(ids) if a in fixed]
            target = [-1 if a in fixed else j4.ANSWERS12.index(y) for a, y in zip(ids, answers)]
            f.write(json.dumps({"doc_id": doc_id, "body_key": body, "home": home, "part": part, "group": group,
                                "learn": learn, "ids": ids, "seq": seq, "pos": pos, "fixed": fix, "target": target})
                    + "\n")
            n += 1
    if left["too_long"]:
        raise SystemExit(f"documents longer than {args.max_length} tokens: {left['too_long']} (E18: never cut)")
    import m03_iso_hints as mh

    meta = {"name": args.name, "task": j4.VERSION, "schema": "e20-v4", "format": "v3h", "hints": mh.VERSION,
            "answers": list(j4.ANSWERS12), "answer_ids": tk.answer_ids, "nl": tk.nl, "max_length": args.max_length,
            "documents": n, "final_parliaments": sorted(final_parl), "left_out": left,
            "pool_ref": rel(DATA / args.pool_ref), "group_ref": rel(DATA / args.group_ref),
            "monitor_rule": "part V and home free (parliaments without any group document and without a training document)",
            "sha256": {"docs.jsonl": sha(out / "docs.jsonl")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k not in ("left_out", "answer_ids", "final_parliaments")}, indent=1))
    print("left out:", {k: len(v) for k, v in left.items() if k != "final_parliament"},
          "readout only (final parliaments):", len(left["final_parliament"]))


def final_bundle(args, tk, titles) -> None:
    """Bundle of the final group: token ids only; no reference is read (the developer sees counts only)."""
    import m03_iso_hints as mh
    import m03_iso_jev4 as j4
    import m03_iso_v4 as v4

    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        allowed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["group"] in v4.FINAL_GROUPS]
    out = DATA / "iso/bundle" / args.name
    out.mkdir(parents=True, exist_ok=True)
    left, n = [], 0
    with open(out / "docs.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            d = r["doc_id"]
            if d not in allowed:
                left.append(d)
                continue
            ids = ms.atom_ids(d)
            fixed = j4.fixed_answers(d)
            seq, pos = tk.repeat_sequence(d, ids, j4.hints_v2(d, titles))
            if len(seq) > args.max_length:
                raise SystemExit(f"{d}: {len(seq)} tokens > {args.max_length} (E18: never cut)")
            f.write(json.dumps({"doc_id": d, "body_key": r["body_key"], "home": "g" + r["group"], "part": "F",
                                "group": r["group"], "learn": False, "ids": ids, "seq": seq, "pos": pos,
                                "fixed": [i for i, a in enumerate(ids) if a in fixed], "target": [-1] * len(ids)}) + "\n")
            n += 1
    meta = {"name": args.name, "final": True, "task": j4.VERSION, "schema": "e20-v4", "format": "v3h", "hints": mh.VERSION,
            "answers": list(j4.ANSWERS12), "answer_ids": tk.answer_ids, "nl": tk.nl, "max_length": args.max_length,
            "documents": n, "left_out_triage": left, "sha256": {"docs.jsonl": sha(out / "docs.jsonl")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"final bundle: {n} documents, left out (triage) {len(left)}, sha256 {meta['sha256']['docs.jsonl']}")


if __name__ == "__main__":
    main()

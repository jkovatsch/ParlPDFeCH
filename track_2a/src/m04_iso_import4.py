# SPDX-License-Identifier: Apache-2.0
"""Import the readout of `m04_iso_torch.py` for E20 version 4 and decide by Viterbi (step 3.9).

Input: one JSON per document (format "e20-v4-readout") with the log probabilities of the answers in
its field "answers" for each atom. Decision over the atoms of a document:
- Fixed answers (`m03_iso_jev4.fixed_answers`) are given; furniture comes only from a fixed answer.
- State = the last text answer. "none" and "furniture" do not change the state (two runs of the
  same answer that only none atoms separate are one text block, E20 v4).
- The decoder adds a transition cost only where a text block starts: lam * log P(first answer) at
  the first text atom, lam * log P(b | a, change) where the text answer changes from a to b. A text
  atom that continues its block and a none atom have no cost (version 1 added log T[a -> a] at
  each text atom; this made none cheaper than text; a code review found this defect on 05.10.2026).
- P from the reference blocks of the training documents of the same fold: documents of the
  excluded groups (--exclude-homes, required: the measured groups of the fold), of group 6 and of
  the parliaments of the final groups are never counted. Each readout document must belong to an
  excluded group. The reference folders for P: --trans-ref-groups and --trans-ref-pool (defaults:
  the folders of the gate runs, iso/v4/ref and iso/v4/pool_ref, relative to the data root).
Output: version 4 answer files in <data>/iso/v4/hyp_<name>/ and run.json with all parameters.

Usage:  python3 src/m04_iso_import4.py data/iso/pod/foldY_v4b --name foldY_v4b --exclude-homes 3,5 --lam 1
        (the readout folder is relative to the working folder; here: track_2a with the default data root)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_jev4 as j4  # noqa: E402
import m03_iso_mass as ms  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
from m03_iso_paths import DATA, rel  # noqa: E402

TEXT = list(v4.TEXT)
FORMAT = "e20-v4-readout"
VERSION = "import4-v2"


def blocks(answers: list[str]) -> list[int]:
    """The text answers of the blocks: none and furniture do not split a block."""
    out = []
    for a in answers:
        if a in TEXT and (not out or out[-1] != TEXT.index(a)):
            out.append(TEXT.index(a))
    return out


def transitions(docs: list[tuple[str, Path]]):
    """Add-one estimates: log P(first block answer), log P(b | a, b != a)."""
    k = len(TEXT)
    start = [1.0] * k
    change = [[0.0 if a == b else 1.0 for b in range(k)] for a in range(k)]
    for d, ref in docs:
        seq = blocks(json.loads((ref / f"{d}.json").read_text())["answers"])
        if seq:
            start[seq[0]] += 1
        for a, b in zip(seq, seq[1:]):
            change[a][b] += 1
    ls = [math.log(v / sum(start)) for v in start]
    lt = [[math.log(v / sum(r)) if v > 0 else 0.0 for v in r] for r in change]
    return ls, lt


def viterbi(logp, cols, ids, fixed, ls, lt, lam):
    """logp[t][i] is the log probability of answer cols[i] at atom t."""
    neg = -1e18
    score, back = {None: 0.0}, []
    free = [i for i, x in enumerate(cols) if x != "furniture"]
    for t, a in enumerate(ids):
        if a in fixed:
            options = [(fixed[a], 0.0)]
        else:
            options = [(cols[i], logp[t][i]) for i in free]
        new, ptr = {}, {}
        for s, v in score.items():
            for ans, e in options:
                if ans in TEXT:
                    c = TEXT.index(ans)
                    cost = 0.0 if s == c else lam * (ls[c] if s is None else lt[s][c])
                    ns, sc = c, v + e + cost
                else:
                    ns, sc = s, v + e
                if sc > new.get(ns, neg):
                    new[ns], ptr[ns] = sc, (s, ans)
        score = new
        back.append(ptr)
    s = max(score, key=score.get)
    out = []
    for ptr in reversed(back):
        prev, ans = ptr[s]
        out.append(ans)
        s = prev
    return out[::-1]


def training_references(excluded: set[str], ref_groups: Path, ref_pool: Path) -> list[tuple[str, Path]]:
    final_parl = v4.final_parliaments()
    with open(DATA / "iso/pool.csv", newline="", encoding="utf-8") as f:
        docs = [(r["doc_id"], ref_pool) for r in csv.DictReader(f)
                if r["home"] not in excluded and r["body_key"] not in final_parl
                and (ref_pool / f"{r['doc_id']}.json").exists()]
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        docs += [(r["doc_id"], ref_groups) for r in csv.DictReader(f)
                 if r["group"] not in excluded and r["body_key"] not in final_parl]
    return docs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--name", required=True)
    ap.add_argument("--exclude-homes", required=True, help="the groups of the readout documents (fold), e.g. 3,5")
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--argmax", action="store_true", help="no Viterbi: the most probable answer of each atom")
    ap.add_argument("--trans-ref-groups", default="iso/v4/ref",
                    help="references of the groups for the transitions, relative to the data root")
    ap.add_argument("--trans-ref-pool", default="iso/v4/pool_ref",
                    help="references of the pool for the transitions, relative to the data root")
    args = ap.parse_args()
    excluded = {h for h in args.exclude_homes.split(",") if h} | {"6"} | v4.FINAL_GROUPS
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        group_of = {r["doc_id"]: r["group"] for r in csv.DictReader(f)}
    train = training_references(excluded, DATA / args.trans_ref_groups, DATA / args.trans_ref_pool)
    ls, lt = transitions(train)
    out = DATA / "iso/v4" / f"hyp_{args.name}"
    files = sorted(p for p in Path(args.src).glob("*.json") if p.name not in ("run.json", "config.json"))
    n, sources = 0, {}
    for p in files:
        x = json.loads(p.read_text())
        if x.get("format") != FORMAT:
            raise SystemExit(f"{p}: format {x.get('format')!r}, expected {FORMAT!r}")
        cols = x["answers"]
        if not set(cols) <= set(v4.ANSWERS) or not set(TEXT) <= set(cols):
            raise SystemExit(f"{p}: answers {cols} do not match E20 version 4")
        d = x["doc_id"]
        if d in group_of and group_of[d] not in excluded:
            raise SystemExit(f"{p}: document of group {group_of[d]} is not in --exclude-homes {args.exclude_homes}")
        ids = ms.atom_ids(d)
        if ids != x["ids"]:
            raise SystemExit(f"{p}: atom ids differ from the atoms of {d}")
        fixed = j4.fixed_answers(d)
        logp = [list(r) for r in x["logprobs"]]
        if args.argmax:
            answers = []
            for t, a in enumerate(ids):
                if a in fixed:
                    answers.append(fixed[a])
                    continue
                row = [v if cols[i] != "furniture" else -1e9 for i, v in enumerate(logp[t])]
                answers.append(cols[max(range(len(row)), key=row.__getitem__)])
        else:
            answers = viterbi(logp, cols, ids, fixed, ls, lt, args.lam)
        v4.write(out, d, answers, f"torch:{args.name}", str(p))
        sources[d] = hashlib.sha256(p.read_bytes()).hexdigest()
        n += 1
    (out / "run.json").write_text(json.dumps({
        "version": VERSION, "src": args.src, "name": args.name, "exclude_homes": sorted(excluded), "lam": args.lam,
        "argmax": args.argmax, "transition_documents": len(train),
        "transition_references": {"groups": rel(DATA / args.trans_ref_groups), "pool": rel(DATA / args.trans_ref_pool)},
        "documents": n, "readout_sha256": sources,
        "log_start": [round(v, 4) for v in ls]}, indent=1), encoding="utf-8")
    print(f"{n} documents -> {out}; transitions from {len(train)} reference documents")


if __name__ == "__main__":
    main()

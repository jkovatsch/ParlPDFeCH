# SPDX-License-Identifier: Apache-2.0
"""Error analysis of an isolation method by cause (E20 version 4.1, step 3.9).

For each document of the set: the reference boundaries that the method misses or labels wrong,
grouped by the pair of answers (previous -> next, for example "title -> submitted"); the method
boundaries that the reference does not have; the omitted and intruded text atoms, grouped by the
answer of the reference or the method and by the Docling form of the atom. Counts only.

Usage:  python3 src/m04_iso_errors.py --ref data/iso/v4/ref41 --hyp data/iso/v4/hyp_oof_a1 --groups 1,2,3,4,5
        (folder arguments are relative to the working folder; here: track_2a with the default data root)
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_mass as ms  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
from m03_iso_paths import DATA  # noqa: E402


def form(atom: dict) -> str:
    h = atom.get("hinweise") or []
    for k in ("Überschrift", "Listenpunkt", "Tabelle", "Fussnote", "Bildlegende", "Kopfzeile", "Fusszeile", "Feld"):
        if any(x.startswith(k) for x in h):
            return k
    return "Text"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--hyp", required=True)
    ap.add_argument("--groups", required=True)
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args()
    docs = v4.group_docs(args.groups.split(","), args.final)
    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        passed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    missed, wrong, extra = collections.Counter(), collections.Counter(), collections.Counter()
    omitted, intruded, classerr = collections.Counter(), collections.Counter(), collections.Counter()
    per_doc = {}
    for d in [x for x in docs if x in passed]:
        atoms = v4.atoms_of(d)
        ids = [a["id"] for a in atoms]
        ref = v4.load_answers(Path(args.ref) / f"{d}.json", d, ids)
        hyp = v4.load_answers(Path(args.hyp) / f"{d}.json", d, ids)
        carried = v4.carried_ids(atoms)
        skip = {i for i, a in enumerate(ids) if a in carried}
        br, bh, good, _ = v4.boundaries(ref, hyp, skip)
        seq = [i for i, x in enumerate(ref) if x in v4.TEXT and i not in skip]
        for k in br - good:
            pair = f"{ref[seq[k - 1]]} -> {ref[seq[k]]}"
            (wrong if k in bh else missed)[pair] += 1
        hseq_prev = {}
        prev = None
        for k, i in enumerate(seq):
            h = hyp[i] if hyp[i] in v4.TEXT else prev
            hseq_prev[k] = (prev, h)
            prev = h
        for k in bh - br:
            p, h = hseq_prev[k]
            extra[f"{p} -> {h} (ref {ref[seq[k]]})"] += 1
        n_err = 0
        for i, (r, h) in enumerate(zip(ref, hyp)):
            if r in v4.TEXT and h not in v4.TEXT:
                omitted[f"{r} [{form(atoms[i])}]"] += 1
                n_err += 1
            elif h in v4.TEXT and r not in v4.TEXT:
                intruded[f"{h} on {r} [{form(atoms[i])}]"] += 1
                n_err += 1
            elif r in v4.TEXT and h in v4.TEXT and r != h:
                classerr[f"{r} -> {h}"] += 1
                n_err += 1
        per_doc[d] = {"boundaries_missed_or_wrong": len(br - good), "extra_boundaries": len(bh - br), "atom_errors": n_err}
    out = {"missed_boundaries": missed.most_common(), "wrong_label_boundaries": wrong.most_common(),
           "extra_boundaries": extra.most_common(15), "omitted_atoms": omitted.most_common(15),
           "intruded_atoms": intruded.most_common(15), "class_errors": classerr.most_common(15), "documents": per_doc}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

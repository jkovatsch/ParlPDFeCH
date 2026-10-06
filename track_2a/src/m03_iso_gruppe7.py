# SPDX-License-Identifier: Apache-2.0
"""Step 3.7: select the final group 7 (gate 3a), by a script with a seed (decision by delegation 05.10.2026).

Group 6 became a development group (measured two times for G3a.3, E20 changed between, exposure of
05.10.2026, 21:55). No parliament of the training set or the validation set is outside the pool and
the groups 1 to 6. Thus group 7 takes 8 parliaments of the pool, and NO method may learn from any
document of these parliaments (pool documents and group documents): `m04_iso_bundle.py` marks them
with home "7" and the training scripts exclude them always.

Candidates: documents of the stratified sample (m03_iso_paths.SAMPLE_LIST) of pool parliaments
(not in pool.csv, not in gruppen.csv, not inspection documents, not R8 duplicates), with the role
vorstoss, antwort or kombiniert, not more than 25 pages, PDF downloaded. One document for each
parliament. Selection with random.Random(SEED): at least 2 French documents, at least 2 Italian or
Romansh documents, then the rest. The project records the SHA-256 of the file before anybody looks
at a document. The rows of group 7 are appended to <data>/iso/gruppen.csv (group "7").

Usage:  python3 src/m03_iso_gruppe7.py
"""

from __future__ import annotations

import collections
import csv
import hashlib
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, SAMPLE_LIST, SAMPLE_PDF  # noqa: E402

AN = DATA / "analyse"
SEED = 20261010
N = 8
SCOPE = ("vorstoss", "antwort", "kombiniert")


def read(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    groups = read(DATA / "iso/gruppen.csv")
    if any(r["group"] == "7" for r in groups):
        raise SystemExit("group 7 exists already")
    split = {z["body_key"]: z["rolle"] for z in read(AN / "synthese/split.csv")}
    dup = {z["doc_id"] for z in read(AN / "synthese/split_ausschluss_duplikate.csv")}
    insp = {z["doc_id"] for z in read(AN / "pdf/augenschein.csv")}
    pool = read(DATA / "iso/pool.csv")
    pool_doc = {r["doc_id"] for r in pool}
    group_doc = {r["doc_id"] for r in groups}
    parl = sorted({r["body_key"] for r in pool})
    cand = collections.defaultdict(list)
    for z in read(SAMPLE_LIST):
        if (z["body_key"] in parl and z["doc_id"] not in pool_doc and z["doc_id"] not in group_doc
                and z["doc_id"] not in dup and z["doc_id"] not in insp and z["dokumentrolle"] in SCOPE
                and 0 < int(z["seiten"] or 0) <= 25
                and (SAMPLE_PDF / f"{z['doc_id']}.pdf").exists()):
            cand[z["body_key"]].append(z)
    rng = random.Random(SEED)
    one = {}
    for b in sorted(cand):
        docs = sorted(cand[b], key=lambda z: int(z["doc_id"]))
        one[b] = docs[rng.randrange(len(docs))]
    order = sorted(one)
    rng.shuffle(order)
    chosen = []

    def take(pred, n):
        for b in order:
            if len([c for c in chosen if pred(one[c])]) >= n or len(chosen) >= N:
                return
            if b not in chosen and pred(one[b]):
                chosen.append(b)

    take(lambda z: z["sprache"] == "fr", 2)
    take(lambda z: z["sprache"] in ("it", "rm"), 2)
    take(lambda z: True, N)
    rows = [{"group": "7", "doc_id": one[b]["doc_id"], "body_key": b, "split": split[b], "ebene": one[b]["ebene"],
             "sprache": one[b]["sprache"], "scan": one[b]["scan"], "dokumentrolle": one[b]["dokumentrolle"],
             "seiten": one[b]["seiten"], "sha256": one[b]["sha256"], "url": one[b]["url"]} for b in chosen]
    with open(DATA / "iso/gruppen.csv", "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=list(groups[0])).writerows(rows)
    with open(DATA / "iso/gruppe7.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    sha = hashlib.sha256((DATA / "iso/gruppe7.csv").read_bytes()).hexdigest()
    print(f"group 7: {len(rows)} documents from {len(chosen)} parliaments; candidates {len(cand)} parliaments; "
          f"languages {dict(collections.Counter(r['sprache'] for r in rows))}; "
          f"roles {dict(collections.Counter(r['dokumentrolle'] for r in rows))}; "
          f"scans {sum(r['scan'] != 'digital' for r in rows)}; sha256 {sha}")


if __name__ == "__main__":
    main()

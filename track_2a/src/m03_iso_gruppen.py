# SPDX-License-Identifier: Apache-2.0
"""Step 3.7 (isolation path, E29): select five groups of documents from whole parliaments.

Pool: the downloaded documents of the stratified sample (m03_iso_paths.SAMPLE_LIST) that
- belong to a parliament of the training set or the validation set of split v2 (E26),
- are not inspection documents and not in `split_ausschluss_duplikate.csv` (R8),
- have the document role vorstoss, antwort or kombiniert (scope of gate 3a),
- have not more than 25 pages (limit of this step; the report states it).

Each parliament goes into exactly one group. The assignment balances state level, language and
scans over the groups (seed 20261005). Each group gets 8 documents:
3 vorstoss, 3 antwort, 2 kombiniert where the pool allows it; at least 2 scans; not more than
2 documents of one parliament.

Groups 1 to 6 are development groups. Group 7 is the final group (m03_iso_gruppe7.py). Group 6 was
selected later with seed 20261006; the code of that selection is not in this repository. The script
stops if gruppen.csv exists, because a new run would remove the rows of groups 6 and 7.

Output: <data>/iso/gruppen.csv. Usage: python3 src/m03_iso_gruppen.py
"""

from __future__ import annotations

import collections
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, SAMPLE_LIST, SAMPLE_PDF  # noqa: E402

AN = DATA / "analyse"
OUT = DATA / "iso"
SEED = 20261005
N_GROUPS = 5
PER_GROUP = 8
ROLE_TARGET = {"vorstoss": 3, "antwort": 3, "kombiniert": 2}
MAX_PAGES = 25


def read(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    if (OUT / "gruppen.csv").exists():
        raise SystemExit(f"{OUT / 'gruppen.csv'} exists: a new run would remove the rows of groups 6 and 7 (stop)")
    split = {z["body_key"]: z["rolle"] for z in read(AN / "synthese/split.csv")}
    dup = {z["doc_id"] for z in read(AN / "synthese/split_ausschluss_duplikate.csv")}
    insp = {z["doc_id"] for z in read(AN / "pdf/augenschein.csv")}
    pool = [z for z in read(SAMPLE_LIST)
            if split.get(z["body_key"]) in ("Training", "Validierung")
            and z["doc_id"] not in dup and z["doc_id"] not in insp
            and z["dokumentrolle"] in ROLE_TARGET
            and 0 < int(z["seiten"] or 0) <= MAX_PAGES
            and (SAMPLE_PDF / f"{z['doc_id']}.pdf").exists()]
    rng = random.Random(SEED)
    by_parl = collections.defaultdict(list)
    for z in pool:
        by_parl[z["body_key"]].append(z)
    parls = sorted(by_parl)
    rng.shuffle(parls)
    # balance: sort parliaments by (state level, language) stratum, then deal them round robin
    def stratum(b: str) -> tuple:
        z = by_parl[b][0]
        return (z["ebene"], z["sprache"])
    parls.sort(key=stratum)
    group_of = {}
    counts = [collections.Counter() for _ in range(N_GROUPS)]
    for b in parls:
        st = stratum(b)
        g = min(range(N_GROUPS), key=lambda i: (counts[i][st], sum(counts[i].values()), rng.random()))
        group_of[b] = g
        counts[g][st] += 1
    rows = []
    for g in range(N_GROUPS):
        cand = [z for b, gg in group_of.items() if gg == g for z in by_parl[b]]
        rng.shuffle(cand)
        chosen, per_parl = [], collections.Counter()
        def take(pred, n):
            for z in cand:
                if len([c for c in chosen if pred(c)]) >= n or len(chosen) >= PER_GROUP:
                    break
                if z in chosen or per_parl[z["body_key"]] >= 2 or not pred(z):
                    continue
                chosen.append(z)
                per_parl[z["body_key"]] += 1
        take(lambda z: z["scan"] != "digital", 2)
        take(lambda z: z["sprache"] == "fr", 2)
        take(lambda z: z["sprache"] == "it", 1)
        for role, n in ROLE_TARGET.items():
            take(lambda z, r=role: z["dokumentrolle"] == r, n)
        take(lambda z: True, PER_GROUP)
        for z in chosen:
            rows.append({"group": g + 1, "doc_id": z["doc_id"], "body_key": z["body_key"],
                         "split": split[z["body_key"]], "ebene": z["ebene"], "sprache": z["sprache"],
                         "scan": z["scan"], "dokumentrolle": z["dokumentrolle"], "seiten": z["seiten"],
                         "sha256": z["sha256"], "url": z["url"]})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "gruppen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"pool {len(pool)} documents in {len(by_parl)} parliaments")
    for g in range(1, N_GROUPS + 1):
        r = [x for x in rows if x["group"] == g]
        print(f"group {g}: {len(r)} documents, {len({x['body_key'] for x in r})} parliaments; "
              f"roles {dict(collections.Counter(x['dokumentrolle'] for x in r))}; "
              f"languages {dict(collections.Counter(x['sprache'] for x in r))}; "
              f"scans {sum(x['scan'] != 'digital' for x in r)}; "
              f"levels {dict(collections.Counter(x['ebene'] for x in r))}")


if __name__ == "__main__":
    main()

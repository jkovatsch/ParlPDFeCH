# SPDX-License-Identifier: Apache-2.0
"""Step 3.7 (isolation path): the training pool for a learned isolation method.

A measurement on a group must be a measurement on parliaments that the method did not see.
Thus, the pool records the group of the parliament of each document ("home"): "free" if no group
uses the parliament. A method that is measured on group g learns only from documents with a home
other than g. When this script ran, group 6 was the final group: the pool does not contain documents
of the parliaments of group 6. Since then, group 6 is a development group, and group 7 is the final
group. The 8 parliaments of group 7 are pool parliaments: m04_iso_bundle.py marks their documents,
and no method learns from them.

Pool: the downloaded documents of the stratified sample (m03_iso_paths.SAMPLE_LIST) that
- belong to a parliament of the training set (part T) or of the validation set (part V) of split v2 (E26),
- are not in gruppen.csv and do not belong to a parliament of group 6,
- are not inspection documents and not in `split_ausschluss_duplikate.csv` (R8),
- have not more than 25 pages (same limit as the groups).
Not more than CAP documents for each parliament (seed SEED): first the documents with the roles
vorstoss, antwort and kombiniert (scope of gate 3a), then the other roles. The other roles are in
the pool, because the document role in the metadata is not reliable (E20).

Output: <data>/iso/pool.csv. The script stops if pool.csv exists. Usage: python3 src/m03_iso_pool.py
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
MAX_PAGES = 25
CAP = 6
SEED = 20261007
SCOPE = ("vorstoss", "antwort", "kombiniert")


def read(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    if (DATA / "iso/pool.csv").exists():
        raise SystemExit(f"{DATA / 'iso/pool.csv'} exists (stop)")
    split = {z["body_key"]: z["rolle"] for z in read(AN / "synthese/split.csv")}
    dup = {z["doc_id"] for z in read(AN / "synthese/split_ausschluss_duplikate.csv")}
    insp = {z["doc_id"] for z in read(AN / "pdf/augenschein.csv")}
    groups = read(DATA / "iso/gruppen.csv")
    home = {z["body_key"]: z["group"] for z in groups}
    group_doc = {z["doc_id"] for z in groups}
    part = {"Training": "T", "Validierung": "V"}
    by_parl = collections.defaultdict(list)
    for z in read(SAMPLE_LIST):
        if (split.get(z["body_key"]) in part and home.get(z["body_key"]) != "6"
                and z["doc_id"] not in group_doc and z["doc_id"] not in dup and z["doc_id"] not in insp
                and 0 < int(z["seiten"] or 0) <= MAX_PAGES
                and (SAMPLE_PDF / f"{z['doc_id']}.pdf").exists()):
            by_parl[z["body_key"]].append(z)
    rows = []
    for b in sorted(by_parl):
        docs = sorted(by_parl[b], key=lambda z: int(z["doc_id"]))
        random.Random(f"{SEED}|{b}").shuffle(docs)
        docs.sort(key=lambda z: z["dokumentrolle"] not in SCOPE)
        for z in docs[:CAP]:
            rows.append({"part": part[split[b]], "home": home.get(b, "free"), "doc_id": z["doc_id"],
                         "body_key": b, "ebene": z["ebene"], "sprache": z["sprache"], "scan": z["scan"],
                         "dokumentrolle": z["dokumentrolle"], "seiten": z["seiten"], "sha256": z["sha256"]})
    rows.sort(key=lambda r: (r["home"], r["part"], r["body_key"], int(r["doc_id"])))
    with open(DATA / "iso/pool.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for h in sorted({x["home"] for x in rows}):
        r = [x for x in rows if x["home"] == h]
        print(f"home {h}: {len(r)} documents, {len({x['body_key'] for x in r})} parliaments; "
              f"roles {dict(collections.Counter(x['dokumentrolle'] for x in r))}; "
              f"languages {dict(collections.Counter(x['sprache'] for x in r))}; "
              f"scans {sum(x['scan'] != 'digital' for x in r)}; "
              f"levels {dict(collections.Counter(x['ebene'] for x in r))}")


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Human gold set (decision E32): select the documents of the pilot, the test set and the training extension.

Three lists, each with a fixed seed, written one time (a list that exists stops the script):

  <data>/gold/pilot.csv       20 documents of the development groups 1 to 6 (they have the reference
                             ref41). The 7 documents of the blind native coding are in the pilot;
                             13 more by seed with at least 4 French, 3 Italian, 1 Romansh and 4 scan
                             documents. Jonathan's decisions on the pilot can change E20 (development).
  <data>/gold/test.csv        the documents of the test parliaments (split role "Gold", process rule 6)
                             that are downloaded: candidates of the human test set. Nobody changes E20
                             from them; the developer of a method sees only counts.
  <data>/gold/extension.csv   documents of training and validation parliaments that no list uses yet:
                             candidates for more training references (AI coding).

Candidates of the test list and the extension list: the documents of the stratified sample
(m03_iso_paths.SAMPLE_LIST, PDF files in SAMPLE_PDF).
Common filters: PDF downloaded, not more than 25 pages, not an inspection document, not an R8 copy,
and for the extension: not a parliament of the final groups.

Usage:  python3 src/m03_gold_select.py
        python3 src/m03_gold_select.py --repeat pilot   (process rule 2.4: 15 % again, blind, 24 h after the last change)
        python3 src/m03_gold_select.py --blind pilot    (4 documents without a proposal; before the review starts)
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
OUT = DATA / "gold"
SEED = 20261006
PILOT = 20
FIELDS = ["list", "doc_id", "body_key", "split", "group", "ebene", "sprache", "scan", "dokumentrolle", "seiten", "sha256", "url"]


def read(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name: str, rows: list[dict]) -> None:
    p = OUT / name
    if p.exists():
        raise SystemExit(f"{p} exists: the list is fixed")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} documents; languages {dict(collections.Counter(r['sprache'] for r in rows))}; "
          f"roles {dict(collections.Counter(r['dokumentrolle'] for r in rows))}; "
          f"scans {sum(r['scan'] != 'digital' for r in rows)}")


def repeat(batch: str) -> None:
    """Process rule 2.4: a blind second check of 15 % of the documents, at least one day after the last change.

    The batch must be complete. The list stores the SHA-256 of each first answer file, so that the
    report can show a change of the first answers after the selection.
    """
    import hashlib
    import json
    import time

    out = OUT / f"{batch}_repeat.csv"
    if out.exists():
        raise SystemExit(f"{out} exists: the list is fixed")
    with open(OUT / f"{batch}.csv", newline="", encoding="utf-8") as f:
        rows = {r["doc_id"]: r for r in csv.DictReader(f)}
    open_docs, last = [], ""
    for d in rows:
        p = OUT / batch / "decisions" / f"{d}.json"
        x = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        if x.get("status") != "fertig":
            open_docs.append(d)
        last = max(last, (x.get("last_changed") or x.get("last_saved") or "")[:19])
    if open_docs:
        raise SystemExit(f"{len(open_docs)} documents of {batch} are not finished; the repetition starts after the end of the batch")
    age_h = (time.time() - time.mktime(time.strptime(last, "%Y-%m-%dT%H:%M:%S"))) / 3600
    if age_h < 24:
        raise SystemExit(f"the last change was {age_h:.1f} h ago; wait until 24 h (process rule 2.4)")
    k = max(1, round(0.15 * len(rows)))
    pick = random.Random(SEED + 1).sample(sorted(rows), k)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["first_sha256"], extrasaction="ignore")
        w.writeheader()
        for d in pick:
            a = OUT / batch / "answers" / f"{d}.json"
            w.writerow(dict(rows[d], list=f"{batch}_repeat", first_sha256=hashlib.sha256(a.read_bytes()).hexdigest()))
    print(f"{out.name}: {k} of {len(rows)} documents")


def blind_list(batch: str, n: int = 4) -> None:
    """Documents of the batch that the review tool shows without a proposal (unanchored measurement)."""
    out = OUT / f"{batch}_blind.csv"
    if out.exists():
        raise SystemExit(f"{out} exists: the list is fixed")
    if any((OUT / batch / "decisions").glob("*.json")):
        raise SystemExit("decisions exist already: the blind documents must be fixed before the review starts")
    with open(OUT / f"{batch}.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pick = random.Random(SEED + 2).sample(sorted(rows, key=lambda r: int(r["doc_id"])), n)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(dict(r, list=f"{batch}_blind") for r in pick)
    print(f"{out.name}: {[r['doc_id'] for r in pick]}")


def main() -> None:
    import sys

    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--repeat":
        return repeat(sys.argv[2])
    if len(sys.argv) > 2 and sys.argv[1] == "--blind":
        return blind_list(sys.argv[2])
    OUT.mkdir(parents=True, exist_ok=True)
    split = {z["body_key"]: z["rolle"] for z in read(AN / "synthese/split.csv")}
    dup = {z["doc_id"] for z in read(AN / "synthese/split_ausschluss_duplikate.csv")}
    insp = {z["doc_id"] for z in read(AN / "pdf/augenschein.csv")}
    groups = read(DATA / "iso/gruppen.csv")
    pool = read(DATA / "iso/pool.csv")
    final_parl = {r["body_key"] for r in groups if r["group"] == "7"}
    used = {r["doc_id"] for r in pool} | {r["doc_id"] for r in groups}
    stichprobe = read(SAMPLE_LIST)

    def ok(z: dict) -> bool:
        return (z["doc_id"] not in dup and z["doc_id"] not in insp and 0 < int(z["seiten"] or 0) <= 25
                and (SAMPLE_PDF / f"{z['doc_id']}.pdf").exists())

    # pilot: development groups 1 to 6
    rng = random.Random(SEED)
    dev = [dict(r, list="pilot", split=split.get(r["body_key"], "")) for r in groups if r["group"] in "123456"]
    with open(DATA / "iso/v4/native_sample.csv", newline="", encoding="utf-8") as f:
        blind = [r["doc_id"] for r in csv.DictReader(f)]
    chosen = [r for r in dev if r["doc_id"] in blind]
    rest = sorted([r for r in dev if r["doc_id"] not in blind], key=lambda r: int(r["doc_id"]))
    rng.shuffle(rest)

    def take(pred, n):
        for r in rest:
            if len([c for c in chosen if pred(c)]) >= n or len(chosen) >= PILOT:
                return
            if r not in chosen and pred(r):
                chosen.append(r)

    take(lambda r: r["sprache"] == "rm", 1)
    take(lambda r: r["sprache"] == "it", 3)
    take(lambda r: r["sprache"] == "fr", 4)
    take(lambda r: r["scan"] != "digital", 4)
    take(lambda r: True, PILOT)
    write("pilot.csv", chosen)

    # test: test parliaments (split role Gold)
    test = [dict(z, list="test", split="Gold", group="") for z in stichprobe
            if split.get(z["body_key"]) == "Gold" and z["doc_id"] not in used and ok(z)]
    write("test.csv", sorted(test, key=lambda r: int(r["doc_id"])))

    # extension: training and validation parliaments, not yet used, not a final parliament
    ext = [dict(z, list="extension", split=split.get(z["body_key"]), group="") for z in stichprobe
           if split.get(z["body_key"]) in ("Training", "Validierung") and z["doc_id"] not in used
           and z["body_key"] not in final_parl and ok(z)]
    write("extension.csv", sorted(ext, key=lambda r: int(r["doc_id"])))


if __name__ == "__main__":
    main()

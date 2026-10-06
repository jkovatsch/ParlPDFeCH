# SPDX-License-Identifier: Apache-2.0
"""Check that a list of documents or parliaments contains no test document (process rule 6).

Reads <data>/analyse/synthese/split.csv (split v2, E26). The value `Gold` marks the test set.
Input: one or more files (CSV with a column body_key or doc_id, or JSONL with body_key or doc_id),
or doc_ids / body_keys as arguments. doc_ids are resolved to parliaments through
<data>/analyse/dokumente/dokumente_merkmale.csv.gz. <data> is the data root (m03_iso_paths.DATA).

Exit code 0: no test document. Exit code 1: test documents found (listed).
Usage:  python3 src/m00_pruefe_testset.py data/iso/gruppen.csv
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA  # noqa: E402


def split_roles() -> dict[str, str]:
    with open(DATA / "analyse/synthese/split.csv", newline="", encoding="utf-8") as f:
        return {z["body_key"]: z["rolle"] for z in csv.DictReader(f)}


def doc_bodies(ids: set[str]) -> dict[str, str]:
    out = {}
    with gzip.open(DATA / "analyse/dokumente/dokumente_merkmale.csv.gz", "rt", newline="", encoding="utf-8") as f:
        for z in csv.DictReader(f):
            if z["id"] in ids:
                out[z["id"]] = z["body_key"]
    return out


def read_items(arg: str) -> list[dict]:
    p = Path(arg)
    if p.exists() and p.suffix == ".csv":
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if p.exists() and p.suffix == ".jsonl":
        with open(p, encoding="utf-8") as f:
            return [json.loads(x) for x in f if x.strip()]
    return [{"doc_id": arg}] if arg.isdigit() else [{"body_key": arg}]


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return 0
    roles = split_roles()
    items = [it for a in sys.argv[1:] for it in read_items(a)]
    ids = {str(it.get("doc_id") or it.get("id")) for it in items if not it.get("body_key")}
    bodies = doc_bodies(ids) if ids else {}
    found = []
    for it in items:
        b = it.get("body_key") or bodies.get(str(it.get("doc_id") or it.get("id")))
        if b is None:
            found.append((it, "unknown parliament"))
        elif roles.get(b) == "Gold":
            found.append((it, f"test parliament {b}"))
    for it, why in found:
        print(f"TEST SET: {why}: {it.get('doc_id') or it.get('id') or it.get('body_key')}")
    print(f"items: {len(items)}, test documents or unknown: {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

# SPDX-License-Identifier: Apache-2.0
"""Isolation at the level of E20: format, validation and measurement (steps 3.7 to 3.9).

SUPERSEDED: this file is the segmentation format and the measurement of E20 version 3.1. The gate 3a
values come from m03_iso_v4.py (measurement version 4.1, class-aware). This file stays, because the
current scripts use GROUPS, atom_ids() and the conversion of the version 3.1 references.

A segmentation (reference or output of a method) is a JSON file:

    {"doc_id": "...", "coder": "A",
     "furniture": ["B1.1", ...],          # atoms with the role page furniture
     "insert": ["B7.2", ...],             # atoms with the role insert
     "segments": [{"class": "head", "first": "B2.1", "last": "B5.3"}, ...],
     "notes": "..."}

The segments cover the main atoms (all atoms that are not furniture and not insert) in atom
order, without a gap and without an overlap. "first" and "last" are the first and the last main
atom of a segment. Classes: see CLASSES (E20, chapter 4).

Measured values (E20, chapter 7): boundary F1 (exact position in the sequence of main atoms of
the reference), omission rate, document exact rate, furniture recall.

Usage:
  python3 src/m03_iso_mass.py validate FILE...         # examine segmentation files
  python3 src/m03_iso_mass.py compare DIR_REF DIR_HYP [--groups 1,2,3,4]
  python3 src/m03_iso_mass.py diff DIR_A DIR_B DOC_ID     # disagreements of two segmentations
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, iso_path  # noqa: E402

ATOMS = DATA / "iso/atome"
GROUPS = DATA / "iso/gruppen.csv"

CLASSES = ("title", "short_title", "submitted", "reasoning", "response", "recommendation", "summary",
           "head", "closing", "distribution", "other_text")


def atom_ids(doc_id: str) -> list[str]:
    d = json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))
    return [a["id"] for a in d["atome"]]


def atom_texts(doc_id: str) -> dict[str, str]:
    d = json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))
    return {a["id"]: a["text"] for a in d["atome"]}


def validate(seg: dict, ids: list[str]) -> list[str]:
    """Errors of a segmentation (empty list = valid)."""
    err = []
    known = set(ids)
    furn, ins = set(seg.get("furniture", [])), set(seg.get("insert", []))
    for a in furn | ins:
        if a not in known:
            err.append(f"unknown atom {a}")
    if furn & ins:
        err.append(f"atoms both furniture and insert: {sorted(furn & ins)[:5]}")
    main = [a for a in ids if a not in furn and a not in ins]
    pos = {a: i for i, a in enumerate(main)}
    expect = 0
    for k, s in enumerate(seg.get("segments", [])):
        if s.get("class") not in CLASSES:
            err.append(f"segment {k}: unknown class {s.get('class')}")
        f, l = s.get("first"), s.get("last")
        if f not in pos or l not in pos:
            err.append(f"segment {k}: first/last not a main atom ({f}, {l})")
            continue
        if pos[f] != expect:
            err.append(f"segment {k}: starts at {f}, expected {main[expect] if expect < len(main) else 'end'}")
        if pos[l] < pos[f]:
            err.append(f"segment {k}: last before first")
        expect = pos[l] + 1
    if expect != len(main) and not err:
        err.append(f"main atoms after the last segment: {main[expect] if expect < len(main) else ''}")
    for k in range(1, len(seg.get("segments", []))):
        if seg["segments"][k]["class"] == seg["segments"][k - 1]["class"]:
            err.append(f"segments {k - 1} and {k} have the same class (rule 8)")
    return err


def labels(seg: dict, ids: list[str]) -> dict[str, tuple[str, int]]:
    """atom -> (role or class, segment index). Roles: furniture, insert."""
    furn, ins = set(seg.get("furniture", [])), set(seg.get("insert", []))
    main = [a for a in ids if a not in furn and a not in ins]
    pos = {a: i for i, a in enumerate(main)}
    out = {a: ("furniture", -1) for a in furn}
    out.update({a: ("insert", -1) for a in ins})
    for k, s in enumerate(seg["segments"]):
        for a in main[pos[s["first"]]: pos[s["last"]] + 1]:
            out[a] = (s["class"], k)
    return out


def boundaries_on(seg: dict, ids: list[str], order: list[str]) -> set[int]:
    """Boundaries of seg, as positions in the sequence `order` (main atoms of the reference):
    position i means: a new segment starts at order[i]. Atoms of `order` that seg does not
    treat as main atoms take the segment of the previous main atom of seg."""
    lab = labels(seg, ids)
    out, prev = set(), None
    for i, a in enumerate(order):
        cls, k = lab.get(a, ("?", -1))
        if cls in ("furniture", "insert"):
            k = prev
        if i > 0 and k != prev:
            out.add(i)
        prev = k
    return out


def compare(ref: dict, hyp: dict, ids: list[str]) -> dict:
    furn_r, ins_r = set(ref.get("furniture", [])), set(ref.get("insert", []))
    order = [a for a in ids if a not in furn_r and a not in ins_r]
    br = boundaries_on(ref, ids, order)
    bh = boundaries_on(hyp, ids, order)
    content = [a for a in ids if a not in furn_r]
    furn_h = set(hyp.get("furniture", []))
    omitted = [a for a in content if a in furn_h]
    return {"tp": len(br & bh), "n_ref": len(br), "n_hyp": len(bh), "content": len(content),
            "omitted": len(omitted), "furniture_ref": len(furn_r),
            "furniture_found": len(furn_r & furn_h), "exact": int(br == bh and not omitted),
            "missed": sorted(order[i] for i in br - bh), "extra": sorted(order[i] for i in bh - br),
            "omitted_atoms": omitted}


def summarize(rows: list[dict]) -> dict:
    tp = sum(r["tp"] for r in rows)
    nr = sum(r["n_ref"] for r in rows)
    nh = sum(r["n_hyp"] for r in rows)
    p = tp / nh if nh else 1.0
    r = tp / nr if nr else 1.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    content = sum(x["content"] for x in rows)
    fr = sum(x["furniture_ref"] for x in rows)
    return {"documents": len(rows), "precision": round(p, 4), "recall": round(r, 4), "boundary_f1": round(f1, 4),
            "omission_rate": round(sum(x["omitted"] for x in rows) / content, 5) if content else 0.0,
            "document_exact_rate": round(sum(x["exact"] for x in rows) / len(rows), 4) if rows else 0.0,
            "furniture_recall": round(sum(x["furniture_found"] for x in rows) / fr, 4) if fr else 1.0}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def groups() -> dict[str, dict]:
    with open(GROUPS, newline="", encoding="utf-8") as f:
        return {r["doc_id"]: r for r in csv.DictReader(f)}


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "validate":
        bad = 0
        for p in sys.argv[2:]:
            seg = load(Path(p))
            e = validate(seg, atom_ids(seg["doc_id"]))
            if e:
                bad += 1
                print(f"{p}: {len(e)} errors: {e[:4]}")
        print(f"files {len(sys.argv) - 2}, invalid {bad}")
        return 1 if bad else 0
    if sys.argv[1] == "compare":
        dref, dhyp = Path(sys.argv[2]), Path(sys.argv[3])
        sel = None
        if "--groups" in sys.argv:
            sel = set(sys.argv[sys.argv.index("--groups") + 1].split(","))
        g = groups()
        per_group: dict[str, list] = {}
        for doc_id, r in sorted(g.items(), key=lambda x: (x[1]["group"], x[0])):
            if sel and r["group"] not in sel:
                continue
            pr, ph = dref / f"{doc_id}.json", dhyp / f"{doc_id}.json"
            if not pr.exists() or not ph.exists():
                print(f"missing {doc_id}")
                continue
            res = compare(load(pr), load(ph), atom_ids(doc_id))
            per_group.setdefault(r["group"], []).append(res)
        allrows = [x for v in per_group.values() for x in v]
        for k in sorted(per_group):
            print(f"group {k}: {summarize(per_group[k])}")
        print(f"all: {summarize(allrows)}")
        return 0
    if sys.argv[1] == "diff":
        da, db, doc_id = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
        ids = atom_ids(doc_id)
        a, b = load(da / f"{doc_id}.json"), load(db / f"{doc_id}.json")
        la, lb = labels(a, ids), labels(b, ids)
        res = compare(a, b, ids)
        print(f"boundaries only in {da.name}: {res['missed']}")
        print(f"boundaries only in {db.name}: {res['extra']}")
        diff_roles = [x for x in ids if (la[x][0] in ("furniture", "insert")) != (lb[x][0] in ("furniture", "insert"))
                      or (la[x][0] in ("furniture", "insert") and la[x][0] != lb[x][0])]
        print(f"atoms with another role: {diff_roles}")
        diff_cls = [x for x in ids if la[x][0] != lb[x][0] and x not in diff_roles]
        print(f"atoms with another class: {diff_cls}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

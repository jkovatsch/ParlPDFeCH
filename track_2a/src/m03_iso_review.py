# SPDX-License-Identifier: Apache-2.0
"""Step 3.7: review of the version 4 references and blind native coding (E20 version 4).

Commands:
  sample    select the documents for the blind native coding (seed SEED): one document of each
            group 1 to 5 and EXTRA more documents of these groups; writes <data>/iso/v4/native_sample.csv
  report    agreements: review coders R1 and R2 (review agreement), converted reference against the
            adjudicated review (change by the review), blind native coding N against the reviewed
            reference (blind agreement)

The coders work only with `m03_iso_v4.py` (view, spans, write4, validate4). The blind coder never
opens a reference directory (<data>/iso/ref*, <data>/iso/v4/ref*, <data>/iso/v4/review*, pool_ref).
All coders were AI agents (Claude Opus 5.5).

Usage:  python3 src/m03_iso_review.py sample
        python3 src/m03_iso_review.py report
        python3 src/m03_iso_review.py consensus   (proposal for the human review of the gold set: blind X and Y
                                                   where they agree, else ref41; README.md, chapter "Gold set")
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_mass as ms  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
from m03_iso_paths import DATA, rel  # noqa: E402

V4 = DATA / "iso/v4"
SEED = 20261006
EXTRA = 2


def sample() -> None:
    out = V4 / "native_sample.csv"
    if out.exists():
        raise SystemExit(f"{out} exists: the sample is fixed")
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["group"] in ("1", "2", "3", "4", "5")]
    rng = random.Random(SEED)
    chosen = []
    for g in ("1", "2", "3", "4", "5"):
        docs = sorted([r for r in rows if r["group"] == g], key=lambda r: int(r["doc_id"]))
        chosen.append(docs[rng.randrange(len(docs))])
    rest = sorted([r for r in rows if r not in chosen], key=lambda r: int(r["doc_id"]))
    chosen += rng.sample(rest, EXTRA)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "group", "sprache", "dokumentrolle"])
        w.writeheader()
        w.writerows({k: r[k] for k in ("doc_id", "group", "sprache", "dokumentrolle")} for r in chosen)
    print(f"{len(chosen)} documents -> {out}: {[(r['group'], r['doc_id']) for r in chosen]}")


def pair(a: Path, b: Path, docs: list[str]) -> dict:
    r1 = v4.compare_docs(a, b, docs)
    r2 = v4.compare_docs(b, a, docs)
    return {"documents": r1["documents"], "labelled_f1_mean": round((r1["labelled_f1"] + r2["labelled_f1"]) / 2, 4),
            "text_class_error": r1["text_class_error"], "text_omission_b": r1["text_omission"],
            "text_intrusion_b": r1["text_intrusion"], "document_exact": r1["document_exact_rate"]}


def report() -> None:
    groups = ["1", "2", "3", "4", "5", "6"]
    docs = v4.group_docs(groups, False)
    have = lambda d, *dirs: all((V4 / x / f"{d}.json").exists() for x in dirs)  # noqa: E731
    rev = [d for d in docs if have(d, "review_R1", "review_R2", "ref_rev")]
    print("review agreement R1/R2:", pair(V4 / "review_R1", V4 / "review_R2", rev))
    print("converted ref / reviewed ref:", pair(V4 / "ref", V4 / "ref_rev", rev))
    with open(V4 / "native_sample.csv", newline="", encoding="utf-8") as f:
        nat = [r["doc_id"] for r in csv.DictReader(f) if have(r["doc_id"], "native_N", "ref_rev")]
    print("blind native N / reviewed ref:", pair(V4 / "ref_rev", V4 / "native_N", nat))
    print("blind native N / converted ref:", pair(V4 / "ref", V4 / "native_N", nat))


def consensus() -> None:
    """Proposal for the human review: the blind codings X and Y where they agree; else ref41 (marked as disputed in the tool)."""
    out = V4 / "consensus_XY"
    out.mkdir(exist_ok=True)
    n = same = 0
    for p in sorted((V4 / "blind_X").glob("*.json")):
        d = p.stem
        ids = [a["id"] for a in v4.atoms_of(d)]
        x = v4.load_answers(p, d, ids)
        y = v4.load_answers(V4 / "blind_Y" / f"{d}.json", d, ids)
        r = v4.load_answers(V4 / "ref41" / f"{d}.json", d, ids)
        ans = [a if a == b else c for a, b, c in zip(x, y, r)]
        v4.write(out, d, ans, "consensus X/Y (else ref41)", f"{rel(V4 / 'blind_X')}, blind_Y, ref41")
        err = v4.validate4(out / f"{d}.json")
        if err:
            raise SystemExit(f"{d}: {err[:3]}")
        n += 1
        same += x == y
    print(f"{n} documents -> {out}; X equal to Y in {same} documents")


if __name__ == "__main__":
    COMMANDS = {"sample": sample, "report": report, "consensus": consensus}
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if {"-h", "--help"} & set(sys.argv[1:]) else 2)
    COMMANDS[sys.argv[1]]()

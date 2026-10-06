# SPDX-License-Identifier: Apache-2.0
"""Gate 3a values of one method (gate 3a criteria, version 3): pooled, each group, scans, selective.

The technical report (track_2a/technical_report.md, chapter 5.3) gives the criteria and their limits.

Input: the answer files of the method (<data>/iso/v4/hyp_<name>), the readout files with the log
probabilities (for the confidence of G3a.11) and the reference directory.
Confidence of a document: the lowest margin between the best and the second answer (log
probability) over its atoms that are not fixed. Selective prediction: the documents sorted by
confidence; for each coverage (100, 90, 80, 70, 50 %) the document exact rate of the accepted
documents.
Agreement gap: the labelled boundary F1 of the method minus two agreement values of AI agents
(Claude Opus 5.5), not of humans: --agree-blind (default 0.944, blind coding of 7 documents against
the reference) and --agree-final (default 0.917, the two coders of the final group).

Usage:  python3 src/m04_iso_report.py --hyp data/iso/v4/hyp_oof_a1 --readout data/iso/pod/foldY_a1,data/iso/pod/foldX_a1 \\
            --ref data/iso/v4/ref41 --groups 1,2,3,4,5
        (folder arguments are relative to the working folder; here: track_2a with the default data root)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_mass as ms  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
from m03_iso_paths import DATA  # noqa: E402

KEYS = ("documents", "labelled_f1", "labelled_f1_lower", "text_omission", "documents_with_omission",
        "text_intrusion", "text_class_error", "document_exact_rate", "boundaries_ref", "boundaries_hyp")


def confidence(readout_dirs: list[str]) -> dict[str, float]:
    out = {}
    for d in readout_dirs:
        for p in Path(d).glob("*.json"):
            if p.name in ("run.json", "config.json"):
                continue
            x = json.loads(p.read_text())
            fixed = set(x.get("fixed", []))
            m = math.inf
            for i, row in enumerate(x["logprobs"]):
                if i in fixed:
                    continue
                a, b = sorted(row, reverse=True)[:2]
                m = min(m, a - b)
            out[x["doc_id"]] = m
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hyp", required=True)
    ap.add_argument("--readout", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--groups", required=True)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--agree-blind", type=float, default=0.944,
                    help="agreement of AI agents: blind coding against the reference (labelled boundary F1)")
    ap.add_argument("--agree-final", type=float, default=0.917,
                    help="agreement of AI agents: the two coders of the final group (labelled boundary F1)")
    args = ap.parse_args()
    groups = args.groups.split(",")
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["group"] in groups]
    with open(DATA / "iso/triage.csv", newline="", encoding="utf-8") as f:
        passed = {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}
    v4.group_docs(groups, args.final)
    rows = [r for r in rows if r["doc_id"] in passed]
    hyp, ref = Path(args.hyp), Path(args.ref)
    res = {"method": args.hyp, "reference": args.ref, "groups": groups, "triage_left_out": []}
    docs = [r["doc_id"] for r in rows]
    res["pooled"] = {k: v for k, v in v4.compare_docs(ref, hyp, docs).items() if k in KEYS}
    res["groups_each"] = {g: {k: v for k, v in v4.compare_docs(ref, hyp, [r["doc_id"] for r in rows if r["group"] == g]).items()
                              if k in ("documents", "labelled_f1", "text_omission", "document_exact_rate")}
                          for g in groups}
    scans = [r["doc_id"] for r in rows if r["scan"] != "digital"]
    res["scans"] = {k: v for k, v in v4.compare_docs(ref, hyp, scans).items() if k in KEYS} if scans else None
    conf = confidence(args.readout.split(","))
    order = sorted(docs, key=lambda d: -conf.get(d, -math.inf))
    sel = {}
    for cov in (1.0, 0.9, 0.8, 0.7, 0.5):
        k = max(1, round(cov * len(order)))
        r = v4.compare_docs(ref, hyp, order[:k])
        sel[f"{int(cov * 100)}%"] = {"documents": k, "document_exact_rate": r["document_exact_rate"],
                                    "labelled_f1": r["labelled_f1"], "text_omission": r["text_omission"]}
    res["selective"] = sel
    pc = res["pooled"]
    res["agreement_gap"] = {f"method_f1_minus_blind_{args.agree_blind}": round(pc["labelled_f1"] - args.agree_blind, 4),
                            f"method_f1_minus_g7_native_{args.agree_final}": round(pc["labelled_f1"] - args.agree_final, 4)}
    c = v4.compare_docs(ref, hyp, docs)["counts"]
    res["boundary_errors"] = {"false": c["bh"] - c["good"], "missed": c["br"] - c["good"]}
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

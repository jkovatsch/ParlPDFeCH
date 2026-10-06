# SPDX-License-Identifier: Apache-2.0
"""Human gold set (E32): report of a review batch (pilot, test, or a repeat batch).

For each document with the status "fertig": active minutes, wall minutes (first opening to
"fertig"), atoms changed against the AI proposal, answers to the 4 questions, notes.

Agreement of the AI codings with the answers of the human annotator (Jonathan; measurement 4.1 of
`m03_iso_v4.py`, the answers of the annotator as the reference), in two parts:
  anchored    documents where the tool showed the proposal. The proposal of the pilot comes from the
              blind codings X and Y, and the tool shows the other codings only at disputed atoms, so
              ALL rows of this part are anchored; they show how often Jonathan changed the proposal.
  unanchored  documents without a proposal (<data>/gold/<batch>_blind.csv): Jonathan coded them from the
              start. Only this part measures the accuracy of the AI codings without the anchor.
Checks: the SHA-256 of each proposal file must be equal to the value in the decision (else the row
is not comparable and the report lists it); for a repeat batch, the SHA-256 of each first answer
file must be equal to the value in the repeat list.

For the test batch the developer of a method sees only these numbers (process rule 6).
Output keys: anchored_agreement_with_annotator, unanchored_ai_accuracy, annotator_first_against_second.

Usage:  python3 src/m03_gold_report.py pilot
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_gold_review as gr  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

KEYS = ("documents", "labelled_f1", "labelled_f1_lower", "text_omission", "text_intrusion", "text_class_error",
        "document_exact_rate", "boundaries_ref", "boundaries_hyp")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compare(gold: Path, d: Path, docs: list[str]) -> dict | None:
    have = [x for x in docs if (d / f"{x}.json").exists()]
    if not have:
        return None
    r = v4.compare_docs(gold, d, have)
    eq = tot = 0
    for x in have:
        a = json.loads((gold / f"{x}.json").read_text())["answers"]
        b = json.loads((d / f"{x}.json").read_text())["answers"]
        eq += sum(i == j for i, j in zip(a, b))
        tot += len(a)
    return {**{k: r[k] for k in KEYS}, "atom_agreement": round(eq / tot, 4)}


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    batch = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    store = gr.Store(batch)
    cfg = gr.BATCHES[batch]
    done, rows, mismatch = [], [], []
    for d in store.ids:
        x = store.decision(d)
        if not x or x.get("status") != "fertig":
            continue
        done.append(d)
        wall = None
        if x.get("first_opened") and x.get("finished"):
            wall = (datetime.fromisoformat(x["finished"][:19]) - datetime.fromisoformat(x["first_opened"][:19])).total_seconds() / 60
        if x.get("proposal_sha256"):
            p = cfg["proposal"] / f"{d}.json"
            if not p.exists() or sha(p) != x["proposal_sha256"]:
                mismatch.append(d)
        rows.append({"doc_id": d, "blind": x.get("blind", False), "active_min": round(x.get("active_seconds", 0) / 60, 1),
                     "wall_min": round(wall, 1) if wall is not None else None, "changed": x.get("changed_vs_proposal"),
                     "questions": x.get("questions"), "note": bool(x.get("notes")), "e20_sha256": x.get("e20_sha256", "")[:12]})
    out = {"batch": batch, "documents_done": len(done), "documents_total": len(store.ids), "documents": rows}
    if mismatch:
        out["proposal_changed_after_review"] = mismatch
    if done:
        for part, sel in (("with_proposal", [r for r in rows if not r["blind"]]), ("without_proposal", [r for r in rows if r["blind"]])):
            act = [r["active_min"] for r in sel]
            if act:
                out[f"active_minutes_{part}"] = {"documents": len(act), "mean": round(statistics.mean(act), 1),
                                                 "median": round(statistics.median(act), 1), "max": max(act)}
        walls = [r["wall_min"] for r in rows if r["wall_min"] is not None and r["wall_min"] < 240]
        if walls:
            out["wall_minutes_median"] = round(statistics.median(walls), 1)
        m = out.get("active_minutes_with_proposal", {}).get("mean")
        if m is not None:
            out["hours_at_mean_with_proposal"] = {n: round(n * m / 60, 1) for n in (100, 200, 400)}
        q = {}
        for r in rows:
            for k, v in (r["questions"] or {}).items():
                q.setdefault(k, {}).setdefault(v, 0)
                q[k][v] += 1
        out["questions"] = q
        gold = store.ans_dir
        anchored = [r["doc_id"] for r in rows if not r["blind"] and r["doc_id"] not in mismatch]
        blind = [r["doc_id"] for r in rows if r["blind"]]
        sources = [("proposal", cfg["proposal"]), *cfg["others"].items()]
        out["anchored_agreement_with_annotator"] = {n: c for n, d in sources if (c := compare(gold, d, anchored))}
        out["unanchored_ai_accuracy"] = {n: c for n, d in sources if (c := compare(gold, d, blind))}
        if batch.endswith("_repeat"):
            base = batch[: -len("_repeat")]
            first = gr.GOLD / base / "answers"
            with open(cfg["list"], newline="", encoding="utf-8") as f:
                want = {r["doc_id"]: r.get("first_sha256") for r in csv.DictReader(f)}
            changed = [x for x in done if (first / f"{x}.json").exists() and want.get(x) and sha(first / f"{x}.json") != want[x]]
            have = [x for x in done if (first / f"{x}.json").exists() and x not in changed]
            if changed:
                out["first_answers_changed_after_selection"] = changed
            if have:
                r1 = v4.compare_docs(first, gold, have)
                r2 = v4.compare_docs(gold, first, have)
                out["annotator_first_against_second"] = {
                    "documents": len(have), "labelled_f1_mean": round((r1["labelled_f1"] + r2["labelled_f1"]) / 2, 4),
                    "text_class_error": r1["text_class_error"], "document_exact_rate": r1["document_exact_rate"]}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

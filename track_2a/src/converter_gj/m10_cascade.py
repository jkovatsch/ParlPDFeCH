# SPDX-License-Identifier: Apache-2.0
"""Cascade of gate GJ: the decisions file (interface 7) of each document, in the floor mode and in the cascade mode.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream D of
workflow <id>, for the AI agent; the cascade mode: stream D of workflow <id> (wave 3).
Phase 4 (modeling) and phase 6 (deployment), gate GJ (OPEN). Status: EXCEPTION (process rule 10), NOT RELEASED.
Criteria: `crisp-dm/04-modeling/gate-jev-cascade-criteria.md`, chapters 4 item 7, 7.1 to 7.4, 8.5 to 8.7 and 10.
Plan: `crisp-dm/00-cross-cutting/plan-full-conversion.md`, chapters 4 and 5.2 item 6.

1 Modes
  floor    the floor converter F1 (criteria 7.4): no Apertus state. Inputs: the rule file daten/gj/rules/<doc>.json
           (src/m10_rules.py) and the calibration file of `src/m10_calibrate.py floor-fit`
           (daten/gj/calibration/floor_v1.json, key floor_lookup). Function floor_decisions().
  cascade  D1, B1 and B2 with Apertus states (criteria 7.1 to 7.3) through src/m10_pipeline.py: the function
           cascade_decisions() of this file calls decide() of src/m10_pipeline.py (assert_apply_allowed() and
           cascade_decisions() of src/m10_design.py with the frozen design; a document without states gets the
           floor decisions with the value status unsure, criteria chapter 4 item 7). The command with --mode
           cascade is cascade_command() of src/m10_pipeline.py (chapter 4 of its docstring).

2 Floor decisions of one document (interface 7)
  blocks      each Docling block gets its rule option and its rule tier. p = the Jeffreys posterior mean of its
              (tier, option) pair on dev (backoff for a pair without a dev block: chapter 4 of m10_calibrate.py).
              The 6-option distribution: p for the rule option, 1 - p for the other 5 options in proportion to
              the dev confusion row of the pair plus 1 (add-one), then the clip to [0.005, 0.995] without a new sum
              (P7) and 4 decimals. source rule; certain_pair true only for a certain pair of the GJ.20 table.
  document    D1 from the S1 rule role (map P3) with p = the Jeffreys posterior mean of its S1 rule id; the other
              3 options as for a block. A document with the S1 rule id R1 (needs_apertus) uses the provisional rule
              role; its calibration record has no threshold a, so the writer gives it the value status unsure.
  boundaries  the switch boundaries of the rule block path (criteria 2.5): after_block = the block directly before
              the first block of the new family; p = the Jeffreys posterior mean of the switch-boundary precision
              of the rules on dev; source rule.
  r2          null in floor mode.
  in_sample   true if the document is in the fit set of the calibration file (dev), else false.
  The writer (src/m10_writer.py) gives the value status from the threshold a of each calibration record.

3 Command (from the project folder)
  uv run --offline --frozen --no-sync python src/m10_cascade.py --mode floor --set dev [--doc ID ...]
      [--calibrations daten/gj/calibration/floor_v1.json] [--out daten/gj/decisions_floor] [--continue-missing]
  Output: daten/gj/decisions_floor/<doc>.json and the run record daten/gj/calibration/runs/cascade_floor_<set>.json
  (the SHA-256 of this file before the first value, the inputs, each output, the time of each document).
  Process rule 6: src/m10_guard.py allows each document for the split of the set before its rule file is read.
  The cascade reads no label file and no model output. validation and group7: only the one held-out run
  (criteria 10.3): the freeze file must exist and name the SHA-256 of this file, of src/m10_calibrate.py and of
  the calibration file. An existing output or run record stops the run. After a technical stop, use
  --continue-missing with a new --label: the run then makes only the documents without an output.
  uv run --offline --frozen --no-sync python src/m10_cascade.py --mode cascade --set dev|validation|group7
      [--doc ID ...] --states DIR [DIR ...] --entry-d1 yes|no --entry-b12 yes|no [--design daten/gj/design]
      [--freeze daten/gj/design_freeze.json] [--r2 FILE] [--r2-calibrations FILE] [--out daten/gj/decisions]
      [--label NAME] [--continue-missing]
  The cascade mode needs the design freeze file (src/m10_pipeline.py, chapter 4 of its docstring).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_calibrate as cal  # noqa: E402  (calibration library, floor lookup, guards of the held-out runs)
import m10_guard as guard  # noqa: E402  (split guard of process rule 6, stream B)

VERSION = "m10-cascade-1"
SCRIPT = Path(__file__).resolve()
ROOT = cal.ROOT
GJ = cal.GJ
OUT_DIR = GJ / "decisions_floor"
MODES = ("floor", "cascade")
SOURCES = ("rule", "apertus_head", "code")


# ------------------------------------------------------------------ shared output (both modes)
def decisions_record(doc_id: str, mode: str, d1: dict, blocks: list[dict], boundaries: list[dict], r2: dict | None,
                     extra: dict | None = None) -> dict:
    """Interface 7. extra: keys that the writer does not read (provenance of the decisions)."""
    rec = {"doc_id": str(doc_id), "mode": mode, "document": {"d1": d1}, "blocks": blocks, "boundaries": boundaries,
           "r2": r2}
    return rec | (extra or {})


def check_decisions(dec: dict, rules: dict) -> list[str]:
    """Structure of interface 7 and agreement with the blocks of the rule file (a subset of the checks of
    src/m10_writer.py, without the block file)."""
    bad = []
    if dec.get("mode") not in MODES:
        bad.append("mode is not floor or cascade")
    d1 = dec["document"]["d1"]
    if d1.get("option") not in cal.D1_OPTIONS or set(d1.get("probs") or {}) != set(cal.D1_OPTIONS):
        bad.append("d1: option or probs not A to D")
    if d1.get("source") not in SOURCES:
        bad.append("d1: source not rule, apertus_head or code")
    if [b["block"] for b in dec["blocks"]] != [b["block"] for b in rules["blocks"]]:
        bad.append("the blocks are not the blocks of the rule file in reading order")
    for b in dec["blocks"]:
        if b.get("option") not in cal.OPTIONS or set(b.get("probs") or {}) != set(cal.OPTIONS):
            bad.append(f"{b.get('block')}: option or probs not the 6 options")
        if b.get("source") not in SOURCES:
            bad.append(f"{b.get('block')}: source")
    probs = [p for b in dec["blocks"] for p in b["probs"].values()] + list(d1["probs"].values()) + \
        [x["p"] for x in dec.get("boundaries") or []]
    if any(not cal.P_MIN <= p <= cal.P_MAX for p in probs):
        bad.append("a probability is outside [0.005, 0.995]")
    ids = [b["block"] for b in dec["blocks"]]
    for x in dec.get("boundaries") or []:
        if x.get("after_block") not in ids[:-1] or x.get("kind") != "switch":
            bad.append(f"boundary {x.get('after_block')}: not a block before the last block, or kind not switch")
    if len({x["after_block"] for x in dec.get("boundaries") or []}) != len(dec.get("boundaries") or []):
        bad.append("two boundaries after the same block")
    if dec.get("mode") == "floor" and dec.get("r2") is not None:
        bad.append("floor mode has no r2")
    return bad


# ------------------------------------------------------------------ floor mode
def floor_decisions(rules: dict, lookup: cal.FloorLookup, in_sample: bool, cal_info: dict | None) -> dict:
    """The floor decisions of one document from its rule file (chapter 2)."""
    blocks = []
    for b in rules["blocks"]:
        e = lookup.block(b["tier"], b["option"])
        blocks.append({"block": b["block"], "option": b["option"],
                       "probs": cal.spread(b["option"], e["p"], e["weights"], cal.OPTIONS), "source": "rule",
                       "tier": b["tier"], "calibration": e["calibration"], "in_sample": bool(in_sample),
                       "certain_pair": bool(e["certain"] and e["level"] == "pair"), "lookup_level": e["level"]})
    opt, role, rid = cal.d1_of_rule(rules)
    s1 = rules["document"]["s1"]
    needs = bool(rules["document"]["d1"]["needs_apertus"])
    if needs != (rid == cal.NEEDS_APERTUS_ID) or (s1["source"] == "rule_provisional") != needs:
        raise SystemExit(f"{rules['doc_id']}: needs_apertus, the S1 rule id and the source of the combined role "
                         f"do not agree")
    e = lookup.d1(rid)
    d1 = {"option": opt, "probs": cal.spread(opt, e["p"], e["weights"], cal.D1_OPTIONS), "source": "rule",
          "rule_id": rid, "calibration": e["calibration"], "in_sample": bool(in_sample), "s1_rule_role": role,
          "role_source": "rule_provisional" if needs else "rule", "needs_apertus": needs, "lookup_level": e["level"]}
    sw = lookup.switch()
    options = [b["option"] for b in rules["blocks"]]
    boundaries = [{"after_block": rules["blocks"][i]["block"], "kind": "switch", "p": cal.as_written(sw["p"]),
                   "calibration": sw["calibration"], "source": "rule"} for i in cal.switch_gaps(options)]
    extra = {"schema": "parlpdfech-gj-decisions/1", "status": cal.STATUS, "split": rules.get("split"),
             "cascade": {"path": cal.rel(SCRIPT), "sha256": cal.sha256(SCRIPT), "version": VERSION}}
    if cal_info:
        extra["calibration"] = cal_info
    return decisions_record(rules["doc_id"], "floor", d1, blocks, boundaries, None, extra)


def cascade_decisions(doc_id, frozen, states_dir, entry_d1: bool, entry_b12: bool, r2=None, **kwargs) -> dict:
    """Mode cascade (criteria 7.1 to 7.3 and 4 item 7): decide() of src/m10_pipeline.py with the mode cascade.
    frozen: load_design() of src/m10_pipeline.py. The output passes check_decisions()."""
    import m10_pipeline as pipeline  # late import: src/m10_pipeline.py imports this file
    return pipeline.decide(doc_id, "cascade", frozen, states_dir, entry_d1, entry_b12, r2, **kwargs)


# ------------------------------------------------------------------ command
def run(args) -> int:
    if args.mode == "cascade":
        import m10_pipeline as pipeline  # late import: src/m10_pipeline.py imports this file
        return pipeline.cascade_command(args)
    if args.states or args.entry_d1 or args.entry_b12 or args.r2 or args.r2_calibrations:
        print("--states, --entry-d1, --entry-b12, --r2 and --r2-calibrations are only for --mode cascade",
              file=sys.stderr)
        return 2
    args.out = args.out or str(OUT_DIR)
    cal_file = Path(args.calibrations).resolve()
    out_dir = Path(args.out).resolve()
    if not out_dir.is_relative_to(GJ.resolve()):
        raise SystemExit("the output folder must be inside daten/gj")
    held = None
    if args.set in ("validation", "group7"):
        held = cal.freeze_check(args.set, cal_file)
    run_path = cal.CAL_RUNS / f"cascade_floor_{args.set}{'_' + args.label if args.label else ''}.json"
    if held and run_path.exists():
        raise SystemExit(f"one-run rule (criteria 10.3): {cal.rel(run_path)} exists; a continuation needs --label")
    t_all = time.perf_counter()
    ids = cal.load_set(args.set, ("dev", "validation", "group7"))
    if args.doc:
        want = [str(d) for d in args.doc]
        if not set(want) <= set(ids):
            raise SystemExit(f"--doc: documents outside the set {args.set}")
        ids = sorted(want, key=int)
    existing = [d for d in ids if (out_dir / f"{d}.json").exists()]
    if held and existing and not args.continue_missing:
        raise SystemExit(f"one-run rule (criteria 10.3): {len(existing)} outputs exist; only --continue-missing")
    if held and args.continue_missing:
        ids = [d for d in ids if d not in existing]
    scripts = [SCRIPT, cal.SCRIPT, Path(guard.__file__).resolve()]
    rec = cal.start_run_record(run_path, f"floor converter F1 (mode floor) on the set {args.set}", scripts)
    rec["documents_with_an_output_before_the_run"] = len(existing)
    calib = cal.read_json(cal_file)
    lookup = cal.FloorLookup(calib)
    cal_info = {"path": cal.rel(cal_file), "sha256": cal.sha256(cal_file), "version": calib.get("version")}
    fit_docs = set(cal.read_json(ROOT / calib["fit_set"]["path"])["documents"])
    if cal.sha256(ROOT / calib["fit_set"]["path"]) != calib["fit_set"]["sha256"]:
        raise SystemExit("the fit set file of the calibration file has another SHA-256")
    docs = cal.load_documents(ids, with_labels=False)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs, seconds, counts = {}, {}, {"blocks": 0, "boundaries": 0, "needs_apertus": 0, "certain_pair_blocks": 0,
                                        "backoff_blocks": 0}
    for d in ids:
        t0 = time.perf_counter()
        r = docs[d]["rules"]
        dec = floor_decisions(r, lookup, d in fit_docs, cal_info)
        bad = check_decisions(dec, r)
        if bad:
            raise SystemExit(f"{d}: decisions check failed: {bad[:5]}")
        p = out_dir / f"{d}.json"
        cal.write_json(p, dec)
        seconds[d] = round(time.perf_counter() - t0, 4)
        outputs[cal.rel(p)] = cal.sha256(p)
        counts["blocks"] += len(dec["blocks"])
        counts["boundaries"] += len(dec["boundaries"])
        counts["needs_apertus"] += dec["document"]["d1"]["needs_apertus"]
        counts["certain_pair_blocks"] += sum(b["certain_pair"] for b in dec["blocks"])
        counts["backoff_blocks"] += sum(b["lookup_level"] != "pair" for b in dec["blocks"])
    sv = list(seconds.values())
    rec.update({"mode": "floor", "set": args.set, "held_out_run": held, "documents": len(ids),
                "inputs": {cal.rel(cal_file): cal.sha256(cal_file), cal.rel(cal.RULES_RUN): cal.sha256(cal.RULES_RUN),
                           cal.rel(cal.SETS_FILE): cal.sha256(cal.SETS_FILE),
                           "rule_files_sha256_canonical": hashlib.sha256(json.dumps(
                               {f"daten/gj/rules/{d}.json": cal.sha256(cal.RULES_DIR / f"{d}.json") for d in ids},
                               sort_keys=True).encode()).hexdigest()},
                "outputs": outputs, "counts": counts,
                "seconds_per_document": {"mean": round(statistics.mean(sv), 4) if sv else None,
                                         "median": round(statistics.median(sv), 4) if sv else None,
                                         "max": max(sv) if sv else None, "each": seconds},
                "seconds_total": round(time.perf_counter() - t_all, 2),
                "limits": ["The floor reads no label file and no model output.",
                           "The probabilities are dev in-sample values of the rules (criteria 8.7 item 5)."]})
    cal.finish_run_record(run_path, rec, scripts)
    print(json.dumps({"set": args.set, "documents": len(ids), "counts": counts,
                      "seconds_per_document": {k: v for k, v in rec["seconds_per_document"].items() if k != "each"},
                      "out": cal.rel(out_dir), "run": {"path": cal.rel(run_path), "sha256": cal.sha256(run_path)},
                      "frozen_files_different": rec["frozen_files"]["different"]}, indent=1))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="cascade of gate GJ (floor mode, cascade mode): decisions files of "
                                             "interface 7")
    ap.add_argument("--mode", required=True, choices=MODES)
    ap.add_argument("--set", required=True, choices=["dev", "validation", "group7"])
    ap.add_argument("--doc", nargs="*")
    ap.add_argument("--calibrations", default=str(cal.FLOOR_FILE), help="the floor calibration file")
    ap.add_argument("--out", default=None, help="default: daten/gj/decisions_floor (floor), daten/gj/decisions "
                                                "(cascade)")
    ap.add_argument("--label", default="", help="suffix of the run record name")
    ap.add_argument("--continue-missing", action="store_true")
    ap.add_argument("--states", nargs="+", default=None, help="cascade: job folders of the states (states/<doc>.npz)")
    ap.add_argument("--entry-d1", choices=("yes", "no"), default=None, help="cascade: entry decision of D1")
    ap.add_argument("--entry-b12", choices=("yes", "no"), default=None, help="cascade: entry decision of B1 and B2")
    ap.add_argument("--design", default=None, help="cascade: the design folder (default daten/gj/design)")
    ap.add_argument("--freeze", default=None,
                    help="cascade: the design freeze file (default daten/gj/design_freeze.json)")
    ap.add_argument("--r2", default=None, help="cascade: JSON {doc_id: {p, calibration}}")
    ap.add_argument("--r2-calibrations", default=None, help="cascade: JSON {calibrations: {id: record}} of R2")
    a = ap.parse_args()
    try:
        code = run(a)
    except guard.GuardRefusal as ex:
        print(f"stopped (GuardRefusal): {ex}", file=sys.stderr)
        code = 3
    sys.exit(code)


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Isolation in sub-tasks: the assembly of S1 to S5 into the 13 answers of each atom (stage 3, iteration of
gate 3a, 08.10.2026). Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent
(Claude Opus 5.5). Status: feasibility measurement in stage 3; no gate result.

Input: the stored outputs of the sub-tasks in daten/iso/sub/s1_role, s2_switch, s3_frame, s4_title (no new
CSCS request). S5 comes from the rule `m03_sub_s5_type.predict_rule` on the composed answers (the families of
the predicted S1 to S4, default types); the stored S5 outputs use the families of the reference and thus are
not an input of the assembly.

Composition: `m03_sub_common.compose(doc, s1, s2, s3, s4, s5)`. Measurement: `m03_sub_common.measure` (the
values of `m03_iso_v4.compare_docs`, measurement 4.1).

Variants
  best        S1 combined, S2 rule, S3 rules, S4 rule, S5 rule (the best variant of each sub-task, chosen on dev)
  rules       S1 rule, S2 rule, S3 rules, S4 rule, S5 rule
  apertus     S1 apertus, S2 apertus_v1, S3 apertus_ctx, S4 apertus; S5 rule (eval and gold only)
  combined    S1 combined, S2 combined_v1, S3 combined, S4 combined; S5 rule (eval and gold only)
  oracle_Sk   "best" with Sk from the reference (k = 1 ... 5)
  only_Sk     the reference with only Sk from "best" (the value of the sub-task report)
  assembled   "best" with the assembly option CHOSEN_OPTION (chosen on dev only, options_dev.json):
              s4_over_s3  an atom of S4 is text (S3 cannot make a predicted title atom none)
              s1_start    when the S2 rule had no strong cue (start family only the default SPONSOR) and S1 is
                          response, minutes or committee, the S2 start is EXECUTIVE, PLENARY or COMMITTEE
              s1_other_frame (not chosen)  S1 other: all atoms frame
Baseline: daten/iso/v4/hyp_oof_a1 (whole-document readout, out of fold: fold X for group 4, fold Y for
group 5); group 6 has no out-of-fold output. Compared on the eval documents that have a baseline file.

Note: this file is a copy of the script that made the outputs in daten/iso/sub/assemble/. The task of the
assembly named no code file in src/, so the script is kept next to its outputs.

Usage (in this order):
  uv run python daten/iso/sub/assemble/m03_sub_assemble.py run          (variants, oracle -> results.json)
  uv run python daten/iso/sub/assemble/m03_sub_assemble.py options      (assembly options, dev only)
  uv run python daten/iso/sub/assemble/m03_sub_assemble.py final        (eval, gold, baseline -> final.json,
                                                                         hyp_<variant>_<split>/)
  uv run python daten/iso/sub/assemble/m03_sub_assemble.py sensitivity  (S5 "empfehlung" -> sensitivity_s5_empfehlung.json)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import m03_sub_common as sc  # noqa: E402
import m03_sub_s5_type as s5m  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

SUB = sc.SUB
OUT = SUB / "assemble"
KEYS = ("documents", "boundaries_ref", "boundaries_hyp", "labelled_f1", "labelled_f1_lower", "inner_boundaries_ref",
        "inner_recall_labelled", "text_omission", "documents_with_omission", "text_intrusion", "text_class_error",
        "document_exact_rate", "unlabelled_f1")
ROLE_FAMILY = {"response": "EXECUTIVE", "minutes": "PLENARY", "committee": "COMMITTEE"}

# file name of each sub-task variant for each split
FILES = {
    "s1": {"rule": "s1_role/rule_{s}.json", "combined": "s1_role/combined_{s}.json", "apertus": "s1_role/apertus_{s}.json"},
    "s2": {"rule": "s2_switch/rule_{s}.json", "combined": "s2_switch/combined_v1_{s}.json",
           "apertus": "s2_switch/apertus_v1_{s}.json"},
    "s3": {"rule": "s3_frame/rules_{s}.json", "combined": "s3_frame/combined_{s}.json",
           "apertus": "s3_frame/apertus_ctx_{s}.json"},
    "s4": {"rule": "s4_title/rule_{s}.json", "combined": "s4_title/combined_{s}.json", "apertus": "s4_title/apertus_{s}.json"},
}
FIELD = {"s1": "role", "s2": "s2", "s3": "s3", "s4": "s4"}
VARIANTS = {
    "best": {"s1": "combined", "s2": "rule", "s3": "rule", "s4": "rule"},
    "rules": {"s1": "rule", "s2": "rule", "s3": "rule", "s4": "rule"},
    "apertus": {"s1": "apertus", "s2": "apertus", "s3": "apertus", "s4": "apertus"},
    "combined": {"s1": "combined", "s2": "combined", "s3": "combined", "s4": "combined"},
}


def source_of(split: str) -> str:
    return "gold" if split == "gold" else "ref"


def load_variant(task: str, variant: str, split: str) -> dict | None:
    p = SUB / FILES[task][variant].format(s=split)
    if not p.exists():
        return None
    docs = json.loads(p.read_text(encoding="utf-8"))["documents"]
    out = {}
    for d, x in docs.items():
        v = x[FIELD[task]]
        out[d] = [tuple(e) for e in v] if task == "s2" else v
    return out


def labels_of(split: str, spec: dict) -> dict[str, dict]:
    """{doc: {s1, s2, s3, s4}} of the variant spec, or {} if a file is missing."""
    got = {t: load_variant(t, v, split) for t, v in spec.items()}
    if any(g is None for g in got.values()):
        return {}
    ids = sc.splits()[split]
    p2 = SUB / FILES["s2"][spec["s2"]].format(s=split)
    reason = {d: x.get("start_reason", "") for d, x in json.loads(p2.read_text(encoding="utf-8"))["documents"].items()}
    out = {}
    for d in ids:
        if all(d in got[t] for t in got):
            out[d] = {t: got[t][d] for t in got}
            # the S2 rule had no strong cue: its start family is only the default SPONSOR
            out[d]["s2_start_weak"] = reason.get(d, "").startswith("no strong cue")
    return out


def assemble(d: str, lab: dict, s5: dict | str = "rule", opt: dict | None = None) -> list[str]:
    """The 13 answers of each atom. s5 "rule": predict_rule on the composed answers; else a {atom: type} dict."""
    opt = opt or {}
    s1, s2, s3, s4 = lab["s1"], list(lab["s2"]), dict(lab["s3"]), list(lab["s4"])
    if opt.get("s4_over_s3"):
        for a in s4:
            s3[a] = "text"
    if opt.get("s1_start") and s1 in ROLE_FAMILY and s2 and len(s2) == 1 and lab.get("s2_start_weak"):
        s2 = [(s2[0][0], ROLE_FAMILY[s1])]
    if opt.get("s1_other_frame") and s1 == "other":
        s3 = {a: "frame" for a in s3}
    base = sc.compose(d, s1, s2, s3, s4, {})
    if s5 == "rule":
        s5 = s5m.predict_rule(d, base)["s5"]
    return sc.compose(d, s1, s2, s3, s4, s5)


def measure(ids: list[str], answers: dict[str, list[str]], split: str) -> dict:
    m = sc.measure(ids, answers, source_of(split))
    return {k: m[k] for k in KEYS}


def run_variant(split: str, spec: dict, oracle: str | None = None, only: str | None = None,
                opt: dict | None = None, ids: list[str] | None = None) -> tuple[dict, dict]:
    labs = labels_of(split, spec)
    src = source_of(split)
    ids = [d for d in (ids or sc.splits()[split]) if d in labs]
    answers = {}
    for d in ids:
        ref = sc.doc_labels(d, src)
        lab = dict(labs[d])
        if only:
            # the reference, with only one sub-task from the method
            lab2 = {k: ref[k] for k in ("s1", "s2", "s3", "s4")}
            if only == "s5":
                answers[d] = sc.compose(d, ref["s1"], ref["s2"], ref["s3"], ref["s4"],
                                        s5m.predict_rule(d, sc.reference(d, src))["s5"])
                continue
            lab2[only] = lab[only]
            answers[d] = sc.compose(d, lab2["s1"], lab2["s2"], lab2["s3"], lab2["s4"], ref["s5"])
            continue
        s5: dict | str = "rule"
        if oracle == "s5":
            s5 = ref["s5"]
        elif oracle:
            lab[oracle] = ref[oracle]
        answers[d] = assemble(d, lab, s5, opt)
    return measure(ids, answers, split), answers


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        OUT.mkdir(parents=True, exist_ok=True)
        res = {}
        for split in ("dev", "eval", "gold"):
            res[split] = {}
            for name, spec in VARIANTS.items():
                m, ans = run_variant(split, spec)
                if not m["documents"]:
                    continue
                res[split][name] = m
                print(split, name, m)
            for k in ("s1", "s2", "s3", "s4", "s5"):
                m, _ = run_variant(split, VARIANTS["best"], oracle=k)
                res[split][f"oracle_{k}"] = m
                print(split, f"oracle_{k}", m)
                m, _ = run_variant(split, VARIANTS["best"], only=k)
                res[split][f"only_{k}"] = m
                print(split, f"only_{k}", m)
        (OUT / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    elif cmd == "options":
        # dev only: each assembly option alone and all together, on the "best" variant
        res = {}
        for name, opt in OPTIONS.items():
            m, _ = run_variant("dev", VARIANTS["best"], opt=opt)
            res[name] = m
            print(name, {k: m[k] for k in ("labelled_f1", "labelled_f1_lower", "text_omission", "text_intrusion",
                                            "text_class_error", "document_exact_rate")})
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "options_dev.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


    elif cmd == "final":
        final()
    elif cmd == "sensitivity":
        sensitivity()


def sensitivity() -> None:
    """The S5 alternative "empfehlung" of RX_PROPOSAL_LABEL has no dev match (verification of S5): the composites
    without it (in memory only; the S5 file is not changed)."""
    import re

    res = {}
    old = s5m.RX_PROPOSAL_LABEL
    for label, rx in (("with", old), ("without", re.compile(
            r"^" + s5m.NUM + r"(?:antr[äa]ge?|antrag|propositions?|propost[ae]|pr[ée]avis)\b(?P<rest>.*)$", re.I))):
        s5m.RX_PROPOSAL_LABEL = rx
        for name, opt in (("best", {}), ("assembled", OPTIONS[CHOSEN_OPTION])):
            for split in ("dev", "eval"):
                m, ans = run_variant(split, VARIANTS["best"], opt=opt)
                res[f"{label}_empfehlung/{name}/{split}"] = m
                if split == "eval":
                    bids = [d for d in ans if (BASELINE / f"{d}.json").exists()]
                    res[f"{label}_empfehlung/{name}/eval_baseline_documents"] = measure(
                        bids, {d: ans[d] for d in bids}, split)
    s5m.RX_PROPOSAL_LABEL = old
    for k, v in res.items():
        print(k, v["labelled_f1"], v["labelled_f1_lower"], v["boundaries_hyp"], v["boundaries_ref"])
    (OUT / "sensitivity_s5_empfehlung.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


CHOSEN_OPTION = "s4_over_s3+s1_start"   # chosen on dev (options_dev.json): most correct boundaries (193 of 283),
                                        # fewest documents with omission (74); "all" has 192 and 85
BASELINE = ROOT / "daten/iso/v4/hyp_oof_a1"   # whole-document readout, out of fold (fold X: group 4, fold Y: group 5)


def pairs(ids: list[str], answers: dict[str, list[str]], split: str) -> dict:
    """Atoms with a text answer on both sides and a different answer: reference -> method (top pairs)."""
    from collections import Counter

    c = Counter()
    for d in ids:
        for r, h in zip(sc.reference(d, source_of(split)), answers[d]):
            if r in v4.TEXT and h in v4.TEXT and r != h:
                c[f"{r}->{h}"] += 1
    return dict(c.most_common(8))


def per_doc(ids: list[str], answers: dict[str, list[str]], split: str) -> dict:
    out = {}
    for d in ids:
        m = sc.measure([d], {d: answers[d]}, source_of(split))
        c = m["counts"]
        out[d] = {"group": sc.load()[d].group, "boundaries_ref": c["br"], "boundaries_hyp": c["bh"], "correct": c["good"],
                  "omitted": c["omitted"], "intruded": c["intruded"], "class_err": c["class_err"], "exact": bool(c["exact"])}
    return out


def baseline_answers(ids: list[str]) -> dict[str, list[str]]:
    out = {}
    for d in ids:
        p = BASELINE / f"{d}.json"
        if p.exists():
            out[d] = v4.load_answers(p, d, sc.load()[d].ids)
    return out


def final() -> None:
    """The composites on eval and gold, the baseline on the same documents, per-document values; writes
    daten/iso/sub/assemble/final.json and the answer files hyp_<variant>_<split>/<doc>.json."""
    res: dict = {"chosen_option": CHOSEN_OPTION, "option": OPTIONS[CHOSEN_OPTION], "baseline": str(BASELINE)}
    for split in ("dev", "eval", "gold"):
        r: dict = {}
        ids = sc.splits()[split]
        var = {"best": run_variant(split, VARIANTS["best"]),
               "assembled": run_variant(split, VARIANTS["best"], opt=OPTIONS[CHOSEN_OPTION])}
        if split != "dev":
            var["apertus"] = run_variant(split, VARIANTS["apertus"])
            var["combined"] = run_variant(split, VARIANTS["combined"])
        for name, (m, ans) in var.items():
            r[name] = {"all": m, "pairs": pairs(list(ans), ans, split)}
            for d, a in ans.items():
                v4.write(OUT / f"hyp_{name}_{split}", d, a, "method", f"m03_sub_assemble {name} ({split})")
            if split != "dev":
                r[name]["per_doc"] = per_doc(list(ans), ans, split)
                groups = sorted({sc.load()[d].group for d in ans})
                r[name]["by_group"] = {g: measure([d for d in ans if sc.load()[d].group == g],
                                                  {d: a for d, a in ans.items() if sc.load()[d].group == g}, split)
                                       for g in groups}
        if split != "dev":
            base = baseline_answers(ids)
            bids = [d for d in ids if d in base]
            r["baseline"] = {"documents": bids, "all": measure(bids, base, split), "pairs": pairs(bids, base, split),
                             "per_doc": per_doc(bids, base, split)}
            for name in ("best", "assembled", "apertus"):
                ans = {d: a for d, a in var[name][1].items() if d in base}
                r[name]["on_baseline_documents"] = measure(bids, ans, split)
                r[name]["pairs_on_baseline_documents"] = pairs(bids, ans, split)
        res[split] = r
        print(split, json.dumps({k: (v["all"] if isinstance(v, dict) and "all" in v else None) for k, v in r.items()}))
        if split != "dev":
            print(split, "baseline docs:", {n: r[n]["on_baseline_documents"] for n in ("best", "assembled", "apertus")})
    (OUT / "final.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


OPTIONS = {
    "none": {},
    "s4_over_s3": {"s4_over_s3": True},
    "s1_start": {"s1_start": True},
    "s1_other_frame": {"s1_other_frame": True},
    "s4_over_s3+s1_start": {"s4_over_s3": True, "s1_start": True},
    "all": {"s4_over_s3": True, "s1_start": True, "s1_other_frame": True},
}


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Isolation at the level of E20 version 4: answers only from eCH-0295 (I95), conversion and measurement.

E20 is the definition of the isolation task in the private project. The technical report
(track_2a/technical_report.md) gives version 4.1: the answers and the fixed answers in chapter 2.2,
the measurement in chapter 5.1. Below, "fixed answers" is the procedure of `m03_iso_hilfe.py`.

Version 4.1 of the measurement (05.10.2026): class-aware values after the code review of 05.10.2026
(the version 4.0 values ignored which text field a block gets).

E20 version 4 gives each atom one answer. The text answers are the TextBlock fields of I95 with their
text type; "none" is "no text field"; "furniture" is the mechanical cleanup (page numbers, running
headers and footers, file data; rules R1, R4, R5 of `m03_iso_hilfe.py`). The model never gives
"furniture": only the rules do (decision by delegation, 05.10.2026).

  answer                   I95 field and text_type
  title                    Affair.title, title
  short_title              Affair.title, short_title
  submitted                Submission.texts, submitted
  reasoning                Submission.texts, reasoning
  response                 ResponseStep.texts, response
  recommendation           ResponseStep.texts, recommendation
  summary                  texts of the step of its author, summary
  committee_recommendation CommitteeDecision.text, recommendation
  speech                   PlenaryDebate.debate_events[].speech.text (text_type not set)
  proposition              PlenaryDebate.debate_events[].proposition.text (text_type not set)
  vote                     PlenaryDebate.debate_events[].vote.text (text_type not set)
  none                     no text field
  furniture                page furniture (cleanup)

Conversion of the version 3.1 references (only references; never method outputs):
  the fixed answers of E20 v4 first (R1, R4, R5 furniture; R3 none); other furniture
  (print template) -> none; footnote (Docling form Fussnote) -> the last text answer before it on
  the same page, else none; caption (Docling form Bildlegende, not inside a picture) -> the answer of
  the text around it if the main atoms before and after it have the same text answer, else none; all
  other inserts -> none; classes title ... summary -> the same answer; head, closing, distribution ->
  none; other_text -> none, except the oral statements in SPEECH_ATOMS -> speech (E20 v4, rule O).

Measurement (E20 version 4; version 4.1):
  carried atoms      footnotes and carried captions; they are not in the boundary sequence
  boundary sequence  the text atoms of the reference without carried atoms, in atom order
  boundary           a position k > 0 in that sequence where the reference answer changes
  method answer      at an atom of the sequence that the method gives no text answer, the method
                     carries its previous text answer of the sequence; before its first text answer
                     it has none (no boundary is counted there)
  labelled boundary  a method boundary at k counts as correct only if the method answers at k - 1
                     and k equal the reference answers (class-aware)
  inner boundary     a boundary whose previous reference answer is not "title"
  text omission      text atoms of the reference that the method gives none or furniture / all text
                     atoms of the reference
  text intrusion     atoms with a text answer of the method that have none or furniture in the
                     reference / all atoms with a text answer of the method
  text class error   atoms with a text answer on both sides and different answers / atoms with a text
                     answer on both sides
  document exact     all labelled boundaries exact, no omission, no intrusion, no class error
A missing method file stops the measurement (or counts as "all none" with --missing-as-none). The
ids and the length of each file must be equal to the atoms of the document.

Native coding (for coders; E20 version 4):
  python3 src/m03_iso_v4.py write4 DOC_ID OUT_DIR --coder A --spans "title:B2.1-B3.1; submitted:B4.1-B12.3"
      every atom outside a span is none; the fixed answers of E20 v4 (R1, R4, R5 furniture;
      R3 none) override the spans; a span is "answer:FIRST-LAST" in atom order (FIRST-LAST may be one id)
  python3 src/m03_iso_v4.py validate4 FILE...      (ids, answers, fixed answers)
  python3 src/m03_iso_v4.py spans FILE              (the text answers of a file as spans for write4)
  python3 src/m03_iso_v4.py view FILE               (the atom lines of the document with the answers of FILE)
  Files of a final group need --final (only for the coders of the final references); test documents
  (<data>/gold/test; test documents stay apart from the development) need --test (only for the
  coders of the gold set).

Usage:
  python3 src/m03_iso_v4.py convert data/iso/ref data/iso/v4/ref --reference
  python3 src/m03_iso_v4.py compare data/iso/v4/ref data/iso/v4/hyp_x --groups 1,2,3
  python3 src/m03_iso_v4.py agree data/iso/v4/ref_A data/iso/v4/ref_B --groups 1,2,3,4,5
  (folder arguments are relative to the working folder; here: track_2a with the default data root)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import iso_path  # noqa: E402
import m03_iso_jev as jev  # noqa: E402
import m03_iso_mass as ms  # noqa: E402

ROOT = jev.ROOT
VERSION = "e20-v4.1"
TEXT = ("title", "short_title", "submitted", "reasoning", "response", "recommendation", "summary",
        "committee_recommendation", "speech", "proposition", "vote")
ANSWERS = TEXT + ("none", "furniture")
SAME = {"title", "short_title", "submitted", "reasoning", "response", "recommendation", "summary"}
# Oral statements in protocols that the version 3.1 references coded as other_text (E20 v4, rule O).
# 925529 B54.1 is the heading of the statement (rule H).
SPEECH_ATOMS = {
    "375917": {"B3.1", "B3.2", "B3.3", "B3.4", "B3.5", "B3.6", "B3.7"},
    "925529": {"B54.1", "B55.1", "B55.2", "B55.3", "B55.4", "B55.5"},
}
FINAL_GROUPS = {"7"}


def atoms_of(doc_id: str) -> list[dict]:
    return json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))["atome"]


def carried_ids(atoms: list[dict]) -> set[str]:
    return {a["id"] for a in atoms if a["label"] == "footnote" or (a["label"] == "caption" and a.get("eltern") != "picture")}


def convert(seg: dict, atoms: list[dict], reference: bool) -> list[str]:
    """Version 3.1 segmentation -> one version 4 answer for each atom."""
    ids = [a["id"] for a in atoms]
    old = jev.answers_from_segmentation(seg, ids)
    speech = SPEECH_ATOMS.get(seg["doc_id"], set()) if reference else set()
    missing = speech - set(ids)
    assert not missing, (seg["doc_id"], missing)
    carried = carried_ids(atoms)
    fixed = fixed_answers(seg["doc_id"])
    out = []
    for a, x in zip(atoms, old):
        if a["id"] in fixed:
            out.append(fixed[a["id"]])
        elif x == "furniture":
            out.append("none")   # print template of an attachment: no fixed rule in E20 v4
        elif x == "insert":
            out.append("carry" if a["id"] in carried else "none")
        elif x in SAME:
            out.append(x)
        elif x == "other_text" and a["id"] in speech:
            out.append("speech")
        else:
            out.append("none")
    for i, x in enumerate(out):
        if x != "carry":
            continue
        a = atoms[i]
        if a["label"] == "footnote":
            prev = next((out[j] for j in range(i - 1, -1, -1) if out[j] in TEXT and atoms[j]["seite"] == a["seite"]), None)
            out[i] = prev or "none"
        else:
            prev = next((out[j] for j in range(i - 1, -1, -1) if out[j] in TEXT or out[j] == "none"), "none")
            nxt = next((out[j] for j in range(i + 1, len(out)) if out[j] in TEXT or out[j] == "none"), "none")
            out[i] = prev if prev in TEXT and prev == nxt else "none"
    return out


def boundaries(ref: list[str], hyp: list[str], skip: set[int]):
    """(reference boundaries, method boundaries, labelled correct boundaries, inner reference boundaries)."""
    seq = [i for i, x in enumerate(ref) if x in TEXT and i not in skip]
    br, bh, good, inner = set(), set(), set(), set()
    prev_r = prev_h = None
    for k, i in enumerate(seq):
        r = ref[i]
        h = hyp[i] if hyp[i] in TEXT else prev_h
        if k > 0 and r != prev_r:
            br.add(k)
            if prev_r != "title":
                inner.add(k)
        if k > 0 and prev_h is not None and h != prev_h:
            bh.add(k)
            if h == r and prev_h == prev_r:
                good.add(k)
        prev_r, prev_h = r, h
    return br, bh, good, inner


def load_answers(path: Path, doc_id: str, ids: list[str]) -> list[str]:
    x = json.loads(path.read_text(encoding="utf-8"))
    if x.get("ids") != ids:
        raise SystemExit(f"{path}: atom ids differ from the atoms of {doc_id}")
    bad = [a for a in x["answers"] if a not in ANSWERS]
    if bad:
        raise SystemExit(f"{path}: answers outside of E20 v4: {sorted(set(bad))[:5]}")
    return x["answers"]


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b) (continued fraction, Numerical Recipes 6.4)."""
    import math

    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)

    def cf(a, b, x):
        qab, qap, qam = a + b, a + 1, a - 1
        c, d = 1.0, 1 - qab * x / qap
        d = 1 / (d if abs(d) > 1e-30 else 1e-30)
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-30 else 1e-30)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-30 else 1e-30
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1 + aa * d
            d = 1 / (d if abs(d) > 1e-30 else 1e-30)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-30 else 1e-30
            de = d * c
            h *= de
            if abs(de - 1) < 1e-12:
                break
        return h

    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * cf(a, b, x) / a
    return 1 - math.exp(lbt) * cf(b, a, 1 - x) / b


def jeffreys_lower(x: int, n: int, level: float = 0.95) -> float | None:
    """One-sided Jeffreys lower bound of a proportion x / n: quantile 1 - level of Beta(x + 0.5, n - x + 0.5)."""
    if n == 0:
        return None
    if x == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _betai(x + 0.5, n - x + 0.5, mid) < 1 - level:
            lo = mid
        else:
            hi = mid
    return round(lo, 4)


def compare_docs(ref_dir: Path, hyp_dir: Path, docs: list[str], missing_as_none: bool = False) -> dict:
    c = {k: 0 for k in ("br", "bh", "good", "unl", "inner", "inner_good", "inner_bh", "text_ref", "omitted",
                        "text_hyp", "intruded", "both", "class_err", "exact", "n", "missing", "docs_omission")}
    for d in docs:
        ids = [a["id"] for a in atoms_of(d)]
        ref = load_answers(ref_dir / f"{d}.json", d, ids)
        hp = hyp_dir / f"{d}.json"
        if not hp.exists():
            if not missing_as_none:
                raise SystemExit(f"missing method file {hp} (use --missing-as-none to count it as all none)")
            hyp = ["none"] * len(ids)
            c["missing"] += 1
        else:
            hyp = load_answers(hp, d, ids)
        skip = {i for i, a in enumerate(ids) if a in carried_ids(atoms_of(d))}
        br, bh, good, inner = boundaries(ref, hyp, skip)
        c["br"] += len(br)
        c["bh"] += len(bh)
        c["good"] += len(good)
        c["unl"] += len(br & bh)
        c["inner"] += len(inner)
        c["inner_good"] += len(good & inner)
        om = sum(1 for r, h in zip(ref, hyp) if r in TEXT and h not in TEXT)
        it = sum(1 for r, h in zip(ref, hyp) if h in TEXT and r not in TEXT)
        both = sum(1 for r, h in zip(ref, hyp) if r in TEXT and h in TEXT)
        ce = sum(1 for r, h in zip(ref, hyp) if r in TEXT and h in TEXT and r != h)
        c["text_ref"] += sum(r in TEXT for r in ref)
        c["text_hyp"] += sum(h in TEXT for h in hyp)
        c["omitted"] += om
        c["docs_omission"] += om > 0
        c["intruded"] += it
        c["both"] += both
        c["class_err"] += ce
        c["n"] += 1
        c["exact"] += good == br and bh == br and om == 0 and it == 0 and ce == 0

    def f1(tp, nh, nr):
        p = tp / nh if nh else 0.0
        r = tp / nr if nr else 0.0
        return round(2 * p * r / (p + r), 4) if p + r else 0.0

    return {"documents": c["n"], "documents_expected": len(docs), "missing_as_none": c["missing"],
            "boundaries_ref": c["br"], "boundaries_hyp": c["bh"],
            "labelled_f1": f1(c["good"], c["bh"], c["br"]),
            "labelled_f1_lower": (lambda lp, lr: round(2 * lp * lr / (lp + lr), 4) if lp and lr else 0.0)(
                jeffreys_lower(c["good"], c["bh"]) or 0.0, jeffreys_lower(c["good"], c["br"]) or 0.0),
            "documents_with_omission": c["docs_omission"],
            "unlabelled_f1": f1(c["unl"], c["bh"], c["br"]),
            "inner_boundaries_ref": c["inner"], "inner_recall_labelled": round(c["inner_good"] / c["inner"], 4) if c["inner"] else None,
            "text_omission": round(c["omitted"] / c["text_ref"], 4) if c["text_ref"] else None,
            "text_intrusion": round(c["intruded"] / c["text_hyp"], 4) if c["text_hyp"] else None,
            "text_class_error": round(c["class_err"] / c["both"], 4) if c["both"] else None,
            "document_exact_rate": round(c["exact"] / c["n"], 4) if c["n"] else None,
            "counts": c}


def write(out_dir: Path, doc_id: str, answers: list[str], coder: str, source: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = [a["id"] for a in atoms_of(doc_id)]
    assert len(ids) == len(answers)
    (out_dir / f"{doc_id}.json").write_text(json.dumps({"doc_id": doc_id, "version": VERSION, "coder": coder,
                                                        "source": source, "ids": ids, "answers": answers},
                                                       ensure_ascii=False, indent=0), encoding="utf-8")


def fixed_answers(doc_id: str) -> dict[str, str]:
    import m03_iso_hilfe as hf

    out = {}
    for a, (role, rule) in hf.fixed_roles(doc_id)[0].items():
        if rule.startswith(("R1", "R4", "R5")):
            out[a] = "furniture"
        elif rule.startswith("R3"):
            out[a] = "none"
    return out


def write4(doc_id: str, out_dir: Path, coder: str, spans: str) -> list[str]:
    ids = [a["id"] for a in atoms_of(doc_id)]
    pos = {a: i for i, a in enumerate(ids)}
    answers = ["none"] * len(ids)
    for part in [x.strip() for x in spans.split(";") if x.strip()]:
        ans, rng = [x.strip() for x in part.split(":", 1)]
        if ans not in TEXT and ans != "none":
            raise SystemExit(f"unknown answer {ans!r}; allowed: {TEXT + ('none',)}")
        first, last = (rng.split("-", 1) + [None])[:2] if "-" in rng else (rng, rng)
        first, last = first.strip(), (last or first).strip()
        if first not in pos or last not in pos or pos[last] < pos[first]:
            raise SystemExit(f"bad span {part!r}")
        for i in range(pos[first], pos[last] + 1):
            answers[i] = ans
    for a, x in fixed_answers(doc_id).items():
        answers[pos[a]] = x
    write(out_dir, doc_id, answers, coder, "native coding, E20 version 4")
    return answers


def validate4(path: Path) -> list[str]:
    x = json.loads(path.read_text(encoding="utf-8"))
    d = x["doc_id"]
    ids = [a["id"] for a in atoms_of(d)]
    err = []
    if x.get("ids") != ids:
        err.append("ids differ from the atoms")
    if len(x.get("answers", [])) != len(ids):
        err.append("length differs")
    err += [f"unknown answer {a}" for a in set(x.get("answers", [])) - set(ANSWERS)]
    fixed = fixed_answers(d)
    for i, a in enumerate(ids):
        if i < len(x.get("answers", [])):
            got = x["answers"][i]
            if a in fixed and got != fixed[a]:
                err.append(f"{a}: {got}, fixed answer {fixed[a]}")
            if a not in fixed and got == "furniture":
                err.append(f"{a}: furniture without a fixed rule")
    return err


def spans_of(ids: list[str], answers: list[str]) -> str:
    """Spans of the text answers in the syntax of write4 (none and furniture are not written)."""
    out, i = [], 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and answers[j + 1] == answers[i]:
            j += 1
        if answers[i] in TEXT:
            out.append(f"{answers[i]}:{ids[i]}" + (f"-{ids[j]}" if j > i else ""))
        i = j + 1
    return "; ".join(out)


def final_docs() -> set[str]:
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        return {r["doc_id"] for r in csv.DictReader(f) if r["group"] in FINAL_GROUPS}


def final_parliaments() -> set[str]:
    """Parliaments of the final groups: no method learns from a document of these parliaments."""
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        return {r["body_key"] for r in csv.DictReader(f) if r["group"] in FINAL_GROUPS}


def group_docs(groups: list[str], final: bool) -> list[str]:
    if FINAL_GROUPS & set(groups) and not final:
        raise SystemExit(f"groups {sorted(FINAL_GROUPS)} are final groups: use --final only for the final measurement")
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        return [r["doc_id"] for r in csv.DictReader(f) if r["group"] in groups]


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    final = "--final" in args
    groups = args[args.index("--groups") + 1].split(",") if "--groups" in args else ["1", "2", "3", "4", "5", "6"]
    if cmd == "write4":
        doc_id, out_dir = args[0], Path(args[1])
        coder = args[args.index("--coder") + 1]
        spans = args[args.index("--spans") + 1]
        ans = write4(doc_id, out_dir, coder, spans)
        print(f"{doc_id}: {sum(a in TEXT for a in ans)} text atoms, {ans.count('none')} none, {ans.count('furniture')} furniture")
        return
    if cmd in ("spans", "view"):
        path = Path(args[0])
        x = json.loads(path.read_text(encoding="utf-8"))
        if x["doc_id"] in final_docs() and not final:
            raise SystemExit("final group: only with --final (never for the developer of a method)")
        from m03_iso_paths import TEST
        if iso_path("atome", x["doc_id"]).is_relative_to(TEST) and "--test" not in args:
            raise SystemExit("test document (kept apart from the development): only with --test (coders of the gold set; never the developer)")
        if cmd == "spans":
            print(spans_of(x["ids"], x["answers"]))
            return
        ans = dict(zip(x["ids"], x["answers"]))
        for raw in iso_path("atome_prompt", x["doc_id"], "txt").read_text(encoding="utf-8").splitlines():
            head = raw.split(" | ", 1)[0]
            print(f"{ans[head]:>24} | {raw}" if head in ans else raw)
        return
    if cmd == "validate4":
        bad = 0
        for p in args:
            if p.startswith("--"):
                continue
            err = validate4(Path(p))
            bad += bool(err)
            print(f"{p}: {'ok' if not err else err[:5]}")
        print(f"files {len([a for a in args if not a.startswith('--')])}, invalid {bad}")
        sys.exit(1 if bad else 0)
    if cmd == "convert":
        src, dst = Path(args[0]), Path(args[1])
        reference = "--reference" in args
        allowed = set(group_docs(groups, final)) if "--groups" in args else None
        final_set = final_docs()
        n = 0
        for p in sorted(src.glob("*.json")):
            seg = json.loads(p.read_text())
            if "segments" not in seg:
                continue
            if seg["doc_id"] in final_set and not final:
                continue
            if allowed is not None and seg["doc_id"] not in allowed:
                continue
            answers = convert(seg, atoms_of(seg["doc_id"]), reference)
            write(dst, seg["doc_id"], answers, seg.get("coder", ""),
                  f"{src}/{p.name} (E20 v3.1, converted, {'reference' if reference else 'method output'})")
            n += 1
        print(f"converted {n} files -> {dst}")
    elif cmd in ("compare", "agree"):
        a_dir, b_dir = Path(args[0]), Path(args[1])
        mn = "--missing-as-none" in args
        for g in groups:
            r = compare_docs(a_dir, b_dir, group_docs([g], final), mn)
            if cmd == "agree":
                r2 = compare_docs(b_dir, a_dir, group_docs([g], final), mn)
                r = {"labelled_f1_mean": round((r["labelled_f1"] + r2["labelled_f1"]) / 2, 4),
                     "a_as_reference": r["labelled_f1"], "b_as_reference": r2["labelled_f1"],
                     "text_class_error": r["text_class_error"], "documents": r["documents"]}
            print(f"group {g}:", {k: v for k, v in r.items() if k != "counts"})
        r = compare_docs(a_dir, b_dir, group_docs(groups, final), mn)
        if cmd == "agree":
            r2 = compare_docs(b_dir, a_dir, group_docs(groups, final), mn)
            r = {"labelled_f1_mean": round((r["labelled_f1"] + r2["labelled_f1"]) / 2, 4),
                 "a_as_reference": r["labelled_f1"], "b_as_reference": r2["labelled_f1"],
                 "text_class_error": r["text_class_error"], "documents": r["documents"]}
        print("all:", {k: v for k, v in r.items() if k != "counts"})
    else:
        raise SystemExit(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    main()

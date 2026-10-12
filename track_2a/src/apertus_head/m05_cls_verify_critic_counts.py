# SPDX-License-Identifier: Apache-2.0
"""Path 2 (E34), step "Verify, integrity critic": artefact baselines and counts (no model).

Questions: is the gain of the frozen readout over the rule baselines real, or an artefact of length,
language, parliament or a weak rule? All rules here are fixed rules. The length thresholds and the two
new keyword rules were made on dev documents only. Validation values are information (counts only).
No test parliament, no group 7 parliament, no document of a protected list.

Inputs: daten/cls/r1_dataset.csv, r2_dataset.csv, daten/cls/apertus/{design,check,validation}_scores_r*.json,
the text cache daten/cls/text/ (dev and validation only), the rule baselines of src/m05_cls_apertus.py.
Output: daten/cls/verify_critic_counts.json.

Usage: .venv/bin/python src/m05_cls_verify_critic_counts.py
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m05_cls_apertus as ap  # noqa: E402
import m05_cls_data as cd  # noqa: E402

OUT = cd.OUT / "verify_critic_counts.json"
FROZEN = {"r1": "r1_v1_i95_de", "r2": "r2_v1_de"}

# R1 keyword rule v2 (made on dev): sentence level, a negation or rejection word in the sentence wins
KW2_AGAINST = re.compile(
    r"nicht\s*erheblich|nichterheblich|abzulehnen|ablehnung|\blehnt\b.{0,160}?\bab\b|nicht\s+(zu\s+)?überweis|"
    r"nichtüberweisung|nicht-?\s?entgegennahme|nicht\s+entgegenzunehmen|nicht\s+bereit|rejet|rejeter|"
    r"ne\s+pas\s+(prendre\s+en\s+considération|accepter|transmettre)|respinger|non\s+(accogliere|accettare)",
    re.I | re.S)
KW2_FOR = re.compile(
    r"erheblich\s*zu\s*erklären|erheblicherklärung|anzunehmen|annahme|zu\s+überweisen|überweisung|überweisen|"
    r"entgegenzunehmen|entgegen\s*zu\s*nehmen|entgegennahme|nimmt\s+.{0,80}?entgegen|abzuschreiben|accepter|"
    r"prendre\s+en\s+considération|transmettre|classer|accoglier|accettar", re.I | re.S)
# R2 response formula rule (made on dev): a formula of an executive response anywhere in the text
R2_FORMULA = re.compile(
    r"(antwort|stellungnahme)\s+(des|der)\s+(regierungs|gemeinde|stadt|kleinen|bundes|land)rat|"
    r"beantwortet\s+(die|den|das)|(erteilt|gibt)\s+folgende\s+antwort|wie\s+folgt\s*:|risposta\s+(del|a|all)|"
    r"rispondiamo|il\s+municipio\s+(osserva|risponde)|r[ée]ponse\s+du|"
    r"le\s+conseil[- ](d.[ée]tat|ex[ée]cutif|communal|municipal)\s+(r[ée]pond|prend\s+position)|"
    r"beantwortung\s*$|;\s*antwort", re.I | re.M)


def kw2(t: str) -> str:
    last = None
    for s in re.split(r"(?<=[.!?:])\s+|\n\s*\n", t):
        if KW2_AGAINST.search(s):
            last = "recommended_against"
        elif KW2_FOR.search(s):
            last = "recommended_for"
    return last or "recommended_against"


def scores(task: str, subset: str) -> dict[str, float | None]:
    x = json.loads((ap.OUT / f"{subset}_scores_{task}.json").read_text(encoding="utf-8"))
    return {d: (s.get(FROZEN[task]) or {}).get("p") for d, s in x["scores"].items()}


def acc(rows, pred) -> dict:
    k = sum(pred.get(r["doc_id"]) == r["label"] for r in rows)
    return {"correct": k, "n": len(rows), "accuracy": round(k / len(rows), 3) if rows else None}


def bal(rows, pred, opts) -> dict:
    rec = {}
    for o in opts:
        rr = [r for r in rows if r["label"] == o]
        rec[o] = round(sum(pred.get(r["doc_id"]) == o for r in rr) / len(rr), 3) if rr else None
    v = [x for x in rec.values() if x is not None]
    return {"n": len(rows), "recall": rec, "balanced_accuracy": round(sum(v) / len(v), 3) if len(v) == 2 else None}


def main() -> None:
    out: dict = {"made": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "r1": {}, "r2": {}}
    prot = cd.protected_doc_ids()
    # ---------------- R1
    rows = {r["doc_id"]: r for r in cd.rows("r1") if r["doc_id"] not in prot}
    p_dev = {**scores("r1", "design"), **scores("r1", "check")}
    p_val = scores("r1", "validation")
    dev = [rows[d] for d in p_dev if d in rows]
    val = [rows[d] for d in p_val if d in rows]
    cd.assert_allowed([r["doc_id"] for r in dev], ("dev",))
    cd.assert_allowed([r["doc_id"] for r in val], ("validation",))
    dl = [r for r in val if r["date_diff_days"] != "" and -7 <= int(r["date_diff_days"]) <= 7]
    model = {d: (None if p is None else "recommended_for" if p >= 0.5 else "recommended_against")
             for d, p in {**p_dev, **p_val}.items()}
    base = ap.baseline_preds("r1", dev + val)
    kw = {r["doc_id"]: kw2(cd.text(r["doc_id"])) for r in dev + val}
    # length rule: the threshold with the best dev accuracy (short document = recommended_for)
    best = max(((sum(("recommended_for" if int(r["n_tokens"]) <= th else "recommended_against") == r["label"]
                     for r in dev), th) for th in (100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1500)))
    th = best[1]
    length = {r["doc_id"]: "recommended_for" if int(r["n_tokens"]) <= th else "recommended_against" for r in dev + val}
    maj = {}
    for name, rs in (("dev", dev), ("validation", val)):
        c = collections.defaultdict(collections.Counter)
        for r in rs:
            c[r["body_key"]][r["label"]] += 1
        maj[name] = sum(x.most_common(1)[0][1] for x in c.values())
    sets = {"dev": dev, "validation": val, "validation_date_linked": dl}
    for b in ("SO", "NE", "247"):
        sets[f"validation_{b}"] = [r for r in val if r["body_key"] == b]
    for b in ("261", "1059", "121"):
        sets[f"dev_{b}"] = [r for r in dev if r["body_key"] == b]
    out["r1"]["length_rule_threshold_tokens"] = th
    out["r1"]["parliament_majority_oracle"] = {"dev": [maj["dev"], len(dev)], "validation": [maj["validation"], len(val)]}
    out["r1"]["median_tokens"] = {f"{n}|{lab}": sorted(int(r["n_tokens"]) for r in rs if r["label"] == lab)[
        len([r for r in rs if r["label"] == lab]) // 2] for n, rs in (("dev", dev), ("validation", val))
        for lab in ap.OPTIONS["r1"]}
    out["r1"]["sets"] = {n: {"model": acc(rs, model), "keyword": acc(rs, base["keyword"]), "keyword_v2": acc(rs, kw),
                             "length_rule": acc(rs, length)} for n, rs in sets.items()}
    # ---------------- R2
    rows2 = {r["doc_id"]: r for r in cd.rows("r2") if r["doc_id"] not in prot}
    q_dev = {**scores("r2", "design"), **scores("r2", "check")}
    q_val = scores("r2", "validation")
    dev2 = [rows2[d] for d in q_dev if d in rows2]
    val2 = [rows2[d] for d in q_val if d in rows2]
    cd.assert_allowed([r["doc_id"] for r in dev2], ("dev",))
    cd.assert_allowed([r["doc_id"] for r in val2], ("validation",))
    model2 = {d: (None if p is None else "yes" if p >= 0.5 else "no") for d, p in {**q_dev, **q_val}.items()}
    base2 = ap.baseline_preds("r2", dev2 + val2)
    form = {r["doc_id"]: "yes" if R2_FORMULA.search(cd.text(r["doc_id"])) else "no" for r in dev2 + val2}
    opts = ap.OPTIONS["r2"]
    best2 = max(((bal(dev2, {r["doc_id"]: "yes" if int(r["n_tokens"]) >= t else "no" for r in dev2}, opts)
                  ["balanced_accuracy"], t) for t in (300, 500, 700, 1000, 1200, 1500, 2000, 2500)))
    t2 = best2[1]
    length2 = {r["doc_id"]: "yes" if int(r["n_tokens"]) >= t2 else "no" for r in dev2 + val2}
    sets2 = {"dev": dev2, "validation": val2,
             "validation_without_306": [r for r in val2 if r["body_key"] != "306"],
             "validation_de_without_306": [r for r in val2 if r["body_key"] != "306" and r["language"] == "de"],
             "validation_fr": [r for r in val2 if r["language"] == "fr"]}
    out["r2"]["length_rule_threshold_tokens"] = t2
    out["r2"]["sets"] = {n: {"model": bal(rs, model2, opts), "heading": bal(rs, base2["heading"], opts),
                             "s1_answer": bal(rs, base2["s1_answer"], opts), "formula_rule": bal(rs, form, opts),
                             "length_rule": bal(rs, length2, opts)} for n, rs in sets2.items()}
    r306 = [r for r in val2 if r["body_key"] == "306"]
    out["r2"]["306_no_documents"] = {"n": len(r306), "model_yes": sum(model2.get(r["doc_id"]) == "yes" for r in r306),
                                     "formula_rule_yes": sum(form[r["doc_id"]] == "yes" for r in r306),
                                     "s1_answer_yes": sum(base2["s1_answer"][r["doc_id"]] == "yes" for r in r306)}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

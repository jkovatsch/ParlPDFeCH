"""Sub-task S1 of the isolation in sub-tasks (stage 3, iteration of gate 3a, 08.10.2026): the document role.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: main agent (Claude Opus 5.5), workflow
sub-agent. Shared base: `m03_sub_common.py` (splits, families, labels, compose, measure, ask).

1 Task
  One decision for each document: the role S1 from the author families of its text atoms (`m03_sub_common.role_of`):
  proposal (only SPONSOR text), response (only EXECUTIVE text), combined (SPONSOR and EXECUTIVE), minutes (PLENARY
  text), committee (COMMITTEE text), other (no author text). The reference is the S1 label of ref41 or pool_ref41
  (dev, eval) or of the gold record (gold split).

2 Variants
  meta     comparison only (not a method): the field dokumentrolle of daten/iso/gruppen.csv and pool.csv,
           mapped to the most frequent dev role of each value. dokumentrolle is NOT a field of the export: it
           comes from the export category, the file name and a regular expression on the Tika text
           (`m03_lehrer_stichprobe.py`). Thus the rule does not use it.
  rule     a decision list (chapter 3) from the export fields of daten/analyse/pdf/docs_pdf_index.csv.gz
           (category_de, category_harmonized, name_klasse of the file name and category) and from keywords of
           the headings and the atom markers of `m03_atome.py`. Each decision has a reason (rule id). Designed on
           dev only. export_meta.json also keeps the type of the affair (affairs export); the rule does not use it.
  apertus  Apertus-v1.5-8B (CSCS), one constrained choice for each document (E19): the whole document, then
           the question (E18). The prompt is in src/prompts/s1_role.txt: [system] (the 6 categories with their
           definitions), [question] (short, last), [choices] (role = German word; each word has its own first
           token, so one request gives the distribution over the 6 roles), [shots] (role = dev document,
           alternate dev document; one example for each role, the alternate when the target is the example).
           Each tried prompt version is kept in daten/iso/sub/s1_role/prompts/<sha>.txt.
  combined rule where it is sure, Apertus elsewhere (chapter 4b). Chosen on dev only.

3 Rule (decision list, the first rule that applies wins; ids in brackets)
  Features: the body atoms (atoms without a fixed answer of E20 chapter 3, not a picture, not empty); the heads
  (atoms with the Docling form heading or title, and short atoms of 1 or 2 lines with at most 90 characters in
  the first 15 body atoms); the answer marks (a Docling heading with an answer word; a short head that starts
  with an answer word; an atom with the marker keyword "response"; an atom with the marker "answer_reference"
  that is not an affair number "ad 22.159"; not a consultation "Stellungnahme zur Verordnung ..."); the block
  marks of a sponsor text anywhere in the document (markers intro_questions, demand_formula, keyword reasoning,
  recall or demand, a head "Wortlaut", "Texte du postulat", "Enoncé", "Testo dell'"); the sponsor marks before
  the first answer mark (affair_type, intro_questions, demand_formula, question_number, keyword reasoning,
  recall, questions, demand).
  [O1]  other: category_harmonized government_resolution, or a head "Regierungsratsbeschluss vom".
  [O2]  other: the first head names a kind without author text (statutes, regulation, ordinance, fact sheet,
        handbook, attachment, consultation, account, tariff, list of pending affairs), or name_klasse "beilage".
  [M1]  minutes: in the first 20 body atoms, a protocol word with a parliament word in the atoms around it
        (2 before, 3 after) and no executive word there, or a head "Beschlusstext".
  [C1]  committee: a head in the first 20 body atoms names a committee (not "Standeskommission", not "an die
        ...kommission"), and there is no answer mark before it.
  [A1]  combined: answer marks, and at least 1 block mark, or the first answer mark at or after SPLIT_POS of
        the body atoms.
  [A2]  response: answer marks (else).
  [P1]  proposal: sponsor marks or an affair type line in the first 20 body atoms, no answer mark.
  [P2]  proposal: export category_harmonized submitted_text or proposal, or name_klasse vorstoss.
  [E1]  proposal: a proposal or report of the executive to the parliament (E20 C1: "Antrag des Stadtrates",
        "Bericht und Antrag", "Botschaft", "Weisung", "Rapport du Conseil communal").
  [R1]  response: export category_harmonized response_text, a category with an answer word, or name_klasse antwort.
  [D0]  other: no rule applies.

4 Measurement (for each split and variant)
  a) accuracy with the one-sided 95 % Jeffreys lower bound, macro F1 over the roles of the reference, recall and
  precision of each role, the confusion matrix. Effect on the composed answers ("role only"): compose with the
  predicted S1, an empty S2 and the reference S3, S4, S5 (the role alone sets the author of all body text),
  measured with `m03_sub_common.measure`, next to the same with the reference S1. S1 changes the composed
  answers only when S2 is empty; this value shows how much of the isolation the role alone gives.
  b) combined: candidates (rule alone; sure_ids: the rule ids whose dev accuracy is at least the Apertus dev
  accuracy keep the rule, the others take Apertus; p_threshold t: Apertus where p >= t, else the rule). The
  candidate with the highest dev accuracy wins; the same choice goes to eval and gold. combine also writes
  sure = (rule id in sure_ids) into rule_<split>.json.

5 Outputs (daten/iso/sub/s1_role/)
  <variant>_<split>.json: {variant, split, version, metrics, documents: {doc_id: {role, sure, reason, probs, p,
  reference, correct, ...}}}; apertus: model, prompt_sha256, usage; combined: the selection on dev.
  apertus_sample48_<sha>_dev.json: the prompt versions on the stratified dev sample (48 documents, seed 20261008).
  export_meta.json: the export fields of each document (cache). The CSCS calls write daten/iso/sub/cscs_log.jsonl
  with the tag "s1_role:<prompt sha>".

6 Results (08.10.2026; prompt a458b4258d86; reference ref41/pool_ref41, gold split: gold records)
  rule      dev 0.721 (132/183), eval 0.773 (17/22), gold 2/2
  apertus   dev 0.508 (93/183), eval 0.591 (13/22), gold 2/2; it never gives "combined"
  combined  dev 0.727 (133/183; Apertus only for rule id R1), eval 0.773 (17/22), gold 2/2
  meta      dev 0.525 (96/183), eval 0.773 (17/22) (comparison only)
  The rule is designed on dev and the combined choice is made on dev: the dev values are optimistic.

Usage (in this order; a new "rule" run clears the sure flags until the next "combine"):
  uv run python src/m03_sub_s1_role.py rule                     (meta and rule on dev, eval, gold)
  uv run python src/m03_sub_s1_role.py design                   (dev only: rule ids and errors)
  uv run python src/m03_sub_s1_role.py apertus --split dev [--sample N] [--workers 4]
  uv run python src/m03_sub_s1_role.py combine                  (select on dev, apply to eval and gold)
"""

from __future__ import annotations

import concurrent.futures as cf
import csv
import gzip
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_sub_common as sc  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

ROOT = sc.ROOT
OUT = sc.SUB / "s1_role"
PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "s1_role.txt"
PDF_INDEX = ROOT / "daten/analyse/pdf/docs_pdf_index.csv.gz"
AFFAIRS = ROOT / "daten/roh/exports/affairs.ndjson.gz"
VERSION = "s1-role-1"
ROLES = sc.ROLES
SPLIT_POS = 0.15          # [A1]: first answer mark at or after this part of the body atoms -> combined
SAMPLE_SEED = 20261008

# ------------------------------------------------------------------ export fields

def export_meta(doc_ids: list[str] | None = None) -> dict[str, dict]:
    """Export fields of each document of dev, eval and gold (cache in OUT/export_meta.json)."""
    cache = OUT / "export_meta.json"
    sp = sc.splits()
    want = set(sp["dev"]) | set(sp["eval"]) | set(sp["gold"])
    if cache.exists():
        got = json.loads(cache.read_text(encoding="utf-8"))
        if want <= set(got):
            return got
    for d in want:
        sc._check_allowed_doc(d)
    idx = {}
    with gzip.open(PDF_INDEX, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["id"] in want:
                idx[r["id"]] = r
    affs = {r["affair_id"] for r in idx.values() if r["affair_id"]}
    aff = {}
    with gzip.open(AFFAIRS, "rt", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            if str(x["id"]) in affs:
                aff[str(x["id"])] = x
    out = {}
    for d in sorted(want, key=int):
        r = idx.get(d, {})
        a = aff.get(r.get("affair_id", ""), {})
        out[d] = {"category_de": r.get("category_de", ""), "category_harmonized": r.get("category_harmonized", ""),
                  "name_klasse": r.get("name_klasse", ""),
                  "affair_type_harmonized": a.get("type_harmonized_de") or "",
                  "affair_type": a.get("type_name_de") or a.get("type_name_fr") or a.get("type_name_it") or ""}
    OUT.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    return out


# ------------------------------------------------------------------ rule

RX_ANSWER = re.compile(r"\b(?:antwort|beantwortung|stellungnahme|r[ée]ponses?|risposta|r\s?i\s?s\s?p\s?o\s?s\s?t\s?a|"
                       r"pr[ée]avis|prise de position|presa di posizione)\b", re.I)
RX_ANSWER_START = re.compile(r"^(?:[\dIVX]{1,4}[.)]\s*|[A-Z]\)\s*)?" + RX_ANSWER.pattern, re.I)
RX_AFFAIR_NO = re.compile(r"^ad\s+\d+\.\d+", re.I)
RX_CONSULT = re.compile(r"stellungnahme\s+(?:zu[mr]?|des\s+datenschutz)\b(?!\s+(?:den\s+)?(?:antrag|vorstoss|motion|"
                        r"postulat|interpellation|anfrage))", re.I)
RX_GOV_RES = re.compile(r"^regierungsratsbeschluss\s+vom\b", re.I)
RX_OTHER_KIND = re.compile(
    r"^(?:statuten|reglement\b|verordnung|faktenblatt|handbuch|beilage|anhang|annexe|allegato|spartenrechnung|"
    r"vernehmlassung|vorabkonsultation|inhaltsverzeichnis|h[äa]ngige\s+motionen|tarif\b)", re.I)
RX_MIN_PROT = re.compile(r"(?:auszug\s+aus\s+dem\s+(?:substanziellen\s+|wort)?protokoll|protokollauszug|"
                         r"proc[èe]s-verbal|verbale)", re.I)
RX_PARLIAMENT = re.compile(r"einwohnerrat|ratssitzung|grossen?\s+gemeinderat|kantonsrat|grossen?\s+rat(?:es)?\b|landrat|"
                           r"conseil\s+g[ée]n[ée]ral|grand\s+conseil|consiglio\s+comunale|gran\s+consiglio", re.I)
RX_EXEC_PROT = re.compile(r"protokoll\s+(?:des\s+)?(?:stadtrat|regierungsrat|gemeinderat\s+von)|regierungsrat|"
                          r"conseil\s+d.[ée]tat|consiglio\s+di\s+stato", re.I)
RX_DECISION_TEXT = re.compile(r"^beschlusstext\b", re.I)
RX_COMMITTEE = re.compile(r"kommission|\brpk\b|\bgpk\b|interfraktionelle\s+konferenz|\bcommission\b", re.I)
RX_NOT_COMMITTEE = re.compile(r"standeskommission|\ban\s+die\s+\w*kommission", re.I)
RX_WORDING = re.compile(r"^(?:\d\.\s*)?(?:wortlaut|texte\s+du\s+(?:postulat|la\s+motion)|[ée]nonc[ée]|testo\s+dell|"
                        r"text\s+(?:des|der)\s+(?:postulat|motion|interpellation))", re.I)
RX_EXEC_PROPOSAL = re.compile(r"antrag\s+des\s+(?:stadtrat|gemeinderat|regierungsrat)|bericht\s+und\s+antrag|^botschaft\b|"
                              r"antrag\s+an\s+(?:den|das)\s+(?:gemeinderat|parlament|einwohnerrat|grossen\s+rat)|"
                              r"rapport\s+du\s+conseil\s+(?:communal|municipal)|^antrag\s+parlament\b|weisung\b", re.I)
SPONSOR_MARKS = {"affair_type", "intro_questions", "demand_formula", "question_number"}
SPONSOR_KEYWORDS = {"reasoning", "recall", "questions", "demand"}
BLOCK_MARKS = {"intro_questions", "demand_formula"}       # marks of a sponsor text block ([A1])
BLOCK_KEYWORDS = {"reasoning", "recall", "demand"}


def features(doc_id: str) -> dict:
    """Heading keywords and atom markers of one document (no reference)."""
    fixed = sc.load()[doc_id].fixed
    atoms = [a for a in sc.atoms(doc_id) if a["id"] not in fixed and a["label"] != "picture" and a["text"].strip()]
    lines_in_block = Counter(a["block"] for a in atoms)
    n = len(atoms)

    def is_head(i: int, a: dict) -> bool:
        if a["label"] in ("section_header", "title"):
            return True
        return i < 15 and lines_in_block[a["block"]] <= 2 and len(a["text"]) <= 90

    heads = [(i, a["text"].strip()) for i, a in enumerate(atoms) if is_head(i, a)]
    first_answer, sponsor_before, n_answer, n_block = None, 0, 0, 0
    for i, a in enumerate(atoms):
        mk = a.get("merkmale") or []
        kinds = {k for k, _ in mk}
        kws = {p for k, p in mk if k == "keyword"}
        head = is_head(i, a)
        t = a["text"].strip()
        docling_head = a["label"] in ("section_header", "title")
        answer = ("response" in kws or ("answer_reference" in kinds and not RX_AFFAIR_NO.match(t))
                  or (head and (RX_ANSWER.search(t) if docling_head else RX_ANSWER_START.match(t))
                      and not RX_CONSULT.search(t)))
        if answer:
            n_answer += 1
            if first_answer is None:
                first_answer = i
        if (kinds & BLOCK_MARKS) or (kws & BLOCK_KEYWORDS) or (head and RX_WORDING.search(a["text"])):
            n_block += 1
        if first_answer is None and ((kinds & SPONSOR_MARKS) or (kws & SPONSOR_KEYWORDS)):
            sponsor_before += 1
    protocol = False
    for i, a in enumerate(atoms[:20]):
        if RX_MIN_PROT.search(a["text"]):
            win = "\n".join(x["text"] for x in atoms[max(i - 2, 0): i + 4])
            if RX_PARLIAMENT.search(win) and not RX_EXEC_PROT.search(win):
                protocol = True
    committee_head = next((i for i, t in heads if i < 20 and RX_COMMITTEE.search(t) and not RX_NOT_COMMITTEE.search(t)), None)
    return {
        "n_body": n,
        "heads": [t for _, t in heads[:8]],
        "first_answer_index": first_answer,
        "first_answer_pos": round(first_answer / n, 3) if first_answer is not None and n else None,
        "n_answer_marks": n_answer,
        "n_block_marks": n_block,
        "sponsor_marks_before_answer": sponsor_before,
        "affair_type_line": any(k == "affair_type" for a in atoms[:20] for k, _ in (a.get("merkmale") or [])),
        "gov_resolution_head": any(RX_GOV_RES.search(t) for _, t in heads),
        "other_kind_head": bool(heads) and bool(RX_OTHER_KIND.search(heads[0][1])),
        "protocol_of_parliament": protocol,
        "decision_text_head": any(RX_DECISION_TEXT.search(t) for i, t in heads if i < 20),
        "committee_head_index": committee_head,
        "exec_proposal": any(RX_EXEC_PROPOSAL.search(t) for i, t in heads if i < 20),
    }


def rule(doc_id: str, meta: dict) -> dict:
    """The decision list of chapter 3: {role, reason}."""
    f = features(doc_id)
    m = meta.get(doc_id, {})
    harm, cat, nk = m.get("category_harmonized", ""), m.get("category_de", ""), m.get("name_klasse", "")

    def out(role: str, reason: str) -> dict:
        return {"role": role, "reason": reason, "features": f}

    if harm == "government_resolution" or f["gov_resolution_head"]:
        return out("other", "O1")
    if f["other_kind_head"] or nk == "beilage":
        return out("other", "O2")
    if f["protocol_of_parliament"] or f["decision_text_head"]:
        return out("minutes", "M1")
    ch = f["committee_head_index"]
    if ch is not None and (f["first_answer_index"] is None or ch < f["first_answer_index"]):
        return out("committee", "C1")
    if f["first_answer_pos"] is not None:
        if f["n_block_marks"] >= 1 or f["first_answer_pos"] >= SPLIT_POS:
            return out("combined", "A1")
        return out("response", "A2")
    if f["sponsor_marks_before_answer"] or f["affair_type_line"]:
        return out("proposal", "P1")
    if harm in ("submitted_text", "proposal") or nk == "vorstoss":
        return out("proposal", "P2")
    if f["exec_proposal"]:
        return out("proposal", "E1")
    if harm == "response_text" or RX_ANSWER.search(cat or "") or nk == "antwort":
        return out("response", "R1")
    return out("other", "D0")


META_MAP_SOURCE = "dev majority of dokumentrolle"


def meta_map(dev: list[str]) -> dict[str, str]:
    """dokumentrolle -> the most frequent dev role (ties: the role order of m03_sub_common.ROLES)."""
    c: dict[str, Counter] = defaultdict(Counter)
    for d in dev:
        c[sc.load()[d].meta_role][sc.doc_labels(d)["s1"]] += 1
    return {k: max(ROLES, key=lambda r: (v[r], -ROLES.index(r))) for k, v in c.items()}


# ------------------------------------------------------------------ Apertus

def load_prompt() -> dict:
    """[system], [question], [choices] (lines "role = Choice") of src/prompts/s1_role.txt."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    parts = dict(re.findall(r"^\[(\w+)\]\n(.*?)(?=^\[\w+\]\n|\Z)", text, re.S | re.M))
    choices = {}
    for line in parts["choices"].strip().splitlines():
        role, word = [x.strip() for x in line.split("=", 1)]
        choices[word] = role
    assert set(choices.values()) == set(ROLES), choices
    shots = []          # [(role, [doc_id, alternate doc_id])] in prompt order
    for line in (parts.get("shots") or "").strip().splitlines():
        role, ds = [x.strip() for x in line.split("=", 1)]
        shots.append((role, [x.strip() for x in ds.split(",")]))
    return {"system": parts["system"].strip(), "question": parts["question"].strip(), "choices": choices,
            "shots": shots, "sha256": hashlib.sha256(text.encode()).hexdigest()[:12]}


def shots_for(doc_id: str, prompt: dict) -> list[tuple[str, str, str]]:
    """Few-shot examples: dev documents with their reference role; the alternate when the target is the shot."""
    word = {r: w for w, r in prompt["choices"].items()}
    dev = set(sc.splits()["dev"])
    out = []
    for role, ds in prompt["shots"]:
        d = next(x for x in ds if x != doc_id)
        if d not in dev or reference(d, "dev") != role:
            raise ValueError(f"shot {d}: not a dev document with the reference role {role}")
        out.append((d, prompt["question"], word[role]))
    return out


def apertus(doc_id: str, prompt: dict) -> dict:
    words = list(prompt["choices"])
    r = sc.ask(doc_id, prompt["question"], choices=words, system=prompt["system"], tag=f"s1_role:{prompt['sha256']}",
               shots=shots_for(doc_id, prompt) or None)
    probs = {prompt["choices"][w]: p for w, p in r["probs"].items()}
    return {"role": prompt["choices"][r["answer"]], "p": probs[prompt["choices"][r["answer"]]], "probs": probs,
            "usage": r["usage"]}


# ------------------------------------------------------------------ measurement

def reference(doc_id: str, split: str) -> str:
    return sc.doc_labels(doc_id, "gold" if split == "gold" else "ref")["s1"]


def metrics(pred: dict[str, str], split: str, compose_effect: bool = True) -> dict:
    ids = list(pred)
    ref = {d: reference(d, split) for d in ids}
    n = len(ids)
    ok = sum(pred[d] == ref[d] for d in ids)
    conf: dict[str, Counter] = defaultdict(Counter)
    for d in ids:
        conf[ref[d]][pred[d]] += 1
    per, f1s = {}, []
    for r in ROLES:
        tp = conf[r][r]
        nr = sum(conf[r].values())
        npred = sum(conf[x][r] for x in conf)
        p = tp / npred if npred else None
        rc = tp / nr if nr else None
        f1 = 2 * p * rc / (p + rc) if p and rc else 0.0
        if nr:
            f1s.append(f1)
        per[r] = {"reference": nr, "predicted": npred, "precision": round(p, 3) if p is not None else None,
                  "recall": round(rc, 3) if rc is not None else None, "f1": round(f1, 3)}
    out = {"documents": n, "correct": ok, "accuracy": round(ok / n, 4) if n else None,
           "accuracy_lower95": v4.jeffreys_lower(ok, n), "macro_f1": round(sum(f1s) / len(f1s), 4) if f1s else None,
           "per_role": per, "confusion_ref_to_pred": {r: dict(conf[r]) for r in ROLES if conf[r]}}
    if compose_effect:
        src = "gold" if split == "gold" else "ref"
        hyp = {d: sc.oracle(d, src, s1=pred[d], s2=[]) for d in ids}
        hyp_ref = {d: sc.oracle(d, src, s2=[]) for d in ids}
        a = sc.measure(ids, hyp, src)
        b = sc.measure(ids, hyp_ref, src)
        keep = ("labelled_f1", "labelled_f1_lower", "text_class_error", "document_exact_rate")
        out["role_only_compose"] = {"predicted_s1": {k: a[k] for k in keep}, "reference_s1": {k: b[k] for k in keep}}
    return out


def write(variant: str, split: str, docs: dict[str, dict], extra: dict | None = None) -> dict:
    pred = {d: x["role"] for d, x in docs.items()}
    m = metrics(pred, split)
    for d, x in docs.items():
        x["reference"] = reference(d, split)
        x["correct"] = x["role"] == x["reference"]
    rec = {"variant": variant, "split": split, "version": VERSION, **(extra or {}), "metrics": m, "documents": docs}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{variant}_{split}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


def short(m: dict) -> str:
    rc = m.get("role_only_compose", {}).get("predicted_s1", {})
    return (f"acc {m['accuracy']} ({m['correct']}/{m['documents']}, lower95 {m['accuracy_lower95']}), "
            f"macro-F1 {m['macro_f1']}, role-only compose labelled F1 {rc.get('labelled_f1')}")


# ------------------------------------------------------------------ commands

def run_rule() -> None:
    sp = sc.splits()
    meta = export_meta()
    mm = meta_map(sp["dev"])
    for split in ("dev", "eval", "gold"):
        docs = {}
        for d in sp[split]:
            r = rule(d, meta)
            docs[d] = {"role": r["role"], "sure": None, "reason": r["reason"], "probs": None, "p": None,
                       "export": meta[d], "features": {k: v for k, v in r["features"].items() if k != "heads"}}
        m = write("rule", split, docs, {"split_pos": SPLIT_POS})
        print(f"rule {split}: {short(m)}")
        mdocs = {d: {"role": mm.get(sc.load()[d].meta_role, "other"), "sure": None,
                     "reason": f"dokumentrolle={sc.load()[d].meta_role}", "probs": None, "p": None} for d in sp[split]}
        m = write("meta", split, mdocs, {"map": mm, "map_source": META_MAP_SOURCE})
        print(f"meta {split}: {short(m)}")


def design() -> None:
    """Dev only: accuracy of each rule id and the errors."""
    sp = sc.splits()
    meta = export_meta()
    by = defaultdict(Counter)
    errs = []
    for d in sp["dev"]:
        r = rule(d, meta)
        ref = reference(d, "dev")
        by[r["reason"]][ref] += 1
        if r["role"] != ref:
            errs.append((r["reason"], ref, r["role"], d, r["features"]["heads"][:4]))
    for k in sorted(by):
        n = sum(by[k].values())
        print(k, n, dict(by[k].most_common()))
    for e in sorted(errs):
        print(e)
    pred = {d: rule(d, meta)["role"] for d in sp["dev"]}
    print(short(metrics(pred, "dev", compose_effect=False)))


def run_apertus(split: str, sample: int | None, workers: int) -> None:
    sp = sc.splits()
    prompt = load_prompt()
    ids = sp[split]
    if sample and sample < len(ids):
        ids = dev_sample(ids, sample) if split == "dev" else ids[:sample]
    docs, usage = {}, Counter()

    def one(d: str):
        return d, apertus(d, prompt)

    with cf.ThreadPoolExecutor(workers) as ex:
        for d, r in ex.map(one, ids):
            usage.update(r.pop("usage"))
            docs[d] = {"role": r["role"], "sure": None, "reason": "apertus", "probs": r["probs"], "p": r["p"]}
    docs = {d: docs[d] for d in ids}
    name = "apertus" + (f"_sample{len(ids)}_{prompt['sha256']}" if split == "dev" and len(ids) < len(sp[split]) else "")
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    (OUT / "prompts" / f"{prompt['sha256']}.txt").write_text(PROMPT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    m = write(name, split, docs, {"model": sc.MODEL, "prompt_sha256": prompt["sha256"], "usage": dict(usage)})
    print(f"{name} {split}: {short(m)}; usage {dict(usage)}")


def dev_sample(ids: list[str], n: int) -> list[str]:
    """Stratified by reference role (dev only), deterministic (SAMPLE_SEED)."""
    import random

    rng = random.Random(SAMPLE_SEED)
    by = defaultdict(list)
    for d in ids:
        by[reference(d, "dev")].append(d)
    for v in by.values():
        rng.shuffle(v)
    out, k = [], 0
    while len(out) < n:
        for r in ROLES:
            if k < len(by[r]) and len(out) < n:
                out.append(by[r][k])
        k += 1
    return sorted(out, key=lambda d: ids.index(d))


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "rule"
    args = sys.argv[2:]

    def opt(name: str, default=None):
        return args[args.index(name) + 1] if name in args else default

    if cmd == "rule":
        run_rule()
    elif cmd == "design":
        design()
    elif cmd == "apertus":
        s = opt("--sample")
        run_apertus(opt("--split", "dev"), int(s) if s else None, int(opt("--workers", "4")))
    elif cmd == "combine":
        combine()
    else:
        raise SystemExit(__doc__)


P_GRID = (0.9, 0.95, 0.99, 0.999, 1.0)


def combine() -> None:
    """Rule where it is sure, Apertus elsewhere. All choices on dev only; then the same choice on eval and gold.

    Candidates: (a) sure_ids: the rule ids whose dev accuracy is at least the Apertus dev accuracy on the same
    documents keep the rule, the other ids take Apertus; (b) p_threshold t: Apertus where its probability is
    at least t, else the rule. The candidate with the highest dev accuracy wins (ties: higher dev macro F1,
    then fewer Apertus decisions). The rule alone is a candidate too (no Apertus).
    """
    sp = sc.splits()
    splits = ("dev", "eval", "gold")
    rule_f = {s_: json.loads((OUT / f"rule_{s_}.json").read_text(encoding="utf-8")) for s_ in splits}
    ap_f = {s_: json.loads((OUT / f"apertus_{s_}.json").read_text(encoding="utf-8")) for s_ in splits}
    R = {s_: rule_f[s_]["documents"] for s_ in splits}
    A = {s_: ap_f[s_]["documents"] for s_ in splits}
    by = defaultdict(lambda: [0, 0, 0])
    for d in sp["dev"]:
        k = R["dev"][d]["reason"]
        by[k][0] += 1
        by[k][1] += R["dev"][d]["correct"]
        by[k][2] += A["dev"][d]["correct"]
    sure_ids = sorted(k for k, (n, rc, ac) in by.items() if rc >= ac)
    per_id = {k: {"documents": n, "rule_correct": rc, "apertus_correct": ac} for k, (n, rc, ac) in sorted(by.items())}

    def decide(split: str, kind: str, t: float | None) -> dict[str, dict]:
        out = {}
        for d in sp[split]:
            r, a = R[split][d], A[split][d]
            sure = r["reason"] in sure_ids
            use_ap = (not sure) if kind == "sure_ids" else (kind == "p_threshold" and a["p"] >= t)
            src = a if use_ap else r
            out[d] = {"role": src["role"], "source": "apertus" if use_ap else "rule", "sure": sure,
                      "reason": r["reason"], "rule_role": r["role"], "apertus_role": a["role"],
                      "probs": a["probs"], "p": a["p"]}
        return out

    cands = [("rule_only", None), ("sure_ids", None)] + [("p_threshold", t) for t in P_GRID]
    table = []
    for kind, t in cands:
        dd = decide("dev", kind, t)
        m = metrics({d: x["role"] for d, x in dd.items()}, "dev", compose_effect=False)
        n_ap = sum(x["source"] == "apertus" for x in dd.values())
        table.append({"kind": kind, "t": t, "dev_accuracy": m["accuracy"], "dev_macro_f1": m["macro_f1"],
                      "dev_apertus_decisions": n_ap})
    best = max(table, key=lambda x: (x["dev_accuracy"], x["dev_macro_f1"], -x["dev_apertus_decisions"]))
    sel = {"selection_on": "dev only", "sure_ids": sure_ids, "per_rule_id_dev": per_id, "candidates_dev": table,
           "chosen": {"kind": best["kind"], "t": best["t"]}, "apertus_prompt_sha256": ap_f["dev"]["prompt_sha256"]}
    for split in splits:
        dd = decide(split, best["kind"], best["t"])
        m = write("combined", split, dd, sel)
        print(f"combined {split}: {short(m)} ({best['kind']} t={best['t']}, apertus decisions "
              f"{sum(x['source'] == 'apertus' for x in dd.values())})")
        for d, x in R[split].items():
            x["sure"] = x["reason"] in sure_ids
        rule_f[split]["sure_ids"] = sure_ids
        rule_f[split]["sure_basis"] = "rule ids with dev accuracy >= Apertus dev accuracy (combine)"
        (OUT / f"rule_{split}.json").write_text(json.dumps(rule_f[split], ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"sure_ids": sure_ids, "per_rule_id_dev": per_id, "candidates_dev": table}, indent=1))


if __name__ == "__main__":
    main()

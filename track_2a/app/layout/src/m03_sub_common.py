"""Isolation in sub-tasks (stage 3, iteration of gate 3a, 08.10.2026): the shared module.

Context: gate 3a (isolation, E20) is NOT MET. The readout of the 13 answers of each atom over the whole
document gave a labelled boundary F1 of 0.315 (OOF) and 0.455 (group 7). The main error is a whole
block with the wrong author (response <-> submitted). Jonathan asked (08.10.2026) to break the task into
small problems that Apertus-8B can solve. This module is the shared base to measure the feasibility of
that split. Written in English to the STE rules (ASD-STE100, Issue 9). Actor: main agent (Claude Opus 5.5),
workflow sub-agent.

1 Loading (`load`)
  The E20 answers (version 4.1 measurement, `m03_iso_v4.py`) of each document of groups 1 to 6
  (daten/iso/v4/ref41), of the pool (daten/iso/v4/pool_ref41) and of the 5 human gold records
  (daten/gold/records/review/<doc>/provenance.yaml, answers by `m03_gold_record.derive`). A gold record
  is a review record with `review_run.datetime_finished` (the record 877101 is an editor test of the main
  agent without this field: it is not a gold record). Each document has its atoms, its group, its
  parliament and its triage result (daten/iso/triage.csv, `final`).
  The module never loads a document of group 7, a file of daten/iso/v4/final_*, a test document
  (daten/gold/test, process rule 6) or a document of a test parliament (split.csv role "Gold"). It reads
  only the ids and the parliaments of group 7 from gruppen.csv, to refuse and exclude them.

2 Splits (`splits`)
  dev     rule and prompt design. The pool and groups 1 to 3, without:
          - documents of a parliament of group 7 (gate-3a criteria, chapter 1, item 2: no method learns
            from these documents; they stay "readout only"),
          - with parliament_disjoint=True (default): pool documents of a parliament of groups 4 to 6
            (the pool rule of `m03_iso_pool.py`: a method that is measured on group g learns only from
            documents of other parliaments).
  eval    groups 4 to 6 (all documents, also of group 7 parliaments: measurement only).
  gold    the gold records that are not in the pool and not in groups 1 to 3: 549658 (group 4) and
          368972 (group 5). Their reference is the gold record (K8, clarifications C8 to C13), not ref41.
          The gold records 879163 (group 1), 375917 and 465245 (group 2) are dev documents.
  readout_only  dev candidates that rule design must not use (see above).
  pass_only=True (default) keeps only documents with triage PASS (only these can go to CSCS).

3 Author families (decision of this module, from the 13 answers of E20 version 4.2)
  TITLE      title, short_title             Affair.title; no author
  SPONSOR    submitted, reasoning           Submission.texts
  EXECUTIVE  response, recommendation       ResponseStep.texts
  COMMITTEE  committee_recommendation       CommitteeDecision.text
  PLENARY    speech, proposition, vote      PlenaryDebate events
  SUMMARY    summary                        own family (see below)
  FRAME      none                           no text field
  FURNITURE  furniture                      only by the fixed rules R1, R4, R5 (E20 chapter 3)
  SUMMARY is its own family. E20 (chapter 2) puts a summary into "the texts of the step of its author",
  and the gold record maps both Submission.texts/summary and ResponseStep.texts/summary to the one answer
  "summary" (`m03_gold_record.ANSWER`). Thus the answer does not tell the author. In dev, the two
  documents with a summary have different authors: 176319 (summary of the executive, "Der Stadtrat
  erachtet ...") and 175889 ("Zusammenfassung der Frage": the question of the sponsor). A map to SPONSOR
  or EXECUTIVE would be wrong for one of them, and compose could not give the answer back.
  Default type of a family (the most frequent type in dev): TITLE title, SPONSOR submitted, EXECUTIVE
  response, PLENARY vote, COMMITTEE committee_recommendation, SUMMARY summary.

4 Sub-task labels (`labels`)
  S1 document role: from the author families of the text atoms (TITLE is not an author):
       PLENARY -> minutes; else COMMITTEE -> committee; else SPONSOR and EXECUTIVE -> combined;
       else SPONSOR -> proposal; else EXECUTIVE -> response; else (no author text, or SUMMARY only) -> other.
  S2 author switch points: the sequence of the text atoms that are not TITLE ("body"), in atom order,
     with footnotes and captions. S2 is a list of runs [(first atom id, family), ...]: the first entry
     gives the family at the start of the body, each next entry is a switch (the family after it).
     TITLE boundaries are not in S2: S4 gives them (37 of 62 boundaries of groups 1 to 5 start after the
     title, E20 chapter 5). A predicted switch at any atom after the last text atom of the old family,
     up to the first text atom of the new family, composes to the same answers.
  S3 frame or text: {atom id: "text" | "frame"}; frame = none or furniture. The fixed answers of E20
     chapter 3 (`m03_iso_v4.fixed_answers`) decide furniture and R3 none; compose applies them always.
     Check (08.10.2026): in ref41 and pool_ref41, each furniture atom has a fixed rule, and each atom with
     a fixed rule has its fixed answer.
  S4 title atoms: the atom ids of the TITLE family (title and short_title), in atom order.
  S5 type inside a family: {atom id: answer} for the text atoms of the families with more than one type
     (TITLE, SPONSOR, EXECUTIVE, PLENARY).

5 Composition and measurement
  compose(doc, s1, s2, s3, s4, s5) -> the 13 answers of each atom:
     fixed answer if the atom has one; else none if S3 is not "text"; else the family (TITLE if the atom
     is in S4, else the family of the last S2 entry at or before the atom; before the first entry: the
     family of the first entry; with an empty S2: the default family of the role S1); then the type from
     S5 if it is a type of that family, else the default type of the family. S1 changes the answers only
     when S2 is empty. strict=True: the role of the composed answers must be S1 (else ValueError).
  measure(docs, answers, reference) -> the values of `m03_iso_v4.compare_docs` (labelled boundary F1 with
     the Jeffreys lower bound, omission, intrusion, class error, document exact rate).
  oracle(doc_id, **override) -> compose with the reference labels, except the given sub-task labels:
     the effect of one predicted sub-task on the measurement.
  Check (the test, `m03_sub_common_test.py`): compose(labels of the reference) gives each reference back.

6 CSCS (`ask`)
  ask(doc_id, question, choices=... | regex=...) -> the answer and its probabilities. Built on
  `m04_iso_cscs.py`: the key from .env.cscs (never printed, never logged); the prompt with the chat template
  of the local tokenizer (daten/modelle/apertus-v1.5-8b-text-bf16), sent as token ids to /v1/completions;
  model swiss-ai/Apertus-v1.5-8B (the model of the submission); temperature 0; the output constrained by
  structured_outputs (E19: no free text). Message: system (short role), then user: "Dokument:\\n" + the whole
  document (daten/iso/atome_prompt/<doc>.txt) + the question at the end (E18).
  Probabilities of a choice: the server gives the log probabilities of the constrained step (top 20). The
  mass of each allowed token goes to the choices whose text starts with the output text so far plus the
  token. A token that two or more choices share is followed on the generated path, or with one more
  request when its mass is >= 0.001 (else its mass is split equally). Choices with distinct first tokens
  need one request. The values are renormalized over the allowed tokens at each step.
  Refusal (ValueError, before any network call): a document that is not in groups 1 to 6 and not in the
  pool, a document of group 7, a test document or a document of a test parliament, a document without
  triage PASS (process rule 13.3). Few-shot examples (shots) must be dev documents.
  Each call writes one line to daten/iso/sub/cscs_log.jsonl (tokens for the cost record, rule 13.5) and
  keeps the raw response in daten/iso/sub/cscs_cache/ (a repeated identical request reads the cache).

Usage:
  uv run python src/m03_sub_common.py summary          (split sizes and label counts -> daten/iso/sub/)
  uv run python src/m03_sub_common.py ask DOC "QUESTION" --choices a,b,c
"""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import TEST, iso_path  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "daten/iso/sub"
REF41 = ROOT / "daten/iso/v4/ref41"
POOL41 = ROOT / "daten/iso/v4/pool_ref41"
GROUPS_CSV = ROOT / "daten/iso/gruppen.csv"
POOL_CSV = ROOT / "daten/iso/pool.csv"
TRIAGE_CSV = ROOT / "daten/iso/triage.csv"
SPLIT_CSV = ROOT / "daten/analyse/synthese/split.csv"
GOLD_REVIEW = ROOT / "daten/gold/records/review"
PROMPTS = ROOT / "daten/iso/atome_prompt"
VERSION = "sub-common-1"

DEV_GROUPS = ("1", "2", "3")
EVAL_GROUPS = ("4", "5", "6")
FINAL_GROUP = "7"

# ------------------------------------------------------------------ families

FAMILY = {
    "title": "TITLE", "short_title": "TITLE",
    "submitted": "SPONSOR", "reasoning": "SPONSOR",
    "response": "EXECUTIVE", "recommendation": "EXECUTIVE",
    "committee_recommendation": "COMMITTEE",
    "speech": "PLENARY", "proposition": "PLENARY", "vote": "PLENARY",
    "summary": "SUMMARY",
    "none": "FRAME",
    "furniture": "FURNITURE",
}
assert set(FAMILY) == set(v4.ANSWERS)
TEXT_FAMILIES = ("TITLE", "SPONSOR", "EXECUTIVE", "COMMITTEE", "PLENARY", "SUMMARY")
AUTHOR_FAMILIES = ("SPONSOR", "EXECUTIVE", "COMMITTEE", "PLENARY", "SUMMARY")
MEMBERS = {f: tuple(a for a in v4.ANSWERS if FAMILY[a] == f) for f in TEXT_FAMILIES}
MULTI_TYPE = tuple(f for f in TEXT_FAMILIES if len(MEMBERS[f]) > 1)
DEFAULT_TYPE = {"TITLE": "title", "SPONSOR": "submitted", "EXECUTIVE": "response",
                "COMMITTEE": "committee_recommendation", "PLENARY": "vote", "SUMMARY": "summary"}
ROLES = ("proposal", "response", "combined", "minutes", "committee", "other")
ROLE_DEFAULT_FAMILY = {"proposal": "SPONSOR", "response": "EXECUTIVE", "combined": "SPONSOR",
                       "minutes": "PLENARY", "committee": "COMMITTEE", "other": "SPONSOR"}


def family(answer: str) -> str:
    return FAMILY[answer]


def role_of(families) -> str:
    """S1: the document role from the families of the text atoms (TITLE is not an author)."""
    a = set(families) & set(AUTHOR_FAMILIES)
    if "PLENARY" in a:
        return "minutes"
    if "COMMITTEE" in a:
        return "committee"
    if {"SPONSOR", "EXECUTIVE"} <= a:
        return "combined"
    if "SPONSOR" in a:
        return "proposal"
    if "EXECUTIVE" in a:
        return "response"
    return "other"


# ------------------------------------------------------------------ loading

def _read_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def _protected() -> tuple[frozenset, frozenset, frozenset]:
    """(doc ids of group 7, parliaments of group 7, test parliaments). Only ids and parliament keys."""
    g7 = [r for r in _read_csv(GROUPS_CSV) if r["group"] == FINAL_GROUP]
    test_parl = {r["body_key"] for r in _read_csv(SPLIT_CSV) if r["rolle"] == "Gold"}
    return frozenset(r["doc_id"] for r in g7), frozenset(r["body_key"] for r in g7), frozenset(test_parl)


@lru_cache(maxsize=1)
def triage() -> dict[str, str]:
    return {r["doc_id"]: r["final"] for r in _read_csv(TRIAGE_CSV)}


def is_test_document(doc_id: str) -> bool:
    return iso_path("atome", doc_id).is_relative_to(TEST)


@dataclass
class Doc:
    doc_id: str
    kind: str              # "group" or "pool"
    group: str             # "1" ... "6", or "pool"
    home: str              # group of the parliament (pool.csv "home"; for a group document: its group)
    body_key: str
    language: str
    meta_role: str         # dokumentrolle of the metadata (not reliable, E20 chapter 8)
    triage: str            # PASS, FAIL or "" (no triage)
    ids: list[str]
    ref: list[str]         # E20 answers of ref41 or pool_ref41
    gold: list[str] | None = None   # E20 answers of the gold record (review), if one exists
    g7_parliament: bool = False
    eval_parliament: bool = False
    fixed: dict[str, str] = field(default_factory=dict)


def _ref_answers(path: Path, doc_id: str) -> tuple[list[str], list[str]]:
    ids = [a["id"] for a in v4.atoms_of(doc_id)]
    return ids, v4.load_answers(path, doc_id, ids)


def gold_record_ids() -> list[str]:
    """The human gold records: review records with review_run.datetime_finished."""
    import yaml

    out = []
    for d in sorted(p.name for p in GOLD_REVIEW.iterdir() if p.is_dir()):
        prov = GOLD_REVIEW / d / "provenance.yaml"
        if not prov.exists() or is_test_document(d):
            continue
        rr = (yaml.safe_load(prov.read_text(encoding="utf-8")) or {}).get("review_run") or {}
        if rr.get("datetime_finished"):
            out.append(d)
    return out


def gold_answers(doc_id: str) -> list[str]:
    import yaml
    import m03_gold_record as gr

    _check_allowed_doc(doc_id)
    prov = yaml.safe_load((GOLD_REVIEW / doc_id / "provenance.yaml").read_text(encoding="utf-8"))
    return gr.derive(doc_id, prov)


@lru_cache(maxsize=1)
def load() -> dict[str, Doc]:
    """All documents of groups 1 to 6 and of the pool with a reference, with the gold answers if any."""
    g7_ids, g7_parl, test_parl = _protected()
    grp = [r for r in _read_csv(GROUPS_CSV) if r["group"] != FINAL_GROUP]
    eval_parl = {r["body_key"] for r in grp if r["group"] in EVAL_GROUPS}
    tri = triage()
    docs: dict[str, Doc] = {}
    for r in grp:
        d = r["doc_id"]
        ids, ref = _ref_answers(REF41 / f"{d}.json", d)
        docs[d] = Doc(d, "group", r["group"], r["group"], r["body_key"], r["sprache"], r["dokumentrolle"],
                      tri.get(d, ""), ids, ref, None, r["body_key"] in g7_parl, r["body_key"] in eval_parl)
    for r in _read_csv(POOL_CSV):
        d = r["doc_id"]
        p = POOL41 / f"{d}.json"
        if not p.exists():
            continue
        assert d not in docs, d
        ids, ref = _ref_answers(p, d)
        docs[d] = Doc(d, "pool", "pool", r["home"], r["body_key"], r["sprache"], r["dokumentrolle"],
                      tri.get(d, ""), ids, ref, None, r["body_key"] in g7_parl, r["body_key"] in eval_parl)
    for d in gold_record_ids():
        if d not in docs:
            raise SystemExit(f"gold record {d} is not a document of groups 1 to 6 or of the pool")
        docs[d].gold = gold_answers(d)
    for d, x in docs.items():
        if d in g7_ids:
            raise SystemExit(f"{d}: group 7 document in the loaded set")
        if x.body_key in test_parl or is_test_document(d):
            raise SystemExit(f"{d}: test document or document of a test parliament (process rule 6)")
        x.fixed = v4.fixed_answers(d)
    return docs


def atoms(doc_id: str) -> list[dict]:
    _check_allowed_doc(doc_id)
    return v4.atoms_of(doc_id)


def splits(pass_only: bool = True, parliament_disjoint: bool = True) -> dict[str, list[str]]:
    docs = load()
    keep = (lambda x: x.triage == "PASS") if pass_only else (lambda x: True)
    dev, readout = [], []
    for d, x in docs.items():
        if not (x.kind == "pool" or x.group in DEV_GROUPS) or not keep(x):
            continue
        if x.g7_parliament or (parliament_disjoint and x.kind == "pool" and x.eval_parliament):
            readout.append(d)
        else:
            dev.append(d)
    ev = [d for d, x in docs.items() if x.kind == "group" and x.group in EVAL_GROUPS and keep(x)]
    gold = [d for d, x in docs.items() if x.gold is not None and x.kind == "group"
            and x.group not in DEV_GROUPS and keep(x)]
    key = lambda d: (docs[d].group, int(d))  # noqa: E731
    return {"dev": sorted(dev, key=key), "eval": sorted(ev, key=key), "gold": sorted(gold, key=key),
            "readout_only": sorted(readout, key=key)}


def reference(doc_id: str, source: str = "ref") -> list[str]:
    """source "ref": ref41 or pool_ref41; "gold": the answers of the gold record."""
    x = load()[doc_id]
    if source == "gold":
        if x.gold is None:
            raise KeyError(f"{doc_id} has no gold record")
        return x.gold
    return x.ref


# ------------------------------------------------------------------ sub-task labels

def labels(ids: list[str], answers: list[str]) -> dict:
    """The labels S1 to S5 of one document from its 13 answers."""
    text = [(a, x) for a, x in zip(ids, answers) if x in v4.TEXT]
    s3 = {a: ("text" if x in v4.TEXT else "frame") for a, x in zip(ids, answers)}
    s4 = [a for a, x in text if FAMILY[x] == "TITLE"]
    s2: list[tuple[str, str]] = []
    for a, x in text:
        f = FAMILY[x]
        if f != "TITLE" and (not s2 or s2[-1][1] != f):
            s2.append((a, f))
    s5 = {a: x for a, x in text if FAMILY[x] in MULTI_TYPE}
    s1 = role_of(FAMILY[x] for _, x in text)
    return {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5}


def doc_labels(doc_id: str, source: str = "ref") -> dict:
    x = load()[doc_id]
    return labels(x.ids, reference(doc_id, source))


def compose(doc, s1: str, s2, s3: dict, s4, s5: dict, strict: bool = False) -> list[str]:
    """The 13 answers of each atom from the sub-task labels (rules in chapter 5 of the docstring)."""
    x = doc if isinstance(doc, Doc) else load()[str(doc)]
    pos = {a: i for i, a in enumerate(x.ids)}
    runs = sorted(((pos[a], f) for a, f in (s2 or [])), key=lambda t: t[0])
    for _, f in runs:
        if f not in AUTHOR_FAMILIES:
            raise ValueError(f"S2 family {f!r} is not an author family {AUTHOR_FAMILIES}")
    starts = [p for p, _ in runs]
    title = set(s4 or [])
    s5 = s5 or {}
    out = []
    for i, a in enumerate(x.ids):
        if a in x.fixed:
            out.append(x.fixed[a])
            continue
        if s3.get(a) != "text":
            out.append("none")
            continue
        if a in title:
            fam = "TITLE"
        elif runs:
            k = bisect.bisect_right(starts, i) - 1
            fam = runs[max(k, 0)][1]
        else:
            fam = ROLE_DEFAULT_FAMILY.get(s1, "SPONSOR")
        t = s5.get(a)
        out.append(t if t in MEMBERS[fam] else DEFAULT_TYPE[fam])
    if strict:
        got = role_of(FAMILY[y] for y in out if y in v4.TEXT)
        if got != s1:
            raise ValueError(f"{x.doc_id}: role of the composed answers {got!r} != S1 {s1!r}")
    return out


def oracle(doc_id: str, source: str = "ref", **override) -> list[str]:
    """compose with the reference labels, except the given labels (s1=..., s2=..., ...)."""
    lab = doc_labels(doc_id, source)
    lab.update(override)
    return compose(doc_id, lab["s1"], lab["s2"], lab["s3"], lab["s4"], lab["s5"])


def label_counts(doc_ids: list[str], source: str = "ref") -> dict:
    s1, s2_start, s2_pair, s5_type, s5_switch = Counter(), Counter(), Counter(), Counter(), Counter()
    n_switch = docs_switch = text = frame = furn = fixed_none = title_atoms = docs_title = docs_title_runs = 0
    for d in doc_ids:
        x = load()[d]
        ans = reference(d, source)
        lab = labels(x.ids, ans)
        s1[lab["s1"]] += 1
        if lab["s2"]:
            s2_start[lab["s2"][0][1]] += 1
        for (_, f0), (_, f1) in zip(lab["s2"], lab["s2"][1:]):
            s2_pair[f"{f0}>{f1}"] += 1
        n_switch += max(len(lab["s2"]) - 1, 0)
        docs_switch += len(lab["s2"]) > 1
        text += sum(v == "text" for v in lab["s3"].values())
        frame += sum(v == "frame" for v in lab["s3"].values())
        furn += ans.count("furniture")
        fixed_none += sum(1 for a in x.ids if x.fixed.get(a) == "none")
        title_atoms += len(lab["s4"])
        docs_title += bool(lab["s4"])
        tset = set(lab["s4"])
        seq = [a for a, v in zip(x.ids, ans) if v in v4.TEXT]
        runs = sum(1 for i, a in enumerate(seq) if a in tset and (i == 0 or seq[i - 1] not in tset))
        docs_title_runs += runs > 1
        s5_type.update(lab["s5"].values())
        prev = None
        for a in seq:
            t = lab["s5"].get(a)
            f = FAMILY[t] if t else None
            if prev and t and FAMILY[prev] == f and prev != t:
                s5_switch[f"{prev}>{t}"] += 1
            prev = t if t else None
    return {
        "documents": len(doc_ids),
        "S1_role": dict(s1.most_common()),
        "S2": {"documents_with_body_text": sum(s2_start.values()), "start_family": dict(s2_start.most_common()),
               "switches": n_switch, "documents_with_switch": docs_switch, "switch_pairs": dict(s2_pair.most_common())},
        "S3": {"text_atoms": text, "frame_atoms": frame, "of_which_furniture": furn, "of_which_fixed_none_R3": fixed_none},
        "S4": {"title_atoms": title_atoms, "documents_with_title": docs_title,
               "documents_with_more_than_one_title_run": docs_title_runs},
        "S5": {"atoms_by_type": dict(s5_type.most_common()), "type_switches_inside_family": dict(s5_switch.most_common())},
    }


# ------------------------------------------------------------------ measurement

def measure(doc_ids: list[str], answers: dict[str, list[str]], reference_source: str = "ref",
            missing_as_none: bool = False) -> dict:
    """The values of m03_iso_v4.compare_docs (measurement 4.1) for method answers against the reference."""
    docs = load()
    for d in doc_ids:
        _check_allowed_doc(d)
    SUB.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SUB, prefix="measure_") as tmp:
        rdir, hdir = Path(tmp) / "ref", Path(tmp) / "hyp"
        for d in doc_ids:
            v4.write(rdir, d, reference(d, reference_source), "reference", f"m03_sub_common {reference_source}")
            if d in answers:
                if len(answers[d]) != len(docs[d].ids):
                    raise ValueError(f"{d}: {len(answers[d])} answers for {len(docs[d].ids)} atoms")
                v4.write(hdir, d, list(answers[d]), "method", "m03_sub_common")
        hdir.mkdir(parents=True, exist_ok=True)
        return v4.compare_docs(rdir, hdir, list(doc_ids), missing_as_none)


# ------------------------------------------------------------------ CSCS

MODEL = "swiss-ai/Apertus-v1.5-8B"
SYSTEM_ASK = "Du liest ein Dokument aus einem Schweizer Parlament und beantwortest eine Frage dazu."
TOP = 20
SPLIT_MASS = 1e-3
_LOCK = threading.Lock()
_TOK = None


@lru_cache(maxsize=1)
def _body_keys() -> dict[str, str]:
    """Parliament of each document of groups 1 to 6 and of the pool."""
    out = {r["doc_id"]: r["body_key"] for r in _read_csv(GROUPS_CSV) if r["group"] != FINAL_GROUP}
    out.update({r["doc_id"]: r["body_key"] for r in _read_csv(POOL_CSV)})
    return out


def _check_allowed_doc(doc_id: str) -> None:
    g7_ids, _, test_parl = _protected()
    if doc_id in g7_ids:
        raise ValueError(f"{doc_id}: group 7 document (final group): refused")
    if doc_id not in _body_keys():
        raise ValueError(f"{doc_id}: not a document of groups 1 to 6 or of the pool: refused")
    if is_test_document(doc_id):
        raise ValueError(f"{doc_id}: test document (process rule 6): refused")
    if _body_keys()[doc_id] in test_parl:
        raise ValueError(f"{doc_id}: document of a test parliament (process rule 6): refused")


def check_cscs(doc_id: str) -> None:
    """ValueError if the document must not go to CSCS."""
    doc_id = str(doc_id)
    _check_allowed_doc(doc_id)
    if triage().get(doc_id) != "PASS":
        raise ValueError(f"{doc_id}: triage is not PASS (process rule 13.3): refused")


def tokenizer():
    global _TOK
    with _LOCK:
        if _TOK is None:
            import m03_iso_jev as jev
            from mlx_lm.utils import load_tokenizer

            _TOK = load_tokenizer(jev.MODEL)
    return _TOK


def document_text(doc_id: str) -> str:
    check_cscs(doc_id)
    return "Dokument:\n" + (PROMPTS / f"{doc_id}.txt").read_text(encoding="utf-8")


def prompt_ids(doc_id: str, question: str, system: str = SYSTEM_ASK, assistant_prefix: str = "",
               shots: list[tuple[str, str, str]] | None = None) -> list[int]:
    """Chat template of the local tokenizer: system, [shots], user = whole document + question (E18)."""
    tok = tokenizer()
    dev = set(splits(pass_only=True)["dev"])
    msgs = [{"role": "system", "content": system}]
    for sd, sq, sa in shots or []:
        if sd not in dev or sd == doc_id:
            raise ValueError(f"shot {sd}: only dev documents (not the target) can be examples")
        msgs += [{"role": "user", "content": document_text(sd) + "\n\n" + sq},
                 {"role": "assistant", "content": sa}]
    msgs.append({"role": "user", "content": document_text(doc_id) + "\n\n" + question})
    ids = list(tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, return_dict=False))
    if assistant_prefix:
        ids += tok.encode(assistant_prefix, add_special_tokens=False)
    return ids


def _env() -> tuple[str, dict]:
    import m04_iso_cscs as cs

    e = cs.env()
    return (e["CSCS_BASE_URL"].rstrip("/") + "/completions",
            {"Authorization": "Bearer " + e["CSCS_API_KEY"], "Content-Type": "application/json"})


def _post(body: dict) -> tuple[dict, bool]:
    """One request with the retry rules of m04_iso_cscs (fewer top tokens after HTTP 500). Cached."""
    key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    cache = SUB / "cscs_cache" / f"{key}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8")), True
        except ValueError:
            pass   # an unreadable cache file (defect fix 08.10.2026: concurrent writes) counts as a miss
    url, headers = _env()
    ladder = [20, 13, 10, 8, 5]
    body = dict(body)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=900) as resp:
                res = json.loads(resp.read())
            break
        except Exception as ex:  # noqa: BLE001
            msg = str(ex)[:200]
            if isinstance(ex, urllib.error.HTTPError):
                msg += " " + ex.read().decode(errors="replace")[:200]
            if attempt == 5:
                raise RuntimeError(f"CSCS request failed: {msg}") from None
            if "500" in msg and body.get("logprobs") in ladder[:-1]:
                body["logprobs"] = ladder[ladder.index(body["logprobs"]) + 1]
            else:
                time.sleep(10 * (attempt + 1))
    cache.parent.mkdir(parents=True, exist_ok=True)
    # atomic write (defect fix 08.10.2026): two threads or processes with the same request wrote one file at
    # the same time and made it unreadable
    tmp = cache.with_name(f"{cache.stem}.{threading.get_ident()}.{time.time_ns()}.tmp")
    tmp.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cache)
    return res, False


def _tid(key: str) -> int:
    return int(key.split(":", 1)[1])


def _path(res: dict) -> list[tuple[int, dict[int, float]]]:
    lp = res["choices"][0]["logprobs"]
    return [(_tid(t), {_tid(k): v for k, v in (top or {}).items()}) for t, top in zip(lp["tokens"], lp["top_logprobs"])]


def choice_probs(choices: list[str], path: list[tuple[int, dict[int, float]]], decode, eos: int,
                 fetch=None, split_mass: float = SPLIT_MASS, max_fetch: int = 8) -> dict[str, float]:
    """Probability of each choice under the constrained decoder (see chapter 6 of the docstring).

    path: [(generated token id, {token id: log probability})] for each output position. fetch(prefix ids)
    returns the {token id: log probability} at an off-path position (one more request) or None.
    """
    probs = {c: 0.0 for c in choices}
    n_fetch = [0]

    def step(prefix_ids: list[int], prefix: str, mass: float, rest) -> None:
        if rest:
            top, on = rest[0][1], rest[0][0]
        else:
            top = fetch(prefix_ids) if (fetch and n_fetch[0] < max_fetch) else None
            n_fetch[0] += top is not None
            on = None
        cand = []
        for tid, lp in (top or {}).items():
            if lp is None or lp < -9000:
                continue
            if tid == eos:
                cs_ = [c for c in choices if c == prefix]
                new = prefix
            else:
                s = decode(tid)
                new = prefix + s
                cs_ = [c for c in choices if s and c.startswith(new)]
            if cs_:
                cand.append((tid, math.exp(lp), cs_, new))
        z = sum(p for _, p, _, _ in cand)
        if not z:
            cs_ = [c for c in choices if c.startswith(prefix)] or choices
            for c in cs_:
                probs[c] += mass / len(cs_)
            return
        for tid, p, cs_, new in cand:
            m = mass * p / z
            if len(cs_) == 1:
                probs[cs_[0]] += m
            elif tid == on:
                step(prefix_ids + [tid], new, m, rest[1:])
            elif m >= split_mass and fetch:
                step(prefix_ids + [tid], new, m, None)
            else:
                for c in cs_:
                    probs[c] += m / len(cs_)

    step([], "", 1.0, path)
    s = sum(probs.values()) or 1.0
    return {c: round(v / s, 4) for c, v in probs.items()}


def ask(doc_id: str, question: str, choices: list[str] | None = None, regex: str | None = None, *,
        system: str = SYSTEM_ASK, assistant_prefix: str = "", shots: list[tuple[str, str, str]] | None = None,
        max_tokens: int | None = None, tag: str = "") -> dict:
    """Ask Apertus-v1.5-8B one constrained question about the whole document (E18, E19).

    choices: the output is one of the strings; returns answer, probs {choice: p}, p.
    regex:   the output matches the regular expression; returns answer (= text), token_ids, tokens
             (decoded), top ({token id: log probability} for each position), offsets; use probs_at().
    """
    doc_id = str(doc_id)
    if (choices is None) == (regex is None):
        raise ValueError("give choices or regex (one of them)")
    if choices is not None:
        choices = [str(c) for c in choices]
        if len(set(choices)) != len(choices) or not all(choices) or len(choices) < 2:
            raise ValueError("choices: at least 2 distinct non-empty strings")
    check_cscs(doc_id)
    for sd, _, _ in shots or []:
        check_cscs(sd)
    tok = tokenizer()
    prompt = prompt_ids(doc_id, question, system, assistant_prefix, shots)
    if choices is not None:
        so = {"choice": choices}
        mt = max_tokens or (max(len(c) for c in choices) + 2)
    else:
        so = {"regex": regex}
        mt = max_tokens or 512
    body = {"model": MODEL, "prompt": prompt, "max_tokens": mt, "temperature": 0, "logprobs": TOP,
            "return_tokens_as_token_ids": True, "structured_outputs": so}
    t0 = time.perf_counter()
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0, "requests": 0, "cache_hits": 0}

    def add(res: dict, hit: bool) -> None:
        u = res.get("usage") or {}
        usage["requests"] += 1
        usage["cache_hits"] += hit
        usage["prompt_tokens"] += u.get("prompt_tokens", 0)
        usage["completion_tokens"] += u.get("completion_tokens", 0)
        usage["cached_tokens"] += (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0

    res, hit = _post(body)
    add(res, hit)
    text = res["choices"][0]["text"]
    path = _path(res)
    out = {"doc_id": doc_id, "model": MODEL, "version": VERSION, "text": text,
           "fingerprint": res.get("system_fingerprint")}
    if choices is not None:
        if text not in choices:
            raise RuntimeError(f"{doc_id}: constrained output {text!r} is not a choice")

        def fetch(prefix_ids: list[int]):
            done = tok.decode(prefix_ids)
            rest = [c[len(done):] for c in choices if c.startswith(done)]
            b = dict(body, prompt=prompt + prefix_ids, max_tokens=1,
                     structured_outputs={"regex": "(" + "|".join(re.escape(r) for r in rest) + ")"})
            r, h = _post(b)
            add(r, h)
            p = _path(r)
            return p[0][1] if p else None

        probs = choice_probs(choices, path, lambda t: tok.decode([t]), tok.eos_token_id, fetch)
        out.update(answer=text, probs=probs, p=probs.get(text))
    else:
        tokens = [tok.decode([t]) for t, _ in path]
        offsets, pos = [], 0
        for s in tokens:
            offsets.append(pos)
            pos += len(s)
        out.update(answer=text, token_ids=[t for t, _ in path], tokens=tokens, offsets=offsets,
                   top=[top for _, top in path])
    out["usage"] = usage
    out["seconds"] = round(time.perf_counter() - t0, 2)
    rec = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "doc_id": doc_id, "model": MODEL,
           "tag": tag, "mode": "choices" if choices is not None else "regex",
           "question_sha256": hashlib.sha256(question.encode()).hexdigest()[:16], "question": question[:300],
           "choices": choices, "regex_sha256": hashlib.sha256(regex.encode()).hexdigest()[:16] if regex else None,
           "shots": [s[0] for s in shots or []], "answer": text if choices is not None else text[:200],
           "probs": out.get("probs"), **usage, "seconds": out["seconds"]}
    with _LOCK:
        SUB.mkdir(parents=True, exist_ok=True)
        with open(SUB / "cscs_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out


def probs_at(result: dict, offset: int, allowed: list[str]) -> dict[str, float]:
    """Regex output: the distribution over the allowed strings at the token that holds character `offset`
    (masked and renormalized; a token counts for the allowed string that equals it without spaces)."""
    tok = tokenizer()
    k = max(i for i, o in enumerate(result["offsets"]) if o <= offset)
    dist: dict[str, float] = {}
    for tid, lp in result["top"][k].items():
        s = tok.decode([int(tid)]).strip()
        if s in allowed and lp is not None and lp > -9000:
            dist[s] = max(dist.get(s, -1e9), lp)
    z = sum(math.exp(v) for v in dist.values()) or 1.0
    return {s: round(math.exp(v) / z, 4) for s, v in dist.items()}


# ------------------------------------------------------------------ command line

def summary() -> dict:
    sp = splits(pass_only=True)
    sp_all = splits(pass_only=False)
    lit = splits(pass_only=True, parliament_disjoint=False)
    docs = load()
    out = {
        "version": VERSION,
        "family_map": {f: list(MEMBERS[f]) for f in TEXT_FAMILIES} | {"FRAME": ["none"], "FURNITURE": ["furniture"]},
        "default_type": DEFAULT_TYPE,
        "gold_records": gold_record_ids(),
        "split_sizes_pass": {k: len(v) for k, v in sp.items()},
        "split_sizes_all_triage": {k: len(v) for k, v in sp_all.items()},
        "split_sizes_pass_without_parliament_rule": {k: len(v) for k, v in lit.items()},
        "dev_composition": dict(Counter("pool" if docs[d].kind == "pool" else f"group {docs[d].group}"
                                        for d in sp["dev"])),
        "gold_split": sp["gold"],
        "excluded_by_triage": sorted(set(sp_all["dev"] + sp_all["eval"]) - set(sp["dev"] + sp["eval"])),
        "label_counts": {"dev": label_counts(sp["dev"]), "eval": label_counts(sp["eval"]),
                         "gold": label_counts(sp["gold"], "gold")},
    }
    SUB.mkdir(parents=True, exist_ok=True)
    (SUB / "splits.json").write_text(json.dumps({"version": VERSION, **sp}, indent=1), encoding="utf-8")
    (SUB / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "summary":
        print(json.dumps(summary(), indent=1, ensure_ascii=False))
    elif cmd == "ask":
        d, q = sys.argv[2], sys.argv[3]
        ch = sys.argv[sys.argv.index("--choices") + 1].split(",") if "--choices" in sys.argv else None
        rx = sys.argv[sys.argv.index("--regex") + 1] if "--regex" in sys.argv else None
        r = ask(d, q, choices=ch, regex=rx, tag="cli")
        print(json.dumps({k: v for k, v in r.items() if k not in ("top", "token_ids", "tokens", "offsets")},
                         ensure_ascii=False))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()

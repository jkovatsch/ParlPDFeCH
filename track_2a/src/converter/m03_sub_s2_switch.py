# SPDX-License-Identifier: Apache-2.0
"""Sub-task S2, author switch points (stage 3, iteration of gate 3a, 08.10.2026): candidate lines, a rule and
an Apertus-8B probe. Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agents (Claude
Opus 5.5). Status: feasibility measurement in stage 3 (iteration of gate 3a); no gate result.

Context: gate 3a (isolation, E20) is NOT MET; the main error of the whole-document readout is a whole block
with the wrong author (response <-> submitted). S2 of `m03_sub_common.py` is the author family of the body
(the text atoms that are not TITLE) as a list of runs [(first atom id, family), ...]. This module predicts S2
and measures it. Splits, families, composition and measurement come from `m03_sub_common.py`. Rule design
and prompt design used only dev (the pool and groups 1 to 3); eval (groups 4 to 6) and gold (549658,
368972, reference = gold record) are measured once with the choices from dev.

1 Candidate lines (`candidates`)
  An atom where an author switch can start. Pictures, page headers and footers and atoms with a fixed
  answer (E20 chapter 3) are never candidates. Kinds:
  heading          the first line of a Docling section header
  answer_label     a short line (<= 70 characters, a heading or the first line of a block) that starts with an
                   answer word (Antwort, Beantwortung, Stellungnahme, Réponse, Risposta ...), or "Antrag/Bericht/
                   Rapport des/du <executive>"
  answer_announce  a sentence that announces the answer ("... beantwortet ... wie folgt:", "erteilt folgende
                   Antwort", "répond comme suit", "risponde come segue"); the candidate is the first line of
                   its block
  sponsor_label    "Text/Wortlaut der Interpellation", "Texte du postulat", "Interpellationstext" ...
  speaker          a speaker label at the start of a block ("Name Vorname (Partei):", "PRONZINI M. -",
                   "M. X :"); executive titles (Regierungsrat, Stadtpräsident, CONSIGLIERE DI STATO ...) give
                   EXECUTIVE (rule O), others PLENARY
  decision         a decision heading ("Beschluss", "Kenntnisnahme" ...) or a decision of the parliament
                   ("Der GGR nimmt Kenntnis", "stillschweigend"); strong only when the line or the next 3
                   lines hold a decision of the parliament
  committee        "Die (Mehrheit der) <Kommission> beantragt/beschliesst ..." (weak)
  after_quote      the first line of a block after a line that ends with a closing quotation mark
  Dev: 1288 candidates in 183 documents; 48 of the 51 dev switches have a candidate in their gap.

2 Rule (`rule_predict`)
  Strong cues: answer_label and answer_announce -> EXECUTIVE; sponsor_label -> SPONSOR; speaker -> PLENARY
  or EXECUTIVE; a strong decision -> PLENARY (not after a SPONSOR text: a proposed decision). Other kinds
  have no cue: "same".
  Start family: SPONSOR when there is no strong cue (dev: 64 of 78 such documents start with SPONSOR).
  Answer labels in the head of the document (page 1, short, no sponsor evidence before them) are ignored
  ("head") when sponsor evidence (>= 2 lines: a question mark at the line end, the markers Auftragsformel,
  Einleitung Fragen, Frage n, Stichwort Begründung/Fragen/Auftrag/Rappel) or a sponsor_label follows before
  the next strong cue. Else the start is the family of the first strong cue when no sponsor evidence comes
  before it, and SPONSOR when sponsor evidence comes before it. Then each strong cue sets the family.

3 Apertus probe (prompt file src/prompts/s2_switch.txt, model swiss-ai/Apertus-v1.5-8B, `m03_sub_common.ask`)
  Each request: system role, "Dokument:" + the whole document, then the question (E18); the output is a
  constrained choice (E19): Vorstoss | Exekutive | Kommission | Parlament | gleich (= same as before). One
  start question for each document, one switch question for each candidate line (with its text and the
  line before it). Only documents with triage PASS go to CSCS.
  v1  sections system, start, switch. The answers do not depend on earlier answers (`probe_document`).
  v2  sections system_v2, start_v2, switch_v2: the switch question names the family before the line (the
      decision so far, so the questions of a document are asked in order) and system_v2 states rule Q.
  v3  v2 with each question in two option orders (switch_v2_rev, start_v2_rev); mean of the probabilities.

4 Variants (each written to daten/iso/sub/s2_switch/<variant>_<split>.json with the start, the S2 runs and
  the decision of each candidate for each document, the metrics and the documents with errors)
  rule            section 2
  const_sponsor   start SPONSOR, no switch (lower reference line)
  apertus_vN      Apertus only: start answer; a family answer switches when p >= threshold
  combined_vN     rule where it is sure (strong cues, head labels; the start of the rule only with
                  start_policy rule_if_sure and a strong cue), Apertus for the other candidates (p >= threshold)
  Parameters of the v1 variants (threshold 0, 0.5, 0.8, 0.95, 0.99; start policy) are chosen on the dev
  sample (`select_on_dev`, selection.json). The best variant is chosen on dev only.
  Selection criterion: the E20 labelled boundary F1 of the S2-only composition, then the family accuracy.
  The family accuracy alone rewards a constant EXECUTIVE output (most body atoms are response atoms).

5 Measurement (`evaluate`)
  On the body sequence of the reference (text atoms that are not TITLE, in atom order), the method family of
  each atom is the family that `m03_sub_common.compose` gives with the predicted S2 and the reference S1, S3,
  S4, S5 (`oracle`). A switch is a position k where the family changes from atom k-1 to atom k; a method
  switch is correct at the same k (this is the same as "inside the gap", chapter 4 of m03_sub_common).
  switch recall / precision        correct positions / reference switches, / method switches
  labelled                         also both families equal the reference
  start accuracy                   documents with the correct family of the first body atom
  family accuracy                  body atoms with the correct family / all body atoms
  e20_oracle_s2_only               `m03_sub_common.measure` of the S2-only composition (labelled boundary F1
                                   with the Jeffreys lower bound, class error, document exact rate)
  error types                      documents with a wrong start (and the atoms until the first correct
                                   atom), other wrong atoms, missed, false and wrong-family switches

6 Dev sample of the probe (`dev_sample`): the 45 dev documents with a switch and 35 other dev documents
  (seeded random choice), 80 documents, 51 switches. Values on it are not values of all of dev.

Usage:
  uv run python src/m03_sub_s2_switch.py rule --split dev|eval|gold|dev_sample
  uv run python src/m03_sub_s2_switch.py probe --split dev_sample|eval|gold [--workers 4]     (prompt v1)
  uv run python src/m03_sub_s2_switch.py select                                              (dev sample)
  uv run python src/m03_sub_s2_switch.py variants --split dev_sample|eval|gold               (v1 variants)
  uv run python src/m03_sub_s2_switch.py v2 --split dev_sample --mode apertus|combined [--orders 2]
  uv run python src/m03_sub_s2_switch.py summary                                             (summary.json)
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_sub_common as sc  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

ROOT = sc.ROOT
OUT = sc.SUB / "s2_switch"
PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "s2_switch.txt"
VERSION = "s2-switch-1"

# ------------------------------------------------------------------ patterns (designed on dev only)

NUM = r"^\s*(?:[A-Z]\)|[IVX]+\.|\d+(?:\.\d+)*[.)]?)?\s*"
EXEC_BODY = (r"(?:Regierungsrat(?:e|es|s)?|Stadtrat(?:e|es|s)?|Gemeinderat(?:e|es|s)?|Bundesrat(?:e|es|s)?|"
             r"Kleinen Rat(?:e|es)?|Standeskommission|Exekutive|Gemeindevorstand(?:es|s)?|Stadtregierung|"
             r"Einwohnergemeinderat(?:e|es|s)?|Regierung|Conseil[- ]exécutif|Conseil d'[ÉE]tat|Conseil communal|"
             r"Conseil municipal|Municipalité|Gouvernement|Consiglio di Stato|Municipio|Governo)")
ANSWER_WORD = (r"(?:Antwort(?:en)?|Beantwortung|Stellungnahme|R[ée]ponses?|RÉPONSES?|Prise de position|Risposte?|"
               r"R I S P O S T A|Presa di posizione)")
# a label line: the answer word at the start of the line, then the end of the line, a colon, or a link word
EXEC_LABEL = re.compile(
    NUM + r"(?:[\w ]{0,30}\. )?" + ANSWER_WORD +
    r"(?:\s*$|\s*:|\s+(?:des|der|zu|zur|zum|auf|an|und|Kleine|Einfache|Gemeinderat|Stadtrat|du|de|à|aux|al|alla|"
    r"alle|del|della|dello|écrite|scritta)\b)"
    r"|" + NUM + r"(?:Antrag|Bericht|Rapport|Rapporto|Proposition|Préavis)(?: \w+)? (?:des|der|du|de la|de l'|del|della) "
    + EXEC_BODY, re.I)
EXEC_ANNOUNCE = re.compile(
    r"(?:beantwortet|beantworten|Stellung|répond|répondons|risponde|rispondiamo)\b.{0,80}"
    r"(?:wie folgt|folgt|nachfolgend|folgende|comme suit|ci-après|come segue|di seguito|seguente)"
    r"|(?:wie folgt|comme suit|come segue) (?:beantwortet|Stellung|répond|risponde)"
    r"|erteilt folgende Antwort|(?:wird|werden) wie folgt beantwortet", re.I)
SPONSOR_LABEL = re.compile(
    NUM + r"(?:Text|Wortlaut|Texte|Testo)(?: \w+)? (?:der|des|du|de la|de l'|dell'|della|del) ?"
    r"(?:Interpellation|Motion|Postulat|Anfrage|Kleinen Anfrage|Einfachen Anfrage|Initiative|Einzelinitiative|"
    r"question|interrogazione|interpellanza|mozione)"
    r"|(?:Interpellations|Motions|Postulats|Anfrage)text\b", re.I)
PARTY = r"(?:\((?:[A-ZÄÖÜ][\w/\-+ .]{0,18})\)|, ?[A-ZÄÖÜ][\w/\-+.]{1,14})"
SPEAKER_DE = re.compile(r"^(?:[A-ZÄÖÜ][\wäöüéèà'\-]+ ){1,4}[A-ZÄÖÜ][\wäöüéèà'\-]+ ?" + PARTY + r"\s?:")
SPEAKER_IT = re.compile(r"^[A-ZÀ-Ý'][A-ZÀ-Ý'\-]+(?: [A-ZÀ-Ý'\-]{2,})* [A-Z]\.(?: ?[A-Z]\.)?(,[^-–]{0,80})?\s[-–]\s")
SPEAKER_FR = re.compile(r"^(?:M\.|Mme|Monsieur|Madame) [A-ZÉ][\w\-]+[^:]{0,60}:")
EXEC_SPEAKER = re.compile(r"CONSIGLI(?:O|ERE|ERA) DI STATO|SINDAC|MUNICIPAL|conseill[eè]re? d'[ÉE]tat|syndic|"
                          r"Regierungsrat|Regierungsrätin|Stadtpräsident|Gemeindepräsident|Gemeindeammann|"
                          r"^Gemeinderat |^Gemeinderätin |^Stadtrat |^Stadträtin ")
DECISION_HEAD = re.compile(r"^(?:Beschluss|Kenntnisnahme|Abstimmung|Schlussabstimmung|Beschlussfassung|Décision|"
                           r"Votation|Votazione)\b[^.]{0,30}$")
PARL_DECIDES = re.compile(
    r"\b(?:GGR|Grosse Gemeinderat|Grosse Stadtrat|Grosse Rat|Einwohnerrat|Kantonsrat|Stadtparlament|Gemeindeparlament|"
    r"Parlament|Rat|Conseil général|Grand Conseil|Consiglio comunale|Gran Consiglio)\b.{0,40}\b(?:nimmt|beschliesst|"
    r"stimmt|genehmigt|lehnt|erklärt|décide|prend acte|adopte|accepte|risolve|approva|decide)|^stillschweigend")
COMMITTEE = re.compile(
    r"^(?:Die |Der |La |Le |)(?:Mehrheit der |Minderheit der |einstimmige )?(?:\w*[Kk]ommission|RPK|GPK|FiKo|FIKO|"
    r"commission|commissione)\b.{0,40}\b(?:beantragt|beantragen|beschliesst|empfiehlt|propose|préavise|recommande|"
    r"propone|raccomanda)")
HEAD_PAGES = 99
CLOSE_QUOTE = ('"', "»", "“", "”", "«")
SPONSOR_MARKS = ("Auftragsformel", "Einleitung Fragen", "Stichwort Begründung", "Stichwort Fragen", "Stichwort Auftrag",
                 "Stichwort Rappel")


def _hints(a: dict) -> list[str]:
    return list(a.get("hinweise") or [])


def _has(a: dict, prefix: str) -> bool:
    return any(h.startswith(prefix) for h in _hints(a))


def _skip(x: sc.Doc, a: dict) -> bool:
    """Atoms that cannot start a text: fixed answers (furniture, R3 none), page headers and footers, pictures."""
    return a["id"] in x.fixed or a["label"] in ("picture", "page_header", "page_footer") or _has(a, "im Bild")


def _join(atoms: list[dict]) -> str:
    """The text of consecutive lines; a hyphen at the end of a line joins the word."""
    out = ""
    for a in atoms:
        t = (a["text"] or "").strip()
        out = out[:-1] + t if out.endswith("-") and t[:1].islower() else (out + " " + t if out else t)
    return out


def candidates(doc_id: str) -> list[dict]:
    """Candidate lines where an author switch can start: {pos, id, page, text, kinds, cue, strong}.

    kinds: heading, answer_label, answer_announce, sponsor_label, speaker, decision, committee, after_quote.
    cue: the family that the rule gives after the line (None: no cue); strong: the rule uses the cue."""
    x = sc.load()[doc_id]
    at = sc.atoms(doc_id)
    out: dict[int, dict] = {}

    def add(i: int, kind: str, cue: str | None = None, strong: bool = False) -> None:
        c = out.setdefault(i, {"pos": i, "id": at[i]["id"], "page": at[i]["seite"], "text": at[i]["text"],
                               "kinds": [], "cue": None, "strong": False})
        if kind not in c["kinds"]:
            c["kinds"].append(kind)
        if cue and not c["strong"]:
            c["cue"], c["strong"] = cue, strong

    keep = [i for i, a in enumerate(at) if not _skip(x, a)]
    for n, i in enumerate(keep):
        a = at[i]
        t = (a["text"] or "").strip()
        first_of_block = i == 0 or at[i - 1]["block"] != a["block"]
        bstart = i
        while bstart > 0 and at[bstart - 1]["block"] == a["block"]:
            bstart -= 1
        heading = a["label"] == "section_header"
        nxt = " ".join((at[k]["text"] or "") for k in keep[n + 1: n + 4])
        if heading and first_of_block:
            add(i, "heading")
        if (heading or first_of_block) and len(t) <= 70 and EXEC_LABEL.search(t):
            add(i, "answer_label", "EXECUTIVE", True)
        if _has(a, "Einleitung folgt") or EXEC_ANNOUNCE.search(t) or (t.endswith(":") and i > bstart):
            if EXEC_ANNOUNCE.search(_join(at[bstart: i + 1])):
                add(bstart, "answer_announce", "EXECUTIVE", True)
        if (heading or first_of_block) and len(t) <= 70 and SPONSOR_LABEL.search(t):
            add(i, "sponsor_label", "SPONSOR", True)
        m = SPEAKER_DE.match(t) or SPEAKER_FR.match(t) or SPEAKER_IT.match(t)
        if m and first_of_block:
            add(i, "speaker", "EXECUTIVE" if EXEC_SPEAKER.search(m.group(0)) else "PLENARY", True)
        if first_of_block and (DECISION_HEAD.search(t) or PARL_DECIDES.search(t[:120])):
            add(i, "decision", "PLENARY", bool(PARL_DECIDES.search(t[:120]) or PARL_DECIDES.search(nxt[:160])))
        if first_of_block and COMMITTEE.search(t):
            add(i, "committee", "COMMITTEE", False)
        prev = at[keep[n - 1]]["text"] if n else None
        if prev is not None and prev.rstrip().endswith(CLOSE_QUOTE) and first_of_block:
            add(i, "after_quote")
    return [out[k] for k in sorted(out)]


def sponsor_evidence(a: dict) -> bool:
    """A line that shows the text of the sponsor: a question, a mandate formula, a reasoning or question label."""
    t = (a["text"] or "").strip()
    return (any(_has(a, m) for m in SPONSOR_MARKS) or any(re.match(r"^Frage \d", h) for h in _hints(a))
            or t.endswith("?"))


def _title_like(c: dict) -> bool:
    """An answer label in the head of the document (page 1, a short label, not an announcement sentence)."""
    return c["page"] <= HEAD_PAGES and "answer_announce" not in c["kinds"] and len((c["text"] or "").strip()) <= 70


def rule_predict(doc_id: str, start_mode: str = "evidence", min_evidence: int = 2) -> dict:
    """The rule (chapter 2 of the docstring). Returns start, s2 [(atom id, family)] and the decision of each
    candidate ("same" or a family; "head" for an answer label of the head that the rule ignores)."""
    x = sc.load()[doc_id]
    at = sc.atoms(doc_id)
    cands = candidates(doc_id)
    evpos = [i for i, a in enumerate(at) if not _skip(x, a) and sponsor_evidence(a)]

    def ev(lo: int, hi: int) -> int:
        return sum(1 for i in evpos if lo <= i < hi)

    strong = [c for c in cands if c["strong"]]
    ignore: set[int] = set()
    if start_mode == "sponsor" or not strong:
        start, why = "SPONSOR", "default" if start_mode == "sponsor" else "no strong cue: default SPONSOR"
    else:
        # answer labels in the head: ignore them when the sponsor text follows before the next strong cue
        for k, c in enumerate(strong):
            if c["cue"] != "EXECUTIVE" or not _title_like(c) or ev(0, c["pos"]) > 0:
                break
            nxt = strong[k + 1] if k + 1 < len(strong) else None
            hi = nxt["pos"] if nxt else len(at)
            if (nxt is not None and nxt["cue"] == "SPONSOR") or (nxt is not None and ev(c["pos"], hi) >= min_evidence):
                ignore.add(c["pos"])
            else:
                break
        first = next((c for c in strong if c["pos"] not in ignore), None)
        if first is None:
            start, why = "SPONSOR", "only head labels"
        elif first["cue"] in ("EXECUTIVE", "PLENARY", "COMMITTEE") and ev(0, first["pos"]) == 0 and not ignore:
            start, why = first["cue"], f"first strong cue {first['id']} ({'+'.join(first['kinds'])}), no sponsor evidence"
        else:
            start, why = "SPONSOR", (f"sponsor evidence {ev(0, first['pos'])} before {first['id']}"
                                     + (f", head labels ignored {len(ignore)}" if ignore else ""))
    cur = start
    s2 = [(x.ids[0], start)]
    decisions = []
    for c in cands:
        if c["pos"] in ignore:
            d = "head"
        else:
            fam = c["cue"] if c["strong"] else None
            if fam == "PLENARY" and "decision" in c["kinds"] and cur == "SPONSOR":
                fam = None   # a decision wording inside the sponsor text (a proposed decision)
            d = fam if fam and fam != cur else "same"
        decisions.append({"id": c["id"], "kinds": c["kinds"], "cue": c["cue"], "strong": c["strong"], "decision": d})
        if d not in ("same", "head"):
            s2.append((c["id"], d))
            cur = d
    return {"start": start, "start_reason": why, "s2": s2, "decisions": decisions}


# ------------------------------------------------------------------ measurement

def body_families(doc_id: str, answers: list[str], ref: list[str]) -> list[tuple[str, str]]:
    """(reference family, method family) of each body atom of the reference (text, not TITLE), in atom order."""
    return [(sc.FAMILY[r], sc.FAMILY[h] if h in v4.TEXT else "FRAME") for r, h in zip(ref, answers)
            if r in v4.TEXT and sc.FAMILY[r] != "TITLE"]


def switch_counts(pairs: list[tuple[str, str]]) -> dict:
    """Switch and atom counts of one document. A switch is a position k in the body sequence where the family
    changes; a method switch is correct (hit) at the same k; labelled: both families equal the reference."""
    c = {"ref": 0, "hyp": 0, "hit": 0, "hit_labelled": 0, "atoms": len(pairs), "atoms_ok": 0, "start_ok": 0,
         "missed": 0, "false": 0, "wrong_family": 0}
    for k, (r, h) in enumerate(pairs):
        c["atoms_ok"] += r == h
        if k == 0:
            c["start_ok"] += r == h
            continue
        rs, hs = r != pairs[k - 1][0], h != pairs[k - 1][1]
        c["ref"] += rs
        c["hyp"] += hs
        c["hit"] += rs and hs
        lab = rs and hs and r == h and pairs[k - 1][0] == pairs[k - 1][1]
        c["hit_labelled"] += lab
        c["missed"] += rs and not hs
        c["false"] += hs and not rs
        c["wrong_family"] += rs and hs and not lab
    return c


def evaluate(doc_ids: list[str], s2_by_doc: dict[str, list], source: str = "ref", e20: bool = True) -> dict:
    tot = {k: 0 for k in ("ref", "hyp", "hit", "hit_labelled", "atoms", "atoms_ok", "start_ok", "docs_body",
                          "docs_all_ok", "missed", "false", "wrong_family", "atoms_start_wrong")}
    answers = {}
    errors = []
    for d in doc_ids:
        ref = sc.reference(d, source)
        ans = sc.oracle(d, source, s2=[tuple(e) for e in s2_by_doc[d]])
        answers[d] = ans
        pairs = body_families(d, ans, ref)
        c = switch_counts(pairs)
        for k in c:
            tot[k] += c[k]
        if pairs:
            if not c["start_ok"]:
                k = next((i for i, (rr, hh) in enumerate(pairs) if rr == hh), len(pairs))
                tot["atoms_start_wrong"] += k
            tot["docs_body"] += 1
            tot["docs_all_ok"] += c["atoms_ok"] == c["atoms"]
            if c["atoms_ok"] != c["atoms"]:
                errors.append({"doc_id": d, "wrong_atoms": c["atoms"] - c["atoms_ok"], "atoms": c["atoms"],
                               "start_ok": bool(c["start_ok"]), "ref_switches": c["ref"], "hyp_switches": c["hyp"]})
    m = sc.measure(doc_ids, answers, source) if e20 else {}

    def r(a, b):
        return round(a / b, 4) if b else None

    p, rc = r(tot["hit"], tot["hyp"]), r(tot["hit"], tot["ref"])
    pl, rl = r(tot["hit_labelled"], tot["hyp"]), r(tot["hit_labelled"], tot["ref"])
    return {
        "documents": len(doc_ids), "documents_with_body": tot["docs_body"],
        "switch_ref": tot["ref"], "switch_hyp": tot["hyp"],
        "switch_recall": rc, "switch_precision": p,
        "switch_recall_labelled": rl, "switch_precision_labelled": pl,
        "switch_recall_lower": v4.jeffreys_lower(tot["hit_labelled"], tot["ref"]),
        "start_accuracy": r(tot["start_ok"], tot["docs_body"]),
        "family_accuracy_atoms": r(tot["atoms_ok"], tot["atoms"]), "body_atoms": tot["atoms"],
        "documents_all_atoms_ok": r(tot["docs_all_ok"], tot["docs_body"]),
        "error_types": {"documents_start_wrong": tot["docs_body"] - tot["start_ok"],
                        "atoms_wrong_from_the_start": tot["atoms_start_wrong"],
                        "atoms_wrong_other": tot["atoms"] - tot["atoms_ok"] - tot["atoms_start_wrong"],
                        "switches_missed": tot["missed"], "switches_false": tot["false"],
                        "switches_wrong_family": tot["wrong_family"]},
        "e20_oracle_s2_only": {k: m[k] for k in ("labelled_f1", "labelled_f1_lower", "inner_recall_labelled",
                                                  "text_class_error", "document_exact_rate")} if e20 else None,
        "error_documents": errors,
    }


# ------------------------------------------------------------------ Apertus probe

CHOICE_FAMILY = {"Vorstoss": "SPONSOR", "Exekutive": "EXECUTIVE", "Kommission": "COMMITTEE", "Parlament": "PLENARY"}
SAME = "gleich"
SWITCH_CHOICES = list(CHOICE_FAMILY) + [SAME]


@lru_cache(maxsize=1)
def prompts() -> dict[str, str]:
    """The sections of src/prompts/s2_switch.txt (system, start, switch)."""
    parts: dict[str, list[str]] = {}
    name = None
    for line in PROMPT_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("=== "):
            name = line[4:].strip()
            parts[name] = []
        elif name is not None:
            parts[name].append(line)
    return {k: "\n".join(v).strip() for k, v in parts.items()}


def _clip(t: str, n: int = 160) -> str:
    t = (t or "").strip().replace("«", '"').replace("»", '"')
    return t if len(t) <= n else t[:n] + " ..."


def probe_document(doc_id: str) -> dict:
    """Apertus-v1.5-8B on one document: the start question, then one switch question for each candidate line.
    The whole document is in each prompt, the question is last (E18); the output is a constrained choice (E19)."""
    p = prompts()
    x = sc.load()[doc_id]
    at = sc.atoms(doc_id)
    keep = [i for i, a in enumerate(at) if not _skip(x, a)]
    usage = {"requests": 0, "cache_hits": 0, "prompt_tokens": 0, "cached_tokens": 0, "completion_tokens": 0}

    def ask(question: str, choices: list[str], tag: str) -> dict:
        r = sc.ask(doc_id, question, choices=choices, system=p["system"], tag=tag)
        for k in usage:
            usage[k] += r["usage"].get(k, 0)
        return {"answer": r["answer"], "p": r["p"], "probs": r["probs"]}

    out = {"doc_id": doc_id, "start": ask(p["start"], list(CHOICE_FAMILY), "s2_start"), "candidates": {}}
    for c in candidates(doc_id):
        prev = [i for i in keep if i < c["pos"]]
        pa = at[prev[-1]] if prev else None
        q = p["switch"].format(id=c["id"], text=_clip(c["text"]), prev_id=pa["id"] if pa else "-",
                               prev_text=_clip(pa["text"]) if pa else "(Anfang des Dokuments)")
        out["candidates"][c["id"]] = ask(q, SWITCH_CHOICES, "s2_switch")
    out["usage"] = usage
    return out


# ------------------------------------------------------------------ variants

def variant_apertus(doc_id: str, probe: dict, threshold: float = 0.0) -> dict:
    """Apertus only: the start answer, then each candidate answer (a family switches when its probability is at
    least the threshold; "gleich" keeps the family)."""
    x = sc.load()[doc_id]
    start = CHOICE_FAMILY[probe["start"]["answer"]]
    cur, s2, dec = start, [(x.ids[0], start)], []
    for c in candidates(doc_id):
        a = probe["candidates"][c["id"]]
        fam = CHOICE_FAMILY.get(a["answer"])
        d = fam if fam and fam != cur and a["p"] >= threshold else "same"
        dec.append({"id": c["id"], "kinds": c["kinds"], "apertus": a["answer"], "p": a["p"], "decision": d})
        if d != "same":
            s2.append((c["id"], d))
            cur = d
    return {"start": start, "start_source": "apertus", "s2": s2, "decisions": dec}


def variant_combined(doc_id: str, probe: dict, threshold: float = 0.5, start_policy: str = "rule_if_sure") -> dict:
    """Rule where it is sure (a strong cue, a head label, a start from a strong cue or from sponsor evidence);
    Apertus for the other candidates (switch only with p >= threshold) and, with start_policy "rule_if_sure",
    for the start when the rule has no strong cue."""
    x = sc.load()[doc_id]
    r = rule_predict(doc_id)
    rule_sure = not r["start_reason"].startswith(("no strong cue", "only head"))
    if start_policy == "apertus" or (start_policy == "rule_if_sure" and not rule_sure):
        start, src = CHOICE_FAMILY[probe["start"]["answer"]], "apertus"
    else:
        start, src = r["start"], "rule"
    cur, s2, dec = start, [(x.ids[0], start)], []
    for rd in r["decisions"]:
        a = probe["candidates"][rd["id"]]
        if rd["decision"] == "head":
            d, by = "same", "rule"
        elif rd["strong"]:
            fam = rd["cue"]
            if fam == "PLENARY" and "decision" in rd["kinds"] and cur == "SPONSOR":
                fam = None
            d, by = (fam if fam and fam != cur else "same"), "rule"
        else:
            fam = CHOICE_FAMILY.get(a["answer"])
            d, by = (fam if fam and fam != cur and a["p"] >= threshold else "same"), "apertus"
        dec.append({"id": rd["id"], "kinds": rd["kinds"], "rule_cue": rd["cue"] if rd["strong"] else None,
                    "apertus": a["answer"], "p": a["p"], "by": by, "decision": d})
        if d != "same":
            s2.append((rd["id"], d))
            cur = d
    return {"start": start, "start_source": src, "s2": s2, "decisions": dec}


STATE = {"SPONSOR": "der Wortlaut des Vorstosses der Einreichenden",
         "EXECUTIVE": "die Antwort, Stellungnahme oder der Bericht der Exekutive",
         "COMMITTEE": "der Antrag oder Beschluss einer Kommission",
         "PLENARY": "die Debatte oder der Beschluss des Parlaments"}


def run_sequential(doc_id: str, mode: str, threshold: float = 0.0, orders: int = 1) -> dict:
    """Prompt v2: the switch question names the family before the line (the decision so far), so the
    questions of one document are asked in atom order.
    mode "apertus": the start and each candidate from Apertus (the answer decides; "gleich" keeps the family).
    mode "combined": the rule where it is sure (start from a strong cue or from sponsor evidence, strong cues,
    head labels), Apertus for the start without a strong cue and for the other candidates (p >= threshold)."""
    p = prompts()
    x = sc.load()[doc_id]
    at = sc.atoms(doc_id)
    keep = [i for i, a in enumerate(at) if not _skip(x, a)]
    usage = {"requests": 0, "cache_hits": 0, "prompt_tokens": 0, "cached_tokens": 0, "completion_tokens": 0}

    def ask1(question: str, choices: list[str], tag: str) -> dict:
        r = sc.ask(doc_id, question, choices=choices, system=p["system_v2"], tag=tag)
        for k in usage:
            usage[k] += r["usage"].get(k, 0)
        return r["probs"]

    def ask(questions: list[str], choices: list[str], tag: str) -> dict:
        """orders = 2: the mean of the probabilities over the two option orders (position bias)."""
        ps = [ask1(q, choices, tag) for q in questions[:orders]]
        probs = {c: round(sum(x.get(c, 0.0) for x in ps) / len(ps), 4) for c in choices}
        best = max(choices, key=lambda c: probs[c])
        return {"answer": best, "p": probs[best], "probs": probs, "probs_by_order": ps}

    r = rule_predict(doc_id)
    rule_sure = not r["start_reason"].startswith(("no strong cue", "only head"))
    start_ans = None
    if mode == "apertus" or not rule_sure:
        start_ans = ask([p["start_v2"], p["start_v2_rev"]], ["Exekutive", "Vorstoss", "Kommission", "Parlament"],
                        f"s2v2_{mode}_start")
        start, src = CHOICE_FAMILY[start_ans["answer"]], "apertus"
    else:
        start, src = r["start"], "rule"
    cur, s2, dec = start, [(x.ids[0], start)], []
    for rd, c in zip(r["decisions"], candidates(doc_id)):
        a, by = None, "apertus"
        if mode == "combined" and rd["decision"] == "head":
            d, by = "same", "rule"
        elif mode == "combined" and rd["strong"]:
            fam = rd["cue"]
            if fam == "PLENARY" and "decision" in rd["kinds"] and cur == "SPONSOR":
                fam = None
            d, by = (fam if fam and fam != cur else "same"), "rule"
        else:
            prev = [i for i in keep if i < c["pos"]]
            pa = at[prev[-1]] if prev else None
            fill = {"id": c["id"], "text": _clip(c["text"]), "prev_id": pa["id"] if pa else "-",
                    "prev_text": _clip(pa["text"]) if pa else "(Anfang des Dokuments)", "state": STATE[cur]}
            a = ask([p["switch_v2"].format(**fill), p["switch_v2_rev"].format(**fill)], SWITCH_CHOICES,
                    f"s2v2_{mode}")
            fam = CHOICE_FAMILY.get(a["answer"])
            d = fam if fam and fam != cur and a["p"] >= threshold else "same"
        dec.append({"id": c["id"], "kinds": c["kinds"], "rule_cue": rd["cue"] if rd["strong"] else None,
                    "state": cur, "apertus": a["answer"] if a else None, "p": a["p"] if a else None, "by": by,
                    "decision": d})
        if d != "same":
            s2.append((c["id"], d))
            cur = d
    return {"doc_id": doc_id, "start": start, "start_source": src, "start_answer": start_ans, "s2": s2,
            "decisions": dec, "usage": usage}


def run_v2(split: str, mode: str, threshold: float = 0.0, workers: int = 4, orders: int = 1) -> dict:
    docs = split_docs(split)
    for d in docs:
        sc.check_cscs(d)
    preds: dict[str, dict] = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        for res in ex.map(lambda d: run_sequential(d, mode, threshold, orders), docs):
            preds[res["doc_id"]] = res
    usage = {k: sum(r["usage"][k] for r in preds.values()) for k in next(iter(preds.values()))["usage"]}
    name = f"{mode}_{'v3' if orders == 2 else 'v2'}" + (f"_t{threshold}" if threshold else "")
    prompt = ("v3 (system_v2; start_v2 and start_v2_rev, switch_v2 and switch_v2_rev: mean over two option orders)"
              if orders == 2 else "v2 (system_v2, start_v2, switch_v2)")
    body = write_variant(name, split, {d: {k: v for k, v in r.items() if k != "doc_id"} for d, r in preds.items()},
                         {"prompt": prompt, "threshold": threshold, "usage": usage})
    return {"variant": name, "usage": usage, "metrics": body["metrics"]}


# ------------------------------------------------------------------ runs and files

def dev_sample(n_other: int = 35, seed: int = 20261008) -> list[str]:
    """Dev sample for the probe: all dev documents with an author switch, and n_other other dev documents
    (seeded random choice). Dev only (rule and prompt design)."""
    import random

    dev = sc.splits()["dev"]
    docs = sc.load()
    sw = [d for d in dev if len(sc.labels(docs[d].ids, docs[d].ref)["s2"]) > 1]
    rest = [d for d in dev if d not in sw]
    rng = random.Random(seed)
    return sorted(sw + rng.sample(rest, n_other), key=lambda d: dev.index(d))


def split_docs(split: str) -> list[str]:
    if split == "dev_sample":
        return dev_sample()
    return sc.splits()[split]


def source_of(split: str) -> str:
    return "gold" if split == "gold" else "ref"


def write_variant(variant: str, split: str, preds: dict[str, dict], params: dict | None = None) -> dict:
    docs = list(preds)
    ev = evaluate(docs, {d: preds[d]["s2"] for d in docs}, source_of(split))
    OUT.mkdir(parents=True, exist_ok=True)
    body = {"version": VERSION, "variant": variant, "split": split, "reference": source_of(split),
            "model": sc.MODEL if variant != "rule" else None, "params": params or {},
            "prompt_file": str(PROMPT_FILE.relative_to(ROOT)) if variant != "rule" else None,
            "metrics": {k: v for k, v in ev.items() if k != "error_documents"},
            "error_documents": ev["error_documents"],
            "documents": {d: {"start": preds[d]["start"], "s2": [list(e) for e in preds[d]["s2"]],
                              **{k: v for k, v in preds[d].items() if k not in ("start", "s2")}} for d in docs}}
    (OUT / f"{variant}_{split}.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    return body


def run_probe(split: str, workers: int = 4) -> dict:
    docs = split_docs(split)
    for d in docs:
        sc.check_cscs(d)
    out: dict[str, dict] = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        for res in ex.map(probe_document, docs):
            out[res["doc_id"]] = res
            print(json.dumps({"doc_id": res["doc_id"], "candidates": len(res["candidates"]), **res["usage"]}),
                  flush=True)
    usage = {k: sum(r["usage"][k] for r in out.values()) for k in next(iter(out.values()))["usage"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"probe_{split}.json").write_text(json.dumps({"version": VERSION, "model": sc.MODEL, "split": split,
                                                         "prompt_file": str(PROMPT_FILE.relative_to(ROOT)),
                                                         "usage": usage, "documents": out},
                                                        ensure_ascii=False, indent=1), encoding="utf-8")
    return {"documents": len(out), **usage}


def load_probe(split: str) -> dict:
    return json.loads((OUT / f"probe_{split}.json").read_text(encoding="utf-8"))["documents"]


THRESHOLDS = (0.0, 0.5, 0.8, 0.95, 0.99)
START_POLICIES = ("rule_if_sure", "apertus")


def select_on_dev() -> dict:
    """Choose the parameters of the prompt-v1 Apertus and combined variants on the dev sample only. Criterion:
    the E20 labelled boundary F1 of the S2-only composition (S2 predicted, S1, S3, S4, S5 from the reference),
    then the family accuracy per body text atom. (The family accuracy alone rewards a constant EXECUTIVE output:
    most body atoms are response atoms.)"""
    probe = load_probe("dev_sample")
    docs = list(probe)

    def score(preds):
        ev = evaluate(docs, {d: preds[d]["s2"] for d in docs})
        return (ev["e20_oracle_s2_only"]["labelled_f1"], ev["family_accuracy_atoms"])

    table = {}
    for t in THRESHOLDS:
        table[f"apertus t={t}"] = score({d: variant_apertus(d, probe[d], t) for d in docs})
        for sp_ in START_POLICIES:
            table[f"combined t={t} start={sp_}"] = score({d: variant_combined(d, probe[d], t, sp_) for d in docs})
    best_a = max((k for k in table if k.startswith("apertus")), key=lambda k: table[k])
    best_c = max((k for k in table if k.startswith("combined")), key=lambda k: table[k])
    sel = {"criterion": "E20 labelled boundary F1 of the S2-only composition, then family accuracy per body "
                        "text atom (dev sample)",
           "table": {k: {"e20_labelled_f1_s2_only": v[0], "family_accuracy_atoms": v[1]} for k, v in table.items()},
           "apertus": {"threshold": float(best_a.split("t=")[1])},
           "combined": {"threshold": float(best_c.split("t=")[1].split()[0]), "start_policy": best_c.split("start=")[1]}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "selection.json").write_text(json.dumps(sel, indent=1), encoding="utf-8")
    return sel


def cscs_usage() -> dict:
    """CSCS requests of S2 from daten/iso/sub/cscs_log.jsonl (tags s2_*: prompt v1; s2v2_*: prompts v2 and v3)."""
    out: dict[str, dict] = {}
    for line in (sc.SUB / "cscs_log.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        t = r.get("tag") or ""
        if not t.startswith(("s2_", "s2v2_")):
            continue
        g = out.setdefault("v1" if t.startswith("s2_") else "v2_v3", {"calls": 0, "network_requests": 0,
                                                                       "cache_hits": 0, "prompt_tokens": 0,
                                                                       "cached_prompt_tokens": 0,
                                                                       "completion_tokens": 0})
        g["calls"] += 1
        g["cache_hits"] += r["cache_hits"]
        n = r["requests"] - r["cache_hits"]
        g["network_requests"] += n
        if n:
            g["prompt_tokens"] += r["prompt_tokens"]
            g["cached_prompt_tokens"] += r["cached_tokens"]
            g["completion_tokens"] += r["completion_tokens"]
    out["total_network_requests"] = sum(v["network_requests"] for v in out.values() if isinstance(v, dict))
    return out


def summary() -> dict:
    """All variant files in one table, the best variant chosen on the dev sample, and the CSCS usage."""
    keys = ("documents", "switch_ref", "switch_hyp", "switch_recall_labelled", "switch_precision_labelled",
            "switch_recall_lower", "start_accuracy", "family_accuracy_atoms", "body_atoms", "error_types")
    table = {}
    for f in sorted(OUT.glob("*_*.json")):
        if f.name.startswith(("probe_", "selection", "summary")):
            continue
        b = json.loads(f.read_text(encoding="utf-8"))
        m = b["metrics"]
        table[f"{b['variant']} / {b['split']}"] = {**{k: m.get(k) for k in keys},
                                                   "e20_oracle_s2_only": m["e20_oracle_s2_only"],
                                                   "params": b.get("params", {})}
    dev = {k.split(" / ")[0]: v for k, v in table.items() if k.endswith(" / dev_sample")}
    best = max(dev, key=lambda k: (dev[k]["e20_oracle_s2_only"]["labelled_f1"], dev[k]["family_accuracy_atoms"]))
    out = {"version": VERSION, "model": sc.MODEL, "prompt_file": str(PROMPT_FILE.relative_to(ROOT)),
           "selection_criterion": "E20 labelled boundary F1 of the S2-only composition on the dev sample, "
                                  "then family accuracy per body text atom",
           "best_variant_by_dev": best, "best_variant_eval": table.get(f"{best} / eval"),
           "best_variant_gold": table.get(f"{best} / gold"), "cscs": cscs_usage(), "table": table}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["rule", "probe", "variants", "select", "report", "candidates", "v2", "summary"])
    ap.add_argument("--mode", default="apertus", choices=["apertus", "combined"])
    ap.add_argument("--threshold", type=float, default=0.0)
    ap.add_argument("--orders", type=int, default=1, choices=[1, 2])
    ap.add_argument("--split", default="dev", choices=["dev", "dev_sample", "eval", "gold"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "candidates":
        for d in split_docs(a.split):
            print(d, len(candidates(d)))
    elif a.cmd == "rule":
        docs = split_docs(a.split)
        preds = {d: rule_predict(d) for d in docs}
        print(json.dumps(write_variant("rule", a.split, preds)["metrics"], ensure_ascii=False))
        const = {d: {"start": "SPONSOR", "s2": [(sc.load()[d].ids[0], "SPONSOR")]} for d in docs}
        print(json.dumps(write_variant("const_sponsor", a.split, const)["metrics"], ensure_ascii=False))
    elif a.cmd == "probe":
        print(json.dumps(run_probe(a.split, a.workers)))
    elif a.cmd == "v2":
        r = run_v2(a.split, a.mode, a.threshold, a.workers, a.orders)
        print(json.dumps({"variant": r["variant"], "usage": r["usage"],
                          **{k: v for k, v in r["metrics"].items() if k != "error_types"}}))
        print(json.dumps(r["metrics"]["error_types"]))
    elif a.cmd == "select":
        print(json.dumps(select_on_dev(), indent=1))
    elif a.cmd == "variants":
        sel = json.loads((OUT / "selection.json").read_text(encoding="utf-8"))
        probe = load_probe(a.split)
        docs = [d for d in split_docs(a.split) if d in probe]
        assert len(docs) == len(probe), "probe file and split differ"
        ta = sel["apertus"]["threshold"]
        tc, spc = sel["combined"]["threshold"], sel["combined"]["start_policy"]
        pa = {d: variant_apertus(d, probe[d], ta) for d in docs}
        pc = {d: variant_combined(d, probe[d], tc, spc) for d in docs}
        print("apertus", json.dumps(write_variant("apertus_v1", a.split, pa, {"prompt": "v1 (system, start, switch)", "threshold": ta})["metrics"]))
        print("combined", json.dumps(write_variant("combined_v1", a.split, pc, {"prompt": "v1 (system, start, switch)", "threshold": tc, "start_policy": spc})["metrics"]))
        if a.split == "dev_sample":
            pr = {d: rule_predict(d) for d in docs}
            print("rule", json.dumps(write_variant("rule", a.split, pr)["metrics"]))
    elif a.cmd == "summary":
        print(json.dumps(summary(), indent=1, ensure_ascii=False))
    elif a.cmd == "report":
        for f in sorted(OUT.glob("*_*.json")):
            if f.name.startswith(("probe_", "selection")):
                continue
            m = json.loads(f.read_text(encoding="utf-8"))["metrics"]
            print(f.name, {k: m[k] for k in ("documents", "switch_ref", "switch_hyp", "switch_recall_labelled",
                                              "switch_precision_labelled", "start_accuracy", "family_accuracy_atoms")},
                  m["e20_oracle_s2_only"]["labelled_f1"])


if __name__ == "__main__":
    main()

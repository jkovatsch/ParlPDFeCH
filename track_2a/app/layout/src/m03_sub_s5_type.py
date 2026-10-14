"""Isolation in sub-tasks, S5: the type inside an author family (stage 3, iteration of gate 3a, 08.10.2026).

Context: gate 3a (isolation, E20) is NOT MET. Jonathan asked (08.10.2026) to break the task into small
problems that Apertus-8B can solve. This script measures the feasibility of sub-task S5. Written in
English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5).

1 Task
  Input: the text atoms of a document and their author family (TITLE, SPONSOR, EXECUTIVE, PLENARY;
  m03_sub_common chapter 3). In this measurement the families come from the reference (oracle S1 to S4
  and S3), so that only S5 is measured. Output: the type of each atom (E20 rule L, C9, C13):
    TITLE      title | short_title
    SPONSOR    submitted | reasoning
    EXECUTIVE  response | recommendation
    PLENARY    vote | speech | proposition
  A run is a sequence of text atoms of one family without a text atom of another family between them.
  A paragraph is the part of a run in one Docling block. Footnotes and carried captions (E20 rule N) get
  the type of the atom before them in the run and do not change the state of a rule.

2 Rule (variant "rule"; designed only on dev: the pool and groups 1 to 3)
  SPONSOR (rule L, C13: a reasoning needs a label; without a label the text is submitted)
    R-S1  Start "reasoning" at a reasoning label: a heading-like atom (heading, short line, or the label
          followed by ":" or a tab) that starts with Begründung, Erwägungen, Gründe, Weisung,
          Hintergrund/Begründung, Développement, Motivation, Exposé des motifs, Motivazione, Giustificazione,
          or a heading that starts with "Warum".
    R-S2  Rule H: heading atoms directly before a reasoning label in the run (only frame atoms between
          them) are reasoning too.
    R-S3  End "reasoning" (back to "submitted") at a label of the submitted text: Antrag, Fragen, Auftrag,
          Wortlaut, Forderungen, Contenu, Texte, Testo, Domande, or an affair type, as a heading-like atom.
    R-S4  End "reasoning" at the sentence with the request of the sponsor (passive "wird gebeten /
          beauftragt / aufgefordert / eingeladen", "wir fordern / bitten / ersuchen", "folgende Fragen",
          "est prié", "nous demandons", "è invitato", "chiediamo" ...). The switch is at the line where
          the sentence starts; if the sentence starts inside a line, at the next line (as in the dev
          references 70507, 894842, 925636).
    R-S5  End "reasoning" at a heading with the same numbering depth as a numbered reasoning label
          ("3. Gründe ..." -> "4. Fazit").
  EXECUTIVE (rule L, C9: a recommendation needs its own paragraph or section with only the formal proposal)
    R-E1  A proposal label (heading-like atom: Antrag, Anträge, Antrag des Stadtrates, Proposition,
          Proposta, Préavis, Empfehlung; not of a committee or of the sponsor) starts "recommendation"
          until the next heading or the end of the run. A heading that continues the proposal
          ("beschliessen:", "Beschluss:") does not end it. An inline label ("Antrag<TAB>text") gives
          only its atom.
    R-E2  A weak label (Conclusion, Fazit, Schlussfolgerung, Conclusione) starts "recommendation" only if
          the next paragraph holds a formal proposal sentence (R-E3 patterns).
    R-E3  A paragraph whose first sentence holds the formal proposal of the executive ("Der Regierungsrat
          beantragt ...", "Dem Kantonsrat wird beantragt ...", "beantragt der Stadtrat", "stellt den
          Antrag", "préavise favorablement", "le Conseil municipal propose / invite", "il Consiglio di Stato
          propone / invita") and has at most 2 sentences is "recommendation". Not if the sentence
          announces reasons ("aus nachstehenden Gründen"). If the paragraph ends with ":", the following
          paragraphs are "recommendation" until the next heading.
  PLENARY: default "vote". A paragraph that starts with a speaker ("NAME X. -", "Name Vorname, SP:",
    "Vorname Name (SVP):", "Referent ...") starts "speech"; headings directly before it are speech (rule
    H); a resolution ("Beschluss", "beschliesst", "beschlossen", "Kenntnisnahme", "nimmt Kenntnis")
    starts "vote".
  TITLE: "title"; "short_title" only with a label (Kurztitel, Titre court, Titolo breve).
  Each paragraph gets a "sure" flag: SPONSOR is not sure for a paragraph in the reasoning state that is
  not the label paragraph and not ended by R-S3 to R-S5 (where reasoning ends without a label is open
  in E20 4.1). EXECUTIVE is not sure for a paragraph without a proposal label that has a proposal word
  (BROAD pattern). TITLE and PLENARY are always sure.

3 Apertus-8B (variant "apertus"; the prompt is src/prompts/s5_type.txt)
  One constrained question for each candidate paragraph (each paragraph of a SPONSOR, EXECUTIVE or
  PLENARY run; TITLE is not asked: no short_title in the references). The whole document comes first,
  the question last (E18); the output is one of the choices of the family (E19). The answer of a
  paragraph goes to all its atoms. ask() of m03_sub_common: Apertus-v1.5-8B, temperature 0, triage PASS
  only, the key from .env.cscs (never printed), log in daten/iso/sub/cscs_log.jsonl (tag "s5_type").
  dev: a fixed sample (SAMPLE_DEV documents, chosen by sorted SHA-256 of the doc id, half with a
  non-default type), eval: all documents, gold: both documents.
  Prompt versions (both in the prompt file): v1 asks for a choice between the two types; v2 asks a yes/no
  question nearer to rule L. On dev, v1 gave "reasoning" for 88 of 105 submitted sponsor paragraphs of
  the sample; v2 is better for the apertus variant (dev sample: accuracy 0.924 against 0.813), v1 is
  better inside the combined variant (all dev: type-split F1 0.934 against 0.670). These choices
  (CHOSEN_PROMPT, COMBINED_PROMPT) were fixed before any eval or gold request.

4 Combined (variant "combined"): the rule where its paragraph is sure, Apertus for the other paragraphs.
  Apertus is asked for the not-sure paragraphs of all dev documents, so that the decision "combined is
  better than rule" uses all of dev. The best variant on eval is the variant with the best dev value
  (labelled F1 of the type splits, then the atom accuracy; the apertus variant is compared with the rule
  on the same dev sample); eval and gold do not change the choice.

5 Measurement (`metrics`)
  accuracy        atoms of a family with more than one type (reference family): predicted type = reference
                  type; also by family, and the accuracy of "always the default type" for comparison.
  type splits     the boundary sequence of measurement 4.1 (text atoms without footnotes and carried
                  captions); a type boundary is a position where the family is the same on both sides and
                  the type changes. A method boundary is correct only if the types on both sides are
                  equal to the reference (labelled). F1 with the Jeffreys lower bound (m03_iso_v4).
  E20 total       m03_sub_common.measure with oracle S1 to S4 and S3 and the predicted S5: labelled boundary
                  F1, text class error, document exact rate.
  errors          atom confusion pairs (reference -> method).

6 Output: daten/iso/sub/s5_type/<variant>_<split>.json (variant rule, apertus, combined; split dev,
  eval, gold; apertus_dev covers the dev sample only): the metrics and for each document the S5 labels
  {atom id: type} (input for compose), the paragraphs with type, source (rule or apertus), sure flag,
  rule name and Apertus probabilities. An assembler with predicted families calls
  predict_rule(doc_id, answers) with the composed answers (default types); for the Apertus answers the
  family of the paragraph must be the same as here.

Usage:
  uv run python src/m03_sub_s5_type.py rule [--split dev] [--all]   (--all: dev, eval and gold)
  uv run python src/m03_sub_s5_type.py errors                (rule errors on dev only, for design)
  uv run python src/m03_sub_s5_type.py apertus --split dev|eval|gold [--prompt v1|v2] [--unsure-only]
      (answers -> s5_type/apertus_answers_<split>_<prompt>.json; a repeated request reads the CSCS cache)
  uv run python src/m03_sub_s5_type.py report                (all variants and splits from the cached
      answers -> s5_type/<variant>_<split>.json and s5_type/metrics.json)
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_sub_common as sc  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

VERSION = "s5-type-1"
OUT = sc.SUB / "s5_type"
PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "s5_type.txt"
SAMPLE_DEV = 24
TAG = "s5_type"
ASKED_FAMILIES = ("SPONSOR", "EXECUTIVE", "PLENARY")
SPLIT_SOURCE = {"dev": "ref", "eval": "ref", "gold": "gold"}
PROMPT_VERSIONS = ("v1", "v2")
# Prompt versions chosen on dev (chapter 3 and 4), fixed on 08.10.2026 before any eval or gold request.
CHOSEN_PROMPT = "v2"            # variant "apertus" (dev sample: accuracy 0.924 against 0.813 for v1)
COMBINED_PROMPT = "v1"          # variant "combined" (all dev: type-split F1 0.934 against 0.670 for v2)
PROMPT_VERSION = CHOSEN_PROMPT  # set by --prompt

# ------------------------------------------------------------------ text helpers

NUM = r"(?:(?:[IVX]{1,4}|\d{1,2}(?:\.\d{1,2})*|[A-Za-z])[.)]?\s+)?"
RX_REASONING = re.compile(
    r"^" + NUM + r"(?:begr[üu]\s?e?\s?ndung|erw[äa]gungen|gr[üu]nde\b|weisung\b|hintergrund\s*/\s*begr[üu]ndung|"
    r"d[ée]veloppement|motivation|expos[ée] des motifs|motivazion[ei]|giustificazione)", re.I)
RX_WHY = re.compile(r"^" + NUM + r"(?:warum|pourquoi|perch[ée])\b", re.I)
RX_SUBMITTED_LABEL = re.compile(
    r"^" + NUM + r"(?:antr[äa]ge?|antrag|fragen|auftrag|wortlaut|forderung(?:en)?|contenu|texte|testo|domande|"
    r"questions?|demandes?|richiest[ae]|interpellation|postulat|motion|anfrage|interpellanza|mozione|"
    r"postulato|petition|einzelinitiative)\b", re.I)
RX_DEMAND = re.compile(
    r"\b(?:wird|werden|sei|seien|ist|sind)\s+(?:[\w.,'’-]+\s+){0,3}?(?:beauftragt|gebeten|aufgefordert|eingeladen|"
    r"ersucht)\b"
    r"|\b(?:wir|ich|postulant\w*|motion[äa]r\w*|interpellant\w*|unterzeichnende\w*)\s+(?:[\w,'’-]+\s+){0,2}?"
    r"(?:ersuchen|ersuche|bitten|bitte|fordern|fordere|verlangen|verlange|erwarten|erwarte)\b"
    r"|\bm[öo]chten?\s+(?:\w+\s+)?wissen\b|\bwollen\s+(?:\w+\s+)?wissen\b"
    r"|\b(?:fraktion|partei|kommission|gruppe|postulant\w*|motion[äa]r\w*|interpellant\w*|unterzeichnende\w*)\s+"
    r"(?:[\w/-]+\s+){0,2}?(?:fordert|verlangt|ersucht|bittet|fordern|verlangen|ersuchen|bitten)\b"
    r"|\b(?:commission|groupe|fraction|motionnaires?|postulante?s?|signataires?|auteure?s?)\s+(?:\w+\s+){0,2}?"
    r"(?:demandent|demande|prient|prie|invitent|invite)\b"
    r"|\b(?:ersuchen|ersuche|bitten|bitte|fordern|fordere|verlangen|verlange|erwarten|erwarte)\s+(?:[\w'’-]+\s+)?"
    r"(?:wir|ich)\b"
    r"|\bfolgende\w*\s+fragen\b|\bfragen\s+zu\s+beantworten\b"
    r"|\b(?:est|sont)\s+(?:\w+\s+)?(?:pri[ée]|invit[ée]|charg[ée])e?s?\b"
    r"|\b(?:nous|je)\s+(?:\w+\s+){0,2}?(?:demandons|demande|prions|prie|invitons|souhaitons|souhaite)\b|\bquestions?\s+suivantes?\b"
    r"|\b(?:[èe]|sono|viene|vengono)\s+(?:\w+\s+)?(?:invitat|incaricat|chiamat)\w\b"
    r"|\b(?:chiediamo|chiedo|invitiamo|domandiamo)\b|\bseguenti\s+domande\b", re.I)

EXEC = (r"(?:stadtrat|gemeinderat|regierungsrat|standeskommission|kleine\s+rat|kleinrat|stadtregierung|"
        r"gemeindevorstand|bundesrat|exekutive|landammann|conseil\s+municipal|conseil\s+communal|"
        r"conseil\s+d['’]\s*[ée]tat|conseil-ex[ée]cutif|municipalit[ée]|conseil\s+administratif|"
        r"consiglio\s+di\s+stato|municipio|governo)")
PARL = (r"(?:kantonsrat|landrat|grossen?\s+rat|gemeinderat|einwohnerrat|stadtrat|parlament|stadtparlament|"
        r"gemeindeparlament|rat|finanzkommission|gemeindeversammlung)")
RX_PROPOSAL = re.compile(
    r"\b(?:dem|der)\s+" + PARL + r"\s+wird\s+(?:\w+\s+)?beantragt"
    r"|\bwird\s+(?:\w+\s+)?(?:dem|der)\s+" + PARL + r"\s+beantragt|\bwird\s+beantragt\b"
    r"|\b" + EXEC + r"\s+(?:\w+\s+){0,2}?(?:beantragt|empfiehlt|stellt\s+(?:\w+\s+)?(?:den\s+)?antrag)"
    r"|\b(?:beantragt|empfiehlt)\s+(?:\w+\s+){0,2}?(?:der|die|das)\s+" + EXEC +
    r"|pr[ée]avise\s+(?:favorablement|d[ée]favorablement|positivement|n[ée]gativement)"
    r"|\b" + EXEC + r"\s+(?:vous\s+)?(?:propose|invite|recommande|demande)\b"
    r"|\bnous\s+vous\s+(?:proposons|invitons|recommandons|demandons)\b"
    r"|\b" + EXEC + r"\s+(?:vi\s+)?(?:invita|propone|chiede|raccomanda)\b|\bvi\s+(?:invitiamo|proponiamo|chiediamo)\b",
    re.I)
RX_PROPOSAL_NOT = re.compile(r"\b(?:nachstehenden|folgenden|nachfolgenden)\s+gr[üu]nden\b", re.I)
RX_PROPOSAL_LABEL = re.compile(
    r"^" + NUM + r"(?:antr[äa]ge?|antrag|propositions?|propost[ae]|pr[ée]avis|empfehlung)\b(?P<rest>.*)$", re.I)
RX_NOT_EXEC = re.compile(r"kommission|commission|commissione|motion[äa]r|postulant|interpellant|fraktion|"
                         r"minderheit|mehrheit", re.I)
RX_WEAK_LABEL = re.compile(r"^" + NUM + r"(?:conclusions?|conclusion[ei]|fazit|schlussfolgerung(?:en)?)\s*:?\s*$", re.I)
RX_BROAD = re.compile(r"beantrag|antrag|antr[äa]ge|empfiehlt|empfehl|propos|pr[ée]avis|invite|recommand|chied|"
                      r"propon|invit|ablehn|abzulehnen|erheblich|abzuschreiben|abschreib|als erledigt|"
                      r"zur kenntnis|kenntnis zu nehmen|gutzuheissen|anzunehmen|accept|refus|classer|respinger|"
                      r"accoglier", re.I)
RX_CONTINUE = re.compile(r"^" + NUM + r"(?:beschluss|beschlussentwurf|dispositiv|d[ée]cision|arr[êe]t[ée]|decisione)\b",
                         re.I)
RX_SPEAKER = re.compile(
    r"^(?:[A-ZÄÖÜÀ-Ý]{2,}[\w'’-]*(?:\s+[A-ZÄÖÜÀ-Ý]{2,}[\w'’-]*)*\s+[A-ZÄÖÜ]\.?(?:\s*[A-ZÄÖÜ]\.)?\s*(?:,[^-–:]{1,60})?\s*[-–]"
    r"|[A-ZÄÖÜÀ-Ý][\w'’-]+(?:\s+[A-ZÄÖÜÀ-Ý][\w'’-]+){1,3}\s*(?:,\s*[\w/ .-]{1,40}|\([\w/ .-]{1,40}\))\s*:"
    r"|(?:Referent|Referentin|Kommissionsreferent|Kommissionsreferentin|Sprecher|Sprecherin|Rapporteur|"
    r"Relatore|Relatrice)\b)")
RX_VOTE = re.compile(r"^(?:" + NUM + r")?(?:beschluss|beschliesst|beschließt|kenntnisnahme|abstimmung|d[ée]cision|"
                     r"arr[êe]te|decisione|risoluzione)\b|\bbeschlossen\b|\bbeschliesst\b|\bnimmt\s+kenntnis\b|"
                     r"\bzur\s+kenntnis\s+genommen\b|\bd[ée]cide\b|\barr[êe]te\b|\brisolve\b", re.I)
RX_SHORT_TITLE = re.compile(r"^(?:kurztitel|titre\s+(?:court|abr[ée]g[ée])|titolo\s+breve)\b", re.I)
ABBREV = re.compile(r"(?:\b(?:Nr|Art|Abs|lit|Ziff|bzw|ca|vgl|z|B|u|a|s|S|al|ch|cf|resp|etc|Dr|Prof|St|Fr|CHF|"
                    r"Mio|Mrd|Jan|Feb|Aug|Sept|Okt|Nov|Dez|M|Mme|MM|n|No|cpv|cfr)\.)$")


def clean(s: str) -> str:
    return (s or "").replace("␣", " ").replace("­", "").strip()


def join_lines(texts: list[str]) -> tuple[str, list[int]]:
    """The text of a paragraph (hyphenation at line ends removed) and the start offset of each line."""
    out, starts = "", []
    for t in texts:
        t = clean(t)
        if out:
            if re.search(r"[a-zäöüàéè]-$", out) and t[:1].islower():
                out = out[:-1]
            else:
                out += " "
        starts.append(len(out))
        out += t
    return out, starts


def sentence_starts(text: str) -> list[int]:
    """Start offsets of the sentences (end mark . ! ? and a capital letter or a quotation mark after it). A
    period after an abbreviation or after a number of 1 or 2 digits (enumeration "1.", date "1. Juli") is
    not a sentence end."""
    starts = [0]
    for m in re.finditer(r"[.!?]\s+(?=[«\"„A-ZÄÖÜÀ-Ý])", text):
        before = text[max(0, m.start() - 6): m.start() + 1]
        if ABBREV.search(before) or re.search(r"(?:^|[\s(])\d{1,2}\.$", before):
            continue
        starts.append(m.end())
    return starts


def heading_like(a: dict, text: str, rx_match, block_lines: int = 1) -> bool:
    """A label: a heading, or a line that starts with a capital letter and is a block of its own (60 characters
    or less), or the label word followed by ":" or a tab."""
    if a["label"] in ("section_header", "title"):
        return True
    if text[:1].islower():
        return False
    rest = text[rx_match.end():] if rx_match else ""
    return (len(text) <= 60 and block_lines <= 2) or rest.lstrip(" ")[:1] in (":", "\t")


def marks(a: dict) -> set:
    return {(m[0], m[1]) for m in a.get("merkmale") or []}


# ------------------------------------------------------------------ runs and paragraphs

def runs(doc_id: str, answers: list[str]) -> list[tuple[str, list[int]]]:
    """Runs of text atoms of one family (atom indices), in atom order."""
    out: list[tuple[str, list[int]]] = []
    for i, x in enumerate(answers):
        if x not in v4.TEXT:
            continue
        f = sc.FAMILY[x]
        if out and out[-1][0] == f:
            out[-1][1].append(i)
        else:
            out.append((f, [i]))
    return out


def paragraphs_of(run: list[int], atoms: list[dict]) -> list[list[int]]:
    out: list[list[int]] = []
    for i in run:
        if out and atoms[out[-1][-1]]["block"] == atoms[i]["block"]:
            out[-1].append(i)
        else:
            out.append([i])
    return out


# ------------------------------------------------------------------ rule

def _sponsor(run: list[int], atoms: list[dict], carried: set) -> tuple[dict, dict]:
    """types {atom index: type}, info {paragraph start index: (rule, sure)}."""
    paras = paragraphs_of(run, atoms)
    types: dict[int, str] = {}
    info: dict[int, tuple[str, bool]] = {}
    state, label_depth = "submitted", None
    label_pos: list[int] = []          # positions in `run` of reasoning label atoms
    pos = {i: k for k, i in enumerate(run)}
    nlines = Counter(x["block"] for x in atoms)
    for para in paras:
        rule, sure = ("default" if state == "submitted" else "reasoning-continues"), state == "submitted"
        lines = [clean(atoms[i]["text"]) for i in para]
        text, starts = join_lines(lines)
        switch = set()
        sst = sentence_starts(text)
        for m in RX_DEMAND.finditer(text):
            ss = max(s for s in sst if s <= m.start())
            k = max(j for j, s in enumerate(starts) if s <= ss)
            if ss - starts[k] > 2:
                k += 1
            if k < len(para):
                switch.add(para[k])
        for i in para:
            a = atoms[i]
            t = clean(a["text"])
            if i in carried:
                types[i] = types.get(run[pos[i] - 1], state) if pos[i] else state
                continue
            mr = RX_REASONING.match(t) or (RX_WHY.match(t) if a["label"] == "section_header" else None)
            ms = RX_SUBMITTED_LABEL.match(t)
            if (mr and heading_like(a, t, mr, nlines[a["block"]])) or ("keyword", "reasoning") in marks(a):
                state = "reasoning"
                label_pos.append(pos[i])
                dm = re.match(r"^\s*((?:\d{1,2}\.)*\d{1,2})\.?\s", t)
                label_depth = dm.group(1).count(".") + 1 if dm else None
                rule, sure = "R-S1 label", True
            elif state == "reasoning" and ((ms and heading_like(a, t, ms, nlines[a["block"]])) or marks(a) & {
                    ("keyword", "proposal"), ("keyword", "questions"), ("keyword", "demand"), ("keyword", "recall")}
                    or (("affair_type", None) in marks(a) and t.rstrip().endswith(":"))):
                state = "submitted"
                rule, sure = "R-S3 submitted label", True
            elif state == "reasoning" and (i in switch or (i == para[0] and marks(a) & {
                    ("demand_formula", None), ("intro_questions", None)})):
                state = "submitted"
                rule, sure = "R-S4 request sentence", True
            elif state == "reasoning" and label_depth and a["label"] == "section_header":
                dm = re.match(r"^\s*((?:\d{1,2}\.)*\d{1,2})\.?\s", t)
                if dm and dm.group(1).count(".") + 1 == label_depth:
                    state = "submitted"
                    rule, sure = "R-S5 same heading level", True
            types[i] = state
        info[para[0]] = (rule, sure)
    # R-S2: headings directly before a reasoning label (rule H)
    for lp in label_pos:
        k = lp - 1
        while k >= 0 and atoms[run[k]]["label"] == "section_header" and types[run[k]] == "submitted" \
                and not RX_SUBMITTED_LABEL.match(clean(atoms[run[k]]["text"])) \
                and not marks(atoms[run[k]]) & {("keyword", "proposal"), ("keyword", "recall"), ("keyword", "questions")}:
            types[run[k]] = "reasoning"
            for p in paras:
                if run[k] in p:
                    info[p[0]] = ("R-S2 heading before label", True)
            k -= 1
    return types, info


def _first_sentence(text: str) -> str:
    st = sentence_starts(text)
    return text[: st[1]] if len(st) > 1 else text


def _formal(text: str, count: bool = True) -> bool:
    if RX_PROPOSAL_NOT.search(text):
        return False
    if not RX_PROPOSAL.search(_first_sentence(text)):
        return False
    return not count or len(sentence_starts(text)) <= 2


def _executive(run: list[int], atoms: list[dict], carried: set) -> tuple[dict, dict]:
    paras = paragraphs_of(run, atoms)
    types: dict[int, str] = {}
    info: dict[int, tuple[str, bool]] = {}
    state = "response"
    texts = [join_lines([atoms[i]["text"] for i in p])[0] for p in paras]
    for n, para in enumerate(paras):
        text = texts[n]
        first = atoms[para[0]]
        t0 = clean(first["text"])
        ml = RX_PROPOSAL_LABEL.match(t0)
        is_head = first["label"] in ("section_header", "title") or len(t0) <= 60
        rule, sure = "default", not RX_BROAD.search(text)
        rest = ml.group("rest") if ml else ""
        if ml and not RX_NOT_EXEC.search(rest) and (is_head or rest.lstrip(" ")[:1] in (":", "\t")):
            inline = rest.lstrip(" ")[:1] == "\t" or (not is_head and rest.lstrip(" ").startswith(":"))
            if inline and rest.strip(" :\t"):
                for i in para:
                    types[i] = "recommendation" if i == para[0] else state
                info[para[0]] = ("R-E1 inline label", True)
                continue
            state = "recommendation"
            rule, sure = "R-E1 label", True
        elif RX_WEAK_LABEL.match(t0) and is_head:
            nxt = texts[n + 1] if n + 1 < len(texts) else ""
            if nxt and _formal(nxt, count=False):
                state = "recommendation"
                rule, sure = "R-E2 weak label", True
            else:
                state = "response"
                rule = "R-E2 weak label without proposal"
        elif state == "recommendation" and first["label"] == "section_header" and not (
                t0[:1].islower() or RX_CONTINUE.match(t0)):
            state = "response"
            rule = "R-E1 end at heading"
        elif state == "recommendation":
            rule, sure = "R-E1 section", True
        if state == "response" and rule.startswith(("default", "R-E1 end")) and _formal(text):
            for i in para:
                types[i] = "recommendation"
            info[para[0]] = ("R-E3 proposal sentence", False)
            if text.rstrip().endswith(":"):
                state = "recommendation"
            continue
        for i in para:
            types[i] = state
        info[para[0]] = (rule, sure)
    for i in run:
        if i in carried:
            k = run.index(i)
            types[i] = types[run[k - 1]] if k else types[i]
    return types, info


def _plenary(run: list[int], atoms: list[dict], carried: set) -> tuple[dict, dict]:
    paras = paragraphs_of(run, atoms)
    types: dict[int, str] = {}
    info: dict[int, tuple[str, bool]] = {}
    state = "vote"
    for n, para in enumerate(paras):
        t0 = clean(atoms[para[0]]["text"])
        rule = "default"
        if RX_VOTE.search(t0) or ("keyword", "resolution") in marks(atoms[para[0]]):
            state, rule = "vote", "R-P vote"
        elif RX_SPEAKER.match(t0):
            state, rule = "speech", "R-P speaker"
            k = n - 1
            while k >= 0 and atoms[paras[k][0]]["label"] == "section_header" and not RX_VOTE.search(
                    clean(atoms[paras[k][0]]["text"])):
                for i in paras[k]:
                    types[i] = "speech"
                info[paras[k][0]] = ("R-P heading before speaker", True)
                k -= 1
        for i in para:
            types[i] = state
        info[para[0]] = (rule, True)
    return types, info


def _title(run: list[int], atoms: list[dict], carried: set) -> tuple[dict, dict]:
    types, info = {}, {}
    for para in paragraphs_of(run, atoms):
        st = "short_title" if RX_SHORT_TITLE.match(clean(atoms[para[0]]["text"])) else "title"
        for i in para:
            types[i] = st
        info[para[0]] = ("R-T label" if st == "short_title" else "default", True)
    return types, info


RULES = {"SPONSOR": _sponsor, "EXECUTIVE": _executive, "PLENARY": _plenary, "TITLE": _title}


def predict_rule(doc_id: str, answers: list[str]) -> dict:
    """S5 by the rule. answers: E20 answers that give the families (reference, or composed with default types).

    Returns {"s5": {atom id: type}, "paragraphs": [...]} for the atoms of the families with more than one type.
    """
    atoms = sc.atoms(doc_id)
    carried = v4.carried_ids(atoms)
    cidx = {i for i, a in enumerate(atoms) if a["id"] in carried}
    s5: dict[str, str] = {}
    paras = []
    for fam, run in runs(doc_id, answers):
        if fam not in RULES:
            continue
        types, info = RULES[fam](run, atoms, cidx)
        for i in run:
            s5[atoms[i]["id"]] = types[i]
        for p in paragraphs_of(run, atoms):
            rule, sure = info.get(p[0], ("default", True))
            paras.append({"family": fam, "block": atoms[p[0]]["block"], "first": atoms[p[0]]["id"],
                          "last": atoms[p[-1]]["id"], "atoms": [atoms[i]["id"] for i in p],
                          "type": Counter(types[i] for i in p).most_common(1)[0][0],
                          "rule": rule, "sure": sure, "source": "rule"})
    return {"s5": s5, "paragraphs": paras}


# ------------------------------------------------------------------ measurement

def metrics(doc_ids: list[str], preds: dict[str, dict[str, str]], source: str) -> dict:
    docs = sc.load()
    n = ok = n_default_ok = 0
    by_fam = defaultdict(lambda: [0, 0])
    conf = Counter()
    br = bh = good = 0
    docs_exact = 0
    for d in doc_ids:
        x = docs[d]
        ref = sc.reference(d, source)
        pred = preds.get(d, {})
        atoms = sc.atoms(d)
        carried = v4.carried_ids(atoms)
        doc_ok = True
        for a, r in zip(x.ids, ref):
            if r not in v4.TEXT or sc.FAMILY[r] not in sc.MULTI_TYPE:
                continue
            f = sc.FAMILY[r]
            p = pred.get(a)
            p = p if p in sc.MEMBERS[f] else sc.DEFAULT_TYPE[f]
            n += 1
            ok += p == r
            n_default_ok += r == sc.DEFAULT_TYPE[f]
            by_fam[f][0] += 1
            by_fam[f][1] += p == r
            if p != r:
                conf[f"{r}->{p}"] += 1
                doc_ok = False
        seq = [(a, r) for a, r in zip(x.ids, ref) if r in v4.TEXT and a not in carried]
        prev = None
        for a, r in seq:
            f = sc.FAMILY[r]
            p = pred.get(a)
            p = p if p in sc.MEMBERS[f] else sc.DEFAULT_TYPE[f]
            if prev and prev[0] == f:
                rb = prev[1] != r
                hb = prev[2] != p
                br += rb
                bh += hb
                good += hb and rb and p == r and prev[2] == prev[1]
            prev = (f, r, p)
        docs_exact += doc_ok
    f1 = lambda tp, nh, nr: round(2 * tp / (nh + nr), 4) if nh + nr else None  # noqa: E731
    lo_p = v4.jeffreys_lower(good, bh) or 0.0
    lo_r = v4.jeffreys_lower(good, br) or 0.0
    hyp = {d: sc.oracle(d, source, s5=preds.get(d, {})) for d in doc_ids}
    tot = sc.measure(doc_ids, hyp, source)
    return {
        "documents": len(doc_ids), "atoms": n,
        "accuracy": round(ok / n, 4) if n else None,
        "accuracy_default_only": round(n_default_ok / n, 4) if n else None,
        "accuracy_by_family": {f: {"atoms": v[0], "accuracy": round(v[1] / v[0], 4)} for f, v in sorted(by_fam.items())},
        "type_boundaries_ref": br, "type_boundaries_hyp": bh, "type_boundaries_correct": good,
        "type_split_f1": f1(good, bh, br) if br else None,
        "type_split_f1_lower": round(2 * lo_p * lo_r / (lo_p + lo_r), 4) if lo_p and lo_r else (0.0 if br else None),
        "type_split_precision": round(good / bh, 4) if bh else None,
        "type_split_recall": round(good / br, 4) if br else None,
        "documents_s5_exact": docs_exact,
        "errors": dict(conf.most_common()),
        "e20_total_oracle_s1_s4": {k: tot[k] for k in ("labelled_f1", "labelled_f1_lower", "boundaries_ref",
                                                       "boundaries_hyp", "text_class_error", "document_exact_rate")},
    }


def reference_answers(d: str, split: str) -> list[str]:
    return sc.reference(d, SPLIT_SOURCE[split])


# ------------------------------------------------------------------ Apertus

def load_prompt(version: str | None = None) -> dict:
    """Sections of src/prompts/s5_type.txt: [system] and, for each family and prompt version, "[FAMILY vN]" with
    the choices (output=type) and the question. A version without a section for a family uses its v1 section."""
    version = version or PROMPT_VERSION
    sec, cur = {}, None
    for line in PROMPT_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        m = re.match(r"^\[(\w+)(?:\s+(v\d+))?\]\s*$", line)
        if m:
            cur = (m.group(1), m.group(2) or "")
            sec[cur] = []
            continue
        if cur:
            sec[cur].append(line)
    out = {"system": "\n".join(sec[("system", "")]).strip(), "version": version}
    for fam in ASKED_FAMILIES:
        lines = sec.get((fam, version)) or sec[(fam, "v1")]
        ch = next(x for x in lines if x.startswith("choices:"))[len("choices:"):]
        choices = dict(tuple(y.strip() for y in c.split("=")) for c in ch.split("|"))
        q = "\n".join(x for x in lines if not x.startswith("choices:")).strip()
        out[fam] = {"choices": choices, "question": q}
    text = json.dumps({k: out[k] for k in ("system",) + ASKED_FAMILIES}, ensure_ascii=False, sort_keys=True)
    out["sha256"] = hashlib.sha256(text.encode()).hexdigest()[:16]
    return out


def question_for(fam: str, para: dict, atoms_by_id: dict, prompt: dict) -> str:
    words = " ".join(clean(atoms_by_id[a]["text"]) for a in para["atoms"]).split()
    start = " ".join(words[:12]) + (" …" if len(words) > 12 else "")
    span = para["first"] if para["first"] == para["last"] else f"{para['first']} bis {para['last']}"
    return prompt[fam]["question"].format(span=span, start=start.replace("{", "(").replace("}", ")"))


def ask_paragraphs(jobs: list[tuple[str, dict]], workers: int = 8) -> dict[tuple[str, str, str], dict]:
    """jobs: [(doc id, paragraph)] -> {(doc, family, first atom): {"type", "answer", "probs", "p"}}."""
    prompt = load_prompt()
    by_doc: dict[str, dict] = {}

    def one(job):
        d, para = job
        fam = para["family"]
        if d not in by_doc:
            by_doc[d] = {a["id"]: a for a in sc.atoms(d)}
        q = question_for(fam, para, by_doc[d], prompt)
        ch = prompt[fam]["choices"]
        r = sc.ask(d, q, choices=list(ch), system=prompt["system"], tag=TAG)
        probs = {ch[k]: v for k, v in r["probs"].items()}
        return (d, fam, para["first"]), {"type": ch[r["answer"]], "answer": r["answer"], "probs": probs,
                                         "p": r["p"], "usage": r["usage"]}

    out = {}
    jobs = sorted(jobs, key=lambda j: (j[0], j[1]["first"]))
    with cf.ThreadPoolExecutor(workers) as ex:
        for k, (key, val) in enumerate(ex.map(one, jobs)):
            out[key] = val
            if (k + 1) % 50 == 0:
                print(f"  {k + 1}/{len(jobs)} paragraphs", flush=True)
    return out


def dev_sample(n: int = SAMPLE_DEV) -> list[str]:
    dev = sc.splits()["dev"]
    key = lambda d: hashlib.sha256(d.encode()).hexdigest()  # noqa: E731
    special, plain = [], []
    for d in sorted(dev, key=key):
        lab = sc.doc_labels(d)
        has_text = any(sc.FAMILY[t] in ASKED_FAMILIES for t in lab["s5"].values())
        if not has_text:
            continue
        nd = any(t not in sc.DEFAULT_TYPE.values() for t in lab["s5"].values())
        (special if nd else plain).append(d)
    return special[: n // 2] + plain[: n - n // 2]


def apply_apertus(pred_rule: dict, answers: dict, only_unsure: bool) -> dict:
    """S5 from the rule paragraphs; Apertus answers replace all paragraphs (or only the not-sure ones)."""
    s5 = dict(pred_rule["s5"])
    paras = []
    for p in pred_rule["paragraphs"]:
        q = dict(p)
        key = (None, p["family"], p["first"])
        ans = answers.get(key[1:])
        if p["family"] in ASKED_FAMILIES and ans is not None and (not only_unsure or not p["sure"]):
            for a in p["atoms"]:
                s5[a] = ans["type"]
            q.update(type=ans["type"], source="apertus", probs=ans["probs"], p=ans["p"])
        elif not only_unsure and p["family"] in ASKED_FAMILIES:
            raise KeyError(f"no Apertus answer for {p['family']} {p['first']}")
        paras.append(q)
    return {"s5": s5, "paragraphs": paras}


# ------------------------------------------------------------------ files

def write_variant(variant: str, split: str, docs: list[str], preds: dict, extra: dict | None = None) -> dict:
    m = metrics(docs, {d: preds[d]["s5"] for d in docs}, SPLIT_SOURCE[split])
    OUT.mkdir(parents=True, exist_ok=True)
    body = {"version": VERSION, "variant": variant, "split": split, "reference": SPLIT_SOURCE[split],
            "families_from": "reference answers (oracle S1 to S4 and S3)", "documents": docs,
            "metrics": m, **(extra or {}),
            "decisions": {d: preds[d] for d in docs}}
    (OUT / f"{variant}_{split}.json").write_text(json.dumps(body, ensure_ascii=False, indent=0), encoding="utf-8")
    return m


def rule_preds(docs: list[str], split: str) -> dict:
    return {d: predict_rule(d, reference_answers(d, split)) for d in docs}


def answers_path(split: str, version: str | None = None) -> Path:
    return OUT / f"apertus_answers_{split}_{version or PROMPT_VERSION}.json"


def cached_answers(split: str, version: str | None = None) -> dict:
    p = answers_path(split, version)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {(r["doc_id"], r["family"], r["first"]): r for r in raw["answers"]}


def save_answers(split: str, answers: dict) -> None:
    old = cached_answers(split)
    old.update(answers)
    rows = [dict(v, doc_id=k[0], family=k[1], first=k[2]) for k, v in sorted(old.items())]
    OUT.mkdir(parents=True, exist_ok=True)
    answers_path(split).write_text(
        json.dumps({"version": VERSION, "prompt_version": PROMPT_VERSION, "prompt_sha256": load_prompt()["sha256"],
                    "model": sc.MODEL,
                    "answers": rows}, ensure_ascii=False, indent=0), encoding="utf-8")


def answers_for_doc(ans: dict, d: str) -> dict:
    return {(k[1], k[2]): v for k, v in ans.items() if k[0] == d}


def usage_of(ans: dict) -> dict:
    u = Counter()
    for v in ans.values():
        for k, x in (v.get("usage") or {}).items():
            u[k] += x
    return dict(u)


# ------------------------------------------------------------------ commands

def cmd_rule(splits: tuple[str, ...]) -> None:
    sp = sc.splits()
    for split in splits:
        docs = sp[split]
        m = write_variant("rule", split, docs, rule_preds(docs, split))
        print(split, json.dumps({k: v for k, v in m.items() if k != "errors"}, ensure_ascii=False))
        print("   errors", m["errors"])


def cmd_errors() -> None:
    """Rule errors on dev only (rule design must not use eval or gold)."""
    for d in sc.splits()["dev"]:
        ref = reference_answers(d, "dev")
        pr = predict_rule(d, ref)
        atoms = {a["id"]: a for a in sc.atoms(d)}
        rinfo = {a: p["rule"] for p in pr["paragraphs"] for a in p["atoms"]}
        bad = [(a, r, pr["s5"].get(a)) for a, r in zip(sc.load()[d].ids, ref)
               if r in v4.TEXT and sc.FAMILY[r] in sc.MULTI_TYPE and pr["s5"].get(a) != r]
        if bad:
            print(f"## {d} ({len(bad)} atoms)")
            for a, r, p in bad[:12]:
                print(f"   {a:8} ref {r:15} rule {p:15} [{rinfo.get(a)}] {clean(atoms[a]['text'])[:90]}")


def cmd_apertus(split: str, workers: int, unsure_only_dev: bool, unsure_only: bool = False) -> None:
    """dev: all paragraphs of the dev sample and the not-sure paragraphs of all other dev documents.
    eval, gold: all paragraphs, or with unsure_only only the not-sure paragraphs (for the combined variant)."""
    sp = sc.splits()
    if split == "dev":
        docs = dev_sample()
    else:
        docs = sp[split]
    jobs = []
    for d in docs:
        pr = predict_rule(d, reference_answers(d, split))
        jobs += [(d, p) for p in pr["paragraphs"] if p["family"] in ASKED_FAMILIES
                 and not (unsure_only and split != "dev" and p["sure"])]
    if split == "dev" and unsure_only_dev:
        docs_all = sp["dev"]
        for d in docs_all:
            if d in docs:
                continue
            pr = predict_rule(d, reference_answers(d, split))
            jobs += [(d, p) for p in pr["paragraphs"] if p["family"] in ASKED_FAMILIES and not p["sure"]]
    have = cached_answers(split)
    todo = [j for j in jobs if (j[0], j[1]["family"], j[1]["first"]) not in have]
    print(f"{split} prompt {PROMPT_VERSION}: {len(jobs)} paragraphs, {len(todo)} to ask", flush=True)
    new = ask_paragraphs(todo, workers) if todo else {}
    save_answers(split, new)


def _key(m: dict) -> tuple:
    return (m["type_split_f1"] or 0.0, m["accuracy"] or 0.0)


def cmd_variants() -> tuple[dict, dict]:
    """rule, apertus and combined variants from the cached answers; returns (metrics of all variants,
    dev metrics of each prompt version: apertus on the dev sample, combined on all dev)."""
    sp = sc.splits()
    allm: dict = {}
    prompt_dev: dict = {}
    smp = dev_sample()
    rp_dev = rule_preds(sp["dev"], "dev")

    def unsure(docs, rp):
        return [(d, p) for d in docs for p in rp[d]["paragraphs"] if p["family"] in ASKED_FAMILIES and not p["sure"]]

    for v in PROMPT_VERSIONS:
        ans = cached_answers("dev", v)
        if ans and all((d, p["family"], p["first"]) in ans for d in smp for p in rp_dev[d]["paragraphs"]
                       if p["family"] in ASKED_FAMILIES):
            ap = {d: apply_apertus(rp_dev[d], answers_for_doc(ans, d), only_unsure=False) for d in smp}
            prompt_dev[f"apertus {v} (dev sample)"] = metrics(smp, {d: ap[d]["s5"] for d in smp}, "ref")
        if ans and all((d, p["family"], p["first"]) in ans for d, p in unsure(sp["dev"], rp_dev)):
            cb = {d: apply_apertus(rp_dev[d], answers_for_doc(ans, d), only_unsure=True) for d in sp["dev"]}
            prompt_dev[f"combined {v} (all dev)"] = metrics(sp["dev"], {d: cb[d]["s5"] for d in sp["dev"]}, "ref")
    for kind, chosen in (("apertus", CHOSEN_PROMPT), ("combined", COMBINED_PROMPT)):
        cand = {k.split()[1]: m for k, m in prompt_dev.items() if k.startswith(kind)}
        if cand and max(cand, key=lambda v: _key(cand[v])) != chosen:
            print(f"WARNING: for {kind}, the best prompt on dev is not {chosen}")
    for split in ("dev", "eval", "gold"):
        docs_all = sp[split]
        rp = rp_dev if split == "dev" else rule_preds(docs_all, split)
        allm.setdefault("rule", {})[split] = write_variant("rule", split, docs_all, rp)
        ans = cached_answers(split, CHOSEN_PROMPT)
        docs_ap = smp if split == "dev" else docs_all
        if ans and all((d, p["family"], p["first"]) in ans for d in docs_ap for p in rp[d]["paragraphs"]
                       if p["family"] in ASKED_FAMILIES):
            ap = {d: apply_apertus(rp[d], answers_for_doc(ans, d), only_unsure=False) for d in docs_ap}
            extra = {"prompt": str(PROMPT_FILE.relative_to(sc.ROOT)), "prompt_version": CHOSEN_PROMPT,
                     "prompt_sha256": load_prompt(CHOSEN_PROMPT)["sha256"],
                     "cscs": usage_of({k: v for k, v in ans.items() if k[0] in docs_ap})}
            allm.setdefault("apertus", {})[split] = write_variant("apertus", split, docs_ap, ap, extra)
            if split == "dev":
                allm.setdefault("rule_on_apertus_docs", {})[split] = metrics(smp, {d: rp[d]["s5"] for d in smp}, "ref")
        else:
            print(f"{split}: apertus ({CHOSEN_PROMPT}) has no complete answers")
        ans_c = cached_answers(split, COMBINED_PROMPT)
        un = unsure(docs_all, rp)
        if all((d, p["family"], p["first"]) in ans_c for d, p in un):     # no not-sure paragraph: combined = rule
            cb = {d: apply_apertus(rp[d], answers_for_doc(ans_c, d), only_unsure=True) for d in docs_all}
            keys = {(d, p["family"], p["first"]) for d, p in un}
            extra = {"prompt": str(PROMPT_FILE.relative_to(sc.ROOT)), "prompt_version": COMBINED_PROMPT,
                     "prompt_sha256": load_prompt(COMBINED_PROMPT)["sha256"], "unsure_paragraphs": len(un),
                     "cscs": usage_of({k: v for k, v in ans_c.items() if k in keys})}
            allm.setdefault("combined", {})[split] = write_variant("combined", split, docs_all, cb, extra)
        else:
            print(f"{split}: combined ({COMBINED_PROMPT}) has no complete answers")
    return allm, prompt_dev


def cmd_report() -> None:
    allm, prompt_dev = cmd_variants()
    # The choice uses dev only. rule and combined cover all dev documents; apertus covers the dev sample,
    # so it is compared with the rule on the same sample. Order: type-split F1, then atom accuracy; a tie
    # keeps the simpler variant (rule before combined before apertus).
    dev = {"rule": _key(allm["rule"]["dev"])}
    basis = {"rule (all dev)": allm["rule"]["dev"], }
    best = "rule"
    if "dev" in allm.get("combined", {}):
        basis["combined (all dev)"] = allm["combined"]["dev"]
        if _key(allm["combined"]["dev"]) > dev["rule"]:
            best = "combined"
    if "dev" in allm.get("apertus", {}):
        basis["apertus (dev sample)"] = allm["apertus"]["dev"]
        basis["rule (dev sample)"] = allm["rule_on_apertus_docs"]["dev"]
        for v, m in prompt_dev.items():
            basis[f"prompt {v}"] = m
        if best == "rule" and _key(allm["apertus"]["dev"]) > _key(allm["rule_on_apertus_docs"]["dev"]):
            best = "apertus"
    rep = {"version": VERSION, "best_variant_by_dev": best,
           "prompt_versions_chosen_on_dev": {"apertus": CHOSEN_PROMPT, "combined": COMBINED_PROMPT},
           "prompt_versions_dev": prompt_dev,
           "dev_basis": {k: {"type_split_f1": v["type_split_f1"], "accuracy": v["accuracy"]} for k, v in basis.items()},
           "metrics": allm}
    (OUT / "metrics.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for v, m in allm.items():
        for s, x in m.items():
            print(f"{v:22} {s:5} docs {x['documents']:3} acc {x['accuracy']} (default {x['accuracy_default_only']}) "
                  f"F1 {x['type_split_f1']} [{x['type_split_f1_lower']}] P {x['type_split_precision']} "
                  f"R {x['type_split_recall']} b {x['type_boundaries_correct']}/{x['type_boundaries_hyp']}/"
                  f"{x['type_boundaries_ref']} E20 {x['e20_total_oracle_s1_s4']['labelled_f1']} "
                  f"ce {x['e20_total_oracle_s1_s4']['text_class_error']} errors {x['errors']}")
    print("best by dev:", best, rep["dev_basis"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("rule", "errors", "apertus", "report"))
    ap.add_argument("--split", default="dev", choices=("dev", "eval", "gold"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--all", action="store_true", help="rule: dev, eval and gold")
    ap.add_argument("--prompt", default=None, choices=PROMPT_VERSIONS, help="prompt version (default: CHOSEN_PROMPT)")
    ap.add_argument("--no-unsure", action="store_true", help="dev: do not ask the not-sure paragraphs of all dev docs")
    ap.add_argument("--unsure-only", action="store_true", help="eval, gold: only the not-sure paragraphs (combined)")
    a = ap.parse_args()
    global PROMPT_VERSION
    PROMPT_VERSION = a.prompt or CHOSEN_PROMPT
    if a.cmd == "rule":
        cmd_rule(("dev", "eval", "gold") if a.all else (a.split,))
    elif a.cmd == "errors":
        cmd_errors()
    elif a.cmd == "apertus":
        cmd_apertus(a.split, a.workers, not a.no_unsure, a.unsure_only)
    else:
        cmd_report()


if __name__ == "__main__":
    main()

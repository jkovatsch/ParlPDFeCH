"""The values of the Apertus step in the record: heads output, combined reader, place of the Apertus type, near marks.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), builder B
of the Apertus build of 15./16.10.2026, for the main agent. Status: EXCEPTION, NOT RELEASED. No human checked this
file. This file changes no existing file. It imports the frozen readers and does not change them.
Spec: scratchpad apertus-build/SPEC.md, chapter 4 (with the order G1 to G3 of the owner of 15.10.2026, 23:41).
Edit of 16.10.2026 (step of the terminal table, owner 06:20): chapter 4 and the functions
entry_tier, suggestion_probability and suggestions (the Apertus suggestions below the entry limit); the key
suggestions of summary_facts. No result of the other functions changes.

1 Task
  The Apertus step gives the layer-20 states of the questions Q0, Q1 and Q2.B<n> (template gj_values_v1_de) of one
  document. This file makes the record values from them, with the rules of the one fixed run of 13.10.2026:
  heads_output        the 8 heads of heads2.npz (final head, model 5) on the layer-20 states, as
                      m11_value_heads2.apply_document (strict False, catch_all True: as cmd_apply of the fixed run),
                      plus the key q2_top (top block, head probability, top-two gap of each Q2 field)
  combined_values     the combined reader m11_values_combined.read_document_combined (frozen, not changed), then
                      the place of an Apertus type (q1_place) and the near marks (near_marks)
  merge_calibration   the calibration file of the Apertus mode: the product file of the rules plus the 2 Apertus
                      tiers of heads2/calibration_dev_combined.json
  reading_for_validator  the reading of check C22 of src/m12_validate.py (the same calls as the writer path)
  summary_facts       the facts of the terminal summary and of convert.json (numbers, classes and block ids only)
  suggestions         the Apertus suggestions below the entry limit (chapter 4; the last step of combined_values)

2 The place of an Apertus type (owner point 3 of 15.10.2026: "wieso können wir keine seitangabe geben")
  Apertus decides the type (head Q1 on the whole document). Code then searches the type words of the rule reader
  (m11_values_type_number: INSTRUMENT_RX, COMPOUND_RX and SPACED_RX for the instruments of a parliament in German,
  French and Italian; the line-start words Anfrage, Auftrag, Question; GOVERNMENT_RX and the short form MM for
  draft_decree) in the blocks, in reading order: each line folded (the line tiers of the rule reader) and each
  block folded with dehyphen (its block tiers). The first word whose list value (_type_value, the term list
  typ_lokal) is the Apertus type gives page, block and span. If no block has such a word, a second pass searches
  the line-only words (Anfrage, Auftrag, Question) as whole words at any place of a short head line (one of the
  first 15 lines, with at most 8 words: a title, not a sentence). For draft_decree a third pass takes a word of a
  short head line whose list value by the term list typ_lokal is draft_decree (Beschluss, Kredit, Crédit, Verordnung, Gesetz, Antrag, Reglement, Budget, ...): GOVERNMENT_RX of
  the rule reader is a short part of that term list. The record then says: place found by code, decision by
  Apertus. Check C20 makes the type again from the wording at this span with the same function _type_value.
  If neither pass finds such a word, the result is "no evidence in the text": the record does not write the Apertus
  type (the writer needs a span for each written value) and the combined reader gives the result of the rules
  for the type (the cascade selection of the rules).
  A list of options (fix step of 16.10.2026, finding of the examiner): a form can name each type as a box to tick
  (879146: the blocks MOTION / POSTULAT / INTERPELLATON / QUESTION, each a short block of its own). Then the word
  shows only that the type is named there, not which box was chosen. Code takes the run of short blocks (at most
  OPTION_WORDS words each, on the same page, next to each other) that holds the place (a longer block: only that
  block). If the type words of this run give 2 or more different types, the detail of the value has the key
  place_option_types (the sorted types), and the label note says so. The place rule does not change.

3 Near marks (owner point 2 of 15.10.2026)
  The heads were fit on torch CUDA bf16 states of one H100. Another runtime gives other bf16 noise. A decision whose
  probability is near a threshold can differ from the fixed run. Thresholds: Q1 0.80 (and the gap to the second
  class); Q2 0.50 (a value) and 0.80 (band hi), and the gap between the top block and the second block.
  Margin of each backend (feasibility test of 15.10.2026, final head, |p Mac - p H100| over 14 dev documents):
  MLX max 0.015 (Q1) and 0.047 (sponsor top block) on these 14 documents; on 16 more development documents (fix
  step of 16.10.2026, each with an Apertus value of the fold heads) max 0.097 (the Q1 top probability of 236623:
  0.7988 on H100, 0.7021 on MLX) and 0.055 (a sponsor top block): 0.10 (before: 0.05, which did not cover this).
  torch MPS max 0.073 and 0.062 on 14 documents: 0.10 (the same kind of kernel noise as MLX). CUDA: 0.10: the
  states of the fit came from one H100 with the frozen engine, but another NVIDIA GPU has other bf16 kernels, and
  no CUDA run of this code was measured. CPU: not measured: 0.10. stored (the H100 states of the fixed run, a test
  aid): 0.05. A remote backend "remote:<b>" gets the margin of <b>. A backend that this table does not name gets
  the largest margin. The near mark is a warning, not a guarantee.

4 Suggestions below the entry limit (owner, 16.10.2026: completeness first, then a filter of what is sure)
  Of the 9 Q2 tiers of entry.json, only apertus_q2_sponsor_hi entered: only its values go into the eCH-0295 part.
  The other Q2 heads can also give a value. Such a value is a "suggestion below the entry limit" (status
  below_entry_limit). It is not a statement of the eCH-0295 record: the writer puts it only into the values file
  (<prefix>.values.ttl, class pvl:Suggestion, pvl:inRecord false) and into the manifest key apertus_suggestions.
  Condition (the condition of the entry design: cmd_table of src/m11_value_heads2.py, stage 3 of
  src/m11_values_combined.py), for each Q2 field of the final result of combined_values:
    1 the cascade searches the field for the kind of the document (else the head is not called, rule I5, item 14);
    2 the combined reader called the head: the rules found no value, or only a value of a weak tier (rule I5,
      item 7: a rule value of a tier that is not weak stays, and the head is not called);
    3 the head gave a value: the top block has a head probability of 0.50 or more, and the span function of the
      field gives a value in the top block (else the reason no_cue, no_pattern or reader_error: no value);
    4 the tier of the value did not enter (entry.json). Tier id: mode bands gives apertus_q2_<field>_<band>
      (band hi at 0.80 or more, else lo); mode one gives apertus_q2_<field>.
  Probability: (equal + 0.5) / (equal + different + 1) of the tier in entry.json, then m10_calibrate.as_written
  (0.005 to 0.995, 4 decimals; the function of each label probability). The units are the development documents
  of the design set under the same condition, with the out-of-fold heads; the reference is the OpenParlData export.
  The converter uses the final head (this is also true for the 2 tiers that entered).
  No suggestion comes from Q0 (the head did not enter and gives no field value), from Q1 (a class below 0.80 or the
  class none has no measured tier; a class that differs from the type of the rules has no measured tier for this
  condition; a Q1 type with no type word in the text is not below the entry limit and has no page or span), or from
  a Q2 head below 0.50, with no value in the top block or with a reader error (the design gave no value: no
  measured tier).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_values_base as vb  # noqa: E402  (frozen interface of the value readers)
import m11_values_cascade as cvc  # noqa: E402  (frozen cascade reader)
import m11_values_combined as cmb  # noqa: E402  (frozen combined reader of addendum I)
import m11_values_type_number as tn  # noqa: E402  (FIXED rule module: the type words and _type_value)

VERSION = "m12-apertus-values-1"
SCRIPT = "src/m12_apertus_values.py"
MODEL_NAME = "Apertus-v1.5-8B"
MERGED_REL = "daten/gj_values/apertus/calibration_values_apertus.json"     # only below a scratch root
PRODUCT_REL = "daten/gj_values/round4/calibration_dev_all.json"             # the product file of the rules
PRODUCT_SHA256 = "e48e7a8d8efdd1e10b68071df85275dc0c5b69e004bb8051b2aecd2a1d4229d7"   # = CALIBRATION_RULES_SHA256 of m11_value_heads2
HEADS_REL = "daten/gj_values/heads2"
COMBINED_CAL_NAME = "calibration_dev_combined.json"
LAYER = 20
FINAL_NAME = "final"
Q1_TIER = cmb.Q1_TIER                                    # "apertus_q1"
APERTUS_TIERS = ("apertus_q1", "apertus_q2_sponsor_hi")  # the tiers that entered (entry.json of 13.10.2026)
TIER_FIELDS = (("affair_type", "apertus_q1"), ("first_author", "apertus_q2_sponsor_hi"))   # calibration ids
Q1_RULE_ID = "m12_apertus_values.q1_place"
Q2_RULE_ID = "m11_value_heads2.read_q2"
PLACE_NOTE = ("place found by code (the first type word of this type in reading order; else a type word of the "
              "head lines), decision by Apertus (head Q1, layer 20, final head)")
NO_EVIDENCE = "no evidence in the text"
Q1_MIN = cmb.CLASS_MIN                                   # 0.80
Q2_VALUE_MIN = 0.50                                      # m11_value_heads2.P_VALUE_MIN
Q2_BAND_HI = 0.80                                        # m11_value_heads2.P_BAND_HI
NEAR_MARGIN = {"mlx": 0.10, "cuda": 0.10, "mps": 0.10, "cpu": 0.10, "stored": 0.05}
PLACE_KINDS = ("instrument", "word", "government")
APERTUS_RX = re.compile(r"apertus_[a-z0-9_]+\Z")
# chapter 4: the suggestions below the entry limit
SUGGESTION_STATUS = "below_entry_limit"
SUGGESTION_FORM = "parlpdfech-apertus-suggestions/1"
SUGGESTION_RULE = ("an Apertus value of a Q2 tier that did not enter (entry.json), under the condition of the entry "
                   "design: the rules found no value or only a value of a weak tier, the head probability of the top "
                   "block is 0.50 or more, and the span function of the field gives a value in the top block; not in "
                   "the eCH-0295 part")
PROBABILITY_RULE = ("(equal + 0.5) / (equal + different + 1) of the tier in entry.json (out-of-fold heads on the "
                    "development design set), then m10_calibrate.as_written (0.005 to 0.995, 4 decimals)")
CALLED_BECAUSE = ("rules_found_no_value", "weak_rule_tier")          # the 2 reasons of stage 3 of the combined reader
SUGGESTION_KEYS = ("field", "status", "in_record", "tier", "band", "called_because", "value", "printed", "normalised",
                   "k", "n", "probability", "head_probability", "top_two_gap", "near", "page", "last_page", "block",
                   "char_start", "char_end", "span_function", "option")
SUGGESTION_FACT_KEYS = ("field", "tier", "band", "probability", "k", "n", "head_probability", "near", "page", "block")


class PlaceError(Exception):
    """The place that code found does not give the Apertus type again (a fault of this file)."""


# ------------------------------------------------------------------ small helpers
def is_apertus_tier(tier) -> bool:
    return bool(APERTUS_RX.match(str(tier or "")))


def rule_id_of(tier) -> str | None:
    """The rule id of the label of an Apertus value. None: the tier is not an Apertus tier."""
    t = str(tier or "")
    if t == Q1_TIER:
        return Q1_RULE_ID
    if t.startswith("apertus_q2_"):
        return Q2_RULE_ID
    return None


def backend_base(backend: str | None) -> str:
    """'remote:cuda' -> 'cuda'; None -> 'stored'."""
    b = str(backend or "stored")
    return b.split(":", 1)[1] if b.startswith("remote:") else b


def margin_of(backend: str | None) -> float:
    return NEAR_MARGIN.get(backend_base(backend), max(NEAR_MARGIN.values()))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _round(x, n: int = 4):
    return None if x is None else round(float(x), n)


# ------------------------------------------------------------------ heads output (numpy; lazy import)
def q2_top(doc: vb.Doc, q2p: dict) -> dict:
    """{field: {block, page, probability, top_two_gap}} of the 6 Q2 heads over the blocks with text. The top block
    is that of m11_value_heads2.top_block (a tie goes to the first block). The gap is 1.0 with one such block."""
    import numpy as np  # noqa: PLC0415
    import m11_value_heads2 as h2  # noqa: PLC0415
    idx = [i for i, b in enumerate(doc.blocks) if b.text]
    out = {}
    for f, p in q2p.items():
        p = np.asarray(p, dtype=np.float64)
        i = h2.top_block(doc, p)
        if i is None:
            out[f] = {"block": None, "page": None, "probability": None, "top_two_gap": None}
            continue
        rest = sorted((float(p[j]) for j in idx if j != i), reverse=True)
        gap = float(p[i]) - rest[0] if rest else 1.0
        out[f] = {"block": doc.blocks[i].block, "page": doc.blocks[i].page, "probability": float(p[i]),
                  "top_two_gap": gap}
    return out


def heads_output(doc: vb.Doc, heads, x0, x1, x2, block_ids: list[str]) -> dict:
    """The heads output of one document from the layer-20 states: x0 [4096] (Q0), x1 [4096] (Q1), x2 [blocks, 4096]
    (Q2.B<n> in the order of block_ids). The same numbers as m11_value_heads2.apply_document(doc, states, heads,
    FINAL, strict=False, catch_all=True). The JSON form of m11_value_heads2.output_to_json, plus q2_top."""
    import numpy as np  # noqa: PLC0415
    import m11_value_heads2 as h2  # noqa: PLC0415
    if list(block_ids) != [b.block for b in doc.blocks]:
        raise h2.OtherSuffixIds(f"{doc.doc_id}: the suffix ids are not Q0, Q1 and Q2.B<n> for each block (rule I1, item 7)")
    if heads.layer != LAYER:
        raise ValueError(f"the heads file reads layer {heads.layer}, not {LAYER}")
    x2 = np.asarray(x2)
    q0p = heads.q0(np.asarray(x0)[None, :], h2.FINAL)[0]
    q1p = heads.q1(np.asarray(x1)[None, :], h2.FINAL)[0]
    q2p = {f: heads.q2(f, x2, h2.FINAL) for f in h2.Q2_FIELDS}
    ho = h2.output_to_json(h2.output_from_probabilities(doc, q0p, q1p, q2p, False, FINAL_NAME, True))
    ho["q2_top"] = q2_top(doc, q2p)
    return ho


def heads_output_from_states(doc: vb.Doc, states, heads) -> dict:
    """heads_output for a states object of m11_value_heads2_data (read_states)."""
    return heads_output(doc, heads, states.q0(LAYER), states.q1(LAYER), states.q2(LAYER), states.block_ids)


# ------------------------------------------------------------------ the place of an Apertus type
def _hits_of_folded(f: vb.Folded) -> list[tuple[int, int, str]]:
    """(start, end, kind) in Doc.text of the type words of one folded text (a line or a block)."""
    out = []
    for s, e, kind in tn._type_hits(f):
        if kind not in PLACE_KINDS:
            continue                                  # kind blocked: a head word with no value of the list
        if kind == "government" and f.text[s:e] in ("decret", "dekret") and tn.LAW_CITATION_RX.match(f.text, e):
            continue                                  # a law citation ("Décret du 4 février 1987") is not a kind
        ds, de = f.span(s, e)
        out.append((ds, de, kind))
    return out


def _block_hits(doc: vb.Doc, b: vb.Block) -> list[tuple[int, int, str]]:
    """(start, end, kind) in Doc.text of the type words of one block, in reading order: the words of the line
    tiers of the rule reader (each line folded; a line-start word such as Anfrage), the words of its block tiers
    (the block folded with dehyphen: a type word can go over a line end) and the short form MM."""
    found = set()
    for ln in b.lines:
        found.update(_hits_of_folded(vb.fold_map(ln.text, base=ln.char_start)))
    found.update(_hits_of_folded(vb.fold_map(b.text, base=b.char_start, dehyphen=True)))
    for m in tn.MM_RX.finditer(b.text):               # "MM N. 91/2019": the short form of Messaggio municipale
        found.add((b.char_start + m.start(), b.char_start + m.end(), "mm"))
    return sorted(found)


WORD_RX = re.compile(r"[^\W\d_]+")
SHORT_LINE_WORDS = 8                                     # a head line with at most 8 words: a title, not a sentence
TERM_LIST_TYPES = ("draft_decree",)


def _short_head_lines(doc: vb.Doc) -> list[vb.Line]:
    """The head lines (the first HEAD_LINES lines of the document, as the rule reader) with at most
    SHORT_LINE_WORDS words: title lines. A sentence of the text is longer."""
    return [ln for ln in doc.first_lines(tn.HEAD_LINES) if len(WORD_RX.findall(ln.text)) <= SHORT_LINE_WORDS]


def _head_word_hits(doc: vb.Doc) -> list[tuple[int, int, str]]:
    """Second pass: a line-only type word (Anfrage, Auftrag, Question; LINE_ONLY_RX of the rule reader) as a whole
    word at any place of a short head line, for example the title line "CONSEIL GÉNÉRAL ... - Question". The rule
    reader accepts such a word only at a line start."""
    out = []
    for ln in _short_head_lines(doc):
        f = vb.fold_map(ln.text, base=ln.char_start)
        for m in tn.LINE_ONLY_RX.finditer(f.text):
            if m.start() > 0 and f.text[m.start() - 1].isalnum():
                continue                              # not the start of a word
            ds, de = f.span(m.start(), m.end())
            out.append((ds, de, "head_word"))
    return out


def _term_list_hits(doc: vb.Doc) -> list[tuple[int, int, str]]:
    """Third pass (draft_decree only): a word of a short head line whose list value by the term list typ_lokal is a
    type (for example Beschluss, Kredit, Crédit, Verordnung, Gesetz, Antrag). GOVERNMENT_RX of the rule reader is a
    short part of this term list; the term list is the rule that check C20 uses for each type word."""
    out = []
    for ln in _short_head_lines(doc):
        for m in WORD_RX.finditer(ln.text):
            out.append((ln.char_start + m.start(), ln.char_start + m.end(), "term_list"))
    return out


def place_value(doc: vb.Doc, start: int, end: int, kind: str) -> str:
    """The list value of the wording at a span, by the rule that check C20 uses (m11_validate.remake)."""
    if kind == "mm":
        m = tn.MM_RX.match(doc.text, start)
        return "draft_decree" if m and m.end() == end else ""
    return tn._type_value(doc.text[start:end])


OPTION_WORDS = 4                                         # a block of a list of options: at most 4 words


def place_option_types(doc: vb.Doc, start: int) -> list[str]:
    """The sorted different types of the type words (pass 1, by the rule of check C20) in the run of short blocks
    that holds the place start: the block of the place and its neighbours on the same page while each has at most
    OPTION_WORDS words (a block of the place with more words: that block only). 2 or more types: the place is in a
    list of options (for example boxes to tick), not a statement of the type."""
    blocks = [b for b in doc.blocks if b.text]
    at = [i for i, b in enumerate(blocks) if b.char_start <= start < b.char_end]
    if not at:
        return []
    k = at[0]

    def short(b) -> bool:
        return len(WORD_RX.findall(b.text)) <= OPTION_WORDS
    run = [blocks[k]]
    if short(blocks[k]):
        i = k - 1
        while i >= 0 and blocks[i].page == blocks[k].page and short(blocks[i]):
            run.insert(0, blocks[i])
            i -= 1
        i = k + 1
        while i < len(blocks) and blocks[i].page == blocks[k].page and short(blocks[i]):
            run.append(blocks[i])
            i += 1
    return sorted({v for b in run for s, e, kind in _block_hits(doc, b) if e > s
                   for v in [place_value(doc, s, e, kind)] if v})


def q1_place(doc: vb.Doc, a_type: str) -> tuple[int, int, str] | None:
    """(start, end, kind) of the first type word of the type a_type in reading order, or None. Pass 1: the type
    words of the rule reader in each block. Pass 2 (only if pass 1 finds nothing): a line-only word in a head line.
    Pass 3 (draft_decree only, if passes 1 and 2 find nothing): a word of a head line by the term list typ_lokal."""
    passes = [h for b in doc.blocks if b.text for h in _block_hits(doc, b)], _head_word_hits(doc)
    if a_type in TERM_LIST_TYPES:
        passes += (_term_list_hits(doc),)
    for hits in passes:
        for s, e, kind in hits:
            if e > s and place_value(doc, s, e, kind) == a_type:
                return s, e, kind
    return None


# ------------------------------------------------------------------ the combined values
def _q1_value_record(doc: vb.Doc, rec: dict, place: tuple[int, int, str], ho: dict) -> dict:
    """The type record of the tier apertus_q1 with the span of the place."""
    s, e, kind = place
    q1 = ho.get("q1") or {}
    detail = {"q1_probability": (rec.get("detail") or {}).get("q1_probability", q1.get("probability")),
              "head": "Q1", "layer": LAYER, "model": ho.get("model"), "place": PLACE_NOTE, "place_kind": kind,
              "place_rule": f"{SCRIPT}, function q1_place ({VERSION})"}
    types = place_option_types(doc, s)
    if len(types) >= 2:
        detail["place_option_types"] = types         # a list of options: the word is there, the choice is not shown
    c = doc.candidate("affair_type", s, e, rec["normalised"], Q1_TIER, detail=detail)
    if place_value(doc, c.char_start, c.char_end, kind) != rec["normalised"]:
        raise PlaceError(f"{doc.doc_id}: the place does not give the type {rec['normalised']} again")
    return dict(c.to_json(), cascade=rec["cascade"])


def combined_values(doc: vb.Doc, ho: dict | None, entry: dict, weak: dict, rule_result: dict | None = None,
                    strict: bool = False, backend: str | None = None) -> dict:
    """The result of the combined reader (the rules of the fixed run) with the place of an Apertus type. Extra key
    apertus: {q1: {...}, values: [fields with an Apertus tier], near: {...} if a backend is given, suggestions:
    [...] (chapter 4; empty with no heads output)}."""
    if rule_result is None:
        rule_result = cvc.read_document(doc, strict=strict)
    res = cmb.read_document_combined(doc, ho, entry, weak, strict, None, rule_result)
    if res is rule_result:                            # no heads output: the reader gives the rule result itself
        res = copy.deepcopy(res)
    q1 = (ho or {}).get("q1") or {}
    info: dict = {"version": VERSION, "q1": {"class": q1.get("class"), "probability": q1.get("probability"),
                                             "given": q1.get("given"), "used": False, "place": None}}
    if (res.get("heads") or {}).get("q1_used"):
        a_type = res["fields"]["affair_type"]["normalised"]
        place = q1_place(doc, a_type)
        if place is not None:
            new = _q1_value_record(doc, res["fields"]["affair_type"], place, ho)
            res["fields"]["affair_type"] = new
            info["q1"].update(used=True, place="found_by_code", page=new["page"], block=new["block"],
                              char_start=new["char_start"], char_end=new["char_end"], place_kind=place[2],
                              place_option_types=(new.get("detail") or {}).get("place_option_types"))
        else:
            # no evidence in the text: the type of the rules (none) and the cascade selection of the rules
            entry2 = copy.deepcopy(entry)
            entry2.setdefault("q1", {})["entered"] = False
            res = cmb.read_document_combined(doc, ho, entry2, weak, strict, None, rule_result)
            info["q1"].update(used=False, place=NO_EVIDENCE, written=False)
    info["values"] = sorted(f for f, r in res["fields"].items() if r.get("found") and is_apertus_tier(r.get("tier")))
    res["apertus"] = info
    if backend is not None:
        res["apertus"]["near"] = near_marks(ho, res, backend)
    # chapter 4: the last step, on the final result (after the Q1 step and the near marks): no value changes
    res["apertus"]["suggestions"] = suggestions(doc, ho, res, entry) if ho else []
    return res


def near_marks(ho: dict | None, res: dict, backend: str | None) -> dict:
    """{margin, backend, q1: bool, q2: {field: bool}} and the keys near and near_margin in the detail of each value
    record with an Apertus tier (the writer note reads them)."""
    m = margin_of(backend)
    out = {"margin": m, "backend": backend, "q1": False, "q2": {}}
    if not ho:
        return out
    q1 = ho.get("q1") or {}
    probs = sorted((float(x) for x in q1.get("probabilities") or []), reverse=True)
    if probs:
        p1, p2 = probs[0], (probs[1] if len(probs) > 1 else 0.0)
        out["q1"] = bool(abs(p1 - Q1_MIN) < m or (p1 - p2) < m)
    top = ho.get("q2_top") or {}
    called = ((res.get("heads") or {}).get("q2") or {})
    for f in sorted(set(called) | ({"sponsor"} if "sponsor" in top else set())):
        t = top.get(f) or {}
        p, gap = t.get("probability"), t.get("top_two_gap")
        if p is None:
            out["q2"][f] = False
            continue
        out["q2"][f] = bool(abs(p - Q2_VALUE_MIN) < m or abs(p - Q2_BAND_HI) < m or (gap is not None and gap < m))
    for f, r in res["fields"].items():
        if r.get("found") and is_apertus_tier(r.get("tier")):
            near = out["q1"] if f == "affair_type" else bool(out["q2"].get(f))
            r["detail"] = dict(r.get("detail") or {}, near=near, near_margin=m, backend=backend)
    return out


def apertus_note(field: str, rec: dict, backend: str | None = None) -> str:
    """The note of the label of an Apertus value (before the comparison note of the reader)."""
    d = rec.get("detail") or {}
    b = backend or d.get("backend")
    where = f", backend {b}" if b else ""
    near = "; near a threshold (another runtime can give another decision)" if d.get("near") else ""
    if str(rec.get("tier")) == Q1_TIER:
        p = d.get("q1_probability")
        opts = d.get("place_option_types") or []
        option_list = (f"; the place is in a list of {len(opts)} types ({', '.join(opts)}), for example boxes to "
                       f"tick: it shows the word of the type, not the choice") if len(opts) >= 2 else ""
        return (f"decision by {MODEL_NAME} (head Q1, layer {LAYER}, final head{where}; head probability "
                f"{float(p):.2f}); place found by code (first type word of this type in reading order)"
                f"{option_list}{near}")
    p = d.get("head_probability")
    return (f"decision by {MODEL_NAME} (head Q2 {field}, layer {LAYER}, final head{where}; top block "
            f"{d.get('top_block')}, head probability {float(p):.2f}, band {d.get('band')}); value read by code "
            f"from the top block (span function {d.get('span_function')}){near}")


# ------------------------------------------------------------------ suggestions below the entry limit (chapter 4)
def entry_tier(entry: dict, field: str, band: str | None) -> tuple[str, dict] | None:
    """The tier id and the tier record of entry.json for a Q2 value of a band (chapter 4, item 4): the rule of
    m11_values_combined.read_document_combined with the key entered ignored. Mode bands: apertus_q2_<field>_<band>;
    mode one: apertus_q2_<field> (no band in the id). None: the field has no such tier record."""
    e = (entry.get("q2") or {}).get(field) or {}
    if e.get("mode") == "bands":
        if band not in cmb.BANDS:
            return None
        tier = cmb.q2_tier(field, band)
    elif e.get("mode") == "one":
        tier = cmb.q2_tier(field)
    else:
        return None
    rec = (e.get("tiers") or {}).get(tier)
    return (tier, rec) if isinstance(rec, dict) else None


def suggestion_probability(k: int, n: int) -> float:
    """(k + 0.5) / (n + 1) (the Jeffreys mean of k equal of n units), written as each label probability:
    m10_calibrate.as_written (the clip to 0.005 ... 0.995, then 4 decimals)."""
    import m10_calibrate as cal  # noqa: PLC0415  (frozen: as_written)
    return cal.as_written((int(k) + 0.5) / (int(n) + 1))


def suggestions(doc: vb.Doc, ho: dict | None, res: dict, entry: dict) -> list[dict]:
    """The Apertus suggestions below the entry limit of one document (chapter 4), in the order of
    m11_values_combined.Q2_FIELDS. `res`: the final result of combined_values (the cascade selection of the record).
    Each item has the keys SUGGESTION_KEYS. The value is the value that the eCH-0295 part would have if the tier had
    entered (m12_writer.record_value of the wording at the span). No value of `res` changes."""
    if not ho:
        return []
    import m12_writer as w12  # noqa: PLC0415  (record_value; m12_writer imports this file at module level)
    called = (res.get("heads") or {}).get("q2") or {}
    near = ((res.get("apertus") or {}).get("near") or {}).get("q2") or {}
    top = ho.get("q2_top") or {}
    heads_q2 = ho.get("q2") or {}
    out = []
    for f in cmb.Q2_FIELDS:
        rec = res["fields"].get(f) or {}
        if not (rec.get("cascade") or {}).get("searched"):
            continue                                  # item 1: the cascade does not search the field
        call = called.get(f)
        if not call or call.get("called_because") not in CALLED_BECAUSE:
            continue                                  # item 2: the head was not called
        gave = call.get("gave") or {}
        if not gave.get("found") or gave.get("tier") is not None or f not in heads_q2:
            continue                                  # item 3 (no value) or item 4 (the tier entered: a written value)
        band = gave.get("band")
        et = entry_tier(entry, f, band)
        if et is None or et[1].get("entered"):
            continue                                  # no tier record, or a tier that entered
        tier, trec = et
        cand = cmb.as_json(heads_q2[f])
        s, e = int(cand["char_start"]), int(cand["char_end"])
        printed = doc.text[s:e]
        if printed != cand["value"]:
            raise PlaceError(f"{doc.doc_id}: {f}: the wording at the span of the heads output is not its value")
        detail = cand.get("detail") or {}
        k, n = int(trec["equal"]), int(trec["equal"]) + int(trec["different"])
        out.append({"field": f, "status": SUGGESTION_STATUS, "in_record": False, "tier": tier, "band": band,
                    "called_because": call["called_because"],
                    "value": w12.record_value(f, printed, cand["normalised"]), "printed": printed,
                    "normalised": cand["normalised"], "k": k, "n": n, "probability": suggestion_probability(k, n),
                    "head_probability": _round(detail.get("head_probability", gave.get("head_probability"))),
                    "top_two_gap": _round((top.get(f) or {}).get("top_two_gap")), "near": bool(near.get(f)),
                    "page": doc.locate(s).page, "last_page": doc.locate(e - 1).page, "block": cand["block"],
                    "char_start": s, "char_end": e, "span_function": detail.get("span_function"),
                    "option": detail.get("option")})
    return out


# ------------------------------------------------------------------ calibration of the Apertus mode
def merge_calibration(product: dict, combined: dict, product_sha: str, combined_sha: str) -> dict:
    """The product file of the rules plus the 2 Apertus tiers of the combined file. The rule tiers keep the
    numbers of the product file. The rows of the key documents of the 2 Apertus tiers come from the combined file
    (they give in_sample for a development document whose value has an Apertus tier)."""
    out = copy.deepcopy(product)
    added, rows = [], 0
    for field, tier in TIER_FIELDS:
        t = combined["lookup"][field]["tiers"][tier]
        out["lookup"][field]["tiers"][tier] = copy.deepcopy(t)
        cid = t.get("calibration") or f"value.{field}.{tier}"
        out.setdefault("calibrations", {})[cid] = copy.deepcopy(combined["calibrations"][cid])
        added.append({"field": field, "tier": tier, "calibration": cid, "p_all_folds": t["p_all_folds"],
                      "k": t.get("k"), "n": t.get("n")})
        for d, row in (combined.get("documents") or {}).items():
            x = (row or {}).get(field)
            if isinstance(x, dict) and x.get("tier") == tier:
                out.setdefault("documents", {}).setdefault(d, {})[field] = copy.deepcopy(x)
                rows += 1
    out["documents"] = dict(sorted(out.get("documents", {}).items(), key=lambda kv: (len(kv[0]), kv[0])))
    out["merged"] = {"version": VERSION, "script": SCRIPT, "product_file": PRODUCT_REL, "product_sha256": product_sha,
                     "combined_file": f"{HEADS_REL}/{COMBINED_CAL_NAME}", "combined_sha256": combined_sha,
                     "tiers_added": added, "document_rows_of_the_apertus_tiers": rows,
                     "rule": "each rule tier and its calibration record are those of the product file; the 2 Apertus "
                             "tiers, their calibration records and their document rows come from the combined file"}
    return out


def write_merged(root: Path, product_p: Path | None = None, combined_p: Path | None = None) -> tuple[Path, str]:
    """Writes root/MERGED_REL. Returns (path, SHA-256). The same inputs give the same bytes."""
    root = Path(root)
    product_p = Path(product_p or root / PRODUCT_REL)
    combined_p = Path(combined_p or root / HEADS_REL / COMBINED_CAL_NAME)
    out = merge_calibration(json.loads(product_p.read_text(encoding="utf-8")),
                            json.loads(combined_p.read_text(encoding="utf-8")),
                            sha256_file(product_p), sha256_file(combined_p))
    p = root / MERGED_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p, sha256_file(p)


# ------------------------------------------------------------------ the reading of the validator (check C22)
def reading_for_validator(doc: vb.Doc, ho: dict, entry: dict, weak: dict, backend: str | None = None) -> dict:
    """The logic of m11_validate.Record.reading (kind from the rule chain), then combined_values. The kind source is
    the plain source of the rule chain (the writer manifest names it; Q0 never enters)."""
    vb.load_rule_modules()
    kind, source = cvc.kind_of(doc)
    kind_from = ("no rule file" if doc.s1_role is None else
                 "rule V5 of the cascade reader" if source.get("rule") == "V5" else "rule chain")
    rule = cvc.read_document(doc, kind=kind, strict=False)
    rule["kind_source"] = source
    res = combined_values(doc, ho, entry, weak, rule, strict=False, backend=backend)
    res["kind_source"] = source
    return res | {"kind_from": kind_from}


# ------------------------------------------------------------------ facts (terminal summary, convert.json)
def summary_facts(ho: dict | None, res: dict) -> dict:
    """{q1: {...}, q2: {field: {...}}, values_from_apertus: [...], near_margin, suggestions: [...]} of one document.
    Numbers, classes, tiers, page numbers and block ids only: no wording of the PDF."""
    near = (res.get("apertus") or {}).get("near") or {}
    info = (res.get("apertus") or {}).get("q1") or {}
    heads = res.get("heads") or {}
    q1 = (ho or {}).get("q1") or {}
    t = res["fields"]["affair_type"]
    rule_type = bool(t.get("found") and not is_apertus_tier(t.get("tier")))
    if info.get("used"):
        q1_state = "used"
    elif info.get("place") == NO_EVIDENCE:
        q1_state = "no_evidence"
    elif rule_type and heads.get("q1_differs"):
        q1_state = "rules_gave_the_type_apertus_differs"
    elif rule_type:
        q1_state = "rules_gave_the_type"
    elif not q1.get("given"):
        q1_state = "below_threshold"
    elif q1.get("class") == "none":
        q1_state = "class_none"
    else:
        q1_state = "not_used"
    out_q1 = {"class": q1.get("class"), "probability": _round(q1.get("probability")), "given": q1.get("given"),
              "state": q1_state, "used": bool(info.get("used")), "rule_type_found": rule_type,
              "differs": bool(heads.get("q1_differs")), "place": info.get("place"), "page": info.get("page"),
              "block": info.get("block"), "near": bool(near.get("q1")),
              "place_option_types": info.get("place_option_types")}
    top = (ho or {}).get("q2_top") or {}
    q2 = {}
    called = heads.get("q2") or {}
    for f in sorted(set(called) | {"sponsor"}):
        c = called.get(f)
        g = (c or {}).get("gave") or {}
        tp = top.get(f) or {}
        r = res["fields"].get(f) or {}
        searched = bool((r.get("cascade") or {}).get("searched"))
        if c is None:
            state = "not_called_rule_value_not_weak" if searched else "not_searched_in_this_kind"
        elif not g.get("found"):
            state = "no_value" if g.get("reason") != "no_cue" else "below_0_50"
        elif g.get("tier") is None:
            state = "below_band_hi" if g.get("band") == "lo" else "tier_not_entered"
        else:
            state = "used"
        q2[f] = {"called_because": (c or {}).get("called_because"), "top_block": tp.get("block"),
                 "top_page": tp.get("page"), "head_probability": _round(tp.get("probability")),
                 "top_two_gap": _round(tp.get("top_two_gap")), "band": g.get("band"), "tier": g.get("tier"),
                 "state": state, "used": state == "used", "near": bool((near.get("q2") or {}).get(f))}
    # chapter 4: the suggestions below the entry limit, facts only (no wording; the manifest key
    # apertus_suggestions of m12_writer holds the value and the wording)
    sugg = [{k: x.get(k) for k in SUGGESTION_FACT_KEYS} for x in (res.get("apertus") or {}).get("suggestions") or []]
    return {"q1": out_q1, "q2": q2, "values_from_apertus": list((res.get("apertus") or {}).get("values") or []),
            "near_margin": near.get("margin"), "suggestions": sugg}

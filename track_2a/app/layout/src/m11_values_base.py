"""Plan `crisp-dm/04-modeling/plan-ech-from-pdf.md`, task T0: the common interface of the value rules that read
eCH-0295 values from the PDF.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: EXCEPTION, NOT RELEASED. No human checked this file. This file changes no existing file and imports
no other project file (the function `guard_check` imports `m10_guard` only when it is called).

1 Inputs of a value rule (hard rule 5 of the wave)
  A rule gets one `Doc`. A `Doc` is made from the block file of the document (Docling blocks with page and
  character range) and, if it exists, from the rule file of the rule chain (`src/m10_rules.py`).
  A rule must not read an export record, a decisions file of B1-S or a state file.
  The block roles of the Apertus candidate are an optional extra tier: `load_doc(doc_id, apertus_roles=True)`.
  A rule that uses them must have its own tier name, and that tier is measured apart.

2 Loaders
  load_doc(doc_id)                 a development document of an OPEN parliament. The id must be in
                                   `daten/gj_values/folds.json` (each id of that file passed `m10_guard` for the
                                   split dev). A document of a closed parliament is refused: `ClosedParliament`.
                                   `allow_closed=True` is only for the one opening that the main agent orders.
  load_from_block_file(path, rule_file=None)
                                   a PDF with no stored project files (the package of the jury). No project path
                                   is used. With no rule file the S1 role and the rule roles are None.
  dev_ids(part="open", fold=None)  the ids of the open part (or of one fold) from folds.json.

3 Forms that the loaders read
  Block file (`src/m10_docs.py`, interface 2): {doc_id, parliament, split, language, blocks: [{block, page,
  docling_label, text, atoms, char_start, char_end}]}. The document text is the block texts with a text, joined
  by 2 line feeds. `text[char_start:char_end]` is the block text. A line is a part of the block text between 2
  line feeds. A line has the page of its block.
  Rule file (`src/m10_rules.py`): document.s1 {rule_role, rule_id, ...}, document.d1, document.s2, and for each
  block {block, option, mixed, tier, tier_detail}. `option` is the block role of the rules mode (floor mode):
  submitted, reasoning, response, recommendation, title or none. The floor mode (`src/m10_cascade.py`,
  `floor_decisions`) copies this option and adds a probability from the calibration file. Thus the rule file gives
  the block role of the rules mode, and this file reads no decisions file for it.
  Limit 1: the rule chain is the method nos4. It asks no title question. In the 1,486 open documents, 0 of
  86,959 blocks have the rule role title (measured 13.10.2026). Thus a title rule cannot use `rule_role`.
  Limit 2 (closed on 13.10.2026, round 4): `RULES_DIR` is the folder `daten/gj/rules_pdf`.
  The tool `src/m11_rules_pdf.py` made these rule files from the PDF alone. It gave the S1 rule empty export
  fields, as the package does for a dropped PDF. Thus the measured reader and the delivered reader are equal.
  The rule ids O1, O2, P2 and R1 have a condition on export fields (`src/m03_sub_s1_role.py`).
  With empty fields the ids P2 and R1 do not occur. The ids O1 and O2 occur only by a heading of the PDF.
  `Doc.s1_export_condition` is true only if the rule id is one of these 4 ids and the rule got an export record.
  The key `export_record.found` of the rule file says if the rule got one. A file with no such key counts as yes.
  The stored rule files of `daten/gj/rules` got 3 export fields of the document. No loader of this file reads them.

4 Output of a rule
  ValueCandidate  field, value (the wording: exactly `doc.text[char_start:char_end]`), normalised (the value in the
                  form of the field), tier (name of the rule tier), page, block, char_start, char_end, evidence
                  (at most 120 characters of the text around the span), others (other candidates, best first).
                  Make it with `doc.candidate(...)`: this function fills page, block, value and evidence.
  NotFound        field, reason (a code of REASONS), detail. A rule that cannot find a value returns NotFound.
                  It does not guess. A wrong value with a high probability is the worst result.
  A rule gives no probability. The calibration gives one probability to each pair of field and tier (plan 4.4).

5 Registry
  @register("title")
  def read_title(doc: Doc) -> ValueCandidate | NotFound: ...
  The function name must be `read_<field>`. The field must be in FIELDS. One reader for each field.
  `load_rule_modules()` imports `m11_values.py` and each `m11_values_<name>.py` that is beside this file.
  `read_field(doc, field)` and `read_all(doc)` call the readers and check each result with `check_result`.

6 Shared helpers
  norm_text, fold, fold_map (folded text with a map back to the positions of the input), find_dates (numeric
  dates, ISO dates and dates with a month name in German, French and Italian), tokens, content_tokens,
  token_share, Doc.first_lines, Doc.last_lines, Doc.dates, Doc.first_response_block,
  Doc.blocks_before_response, Doc.blocks_from_response, Doc.blocks_with_role, Doc.locate.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_base.py selftest
  uv run --offline --frozen --no-sync python src/m11_values_base.py show DOC_ID [--lines 15]
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import re
import sys
import unicodedata
from bisect import bisect_right
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Callable

VERSION = "m11-values-base-1"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
FOLDS_FILE = ROOT / "daten/gj_values/folds.json"
DOCS_DIR = ROOT / "daten/gj/docs"
RULES_DIR = ROOT / "daten/gj/rules_pdf"       # rule files from the PDF alone (src/m11_rules_pdf.py)
APERTUS_DECISIONS_DIR = ROOT / "daten/gj/fullrun_b1s_dev/decisions"
SEP = "\n\n"                                  # block separator of the document text (interface 2)
EVIDENCE_MAX = 120
ROLES = ("submitted", "reasoning", "response", "recommendation", "title", "none")     # block roles (6 options)
RESPONSE_ROLES = ("response", "recommendation")
SPONSOR_ROLES = ("submitted", "reasoning")
S1_ROLES = ("proposal", "response", "combined", "committee", "minutes", "other")
S1_IDS_WITH_EXPORT_CONDITION = ("O1", "O2", "P2", "R1")
ROLE_TIERS = ("rules", "apertus")

# field -> (class and slot of eCH-0295, form of the key `normalised`). Addendum G wins where it is more exact.
FIELDS = {
    "affair_type": ("Affair.affair_type", "a value of the list of the term rule typ_ech"),
    "title": ("Affair.title", "the title text after norm_text (one line, no line-end hyphen)"),
    "affair_number": ("Affair.affair_number", "the number as printed, after norm_text"),
    "submission_date": ("Submission.submission_date", "ISO date YYYY-MM-DD"),
    "response_date": ("ResponseStep.date_end_actual", "ISO date YYYY-MM-DD"),
    "responder": ("ResponseStep.responder.name", "the body word as printed, after norm_text"),
    "sponsor": ("Submission.sponsorship (role sponsor)", "the name of the first author as printed, after norm_text"),
}
REASONS = {
    "no_text": "the document has no text",
    "no_pattern": "no text of the search area has the form of the value",
    "no_cue": "the form exists, but no cue word or position rule selects a candidate",
    "ambiguous": "two or more candidates stay and no rule selects one",
    "no_response_block": "the value is read from response blocks, and the document has none",
    "not_in_document_type": "this document type does not hold the value",
    "no_rule_file": "the rule needs the rule file, and the document has none",
    "no_reader": "no rule is registered for the field",
    "reader_error": "the rule stopped with an error (only with strict=False)",
}
TIER_RX = re.compile(r"[a-z][a-z0-9_]{1,39}\Z")


class ClosedParliament(Exception):
    """The document is in a closed parliament of daten/gj_values/folds.json."""


class NotADevDocument(Exception):
    """The id is not a development document of daten/gj_values/folds.json."""


class BadResult(Exception):
    """A rule returned a result that does not agree with the interface."""


# ------------------------------------------------------------------ text helpers

_REPLACE = {"\u2019": "'", "\u2018": "'", "\u02bc": "'", "\u00b4": "'", "`": "'", "\u00ab": '"', "\u00bb": '"',
            "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2039": "'", "\u203a": "'", "\u2013": "-", "\u2014": "-",
            "\u2010": "-", "\u2011": "-", "\u2212": "-", "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2007": " "}
_DROP = {"\u00ad", "\u200b", "\u200c", "\u200d", "\ufeff"}


def norm_text(s: str, dehyphen: bool = True) -> str:
    """NFKC, no soft hyphen, typographic quotes and dashes as ASCII, a hyphen at a line end joined (if `dehyphen`:
    a lower-case letter, a hyphen, a line feed, a lower-case letter), each run of white space as one space,
    no space at the ends. Case and accents stay."""
    s = unicodedata.normalize("NFKC", s or "")
    s = "".join(_REPLACE.get(c, c) for c in s if c not in _DROP)
    if dehyphen:
        s = re.sub(r"(?<=[^\W\d_])-[ \t]*\n[ \t]*(?=[a-zà-ÿ])", "", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass(frozen=True)
class Folded:
    """A folded text with a map back to the input. text[i] comes from input[index[i]]."""
    text: str
    index: tuple[int, ...]
    base: int = 0            # is added to each position that span() returns
    source_len: int = 0

    def span(self, start: int, end: int) -> tuple[int, int]:
        """The span of the input (plus base) that gave text[start:end]. An empty span stays empty."""
        if end <= start:
            p = self.index[start] if start < len(self.index) else self.source_len
            return self.base + p, self.base + p
        return self.base + self.index[start], self.base + self.index[end - 1] + 1

    def match_span(self, m: re.Match, group: int | str = 0) -> tuple[int, int]:
        return self.span(m.start(group), m.end(group))


def fold_map(s: str, base: int = 0, keep_newlines: bool = False, dehyphen: bool = False) -> Folded:
    """Fold a text for a search and keep the positions: lower case, no accents, sharp s as ss, typographic quotes
    and dashes as ASCII, no soft hyphen, each run of white space as one space (with `keep_newlines`: a run that
    holds a line feed becomes one line feed). With `dehyphen` a hyphen at a line end between 2 lower-case letters
    is removed together with the line feed. Use `Folded.span` to get the positions in the input again."""
    out: list[str] = []
    idx: list[int] = []
    n = len(s)
    i = 0
    while i < n:
        c = s[i]
        if c in _DROP:
            i += 1
            continue
        c = _REPLACE.get(c, c)
        if dehyphen and c == "-" and out and out[-1].isalpha() and out[-1].islower():
            j = i + 1
            while j < n and s[j] in " \t":
                j += 1
            if j < n and s[j] == "\n":
                k = j + 1
                while k < n and s[k] in " \t":
                    k += 1
                if k < n and s[k].isalpha() and s[k].islower():
                    i = k
                    continue
        if c.isspace():
            nl = keep_newlines and c in "\n\r"
            if out and out[-1] in " \n":
                if nl and out[-1] == " ":
                    out[-1] = "\n"
            else:
                out.append("\n" if nl else " ")
                idx.append(i)
            i += 1
            continue
        if c == "ß":
            f = "ss"
        else:
            f = "".join(x for x in unicodedata.normalize("NFKD", c) if unicodedata.category(x) != "Mn").lower()
        for x in f:
            if x.isspace():
                if out and out[-1] in " \n":
                    continue
                x = " "
            out.append(x)
            idx.append(i)
        i += 1
    return Folded("".join(out), tuple(idx), base, n)


def fold(s: str) -> str:
    """The folded text of fold_map with no space at the ends (for a comparison of two values)."""
    return fold_map(s or "", dehyphen=True).text.strip()


@dataclass(frozen=True)
class Token:
    text: str                # folded form: lower case, no accents
    start: int
    end: int


_TOKEN_RX = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "der die das des dem den und in im zu zur zum von vom fuer fur auf an am ein eine einer eines mit bei aus als ist "
    "de la le les du des et en au aux un une pour sur dans par a l d "
    "di del della dei delle il lo i gli e per con su nel nella al alla da un una".split())


def tokens(s: str, base: int = 0) -> list[Token]:
    """Words and numbers of a text in the folded form, each with its span in the input (plus base)."""
    f = fold_map(s or "", base)
    return [Token(m.group(0), *f.match_span(m)) for m in _TOKEN_RX.finditer(f.text)]


def content_tokens(s: str) -> list[str]:
    """The folded tokens with no stop word of German, French or Italian."""
    return [t.text for t in tokens(s) if t.text not in STOPWORDS]


def token_share(a: str, b: str) -> float:
    """The share of the content tokens of `a` that are also content tokens of `b` (0.0 if `a` has none)."""
    ta, tb = content_tokens(a), set(content_tokens(b))
    return sum(1 for t in ta if t in tb) / len(ta) if ta else 0.0


# ------------------------------------------------------------------ dates

_MONTH_NAMES = [
    "januar jan janner janvier janv gennaio genn gen",
    "februar feb febr fevrier fevr fev febbraio febb",
    "marz maerz mrz mars marzo mar",
    "april apr avril avr aprile",
    "mai maggio mag",
    "juni jun juin giugno giu",
    "juli jul juillet juil luglio lug",
    "august aug aout agosto ago",
    "september sept sep septembre settembre sett set",
    "oktober okt octobre oct ottobre ott",
    "november nov novembre",
    "dezember dez decembre dec dicembre dic",
]
MONTHS = {name: i for i, names in enumerate(_MONTH_NAMES, 1) for name in names.split()}
_MON_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
_RX_NUM = re.compile(r"(?<![\d.,/-])(\d{1,2}) ?([./-]) ?(\d{1,2}) ?\2 ?(\d{4}|\d{2})(?![\d])(?!\.\d)")
_RX_ISO = re.compile(r"(?<![\d.-])(\d{4})-(\d{2})-(\d{2})(?![\d-])")
_RX_MON = re.compile(r"(?<![\d.,/])(\d{1,2})(?:\. ?|er |° ?|o | )(" + _MON_ALT + r")\b\.? ?(\d{4})(?!\d)")
YEAR_MIN, YEAR_MAX = 1848, 2099


@dataclass(frozen=True)
class DateHit:
    iso: str                 # YYYY-MM-DD
    start: int               # span in the text that was given to find_dates (plus base)
    end: int
    wording: str             # the text of the span
    form: str                # numeric | iso | month_name
    page: int | None = None  # filled by Doc.dates
    block: str | None = None


def _date(y: int, m: int, d: int) -> str | None:
    if not YEAR_MIN <= y <= YEAR_MAX:
        return None
    try:
        return dt.date(y, m, d).isoformat()
    except ValueError:
        return None


def find_dates(text: str, base: int = 0) -> list[DateHit]:
    """All dates of a text in reading order, each with its span: numeric dates in the order day, month, year
    (separators . / -; a year of 2 digits only with . or /: 00 to 39 is 2000 to 2039, else 1900), ISO dates and
    dates with a month name or a month short form in German, French or Italian ("9. September 2013", "1er mars
    2021", "20 dicembre 2019"). A date over a line end is found. A day or month that is not possible gives no
    hit. A year outside 1848 to 2099 gives no hit. If two hits overlap, the hit that starts first stays."""
    f = fold_map(text or "", base)
    hits: list[tuple[int, int, str, str]] = []
    for m in _RX_NUM.finditer(f.text):
        d, sep, mo, y = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        if len(y) == 2:
            if sep == "-":
                continue
            yy = 2000 + int(y) if int(y) < 40 else 1900 + int(y)
        else:
            yy = int(y)
        iso = _date(yy, mo, d)
        if iso:
            hits.append((m.start(), m.end(), iso, "numeric"))
    for m in _RX_ISO.finditer(f.text):
        iso = _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if iso:
            hits.append((m.start(), m.end(), iso, "iso"))
    for m in _RX_MON.finditer(f.text):
        iso = _date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
        if iso:
            hits.append((m.start(), m.end(), iso, "month_name"))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, last_end = [], -1
    for s, e, iso, form in hits:
        if s < last_end:
            continue
        last_end = e
        a, b = f.span(s, e)
        out.append(DateHit(iso, a, b, text[a - base:b - base], form))
    return out


# ------------------------------------------------------------------ language fallback (only for a block file with no language key)

_LANG_WORDS = {
    "de": frozenset("der die das und nicht ist mit von den des dem ein eine werden wird für auf im zu sich dass".split()),
    "fr": frozenset("le la les des et est une dans pour que qui du au aux pas sur par ce cette sont".split()),
    "it": frozenset("il lo la gli le di che è per una del della dei delle nel con non sono alla si".split()),
}


def guess_language(text: str) -> str | None:
    """de, fr, it or None. A fallback of this file for a block file with no key `language`: the word set with the
    most hits in the first 20,000 characters, with 3 hits or more and more than 1.5 times the hits of the
    second set. It is not the function m05_cls_data.language (that function also gives rm and en)."""
    words = re.findall(r"[^\W\d_]+", (text or "")[:20000].lower())
    n = {k: sum(1 for w in words if w in s) for k, s in _LANG_WORDS.items()}
    first, second = sorted(n.values(), reverse=True)[:2]
    return max(n, key=n.get) if first >= 3 and first > 1.5 * second else None


# ------------------------------------------------------------------ document

@dataclass(frozen=True)
class Line:
    number: int              # 0, 1, ... over the lines of the document that have text
    block: str               # block id "B<n>"
    block_index: int         # index of the block in Doc.blocks
    index_in_block: int      # 0, 1, ... over all lines of the block (also the empty lines)
    page: int
    text: str                # the line as printed (no line feed)
    char_start: int          # span in Doc.text
    char_end: int


@dataclass(frozen=True)
class Block:
    index: int               # 0, 1, ... in reading order
    block: str               # block id "B<n>"
    label: str               # Docling label (text, section_header, page_header, list_item, picture, ...)
    page: int
    text: str
    char_start: int          # span in Doc.text
    char_end: int
    lines: tuple[Line, ...]  # the lines with text
    rule_role: str | None    # block role of the rules mode (None: no rule file)
    rule_tier: str | None    # tier of the rule chain (s2_switch:answer_label, fixed:R1, ...)
    rule_mixed: bool | None
    rule_detail: dict | None  # key tier_detail of the rule file
    apertus_role: str | None = None    # only with apertus_roles=True (optional extra tier)
    apertus_source: str | None = None

    def role(self, tier: str = "rules") -> str | None:
        if tier not in ROLE_TIERS:
            raise ValueError(f"tier must be one of {ROLE_TIERS}")
        return self.rule_role if tier == "rules" else self.apertus_role


@dataclass(frozen=True)
class ValueCandidate:
    field: str
    value: str               # the wording: exactly Doc.text[char_start:char_end]
    normalised: str          # the value in the form of the field (FIELDS)
    tier: str                # name of the rule tier (lower case, digits, underscore)
    page: int
    block: str
    char_start: int
    char_end: int
    evidence: str            # at most 120 characters
    others: tuple["ValueCandidate", ...] = ()
    detail: dict | None = None     # free notes of the rule (cue word, pattern name); not a value

    found = True

    def to_json(self, with_others: bool = True) -> dict:
        d = {"field": self.field, "found": True, "value": self.value, "normalised": self.normalised,
             "tier": self.tier, "page": self.page, "block": self.block, "char_start": self.char_start,
             "char_end": self.char_end, "evidence": self.evidence}
        if self.detail:
            d["detail"] = self.detail
        if with_others:
            d["others"] = [o.to_json(False) for o in self.others]
        return d


@dataclass(frozen=True)
class NotFound:
    field: str
    reason: str              # a code of REASONS
    detail: str = ""
    others: tuple[ValueCandidate, ...] = ()      # candidates that the rule refused (for the reason ambiguous)

    found = False

    def to_json(self) -> dict:
        return {"field": self.field, "found": False, "result": "not found in the PDF", "reason": self.reason,
                "detail": self.detail, "others": [o.to_json(False) for o in self.others]}


@dataclass
class Doc:
    doc_id: str | None
    parliament: str | None           # parliament key of m10_guard (None for a PDF with no stored project files)
    language: str | None             # de, fr, it, rm, en or None
    blocks: tuple[Block, ...]
    text: str                        # the document text (block texts joined by SEP)
    lines: tuple[Line, ...]          # all lines with text in reading order
    s1_role: str | None              # S1 rule role: proposal, response, combined, committee, minutes, other
    s1_rule_id: str | None           # rule id of the S1 rule (A1, A2, P1, ...)
    s1_export_condition: bool | None  # True: rule id O1, O2, P2 or R1, and the rule got an export record
    rules_document: dict | None      # key `document` of the rule file (s1, s2, d1, claims)
    has_rule_file: bool
    has_apertus_roles: bool
    origin: str                      # "project" (load_doc) or "block_file" (load_from_block_file)
    inputs: dict = dc_field(default_factory=dict)
    _starts: list = dc_field(default_factory=list, repr=False)
    _line_starts: list = dc_field(default_factory=list, repr=False)

    # ---- positions
    def locate(self, pos: int) -> Block:
        """The block that holds the character position (for a position in a separator: the block before it)."""
        if not self.blocks:
            raise ValueError("the document has no block")
        with_text = self._starts
        i = bisect_right([s for s, _ in with_text], pos) - 1
        return self.blocks[with_text[max(i, 0)][1]]

    def line_at(self, pos: int) -> Line | None:
        """The line that holds the character position, or the last line before it."""
        i = bisect_right(self._line_starts, pos) - 1
        return self.lines[i] if i >= 0 else None

    def block_by_id(self, block: str) -> Block:
        b = self.blocks[int(block[1:]) - 1] if block[1:].isdigit() and 0 < int(block[1:]) <= len(self.blocks) else None
        if b is None or b.block != block:
            b = next((x for x in self.blocks if x.block == block), None)
        if b is None:
            raise KeyError(block)
        return b

    @property
    def pages(self) -> int:
        return max((b.page for b in self.blocks), default=0)

    # ---- lines
    def first_lines(self, n: int = 15, skip_labels: tuple[str, ...] = ()) -> list[Line]:
        """The first n lines with text in reading order (the same line count as probe 3). `skip_labels`: Docling
        labels whose lines do not count (for example page_header, page_footer)."""
        return [ln for ln in self.lines if self.blocks[ln.block_index].label not in skip_labels][:n]

    def last_lines(self, n: int = 15, skip_labels: tuple[str, ...] = ()) -> list[Line]:
        """The last n lines with text, in reading order."""
        got = [ln for ln in self.lines if self.blocks[ln.block_index].label not in skip_labels]
        return got[-n:] if n else []

    def page_lines(self, page: int) -> list[Line]:
        return [ln for ln in self.lines if ln.page == page]

    @staticmethod
    def lines_span(lines: list[Line]) -> tuple[int, int] | None:
        """(start, end) in Doc.text from the first to the last of the lines; None for no line."""
        return (lines[0].char_start, lines[-1].char_end) if lines else None

    # ---- block roles
    def blocks_with_role(self, *roles: str, tier: str = "rules") -> list[Block]:
        bad = set(roles) - set(ROLES)
        if bad:
            raise ValueError(f"unknown block roles: {sorted(bad)}")
        return [b for b in self.blocks if b.role(tier) in roles]

    def first_response_block(self, tier: str = "rules") -> Block | None:
        """The first block with the role response or recommendation; None if no such block (or no roles)."""
        return next((b for b in self.blocks if b.role(tier) in RESPONSE_ROLES), None)

    def blocks_before_response(self, tier: str = "rules") -> list[Block]:
        """The blocks before the first response block. All blocks if the document has no response block."""
        f = self.first_response_block(tier)
        return list(self.blocks) if f is None else list(self.blocks[:f.index])

    def blocks_from_response(self, tier: str = "rules") -> list[Block]:
        """The first response block and all blocks after it. Empty if the document has no response block."""
        f = self.first_response_block(tier)
        return [] if f is None else list(self.blocks[f.index:])

    # ---- dates
    def dates(self, start: int = 0, end: int | None = None) -> list[DateHit]:
        """The dates of Doc.text[start:end] with page and block. A date over 2 blocks is not found."""
        end = len(self.text) if end is None else end
        out = []
        for b in self.blocks:
            if not b.text or b.char_end <= start or b.char_start >= end:
                continue
            a, z = max(b.char_start, start), min(b.char_end, end)
            for h in find_dates(self.text[a:z], a):
                out.append(DateHit(h.iso, h.start, h.end, h.wording, h.form, b.page, b.block))
        return out

    def dates_in(self, blocks_or_lines) -> list[DateHit]:
        """The dates in a list of blocks or lines (each item has char_start and char_end)."""
        out = []
        for x in blocks_or_lines:
            out += self.dates(x.char_start, x.char_end)
        return out

    # ---- results
    def evidence(self, start: int, end: int) -> str:
        """At most 120 characters: the line or lines of the span, white space as one space. If that is too long,
        the value with text before and after it, cut to 120 characters."""
        a, z = self.line_at(start), self.line_at(max(end - 1, start))
        s = a.char_start if a and a.char_start <= start else start
        e = z.char_end if z and z.char_end >= end else end
        full = re.sub(r"\s+", " ", self.text[s:e]).strip()
        if len(full) <= EVIDENCE_MAX:
            return full
        val = re.sub(r"\s+", " ", self.text[start:end]).strip()
        if len(val) >= EVIDENCE_MAX:
            return val[:EVIDENCE_MAX]
        room = EVIDENCE_MAX - len(val)
        before = re.sub(r"\s+", " ", self.text[s:start])
        after = re.sub(r"\s+", " ", self.text[end:e])
        lb = min(len(before), room // 2)
        la = min(len(after), room - lb)
        return ((before[len(before) - lb:] if lb else "") + val + after[:la]).strip()[:EVIDENCE_MAX]

    def candidate(self, field: str, start: int, end: int, normalised: str, tier: str,
                  others: tuple[ValueCandidate, ...] | list = (), detail: dict | None = None) -> ValueCandidate:
        """A candidate for Doc.text[start:end]. Page and block are those of the first character of the span."""
        if not 0 <= start < end <= len(self.text):
            raise BadResult(f"{field}: span {start}:{end} is empty or outside the document text")
        b = self.locate(start)
        c = ValueCandidate(field, self.text[start:end], normalised, tier, b.page, b.block, start, end,
                           self.evidence(start, end), tuple(others), detail)
        check_result(self, field, c)
        return c

    def not_found(self, field: str, reason: str, detail: str = "", others=()) -> NotFound:
        r = NotFound(field, reason, detail, tuple(others))
        check_result(self, field, r)
        return r


def _build(doc: dict, rules: dict | None, apertus: dict | None, origin: str, inputs: dict) -> Doc:
    raw = doc["blocks"]
    text = SEP.join(b["text"] for b in raw if b["text"])
    rule_blocks = None
    if rules is not None:
        rule_blocks = rules["blocks"]
        if [b["block"] for b in rule_blocks] != [b["block"] for b in raw]:
            raise ValueError("the blocks of the rule file are not the blocks of the block file in reading order")
    ap_blocks = None
    if apertus is not None:
        ap_blocks = apertus["blocks"]
        if [b["block"] for b in ap_blocks] != [b["block"] for b in raw]:
            raise ValueError("the blocks of the decisions file are not the blocks of the block file")
    blocks, lines, starts = [], [], []
    pos, first = 0, True
    for i, b in enumerate(raw):
        t = b["text"] or ""
        if t:
            if not first:
                pos += len(SEP)
            first = False
            s, e = pos, pos + len(t)
            pos = e
        else:
            s = e = pos
        if "char_start" in b and (b["char_start"], b["char_end"]) != (s, e):
            raise ValueError(f"{b['block']}: the stored span differs from the span in the document text")
        if text[s:e] != t:
            raise ValueError(f"{b['block']}: the span does not give the block text")
        own, off = [], s
        for k, part in enumerate(t.split("\n")):
            if part.strip():
                ln = Line(len(lines) + len(own), b["block"], i, k, int(b["page"]), part, off, off + len(part))
                own.append(ln)
            off += len(part) + 1
        lines += own
        if t:
            starts.append((s, i))
        r = rule_blocks[i] if rule_blocks else None
        a = ap_blocks[i] if ap_blocks else None
        if r is not None and r["option"] not in ROLES:
            raise ValueError(f"{b['block']}: unknown rule option {r['option']}")
        blocks.append(Block(i, b["block"], b.get("docling_label") or "", int(b["page"]), t, s, e, tuple(own),
                            r["option"] if r else None, r.get("tier") if r else None,
                            r.get("mixed") if r else None, r.get("tier_detail") if r else None,
                            a.get("option") if a else None, a.get("source") if a else None))
    s1 = (rules or {}).get("document", {}).get("s1") or {}
    role, rid = s1.get("rule_role"), s1.get("rule_id")
    if role is not None and role not in S1_ROLES:
        raise ValueError(f"unknown S1 rule role {role}")
    lang = doc["language"] if "language" in doc else guess_language(text)
    return Doc(doc_id=str(doc["doc_id"]) if doc.get("doc_id") is not None else None,
               parliament=doc.get("parliament"), language=lang, blocks=tuple(blocks), text=text,
               lines=tuple(lines), s1_role=role, s1_rule_id=rid,
               s1_export_condition=(rid in S1_IDS_WITH_EXPORT_CONDITION
                                    and ((rules or {}).get("export_record") or {}).get("found") is not False)
               if rid else None,
               rules_document=(rules or {}).get("document"), has_rule_file=rules is not None,
               has_apertus_roles=apertus is not None, origin=origin, inputs=inputs, _starts=starts,
               _line_starts=[ln.char_start for ln in lines])


def _read_json(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


_FOLDS: dict | None = None


def folds() -> dict:
    """The content of daten/gj_values/folds.json (read one time)."""
    global _FOLDS
    if _FOLDS is None:
        if not FOLDS_FILE.is_file():
            raise FileNotFoundError("daten/gj_values/folds.json does not exist: run src/m11_value_folds.py build")
        _FOLDS = _read_json(FOLDS_FILE)
    return _FOLDS


def dev_ids(part: str = "open", fold: int | None = None) -> list[str]:
    """The development ids of one part in number order. part: "open" or "closed" ("closed" gives ids only; a
    loader call for such an id is refused). fold: 0 to 4 for the open part."""
    if part not in ("open", "closed"):
        raise ValueError("part must be open or closed")
    docs = folds()["documents"]
    return sorted((d for d, v in docs.items() if v["part"] == part and (fold is None or v["fold"] == fold)), key=int)


def fold_of(doc_id: str) -> int | None:
    return folds()["documents"][str(doc_id)]["fold"]


def load_doc(doc_id: str | int, apertus_roles: bool = False, allow_closed: bool = False) -> Doc:
    """A development document of an open parliament: the block file daten/gj/docs/<doc>.json and the rule file
    daten/gj/rules_pdf/<doc>.json. No export record, no decisions file and no state file is read.
    apertus_roles=True (optional extra tier, measured apart) also reads the block options of
    daten/gj/fullrun_b1s_dev/decisions/<doc>.json. allow_closed=True is only for the one opening that the main
    agent orders. The check of the part comes before each file of the document is opened."""
    d = str(doc_id)
    entry = folds()["documents"].get(d)
    if entry is None:
        raise NotADevDocument(f"{d}: not a development document of daten/gj_values/folds.json")
    if entry["part"] != "open" and not allow_closed:
        raise ClosedParliament(f"{d}: the document is in a closed parliament; the main agent did not order the opening")
    inputs = {"block_file": f"daten/gj/docs/{d}.json", "rule_file": f"{RULES_DIR.relative_to(ROOT).as_posix()}/{d}.json"}
    doc = _read_json(DOCS_DIR / f"{d}.json")
    if doc.get("split") != "dev" or str(doc.get("doc_id")) != d or doc.get("parliament") != entry["parliament"]:
        raise NotADevDocument(f"{d}: the block file does not agree with folds.json (split, id or parliament)")
    rules = _read_json(RULES_DIR / f"{d}.json")
    if str(rules.get("doc_id")) != d:
        raise ValueError(f"{d}: the rule file has another doc id")
    ap = None
    if apertus_roles:
        ap = _read_json(APERTUS_DECISIONS_DIR / f"{d}.json")
        ap = {"blocks": [{"block": b["block"], "option": b["option"], "source": b.get("source")} for b in ap["blocks"]]}
        inputs["apertus_roles"] = f"daten/gj/fullrun_b1s_dev/decisions/{d}.json (block options only)"
    return _build(doc, rules, ap, "project", inputs)


def load_from_block_file(path: str | Path, rule_file: str | Path | None = None) -> Doc:
    """A PDF with no stored project files: the block file (form of interface 2) and, if given, its rule file (form
    of src/m10_rules.py). No project path is used. With no rule file: s1_role, s1_rule_id and each rule_role are
    None. If the block file has no key `language`, guess_language gives it."""
    doc = _read_json(Path(path))
    rules = _read_json(Path(rule_file)) if rule_file is not None else None
    return _build(doc, rules, None, "block_file", {"block_file": str(path), "rule_file": str(rule_file) if rule_file else None})


def guard_check(ids) -> dict:
    """An extra test of ids with src/m10_guard.py (split dev only). It reads the guard tables, no document."""
    sys.path.insert(0, str(SCRIPT.parent))
    import m10_guard as guard  # noqa: PLC0415

    g = guard.assert_allowed([str(i) for i in ids], ("dev",))
    return {"items": g["items"], "by_split": g["by_split"], "refused": g["refused"]}


# ------------------------------------------------------------------ registry

Reader = Callable[[Doc], "ValueCandidate | NotFound"]
REGISTRY: dict[str, Reader] = {}


def register(field: str, registry: dict | None = None):
    """Decorator: register `read_<field>(doc)` as the one reader of a field of FIELDS."""
    reg = REGISTRY if registry is None else registry

    def deco(fn: Reader) -> Reader:
        if field not in FIELDS:
            raise ValueError(f"unknown field {field}; fields: {sorted(FIELDS)}")
        if fn.__name__ != f"read_{field}":
            raise ValueError(f"the reader of {field} must have the name read_{field}, not {fn.__name__}")
        if field in reg and (reg[field].__module__, reg[field].__qualname__) != (fn.__module__, fn.__qualname__):
            raise ValueError(f"{field}: a reader is registered already ({reg[field].__module__})")
        reg[field] = fn
        return fn
    return deco


def check_result(doc: Doc, field: str, res) -> None:
    """Stop (BadResult) if a result does not agree with the interface. For a candidate: the span gives the value
    again, page and block are those of the span start, the evidence has at most 120 characters."""
    if isinstance(res, NotFound):
        if res.field != field:
            raise BadResult(f"{field}: NotFound with the field {res.field}")
        if res.reason not in REASONS:
            raise BadResult(f"{field}: unknown reason code {res.reason}; codes: {sorted(REASONS)}")
        for o in res.others:
            check_result(doc, field, o)
        return
    if not isinstance(res, ValueCandidate):
        raise BadResult(f"{field}: the reader returned {type(res).__name__}, not ValueCandidate or NotFound")
    if res.field != field:
        raise BadResult(f"{field}: candidate with the field {res.field}")
    if not 0 <= res.char_start < res.char_end <= len(doc.text) or doc.text[res.char_start:res.char_end] != res.value:
        raise BadResult(f"{field}: the span {res.char_start}:{res.char_end} does not give the value again")
    b = doc.locate(res.char_start)
    if (res.block, res.page) != (b.block, b.page):
        raise BadResult(f"{field}: page or block is not that of the span start")
    if not isinstance(res.normalised, str) or not res.normalised.strip():
        raise BadResult(f"{field}: the normalised value is empty")
    if not TIER_RX.match(res.tier or ""):
        raise BadResult(f"{field}: tier name {res.tier!r} (lower-case letters, digits and underscore, 2 to 40)")
    if len(res.evidence) > EVIDENCE_MAX:
        raise BadResult(f"{field}: evidence longer than {EVIDENCE_MAX} characters")
    for o in res.others:
        if o.others:
            raise BadResult(f"{field}: a candidate of the list others has its own list others")
        check_result(doc, field, o)


def read_field(doc: Doc, field: str, strict: bool = True, registry: dict | None = None):
    """The result of the reader of one field. No reader: NotFound with the reason no_reader. strict=False: an
    error of the reader gives NotFound with the reason reader_error (for the package; a measurement uses strict)."""
    reg = REGISTRY if registry is None else registry
    if field not in FIELDS:
        raise ValueError(f"unknown field {field}")
    fn = reg.get(field)
    if fn is None:
        return NotFound(field, "no_reader")
    if not doc.text.strip():
        return NotFound(field, "no_text")
    try:
        res = fn(doc)
        check_result(doc, field, res)
    except Exception as e:  # noqa: BLE001
        if strict:
            raise
        return NotFound(field, "reader_error", f"{type(e).__name__}: {e}"[:200])
    return res


def read_all(doc: Doc, strict: bool = True, registry: dict | None = None) -> dict:
    """{field: ValueCandidate | NotFound} for each field of FIELDS."""
    return {f: read_field(doc, f, strict, registry) for f in FIELDS}


def load_rule_modules() -> list[str]:
    """Import m11_values.py and each m11_values_<name>.py beside this file (not this file, not a test file).
    Each module registers its readers at import. Returns the module names."""
    here = SCRIPT.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    # a rule module imports this file by its name; a run as a script has the name __main__
    sys.modules.setdefault("m11_values_base", sys.modules[__name__])
    names = sorted(p.stem for p in here.glob("m11_values*.py")
                   if p.stem not in ("m11_values_base",) and not p.stem.endswith("_test"))
    for n in names:
        importlib.import_module(n)
    return names


# ------------------------------------------------------------------ self-test and show

SELFTEST_DOCS = ("22700", "45623", "684152")    # open parliaments BE, TI and CHE (chosen after folds.json existed)


def selftest() -> dict:
    """Unit cases with synthetic text, and hand-checked facts of 3 open development documents. No export value."""
    res: dict[str, object] = {}
    bad: list[str] = []

    def want(name: str, got, expected) -> None:
        if got != expected:
            bad.append(f"{name}: got {got!r}, expected {expected!r}")

    # ---- text
    src = "Der Regierungs-\nrat  beschließt:\u00a0«Straße» –  ﬁx"
    want("norm_text", norm_text(src), 'Der Regierungsrat beschließt: "Straße" - fix')
    f = fold_map(src, dehyphen=True)
    want("fold_map.text", f.text, 'der regierungsrat beschliesst: "strasse" - fix')
    m = re.search(r"regierungsrat", f.text)
    want("fold_map.span", src[slice(*f.match_span(m))], "Regierungs-\nrat")
    m = re.search(r"strasse", f.text)
    want("fold_map.span_ss", src[slice(*f.match_span(m))], "Straße")
    want("fold_map.base", fold_map("Ä b", base=100).span(0, 1), (100, 101))
    want("fold_map.newlines", fold_map("a \n\n b\nc", keep_newlines=True).text, "a\nb\nc")
    want("fold", fold("  Conseil d’État "), "conseil d'etat")
    want("tokens", [(t.text, t.start, t.end) for t in tokens("L’Été 2020")], [("l", 0, 1), ("ete", 2, 5), ("2020", 6, 10)])
    want("content_tokens", content_tokens("Motion über die Zukunft der Bahn"), ["motion", "uber", "zukunft", "bahn"])
    want("token_share", token_share("Zukunft der Bahn", "Die Bahn hat Zukunft"), 1.0)

    # ---- dates
    cases = [("Bern, 9. September 2013", ["2013-09-09"]), ("vom 03.12.2019 und 4.1.20", ["2019-12-03", "2020-01-04"]),
             ("le 1er mars 2021", ["2021-03-01"]), ("Bellinzona, 20 dicembre 2019 / 212.19", ["2019-12-20"]),
             ("eingereicht am 12. März\n2018", ["2018-03-12"]), ("2021-06-30", ["2021-06-30"]),
             ("Geschäft 2013.0071", []), ("Art. 31.2.2020", []), ("le 14 février 2017 et l'8 agosto 2016",
                                                                 ["2017-02-14", "2016-08-08"]),
             ("15/06/2015", ["2015-06-15"]), ("Nr. 12.345.67", []), ("22.159", []), ("7. Mai 22", [])]
    for t, exp in cases:
        want(f"find_dates({t!r})", [h.iso for h in find_dates(t)], exp)
    h = find_dates("x 9. September 2013 y", base=50)[0]
    want("find_dates.span", (h.start, h.end, h.wording, h.form), (52, 69, "9. September 2013", "month_name"))

    # ---- registry (a private registry; the registry of the module stays empty)
    reg: dict = {}
    try:
        register("no_such_field", reg)(lambda doc: None)
        bad.append("registry: an unknown field was accepted")
    except ValueError:
        pass

    def read_title(doc):       # a test reader, not a rule: it returns the first line as a candidate
        ln = doc.lines[0]
        return doc.candidate("title", ln.char_start, ln.char_end, norm_text(ln.text), "test_first_line")

    register("title", reg)(read_title)
    want("registry.no_reader", read_field(_build({"doc_id": None, "blocks": [
        {"block": "B1", "page": 1, "docling_label": "text", "text": "a"}]}, None, None, "block_file", {}),
        "sponsor", registry=reg).reason, "no_reader")

    # ---- closed parliament: refused before a file of the document is opened
    closed = dev_ids("closed")
    try:
        load_doc(closed[0])
        bad.append("load_doc opened a document of a closed parliament")
    except ClosedParliament:
        pass
    try:
        load_doc("0")
        bad.append("load_doc opened an unknown id")
    except NotADevDocument:
        pass
    res["folds"] = {"open": len(dev_ids("open")), "closed": len(closed),
                    "by_fold": [len(dev_ids("open", i)) for i in range(5)]}
    want("folds.sum", res["folds"]["open"] + res["folds"]["closed"], 1793)
    want("folds.fold_sum", sum(res["folds"]["by_fold"]), res["folds"]["open"])
    res["guard"] = guard_check(SELFTEST_DOCS)
    want("guard", (res["guard"]["by_split"]["dev"], res["guard"]["refused"]), (3, 0))

    # ---- 3 open documents (values read by eye from the block files on 13.10.2026)
    expected = {
        "22700": {"parliament": "BE", "language": "de", "s1_role": "proposal", "s1_rule_id": "P1", "blocks": 10,
                  "first_date": ("2013-09-09", "9. September 2013", 1, "B5"), "response": None,
                  "line": (3, "Der Grosse Rat", "B4")},
        "45623": {"parliament": "TI", "language": "it", "s1_role": "proposal", "s1_rule_id": "P1", "blocks": 23,
                  "first_date": ("2019-12-20", "20 dicembre 2019", 1, "B2"), "response": None,
                  "line": (2, "20 dicembre 2019 / 212.19", "B2")},
        "684152": {"parliament": "CHE", "language": "fr", "s1_role": "combined", "s1_rule_id": "A1", "blocks": 23,
                   "first_date": ("2026-01-28", "28.01.2026", 1, "B6"), "response": "B14",
                   "line": (0, "Département fédéral des finances DFF", "B1")},
    }
    docs_out = {}
    for d in SELFTEST_DOCS:
        doc = load_doc(d)
        e = expected[d]
        for b in doc.blocks:
            want(f"{d}.{b.block}.span", doc.text[b.char_start:b.char_end], b.text)
            want(f"{d}.{b.block}.locate", doc.locate(b.char_start).block if b.text else b.block, b.block)
        for ln in doc.lines:
            want(f"{d}.line{ln.number}", doc.text[ln.char_start:ln.char_end], ln.text)
            want(f"{d}.line{ln.number}.at", doc.line_at(ln.char_start).number, ln.number)
        want(f"{d}.line_numbers", [ln.number for ln in doc.lines], list(range(len(doc.lines))))
        for k in ("parliament", "language", "s1_role", "s1_rule_id"):
            want(f"{d}.{k}", getattr(doc, k), e[k])
        want(f"{d}.blocks", len(doc.blocks), e["blocks"])
        dates = doc.dates()
        first = dates[0] if dates else None
        want(f"{d}.first_date", (first.iso, first.wording, first.page, first.block) if first else None, e["first_date"])
        for h2 in dates:
            want(f"{d}.date_span", doc.text[h2.start:h2.end], h2.wording)
        fr = doc.first_response_block()
        want(f"{d}.first_response_block", fr.block if fr else None, e["response"])
        want(f"{d}.before_plus_from", len(doc.blocks_before_response()) + len(doc.blocks_from_response()), len(doc.blocks))
        n, t, blk = e["line"]
        ln = doc.first_lines(15)[n]
        want(f"{d}.line", (ln.text, ln.block), (t, blk))
        want(f"{d}.last_lines", [x.number for x in doc.last_lines(3)], [x.number for x in doc.lines[-3:]])
        c = read_field(doc, "title", registry=reg)
        want(f"{d}.candidate", (doc.text[c.char_start:c.char_end], c.block, c.page), (c.value, doc.lines[0].block, doc.lines[0].page))
        if len(c.evidence) > EVIDENCE_MAX:
            bad.append(f"{d}: evidence too long")
        try:
            check_result(doc, "title", ValueCandidate("title", "x", "x", "test_first_line", 1, "B1", 0, 3, ""))
            bad.append(f"{d}: check_result accepted a span that does not give the value")
        except BadResult:
            pass
        # the same document through the loader of the package, with and with no rule file
        p_blocks, p_rules = DOCS_DIR / f"{d}.json", RULES_DIR / f"{d}.json"
        d2 = load_from_block_file(p_blocks, p_rules)
        want(f"{d}.block_file_loader", (d2.text, d2.s1_role, [b.rule_role for b in d2.blocks], d2.language),
             (doc.text, doc.s1_role, [b.rule_role for b in doc.blocks], doc.language))
        d3 = load_from_block_file(p_blocks)
        want(f"{d}.no_rule_file", (d3.s1_role, d3.has_rule_file, {b.rule_role for b in d3.blocks}, d3.first_response_block()),
             (None, False, {None}, None))
        d4 = load_doc(d, apertus_roles=True)
        roles = {}
        for b in doc.blocks:
            roles[b.rule_role] = roles.get(b.rule_role, 0) + 1
        ap = {}
        for b in d4.blocks:
            ap[b.apertus_role] = ap.get(b.apertus_role, 0) + 1
        docs_out[d] = {"parliament": doc.parliament, "language": doc.language, "s1_role": doc.s1_role,
                       "s1_rule_id": doc.s1_rule_id, "s1_export_condition": doc.s1_export_condition,
                       "blocks": len(doc.blocks), "lines": len(doc.lines), "pages": doc.pages, "dates": len(dates),
                       "rule_roles": dict(sorted(roles.items())), "apertus_roles_optional_tier": dict(sorted(ap.items())),
                       "first_response_block": fr.block if fr else None, "guessed_language": guess_language(doc.text)}
    res["documents"] = docs_out
    res["registered_readers_of_the_module"] = sorted(REGISTRY)
    res["failed"] = bad
    res["result"] = "all cases as expected" if not bad else f"{len(bad)} cases NOT AS EXPECTED"
    return res


def show(doc_id: str, n_lines: int) -> None:
    """Print the head facts, the first lines and the block roles of one open development document."""
    doc = load_doc(doc_id)
    print(json.dumps({"doc_id": doc.doc_id, "parliament": doc.parliament, "language": doc.language,
                      "s1_role": doc.s1_role, "s1_rule_id": doc.s1_rule_id,
                      "s1_export_condition": doc.s1_export_condition, "blocks": len(doc.blocks),
                      "lines": len(doc.lines), "pages": doc.pages, "fold": fold_of(doc_id)}, ensure_ascii=False))
    for ln in doc.first_lines(n_lines):
        b = doc.blocks[ln.block_index]
        print(f"{ln.number:3d} p{ln.page} {ln.block:5s} {b.label:15s} {str(b.rule_role):14s} {ln.text[:100]!r}")
    for h in doc.dates()[:10]:
        print(f"date {h.iso} p{h.page} {h.block} {h.start}:{h.end} {h.wording!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description="common interface of the value rules (plan task T0)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    s = sub.add_parser("show")
    s.add_argument("doc_id")
    s.add_argument("--lines", type=int, default=15)
    a = ap.parse_args()
    if a.cmd == "show":
        show(a.doc_id, a.lines)
        return 0
    r = selftest()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())

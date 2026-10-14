# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""m11_value_norm: the normalisation and comparison rules of addendum G (rule G3, chapters 3.3 and 4).

One module for all tools: the reference tool (src/m11_value_reference.py) makes each normalised reference value
with a function of this module, and the measurement code imports the same functions for the reader values.
Source of each rule: crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md, version 2 (13.10.2026).

Version 2 of the addendum changed these points of the module (module version m11-value-norm-2):
  chapter 4.2 item 2    the type string of a reader is compared with no change (no strip).
  chapter 4.3 item 5    the overlap is compared with whole numbers (5 x common tokens >= 4 x larger set size).
  chapter 4.5 item 2    a reader string that is not a calendar day YYYY-MM-DD is different and not "within 7 days".
  chapter 4.6 item 8    the responder input is always a text; a key of table 3 is not accepted in its key form.
  chapter 4.9           two empty normal forms are never equal (this was so in version 1 of the module).
The function norm() gives the normal form of a REFERENCE value (it reads the first 10 characters of an export
date string). The function compare() applies the reader rules to the reader string.

The module uses the standard library only. It reads no file and no document. It calculates no measure.

Field ids (addendum G, table 1): affair_type, title, affair_number, submission_date, response_date,
responder_name, first_author. The reader registry of src/m11_values_base.py uses the ids `responder` and
`sponsor` for the last two; FIELD_ALIASES maps them.

Use:
  import m11_value_norm as vn
  vn.fold("Conseil d'État")                      -> "conseil d etat"
  vn.norm(field, value)                          -> the normal form of ONE reference value (None = no normal form)
  vn.compare(field, reader_value, references)    -> {"equal": bool, ...}  (references = normal forms of the file)
  python src/m11_value_norm.py selftest          -> unit cases, exit code 1 on a failure
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
import unicodedata

VERSION = "m11-value-norm-2"
ADDENDUM = "gate-jev-cascade-criteria-addendum-g.md, version 2"

FIELDS = ("affair_type", "title", "affair_number", "submission_date", "response_date", "responder_name",
          "first_author")
FIELD_ALIASES = {"responder": "responder_name", "sponsor": "first_author"}
TITLE_OVERLAP_MIN = 0.8            # chapter 4.3, item 5 (the comparison uses the whole numbers 5 and 4)
DATE_NEAR_DAYS = 7                 # chapter 4.5, item 4 (information only)


def field_id(field: str) -> str:
    """The field id of addendum G for an id of the addendum or of the reader registry."""
    f = FIELD_ALIASES.get(field, field)
    if f not in FIELDS:
        raise ValueError(f"unknown field: {field}")
    return f


# ------------------------------------------------------------------ chapter 4.1: fold

_NOT_ALNUM = re.compile(r"[^a-z0-9]")
_SPACES = re.compile(r" +")


def fold(s: str | None) -> str:
    """The base function of chapter 4.1, steps 1 to 7, in the order of the text."""
    s = unicodedata.normalize("NFKC", s or "")                       # step 1
    s = s.replace("­", "")                                      # step 2
    s = s.replace("ß", "ss")                                         # step 3
    s = s.lower()                                                    # step 4
    s = unicodedata.normalize("NFD", s)                              # step 5
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = _NOT_ALNUM.sub(" ", s)                                       # step 6
    return _SPACES.sub(" ", s).strip()                               # step 7


def token_list(s: str | None) -> list[str]:
    """The parts of fold(s) between spaces."""
    f = fold(s)
    return f.split(" ") if f else []


# ------------------------------------------------------------------ chapter 4.2: affair type

def norm_affair_type(value: str | None) -> str | None:
    """The list value as a string with no space at the ends. No value is merged with a different value."""
    v = (value or "").strip()
    return v or None


def affair_type_equal(reader: str | None, references) -> bool:
    """Chapter 4.2, item 2: the same string, with no change of the reader string (no fold, no strip, no case)."""
    return isinstance(reader, str) and reader != "" and reader in set(references or ())


# ------------------------------------------------------------------ chapter 4.3: title

def norm_title(value: str | None) -> str | None:
    """fold(value); None if the fold form is empty."""
    return fold(value) or None


def title_overlap(a: str | None, b: str | None) -> float:
    """Chapter 4.3, items 2 to 4: |A and B| / max(|A|, |B|) on the token sets; 0 if one set is empty."""
    ta, tb = set(token_list(a)), set(token_list(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def title_compare(reader: str | None, references) -> dict:
    """equal = exact form or overlap >= 0.8 with one reference value; `exact` is the count that is given apart.
    The overlap is compared with whole numbers: 5 x (tokens in A and in B) >= 4 x (the larger set size).
    An empty fold form of the reader value or of a reference value is never equal (chapter 4.9)."""
    r = fold(reader)
    ta = set(r.split(" ")) if r else set()
    exact = near = False
    best = 0.0
    for ref in references or ():
        fr = fold(ref)
        tb = set(fr.split(" ")) if fr else set()
        if not ta or not tb:
            continue
        if r == fr:
            exact = True
        common, larger = len(ta & tb), max(len(ta), len(tb))
        if 5 * common >= 4 * larger:
            near = True
        best = max(best, common / larger)
    return {"equal": bool(exact or near), "exact": exact, "overlap": best}


# ------------------------------------------------------------------ chapters 3.3 and 4.4: affair number

_RX_S1 = re.compile(r"[0-9]{5,}")
_RX_S2 = re.compile(r"[0-9a-f]{8}")
_RX_RUN = re.compile(r"[a-z]+|[0-9]+")
_RX_SHORT_DIGITS = re.compile(r"[0-9]{1,4}")


def number_class(value: str | None) -> str | None:
    """Chapter 3.3: the class "system identifier" of ONE export number, on the stripped string, full match.
    S1 = digits only, 5 or more digits; S2 = 8 hexadecimal characters in lower case. S1 is tested first
    (a string of 8 digits is in the two patterns). None = no class."""
    v = (value or "").strip()
    if _RX_S1.fullmatch(v):
        return "S1"
    if _RX_S2.fullmatch(v):
        return "S2"
    return None


def number_is_short_digits(value: str | None) -> bool:
    """Chapter 3.3, item 8: a number of 1 to 4 digits only (it stays a reference value; counts apart)."""
    return bool(_RX_SHORT_DIGITS.fullmatch((value or "").strip()))


def norm_number(value: str | None) -> list[str] | None:
    """Chapter 4.4: fold, runs of letters and runs of digits, no leading zeros in a run of digits
    (a run of zeros only becomes "0"). None if the list is empty."""
    runs = []
    for run in _RX_RUN.findall(fold(value)):
        if run[0].isdigit():
            run = run.lstrip("0") or "0"
        runs.append(run)
    return runs or None


def number_equal(reader: str | None, references) -> bool:
    """The run list of the reader value is the same as the run list of one reference value.
    `references` holds run lists (the form of the reference file) or raw strings."""
    r = norm_number(reader)
    if r is None:
        return False
    for ref in references or ():
        if (norm_number(ref) if isinstance(ref, str) else list(ref)) == r:
            return True
    return False


# ------------------------------------------------------------------ chapters 3.2 and 4.5: dates

_RX_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def norm_day(value: str | None) -> str | None:
    """Chapter 3.2, items 4 and 5: the first 10 characters of the string, form YYYY-MM-DD, a real calendar day.
    A day that starts with 1900 is no reference (None). The time part is not used. No time zone is applied."""
    if not isinstance(value, str):
        return None
    day = value.strip()[:10]
    if not _RX_DAY.fullmatch(day) or day.startswith("1900"):
        return None
    try:
        _dt.date.fromisoformat(day)
    except ValueError:
        return None
    return day


def day_reason(value: str | None) -> str | None:
    """Why norm_day gives None: empty, day_1900 or bad_form. None if the value has a normal form."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return "empty"
    if norm_day(value) is not None:
        return None
    if isinstance(value, str) and value.strip()[:10].startswith("1900"):
        return "day_1900"
    return "bad_form"


def reader_day(value) -> str | None:
    """Chapter 4.5, items 1 and 2: the reader string must be a calendar day in the form YYYY-MM-DD. The whole
    string must have this form (no strip, no time part). None = the string is not such a day."""
    if not isinstance(value, str) or not _RX_DAY.fullmatch(value):
        return None
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        return None
    return value


def days_to_nearest(reader: str | None, references) -> int | None:
    """The smallest absolute difference in days between the reader day and a day of the reference set."""
    r = reader_day(reader)
    refs = [d for d in (norm_day(x) for x in references or ()) if d]
    if r is None or not refs:
        return None
    rd = _dt.date.fromisoformat(r)
    return min(abs((rd - _dt.date.fromisoformat(d)).days) for d in refs)


def date_compare(reader: str | None, references) -> dict:
    """equal = the day is in the reference set. within_7_days is the second count (it holds the equal cases;
    information only, it changes no outcome). A reader string that is not a calendar day YYYY-MM-DD is not
    equal and not within 7 days (chapter 4.5, item 2); the key reader_is_a_day says so."""
    r = reader_day(reader)
    refs = {d for d in (norm_day(x) for x in references or ()) if d}
    diff = days_to_nearest(r, refs)
    return {"equal": r is not None and r in refs, "within_7_days": diff is not None and diff <= DATE_NEAR_DAYS,
            "days_to_nearest": diff, "reader_is_a_day": r is not None}


# ------------------------------------------------------------------ chapter 4.6: responder (table 3)

# key -> (patterns on the fold form, full token)
BODY_WORDS: dict[str, tuple[tuple[str, ...], bool]] = {
    "regierungsrat": (("regierungsrat",), False),
    "staatsrat": (("staatsrat",), False),
    "bundesrat": (("bundesrat",), False),
    "stadtrat": (("stadtrat",), False),
    "gemeinderat": (("gemeinderat",), False),
    "standeskommission": (("standeskommission",), False),
    "kleiner_rat": (("kleine rat", "kleiner rat", "kleinen rat"), False),
    "regierung": (("regierung",), True),
    "conseil_etat": (("conseil d etat",), False),
    "conseil_municipal": (("conseil municipal",), False),
    "conseil_communal": (("conseil communal",), False),
    "conseil_federal": (("conseil federal",), False),
    "conseil_administratif": (("conseil administratif",), False),
    "conseil_executif": (("conseil executif",), False),
    "municipalite": (("municipalite",), False),
    "gouvernement": (("gouvernement",), False),
    "consiglio_di_stato": (("consiglio di stato",), False),
    "municipio": (("municipio",), False),
    "consiglio_federale": (("consiglio federale",), False),
    "governo": (("governo",), True),
}
_BODY_RX = [(key, pat, re.compile(r"(?<![a-z0-9])" + re.escape(pat) + (r"(?![a-z0-9])" if full else "")))
            for key, (pats, full) in BODY_WORDS.items() for pat in pats]


def body_word(value: str | None) -> str | None:
    """Chapter 4.6, items 2 and 3: the body word of a string, found in fold(string). A pattern matches at the
    start of a token. The match with the lowest start position gives the key; at one position the longer pattern.
    None = no body word of table 3."""
    f = fold(value)
    best = None
    for key, pat, rx in _BODY_RX:
        m = rx.search(f)
        if m and (best is None or (m.start(), -len(pat)) < best[0]):
            best = ((m.start(), -len(pat)), key)
    return best[1] if best else None


def norm_responder(value: str | None) -> str | None:
    """The key of table 3 of a TEXT (chapter 4.6, item 8). The input is always a text: a key of table 3 in its
    key form is not accepted as it is. Example: `conseil_etat` has the fold form `conseil etat`; it holds no body
    word of table 3 (chapter 4.8, item 9)."""
    return body_word(value)


def responder_equal(reader: str | None, references) -> bool:
    """The body word of the reader value is in the reference set. No body word = not equal (outcome different)."""
    r = norm_responder(reader)
    return r is not None and r in set(references or ())


# ------------------------------------------------------------------ chapter 4.7: first author

def norm_author(value: str | None) -> list[str] | None:
    """The token list of a family name; None if it is empty."""
    return token_list(value) or None


def _is_part(short: list[str], long: list[str]) -> bool:
    n = len(short)
    return n > 0 and any(long[i:i + n] == short for i in range(len(long) - n + 1))


def author_equal(reader: str | None, references) -> bool:
    """The token lists are the same, or one list is a part of the other list with no gap.
    `references` holds token lists (the form of the reference file) or raw strings."""
    r = norm_author(reader)
    if r is None:
        return False
    for ref in references or ():
        t = norm_author(ref) if isinstance(ref, str) else list(ref)
        if t and (_is_part(r, t) or _is_part(t, r)):
            return True
    return False


# ------------------------------------------------------------------ one entry for all fields

_NORM = {
    "affair_type": norm_affair_type,
    "title": norm_title,
    "affair_number": norm_number,
    "submission_date": norm_day,
    "response_date": norm_day,
    "responder_name": norm_responder,
    "first_author": norm_author,
}
NORMALISATION_RULE = {
    "affair_type": "G3-4.2 list value, same string",
    "title": "G3-4.3 fold; equal if same fold string or token-set overlap >= 0.8",
    "affair_number": "G3-4.4 fold, runs of letters and digits, no leading zeros",
    "submission_date": "G3-4.5 day YYYY-MM-DD in the reference set",
    "response_date": "G3-4.5 day YYYY-MM-DD in the reference set",
    "responder_name": "G3-4.6 body word of table 3",
    "first_author": "G3-4.7 token list of the family name, equal or gap-free part",
}


def norm(field: str, value):
    """The normal form of ONE value of a field (None = the value has no normal form)."""
    return _NORM[field_id(field)](value)


def compare(field: str, reader_value: str | None, references) -> dict:
    """The comparison of chapter 4 for one reader value and the normal forms of the reference of one document.
    The result always has the key `equal`. Extra keys: title -> exact, overlap; dates -> within_7_days,
    days_to_nearest. The function gives no outcome: the measurement code makes the 4 outcomes of chapter 5.1
    (a document with no reference never comes here)."""
    f = field_id(field)
    if f == "affair_type":
        return {"equal": affair_type_equal(reader_value, references)}
    if f == "title":
        return title_compare(reader_value, references)
    if f == "affair_number":
        return {"equal": number_equal(reader_value, references)}
    if f in ("submission_date", "response_date"):
        return date_compare(reader_value, references)
    if f == "responder_name":
        return {"equal": responder_equal(reader_value, references)}
    return {"equal": author_equal(reader_value, references)}


# ------------------------------------------------------------------ unit cases

def selftest() -> dict:
    """Unit cases with hand-made values. The examples of the addendum text are marked (G)."""
    cases: list[tuple[str, object, object]] = []

    def want(name, got, expected):
        cases.append((name, got, expected))

    # fold, chapter 4.1
    want("fold accents", fold("Conseil d'État"), "conseil d etat")
    want("fold sharp s", fold("Straße  und\tWeg"), "strasse und weg")
    want("fold soft hyphen", fold("Regie­rungs­rat"), "regierungsrat")
    want("fold NFKC ligature", fold("Geschäﬀt"), "geschafft")
    want("fold umlaut", fold("Mühlheim-Übersax"), "muhlheim ubersax")
    want("fold punctuation ends", fold(" «Titel»: 12/3. "), "titel 12 3")
    want("fold empty", fold(None), "")
    want("fold non-latin letter to space", fold("Søren"), "s ren")
    want("token list", token_list("L'égalité, enfin!"), ["l", "egalite", "enfin"])
    # affair type, chapter 4.2
    want("type equal", compare("affair_type", "motion", ["motion"])["equal"], True)
    want("type with spaces is no list value (no change of the string)", compare("affair_type", " motion ", ["motion"])["equal"], False)
    want("type other case is different", compare("affair_type", "Motion", ["motion"])["equal"], False)
    want("type question is not request", compare("affair_type", "question", ["request"])["equal"], False)
    want("type none", compare("affair_type", None, ["motion"])["equal"], False)
    # title, chapter 4.3
    want("title exact", title_compare("Hustenmittel sind legale Suchtmittel!", ["hustenmittel sind legale suchtmittel"]),
         {"equal": True, "exact": True, "overlap": 1.0})
    want("title overlap 4 of 5", title_overlap("a b c d", "a b c d e"), 0.8)
    want("title overlap 4 of 5 equal", title_compare("a b c d", ["a b c d e"])["equal"], True)
    want("title overlap 3 of 4", title_compare("a b c", ["a b c d"]), {"equal": False, "exact": False, "overlap": 0.75})
    want("title empty set", title_overlap("", "a b"), 0.0)
    want("title sets, not lists", title_overlap("a a b", "b a"), 1.0)
    want("title set equal, not exact", title_compare("b a", ["a b"]), {"equal": True, "exact": False, "overlap": 1.0})
    want("title no reader value", title_compare(None, ["a b"])["equal"], False)
    want("title overlap 8 of 10 with whole numbers", title_compare("a b c d e f g h x y", ["a b c d e f g h i j"])["equal"], True)
    want("title overlap 7 of 9", title_compare("a b c d e f g x y", ["a b c d e f g h i"])["equal"], False)
    want("title two empty forms are never equal (4.9)", title_compare("---", ["", "!"]), {"equal": False, "exact": False, "overlap": 0.0})
    want("number empty reader form is different (4.9)", number_equal(" - ", [[], ["1"]]), False)
    # affair number, chapters 3.3 and 4.4
    want("number (G) in2211", norm_number("in2211"), ["in", "2211"])
    want("number (G) 2019.SR.000009", norm_number("2019.SR.000009"), ["2019", "sr", "9"])
    want("number zeros only", norm_number("17.000"), ["17", "0"])
    want("number case and separators", number_equal("IN 22-11", [["in", "22", "11"]]), True)
    want("number glued runs differ", number_equal("IN2211", [["in", "22", "11"]]), False)
    want("number leading zeros", number_equal("0107 / 2015", ["107-2015"]), True)
    want("number 2-digit year differs", number_equal("107-15", ["107-2015"]), False)
    want("number missing run differs", number_equal("2015.334", ["2015.RRGR.334"]), False)
    want("number empty", norm_number(" - "), None)
    want("class S1 5 digits", number_class(" 12345 "), "S1")
    want("class 4 digits", number_class("1234"), None)
    want("class S2 hex", number_class("1db218b5"), "S2")
    want("class 8 digits is S1", number_class("20190001"), "S1")
    want("class upper hex is none", number_class("1DB218B5"), None)
    want("class 9 hex is none", number_class("1db218b5a"), None)
    want("class structured", number_class("2019.SR.000009"), None)
    want("class full match only", number_class("12345 a"), None)
    want("short digits", [number_is_short_digits("123"), number_is_short_digits("12345"), number_is_short_digits("1a")],
         [True, False, False])
    # dates, chapters 3.2 and 4.5
    want("day with time", norm_day("2013-01-21T00:00:00"), "2013-01-21")
    want("day time not midnight, no zone step", norm_day("2020-03-04T23:30:00"), "2020-03-04")
    want("day 1900", norm_day("1900-01-01T00:00:00"), None)
    want("day 1900 reason", day_reason("1900-01-01"), "day_1900")
    want("day none", [norm_day(None), day_reason(None), day_reason("")], [None, "empty", "empty"])
    want("day bad form", [norm_day("21.01.2013"), day_reason("21.01.2013")], [None, "bad_form"])
    want("day not a calendar day", norm_day("2013-02-30"), None)
    want("date equal in set", date_compare("2013-01-21", ["2013-01-17", "2013-01-21"]),
         {"equal": True, "within_7_days": True, "days_to_nearest": 0, "reader_is_a_day": True})
    want("date 4 days", date_compare("2013-01-17", ["2013-01-21"]),
         {"equal": False, "within_7_days": True, "days_to_nearest": 4, "reader_is_a_day": True})
    want("date 7 days", date_compare("2013-01-14", ["2013-01-21"])["within_7_days"], True)
    want("date 8 days", date_compare("2013-01-13", ["2013-01-21"]),
         {"equal": False, "within_7_days": False, "days_to_nearest": 8, "reader_is_a_day": True})
    want("date no reader day", date_compare(None, ["2013-01-21"]),
         {"equal": False, "within_7_days": False, "days_to_nearest": None, "reader_is_a_day": False})
    bad = {"equal": False, "within_7_days": False, "days_to_nearest": None, "reader_is_a_day": False}
    want("date reader string with a time part is no day (4.5 item 2)", date_compare("2013-01-21T00:00:00", ["2013-01-21"]), bad)
    want("date reader string in a printed form is no day", date_compare("21.01.2013", ["2013-01-21"]), bad)
    want("date reader string that is no calendar day", date_compare("2013-02-30", ["2013-03-01"]), bad)
    want("date reader string with a space is no day", date_compare(" 2013-01-21", ["2013-01-21"]), bad)
    want("reader day", [reader_day("2013-01-21"), reader_day("2013-1-21"), reader_day(None)], ["2013-01-21", None, None])
    # responder, chapter 4.6
    want("body regierungsrat", body_word("Regierungsrat des Kantons Bern"), "regierungsrat")
    want("body genitive", body_word("Antwort des Regierungsrates"), "regierungsrat")
    want("body regierung full token", body_word("Die Regierung des Kantons"), "regierung")
    want("body regierungen is no full token", body_word("Regierungen"), None)
    want("body regierungsrat is not regierung", body_word("Regierungsrat"), "regierungsrat")
    want("body token start", body_word("Altregierungsrat"), None)
    want("body conseil d'etat", body_word("Le Conseil d'État"), "conseil_etat")
    want("body conseil-executif", body_word("Conseil-exécutif"), "conseil_executif")
    want("body consiglio esecutivo not in table", body_word("Consiglio esecutivo"), None)
    want("body kleiner rat", [body_word("Kleiner Rat"), body_word("des Kleinen Rates"), body_word("Der Kleine Rat")],
         ["kleiner_rat"] * 3)
    want("body lowest position", body_word("Der Stadtrat an den Gemeinderat"), "stadtrat")
    want("body governo full token", [body_word("Il Governo"), body_word("governolo")], ["governo", None])
    want("body municipio", body_word("Il Municipio di Lugano"), "municipio")
    want("body none", body_word("Kommission"), None)
    want("responder (G) key form conseil_etat is no body word", [fold("conseil_etat"), norm_responder("conseil_etat")],
         ["conseil etat", None])
    want("responder (G) key form is different", compare("responder_name", "conseil_etat", ["conseil_etat"])["equal"], False)
    want("responder key forms whose fold form holds a pattern give that body word (rule for a text)",
         [norm_responder(k) for k in ("conseil_municipal", "conseil_federal")], ["conseil_municipal", "conseil_federal"])
    want("responder text of the key conseil_etat is equal", compare("responder_name", "Conseil d'Etat", ["conseil_etat"])["equal"], True)
    want("responder equal", compare("responder_name", "Der Regierungsrat", ["conseil_executif", "regierungsrat"])["equal"], True)
    want("responder other word", compare("responder_name", "Stadtrat", ["gemeinderat"])["equal"], False)
    want("responder no word", compare("responder_name", "Kommission", ["gemeinderat"])["equal"], False)
    want("responder alias field id", compare("responder", "Stadtrat Zug", ["stadtrat"])["equal"], True)
    # first author, chapter 4.7
    want("author same", author_equal("Mühlheim", [["muhlheim"]]), True)
    want("author part of reference", author_equal("Müller", ["Müller Meier"]), True)
    want("author reference part of reader", author_equal("von Allmen-Meier", [["allmen"]]), True)
    want("author gap", author_equal("von Meier", [["von", "allmen", "meier"]]), False)
    want("author different", author_equal("Meier", [["muller"]]), False)
    want("author empty", author_equal("-", [["muller"]]), False)
    want("author alias field id", compare("sponsor", "Linder", [["linder"]])["equal"], True)
    # norm entry
    want("norm entry", [norm("title", "Ä b"), norm("affair_number", "A-01"), norm("response_date", "2020-01-02T10:00:00"),
                        norm("responder", "Staatsrat"), norm("sponsor", "De la Rive")],
         ["a b", ["a", "1"], "2020-01-02", "staatsrat", ["de", "la", "rive"]])
    want("body word table has 20 keys", len(BODY_WORDS), 20)

    failed = [{"case": n, "got": g, "expected": e} for n, g, e in cases if g != e]
    return {"version": VERSION, "cases": len(cases), "failed": failed}


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "selftest":
        res = selftest()
        for f in res["failed"]:
            print("FAILED", f)
        print(f"{res['version']}: unit cases {res['cases']}, failed {len(res['failed'])}")
        return 1 if res["failed"] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

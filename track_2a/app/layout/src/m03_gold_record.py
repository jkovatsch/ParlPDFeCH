"""Gold set record (E33): export context, build, validation and derivation of one document.

A gold set record has two files (gold-record guideline, chapter 2): the eCH-0295 instance
(`instance.yaml`, root class Container, valid against I95) and the provenance file (`provenance.yaml`,
root class GoldRecord of `src/m03_gold_profile.yaml`). A proposal is written by AI agents as
`instance.draft.yaml` (the instance WITHOUT the wording of the TextBlocks) and `evidence.yaml` (the
evidence of each value and the atoms of each text block). `build` makes the two record files: it
copies the wording of each text block from the atoms (E19: no generated text), in the form of rule
G19 (paragraphs, headings, lists, tables, joined lines, removed hyphens and page furniture, each
change recorded), and it makes one GoldValue for each leaf value with its evidence.

Folders: development documents daten/gold/records/<stage>/<doc_id>/, test documents
daten/gold/test/records/<stage>/<doc_id>/ (process rule 6). Stages: proposal_A, proposal_B (two AI
coders), proposal (adjudicated), review (after Jonathan's review).

Commands:
  context DOC...                 export context of each document -> daten/gold[/test]/context/<doc_id>.json
  build DOC --stage S            instance.draft.yaml + evidence.yaml -> instance.yaml + provenance.yaml
  validate DOC --stage S         I95 (linkml-validate), gold profile, evidence and verbatim checks, E20 derivation
  derive DOC --stage S           E20 isolation answers from the record (guideline chapter 7.1) -> e20_answers.json
  diff DOC --a S1 --b S2         differences of two stages: leaf values and text block atoms
  checkf DOC --stage S           compare the derived answers with Jonathan's block decision of the pilot (Check F)
  textform DOC --stage S         text-form view: elements, line-end hyphens, candidates for text-form decisions

Usage:  uv run python src/m03_gold_record.py context 879163 375917
        uv run python src/m03_gold_record.py build 879163 --stage proposal_A
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import TEST, iso_path, pdf_path  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "daten/gold"
EXPORTS = ROOT / "daten/roh/exports"
I95 = ROOT / "quellen/political-affairs-ech-group/ech-0295_affairs/input/schema.yaml"
PROFILE = ROOT / "src/m03_gold_profile.yaml"
GUIDE = ROOT / "crisp-dm/03-data-preparation/gold-record-guideline.md"
FIELDS = ROOT / "crisp-dm/03-data-preparation/gold-record/fields.yaml"
E20_FILE = ROOT / "crisp-dm/03-data-preparation/isolation-level-e20.md"
VERSION = "gold-record-v1"
MINT = "https://data.parlpdfech.example/id/"

# E20 answer of each pair of slot and text type (guideline chapter 7.2)
ANSWER = {("Affair.title", "title"): "title", ("Affair.title", "short_title"): "short_title",
          ("Submission.texts", "submitted"): "submitted", ("Submission.texts", "reasoning"): "reasoning",
          ("Submission.texts", "summary"): "summary", ("ResponseStep.texts", "response"): "response",
          ("ResponseStep.texts", "recommendation"): "recommendation", ("ResponseStep.texts", "summary"): "summary",
          ("CommitteeDecision.text", "recommendation"): "committee_recommendation",
          ("Speech.text", None): "speech", ("Proposition.text", None): "proposition", ("Vote.text", None): "vote"}
# a word after a suspended line-end hyphen: the hyphen stays with its space ("Bundes- und"; G19 detail 12)
CONJ = {"und", "oder", "bzw", "sowie", "resp", "et", "ou", "e", "o", "ed", "od", "u", "bis"}
# printed list markers (G19 detail 6). A character of the Private Use Area is a glyph of a symbol font (for
# example U+F0B7 of Symbol), never a letter; U+E000 to U+E003 are the marks of corrected().
MARKER = re.compile(r"^\s*((\d{1,3}|[a-zA-Z]|[ivxlcIVXLC]{1,6})[.)]|[-–•·▪◦*>›\ue004-\uf8ff])\s+")


def is_test(doc_id: str) -> bool:
    return iso_path("atome", doc_id).is_relative_to(TEST)


def base_dir(doc_id: str) -> Path:
    return (TEST if is_test(doc_id) else GOLD)


def rec_dir(doc_id: str, stage: str) -> Path:
    return base_dir(doc_id) / "records" / stage / doc_id


def atoms(doc_id: str) -> list[dict]:
    return json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))["atome"]


def ranges(doc_id: str, spec, keep_order: bool = False) -> list[str]:
    """Atom ids of a list of ranges ("B9.1-B12.3", "B14.1") in document order. keep_order: in the order of the
    list, each range in document order (the reading order of a text block, G19 and 4.21 text detail 1)."""
    ids = [a["id"] for a in atoms(doc_id)]
    pos = {a: i for i, a in enumerate(ids)}
    out = []
    for part in (spec if isinstance(spec, list) else [spec]):
        part = str(part).strip()
        a, b = (part.split("-", 1) + [None])[:2] if "-" in part and part.count("B") == 2 else (part, part)
        a, b = a.strip(), (b or a).strip()
        if a not in pos or b not in pos or pos[b] < pos[a]:
            raise SystemExit(f"{doc_id}: bad atom range {part!r}")
        out += ids[pos[a]: pos[b] + 1]
    seen = set()
    return [x for x in (out if keep_order else sorted(out, key=pos.get)) if not (x in seen or seen.add(x))]


# ---------------------------------------------------------------- export context

def doc_rows(doc_ids: set[str]) -> dict[str, dict]:
    want = set(doc_ids)
    found = {}
    lists = [GOLD / n for n in ("pilot.csv", "test.csv", "extension.csv", "bulk_test.csv", "bulk_train.csv")]
    body = {}
    for p in [ROOT / "daten/analyse/lehrer_stichprobe/auswahl_lehrer.csv", *lists]:
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get("doc_id") in want and r.get("body_key"):
                        body[r["doc_id"]] = r["body_key"]
    for b in sorted(set(body.values())):
        f = EXPORTS / "docs" / f"docs_{b}.ndjson.gz"
        if not f.exists():
            continue
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                x = json.loads(line)
                if str(x.get("id")) in want:
                    x.pop("text", None)
                    x.pop("tika_metadata", None)
                    found[str(x["id"])] = x
    return found


def scan(name: str, pred) -> list[dict]:
    p = EXPORTS / f"{name}.ndjson.gz"
    out = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for line in fh:
            if pred(line):
                x = json.loads(line)
                if pred(x):
                    out.append(x)
    return out


def cmd_context(args) -> None:
    docs = doc_rows(set(args.docs))
    missing = sorted(set(args.docs) - set(docs))
    if missing:
        print("no export row for", missing)
    # all docs rows of the same file (hash): their affairs are main affairs (G1)
    hashes = {d["hash"] for d in docs.values() if d.get("hash")}
    same = {}
    for b in sorted({d["body_key"] for d in docs.values()}):
        with gzip.open(EXPORTS / "docs" / f"docs_{b}.ndjson.gz", "rt", encoding="utf-8") as fh:
            for line in fh:
                if any(h in line for h in hashes):
                    x = json.loads(line)
                    if x.get("hash") in hashes:
                        x.pop("text", None)
                        x.pop("tika_metadata", None)
                        same.setdefault(x["hash"], []).append(x)
    aff_ids = {int(x["affair_id"]) for rows in same.values() for x in rows if x.get("affair_id")}
    sid = {str(a) for a in aff_ids}

    def has_aff(key):
        def f(x):
            if isinstance(x, str):
                return any(f'"{key}": {a}' in x or f'"{key}":{a}' in x for a in sid)
            return str(x.get(key)) in sid
        return f

    affairs = scan("affairs", lambda x: (any(f'"id": {a},' in x or f'"id":{a},' in x for a in sid)
                                         if isinstance(x, str) else str(x.get("id")) in sid))
    events = scan("events", has_aff("affair_id"))
    contributors = scan("contributors", has_aff("affair_id"))
    votings = scan("votings", has_aff("affair_id"))
    agendas = scan("agendas", has_aff("item_affair_id"))
    bodies_keys = {d["body_key"] for d in docs.values()}
    bodies = scan("bodies", lambda x: (any(f'"{b}"' in x for b in bodies_keys) if isinstance(x, str)
                                       else x.get("body_key") in bodies_keys))
    person_ids = {str(c["person_id"]) for c in contributors if c.get("person_id")}
    group_ids = {str(c["group_id"]) for c in contributors if c.get("group_id")} | \
                {str(v["group_id"]) for v in votings if v.get("group_id")}
    meeting_ids = {str(e["meeting_id"]) for e in events if e.get("meeting_id")} | \
                  {str(v["meeting_id"]) for v in votings if v.get("meeting_id")}
    memberships = scan("memberships", lambda x: (any(f'"person_id": {p},' in x or f'"person_id":{p},' in x for p in person_ids)
                                                 if isinstance(x, str) else str(x.get("person_id")) in person_ids)) if person_ids else []
    group_ids |= {str(m["group_id"]) for m in memberships if m.get("group_id")}
    groups = scan("groups", lambda x: (any(f'"id": {g},' in x or f'"id":{g},' in x for g in group_ids)
                                       if isinstance(x, str) else str(x.get("id")) in group_ids)) if group_ids else []
    meetings = scan("meetings", lambda x: (any(f'"id": {m},' in x or f'"id":{m},' in x for m in meeting_ids)
                                           if isinstance(x, str) else str(x.get("id")) in meeting_ids)) if meeting_ids else []
    retrieved = (EXPORTS / "abgerufen_utc.txt").read_text().strip() if (EXPORTS / "abgerufen_utc.txt").exists() else ""
    for d, row in docs.items():
        a_ids = {str(x["affair_id"]) for x in same.get(row.get("hash"), [row]) if x.get("affair_id")}
        ctx = {"doc_id": d, "export_retrieved": retrieved, "doc": row,
               "same_file_rows": same.get(row.get("hash"), []),
               "affairs": [a for a in affairs if str(a["id"]) in a_ids],
               "events": [e for e in events if str(e.get("affair_id")) in a_ids],
               "contributors": [c for c in contributors if str(c.get("affair_id")) in a_ids],
               "votings": [v for v in votings if str(v.get("affair_id")) in a_ids],
               "agendas": [g for g in agendas if str(g.get("item_affair_id")) in a_ids],
               "bodies": [b for b in bodies if b.get("body_key") == row.get("body_key")]}
        pids = {str(c["person_id"]) for c in ctx["contributors"] if c.get("person_id")}
        ctx["memberships"] = [m for m in memberships if str(m.get("person_id")) in pids]
        gids = {str(c["group_id"]) for c in ctx["contributors"] if c.get("group_id")} | \
               {str(m["group_id"]) for m in ctx["memberships"] if m.get("group_id")} | \
               {str(v["group_id"]) for v in ctx["votings"] if v.get("group_id")}
        ctx["groups"] = [g for g in groups if str(g["id"]) in gids]
        mids = {str(e["meeting_id"]) for e in ctx["events"] if e.get("meeting_id")}
        ctx["meetings"] = [m for m in meetings if str(m["id"]) in mids]
        out = base_dir(d) / "context" / f"{d}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{d}: affairs {len(ctx['affairs'])}, events {len(ctx['events'])}, contributors {len(ctx['contributors'])}, "
              f"votings {len(ctx['votings'])}, memberships {len(ctx['memberships'])}, groups {len(ctx['groups'])}")


# ---------------------------------------------------------------- text form (G19)
#
# The text form of a text block follows from the atoms and from the text-form decisions of the
# proposal or the review. The decisions are keys of the text block in evidence.yaml:
#   ocr_corrections  [{atom_id, range_start, range_end, ocr_text, printed_text}]  positions in the Docling full text (G20)
#   keep_hyphen      [atom]   the line-end hyphen of the atom stays although the next word starts in lower case
#   remove_hyphen    [atom]   the line-end hyphen of the atom goes although the default keeps it
#   paragraph_starts [atom]   a printed paragraph (or list item, row) starts at the atom inside a Docling block
#   continues        [atom]   the atom starts a Docling block but continues the element before it (page break)
#   forms            {atom: paragraph | heading_2 | heading_3 | heading_4 | list_item | table_row | table_head_row}
#   heading_ranks    {atom: printed rank}   only when the print has more than three heading ranks (A9)
#   superscripts     [{range_start, range_end}]  printed superscript characters, positions in the Docling full text
#   subscripts       [{range_start, range_end}]  printed subscript characters
#   empty_cells      {atom: [cell index]}  a printed empty table cell before the cell with this index (0 = first)
# The record keeps each decision in GoldTextChanges, so that `validate` rebuilds the same text.

FORM_TAG = {"paragraph": "p", "heading_2": "h2", "heading_3": "h3", "heading_4": "h4"}
FORMS = set(FORM_TAG) | {"list_item", "table_row", "table_head_row"}
ROMAN = re.compile(r"^[ivxlcdm]+$", re.I)
HYPHEN = re.compile(r"(\w)[-\u00ad\u2010]$")
URL = re.compile(r"\b(?:https?://|www\.)[^\s<>\"\ue000-\ue003]+[^\s<>\".,;:!?)\]\ue000-\ue003]")


def roman(s: str) -> int:
    v = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    n, prev = 0, 0
    for ch in reversed(s.lower()):
        x = v[ch]
        n = n - x if x < prev else n + x
        prev = max(prev, x)
    return n


def text_form(tb: dict) -> dict:
    """The text-form decisions of a text block of evidence.yaml (the keys above)."""
    tf = {k: tb.get(k) for k in ("ocr_corrections", "keep_hyphen", "remove_hyphen", "paragraph_starts", "continues",
                                 "forms", "heading_ranks", "superscripts", "subscripts", "empty_cells")}
    bad = {a: f for a, f in (tf["forms"] or {}).items() if f not in FORMS}
    if bad:
        raise SystemExit(f"unknown forms {bad}")
    return tf


def text_form_from_changes(doc_id: str, ch: dict) -> dict:
    """The text-form decisions that the record keeps (inverse of richtext): for the rebuild check."""
    by_pos = {}
    for x in atoms(doc_id):
        for i in range(x["zeichen"][0], x["zeichen"][1]):
            by_pos[i] = x["id"]
    return {"ocr_corrections": ch.get("ocr_corrections") or [],
            "keep_hyphen": [by_pos[p] for p in ch.get("kept_hyphens") or []],
            "remove_hyphen": [by_pos[p] for p in ch.get("hyphens_removed") or []],
            "paragraph_starts": ch.get("paragraph_starts") or [],
            "continues": ch.get("continued_elements") or [],
            "forms": {f["atom_id"]: f["element_form"] for f in ch.get("form_overrides") or []},
            "heading_ranks": {h["atom_id"]: h["printed_rank"] for h in ch.get("heading_ranks") or []},
            "superscripts": ch.get("superscripts") or [], "subscripts": ch.get("subscripts") or [],
            "empty_cells": _cells(ch)}


def _cells(ch: dict) -> dict:
    out = {}
    for e in ch.get("empty_cells") or []:
        out.setdefault(e["atom_id"], []).append(e["cell_index"])
    return out


SUP0, SUP1, SUB0, SUB1 = "\ue000", "\ue001", "\ue002", "\ue003"
# Docling writes ’ – „ “ as ' - " (src/m03_atome.py, TYPO). The text layer keeps the printed character.
TYPO = {"’": "'", "‘": "'", "‚": "'", "‛": "'", "′": "'", "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
        "–": "-", "—": "-", "‒": "-", "―": "-", "‑": "-", "‐": "-"}
TYPOGRAPHY_FROM_TEXT_LAYER = True


def text_layer_corrections(x: dict) -> list[dict]:
    """The printed typographic characters of a text-layer atom (G20a): each character where the text
    layer has a typographic character that Docling replaced. Only one-to-one replacements count."""
    t, s = x.get("text") or "", x.get("text_textschicht") or ""
    if not TYPOGRAPHY_FROM_TEXT_LAYER or not s or x.get("zeilenrahmen_quelle") != "text_layer":
        return []
    ai = [i for i, ch in enumerate(t) if not ch.isspace()]
    sc = [ch for ch in s if not ch.isspace()]
    if len(ai) != len(sc):
        return []
    out = []
    for i, ch in zip(ai, sc):
        if t[i] != ch:
            if TYPO.get(ch) != t[i]:
                return []   # another difference: no automatic correction
            z = x["zeichen"][0] + i
            out.append({"atom_id": x["id"], "range_start": z, "range_end": z + 1, "ocr_text": t[i], "printed_text": ch})
    return out


def corrected(x: dict, tf: dict) -> str:
    """The wording of an atom with the corrections to the printed wording (G20 from the page image, G20a from
    the text layer) and marks for printed superscript and subscript ranges (G19 detail 8). Ranges are
    positions in the Docling full text."""
    t, z0 = x.get("text") or "", x["zeichen"][0]
    mine = lambda key: [c for c in tf.get(key) or [] if x["zeichen"][0] <= c["range_start"] < x["zeichen"][1]
                        or c.get("atom_id") == x["id"]]
    ocr = {c["range_start"] - z0: c for c in mine("ocr_corrections")}
    if ocr and x.get("zeilenrahmen_quelle") == "text_layer":
        raise SystemExit(f"atom {x['id']} has a text layer: no correction from the page image (G20); the text layer "
                         f"gives the typography (G20a)")
    ocr.update({c["range_start"] - z0: c for c in text_layer_corrections(x)})
    marks = {}
    for key, a0, a1 in (("superscripts", SUP0, SUP1), ("subscripts", SUB0, SUB1)):
        for r in mine(key):
            if not (z0 <= r["range_start"] < r["range_end"] <= x["zeichen"][1]):
                raise SystemExit(f"{key} range {r} is not inside atom {x['id']}")
            marks.setdefault(r["range_end"] - z0, []).append(a1)
            marks.setdefault(r["range_start"] - z0, []).append(a0)
    out, i = [], 0
    while True:
        out += sorted(marks.get(i, []), key=lambda m: m not in (SUP1, SUB1))
        if i >= len(t):
            break
        if i in ocr:
            c = ocr[i]
            if t[i:i + len(c["ocr_text"])] != c["ocr_text"] or c["range_end"] - c["range_start"] != len(c["ocr_text"]):
                raise SystemExit(f"OCR correction {c} does not match the wording of atom {x['id']}")
            lo, lp = len(c["ocr_text"]), len(c["printed_text"])
            if abs(lp - lo) > max(3, lo // 2) and not c.get("reviewer_confirmed"):
                raise SystemExit(f"OCR correction {c} changes the length too much: only the reviewer can confirm it (E19)")
            if any(k in marks for k in range(i + 1, i + len(c["ocr_text"]))):
                raise SystemExit(f"a superscript or subscript range cuts the OCR correction {c}")
            out.append(c["printed_text"])
            i += len(c["ocr_text"])
            continue
        out.append(t[i])
        i += 1
    return "".join(out)


def scripts(text: str, plain: bool) -> str:
    """Write the marks of corrected() as <sup> and <sub>; a space before a superscript goes (G19 detail 8)."""
    text = re.sub(r"\s+" + SUP0, SUP0, text)
    text = re.sub(SUP1 + r"\s+(?=[.,;:!?)\]])", SUP1, text)   # "question¹ ." prints as "question¹."
    if plain:
        return re.sub("[\ue000-\ue003]", "", text)
    return text.replace(SUP0, "<sup>").replace(SUP1, "</sup>").replace(SUB0, "<sub>").replace(SUB1, "</sub>")


CLITICS = {"il", "elle", "ils", "elles", "on", "je", "tu", "nous", "vous", "ci", "là", "même", "mêmes", "être", "dessus",
           "dessous", "t", "y", "en", "le", "la", "les", "moi", "toi", "lui", "leur", "eux"}
_VOCAB: dict | None = None


def hyphen_vocab() -> dict:
    """Word counts inside printed lines of the development atoms (no test document, process rule 6): the
    joined form and the hyphenated form of each word pair decide the default for a line-end hyphen."""
    global _VOCAB
    if _VOCAB is not None:
        return _VOCAB
    files = sorted((ROOT / "daten/iso/atome").glob("*.json"))
    key = f"v2:{len(files)}:{sum(f.stat().st_size for f in files)}"
    cache = GOLD / "cache" / "hyphen_vocab.json"
    if cache.exists():
        c = json.loads(cache.read_text(encoding="utf-8"))
        if c.get("key") == key:
            _VOCAB = c["counts"]
            return _VOCAB
    counts: dict[str, int] = {}
    word = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
    for f in files:
        for a in json.loads(f.read_text(encoding="utf-8")).get("atome") or []:
            t = (a.get("text") or "").rstrip()
            t = re.sub(r"[^\W\d_]+-$", "", t)   # the word split at the line end does not count
            for w in word.findall(t):
                w = w.lower()
                counts[w] = counts.get(w, 0) + 1
                parts = w.split("-")
                if len(parts) > 2:
                    for k in range(len(parts) - 1):
                        pair = f"{parts[k]}-{parts[k + 1]}"
                        counts[pair] = counts.get(pair, 0) + 1
    _VOCAB = counts
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"key": key, "counts": counts}, ensure_ascii=False), encoding="utf-8")
    return counts


def default_keep_hyphen(left: str, right: str) -> bool:
    """Default for a line-end hyphen between the word part `left` and the word `right` (G19 details 11-12):
    a digit on one side keeps it; else the form that the corpus prints inside a line wins; else a clitic or
    compound part after it keeps it, a word in lower case or a word split in capitals removes it, all other
    cases keep it."""
    if not left or left[-1:].isdigit() or right[:1].isdigit():
        return True
    v = hyphen_vocab()
    joined, hyph = v.get((left + right).lower(), 0), v.get(f"{left}-{right}".lower(), 0)
    if hyph != joined:
        return hyph > joined
    if right.lower() in CLITICS:
        return True
    if right[:1].islower():
        return False
    return not (left.isupper() and right.isupper() and len(left) > 1)


def join_atoms(xs: list[tuple[str, dict]], tf: dict, changes: dict) -> str:
    """Join the atoms of one element (G19 details 11 and 12). Parts of one printed line keep their spacing:
    no space when the character ranges touch. A line break becomes one space, except inside a URL. A
    line-end hyphen is a decision: the review keeps or removes it, else default_keep_hyphen decides; a
    hyphen before a conjunction ("Bundes- und") stays with its space. Each hyphen decision is recorded."""
    keep, drop = set(tf.get("keep_hyphen") or []), set(tf.get("remove_hyphen") or [])
    out, prev = "", None
    for raw, x in xs:
        t = raw.strip()
        if not t:
            continue
        if prev is None:
            out, prev = t, (raw, x)
            continue
        praw, px = prev
        if x["block"] == px["block"] and x["zeile"] == px["zeile"] and x["seite"] == px["seite"]:
            gap = x["zeichen"][0] > px["zeichen"][1] or praw[-1:].isspace() or raw[:1].isspace()
            out += (" " if gap else "") + t
            prev = (raw, x)
            continue
        changes["joined_line_breaks"] += 1
        orig = (px.get("text") or "").rstrip()
        m, nxt = HYPHEN.search(out), re.match(r"\w+", t)
        url = re.search(r"(?:https?://|www\.)\S*$", out)
        if url and not re.search(r"[.,;:!?)]$", out) and (out.endswith("-") or re.fullmatch(r"\S*[/=?&_]\S*", t.split(" ")[0])):
            if out.endswith("-") and HYPHEN.search(orig):
                changes["kept_hyphens"].append(px["zeichen"][0] + len(orig) - 1)
            out += t   # a URL that goes on in the next line
        elif m and nxt and HYPHEN.search(orig):
            pos = px["zeichen"][0] + len(orig) - 1
            word = nxt.group(0)
            left = (re.search(r"(\w+)[-­‐]$", out) or [None, ""])[1]
            if word.lower() in CONJ and px["id"] not in drop:
                out += " " + t
                changes["kept_hyphens"].append(pos)
            elif px["id"] in drop or (px["id"] not in keep and not default_keep_hyphen(left, word)):
                out = out[:-1] + t
                changes["hyphens_removed"].append(pos)
            else:
                out += t
                changes["kept_hyphens"].append(pos)
        else:
            out += " " + t
        prev = (raw, x)
    return out


def links(t: str) -> str:
    """Escape the text and write each printed URL as <a href> with the same text (G19 detail 8)."""
    out, pos = [], 0
    for m in URL.finditer(t):
        u = m.group(0)
        href = u if u.lower().startswith("http") else "http://" + u
        out += [html.escape(t[pos:m.start()], quote=False), f'<a href="{html.escape(href)}">{html.escape(u, quote=False)}</a>']
        pos = m.end()
    return "".join(out) + html.escape(t[pos:], quote=False)


def marker(text: str, x: dict, lst: dict | None, changes: dict, ocr: list[dict] = ()) -> tuple[str, str, int | None, str]:
    """Remove the printed list marker (G19 detail 6). Returns the text, the list kind, the number and the
    type (RT92:22: "", "a", "A", "i", "I"). A single letter is a marker only when it starts a letter list
    (a, A) or continues the list before it; else it stays text (an initial such as "P. Remund")."""
    m = MARKER.match(text)
    if not m:
        return text, "ul", None, ""
    mk = m.group(2) or ""
    kind, n, typ = "ul", None, ""
    if mk.isdigit():
        kind, n = "ol", int(mk)
    elif mk:
        def cont(t, k):
            return lst is not None and lst["type"] == t and lst["n"] is not None and k == lst["n"] + 1
        letter = ord(mk.lower()) - 96 if len(mk) == 1 else None
        rtyp = "I" if mk.isupper() else "i"
        ltyp = "A" if mk.isupper() else "a"
        if letter and cont(ltyp, letter):
            kind, n, typ = "ol", letter, ltyp
        elif ROMAN.match(mk) and (cont(rtyp, roman(mk)) or mk in ("i", "I") or (len(mk) > 1 and roman(mk) == 1)):
            kind, n, typ = "ol", roman(mk), rtyp
        elif letter == 1:
            kind, n, typ = "ol", 1, ltyp
        else:
            return text, "ul", None, ""   # not a marker
    raw = x.get("text") or ""
    mo = MARKER.match(raw)
    if mo:   # the raw marker; a G20 or G20a correction can change its characters (for example - to –)
        a0, a1 = mo.start(1), mo.end()
    else:    # an OCR correction makes the marker: the range of the corrections at the start of the atom
        cs = [c for c in ocr if c["atom_id"] == x["id"] and c["range_start"] - x["zeichen"][0] <= len(raw) - len(raw.lstrip()) + 1]
        if not cs:
            raise SystemExit(f"atom {x['id']}: list marker without a raw marker or a correction")
        a0 = min(c["range_start"] for c in cs) - x["zeichen"][0]
        a1 = max(c["range_end"] for c in cs) - x["zeichen"][0]
        a1 += len(raw[a1:]) - len(raw[a1:].lstrip())
    changes["list_markers_removed"].append({"range_start": x["zeichen"][0] + a0, "range_end": x["zeichen"][0] + a1})
    return text[m.end():], kind, n, typ


def applicable(tf: dict, ids: list[str], by_id: dict) -> dict:
    """The text-form decisions for atoms of the extent. Decisions for other atoms rest in evidence.yaml and
    apply again when the atoms come back into the extent (the review tool keeps them)."""
    inside = set(ids)
    pos = set()
    for a in ids:
        z = by_id[a]["zeichen"]
        pos.update(range(z[0], z[1]))
    out = dict(tf)
    for k in ("keep_hyphen", "remove_hyphen", "paragraph_starts", "continues"):
        out[k] = [a for a in tf.get(k) or [] if a in inside]
    for k in ("forms", "heading_ranks", "empty_cells"):
        out[k] = {a: v for a, v in (tf.get(k) or {}).items() if a in inside}
    out["ocr_corrections"] = [c for c in tf.get("ocr_corrections") or [] if c["atom_id"] in inside]
    for k in ("superscripts", "subscripts"):
        out[k] = [r for r in tf.get(k) or [] if r["range_start"] in pos]
    return out


def resting(tf: dict, ids: list[str], by_id: dict) -> int:
    """Number of text-form decisions for atoms outside the extent."""
    a = applicable(tf, ids, by_id)
    n = 0
    for k, v in tf.items():
        if isinstance(v, (list, dict)):
            n += len(v) - len(a.get(k) or [])
    return n


def default_form(label: str) -> str:
    return ("heading_2" if label in ("section_header", "title") else "list_item" if label == "list_item"
            else "table_row" if label == "table" else "paragraph")


def richtext(doc_id: str, ids: list[str], plain: bool, tf: dict | None = None) -> tuple[str, dict]:
    """The wording of the atoms in the form of G19 and the record of each change (GoldTextChanges)."""
    by_id = {a["id"]: a for a in atoms(doc_id)}
    tf = applicable(tf or {}, ids, by_id)
    fixed = v4.fixed_answers(doc_id)
    changes = {"hyphens_removed": [], "kept_hyphens": [], "list_markers_removed": [], "empty_atoms": [], "nfc_changed": False,
               "removed_furniture_atoms": [], "joined_line_breaks": 0, "ocr_corrections": [],
               "paragraph_starts": [], "continued_elements": [], "form_overrides": [], "heading_ranks": [], "empty_cells": [],
               "text_layer_corrections": []}
    ocr = tf.get("ocr_corrections") or []
    starts, cont = set(tf.get("paragraph_starts") or []), set(tf.get("continues") or [])
    forms, ranks = dict(tf.get("forms") or {}), dict(tf.get("heading_ranks") or {})
    empty = {a: sorted(int(i) for i in v) for a, v in (tf.get("empty_cells") or {}).items()}
    body = []
    for a in ids:
        x = by_id[a]
        if fixed.get(a) == "furniture":
            changes["removed_furniture_atoms"].append(a)
        elif fixed.get(a) == "none" or x.get("label") == "picture":
            changes["empty_atoms"].append(a)   # a picture, logo or stamp: not text (G19 details 8 and 14)
        elif not (x.get("text") or "").strip():
            changes["empty_atoms"].append(a)
        else:
            body.append((corrected(x, tf), x))
    changes["ocr_corrections"] = [{k: c[k] for k in ("atom_id", "range_start", "range_end", "ocr_text", "printed_text",
                                                     "reviewer_confirmed") if k in c}
                                  for c in sorted(ocr, key=lambda c: c["range_start"])]
    changes["text_layer_corrections"] = [c for _, x in body for c in text_layer_corrections(x)]
    for key in ("superscripts", "subscripts"):
        changes[key] = [{"range_start": r["range_start"], "range_end": r["range_end"]}
                        for r in sorted(tf.get(key) or [], key=lambda r: r["range_start"])]
    elements = []   # [form, [(text, atom)], starts a new Docling block]
    for t, x in body:
        default = default_form(x.get("label") or "text")
        new_block = not elements or elements[-1][1][-1][1]["block"] != x["block"]
        if new_block and x["id"] in cont and elements:
            changes["continued_elements"].append(x["id"])
            form = forms.get(x["id"], default)
            if form in ("table_row", "table_head_row") and elements[-1][0] in ("table_row", "table_head_row"):
                if x["id"] in forms:   # the table goes on with a new row
                    changes["form_overrides"].append({"atom_id": x["id"], "element_form": form})
                elements.append([form, [(t, x)], False])
            else:                       # the paragraph or list item goes on after the page break
                elements[-1][1].append((t, x))
            continue
        if new_block or x["id"] in starts or x["id"] in forms or default == "table_row":
            if not new_block and x["id"] in starts:
                changes["paragraph_starts"].append(x["id"])
            form = forms.get(x["id"], default)
            if x["id"] in forms:
                changes["form_overrides"].append({"atom_id": x["id"], "element_form": form})
            elements.append([form, [(t, x)], new_block])
        else:
            elements[-1][1].append((t, x))
    if plain:
        text = " ".join(join_atoms(xs, tf, changes) for _, xs, _ in elements)
        text = re.sub(r"\s+", " ", text).strip()
    else:
        parts, lst, table = [], None, None   # lst: {"kind", "type", "n"}
        def close_list():
            nonlocal lst
            if lst:
                parts.append(f"</{lst['kind']}>")
                lst = None
        def close_table():
            nonlocal table
            if table:
                head = "".join(r for h, r in table if h)
                body_ = "".join(r for h, r in table if not h)
                parts.append("<table>" + (f"<thead>{head}</thead>" if head else "") + f"<tbody>{body_}</tbody></table>")
                table = None
        for form, xs, new_block in elements:
            if form not in ("table_row", "table_head_row"):
                close_table()
            if form != "list_item":
                close_list()
            if form == "list_item":
                first, x0 = xs[0]
                rest, kind, n, typ = marker(first, x0, lst, changes, ocr)
                item = join_atoms([(rest, x0)] + xs[1:], tf, changes)
                restart = (not lst or lst["kind"] != kind or lst["type"] != typ
                           or (kind == "ol" and (n is None or lst["n"] is None or n != lst["n"] + 1)))
                if restart:
                    close_list()
                    attrs = (f' type="{typ}"' if typ else "") + (f' start="{n}"' if kind == "ol" and n not in (None, 1) else "")
                    parts.append(f"<{kind}{attrs}>")
                    lst = {"kind": kind, "type": typ, "n": n}
                lst["n"] = n
                parts.append(f"<li>{links(item)}</li>")
            elif form in ("table_row", "table_head_row"):
                if table is not None and new_block:
                    close_table()
                cells = [c.strip() for c in "\t".join(t for t, _ in xs).split("\t")]
                for k in empty.get(xs[0][1]["id"], []):   # a printed empty cell (G19 detail 7)
                    if k > len(cells):
                        raise SystemExit(f"{doc_id}: empty cell index {k} of atom {xs[0][1]['id']} is after the last cell")
                    cells.insert(k, "")
                    changes["empty_cells"].append({"atom_id": xs[0][1]["id"], "cell_index": k})
                row = "<tr>" + "".join(f"<td>{links(c)}</td>" for c in cells) + "</tr>"   # RT92:19 has no <th>
                table = (table or []) + [(form == "table_head_row", row)]
            else:
                tag = FORM_TAG[form]
                if xs[0][1]["id"] in ranks and tag != "p":
                    changes["heading_ranks"].append({"atom_id": xs[0][1]["id"], "printed_rank": int(ranks[xs[0][1]["id"]]),
                                                     "html_rank": tag})
                parts.append(f"<{tag}>{links(join_atoms(xs, tf, changes))}</{tag}>")
        close_table()
        close_list()
        text = "".join(parts)
    changes["_elements"] = [{"form": f, "default": default_form(xs[0][1].get("label") or "text"), "atoms": [x["id"] for _, x in xs]}
                            for f, xs, _ in elements]
    text = scripts(text, plain)
    nfc = unicodedata.normalize("NFC", text)
    changes["nfc_changed"] = nfc != text
    return nfc, changes


def signature_text(t: str) -> str:
    """The letters of a text without markup and white space (E19 check)."""
    return unicodedata.normalize("NFC", re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", t))))


def signature_atoms(doc_id: str, ids: list[str], ch: dict) -> str:
    """The letters of the atoms after the recorded changes only: OCR corrections, removed hyphens, removed
    list markers (E19 check). Markup, spaces and line breaks do not count."""
    by_id = {a["id"]: a for a in atoms(doc_id)}
    drop = set(ch.get("hyphens_removed") or [])
    for m in ch.get("list_markers_removed") or []:
        drop |= set(range(m["range_start"], m["range_end"]))
    repl = {c["range_start"]: c for c in (ch.get("ocr_corrections") or []) + (ch.get("text_layer_corrections") or [])}
    empty = set(ch.get("empty_atoms") or [])
    out = []
    for a in ids:
        if a in empty:
            continue
        x = by_id[a]
        t, z0, i = x.get("text") or "", x["zeichen"][0], 0
        while i < len(t):
            p = z0 + i
            if p in repl:
                c = repl[p]
                if not all(q in drop for q in range(c["range_start"], c["range_end"])):
                    out.append(c["printed_text"])
                i += c["range_end"] - c["range_start"]
                continue
            if p not in drop:
                out.append(t[i])
            i += 1
    return unicodedata.normalize("NFC", re.sub(r"\s+", "", "".join(out)))


ORDINAL = re.compile(r"(?<![\d.,])\d{1,3} ?(er|re|e|ème|ères|ers|nd|nde)\b(?= \w)")


def textform_view(d: str, tb: dict) -> dict:
    """The text-form view of one text block of evidence.yaml: the elements with their form, every line-end
    hyphen with its decision, the corrections, and candidates for decisions (paragraph starts from the
    geometry of the text layer, continuations after a page break, superscript ordinals)."""
    by_id = {a["id"]: a for a in atoms(d)}
    ids = ranges(d, tb["atoms"], keep_order=True)
    tf = text_form(tb)
    plain = tb["slot"] == "Affair.title"
    text, ch = richtext(d, ids, plain, tf)
    decided = set(tf.get("keep_hyphen") or []) | set(tf.get("remove_hyphen") or [])
    hyphens = []
    for k, kept in (("hyphens_removed", False), ("kept_hyphens", True)):
        for pos in ch.get(k) or []:
            a = next(a for a in ids if by_id[a]["zeichen"][0] <= pos < by_id[a]["zeichen"][1])
            nxt = next((b for b in ids[ids.index(a) + 1:] if not fixed_skip(d, b)), None)
            hyphens.append({"atom": a, "pos": pos, "kept": kept, "decided": a in decided,
                            "left": (by_id[a]["text"] or "").rstrip()[-25:], "right": (by_id[nxt]["text"] or "")[:20] if nxt else ""})
    hyphens.sort(key=lambda h: h["pos"])
    cand = []
    prev = None
    for a in ([] if plain else ids):
        x = by_id[a]
        if prev is not None and x["block"] == prev["block"] and geometric_gap(prev, x) and a not in (tf.get("paragraph_starts") or []):
            cand.append({"kind": "paragraph_start", "atom": a, "info": f"blank space {geometric_gap(prev, x):.2f} line heights"})
        if (prev is not None and x["block"] != prev["block"] and x["seite"] != prev["seite"] and x.get("label") == prev.get("label")
                and not re.search(r"[.!?:;»«\"]\s*$", prev.get("text") or "") and re.match(r"\s*[^\W\d_]", x.get("text") or "")
                and (x.get("text") or "").lstrip()[:1].islower() and a not in (tf.get("continues") or [])):
            cand.append({"kind": "continues", "atom": a, "info": f"page {x['seite']}: {(prev['text'] or '')[-30:]!r} | {(x['text'] or '')[:30]!r}"})
        for m in ORDINAL.finditer(x.get("text") or ""):
            z = x["zeichen"][0] + m.start(1)
            if not any(r["range_start"] == z for r in tf.get("superscripts") or []):
                cand.append({"kind": "superscript", "atom": a, "range_start": z, "range_end": z + len(m.group(1)),
                             "info": (x["text"] or "")[max(0, m.start() - 12):m.end() + 8]})
        if not fixed_skip(d, a):
            prev = x
    elements = [{"form": e["form"], "default": e["default"], "atoms": e["atoms"], "first": e["atoms"][0],
                 "preview": " ".join((by_id[a]["text"] or "") for a in e["atoms"])[:90]} for e in ch.get("_elements") or []]
    return {"text": text, "elements": elements, "hyphens": hyphens, "candidates": cand, "decisions": tf,
            "resting": resting(tf, ids, by_id),
            "text_layer_corrections": ch.get("text_layer_corrections") or [], "plain": plain}


def cmd_textform(args) -> None:
    """Print the text-form view of each text block (for the proposal agents)."""
    d = args.doc
    ev = yaml.safe_load((rec_dir(d, args.stage) / "evidence.yaml").read_text(encoding="utf-8"))
    for i, tb in enumerate(ev.get("text_blocks") or []):
        v = textform_view(d, tb)
        ids = ranges(d, tb["atoms"], keep_order=True)
        print(f"== TB{i + 1} {tb['slot']} {tb.get('text_type') or ''} atoms {ids[0]}..{ids[-1]}")
        for e in v["elements"]:
            print(f"   <{e['form']}> {e['first']}: {e['preview']}")
        for h in v["hyphens"]:
            print(f"   hyphen {'kept' if h['kept'] else 'removed'} ({'decided' if h['decided'] else 'default'}) {h['atom']}: "
                  f"...{h['left']!r} + {h['right']!r}")
        for c in v["text_layer_corrections"]:
            print(f"   text layer typography {c['atom_id']} {c['range_start']}: {c['ocr_text']!r} -> {c['printed_text']!r}")
        for c in v["candidates"]:
            extra = f" range_start {c['range_start']}, range_end {c['range_end']}" if "range_start" in c else ""
            print(f"   candidate {c['kind']} {c['atom']}{extra}: {c['info']}")


def geometric_gap(a: dict, b: dict) -> float:
    """The blank space between two lines of the text layer in line heights (0 when unknown)."""
    if a["seite"] != b["seite"] or a.get("zeilenrahmen_quelle") != "text_layer" or b.get("zeilenrahmen_quelle") != "text_layer":
        return 0.0
    ra, rb = a.get("zeilenrahmen"), b.get("zeilenrahmen")
    if not ra or not rb or a.get("zeile") == b.get("zeile"):
        return 0.0
    h = ra[3] - ra[1]
    g = (rb[1] - ra[3]) / h if h > 0 else 0.0
    return g if g >= 0.6 else 0.0


def fixed_skip(d: str, a: str) -> bool:
    return v4.fixed_answers(d).get(a) in ("furniture", "none")


# ---------------------------------------------------------------- paths in the instance

TOKEN = re.compile(r"([A-Za-z_]+)(?:\[(\d+)\])?")


def get_path(obj, path: str):
    cur = obj
    for name, idx in TOKEN.findall(path):
        if not isinstance(cur, dict) or name not in cur:
            raise KeyError(path)
        cur = cur[name]
        if idx:
            cur = cur[int(idx)]
    return cur


def set_path(obj, path: str, value) -> None:
    toks = TOKEN.findall(path)
    cur = obj
    for i, (name, idx) in enumerate(toks):
        last = i == len(toks) - 1
        if last and not idx:
            cur[name] = value
            return
        cur = cur[name]
        if idx:
            if last:
                cur[int(idx)] = value
                return
            cur = cur[int(idx)]


def leaves(obj, prefix="", skip=frozenset()):
    """Leaf values of the instance as (path, value). The text of a TextBlock that a text block of the
    record fills from atoms (paths in skip) is not a leaf here: its provenance is the text block."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            if p in skip:
                continue
            yield from leaves(v, p, skip)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]", skip)
    else:
        yield prefix, obj


# ---------------------------------------------------------------- build

def atom_evidence(doc_id: str, a: str, match: str | None = None) -> dict:
    x = {y["id"]: y for y in atoms(doc_id)}[a]
    b = x.get("zeilenrahmen") or x.get("rahmen") or [0, 0, 0, 0]
    ev = {"atom_id": a, "page_number": x["seite"],
          "bbox": {"bbox_left": b[0], "bbox_top": b[1], "bbox_right": b[2], "bbox_bottom": b[3]},
          "char_start": x["zeichen"][0], "char_end": x["zeichen"][1],
          "from_ocr": any("OCR" in h for h in (x.get("hinweise") or []))}
    if match is not None:
        t = x.get("text") or ""
        k = t.find(match)
        if k < 0:
            raise SystemExit(f"{doc_id}: {match!r} is not in the wording of atom {a}")
        ev.update({"matched_text": match, "match_start": k, "match_end": k + len(match)})
    return ev


URI_SAFE = ":/?#[]@!$&'()*+,;=-._~"   # RFC 3986: reserved characters and unreserved marks (letters and digits stay)


def as_uri(s: str | None) -> str | None:
    """An export URL for a slot with the range uri: percent-encode each character that RFC 3986 does not allow
    (for example a space or a letter that is not ASCII). Reserved characters and existing percent escapes stay."""
    if not isinstance(s, str):
        return s
    return "".join(p if re.fullmatch(r"%[0-9A-Fa-f]{2}", p) else quote(p, safe=URI_SAFE)
                   for p in re.split(r"(%[0-9A-Fa-f]{2})", s))


def cmd_build(args) -> None:
    d = args.doc
    folder = rec_dir(d, args.stage)
    draft = yaml.safe_load((folder / "instance.draft.yaml").read_text(encoding="utf-8"))
    ev = yaml.safe_load((folder / "evidence.yaml").read_text(encoding="utf-8"))
    ctx_p = base_dir(d) / "context" / f"{d}.json"
    ctx = json.loads(ctx_p.read_text(encoding="utf-8")) if ctx_p.exists() else {"doc": {}}
    inst = json.loads(json.dumps(draft))
    proposed = {"review_status": "proposed"}

    def rev(entry: dict) -> dict:
        """The review of an entry (written by the review tool), else the status proposed."""
        r = entry.get("review")
        if not r:
            return dict(proposed)
        out = {"review_status": r["status"]}
        if r["status"] != "proposed":
            out["reviewer"] = r.get("reviewer", "Jonathan")
        for k, t in (("datetime", "datetime_reviewed"), ("proposal_value", "proposal_value"), ("proposal_evidence", "proposal_evidence"),
                     ("note", "review_note")):
            if r.get(k) not in (None, ""):
                out[t] = r[k] if isinstance(r[k], str) else json.dumps(r[k], ensure_ascii=False)
        return out
    used_atoms: dict[str, str] = {}
    pdf = pdf_path(d)
    srcdoc_iri = f"{MINT}{hashlib.sha256(pdf.read_bytes()).hexdigest()[:32]}"
    blocks = []
    for i, tb in enumerate(ev.get("text_blocks") or []):
        ids = ranges(d, tb["atoms"], keep_order=True)
        for a in ids:
            if a in used_atoms:
                raise SystemExit(f"{d}: atom {a} in two text blocks ({used_atoms[a]}, {i})")
            used_atoms[a] = str(i)
        slot = tb["slot"]
        plain = slot == "Affair.title"
        text, ch = richtext(d, ids, plain, text_form(tb))
        if (slot, tb.get("text_type")) not in ANSWER:
            raise SystemExit(f"{d}: slot {slot} with text_type {tb.get('text_type')} is not permitted (G23)")
        status = tb.get("mapping_status", "in_ech_instance")
        if plain and status == "in_ech_instance":
            raise SystemExit(f"{d}: text block {i + 1}: an Affair.title text block is profile_only. The Affair.title value is "
                             f"the registry title of the export, with the title atoms as its PDF evidence (G24, J4)")
        if status == "in_ech_instance":
            if tb["path"] in [b["instance_path"] for b in blocks if b["mapping_status"] == "in_ech_instance"]:
                raise SystemExit(f"{d}: two text blocks on the instance path {tb['path']}")
            obj = get_path(inst, tb["path"])
            obj["text"] = text
        block = {"local_id": f"TB{i + 1}", "global_uri": f"{MINT}{hashlib.sha256(f'{d}:TB{i + 1}'.encode()).hexdigest()[:32]}",
                 "instance_path": tb.get("path") or "", "ech_slot": slot, "mapping_status": status,
                 "text_content": text, "source_document": srcdoc_iri,
                 "atom_evidence": [atom_evidence(d, a) for a in ids if a not in ch["removed_furniture_atoms"]],
                 "gold_text_changes": {k: v for k, v in ch.items() if not k.startswith("_") and v not in ([], None)},
                 "rule_ids": tb.get("rules") or [], "review": rev(tb)}
        block["gold_text_changes"]["nfc_changed"] = ch["nfc_changed"]
        block["gold_text_changes"]["joined_line_breaks"] = ch["joined_line_breaks"]
        for k in ("ech_text_type", "text_language", "not_mapped_reason"):
            src = {"ech_text_type": "text_type", "text_language": "language"}.get(k, k)
            if tb.get(src):
                block[k] = tb[src]
        blocks.append(block)
    values = []
    live = [v["path"] for v in ev.get("values") or [] if not v.get("removed")]
    dup = sorted({x for x in live if live.count(x) > 1})
    if dup:
        raise SystemExit(f"{d}: two evidence entries for the same path: {dup}")
    by_path = {v["path"]: v for v in ev.get("values") or [] if not v.get("removed")}
    missing = []
    skip = frozenset(f"{b['instance_path']}.text" for b in blocks if b["mapping_status"] == "in_ech_instance")
    for path, val in leaves(inst, "", skip):
        e = by_path.get(path)
        if e is None:
            missing.append(path)
            continue
        gv = {"instance_path": path, "recorded_value": str(val), "gold_derivation": e["derivation"],
              "rule_ids": e.get("rules") or [], "review": rev(e)}
        if e.get("ech_slot"):
            gv["ech_slot"] = e["ech_slot"]
        if e.get("export"):
            x = e["export"]
            me = {"export_file": x["file"], "record_type": x.get("record_type", x["file"]), "record_id": str(x["id"]),
                  "field_name": x["field"], "source_value": str(x.get("value", ""))}
            if ctx.get("export_retrieved"):
                me["datetime_export_retrieved"] = ctx["export_retrieved"]
            gv["metadata_evidence"] = [me]
        for x in e.get("also_export") or []:   # further export records that give or confirm the value
            me = {"export_file": x["file"], "record_type": x.get("record_type", x["file"]), "record_id": str(x["id"]),
                  "field_name": x["field"], "source_value": str(x.get("value", ""))}
            if ctx.get("export_retrieved"):
                me["datetime_export_retrieved"] = ctx["export_retrieved"]
            gv.setdefault("metadata_evidence", []).append(me)
        if e.get("atoms"):
            gv["pdf_evidence"] = [atom_evidence(d, a["atom"], a.get("match")) if isinstance(a, dict) else atom_evidence(d, a)
                                  for a in e["atoms"]]
        if e.get("consistency"):
            gv["pdf_consistency"] = e["consistency"]
        if e.get("derived_from"):
            gv["derived_from"] = e["derived_from"]
        alts = []
        for a in e.get("alternatives") or []:
            if isinstance(a, dict):
                alts.append({"alternative_value": str(a["value"]), **({"alternative_source": a["source"]} if a.get("source") else {}),
                             **({"alternative_note": a["note"]} if a.get("note") else {})})
            else:
                alts.append({"alternative_value": str(a)})
        if alts:
            gv["alternatives"] = alts
        values.append(gv)
    if missing:
        raise SystemExit(f"{d}: leaf values without evidence: {missing[:10]} ({len(missing)})")
    not_mapped = []
    for e in ev.get("values") or []:
        if e.get("removed"):
            r = rev(e)
            not_mapped.append({"not_mapped_item": f"removed by the review: {e['path']}", "not_mapped_reason": "value of the proposal removed",
                               "candidate_value": str((e.get("review") or {}).get("proposal_value", "")), "review": r,
                               "rule_ids": e.get("rules") or []})
    for n in ev.get("not_mapped") or []:
        nm = {"not_mapped_item": n["item"], "not_mapped_reason": n.get("reason", ""), "review": rev(n),
              "rule_ids": n.get("rules") or []}
        for k in ("candidate_value", "candidate_source", "actor_class", "unreachable_class"):
            if n.get(k):
                nm[k] = n[k]
        if n.get("atoms"):
            nm["pdf_evidence"] = [atom_evidence(d, a) for a in (ranges(d, n["atoms"]) if isinstance(n["atoms"], (str, list)) else [])]
        not_mapped.append(nm)
    units = []
    for u in ev.get("units") or []:
        tbid = {b["instance_path"]: b["local_id"] for b in blocks if b["instance_path"]}.get(u.get("text_block"), u.get("text_block", ""))
        if tbid not in {b["local_id"] for b in blocks}:
            raise SystemExit(f"{d}: unit {u['unit_id']}: text_block {u.get('text_block')!r} names no text block")
        un = {"unit_id": u["unit_id"], "unit_role": u["role"], "text_block": tbid,
              "atom_evidence": [atom_evidence(d, a) for a in ranges(d, u["atoms"])], "review": rev(u)}
        if u.get("printed_numbers"):
            un["printed_numbers"] = [str(x) for x in (u["printed_numbers"] if isinstance(u["printed_numbers"], list) else [u["printed_numbers"]])]
        if u.get("answers_unit"):
            un["answers_unit"] = u["answers_unit"] if isinstance(u["answers_unit"], list) else [u["answers_unit"]]
        units.append(un)
    doc = ctx.get("doc") or {}
    af = json.loads(iso_path("atome", d).read_text(encoding="utf-8"))
    fp = hashlib.sha256(json.dumps([[a["id"], a["zeichen"]] for a in af["atome"]], separators=(",", ":")).encode("utf-8")).hexdigest()
    srcdoc = {"global_uri": srcdoc_iri, "local_id": d,
              "file_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "page_count": len(json.loads(iso_path("docling", d).read_text())["seiten"]),
              "docling_json_sha256": af.get("quelle_sha256") or "",   # the Docling decomposition of the atoms
              "atom_fingerprint": fp}                                  # IDs and character ranges (m03_isolierung_taxonomie)
    if doc.get("url_oparl"):
        srcdoc["manifestation_url"] = as_uri(doc["url_oparl"])
    if (doc.get("url") or "").startswith("http"):
        srcdoc["publisher_url"] = as_uri(doc["url"])
    stage = getattr(args, "record_stage", None) or args.stage
    prov = {"global_uri": f"{MINT}record-{d}-{stage}", "local_id": f"{d}/{stage}",
            "describes_delivery": inst.get("global_uri", f"{MINT}container-{d}"), "ech_schema_version": "I95 3cab44d",
            "review_run": {"proposal_source": ev.get("proposal_source", ""),
                           "tool_version": "; ".join(x for x in (VERSION, (ev.get("review_run") or {}).get("tool_version")) if x),
                           "guideline_file": str(GUIDE.relative_to(ROOT)),
                           "guideline_sha256": hashlib.sha256(GUIDE.read_bytes()).hexdigest(),
                           "fields_sha256": hashlib.sha256(FIELDS.read_bytes()).hexdigest(),
                           "e20_version": next((ln for ln in E20_FILE.read_text().splitlines() if ln.startswith("Version ")), "")[:80],
                           "e20_sha256": hashlib.sha256(E20_FILE.read_bytes()).hexdigest(),
                           "atom_version": f"{af.get('version', '')} {af.get('erzeugt_utc', '')}".strip(),
                           **{k: v for k, v in (ev.get("review_run") or {}).items()
                              if k in ("reviewer", "datetime_started", "datetime_finished", "freeze_sha256", "reopened", "i95_gaps")}},
            "source_documents": [srcdoc],
            "affair_scopes": [{"affair_iri": get_path(inst, s["affair_path"])["global_uri"], "affair_scope": s["scope"]}
                              for s in ev.get("affair_scopes") or []],
            "text_blocks": blocks, "values": values, "not_mapped": not_mapped, "units": units,
            "register": ev.get("register") or []}
    if "global_uri" not in inst:
        inst["global_uri"] = prov["describes_delivery"]
    (folder / "instance.yaml").write_text(yaml.safe_dump(inst, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    (folder / "provenance.yaml").write_text(yaml.safe_dump(prov, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    problems, _, _ = record_problems(d, folder)
    ch_all = [b["gold_text_changes"] for b in blocks]
    prov["verbatim_check"] = {
        "check_method": "letters of each text block against the letters of its atoms after the recorded changes "
                        "(E19), rebuild from the recorded text-form decisions (G19), copied values against the export",
        "text_blocks_checked": len(blocks),
        "characters_checked": sum(len(signature_text(b["text_content"])) for b in blocks),
        "hyphens_removed_count": sum(len(c.get("hyphens_removed") or []) for c in ch_all),
        "list_markers_removed_count": sum(len(c.get("list_markers_removed") or []) for c in ch_all),
        "metadata_values_checked": sum(1 for v in values if v["gold_derivation"] == "copied_from_metadata" and v.get("metadata_evidence")),
        "leaves_without_provenance": sum(1 for x in problems if x.startswith("leaf without provenance")),
        "check_passed": not any(("(E19)" in x or "(G19)" in x or x.startswith("leaf without provenance")
                                 or "copied_from_metadata" in x) for x in problems)}
    (folder / "provenance.yaml").write_text(yaml.safe_dump(prov, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    print(f"{d} {args.stage}: {len(blocks)} text blocks, {len(values)} values, {len(not_mapped)} not mapped, {len(units)} units")


# ---------------------------------------------------------------- validation and derivation

def linkml_validate(schema: Path, cls: str, data: Path) -> tuple[bool, str]:
    r = subprocess.run(["uv", "run", "--no-project", "--with", "linkml", "linkml-validate", "-s", str(schema), "-C", cls, str(data)],
                       capture_output=True, text=True, cwd=str(schema.parent))
    out = (r.stdout + r.stderr).strip()
    return r.returncode == 0 and "No issues found" in out, out[-1500:]


def derive(d: str, prov: dict) -> list[str]:
    ids = [a["id"] for a in atoms(d)]
    fixed = v4.fixed_answers(d)
    ans = {a: "none" for a in ids}
    for tb in prov.get("text_blocks") or []:
        key = (tb["ech_slot"], tb.get("ech_text_type"))
        for e in tb.get("atom_evidence") or []:
            ans[e["atom_id"]] = ANSWER[key]
        for a in (tb.get("gold_text_changes") or {}).get("removed_furniture_atoms") or []:
            ans[a] = "furniture"
    for a, x in fixed.items():
        ans[a] = x
    return [ans[a] for a in ids]


_SCHEMA: dict | None = None


def i95() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = yaml.safe_load(I95.read_text(encoding="utf-8"))
    return _SCHEMA


def class_of_path(path: str) -> str:
    """The I95 class of the object at a path of the instance (slot ranges, with the slot_usage of the class)."""
    sch = i95()
    classes = sch.get("classes") or {}
    cls = "Container"
    for name, _ in TOKEN.findall(path):
        rng = None
        c = cls
        while c and rng is None:
            rng = (((classes.get(c) or {}).get("slot_usage") or {}).get(name) or {}).get("range")
            c = (classes.get(c) or {}).get("is_a")
        rng = rng or ((sch.get("slots") or {}).get(name) or {}).get("range")
        if rng in classes:
            cls = rng
    return cls


def slot_range(cls: str, name: str) -> str | None:
    """The range of a slot in a class (slot_usage of the class and its parents first)."""
    sch = i95()
    classes = sch.get("classes") or {}
    c = cls
    while c:
        rng = (((classes.get(c) or {}).get("slot_usage") or {}).get(name) or {}).get("range")
        if rng:
            return rng
        c = (classes.get(c) or {}).get("is_a")
    return ((sch.get("slots") or {}).get(name) or {}).get("range")


def missing_required(inst: dict) -> list[str]:
    """Paths of required I95 slots without a value (a required slot can stay empty without a source, G5)."""
    sch = i95()
    classes = sch.get("classes") or {}
    out = []

    def req(cls):
        names, c, chain = set(), cls, []
        while c:
            chain.append(c)
            c = (classes.get(c) or {}).get("is_a")
        for c in reversed(chain):
            cd = classes.get(c) or {}
            for sl in cd.get("slots") or []:
                if ((sch.get("slots") or {}).get(sl) or {}).get("required"):
                    names.add(sl)
            for sl, su in (cd.get("slot_usage") or {}).items():
                if (su or {}).get("required"):
                    names.add(sl)
        return names

    def walk(obj, path):
        if isinstance(obj, dict):
            cls = class_of_path(path) if path else "Container"
            for sl in sorted(req(cls)):
                if obj.get(sl) in (None, "", [], {}):
                    out.append(f"{path}.{sl}" if path else sl)
            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
    walk(inst, "")
    return out


def ancestors(cls: str) -> list[str]:
    out, classes = [], i95().get("classes") or {}
    while cls:
        out.append(cls)
        cls = (classes.get(cls) or {}).get("is_a")
    return out


def record_problems(d: str, folder: Path) -> tuple[list[str], dict, dict]:
    """The checks of a built record without LinkML (used by validate and by the review tool)."""
    inst = yaml.safe_load((folder / "instance.yaml").read_text(encoding="utf-8"))
    prov = yaml.safe_load((folder / "provenance.yaml").read_text(encoding="utf-8"))
    problems = []
    order = {a["id"]: i for i, a in enumerate(atoms(d))}
    for tb in prov.get("text_blocks") or []:
        ch = tb.get("gold_text_changes") or {}
        ids = [e["atom_id"] for e in tb["atom_evidence"]]
        # E19: the letters of the text are the letters of the atoms after the recorded changes only
        if signature_text(tb["text_content"]) != signature_atoms(d, ids, ch):
            problems.append(f"{tb['local_id']}: the letters of the text differ from the atoms after the recorded changes (E19)")
        # G19: the recorded decisions give the same text form again (atom_evidence keeps the reading order;
        # removed furniture gives no text, so its place in the list does not change the text)
        furn = ch.get("removed_furniture_atoms") or []
        all_ids = sorted(ids + furn, key=order.get) if ids == sorted(ids, key=order.get) else ids + furn
        text, _ = richtext(d, all_ids, tb["ech_slot"] == "Affair.title", text_form_from_changes(d, ch))
        if text != tb["text_content"]:
            problems.append(f"{tb['local_id']}: the recorded text-form decisions do not give the same text (G19)")
        if tb["mapping_status"] == "in_ech_instance":
            try:
                obj = get_path(inst, tb["instance_path"])
            except (KeyError, IndexError, TypeError):
                problems.append(f"{tb['local_id']}: instance path {tb['instance_path']} not found")
                continue
            if obj.get("text") != tb["text_content"]:
                problems.append(f"{tb['local_id']}: instance text differs")
            # E20/G23: the slot of the instance and the text type give the E20 answer of the atoms
            parent, slot = tb["instance_path"].rsplit(".", 1)
            slot = TOKEN.findall(slot)[0][0]
            ecls, eslot = tb["ech_slot"].split(".")
            if slot != eslot or (ecls not in ancestors(class_of_path(parent)) and class_of_path(parent) not in ancestors(ecls)):
                problems.append(f"{tb['local_id']}: instance slot {class_of_path(parent)}.{slot} is not {tb['ech_slot']} (E20, G23)")
            if obj.get("text_type") != tb.get("ech_text_type"):
                problems.append(f"{tb['local_id']}: instance text_type {obj.get('text_type')} is not {tb.get('ech_text_type')} (G23)")
            if obj.get("text_language") != tb.get("text_language"):
                problems.append(f"{tb['local_id']}: instance text_language {obj.get('text_language')} is not {tb.get('text_language')}")
    have = {v["instance_path"] for v in prov.get("values") or []}
    skip = frozenset(f"{tb['instance_path']}.text" for tb in prov.get("text_blocks") or [] if tb["mapping_status"] == "in_ech_instance")
    lv = [p for p, _ in leaves(inst, "", skip)]
    problems += [f"leaf without provenance: {p}" for p in lv if p not in have]
    problems += [f"provenance without leaf: {p}" for p in have if p not in set(lv)]
    for v in prov.get("values") or []:
        if v["gold_derivation"] == "copied_from_metadata":
            src = [m.get("source_value") for m in v.get("metadata_evidence") or []]
            if src and v["recorded_value"] not in src:
                problems.append(f"{v['instance_path']}: copied_from_metadata, but the value is not the export value {src[0]!r}")
    shas = {sd.get("file_sha256") for sd in prov.get("source_documents") or []}
    for r in prov.get("register") or []:
        for h in re.findall(r"sha-?256\W{0,3}([0-9a-f]{64})", str(r.get("identifying_facts") or ""), re.I):
            if h not in shas:
                problems.append(f"register {r.get('minted_iri')}: SHA-256 {h[:12]}… is not the SHA-256 of the PDF (export docs.hash?)")
    units = {u["unit_id"] for u in prov.get("units") or []}
    problems += [f"unit {u['unit_id']}: answers unknown unit {a}" for u in prov.get("units") or []
                 for a in u.get("answers_unit") or [] if a not in units]
    tb_atoms = {t["local_id"]: {e["atom_id"] for e in t.get("atom_evidence") or []} for t in prov.get("text_blocks") or []}
    for u in prov.get("units") or []:
        out_ = [e["atom_id"] for e in u.get("atom_evidence") or [] if e["atom_id"] not in tb_atoms.get(u.get("text_block"), set())]
        if out_:
            problems.append(f"unit {u['unit_id']}: atoms outside its text block {u.get('text_block')}: {out_[:5]}")
    for tb in prov.get("text_blocks") or []:
        hr = (tb.get("gold_text_changes") or {}).get("heading_ranks") or []
        ranks = sorted({h["printed_rank"] for h in hr})
        want = {r: ("h2", "h3", "h4")[min(k, 2)] for k, r in enumerate(ranks)}
        for h in hr:
            if h["printed_rank"] < 1 or h["html_rank"] != want[h["printed_rank"]]:
                problems.append(f"{tb['local_id']}: printed heading rank {h['printed_rank']} of {h['atom_id']} gives {h['html_rank']}, "
                                f"not {want.get(h['printed_rank'])} (G19 detail 5)")
    # G52, A2, process rule 2.6: only Jonathan reviews; a correction keeps the proposal
    entries = ([("value " + v["instance_path"], v) for v in prov.get("values") or []]
               + [("text block " + t["local_id"], t) for t in prov.get("text_blocks") or []]
               + [("unit " + u["unit_id"], u) for u in prov.get("units") or []]
               + [("fact " + n["not_mapped_item"][:40], n) for n in prov.get("not_mapped") or []])
    for name, e in entries:
        r = e.get("review") or {}
        st = r.get("review_status")
        if st is None:
            problems.append(f"{name}: no review status (G52)")
        elif st != "proposed":
            if r.get("reviewer") != "Jonathan" or not r.get("datetime_reviewed"):
                problems.append(f"{name}: status {st} needs the reviewer Jonathan and the time (process rule 2.6)")
            if st == "corrected" and not (r.get("proposal_value") or r.get("proposal_evidence")):
                problems.append(f"{name}: status corrected without the proposal (A3)")
        elif r.get("reviewer"):
            problems.append(f"{name}: a proposal has no reviewer (A2)")
    return problems, inst, prov


def cmd_validate(args) -> None:
    d = args.doc
    folder = rec_dir(d, args.stage)
    ok1, out1 = linkml_validate(I95, "Container", folder / "instance.yaml")
    ok2, out2 = linkml_validate(PROFILE, "GoldRecord", folder / "provenance.yaml")
    problems, inst, prov = record_problems(d, folder)
    answers = derive(d, prov)
    out = folder / "e20_answers.json"
    v4.write(folder, d, answers, f"derived from {args.stage}", str(folder / "provenance.yaml"))
    (folder / f"{d}.json").replace(out)
    err = v4.validate4(out)
    res = {"doc": d, "stage": args.stage, "instance_I95": ok1, "provenance_profile": ok2, "problems": problems,
           "e20_validate4": err or "ok", "text_atoms": sum(a in v4.TEXT for a in answers)}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if not ok1:
        print("I95:", out1)
    if not ok2:
        print("profile:", out2)


def cmd_derive(args) -> None:
    folder = rec_dir(args.doc, args.stage)
    prov = yaml.safe_load((folder / "provenance.yaml").read_text(encoding="utf-8"))
    print(json.dumps(derive(args.doc, prov)))


def cmd_diff(args) -> None:
    d = args.doc
    A = yaml.safe_load((rec_dir(d, args.a) / "provenance.yaml").read_text(encoding="utf-8"))
    B = yaml.safe_load((rec_dir(d, args.b) / "provenance.yaml").read_text(encoding="utf-8"))
    va = {v["instance_path"]: v["recorded_value"] for v in A.get("values") or []}
    vb = {v["instance_path"]: v["recorded_value"] for v in B.get("values") or []}
    diffs = [{"path": p, args.a: va.get(p), args.b: vb.get(p)} for p in sorted(set(va) | set(vb)) if va.get(p) != vb.get(p)]
    ea, eb = derive(d, A), derive(d, B)
    ids = [a["id"] for a in atoms(d)]
    atom_diffs = [{"atom": a, args.a: x, args.b: y} for a, x, y in zip(ids, ea, eb) if x != y]
    print(json.dumps({"doc": d, "value_differences": diffs, "e20_atom_differences": atom_diffs}, ensure_ascii=False, indent=1))


def cmd_checkf(args) -> None:
    d = args.doc
    prov = yaml.safe_load((rec_dir(d, args.stage) / "provenance.yaml").read_text(encoding="utf-8"))
    dec = json.loads((GOLD / "pilot/decisions" / f"{d}.json").read_text(encoding="utf-8"))
    der = derive(d, prov)
    ids = [a["id"] for a in atoms(d)]
    diff = [(a, x, y) for a, x, y in zip(ids, dec["answers"], der) if x != y]
    print(json.dumps({"doc": d, "jonathan_block_decision_status": dec.get("status"), "differences": diff}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("context")
    p.add_argument("docs", nargs="+")
    for name in ("build", "validate", "derive", "checkf", "textform"):
        p = sub.add_parser(name)
        p.add_argument("doc")
        p.add_argument("--stage", required=True)
    p = sub.add_parser("diff")
    p.add_argument("doc")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    args = ap.parse_args()
    {"context": cmd_context, "build": cmd_build, "validate": cmd_validate, "derive": cmd_derive, "diff": cmd_diff,
     "checkf": cmd_checkf, "textform": cmd_textform}[args.cmd](args)


if __name__ == "__main__":
    main()

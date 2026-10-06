# SPDX-License-Identifier: Apache-2.0
"""Isolation at the level of E20, version 3: the fixed part of the roles (chapter 3, rules R1 to R5).

Version 4 (E20 version 4.1, m03_iso_jev4.fixed_answers) uses this procedure with another mapping:
R1, R4 and R5 give page furniture, R3 gives none, and footnotes (R2) are not fixed.

E20 version 3 defines some roles by a procedure. This script applies that procedure exactly. The
reference coders and every method use the same result. The other roles (text inside a picture,
print template of an attachment, caption outside a picture, misplaced head atoms) need a decision
by meaning; this script lists the atoms for some of them, but does not give their role.

Rules, in this order (the first rule that applies gives the role):
  R1 furniture  page number: the atom has the hint "Seitenzahl"; or its text is only a continuation
                mark ("./..", "…/…", "-/-") or only a page count ("2/3", "- 2/3 -"); or it is in the
                header or footer zone, not inside a picture, and its text is only a number of 1 to 3 digits
                ("5", "- 5 -").
  R2 insert     footnote text: Docling form "Fussnote".
  R3 insert     picture: the atom is a picture (Docling form "Bild"; the text is "(ohne Text)" or the
                OCR text of the picture block itself), or a fragment of a logo: an atom in the header
                or footer zone with not more than 2 characters and without a digit.
  R4 furniture  header or footer: the atom is in the header zone (or the footer zone), its text
                has 3 or more letters or 4 or more digits, and the same text occurs in the same zone
                of another page.
                The other copy must be at about the same height (top edges not more than 30 pt apart),
                or one of the two copies has the Docling form Kopfzeile or Fusszeile.
                Same text: first remove the page number parts ("Seite 2 von 5", "- 2 -", "2/5").
                Then the digits must be equal, and the letters (lower case, without all other
                characters) must be equal or have a similarity of 0.9 or more (OCR errors).
                This rule also applies to text inside a picture (a logo text that repeats on each page).
  R5 furniture  file data: a line that is only a file name or a folder path, or that contains a
                drive letter path ("I:\\Daten\\…") or a file name with the extension .doc, .docx,
                .dot, .dotx, .pdf, .xls, .xlsx without "http" or "www"; a document property field
                ("Fehler! Unbekannter Name für Dokument-Eigenschaft"); a line of only underscores; a
                rotated line that is not inside a picture.
Header zone: Docling form "Kopfzeile", or the top edge of the atom frame in the top 20 % of the page.
Footer zone: Docling form "Fusszeile", or the bottom edge of the atom frame in the bottom 12 % of the page.
Page size: from the Docling file (<data>/iso/docling/<doc_id>.json).

Usage:  python3 src/m03_iso_hilfe.py DOC_ID            (one line for each atom with a fixed role, then the
                                                     atoms inside a picture and the zone atoms without one)
        python3 src/m03_iso_hilfe.py --check FILE...  (segmentation files: atoms whose role differs from a fixed role)
"""

from __future__ import annotations

import collections
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import iso_path  # noqa: E402

VERSION = "e20-v3-fixed-roles-1"

RX_CONTINUATION = re.compile(r"^\s*[-–.…]{0,3}\s*/\s*[-–.…]{1,3}\s*$")
RX_FILE = re.compile(r"(\.docx?\b|\.pdf\b|\.xlsx?\b|\.dotx?\b|\b[a-z]:\\|\\\\|"
                     r"fehler! |error! |erreur ! |errore! )", re.I)
RX_PATH_LINE = re.compile(r"^\s*(/|[a-z]:\\|\\\\)\S+\s*$", re.I)
RX_WEB = re.compile(r"http|www\.", re.I)
RX_UNDERSCORES = re.compile(r"^\s*_{5,}\s*$")
RX_DATE = re.compile(r"\d{1,2}\s*\.\s*\d{1,2}\s*\.\s*\d{2,4}")
RX_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
RX_DIGIT = re.compile(r"\d")
RX_PAGE_LINE = re.compile(r"^\s*[-–—]?\s*\d{1,3}\s*/\s*\d{1,3}\s*[-–—]?\s*$")
RX_BARE_NUMBER = re.compile(r"^\s*[-–—]?\s*\d{1,3}\s*[-–—]?\.?\s*$")
RX_PAGE_PART = re.compile(r"\b(seite|page|pagina|pag\.|p\.|s\.)\s*\d{1,3}(\s*(/|von|de|di|da|sur|of)\s*\d{1,3})?"
                          r"|[-–—]\s*\d{1,3}\s*[-–—]|\b\d{1,3}\s*(/|von|de|di|da|sur)\s*\d{1,3}\s*$", re.I)
HEADER_ZONE = 0.20
FOOTER_ZONE = 0.12
SAME_POSITION_PT = 30.0


def has(a: dict, key: str) -> bool:
    return any(m[0] == key for m in a.get("merkmale", []))


def letters(t: str) -> str:
    return "".join(RX_LETTER.findall(t.lower()))


def page_heights(doc_id: str) -> dict[int, float]:
    d = json.loads(iso_path("docling", doc_id).read_text(encoding="utf-8"))
    return {p["seite"]: float(p["hoehe"]) for p in d.get("seiten", [])}


def zone(a: dict, heights: dict[int, float]) -> str | None:
    if a["label"] == "page_header" or a.get("kopf_fuss") == "kopf":
        return "header"
    if a["label"] == "page_footer" or a.get("kopf_fuss") == "fuss":
        return "footer"
    r, h = a.get("rahmen"), heights.get(a["seite"])
    if not r or not h:
        return None
    if r[1] < HEADER_ZONE * h:
        return "header"
    if r[3] > (1 - FOOTER_ZONE) * h:
        return "footer"
    return None


def marked(a: dict) -> bool:
    """Docling marks the atom as a page header or a page footer."""
    return a["label"] in ("page_header", "page_footer") or bool(a.get("kopf_fuss"))


def key(t: str) -> tuple[str, str]:
    """(letters, digits) of a text without page number parts, for the comparison of R4."""
    t = RX_PAGE_PART.sub(" ", t.lower())
    return letters(t), "".join(RX_DIGIT.findall(t))


def same(x: tuple[str, str], y: tuple[str, str]) -> bool:
    return x[1] == y[1] and (x[0] == y[0] or difflib.SequenceMatcher(None, x[0], y[0]).ratio() >= 0.9)


def fixed_roles(doc_id: str, atoms: list[dict] | None = None) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """({atom id: (role, rule)}, {atom id: zone}) for the rules R1 to R5."""
    if atoms is None:
        atoms = json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))["atome"]
    heights = page_heights(doc_id)
    zones = {a["id"]: z for a in atoms if (z := zone(a, heights))}
    cand = [a for a in atoms if a["id"] in zones and a.get("rahmen")
            and (len(letters(a["text"])) >= 3 or len(RX_DIGIT.findall(a["text"])) >= 4)]
    keys = {a["id"]: key(a["text"]) for a in cand}

    def repeated(a: dict) -> bool:
        return any(b["seite"] != a["seite"] and zones[b["id"]] == zones[a["id"]] and same(keys[a["id"]], keys[b["id"]])
                   and (marked(a) or marked(b) or abs(a["rahmen"][1] - b["rahmen"][1]) <= SAME_POSITION_PT)
                   for b in cand)

    out = {}
    for a in atoms:
        t = a["text"].strip()
        in_picture = a.get("eltern") == "picture"
        if (has(a, "page_number") or "Seitenzahl" in a.get("hinweise", [])
                or (t and (RX_CONTINUATION.match(t) or RX_PAGE_LINE.match(t)))
                or (a["id"] in zones and not in_picture and RX_BARE_NUMBER.match(t))):
            out[a["id"]] = ("furniture", "R1 page number")
        elif a["label"] == "footnote":
            out[a["id"]] = ("insert", "R2 footnote")
        elif a["label"] == "picture" or (a["id"] in zones and t and len(t) <= 2 and not re.search(r"\d", t)):
            out[a["id"]] = ("insert", "R3 picture")
        elif a["id"] in keys and repeated(a):
            out[a["id"]] = ("furniture", "R4 header or footer")
        elif t and not in_picture and (RX_PATH_LINE.match(t) or (RX_FILE.search(t) and not RX_WEB.search(t))
                                       or RX_UNDERSCORES.match(t) or has(a, "rotated")):
            out[a["id"]] = ("furniture", "R5 file data")
    return out, zones


def check(paths: list[str]) -> int:
    bad = 0
    for path in paths:
        seg = json.loads(Path(path).read_text(encoding="utf-8"))
        roles, _ = fixed_roles(seg["doc_id"])
        furn, ins = set(seg.get("furniture", [])), set(seg.get("insert", []))
        diff = []
        for a, (role, rule) in roles.items():
            got = "furniture" if a in furn else "insert" if a in ins else "main"
            if got != role:
                diff.append(f"{a}: {got}, fixed role {role} ({rule})")
        bad += bool(diff)
        print(f"{path}: {len(diff)} deviations" + "".join(f"\n  {d}" for d in diff))
    print(f"files {len(paths)}, files with deviations {bad}")
    return 1 if bad else 0


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    if sys.argv[1] == "--check":
        sys.exit(check(sys.argv[2:]))
    doc_id = sys.argv[1]
    atoms = json.loads(iso_path("atome", doc_id).read_text(encoding="utf-8"))["atome"]
    roles, zones = fixed_roles(doc_id, atoms)
    print(f"# {VERSION}: fixed roles (E20 v3, rules R1 to R5) of {doc_id}")
    for a in atoms:
        if a["id"] in roles:
            role, rule = roles[a["id"]]
            print(f"{a['id']} | {role} | {rule} | {a['text'][:60]}")
    print("# text inside a picture (hint 'im Bild') without a fixed role: decide by E20 chapter 3, insert 2")
    for a in atoms:
        if a.get("eltern") == "picture" and a["id"] not in roles:
            print(f"{a['id']} | im Bild | page {a['seite']} | {a['text'][:60]}")
    print("# atoms in the header or footer zone without a fixed role (decide by meaning)")
    for a in atoms:
        if a["id"] in zones and a["id"] not in roles:
            print(f"{a['id']} | {zones[a['id']]} | page {a['seite']} | {a['text'][:60]}")


if __name__ == "__main__":
    main()

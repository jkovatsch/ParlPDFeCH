# SPDX-License-Identifier: Apache-2.0
"""2.7 Augenschein, Schritt 1: schlanker Index aller PDF-Dokumente aus <data>/roh/exports/docs/.

Streamt jede docs_<body_key>.ndjson.gz zeilenweise (gzip -dc als Unterprozess), behaelt nur
Dokumente mit format application/pdf und schreibt pro Dokument eine Zeile ohne Volltext und
ohne Dateinamen (Dateinamen koennen Personennamen enthalten). Statt des Namens wird nur eine
grobe Rollenklasse aus Name und Kategorie abgeleitet (Regex, siehe NAME_KLASSEN).

Ausgabe: <data>/analyse/pdf/docs_pdf_index.csv.gz
Aufruf (im Ordner track_2a): uv run python src/m02_pdf_index.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
EXPORTE = DATA / "roh/exports"
AUS = DATA / "analyse/pdf/docs_pdf_index.csv.gz"

# Reihenfolge zaehlt: erste passende Klasse gewinnt.
NAME_KLASSEN: list[tuple[str, re.Pattern]] = [
    ("antwort", re.compile(
        r"antwort|beantwortung|stellungnahme|\brrb\b|regierungsratsbeschluss|r[ée]ponse|"
        r"risposta|prise de position|rapport du conseil d.[ée]tat|r[ée]ponse du conseil|"
        r"rapporto del consiglio di stato|presa di posizione", re.I)),
    ("vorstoss", re.compile(
        r"motion|postulat|interpellation|anfrage|\bfrage\b|fragestunde|vorstoss|"
        r"parlamentarische initiative|einzelinitiative|beh[öo]rdeninitiative|standesinitiative|"
        r"question|interpellanza|mozione|interrogazione|iniziativa parlamentare|"
        r"initiative parlementaire|r[ée]solution|resolution|petition|p[ée]tition|"
        r"dringliche|urgente|eingereicht|d[ée]pos[ée]|wortlaut", re.I)),
    ("bericht_vorlage", re.compile(
        r"bericht|botschaft|vorlage|antrag|message|rapport|messaggio|preavviso|"
        r"entwurf|projet|disegno|erl[äa]uter", re.I)),
    ("beschluss", re.compile(r"beschluss|d[ée]cision|decisione|risoluzione|d[ée]cret|dekret", re.I)),
    ("protokoll", re.compile(r"protokoll|proc[èe]s-verbal|verbale|bulletin|wortprotokoll", re.I)),
    ("beilage", re.compile(r"beilage|anhang|annexe|allegato|anlage", re.I)),
]


def name_klasse(name: str | None, kat: str | None) -> str:
    s = " ".join(x for x in (name, kat) if x)
    if not s:
        return "leer"
    for k, rx in NAME_KLASSEN:
        if rx.search(s):
            return k
    return "andere"


def ebene(body_key: str) -> str:
    if body_key == "CHE":
        return "bund"
    if body_key == "LIE":
        return "ausland_li"
    if body_key.isdigit():
        return "gemeinde"
    return "kanton"


FELDER = [
    "id", "body_key", "ebene", "language", "parent_type", "affair_id", "category_de",
    "category_harmonized", "name_klasse", "size", "text_len", "text_nonws", "hash",
    "url_oparl", "date",
]


def verarbeite(pfad: Path) -> tuple[str, list[list]]:
    body_key = pfad.name[len("docs_"):-len(".ndjson.gz")]
    zeilen: list[list] = []
    proc = subprocess.Popen(["gzip", "-dc", str(pfad)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    for roh in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        # billiger Vorfilter vor dem JSON-Parsen
        if '"application/pdf"' not in roh:
            continue
        d = json.loads(roh)
        if d.get("format") != "application/pdf":
            continue
        text = d.get("text") or ""
        zeilen.append([
            d.get("id"), body_key, ebene(body_key), d.get("language") or "",
            d.get("parent_type") or "", d.get("affair_id") or "",
            (d.get("category_de") or "").strip(), d.get("category_harmonized") or "",
            name_klasse(d.get("name"), d.get("category_de")),
            d.get("size") if d.get("size") is not None else "",
            len(text), len(re.sub(r"\s+", "", text)),
            d.get("hash") or "", d.get("url_oparl") or "", (d.get("date") or "")[:10],
        ])
    proc.wait()
    return body_key, zeilen


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    dateien = sorted((EXPORTE / "docs").glob("docs_*.ndjson.gz"), key=lambda p: -p.stat().st_size)
    AUS.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(AUS, "wt", encoding="utf-8", newline="") as f, Pool(4) as pool:
        w = csv.writer(f)
        w.writerow(FELDER)
        for body_key, zeilen in pool.imap_unordered(verarbeite, dateien):
            w.writerows(zeilen)
            n += len(zeilen)
            print(f"{body_key}: {len(zeilen)} PDF", file=sys.stderr, flush=True)
    print(f"fertig: {n} PDF-Dokumente in {rel(AUS)}")


if __name__ == "__main__":
    main()

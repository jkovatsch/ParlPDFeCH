# SPDX-License-Identifier: Apache-2.0
"""Gemeinsame Hilfen für das Korpus-Profil (Teilfrage 2.2).

Wird von m02_korpus_geschaefte.py importiert (im privaten Projekt auch von zwei weiteren
Profil-Skripten, die nicht in diesem Repository sind). Liest die OpenParlData-Exporte
(<data>/roh/exports, m02_exporte_holen.sh) zeilenweise (gzip-NDJSON), nie als Ganzes.

Ebenen-Zuordnung (aus bodies.type):
  country + body_key CHE  -> Bund
  country + body_key LIE  -> Liechtenstein (separat ausgewiesen)
  canton                  -> Kanton
  city, municipality      -> Gemeinde (Untertyp in Spalte typ_name_de)
"""

from __future__ import annotations

import csv
import gzip
import json
import statistics
import sys
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
EXPORTE = DATA / "roh" / "exports"
AUSGABE = DATA / "analyse" / "korpus"

EBENEN = ["Bund", "Kanton", "Gemeinde", "Liechtenstein"]


def zeilen(entitaet: str) -> Iterator[dict]:
    """Streamt einen Export (z. B. 'affairs') zeilenweise als dict."""
    with gzip.open(EXPORTE / f"{entitaet}.ndjson.gz", "rt", encoding="utf-8") as f:
        for zeile in f:
            if zeile.strip():
                yield json.loads(zeile)


def ebene(body: dict) -> str:
    typ = body.get("type")
    if typ == "country":
        if body.get("body_key") == "CHE":
            return "Bund"
        if body.get("body_key") == "LIE":
            return "Liechtenstein"
        return "Staat (andere)"
    if typ == "canton":
        return "Kanton"
    if typ in ("city", "municipality"):
        return "Gemeinde"
    return "unbekannt"


def bodies() -> dict[str, dict]:
    """body_key -> body (klein, 2411 Zeilen)."""
    return {b["body_key"]: b for b in zeilen("bodies")}


def affair_index() -> dict[int, tuple[str, str, int | None]]:
    """affair id -> (body_key, Ebene, type_harmonized_id)."""
    b = bodies()
    idx: dict[int, tuple[str, str, int | None]] = {}
    for a in zeilen("affairs"):
        idx[a["id"]] = (a["body_key"], ebene(b[a["body_key"]]), a.get("type_harmonized_id"))
    return idx


def leer(wert) -> bool:
    return wert is None or (isinstance(wert, str) and wert.strip() == "")


def erster(*werte):
    """Erster nicht-leerer Wert oder None."""
    for w in werte:
        if not leer(w):
            return w
    return None


def anteil(zaehler: int, nenner: int, stellen: int = 4) -> float | str:
    return round(zaehler / nenner, stellen) if nenner else ""


def median(werte: list[int]) -> float | str:
    return statistics.median(werte) if werte else ""


def schreibe_csv(name: str, kopf: list[str], zeilen_: list[list]) -> Path:
    AUSGABE.mkdir(parents=True, exist_ok=True)
    pfad = AUSGABE / name
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(kopf)
        w.writerows(zeilen_)
    return pfad

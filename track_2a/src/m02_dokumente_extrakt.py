# SPDX-License-Identifier: Apache-2.0
"""2.3 Dokument-Profil, Schritt 1: Merkmalstabelle aller Dokumente aus <data>/roh/exports/docs/.

Streamt jede docs_<body_key>.ndjson.gz zeilenweise (gzip -dc als Unterprozess, parallel ueber
Dateien) und schreibt pro Dokument eine Zeile ohne Volltext und ohne Dateinamen (Dateinamen
koennen Personennamen enthalten). Aus dem Tika-Volltext werden nur Zaehlwerte abgeleitet:

- text_status   none (Feld fehlt/null), leer (nur Leerraum), ok
- textlaenge    len(text) in Zeichen (Rohtext inkl. Leerraum)
- zeichen_nows  Zeichen ohne Leerraum
- buchstaben    Unicode-Buchstaben (Text ohne Treffer von [\\W\\d_]+)
- muell         Zeichen aus Private-Use-Bereich U+E000-U+F8FF oder U+FFFD (Hinweis auf
                kaputte Schriftkodierung)
- text_md5      die ersten 16 Hex-Zeichen des MD5 ueber den Text mit zusammengefasstem Leerraum
                (nur zum Erkennen identischer Platzhaltertexte, nicht umkehrbar)
- m_antwort, m_einreichung, m_auftrag
                1/0: Treffer der Marker-Regexe RX_ANTWORT, RX_EINREICHUNG, RX_AUFTRAG in den
                ersten 3000 Zeichen (kleingeschrieben); grobe Inhaltsmarker zur Plausibilisierung
                der Kategorien, kein Klassifikator

Kategoriefelder (category_de/fr/it), die wie Dateinamen oder Freitext aussehen (RX_DATEINAME oder
laenger als 80 Zeichen), werden durch KATEGORIE_MASKE ersetzt, weil Dateinamen Personennamen
enthalten koennen. Die Spalte kat_freitext_stichwort haelt nur die Rollenklasse fest, die die
Stichwortregeln ROLLE_* (auch von m02_dokumente_profil.py genutzt) im maskierten Wert finden.

Zusaetzlich wird tika_metadata auf Schluessel geprueft (Zaehlung aller Schluessel) und eine
Seitenzahl uebernommen, falls ein bekannter Seitenschluessel vorhanden ist.

Ausgaben:
  <data>/analyse/dokumente/dokumente_merkmale.csv.gz   eine Zeile pro Dokument
  <data>/analyse/dokumente/tika_metadata_schluessel.csv Schluessel in tika_metadata mit Anzahl
  <data>/analyse/dokumente/extrakt_dateien.csv          Zeilen/Fehler pro Exportdatei

Aufruf (im Ordner track_2a): uv run python src/m02_dokumente_extrakt.py
"""

from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
DOCS = DATA / "roh/exports/docs"
AUSDIR = DATA / "analyse/dokumente"
TEILE = AUSDIR / ".teile_extrakt"
AUS = AUSDIR / "dokumente_merkmale.csv.gz"

SPALTEN = [
    "id", "datei_key", "body_key", "parent_type", "format", "url_endung", "language",
    "category_de", "category_fr", "category_it", "category_harmonized",
    "affair_id", "agenda_id", "meeting_id", "jahr", "size", "hash", "url_oparl",
    "text_status", "textlaenge", "zeichen_nows", "buchstaben", "muell", "seiten",
    "text_md5", "m_antwort", "m_einreichung", "m_auftrag", "kat_freitext_stichwort",
]

KATEGORIE_MASKE = "<Dateiname/Freitext>"
RX_DATEINAME = re.compile(r"\.[A-Za-z0-9]{2,4}$|_.*_")
# Stichwortregeln fuer die Rolle einer lokalen Kategorie (Heuristik)
ROLLE_ANTWORT = re.compile(
    r"antwort|beantwortung|r[ée]ponse|rispost|stellungnahme des (regierungs|gemeinde|stadt|bundes)rat|"
    r"avis du conseil|prise de position du conseil")
ROLLE_ANTWORT_BERICHT = re.compile(
    r"(bericht|rapports?) (zu[mr]?|sur|über|au) (de[nmr] |l[ae] |les |l.)?(postulat|motion|interpellation)")
ROLLE_EXEKUTIVBESCHLUSS = re.compile(
    r"regierungsratsbeschluss|regierungsbeschluss|decreto governativo|\brrb\b|\bace\b|"
    r"arr[êe]t[ée] du conseil")
ROLLE_VORSTOSS = re.compile(
    r"vorst[oö]ss|intervention|interventi|\bmotion|postulat|interpellation|interpellanz|"
    r"interpellanza|anfrage|\bfrage\b|domanda|question|interrogazione|mozione|d[ée]p[ôo]t\b|"
    r"\beingabe\b|texte soumis|testo dell|eingereicht|einreichung|\bauftrag\b|\banzug\b|"
    r"parlamentarische initiative|initiative parlementaire|iniziativa parlamentare|"
    r"einzelinitiative|standesinitiative|beh[öo]rdeninitiative")
ROLLE_AUSNAHME = re.compile(r"antwortformular|ordnungsantrag|motion d.ordre")


def stichwort_rolle(s: str) -> str:
    """Rollenklasse eines (kleingeschriebenen) Kategorietextes nach den Stichwortregeln; '' wenn keine"""
    if ROLLE_AUSNAHME.search(s):
        return ""
    if ROLLE_ANTWORT.search(s) or ROLLE_ANTWORT_BERICHT.search(s):
        return "antwort_exekutive"
    if ROLLE_EXEKUTIVBESCHLUSS.search(s):
        return "exekutivbeschluss"
    if ROLLE_VORSTOSS.search(s):
        return "vorstoss_eingereicht"
    return ""


def kategorie(x) -> tuple[str, str]:
    """(Kategorie oder Maske, Stichwortrolle des maskierten Werts)"""
    if x is None:
        return "", ""
    s = str(x)
    if RX_DATEINAME.search(s) or len(s) > 80:
        return KATEGORIE_MASKE, stichwort_rolle(s.lower().replace("_", " "))
    return s, ""

RX_NICHTBUCHSTABE = re.compile(r"[\W\d_]+")
RX_MUELL = re.compile("[\ue000-\uf8ff\ufffd]")
RX_LEER = re.compile(r"\s+")
KOPF = 3000
RX_ANTWORT = re.compile(
    r"\bantwort|\bbeantwort|\br[ée]ponse|\brispost|stellungnahme de[sr] (regierung|gemeinde|stadt|"
    r"bundes|staats|klein)|avis du (conseil|municipal)|prise de position du|presa di posizione")
RX_EINREICHUNG = re.compile(
    r"eingereicht|einreichung|\bd[ée]pos[ée]e?s?\b|\bd[ée]p[ôo]t\b|\bdepositat|\bpresentat[aoei]\b|"
    r"inoltrat|mitunterzeichn|unterzeichnet|cosignatair|cofirmatar")
RX_AUFTRAG = re.compile(
    r"wird beauftragt|wird gebeten|wird ersucht|wird eingeladen|\best charg[ée]|\best invit[ée]|"
    r"\best pri[ée]|\bdemande au conseil|\bchiede(no)? al|\binvita(no)? il|si chiede|"
    r"\bfragen an\b|\bich frage|\bwir fragen|\bfolgende fragen|questions suivantes|seguenti domande")
# bekannte Tika-Schluessel fuer Seitenzahlen (PDF: xmpTPg:NPages; Office: meta:page-count)
SEITEN_SCHLUESSEL = ("xmpTPg:NPages", "meta:page-count", "Page-Count", "nbPage", "pdf:NPages")


def url_endung(url: str | None) -> str:
    if not url:
        return ""
    u = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    letzter = u.rsplit("/", 1)[-1]
    if "." not in letzter:
        return ""
    end = letzter.rsplit(".", 1)[-1].lower()
    return end if 1 <= len(end) <= 5 and end.isalnum() else ""


def leer(x) -> str:
    return "" if x is None else str(x)


def seiten_aus(tm) -> tuple[str, list[str]]:
    """liefert (Seitenzahl oder '', Liste der Schluessel)"""
    if not tm:
        return "", []
    if isinstance(tm, str):
        try:
            tm = json.loads(tm)
        except Exception:
            return "", ["<unlesbar>"]
    if isinstance(tm, list):
        tm = tm[0] if tm and isinstance(tm[0], dict) else {}
    if not isinstance(tm, dict):
        return "", ["<kein dict>"]
    seiten = ""
    for k in SEITEN_SCHLUESSEL:
        v = tm.get(k)
        if isinstance(v, list):
            v = v[0] if v else None
        if v not in (None, ""):
            try:
                seiten = str(int(str(v).strip()))
                break
            except ValueError:
                pass
    return seiten, list(tm.keys())


def verarbeite(pfad_str: str) -> dict:
    pfad = Path(pfad_str)
    datei_key = pfad.name[len("docs_"):-len(".ndjson.gz")]
    teil = TEILE / f"{datei_key}.csv.gz"
    schluessel = collections.Counter()
    zeilen = fehler = 0
    proc = subprocess.Popen(["gzip", "-dc", str(pfad)], stdout=subprocess.PIPE, bufsize=1 << 20)
    with gzip.open(teil, "wt", newline="", encoding="utf-8", compresslevel=5) as fo:
        w = csv.writer(fo)
        for roh in io.TextIOWrapper(proc.stdout, encoding="utf-8", errors="replace"):
            if not roh.strip():
                continue
            zeilen += 1
            try:
                d = json.loads(roh)
            except Exception:
                fehler += 1
                continue
            t = d.get("text")
            md5, ma, me, mf = "", 0, 0, 0
            if t is None:
                status, tl, nows, bu, mu = "none", 0, 0, 0, 0
            else:
                tl = len(t)
                nows = len(RX_LEER.sub("", t)) if tl else 0
                if nows == 0:
                    status, bu, mu = "leer", 0, 0
                else:
                    status = "ok"
                    bu = len(RX_NICHTBUCHSTABE.sub("", t))
                    mu = len(RX_MUELL.findall(t))
                    norm = RX_LEER.sub(" ", t).strip()
                    md5 = hashlib.md5(norm.encode("utf-8", "replace")).hexdigest()[:16]
                    kopf = norm[:KOPF].lower()
                    ma = 1 if RX_ANTWORT.search(kopf) else 0
                    me = 1 if RX_EINREICHUNG.search(kopf) else 0
                    mf = 1 if RX_AUFTRAG.search(kopf) else 0
            seiten, keys = seiten_aus(d.get("tika_metadata"))
            schluessel.update(keys)
            datum = d.get("date") or ""
            kats = [kategorie(d.get(f"category_{sp}")) for sp in ("de", "fr", "it")]
            kat_stw = next((r for _, r in kats if r), "")
            w.writerow([
                leer(d.get("id")), datei_key, leer(d.get("body_key")), leer(d.get("parent_type")),
                leer(d.get("format")), url_endung(d.get("url")), leer(d.get("language")),
                kats[0][0], kats[1][0], kats[2][0],
                leer(d.get("category_harmonized")),
                leer(d.get("affair_id")), leer(d.get("agenda_id")), leer(d.get("meeting_id")),
                datum[:4], leer(d.get("size")), leer(d.get("hash")), leer(d.get("url_oparl")),
                status, tl, nows, bu, mu, seiten, md5, ma, me, mf, kat_stw,
            ])
    rc = proc.wait()
    return {"datei_key": datei_key, "zeilen": zeilen, "json_fehler": fehler, "gzip_rc": rc,
            "schluessel": dict(schluessel)}


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    AUSDIR.mkdir(parents=True, exist_ok=True)
    if TEILE.exists():
        shutil.rmtree(TEILE)
    TEILE.mkdir()
    dateien = sorted(DOCS.glob("docs_*.ndjson.gz"), key=lambda p: p.stat().st_size, reverse=True)
    print(f"{len(dateien)} Dateien", file=sys.stderr)
    t0 = time.time()
    ergebnisse = []
    with Pool(6) as pool:
        for r in pool.imap_unordered(verarbeite, [str(p) for p in dateien]):
            ergebnisse.append(r)
            print(f"[{time.time() - t0:6.0f}s] {r['datei_key']}: {r['zeilen']} Zeilen, "
                  f"{r['json_fehler']} JSON-Fehler, rc={r['gzip_rc']}", file=sys.stderr)
    # Kopfzeile als eigenes gzip-Mitglied, danach Teile anhaengen (gzip-Mitglieder sind verkettbar)
    with open(AUS, "wb") as fo:
        kopf = io.StringIO()
        csv.writer(kopf).writerow(SPALTEN)
        fo.write(gzip.compress(kopf.getvalue().encode("utf-8")))
        for r in sorted(ergebnisse, key=lambda r: r["datei_key"]):
            with open(TEILE / f"{r['datei_key']}.csv.gz", "rb") as fi:
                shutil.copyfileobj(fi, fo)
    shutil.rmtree(TEILE)
    gesamt = collections.Counter()
    for r in ergebnisse:
        gesamt.update(r["schluessel"])
    with open(AUSDIR / "tika_metadata_schluessel.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["schluessel", "anzahl_dokumente"])
        for k, n in gesamt.most_common():
            w.writerow([k, n])
    with open(AUSDIR / "extrakt_dateien.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["datei_key", "zeilen", "json_fehler", "gzip_rc"])
        for r in sorted(ergebnisse, key=lambda r: r["datei_key"]):
            w.writerow([r["datei_key"], r["zeilen"], r["json_fehler"], r["gzip_rc"]])
    print(f"fertig in {time.time() - t0:.0f}s: {sum(r['zeilen'] for r in ergebnisse)} Zeilen, "
          f"{len(gesamt)} tika-Schluessel", file=sys.stderr)


if __name__ == "__main__":
    main()

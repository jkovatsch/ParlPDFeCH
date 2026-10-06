# SPDX-License-Identifier: Apache-2.0
"""Synthese Phase 2: Aufteilung der Parlamente auf Training, Validierung und Gold.

Die Rolle «Gold» ist die Testmenge (test set). Das Skript braucht die Tabellen der Phase 2 (unten);
die Skripte m02_texte_profil.py und die Skripte der PDF-Sichtung (augenschein.csv) sind nicht in
diesem Repository.

Liest nur Tabellen, die die Analyse-Skripte der Teilfragen 2.2 bis 2.7 geschrieben haben, dazu die
Pilot-Kandidaten aus src/m02_synthese_pilot_kandidaten.py:

  <data>/analyse/korpus/parlamente.csv              Ebene, Sprache, Geschaefte      (m02_korpus_geschaefte.py)
  <data>/analyse/dokumente/parlamente.csv           Scan-Anteil, PDF                (m02_dokumente_profil.py)
  <data>/analyse/dokumente/verteilung_rolle.csv     Dokumente je Kategorie-Rolle    (m02_dokumente_profil.py)
  <data>/analyse/texte/profil_parlamente.csv        strukturierte Texte             (m02_texte_profil.py)
  <data>/analyse/ech/geschaefte_merkmale.csv.gz     Silber-Labels je Geschaeft      (m02_ech_abgleich.py)
  <data>/analyse/synthese/pilot_kandidaten_je_parlament.csv                         (m02_synthese_pilot_kandidaten.py)

Version 2 (05.10.2026, project decision E26): GE, SG and 1061 move from test (`Gold`) to validation,
AR and FR from validation to test, 1024 from training to test. Reason: 3 inspection documents
(development documents) came from GE, SG and 1061. New and changed rules: R2 at affair level, R5 for
each task, R7 (no development document in the test set), R8 (duplicate texts), R9 (parliaments
without affairs). Version 1 of 04.10.2026: <data>/analyse/synthese/split_v1_2026-10-04.csv.

Die Zuteilung steht als Tabelle ZUTEILUNG im Skript (ganze Parlamente, mit Kurzbegruendung). Das
Skript prueft die Regeln R1-R9 und bricht ab, wenn eine verletzt ist:

  R1 jedes der 89 Parlamente mit Geschaeften genau einer Rolle zugeteilt
  R2 (v2) no affair of the test set has a structured text (submitted, reasoning, response, summary).
     Affairs of test parliaments with such a text are excluded from the test set
     (split_ausschluss_texte.csv); on 05.10.2026 these are the 93 consultation summaries of FR.
  R3 alle Parlamente mit strukturierten Texten zu Vorstoessen (eingereicht, Begruendung, Antwort)
     im Training oder in der Validierung, nicht im Gold
  R4 jede Rolle enthaelt Kantone und Gemeinden sowie die Sprachen de, fr und it
  R5 (v2) for each task with silver labels (recommendation, affair type): at least 3 validation
     parliaments with at least 20 labels each
  R6 Validierung und Gold je hoechstens 30 % der Parlamente
  R7 no parliament with a development document is in the test set (inspection documents and
     training examples <data>/beispiele/*/*.jsonl). The stratified sample (m03_iso_paths.SAMPLE_LIST)
     is not a source of R7: when this rule was written (05.10.2026), the sample was only
     downloaded and not processed. An earlier version of the split selected it.
  R8 a text (text_md5, at least 100 characters) in more than one set: the copies in the test set and
     in the validation set go to split_ausschluss_duplikate.csv (excluded from these sets)
  R9 parliaments with documents but without affairs: listed in split_ohne_geschaefte.csv, outside
     the split

Sprache eines Parlaments: Titelsprachen mit mindestens 10 % Anteil an den Geschaeftstiteln
(Spalten anteil_title_* aus korpus/parlamente.csv); mehrere Sprachen mit «/» verbunden.

Ausgaben nach <data>/analyse/synthese/:
  split.csv             ein Parlament pro Zeile mit Rolle, Begruendung und Kennzahlen
  split_schichten.csv   Parlamente und Geschaefte je Ebene x Sprache x Rolle
  silber_je_rolle.csv   Silber-Labels mit PDF-Text je Aufgabe und Rolle (Obergrenzen)

Aufruf (im Ordner track_2a): uv run python src/m02_synthese_split.py
"""

from __future__ import annotations

import collections
import csv
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
AN = DATA / "analyse"
AUSDIR = AN / "synthese"

T, V, G = "Training", "Validierung", "Gold"

# body_key -> (Rolle, Kurzbegruendung)
ZUTEILUNG: dict[str, tuple[str, str]] = {
    # Bund und Liechtenstein
    "CHE": (T, "strukturierte Texte (eingereicht, Begründung, Antwort) als Textbeispiele; fast keine Vorstoss-PDF"),
    "LIE": (T, "strukturierte Texte (Kleine Anfragen); kaum PDF an Vorstössen"),
    # Kantone deutsch
    "ZH": (T, "beste Metadaten, Empfehlung belegt, viele Vorstoss-/Antwort-PDF"),
    "BS": (T, "grosser Bestand; 40 % ohne harmonisierten Typ, kurze Texte"),
    "AG": (T, "Empfehlung belegt; texts nur Vernehmlassungs-Leads"),
    "LU": (T, "Empfehlung belegt; texts nur Vernehmlassungs-Leads"),
    "TG": (T, "texts nur Vernehmlassungs-Leads (Lead wortgleich im PDF)"),
    "UR": (T, "texts nur Vernehmlassungs-Leads"),
    "OW": (T, "texts nur Vernehmlassungs-Leads"),
    "NW": (T, "texts nur Vernehmlassungs-Leads; viele fehlgeschlagene Extraktionen"),
    "GL": (T, "Pilot-Kandidaten (Vorstoss-Kategorie)"),
    "GR": (T, "Pilot: einzige Quelle für question; einziges Parlament mit Rätoromanisch"),
    "AI": (T, "klein; kaum Typ-Labels"),
    "SO": (V, "Empfehlung belegt (86 %); Pilot-Kandidaten"),
    "ZG": (V, "Pilot-Kandidaten; texts nur Vernehmlassungs-Leads"),
    "SZ": (V, "geringe PDF-Abdeckung"),
    "AR": (G, "kleiner Kanton; v2: in den Test (E26), keine Entwicklungsdokumente"),
    "SG": (V, "digital, Vorstoss und Antwort nach Dateiname; v2: Validierung (E26), Augenschein K10"),
    "BL": (G, "Empfehlung belegt (Silber prüfbar); keine texts"),
    "SH": (G, "Scan-Anteil 5 %; keine texts"),
    # Kantone zweisprachig
    "BE": (T, "grösste Pilot-Quelle für motion; Metadatentabellen im PDF"),
    "FR": (G, "zweisprachig; Antwort-Kategorie; texts nur Vernehmlassungs-Teaser (keine Geschaefte mit Text); v2: Test (E26)"),
    "VS": (G, "zweisprachig; Vorstoss- und Antwort-Kategorien; keine texts"),
    # Kantone franzoesisch
    "JU": (T, "grösste FR-Pilot-Quelle; Empfehlung belegt"),
    "VD": (T, "strukturierte eingereichte Texte (7); Scan-Anteil 13 %"),
    "NE": (V, "Empfehlung belegt; kaum Scans"),
    "GE": (V, "97 % ohne harmonisierten Typ, Typ nur am PDF prüfbar; keine texts; v2: Validierung (E26), Augenschein K05"),
    # Kanton italienisch
    "TI": (T, "einziger italienischsprachiger Kanton; Hauptquelle für parliamentary_initiative"),
    # Gemeinden deutsch
    "261": (T, "grosser Bestand, Empfehlung belegt"),
    "351": (T, "grösste Gemeinde-Pilot-Quelle"),
    "230": (T, "Pilot-Kandidaten"),
    "1059": (T, "Pilot-Kandidaten; Empfehlung belegt"),
    "2581": (T, "texts (Beschreibung)"),
    "361": (T, "texts (Beschreibung)"),
    "4082": (T, "texts (Beschreibung); Scan-Anteil 28 %"),
    "581": (T, "strukturierte Texte (Vorstoss, Begründung); kein Tika-Text"),
    "3901": (T, "keine PDF mit affair_id"),
    "2939": (T, "keine PDF mit affair_id"),
    "1058": (T, "Gemeinde DE"), "942": (T, "Gemeinde DE"), "66": (T, "Gemeinde DE"),
    "1024": (G, "Gemeinde DE; v2: Test (E26), keine Entwicklungsdokumente"), "3427": (T, "Gemeinde DE"), "4001": (T, "Gemeinde DE"),
    "191": (T, "Gemeinde DE"), "3443": (T, "Gemeinde DE"), "293": (T, "Gemeinde DE"),
    "62": (T, "Gemeinde DE"), "2703": (T, "Gemeinde DE"), "121": (T, "Gemeinde DE"),
    "2937": (T, "Gemeinde DE"), "4566": (T, "Gemeinde DE"), "131": (T, "Gemeinde DE"),
    "329": (T, "Gemeinde DE"), "616": (T, "Gemeinde DE; wenige PDF"), "3001": (T, "Gemeinde DE"),
    "4401": (T, "Gemeinde DE"), "4201": (T, "Gemeinde DE"), "404": (T, "Gemeinde DE"),
    "743": (T, "grösste unabhängige Blockrollen-Quelle (Webseite, rund 100 Geschäfte); Pilot-Kandidaten"),
    "296": (V, "Pilot-Kandidaten; Scan-Anteil 21 %"),
    "306": (V, "Pilot-Kandidaten"),
    "247": (V, "Empfehlung belegt"),
    "243": (V, "Scan-Anteil 38 %"),
    "1711": (V, "Gemeinde DE"), "2829": (V, "Gemeinde DE"), "4045": (V, "Gemeinde DE"),
    "4671": (V, "Gemeinde DE"),
    "2831": (G, "Scan-Anteil 38 %"),
    "3203": (G, "Scan-Anteil 24 %; viele Beschlüsse und Berichte"),
    "198": (G, "Empfehlung belegt"),
    "1061": (V, "grosse Stadt, Vorstoss und Antwort nach Dateiname; v2: Validierung (E26), Augenschein G05"),
    "4289": (G, "Empfehlung belegt; Scan-Anteil 16 %"),
    "53": (G, "kleine Stadt, Bestand erst ab 2019"),
    # Gemeinden franzoesisch
    "6621": (T, "grosser Bestand; 35 % ohne harmonisierten Typ"),
    "5586": (V, "Pilot-Kandidaten FR; Résumé (texts) mögliche Blockrollen-Validierung"),
    "6248": (T, "strukturierte Texte aus LLM-Extraktion"),
    "6421": (T, "strukturierte Texte (Regex aus PDF); harmonisierte Kategorien"),
    "6458": (T, "wenige PDF mit Text"), "2125": (T, "keine PDF"), "6037": (T, "sehr klein"),
    "6152": (V, "Pilot-Kandidaten; harmonisierte Kategorie submitted_text"),
    "2196": (V, "zweisprachige Titel, geringe PDF-Abdeckung"),
    "6643": (G, "Empfehlung belegt; keine texts"),
    "6153": (G, "kleiner Bestand (165 Geschäfte); keine texts"),
    # Gemeinden italienisch
    "5254": (T, "kein harmonisierter Typ; harmonisierte Kategorien Vorstoss/Antwort"),
    "5192": (V, "einzige IT-Validierung im Pilot; Scan-Anteil 39 %"),
    "5002": (G, "Scan-Anteil 25 %; keine texts"),
    "5113": (G, "46 % ohne harmonisierten Typ; keine texts"),
}

AUFGABEN = [
    # (Aufgabe, Einheit, Spalte in geschaefte_merkmale oder Sonderquelle)
    ("Geschaeftstyp (affair_type exakt/nah)", "Geschaefte mit PDF-Text", "typ_ech_exakt_nah"),
    ("Geschaeftstyp, Pilot-Kandidaten (eindeutig, Vorstoss-Kategorie)", "Dokumente", "pilot"),
    ("Empfehlung der Exekutive", "Geschaefte mit PDF-Text", "empfehlung"),
    ("Ratsentscheid (ProcedureDecisionEnum)", "Geschaefte mit PDF-Text", "entscheid"),
    ("Einreichende (Zeige-Aufgabe, sponsor sicher)", "Geschaefte mit PDF-Text", "sponsor_sicher"),
    ("Einreichungsdatum (Zeige-Aufgabe, Ereignis)", "Geschaefte mit PDF-Text", "eingereicht_ereignis"),
    ("Antwortende Stelle", "Geschaefte mit PDF-Text", "responder"),
    ("Dokumentart: Vorstoss (Kategorie-Heuristik)", "Dokumente", "dok:vorstoss_eingereicht"),
    ("Dokumentart: Antwort der Exekutive (Kategorie-Heuristik)", "Dokumente", "dok:antwort_exekutive"),
    ("Blockrolle per Textabgleich (Schaetzung aus Phase 2)", "Geschaefte", "block"),
    ("Blockrolle: Resume Lausanne, Rolle unbestaetigt (Phase 2)", "Geschaefte", "block_resume"),
]

# Blockrollen-Silber je Parlament: Zahlen von Hand übernommen aus einer Auswertung der Phase 2
# (Geschaefte mit PDF-Treffer >= 0.5; Skripte [A] m02_texte_abgleich.py und [Pr] m02_pruefung_texte.py,
# nicht in diesem Repository).
# 5586: Resume, Rolle unbestaetigt -> nicht mitgezaehlt.
BLOCK = {"743": 104 + 52 + 7, "6421": 20, "VD": 5, "6248": 28 + 12}
BLOCK_RESUME = {"5586": 1075}


def lies_csv(pfad: Path) -> list[dict]:
    with open(pfad, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sprache(z: dict) -> str:
    sp = [s for s in ("de", "fr", "it", "rm") if z.get(f"anteil_title_{s}") and float(z[f"anteil_title_{s}"]) >= 0.10]
    return "/".join(sp) if sp else "unbekannt"


TEXT_SPALTEN = ("text_submitted", "text_reasoning", "text_response", "text_summary")


def text_affairs_in(keys: set[str]) -> list[tuple[str, str, str]]:
    """R2 (v2): affairs of these parliaments with a structured text: (affair_id, body_key, columns)."""
    out = []
    with gzip.open(AN / "ech/geschaefte_merkmale.csv.gz", "rt", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        kopf = next(r)
        idx = {name: i for i, name in enumerate(kopf)}
        for z in r:
            if z[idx["body_key"]] in keys:
                spalten = [c for c in TEXT_SPALTEN if z[idx[c]] == "1"]
                if spalten:
                    out.append((z[idx["affair_id"]], z[idx["body_key"]], "+".join(spalten)))
    return out


def entwicklungs_parlamente() -> set[str]:
    """R7: parliaments of all development documents."""
    import json
    keys = {z["body_key"] for z in lies_csv(AN / "pdf/augenschein.csv")}
    for p in sorted((DATA / "beispiele").glob("*/*.jsonl")):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                k = json.loads(zeile).get("body_key")
                if k:
                    keys.add(k)
    return keys


def duplikate(rolle_von: dict[str, str]) -> int:
    """R8: texts (text_md5, at least 100 characters) in more than one set. Copies in the test set and
    in the validation set go to split_ausschluss_duplikate.csv. Order of priority: training keeps,
    then validation, then test."""
    rang = {T: 0, V: 1, G: 2}
    gruppen = collections.defaultdict(list)
    with gzip.open(AN / "dokumente/dokumente_merkmale.csv.gz", "rt", newline="", encoding="utf-8") as f:
        for z in csv.DictReader(f):
            md5 = z.get("text_md5") or ""
            if not md5 or int(z.get("zeichen_nows") or 0) < 100:
                continue
            rolle = rolle_von.get(z["body_key"])
            if rolle:
                gruppen[md5].append((rang[rolle], z["id"], z["body_key"], rolle))
    aus = []
    for md5, eintraege in gruppen.items():
        rollen = {e[0] for e in eintraege}
        if len(rollen) < 2:
            continue
        beste = min(rollen)
        aus += [(md5, i, b, r) for rg, i, b, r in eintraege if rg > beste]
    with open(AUSDIR / "split_ausschluss_duplikate.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text_md5", "doc_id", "body_key", "rolle"])
        w.writerows(sorted(aus, key=lambda x: (x[3], x[2], x[1])))
    return len(aus)


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    AUSDIR.mkdir(parents=True, exist_ok=True)
    korpus = {z["body_key"]: z for z in lies_csv(AN / "korpus/parlamente.csv")}
    doks = {z["body_key"]: z for z in lies_csv(AN / "dokumente/parlamente.csv")}
    rollen_dok = collections.defaultdict(dict)
    for z in lies_csv(AN / "dokumente/verteilung_rolle.csv"):
        rollen_dok[z["body_key"]][z["wert"]] = int(z["anzahl"])
    texte = {z["body_key"]: z for z in lies_csv(AN / "texte/profil_parlamente.csv")}
    pilot = {z["body_key"]: z for z in lies_csv(AUSDIR / "pilot_kandidaten_je_parlament.csv")}

    # Silber-Labels je Parlament aus geschaefte_merkmale (doppelte Spaltennamen positionsweise lesen)
    spalten = ["typ_ech_exakt_nah", "empfehlung", "entscheid", "sponsor_sicher", "eingereicht_ereignis",
               "responder"]
    silber = collections.defaultdict(collections.Counter)
    with gzip.open(AN / "ech/geschaefte_merkmale.csv.gz", "rt", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        kopf = next(r)
        # bei doppelten Namen gilt das letzte Vorkommen (0/1-Flag)
        idx = {n: i for i, n in enumerate(kopf)}
        for z in r:
            k = z[idx["body_key"]]
            p = z[idx["pdf_text"]] == "1"
            silber[k]["geschaefte"] += 1
            silber[k]["pdf_text"] += p
            for s in spalten:
                if z[idx[s]] == "1" and p:
                    silber[k][s] += 1

    # ---------- R1 ----------
    fehlt = sorted(set(korpus) - set(ZUTEILUNG))
    zuviel = sorted(set(ZUTEILUNG) - set(korpus))
    if fehlt or zuviel:
        sys.exit(f"R1 verletzt: ohne Rolle {fehlt}, ohne Geschaefte {zuviel}")

    relevante_texte = {k for k, z in texte.items()
                       if int(z["n_geschaefte_eingereicht"] or 0) + int(z["n_geschaefte_begruendung"] or 0)
                       + int(z["n_geschaefte_antwort"] or 0) > 0}

    zeilen = []
    for k, z in korpus.items():
        rolle, grund = ZUTEILUNG[k]
        d = doks.get(k, {})
        t = texte.get(k)
        zeilen.append({
            "body_key": k, "name_de": z["name_de"], "ebene": z["ebene"], "sprache": sprache(z),
            "rolle": rolle, "begruendung": grund,
            "geschaefte": int(z["anzahl_geschaefte"]),
            "geschaefte_mit_pdf_text": silber[k]["pdf_text"],
            "anteil_scan_verdacht": d.get("anteil_scan_ja_von_bewertbar", ""),
            "texts_datei": "ja" if t else "nein",
            "texts_zu_vorstoessen": "ja" if k in relevante_texte else "nein",
            "pilot_kandidaten": int(pilot[k]["kandidaten"]) if k in pilot else 0,
            "typ_label_pdf": silber[k]["typ_ech_exakt_nah"],
            "empfehlung_pdf": silber[k]["empfehlung"],
            "entscheid_pdf": silber[k]["entscheid"],
            "dok_vorstoss": rollen_dok[k].get("vorstoss_eingereicht", 0),
            "dok_antwort": rollen_dok[k].get("antwort_exekutive", 0),
        })
    ordnung = {"Bund": 0, "Kanton": 1, "Gemeinde": 2, "Liechtenstein": 3}
    rang = {T: 0, V: 1, G: 2}
    zeilen.sort(key=lambda r: (rang[r["rolle"]], ordnung[r["ebene"]], r["sprache"], -r["geschaefte"]))

    # ---------- R2-R6 ----------
    gold_keys = {r["body_key"] for r in zeilen if r["rolle"] == G}
    r2 = text_affairs_in(gold_keys)
    with open(AUSDIR / "split_ausschluss_texte.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["affair_id", "body_key", "texte"])
        w.writerows(sorted(r2, key=lambda x: (x[1], x[0])))
    if any("summary" not in t or "+" in t for _, _, t in r2):
        sys.exit("R2 verletzt: Testgeschaefte mit eingereichtem Text, Begruendung oder Antwort")
    if any(r["rolle"] == G for r in zeilen if r["body_key"] in relevante_texte):
        sys.exit("R3 verletzt")
    for rolle in (T, V, G):
        rr = [r for r in zeilen if r["rolle"] == rolle]
        eb = {r["ebene"] for r in rr}
        sp = {s for r in rr for s in r["sprache"].split("/")}
        if not {"Kanton", "Gemeinde"} <= eb or not {"de", "fr", "it"} <= sp:
            sys.exit(f"R4 verletzt fuer {rolle}: Ebenen {eb}, Sprachen {sp}")
    pk = collections.Counter()
    for r in zeilen:
        pk[r["rolle"]] += r["pilot_kandidaten"]
    for spalte in ("empfehlung_pdf", "typ_label_pdf"):
        n_v = sum(1 for r in zeilen if r["rolle"] == V and r[spalte] >= 20)
        if n_v < 3:
            sys.exit(f"R5 verletzt: {spalte} nur in {n_v} Validierungsparlamenten mit mindestens 20 Labels")
    entw = entwicklungs_parlamente()
    verletzt = sorted(entw & gold_keys)
    if verletzt:
        sys.exit(f"R7 verletzt: Entwicklungsdokumente aus Testparlamenten {verletzt}")
    n = len(zeilen)
    for rolle in (V, G):
        if sum(r["rolle"] == rolle for r in zeilen) > 0.3 * n:
            sys.exit(f"R6 verletzt: {rolle}")

    with open(AUSDIR / "split.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()))
        w.writeheader()
        w.writerows(zeilen)

    # ---------- R8 ----------
    rolle_von = {r["body_key"]: r["rolle"] for r in zeilen}
    n_aus = duplikate(rolle_von)
    # ---------- R9 ----------
    ohne = sorted(set(doks) - set(korpus))
    with open(AUSDIR / "split_ohne_geschaefte.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["body_key", "name_de", "dokumente", "pdf", "status"])
        for k in ohne:
            w.writerow([k, doks[k].get("name_de", ""), doks[k].get("dokumente", ""), doks[k].get("pdf", ""),
                        "outside the split (no affairs)"])

    # ---------- Schichten ----------
    sch = collections.defaultdict(lambda: collections.Counter())
    for r in zeilen:
        key = (r["ebene"], r["sprache"])
        sch[key][(r["rolle"], "p")] += 1
        sch[key][(r["rolle"], "g")] += r["geschaefte"]
    with open(AUSDIR / "split_schichten.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ebene", "sprache", "parlamente_training", "parlamente_validierung", "parlamente_gold",
                    "geschaefte_training", "geschaefte_validierung", "geschaefte_gold"])
        for key in sorted(sch, key=lambda x: (ordnung[x[0]], x[1])):
            c = sch[key]
            w.writerow(list(key) + [c[(x, "p")] for x in (T, V, G)] + [c[(x, "g")] for x in (T, V, G)])
        w.writerow(["alle", "alle"] + [sum(r["rolle"] == x for r in zeilen) for x in (T, V, G)]
                   + [sum(r["geschaefte"] for r in zeilen if r["rolle"] == x) for x in (T, V, G)])

    # ---------- Silber je Rolle ----------
    def wert(k: str, quelle: str) -> int:
        if quelle == "pilot":
            return int(pilot[k]["kandidaten"]) if k in pilot else 0
        if quelle == "block":
            return BLOCK.get(k, 0)
        if quelle == "block_resume":
            return BLOCK_RESUME.get(k, 0)
        if quelle.startswith("dok:"):
            return rollen_dok[k].get(quelle[4:], 0)
        return silber[k][quelle]

    with open(AUSDIR / "silber_je_rolle.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["aufgabe", "einheit", "training", "validierung", "gold",
                    "parlamente_training", "parlamente_validierung", "parlamente_gold",
                    "parlamente_ab_20_training", "parlamente_ab_20_validierung", "parlamente_ab_20_gold"])
        for name, einheit, quelle in AUFGABEN:
            summe = collections.Counter()
            parl = collections.Counter()
            parl20 = collections.Counter()
            for r in zeilen:
                x = wert(r["body_key"], quelle)
                summe[r["rolle"]] += x
                parl[r["rolle"]] += x > 0
                parl20[r["rolle"]] += x >= 20
            w.writerow([name, einheit] + [summe[x] for x in (T, V, G)] + [parl[x] for x in (T, V, G)]
                       + [parl20[x] for x in (T, V, G)])

    for rolle in (T, V, G):
        rr = [r for r in zeilen if r["rolle"] == rolle]
        print(f"{rolle}: {len(rr)} Parlamente, {sum(r['geschaefte'] for r in rr)} Geschaefte, "
              f"Pilot-Kandidaten {pk[rolle]}")
    print(f"R2: {len(r2)} Geschaefte mit Zusammenfassung aus dem Test ausgeschlossen "
          f"({collections.Counter(b for _, b, _ in r2)})")
    print(f"R7: {len(entw)} Parlamente mit Entwicklungsdokumenten, keines im Test")
    print(f"R8: {n_aus} Dokumente als Duplikate aus Test und Validierung ausgeschlossen")
    print(f"R9: {len(ohne)} Parlamente ohne Geschaefte ausserhalb der Aufteilung")
    print("Regeln R1-R9 erfuellt")


if __name__ == "__main__":
    main()

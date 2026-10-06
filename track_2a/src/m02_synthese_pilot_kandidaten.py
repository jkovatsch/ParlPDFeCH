# SPDX-License-Identifier: Apache-2.0
"""Synthese Phase 2: Kandidaten fuer den Mini-Pilot (Iteration 1, Aufgabe Geschaeftstyp).

Liest die Merkmalstabelle der Dokumente (<data>/analyse/dokumente/dokumente_merkmale.csv.gz, aus
src/m02_dokumente_extrakt.py), dazu bodies und affairs aus <data>/roh/exports/. Es wird kein
Volltext gelesen; die Datei enthaelt nur Kennungen und Zaehlwerte.

Ein Dokument ist Kandidat, wenn alle Filter F1-F8 greifen und sein Geschaeft ein eindeutiges
Label L1-L3 hat. Jede Verwerfung wird mit dem ersten verletzten Filter gezaehlt.

Der Split (m02_synthese_split.py) liest von diesen Ausgaben nur die Zahl der Kandidaten je
Parlament (pilot_kandidaten_je_parlament.csv).

Filter (in dieser Reihenfolge):
  F1 Rolle der Dokumentkategorie = vorstoss_eingereicht (Heuristik rolle() aus
     m02_dokumente_profil.py: harmonisiert submitted_text oder Stichwortregeln auf category_*)
  F2 PDF (format_gruppe pdf oder pdf_laut_url, wie in 2.3)
  F3 affair_id gesetzt und im affairs-Export vorhanden
  F4 Textklasse text (nicht leer, kein Fehlermarker, kein Platzhalter; Regel aus 2.3)
  F5 kein Scan-Verdacht: Dateigroesse bekannt und >= 1 Zeichen ohne Leerraum pro KB
  F6 mindestens 200 Zeichen ohne Leerraum (wie PDF-Index in 2.5)
  F7 derselbe Text (text_md5) haengt an genau einem Geschaeft
  F8 ein Dokument pro Geschaeft (kleinste Dokument-ID)

Label (nur eindeutige Zuordnungen harmonisierter Typen):
  L1 type_harmonized_id in LABEL_HARM: 2 Motion -> motion, 3 Postulat -> postulate,
     8 Interpellation -> interpellation, 12 Anfrage -> request, 10 Fragestunde -> question,
     4 Parlamentarische Initiative -> parliamentary_initiative; 11 Petition, 7 Volksinitiative,
     6 Wahl, 14 Einbuergerung, 16 Bericht, 5 Vernehmlassung, 15 Informationsdokument ->
     keine (Option «Keine der Optionen passt»). Nicht verwendet: 9 Regierungsgeschaeft und
     17 Genehmigungsbeschluss (draft_decree nur «weiter»), 1 Diverses, 13 Ergaenzungsantrag,
     leer.
  L2 Das Paar (Parlament, lokale Bezeichnung) ist im ganzen Parlament auf genau einen
     harmonisierten Wert abgebildet (kein Eintrag wie in typen_lokal_uneinheitlich.csv).
  L3 Die lokale Regel typ_lokal() aus m02_ech_regeln.py widerspricht nicht: gleicher eCH-Wert
     mit Match exakt oder nah, oder lokale Bezeichnung unbestimmt/leer. Fuer «keine»: lokale
     Regel ebenfalls keine oder unbestimmt.

Ausgaben nach <data>/analyse/synthese/:
  pilot_kandidaten.csv.gz          eine Zeile pro Kandidat (nur Kennungen und Zahlen)
  pilot_kandidaten_je_parlament.csv Kandidaten je Parlament und Label
  pilot_verwerfung.csv             Verwerfungen je Parlament und Filter
  pilot_keine_zusatz_je_parlament.csv  nur gezaehlt: Geschaefte mit Label «keine» (L1-L3) und einem
                                   PDF beliebiger Kategorie, das F2-F7 erfuellt (Zusatzquelle fuer
                                   eine spaetere Iteration)

Aufruf (im Ordner track_2a): uv run python src/m02_synthese_pilot_kandidaten.py
"""

from __future__ import annotations

import collections
import csv
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import m02_ech_regeln as R  # noqa: E402
from m02_dokumente_profil import (FEHL_MD5, PLATZHALTER_MAXLEN, PLATZHALTER_MIN, SCAN_SCHWELLE,  # noqa: E402
                                  format_gruppe, rolle)
from m03_iso_paths import DATA, rel  # noqa: E402,F401
EXPORTE = DATA / "roh/exports"
MERKMALE = DATA / "analyse/dokumente/dokumente_merkmale.csv.gz"
AUSDIR = DATA / "analyse/synthese"

MIN_NOWS = 200

LABEL_HARM = {
    2: "motion", 3: "postulate", 8: "interpellation", 12: "request", 10: "question",
    4: "parliamentary_initiative",
    11: "keine", 7: "keine", 6: "keine", 14: "keine", 16: "keine", 5: "keine", 15: "keine",
}

FILTER = ["F1_rolle", "F2_pdf", "F3_geschaeft", "F4_textklasse", "F5_scan", "F6_mindestlaenge",
          "F7_text_mehrere_geschaefte", "F8_dublette_geschaeft",
          "L1_harm_typ_nicht_eindeutig", "L2_paar_uneinheitlich", "L3_lokal_widerspricht"]


def lies_ndjson(pfad: Path):
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for z in f:
            if z.strip():
                yield json.loads(z)


def ebene_von(body: dict, key: str) -> str:
    return R.ebene(key, body.get("type"))


def sprache_parlament(body: dict) -> str:
    langs = body.get("languages") or ""
    if "," in langs:
        return "mehrsprachig"
    return (body.get("lang") or "").lower() or "unbekannt"


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    AUSDIR.mkdir(parents=True, exist_ok=True)
    bodies = {b["body_key"]: b for b in lies_ndjson(EXPORTE / "bodies.ndjson.gz")}

    def organ(k: str, art: str) -> list[str]:
        b = bodies.get(k, {})
        return [b.get(f"{art}_name_{s}") or "" for s in ("de", "fr", "it")]

    # ---------- Geschaefte ----------
    aff = {}                                       # id -> (body, hid, lok)
    paar_harm = collections.defaultdict(set)       # (body, lok) -> {hid}
    for a in lies_ndjson(EXPORTE / "affairs.ndjson.gz"):
        lok = None
        for sp in ("de", "fr", "it", "rm"):
            if a.get(f"type_name_{sp}"):
                lok = a[f"type_name_{sp}"].strip()
                break
        hid = a.get("type_harmonized_id")
        aff[str(a["id"])] = (a["body_key"], hid, lok)
        paar_harm[(a["body_key"], lok)].add(hid)

    def label(aid: str) -> tuple[str, str]:
        """-> (label, Verwerfungsgrund oder '')"""
        bk, hid, lok = aff[aid]
        if hid not in LABEL_HARM:
            return "", "L1_harm_typ_nicht_eindeutig"
        if len(paar_harm[(bk, lok)]) != 1:
            return "", "L2_paar_uneinheitlich"
        lab = LABEL_HARM[hid]
        lw, la, _ = R.typ_lokal(lok)
        if la != "unbestimmt":
            if lab == "keine":
                if la != "keine":
                    return "", "L3_lokal_widerspricht"
            elif not (lw == lab and la in ("exakt", "nah")):
                return "", "L3_lokal_widerspricht"
        return lab, ""

    # ---------- Durchgang 1: Platzhalter und Mehrfachtexte ----------
    md5_n = collections.Counter()
    md5_min = {}
    md5_aff = collections.defaultdict(set)
    with gzip.open(MERKMALE, "rt", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["text_status"] != "ok":
                continue
            m = d["text_md5"]
            md5_n[m] += 1
            lg = int(d["textlaenge"])
            if lg < md5_min.get(m, 1 << 62):
                md5_min[m] = lg
            if d["affair_id"] and len(md5_aff[m]) < 3:
                md5_aff[m].add(d["affair_id"])

    def text_klasse(d) -> str:
        st = d["text_status"]
        if st == "none":
            return "kein_feld"
        if st == "leer":
            return "leer"
        if d["text_md5"] in FEHL_MD5:
            return "fehlgeschlagen"
        if md5_n[d["text_md5"]] >= PLATZHALTER_MIN and md5_min[d["text_md5"]] < PLATZHALTER_MAXLEN:
            return "platzhalter"
        return "text"

    # ---------- Durchgang 2: Filter ----------
    verw = collections.defaultdict(collections.Counter)    # body -> filter -> n
    zusatz = collections.defaultdict(set)                   # body -> Geschaefte (Zusatzquelle «keine»)
    roh = collections.Counter()                             # body -> Dokumente mit Rolle vorstoss
    rolle_cache = {}
    beste = {}                                             # affair_id -> Zeile (kleinste Dok-ID)
    with gzip.open(MERKMALE, "rt", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            k = d["body_key"]
            rk = (k, d["category_harmonized"], d["category_de"], d["category_fr"], d["category_it"],
                  d["kat_freitext_stichwort"])
            if rk not in rolle_cache:
                rolle_cache[rk] = rolle(d["category_harmonized"], d["category_de"], d["category_fr"],
                                        d["category_it"], organ(k, "executive"), organ(k, "legislative"),
                                        d["kat_freitext_stichwort"])
            if rolle_cache[rk][0] != "vorstoss_eingereicht":
                # Zusatzquelle fuer «keine» (nur gezaehlt, nicht im Pilot): beliebige Kategorie,
                # Geschaeft mit harmonisiertem Typ ohne eCH-Entsprechung, Filter F2-F7, Label L2/L3
                aid = d["affair_id"]
                if aid in aff and LABEL_HARM.get(aff[aid][1]) == "keine" \
                        and format_gruppe(d["format"], d["url_endung"]) in ("pdf", "pdf_laut_url") \
                        and text_klasse(d) == "text" and int(d["size"] or 0) > 0 \
                        and int(d["zeichen_nows"]) / (int(d["size"]) / 1024) >= SCAN_SCHWELLE \
                        and int(d["zeichen_nows"]) >= MIN_NOWS and len(md5_aff[d["text_md5"]]) == 1 \
                        and label(aid)[0] == "keine":
                    zusatz[k].add(aid)
                continue
            roh[k] += 1
            if format_gruppe(d["format"], d["url_endung"]) not in ("pdf", "pdf_laut_url"):
                verw[k]["F2_pdf"] += 1
                continue
            aid = d["affair_id"]
            if not aid or aid not in aff:
                verw[k]["F3_geschaeft"] += 1
                continue
            if text_klasse(d) != "text":
                verw[k]["F4_textklasse"] += 1
                continue
            size = int(d["size"] or 0)
            nows = int(d["zeichen_nows"])
            if size <= 0 or nows / (size / 1024) < SCAN_SCHWELLE:
                verw[k]["F5_scan"] += 1
                continue
            if nows < MIN_NOWS:
                verw[k]["F6_mindestlaenge"] += 1
                continue
            if len(md5_aff[d["text_md5"]]) > 1:
                verw[k]["F7_text_mehrere_geschaefte"] += 1
                continue
            alt = beste.get(aid)
            if alt is not None:
                verw[k]["F8_dublette_geschaeft"] += 1
                if int(d["id"]) >= int(alt["id"]):
                    continue
            beste[aid] = d

    # ---------- Label ----------
    kand = []
    for aid, d in beste.items():
        k = d["body_key"]
        lab, grund = label(aid)
        if grund:
            verw[k][grund] += 1
            continue
        b = bodies.get(k, {})
        lang_dok = (d["language"] or "").lower()
        sp_p = sprache_parlament(b)
        sprache = lang_dok if lang_dok in ("de", "fr", "it", "rm") else (
            sp_p if sp_p in ("de", "fr", "it") else "unbekannt")
        _, hid, lok = aff[aid]
        lw, la, _ = R.typ_lokal(lok)
        kand.append({
            "doc_id": d["id"], "datei_key": d["datei_key"], "affair_id": aid, "body_key": k,
            "ebene": ebene_von(b, k),
            "sprache_parlament": sp_p, "sprache": sprache, "label": lab,
            "type_harmonized_id": hid, "lokal_ech": lw, "lokal_match": la,
            "textlaenge": d["textlaenge"], "zeichen_nows": d["zeichen_nows"], "size": d["size"],
            "text_md5": d["text_md5"],
        })
    kand.sort(key=lambda r: (r["body_key"], int(r["doc_id"])))

    spalten = list(kand[0].keys())
    with gzip.open(AUSDIR / "pilot_kandidaten.csv.gz", "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=spalten)
        w.writeheader()
        w.writerows(kand)

    labels = ["motion", "postulate", "interpellation", "request", "question", "parliamentary_initiative",
              "keine"]
    je = collections.defaultdict(collections.Counter)
    for r in kand:
        je[r["body_key"]][r["label"]] += 1
    with open(AUSDIR / "pilot_kandidaten_je_parlament.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["body_key", "name_de", "ebene", "sprache_parlament", "dok_rolle_vorstoss",
                    "kandidaten"] + labels)
        for k in sorted(set(roh) | set(je)):
            b = bodies.get(k, {})
            w.writerow([k, b.get("name_de", ""), ebene_von(b, k), sprache_parlament(b), roh[k],
                        sum(je[k].values())] + [je[k][x] for x in labels])
        w.writerow(["GESAMT", "", "", "", sum(roh.values()), len(kand)]
                   + [sum(je[k][x] for k in je) for x in labels])

    with open(AUSDIR / "pilot_verwerfung.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["body_key", "dok_rolle_vorstoss"] + FILTER + ["kandidaten"])
        for k in sorted(roh):
            w.writerow([k, roh[k]] + [verw[k][x] for x in FILTER] + [sum(je[k].values())])
        w.writerow(["GESAMT", sum(roh.values())] + [sum(verw[k][x] for k in verw) for x in FILTER]
                   + [len(kand)])

    with open(AUSDIR / "pilot_keine_zusatz_je_parlament.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["body_key", "geschaefte_keine_mit_pdf_text"])
        for k in sorted(zusatz):
            w.writerow([k, len(zusatz[k])])
        w.writerow(["GESAMT", sum(len(v) for v in zusatz.values())])

    print(f"Zusatzquelle «keine» (andere Kategorien): {sum(len(v) for v in zusatz.values())} Geschaefte "
          f"in {len(zusatz)} Parlamenten")
    print(f"Dokumente mit Rolle vorstoss_eingereicht: {sum(roh.values())} in {len(roh)} Parlamenten")
    print(f"Kandidaten: {len(kand)} in {sum(1 for k in je if je[k])} Parlamenten")
    tot = collections.Counter(r["label"] for r in kand)
    print("je Label:", dict(tot))
    print("Verwerfung gesamt:", {x: sum(verw[k][x] for k in verw) for x in FILTER})


if __name__ == "__main__":
    main()

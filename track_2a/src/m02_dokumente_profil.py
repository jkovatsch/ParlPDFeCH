# SPDX-License-Identifier: Apache-2.0
"""2.3 Dokument-Profil, Schritt 2: Kennzahlen, Kategorien, Scan-Schaetzung, Abdeckung, Stichprobe.

Liest die Merkmalstabelle aus src/m02_dokumente_extrakt.py (eine Zeile pro Dokument, ohne Volltext)
sowie bodies, affairs und agendas aus <data>/roh/exports/ und schreibt Tabellen nach
<data>/analyse/dokumente/.

Begriffe:

- PDF: format (klein) ist application/pdf oder pdf, oder format ist leer/application/octet-stream
  und die Quell-URL endet auf .pdf.
- text_klasse: kein_feld (text null), leer (nur Leerraum), fehlgeschlagen (Marker
  «[extraction_failed…]»), platzhalter (identischer normalisierter Text in >= PLATZHALTER_MIN
  Dokumenten, kuerzester Rohtext der Gruppe unter PLATZHALTER_MAXLEN Zeichen; Schaetzung),
  text (alles andere).
- Scan-Verdacht (nur PDF): ja, wenn text_klasse leer ist oder Zeichen ohne Leerraum pro KB
  Dateigroesse < SCAN_SCHWELLE; nein, wenn text_klasse text und Dichte >= Schwelle;
  unbekannt sonst (kein Text-Feld, Extraktion fehlgeschlagen, Platzhalter, Groesse fehlt).
- Rolle einer Kategorie: harmonisierte Kategorie, wo eindeutig, sonst Stichwortregeln auf
  category_de/fr/it (ROLLE_* aus m02_dokumente_extrakt.py). Heuristik, keine amtliche Zuordnung.

Aufruf (im Ordner track_2a): uv run python src/m02_dokumente_profil.py
"""

from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

from m02_dokumente_extrakt import (KATEGORIE_MASKE, ROLLE_ANTWORT, ROLLE_ANTWORT_BERICHT, ROLLE_AUSNAHME,
                                   ROLLE_EXEKUTIVBESCHLUSS, ROLLE_VORSTOSS)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, rel  # noqa: E402,F401
EXPORTE = DATA / "roh/exports"
AUSDIR = DATA / "analyse/dokumente"
MERKMALE = AUSDIR / "dokumente_merkmale.csv.gz"

SCAN_SCHWELLE = 1.0                      # Zeichen ohne Leerraum pro KB
SENSITIVITAET = [0.25, 0.5, 1.0, 2.0, 4.0]
PLATZHALTER_MIN = 20
PLATZHALTER_MAXLEN = 5000
STICHPROBE_N = 300
STICHPROBE_SEED = 42
STICHPROBE_MIN_SCHICHT = 3
KATEGORIE_MIN_DOKS = 5

FEHL_MD5 = {hashlib.md5(s.encode()).hexdigest()[:16]
            for s in ("[extraction_failed]", "[extraction_failed:unsupported_format]")}

# harmonisierte Kategorien mit eindeutiger Rolle
HARM_ROLLE = {
    "submitted_text": "vorstoss_eingereicht",
    "response_text": "antwort_exekutive",
    "government_resolution": "exekutivbeschluss",
}
# harmonisierte Kategorien, die sicher weder Vorstoss noch Antwort sind
HARM_ANDERE = {
    "agenda", "protocol", "protocol_decision", "protocol_verbatim", "protocol_short", "voting",
    "voting_result", "opinionHasDraftRelatedDocument", "opinionIsAboutDraftDocument", "image",
    "recording_video", "recording_audio", "recording", "affairs_directory", "invitation",
    "work_schedule", "press_release", "media_release", "signature_list", "participant_list",
    "seating_plan", "opening_speech", "committee_allocations", "agenda_preview", "speaker_list",
    "open_data", "preview", "invitee_list", "wording_initiative", "proces_verbal",
    "commission_report", "rapport_commission", "council_report", "preavis", "decision",
}


def lies_ndjson(pfad: Path):
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for z in f:
            if z.strip():
                yield json.loads(z)


def schreibe(name: str, kopf: list[str], zeilen) -> None:
    with open(AUSDIR / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(kopf)
        for z in zeilen:
            w.writerow(z)


def anteil(a: int, b: int) -> str:
    return f"{a / b:.4f}" if b else ""


def median(xs) -> str:
    xs = list(xs)
    return f"{statistics.median(xs):.1f}" if xs else ""


def ist_pdf(fmt: str, endung: str) -> bool:
    f = fmt.lower()
    return f in ("application/pdf", "pdf") or (f in ("", "application/octet-stream") and endung == "pdf")


def format_gruppe(fmt: str, endung: str) -> str:
    f = fmt.lower()
    if ist_pdf(fmt, endung):
        return "pdf" if f in ("application/pdf", "pdf") else "pdf_laut_url"
    if f == "":
        return "unbekannt"
    if "html" in f:
        return "html"
    if f.startswith("image") or f in ("jpg", "jpeg", "png", "webp", "gif", "tif", "tiff"):
        return "bild"
    if f.startswith(("video", "audio")) or f in ("vimeo",):
        return "audio_video"
    if "word" in f or "msword" in f or "spreadsheet" in f or "excel" in f or "rtf" in f \
            or "presentation" in f or "opendocument" in f:
        return "office"
    if "zip" in f:
        return "zip"
    if f == "link":
        return "link"
    return "andere"


def rolle(harm: str, de: str, fr: str, it: str, exek_namen: list[str], leg_namen: list[str],
          stw_maskiert: str = "") -> tuple[str, str]:
    """liefert (rolle, quelle)"""
    if harm in HARM_ROLLE:
        return HARM_ROLLE[harm], "harmonisiert"
    if harm in HARM_ANDERE:
        return "andere", "harmonisiert"
    teile = [x for x in (de, fr, it) if x and x != KATEGORIE_MASKE]
    s = " | ".join(teile).lower()
    if not s:
        if KATEGORIE_MASKE in (de, fr, it):
            # nur Dateiname/Freitext im Kategoriefeld: Rolle aus der Extraktion (Stichwort im maskierten Wert)
            return (stw_maskiert or "andere"), "stichwort_dateiname"
        return "ohne_kategorie", "-"
    q = "stichwort"
    if ROLLE_AUSNAHME.search(s):
        return "andere", q
    if ROLLE_ANTWORT.search(s) or ROLLE_ANTWORT_BERICHT.search(s):
        return "antwort_exekutive", q
    if ROLLE_EXEKUTIVBESCHLUSS.search(s):
        return "exekutivbeschluss", q
    if "beschluss" in s or "décision" in s or "decisione" in s:
        # Organname aus bodies: Beschluss der Exekutive oder des Parlaments
        if any(n and n.lower() in s for n in exek_namen) and not any(n and n.lower() in s for n in leg_namen):
            return "exekutivbeschluss", q + "+organ"
    if ROLLE_VORSTOSS.search(s):
        return "vorstoss_eingereicht", q
    return "andere", q


def kategorie_label(de: str, fr: str, it: str) -> str:
    # Dateinamen/Freitexte sind bereits in der Extraktion maskiert; Laengenbegrenzung als Sicherung
    return " | ".join(x if len(x) <= 80 else KATEGORIE_MASKE for x in (de, fr, it))


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    # ---------- Stammdaten ----------
    bodies = {}
    for b in lies_ndjson(EXPORTE / "bodies.ndjson.gz"):
        bodies[b["body_key"]] = b

    def ebene(k: str) -> str:
        if k == "CHE":
            return "Bund"
        if k == "LIE":
            return "FL"
        t = bodies.get(k, {}).get("type")
        return {"canton": "Kanton", "city": "Gemeinde", "municipality": "Gemeinde"}.get(t, "?")

    def sprache_body(k: str) -> str:
        b = bodies.get(k, {})
        langs = b.get("languages")
        if langs and "," in langs:
            return ""
        return (b.get("lang") or "").lower()

    def organ_namen(k: str, art: str) -> list[str]:
        b = bodies.get(k, {})
        return [b.get(f"{art}_name_{s}") or "" for s in ("de", "fr", "it")]

    affair_body = {}
    for a in lies_ndjson(EXPORTE / "affairs.ndjson.gz"):
        affair_body[str(a["id"])] = a["body_key"]
    agenda_affair = {}
    for g in lies_ndjson(EXPORTE / "agendas.ndjson.gz"):
        if g.get("item_affair_id") is not None:
            agenda_affair[str(g["id"])] = str(g["item_affair_id"])

    # ---------- Durchgang 1: Haeufigkeit identischer Texte ----------
    md5_n = collections.Counter()
    md5_min = {}                                # kuerzeste Rohtextlaenge je Gruppe gleicher Texte
    with gzip.open(MERKMALE, "rt", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["text_status"] == "ok":
                md5_n[d["text_md5"]] += 1
                lg = int(d["textlaenge"])
                if lg < md5_min.get(d["text_md5"], 1 << 62):
                    md5_min[d["text_md5"]] = lg

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

    # ---------- Durchgang 2: Aggregation ----------
    pro = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    tl = collections.defaultdict(list)          # (body, 'alle'|'pdf') -> Textlaengen (text_klasse text)
    kb = collections.defaultdict(list)          # body -> KB pro PDF
    dichte = collections.defaultdict(list)      # body -> Zeichen/KB pro PDF (text/leer, Groesse bekannt)
    scan = collections.defaultdict(collections.Counter)
    sens = collections.defaultdict(collections.Counter)
    hist = collections.Counter()
    aff_dok, aff_pdf, aff_pdf_text, aff_pdf_ind = set(), set(), set(), set()
    aff_rolle = collections.defaultdict(set)
    waisen = collections.Counter()
    harm_stat = collections.defaultdict(lambda: collections.Counter())
    harm_tl = collections.defaultdict(list)
    harm_bodies = collections.defaultdict(collections.Counter)
    lok_stat = collections.defaultdict(lambda: collections.Counter())
    lok_tl = collections.defaultdict(list)
    lok_harm = collections.defaultdict(collections.Counter)
    rolle_cache = {}
    pdf_pool = []
    mehr_body = collections.defaultdict(collections.Counter)
    mehr_len, mehr_klasse = {}, {}

    with gzip.open(MERKMALE, "rt", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            k = d["body_key"]
            fg = format_gruppe(d["format"], d["url_endung"])
            pdf = fg in ("pdf", "pdf_laut_url")
            tk = text_klasse(d)
            p = pro[k]
            p["n"]["dok"] += 1
            p["parent_type"][d["parent_type"] or "(leer)"] += 1
            p["format_gruppe"][fg] += 1
            p["format_roh"][d["format"] or "(leer)"] += 1
            p["language"][d["language"] or "(leer)"] += 1
            p["text_klasse"][tk] += 1
            p["kat"]["lokal" if (d["category_de"] or d["category_fr"] or d["category_it"]) else "ohne_lokal"] += 1
            p["kat"]["harm" if d["category_harmonized"] else "ohne_harm"] += 1
            if tk == "text":
                tl[(k, "alle")].append(int(d["textlaenge"]))
            if d["text_status"] == "ok" and md5_n[d["text_md5"]] >= PLATZHALTER_MIN:
                mehr_body[d["text_md5"]][k] += 1
                mehr_len[d["text_md5"]] = md5_min[d["text_md5"]]
                mehr_klasse[d["text_md5"]] = tk
            # Rolle
            rk = (k, d["category_harmonized"], d["category_de"], d["category_fr"], d["category_it"],
                  d["kat_freitext_stichwort"])
            if rk not in rolle_cache:
                rolle_cache[rk] = rolle(d["category_harmonized"], d["category_de"], d["category_fr"],
                                        d["category_it"], organ_namen(k, "executive"),
                                        organ_namen(k, "legislative"), d["kat_freitext_stichwort"])
            ro, rq = rolle_cache[rk]
            p["rolle"][ro] += 1
            # Kategorien
            hk = d["category_harmonized"] or "(leer)"
            hs = harm_stat[hk]
            hs["dok"] += 1
            hs["pdf"] += pdf
            hs["text"] += tk == "text"
            harm_bodies[hk][k] += 1
            if tk == "text":
                hs["m_antwort"] += int(d["m_antwort"])
                hs["m_einreichung"] += int(d["m_einreichung"])
                hs["m_auftrag"] += int(d["m_auftrag"])
                harm_tl[hk].append(int(d["textlaenge"]))
            lk = (k, kategorie_label(d["category_de"], d["category_fr"], d["category_it"]))
            ls = lok_stat[lk]
            ls["dok"] += 1
            ls["pdf"] += pdf
            ls["text"] += tk == "text"
            ls[("rolle", ro, rq)] += 1
            lok_harm[lk][hk] += 1
            if tk == "text":
                ls["m_antwort"] += int(d["m_antwort"])
                ls["m_einreichung"] += int(d["m_einreichung"])
                ls["m_auftrag"] += int(d["m_auftrag"])
                lok_tl[lk].append(int(d["textlaenge"]))
            # Geschaefte
            aid = d["affair_id"]
            if aid:
                if aid not in affair_body:
                    waisen[k] += 1
                aff_dok.add(aid)
                if ro in ("vorstoss_eingereicht", "antwort_exekutive", "exekutivbeschluss"):
                    aff_rolle[ro].add(aid)
            ind = agenda_affair.get(d["agenda_id"]) if d["agenda_id"] else None
            # PDF-spezifisch
            if not pdf:
                continue
            p["n"]["pdf"] += 1
            p["pdf_text_klasse"][tk] += 1
            if not d["url_oparl"]:
                p["n"]["pdf_ohne_url_oparl"] += 1
                if tk == "kein_feld":
                    p["n"]["pdf_kein_feld_ohne_url_oparl"] += 1
            size = int(d["size"] or 0)
            nows = int(d["zeichen_nows"])
            if size > 0:
                kb[k].append(size / 1024)
            if tk == "text":
                tl[(k, "pdf")].append(int(d["textlaenge"]))
            x = None
            if tk == "leer":
                sv = "ja"
                if size > 0:
                    x = 0.0
            elif tk == "text" and size > 0:
                x = nows / (size / 1024)
                sv = "ja" if x < SCAN_SCHWELLE else "nein"
            else:
                sv = "unbekannt"
            if x is not None:
                dichte[k].append(x)
                hist[-99 if x == 0 else math.floor(math.log10(x) * 4) / 4] += 1
                for s in SENSITIVITAET:
                    sens[k][(s, x < s)] += 1
            elif tk == "leer":
                for s in SENSITIVITAET:
                    sens[k][(s, True)] += 1
            scan[k][sv] += 1
            if sv == "ja":
                scan[k]["ja_text_leer" if tk == "leer" else "ja_dichte"] += 1
                if size and size < 30 * 1024:
                    scan[k]["ja_unter_30kb"] += 1
            if aid:
                aff_pdf.add(aid)
                if tk == "text" and sv == "nein":
                    aff_pdf_text.add(aid)
                aff_pdf_ind.add(aid)
            if ind:
                aff_pdf_ind.add(ind)
            # Stichproben-Grundgesamtheit: PDF mit Kopie bei OpenParlData, ohne bekannte Platzhalter
            if d["url_oparl"] and tk not in ("platzhalter", "fehlgeschlagen"):
                pdf_pool.append((d["id"], k, d["language"], d["category_de"], d["category_harmonized"],
                                 aid, d["url_oparl"], d["textlaenge"] if d["text_status"] != "none" else "",
                                 d["seiten"], sv))

    alle_keys = sorted(pro)
    GES = "GESAMT"

    def summe(feld: str) -> collections.Counter:
        c = collections.Counter()
        for k in alle_keys:
            c.update(pro[k][feld])
        return c

    # ---------- Tabelle: Parlamente ----------
    zeilen = []
    for k in alle_keys + [GES]:
        if k == GES:
            n = summe("n"); tkl = summe("text_klasse"); ptk = summe("pdf_text_klasse"); kat = summe("kat")
            tl_a = [v for (b, t), xs in tl.items() if t == "alle" for v in xs]
            tl_p = [v for (b, t), xs in tl.items() if t == "pdf" for v in xs]
            kbs = [v for xs in kb.values() for v in xs]
            di = [v for xs in dichte.values() for v in xs]
            sc = collections.Counter()
            for c in scan.values():
                sc.update(c)
            name, eb, kt = "alle Parlamente", "", ""
        else:
            p = pro[k]
            n, tkl, ptk, kat = p["n"], p["text_klasse"], p["pdf_text_klasse"], p["kat"]
            tl_a, tl_p, kbs, di, sc = tl[(k, "alle")], tl[(k, "pdf")], kb[k], dichte[k], scan[k]
            b = bodies.get(k, {})
            name, eb, kt = b.get("name_de") or "", ebene(k), b.get("canton_key") or ""
        bewertbar = sc["ja"] + sc["nein"]
        zeilen.append([
            k, name, eb, kt, n["dok"], n["pdf"], anteil(n["pdf"], n["dok"]),
            tkl["text"], anteil(tkl["text"], n["dok"]),
            n["dok"] - tkl["kein_feld"] - tkl["leer"], anteil(n["dok"] - tkl["kein_feld"] - tkl["leer"], n["dok"]),
            tkl["fehlgeschlagen"], tkl["platzhalter"],
            ptk["text"], anteil(ptk["text"], n["pdf"]), ptk["kein_feld"], ptk["leer"], ptk["fehlgeschlagen"],
            ptk["platzhalter"],
            median(tl_a), median(tl_p), median(kbs), median(di),
            sc["ja"], sc["nein"], sc["unbekannt"], anteil(sc["ja"], bewertbar),
            anteil(kat["lokal"], n["dok"]), anteil(kat["harm"], n["dok"]),
        ])
    schreibe("parlamente.csv", [
        "body_key", "name_de", "ebene", "kanton", "dokumente", "pdf", "anteil_pdf",
        "dok_text", "anteil_dok_text", "dok_text_roh_nicht_leer", "anteil_dok_text_roh_nicht_leer",
        "dok_extraktion_fehlgeschlagen", "dok_platzhalter",
        "pdf_text", "anteil_pdf_text", "pdf_kein_textfeld", "pdf_text_leer", "pdf_extraktion_fehlgeschlagen",
        "pdf_platzhalter",
        "median_textlaenge_dok", "median_textlaenge_pdf", "median_kb_pdf", "median_zeichen_pro_kb_pdf",
        "pdf_scan_ja", "pdf_scan_nein", "pdf_scan_unbekannt", "anteil_scan_ja_von_bewertbar",
        "anteil_mit_lokaler_kategorie", "anteil_mit_harmonisierter_kategorie",
    ], zeilen)

    # ---------- Tabellen: Verteilungen (lang) ----------
    for feld, datei in (("parent_type", "verteilung_parent_type.csv"), ("format_gruppe", "verteilung_format.csv"),
                        ("format_roh", "verteilung_format_roh.csv"), ("language", "verteilung_sprache.csv"),
                        ("text_klasse", "verteilung_text_klasse.csv"), ("rolle", "verteilung_rolle.csv")):
        z = []
        for k in alle_keys + [GES]:
            c = summe(feld) if k == GES else pro[k][feld]
            tot = sum(c.values())
            for w, a in c.most_common():
                z.append([k, ebene(k) if k != GES else "", w, a, anteil(a, tot)])
        schreibe(datei, ["body_key", "ebene", "wert", "anzahl", "anteil"], z)

    # Ebene x Verteilung
    z = []
    for feld in ("parent_type", "format_gruppe", "language", "text_klasse", "rolle"):
        agg = collections.defaultdict(collections.Counter)
        for k in alle_keys:
            agg[ebene(k)].update(pro[k][feld])
        for eb in sorted(agg):
            tot = sum(agg[eb].values())
            for w, a in agg[eb].most_common():
                z.append([feld, eb, w, a, anteil(a, tot)])
    schreibe("verteilung_nach_ebene.csv", ["merkmal", "ebene", "wert", "anzahl", "anteil"], z)

    # ---------- Kategorien ----------
    z = []
    gesamt_dok = sum(s["dok"] for s in harm_stat.values())
    for hk, s in sorted(harm_stat.items(), key=lambda x: -x[1]["dok"]):
        ro = HARM_ROLLE.get(hk, "andere" if hk in HARM_ANDERE else ("ohne_kategorie" if hk == "(leer)" else "gemischt"))
        z.append([hk, ro, s["dok"], anteil(s["dok"], gesamt_dok), s["pdf"], s["text"], median(harm_tl[hk]),
                  anteil(s["m_antwort"], s["text"]), anteil(s["m_einreichung"], s["text"]),
                  anteil(s["m_auftrag"], s["text"]), len(harm_bodies[hk]),
                  " ".join(f"{b}:{a}" for b, a in harm_bodies[hk].most_common(5))])
    schreibe("kategorien_harmonisiert.csv", [
        "category_harmonized", "rolle", "dokumente", "anteil_dokumente", "pdf", "mit_text", "median_textlaenge",
        "anteil_marker_antwort", "anteil_marker_einreichung", "anteil_marker_auftrag", "parlamente",
        "top_parlamente"], z)

    z = []
    selten = collections.Counter()
    for (k, lab), s in sorted(lok_stat.items(), key=lambda x: (-x[1]["dok"])):
        if lab == " |  | ":
            continue
        if s["dok"] < KATEGORIE_MIN_DOKS:
            selten[k] += s["dok"]
            continue
        rollen = collections.Counter({(r, q): v for key, v in s.items() if isinstance(key, tuple)
                                      for _, r, q in [key]})
        (ro, rq), _ = rollen.most_common(1)[0]
        harm = lok_harm[(k, lab)].most_common(1)[0][0]
        z.append([k, ebene(k), lab, harm, ro, rq, s["dok"], s["pdf"], s["text"], median(lok_tl[(k, lab)]),
                  anteil(s["m_antwort"], s["text"]), anteil(s["m_einreichung"], s["text"]),
                  anteil(s["m_auftrag"], s["text"])])
    for k, a in sorted(selten.items()):
        z.append([k, ebene(k), f"<seltene Kategorien mit < {KATEGORIE_MIN_DOKS} Dokumenten>", "", "", "", a,
                  "", "", "", "", "", ""])
    schreibe("kategorien_lokal.csv", [
        "body_key", "ebene", "kategorie_de_fr_it", "category_harmonized_haeufigste", "rolle", "rolle_quelle",
        "dokumente", "pdf", "mit_text", "median_textlaenge", "anteil_marker_antwort",
        "anteil_marker_einreichung", "anteil_marker_auftrag"], z)

    # Top-Kategorien gesamt (Label ueber Parlamente zusammengefasst)
    top = collections.defaultdict(lambda: [0, set(), collections.Counter()])
    for (k, lab), s in lok_stat.items():
        if lab == " |  | ":
            continue
        t = top[lab]
        t[0] += s["dok"]
        t[1].add(k)
        for key, v in s.items():
            if isinstance(key, tuple):
                t[2][key[1]] += v
    z = []
    for lab, (a, bs, rc) in sorted(top.items(), key=lambda x: -x[1][0])[:100]:
        if a < KATEGORIE_MIN_DOKS:
            break
        z.append([lab, a, anteil(a, gesamt_dok), len(bs), " ".join(sorted(bs)[:10]), rc.most_common(1)[0][0]])
    schreibe("kategorien_top.csv", ["kategorie_de_fr_it", "dokumente", "anteil_alle_dokumente", "parlamente",
                                     "parlamente_liste_max10", "rolle"], z)

    # ---------- Abdeckung Geschaefte ----------
    aff_n = collections.Counter(affair_body.values())

    def zaehle(ids):
        c = collections.Counter()
        for a in ids:
            b = affair_body.get(a)
            if b:
                c[b] += 1
        return c

    c_dok, c_pdf, c_pdft, c_ind = zaehle(aff_dok), zaehle(aff_pdf), zaehle(aff_pdf_text), zaehle(aff_pdf_ind)
    c_vor, c_ant = zaehle(aff_rolle["vorstoss_eingereicht"]), zaehle(aff_rolle["antwort_exekutive"])
    c_exb = zaehle(aff_rolle["exekutivbeschluss"])
    z = []
    for k in sorted(set(aff_n) | set(alle_keys)) + [GES]:
        if k == GES:
            vals = [sum(c.values()) for c in (aff_n, c_dok, c_pdf, c_pdft, c_ind, c_vor, c_ant, c_exb)]
            name, eb = "alle Parlamente", ""
            ws = sum(waisen.values())
        else:
            vals = [c[k] for c in (aff_n, c_dok, c_pdf, c_pdft, c_ind, c_vor, c_ant, c_exb)]
            name, eb = bodies.get(k, {}).get("name_de") or "", ebene(k)
            ws = waisen[k]
        n0 = vals[0]
        z.append([k, name, eb, n0, vals[1], anteil(vals[1], n0), vals[2], anteil(vals[2], n0),
                  vals[3], anteil(vals[3], n0), vals[4], anteil(vals[4], n0),
                  vals[5], anteil(vals[5], n0), vals[6], anteil(vals[6], n0), vals[7], anteil(vals[7], n0), ws])
    schreibe("abdeckung_geschaefte.csv", [
        "body_key", "name_de", "ebene", "geschaefte", "mit_dokument", "anteil_mit_dokument",
        "mit_pdf", "anteil_mit_pdf", "mit_pdf_text_ohne_scanverdacht", "anteil_mit_pdf_text_ohne_scanverdacht",
        "mit_pdf_inkl_traktandum", "anteil_mit_pdf_inkl_traktandum",
        "mit_vorstoss_dok", "anteil_mit_vorstoss_dok", "mit_antwort_dok", "anteil_mit_antwort_dok",
        "mit_exekutivbeschluss_dok", "anteil_mit_exekutivbeschluss_dok", "dok_mit_affair_id_ohne_geschaeft"], z)

    # ---------- Scan-Schwelle: Histogramm und Sensitivitaet ----------
    tot = sum(hist.values())
    kum = 0
    z = []
    for b in sorted(hist):
        kum += hist[b]
        if b == -99:
            z.append(["0 (kein Text)", "0", "0", hist[b], anteil(hist[b], tot), anteil(kum, tot)])
        else:
            z.append([f"{b:.2f}", f"{10 ** b:.4g}", f"{10 ** (b + 0.25):.4g}", hist[b], anteil(hist[b], tot),
                      anteil(kum, tot)])
    schreibe("scan_dichte_histogramm.csv", ["log10_untergrenze", "zeichen_pro_kb_von", "zeichen_pro_kb_bis",
                                            "pdf", "anteil", "kumuliert"], z)
    z = []
    for k in alle_keys + [GES]:
        c = collections.Counter()
        if k == GES:
            for v in sens.values():
                c.update(v)
        else:
            c = sens[k]
        row = [k, ebene(k) if k != GES else ""]
        for s in SENSITIVITAET:
            row += [c[(s, True)], anteil(c[(s, True)], c[(s, True)] + c[(s, False)])]
        z.append(row)
    kopf = ["body_key", "ebene"]
    for s in SENSITIVITAET:
        kopf += [f"scan_ja_schwelle_{s}", f"anteil_schwelle_{s}"]
    schreibe("scan_sensitivitaet.csv", kopf, z)

    # Ebene-Zusammenfassung Scan
    z = []
    agg = collections.defaultdict(collections.Counter)
    for k in alle_keys:
        agg[ebene(k)].update(scan[k])
    for eb, c in sorted(agg.items()):
        z.append([eb, c["ja"], c["nein"], c["unbekannt"], anteil(c["ja"], c["ja"] + c["nein"])])
    schreibe("scan_nach_ebene.csv", ["ebene", "pdf_scan_ja", "pdf_scan_nein", "pdf_scan_unbekannt",
                                      "anteil_scan_ja_von_bewertbar"], z)

    # Mehrfachtexte (nur Kennungen und Zaehler, kein Text)
    z = [[h, a, mehr_len[h], mehr_klasse[h], len(mehr_body[h]),
          " ".join(f"{b}:{c}" for b, c in mehr_body[h].most_common(3))]
         for h, a in md5_n.most_common() if a >= PLATZHALTER_MIN]
    schreibe("mehrfachtexte.csv", ["text_md5", "dokumente", "textlaenge_min", "text_klasse", "parlamente",
                                   "top_parlamente"], z)

    # ---------- Stichprobe ----------
    def sprache_eff(r) -> str:
        l = (r[2] or "").lower()
        if l in ("de", "fr", "it", "rm"):
            return l
        return sprache_body(r[1]) or "unbekannt"

    schichten = collections.defaultdict(list)
    for r in sorted(pdf_pool, key=lambda r: int(r[0])):
        schichten[(ebene(r[1]), sprache_eff(r))].append(r)
    keys = sorted(schichten)
    gew = {s: math.sqrt(len(schichten[s])) for s in keys}
    quote = {s: min(len(schichten[s]), STICHPROBE_MIN_SCHICHT) for s in keys}
    rest = STICHPROBE_N - sum(quote.values())
    # Quadratwurzel-Aufteilung des Rests (groesste Reste), gedeckelt durch Verfuegbarkeit
    while rest > 0:
        offen = [s for s in keys if quote[s] < len(schichten[s])]
        gsum = sum(gew[s] for s in offen)
        roh = {s: rest * gew[s] / gsum for s in offen}
        ganz = {s: min(int(roh[s]), len(schichten[s]) - quote[s]) for s in offen}
        if sum(ganz.values()) == 0:
            for s in sorted(offen, key=lambda s: -(roh[s] - int(roh[s])))[:rest]:
                ganz[s] = 1
        for s in offen:
            quote[s] += ganz[s]
        rest = STICHPROBE_N - sum(quote.values())
    rng = random.Random(STICHPROBE_SEED)
    stich = []
    for s in keys:
        stich += rng.sample(schichten[s], quote[s])
    stich.sort(key=lambda r: (ebene(r[1]), r[1], int(r[0])))
    schreibe("stichprobe_kandidaten.csv", ["id", "body_key", "language", "category_de", "category_harmonized",
                                           "affair_id", "url_oparl", "textlaenge", "seiten", "scan_verdacht"],
             [[r[0], r[1], r[2], (kategorie_label(r[3], "", "").split(" | ")[0]), r[4], r[5], r[6], r[7], r[8],
               r[9]] for r in stich])
    schreibe("stichprobe_schichten.csv", ["ebene", "sprache_effektiv", "pdf_grundgesamtheit", "stichprobe"],
             [[s[0], s[1], len(schichten[s]), quote[s]] for s in keys])

    # ---------- Abdeckung nach Ebene ----------
    z = []
    for eb in ("Bund", "Kanton", "Gemeinde", "FL"):
        ks = [k for k in aff_n if ebene(k) == eb]
        vals = [sum(c[k] for k in ks) for c in (aff_n, c_dok, c_pdf, c_pdft, c_ind, c_vor, c_ant)]
        n0 = vals[0]
        z.append([eb, len(ks), n0, vals[1], anteil(vals[1], n0), vals[2], anteil(vals[2], n0), vals[3],
                  anteil(vals[3], n0), vals[4], anteil(vals[4], n0), vals[5], anteil(vals[5], n0),
                  vals[6], anteil(vals[6], n0)])
    schreibe("abdeckung_nach_ebene.csv", [
        "ebene", "parlamente_mit_geschaeften", "geschaefte", "mit_dokument", "anteil_mit_dokument", "mit_pdf",
        "anteil_mit_pdf", "mit_pdf_text_ohne_scanverdacht", "anteil_mit_pdf_text_ohne_scanverdacht",
        "mit_pdf_inkl_traktandum", "anteil_mit_pdf_inkl_traktandum", "mit_vorstoss_dok", "anteil_mit_vorstoss_dok",
        "mit_antwort_dok", "anteil_mit_antwort_dok"], z)

    # ---------- Ebenen-Uebersicht ----------
    z = []
    for eb in ("Bund", "Kanton", "Gemeinde", "FL"):
        ks = [k for k in alle_keys if ebene(k) == eb]
        n_ = collections.Counter(); ptk_ = collections.Counter(); tk_ = collections.Counter()
        sc_ = collections.Counter()
        for k in ks:
            n_.update(pro[k]["n"]); ptk_.update(pro[k]["pdf_text_klasse"]); tk_.update(pro[k]["text_klasse"])
            sc_.update(scan[k])
        z.append([eb, len(ks), n_["dok"], n_["pdf"], anteil(n_["pdf"], n_["dok"]), tk_["text"],
                  anteil(tk_["text"], n_["dok"]), ptk_["text"], anteil(ptk_["text"], n_["pdf"]),
                  median(v for k in ks for v in tl[(k, "pdf")]), median(v for k in ks for v in kb[k]),
                  sc_["ja"], sc_["ja"] + sc_["nein"], anteil(sc_["ja"], sc_["ja"] + sc_["nein"])])
    schreibe("ebenen.csv", ["ebene", "parlamente", "dokumente", "pdf", "anteil_pdf", "dok_text", "anteil_dok_text",
                            "pdf_text", "anteil_pdf_text", "median_textlaenge_pdf", "median_kb_pdf",
                            "pdf_scan_ja", "pdf_bewertbar", "anteil_scan_ja"], z)

    # ---------- Kennzahlen gesamt ----------
    n = summe("n"); fg = summe("format_gruppe"); tkl = summe("text_klasse"); ptk = summe("pdf_text_klasse")
    ro = summe("rolle")
    sc = collections.Counter()
    for c in scan.values():
        sc.update(c)
    tika = sum(1 for _ in open(AUSDIR / "tika_metadata_schluessel.csv", encoding="utf-8")) - 1
    lokal_kombis = {lab for (k, lab) in lok_stat if lab != " |  | "}
    kz = [
        ("parlamente_mit_dokumenten", len(alle_keys)),
        ("dokumente", n["dok"]),
        ("pdf", n["pdf"]),
        ("pdf_laut_format", fg["pdf"]),
        ("pdf_laut_url_endung", fg["pdf_laut_url"]),
        ("dok_text_verwertbar", tkl["text"]),
        ("dok_kein_textfeld", tkl["kein_feld"]),
        ("dok_text_leer", tkl["leer"]),
        ("dok_extraktion_fehlgeschlagen", tkl["fehlgeschlagen"]),
        ("dok_platzhalter", tkl["platzhalter"]),
        ("pdf_text_verwertbar", ptk["text"]),
        ("pdf_kein_textfeld", ptk["kein_feld"]),
        ("pdf_text_leer", ptk["leer"]),
        ("pdf_extraktion_fehlgeschlagen", ptk["fehlgeschlagen"]),
        ("pdf_platzhalter", ptk["platzhalter"]),
        ("median_textlaenge_dok_text", median(v for (b, t), xs in tl.items() if t == "alle" for v in xs)),
        ("median_textlaenge_pdf_text", median(v for (b, t), xs in tl.items() if t == "pdf" for v in xs)),
        ("median_kb_pdf", median(v for xs in kb.values() for v in xs)),
        ("median_zeichen_pro_kb_pdf", median(v for xs in dichte.values() for v in xs)),
        ("pdf_scan_ja", sc["ja"]), ("pdf_scan_nein", sc["nein"]), ("pdf_scan_unbekannt", sc["unbekannt"]),
        ("anteil_scan_ja_von_bewertbar", anteil(sc["ja"], sc["ja"] + sc["nein"])),
        ("pdf_scan_ja_regel_text_leer", sc["ja_text_leer"]),
        ("pdf_scan_ja_regel_dichte", sc["ja_dichte"]),
        ("pdf_scan_ja_datei_unter_30kb", sc["ja_unter_30kb"]),
        ("tika_metadata_schluessel_gesamt", tika),
        ("lokale_kategorie_kombinationen", len(lokal_kombis)),
        ("dok_rolle_vorstoss_eingereicht", ro["vorstoss_eingereicht"]),
        ("dok_rolle_antwort_exekutive", ro["antwort_exekutive"]),
        ("dok_rolle_exekutivbeschluss", ro["exekutivbeschluss"]),
        ("dok_ohne_kategorie", ro["ohne_kategorie"]),
        ("parlamente_mit_vorstoss_kategorie", sum(1 for k in alle_keys if pro[k]["rolle"]["vorstoss_eingereicht"])),
        ("parlamente_mit_antwort_kategorie", sum(1 for k in alle_keys if pro[k]["rolle"]["antwort_exekutive"])),
        ("parlamente_mit_vorstoss_und_antwort_kategorie",
         sum(1 for k in alle_keys if pro[k]["rolle"]["vorstoss_eingereicht"] and pro[k]["rolle"]["antwort_exekutive"])),
        ("pdf_ohne_url_oparl", n["pdf_ohne_url_oparl"]),
        ("pdf_kein_textfeld_ohne_url_oparl", n["pdf_kein_feld_ohne_url_oparl"]),
        ("parlamente_mit_exekutivbeschluss_kategorie",
         sum(1 for k in alle_keys if pro[k]["rolle"]["exekutivbeschluss"])),
        ("geschaefte", sum(aff_n.values())),
        ("geschaefte_mit_pdf", sum(c_pdf.values())),
        ("geschaefte_mit_pdf_text_ohne_scanverdacht", sum(c_pdft.values())),
        ("geschaefte_mit_pdf_inkl_traktandum", sum(c_ind.values())),
        ("stichprobe_grundgesamtheit_pdf", len(pdf_pool)),
    ]
    schreibe("kennzahlen_gesamt.csv", ["kennzahl", "wert"], kz)

    # ---------- Kurzbericht auf stdout ----------
    n = summe("n")
    print(f"Dokumente {n['dok']}, PDF {n['pdf']}, Parlamente {len(alle_keys)}")
    print(f"PDF-Pool Stichprobe {len(pdf_pool)}, Schichten {len(keys)}, gezogen {len(stich)}")
    print("Stichprobe scan_verdacht:", dict(collections.Counter(r[9] for r in stich)))
    print(f"Stichprobe mit affair_id: {sum(1 for r in stich if r[5])}, Parlamente: {len({r[1] for r in stich})}, "
          f"ohne language: {sum(1 for r in stich if not r[2])}")


if __name__ == "__main__":
    main()

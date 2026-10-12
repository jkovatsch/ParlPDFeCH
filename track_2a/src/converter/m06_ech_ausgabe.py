# SPDX-License-Identifier: Apache-2.0
"""CRISP-DM 6, eCH-Ausgabe (Prototyp): Zerlegung + Atome + Geschäftsmetadaten → eCH-0295-Instanz je Geschäft.

Ziel: eine saubere Datei, die korrekt gelabelt ist und sich in die Metadaten
einfügen lässt. Dieser Prototyp baut den letzten Pipeline-Schritt (E17 Schritt 7) an drei echten Dokumenten:

  1. Metadaten-Auszug aus den OpenParlData-Exporten (Dokument, Geschäft, Ereignisse, Gremien, Körperschaft).
  2. TextBlocks aus der Referenz-Zerlegung über richtext() und ech_texte() (m03_isolierung_taxonomie.py, nur
     benutzt, nicht geändert), je Fassung: K95 (Kern v0.2.0, 02_LinkML_files) und I95 (input/schema.yaml).
  3. eCH-0295-Instanz je Geschäft und Fassung (YAML und JSON) und eine Provenienz-Seitendatei nach dem
     ParlPDFeCH-Profil (src/m06_ech_profil.yaml): je TextBlock und je Wert die Belegstelle (doc_id, Seite,
     Rahmen, Zeichenbereich, Atom-IDs bzw. Export-Datensatz und Feld), Platzhalter-Wahrscheinlichkeiten 1.0
     aus der Referenz, nicht Abbildbares als eigene Einträge. Das eCH-Schema bleibt unverändert.
  4. Prüfung «kein erzeugter Text» (E19): jeder Einzelwert der Instanz braucht einen Provenienz-Eintrag;
     Texte aus dem PDF werden nach Entfernen der HTML-Auszeichnung unabhängig gegen die Atomtexte
     abgeglichen (nur Leerraum, Trennstriche am Zeilenende und Listenmarker am Atomanfang dürfen fehlen),
     Metadatenwerte wörtlich gegen den Export-Datensatz, Begriffe gegen die Enums des Schemas.
  5. Validierung mit LinkML in einer isolierten Werkzeugumgebung (uvx --offline --from linkml==1.11.1, nicht in
     .venv): linkml-validate gegen K95 (und Motion-Profil), I95 und das Profil; linkml-convert nach Turtle.
     Dazu Kontrollen (Beispieldaten der Fachgruppe) und eine Diagnose an einer Kopie von K95 in
     daten/ech/diagnose/ (nur zur Einordnung der Fehler, nicht als Ausgabe).

Kein Netz (uvx --offline, Paket liegt im uv-Cache), kein Modell, keine API. Prozesse bleiben klein (< 1 GB).

Aufruf:
  uv run python src/m06_ech_ausgabe.py                     (alles: Auszug, Instanzen, Prüfung, Validierung, RDF)
  uv run python src/m06_ech_ausgabe.py --ohne-validierung  (nur Instanzen und Prüfung «kein erzeugter Text»)
  uv run python src/m06_ech_ausgabe.py --metadaten-neu     (Metadaten-Auszug neu aus den Exporten lesen)

Ausgaben: daten/ech/{metadaten,instanzen,provenienz,rdf,validierung,diagnose}/ und daten/ech/zusammenfassung.json.
Bericht: crisp-dm/06-deployment/ech-ausgabe-prototyp.md.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m02_ech_regeln as er  # noqa: E402  (Begriffsliste Geschäftstypen, nur gelesen)
import m03_isolierung_taxonomie as tx  # noqa: E402  (nur benutzt, nicht ändern: anderer Arbeitsschritt)

PROJEKT = Path(__file__).resolve().parents[1]
ECH = PROJEKT / "quellen" / "political-affairs-ech-group"
ECH_COMMIT = "3cab44d6a07f60bd8211cccdcf948717ef8fba5c"
EXPORTE = PROJEKT / "daten" / "roh" / "exports"
PDF = PROJEKT / "daten" / "pdf" / "augenschein"
REFERENZEN = PROJEKT / "daten" / "isolierung"
AUS = PROJEKT / "daten" / "ech"
PROFIL = PROJEKT / "src" / "m06_ech_profil.yaml"
LINKML = "linkml==1.11.1"
UVX = ["uvx", "--offline", "--from", LINKML]

SCHEMA = {
    "k95": ECH / "ech-0295_affairs" / "02_LinkML_files" / "ech-0295_affairs.yaml",
    "k95_motion": ECH / "ech-0295_affairs" / "02_LinkML_files" / "ech-0295_affairs_motion_profile.yaml",
    "i95": ECH / "ech-0295_affairs" / "input" / "schema.yaml",
}
FASSUNG_TEXT = {"k95": "eCH-0295 K95 (Kern v0.2.0, 02_LinkML_files), Commit 3cab44d",
                "i95": "eCH-0295 I95 (input/schema.yaml), Commit 3cab44d"}

# IRIs. OpenParlData-API-Adressen als vorläufige global_uri (Datenanbieter; keine vereinbarte IRI-Regel, E3/F19).
# Abgeleitete Objekte (Lieferung, Schritte, Provenienz) im Platzhalter-Namensraum nach RFC 2606 (.example).
OPD = "https://api.openparldata.ch/v1/"
PPD = "https://data.parlpdfech.example/"
WIKIDATA = "http://www.wikidata.org/entity/"
SPRACHEN = {"de", "fr", "it", "rm", "en"}

# Auswahl (Auftrag: ein eingereichter Vorstoss, eine Antwort mit Fragen und Antworten, ein Dokument fr/it;
# nur digitale PDF). Begründung im Bericht, Abschnitt 1.
AUSWAHL = [
    ("K03", "248210", "eingereichter Vorstoss: Motion BE, de, digital; K95 hat ein Motion-Profil"),
    ("K02", "117181", "Antwort der Exekutive je Frage: Anfrage ZH, de, digital, 4 Fragen und 4 Antworten"),
    ("K06", "552585", "Antwort der Exekutive je Frage auf Französisch: Interpellation VD, fr, digital, 3 Fragen"),
]

# Abschnitt der Taxonomie → Schritt der eCH-Instanz, je nach Slot-Angabe aus ech_texte()
SLOT_ZIEL = {
    "Affair.title (TextBlock)": "title", "Affair.title (MultilingualValue)": "title",
    "Submission.texts": "submission", "SubmissionStep.texts": "submission",
    "ResponseStep.texts": "response", "ExecutiveResponseStep.texts": "response",
    "Submission.texts oder ResponseStep.texts (nach Verfasser)": "dokument",
    "ProcessStep.texts (Schritt, den der Vermerk betrifft)": "dokument",
}
SCHRITT_KLASSE = {"k95": {"submission": "SubmissionStep", "response": "ExecutiveResponseStep"},
                  "i95": {"submission": "Submission", "response": "ResponseStep"}}
I95_KLASSE = {"motion": "Motion", "postulate": "Postulate", "interpellation": "Interpellation",
              "request": "Request", "question": "Question", "parliamentary_initiative": "ParliamentaryInitiative",
              "draft_decree": "DraftDecree"}
# I95-Wert (Begriffsliste m02_ech_regeln) → K95-Wert, Güte (ech-weisungen.md W5)
I95_ZU_K95 = {"motion": ("motion", "exact"), "postulate": ("postulate", "exact"),
              "interpellation": ("interpellation", "exact"), "request": ("question", "close"),
              "question": ("question", "exact"), "parliamentary_initiative": ("parliamentary_initiative", "exact"),
              "draft_decree": ("other", "none"), "motion_and_postulate": ("other", "none"),
              "motion_then_postulate": ("other", "none"), "": ("other", "none")}
MATCH = {"exakt": "exact", "nah": "close", "weiter": "broad", "keine": "none", "unbestimmt": "none"}
GUETE = ["exact", "close", "broad", "none"]

EREIGNIS_EINGEREICHT = 1   # title_harmonized_id im events-Export
EREIGNIS_BEANTWORTET = 6


# ================================================================ Hilfen


@dataclass
class V:
    """Ein Einzelwert der eCH-Instanz mit seiner Herkunft. Jeder Blattwert der Instanz muss so entstehen;
    entpacken() meldet jeden Wert ohne Herkunft (Prüfung «kein erzeugter Text»)."""
    wert: Any
    herkunft: dict


def sha256_datei(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


URI_SAFE = ":/?#[]@!$&'()*+,;=-._~"   # RFC 3986: reserved characters and unreserved marks (letters and digits stay)


def as_uri(s: str | None) -> str | None:
    """An export URL for a slot with the range uri: percent-encode each character that RFC 3986 does not allow
    (for example a space or a letter that is not ASCII). Reserved characters and existing percent escapes stay."""
    if not isinstance(s, str):
        return s
    return "".join(p if re.fullmatch(r"%[0-9A-Fa-f]{2}", p) else quote(p, safe=URI_SAFE)
                   for p in re.split(r"(%[0-9A-Fa-f]{2})", s))


def rel(p: Path) -> str:
    return str(p.relative_to(PROJEKT))


def schreibe_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def schreibe_yaml(p: Path, obj: Any, kopf: str = "") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=100000, default_flow_style=False)
    p.write_text(kopf + text, encoding="utf-8")


def speicher_pruefen() -> None:
    """Vor grösseren Schritten: unter 15 % freiem Speicher warten (Training läuft parallel)."""
    for _ in range(40):
        try:
            aus = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=30).stdout
            m = re.search(r"free percentage:\s*(\d+)%", aus)
            if not m or int(m.group(1)) >= 15:
                return
            print(f"  Speicher frei {m.group(1)} % < 15 %: warte 30 s", flush=True)
        except (OSError, subprocess.SubprocessError):
            return
        time.sleep(30)
    raise SystemExit("Speicher bleibt unter 15 % frei: abgebrochen")


def ech_stand_pruefen() -> str:
    kopf = subprocess.run(["git", "-C", str(ECH), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if kopf != ECH_COMMIT:
        raise SystemExit(f"eCH-Repository steht auf {kopf}, erwartet {ECH_COMMIT}")
    return kopf


def enum_werte(fassung: str, enum: str) -> set[str]:
    schema = yaml.safe_load(SCHEMA[fassung].read_text(encoding="utf-8"))
    return set((schema["enums"][enum].get("permissible_values") or {}).keys())


def equals_string(fassung: str, klasse: str, slot: str) -> str | None:
    schema = yaml.safe_load(SCHEMA[fassung].read_text(encoding="utf-8"))
    return ((schema["classes"][klasse].get("slot_usage") or {}).get(slot) or {}).get("equals_string")


# ================================================================ Auswahl und Referenz


def referenz_quelle(doc_id: str) -> str:
    """Hauptreferenz: die 26 Augenschein-Dokumente mit Atomen (Status success), doc_id als Text sortiert;
    Positionen 1–13 → ref_a, 14–26 → ref_b (ref_a/notizen.md, ref_b/notizen.md)."""
    mit_atomen = sorted(p.stem for p in tx.ATOME.glob("*.json")
                        if json.loads(p.read_text(encoding="utf-8")).get("status") == "success")
    if len(mit_atomen) != 26:
        raise SystemExit(f"{len(mit_atomen)} Atom-Dateien mit Status success, erwartet 26")
    return "ref_a" if mit_atomen.index(doc_id) < 13 else "ref_b"


def referenz_laden(doc_id: str) -> tuple[dict, str]:
    quelle = referenz_quelle(doc_id)
    pfad = REFERENZEN / quelle / f"{doc_id}.json"
    return json.loads(pfad.read_text(encoding="utf-8")), quelle


# ================================================================ Metadaten-Auszug (OpenParlData-Exporte)


def _feld(s: str, schluessel: str, wert: Any) -> bool:
    """Vorfilter auf der Rohzeile (die Exporte schreiben teils mit, teils ohne Leerzeichen nach dem Doppelpunkt)."""
    return f'"{schluessel}":{wert},' in s or f'"{schluessel}": {wert},' in s


def _zeilen(datei: Path, vorfilter):
    with gzip.open(datei, "rt", encoding="utf-8") as fh:
        for z in fh:
            if vorfilter(z):
                yield json.loads(z)


def metadaten_auszug(neu: bool = False) -> dict[str, dict]:
    """Je ausgewähltem Dokument die Export-Datensätze, die die Instanz verwendet (ohne Volltext). Wird unter
    daten/ech/metadaten/<doc_id>.json abgelegt und ist die Prüfgrundlage für alle Metadatenwerte."""
    aug = tx.augenschein()
    ziel = {d: AUS / "metadaten" / f"{d}.json" for _, d, _ in AUSWAHL}
    if not neu and all(p.exists() for p in ziel.values()):
        return {d: json.loads(p.read_text(encoding="utf-8")) for d, p in ziel.items()}
    print("Metadaten-Auszug aus den Exporten (Durchlauf über affairs, events, groups, bodies, docs)", flush=True)
    zeilen = {d: aug[d] for _, d, _ in AUSWAHL}
    aff_ids = {int(z["affair_id"]): d for d, z in zeilen.items()}
    aus: dict[str, dict] = {d: {"doc_id": d, "zelle": z["zelle"], "body_key": z["body_key"],
                                "affair_docs": [], "events": [], "groups": []} for d, z in zeilen.items()}
    for d, z in zeilen.items():
        datei = EXPORTE / "docs" / f"docs_{z['body_key']}.ndjson.gz"
        aid = int(z["affair_id"])
        for r in _zeilen(datei, lambda s, aid=aid, d=d: _feld(s, "affair_id", aid) or _feld(s[:20], "id", d)):
            r.pop("text", None)
            r.pop("tika_metadata", None)
            if str(r["id"]) == d:
                aus[d]["doc"] = r
            if r.get("affair_id") == aid:
                aus[d]["affair_docs"].append({k: r.get(k) for k in ("id", "name", "date", "language", "category_de",
                                                                      "category_fr", "format", "url_oparl")})
        aus[d]["doc_export_file"] = rel(datei)
    for r in _zeilen(EXPORTE / "affairs.ndjson.gz",
                     lambda s: any(_feld(s[:20], "id", a) for a in aff_ids)):
        aus[aff_ids[r["id"]]]["affair"] = r
    for r in _zeilen(EXPORTE / "events.ndjson.gz", lambda s: any(_feld(s, "affair_id", a) for a in aff_ids)):
        if r.get("affair_id") in aff_ids:
            aus[aff_ids[r["affair_id"]]]["events"].append(r)
    body_ids = {}
    for d in aus:
        body_ids.setdefault(aus[d]["affair"]["body_id"], []).append(d)
    for r in _zeilen(EXPORTE / "groups.ndjson.gz", lambda s: any(_feld(s, "body_id", b) for b in body_ids)):
        if r.get("body_id") in body_ids and r.get("type_harmonized") in ("council_executive", "council_legislative"):
            for d in body_ids[r["body_id"]]:
                aus[d]["groups"].append({k: v for k, v in r.items() if k != "contact"})
    for r in _zeilen(EXPORTE / "bodies.ndjson.gz", lambda s: any(_feld(s[:20], "id", b) for b in body_ids)):
        for d in body_ids.get(r["id"], []):
            aus[d]["body"] = r
    abruf = (EXPORTE / "abgerufen_utc.txt").read_text(encoding="utf-8").strip()
    for d, a in aus.items():
        for pflicht in ("doc", "affair", "body"):
            if pflicht not in a:
                raise SystemExit(f"{d}: Export-Datensatz {pflicht} fehlt")
        a["export_retrieved_utc"] = abruf
        a["events"].sort(key=lambda e: (e.get("date") or "", e.get("position") or 0))
        schreibe_json(ziel[d], a)
    return aus


def beleg_meta(datei: str, art: str, rid: Any, feld: str, wert: Any, abruf: str) -> dict:
    return {"export_file": datei, "record_type": art, "record_id": str(rid), "field_name": feld,
            "source_value": "" if wert is None else str(wert), "datetime_export_retrieved": abruf}


# ================================================================ Fundstellen im PDF


def atom_beleg(a: dict, treffer: tuple[int, int] | None = None) -> dict:
    r = a.get("zeilenrahmen") or a.get("rahmen")
    b = {"atom_id": a["id"], "page_number": a["seite"]}
    if r:
        b["bbox"] = {"bbox_left": r[0], "bbox_top": r[1], "bbox_right": r[2], "bbox_bottom": r[3]}
    b |= {"char_start": a["zeichen"][0], "char_end": a["zeichen"][1], "from_ocr": bool(a.get("ocr"))}
    if treffer:
        b |= {"matched_text": a["text"][treffer[0]:treffer[1]], "match_start": treffer[0], "match_end": treffer[1]}
    return b


def fundstellen(wert: str, liste: list[dict]) -> list[dict]:
    """Wörtliche Fundstellen eines Werts in den Atomtexten (Leerraum zusammengefasst, auch über
    Atomgrenzen hinweg). Rückgabe: Atom-Belege mit dem Teil des Treffers je Atom."""
    if not wert.strip():
        return []
    teile, atom_an = [], []
    for a in liste:
        if not a["text"]:
            continue
        if teile:
            teile.append(" ")
            atom_an.append(None)
        atom_an.extend((a, k) for k in range(len(a["text"])))
        teile.append(a["text"])
    heu = "".join(teile)
    # Leerraum vereinheitlichen, Abbildung auf Ursprungspositionen behalten
    norm, karte = [], []
    for i, c in enumerate(heu):
        if c.isspace():
            if norm and norm[-1] == " ":
                continue
            norm.append(" ")
        else:
            norm.append(c)
        karte.append(i)
    norm_s = "".join(norm)
    such = re.sub(r"\s+", " ", wert.strip())
    belege, start = [], 0
    while (i := norm_s.find(such, start)) >= 0:
        je_atom: dict[str, list] = {}
        for j in range(i, i + len(such)):
            ziel = atom_an[karte[j]]
            if ziel is None:
                continue
            a, k = ziel
            je_atom.setdefault(a["id"], [a, k, k])[2] = k
        for a, von, bis in je_atom.values():
            belege.append(atom_beleg(a, (von, bis + 1)))
        start = i + 1
    return belege


MONATE = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
           "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
           "novembre", "décembre"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
           "ottobre", "novembre", "dicembre"],
}
_MONAT = {m.lower(): i + 1 for ms in MONATE.values() for i, m in enumerate(ms)}
RX_DATUM = [
    re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b"),
    re.compile(r"\b(\d{1,2})\.\s?(" + "|".join(MONATE["de"]) + r")\s(\d{4})\b"),
    re.compile(r"\b(1er|\d{1,2})\s(" + "|".join(MONATE["fr"]) + r")\s(\d{4})\b", re.I),
    re.compile(r"\b(\d{1,2})\s(" + "|".join(MONATE["it"]) + r")\s(\d{4})\b", re.I),
]


def daten_im_pdf(liste: list[dict]) -> list[dict]:
    """Alle vollständigen Datumsangaben in den Atomtexten (eine Zeile; Formate TT.MM.JJJJ und Tag Monat Jahr
    de/fr/it). Rückgabe: {iso, atom, match}."""
    gef = []
    for a in liste:
        for rx in RX_DATUM:
            for m in rx.finditer(a["text"] or ""):
                tag = 1 if m.group(1).lower() == "1er" else int(m.group(1))
                mon = int(m.group(2)) if m.group(2).isdigit() else _MONAT[m.group(2).lower()]
                try:
                    iso = datetime(int(m.group(3)), mon, tag).date().isoformat()
                except ValueError:
                    continue
                gef.append({"iso": iso, "atom": a, "span": m.span()})
    return gef


def datum_belege(iso: str, gefunden: list[dict]) -> list[dict]:
    return [atom_beleg(g["atom"], g["span"]) for g in gefunden if g["iso"] == iso]


# ================================================================ Wortlaut-Abgleich (E19), unabhängig von richtext()

RX_MARKER_ROH = re.compile(r"^\s*(?:\d{1,3}[.)]|[-–—•·▪◦●■*]|o)(?=\s)")


def sichtbarer_text(t: str, form: str) -> str:
    if form == "richtext":
        return html.unescape(re.sub(r"<[^>]+>", "", t))
    return t


def wortlaut_abgleich(sichtbar: str, atomtexte: list[str]) -> dict:
    """Prüft, ob der sichtbare Text Zeichen für Zeichen aus den Atomtexten in dieser Reihenfolge besteht.
    Erlaubt sind nur: Leerraum (wird ignoriert), Wegfall eines Trennstrichs am Ende eines Atoms, Wegfall
    eines Listenmarkers am Anfang eines Atoms. Alles andere (zusätzliche, geänderte oder fehlende Zeichen)
    lässt die Prüfung scheitern."""
    s = re.sub(r"\s", "", unicodedata.normalize("NFC", sichtbar))
    varianten = []
    for t in atomtexte:
        t = unicodedata.normalize("NFC", t)
        m = RX_MARKER_ROH.match(t)
        voll = re.sub(r"\s", "", t)
        ohne_m = re.sub(r"\s", "", t[m.end():]) if m else None
        v = [(voll, 0, 0)]
        if voll.endswith("-"):
            v.append((voll[:-1], 1, 0))
        if ohne_m is not None:
            v.append((ohne_m, 0, 1))
            if ohne_m.endswith("-"):
                v.append((ohne_m[:-1], 1, 1))
        varianten.append(v)
    sys.setrecursionlimit(max(10000, 4 * len(varianten)))

    @lru_cache(maxsize=None)
    def weiter(i: int, p: int):
        if i == len(varianten):
            return () if p == len(s) else None
        for txt, h, l in varianten[i]:
            if s.startswith(txt, p):
                r = weiter(i + 1, p + len(txt))
                if r is not None:
                    return ((h, l),) + r
        return None

    r = weiter(0, 0)
    if r is None:
        # längster passender Anfang zur Fehlermeldung
        p = 0
        for v in varianten:
            txt = next((t for t, _, _ in v if s.startswith(t, p)), None)
            if txt is None:
                break
            p += len(txt)
        return {"ok": False, "zeichen": len(s), "abweichung_ab": p, "kontext": s[max(0, p - 20):p + 20]}
    return {"ok": True, "zeichen": len(s), "trennstriche": sum(h for h, _ in r), "listenmarker": sum(l for _, l in r)}


# ================================================================ Bausteine der Instanz


def wert_meta(wert: Any, meta: dict, ableitung: str = "copied_from_metadata", **zus) -> V:
    return V(wert, {"derivation": ableitung, "metadata_evidence": [meta], **zus})


def typ_bestimmen(affair: dict, fassung: str, abruf: str) -> V | None:
    """affair_type über die Begriffsliste (m02_ech_regeln.typ_ech: lokale Bezeichnung vor Harmonisierung),
    nur erlaubte Enum-Werte; K95: Abbildung I95 → K95 (W5), sonst other; I95: leer mit Vermerk."""
    lokal = affair.get("type_name_de") or affair.get("type_name_fr") or affair.get("type_name_it")
    feld = next(f for f in ("type_name_de", "type_name_fr", "type_name_it", "type_harmonized_id")
                if affair.get(f) is not None)
    w, art, kat, quelle = er.typ_ech(affair.get("type_harmonized_id"), lokal)
    belege = [beleg_meta("daten/roh/exports/affairs.ndjson.gz", "affair", affair["id"], f, affair.get(f), abruf)
              for f in dict.fromkeys((feld, "type_harmonized_id")) if affair.get(f) is not None]
    regel = f"m02_ech_regeln.typ_ech (Quelle {quelle}, Regel {art}{', ' + kat if kat else ''})"
    if fassung == "i95":
        if not w:
            return None
        return V(w, {"derivation": "mapped_from_metadata", "rule": regel, "match": MATCH[art],
                     "metadata_evidence": belege, "_enum": ("i95", "AffairTypeEnum")})
    k, g = I95_ZU_K95.get(w, ("other", "none"))
    guete = GUETE[max(GUETE.index(MATCH[art]), GUETE.index(g))]
    return V(k, {"derivation": "mapped_from_metadata", "rule": regel + f"; I95 {w or '(leer)'} → K95 {k} (W5)",
                 "match": guete, "metadata_evidence": belege, "_enum": ("k95", "AffairTypeEnum")})


def gruppe(meta: dict, typ: str) -> dict | None:
    kand = [g for g in meta["groups"] if g.get("type_harmonized") == typ and g.get("active")]
    return kand[0] if len(kand) == 1 else None


def gruppen_referenz(g: dict, sprache: str, fassung: str, abruf: str, regel: str) -> dict:
    """K95: GroupReference (global_uri, label, wikidata_uri); I95: Organization (global_uri, name, wikidata_uri).
    Name nur in der Dokumentsprache (das Feld name_de enthält bei VD französischen Text)."""
    datei = "daten/roh/exports/groups.ndjson.gz"
    feld = f"name_{sprache}" if g.get(f"name_{sprache}") else next(f for f in ("name_de", "name_fr", "name_it")
                                                                       if g.get(f))
    uri = V(f"{OPD}groups/{g['id']}", {"derivation": "identifier_from_metadata", "rule": f"{OPD}groups/{{id}}; {regel}",
                                         "metadata_evidence": [beleg_meta(datei, "group", g["id"], "id", g["id"], abruf)],
                                         "_muster": (f"{OPD}groups/{{}}", g["id"])})
    name = wert_meta(g[feld], beleg_meta(datei, "group", g["id"], feld, g[feld], abruf))
    ref: dict[str, Any] = {"global_uri": uri}
    if fassung == "k95":
        ref["label"] = name
    else:
        ref["name"] = [{"text": name, "text_language": V(feld[-2:], {
            "derivation": "normalized_from_metadata", "rule": "Sprachcode aus dem Feldnamen name_<sprache>",
            "metadata_evidence": [beleg_meta(datei, "group", g["id"], feld, g[feld], abruf)], "_norm": "feldsprache"})}]
    if g.get("wikidata_id"):
        ref["wikidata_uri"] = V(WIKIDATA + g["wikidata_id"], {
            "derivation": "identifier_from_metadata", "rule": "http://www.wikidata.org/entity/{wikidata_id}",
            "metadata_evidence": [beleg_meta(datei, "group", g["id"], "wikidata_id", g["wikidata_id"], abruf)],
            "_muster": (WIKIDATA + "{}", g["wikidata_id"])})
    return ref


def ereignis(meta: dict, harm_id: int) -> dict | None:
    e = [x for x in meta["events"] if x.get("title_harmonized_id") == harm_id]
    return e[0] if len(e) == 1 else None


def datum_wert(datum: str, beleg: dict, gefunden: list[dict], regel: str, match: str = "exact",
               alternativen: list | None = None) -> V:
    iso = datum[:10]
    pdf = datum_belege(iso, gefunden)
    return V(iso, {"derivation": "normalized_from_metadata", "rule": regel + "; Datumsteil (JJJJ-MM-TT) des Zeitstempels",
                   "match": match, "metadata_evidence": [beleg], "pdf_evidence": pdf,
                   "konsistenz": "confirmed" if pdf else "not_found", "alternativen": alternativen or [],
                   "_norm": "datumsteil"})


# ================================================================ Instanz je Fassung


@dataclass
class Dokument:
    zelle: str
    doc_id: str
    grund: str
    meta: dict
    aug: dict
    ref: dict
    ref_quelle: str
    dok: dict
    liste: list[dict]
    sprache: str
    sprache_herkunft: dict
    art: str            # submission | response (Hauptschritt des Dokuments)


def dokument_laden(zelle: str, doc_id: str, grund: str, meta: dict) -> Dokument:
    aug = tx.augenschein()[doc_id]
    if aug["herkunft_auto"] != "digital":
        raise SystemExit(f"{doc_id}: nicht digital ({aug['herkunft_auto']})")
    ref, quelle = referenz_laden(doc_id)
    dok = tx.lade(doc_id)
    liste = tx.atome_laden(doc_id, dok)
    warnung = tx.atome_passen(ref, liste)
    if warnung:
        raise SystemExit(f"{doc_id}: {warnung}")
    fehler, _ = tx.pruefe_zerlegung(ref, liste)
    if fehler:
        raise SystemExit(f"{doc_id}: Referenz ungültig: {fehler[:3]}")
    d = meta["doc"]
    abruf = meta["export_retrieved_utc"]
    if d.get("language") in SPRACHEN:
        sprache = d["language"]
        herkunft = {"derivation": "copied_from_metadata",
                    "metadata_evidence": [beleg_meta(meta["doc_export_file"], "doc", d["id"], "language", d["language"], abruf)]}
    elif aug.get("sprache_auto") in SPRACHEN:
        sprache = aug["sprache_auto"]
        herkunft = {"derivation": "detected_by_rule",
                    "rule": "Export ohne Sprache; automatische Spracherkennung der Stichprobe (augenschein.csv, "
                            f"Spalte sprache_auto, Anteile {aug.get('sprachanteile')}; von Hand: {aug.get('sprache_augenschein')})",
                    "_augenschein": aug["sprache_auto"]}
    else:
        raise SystemExit(f"{doc_id}: keine Sprache")
    art = {"vorstoss": "submission", "antwort_exekutive": "response"}.get(aug["dokumentart"])
    if not art:
        raise SystemExit(f"{doc_id}: Dokumentart {aug['dokumentart']} nicht im Prototyp")
    return Dokument(zelle, doc_id, grund, meta, aug, ref, quelle, dok, liste, sprache, herkunft, art)


def instanz_bauen(D: Dokument, fassung: str) -> tuple[dict, dict]:
    """Baut die eCH-Instanz (mit V-Werten) und die Rohdaten der Seitendatei für eine Fassung."""
    meta, aff, doc = D.meta, D.meta["affair"], D.meta["doc"]
    abruf = meta["export_retrieved_utc"]
    adatei, ddatei = "daten/roh/exports/affairs.ndjson.gz", meta["doc_export_file"]
    aid = aff["id"]
    gefunden = daten_im_pdf(D.liste)
    affair_iri = f"{OPD}affairs/{aid}"
    container_iri = f"{PPD}delivery/{fassung}/affair-{aid}/doc-{D.doc_id}"
    doc_iri = f"{OPD}docs/{D.doc_id}"
    sprache_v = lambda: V(D.sprache, dict(D.sprache_herkunft))  # noqa: E731
    url = V(doc["url_oparl"], {"derivation": "copied_from_metadata",
                               "metadata_evidence": [beleg_meta(ddatei, "doc", doc["id"], "url_oparl", doc["url_oparl"], abruf)]})
    zl = tx.ZUSAMMENLEGEN_K95 if fassung == "k95" else None
    bloecke = tx.richtext(D.ref, D.liste, D.dok, zusammenlegen=zl)
    rp = tx.richtext_pruefen(bloecke, D.ref, D.liste, D.dok)
    if rp:
        raise SystemExit(f"{D.doc_id} {fassung}: richtext_pruefen: {rp[:3]}")

    nicht: list[dict] = []          # NotMappedRecords
    tb_records: list[dict] = []     # TextBlockRecords (roh)
    texte: dict[str, list] = {"submission": [], "response": []}
    pdf_titel = None
    for tb in bloecke:
        et = tx.ech_texte([tb], fassung, D.sprache, doc["url_oparl"])
        tb_iri = f"{PPD}affair-{aid}/doc-{D.doc_id}/{fassung}/textblock/{tb['section']}{'-quoted' if tb['quoted'] else ''}"
        rec = {"tb": tb, "global_uri": tb_iri, "mapping_status": "profile_only"}
        tb_records.append(rec)
        if not et["texts"]:
            rec["not_mapped_reason"] = et["not_mappable"][0]["reason"]
            continue
        eintrag = et["texts"][0]
        ziel = SLOT_ZIEL[eintrag["slot"]]
        if ziel == "dokument":
            ziel = D.art
        if ziel == "title":
            # Geschäftstitel kommt aus den Metadaten; der Titel im PDF ist der Titel dieses Dokuments
            # (Expression-Titel nach eCH-0292), nicht zwingend der Geschäftstitel.
            pdf_titel = rec
            if any(aff.get(f"title_{s}") for s in ("de", "fr", "it", "rm")):
                rec["not_mapped_reason"] = ("Dokumenttitel (Expression-Titel nach eCH-0292); Affair.title kommt aus den "
                                            "Metadaten; eCH-0295 hat kein Feld für den Titel eines Dokuments")
                continue
        blk = eintrag["text_block"]
        h_text = {"derivation": "extracted_from_pdf", "_textblock": rec,
                  "rule": f"richtext() und ech_texte() aus den Einheiten; Belege im TextBlockRecord {tb_iri}"}
        tt = blk.get("text_type")
        h_tt = {"derivation": "fixed_by_schema", "rule": f"Abschnitt {tb['section']} → TextTypeEnum {tt} "
                "(isolierung-strategie.md Abschnitt 2)", "_enum": (fassung, "TextTypeEnum")}
        if fassung == "k95":
            neu = {"text_type": V(tt, h_tt), "value": [{"value": V(blk["value"][0]["value"], h_text),
                                                        "language": sprache_v()}], "document_url": url}
        else:
            neu = {"text": V(blk["text"], h_text), "text_language": sprache_v(), "text_type": V(tt, h_tt),
                   "document_url": url}
        rec["mapping_status"] = "in_ech_instance"
        rec["ziel"] = ziel
        rec["ech_text_type"] = tt
        if ziel == "title":
            texte.setdefault("title", []).append((neu, rec))
        else:
            texte[ziel].append((neu, rec))

    # ---------------------------------------------------------------- Geschäft
    affair: dict[str, Any] = {"__entity__": (affair_iri, "Affair" if fassung == "k95" else
                                             I95_KLASSE.get((typ_bestimmen(aff, "i95", abruf) or V("", {})).wert, "Affair"))}
    affair["global_uri"] = V(affair_iri, {"derivation": "identifier_from_metadata",
                                          "rule": f"{OPD}affairs/{{id}} (OpenParlData-API, vorläufig; E3, F19)",
                                          "metadata_evidence": [beleg_meta(adatei, "affair", aid, "id", aid, abruf)],
                                          "_muster": (f"{OPD}affairs/{{}}", aid)})
    if aff.get("external_id"):
        affair["local_id"] = wert_meta(aff["external_id"], beleg_meta(adatei, "affair", aid, "external_id", aff["external_id"], abruf),
                                       rule="ID im Ratsinformationssystem (external_id)")
    if fassung == "k95":
        affair["affair_uid"] = V(affair_iri, {"derivation": "identifier_from_metadata",
                                              "rule": "gleich global_uri: OpenParlData ist das herausgebende System dieser "
                                                      "Lieferung; K95 verlangt zwei Identifier (affair_uid, global_uri)",
                                              "metadata_evidence": [beleg_meta(adatei, "affair", aid, "id", aid, abruf)],
                                              "_muster": (f"{OPD}affairs/{{}}", aid)})
    affair["affair_number"] = wert_meta(aff["number"], beleg_meta(adatei, "affair", aid, "number", aff["number"], abruf),
                                        pdf_evidence=fundstellen(aff["number"], D.liste),
                                        konsistenz="confirmed" if fundstellen(aff["number"], D.liste) else "not_found")
    typ = typ_bestimmen(aff, fassung, abruf)
    if typ is not None:
        affair["affair_type"] = typ
    else:
        nicht.append({"not_mapped_item": "Affair.affair_type", "not_mapped_reason":
                      "Begriffsliste ergibt keinen Wert der I95-AffairTypeEnum (kein other in I95)",
                      "candidate_value": str(aff.get("type_name_de") or aff.get("type_name_fr") or ""),
                      "candidate_source": "affairs.type_name_*"})
    titel = []
    for s in ("de", "fr", "it", "rm"):
        t = aff.get(f"title_{s}")
        if not t:
            continue
        b = beleg_meta(adatei, "affair", aid, f"title_{s}", t, abruf)
        fs = fundstellen(t, D.liste) if s == D.sprache else []
        tv = wert_meta(t, b, pdf_evidence=fs, konsistenz=("confirmed" if fs else "not_found") if s == D.sprache else "not_checked")
        lv = V(s, {"derivation": "normalized_from_metadata", "rule": "Sprachcode aus dem Feldnamen title_<sprache>",
                   "metadata_evidence": [b], "_norm": "feldsprache"})
        titel.append({"value": tv, "language": lv} if fassung == "k95" else
                     {"text": tv, "text_language": lv,
                      "text_type": V("title", {"derivation": "fixed_by_schema", "rule": "Titel des Geschäfts → TextTypeEnum title",
                                               "_enum": ("i95", "TextTypeEnum")})})
    if not titel and texte.get("title"):
        neu, rec = texte["title"][0]
        titel.append(neu if fassung == "i95" else {"value": neu["value"][0]["value"], "language": neu["value"][0]["language"]})
        rec["ziel"] = "title"
    if titel:
        affair["title"] = titel

    # ---------------------------------------------------------------- Schritte
    schritte: dict[str, dict] = {}
    ev_ein, ev_ant = ereignis(meta, EREIGNIS_EINGEREICHT), ereignis(meta, EREIGNIS_BEANTWORTET)
    edatei = "daten/roh/exports/events.ndjson.gz"

    def schritt_iri(typ_: str) -> str:
        return f"{PPD}affair-{aid}/step/{typ_}/doc-{D.doc_id}"

    def schritt_kopf(art: str) -> dict:
        klasse = SCHRITT_KLASSE[fassung][art]
        iri = schritt_iri(art)
        kopf: dict[str, Any] = {"__entity__": (iri, klasse)}
        h_iri = {"derivation": "identifier_minted", "rule": "{Platzhalter}/affair-{id}/step/{art}/doc-{doc_id} "
                 "(deterministisch, Namensraum vorläufig)"}
        if fassung == "k95":
            kopf["step_uid"] = V(iri, h_iri)
            st = equals_string("k95", klasse, "step_type")
            kopf["step_type"] = V(st, {"derivation": "fixed_by_schema", "rule": f"{klasse}.step_type equals_string {st}",
                                       "_equals": ("k95", klasse, "step_type")})
        else:
            kopf["global_uri"] = V(iri, h_iri)
        return kopf

    # Einreichung
    s_texte = texte["submission"]
    s_datum = None
    if ev_ein:
        b = beleg_meta(edatei, "event", ev_ein["id"], "date", ev_ein["date"], abruf)
        s_datum = datum_wert(ev_ein["date"], b, gefunden, "Ereignis mit title_harmonized_id 1 (Eingereicht)")
    leg = gruppe(meta, "council_legislative")
    if fassung == "k95" and not s_texte:
        nicht.append({"not_mapped_item": "SubmissionStep", "not_mapped_reason":
                      "texts ist Pflicht; das Dokument enthält den Vorstoss nur zitiert, das Original liegt als eigenes "
                      f"Dokument vor ({', '.join(str(x['id']) for x in meta['affair_docs'] if str(x['id']) != D.doc_id)}); "
                      "Einreichungsdatum und Parlament (chamber) sind darum nicht abbildbar",
                      "candidate_value": f"submission_date {s_datum.wert if s_datum else '–'}; chamber "
                                         f"{OPD}groups/{leg['id'] if leg else '–'}",
                      "candidate_source": "events (Eingereicht), groups (council_legislative)"})
    elif s_texte or (fassung == "i95" and s_datum):
        st = schritt_kopf("submission")
        if fassung == "k95":
            st["texts"] = [n for n, _ in s_texte]
            if s_datum:
                st["submission_date"] = s_datum
            if leg:
                st["chamber"] = gruppen_referenz(leg, D.sprache, "k95", abruf,
                                                 "einzige aktive Gruppe council_legislative des Parlaments")
        else:
            if s_datum:
                st["submission_date"] = s_datum
            if s_texte:
                st["texts"] = [n for n, _ in s_texte]
            if leg:
                nicht.append({"not_mapped_item": "Parlament (chamber)", "not_mapped_reason":
                              "I95 hat am Geschäft und an Submission kein Feld für das Parlament",
                              "candidate_value": f"{OPD}groups/{leg['id']}", "candidate_source": "groups (council_legislative)"})
        schritte["submission"] = st
    # Antwort der Exekutive
    r_texte = texte["response"]
    exe = gruppe(meta, "council_executive")
    r_datum = None
    if ev_ant:
        b = beleg_meta(edatei, "event", ev_ant["id"], "date", ev_ant["date"], abruf)
        r_datum = datum_wert(ev_ant["date"], b, gefunden, "Ereignis mit title_harmonized_id 6 (Beantwortet)")
    elif D.art == "response":
        sig_atome = {i for e in D.ref["units"] if e["type"] == "signature" for i in einheit_atome(e, D.liste)}
        kand = [g for g in gefunden if g["atom"]["id"] in sig_atome]
        doc_datum = (doc.get("date") or "")[:10]
        if len({g["iso"] for g in kand}) == 1:
            g = kand[0]
            alt = ([{"alternative_value": doc_datum, "alternative_source": f"docs.date (Export, Dokument {doc['id']})",
                     "alternative_note": "Datum des Dokuments im Export; das PDF nennt in der Schlussformel der Exekutive "
                                         "ein anderes Beschlussdatum"}] if doc_datum and doc_datum != g["iso"] else [])
            r_datum = V(g["iso"], {"derivation": "extracted_from_pdf_by_rule",
                                   "rule": "kein Antwortereignis im Export; Datum in der Schlussformel der Exekutive "
                                           "(Einheit signature), genau eines",
                                   "match": "exact", "pdf_evidence": [atom_beleg(g["atom"], g["span"])],
                                   "konsistenz": "metadata_differs" if alt else "confirmed", "alternativen": alt,
                                   "_pdf_datum": (g["atom"]["id"], g["span"])})
        elif doc_datum:
            b = beleg_meta(ddatei, "doc", doc["id"], "date", doc["date"], abruf)
            r_datum = datum_wert(doc["date"], b, gefunden, "kein Antwortereignis; Datum des Antwortdokuments", "close")
    if fassung == "k95" and not r_texte:
        if ev_ant or D.art == "response":
            nicht.append({"not_mapped_item": "ExecutiveResponseStep", "not_mapped_reason":
                          "texts ist Pflicht; der Antworttext steht nicht in diesem Dokument",
                          "candidate_value": f"response_date {r_datum.wert if r_datum else '–'}; responder "
                                             f"{OPD}groups/{exe['id'] if exe else '–'}",
                          "candidate_source": "events (Beantwortet), groups (council_executive)"})
    elif r_texte or (fassung == "i95" and r_datum):
        st = schritt_kopf("response")
        if fassung == "k95":
            st["texts"] = [n for n, _ in r_texte]
            if exe:
                st["responder"] = gruppen_referenz(exe, D.sprache, "k95", abruf,
                                                   "einzige aktive Gruppe council_executive des Parlaments")
            if r_datum:
                st["response_date"] = r_datum
        else:
            if r_datum:
                r_datum.herkunft["rule"] += "; I95 hat kein Antwortdatum: Ende des Antwortschritts (date_end_actual)"
                r_datum.herkunft["match"] = "close"
                st["date_end_actual"] = r_datum
            if exe:
                st["responder"] = gruppen_referenz(exe, D.sprache, "i95", abruf,
                                                   "einzige aktive Gruppe council_executive des Parlaments")
            if r_texte:
                st["texts"] = [n for n, _ in r_texte]
        schritte["response"] = st
    # weitere Ereignisse: im Prototyp nicht abgebildet, aber gemeldet
    for e in meta["events"]:
        if e.get("title_harmonized_id") in (EREIGNIS_EINGEREICHT, EREIGNIS_BEANTWORTET):
            continue
        nicht.append({"not_mapped_item": f"Ereignis {e.get('title_harmonized_de') or e.get('title_de')}",
                      "not_mapped_reason": "nicht Umfang des Prototyps (nur Schritte, die das Dokument oder die "
                                           "Einreichung/Antwort betreffen)",
                      "candidate_value": (e.get("date") or "")[:10], "candidate_source": f"events {e['id']}"})
    nicht.append({"not_mapped_item": "Dokument (FRBR Work/Expression/Manifestation)", "not_mapped_reason":
                  "eCH-0295 kennt nur document_url je TextBlock; Dokumenttitel, Sprache, Datei-Hash und Abrufquelle "
                  "stehen im Profil (SourceDocument, TextBlockRecord title)",
                  "candidate_value": doc_iri, "candidate_source": "docs"})
    nicht.append({"not_mapped_item": "Urheberschaft (sponsorships)", "not_mapped_reason":
                  "im Prototyp nicht übernommen (Datenminimierung); contributors-Export liefert Personen-IDs für "
                  "PersonReference", "candidate_source": "contributors"})
    if fassung == "k95":
        if schritte:
            affair["procedure_steps"] = [schritte[k] for k in ("submission", "response") if k in schritte]
    else:
        if "submission" in schritte:
            affair["submission"] = schritte["submission"]
        if "response" in schritte:
            affair["response_steps"] = [schritte["response"]]
    container = {"__entity__": (container_iri, "Container"),
                 "global_uri": V(container_iri, {"derivation": "identifier_minted",
                                                 "rule": "{Platzhalter}/delivery/{fassung}/affair-{id}/doc-{doc_id}"}),
                 "affairs": [affair]}
    for rec in tb_records:
        if rec["mapping_status"] == "profile_only" and "not_mapped_reason" in rec:
            tb = rec["tb"]
            nicht.append({"not_mapped_item": f"TextBlock {tb['section']}{' (quoted)' if tb['quoted'] else ''}",
                          "not_mapped_reason": rec["not_mapped_reason"], "candidate_value": rec["global_uri"],
                          "candidate_source": "TextBlockRecord"})
    roh = {"tb_records": tb_records, "nicht": nicht, "affair_iri": affair_iri, "container_iri": container_iri,
           "doc_iri": doc_iri, "pdf_titel": pdf_titel}
    return container, roh


def einheit_atome(e: dict, liste: list[dict]) -> list[str]:
    """Atom-IDs einer Einheit (alle Bereiche), eigene Berechnung ohne Taxonomie-Hilfen."""
    pos = {a["id"]: i for i, a in enumerate(liste)}
    return [liste[i]["id"] for b in e["atoms"] for i in range(pos[b["from"]], pos[b["to"]] + 1)]


# ================================================================ Entpacken, Provenienz, Prüfung


def pfad_text(p: tuple) -> str:
    s = ""
    for x in p:
        s += f"[{x}]" if isinstance(x, int) else (("." if s else "") + x)
    return s


def entpacken(knoten: Any, pfad: tuple = (), ent: tuple | None = None, basis: int = 0,
              eintraege: list | None = None, ohne: list | None = None) -> Any:
    """Ersetzt V-Werte durch ihre Werte und sammelt (Pfad, Entität, Slot, V). Blattwerte ohne V landen in ohne."""
    if isinstance(knoten, V):
        slot = ent[1] + "." + ".".join(x for x in pfad[basis:] if isinstance(x, str)) if ent else pfad_text(pfad)
        eintraege.append((pfad, ent[0] if ent else None, slot, knoten))
        return knoten.wert
    if isinstance(knoten, dict):
        if "__entity__" in knoten:
            ent, basis = knoten["__entity__"], len(pfad)
        return {k: entpacken(v, pfad + (k,), ent, basis, eintraege, ohne) for k, v in knoten.items()
                if k != "__entity__"}
    if isinstance(knoten, list):
        return [entpacken(v, pfad + (i,), ent, basis, eintraege, ohne) for i, v in enumerate(knoten)]
    ohne.append(pfad_text(pfad))
    return knoten


def unit_records(tb: dict, D: Dokument) -> list[dict]:
    atom = {a["id"]: a for a in D.liste}
    einheit = {e["id"]: e for e in D.ref["units"]}
    aus = []
    for u in tb["units"]:
        e = einheit[u["id"]]
        ent = [{"decision_kind": "boundary_start", "chosen_value": e["atoms"][0]["from"]},
               {"decision_kind": "unit_type", "chosen_value": e["type"]},
               {"decision_kind": "section", "chosen_value": e["section"]}]
        if e.get("quoted"):
            ent.append({"decision_kind": "quoted", "chosen_value": "true"})
        ent += [{"decision_kind": "refers_to", "chosen_value": r} for r in e.get("refers_to") or []]
        for x in ent:
            x |= {"probability": 1.0, "probability_source": "reference_decomposition", "is_placeholder": True}
        r = {"unit_id": u["id"], "unit_type": u["type"]}
        if u["number"]:
            r["printed_numbers"] = list(u["number"])
        if u["refers_to"]:
            r["refers_to_units"] = list(u["refers_to"])
        r["html_ranges"] = [{"range_start": a, "range_end": b} for a, b in u["html_ranges"]]
        r["atom_evidence"] = [atom_beleg(atom[x]) for x in u["atoms"]]
        r["decisions"] = ent
        aus.append(r)
    return aus


def provenienz_bauen(D: Dokument, fassung: str, roh: dict, eintraege: list, pfade_tb: dict,
                     pruefung: dict) -> dict:
    kopf = tx.atome_kopf(D.doc_id)
    doc = D.meta["doc"]
    pdf = PDF / f"{D.doc_id}.pdf"
    herkunft_ref = D.ref.get("_herkunft") or D.ref.get("_reference") or {}
    lauf = {"script_name": "src/m06_ech_ausgabe.py",
            "decomposition_source": f"{D.ref_quelle} (daten/isolierung/{D.ref_quelle}/{D.doc_id}.json)",
            "decomposition_accepted": bool(herkunft_ref.get("abgenommen", False)),
            "taxonomy_version": herkunft_ref.get("schema_version") or "isolierung-v2",
            "atom_version": kopf["version"], "ech_commit": ECH_COMMIT, "linkml_version": LINKML,
            "datetime_generated": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")}
    if herkunft_ref.get("taxonomie_prompt_hash"):
        lauf["taxonomy_prompt_hash"] = herkunft_ref["taxonomie_prompt_hash"]
    quelle = {"global_uri": roh["doc_iri"], "local_id": D.doc_id, "manifestation_url": as_uri(doc["url_oparl"]),
              "publisher_url": as_uri(doc["url"]), "file_sha256": sha256_datei(pdf), "export_hash": doc.get("hash"),
              "docling_json_sha256": kopf["quelle_sha256"], "atom_fingerprint": kopf["fingerabdruck"],
              "page_count": len(D.dok["seiten"]), "document_language": D.sprache,
              "document_language_source": "Export (docs.language)" if D.sprache_herkunft["derivation"] == "copied_from_metadata"
              else "automatische Spracherkennung (augenschein.csv, sprache_auto)",
              "document_kind": D.aug["dokumentart"]}
    tbr = []
    for rec in roh["tb_records"]:
        tb = rec["tb"]
        r = {"global_uri": rec["global_uri"]}
        if rec["mapping_status"] == "in_ech_instance":
            pfad, ent = pfade_tb[id(rec)]
            r |= {"about_entity": ent, "instance_path": pfad,
                  "ech_slot": {"submission": SCHRITT_KLASSE[fassung]["submission"] + ".texts",
                               "response": SCHRITT_KLASSE[fassung]["response"] + ".texts",
                               "title": "Affair.title"}[rec["ziel"]], "ech_text_type": rec.get("ech_text_type")}
        else:
            r["about_entity"] = roh["affair_iri"]
        r |= {"section_key": tb["section"], "quotation_status": "quoted" if tb["quoted"] else "own_text",
              "mapping_status": rec["mapping_status"]}
        if rec.get("not_mapped_reason"):
            r["not_mapped_reason"] = rec["not_mapped_reason"]
        r["text_form"] = tb["form"]
        if rec["mapping_status"] == "profile_only":
            r["text_content"] = tb["text"]
        r |= {"char_count": len(tb["text"]), "source_document": roh["doc_iri"], "units": unit_records(tb, D),
              "text_changes": {"hyphens_removed": tb["changes"]["hyphen_removed"],
                               "list_markers_removed": [{"range_start": a, "range_end": b}
                                                        for a, b in tb["changes"]["list_marker_removed"]],
                               "empty_atoms": tb["changes"]["empty_atoms"], "nfc_changed": tb["nfc_changed"]}}
        tbr.append({k: v for k, v in r.items() if v not in (None, [], "")} | {"text_changes": r["text_changes"]})
    werte = []
    for pfad, ent, slot, v in eintraege:
        h = v.herkunft
        w = v.wert
        rec = {"about_entity": ent, "instance_path": pfad_text(pfad), "ech_slot": slot,
               "recorded_value": f"sha256:{sha256_text(w)}" if h["derivation"] == "extracted_from_pdf" else str(w),
               "derivation": h["derivation"]}
        if h.get("rule"):
            rec["rule_applied"] = h["rule"]
        rec["mapping_match"] = h.get("match", "not_applicable")
        for k_in, k_aus in (("metadata_evidence", "metadata_evidence"), ("pdf_evidence", "pdf_evidence"),
                            ("alternativen", "alternatives")):
            if h.get(k_in):
                rec[k_aus] = h[k_in]
        rec["pdf_consistency"] = h.get("konsistenz", "not_checked")
        werte.append(rec)
    return {"global_uri": f"{PPD}provenance/{fassung}/affair-{D.meta['affair']['id']}/doc-{D.doc_id}",
            "describes_delivery": roh["container_iri"], "ech_schema_version": FASSUNG_TEXT[fassung],
            "pipeline_run": lauf, "source_documents": [quelle], "text_block_records": tbr,
            "value_records": werte, "not_mapped_records": roh["nicht"],
            "verbatim_check": {
                "check_method": "Jeder Blattwert braucht einen Provenienz-Eintrag; PDF-Texte nach Entfernen der HTML-"
                                "Auszeichnung zeichengenau gegen die Atomtexte der Einheiten (nur Leerraum, Trennstrich "
                                "am Atomende, Listenmarker am Atomanfang dürfen fehlen); Metadatenwerte wörtlich gegen "
                                "den Export-Datensatz; Begriffe gegen die Enums des Schemas; Daten aus dem PDF gegen den "
                                "Treffer im Atom.",
                "text_blocks_checked": pruefung["textbloecke"], "characters_checked": pruefung["zeichen"],
                "hyphens_removed_count": pruefung["trennstriche"],
                "list_markers_removed_count": pruefung["listenmarker"],
                "metadata_values_checked": pruefung["metadaten"],
                "leaves_without_provenance": len(pruefung["ohne_herkunft"]),
                "check_passed": not pruefung["fehler"]}}


def herkunft_pruefen(D: Dokument, fassung: str, roh: dict, eintraege: list, ohne: list) -> dict:
    """Prüfung «kein erzeugter Text» (E19) über alle Blattwerte der Instanz und alle Textblöcke."""
    meta = D.meta
    index = {("doc", str(meta["doc"]["id"])): meta["doc"], ("affair", str(meta["affair"]["id"])): meta["affair"]}
    index |= {("event", str(e["id"])): e for e in meta["events"]}
    index |= {("group", str(g["id"])): g for g in meta["groups"]}
    atom = {a["id"]: a for a in D.liste}
    fehler, n_meta = [], 0
    for p in ohne:
        fehler.append(f"Wert ohne Herkunft: {p}")
    for pfad, _, _, v in eintraege:
        h, w, ort = v.herkunft, v.wert, pfad_text(pfad)
        abl = h["derivation"]
        for b in h.get("metadata_evidence", []):
            rec = index.get((b["record_type"], b["record_id"]))
            if rec is None or str(rec.get(b["field_name"])) != b["source_value"]:
                fehler.append(f"{ort}: Beleg {b['record_type']} {b['record_id']}.{b['field_name']} stimmt nicht mit dem Export")
            n_meta += 1
        if abl == "copied_from_metadata":
            if str(w) != h["metadata_evidence"][0]["source_value"]:
                fehler.append(f"{ort}: Wert weicht vom Exportfeld ab")
        elif abl == "normalized_from_metadata":
            quelle = h["metadata_evidence"][0]
            soll = quelle["source_value"][:10] if h["_norm"] == "datumsteil" else quelle["field_name"].rsplit("_", 1)[-1]
            if str(w) != soll:
                fehler.append(f"{ort}: Normalisierung {h['_norm']} ergibt {soll!r}, nicht {w!r}")
        elif abl == "mapped_from_metadata":
            if w not in enum_werte(*h["_enum"]):
                fehler.append(f"{ort}: {w!r} nicht in {h['_enum'][1]} ({h['_enum'][0]})")
        elif abl == "identifier_from_metadata":
            muster, wid = h["_muster"]
            if w != muster.format(wid):
                fehler.append(f"{ort}: Kennung entspricht nicht dem Muster")
        elif abl == "identifier_minted":
            if not str(w).startswith(PPD):
                fehler.append(f"{ort}: geprägte Kennung ausserhalb des Platzhalter-Namensraums")
        elif abl == "fixed_by_schema":
            if "_equals" in h:
                if w != equals_string(*h["_equals"]):
                    fehler.append(f"{ort}: {w!r} ist nicht equals_string des Schemas")
            elif w not in enum_werte(*h["_enum"]):
                fehler.append(f"{ort}: {w!r} nicht in {h['_enum'][1]}")
        elif abl == "detected_by_rule":
            if w not in SPRACHEN or w != h["_augenschein"]:
                fehler.append(f"{ort}: Sprachcode {w!r} nicht belegt")
        elif abl == "extracted_from_pdf_by_rule":
            aid, (a0, a1) = h["_pdf_datum"]
            treffer = atom[aid]["text"][a0:a1]
            g = [x for x in daten_im_pdf([atom[aid]]) if x["span"] == (a0, a1)]
            if not g or g[0]["iso"] != w:
                fehler.append(f"{ort}: Datum {w} nicht aus dem Treffer {treffer!r} in {aid}")
        elif abl != "extracted_from_pdf":
            fehler.append(f"{ort}: unbekannte Herleitung {abl}")
    # Textblöcke: sichtbarer Text gegen die Atome der Einheiten (alle Blöcke, auch die nur im Profil)
    zeichen = trenn = listen = n_tb = 0
    einheit = {e["id"]: e for e in D.ref["units"]}
    for rec in roh["tb_records"]:
        tb = rec["tb"]
        soll = sorted(x for u in tb["units"] for x in einheit_atome(einheit[u["id"]], D.liste) if atom[x]["text"])
        if sorted(tb["source_atoms"]) != soll:
            fehler.append(f"Textblock {tb['section']}: Quellatome ≠ Atome der Einheiten")
        r = wortlaut_abgleich(sichtbarer_text(tb["text"], tb["form"]), [atom[x]["text"] for x in tb["source_atoms"]])
        n_tb += 1
        zeichen += r["zeichen"]
        if not r["ok"]:
            fehler.append(f"Textblock {tb['section']}: Wortlaut weicht ab bei Zeichen {r['abweichung_ab']} ({r['kontext']!r})")
            continue
        trenn += r["trennstriche"]
        listen += r["listenmarker"]
        if (r["trennstriche"], r["listenmarker"]) != (len(tb["changes"]["hyphen_removed"]),
                                                      len(tb["changes"]["list_marker_removed"])):
            fehler.append(f"Textblock {tb['section']}: Abgleich {r['trennstriche']}/{r['listenmarker']} ≠ Protokoll "
                          f"{len(tb['changes']['hyphen_removed'])}/{len(tb['changes']['list_marker_removed'])}")
    # Jeder PDF-Text der Instanz gehört zu genau einem geprüften Textblock
    for pfad, _, _, v in eintraege:
        if v.herkunft["derivation"] == "extracted_from_pdf" and v.wert != v.herkunft["_textblock"]["tb"]["text"]:
            fehler.append(f"{pfad_text(pfad)}: Text der Instanz ≠ Text des Textblocks")
    return {"textbloecke": n_tb, "zeichen": zeichen, "trennstriche": trenn, "listenmarker": listen,
            "metadaten": n_meta, "ohne_herkunft": ohne, "fehler": fehler,
            "blattwerte": len(eintraege),
            "je_herleitung": {k: sum(1 for *_, v in eintraege if v.herkunft["derivation"] == k)
                              for k in sorted({v.herkunft["derivation"] for *_, v in eintraege})}}


def erzeugen(meta_alle: dict) -> list[dict]:
    ergebnisse = []
    for zelle, doc_id, grund in AUSWAHL:
        D = dokument_laden(zelle, doc_id, grund, meta_alle[doc_id])
        for fassung in ("k95", "i95"):
            container, roh = instanz_bauen(D, fassung)
            eintraege, ohne = [], []
            instanz = entpacken(container, eintraege=eintraege, ohne=ohne)
            # Pfad der TextBlocks für die Seitendatei
            pfade_tb = {}
            for pfad, ent, _, v in eintraege:
                if v.herkunft["derivation"] == "extracted_from_pdf":
                    tb_pfad = pfad[:-3] if fassung == "k95" else pfad[:-1]
                    if fassung == "k95" and pfad[-3:-1] != ("value", 0):
                        tb_pfad = pfad[:-1]
                    pfade_tb[id(v.herkunft["_textblock"])] = (pfad_text(tb_pfad), ent)
            pruefung = herkunft_pruefen(D, fassung, roh, eintraege, ohne)
            prov = provenienz_bauen(D, fassung, roh, eintraege, pfade_tb, pruefung)
            kopf = (f"# eCH-0295-Instanz ({FASSUNG_TEXT[fassung]}), erzeugt von src/m06_ech_ausgabe.py\n"
                    f"# Dokument {zelle} (doc_id {doc_id}), Geschäft {D.meta['affair']['id']}; Zerlegung {D.ref_quelle} "
                    "(nicht abgenommen). Orientiert sich am Entwurfsstand, keine Konformitätsaussage.\n"
                    f"# Provenienz: daten/ech/provenienz/{doc_id}_{fassung}_provenienz.yaml\n")
            schreibe_yaml(AUS / "instanzen" / f"{doc_id}_{fassung}.yaml", instanz, kopf)
            schreibe_json(AUS / "instanzen" / f"{doc_id}_{fassung}.json", instanz)
            pk = (f"# Provenienz-Seitendatei (ParlPDFeCH-Profil, src/m06_ech_profil.yaml) zu "
                  f"daten/ech/instanzen/{doc_id}_{fassung}.yaml\n")
            schreibe_yaml(AUS / "provenienz" / f"{doc_id}_{fassung}_provenienz.yaml", prov, pk)
            schreibe_json(AUS / "provenienz" / f"{doc_id}_{fassung}_provenienz.json", prov)
            zusammen = {"zelle": zelle, "doc_id": doc_id, "affair_id": D.meta["affair"]["id"], "fassung": fassung,
                        "referenz": D.ref_quelle, "sprache": D.sprache, "dokumentart": D.aug["dokumentart"],
                        "affair_type": instanz["affairs"][0].get("affair_type"),
                        "textbloecke_instanz": sum(1 for r in roh["tb_records"] if r["mapping_status"] == "in_ech_instance"),
                        "textbloecke_nur_profil": sum(1 for r in roh["tb_records"] if r["mapping_status"] == "profile_only"),
                        "nicht_abgebildet": [n["not_mapped_item"] for n in roh["nicht"]],
                        "pruefung": {k: v for k, v in pruefung.items() if k != "ohne_herkunft"}}
            ergebnisse.append(zusammen)
            status = "bestanden" if not pruefung["fehler"] else f"{len(pruefung['fehler'])} Fehler"
            print(f"{zelle} {doc_id} {fassung}: {pruefung['blattwerte']} Werte, {pruefung['textbloecke']} Textblöcke, "
                  f"{pruefung['zeichen']} Zeichen abgeglichen; Prüfung «kein erzeugter Text» {status}", flush=True)
            for f in pruefung["fehler"][:10]:
                print("   ", f)
    schreibe_json(AUS / "pruefung_wortlaut.json", ergebnisse)
    return ergebnisse


# ================================================================ Validierung (isoliert über uvx)

HELFER = r'''
import json, sys, yaml
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
schema, klasse, datei = sys.argv[1:4]
v = Validator(schema, validation_plugins=[JsonschemaValidationPlugin(closed=True)])
with open(datei, encoding="utf-8") as fh:
    inst = yaml.safe_load(fh)
aus = []
for r in v.validate(inst, klasse).results:
    e = r.source
    eintrag = {"severity": str(r.severity.value), "message": r.message,
               "path": "/" + "/".join(str(p) for p in e.absolute_path), "validator": e.validator}
    if e.validator in ("anyOf", "oneOf") and e.context:
        zweige = {}
        for c in e.context:
            zweige.setdefault(c.relative_schema_path[0] if c.relative_schema_path else None, []).append(c)
        passend = []
        for idx, cs in zweige.items():
            if any(c.validator == "const" for c in cs):
                continue
            ref = e.schema[e.validator][idx].get("$ref") if isinstance(idx, int) else None
            passend.append({"branch": ref, "errors": [{"message": c.message[:300], "validator": c.validator,
                            "path": "/" + "/".join(str(p) for p in c.absolute_path)} for c in cs]})
        eintrag["branches"] = passend
    aus.append(eintrag)
print(json.dumps(aus, ensure_ascii=False))
'''


def uvx(args: list[str], cwd: Path | None = None, eingabe: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(UVX + args, cwd=cwd, input=eingabe, capture_output=True, text=True, timeout=900)


def validieren_eins(schema: Path, klasse: str, datei: Path, name: str) -> dict:
    """linkml-validate (offizielles Ergebnis) und Detail-Auswertung der Fehler (gleiche Einstellungen:
    JsonschemaValidationPlugin closed=True, Unterklassen der Range eingeschlossen)."""
    speicher_pruefen()
    p = uvx(["linkml-validate", "-s", str(schema), "-C", klasse, str(datei)])
    log = AUS / "validierung" / f"{name}.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    text = (f"$ linkml-validate -s {rel(schema)} -C {klasse} {rel(datei)}\n# {LINKML}, rc={p.returncode}\n"
            + p.stdout + (("\n# stderr (Ende)\n" + "\n".join(p.stderr.strip().splitlines()[-15:])) if p.stderr.strip() else ""))
    log.write_text(text + "\n", encoding="utf-8")
    d = uvx(["python", "-", str(schema), klasse, str(datei)], eingabe=HELFER)
    try:
        detail = json.loads(d.stdout.strip().splitlines()[-1]) if d.stdout.strip() else []
    except json.JSONDecodeError:
        detail = [{"message": "Detail-Auswertung fehlgeschlagen", "stderr": d.stderr[-2000:]}]
    schreibe_json(AUS / "validierung" / f"{name}.json", detail)
    fehler = [z for z in p.stdout.splitlines() if z.startswith("[ERROR]")]
    gueltig = p.returncode == 0 and not fehler and "No issues found" in p.stdout
    return {"name": name, "schema": rel(schema), "klasse": klasse, "datei": rel(datei), "rc": p.returncode,
            "gueltig": gueltig, "fehler": len(fehler), "fehlermeldungen": [re.sub(r"^\[ERROR\] \[[^]]*\] ", "", z)[:400]
                                                                          for z in fehler], "log": rel(log),
            "abbruch": "" if fehler or gueltig else "\n".join(p.stderr.strip().splitlines()[-3:])}


def konvertieren_eins(schema: Path, klasse: str, datei: Path, ziel: Path, name: str) -> dict:
    """linkml-convert nach Turtle. Arbeitsverzeichnis = Ordner des Schemas: linkml-convert löst Importe relativ
    zum Arbeitsverzeichnis auf (so auch die CI der Fachgruppe: cd …/input; linkml-convert -s schema.yaml)."""
    speicher_pruefen()
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if ziel.exists():
        ziel.unlink()
    p = uvx(["linkml-convert", "-s", schema.name, "-C", klasse, "-t", "ttl", "-o", str(ziel), str(datei)], cwd=schema.parent)
    log = AUS / "validierung" / f"{name}.txt"
    letzte = "\n".join(p.stderr.strip().splitlines()[-4:])
    log.write_text(f"$ (cd {rel(schema.parent)}; linkml-convert -s {schema.name} -C {klasse} -t ttl -o {rel(ziel)} "
                   f"{rel(datei)})\n# {LINKML}, rc={p.returncode}\n{p.stdout}\n# stderr (Ende)\n{letzte}\n", encoding="utf-8")
    ok = p.returncode == 0 and ziel.exists() and ziel.stat().st_size > 0
    rdf = {}
    if ok:
        r = uvx(["python", "-", str(ziel)], eingabe=RDF_HELFER)
        try:
            rdf = json.loads(r.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            rdf = {"fehler": r.stderr[-500:]}
    return {"name": name, "schema": rel(schema), "datei": rel(datei), "ziel": rel(ziel) if ok else None, "rc": p.returncode,
            "ok": ok, "fehler": "" if ok else (p.stderr.strip().splitlines() or ["?"])[-1][:400], "log": rel(log)} | rdf


RDF_HELFER = r'''
import json, re, sys, rdflib
g = rdflib.Graph()
g.parse(sys.argv[1], format="turtle")
iris = {str(t) for tr in g for t in tr if isinstance(t, rdflib.URIRef)}
roh = sorted(i for i in iris if not re.match(r"^(https?|urn|mailto):", i))
lit = sum(1 for _, _, o in g if isinstance(o, rdflib.Literal))
print(json.dumps({"tripel": len(g), "literale": lit, "unaufgeloeste_iris": roh[:20], "n_unaufgeloest": len(roh)}))
'''


def validieren(ergebnisse: list[dict]) -> dict:
    val, conv = [], []
    for e in ergebnisse:
        doc_id, fassung = e["doc_id"], e["fassung"]
        inst = AUS / "instanzen" / f"{doc_id}_{fassung}.yaml"
        prov = AUS / "provenienz" / f"{doc_id}_{fassung}_provenienz.yaml"
        schemata = [fassung] + (["k95_motion"] if fassung == "k95" and e["affair_type"] == "motion" else [])
        for s in schemata:
            print(f"  validiere {doc_id} {fassung} gegen {s}", flush=True)
            val.append(validieren_eins(SCHEMA[s], "Container", inst, f"{doc_id}_{fassung}__{s}") | {"doc_id": doc_id, "fassung": fassung, "gegen": s})
        conv.append(konvertieren_eins(SCHEMA[fassung], "Container", inst, AUS / "rdf" / f"{doc_id}_{fassung}.ttl",
                                      f"{doc_id}_{fassung}__{fassung}__ttl") | {"doc_id": doc_id, "fassung": fassung})
        val.append(validieren_eins(PROFIL, "ExtractionRecord", prov, f"{doc_id}_{fassung}_provenienz__profil")
                   | {"doc_id": doc_id, "fassung": fassung, "gegen": "profil"})
        conv.append(konvertieren_eins(PROFIL, "ExtractionRecord", prov, AUS / "rdf" / f"{doc_id}_{fassung}_provenienz.ttl",
                                      f"{doc_id}_{fassung}_provenienz__profil__ttl") | {"doc_id": doc_id, "fassung": fassung})
    lint = uvx(["linkml-lint", str(PROFIL)])
    (AUS / "validierung" / "profil__lint.txt").write_text(f"$ linkml-lint {rel(PROFIL)}\n{lint.stdout}{lint.stderr[-2000:]}",
                                                          encoding="utf-8")
    return {"validierung": val, "konvertierung": conv, "profil_lint": lint.stdout.strip().splitlines()[-1:] or ["?"]}


def kontrollen() -> list[dict]:
    """Beispieldaten der Fachgruppe gegen ihre eigenen Schemata (Einordnung: was gilt schon dort?)."""
    aus = []
    for f in sorted((ECH / "ech-0295_affairs" / "input").glob("data_*.yaml")):
        aus.append(validieren_eins(SCHEMA["i95"], "Container", f, f"kontrolle__i95__{f.stem}") | {"gegen": "i95"})
    for f in sorted((ECH / "ech-0295_affairs" / "03_Example_Pursuits:Affairs").glob("*.yaml")):
        s = "k95_motion" if "motion" in f.name else "k95_pi"
        schema = SCHEMA["k95_motion"] if s == "k95_motion" else SCHEMA["k95"].parent / "ech-0295_affairs_parliamentary_initiative_profile.yaml"
        aus.append(validieren_eins(schema, "Container", f, f"kontrolle__{s}__{f.stem}") | {"gegen": s})
    return aus


# ================================================================ Diagnose an einer Kopie von K95 (keine Ausgabe)

DIAGNOSE_SCHRITTE = [
    ("A", "Slots value (TextBlock) und label (CommitteePosition) als Klassenattribute statt globaler Slots; "
          "verdeckt damit value und label aus schema_common nicht mehr (Instanz unverändert)"),
    ("B", "zusätzlich step_type mit range string statt StepTypeEnum (equals_string verlangt string)"),
    ("C", "zusätzlich affair_uid ohne identifier: true (nur ein Identifier je Klasse)"),
]


def _diagnose_schema(stufe: str, ziel: Path) -> Path:
    """Kopie von K95 mit unveränderter Verzeichnistiefe (Import ../../ech-0292_meta/…) und den Änderungen
    bis zur Stufe. Nur zur Einordnung der Fehler; die Ausgaben beziehen sich immer auf das unveränderte K95."""
    if ziel.exists():
        shutil.rmtree(ziel)
    (ziel / "ech-0292_meta" / "input").mkdir(parents=True)
    k = ziel / "ech-0295_affairs" / "02_LinkML_files"
    k.mkdir(parents=True)
    shutil.copy(ECH / "ech-0292_meta" / "input" / "schema_common.yaml", ziel / "ech-0292_meta" / "input")
    shutil.copy(SCHEMA["k95_motion"], k)
    t = SCHEMA["k95"].read_text(encoding="utf-8")
    s = yaml.safe_load(t)
    stufen = "ABC"[: "ABC".index(stufe) + 1]
    if "A" in stufen:
        for klasse, slot in (("TextBlock", "value"), ("CommitteePosition", "label")):
            definition = s["slots"].pop(slot)
            s["classes"][klasse]["slots"].remove(slot)
            s["classes"][klasse].setdefault("attributes", {})[slot] = definition
    if "B" in stufen:
        s["slots"]["step_type"]["range"] = "string"
    if "C" in stufen:
        s["slots"]["affair_uid"].pop("identifier")
    kopf = "# DIAGNOSE-KOPIE, nicht verwenden: " + "; ".join(f"{x}: {b}" for x, b in DIAGNOSE_SCHRITTE if x in stufen) + "\n"
    (k / "ech-0295_affairs.yaml").write_text(kopf + yaml.safe_dump(s, allow_unicode=True, sort_keys=False, width=200),
                                             encoding="utf-8")
    return k / "ech-0295_affairs.yaml"


def diagnose(ergebnisse: list[dict]) -> list[dict]:
    aus = []
    for stufe, beschreibung in DIAGNOSE_SCHRITTE:
        schema = _diagnose_schema(stufe, AUS / "diagnose" / f"k95_stufe_{stufe}")
        for e in ergebnisse:
            if e["fassung"] != "k95":
                continue
            inst = AUS / "instanzen" / f"{e['doc_id']}_k95.yaml"
            v = validieren_eins(schema, "Container", inst, f"diagnose__{stufe}__{e['doc_id']}_k95") if stufe == "A" else None
            if stufe == "A" and e["affair_type"] == "motion":
                vm = validieren_eins(schema.parent / SCHEMA["k95_motion"].name, "Container", inst,
                                     f"diagnose__{stufe}__{e['doc_id']}_k95_motion")
                aus.append({"stufe": stufe, "aenderung": beschreibung + " (Motion-Profil, importiert die Kopie)",
                            "doc_id": e["doc_id"], "gegen": "k95_motion", "gueltig": vm["gueltig"],
                            "fehler_validierung": vm["fehlermeldungen"], "turtle": None, "fehler_turtle": None})
            c = konvertieren_eins(schema, "Container", inst, AUS / "diagnose" / "rdf" / f"{e['doc_id']}_k95_stufe_{stufe}.ttl",
                                  f"diagnose__{stufe}__{e['doc_id']}_k95__ttl")
            aus.append({"stufe": stufe, "aenderung": beschreibung, "doc_id": e["doc_id"], "gegen": "k95",
                        "gueltig": v["gueltig"] if v else None, "fehler_validierung": v["fehlermeldungen"] if v else None,
                        "turtle": c["ok"], "fehler_turtle": c["fehler"]})
    return aus


# ================================================================ Selbsttest der Prüfungen


def selbsttest() -> dict:
    """Prüft, dass der Wortlaut-Abgleich erlaubte Änderungen annimmt und jede andere Abweichung meldet, und dass
    entpacken() Werte ohne Herkunft findet. Synthetische Fälle und Mutationen echter Textblöcke (K02)."""
    atome = ["1. Erste Zei-", "le mit Trenn-", "strich.", "- Punkt zwei"]
    faelle = [
        ("erlaubt: Trennstriche, Listenmarker", "Erste Zeile mit Trennstrich. Punkt zwei", True),
        ("erlaubt: Trennstrich bleibt", "Erste Zeile mit Trenn-strich. Punkt zwei", True),
        ("geändertes Zeichen", "Erste Zeile mit Trennstrich. Punkt drei", False),
        ("eingefügtes Wort", "Erste neue Zeile mit Trennstrich. Punkt zwei", False),
        ("fehlendes Wort", "Erste mit Trennstrich. Punkt zwei", False),
        ("andere Reihenfolge", "Punkt zwei Erste Zeile mit Trennstrich.", False),
        ("Satzzeichen ergänzt", "Erste Zeile mit Trennstrich. Punkt zwei.", False),
    ]
    ergebnis, fehler = [], []
    for name, text, soll in faelle:
        ist = wortlaut_abgleich(text, atome)["ok"]
        ergebnis.append({"fall": name, "erwartet": soll, "ergebnis": ist})
        if ist != soll:
            fehler.append(name)
    if wortlaut_abgleich("LagerHalle", ["Lager-Halle"])["ok"]:
        fehler.append("Strich mitten im Atom darf nicht wegfallen")
    ohne: list = []
    entpacken({"a": V("x", {}), "b": "frei"}, eintraege=[], ohne=ohne)
    if ohne != ["b"]:
        fehler.append("Wert ohne Herkunft nicht erkannt")
    # Mutationen eines echten Textblocks (K02, Antwort, I95-Richtext)
    dok = tx.lade("117181")
    liste = tx.atome_laden("117181", dok)
    ref, _ = referenz_laden("117181")
    tb = next(b for b in tx.richtext(ref, liste, dok) if b["section"] == "response")
    atom = {a["id"]: a for a in liste}
    quellen = [atom[x]["text"] for x in tb["source_atoms"]]
    sicht = sichtbarer_text(tb["text"], tb["form"])
    mutationen = {"unverändert": (sicht, True)}
    i = sicht.index("steuerpflichtig")
    mutationen["ein Buchstabe geändert"] = (sicht[:i] + "S" + sicht[i + 1:], False)
    mutationen["ein Wort entfernt"] = (sicht.replace("sämtliche ", "", 1), False)
    mutationen["ein Wort eingefügt"] = (sicht.replace("Grundsätzlich ", "Grundsätzlich nicht ", 1), False)
    j = sicht.index("Zu Frage 2")
    mutationen["Zahl geändert"] = (sicht[:j] + "Zu Frage 3" + sicht[j + 10:], False)
    for name, (text, soll) in mutationen.items():
        ist = wortlaut_abgleich(text, quellen)["ok"]
        ergebnis.append({"fall": f"K02 Antwort: {name}", "erwartet": soll, "ergebnis": ist})
        if ist != soll:
            fehler.append(f"K02 Antwort: {name}")
    return {"faelle": ergebnis, "fehler": fehler, "bestanden": not fehler}


# ================================================================ Hauptprogramm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ohne-validierung", action="store_true")
    ap.add_argument("--metadaten-neu", action="store_true")
    ap.add_argument("--selbsttest", action="store_true", help="nur den Selbsttest der Prüfungen")
    args = ap.parse_args()
    ech_stand_pruefen()
    st = selbsttest()
    print(f"Selbsttest der Prüfungen: {len(st['faelle'])} Fälle, {'bestanden' if st['bestanden'] else st['fehler']}")
    if args.selbsttest or not st["bestanden"]:
        for f in st["faelle"]:
            print(f"  {f['fall']}: erwartet {f['erwartet']}, Ergebnis {f['ergebnis']}")
        return
    meta = metadaten_auszug(neu=args.metadaten_neu)
    ergebnisse = erzeugen(meta)
    zusammenfassung: dict[str, Any] = {"erzeugt_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
                                       "ech_commit": ECH_COMMIT, "linkml": LINKML,
                                       "auswahl": [{"zelle": z, "doc_id": d, "grund": g} for z, d, g in AUSWAHL],
                                       "selbsttest": st, "instanzen": ergebnisse}
    if not args.ohne_validierung:
        zusammenfassung |= validieren(ergebnisse)
        print("Kontrollen (Beispieldaten der Fachgruppe)", flush=True)
        zusammenfassung["kontrollen"] = [{k: v for k, v in x.items() if k in ("name", "gegen", "gueltig", "fehler", "abbruch")}
                                         for x in kontrollen()]
        print("Diagnose an Kopien von K95", flush=True)
        zusammenfassung["diagnose"] = diagnose(ergebnisse)
    schreibe_json(AUS / "zusammenfassung.json", zusammenfassung)
    if not args.ohne_validierung:
        with (AUS / "zusammenfassung.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["doc_id", "fassung", "gegen", "gueltig", "fehler", "erste_meldung", "turtle"])
            conv = {(c["doc_id"], c["fassung"], "provenienz" in c["name"]): c for c in zusammenfassung["konvertierung"]}
            for v in zusammenfassung["validierung"]:
                c = conv.get((v["doc_id"], v["fassung"], v["gegen"] == "profil"))
                w.writerow([v["doc_id"], v["fassung"], v["gegen"], v["gueltig"], v["fehler"],
                            (v["fehlermeldungen"] or [v["abbruch"]])[0][:200] if not v["gueltig"] else "",
                            ("ja" if c and c["ok"] else "nein") if v["gegen"] in ("profil", "i95", "k95") else ""])
        for v in zusammenfassung["validierung"]:
            print(f"  {v['doc_id']} {v['fassung']} gegen {v['gegen']}: {'gültig' if v['gueltig'] else 'ungültig'}"
                  f" ({v['fehler']} Fehler)")
        for c in zusammenfassung["konvertierung"]:
            print(f"  Turtle {c['name']}: {'ja' if c['ok'] else 'nein: ' + c['fehler'][:160]}")


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: Apache-2.0
"""Iteration 3, Isolierung: Docling-Blöcke in Atome zerlegen, bevor beschriftet wird.

Frage: Lassen sich alle Elemente eines PDF sauber isolieren? Ohne saubere Isolierung ist
Beschriften sinnlos (ein Block mit den Antworten 1 bis 9 kann keine einzelne Rolle tragen).

Atom = kleinste Einheit, aus der sich jede inhaltliche Einheit zusammensetzen lässt:
- eine Zeile eines Docling-Blocks (Zeilenumbruch im Wortlaut aus den Textzellen,
  m03_docling_zerlegen.py), bei Tabellen eine Tabellenzeile (Zellen mit Tabulator);
- innerhalb einer Zeile zusätzlich geteilt
  * an Spaltenlücken: grosse Lücke zwischen zwei Wörtern derselben Zeile laut Textschicht
    (pdftotext -bbox -cropbox), z.B. zwei Unterschriften oder Feldname und Wert nebeneinander;
    Hängeeinzug nach einer Nummer («8.   Kann …») zählt nicht;
  * an Rahmengrenzen (Docling-Text ohne Zeilen, dessen Rahmen in derselben Zeile liegen);
  * an Satzgrenzen, wenn die Zeile länger als SATZ_AB Zeichen ist (Fliesstext ohne
    Zeilenumbruch); Tabellenzeilen werden nicht an Sätzen geteilt, nur gekennzeichnet.
ID: <Block>.<Zeile> (B12.3), Teile einer Zeile <Block>.<Zeile>.<Teil> (B12.3.2). Blöcke
ohne Text (Bilder) bekommen ein leeres Atom <Block>.1, damit ihre Lage sichtbar bleibt.
Achtung: m03_render.py nennt Teile eines an Antwortmarkern geteilten Blocks
ebenfalls B25.1, B25.2 …; dort ist .n ein Blockteil, hier eine Zeile.

Je Atom: Seite, Blocklabel, schicht/kopf_fuss, Zeichenbereich in text_gesamt, Wortlaut, Rahmen
des Blocks und Zeilenrahmen (aus der Textschicht oder geschätzt), Satzanfänge im Atom.
Merkmale (englische Schlüssel, `merkmale`) mit deutscher Bezeichnung (`hinweise`), nur Hinweise,
keine Entscheidung:
- Form aus Docling (Überschrift, Listenpunkt, Tabelle, Kopf-/Fusszeile, Feld, OCR …);
- Teilung und Lage: Spalten-, Rahmen-, Satzteil, Seitenwechsel (im Block mit Drittel-Regel),
  Zeile über ihrem Vorgänger (Lesereihenfolge springt zurück);
- mögliche Grenzmarker: Bezug auf Frage n, Frage n, Aufzählung, Stichwörter (Antrag,
  Begründung, Antwort, Vorbemerkung, Fragen, Auftrag, Beschluss, Rappel, Urheberschaft),
  Typbezeichnung, Einleitungsformeln (folgende Fragen, wird beauftragt, wie folgt:),
  Unterschrifts- und Grussformeln, Ort und Datum, Verteiler, Seitenzahl, Sperrschrift;
- Schlüssel-Wert-Kandidaten aus Schlüssel-Wert-/Formularbereichen, Rahmen oder Spalten
  nebeneinander und «Schlüssel: Wert» in einer Zeile.

Prüfungen je Dokument: Atome bilden eine vollständige, überschneidungsfreie Zerlegung von
text_gesamt (jedes Zeichen ausser Trennern genau einmal, Trenner nur Leerraum), Wortlaut
gleich text_gesamt[von:bis], jedes Atom in einem Block und einem Rahmen, IDs eindeutig,
Reihenfolge steigend; Anzahl Atome, Längen, lange und kurze Atome, Antwortmarker mitten in
einem Atom. Textschicht-Abgleich: jede Zeile (ohne OCR und Tabellen) wird als Wortfolge einer
physischen Zeile der Textschicht gesucht; daraus Zeilenrahmen, Spaltenlücken und Abweichungen
in der Typografie (Docling ersetzt ’ – „ “ durch ' - "; der Wortlaut der Textschicht steht dann
zusätzlich in text_textschicht). Gegenprobe ohne Zeilen: dieselbe Zerlegung, wenn jeder Block
ein Fliesstext ohne Zeilenumbruch wäre.

Fassungen: atome-v2 (Standard, Runde 1, unverändert reproduzierbar) und atome-v3 (Runde 2).
Für neue Läufe gilt atome-v3 (m03_gold_prepare.py nutzt atome-v3). atome-v3 = atome-v2 und zusätzlich
- Teilung an Satzgrenzen ohne Leerzeichen («…ABC.Am …») auch in kurzen Zeilen (nicht in
  Tabellen; nicht in Adressen, Pfaden, Abfragen; nicht nach Abkürzungen, auch «Name-St.Gallen»);
  die Teile heissen wie andere Teile <Block>.<Zeile>.<Teil>, Teilung sentence_no_space;
- vier Merkmale für Kandidatengrenzen: Folgenummer (Zeile beginnt mit der nächsten Nummer nach
  einer nummerierten Zeile desselben Blocks, z.B. zweite Fussnote), Klammerzeile mit Datum,
  Zitatende (kurze Zeile mit schliessendem Anführungszeichen nach einem Satzende), Zellenzahl
  wechselt (Tabellenzeile mit anderer Zahl gefüllter Zellen als die vorige).
Nicht in atome-v3: Teilung an Tabellenzellen und Feldlücken, Korrektur der Lesereihenfolge.

Kein Netz, kein Modell. Pfade unter dem Datenordner <data> (m03_iso_paths.DATA). Liest <data>/docling/<doc_id>.json, <data>/pdf/augenschein/<doc_id>.pdf
(nur pdftotext) und <data>/analyse/pdf/augenschein.csv.
Schreibt <data>/isolierung/atome/<doc_id>.json und <data>/isolierung/atome_kennzahlen.csv (atome-v2)
bzw. <data>/isolierung/runde2/atome/<doc_id>.json und <data>/isolierung/runde2/atome_kennzahlen.csv
(atome-v3).

  (im Ordner track_2a)
  uv run python src/m03_atome.py                 alle Dokumente in <data>/docling/ (atome-v2)
  uv run python src/m03_atome.py --fassung atome-v3   alle Dokumente, atome-v3 (Runde 2)
  uv run python src/m03_atome.py DOC_ID DOC_ID   einzelne Dokumente (Kennzahlen-CSV nur bei allen)
  uv run python src/m03_atome.py --zeigen DOC_ID Prompt-Form im Terminal (enthält Namen)
  uv run python src/m03_atome.py --selbsttest
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_render import ELTERN, FORM, bloecke_vorbereiten, dokument_rendern  # noqa: E402
from m03_iso_paths import DATA, rel  # noqa: E402
DOCLING = DATA / "docling"
PDF = DATA / "pdf" / "augenschein"
AUGENSCHEIN = DATA / "analyse" / "pdf" / "augenschein.csv"
AUS = DATA / "isolierung" / "atome"
KENNZAHLEN = DATA / "isolierung" / "atome_kennzahlen.csv"

VERSION = "atome-v2"         # Standard: Atome der Runde 1
VERSION_V3 = "atome-v3"      # Runde 2 (Fassung in --fassung)
FASSUNGEN = (VERSION, VERSION_V3)
AUS_V3 = DATA / "isolierung" / "runde2" / "atome"
KENNZAHLEN_V3 = DATA / "isolierung" / "runde2" / "atome_kennzahlen.csv"
SATZ_AB = 200           # Textzeilen über dieser Länge werden an Satzgrenzen geteilt
LANG_AB = 200            # Atome über dieser Länge zählen als lang
KURZ_BIS = 2             # Atome bis zu dieser Länge zählen als kurz
ZEICHEN_JE_TOKEN = 3.48  # Median im Dokumentteil (Schätzung für die Blockform, m03_render.py)
TABELLEN = {"table", "document_index"}
KV_ELTERN = {"key_value_area", "form_area"}
SPALTENLUECKE_PT = 18    # Wortabstand in einer Zeile, ab dem eine Spaltenlücke gilt (und > 3× Median)
RAHMEN_TOLERANZ_PT = 3   # Zeilenmitte darf so weit ausserhalb des Blockrahmens liegen
TEXTSCHICHT_WERKZEUG = "pdftotext -bbox -cropbox (Poppler)"

# Merkmal-Schlüssel (englisch, snake_case) → deutsche Bezeichnung im Prompt; {p} = Parameter
MERKMALE = {
    "form": "{p}", "group": "{p}", "ocr": "OCR", "no_line_breaks": "ohne Zeilen",
    "table_row": "Tabellenzeile {p}", "no_text": "ohne Text",
    "column_part": "Spaltenteil {p}", "frame_part": "Rahmenteil", "sentence_part": "Satzteil {p}",
    "long_line": "lange Zeile", "rotated": "gedreht", "new_frame": "neuer Rahmen",
    "page_break": "Seitenwechsel", "page_break_back": "Seitenwechsel zurück",
    "page_break_in_block": "Seitenwechsel im Block", "thirds_rule_violated": "Drittel-Regel verletzt",
    "above_previous": "über Vorgänger", "outside_frame": "ausserhalb Rahmen",
    "letterspacing": "Sperrschrift", "page_number": "Seitenzahl",
    "answer_reference": "Bezug Frage {p}", "question_number": "Frage {p}", "enumeration": "Aufzählung {p}",
    "keyword": "Stichwort {p}", "affair_type": "Typbezeichnung", "intro_questions": "Einleitung Fragen",
    "demand_formula": "Auftragsformel", "intro_follows": "Einleitung folgt",
    "signature_formula": "Unterschriftsformel", "place_date": "Ort und Datum", "date_line": "Datum",
    "distribution": "Verteiler", "marker_inside": "Marker im Atom",
    "kv_key": "Schlüssel→{p}", "kv_value": "Wert←{p}", "kv_key_without_value": "Schlüssel ohne Wert",
    "kv_value_without_key": "Wert ohne Schlüssel{p}", "kv_inline": "Schlüssel: Wert in Zeile",
}

LEGENDE = {
    "Spalten": "ID | Seite | Hinweise | Text. ID <Block>.<Zeile>, Teil einer Zeile <Block>.<Zeile>.<Teil>.",
    "Text": "Wortlaut der Zeile unverändert; Tabellenzellen mit ¦ getrennt; (ohne Text) = Bild ohne Text.",
    "Form": "Docling-Form des Blocks: Überschrift, Listenpunkt, Tabelle, Verzeichnis, Kopfzeile, Fusszeile, "
            "Fussnote, Bild, Bildlegende, Kästchen; Feld = Schlüssel-Wert-Bereich, Formular, im Bild; "
            "OCR = Texterkennung; ohne Zeilen = Docling-Text ohne Zeilenumbrüche. Ohne Formangabe: Text.",
    "Teile": "Spaltenteil k/n = Zeile an einer grossen Lücke zwischen Wörtern geteilt (Spalten nebeneinander); "
             "Rahmenteil = Zeile über mehrere Rahmen geteilt; Satzteil k/n = an Satzgrenze geteilte lange Zeile; "
             "neuer Rahmen = Block läuft hier in einem weiteren Rahmen weiter; lange Zeile = über 200 Zeichen; "
             "gedreht = einzeiliger Rahmen höher als breit.",
    "Lage": "Seitenwechsel (zurück = Lesereihenfolge springt auf frühere Seite); im Block = derselbe "
            "Docling-Block läuft weiter; Drittel-Regel verletzt = Teil endet nicht im unteren bzw. beginnt "
            "nicht im oberen Seitendrittel, der Block ist vermutlich falsch zusammengefügt; über Vorgänger = "
            "Zeile steht auf der Seite über der vorangehenden Zeile derselben Spalte (Lesereihenfolge springt "
            "zurück); ausserhalb Rahmen = Zeile liegt laut Textschicht nicht im Rahmen ihres Blocks.",
    "Marker": "Bezug Frage n (Zu Frage n, Ad n, Réponse à la question n …), Frage n, Aufzählung <Zeichen>, "
              "Stichwort <Wort>, Typbezeichnung (Motion, Interpellation, Anfrage …), Einleitung Fragen "
              "(folgende Fragen, questions suivantes …), Auftragsformel (wird beauftragt, est chargé …), "
              "Einleitung folgt (wie folgt: …), Unterschriftsformel (auch Gruss- und Protokollformel), "
              "Ort und Datum, Datum, Verteiler, Seitenzahl, Sperrschrift, Marker im Atom (Antwortmarker mit "
              "Doppelpunkt nicht am Atomanfang). Alles nur Kandidaten.",
    "Schlüssel-Wert": "Schlüssel→ID = Feldname, Wert im genannten Atom; Wert←ID = Wert zum genannten Feldnamen; "
                      "Schlüssel ohne Wert; Wert ohne Schlüssel (unter ID = steht unter diesem Wert); "
                      "Schlüssel: Wert in Zeile.",
}

# atome-v3: Merkmale für Kandidatengrenzen
MERKMALE_V3 = {"number_sequence": "Folgenummer {p}", "bracket_date": "Klammerzeile mit Datum",
               "quote_end": "Zitatende", "table_cells_change": "Zellenzahl wechselt"}
LEGENDE_V3 = LEGENDE | {
    "Teile": "Spaltenteil k/n = Zeile an einer grossen Lücke zwischen Wörtern geteilt (Spalten nebeneinander); "
             "Rahmenteil = Zeile über mehrere Rahmen geteilt; Satzteil k/n = an einer Satzgrenze geteilte Zeile "
             "(lange Zeile oder Satzende ohne Leerzeichen wie «…Ende.Neuer Satz»); neuer Rahmen = Block läuft "
             "hier in einem weiteren Rahmen weiter; lange Zeile = über 200 Zeichen; gedreht = einzeiliger Rahmen "
             "höher als breit.",
    "Marker": LEGENDE["Marker"].removesuffix(" Alles nur Kandidaten.")
              + " Folgenummer n (Zeile beginnt mit der nächsten Nummer nach einer nummerierten Zeile desselben "
                "Blocks, z. B. zweite Fussnote im selben Block), Klammerzeile mit Datum, Zitatende (kurze Zeile, "
                "die nach einem Satzende mit einem schliessenden Anführungszeichen endet), Zellenzahl wechselt "
                "(Tabellenzeile mit anderer Zahl gefüllter Zellen als die vorige). Alles nur Kandidaten.",
}

# Werte-Schlüssel in der Ausgabe (englisch) mit deutscher Bezeichnung
TEILUNG = {"sentence": "Satzgrenze", "frame": "Rahmengrenze", "column": "Spaltenlücke",
           "frame_column": "Rahmengrenze und Spaltenlücke"}
TEILUNG_V3 = TEILUNG | {"sentence_no_space": "Satzgrenze ohne Leerzeichen"}


def merkmale_tabelle(fassung: str = VERSION) -> dict:
    return MERKMALE | MERKMALE_V3 if fassung == VERSION_V3 else MERKMALE


def legende(fassung: str = VERSION) -> dict:
    return LEGENDE_V3 if fassung == VERSION_V3 else LEGENDE
KV_ROLLEN = {"key": "Schlüssel", "value": "Wert", "key_value_inline": "Schlüssel und Wert in einer Zeile"}
ZEILENRAHMEN_QUELLE = {"text_layer": "Wortrahmen der Textschicht (pdftotext)",
                       "estimated": "geschätzt: Blockrahmen gleichmässig auf seine Zeilen verteilt"}

# Mögliches Ziel in eCH-0295, falls die Einheit, die mit diesem Merkmal beginnt, die erwartete
# Rolle hat. Nur Hinweis für die spätere Beschriftung, keine Zuordnung. Zwei Fassungen:
# input = ech-0295_affairs/input/schema.yaml (Stand 3cab44d, TextTypeEnum mit submitted, reasoning,
# response, recommendation, title, short_title, summary); kern = 02_LinkML_files/ech-0295_affairs.yaml
# v0.2.0 (TextTypeEnum main_text, reasoning, response, official_communication, note).
MERKMAL_ECH = {
    "keyword:proposal": {"text_type_input": "recommendation", "text_type_kern": None,
                         "bemerkung": "Kern v0.2.0: Antrag als Wert in ExecutiveResponseStep.recommendation "
                                      "(RecommendationEnum), kein eigener Texttyp"},
    "keyword:reasoning": {"text_type_input": "reasoning", "text_type_kern": "reasoning"},
    "keyword:response": {"text_type_input": "response", "text_type_kern": "response"},
    "keyword:preliminary_remark": {"text_type_input": "response", "text_type_kern": "response",
                                   "bemerkung": "nur im Antwortteil; in einem Vorstoss submitted bzw. main_text"},
    "keyword:questions": {"text_type_input": "submitted", "text_type_kern": "main_text"},
    "keyword:demand": {"text_type_input": "submitted", "text_type_kern": "main_text"},
    "keyword:resolution": {"text_type_input": None, "text_type_kern": None,
                           "bemerkung": "kein Texttyp für Beschluss oder Dispositiv (eCH-Befund 11)"},
    "keyword:recall": {"text_type_input": "submitted", "text_type_kern": "main_text",
                       "bemerkung": "zitierter Vorstoss in einer Antwort; nicht doppelt übernehmen, wenn das "
                                    "Original vorliegt"},
    "keyword:sponsorship": {"text_type_input": None, "text_type_kern": None,
                            "bemerkung": "Beleg für die Urheberschaft (input: Affair.sponsorship), kein Text"},
    "affair_type": {"text_type_input": "title", "text_type_kern": None,
                    "bemerkung": "Beleg für affair_type; Titelzeile: input TextTypeEnum.title, Kern v0.2.0 "
                                 "Feld Affair.title statt Texttyp"},
    "question_number": {"text_type_input": "submitted", "text_type_kern": "main_text"},
    "intro_questions": {"text_type_input": "submitted", "text_type_kern": "main_text"},
    "demand_formula": {"text_type_input": "submitted", "text_type_kern": "main_text"},
    "answer_reference": {"text_type_input": "response", "text_type_kern": "response"},
}

# ---------------------------------------------------------------- Muster

MONATE = ("januar|jänner|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|"
          "dezember|janvier|février|fevrier|mars|avril|juin|juillet|août|aout|septembre|octobre|"
          "novembre|décembre|decembre|gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
          "settembre|ottobre|dicembre|schaner|favrer|avrigl|matg|zercladur|fanadur|avust|settember|"
          "october|december")
RX_DATUM = (r"\d{1,2}(?:\.|er)?\s*(?:\d{1,2}\.\s*|(?:d['’]|da\s+|de\s+)?(?:" + MONATE + r")\s+)\d{4}")
RX_ORT_DATUM = re.compile(r"^[A-ZÄÖÜÀ-Ý][\w.'’\- ]{1,40},\s*(?:den\s+|le\s+|il\s+|ils\s+)?"
                          + RX_DATUM + r"\s*$", re.I)
RX_NUR_DATUM = re.compile(r"^(?:(?:den|le|il|ils)\s+)?" + RX_DATUM + r"\s*$", re.I)
RX_SEITENZAHL = re.compile(
    r"^(?:[-–—]\s*\d{1,3}\s*[-–—]|(?:seite|page|pagina|pag\.|p\.|s\.|paginaziun)\s*\d{1,3}"
    r"(?:\s*(?:/|von|de|di|da|sur|of)\s*\d{1,3})?|\d{1,3}\s*(?:/|von|de|di|da|sur)\s*\d{1,3})$", re.I)
RX_SEITENZAHL_KF = re.compile(r"^\d{1,3}\.?$")   # nackte Zahl nur in Kopf- und Fusszeilen

# Bezug auf eine Frage am Atomanfang (typisch Antwort) und Fragenummer (typisch Frage).
NUMMERN = r"(?P<nr>\d{1,2}(?:\s*(?:,|und|bis|et|à|e|ed|a|-|–|u\.)\s*\d{1,2})*)"
RX_BEZUG = re.compile(
    r"^\s*(?:zu\s+(?:den\s+)?(?:frage|fragen|ziffer|ziffern|punkt|punkten)|"
    r"ad(?:\s+(?:frage|fragen|ziffer|punkt|domanda|question|questions))?|"
    r"antwort\s+(?:auf|zu)\s+(?:den\s+)?(?:frage|fragen)?|"
    r"r[ée]ponses?\s+(?:à|a|aux)?\s*(?:la\s+|les\s+)?(?:questions?)?|"
    r"risposta\s+(?:alla|alle)?\s*(?:domanda|domande)?|"
    r"tar\s+las?\s+dumondas?)\s*" + NUMMERN, re.I)
RX_FRAGE = re.compile(r"^\s*(?:frage|question|domanda|quesito|dumonda)\s*(?:n[or°]?\.?\s*)?(?P<nr>\d{1,2})"
                      r"(?=\s*[:.)\-–]|\s*$)", re.I)
# Antwortmarker mit Doppelpunkt irgendwo im Atom (Gegenprobe der Isolierung)
RX_MARKER_IRGENDWO = re.compile(
    r"(?:zu\s+(?:den\s+)?fragen?\s+\d{1,2}(?:\s*(?:,|und|bis)\s*\d{1,2})*|ad\s+\d{1,2}|"
    r"question\s+\d{1,2}|domanda\s+\d{1,2}|tar\s+la\s+dumonda\s+\d{1,2}|"
    r"r[ée]ponse\s+à\s+la\s+question\s+\d{1,2}|risposta\s+alla\s+domanda\s+\d{1,2}|frage\s+\d{1,2})\s*:", re.I)

RX_AUFZ = re.compile(
    r"^(?P<m>\(?\d{1,2}(?:\.\d{1,2}){1,3}\.?(?=\s+[A-ZÄÖÜÀ-Ý])|"     # 2.2.7 Gliederung
    r"\(\d{1,2}\)|\d{1,2}\.(?=\s|$)|\d{1,2}\)(?=\s|[A-Za-zÄÖÜäöüÀ-ÿ«\"(])|"  # (1) 1. 1)
    r"\(?[a-z]\)|[a-k]\.(?=\s+\w\w)|"                                 # a) (a) a.
    r"[IVX]{1,5}[.)](?=\s+[A-ZÄÖÜÀ-Ý])|"                               # II.
    r"[-–—•·▪◦●■□○*>.](?=\s)|o(?=\s+[A-ZÄÖÜ]))")                      # Striche, Punkte
RX_NACH_AUFZ_DATUM = re.compile(r"^\s*(?:" + MONATE + r")\b|^\s*\d", re.I)

# (Schlüssel, deutsche Bezeichnung, Muster am Zeilenanfang)
STICHWORTE = [
    ("proposal", "Antrag", r"antr[aä]ge?|antrag|propositions?|proposta|proposte|conclusions?|empfehlung|"
                           r"recommandations?|raccomandazione"),
    ("reasoning", "Begründung", r"begründung|begruendung|développement|developpement|motivation|"
                                r"exposé des motifs|motivazioni?|motivaziun|giustificazione"),
    ("response", "Antwort", r"antwort|stellungnahme|réponse|reponse|risposta|resposta|prise de position|"
                            r"presa di posizione|parere"),
    ("preliminary_remark", "Vorbemerkung", r"vorbemerkung(?:en)?|allgemeines|allgemeine bemerkungen|einleitung|"
                                           r"remarques? préliminaires?|préambule|considérations générales|"
                                           r"considerazioni generali|premessa|osservazioni (?:preliminari|"
                                           r"introduttive)|introduction|introduzione"),
    ("questions", "Fragen", r"fragen|questions|domande|dumondas|interrogativi"),
    ("demand", "Auftrag", r"auftrag|forderung(?:en)?|demandes?|richiest[ae]|incarico"),
    ("resolution", "Beschluss", r"beschluss|beschlüsse|beschlussentwurf|dispositiv|arrête|décide|décision|"
                                r"risolve|decisione|decreta|decida"),
    ("recall", "Rappel", r"rappel|wortlaut|testo dell"),
    ("sponsorship", "Urheberschaft", r"eingereicht von|erstunterzeichne\w*|mitunterzeichne\w*|"
                                     r"weitere unterschriften|déposée? par|cosignataires?|co-signataires?|"
                                     r"firmatari|cofirmatari|primo firmatario|prima firmataria"),
]
RX_STICHWORTE = [(k, re.compile(r"^(?:" + rx + r")\b", re.I)) for k, _, rx in STICHWORTE]
STICHWORT_DE = {k: de for k, de, _ in STICHWORTE}
RX_BESCHLUSS_ENDE = re.compile(r"\b(?:beschliesst|beschließt|arrête|décide|risolve|decreta|decida)"
                               r"(?:\s+(?:der|die|das|le|la|il)\s+\w+)?\s*:?\s*$", re.I)
RX_BESCHLUSS_LOSE = re.compile(r"(?:beschliesst|beschließt|arrête|décide|risolve|decreta)", re.I)

RX_TYP = re.compile(
    r"^\(?(?:(?:kleine|schriftliche|dringliche|einfache|parlamentarische)\s+)?"
    r"(?:anfrage|interpellation|motion|postulat|richtlinienmotion|finanzmotion|einzelinitiative|"
    r"standesinitiative|behördeninitiative|initiative|petition|interpellanza|interrogazione|mozione|"
    r"postulato|iniziativa(?:\s+parlamentare)?|petizione|question(?:\s+écrite)?(?:\s+urgente)?|"
    r"simple\s+question|résolution|resolution|dumonda|incumbensa|interpellaziun)"
    r"\b(?!\s*\d{1,2}\s*[:.)])", re.I)
# nach der Typbezeichnung: Ende, Nummer, Urheber oder Betreff (sonst Fliesstext: «question qu'…»)
RX_NACH_TYP = re.compile(r"^\s*(?:$|[:(«\"„“\d–-]|(?:von|vom|der|des|de|du|di|del|della|dal|da|d'|betreffend|"
                         r"betr\.|concernant|concernente|nr\.?|no\.?|n\.|n°|urgente|écrite|parlamentare)\b)", re.I)
RX_RELATIVSATZ = re.compile(r"\b(?:qui|welche[rsnm]?|che|il quale|la quale)\s+$", re.I)
RX_EINL_FRAGEN = re.compile(
    r"\bfolgende(?:n)?\s+fragen\b|\b(?:ich|wir)\s+(?:frage|fragen|bitte|bitten|ersuche|ersuchen)\s+"
    r"(?:den|die|das)\s+(?:regierung|regierungsrat|stadtrat|gemeinderat|bundesrat)|"
    r"\bquestions?\s+suivantes?\b|\bseguenti\s+domande\b|\bdomande\s+seguenti\b|\bsuandantas?\s+dumondas?\b",
    re.I)
RX_AUFTRAG = re.compile(
    r"\b(?:wird|werden)\s+(?:beauftragt|ersucht|eingeladen|gebeten|aufgefordert)\b|"
    r"\b(?:est|sont)\s+(?:chargée?s?|invitée?s?|priée?s?)\b|"
    r"\b(?:è|sono)\s+(?:incaricat|invitat)[oaie]\b|\bvegn(?:an)?\s+(?:incumbensad|envidad)[ai]\b", re.I)
RX_EINL_FOLGT = re.compile(r"\b(?:wie\s+folgt|comme\s+(?:il\s+)?suit|come\s+segue|teneur\s+suivante|"
                           r"folgenden\s+wortlaut|seguente\s+tenore|seguente\s+testo|sco\s+suonda)\b", re.I)

RX_UNTERSCHRIFT = re.compile(
    r"^(?:mit freundlichen grüssen|mit freundlichem gruss|freundliche grüsse|hochachtungsvoll|"
    r"im namen (?:des|der)|namens (?:des|der)|"
    r"für (?:den|die) (?:regierungsrat|stadtrat|gemeinderat|regierung|gemeindeversammlung)\s*:?\s*$|"
    r"vor dem (?:regierungsrat|stadtrat|gemeinderat|kantonsrat)\s*$|"
    r"(?:der|die) (?:vize)?(?:präsident|präsidentin|staatsschreiber|staatsschreiberin|stadtschreiber|"
    r"stadtschreiberin|gemeindeschreiber|gemeindeschreiberin|ratsschreiber|ratsschreiberin|ratssekretär|"
    r"ratssekretärin|kanzler|kanzlerin|landammann|regierungspräsident|regierungspräsidentin|"
    r"stadtpräsident|stadtpräsidentin|gemeindepräsident|gemeindepräsidentin)\b|"
    r"(?:le|la) (?:vice-)?(?:président|présidente|chancelier|chancelière|secrétaire|syndic|syndique)\b|"
    r"au nom (?:du|de la)|veuillez agréer|nous vous prions d|je vous prie d|"
    r"(?:avec )?(?:nos |mes )?(?:meilleures |sincères |cordiales )?salutations|"
    r"per (?:il|la) (?:consiglio|municipio|cancelleria|commissione)|"
    r"(?:il|la) (?:vice)?(?:presidente|cancelliere|segretario|segretaria|sindaco|sindaca)\b|"
    r"(?:con )?(?:distinti|cordiali|migliori) saluti|con (?:ossequio|stima)|vogliate gradire|"
    r"voglia gradire|gradisca|ci è grata l|en num da|il (?:president|chancelier)\b|"
    r"la (?:presidenta|chancelliera)\b|cun salids|sig\.|\(sig\.?\)|gez\.)", re.I)
RX_VERTEILER = re.compile(
    r"^(?:mitteilung(?:en)? an|verteiler|kopien? (?:an|z\.?\s?k\.?)|kopien?\s*:|z\.?\s?k\.?\s*(?:an|:)|"
    r"zur kenntnis an|geht an|zustellung an|versand an|copies? (?:à|a|conforme)|copies?\s*:|"
    r"communication à|communiqué à|distribution\s*:?\s*$|comunicazione a|intimazione a|"
    r"per conoscenza|copia (?:a|per)|copia\s*:|c\.\s?p\.\s?c\.|communicaziun a)", re.I)

# Schlüssel-Wert: Feldnamen ohne Doppelpunkt, die links neben ihrem Wert stehen
RX_FELDNAME = re.compile(r"^(?:betreffend|betrifft|betr\.?|betreff|gegenstand|objet|concerne|oggetto|"
                         r"concernente|e-?mail|tel\.?|telefon|téléphone|telefono|fax|web|www|internet|"
                         r"homepage|site internet|sito(?: web)?)\s*:?$", re.I)
RX_KV_ZEILE = re.compile(r"^(?P<k>[A-ZÄÖÜÀ-Ý][^:|]{0,38}?)\s*:\s*(?P<v>\S.*)$")

ABKUERZUNGEN = {
    "z", "zb", "bzw", "bspw", "ca", "vgl", "evtl", "ggf", "resp", "sog", "inkl", "exkl", "insb", "gem",
    "betr", "art", "abs", "lit", "ziff", "nr", "no", "n", "s", "bd", "jh", "kap", "anm", "abb", "tab",
    "fig", "mio", "mia", "mrd", "fr", "chf", "dr", "prof", "hr", "frau", "st", "kt", "bst", "dir",
    "reg", "tel", "vs", "lic", "phil", "iur", "oec", "rer", "pol", "dipl", "ing", "arch", "m", "mm",
    "mme", "mmes", "mlle", "al", "cf", "p", "pp", "ch", "let", "chap", "env", "réf", "ref", "cit", "op",
    "éd", "vol", "cpv", "cfr", "ecc", "sig", "sigg", "on", "avv", "dott", "rag", "u", "ua",
    "dh", "idr", "uu", "o", "od", "ff", "f", "sr", "rs", "bbl", "seq", "ss", "lett", "cap", "par", "ch",
}
RX_SATZ = re.compile(r"[.!?…][\"»«”’)\]]*(?P<ws>\s+)(?=[\"«»„“‘(\[]?[A-ZÄÖÜÀ-ÝČŠŽ0-9])")
# atome-v3: Satzende ohne Leerzeichen («…ABC.Am 28.Oktober»): zwei Buchstaben, Satzzeichen, Gross-
# und Kleinbuchstabe; nicht in Adressen, Pfaden und Abfragen (Token mit / = @ \ _ www http)
RX_SATZ_OHNE_LEER = re.compile(r"(?<=[^\W\d_]{2})[.!?](?=[A-ZÄÖÜÀ-ÝČŠŽ][a-zß-ÿ])")
RX_TOKEN_ADRESSE = re.compile(r"[/=@\\_]|www|https?:", re.I)
# atome-v3: Kandidatenmerkmale
RX_NR_ANFANG = re.compile(r"^(\d{1,3})\s+\S")
RX_KLAMMER_DATUM = re.compile(r"^\(.*(?:" + RX_DATUM + r").*\)$", re.I)
RX_ZITATENDE = re.compile(r"[»”“\"]\s*$")
RX_SATZENDE_ZEILE = re.compile(r"[.?!:;][\"»«”’)\]]*\s*$")

# Hängeeinzug: links der Lücke steht nur eine Nummer, ein Aufzählungszeichen oder ein Artikel
RX_EINZUG = re.compile(r"^(?:\(?\d{1,2}(?:\.\d{1,2})*[.)]?|\(?[a-z]\)|[IVX]{1,5}[.)]|art\.?\s*\d+\w*"
                       r"(?:\s+(?:bis|ter|quater))?|§\s*\d+\w*|"
                       r"(?:annexe|anhang|allegato|partie|teil|parte|kapitel|chapitre|capitolo|titre|titel|"
                       r"titolo)\s+[\w.]+|[-–—•·▪◦●■□○*>])$", re.I)

# Typografie: Docling (docling-parse) gibt ’ – „ “ als ' - " aus; für den Abgleich gleichsetzen.
TYPO = str.maketrans({"’": "'", "‘": "'", "‚": "'", "‛": "'", "′": "'", "“": '"', "”": '"', "„": '"',
                      "‟": '"', "″": '"', "–": "-", "—": "-", "‒": "-", "―": "-", "‑": "-", "‐": "-",
                      "­": "-"})


# ---------------------------------------------------------------- Hilfsfunktionen

def sha256_datei(pfad: Path) -> str:
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def innen(t: str, a: int, e: int) -> tuple[int, int]:
    """Bereich [a, e) ohne Leerraum am Rand."""
    while a < e and t[a].isspace():
        a += 1
    while e > a and t[e - 1].isspace():
        e -= 1
    return a, e


def abkuerzung(t: str, punkt: int) -> bool:
    """Steht der Punkt an Position punkt hinter einer Abkürzung, Initiale oder Ordnungszahl?"""
    m = re.search(r"(\S+)$", t[:punkt])
    if not m:
        return False
    wort = m.group(1).lstrip("(«\"„“'[")
    if not wort:
        return False
    if re.fullmatch(r"(?:[^\W\d_]{1,3}\.)+[^\W\d_]{0,3}", wort):   # z.B, d.h, u.a, S.A
        return True
    w = wort.lower()
    if w in ABKUERZUNGEN:
        return True
    if len(wort) == 1 and wort.isalpha():  # Initiale
        return True
    if wort.isdigit() and len(wort) <= 2:  # 17. Juni, 1. Lesung
        return True
    if re.fullmatch(r"[IVX]{1,5}", wort):  # Ziff. II.
        return True
    return False


def satzgrenzen(t: str, a: int, e: int) -> list[tuple[int, int]]:
    """(Punkt, Beginn des nächsten Satzes) für alle Satzgrenzen in t[a:e]."""
    aus = []
    for m in RX_SATZ.finditer(t, a, e):
        if t[m.start()] == "." and abkuerzung(t, m.start()):
            continue
        aus.append((m.start("ws"), m.end("ws")))
    return aus


def satzgrenzen_ohne_leerzeichen(t: str, a: int, e: int) -> list[int]:
    """atome-v3: Positionen in t[a:e], an denen nach einem Satzende ohne Leerzeichen der nächste Satz
    beginnt («…ABC.Am»). Nicht nach Abkürzungen (auch im letzten Teil eines Bindestrich-Worts,
    «Name-St.Gallen») und nicht in Tokens, die wie Adresse, Pfad oder Abfrage aussehen."""
    aus = []
    for m in RX_SATZ_OHNE_LEER.finditer(t, a, e):
        p = m.start()
        ta, te = p, p
        while ta > a and not t[ta - 1].isspace():
            ta -= 1
        while te < e and not t[te].isspace():
            te += 1
        if RX_TOKEN_ADRESSE.search(t[ta:te]):
            continue
        wort = re.split(r"[-–/]", t[ta:p])[-1].lstrip("(«\"„“'[")
        if t[p] == "." and (abkuerzung(t, p) or wort.lower() in ABKUERZUNGEN or len(wort) <= 1):
            continue
        aus.append(p + 1)
    return aus


def ohne_leerzeichen_teilen(t: str, teile: list[tuple]) -> list[tuple]:
    """atome-v3: Teile (von, bis, Art) einer Zeile zusätzlich an Satzgrenzen ohne Leerzeichen teilen;
    neue Teile haben die Art sentence_no_space."""
    aus = []
    for x, y, art in teile:
        schnitte = satzgrenzen_ohne_leerzeichen(t, x, y)
        if not schnitte:
            aus.append((x, y, art))
            continue
        for p, q in zip([x] + schnitte, schnitte + [y]):
            p, q = innen(t, p, q)
            if q > p:
                aus.append((p, q, "sentence_no_space"))
    return aus


def satzteile(t: str, a: int, e: int) -> list[tuple[int, int]]:
    """Teilbereiche von t[a:e] an Satzgrenzen, ohne Leerraum an den Grenzen."""
    teile, start = [], a
    for ende, naechster in satzgrenzen(t, a, e):
        teile.append((start, ende))
        start = naechster
    teile.append((start, e))
    aus = []
    for x, y in teile:
        x, y = innen(t, x, y)
        if y > x:
            aus.append((x, y))
    return aus


def sperrschrift(t: str) -> str | None:
    """Zusammengezogener Text, wenn die Zeile in Sperrschrift steht (M U N I C I P I O)."""
    tok = t.split()
    if len(tok) >= 4 and sum(1 for x in tok if len(x) == 1) >= 0.8 * len(tok):
        return re.sub(r"\s{2,}", " ", re.sub(r"(?<=\S) (?=\S)", "", t)).strip()
    return None


def ohne_aufzaehlung(t: str) -> tuple[str, str | None]:
    """(Rest, Aufzählungszeichen) – Daten am Zeilenanfang (17. Juni) zählen nicht."""
    m = RX_AUFZ.match(t)
    if not m:
        return t, None
    zeichen = m.group("m")
    rest = t[m.end():]
    if re.fullmatch(r"\d{1,2}\.", zeichen) and RX_NACH_AUFZ_DATUM.match(rest):
        return t, None
    if re.fullmatch(r"[IVX]\.", zeichen) and len(t) <= 25:   # Initiale wie «V. Name»
        return t, None
    return rest.lstrip(), zeichen


def merk(a: dict, schluessel: str, p: str | None = None) -> None:
    a["merkmale"].append([schluessel, p])


def hat(a: dict, *schluessel: str) -> bool:
    return any(k in schluessel for k, _ in a.get("merkmale", []))


def bezeichnung(schluessel: str, p: str | None) -> str:
    if schluessel == "keyword":
        p = STICHWORT_DE.get(p, p)
    elif schluessel == "kv_value_without_key":
        p = f" (unter {p})" if p else ""
    return (MERKMALE.get(schluessel) or MERKMALE_V3[schluessel]).format(p=p)


def grenzmarker(text: str, label: str, n_zeilen_block: int, kopf_fuss: str | None) -> list[tuple[str, str | None]]:
    """Merkmale möglicher Grenzen am Anfang eines Atoms (Schlüssel, Parameter)."""
    aus: list[tuple[str, str | None]] = []
    t = text.strip()
    if not t:
        return aus
    zusammen = sperrschrift(t)
    if zusammen:
        aus.append(("letterspacing", None))
        t = zusammen
    if RX_SEITENZAHL.match(t) or (kopf_fuss and RX_SEITENZAHL_KF.match(t)):
        aus.append(("page_number", None))
        return aus
    m = RX_BEZUG.match(t)
    if m:
        aus.append(("answer_reference", ", ".join(re.findall(r"\d{1,2}", m.group("nr")))))
    else:
        m = RX_FRAGE.match(t)
        if m:
            aus.append(("question_number", m.group("nr")))
    rest, zeichen = ohne_aufzaehlung(t)
    if zeichen and not m:
        aus.append(("enumeration", zeichen))
    kopfartig = label in {"section_header", "title"} or (len(rest) <= 60 and n_zeilen_block <= 2)
    for schluessel, rx in RX_STICHWORTE:
        ms = rx.match(rest)
        if ms and (kopfartig or rest[ms.end():].lstrip().startswith(":") or not rest[ms.end():].strip(" :")):
            aus.append(("keyword", schluessel))
            break
    else:
        if (len(rest) <= 100 and RX_BESCHLUSS_ENDE.search(rest)) or (
                zusammen and RX_BESCHLUSS_LOSE.search(zusammen)):
            aus.append(("keyword", "resolution"))
    mt = RX_TYP.match(rest)
    if mt and (kopfartig or RX_NACH_TYP.match(rest[mt.end():])):
        aus.append(("affair_type", None))
    if RX_EINL_FRAGEN.search(t):
        aus.append(("intro_questions", None))
    if any(not RX_RELATIVSATZ.search(t[:ma.start()]) for ma in RX_AUFTRAG.finditer(t)):
        aus.append(("demand_formula", None))
    if RX_EINL_FOLGT.search(t) and t.rstrip().endswith(":"):
        aus.append(("intro_follows", None))
    if RX_UNTERSCHRIFT.match(rest):
        aus.append(("signature_formula", None))
    if RX_ORT_DATUM.match(t):
        aus.append(("place_date", None))
    elif RX_NUR_DATUM.match(t):
        aus.append(("date_line", None))
    if RX_VERTEILER.match(rest):
        aus.append(("distribution", None))
    return aus


def form_merkmale(b: dict) -> list[tuple[str, str | None]]:
    aus = []
    label = b.get("label") or ""
    if label and label != "text":
        aus.append(("form", FORM.get(label, label)))
    eltern = (b.get("eltern") or {}).get("label")
    if eltern in ELTERN:
        aus.append(("group", ELTERN[eltern]))
    if (b.get("ocr_anteil") or 0) >= 0.5:
        aus.append(("ocr", None))
    if b.get("text_quelle") == "docling" and b.get("text"):
        aus.append(("no_line_breaks", None))
    return aus


def rahmen_des_blocks(b: dict) -> list[dict]:
    if b.get("prov"):
        return [{"seite": p["seite"], "bbox": p["bbox"], "zeichen": p.get("zeichen")} for p in b["prov"]]
    return [{"seite": b.get("seite"), "bbox": b.get("bbox"), "zeichen": b.get("zeichen")}]


def rahmen_fuer(rahmen: list[dict], pos: int) -> int:
    for i, r in enumerate(rahmen):
        z = r.get("zeichen")
        if z and z[0] <= pos < z[1]:
            return i
    return 0


def gedreht(a: dict, zeilen_im_rahmen: dict[tuple, set]) -> bool:
    """Einzeilige Rahmen, die deutlich höher als breit sind (gedrehter Text, S1)."""
    bb = a.get("rahmen")
    if not bb or len(a["text"]) < 4 or len(zeilen_im_rahmen[(a["block"], a["rahmen_nr"])]) != 1:
        return False
    return (bb[3] - bb[1]) > 1.5 * (bb[2] - bb[0])


def drittel_ok(vor: dict, nach: dict, hoehen: dict[int, float]) -> bool:
    """Drittel-Regel: erster Teil endet im unteren, zweiter beginnt im oberen Drittel."""
    hv, hn = hoehen.get(vor["seite"]), hoehen.get(nach["seite"])
    if not hv or not hn or not vor.get("bbox") or not nach.get("bbox"):
        return True
    return vor["bbox"][3] >= 2 * hv / 3 and nach["bbox"][1] <= hn / 3


def median_zahl(werte) -> int | float:
    m = statistics.median(werte)
    return int(m) if float(m).is_integer() else round(m, 1)


# ---------------------------------------------------------------- Zerlegung

def zerlegen(dok: dict, satz_ab: int = SATZ_AB, ohne_zeilen: bool = False,
             spalten: dict[str, set[int]] | None = None, fassung: str = VERSION) -> list[dict]:
    """Atome eines Docling-Dokuments in Lesereihenfolge.

    spalten: Block-ID → Zeichenpositionen in text_gesamt, an denen eine Zeile an einer
    Spaltenlücke geteilt wird (aus spaltenschnitte()).
    ohne_zeilen=True ist die Gegenprobe: Zeilenumbrüche gelten als Leerzeichen, jeder Block
    ist eine einzige Zeile (wie bei einem Zerleger ohne Zeilen).
    fassung atome-v3: zusätzlich Teilung an Satzgrenzen ohne Leerzeichen (nicht in Tabellen)."""
    spalten = spalten or {}
    atome: list[dict] = []
    for b in dok["bloecke"]:
        t = b.get("text") or ""
        z0 = (b.get("zeichen") or [0, 0])[0]
        label = b.get("label") or ""
        rahmen = rahmen_des_blocks(b)
        basis = {
            "block": b["id"], "label": label, "schicht": b.get("schicht"), "kopf_fuss": b.get("kopf_fuss"),
            "eltern": (b.get("eltern") or {}).get("label"),
            "eltern_ref": (b.get("eltern") or {}).get("ref"),
        }
        if not t.strip():
            r = rahmen[0]
            atome.append(basis | {"id": f"{b['id']}.1", "zeile": 1, "teil": None, "teile": None,
                                  "teilung": None, "seite": r["seite"], "rahmen_nr": 0, "rahmen": r["bbox"],
                                  "zeichen": [z0, z0], "text": "", "zellen": None})
            continue
        if ohne_zeilen:
            zeilen_bereiche = [(0, len(t))]
        else:
            zeilen_bereiche, pos = [], 0
            for zeile in t.split("\n"):
                zeilen_bereiche.append((pos, pos + len(zeile)))
                pos += len(zeile) + 1
        # Schnitte relativ zum Block: Rahmenanfänge und Spaltenlücken
        schnitte = {r["zeichen"][0] - z0: "frame" for r in rahmen if r.get("zeichen")}
        schnitte.pop(0, None)
        for s in spalten.get(b["id"], ()):
            schnitte.setdefault(s - z0, "column")
        tabelle = label in TABELLEN
        for k, (a, e) in enumerate(zeilen_bereiche, 1):
            a, e = innen(t, a, e)
            if e <= a:
                continue
            stuecke, x, arten = [], a, set()
            for s in sorted(schnitte):
                if x < s < e:
                    stuecke.append((x, s))
                    arten.add(schnitte[s])
                    x = s
            stuecke.append((x, e))
            art_zeile = (None if len(stuecke) == 1 else
                         "frame" if arten == {"frame"} else "column" if arten == {"column"} else "frame_column")
            teile = []
            for x, y in stuecke:
                x, y = innen(t, x, y)
                if y <= x:
                    continue
                if not tabelle and y - x > satz_ab:
                    st = satzteile(t, x, y)
                    if len(st) > 1:
                        teile += [(p, q, "sentence") for p, q in st]
                        continue
                teile.append((x, y, art_zeile))
            if fassung == VERSION_V3 and not tabelle and not ohne_zeilen:
                teile = ohne_leerzeichen_teilen(t, teile)
            for j, (x, y, art) in enumerate(teile, 1):
                rnr = rahmen_fuer(rahmen, z0 + x)
                r = rahmen[rnr]
                zellen_ber = None
                if tabelle:
                    zellen_ber, q = [], x
                    for zelle in t[x:y].split("\t"):
                        p0, p1 = innen(t, q, q + len(zelle))
                        if p1 > p0:
                            zellen_ber.append([z0 + p0, z0 + p1])
                        q += len(zelle) + 1
                atome.append(basis | {
                    "zellen": zellen_ber,
                    "id": f"{b['id']}.{k}" if len(teile) == 1 else f"{b['id']}.{k}.{j}",
                    "zeile": k, "teil": None if len(teile) == 1 else j,
                    "teile": None if len(teile) == 1 else len(teile),
                    "teilung": art if len(teile) > 1 else None,
                    "seite": r["seite"], "rahmen_nr": rnr, "rahmen": r["bbox"],
                    "zeichen": [z0 + x, z0 + y], "text": t[x:y],
                })
    return atome


# ---------------------------------------------------------------- Textschicht-Abgleich

RX_WORT = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def pdf_woerter(pfad: Path) -> dict[int, list[tuple[float, float, float, float, str]]]:
    """Wörter je Seite aus der Textschicht. -cropbox: Koordinaten wie Docling (Ursprung oben
    links der CropBox, PDF-Punkte); ohne -cropbox sind sie bei K05 um die CropBox verschoben."""
    try:
        out = subprocess.run(["pdftotext", "-bbox", "-cropbox", str(pfad), "-"], capture_output=True,
                             text=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    seiten = {}
    for nr, teil in enumerate(out.split("<page ")[1:], 1):
        seiten[nr] = [(float(a), float(b), float(c), float(d), html.unescape(t))
                      for a, b, c, d, t in RX_WORT.findall(teil)]
    return seiten


def kern_index(t: str, typo: bool = True) -> tuple[str, list[int]]:
    """Zeichen ohne Leerraum (Typografie gleichgesetzt) und ihre Positionen in t."""
    zeichen, idx = [], []
    for i, c in enumerate(t):
        if not c.isspace():
            zeichen.append(c)
            idx.append(i)
    s = "".join(zeichen)
    return (s.translate(TYPO) if typo else s), idx


def reihen_bilden(ws: list[tuple]) -> list[list[tuple]]:
    """Physische Zeilen einer Seite: Wörter mit ähnlicher Mitte (y), je Zeile nach x geordnet.
    Spalten auf gleicher Höhe landen in derselben physischen Zeile. Massstab ist die kleinere
    Worthöhe, nicht die der Seite: sonst verschmelzen kleine Kopfzeilen mit Zeilen darunter."""
    if not ws:
        return []
    reihen: list[dict] = []
    for w in sorted(ws, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        yc, h = (w[1] + w[3]) / 2, max(w[3] - w[1], 1.0)
        if reihen and abs(yc - reihen[-1]["yc"]) <= 0.35 * min(h, reihen[-1]["h"]):
            r = reihen[-1]
            r["w"].append(w)
            r["yc"] += (yc - r["yc"]) / len(r["w"])
            r["h"] = min(r["h"], h)
        else:
            reihen.append({"yc": yc, "h": h, "w": [w]})
    return [sorted(r["w"], key=lambda w: w[0]) for r in reihen]


def _umriss(ws: list) -> list[float]:
    return [round(min(w[0] for w in ws), 2), round(min(w[1] for w in ws), 2),
            round(max(w[2] for w in ws), 2), round(max(w[3] for w in ws), 2)]


def zeilen_abgleich(dok: dict, atome: list[dict], woerter: dict[int, list[tuple]]) -> tuple[dict, dict]:
    """Sucht jede Atom-Zeile als zusammenhängende Wortfolge einer physischen Zeile der Textschicht.

    Nur Seiten mit Textquelle «pdf» oder «gemischt», Blöcke ohne OCR, keine Tabellen. Vergleich
    ohne Leerraum, Typografie gleichgesetzt (TYPO). Unter mehreren Treffern gilt der oberste
    unbenutzte im Rahmen des Blocks; liegt keiner im Rahmen, nur ein eindeutiger Treffer knapp
    ausserhalb (höchstens anderthalb Zeilenhöhen, Merkmal ausserhalb Rahmen). Ergebnis: (Block, Zeile) → Treffer mit Wörtern, deren
    Zeichenbereich in text_gesamt und Rahmen; dazu Zähler."""
    g = dok.get("text_gesamt") or ""
    textseiten = {s["seite"] for s in dok.get("seiten", []) if s.get("textquelle") in ("pdf", "gemischt")}
    bloecke = {b["id"]: b for b in dok["bloecke"]}
    zeilen: dict[tuple, list[dict]] = {}
    for a in atome:
        b = bloecke[a["block"]]
        if (not a["text"] or a["seite"] not in textseiten or (b.get("ocr_anteil") or 0) > 0
                or a["label"] in TABELLEN):
            continue
        zeilen.setdefault((a["block"], a["zeile"]), []).append(a)
    reihen = {s: reihen_bilden(ws) for s, ws in woerter.items()}
    kerne = {s: [[kern_index(w[4])[0] for w in r] for r in rs] for s, rs in reihen.items()}
    benutzt: set[tuple] = set()
    treffer: dict[tuple, dict] = {}
    z = {"ts_zeilen": len(zeilen), "ts_gefunden": 0, "ts_ausserhalb_rahmen": 0, "ts_typografie": 0,
         "ts_nicht_gefunden": 0}
    for (blk, nr), teile in zeilen.items():
        s = teile[0]["seite"]
        x0, x1 = teile[0]["zeichen"][0], teile[-1]["zeichen"][1]
        ziel, idx = kern_index(g[x0:x1])
        kandidaten = []
        if all(t["seite"] == s for t in teile) and ziel:
            for ri, (r, kr) in enumerate(zip(reihen.get(s, []), kerne.get(s, []))):
                for i in range(len(r)):
                    if not kr[i] or (s, ri, i) in benutzt or not ziel.startswith(kr[i]):
                        continue
                    j, n = i, len(kr[i])
                    while (n < len(ziel) and j + 1 < len(r) and kr[j + 1]
                           and (s, ri, j + 1) not in benutzt and ziel.startswith(kr[j + 1], n)):
                        j += 1
                        n += len(kr[j])
                    if n == len(ziel):
                        kandidaten.append((ri, i, j))
        if not kandidaten:
            z["ts_nicht_gefunden"] += 1
            continue
        rahmen = [r["bbox"] for r in rahmen_des_blocks(bloecke[blk]) if r["seite"] == s and r.get("bbox")]

        def im_rahmen(bb: list[float], t_: float) -> bool:
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            return any(r[0] - t_ <= cx <= r[2] + t_ and r[1] - t_ <= cy <= r[3] + t_ for r in rahmen)

        umrisse = {c: _umriss(reihen[s][c[0]][c[1]:c[2] + 1]) for c in kandidaten}
        drin = [c for c in kandidaten if im_rahmen(umrisse[c], RAHMEN_TOLERANZ_PT)]
        # knapp ausserhalb (höchstens anderthalb Zeilenhöhen): Rahmen von Docling zu eng oder überlappend
        nah = [c for c in kandidaten
               if im_rahmen(umrisse[c], max(RAHMEN_TOLERANZ_PT, 1.5 * (umrisse[c][3] - umrisse[c][1])))]
        if drin:
            wahl, aussen = min(drin, key=lambda c: (umrisse[c][1], umrisse[c][0])), False
        elif len(nah) == 1:
            wahl, aussen = nah[0], True
        else:
            z["ts_nicht_gefunden"] += 1
            continue
        ri, i, j = wahl
        ws = reihen[s][ri][i:j + 1]
        benutzt.update((s, ri, q) for q in range(i, j + 1))
        liste, n = [], 0
        for w in ws:
            k = kern_index(w[4])[0]
            liste.append({"bbox": list(w[:4]), "text": w[4], "zeichen": [x0 + idx[n], x0 + idx[n + len(k) - 1] + 1]})
            n += len(k)
        roh_atom = kern_index(g[x0:x1], typo=False)[0]
        roh_pdf = "".join(kern_index(w[4], typo=False)[0] for w in ws)
        treffer[(blk, nr)] = {"seite": s, "woerter": liste, "ausserhalb": aussen, "typografie": roh_atom != roh_pdf}
        z["ts_gefunden"] += 1
        z["ts_ausserhalb_rahmen"] += int(aussen)
        z["ts_typografie"] += int(roh_atom != roh_pdf)
    return treffer, z


def spaltenschnitte(treffer: dict[tuple, dict]) -> dict[str, set[int]]:
    """Schnittstellen an Spaltenlücken: Lücke > SPALTENLUECKE_PT und > 3× Median der übrigen
    Lücken der Zeile, links davon nicht nur Nummer oder Aufzählungszeichen (Hängeeinzug)."""
    schnitte: dict[str, set[int]] = {}
    for (blk, _), t in treffer.items():
        ws = t["woerter"]
        luecken = [ws[k + 1]["bbox"][0] - ws[k]["bbox"][2] for k in range(len(ws) - 1)]
        for k, lu in enumerate(luecken):
            andere = luecken[:k] + luecken[k + 1:]
            if lu <= SPALTENLUECKE_PT or (andere and lu <= 3 * statistics.median(andere)):
                continue
            links = [w["text"] for w in ws[:k + 1]]
            if RX_EINZUG.match(" ".join(links)) or RX_EINZUG.match("".join(links)):
                continue
            schnitte.setdefault(blk, set()).add(ws[k + 1]["zeichen"][0])
    return schnitte


def _band(a: dict, pos: dict) -> tuple[float, float] | None:
    """Geschätzte senkrechte Lage einer Zeile: Rahmen gleichmässig auf seine Zeilen verteilt."""
    bb = a.get("rahmen")
    if not bb or (a["block"], a["rahmen_nr"], a["zeile"]) not in pos:
        return None
    i, n = pos[(a["block"], a["rahmen_nr"], a["zeile"])]
    hoehe = (bb[3] - bb[1]) / n
    return bb[1] + i * hoehe, bb[1] + (i + 1) * hoehe


def zeilenpositionen(atome: list[dict]) -> dict[tuple, tuple[int, int]]:
    zeilen: dict[tuple, list[int]] = {}
    for a in atome:
        if a["text"]:
            zl = zeilen.setdefault((a["block"], a["rahmen_nr"]), [])
            if a["zeile"] not in zl:
                zl.append(a["zeile"])
    return {(blk, rnr, z): (i, len(zl)) for (blk, rnr), zl in zeilen.items() for i, z in enumerate(zl)}


def zeilenrahmen_setzen(atome: list[dict], treffer: dict[tuple, dict]) -> None:
    """Zeilenrahmen je Atom aus den Wörtern seines Zeichenbereichs, sonst geschätzt; Wortlaut der
    Textschicht, wenn er sich in der Typografie unterscheidet."""
    pos = zeilenpositionen(atome)
    for a in atome:
        a["zeilenrahmen"], a["zeilenrahmen_quelle"], a["text_textschicht"] = None, None, None
        a["_ausserhalb"] = False
        if not a["text"]:
            continue
        t = treffer.get((a["block"], a["zeile"]))
        ws = [w for w in t["woerter"] if w["zeichen"][0] < a["zeichen"][1] and w["zeichen"][1] > a["zeichen"][0]] \
            if t else []
        if ws:
            a["zeilenrahmen"] = _umriss([w["bbox"] for w in ws])
            a["zeilenrahmen_quelle"] = "text_layer"
            a["_ausserhalb"] = t["ausserhalb"]
            if t["typografie"]:
                roh_a = kern_index(a["text"], typo=False)[0]
                roh_w = "".join(kern_index(w["text"], typo=False)[0] for w in ws)
                if roh_a != roh_w:
                    a["text_textschicht"] = " ".join(w["text"] for w in ws)
            continue
        band = _band(a, pos)
        if band and a.get("rahmen"):
            a["zeilenrahmen"] = [a["rahmen"][0], round(band[0], 2), a["rahmen"][2], round(band[1], 2)]
            a["zeilenrahmen_quelle"] = "estimated"


def ueber_vorgaenger(vor: dict, a: dict) -> bool:
    """Zeile steht über der vorangehenden Zeile derselben Spalte (beide aus der Textschicht)."""
    if (vor["zeilenrahmen_quelle"] != "text_layer" or a["zeilenrahmen_quelle"] != "text_layer"
            or vor["seite"] != a["seite"] or vor["schicht"] != "body" or a["schicht"] != "body"
            or vor["label"] in TABELLEN or a["label"] in TABELLEN):
        return False
    v, b = vor["zeilenrahmen"], a["zeilenrahmen"]
    breite = min(v[2] - v[0], b[2] - b[0])
    if breite <= 0 or min(v[2], b[2]) - max(v[0], b[0]) < 0.5 * breite:
        return False
    return b[1] < v[1] - 0.5 * (v[3] - v[1])


# ---------------------------------------------------------------- Merkmale

def merkmale_v3(a: dict, vorher: dict | None, vorher_text: dict | None, letzte_nr: dict[str, int]) -> list:
    """atome-v3: Merkmale für Kandidatengrenzen (Folgenummer, Klammerzeile mit Datum, Zitatende,
    Zellenzahl wechselt). letzte_nr: Block → Nummer am Anfang der letzten nummerierten Zeile."""
    aus: list[tuple[str, str | None]] = []
    t = a["text"].strip()
    if not t:
        return aus
    m = RX_NR_ANFANG.match(t)
    if m and a["label"] not in TABELLEN and a["teil"] in (None, 1):
        n = int(m.group(1))
        if letzte_nr.get(a["block"]) == n - 1 and not hat(a, "enumeration"):
            aus.append(("number_sequence", str(n)))
        letzte_nr[a["block"]] = n
    if RX_KLAMMER_DATUM.match(t):
        aus.append(("bracket_date", None))
    if (RX_ZITATENDE.search(t) and len(t.split()) <= 5 and vorher_text is not None
            and RX_SATZENDE_ZEILE.search(vorher_text["text"])):
        aus.append(("quote_end", None))
    if (a["label"] in TABELLEN and vorher is not None and vorher["block"] == a["block"] and vorher["text"]
            and len([c for c in vorher["text"].split("\t") if c.strip()])
            != len([c for c in a["text"].split("\t") if c.strip()])):
        aus.append(("table_cells_change", None))
    return aus


def hinweise_setzen(dok: dict, atome: list[dict], fassung: str = VERSION) -> dict:
    """Setzt atom['merkmale'], atom['hinweise'], atom['kv'], atom['satzanfaenge']; gibt Zähler
    für Schlüssel-Wert-Paare zurück (alle anderen Zähler: zaehlen()). atome-v3: zusätzlich
    merkmale_v3()."""
    letzte_nr: dict[str, int] = {}
    bloecke = {b["id"]: b for b in dok["bloecke"]}
    hoehen = {s["seite"]: s["hoehe"] for s in dok.get("seiten", [])}
    zaehler: dict[str, int] = {}

    def zaehle(k: str, n: int = 1) -> None:
        zaehler[k] = zaehler.get(k, 0) + n

    zeilen_je_block: dict[str, int] = {}
    zeilen_im_rahmen: dict[tuple, set] = {}
    for a in atome:
        zeilen_je_block[a["block"]] = max(zeilen_je_block.get(a["block"], 0), a["zeile"])
        zeilen_im_rahmen.setdefault((a["block"], a["rahmen_nr"]), set()).add(a["zeile"])

    vorher = vorher_text = None
    for a in atome:
        a["merkmale"] = []
        b = bloecke[a["block"]]
        for k, p in form_merkmale(b):
            merk(a, k, p)
        if a["label"] in TABELLEN and a["text"]:
            merk(a, "table_row", str(a["zeile"]))
        if a["teilung"] in ("sentence", "sentence_no_space"):
            merk(a, "sentence_part", f"{a['teil']}/{a['teile']}")
        elif a["teilung"] in ("column", "frame_column"):
            merk(a, "column_part", f"{a['teil']}/{a['teile']}")
        elif a["teilung"] == "frame":
            merk(a, "frame_part")
        if not a["text"]:
            merk(a, "no_text")
        elif gedreht(a, zeilen_im_rahmen):
            merk(a, "rotated")
        if len(a["text"]) > LANG_AB:
            merk(a, "long_line")
        if a.get("_ausserhalb"):
            merk(a, "outside_frame")
        if vorher is not None:
            gleich = vorher["block"] == a["block"]
            if a["seite"] != vorher["seite"]:
                if gleich:
                    merk(a, "page_break_in_block")
                    r = rahmen_des_blocks(b)
                    if not drittel_ok(r[vorher["rahmen_nr"]], r[a["rahmen_nr"]], hoehen):
                        merk(a, "thirds_rule_violated")
                else:
                    merk(a, "page_break_back" if (a["seite"] or 0) < (vorher["seite"] or 0) else "page_break")
            elif gleich and a["rahmen_nr"] != vorher["rahmen_nr"] and a["teilung"] not in ("frame", "frame_column"):
                merk(a, "new_frame")
        if a["text"] and vorher_text is not None and ueber_vorgaenger(vorher_text, a):
            merk(a, "above_previous")
        for k, p in grenzmarker(a["text"], a["label"], zeilen_je_block[a["block"]], a["kopf_fuss"]):
            merk(a, k, p)
        if fassung == VERSION_V3:
            for k, p in merkmale_v3(a, vorher, vorher_text, letzte_nr):
                merk(a, k, p)
        # Antwortmarker mit Doppelpunkt, die nicht am Atomanfang stehen
        start = len(a["text"]) - len(a["text"].lstrip())
        if any(mm.start() > start for mm in RX_MARKER_IRGENDWO.finditer(a["text"])):
            merk(a, "marker_inside")
        a["satzanfaenge"] = ([n - a["zeichen"][0] for _, n in satzgrenzen(dok["text_gesamt"], *a["zeichen"])]
                             if a["text"] and a["label"] not in TABELLEN else None)
        a["kv"] = None
        vorher = a
        if a["text"]:
            vorher_text = a
    kv_kandidaten(atome, zaehle)
    for a in atome:
        a["hinweise"] = [bezeichnung(k, p) for k, p in a["merkmale"]]
    return zaehler


def kv_kandidaten(atome: list[dict], zaehle) -> None:
    """Schlüssel-Wert-Kandidaten (nur Hinweise) in drei Formen:
    1. Schlüssel-Wert- und Formularbereiche von Docling: Zeilen gleicher Höhe, Wert rechts;
    2. Rahmen oder Spaltenteile nebeneinander im selben Block (Feldname wie «betreffend» links,
       Inhalt rechts);
    3. «Schlüssel: Wert» in einer Zeile (in Bereichen, Kopf-/Fusszeilen, kurzen Blöcken auf
       Seite 1 und Tabellenzeilen mit Feldname in der ersten Zelle)."""
    pos = zeilenpositionen(atome)

    def setze(a: dict, rolle: str, partner: list[str], schluessel: str, p: str | None = None) -> None:
        a["kv"] = {"rolle": rolle, "partner": partner}
        merk(a, schluessel, p)

    def ueberlappt(b1, b2) -> bool:
        if not b1 or not b2:
            return False
        h = min(b1[1] - b1[0], b2[1] - b2[0])
        return h > 0 and min(b1[1], b2[1]) - max(b1[0], b2[0]) >= 0.5 * h

    # 1. Bereiche
    gruppen: dict[tuple, list[dict]] = {}
    for a in atome:
        if (a["eltern"] in KV_ELTERN and a["text"] and a["teil"] in (None, 1)
                and not hat(a, "rotated")):
            gruppen.setdefault((a["eltern_ref"], a["seite"]), []).append(a)
    for _, gl in gruppen.items():
        info = []
        for a in gl:
            bb = a["rahmen"]
            info.append({"a": a, "x0": bb[0], "x1": bb[2], "band": _band(a, pos),
                         "doppelpunkt": a["text"].rstrip().endswith(":")})
        info = [i for i in info if i["band"]]
        if not info:
            continue
        minx = min(i["x0"] for i in info)
        for i in info:
            i["rechts"] = [j for j in info if j is not i and j["x0"] >= i["x1"] - 2
                           and ueberlappt(i["band"], j["band"])]
            i["links_spalte"] = abs(i["x0"] - minx) <= 6
        paare: list[tuple[dict, dict]] = []
        gepaart: set[int] = set()
        # a) Feldnamen in einer Zeile, Werte in der Zeile darunter (Spalten gleich ausgerichtet)
        reihen: list[list[dict]] = []
        for i in sorted(info, key=lambda i: (i["band"][0], i["x0"])):
            for r in reihen:
                if ueberlappt(r[0]["band"], i["band"]):
                    r.append(i)
                    break
            else:
                reihen.append([i])
        n_doppelpunkt = sum(1 for i in info if i["doppelpunkt"])
        for r1, r2 in zip(reihen, reihen[1:]):
            r1, r2 = sorted(r1, key=lambda i: i["x0"]), sorted(r2, key=lambda i: i["x0"])
            abstand = r2[0]["band"][0] - r1[0]["band"][1]
            if (n_doppelpunkt < 2 and len(r1) == len(r2) >= 2 and 0 <= abstand <= 40
                    and not any(k["doppelpunkt"] for k in r1)
                    and all(abs(k["x0"] - v["x0"]) <= 6 for k, v in zip(r1, r2))
                    and not any(v["doppelpunkt"] for v in r2)):
                for k, v in zip(r1, r2):
                    paare.append((k, v))
                    gepaart |= {id(k), id(v)}
        # b) Feldname links, Wert rechts auf gleicher Höhe. Feldname = endet mit Doppelpunkt
        #    oder (nur in Bereichen mit mindestens zwei solchen) steht in der linken Spalte.
        schluessel = [i for i in info if id(i) not in gepaart and (
            i["doppelpunkt"] or (n_doppelpunkt >= 2 and i["links_spalte"] and i["rechts"]))]
        s_ids = {id(i) for i in schluessel}
        for k in schluessel:
            werte = sorted((j for j in k["rechts"] if id(j) not in gepaart and not j["doppelpunkt"]
                            and id(j) not in s_ids), key=lambda j: j["x0"])
            if not werte and k["doppelpunkt"]:
                # c) Wert unter dem Feldnamen (Unterschriftsblöcke: «Il chancelier:» über dem Namen)
                unten = [j for j in info if id(j) not in gepaart and not j["doppelpunkt"] and id(j) not in s_ids
                         and 0 <= j["band"][0] - k["band"][1] <= 90
                         and min(j["x1"], k["x1"]) - max(j["x0"], k["x0"])
                         >= 0.5 * min(j["x1"] - j["x0"], k["x1"] - k["x0"])]
                werte = sorted(unten, key=lambda j: j["band"][0])[:1]
            for w in werte:
                paare.append((k, w))
                gepaart.add(id(w))
            if werte:
                gepaart.add(id(k))
            elif k["doppelpunkt"]:
                setze(k["a"], "key", [], "kv_key_without_value")
                zaehle("kv_schluessel_ohne_wert")
        werte_von: dict[int, list[str]] = {}
        werte_zu: dict[int, list[str]] = {}
        for k, v in paare:
            werte_zu.setdefault(id(k), []).append(v["a"]["id"])
            werte_von.setdefault(id(v), []).append(k["a"]["id"])
        zaehle("kv_paare", len(paare))
        for i in info:
            if id(i) in werte_zu:
                setze(i["a"], "key", werte_zu[id(i)], "kv_key", "+".join(werte_zu[id(i)]))
            if id(i) in werte_von:
                if i["a"]["kv"] is None:
                    setze(i["a"], "value", werte_von[id(i)], "kv_value", "+".join(werte_von[id(i)]))
                else:
                    i["a"]["kv"]["wert_von"] = werte_von[id(i)]
                    merk(i["a"], "kv_value", "+".join(werte_von[id(i)]))
        # d) Wert ohne Feldnamen: rechts der Feldnamen-Spalte, zwischen gepaarten Zeilen
        links_paare = [(k, v) for k, v in paare if v["x0"] >= k["x1"] - 2]
        if not links_paare:
            continue
        spalte = min(k["x1"] for k, _ in links_paare) - 2
        oben = min(k["band"][0] for k, _ in links_paare)
        unten_g = max(max(k["band"][1], v["band"][1]) for k, v in links_paare)
        for i in info:
            if (i["a"]["kv"] is None and id(i) not in gepaart and i["x0"] >= spalte
                    and oben <= i["band"][0] <= unten_g + 14):
                ueber = [j for j in info if j["a"]["kv"] is not None and abs(j["x0"] - i["x0"]) <= 6
                         and 0 <= i["band"][0] - j["band"][1] <= 14]
                o = max(ueber, key=lambda j: j["band"][1])["a"]["id"] if ueber else None
                setze(i["a"], "value", [], "kv_value_without_key", o)
                zaehle("kv_wert_ohne_schluessel")

    # 2. Rahmen oder Spaltenteile nebeneinander im selben Block
    nach_block: dict[str, list[dict]] = {}
    for a in atome:
        if a["text"]:
            nach_block.setdefault(a["block"], []).append(a)
    for _, al in nach_block.items():
        for k, v in zip(al, al[1:]):
            if k["kv"] is not None or v["kv"] is not None:
                continue
            if not (k["text"].rstrip().endswith(":") or RX_FELDNAME.match(k["text"].strip())):
                continue
            if v["text"].rstrip().endswith(":"):
                continue
            rahmen_nebeneinander = (k["rahmen_nr"] != v["rahmen_nr"] and k["seite"] == v["seite"]
                                    and k["rahmen"] and v["rahmen"] and v["rahmen"][0] >= k["rahmen"][2] - 2
                                    and ueberlappt(_band(k, pos), _band(v, pos)))
            spalten_nebeneinander = (k["zeile"] == v["zeile"] and k["teilung"] in ("column", "frame_column")
                                     and v["teilung"] == k["teilung"])
            if rahmen_nebeneinander or spalten_nebeneinander:
                setze(k, "key", [v["id"]], "kv_key", v["id"])
                setze(v, "value", [k["id"]], "kv_value", k["id"])
                zaehle("kv_paare")

    # 3. «Schlüssel: Wert» in einer Zeile
    zeilen_je_block: dict[str, int] = {}
    for a in atome:
        zeilen_je_block[a["block"]] = max(zeilen_je_block.get(a["block"], 0), a["zeile"])
    for a in atome:
        if not a["text"] or a["kv"] is not None:
            continue
        bereich = a["eltern"] in KV_ELTERN or bool(a["kopf_fuss"])
        ort = bereich or (a["seite"] == 1 and zeilen_je_block[a["block"]] <= 3
                          and a["label"] in {"text", "section_header"})
        if a["label"] in TABELLEN:
            erste = a["text"].split("\t")[0].strip()
            if erste.endswith(":") and "\t" in a["text"]:
                setze(a, "key_value_inline", [], "kv_inline")
                zaehle("kv_in_zeile")
            continue
        if not ort or hat(a, "answer_reference", "question_number"):
            continue
        treffer = 0
        for seg in re.split(r"\s+\|\s+", a["text"]):
            m = RX_KV_ZEILE.match(seg.strip())
            if not m or m.group("v").rstrip().endswith(":") or len(re.sub(r"\W", "", m.group("k"))) < 2:
                continue
            # ausserhalb von Bereichen nur kurze Feldnamen und Werte (Titel mit Doppelpunkt sind häufig)
            if (len(m.group("k").split()) <= 5 if bereich
                    else len(m.group("k").split()) <= 3 and len(m.group("v")) <= 60):
                treffer += 1
        if treffer:
            setze(a, "key_value_inline", [], "kv_inline")
            zaehle("kv_in_zeile")


# ---------------------------------------------------------------- Prüfung

def pruefen(dok: dict, atome: list[dict]) -> dict:
    """Vollständige, überschneidungsfreie Zerlegung von text_gesamt."""
    g = dok.get("text_gesamt") or ""
    n = len(g)
    abdeckung = [0] * n
    wortlaut_falsch = []
    for a in atome:
        x, y = a["zeichen"]
        if g[x:y] != a["text"]:
            wortlaut_falsch.append(a["id"])
        for i in range(x, y):
            abdeckung[i] += 1
    ueberschneidung = sum(1 for c in abdeckung if c > 1)
    frei = [i for i, c in enumerate(abdeckung) if c == 0]
    nichtleer_frei = sum(1 for i in frei if not g[i].isspace())
    # Trenner nach Art: zwischen Blöcken, Zeilenumbruch im Block, sonstiger Leerraum
    in_block = [False] * n
    for b in dok["bloecke"]:
        x, y = b.get("zeichen") or (0, 0)
        for i in range(x, y):
            in_block[i] = True
    zwischen = sum(1 for i in frei if not in_block[i])
    umbruch = sum(1 for i in frei if in_block[i] and g[i] == "\n")
    sonst = len(frei) - zwischen - umbruch
    # Atom in seinem Block und in einem Rahmen
    bl = {b["id"]: b for b in dok["bloecke"]}
    ausserhalb_block, ueber_rahmen = [], []
    for a in atome:
        b = bl[a["block"]]
        bx, by = b["zeichen"]
        if not (bx <= a["zeichen"][0] <= a["zeichen"][1] <= by):
            ausserhalb_block.append(a["id"])
        if a["text"] and b.get("prov"):
            r = rahmen_des_blocks(b)[a["rahmen_nr"]]
            z = r.get("zeichen")
            if z and not (z[0] <= a["zeichen"][0] and a["zeichen"][1] <= z[1]):
                ueber_rahmen.append(a["id"])
    ids = [a["id"] for a in atome]
    starts = [a["zeichen"][0] for a in atome if a["text"]]
    ohne_atom = sorted({b["id"] for b in dok["bloecke"]} - {a["block"] for a in atome})
    return {
        "zeichen_gesamt": n,
        "zeichen_in_atomen": sum(1 for c in abdeckung if c > 0),
        "zeichen_trenner": len(frei),
        "trenner_zwischen_bloecken": zwischen,
        "trenner_zeilenumbruch": umbruch,
        "trenner_sonst_leerraum": sonst,
        "nichtleer_ausserhalb": nichtleer_frei,
        "ueberschneidungen": ueberschneidung,
        "wortlaut_abweichend": wortlaut_falsch,
        "ausserhalb_block": ausserhalb_block,
        "ueber_rahmengrenze": ueber_rahmen,
        "bloecke_ohne_atom": ohne_atom,
        "ids_eindeutig": len(ids) == len(set(ids)),
        "reihenfolge_steigend": starts == sorted(starts),
        "vollstaendig": (nichtleer_frei == 0 and ueberschneidung == 0 and not wortlaut_falsch
                         and not ausserhalb_block and not ueber_rahmen and not ohne_atom
                         and len(ids) == len(set(ids)) and starts == sorted(starts)),
    }


# ---------------------------------------------------------------- Ausgabe

def anzeige(a: dict) -> str:
    if not a["text"]:
        return "(ohne Text)"
    return a["text"].replace("\t", " ¦ ")


def prompt_zeilen(atome: list[dict]) -> list[str]:
    return [f"{a['id']} | {a['seite']} | {', '.join(a['hinweise'])} | {anzeige(a)}" for a in atome]


def prompt_text(atome: list[dict], mit_legende: bool = True, fassung: str = VERSION) -> str:
    kopf = []
    if mit_legende:
        kopf = [f"# {k}: {v}" for k, v in legende(fassung).items()]
    return "\n".join(kopf + ["ID | Seite | Hinweise | Text"] + prompt_zeilen(atome))


def quantil(werte: list[int], q: float) -> int:
    if not werte:
        return 0
    s = sorted(werte)
    return s[min(len(s) - 1, int(q * len(s)))]


def gegenprobe(dok: dict, atome: list[dict]) -> dict:
    """Zerlegung ohne Zeilen (jeder Block Fliesstext) und Isolierung der Antwortmarker.

    Ein Antwortmarker gilt als isoliert, wenn er an einem Atomanfang steht. Grundlage sind die
    Marker «Bezug Frage» und «Frage n» am Anfang einer Zeile in der Zeilen-Zerlegung."""
    gp = zerlegen(dok, ohne_zeilen=True)
    laengen = [len(a["text"]) for a in gp if a["text"]]
    marker = [a["zeichen"][0] for a in atome if hat(a, "answer_reference", "question_number")]
    gp_starts = {a["zeichen"][0] for a in gp}
    return {
        "gp_atome": len([a for a in gp if a["text"]]),
        "gp_laenge_median": int(statistics.median(laengen)) if laengen else 0,
        "gp_laenge_p90": quantil(laengen, 0.9),
        "gp_laenge_max": max(laengen) if laengen else 0,
        "gp_atome_lang": sum(1 for x in laengen if x > LANG_AB),
        "gp_marker_gesamt": len(marker),
        "gp_marker_isoliert": sum(1 for s in marker if s in gp_starts),
    }


# Kennzahl-Spalte → Merkmal-Schlüssel (Anzahl Atome mit diesem Merkmal)
ZAEHL_MERKMALE = {
    "seitenwechsel_im_block": ("page_break_in_block",), "drittel_regel_verletzt": ("thirds_rule_violated",),
    "seitenwechsel": ("page_break", "page_break_back", "page_break_in_block"),
    "seitenwechsel_zurueck": ("page_break_back",),
    "ueber_vorgaenger": ("above_previous",), "ausserhalb_rahmen": ("outside_frame",),
    "bezug_frage": ("answer_reference",), "frage_nr": ("question_number",), "aufzaehlung": ("enumeration",),
    "stichwort": ("keyword",), "typbezeichnung": ("affair_type",), "einleitung_fragen": ("intro_questions",),
    "auftragsformel": ("demand_formula",), "einleitung_folgt": ("intro_follows",),
    "unterschriftsformel": ("signature_formula",), "ort_datum": ("place_date",), "datumszeile": ("date_line",),
    "verteiler": ("distribution",), "seitenzahl": ("page_number",), "sperrschrift": ("letterspacing",),
    "marker_im_atom": ("marker_inside",), "gedreht": ("rotated",),
}


ZAEHL_MERKMALE_V3 = {"folgenummer": ("number_sequence",), "klammerzeile_datum": ("bracket_date",),
                     "zitatende": ("quote_end",), "zellenzahl_wechselt": ("table_cells_change",)}


def zaehlen(atome: list[dict], fassung: str = VERSION) -> dict:
    z = {k: sum(1 for a in atome if hat(a, *schl)) for k, schl in ZAEHL_MERKMALE.items()}
    if fassung == VERSION_V3:
        z |= {k: sum(1 for a in atome if hat(a, *schl)) for k, schl in ZAEHL_MERKMALE_V3.items()}
        z["zeilen_satz_ohne_leerzeichen"] = len({(a["block"], a["zeile"]) for a in atome
                                                 if a["teilung"] == "sentence_no_space"})
    for spalte, arten in (("zeilen_satzgeteilt", ("sentence",)), ("rahmenteilungen", ("frame", "frame_column")),
                          ("spaltenteilungen", ("column", "frame_column"))):
        z[spalte] = len({(a["block"], a["zeile"]) for a in atome if a["teilung"] in arten})
    mit = [a for a in atome if a.get("satzanfaenge") is not None]
    z["satzanfaenge_im_atom"] = sum(len(a["satzanfaenge"]) for a in mit)
    z["atome_mit_satzanfang"] = sum(1 for a in mit if a["satzanfaenge"])
    # Satzgrenze genau an einer Atomgrenze: Atom endet mit Satzzeichen, nächstes Atom im selben Block
    z["satzgrenzen_am_atomende"] = sum(
        1 for a, n in zip(atome, atome[1:]) if a.get("satzanfaenge") is not None and n["block"] == a["block"]
        and re.search(r"[.!?…][\"»«”’)\]]*$", a["text"]) and not (a["text"].endswith(".")
                                                                  and abkuerzung(a["text"], len(a["text"]) - 1)))
    z["zeilenrahmen_textschicht"] = sum(1 for a in atome if a.get("zeilenrahmen_quelle") == "text_layer")
    z["zeilenrahmen_geschaetzt"] = sum(1 for a in atome if a.get("zeilenrahmen_quelle") == "estimated")
    z["text_textschicht_abweichend"] = sum(1 for a in atome if a.get("text_textschicht"))
    return z


SPALTEN = [
    "doc_id", "zelle", "status", "seiten", "bloecke", "bloecke_ohne_text", "atome", "atome_mit_text",
    "atome_je_block_median", "atome_je_block_max", "zeichen_gesamt", "zeichen_in_atomen", "zeichen_trenner",
    "trenner_zwischen_bloecken", "trenner_zeilenumbruch", "trenner_sonst_leerraum", "nichtleer_ausserhalb",
    "ueberschneidungen", "wortlaut_abweichend", "ausserhalb_block", "ueber_rahmengrenze", "vollstaendig",
    "laenge_median", "laenge_p90", "laenge_max", "laengstes_atom", "atome_lang", "atome_lang_tabelle",
    "atome_kurz", "zeilen_satzgeteilt", "rahmenteilungen", "spaltenteilungen", "seitenwechsel",
    "seitenwechsel_zurueck", "seitenwechsel_im_block", "drittel_regel_verletzt", "ueber_vorgaenger",
    "ausserhalb_rahmen", "bezug_frage", "frage_nr", "aufzaehlung", "stichwort", "typbezeichnung",
    "einleitung_fragen", "auftragsformel", "einleitung_folgt", "unterschriftsformel", "ort_datum",
    "datumszeile", "verteiler", "seitenzahl", "sperrschrift", "marker_im_atom", "gedreht", "kv_paare",
    "kv_schluessel_ohne_wert", "kv_wert_ohne_schluessel", "kv_in_zeile", "satzanfaenge_im_atom",
    "atome_mit_satzanfang", "satzgrenzen_am_atomende", "ts_zeilen", "ts_gefunden", "ts_ausserhalb_rahmen",
    "ts_typografie", "ts_nicht_gefunden", "zeilenrahmen_textschicht", "zeilenrahmen_geschaetzt",
    "text_textschicht_abweichend", "prompt_zeichen", "prompt_tokens_schaetzung",
    "blockformat_tokens_schaetzung", "faktor_atom_zu_block", "gp_atome", "gp_laenge_median", "gp_laenge_p90",
    "gp_laenge_max", "gp_atome_lang", "gp_marker_gesamt", "gp_marker_isoliert",
]
SPALTEN_V3 = SPALTEN + ["zeilen_satz_ohne_leerzeichen", *ZAEHL_MERKMALE_V3]


def spalten_fuer(fassung: str = VERSION) -> list[str]:
    return SPALTEN_V3 if fassung == VERSION_V3 else SPALTEN


def zellen() -> dict[str, str]:
    if not AUGENSCHEIN.exists():
        return {}
    with AUGENSCHEIN.open(encoding="utf-8") as f:
        return {r["doc_id"]: r["zelle"] for r in csv.DictReader(f)}


def verarbeiten(dok: dict, woerter: dict[int, list[tuple]], fassung: str = VERSION) -> tuple[list[dict], dict]:
    """Zerlegen, Textschicht abgleichen, an Spaltenlücken nachteilen, Merkmale setzen."""
    atome = zerlegen(dok, fassung=fassung)
    treffer, ts = zeilen_abgleich(dok, atome, woerter)
    spalten = spaltenschnitte(treffer)
    if spalten:
        atome = zerlegen(dok, spalten=spalten, fassung=fassung)   # gleiche Zeilen, Treffer bleiben gültig
    zeilenrahmen_setzen(atome, treffer)
    kv = hinweise_setzen(dok, atome, fassung)
    return atome, kv | ts | zaehlen(atome, fassung)


_POPPLER: str | None = None


def poppler_version() -> str:
    global _POPPLER
    if _POPPLER is None:
        try:
            r = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True, timeout=10)
            _POPPLER = (r.stderr or r.stdout).splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            _POPPLER = ""
    return _POPPLER


def dokument(pfad: Path, zelle: str | None, fassung: str = VERSION) -> tuple[dict, dict]:
    dok = json.loads(pfad.read_text(encoding="utf-8"))
    pdf = PDF / f"{pfad.stem}.pdf"
    pdf_sha = sha256_datei(pdf) if pdf.exists() else None
    kopf = {
        "doc_id": str(dok.get("doc_id")), "zelle": zelle, "version": fassung,
        "skript": "src/m03_atome.py", "erzeugt_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quelle": rel(pfad), "quelle_sha256": sha256_datei(pfad),
        "docling_lauf": dok.get("lauf"), "werkzeug": dok.get("werkzeug"),
        "textschicht": {"pdf": rel(pdf) if pdf.exists() else None, "pdf_sha256": pdf_sha,
                        "pdf_gleich_docling": (pdf_sha == dok.get("sha256")) if pdf_sha else None,
                        "werkzeug": TEXTSCHICHT_WERKZEUG, "version": poppler_version()},
        "parameter": {"satz_ab": SATZ_AB, "lang_ab": LANG_AB, "kurz_bis": KURZ_BIS,
                      "spaltenluecke_pt": SPALTENLUECKE_PT, "rahmen_toleranz_pt": RAHMEN_TOLERANZ_PT}
                     | ({"satz_ohne_leerzeichen": True} if fassung == VERSION_V3 else {}),
        "status": dok.get("status"),
    }
    werte = {"merkmale": merkmale_tabelle(fassung), "stichworte": STICHWORT_DE,
             "teilung": TEILUNG_V3 if fassung == VERSION_V3 else TEILUNG, "kv_rolle": KV_ROLLEN,
             "zeilenrahmen_quelle": ZEILENRAHMEN_QUELLE, "merkmal_ech": MERKMAL_ECH}
    zeile = {"doc_id": kopf["doc_id"], "zelle": zelle, "status": dok.get("status"),
             "seiten": len(dok.get("seiten") or [])}
    if dok.get("status") != "success":
        return kopf | {"legende": legende(fassung), "werte": werte, "pruefung": None, "atome": [], "prompt": []}, zeile
    # Textschicht nur, wenn die PDF dieselbe ist, die Docling gelesen hat
    woerter = pdf_woerter(pdf) if pdf_sha and pdf_sha == dok.get("sha256") else {}
    atome, zaehler = verarbeiten(dok, woerter, fassung)
    pr = pruefen(dok, atome)
    mit_text = [a for a in atome if a["text"]]
    laengen = [len(a["text"]) for a in mit_text]
    je_block: dict[str, int] = {}
    for a in mit_text:
        je_block[a["block"]] = je_block.get(a["block"], 0) + 1
    laengstes = max(mit_text, key=lambda a: len(a["text"])) if mit_text else None
    ptxt = prompt_text(atome, mit_legende=False)
    blocktxt = dokument_rendern(bloecke_vorbereiten(dok))
    zeile |= {
        "bloecke": len(dok["bloecke"]),
        "bloecke_ohne_text": sum(1 for b in dok["bloecke"] if not (b.get("text") or "").strip()),
        "atome": len(atome), "atome_mit_text": len(mit_text),
        "atome_je_block_median": median_zahl(je_block.values()) if je_block else 0,
        "atome_je_block_max": max(je_block.values()) if je_block else 0,
        **{k: pr[k] for k in ("zeichen_gesamt", "zeichen_in_atomen", "zeichen_trenner",
                              "trenner_zwischen_bloecken", "trenner_zeilenumbruch", "trenner_sonst_leerraum",
                              "nichtleer_ausserhalb", "ueberschneidungen")},
        "wortlaut_abweichend": len(pr["wortlaut_abweichend"]),
        "ausserhalb_block": len(pr["ausserhalb_block"]),
        "ueber_rahmengrenze": len(pr["ueber_rahmengrenze"]),
        "vollstaendig": "ja" if pr["vollstaendig"] else "nein",
        "laenge_median": int(statistics.median(laengen)) if laengen else 0,
        "laenge_p90": quantil(laengen, 0.9), "laenge_max": max(laengen) if laengen else 0,
        "laengstes_atom": laengstes["id"] if laengstes else "",
        "atome_lang": sum(1 for x in laengen if x > LANG_AB),
        "atome_lang_tabelle": sum(1 for a in mit_text if len(a["text"]) > LANG_AB and a["label"] in TABELLEN),
        "atome_kurz": sum(1 for x in laengen if x <= KURZ_BIS),
        "prompt_zeichen": len(ptxt),
        "prompt_tokens_schaetzung": round(len(ptxt) / ZEICHEN_JE_TOKEN),
        "blockformat_tokens_schaetzung": round(len(blocktxt) / ZEICHEN_JE_TOKEN),
        "faktor_atom_zu_block": round(len(ptxt) / len(blocktxt), 2) if blocktxt else "",
    }
    for k in spalten_fuer(fassung):
        if k not in zeile and k in zaehler:
            zeile[k] = zaehler[k]
    for k in ("kv_paare", "kv_schluessel_ohne_wert", "kv_wert_ohne_schluessel", "kv_in_zeile"):
        zeile.setdefault(k, 0)
    zeile |= gegenprobe(dok, atome)
    felder = ("id", "block", "zeile", "teil", "teilung", "seite", "label", "schicht", "kopf_fuss", "eltern",
              "zeichen", "rahmen", "zeilenrahmen", "zeilenrahmen_quelle", "zellen", "text", "text_textschicht",
              "satzanfaenge", "merkmale", "hinweise", "kv")
    aus = kopf | {
        "legende": legende(fassung),
        "werte": werte,
        "pruefung": pr,
        "kennzahlen": {k: v for k, v in zeile.items() if k not in ("doc_id", "zelle", "status")},
        "atome": [{k: a.get(k) for k in felder} for a in atome],
        "prompt": prompt_zeilen(atome),
    }
    return aus, zeile


# ---------------------------------------------------------------- Selbsttest

def selbsttest() -> None:
    """Kunstdokument mit allen Sonderfällen; prüft Zerlegung, IDs, Merkmale und Textschicht-Abgleich."""
    bloecke_roh = [
        dict(id="B1", label="page_header", schicht="furniture", kopf_fuss="kopf", text="Ort, 17. Juni 2019",
             seite=1, bbox=[70, 70, 200, 80]),
        dict(id="B2", label="text", eltern={"ref": "#/groups/0", "label": "key_value_area"}, text="Vorstoss-Nr.:",
             seite=1, bbox=[68, 185, 119, 193]),
        dict(id="B3", label="text", eltern={"ref": "#/groups/0", "label": "key_value_area"}, text="Vorstossart:",
             seite=1, bbox=[68, 196, 114, 203]),
        dict(id="B4", label="text", eltern={"ref": "#/groups/0", "label": "key_value_area"},
             text="000-2023\nMotion", seite=1, bbox=[210, 185, 246, 203]),
        dict(id="B5", label="text", eltern={"ref": "#/groups/0", "label": "key_value_area"},
             text="Dringlichkeit gewährt:", seite=1, bbox=[68, 230, 151, 238]),
        dict(id="B6", label="text", text="Zu Frage 1: Erste Antwort.\nZu den Fragen 2 und 3:Weiter.\n 1. Juni 2020",
             seite=1, bbox=[70, 300, 500, 700],
             prov=[{"seite": 1, "bbox": [70, 300, 500, 700]}, {"seite": 2, "bbox": [70, 400, 500, 450]}]),
        dict(id="B7", label="picture", text="", seite=2, bbox=[70, 500, 100, 530]),
        dict(id="B8", label="text", text_quelle="docling",
             text=("Der Regierungsrat hat am 17. Juni 2019 entschieden, gemäss Art. 5 Abs. 2 z.B. die "
                   "Frist zu verlängern. Zu Frage 4: Dies betrifft u.a. Herrn R. Muster und die Fr. 100 "
                   "Gebühren. Ist das richtig? Ja! Die Antwort folgt am 3. Mai 2020. Weitere Ausführungen "
                   "folgen im Bericht des Regierungsrates zuhanden des Parlaments."),
             seite=3, bbox=[70, 100, 500, 200]),
        dict(id="B9", label="table", text="Kopf:\tWert\nA\tB", seite=3, bbox=[70, 300, 500, 340]),
        dict(id="B10", label="text", text="betreffend\nThema X", seite=3, bbox=[70, 400, 120, 410],
             prov=[{"seite": 3, "bbox": [70, 400, 120, 410]}, {"seite": 3, "bbox": [150, 400, 400, 410]}]),
        dict(id="B11", label="section_header", text="M i t t e i l u n g  a n", seite=3, bbox=[70, 600, 300, 610]),
        dict(id="B12", label="text", text="Mit freundlichen Grüssen", seite=3, bbox=[70, 650, 300, 660]),
        dict(id="B13", label="text", text="Der Präsident: Die Schreiberin:\nA. Muster B. Beispiel",
             seite=3, bbox=[70, 700, 400, 722]),
        dict(id="B14", label="list_item", text="8 . Kann die Regierung sagen, ob das stimmt?",
             seite=3, bbox=[70, 730, 500, 740]),
        dict(id="B15", label="page_footer", schicht="furniture", kopf_fuss="fuss", text="- 3 -",
             seite=3, bbox=[280, 800, 300, 808]),
        dict(id="B16", label="section_header", text="Interpellation Nr. 70 betreffend Strassen",
             seite=4, bbox=[70, 100, 400, 110]),
        dict(id="B17", label="text", text="Der Regierungsrat wird beauftragt, folgende Fragen zu beantworten:",
             seite=4, bbox=[70, 120, 500, 130]),
        dict(id="B18", label="text", text="Die Regierung antwortet wie folgt:\nl'Etat - oui",
             seite=4, bbox=[70, 140, 500, 162]),
        dict(id="B19", label="text", text="Zweiter Absatz unten", seite=4, bbox=[70, 300, 500, 310]),
        dict(id="B20", label="text", text="Erster Absatz oben", seite=4, bbox=[70, 200, 500, 210]),
    ]
    teile, pos = [], 0
    for b in bloecke_roh:
        b.setdefault("schicht", "body")
        b.setdefault("kopf_fuss", None)
        b.setdefault("eltern", None)
        b.setdefault("text_quelle", "zeilen")
        if b["text"]:
            if teile:
                teile.append("\n\n")
                pos += 2
            b["zeichen"] = [pos, pos + len(b["text"])]
            teile.append(b["text"])
            pos += len(b["text"])
        else:
            b["zeichen"] = [pos, pos]
    for b in bloecke_roh:
        if "prov" in b:
            z0 = b["zeichen"][0]
            if b["id"] == "B6":
                n1 = len("Zu Frage 1: Erste Antwort.\nZu den Fragen 2 und 3:Weiter.")
                b["prov"][0]["zeichen"] = [z0, z0 + n1]
                b["prov"][1]["zeichen"] = [z0 + n1 + 1, b["zeichen"][1]]
            else:
                b["prov"][0]["zeichen"] = [z0, z0 + len("betreffend")]
                b["prov"][1]["zeichen"] = [z0 + len("betreffend") + 1, b["zeichen"][1]]
    dok = {"doc_id": "test", "status": "success", "bloecke": bloecke_roh, "text_gesamt": "".join(teile),
           "seiten": [{"seite": s, "hoehe": 842.0, "textquelle": "pdf" if s >= 3 else "ocr"} for s in (1, 2, 3, 4)]}

    def w(x0, y0, x1, text, h=10):
        return (float(x0), float(y0), float(x1), float(y0 + h), text)

    woerter = {
        3: [w(70, 400, 115, "betreffend"), w(150, 400, 180, "Thema"), w(182, 400, 188, "X"),
            w(70, 650, 90, "Mit"), w(92, 650, 150, "freundlichen"), w(152, 650, 190, "Grüssen"),
            w(70, 700, 85, "Der"), w(87, 700, 130, "Präsident:"), w(250, 700, 262, "Die"),
            w(264, 700, 310, "Schreiberin:"),
            w(70, 712, 80, "A."), w(82, 712, 120, "Muster"), w(250, 712, 260, "B."), w(262, 712, 300, "Beispiel"),
            w(70, 730, 75, "8"), w(75, 730, 77, "."), w(100, 730, 120, "Kann"), w(122, 730, 135, "die"),
            w(137, 730, 180, "Regierung"), w(182, 730, 210, "sagen,"), w(212, 730, 222, "ob"),
            w(224, 730, 240, "das"), w(242, 730, 280, "stimmt?"), w(282, 800, 298, "–3–")],
        4: [w(70, 140, 85, "Die"), w(87, 140, 130, "Regierung"), w(132, 140, 180, "antwortet"),
            w(182, 140, 200, "wie"), w(202, 140, 230, "folgt:"),
            w(70, 152, 100, "l’Etat"), w(102, 152, 108, "–"), w(110, 152, 125, "oui"),
            w(70, 300, 110, "Zweiter"), w(112, 300, 150, "Absatz"), w(152, 300, 180, "unten"),
            w(70, 200, 100, "Erster"), w(102, 200, 140, "Absatz"), w(142, 200, 170, "oben")],
    }
    atome, zaehler = verarbeiten(dok, woerter)
    pr = pruefen(dok, atome)
    h = {a["id"]: a["hinweise"] for a in atome}
    am = {a["id"]: a for a in atome}
    fehler = []

    def soll(bed: bool, text: str) -> None:
        if not bed:
            fehler.append(text)

    soll(pr["vollstaendig"], f"Zerlegung unvollständig: {pr}")
    soll(pr["trenner_sonst_leerraum"] > 0, "Satzgrenzen-Leerraum fehlt in den Trennern")
    soll("Ort und Datum" in h["B1.1"], f"B1.1 {h['B1.1']}")
    soll("Schlüssel→B4.1" in h["B2.1"] and "Schlüssel→B4.2" in h["B3.1"], f"KV {h['B2.1']} {h['B3.1']}")
    soll("Wert←B2.1" in h["B4.1"] and "Wert←B3.1" in h["B4.2"], f"KV {h['B4.1']} {h['B4.2']}")
    soll(am["B4.1"]["kv"]["rolle"] == "value" and am["B2.1"]["kv"]["rolle"] == "key", "KV-Rollen englisch")
    soll("Typbezeichnung" in h["B4.2"], f"B4.2 {h['B4.2']}")
    soll("Schlüssel ohne Wert" in h["B5.1"], f"B5.1 {h['B5.1']}")
    soll("Bezug Frage 1" in h["B6.1"] and "Bezug Frage 2, 3" in h["B6.2"], f"B6 {h['B6.1']} {h['B6.2']}")
    soll("Seitenwechsel im Block" in h["B6.3"] and "Drittel-Regel verletzt" in h["B6.3"], f"B6.3 {h['B6.3']}")
    soll("Aufzählung 1." not in h["B6.3"] and "Datum" in h["B6.3"], f"B6.3 Datum {h['B6.3']}")
    soll("ohne Text" in h["B7.1"], f"B7.1 {h['B7.1']}")
    b8 = [a for a in atome if a["block"] == "B8"]
    soll(len(b8) == 6 and all(a["teilung"] == "sentence" for a in b8),
         f"Satzteilung B8: {[a['text'] for a in b8]}")
    soll(any(a["text"].startswith("Zu Frage 4:") and "Bezug Frage 4" in a["hinweise"] for a in b8),
         "Marker in B8 nicht isoliert")
    soll("Seitenwechsel" in h["B8.1.1"], f"B8.1.1 {h['B8.1.1']}")
    soll(am["B8.1.1"]["zeilenrahmen_quelle"] == "estimated", "B8 Zeilenrahmen geschätzt")
    soll("Tabellenzeile 1" in h["B9.1"] and "Schlüssel: Wert in Zeile" in h["B9.1"], f"B9.1 {h['B9.1']}")
    soll("Schlüssel→B10.2" in h["B10.1"] and "Wert←B10.1" in h["B10.2"], f"B10 {h['B10.1']} {h['B10.2']}")
    soll(am["B10.2"]["zeilenrahmen"] == [150.0, 400.0, 188.0, 410.0], f"B10.2 {am['B10.2']['zeilenrahmen']}")
    soll("Sperrschrift" in h["B11.1"] and "Verteiler" in h["B11.1"], f"B11.1 {h['B11.1']}")
    soll("Unterschriftsformel" in h["B12.1"] and am["B12.1"]["zeilenrahmen_quelle"] == "text_layer",
         f"B12.1 {h['B12.1']}")
    # Spaltenlücke: zwei Unterschriften nebeneinander
    soll(am.get("B13.1.1", {}).get("text") == "Der Präsident:" and am.get("B13.1.2", {}).get("text")
         == "Die Schreiberin:", f"Spaltenteilung B13.1: {[a['id'] for a in atome if a['block'] == 'B13']}")
    soll("Spaltenteil 1/2" in h.get("B13.1.1", []) and "Unterschriftsformel" in h.get("B13.1.1", []),
         f"B13.1.1 {h.get('B13.1.1')}")
    soll("Schlüssel→B13.1.2" not in h.get("B13.1.1", []), "zwei Feldnamen sind kein Paar")
    soll(am.get("B13.2.2", {}).get("text") == "B. Beispiel", "Spaltenteilung B13.2")
    soll(am.get("B13.1.2", {}).get("zeilenrahmen") == [250.0, 700.0, 310.0, 710.0], "Rahmen Spaltenteil")
    # Hängeeinzug nach Nummer teilt nicht
    soll("B14.1" in am and am["B14.1"]["teilung"] is None, "Hängeeinzug B14 geteilt")
    soll("Seitenzahl" in h["B15.1"] and not any(x.startswith("Aufzählung") for x in h["B15.1"]),
         f"B15.1 {h['B15.1']}")
    soll(am["B15.1"]["text_textschicht"] == "–3–", f"Typografie B15.1 {am['B15.1']['text_textschicht']}")
    soll("Typbezeichnung" in h["B16.1"], f"B16.1 {h['B16.1']}")
    soll("Auftragsformel" in h["B17.1"] and "Einleitung Fragen" in h["B17.1"], f"B17.1 {h['B17.1']}")
    soll("Einleitung folgt" in h["B18.1"], f"B18.1 {h['B18.1']}")
    soll(am["B18.2"]["text_textschicht"] == "l’Etat – oui", f"B18.2 {am['B18.2']['text_textschicht']}")
    soll("über Vorgänger" in h["B20.1"] and "über Vorgänger" not in h["B19.1"], f"B20.1 {h['B20.1']}")
    soll(am["B8.1.1"]["satzanfaenge"] == [], f"Satzanfänge B8.1.1 {am['B8.1.1']['satzanfaenge']}")
    soll(zaehler["spaltenteilungen"] == 2 and zaehler["ts_gefunden"] >= 9, f"Zähler {zaehler}")
    soll(zaehler.get("marker_im_atom", 0) == 0, f"Marker im Atom: {zaehler}")
    gp = gegenprobe(dok, atome)
    soll(gp["gp_marker_gesamt"] == 3, f"Gegenprobe {gp}")
    t = "Gemäss Art. 5 Abs. 2 gilt dies. Herr M. Muster am 1. Mai. Neu ab 2019. Ende"
    st = [t[x:y] for x, y in satzteile(t, 0, len(t))]
    soll(st == ["Gemäss Art. 5 Abs. 2 gilt dies.", "Herr M. Muster am 1. Mai.", "Neu ab 2019.", "Ende"],
         f"Satzteile {st}")
    prompt = prompt_text(atome)
    soll("B8.1.2 | 3 | ohne Zeilen, Satzteil 2/6, Bezug Frage 4 |" in prompt, "Prompt-Zeile B8.1.2")
    soll(all(k in MERKMALE for a in atome for k, _ in a["merkmale"]), "unbekannter Merkmal-Schlüssel")
    soll(all(k.split(":")[0] in MERKMALE and (":" not in k or k.split(":")[1] in STICHWORT_DE)
             for k in MERKMAL_ECH), "MERKMAL_ECH mit unbekanntem Schlüssel")
    # atome-v3 auf demselben Kunstdokument: keine zusätzliche Teilung, keine neuen Merkmale
    atome_v3, _ = verarbeiten(json.loads(json.dumps(dok)), woerter, VERSION_V3)
    soll([(a["id"], a["zeichen"]) for a in atome_v3] == [(a["id"], a["zeichen"]) for a in atome],
         "atome-v3 ändert das Kunstdokument von atome-v2")
    fehler += selbsttest_v3()
    if fehler:
        print("Selbsttest FEHLER:")
        for f in fehler:
            print(" -", f)
        sys.exit(1)
    print(f"Selbsttest ok: {len(atome)} Atome, {len(fehler)} Fehler, Prüfung {pr['vollstaendig']}")
    print("\n".join(prompt_zeilen(atome)))


def selbsttest_v3() -> list[str]:
    """atome-v3: Satzgrenzen ohne Leerzeichen (mit Ausnahmen) und die vier Kandidatenmerkmale."""
    texte = [
        ("B1", "text", "Titel der Anfrage zur ABC.Am 3. Mai reichte die Fraktion folgende Anfrage ein:"),
        ("B2", "text", "Siehe Muster-St.Gallen, www.example.ch/Geschaeft?AffairId=5, z.B.Bern und S.Muster"),
        ("B3", "footnote", "21 Charta der Grundrechte, ABl. C 202\nvom 7. Juni 2016\n22 SR 0.101"),
        ("B4", "text", "(StB 123 vom 1. Januar 2017)"),
        ("B5", "list_item", "9. Wie oft tauschen sich die Stellen aus?\nMax Muster»"),
        ("B6", "table", "mm\t1\tOrt, 22. Februar 2017\tnumero 1\nRepubblica e Cantone\nTicino"),
        ("B7", "text", "Das ist ein Satz.Und noch einer.Dritter Satz"),
        ("B8", "text", "1 Gegenstand\n2 Rechtsgrundlagen"),
    ]
    bloecke, teile, pos = [], [], 0
    for bid, label, text in texte:
        if teile:
            teile.append("\n\n")
            pos += 2
        bloecke.append({"id": bid, "label": label, "text": text, "seite": 1, "bbox": [70, 100, 500, 110],
                        "schicht": "body", "kopf_fuss": None, "eltern": None, "text_quelle": "zeilen",
                        "zeichen": [pos, pos + len(text)]})
        teile.append(text)
        pos += len(text)
    dok = {"doc_id": "test3", "status": "success", "bloecke": bloecke, "text_gesamt": "".join(teile),
           "seiten": [{"seite": 1, "hoehe": 842.0, "textquelle": "ocr"}]}
    f: list[str] = []
    a2, _ = verarbeiten(json.loads(json.dumps(dok)), {}, VERSION)
    a3, z3 = verarbeiten(json.loads(json.dumps(dok)), {}, VERSION_V3)
    am = {a["id"]: a for a in a3}
    if [a["text"] for a in a3 if a["block"] == "B1"] != ["Titel der Anfrage zur ABC.",
                                                           "Am 3. Mai reichte die Fraktion folgende Anfrage ein:"]:
        f.append(f"v3 Satzgrenze ohne Leerzeichen B1: {[a['text'] for a in a3 if a['block'] == 'B1']}")
    if am.get("B1.1.2", {}).get("teilung") != "sentence_no_space" or "Satzteil 2/2" not in am["B1.1.2"]["hinweise"]:
        f.append(f"v3 Teilung/Hinweis B1.1.2: {am.get('B1.1.2')}")
    if [a["id"] for a in a3 if a["block"] == "B2"] != ["B2.1"]:
        f.append("v3 teilt nach Abkürzung, in Adresse oder nach Initiale")
    if [a["text"] for a in a3 if a["block"] == "B7"] != ["Das ist ein Satz.", "Und noch einer.", "Dritter Satz"]:
        f.append(f"v3 mehrere Satzgrenzen B7: {[a['text'] for a in a3 if a['block'] == 'B7']}")
    if "Folgenummer 22" not in am["B3.3"]["hinweise"] or any("Folgenummer" in h for h in am["B3.1"]["hinweise"]):
        f.append(f"v3 Folgenummer B3: {am['B3.1']['hinweise']} {am['B3.3']['hinweise']}")
    if "Folgenummer 2" not in am["B8.2"]["hinweise"]:
        f.append(f"v3 Folgenummer B8.2: {am['B8.2']['hinweise']}")
    if "Klammerzeile mit Datum" not in am["B4.1"]["hinweise"]:
        f.append(f"v3 Klammerzeile B4.1: {am['B4.1']['hinweise']}")
    if "Zitatende" not in am["B5.2"]["hinweise"] or "Zitatende" in am["B5.1"]["hinweise"]:
        f.append(f"v3 Zitatende B5: {am['B5.1']['hinweise']} {am['B5.2']['hinweise']}")
    if "Zellenzahl wechselt" not in am["B6.2"]["hinweise"] or "Zellenzahl wechselt" in am["B6.3"]["hinweise"]:
        f.append(f"v3 Zellenzahl B6: {am['B6.2']['hinweise']} {am['B6.3']['hinweise']}")
    if z3.get("zeilen_satz_ohne_leerzeichen") != 2 or z3.get("folgenummer") != 2 or z3.get("zellenzahl_wechselt") != 1:
        f.append(f"v3 Zähler {z3}")
    if pruefen(dok, a3)["vollstaendig"] is not True:
        f.append("v3 Zerlegung unvollständig")
    neu = set(MERKMALE_V3)
    if any(k in neu for a in a2 for k, _ in a["merkmale"]) or len(a2) != len(a3) - 3:
        f.append("atome-v2 mit Merkmalen oder Teilen aus atome-v3")
    if "Folgenummer" not in prompt_text(a3, fassung=VERSION_V3) or "Folgenummer" in prompt_text(a2):
        f.append("Legende atome-v3")
    return f


# ---------------------------------------------------------------- Hauptprogramm

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("doc_ids", nargs="*")
    ap.add_argument("--zeigen", metavar="DOC_ID", help="Prompt-Form eines Dokuments ausgeben (enthält Namen)")
    ap.add_argument("--selbsttest", action="store_true")
    ap.add_argument("--fassung", choices=FASSUNGEN, default=VERSION,
                    help=f"{VERSION} (Standard, Runde 1) oder {VERSION_V3} (Runde 2)")
    args = ap.parse_args()
    if args.selbsttest:
        selbsttest()
        return
    z = zellen()
    fassung = args.fassung
    aus_ordner, kennzahlen_pfad = (AUS_V3, KENNZAHLEN_V3) if fassung == VERSION_V3 else (AUS, KENNZAHLEN)
    if args.zeigen:
        aus, _ = dokument(DOCLING / f"{args.zeigen}.json", z.get(args.zeigen), fassung)
        print("\n".join([f"# {k}: {v}" for k, v in legende(fassung).items()] + ["ID | Seite | Hinweise | Text"]
                        + aus["prompt"]))
        return
    pfade = ([DOCLING / f"{d}.json" for d in args.doc_ids] if args.doc_ids
             else sorted(DOCLING.glob("*.json"), key=lambda p: z.get(p.stem, p.stem)))
    aus_ordner.mkdir(parents=True, exist_ok=True)
    zeilen_csv = []
    for p in pfade:
        aus, zeile = dokument(p, z.get(p.stem), fassung)
        (aus_ordner / f"{p.stem}.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1), encoding="utf-8")
        zeilen_csv.append(zeile)
        if zeile.get("status") != "success":
            print(f"{zeile['zelle'] or '-':4} {p.stem:>7} Status {zeile.get('status')}, keine Atome")
            continue
        print(f"{zeile['zelle'] or '-':4} {p.stem:>7} Blöcke {zeile['bloecke']:4} Atome {zeile['atome']:5} "
              f"vollständig {zeile['vollstaendig']:4} Länge Median/P90/Max {zeile['laenge_median']}/"
              f"{zeile['laenge_p90']}/{zeile['laenge_max']} lang {zeile['atome_lang']} kurz {zeile['atome_kurz']} "
              f"Spalten {zeile['spaltenteilungen']} SW {zeile['seitenwechsel']}/{zeile['seitenwechsel_im_block']}/"
              f"{zeile['drittel_regel_verletzt']} über Vorg. {zeile['ueber_vorgaenger']} "
              f"Marker B{zeile['bezug_frage']} F{zeile['frage_nr']} im Atom {zeile['marker_im_atom']} "
              f"KV {zeile['kv_paare']}/{zeile['kv_in_zeile']} Textschicht {zeile['ts_gefunden']}/{zeile['ts_zeilen']} "
              f"Tokens {zeile['prompt_tokens_schaetzung']} (×{zeile['faktor_atom_zu_block']})")
    if not args.doc_ids:
        with kennzahlen_pfad.open("w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=spalten_fuer(fassung))
            wr.writeheader()
            for zeile in zeilen_csv:
                wr.writerow({k: zeile.get(k, "") for k in spalten_fuer(fassung)})
        ok = [r for r in zeilen_csv if r.get("status") == "success"]
        summe = lambda k: sum(int(r.get(k) or 0) for r in ok)  # noqa: E731
        print(f"\nDokumente {len(zeilen_csv)}, davon mit Atomen {len(ok)}; vollständig "
              f"{sum(1 for r in ok if r['vollstaendig'] == 'ja')}")
        print(f"Blöcke {summe('bloecke')}, Atome {summe('atome')} (mit Text {summe('atome_mit_text')}); "
              f"Zeichen {summe('zeichen_gesamt')}, in Atomen {summe('zeichen_in_atomen')}, Trenner "
              f"{summe('zeichen_trenner')} (zwischen Blöcken {summe('trenner_zwischen_bloecken')}, Zeilenumbruch "
              f"{summe('trenner_zeilenumbruch')}, sonst {summe('trenner_sonst_leerraum')}); nicht leer ausserhalb "
              f"{summe('nichtleer_ausserhalb')}, Überschneidungen {summe('ueberschneidungen')}")
        print(f"Atome lang (> {LANG_AB}) {summe('atome_lang')} (davon Tabellenzeilen {summe('atome_lang_tabelle')}), "
              f"kurz (≤ {KURZ_BIS}) {summe('atome_kurz')}; geteilte Zeilen: Satz {summe('zeilen_satzgeteilt')}, "
              f"Rahmen {summe('rahmenteilungen')}, Spalte {summe('spaltenteilungen')}")
        print(f"Seitenwechsel {summe('seitenwechsel')} (zurück {summe('seitenwechsel_zurueck')}, im Block "
              f"{summe('seitenwechsel_im_block')}, Drittel-Regel verletzt {summe('drittel_regel_verletzt')}); "
              f"über Vorgänger {summe('ueber_vorgaenger')}, ausserhalb Rahmen {summe('ausserhalb_rahmen')}")
        print(f"Marker: Bezug Frage {summe('bezug_frage')}, Frage n {summe('frage_nr')}, Aufzählung "
              f"{summe('aufzaehlung')}, Stichwort {summe('stichwort')}, Typbezeichnung {summe('typbezeichnung')}, "
              f"Einleitung Fragen {summe('einleitung_fragen')}, Auftragsformel {summe('auftragsformel')}, "
              f"Einleitung folgt {summe('einleitung_folgt')}, Unterschriftsformel {summe('unterschriftsformel')}, "
              f"Ort und Datum {summe('ort_datum')}, Datum {summe('datumszeile')}, Verteiler {summe('verteiler')}, "
              f"Seitenzahl {summe('seitenzahl')}, Sperrschrift {summe('sperrschrift')}, Marker im Atom "
              f"{summe('marker_im_atom')}")
        print(f"Schlüssel-Wert: Paare {summe('kv_paare')}, Schlüssel ohne Wert {summe('kv_schluessel_ohne_wert')}, "
              f"Wert ohne Schlüssel {summe('kv_wert_ohne_schluessel')}, in Zeile {summe('kv_in_zeile')}")
        print(f"Satzanfänge mitten im Atom {summe('satzanfaenge_im_atom')} (in {summe('atome_mit_satzanfang')} "
              f"Atomen), Satzgrenzen am Atomende {summe('satzgrenzen_am_atomende')}")
        print(f"Textschicht: Zeilen {summe('ts_zeilen')}, gefunden {summe('ts_gefunden')} (ausserhalb Rahmen "
              f"{summe('ts_ausserhalb_rahmen')}, Typografie abweichend {summe('ts_typografie')}), nicht gefunden "
              f"{summe('ts_nicht_gefunden')}; Zeilenrahmen aus Textschicht {summe('zeilenrahmen_textschicht')}, "
              f"geschätzt {summe('zeilenrahmen_geschaetzt')}; gedreht {summe('gedreht')}")
        print(f"Prompt-Tokens (Schätzung, {ZEICHEN_JE_TOKEN} Zeichen/Token) {summe('prompt_tokens_schaetzung')}, "
              f"Blockformat {summe('blockformat_tokens_schaetzung')}")
        print(f"Gegenprobe ohne Zeilen: Atome {summe('gp_atome')}, lang {summe('gp_atome_lang')}, "
              f"Antwortmarker isoliert {summe('gp_marker_isoliert')} von {summe('gp_marker_gesamt')}")
        if fassung == VERSION_V3:
            print(f"atome-v3: Zeilen an Satzgrenzen ohne Leerzeichen geteilt {summe('zeilen_satz_ohne_leerzeichen')}, "
                  f"Folgenummer {summe('folgenummer')}, Klammerzeile mit Datum {summe('klammerzeile_datum')}, "
                  f"Zitatende {summe('zitatende')}, Zellenzahl wechselt {summe('zellenzahl_wechselt')}")
        print(f"\nGeschrieben: {rel(aus_ordner)}/<doc_id>.json, {rel(kennzahlen_pfad)}")


if __name__ == "__main__":
    main()

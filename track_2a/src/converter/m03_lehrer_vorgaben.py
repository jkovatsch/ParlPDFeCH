# SPDX-License-Identifier: Apache-2.0
"""Iteration 3 (E13): Vorgaben für den Lehrer, der ganze Docling-Dokumente beschriftet.

Reines Definitionsmodul ohne Netz- und Exportzugriff. Wird von m03_lehrer.py (Client),
m03_lehrer_pruefen.py (Plausibilität) und m03_lehrer_umfang.py (Kosten) importiert.

Enthält:
- ROLLEN: Blockrollen mit Definition und Abbildung auf eCH-0295 (TextTypeEnum u. a.)
- Wertelisten für die Felder auf Dokumentebene (Dokumentart, Typ, Empfehlung …)
- bloecke_vorbereiten(): Blöcke aus daten/docling/<id>.json, lange Antwortblöcke an
  Antwortmarkern geteilt (Unter-IDs B25.1, B25.2 …, die übrigen IDs bleiben)
- dokument_rendern(), nachrichten(): Eingabe für den Lehrer (Prompt deutsch, gilt für
  de/fr/it/rm-Dokumente); prompt_hash()
- json_schema(): JSON Schema je Aufruf (Block-IDs als Aufzählung, für json_schema-Modus)
- json_lesen(), pruefen(), teile_zusammenfuehren(): Validierung der Lehrer-Ausgabe

Der Lehrer schreibt keinen Text, nur Rollen-Schlüssel, Block-IDs und Listenwerte.
Grundlage: crisp-dm/archive-de/entscheide-de.md E13, crisp-dm/02-data-understanding/abschnitte/pdf.md
(Abschnitte 4 und 5), eCH-0295 schema.yaml (Stand 3cab44d vom 30.09.2026).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iter2_aufgabe import ECH_ABBILDUNG as EMPFEHLUNG_ECH  # noqa: E402
from m03_iter2_aufgabe import OPTIONEN as EMPFEHLUNG_OPTIONEN  # noqa: E402

SCHEMA_VERSION = "lehrer-v1"

# ---------------------------------------------------------------- Blockrollen

# (Schlüssel, Gruppe, Kurzname, Definition für den Lehrer, eCH-Ziel, Match-Art, zitierbar)
# eCH-Ziel: Wert von TextTypeEnum (text_type eines TextBlock) oder, ohne TextType, das
# Feld im eCH-Modell, für das der Block als Beleg dient. Match-Art wie m02_ech_regeln.py.
ROLLEN: list[tuple[str, str, str, str, str, str, bool]] = [
    # Vorstoss: von den Einreichenden verfasst
    ("title", "Vorstoss", "Titel",
     "Titel oder Betreff des Geschäfts, meist mit Typbezeichnung, oft mit Nummer oder "
     "Einreichenden («Interpellation … betreffend …», «Objet :», «Oggetto:»). Nicht für "
     "Abschnittsüberschriften.",
     "TextTypeEnum.title", "exakt", True),
    ("short_title", "Vorstoss", "Kurztitel",
     "Kurztitel oder Stichwort neben einem längeren Titel.",
     "TextTypeEnum.short_title", "exakt", True),
    ("submitted", "Vorstoss", "Vorstosstext",
     "Eingereichter Text, soweit er nicht Frage, Forderung oder Begründung ist: einleitende "
     "Sätze, Sachverhalt vor den Fragen, ungegliederter Vorstoss.",
     "TextTypeEnum.submitted", "exakt", True),
    ("demand", "Vorstoss", "Forderung",
     "Was der Vorstoss von der Exekutive verlangt: Auftrag einer Motion, Prüfauftrag eines "
     "Postulats, Antrag einer parlamentarischen Initiative, auch nummerierte Forderungen, die "
     "wie Fragen aussehen.",
     "TextTypeEnum.submitted", "nah", True),
    ("question", "Vorstoss", "Frage",
     "Eine Frage des Vorstosses an die Exekutive (Interpellation, Anfrage), nummeriert oder "
     "nicht. Stehen mehrere Fragen in einem Block, bekommt er trotzdem diese Rolle.",
     "TextTypeEnum.submitted", "nah", True),
    ("reasoning", "Vorstoss", "Begründung",
     "Begründung oder Erläuterung der Einreichenden (oft nach «Begründung», «Développement», "
     "«Motivazione»).",
     "TextTypeEnum.reasoning", "exakt", True),
    ("sponsor_info", "Vorstoss", "Urheberschaft",
     "Eigener Block, der Einreichende oder Mitunterzeichnende angibt: «eingereicht von», "
     "Namensliste, Fraktion, Zahl der Mitunterzeichnenden. Nicht für Titel mit Namen (title) "
     "oder den Unterschriftsblock (signature).",
     "Submission.sponsorship (Beleg)", "keine", True),
    # Antwort: von der Exekutive verfasst
    ("response_intro", "Antwort", "Einleitung der Antwort",
     "Vorbemerkung oder allgemeiner Teil der Exekutive, der keine bestimmte Frage beantwortet "
     "(«Vorbemerkung», «Allgemeines», «Remarques préliminaires», «Considerazioni generali»).",
     "TextTypeEnum.response", "nah", False),
    ("response", "Antwort", "Antwort",
     "Antwort der Exekutive auf eine oder mehrere Fragen oder Stellungnahme zum Vorstoss, "
     "auch als Fliesstext.",
     "TextTypeEnum.response", "exakt", False),
    ("recommendation", "Antwort", "Antrag der Exekutive",
     "Eigener Satz oder Abschnitt, in dem die Exekutive dem Parlament beantragt, den Vorstoss "
     "anzunehmen, abzulehnen, teilweise anzunehmen, in ein Postulat umzuwandeln oder "
     "abzuschreiben («Der Regierungsrat beantragt …», «Le Conseil d'État propose …», "
     "«Il Consiglio di Stato invita …»). Steht der Antrag mitten in einem Antwortblock, bleibt "
     "dieser response.",
     "TextTypeEnum.recommendation", "exakt", False),
    ("resolution", "Antwort", "Beschluss",
     "Beschlussformel oder Dispositiv («beschliesst:», «arrête :», «risolve:», nummerierte "
     "Beschlussziffern), auch Beschlussentwurf einer Vorlage.",
     "– (kein TextType, eCH-Befund 11)", "keine", False),
    # weitere Inhalte
    ("summary", "Inhalt", "Zusammenfassung",
     "Zusammenfassung, Résumé oder Kurzbeschrieb des Geschäfts.",
     "TextTypeEnum.summary", "exakt", False),
    ("report", "Inhalt", "Bericht oder Botschaft",
     "Erläuternder Text einer Vorlage, einer Botschaft oder eines Berichts der Exekutive, der "
     "keine Antwort auf einen Vorstoss ist.",
     "– (kein TextType, eCH-Befund 11)", "keine", False),
    ("table", "Inhalt", "Tabelle",
     "Tabelle mit Sachinhalt (Zahlen, Beträge, Übersicht), die keinem anderen Teil klar "
     "zugehört. Gehört sie zu einer Antwort, Forderung oder Begründung, gilt deren Rolle.",
     "– (kein TextType)", "keine", False),
    ("attachment", "Inhalt", "Anhang",
     "Anhang, Beilage, Beilagenverzeichnis, Verweis auf separate Unterlagen, "
     "Unterschriftenliste.",
     "– (kein TextType; separate Datei: TextBlock.document_url)", "keine", False),
    # Verfahren und Form
    ("metadata", "Form", "Metadaten",
     "Angaben im Kopf oder auf dem Deckblatt als Feld, Kasten oder Tabelle: Geschäftsnummer, "
     "Datum, Typ, Direktion, Dossier, Sitzung, Status. Bei Feldern bekommen Feldname und Wert "
     "diese Rolle.",
     "affair_number, Daten, affair_type (Beleg)", "keine", False),
    ("procedural_note", "Form", "Verfahrensvermerk",
     "Vermerk über einen Verfahrensschritt: Eingang, Überweisung, Zustellung, Ratsentscheid, "
     "Traktandierung, Frist, Aufwand für die Antwort, Satz wie «Am … reichte … folgende "
     "Anfrage ein».",
     "ProcedureState, Prozessschritte (Beleg)", "keine", False),
    ("letter", "Form", "Briefelemente",
     "Adress- und Absenderblock, Anrede, Grussformel.",
     "– (kein TextType)", "keine", False),
    ("signature", "Form", "Unterschrift",
     "Ort und Datum, Unterschriftsblock mit Funktion und Namen, Unterschriftsbild.",
     "Submission.sponsorship bzw. ResponseStep.responder (Beleg)", "keine", False),
    ("distribution", "Form", "Verteiler",
     "Verteiler, «Mitteilung an», «Kopie an», Empfänger eines Protokollauszugs.",
     "– (kein TextType)", "keine", False),
    ("heading", "Form", "Zwischenüberschrift",
     "Gliederungsüberschrift ohne eigenen Inhalt («Begründung», «Antwort des Regierungsrates», "
     "«Zu Frage 3», «Développement»). Enthält die Überschrift die Frage selbst, gilt question.",
     "– (kein TextType)", "keine", False),
    ("header_footer", "Form", "Kopf- oder Fusszeile",
     "Wiederkehrende Kopf- oder Fusszeile, Seitenzahl, Dateiname. Trägt sie eine "
     "Geschäftsnummer oder ein Datum, bleibt die Rolle; als Beleg darf sie trotzdem dienen.",
     "– (kein TextType)", "keine", False),
    ("other", "Form", "Sonstiges",
     "Alles andere: Logo, Wappen, Bild ohne Text, Inhaltsverzeichnis, Fussnote, Vorlagenrest "
     "oder Platzhalter, Zeichenmüll aus der Texterkennung.",
     "– (kein TextType)", "keine", False),
]
ROLLEN_KEYS = [r[0] for r in ROLLEN]
ZITIERBAR = {r[0] for r in ROLLEN if r[6]}
GRUPPEN = {"Vorstoss": "Vorstoss (von den Einreichenden verfasst)",
           "Antwort": "Antwort (von der Exekutive verfasst)",
           "Inhalt": "Weitere Inhalte",
           "Form": "Verfahren und Form"}

# ---------------------------------------------------------------- Felder auf Dokumentebene

DOKUMENTARTEN = {
    "vorstoss": "eingereichter Vorstoss ohne Antwort",
    "antwort_mit_vorstoss": "Antwort der Exekutive, die den Vorstoss oder seine Fragen wiederholt",
    "antwort_ohne_vorstoss": "Antwort der Exekutive ohne Wiederholung des Vorstosses",
    "vorlage_bericht": "Vorlage, Botschaft oder Bericht der Exekutive",
    "beschluss": "Beschluss oder Protokollauszug ohne Antwort auf einen Vorstoss",
    "verweis": "Verweis auf ein anderes Dokument, kaum eigener Inhalt",
    "anderes": "anderes Dokument",
}
SPRACHEN = ["de", "fr", "it", "rm", "mehrsprachig"]
# AffairTypeEnum (eCH-0295) und zwei eigene Werte
TYPEN = {
    "motion": "Motion (auch Auftrag, Mozione)",
    "postulate": "Postulat (auch Anzug)",
    "interpellation": "Interpellation (auch Interpellanza)",
    "request": "schriftliche Anfrage (Kleine/Einfache Anfrage, Question écrite, Interrogazione)",
    "question": "Frage für die Fragestunde, mündlich beantwortet",
    "parliamentary_initiative": "parlamentarische Initiative",
    "draft_decree": "Vorlage oder Beschlussesentwurf der Exekutive",
    "motion_and_postulate": "Motion und Postulat kombiniert",
    "motion_then_postulate": "Motion, als Postulat überwiesen",
    "anderer": "ein anderer Typ (z. B. Petition, Resolution, Wahl, Bericht, Volksinitiative)",
    "nicht_erkennbar": "das Dokument nennt keinen Typ",
}
ANTWORTGLIEDERUNG = {
    "je_frage": "jede Antwort bezieht sich auf eine bestimmte Frage",
    "gruppiert": "je Frage, aber einzelne Antworten beantworten mehrere Fragen zusammen",
    "fliesstext": "Antwort als Fliesstext ohne Bezug auf einzelne Fragen",
    "keine_antwort": "das Dokument enthält keine Antwort",
}
MITUNTERZEICHNENDE_ANGABE = {
    "namen": "Namen der Mitunterzeichnenden stehen im Dokument",
    "anzahl": "nur die Zahl der Mitunterzeichnenden",
    "erwaehnt": "erwähnt ohne Namen und ohne Zahl",
    "keine": "keine Angabe",
}
FELDER_UNSICHER = ["dokumentart", "geschaeftstyp", "fragen_antworten", "empfehlung",
                   "einreichende", "mitunterzeichnende", "antwortende_stelle", "daten"]
DATEN_SCHLUESSEL = ["eingereicht", "beantwortet"]
# Rollen, die als Beleg einer Empfehlung bzw. für Einreichende plausibel sind (nur Warnungen)
EMPFEHLUNG_BELEGROLLEN = {"recommendation", "response", "resolution", "metadata", "title",
                          "procedural_note", "response_intro", "header_footer"}
PERSONEN_BELEGROLLEN = {"title", "sponsor_info", "signature", "metadata", "letter", "submitted",
                        "procedural_note", "header_footer", "attachment", "short_title"}

RX_ID = re.compile(r"^B\d+(\.\d+)?$")

# ---------------------------------------------------------------- Blöcke vorbereiten

# Antwortmarker am Zeilenanfang (de, fr, it, rm). Gedruckte Nummern sind kein verlässlicher
# Schlüssel (pdf.md, Abschnitt 5.3); geteilt wird nur, damit der Lehrer einzelne Antworten
# zeigen kann. Die Zuordnung macht der Lehrer.
ANTWORTMARKER = re.compile(
    r"^\s*(zu (den )?(frage|fragen|ziffer|ziffern|punkt|punkten)\s+\d|"
    r"ad (frage |ziffer |punkt |domanda )?\d+\s*[:.)]|antwort (auf|zu) (frage )?\d|"
    r"frage \d+\s*[:.)]|r[ée]ponse (à |a )?(la )?(question )?\d|"
    r"(à |a )?(la )?question \d+\s*[:.)]|risposta (alla )?(domanda )?\d|domanda \d+\s*[:.)]|"
    r"tar la dumonda \d|dumonda \d+\s*[:.)])",
    re.I)
TEILEN_AB_ZEICHEN = 800      # nur längere Blöcke werden geteilt
TEILEN_LABELS = {"text", "list_item"}


def _teile_an_markern(text: str) -> list[tuple[int, int]]:
    """Zeichenbereiche der Teile, wenn der Text mindestens zwei Antwortmarker an
    Zeilenanfängen hat; sonst leere Liste."""
    starts = []
    pos = 0
    for zeile in text.split("\n"):
        if ANTWORTMARKER.match(zeile):
            starts.append(pos)
        pos += len(zeile) + 1
    if len(starts) < 2:
        return []
    if text[:starts[0]].strip():
        starts = [0] + starts
    grenzen = starts + [len(text)]
    return [(grenzen[i], grenzen[i + 1]) for i in range(len(starts))]


def bloecke_vorbereiten(dok: dict, teilen: bool = True) -> list[dict]:
    """Blöcke eines Docling-JSON (m03_docling_zerlegen.py) für den Lehrer.

    Je Block: id, label, seite, kopf_fuss, eltern (Label der Gruppe), liste (nummeriert),
    ocr (Anteil ≥ 0,5), text (Wortlaut aus den Textzellen), zeichen, teil_von.
    Lange Text- oder Listenblöcke mit mindestens zwei Antwortmarkern werden geteilt; die
    Teile heissen <ID>.1, <ID>.2 …, ihr Zeichenbereich bezieht sich auf text_gesamt.
    """
    if dok.get("status") != "success":
        raise ValueError(f"Docling-Status {dok.get('status')!r}, Dokument {dok.get('doc_id')}")
    aus = []
    for b in dok["bloecke"]:
        text = b.get("text") or ""
        basis = {
            "id": b["id"], "label": b.get("label") or "", "seite": b.get("seite"),
            "kopf_fuss": b.get("kopf_fuss"),
            "eltern": (b.get("eltern") or {}).get("label"),
            "liste_nummeriert": bool((b.get("liste") or {}).get("nummeriert")),
            "ocr": (b.get("ocr_anteil") or 0) >= 0.5,
            "teil_von": None,
        }
        z0 = (b.get("zeichen") or [0, 0])[0]
        teile = (_teile_an_markern(text) if teilen and basis["label"] in TEILEN_LABELS
                 and len(text) >= TEILEN_AB_ZEICHEN else [])
        if not teile:
            aus.append(basis | {"text": text, "zeichen": b.get("zeichen")})
            continue
        for k, (a, e) in enumerate(teile, 1):
            stueck = text[a:e]
            rechts = len(stueck.rstrip())
            aus.append(basis | {"id": f"{b['id']}.{k}", "teil_von": b["id"],
                                "text": stueck[:rechts], "zeichen": [z0 + a, z0 + a + rechts]})
    return aus


# ---------------------------------------------------------------- Eingabe rendern

FORM = {
    "section_header": "Überschrift", "title": "Überschrift", "text": "Text",
    "list_item": "Listenpunkt", "page_header": "Kopfzeile", "page_footer": "Fusszeile",
    "picture": "Bild", "footnote": "Fussnote", "table": "Tabelle", "caption": "Bildlegende",
    "document_index": "Verzeichnis", "checkbox_selected": "Kästchen angekreuzt",
    "checkbox_unselected": "Kästchen leer", "formula": "Formel", "code": "Code",
}
ELTERN = {"key_value_area": "Feld", "form_area": "Formular", "picture": "im Bild"}
MAX_ZEICHEN_BLOCK = 2000
KOPF_ZEICHEN, FUSS_ZEICHEN = 1500, 400


def _anzeigetext(b: dict, max_zeichen: int) -> str:
    t = b["text"] or ""
    if b["label"] == "table":
        zeilen = [" | ".join(c.strip() for c in z.split("\t")) for z in t.split("\n") if z.strip()]
        t = " / ".join(zeilen)
    else:
        t = re.sub(r"(\w)-\n(?=[a-zäöüàéèç])", r"\1", t)   # nur Anzeige; Wortlaut bleibt im Block
        t = re.sub(r"\s*\n\s*", " ", t)
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    if not t:
        return "(ohne Text)"
    if len(t) > max_zeichen:
        t = (t[:KOPF_ZEICHEN].rstrip() + f" […{len(t) - KOPF_ZEICHEN - FUSS_ZEICHEN} Zeichen "
             "ausgelassen…] " + t[-FUSS_ZEICHEN:].lstrip())
    return t


def dokument_rendern(bloecke: list[dict], max_zeichen_block: int = MAX_ZEICHEN_BLOCK) -> str:
    """Blockliste als Text: Seitenmarken, je Block «[ID] (Form, Merkmale) Text»."""
    zeilen = []
    seite = None
    for b in bloecke:
        if b["seite"] != seite:
            seite = b["seite"]
            zeilen.append(f"=== Seite {seite} ===")
        merkmale = [FORM.get(b["label"], b["label"] or "Block")]
        if b["eltern"] in ELTERN:
            merkmale.append(ELTERN[b["eltern"]])
        if b["label"] == "list_item" and b["liste_nummeriert"]:
            merkmale.append("nummeriert")
        if b["ocr"]:
            merkmale.append("OCR")
        zeilen.append(f"[{b['id']}] ({', '.join(merkmale)}) {_anzeigetext(b, max_zeichen_block)}")
    return "\n".join(zeilen)


# ---------------------------------------------------------------- Prompt

SYSTEM = ("Du beschriftest Dokumente aus Schweizer Parlamenten (Deutsch, Französisch, "
          "Italienisch, Rätoromanisch). Du schreibst keinen Text ab und erfindest nichts. Du "
          "antwortest nur mit einem JSON-Objekt aus Rollen-Schlüsseln, Block-IDs und Werten "
          "aus vorgegebenen Listen.")

EINLEITUNG = """\
# Aufgabe

Unten steht ein Dokument aus einem Schweizer Parlament, zerlegt in Blöcke mit den IDs [B1], [B2] … in Lesereihenfolge; geteilte Blöcke heissen [B25.1], [B25.2] … Vor jedem Block steht in Klammern seine Form laut Layout-Erkennung (Überschrift, Text, Listenpunkt, Tabelle, Kopfzeile …), «Feld» für Schlüssel/Wert-Felder und «OCR», wenn der Text aus einer Texterkennung stammt. Die Form ist nur ein Hinweis: Die Rolle bestimmst du nach der Funktion des Blocks im parlamentarischen Verfahren. Das Dokument kann deutsch, französisch, italienisch oder rätoromanisch sein; die Listen unten gelten für alle Sprachen.

Du gibst nur Schlüssel, Block-IDs und Werte aus den Listen aus, nie Text aus dem Dokument, keine Namen, keine Daten, keine Erklärungen."""

REGELN = """\
# Regeln

1. Jeder Block erhält genau eine Rolle aus der Liste. Massgebend ist seine Funktion, nicht seine Form.
2. «zitiert»: Liste der Blöcke, die den Vorstoss in einem Dokument der Exekutive wiederholen (zitierter Vorstosstext, wiederholte Fragen, zitierte Forderung oder Begründung, wiederholter Titel des Vorstosses). Erlaubt nur bei den Rollen {zitierbar}. In einem eingereichten Vorstoss selbst ist nichts zitiert.
3. «fragen_antworten»: Paare aus Frage-Block und Antwort-Block. «frage» ist ein Block mit Rolle question oder demand (zitiert oder nicht), «antwort» ein Block mit Rolle response. Beantwortet ein Block mehrere Fragen, gib mehrere Paare mit derselben Antwort aus; verteilt sich eine Antwort auf mehrere Blöcke, mehrere Paare mit derselben Frage. Ordne nach Inhalt und Reihenfolge zu, nicht nur nach der gedruckten Nummer. Steht die Frage nicht im Dokument, aber die Antwort nennt ihre Nummer, setze «frage» auf null und «frage_nr» auf diese Nummer; sonst ist «frage_nr» null. Antwortet die Exekutive nur im Fliesstext ohne Bezug auf einzelne Fragen, bleibt die Liste leer.
4. «empfehlung»: Antrag der Exekutive an das Parlament zu diesem Vorstoss, mit «beleg» = Block, in dem er steht. Ohne Antrag im Dokument (z. B. Interpellation, Anfrage, eingereichter Vorstoss) gilt keine_passt mit beleg null. Massgebend ist der Antrag zur Annahme oder Überweisung, nicht seine Begründung.
5. «geschaeftstyp»: Typ des Geschäfts, wie ihn das Dokument nennt, mit «beleg» = Block mit der Typbezeichnung; bei nicht_erkennbar ist beleg null.
6. «einreichende», «mitunterzeichnende», «antwortende_stelle»: alle Blöcke, in denen die Einreichenden, die Mitunterzeichnenden bzw. die antwortende Exekutive genannt sind (Titel, Urheberschaft, Unterschrift, Metadaten, Briefkopf …). Leere Liste, wenn das Dokument sie nicht nennt.
7. «daten»: Block mit dem Datum der Einreichung bzw. dem Datum der Antwort oder des Beschlusses der Exekutive; null, wenn es fehlt.
8. «unsicher»: Blöcke, deren Rolle du nicht sicher bestimmen kannst; «unsichere_felder»: Felder, bei denen du unsicher bist. «unlesbar»: Blöcke, deren Text offensichtlich verstümmelt ist (Zeichenmüll aus der Texterkennung).
9. Rate nicht. Was das Dokument nicht enthält, ist null, keine_passt oder eine leere Liste."""

AUSGABE_VOLL = """\
# Ausgabe

{bereich}

Gib genau ein JSON-Objekt mit diesen Feldern aus:
- "dokumentart": {dokumentarten}
- "sprache": {sprachen}
- "rollen": Objekt Block-ID → Rolle, für jeden Block des Bereichs genau einmal
- "zitiert", "unsicher", "unlesbar": Listen von Block-IDs aus dem Bereich
- "unsichere_felder": Liste aus {felder}
- "geschaeftstyp": {{"wert": {typen}, "beleg": Block-ID oder null}}
- "fragen_antworten": Liste von {{"frage": Block-ID oder null, "frage_nr": Zahl oder null, "antwort": Block-ID}}
- "antwortgliederung": {gliederung}
- "empfehlung": {{"wert": {empfehlungen}, "beleg": Block-ID oder null}}
- "einreichende", "mitunterzeichnende", "antwortende_stelle": Listen von Block-IDs
- "mitunterzeichnende_angabe": {mitangabe}
- "daten": {{"eingereicht": Block-ID oder null, "beantwortet": Block-ID oder null}}

Werte:
- dokumentart: {dokumentarten_def}
- geschaeftstyp: {typen_def}
- antwortgliederung: {gliederung_def}
- empfehlung: {empfehlungen_def}
- mitunterzeichnende_angabe: {mitangabe_def}"""

AUSGABE_TEIL = """\
# Ausgabe

{bereich}

Gib genau ein JSON-Objekt mit diesen Feldern aus:
- "rollen": Objekt Block-ID → Rolle, für jeden Block des Bereichs genau einmal
- "zitiert", "unsicher", "unlesbar": Listen von Block-IDs aus dem Bereich"""

BEISPIEL = """\
# Beispiel (erfundenes, gekürztes Dokument)

=== Seite 1 ===
[B1] (Kopfzeile) Regierungsrat · Sitzung vom ‹Datum›
[B2] (Überschrift) Interpellation ‹Name› betreffend Schulwege; Beantwortung
[B3] (Text) Am ‹Datum› reichte ‹Name› folgende Interpellation ein:
[B4] (Text) «Viele Schulwege sind gefährlich. Ich bitte den Regierungsrat um Antwort auf folgende Fragen:
[B5] (Listenpunkt, nummeriert) 1. Wie viele Unfälle gab es?
[B6] (Listenpunkt, nummeriert) 2. Was unternimmt der Kanton?»
[B7] (Überschrift) Antwort des Regierungsrates
[B8] (Text) Zu Frage 1: Im Jahr ‹Jahr› waren es ‹Zahl›.
[B9] (Text) Zu Frage 2: Der Kanton prüft Massnahmen.
[B10] (Text) Im Namen des Regierungsrates ‹Funktion› ‹Name›

{{"dokumentart": "antwort_mit_vorstoss", "sprache": "de", "rollen": {{"B1": "header_footer", "B2": "title", "B3": "procedural_note", "B4": "submitted", "B5": "question", "B6": "question", "B7": "heading", "B8": "response", "B9": "response", "B10": "signature"}}, "zitiert": ["B4", "B5", "B6"], "unsicher": [], "unlesbar": [], "unsichere_felder": [], "geschaeftstyp": {{"wert": "interpellation", "beleg": "B2"}}, "fragen_antworten": [{{"frage": "B5", "frage_nr": null, "antwort": "B8"}}, {{"frage": "B6", "frage_nr": null, "antwort": "B9"}}], "antwortgliederung": "je_frage", "empfehlung": {{"wert": "keine_passt", "beleg": null}}, "einreichende": ["B2", "B3"], "mitunterzeichnende": [], "mitunterzeichnende_angabe": "keine", "antwortende_stelle": ["B1", "B10"], "daten": {{"eingereicht": "B3", "beantwortet": "B1"}}}}"""


def _rollenliste(reihenfolge: str) -> str:
    rollen = ROLLEN if reihenfolge == "standard" else list(reversed(ROLLEN))
    gruppen = list(GRUPPEN) if reihenfolge == "standard" else list(reversed(GRUPPEN))
    teile = ["# Blockrollen"]
    for g in gruppen:
        teile.append(f"\n## {GRUPPEN[g]}")
        for key, gr, name, definition, *_ in rollen:
            if gr == g:
                teile.append(f"- {key} ({name}): {definition}")
    return "\n".join(teile)


def _liste(werte) -> str:
    return " | ".join(werte)


def _def(werte: dict) -> str:
    return "; ".join(f"{k} = {v}" for k, v in werte.items())


def bereich_text(ids_bereich: list[str], ids_alle: list[str], teil: int, teile: int) -> str:
    if len(ids_bereich) == len(ids_alle):
        return (f"Beschrifte alle Blöcke {ids_alle[0]} bis {ids_alle[-1]} "
                f"({len(ids_alle)} Blöcke).")
    s = (f"Dieses Dokument wird in {teile} Aufrufen beschriftet. In diesem Aufruf (Teil "
         f"{teil}) beschriftest du nur die Blöcke {ids_bereich[0]} bis {ids_bereich[-1]} "
         f"({len(ids_bereich)} Blöcke); die übrigen Blöcke erfassen andere Aufrufe.")
    if ids_bereich[-1] == ids_alle[-1]:
        s += (" Die Felder zum ganzen Dokument (Paare, Empfehlung, Personen, Daten) gibst du "
              "in diesem Aufruf aus; sie dürfen auf alle Blöcke des Dokuments verweisen.")
    return s


def anleitung(reihenfolge: str = "standard", voll: bool = True, bereich: str = "{bereich}") -> str:
    """Anleitung ohne Dokument. Die Reihenfolge «umgekehrt» kehrt die Rollenliste um
    (zweiter Durchlauf desselben Lehrers als Zweitmeinung, E13 Punkt 3)."""
    zitierbar = ", ".join(k for k in ROLLEN_KEYS if k in ZITIERBAR)
    if voll:
        ausgabe = AUSGABE_VOLL.format(
            bereich=bereich, dokumentarten=_liste(DOKUMENTARTEN), sprachen=_liste(SPRACHEN),
            felder=_liste(FELDER_UNSICHER), typen=_liste(TYPEN),
            gliederung=_liste(ANTWORTGLIEDERUNG), empfehlungen=_liste(EMPFEHLUNG_OPTIONEN),
            mitangabe=_liste(MITUNTERZEICHNENDE_ANGABE),
            dokumentarten_def=_def(DOKUMENTARTEN), typen_def=_def(TYPEN),
            gliederung_def=_def(ANTWORTGLIEDERUNG),
            empfehlungen_def=_def({k: v for k, v in EMPFEHLUNG_OPTIONEN.items()}),
            mitangabe_def=_def(MITUNTERZEICHNENDE_ANGABE))
    else:
        ausgabe = AUSGABE_TEIL.format(bereich=bereich)
    return "\n\n".join([EINLEITUNG, _rollenliste(reihenfolge), REGELN.format(zitierbar=zitierbar),
                        ausgabe, BEISPIEL.format()])


def prompt_hash(reihenfolge: str = "standard") -> str:
    """SHA-256 über Systemprompt, beide Anleitungsformen und Schemaversion (ohne Dokument)."""
    h = hashlib.sha256()
    for teil in (SCHEMA_VERSION, SYSTEM, anleitung(reihenfolge, True), anleitung(reihenfolge, False)):
        h.update(teil.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def nachrichten(dok_text: str, ids_bereich: list[str], ids_alle: list[str], teil: int = 1,
                teile: int = 1, reihenfolge: str = "standard") -> list[dict]:
    """Chat-Nachrichten für einen Aufruf. Die Anleitung steht vor dem Dokument, damit
    Anbieter mit Präfix-Cache den gleichen Anfang wiederverwenden können."""
    voll = ids_bereich[-1] == ids_alle[-1]
    text = (anleitung(reihenfolge, voll, bereich_text(ids_bereich, ids_alle, teil, teile))
            + "\n\n# Dokument\n\n" + dok_text)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]


def eingabe_hash(dok_text: str) -> str:
    return hashlib.sha256(dok_text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- JSON Schema

def json_schema(ids_alle: list[str], ids_bereich: list[str], voll: bool,
                reihenfolge: str = "standard") -> dict:
    """JSON Schema (Draft 2020-12, ohne patternProperties) für einen Aufruf.

    Block-IDs stehen als Aufzählung im Schema. Mit strukturierter Ausgabe (vLLM, Infomaniak
    json_schema) kann der Lehrer damit nur gültige IDs und Rollen erzeugen; die Querbezüge
    (Rollen in Paaren, Belege) prüft pruefen()."""
    rollen = ROLLEN_KEYS if reihenfolge == "standard" else list(reversed(ROLLEN_KEYS))
    alle = list(ids_alle)
    bereich = list(ids_bereich)

    def liste(ids):
        return {"type": "array", "items": {"type": "string", "enum": ids}}

    def id_oder_null():
        return {"anyOf": [{"type": "string", "enum": alle}, {"type": "null"}]}

    props = {
        "rollen": {"type": "object",
                   "properties": {i: {"type": "string", "enum": rollen} for i in bereich},
                   "required": bereich, "additionalProperties": False},
        "zitiert": liste(bereich), "unsicher": liste(bereich), "unlesbar": liste(bereich),
    }
    if voll:
        props |= {
            "dokumentart": {"type": "string", "enum": list(DOKUMENTARTEN)},
            "sprache": {"type": "string", "enum": SPRACHEN},
            "unsichere_felder": {"type": "array",
                                 "items": {"type": "string", "enum": FELDER_UNSICHER}},
            "geschaeftstyp": {"type": "object",
                              "properties": {"wert": {"type": "string", "enum": list(TYPEN)},
                                             "beleg": id_oder_null()},
                              "required": ["wert", "beleg"], "additionalProperties": False},
            "fragen_antworten": {"type": "array", "items": {
                "type": "object",
                "properties": {"frage": id_oder_null(),
                               "frage_nr": {"anyOf": [{"type": "integer", "minimum": 1},
                                                      {"type": "null"}]},
                               "antwort": {"type": "string", "enum": alle}},
                "required": ["frage", "frage_nr", "antwort"], "additionalProperties": False}},
            "antwortgliederung": {"type": "string", "enum": list(ANTWORTGLIEDERUNG)},
            "empfehlung": {"type": "object",
                           "properties": {"wert": {"type": "string",
                                                   "enum": list(EMPFEHLUNG_OPTIONEN)},
                                          "beleg": id_oder_null()},
                           "required": ["wert", "beleg"], "additionalProperties": False},
            "einreichende": liste(alle), "mitunterzeichnende": liste(alle),
            "antwortende_stelle": liste(alle),
            "mitunterzeichnende_angabe": {"type": "string",
                                          "enum": list(MITUNTERZEICHNENDE_ANGABE)},
            "daten": {"type": "object",
                      "properties": {k: id_oder_null() for k in DATEN_SCHLUESSEL},
                      "required": DATEN_SCHLUESSEL, "additionalProperties": False},
        }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"ParlPDFeCH {SCHEMA_VERSION}", "type": "object", "properties": props,
            "required": list(props), "additionalProperties": False}


FELDER_VOLL = list(json_schema(["B1"], ["B1"], True)["properties"])
FELDER_TEIL = list(json_schema(["B1"], ["B1"], False)["properties"])

# ---------------------------------------------------------------- Ausgabe lesen und prüfen


def json_lesen(text: str) -> tuple[dict | None, str]:
    """Liest das JSON-Objekt aus der Antwort; toleriert Markdown-Zäune und Text davor/danach.
    -> (Objekt, Fehler)."""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    a, e = t.find("{"), t.rfind("}")
    if a < 0 or e <= a:
        return None, "kein vollständiges JSON-Objekt gefunden"
    try:
        obj = json.loads(t[a:e + 1])
    except json.JSONDecodeError as ex:
        return None, f"kein gültiges JSON ({ex.msg}, Zeichen {ex.pos})"
    if not isinstance(obj, dict):
        return None, "JSON ist kein Objekt"
    return obj, ""


def _ist_id_liste(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def pruefen(obj: dict, ids_alle: list[str], ids_bereich: list[str], voll: bool,
            rollen_vorher: dict | None = None) -> tuple[list[str], list[str]]:
    """Prüft eine Lehrer-Ausgabe. -> (Fehler, Warnungen).

    Fehler machen die Ausgabe ungültig (Korrekturaufruf bzw. Verwerfen): Felder, Typen,
    Listenwerte, Rollen für genau die Blöcke des Bereichs, existierende IDs, Querbezüge
    (Paare: Frage question/demand, Antwort response; «zitiert» nur bei zitierbaren Rollen;
    Beleg der Empfehlung genau dann, wenn ein Antrag genannt ist).
    Warnungen sind Plausibilitätshinweise ohne Verwerfen.
    rollen_vorher: Rollen aus früheren Teilen desselben Dokuments (für Querbezüge)."""
    f: list[str] = []
    w: list[str] = []
    erwartet = FELDER_VOLL if voll else FELDER_TEIL
    fehlt = [k for k in erwartet if k not in obj]
    extra = [k for k in obj if k not in erwartet]
    if fehlt:
        f.append("fehlende Felder: " + ", ".join(map(str, fehlt)))
    if extra:
        f.append("unbekannte Felder: " + ", ".join(map(str, extra)))
    alle = set(ids_alle)
    bereich = set(ids_bereich)

    rollen = obj.get("rollen")
    if not isinstance(rollen, dict):
        f.append("rollen ist kein Objekt")
        rollen = {}
    fehlend = [i for i in ids_bereich if i not in rollen]
    fremd = [i for i in rollen if i not in bereich]
    if fehlend:
        f.append(f"rollen fehlt für {len(fehlend)} Blöcke: " + ", ".join(map(str, fehlend[:15])))
    if fremd:
        f.append(f"rollen für Blöcke ausserhalb des Bereichs: " + ", ".join(map(str, fremd[:15])))
    falsch = {i: r for i, r in rollen.items() if not isinstance(r, str) or r not in ROLLEN_KEYS}
    if falsch:
        f.append("unbekannte Rollen: " + ", ".join(f"{i}={r!r}" for i, r in list(falsch.items())[:10]))
    bekannt = dict(rollen_vorher or {}) | {i: r for i, r in rollen.items()
                                           if i in bereich and isinstance(r, str)}

    for feld in ("zitiert", "unsicher", "unlesbar"):
        v = obj.get(feld, [])
        if not _ist_id_liste(v):
            f.append(f"{feld} ist keine Liste von Block-IDs")
            continue
        aus = [i for i in v if i not in bereich]
        if aus:
            f.append(f"{feld} enthält IDs ausserhalb des Bereichs: " + ", ".join(map(str, aus[:10])))
    for i in obj.get("zitiert", []) if _ist_id_liste(obj.get("zitiert", [])) else []:
        if isinstance(rollen.get(i), str) and rollen[i] not in ZITIERBAR:
            f.append(f"zitiert: {i} hat Rolle {rollen[i]}, zitiert ist nur bei "
                     + ", ".join(sorted(ZITIERBAR)) + " erlaubt")

    if not voll:
        return f, w

    def wert(feld, liste):
        v = obj.get(feld)
        if not isinstance(v, str) or v not in liste:
            f.append(f"{feld}: {v!r} ist kein erlaubter Wert")

    wert("dokumentart", DOKUMENTARTEN)
    wert("sprache", SPRACHEN)
    wert("antwortgliederung", ANTWORTGLIEDERUNG)
    wert("mitunterzeichnende_angabe", MITUNTERZEICHNENDE_ANGABE)
    uf = obj.get("unsichere_felder", [])
    if not isinstance(uf, list) or any(x not in FELDER_UNSICHER for x in uf):
        f.append("unsichere_felder enthält unbekannte Felder")

    def id_ok(feld, v, null_ok=True):
        if v is None and null_ok:
            return True
        if not isinstance(v, str) or v not in alle:
            f.append(f"{feld}: {v!r} ist keine Block-ID des Dokuments")
            return False
        return True

    for feld in ("einreichende", "mitunterzeichnende", "antwortende_stelle"):
        v = obj.get(feld, [])
        if not _ist_id_liste(v):
            f.append(f"{feld} ist keine Liste von Block-IDs")
            continue
        for i in v:
            if id_ok(feld, i, False) and i in bekannt and bekannt[i] not in PERSONEN_BELEGROLLEN:
                w.append(f"{feld}: {i} hat Rolle {bekannt[i]}")

    gt = obj.get("geschaeftstyp")
    if not isinstance(gt, dict) or set(gt) != {"wert", "beleg"}:
        f.append("geschaeftstyp muss genau wert und beleg enthalten")
    else:
        if not isinstance(gt["wert"], str) or gt["wert"] not in TYPEN:
            f.append(f"geschaeftstyp.wert: {gt['wert']!r} ist kein erlaubter Wert")
        id_ok("geschaeftstyp.beleg", gt["beleg"])
        if gt["wert"] == "nicht_erkennbar" and gt["beleg"] is not None:
            f.append("geschaeftstyp: bei nicht_erkennbar muss beleg null sein")
        if isinstance(gt["wert"], str) and gt["wert"] in TYPEN and gt["wert"] != "nicht_erkennbar" \
                and gt["beleg"] is None:
            f.append("geschaeftstyp: beleg fehlt")

    em = obj.get("empfehlung")
    if not isinstance(em, dict) or set(em) != {"wert", "beleg"}:
        f.append("empfehlung muss genau wert und beleg enthalten")
    else:
        if not isinstance(em["wert"], str) or em["wert"] not in EMPFEHLUNG_OPTIONEN:
            f.append(f"empfehlung.wert: {em['wert']!r} ist kein erlaubter Wert")
        id_ok("empfehlung.beleg", em["beleg"])
        if em["wert"] == "keine_passt" and em["beleg"] is not None:
            f.append("empfehlung: bei keine_passt muss beleg null sein")
        if isinstance(em["wert"], str) and em["wert"] in EMPFEHLUNG_OPTIONEN \
                and em["wert"] != "keine_passt" and em["beleg"] is None:
            f.append("empfehlung: beleg fehlt")
        if isinstance(em["beleg"], str) and em["beleg"] in bekannt \
                and bekannt[em["beleg"]] not in EMPFEHLUNG_BELEGROLLEN:
            w.append(f"empfehlung.beleg {em['beleg']} hat Rolle {bekannt[em['beleg']]}")

    paare = obj.get("fragen_antworten")
    if not isinstance(paare, list):
        f.append("fragen_antworten ist keine Liste")
        paare = []
    gesehen = set()
    for k, p in enumerate(paare, 1):
        if not isinstance(p, dict) or set(p) != {"frage", "frage_nr", "antwort"}:
            f.append(f"fragen_antworten[{k}] muss genau frage, frage_nr, antwort enthalten")
            continue
        fr, nr, an = p["frage"], p["frage_nr"], p["antwort"]
        if nr is not None and (not isinstance(nr, int) or isinstance(nr, bool) or nr < 1):
            f.append(f"fragen_antworten[{k}].frage_nr: {nr!r} ist keine positive Zahl")
        if fr is None and nr is None:
            f.append(f"fragen_antworten[{k}]: frage und frage_nr sind beide null")
        if fr is not None and nr is not None:
            f.append(f"fragen_antworten[{k}]: frage_nr nur, wenn frage null ist")
        if id_ok(f"fragen_antworten[{k}].frage", fr) and fr in bekannt \
                and bekannt[fr] not in ("question", "demand"):
            f.append(f"fragen_antworten[{k}]: Frage {fr} hat Rolle {bekannt[fr]} "
                     "(erlaubt: question, demand)")
        if id_ok(f"fragen_antworten[{k}].antwort", an, False) and an in bekannt \
                and bekannt[an] != "response":
            f.append(f"fragen_antworten[{k}]: Antwort {an} hat Rolle {bekannt[an]} "
                     "(erlaubt: response)")
        schluessel = tuple(x if isinstance(x, (str, int, type(None))) else repr(x)
                           for x in (fr, nr, an))
        if schluessel in gesehen:
            w.append(f"fragen_antworten[{k}]: Paar doppelt")
        gesehen.add(schluessel)

    da = obj.get("daten")
    if not isinstance(da, dict) or set(da) != set(DATEN_SCHLUESSEL):
        f.append("daten muss genau " + " und ".join(DATEN_SCHLUESSEL) + " enthalten")
    else:
        for k in DATEN_SCHLUESSEL:
            id_ok(f"daten.{k}", da[k])

    # Warnungen zur Stimmigkeit (nur wenn die Rollen aller Blöcke bekannt sind)
    if set(bekannt) >= alle:
        art = obj.get("dokumentart")
        n_resp = sum(r == "response" for r in bekannt.values())
        if art == "vorstoss" and n_resp:
            w.append(f"dokumentart vorstoss, aber {n_resp} Blöcke response")
        if art == "vorstoss" and obj.get("zitiert"):
            w.append("dokumentart vorstoss, aber Blöcke als zitiert markiert")
        if art in ("antwort_mit_vorstoss", "antwort_ohne_vorstoss") and not n_resp:
            w.append("Antwort-Dokument ohne Block mit Rolle response")
        gl = obj.get("antwortgliederung")
        if gl in ("je_frage", "gruppiert") and not paare:
            w.append(f"antwortgliederung {gl}, aber keine Frage-Antwort-Paare")
        if gl in ("fliesstext", "keine_antwort") and paare:
            w.append(f"antwortgliederung {gl}, aber {len(paare)} Paare")
    return f, w


def teile_zusammenfuehren(teile: list[dict]) -> dict:
    """Führt die Ausgaben mehrerer Aufrufe eines Dokuments zusammen. Die Felder zum ganzen
    Dokument stammen aus dem Teil, der sie enthält (dem letzten Bereich)."""
    aus: dict = {"rollen": {}, "zitiert": [], "unsicher": [], "unlesbar": []}
    for t in teile:
        aus["rollen"].update(t["rollen"])
        for k in ("zitiert", "unsicher", "unlesbar"):
            aus[k] += [i for i in t.get(k, []) if i not in aus[k]]
        for k in FELDER_VOLL:
            if k not in FELDER_TEIL and k in t:
                aus[k] = t[k]
    return {k: aus[k] for k in FELDER_VOLL if k in aus}


def nach_ech(labels: dict) -> dict:
    """Abbildung der Lehrer-Labels auf eCH-0295-Werte: TextTypeEnum je Block (Blöcke ohne
    TextType fehlen), RecommendationEnum (über ECH_ABBILDUNG aus Iteration 2) und
    AffairTypeEnum. «zitiert» bleibt eine eigene Liste (Merkmal des Erweiterungsprofils)."""
    tt = {k: e.split(".", 1)[1] for k, _, _, _, e, _, _ in ROLLEN if e.startswith("TextTypeEnum.")}
    texte = {i: tt[r] for i, r in (labels.get("rollen") or {}).items() if r in tt}
    em = (labels.get("empfehlung") or {}).get("wert")
    typ = (labels.get("geschaeftstyp") or {}).get("wert")
    return {"text_type": texte, "zitiert": list(labels.get("zitiert") or []),
            "recommendation": EMPFEHLUNG_ECH.get(em, ("", "keine", ""))[0] or None,
            "affair_type": typ if typ in TYPEN and typ not in ("anderer", "nicht_erkennbar") else None}


def tabelle_rollen() -> list[list[str]]:
    """Rollenliste als Tabelle (für Dokumentation und Prüfung)."""
    return [[k, g, n, d, e, m, "ja" if z else "nein"] for k, g, n, d, e, m, z in ROLLEN]


if __name__ == "__main__":
    # uv run python src/m03_lehrer_vorgaben.py [--prompt <doc_id>]: Hashes bzw. ganzer Prompt
    if len(sys.argv) == 3 and sys.argv[1] == "--prompt":
        _dok = json.loads((Path(__file__).resolve().parents[1] / "daten/docling"
                           / f"{sys.argv[2]}.json").read_text(encoding="utf-8"))
        _b = bloecke_vorbereiten(_dok)
        _ids = [x["id"] for x in _b]
        for _m in nachrichten(dokument_rendern(_b), _ids, _ids):
            print(f"===== {_m['role']} =====\n{_m['content']}\n")
        sys.exit(0)
    print(f"{SCHEMA_VERSION}: {len(ROLLEN)} Rollen, davon zitierbar {len(ZITIERBAR)}, "
          f"mit TextTypeEnum-Ziel {sum(e.startswith('TextTypeEnum') for *_, e, _, _ in ROLLEN)}")
    print("Prompt-Hash standard:  ", prompt_hash("standard"))
    print("Prompt-Hash umgekehrt: ", prompt_hash("umgekehrt"))

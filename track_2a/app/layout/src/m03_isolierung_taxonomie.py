"""Iteration 3, Isolierung: Taxonomie, Ausgabeformat, Prüfung, Messgrössen und eCH-Richtext.

Frage: Lassen sich alle Elemente eines PDF sauber isolieren, bevor sie beschriftet werden?
Dieses Modul legt fest, WAS eine Einheit ist, und prüft Zerlegungen. Reines Definitionsmodul
ohne Netz und ohne Modell; Isolierer-Client (m03_isolierung_rauchtest.py), Referenz und
Auswertung importieren es. Begründung und Regeln: crisp-dm/03-data-preparation/isolierung-strategie.md.

Ebenen:
  Dokument  → ein PDF (FRBR-Work/Manifestation, eCH-0292 Kap. 07)
  Abschnitt → Ebene eCH-0295 TextBlock (SECTIONS, Abbildung auf I95 und K95)
  Einheit   → was beschriftet wird (UNIT_TYPES), geordnete Folge zusammenhängender Atome
  Atom      → Zeile eines Docling-Blocks mit Zeichenbereich (m03_atome.py, ID B12.3)

Schlüssel in Profil und Ausgabeformat englisch (eCH-Namenskonvention, snake_case), deutsche
Texte als Bezeichnungen. Isolierer-Ausgabe (keine Textausgabe durch das Modell):
  {"units": [{"id": "E1", "type": "question", "atoms": [{"from": "B9.1", "to": "B9.4"}],
              "section": "submitted_text", "refers_to": [], "number": ["1"], "quoted": true}, …],
   "atoms_with_boundary": [], "uncertain": []}

Aufruf (kein Netz, kein Modell, nur leichte Rechnungen):
  uv run python src/m03_isolierung_taxonomie.py --selbsttest
  uv run python src/m03_isolierung_taxonomie.py --kennzahlen        (alle Augenschein-Dokumente)
  uv run python src/m03_isolierung_taxonomie.py --tabellen          (Typen- und Abschnittstabellen, Markdown)
  uv run python src/m03_isolierung_taxonomie.py --zeige 117181      (Prompt im Terminal, enthält Namen)
  uv run python src/m03_isolierung_taxonomie.py --pruefe-datei PFAD DOC_ID   (Zerlegung + Richtext prüfen)
  uv run python src/m03_isolierung_taxonomie.py --basislinie DOC_ID REF_PFAD (Docling-Blöcke als Einheiten)
  uv run python src/m03_isolierung_taxonomie.py --prompt-hash [isolierung-v2.1]
  uv run python src/m03_isolierung_taxonomie.py --uebertragen      (Referenzen atome-v2 → atome-v3, Runde 2)

Fassungen (Runde 2, isolierung-runde2-2026-10-05.md): isolierung-v2 (Standard, Runde 1, unverändert) und
isolierung-v2.1 auf atome-v3. Taxonomie (Typen, Definitionen, Abschnitte, Regeln 1–11, Normalisierung,
Messgrössen) ist in beiden gleich. isolierung-v2.1 ändert nur:
  Prompt:     zusätzliche Grenzfälle (wiederholte Frage mit Marker vor der Antwort; Beschluss mit
              nummerierten Abschnitten) und ein zweites erfundenes Beispiel (Beschluss); Atome mit
              Legende atome-v3
  Prüfung:    Regel 7 (quoted ohne Antwort oder Beschluss im Dokument) ist Fehler statt Warnung;
              Warnung, wenn eine answer mit einem Atom mit Fragemarker («Frage n») beginnt
  Korrektur:  reparaturhinweise() je Fehlerart für die Korrekturschleife des Clients
Kandidatengrenzen: KANDIDAT_MERKMALE enthält die vier Merkmale aus atome-v3; auf atome-v2 ändert das
nichts (dort gibt es sie nicht).

Grundlagen: docling-test.md, lehrer-entwurf.md, pdf.md, crisp-dm/01-business-understanding/ech-weisungen.md (2, 3.3);
eCH-0292 Kap. 06/07; eCH-0295 input/schema.yaml (I95) und 02_LinkML_files/ech-0295_affairs.yaml
(K95, Kern v0.2.0), Stand Commit 3cab44d vom 30.09.2026.
"""

from __future__ import annotations

import csv
import hashlib
import html
import itertools
import json
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_atome as at

PROJEKT = Path(__file__).resolve().parents[1]
DOCLING = PROJEKT / "daten" / "docling"
ATOME = PROJEKT / "daten" / "isolierung" / "atome"
AUGENSCHEIN = PROJEKT / "daten" / "analyse" / "pdf" / "augenschein.csv"
ANALYSE = PROJEKT / "daten" / "analyse" / "isolierung"

SCHEMA_VERSION = "isolierung-v2"   # v1: deutsche Schlüssel, eigene Atome A1…An (abgelöst 04.10.2026)
SCHEMA_V21 = "isolierung-v2.1"     # Runde 2: Prompt und Prüfregeln (Taxonomie unverändert), atome-v3
SCHEMATA = (SCHEMA_VERSION, SCHEMA_V21)
ATOME_V3 = PROJEKT / "daten" / "isolierung" / "runde2" / "atome"
ATOME_ORDNER = {"atome-v2": ATOME, "atome-v3": ATOME_V3}
ATOME_ZU_SCHEMA = {SCHEMA_VERSION: "atome-v2", SCHEMA_V21: "atome-v3"}
ECH_STAND = "3cab44d (30.09.2026)"

# ================================================================ Abschnitte (eCH-0295 TextBlock)


@dataclass(frozen=True)
class Section:
    key: str
    label_de: str
    form: str                 # "plain" (Klartext, kein HTML) | "richtext" (eCH-0292 Kap. 06)
    i95_text_type: str | None  # input/schema.yaml, TextTypeEnum (7 Werte)
    i95_slot: str | None
    i95_match: str            # exact | close | none
    k95_text_type: str | None  # 02_LinkML_files/ech-0295_affairs.yaml, TextTypeEnum (5 Werte)
    k95_slot: str | None
    k95_match: str            # exact | close | merged | slot | none
    note: str = ""


SECTIONS: list[Section] = [
    Section("title", "Titel", "plain",
            "title", "Affair.title (TextBlock)", "exact",
            None, "Affair.title (MultilingualValue)", "slot",
            "K95: Titel ist ein Slot, kein TextBlock; Text ohne HTML."),
    Section("short_title", "Kurztitel", "plain",
            "short_title", "Affair.title (TextBlock)", "exact",
            None, None, "none",
            "K95 kennt keinen Kurztitel: Profil (Erweiterung)."),
    Section("submitted_text", "Eingereichter Text (Wortlaut)", "richtext",
            "submitted", "Submission.texts", "exact",
            "main_text", "SubmissionStep.texts", "exact",
            "Fragen und Forderungen sind Teile dieses Textes (Gliederung im Profil)."),
    Section("reasoning", "Begründung", "richtext",
            "reasoning", "Submission.texts", "exact",
            "reasoning", "SubmissionStep.texts", "exact"),
    Section("response", "Antwort der Exekutive", "richtext",
            "response", "ResponseStep.texts", "exact",
            "response", "ExecutiveResponseStep.texts", "exact",
            "Antwort-Frage-Bezüge im Profil (Kern kennt keine Teilantworten)."),
    Section("recommendation", "Antrag der Exekutive", "richtext",
            "recommendation", "ResponseStep.texts", "exact",
            "response", "ExecutiveResponseStep.texts", "merged",
            "Wert (RecommendationEnum) kommt aus der Beschriftung, nicht aus der Isolierung. K95: "
            "kein Texttyp, der Text geht in den response-TextBlock (in Lesereihenfolge)."),
    Section("summary", "Zusammenfassung", "richtext",
            "summary", "Submission.texts oder ResponseStep.texts (nach Verfasser)", "exact",
            None, None, "none", "K95: kein Texttyp, Profil."),
    Section("resolution", "Beschluss, Dispositiv", "richtext",
            None, None, "none", None, None, "none",
            "In keiner Fassung (ech.md Befund 11): Profil, Rückmeldung an die Fachgruppe."),
    Section("report", "Bericht, Botschaft", "richtext",
            None, None, "none", None, None, "none",
            "In keiner Fassung (Befund 11); Botschaften/Berichte erst in eCH-0296 V2 bzw. eCH-0297."),
    Section("note", "Verfahrensvermerk", "richtext",
            None, None, "none",
            "note", "ProcessStep.texts (Schritt, den der Vermerk betrifft)", "close",
            "K95 note = «Interne oder verfahrensbezogene Notiz»; die Werte (Datum, Entscheid) "
            "gehören trotzdem in die Schrittfelder."),
]
SECTION: dict[str, Section] = {s.key: s for s in SECTIONS}
SECTION_KEYS = list(SECTION)
ZUSAMMENLEGEN_K95 = {"recommendation": "response"}   # K95 hat keinen Texttyp recommendation
# eCH-Werte ohne Gegenstück in unseren Abschnitten (keine Einheit bildet darauf ab)
OHNE_GEGENSTUECK = {"k95": ["official_communication"], "i95": []}

# ================================================================ Einheitstypen

_F = frozenset
_KEIN = _F({None})
_INHALT = _F({None, "submitted_text", "reasoning", "response", "recommendation", "summary",
              "resolution", "report"})


@dataclass(frozen=True)
class UnitType:
    key: str
    group: str
    label_de: str
    definition: str                 # wie im Prompt
    edge_cases: tuple[str, ...]     # Grenzfälle mit Zellen aus pdf.md (Doku)
    section: str | None             # Standardabschnitt
    sections: frozenset             # erlaubte Abschnitte (None = kein Abschnitt)
    html: str                       # Element im eCH-Richtext
    quotable: bool = False          # quoted = true erlaubt
    numbered: bool = False          # number erlaubt
    relation: str | None = None     # Bedeutung von refers_to: answers | annotates
    targets: frozenset = _F()       # erlaubte Zieltypen von refers_to
    insert: bool = False            # Einschub: darf zwischen den Bereichen einer Einheit liegen
    core: bool = False              # Kerntyp: Grenzen verschieben Text zwischen eCH-TextBlocks
    teacher_role: str | None = None  # Rolle im Lehrer-Entwurf (lehrer-entwurf.md 1.1)
    evidence_for: str | None = None  # eCH-Feld, für das die Einheit Beleg ist


GROUPS = {"submission": "Vorstoss (von den Einreichenden verfasst)",
          "response": "Antwort und Beschluss (von der Exekutive verfasst)",
          "content": "Weitere Inhalte",
          "form": "Verfahren und Form (Belege, kein eCH-Text)"}

UNIT_TYPES: list[UnitType] = [
    # ---- Vorstoss
    UnitType(
        "title", "submission", "Titel",
        "Titel oder Betreff des Geschäfts, mit Typbezeichnung, Nummer, Datum, Feldname («betreffend», «Objet "
        ":», «Oggetto:») und Namen, wenn sie in denselben oder direkt anschliessenden Zeilen stehen; auch über "
        "mehrere Layout-Blöcke eine einzige Einheit. Nicht für Abschnittsüberschriften.",
        ("Typ, Nummer und Betreff im selben Block (K07, K09, G04): eine Einheit title",
         "Feldname und Betreff in zwei Rahmen (K01 «betreffend»): eine Einheit title",
         "Titel mit Einreichenden («Interpellation … betreffend …»): title, nicht sponsor_info",
         ("Typzeile mit Datum und Nummer und darunter der Betreff (S2 «Interrogazione … n. …» + Betreff): eine "
          "Einheit title"),
         "Beschlussnummer vor dem Titel im Protokollauszug (K02 «1334. Anfrage (…)»): title",
         "Dokumenttitel eines Berichts oder Erlassentwurfs (B2, B4): title",
         ("Titel endet mitten in der Zeile, danach beginnt der Einleitungssatz (G01 «…OIZ.Am 28.Oktober»): "
          "Atom in atoms_with_boundary")),
        "title", _F({"title"}), "Klartext ohne HTML", quotable=True, core=True,
        teacher_role="title", evidence_for="affair_type, affair_number (Typbezeichnung, Nummer)"),
    UnitType(
        "short_title", "submission", "Kurztitel",
        "Kurztitel oder Stichwort, das neben einem längeren Titel eigene Zeilen hat.",
        ("Stichwort in Klammern in derselben Zeile wie der Titel: Teil von title",),
        "short_title", _F({"short_title"}), "Klartext ohne HTML", quotable=True, core=True,
        teacher_role="short_title"),
    UnitType(
        "sponsor_info", "submission", "Angaben zur Urheberschaft",
        "Eigene Zeilen, die angeben, wer den Vorstoss einreicht oder mitunterzeichnet: «eingereicht von», "
        "Namensliste, Fraktion oder Partei, Zahl der Mitunterzeichnenden, Satz wie «X und Mitunterzeichnende "
        "haben am … folgende Anfrage eingereicht». Nicht: Titel mit Namen (title), Unterschriftsblock "
        "(signature), Adressblock eines Briefs (letter_element), Feld einer Metadatentabelle (metadata_field).",
        (("Einleitungssatz mit Namen und Datum im Protokollauszug (K02, G01): sponsor_info; Urheberschaft "
          "geht Verfahrensvermerk vor"),
         "Namensliste unter dem Titel (Mitunterzeichnende, 5 von 26 Dokumenten): sponsor_info",
         "nur Partei, keine Namen (L1): sponsor_info",
         "Ort, Datum und Name unter dem Vorstoss (K01, K10, G02, G03, L1): signature",
         "Feld «Eingereicht von:» mit Wert (K03, K04): metadata_field"),
        None, _KEIN, "– (Beleg, nicht im Richtext)", quotable=True,
        teacher_role="sponsor_info", evidence_for="Submission.sponsorship (I95), SubmissionStep.sponsorships (K95)"),
    UnitType(
        "submitted_text", "submission", "Eingereichter Text",
        "Text des Vorstosses, der weder Titel, Frage, Forderung noch Begründung ist: Einleitung, Sachverhalt "
        "vor den Fragen ohne eigene Überschrift, Überleitung zu den Fragen, ungegliederter Vorstoss. "
        "Zusammenhängende Absätze bilden eine Einheit.",
        ("Sachverhalt vor den Fragen ohne Überschrift (K02 zitiert): submitted_text",
         ("Einleitungssatz zur Liste der Fragen oder Forderungen («… um Beantwortung folgender Fragen:», «Der "
          "Regierungsrat wird beauftragt,» vor nummerierten Forderungen, K02, K03): submitted_text, nicht Teil "
          "der ersten Frage oder Forderung"),
         "Sachverhalt unter der Überschrift «Begründung»: reasoning",
         "ganzer Vorstoss als Fliesstext ohne Gliederung (G02, S3): eine Einheit submitted_text",
         "ganzer Vorstoss als ein Satz ohne Ziffern («Der Regierungsrat wird beauftragt, … zu …»): demand"),
        "submitted_text", _F({"submitted_text"}), "p; Listen ol/ul", quotable=True, core=True,
        teacher_role="submitted"),
    UnitType(
        "demand", "submission", "Auftrag oder Forderung",
        "Was der Vorstoss verlangt: Auftrag einer Motion, Prüfauftrag eines Postulats, Antrag einer "
        "parlamentarischen Initiative. Jede nummerierte oder als Listenpunkt abgesetzte Forderung ist eine "
        "eigene Einheit; eine ungegliederte Forderung ist eine Einheit.",
        ("nummerierte Forderungen, die wie Fragen aussehen (K03): demand, nicht question",
         ("«Der Regierungsrat wird beauftragt, 1. …; 2. …; 3. …» (K03): Einleitung submitted_text, je Ziffer eine "
          "Einheit demand, auch wenn alles ein Satz ist"),
         "Prüfpunkte eines Postulats in der Antwort zitiert (G05): demand mit quoted",
         "«… ist zu prüfen, ob …» in einer Motion: demand"),
        "submitted_text", _F({"submitted_text"}), "li in ol/ul, sonst p", quotable=True, numbered=True,
        core=True, teacher_role="demand"),
    UnitType(
        "question", "submission", "Frage",
        "Eine Frage des Vorstosses an die Exekutive, mit ihren Unterfragen. Jede nummerierte oder als "
        "Listenpunkt abgesetzte Frage ist eine eigene Einheit; Fragen in einem gemeinsamen Absatz ohne "
        "Nummer bilden eine Einheit. In einem Dokument der Exekutive wiederholt: quoted (zitierte Frage).",
        ("mehrere Fragezeichen in einem Listenpunkt (K05, K07, S3): eine Einheit",
         "Aufzählung ohne Nummern (K05, K06, G05): je Listenpunkt eine Einheit, number []",
         ("Zählung mit Neustart oder Kollision mit Kapitelnummern (B1, K09): gedruckte Nummer, keine "
          "Eindeutigkeit verlangt"),
         "Fragen vor jeder Antwort wiederholt (K09, K07, G04): quoted question vor jeder answer",
         "Einzelfrage ohne Nummer (S1): eine Einheit, number []",
         "rhetorische Frage in der Begründung: reasoning"),
        "submitted_text", _F({"submitted_text"}), "li in ol (fortlaufende Nummern) bzw. ul, sonst p",
        quotable=True, numbered=True, core=True, teacher_role="question"),
    UnitType(
        "reasoning", "submission", "Begründung",
        "Begründung oder Erläuterung der Einreichenden, meist nach «Begründung», «Développement», "
        "«Motivazione», «Motivaziun»; die Überschrift gehört dazu. Mehrere Absätze bilden eine Einheit.",
        ("Überschrift «Begründung» und Absätze (K03, K04, G06, L1): eine Einheit",
         "Sachverhalt vor den Fragen ohne Überschrift: submitted_text"),
        "reasoning", _F({"reasoning"}), "p; Überschrift am Anfang h4", quotable=True, core=True,
        teacher_role="reasoning"),
    # ---- Antwort und Beschluss
    UnitType(
        "response_intro", "response", "Einleitung der Antwort",
        "Vorbemerkung oder allgemeiner Teil der Exekutive vor den Antworten auf einzelne Fragen («Vorbemerkung», "
        "«Allgemeines», «Remarques préliminaires», «Considerazioni generali», «Der Regierungsrat beantwortet die "
        "Interpellation wie folgt:»). Nur, wenn danach Antworten auf einzelne Fragen folgen; zusammenhängende "
        "Absätze bilden eine Einheit.",
        ("Vorbemerkung vor den Antworten (K06, K07, K09 «1. Einleitung», G05): response_intro",
         ("Fliesstext-Antwort ohne Bezug auf einzelne Fragen (K04, K05, G05, S2): alles eine Einheit answer, "
          "auch der erste Absatz")),
        "response", _F({"response"}), "p; Überschrift am Anfang h4", core=True, teacher_role="response_intro"),
    UnitType(
        "answer", "response", "Antwort",
        "Antwort der Exekutive: je beantwortete Frage oder Fragengruppe eine Einheit, samt Marker («Zu Frage "
        "3:», «Ad 3», «Réponse à la question 3», «Tar la dumonda 3») und den Tabellen und Listen darin; oder "
        "die ganze zusammenhängende Stellungnahme ohne Bezug auf einzelne Fragen als eine Einheit (alle "
        "Absätze, über Seitenwechsel).",
        ("«Zu den Fragen 2 und 3:» (G01): eine Einheit, refers_to beide Fragen, number [\"2\", \"3\"]",
         "alle Antworten in einem Docling-Block (G01 B25, K08 B13): je Marker eine Einheit (Zeilenatome)",
         "nur Fragenummern, Fragen nicht im Dokument (K08): refers_to [], number gesetzt",
         "Frage vor der Antwort wiederholt (K09): refers_to die unmittelbar vorangehende Wiederholung",
         "Antragssatz in eigenen Zeilen am Schluss: recommendation"),
        "response", _F({"response"}), "p, Listen, table; Marker-Zeile allein h4", numbered=True,
        relation="answers", targets=_F({"question", "demand"}), core=True, teacher_role="response"),
    UnitType(
        "recommendation", "response", "Antragssatz der Exekutive",
        "Satz oder Absatz in eigenen Zeilen, in dem die Exekutive dem Parlament beantragt, den Vorstoss "
        "anzunehmen, abzulehnen, teilweise anzunehmen, in ein Postulat umzuwandeln oder abzuschreiben («Der "
        "Regierungsrat beantragt …», «Le Conseil d'État propose …», «Il Consiglio di Stato invita …»).",
        ("Schlusssatz «Der Stadtrat nimmt das Postulat teilweise entgegen.» (G05): recommendation",
         "Antrag je Ziffer einer Motion: refers_to die demand-Einheiten",
         "Begründung des Antrags («Fazit»-Absatz, G05): answer",
         "Antrag der Regierung in einer Botschaft («Wir beantragen Ihnen …», K11): recommendation",
         "Antragssatz mitten in einer Zeile: bleibt answer, Atom in atoms_with_boundary",
         "Kasten mit dem Ratsentscheid (G05): procedural_note"),
        "recommendation", _F({"recommendation"}), "p", numbered=True, relation="answers",
        targets=_F({"question", "demand"}), core=True, teacher_role="recommendation",
        evidence_for="ResponseStep.recommendation (I95), ExecutiveResponseStep.recommendation (K95)"),
    UnitType(
        "resolution", "response", "Beschluss",
        "Beschlussformel samt Einleitung («Auf Antrag der … beschliesst der Regierungsrat:», «arrête :», "
        "«risolve:»), Dispositiv, Beschlussziffer («I. … II. …»), Erlasstext oder Beschlussentwurf einer Vorlage. "
        "Die Formel gehört zur ersten Ziffer; jede weitere Ziffer mit eigenem Inhalt ist eine Einheit.",
        (("«Auf Antrag … beschliesst der Regierungsrat: I. Die Anfrage … wird wie folgt beantwortet:» (K02): "
          "resolution, number [\"I\"]"),
         "Ziffer, die nur Empfänger nennt («II. Mitteilung an …», K02): distribution, nicht resolution",
         ("Artikel eines Erlassentwurfs (B4), Beschlussziffern einer Botschaft (K11), Regierungsratsbeschluss "
          "(S5): resolution")),
        "resolution", _F({"resolution"}), "p; Ziffern als ol", numbered=True, teacher_role="resolution"),
    # ---- weitere Inhalte
    UnitType(
        "summary", "content", "Zusammenfassung",
        "Zusammenfassung, Résumé, Kurzbeschrieb des Geschäfts mit eigener Überschrift oder eigenem Kasten.",
        ("Abschnitt «Résumé» eines Berichts (B2): summary",),
        "summary", _F({"summary"}), "p", core=True, teacher_role="summary"),
    UnitType(
        "report", "content", "Bericht oder Botschaft",
        "Erläuternder Text einer Vorlage, einer Botschaft oder eines Berichts der Exekutive, der keine "
        "Antwort auf einen Vorstoss ist; je Kapitelabschnitt (Überschrift bis zur nächsten) eine Einheit.",
        ("Kapiteltext eines erläuternden Berichts (B2) oder einer Botschaft (K11): report",
         "Begleitschreiben einer Vernehmlassung (B1): report"),
        "report", _F({"report"}), "p, Listen, table", teacher_role="report"),
    UnitType(
        "table", "content", "Tabelle",
        "Eigenständige Tabelle, die keinem anderen Teil zugehört. Gehört eine Tabelle zu einer Antwort, "
        "Forderung, Begründung oder einem Berichtsabschnitt, ist sie Teil dieser Einheit.",
        ("Finanztabellen einer Botschaft (K11), Betragstabelle (S5): table",
         "Metadatentabelle (K03, K04): je Feld metadata_field",
         "Briefkopf, den Docling als Tabelle liest (S2): letter_element"),
        None, _INHALT, "table/thead/tbody/tr/td", teacher_role="table"),
    UnitType(
        "heading", "content", "Zwischenüberschrift",
        "Gliederungsüberschrift, die mehrere Einheiten oder einen Dokumentteil einleitet («Antwort des "
        "Regierungsrates», «Zu den einzelnen Fragen», Kapitelüberschrift). Leitet sie genau eine Einheit ein "
        "(«Begründung», «Zu Frage 3»), gehört sie zu dieser Einheit.",
        ("«Zu Frage 1:» als eigene Zeile vor genau einer Antwort (K02): Teil der answer",
         "Kapitel «2. Zu den einzelnen Fragen» (K09): heading, section response",
         "Kapitelüberschrift im Bericht (B2, K11): heading, section report",
         ("Dokumentart am Kopf («Parlamentarischer Vorstoss» K03, «Auszug aus dem Protokoll» K02, «Stellungnahme "
          "zum» G05): letter_element, nicht heading")),
        None, _INHALT, "h3 (in Berichten h2–h4 nach Gliederungstiefe)", teacher_role="heading"),
    UnitType(
        "attachment", "content", "Anhang",
        "Anhang, Beilage, Beilagenverzeichnis, Verweis auf separate Unterlagen, Unterschriftenliste.",
        ("gedrehte Unterschriftenliste (S1): attachment",
         "Verweis auf separate Beilagen (B1, K11): attachment"),
        None, _KEIN, "– (separate Datei: TextBlock.document_url)", teacher_role="attachment"),
    UnitType(
        "footnote", "content", "Fussnote",
        "Fussnote oder Anmerkung am Seitenende. refers_to: die Einheit mit dem Fussnotenzeichen, wenn klar.",
        ("Fussnoten eines Berichts (B2, B4, K11): footnote mit dem Abschnitt der verweisenden Einheit",),
        None, _INHALT, "p am Ende des TextBlocks", relation="annotates", insert=True, teacher_role="other"),
    # ---- Verfahren und Form
    UnitType(
        "metadata_field", "form", "Metadatenfeld",
        "Ein Feld im Kopf, Kasten, Deckblatt oder in einer Metadatentabelle, Schlüssel und Wert zusammen "
        "(«Vorstoss-Nr.: …», «KR-Nr. …», «Sitzung vom …», «Eingereicht am: …», Geschäftsnummer allein). Jedes "
        "Feld ist eine Einheit; stehen Schlüssel und Wert im Schlüssel-Wert-Bereich nicht nebeneinander, hat "
        "die Einheit zwei Bereiche.",
        ("Metadatentabelle (K03, K04): je Schlüssel-Wert-Paar eine Einheit; Docling-Reihenfolge K, K, W, W",
         "Kasten oder Kopf mit Geschäftsnummer und Datum (16 von 26 Dokumenten): je Feld eine Einheit",
         "dreisprachiger Kopf (K08): je Feld eine Einheit",
         "vorgedrucktes Formularfeld (G06): metadata_field",
         "wiederkehrende Kopfzeile mit Nummer: header_footer"),
        None, _KEIN, "–", teacher_role="metadata",
        evidence_for="affair_number, affair_type, Daten, Zuständigkeit"),
    UnitType(
        "procedural_note", "form", "Verfahrensvermerk",
        "Vermerk über einen Verfahrensschritt: Eingang (Stempel), Überweisung, Zustellung, Traktandierung, "
        "Frist, Ratsentscheid, Regierungsratsbeschluss mit Datum, Aufwand für die Antwort.",
        (("Eingangsstempel (S1), Ratsentscheid im Kasten (G05), Zustellvermerk am Seitenfuss (K09), Aufwand in "
          "Stunden (K07, S2): procedural_note"),
         "«(Eingereicht vor der Grossratssitzung vom …)» (K09): procedural_note"),
        "note", _F({"note"}), "p (TextBlock note, nur K95)", teacher_role="procedural_note",
        evidence_for="Schritte und Daten (SubmissionStep, PlenaryDebateStep …)"),
    UnitType(
        "signature", "form", "Unterschrift",
        "Unterschriftsblock als eine Einheit: Grussformel direkt davor, Ort und Datum, «Für den Regierungsrat», "
        "Funktionen, Namen, Unterschriftsbilder dazwischen. Ort und Datum allein unter einem Vorstoss ebenfalls. "
        "Im zitierten Vorstoss: quoted.",
        ("eingefügtes Unterschriftsbild (K07, K08, K09) und Handschrift (B1, G03, G06, S1, S2)",
         "nur Behördenname (K11, G05): signature",
         ("Grussformel, «Per il Consiglio di Stato», Präsident, Kanzler mit Namen und Bildern dazwischen (S2): "
          "eine Einheit signature (Bilder ohne Text dazwischen als picture-Einschub zulässig)"),
         "Name am Ende des zitierten Vorstosses (K09 «… Name»»): signature, quoted"),
        None, _KEIN, "–", quotable=True, teacher_role="signature",
        evidence_for="Submission.sponsorship bzw. ResponseStep.responder, Daten"),
    UnitType(
        "distribution", "form", "Verteiler",
        "Verteiler, «Mitteilung an», «Kopie an», «Copia:», Empfänger eines Protokollauszugs; Einleitung und alle "
        "Empfänger zusammen sind eine Einheit.",
        ("Ziffer «II. Mitteilung an …» im Protokollauszug (K02): distribution",
         "«Copia:» und eine Liste von Stellen (S2): eine Einheit distribution"),
        None, _KEIN, "–", teacher_role="distribution"),
    UnitType(
        "letter_element", "form", "Brief- und Dokumentkopf",
        "Dokument- oder Briefkopf mit Behörde und Dokumentart («Auszug aus dem Protokoll des Regierungsrates», "
        "«Parlamentarischer Vorstoss», «Stellungnahme zum»), Adress- und Absenderblock, Anrede, Behördenname im "
        "Wappen. Ein Adressblock ist eine Einheit. Die Grussformel vor einer Unterschrift gehört zu signature.",
        ("Adressblock an das Ratsmitglied (K07, G04, S2): letter_element",
         "Wappen mit Behördenname als Text im Bild (K03, G05): letter_element",
         "Briefkopf, den Docling als Tabelle liest (S2): letter_element"),
        None, _KEIN, "–", teacher_role="letter", evidence_for="ResponseStep.responder"),
    UnitType(
        "header_footer", "form", "Kopf- oder Fusszeile",
        "Wiederkehrende Kopf- oder Fusszeile, Seitenzahl, Dateiname, Ablagepfad oder Vorlagenrest am "
        "Seitenrand; auch mit Geschäftsnummer oder Datum. Je Seite und Stelle eine Einheit.",
        ("Nummern und Daten im Kopf oder Fuss (K04, K05, K07, K10, G01, S3): header_footer, als Beleg nutzbar",
         "Vorlagenrest in der Fusszeile (B2, B4, K10, S5): header_footer",
         "einmaliger Zustellvermerk am Seitenfuss (K09): procedural_note"),
        None, _KEIN, "– (markiert, nicht gelöscht)", insert=True, teacher_role="header_footer"),
    UnitType(
        "picture", "form", "Bild",
        "Bild ohne verwertbaren Text (Atom «ohne Text»): Logo, Wappen, Siegel, Zierelement.",
        ("Unterschriftsbild: signature; Stempel mit Datum: procedural_note; Text im Wappen: letter_element",),
        None, _KEIN, "– (kein img, Bild bleibt im PDF)", insert=True, teacher_role="other"),
    UnitType(
        "other", "form", "Sonstiges",
        "Alles andere: Inhaltsverzeichnis, Vorlagenrest oder Platzhalter im Text, Bildlegende ohne Zuordnung, "
        "Zeichenmüll aus der Texterkennung.",
        ("Platzhalter für Nummer, Siegel, QR-Code (B2, B4): other",
         "Handschrift als Zeichenmüll (G06, S1): other",
         "Inhaltsverzeichnis (B2): other"),
        None, _KEIN, "–", teacher_role="other"),
]

TYPES: dict[str, UnitType] = {t.key: t for t in UNIT_TYPES}
TYPE_KEYS = list(TYPES)
QUOTABLE = {t.key for t in UNIT_TYPES if t.quotable}
NUMBERED = {t.key for t in UNIT_TYPES if t.numbered}
INSERT_TYPES = {t.key for t in UNIT_TYPES if t.insert}
CORE_TYPES = {t.key for t in UNIT_TYPES if t.core}
QUESTION_TYPES = {"question", "demand"}
VORSTOSS_TEXT = {"submitted_text", "demand", "question", "reasoning"}   # im Antwortdokument quoted
UNIT_FIELDS = ("id", "type", "atoms", "section", "refers_to", "number", "quoted")
OUTPUT_FIELDS = ("units", "atoms_with_boundary", "uncertain")
RX_UNIT = re.compile(r"^E[1-9]\d*$")
RX_UNIT_EXTERN = re.compile(r"^[0-9A-Za-z_-]+#E[1-9]\d*$")   # quoted → Original in anderem Dokument
RX_NUMBER = re.compile(r"^(?:\d{1,3}[a-z]?(?:\.\d{1,3}){0,3}|[IVXLC]{1,6}|[a-z])$")
KV_ELTERN = {"key_value_area", "form_area"}

# Lehrer-Rollen (lehrer-entwurf.md) → Einheitstyp; zwei Rollen werden je nach Form zwei Typen
LEHRER_ZU_TYP = {t.teacher_role: t.key for t in UNIT_TYPES if t.teacher_role and t.teacher_role != "other"}
LEHRER_ZU_TYP["other"] = "other"   # Fussnote und Bild ohne Text sind im Lehrer-Entwurf «other»

# ================================================================ Atome laden


def lade(doc_id: str | int) -> dict:
    return json.loads((DOCLING / f"{doc_id}.json").read_text(encoding="utf-8"))


def _sha256(pfad: Path) -> str:
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def atome_datei(doc_id: str | int, atome: str = "atome-v2") -> dict:
    """Ganze Atom-Datei daten/isolierung/atome/<doc_id>.json (m03_atome.py; atome-v3:
    daten/isolierung/runde2/atome/), geprüft gegen die aktuelle Docling-Datei (quelle_sha256) und die
    Fassung. Fehlt sie oder ist sie veraltet, bricht das Laden ab: Atom-IDs sind die Bezugspunkte von
    Referenzen und Ausgaben und dürfen nicht still wechseln."""
    pfad = ATOME_ORDNER[atome] / f"{doc_id}.json"
    if not pfad.exists():
        raise FileNotFoundError(f"{pfad} fehlt: uv run python src/m03_atome.py --fassung {atome} {doc_id}")
    roh = json.loads(pfad.read_text(encoding="utf-8"))
    if roh.get("quelle_sha256") != _sha256(DOCLING / f"{doc_id}.json"):
        raise ValueError(f"{pfad} gehört nicht zur aktuellen Docling-Datei: m03_atome.py neu laufen lassen")
    if roh.get("version") != atome:
        raise ValueError(f"{pfad} hat Fassung {roh.get('version')!r}, erwartet {atome!r}")
    return roh


def atome_fingerabdruck(liste: list[dict]) -> str:
    """SHA-256 über (ID, Zeichenbereich) aller Atome: gleich, solange dieselben Atome gelten,
    unabhängig vom Zeitpunkt der Erzeugung. Referenzen und Ausgaben tragen ihn mit."""
    roh = json.dumps([[a["id"], a["zeichen"]] for a in liste], separators=(",", ":"))
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def atome_kopf(doc_id: str | int, atome: str = "atome-v2") -> dict:
    """Herkunft der Atome für Protokolle: Version, Erzeugung, Prüfsummen, Fingerabdruck."""
    roh = atome_datei(doc_id, atome)
    kopf = {k: roh.get(k) for k in ("version", "erzeugt_utc", "quelle_sha256", "docling_lauf")}
    return kopf | {"fingerabdruck": atome_fingerabdruck(roh["atome"])}


def atome_passen(datei_inhalt: dict, liste: list[dict]) -> str | None:
    """Warnung, wenn eine Referenz oder Ausgabe auf anderen Atomen beruht als den aktuellen."""
    kopf = datei_inhalt.get("_atome") or datei_inhalt.get("atome_kopf") or {}
    fp = kopf.get("fingerabdruck")
    if fp and fp != atome_fingerabdruck(liste):
        return (f"Atome geändert seit Erstellung (Version {kopf.get('version')}, {kopf.get('erzeugt_utc')}): "
                "IDs prüfen, Referenz gegebenenfalls übertragen")
    return None


def atome_laden(doc_id: str | int, dok: dict | None = None, atome: str = "atome-v2") -> list[dict]:
    """Atome in Lesereihenfolge (m03_atome.py, Fassung atome). Ergänzt je Atom eltern_ref
    (Schlüssel-Wert-Bereich) und ocr aus dem Docling-Block und prüft den Wortlaut gegen text_gesamt."""
    dok = dok or lade(doc_id)
    if dok.get("status") != "success":
        raise ValueError(f"Docling-Status {dok.get('status')!r}, Dokument {doc_id}")
    liste = atome_datei(doc_id, atome)["atome"]
    bloecke = {b["id"]: b for b in dok["bloecke"]}
    g = dok["text_gesamt"]
    for a in liste:
        b = bloecke[a["block"]]
        a["eltern_ref"] = (b.get("eltern") or {}).get("ref")
        a["ocr"] = (b.get("ocr_anteil") or 0) >= 0.5
        a.setdefault("hinweise", [])
        assert g[a["zeichen"][0]:a["zeichen"][1]] == a["text"], (doc_id, a["id"])
    return liste


# Merkmale der Atome (m03_atome.py: englische Schlüssel in «merkmale», atome-v1 nur deutsche «hinweise»)
_HINWEIS_V1 = {"page_break_back": "Seitenwechsel zurück", "thirds_rule_violated": "Drittel-Regel verletzt",
               "answer_reference": "Bezug Frage", "marker_inside": "Marker im Atom", "above_previous": "über Vorgänger",
               "column_part": "Spaltenteil", "sentence_part": "Satzteil"}


def hat_merkmal(a: dict, schluessel: str) -> bool:
    if "merkmale" in a:
        return any(k == schluessel for k, _ in a["merkmale"])
    return any(h.startswith(_HINWEIS_V1.get(schluessel, "\0")) for h in a.get("hinweise", []))


def eingabe_rendern(liste: list[dict], atome: str = "atome-v2") -> str:
    """Prompt-Form der Atome aus m03_atome.py (eine Zeile je Atom: ID | Seite | Hinweise | Text),
    Legende der Atom-Fassung."""
    return at.prompt_text(liste, mit_legende=True, fassung=atome)


# ================================================================ Prompt für den Isolierer

SYSTEM = ("Du zerlegst Dokumente aus Schweizer Parlamenten (Deutsch, Französisch, Italienisch, "
          "Rätoromanisch) in Einheiten. Du schreibst keinen Text ab und erfindest nichts. Du antwortest "
          "nur mit einem JSON-Objekt aus Typ-Schlüsseln, Atom-IDs, Einheiten-IDs und Werten aus "
          "vorgegebenen Listen.")

EINLEITUNG = """\
Aufgabe: Zerlege das Dokument unten vollständig in Einheiten. Jede Zeile des Dokuments ist ein Atom: ID (B12.3 = Layout-Block 12, Zeile 3), Seite, Hinweise, Text. Die Hinweise (Form aus dem Layout, mögliche Marker, Schlüssel-Wert-Kandidaten) sind nur Hinweise. Eine Einheit ist eine zusammenhängende Folge von Atomen mit einer Funktion im Verfahren, zum Beispiel eine Frage, die Antwort auf eine Frage, die Begründung, ein Metadatenfeld oder eine Kopfzeile. Du bestimmst nur Grenzen, Typ, Abschnitt, Bezüge, Nummern und das Merkmal quoted; den Inhalt beschriftet ein späterer Schritt."""

REGELN = """\
1. Vollständig: Jedes Atom gehört zu genau einer Einheit, ohne Lücke und ohne Überlappung, auch Kopf- und Fusszeilen, Bilder ohne Text und Zeichenmüll. IDs E1, E2 … in der Reihenfolge des ersten Atoms.
2. Grenzen: Eine neue Einheit beginnt, wenn die Funktion wechselt oder eine neue Instanz derselben Funktion beginnt (nächste Frage, nächste Antwort, nächstes Feld, nächste Ziffer, nächste Kopfzeile). Mehrere Absätze und Zeilen mit derselben Funktion bilden eine Einheit, besonders: der ganze Titel, ein Adressblock, die ganze Begründung, eine Antwort im Fliesstext, ein Unterschriftsblock, ein Verteiler. Massgebend ist die Funktion, nicht die Form: Layout-Blöcke (B-Nummer) dürfen geteilt und zusammengefasst werden.
3. Bereiche: atoms ist eine Liste von Bereichen {"from", "to"} (einschliesslich, in Dokumentreihenfolge), meist genau einer. Mehrere Bereiche nur, wenn dazwischen ausschliesslich Kopf- und Fusszeilen, Fussnoten oder Bilder ohne Text liegen (Seitenwechsel), Zeilen eines Blocks mit dem Hinweis «Drittel-Regel verletzt» (falsch eingeordneter Block, z. B. ein Adressblock zwischen zwei Seiten einer Antwort), oder bei metadata_field im selben Schlüssel-Wert-Bereich (Hinweis «Feld»), wenn Schlüssel und Wert nicht nebeneinander stehen (Hinweise «Schlüssel→» und «Wert←»). Liegt anderes dazwischen, bilde zwei Einheiten desselben Typs (bei answer mit denselben refers_to).
4. Überschriften: Leitet eine Überschrift genau eine Einheit ein («Begründung», «Zu Frage 3:»), gehört sie zu dieser Einheit. Leitet sie mehrere Einheiten oder einen Dokumentteil ein («Antwort des Regierungsrates», «2. Zu den einzelnen Fragen»), ist sie eine Einheit heading mit dem Abschnitt des eingeleiteten Teils. Tabellen und Listen, die zu einer Antwort, Forderung, Begründung oder einem Berichtsabschnitt gehören, sind Teil dieser Einheit.
5. Fragen und Forderungen: Jede nummerierte oder als Listenpunkt abgesetzte Frage oder Forderung ist eine eigene Einheit, mit ihren Unterfragen. number = gedruckte Nummer ohne Punkt und Klammer (["3"], ["2a"], ["II"]), sonst [].
6. Antworten: Je beantwortete Frage oder Fragengruppe eine Einheit answer. refers_to = IDs der beantworteten question- oder demand-Einheiten in diesem Dokument (quoted oder nicht); wird die Frage direkt vor ihrer Antwort wiederholt, die unmittelbar vorangehende Wiederholung. Ordne nach Inhalt und Reihenfolge zu, nicht nur nach der gedruckten Nummer. number = gedruckte Fragenummern (["2", "3"]). Steht die Frage nicht im Dokument: refers_to [] und number gesetzt. Antwort im Fliesstext ohne Bezug auf einzelne Fragen: eine Einheit answer mit refers_to [] und number [].
7. quoted = true für jede Einheit des wiedergegebenen Vorstosses in einem Dokument der Exekutive (Protokollauszug, Antwortbrief, Formular mit Antwortteil), mit oder ohne Anführungszeichen: Wortlaut, Fragen, auch vor jeder Antwort wiederholte Fragen, Forderungen, Begründung, Urheberschaft und Unterschrift innerhalb des wiedergegebenen Textes. Nicht quoted sind Titel, Betreff und Einleitungssatz («X hat am … folgende Anfrage eingereicht:»), mit denen die Exekutive ihr eigenes Dokument einleitet. In einem eingereichten Vorstoss ist nichts quoted.
8. section: der Abschnitt aus der Typenliste. Bei table, heading und footnote der Abschnitt der Einheiten, zu denen sie gehören, sonst null.
9. Kopf- und Fusszeilen nie weglassen: je Seite und Stelle eine Einheit header_footer, auch wenn sie Nummern oder Daten tragen. Ein einmaliger Vermerk am Seitenrand (Zustellung, Eingang) ist procedural_note.
10. Liegt in einem Atom eine Grenze (zwei Funktionen in derselben Zeile, z. B. Titel endet und der Einleitungssatz beginnt in derselben Zeile), ordne das Atom der Einheit zu, in der es beginnt, beginne mit dem nächsten Atom die neue Einheit und nenne das Atom in atoms_with_boundary.
11. uncertain: IDs der Einheiten, deren Grenzen oder Typ du nicht sicher bestimmen kannst. Rate nicht; Zeichenmüll aus der Texterkennung ist other."""

AUSGABE = """\
Antworte nur mit diesem JSON-Objekt:
{"units": [{"id": "E1", "type": "<Typ>", "atoms": [{"from": "<Atom-ID>", "to": "<Atom-ID>"}], "section": <Abschnitt oder null>, "refers_to": [], "number": [], "quoted": false}, …], "atoms_with_boundary": [], "uncertain": []}
- refers_to: nur bei answer und recommendation (beantwortete question/demand) und bei footnote (Einheit mit dem Fussnotenzeichen), sonst [].
- number: nur bei Typen mit «number», sonst [].
- Keine Texte, keine Erklärungen."""

BEISPIEL_EINGABE = """\
ID | Seite | Hinweise | Text
B1.1 | 1 | Kopfzeile | Gemeinde Musterhausen · Gemeinderat
B2.1 | 1 | Überschrift | Interpellation ‹Name› betreffend Velowege
B3.1 | 1 |  | Am ‹Datum› hat ‹Name› folgende Interpellation eingereicht:
B4.1 | 1 |  | «Der Gemeinderat wird gebeten, folgende Fragen zu beantworten:
B5.1 | 1 | Listenpunkt, Aufzählung 1. | 1. Wie viele Kilometer Velowege gibt es?
B6.1 | 1 | Listenpunkt, Aufzählung 2. | 2. Welche Lücken will der Gemeinderat bis 2030
B6.2 | 1 | Listenpunkt | schliessen?»
B7.1 | 1 | Überschrift, Stichwort Antwort | Antwort des Gemeinderates
B8.1 | 1 | Bezug Frage 1 | Zu Frage 1: Es gibt 14 Kilometer. Davon sind 9 Kilometer
B8.2 | 1 |  | getrennt geführt.
B9.1 | 1 | Fusszeile | Seite 1
B10.1 | 2 | Kopfzeile, Seitenwechsel | Gemeinde Musterhausen · Gemeinderat
B11.1 | 2 |  | Die übrigen 5 Kilometer sind Radstreifen.
B12.1 | 2 | Bezug Frage 2 | Zu Frage 2: Die Planung liegt im Anhang.
B13.1 | 2 | Ort und Datum | Musterhausen, ‹Datum›
B13.2 | 2 | Unterschriftsformel | Im Namen des Gemeinderates"""

BEISPIEL_AUSGABE = """\
{"units": [
 {"id": "E1", "type": "header_footer", "atoms": [{"from": "B1.1", "to": "B1.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E2", "type": "title", "atoms": [{"from": "B2.1", "to": "B2.1"}], "section": "title", "refers_to": [], "number": [], "quoted": false},
 {"id": "E3", "type": "sponsor_info", "atoms": [{"from": "B3.1", "to": "B3.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E4", "type": "submitted_text", "atoms": [{"from": "B4.1", "to": "B4.1"}], "section": "submitted_text", "refers_to": [], "number": [], "quoted": true},
 {"id": "E5", "type": "question", "atoms": [{"from": "B5.1", "to": "B5.1"}], "section": "submitted_text", "refers_to": [], "number": ["1"], "quoted": true},
 {"id": "E6", "type": "question", "atoms": [{"from": "B6.1", "to": "B6.2"}], "section": "submitted_text", "refers_to": [], "number": ["2"], "quoted": true},
 {"id": "E7", "type": "heading", "atoms": [{"from": "B7.1", "to": "B7.1"}], "section": "response", "refers_to": [], "number": [], "quoted": false},
 {"id": "E8", "type": "answer", "atoms": [{"from": "B8.1", "to": "B8.2"}, {"from": "B11.1", "to": "B11.1"}], "section": "response", "refers_to": ["E5"], "number": ["1"], "quoted": false},
 {"id": "E9", "type": "header_footer", "atoms": [{"from": "B9.1", "to": "B9.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E10", "type": "header_footer", "atoms": [{"from": "B10.1", "to": "B10.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E11", "type": "answer", "atoms": [{"from": "B12.1", "to": "B12.1"}], "section": "response", "refers_to": ["E6"], "number": ["2"], "quoted": false},
 {"id": "E12", "type": "signature", "atoms": [{"from": "B13.1", "to": "B13.2"}], "section": null, "refers_to": [], "number": [], "quoted": false}],
 "atoms_with_boundary": [], "uncertain": []}"""


RX_ZELLEN = re.compile(r"\s*\((?:[BKGSL]\d{1,2}[^()]*?)\)|\s*\b[BKGSL]\d{1,2}\b(?:\s+B\d+(?:\.\d+)*)?")


def grenzfall_prompt(text: str) -> str:
    """Grenzfall ohne Zellen-Kürzel (K02, G01 …) und Block-IDs: der Prompt bleibt allgemein."""
    t = RX_ZELLEN.sub("", text)
    for _ in range(2):
        t = re.sub(r"\(\s+", "(", t)
        t = re.sub(r",\s*(?=[,)])", "", t)
        t = re.sub(r"\(\s*\)", "", t)
        t = re.sub(r"\s+([:,;)])", r"\1", t)
    return t.strip()


# isolierung-v2.1 (Runde 2, isolierung-test-2026-10-05.md 8.3 Punkte 1 und 3): zusätzliche Grenzfälle im
# Prompt, angehängt an die Grenzfälle des Typs. Definitionen und Regeln bleiben unverändert.
GRENZFAELLE_V21: dict[str, tuple[str, ...]] = {
    "question": (("Frage vor ihrer Antwort wiederholt, auch mit vorangestelltem Marker («Question 1 :», «Domanda "
                  "1», «Frage 1:») oder als nummerierter Listenpunkt (K06, K09): eigene Einheit question mit "
                  "quoted und der gedruckten Nummer; die answer beginnt erst mit der Zeile nach der wiederholten "
                  "Frage"),),
    "answer": (("Zeile mit Hinweis «Frage n» oder wiederholter Fragetext direkt vor der Antwort (K06, K09): nicht "
                "Teil der answer, sondern eigene Einheit question mit quoted; refers_to der answer zeigt auf sie"),),
    "resolution": (("Beschluss der Exekutive mit nummerierten Abschnitten («1 Gegenstand», «2 Rechtsgrundlagen» … "
                    "jeweils mit Text, S5): je Abschnitt eine Einheit resolution samt Abschnittsüberschrift, number "
                    "[\"1\"], [\"2\"] …; nicht report (siehe Beispiel 2)"),),
}

BEISPIEL2_EINGABE = """\
ID | Seite | Hinweise | Text
B1.1 | 1 | Überschrift | Auszug aus dem Protokoll des Regierungsrates
B2.1 | 1 | Feld | Sitzung vom ‹Datum›
B3.1 | 1 | Überschrift | 512. Beitrag an die Sanierung der Kantonsstrasse ‹Ort›
B4.1 | 1 | Überschrift | 1 GEGENSTAND
B5.1 | 1 |  | Mit diesem Beschluss wird ein Beitrag an die Sanierung
B5.2 | 1 |  | der Kantonsstrasse bewilligt.
B6.1 | 1 | Überschrift | 2 BESCHLUSS
B7.1 | 1 | Listenpunkt, Aufzählung - | - Der Beitrag beträgt höchstens ‹Betrag› Franken.
B8.1 | 1 | Listenpunkt, Aufzählung - | - Die Direktion vollzieht diesen Beschluss.
B9.1 | 1 | Fusszeile, Seitenzahl | Seite 1
B10.1 | 2 | Seitenwechsel, Verteiler | Mitteilung an die Direktion ‹Name›"""

BEISPIEL2_AUSGABE = """\
{"units": [
 {"id": "E1", "type": "letter_element", "atoms": [{"from": "B1.1", "to": "B1.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E2", "type": "metadata_field", "atoms": [{"from": "B2.1", "to": "B2.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E3", "type": "title", "atoms": [{"from": "B3.1", "to": "B3.1"}], "section": "title", "refers_to": [], "number": [], "quoted": false},
 {"id": "E4", "type": "resolution", "atoms": [{"from": "B4.1", "to": "B5.2"}], "section": "resolution", "refers_to": [], "number": ["1"], "quoted": false},
 {"id": "E5", "type": "resolution", "atoms": [{"from": "B6.1", "to": "B8.1"}], "section": "resolution", "refers_to": [], "number": ["2"], "quoted": false},
 {"id": "E6", "type": "header_footer", "atoms": [{"from": "B9.1", "to": "B9.1"}], "section": null, "refers_to": [], "number": [], "quoted": false},
 {"id": "E7", "type": "distribution", "atoms": [{"from": "B10.1", "to": "B10.1"}], "section": null, "refers_to": [], "number": [], "quoted": false}],
 "atoms_with_boundary": [], "uncertain": []}"""


def typenliste(schema: str = SCHEMA_VERSION) -> str:
    zeilen = []
    for g, titel in GROUPS.items():
        zeilen.append(f"{titel}:")
        for t in UNIT_TYPES:
            if t.group != g:
                continue
            ab = t.section if t.section else ("wie der zugehörige Teil oder null" if len(t.sections) > 1
                                              else "null")
            merk = [f"section {ab}"]
            if t.quotable:
                merk.append("quoted erlaubt")
            if t.numbered:
                merk.append("number")
            zeilen.append(f"- {t.key} ({t.label_de}; {', '.join(merk)}): {t.definition}")
            faelle = t.edge_cases + (GRENZFAELLE_V21.get(t.key, ()) if schema == SCHEMA_V21 else ())
            if faelle:
                zeilen.append("  Grenzfälle: " + "; ".join(grenzfall_prompt(x) for x in faelle) + ".")
    return "\n".join(zeilen)


def abschnittsliste() -> str:
    return ("Abschnitte (section; Ebene eCH-0295 TextBlock): "
            + ", ".join(f"{s.key} ({s.label_de})" for s in SECTIONS) + "; null = kein Abschnitt.")


def anleitung(schema: str = SCHEMA_VERSION) -> str:
    if schema == SCHEMA_V21:
        return (f"{EINLEITUNG}\n\nTypen:\n{typenliste(schema)}\n\n{abschnittsliste()}\n\nRegeln:\n{REGELN}\n\n"
                f"{AUSGABE}\n\nBeispiel 1 (erfunden, Antwort der Exekutive mit zitierter Interpellation).\n"
                f"Eingabe:\n{BEISPIEL_EINGABE}\nAusgabe:\n{BEISPIEL_AUSGABE}\n\n"
                f"Beispiel 2 (erfunden, Beschluss der Exekutive mit nummerierten Abschnitten).\n"
                f"Eingabe:\n{BEISPIEL2_EINGABE}\nAusgabe:\n{BEISPIEL2_AUSGABE}")
    return (f"{EINLEITUNG}\n\nTypen:\n{typenliste()}\n\n{abschnittsliste()}\n\nRegeln:\n{REGELN}\n\n"
            f"{AUSGABE}\n\nBeispiel (erfunden).\nEingabe:\n{BEISPIEL_EINGABE}\nAusgabe:\n{BEISPIEL_AUSGABE}")


def nachrichten(liste: list[dict], schema: str = SCHEMA_VERSION) -> list[dict]:
    """Systemprompt und Benutzernachricht; die Anleitung steht vor dem Dokument und ist für alle
    Dokumente gleich (Präfix-Cache). isolierung-v2.1: Atome mit Legende atome-v3."""
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"{anleitung(schema)}\n\nDokument:\n"
                                        f"{eingabe_rendern(liste, ATOME_ZU_SCHEMA[schema])}"}]


def prompt_hash(schema: str = SCHEMA_VERSION) -> str:
    roh = json.dumps([schema, SYSTEM, anleitung(schema)], ensure_ascii=False)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


# ================================================================ Ausgabeformat und Gültigkeit


def json_schema(atom_ids: list[str]) -> dict:
    """JSON Schema (Draft 2020-12) der Isolierer-Ausgabe; Atom-IDs als Aufzählung. Querbezüge
    (Abdeckung, Zusammenhang, erlaubte Abschnitte, Bezüge) prüft pruefe_zerlegung()."""
    atom = {"type": "string", "enum": list(atom_ids)}
    uid = {"type": "string", "pattern": RX_UNIT.pattern}
    bereich = {"type": "object", "additionalProperties": False, "required": ["from", "to"],
               "properties": {"from": atom, "to": atom}}
    unit = {
        "type": "object", "additionalProperties": False, "required": list(UNIT_FIELDS),
        "properties": {
            "id": uid,
            "type": {"type": "string", "enum": TYPE_KEYS},
            "atoms": {"type": "array", "minItems": 1, "items": bereich},
            "section": {"enum": SECTION_KEYS + [None]},
            "refers_to": {"type": "array", "items": uid},
            "number": {"type": "array", "items": {"type": "string", "pattern": RX_NUMBER.pattern}},
            "quoted": {"type": "boolean"},
        }}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "additionalProperties": False, "required": ["units"],
            "properties": {"units": {"type": "array", "minItems": 1, "items": unit},
                           "atoms_with_boundary": {"type": "array", "items": atom},
                           "uncertain": {"type": "array", "items": uid}}}


def json_lesen(roh: str) -> dict:
    """JSON aus einer Modellantwort; Markdown-Zäune und Text darum werden toleriert."""
    t = roh.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        t = m.group(1).strip()
    a, e = t.find("{"), t.rfind("}")
    if a < 0 or e < a:
        raise ValueError("kein JSON-Objekt in der Antwort")
    return json.loads(t[a:e + 1])


def ohne_herkunft(ausgabe: dict) -> dict:
    """Felder mit «_» am Anfang (Herkunftsangaben in Referenzdateien) entfernen."""
    return {k: v for k, v in ausgabe.items() if not k.startswith("_")}


def _pos(atom_ids: list[str]) -> dict[str, int]:
    return {a: i for i, a in enumerate(atom_ids)}


def bereiche_von(einheit: dict, pos: dict[str, int]) -> list[tuple[int, int]]:
    return [(pos[b["from"]], pos[b["to"]]) for b in einheit["atoms"]]


def zuordnung(ausgabe: dict, atom_ids: list[str]) -> list[str | None]:
    """Einheit je Atom (Position) einer gültigen Zerlegung."""
    pos = _pos(atom_ids)
    z: list[str | None] = [None] * len(atom_ids)
    for e in ausgabe["units"]:
        for von, bis in bereiche_von(e, pos):
            for i in range(von, bis + 1):
                z[i] = e["id"]
    return z


def ist_einschub(einheit_typ: str, atome_der_einheit: list[dict]) -> bool:
    """Einschub: Typ header_footer, footnote, picture, oder alle Atome sind Seitenmobiliar
    (Docling page_header/page_footer), z. B. ein Zustellvermerk am Seitenfuss (K09)."""
    return einheit_typ in INSERT_TYPES or (bool(atome_der_einheit)
                                           and all(a.get("kopf_fuss") for a in atome_der_einheit))


def pruefe_zerlegung(ausgabe: dict, liste: list[dict], schema: str = SCHEMA_VERSION) -> tuple[list[str], list[str]]:
    """(Fehler, Warnungen) einer Isolierer-Ausgabe gegen die Atome des Dokuments.

    Gültig heisst: Format und Werte stimmen; jedes Atom liegt in genau einer Einheit (Abdeckung);
    mehrere Bereiche einer Einheit sind nur durch Einschübe getrennt oder liegen als metadata_field
    im selben Schlüssel-Wert-Bereich (Zusammenhang); section, quoted, number und refers_to passen
    zum Typ. Felder mit «_» am Anfang (Herkunft) werden übergangen.
    isolierung-v2.1: Regel 7 (quoted ohne Antwort oder Beschluss im Dokument) ist ein Fehler; Warnung,
    wenn eine answer mit einem Atom mit Fragemarker beginnt."""
    f: list[str] = []
    w: list[str] = []
    if not isinstance(ausgabe, dict) or not isinstance(ausgabe.get("units"), list):
        return ["kein Objekt mit Liste «units»"], w
    ausgabe = ohne_herkunft(ausgabe)
    for k in ausgabe:
        if k not in OUTPUT_FIELDS:
            f.append(f"unbekanntes Feld {k!r}")
    atom_ids = [a["id"] for a in liste]
    pos = _pos(atom_ids)
    n = len(atom_ids)
    units = ausgabe["units"]
    typ_von: dict[str, str] = {}
    bereiche: dict[str, list[tuple[int, int]]] = {}
    for k, e in enumerate(units):
        if not isinstance(e, dict):
            f.append(f"Einheit {k + 1} ist kein Objekt")
            continue
        uid = e.get("id")
        wo = f"Einheit {uid!r}"
        if not isinstance(uid, str) or not RX_UNIT.match(uid):
            f.append(f"{wo}: ID nicht im Format E1, E2 …")
            continue
        if uid in typ_von:
            f.append(f"{wo}: ID doppelt")
            continue
        fehlend = set(UNIT_FIELDS) - set(e)
        if fehlend:
            f.append(f"{wo}: Felder fehlen {sorted(fehlend)}")
        for x in set(e) - set(UNIT_FIELDS):
            f.append(f"{wo}: unbekanntes Feld {x!r}")
        typ = e.get("type")
        if typ not in TYPES:
            f.append(f"{wo}: unbekannter Typ {typ!r}")
            continue
        typ_von[uid] = typ
        t = TYPES[typ]
        bs = e.get("atoms")
        ok_b: list[tuple[int, int]] = []
        if not isinstance(bs, list) or not bs:
            f.append(f"{wo}: «atoms» leer oder keine Liste")
        else:
            for b in bs:
                if not isinstance(b, dict) or set(b) != {"from", "to"}:
                    f.append(f"{wo}: Bereich {b!r} nicht {{\"from\", \"to\"}}")
                    continue
                if b["from"] not in pos or b["to"] not in pos:
                    f.append(f"{wo}: unbekannte Atom-ID in {b!r}")
                    continue
                if pos[b["from"]] > pos[b["to"]]:
                    f.append(f"{wo}: Bereich {b['from']}–{b['to']} rückwärts")
                    continue
                ok_b.append((pos[b["from"]], pos[b["to"]]))
        if ok_b != sorted(ok_b):
            w.append(f"{wo}: Bereiche nicht aufsteigend")
        bereiche[uid] = sorted(ok_b)
        ab = e.get("section")
        if ab not in t.sections:
            f.append(f"{wo}: section {ab!r} bei Typ {typ} nicht erlaubt "
                     f"(erlaubt: {sorted(x or 'null' for x in t.sections)})")
        q = e.get("quoted")
        if not isinstance(q, bool):
            f.append(f"{wo}: «quoted» nicht true/false")
        elif q and not t.quotable:
            f.append(f"{wo}: quoted bei Typ {typ} nicht erlaubt")
        nr = e.get("number")
        if not isinstance(nr, list) or not all(isinstance(x, str) for x in nr):
            f.append(f"{wo}: «number» keine Liste von Texten")
        elif nr and not t.numbered:
            f.append(f"{wo}: number bei Typ {typ} nicht erlaubt")
        elif any(not RX_NUMBER.match(x) for x in nr):
            f.append(f"{wo}: number {nr!r} nicht im Format «3», «2a», «1.2», «II»")
        elif typ in QUESTION_TYPES and len(nr) > 1:
            f.append(f"{wo}: eine {typ} hat höchstens eine Nummer")
    # Bezüge (zweiter Durchgang, damit Vorwärtsverweise geprüft werden können)
    for e in units:
        if not isinstance(e, dict) or e.get("id") not in typ_von:
            continue
        uid, typ = e["id"], typ_von[e["id"]]
        t = TYPES[typ]
        rt = e.get("refers_to")
        wo = f"Einheit {uid!r}"
        if not isinstance(rt, list) or not all(isinstance(x, str) for x in rt):
            f.append(f"{wo}: «refers_to» keine Liste von IDs")
            continue
        if not rt:
            continue
        if len(set(rt)) != len(rt):
            w.append(f"{wo}: refers_to mit Wiederholungen")
        if t.relation == "answers":
            for z in rt:
                if typ_von.get(z) not in t.targets:
                    f.append(f"{wo}: refers_to {z!r} ist keine question/demand")
        elif t.relation == "annotates":
            for z in rt:
                if z not in typ_von or typ_von[z] in INSERT_TYPES or z == uid:
                    f.append(f"{wo}: refers_to {z!r} ist keine Einheit mit Fussnotenzeichen")
        elif e.get("quoted") and all(RX_UNIT_EXTERN.match(z) for z in rt):
            pass   # quoted → Original in einem anderen Dokument (setzt die Verknüpfung, nicht der Isolierer)
        else:
            f.append(f"{wo}: refers_to bei Typ {typ} nicht erlaubt")
    # Abdeckung
    besitzer: list[list[str]] = [[] for _ in range(n)]
    for uid, bs in bereiche.items():
        for a, b in bs:
            for i in range(a, b + 1):
                besitzer[i].append(uid)
    luecken = [atom_ids[i] for i in range(n) if not besitzer[i]]
    doppelt = [atom_ids[i] for i in range(n) if len(besitzer[i]) > 1]
    if luecken:
        f.append(f"Lücke: {len(luecken)} Atome ohne Einheit, ab {luecken[:5]}")
    if doppelt:
        f.append(f"Überlappung: {len(doppelt)} Atome in mehreren Einheiten, ab {doppelt[:5]}")
    # Zusammenhang
    if not luecken and not doppelt:
        atome_von = {uid: [liste[i] for a, b in bs for i in range(a, b + 1)] for uid, bs in bereiche.items()}
        einschub = {uid: ist_einschub(typ_von[uid], atome_von[uid]) for uid in bereiche}
        defekt = defekt_bloecke(liste)
        for uid, bs in bereiche.items():
            for (_a1, b1), (a2, _) in itertools.pairwise(bs):
                if a2 == b1 + 1:
                    w.append(f"Einheit {uid!r}: angrenzende Bereiche, zusammenfassen")
                    continue
                dazwischen = {besitzer[i][0] for i in range(b1 + 1, a2)
                              if liste[i]["block"] not in defekt}
                fremd = sorted(x for x in dazwischen if not einschub[x])
                if not fremd:
                    continue
                if typ_von[uid] == "metadata_field" and _kv_verschraenkt(liste, bs, range(b1 + 1, a2),
                                                                        besitzer, typ_von):
                    continue
                f.append(f"Einheit {uid!r}: zwischen den Bereichen liegen {fremd[:3]}; erlaubt sind dort nur "
                         f"Kopf-/Fusszeile, Fussnote, Bild, Zeilen eines Blocks mit «Drittel-Regel verletzt» "
                         f"und bei metadata_field Felder desselben Schlüssel-Wert-Bereichs. Teile die Einheit "
                         f"dort in zwei Einheiten desselben Typs")
        ids = [e["id"] for e in units if isinstance(e, dict) and e.get("id") in bereiche and bereiche[e["id"]]]
        if ids != sorted(ids, key=lambda x: bereiche[x][0][0]):
            w.append("Einheiten nicht in der Reihenfolge ihres ersten Atoms")
        if [int(x[1:]) for x in ids] != list(range(1, len(ids) + 1)):
            w.append("Einheiten-IDs nicht fortlaufend E1 … En")
        # Fragenummern ohne Zitat doppelt (Zählung mit Neustart ist möglich, B1)
        gesehen: dict[tuple, str] = {}
        for e in units:
            if isinstance(e, dict) and typ_von.get(e.get("id")) == "question" and not e.get("quoted"):
                for x in e.get("number") or []:
                    if (x,) in gesehen:
                        w.append(f"Einheit {e['id']!r}: Fragenummer {x} doppelt (Neustart der Zählung?)")
                    gesehen[(x,)] = e["id"]
    # Dokument-Felder
    for k, gueltig in (("atoms_with_boundary", pos), ("uncertain", typ_von)):
        v = ausgabe.get(k, [])
        if not isinstance(v, list):
            f.append(f"«{k}» keine Liste")
            continue
        for x in v:
            if x not in gueltig:
                f.append(f"{k}: unbekannte ID {x!r}")
    # Warnungen zum Inhalt
    typen = set(typ_von.values())
    if typen & QUESTION_TYPES and "answer" in typen:
        for e in units:
            if (isinstance(e, dict) and typ_von.get(e.get("id")) == "answer"
                    and not e.get("refers_to") and not e.get("number")):
                w.append(f"Einheit {e['id']!r}: answer ohne refers_to und ohne number, obwohl Fragen "
                         "im Dokument stehen")
    exekutive = typen & {"answer", "response_intro", "recommendation", "resolution"}
    if exekutive:
        for e in units:
            if (isinstance(e, dict) and typ_von.get(e.get("id")) in VORSTOSS_TEXT and e.get("quoted") is False):
                w.append(f"Einheit {e['id']!r}: {typ_von[e['id']]} nicht quoted in einem Dokument der Exekutive")
    if not exekutive and any(
            isinstance(e, dict) and e.get("quoted") for e in units):
        if schema == SCHEMA_V21:
            q_ids = [e.get("id") for e in units if isinstance(e, dict) and e.get("quoted")]
            f.append(f"Regel 7: quoted-Einheiten {q_ids[:5]}{' …' if len(q_ids) > 5 else ''}, aber keine Einheit "
                     "answer, response_intro, recommendation oder resolution im Dokument: Das Dokument ist ein "
                     "eingereichter Vorstoss, darin ist nichts quoted. Setze quoted false")
        else:
            w.append("quoted-Einheiten, aber keine Antwort oder kein Beschluss im Dokument")
    if schema == SCHEMA_V21:
        for e in units:
            if (isinstance(e, dict) and typ_von.get(e.get("id")) == "answer" and bereiche.get(e["id"])
                    and hat_merkmal(liste[bereiche[e["id"]][0][0]], "question_number")):
                w.append(f"Einheit {e['id']!r}: answer beginnt mit Fragemarker (Atom "
                         f"{liste[bereiche[e['id']][0][0]]['id']}); eine vor der Antwort wiederholte Frage ist eine "
                         "eigene Einheit question mit quoted")
    for i, a in enumerate(liste):
        if not a["text"] and besitzer[i] and typ_von.get(besitzer[i][0]) not in (
                "picture", "signature", "letter_element", "procedural_note", "other"):
            w.append(f"Atom {a['id']} ohne Text in Einheit vom Typ {typ_von.get(besitzer[i][0])}")
    return f, w


def defekt_bloecke(liste: list[dict]) -> set[str]:
    """Blöcke mit Lesereihenfolge-Defekt: über einen Seitenwechsel falsch zusammengefügt
    (Merkmal thirds_rule_violated, docling-test.md 5.2: S2 B12, K11 B10). Ihre Atome dürfen
    zwischen zwei Bereichen einer Einheit liegen."""
    return {a["block"] for a in liste if hat_merkmal(a, "thirds_rule_violated")}


def _kv_verschraenkt(liste: list[dict], bs: list[tuple[int, int]], luecke: range,
                     besitzer: list[list[str]], typ_von: dict[str, str]) -> bool:
    """Ausnahme für Schlüssel-Wert-Bereiche: Einheit und alle Atome dazwischen liegen im selben
    Bereich (eltern_ref), und dazwischen liegen nur metadata_field oder Einschübe."""
    refs = {liste[i].get("eltern_ref") for a, b in bs for i in range(a, b + 1)}
    if len(refs) != 1 or None in refs or liste[bs[0][0]].get("eltern") not in KV_ELTERN:
        return False
    ref = refs.pop()
    for i in luecke:
        if typ_von[besitzer[i][0]] in INSERT_TYPES:
            continue
        if liste[i].get("eltern_ref") != ref or typ_von[besitzer[i][0]] != "metadata_field":
            return False
    return True


def reparaturhinweise(fehler: list[str], ausgabe: dict | None, liste: list[dict]) -> list[str]:
    """isolierung-v2.1 (8.3 Punkt 4): Hinweise je Fehlerart für die Korrekturschleife. Bei einer Lücke
    nennt der Hinweis die Einheiten vor und nach dem Atom; sonst ein fester Satz je Fehlerart. Nur
    Kennungen und Typen, kein Dokumenttext."""
    ids = [a["id"] for a in liste]
    pos = _pos(ids)
    besitzer: dict[int, list[tuple[str, str]]] = {}
    for e in (ausgabe or {}).get("units") or []:
        if not isinstance(e, dict) or not isinstance(e.get("atoms"), list):
            continue
        for b in e["atoms"]:
            if isinstance(b, dict) and b.get("from") in pos and b.get("to") in pos:
                for i in range(pos[b["from"]], pos[b["to"]] + 1):
                    besitzer.setdefault(i, []).append((str(e.get("id")), str(e.get("type"))))
    aus: list[str] = []

    def nachbar(i: int, schritt: int) -> str:
        j = i + schritt
        while 0 <= j < len(ids) and j not in besitzer:
            j += schritt
        if not 0 <= j < len(ids):
            return "Dokumentrand"
        uid, typ = besitzer[j][0]
        return f"{uid} ({typ}, {'endet mit' if schritt < 0 else 'beginnt mit'} {ids[j]})"
    for x in fehler:
        if x.startswith("Lücke"):
            luecke = [i for i in range(len(ids)) if i not in besitzer]
            for i in luecke[:5]:
                aus.append(f"Atom {ids[i]} gehört zu keiner Einheit; davor {nachbar(i, -1)}, danach {nachbar(i, 1)}. "
                           "Ordne es einer dieser Einheiten zu (Bereich erweitern) oder bilde eine eigene Einheit, "
                           "z. B. letter_element für eine Dokumentart-Überschrift, header_footer, picture oder other.")
        elif x.startswith("Überlappung"):
            doppelt = [i for i, b in sorted(besitzer.items()) if len(b) > 1]
            for i in doppelt[:5]:
                aus.append(f"Atom {ids[i]} steht in {', '.join(u for u, _ in besitzer[i])}: lass es nur in einer "
                           "Einheit und kürze die Bereiche der anderen.")
        elif "unbekannte Atom-ID" in x or "unbekannte ID" in x:
            aus.append("Verwende nur Atom-IDs aus der Liste, genau wie geschrieben (B<Block>.<Zeile> bzw. "
                       "B<Block>.<Zeile>.<Teil>); erfinde keine IDs.")
        elif x.startswith("Regel 7"):
            aus.append("Setze in diesem Dokument bei allen Einheiten quoted false (eingereichter Vorstoss).")
        elif "ist keine question/demand" in x:
            aus.append("refers_to einer answer oder recommendation zeigt nur auf Einheiten vom Typ question oder "
                       "demand; steht die Frage nicht im Dokument, refers_to [] und number setzen.")
        elif "nicht im Format" in x:
            aus.append("number enthält nur die gedruckte Nummer ohne Punkt und Klammer («3», «2a», «1.2», «II»).")
        elif "kein gültiges JSON" in x or "abgeschnitten" in x:
            aus.append("Gib nur das vollständige JSON-Objekt aus, ohne Text davor oder danach.")
    return list(dict.fromkeys(aus))


# ================================================================ Normalisierung (deterministisch, nach der Prüfung)

# Ganzheiten: benachbarte Einheiten dieses Typs (gleicher Abschnitt, gleiches quoted, nur Einschübe oder
# Blöcke mit Lesereihenfolge-Defekt dazwischen) sind nach Regel 2 eine Einheit. answer nur, wenn beide
# weder refers_to noch number haben (Fliesstext-Antwort).
GANZHEITEN = {"title", "short_title", "sponsor_info", "submitted_text", "reasoning", "response_intro",
              "signature", "distribution", "summary"}


def normalisieren(ausgabe: dict, liste: list[dict]) -> tuple[dict, list[str]]:
    """Gültige Zerlegung → normalisierte Zerlegung und Protokoll. Schritte: (1) angrenzende Bereiche
    einer Einheit zusammenfassen; (2) benachbarte Ganzheiten zusammenfassen (GANZHEITEN, Fliesstext-
    answer); (3) Einheiten nach erstem Atom neu nummerieren, refers_to und uncertain umschreiben.
    Ändert keine Grenze zwischen verschiedenen Typen und keinen Typ."""
    ausgabe = json.loads(json.dumps(ohne_herkunft(ausgabe)))
    ids = [a["id"] for a in liste]
    pos = _pos(ids)
    protokoll: list[str] = []
    z = zuordnung(ausgabe, ids)
    units = sorted(ausgabe["units"], key=lambda e: pos[e["atoms"][0]["from"]])
    typ = {e["id"]: e["type"] for e in units}
    atome_von: dict[str, list[dict]] = {}
    for i, u in enumerate(z):
        atome_von.setdefault(u, []).append(liste[i])
    einschub = {u: ist_einschub(typ[u], atome_von[u]) for u in typ}
    defekt = defekt_bloecke(liste)

    def luecke_ok(b1: int, a2: int) -> bool:
        return all(einschub[z[i]] or liste[i]["block"] in defekt for i in range(b1 + 1, a2))

    def bereiche_setzen(e: dict, br: list[tuple[int, int]]) -> None:
        br = sorted(br)
        zus: list[list[int]] = []
        for a, b in br:
            if zus and a == zus[-1][1] + 1:
                zus[-1][1] = b
            else:
                zus.append([a, b])
        e["atoms"] = [{"from": ids[a], "to": ids[b]} for a, b in zus]

    aus: list[dict] = []
    umbenannt: dict[str, str] = {}
    for e in units:
        br = bereiche_von(e, pos)
        vor = next((x for x in reversed(aus) if not einschub[x["_id0"]]), None)
        if vor is not None and not einschub[e["id"]]:
            vbr = bereiche_von(vor, pos)
            gleich = (vor["type"] == e["type"] and vor.get("section") == e.get("section")
                      and bool(vor.get("quoted")) == bool(e.get("quoted")))
            ganz = e["type"] in GANZHEITEN or (
                e["type"] == "answer" and not vor.get("refers_to") and not e.get("refers_to")
                and not vor.get("number") and not e.get("number"))
            if gleich and ganz and luecke_ok(max(b for _, b in vbr), min(a for a, _ in br)):
                bereiche_setzen(vor, vbr + br)
                umbenannt[e["id"]] = vor["_id0"]
                protokoll.append(f"{e['id']} in {vor['_id0']} zusammengefasst ({e['type']})")
                continue
        n = dict(e, _id0=e["id"])
        if len(br) > 1 and any(b + 1 == a for (_, b), (a, _) in itertools.pairwise(br)):
            protokoll.append(f"{e['id']}: angrenzende Bereiche zusammengefasst")
        bereiche_setzen(n, br)
        aus.append(n)
    neu = {x["_id0"]: f"E{k}" for k, x in enumerate(aus, 1)}
    for alt, ziel in umbenannt.items():
        neu[alt] = neu[ziel]
    for x in aus:
        x["id"] = neu[x.pop("_id0")]
        x["refers_to"] = list(dict.fromkeys(neu.get(r, r) for r in x.get("refers_to") or []))
    ergebnis = {"units": aus, "atoms_with_boundary": ausgabe.get("atoms_with_boundary", []),
                "uncertain": list(dict.fromkeys(neu.get(u, u) for u in ausgabe.get("uncertain", [])))}
    return ergebnis, protokoll


# ================================================================ Messgrössen

# Vorschlag, Begründung in isolierung-strategie.md Abschnitt 8. Mindestwerte; «_max» = Höchstwerte.
GATE = {
    "digital": {"gueltig_nach_korrektur": 1.00, "grenzen_f1": 0.95, "kerngrenzen_f1": 0.97,
                "pk_max": 0.05, "windowdiff_max": 0.08, "einheiten_exakt": 0.90,
                "typ_genauigkeit": 0.95, "bezug_f1": 0.95, "abschnitt_genauigkeit": 0.98,
                "textblock_treffer": 0.90, "dokumente_ohne_kernfehler": 0.80,
                "atome_mit_grenze_ref_max": 0.01},
    "scan": {"gueltig_nach_korrektur": 0.85, "grenzen_f1": 0.90, "kerngrenzen_f1": 0.93,
             "pk_max": 0.10, "windowdiff_max": 0.15, "einheiten_exakt": 0.80,
             "typ_genauigkeit": 0.90, "bezug_f1": 0.90, "abschnitt_genauigkeit": 0.95,
             "textblock_treffer": 0.80, "dokumente_ohne_kernfehler": 0.60,
             "atome_mit_grenze_ref_max": 0.03},
}


def grenzen(z: list) -> set[int]:
    """Grenzen als Positionen i: zwischen Atom i und i+1 wechselt die Einheit."""
    return {i for i in range(len(z) - 1) if z[i] != z[i + 1]}


def kernbereich(ref: list, typ_ref: dict) -> set[int]:
    """Positionen, an denen nach der Referenz eine Kerneinheit beginnt, endet oder weitergeht
    (mindestens eines der beiden Atome gehört zu einem Kerntyp). Gilt für Referenz und Hypothese
    gleich, damit Typfehler der Hypothese hier nicht mitzählen."""
    return {i for i in range(len(ref) - 1) if typ_ref.get(ref[i]) in CORE_TYPES
            or typ_ref.get(ref[i + 1]) in CORE_TYPES}


def prf(tp: int, n_hyp: int, n_ref: int) -> tuple[float, float, float]:
    p = tp / n_hyp if n_hyp else 1.0
    r = tp / n_ref if n_ref else 1.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def grenzen_prf(ref: list, hyp: list, toleranz: int = 0) -> tuple[int, int, int]:
    """(Treffer, Grenzen Hypothese, Grenzen Referenz); mit Toleranz zählt eine Hypothesengrenze,
    wenn eine noch nicht vergebene Referenzgrenze höchstens so weit entfernt ist."""
    gr, gh = sorted(grenzen(ref)), sorted(grenzen(hyp))
    if toleranz == 0:
        return len(set(gr) & set(gh)), len(gh), len(gr)
    frei = set(gr)
    tp = 0
    for g in gh:
        kand = [x for x in frei if abs(x - g) <= toleranz]
        if kand:
            frei.discard(min(kand, key=lambda x: (abs(x - g), x)))
            tp += 1
    return tp, len(gh), len(gr)


def k_wert(ref: list) -> int:
    """Fensterbreite für Pk und WindowDiff: halbe mittlere Einheitenlänge der Referenz (Atome)."""
    n_einheiten = len(set(ref))
    return max(1, round(len(ref) / (2 * max(1, n_einheiten))))


def pk(ref: list, hyp: list, k: int | None = None) -> float:
    """Pk (Beeferman et al. 1999): Anteil der Fensterpaare (i, i+k), bei denen Referenz und
    Hypothese uneins sind, ob beide Atome in derselben Einheit liegen. Einheit = Identität, Bereiche
    über einen Seitenwechsel zählen als dieselbe Einheit."""
    k = k or k_wert(ref)
    n = len(ref) - k
    if n <= 0:
        return 0.0
    return sum((ref[i] == ref[i + k]) != (hyp[i] == hyp[i + k]) for i in range(n)) / n


def windowdiff(ref: list, hyp: list, k: int | None = None) -> float:
    """WindowDiff (Pevzner und Hearst 2002): Anteil der Fenster, in denen die Zahl der Grenzen in
    Referenz und Hypothese verschieden ist."""
    k = k or k_wert(ref)
    n = len(ref) - k
    if n <= 0:
        return 0.0
    gr, gh = grenzen(ref), grenzen(hyp)
    return sum(sum(1 for j in range(i, i + k) if j in gr) != sum(1 for j in range(i, i + k) if j in gh)
               for i in range(n)) / n


def _mengen(z: list) -> dict[str, frozenset]:
    m: dict[str, set] = {}
    for i, e in enumerate(z):
        m.setdefault(e, set()).add(i)
    return {e: frozenset(s) for e, s in m.items()}


def einheiten_abgleich(ref: list, hyp: list, schwelle: float = 0.5) -> dict[str, str]:
    """Eins-zu-eins-Zuordnung Hypothese → Referenz nach Atom-IoU (gierig, absteigend), nur Paare
    mit IoU ≥ Schwelle."""
    mr, mh = _mengen(ref), _mengen(hyp)
    paare = []
    for h, sh in mh.items():
        for r, sr in mr.items():
            inter = len(sh & sr)
            if inter:
                paare.append((inter / len(sh | sr), h, r))
    paare.sort(key=lambda x: (-x[0], x[1], x[2]))
    zu, belegt = {}, set()
    for iou, h, r in paare:
        if iou >= schwelle and h not in zu and r not in belegt:
            zu[h] = r
            belegt.add(r)
    return zu


def typ_genauigkeit(ref: list, hyp: list, typ_ref: dict, typ_hyp: dict,
                    q_ref: dict | None = None, q_hyp: dict | None = None) -> tuple[int, int, int]:
    """(gleiche Einheiten, davon Typ gleich, davon Typ und quoted gleich). Gleich = identische
    Atommenge."""
    mr = {s: e for e, s in _mengen(ref).items()}
    gleich = typ_ok = beide_ok = 0
    for h, s in _mengen(hyp).items():
        r = mr.get(s)
        if r is None:
            continue
        gleich += 1
        if typ_ref.get(r) == typ_hyp.get(h):
            typ_ok += 1
            if q_ref is None or bool(q_ref.get(r)) == bool((q_hyp or {}).get(h)):
                beide_ok += 1
    return gleich, typ_ok, beide_ok


def _bezugspaare(ausgabe: dict) -> set[tuple[str, str]]:
    """Antwort-Frage-Paare: (answer/recommendation, question/demand); ohne Frage im Dokument
    (refers_to leer, number gesetzt): (Einheit, «nr:<n>»)."""
    paare = set()
    for e in ausgabe["units"]:
        if TYPES[e["type"]].relation != "answers":
            continue
        for q in e.get("refers_to") or []:
            paare.add((e["id"], q))
        if not e.get("refers_to"):
            for nr in e.get("number") or []:
                paare.add((e["id"], f"nr:{nr}"))
    return paare


def bezug_prf(ref_aus: dict, hyp_aus: dict, ref: list, hyp: list) -> tuple[int, int, int]:
    """(Treffer, Paare Hypothese, Paare Referenz). Ein Paar der Hypothese trifft, wenn Antwort und
    Frage über einheiten_abgleich() auf ein Referenzpaar abgebildet werden."""
    zu = einheiten_abgleich(ref, hyp)
    pr, ph = _bezugspaare(ref_aus), _bezugspaare(hyp_aus)
    tp = sum(1 for a, q in ph if (zu.get(a), q if q.startswith("nr:") else zu.get(q)) in pr)
    return tp, len(ph), len(pr)


def abschnitt_je_atom(ausgabe: dict, atom_ids: list[str]) -> list:
    ab = {e["id"]: e.get("section") for e in ausgabe["units"]}
    return [ab[e] for e in zuordnung(ausgabe, atom_ids)]


def textbloecke_atome(ausgabe: dict, atom_ids: list[str]) -> dict[tuple, frozenset]:
    """Atommenge je TextBlock (section, quoted)."""
    pos = _pos(atom_ids)
    m: dict[tuple, set] = {}
    for e in ausgabe["units"]:
        if e.get("section") is None:
            continue
        for a, b in bereiche_von(e, pos):
            m.setdefault((e["section"], bool(e.get("quoted"))), set()).update(range(a, b + 1))
    return {k: frozenset(v) for k, v in m.items()}


def vergleiche(ref_aus: dict, hyp_aus: dict, atom_ids: list[str]) -> dict:
    """Alle Messgrössen eines Dokuments als Zähler (für Mikro-Mittel über Dokumente)."""
    ref_aus, hyp_aus = ohne_herkunft(ref_aus), ohne_herkunft(hyp_aus)
    ref, hyp = zuordnung(ref_aus, atom_ids), zuordnung(hyp_aus, atom_ids)
    tr = {e["id"]: e["type"] for e in ref_aus["units"]}
    th = {e["id"]: e["type"] for e in hyp_aus["units"]}
    qr = {e["id"]: e.get("quoted") for e in ref_aus["units"]}
    qh = {e["id"]: e.get("quoted") for e in hyp_aus["units"]}
    tp, nh, nr = grenzen_prf(ref, hyp)
    tp1, _, _ = grenzen_prf(ref, hyp, toleranz=1)
    kb = kernbereich(ref, tr)
    kr, kh = grenzen(ref) & kb, grenzen(hyp) & kb
    gleich, typ_ok, beide_ok = typ_genauigkeit(ref, hyp, tr, th, qr, qh)
    btp, bnh, bnr = bezug_prf(ref_aus, hyp_aus, ref, hyp)
    ar, ah = abschnitt_je_atom(ref_aus, atom_ids), abschnitt_je_atom(hyp_aus, atom_ids)
    br, bh = textbloecke_atome(ref_aus, atom_ids), textbloecke_atome(hyp_aus, atom_ids)
    alle_tb = set(br) | set(bh)
    mg_r = set(ref_aus.get("atoms_with_boundary") or [])
    mg_h = set(hyp_aus.get("atoms_with_boundary") or [])
    return {"atome": len(atom_ids), "einheiten_ref": len(tr), "einheiten_hyp": len(th),
            "grenzen_tp": tp, "grenzen_hyp": nh, "grenzen_ref": nr, "grenzen_tp_tol1": tp1,
            "kern_tp": len(kr & kh), "kern_hyp": len(kh), "kern_ref": len(kr), "kernfehler": len(kr ^ kh),
            "pk": pk(ref, hyp), "windowdiff": windowdiff(ref, hyp), "k": k_wert(ref),
            "einheiten_exakt": gleich, "typ_ok": typ_ok, "typ_quoted_ok": beide_ok,
            "typ_atom_ok": sum(1 for x, y in zip(ref, hyp) if tr[x] == th[y]),
            "bezug_tp": btp, "bezug_hyp": bnh, "bezug_ref": bnr,
            "abschnitt_ok": sum(1 for x, y in zip(ar, ah) if x == y),
            "textblock_ok": sum(1 for k in alle_tb if br.get(k) == bh.get(k)), "textblock_n": len(alle_tb),
            "mit_grenze_ref": len(mg_r), "mit_grenze_hyp": len(mg_h), "mit_grenze_beide": len(mg_r & mg_h)}


def zusammenfassen(je_dok: list[dict], gueltig: float | None = None,
                   atome_mit_text: int | None = None) -> dict:
    """Mikro-Mittel über Dokumente (Zähler summiert); Pk und WindowDiff nach Atomen gewichtet.
    gueltig = Anteil Dokumente mit gültiger Zerlegung nach Korrektur (aus dem Lauf);
    atome_mit_text = Nenner für den Anteil der Atome mit innerer Grenze (Referenz)."""
    def s(k):
        return sum(m[k] for m in je_dok)
    n_atome = s("atome") or 1
    g = prf(s("grenzen_tp"), s("grenzen_hyp"), s("grenzen_ref"))
    return {
        "dokumente": len(je_dok),
        "gueltig_nach_korrektur": gueltig,
        "grenzen_p": g[0], "grenzen_r": g[1], "grenzen_f1": g[2],
        "grenzen_f1_tol1": prf(s("grenzen_tp_tol1"), s("grenzen_hyp"), s("grenzen_ref"))[2],
        "kerngrenzen_f1": prf(s("kern_tp"), s("kern_hyp"), s("kern_ref"))[2],
        "pk_max": sum(m["pk"] * m["atome"] for m in je_dok) / n_atome,
        "windowdiff_max": sum(m["windowdiff"] * m["atome"] for m in je_dok) / n_atome,
        "einheiten_exakt": s("einheiten_exakt") / (s("einheiten_ref") or 1),
        "typ_genauigkeit": s("typ_ok") / (s("einheiten_exakt") or 1),
        "typ_quoted_genauigkeit": s("typ_quoted_ok") / (s("einheiten_exakt") or 1),
        "typ_je_atom": s("typ_atom_ok") / n_atome,
        "bezug_f1": prf(s("bezug_tp"), s("bezug_hyp"), s("bezug_ref"))[2],
        "abschnitt_genauigkeit": s("abschnitt_ok") / n_atome,
        "textblock_treffer": s("textblock_ok") / (s("textblock_n") or 1),
        "dokumente_ohne_kernfehler": sum(1 for m in je_dok if m["kernfehler"] == 0) / (len(je_dok) or 1),
        "atome_mit_grenze_ref_max": (s("mit_grenze_ref") / atome_mit_text) if atome_mit_text else None,
        "atome_mit_grenze_f1": prf(s("mit_grenze_beide"), s("mit_grenze_hyp"), s("mit_grenze_ref"))[2],
    }


def gate_pruefen(werte: dict, klasse_: str) -> dict[str, tuple]:
    """Je Gate-Grösse (Wert, Schwelle, erfüllt). Schlüssel mit «_max» sind Höchstwerte."""
    aus = {}
    for k, schwelle in GATE[klasse_].items():
        v = werte.get(k)
        aus[k] = (None, schwelle, None) if v is None else (
            v, schwelle, v <= schwelle if k.endswith("_max") else v >= schwelle)
    return aus


# ================================================================ eCH-Richtext je Abschnitt

KONJUNKTIONEN = {"und", "oder", "bzw.", "resp.", "sowie", "et", "ou", "e", "o", "ed", "u", "and", "or"}
# Vorderteile, nach denen ein Trennstrich am Zeilenende zum Wort gehört (fr/it Zusammensetzungen)
BINDESTRICH_VOR = {"peut", "c'est", "c’est", "vis", "au", "ci", "là", "celui", "celle", "ceux", "celles",
                   "sous", "porte", "avant", "contre", "demi", "mi", "non", "quasi", "semi", "anti", "après",
                   "arrière", "grand", "garde", "ex", "vice", "co", "est-ce", "dit", "elle", "il", "lui"}
RX_OL = re.compile(r"^(\d{1,3})[.)][ \t]+")
RX_UL = re.compile(r"^([-–—•·▪◦●■*]|o(?=[ \t]+[A-ZÄÖÜ]))[ \t]+")
RX_GLIEDERUNG = re.compile(r"^(\d+(?:\.\d+)*)\.?\s")
ERLAUBTE_TAGS = {"p", "h2", "h3", "h4", "ol", "ul", "li", "table", "thead", "tbody", "tr", "td",
                 "em", "strong", "i", "b", "u", "s", "sub", "sup", "a", "img", "figure"}


def _esc(t: str) -> str:
    return html.escape(t, quote=False)


def _trennstrich_weg(links: str, rechts: str, gesamt: str) -> str:
    """Entscheid am Zeilenende «…x-» + «y…»: 'weg' (Silbentrennung, Strich entfällt), 'halten'
    (Strich bleibt, kein Leerzeichen) oder 'leer' (Strich bleibt, Leerzeichen: «Lager- und»)."""
    if not re.search(r"[^\W\d_]-$", links) or links.endswith("--"):
        return "kein"
    erstes = rechts.split(" ", 1)[0]
    if erstes in KONJUNKTIONEN:
        return "leer"
    if not rechts[:1].islower():
        return "halten"
    vorder = re.split(r"[\s(«\"'„]", links[:-1])[-1].lower()
    if vorder in BINDESTRICH_VOR:
        return "halten"
    wort_rechts = re.match(r"[^\W\d_]+", rechts)
    if wort_rechts and f"{vorder}-{wort_rechts.group(0).lower()}" in gesamt.lower():
        return "halten"   # Bindestrich-Form kommt im Dokument auf einer Zeile vor
    return "weg"


def _absatz_text(atome_abs: list[dict], gesamt: str, aenderungen: dict) -> tuple[str, list[str]]:
    """Zeilen eines Absatzes zu einer Zeile. Einzige Textänderung neben Leerraum: Trennstrich am
    Zeilenende vor Kleinbuchstaben fällt weg (absolute Position in text_gesamt wird protokolliert).
    Gibt (Text, Atom-IDs in Reihenfolge) zurück."""
    aus, ids, prev_ende = "", [], 0
    for a in atome_abs:
        t = a["text"]
        if not t:
            continue
        ids.append(a["id"])
        if not aus:
            aus, prev_ende = t, a["zeichen"][1]
            continue
        art = _trennstrich_weg(aus, t, gesamt)
        if art == "weg":
            aenderungen["hyphen_removed"].append(prev_ende - 1)
            aus = aus[:-1] + t
        elif art == "halten":
            aus += t
        else:
            aus += " " + t
        prev_ende = a["zeichen"][1]
    return re.sub(r"[ \t]+", " ", aus), ids


def richtext(ausgabe: dict, liste: list[dict], dok: dict, zusammenlegen: dict | None = None) -> list[dict]:
    """eCH-Richtext je TextBlock (section, quoted) aus einer gültigen Zerlegung, deterministisch.

    Regeln: Absatz = Atome derselben Einheit aus demselben Docling-Block. Element nach Typ und
    Docling-Form: heading → h3 (report: h2–h4 nach Gliederungstiefe); Überschrift oder einzeiliger
    Antwortmarker am Anfang einer mehrteiligen Einheit → h4; Listenpunkte → ol (fortlaufende arabische
    Nummern, mit start) bzw. ul (Aufzählungszeichen), Marker entfernt, sonst p mit Marker; Tabellen
    → table (Kopfzeilen in thead, Zellen td); Bilder ohne Text entfallen; footnote → p am Ende; sonst p.
    title und short_title als Klartext. Text bleibt Wortlaut; einzige Änderungen: Zeilen werden mit
    Leerzeichen verbunden, Trennstriche der Silbentrennung entfallen, Listenmarker gehen in ol/ul
    über (alles protokolliert, umkehrbar). Seiten, Rahmen und Zeichenbereiche stehen in der Provenienz
    (provenance), nie im HTML. zusammenlegen: {Abschnitt: Ziel} (K95: recommendation → response)."""
    ausgabe = ohne_herkunft(ausgabe)
    zusammenlegen = zusammenlegen or {}
    gesamt = dok["text_gesamt"]
    ids = [a["id"] for a in liste]
    pos = _pos(ids)
    atom = {a["id"]: a for a in liste}
    tabellen = {b["id"]: b.get("tabelle") for b in dok["bloecke"] if b.get("label") in at.TABELLEN}
    units = sorted(ausgabe["units"], key=lambda e: pos[e["atoms"][0]["from"]])
    gruppen: dict[tuple, list[dict]] = {}
    for e in units:
        if e.get("section") is None:
            continue
        ab = zusammenlegen.get(e["section"], e["section"])
        gruppen.setdefault((ab, bool(e.get("quoted"))), []).append(e)
    bloecke_aus = []
    for (abschnitt, quoted), es in sorted(gruppen.items(), key=lambda kv: pos[kv[1][0]["atoms"][0]["from"]]):
        aenderungen = {"hyphen_removed": [], "list_marker_removed": [], "empty_atoms": []}
        teile: list[dict] = []        # {"el", "text", "unit", "atoms", "extra"}
        fussnoten: list[dict] = []
        for e in es:
            atome_e = [atom[ids[i]] for a, b in bereiche_von(e, pos) for i in range(a, b + 1)]
            absaetze: list[list[dict]] = []
            for a in atome_e:
                if absaetze and absaetze[-1][-1]["block"] == a["block"]:
                    absaetze[-1].append(a)
                else:
                    absaetze.append([a])
            mit_text = [ab_ for ab_ in absaetze if any(a["text"] for a in ab_)]
            for a in atome_e:
                if not a["text"]:
                    aenderungen["empty_atoms"].append(a["id"])
            for k, ab_ in enumerate(mit_text):
                lab = ab_[0]["label"]
                if lab in at.TABELLEN:
                    teile.append({"el": "table", "unit": e["id"], "atoms": [a["id"] for a in ab_ if a["text"]],
                                  "extra": (tabellen.get(ab_[0]["block"]), ab_)})
                    continue
                text, a_ids = _absatz_text(ab_, gesamt, aenderungen)
                stueck = {"text": text, "unit": e["id"], "atoms": a_ids, "erstes": atom[a_ids[0]]}
                if e["type"] == "footnote" or lab == "footnote":
                    fussnoten.append(stueck | {"el": "p"})
                elif e["type"] == "heading":
                    m = RX_GLIEDERUNG.match(text)
                    tiefe = m.group(1).count(".") + 1 if (m and abschnitt == "report") else 2
                    teile.append(stueck | {"el": f"h{min(4, tiefe + 1)}"})
                elif k == 0 and len(mit_text) > 1 and (
                        lab == "section_header"
                        or (len(ab_) == 1 and len(text) <= 60 and at.RX_BEZUG.match(text)
                            and text.rstrip().endswith(":"))):
                    teile.append(stueck | {"el": "h4"})
                elif lab == "list_item":
                    teile.append(stueck | {"el": "li"})
                else:
                    teile.append(stueck | {"el": "p"})
        teile += fussnoten
        quell_atome = [x for t in teile for x in t["atoms"]]
        form = SECTION[abschnitt].form
        stuecke: list[tuple[str, str | None]] = []   # (HTML oder Text, Einheit; Listen-Tags: erste/letzte)
        if form == "plain":
            for j, t in enumerate(teile):
                if t["el"] == "table":
                    txt = " ".join(a["text"].replace("\t", " ") for a in t["extra"][1] if a["text"])
                else:
                    txt = t["text"]
                stuecke.append(((" " if j else "") + txt, t["unit"]))
        else:
            i = 0
            while i < len(teile):
                t = teile[i]
                if t["el"] == "li":
                    j = i
                    while j < len(teile) and teile[j]["el"] == "li":
                        j += 1
                    lis = teile[i:j]
                    nrs = [RX_OL.match(x["text"]) for x in lis]
                    pkt = [RX_UL.match(x["text"]) for x in lis]
                    folge = all(nrs) and [int(m.group(1)) for m in nrs] == list(
                        range(int(nrs[0].group(1)), int(nrs[0].group(1)) + len(lis)))
                    if folge or all(pkt):
                        ms = nrs if folge else pkt
                        start = int(nrs[0].group(1)) if folge else 1
                        stuecke.append((f'<ol start="{start}">' if folge and start != 1 else
                                        ("<ol>" if folge else "<ul>"), lis[0]["unit"]))
                        for x, m in zip(lis, ms):
                            a0 = x["erstes"]
                            aenderungen["list_marker_removed"].append(
                                [a0["zeichen"][0], a0["zeichen"][0] + len(m.group(0).rstrip(" \t"))])
                            stuecke.append((f"<li>{_esc(x['text'][m.end():])}</li>", x["unit"]))
                        stuecke.append(("</ol>" if folge else "</ul>", lis[-1]["unit"]))
                    else:
                        stuecke += [(f"<p>{_esc(x['text'])}</p>", x["unit"]) for x in lis]
                    i = j
                    continue
                if t["el"] == "table":
                    stuecke.append((_tabelle_html(*t["extra"]), t["unit"]))
                else:
                    stuecke.append((f"<{t['el']}>{_esc(t['text'])}</{t['el']}>", t["unit"]))
                i += 1
        text, bereiche_html, p0 = "", {}, 0
        for s, u in stuecke:
            if u is not None:
                br_ = bereiche_html.setdefault(u, [])
                if br_ and br_[-1][1] == p0:
                    br_[-1][1] = p0 + len(s)
                else:
                    br_.append([p0, p0 + len(s)])
            text += s
            p0 += len(s)
        if form == "plain":
            text = re.sub(r"[ \t]+", " ", text)
        nfc = unicodedata.normalize("NFC", text)
        sec = SECTION[abschnitt]
        bloecke_aus.append({
            "section": abschnitt, "quoted": quoted, "form": form,
            "label_de": sec.label_de + (" (zitiert)" if quoted else ""),
            "text": nfc, "nfc_changed": nfc != text,
            "units": [{"id": e["id"], "type": e["type"], "number": e.get("number") or [],
                       "refers_to": e.get("refers_to") or [], "html_ranges": bereiche_html.get(e["id"], []),
                       "atoms": [ids[i] for a, b in bereiche_von(e, pos) for i in range(a, b + 1)]}
                      for e in es],
            "source_atoms": quell_atome,
            "provenance": [{"atom": x, "page": atom[x]["seite"], "bbox": atom[x].get("zeilenrahmen")
                            or atom[x].get("rahmen"), "chars": atom[x]["zeichen"], "ocr": atom[x].get("ocr", False)}
                           for x in quell_atome],
            "changes": aenderungen,
        })
    return bloecke_aus


def _tabelle_html(tab: dict | None, ab_: list[dict]) -> str:
    """Tabelle aus den Zeilenatomen (Zellen mit Tabulator, Wortlaut unverändert). Kopfzeile, wenn
    alle Docling-Zellen dieser Zeile Spaltenköpfe sind. colspan/rowspan nennt eCH-0292 nicht; eine
    Zeile hat so viele td wie das Atom Zellen."""
    kopf_zeilen = set()
    if tab and tab.get("zellen"):
        je_zeile: dict[int, list[bool]] = {}
        for c in tab["zellen"]:
            je_zeile.setdefault(c["zeile"], []).append(bool(c.get("spaltenkopf")))
        kopf_zeilen = {z for z, v in je_zeile.items() if v and all(v)}
    thead, tbody = [], []
    for a in ab_:
        if not a["text"]:
            continue
        zeile = "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in a["text"].split("\t")) + "</tr>"
        (thead if (a["zeile"] - 1) in kopf_zeilen and not tbody else tbody).append(zeile)
    teil = ("<thead>" + "".join(thead) + "</thead>" if thead else "") + (
        "<tbody>" + "".join(tbody) + "</tbody>" if tbody else "")
    return f"<table>{teil}</table>"


def richtext_pruefen(bloecke: list[dict], ausgabe: dict, liste: list[dict], dok: dict) -> list[str]:
    """Prüft je TextBlock unabhängig von der Erzeugung:
    (a) nur erlaubte Elemente, keine Attribute ausser start an ol;
    (b) jedes Atom mit Text aus den Einheiten des TextBlocks genau einmal in source_atoms;
    (c) Textgleichheit: sichtbarer Text ohne Leerraum = Atomtexte (in source_atoms-Reihenfolge) ohne
        Leerraum, abzüglich genau der protokollierten Änderungen;
    (d) jede Änderung ist ein Trennstrich am Ende eines Atoms bzw. ein Listenmarker am Atomanfang."""
    f = []
    ausgabe = ohne_herkunft(ausgabe)
    g = dok["text_gesamt"]
    atom = {a["id"]: a for a in liste}
    unit = {e["id"]: e for e in ausgabe["units"]}
    pos = _pos([a["id"] for a in liste])
    for tb in bloecke:
        key = f"{tb['section']}{' (quoted)' if tb['quoted'] else ''}"
        t = tb["text"]
        if tb["form"] == "richtext":
            for tag, attr in re.findall(r"<\s*/?\s*([a-zA-Z0-9]+)([^>]*)>", t):
                if tag.lower() not in ERLAUBTE_TAGS:
                    f.append(f"{key}: Element <{tag}> nicht erlaubt")
                if attr.strip() and not (tag == "ol" and re.fullmatch(r'\s+start="\d+"', attr)):
                    f.append(f"{key}: Attribut {attr.strip()!r} an <{tag}> nicht erlaubt")
            sichtbar = html.unescape(re.sub(r"<[^>]+>", "", t))
        else:
            if re.search(r"<\s*/?\s*(?:" + "|".join(sorted(ERLAUBTE_TAGS)) + r")\b[^>]*>", t):
                f.append(f"{key}: HTML-Element in Klartext-Abschnitt")
            sichtbar = t
        soll = sorted(liste[i]["id"] for u in tb["units"] for a, b in bereiche_von(unit[u["id"]], pos)
                      for i in range(a, b + 1) if liste[i]["text"])
        if sorted(tb["source_atoms"]) != soll:
            f.append(f"{key}: source_atoms decken die Atome der Einheiten nicht genau einmal ab")
        geloescht = set(tb["changes"]["hyphen_removed"])
        for von, bis in tb["changes"]["list_marker_removed"]:
            geloescht.update(range(von, bis))
        erwartet = "".join(c for x in tb["source_atoms"]
                           for p, c in enumerate(g[atom[x]["zeichen"][0]:atom[x]["zeichen"][1]],
                                                 start=atom[x]["zeichen"][0]) if p not in geloescht)
        erwartet = unicodedata.normalize("NFC", re.sub(r"\s", "", erwartet))
        if re.sub(r"\s", "", sichtbar) != erwartet:
            f.append(f"{key}: Text weicht vom Wortlaut ab (über die protokollierten Änderungen hinaus)")
        enden = {atom[x]["zeichen"][1] - 1 for x in tb["source_atoms"]}
        for p in tb["changes"]["hyphen_removed"]:
            if g[p] != "-" or p not in enden:
                f.append(f"{key}: entfernter Trennstrich an {p} ist kein Strich am Zeilenende")
        anfaenge = {atom[x]["zeichen"][0]: atom[x]["text"] for x in tb["source_atoms"]}
        for von, bis in tb["changes"]["list_marker_removed"]:
            txt = anfaenge.get(von)
            if txt is None or not (RX_OL.match(txt) or RX_UL.match(txt)) or bis - von > 4:
                f.append(f"{key}: entfernter Listenmarker {von}–{bis} nicht am Atomanfang")
    return f


def ech_texte(bloecke: list[dict], fassung: str, sprache: str | None, document_url: str | None,
              zitierte_als_ersatz: bool = False) -> dict:
    """TextBlocks im Format der eCH-0295-Fassung (i95: input/schema.yaml, k95: Kern v0.2.0).

    Für K95 vorher richtext(…, zusammenlegen=ZUSAMMENLEGEN_K95) aufrufen. Zitierte TextBlocks
    werden nur übernommen, wenn zitierte_als_ersatz (Original fehlt); I95 kennt «quoted» in
    TextOriginEnum nicht, K95 hat keine Herkunft: das Merkmal steht im Profil. Rückgabe:
    {"texts": [{"slot", "text_block"}], "not_mappable": [{"section", "quoted", "reason"}]}."""
    texts, rest = [], []
    for tb in bloecke:
        sec = SECTION[tb["section"]]
        if tb["quoted"] and not zitierte_als_ersatz:
            rest.append({"section": sec.key, "quoted": True, "reason": "zitiert, Original massgebend"})
            continue
        if fassung == "i95":
            if sec.i95_match == "none":
                rest.append({"section": sec.key, "quoted": tb["quoted"], "reason": "kein Texttyp in I95"})
                continue
            blk = {"text": tb["text"], "text_language": sprache, "text_type": sec.i95_text_type}
            if document_url:
                blk["document_url"] = document_url
            texts.append({"slot": sec.i95_slot, "text_block": blk})
        elif fassung == "k95":
            if sec.k95_match in ("none", "merged"):
                rest.append({"section": sec.key, "quoted": tb["quoted"],
                             "reason": "kein Texttyp in K95" if sec.k95_match == "none"
                             else "in response zusammengelegt (richtext mit ZUSAMMENLEGEN_K95)"})
                continue
            wert = {"value": tb["text"]} | ({"language": sprache} if sprache else {})
            if sec.k95_match == "slot":
                texts.append({"slot": sec.k95_slot, "text_block": wert})
                continue
            blk = {"text_type": sec.k95_text_type, "value": [wert]}
            if document_url:
                blk["document_url"] = document_url
            texts.append({"slot": sec.k95_slot, "text_block": blk})
        else:
            raise ValueError(f"Fassung {fassung!r}: i95 oder k95")
    return {"texts": texts, "not_mappable": rest}


# ================================================================ Hilfen: Dokumente, Basislinie, Kennzahlen


def augenschein() -> dict[str, dict]:
    with AUGENSCHEIN.open(encoding="utf-8") as fh:
        return {r["doc_id"]: r for r in csv.DictReader(fh)}


def klasse(zeile: dict | None, liste: list[dict] | None = None) -> str:
    """digital oder scan: aus der Herkunft nach pdf.md [PR] (herkunft_auto), sonst aus dem
    OCR-Anteil der Atome (mindestens die Hälfte der Atome mit Text aus OCR)."""
    if zeile and zeile.get("herkunft_auto"):
        return "digital" if zeile["herkunft_auto"] == "digital" else "scan"
    mit_text = [a for a in (liste or []) if a["text"]]
    return "scan" if mit_text and sum(a.get("ocr", False) for a in mit_text) * 2 >= len(mit_text) else "digital"


BASIS_TYP = {"page_header": "header_footer", "page_footer": "header_footer", "picture": "picture",
             "footnote": "footnote", "table": "table"}


def basislinie_docling(liste: list[dict]) -> dict:
    """Untere Schranke ohne Modell: jeder Docling-Block ist eine Einheit (Typ nur aus der Form, sonst
    other, ohne Abschnitt und Bezüge). Misst, was die Isolierung über Docling hinaus leisten muss."""
    units, block = [], None
    for a in liste:
        if a["block"] == block and units:
            units[-1]["atoms"][-1]["to"] = a["id"]
            continue
        block = a["block"]
        units.append({"id": f"E{len(units) + 1}", "type": BASIS_TYP.get(a["label"], "other"),
                      "atoms": [{"from": a["id"], "to": a["id"]}], "section": None, "refers_to": [],
                      "number": [], "quoted": False})
    return {"units": units, "atoms_with_boundary": [], "uncertain": []}


# Merkmale aus m03_atome.py, die eine Kandidatengrenze VOR dem Atom anzeigen (E16: der Isolierer-Adapter
# entscheidet nur an Kandidaten)
KANDIDAT_MERKMALE = {"answer_reference", "question_number", "enumeration", "keyword", "affair_type",
                     "intro_questions", "demand_formula", "signature_formula", "place_date", "date_line",
                     "distribution", "page_number", "kv_key", "kv_value", "kv_key_without_value",
                     "kv_value_without_key", "kv_inline", "letterspacing", "column_part", "frame_part",
                     "sentence_part", "page_break", "page_break_back", "page_break_in_block",
                     "thirds_rule_violated", "above_previous", "new_frame",
                     # atome-v3 (Runde 2, 8.2 Punkt 2); in atome-v2 nicht vorhanden, dort also ohne Wirkung
                     "number_sequence", "bracket_date", "quote_end", "table_cells_change"}


def kandidaten(liste: list[dict]) -> set[int]:
    """Kandidatengrenzen (Position i = zwischen Atom i und i+1): Blockwechsel, Wechsel von Seite oder
    Docling-Form, oder Merkmal am Atom i+1 aus KANDIDAT_MERKMALE. Regeln, kein Modell."""
    k = set()
    for i in range(len(liste) - 1):
        a, b = liste[i], liste[i + 1]
        if (a["block"] != b["block"] or a["seite"] != b["seite"] or a["label"] != b["label"]
                or any(hat_merkmal(b, m) for m in KANDIDAT_MERKMALE)):
            k.add(i)
    return k


def kandidaten_abdeckung(ref_aus: dict, liste: list[dict]) -> dict:
    """Wie viele Referenzgrenzen liegen auf Kandidaten (Obergrenze des Recalls eines Isolierers, der
    nur an Kandidaten entscheidet), und wie viele Entscheide braucht er (Kandidaten statt Atomgrenzen)."""
    ids = [a["id"] for a in liste]
    gr = grenzen(zuordnung(ohne_herkunft(ref_aus), ids))
    k = kandidaten(liste)
    return {"ref_grenzen": len(gr), "auf_kandidaten": len(gr & k), "kandidaten": len(k),
            "atomgrenzen": max(0, len(ids) - 1), "verpasst_vor": [ids[i + 1] for i in sorted(gr - k)]}


# ================================================================ Übertragung auf eine neue Atom-Fassung (Runde 2)


def atome_zuordnen(alt: list[dict], neu: list[dict]) -> list[int]:
    """Je neues Atom die Position des alten Atoms, aus dem es stammt (über Zeichenbereiche). Erlaubt ist nur
    Verfeinerung ohne Umordnung: jedes neue Atom liegt im Zeichenbereich genau eines alten Atoms desselben
    Blocks (Atome ohne Text: gleiche ID), die alten Positionen steigen nicht ab, und die Teile eines alten
    Atoms ergeben ohne Leerraum genau seinen Wortlaut. Sonst ValueError."""
    nach_block: dict[str, list[int]] = {}
    for j, a in enumerate(alt):
        nach_block.setdefault(a["block"], []).append(j)
    zu: list[int] = []
    for b in neu:
        if not b["text"]:
            kand = [j for j in nach_block.get(b["block"], []) if alt[j]["id"] == b["id"] and not alt[j]["text"]]
        else:
            kand = [j for j in nach_block.get(b["block"], []) if alt[j]["text"]
                    and alt[j]["zeichen"][0] <= b["zeichen"][0] and b["zeichen"][1] <= alt[j]["zeichen"][1]]
        if len(kand) != 1:
            raise ValueError(f"Atom {b['id']}: {len(kand)} passende alte Atome")
        zu.append(kand[0])
    if zu != sorted(zu):
        raise ValueError("Reihenfolge der Atome geändert: Übertragung nur für Verfeinerung ohne Umordnung")
    if set(zu) != set(range(len(alt))):
        raise ValueError(f"alte Atome ohne neues Atom: {[alt[j]['id'] for j in sorted(set(range(len(alt))) - set(zu))][:5]}")
    for j in set(zu):
        teile = "".join(neu[i]["text"] for i, x in enumerate(zu) if x == j)
        if re.sub(r"\s", "", teile) != re.sub(r"\s", "", alt[j]["text"]):
            raise ValueError(f"Wortlaut von {alt[j]['id']} nicht vollständig auf seine Teile verteilt")
    return zu


def uebertragen(ausgabe: dict, alt: list[dict], neu: list[dict]) -> tuple[dict, list[str]]:
    """Zerlegung von Atomen «alt» auf verfeinerte Atome «neu» übertragen (deterministisch, über
    Zeichenbereiche, atome_zuordnen()). Jeder Teil eines alten Atoms erbt dessen Einheit. Ausnahme Regel 10:
    Steht das alte Atom in atoms_with_boundary und ist es in genau zwei Teile geteilt, gehört der zweite Teil
    zur Einheit des nächsten alten Atoms (dort beginnt nach Regel 10 die neue Einheit), wenn diese eine andere
    ist; das Atom fällt dann aus atoms_with_boundary. Sonst (mehr Teile, keine Grenze danach) ValueError.
    Einheiten-IDs, Typen, Abschnitte, Bezüge, Nummern, quoted und uncertain bleiben; Bereiche werden aus den
    Atommengen neu gebildet. Felder mit «_» werden mitkopiert. Gibt (Zerlegung, Protokoll)."""
    zu = atome_zuordnen(alt, neu)
    roh = ohne_herkunft(ausgabe)
    z_alt = zuordnung(roh, [a["id"] for a in alt])
    if None in z_alt:
        raise ValueError("Zerlegung deckt die alten Atome nicht vollständig ab")
    awb = list(roh.get("atoms_with_boundary") or [])
    pos_alt = _pos([a["id"] for a in alt])
    prot: list[str] = []
    einheit_neu: list[str] = []
    teile_von: dict[int, list[int]] = {}
    for i, j in enumerate(zu):
        teile_von.setdefault(j, []).append(i)
    aufgeloest: set[str] = set()
    for i, j in enumerate(zu):
        u = z_alt[j]
        tl = teile_von[j]
        if alt[j]["id"] in awb and len(tl) > 1:
            if len(tl) != 2 or j + 1 >= len(alt) or z_alt[j + 1] == u:
                raise ValueError(f"Atom mit Grenze {alt[j]['id']}: {len(tl)} Teile, Grenze nicht eindeutig übertragbar")
            if i == tl[1]:
                u = z_alt[j + 1]
                if alt[j]["id"] not in aufgeloest:
                    prot.append(f"{alt[j]['id']} (atoms_with_boundary) → {neu[tl[0]]['id']} bleibt bei {z_alt[j]}, "
                                f"{neu[i]['id']} zu {u} (Regel 10: dort beginnt die neue Einheit)")
                aufgeloest.add(alt[j]["id"])
        elif len(tl) > 1 and i == tl[0]:
            prot.append(f"{alt[j]['id']} → {', '.join(neu[k]['id'] for k in tl)} (alle bei {u})")
        einheit_neu.append(u)
    ids_neu = [a["id"] for a in neu]
    units = []
    for e in roh["units"]:
        pos_e = [i for i, u in enumerate(einheit_neu) if u == e["id"]]
        if not pos_e:
            raise ValueError(f"Einheit {e['id']} ohne Atome nach der Übertragung")
        laeufe: list[list[int]] = []
        for i in pos_e:
            if laeufe and i == laeufe[-1][1] + 1:
                laeufe[-1][1] = i
            else:
                laeufe.append([i, i])
        units.append(dict(e, atoms=[{"from": ids_neu[a], "to": ids_neu[b]} for a, b in laeufe]))
    # atoms_with_boundary: aufgelöste fallen weg, ungeteilte behalten ihre (gleiche) ID
    awb_neu = []
    for x in awb:
        if x in aufgeloest:
            continue
        tl = teile_von[pos_alt[x]]
        if len(tl) != 1:
            raise ValueError(f"Atom mit Grenze {x} anders geteilt")
        awb_neu.append(ids_neu[tl[0]])
    ergebnis = {k: v for k, v in ausgabe.items() if k.startswith("_")} | {
        "units": units, "atoms_with_boundary": awb_neu, "uncertain": list(roh.get("uncertain") or [])}
    return ergebnis, prot


def kennzahlen_ausgeben(m: dict) -> str:
    p, r, f1 = prf(m["grenzen_tp"], m["grenzen_hyp"], m["grenzen_ref"])
    _, _, kf = prf(m["kern_tp"], m["kern_hyp"], m["kern_ref"])
    _, _, bf = prf(m["bezug_tp"], m["bezug_hyp"], m["bezug_ref"])
    return (f"Grenzen P/R/F1 {p:.3f}/{r:.3f}/{f1:.3f} (Ref {m['grenzen_ref']}, Hyp {m['grenzen_hyp']}); "
            f"Kerngrenzen F1 {kf:.3f}; Pk {m['pk']:.3f}, WindowDiff {m['windowdiff']:.3f} (k={m['k']}); "
            f"Einheiten exakt {m['einheiten_exakt']}/{m['einheiten_ref']}, Typ gleich {m['typ_ok']}; "
            f"Bezüge F1 {bf:.3f} ({m['bezug_tp']}/{m['bezug_hyp']}/{m['bezug_ref']}); "
            f"Abschnitt je Atom {m['abschnitt_ok']}/{m['atome']}; TextBlocks {m['textblock_ok']}/{m['textblock_n']}")


def kennzahlen() -> None:
    """Je Augenschein-Dokument: Atome, Einschub-Atome, Schlüssel-Wert-Bereiche mit verschränkter
    Reihenfolge, Hinweise auf Grenzen in Atomen, Prompt-Länge. Schreibt
    daten/analyse/isolierung/taxonomie_kennzahlen.csv (nur Kennungen und Zahlen)."""
    aug = augenschein()
    ANALYSE.mkdir(parents=True, exist_ok=True)
    anleitung_zeichen = len(SYSTEM) + len(anleitung())
    zeilen = []
    for p in sorted(DOCLING.glob("*.json")):
        dok = json.loads(p.read_text(encoding="utf-8"))
        doc_id = str(dok["doc_id"])
        z = aug.get(doc_id, {})
        if dok.get("status") != "success":
            zeilen.append({"zelle": z.get("zelle"), "doc_id": doc_id, "status": dok.get("status")})
            continue
        liste = atome_laden(doc_id, dok)
        kv_runs: dict[str, list[dict]] = {}
        for a in liste:
            if a.get("eltern") in KV_ELTERN and a.get("eltern_ref"):
                kv_runs.setdefault(a["eltern_ref"], []).append(a)
        verschraenkt = 0
        for run in kv_runs.values():
            ids_run = [a["id"] for a in run]
            for a in run:
                kv = a.get("kv") or {}
                if kv.get("rolle") in ("key", "schluessel"):
                    for partner in kv.get("partner") or []:
                        if partner in ids_run and ids_run.index(partner) != ids_run.index(a["id"]) + 1:
                            verschraenkt += 1
        eingabe = eingabe_rendern(liste)
        zeilen.append({
            "zelle": z.get("zelle"), "doc_id": doc_id, "status": "success", "klasse": klasse(z, liste),
            "dokumentart": z.get("dokumentart"), "seiten": len(dok["seiten"]), "atome": len(liste),
            "atome_mit_text": sum(1 for a in liste if a["text"]),
            "atome_ohne_text": sum(1 for a in liste if not a["text"]),
            "atome_seitenmobiliar": sum(1 for a in liste if a.get("kopf_fuss")),
            "atome_fussnote": sum(1 for a in liste if a["label"] == "footnote"),
            "atome_tabelle": sum(1 for a in liste if a["label"] in at.TABELLEN),
            "atome_ocr": sum(1 for a in liste if a.get("ocr")),
            "kv_bereiche": len(kv_runs), "kv_atome": sum(len(r) for r in kv_runs.values()),
            "kv_paare_verschraenkt": verschraenkt,
            "atome_bezug_frage": sum(1 for a in liste if hat_merkmal(a, "answer_reference")),
            "atome_marker_im_atom": sum(1 for a in liste if hat_merkmal(a, "marker_inside")),
            "atome_drittel_verletzt": sum(1 for a in liste if hat_merkmal(a, "thirds_rule_violated")),
            "atome_seitenwechsel_zurueck": sum(1 for a in liste if hat_merkmal(a, "page_break_back")),
            "atome_ueber_vorgaenger": sum(1 for a in liste if hat_merkmal(a, "above_previous")),
            "atome_spaltenteil": sum(1 for a in liste if hat_merkmal(a, "column_part")),
            "atome_mehrere_saetze": sum(1 for a in liste if len(a.get("satzanfaenge") or []) > 0),
            "atome_satz_ohne_leerzeichen": sum(1 for a in liste
                                               if re.search(r"[a-zäöüéèà]{2}[.!?:][A-ZÄÖÜÀ-Ý][a-zäöü]", a["text"])),
            "eingabe_zeichen": len(eingabe),
            "eingabe_tokens_schaetzung": round((len(eingabe) + anleitung_zeichen) / at.ZEICHEN_JE_TOKEN),
        })
    felder = list(max(zeilen, key=len))
    with (ANALYSE / "taxonomie_kennzahlen.csv").open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=felder)
        wr.writeheader()
        wr.writerows(zeilen)
    ok = [r for r in zeilen if r.get("status") == "success"]
    print(f"Dokumente {len(zeilen)}, zerlegt {len(ok)}; Anleitung {anleitung_zeichen} Zeichen "
          f"(≈ {round(anleitung_zeichen / at.ZEICHEN_JE_TOKEN)} Tokens); Prompt-Hash {prompt_hash()[:12]}…")
    for kl in ("digital", "scan"):
        t = [r for r in ok if r["klasse"] == kl]
        a = [r["atome"] for r in t]
        print(f"  {kl}: {len(t)} Dokumente, Atome Summe {sum(a)}, Median {statistics.median(a)}, "
              f"Min {min(a)}, Max {max(a)}")
    def s(k):
        return sum(r[k] for r in ok)
    print(f"Atome {s('atome')}: mit Text {s('atome_mit_text')}, ohne Text {s('atome_ohne_text')}, "
          f"Seitenmobiliar {s('atome_seitenmobiliar')}, Fussnote {s('atome_fussnote')}, "
          f"Tabelle {s('atome_tabelle')}, OCR {s('atome_ocr')}")
    print(f"Schlüssel-Wert: {s('kv_bereiche')} Bereiche, {s('kv_atome')} Atome; verschränkte Paare "
          f"{s('kv_paare_verschraenkt')} in {[r['zelle'] for r in ok if r['kv_paare_verschraenkt']]}")
    print(f"Antwortmarker am Atomanfang {s('atome_bezug_frage')}, mitten im Atom {s('atome_marker_im_atom')}; "
          f"Drittel-Regel verletzt {s('atome_drittel_verletzt')} {[r['zelle'] for r in ok if r['atome_drittel_verletzt']]}; "
          f"Satzende ohne Leerzeichen im Atom {s('atome_satz_ohne_leerzeichen')} "
          f"{[r['zelle'] for r in ok if r['atome_satz_ohne_leerzeichen']]}")
    print(f"Lesereihenfolge: Seitenwechsel zurück {s('atome_seitenwechsel_zurueck')}, über Vorgänger "
          f"{s('atome_ueber_vorgaenger')} in {[r['zelle'] for r in ok if r['atome_ueber_vorgaenger']]}; "
          f"Spaltenteile {s('atome_spaltenteil')}; Atome mit Satzanfang im Innern {s('atome_mehrere_saetze')}")
    et = sorted(r["eingabe_tokens_schaetzung"] for r in ok)
    print(f"Eingabe-Tokens je Aufruf (Schätzung): Median {statistics.median(et)}, ohne B2 max "
          f"{max(r['eingabe_tokens_schaetzung'] for r in ok if r['zelle'] != 'B2')}, B2 "
          f"{next((r['eingabe_tokens_schaetzung'] for r in ok if r['zelle'] == 'B2'), '–')}")
    print(f"geschrieben: {ANALYSE / 'taxonomie_kennzahlen.csv'}")


def tabellen() -> None:
    """Typen- und Abschnittstabellen als Markdown (für isolierung-strategie.md, damit Doku und Code
    übereinstimmen)."""
    print("| Schlüssel | Bezeichnung | Gruppe | Abschnitt | I95 TextType | K95 TextType | HTML | quoted | number | refers_to | Einschub | Kern | Lehrer-Rolle |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for t in UNIT_TYPES:
        if t.section:
            sec = SECTION[t.section]
            i95, k95 = sec.i95_text_type or "–", sec.k95_text_type or (
                "Slot title" if sec.k95_match == "slot" else "–")
            if sec.k95_match == "merged":
                k95 = "response (zusammengelegt)"
            ab = t.section
        else:
            i95 = k95 = "–" if len(t.sections) == 1 else "wie zugehöriger Teil"
            ab = "null" if len(t.sections) == 1 else "wie zugehöriger Teil"
        rel = f"{t.relation} → {', '.join(sorted(t.targets))}" if t.targets else (t.relation or "–")
        print(f"| `{t.key}` | {t.label_de} | {t.group} | {ab} | {i95} | {k95} | {t.html} | "
              f"{'ja' if t.quotable else '–'} | {'ja' if t.numbered else '–'} | {rel} | "
              f"{'ja' if t.insert else '–'} | {'ja' if t.core else '–'} | `{t.teacher_role}` |")
    print()
    print("| Abschnitt | Bezeichnung | Form | I95 (input/schema.yaml) | K95 (Kern v0.2.0) | Bemerkung |")
    print("|---|---|---|---|---|---|")
    for s in SECTIONS:
        i95 = f"`{s.i95_text_type}` an {s.i95_slot}" if s.i95_text_type else "–"
        k95 = (f"`{s.k95_text_type}` an {s.k95_slot}" if s.k95_text_type else
               (s.k95_slot or "–"))
        print(f"| `{s.key}` | {s.label_de} | {s.form} | {i95} ({s.i95_match}) | {k95} ({s.k95_match}) | {s.note} |")


# ================================================================ Selbsttest


def _synth(n: int) -> list[dict]:
    return [{"id": f"B{i}.1", "block": f"B{i}", "zeile": 1, "label": "text", "text": f"Satz {i}.",
             "eltern": None, "eltern_ref": None, "kopf_fuss": None, "seite": 1, "ocr": False,
             "zeichen": [0, 0], "hinweise": [], "kv": None}
            for i in range(1, n + 1)]


def _e(uid, typ, bereiche, section=None, refers_to=None, number=None, quoted=False):
    return {"id": uid, "type": typ, "atoms": [{"from": f"B{a}.1", "to": f"B{b}.1"} for a, b in bereiche],
            "section": section, "refers_to": refers_to or [], "number": number or [], "quoted": quoted}


def _synth_dok(liste: list[dict], texte: list[str]) -> dict:
    """Kunstdokument: setzt Texte und Zeichenbereiche der Atome, gibt ein Docling-artiges Objekt."""
    teile, p = [], 0
    for a, t in zip(liste, texte):
        if teile:
            teile.append("\n\n")
            p += 2
        a["text"], a["zeichen"] = t, [p, p + len(t)]
        teile.append(t)
        p += len(t)
    return {"text_gesamt": "".join(teile), "bloecke": []}


def selbsttest() -> None:
    ok = gesamt = 0

    def check(bed, text):
        nonlocal ok, gesamt
        gesamt += 1
        ok += bool(bed)
        if not bed:
            print("  FEHLER:", text)

    # Konsistenz der Konstanten
    check(len(TYPE_KEYS) == len(set(TYPE_KEYS)), "Typschlüssel eindeutig")
    check(all(re.fullmatch(r"[a-z][a-z_]*", k) for k in TYPE_KEYS + SECTION_KEYS), "Schlüssel snake_case")
    check({t.section for t in UNIT_TYPES} - {None} <= set(SECTION_KEYS), "Abschnitte gültig")
    check(set(SECTION_KEYS) <= {a for t in UNIT_TYPES for a in t.sections}, "jeder Abschnitt erreichbar")
    check(all(t.section in t.sections for t in UNIT_TYPES), "Standardabschnitt erlaubt")
    check(all(bool(t.targets) == (t.relation == "answers") for t in UNIT_TYPES), "Bezugsziele nur bei answers")
    i95 = {"title", "short_title", "submitted", "reasoning", "response", "recommendation", "summary"}
    k95 = {"main_text", "reasoning", "response", "official_communication", "note"}
    check({s.i95_text_type for s in SECTIONS} - {None} == i95, "alle 7 I95-Texttypen abgebildet")
    check({s.k95_text_type for s in SECTIONS} - {None} | set(OHNE_GEGENSTUECK["k95"]) == k95,
          "K95-Texttypen abgebildet oder als ohne Gegenstück geführt")
    check(set(LEHRER_ZU_TYP) >= {"title", "submitted", "question", "response", "metadata", "other"},
          "Lehrer-Rollen abgebildet")
    check(len(prompt_hash()) == 64 and "units" in anleitung(), "Prompt baut")
    beispiel = json.loads(BEISPIEL_AUSGABE)
    b_liste = []
    for zeile in BEISPIEL_EINGABE.splitlines()[1:]:
        aid, seite, hinw, text = [x.strip() for x in zeile.split("|", 3)]
        b_liste.append({"id": aid, "block": aid.split(".")[0], "seite": int(seite), "label": "text",
                        "text": text, "hinweise": [h for h in hinw.split(", ") if h],
                        "kopf_fuss": ("kopf" if "Kopfzeile" in hinw else "fuss" if "Fusszeile" in hinw else None),
                        "eltern": None, "eltern_ref": None})
    fb, _ = pruefe_zerlegung(beispiel, b_liste)
    check(not fb, f"Beispiel im Prompt gültig: {fb}")
    # Referenz: 10 Atome
    liste = _synth(10)
    ids = [a["id"] for a in liste]
    ref = {"units": [
        _e("E1", "header_footer", [(1, 1)]),
        _e("E2", "title", [(2, 2)], "title"),
        _e("E3", "question", [(3, 3)], "submitted_text", number=["1"], quoted=True),
        _e("E4", "question", [(4, 4)], "submitted_text", number=["2"], quoted=True),
        _e("E5", "answer", [(5, 6), (8, 8)], "response", ["E3"], ["1"]),
        _e("E6", "header_footer", [(7, 7)]),
        _e("E7", "answer", [(9, 9)], "response", ["E4"], ["2"]),
        _e("E8", "signature", [(10, 10)])],
        "atoms_with_boundary": [], "uncertain": []}
    f, _w = pruefe_zerlegung(ref, liste)
    check(not f, f"Referenz gültig: {f}")
    check(json_schema(ids)["properties"]["units"]["items"]["properties"]["type"]["enum"] == TYPE_KEYS,
          "Schema enthält Typen")

    def fehler(units, muster, lst=liste, **extra):
        f_, _ = pruefe_zerlegung({"units": units, **extra}, lst)
        check(any(muster in x for x in f_), f"erwartet «{muster}», erhalten {f_}")

    basis = ref["units"]
    fehler([x for x in basis if x["id"] != "E8"], "Lücke")
    fehler(basis[:-1] + [_e("E8", "signature", [(9, 10)])], "Überlappung")
    fehler(basis[:4] + [_e("E5", "answer", [(5, 6), (9, 9)], "response", ["E3"]),
                        _e("E6", "header_footer", [(7, 7)]), _e("E7", "answer", [(8, 8)], "response"),
                        basis[7]], "zwischen den Bereichen")
    fehler([_e("E1", "header_footer", [(1, 1)], "response")] + basis[1:], "section")
    fehler(basis[:7] + [_e("E8", "letter_element", [(10, 10)], quoted=True)], "quoted bei Typ")
    fehler(basis[:6] + [_e("E7", "answer", [(9, 9)], "response", ["E2"])] + basis[7:], "keine question")
    fehler(basis[:7] + [_e("E8", "gibtsnicht", [(10, 10)])], "unbekannter Typ")
    fehler(basis[:7] + [_e("E8", "signature", [(10, 11)])], "unbekannte Atom-ID")
    fehler(basis[:1] + [_e("E2", "title", [(2, 2)], "title", number=["1"])] + basis[2:], "number bei Typ")
    fehler(basis[:7] + [_e("E8", "signature", [(10, 10)], refers_to=["E2"])], "refers_to bei Typ")
    fehler(basis, "unbekannte ID", atoms_with_boundary=["B99.1"])
    fehler([dict(basis[0], atoms=[["B1.1", "B1.1"]])] + basis[1:], "nicht {")
    # quoted → Original in anderem Dokument ist erlaubt
    f2, _ = pruefe_zerlegung({"units": basis[:2] + [_e("E3", "question", [(3, 3)], "submitted_text",
                                                         ["57461#E5"], ["1"], True)] + basis[3:]}, liste)
    check(not f2, f"quoted mit externem Original gültig: {f2}")
    # Schlüssel-Wert-Bereich: K, K, W, W verschränkt
    kv = _synth(5)
    for a in kv[:4]:
        a["eltern"], a["eltern_ref"] = "key_value_area", "#/groups/0"
    kv_units = [_e("E1", "metadata_field", [(1, 1), (3, 3)]), _e("E2", "metadata_field", [(2, 2), (4, 4)]),
                _e("E3", "title", [(5, 5)], "title")]
    check(not pruefe_zerlegung({"units": kv_units}, kv)[0], "KV verschränkt gültig")
    kv[1]["eltern_ref"] = "#/groups/1"
    fehler(kv_units, "zwischen den Bereichen", lst=kv)
    # Einschub aus Seitenmobiliar: procedural_note in der Fusszeile trennt Bereiche nicht
    lm = _synth(4)
    lm[1]["kopf_fuss"] = "fuss"
    check(not pruefe_zerlegung({"units": [_e("E1", "answer", [(1, 1), (3, 3)], "response"),
                                          _e("E2", "procedural_note", [(2, 2)], "note"),
                                          _e("E3", "signature", [(4, 4)])]}, lm)[0],
          "Vermerk im Seitenmobiliar als Einschub")
    # Lesereihenfolge-Defekt: Block mit verletzter Drittel-Regel darf zwischen Bereichen liegen
    ld = _synth(4)
    ld[1]["merkmale"] = [["thirds_rule_violated", None]]
    lu = [_e("E1", "answer", [(1, 1), (3, 3)], "response"), _e("E2", "letter_element", [(2, 2)]),
          _e("E3", "signature", [(4, 4)])]
    check(not pruefe_zerlegung({"units": lu}, ld)[0], "Lücke über Block mit Lesereihenfolge-Defekt gültig")
    ld[1]["merkmale"] = []
    fehler(lu, "zwischen den Bereichen", lst=ld)
    # Warnung: Vorstoss-Text im Antwortdokument nicht quoted
    _, w3 = pruefe_zerlegung({"units": basis[:2] + [dict(basis[2], quoted=False)] + basis[3:]}, liste)
    check(any("nicht quoted" in x for x in w3), f"Warnung quoted: {w3}")
    # Normalisierung: drei Unterschriftszeilen mit Bild dazwischen werden eine Einheit
    ln = _synth(6)
    nu = [_e("E1", "answer", [(1, 2)], "response"), _e("E2", "signature", [(3, 3)]),
          _e("E3", "picture", [(4, 4)]), _e("E4", "signature", [(5, 5)]), _e("E5", "signature", [(6, 6)])]
    norm, prot = normalisieren({"units": nu}, ln)
    check([u["type"] for u in norm["units"]] == ["answer", "signature", "picture"]
          and norm["units"][1]["atoms"] == [{"from": "B3.1", "to": "B3.1"}, {"from": "B5.1", "to": "B6.1"}]
          and not pruefe_zerlegung(norm, ln)[0] and len(prot) == 2, f"Normalisierung {norm} {prot}")
    norm2, _ = normalisieren(ref, liste)
    check([u["type"] for u in norm2["units"]] == [u["type"] for u in ref["units"]]
          and norm2["units"][4]["refers_to"] == ["E3"], "Normalisierung lässt Fragen und Antworten getrennt")
    # Kandidatengrenzen: Blockwechsel und Merkmale
    lk = _synth(3)
    lk[1]["block"] = lk[0]["block"]
    lk[2]["block"] = lk[0]["block"]
    lk[2]["merkmale"] = [["answer_reference", "2"]]
    check(kandidaten(lk) == {1}, f"Kandidaten {kandidaten(lk)}")
    # Messgrössen
    m = vergleiche(ref, ref, ids)
    check(m["grenzen_tp"] == m["grenzen_ref"] == m["grenzen_hyp"] and m["pk"] == 0 and m["windowdiff"] == 0,
          "identisch: alle Grenzen, Pk 0")
    check(m["bezug_tp"] == m["bezug_ref"] == 2 and m["textblock_ok"] == m["textblock_n"], "identisch: Bezüge")
    hyp = {"units": [
        _e("E1", "header_footer", [(1, 1)]), _e("E2", "title", [(2, 2)], "title"),
        _e("E3", "question", [(3, 4)], "submitted_text", quoted=True),
        _e("E4", "answer", [(5, 8)], "response", ["E3"]),
        _e("E5", "answer", [(9, 9)], "response", ["E3"]),
        _e("E6", "signature", [(10, 10)])]}
    check(not pruefe_zerlegung(hyp, liste)[0], "Hypothese gültig")
    m = vergleiche(ref, hyp, ids)
    check((m["grenzen_tp"], m["grenzen_hyp"], m["grenzen_ref"]) == (5, 5, 8), f"Grenzen {m}")
    check(m["einheiten_exakt"] == 4 and m["typ_ok"] == 4, f"gleiche Einheiten {m['einheiten_exakt']}")
    check(m["bezug_tp"] == 1 and m["bezug_ref"] == 2, f"Bezüge {m['bezug_tp']}/{m['bezug_hyp']}/{m['bezug_ref']}")
    check(m["abschnitt_ok"] == 9, f"Abschnitt je Atom {m['abschnitt_ok']}")
    check(0 < m["pk"] < 1 and 0 < m["windowdiff"] < 1, "Pk/WindowDiff im Bereich")
    check(grenzen_prf([1, 1, 2, 2], [1, 2, 2, 2], toleranz=1)[0] == 1, "Toleranz 1")
    zf = zusammenfassen([vergleiche(ref, ref, ids)], gueltig=1.0, atome_mit_text=10)
    check(all(ok_ for _, _, ok_ in gate_pruefen(zf, "digital").values()), f"Gate identisch {zf}")
    check(not all(ok_ for _, _, ok_ in gate_pruefen(zusammenfassen([m], 1.0, 10), "scan").values()),
          "Gate verfehlt bei Fehlern")
    # Richtext
    check(_trennstrich_weg("gemein-", "nützige Zwecke", "") == "weg", "Silbentrennung")
    check(_trennstrich_weg("Lager-", "und Umschlag", "") == "leer", "Konjunktion")
    check(_trennstrich_weg("Rotterdam-", "Strasse 3", "") == "halten", "Grossbuchstabe")
    check(_trennstrich_weg("il est peut-", "être", "") == "halten", "französische Zusammensetzung")
    check(_trennstrich_weg("die E-", "mail", "die e-mail kam") == "halten", "Bindestrich-Form im Dokument")
    liste = _synth(10)
    for i in (2, 3):
        liste[i]["label"] = "list_item"
    dok = _synth_dok(liste, ["- 1 -", "Titel <A&B>", "1. Erste Frage?", "2. Zweite Frage?", "Zu Frage 1:",
                             "Antwort gemein-", "- 2 -", "nützig.", "Antwort zwei.", "Ort, Datum"])
    liste[5]["block"] = liste[4]["block"] = "B5"   # Marker und Antwort im selben Block
    liste[7]["block"] = "B5"                        # Fortsetzung nach der Kopfzeile, selber Block
    r = {(tb["section"], tb["quoted"]): tb for tb in richtext(ref, liste, dok)}
    check(r[("title", False)]["text"] == "Titel <A&B>", f"Titel als Klartext: {r[('title', False)]['text']}")
    check(r[("submitted_text", True)]["text"] == "<ol><li>Erste Frage?</li><li>Zweite Frage?</li></ol>",
          f"Liste: {r[('submitted_text', True)]['text']}")
    check(r[("response", False)]["text"] == "<p>Zu Frage 1: Antwort gemeinnützig.</p><p>Antwort zwei.</p>",
          f"Antwort: {r[('response', False)]['text']}")
    check(r[("response", False)]["units"][0]["html_ranges"] == [[0, 40]],
          f"HTML-Bereich der Einheit {r[('response', False)]['units'][0]['html_ranges']}")
    pr_ = richtext_pruefen(list(r.values()), ref, liste, dok)
    check(not pr_, f"Richtext-Prüfung {pr_}")
    kaputt = [dict(tb) for tb in r.values()]
    for tb in kaputt:
        if tb["section"] == "response":
            tb["text"] = tb["text"].replace("zwei", "drei")
    check(any("weicht" in x for x in richtext_pruefen(kaputt, ref, liste, dok)), "Textänderung erkannt")
    e_i95 = ech_texte(list(r.values()), "i95", "de", "https://example.org/x.pdf")
    check([t["text_block"]["text_type"] for t in e_i95["texts"]] == ["title", "response"]
          and e_i95["not_mappable"][0]["reason"].startswith("zitiert"), f"I95: {e_i95}")
    e_k95 = ech_texte(richtext(ref, liste, dok, ZUSAMMENLEGEN_K95), "k95", "de", None)
    check(e_k95["texts"][0]["slot"].startswith("Affair.title")
          and e_k95["texts"][1]["text_block"]["text_type"] == "response", f"K95: {e_k95}")

    # ---- Runde 2: isolierung-v2.1, atome-v3, Übertragung
    check(prompt_hash() == "04a6a73d8bb9f9df367fff76a03717f84e4da6a1b649f5ff66f3e9626dd54fa8",
          "Prompt isolierung-v2 unverändert (Runde 1 nachrechenbar)")
    a2, a21 = anleitung(), anleitung(SCHEMA_V21)
    check(a21.startswith(EINLEITUNG) and REGELN in a21 and "Beispiel 2" in a21 and "Beispiel 2" not in a2
          and "«Domanda 1»" in a21 and "«Domanda 1»" not in a2 and prompt_hash(SCHEMA_V21) != prompt_hash(),
          "Prompt isolierung-v2.1: Grenzfälle und Beispiel 2 nur dort")
    check(not re.search(r"\b[BKGSL]\d{1,2}\b", typenliste(SCHEMA_V21)), "Grenzfälle v2.1 ohne Zellen-Kürzel")
    b2_liste = []
    for zeile in BEISPIEL2_EINGABE.splitlines()[1:]:
        aid, seite, hinw, text = [x.strip() for x in zeile.split("|", 3)]
        b2_liste.append({"id": aid, "block": aid.split(".")[0], "seite": int(seite), "label": "text", "text": text,
                         "hinweise": [h for h in hinw.split(", ") if h], "eltern": None, "eltern_ref": None,
                         "kopf_fuss": "fuss" if "Fusszeile" in hinw else None})
    fb2, _ = pruefe_zerlegung(json.loads(BEISPIEL2_AUSGABE), b2_liste, SCHEMA_V21)
    check(not fb2, f"Beispiel 2 gültig: {fb2}")
    # Regel 7: quoted ohne Antwort oder Beschluss: v2 Warnung, v2.1 Fehler
    vq = {"units": [_e("E1", "title", [(1, 1)], "title"), _e("E2", "question", [(2, 3)], "submitted_text",
                                                               number=["1"], quoted=True)]}
    l3 = _synth(3)
    f_v2, w_v2 = pruefe_zerlegung(vq, l3)
    f_v21, _ = pruefe_zerlegung(vq, l3, SCHEMA_V21)
    check(not f_v2 and any("keine Antwort" in x for x in w_v2) and any(x.startswith("Regel 7") for x in f_v21),
          f"Regel 7 v2/v2.1: {f_v2} {w_v2} {f_v21}")
    check(any("quoted false" in x for x in reparaturhinweise(f_v21, vq, l3)), "Reparaturhinweis Regel 7")
    # answer beginnt mit Fragemarker: Warnung nur in v2.1
    lf = _synth(4)
    lf[2]["merkmale"] = [["question_number", "1"]]
    uf = {"units": [_e("E1", "title", [(1, 1)], "title"), _e("E2", "question", [(2, 2)], "submitted_text",
                                                               number=["1"], quoted=True),
                    _e("E3", "answer", [(3, 4)], "response", ["E2"], ["1"])]}
    _, wf2 = pruefe_zerlegung(uf, lf)
    ff21, wf21 = pruefe_zerlegung(uf, lf, SCHEMA_V21)
    check(not ff21 and any("Fragemarker" in x for x in wf21) and not any("Fragemarker" in x for x in wf2),
          f"Warnung Fragemarker {wf21}")
    # Reparaturhinweis bei einer Lücke nennt die Nachbareinheiten
    ul = {"units": [_e("E1", "title", [(1, 1)], "title"), _e("E2", "signature", [(3, 4)])]}
    fl, _ = pruefe_zerlegung(ul, lf)
    rh = reparaturhinweise(fl, ul, lf)
    check(any("B2.1" in x and "E1 (title" in x and "E2 (signature" in x for x in rh), f"Hinweis Lücke {rh}")
    # Kandidaten: Merkmale aus atome-v3
    lk3 = _synth(3)
    for a in lk3:
        a["block"] = "B1"
    lk3[2]["merkmale"] = [["number_sequence", "22"]]
    check(kandidaten(lk3) == {1}, f"Kandidat Folgenummer {kandidaten(lk3)}")
    # Übertragung: Atom mit Grenze in zwei Teile geteilt → zweiter Teil zur nächsten Einheit
    alt = _synth(3)
    _synth_dok(alt, ["Titel.Am Montag", "reichte X ein:", "Text"])
    neu = [dict(alt[0], id="B1.1.1", text="Titel.", zeichen=[0, 6]),
           dict(alt[0], id="B1.1.2", text="Am Montag", zeichen=[6, 15])] + [dict(a) for a in alt[1:]]
    ref_u = {"_atome": {"x": 1}, "units": [_e("E1", "title", [(1, 1)], "title"), _e("E2", "sponsor_info", [(2, 2)]),
                                          _e("E3", "submitted_text", [(3, 3)], "submitted_text")],
             "atoms_with_boundary": ["B1.1"], "uncertain": []}
    ue, prot_ = uebertragen(ref_u, alt, neu)
    check([(u["id"], [(b["from"], b["to"]) for b in u["atoms"]]) for u in ue["units"]]
          == [("E1", [("B1.1.1", "B1.1.1")]), ("E2", [("B1.1.2", "B2.1")]), ("E3", [("B3.1", "B3.1")])]
          and ue["atoms_with_boundary"] == [] and ue["_atome"] == {"x": 1} and len(prot_) == 1
          and not uebertragung_pruefen(ref_u, ue, alt, neu), f"Übertragung mit Grenze {ue} {prot_}")
    ue2, _ = uebertragen(dict(ref_u, atoms_with_boundary=[]), alt, neu)
    check(ue2["units"][0]["atoms"] == [{"from": "B1.1.1", "to": "B1.1.2"}], "Übertragung ohne Grenze: Teile bleiben")
    for kaputt, was in ((list(reversed(neu)), "Umordnung"), (neu[:1] + neu[2:], "fehlender Teil")):
        try:
            uebertragen(ref_u, alt, kaputt)
            check(False, f"Übertragung bei {was} nicht abgebrochen")
        except ValueError:
            check(True, was)
    print(f"Selbsttest: {ok} von {gesamt} Prüfpunkten bestanden")
    if ok != gesamt:
        sys.exit(1)


# ================================================================ Kommandozeile


def zeige(doc_id: str, schema: str = SCHEMA_VERSION) -> None:
    print(nachrichten(atome_laden(doc_id, atome=ATOME_ZU_SCHEMA[schema]), schema)[1]["content"])


def pruefe_datei(pfad: str, doc_id: str) -> None:
    dok = lade(doc_id)
    liste = atome_laden(doc_id, dok)
    roh = json.loads(Path(pfad).read_text(encoding="utf-8"))
    if warnung := atome_passen(roh, liste):
        print("Achtung:", warnung)
    ausgabe = ohne_herkunft(roh)
    if "ausgabe" in ausgabe and "units" not in ausgabe:   # Ablage des Rauchtests
        ausgabe = ausgabe["ausgabe"] or {}
    f, w = pruefe_zerlegung(ausgabe, liste)
    print(f"Fehler {len(f)}, Warnungen {len(w)}")
    for x in f:
        print("  F:", x)
    for x in w:
        print("  W:", x)
    if f:
        return
    for name, zl in (("I95", None), ("K95", ZUSAMMENLEGEN_K95)):
        r = richtext(ausgabe, liste, dok, zl)
        rp = richtext_pruefen(r, ausgabe, liste, dok)
        print(f"Richtext {name}: {len(r)} TextBlocks; Prüfung {'ok' if not rp else rp}")
        for tb in r:
            ch = tb["changes"]
            print(f"  {tb['section']}{' (quoted)' if tb['quoted'] else ''}: {len(tb['text'])} Zeichen, "
                  f"{len(tb['units'])} Einheiten, Trennstriche {len(ch['hyphen_removed'])}, Listenmarker "
                  f"{len(ch['list_marker_removed'])}, leere Atome {len(ch['empty_atoms'])}")


REF_QUELLEN = ("ref_a", "ref_b", "ref_c", "referenz_entwurf")
RUNDE2 = PROJEKT / "daten" / "isolierung" / "runde2"


def uebertragung_pruefen(alt_aus: dict, neu_aus: dict, alt: list[dict], neu: list[dict]) -> list[str]:
    """Befunde (leer = in Ordnung): Zerlegung nach isolierung-v2 und -v2.1 gültig, normalisierbar, und je
    Einheit dieselben Zeichen (ohne Leerraum) wie vorher, ausser den nach Regel 10 verschobenen Teilen."""
    bef = []
    for schema in SCHEMATA:
        f, _ = pruefe_zerlegung(neu_aus, neu, schema)
        if f:
            bef.append(f"{schema}: {f[:2]}")
    if not bef:
        norm, _ = normalisieren(neu_aus, neu)
        if pruefe_zerlegung(norm, neu)[0]:
            bef.append("normalisiert ungültig")

    def zeichen(aus: dict, liste: list[dict]) -> dict[str, set[int]]:
        z = zuordnung(ohne_herkunft(aus), [a["id"] for a in liste])
        m: dict[str, set[int]] = {}
        for u, a in zip(z, liste):
            m.setdefault(u, set()).update(i for i in range(*a["zeichen"]) if not a["text"][i - a["zeichen"][0]].isspace())
        return m
    za, zn = zeichen(alt_aus, alt), zeichen(neu_aus, neu)
    verschoben = sum(len(za[u] ^ zn.get(u, set())) for u in za)
    if set(za) != set(zn):
        bef.append("andere Einheiten")
    awb_alt = set(ohne_herkunft(alt_aus).get("atoms_with_boundary") or [])
    awb_neu = set(ohne_herkunft(neu_aus).get("atoms_with_boundary") or [])
    if verschoben and not (awb_alt - awb_neu):
        bef.append(f"{verschoben} Zeichen in anderer Einheit ohne aufgelöste Grenze")
    return bef


def uebertragen_referenzen() -> None:
    """Runde 2: alle Referenzen (ref_a, ref_b, ref_c, referenz_entwurf) von atome-v2 auf atome-v3 übertragen
    und nach daten/isolierung/runde2/<quelle>/ schreiben; die Originale bleiben unverändert (Prüfsumme vor und
    nach). Bricht ab, wenn eine Übertragung nicht eindeutig oder danach ungültig ist."""
    bericht = {"erzeugt_utc": datetime.now(UTC).isoformat(timespec="seconds"), "von": "atome-v2", "nach": "atome-v3", "regel": uebertragen.__doc__.split("\n")[0],
        "dateien": []}
    for q in REF_QUELLEN:
        (RUNDE2 / q).mkdir(parents=True, exist_ok=True)
        for p in sorted((PROJEKT / "daten" / "isolierung" / q).glob("*.json")):
            d = p.stem
            sha_vor = _sha256(p)
            roh = json.loads(p.read_text(encoding="utf-8"))
            dok = lade(d)
            alt, neu = atome_laden(d, dok), atome_laden(d, dok, "atome-v3")
            if warn := atome_passen(roh, alt):
                raise SystemExit(f"{q}/{d}: {warn}")
            neu_aus, prot = uebertragen(roh, alt, neu)
            bef = uebertragung_pruefen(roh, neu_aus, alt, neu)
            if bef:
                raise SystemExit(f"{q}/{d}: Übertragung nicht sauber: {bef}")
            neu_aus["_atome"] = atome_kopf(d, "atome-v3")
            neu_aus["_uebertragung"] = {"quelle": str(p.relative_to(PROJEKT)), "quelle_sha256": sha_vor,
                                        "von": roh.get("_atome"), "nach": "atome-v3",
                                        "skript": "src/m03_isolierung_taxonomie.py --uebertragen",
                                        "protokoll": prot}
            ziel = RUNDE2 / q / p.name
            ziel.write_text(json.dumps(neu_aus, ensure_ascii=False, indent=1), encoding="utf-8")
            if _sha256(p) != sha_vor:
                raise SystemExit(f"{p} wurde verändert")
            bericht["dateien"].append({"quelle": q, "doc_id": d, "einheiten": len(neu_aus["units"]),
                                       "atome_alt": len(alt), "atome_neu": len(neu), "aenderungen": prot,
                                       "quelle_sha256": sha_vor, "ziel_sha256": _sha256(ziel), "befunde": bef})
            if prot:
                print(f"{q}/{d}: {len(prot)} Änderungen: {prot}")
    (RUNDE2 / "referenzen_uebertragung.json").write_text(json.dumps(bericht, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    n = len(bericht["dateien"])
    print(f"übertragen: {n} Referenzdateien, davon mit Änderungen {sum(bool(x['aenderungen']) for x in bericht['dateien'])}; "
          f"alle gültig nach isolierung-v2 und -v2.1; geschrieben: {RUNDE2.relative_to(PROJEKT)}/<quelle>/, "
          f"referenzen_uebertragung.json")


def basislinie(doc_id: str, ref_pfad: str) -> None:
    liste = atome_laden(doc_id)
    ids = [a["id"] for a in liste]
    roh = json.loads(Path(ref_pfad).read_text(encoding="utf-8"))
    if warnung := atome_passen(roh, liste):
        print("Achtung:", warnung)
    ref = ohne_herkunft(roh)
    print("Docling-Blöcke als Einheiten gegen Referenz:")
    print("  " + kennzahlen_ausgeben(vergleiche(ref, basislinie_docling(liste), ids)))
    ka = kandidaten_abdeckung(ref, liste)
    print(f"Kandidatengrenzen (Regeln, E16): {ka['kandidaten']} von {ka['atomgrenzen']} Atomgrenzen; "
          f"Referenzgrenzen auf Kandidaten {ka['auf_kandidaten']}/{ka['ref_grenzen']}, verpasst vor {ka['verpasst_vor']}")


if __name__ == "__main__":
    arg = sys.argv[1:]
    if not arg or arg[0] == "--selbsttest":
        selbsttest()
    elif arg[0] == "--kennzahlen":
        kennzahlen()
    elif arg[0] == "--tabellen":
        tabellen()
    elif arg[0] == "--zeige":
        zeige(arg[1], arg[2] if len(arg) > 2 else SCHEMA_VERSION)
    elif arg[0] == "--pruefe-datei":
        pruefe_datei(arg[1], arg[2])
    elif arg[0] == "--basislinie":
        basislinie(arg[1], arg[2])
    elif arg[0] == "--prompt-hash":
        print(prompt_hash(arg[1] if len(arg) > 1 else SCHEMA_VERSION))
    elif arg[0] == "--uebertragen":
        uebertragen_referenzen()
    else:
        print(__doc__)

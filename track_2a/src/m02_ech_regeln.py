# SPDX-License-Identifier: Apache-2.0
"""Teilfragen 2.5/2.6 (thema ech): Zuordnungsregeln OpenParlData -> eCH-0295.

Reines Regelmodul ohne Datenzugriff. Wird von m02_ech_abgleich.py importiert.
Quelle der Zielwerte: ech-0295_affairs/input/schema.yaml (I95) des eCH-Arbeitsrepositorys
https://github.com/swiss/political-affairs-ech-group, Commit 3cab44d
(AffairTypeEnum, SponsorRoleEnum, TextTypeEnum, RecommendationEnum, StatusEnum,
ProcedureStageEnum, ProcedureDecisionEnum, AssignmentStepTypeEnum, PlenaryDebateTypeEnum).

Match-Art (gilt fuer alle Zuordnungen):
  exakt   gleicher Begriff, 1:1
  nah     gleicher Begriff, Umfang leicht verschieden (Varianten, Dringlichkeit, Sprachform)
  weiter  nur teilweise deckungsgleich: die Quellklasse ist deutlich breiter oder enger,
          oder der Zielwert ist nur der naechstliegende
  keine   keine Entsprechung im eCH-0295-Wertebereich
  unbestimmt  Bezeichnung zu allgemein, Zuordnung nur mit Zusatzinformation moeglich

Alle Regeln sind Vorschlaege (Silber-Qualitaet), nicht amtlich geprueft.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------- Ebene

def ebene(body_key: str, body_type: str | None = None) -> str:
    if body_key == "CHE":
        return "Bund"
    if body_key == "LIE":
        return "Liechtenstein"
    if body_type == "canton" or (body_type is None and not body_key.isdigit()):
        return "Kanton"
    return "Gemeinde"


# ---------------------------------------------------------------- Vorstoss-Mengen

VORSTOSS_TYPEN = {"motion", "postulate", "interpellation", "request", "question",
                  "parliamentary_initiative", "motion_and_postulate", "motion_then_postulate"}
ANTRAG_TYPEN = {"motion", "postulate", "motion_and_postulate", "motion_then_postulate"}
ANTWORT_TYPEN = {"motion", "postulate", "interpellation", "request", "question",
                 "motion_and_postulate", "motion_then_postulate"}


# ---------------------------------------------------------------- Geschaeftstypen

# type_harmonized_id -> (eCH-Wert, Match-Art, Kategorie ohne Entsprechung, Bemerkung)
TYP_HARMONISIERT: dict[int | None, tuple[str, str, str, str]] = {
    2: ("motion", "exakt", "", "enthaelt lokal auch Richtlinienmotion, Auftrag (SO), Mozione"),
    3: ("postulate", "exakt", "", "enthaelt lokal auch Anzug (BS, Riehen) und dringliche Postulate"),
    8: ("interpellation", "exakt", "", "Dringlichkeit nur im lokalen Typ oder Titel"),
    12: ("request", "nah", "", "mischt schriftliche Anfragen mit Fragestunde-Fragen und muendlichen Fragen"),
    10: ("question", "nah", "", "teils Einzelfrage (Bund), teils Sammelgeschaeft einer Fragestunde (Vermutung)"),
    4: ("parliamentary_initiative", "exakt", "", ""),
    9: ("draft_decree", "weiter", "", "Regierungsgeschaeft ist breiter: Vorlagen, Berichte, Kredite, Gesetze"),
    17: ("draft_decree", "weiter", "", "Genehmigungsbeschluss des Parlaments"),
    6: ("", "keine", "Wahl", "Wahlgeschaefte; englisches Label im Export lautet 'Votaziun'"),
    16: ("", "keine", "Bericht", "Berichte; teils Umsetzungsbericht zu einem anderen Geschaeft (Etappe statt Typ)"),
    5: ("", "keine", "Vernehmlassung", "gehoert zu eCH-0297 (Konsultationen)"),
    15: ("", "keine", "Informationsdokument", ""),
    11: ("", "keine", "Petition", ""),
    7: ("", "keine", "Volks-/Einzel-/Behoerdeninitiative", ""),
    1: ("", "keine", "Diverses", ""),
    14: ("", "keine", "Einbuergerung", ""),
    13: ("", "keine", "Aenderungsantrag", "im eCH-Modell ein Proposition-Objekt einer Debatte, kein Geschaeft"),
    None: ("", "unbestimmt", "", "kein harmonisierter Typ; nur ueber lokale Bezeichnung zuordenbar"),
}

_R = lambda p: re.compile(p, re.I)  # noqa: E731

# (Regex auf lokale Typbezeichnung, eCH-Wert, Match-Art, Kategorie ohne Entsprechung)
# Reihenfolge zaehlt: erste passende Regel gewinnt.
TYP_LOKAL_REGELN: list[tuple[re.Pattern, str, str, str]] = [
    (_R(r"richtlinie"), "motion", "weiter", "Richtlinienmotion"),
    (_R(r"standesinitiative|kantonsinitiative|initiative cantonale|iniziativa cantonale"),
     "", "keine", "Standes-/Kantonsinitiative"),
    (_R(r"volksinitiative|einzelinitiative|initiative populaire|iniziativa popolare|"
        r"gemeindeinitiative|beh[öo]rdeninitiative|initiative communale|initiative individuelle|"
        r"volksbegehren|volksanregung"),
     "", "keine", "Volks-/Einzel-/Behoerdeninitiative"),
    (_R(r"volksmotion|volksauftrag|b[üu]rgermotion"), "motion", "weiter", "Volksmotion/Volksauftrag"),
    (_R(r"petition|p[ée]tition|petizion"), "", "keine", "Petition"),
    (_R(r"r[ée]solution|risoluzion"), "", "keine", "Resolution"),
    (_R(r"einb[üu]rgerung|naturalisation|naturalizzazion|b[üu]rgerrecht"), "", "keine", "Einbuergerung"),
    (_R(r"vernehmlassung|consultation|consultazion"), "", "keine", "Vernehmlassung"),
    (_R(r"erg[äa]nzungsantrag|amendement|emendament|[äa]nderungsantrag"), "", "keine", "Aenderungsantrag"),
    (_R(r"empfehlung|recommandation|raccomandazione"), "", "keine", "Empfehlung (Bund)"),
    (_R(r"fragestunde|question orale|questions? orales?|heure des questions|ora delle domande|"
        r"interrogazione orale|^frage$|^fragen$"), "question", "nah", ""),
    (_R(r"interpellation|interpellanz|interpellanza"), "interpellation", "exakt", ""),
    (_R(r"anfrage|interrogazion|question [ée]crite|questions? [ée]crites?|simple question|"
        r"questions? du conseil|auskunftsbegehren|^questions?$|^question urgente"),
     "request", "nah", ""),
    (_R(r"postula|anzug"), "postulate", "exakt", ""),
    (_R(r"motion|mozion|^auftrag$|^auftr[äa]ge$"), "motion", "exakt", ""),
    (_R(r"parlamentarische initiative|iniziativa parlamentare|initiative parlementaire|"
        r"parl\. ?initiative|\bpa\.? ?iv\b"), "parliamentary_initiative", "exakt", ""),
    (_R(r"wahl|[ée]lection|elezion|nomina|ernennung|inpflichtnahme|vereidigung|assermentation|"
        r"gew[äa]hlt|ersatzwahl|ratsmitglied|mutation"), "", "keine", "Wahl"),
    (_R(r"r[üu]cktritt|d[ée]mission|dimission"), "", "keine", "Ruecktritt"),
    (_R(r"erkl[äa]rung|d[ée]claration|dichiarazion|mitteilung|communication|information"),
     "", "keine", "Erklaerung/Mitteilung"),
    (_R(r"bericht und antrag|bericht & antrag|\bb\+a\b|vorlage|botschaft|weisung|ratschlag|"
        r"messagg|projet de loi|projet de d[ée]cret|d[ée]cret|dekret|gesetz|\bloi\b|kredit|"
        r"cr[ée]dit|beschluss|sachgesch[äa]ft|gesch[äa]ft des (bundesrates|stadtrat|gemeinderat|"
        r"regierung)|regierungsratsbeschluss|antrag|projet de d[ée]lib[ée]ration|pr[ée]avis|"
        r"proposition|rechtsetzung|gesetzgebung|verordnung|reglement|r[èe]glement|regolament|"
        r"budget|voranschlag|preventivo|rechnung|consuntivo|verwaltungsgesch[äa]ft|"
        r"ausgabenbericht|planungsbericht|richtplan|konzession|vertrag|convenzione"),
     "draft_decree", "weiter", ""),
    (_R(r"bericht|rapport|report|resoconto"), "", "keine", "Bericht"),
    (_R(r"divers|[üu]brige|andere|autres?\b|varie|vari\b|sonstige"), "", "keine", "Diverses"),
    (_R(r"vorstoss|vorst[öo]sse|intervention|atto parlamentare|politisches gesch[äa]ft|"
        r"gesch[äa]ft des parlaments|sachgesch|gesch[äa]ft"), "", "unbestimmt", ""),
]

DRINGLICH = _R(r"dringlich|dringend|urgen[tz]|urgente")


def typ_lokal(name: str | None) -> tuple[str, str, str]:
    """Lokale Typbezeichnung -> (eCH-Wert, Match-Art, Kategorie ohne Entsprechung)."""
    if not name or not name.strip():
        return "", "unbestimmt", ""
    s = name.strip()
    for rx, wert, art, kat in TYP_LOKAL_REGELN:
        if rx.search(s):
            if wert and art == "exakt" and (DRINGLICH.search(s) or s.lower() not in {
                    "motion", "postulat", "interpellation", "anfrage", "mozione", "interpellanza",
                    "postulato", "parlamentarische initiative", "iniziativa parlamentare",
                    "initiative parlementaire", "motions", "postulats", "interpellations"}):
                art = "nah"
            return wert, art, kat
    return "", "unbestimmt", ""


def typ_ech(harm_id: int | None, lokal: str | None) -> tuple[str, str, str, str]:
    """Kombinierte Zuordnung pro Geschaeft.

    Lokale Regel gewinnt, wenn sie bestimmt ist (spezifischer als die Harmonisierung),
    sonst gilt die Harmonisierung. Rueckgabe: (Wert, Match-Art, Kategorie, Quelle).
    """
    w, a, k = typ_lokal(lokal)
    if a != "unbestimmt":
        return w, a, k, "lokal"
    hw, ha, hk, _ = TYP_HARMONISIERT.get(harm_id, TYP_HARMONISIERT[None])
    return hw, ha, hk, ("harmonisiert" if harm_id is not None else "keine")


# ---------------------------------------------------------------- Rollen -> SponsorRoleEnum

# role_harmonized -> (Zielort im eCH-Modell, SponsorRole-Vorschlag, Match-Art, Bemerkung)
ROLLE_HARMONISIERT: dict[str, tuple[str, str, str, str]] = {
    "author": ("Submission.sponsorship", "sponsor", "weiter",
               "in vielen Parlamenten auch Mitunterzeichnende, Berichterstattende, Regierungsvertretung"),
    "cosign": ("Submission.sponsorship", "cosponsor", "exakt", "nur Bund"),
    "co-signer": ("Submission.sponsorship", "cosponsor", "exakt", ""),
    "primary": ("Submission.sponsorship", "sponsor", "exakt", ""),
    "assuming": ("Submission.sponsorship", "transferred", "exakt", "Bund: 'Uebernommen von'"),
    "party-group": ("Submission.sponsorship", "sponsor", "nah", "Fraktion als Urheberin"),
    "multigroup": ("Submission.sponsorship", "sponsor", "nah", "mehrere Fraktionen"),
    "interpartis": ("Submission.sponsorship", "sponsor", "nah", "interfraktionell"),
    "controvert": ("PlenaryDebateEvent.proposition (proposer)", "", "keine",
                   "Bekaempfer/in; keine Sponsor-Rolle"),
    "speaker": ("CommitteeDeliberationStep.spokesperson", "", "keine", "Sprecher/in"),
    "rapporteur": ("CommitteeDeliberationStep.spokesperson", "", "keine", "Berichterstatter/in"),
    "responder": ("ResponseStep.responder", "", "keine", "nur Liechtenstein"),
    "leading_department": ("AssignmentStep(executive_routing).assigned_to", "", "keine",
                           "federfuehrende Stelle, nicht die formell antwortende Exekutive"),
    "departement": ("AssignmentStep(executive_routing).assigned_to", "", "keine", ""),
    "assigned_committee": ("AssignmentStep(committee_referral).assigned_to", "", "keine", ""),
    "committee": ("CommitteeDeliberationStep.committee", "", "keine", ""),
    "council_initial": ("AssignmentStep(chamber_assignment).assigned_to", "", "keine", "Erstrat (Bund)"),
    "authority": ("Submission.sponsorship", "", "unbestimmt", "Behoerde als Einreicherin"),
    "citizen-initiative": ("", "", "keine", "Initiativkomitee"),
    "mentioned": ("", "", "keine", "nur bei news"),
    "publisher": ("", "", "keine", "nur bei news, kein Geschaeftsbezug"),
}

ROLLE_LOKAL_REGELN: list[tuple[re.Pattern, str]] = [
    (_R(r"[üu]bernommen|repris|ripreso|urheber/?in initial|ersatzurheber|stv\. urheber"), "transferred"),
    (_R(r"mitunterzeic|zweitunterzeich|drittunterzeich|miturheber|mitvorst[öo]ss|miteinreich|mitinterpell|mitmotion|mitpostul|cosign|"
        r"co-sign|cofirmat|coauteur|co-auteur|mitverfasser|mitantragsteller|cosottoscritt|"
        r"weitere unterzeich|mitunterst|cofirmatari"), "cosponsor"),
    (_R(r"berichterstatt|rapporteur|relator|sprecher|porte-parole|regierungsvertret|"
        r"repr[ée]sentant|kommission|commission|federf[üu]hr|zust[äa]ndig|beh[öo]rde|autorit|"
        r"keine funktion|direktion|departement|d[ée]partement|bek[äa]mpf|opposant|"
        r"antwortende|r[ée]pondant"), "andere"),
    (_R(r"erstunterzeich|hauptvorst[öo]ss|hauptunterzeich|urheber|auteur|autore|autor\b|"
        r"vorst[öo]sser|vorstossurheber|verfasser|fragesteller|presentat|primi firmatari|"
        r"primo firmatario|premier signataire|motion[äa]r|postulant|interpellant|einreicher|"
        r"eingereicht von|initiant|deposit|antragsteller|primo proponente"), "sponsor"),
    (_R(r"unterzeichner|signataire|firmatari|beteiligung|teilnehm"), "unbestimmt"),
]


def rolle_lokal(role_de: str | None, role_fr: str | None, role_it: str | None) -> str:
    s = " | ".join(x for x in (role_de, role_fr, role_it) if x)
    if not s:
        return "unbestimmt"
    for rx, klasse in ROLLE_LOKAL_REGELN:
        if rx.search(s):
            return klasse
    return "unbestimmt"


def rolle_sponsor(role_harm: str | None, role_de: str | None, role_fr: str | None,
                  role_it: str | None) -> str:
    """-> sponsor | cosponsor | transferred | andere | unbestimmt."""
    if role_harm in ("cosign", "co-signer"):
        return "cosponsor"
    if role_harm == "assuming":
        return "transferred"
    if role_harm in ("primary", "party-group", "multigroup", "interpartis"):
        return "sponsor"
    if role_harm != "author":
        return "andere"
    return rolle_lokal(role_de, role_fr, role_it)


# ---------------------------------------------------------------- Texttypen -> TextTypeEnum

TEXTTYP_REGELN: list[tuple[re.Pattern, str, str]] = [
    (_R(r"titel des gesch|titre de l|titolo dell"), "title", "exakt"),
    (_R(r"eingereichter text|texte d[ée]pos[ée]|testo depositato|text des vorstosses|"
        r"texte soumis|^vorstoss$|^frage vom"), "submitted", "exakt"),
    (_R(r"^antrag$"), "submitted", "nah"),
    (_R(r"begr[üu]ndung|d[ée]veloppement|motivazione"), "reasoning", "exakt"),
    (_R(r"antwort|r[ée]ponse|risposta"), "response", "exakt"),
    (_R(r"zusammenfassung|r[ée]sum[ée]|kurzbeschrieb|kurzbeschreibung|lead|teaser"), "summary", "nah"),
    (_R(r"beschreibung|contenu"), "summary", "weiter"),
]


def texttyp(type_de: str | None, type_fr: str | None, type_it: str | None) -> tuple[str, str]:
    for t in (type_de, type_fr, type_it):
        if not t:
            continue
        for rx, wert, art in TEXTTYP_REGELN:
            if rx.search(t.strip()):
                return wert, art
    return "", "keine"


# ---------------------------------------------------------------- Empfehlung (Exekutive)

# Satzmuster wie in den Bundes-Ereignissen ("Der Bundesrat beantragt die Ablehnung der Motion.")
# Reihenfolge zaehlt.
EMPFEHLUNG_REGELN: list[tuple[re.Pattern, str]] = [
    (_R(r"(annahme|ablehnung)[^.]{0,60}(ziffer|punkt|punkte|ziffern)|(ziffer|punkt)[^.]{0,80}"
        r"(annahme|ablehnung|umzuwandeln)"), "partial_acceptance"),
    (_R(r"in (ein|einen) postulat umzuwandeln|[üu]berweisen als postulat|als postulat "
        r"(entgegen|[üu]berweis)|transformer en postulat|en postulat"), "partial_acceptance"),
    (_R(r"als erf[üu]llt abzuschreiben|annehmen und abschreiben|abzuschreiben|"
        r"beantragt die abschreibung"), "already_done"),
    (_R(r"beantragt,? (die )?ablehnung|beantragt,? [^.]{0,40}abzulehnen|antrag:? ablehn|"
        r"antrag gemeinderat: ablehnung|stadtrat, ablehnung|refus (du postulat|de la motion)|"
        r"propose de (la )?refuser|propose le rejet|nicht-entgegennahme|nichtentgegennahme|"
        r"nicht entgegen"), "reject"),
    (_R(r"beantragt,? (die )?annahme|beantragt,? [^.]{0,40}anzunehmen|bereit, [^.]{0,40}"
        r"entgegenzunehmen|antrag:? annehm|antrag:? [üu]berweis|annahmeempfehlung|"
        r"antrag:? annahme|entgegennahme|acceptation (du postulat|de la motion)|propose d.accepter"),
     "accept"),
]

# harmonisierte Antrags-Ereignisse (title_harmonized_id) -> Empfehlung
EMPFEHLUNG_HARM: dict[int, str] = {29: "reject", 30: "accept", 31: "already_done", 32: "accept",
                                   33: "partial_acceptance"}

EXEKUTIVE = _R(r"regierung|bundesrat|stadtrat|gemeinderat|staatsrat|conseil d.?[ée]tat|"
               r"conseil communal|conseil municipal|municipalit|consiglio di stato|municipio|"
               r"standeskommission|exekutive|b[üu]ro")


def empfehlung_aus_titel(titel: str) -> str:
    for rx, wert in EMPFEHLUNG_REGELN:
        if rx.search(titel):
            return wert
    return ""


# ---------------------------------------------------------------- Ereignisse

# Ein Ereignis wird auf (eCH-Schritt, Etappe, Entscheid, Status) abgebildet.
# eCH-Schritt: Klasse/Slot im eCH-0295-Modell. Etappe: ProcedureStageEnum. Entscheid:
# ProcedureDecisionEnum ("" = kein Entscheid kodiert, "keine:<grund>" = Entscheid ohne eCH-Wert).
# Status: StatusEnum-Hinweis (open/closed/"").
# title_harmonized_id -> (Schritt, Etappe, Entscheid, Status, Match-Art, Bemerkung)
EREIGNIS_HARM: dict[int, tuple[str, str, str, str, str, str]] = {
    1: ("Submission", "submission", "none", "open", "exakt", "enthaelt auch 'Antrag Regierungsrat' (Regierungsvorlagen)"),
    2: ("SubmissionValidationStep(urgency_request)", "urgency_review", "", "", "nah", "Ergebnis nicht kodiert"),
    3: ("", "", "", "", "keine", "Vernehmlassung"),
    4: ("AssignmentStep.deadline (geplant)", "", "", "", "weiter", ""),
    6: ("ResponseStep", "executive_response", "", "", "nah", "enthaelt auch Kommissionsantraege (actor 'Kommission')"),
    8: ("PlenaryDebate", "plenary", "", "", "nah", "Ergebnis nicht kodiert; enthaelt auch Antraege"),
    9: ("AssignmentStep.deadline", "", "", "", "nah", "Frist; Art der Frist nicht kodiert"),
    10: ("CommitteeDeliberationStep", "committee", "", "", "exakt", ""),
    11: ("", "", "", "", "keine", "Volksabstimmung, nachparlamentarisch"),
    12: ("", "", "", "", "keine", "Volksabstimmung, nachparlamentarisch"),
    13: ("PlenaryDebate(verzoegerung)", "plenary", "", "", "nah", ""),
    14: ("", "", "", "", "keine", ""),
    15: ("", "", "", "", "keine", "Wahlgeschaeft"),
    16: ("PlenaryDebate", "plenary", "", "", "weiter", ""),
    17: ("", "", "", "", "keine", "Publikation"),
    18: ("AssignmentStep.deadline (Referendumsfrist)", "", "", "", "weiter", ""),
    19: ("PlenaryDebate", "report_review_in_council", "keine:kenntnisnahme", "", "weiter", "Kenntnisnahme != Genehmigung"),
    22: ("PlenaryDebate", "report_review_in_council", "keine:stehen_lassen", "open", "weiter", "'stehen lassen': kein eCH-Entscheid"),
    24: ("AssignmentStep(agenda_placement)", "", "", "open", "exakt", "enthaelt auch 'Urgence acceptee' (GE)"),
    25: ("", "", "", "open", "keine", "Wiederaufnahme"),
    26: ("PlenaryDebate", "forwarded_to_executive", "adopted", "open", "nah", "Ueberweisung an die Exekutive"),
    27: ("PlenaryDebate", "forwarded_to_executive", "keine:als_postulat", "open", "weiter", "als Postulat ueberwiesen: Typwechsel statt Entscheid"),
    28: ("AssignmentStep(committee_referral)", "committee", "", "open", "exakt", ""),
    29: ("ResponseStep", "executive_response", "recommended_against", "open", "exakt", ""),
    30: ("ResponseStep", "executive_response", "recommended_for", "open", "exakt", ""),
    31: ("ResponseStep", "executive_response", "recommended_for", "open", "weiter", "zugleich Abschreibung beantragt"),
    32: ("ResponseStep", "executive_response", "recommended_for", "open", "nah", ""),
    33: ("ResponseStep", "executive_response", "keine:umwandlung_postulat_beantragt", "open", "weiter", "Umwandlung in Postulat: kein eCH-Entscheid"),
    34: ("ResponseStep", "report_submitted_to_council", "keine:fristverlaengerung_beantragt", "open", "weiter", "Fristverlaengerung beantragt"),
    35: ("PlenaryDebate", "plenary", "rejected", "closed", "exakt", ""),
    36: ("PlenaryDebate(abschreibung)", "report_review_in_council", "keine:abgeschrieben", "closed", "weiter", "Abschreibung: kein eCH-Entscheid"),
    37: ("PlenaryDebate", "plenary", "adopted", "", "exakt", ""),
    38: ("ProcedureState", "", "", "closed", "nah", "Erledigt: nur Status"),
    39: ("PlenaryDebate", "plenary", "keine:rueckweisung", "", "weiter", "Rueckweisung: kein eCH-Entscheid"),
    40: ("Submission.withdrawn_date", "withdrawal", "withdrawn", "closed", "exakt", ""),
    41: ("PlenaryDebate", "plenary", "adopted", "", "nah", ""),
    42: ("ProcedureState", "", "", "closed", "nah", ""),
    47: ("AssignmentStep(agenda_placement)", "", "", "open", "nah", "geplant"),
    48: ("PlenaryDebate(fristverlaengerung)", "", "keine:fristverlaengerung", "open", "nah", ""),
    49: ("", "", "", "", "keine", "Referendumsfrist abgelaufen"),
    50: ("PlenaryDebate", "plenary", "adopted", "", "nah", "erheblich erklaert"),
    52: ("", "", "", "", "keine", ""),
    53: ("", "", "", "", "keine", ""),
    54: ("PlenaryDebate", "plenary", "", "", "weiter", "Ergebnis nicht kodiert"),
    55: ("SubmissionValidationStep(initial_check)", "submission_validation", "", "", "exakt", ""),
    56: ("Submission", "submission", "none", "open", "nah", ""),
    57: ("PlenaryDebate", "plenary", "keine:volksempfehlung", "", "keine", "Abstimmungsempfehlung an das Volk"),
    58: ("", "", "", "", "keine", "Platzhalter '-'"),
    60: ("PlenaryDebate", "plenary", "", "", "nah", ""),
    62: ("", "", "", "", "keine", ""),
    63: ("PlenaryDebate", "report_review_in_council", "keine:nichtabschreibung", "open", "weiter", "Nichtabschreibung"),
    64: ("PlenaryDebate(fristverlaengerung)", "", "keine:fristverlaengerung", "open", "nah", ""),
    66: ("PlenaryDebate(verzoegerung)", "plenary", "", "open", "nah", ""),
    67: ("Submission", "submission", "none", "open", "exakt", ""),
    68: ("PlenaryDebateEvent(vote)", "plenary", "", "", "weiter", "Ergebnis nicht kodiert"),
    70: ("Submission (Regierungsvorlage)", "submission", "none", "open", "weiter", ""),
    71: ("SubmissionValidationStep", "submission_validation", "validated", "", "weiter", "Volksinitiative zustande gekommen"),
    72: ("", "", "", "closed", "keine", "Volksinitiative"),
    73: ("PlenaryDebate", "forwarded_to_executive", "keine:als_postulat", "open", "weiter", ""),
    75: ("PlenaryDebate", "plenary", "", "", "nah", ""),
    76: ("ResponseStep", "executive_response", "", "", "nah", "enthaelt auch Antraege der Exekutive"),
    78: ("", "", "", "", "keine", "Volksinitiative"),
    80: ("PlenaryDebate", "forwarded_to_executive", "adopted", "open", "nah", ""),
    81: ("PlenaryDebate", "forwarded_to_executive", "adopted", "open", "weiter", "lokal 'Ueberwiesen' und 'Ueberweisen'"),
    82: ("", "", "", "", "keine", ""),
    84: ("PlenaryDebate", "plenary", "keine:volksempfehlung", "", "keine", "Abstimmungsempfehlung an das Volk"),
    88: ("PlenaryDebate", "plenary", "rejected", "closed", "nah", ""),
    89: ("ProcedureState", "", "keine:wegfall", "closed", "weiter", "Wegfall"),
    90: ("PlenaryDebate(abschreibung)", "report_review_in_council", "keine:abgeschrieben", "closed", "weiter", ""),
    91: ("PlenaryDebate", "plenary", "", "", "nah", ""),
    93: ("", "", "", "", "keine", ""),
    94: ("", "", "", "", "keine", "Inkrafttreten"),
    95: ("", "", "", "", "keine", ""),
    96: ("Submission.withdrawn_date", "withdrawal", "withdrawn", "", "nah", "bedingter Rueckzug"),
    97: ("PlenaryDebate", "plenary", "", "", "weiter", ""),
    98: ("SubmissionValidationStep", "submission_validation", "failed_validation", "closed", "weiter", ""),
    99: ("Submission (Regierungsvorlage)", "submission", "none", "open", "weiter", ""),
    100: ("SubmissionValidationStep", "submission_validation", "failed_validation", "closed", "weiter", ""),
    101: ("", "", "", "closed", "keine", "Volksinitiative"),
    102: ("PlenaryDebate", "plenary", "adopted", "", "exakt", ""),
    103: ("", "", "", "", "keine", ""),
    104: ("", "", "", "", "keine", ""),
    105: ("Submission.reasoning_in_council", "plenary", "", "", "nah", "muendlich begruendet"),
    106: ("", "", "", "", "keine", "Platzhalter '1'"),
}

# Lokale Titelregeln (alle Sprachen), vor der Harmonisierung angewandt.
# (Regex, Schritt, Etappe, Entscheid, Status)
EREIGNIS_LOKAL_REGELN: list[tuple[re.Pattern, str, str, str, str]] = [
    (_R(r"(bundesrat|b[üu]ro|regierung|regierungsrat|stadtrat|gemeinderat)[^.]{0,40}"
        r"(beantragt|ist bereit)|^antrag: |antrag (des )?(regierungsrat|gemeinderat|stadtrat)"
        r"e?s?[ :,]+\S|annahmeempfehlung|stellungnahme regierungsrat|"
        r"stadtrat, (ablehnung|entgegennahme)|(acceptation|refus) (du postulat|de la motion)"),
     "ResponseStep", "executive_response", "@empfehlung", "open"),
    (_R(r"kommissionsantrag|antrag (der )?kommission|la commission propose|"
        r"rapport de (la )?commission"), "CommitteeDeliberationStep", "committee", "", "open"),
    (_R(r"dringlich\w*,? (abgelehnt|nicht erfolgt)|urgence refus|urgenza (rifiut|respint)"),
     "SubmissionValidationStep(urgency_request)", "urgency_review", "urgency_denied", ""),
    (_R(r"dringlich\w*,? (angenommen|erfolgt|erkl[äa]rt)|dringlich erkl|urgence accept|"
        r"urgenza (accolt|adott)|annahme der dringlichkeitsklausel|beschluss dringlichkeit"),
     "SubmissionValidationStep(urgency_request)", "urgency_review", "urgency_granted", ""),
    (_R(r"dringlicherkl[äa]rung, beantragt"), "SubmissionValidationStep(urgency_request)",
     "urgency_review", "", ""),
    (_R(r"zur[üu]ckgezogen|r[üu]ckzug|retir[ée]|ritirat"), "Submission.withdrawn_date",
     "withdrawal", "withdrawn", "closed"),
    (_R(r"abschreibungsantrag|antrag auf abschreibung"), "ResponseStep(Abschreibungsantrag)",
     "report_submitted_to_council", "", "open"),
    (_R(r"nichtabschreibung|nicht abgeschrieben|keine abschreibung|non-classement|stehen lassen"),
     "PlenaryDebate",
     "report_review_in_council", "keine:nichtabschreibung", "open"),
    (_R(r"abgeschrieben|abschreibung|class[ée]|classement"), "PlenaryDebate(abschreibung)",
     "report_review_in_council", "keine:abgeschrieben", "closed"),
    (_R(r"in (ein|form eines) postulat|als postulat [üu]berwiesen|umwandlung in (ein )?postulat|"
        r"transform[ée]e? en postulat"), "PlenaryDebate", "forwarded_to_executive", "keine:als_postulat", "open"),
    (_R(r"nicht [üu]berwiesen|keine folge gegeben|keine zustimmung|^ablehnung$|^abgelehnt|"
        r"nichteintreten|non-entr[ée]e en mati|"
        r"nicht erheblich|nicht-erheblich|refus[ée]e?\b|rejet[ée]e?\b|respint|"
        r"nicht vorl[äa]ufig unterst"), "PlenaryDebate", "plenary", "rejected", "closed"),
    (_R(r"zur stellungnahme|pour (pr[ée]avis|avis)"), "AssignmentStep(executive_routing)", "",
     "", "open"),
    (_R(r"[üu]berweisung an (den )?(rr|regierungsrat|bundesrat|stadtrat|gemeinderat)\b|"
        r"[üu]berwiesen an (den bundesrat|rr|die regierung|den regierungsrat|den stadtrat|"
        r"den gemeinderat)|renvoy[ée]e? au conseil d.[ée]tat|transmise? au c|"
        r"^[üu]berwiesen|^[üu]berweisung, frist"), "PlenaryDebate", "forwarded_to_executive",
     "adopted", "open"),
    (_R(r"[üu]berweisung an (?!rr|den bundesrat|die regierung)|zugewiesen an (die )?"
        r"(behandelnde|zust[äa]ndige) kommission|renvoy[ée]e? (en|[àa] la) commission|"
        r"zuweisung an"), "AssignmentStep(committee_referral)", "committee", "", "open"),
    (_R(r"in kommission|beratung in kommission|vorberatung|commission .* (examen|charg)"),
     "CommitteeDeliberationStep", "committee", "", "open"),
    (_R(r"^annahme|^angenommen|^zustimmung|folge gegeben|folge geben|^beschluss gem[äa]ss|"
        r"beschluss, einen erlassentwurf|"
        r"beschluss abweichend|erheblich erkl|adopt[ée]|accept[ée]|approvat|pris en consid|"
        r"genehmigt|^beschlossen"), "PlenaryDebate", "plenary", "adopted", ""),
    (_R(r"^eingereicht|^einreichung|^d[ée]pos[ée]|^presentat|^eingabe|eingericht"),
     "Submission", "submission", "none", "open"),
    (_R(r"beantwort|antwort|r[ée]ponse|risposta|stellungnahme zum vorstoss liegt vor"),
     "ResponseStep", "executive_response", "", ""),
    (_R(r"berichterstattung zum umsetzungsstand|bericht in erf[üu]llung|bericht .*umsetzung|"
        r"rapport .*(r[ée]ponse|"
        r"ex[ée]cution)"), "ResponseStep(Bericht)", "report_submitted_to_council", "", "open"),
    (_R(r"kenntnisnahme|zur kenntnis|pris acte|prend acte"), "PlenaryDebate",
     "report_review_in_council", "keine:kenntnisnahme", ""),
    (_R(r"fristverl[äa]nger|fristerstreck|prolongation"), "PlenaryDebate(fristverlaengerung)",
     "", "keine:fristverlaengerung", "open"),
    (_R(r"diskussion verschoben|verschoben|report[ée]e?\b|renvoy[ée]e? par manque"),
     "PlenaryDebate(verzoegerung)", "plenary", "", "open"),
    (_R(r"^erledigt|objet clos|est close|^abgeschlossen|^termin[ée]|^evas"), "ProcedureState",
     "", "", "closed"),
    (_R(r"im rat noch nicht behandelt"), "ProcedureState", "", "", "open"),
    (_R(r"^abweichung|differenzbereinigung|einigungskonferenz"), "PlenaryDebate", "plenary", "", ""),
    (_R(r"in (national|st[äa]nde)rat geplant|geplant f[üu]r|^traktandiert|"
        r"inscrit|bereit zur traktandierung"), "AssignmentStep(agenda_placement)", "", "", "open"),
    (_R(r"wird [üu]bernommen"), "Submission.sponsorship(transferred)", "", "", ""),
    (_R(r"behandelt vom|von beiden r[äa]ten behandelt|im (parlament|rat) behandelt|"
        r"vom parlament behandelt|motion an 2\. rat"), "PlenaryDebate", "plenary", "", ""),
]


def ereignis(harm_id: int | None, titel: str) -> tuple[str, str, str, str, str, str]:
    """-> (Schritt, Etappe, Entscheid, Status, Empfehlung, Quelle).

    Quelle: 'lokal' (Regel auf lokalem Titel), 'harmonisiert' oder ''.
    Empfehlung (RecommendationEnum) nur bei Antraegen der Exekutive.
    """
    t = (titel or "").strip()
    if t:
        for rx, schritt, etappe, entscheid, status in EREIGNIS_LOKAL_REGELN:
            if rx.search(t):
                empf = ""
                if entscheid == "@empfehlung":
                    empf = empfehlung_aus_titel(t) or EMPFEHLUNG_HARM.get(harm_id or -1, "")
                    entscheid = {"accept": "recommended_for", "reject": "recommended_against"}.get(
                        empf, ("keine:empfehlung_" + empf) if empf else "")
                    if empf == "already_done" and re.search(r"annehm|annahme", t, re.I):
                        entscheid = "recommended_for"
                return schritt, etappe, entscheid, status, empf, "lokal"
    if harm_id is not None and harm_id in EREIGNIS_HARM:
        s, e, d, st, _, _ = EREIGNIS_HARM[harm_id]
        return s, e, d, st, EMPFEHLUNG_HARM.get(harm_id, ""), "harmonisiert"
    return "", "", "", "", "", ""


# ---------------------------------------------------------------- Status (affairs.state_name_*)

STATUS_REGELN: list[tuple[re.Pattern, str, str, str]] = [
    # (Regex, StatusEnum, Etappe, Entscheid)
    (_R(r"non evas|nicht erledigt|unerledigt|^offen|hängig|h[äa]ngig|pendent|in bearbeitung|"
        r"inbearbeitung|laufend|en cours|in corso|pendente|eingereicht|d[ée]pos[ée]|traktandiert|"
        r"inscrit|zugewiesen|in kommission|renvoy[ée]e? [àa] commission|stellungnahme zum vorstoss "
        r"liegt vor|bericht und antrag|berichterstattung zum umsetzungsstand|vollzug|"
        r"im rat noch nicht|^kommission|manque de temps"), "open", "", ""),
    (_R(r"als postulat [üu]berwiesen und abgeschrieben"), "closed", "report_review_in_council", "keine:abgeschrieben"),
    (_R(r"als postulat|annahme als postulat"), "open", "forwarded_to_executive", "keine:als_postulat"),
    (_R(r"[üu]berwiesen|renvoy[ée]e? au conseil d|transmise? au|folge geleistet|^erheblich$"),
     "open", "forwarded_to_executive", "adopted"),
    (_R(r"zur[üu]ckgezogen|r[üu]ckzug|retir|ritirat"), "closed", "withdrawal", "withdrawn"),
    (_R(r"abgeschrieben|class[ée]"), "closed", "report_review_in_council", "keine:abgeschrieben"),
    (_R(r"nicht erheblich|nicht-erheblich|abgelehnt|ablehnung|refus|respint|non accolt"),
     "closed", "plenary", "rejected"),
    # angenommen: Status offen (Vorstoss in Umsetzung) oder geschlossen (Vorlage) -> unbestimmt
    (_R(r"angenommen|annahme|adopt|accept|approvat|genehmig|beschlossen|zustimmung|pris en consid|"
        r"gew[äa]hlt"), "", "plenary", "adopted"),
    (_R(r"erledigt|abgeschlossen|evas|termin|trait[ée]|liquid|close|kenntnis|beantwortet|archiv|"
        r"schlussabstimmung|behandlung .* erfolgt"), "closed", "", ""),
]


def status_lokal(name: str | None) -> tuple[str, str, str]:
    if not name or not name.strip():
        return "", "", ""
    for rx, status, etappe, entscheid in STATUS_REGELN:
        if rx.search(name.strip()):
            return status, etappe, entscheid
    return "", "", ""


# ---------------------------------------------------------------- Geschaeftsnummer

RX_HEX = re.compile(r"^[0-9a-f]{8,}$", re.I)


def nummer_plausibel(number: str | None, external_id: str | None) -> bool:
    """Heuristik (Schaetzung): sieht `number` wie eine amtliche Geschaeftsnummer aus?

    Nicht plausibel: leer, reine Hex-Kennung, oder identisch mit external_id und rein
    numerisch mit mindestens 5 Stellen (dann vermutlich System-ID).
    """
    if not number or not number.strip():
        return False
    n = number.strip()
    if RX_HEX.match(n) and not n.isdigit():
        return False
    if n.isdigit() and len(n) >= 5 and (external_id or "").strip() == n:
        return False
    return True


AUSKUNFT_TYPEN = {"interpellation", "request", "question"}


def ereignis_fuer_typ(res: tuple, ech_typ: str) -> tuple:
    """Typabhaengige Korrektur: 'Ueberwiesen' bei Interpellation/Anfrage/Frage heisst
    Weiterleitung an die Exekutive zur Beantwortung, nicht Annahme."""
    if ech_typ in AUSKUNFT_TYPEN and res[1] == "forwarded_to_executive":
        return ("AssignmentStep(executive_routing)", "", "", "open", res[4], res[5])
    return res

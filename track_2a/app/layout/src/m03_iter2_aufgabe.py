"""Iteration 2: Aufgabe «Antrag der Exekutive» (eCH-0295 ResponseStep.recommendation).

Reines Definitionsmodul ohne Datenzugriff. Wird von den Skripten m03_iter2_*.py und von
m04_auswerten.py (Regel-Baseline) importiert. Enthält:

- OPTIONEN: die Antwortoptionen (Antrag der Exekutive) mit kurzen Definitionen
- ECH_ABBILDUNG: Abbildung jeder Option auf RecommendationEnum mit Match-Art und Verlust
- antrag_aus_ereignis(): Silber-Label aus einem Ereignis (Titel, harmonisierte ID, Akteur)
- ANTRAGSSATZ / antragssaetze(): Regex für Antragssätze im Antworttext (de, fr, it), dient
  zum Messen der Position und als Regel-Baseline (regel_baseline())

- schlussblock_entfernen(): formalen Schlussblock (Verteiler, wiederholte Gliederung) abtrennen
- regel_baseline(kontext, variante): Regel-Baseline in drei Varianten (geliefert,
  ohne_valwissen, rueckfall), siehe REGEL_VARIANTEN

Alle Regeln sind Vorschläge (Silber-Qualität), geprüft nur an Stichproben
(crisp-dm/03-data-preparation/iter2-empfehlung.md).

Stand nach der Prüfung für Iteration 2 (iter2-empfehlung.md, Abschnitt 11): FRAGE und die
Optionstexte annehmen, ablehnen, teilweise und keine_passt sind an die Label-Definition
angeglichen (Antrag zählt, auch mit geändertem Wortlaut; Antrag darf aus der Stellungnahme
folgen). Die Regex der Antragsstellen ist seit dieser Prüfung eingefroren; Alternativen ohne
Beleg in den Trainingsparlamenten sind in VALIDIERUNGSWISSEN aufgeführt.
"""

from __future__ import annotations

import re

SYSTEM = "Du klassifizierst Abschnitte aus Schweizer Parlamentsdokumenten."  # wie Iteration 1
# Frage: Satz 2 und 3 seit der Prüfung für Iteration 2 (Richter A/B): die Regel «Antrag statt
# Begründung» stand vorher nur in der Dokumentation; der Antrag darf aus der Stellungnahme
# folgen (NE «Position du Conseil d'État» ohne Antragssatz, Label aus dem Ereignis).
FRAGE = ("Was beantragt die Exekutive (Regierung, Gemeinderat, Bundesrat) dem Parlament "
         "zu diesem Vorstoss? Massgebend ist der Antrag, nicht seine Begründung. Der Antrag "
         "kann auch ohne ausdrücklichen Antragssatz aus der Stellungnahme hervorgehen.")

# Antrag der Exekutive. Schlüssel sind eigene Namen, die Abbildung auf eCH steht in
# ECH_ABBILDUNG. Die Optionen schliessen sich gegenseitig aus: massgebend ist der Antrag
# zur Überweisung bzw. Annahme des Vorstosses, nicht dessen Begründung.
# Texte annehmen, ablehnen, teilweise und keine_passt seit der Prüfung für Iteration 2 an die
# Label-Definition angeglichen (harmonisierte Ereignisse «Annehmen»/«Überweisen» umfassen
# auch die Annahme mit geändertem Wortlaut oder mit Erklärung); vorher «ganz annehmen» bzw.
# «der Text nennt keinen Antrag» (iter2-empfehlung.md, Abschnitt 11).
OPTIONEN = {
    "annehmen": ("Annehmen: den Vorstoss annehmen, überweisen, entgegennehmen oder erheblich "
                 "erklären, auch mit geändertem Wortlaut oder mit einer Erklärung"),
    "ablehnen": ("Ablehnen: den Vorstoss ablehnen, nicht überweisen, nicht entgegennehmen oder "
                 "nicht erheblich erklären"),
    "teilweise": ("Teilweise annehmen: nur einzelne Ziffern oder Teile annehmen und die übrigen "
                  "ausdrücklich ablehnen"),
    "umwandlung": "In ein Postulat umwandeln: die Motion nur als Postulat überweisen",
    "annehmen_abschreiben": "Annehmen und abschreiben: annehmen und zugleich als erledigt abschreiben",
    "keine_empfehlung": "Keine Empfehlung: die Exekutive verzichtet ausdrücklich auf einen Antrag",
    "keine_passt": ("Keine der Optionen passt: Der Text lässt keinen Antrag zu diesem Vorstoss "
                    "erkennen, oder der Antrag passt zu keiner Option"),
}
BUCHSTABEN = "ABCDEFGHIJKLMNOP"

# Option -> (RecommendationEnum, Match-Art, was verloren geht)
ECH_ABBILDUNG = {
    "annehmen": ("accept", "exakt", ""),
    "ablehnen": ("reject", "exakt", ""),
    "teilweise": ("partial_acceptance", "exakt", "welche Ziffern angenommen werden"),
    "umwandlung": ("partial_acceptance", "weiter",
                   "dass die Teilannahme eine Umwandlung in ein Postulat ist (Typwechsel)"),
    "annehmen_abschreiben": ("already_done", "weiter",
                             "der Antrag selbst (Annahme); already_done ist eine Begründung und "
                             "deckt auch «ablehnen, weil erfüllt»"),
    "keine_empfehlung": ("neutral", "nah", ""),
    "keine_passt": ("", "keine", "kein Wert; defer und no_competence haben keine eigene Option"),
}

_R = lambda p: re.compile(p, re.I)  # noqa: E731

# ---------------------------------------------------------------- Silber-Labels aus Ereignissen

# Harmonisierte Antrags-Ereignisse (title_harmonized_id) -> Option, wenn der lokale Titel
# leer ist oder selbst keine Klasse ergibt.
HARM_OPTION = {29: "ablehnen", 30: "annehmen", 31: "annehmen_abschreiben", 32: "annehmen",
               33: "umwandlung"}

# Ein Ereignis zählt nur als Antrag der Exekutive, wenn eine dieser Bedingungen gilt:
# harmonisierte ID in HARM_OPTION, oder lokaler Titel passt auf EXEKUTIV_ANTRAG, oder
# (nur LU) harmonisiert 76 «Beantwortung» mit lokalem Titel «Antrag: …».
EXEKUTIV_ANTRAG = _R(
    r"^(der |die |le |il )?(bundesrat|regierungsrat|stadtrat|gemeinderat|conseil d.[ée]tat|"
    r"gouvernement|consiglio di stato|municipio|municipalit[ée]|conseil communal)\b[^.]{0,40}"
    r"(beantragt|ist bereit|propose|chiede|propone)|"
    r"^antrag (des |der )?(regierungsrat|stadtrat|gemeinderat|regierung)(e?s)?\b|"
    r"^(stadtrat|gemeinderat|regierungsrat), (ablehnung|entgegennahme|annahme)|"
    r"^(acceptation|refus) (du postulat|de la motion)|^antrag: ")
ANDERE_STELLE = _R(r"^das b[üu]ro|b[üu]ro des (national|st[äa]nde)rates")
KOMMISSION = _R(r"kommission|commission|commissione")

# Klassen auf dem lokalen Titel, Reihenfolge zählt (spezifisch vor allgemein).
# (Regelname, Regex, Option); Option "" heisst: Ereignis erkannt, aber kein Label (unsicher).
TITEL_REGELN: list[tuple[str, re.Pattern, str]] = [
    ("teilweise_ziffer",
     _R(r"(annahme|ablehnung|anzunehmen|abzulehnen)[^.]{0,60}(ziffer|ziff\.|punkt)|"
        r"(ziffer|ziff\.|punkt)[^.]{0,80}(annahme|ablehnung|anzunehmen|abzulehnen)|teilweise"),
     "teilweise"),
    ("umwandlung_abschreiben",
     _R(r"als postulat[^.]{0,30}(und|sowie)[^.]{0,20}abschreib"), ""),
    ("umwandlung",
     _R(r"in (ein|einen) postulat umzuwandeln|als postulat|umwandlung in (ein )?postulat|"
        r"en postulat|in forma di postulato"), "umwandlung"),
    ("annehmen_abschreiben",
     _R(r"(annehmen|annahme|entgegennahme|entgegennehmen|entgegenahme|[üu]berweisen|[üu]berweisung|"
        r"erheblich)[^.]{0,30}(und|sowie)[^.]{0,20}(gleichzeitig[^.]{0,10})?abschreib"),
     "annehmen_abschreiben"),
    ("nur_abschreiben", _R(r"abzuschreiben|abschreibung|abschreiben|classement"), ""),
    ("ablehnen",
     _R(r"ablehn|ablehnung|abzulehnen|nicht (zu )?([üu]berweis|entgegen)|nicht-entgegen|"
        r"nichtentgegen|nicht erheblich|refus|rejet|respin"), "ablehnen"),
    ("annehmen",
     _R(r"annahme|annehmen|anzunehmen|[üu]berweis|entgegen|erheblich|acceptation|accept|accolt"),
     "annehmen"),
]


def antrag_aus_ereignis(harm_id: int | None, titel: str, actor: str) -> tuple[str, str]:
    """-> (Option, Regel). Option '' mit Regel '' = kein Antrags-Ereignis.

    Option '' mit Regel != '' = Antrags-Ereignis erkannt, aber ohne verwertbares Label
    (z. B. andere Stelle, nur Abschreibung, Umwandlung und Abschreibung).
    """
    t = (titel or "").strip()
    a = (actor or "").strip()
    ist_antrag = (harm_id in HARM_OPTION or bool(EXEKUTIV_ANTRAG.search(t))
                  or (harm_id == 76 and t.lower().startswith("antrag:")))
    if not ist_antrag:
        return "", ""
    if ANDERE_STELLE.search(t):
        return "", "andere_stelle_buero"
    if a and KOMMISSION.search(a):
        return "", "andere_stelle_kommission"
    t_ohne_harm = t
    if t:
        for name, rx, option in TITEL_REGELN:
            if rx.search(t_ohne_harm):
                return option, "titel:" + name
    if harm_id in HARM_OPTION:
        return HARM_OPTION[harm_id], f"harmonisiert:{harm_id}"
    return "", "unklar"


# ---------------------------------------------------------------- Antragsstellen im Text

def normalisieren(text: str) -> str:
    """Leerraum vereinheitlichen und Silbentrennung am Zeilenende auflösen.

    Tika liefert viel Leerraum (Spalten, Seitenköpfe). Zusammengefasst werden Leerzeichen,
    Tabs und geschützte Leerzeichen; Zeilenumbrüche bleiben (höchstens eine Leerzeile).
    «entgegenzu-\nnehmen» wird zu «entgegenzunehmen», wenn beidseits Kleinbuchstaben stehen.
    """
    t = text.replace("­", "").replace("\r", "\n")
    t = re.sub(r"[ \t   ]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    t = re.sub(r"([a-zäöüàéèçß])-\n([a-zäöüàéèç])", r"\1\2", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# Formaler Schlussblock: Zeile «Verteiler» (Verteilerliste mit Adresszeilen; in SO folgt danach
# oft die Gliederung des Dokuments als zweite Fassung der Überschriften). Gesucht wird nur in
# der zweiten Hälfte des Texts, damit ein Verteiler im Kopf nichts abschneidet. Die Regel
# richtet sich nach dem Format, nicht nach Antragsstellen (Anlass: Prüfung für Iteration 2,
# SO-Kontexte, deren Ende-Fenster ganz aus dem Verteiler bestand).
SCHLUSSBLOCK = re.compile(r"^verteiler\s*:?\s*$", re.I | re.M)
SCHLUSSBLOCK_AB = 0.5   # frühestens ab diesem Anteil der Textlänge


def schlussblock_entfernen(text: str) -> str:
    """Text ab der ersten Zeile «Verteiler» in der zweiten Hälfte abschneiden (sonst unverändert)."""
    for m in SCHLUSSBLOCK.finditer(text):
        if m.start() >= len(text) * SCHLUSSBLOCK_AB:
            return text[:m.start()].rstrip()
    return text


# Organ der Exekutive (de, fr, it), Ich-Form der Exekutive und Antragsverben.
ORGAN = (r"(bundesrat|conseil f[ée]d[ée]ral|consiglio federale|regierungsrat|regierung|"
         r"stadtrat|gemeinderat|kleine[rn]? rat|conseil[- ]ex[ée]cutif|conseil d.[ée]tat|"
         r"gouvernement|conseil communal|municipalit[ée]|consiglio di stato|municipio|governo)")
ICH_FORM = (r"(wir (ihnen |euch )?(beantragen|empfehlen|sind (daher |deshalb |somit )?bereit|lehnen)|"
            r"beantragen wir|empfehlen wir|lehnen wir|unser rat (beantragt|ist bereit|lehnt)|"
            r"nous (vous )?(proposons|recommandons|refusons|acceptons)|vous (propose|proposons)|"
            r"(vi )?proponiamo|chiediamo)")
VERB = (r"(beantrag\w*|ist bereit|sind bereit|erkl[äa]rt sich bereit|bereit erkl[äa]rt|empfiehlt|"
        r"lehnt|ablehn\w*|abzulehnen|nimmt|entgegen\w*|propose\w*|recommande|s.oppose|accepte|"
        r"refuse|rejette|invite|chiede|propone|invita|respinge|accoglie)")
_NAH = r"[^.!?\n]{0,120}"
ANKER_SATZ = re.compile(rf"\b{ORGAN}\b{_NAH}\b{VERB}|\b{VERB}{_NAH}\b{ORGAN}\b|\b{ICH_FORM}\b", re.I)
# Kopfzeilen und Felder: «Antrag Regierungsrat: … / Ablehnung», «4. Antrag des Regierungsrates»,
# «Antrag des Stadtrates:», «Position du Conseil d'État :», «Proposition du Gouvernement»
ANKER_FELD = re.compile(
    r"^(\d+\.?\s*)?(antrag|antr[äa]ge|proposition|propositions|conclusion|conclusions|"
    r"position du conseil|position du gouvernement|proposta|dispositivo)\b[^\n]{0,120}$", re.I | re.M)
# Titelvermerk in den ersten Zeilen: «…betreffend X; Ablehnung», «…, Entgegennahme als Postulat»
ANKER_VERMERK = re.compile(
    r"[,;–]\s*(teilweise |gleichzeitige )?(ablehnung|entgegennahme|annahme|umwandlung|"
    r"nicht-?entgegennahme|nichterheblicherkl[äa]rung|erheblicherkl[äa]rung|"
    r"abschreibung)\b[^\n]{0,80}$", re.I | re.M)
VERMERK_BEREICH = 1500  # Zeichen am Dokumentanfang, in denen Titelvermerke gesucht werden

ABKUERZUNG = re.compile(r"(\b(bzw|vgl|z|b|nr|art|abs|dr|lit|ziff|mio|mia|ca|inkl|resp|evtl|st|prof|"
                        r"sog|gem|etc|al|kap|fr|bst|hr|mo|po|ip|kt|bd|s|ff|u|a|d|h|v|mit|ref|"
                        r"no|n°|cf|mme|m|let|al|ch|chf|sr|bbl|as|lic|phil|iur|med)\.|\d\.)$", re.I)
SATZENDE = re.compile(r"[.!?](?=\s+[A-ZÄÖÜÀÉÈÎÔ«\"„(]|\s*$)|\n\n")

BOILERPLATE = re.compile(r"oder beantragt er|hat er dies|lehnt der \w+ die entgegennahme einer|"
                         r"innert (sechs|drei) monaten nach", re.I)

_ZIFFER = r"(ziffern?|ziff\.|punkte?|chiffres?|points?|cifr[ae]|punt[io])\W{1,3}(\w{1,3}\W{1,2})?\d"
_JA = r"(annahme|annehmen|anzunehmen|entgegen\w*|[üu]berweis\w*|erheblich\w*|accept\w*|accogl\w*|approv\w*)"
_NEIN = r"(ablehn\w*|abzulehnen|refus\w*|rejet\w*|rejeter|respin\w*)"
SATZ_KLASSEN: list[tuple[str, re.Pattern]] = [
    ("teilweise", _R(rf"{_ZIFFER}[^.]{{0,80}}({_JA}|{_NEIN})|({_JA}|{_NEIN})[^.]{{0,60}}{_ZIFFER}|"
                     r"teilweise (als )?(erheblich|anzunehmen|entgegen|zu [üu]berweisen|annahme|"
                     r"[üu]berweisung)|partiellement|parzialmente|pour le surplus|per il resto")),
    ("ablehnen", _R(r"(nicht|kein\w*|weder)[^.]{0,50}(bereit|gewillt|m[öo]glich)[^.]{0,80}"
                    r"postulat|auch (nicht|kein)[^.]{0,80}postulat|ne (peut|souhaite|saurait) "
                    r"pas[^.]{0,60}postulat")),
    ("umwandlung", _R(r"als postulat|in (ein|einen|das) postulat|in form eines postulat|"
                      r"umwandlung in|umzuwandeln|sous (la )?forme (d.un|de) postulat|"
                      r"en postulat|transformer|transformation|in (un )?postulato|"
                      r"(forma|sotto forma) di postulato|trasformar")),
    ("teilweise", _R(rf"{_JA}[^.]{{0,200}}\b(und|et|e|sowie|mais|aber)\b[^.]{{0,40}}{_NEIN}|"
                     rf"{_NEIN}[^.]{{0,200}}\b(und|et|e|sowie|mais|aber)\b[^.]{{0,40}}{_JA}")),
    ("annehmen_abschreiben", _R(rf"{_JA}[^.]{{0,60}}\b(und|sowie|et|e)\b[^.]{{0,40}}"
                                r"(gleichzeitig[^.]{0,10})?(abzuschreiben|abschreib|class[ée]|"
                                r"classement|stralci|archiviar)|unter gleichzeitiger abschreibung|"
                                r"gleichzeitig (als erledigt |als erf[üu]llt )?abzuschreiben|"
                                r"gleichzeitige abschreibung")),
    ("keine_empfehlung", _R(r"verzicht\w* (auf|darauf)[^.]{0,30}antrag|keinen antrag|"
                            r"ohne antrag|s.en remet|sans (pr[ée]avis|proposition)|"
                            r"nessuna proposta|senza preavviso")),
    ("ablehnen", _R(r"ablehn|abzulehnen|lehnt\b[^.]{0,120}\bab\b|lehnen\b[^.]{0,120}\bab\b|"
                    r"nicht (zu )?([üu]berweis|entgegen|erheblich|anzunehmen)|nicht bereit|"
                    r"nicht-?entgegen|nichtentgegen|nichterheblich|nicht als erheblich|refus|"
                    r"rejet|rejeter|s.oppose|oppos[ée]|ne pas (accepter|prendre en consid|entrer)|"
                    r"non (entrer|accepter)|respin|non accogl|non accett")),
    ("nur_abschreiben", _R(r"abzuschreiben|abschreib|class[ée]|classement")),
    ("annehmen", _R(r"annahme|annehmen|anzunehmen|[üu]berweis|entgegen|erheblich|bereit|"
                    r"accept|soutient|favorable|prendre en consid|adopt|accogl|accett|approva|"
                    r"dar seguito")),
]
OPTIONS_KLASSEN = set(OPTIONEN)  # nur_abschreiben ist keine Option

# Regex-Alternativen ohne Beleg in den Trainingskandidaten: Sie kommen in keinem
# Trainingskontext und in keinem Antwortdokument-Kandidaten der Trainingsparlamente vor, wohl
# aber in der Validierung (Prüfung für Iteration 2, daten/pruefung_iter2/p3_regel_kandidaten.log
# und p4_regel_ablation2.log; «nichterheblich» steht im übrigen Korpus aber in TG, 329, GR).
# Vermutlich beim Augenschein an Validierungstexten entstanden. Die
# Regel bleibt so eingefroren; die Variante «ohne_valwissen» der Regel-Baseline lässt diese
# Alternativen weg und wird daneben ausgewiesen.
VALIDIERUNGSWISSEN = {"ANKER_FELD": "position du conseil", "SATZ_KLASSEN[6] (ablehnen)": "nichterheblich"}


def _ohne_alternative(rx: re.Pattern, alternative: str) -> re.Pattern:
    p = rx.pattern
    assert p.count(alternative + "|") == 1, alternative
    return re.compile(p.replace(alternative + "|", "", 1), rx.flags)


ANKER_FELD_OHNE = _ohne_alternative(ANKER_FELD, "position du conseil")
SATZ_KLASSEN_OHNE = [(k, _ohne_alternative(rx, "nichterheblich") if i == 6 else rx)
                     for i, (k, rx) in enumerate(SATZ_KLASSEN)]
assert SATZ_KLASSEN[6][0] == "ablehnen"

# Typwort für den Rückfall der Regel-Variante «rueckfall» und für die Schicht «typwort»
RX_TYPWORT = re.compile(r"interpellation|interpellanz|interpellazione", re.I)
REGEL_VARIANTEN = ("geliefert", "ohne_valwissen", "rueckfall")


def klasse(stelle: str, klassen: list[tuple[str, re.Pattern]] = SATZ_KLASSEN) -> str:
    """Klasse einer Antragsstelle; '' wenn keine Klasse passt, None bei Textbausteinen."""
    if BOILERPLATE.search(stelle):
        return None
    for name, rx in klassen:
        if rx.search(stelle):
            return name
    return ""


def _satzanfang(t: str, pos: int) -> int:
    lo = max(0, pos - 200)
    stueck = t[lo:pos]
    best = lo
    for m in SATZENDE.finditer(stueck):
        if not ABKUERZUNG.search(stueck[:m.start() + 1][-12:]):
            best = lo + m.end()
    nl = t.rfind("\n\n", lo, pos)
    return max(best, nl + 2 if nl >= 0 else 0)


def _satzende(t: str, pos: int, maxlen: int = 320) -> int:
    hi = min(len(t), pos + maxlen)
    for m in SATZENDE.finditer(t, pos, hi):
        if m.group(0) == "\n\n":
            if m.start() > 0 and t[m.start() - 1] in ",;-(" or (
                    m.start() > 0 and t[m.start() - 1].islower() and m.end() < len(t)
                    and t[m.end()].islower()):
                continue   # Absatz mitten im Satz (Seiten- oder Spaltenumbruch)
            return m.start()
        if not ABKUERZUNG.search(t[max(0, m.start() - 11):m.start() + 1]):
            return m.end()
    return hi


def antragsstellen(text: str, ohne_valwissen: bool = False) -> list[tuple[int, int, str, str]]:
    """Antragsstellen im (normalisierten) Text: (Start, Ende, Art, Klasse).

    Art: satz (Exekutive + Antragsverb in einem Satz, oder Ich-Form der Exekutive),
    feld (Zeile beginnt mit «Antrag», «Proposition», «Position du Conseil d'État» …, dazu
    die nächste nicht leere Zeile) oder vermerk (Titelvermerk in den ersten VERMERK_BEREICH Zeichen).
    Klasse: Option, «nur_abschreiben» oder '' (Stelle ohne erkennbaren Wert).
    Textbausteine (z. B. Zitat der Geschäftsordnung) werden ausgelassen.
    ohne_valwissen=True: ohne die Alternativen in VALIDIERUNGSWISSEN.
    """
    t = text
    feld_rx = ANKER_FELD_OHNE if ohne_valwissen else ANKER_FELD
    klassen = SATZ_KLASSEN_OHNE if ohne_valwissen else SATZ_KLASSEN
    stellen = []
    for m in ANKER_SATZ.finditer(t):
        a, e = _satzanfang(t, m.start()), _satzende(t, m.end())
        stellen.append((a, e, "satz"))
    for m in feld_rx.finditer(t):
        # Feldzeile und die nächste nicht leere Zeile («4. Antrag des Regierungsrates» /
        # «Nichterheblicherklärung.»)
        nach = re.match(r"\n+[^\n]*", t[m.end():])
        e = m.end() + (nach.end() if nach else 0)
        stellen.append((m.start(), e, "feld"))
    for m in ANKER_VERMERK.finditer(t, 0, min(len(t), VERMERK_BEREICH)):
        a = t.rfind("\n", 0, m.start()) + 1
        stellen.append((a, m.end(), "vermerk"))
    stellen.sort()
    aus = []
    for a, e, art in stellen:
        if aus and a < aus[-1][1] and art == aus[-1][2]:
            continue  # überlappende Treffer derselben Art einmal zählen
        k = klasse(t[a:e].replace("\n", " "), klassen)
        if k is None:
            continue
        aus.append((a, e, art, k))
    return aus


def regel_detail(kontext: str, variante: str = "geliefert") -> tuple[str, bool]:
    """Regel-Baseline mit Angabe, ob eine Antragsstelle mit Optionswert gefunden wurde.

    Varianten (REGEL_VARIANTEN):
      geliefert       Klasse der letzten Antragsstelle mit Optionswert, sonst keine_passt
      ohne_valwissen  wie geliefert, aber ohne die Alternativen in VALIDIERUNGSWISSEN
      rueckfall       wie geliefert; ohne Antragsstelle: Typwort «Interpellation» im Kontext ->
                      keine_passt, sonst ablehnen (einfache Vergleichsgrösse der Prüfung p2)
    """
    assert variante in REGEL_VARIANTEN, variante
    stellen = antragsstellen(normalisieren(kontext), ohne_valwissen=variante == "ohne_valwissen")
    klassen = [k for _, _, _, k in stellen if k in OPTIONS_KLASSEN]
    if klassen:
        return klassen[-1], True
    if variante == "rueckfall":
        return ("keine_passt" if RX_TYPWORT.search(kontext) else "ablehnen"), False
    return "keine_passt", False


def regel_baseline(kontext: str, variante: str = "geliefert") -> str:
    """Regel-Baseline: Klasse der letzten Antragsstelle mit Optionswert im Kontext.

    Die letzte Stelle, weil der Antrag meist am Schluss steht und frühere Stellen oft den
    Vorstoss zitieren (Messung in iter2-empfehlung.md). Ohne Antragsstelle mit Wert gilt
    «keine_passt» (der Text lässt keinen Antrag erkennen). Der Kontext wird vorher
    normalisiert wie die Dokumente. Varianten siehe regel_detail().
    """
    return regel_detail(kontext, variante)[0]

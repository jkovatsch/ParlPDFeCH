# SPDX-License-Identifier: Apache-2.0
"""Plan `crisp-dm/04-modeling/plan-ech-from-pdf.md`, task <id>: the value rules for the affair type and the affair
number. The rules read the two values from the PDF text. They do not read the export.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5) for the AI
agent. Status: EXCEPTION, NOT RELEASED. No human checked this file. Version 3 (round 3, 13.10.2026) was written AFTER
THE OPENING of the closed parliaments: the author read documents of all 44 development parliaments. Thus a value of
this version on a development document is not a value on a parliament that no author read.

1 Inputs
  One `Doc` of `src/m11_values_base.py`: the blocks of Docling with page, label and character range. The rules use
  the text, the lines, the pages and the Docling labels. They do not use the export record, the B1-S decisions,
  a state file, the block roles or the parliament key. Thus they work for a PDF with no rule file.
  The term list `typ_lokal` of `src/m02_ech_regeln.py` is imported. It changes a printed type word to the list
  value of eCH-0295. It is the same list that makes the reference value (`typ_ech`). It reads no data.

2 Output
  `read_affair_type(doc)` and `read_affair_number(doc)` give a `ValueCandidate` or a `NotFound`.
  Affair type: `value` is the printed type word, `normalised` is the list value (motion, postulate,
  interpellation, request, question, parliamentary_initiative, draft_decree).
  Affair number: `value` is the printed number, `normalised` is the number with no space at a separator.
  The rules give no probability. The probability of a value is the measured precision of its tier.

3 Tiers of the affair type (in the order of the rule; the first tier with a value gives the result)
  type_cue_label           the type word after a label such as "Vorstossart", "Type d'intervention" or "Catégorie".
                           A line of a check box list is not the value of a label.
  type_checkbox            the one selected line of a list of type words with check boxes. A printed mark (x, ☒)
                           is stronger than the Docling label.
  type_checkbox_odd_mark   the one line of such a list whose mark is different from the mark of all other lines
                           (no line has a known mark of selection).
  type_line_start          a type word of a parliament instrument at the start of a block in the first 15 lines
                           (marks, an agenda number with "Eingereichte", "Testo dell'" can be before it).
  type_response_phrase     a type word after a response word (Beantwortung, Antwort, Réponse, Risposta) in the head.
  type_line_start_late     a type word at the start of a short text block or of a section header in the lines
                           16 to 40 of the first page (no bullet before the word).
  type_response_phrase_late  a type word after a response word in a section header in the lines 16 to 40.
  type_line_word           a common word that is a type word only at a line start (Anfrage, Auftrag, Question),
                           at the start of a block.
  type_head_inline         the first type word in a title line of the first 15 lines: only a title prefix is before
                           it ("Werkbetriebe: Postulat betr.", "Nr. 2020-425 R-151-10 Motion ...").
  type_line_start_gov      a type word at the start of a block, and a government document word starts a block
                           before it: a document of the executive ABOUT an intervention (see chapter 3a).
  type_head_inline_gov     a type word in the text of the first 15 lines, after a government document word.
  type_submission_phrase   a type word in a submission phrase of the first page ("folgende Motion", "a déposé").
  type_head_inline_text    the first type word in a sentence of the first 15 lines (running text).
  type_government_head     a government document word (Botschaft, Bericht und Antrag, Messaggio, Beschlussantrag)
                           at a block start in the first 15 lines (not in a list item, not after a bullet, not a
                           law citation "Décret du 4 février 1987"). The list value is draft_decree.
  type_government_phrase   the phrase "Antrag an den <parliament>" in a head block. The list value is draft_decree.
  No value: a head that starts with a word with no list value (Petition, Volksinitiative, Standesinitiative,
  Résolution) gives "not found in the PDF" with the reason not_in_document_type. A type word before
  "trasformata" / "umgewandelt" (the former type) and a type word that is a label in a stack of labels
  ("Richtlinienmotion:") are not read.

3a A document of the executive about an intervention (two readings)
  Example: "Bericht und Antrag" / "Postulat <name> - Beantwortung". Reading A: the affair is the intervention
  (the document is a step of that affair). Reading B: the document is an affair of its own with the type of
  the government document (draft_decree). The PDF does not say which reading a register uses. The rule gives
  reading A (the type word of the intervention) and puts it in the tiers type_line_start_gov and
  type_head_inline_gov. The government word is in the list `others` (tier type_government_head).
  Local type names with no pattern (version 2, 13.10.2026): Weisung, Antrag, Kreditantrag, Bericht und Antrag,
  Botschaft, Vorlage, Beschlussantrag, Dekret map to draft_decree by the term list, and the rule reads them
  only as the head word of the document. Names that are not printed as a document kind (Geschäft des
  Bundesrates, Politisches Geschäft, Gesetz, Verfassung, Kreditgeschäft, Verwaltungsgeschäft, Memorialsantrag)
  give no value: the reader does not derive a type from the content of a document.

4 Tiers of the affair number (same order rule). The reader gives the number as printed. It adds no letter.
  Label words (lists AFFAIR_LABELS and INTERVENTION_LABELS, German, French and Italian): Geschäftsnummer,
  Geschäfts-Nr., Geschäft Nr., Gesch.-Nr., Parlamentsgeschäft; N° de l'objet, N° d'objet, Numéro de l'objet,
  N° d'affaire, N° de l'affaire, Objet n°; Numero dell'oggetto, N. oggetto, Numero dell'affare; Vorstoss-Nr.,
  N° de l'intervention, Numero dell'atto. The value is on the same line, in the next cell, on the line below or
  in the same column of the next line.
  number_cue_affair_line        the number after an affair label on the same line or in the same table cell, on the
                                first page. The label can go over a line end. After the plain word "Geschäft",
                                1 or 2 digits are not a number.
  number_cue_affair_below       the number on a line below a label line with an affair label.
  number_cue_affair_table       the number in the column of an affair label: a table row of labels and the next
                                row ("N° de l'objet <tab> Date du dépôt" / "23.054 <tab> 24.10.2023"), a row of
                                label words and a row of values, or a row of n label words and n value lines.
  number_cue_council            the number after a council short form and "Nr." (GR Nr., GGR-Nr., GRG Nr.), first
                                page; also the form "12 EA 3 29" (period, letters of the type, 2 numbers).
  number_cue_affair_council     the number after a council short form and an affair cue ("GR Geschäft Nr. 145/2016").
  number_form_year_letters      the form year, capital letters, running number (2015.RRGR.394) on the first page.
                                Not after the word "Signatur" (the signature of a records system).
  number_docpart_cue            a number with a document part after "Nr." ("Nr. 22-26.633.02", "Reg. Nr.:
                                22-26.607.01"). See chapter 4a.
  number_docpart_head           a number with a document part alone on a head line, at its start or at its end
                                ("19.5415.01", "21.1626.01, Ratschlag ...").
  number_cue_affair_digits      as number_cue_affair_line or number_cue_affair_below, but the value has digits only
                                (3 or more): a running number of a records system.
  number_cue_intervention_line  the number after an intervention label on the same line (Vorstoss-Nr.).
  number_cue_intervention_below the number on a line below a label line with an intervention label, or in its column.
  number_nr_type                "Nr.", the number, then a type word at the start of a title line.
  number_type_cue               the number (with a separator or letters) after a type word and "Nr.", "No" or
                                "Nummer". The type word starts a head line or a section header of the first page.
  number_type_adjacent          the number (with a separator or letters) directly after such a type word.
  number_type_paren             a number with a separator in brackets after a type word, in a block of the head.
  number_bare_nr                a head line that holds only "Nr." and a number with a separator or letters.
  number_line_dotted            the form 2 digits, point, 3 or 4 digits at the start of a head line (22.406), or at
                                the start of a block in the lines 16 to 25. A letter n or s after it is not read.
  number_line_dotted3           3 groups with points alone on a line, not in the form of a date (22.16.01,
                                "16.05.3 17-7"), in the first 40 lines. Not a value line of a row of labels.
  number_line_form              a head line that holds only a number with letters ("M 189", "MM N. 91/2019",
                                "P 16/2021"); also "3363. 2017/165" (agenda number first) and "1/2021: text".
  number_line_year_running      a head line that holds only digits with a year ("2025.03", "145/2009").
  number_after_head_date        a head line with a date, a stroke and a number ("11 giugno 2024 / 115.24").
  number_line_dotted3_type      3 groups with points alone on a line in the form of a date (23.03.03), and the
                                line before or after holds only a type word.
  number_docpart_last_line      a number with a document part alone on one of the last 3 lines of the first page
                                or of the document.
  number_docpart_page1          a number with a document part at the start or the end of a short line of page 1.
  number_letter_code_cue        one capital letter and 6 digits after the label "Präsidial-Nr." ("P180214").
  number_letter_code_line       one capital letter and 6 digits alone on a line of the first page, or at the end
                                of a head line. It is the code of a decision of the executive.
  number_type_cue_late, number_type_adjacent_late
                                as number_type_cue and number_type_adjacent, but the line is the start of a text
                                block in the lines 16 to 40 (not a section header).
  number_paren_code             1 or 2 capital letters and 3 to 5 digits in brackets after a type word or at the
                                end of a table row with the cue "Geschäft": "(P2311)", "(RM2513)".
  number_cue_file               the number after "zu den Akten" (file cue of a distribution list), each page.
  number_bare_nr_late           "Nr." and a number alone on a line after the head of the first page (a stamp).
  number_line_form_late         letters of the type word and a number alone on a line after the head ("M 126/2010").
  number_form_year_letters_p2   the form year, capital letters, number in a page header or footer of page 2.
  number_type_cue_inline, number_type_adjacent_inline
                                as number_type_cue and number_type_adjacent, but the type word is in a sentence
                                of a head line (often a reference to a different affair).
  number_type_adjacent_digits   3 to 5 digits directly after a type word ("Interpellation 8145; ...", "Anfrage
                                16003 betreffend"), in each kind of line. A decision word with its own number
                                before the type word does not stop the rule ("Beschluss Nr. 121-2021 Interpellation
                                8145").
  number_cue_running_footer     WEAK: the number after "Laufnummer" in a page header or footer (each page).
  number_cue_affair_sentence    WEAK: the number after an affair label, and running text follows the number
                                ("Geschäfts-Nr. 52.14.01 gemäss Auftrag ..."): a reference in a sentence.
  number_type_cue_seq           WEAK: digits only after a type word and "Nr." ("Interpellation Nr. 121"): the
                                sequence number of the type or of the session, not the affair number.
  number_cue_affair_short       WEAK: 1 or 2 digits, or "3.3", after an affair label ("Geschäft Nr. 5"): the
                                item number of a session.
  number_form_year_serial6      WEAK: the form 2 digits, point, 6 digits ("08.000136") in the head, in a page
                                header or footer or in a short line of the first page.
  number_cue_bare_label         the number below a label "Numero" / "Nummer" that is directly below a government
                                document word ("Messaggio" / "numero" / "8608").
  number_line_registry_code     a registry code at the end of a head line ("G3.1.4", "L 3.1.6", "9.0.0"). WEAK:
                                in some registers it is the affair number, in others the position of the plan.
  No value: a head line that holds only "Nr." and digits (for example "Nr. 726"), and the number below a label
  "Numero" / "Nummer" with no government word before it (it is the number of a decision of the executive in
  the documents that the author read). These are in the list `others` only.

4a A number with a document part (decision of the author, round 3)
  Form: 2 digits (or a period "22-26"), a point or a comma, 3 or 4 digits, a point, 2 digits: "19.5497.01",
  "22-26.633.02". The last group counts the documents of the affair (01 = the text, 02 = the response, ...).
  The reader gives the part BEFORE the document part as the value ("19.5497"): the span of the value is printed
  text. The key `detail` holds the document part and the full printed text. Reason: the affair number is the
  same for each document of the affair. The form is the evidence: a decision word before it ("Reg. Nr.") does
  not stop the rule. A line with this form is read by the docpart tiers only.

5 Exclusions of the affair number (function `refuse`)
  date, page_number, phone, postal_code, law_number, amount, year, decision_number. A number after a decision
  word (Beschluss-Nr., Prot.-Nr., SRB, RRB, N° d'ACE, Laufnummer, Aktenzeichen, Référence, Risoluzione, RG) is not
  an affair number. A text with the form of a date and a year of 2 digits (24.01.05) is given only after an
  affair cue word or by the tier number_line_dotted3_type. More exclusions in the tiers: 1 or 2 digits after a
  type word; a count ("Postulat 12 Mitunterzeichnende"); a month and a year ("09.2023"); letters in brackets
  that are not the letters of the type word ("(RB 10.4111)").

6 What the author read
  Version 1: open parliaments only (31 parliaments, the 3 languages). Version 2 (improvement round): the
  outcomes of the open part against the export (first table of 13.10.2026) and the review by eye of 60 open
  documents. Version 3 (round 3, after the opening): the outcomes of the closed part, the 2 reading checks by
  eye, and documents of all 44 development parliaments. Thus the values of ALL development documents are
  optimistic. The closed part has 0 Italian documents: the Italian label words of version 3 are not tested on a
  form. No rule uses a parliament or a document.
  The reader was not tuned to an export value that the document does not print (a type letter that the export
  adds: "I 2023-765" for the printed "Interpellation Nr. 2023-765").

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_type_number.py read DOC_ID
  uv run --offline --frozen --no-sync python src/m11_values_type_number.py coverage [--out FILE] [--skip KEY,KEY]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import m11_values_base as vb  # noqa: E402
from m02_ech_regeln import typ_lokal  # noqa: E402  (term list only; the module reads no data)

VERSION = "m11-values-type-number-3"
HEAD_LINES = 15          # the head: the line count of probe 3
PAGE1_LINES = 40         # the limit for the late tiers and for the label search
DOTTED_LINES = 25        # the limit for the form 22.406 at the start of a block
TYPE_VALUES = ("motion", "postulate", "interpellation", "request", "question", "parliamentary_initiative",
               "draft_decree")

TYPE_TIERS = ("type_cue_label", "type_checkbox", "type_checkbox_odd_mark", "type_line_start", "type_response_phrase",
              "type_line_start_late", "type_response_phrase_late", "type_line_word", "type_head_inline",
              "type_line_start_gov", "type_head_inline_gov", "type_submission_phrase", "type_head_inline_text",
              "type_government_head", "type_government_phrase")
NUMBER_TIERS = ("number_cue_affair_line", "number_cue_affair_below", "number_cue_affair_table", "number_cue_council",
                "number_cue_affair_council", "number_form_year_letters", "number_docpart_cue", "number_docpart_head",
                "number_cue_affair_digits",
                "number_cue_intervention_line", "number_cue_intervention_below",
                "number_nr_type", "number_type_cue", "number_type_adjacent", "number_type_paren", "number_bare_nr",
                "number_line_dotted", "number_line_dotted3", "number_line_form", "number_line_year_running",
                "number_after_head_date",
                "number_line_dotted3_type", "number_docpart_last_line", "number_docpart_page1",
                "number_letter_code_cue", "number_letter_code_line",
                "number_type_cue_late", "number_type_adjacent_late", "number_paren_code", "number_cue_file",
                "number_bare_nr_late", "number_line_form_late", "number_form_year_letters_p2",
                "number_type_cue_inline", "number_type_adjacent_inline", "number_type_adjacent_digits",
                "number_cue_running_footer", "number_cue_affair_sentence", "number_type_cue_seq", "number_cue_affair_short",
                "number_form_year_serial6", "number_cue_bare_label", "number_line_registry_code")
REFUSED_TIER = "number_refused_plain_nr"      # only in the list `others`; never the result

# ------------------------------------------------------------------ type words (patterns on the folded text)
# The folded text is lower case with no accents (vb.fold_map). Each pattern gives the printed wording. The list
# value comes from typ_lokal(wording). Source of the terms: TYP_LOKAL_REGELN of src/m02_ech_regeln.py and the head
# lines of open documents.
_INSTRUMENT = (
    r"parlamentarische[nr]? initiative|initiative parlementaire|iniziativa parlamentare"
    r"|(?:dringliche[nrs]? |schriftliche[nrs]? )?interpellation(?:en|s)?(?: urgente| ecrite)?|interpellanza"
    r"|(?:dringliche[nrs]? )?(?:schriftliche[nrs]?|kleine[nrs]?|einfache[nrs]?) anfragen?"
    r"|dringliche[nrs]? anfragen?|kleinanfrage"
    r"|einfache[ns]? auskunftsbegehren|questions? ecrites?|interrogazione(?: orale)?"
    r"|questions? orales?|fragestunde(?= (?:[a-z]{1,2} ?\d|betreffend))"
    r"|anfrage(?= (?:\d{3,6} )?(?:von|betr|betreffend)(?![a-z]))"
    r"|(?:dringliche[nrs]? )?postulat(?:es|e|o|s)?|anzug"
    r"|(?:dringliche[nrs]? )?(?:richtlinien|volks|budget-?|globalbudget-?)?motion(?:en|s)?(?: urgente)?|mozione"
    r"|volksauftrag")
INSTRUMENT_RX = re.compile(r"(?<![a-z-])(?:" + _INSTRUMENT + r")(?![a-z])")
# A type word in capital letters with a space between the letters: "P O S T U L A T".
SPACED_RX = re.compile(r"(?<![a-z])((?:[a-z] ){4,}[a-z])(?![a-z])")
# A type word that names the former type of the affair is not the type: "(INTERPELLANZA trasformata in ...".
FORMER_TYPE_RX = re.compile(r"\s+(?:trasformat[ao]|umgewandelt|transformee?)(?![a-z])")
# Words that are type words only when they are the whole start of a line (they are common words in a sentence).
LINE_ONLY_RX = re.compile(r"(?:anfrage(?= *$| *:| (?:von|an|der|des|betr|betreffend|zur|zum|nr|gemass|gemaess)\b| [\"']"
                          r"| (?!(?:19|20)\d{2}[;:,])\d{3,6}[;:,] "
                          r"|[^.;]{0,120}, beantwortung(?![a-z]))"
                          r"|auftrag(?= *$| *:| (?:fraktion|betr|betreffend)\b| (?:der|des) [^.;]{0,60} betreffend\b)"
                          r"|questions?(?= *$| *:| *\(art))")
# Compound words of a response: the first part is the type word.
COMPOUND_RX = re.compile(r"(?<![a-z])(motion|postulat|interpellation)s(?:antwort|beantwortung|bericht)(?![a-z])")
GOVERNMENT_RX = re.compile(
    r"(?<![a-z])(?:bericht und antrag|antrag und bericht|bericht & antrag|botschaft|weisung|vorlage|ratschlag"
    r"|messaggio(?: municipale)?|preavis|projet de (?:loi|decret|deliberation)|rapport et proposition"
    r"|antrag des (?:stadt|gemeinde|regierungs)rate?s|[a-z]*ratsbeschluss|beschluss des [a-z]+rate?s"
    r"|kreditvorlage|kreditantrag|beschlussantrag|dekret|decret)(?![a-z])")
# A law citation is not a document kind: "Décret du 4 février 1987 sur ...".
LAW_CITATION_RX = re.compile(r"\s+(?:du|vom|del|dell') ?\d")
# A submission of the executive to the parliament, in a head block: "Antrag an den Grossen Gemeinderat".
GOV_PHRASE_RX = re.compile(
    r"(?<![a-z])antrag an (?:den|das|die) (?:grossen? |hohen )?(?:gemeinderat|landrat|kantonsrat|einwohnerrat"
    r"|stadtrat|rat|landtag|parlament|stadtparlament|gemeindeparlament|generalrat)(?![a-z])")
# French: the response to a question ("RÉPONSE DE LA MUNICIPALITÉ A LA QUESTION").
QUESTION_RESPONSE_RX = re.compile(r"(?<![a-z])reponse (?:[a-z']+ ){0,5}?a la (question)(?! (?:de savoir|suivante))(?![a-z])")
# "MM" is the short form of "Messaggio municipale" before a number (documents in Italian).
MM_RX = re.compile(r"(?<![A-Za-z])MM(?= ?(?:[Nn][.°o]\.? ?)?\d)")
BLOCKED_RX = re.compile(
    r"(?<![a-z])(?:petition|petizione|volksinitiative|einzelinitiative|standesinitiative|kantonsinitiative"
    r"|gemeindeinitiative|initiative populaire|iniziativa popolare|initiative cantonale|iniziativa cantonale"
    r"|resolution|risoluzione|vernehmlassung(?:santwort)?)(?![a-z])")
TYPE_LABEL_RX = re.compile(
    r"(?<![a-z])(?:vorstossart|vorstosstyp|geschaftsart|geschaftstyp|art des vorstosse?s|typ des vorstosse?s"
    r"|type d'intervention|genre d'intervention|type d'objet|categorie|tipo di atto|tipo d'atto)(?![a-z]) *:? *")
RESPONSE_RX = re.compile(
    r"(?<![a-z])(?:beantwortung|antwort|stellungnahme|begrundung|reponse|risposta|rapport|bericht)(?![a-z])")
SUBMISSION_RXS = (
    re.compile(r"(?<![a-z])(?:folgende[nrs]?|nachstehende[nrs]?) (?:[a-z]+ ){0,2}?(?P<t>" + _INSTRUMENT + r")(?![a-z])"),
    re.compile(r"(?<![a-z])(?:a|ont|ai|avons) depose (?:une?|la|le|l') ?(?:[a-z]+ ){0,2}?(?P<t>" + _INSTRUMENT + r")(?![a-z])"),
    re.compile(r"(?<![a-z])(?:la|le|l') ?(?P<t>" + _INSTRUMENT + r") suivante?(?![a-z])"),
    re.compile(r"(?<![a-z])(?:la|il) seguente (?P<t>" + _INSTRUMENT + r")(?![a-z])"),
)
# Before a type word at a line start: marks; an agenda number and "Eingereichte" (minutes); "Testo dell'".
LINE_START_PREFIX_RX = re.compile(
    r"[^a-z]{0,8}(?:(?:[a-z] ?\.? )?eingereichte[rs]?,? |test[oi] dell'|texte de (?:l'|la )|text de[rs] )?"
    r"(?:(?:a |de )?l'|all')?\Z")
MARK_PREFIX_RX = re.compile(r"[^a-z0-9]{0,4}(?:[a-z0-9]{1,2} )?[^a-z0-9]{0,2}\Z")
SELECTED_RX = re.compile(r"^\s*[xX×☒☑⊠⌧✓✔■●]\s")

# ------------------------------------------------------------------ number patterns (on the printed text)
COUNCIL_ABBR = ("GGR", "GGr", "GRG", "GR", "ER", "EWR", "KR", "LR", "SR")
# Label words of the affair number (a form, a table or a list names the value). The lists are the source of
# AFFAIR_CUE_RX and INTERVENTION_CUE_RX: each wording of a list must match its pattern (unit case of the test file).
AFFAIR_LABELS = {
    "de": ("Geschäftsnummer", "Geschäfts-Nr.", "Geschäftsnr.", "Geschäft Nr.", "Gesch.-Nr.", "Gesch. Nr.",
           "Geschäfts-No", "Parlamentsgeschäft", "Ratsgeschäft", "Sachgeschäft"),
    "fr": ("N° de l'objet", "N° d'objet", "No de l'objet", "Numéro de l'objet", "Numéro d'objet", "N° de l'affaire",
           "N° d'affaire", "Numéro de l'affaire", "Numéro d'affaire", "Objet n°", "Affaire n°"),
    "it": ("Numero dell'oggetto", "N. dell'oggetto", "N° dell'oggetto", "Numero oggetto", "N. oggetto", "N° oggetto",
           "Numero dell'affare", "N. affare", "Oggetto n.", "Oggetto n°"),
}
INTERVENTION_LABELS = {
    "de": ("Vorstoss-Nr.", "Vorstossnummer", "Vorstoss Nr.", "Nummer des Vorstosses"),
    "fr": ("N° de l'intervention", "N° d'intervention", "Numéro de l'intervention", "Intervention n°"),
    "it": ("Numero dell'atto", "N. dell'atto", "N. atto", "Numero atto", "Numero dell'atto parlamentare",
           "N. dell'intervento", "Numero dell'intervento"),
}
_NUM = (r"(?:[A-Z]{1,4}[ .-]?)?\d{1,7}"
        r"(?:\s?[./-]\s?(?:\d{1,6}|[A-Z]{2,8}(?:-[A-Z]{2,4})?(?=\s?[./-]\s?\d)))*")
NUM_RX = re.compile(_NUM)
_END = r"(?![\w°])(?![.,]\d)"
_NO = r"(?:n ?[°ºo]\.?|n\.|num[ée]ro)"                  # "N°", "No", "N.", "Numéro", "Numero" (case: see the use)
AFFAIR_CUE_RX = re.compile(
    r"(?i:gesch(?:ä|ae|a)fts?[- ]?(?:nr|no|nummer)\b\.?"
    r"|gesch\.[- ]?nr\b\.?"
    r"|(?<![a-zäöü])(?:parlaments|rats|sach)?gesch(?:ä|ae|a)ft(?=\s+(?:[A-Z]{1,4} )?\d)"
    r"|(?<![a-zäöü])(?:parlaments|rats|sach)gesch(?:ä|ae|a)ft(?![a-zäöü])"
    r"|(?<![a-zà-ÿ])" + _NO + r" ?(?:de l['’] ?|d['’] ?|du |de la )?(?:objet|affaire)(?![a-zà-ÿ])"
    r"|(?<![a-zà-ÿ])(?:objet|affaire) n ?[°º]"
    r"|(?<![a-zà-ÿ])" + _NO + r" ?(?:dell['’] ?|d['’] ?|dell )?(?:oggetto|affare)(?![a-zà-ÿ])"
    r"|(?<![a-zà-ÿ])oggetto n(?:\.| ?[°º]))")
INTERVENTION_CUE_RX = re.compile(
    r"(?i:vorstoss[- ]?(?:nr|nummer)\b\.?|vorstossnummer|nummer des vorstosse?s"
    r"|(?<![a-zà-ÿ])" + _NO + r" ?(?:de l['’] ?|d['’] ?)intervention(?![a-zà-ÿ])|(?<![a-zà-ÿ])intervention n ?[°º]"
    r"|(?<![a-zà-ÿ])" + _NO + r" ?(?:dell['’] ?|d['’] ?)?(?:atto|intervento)(?! di| del)(?![a-zà-ÿ])(?: parlamentare)?)")
# A word of a label row: a row that holds only labels ("Beschlussnummer Geschäftsnummer Ordnungsnummer").
LABEL_WORD_RX = re.compile(r"(?i)[a-zäöüéè.'’-]*(?:nummer|nr\.?|datum|traktandum|date|data|num[ée]ro)\Z")
# The number of a council after its cue in the form "12 EA 3 29": period, 2 or 3 letters of the type, 2 running numbers.
SPACED_NUM_RX = re.compile(r"\s*:?\s*(\d{1,2} [A-Z]{2,3} \d{1,3} \d{1,4})(?![\w.])")
# A number with a document part: "19.5497.01", "22-26.633.02". The last group (2 digits) counts the documents of
# the affair; the affair number is the part before it. The group before the document part has 3 or 4 digits.
DOCPART_RX = re.compile(r"(?<![\d,/-])(?<!\d\.)(\d{2}(?:\s?-\s?\d{2})?[.,]\d{3,4})\.(\d{2})(?![\w])(?!\.\d)")
# One capital letter and 6 digits ("P180214"): the code of a decision of the executive.
LETTER_CODE_RX = re.compile(r"(?<![\w.-])([A-Z]\d{6})(?![\w.-])")
LETTER_CODE_CUE_RX = re.compile(r"(?i)pr(?:ä|ae)sidial[- ]?(?:nr|nummer)\b\.?\s*:?\s*\Z")
# The running number of a records system in a page header or footer: "Laufnummer · 9596", "Laufnummer 2025-0228".
RUNNING_CUE_RX = re.compile(r"(?i)(?<![a-zäöü])laufnummer\s*[·:.•-]?\s*((?:19|20)\d{2}-\d{1,5}|\d{3,6})(?![\w.-])")
# 2 digits of the year, a point, 6 digits ("08.000136").
# 1 or 2 digits, or 2 such groups with a point: the item number of a session ("5", "3.3").
SHORT_RX = re.compile(r"\d{1,2}(?:\.\d{1,2})?")
YEAR_SERIAL6_RX = re.compile(r"(?<![\d.])(\d{2}\.\d{6})(?![\d.])")
# A label line that holds only "Numero" or "Nummer": the document does not say what the number is.
BARE_LABEL_RX = re.compile(r"(?i)\s*(?:num[ée]ro|nummer)\s*:?\s*\Z")
COUNCIL_CUE_RX = re.compile(r"(?<![A-Za-z])(?:" + "|".join(COUNCIL_ABBR) + r")[- ]?(?:Nr|NR|No|N°)\b\.?")
NR_CUE = r"(?i:(?<![a-zäöü])(?:nr|no|n°|nº|n\.|nummer|num[ée]ro)(?![a-zäöü])\.?)"
YEAR_LETTERS_RX = re.compile(
    r"(?<![A-Za-z0-9.])\d{4}\. ?[A-Z]{2,8}(?:-[A-Z]{2,4})?\. ?\d{1,6}(?!\w)(?!\.\d)(?! \d{2}\.[A-Z]{2,8}\.\d)")
# 22.406 at a line start; a letter n or s (the council) can touch the number ("21.067n : ..."): it is not read.
DOTTED_RX = re.compile(r"\s*(\d{2}\.\d{3,4})(?:[ns](?![a-z]))?(?=\s*$|\s*:\s|\s+[^\W\d_]|\s+[\"«])")
# 3 groups of 2 digits with points, alone on a line (23.03.03, 22.16.01); a part "17-7" can follow ("16.05.3 17-7").
DOTTED3_RX = re.compile(r"\s*(\d{2}\.\d{2}\.\d{1,2}(?: \d{2}-\d{1,2})?)\s*\Z")
# A code of 1 or 2 capital letters and 3 to 5 digits in brackets at a line end: "(P2311)", "(RM2513)".
PAREN_CODE_RX = re.compile(r"\(([A-Z]{1,2} ?\d{3,5})\)\s*\Z")
# A number in brackets after a type word: "(54.25.01)", "(Nr. 54.15.03)", "(GGR 16.05.3 16-10)", "(19.464)".
PAREN_NUM_RX = re.compile(r"\(\s*(?:(?:" + "|".join(COUNCIL_ABBR) + r")\s+)?(?P<nr>" + NR_CUE + r"\s*)?(?P<n>"
                          + _NUM + r"(?: \d{2}-\d{1,2})?)\s*\)")
# A head line with a date, a stroke and a number of the form 115.24: "11 giugno 2024 / 115.24".
HEAD_DATE_NUM_RX = re.compile(r"\s/\s*(\d{1,3}\.\d{2})\s*\Z")
# The file cue of a distribution list: "zu den Akten (2022-844)".
FILE_CUE_RX = re.compile(r"(?i)(?<![a-zäöü])(?:zu )?den akten\s*\(?\s*((?:19|20)\d{2}-\d{1,5})(?!\d)")
# A registry code at a line end: a capital letter and groups with points ("G3.1.4", "L 3.1.6", "F6.A", "9.0.0").
REGISTRY_RX = re.compile(r"(?:^|\s)([A-Z] ?\d(?:\.\d{1,2}){1,3}|[A-Z]\d\.[A-Z]|\d\.\d\.\d(?:\.\d)?)\s*\Z")
# "Nr. 025/2025 Postulat ...": the number, then the type word.
NR_TYPE_RX = re.compile(r"\s*" + NR_CUE + r"\s*:?\s*(" + _NUM + r")(?=\s+\S)")
LATE_FORM_RX = re.compile(r"\s*([A-Z]{1,3} ?\d{1,4}(?:\s?/\s?(?:(?:19|20)\d{2}|\d{2}))?)\s*\Z")
COUNT_AFTER_RX = re.compile(r"(?i)\s+(?:mitunterzeichn|unterzeichn|unterschrift|frage|punkt|massnahme|jahr|signatair"
                            r"|cofirmatar|firmatar|question)")
STRONG_PREFIX_RX = re.compile(
    r"[^a-z]{0,8}(?:(?:schriftliche[nr]? |mundliche[nr]? )?(?:beantwortung|antwort|stellungnahme|reponse|risposta"
    r"|bericht|rapport|rapporto)(?: de[rs]| zu[rm]?| auf die| auf das| a la| au| a l'| all'| alla| sur la| sur le"
    r"| sulla| sull')? ?)?\Z")
BARE_NR_RX = re.compile(r"\s*\(?\s*" + NR_CUE + r"\s*:?\s*(" + _NUM + r")\s*\)?\s*\Z")
LINE_FORMS = (
    ("agenda_year_running", re.compile(r"\s*\d{1,4}\.\s((?:19|20)\d{2}/\d{1,4})\s*\Z")),
    ("running_year_colon", re.compile(r"\s*(\d{1,4}/(?:19|20)\d{2})(?=:\s+\S)")),
    ("year_running", re.compile(r"\s*((?:19|20)\d{2}\s?[/.-]\s?\d{1,4})\s*\Z")),
    ("running_year", re.compile(r"\s*(\d{1,4}\s?[/-]\s?(?:19|20)\d{2})\s*\Z")),
    ("letters_running_year", re.compile(r"\s*([A-Z]{1,3}[ -]?\d{1,4}\s?/\s?(?:19|20)\d{2})\s*\Z")),
    ("letters_running", re.compile(r"\s*([A-Z]{1,3}[ -]?\d{1,4})\s*\Z")),
)
PREFIX_NR_RX = re.compile(r"\s*(([A-Z]{1,3}) " + NR_CUE + r" ?(\d{1,4}\s?/\s?(?:19|20)\d{2}))\s*\Z")
# Words before a number that is NOT an affair number (decision, minutes, register, land, account, reference).
NEGATIVE_RX = re.compile(
    r"(?i:beschl(?:uss|\.)?(?:es)?[- ]?(?:nr|nummer)|beschluss\b|prot(?:okoll|\.)?[- ]?(?:nr|nummer)"
    r"|\b(?:srb|rrb|grb|strb|stb)\b|n ?[°ºo]\.? ?d['’] ?ace|laufnummer|registratur|reg\. ?nr|aktenzeichen"
    r"|archiv|r[ée]f[ée]rence|referenz|n\. ?rif|riferimento|dossier|\bn ?[°ºo]\.? ?de document|dokument[- ]?nr"
    r"|konto|parzelle|grundst[üu]ck|kat\.?[- ]?nr|\bgb[- ]?nr|plan[- ]?nr|objekt[- ]?nr|traktand\w*|sitzung"
    r"|beilage|geko|bericht nr|rapport n|version|risoluzione|r[ée]solution|\brg\b)")
_REFUSE_BEFORE = (
    ("phone", re.compile(r"(?i)(?:tel|telefon|t[ée]l[ée]phone|t[ée]l|fax|telefax|natel|mobile)\.?\s*:?\s*(?:\+\d{2}\s*)?\Z")),
    ("phone", re.compile(r"\+\d{2}\s*(?:\(0\)\s*)?\Z")),
    ("law_number", re.compile(r"(?i)(?:\b(?:sr|rs|srs|bgs|sgs|bsg|rsb|gs|ls|ng|gdb|art|artikel|article|abs|ziff|lit|al|cpv)\.?|§+)\s*\Z")),
    ("page_number", re.compile(r"(?i)\b(?:seite|page|pagina|pag\.|s\.|p\.)\s*\Z")),
    ("amount", re.compile(r"(?i)(?:\bchf|\bfr\.|\bsfr\.?|\beur|€)\s*\Z")),
    ("postal_code", re.compile(r"(?i)\b(?:ch|fl)-\Z")),
)
_REFUSE_AFTER = (
    ("amount", re.compile(r"(?i)\s*(?:%|franken\b|francs?\b|franchi\b|chf\b|fr\.|mio\b|million|m2\b|m²|uhr\b)")),
    ("page_number", re.compile(r"(?i)\s*(?:von|de|di|sur)\s+\d{1,3}\s*\Z")),
)
PHONE_RX = re.compile(r"0\d{2} ?\d{3} ?\d{2} ?\d{2}\Z|\d{3} \d{2} \d{2}\Z")
MONTH_AFTER_RX = re.compile(r"\.? ?(?:" + "|".join(sorted(vb.MONTHS, key=len, reverse=True)) + r")(?![a-z])")
PLACE_AFTER_RX = re.compile(r"\s+[A-ZÄÖÜ][a-zäöüéèàâ]{2,}")


def negative_before(text: str, pos: int) -> bool:
    """True if a decision word stands in the 40 characters before text[pos] and no digit stands between the word
    and the position. Thus "Beschluss-Nr. 30" is negative, and "Sitzung vom 3. Mai 2021, Motion 12/2020" is not."""
    last = None
    for m in NEGATIVE_RX.finditer(text, max(0, pos - 40), pos):
        last = m
    return last is not None and not re.search(r"\d", text[last.end():pos])


def refuse(text: str, start: int, end: int, explicit: bool = False) -> str | None:
    """The cause why text[start:end] is not an affair number, or None. `explicit`: an affair cue word or an
    intervention cue word stands directly before the span. Causes: date, phone, postal_code, law_number,
    page_number, amount, year, decision_number."""
    val, before, after = text[start:end], text[:start], text[end:]
    for h in vb.find_dates(text):
        if h.start < end and h.end > start:
            four = h.form != "numeric" or re.search(r"\d{4}", h.wording) is not None
            if four or not explicit:
                return "date"
    if MONTH_AFTER_RX.match(vb.fold_map(after[:20]).text):
        return "date"
    if PHONE_RX.match(val.strip()):
        return "phone"
    for cause, rx in _REFUSE_BEFORE:
        if rx.search(before):
            return cause
    for cause, rx in _REFUSE_AFTER:
        if rx.match(after):
            return cause
    digits = val.strip()
    if re.fullmatch(r"\d{4}", digits) and PLACE_AFTER_RX.match(after) and not explicit:
        return "postal_code"
    if re.fullmatch(r"\d{1,3}\s?/\s?\d{1,3}", digits) and not explicit:
        return "page_number"
    if re.fullmatch(r"(?:19|20)\d{2}", digits) and not explicit:
        return "year"
    if re.fullmatch(r"(?:19|20)\d{2}\s?[-/]\s?(?:19|20)\d{2}", digits) and not explicit:
        return "year"
    if negative_before(text, start):
        return "decision_number"
    return None


def normal_number(value: str) -> str:
    """The printed number after norm_text, with no space at a separator: "2022/ 639" gives "2022/639"."""
    return re.sub(r"\s*([./-])\s*", r"\1", vb.norm_text(value, dehyphen=False))


# ------------------------------------------------------------------ helpers of both readers

def _page1_lines(doc: vb.Doc) -> list[vb.Line]:
    """All lines of the first page that has text, in reading order."""
    if not doc.lines:
        return []
    first = doc.lines[0].page
    return [ln for ln in doc.lines if ln.page == first]


def _fold_line(ln: vb.Line) -> vb.Folded:
    return vb.fold_map(ln.text, base=ln.char_start)


def _is_block_start(ln: vb.Line) -> bool:
    return ln.index_in_block == 0


def _values_below(lines: list[vb.Line], i: int) -> list[vb.Line]:
    """The lines that can hold the value of the label line lines[i] (a line with a label and no value).
    Layout 1: a label, then its value. Layout 2: a run of n label lines, then n value lines in the same order.
    A label line ends with a colon. If the cue line has no colon, a label line is a short line with no digit.
    The paired line comes first; then the next 3 lines after the run (some layouts put a mark between)."""
    colon = lines[i].text.rstrip().endswith(":")

    def is_label(t: str) -> bool:
        t = t.strip()
        if colon:
            return t.endswith(":")
        return len(t) <= 22 and not re.search(r"\d", t) and len(t.split()) <= 2 and not t.endswith(":")

    a = i
    while a > 0 and is_label(lines[a - 1].text) and i - a < 8:
        a -= 1
    z = i
    while z + 1 < len(lines) and is_label(lines[z + 1].text) and z - i < 8:
        z += 1
    out = []
    k = z + 1 + (i - a)
    if k < len(lines):
        out.append(lines[k])
    for ln in lines[z + 1:z + 4]:
        if ln not in out:
            out.append(ln)
    return out


# ------------------------------------------------------------------ affair type

INSTRUMENT_KINDS = ("instrument", "word")


def _type_value(wording: str) -> str:
    """The list value of a printed type word by the term list typ_lokal; an empty string for no value."""
    w = vb.norm_text(wording)
    if re.fullmatch(r"(?:\w ){4,}\w", w):
        w = w.replace(" ", "")                       # "P O S T U L A T"
    return typ_lokal(w)[0]


def _type_hits(f: vb.Folded) -> list[tuple[int, int, str]]:
    """(start, end, kind) in the folded text, in reading order. kind: instrument (a type word of a parliament
    instrument), word (a common word that is a type word only at a line start: Anfrage, Auftrag, Question),
    government or blocked."""
    hits = [(m.start(), m.end(), "instrument") for m in INSTRUMENT_RX.finditer(f.text)
            if not FORMER_TYPE_RX.match(f.text, m.end())]
    hits += [(m.start(1), m.end(1), "instrument") for m in COMPOUND_RX.finditer(f.text)]
    for m in SPACED_RX.finditer(f.text):
        if INSTRUMENT_RX.fullmatch(m.group(1).replace(" ", "")):
            hits.append((m.start(1), m.end(1), "instrument"))
    hits += [(m.start(), m.end(), "government") for m in GOVERNMENT_RX.finditer(f.text)]
    hits += [(m.start(), m.end(), "blocked") for m in BLOCKED_RX.finditer(f.text)]
    m = re.match(r"[^a-z]{0,8}", f.text)
    lo = LINE_ONLY_RX.match(f.text, m.end() if m else 0)
    if lo and not any(s <= lo.start() < e for s, e, _ in hits):
        hits.append((lo.start(), lo.end(), "word"))
    hits.sort()
    out, last = [], -1
    for s, e, k in hits:
        if s >= last:
            out.append((s, e, k))
            last = e
    return out


def _at_start(f: vb.Folded, start: int, marks: bool = False) -> bool:
    rx = MARK_PREFIX_RX if marks else LINE_START_PREFIX_RX
    return rx.match(f.text[:start]) is not None


def _type_candidate(doc: vb.Doc, span: tuple[int, int], tier: str, detail: dict | None = None):
    value = _type_value(doc.text[span[0]:span[1]])
    if value not in TYPE_VALUES:
        return None
    return doc.candidate("affair_type", span[0], span[1], value, tier, detail=detail)


def _only_marks(rest: str) -> bool:
    """True if the folded text after a type word of a list line holds no more than marks: the text of the cell
    (the caller cuts it at a tabulator), with no reference in brackets, no second type word and no single characters."""
    rest = re.sub(r"\([^)]{0,14}\)", " ", rest)
    rest = re.sub(r"[a-z]{0,2}(?:" + _INSTRUMENT + r")(?![a-z])", " ", rest)
    rest = re.sub(r"(?<![a-z0-9])[a-z0-9](?![a-z0-9])", " ", rest)
    return len(re.sub(r"[\W_]+", "", rest)) <= 3


ARTICLE_END_RX = re.compile(r"(?i)(?<![^\W\d_])(?:la|le|il|lo|l['’]|die|der|das|den|dem|des|eine?|einer|un|une|du|de"
                            r"|della|sulla|zur|zum)\s*\Z")


def _title_prefix(before: str) -> bool:
    """True if the printed text before a type word on its line is the start of a title line and not of a
    sentence: at most 60 characters, each word of 3 or more letters starts with a capital letter, and the last
    word is not an article ("Werkbetriebe: ", "Nr. 2020-425 R-151-10 ", "2012.1566 ")."""
    return (len(before) <= 60 and all(t[0].isupper() for t in re.findall(r"[^\W\d_]{3,}", before))
            and not ARTICLE_END_RX.search(before))


def _checkbox_groups(lines: list[vb.Line], doc: vb.Doc) -> list[list[tuple]]:
    """Groups of lines that form a list of type words with check boxes: each line holds a type word and no more
    than a mark before it and a mark after it. A group has 3 or more different list values, or 2 or more with a
    Docling check box label. Item: (line, span, list value, glued mark, mark before the word)."""
    items = []
    for ln in lines:
        f = _fold_line(ln)
        hit = next(((s, e) for s, e, k in _type_hits(f) if k in INSTRUMENT_KINDS and _at_start(f, s, marks=True)), None)
        glued = False
        if hit is None:
            # a mark that touches the word: "xeinfache Anfrage"
            g = re.match(r"\s*x(" + _INSTRUMENT + r")(?![a-z])", f.text)
            if g:
                hit, glued = (g.start(1), g.end(1)), True
        if hit and not ln.text.rstrip().endswith(":"):
            span = f.span(*hit)
            if not _only_marks(vb.fold(doc.text[span[1]:ln.char_end].split("\t")[0])):
                continue
            mark = doc.text[ln.char_start:span[0]].strip()
            items.append((ln, span, _type_value(doc.text[span[0]:span[1]]), glued, mark))
    groups, cur = [], []
    for it in items:
        if cur and it[0].number - cur[-1][0].number > 2:
            groups.append(cur)
            cur = []
        cur.append(it)
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        values = {it[2] for it in g if it[2]}
        boxes = sum(1 for it in g if doc.blocks[it[0].block_index].label.startswith("checkbox"))
        if len(values) >= 3 or (len(values) >= 2 and boxes >= 1 and len(g) >= 2):
            out.append(g)
    return out


def _checkbox_selection(g: list[tuple], doc: vb.Doc) -> tuple[list[tuple], str]:
    """(the selected items, kind of evidence). A printed mark (x, ☒, ...) is stronger than the Docling label: if
    one or more lines have a printed mark, only these lines are selected. If no line is selected and each line
    starts with a mark, the ONE line whose mark is different from the mark of all other lines is the odd mark."""
    marked = [it for it in g if it[2] and (it[3] or SELECTED_RX.match(it[0].text))]
    if marked:
        return marked, "printed_mark"
    labelled = [it for it in g if it[2] and doc.blocks[it[0].block_index].label == "checkbox_selected"]
    if labelled:
        return labelled, "docling_label"
    marks = [it[4] for it in g]
    if len(g) >= 3 and all(0 < len(m) <= 2 for m in marks):
        count = collections.Counter(marks)
        if len(count) == 2 and sorted(count.values())[0] == 1:
            odd = min(count, key=count.get)
            return [it for it in g if it[4] == odd and it[2]], "odd_mark"
    return [], "none"


def _type_scan(doc: vb.Doc) -> dict:
    """All type candidates of the document by tier, plus the blocked word. Used by both readers."""
    p1 = _page1_lines(doc)[:PAGE1_LINES]
    head_numbers = {ln.number for ln in doc.first_lines(HEAD_LINES)} & {ln.number for ln in p1}
    res: dict = {"cands": [], "blocked": None, "p1": p1}
    cands = res["cands"]

    def add(span, tier, detail=None, order=None):
        c = _type_candidate(doc, span, tier, detail)
        if c is not None:
            cands.append((TYPE_TIERS.index(tier), order if order is not None else span[0], c))
        return c

    # tiers type_checkbox and type_checkbox_odd_mark
    in_list: set[int] = set()
    for g in _checkbox_groups(p1, doc):
        in_list |= {it[0].number for it in g}
        sel, kind = _checkbox_selection(g, doc)
        if len(sel) == 1:
            add(sel[0][1], "type_checkbox_odd_mark" if kind == "odd_mark" else "type_checkbox",
                {"lines_of_list": len(g), "selection": kind})
    # tier type_cue_label (a line of a check box list is not the value of a label: the selected line is)
    for i, ln in enumerate(p1):
        f = _fold_line(ln)
        m = TYPE_LABEL_RX.search(f.text)
        if not m:
            continue
        rest = [(s, e) for s, e, k in _type_hits(f) if k in INSTRUMENT_KINDS and s >= m.end() and s - m.end() <= 2]
        if rest:
            add(f.span(*rest[0]), "type_cue_label", {"cue": f.text[m.start():m.end()].strip(" :"), "layout": "same line"})
        elif not f.text[m.end():].strip():
            for v in _values_below(p1, i):
                if v.number in in_list:
                    continue
                fv = _fold_line(v)
                hit = next(((s, e) for s, e, k in _type_hits(fv) if k in INSTRUMENT_KINDS and _at_start(fv, s)), None)
                if hit:
                    add(fv.span(*hit), "type_cue_label", {"cue": f.text[m.start():m.end()].strip(" :"), "layout": "line below"})
                    break
    # line tiers
    gov_first = None
    first_instrument_start = None

    def is_label(k: int) -> bool:
        return 0 <= k < len(p1) and p1[k].text.rstrip().endswith(":")

    for idx, ln in enumerate(p1):
        block = doc.blocks[ln.block_index]
        label = block.label
        if ln.number in in_list or label == "document_index" or "....." in ln.text:
            continue                                  # a check box list or a line of a table of contents
        f = _fold_line(ln)
        head = ln.number in head_numbers
        for s, e, kind in _type_hits(f):
            line_start = _at_start(f, s)
            start = _is_block_start(ln) and line_start
            span = f.span(s, e)
            if kind == "blocked":
                before_b = doc.text[ln.char_start:span[0]]
                title_end = ((ln.index_in_block == 0 or label == "section_header") and not f.text[e:].strip()
                             and re.search(r"[-:]\s*\Z", vb.norm_text(before_b) + " ") is not None
                             and _title_prefix(before_b))
                if head and (start or title_end) and res["blocked"] is None and first_instrument_start is None:
                    res["blocked"] = (span, doc.text[span[0]:span[1]])
            elif kind == "government":
                before = doc.text[ln.char_start:span[0]]
                place = start or (label == "section_header" and line_start)
                citation = f.text[s:e] in ("decret", "dekret") and LAW_CITATION_RX.match(f.text, e)
                if (head and place and gov_first is None and label != "list_item"
                        and not re.search(r"[•·▪■*–-]", before) and not citation):
                    gov_first = span
                    add(span, "type_government_head")
            if kind not in INSTRUMENT_KINDS:
                continue
            if is_label(idx) and is_label(idx - 1) and is_label(idx + 1) and not f.text[e:].strip(" :"):
                continue                              # a label in a stack of labels ("Richtlinienmotion:")
            gov = gov_first is not None and gov_first[0] < span[0]
            late = (start and label in ("section_header", "text") and not f.text[:s].strip() and (
                label == "section_header" or len(ln.text) <= 90))   # no bullet before the word: not a list of affairs
            if kind in INSTRUMENT_KINDS and gov and start and (head or late):
                # a document of the executive (Bericht und Antrag, Botschaft) about an intervention
                add(span, "type_line_start_gov", {"place": "head" if head else "after the head"})
            elif kind == "word":
                if start and (head or late) and not re.search(r"\d", f.text[:s]):
                    if first_instrument_start is None and head:
                        first_instrument_start = span[0]
                    add(span, "type_line_word", {"place": "head" if head else "after the head"})
            elif start and head:
                if first_instrument_start is None:
                    first_instrument_start = span[0]
                add(span, "type_line_start")
            elif late:
                add(span, "type_line_start_late")
            elif head:
                title = (ln.index_in_block == 0 or label == "section_header") and _title_prefix(
                    doc.text[ln.char_start:span[0]])
                add(span, "type_head_inline_gov" if gov else "type_head_inline" if title else "type_head_inline_text")
        if head and gov_first is None:
            m = MM_RX.search(ln.text)
            if m and _is_block_start(ln) and not ln.text[:m.start()].strip():
                gov_first = (ln.char_start + m.start(), ln.char_start + m.end())
                cands.append((TYPE_TIERS.index("type_government_head"), gov_first[0],
                              doc.candidate("affair_type", gov_first[0], gov_first[1], "draft_decree",
                                            "type_government_head", detail={"short_form": "Messaggio municipale"})))
    # block tiers: response phrase (head blocks), submission phrase (first page), government phrase (head blocks)
    seen_blocks = set()
    for ln in p1:
        if ln.block_index in seen_blocks:
            continue
        seen_blocks.add(ln.block_index)
        b = doc.blocks[ln.block_index]
        if any(x.number in in_list for x in b.lines):
            continue
        f = vb.fold_map(b.text, base=b.char_start, dehyphen=True)     # a type word can go over a line end
        hits = [(s, e) for s, e, k in _type_hits(f) if k in INSTRUMENT_KINDS]
        if ln.number in head_numbers or b.label == "section_header":
            tier = "type_response_phrase" if ln.number in head_numbers else "type_response_phrase_late"
            found = False
            for r in RESPONSE_RX.finditer(f.text):
                nxt = next(((s, e) for s, e in hits if 0 <= s - r.end() <= 80), None)
                if nxt and "." not in f.text[r.end():nxt[0]].replace("nr.", ""):
                    add(f.span(*nxt), tier, {"cue": r.group(0)})
                    found = True
                    break
            q = None if found else QUESTION_RESPONSE_RX.search(f.text)
            if q:
                add(f.span(q.start(1), q.end(1)), tier, {"cue": "reponse a la question"})
        if ln.number in head_numbers and b.label != "list_item":
            g = GOV_PHRASE_RX.search(f.text)
            if g:
                add(f.span(g.start(), g.end()), "type_government_phrase")
        for rx in SUBMISSION_RXS:
            m = rx.search(f.text)
            if m:
                gov = gov_first is not None
                add(f.span(m.start("t"), m.end("t")), "type_submission_phrase", {"government_word_in_head": gov})
                break
    cands.sort(key=lambda x: (x[0], x[1]))
    return res


def _dedupe(cands: list[vb.ValueCandidate], limit: int = 5) -> list[vb.ValueCandidate]:
    out, seen = [], set()
    for c in cands:
        key = (c.char_start, c.char_end)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out[:limit]


def _with_others(first: vb.ValueCandidate, rest: list[vb.ValueCandidate]) -> vb.ValueCandidate:
    others = tuple(c for c in _dedupe([first] + rest, 6)[1:])
    return vb.ValueCandidate(first.field, first.value, first.normalised, first.tier, first.page, first.block,
                             first.char_start, first.char_end, first.evidence, others, first.detail)


@vb.register("affair_type")
def read_affair_type(doc: vb.Doc) -> vb.ValueCandidate | vb.NotFound:
    """The affair type from the type word of the head (tiers: module text, chapter 3)."""
    if not doc.lines:
        return doc.not_found("affair_type", "no_text")
    scan = _type_scan(doc)
    cands = [c for _, _, c in scan["cands"]]
    blocked = scan["blocked"]
    if blocked is not None:
        # A word with no list value starts the head. A cue label or a selected check box still wins.
        strong = [c for c in cands if c.tier in ("type_cue_label", "type_checkbox")]
        early = [c for c in cands if c.tier == "type_line_start" and c.char_start < blocked[0][0]]
        if strong or early:
            first = (strong or early)[0]
            return _with_others(first, [c for c in cands if c is not first])
        return doc.not_found("affair_type", "not_in_document_type",
                             f"the head starts with the word {vb.norm_text(blocked[1])!r}; the value list of "
                             "eCH-0295 has no value for it", _dedupe(cands))
    if cands:
        return _with_others(cands[0], cands[1:])
    return doc.not_found("affair_type", "no_pattern", "no type word in the head lines of the first page")


# ------------------------------------------------------------------ affair number

def _strip_council(text: str, start: int, end: int) -> tuple[int, int]:
    """A council short form at the start of a number is a cue, not a part of the number: "GR 110/2016"."""
    m = re.match(r"(?:" + "|".join(COUNCIL_ABBR) + r")[ .-]?(?=\d)", text[start:end])
    return (start + m.end(), end) if m else (start, end)


def _extend_tail(text: str, start: int, end: int) -> int:
    """The form "16.05.3 15-3": 3 parts with points, a space, then a part with a year and a running number."""
    if text[start:end].count(".") >= 2:
        m = re.match(r" \d{2,4}[-/]\d{1,3}(?![\w.])", text[end:])
        if m:
            return end + m.end()
    return end


def _num_after(text: str, pos: int, explicit: bool, plain_max: int = 7) -> tuple[int, int] | str | None:
    """The span of a number that starts at text[pos:] (after white space, a colon or a point), a refusal cause
    (text), or None for no number form."""
    m = re.compile(r"[\s:.]*\(?\s*(" + _NUM + r")" + _END).match(text, pos)
    if not m:
        return None
    s, e = _strip_council(text, m.start(1), m.end(1))
    e = _extend_tail(text, s, e)
    cause = refuse(text, s, e, explicit)
    if cause:
        return cause
    val = text[s:e]
    if val.isdigit() and len(val) > plain_max:
        return "too_long"
    return s, e


def _whole_line_number(ln: vb.Line, explicit: bool) -> tuple[int, int] | None:
    """The span of a number that fills the line (for a value line below a label)."""
    m = re.fullmatch(r"\s*(" + _NUM + r")\s*", ln.text)
    if not m:
        return None
    s, e = _strip_council(ln.text, m.start(1), m.end(1))
    if refuse(ln.text, s, e, explicit):
        return None
    return s, e


def _is_label_row(text: str) -> bool:
    """True for a line that holds only 2 to 6 label words: "Beschlussnummer Geschäftsnummer Ordnungsnummer"."""
    parts = text.split()
    return 2 <= len(parts) <= 6 and all(LABEL_WORD_RX.fullmatch(p) for p in parts)


def _column_value(lines: list[vb.Line], k: int, start: int) -> tuple[vb.Line, int, int, str, list[int]] | None:
    """The value of a label in a row of labels (lines[k], the label starts at `start`).
    Layout "table column": the cells have tabulators, the label fills its cell, the next line has the same
    number of cells (for the first cell, a shorter line is permitted). Layout "label row": the line holds only
    label words, and the next line has the same number of words. Layout "label row, value lines": the line
    holds only n label words, and each of the next n lines holds one word.
    Result: (value line, start, end, layout, line numbers of all value lines)."""
    line = lines[k]
    t = line.text
    nxt = lines[k + 1] if k + 1 < len(lines) and lines[k + 1].page == line.page else None
    if nxt is None:
        return None
    if "\t" in t:
        cells, idx = t.split("\t"), t[:start].count("\t")
        rest = (AFFAIR_CUE_RX.sub("", cells[idx]) if AFFAIR_CUE_RX.search(cells[idx]) else
                INTERVENTION_CUE_RX.sub("", cells[idx]))
        if rest.strip(" :."):
            return None
        vcells = nxt.text.split("\t")
        if not (len(vcells) == len(cells) or (idx == 0 and len(vcells) >= 2)):
            return None
        pos = sum(len(c) + 1 for c in vcells[:idx])
        m = re.fullmatch(r"\s*(" + _NUM + r")\s*", vcells[idx])
        return (nxt, pos + m.start(1), pos + m.end(1), "table column", [nxt.number]) if m else None
    if _is_label_row(t):
        n, idx = len(t.split()), len(t[:start].split())
        words = list(re.finditer(r"\S+", nxt.text))
        if len(words) == n:
            m = re.fullmatch(_NUM, words[idx].group(0))
            return (nxt, words[idx].start(), words[idx].end(), "label row", [nxt.number]) if m else None
        below = lines[k + 1:k + 1 + n]
        if len(below) == n and all(len(x.text.split()) == 1 and x.page == line.page for x in below):
            v = below[idx]
            m = re.fullmatch(r"\s*(" + _NUM + r")\s*", v.text)
            return (v, m.start(1), m.end(1), "label row, value lines", [x.number for x in below]) if m else None
    return None


def _number_scan(doc: vb.Doc) -> dict:
    p1_all = _page1_lines(doc)
    p1 = p1_all[:PAGE1_LINES]
    head = [ln for ln in doc.first_lines(HEAD_LINES) if ln in p1]
    head_numbers = {ln.number for ln in head}
    p1_numbers = {ln.number for ln in p1}

    def label_of(ln: vb.Line) -> str:
        return doc.blocks[ln.block_index].label

    def cue_place(ln: vb.Line, start: int) -> bool:
        """A cue word in a sentence of the body text is a reference to a different affair. The cue must be in
        the head, in a page header or footer, at the start of its line, or in a short line."""
        return (ln.number in head_numbers or label_of(ln) in ("page_header", "page_footer")
                or not ln.text[:start].strip(" (\t") or len(ln.text) <= 60)
    cands: list[tuple[int, int, vb.ValueCandidate]] = []
    refused: list[vb.ValueCandidate] = []
    causes: collections.Counter = collections.Counter()

    def add(ln: vb.Line, s: int, e: int, tier: str, detail: dict | None = None, normalised: str | None = None):
        a, z = ln.char_start + s, ln.char_start + e
        c = doc.candidate("affair_number", a, z, normalised or normal_number(doc.text[a:z]), tier, detail=detail)
        (refused if tier == REFUSED_TIER else cands).append(
            (NUMBER_TIERS.index(tier) if tier != REFUSED_TIER else 99, a, c))

    # lines whose number belongs to a decision word (label line and its value lines)
    labelled: set[int] = set()         # value lines of a row of labels: the labels say what the values are
    negative: set[int] = set()
    below: set[int] = set()            # value lines of a label line with a decision word
    negative_cue: set[int] = set()     # the decision word and its number are on the line: a test for each number
    for i, ln in enumerate(p1):
        m = NEGATIVE_RX.search(ln.text)
        if m:
            negative.add(ln.number)
            if not re.search(r"\d", ln.text[m.end():]):
                below |= {v.number for v in _values_below(p1, i)[:2]}
            else:
                negative_cue.add(ln.number)
    negative |= below
    negative_cue -= below

    def cue_tiers(rx: re.Pattern, tier_line: str, tier_below: str, lines: list[vb.Line]):
        for k, ln in enumerate(lines):
            hits = [(m.start(), m.end(), m.group(0)) for m in rx.finditer(ln.text)]
            prev = lines[k - 1] if k else None
            if not hits and prev is not None and prev.block_index == ln.block_index and prev.text.rstrip().endswith("-"):
                # the cue word goes over a line end: "(Parla-" / "mentsgeschäft 24.01.05)"
                part = prev.text.rstrip()[:-1]
                m = rx.search(part + ln.text)
                if m and m.start() < len(part) < m.end():
                    hits = [(0, m.end() - len(part), m.group(0))]
            for start, end, cue in hits:
                if not cue_place(ln, start):
                    continue
                row = "\t" in ln.text or _is_label_row(ln.text)
                cell = ln.text.rfind("\t", 0, start) + 1     # a decision word in a different cell is a different label
                if not _is_label_row(ln.text) and negative_before(ln.text[cell:], start - cell):
                    causes["decision_number"] += 1
                    continue
                affair = tier_line == "number_cue_affair_line"
                detail = {"cue": vb.norm_text(cue)}
                got = _num_after(ln.text, end, explicit=True)
                if isinstance(got, tuple) and vb.fold(cue).endswith("geschaft"):
                    # the plain word "Geschäft": 1 or 2 digits are a count or a column, not a number
                    val = ln.text[got[0]:got[1]]
                    if val.isdigit() and len(val) < 3:
                        got = "too_short"
                    elif re.match(r"0\d{2} \d{3} \d{2} \d{2}", ln.text[got[0]:]):
                        got = "phone"
                if isinstance(got, tuple):
                    val = ln.text[got[0]:got[1]]
                    # "GR Geschäft Nr. 145/2016": the number of the council, a tier of its own
                    council = affair and re.search(
                        r"(?<![A-Za-z])(?:" + "|".join(COUNCIL_ABBR) + r")[ -]\Z", ln.text[:start])
                    after = ln.text[got[1]:]
                    if re.match(r" \d{2}\.[A-Z]{2,8}\.\d", after):
                        causes["printed_two_times"] += 1      # "2014.RRGR.9 14.RRGR.944": two texts, one on the other
                        continue
                    if affair and re.match(r"\)?[,;]?\s+[a-zäöü]{2,}", after):
                        tier = "number_cue_affair_sentence"   # running text follows: a reference in a sentence
                    elif affair and SHORT_RX.fullmatch(val):
                        tier = "number_cue_affair_short"      # "Geschäft Nr. 5", "Geschäft Nr. 3.3": an item of a session
                    elif affair and val.isdigit() and not council:
                        tier = "number_cue_affair_digits"     # digits only: a running number of a records system
                    else:
                        tier = "number_cue_affair_council" if council else tier_line
                    add(ln, got[0], got[1], tier, detail)
                elif isinstance(got, str):
                    causes[got] += 1
                elif row:
                    # a row of labels: the value is in the same column of the next line
                    col = _column_value(lines, k, start)
                    if col:
                        nxt, c0, c1, layout = col[:4]
                        labelled.update(col[4])
                        val = nxt.text[c0:c1]
                        cause = refuse(nxt.text, c0, c1, explicit=True)
                        if cause:
                            causes[cause] += 1
                        elif SHORT_RX.fullmatch(val):
                            add(nxt, c0, c1, "number_cue_affair_short" if affair else tier_below,
                                {**detail, "layout": layout})
                        else:
                            add(nxt, c0, c1, "number_cue_affair_table" if affair else tier_below,
                                {**detail, "layout": layout})
                elif not ln.text[end:].strip(" :.\t") and ln in p1:
                    for v in _values_below(p1, p1.index(ln)):
                        span = _whole_line_number(v, explicit=True)
                        if span and v.number not in negative:
                            val = v.text[span[0]:span[1]]
                            if (val.isdigit() and len(val) < 3) or re.fullmatch(r"\d{1,2}\.(?:19|20)\d{2}", val):
                                causes["too_short" if val.isdigit() else "date"] += 1
                                continue
                            add(v, span[0], span[1], "number_cue_affair_digits" if affair and val.isdigit()
                                else tier_below, {**detail, "layout": "line below"})
                            break

    cue_tiers(AFFAIR_CUE_RX, "number_cue_affair_line", "number_cue_affair_below", p1_all)
    cue_tiers(INTERVENTION_CUE_RX, "number_cue_intervention_line", "number_cue_intervention_below", p1)
    # council short form and "Nr." (the whole first page: a stamp or a footer can hold it)
    for ln in p1_all:
        for m in COUNCIL_CUE_RX.finditer(ln.text):
            if not cue_place(ln, m.start()):
                continue
            sp = SPACED_NUM_RX.match(ln.text, m.end())
            if sp:
                add(ln, sp.start(1), sp.end(1), "number_cue_council", {"cue": m.group(0), "form": "period letters running"})
                continue
            got = _num_after(ln.text, m.end(), explicit=True)
            if isinstance(got, tuple):
                add(ln, got[0], got[1], "number_cue_council", {"cue": m.group(0)})
            elif isinstance(got, str):
                causes[got] += 1
    # the form year.LETTERS.number on the first page; in a page header or footer of the second page
    first_page = p1_all[0].page if p1_all else None
    for ln in doc.lines:
        if ln.page == first_page:
            tier = "number_form_year_letters"
        elif ln.page == first_page + 1 and label_of(ln) in ("page_header", "page_footer"):
            tier = "number_form_year_letters_p2"
        else:
            if ln.page > first_page + 1:
                break
            continue
        for m in YEAR_LETTERS_RX.finditer(ln.text):
            if re.search(r"(?i)signatur\s*[·:.•-]?\s*\Z", ln.text[:m.start()]):
                continue                              # the signature of a records system is not the affair number
            if not negative_before(ln.text, m.start()):
                add(ln, m.start(), m.end(), tier)
    # a number with a document part ("19.5497.01", "Nr. 22-26.633.02"): the value is the part before the
    # document part. Places: after "Nr." (also "Reg. Nr."), a head line, the last 3 lines, a short line of page 1.
    tail = [x for x in doc.lines[-3:] if x.page != first_page]
    last3 = {x.number for x in doc.lines[-3:]} | {x.number for x in p1_all[-3:]}
    docpart_lines: set[int] = set()
    for ln in list(p1_all) + tail:
        for m in DOCPART_RX.finditer(ln.text):
            before, after = ln.text[:m.start()], ln.text[m.end():]
            if refuse(ln.text, m.start(), m.end(), explicit=True) not in (None, "decision_number"):
                continue                              # the form is the evidence: "Reg. Nr. 22-26.592.01" is read
            alone = not before.strip() and not after.strip()
            at_start = not before.strip() and re.match(r"\s*[,;/]|\s+[^\W\d_]", after) is not None
            at_end = not after.strip() and before[-1:] in (" ", "\t")
            short = len(ln.text) <= 60
            cue = re.search(NR_CUE + r"\s*:?\s*\Z", before)
            if cue and not after.strip(" ,;") and (short or ln.number in head_numbers):
                tier = "number_docpart_cue"
            elif ln.number in head_numbers and (alone or at_start or at_end):
                tier = "number_docpart_head"
            elif alone and ln.number in last3:
                tier = "number_docpart_last_line"
            elif ln.page == first_page and short and (alone or at_start or at_end):
                tier = "number_docpart_page1"
            else:
                continue
            docpart_lines.add(ln.number)
            add(ln, m.start(1), m.end(1), tier, {"document_part": m.group(2), "printed": vb.norm_text(m.group(0))})
            break
    # one capital letter and 6 digits: after the label "Präsidial-Nr.", alone on a line, or at the end of a head line
    for i, ln in enumerate(p1_all):
        for m in LETTER_CODE_RX.finditer(ln.text):
            before, after = ln.text[:m.start()], ln.text[m.end():]
            if after.strip() or negative_before(ln.text, m.start()):
                continue
            label_above = i > 0 and LETTER_CODE_CUE_RX.search(p1_all[i - 1].text) is not None and not before.strip()
            if LETTER_CODE_CUE_RX.search(before) or label_above:
                add(ln, m.start(1), m.end(1), "number_letter_code_cue", {"cue": "Präsidial-Nr."})
            elif not before.strip():
                add(ln, m.start(1), m.end(1), "number_letter_code_line", {"place": "alone on a line"})
            elif ln.number in head_numbers and before[-1:] in (" ", "\t"):
                add(ln, m.start(1), m.end(1), "number_letter_code_line", {"place": "end of a head line"})
    # the running number of a records system in a page header or footer (each page; the first one)
    for ln in doc.lines:
        if label_of(ln) in ("page_header", "page_footer"):
            m = RUNNING_CUE_RX.search(ln.text)
            if m:
                add(ln, m.start(1), m.end(1), "number_cue_running_footer", {"cue": "Laufnummer"})
                break
    # the form 2 digits, point, 6 digits on the first page (weak: the number of the executive for the affair)
    for ln in p1_all:
        m = YEAR_SERIAL6_RX.search(ln.text)
        if m and (ln.number in head_numbers or label_of(ln) in ("page_header", "page_footer") or len(ln.text) <= 60) \
                and not AFFAIR_CUE_RX.search(ln.text[:m.start()]):
            add(ln, m.start(1), m.end(1), "number_form_year_serial6")
    # a label line with only "Numero" / "Nummer": the number below it (weak: often the number of a decision)
    # It is a result only if the line before is a document word of the executive ("Messaggio" / "numero" /
    # "8608"). In each other place it is the number of a decision of the executive: list `others` only.
    for i, ln in enumerate(p1):
        if BARE_LABEL_RX.fullmatch(ln.text) and ln.number not in negative:
            fp = _fold_line(p1[i - 1]) if i else None
            gov = fp is not None and any(k == "government" and _at_start(fp, s) and not fp.text[e:].strip()
                                         for s, e, k in _type_hits(fp))
            for v in _values_below(p1, i):
                span = _whole_line_number(v, explicit=True)
                if span and v.number not in negative and not (v.text[span[0]:span[1]].isdigit() and span[1] - span[0] < 3):
                    add(v, span[0], span[1], "number_cue_bare_label" if gov else REFUSED_TIER,
                        {"cue": vb.norm_text(ln.text)} if gov else {"cause": "a label with only the word Numero or Nummer"})
                    break
    # the file cue of a distribution list (each page)
    for ln in doc.lines:
        m = FILE_CUE_RX.search(ln.text)
        if m:
            add(ln, m.start(1), m.end(1), "number_cue_file", {"cue": "zu den Akten"})
            break
    # tiers with a type word. Title lines: the head lines and the section headers of the first page. A line at
    # the start of a block of the first 40 lines is read only if the type word starts the line.
    type_scan = _type_scan(doc)
    type_wordings = [c.value for _, _, c in type_scan["cands"]]
    for ln in p1_all:
        title_line = ln.number in head_numbers or label_of(ln) == "section_header"
        block_start = ln.number in p1_numbers and _is_block_start(ln)
        if not (title_line or block_start) or (ln.number in negative and ln.number not in negative_cue):
            continue
        per_number = ln.number in negative_cue       # "Beschluss Nr. 121-2021 Interpellation 8145": test each number
        f = _fold_line(ln)
        hits = _type_hits(f)
        # "Nr. 025/2025 Postulat ...": the number, then the type word
        m = NR_TYPE_RX.match(ln.text)
        if m and hits and not ln.text[m.start(1):m.end(1)].isdigit():
            a0 = f.span(hits[0][0], hits[0][1])[0] - ln.char_start
            s0, e0 = _strip_council(ln.text, m.start(1), m.end(1))
            if 0 <= a0 - m.end(1) <= 2 and hits[0][2] != "government" and not refuse(ln.text, s0, e0) \
                    and not per_number:
                add(ln, s0, e0, "number_nr_type", {"type_word": ln.text[a0:a0 + hits[0][1] - hits[0][0]]})
                continue
        for s, e, kind in hits:
            a, z = f.span(s, e)
            pos = z - ln.char_start
            before = doc.text[ln.char_start:a]
            # strong: the type word starts the line (after marks, an article, a response word or a title prefix)
            strong = (_at_start(f, s) or STRONG_PREFIX_RX.match(f.text[:s]) is not None or _title_prefix(before))
            if not strong and not title_line:
                continue
            kind_of_line = "" if strong and title_line else "_late" if strong else "_inline"
            if kind == "blocked" and re.match(r"risoluz|resolu", f.text[s:e]):
                continue                              # the resolution of an executive is not the affair
            word = {"type_word": doc.text[a:z]}
            rest = ln.text[pos:]
            got = _num_after(ln.text, pos, explicit=False, plain_max=5) if re.match(r"\s+\S", rest) and not re.match(
                r"\s+" + NR_CUE, rest) else None
            if isinstance(got, tuple) and per_number and negative_before(ln.text, got[0]):
                got = "decision_number"
            if isinstance(got, tuple) and kind != "government":
                val = ln.text[got[0]:got[1]]
                if (val.isdigit() and len(val) < 3) or COUNT_AFTER_RX.match(ln.text, got[1]):
                    causes["count"] += 1
                elif val.isdigit():
                    add(ln, got[0], got[1], "number_type_adjacent_digits", {**word, "line": kind_of_line.strip("_") or "title"})
                elif re.fullmatch(r"[A-Z]{1,2} ?\d{3,5}", val) and re.match(r"\s*\(\s*\Z", ln.text[pos:got[0]]) and \
                        ln.text[got[1]:got[1] + 1] == ")":
                    add(ln, got[0], got[1], "number_paren_code", word)
                else:
                    add(ln, got[0], got[1], "number_type_adjacent" + kind_of_line, word)
                continue
            if isinstance(got, str):
                causes[got] += 1
            m = re.compile(r"([^\d]{0,25}?)" + NR_CUE + r"\s*:?\s*(?=\(?[A-Z]{0,4}[ .-]?\d)").match(ln.text, pos)
            if m and not NEGATIVE_RX.search(m.group(1)) and "." not in m.group(1).strip().rstrip("("):
                got = _num_after(ln.text, m.end(), explicit=False, plain_max=4)
                if got == "year" and re.match(r"\s*\d{4}(?!\s?[./-]\s?\d)", ln.text[m.end():]):
                    got = _num_after(ln.text, m.end(), explicit=True, plain_max=4)   # "Interpellanza n. 2043 del"
                if isinstance(got, tuple) and per_number and negative_before(ln.text, got[0]):
                    got = "decision_number"
                if isinstance(got, tuple) and ln.text[got[0]:got[1]].isdigit():
                    # "Interpellation Nr. 121": the sequence number of the type or of the session
                    add(ln, got[0], got[1], "number_type_cue_seq", {**word, "line": kind_of_line.strip("_") or "title"})
                elif isinstance(got, tuple):
                    add(ln, got[0], got[1], "number_type_cue" + kind_of_line, word)
                elif isinstance(got, str):
                    causes[got] += 1
    # a number in brackets after a type word, in a block of the head
    seen: set[int] = set()
    for ln in head:
        if ln.block_index in seen:
            continue
        seen.add(ln.block_index)
        block = doc.blocks[ln.block_index]
        typed = False
        for bl in block.lines:
            fb = _fold_line(bl)
            ends = [fb.span(s, e)[1] - bl.char_start for s, e, k in _type_hits(fb) if k in INSTRUMENT_KINDS]
            for m in PAREN_NUM_RX.finditer(bl.text):
                if not (typed or any(x <= m.start() for x in ends)) or bl.number in negative:
                    continue
                s0, e0 = m.start("n"), m.end("n")
                val = bl.text[s0:e0]
                if not re.search(r"\d\s?[./-]\s?\d", val) or negative_before(bl.text, m.start()):
                    continue                          # digits only: a count, a year, a page
                if re.match(r"[A-Z]", val) and not _letters_of_type(val, type_wordings):
                    causes["law_number"] += 1         # "(RB 10.4111)": the letters are not those of the type word
                    continue
                cause = refuse(bl.text, s0, e0, explicit=m.group("nr") is not None)
                if cause:
                    causes[cause] += 1
                else:
                    add(bl, s0, e0, "number_type_paren")
            typed = typed or bool(ends)
    # a code in brackets at the end of a title line or of a table row with the cue "Geschäft": "(P2311)"
    for ln in head:
        m = PAREN_CODE_RX.search(ln.text)
        if m and ln.number not in negative and (re.match(r"\s*Gesch(?:ä|ae)ft\b", ln.text) or any(
                k in INSTRUMENT_KINDS for _, _, k in _type_hits(_fold_line(ln)))):
            add(ln, m.start(1), m.end(1), "number_paren_code")

    def type_only(k: int) -> bool:
        if not 0 <= k < len(p1):
            return False
        fk = _fold_line(p1[k])
        return any(kind in INSTRUMENT_KINDS and _at_start(fk, s) and len(fk.text[e:].strip(" :")) <= 1
                   for s, e, kind in _type_hits(fk))

    for i, ln in enumerate(p1):
        if ln.number in negative or ln.number in docpart_lines or ln.number in labelled:
            continue
        t = ln.text
        # 3 groups with points, alone on a line. If the text has the form of a date, a line with only a type
        # word must be the line before or the line after.
        m = DOTTED3_RX.match(t)
        if m and not PHONE_RX.match(m.group(1)):
            date_form = any(h.start < m.end(1) and h.end > m.start(1) for h in vb.find_dates(t))
            if not date_form:
                add(ln, m.start(1), m.end(1), "number_line_dotted3")
                continue
            if type_only(i - 1) or type_only(i + 1):
                add(ln, m.start(1), m.end(1), "number_line_dotted3_type")
                continue
        if i >= DOTTED_LINES:
            continue
        m = HEAD_DATE_NUM_RX.search(t)
        if m and any(h.end <= m.start(1) for h in vb.find_dates(t)) and ln.number in head_numbers:
            add(ln, m.start(1), m.end(1), "number_after_head_date")
            continue
        if ln.number not in head_numbers:
            # after the head only the form 22.406 at the start of a block is read (a letterhead fills the head)
            m = DOTTED_RX.match(t)
            if m and _is_block_start(ln) and not refuse(t, m.start(1), m.end(1)) and not _month_year(m.group(1)):
                add(ln, m.start(1), m.end(1), "number_line_dotted", {"place": "after the head"})
            continue
        # short form, "Nr.", number: "MM N. 91/2019" (the short form is a part of the number, the cue is not)
        m = PREFIX_NR_RX.match(t)
        if m and m.group(2) not in COUNCIL_ABBR and not refuse(t, m.start(1), m.end(1)):
            add(ln, m.start(1), m.end(1), "number_line_form", {"form": "letters_nr_running_year"},
                normalised=m.group(2) + " " + normal_number(m.group(3)))
            continue
        m = BARE_NR_RX.match(t)
        if m:
            s, e = _strip_council(t, m.start(1), m.end(1))
            cause = refuse(t, s, e)
            if cause:
                causes[cause] += 1
            elif t[s:e].isdigit():
                add(ln, s, e, REFUSED_TIER, {"cause": "a line with only Nr. and digits"})
            else:
                add(ln, s, e, "number_bare_nr")
            continue
        m = DOTTED_RX.match(t)
        if m and not refuse(t, m.start(1), m.end(1)) and not _month_year(m.group(1)) and (
                ln.number in head_numbers or _is_block_start(ln)):
            add(ln, m.start(1), m.end(1), "number_line_dotted")
            continue
        done = False
        for name, rx in LINE_FORMS:
            m = rx.match(t)
            if not m:
                continue
            done = True
            a0, z0 = _strip_council(t, m.start(1), m.end(1))
            if refuse(t, a0, z0):
                break
            if a0 != m.start(1):
                add(ln, a0, z0, "number_line_form", {"form": name, "council_short_form": t[m.start(1):a0].strip()})
                break
            if name == "letters_running" and not _letters_of_type(m.group(1), type_wordings):
                break
            add(ln, m.start(1), m.end(1), "number_line_year_running" if name in ("year_running", "running_year")
                else "number_line_form", {"form": name})
            break
        if done:
            continue
        # a registry code at the end of a head line (weak: in some registers it is the plan position)
        m = REGISTRY_RX.search(t)
        if m and not refuse(t, m.start(1), m.end(1)) and not re.search(r"(?i)\b(?:art|ziff|abs|kap|§)\.?\s*\Z", t[:m.start(1)]):
            add(ln, m.start(1), m.end(1), "number_line_registry_code")
    # late lines of the first page (a stamp): "Nr. 188/2023"; "Nr." and the number on the next line; "M 126/2010"
    for i, ln in enumerate(p1_all):
        if ln.number in head_numbers or ln.number in negative or ln.number in docpart_lines:
            continue
        t = ln.text
        m = BARE_NR_RX.match(t)
        if m:
            s, e = _strip_council(t, m.start(1), m.end(1))
            if not t[s:e].isdigit() and not refuse(t, s, e):
                add(ln, s, e, "number_bare_nr_late")
            continue
        if re.fullmatch(r"\s*" + NR_CUE + r"\s*:?\s*", t) and i + 1 < len(p1_all):
            v = p1_all[i + 1]
            span = _whole_line_number(v, explicit=True)
            if span and not v.text[span[0]:span[1]].isdigit() and v.number not in negative:
                add(v, span[0], span[1], "number_bare_nr_late", {"layout": "line below"})
            continue
        m = LATE_FORM_RX.match(t)
        if m and _letters_of_type(m.group(1), type_wordings) and not refuse(t, m.start(1), m.end(1)):
            add(ln, m.start(1), m.end(1), "number_line_form_late")
    cands.sort(key=lambda x: (x[0], x[1]))
    return {"cands": [c for _, _, c in cands], "refused": [c for _, _, c in refused], "causes": dict(causes)}


def _month_year(value: str) -> bool:
    """True for a month and a year with a point: "09.2023" (not an affair number)."""
    return re.fullmatch(r"(?:0[1-9]|1[0-2])\.(?:19|20)\d{2}", value) is not None


def _letters_of_type(value: str, type_wordings: list[str]) -> bool:
    """True if the capital letters at the start of `value` are the initial letters of a type word that the
    document prints ("M 189" with "Motion", "KA 12" with "Kleine Anfrage")."""
    letters = re.match(r"[A-Z]+", value).group(0)
    initials = {vb.fold(w)[:1].upper() for w in type_wordings} | {
        "".join(p[:1] for p in vb.fold(w).split()).upper() for w in type_wordings}
    return letters[:1] in {i[:1] for i in initials if i} or letters in initials


@vb.register("affair_number")
def read_affair_number(doc: vb.Doc) -> vb.ValueCandidate | vb.NotFound:
    """The affair number that the first page prints (tiers: module text, chapter 4)."""
    if not doc.lines:
        return doc.not_found("affair_number", "no_text")
    scan = _number_scan(doc)
    cands = scan["cands"]
    if cands:
        return _with_others(cands[0], cands[1:])
    if scan["refused"]:
        return doc.not_found("affair_number", "no_cue", "a head line holds only Nr. and digits; no affair cue word",
                             _dedupe(scan["refused"]))
    detail = "no number form after a cue word or in a head line"
    if scan["causes"]:
        detail += "; refused forms: " + ", ".join(f"{k} {v}" for k, v in sorted(scan["causes"].items()))
    return doc.not_found("affair_number", "no_pattern", detail)


# ------------------------------------------------------------------ commands

def coverage(skip: tuple[str, ...] = ()) -> dict:
    """COUNTS ONLY: for each field the number of open documents by tier and by reason of "not found". No export
    value is read and no agreement value is calculated. `skip`: parliament keys that are not read."""
    f = vb.folds()
    ids = [d for d in vb.dev_ids("open") if f["documents"][d]["parliament"] not in skip]
    guard = vb.guard_check(ids)
    out: dict = {"version": VERSION, "documents": len(ids), "skipped_parliaments": sorted(skip),
                 "parliaments": len({f["documents"][d]["parliament"] for d in ids}),
                 "guard": {"dev": guard["by_split"].get("dev"), "refused": guard["refused"]},
                 "what": "coverage by tier; counts only; not an agreement value"}
    for field, fn in (("affair_type", read_affair_type), ("affair_number", read_affair_number)):
        tiers: collections.Counter = collections.Counter()
        reasons: collections.Counter = collections.Counter()
        by_lang: dict = collections.defaultdict(collections.Counter)
        values: collections.Counter = collections.Counter()
        parl_with_value: set = set()
        for d in ids:
            doc = vb.load_doc(d)
            res = vb.read_field(doc, field, registry={field: fn})
            lang = doc.language or "none"
            if res.found:
                tiers[res.tier] += 1
                by_lang[lang]["value"] += 1
                parl_with_value.add(doc.parliament)
                if field == "affair_type":
                    values[res.normalised] += 1
            else:
                reasons[res.reason] += 1
                by_lang[lang]["not_found"] += 1
        order = TYPE_TIERS if field == "affair_type" else NUMBER_TIERS
        out[field] = {"with_value": sum(tiers.values()), "not_found": sum(reasons.values()),
                      "by_tier": {t: tiers.get(t, 0) for t in order}, "not_found_by_reason": dict(reasons),
                      "by_language": {k: dict(v) for k, v in sorted(by_lang.items())},
                      "parliaments_with_1_or_more_values": len(parl_with_value)}
        if field == "affair_type":
            out[field]["by_list_value"] = dict(values.most_common())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="value rules for the affair type and the affair number (task <id>)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("doc_id")
    c = sub.add_parser("coverage")
    c.add_argument("--out")
    c.add_argument("--skip", default="", help="parliament keys that are not read, with commas")
    a = ap.parse_args()
    if a.cmd == "read":
        doc = vb.load_doc(a.doc_id)
        for fn in (read_affair_type, read_affair_number):
            print(json.dumps(fn(doc).to_json(), ensure_ascii=False, indent=1))
        return 0
    res = coverage(tuple(k for k in a.skip.split(",") if k))
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

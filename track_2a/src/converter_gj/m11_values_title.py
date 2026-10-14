# SPDX-License-Identifier: Apache-2.0
"""Plan `crisp-dm/04-modeling/plan-ech-from-pdf.md`, task <id>: the rule that reads the title of the affair
(`Affair.title` of eCH-0295) from the PDF.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5) for the AI
agent. Status: EXCEPTION, NOT RELEASED. No human checked this file. Interface: `src/m11_values_base.py` (not changed).

1 Inputs (hard rule 5 of the wave)
  The rule reads one `Doc`: the Docling blocks and lines of the block file. It reads no export record, no B1-S
  decision and no state file. It uses the Docling label of a block (section_header, title, text, table, ...) as an
  input. It does not use the rule-chain role `title`: the rule chain gives this role to no block (interface file,
  limit 1). It does not use the S1 role. Thus the rule works with no rule file.
  No rule has a condition on a parliament name or a parliament id. The conditions are layout forms and cue words in
  German, French and Italian.

2 Search area
  The lines of the first page that has text, at most 60 lines, in reading order. Blocks with the Docling label
  page_footer, footnote, picture or document_index are not read. The lines are examined in reading order with the
  line tiers (table 3.1). The first line that gives a title decides. If no line gives a title, the head tiers
  (table 3.2) are tried in their order. If no tier gives a title, the result is "not found in the PDF".

3 Tiers (the name is stable; the calibration gives one probability to each name; each tier has one kind of evidence)
  3.1 Line tiers
  | Tier name              | One sentence                                                                        |
  |------------------------|-------------------------------------------------------------------------------------|
  | label_cue              | The text after a title label of a form, on the same line, in the next table cell or on the next value line. Label words: German Titel, Titel des Vorstosses, Titel des Geschäfts, Titel der Vorlage, Geschäftstitel, Vorstosstitel, Betreff, Betrifft, Gegenstand, Thema; French Titre, Titre de l'objet, Titre de l'intervention, Objet, Objet de l'intervention, Sujet, Sujet/Titre, Intitulé, Concerne; Italian Titolo, Titolo dell'atto, Oggetto, Tema, Argomento. A title after a label on the same line can end with a full stop. |
  | label_no_colon         | A title label with no colon at the start of a line of a form ("Titre Pour une ..."): 3 or more label lines with a colon stand in the head and a label line or a heading comes directly after the block. |
  | label_stack_last       | A title label that is the last label of a stack of 3 or more label lines: the last value block below the stack. |
  | label_stack_order      | A title label in a stack of 3 or more label lines of which one or more have no colon (Datum / Archiv / Thema / Beschluss-Nr.): the value block that has the place of the label in the stack. |
  | label_affair_cell      | The value cell of a table row with a label that names the affair (Geschäft, Vorlage, Vorstoss, Traktandum, Affaire, Intervention, Atto, Trattanda); a part " - <type word> ..." after the title is cut. |
  | cue_line               | The text after a cue word (betreffend, betr., concernant, intitulé, riguardante) at the start of a line, with no type word before it. |
  | cue_in_line            | The text after "betreffend" or "betr." in the first line of a short block of the first 15 lines (3 lines; 5 lines if the line starts with a document kind or a decision kind), with no type word in the line. |
  | act_title_line         | The same line form, but the word directly before the cue word is the kind of an act (Gesetz, Verordnung, Dekret, Reglement, Loi, Ordonnance, Décret, Règlement, Legge, Regolamento): the full block is the title ("Gesetz betreffend die Änderung des Gesetzes über ..."). |
  | number_line_title      | A block of the first 25 lines that starts with an affair number of the form 21.067 or 21.4209 and then prints the title. |
  | type_semicolon         | A head block with fields divided by semicolons, with a type word in one of the first 3 fields: the field directly before the first status or year field. |
  | type_semicolon_author  | A head line with fields divided by semicolons: a field that ends with a type word (a date and a decision number can stand before it, an affair number after it), then the author field (name and party mark), then the title field ("4. Juni 2019 · Beschluss Nr. 22-2019 Postulat; <author>, SP; <title>"). The form type_semicolon is tried first. |
  | type_list_item         | The first list item of the head, in the first 12 lines, that starts with a type word (an item of an agenda): only a title in quotation marks, after a cue word or after a colon. |
  | minute_number_title    | Below the head line of a minute extract, a block that starts with the decision number (3 or 4 digits) and then prints the title. |
  | after_decision_date_text | The text block (at most 4 lines) after a block of the first 15 lines that holds only the kind and the date of a decision (Regierungsratsbeschluss vom ..., Antrag des Stadtrates / vom ..., Weisung vom ...:, Arrêté du Conseil d'Etat du ..., Risoluzione ... del ...). A number line below the title is not a part of it. A block that starts with a type word is left to the type tiers. |
  | after_decision_number_text | The same, after a line that holds only the label and the number of a decision ("SRB Nr. 2022-506", "04. März 2025 · Beschluss 81-2025"); page lines, registry lines and short form lines between them are ignored. |
  | after_number_label_text | The same, after a line that holds only a number label and an affair number with a divider ("Nr. 18-22.034.01", "MM 61/2015"). |
  | after_kind_cue         | After a line that holds only a document kind: a block that starts with a cue word (betreffend, concernant, relatif à, in merito a ...), at most 6 lines; or a kind line with a cue word (zum, zur, über, sur, sul) that goes on in its heading block: the text after the cue word. |
  | type_quoted            | The text in quotation marks in a block that starts with a type word (Motion, Postulat, Interpellation, Anfrage, question, mozione, interrogazione, ...); only an author or a cue word can stand before the quotation mark. |
  | type_cue               | The text after a cue word (betreffend, betr., bezüglich, zur, concernant, relative à, in merito a, ...; or author, place and "zu" or "für") in a block that starts with a type word, or on the lines after a type word. |
  | type_colon             | The text after a colon or a dash in a block that starts with a type word; a number, an author or an addressee can be between the type word and the colon. |
  | type_plain             | The text directly after a type word (and after a number, a list of party marks or an author with a party in brackets) with no cue word, no colon and no quotation marks. |
  | type_plain_short       | A weak candidate: one word, or 2 or 3 name-like words, directly after a type word, if the lines after it give no title. |
  | before_type_line       | The lines of a block before a line "type word + name" (head block of a minute: title / "Postulat <name>" / status). |
  | type_presented         | Italian form below a line with only a type word: "presentata nella forma generica|elaborata da <author> ...": the text in quotation marks at the block end, or the text after the first "per" or "a favore" that is no group name. |
  | after_type_heading     | The first heading block (Docling label section_header or title) after a line that holds only a type word (also "TESTO DELL'INTERROGAZIONE", "Postulat gemäss § 44 ..."); date, number, author, addressee, check box and bracket lines between them are ignored. |
  | after_type_text        | The same as after_type_heading, but the block has the Docling label text (not a list item). |
  | after_kind_heading     | The first heading block after a line that holds only a document kind and an addressee (Bericht und Antrag an ..., Botschaft, Rapport, Messaggio, Réponse, Risposta). |
  | after_kind_text        | The same, but the block has the Docling label text, has at most 3 lines, and a salutation or a structure heading comes directly after it. |
  3.2 Head tiers (in this order)
  | sentence_titled_quote  | The text in quotation marks after a title phrase (mit dem Titel, intitulé, dal titolo) in a sentence of the head that also holds a type word. |
  | sentence_type_quote    | The text in quotation marks at most 80 characters after a type word in a sentence of the first 30 lines, with no title phrase. |
  | heading_after_form     | The first heading block after a form head: each label line has its value line (3 or more labels), or 3 or more label lines stand in the 12 lines before the heading. |
  | text_after_form        | The first text block (at most 4 lines) after a form head in which each of 3 or more label lines has its value line. |
  | sentence_cue           | A weak candidate: the text after a type word or a document kind and a cue word in a sentence of the first 30 lines, to the end of the sentence. |
  | heading_before_response| A heading block of the first 15 lines directly before a line "Risposta|Réponse|Antwort|Beantwortung ... <type word>". |
  | heading_before_salutation | A heading block of the first 15 lines directly before the salutation (the subject line of a letter). |
  | heading_type_in_head   | A weak candidate: the first heading block of the first 15 lines, if a type word stands in the head before it. |
  | weak_first_heading     | A weak candidate: the first heading block of the first 15 lines that is no letterhead, no body name, no addressee, no document kind and no structure heading; no type word stands before it. |
  Optional extra tier (not registered, measured apart, needs `load_doc(doc_id, apertus_roles=True)`):
  | apertus_title_block    | The first block with the Apertus block role title on the first page, if no tier but a weak heading tier gives a title. |

4 What a title is
  The value is the wording of the title in the document: `Doc.text[char_start:char_end]`. The span starts at the first
  title word and ends at the last title word. The type word, the number, the author, the date and a status word
  (Beantwortung, Gutheissung, Ablehnung, Prise de connaissance ...) on the same line are outside the span. A title
  that continues on the next line or in the next block is one span (the span then holds line feeds). Quotation marks
  around the full title are outside the span. The key `normalised` is the value on one line: a hyphen at a line end
  is joined, each run of white space is one space (`norm_title`).
  The rule prefers "not found in the PDF" to a weak candidate. Weak candidates have their own tiers.
  A line that holds only a type word or a document kind counts only in the first 30 lines.
  The rule gives what the document prints. An export title can be an edited form; the rule is not tuned to it.

  Layout rules of version 3 that are no tier of their own: a table block in which fewer than 1 of 3 lines has a cell
  limit is read as text lines; a table row with 2 cells "type line | affair number" in the first 8 lines is read as a
  type line; a table of the signers, a stamp line ("EINGANG GR") and a code line after a type line are ignored.

4a Changes of version 2 (improvement round on the open part, 13.10.2026; the open values are optimistic)
  New tiers: label_stack_last, number_line_title, type_semicolon, minute_number_title, type_plain_short,
  before_type_line, type_presented, text_after_form, heading_before_response, heading_before_salutation,
  heading_type_in_head. The tier weak_first_heading is now only the rest (15 lines, no body names, no addressees).
  Guards: a cue word at the start needs a word limit ("über" in "übernommen", "zu" in "Zukunft"); a party mark that
  is also a common word counts only in its printed form; no type line in the second half of a hyphenated word or in
  the middle of a paragraph; a word in quotation marks at the end of a title is not the title; a status word after a
  colon is no title; a family name or a list of names after a type word is no title; a list item is no title.

4b Changes of version 3 (round 3, 13.10.2026, after the one opening of the closed parliaments)
  From the opening on, the rules learn from all 1,793 development documents (36 parliaments that were open and 8
  that were closed). Thus each value of this version is a value "after the opening": the values of the closed part
  are not blind values any more. No rule has a condition on a parliament or on one document.
  New tiers (each has one kind of evidence): label_no_colon, label_stack_order, label_affair_cell, cue_in_line and
  act_title_line (split from cue_line), type_semicolon_author (beside type_semicolon), type_list_item,
  after_decision_date_text, after_decision_number_text, after_number_label_text, after_kind_cue (split from type_cue
  and after_kind_heading).
  Wrong values of strong tiers that are removed: a label with no colon is no value of a title label ("Beschluss-Nr."
  after "Thema"); a line "An seiner Sitzung ..." is no addressee line; a kind line that goes on in its block is no
  line "only a document kind" ("... zum Jahresbericht 2024 des" / "Gemeinderats"); a block that continues a
  hyphenated line is no title ("tember 2011"); a title label later in the head is preferred to a text block after a
  type word (form with "Name / Vorname" before "Titel"); the colon after the author comes before a cue word in the
  title; a date after the author is a part of the author ("(Urs Frieden, GB) vom 3. Juli 2008:"); in a block that
  holds the title and the body text the title ends at the first short line; status words Begründung,
  Begründungsbericht, Mitbericht, Antwort, "Bericht der" and a structure heading as the last line are cut.
  Weak tiers: a letterhead word with no space, a kind word and a body, a body that decides, and a body with a type
  word are no weak heading; a body name of 2 heading lines is no weak heading.
  Response documents: the head of a response often prints the type, the author and the date of the proposal before
  the title ("Interpellation Muster vom 3. Mai 2021: <title>; Antwort", "Postulat de Mme X et Mme Y du 30.03.2023 :
  <title>", "Stellungnahme des Gemeinderats zur Motion <author> und Kons. betreffend <title>"). The title rule reads
  the title after them; the author and the date are values of other fields.

5 Helpers of this file that the interface does not have
  norm_title (norm_text plus two line-end cases: a soft hyphen at a line end, and a hyphen before und, oder, et, e),
  the type-word patterns, the line classes (date line, number line, author line, label line, salutation, letterhead)
  and a region class with a folded text and a map back to the positions of the document text.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_title.py show DOC_ID
  uv run --offline --frozen --no-sync python src/m11_values_title.py coverage [--out FILE] [--apertus]
  uv run --offline --frozen --no-sync python src/m11_values_title_test.py
The command coverage only COUNTS documents by tier (open part). It reads no export value and calculates no agreement.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_values_base as vb  # noqa: E402

VERSION = "m11-values-title-3"
FIELD = "title"
TIERS = ("label_cue", "label_no_colon", "label_stack_last", "label_stack_order", "label_affair_cell", "cue_line", "cue_in_line", "act_title_line", "type_quoted", "type_cue", "type_colon", "type_plain", "type_plain_short",
         "before_type_line", "type_presented", "type_semicolon", "type_semicolon_author", "type_list_item", "number_line_title", "minute_number_title",
         "after_decision_date_text", "after_decision_number_text", "after_number_label_text", "after_kind_cue", "after_type_heading",
         "after_type_text", "after_kind_heading", "after_kind_text", "sentence_titled_quote", "sentence_type_quote", "heading_after_form", "text_after_form", "sentence_cue",
         "heading_before_response", "heading_before_salutation", "heading_type_in_head", "weak_first_heading")
APERTUS_TIER = "apertus_title_block"
HEAD_LINES = 60
WEAK_LINES = 15
MAX_TITLE = 400
HEADING_LABELS = ("section_header", "title")
SKIP_LABELS = ("page_footer", "footnote", "picture", "document_index")
NO_TYPE_LABELS = ("table", "list_item", "code", "formula", "caption")

# ------------------------------------------------------------------ word lists (folded: lower case, no accents)

_ADJ = (r"(?:(?:dringliche[rsn]?|schriftliche[rsn]?|kleine[rn]?|einfache[rsn]?|parlamentarische[rsn]?|"
        r"uberparteiliche[rsn]?|interfraktionelle[rsn]?|uberwiesene[rsn]?) )*")
_NOUN = (r"(?:parlamentarische erklarung|parlamentarische empfehlung|interpellation|motion|postulat|anfrage|auftrag|vorstoss|volksmotion|jugendmotion|petition|"
         r"volksinitiative|einzelinitiative|standesinitiative|gemeindeinitiative|initiative|resolution|"
         r"beschlussesantrag|fraktionserklarung|leistungsmotion|budgetpostulat|auskunftsbegehren|anzug|"
         r"question|interpellanza|interrogazione|mozione|postulato|iniziativa|petizione|risoluzione)")
_ADJ_POST = (r"(?: (?:ecrite|orale|urgente|populaire|parlementaire|scritta|interpartitica|parlamentare|generica|"
             r"elaborata|popolare|cantonale|comunale))?")
TYPE = _ADJ + _NOUN + _ADJ_POST + r"(?![\w-])"
# words that can stand before the type word on a line of a response document
_PREFIX = (r"(?:(?:schriftliche |mundliche )?(?:beantwortung|antwort|stellungnahme|bericht|zwischenbericht|schlussbericht)"
           r"(?: de[sr] [a-z-]{4,30})?(?: (?:der|des|zur|zum|zu|einer|eines|auf die|auf das|auf den))? |"
           r"(?:reponse|rapport)(?: d[ue] [a-z' -]{3,40}?)? (?:a l'|a la |au |aux |sur l'|sur la |sur le )|"
           r"(?:risposta|rapporto)(?: del(?:la)? [a-z' -]{3,40}?)? (?:all'|alla |al |sull'|sulla |sul )|"
           r"testo dell'|testo della |a l'|a la |au |zur |zum |alla |l'|all')?")
# a number of the agenda or of the affair before the type word: "8 B. Eingereichte Motion", "2012.1566 Interpellation",
# "(24/130) Schriftliche Anfrage", "21.4209 Motion"
_NUM_PRE = (r"(?:traktandum \d{1,3}[a-z]?[:.]? )?(?:(?:nr\.? ?)?\(?\d[\d./-]{0,11}\)?\.? (?:[a-z]\.? |[a-z]{1,2}-\d[\d./-]{0,9} |\d\.\d[\d.]{0,6} )?)?"
            r"(?:eingereichte[rs]? )?")
_MARK = r"[\sx☐☒□■\uf0fd\uf0b7\uf0a8•·*@\"-]{0,4}"
TYPE_LINE_RX = re.compile(r"^(?P<mark>" + _MARK + r")(?P<num>" + _NUM_PRE + r")(?P<prefix>" + _PREFIX
                          + r")(?P<type>" + TYPE + r")")
TYPE_ANY_RX = re.compile(r"(?<![\w-])" + TYPE)
NUM_RX = re.compile(r"\s*(?:(?:nr|no|n°|n|numero|nummer)\b\.? ?)?(?:[a-z]{1,3} ?)?\d[\d.]*(?: ?[/-] ?\d[\d.]*)*\b")
KIND = (r"(?:bericht und antrag|botschaft|bericht|vorlage|weisung|rapport|message|preavis|messaggio|rapporto|"
        r"beantwortung|antwort|reponse|risposta|stellungnahme)")
KIND_ONLY_RX = re.compile(r"^" + KIND + r"(?: (?:an|ans|zuhanden|zu handen|a|au|aux|al|alla|all'|des|der|du|de la|"
                          r"del|della|vom|zum|zur) ?.{0,70})?[:.]?$")
LABEL_WORDS = (r"(?:titel des vorstosses|titel des geschafts|titel der vorlage|geschaftstitel|vorstosstitel|titel|"
               r"betreff|betrifft|gegenstand|thema|"
               r"titre de l'objet|titre de l'intervention|objet de l'intervention|objet|sujet ?.? ?titre|sujet|titre|"
               r"intitule|concerne|"
               r"titolo dell'atto|titolo|oggetto|tema|argomento)")
# labels that name the affair as a whole (title, and often the type and the author too): table rows only
AFFAIR_LABEL_WORDS = r"(?:geschaft|vorlage|vorstoss|traktandum|affaire|intervention|atto|trattanda)"
# labels of a form that stand on their own line with no colon ("Datum", "Archiv", "Beschluss-Nr.", "Sitzung Nr.")
BARE_LABEL_RX = re.compile(
    r"^(?:datum|date|data|archiv|registratur|ablage|beschluss|sitzung|seance|seduta|geschaft|nummer|numero|"
    r"referenz|reference|riferimento|aktenzeichen|direktion|departement|dipartimento|ressort|seite|page|pagina|"
    r"eingang|eingereicht|depot|typ|type|tipo|art|kategorie|status|klassifizierung|autor|auteur|autore|"
    r"urheber|verfasser|absender|zustandig)[a-z]*(?:[\s./-]{0,2}(?:nr|no|n°|am|vom|du|del)\.?)?\s*$")
LABEL_RX = re.compile(r"^(?P<label>" + LABEL_WORDS + r")\s*(?:(?P<sep>[:\t])\s*(?P<rest>.*))?$")
_CUE_A = (r"(?:betreffend|betr\b\.?|bezuglich|zum thema|mit dem titel|unter dem titel|concernant|intitulee?s?|"
          r"riguardante|concernente|inerente|circa|dal titolo|avente per oggetto)")
_CUE_B = (r"(?:relati(?:f|ve|fs|ves) (?:a la |a l'|au |aux |a )|au sujet (?:de la |de l'|du |des |de |d')|"
          r"in merito (?:alla |allo |all'|alle |agli |ai |al |a )|"
          r"relativa (?:alla |allo |all'|alle |agli |ai |al |a ))")
_CUE_A, _CUE_B = _CUE_A.replace(" ", r"\s"), _CUE_B.replace(" ", r"\s")
_CUE_A = _CUE_A.replace("betreffend|", r"be(?:-\n)?tref(?:-\n)?fend|", 1).replace("concernant|", r"con(?:-\n)?cer(?:-\n)?nant|", 1)
CUE_RX = re.compile(r"(?:(?<=\s)|^)(?:" + _CUE_A + r"(?=[\s:\"])\s*:?\s*|" + _CUE_B + r")")
CUE_START_RX = re.compile(r"^\s*(?:(?:zur|zum|zu|uber)\s+|sur la |sur le |sur les |sur l'|sur |sulla |sullo |sull'|sul |"
                          r"sui |circa )\s*")
CUE_LINE_RX = re.compile(r"^\s*(?P<cue>betreffend|betr\b\.?|concernant|intitulee?s?|riguardante|concernente)"
                         r"\s*:?\s*(?P<rest>.*)$")
PLAIN_LOWER_NO = re.compile(r"^(?:gemass|allenfalls|eventuell|vorgeschlagen|betreffend|eingereicht|namens|selon|"
                            r"secondo|conformement|presentat[ao]|depose[es]?)\b")
PLAIN_LOWER_OK = re.compile(r"^(?:pour|per|fur|gegen|contre|contro|wie|was|wo|warum|weshalb|quels?|quelles?|comment|"
                            r"pourquoi|quale|quali|come|perche|stop|ja|nein|non|oui|no|si)\b")
STATUS = (r"(?:(?:schriftliche )?beantwortung|gutheissung|ablehnung|antrag an|antrag des|antrag auf|"
          r"bericht und antrag|bericht des|stellungnahme|abschreibung|nichterheblicherklarung|erheblicherklarung|"
          r"uberweisung|entgegennahme|annahme|umwandlung|fristerstreckung|fristverlangerung|kenntnisnahme|"
          r"reponse|risposta|antwort des|antwort der|dringlicherklarung|ruckzug|prise de connaissance|"
          r"prise d'acte|presa d'atto|begrundungsbericht|begrundung|prufungsbericht|dokumenttitel|mitbericht|bericht der|antwort|"
          r"antwort stadtrat|antwort gemeinderat|motiv\. beschluss)")
# a status phrase can go over a line end: "Antwort" / "des Regierungsrats", "Ant-" / "wort des Regierungsrats"
STATUS = STATUS.replace(" ", r"\s+").replace("antwort\\s+des|", "antwort\\s+des|ant-\\s+wort\\s+de[sr]|", 1)
STATUS_RX = re.compile(r"(?:\s*[.;,:/]\s*|\s*\n\s*|\s+-\s+)" + STATUS + r"\b.*$", re.S)
PARTY = (r"(?:sp|svp|fdp|cvp|glp|evp|edu|bdp|gps|gp|grune|grunen|mitte|al|juso|jsvp|jfdp|plr|ps|udc|pdc|pvl|pev|"
         r"verts|vert'liberaux|lega|ppd|plrt|udf|centro|verdi|freie wahler|fw|parteilos|fraktion|fraktionen|"
         r"groupe|gruppo|mitunterzeichn\w*|mitunterzeichnende|consorts|cofirmatari|kons\.|konsorten|\w*partei|parti|partito|"
         r"union|liberalen)")
PARTY_RX = re.compile(r"(?<![\w-])" + PARTY + r"(?![\w])")
# party marks that are no common word of German, French or Italian (folded text)
PARTY_SURE_RX = re.compile(r"(?<![\w-])(?:svp|fdp|cvp|glp|evp|edu|bdp|gps|juso|jsvp|jfdp|plr|udc|pdc|pvl|pev|ppd|plrt|"
                           r"udf|vert'liberaux|freie wahler|parteilos|fraktion|fraktionen|mitunterzeichn\w*|consorts|konsorten|"
                           r"junge grune|junge grunliberale|jungfreisinnige|grunliberale[nr]?|unterzeichn\w*|erstunterzeichn\w*|"
                           r"cofirmatari[eo]?|\w*partei)(?![\w])")
# party marks that are also common words: they count in the printed form only (capital letters), see _party_mark
PARTY_UPPER_RX = re.compile(r"(?<![\w-])(?:SP|GP|AL|PS|FW|PLR|PPD|UDC|PS|GLP|EVP|EDU)(?![\w])")
PARTY_CAP_RX = re.compile(r"(?:[(,/]\s*|\b(?:der|des|du|del|della|die|les|la|il)\s+)(?:Grüne[nr]?|GRÜNE|Mitte|Verts|Lega|"
                          r"Centro|Verdi|Liberalen|Parti\s+[a-z]+|Partito\s+[a-z]+|Union\s+[a-zA-Z]+)(?![\w])"
                          r"|(?<![\w-])(?:Grüne|Mitte|Lega|Verdi|Centro)[-/ ](?:Fraktion|Gruppo|[A-Z]{2,4}\b)")
ROLE = (r"(?:gemeinderat|gemeinderatin|landrat|landratin|kantonsrat|kantonsratin|grossrat|grossratin|"
        r"einwohnerrat|einwohnerratin|stadtrat|stadtratin|parlamentarier\w*|herrn?|frau|m\.|mme|mm\.|"
        r"conseiller|conseillere|depute|deputee|on\.|signor\w*|consigliere)")
AUTHOR_CUE_RX = re.compile(r"^\s*(?:nr\.? ?[\w./-]+ )?von [^\n\"]{3,90}?(?:\)|,)\s+(?:zu|zur|zum|uber)\s+")
MID_CUE_RX = re.compile(r"\s(?:betreffend|betr\b\.?)\s*:?\s+")
SENT_TYPE_QUOTE_RX = re.compile(r"(?<![\w-])" + TYPE + r"[^\".:;!?]{0,80}\"([^\"]{3,400})\"", re.S)
AUTHOR_TAIL_RX = re.compile(r"[,;]?\s+(?P<w>von|eingereicht|eingegangen|uberwiesen|depose[es]? par|presentat[ao] da|"
                            r"du groupe|des groupes|de m\.|de mme)\s")
AUTHOR_VERB_RX = re.compile(r"^\s*(?:eingereicht|eingegangen|erstunterzeichn\w*|unterzeichn\w*|mitunterzeichn\w*|"
                            r"depose[es]?|presentat[ao])\b")
HEAD_KIND_RX = re.compile(r"^(?:" + KIND + r"|intervention parlementaire|interventions parlementaires|"
                          r"parlamentarische[rs]? vorsto(?:ss|sse)|atto parlamentare|auszug aus dem (?:\w+ )?protokoll|"
                          r"antrag de[rs]|antrag an|note de service|note a l'attention|proposta di risoluzione|"
                          r"mitteilung durch|version \d|analyse der antrage|adressatenliste|ordnungsantrag|"
                          r"protokollauszug|extrait du proces-verbal|proces-verbal|protokoll|estratto|arrete|decision|"
                          r"decisione|\w*beschluss|fassung|synopse|vergleich)\b")
AUTHOR_ORG_TAIL_RX = re.compile(r"[,;]?\s+(?:der|des|du|del|della)\s+" + PARTY
                                + r"(?:[-\s]?fraktion\w*|\s[a-z]+)?\s*$")
AUTHOR_START_RX = re.compile(r"^\s*[/,(]?\s*(?:von|eingereicht|erstunterzeichn\w*|unterzeichn\w*|mitunterzeichn\w*|"
                             r"namens|de mm?\.|de mme|depose[es]?|presentat[ao]|del signor|della signora|dell'on|"
                             r"fraktion|groupe|gruppo|der fraktion|der fraktionen|du groupe|des groupes|dei gruppi|"
                             r"del gruppo)(?![a-z])")
SUBMIT_RX = re.compile(r"^\s*(?:eingereicht|eingang|eingegangen|depot|depose[es]?|presentat[ao]|inoltrat[ao]|datum|"
                       r"date|data|am|vom|du|del)\b")
ADDRESSEE_RX = re.compile(r"^\s*(?:an|ans|zuhanden|zu handen|z\. ?h\.|au|aux|a l'attention|al|alla|all'|agli)\s+"
                          r"(?:den|das|die|der|dem|le|la|les|l'|il|lo|i)?\s*\w+")
ADDRESS_RX = re.compile(r"^(?:herrn?|frau|monsieur|madame|egregio|gentile|signora?|familie)\b")
SALUTATION_RX = re.compile(r"^\s*(?:sehr geehrte|geehrte|geschatzte|liebe |werte |monsieur|madame|mesdames|"
                           r"messieurs|egregi|gentil|lodevol|onorevol|signor|stimat|herr prasident|frau prasident)")
STRUCT_RX = re.compile(r"^(?:ausgangslage|antrag|antrage|begrundung|sachverhalt|einleitung|frage|fragen|text|"
                       r"wortlaut(?: de[rs] \w+)?|hintergrund|erwagungen|zusammenfassung|inhaltsverzeichnis|inhalt|"
                       r"sommaire|table des matieres|indice|sommario|contexte|introduction|developpement|motivation|conclusions?|premessa|"
                       r"introduzione|considerato che|antwort|antworten|beantwortung|stellungnahme|"
                       r"text und begrundung|protokollauszug|beschluss|abstimmung|synopse|anhang|beilagen?|"
                       r"annexes?|allegat[oi]|traktandum|tagesordnung|enonce de la question|absender|adressat|empfanger|"
                       r"kontakt|verteiler|formelles|rechtliches|eingegangen|eintretensdebatte|wiedererwagung|"
                       r"vorbemerkung(?:en)?|einleitende bemerkungen|zu den gestellten fragen|um was geht es|"
                       r"motivazione|nel merito|geltende regelung|premesse?|mandat|"
                       r"der \w+ beantwortet|aktennotiz|medienmitteilung)\b[\s:.]*$")
NUMBERED_RX = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2})*[.)]?|[ivx]{1,4}\.|[a-z][.)]|art\.|§)\s")
ORG_FIRST = frozenset(
    "stadt gemeinde kanton stadtrat gemeinderat regierungsrat grosser einwohnerrat parlament stadtparlament landrat "
    "kantonsrat standeskommission stadtkanzlei gemeindekanzlei staatskanzlei departement direktion bundesamt "
    "conseil commune ville canton municipalite chancellerie office republique confederation "
    "municipio municipalita citta comune consiglio cancelleria repubblica fraktion partei groupe gruppo parti partito "
    "schweizerische eidgenossisches eidgenossische buro bureau ufficio ratsburo sekretariat ratssekretariat "
    "parlamentsdienste parlamentsdienst dipartimento dicastero dicastere divisione commissione commission kommission".split())
NUM_LINE_WORDS = frozenset("nr no n gr ggr sr er kr lr geschaft geschafts gesch mm prot srb rrb ka po mo ip ir p i m a "
                           "numero nummer beschluss ref rif".split())
YES_NO = frozenset("ja nein oui non si no x".split())
NOUN_SUFFIX_RX = re.compile(r"(?:ung|heit|keit|schaft|tion|itat|ment|nis|ismus|ierung|gesetz|plan|konzept)$")
BODY_RX = re.compile(r"\b(?:ich|wir|je|nous|gestutzt auf|vu l'|vu les|visto|visti)\b")
VERB_RX = re.compile(r"\b(?:wird|wurde|wurden|hat|haben|ist|sind|est|sont|a ete|ont ete|viene|sono|e stat[oa])\b")
ABBREV_END_RX = re.compile(r"(?:\b(?:st|nr|art|abs|bzw|dr|ca|kt|inkl|resp|str|ev|evtl|ch|no|m|mme|on|sig|lett|cpv|"
                           r"ziff|lit|z|b|u|a|d|h|s|vgl)|\d)\.$")
SENT_TITLE_RX = re.compile(r"(?:mit\sdem\stitel|unter\sdem\stitel|mit\sdem\sbetreff|betitelt(?:\smit)?|"
                           r"intitulee?s?|dal\stitolo|intitolat[ao]|con\sil\stitolo|portant\sle\stitre)"
                           r"\s*:?\s*\"([^\"]{3,400})\"", re.S)
TYPE_OR_KIND_RX = re.compile(r"(?<![\w-])(?:" + TYPE + r"|" + KIND + r"(?![\w-]))")
WEAK_FORM_TIERS = ("weak_first_heading", "heading_after_form", "text_after_form", "after_type_text", "sentence_cue",
                   "before_type_line", "heading_before_response", "heading_before_salutation")
SOFT_LINE_TIERS = ("after_type_text", "after_kind_text", "type_plain_short")
AFTER_LINES = 30          # a line that holds only a type word counts only in the first 30 lines
STOP_END = vb.STOPWORDS | frozenset("bei nach vor uber unter gegen ohne um bzw sowie oder ou o ed ad sulla sul".split())


# ------------------------------------------------------------------ helpers of this file

def norm_title(s: str) -> str:
    """The title on one line. norm_text of the interface, plus two line-end cases that norm_text does not have:
    a soft hyphen at a line end is a word join, and a hyphen at a line end before und, oder, bzw, sowie, et, ou, e, o
    stays (for example "Aus-\\nund Weiterbildung")."""
    s = re.sub(r"\u00ad[ \t]*\n\s*", "", s or "")
    s = re.sub(r"[ \t]*\n\s*\n[ \t]*", "\n", s)                       # a block limit in the span is one line end
    s = re.sub(r"(?<=[A-ZÀ-Ý])-[ \t]*\n[ \t]*(?=[A-ZÀ-Ý]{1,3}-)", "-", s)   # "DESIRE-\nT-IL"
    s = re.sub(r"-[ \t]*\n\s*(?=(?:und|oder|bzw|sowie|et|ou|e|o|ed)\b)", "- ", s)
    return vb.norm_text(s)


class _Reg:
    """A part of the document text with its folded form (line feeds kept) and the map back to Doc.text."""

    def __init__(self, doc: vb.Doc, start: int, end: int):
        self.doc, self.start, self.end = doc, start, end
        self.f = vb.fold_map(doc.text[start:end], base=start, keep_newlines=True)
        self.t = self.f.text

    def span(self, a: int, b: int) -> tuple[int, int]:
        return self.f.span(a, b)


def _fold_line(text: str) -> str:
    t = vb.fold_map(text, keep_newlines=False).text.strip()
    if re.fullmatch(r"(?:\w ){3,}\w", t):          # letter-spaced word: "R I S P O S T A"
        return t.replace(" ", "")
    # a letter-spaced word with other words on the line: "P O S T U L A T gemäss § 44"
    return re.sub(r"(?<![a-z0-9])(?:[a-z] ){3,}[a-z](?![a-z0-9])", lambda m: m.group(0).replace(" ", ""), t)


def _head(doc: vb.Doc) -> list[vb.Line]:
    lines = [ln for ln in doc.lines if doc.blocks[ln.block_index].label not in SKIP_LABELS]
    if not lines:
        return []
    page = lines[0].page
    return [ln for ln in lines if ln.page == page][:HEAD_LINES]


def _label(doc: vb.Doc, ln: vb.Line) -> str:
    """The Docling label of the block of the line. A table block in which fewer than 1 of 3 lines has a cell limit
    is a list of lines, not a table: it is read as text (a head table with one column)."""
    b = doc.blocks[ln.block_index]
    if b.label == "table" and 3 * sum(1 for x in b.lines if "\t" in x.text) < len(b.lines) and "\t" not in ln.text:
        return "text"
    return b.label


def _date_only(fl: str) -> bool:
    hits = vb.find_dates(fl)
    if not hits:
        return False
    rest = fl
    for h in reversed(hits):
        rest = rest[:h.start] + " " + rest[h.end:]
    return len(re.findall(r"[a-z]{2,}", rest)) <= 2 and len(rest.strip()) <= 30


YEARS_RX = re.compile(r"(?:19|20)\d\d ?[-/] ?(?:19|20)?\d\d")           # "2016 - 2019": a part of a title


def _number_line(fl: str) -> bool:
    if len(fl) > 28 or not re.search(r"\d", fl):
        return False
    return all(w in NUM_LINE_WORDS for w in re.findall(r"[a-z]+", fl))


def _name_like(raw: str) -> bool:
    """2 or 3 words, each with a first capital letter and then lower-case letters (a person name on its own line)."""
    words = raw.replace(",", " ").split()
    return 2 <= len(words) <= 3 and all(re.fullmatch(r"[A-ZÄÖÜÉÈÀ][a-zäöüéèàçñ'.-]+", w) for w in words)


def _party_mark(fl: str, raw: str) -> bool:
    """True if the line holds a party mark. A mark that is also a common word ("al", "parti", "union", "centro",
    "verdi", "lega", "mitte", "ps", "sp") counts only in its printed form: capital letters, or a capital first letter
    after a bracket, a comma or an article, or joined to a group word."""
    if PARTY_SURE_RX.search(fl) or PARTY_UPPER_RX.search(raw) or PARTY_CAP_RX.search(raw):
        return True
    words = raw.split()                                      # a short line that is the name of a party
    return len(words) <= 4 and bool(words) and bool(re.fullmatch(
        r"(?:Union|Partei|Parti|Partito|Lega|Mitte|Grüne|GRÜNE|Verdi|Verts|Liberalen)", words[-1].strip(".,")) or re.fullmatch(
        r"(?:Die Mitte|Grüne|GRÜNE|Lega|I Verdi|Les Verts)\b.*", raw.strip()))


def _author_line(fl: str, raw: str) -> bool:
    if AUTHOR_START_RX.match(fl):
        return True
    n = len(re.findall(r"[a-z0-9]+", fl))
    if n <= 14 and _party_mark(fl, raw) and not CUE_RX.search(fl) and '"' not in fl:
        return True
    if n <= 40 and len(PARTY_UPPER_RX.findall(raw)) + len(PARTY_SURE_RX.findall(fl)) >= 3 and raw.count(",") >= 2 \
            and '"' not in fl:
        return True                                          # "Lukas Auer SP / Grüne, Heidi Heine SP / Grüne, ..."
    return bool(re.search(r"\((?:[a-z./ -]{0,12}[ ./-])?" + PARTY + r"(?:[ ./,-][a-z./ -]{0,12})?\)", fl)) \
        and n <= 14 and '"' not in fl


def _letterhead(fl: str) -> bool:
    words = re.findall(r"[a-z]+", fl)
    if not words:
        return True
    if re.search(r"@|www\.|\.ch\b|https?:|telefon|\btel\b|\bfax\b|postfach|case postale|casella postale", fl):
        return True
    if re.match(r"^(?:ch-)?\d{4} [a-z]", fl) or (len(words) <= 10 and re.search(r"\b(?:ch-)?\d{4} [a-z]{3,}$", fl)):
        return True                                          # postal code and place
    return words[0] in ORG_FIRST and len(words) <= 6


def _org_line(fl: str) -> bool:
    """A line that names a body, not a title: "del Municipio di Mendrisio", "DU CONSEIL MUNICIPAL", "AU"."""
    words = re.findall(r"[a-z]+", fl)
    while words and words[0] in ("del", "della", "dei", "du", "de", "la", "le", "des", "der", "den", "das", "dem", "an",
                                 "au", "aux", "al", "alla", "l", "vom", "von", "di", "a"):
        words = words[1:]
    return len(words) <= 6 and (not words or words[0] in ORG_FIRST)


def _form_label(fl: str) -> bool:
    """A label of a form: a short text and a colon, with no value or a short value ("Geschäftsnummer: 2009/116")."""
    m = re.match(r"^([^:\"]{2,40}):\s*(.{0,45})$", fl)
    return bool(m) and not LABEL_RX.match(fl) and not CUE_LINE_RX.match(fl)


FORM_WORD_RX = re.compile(
    r"^(?:datum|date|data|nr|nummer|numero|n°|no|geschaft\w*|eingereicht\w*|eingang|von|am|vom|direktion|direction|"
    r"direzione|ressort|klassifizierung|classification|sitzung\w*|seance|seduta|beschluss\w*|traktandum|registratur|"
    r"aktenzeichen|referenz|reference|riferimento|telefon|kontakt|typ|art|vorstoss\w*|urgence|depos\w*|auteur\S*|"
    r"cosignataires|mitunterzeichn\w*|erstunterzeichn\w*|antrag\w*|beilagen?|zustandig\w*|verfasser\w*|urheber\w*|"
    r"absender|an|kopie|cc|seite|page|pagina|version|stand|status|frist|termin|tel|fax|e-mail|mail|ort|lieu|luogo|"
    r"bearbeit\w*|sachbearbeit\w*|departement|dipartimento|dicastero|abteilung|motion\w*|richtlinienmotion|"
    r"dringlich\w*|type|tipo|mots cles|stichworte?|schlagworte?)\b")


def _form_label_strict(fl: str) -> bool:
    """A label of a form, with a narrow test for a line that has text after the colon: a title can hold a colon
    ("Rechtsabbiegen bei Rot: Stärkung der Velostadt", "Nouvel horaire CFF 2025 : Bienne ... ?")."""
    m = re.match(r"^([^:\"]{2,40}):\s*(.{0,45})$", fl)
    if not m or LABEL_RX.match(fl) or CUE_LINE_RX.match(fl):
        return False
    lab, val = m.group(1).strip(), m.group(2).strip()
    if not val:
        return True
    if "?" in val or "!" in val or len(lab.split()) > 3:
        return False
    return bool(FORM_WORD_RX.match(lab) or re.search(r"\d", val) or len(val.split()) <= 2)


def _structural(fl: str) -> bool:
    return bool(STRUCT_RX.match(fl) or NUMBERED_RX.match(fl))


def _type_only_rest(rest: str, raw_rest: str) -> bool:
    """True if the text after the type word on its line is no title: empty, a number, a date, an author,
    an addressee, brackets or only function words."""
    r = rest
    m = NUM_RX.match(r)
    if m:
        r = r[m.end():]
    r = r.strip(" \t:.,;/-")
    if not r:
        return True
    if r.startswith("(") and r.endswith(")"):
        return True
    if _date_only(r) or (ADDRESSEE_RX.match(r) and ":" not in r and len(r.split()) <= 5
                         and not re.search(r"\s(?:zu|zur|zum|uber|betreffend|betr\.?)\s", r)):
        return True
    if re.match(r"^(?:gemass|gem\.?|nach|selon|conformement a|ai sensi|secondo) .{0,60}$", r) and ":" not in r \
            and re.search(r"§|\bart\b|\d", r):
        return True                                          # "Postulat gemäss § 44 der GO"
    if re.fullmatch(r"(?:evtl\.?|eventuell|allenfalls)? ?(?:motion )?(?:mit|ohne) richtliniencharakter", r):
        return True
    words = re.findall(r"[a-z0-9']+", r)
    if all(w in vb.STOPWORDS or w in ("vom", "del", "du", "nr", "no", "von", "dell") for w in words):
        return True
    return False


def _title_ok(norm: str, label: str, weak: bool = False, quoted: bool = False, labelled: bool = False) -> bool:
    """Form test of a candidate (the normalised title)."""
    if not 3 <= len(norm) <= MAX_TITLE:
        return False
    fl = vb.fold(norm)
    words = re.findall(r"[a-z]+", fl)
    if quoted and len(words) == 1 and len(words[0]) >= 3 and norm.isupper():
        return True                                          # Interpellation "GZO"
    if not any(len(w) >= 4 for w in words) or (
            len(words) == 1 and len(words[0]) < 6
            and not (re.search(r"\d", fl) and any(tok.isalpha() and len(tok) >= 4 for tok in fl.split()))):
        return False                                         # "Tempo 30" is a title; "Dorf" is not
    if all(w in YES_NO for w in words):
        return False
    if SALUTATION_RX.match(fl) or _structural(fl) or _date_only(fl) or _number_line(fl):
        return False
    if re.search(r"@|www\.|https?:|klicken sie hier|text eingeben|cliquez ici|click here", fl):
        return False
    if label not in HEADING_LABELS and len(words) >= 9 and norm.endswith(".") and not norm.endswith("...") \
            and not labelled:
        return False                                         # a sentence of the body text
    if weak and (len(words) < 2 and len(fl) < 10):
        return False
    if weak and (re.search(r"\b(?:sfr|chf|fr)\b\.? ?\d|, (?:ch-)?\d{4} [a-z]{3,}|strasse \d+[a-z]?(?:,|$)|\((?:geandert|neu|aufgehoben)\)$", fl)
                 or ADDRESS_RX.match(fl)):
        return False
    return True


def _trim(reg: _Reg, a: int, b: int) -> tuple[int, int] | None:
    """Remove white space, list punctuation and the quotation marks around the full title from reg.t[a:b]."""
    t = reg.t
    for _ in range(4):
        while a < b and t[a] in " \n\t:;,.-/‚'":
            a += 1
        while b > a and t[b - 1] in " \n\t:;,/-":
            b -= 1
        if b - a >= 2 and t[b - 1] == "." and not t[a:b].endswith("...") and not ABBREV_END_RX.search(t[a:b]):
            b -= 1
            continue
        body = t[a:b]
        n = body.count('"')
        if n == 2 and body.startswith('"') and body.endswith('"'):
            a, b = a + 1, b - 1
            continue
        if n == 1 and body.startswith('"'):
            a += 1
            continue
        if n == 1 and body.endswith('"'):
            b -= 1
            continue
        if body.endswith("'") and body.count("'") == 1:
            b -= 1
            continue
        break
    return (a, b) if b > a else None


def _cut_tail(reg: _Reg, a: int, b: int) -> int:
    """The end of the title in reg.t[a:b]: a status word, an author or a date after the title is cut."""
    t = reg.t
    m = STATUS_RX.search(t, a, b)
    if m and m.start() > a:
        b = m.start()
    for m in AUTHOR_TAIL_RX.finditer(t, a, b):
        if m.start() <= a:
            continue
        tail = t[m.end():b]
        s0, _ = reg.span(m.end(), m.end() + 1) if m.end() < len(t) else (reg.end, reg.end)
        raw_tail = reg.doc.text[s0:reg.end]
        tail, raw_tail = re.sub(r"-\n", "", tail), re.sub(r"-\n", "", raw_tail)
        role = re.match(r"\s*" + ROLE + r"(?![\w])", tail)
        names = re.match(r"\s*[A-ZÄÖÜÉ][\w.'-]+\s+(?:(?:von|van|de|del|di)\s+)?[A-ZÄÖÜÉ][\w'-]+", raw_tail)
        party = PARTY_RX.search(tail)
        if m.group("w") == "von" and not role and not party:
            before = re.findall(r"[a-z]+", t[a:m.start()])
            segs = [x for x in re.split(r",\s+|\s+(?:und|et|e)\s+", " ".join(raw_tail[:b - m.end() + 40].split())) if x]
            if len(segs) >= 2 and all(re.fullmatch(r"[A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+(?: [A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+){1,2}", x)
                                      for x in segs):
                b = m.start()                               # a list of names: "von Daniela Morf, Markus Bürgi und Daniel Frei"
                break
            if before and NOUN_SUFFIX_RX.search(before[-1]) and not t[a:m.start()].rstrip().endswith(","):
                continue                                    # "Überprüfung von Lizenzgebühren": no author
        if m.group("w") in ("eingereicht", "eingegangen", "uberwiesen") or m.group("w").startswith(("depose", "presentat")) \
                or role or (names and (party or len(tail.split()) <= 4)) or (party and len(tail.split()) <= 12
                                                                      and re.match(r"\s*[A-ZÄÖÜÉ]", raw_tail)):
            b = m.start()
            break
    m = AUTHOR_ORG_TAIL_RX.search(t, a, b)
    if m and m.start() > a:
        b = m.start()
    m = re.search(r"\s+fraktion(?:en)?\s+[a-z+/ -]{2,24}$", t[a:b])
    if m and m.start() > 0 and PARTY_RX.search(m.group(0)[9:]):
        b = a + m.start()                                   # "... der Stadt Thun Fraktion EVP+EDU"
    for _ in range(3):                                      # number, date and structure lines after the title
        nl = t.rfind("\n", a, b)
        if nl <= a or not (_number_line(t[nl + 1:b].strip()) or _date_only(t[nl + 1:b].strip())
                           or STRUCT_RX.match(t[nl + 1:b].strip())) \
                or YEARS_RX.fullmatch(t[nl + 1:b].strip()) or re.search(r"\b(?:bis|ab|seit|fur|per|vom|des)$", t[a:nl].strip()):
            break
        b = nl
    m = re.search(r"[,;]?\s+(?:vom|du|del|dell')\s*\d{1,2}[.\s][^\n]{3,22}$", t[a:b])
    if m and m.start() > 0 and vb.find_dates(m.group(0)):
        b = a + m.start()
    return b


def _result(reg: _Reg, a: int, b: int, tier: str, label: str, detail: dict, cut: bool = True):
    """(start, end, tier, detail) in Doc.text for reg.t[a:b], or None if the form test fails."""
    if cut:
        b = _cut_tail(reg, a, b)
        if label not in HEADING_LABELS and tier in ("type_cue", "type_colon", "cue_line", "cue_in_line", "after_kind_cue"):
            for m in re.finditer(r"\.\s+(?=\S)", reg.t[a:b]):  # the end of the sentence, if a new sentence follows
                p0 = reg.span(a + m.end(), a + m.end() + 1)[0]
                rest = reg.t[a + m.end():b]
                if reg.doc.text[p0:p0 + 1].isupper() and not ABBREV_END_RX.search(reg.t[a:a + m.start() + 1]) \
                        and VERB_RX.search(rest) and len(rest.split()) >= 6:
                    b = a + m.start()
                    break
    body = reg.t[a:b].strip()
    if label not in HEADING_LABELS and tier in ("after_type_text", "after_kind_text", "type_plain", "label_cue",
                                                "cue_line", APERTUS_TIER):
        n_words = len(re.findall(r"[a-z]+", body))
        if n_words >= 9 and body.endswith((".", ":")) and not body.endswith("...") \
                and not (((tier == "label_cue" and detail.get("same_line")) or detail.get("closed_by"))
                         and n_words <= 30 and body.endswith(".")):
            return None
        if tier in ("after_type_text", "after_kind_text") and (
                (not body.endswith(("?", "!")) and VERB_RX.search(body) and n_words >= 9 and not detail.get("closed_by")) or BODY_RX.search(body)
                or len(body) > 220):
            return None
    if tier == "sentence_cue" and body.count('"') % 2 == 1:
        return None
    ab = _trim(reg, a, b)
    if ab is None:
        return None
    s, e = reg.span(*ab)
    while s < e and reg.doc.text[s].isspace():
        s += 1
    while e > s and reg.doc.text[e - 1].isspace():
        e -= 1
    if e <= s:
        return None
    norm = norm_title(reg.doc.text[s:e])
    if not _title_ok(norm, label, weak=tier in WEAK_FORM_TIERS, quoted=bool(detail.get("quote_first")),
                     labelled=(tier == "label_cue" and bool(detail.get("same_line"))) or bool(detail.get("closed_by"))):
        return None
    if tier in ("after_type_text", "sentence_cue") and len(re.findall(r"[a-z0-9]+", vb.fold(norm))) < 2:
        return None
    return s, e, tier, detail


def _line_end(ln: vb.Line) -> int:
    """The end of the line in Doc.text; for a line that prints its text 2 times ("A A") the end of the first copy."""
    t = ln.text
    n = len(t)
    for cut in range(n // 2 - 2, n // 2 + 3):
        if 12 <= cut < n and t[cut:cut + 1] == " " and t[:cut].strip() == t[cut + 1:].strip():
            return ln.char_start + len(t[:cut].rstrip())
    return ln.char_end


def _block_rest(head: list[vb.Line], i: int) -> list[int]:
    """The indexes in `head` of line i and of the lines after it in the same block."""
    out = [i]
    j = i + 1
    while j < len(head) and head[j].block_index == head[i].block_index:
        out.append(j)
        j += 1
    return out


def _continues(doc: vb.Doc, head: list[vb.Line], last: int) -> bool:
    """True if the title of line `last` continues in the next block: the line ends with a hyphen or with a function
    word, the next block has the same Docling label and at most 3 lines, and it is no new start."""
    if last + 1 >= len(head):
        return False
    a, b = head[last], head[last + 1]
    if b.block_index == a.block_index or _label(doc, a) != _label(doc, b):
        return False
    if len(_block_rest(head, last + 1)) > 3:
        return False
    fa, fb = _fold_line(a.text), _fold_line(b.text)
    if TYPE_LINE_RX.match(fb) or SALUTATION_RX.match(fb) or _structural(fb) or _form_label_strict(fb):
        return False
    words = re.findall(r"[a-z0-9']+", fa)
    open_quote = fa.count('"') % 2 == 1 and '"' in " ".join(_fold_line(head[k].text) for k in _block_rest(head, last + 1))
    lower_go_on = (_label(doc, a) in HEADING_LABELS and a.text.rstrip()[-1:].isalpha() and b.text.lstrip()[:1].islower()
                   and len(_block_rest(head, last + 1)) <= 2 and not _author_line(fb, b.text)
                   and not CUE_LINE_RX.match(fb) and not AUTHOR_START_RX.match(fb))
    text_go_on = (_label(doc, a) == "text" and len(doc.blocks[a.block_index].lines) == 1 and len(_block_rest(head, last + 1)) == 1
                  and a.text.rstrip()[-1:].isalpha() and b.text.lstrip()[:1].islower() and 2 <= len(fb.split()) <= 9
                  and len(fa.split()) >= 4 and not b.text.rstrip().endswith((".", ":")) and not VERB_RX.search(fb)
                  and not _author_line(fb, b.text) and not CUE_LINE_RX.match(fb) and not AUTHOR_START_RX.match(fb)
                  and not SUBMIT_RX.match(fb) and not _date_only(fb))
    return a.text.rstrip().endswith(("-", "\u00ad")) or (bool(words) and words[-1] in STOP_END) or open_quote \
        or lower_go_on or text_go_on


def _run_from(doc: vb.Doc, head: list[vb.Line], j: int, max_lines: int = 4) -> tuple[int, int] | None:
    """The title lines that start at head[j]: the lines of the block to its end, cut before a date, author, label
    or status line, and continued in the next block if `_continues` says so. Returns (start, end) in Doc.text."""
    idx = _block_rest(head, j)
    keep = [idx[0]]
    for k in idx[1:]:
        fl = _fold_line(head[k].text)
        prev_words = re.findall(r"[a-z]+", _fold_line(head[keep[-1]].text))
        if YEARS_RX.fullmatch(fl) or (prev_words and prev_words[-1] in ("bis", "ab", "seit") and vb.find_dates(fl)) \
                or (head[keep[-1]].text.rstrip().endswith(("-", "\u00ad")) and head[k].text.lstrip()[:1].islower()):
            keep.append(k)                                  # "... Förderperiode" / "2016 - 2019", "... bis" / "am 1. Januar 2025"
            continue
        if (_date_only(fl) or _number_line(fl) or AUTHOR_VERB_RX.match(fl) or SALUTATION_RX.match(fl)
                or (PARTY_RX.search(fl) and (fl.startswith("von ") or re.match(
                    r"^[A-ZÄÖÜÉ][\w.'-]+ [A-ZÄÖÜÉ][\w'-]+\s*[,(]", head[k].text.strip())))
                or (SUBMIT_RX.match(fl) and vb.find_dates(fl))
                or _form_label_strict(fl) or re.match(r"^" + STATUS + r"\b", fl)):
            break
        keep.append(k)
    full_block = len(keep) == len(idx)
    for _ in range(2):
        if full_block and _continues(doc, head, keep[-1]):
            nxt = _block_rest(head, keep[-1] + 1)
            keep += nxt
        else:
            break
    first = head[keep[0]].text.strip()
    for n, k in enumerate(keep[1:], 1):                     # a block that prints its lines 2 or 3 times
        if head[k].text.strip() == first and len(first) >= 12:
            keep = keep[:n]
            break
    if len(keep) > max_lines + 1:
        return None
    return head[keep[0]].char_start, (_line_end(head[keep[0]]) if len(keep) == 1 else head[keep[-1]].char_end)


def _type_region(doc: vb.Doc, head: list[vb.Line], i: int, start: int) -> _Reg:
    """The text from `start` (after the type word of line i) to the end of the block, at most 6 lines; with the next
    block if the title continues there."""
    idx = _block_rest(head, i)
    if len(idx) > 6:
        # a block that holds the title and the body text: the title ends at the first short line (the end of a paragraph)
        width = max(len(head[k].text) for k in idx)
        short = next((n for n, k in enumerate(idx[:6]) if len(head[k].text) < 0.6 * width), 5)
        return _Reg(doc, start, head[idx[short]].char_end)
    last = idx[-1]
    for _ in range(2):
        if not _continues(doc, head, last):
            break
        last = _block_rest(head, last + 1)[-1]
    if last == i:
        return _Reg(doc, start, max(start, _line_end(head[i])))
    return _Reg(doc, start, head[last].char_end)


# ------------------------------------------------------------------ label tiers and cue line

def _value_after(doc: vb.Doc, head: list[vb.Line], i: int):
    """The first value line after a label-only line: label lines, date lines and number lines are passed
    (a form can print 2 labels and then 2 values)."""
    j, passed = i + 1, 0
    while j < len(head) and passed <= 4:
        fl = _fold_line(head[j].text)
        m = LABEL_RX.match(fl) or CUE_LINE_RX.match(fl)
        if ((m and not m.group("rest")) or _date_only(fl) or _number_line(fl) or re.match(r"^[^:]{2,40}:$", fl)
                or len(fl) <= 1 or BARE_LABEL_RX.match(fl)):
            j, passed = j + 1, passed + 1
            continue
        if AUTHOR_START_RX.match(fl) and fl.startswith(("von ", "de ", "da ", "di ", "eingereicht ")):
            b = head[j].block_index                         # "betreffend" / "von <author>" / title block
            while j < len(head) and head[j].block_index == b:
                j += 1
            passed += 1
            continue
        if m or SALUTATION_RX.match(fl) or _form_label_strict(fl):
            return None
        return j
    return None


LABEL_NO_COLON_RX = re.compile(r"^(titel|betreff|gegenstand|titre|objet|titolo|oggetto)\s+(?=\S)")
ACT_START_RX = re.compile(r"^(?:gesetz|verordnung|dekret|reglement|loi|ordonnance|decret|reglement|legge|regolamento)$")


def _stack_label(fl: str) -> bool:
    m = LABEL_RX.match(fl)
    return bool(BARE_LABEL_RX.match(fl) or (m and not m.group("rest")) or re.match(r"^[^:\d]{2,25}:$", fl))


def _bare_stack(doc: vb.Doc, head: list[vb.Line], i: int, detail: dict):
    """Tier label_stack_order. The title label at head[i] is a line of a stack of 3 or more label lines of which one or
    more have no colon ("Datum" / "Archiv" / "Thema" / "Beschluss-Nr."), and the value blocks stand below the stack in
    the order of the labels. Returns None if the line is in no such stack, else a tuple (result or None,)."""
    p = q = 0
    while i - p - 1 >= 0 and _stack_label(_fold_line(head[i - p - 1].text)):
        p += 1
    while i + q + 1 < len(head) and _stack_label(_fold_line(head[i + q + 1].text)):
        q += 1
    around = [_fold_line(head[k].text) for k in range(i - p, i + q + 1) if k != i]
    if p + q < 2 or not any(BARE_LABEL_RX.match(x) for x in around):
        return None
    blocks, k = [], i + q + 1
    while k < len(head) and len(blocks) < p + q + 1:
        if _label(doc, head[k]) in HEADING_LABELS + ("table", "list_item") or STRUCT_RX.match(_fold_line(head[k].text)):
            break
        blocks.append(k)
        k = _block_rest(head, k)[-1] + 1
    if len(blocks) < p + q + 1:
        return (None,)                                      # the order of the values is not known
    v = blocks[p]
    fv = _fold_line(head[v].text)
    det = dict(detail, stack=p + q + 1, place=p + 1)
    if _date_only(fv) or _number_line(fv) or _letterhead(fv):
        return (None,)
    if TYPE_LINE_RX.match(fv):
        r = _try_type(doc, head, v)[0]
        return ((r[0], r[1], "label_stack_order", dict(det, form=r[2])) if r else None,)
    run = _run_from(doc, head, v)
    if run is None:
        return (None,)
    reg = _Reg(doc, *run)
    return (_result(reg, 0, len(reg.t), "label_stack_order", _label(doc, head[v]), det),)


def _affair_cell(doc: vb.Doc, head: list[vb.Line], i: int, s0: int, cell: str, lab: str):
    """Tier label_affair_cell: the value cell of a table row with a label that names the affair (Geschäft, Vorlage,
    Affaire, Atto). The cell can also print the type and the author after the title (" - <type word> ..."): that
    part is cut."""
    reg = _Reg(doc, s0, s0 + len(cell))
    t = reg.t
    if TYPE_LINE_RX.match(t.strip()) or len(re.findall(r"[a-z]{3,}", t)) < 2:
        return None
    b = len(t)
    for m in re.finditer(r"\s[-\u2013]\s", t):
        if m.start() > 8 and re.search(r"motion|postulat|interpellation|anfrage|initiative|petition|question|mozione|"
                                       r"interrogazione|interpellanza|vorstoss", t[m.end():m.end() + 70]):
            b = m.start()
            break
    return _result(reg, 0, b, "label_affair_cell", "table", {"cue": lab})


def _try_label(doc: vb.Doc, head: list[vb.Line], i: int, tier_label: str = "label_cue", tier_cue: str = "cue_line"):
    ln = head[i]
    label = _label(doc, ln)
    raw = ln.text
    detail: dict = {}
    if "\t" in raw:                                         # a row of a table: label cell, value cell
        cells = raw.split("\t")
        lab0 = _fold_line(cells[0]).strip(" :")
        if not cells[1].strip():
            return None
        if re.fullmatch(AFFAIR_LABEL_WORDS, lab0) and len(cells) == 2 and i < 20:
            return _affair_cell(doc, head, i, ln.char_start + len(cells[0]) + 1, cells[1], lab0)
        if not re.fullmatch(LABEL_WORDS, lab0):
            return None
        s0 = ln.char_start + len(cells[0]) + 1
        cell = cells[1]
        sal = re.search(r"\s(?:Monsieur le|Madame la|Mesdames|Messieurs|Sehr geehrte|Geschätzte|Egregi|Gentil|Onorevol)", cell)
        if sal and sal.start() >= 8:
            cell = cell[:sal.start()]                       # the cell holds the title and the start of the letter
        reg = _Reg(doc, s0, s0 + len(cell))
        return _result(reg, 0, len(reg.t), tier_label, label, {"cue": _fold_line(cells[0])}, cut=False)
    if label == "table":
        return None
    f = vb.fold_map(raw, base=ln.char_start, keep_newlines=False)
    t = f.text
    lead = len(t) - len(t.lstrip())
    m = LABEL_RX.match(t.strip())
    tier = tier_label
    mn = LABEL_NO_COLON_RX.match(t.strip()) if not m and tier_label == "label_cue" and ln.index_in_block == 0 else None
    if mn and len(_block_rest(head, i)) <= 3:
        # "Titre Pour une transparence accrue ..." in a form: 3 or more label lines with a colon stand in the head, and
        # the line after the block is a label line or a heading
        p0 = mn.end() + lead
        s0 = f.span(p0, p0 + 1)[0]
        nxt_k = _block_rest(head, i)[-1] + 1
        nxt_f = _fold_line(head[nxt_k].text) if nxt_k < len(head) else ""
        n_form = sum(1 for x in head if re.match(r"^[^:\"]{2,45} ?:(?:\s|$)", _fold_line(x.text)))
        if doc.text[s0:s0 + 1].isupper() and n_form >= 3 and nxt_k < len(head) and (
                re.match(r"^[^:\"]{2,45} ?:(?:\s|$)", nxt_f) or _label(doc, head[nxt_k]) in HEADING_LABELS):
            reg = _Reg(doc, s0, head[nxt_k - 1].char_end)
            return _result(reg, 0, len(reg.t), "label_no_colon", label, {"cue": mn.group(1), "closed_by": "label"}, cut=False)
    if not m:
        m = CUE_LINE_RX.match(t.strip())
        tier = tier_cue
        n_block = len(doc.blocks[ln.block_index].lines)
        if not m:
            kind_start = bool(re.match(r"\s*(?:" + DECISION_KIND + r"|" + KIND + r")\b", t))
            mid = MID_CUE_RX.search(t) if (i < 15 and ln.index_in_block == 0 and n_block <= (5 if kind_start else 3)
                                           and not TYPE_ANY_RX.search(t)) else None
            if not mid or VERB_RX.search(t[:mid.start()]) or tier_cue == "-":
                return None
            run = _run_from(doc, head, i, max_lines=5)
            if ACT_START_RX.match(t[:mid.start()].strip()):
                # the title of an act: "Gesetz betreffend die Änderung des Gesetzes über ..." is one title
                if run is None:
                    return None
                reg = _Reg(doc, ln.char_start, run[1])
                return _result(reg, 0, len(reg.t), "act_title_line", label, {"cue": mid.group(0).strip()}, cut=False)
            reg = _Reg(doc, f.span(mid.end(), mid.end() + 1)[0], run[1] if run else ln.char_end)
            return _result(reg, 0, len(reg.t), "cue_in_line", label, {"cue": mid.group(0).strip()})
        prev = _fold_line(head[i - 1].text) if i and head[i - 1].block_index == ln.block_index else ""
        below_head = bool(prev) and bool(TYPE_LINE_RX.match(prev) or KIND_ONLY_RX.match(prev) or STACK_LABEL_RX.match(prev))
        if not (ln.index_in_block == 0 or label in HEADING_LABELS or n_block <= 4 or (below_head and n_block <= 12)):
            return None
    detail = {"cue": (m.groupdict().get("label") or m.groupdict().get("cue"))}
    stack, k = 0, i - 1                                     # "von" / "betreffend" / <author> / <title>
    while k >= 0 and head[k].block_index == ln.block_index and STACK_LABEL_RX.match(_fold_line(head[k].text)):
        stack, k = stack + 1, k - 1
    rest = m.group("rest") or ""
    if rest.strip(" ☐☒□:") and re.search(r"[a-z]{2,}", rest):
        p = m.start("rest") + lead
        s0 = f.span(p, p + 1)[0]
        run = _run_from(doc, head, i)
        reg = _Reg(doc, s0, run[1] if run else ln.char_end)
        return _result(reg, 0, len(reg.t), tier, label, dict(detail, same_line=True) if tier == tier_label else detail)
    if tier == tier_label:
        st = _bare_stack(doc, head, i, detail)
        if st is not None:
            return st[0]
    j = _value_after(doc, head, i)
    if j is None:
        return None
    def _colon_label(k: int) -> bool:
        x = _fold_line(head[k].text)
        if not re.match(r"^[^:]{1,25}:$", x):
            return False
        prev_w = re.findall(r"[a-z']+", _fold_line(head[k - 1].text)) if k else []
        return not TYPE_LINE_RX.match(x) or (bool(prev_w) and prev_w[-1] in STOP_END)   # "Auteur/e de la" / "motion :"

    if sum(1 for k in (i - 1, i - 2, i - 3) if k >= 0 and _colon_label(k)) >= 2 and not stack:
        # a stack of labels and then a stack of values: the last label has the last value block
        blocks, k = [], j
        while k < len(head) and len(blocks) < 4:
            fk = _fold_line(head[k].text)
            if (re.match(r"^[^:]{1,40}:", fk) and _form_label_strict(fk)) or LABEL_RX.match(fk) or SALUTATION_RX.match(fk) \
                    or _structural(fk) or _label(doc, head[k]) in HEADING_LABELS + ("table", "list_item"):
                break
            blocks.append(k)
            k = _block_rest(head, k)[-1] + 1
        if len(blocks) == 3 and len(_block_rest(head, blocks[-1])) > 3:
            blocks = blocks[:2]                             # the third block is body text
        if len(blocks) < 2 or len(blocks) > 3 or len(_block_rest(head, blocks[-1])) > 3:
            return None                                     # the order of the values is not known
        run = _run_from(doc, head, blocks[-1])
        if run is None or _author_line(_fold_line(head[blocks[-1]].text), head[blocks[-1]].text):
            return None
        reg = _Reg(doc, *run)
        return _result(reg, 0, len(reg.t), "label_stack_last", _label(doc, head[blocks[-1]]), detail)
    if stack:                                               # the values stand in the order of the labels
        if j + stack >= len(head) or head[j + stack].block_index != head[j].block_index:
            return None
        j += stack
    run = _run_from(doc, head, j)
    if run is None:
        return None
    reg = _Reg(doc, *run)
    if TYPE_LINE_RX.match(_fold_line(head[j].text)):
        return _try_type(doc, head, j)[0]
    if _letterhead(_fold_line(head[j].text)) or _author_line(_fold_line(head[j].text), head[j].text):
        return None
    return _result(reg, 0, len(reg.t), tier, _label(doc, head[j]), detail)


# ------------------------------------------------------------------ type word and document kind tiers

def _before_type(doc: vb.Doc, head: list[vb.Line], i: int):
    """Tier before_type_line: the lines of the block before a line "type word + author" (the head block of a minute:
    title line / "Postulat <name>" / "Beantwortung"). The block starts at most 3 lines before the type line."""
    ln = head[i]
    idx = [k for k in range(max(0, i - 3), i) if head[k].block_index == ln.block_index]
    if not idx or (idx[0] > 0 and head[idx[0] - 1].block_index == ln.block_index):
        return None
    for k in idx:
        fl = _fold_line(head[k].text)
        if (_date_only(fl) or _number_line(fl) or _letterhead(fl) or _form_label(fl) or TYPE_LINE_RX.match(fl)
                or _author_line(fl, head[k].text) or SALUTATION_RX.match(fl) or KIND_ONLY_RX.match(fl)
                or HEAD_KIND_RX.match(fl) or _structural(fl)):
            return None
    reg = _Reg(doc, head[idx[0]].char_start, head[idx[-1]].char_end)
    return _result(reg, 0, len(reg.t), "before_type_line", _label(doc, ln), {"type_line": ln.text[:60]}, cut=False)


STACK_LABEL_RX = re.compile(r"^(?:von|eingereicht von|de|da|par)\s*:?$")
PRESENTED_RX = re.compile(r"^presentata nella forma (?:generica|elaborata) (?P<by>da|dal|dalla|dai|dagli|dalle|dall')\s")


def _presented(doc: vb.Doc, head: list[vb.Line], j: int):
    """Tier type_presented: the Italian form "presentata nella forma generica|elaborata da <author> ..." below a line
    that holds only a type word. The title is the text in quotation marks at the end of the block, or the text after
    the first "per" or "a favore" that is no group name ("per il Gruppo PLR", "per MPS-POP-Indipendenti")."""
    idx = _block_rest(head, j)
    if len(idx) > 6:
        return None
    reg = _Reg(doc, head[j].char_start, head[idx[-1]].char_end)
    t = reg.t
    m = PRESENTED_RX.match(t)
    if not m or m.group("by") != "da":
        return None
    label = _label(doc, head[j])
    q1 = t.find('"', m.end())
    if 0 <= q1 - m.end() <= 90 and t.rstrip().endswith('"') and t.count('"', q1) == 2:
        return _result(reg, q1 + 1, len(t.rstrip()) - 1, "type_presented", label, {"form": "quoted"}, cut=False)
    for c in re.finditer(r"\s(per|a favore)\s+", t):
        if c.start() < m.end():
            continue
        s0 = reg.span(c.end(), c.end() + 1)[0]
        if c.group(1) == "per" and (doc.text[s0:s0 + 1].isupper() or re.match(r"il\s+gruppo|i\s+gruppi", t[c.end():])):
            continue                                        # the group of the author
        art = re.match(r"(?:la|il|lo|le|gli|i)\s+|l'", t[c.end():]) if c.group(1) == "per" else None
        start = c.end() + art.end() if art else c.start(1)
        return _result(reg, start, len(t), "type_presented", label, {"form": c.group(1)}, cut=False)
    return None


DATE_TAIL_RX = re.compile(r"\s+(?:vom|du|del|dell')\s+(?:\d{1,2}\.?(?:er)?\s+[A-Za-zäöüéèû]{3,10}\.?\s+\d{4}|"
                          r"\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4})\s*$")


def _author_pre(pre: str, raw_pre: str) -> bool:
    """True if the text between the type word and a colon is a number or an author, not a part of the title."""
    p = pre
    m = NUM_RX.match(p)
    if m:
        p = p[m.end():]
    p = p.strip(" \n,;/-")
    if not p:
        return True
    p = DATE_TAIL_RX.sub("", p).strip(" \n,;/-")              # "... (Urs Frieden, GB) vom 3. Juli 2008"
    raw_pre = DATE_TAIL_RX.sub("", raw_pre.strip()).strip()
    if not p:
        return True
    if PARTY_RX.search(p) or re.search(r"\bvon\b|\bde m\.|\bdu groupe\b|\bdel\b", p) or re.match(ROLE + r"\b", p):
        return True
    if re.match(r"(?:de |d'|di |della |dell')(?:mme|mmes|mm\.|m\.|madame|monsieur|on\.|signor\w*)(?![\w])", p):
        return True                                          # "Postulat de Mme X et Mme Y du 30.03.2023 : ..."
    if re.search(r"\([A-ZÄÖÜÉ][^()]{3,90},\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöü!/+ ]{0,13}\)$", raw_pre, re.S):
        return True                                          # "Kommission ... (Urs Frieden, GB)": name and party mark
    if (ADDRESSEE_RX.match(p) and len(p.split()) <= 5) or re.match(r"(?:gemass|gem\.?|nach|selon|ai sensi) .*(?:§|\bart\b)", p):
        return True                                          # "Anfrage an den Stadtrat: ...", "gemäss Art. 47 ...: ..."
    if re.fullmatch(r"(?:[\w.'-]+ ){1,3}\([^)]{1,25}\)(?: ?(?:,|und|et|e) (?:[\w.'-]+ ){1,3}\([^)]{1,25}\)){0,5}"
                    r"(?: (?:und|et|e) (?:mit\w+|consorts|cofirmatari))?", p.replace("\n", " ")):
        return True                                          # "Benita Leitner (Pro Aarau) und Samir Hertig (Pro Aarau): ..."
    raw = re.sub(r"^\W*(?:Nr\.?|No\.?|N°)?\s*[\w./-]*\d[\w./-]*\s*", "", raw_pre.strip())
    words = raw.replace(",", " ").split()
    if 1 <= len(words) <= 3 and all(re.fullmatch(r"[A-ZÄÖÜÉÈ][a-zäöüéèàç'.-]+", w) for w in words):
        return not any(NOUN_SUFFIX_RX.search(vb.fold(w)) or len(w) > 13 for w in words)
    return False


ADDR_CUE_RX = re.compile(r"^\s*(?:an|ans)\s(?:den|die|das)\s[a-z-]+(?:\s[a-z-]+)?\s+(?:zu|zur|zum|uber|betreffend|betr\.?)\s+")


def _type_text(doc: vb.Doc, head: list[vb.Line], i: int, reg: _Reg, label: str, type_word: str):
    """Tiers 3 to 6 on the text after the type word (reg). Returns a result, the word "only" (the text is no
    title: go on with the lines after it) or None."""
    t = reg.t
    detail = {"type_word": type_word}
    # tier 3: quotation marks around the full title
    q1 = t.find('"')
    pre_cue = CUE_START_RX.match(t[:max(q1, 0)]) or CUE_RX.search(t[:max(q1, 0)])
    partial = bool(pre_cue and re.search(r"[a-z]{3,}", t[pre_cue.end():q1]))
    if q1 > 0 and not pre_cue and not partial:
        pre = NUM_RX.sub("", t[:q1], count=1) if NUM_RX.match(t[:q1]) else t[:q1]
        pre = pre.strip(" \n:-,;")
        s_pre = reg.span(0, max(q1, 1))
        if len(re.findall(r"[a-z]{3,}", pre)) >= 2 and not _author_pre(pre, doc.text[s_pre[0]:s_pre[1]]) \
                and not _author_line(pre, doc.text[s_pre[0]:s_pre[1]]) and not AUTHOR_START_RX.match(pre):
            partial = True                                  # "Postulat - Ausbau Angebot «Nextbike»"
    if 0 <= q1 <= 220 and not partial and len(re.findall(r"[a-z0-9]+", t[:q1])) <= 30 and "?" not in t[:q1]:
        q2 = t.find('"', q1 + 1)
        if q2 > q1 + 3:
            rest = t[q2 + 1:]
            ok = not rest.strip() or re.match(r"\s*[,;:.)/\n-]", rest) is not None \
                or re.fullmatch(r"\s*\([^()]{2,30}\)\s*", rest) is not None       # '"<title>" (12/MO 21/158)'
            if not ok:
                cut = _cut_tail(reg, q1, len(t))
                ok = cut <= q2 + 1 + (len(rest) - len(rest.lstrip()))
            if not ok and re.match(r"\s*(?:eingereicht|ein\b|wurde|wird|depose|presentat)", rest):
                ok = True
            if not ok and len(re.findall(r"[a-z0-9]+", t[q1 + 1:q2])) >= 2 \
                    and re.match(r"\s*(?:von|der|des|du|de la|del|della|di|dei)\s", rest):
                ok = True
            if ok and len(re.findall(r"[a-z]{3,}", t[q1 + 1:q2])) >= 1:
                r = _result(reg, q1 + 1, q2, "type_quoted", label,
                            dict(detail, quote_first=not t[:q1].strip()) if not t[:q1].strip() else detail, cut=False)
                if r:
                    return r
    # tier 4: cue word
    m = CUE_START_RX.match(t) or AUTHOR_CUE_RX.match(t) or ADDR_CUE_RX.match(t)
    colon0 = re.search(r":(?=\s)", t[:220])
    cue0 = CUE_RX.search(t, 0, 240)
    colon_first = bool(not m and colon0 and cue0 and colon0.start() < cue0.start()
                       and len(re.findall(r"[a-z]{3,}", t[colon0.end():cue0.start()])) >= 2
                       and _author_pre(t[:colon0.start()], doc.text[slice(*reg.span(0, max(colon0.start(), 1)))]))
    if not m and not colon_first:
        # author and place, then "zu": "Motion Céline Huber, Altdorf, zu Schaffung einer Rechtsgrundlage"
        m2 = re.match(r"^\s*[^\n\":;]{3,60}?,\s+(?P<c>zu|zur|zum|uber|fur|pour|per)\s+", t)
        if m2:
            pre = t[:m2.end()].rsplit(",", 1)[0]
            sp = reg.span(0, max(len(pre), 1))
            if _author_pre(pre, doc.text[sp[0]:sp[1]]):
                if m2.group("c") in ("fur", "pour", "per"):     # the word is a part of the title
                    r = _result(reg, m2.start("c"), len(t), "type_cue", label, dict(detail, cue="author, " + m2.group("c")))
                    if r:
                        return r
                else:
                    m = m2
    if not m and not colon_first:
        m = CUE_RX.search(t, 0, 240)
        if m and VERB_RX.search(t[:m.start()]):
            m = None
    if m:
        detail = dict(detail, cue=m.group(0).strip(" :\n"))
        r = _result(reg, m.end(), len(t), "type_cue", label, detail)
        if r:
            return r
    # tier 5: colon or dash
    m = re.search(r":(?=\s|$)", t[:220])
    if m and re.match(r"\s*(?:" + STATUS + r")\b", t[m.end():]):
        m = None                                            # "Postulat SP ein Kronenplatz für alle: Überweisung"
    if m:
        s0, e0 = reg.span(0, max(m.start(), 1))
        s1 = reg.span(m.end(), m.end() + 1)[0] if m.end() < len(t) else reg.end
        after = doc.text[s1:reg.end].strip().replace("\n", " ")
        names = [x for x in re.split(r",\s+|\s+(?:und|et|e)\s+", after) if x]
        if len(names) >= 2 and all(re.fullmatch(r"(?:[A-ZÄÖÜÉÈ][\w'-]+ ){1,3}[A-ZÄÖÜÉÈ][\w'-]+", x) for x in names) \
                and re.search(r"(?:mitunterzeichn\w*|cosignataires|cofirmatari\w*)\s*$", t[:m.start()]):
            return "only"                                   # "... und den weiteren Mitunterzeichnern:" + a list of names
        if _author_pre(t[:m.start()], doc.text[s0:e0] if m.start() else ""):
            r = _result(reg, m.end(), len(t), "type_colon", label, detail)
            if r:
                return r
            if m.start() > 2:
                return None                                 # author and colon, but the text after the colon is no title
    m = re.match(r"^(?:" + NUM_RX.pattern + r")?\s*(?:\([a-z ]{3,20}\)|,\s(?:evtl\.?|eventuell)\smit\srichtliniencharakter)?"
                 r"\s*[-\u2013]\s+", t)
    if m:
        r = _result(reg, m.end(), len(t), "type_colon", label, detail)
        if r:
            return r
    # tier 6: plain
    a = 0
    m = NUM_RX.match(t)
    if m:
        a = m.end()
    while a < len(t) and t[a] in " \n,;/":
        a += 1
    s0, _ = reg.span(a, a + 1) if a < len(t) else (reg.end, reg.end)
    raw = doc.text[s0:reg.end]
    m = re.match(r"((?:(?:[A-ZÄÖÜÉÈ][\w.'-]+\s+){1,3}\(([^)\n]{1,25})\)\s*(?:,|und|et|e)?\s*){1,6})"
                 r"(?:und\s+Mit\w+|et\s+consorts|e\s+cofirmatari)?\s*[,:]?\s+(?=[A-ZÄÖÜÉÈ\"«„“])", raw)
    if m and (m.group(0).rstrip().endswith((",", ":")) or m.group(0).count("(") >= 2):
        off = next((k for k in range(a, len(t)) if reg.f.index[k] + reg.start >= s0 + m.end()), len(t))
        r = _result(reg, off, len(t), "type_plain", label, dict(detail, form="author_then_title"))
        if r:
            return r
    b = _cut_tail(reg, a, len(t))
    body = t[a:b].strip()
    raw_body = doc.text[slice(*reg.span(a, b))] if b > a else ""
    if not body or _date_only(body):
        return "only"
    # party marks before the title: "Motion 1a Grüne, Grünliberale, Städtische Gebäude als Kraftwerke"
    lead = re.match(r"(?:[\w.'/ -]{1,22},\s+){1,5}", body)
    if lead:
        segs = [x for x in re.split(r",\s+", lead.group(0)) if x]
        segs_raw = [x for x in re.split(r",\s+", raw_body.strip()[:len(lead.group(0))]) if x]
        n_party = 0
        for x, y in zip(segs, segs_raw):
            if not _party_mark(x, y) or len(x.split()) > 3:
                break
            n_party += 1
        skip = sum(len(x) for x in re.findall(r"[^,]*,\s+", body)[:n_party])
        rest_words = len(re.findall(r"[a-z]{3,}", body[skip:]))
        if n_party and rest_words >= 2 and not _author_line(body[skip:], raw_body.strip()[skip:]):
            off = a + (len(t[a:b]) - len(t[a:b].lstrip())) + skip
            return _result(reg, off, b, "type_plain", label, dict(detail, form="parties_then_title"), cut=False)
    lead_p = re.match(r"(?:(?:[A-ZÄÖÜ]{2,5}|Grüne|GRÜNE|Mitte|Die Mitte|Grünliberale)(?:\s*[,/+]\s*|\s+(?:und|et)\s+|\s+))+"
                      r"(?=[a-zäöüA-ZÄÖÜ\"«])", raw_body.lstrip())
    if lead_p and all(_party_mark(vb.fold(x), x) for x in re.split(r"\s*[,/+]\s*|\s+(?:und|et)\s+|\s+", lead_p.group(0).strip())
                      if x) and len(re.findall(r"[a-z]{3,}", vb.fold(raw_body.lstrip()[lead_p.end():]))) >= 2:
        rest_raw = raw_body.lstrip()[lead_p.end():]
        if not _author_line(vb.fold(rest_raw), rest_raw):
            abs_pos = reg.span(a, b)[0] + (len(raw_body) - len(raw_body.lstrip())) + lead_p.end()
            off = next((k for k in range(a, b) if reg.f.index[k] + reg.start >= abs_pos), b)
            return _result(reg, off, b, "type_plain", label, dict(detail, form="parties_then_title"), cut=False)
    if _author_line(body, raw_body):
        return "only"
    if re.match(r"^(?:" + STATUS + r"|" + KIND + r")\b", body):
        return "only"                                       # "Parlamentarischer Vorstoss. Antwort des Regierungsrates"
    line0 = raw.strip().split("\n")[0]
    if "\n" not in body and (re.fullmatch(r"(?:[A-ZÄÖÜÉÈ][a-zäöüéèàç'.-]+\s+){1,3}\([^)]*\)", line0) or re.fullmatch(
            r"[A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+ [A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+(?:(?:, | und | et | e )[A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+ "
            r"[A-ZÄÖÜÉÈ][a-zäöüéèàç'-]+)+", line0)):
        return "only"                                       # a name with a note in brackets, or a list of names
    if re.fullmatch(r"(?:" + TYPE + r"[\s,/]*)+", body):
        return None                                         # only type words (a form)
    first = raw[:1]
    w0 = re.match(r"[a-z']+", body)
    lower_ok = label in HEADING_LABELS and bool(w0) and len(w0.group(0)) >= 6 and not PLAIN_LOWER_NO.match(body)
    if not (first.isupper() or first.isdigit() or first in "\"«„“" or PLAIN_LOWER_OK.match(body) or lower_ok):
        return None
    if label not in HEADING_LABELS and ((len(_block_rest(head, i)) > 3 and not (b < len(t.rstrip()) and len(_block_rest(head, i)) <= 6))
                                        or VERB_RX.search(body)):
        return None                                         # (a long block is read only if an author list is cut from it)
    if ":" in body and len(body) < 40 and all(w in YES_NO for w in re.findall(r"[a-z]+", body.split(":")[-1])):
        return None
    n_body = len(re.findall(r"[a-z0-9']+", body))
    name_word = r"[A-ZÄÖÜÉÈ][a-zäöüéèàç'-]{1,14}"
    if n_body == 1:
        # one word after the type word ("Motion Romano", "Postulat Tannenrain"): the title can stand below it
        return "short", _result(reg, a, b, "type_plain_short", label, detail, cut=False)
    if "\n" not in body.strip() and re.fullmatch(name_word + r"(?: (?:von |van |de |di |del )?" + name_word + r"){1,2}",
                                                 raw_body.strip()) \
            and not any(NOUN_SUFFIX_RX.search(w) for w in body.split()):
        # 2 or 3 name-like words ("Interpellation Hans Baumann"): the title can stand on the lines before in the block
        r = _before_type(doc, head, i)
        if r:
            return r
        return "short", _result(reg, a, b, "type_plain_short", label, detail, cut=False)
    return _result(reg, a, b, "type_plain", label, detail, cut=False)


SIGN_TABLE_RX = re.compile(r"\b(?:unterschrift|signature|firma|vorname|prenom|sitzplatz|partei|parti|partito)\b")
STAMP_RX = re.compile(r"(?:eingang|eingegangen|eingereicht|recu|ricevuto)(?: [a-z]{1,12}){0,2}")


def _after(doc: vb.Doc, head: list[vb.Line], i: int, kind: bool):
    """Tiers 7 to 10: the title block after a line that holds only a type word (or only a document kind)."""
    first_block = head[i].block_index
    j, passed = i + 1, 0
    while j < len(head) and passed <= 6:
        x = head[j]
        fl = _fold_line(x.text)
        label = _label(doc, x)
        if label == "table":
            if SIGN_TABLE_RX.search(fl) and passed <= 4:       # a table of the signers: the title can stand below it
                j, passed = _block_rest(head, j)[-1] + 1, passed + 1
                continue
            return None
        if PRESENTED_RX.match(fl):
            return _presented(doc, head, j)
        if x.block_index == first_block and head[j - 1].text.rstrip().endswith(("-", "\u00ad")):
            return None                                     # the author goes on: "... und weitere Mitunter-" / "zeichnende ..."
        if fl.startswith("(") and ")" not in fl:            # a note in brackets that ends on one of the next 2 lines
            close = next((q for q in (j + 1, j + 2) if q < len(head) and head[q].block_index == x.block_index
                          and _fold_line(head[q].text).endswith(")") and "(" not in head[q].text), None)
            if close is not None:
                j, passed = close + 1, passed + 1
                continue
        if re.fullmatch(r"(?:de|von|di|da|par|des|d')\s*(?:(?:MM?\.|Mme|Herrn?|Frau)\s+)?[A-ZÄÖÜÉÈ][\w'-]+(?: [A-ZÄÖÜÉÈ][\w'-]+){1,2}"
                        r"(?:(?:, | et | und | e )[A-ZÄÖÜÉÈ][\w'-]+(?: [A-ZÄÖÜÉÈ][\w'-]+){1,2}){0,4}", x.text.strip()):
            j, passed = j + 1, passed + 1                   # "de Samuel Amos et Olivier Moser"
            continue
        if label.startswith("checkbox") or (TYPE_ANY_RX.search(fl) and len(re.findall(r"[a-z]+", fl)) <= 3
                                            and not TYPE_LINE_RX.match(fl)):
            j, passed = j + 1, passed + 1                   # a check box line of a form, or a short line with a type word
            continue
        r = _try_label(doc, head, j, tier_cue="after_kind_cue" if kind else "type_cue")
        if r:
            return r
        if LABEL_RX.match(fl) or CUE_LINE_RX.match(fl):
            return None
        if head[j - 1].text.rstrip().endswith(("-", "\u00ad")) and x.text.lstrip()[:1].islower() and x.index_in_block == 0 \
                and len(_block_rest(head, j)) == 1:
            j, passed = j + 1, passed + 1                   # "... vom 14. Sep-" / "tember 2011": the rest of a split block
            continue
        mc = re.match(r"^([^:\"]{3,60}):\s+(?=\S)", fl) if not kind else None
        if mc and mc.group(1).rstrip().endswith(")") and _author_line(mc.group(1), x.text[:len(mc.group(1))]) \
                and not AUTHOR_START_RX.match(fl):
            # "Beantwortung einer Anfrage" / 'Urs Winzenried (SVP): "Sanierung/Neugestaltung der Tellistrasse"'
            run = _run_from(doc, head, j, max_lines=3)
            if run is not None:
                f2 = vb.fold_map(x.text, base=x.char_start, keep_newlines=False)
                lead2 = len(f2.text) - len(f2.text.lstrip())
                p2 = mc.end() + lead2
                if p2 < len(f2.text):
                    reg = _Reg(doc, f2.span(p2, p2 + 1)[0], run[1])
                    mq2 = re.match(r'\s*(?:' + TYPE + r')?\s*"([^"]{3,300})"', reg.t)
                    if mq2:
                        r = _result(reg, mq2.start(1), mq2.end(1), "type_quoted", label, {"after_line": head[i].text[:60], "form": "author_colon"}, cut=False)
                        if r:
                            return r
                    r = _result(reg, 0, len(reg.t), "type_colon", label, {"after_line": head[i].text[:60], "form": "author_colon"})
                    if r:
                        return r
        if STAMP_RX.fullmatch(fl) or (re.fullmatch(r"[\dA-Z ./-]{3,24}", x.text.strip()) and re.search(r"\d", x.text)):
            j, passed = j + 1, passed + 1                   # a stamp ("EINGANG GR") or a code line ("12 EA IF 276")
            continue
        m = TYPE_LINE_RX.match(fl)
        if m:
            if _type_only_rest(fl[m.end():], x.text):
                j, passed = j + 1, passed + 1
                continue
            return None                                     # the main loop reads this line as a type line
        if KIND_ONLY_RX.match(fl):
            j, passed = j + 1, passed + 1
            continue
        same_block_text = x.block_index == first_block and label not in HEADING_LABELS
        hits = vb.find_dates(fl)                            # "20 settembre 2023 DIPARTIMENTO DELLE FINANZE ..."
        fl_org = (fl[:hits[0].start] + fl[hits[0].end:]).strip() if len(hits) == 1 else fl
        if fl in ("numero", "data", "competenza", "nummer", "datum", "date", "numero data competenza") \
                or (fl_org != fl and fl_org and (_letterhead(fl_org) or _org_line(fl_org))):
            j, passed = j + 1, passed + (0 if fl in ("numero", "data", "competenza") else 1)
            continue
        if (_date_only(fl) or _number_line(fl) or _author_line(fl, x.text)
                or (ADDRESSEE_RX.match(fl) and len(fl.split()) <= 8)
                or (fl.startswith("(") and fl.endswith(")")) or (SUBMIT_RX.match(fl) and vb.find_dates(fl))
                or _letterhead(fl) or _org_line(fl) or len(fl) <= 2
                or (same_block_text and _name_like(x.text.strip()))):
            j, passed = j + 1, passed + 1
            continue
        if (re.match(r"^" + STATUS + r"\b", fl) or HEAD_KIND_RX.match(fl)) and len(re.findall(r"[a-z]+", fl)) <= 6 \
                and not CUE_RX.search(fl):
            j, passed = j + 1, passed + 1
            continue
        heading = label in HEADING_LABELS
        if label == "list_item" or x.text.lstrip()[:1] in "•·\uf0b7\uf0a7▪■":
            return None                                     # a list item is no title
        segs = [q for q in re.split(r",\s+|\s+(?:und|et|e)\s+", x.text.strip()) if q]
        if len(segs) >= 2 and all(re.fullmatch(r"[A-ZÄÖÜÉÈ][\w'-]+(?: [A-ZÄÖÜÉÈ][\w'-]+){1,3}", q) for q in segs) \
                and not heading:
            j, passed = j + 1, passed + 1                   # a list of names
            continue
        if SALUTATION_RX.match(fl) or ADDRESS_RX.match(fl) or (_form_label_strict(fl) and not heading) or _structural(fl):
            return None
        cue0 = CUE_RX.match(fl) if kind else None
        if cue0:                                            # "Rapport du Conseil communal" / "relatif à la constitution ..."
            run = _run_from(doc, head, j, max_lines=6)
            if run is None:
                return None
            reg = _Reg(doc, *run)
            c = CUE_RX.match(reg.t)
            return _result(reg, c.end() if c else 0, len(reg.t), "after_kind_cue", label, {"after_line": head[i].text[:60]})
        run = _run_from(doc, head, j, max_lines=4 if heading else 3)
        if run is None:
            return None
        if kind and not heading:
            nxt = next((_fold_line(y.text) for y in head[j + 1:] if y.char_start >= run[1]), "")
            if not (SALUTATION_RX.match(nxt) or _structural(nxt)) or doc.text[run[0]:run[1]].count("\n") > 2:
                return None
        reg = _Reg(doc, *run)
        tier = ("after_kind_heading" if heading else "after_kind_text") if kind else \
            ("after_type_heading" if heading else "after_type_text")
        mq = SENT_TITLE_RX.search(reg.t)
        if mq and TYPE_ANY_RX.search(reg.t, 0, mq.start()):  # "... A L'INTERPELLATION NO 21-610 ... INTITULEE « ... »"
            r = _result(reg, mq.start(1), mq.end(1), "type_quoted", label, {"cue": mq.group(0)[:20]}, cut=False)
            if r:
                return r
        c = CUE_START_RX.match(reg.t) or CUE_RX.match(reg.t)
        det = {"after_line": head[i].text[:60]}
        nxt2 = next((_fold_line(y.text) for y in head[j + 1:] if y.char_start >= run[1]), "")
        if not heading and not kind and SALUTATION_RX.match(nxt2) and reg.t.count("\n") <= 2:
            det["closed_by"] = "salutation"                 # the subject block of a letter can end with a full stop
        r = _result(reg, c.end() if c else 0, len(reg.t), tier, label, det)
        if r is None and not heading and len(re.findall(r"[a-z0-9]+", fl)) <= 2 and x.block_index != first_block:
            j, passed = j + 1, passed + 1                   # a short line that is no title (a logo word)
            continue
        return r
    return None


def _try_type(doc: vb.Doc, head: list[vb.Line], i: int):
    ln = head[i]
    label = _label(doc, ln)
    line_text, cell_end = ln.text, None
    if label == "table":
        # a head table with 2 cells: the type line and the affair number ("Schriftliche Anfrage betreffend ...<tab>19.5415.01")
        cells = ln.text.split("\t")
        if not (i < 8 and len(cells) == 2 and re.fullmatch(r"[\d./ -]{4,16}", cells[1].strip()) and cells[0].strip()):
            return None, False
        line_text, cell_end, label = cells[0], ln.char_start + len(cells[0].rstrip()), "text"
    elif label in NO_TYPE_LABELS and label != "list_item":
        return None, False
    if i and head[i - 1].block_index == ln.block_index and head[i - 1].text.rstrip().endswith(("-", "\u00ad")):
        return None, False                                  # "Volks-" / "initiative zur ...": no type line
    if i and head[i - 1].block_index == ln.block_index and label not in HEADING_LABELS \
            and len(doc.blocks[ln.block_index].lines) >= 4 and len(head[i - 1].text) > 60:
        return None, False                                  # a line in the middle of a paragraph
    f = vb.fold_map(line_text, base=ln.char_start, keep_newlines=False)
    t = f.text
    lead = len(t) - len(t.lstrip())
    fl = _fold_line(line_text)
    spaced = fl != t.strip()                                # a letter-spaced word: "R I S P O S T A"
    m = TYPE_LINE_RX.match(fl)
    early = i < AFTER_LINES
    if not m:
        if KIND_ONLY_RX.match(fl) and not CUE_RX.search(fl) and early and label != "list_item":
            nx = head[i + 1] if i + 1 < len(head) and head[i + 1].block_index == ln.block_index else None
            if nx is not None and len(fl.split()) > 3 and not spaced:
                # "Bericht der Finanzkommission (FiKo) zum Jahresbericht 2024 des" / "Gemeinderats": the title is the
                # text after the first cue word, to the end of the heading block
                mk = re.search(r"\s(?:zum|zur|zu|uber|sur la|sur le|sur les|sur l'|sur|sul|sulla|sull')(?:\s+(?=\S)|$)", t)
                blk = _block_rest(head, i)
                if mk and label in HEADING_LABELS and len(blk) <= 4:
                    s1 = f.span(mk.end(), mk.end() + 1)[0] if mk.end() < len(t) else nx.char_start
                    reg = _Reg(doc, s1, head[blk[-1]].char_end)
                    if TYPE_LINE_RX.match(" ".join(reg.t.split())):
                        return None, False                  # "Bericht der Pensionskasse zum" / "Postulat der SP-Fraktion vom ..."
                    return _result(reg, 0, len(reg.t), "after_kind_cue", label, {"form": "kind_line", "cue": mk.group(0).strip()}), False
                if re.search(r"\s(?:zum|zur|zu|uber|sur|sul|sulla|des|der|du|de la|del|della)$", " " + fl):
                    return None, False
            return _after(doc, head, i, kind=True), False
        return None, False
    if spaced:
        if not _type_only_rest(fl[m.end():], ln.text):
            return None, True                               # the positions of a letter-spaced line are not mapped
        return (_after(doc, head, i, kind=False) if early else None), True
    rest = fl[m.end():]
    last_of_block = len(_block_rest(head, i)) == 1
    bare = NUM_RX.sub("", rest, count=1).strip(" \t:.,;/-") if NUM_RX.match(rest) else rest.strip(" \t:.,;/-")
    if cell_end is not None:
        p = m.end() + lead
        if not bare or p >= len(t):
            return None, True
        reg = _Reg(doc, f.span(p, p + 1)[0], cell_end)
        r = _type_text(doc, head, i, reg, label, m.group("type"))
        return (r if isinstance(r, tuple) and len(r) == 4 else None), True
    if not bare or (bare.startswith("(") and bare.endswith(")")) or _date_only(bare) \
            or (last_of_block and not _continues(doc, head, i) and _type_only_rest(rest, ln.text)):
        return (_after(doc, head, i, kind=False) if early else None), True
    if label == "list_item":
        # the first list item of the head (an item of an agenda: "6. Postulat <author>" / '"<title>" - Überweisung'):
        # only a title in quotation marks, after a cue word or after a colon counts
        first_item = not any(_label(doc, head[k]) == "list_item" and head[k].block_index != ln.block_index
                             for k in range(i))
        if not (i < 12 and ln.index_in_block == 0 and first_item):
            return None, False
        p = m.end() + lead
        reg = _type_region(doc, head, i, f.span(p, p + 1)[0] if p < len(t) else ln.char_end)
        r = _type_text(doc, head, i, reg, label, m.group("type"))
        if isinstance(r, tuple) and len(r) == 4 and r[2] in ("type_quoted", "type_cue", "type_colon"):
            return (r[0], r[1], "type_list_item", dict(r[3], form=r[2])), True
        return None, False
    p = m.end() + lead
    s0 = f.span(p, p + 1)[0] if p < len(t) else ln.char_end
    reg = _type_region(doc, head, i, s0)
    r = _type_text(doc, head, i, reg, label, m.group("type"))
    if r == "only":
        return (_after(doc, head, i, kind=False) if early else None), True
    if isinstance(r, tuple) and r and r[0] == "short":
        # a short text after the type word (a name or one word): a title on the lines after it is preferred
        r2 = _after(doc, head, i, kind=False) if early else None
        return (r2 or r[1]), True
    return r, True


# ------------------------------------------------------------------ head tiers

def _blocks_of(doc: vb.Doc, head: list[vb.Line]) -> list[tuple[int, int, str, int]]:
    """(start, end, label, index of the first line in head) for each block of the head, in reading order."""
    out, seen = [], set()
    for k, ln in enumerate(head):
        if ln.block_index in seen:
            continue
        seen.add(ln.block_index)
        idx = _block_rest(head, k)
        out.append((ln.char_start, head[idx[-1]].char_end, _label(doc, ln), k))
    return out


def _sentence_titled_quote(doc: vb.Doc, head: list[vb.Line]):
    for s, e, label, k in _blocks_of(doc, head):
        if label == "table":
            continue
        reg = _Reg(doc, s, e)
        m = SENT_TITLE_RX.search(reg.t)
        if m and TYPE_ANY_RX.search(reg.t, max(0, m.start() - 320), m.start()):
            r = _result(reg, m.start(1), m.end(1), "sentence_titled_quote", label, {"cue": m.group(0)[:20]}, cut=False)
            if r:
                return r
    return None


def _sentence_type_quote(doc: vb.Doc, head: list[vb.Line]):
    for s, e, label, k in _blocks_of(doc, head):
        if label in ("table", "list_item") or k >= AFTER_LINES:
            continue
        reg = _Reg(doc, s, e)
        m = SENT_TYPE_QUOTE_RX.search(reg.t)
        if m:
            r = _result(reg, m.start(1), m.end(1), "sentence_type_quote", label, {}, cut=False)
            if r:
                return r
    return None


def _sentence_cue(doc: vb.Doc, head: list[vb.Line]):
    for s, e, label, k in _blocks_of(doc, head):
        if label in ("table", "list_item") or k >= AFTER_LINES:
            continue
        reg = _Reg(doc, s, e)
        t = reg.t
        for m in TYPE_OR_KIND_RX.finditer(t):
            c = CUE_RX.search(t, m.end(), min(len(t), m.end() + 260))
            if not c:
                continue
            mid = re.sub(r"\b(?:st|nr|art|abs|dr|[a-z])\.\s", " ", t[m.end():c.start()])
            if '"' in mid or re.search(r"[?!:;]|\.\s", mid):
                continue
            a = c.end()
            end = len(t)
            for stop in re.finditer(r",? (?:eingereicht|uberwiesen|eingegangen|ein[.,:]|ein$|depose[es]?|presentat[ao])\b"
                                    r"|[;:]|\.(?=\s|$)|\?(?=\s|$)", t[a:]):
                if stop.group(0).startswith(".") and ABBREV_END_RX.search(t[a:a + stop.start() + 1]):
                    continue
                end = a + stop.start() + (1 if stop.group(0) == "?" else 0)
                break
            if end - a > MAX_TITLE:
                continue
            r = _result(reg, a, end, "sentence_cue", label, {"type_word": m.group(0), "cue": c.group(0).strip(" :\n")})
            if r:
                return r
    return None


WEAK_DOC_WORDS = frozenset("antrag protokoll beschluss bericht proposition proposta rapport rapporto anhang beilage annexe allegato".split())


def _weak_junk(fl: str, raw: str) -> bool:
    """A heading that is no title for the weak tiers: a letterhead word with no space ("STADTKLOTEN"), a kind word and
    a body ("ANTRAG GEMEINDERAT KLOTEN"), a body that decides ("Die Fachkommission I beantragt dem Parlament"), a
    body and a type word ("CONSEIL GENERAL DE LA CHAUX-DE-FONDS - MOTION")."""
    words = re.findall(r"[a-z]+", fl)
    if not words:
        return True
    if len(words) == 1 and raw.strip().isupper() and re.match(r"(?:stadt|gemeinde|kanton|ville|commune|comune|citta)[a-z]{3,}$", words[0]):
        return True
    if len(words) <= 4 and words[0] in WEAK_DOC_WORDS and len(words) >= 2 and words[1] in ORG_FIRST:
        return True
    if len(words) <= 10 and re.search(r"\b(?:beantragt|beantragen|beschliesst|propose|arrete|decide|risolve|decreta)\b", fl):
        return True
    if re.match(r"^(?:des kantons|du canton|de la ville|der stadt|del cantone|della citta|de la commune|der gemeinde)\b", fl):
        return True
    return words[0] in ORG_FIRST and bool(re.search(r"\s[-\u2013]\s(?:" + TYPE + r")$", fl))


def _heading_candidate(doc: vb.Doc, head: list[vb.Line], k: int, tier: str):
    ln = head[k]
    fl = _fold_line(ln.text)
    if (_letterhead(fl) or _structural(fl) or KIND_ONLY_RX.match(fl) or SALUTATION_RX.match(fl) or _date_only(fl)
            or _number_line(fl) or _form_label_strict(fl)):
        return None
    form = tier in ("heading_after_form", "text_after_form")
    if TYPE_LINE_RX.match(fl) or _org_line(fl):
        return None
    if HEAD_KIND_RX.match(fl) and not (form and len(re.findall(r"[a-z0-9]+", fl)) >= 5):
        return None                                         # after a form a title can start with a kind word
    if _party_mark(fl, ln.text) and len(re.findall(r"[a-z]+", fl)) <= 8 and tier == "weak_first_heading":
        return None
    if re.fullmatch(r"(?:\w ){3,}\w", vb.fold_map(ln.text).text.strip()):
        return None
    if tier == "weak_first_heading" and _weak_junk(fl, ln.text):
        return None
    if form and VERB_RX.search(fl) and len(fl.split()) >= 8 and re.search(r"\b(?:obligatoirement|bitte|veuillez|prego)\b", fl):
        return None                                         # an instruction line of a form
    run = _run_from(doc, head, k, max_lines=3)
    if run is None:
        return None
    reg = _Reg(doc, *run)
    return _result(reg, 0, len(reg.t), tier, _label(doc, ln), {}, cut=tier != "weak_first_heading")


def _form_stack_end(head: list[vb.Line]) -> int | None:
    """The index of the first line after a form head in which each label line has one value line (a stack of labels
    and then a stack of values, or label and value in turn). None if the head has no such form with 3 or more labels."""
    lab = re.compile(r"^[^:\"]{2,40}:$")
    i0 = next((k for k in range(min(len(head), 20)) if lab.match(_fold_line(head[k].text))), None)
    if i0 is None:
        return None
    n_lab = n_val = 0
    for k in range(i0, min(len(head), i0 + 30)):
        fl = _fold_line(head[k].text)
        if lab.match(fl):
            n_lab += 1
        elif not (":" in fl and _form_label_strict(fl)):    # not "label: value" on one line
            n_val += 1
            if n_val > n_lab:
                return None
        nxt = _fold_line(head[k + 1].text) if k + 1 < len(head) else ""
        if n_lab >= 3 and n_val == n_lab and nxt and not lab.match(nxt) and not (":" in nxt and _form_label_strict(nxt)):
            return k + 1
    return None


def _heading_after_form(doc: vb.Doc, head: list[vb.Line]):
    """Tiers heading_after_form and text_after_form."""
    k_end = _form_stack_end(head)
    if k_end is not None and (k_end and head[k_end - 1].block_index == head[k_end].block_index):
        k_end = None
    if k_end is not None and _label(doc, head[k_end]) in HEADING_LABELS:
        r = _heading_candidate(doc, head, k_end, "heading_after_form")
        if r:
            return r
    for s, e, label, k in _blocks_of(doc, head):
        if label not in HEADING_LABELS:
            continue
        before = [_fold_line(x.text) for x in head[max(0, k - 12):k]]
        if sum(1 for fl in before if re.match(r"^[^:\"]{2,40}:(?:\s.{0,45})?$", fl)) < 3:
            continue
        r = _heading_candidate(doc, head, k, "heading_after_form")
        if r:
            return r
    if k_end is not None and _label(doc, head[k_end]) == "text" and len(_block_rest(head, k_end)) <= 4 \
            and not head[k_end].text.strip().startswith("("):
        return _heading_candidate(doc, head, k_end, "text_after_form")
    return None


NUM_TITLE_RX = re.compile(r"^(?P<num>(?P<y>\d{2})\.(?P<n>\d{3,4})) ?(?P<suffix>[a-z]{1,2})?\s*:?\s+(?=\S)")


def _try_number_line(doc: vb.Doc, head: list[vb.Line], i: int):
    """Tier number_line_title: a block of the first 25 lines that starts with an affair number of the form 21.067 or
    21.4209 and then prints the title ("09.528 Finanzierung der Gesundheitsleistungen aus einer Hand")."""
    ln = head[i]
    label = _label(doc, ln)
    if i >= 25 or (i and head[i - 1].block_index == ln.block_index) or label in NO_TYPE_LABELS:
        return None
    f = vb.fold_map(ln.text, base=ln.char_start, keep_newlines=False)
    t = f.text
    lead = len(t) - len(t.lstrip())
    m = NUM_TITLE_RX.match(t.strip())
    if not m or (int(m.group("y")) <= 12 and 1990 <= int(m.group("n")) <= 2040):       # a month and a year
        return None
    rest = t.strip()[m.end():]
    if TYPE_LINE_RX.match(rest) or re.match(r"(?:iv\.? ?pa\.?|pa\.? ?iv\.?|mo\.|po\.|ip\.|kt\.? ?iv\.?|bv\.)\s", rest) \
            or len(re.findall(r"[a-z]{3,}", rest)) < 2:
        return None
    p = m.end() + lead
    s0 = f.span(p, p + 1)[0]
    run = _run_from(doc, head, i)
    reg = _Reg(doc, s0, run[1] if run else ln.char_end)
    return _result(reg, 0, len(reg.t), "number_line_title", label, {"number": m.group("num")})


MINUTE_HEAD_RX = re.compile(r"^(?:auszug aus dem (?:\w+ )?protokoll|protokollauszug|extrait du proces-verbal|"
                            r"estratto (?:del|dal) (?:verbale|protocollo))")


def _try_minute_number(doc: vb.Doc, head: list[vb.Line], i: int):
    """Tier minute_number_title: below the head line of a minute extract (Auszug aus dem Protokoll, Extrait du
    procès-verbal), a block of the first 14 lines that starts with the number of the decision (3 or 4 digits) and
    then prints the title ("0631 Grand Conseil. Démission et remplacement")."""
    ln = head[i]
    label = _label(doc, ln)
    if not 1 <= i < 14 or head[i - 1].block_index == ln.block_index or label in NO_TYPE_LABELS:
        return None
    f = vb.fold_map(ln.text, base=ln.char_start, keep_newlines=False)
    t = f.text
    m = re.match(r"^\s*(?:< ?)?(\d{3,4})\s+(?=[a-z])", t)
    if not m or not any(MINUTE_HEAD_RX.match(_fold_line(x.text)) for x in head[:i]):
        return None
    if len(m.group(1)) == 4 and not m.group(1).startswith("0") and len(t.split()) <= 4:
        return None                                         # a postal code and a place
    if VERB_RX.search(t) or len(_block_rest(head, i)) > 5:
        return None                                         # a sentence of the body text that starts with a number
    s0 = f.span(m.end(), m.end() + 1)[0]
    if not doc.text[s0:s0 + 1].isupper() or TYPE_LINE_RX.match(t[m.end():]):
        return None
    run = _run_from(doc, head, i)
    reg = _Reg(doc, s0, run[1] if run else ln.char_end)
    return _result(reg, 0, len(reg.t), "minute_number_title", label, {"number": m.group(1)})


SEMI_TYPE_END_RX = re.compile(r"^(?P<pre>.{0,70}?)(?<![\w-])" + TYPE + r"(?:\s+(?:nr\.?\s*)?\d[\d./-]{0,9})?$")


def _semi_author(doc: vb.Doc, reg: _Reg, part: tuple[int, int]) -> bool:
    """True if the field reg.t[a:b] of a semicolon line is an author: a name and a party mark, or a name."""
    a, b = part
    fl = " ".join(reg.t[a:b].split())
    raw = " ".join(doc.text[slice(*reg.span(a, b))].split()) if b > a else ""
    if not fl or len(fl.split()) > 8 or re.search(r"\d", fl):
        return False
    return _author_line(fl, raw) or _name_like(raw)


def _semicolon_author(doc: vb.Doc, head: list[vb.Line], i: int, reg: _Reg, parts, seg, label: str):
    """Tier type_semicolon_author: a head line with fields divided by semicolons in which a field ends with a type word
    (a date and a decision number can stand before it, an affair number after it), the next field is the author
    (name and party mark) and the field after that is the title: "4. Juni 2019 · Beschluss Nr. 22-2019 Postulat;
    Christoph Fischbach, SP; Wahrzeichen für sämtliche Klotener Sportvereine"."""
    for k in range(min(2, len(seg) - 2)):
        m = SEMI_TYPE_END_RX.match(seg[k])
        if not m:
            continue
        pre = m.group("pre").strip()
        if pre and not (re.search(r"\d", pre) and len(re.findall(r"[a-z]{4,}", pre)) <= 3):
            continue                                        # only a date and a decision number can stand before
        if not _semi_author(doc, reg, parts[k + 1]):
            continue
        n = k + 2
        raw_n = " ".join(doc.text[slice(*reg.span(*parts[n]))].split()) if parts[n][1] > parts[n][0] else ""
        if n + 1 < len(seg) and len(seg[n].split()) <= 3 and _party_mark(seg[n], raw_n):
            n += 1                                          # "Schriftliche Anfrage; Manuel Silva; SVP; <title>"
        a, b = parts[n]
        if not seg[n] or re.match(r"^(?:" + STATUS + r")\b", seg[n]):
            return None
        return _result(reg, a, b, "type_semicolon_author", label, {"type_word": seg[k][len(pre):].strip()})
    return None


def _try_semicolon(doc: vb.Doc, head: list[vb.Line], i: int):
    """Tier type_semicolon: a head block with fields that are divided by semicolons, with a type word in one of the
    first 3 fields and a status word or a year in a later field ("Einwohnerrat; schriftliche Anfrage; SP; <title>;
    2025; Beantwortung des Stadtrats"). The title is the field directly before the first status or year field."""
    ln = head[i]
    label = _label(doc, ln)
    if i >= 15 or (i and head[i - 1].block_index == ln.block_index) or label in NO_TYPE_LABELS:
        return None
    idx = _block_rest(head, i)
    if len(idx) > 5:
        return None
    reg = _Reg(doc, ln.char_start, head[idx[-1]].char_end)
    t = reg.t
    if t.count(";") < 2:
        return None
    parts, pos = [], 0
    for m in re.finditer(";", t):
        parts.append((pos, m.start()))
        pos = m.end()
    parts.append((pos, len(t)))
    seg = [" ".join(t[a:b].split()) for a, b in parts]
    k_type = next((k for k in range(min(3, len(seg))) if TYPE_LINE_RX.match(seg[k])), None) if '"' not in t else None
    k_end = None
    if k_type is not None:
        k_end = next((k for k in range(k_type + 2, len(seg)) if re.match(r"^(?:" + STATUS + r"|" + KIND + r")\b", seg[k])
                      or re.fullmatch(r"(?:19|20)\d\d", seg[k])), None)
    if k_end is not None:
        a, b = parts[k_end - 1]
        raw = doc.text[slice(*reg.span(a, b))] if b > a else ""
        if seg[k_end - 1] and not _author_line(seg[k_end - 1], raw):
            r = _result(reg, a, b, "type_semicolon", label, {"type_word": seg[k_type]}, cut=False)
            if r:
                return r
    return _semicolon_author(doc, head, i, reg, parts, seg, label)


DECISION_KIND = (r"(?:[a-z-]*beschluss|[a-z-]*entscheid|weisung|antrag|arrete|decision|decisione|risoluzione|decreto|"
                 r"proposition|proposta)")
DECISION_DATE_RX = re.compile(r"^" + DECISION_KIND + r"(?: (?:de[sr]|du|de la|del|della|dello) [a-z' -]{3,40}?)? "
                              r"(?:vom|du|del|dell') ?(?P<date>.{6,24}?)[:.]?$")
DECISION_NUMBER_RX = re.compile(r"^(?P<pre>.{0,24}?)(?:srb|rrb|grb|gr-beschluss|sr-beschluss|rr-beschluss|[a-z]*beschluss|arrete|"
                                r"decision|decisione|risoluzione|decreto)[ -]?(?:(?:nr|no|n°|n)\b\.? ?\d[\d./-]{0,11}|\d{1,4}[./-]\d{2,4})$")
REGISTRY_LINE_RX = re.compile(r"^[a-z]?\d{1,2}(?:\.\d{1,2}){1,3}\.? [a-z][a-z -]{2,40}$")
NUMBER_LABEL_RX = re.compile(r"^(?:nr|no|n°|mm|geschafts?[ -]?nr|vorlage[ -]?nr|messaggio(?: municipale)? n|message n°?)"
                             r"\.? ?\d[\d./ -]{3,14}$")
PAGE_LINE_RX = re.compile(r"^(?:seite|page|pagina|sitzung vom|seance du|seduta del)$|^(?:seite |page |pagina )?\d{1,3} (?:von|de|di|/) \d{1,3}$"
                          r"|^[_\-=. ]{4,}$")


def _try_decision_head(doc: vb.Doc, head: list[vb.Line], i: int):
    """Tiers after_decision_date_text and after_decision_number_text: the head of a decision of a government or of a
    council. A block of the first 15 lines holds only the kind of the decision and its date ("Regierungsratsbeschluss
    vom 05. Juli 2022", "Antrag des Stadtrates" / "vom 7. April 2009", "Weisung vom 07.06.2017:"), or only the label
    and the number of the decision ("SRB Nr. 2022-506"). The next text block (at most 4 lines) is the title. A number
    line below the title ("P140393") is not a part of it. If the next block starts with a type word, the type tiers
    read it."""
    ln = head[i]
    if i >= 15 or ln.index_in_block != 0 or _label(doc, ln) in ("table", "list_item", "code", "formula", "caption"):
        return None
    idx = _block_rest(head, i)
    if len(idx) > 2:
        return None
    fl = " ".join(_fold_line(head[k].text) for k in idx)
    m = DECISION_DATE_RX.match(fl)
    if m and vb.find_dates(m.group("date")) and len(fl) <= 80:
        tier = "after_decision_date_text"
    elif len(idx) == 1 and DECISION_NUMBER_RX.match(fl) and (
            not DECISION_NUMBER_RX.match(fl).group("pre").strip(" ·.-")
            or _date_only(DECISION_NUMBER_RX.match(fl).group("pre").strip(" ·.-"))):
        tier = "after_decision_number_text"                 # "SRB Nr. 2022-506", "04. März 2025 · Beschluss 81-2025"
    elif len(idx) == 1 and NUMBER_LABEL_RX.match(fl) and re.search(r"\d[./-]\d", fl):
        tier = "after_number_label_text"                    # "Nr. 18-22.034.01" / title block, "MM 61/2015" / title block
    else:
        return None
    j, passed = idx[-1] + 1, 0
    while j < len(head) and passed < 4:                     # rule, page, number, registry and form lines
        fj = _fold_line(head[j].text)
        if not (PAGE_LINE_RX.match(fj) or _number_line(fj) or _date_only(fj) or len(fj) <= 1
                or (REGISTRY_LINE_RX.match(fj) and len(fj.split()) <= 5)
                or (re.match(r"^[a-z-]{2,20}: ?[a-z]{0,20}$", fj) and tier != "after_decision_date_text")):
            break
        j, passed = j + 1, passed + 1
    if j >= len(head) or head[j].index_in_block != 0 or _label(doc, head[j]) != "text":
        return None
    fj = _fold_line(head[j].text)
    if (TYPE_LINE_RX.match(fj) or KIND_ONLY_RX.match(fj) or HEAD_KIND_RX.match(fj) or SALUTATION_RX.match(fj)
            or _structural(fj) or _form_label_strict(fj) or _letterhead(fj) or _org_line(fj) or LABEL_RX.match(fj)
            or CUE_LINE_RX.match(fj) or ADDRESS_RX.match(fj) or (ADDRESSEE_RX.match(fj) and len(fj.split()) <= 8)
            or DECISION_DATE_RX.match(fj) or DECISION_NUMBER_RX.match(fj) or _author_line(fj, head[j].text)):
        if not (";" in fj and (_letterhead(fj) or _org_line(fj)) and not TYPE_LINE_RX.match(fj)):
            return None                                     # "Eidgenössisches Finanzdepartement EFD; Änderung des ..." is a title
    blk = _block_rest(head, j)
    if len(blk) > 5:
        return None
    run = _run_from(doc, head, j, max_lines=4)
    if run is None:
        return None
    for k in blk[1:]:                                       # '"<title>"' / "Postulat <author> und Mitunterzeichnende"
        if head[k].char_end <= run[1] and TYPE_LINE_RX.match(_fold_line(head[k].text)):
            run = (run[0], head[k - 1].char_end)
            break
    reg = _Reg(doc, *run)
    body = reg.t.strip()
    mq = re.match(r'^"([^"]{6,300})"\s*(?:[-\u2013]\s*)?(?:' + TYPE + r")?[^\"]{0,40}$", body)
    if mq:                                                  # '"<title>" Interpellation'
        a0 = reg.t.find('"') + 1
        return _result(reg, a0, a0 + len(mq.group(1)), tier, "text", {"after_line": ln.text[:60], "form": "quoted"}, cut=False)
    if BODY_RX.search(body) or (VERB_RX.search(body) and not body.endswith(("?", "!"))):
        return None                                         # a sentence of the decision, not a title
    return _result(reg, 0, len(reg.t), tier, "text", {"after_line": ln.text[:60]})


ORG_HEADING_RX = re.compile(r"(?:kommission|commission|commissione|departement|direktion|parlamentsdienst|konferenz|"
                            r"sezione|kanzlei|ausgleichskasse|standeskommission)\b")
RESPONSE_LINE_RX = re.compile(r"^(?:risposta|reponse|antwort|beantwortung)\b.{0,60}?(?<![\w-])" + TYPE)


def _org_heading(fl: str) -> bool:
    """A heading that names a body or an addressee, not a title: "Geschäftsprüfungskommission", "Il Consiglio di Stato",
    "An die Aufsichtskommission", "Die Geschäftsprüfungs- und Finanzkommission an den Einwohnerrat"."""
    words = re.findall(r"[a-z]+", fl)
    if len(words) <= 4 and ORG_HEADING_RX.search(fl):
        return True
    if re.match(r"^(?:an|a l'attention|all'attenzione) (?:den|die|das|der|de|du|della|del)?", fl) and len(words) <= 6:
        return True
    if len(words) <= 9 and re.search(r"(?:kommission|rat) an (?:den|die|das) \w+$", fl):
        return True
    if len(words) <= 6 and re.search(r"\bbeschliesst\b|^au nom d[ue]|^im namen de[rs]|^anderung vom\b", fl):
        return True
    return len(words) <= 8 and bool(re.match(
        r"^(?:der|die|il|le|la|l')\s?(?:grosse rat|grand conseil|consiglio di stato|conseil-executif|regierungsrat|"
        r"stadtrat|gemeinderat|municipio|conseil \w+|consiglio \w+)", fl))


def _weak_first_heading(doc: vb.Doc, head: list[vb.Line]):
    """Tiers heading_before_response, heading_before_salutation, heading_type_in_head and weak_first_heading: a
    heading block of the first 15 lines that is no letterhead, no body name, no document kind and no structure
    heading. The tier is the evidence beside the heading. A heading before a response line or before a salutation
    is preferred to the first heading."""
    found = []
    for s, e, label, k in _blocks_of(doc, head):
        if k >= WEAK_LINES:
            break
        if label not in HEADING_LABELS or _org_heading(_fold_line(head[k].text)) \
                or _org_heading(" ".join(_fold_line(head[q].text) for q in _block_rest(head, k)[:3])):
            continue
        r = _heading_candidate(doc, head, k, "weak_first_heading")
        if not r:
            continue
        nxt = next((_fold_line(x.text) for x in head if x.char_start >= r[1]), "")
        if RESPONSE_LINE_RX.match(nxt):
            return r[0], r[1], "heading_before_response", r[3]
        if SALUTATION_RX.match(nxt):
            return r[0], r[1], "heading_before_salutation", r[3]
        before = [_fold_line(x.text) for x in head[:k]]
        typed = any(TYPE_LINE_RX.match(x) or (TYPE_ANY_RX.search(x) and len(x.split()) <= 8) for x in before)
        found.append((r[0], r[1], "heading_type_in_head" if typed else "weak_first_heading", r[3]))
    return found[0] if found else None


# ------------------------------------------------------------------ the reader

def _find(doc: vb.Doc):
    """(result or None, a type line was seen). A result is (start, end, tier, detail)."""
    head = _head(doc)
    type_seen = False
    for i in range(len(head)):
        r = _try_label(doc, head, i) or _try_number_line(doc, head, i) or _try_semicolon(doc, head, i) \
            or _try_minute_number(doc, head, i) or _try_decision_head(doc, head, i)
        if r:
            return r, type_seen
        r, seen = _try_type(doc, head, i)
        type_seen = type_seen or seen
        if r:
            if r[2] in SOFT_LINE_TIERS:
                # a title label of a form later in the head is better evidence than a text block after a type word
                for k in range(i + 1, len(head)):
                    if not LABEL_RX.match(_fold_line(head[k].text).strip()):
                        continue
                    r2 = _try_label(doc, head, k, tier_cue="-")
                    if r2:
                        return r2, type_seen
            return r, type_seen
    for fn in (_sentence_titled_quote, _sentence_type_quote, _heading_after_form, _sentence_cue, _weak_first_heading):
        r = fn(doc, head)
        if r:
            return r, type_seen
    return None, type_seen


def _candidate(doc: vb.Doc, r) -> vb.ValueCandidate:
    s, e, tier, detail = r
    return doc.candidate(FIELD, s, e, norm_title(doc.text[s:e]), tier, detail={k: v for k, v in detail.items() if v})


@vb.register(FIELD)
def read_title(doc: vb.Doc):
    """The title of the affair as the document prints it, or "not found in the PDF"."""
    if not doc.text.strip():
        return doc.not_found(FIELD, "no_text")
    r, type_seen = _find(doc)
    if r is None:
        if type_seen:
            return doc.not_found(FIELD, "no_cue", "a type word stands in the head, but no title form follows it")
        return doc.not_found(FIELD, "no_pattern", "no type word, no title label and no heading in the head")
    return _candidate(doc, r)


def read_title_apertus(doc: vb.Doc):
    """Optional extra tier, not registered, measured apart. The result of read_title, but: if read_title gives no
    title or only a weak heading tier (weak_first_heading, heading_type_in_head), the first block with the Apertus block role title on the first page
    gives the title (tier apertus_title_block). The document must be loaded with apertus_roles=True."""
    if not doc.has_apertus_roles:
        raise ValueError("load the document with apertus_roles=True")
    base = read_title(doc)
    if base.found and base.tier not in ("weak_first_heading", "heading_type_in_head"):
        return base
    head = _head(doc)
    for k, ln in enumerate(head):
        b = doc.blocks[ln.block_index]
        if b.apertus_role != "title" or (k and head[k - 1].block_index == ln.block_index):
            continue
        r, _ = _try_type(doc, head, k)
        if r is None:
            run = _run_from(doc, head, k)
            if run is None:
                continue
            reg = _Reg(doc, *run)
            r = _result(reg, 0, len(reg.t), APERTUS_TIER, b.label, {"base": base.tier if base.found else base.reason})
        if r:
            s, e, _, detail = r
            return doc.candidate(FIELD, s, e, norm_title(doc.text[s:e]), APERTUS_TIER,
                                 others=(base,) if base.found else (), detail=detail)
    return base


# ------------------------------------------------------------------ commands

def coverage(apertus: bool = False) -> dict:
    """Counts by tier over all open development documents. No export value is read. No agreement is calculated."""
    ids = vb.dev_ids("open")
    guard = vb.guard_check(ids)
    if guard["refused"] or guard["by_split"].get("dev") != len(ids):
        raise SystemExit("the guard refused ids of the open part")
    tiers: dict[str, int] = {}
    by_lang: dict[str, dict[str, int]] = {}
    by_role: dict[str, dict[str, int]] = {}
    reasons: dict[str, int] = {}
    parl: dict[str, set] = {}
    for d in ids:
        doc = vb.load_doc(d, apertus_roles=apertus)
        res = read_title_apertus(doc) if apertus else vb.read_field(doc, FIELD)
        key = res.tier if res.found else "not_found"
        tiers[key] = tiers.get(key, 0) + 1
        for table, k in ((by_lang, str(doc.language)), (by_role, str(doc.s1_role))):
            table.setdefault(k, {})[key] = table.setdefault(k, {}).get(key, 0) + 1
        parl.setdefault(key, set()).add(doc.parliament)
        if not res.found:
            reasons[res.reason] = reasons.get(res.reason, 0) + 1
    order = list(TIERS) + [APERTUS_TIER, "not_found"]
    return {"version": VERSION, "base_version": vb.VERSION, "field": FIELD,
            "what": "coverage by tier: counts of documents only; no export value read; not an agreement value",
            "mode": "with the optional Apertus tier" if apertus else "rules only (registered reader)",
            "documents": len(ids), "guard": guard,
            "with_value": sum(v for k, v in tiers.items() if k != "not_found"),
            "by_tier": {k: tiers[k] for k in order if k in tiers},
            "parliaments_by_tier": {k: len(parl[k]) for k in order if k in parl},
            "not_found_reasons": dict(sorted(reasons.items())),
            "by_language": {k: {t: v[t] for t in order if t in v} for k, v in sorted(by_lang.items())},
            "by_s1_role": {k: {t: v[t] for t in order if t in v} for k, v in sorted(by_role.items())}}


def main() -> int:
    ap = argparse.ArgumentParser(description="rule for the title (plan task <id>)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("doc_id")
    s.add_argument("--apertus", action="store_true")
    c = sub.add_parser("coverage")
    c.add_argument("--out")
    c.add_argument("--apertus", action="store_true")
    a = ap.parse_args()
    if a.cmd == "show":
        doc = vb.load_doc(a.doc_id, apertus_roles=a.apertus)
        res = read_title_apertus(doc) if a.apertus else vb.read_field(doc, FIELD)
        print(json.dumps(res.to_json(), ensure_ascii=False, indent=1))
        return 0
    r = coverage(a.apertus)
    text = json.dumps(r, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.modules.setdefault("m11_values_title", sys.modules[__name__])
    sys.exit(main())

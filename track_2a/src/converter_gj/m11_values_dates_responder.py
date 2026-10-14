# SPDX-License-Identifier: Apache-2.0
"""Plan `crisp-dm/04-modeling/plan-ech-from-pdf.md`, task <id>: the value rules for the submission date, the
response date and the responder. Interface: `src/m11_values_base.py` (not changed).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5) for the AI
agent. Status: EXCEPTION, NOT RELEASED. No human checked this file.

Version 2 (13.10.2026) is the result of the improvement round on the open parliaments: the author read the
outcomes of the open part (first table, error groups, review by eye) and changed the tiers. The values of the
open part are thus optimistic for this version. No document of a closed parliament was read.

Version 3 (13.10.2026, round 3, AFTER THE OPENING of the closed parliaments at 14:35) is the result of the round on
all 1,793 development documents: the author read the outcomes and the documents of the open and of the closed
parliaments (closed_table.md, closed_review_a.json, closed_review_b.json). Each value of this version is thus a
value "after the opening"; the values of the development documents are optimistic. The changes of version 3:
labels in table cells and label rows (sub_label_cue, sub_label_table), more label words in 3 languages, the date
above the signers (sub_signers_date), tiers of their own for the head of a response document (sub_label_cue_resp,
sub_resp_head_near, sub_resp_head_far), the forms parliament_decision_form and executive_letter_form, the
signature of the executive below a place and date line (rsp_signature_place), the body of a decision
(rsp_decision_body), the split of resp_cue_date (resp_approval_date, resp_cue_text, resp_cited_date) and the
letter of the executive to the parliament (sub_dispatch_letter).

1 Inputs
  Each reader gets one `Doc` of the interface: the block file, the rule file of the rule chain and the block roles
  of the rules mode. No reader reads an export record, a decisions file or a state file. No tier uses the block
  roles of the Apertus candidate. No rule uses the parliament key, the document id or a place name list.
  A rule uses cue words (German, French, Italian), layout forms and the S1 rule role of the rule file.
  With no rule file the S1 role is None. Then a cue test of this file says if the document holds a response.

2 Output
  A reader returns the first candidate of the tier order below, or NotFound. A reader gives no probability.
  The probability of a value will be the measured precision of its tier (addendum G).
  Date fields: `value` is the date as printed, `normalised` is the ISO day.
  Responder: `value` is the body word as printed (for example "Regierungsrates"), `normalised` is the base
  wording of the body word (for example "Regierungsrat", "Conseil d'Etat"). The key of table 3 of addendum G
  is in `detail["body_key"]`. `fold(normalised)` holds the pattern of that key. A name of a person is never
  returned.
  `others` holds at most 3 candidates of later tiers that have a different normalised value.
  A reader returns the day that the document prints. The export can hold a different day (for example the day of
  registration 1 to 7 days after the letter date of a proposal). No rule tries to give the export day.

3 Forms of a document (functions executive_form, proposal_form, is_proposal_document, is_response_document)
  executive_form       A minute cue starts one of the first 12 lines ("Auszug aus dem Protokoll", "Protokollauszug"),
                       or a line is a signature formula of the executive ("Im Namen des Regierungsrates", "NAMENS DES
                       STADTRATES FRAUENFELD", "PER IL CONSIGLIO DI STATO"). A formula with a signer of a parliament
                       below it ("Die Ratssekretärin:", "Präsidium", "Sekretariat") does not count.
                       Also: a line "<place>, <date>" directly above a line that holds only the body word
                       ("Riehen, 23. April 2024" then "Gemeinderat Riehen"; not in an address block), and the
                       executive_letter_form.
  executive_letter_form  One of the first 6 lines is an address line of the parliament ("An den Grossen Rat"), and one
                       of the 3 lines before it holds only the body word ("Regierungsrat des Kantons Basel-Stadt").
                       With a proposal type word at a line start of the first 12 lines the letter is a response
                       document (also if the S1 role is other).
  parliament_decision_form  A signature formula with a signer of the parliament below it ("Namens des Stadtrats",
                       "Der Präsident", ..., "Die Ratssekretärin"; the role line can be 5 to 10 lines below the
                       formula), or a body that takes note of the answer or the report of a different body ("Der
                       Stadtrat nimmt Kenntnis von der schriftlichen Antwort des Gemeinderats"). Such a document is
                       no proposal document, and its formula is no formula of the executive: its dates are the day
                       of the meeting and the day of the signature of the decision.
  proposal_form        The first 25 lines hold a proposal type word or a phrase that addresses the body, and none of
                       the first 15 lines starts with a response noun ("Bericht und Antrag", "Rapport", "Mitteilung").
  proposal document    S1 role proposal with the proposal form and not the executive form.
  response document    S1 role response or combined; also S1 role proposal with the executive form (the S1 role has
                       errors: a minute or a letter of the executive can have the S1 role proposal).

4 Tiers of `submission_date` (in this order)
  sub_label_cue        A form label selects the date: "Eingereicht am:", "Eingang:", "Eingegangen:", "Déposée
                       le :", "Date du dépôt", "Presentata il", "Ricevuta il". The date is on the label line (a
                       weekday between them is permitted) or on a value line below it; label lines between them
                       are permitted, and if the label is the first line of a stack of label lines, the first
                       value line below the stack is its value. A receipt label ("Eingegangen:") on a minute of
                       the executive is refused: it is the stamp of the parliament office on the response.
                       Also in a table (cells are the parts of a line between tab characters): the label starts a
                       cell and the date is directly after it ("N° de l'objet 23.051 ... <tab> Date du dépôt
                       17.10.2023 ..."), or the label fills a cell and the date starts the next cell. The label
                       words are the lists SUB_LABEL_DE, SUB_LABEL_FR, SUB_LABEL_IT and SUB_LABEL_STAMP (the stamp of
                       a parliament office: "EINGANG GR" then the date).
  sub_label_table      A row of labels and a row of values: a cell of the label row holds only a label word, and
                       the cell with the same number in the next row starts with the date ("N° de l'objet <tab> Date
                       du dépôt <tab> Heure du dépôt" then "23.054 <tab> 24.10.2023 <tab> 10:12"). A table with a
                       date in this cell of 2 rows, or 2 such tables with different days, is a list of items: no
                       candidate.
  sub_label_cue_resp   The tier sub_label_cue in a response document (the label is in the head of a response; it
                       can be the receipt stamp on the response).
  sub_type_date_near   A proposal type word at a line start (or after a response noun at the line start) is
                       directly before the date, with at most a number and one of "vom", "du", "del" between
                       them ("Interpellation vom 17. September 2019", "Interrogazione del" then the date line).
                       With no "vom", "du", "del" the submit verb must be directly after the date.
  sub_resp_head_near   The tier sub_type_date_near in a response document: the head of a response prints the
                       proposal, its authors and its date ("Interpellation Muster vom 3. Mai 2021: Antwort").
  sub_signers_date     A line "<place>, <date>" directly above the signers of the proposal: one of the 2 lines below
                       it starts with a signer label ("Erstunterzeichnende:", "Mitunterzeichnende:", "Premier
                       signataire", "Primo firmatario"), or (after line 12) the line below it starts with a type
                       word, a name and a party in parentheses ("Bern, 9. Juni 2005" then "Motion A. Muster (SP);
                       B. Muster, ..."). All kinds of documents: a combined document prints the proposal with this
                       line before the response.
  sub_resp_head_far    The tier sub_type_date_far in a response document ("Postulat de Mme X et Mme Y du
                       30.03.2023", "Motion von A, B und C vom 11. September 2013" then the title in quotation
                       marks). In a response document this tier is before sub_sentence_cue.
  sub_sentence_cue     Not for a proposal document: a sentence in the head has a submit verb, a type word and the
                       date ("Am 8. Mai 2024 hat ... eine Kleine Anfrage ... eingereicht"). The date directly
                       after the submit verb is the candidate ("presentata il 28 agosto 2018"), else the first
                       date that is not the date of a response or of a numbered decision.
  sub_type_date_far    A type word at a line start is at most 250 characters before the date, the text between
                       ends with "vom", "du" or "del" and has no word for a meeting, a law, a body or a
                       response, and the date ends its clause or the title follows ("vom 24. August 2020 mit dem
                       Titel", "betreffend"). With "; Beantwortung" after the date the limit is 500 characters.
                       Also a line that holds only "vom", "du" or "del" and the date below a proposal heading.
  sub_type_date_inline Not for a proposal document: a type word in running text and "vom", "du" or "del" are
                       directly before the date ("In ihrem Vorstoss vom 19. Juni 2019"), or the submit verb is
                       directly after the date ("iniziativa 17 ottobre 2022 presentata da").
  sub_sentence_meeting Not for a proposal document: the sentence form of sub_sentence_cue, but the date is the day
                       of a meeting ("An der Parlamentssitzung vom 28. September 2019 reichten ... ein").
  sub_letter_head      Proposal documents only: a line "<place>, <date>" or "Datum: <date>" in the first 25
                       lines (the date of the letter). A postal code before the place is permitted. A line
                       "<place> <date>" with no comma counts if the place is one word.
  sub_letter_tail      Proposal documents only: such a line in the last 15 lines (before the signature).
  sub_head_date_line   Proposal documents only: the first 15 lines hold exactly one day on a line that holds only
                       the date ("15 novembre 2021 / 109.21", "del 22 giugno 2020"). A date line below the labels
                       of a memo ("Pour :", "Copie à :") is refused.
  sub_tail_date_line   Proposal documents only: the last line of the last 15 lines that holds only the date, or the
                       date and the names of the signers ("17.3.2011 A. Muster", "A. Muster, Stadtrat SVP, 17.09.2020").
  sub_letter_body      Proposal documents only: a line "<place>, <date>" between the first 25 and the last 15 lines
                       (the reading order of a page with 2 columns puts the letter date there).
  sub_sentence_other   Proposal documents only: the sentence form of sub_sentence_cue. The sentence can refer
                       to a different proposal.
  sub_dispatch_date    The date of a dispatch of the executive: "Bericht und Antrag vom", "Weisung vom", "Messaggio
                       n. 8327 del" at a line start of the first 12 lines; or, not for a proposal document and not
                       with the S1 role response or combined, the letter date in a head that has a line "Bericht
                       und Antrag ...", "Botschaft ...". This is
                       the day of the dispatch. It is not the day of a proposal of a member. Also "21.1626.01,
                       Ratschlag des RR vom 01.12.2021" (a number before the dispatch word, the short form of the body).
  sub_dispatch_letter  Not for a proposal document, a response document or the S1 role committee: one of the first
                       6 lines is an address line of the parliament ("An den Grossen Rat"), no line of the first 12
                       lines starts with a proposal type word, and the head has a line "<place>, <date>". This is
                       the letter date of a letter to the parliament. It is not the day of a proposal of a member.
  The date of a decision of the executive ("Regierungsratsbeschluss vom 08. April 2014") is never a submission
  date: see resp_decision_date.
  Each tier refuses a date after a word for a meeting, a law or a page footer.
  Version 1 had the tier sub_weak_head_date (the only day of the first 15 lines). It is gone: a date in running
  text is no evidence. The date line form is now sub_head_date_line.

5 Tiers of `response_date` (only for a response document, or with a response block of the rules mode)
  resp_cue_date        A response noun and the body word are directly before the date ("Antwort des
                       Regierungsrates vom", "Réponse du Conseil d'Etat du", "Risposta del Municipio del",
                       "(Bericht Regierungsrat, 26.1.2016)", "Bericht vom", "Stellungnahme des RR vom") and the
                       cue is a heading: it starts a line of the first 12 lines (a number before it is permitted).
                       Also a form label "Datum Beantwortung:" at a line start.
  resp_approval_date   "Approuvé par le Conseil municipal le", "Réponse adoptée par le Conseil municipal en séance
                       du": the day when the body approved the response.
  resp_decision_date   The date of the decision of the executive: a decision word of the body ("Stadtratsbeschluss
                       vom", "RRB vom"), a decision number with "vom" or "du" below a label "RRB-Nr.:" or "N° d'ACE:",
                       or a line "RG n. 6322 del <date>" (response documents only, one day in the document).
  resp_minute_head     A minute cue starts one of the first 12 lines (or "Sitzung vom" with "Beschluss Nr." and no
                       parliament word). The date after "Sitzung vom", or the first date line of the head, is the
                       day of the decision. The tier is off if the body word of the cue names the parliament
                       (see rsp_minute_cue).
  resp_heading_date    A line that holds only "vom", "du" or "del" and the date, below a heading with a response
                       noun ("RÉPONSE DU CONSEIL COMMUNAL ..." then "(Du 19 février 2024)").
  resp_signature_date  A line "<place>, <date>" at a signature formula of the executive in the whole document (the
                       formula can be before the attachments) or at a body word line of the last 30 lines: at
                       most 4 lines before it, else at most 3 lines after it.
  resp_letter_head     Response documents only, and a tier of the responder shows the executive as the sender: a
                       line that holds only a date in the first 12 lines, or a line "<place>, <date>" in the
                       first 25 lines.
  resp_letter_tail     Response documents only: a line "<place>, <date>" in the last 15 lines with no
                       signature formula near it.
  resp_cue_text        The cue of resp_cue_date in running text, or after line 12, or a response label in a sentence
                       ("Die Antwort des Gemeinderates vom 3. Juni 2009 ist ...", "(Beantwortung vom 2. Juni 2009)").
                       This is a weak candidate: the phrase can refer to a different response.
  resp_page1_date_line Response documents only: the first block of page 1 after line 12 that holds only
                       a date (a letter date beside the address). This is a weak candidate.
  resp_tail_date_line  Response documents only: the last block of the last 12 lines that holds only a
                       date. This is a weak candidate.
  resp_cited_date      Only for a document that holds no response: the heading cue of resp_cue_date ("16.5361.02,
                       Stellungnahme des RR vom 11.01.2017" in a decision of the parliament). The document cites
                       the response and its date. The writer decides what to do with it.
  The signature date of a decision of a parliament is no response date: with the parliament_decision_form the
  document is no response document by its form.
  The tiers resp_letter_head, resp_letter_tail and resp_page1_date_line refuse a date that a label or a type
  word gives to the proposal. The tail tiers refuse a place and date line after words of thanks (the letter
  date of a proposal that is added to the response).
  Version 1 had the decision dates in resp_cue_date, and resp_minute_head took any first date of the head.

6 Tiers of `responder`
  rsp_response_cue     Not for a proposal document: a phrase says that the body answers ("Antwort des
                       Regierungsrates", "Der Stadtrat beantwortet", "Der Stadtrat erteilt folgende Antwort",
                       "Réponse du Conseil communal", "Risposta del Municipio", "lo scrivente Municipio"). The
                       phrase is in the first 30 lines or starts a line (a heading).
  rsp_signature        The body word is in a signature formula of the executive (the last one of the document:
                       "Im Namen des Stadtrates", "Für den Gemeinderat", "Au nom du Conseil d'Etat", "Per il
                       Municipio") or it is a full line of the last 30 lines with an article ("DER GEMEINDERAT").
  rsp_signature_place  The body word is a full line directly below a line "<place>, <date>" after line 12, with at
                       most an article, link words and one place word ("Dübendorf, 11. Juni 2020" then "Stadtrat
                       Dübendorf"). Not in an address block (a line with a postal code below it, "An den" before it).
  rsp_minute_cue       A minute cue with the body word starts a line of page 1 ("Auszug aus dem Protokoll des
                       Stadtrats"). The tier is off if the document shows that the word names the parliament: a
                       compound for its president ("Gemeinderatspräsident"), an item that goes
                       to a different body ("an den Stadtrat überwiesen") or a proposal of a different body
                       ("Antrag des Stadtrates").
  rsp_decision_body    One of the first 6 lines starts with a decision word of the body ("Regierungsratsbeschluss
                       vom ...", "Beschluss des Stadtrats", "Arrêté du Conseil d'Etat"). This is the body that
                       DECIDES. It is not in each case the responder of a response step: the document can be a
                       decision with no response. The tier is off with the parliament_decision_form and if a
                       different body makes the proposal for the decision ("ANTRAG des Stadtrates", "Beschluss des
                       Gemeinderates": the draft of a decision of the parliament).
  rsp_letter_head      Response documents only: the body word is a full line of the first 12 lines (the letter
                       head), with at most a place after it, and it is not a part of an address ("An den").
  rsp_tail_line        Response documents only: the body word with at most a place after it is a full line of
                       the last 30 lines ("Stadtrat Wetzikon").
  rsp_sender_block     Response documents only: the body word is a full line of page 1 directly above an address
                       or contact line ("Stadtrat", "Marktgasse 58", "E-Mail ...").
  rsp_page_line        Response documents only: a page head or page foot line "<Stadt|Gemeinde|Kanton> <place>
                       <body word>" ("Stadt Kriens Stadtrat").
  rsp_response_block   The body word that is most frequent after an article in the response blocks of the rules
                       mode (2 or more hits, more than each other body word).
  rsp_addressee_cue    The proposal addresses the body ("Der Gemeinderat wird gebeten", "Ich bitte den Stadtrat",
                       "Lodevole Municipio", "Le Conseil d'Etat est prié", "Intende il Consiglio di Stato",
                       "questions posées au Conseil communal"). This is the ADDRESSED body: the body that is asked,
                       not the body that signs. A document that holds only a proposal has no responder of a response
                       step; the writer decides what to do with this value. A specific body word is before a word
                       that is also a common noun ("Regierung", "Gouvernement", "Governo").
  rsp_response_text    A response phrase in the running text, or in a proposal document ("vgl. auch Antwort des
                       Bundesrates zur ..."). This is a weak candidate: the phrase can refer to a different answer.
  "Grosser Gemeinderat" and "Grosser Stadtrat" are never a body word (a parliament).

7 Limits
  The word "Stadtrat" or "Gemeinderat" is the executive in one town and the parliament in a different town.
  A cue word cannot see this in each document: rsp_letter_head and rsp_minute_cue can return the parliament if no
  cue of chapter 6 is in the text. The S1 role and the block roles of the rule chain have errors. A date after
  "Sitzung vom" in a minute of the executive is the day of the decision, not the day of the dispatch. The letter
  date of a proposal is the day when it was written; the day of registration is not printed in most documents.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_dates_responder.py show DOC_ID
  uv run --offline --frozen --no-sync python src/m11_values_dates_responder.py coverage [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from bisect import bisect_left
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_values_base as vb  # noqa: E402

VERSION = "m11-values-dates-responder-3"
MY_FIELDS = ("submission_date", "response_date", "responder")
SUBMISSION_TIERS = ("sub_label_cue", "sub_label_table", "sub_label_cue_resp", "sub_type_date_near",
                    "sub_resp_head_near", "sub_signers_date", "sub_resp_head_far", "sub_sentence_cue",
                    "sub_type_date_far", "sub_type_date_inline", "sub_sentence_meeting", "sub_letter_head",
                    "sub_letter_tail", "sub_head_date_line", "sub_tail_date_line", "sub_letter_body",
                    "sub_sentence_other", "sub_dispatch_date", "sub_dispatch_letter")
RESPONSE_TIERS = ("resp_cue_date", "resp_approval_date", "resp_decision_date", "resp_minute_head", "resp_heading_date",
                  "resp_signature_date", "resp_letter_head", "resp_letter_tail", "resp_cue_text",
                  "resp_page1_date_line", "resp_tail_date_line", "resp_cited_date")
RESPONDER_TIERS = ("rsp_response_cue", "rsp_signature", "rsp_signature_place", "rsp_minute_cue", "rsp_decision_body", "rsp_letter_head",
                   "rsp_tail_line", "rsp_sender_block", "rsp_page_line", "rsp_response_block", "rsp_addressee_cue",
                   "rsp_response_text")
# tiers of the responder that show the executive as the sender of the document
SENDER_TIERS = ("rsp_response_cue", "rsp_signature", "rsp_signature_place", "rsp_minute_cue", "rsp_decision_body", "rsp_letter_head",
                "rsp_tail_line", "rsp_sender_block", "rsp_page_line")
SKIP_LABELS = ("page_footer", "footnote")
HEAD_LINES, TAIL_LINES = 40, 30

# ------------------------------------------------------------------ body words (table 3 of addendum G)

# key -> (pattern on the folded text, base wording)
BODY_WORDS = (
    ("regierungsrat", r"regierungsrat(?:e?s)?", "Regierungsrat"),
    ("staatsrat", r"staatsrat(?:e?s)?", "Staatsrat"),
    ("bundesrat", r"bundesrat(?:e?s)?", "Bundesrat"),
    ("stadtrat", r"stadtrat(?:e?s)?", "Stadtrat"),
    ("gemeinderat", r"gemeinderat(?:e?s)?", "Gemeinderat"),
    ("standeskommission", r"standeskommission", "Standeskommission"),
    ("kleiner_rat", r"kleine[rn]? rat(?:e?s)?", "Kleiner Rat"),
    ("regierung", r"regierung", "Regierung"),
    ("conseil_etat", r"conseil d[' ]etat", "Conseil d'Etat"),
    ("conseil_municipal", r"conseil municipal", "Conseil municipal"),
    ("conseil_communal", r"conseil communal", "Conseil communal"),
    ("conseil_federal", r"conseil federal", "Conseil fédéral"),
    ("conseil_administratif", r"conseil administratif", "Conseil administratif"),
    ("conseil_executif", r"conseil[ -]executif", "Conseil-exécutif"),
    ("municipalite", r"municipalite", "Municipalité"),
    ("gouvernement", r"gouvernement", "Gouvernement"),
    ("consiglio_di_stato", r"consiglio di stato", "Consiglio di Stato"),
    ("municipio", r"municipio", "Municipio"),
    ("consiglio_federale", r"consiglio federale", "Consiglio federale"),
    ("governo", r"governo", "Governo"),
)
BODY = "(?:" + "|".join(p for _, p, _ in BODY_WORDS) + ")"
_BODY_KEY_RX = [(k, re.compile(p + r"\Z"), w) for k, p, w in BODY_WORDS]
# one body word as a full token, group `body`. "Grosser Gemeinderat" and "Grosser Stadtrat" name a parliament.
B = r"(?<![a-z])(?<!grossen )(?<!grosser )(?<!grosse )(?P<body>" + BODY + r")(?![a-z])"


def body_key(folded_word: str) -> tuple[str, str] | None:
    """(key of table 3, base wording) of a folded body word; None if it is not one."""
    for k, rx, w in _BODY_KEY_RX:
        if rx.match(folded_word):
            return k, w
    return None


# ------------------------------------------------------------------ cue words (folded form: lower case, no accents)

TYPE_WORD = (r"(?<![a-z])(?:(?:richtlinien|globalbudget|budget|volks|fraktions|kommissions|jugend|planungs|leistungs)?motion"
             r"|(?:fraktions|kommissions|jugend|volks|dringlichkeits)?postulat|interpellation"
             r"|(?:kleine|einfache|schriftliche|dringliche|parlamentarische)"
             r" anfrage|anfrage|vorstoss|vorstosses|(?:parlamentarische |einzel|volks)?initiative|(?<!im )auftrag"
             r"|beschlussantrag|parlamentarische (?:empfehlung|erklarung)"
             r"|petition|resolution|question ecrite|question|interpellation|postulat|initiative"
             r"|interrogazione|interpellanza|mozione|iniziativa|postulato)(?:s|es|en|e)?(?![a-z])")
TYPE_RX = re.compile(TYPE_WORD)
SUBMIT_VERB = (r"(?:eingereicht(?:e[nrs]?)?|reicht(?:e|en)|eingegangen|zugestellt|depose(?:e|es|s)?|deposai(?:en)?t"
               r"|presentat[aoie]|inoltrat[aoie]|depositat[aoie])")
SUBMIT_VERB_RX = re.compile(r"(?<![a-z])" + SUBMIT_VERB + r"(?![a-z])")
# the date is directly after the submit verb ("presentata il", "eingereicht am", "deposee le")
VERB_PRE_RX = re.compile(r"(?<![a-z])" + SUBMIT_VERB + r" (?:am|le|il|in data|en date du|dato del) \Z")
# the date is directly before the submit verb ("17 ottobre 2022 presentate da", "vom 3. Mai 2021 eingereichte")
VERB_POST_RX = re.compile(r"^,? " + SUBMIT_VERB + r"(?![a-z])")
# the date after a response noun with no body word ("Risposta del 17 settembre 2018 all'interpellanza")
RESP_NOUN_PRE_RX = re.compile(r"(?<![a-z])(?:antwort|beantwortung|stellungnahme|reponse|risposta|osservazioni)"
                              r" (?:vom|du|del) \Z")
RESP_NOUN = (r"(?:antwort|beantwortung|stellungnahme|bericht und antrag|bericht|beschluss|erklarung|mitteilung"
             r"|reponse|prise de position|rapport|determination|risposta|osservazioni|presa di posizione|rapporto)")
RESP_NOUN_RX = re.compile(r"(?<![a-z])" + RESP_NOUN + r"(?![a-z])")
WEEKDAY = (r"(?:montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|lundi|mardi|mercredi|jeudi|vendredi"
           r"|samedi|dimanche|lunedi|martedi|mercoledi|giovedi|venerdi|sabato|domenica)")
# context directly before a date that a tier refuses
LAW_PRE_RX = re.compile(r"(?:gesetz|gesetzes|verordnung|ordnung|reglement|reglements|loi|ordonnance|arrete|decret"
                        r"|legge|regolamento|decreto|vereinbarung|konkordat|vertrag|vertrages|verfassung|weisung"
                        r"|richtlinie|convention|constitution|statut|abkommen)(?:s|es)?(?: [a-z()\[\].,;'/-]+){0,6}?"
                        r" (?:vom|du|del|della|dell')[ (]*\Z")
MEETING_PRE_RX = re.compile(r"(?:sitzung|seance|seduta|plenum|session|tagung|versammlung)[a-z]*(?: [a-z.,()]+){0,4}?"
                            r"[ :,]*(?:" + WEEKDAY + r",? ?(?:den |le |il )?)?\Z")
FOOT_PRE_RX = re.compile(r"(?:bearbeitung|modification|version|versand|versandt|versanddatum|verteilt|veroffentlichung"
                         r"|beschwerdefrist|referendumsfrist|stand|e-parl|gultig|kraft|frist|spatestens|bis|ab|seit"
                         r"|per|expedition|spedizione|druck|gedruckt)(?: am| zum| dem| du| le)?[ :]*\Z")
# form labels for the submission date
# German, French and Italian label words. A label names the day when the proposal came to the parliament.
SUB_LABEL_DE = (r"eingereicht am|eingereicht den|eingereicht per|eingereicht|eingang am|eingang|eingegangen am"
                r"|eingegangen|eingangsdatum|datum des eingangs|datum eingang|einreichungsdatum|einreichedatum"
                r"|datum der einreichung|datum einreichung|einreichung|eingabedatum|datum der eingabe|eingabe vom"
                r"|eingereicht am/um|posteingang")
SUB_LABEL_FR = (r"deposee? le|date d[eu] depot(?: aupres du bureau)?|date de depot de l'intervention|depot le|depot"
                r"|date de reception|recue? le|date de remise|remise? le")
SUB_LABEL_IT = (r"presentat[ao] il|data(?: di| della)? presentazione|ricevut[ao] il|inoltrat[ao] il|data d'inoltro"
                r"|data di inoltro|data di ricezione|data di deposito|depositat[ao] il|data(?: di| della)? consegna"
                r"|consegnat[ao] il")
# the receipt stamp of a parliament office: "EINGANG GR", "Eingang Ratssekretariat"
SUB_LABEL_STAMP = (r"eingang (?:gr|kr|lr|sr|er|ggr|ratsburo|ratssekretariat|parlamentsdienste|staatskanzlei"
                   r"|stadtkanzlei|gemeindekanzlei|kanzlei)")
SUB_LABEL = "(?:" + SUB_LABEL_STAMP + "|" + SUB_LABEL_DE + "|" + SUB_LABEL_FR + "|" + SUB_LABEL_IT + ")"
# a label and at most a weekday in one table cell, directly before the date
CELL_LABEL_RX = re.compile(r"^" + SUB_LABEL + r" ?:?(?: " + WEEKDAY + r",?(?: den| le| il)?)?\Z")
# labels and lines that name the signers of a proposal (below the place and date line of the proposal)
SIGNER_LABEL_RX = re.compile(r"^(?:erstunterzeichne(?:r|nde)|mitunterzeichne(?:r|nde)|unterzeichne(?:r|nde)"
                             r"|erstunterzeichnerin|unterschriften|premiere? signataire|premiers signataires"
                             r"|signataires?|cosignataires?|prim[oa] firmatari[oa]|primi firmatari|cofirmatar[io]"
                             r"|firmatar[io])(?![a-z])")
SUB_LABEL_LINE_RX = re.compile(r"^" + SUB_LABEL + r" ?:?\Z")
SUB_LABEL_PRE_RX = re.compile(r"(?:^|(?<![a-z]))(?P<label>" + SUB_LABEL + r") ?(?P<colon>[:\t]?) ?(?:" + WEEKDAY +
                              r",? ?(?:den |le |il )?)?\Z")
# a label for the day of receipt. On a minute of the executive it is the stamp of the parliament office on the response.
RECEIPT_LABEL_RX = re.compile(r"^(?:eingang|eingegangen|posteingang|datum des eingangs|datum eingang"
                              r"|date de reception|recu|ricevut|data di ricezione)")
# the text after a date that ends the reference to a proposal ("vom 24. August 2020 mit dem Titel", "betreffend")
# after the date of a proposal heading: the response follows ("... (SVP) vom 17. Januar 2025; Beantwortung")
AFTER_RESP_RX = re.compile(r"^ ?; ?(?:beantwortung|antwort|stellungnahme|reponse|risposta)(?![a-z])")
# a signed date in the tail of a proposal: names before the date, or a comma and names after it
SIGNED_PRE_RX = re.compile(r"^[a-z][a-z .'-]{2,40},(?: [a-z][a-z .'/-]{1,30},)? \Z")
SIGNED_POST_RX = re.compile(r"^,(?: [a-z][a-z .'-]{2,40}[,.]?){1,6}\Z")
AFTER_TITLE_RX = re.compile(r"^ (?:(?:betreffend|betr\.?|mit dem titel|concernant|intitulee?s?|concernente|dal titolo"
                            r"|riguardante)(?![a-z])|\")")        # also a title in quotation marks directly after the date
# a dispatch of the executive with its date at a line start ("Bericht und Antrag vom", "Weisung vom", "Messaggio n. 8327 del")
MEMO_LABEL_RX = re.compile(r"^(?:pour|a|copie a|copies a|an|kopie an|geht an|per|a l'attention de) ?:\Z")
DISPATCH_INITIAL_RX = re.compile(r"^(?:bericht und antrag|weisung|botschaft|vorlage|ratschlag|ausgabenbericht|message"
                                 r"|messaggio)(?![a-z])")
# the address line of a letter to the parliament ("An den Grossen Rat", "Au Grand Conseil", "Al Gran Consiglio")
PARL_ADDRESS_RX = re.compile(r"^(?:an (?:den|das|die) (?:grossen rat|grossen gemeinderat|grossen stadtrat|landrat|kantonsrat"
                             r"|einwohnerrat|stadtparlament|gemeindeparlament|parlament|landtag)"
                             r"|au (?:grand conseil|conseil general|conseil de ville)"
                             r"|al (?:gran consiglio|consiglio comunale))(?![a-z])")
DISPATCH_PRE_RX = re.compile(r"^(?:[0-9][0-9.]{3,14},? )?(?:bericht und antrag|weisung|botschaft|vorlage|ratschlag"
                             r"|ausgabenbericht|message|messaggio|messaggio municipale)"
                             r"(?: des (?:rr|sr|gr|" + BODY + r"))?"
                             r"(?: (?:nr|no|n)\.? ?[0-9][0-9a-z./-]*)? (?:vom|du|del) \Z")
LABEL_ONLY_RX = re.compile(r"^(?:titolo|titre|titel|oggetto|objet|betreff|betrifft)\Z")
PREP_END_RX = re.compile(r"(?:^|[ (])(?:vom|du|del|dell'|della|datee? du|in data|di data|en date du)[ (]*\Z")
NEAR_BETWEEN_RX = re.compile(r"^(?:[ ,.:()-]|n[ro]?\.? ?[0-9./-]+|[0-9./-]+)*(?:vom|du|del|dell'|della|in data)?[ (]*\Z")
INITIAL_TYPE_RX = re.compile(r"^[^a-z0-9]{0,3}(?:[0-9][0-9a-z./ -]{0,12} )?(?:eingereichte[rsn]?,? )?"
                             r"(?:a l'|au |a la |aux |zur |zum |all'|alla |al |sull'|sulla |sul )?"
                             r"(?:dringliche[rs]? |urgente? |interfraktionelle[rs]? |uberparteiliche[rs]? )?" + TYPE_WORD)
RESP_INITIAL_RX = re.compile(r"^[^a-z0-9]{0,3}" + RESP_NOUN + r"(?![a-z])")
FAR_STOP_RX = re.compile(r"sitzung|seance|seduta|gesetz|verordnung|reglement|(?<![a-z])loi(?![a-z])|legge|protokoll|anhorung"
                         r"|beratung|audition|debatte|behandlung|uberwiesen|antrag|" + BODY)
AM_LABEL_RX = re.compile(r"^am ?: ?\Z")
STANDALONE_PRE_RX = re.compile(r"^\(? ?(?:vom|du|del|dell'|della)? ?\Z")
PLACE_STOP_RX = re.compile(r"(?<![a-z])(?:" + WEEKDAY + r"|datum|date|data|vom|versand|versandt|stand|sitzung"
                           r"|seance|seduta|seite|page|pagina|version|eingang|bericht|antwort|beschluss|gesetz"
                           r"|bis|ab|seit|und|et|ed)(?![a-z])")
PLACE_PRE_RX = re.compile(r"^(?:[0-9]{4} )?[a-z][a-z.'/-]*(?:[ -][a-z][a-z.'/-]*){0,3},(?: den| le| il| li)? ?\Z")
# "<place> <date>" with no comma: one word of 4 or more letters ("Nidau 18. Juni 2015", "Mendrisio 12 febbraio 2016")
PLACE_PLAIN_PRE_RX = re.compile(r"^(?:[0-9]{4} )?(?P<word>[a-z]{4,})(?: den| le| il| li)? \Z")
# after the date of a place line: nothing, or a dash and a name ("Nidau, 23. Juni 2011 - A. Muster")
PLACE_POST_NAME_RX = re.compile(r"^ ?[-/] ?[a-z][a-z .'-]{2,40}\Z")
DATE_LABEL_PRE_RX = re.compile(r"^(?:datum|date|data) ?:? ?\Z")
MINUTE_CUE_RX = re.compile(r"(?:auszug aus dem protokoll|protokollauszug|extrait du proces[- ]verbal"
                           r"|estratto (?:del|dal) (?:verbale|protocollo)|protokoll (?:des|der) " + BODY + r")")
DECISION_NO_RX = re.compile(r"(?<![a-z])(?:beschluss[ -]?nr|beschluss[ -]?nummer|decision n|risoluzione n)")
SITTING_PRE_RX = re.compile(r"(?<![a-z])(?:sitzung vom|seance du|seduta del)[ :]*(?:" + WEEKDAY + r",? ?(?:den |le |il )?)?\Z")
SITTING_LINE_RX = re.compile(r"^(?:[0-9]+\. )?(?:sitzung vom|seance du|seduta del)[ :]*(?:" + WEEKDAY +
                             r",? ?(?:den |le |il )?)?\Z")
DE_ART = r"(?:des|der|du|de la|del|della|dello|de l'|dell'|durch den|durch die|par le|par la)"
SIG_PREFIX = (r"(?:im namen|namens|im auftrag|im auftrage|fur den|fur die|vor dem|au nom d[ue]|pour le|pour la"
              r"|per il|per la|a nome del|in nome del)")
# a response noun with the body word and then a date ("antwort des regierungsrates vom")
RESP_CUE_DATE_RX = re.compile(
    r"(?<![a-z])(?:(?P<noun>" + RESP_NOUN + r")(?: (?:" + DE_ART + r" )?(?P<nbody>" + BODY + r"|rr)(?: [a-z.'-]+){0,3}?)?"
    r"|(?P<dec>" + BODY + r"s?beschluss(?:es)?|rrb|srb|grb))"
    r"(?: (?:nr|no|n)\.? ?[0-9][0-9a-z./-]*)?[ ,:(]*(?P<prep>vom|du|del|della|dell'|,)[ (]*\Z")
APPROVAL_DATE_RX = re.compile(r"(?:approuvee?s?|adoptee?s?|validee?s?|genehmigt|verabschiedet|beschlossen|approvat[oa]|licenziat[oa])"
                              r"(?: [a-z]+){0,2}? (?:par le|par la|vom|durch den|durch die|dal|dalla) " + BODY +
                              r"(?: [a-z.'-]+){0,3}? (?:le|am|il|vom|du|del)[ (]*\Z")
DECISION_LABEL_RX = re.compile(r"^(?:(?:rrb|srb|grb|beschluss|ace|arrete)[ -]?(?:nr|nummer|no|n)?\.?|n ?[o°]? ?d'ace) ?:?\Z")
RESP_LABEL = (r"(?:datum(?: der)? beantwortung|beantwortet am|beantwortung vom|datum(?: der)? antwort"
              r"|date de(?: la)? reponse|data(?: della)? risposta)")
# the number and the date of a decision of the executive in a head or page head line ("RG n. 6322 del 15 dicembre 2021")
DECISION_NUMBER_LINE_RX = re.compile(r"^(?:rg|ris\.? ?mun\.?|risoluzione(?: governativa| municipale)?) (?:n|nr|no)\.? ?[0-9]+ del \Z")
# the body word of a minute cue names the parliament: a compound with a word for its president
# a different body makes a proposal to the body of the minute ("Gestützt auf den Antrag des Stadtrates")
PROPOSAL_OF_RX = re.compile(r"(?<![a-z])(?:antrag|bericht und antrag|weisung|botschaft|vorlage) (?:des|der) " + B)
# lines below a signature formula that make it the formula of a parliament ("Die Ratssekretärin:", "Präsidium",
# "Sekretariat", "Der Stadtratspräsident:")
PARLIAMENT_SIGNER_RX = re.compile(r"ratssekretar|parlamentssekretar|^(?:der|die) sekretar(?:in)? ?:?\Z|^sekretariat ?:?\Z"
                                  r"|^prasidium ?:?\Z|(?:stadtrats|gemeinderats|(?<![a-z])rats|parlaments)prasid(?:ent|ium)")
# a role line of the office of a parliament, 5 to 10 lines below a signature formula (digital signature blocks are
# between them): "Die Ratssekretärin", "Der Stv. Ratssekretär", "Die Leitung des Ratssekretariats"
PARLIAMENT_ROLE_LINE_RX = re.compile(r"^(?:(?:der|die|das) )?(?:stv\.? )?(?:rats|parlaments)sekretar(?:in)? ?:?\Z"
                                     r"|^(?:die )?leitung des (?:rats|parlaments)sekretariats ?:?\Z")
# a body takes note of the answer or the report of a different body: the first body is the parliament
# ("Der Stadtrat nimmt Kenntnis von der schriftlichen Antwort des Gemeinderats")
TAKES_NOTE_RX = re.compile(r"(?<![a-z])(?:der|die) " + B + r" nimmt kenntnis vo[nm] (?:der |dem )?(?:schriftlichen )?"
                           r"(?:antwort|beantwortung|bericht|prufungsbericht|stellungnahme) (?:des|der) (?P<other>" + BODY + r")")
# the head of a decision of a body: "Regierungsratsbeschluss vom", "Beschluss des Stadtrats", "Arrêté du Conseil d'Etat"
DECISION_HEAD_RX = re.compile(r"^(?:(?P<body>" + BODY + r")s?beschluss(?:es)?(?![a-z])"
                              r"|(?:beschluss|entscheid|decision|arrete|decisione|risoluzione) (?:des|der|du|de la|del|della) "
                              + B.replace("?P<body>", "?P<body2>") + r")")
# body words that are also common nouns: a specific body word in the same tier is better
GENERIC_BODY_KEYS = frozenset(("regierung", "gouvernement", "governo"))
TRANSFER_RX = re.compile(r"(?<![a-z])an (?:den|die) " + B + r"(?: [a-z]+){0,3}? (?:uberwiesen|uberweisen|zu uberweisen)(?![a-z])")
PARLIAMENT_COMPOUND = r"s?(?:prasident|vizeprasident)"
RESP_LABEL_PRE_RX = re.compile(r"(?:^|(?<![a-z]))" + RESP_LABEL + r" ?:? ?\Z")
RESP_LABEL_LINE_RX = re.compile(r"^" + RESP_LABEL + r" ?:?\Z")
THANKS_RX = re.compile(r"(?<![a-z])(?:bedanken|bedanke|danken|danke|dank|merci|remercie|remercions|remerciements|ringrazio"
                       r"|ringraziamo|ringraziando|grazie)(?![a-z])")
URGENCY_RX = re.compile(r"dringlichkeit|urgence|urgenza")
# the date of a numbered decision in a sentence ("con Risoluzione Municipale N. 4618 del 24 marzo 2026")
DECISION_NO_SENTENCE_RX = re.compile(r"(?:risoluzione|beschluss|decision|arrete)[a-z ]{0,25}(?:n|nr|no)\.? ?[0-9][0-9./-]* (?:del|vom|du) \Z")
DECISION_NO_PRE_RX = re.compile(r"^(?:nr\.? ?)?[0-9]{1,5}[/.-][0-9]{2,4} (?:vom|du|del) \Z")
PARLIAMENT_RX = re.compile(r"(?<![a-z])(?:landrat|kantonsrat|grosser rat|grossen rat|einwohnerrat|parlament|stadtparlament"
                           r"|landtag|grand conseil|conseil general|conseil de ville|gran consiglio|consiglio comunale)")
RESP_NOUN_BODY = (r"(?:antwort|beantwortung|stellungnahme|bericht und antrag|bericht|reponse|prise de position|rapport"
                  r"|determination|risposta|osservazioni|presa di posizione|rapporto"
                  r"|a n t w o r t|r e p o n s e|r i s p o s t a)")       # also a heading with spaces between the letters
RESPONSE_PHRASES = (
    re.compile(r"(?<![a-z])" + RESP_NOUN_BODY + r"(?: [a-z]+){0,2}? " + DE_ART + " " + B),
    re.compile(r"(?<![a-z])(?:auszug aus dem protokoll|protokollauszug|protokoll|extrait du proces[- ]verbal)"
               r"(?: [a-z]+){0,3}? (?:des|der|du|del)? ?" + B),
    re.compile(B + r" (?:beantwortet|antwortet|nimmt(?: [a-z,.()0-9'-]+){0,14}? stellung|repond|risponde|si pregia"
               r"|unterbreitet|erstattet|erteilt (?:folgende|die) antwort|ha deciso di rispondere"
               r"|a decide de repondre)(?![a-z])"),
    re.compile(r"(?<![a-z])(?:lo scrivente|il sottoscritto) " + B),
)
ANSWER_PHRASES = (RESPONSE_PHRASES[0], RESPONSE_PHRASES[2], RESPONSE_PHRASES[3])     # the body answers
MINUTE_PHRASE_RX = RESPONSE_PHRASES[1]                                              # a minute of the body
ADDRESSEE_PHRASES = (
    re.compile(r"(?<!buro des )(?<!buro der )" + B + r" (?:wird|werden|sei|ist)(?: [a-z,.'-]+){0,5}? (?:beauftragt|ersucht|gebeten|eingeladen"
               r"|aufgefordert|angefragt)(?![a-z])"),
    re.compile(r"(?<![a-z])(?:beauftragt|beauftragen|ersucht|ersuchen|bittet|bitten|fragt|fragen|laden|ladet)"
               r"(?: wir| ich)? (?:den|die|das) " + B),
    re.compile(r"(?<![a-z])(?:lodevole|onorevole|spettabile|egregio) " + B),
    re.compile(r"(?<![a-z])(?:chiedo|chiediamo|chiede|chiedono|interrogo|interroghiamo|interpello|interpelliamo|invito"
               r"|invitiamo)(?: [a-z,.'-]+){0,4}? (?:il|al|lo|allo) " + B),
    re.compile(r"(?<![a-z])(?:le|la) " + B + r" est (?:prie|charge|invite|priee|chargee|invitee)(?![a-z])"),
    re.compile(r"(?<![a-z])(?:demande|demandons|demandent|prie|prions|prient|invite|invitons|invitent|charge"
               r"|chargeons|chargent)(?: [a-z,.'-]+){0,3}? (?:le|la|au|a la) " + B),
    re.compile(r"(?<![a-z])fragen an (?:den|die) " + B),
    re.compile(r"(?<![a-z])(?:bitte|bitten|ersuche) (?:den|die) " + B),
    re.compile(r"(?<![a-z])(?:stellen wir|stelle ich|stellt) (?:dem|der) " + B),
    re.compile(r"(?<![a-z])(?:wird|werden) (?:der|die) " + B + r"(?: [a-z,.'-]+){0,5}? (?:beauftragt|ersucht|gebeten"
               r"|eingeladen|aufgefordert)(?![a-z])"),
    re.compile(r"(?<![a-z])(?:der|die) " + B + r" (?:soll|solle|moge|wolle)(?![a-z])"),
    re.compile(TYPE_WORD + r" an (?:den|die) " + B),
    re.compile(r"(?<![a-z])ist (?:der|die) " + B + r" bereit(?![a-z])"),
    re.compile(r"(?<![a-z])(?:plant|will|gedenkt|beabsichtigt|erachtet|wie beurteilt|was gedenkt|wie stellt sich)"
               r" (?:der|die) " + B),
    re.compile(r"(?<![a-z])(?:chiedere|si chiede|domandare|domandiamo|domando) (?:al|allo|alla) " + B),
    re.compile(r"(?<![a-z])(?:intende|non ritiene|ritiene|e disposto|come valuta|come giudica) (?:il|lo) " + B),
    re.compile(r"(?<![a-z])(?:que pense|qu'en pense|comment) (?:le|la) " + B),
    re.compile(r"(?<![a-z])(?:le|la) " + B + r" (?:peut|a|est|entend|envisage|compte|pense|prevoit)[ -]t?[ -]?(?:il|elle)(?![a-z])"),
    re.compile(r"(?<![a-z])(?:demande|demandons|demandent) (?:au|a la) " + B),
    re.compile(r"(?<![a-z])(?:posees?|adressees?|soumises?) (?:au|a la) " + B),
    re.compile(r"(?<![a-z])(?:rivolt[aeio]|post[aeio]|indirizzat[aeio]) (?:al|allo|alla) " + B),
    re.compile(r"(?<![a-z])(?:gerichtet|gestellt) an (?:den|die) " + B),
)
SIG_FORMULA_RX = re.compile(r"^" + SIG_PREFIX + r"(?: [a-z,.'-]+){0,4}? " + B)
BODY_ARTICLE_LINE_RX = re.compile(r"^(?:der|die|le|la|il|lo) " + B + r" ?:?\Z")
# "<Stadt|Gemeinde|Kanton> <place> <body word>" in a page head or page foot ("Stadt Kriens Stadtrat")
BODY_PAGE_LINE_RX = re.compile(r"^(?:stadt|gemeinde|kanton|ville de|commune de|canton de|comune di|citta di|cantone)"
                               r" [a-z.'-]+(?: [a-z.'-]+)? " + B + r"\Z")
# lines before a body word line that make it a part of an address ("An den Stadtrat und", "die Mitglieder des")
ADDRESS_PRE_RX = re.compile(r"^(?:an (?:den|die|das)|zuhanden|z\. ?h(?:d)?\.|a l'attention|aux?|alla?|all'|ai)(?![a-z])"
                            r"|(?:mitglieder|membres|membri|buro|bureau|ufficio|prasident(?:in)?|presidente?) (?:des|der|du|del)\Z")
ADDRESS_WORD_RX = re.compile(r"^(?:lodevole|onorevole|spettabile|egregi[oa]?|an|a|al|alla|au|aux)\Z")
POSTAL_LINE_RX = re.compile(r"^(?:ch-)?[0-9]{4} [a-z]")
# lines after a body word line that make it the sender block of a letter
SENDER_POST_RX = re.compile(r"^(?:e-?mail|telefon|tel\.?|fax|www\.|postfach|case postale|casella postale|[0-9]{4} [a-z])")
BODY_LINE_RX = re.compile(r"^(?:der |die |le |la |il |lo )?" + B + r"(?: (?:des kantons|der stadt|der gemeinde|von|de la"
                          r" ville de|de la commune de|de|du|di|del comune di|della citta di) [a-z.'-]+(?: [a-z.'-]+){0,2}"
                          r"| [a-z][a-z.'-]{3,}(?: [a-z.'-]+){0,2})? ?:?\Z")
ARTICLE_BODY_RX = re.compile(r"(?<![a-z])(?:der|le|il|lo) " + B)


# ------------------------------------------------------------------ view of one document

class View:
    """The folded text of a document with the dates and the lines in folded positions. Made one time for a Doc."""

    def __init__(self, doc: vb.Doc):
        self.doc = doc
        f = vb.fold_map(doc.text, 0, keep_newlines=True, dehyphen=True)
        self.f = f
        self.nl = f.text                          # folded text, a line end is "\n"
        self.sp = f.text.replace("\n", " ")       # the same positions, a line end is a space
        self.index = f.index
        n = len(doc.lines)
        self.n = n
        self.dates = []                           # dict for each date, in reading order
        for h in doc.dates():
            fs = bisect_left(self.index, h.start)
            fe = bisect_left(self.index, h.end)
            ls = self.nl.rfind("\n", 0, fs) + 1
            le = self.nl.find("\n", fe)
            le = len(self.nl) if le < 0 else le
            ln = doc.line_at(h.start)
            blk = doc.locate(h.start)
            self.dates.append({"h": h, "fs": fs, "fe": fe, "line": ln.number, "label": blk.label, "page": ln.page,
                               "pre_line": self.nl[ls:fs], "post_line": self.nl[fe:le],
                               "raw_pre": doc.text[ln.char_start:h.start],
                               "pre": self.sp[max(0, fs - 320):fs], "ls": ls})
        self.lines = [vb.fold(ln.text) for ln in doc.lines]
        self.line_label = [doc.blocks[ln.block_index].label for ln in doc.lines]
        self.memo: dict = {}                      # results of tests on the whole document

    def span(self, m: re.Match, group: str | int = 0) -> tuple[int, int]:
        return self.f.match_span(m, group)

    def fpos(self, pos: int) -> int:
        return bisect_left(self.index, pos)

    def head_end(self, n_lines: int) -> int:
        """Folded position of the end of line n_lines - 1 (or of the document)."""
        if not self.doc.lines:
            return 0
        ln = self.doc.lines[min(n_lines, self.n) - 1]
        return self.fpos(ln.char_end)

    def tail_start(self, n_lines: int) -> int:
        if not self.doc.lines:
            return 0
        ln = self.doc.lines[max(self.n - n_lines, 0)]
        return self.fpos(ln.char_start)


def view(doc: vb.Doc) -> View:
    v = getattr(doc, "_m11_t7_view", None)
    if v is None or v.doc is not doc:
        v = View(doc)
        doc._m11_t7_view = v
    return v


def _own_response_cue(v: View) -> bool:
    """A cue test for a document with no rule file: a response phrase in the head or a signature formula of the
    executive in the tail."""
    head = v.sp[:v.head_end(30)]
    if any(rx.search(head) for rx in RESPONSE_PHRASES):
        return True
    return any(i >= v.n - TAIL_LINES for i, _ in _signature_formulas(v))


def _minute_line(v: View) -> int | None:
    """The number of the first line of page 1 that starts with a minute cue of the executive and is not in a table.
    None if no line does, or if the cue is "Protokoll der <n>. Sitzung" (a minute of a parliament)."""
    if "minute_line" not in v.memo:
        hit = None
        for i, t in enumerate(v.lines[:120]):
            if v.doc.lines[i].page != 1:
                break
            if MINUTE_CUE_RX.match(t.strip()) and v.line_label[i] != "table":
                hit = i
                break
        if hit is not None and re.search(r"protokoll der [0-9]+\.", " ".join(v.lines[hit:hit + 3])):
            hit = None
        v.memo["minute_line"] = hit
    return v.memo["minute_line"]


def _minute_head(v: View) -> bool:
    """One of the first 12 lines starts with a minute cue of the executive, and the line is not in a table."""
    k = _minute_line(v)
    return k is not None and k < 12


def _signature_formulas(v: View) -> list[tuple[int, re.Match]]:
    """(line number, match) of each line of the document that is a signature formula of the executive: the formula
    starts the line, and each word after the body word is a link word or starts with a capital letter in print
    ("NAMENS DES STADTRATES FRAUENFELD"; not "Für den Gemeinderat ist es von grösster Bedeutung")."""
    if "sig" not in v.memo:
        got, parl = [], []
        for i, raw in enumerate(v.lines):
            if v.line_label[i] == "footnote":
                continue
            t = raw.strip()
            m = SIG_FORMULA_RX.match(t)
            if not m:
                continue
            k = len(t[m.end("body"):].strip(" :,.").split())
            words = v.doc.lines[i].text.strip(" :,.").split()[-k:] if k else []
            if k > 5 or not all(w.lower() in LINK_WORDS or w[:1].isupper() for w in words):
                continue
            if (any(PARLIAMENT_SIGNER_RX.search(x.strip()) for x in v.lines[i + 1:i + 5])
                    or any(PARLIAMENT_ROLE_LINE_RX.match(x.strip()) for x in v.lines[i + 5:i + 11])
                    or body_key(m.group("body"))[0] in _note_taking_bodies(v)):
                parl.append(i)  # the formula of a parliament
                continue
            got.append((i, m))
        v.memo["sig"] = got
        v.memo["sig_parliament"] = parl
    return v.memo["sig"]


def _note_taking_bodies(v: View) -> set[str]:
    """Keys of the body words that the document shows as the parliament: the body takes note of the answer or the
    report of a different body ("Der Stadtrat nimmt Kenntnis von der schriftlichen Antwort des Gemeinderats")."""
    if "note_bodies" not in v.memo:
        got = set()
        for x in TAKES_NOTE_RX.finditer(v.sp):
            a, b = body_key(x.group("body")), body_key(x.group("other"))
            if a and b and a[0] != b[0]:
                got.add(a[0])
        v.memo["note_bodies"] = got
    return v.memo["note_bodies"]


def parliament_decision_form(v: View) -> bool:
    """The document is a decision of the parliament: a signature formula with a signer of the parliament below it
    ("Namens des Stadtrats", "Der Präsident", "Die Ratssekretärin"), or a body that takes note of the answer of a
    different body. The dates of such a document are the day of the meeting and the day of the signature. They
    are not the day of a proposal and not the day of a response."""
    _signature_formulas(v)
    return bool(v.memo["sig_parliament"]) or bool(_note_taking_bodies(v))


def _tail_body_signature(v: View) -> list[tuple[int, int]]:
    """(line of the date, line of the body word) for each signature of the executive at the end of a letter: a
    line "<place>, <date>" after line 12 and, at most 2 lines below it, a line that holds only the body word with
    at most an article, link words and one place word ("Riehen, 23. April 2024" then "Gemeinderat Riehen";
    "Bern, 14. August 2002" then "Der Gemeinderat"). A body word with 2 words after it can be a title and a name
    of a person: it does not count."""
    if "tail_body_sig" not in v.memo:
        got = []
        for d in _letter_lines(v, range(12, v.n)):
            k = d["line"]
            for j in range(k + 1, min(k + 3, v.n)):
                m = _body_line(v, j)
                if not m:
                    continue
                extra = [w for w in v.lines[j][m.end("body"):].strip(" :").split() if w not in LINK_WORDS]
                # the body word in an address block is the addressed body ("Kloten, 20. April 2017", "Gemeinderat
                # Stadt Kloten", "Ratsleitung", "Stadthaus", "8302 Kloten"; "Lodevole", "Municipio")
                address = (any(ADDRESS_PRE_RX.search(t.strip()) or ADDRESS_WORD_RX.match(t.strip())
                               for t in v.lines[max(0, j - 2):j])
                           or any(POSTAL_LINE_RX.match(t.strip()) for t in v.lines[j + 1:j + 5]))
                if len(extra) <= 1 and not address:
                    got.append((k, j))
                    break
        v.memo["tail_body_sig"] = got
    return v.memo["tail_body_sig"]


def executive_form(v: View) -> bool:
    """The document has the form of a document of the executive: a minute cue starts one of the first 12 lines, a
    line is a signature formula of the executive, or a letter ends with a place and date line directly above a
    line that holds only the body word."""
    return (_minute_head(v) or bool(_signature_formulas(v)) or bool(_tail_body_signature(v))
            or executive_letter_form(v))


def executive_letter_form(v: View) -> bool:
    """The head of a letter of the executive to the parliament: one of the first 6 lines is an address line of
    the parliament ("An den Grossen Rat"), and one of the 3 lines before it holds only the body word
    ("Regierungsrat des Kantons Basel-Stadt", "Der Regierungsrat des Kantons Thurgau")."""
    if "exec_letter" not in v.memo:
        v.memo["exec_letter"] = any(PARL_ADDRESS_RX.match(t.strip()) and any(_body_line(v, j) for j in range(max(0, i - 3), i))
                                    for i, t in enumerate(v.lines[:6]))
    return v.memo["exec_letter"]


def _type_heading(v: View) -> bool:
    """One of the first 12 lines starts with a proposal type word."""
    return any(INITIAL_TYPE_RX.match(t) for t in v.lines[:12])


def proposal_form(v: View) -> bool:
    """The head has the form of a proposal: the first 25 lines hold a proposal type word, and none of the first 15
    lines starts with a response noun ("Bericht und Antrag an das Stadtparlament", "Rapport", "Mitteilung")."""
    if "proposal_form" not in v.memo:
        head = " ".join(v.lines[:25])
        # a heading with spaces between the letters ("P O S T U L A T") is read as one word
        head = re.sub(r"(?<![a-z])(?:[a-z] ){4,}[a-z](?![a-z])", lambda x: x.group(0).replace(" ", ""), head)
        v.memo["proposal_form"] = ((bool(TYPE_RX.search(head)) or any(rx.search(head) for rx in ADDRESSEE_PHRASES))
                                   and not any(RESP_INITIAL_RX.match(t) for t in v.lines[:15]))
    return v.memo["proposal_form"]


def is_response_document(doc: vb.Doc) -> bool:
    """S1 role response or combined. Also S1 role proposal with the form of a document of the executive (the S1
    role has errors). With no rule file: the cue test of this file."""
    v = view(doc)
    if doc.s1_role is None:
        return _own_response_cue(v)
    if doc.s1_role in ("response", "combined") or (doc.s1_role == "proposal" and executive_form(v)):
        return True
    # a letter of the executive to the parliament with a proposal of a member in its head is the response to it
    return executive_letter_form(v) and _type_heading(v)


def is_proposal_document(doc: vb.Doc) -> bool:
    """S1 role proposal from a rule with no condition on export fields, and the document has the form of a proposal
    and not the form of a document of the executive. With no rule file: no response cue and the form of a
    proposal."""
    v = view(doc)
    if parliament_decision_form(v):
        return False
    if doc.s1_role is None:
        return not _own_response_cue(v) and proposal_form(v)
    if doc.s1_role != "proposal":
        return False
    return proposal_form(v) and not executive_form(v)


def holds_response(doc: vb.Doc) -> bool:
    """The document holds a response: S1 role response or combined, or a response block of the rules mode."""
    return is_response_document(doc) or doc.first_response_block() is not None


def _refused(d: dict) -> str | None:
    """The cause if the context directly before the date is a law, a meeting or a footer word."""
    if d["label"] in SKIP_LABELS:
        return "footer_block"
    pre = d["pre"][-110:]
    if LAW_PRE_RX.search(pre):
        return "law"
    if MEETING_PRE_RX.search(pre):
        return "meeting"
    if FOOT_PRE_RX.search(pre):
        return "footer_word"
    if re.search(WEEKDAY + r"(?: \([a-z]+\))?,? ?(?:den |le |il )?\Z", pre):
        return "weekday"
    m = RESP_CUE_DATE_RX.search(pre)
    if m and (m.group("nbody") or m.group("dec")) and not TYPE_RX.search(pre[m.start():]):
        return "response_cue"
    return None


def _stacked_meeting_label(v: View, d: dict) -> bool:
    """The date is on a value line below label lines, and one of the 3 lines before it is a label for a meeting."""
    k = d["line"]
    return any(t.endswith(":") and re.search(r"sitzung|seance|seduta", t) for t in v.lines[max(0, k - 3):k])


def _is_place_line(v: View, d: dict) -> bool:
    """The line is "<place>, <date>": 1 to 5 words that start with a capital letter in print, then a comma or
    "den", "le", "il", then the date and no more text (the same date a second time is permitted)."""
    pre, post = d["pre_line"], d["post_line"].strip(" .")
    if post and post != vb.fold(d["h"].wording) and not PLACE_POST_NAME_RX.match(d["post_line"]):
        return False
    if PLACE_STOP_RX.search(pre):
        return False
    if not PLACE_PRE_RX.match(pre):
        m = PLACE_PLAIN_PRE_RX.match(pre)
        if not m or m.group("word") in vb.MONTHS or TYPE_RX.search(pre) or RESP_NOUN_RX.search(pre) or post:
            return False
    ln = v.doc.lines[d["line"]]
    first = ln.text.lstrip(" 0123456789")[:1]
    return first.isupper()


def _is_date_only_line(d: dict) -> bool:
    pre, post = d["pre_line"].strip(" _.:-"), d["post_line"].strip(" .")
    # before the date: no text (marks of a form line are permitted: "__08.05.2026"). After the date: no text, or a file number ("20 dicembre 2019 / 212.19", "12. Juni 2025 2025-257")
    return not pre and (not post or bool(re.match(r"^/? ?[0-9][0-9a-z./ -]{0,19}\Z", post)))


def _cand(doc: vb.Doc, field: str, d: dict, tier: str, cue: str) -> tuple:
    h = d["h"]
    return (h.start, h.end, h.iso, tier, {"cue": cue, "line": d["line"]})


# ------------------------------------------------------------------ submission date

def _sub_label(v: View) -> list[tuple]:
    out = []
    doc = v.doc
    by_line: dict[int, list[dict]] = {}
    for d in v.dates:
        by_line.setdefault(d["line"], []).append(d)
    # on a minute of the executive a receipt label is the stamp on the response, not the day of the proposal
    receipt_off = any(MINUTE_CUE_RX.match(t.strip()) for t in v.lines[:80])
    for d in v.dates:
        if d["line"] >= 80 or d["page"] > 2 or d["label"] in SKIP_LABELS:
            continue
        m = SUB_LABEL_PRE_RX.search(d["pre_line"])
        if m and receipt_off and RECEIPT_LABEL_RX.match(m.group("label")):
            continue
        if m and (m.start() == 0 or m.group("colon")):
            out.append(_cand(doc, "submission_date", d, "sub_label_cue", "label and date on one line"))
            continue
        # the label starts a table cell and the date is directly after it ("... <tab>Date du dépôt 17.10.2023 ..."),
        # or the label fills a table cell and the date starts the next cell
        cells = d["raw_pre"].split("\t")
        if len(cells) > 1:
            here, before = vb.fold(cells[-1]), vb.fold(cells[-2])
            hit = CELL_LABEL_RX.match(here) or (not here and CELL_LABEL_RX.match(before))
            if hit and not (receipt_off and RECEIPT_LABEL_RX.match(hit.group(0))):
                out.append(_cand(doc, "submission_date", d, "sub_label_cue", "label and date in a table cell"))
                continue
        # "eingereicht von: <name>" and then "am: <date>" (the label "am:" on the date line or on the line before)
        k = d["line"]
        am = AM_LABEL_RX.match(d["pre_line"]) or (_is_date_only_line(d) and k > 0 and AM_LABEL_RX.match(v.lines[k - 1]))
        if am and any(t.startswith("eingereicht") for t in v.lines[max(0, k - 6):k]):
            out.append(_cand(doc, "submission_date", d, "sub_label_cue", "label 'am:' below 'eingereicht von:'"))
    # a label line with the date on a later value line; label lines between them are permitted
    for i, t in enumerate(v.lines[:80]):
        if not SUB_LABEL_LINE_RX.match(t) or v.line_label[i] in SKIP_LABELS:
            continue
        if receipt_off and RECEIPT_LABEL_RX.match(t):
            continue
        # the label is the first line of a stack of label lines ("Eingereicht am:", "Eingereicht von:", ...): the
        # first value line below the stack is its value. Else at most 3 label lines are between label and date.
        first_of_stack = t.endswith(":") and not (i > 0 and v.lines[i - 1].endswith(":"))
        for j in range(i + 1, min(i + (9 if first_of_stack else 4), v.n)):
            ds = by_line.get(j)
            if ds and _is_date_only_line(ds[0]) or (ds and ds[0]["post_line"].strip(" .") == vb.fold(ds[0]["h"].wording)
                                                   and not ds[0]["pre_line"].strip()):
                out.append(_cand(doc, "submission_date", ds[0], "sub_label_cue", "label line, date on a value line"))
                break
            tj = v.lines[j]
            # a line between must be a label with no date word, else the search stops. A label is a line that ends
            # with a colon, or (in the first 3 lines) a line of 1 to 3 words with no digit and no full stop.
            short = j < i + 4 and bool(re.match(r"^[a-z][a-z.'/-]*(?: [a-z][a-z.'/-]*){0,2}\Z", tj)) and not tj.endswith(".")
            if not (tj.endswith(":") or short) or re.search(r"datum|date|data|sitzung|seance|seduta|vom", tj):
                break
    out.sort(key=lambda c: c[0])
    return out


def _cell_date(v: View, by_line: dict, j: int, k: int) -> dict | None:
    """The date that starts table cell k of line j (cells are the parts of the line between tab characters)."""
    if not 0 <= j < v.n:
        return None
    ln = v.doc.lines[j]
    cells = ln.text.split("\t")
    if len(cells) <= k:
        return None
    start = ln.char_start + sum(len(c) + 1 for c in cells[:k])
    start += len(cells[k]) - len(cells[k].lstrip())
    return next((d for d in by_line.get(j, ()) if d["h"].start == start), None)


def _sub_label_table(v: View) -> list[tuple]:
    """A head table with a row of labels and a row of values: a cell of the label row holds only a label of the
    submission date, and the cell with the same number in the next row starts with a date ("N° de l'objet <tab>
    Date du dépôt <tab> Heure du dépôt" then "23.054 <tab> 24.10.2023 <tab> 10:12"). A table that has a date in
    this cell of 2 rows is a list of items: it gives no candidate."""
    out = []
    doc = v.doc
    by_line: dict[int, list[dict]] = {}
    for d in v.dates:
        by_line.setdefault(d["line"], []).append(d)
    receipt_off = any(MINUTE_CUE_RX.match(t.strip()) for t in v.lines[:80])
    for i in range(min(80, v.n - 1)):
        ln = doc.lines[i]
        if ln.page > 2 or v.line_label[i] in SKIP_LABELS or "\t" not in ln.text:
            continue
        for k, cell in enumerate(ln.text.split("\t")):
            f = vb.fold(cell)
            if not SUB_LABEL_LINE_RX.match(f) or (receipt_off and RECEIPT_LABEL_RX.match(f)):
                continue
            d = _cell_date(v, by_line, i + 1, k)
            if d is not None and _cell_date(v, by_line, i + 2, k) is not None:
                return []       # a list of items
            if d is not None:
                out.append(_cand(doc, "submission_date", d, "sub_label_table", "label row and value row of a table"))
    if len({c[2] for c in out}) > 1:
        return []               # 2 tables with different days: a list of items
    return out


def _sub_signers(v: View) -> list[tuple]:
    """The place and date line of a proposal directly above the lines of its signers: one of the 2 lines below it
    starts with a signer label ("Erstunterzeichnende:", "Mitunterzeichnende:", "Premier signataire", "Primo
    firmatario"), or (after line 12) the line below it starts with a type word, a name and a party in parentheses
    ("Bern, 9. Juni 2005" then "Motion A. Muster (SP); B. Muster, ...")."""
    out = []
    for d in _letter_lines(v, range(0, v.n)):
        k = d["line"]
        nxt = [t.strip() for t in v.lines[k + 1:k + 3]]
        label = any(SIGNER_LABEL_RX.match(t) for t in nxt)
        typed = bool(k >= 12 and nxt and INITIAL_TYPE_RX.match(nxt[0])
                     and re.match(r"^[^(]{3,80}\([^)]{1,40}\)", nxt[0]) and not RESP_NOUN_RX.search(nxt[0]))
        if label or typed:
            out.append(_cand(v.doc, "submission_date", d, "sub_signers_date", "place and date line above the signers"))
    return out


def _short_year(d: dict) -> bool:
    """A numeric date with a year of 2 digits ("25.01.03"). Such a string can be a file number."""
    return bool(re.match(r"^[0-9]{1,2} ?[./] ?[0-9]{1,2} ?[./] ?[0-9]{2}\Z", d["h"].wording.strip()))


def _type_context(v: View, d: dict, back: int) -> dict:
    """The last proposal type word in the `back` lines before the date line and in the date line up to the date.
    A line that holds only a label word (Titolo, Titre, Titel, Betreff) is left out.
    between: the folded text from the type word to the date. initial: the line of the type word starts with the
    type word or with a response noun. resp_before: a response noun is before the type word."""
    k = d["line"]
    lines = [t for t in v.lines[max(0, k - back):k] if not LABEL_ONLY_RX.match(t.strip(" :"))] + [d["pre_line"]]
    for i in range(len(lines) - 1, -1, -1):
        ms = list(TYPE_RX.finditer(lines[i]))
        if not ms:
            continue
        m = ms[-1]
        before = " ".join(lines[:i] + [lines[i][:m.start()]])
        return {"has_type": True, "between": " ".join([lines[i][m.end():]] + lines[i + 1:]),
                "initial": bool(INITIAL_TYPE_RX.match(lines[i]) or RESP_INITIAL_RX.match(lines[i])),
                "resp_before": bool(RESP_NOUN_RX.search(before)), "window": " ".join(lines)}
    return {"has_type": False, "between": "", "initial": False, "resp_before": False, "window": " ".join(lines)}


def _sub_type_date(v: View) -> dict:
    """Candidates by the type word before the date: keys near, far, inline (submission date) and resp (dates of a
    response heading, for the response date)."""
    out = {"near": [], "far": [], "inline": [], "resp": []}
    doc = v.doc
    for d in v.dates:
        if d["line"] >= 25 or d["page"] > 1 or _refused(d):
            continue
        standalone = bool(STANDALONE_PRE_RX.match(d["pre_line"])) and not d["post_line"].strip(" .)")
        own_prep = standalone and bool(d["pre_line"].strip(" ("))
        c = _type_context(v, d, 12 if standalone else 5)
        between = c["between"]
        if c["has_type"] and NEAR_BETWEEN_RX.match(between):
            prep = bool(PREP_END_RX.search(between))
            verb_after = bool(VERB_POST_RX.match(d["post_line"]))      # "iniziativa 17 ottobre 2022 presentata da"
            if not prep and not verb_after and (_short_year(d) or c["resp_before"] or _stacked_meeting_label(v, d)):
                continue        # a date with no preposition below a response heading can be the date of the response
            if not c["initial"] and not prep and not verb_after:
                continue
            if c["initial"]:
                out["near"].append(_cand(doc, "submission_date", d, "sub_type_date_near", "type word directly before the date"))
            else:
                out["inline"].append(_cand(doc, "submission_date", d, "sub_type_date_inline",
                                           "type word in running text directly before the date"))
            continue
        if own_prep and RESP_NOUN_RX.search(c["window"]) and (not c["has_type"] or c["resp_before"]):
            # "(Du 19 février 2024)" below a response heading: the date of the response
            out["resp"].append(_cand(doc, "response_date", d, "resp_heading_date", "date line below a response heading"))
            continue
        resp_after = bool(AFTER_RESP_RX.match(d["post_line"]))
        if not c["has_type"] or not c["initial"] or len(between) > (500 if resp_after else 300):
            continue
        if RESP_NOUN_RX.search(between) or FAR_STOP_RX.search(between):
            continue
        # after the date: the line end or ; ) : (a comma only if the type word is at most 80 characters before)
        after_ok = bool(re.match(r"^ ?(?:\Z|[;).:]+(?: |\Z))", d["post_line"])) or (
            len(between) <= 80 and d["post_line"].startswith(",")) or bool(AFTER_TITLE_RX.match(d["post_line"]))
        if own_prep or (PREP_END_RX.search(between) and not standalone and after_ok
                        and (len(between) <= 250 or resp_after)):
            out["far"].append(_cand(doc, "submission_date", d, "sub_type_date_far", "type word and preposition before the date"))
    return out


def _sentence_bounds(text: str, pos: int) -> tuple[int, int]:
    """The sentence around a position of the folded text: from the last sentence end before it to the next one.
    The caller cuts the result to the block of the position.
    A full stop after a number or after a word of 1 to 3 letters is not a sentence end. At most 320 characters
    on each side."""
    lo, hi = max(0, pos - 320), min(len(text), pos + 320)
    start = lo
    for m in re.finditer(r"[.!?;] ", text[lo:pos]):
        before = re.search(r"([a-z0-9]+)\Z", text[lo:lo + m.start()])
        if text[lo + m.start()] == "." and before and (before.group(1).isdigit() or len(before.group(1)) <= 3):
            continue
        start = lo + m.end()
    end = hi
    for m in re.finditer(r"[.!?;](?: |\Z)", text[pos:hi]):
        before = re.search(r"([a-z0-9]+)\Z", text[pos:pos + m.start()])
        if text[pos + m.start()] == "." and before and (before.group(1).isdigit() or len(before.group(1)) <= 3):
            continue
        end = pos + m.start()
        break
    return start, end


def _sub_sentence(v: View, tier: str) -> tuple[list[tuple], list[tuple]]:
    """(candidates of the tier, candidates of sub_sentence_meeting)."""
    out, meet = [], []
    doc = v.doc
    for d in v.dates:
        if d["line"] >= HEAD_LINES or d["page"] > 2 or d["label"] in SKIP_LABELS:
            continue
        cause = _refused(d)
        if cause in ("law", "footer_word", "footer_block"):
            continue
        s, e = _sentence_bounds(v.sp, d["fs"])
        blk = doc.locate(d["h"].start)
        s, e = max(s, v.fpos(blk.char_start)), min(e, v.fpos(blk.char_end))      # a sentence stays in its block
        sent = v.sp[s:e]
        if not SUBMIT_VERB_RX.search(sent) or not TYPE_RX.search(sent):
            continue
        # the candidate of the sentence: the date directly after the submit verb ("presentata il 28 agosto 2018"),
        # else the first date that is not refused and is not the date of a response ("Risposta del 17 settembre 2018")
        ds = [x for x in v.dates if s <= x["fs"] < e and _refused(x) not in ("law", "footer_word", "footer_block")
              and not DECISION_NO_SENTENCE_RX.search(x["pre"][-60:])]
        pick = next((x for x in ds if VERB_PRE_RX.search(x["pre"][-60:])), None)
        if pick is None:
            pick = next((x for x in ds if not RESP_NOUN_PRE_RX.search(x["pre"][-40:])), None)
        if pick is not d:
            continue
        if cause == "meeting":      # "An der Sitzung vom 28. September 2019 reichten ... ein": the day of a meeting
            meet.append(_cand(doc, "submission_date", d, "sub_sentence_meeting",
                              "sentence with a submit verb; the date is the day of a meeting"))
        else:
            out.append(_cand(doc, "submission_date", d, tier, "sentence with a submit verb and a type word"))
    return out, meet


def _letter_lines(v: View, lines: range, with_label: bool = False, date_only: bool = False) -> list[dict]:
    got = []
    for d in v.dates:
        if d["line"] not in lines or d["label"] == "footnote":
            continue
        if _is_place_line(v, d):
            got.append(d)
        elif with_label and DATE_LABEL_PRE_RX.match(d["pre_line"]) and not d["post_line"].strip(" ."):
            got.append(d)
        elif (date_only and _is_date_only_line(d) and d["label"] not in SKIP_LABELS
              and not _stacked_meeting_label(v, d)):
            got.append(d)
    return got


def _is_date_line(d: dict) -> bool:
    """The line holds only the date (a file number after it is permitted), or only "vom", "du", "del" and the date."""
    return _is_date_only_line(d) or (bool(STANDALONE_PRE_RX.match(d["pre_line"])) and not d["post_line"].strip(" .)"))


def _is_signed_date_line(v: View, d: dict) -> bool:
    """The line holds only the date, or the date and then a name of 2 to 4 words that start with a capital letter in
    print ("17.3.2011 A. Muster")."""
    if _is_date_only_line(d):
        return True
    post = d["post_line"].strip()
    if SIGNED_PRE_RX.match(d["pre_line"]) and post in ("", ",", "."):
        return v.doc.lines[d["line"]].text.lstrip()[:1].isupper()       # "A. Muster, Stadtrat SVP, 17.09.2020"
    if not d["pre_line"].strip() and SIGNED_POST_RX.match(d["post_line"]):
        return True                                                    # "22.10.2025, A. Muster, B. Muster"
    if d["pre_line"].strip():
        return False
    k = len(d["post_line"].split())
    words = v.doc.lines[d["line"]].text.split()[-k:] if k else []
    return 2 <= k <= 4 and all(w[:1].isupper() and not any(c.isdigit() for c in w) for w in words)


def _retier(cands: list[tuple], tier: str) -> list[tuple]:
    return [(s, e, iso, tier, det) for s, e, iso, _, det in cands]


def submission_candidates(doc: vb.Doc) -> list[tuple]:
    """All candidates of the submission date in the tier order (start, end, iso, tier, detail)."""
    v = view(doc)
    proposal = is_proposal_document(doc)
    t = _sub_type_date(v)
    sent, sent_meet = _sub_sentence(v, "sub_sentence_other" if proposal else "sub_sentence_cue")
    # a response document prints the date of the proposal in its head: tiers of their own
    resp_doc = is_response_document(doc)
    label, near, far = _sub_label(v), t["near"], t["far"]
    if resp_doc:
        label = _retier(label, "sub_label_cue_resp")
        near = _retier(near, "sub_resp_head_near")
        far = _retier(far, "sub_resp_head_far")
    out = label + _sub_label_table(v) + near + _sub_signers(v)
    if resp_doc:            # the head of the response is before a sentence of its text
        out += far + sent
    else:
        if not proposal:
            out += sent
        out += far
    if not proposal:        # in a proposal such a phrase refers to a different proposal
        out += t["inline"] + sent_meet
    if proposal:
        out += [_cand(doc, "submission_date", d, "sub_letter_head", "place and date line in the head")
                for d in _letter_lines(v, range(0, 25), with_label=True) if d["page"] == 1]
        tail_from = max(v.n - 15, 25)
        tail = _letter_lines(v, range(tail_from, v.n), with_label=True)
        out += [_cand(doc, "submission_date", d, "sub_letter_tail", "place and date line in the tail")
                for d in reversed(tail)]
        ok = [d for d in v.dates if not _refused(d) and not _short_year(d) and not _stacked_meeting_label(v, d)]
        # a date line below the labels of a memo ("Date :", "Pour :", "Copie à :") is the date of the memo
        head = [d for d in ok if d["line"] < 15 and d["page"] == 1 and _is_date_line(d)
                and not any(MEMO_LABEL_RX.match(x.strip()) for x in v.lines[max(0, d["line"] - 4):d["line"]])]
        if len({d["h"].iso for d in head}) == 1:
            out.append(_cand(doc, "submission_date", head[0], "sub_head_date_line", "the only date line of the first 15 lines"))
        last = [d for d in ok if d["line"] >= max(v.n - 15, 15) and _is_signed_date_line(v, d)]
        out += [_cand(doc, "submission_date", d, "sub_tail_date_line", "date line in the tail") for d in last[-1:]]
        body = [d for d in _letter_lines(v, range(25, tail_from))]
        body.sort(key=lambda d: (d["page"] != 1, d["line"] if d["page"] == 1 else -d["line"]))
        out += [_cand(doc, "submission_date", d, "sub_letter_body", "place and date line between head and tail")
                for d in body[:1]]
        out += sent
    disp = [d for d in v.dates if d["line"] < 12 and d["page"] == 1 and d["label"] not in SKIP_LABELS
            and DISPATCH_PRE_RX.match(d["pre_line"])]
    if (not disp and not proposal and doc.s1_role not in ("response", "combined")
            and any(DISPATCH_INITIAL_RX.match(x) for x in v.lines[:15])):
        # the head of a dispatch of the executive ("Bericht und Antrag an den Einwohnerrat") with its letter date.
        # Not with the S1 role response or combined: there the letter date is the date of the response.
        disp = [d for d in _letter_lines(v, range(0, 25), with_label=True) if d["page"] == 1 and not _refused(d)]
    out += [_cand(doc, "submission_date", d, "sub_dispatch_date", "dispatch of the executive with its date")
            for d in disp[:1]]
    if (not disp and not proposal and not resp_doc and doc.s1_role != "committee" and not _type_heading(v)
            and any(PARL_ADDRESS_RX.match(x.strip()) for x in v.lines[:6])):
        # a letter to the parliament with no dispatch word and no proposal of a member in its head: the letter date
        let = [d for d in _letter_lines(v, range(0, 25), with_label=True) if d["page"] == 1 and not _refused(d)]
        out += [_cand(doc, "submission_date", d, "sub_dispatch_letter", "letter to the parliament with its date")
                for d in let[:1]]
    return out


# ------------------------------------------------------------------ response date

LINK_WORDS = frozenset("des der von de du di del la della kantons stadt gemeinde ville commune comune citta città".split())


def _body_line(v: View, i: int) -> re.Match | None:
    """The match of BODY_LINE_RX on line i, if each word after the body word is a link word ("des Kantons", "di")
    or starts with a capital letter in print (a place name). "Stadtrat zwei Fragen stellt." is not such a line."""
    t = v.lines[i]
    m = BODY_LINE_RX.match(t)
    if not m:
        return None
    k = len(t[m.end("body"):].strip(" :").split())
    words = v.doc.lines[i].text.strip(" :").split()[-k:] if k else []
    if all(w.lower() in LINK_WORDS or w[:1].isupper() for w in words):
        return m
    return None


def _signature_lines(v: View) -> list[int]:
    """Line numbers of each signature formula of the executive in the document and of each body word line of the
    last 30 lines."""
    got = {i for i, _ in _signature_formulas(v)}
    for i in range(max(v.n - TAIL_LINES, 0), v.n):
        t = re.sub(r"[^a-z' .,:-]", "", v.lines[i]).strip()
        if SIG_FORMULA_RX.match(t) or _body_line(v, i):
            got.add(i)
    return sorted(got)


def _minute_body_is_parliament(v: View) -> bool:
    """The body word of the minute cue in the head names the parliament of this town: the first 40 lines hold a
    compound of this word with a word for a president ("Gemeinderatspräsident"), or the text says that an item
    goes to a different body ("wird an den Stadtrat überwiesen") or that a different body makes the proposal
    ("Gestützt auf den Antrag des Stadtrates")."""
    if "minute_parl" not in v.memo:
        res = False
        k = _minute_line(v) or 0
        head = " ".join(v.lines[k:k + 12])
        m = re.search(r"(?:protokoll|protokollauszug|proces[- ]verbal|verbale)(?: [a-z]+){0,3}? (?:des|der|du|del)? ?" + B, head)
        if m:
            word = re.sub(r"e?s\Z", "", m.group("body"))
            key = body_key(m.group("body"))[0]
            if re.search(r"(?<![a-z])" + re.escape(word) + PARLIAMENT_COMPOUND, " ".join(v.lines[:40])):
                res = True
            for rx in (TRANSFER_RX, PROPOSAL_OF_RX):
                for x in rx.finditer(v.sp):
                    if body_key(x.group("body"))[0] != key:
                        res = True
        v.memo["minute_parl"] = res
    return v.memo["minute_parl"]


def response_candidates(doc: vb.Doc) -> list[tuple]:
    """All candidates of the response date in the tier order."""
    v = view(doc)
    out, dec, appr, weak_cue = [], [], [], []
    resp_doc = is_response_document(doc)
    # tier 1: response noun and body word directly before the date, on the date line or the line before it,
    # in the first 40 lines (approval cue: all lines)
    for d in v.dates:
        if d["label"] in SKIP_LABELS:
            continue
        k = d["line"]
        prev_start = v.nl.rfind("\n", 0, max(d["ls"] - 1, 0)) + 1
        pre = v.sp[prev_start:d["fs"]][-200:]
        if APPROVAL_DATE_RX.search(pre):
            appr.append(_cand(doc, "response_date", d, "resp_approval_date", "approval by the body before the date"))
            continue
        if k >= HEAD_LINES:
            continue
        lab = RESP_LABEL_PRE_RX.search(d["pre_line"])
        if (lab and re.match(r"^[^a-z]{0,8}\Z", d["pre_line"][:lab.start()])) or (
                _is_date_only_line(d) and k > 0 and RESP_LABEL_LINE_RX.match(v.lines[k - 1])):
            out.append(_cand(doc, "response_date", d, "resp_cue_date", "form label for the date of the response"))
            continue
        if lab:     # the label words in running text ("(Beantwortung vom 2. Juni 2009)"): a different response
            weak_cue.append(_cand(doc, "response_date", d, "resp_cue_text", "response label in running text"))
            continue
        label_near = any(DECISION_LABEL_RX.match(t) for t in v.lines[max(0, k - 10):k])
        if label_near and (DECISION_NO_PRE_RX.match(d["pre_line"]) or (
                re.match(r"^(?:vom|du|del) \Z", d["pre_line"]) and not d["post_line"].strip(" ."))):
            dec.append(_cand(doc, "response_date", d, "resp_decision_date", "decision number and date below a decision label"))
            continue
        m = RESP_CUE_DATE_RX.search(pre)
        if not m:
            continue
        cue = pre[m.start():]
        if TYPE_RX.search(cue) or re.search(r"sitzung|seance|seduta", cue):
            continue
        if m.group("dec"):
            ok = k < 12 and m.group("prep") != ","
        elif m.group("nbody"):
            ok = True
        else:       # the noun alone ("Bericht vom") counts only at a line start of the first 12 lines
            ok = k < 12 and resp_doc and m.group("prep") != "," and bool(RESP_INITIAL_RX.match(d["pre_line"]))
        # the cue is a heading: it starts a line (the date line or the line before it) of the first 12 lines, with at
        # most a number or a bullet before it. A cue in running text can refer to a different response.
        heading = k < 12 and bool(re.match(r"^(?:[^a-z]{0,8}|[^a-z]{0,3}[0-9][0-9a-z./ -]{0,14}, ?)\Z",
                                           re.sub(r"^.*\n", "", v.nl[prev_start:d["fs"]][:max(0, len(v.nl[prev_start:d["fs"]]) - len(cue))], flags=re.S)))
        if ok and m.group("dec"):
            dec.append(_cand(doc, "response_date", d, "resp_decision_date", "decision word of the body before the date"))
        elif ok and heading:
            out.append(_cand(doc, "response_date", d, "resp_cue_date", "response noun and body word before the date"))
        elif ok:
            weak_cue.append(_cand(doc, "response_date", d, "resp_cue_text",
                                  "response noun and body word before the date in running text"))
    # tier 2: the date of the decision ("Stadtratsbeschluss vom", "RRB-Nr.: ... vom", "RG n. 6322 del")
    if resp_doc:
        rg = [d for d in v.dates if d["label"] != "footnote" and DECISION_NUMBER_LINE_RX.match(d["pre_line"])
              and not d["post_line"].strip(" .")]
        if len({d["h"].iso for d in rg}) == 1:
            dec.append(_cand(doc, "response_date", rg[0], "resp_decision_date", "number and date of the decision in a head line"))
    out += appr + dec
    # tier 3: minute of the executive
    minute = _minute_head(v) and not _minute_body_is_parliament(v)
    head8 = " ".join(v.lines[:8])
    form = bool(DECISION_NO_RX.search(head8) and re.search(r"sitzung vom|seance du|seduta del", head8)
                and not PARLIAMENT_RX.search(head8))
    if minute or form:
        heads = [d for d in v.dates if d["line"] < 12 and d["label"] not in SKIP_LABELS]
        sit = [d for d in heads if d["line"] < 8 and SITTING_LINE_RX.match(d["pre_line"])]
        only = [d for d in heads if _is_date_line(d) or _is_place_line(v, d)]
        pick = (sit or only)[:1]
        out += [_cand(doc, "response_date", d, "resp_minute_head", "minute of the executive") for d in pick]
    # tier 4: date line below a response heading
    out += _sub_type_date(v)["resp"]
    # tier 5: place and date line at a signature formula of the executive (the formula can be before the
    # attachments, not only in the last 30 lines). A line at most 4 lines before the formula is better than a line
    # at most 3 lines after it (a line after it can be the letter date of the proposal that is attached).
    sig = _signature_lines(v)
    # a place and date line after words of thanks is the letter date of a proposal that is added to the response
    places = [d for d in _letter_lines(v, range(12, v.n))
              if not any(THANKS_RX.search(t) for t in v.lines[max(0, d["line"] - 3):d["line"]])]
    tail = [d for d in places if d["line"] >= v.n - TAIL_LINES]
    near_sig = []
    for d in places:
        before = min((s - d["line"] for s in sig if 0 < s - d["line"] <= 4), default=None)
        after = min((d["line"] - s for s in sig if 0 < d["line"] - s <= 3), default=None)
        if before is not None:
            near_sig.append((0, before, -d["line"], d))
        elif after is not None:
            near_sig.append((1, after, -d["line"], d))
    near_sig.sort(key=lambda x: x[:3])
    near_sig = [(x[0], x[1], x[3]) for x in near_sig]
    out += [_cand(doc, "response_date", d, "resp_signature_date", "place and date line at the signature formula")
            for _, _, d in near_sig]
    if resp_doc:
        # a date that a cue gives to the proposal (label or type word) is not the date of the response
        t = _sub_type_date(v)
        taken = {c[0] for c in _sub_label(v) + t["near"] + t["far"] + t["inline"]}
        # the letter head is the head of the executive only if the document shows the executive as the sender: a
        # response phrase, a signature formula, a minute cue or a body word line (a tier of the responder that
        # reads such a form gives a value)
        own = any(c[3] in SENDER_TIERS for c in responder_candidates(doc))
        heads = [d for d in _letter_lines(v, range(0, 25), date_only=True)
                 if own and d["page"] == 1 and not _refused(d) and d["h"].start not in taken
                 and (d["line"] < 12 or _is_place_line(v, d))
                 and not (_short_year(d) and _is_date_only_line(d))
                 and not any(URGENCY_RX.search(t) for t in v.lines[max(0, d["line"] - 2):d["line"]])]
        out += [_cand(doc, "response_date", d, "resp_letter_head", "date line of the letter head") for d in heads]
        used = {id(d) for _, _, d in near_sig}
        rest = [d for d in tail if id(d) not in used and d["line"] >= v.n - 15 and d["line"] >= 12]
        out += [_cand(doc, "response_date", d, "resp_letter_tail", "place and date line in the tail")
                for d in reversed(rest)]
        out += weak_cue
        page1 = [d for d in v.dates if d["page"] == 1 and d["line"] >= 12 and _is_date_only_line(d)
                 and d["label"] not in SKIP_LABELS and not _refused(d) and not _stacked_meeting_label(v, d)
                 and d["h"].start not in taken and not _short_year(d)
                 and len(doc.locate(d["h"].start).lines) == 1
                 and not any(URGENCY_RX.search(t) for t in v.lines[max(0, d["line"] - 2):d["line"]])]
        out += [_cand(doc, "response_date", d, "resp_page1_date_line", "line that holds only a date on page 1")
                for d in page1[:1]]
        last = [d for d in v.dates if d["line"] >= max(v.n - 12, 12) and _is_date_only_line(d)
                and d["label"] not in SKIP_LABELS and not _refused(d) and not _short_year(d)
                and len(doc.locate(d["h"].start).lines) == 1]
        out += [_cand(doc, "response_date", d, "resp_tail_date_line", "block that holds only a date in the tail")
                for d in last[-1:]]
    else:
        out += weak_cue
    return out


# ------------------------------------------------------------------ responder

def _body_cand(v: View, m: re.Match, tier: str, cue: str, shift: int = 0) -> tuple:
    a, z = m.start("body") + shift, m.end("body") + shift
    key, wording = body_key(v.sp[a:z])
    s, e = v.f.span(a, z)
    return (s, e, wording, tier, {"cue": cue, "body_key": key})


def _line_initial(v: View, pos: int) -> bool:
    """The folded position is at the start of a line (a number or a bullet before it is permitted)."""
    ls = v.nl.rfind("\n", 0, pos) + 1
    return bool(re.match(r"^[^a-z]{0,8}\Z", v.nl[ls:pos]))


def _line_of(v: View, pos: int) -> int:
    s, _ = v.f.span(pos, pos + 1)
    ln = v.doc.line_at(s)
    return ln.number if ln is not None else 0


def responder_candidates(doc: vb.Doc) -> list[tuple]:
    """All candidates of the responder in the tier order (start, end, base wording, tier, detail)."""
    v = view(doc)
    out = []
    resp_doc = is_response_document(doc)
    proposal = is_proposal_document(doc)
    # tier 1: a phrase says that the body answers. It counts as a cue in the first 30 lines or at a line start
    # (a heading). A hit in the running text (and each hit in a proposal) is a candidate of the last tier.
    cue, weak = [], []
    for i, rx in enumerate(ANSWER_PHRASES):
        for m in rx.finditer(v.sp):
            strong = not proposal and (_line_of(v, m.start()) < 30 or _line_initial(v, m.start()))
            (cue if strong else weak).append((m.start("body"), i, m))
    cue.sort(key=lambda x: x[:2])
    weak.sort(key=lambda x: x[:2])
    out += [_body_cand(v, m, "rsp_response_cue", "response phrase") for _, _, m in cue[:1]]
    # tier 2: signature formula of the executive (the last one of the document), or a body word line with an
    # article in the last 30 lines
    sig = None
    forms = _signature_formulas(v)
    if forms:
        i, m = forms[-1]
        raw = v.lines[i]
        base = v.fpos(doc.lines[i].char_start) + len(raw) - len(raw.lstrip())
        if v.sp[base + m.start("body"):base + m.end("body")] == m.group("body"):
            sig = (i, _body_cand(v, m, "rsp_signature", "signature formula", base))
    for i in range(v.n - 1, max(v.n - TAIL_LINES, 0) - 1, -1):
        if v.line_label[i] == "footnote" or (sig and sig[0] >= i):
            continue
        raw = v.lines[i]
        base = v.fpos(doc.lines[i].char_start) + len(raw) - len(raw.lstrip())
        m = BODY_ARTICLE_LINE_RX.match(raw.strip())
        if m and v.sp[base + m.start("body"):base + m.end("body")] == m.group("body"):
            sig = (i, _body_cand(v, m, "rsp_signature", "body word line with an article in the tail", base))
            break
    if sig:
        out.append(sig[1])
    # tier 2b: the body word line directly below a place and date line (the signature at the end of a letter)
    for _, j in _tail_body_signature(v)[-1:]:
        m = _body_line(v, j)
        base = v.fpos(doc.lines[j].char_start)
        if v.sp[base + m.start("body"):base + m.end("body")] == m.group("body"):
            out.append(_body_cand(v, m, "rsp_signature_place", "body word line below a place and date line", base))
    # tier 3: a minute cue of the body starts a line of page 1, and no cue says that the word names the parliament
    k = _minute_line(v)
    if k is not None and not _minute_body_is_parliament(v):
        m = MINUTE_PHRASE_RX.search(v.sp, v.fpos(doc.lines[k].char_start), v.head_end(min(k + 3, v.n)))
        if m:
            out.append(_body_cand(v, m, "rsp_minute_cue", "minute of the body"))
    # tier 4: the head of a decision of the body in the first 6 lines ("Regierungsratsbeschluss vom ..."). This
    # is the body that decides. The tier is off if the document shows that the word names the parliament.
    for i in range(0, min(6, v.n)):
        raw = v.lines[i]
        m = DECISION_HEAD_RX.match(raw.strip())
        if not m or doc.lines[i].page != 1 or v.line_label[i] == "table":
            continue
        g = "body" if m.group("body") else "body2"
        key = body_key(m.group(g))[0]
        # off: the word names the parliament, or a different body makes the proposal for this decision ("ANTRAG des
        # Stadtrates vom ...", "Beschluss des Gemeinderates": the draft of a decision of the parliament)
        head12 = " ".join(v.lines[:12])
        if (key in _note_taking_bodies(v) or parliament_decision_form(v)
                or any(body_key(x.group("body"))[0] != key for x in PROPOSAL_OF_RX.finditer(head12))
                or any(re.match(r"^(?:antrag|bericht und antrag|weisung|vorlage)(?![a-z])", t.strip()) for t in v.lines[:i])):
            break
        base = v.fpos(doc.lines[i].char_start) + len(raw) - len(raw.lstrip())
        if v.sp[base + m.start(g):base + m.end(g)] == m.group(g):
            s, e = v.f.span(base + m.start(g), base + m.end(g))
            out.append((s, e, body_key(m.group(g))[1], "rsp_decision_body",
                        {"cue": "head of a decision of the body", "body_key": key}))
        break
    # tiers 5 to 8: line forms
    if resp_doc:
        for i in range(0, min(12, v.n)):
            m = _body_line(v, i)
            base = v.fpos(doc.lines[i].char_start)
            if (m and doc.lines[i].page == 1 and v.sp[base + m.start("body"):base + m.end("body")] == m.group("body")
                    and not any(ADDRESS_PRE_RX.search(t.strip()) for t in v.lines[max(0, i - 2):i])):
                out.append(_body_cand(v, m, "rsp_letter_head", "body word line in the letter head", base))
                break
        for i in range(v.n - 1, max(v.n - TAIL_LINES, 0) - 1, -1):
            if v.line_label[i] == "footnote":
                continue
            m = _body_line(v, i)
            base = v.fpos(doc.lines[i].char_start)
            if m and v.sp[base + m.start("body"):base + m.end("body")] == m.group("body"):
                out.append(_body_cand(v, m, "rsp_tail_line", "body word line in the tail", base))
                break
        for i in range(12, v.n):
            if doc.lines[i].page != 1:
                break
            m = BODY_LINE_RX.match(v.lines[i]) if v.lines[i].strip() == v.lines[i] else None
            base = v.fpos(doc.lines[i].char_start)
            if (m and m.end("body") == len(v.lines[i].rstrip(" :"))
                    and v.sp[base + m.start("body"):base + m.end("body")] == m.group("body")
                    and any(SENDER_POST_RX.match(t.strip()) for t in v.lines[i + 1:i + 4])
                    and not any(ADDRESS_PRE_RX.search(t.strip()) for t in v.lines[max(0, i - 2):i])):
                out.append(_body_cand(v, m, "rsp_sender_block", "body word line above an address or contact line", base))
                break
        for i in range(v.n):
            if v.line_label[i] not in ("page_header", "page_footer"):
                continue
            m = BODY_PAGE_LINE_RX.match(v.lines[i].strip())
            base = v.fpos(doc.lines[i].char_start) + len(v.lines[i]) - len(v.lines[i].lstrip())
            if m and v.sp[base + m.start("body"):base + m.end("body")] == m.group("body"):
                out.append(_body_cand(v, m, "rsp_page_line", "body word after the place in a page head or page foot", base))
                break
    # tier 8: the most frequent body word after an article in the response blocks of the rules mode
    count: Counter = Counter()
    first: dict[str, tuple] = {}
    for b in doc.blocks_with_role("response", "recommendation") if doc.has_rule_file else []:
        if not b.text:
            continue
        a, z = v.fpos(b.char_start), v.fpos(b.char_end)
        for m in ARTICLE_BODY_RX.finditer(v.sp, a, z):
            key = body_key(m.group("body"))[0]
            count[key] += 1
            first.setdefault(key, _body_cand(v, m, "rsp_response_block", "most frequent body word in response blocks"))
    top = count.most_common(2)
    if top and top[0][1] >= 2 and (len(top) == 1 or top[0][1] > top[1][1]):
        out.append(first[top[0][0]])
    # tier 9: the body that a proposal addresses (the first phrase in reading order)
    hits = []
    for i, rx in enumerate(ADDRESSEE_PHRASES):
        m = rx.search(v.sp)
        if m:
            hits.append((m.start("body"), i, m))
    # a specific body word is better than a word that is also a common noun ("Regierung", "Governo")
    hits.sort(key=lambda x: (body_key(x[2].group("body"))[0] in GENERIC_BODY_KEYS,) + x[:2])
    out += [_body_cand(v, m, "rsp_addressee_cue", "the proposal addresses the body") for _, _, m in hits[:1]]
    # tier 10: a response phrase in the running text
    out += [_body_cand(v, m, "rsp_response_text", "response phrase in the running text") for _, _, m in weak[:1]]
    return out


# ------------------------------------------------------------------ readers

def _result(doc: vb.Doc, field: str, cands: list[tuple], reason: str, detail: str):
    if not cands:
        return doc.not_found(field, reason, detail)
    s, e, norm, tier, det = cands[0]
    others, seen = [], {norm}
    for s2, e2, n2, t2, d2 in cands[1:]:
        if n2 in seen or len(others) >= 3:
            continue
        seen.add(n2)
        others.append(doc.candidate(field, s2, e2, n2, t2, detail=d2))
    return doc.candidate(field, s, e, norm, tier, others, det)


@vb.register("submission_date")
def read_submission_date(doc: vb.Doc):
    """The day when the proposal was handed in, by the tiers of chapter 3 of the module text."""
    v = view(doc)
    if not v.dates:
        return doc.not_found("submission_date", "no_pattern", "the document text has no complete date")
    return _result(doc, "submission_date", submission_candidates(doc), "no_cue",
                   "no cue word or layout form selects one of the dates")


@vb.register("response_date")
def read_response_date(doc: vb.Doc):
    """The day of the response or decision of the executive, by the tiers of chapter 4 of the module text."""
    if not holds_response(doc):
        # the document holds no response, but a heading cue gives a date to a response that the document cites
        # ("16.5361.02, Stellungnahme des RR vom 11.01.2017" in a decision of the parliament): a tier of its own
        cited = _retier([c for c in response_candidates(doc) if c[3] == "resp_cue_date"], "resp_cited_date") \
            if view(doc).dates else []
        if cited:
            return _result(doc, "response_date", cited, "no_cue", "")
        if doc.s1_role is None:
            return doc.not_found("response_date", "no_response_block", "no rule file and no response cue")
        return doc.not_found("response_date", "not_in_document_type",
                             f"S1 role {doc.s1_role} and no response block of the rules mode")
    v = view(doc)
    if not v.dates:
        return doc.not_found("response_date", "no_pattern", "the document text has no complete date")
    return _result(doc, "response_date", response_candidates(doc), "no_cue",
                   "no cue word or layout form selects one of the dates")


@vb.register("responder")
def read_responder(doc: vb.Doc):
    """The body word of the executive that answers, by the tiers of chapter 5 of the module text."""
    v = view(doc)
    if not re.search(B, v.sp):
        return doc.not_found("responder", "no_pattern", "the document text has no body word of table 3")
    return _result(doc, "responder", responder_candidates(doc), "no_cue",
                   "a body word exists, but no response phrase, signature formula or line form selects it")


# ------------------------------------------------------------------ commands

def coverage(out: Path | None) -> dict:
    """Count the documents of the open parliaments by tier and by 'not found'. This is a count of written values.
    It is not an agreement value: no export value is read."""
    ids = vb.dev_ids("open")
    res = {"version": VERSION, "base": vb.VERSION, "documents": len(ids),
           "note": "coverage by tier over the open parliaments; no export value was read; not an agreement value",
           "fields": {}}
    counts = {f: Counter() for f in MY_FIELDS}
    by_role = {f: {} for f in MY_FIELDS}
    by_lang = {f: {} for f in MY_FIELDS}
    parl = {f: {} for f in MY_FIELDS}
    for d in ids:
        doc = vb.load_doc(d)
        for f in MY_FIELDS:
            r = vb.read_field(doc, f)
            key = r.tier if r.found else f"not_found:{r.reason}"
            counts[f][key] += 1
            by_role[f].setdefault(str(doc.s1_role), Counter())["found" if r.found else "not_found"] += 1
            by_lang[f].setdefault(str(doc.language), Counter())["found" if r.found else "not_found"] += 1
            if r.found:
                parl[f].setdefault(r.tier, set()).add(doc.parliament)
    order = {"submission_date": SUBMISSION_TIERS, "response_date": RESPONSE_TIERS, "responder": RESPONDER_TIERS}
    for f in MY_FIELDS:
        c = counts[f]
        res["fields"][f] = {
            "found": sum(n for k, n in c.items() if not k.startswith("not_found")),
            "not_found": sum(n for k, n in c.items() if k.startswith("not_found")),
            "by_tier": {t: c.get(t, 0) for t in order[f]},
            "parliaments_by_tier": {t: len(parl[f].get(t, ())) for t in order[f]},
            "not_found_by_reason": {k.split(":", 1)[1]: n for k, n in sorted(c.items()) if k.startswith("not_found")},
            "by_s1_role": {k: dict(x) for k, x in sorted(by_role[f].items())},
            "by_language": {k: dict(x) for k, x in sorted(by_lang[f].items())},
        }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return res


def show(doc_id: str) -> None:
    doc = vb.load_doc(doc_id)
    print(json.dumps({"doc_id": doc.doc_id, "parliament": doc.parliament, "language": doc.language,
                      "s1_role": doc.s1_role, "lines": len(doc.lines)}, ensure_ascii=False))
    for f in MY_FIELDS:
        print(json.dumps(vb.read_field(doc, f).to_json(), ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="value rules for submission date, response date and responder (T7)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("doc_id")
    c = sub.add_parser("coverage")
    c.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    if a.cmd == "show":
        show(a.doc_id)
        return 0
    print(json.dumps(coverage(a.out), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

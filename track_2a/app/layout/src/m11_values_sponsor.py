"""Plan `crisp-dm/04-modeling/plan-ech-from-pdf.md`, task T8: the value rule for the first author (field `sponsor`,
slot `Submission.sponsorship` with the role sponsor). A should-field.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5) for the main
agent. Status: EXCEPTION, NOT RELEASED. No human checked this file.
Version 2 (13.10.2026, improvement round before the closed part is opened): the author compared the reader output
with the reference of the OPEN part (`daten/gj_values/reference_open.json`) to find error patterns. Thus each
value of this rule on the open part is optimistic. The author read documents of open parliaments only. The export
role of the reference also holds co-signers: where a document prints 2 or more authors, the rule returns the
first one as printed, also if the export names a different person.
Version 3 (13.10.2026, round 3, AFTER THE OPENING of the closed part): the author read documents of all 44
development parliaments (open and closed) and the 2 reading checks of the closed part
(`daten/gj_values/closed_review_a.json`, `closed_review_b.json`), and compared the reader output with the reference of
the open part and of the closed part. Thus each value of this rule on the 1,793 development documents is optimistic.
Only the last run on documents that no author read is a clean measure. New in version 3: forms with a field label
and a hint of the form ("Auteur-e ou premier-ère signataire : prénom, nom (obligatoire) :"), a label column, a form
with one field for the family name and one for the first name, the group with the names in a bracket after a type
word, head lines with semicolons, the head of a document of the executive in tiers of its own, the addressee of an
answer by letter, the list of the other signers as a zone that gives no first author, names with the family name in
upper case, and the further authors of the same cue in the list `others` (tier `co_author`).

1 Inputs
  One `Doc` of `src/m11_values_base.py`: the blocks and lines of the block file, the S1 rule role and the block
  roles of the rules mode. The rule reads no export record, no decisions file and no state file. It has no
  condition on a parliament name or id. It uses cue words, layout forms and a list of first names.

2 Scope
  The tiers with a label cue, a type word, a submission verb or an addressee block read each document (an answer
  of the executive prints the author in its heading). The tiers that read a head sender or a signature read only
  a document with the S1 rule role proposal or combined, and a document with no rule file. In a document with a
  different S1 role (not minutes) a short name line in the head gives a value only in the tier
  `head_sender_other_role`. A document with a different S1 role and no value gives `not found in the PDF` with
  the reason `not_in_document_type`.

3 Tiers (in the order of the selection; the first tier that gives a candidate gives the value)

  | Tier | What the tier reads |
  |---|---|
  | `label_same_line` | A name on the same line after a label cue ("Eingereicht von:", "Erstunterzeichner/in:", "Urheber/-in:", "Déposée par:", "Auteur-e ou premier-ère signataire : prénom, nom (obligatoire) :", "Presentata da:", "Proponente:"; a tab counts as a colon; a second label after "ou"/"oder"/"o" and a hint of the form are parts of the label; a group before the name is skipped: "PLR VDB / Martine Tristan"), or directly before a first-signer cue in brackets ("... (primo firmatario)"). Not in a footnote and not in a line with the data of a file ("Autor: ... Speicherdatum"). |
  | `type_prep_name` | In the first 25 lines, a type word in the form of a heading, a preposition and a name with a known first name, a title, an initial or 2 to 3 name words ("Kleine Anfrage von Landrat Christoph Keller", "Postulat von A. Abdurahman"). The document is no document of the executive. |
  | `response_head_prep_name` | The same form in the head of a document of the executive: a response noun before the type word in the same sentence ("Beantwortung der Interpellation Nr. 629/2013 von ...", "Préavis du Conseil municipal sur le postulat / de Mme Tristan et Mme Heinis du 30.03.2023"), a cue of a document of the executive in the first 12 lines, or the S1 rule role response. The name is the author of the proposal. |
  | `type_group_bracket` | A type word in the form of a heading, a group and a bracket that starts with a name of 2 or more words ("Postulat Fraktion SP/JUSO (Laura Binz/Marieke Kruit, SP): ...", "Interpellation der SVP-Fraktion (Christian Schuler, Erstfeld)"). The first name in the bracket is the value. |
  | `type_separator_name` | A head line with the parts between semicolons: a type word, an optional number, a semicolon and a name of 2 or more words with a party mark or a semicolon directly after it ("Interpellation 8145; Max Töpfer, SP; ..."). |
  | `spokesperson_entry` | A list entry "<family name> (<place>, <mark>)" with the mark of the spokesperson ("(Sprecher/-in)", "(porte-parole)") on the same line or on the next line. |
  | `addressee_member` | The addressee block of an answer in the first 80 lines: a line with a salutation word only, a name line, and a line with a member word only before or after the name ("Signor" / "Matteo Pronzini" / "Deputato al Gran Consiglio"). |
  | `label_next_lines` | A line that is only a label cue, and a name line or a list entry in the 3 lines after it (the search stops at the label of the other signers; a name directly before that label on the same line is the value). Also a name line directly before a label with no colon (form layout). |
  | `label_column_form` | A label cue with a colon in a column of 3 or more lines with a label only, no name in the 3 lines after it, and no label of the co-signers before it in the column: the first name line in the 8 lines after the column ("Eingereicht am:" / "Eingereicht von:" / "Mitunterzeichnende:" / ... / "19.09.2018" / "Pauli Pauline, PRR"). |
  | `label_form_fields` | A line of at most 50 characters with a label cue, and in the 3 lines after it one field for the family name and one field for the first name ("1. Personalien Motionsteller" / "Name<tab>Herbst" / "Vorname<tab>Adrian"). The value is the family name; the first name is in the detail. |
  | `sender_signature` | A name line in the first 12 lines (in a short document: in the first half) whose family name is also a name line in the signature zone. |
  | `type_entry_name` | A type word in the form of a heading and a family name with a bracket that holds a place and a mark ("Motion 026-2013 Linder (Bern, Grüne)"). |
  | `type_full_name` | A type word in the form of a heading and a full name with a known first name, with no preposition or with title words between them ("Motion Michael Arnold, Altdorf"). The document is no document of the executive. |
  | `response_head_full_name` | The same form in the head of a document of the executive ("Bericht des Gemeinderats zum Anzug Martin Leschhorn Strebel und Kons. betreffend ..."). |
  | `type_name_cue_after` | A type word in the form of a heading and 2 to 3 name words with NO known first name, with a cue directly after the name: a party mark in a bracket, a co-signer cue or the word that starts the title ("Motion Ahila Gunaratnam und Mitunterzeichnende betreffend"). |
  | `addressee_reply` | The addressee block of an answer by letter: a line with a salutation word only or with a member word only, a name line, and "your <type word>" in the 25 lines after the name or before the block ("Egregio Signor" / "Samuele Cavadini" / ... "alla sua interrogazione"; "Ihre Interpellation"; "votre postulat"). No line with a member word is necessary. |
  | `narrative_submit` | In the first 60 lines: a name beside a submission verb in a sentence that has a type word ("reichte Landrat ... ein", "Daniel Körner, FDP und Mitunterzeichnende haben am ... eingereicht", "welche die Kantonsräte ... eingereicht haben", "par M. ..., a déposé", "inoltrata dai Consiglieri comunali ..."). With 2 or more names before the verb the first name is the value. "hat" / "haben" need a submission participle later in the sentence. |
  | `head_sender_marked` | A name line in the first 12 lines with a member mark or a party mark beside it, and no addressee cue before it. A wrapped line of running text is no name line. |
  | `head_sender_other_role` | The forms of `sender_signature` and `head_sender_marked` in a document whose S1 rule role is not proposal or combined (and not minutes): a name line of at most 60 characters. Only the head says that the document holds a proposal. |
  | `signature_marked` | The first name line of the signature zone with a member mark, a party mark or a signer cue beside it, if the line before it is no unread short line. |
  | `type_prep_cosigners` | In the first 60 lines, also in running text: a type word (with no indefinite article before it), an optional title in quotation marks, a preposition, a name with a known first name or a title, and a co-signer cue with a count or a co-signer word ("Das nachfolgende Postulat von Timotheus Bruderer (SVP) und 16 Mitunterzeichnenden"). |
  | `type_family_name` | Weak: a type word in the form of a heading and ONE family name with a colon, a party mark, a co-signer cue, a number or a quotation mark after it ("Postulat Tanner: ...", "Motion Zosso (Nr. 037/2025)"). 2 or 3 name words with a cue after them are in the tier `type_name_cue_after`. Also one name word after a preposition. |
  | `signature_plain` | The first name line of the signature zone with no mark beside it, in a zone with 1 to 3 name lines and no unread short line directly before it. |
  | `type_in_sentence` | Weak: a type word in a sentence of running text and a name after it ("Der Stadtrat hat das Postulat von ... abgelehnt"). The sentence can name a different affair. Also a type word in the form of a heading with a name that is different from the name of the FIRST type word with a name (the first one names the affair of the document). |
  | `signature_list_first` | Weak: the first READ name line of a list of signatures: a zone with 4 or more name lines, or an unread short line directly before the name line (handwriting, a first name that is not in the list). |
  | `signature_marked_later` | Weak: a name line with a mark that is not the first name line of the signature zone. Only as a second candidate (list `others`). |
  | `signature_untyped` | Weak: the first name line of the signature zone of a document whose first 25 lines have no type word. Only the S1 rule role says that the document is a proposal. |
  | `co_author` | Only in the list `others`, never the value: a further author that the cue of the value prints after the first author ("... (Laura Binz/Marieke Kruit, SP)", "de Mme Tristan et Mme Heinis", "Erstunterzeichnende: A, B"). The list ends before a co-signer cue. |

  The list of the other signers: the short lines after a line that starts with the label of the co-signers ("Autres
  signataires", "Mitunterzeichnende:", "Cosignataires", "Cofirmatari") until a line of running text, a closing
  formula, a label of the first author or 40 lines. A name line in this list gives no candidate in a signature tier.
  A type word is in the form of a heading if its block is a heading, if at most 2 words stand between the start of
  the sentence and the type word, or if the sentence starts with a response noun ("Beantwortung", "Réponse").
  The signature zone is in the last 25 lines before the first response block (footnote lines at the end do not
  count): the lines after the last 2 lines of running text that are one after the other (with no such pair: after
  the last line of running text). With no running text in the 25 lines the zone goes back to 60 lines. If the end
  of the document has no name line with a mark, the rule also reads the zone before an annex heading ("Beilagen:",
  "Allegati"). The tiers `sender_signature`, `head_sender_marked` and all signature tiers are off if the first
  line of a block in the first 12 lines starts with a cue of a document of the executive ("Bericht und Antrag",
  "Beantwortung", "Réponse du", "Messaggio"). The head tiers and the signature tiers other than
  `signature_untyped` are off if the first 25 lines have no type word. A name with a cue of the executive or of an
  official near it is refused in each tier ("Im Namen des Stadtrats", "Stadtschreiber", "Le chancelier",
  "Sindaco"; also a title of the executive before or after the name: "Regierungsrätin ...", "..., Stadtpräsident").

4 Output
  value       the printed name (first names and family name, with no title and no party mark)
  normalised  the family name: lower case, no accents, each character that is not a letter or a digit as a space.
              With a known first name the words after the first names are the family name. With a known first name
              as the last of 2 words the first word is the family name. With no known first name the first word is
              taken as the first name in the detail, detail.split_uncertain is true, and `normalised` keeps all
              words and particles of the name (the rule cannot say which word is the family name).
  detail      printed_name, first_names, family_name, cue, and `party` (the party or group mark beside the name
              with its span) as extra evidence. The party mark is not a value. `co_authors`: the further authors of
              the same cue (printed name, span, normalised value).
  others      first the further authors of the same cue (tier `co_author`), then at most 5 candidates of the
              tiers that did not give the value.
  A name with the family name in upper case ("Mathias GAUTSCHI", "GAUTSCHI Mathias") is read as printed.
  A group author ("Motion der SP-Fraktion") is not a person name. The rule returns no value for it.

5 Limits
  The list of first names is not complete. A name line whose first name is not in the list gives no candidate in
  the tiers that need a known first name. A document that prints the family name only (lists of signers) gives a
  candidate only in the weak tier `type_family_name`. Where 2 lists of the same document print the authors in a
  different order, the rule returns the name of the first tier that matches. The reference of the measurement
  (export role author) can name a co-signer; such a document counts as different although the reader value is
  the first printed author. The owner decides if names enter published records
  (decision D3 of the plan); this file only reads what the public document prints.

Usage (from the project folder):
  uv run --offline --frozen --no-sync python src/m11_values_sponsor.py show DOC_ID
  uv run --offline --frozen --no-sync python src/m11_values_sponsor.py coverage
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m11_values_base as base  # noqa: E402
from m11_values_base import Doc, NotFound, ValueCandidate, register  # noqa: E402

VERSION = "m11-values-sponsor-3"
FIELD = "sponsor"
TIERS = ("label_same_line", "type_prep_name", "response_head_prep_name", "type_group_bracket",
         "type_separator_name", "spokesperson_entry", "addressee_member", "label_next_lines", "label_column_form",
         "label_form_fields", "sender_signature", "type_entry_name", "type_full_name", "response_head_full_name",
         "type_name_cue_after", "addressee_reply", "narrative_submit", "head_sender_marked",
         "head_sender_other_role", "signature_marked", "type_prep_cosigners", "type_family_name", "signature_plain",
         "type_in_sentence", "signature_list_first", "signature_marked_later", "signature_untyped")
CO_AUTHOR_TIER = "co_author"       # only in the list `others`: a further author that the same cue prints
STRONG_TYPE_TIERS = ("type_prep_name", "response_head_prep_name", "type_group_bracket", "type_separator_name",
                     "type_entry_name", "type_full_name", "response_head_full_name", "type_name_cue_after")
HEAD_LINES_COSIGNERS = 60
LABEL_COLUMN_MIN = 3               # lines with a label only, one after the other, that make a label column
LABEL_COLUMN_REACH = 8             # lines after the label column in which the value of the label is read
S1_ROLES_IN_SCOPE = ("proposal", "combined")
HEAD_LINES_TYPE = 25
HEAD_LINES_NARRATIVE = 60
HEAD_LINES_SENDER = 12
SIGNATURE_WINDOW = 25
SIGNATURE_WINDOW_LIST = 60
SIGNATURE_LIST_MIN = 4
HEAD_LINES_ADDRESSEE = 80
COVERAGE_FILE = base.ROOT / "daten/gj_values/coverage_sponsor.json"

# ------------------------------------------------------------------ word lists (folded: lower case, no accents)

FIRST_NAMES = frozenset("""
aaron achim adolf adrian adriano advije agnes alain alan albert alberto albin aldo alex alexander alexandra alexandre
alexis alfons alfred alice aline alois amanda amelie ana anastasia andre andrea andreas andri andrin angela angelika
angelo anita anja anna annamarie anne annelies annemarie annette annina anton antonia antonio antoine arianna armin
arnaud arno arthur astrid attilio audrey august aurelie aurelio balz barbara bastien beat beata beatrice beatrix
benedikt benjamin benno benoit bernadette bernard bernhard bettina bianca boris brigitta brigitte bruno camille
carina carl carla carlo carmela carmen carole carolina caroline catherine cecile cedric celine chantal charles
charlotte chiara christa christian christiane christina christine christof christoph christophe claire clara
claude claudia claudine claudio clemens colette conrad corina corine corinne cornelia cristina cyril cyrill damian
damien daniel daniela daniele danielle dario david davide delphine denis denise diana didier diego dieter dominic
dominik dominique dora doris edgar edith edo eduard edwin elena eliane elias elisabeth elodie elsa elsbeth emanuel
emil emilie emmanuel enrico eric erich erika ernst erwin esther etienne eugen eva evaristo eveline evelyne fabian
fabien fabienne fabio fabrice fabrizio federica federico felix ferdinand filippo fiorenzo flavia flavio florence
florian franca francesca francesco francine francis franco francois francoise frank franz franziska fred frederic
frederik fredi fredo fredy frieda fridolin fritz gabi gabriel gabriela gabriele gabriella gabrielle genevieve georg
george georges gerald gerard gerda gerhard gian giancarlo gianluca gianni gilbert gilles gina gino giorgio giovanna
giovanni gisela giulia giuliano giuseppe gottfried greta gregor gregory guido guillaume guy hanna hannah hannes hans
hansjorg hanspeter hansruedi hansueli harald harry hedi hedwig heidi heinrich heinz heiri helen helena helene helga
henri henrik herbert hermann herve hubert hugo ida ignaz ines ingrid irene irina iris irma isabel isabella isabelle
ivan ivo jacqueline jacques jakob jan janine jari jasmin jean jeanne jeannette jeannine jens jerome joachim joel
joelle johann johanna johannes jolanda jonas jonathan jorg jose josef joseph josiane jost judith julia julian julie
julien juliette jurg jurgen karin karine karl kaspar katharina kathrin katja katrin kevin kilian klara klaus konrad
kurt lara lars laura laure laurence laurent lea lena leo leon leonie lilian liliane lina linda linus lionel lisa
loic lorenz lorenzo lothar louis louise luc luca lucas lucia luciano lucie ludwig luigi lukas luzia lydia maddalena
magali magdalena maja manfred manon manuel manuela mara marc marcel marcello marco marcus margot margrit marguerite
maria marianne marie marina mario marion maristella marius markus marlene marlies marta martha martin martina
martine massimo mathias mathieu mathilde matteo matthias matthieu maurice maurizio max maxime maya melanie meinrad
michael michel michela michele micheline michelle milena mireille miriam mirjam monica monika monique moritz muriel
nadia nadine nadja nara natalia natalie natascha nathalie nicola nicolas nicole nico niklaus nils nina noah noe
noemi noemie norbert odile olga oliver olivia olivier omar oskar osman oswald othmar otto pablo paola paolo pascal
pascale patricia patrick patrik patrizia paul paula pauline peter petra philip philipp philippe pia pierre pietro
pirmin pius priska rachel rafael raffaele raffaella rahel rainer ralf ralph ramon raoul raphael raphaela raymond
rebecca rebekka regina regula reinhard remo remy renata renate renato rene reto riccardo richard rico riquet rita
robert roberta roberto roger roland rolf roman romana romano romain ronald rosa rosemarie rosmarie ruedi rudolf ruth
sabina sabine sabrina salome salvatore samantha samuel sandra sandrine sandro sara sarah sascha sebastian sebastien
selina sem sepp serge sergio severin severine sibylle siegfried silvan silvana silvia silvio simon simona simone
sofia solange sonja sophie stefan stefania stefanie stefano stephan stephane stephanie susanna susanne suzanne sven
sylvain sylvia sylvie tamara tania tanja teresa tessa theo theodor theres therese thierry thomas tim timo tina
tiziano tobias tom toni tullio ueli ulrich ulrike urban urs ursina ursula valentin valentina valentine valerie
vera verena veronika veronique victor viktor vincent vincenzo viola violaine virginie vito vreni walter werner
wilhelm willi willy wolfgang xaver xavier yann yannick yasmine yves yvette yvonne zeno
ada adriana adrien agathe alessandra alessandro alessia alessio alfio ali amalia amandine amos annick anouk anthony
arnold athos aude aurelien baptiste bea beda benedicte beni bertrand bixio blandine celestino christelle cindy
clement cleto clotilde coralie corentin corinna cristian curdin cyrille danilo debora deborah dino dirk donato
dragan duri dylan edoardo edouard eleonora elia elif elio elisa ella eloi emanuele emma emmanuelle enea ermanno
estelle ettore fanny fatima florent flurin fulvio gael gaelle gaetan gerardo germano ghislaine giada giampiero
gianmaria gianpaolo giordano goran graziano gregorio hanni heidy heike holger igor ilaria ivana ivano jack jacopo
jana jennifer jenny jeremie jeremy jessica jocelyne johan joris justine kathi kathy kerstin kirsten kobi kristian
kristina laetitia leonard lia lino lise livia livio lorena loris lotti luana lucien lucio ludovic lutz lynn mael
manuele marilena marino marjorie marylene marzio mathis mattia matthew maud maude mauro mehmet melissa mia milan
mirco mirko moreno mustafa myriam nadege nando nello nenad nevio nicolo oreste orlando pier pierangelo pierfranco
pierluigi piero pierrick quentin ramona remigio renzo rino robi rolando ruben rudiger samuele sasha seppi sibyl
simeon sina sofie sonia sophia steffi svenja sybille tabea thea thibault thibaut thorsten till timon tino tommaso
tony torsten trudi trudy ulla ute uwe valeria vanessa victoria viktoria violette vital vroni wisi yolanda yolande
zita zoran
amedeo angelica arnoldo aron bruna cesare dafne daria emanuela eolo evelyn fausto felice giacomo gianrico giorgia
graziella katia katya lelia luisa marisa massimiliano mattea maura mirella nadir nicholas ornella paride patrizio
rosanna sebastiano tatiana tiziana ugo
abdul amr carine carola dimitri jasmine marianna ricardo anjushka anke ann annetta arber attila berti beryll bigi brigitt cloe dagmar darryl davina deny derek dubravko
elmar esen gaby gallus gloria grazia gunter gunthard ira jann janina janosch jigme jules kanny konyo kuno leona
leonora linnea maline mark marlis martial maurane mila mirta myrtha nathanael nolan nora pepo perparim pio qendresa
randy robin saima sait sam selim soumaya stellio timotheus tiba tomas tristan urim volkan xhelajdin zoe
alicia belinda brian carol emine hasim heiner jelena karim marieke milena mourad rezio rossano zubaida
""".split())

# tokens that end a name or that are no name (roles, bodies, type words, letter words, months, days)
NON_NAME = frozenset("""
fraktion fraktionen gruppe groupe groupes gruppo partei parti partito ortspartei sektion section sezione kommission
commission commissione stadtrat gemeinderat regierungsrat landrat kantonsrat grossrat einwohnerrat bundesrat
staatsrat parlament stadtparlament kanton canton cantone stadt ville citta gemeinde commune comune conseil consiglio
municipio municipal communal general kanzlei staatskanzlei standeskanzlei departement dipartimento direktion
direction verwaltung amt buro bureau prasident prasidentin president presidente prasidium sekretariat herr herrn
frau monsieur madame signor signora sehr geehrte geehrter freundliche grusse gruss dank danke merci grazie datum
date data beilage beilagen annexe allegato kopie betreff betreffend betrifft concernant intitulee intitule titel
titre titolo motion motionen postulat postulate postulats postulato interpellation interpellationen anfrage
anfragen vorstoss auftrag initiative question interrogation mozione interpellanza interrogazione iniziativa
resolution risoluzione antwort beantwortung reponse risposta bericht rapport rapporto antrag begrundung wortlaut
januar februar marz april mai juni juli september oktober november dezember janvier fevrier mars avril juin
juillet aout septembre octobre novembre decembre gennaio febbraio marzo aprile maggio giugno luglio agosto
settembre ottobre dicembre montag dienstag mittwoch donnerstag freitag samstag sonntag schweiz suisse svizzera
schweizerische schweizer und et ed oder ou der die das des dem den le la les il lo gli ein eine un une uno una
mitunterzeichner mitunterzeichnende mitunterzeichnenden konsorten consorts cofirmatari unterzeichner
unterzeichnende erstunterzeichner fur per pour mit avec con zur zum uber sur nr no art abs seite page pagina
regierungsratin stadtratin gemeinderatin landratin kantonsratin grossratin einwohnerratin bundesratin staatsratin
egregi egregio egregia gentile gentili signori signore lodevole onorevoli spettabile messieurs mesdames damen herren
nationalrat nationalratin standerat standeratin stadtammann gemeindeammann landammann statthalter syndic sindaco
strasse rue via platz postfach telefon mail www http https depose deposee relative relatif aus sicht im in an am auf bei wir ich es wie was wer nach seit vor nous je en au person personen weitere name vorname mitte liberalen grune grunen centre centro verts
""".split())
# a word of NON_NAME that is also a family name: it is a part of a name directly after a known first name
FAMILY_AFTER_FIRST_NAME = frozenset(("schweizer", "mai", "marz", "freitag", "sonntag", "montag", "herr", "kanton"))
_NON_NAME_SUFFIX = ("strasse", "gasse", "platz", "kommission", "fraktion", "partei", "gemeinde", "verwaltung",
                    "departement", "direktion", "kanzlei", "prasident", "prasidentin", "sekretar", "sekretarin",
                    "schreiber", "schreiberin", "verband", "verein", "gruppe", "ordnung", "gesetz", "reglement",
                    "rates", "rats")
PARTICLES = ("von der", "von den", "van der", "van den", "de la", "von", "van", "de", "del", "della", "dei", "di",
             "da", "dal", "du", "des", "le", "la", "zu", "ten", "ter")

# ------------------------------------------------------------------ patterns

_UP = "A-ZÀ-ÖØ-Þ"
_LO = "a-zß-öø-ÿ"
_AP = "'’"
RX_TOK = re.compile(rf"[{_UP}][{_LO}]+(?:[-{_AP}][{_UP}]?[{_LO}]+)*")
RX_CAPTOK = re.compile(rf"[{_UP}]{{2,}}(?:[-{_AP}][{_UP}]{{2,}})*(?![{_LO}])")
RX_INITIAL = re.compile(rf"[{_UP}](?:\.(?=\s|$)|(?= [{_UP}][{_LO}]))")
_CAP_PARTICLES = frozenset(("la", "le", "de", "del", "della", "di", "da", "dal", "von", "van", "zu", "ten", "ter"))
RX_PARTICLE = re.compile(r"(?:" + "|".join(re.escape(p) for p in PARTICLES) + r") (?=[" + _UP + r"])")

# the party or group mark beside a name (searched in the text as printed; the short forms need upper case)
PARTY = (r"(?:SP|SVP|FDP|CVP|GLP|glp|EVP|EDU|BDP|GPS|GP|GB|AL|JUSO|PLR|PLRT|PDC|PS|UDC|PEV|PVL|POP|PPD|MPS|UDF|PC|LDP|"
         r"CSP|JSVP|JGLP|JFDP|GFL|FW|PRR|GRÜNE|Grüne[nr]?|GRUENE|Grünliberale[nr]?|Die Mitte|DIE MITTE|Mitte|Les Vert[-·.e]*s|"
         r"Le Centre|Il Centro|Centro|Lega|I Verdi|Verdi|VertsPopSol|VERTSPOPSOL|Socialiste[s]?|SOCIALISTE|"
         r"Vert'?libéra(?:l|ux)|Schweizerische Volkspartei|FDP\.Die Liberalen|Die Liberalen|Avanti|Più Donne|"
         r"parteilos|Parteilos|PARTEILOS)")
RX_PARTY = re.compile(rf"(?<![{_UP}{_LO}])" + PARTY + rf"(?![{_UP}{_LO}])")
RX_PARTY_AFTER = re.compile(
    rf"[ \t]*(?:[,(/|–-][ \t]*)?(?:(?:[{_UP}{_LO}.-]+[ \t]+){{0,3}})?(" + PARTY + rf")(?![{_UP}{_LO}])")
RX_PAREN_AFTER = re.compile(r"[ \t]*\(([^()\n]{1,40})\)")

COUNCIL = (r"(?:gemeinde|kantons|land|gross|einwohner|stadt|national|stande|parlaments)"
           r"(?:ratinnen|ratin|raten|rates|rate|rats|rat|ratsmitglieder|ratsmitglied|mitglieder|mitglied)")
RX_COUNCIL_WORD = re.compile(COUNCIL)
# all patterns below are searched in the folded text (function sfold): lower case, no accents
TITLE = (r"(?:(?:herrn?|frau|hr\.|fr\.|m\.|mme|mlle|mmes|mm\.|monsieur|madame|on\.|onorevole|sig\.(?:ra)?|signora?|"
         r"dr\.(?: ?[a-z]{2,5}\.)?|prof\.|lic\. ?iur\.|avv\.|ing\.|arch\.|dott\.(?:ssa)?|lr|kr|er|" + COUNCIL + r"|parlamentarier(?:in|innen)?|"
         r"deputee?s?|deputat[oai]|granconsiglier[eai]|"
         r"consiglier[eai](?: comunal[ei]| nazional[ei])?|"
         r"conseill(?:ers?|eres?)(?: genera(?:le?s?|ux)| communa(?:le?s?|ux)| nationa(?:le?s?|ux))?|"
         r"erstunterzeichner(?:in)?|(?:gemeinde|stadt|kantons|land|gross|einwohner)?ratsmitglied(?:er)?|kollegin?) )")
RX_MEMBER_TITLE = re.compile(r"(?:^|[ \t(])(?:lr|kr|er|(?:kantons|land|gross|einwohner)(?:ratinnen|ratin|raten|rate|rat)|"
                             r"(?:gemeinde|stadt|kantons|land|gross|einwohner)?ratsmitglied(?:er)?|"
                             r"parlamentarier(?:in)?|deputee?|deputat[oa]|granconsiglier[ea]) $")
RX_TITLES = re.compile(TITLE + r"*")
RX_EXEC_TITLE = re.compile(
    r"(?:regierungsrat|regierungsratin|regierungsprasident(?:in)?|staatsrat|staatsratin|bundesrat|bundesratin|"
    r"bundesprasident(?:in)?|stadtprasident(?:in)?|gemeindeprasident(?:in)?|stadtammann|gemeindeammann|landammann|"
    r"statthalter|conseill(?:er|ere) d'etat|conseill(?:er|ere) federale?|conseill(?:er|ere) municipale?|"
    r"consiglier[ea] di stato|municipale|sindaco|syndic|syndique|stadtschreiber(?:in)?|gemeindeschreiber(?:in)?|"
    r"staatsschreiber(?:in)?|chanceli(?:er|ere)|cancellier[ea]|direktor(?:in)?|vorsteher(?:in)?) $")
TYPE = (r"(?<![a-z])(?:(?:dringlich|klein|einfach|schriftlich|parlamentarisch|mundlich)e[rnms]? )?"
        r"(?:(?:volks|globalbudget|richtlinien|fraktions|jugend|leistungs)?motion(?:en|s)?|(?:budget)?postulat(?:e?s|o)?|interpellation(?:en|s)?|anfragen?|vorstoss(?:es)?|leitmotion|"
        r"(?:planungs)?anzug(?:e?s)?|"
        r"resolution|question(?: ecrite| orale)?|interrogation|mozione|interpellanza|interrogazione|"
        r"iniziativa parlamentare|parlamentarische[rn]? initiative|parlamentarische[rn]? empfehlung|"
        r"initiative parlementaire|risoluzione)(?![a-z])")
RX_TYPE = re.compile(TYPE)
RX_TYPE_NUMBER = re.compile(r" (?:nr\.?|n[o°]\.?|n\.)? ?[0-9][0-9a-z./-]{0,14}(?= )")
RX_PREP = re.compile(r" (?:(?:von|della|del|der|des|de la|de|du|di|da) |d'|de l')")
RX_WEAK_PREP = re.compile(r" (?:von|de|di|da) ")
RX_AFTER_FAMILY = re.compile(r"(?:\s?:|\s\((?:" + PARTY + r")[^)]{0,20}\)|,? und (?:mit|kons)|,? et consorts|,? e cofirmatari|"
                             r"\s\(?(?:nr|n[o°])\.? ?[0-9]|\s[«\"„“][^ ]|\s« [^ ]|\s[0-9]{2}\.[0-9]{3,4}(?![0-9]))",
                             re.IGNORECASE)
RX_AFTER_FAMILY_STRICT = re.compile(r"(?:\s\((?:" + PARTY + r")[^)]{0,20}\)|,? und (?:mit|kons)|,? et consorts|,? e cofirmatari)",
                                    re.IGNORECASE)
LABEL = (r"(?<![a-z])(?:eingereicht (?:am [0-9. a-z]{6,20} )?(?:von|durch)|erstunterzeichn(?:erin|er|ende[rn]?|ete[rn]?)|"
         r"urheber(?:in|schaft)?|motionar(?:in|s|en)?|postul[ae]nt(?:in|en)?|interpellant(?:in|en)?|absender(?:in)?|"
         r"verfasser(?:in)?|unterzeichner(?:in)?|unterzeichnende[rn]?(?: person(?:\(en\)|en)?)?|einreicher(?:in)?|"
         r"(?:an)?fragesteller(?:in)?|(?:motions?|postulats?|interpellations?|antrags?)steller(?:in)?|initiant(?:in|en)?|"
         r"vorstosser(?:in)?|deposee? par|presentee? par|depositaires?|auteure?s?|"
         r"premi(?:er|ere)(?:[-/. ]e?re)? signataire|signataires?|proponent[ei]|"
         r"presentat[aoei] (?:il [0-9]{1,2}°? [a-z]+ [0-9]{4} )?(?:nella forma (?:generica|elaborata) )?da|prim[oa] firmatari[oa]|firmatari[oa]?|"
         r"autor[ei]|autrice|interpellant[ei]|mozionant[ei]|interrogant[ei])(?![a-z])")
RX_LABEL = re.compile(LABEL)
_LABEL_TAIL = (r"(?:\((?:e|in|en|i|n)\)|/ ?-? ?in(?:nen)?|[./·-]e)?"
               r"(?: (?:de l'|du |de la |des |dell[ao']? ?|del |der |des )(?:intervention|objet|proposition|vorstoss(?:es)?|"
               r"atto|" + TYPE[len("(?<![a-z])"):] + r"))?")
# a second label after "ou" / "oder" / "o" ("Auteur-e ou premier-ère signataire"), and a hint of the form that
# says what the field holds ("prénom, nom (obligatoire)", "(Vorname, Name)", "nome e cognome")
_LABEL_CHAIN = r"(?: (?:ou|oder|o|bzw\.?|/) (?:le |la |der |die |il |i )?" + LABEL + _LABEL_TAIL + r")?"
_LABEL_HINT = (r"(?: ?:? ?\(?(?:prenom,? (?:et )?nom|nom,? (?:et )?prenom|vorname,? (?:und )?name|name,? (?:und )?vorname|"
               r"nome,? (?:e )?cognome|cognome,? (?:e )?nome)\)?(?: \((?:obligatoire|pflichtfeld|obligatorisch|"
               r"obbligatorio)\))?)?")
RX_LABEL_TAIL = re.compile(_LABEL_TAIL + _LABEL_CHAIN + _LABEL_HINT)
RX_LABEL_ONLY = re.compile(r"\s*(?:[-•*]\s*)?\(?(?:der |die |le |la |il |i )?" + LABEL + _LABEL_TAIL + _LABEL_CHAIN +
                           _LABEL_HINT + r"\)?\s*(:?)\s*")
# the label of the list of the other signers, at a line start: the names after it are not the first author
RX_COSIGNER_LABEL = re.compile(r"\s*(?:[-•*]\s*)?(?:liste des |lista dei |liste der )?(?:autres? signataires?|co-?signataires?|"
                               r"mit-?unterzeichn[a-z]*|weitere unterzeichn[a-z]*|co-?firmatar[a-z]*|altri firmatar[a-z]*)"
                               r"(?![a-z])")
# a co-signer cue after a connector: the list of the authors ends here
RX_COSIGNER_CUE = re.compile(r"(?:(?:den |die |der |les |le |i |gli )?(?:weitere[nr]? |autres |altri )?"
                             r"(?:mit-?unter-? ?zeichn|unterzeichn|kons(?:orten|\.)|consorts|co-?signataires|co-?firmatar)|"
                             r"(?:[0-9]+|zwei|drei|vier|funf|sechs|sieben|acht|neun|zehn|elf|zwolf|deux|trois|quatre|"
                             r"cinq|six|sept|huit|neuf|dix|due|tre|quattro|cinque|sei|sette|otto|nove|dieci) )")
# a line of the data of a file ("Autor: ... Speicherdatum ... Pfad"): the author of the file is no author of an affair
RX_FILE_DATA = re.compile(r"(?<![a-z])(?:speicherdatum|druckdatum|dateiname|pfad|status ?:|version ?:|letzte anderung)")
# a group word between a type word and a bracket with the names ("Postulat Fraktion SP/JUSO (Laura Binz/...")
RX_GROUP_WORD = re.compile(r"(?<![a-z])(?:[a-z/!-]*fraktion(?:en)?|interfraktionell[a-z]*|groupes?|gruppo|gruppi|"
                           r"intergroupes?|interpartitic[ao])(?![a-z])")
# a cue directly after a name of 2 or 3 words that follows a type word
RX_AFTER_NAME_CUE = re.compile(r"(?: \((?:" + PARTY + r")[^)]{0,20}\))?(?:,? und (?:mit|kons)|,? et consorts|,? e cofirmatari|"
                               r",? (?:betreffend|betr\.|concernant|riguardante|concernente)(?![a-z]))", re.IGNORECASE)
# the possessive form with a type word in an answer by letter ("alla sua interrogazione", "Ihre Interpellation")
RX_YOUR_AFFAIR = re.compile(r"(?<![a-z])(?:(?:alla|la|della|sulla) (?:sua|vostra|loro)|(?:al|il|del|sul) (?:suo|vostro)|"
                            r"(?:a |sur |de )?(?:votre|vos)|ihre[rnms]?|deine[rnms]?|eure[rnms]?) (?:[a-z]+ ){0,2}?"
                            r"(?:" + TYPE[len("(?<![a-z])"):] + r")")
RX_LABEL_LIKE = re.compile(r"\s*[^\s:][^:\t]{1,38}:\s*$")
RX_FORM_FAMILY = re.compile(r"\s*(?:name|nachname|familienname|nom|cognome)\s*[:\t]\s*(?=\S)")
RX_FORM_FIRST = re.compile(r"\s*(?:vorname|prenom|nome)\s*[:\t]\s*(?=\S)")
RX_ARTICLE = re.compile(r"(?:le |la |les |l'|il |la |den |dem |der |die )?")
RX_SPOKESPERSON = re.compile(r"\((?:sprecher|porte-parole|portavoce)")
RX_ENTRY_PAREN = re.compile(r" ?\((?:[^(),]{2,30}, ?\()?([^(),]{2,30}), ?([^()]{2,20})\)")
RX_ENTRY_GROUP = re.compile(rf"\s*(?:[-•*·]\s*)?([{_UP}][{_UP}{_LO}./' -]{{1,24}}) \(")
RX_CLOSING = re.compile(r"\s*(?:in fede|con (?:la massima )?stima|con ossequi[oa]?|ossequi|cordiali saluti|"
                        r"distinti saluti|(?:mit )?freundliche[nr]? gruss(?:e|en)?|besten dank|"
                        r"(?:avec )?(?:nos|mes) (?:meilleures |cordiales )?salutations|meilleures salutations|"
                        r"cordialement)[.,!]?\s*$")
MEMBER = (r"(?<![a-z])(?:landrat|landratin|lr|kantonsrat|kantonsratin|kr|grossrat|grossratin|einwohnerrat|"
          r"einwohnerratin|parlamentarier(?:in)?|mitunterzeichn[a-z]*|erstunterzeichn[a-z]*|unterzeichner(?:in)?|"
          r"fraktion|fraktionsprasident(?:in)?|fraktionschef(?:in)?|ortspartei|partei|consiglier[ea] comunale|"
          r"granconsiglier[ea]|deputat[oa]|deputee?|conseill(?:er|ere) (?:general|communal)e?|capogruppo|gruppo|"
          r"groupe|chef(?:fe)? de groupe|mitglied des (?:grossen )?(?:gemeinde|stadt|einwohner|kantons|land)rate?s)(?![a-z])")
RX_MEMBER = re.compile(MEMBER)
RX_OFFICIAL = re.compile(
    r"(?<![a-z])(?:im namen|namens|au nom d|a nome d|per il municipio|per il consiglio|pour le conseil|"
    r"der stadtrat|der gemeinderat|der regierungsrat|le conseil (?:communal|municipal|d'etat|executif)|"
    r"il municipio|il consiglio di stato|[a-z]*schreiber(?:in)?|[a-z]*kanzler(?:in)?|kanzleidirektor(?:in)?|"
    r"chanceli(?:er|ere)|secretaire|segretari[oa]|cancellier[ea]|sindaco|syndic|syndique|landammann|"
    r"[a-z]*statthalter|auftraggeber|chef(?:fe)? (?:de l'|du |de la |de (?!groupe))|office federal|bundesamt|"
    r"ufficio federale|staatssekretariat|secretariat d'etat|abteilung|dienststelle|"
    r"[a-z]*ammann|[a-z]*sekretar(?:in)?|sachbearbeiter(?:in)?|verfasst durch|[a-z]*leiter(?:in)?|vorsteher(?:in)?|"
    r"[a-z]*direktor(?:in)?|direttor[ei]|direttrice|directeur|directrice|responsable|"
    r"(?:regierungs|stadt|gemeinde|rats|landrats|kantonsrats|grossrats|einwohnerrats|parlaments|kommissions|"
    r"bundes|vize)?prasident(?:in)?|presidente?|prasidium|buro des|referent(?:in)?|"
    r"departement|dipartimento|direktion|kommission|commission|commissione)(?![a-z])")
RX_ROLE_LINE = re.compile(r"\s*(?:" + MEMBER[len("(?<![a-z])"):-len("(?![a-z])")] + "|" + COUNCIL + r")(?![a-z])")
RX_FOR_GROUP = re.compile(r"\s*(?:fur die|im namen der|namens der|per il|per la|pour le|au nom du) .{0,30}"
                          r"(?:fraktion|gruppo|groupe|partei|parti|lista|liste)")
RX_MEMBER_OVERRIDE = re.compile(r"(?<![a-z])(?:[a-z]*fraktion[a-z]*|groupe|gruppo|partei|parti|partito|capogruppo|"
                                r"einwohnerrat|landrat|kantonsrat|grossrat)(?![a-z])")
RX_ADDRESSEE = re.compile(r"\s*(?:herrn?\b|frau\b|an\b|a l'att|monsieur\b|madame\b|egregi|onorevol|spett|c/o|z\. ?h|"
                          r"zuhanden|zu handen|.*prasident(?:in)?\s*$|.*prasidium\s*$|.*presidente?\s*$|.*buro des )")
RX_GOV_HEAD = re.compile(
    r"\s*(?:bericht und antrag|botschaft|messaggio|beschluss des|auszug aus dem protokoll|protokollauszug|"
    r"rapport d[ue]|reponse d[ue]|beantwortung|antwort des|stellungnahme des|risposta|weisung|vernehmlassung|"
    r"aktennotiz|(?:der |die )?[a-z]+(?:rat|regierung) an (?:den|das|die) |le conseil [a-z' ]{4,20} au |"
    r"il (?:municipio|consiglio di stato) al |der [a-z]+ beschliesst|"
    r"beschliesst:|expertenmeinung|gutachten|medienmitteilung|communique)")
RX_TYPE_GUARD = re.compile(TYPE + r"|(?<![a-z])(?:auftrag|einzelinitiative|initiative|iniziativa|volksmotion|fragestunde)(?![a-z])")
RX_SUBMIT_AFTER = re.compile(r"(?: \([^)]{1,30}\))?(?:, [^,]{2,25},|, [a-z/!.-]{2,12}(?= und | et | e ))?(?: [a-z/-]{2,20}){0,2},? "
                             r"(?:hat|haben|reicht|reichen|reichte|reichten|a depose|ont depose|ha presentato|hanno presentato|"
                             r"ha inoltrato|hanno inoltrato) ")
RX_SUBMIT_BEFORE = re.compile(r"(?:(?:reicht(?:e|en)|hat|haben)(?: am [0-9a-z. ]{6,22})?(?: (?:die|der|den))?|"
                              r"groupe [^,]{2,30},? par|gruppo [^,]{2,30},? da|eingereicht von|deposee? par|"
                              r"(?:inoltrat[aeoi]|presentat[aeoi]|depositat[aeoi]) (?:il [0-9a-z° ]{6,22} )?"
                              r"(?:da|dal|dalla|dai|dagli|dalle)) $")
# a member title before the name, and a submission verb later in the same sentence
RX_SUBMIT_LATER = re.compile(r"(?:[^.;!?]|(?<=[0-9])\.|(?<=nr)\.){0,400}?(?<![a-z])(?:eingereicht(?:e[nrs]?)?|einreicht(?:e|en)?|"
                             r"eingegeben|unterbreitet(?:e|en)?|gestellt|a depose|ont depose|ha presentato|hanno presentato|ha inoltrato|hanno inoltrato)(?![a-z])")
RX_EXEC_AFTER = re.compile(
    r",? (?:regierungs(?:rat|ratin|prasident(?:in)?)|staats(?:rat|ratin|schreiber(?:in)?)|bundes(?:rat|ratin|prasident(?:in)?)|"
    r"stadtprasident(?:in)?|gemeindeprasident(?:in)?|stadtammann|gemeindeammann|landammann|statthalter|"
    r"stadtschreiber(?:in)?|gemeindeschreiber(?:in)?|conseill(?:er|ere) d'etat|conseill(?:er|ere) federale?|"
    r"consiglier[ea] di stato|sindaco|syndic|syndique|chanceli(?:er|ere)|cancellier[ea]|"
    r"departements?(?:vorsteher(?:in)?|chef(?:in)?)|direktor(?:in)?|vorsteher(?:in)?)(?![a-z])")
RX_SENT_BREAK = re.compile(r"(?<![0-9])(?<! nr)(?<! art)(?<! abs)(?<! bzw)(?<! betr)[.;!?] |: ")
RX_RESP_PREFIX = re.compile(r"\s*(?:[0-9][0-9a-z./ -]{0,20} )?(?:(?:schriftliche|mundliche) )?(?:beantwortung|antwort|stellungnahme|bericht|"
                            r"reponse|risposta|rapporto?|prise de position|preavis|avis)(?![a-z])")
RX_DATE_LEAD = re.compile(r"\s*(?:[a-z][a-z .'-]{1,24},? (?:den |le |il |li )?)?[0-9]{1,2}(?:\.|er|°)? ?"
                          r"(?:[0-9]{1,2}\.|[a-z]{3,9}\.?) ?[0-9]{2,4}\s*(?:[-–,:]\s*|\s)")
RX_ANNEX = re.compile(r"\s*(?:allegat[oi]|beilagen?|annexes?|anhang|anhange)\s*(?::|$)")
RX_SALUTE_LINE = re.compile(r"\s*(?:egregi[oa]? |gentil[ei] |onorevol[ei] )?(?:signor[aei]?|signore|herrn?|frau|monsieur|"
                            r"madame|messieurs|mesdames)(?: (?:e|ed|und|et) (?:egregi[oa]? |gentil[ei] )?"
                            r"(?:signor[aei]?|signore|herrn?|frau|monsieur|madame|messieurs|mesdames))?\s*$")
RX_MEMBER_LINE = re.compile(r"\s*(?:deputat[oaie] al gran consiglio|granconsiglier[eai]|consiglier[eai](?:/[eai])? comunal[ei]|"
                            r"deputee?s? au grand conseil|conseill(?:ers?|eres?) (?:genera(?:le?s?|ux)|communa(?:le?s?|ux))|"
                            r"mitglied(?:er)? des [a-z]+rate?s|" + COUNCIL + r")\s*$")
RX_NAME_LINE_REST = re.compile(r"\s*(?:$|[,(/|]|[-–]\s|\s*(?:fur|per|pour|und|et|e) )")


def sfold(s: str) -> str:
    """A folded copy with the SAME length as the input: lower case, no accents, typographic quotes and dashes as
    ASCII, each white space except the tab as one space character, soft hyphen as a hyphen. A position in the copy
    is the same position in the input."""
    out = []
    for c in s:
        if c == "\t":
            out.append("\t")
            continue
        if c.isspace() or c == "\u2423":                  # also the sign of a visible space
            out.append(" ")
            continue
        if c == "­":
            out.append("-")
            continue
        r = base._REPLACE.get(c, c)                       # the replace table of the base file (1 character each)
        d = "".join(x for x in unicodedata.normalize("NFKD", r) if unicodedata.category(x) != "Mn").lower()
        out.append(d if len(d) == 1 else (r.lower() if len(r.lower()) == 1 else r))
    return "".join(out)


def _flat(s: str) -> str:
    """The text as printed, with each line feed and each sign of a visible space as one space (same length)."""
    return s.replace("\n", " ").replace("\r", " ").replace("\u2423", " ")


def _fold_token(t: str) -> str:
    return base.fold(t).replace("'", "")


def _is_non_name(t: str) -> bool:
    f = _fold_token(t)
    return f in NON_NAME or f.endswith(_NON_NAME_SUFFIX) or bool(RX_PARTY.fullmatch(t)) or \
        bool(RX_COUNCIL_WORD.fullmatch(f))


class _Name:
    """A name as printed: span in the text of the search (start, end), tokens and flags."""
    __slots__ = ("start", "end", "tokens", "caps", "first_known")

    def __init__(self, start, end, tokens, caps):
        self.start, self.end, self.tokens, self.caps = start, end, tokens, caps
        words = [t for t, k in tokens if k == "word"]
        self.first_known = bool(words) and _fold_token(words[0]).split("-")[0] in FIRST_NAMES

    @property
    def words(self) -> list[str]:
        return [t for t, k in self.tokens if k == "word"]

    def split(self) -> tuple[list[str], list[str]]:
        """(first names, family name tokens). The family name keeps its particles. With a known first name the
        tokens after the first names are the family name; the last word is always a part of the family name."""
        toks = [(t, k) for t, k in self.tokens if k != "initial"]
        n_words = sum(1 for _, k in toks if k == "word")
        if n_words <= 1 or not self.first_known:
            words = self.words
            if n_words == 2 and _fold_token(words[1]).split("-")[0] in FIRST_NAMES:
                return [words[1]], [words[0]]     # the order family name, first name: "Jung Hans-Ruedi"
            if n_words >= 2:                      # no known first name: the first word is taken as the first name
                i = next(i for i, (_, k) in enumerate(toks) if k == "word")
                return [toks[i][0]], [t for t, _ in toks[i + 1:]]
            return [], [t for t, _ in toks]
        first, i, seen = [], 0, 0
        while i < len(toks):
            t, k = toks[i]
            if k == "word" and seen < n_words - 1 and _fold_token(t).split("-")[0] in FIRST_NAMES:
                first.append(t)
                seen += 1
                i += 1
                continue
            break
        return first, [t for t, _ in toks[i:]]


def first_last_known(name: "_Name") -> bool:
    """True if the last word of a name of 2 words is a known first name (order family name, first name)."""
    w = name.words
    return len(w) == 2 and _fold_token(w[1]).split("-")[0] in FIRST_NAMES


def _name_at(orig: str, pos: int, limit: int | None = None, max_words: int = 4) -> _Name | None:
    """Read a name that starts exactly at `pos` in the text as printed. Tokens: capitalised words, initials and
    name particles, with one space between them. A name in upper case has at most 3 words. The name ends before
    a word of NON_NAME, a party mark or a word in the other case form."""
    limit = len(orig) if limit is None else limit
    toks: list[tuple[str, str]] = []
    spans: list[tuple[int, int]] = []
    i, caps, words = pos, None, 0
    mixed = False                 # "Mathias GAUTSCHI": words in lower case, then the family name in upper case
    while i < limit and words < max_words:
        m = RX_PARTICLE.match(orig, i)
        if m and m.end() <= limit:
            nxt = RX_TOK.match(orig, m.end())
            if nxt and not _is_non_name(nxt.group(0)) and caps is not True:
                toks.append((m.group(0).strip(), "particle"))
                spans.append((m.start(), m.end() - 1))
                i = m.end()
                continue
        m = RX_INITIAL.match(orig, i)
        if m and toks and caps is not True:
            toks.append((m.group(0), "initial"))
            spans.append(m.span())
            i = m.end()
        else:
            m_caps = RX_CAPTOK.match(orig, i)
            m_tok = RX_TOK.match(orig, i)
            if m_caps and (caps is None or caps) and (not m_tok or m_caps.end() >= m_tok.end()):
                m, is_caps = m_caps, True
            elif m_tok and not caps and not mixed:
                m, is_caps = m_tok, False
            elif m_caps and caps is False and words >= 1 and len(m_caps.group(0)) >= 4 and m_caps.end() <= limit and \
                    (mixed or words == 1 or _fold_token(toks[-1][0]).split("-")[0] in FIRST_NAMES) and \
                    not orig[m_caps.end():m_caps.end() + 1].isalpha() and \
                    not _is_non_name(m_caps.group(0)) and sum(1 for t, k in toks if k == "word" and t.isupper()) < 2:
                mixed = True                               # the family name in upper case after the first names
                toks.append((m_caps.group(0), "word"))
                spans.append(m_caps.span())
                words += 1
                i = m_caps.end()
                if i < limit and orig[i] in " \xa0" and i + 1 < limit and orig[i + 1] not in " \xa0":
                    i += 1
                    continue
                break
            elif m_tok and caps is True and words == 1 and m_tok.end() <= limit and \
                    _fold_token(m_tok.group(0)).split("-")[0] in FIRST_NAMES:
                toks.append((m_tok.group(0), "word"))      # "GAUTSCHI Mathias": the first name after the family name
                spans.append(m_tok.span())
                words += 1
                break
            else:
                break
            if toks and not is_caps and _fold_token(m.group(0)) in _CAP_PARTICLES and m.end() < limit and \
                    RX_TOK.match(orig, m.end() + 1) and not _is_non_name(RX_TOK.match(orig, m.end() + 1).group(0)):
                toks.append((m.group(0), "particle"))      # "Gina La Mantia", "Luca De Rosa"
                spans.append(m.span())
                i = m.end() + 1
                continue
            if m.end() > limit:
                break
            if _is_non_name(m.group(0)) and not (
                    _fold_token(m.group(0)) in FAMILY_AFTER_FIRST_NAME and words >= 1 and toks[-1][1] == "word" and
                    _fold_token(toks[-1][0]).split("-")[0] in FIRST_NAMES):
                break
            if is_caps and (len(m.group(0)) < 3 or words >= 3 or
                            (words == 2 and _fold_token(toks[-1][0]).split("-")[0] not in FIRST_NAMES)):
                break                                      # upper case: 2 words, or 3 if the second is a first name
            caps = is_caps
            toks.append((m.group(0), "word"))
            spans.append(m.span())
            words += 1
            i = m.end()
        if i < limit and orig[i] in " \xa0":
            j = i + 2 if i + 1 < limit and orig[i + 1] in " \xa0" else i + 1
            if j < limit and orig[j] not in " \xa0":
                i = j
            else:
                break
        else:
            break
    while toks and toks[-1][1] != "word":
        toks.pop()
        spans.pop()
    while toks and toks[0][1] == "initial":
        toks.pop(0)
        spans.pop(0)
    # "von Anna Muster": a particle before 2 or more name words is a preposition of the text
    if toks and toks[0][1] == "particle" and sum(1 for _, k in toks if k == "word") >= 2 and toks[1][1] == "word":
        toks.pop(0)
        spans.pop(0)
    def known(t: str) -> bool:
        return _fold_token(t).split("-")[0] in FIRST_NAMES

    # "Von Patrik Brunner" at a line start: a capitalised preposition before a first name is no part of the name
    if len(toks) >= 3 and toks[0][1] == "word" and _fold_token(toks[0][0]) in _CAP_PARTICLES and \
            toks[1][1] == "word" and known(toks[1][0]):
        toks.pop(0)
        spans.pop(0)
    # 2 names with no mark between them ("Alexander Umbricht Peter Jann"): the name ends before the second
    # first name that comes after a family name word and has one more word after it
    family_seen = False
    for k, (t, kind) in enumerate(toks):
        if kind != "word":
            continue
        if k and family_seen and known(t) and k + 1 < len(toks) and known(toks[0][0]):
            del toks[k:]
            del spans[k:]
            break
        if k and not known(t):
            family_seen = True
    while toks and toks[-1][1] != "word":
        toks.pop()
        spans.pop()
    if not any(k == "word" for _, k in toks):
        return None
    return _Name(spans[0][0], spans[-1][1], toks, bool(caps) and not any(t[:1].isupper() and t[1:].islower()
                                                                           for t, k in toks if k == "word"))


def _party_after(orig: str, end: int) -> dict | None:
    """The party or group mark directly after a name: {mark, start, end} with positions in `orig`."""
    seg_end = min(len(orig), end + 60)
    m = RX_PARTY_AFTER.match(orig, end, seg_end)
    if m:
        return {"mark": m.group(1), "start": m.start(1), "end": m.end(1)}
    m = RX_PAREN_AFTER.match(orig, end, seg_end)
    if m:
        p = RX_PARTY.search(m.group(1))
        if p:
            return {"mark": p.group(0), "start": m.start(1) + p.start(), "end": m.start(1) + p.end()}
    return None


def _official_line(low: str) -> bool:
    """True if a folded line has a cue of the executive or of an official, and no cue of a member group."""
    return bool(RX_OFFICIAL.search(low)) and not RX_MEMBER_OVERRIDE.search(low)


class _Reader:
    """The search of one document. All positions that leave this class are positions in Doc.text."""

    def __init__(self, doc: Doc, signatures: bool = True):
        self.doc = doc
        self.signatures = signatures
        self.lines = list(doc.lines)
        self.low_lines = [sfold(ln.text) for ln in self.lines]
        self.found: list[tuple[str, int, int, _Name, dict]] = []      # tier, start, end, name, detail
        self.saw_name = False
        # a cue of a document of the executive at the start of one of the first 12 lines
        self.gov_head = any(RX_GOV_HEAD.match(x) for k, x in enumerate(self.low_lines[:HEAD_LINES_SENDER])
                            if k == 0 or self.lines[k - 1].block_index != self.lines[k].block_index)
        # a type word in the first 25 lines: necessary for the tiers that read a head sender or a signature
        self.type_in_head = any(RX_TYPE_GUARD.search(x) for x in self.low_lines[:HEAD_LINES_TYPE])

    # ---- helpers
    def add(self, tier: str, base_pos: int, orig: str, name: _Name, cue: str, extra: dict | None = None,
            co: list | None = None) -> None:
        """Keep one candidate. `co`: the further authors that the same cue prints, as (name, text, start of the
        text in Doc.text); they go to detail.co_authors and to the list `others` with the tier co_author."""
        first, family = name.split()
        det = {"printed_name": base.norm_text(orig[name.start:name.end]), "first_names": " ".join(first),
               "family_name": " ".join(family), "cue": cue}
        if len(name.words) >= 2 and not name.first_known and not first_last_known(name):
            det["split_uncertain"] = True     # no word of the name is in the list of first names
        p = _party_after(orig, name.end)
        if p:
            det["party"] = {"mark": p["mark"], "char_start": base_pos + p["start"], "char_end": base_pos + p["end"]}
        if extra:
            det.update(extra)
        if co:
            det["co_authors"] = [{"printed_name": base.norm_text(o[n.start:n.end]), "char_start": b + n.start,
                                  "char_end": b + n.end, "normalised": _co_norm(n)} for n, o, b in co]
        self.found.append((tier, base_pos + name.start, base_pos + name.end, name, det))

    def more_names(self, orig: str, low: str, end: int, limit: int | None = None, loose: bool = False,
                   raw: str | None = None) -> list[_Name]:
        """The further names of a list of authors that starts with the name that ends at `end`: names after a
        comma, a slash, "&", "und", "sowie", "et", "e". A bracket, a party mark and one place word after a name
        are no names. The list ends before a co-signer cue ("und Mitunterzeichnende", "et consorts", a count).
        loose=False: a further name needs a known first name or a title. raw: the text with its line feeds; a
        further name does not go over a line end."""
        limit = len(orig) if limit is None else limit
        out: list[_Name] = []
        pos = end
        while len(out) < 8 and pos < limit:
            m = re.match(r" ?\([^()\n]{1,40}\)", orig[pos:limit])
            if m:
                pos += m.end()
            m = re.match(r"(?:, ?| )(?:" + PARTY + r")(?:[/-][A-Za-zÀ-ÿ!]+)*(?![A-Za-zÀ-ÿ])", orig[pos:limit])
            if m:
                pos += m.end()
            m = re.match(rf", ([{_UP}][{_LO}.-]+)(?=,? (?:und|sowie|et|e|ed) |, )", orig[pos:limit])
            if m and _fold_token(m.group(1)).split("-")[0] not in FIRST_NAMES and \
                    not re.match(rf", [{_UP}][{_LO}-]+ [{_UP}][{_LO}]", orig[pos:limit]):
                pos += m.end()                                 # a place word: "..., Stans, und Landrat ..."
            m = re.match(r"(?:,? (?:und|sowie|et|e|ed) | ?[/&;] ?|, ?)", low[pos:limit])
            if not m:
                break
            p2 = pos + m.end()
            if RX_COSIGNER_CUE.match(low, p2):
                break
            lim = limit
            if raw is not None:
                t = RX_TITLES.match(low, p2)
                nl = raw.find("\n", t.end() if t else p2, limit)
                lim = nl if nl >= 0 else limit
            name, has_title, executive = self.name_after(orig, low, p2, lim)
            if name is None or executive:
                break
            two = len(name.words) >= 2
            if not ((two and (name.first_known or first_last_known(name) or loose)) or has_title):
                break
            out.append(name)
            pos = name.end
        return out

    def name_after(self, orig: str, low: str, pos: int, limit: int | None = None,
                   initials: bool = False) -> tuple[_Name | None, bool, bool]:
        """(name, a title stands before the name, the title is a title of the executive) for a name that starts
        at `pos` after optional titles. initials=True: 1 or 2 initials before a family name count as a title
        ("Postulat von A. Abdurahman")."""
        m = RX_TITLES.match(low, pos)
        start = m.end() if m else pos
        name = _name_at(orig, start, limit)
        has_title = start > pos
        if name is None and initials:
            ini = re.match(rf"(?:[{_UP}]\. ?){{1,2}}(?=[{_UP}][{_LO}])", orig[start:])
            if ini:
                name = _name_at(orig, start + ini.end(), limit)
                has_title = name is not None
        executive = bool(RX_EXEC_TITLE.search(low[max(0, start - 45):start]))
        if name is not None and RX_EXEC_AFTER.match(low, name.end):
            executive = True
        return name, has_title, executive

    def name_line(self, i: int, need_first: bool = True) -> tuple[_Name, str, int] | None:
        """If line i is a name line, (name, text of the line, start of the line in Doc.text). A name line: an
        optional bullet, optional titles, a name with a known first name, then the line end or a comma, a bracket,
        a dash or a short group phrase. Also "<group mark>, <name>"."""
        ln = self.lines[i]
        orig, low = ln.text, self.low_lines[i]
        if len(orig) > 130:
            return None
        m = re.match(r"\s*(?:[-•*·]\s*)?", low)
        starts = [m.end()]
        comma = low.find(", ")
        if 0 < comma <= 40 and (RX_MEMBER.search(low[:comma]) or RX_PARTY.search(orig[:comma])):
            lead = self.name_after(orig, low, m.end())[0]
            if (lead is None or len(lead.words) < 2 or lead.end > comma) and len(low[:comma].split()) <= 4:
                # a short group phrase before the comma, and no person name
                starts.append(comma + 2)
        d = RX_DATE_LEAD.match(low)
        if d and d.end() < len(low):
            starts.append(d.end())
        for pos in starts:
            name, _, executive = self.name_after(orig, low, pos)
            if name is None or executive or len(name.words) < 2 or \
                    (need_first and not (name.first_known or first_last_known(name))):
                continue
            if len(orig) > 90 and not RX_PAREN_AFTER.match(orig, name.end):
                continue                                       # a long line: only with a bracket after the name
            if not need_first and (name.caps or len(name.words) > 3 or len(orig) > 60 or
                                   any(len(w) < 3 for w in name.words)):
                continue
            nxt = self.lines[i + 1] if i + 1 < len(self.lines) else None
            if len(orig) >= 50 and nxt is not None and nxt.block_index == ln.block_index and \
                    nxt.text[:1].islower() and not (RX_MEMBER.search(low[name.end:]) or RX_PARTY.search(orig[name.end:])):
                continue                                       # the line goes on as running text
            if RX_NAME_LINE_REST.match(low, name.end) or RX_MEMBER.match(low, name.end + 1) or \
                    RX_PARTY.match(orig, name.end + 1) or (need_first and _party_after(orig, name.end)):
                return name, orig, ln.char_start
            second = _name_at(orig, name.end + 1) if need_first and name.end + 1 < len(orig) else None
            if second is not None and second.first_known and len(second.words) >= 2:
                return name, orig, ln.char_start               # 2 names side by side on one line
        return None

    def marked_name_line(self, i: int) -> tuple[_Name, str, int] | None:
        """A name line whose first name is not in the list, with a member mark or a party mark on the same line
        after the name ("Corin Ballhaus, Einwohnerrätin SVP")."""
        got = self.name_line(i, need_first=False)
        if got:
            name, orig, _ = got
            rest_low, rest = self.low_lines[i][name.end:], orig[name.end:]
            if RX_MEMBER.search(rest_low) or RX_PARTY.search(rest) or \
                    RX_MEMBER_TITLE.search(self.low_lines[i][:name.start]):
                return got
            if not rest.strip(" ,"):                           # a line with the name only
                nxt = self.low_lines[i + 1] if i + 1 < len(self.lines) else ""
                prv = self.low_lines[i - 1] if i else ""
                if RX_ROLE_LINE.match(nxt) or RX_FOR_GROUP.match(prv):
                    return got
        return None

    def title_mark(self, i: int, name: _Name) -> str | None:
        m = RX_MEMBER_TITLE.search(self.low_lines[i][:name.start])
        return m.group(0).strip(" \t(") if m else None

    def official_near(self, i: int, before: int = 3, after: int = 1) -> bool:
        lo, hi = max(0, i - before), min(len(self.lines), i + after + 1)
        page = self.lines[i].page
        # a line of running text is no signature line: only short lines count
        return any(_official_line(self.low_lines[k]) for k in range(lo, hi)
                   if self.lines[k].page == page and len(self.lines[k].text) <= 60)

    def member_near(self, i: int, before: int = 2, after: int = 2) -> str | None:
        """A member mark, a party mark or a signer cue on line i or beside it (the cue text or None)."""
        lo, hi = max(0, i - before), min(len(self.lines), i + after + 1)
        for k in [i] + [x for x in range(lo, hi) if x != i]:
            if abs(self.lines[k].block_index - self.lines[i].block_index) > 1:
                continue
            m = RX_MEMBER.search(self.low_lines[k]) or (RX_ROLE_LINE.match(self.low_lines[k]) if k == i + 1 else None)
            if m:
                return m.group(0).strip()
            p = RX_PARTY.search(self.lines[k].text)
            if p:
                return p.group(0)
        return None

    # ---- tiers with a label cue
    def entry_line(self, i: int) -> tuple[_Name, str, int, str] | None:
        """If line i is a list entry "<family name> (<place>, <mark>)": (name, text of the line, start of the line
        in Doc.text, mark). The entry prints no first name (form of a signer list)."""
        ln = self.lines[i]
        orig, low = ln.text, self.low_lines[i]
        m = re.match(r"\s*(?:[-•*·]\s*)?", low)
        name = _name_at(orig, m.end(), max_words=3)
        if name is not None and not name.caps:
            e = RX_ENTRY_PAREN.match(orig, name.end)
            if e:
                return name, orig, ln.char_start, e.group(2).strip()
        # the group first and the name in the bracket: "PS-JS (Riesen, La Neuveville) (porte-parole)"
        g = RX_ENTRY_GROUP.match(orig)
        if g:
            name = _name_at(orig, g.end(), max_words=3)
            if name is not None and not name.caps and re.match(r", ?[^()]{2,30}\)", orig[name.end:]):
                return name, orig, ln.char_start, g.group(1).strip()
        return None

    def labels(self) -> None:
        doc = self.doc
        for b in doc.blocks:
            if not b.text:
                continue
            in_head = bool(b.lines) and b.lines[0].number < HEAD_LINES_TYPE
            if b.rule_role in base.RESPONSE_ROLES and not in_head:
                continue
            orig = _flat(b.text)
            low = sfold(orig)
            for m in RX_LABEL.finditer(low):
                # the word before the cue must not make a co-signer cue ("Mit-unterzeichner", "co-firmatari")
                if re.search(r"(?:mit|co|weitere|autres|altri|zweit)[- ]?$", low[max(0, m.start() - 9):m.start()]):
                    continue
                if b.label == "footnote":
                    continue                                   # a footnote names a different affair
                pos = RX_LABEL_TAIL.match(low, m.end()).end()
                t = re.match(r"[ \t]*(:?)[ \t]*:?[ \t]*", low[pos:])
                colon = bool(t.group(1)) or "\t" in t.group(0)
                pos += t.end()
                if "\n" in b.text[m.end():pos]:
                    continue                                   # the name is on the next line: tier label_next_lines
                pos = RX_ARTICLE.match(low, pos).end()
                eol = b.text.find("\n", pos)                   # a name after a label does not go over a line end
                eol = eol if eol >= 0 else None
                sol = b.text.rfind("\n", 0, m.start()) + 1
                if RX_FILE_DATA.search(low[sol:eol]):
                    continue                                   # the data of a file: "Autor: ... Speicherdatum ..."
                extra = None
                g = re.match(r"(?:" + PARTY + r")[^/\n\t]{0,30} / (?=\S)", orig[pos:eol])
                if g and colon:                                # the group before the name: "PLR VDB / Martine Tristan"
                    extra = {"group_before_the_name": orig[pos:pos + g.end() - 3].strip()}
                    pos += g.end()
                name, has_title, executive = self.name_after(orig, low, pos, eol)
                if name is not None and not colon and eol is not None and len(name.words) == 1 and name.end == eol:
                    # a label in a sentence ("presentata il ... da Tuto / Rossi"): the name goes on in the next line
                    longer = self.name_after(orig, low, pos)
                    if longer[0] is not None and len(longer[0].words) == 2 and name.first_known:
                        name, has_title, executive = longer
                        eol = None
                if name is None or executive:
                    continue
                self.saw_name = True
                two = len(name.words) >= 2
                first_signer = m.group(0).startswith(("erstunterzeichn", "premi", "prim")) or \
                    "signataire" in low[m.start():pos] and "premi" in low[m.start():pos]
                if (colon and two) or (name.first_known and two) or (has_title and (colon or two)) or \
                        (first_signer and two and not name.caps):
                    co = self.more_names(orig, low, name.end, eol)
                    self.add("label_same_line", b.char_start, orig, name, low[m.start():RX_LABEL_TAIL.match(low, m.end()).end()],
                             extra, [(n, orig, b.char_start) for n in co])
        for i, low in enumerate(self.low_lines):
            # a name and then the cue in brackets or after a comma: "Gregorio Aostalli (primo firmatario)"
            for m in RX_LABEL.finditer(low):
                if not m.group(0).startswith(("erstunterzeichn", "premi", "prim", "urheber", "motionar",
                                              "postulant", "interpellant")):
                    continue
                lead = re.search(r"(?:, | \(| - )$", low[:m.start()])
                if not lead:
                    continue
                orig = self.lines[i].text
                seg_start = max(low.rfind("\t", 0, lead.start()), -1) + 1
                st = re.match(r"\s*(?:[-•*·]\s*)?", low[seg_start:]).end() + seg_start
                name, _, executive = self.name_after(orig, low, st)
                if name is not None and not executive and len(name.words) >= 2 and name.end == lead.start():
                    self.saw_name = True
                    self.add("label_same_line", self.lines[i].char_start, orig, name, m.group(0),
                             {"form": "name before the cue"})
            if len(low) <= 50 and RX_LABEL.search(low) and self.form_fields(i, low.strip(" :()")):
                continue
            lm = RX_LABEL_ONLY.fullmatch(low)
            if not lm:
                continue
            blk = doc.blocks[self.lines[i].block_index]
            if blk.rule_role in base.RESPONSE_ROLES and i >= HEAD_LINES_TYPE:
                continue
            colon = bool(lm.group(1))
            cue = low.strip(" :()")
            got_after = None
            for k in range(i + 1, min(i + 4, len(self.lines))):
                cl = RX_COSIGNER_LABEL.search(self.low_lines[k])
                if cl:                                         # the list of the other signers starts
                    if self.low_lines[k][:cl.start()].strip():
                        nm = self.name_after(self.lines[k].text, self.low_lines[k], 0, cl.start())[0]
                        if nm is not None and len(nm.words) >= 2 and not self.low_lines[k][nm.end:cl.start()].strip():
                            got_after = (k, (nm, self.lines[k].text, self.lines[k].char_start), None)
                    break
                if _official_line(self.low_lines[k]):
                    continue
                got = self.name_line(k) or self.marked_name_line(k) or (self.name_line(k, need_first=False)
                                            if colon and k == i + 1 and cue.startswith("erstunterzeichn") else None)
                if got:
                    got_after = (k, got, None)
                    break
                ent = self.entry_line(k)
                if ent:
                    got_after = (k, ent[:3], ent[3])
                    break
            got_before = None
            if not colon and i > 0 and not _official_line(self.low_lines[i - 1]):
                gb = self.name_line(i - 1, need_first=False)
                if gb and len(self.lines[i - 1].text) <= 60:
                    got_before = gb
            if got_before and got_after and got_after[0] == i + 1:
                continue                                       # a name on each side of a label with no colon
            if got_before:
                name, orig, start = got_before
                self.add("label_next_lines", start, orig, name, cue, {"form": "name line before the label"})
            elif got_after:
                k, (name, orig, start), mark = got_after
                extra = {"lines_after_label": k - i}
                if mark:
                    extra["entry_mark"] = mark
                co = [] if mark else self.more_names(orig, self.low_lines[k], name.end)
                self.add("label_next_lines", start, orig, name, cue, extra, [(n, orig, start) for n in co])
            elif colon:
                self.label_column(i, cue)
        # a list entry with the mark of the spokesperson: "Vogt (Oberdiessbach, PLR) (porte-parole)"
        for i, low in enumerate(self.low_lines):
            if not RX_SPOKESPERSON.search(low):
                continue
            for k in (i, i - 1):
                if k < 0 or (k != i and not RX_SPOKESPERSON.match(low.strip())):
                    continue
                ent = self.entry_line(k)
                if ent:
                    name, orig, start, mark = ent
                    self.saw_name = True
                    self.add("spokesperson_entry", start, orig, name, RX_SPOKESPERSON.search(low).group(0),
                             {"entry_mark": mark})
                    break
            else:
                continue
            break

    def label_column(self, i: int, cue: str) -> None:
        """A form that prints a column of labels and then the column of the values: the label of line i is one of
        3 or more lines with a label only, one after the other. The value is the first name line in the 8 lines
        after the label column. The rule needs the label of the co-signers after the label of the author (then
        the first name line is the author)."""
        n = len(self.lines)
        a = i
        while a > 0 and RX_LABEL_LIKE.match(self.low_lines[a - 1]):
            a -= 1
        z = i
        while z + 1 < n and RX_LABEL_LIKE.match(self.low_lines[z + 1]):
            z += 1
        if z - a + 1 < LABEL_COLUMN_MIN or z == i:
            return
        if any(RX_COSIGNER_LABEL.match(self.low_lines[k]) for k in range(a, i)):
            return
        for k in range(z + 1, min(z + 1 + LABEL_COLUMN_REACH, n)):
            if RX_COSIGNER_LABEL.match(self.low_lines[k]) or _official_line(self.low_lines[k]):
                return
            got = self.name_line(k) or self.marked_name_line(k)
            if got:
                name, orig, start = got
                self.saw_name = True
                self.add("label_column_form", start, orig, name, cue,
                         {"labels_in_column": z - a + 1, "lines_after_column": k - z})
                return

    def form_fields(self, i: int, cue: str) -> bool:
        """A form with one field for the family name and one field for the first name below a heading that is a
        label of the author ("1. Personalien Motionsteller" / "Name<tab>Herbst" / "Vorname<tab>Adrian"). The value
        is the family name (the 2 parts are not one after the other in the text)."""
        fam = first = None
        for k in range(i + 1, min(i + 4, len(self.lines))):
            f = RX_FORM_FIRST.match(self.low_lines[k])
            g = RX_FORM_FAMILY.match(self.low_lines[k])
            if f and first is None:
                first = (k, f.end())
            elif g and fam is None:
                fam = (k, g.end())
        if not fam or not first:
            return False
        k, pos = fam
        orig = self.lines[k].text
        name = _name_at(orig, pos, max_words=3)
        fk, fpos = first
        first_name = _name_at(self.lines[fk].text, fpos, max_words=3)
        if name is None or first_name is None or orig[name.end:].strip() or self.lines[fk].text[first_name.end:].strip():
            return False
        self.saw_name = True
        self.found.append(("label_form_fields", self.lines[k].char_start + name.start, self.lines[k].char_start + name.end,
                           name, {"printed_name": base.norm_text(orig[name.start:name.end]),
                                  "first_names": base.norm_text(self.lines[fk].text[first_name.start:first_name.end]),
                                  "family_name": " ".join(t for t, _ in name.tokens), "cue": cue,
                                  "form": "one field for the family name and one field for the first name",
                                  "family_only_value": True}))
        return True

    # ---- tiers with a type word
    @staticmethod
    def heading_form(b, low: str, pos: int) -> bool:
        """True if the type word at `pos` is in the form of a heading: the block is a heading, or at most 2 words
        stand between the start of the sentence and the type word, or the sentence starts with a response noun
        ("Beantwortung der Interpellation von ..."). False: the type word is in a sentence of running text."""
        if b.label in ("section_header", "title"):
            return True
        seg_start = max(0, pos - 160)
        seg = low[seg_start:pos]
        cut = max((x.end() for x in RX_SENT_BREAK.finditer(seg)), default=None)
        if cut is None and seg_start > 0:
            return False
        pre = seg[cut or 0:]
        if RX_RESP_PREFIX.match(pre):
            return True
        return len(re.findall(r"[a-z]{2,}", pre)) <= 2

    def type_words(self) -> None:
        doc = self.doc
        for b in doc.blocks:
            if not b.lines or b.lines[0].number >= HEAD_LINES_TYPE:
                continue
            orig = _flat(b.text)
            low = sfold(orig)
            for m in RX_TYPE.finditer(low):
                heading = self.heading_form(b, low, m.start())
                # the head of a document of the executive that names the author of the proposal: a tier of its own
                resp = heading and self.response_head(low, m.start())
                kind_tier = {"type_prep_name": "response_head_prep_name", "type_full_name": "response_head_full_name"}
                tier_of = (lambda t: "type_in_sentence") if not heading else \
                    (lambda t: kind_tier.get(t, t)) if resp else (lambda t: t)
                pos = m.end()
                n = RX_TYPE_NUMBER.match(low, pos)
                if n:
                    pos = n.end()
                if self.group_bracket(b, orig, low, m, pos, heading) or self.separator_name(b, orig, low, m, pos, heading):
                    continue
                p = RX_PREP.match(low, pos)
                if p:
                    name, has_title, executive = self.name_after(orig, low, p.end(),
                                                                 initials=bool(RX_WEAK_PREP.match(low, pos)))
                    if name is not None and not executive:
                        self.saw_name = True
                        if (name.first_known and len(name.words) >= 2) or has_title or \
                                (RX_WEAK_PREP.match(low, pos) and not name.caps and 2 <= len(name.words) <= 3):
                            co = self.more_names(orig, low, name.end, raw=b.text)
                            self.add(tier_of("type_prep_name"), b.char_start, orig, name, low[m.start():p.end()].strip(),
                                     None, [(x, orig, b.char_start) for x in co])
                        elif RX_WEAK_PREP.match(low, pos) and not name.caps:
                            self.add(tier_of("type_family_name"), b.char_start, orig, name,
                                     low[m.start():p.end()].strip())
                        continue
                if pos < len(low) and low[pos] == " ":
                    name, has_title, executive = self.name_after(orig, low, pos + 1)
                    if name is not None and not executive:
                        if name.first_known and len(name.words) >= 2:
                            self.saw_name = True
                            co = self.more_names(orig, low, name.end, raw=b.text)
                            self.add(tier_of("type_full_name"), b.char_start, orig, name, m.group(0),
                                     None, [(x, orig, b.char_start) for x in co])
                            continue
                        if len(name.words) <= 3 and not name.caps and RX_ENTRY_PAREN.match(orig, name.end):
                            self.saw_name = True
                            self.add(tier_of("type_entry_name"), b.char_start, orig, name, m.group(0),
                                     {"entry_mark": RX_ENTRY_PAREN.match(orig, name.end).group(2).strip()})
                            continue
                        # 2 or 3 name words with no known first name, and a cue directly after the name: a
                        # party mark in a bracket, a co-signer cue or the word that starts the title
                        if 2 <= len(name.words) <= 3 and not name.caps and all(len(w) >= 3 for w in name.words) and \
                                RX_AFTER_NAME_CUE.match(orig, name.end):
                            self.saw_name = True
                            self.add(tier_of("type_name_cue_after"), b.char_start, orig, name, m.group(0),
                                     {"cue_after": RX_AFTER_NAME_CUE.match(orig, name.end).group(0).strip(" ,")})
                            continue
                        # one family name with a mark after it; 2 words only with a party mark or a co-signer cue
                        after = RX_AFTER_FAMILY if len(name.words) == 1 else RX_AFTER_FAMILY_STRICT
                        numbered_line_end = len(name.words) == 1 and b.text[name.end:name.end + 1] in ("", "\n") and \
                            re.search(r"(?:^|\n)\s*[0-9]{2}\.[0-9]{3,4} $", b.text[:m.start()].lower()) is not None
                        if len(name.words) <= 2 and not name.caps and (after.match(orig, name.end) or numbered_line_end):
                            self.saw_name = True
                            self.add(tier_of("type_family_name"), b.char_start, orig, name, m.group(0))
                            continue
                # title words between the type word and the preposition, in the same sentence
                seg_end = min(len(low), pos + 110)
                stop = re.search(r"[.;?!] ", low[pos:seg_end])
                if stop:
                    seg_end = pos + stop.start()
                for g in re.finditer(r" (?:von|de|di|da|der|des) ", low[pos:seg_end]):
                    name, has_title, executive = self.name_after(orig, low, pos + g.end())
                    if g.group(0) in (" der ", " des ") and not has_title:
                        continue
                    if name is not None and not executive and name.first_known and len(name.words) >= 2:
                        self.saw_name = True
                        self.add(tier_of("type_full_name"), b.char_start, orig, name,
                                 m.group(0) + " ..." + g.group(0).rstrip())
                        break

        # a line "von <name>" directly after a line that ends with a type word (2 blocks)
        for i in range(1, min(HEAD_LINES_TYPE, len(self.lines))):
            low = self.low_lines[i]
            g = re.match(r"\s*(?:von|de|di|da|par) ", low)
            t = RX_TYPE.search(self.low_lines[i - 1])
            if not g or not t or self.low_lines[i - 1][t.end():].strip(" :"):
                continue
            orig = self.lines[i].text
            name, has_title, executive = self.name_after(orig, low, g.end())
            if name is not None and not executive and (has_title or (len(name.words) >= 2 and name.first_known)):
                self.saw_name = True
                resp = self.response_head(self.low_lines[i - 1], t.start())
                co = self.more_names(orig, low, name.end)
                self.add("response_head_prep_name" if resp else "type_prep_name", self.lines[i].char_start, orig, name,
                         t.group(0) + " /" + g.group(0).rstrip(), {"form": "type word at the end of the line before"},
                         [(x, orig, self.lines[i].char_start) for x in co])

        # the first type word in the form of a heading with a name names the affair of the document; a later
        # type word with a different name can name a different affair (a weak candidate)
        strong = [k for k, it in enumerate(self.found) if it[0] in STRONG_TYPE_TIERS]
        if len(strong) > 1:
            k0 = min(strong, key=lambda k: self.found[k][1])
            fam0 = set(_co_norm(self.found[k0][3]).split())
            co0 = {w for c in self.found[k0][4].get("co_authors", ()) for w in c["normalised"].split()}
            for k in strong:
                tier, a, z, name, det = self.found[k]
                fam = set(_co_norm(name).split())
                if k != k0 and fam and not (fam & (fam0 | co0)):
                    self.found[k] = ("type_in_sentence", a, z, name,
                                     {**det, "note": "a type word with a different name stands before this one",
                                      "tier_before": tier})

    def response_head(self, low: str, pos: int) -> bool:
        """True if the type word at `pos` is in the head of a document of the executive: a response noun stands
        before it in the same sentence ("Beantwortung der Interpellation von ...", "Préavis ... sur le postulat"),
        the first 12 lines have a cue of a document of the executive, or the S1 rule role is response."""
        seg = low[max(0, pos - 160):pos]
        cut = max((x.end() for x in RX_SENT_BREAK.finditer(seg)), default=0)
        return bool(RX_RESP_PREFIX.match(seg[cut:])) or self.gov_head or self.doc.s1_role == "response"

    def group_bracket(self, b, orig: str, low: str, m: re.Match, pos: int, heading: bool) -> bool:
        """A type word, a group and a bracket with the names of the authors: "Postulat Fraktion SP/JUSO (Laura
        Binz/Marieke Kruit, SP): ...". The first name in the bracket is the value."""
        par = low.find("(", pos, pos + 70)
        if par < 0:
            return False
        between = low[pos:par]
        if re.search(r"[;:]|[.?] ", between) or not (RX_GROUP_WORD.search(between) or
                                                  RX_GROUP_WORD.search(low[max(0, m.start() - 20):m.start()])):
            return False
        close = low.find(")", par)
        if close < 0 or close - par > 160:
            return False
        name, _, executive = self.name_after(orig, low, par + 1, close)
        if name is None or executive or len(name.words) < 2 or name.caps or \
                not re.match(r" ?[,/)]", low[name.end:close + 1]):
            return False
        self.saw_name = True
        co = self.more_names(orig, low, name.end, close, loose=True, raw=b.text)
        self.add("type_group_bracket" if heading else "type_in_sentence", b.char_start, orig, name, m.group(0),
                 {"group": base.norm_text(orig[pos:par]).strip()}, [(x, orig, b.char_start) for x in co])
        return True

    def separator_name(self, b, orig: str, low: str, m: re.Match, pos: int, heading: bool) -> bool:
        """A head line with the parts between semicolons: "Interpellation 8145; Max Töpfer, SP; <title>". The
        name needs 2 words and a party mark or a semicolon directly after it."""
        sep = re.match(r"(?: (?:nr\.? ?)?[0-9][0-9a-z./-]{0,14})? ?; ?", low[pos:])
        if not sep:
            return False
        name, _, executive = self.name_after(orig, low, pos + sep.end())
        if name is None or executive or len(name.words) < 2 or name.caps:
            return False
        party = _party_after(orig, name.end)
        if not (re.match(r" ?;", low[name.end:]) or (party and party["start"] - name.end <= 3)):
            return False
        self.saw_name = True
        self.add("type_separator_name" if heading else "type_in_sentence", b.char_start, orig, name, m.group(0) + " ;")
        return True

    # ---- narrative tier
    def narrative(self) -> None:
        doc = self.doc
        for b in doc.blocks:
            if not b.lines or b.lines[0].number >= HEAD_LINES_NARRATIVE:
                continue
            orig = _flat(b.text)
            low = sfold(orig)
            if not RX_TYPE.search(low):
                continue
            for m in re.finditer(rf"(?<![{_UP}{_LO}-])[{_UP}]", orig):
                name = _name_at(orig, m.start())
                if name is None or len(name.words) < 2:
                    continue
                before = low[max(0, name.start - 60):name.start]
                t = re.search(r"(?<![a-z])" + TITLE + r"+$", before)
                marked = not name.caps and len(name.words) <= 3 and _party_after(orig, name.end) is not None
                if not name.first_known and not (t and not name.caps and len(name.words) <= 3) and not marked:
                    continue
                lead = before[:t.start()] if t else before
                if RX_EXEC_TITLE.search(before):
                    continue
                cue = None
                a = RX_SUBMIT_AFTER.match(low, name.end)
                if not a:                                      # the verb after the last name of a list of authors
                    more = self.more_names(orig, low, name.end, raw=b.text)
                    a = RX_SUBMIT_AFTER.match(low, more[-1].end) if more else None
                if a and a.group(0).strip().split(" ")[-1] in ("hat", "haben") and \
                        not RX_SUBMIT_LATER.match(low, a.end() - 1):
                    a = None                                   # "hat ... eingebracht": no submission verb
                if a:
                    cue = a.group(0).strip().split(" ")[-1]
                else:
                    s = RX_SUBMIT_BEFORE.search(lead.rstrip() + " ") or \
                        re.search(r"(?:reicht(?:e|en)|, par|, da) (?:am [0-9a-z. ]{6,22} )?$", lead)
                    if s:
                        cue = s.group(0).strip()
                    elif (t and RX_MEMBER_TITLE.search(before)) or \
                            re.search(r"(?<![a-z])(?:wurde|wurden)[^.;!?]{0,170} von (?:den |der |dem )?$",
                                      low[max(0, name.start - 200):(name.start - len(before) + len(lead))]):
                        later = RX_SUBMIT_LATER.match(low, name.end)
                        if later:
                            cue = "... " + later.group(0).strip().split(" ")[-1]
                if cue and RX_EXEC_AFTER.match(low, name.end):
                    continue
                if cue and RX_TYPE.search(low[max(0, name.start - 300):name.end + 300]):
                    self.saw_name = True
                    co = self.more_names(orig, low, name.end, raw=b.text)
                    self.add("narrative_submit", b.char_start, orig, name, cue, None, [(x, orig, b.char_start) for x in co])
                    return

    def prep_cosigners(self) -> None:
        """In the first 60 lines: a type word, an optional title in quotation marks, a preposition, a name and
        a co-signer cue with a count or a co-signer word ("Das nachfolgende Postulat von Timotheus Bruderer (SVP)
        und 16 Mitunterzeichnenden ..."). The type word can be in a sentence of running text."""
        for b in self.doc.blocks:
            if not b.lines or b.lines[0].number >= HEAD_LINES_COSIGNERS:
                continue
            orig = _flat(b.text)
            low = sfold(orig)
            for m in RX_TYPE.finditer(low):
                if re.search(r"(?<![a-z])(?:eine[rnms]?|una?|une?|d'une?|di una?) (?:[a-z]+ )?$", low[max(0, m.start() - 30):m.start()]):
                    continue                                   # "eine Interpellation von ...": a different affair
                pos = m.end()
                q = re.match(r' ?(?:nr\.? ?)?[0-9./-]{0,12} ?["][^"]{3,140}["]', low[pos:])
                if q:
                    pos += q.end()
                p = RX_PREP.match(low, pos)
                if not p:
                    continue
                name, has_title, executive = self.name_after(orig, low, p.end())
                if name is None or executive or len(name.words) < 2 or not (name.first_known or has_title):
                    continue
                co = self.more_names(orig, low, name.end, raw=b.text)
                end = co[-1].end if co else name.end
                tail = re.match(r"(?: ?\([^()]{1,30}\))?(?:,? [a-z/!.-]{2,12})?,? (?:und|sowie|mit|et|avec|e|con) ", low[end:])
                if tail and RX_COSIGNER_CUE.match(low, end + tail.end()) and \
                        re.match(r".{0,40}(?:unter-? ?zeichn|signataires|firmatar)", low[end + tail.end():]):
                    self.saw_name = True
                    self.add("type_prep_cosigners", b.char_start, orig, name, low[m.start():p.end()].strip(),
                             {"cue_after": low[end + tail.end():end + tail.end() + 30].strip()},
                             [(x, orig, b.char_start) for x in co])
                    return

    # ---- head sender and signature
    def signature_zone(self, end_limit: int | None = None) -> list[int]:
        """Line indexes of the signature zone: the lines after the last line of running text, in the last 25
        lines before the first response block (all lines if the document has no response block)."""
        doc = self.doc
        fr = doc.first_response_block()
        end = len(self.lines)
        if fr is not None:
            end = next((i for i, ln in enumerate(self.lines) if ln.block_index >= fr.index), len(self.lines))
        if end_limit is not None:
            end = min(end, end_limit)
        while end > 10 and doc.blocks[self.lines[end - 1].block_index].label == "footnote":
            end -= 1
        start = max(0, end - SIGNATURE_WINDOW)
        def running(i: int) -> bool:
            t = self.lines[i].text
            w = t.split()
            return len(t) >= 60 and len(w) >= 7 and sum(1 for x in w if x[:1].islower()) * 2 >= len(w)

        flags = [running(i) for i in range(start, end)]
        if not any(flags):               # a long list of signers: the zone starts after the text before the list
            start = max(0, end - SIGNATURE_WINDOW_LIST)
            flags = [running(i) for i in range(start, end)]
        last_run = last_single = -1
        for k, f in enumerate(flags):
            if f:
                last_single = k
                if k and flags[k - 1]:
                    last_run = k
        last_text = last_run if last_run >= 0 else last_single
        return [start + k for k in range(last_text + 1, len(flags)) if not flags[k]]

    def wrapped(self, i: int) -> bool:
        """True if line i goes on from a long line of the same block (running text that was wrapped)."""
        return i > 0 and self.lines[i - 1].block_index == self.lines[i].block_index and \
            len(self.lines[i - 1].text) >= 60 and not re.search(r"[.:!?]\s*$", self.lines[i - 1].text)

    def after_unread_line(self, i: int, zone: list[int]) -> bool:
        """True if the line before name line i is a short line of the signature zone that is no text end, no
        closing formula, no date, no cue and no group line: the form of a list of signatures in which the lines
        before were not read (handwriting, a first name that is not in the list)."""
        if i - 1 not in zone:
            return False
        prev, low = self.lines[i - 1].text.strip(), self.low_lines[i - 1].strip()
        if len(prev) >= 40 or not re.search(r"[a-z]{2}", low) or re.search(r"[.?!:;,]$|[0-9]", prev):
            return False
        return not (RX_CLOSING.match(low) or RX_FOR_GROUP.match(low) or RX_MEMBER.search(low) or
                    RX_LABEL.search(low) or RX_PARTY.search(prev))

    def cosigner_lines(self) -> set[int]:
        """The lines of a list of the other signers: the short lines after a line that starts with the label of
        the co-signers ("Autres signataires", "Mitunterzeichnende:", "Cofirmatari"). The list ends at a line of
        running text, at a closing formula, at a label of the first author or after 40 lines."""
        out: set[int] = set()
        left = 0
        for i, low in enumerate(self.low_lines):
            t = self.lines[i].text
            if RX_COSIGNER_LABEL.match(low):
                left = 40
                out.add(i)
                continue
            if left:
                w = t.split()
                running = len(t) >= 60 and len(w) >= 7 and sum(1 for x in w if x[:1].islower()) * 2 >= len(w)
                lab = RX_LABEL.search(low)
                first_label = lab and not re.search(r"(?:mit|co|weitere|autres|altri|zweit)[- ]?$", low[:lab.start()])
                if running or RX_CLOSING.match(low) or first_label:
                    left = 0
                    continue
                out.add(i)
                left -= 1
        return out

    def signature_names(self, zone: list[int], head_limit: int) -> list:
        sig: list[tuple[int, _Name, str, int, str | None]] = []
        cosigners = self.cosigner_lines()
        for i in zone:
            if i < head_limit or self.wrapped(i):
                continue
            if i in cosigners:
                if self.name_line(i):
                    self.saw_name = True
                continue                                       # a name of the list of the other signers
            got = self.name_line(i) or self.marked_name_line(i)
            if not got and i and RX_CLOSING.match(self.low_lines[i - 1]):
                got = self.name_line(i, need_first=False)      # directly after a closing formula
            if not got:
                continue
            self.saw_name = True
            if self.official_near(i):
                continue
            sig.append((i, *got, self.member_near(i) or self.title_mark(i, got[0])))
        return sig

    def addressee(self) -> None:
        """The addressee block of an answer: a line with a salutation word only, a name line, and a line with a
        member word only in the 4 lines after it ("Signor" / "Matteo Pronzini" / "Deputato al Gran Consiglio")."""
        n = len(self.lines)
        for i in range(min(HEAD_LINES_ADDRESSEE, n - 2)):
            salute = bool(RX_SALUTE_LINE.match(self.low_lines[i]))
            if not salute and not RX_MEMBER_LINE.match(self.low_lines[i]):
                continue
            k = i + 1 if salute else i
            member = None
            while k < min(i + 4, n) and (RX_SALUTE_LINE.match(self.low_lines[k]) or
                                         RX_MEMBER_LINE.match(self.low_lines[k])):
                if RX_MEMBER_LINE.match(self.low_lines[k]):
                    member = self.low_lines[k].strip()
                k += 1
            if k >= n:
                continue
            got = self.name_line(k) or self.name_line(k, need_first=False)
            if not got:
                continue
            self.saw_name = True
            member = member or next((self.low_lines[j].strip() for j in range(k + 1, min(k + 5, n))
                                     if RX_MEMBER_LINE.match(self.low_lines[j])), None)
            name, orig, start = got
            co = [(x, orig, start) for x in self.more_names(orig, self.low_lines[k], name.end)]
            for j in range(k + 1, min(k + 7, n)):              # the further names of the addressee block
                nxt = self.name_line(j)
                if not nxt:
                    break
                co.append((nxt[0], nxt[1], nxt[2]))
                co += [(x, nxt[1], nxt[2]) for x in self.more_names(nxt[1], self.low_lines[j], nxt[0].end)]
            if member and salute:
                self.add("addressee_member", start, orig, name, self.low_lines[i].strip() + " / " + member, None, co)
                return
            # an answer by letter: the addressee, and "your <type word>" in the 25 lines after the name or in the
            # 25 lines before the block (the reading order of a letter head is not always the printed order)
            near = [j for j in range(k + 1, min(k + 26, n))] + [j for j in range(max(0, i - 25), i)]
            yours = next((RX_YOUR_AFFAIR.search(self.low_lines[j]) for j in near
                          if RX_YOUR_AFFAIR.search(self.low_lines[j])), None)
            if yours and not self.official_near(k, 1, 2):
                self.add("addressee_reply", start, orig, name,
                         self.low_lines[i].strip() + " / ... " + yours.group(0), None, co)
                return

    def head_and_signature(self) -> None:
        if self.gov_head:
            return
        other_role = not self.signatures
        head_limit = min(HEAD_LINES_SENDER, len(self.lines) // 2)   # a short document: the first half is the head
        zone = self.signature_zone()
        sig = self.signature_names(zone, head_limit)
        sig_zone = zone
        if not sig or not sig[0][4]:     # no marked name at the end: the lines before an annex heading
            annex = next((i for i in range(max(10, head_limit), len(self.lines))
                          if RX_ANNEX.match(self.low_lines[i])), None)
            if annex is not None:
                before_annex = self.signature_names(self.signature_zone(annex), head_limit)
                if before_annex and (not sig or before_annex[0][4]):
                    sig, sig_zone = before_annex, self.signature_zone(annex)
        if not self.type_in_head:
            # no type word in the head: only the S1 rule role says that the document is a proposal
            if sig and self.doc.s1_role in S1_ROLES_IN_SCOPE and not other_role:
                self.add("signature_untyped", sig[0][3], sig[0][2], sig[0][1],
                         sig[0][4] or "first name line of the signature zone", {"note": "no type word in the head"})
            return
        head: list[tuple[int, _Name, str, int, str | None]] = []
        for i in range(head_limit):
            got = None if self.wrapped(i) else (self.name_line(i) or self.marked_name_line(i))
            if not got:
                continue
            self.saw_name = True
            same_block_prev = [k for k in range(max(0, i - 2), i)
                               if self.lines[k].block_index == self.lines[i].block_index]
            prev = same_block_prev or ([i - 1] if i else [])
            if any(RX_ADDRESSEE.match(self.low_lines[k]) for k in prev) or self.official_near(i, 2, 1):
                continue
            head.append((i, *got, self.member_near(i, 1, 3) or self.title_mark(i, got[0])))

        def fam(n: _Name) -> str:
            return _normalise(n.split()[1])

        sig_fams = {fam(s[1]): s for s in reversed(sig)}
        if other_role:
            # a different S1 rule role: only a short name line (no line of the minutes with a speaker)
            head = [h for h in head if self.doc.s1_role != "minutes" and len(h[2]) <= 60]
        for i, name, orig, start, mark in head:
            s = sig_fams.get(fam(name))
            if s is not None and s[0] != i:
                self.add("head_sender_other_role" if other_role else "sender_signature", start, orig, name,
                         "name line in the head and in the signature zone",
                         {"signature_span": [s[3] + s[1].start, s[3] + s[1].end], "member_mark": mark or s[4]})
                break
        for i, name, orig, start, mark in head:
            if mark:
                self.add("head_sender_other_role" if other_role else "head_sender_marked", start, orig, name, mark)
                break
        if other_role:
            return
        marked = next((s for s in sig if s[4]), None)
        if sig and sig[0][4]:
            unread = self.after_unread_line(sig[0][0], sig_zone)
            self.add("signature_list_first" if unread else "signature_marked", sig[0][3], sig[0][2], sig[0][1],
                     sig[0][4], {"name_lines_in_zone": len(sig)})
        elif sig:
            in_list = len(sig) >= SIGNATURE_LIST_MIN or self.after_unread_line(sig[0][0], sig_zone)
            tier = "signature_list_first" if in_list else "signature_plain"
            self.add(tier, sig[0][3], sig[0][2], sig[0][1], "first name line of the signature zone",
                     {"name_lines_in_zone": len(sig)})
            if marked:
                self.add("signature_marked_later", marked[3], marked[2], marked[1], marked[4],
                         {"note": "not the first name line of the signature zone"})

    def run(self) -> None:
        self.labels()
        self.type_words()
        self.narrative()
        self.prep_cosigners()
        self.addressee()
        self.head_and_signature()


def _co_norm(name: _Name) -> str:
    """The normalised value of a further author (the same form as the value of the field)."""
    words = [t for t, k in name.tokens if k != "initial"]
    uncertain = len(name.words) >= 2 and not name.first_known and not first_last_known(name)
    return _normalise(words if uncertain else name.split()[1])


def _normalise(family: list[str]) -> str:
    """The family name for the comparison: lower case, no accents, each other character as a space."""
    return re.sub(r"[^a-z0-9]+", " ", base.fold(" ".join(family))).strip()


def _candidate(doc: Doc, item, others=()) -> ValueCandidate | None:
    tier, start, end, name, det = item
    # with an uncertain split the normalised value keeps all words of the name
    all_words = det.get("split_uncertain") or det.get("family_only_value")
    norm = _normalise([t for t, k in name.tokens if k != "initial"] if all_words else name.split()[1])
    if not norm:
        return None
    return doc.candidate(FIELD, start, end, norm, tier, others, det)


@register(FIELD)
def read_sponsor(doc: Doc) -> ValueCandidate | NotFound:
    """The first author as the document prints it, or `not found in the PDF`."""
    in_scope = doc.s1_role is None or doc.s1_role in S1_ROLES_IN_SCOPE
    r = _Reader(doc, signatures=in_scope)        # signatures=False: only the tier head_sender_other_role
    r.run()
    order = {t: i for i, t in enumerate(TIERS)}
    items = sorted(r.found, key=lambda x: (order[x[0]], x[1]))
    seen, uniq = set(), []
    for it in items:
        key = (it[1], it[2])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    cands = [c for c in (_candidate(doc, it) for it in uniq) if c is not None]
    if not cands:
        if not in_scope:
            return doc.not_found(FIELD, "not_in_document_type",
                                 f"S1 rule role {doc.s1_role}: no name after a label, a type word or a submission "
                                 "verb and no marked name line in the head; the signature tiers do not read this "
                                 "document type")
        if r.saw_name:
            return doc.not_found(FIELD, "no_cue", "a name is printed, but no cue or position rule selects it")
        return doc.not_found(FIELD, "no_pattern", "no name line and no name after a cue")
    best = cands[0]
    others, spans = [], {(best.char_start, best.char_end)}
    for c in (best.detail or {}).get("co_authors", ()):          # the further authors that the same cue prints
        if (c["char_start"], c["char_end"]) not in spans and c["normalised"]:
            spans.add((c["char_start"], c["char_end"]))
            others.append(doc.candidate(FIELD, c["char_start"], c["char_end"], c["normalised"], CO_AUTHOR_TIER, (),
                                        {"note": "a further author after the first author", "cue": best.detail.get("cue")}))
    others += [c for c in cands[1:6] if (c.char_start, c.char_end) not in spans]
    return doc.candidate(FIELD, best.char_start, best.char_end, best.normalised, best.tier, others, best.detail)


# ------------------------------------------------------------------ commands

def coverage() -> dict:
    """Counts only: how many open development documents get a value by tier, and how many get `not found`. This
    command compares no value with a reference. The result goes to daten/gj_values/coverage_sponsor.json."""
    ids = base.dev_ids("open")
    guard = base.guard_check(ids)
    by_tier, by_reason, by_role, by_lang = Counter(), Counter(), Counter(), Counter()
    parliaments_with_value: dict[str, set] = {}
    errors = 0
    for d in ids:
        doc = base.load_doc(d)
        res = base.read_field(doc, FIELD, strict=True)
        role = doc.s1_role or "none"
        if res.found:
            by_tier[res.tier] += 1
            by_role[f"{role}|value"] += 1
            by_lang[f"{doc.language}|value"] += 1
            parliaments_with_value.setdefault(res.tier, set()).add(doc.parliament)
        else:
            by_reason[res.reason] += 1
            by_role[f"{role}|not_found"] += 1
            by_lang[f"{doc.language}|not_found"] += 1
            errors += res.reason == "reader_error"
    out = {
        "what": "coverage of the sponsor rule by tier over the open development documents; counts only, no "
                "comparison with a reference",
        "version": VERSION, "base_version": base.VERSION, "documents": len(ids),
        "guard": guard,
        "with_value": sum(by_tier.values()),
        "not_found": sum(by_reason.values()),
        "by_tier": {t: by_tier.get(t, 0) for t in TIERS},
        "parliaments_by_tier": {t: len(parliaments_with_value.get(t, ())) for t in TIERS},
        "not_found_by_reason": dict(sorted(by_reason.items())),
        "by_s1_role": dict(sorted(by_role.items())),
        "by_language": dict(sorted(by_lang.items())),
    }
    COVERAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="value rule for the first author (plan task T8)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("doc_id", nargs="+")
    sub.add_parser("coverage")
    a = ap.parse_args()
    if a.cmd == "coverage":
        print(json.dumps(coverage(), ensure_ascii=False, indent=1))
        return 0
    for d in a.doc_id:
        res = base.read_field(base.load_doc(d), FIELD)
        print(json.dumps({"doc_id": d, **res.to_json()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    # a run as a script: the registry of the base file must hold this reader under the module name
    sys.exit(main())

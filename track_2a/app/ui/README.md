# The browser app of the ParlPDFeCH package

Status of all results of the package: EXCEPTION, NOT RELEASED. No human checked the results.

This folder holds the page that the server shows below `/app/`. The page is plain HTML, CSS and one script. It has no framework, no library and no build step. It loads no file from another host. It sets no cookie and stores nothing in the browser.

The reference for all interfaces is `../CONTRACT.md` (chapters 5, 6, 7, 14 and 15).

State of now (14.10.2026, after the step "start page and result view"): `strings.json` has 795 keys, `node ui/tools/check_ui.mjs` gives 0 errors; the chapter "Changes of 14.10.2026" at the end describes the new start page, the page "About" and the result view. State of 13.10.2026, after the step "one site": `strings.json` has 463 keys (20 of them with the ending `.hosted`), `rdfpanel.strings.json` has 83 keys, `node ui/tools/check_ui.mjs` gives 0 errors. The chapters "Changes of ..." below are the history of earlier steps; their key counts (424 and 81, 430 and 83) are the counts of those steps. The last chapter describes the page of a site that takes no file, of a hosted site and of a server with a static site.

## Files

| File | Content |
|---|---|
| `index.html` | the one page; all screens are sections of it; no inline script and no inline style |
| `app.css` | the style sheet; colours are CSS variables; a light and a dark scheme |
| `app.js` | the script (an ES module) |
| `strings.json` | all texts of the page, form `{key: {en, de}}`. A key with the ending `.hosted` is the text of its base key on a hosted site. |
| `run_numbers.json` | the numbers of the one fixed run of 13.10.2026 on the start page and in the result view. They are display values of `public/track_2a/numbers.json` of the project, with their ids. `tools/make_run_numbers.py` writes the file; `--check` compares it with the source. |
| `favicon.svg` | the icon |
| `fixtures/` | byte-equal copies of `../contract/examples/*` and of `../contract/errors.json`, for the fixture mode. The server of the package does not serve this folder. |
| `tools/check_ui.mjs` | static checks (Node.js, no library). The server of the package does not serve this folder and not this README. |

The files `rdfpanel.js`, `rdfpanel.css`, `rdfpanel.strings.json` and the folder `pkg/` belong to the WebAssembly part. The folder `pkg/` is generated. The second correction round changed `rdfpanel.js`, `rdfpanel.css` and `rdfpanel.strings.json` (chapter below).

## Screens and routes

| Route | Screen |
|---|---|
| `#/` | S0 start (14.10.2026): one sentence, the picture of the flow, the 3 samples as cards, the box "How often correct?" and the button for an own PDF. The box has 4 fields of `run_numbers.json`. Each topic has a link "more". A card with a ready result opens `#/view/<id>`. Else the card starts the conversion of its first mode, and the page opens the result view at the end. |
| `#/about`, `#/about/<part>` | About, with 4 parts: `method`, `numbers` (the 7 fields of the fixed run), `limits` and `technical`. The part `technical` has the technical view, the modes, the mode line of `GET /api/health`, the notices and the list of the words. A route with a part sets the focus to the heading of that part. |
| `#/view/<record_id>` | The result view: the PDF (page images with boxes), the values with their probability, the RDF (2 Turtle files). A finished job opens this route. |
| `#/samples` | S1 samples from `GET /api/samples` |
| `#/upload` | S2 upload: a file input, a drop zone, the limits from `GET /api/health`, the optional document number |
| `#/job/<job_id>` | S3 stages from the event stream; if the stream fails, the page asks `GET /api/jobs/<id>` each 2 s |
| `#/record/<record_id>` | S4 result, now called "the technical view"; a link at its top goes back to `#/view/<record_id>` |
| `#/record/<record_id>/label/<label_id>` | S4 with one label selected |

The table describes a local run. Three values of `GET /api/health` change the entries and the texts (last chapter): `modes.read_only`, `hosted` and `site`. The page asks `/api/health` before it shows its first text.

An unknown route shows S0. A case (an error object of the API) replaces the screen. It shows the title, the text, the action and one button for each exit.

The language is the query `?lang=en` or `?lang=de`. With no query the page takes `de` if the language of the browser starts with `de`, else `en`. The language switch changes the query with no new load of the page.

## Rules of the display

- A probability shows as the stored decimal. The page does not round it and adds no percent sign. A share of the fixed run (not a probability) shows as a percent of the documents, rounded to a whole number.
- The words "certain" and "unsure" have a word and a shape (a full square, a dashed square). No red and no green carry a meaning. The technical view has no bar for a probability. The result view (14.10.2026) shows a bar next to the stored decimal, and the word certain (a full badge) or unsure (a dashed badge).
- In the result view each field has one colour (classes `c0` to `c6`, by the sequence affair type, title, affair number, submission date, first author, response date, responder). The colour says which value a row, a box and a triple belong to. It says nothing about the value.
- A label with no probability shows its source and no number.
- The sequence of the cards is the sequence of `labels[]` of the view. The filters hide cards; they do not sort.
- The technical view draws the page from the line frames of the view. It is not an image of the PDF. The result view shows the image of the page (`pages[].image` of the view) if the record has one; else it draws the lines and says "drawn from the text layer".
- The notices of the view show as plain sentences on S4. The first two show on S0.
- The page does not show the internal status (CONTRACT.md chapter 7.5). The field `run.status` of the view is not printed. No text of `strings.json`, `index.html` or `app.js` holds the status words.
- "Development document" comes from the data (`samples[].in_sample`, the notices of the view, `labels[].in_sample`). The page has no list of document numbers.

## Keyboard

- The first control of the page is "Skip to the content".
- Each screen sets the focus to its heading.
- The drawn page has one tab stop. The arrow keys, Home and End move between the lines. Enter or Space selects the label of the line.
- "Show on the page" on a card marks the lines of the label; a second press removes the marks. "Go to the card of the selected label" above the drawn page sets the focus to the card.
- S4 has a list of its parts below the facts of the document. A button of the list sets the focus to the heading of the part.
- A link to one label (`#/record/<id>/label/<label>`) sets the focus to the heading of the card.
- The outline of a heading that the script gave the focus shows only after a press of Tab or of an arrow key.
- The part "The lines of the page as a text list" holds each line as a button. It is the path with no drawn page.
- Changes of a stage, of the filters and of the marks go to a region with `aria-live`. A case goes to a region with the role `alert`.

## Fixture mode

With the query `fixture=1` the page calls no API. It reads the files of `fixtures/`. The server of the package gives the page files only (`/app/fixtures/` answers 404), so the fixture mode needs a plain file server for this folder (command below). It is a mode for the development of the page.

- `health.json`, `samples.json`;
- `events_sample.jsonl` for a sample (one line each 450 ms), then `view_26171.json`. The view of document 26171 shows for each record id;
- `events_refused.jsonl` for an own PDF, then the case `not_in_package` with the texts of `errors.json`.

The download addresses and the RDF panel need the server. They do not work in the fixture mode.

Run, from this folder:

```
python3 -m http.server 8896 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8896/?fixture=1&lang=en`.

## Checks

Run, from the folder `package/`:

```
node --check ui/app.js
node ui/tools/check_ui.mjs
```

`check_ui.mjs` checks these points:

1. `strings.json` parses; each key has a text in `en` and in `de`; the placeholders are equal in the two languages.
2. Each key of `../contract/strings.contract.json` is in `strings.json` with the same texts.
3. Each key that `app.js` or `index.html` uses is in `strings.json`. Each key of `strings.json` is used.
4. Each id that `app.js` uses is in `index.html`. No id is there twice. Each reference between elements has a target.
5. No text matches a pattern of the stop list of the preview site (`web/content/stop_list.json`), and no text uses the word "live".
6. The page has no inline script, no inline style, no address of another host, no storage call and no HTML string.
7. The fixtures are byte-equal to the contract files.
8. No German text holds the letter sharp s. No file holds a home path.

Results of the last run (measured):

- `node --check ui/app.js`: passed (Node.js 24.19.0).
- `node ui/tools/check_ui.mjs`: 0 errors; 424 keys of the page and 81 keys of the panel (13.10.2026, document and gate step, after the second correction round).
- Notes of check 5: none. The three contract texts that matched the stop list were changed in the examination step (`notice.no_human_check`, `s2.limits`).
- Notes of check 3: four contract keys (`rdf.intro`, `rdf.counts.agree`, `rdf.counts.differ`, `rdf.query.run`) are for the RDF panel module.

The checks in a browser below are the checks of the first build of the page (fixture mode). The checks of the examination step (real server) are in `../STATE.md` chapter 3.

Checks in a browser (Chromium engine, fixture mode, served by `python3 -m http.server` on port 8896):

- S0, S1, S2, S3 and S4 loaded in English and in German. The console showed no error of the script.
- S1 to S3 to S4 for the sample 26171: 6 stages, then the result with 33 cards, 36 lines, 5 notices, the count line and the checks line.
- S4: "Show on the page" marked 10 lines for the block B4. A click on a line selected the card of its block. Arrow key and Enter on a line worked. The filters gave 6 cards for "unsure" and 10 cards for the source "OpenParlData export". The language switch kept the route. The delete control went to S0.
- S2: no file, a document number with a letter, and a PDF that is not a sample gave their messages; the case `not_in_package` showed two exits.
- S3: "Stop" gave the case "The conversion was stopped" with two exits.
- With no API (no fixture query), the page showed a case with the exits "Try again" and "Back to the start".
- Width 320 px (in a frame): S0, S1, S2, S3, S4 (all details open) and the case screen had no horizontal scroll.
- The RDF panel module loaded. Its request for the TriG file got 404 from the static server. The section showed the text `rdf.absent`, and all other functions worked.
- Contrast of the colour variables (calculated): text on the two backgrounds is 5.57 or more in the light scheme and 7.83 or more in the dark scheme.

Not checked:

- The page against the real server: the event stream (`EventSource`), the fallback poll, the downloads, `DELETE` of a record and of a job, each error code of the API.
- A screen reader, a zoom of 200 % in a browser window, the forced-colours mode, Firefox and Safari.
- A drop of a file with the mouse (the check set the file by script).
- A document with more than one page, a label with `chosen_is_top: false`, a calibration with `basis`, a record with `valid: false`. The example view has none of them.

## Differences from the contract

- `index.html` has no `script` element for `rdfpanel.js`. `app.js` loads the module with `import('./rdfpanel.js')` when S4 opens. A missing module or a failed mount gives the text `rdf.absent`.
- The card shows the key `s4.card.label` ("Label") before the selected answer. The head line of S4 takes its key from `run.origin` and `run.apertus` (`stored` gives `auto`, `none` gives `rules`).
- The page has three cases of its own for answers that are not an error object: no answer of the server, an answer of an unknown form, a stopped conversion. Their texts are in `strings.json` (`case.*`).
- An upload always sends `mode=auto`.

## Changes of the examination step (13.10.2026)

- The mode sentences of S0 and S2 follow `GET /api/health` (keys `mode.upload.*`, `mode.ocr.*`, `mode.samples.stored`). The keys `s0.mode.slim`, `s0.mode.full`, `s2.mode.upload` and `about.ocr` are gone.
- S1 and S4 show the name of the body with its key in parentheses (`parliament_name` and `parliament` of the data), the kind of affair from one map `affair_type.<value>` (the 9 values of the eCH-0295 enumeration; another value shows as it is) and the name of the language (`lang.name.<code>`).
- S1 and S4 show the counts of the two results of a sample when the two records are on the computer (`cmp.line`): certain and unsure labels of the two views. The page reads the two views; it makes no other statement.
- A card whose selected answer has not the highest number says who selected the answer (`unc.other_higher`, `.rule`, `.readout`). The document label of the mode with stored states says that a code rule selected the answer and that the number is a read-out (`source.rule.readout_number`; the view gives the calibration method `verifier_platt`).
- The basis line shows for each rule label whose calibration record holds counts (`unc.basis` for blocks, `unc.basis.documents` for documents).
- The card of the label "response of the executive" shows the final check from the count `r2_agrees_with_block_path` of the record and does not print the fixed note of the converter.
- The page caption says how many line frames are not frames of the text layer, and if a text recognition gave the text before (a sample) or in this conversion.
- S2 compares the size of the file with the limit and asks `GET /api/health` for a running job before it sends the file.

## Changes of the second correction round (13.10.2026)

The input was the full list of the examiner of the page (30 findings) and 5 findings of the later check.

Texts for a reader with no background:

- The fourth step of S3 has a name that is true for what runs: "Read the stored Apertus results" for a sample (`s3.stage.model.sample`), "Language model" with the state "skipped: this package runs no language model" for an own PDF (`s3.stage.model.own`, `s3.skip.no_model`). The contract keys `s3.stage.apertus` and `s3.stage.apertus.stored` are not used.
- The list "Words used on these pages" (keys `words.*`, constant `WORDS` of `app.js`) is on S0 and, closed, on S1 and S4.
- The mode names are `mode.name.*` and `mode.inline.*` ("stored Apertus results"). The head line of S4 is `s4.headline.<origin>` with the mode name. The source lines of a read-out are `source.readout.*`; the label "response of the executive" of a sample has the line `source.stored_value`.
- A card of a code rule whose selected answer has not the highest number says why the answer stays (`unc.why.rule`). Each rule card with counts says what the number is (`unc.rule.basis.blocks`, `unc.basis.documents`); for a PDF with no export record the document label adds `unc.basis.no_export`. A card of a mode with no limit for the word "certain" says so (`unc.card.no_limit`).
- A card of a value has the caption "Value", a wording card shows the start of the text (the stored value is a hash), and the name of a value card holds the part of the record and a plain name of the property (`part.*`, `slot.*`). The stored names are in the technical details.
- The technical details of a card and of the run show no working name of the project: no step name, no calibration id, no name of the converter variant. The method of a number shows in plain words (`method.*`). A note shows only as the text of its code (`note.*`, view keys `note_code` and `note_params`); a view with no key `note_code` shows no note.
- The notice about the text recognition gives the counts of the pages by text source from `pages[].text_source` (`ocr.apple.pages`).
- The values of the eCH-0295 record have a plain name and, below, the name in eCH-0295. Marks for headings and paragraphs are removed from a shown text (`s4.head.markup`). The checks have plain names (`check.*`) with the id in parentheses.

Numbers: one function (`count` in `app.js`, used by `fill` and `dlRow`) writes each count with the thousands mark of the language (`en`, `de-CH`); the RDF panel uses the same form. A probability stays the stored decimal. The function `tn` selects the key with the ending `.one` for the count 1.

Keyboard and accessibility: chapter "Keyboard" above, and: the file control of the browser is out of sight and its label is the button; a line with no text has a name and a dashed frame; the help for the arrow keys is in sight; the texts about the selected line stay in sight in the pane of the page; the summary of each card has the name of its card; a filter pair with no match has its own text; the exit "Choose another PDF" removes the refused file; a record address with a wrong form shows a case of the page (`case.no_record.*`); the pressed state of a button has a check sign and a thick lower edge; values in the language of the document have a `lang` attribute; on a narrow screen the text list of the lines is open.

RDF panel: the tables keep a readable width and their box scrolls sideways (a named region; a tab stop only while it scrolls); the borders of the controls have 65 % of the text colour; the sources show in the words of the page with the stored name in parentheses; the hint names the three limits; the count line has a form for 1 row; the example of the head values is not shown for a record with no export record (mount option `hasExport`); the example "labels" sorts the labels with a page first (the script changes the `ORDER BY` line of that example; the source of the example is in the WebAssembly module); a language switch does not read the TriG file again.

`check_ui.mjs` has check 9 (the strings of the RDF panel) and knows `tn` and the list of words.

Results of this round (measured, 13.10.2026; one browser engine, Chromium, with the real server of the package on `127.0.0.1:8896`, profile `native`):

- `node ui/tools/check_ui.mjs`: 0 errors; 424 keys of the page, 81 keys of the panel; no stop list match in the 1,010 texts of the two strings files. Notes: the contract keys `s1.card.stored`, `s1.card.in_sample`, `s1.mode.auto`, `s1.mode.rules` and `unc.basis` are not used by `app.js`. The contract keys `s3.stage.apertus`, `s3.stage.apertus.stored`, `s3.skip.not_in_package`, `s4.head.stored.auto`, `s4.head.stored.rules`, `s4.head.new.rules`, `source.apertus_readout.apertus_head` and `source.apertus_readout.code_step` are not used either; the tool counts them as used, because their prefix is in `app.js`.
- S0, S1, S2 and S4 (`s-26171`, `s-26171-rules`, `s-879163`, one record of a synthetic PDF) in English and in German: each screen showed, no horizontal scroll at 1280 px, no working name of the project and no empty placeholder in the text (search by pattern, all details open), the RDF panel ready. S3: a sample in the two modes (English) and a synthetic PDF (German) from the start to the result.
- Widths 320, 375, 480, 768, 1024 and 1280 px: S4 of the record of the synthetic PDF (light scheme) and of `s-714840` (dark scheme) had no horizontal scroll and no element wider than the window; the numbers of an answer list stood in one column; the comparison table of the panel had a name column of 120 px or more (highest row 224 px at 320 px). S0, S1, S2 and the case screen: 320 and 768 px, light scheme.
- Keyboard (real key presses): Tab through the list of the parts, the drawn page and the filters; arrow keys and Enter on the page; Space two times on "Show on the page"; Tab after a link to one label; Tab to the file control.
- After the last browser check one text changed (`mode.samples.stored`); it was not seen in a browser again.

Not run in this round: the fixture mode, the stop button, a drop of a file with the mouse, a screen reader, Firefox, Safari, the forced-colours mode, a zoom of 200 %, a record with more than one page, the profile `slim` beyond the mode lines of S0 and S2. The lines "Results of the last run" above are the lines of the earlier step.

## Changes after the second skeptic check (13.10.2026)

The list is in `../EXAMINATION.md` chapter 9 and in `../CONTRACT.md` chapter 13. The values above this chapter are the values of the earlier steps.

- Texts: 13 contract texts and 18 other texts of the page have new wording; 6 new keys (`fmt.size.*`, `s3.stage.read_pdf.sample`, `s3.stage.lines.sample`, `s4.card.nochars`). The headline says "a PDF of a Swiss parliament or government".
- `app.js`: for a sample the first two steps have their own names (the package reads stored pages and lines, no PDF); the size of a selected file shows in MB, KB or bytes; a block with an empty character range shows "no characters"; the one tab stop of the drawn page starts on the first line with text.
- Panel: the stored names of the tables "Labels by source" and "Comparison with manifest.json" are in `title` attributes; the row for labels with a statement `plb:inSample` shows "not known" when no label has the statement.
- `node ui/tools/check_ui.mjs`: 0 errors; 430 keys of the page, 83 keys of the panel; no stop list match. The tool has a new check 10 (two rows for the panel).
- Seen in one browser engine (Chromium), one width: S0, S1, S2, S3 of a sample, S4 of 3 sample records and of one upload record, in English or German (`../STATE.md` chapter 10.2 has the list). Not run: the widths 320 and 800 px, a key press on the drawn page, a screen reader, another engine, the fixture mode.

## The page of a hosted site, of a site that takes no file, and the link to the static site (13.10.2026)

The rule is in `../CONTRACT.md` chapters 14 and 15. The page reads four values of `GET /api/health`.

| Value | What the page does |
|---|---|
| `modes.read_only` true (the server takes no file and refuses each DELETE) | S0: the line `s0.line.read_only`; the second way has the text `s0.button.local` ("Run it on your computer") and the note `s0.local.note`; the mode line starts with `mode.read_only`. Navigation: the entry `nav.local` ("On your computer") in place of `nav.upload`. S2 (`#/upload`): the headline `s2.title.read_only`, the text `s2.read_only` (how to convert an own PDF with the package on the own computer), a button to the samples, and the link `nav.site` if the server has a static site; no form. S3: no stop button. S4: no part "Delete the result". S1: the link to a ready record has the text `s1.open.site`. |
| `modes.sample_runs` false | S1: the lead `s1.lead.ready`; a mode whose record is ready has one link and no convert button. A refusal of the server has the code `sample_runs_off`. |
| `hosted` true (the operator set `PARLPDFECH_HOSTED=1`) | The function `t` of `app.js` takes the key `<key>.hosted` in place of `<key>` if the strings file has it. 20 keys have such a form: each text that says "on this computer", "Your PDF stays", "no request to another computer" or "the server of this package on this computer". For the server codes `forbidden` and `internal` the case screen shows the page texts `err.hosted.<code>.text` and `err.hosted.<code>.action` if they exist. |
| `site` true (the server gives a static site below `/`) | The navigation has the entry `nav.site` ("About this project" / «Über das Projekt») with the address `/` (German page: `/de/`). |

Texts that name this computer and have no form for a hosted site: none that the page shows. The contract key `s4.head.new.rules` has such a text and is not used by `app.js`. The texts of `rdfpanel.strings.json` say "in this browser"; this is true on each site.

`tools/check_ui.mjs` checks for each key with the ending `.hosted`: the base key exists and is used, the placeholders are the same, the text does not name this computer or `localhost`, and the key is not a contract key.

Seen in one browser engine (Chromium, the built-in browser pane of the desktop app, one width), with the real server on `127.0.0.1:8897`, profile `native` (`../STATE.md` chapter 10.5 has the list): the link with a site and no link with no site; on an instance with `PARLPDFECH_READONLY=1`, `PARLPDFECH_SAMPLE_RUNS=off`, `PARLPDFECH_HOSTED=1` and a site: S0, S1, S2 and S4 of 2 records in English and German. Not run: the widths 320 and 800 px, the keyboard path of the new entries, a screen reader, another engine, the fixture mode, a hosted instance with no read-only setting (the texts `s0.line.hosted`, `s0.upload.note.hosted`, `s2.sending.hosted`, `mode.upload.yes.hosted`, `s4.delete.hosted`, `s4.delete.note.hosted`, `s4.headline.new.hosted` and `s3.time.hosted` were read in the strings file and not seen in a browser), the case screens with the texts `err.hosted.*` and `case.network.*.hosted`.

## Values that are read from the PDF (13.10.2026)

The contract is `CONTRACT.md` chapter 16.4. `STATE.md` chapter 11 has what was seen in a browser.

1. `app.js` has the new functions `renderEch`, `echRow`, `fromPdf` and `valueShown`. The constant `ECH_GROUPS` fixes the rows of the 3 tables.
2. The part "The eCH-0295 record" shows only if the view key `head_values.source` is `pdf`.
3. Replaced on 13.10.2026 (last chapter): each value has a stored decimal; the text `values.not_measured` does not exist any more.
4. The value of the export shows in the column "OpenParlData" only.
5. "Show on the page" selects the label of the value. `setMarks` draws a frame around the span. The place of the frame is an estimate from the count of the letters of the line.
6. A label of the kind `pdf_value` also has a card in "The text parts".
7. The tables are stacked below a width of 47.5 rem. Each cell then has the name of its column.
8. `strings.json` has 604 keys. `STATE.md` chapter 11.4 lists the texts that changed.
9. The RDF panel gets `hasExport` false for a record of the new form: it hides the example query for the head values.
10. Not run: the keyboard path through the tables, a screen reader, Firefox, Safari, the forced-colours mode, the print view, the fixture mode.

## Corrections after the skeptic check of the values (13.10.2026)

Contract: `CONTRACT.md` chapter 17. Findings: `EXAMINATION.md` chapter 12.

1. A value row shows the stored word (certain or unsure), the stored decimal and the line "equal in k of n development documents". The paragraph above the tables says what the number is.
2. A value whose form in the record differs from the printed wording shows the two strings ("printed: ...; in the record: ...") and one sentence with the rule (`values.form.*`). A list value shows the stored value and the word of the list in parentheses.
3. A weak candidate (`values[].written` false) shows the state "Not found in the PDF", the reason, the candidate with the words "not in the record", its number and the line "below 0.5: not written to the record". Its label card has the name "Weak candidate (not in the record)".
4. REPLACED (next chapter). Earlier text: A sample of the open part shows one more line: its number leaves out the group of parliaments of the document, and the line gives the number from all development documents.
5. The comparison with OpenParlData says "equal by the comparison rule" if the two strings differ, shows the string of OpenParlData and names the rule of the field (`export_rule.*`).
6. The state `not_in_this_document_type` has the words "Not searched in this kind of document". The reason names the kind of the document that the rules chose, or, for the first author, the rule of the submitted text.
7. A gap text says that the rules found no value that they write to the record. No text says that the PDF does not print a value.
8. The row of the text blocks has the button "Go to the text blocks" and the sentence "Each text block has its own label below."
9. An address that the converter made has the state word "Made by the converter" in the list of the other entries. This list was not opened in the browser check.
10. The RDF panel shows the example query for the head values for each record with values from the PDF.
11. Strings: 639 keys. Removed: `notice.values_not_measured`, `s4.record.not_measured`, `values.not_measured`. `node ui/tools/check_ui.mjs`: passed, 0 errors.

## The cascade of a record on the result page (13.10.2026)

`../CONTRACT.md` chapter 18.5 has the rules. Changes:

1. `index.html`: one element `rec-cascade` at the top of the eCH-0295 part.
2. `app.js`: the functions `renderCascade` and `cascadeEntry` build the part "What this document can state" from the view key `head_values.cascade`. `reasonText` reads the kind of a slot from `slots[].kind`. A candidate of the kind `addressee` has its own row text in the table. The fold line is removed; the line `values.prob.in_sample` shows for `values[].in_sample` true.
3. `strings.json`: 42 new keys (`cascade.*`, `notice.cascade_selection`, `notice.addressee_candidate`, `slot_reason.not_searched`, `doc_kind.executive_proposal`, `doc_kind.committee_report`, `values.prob.in_sample`, `values.addressee`, `values.addressee.prob`, `note.addressee_candidate`, `check.C22_values_from_the_readers`); 4 keys removed; changed texts: `notice.values_measured`, `s4.record.measured`, `words.states`, `about.p5`, `slot_reason.not_in_this_document_type`, `doc_kind.proposal`, `export_check.no_export_value`.
4. `app.css`: the classes `cascade*`.
5. `node ui/tools/check_ui.mjs`: PASSED, 0 errors.

## Rule V5, the reason `reader_scope` and the corrections S3-06 to S3-08 (13.10.2026)

`../CONTRACT.md` chapter 19.4 has the rules. Changes:

1. `app.js`: `renderCascade` shows where the kind comes from and the 2 facts of rule V5. `cascadeEntry` and `reasonText` know the reason `reader_scope`. `labelName` gives the card of an addressed body its own heading. The count line uses the limit of the labels of the blocks only.
2. `strings.json`: 699 keys. New: `cascade.kind.from*`, `cascade.kind.fact.*`, `cascade.state.reader_scope`, `cascade.texts.not_written*`, `slot_reason.reader_scope*`, `notice.response_signs`, `kind.pdf_addressee`. Removed: `cascade.kind.value`, `cascade.texts.kept`. Changed: `about.p3`, `unc.no_threshold`, `cascade.idea`, `cascade.step.not`, `cascade.texts.cut*`, `note.addressee_candidate`, `notice.cascade_selection`, `notice.values_measured`, `s4.record.measured`.
3. `app.css`: the class `cascade-warn`.
4. `node ui/tools/check_ui.mjs`: passed, 0 errors.
5. Browser (built-in browser pane, the server of the package): 3 result pages, 1 in English and 2 in German (`../STATE.md` chapter 14.3).

## The findings V4-01, V4-04 and V4-06 (13.10.2026)

`../CONTRACT.md` chapter 20.2 has the rules. Changes:

1. `app.js`: `renderCascade` shows the paragraph of the limit of rule V5 for a record with the kind response by rule V5. The card of the document label has one more sentence for a record with a kind by rule V5.
2. `strings.json`: 701 keys. New: `cascade.kind.v5.response_limit`, `unc.doclabel.v5`. Changed: `slot_reason.reader_scope.response_date` (German text).
3. `node ui/tools/check_ui.mjs`: passed, 0 errors.
4. Browser (built-in browser pane, the server of the package): 3 result pages, 1 in English and 2 in German (`../STATE.md` chapter 15.2).

## Rule V5 made narrower (13.10.2026)

`../CONTRACT.md` chapter 21.3 has the rules. Changes:

1. `app.js`: `renderCascade` does not show the paragraph of the limit of rule V5. The row of fact 2 has a third text for a sign of the executive that is no response cue (`kind_facts.response_sign`). The row of the result has one more text for such a document with no type word.
2. `strings.json`: 702 keys. Removed: `cascade.kind.v5.response_limit`. New: `cascade.kind.fact.response.sign`, `cascade.kind.fact.result.sign`. Changed: `cascade.kind.fact.response`, `cascade.kind.fact.result.changed`.
3. `node ui/tools/check_ui.mjs`: passed, 0 errors.
4. Browser (built-in browser pane, the server of the package): the cascade part of 3 records, 2 pages in English and 2 in German (`../STATE.md` chapter 16.3).

## Changes of 14.10.2026: start page, page "About", result view

Reason: the owner said that a person must understand the page in 3 minutes. For each topic, a link must lead to the place with more facts. The page needs a place with the PDF, a place with the RDF and a place with the probability of each label.

- `index.html`: new S0 (start), new section `screen-about`, new section `screen-view`; the long texts of the earlier S0 are now in `screen-about`; a link at the top of S4 goes back to the result view. New navigation entry "About".
- `app.js`: the functions `showStart`, `renderStartSamples`, `renderGood`, `showAbout`, `renderNumbers`, `showView`, `renderView`, `renderViewPages`, `renderViewRows`, `loadTtl`, `renderTtl`, `selectValue`, `bindView`; `loadView` is the one load of a view for the result view and the technical view. A finished job opens `#/view/<id>`. The sample cards of S1 open the result view.
- The box of a written value is the part of each line of its span: the share of the characters of the line, as in the technical view. With no span, it is the frame of its lines. The grey boxes are the union of the line frames of each block.
- The RDF place reads the files with the roles `ech_ttl` and `values_ttl` of the view (`GET /api/records/<id>/files/<name>`). The marks of a value: in the eCH-0295 file each line that holds the value as a whole string; in the file of the values the lines of the node `<record IRI>/value/<field>`.
- `app.css`: the styles of the new parts; the colours `--c0` to `--c7`, `--certain`, `--unsure`, `--blk` for the light and the dark scheme.
- `strings.json`: 93 new keys (`nav.about`, `fmt.percent`, `start.*`, `about.*`, `view.*`, `s4.to_view`, `dl.role.values_ttl`, `dl.role.source_pdf`, `dl.role.page_image`); 3 keys of the earlier S0 removed (`s0.choices.label`, `s0.sample.note`, `s0.about.note`); `about.steps.note` and its hosted text say that the PDF of a sample is in the package for the page image and the download.
- Checks: `node --check ui/app.js` passed; `node ui/tools/check_ui.mjs` 0 errors (795 keys); `python3 ui/tools/make_run_numbers.py --check` equal. Browser (the built-in browser pane, Chromium, and Google Chrome headless for screenshots at 1440 px): the start page and the result view in English and German, the page "About", the fixture mode (a record with no image: the page draws the lines), a width of 375 px with no horizontal scroll on the start page, the page "About" and the result view. A click on a row, a box and a triple marked the same value in the 3 places. Not run: Firefox, Safari, a screen reader, a zoom of 200 %.

## Corrections of 14.10.2026 after two readers (a jury reader and an examiner)

Reason: the readers found that the page gave a probability of 0.97 next to "correct in 22 %" and did not say which number to believe. They also found defects in the file of the values, in the heading and in the layout.

- Result view, line under the heading (`view-source`): where the values come from. A sample in the mode with Apertus: "The values in the table come from code rules. The stored Apertus results give only the labels of the text blocks." The mode "code rules only" and an own PDF have their own sentence.
- Heading: a title that the rules read from the PDF. With no such title: the OpenParlData title of a sample (from `GET /api/samples`), or the weak candidate; the line `view-title-note` says which one, with the number of the weak candidate.
- Above the table: one line on the probability. It comes from the development documents; on the documents of other parliaments in the fixed run the values were right less often. One line on «certain»: only the type of affair and the responding body can be «certain». The rule tier must be right in 95 % or more of 30 or more development documents (source: `values.round4.<field>.calibration.threshold_a` of `numbers.json`).
- Below each value row, one line (`tr.vrow-sub`): "{k} of {n} development documents right" (from `calibrations[].basis` of the view; "this sample is one of them" if `in_sample`), "Few documents: the number is not stable." and a pale bar for fewer than 30 documents; the precision of the field in the fixed run with its counts (correct of given); for a sample the comparison with OpenParlData (equal, equal by the comparison rule with the OpenParlData value, different with the value, or no value). The share correct of the documents stays on the start page and on the page "About" only.
- The body that a proposal addresses (`addressee_candidate`) has its own row with its number. It is not in the line of the fields that were not searched. That line now names the role of the document: "Role of the document: «proposal». The role decides which steps the document can state. The rules do not search: …".
- Layout: the PDF and the values side by side (columns 1 : 1.15), the RDF below them across the width. At 1440 px the page image is about 540 px wide; a link opens the image in full size. A word in the column "Value as printed" breaks only if it does not fit the line.
- In the RDF place, the first line of the triples of each value is a button for the keyboard (Enter or space). Its name is "Triples of the value …".
- The cards of the start page have an accessible name (title, facts, action).
- The link "Details" goes to the card of the label in the technical view at once (no smooth scroll: a smooth scroll over the long page stopped before the card). `intoView` uses no smooth scroll if the tab is hidden.
- Start page: the box "How often correct?" lists the 7 fields on one line each and says "code rules only". The heading says "Each of its 7 head values has a probability". The flow names the text parts of the PDF.
- Page "About": `s0.values` (a repetition of the 7 fields) removed; `about.p5` shorter; `about.p3` (certain and unsure) matches the result view; the probability is described as coming from the development documents in which the same rule tier gave a value; the column header says "with an OpenParlData value"; the run is "code rules only".
- The RDF notes: the eCH-0295 file holds the text parts of the PDF as HTML text with no row in the table; the file of the values names the actor whose name holds a value.
- The back link of the technical view: "Back to the result" (the double arrow is gone).
- `ui/run_numbers.json`: new value `given` (correct + wrong) for each field; the key `start_fields` is gone (`make_run_numbers.py`).
- `strings.json`: 808 keys (795 before). New: `start.card.label`, `view.source.auto`, `view.source.rules`, `view.source.own`, `view.title.weak`, `view.title.sample`, `view.values.certain`, `view.basis`, `view.basis.in`, `view.basis.few`, `view.run_precision`, `view.export`, `view.miss.addressee`, `view.role`, `view.pdf.full`, `view.ttl.aria`. Removed: `view.run_share`, `view.not_searched`, `s0.values`.

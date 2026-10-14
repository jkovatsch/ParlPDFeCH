# State of the ParlPDFeCH package after the correction round (stages P0a and P0b)

Status of all results of the package: EXCEPTION, NOT RELEASED. No human checked this file or the results.

Date of all measurements: 13.10.2026. Host: one Mac (Apple silicon, macOS), cargo 1.97.1, Python 3.12, Node.js 24.19.0, no network. Each value has one of three marks where it is not a rule: measured, read or estimate. A check that was not run has the words "not run". Each value is from one run if the text does not say more.

This file describes the package after two fixers changed it (worker and data; page) and after the document and gate step ran each check again. After that, a second skeptic check made 10 more findings (S2-01 to S2-10); chapter 10 describes the changes for them and what was run after them. The chapters 1 to 8 give the values of the document and gate step where they do not name chapter 10. After that, the package got a self-contained source tree (`make dist-src`), a deploy kit for a hosted sample site (`deploy/`, never applied) and two server settings for a public site; a third check made 13 findings on them (D-01 to D-13); chapter 10.4 describes the changes for them and what was run. After that, a fourth check made 7 findings (E-01 to E-07), and one step made the static site below `/` a supported part of the package and gave the page its texts for a hosted site; chapter 10.5 describes these changes and what was run. Where chapter 10.5 gives another value than an earlier chapter (the count of tests, of string keys and of error codes, the size of the server binary), chapter 10.5 is the value of now. `EXAMINATION.md` lists each of the 108 findings with its decision. Chapter 9 holds the decisions for the owner. After that, the package got the record whose head values are read from the PDF; chapter 11 describes it and what was run. Where chapter 11 gives another statement than an earlier chapter, chapter 11 is the statement of now. This applies to what an unknown PDF gets, to the source of the head values, to the view version and to the counts of string keys, layout files and gate rows. The chapters 1 to 10 describe the earlier record form, which stays in the package behind the switch `PARLPDFECH_VALUES=off`. After that, a third skeptic examined the cascade in writer, validator and package (findings S3-01 to S3-10); chapter 14 describes the changes and what was run. Where chapter 14 gives another statement than chapter 13, chapter 14 is the statement of now. This applies to the calibration file, to the source of the kind, to the text blocks and to the numbers of the samples. After that, a fourth skeptic examined rule V5 and the validator (findings V4-01 to V4-07); chapter 15 describes the changes and what was run. Where chapter 15 gives another statement than chapter 14, chapter 15 is the statement of now. After that, the main agent made rule V5 narrower (reader `m11-values-cascade-4`) and made round 4 again; chapter 16 describes the changes of the package and what was run. Where chapter 16 gives another statement than the chapters 14 and 15, chapter 16 is the statement of now. This applies to rule V5, to the calibration file, to the numbers of the records and to the rule files of the samples. Chapter 17 has the findings V5-01 to V5-08. On 14.10.2026 the texts that named a last run as future work were changed; chapter 18 describes it. An earlier chapter can name that run as planned or in work, or its documents as documents that nobody read. There chapter 18 is the statement of now. On 14.10.2026 the package got a new start page, a page "About" and a result view with the PDF, the values and the RDF side by side; chapter 19 describes them. Where chapter 19 gives another statement than an earlier chapter (the files of a record, the versions of the writer and of the validator, the counts of string keys, the sample folders), chapter 19 is the statement of now. After that, two readers (a jury reader and an examiner) checked chapter 19; chapter 20 describes the corrections. Where chapter 20 gives another statement than chapter 19, chapter 20 is the statement of now. This applies to the file of the values, the versions of the writer and of the validator, and the result view.

## 1 What is built

| Part | Result | Measured |
|---|---|---|
| Sample data `data/samples/` | `worker/make_samples.py --check`: 0 problems | 3 samples, 28 files, 3,030,092 bytes, no PDF |
| Code layout `build/layout/` (not tracked by git) | `worker/layout.py --check`: exit code 0 | 72 files, 0 SHA-256 differences; 42 compiled files with a recorded SHA-256, 0 different, 0 compiled files that the manifest does not record (the correction round removed 42 files of another Python version) |
| Server | built again with `make native-server` (cargo, release, with `--remap-path-prefix`) after the server changes of chapter 10.4 (the settings `PARLPDFECH_READONLY` and `PARLPDFECH_SAMPLE_RUNS`, the error code `read_only`, 2 new keys of `/api/health`) | binary 2,944,544 bytes after chapter 10.4 (before these changes: 2,944,480); 2,961,168 bytes after the changes of chapter 10.5; the search step of each build: 0 paths of this computer |
| WebAssembly bundle | built by the correction round with `rdfcheck/build.sh` (two builds gave the same SHA-256, reported by the fixer); not built again in this step: no source file of the module is newer than the bundle | `ui/pkg/parlpdfech_rdfcheck_bg.wasm` 2,067,498 bytes, glue script 13,174 bytes; 0 paths of the build host (before: 163) |
| Stage P0b: a PDF that is not a sample (`worker/fresh.py`, `worker/pdf_only.py`) | runs in the profile `native` on macOS | chapter 3.1 |
| Container image | NOT BUILT. No Docker command that builds or starts was run. | |
| Self-contained source tree `dist-src/` (not tracked by git) | `make dist-src` made it; `make -C dist-src check-dist` passed (chapters 10.4 and 10.5) | 184 files and `DIST-MANIFEST.json`; `layout/` 73 files (the 72 copies and the layout manifest). With `SITE_DIR` the tree also has the folder `site/` (chapter 10.5: 211 files with the site of that run) |
| Static site below `/` (`PARLPDFECH_SITE_DIR`; the pages are built outside the package) | run with no container (chapter 10.5) | the 27 files of the site of that run answer 200 with the bytes of the folder |
| Deploy kit `deploy/` (a pipeline file and manifests for a hosted sample site) | WRITTEN AND READ. NOT APPLIED: no pipeline ran, no image was built, no manifest was applied. | `deploy/README.md`, `deploy/RUNBOOK.md` |

A build of the server or of the bundle from an empty target folder was not run in this step.

## 2 Checks of the parts (each one run in the document and gate step)

All checks ran after the last change of the two fixers. One test file changed during this step (`rdfcheck/tests/samples.rs`, row "clippy" below); the checks of the module ran again after that change.

| Check | Result | Values |
|---|---|---|
| `make test` | passed, exit code 0 (run again after the changes of chapter 10.4 and of chapter 10.5) | server: 16 unit tests, 32 integration tests after chapter 10.5 (28 in the document and gate step; 30 after chapter 10.4); rdfcheck: 7 tests. 2 of the 7 tests read no record when the variable `PARLPDFECH_TEST_RECORDS` is not set. They pass, and the output of `make test` does not show that they read nothing (the line "SKIPPED" goes to the error output, which cargo keeps for a test that passes; the second skeptic found 0 such lines in the log); the example view is valid against the schema; `view/check_view.py` passed; 6.2 s with built test programs |
| `cargo test -p parlpdfech-server` (alone) | passed | 16 + 28 tests in the document and gate step; 16 + 30 inside `make test` after the changes of chapter 10.4 |
| `cargo test -p parlpdfech-rdfcheck` with the records of the server of this step (variable `PARLPDFECH_TEST_RECORDS`) | passed | 7 tests with the 3 records of the mode `auto`; 7 tests with the 3 records of the mode `rules` |
| `cargo clippy -p parlpdfech-server --all-targets -- -D warnings` | passed (run again after the changes of chapter 10.4) | no finding |
| `cargo clippy -p parlpdfech-rdfcheck --all-targets -- -D warnings` | first run: NOT PASSED, 5 findings in the test file `rdfcheck/tests/samples.rs`. The 5 places were changed in this step (a parameter type; 4 calls of the form `.err().expect()`). Second run: passed. | The same command for the target `wasm32-unknown-unknown` (library only): passed |
| `node rdfcheck/tools/check_wasm.mjs` (the built module in Node.js) | passed, 4 runs, each "ALL CHECKS PASSED" | 3 sample records of the mode `auto`; 3 of the mode `rules`; the upload record of the mode `auto` and of the mode `rules` (1,311 statements, 14 labels, 12 rows compared and equal, 14 of 14 labels with no `inSample` statement, 0 rows for the example of the head values); 0 paths of a build host in the 2 bundle files |
| `worker/check_worker.py --reference-dir <reference run> --sample-pdf <PDF of 26171>` | passed | 82 of 82 checks; 59.2 s |
| `worker/check_fresh.py --pdf-dir <folder of the 3 sample PDF files>` (variant `stored`) | passed, exit code 0 | each run as expected. The 3 sample PDF files as PDFs that are not in the package: valid; blocks equal 13 of 13, 24 of 24, 8 of 8; lines equal 36, 45, 11; labels with a probability equal to the record of the mode `rules` 14 of 14, 25 of 25, 9 of 9; the search in the 11 files of each record: 0 hits (document numbers, export addresses, home folder, reference text); 0 labels with the slot `in_sample`. 5 synthetic cases: `done`, `pdf_unreadable` (2), `too_long`, `no_text_layer`. 59.8 s |
| `view/check_view.py` | passed | 4 records and the note filter; the view of `s-26171` equals the example (0 differences in the rule, 0 exempt) |
| `node ui/tools/check_ui.mjs` | passed, 0 errors (run again after the changes of chapter 10, of chapter 10.4 and of chapter 10.5) | 463 string keys of the page after chapter 10.5 (435 after chapter 10.4, 430 before), each with `en` and `de`; 83 keys of the panel; no stop list note; 2 new rows for the panel (chapter 10). Notes: 5 contract keys are not used by `app.js`; 4 contract keys are for the panel |
| `worker/layout.py --check`, `worker/make_samples.py --check` | passed | chapter 1 |

Not run in this step: a browser; the variant `full_settings` of `check_fresh.py`; the runs with an empty home folder and a write audit (the fixer of the worker ran them: 3 runs, 0 entries in the home folder).

## 3 The gate (CONTRACT.md chapters 8, 11.5 and 12)

The server of this step ran on `127.0.0.1:8897`: the binary of chapter 1, profile `native`, the variables of the target `run-native` with an own empty work folder (`work/docs/work`), the real worker through `uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/serve_convert.py`, working folder = the project folder. The target `make run-native` itself was not called in this step (its work folder was in use by another server process).

`make gate PORT=8897 GATE_OUT=work/docs/gate GATE_REFERENCE=<reference run>` gave 100 rows: 97 passed, 0 not passed, 3 rows of information not met (G2 plain SHA-256, as before). Exit code 0. Time 111 s. The report file is `work/docs/gate/gate_report.json`.

| Gate | Rows | Result | Values (measured) |
|---|---|---|---|
| G1 conversion through the server, mode `auto` | 3 | passed | 13 events, last event `done`, `valid` true, `apertus` `stored`. Labels: 26171 33 (9 certain, 6 unsure); 879163 42 (12, 14); 714840 18 (6, 4) |
| G2.0, G2.1, G2.2, G2.3, G2 | 3, 3, 3, 3, 9 | passed | against the direct call and against the reference record: the 3 YAML files and the TriG file equal after the replacement of the run time, the Turtle file and the eCH-0295 YAML file byte-equal, the 2 RDF/XML files isomorphic |
| G2 plain SHA-256 of the 7 server files against the run record | 3 | NOT MET (information) | equal: `ech_yaml`, `ech_ttl`; not equal: the 5 files that hold the run time or RDF/XML |
| G3 mode `rules` | 9 | passed | Labels: 26171 32 (0 certain, 14 unsure); 879163 47 (0, 25); 714840 21 (0, 9). Statements: 2,624; 3,751; 1,481 |
| G4 view | 3 | passed | the views are valid; the view of `s-26171` equals the example; new row: 8 views hold no document number of another document, no project path, no words of the reference text and no raw note of the converter |
| G5 API | 44 | passed | as before, with: a foreign `Host` header gives 403 (API and page); a POST with a foreign `Origin` and a DELETE with `Sec-Fetch-Site: cross-site` give 403 and change nothing; a path that is not UTF-8 gives 404 with the error object; 6 addresses of development files below `/app/` give 404; the job object of a stopped job has no stage `running` |
| P0b upload | 17 | passed | chapter 3.1 |

Measured outside the gate: `/healthz` with a foreign `Host` header answers 200 (the rule of the contract); `/api/health` and `/app/` with the same header answer 403.

Time for one sample through the server (seconds from the POST to the end of the job, one run each): mode `auto` 26171 3.59, 879163 3.81, 714840 3.36; mode `rules` 26171 3.52, 879163 3.89, 714840 3.23. Earlier runs of the same step gave 3.3 to 5.3 s.

### 3.1 Stage P0b through the server (profile `native`, macOS)

The PDF files are synthetic (`contract/tools/make_test_pdf.py`: written by hand, invented text). No PDF of a parliament that is not a sample was read. The 3 sample PDF files were converted as PDFs that are not in the package by `check_fresh.py` (chapter 2), not through the server.

| Check | Result | Values |
|---|---|---|
| `/api/health` | passed | `modes.upload` true, `reason.upload` null, `ocr` `apple` |
| Upload of `text_layer.pdf` (1,789 bytes, 13 lines) | passed | 12 events, `done`, `valid` true, `apertus` `none`; record `u-<first 16 hex of the SHA-256>`; 9.63 s |
| The view | passed | valid against `contract/view.schema.json`; `origin` `new`, `doc_id` null, no export; `in_sample` null for the record and for each label; notices `proposal`, `no_human_check`, `no_apertus`, `chosen_not_top`, `no_export`, `not_a_sample`, `not_examined_pipeline`, `ocr_apple`, `shacl_not_run`; 14 labels (0 certain, 11 unsure, 3 with no probability; for 6 of the 11 the selected answer is not the answer with the highest number); 1 page, 13 lines, 9 blocks, 1,311 statements |
| The 11 files and `bundle.zip` | passed | media types of the contract; served bytes equal `convert.json` 10 of 10; 12 entries, 11 of 11 `SHA256SUMS` lines correct |
| Content of the files, the two upload records | passed, 7 rows | no home path, no export address; conformance `pdf_only_with_recorded_gaps`; document IRI `urn:parlpdfech:local:sha256:<hash>`; 21 absent slots recorded; 0 document numbers of the search list (5 numbers) in the 11 files; 0 absolute paths, 0 project paths outside the code layout and the run, 0 words of the reference text; no label with the slot `in_sample`; `manifest.json`: `apertus` `none`, `sample_of_the_package` false, `development_document` null, `probabilities_checked_on_other_documents` false |
| Mode `rules` | passed | `done`, valid, record `u-...-rules` |
| Refusals | passed | a file with no PDF content and a PDF with 0 pages: `pdf_unreadable`; 26 pages: `too_long`; one picture with no letters: `no_text_layer`; document number that is not a sample: `doc_id_unknown`; the number of a sample with another PDF: `pdf_differs_from_doc_id` |
| DELETE | passed | 204, then 404 `record_unknown`; the rules record: 204 |

Stage times of one upload of the same PDF after the gate (worker, `convert.json`): `read_pdf` 6.30 s (start of Docling 5.65 s, conversion 0.40 s), `lines` 0.05, `rules` 0.004, `write` 1.74, `check` 0.77, total 8.86 s.

### 3.2 The page in a browser

No browser ran in the document and gate step. The fixer of the page ran one engine (Chromium) with the real server of the package; `ui/README.md` chapter "Changes of the second correction round" has the list of what was seen (S0, S1, S2, S3, S4 in English and German; 6 widths; keyboard) and of what was not run (the fixture mode, the stop button, a drop of a file with the mouse, a screen reader, Firefox, Safari, the forced-colours mode, a zoom of 200 %, a record with more than one page, a record that is not valid). One text (`mode.samples.stored`) changed after the last browser pass of that fixer.

### 3.3 Measurements for single findings (earlier steps; not repeated in this step if not said)

| Finding | Measurement | Result |
|---|---|---|
| X1-01 | a second start during an upload job (fix step); the lock with two processes (skeptic) | exit code 2; the job folder stayed; the job ended valid |
| X1-08 | a client that sends the full body before it reads (fix step, 3 cases) | all bytes sent; 413, 415, 409; no reset |
| X2-08 | a synthetic copy of sample 26171 with one U+0007 (fix step; skeptic with a new copy) | exit code 2; checks that did not run have the state `skipped`; notice `rdfxml_not_readable`; no absolute path in `validation.json` |
| X2-09 | 3 runs with an empty home folder and a write audit (fixer of the worker) | 0 entries in the home folder, 0 writes outside the scratch folder. The audit covers the Python process only. |
| X2-10 | a compiled file replaced after the build (fix step; skeptic) | the file did not run |
| V-13 | trace of a fresh run (fixer of the worker) | 0 opened or listed paths below the project folders `src`, `daten`, `web`, `public`, `crisp-dm`, `quellen`; 6 child processes (`uname`, `file`, `pdftotext` 4 times); 1 network event (a bind to `::1`) |
| Sample path, this step (`check_worker.py` group T) | trace of sample 26171 in the two modes | 0 paths of the project folders opened or listed (2,891 and 2,458 paths); 0 child processes; 1 network event (a bind to `::1`) |

## 4 What does not work, and limits

1. The container files were not run. `Dockerfile`, `compose.yaml` and the targets `run`, `run-full`, `check-offline`, `stop`, `remove` are written and read only. The lines that the correction round added to the `Dockerfile` (the path mapping of the build and two search steps) were not run; if a binary holds one of the search patterns for another reason, the build stage stops.
2. Nothing was run on Linux. The profile `full` (own PDF with no OCR, device `cpu`) is code that was read; the builder of stage P0b ran its two Docling arguments on macOS: 1 of 3 sample block files was equal to the stored one with no OCR.
3. The profile `slim` converts no PDF that is not a sample (answer `not_in_package`). This is the design.
4. The record of an own PDF is not a full eCH-0295 record: the eCH-0295 graph holds 1 statement (a container with no affair); the text blocks are in the provenance graph (CONTRACT.md chapter 10.3).
5. The probabilities of an own PDF were not checked on any document outside the development documents. The record does not say if the PDF is a development document. The counts of the rule of the document label come from runs with export values.
6. The conversion of an own PDF in the profile `native` needs the two Docling models in the hub cache of the user account and the command `pdftotext`. The worker reads that cache, also its two token files. The statement "no request to another host" for this branch rests on the audit trace of the Python process (one run of the fixer), not on a capture of the network; native code is not seen by the trace.
7. Plain SHA-256 equality with the run record is not possible for 5 of the 7 output files (the run time; the sequence of the XML elements).
8. The server has no time limit for the request header and no limit for open connections (X1-09). A worker whose child process holds the standard output open keeps the job slot until the job time limit (X1-18). A known address with a wrong method gives 404, not 405 (X1-13). A request that the HTTP parser refuses gets an answer with no header of the contract (X1-14).
9. `/api/health` does not test that the states file of a sample exists (X2-14 point 5).
10. The time limit of a free SPARQL query in the page fallback (no worker thread) cannot stop a query before its first row (reported by the WebAssembly part; not run again). The messages of the query engine are English in the German page.
11. The fixture mode of the page (`?fixture=1`) does not work through the server of the package: the server does not serve `ui/fixtures/`. It needs a plain file server. It was not run after the changes.
12. The drawn page text is 4 to 7 px high at a width of 320 px; the text list is open there. The height of a table row at 320 px, measured by two parties in one browser engine: a result row of a query up to 283 px (fixer of the page) and up to 333 px (second skeptic: German page, record `s-26171`, first example query); a row of the comparison table up to 224 px (second skeptic). Not measured again after the changes of chapter 10 (a cell of the comparison table no longer holds the line with the stored name).
13. The contract texts `notice.stored_apertus`, `notice.in_sample_heads`, `notice.in_sample_rules`, `notice.proposal` and `unc.target.*` were written again in chapter 10; `notice.proposal` keeps the words "AI reference" (in the list of words). The list of words is closed on S1 and S4. 12 contract keys are not used by the page (CONTRACT.md chapter 7.7).
14. `calibrations[].note` and `measure_sets[].name` of the view are the English texts of the converter with working words of the project. The page does not print the note; the name of a measure set shows in one line of a card. An IRI with the path part `/gj/` shows in the technical details and in the panel.
15. The record of an own PDF is not a neutral file. Each of its files that the converter code writes keeps texts of the project (counts of the second skeptic on one record): 31 different project-relative paths (inputs with their SHA-256 in `manifest.json`, 12 names of reduced tables and the Docling arguments in `convert.json`, `fit_set_file` in the label files); the internal status text in `local.labels.yaml`, `local.ech.yaml` (a comment), `manifest.json`, `convert.json` and `view.json`; working words of the project in the notes of the calibration records. `/api/health` also returns the status text. No page prints these. This is decision 4 (d) of chapter 9.
16. Not run: a scan with letters; a PDF of about 20 pages in the fresh branch; a full disk for the note `out`; two uploads at the same instant with the real worker; a page of another site against the origin rule in a browser.

## 5 Stubs

1. `worker/states_provider.py`: the kinds `stored` and `remote` are NOT IMPLEMENTED (they raise `NotImplementedError`). Only the kind `none` exists. No model starts for an own PDF.
2. `worker/fresh_tables.json`: tables of the rule chain with no row. The guards and the measurement tables of the rule chain have no function in the package.
3. The split guard of the converter: for a sample it runs with a table in memory that holds only the parliament of the sample; for an own PDF it is not called. It has no protecting function in the package.
4. The environment switches `PARLPDFECH_FRESH_OCR=none` and `PARLPDFECH_FRESH_DEVICE=cpu` are a measurement aid for the profile `native`.
5. `/api/health` key `ocr`: `apple` comes from the profile and the platform; the server does not test if the package `ocrmac` is present (the worker does).
6. `server/tests/fake_worker.py` and `server/tests/fixtures/` are test stand-ins. `ui/fixtures/` and the query `fixture=1` replay the contract examples.

## 6 Hygiene scan (run in the document and gate step, after the last change of a document)

### 6.1 The files of the package (without `target*/`, `build/`, `work/`; 119 files, also the 2 generated files of `ui/pkg/`; each file read as bytes)

| Scan | Files with a hit |
|---|---|
| First name of the owner (from `git config user.name`), family name, local part of the mail address, name of the user account | 0, 0, 0, 0 |
| A path that starts with a home folder of this computer | 0 |
| The pattern `/home/<letter>` | 2: `server/src/errors.rs` and `view/check_view.py`, each a made-up path in a test that checks that paths are removed |
| The words that the hygiene rule forbids (4 patterns) | 0 |
| Key or token patterns (9 patterns) | 0 |
| The word "token" | 13: this file, `README.md` (the token files of the hub cache), `container/requirements-full.txt` (a package name), the 3 `atoms.json` files (field names of counts), the 3 `states.npz` files (names of arrays), the WebAssembly module (words of the parser), `worker/README.md` and `worker/states_provider.py` (the interface of a later states provider), `worker/fresh.py` (the name of a variable that keeps the stored hub token out of requests) |
| PDF files (by name and by the first 5 bytes) | 0 |
| A file name with a 5 to 7 digit number that is not a sample | 0 |
| The internal status words and the working names (candidate, addendum, cascade, floor, tier, gate) in the 8 files that the server gives below `/app/` | status words 0. Working names 0, except the function name `Math.floor` in `app.js` (1). The words "AI reference" / «KI-Referenz» are in 3 texts of `strings.json` (`notice.proposal`, `unc.basis`, `words.reference`); they are texts of the contract and of the list of words |

### 6.2 Binary files (byte search)

| File | Home folder path | Name of the user account | Mapped names of the build |
|---|---|---|---|
| `ui/pkg/parlpdfech_rdfcheck_bg.wasm` (2,067,498 bytes) | 0 | 0 | `/cargo/` 138, `/rustup/` 25 |
| `ui/pkg/parlpdfech_rdfcheck.js` (13,174 bytes) | 0 | 0 | 0 |
| `target-server/release/parlpdfech-server` (2,944,480 bytes; the binary before the changes of chapter 10.4. The binary of now has 2,961,168 bytes; for it only the search step of `make native-server` ran: 0 paths of this computer) | 0 | 0 | `/cargo/` 304, `/rustup/` 52 |

The mapped names stand in place of the folders of the build host (source paths of crates in messages of the code).

### 6.3 The files of three records (downloaded as `bundle.zip` from the server of this step; 11 files each, each `SHA256SUMS` line correct)

Counts of hits by file. "Paths" = a project-relative path that starts with `daten/`, `src/`, `quellen/`, `crisp-dm/`, `web/` or `public/`. "Other numbers" = the document numbers 879163, 714840, 375917, 549658 in a record of 26171. "Working names" = the sum of the hits for candidate or B1-S, addendum, cascade, floor, tier, gate names. "Reference text" = the words "AI reference" and the 2 folder names of the reference (each hit counted). Each of the 33 files: 0 home paths, 0 names of the user account, 0 absolute paths.

| File | `s-26171`: paths / other numbers / working names / reference text / status words | `s-26171-rules`: the same | upload record: the same |
|---|---|---|---|
| `<doc>.ech.rdf.xml` | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| `<doc>.ech.ttl` | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| `<doc>.ech.yaml` | 1 / 0 / 2 / 0 / 2 | 1 / 0 / 2 / 0 / 2 | 0 / 0 / 0 / 0 / 2 |
| `<doc>.gesamt.rdf.xml` | 40 / 0 / 82 / 9 / 3 | 37 / 6 / 87 / 6 / 3 | 12 / 0 / 52 / 0 / 2 |
| `<doc>.gesamt.trig` | 40 / 0 / 50 / 9 / 3 | 37 / 6 / 61 / 6 / 3 | 12 / 0 / 42 / 0 / 2 |
| `<doc>.labels.yaml` | 17 / 0 / 20 / 9 / 2 | 14 / 6 / 33 / 6 / 2 | 10 / 0 / 31 / 0 / 2 |
| `<doc>.provenance.yaml` | 24 / 0 / 30 / 0 / 1 | 24 / 0 / 26 / 0 / 1 | 2 / 0 / 7 / 0 / 0 |
| `manifest.json` | 32 / 0 / 2 / 0 / 2 | 33 / 0 / 4 / 0 / 2 | 22 / 0 / 6 / 0 / 2 |
| `validation.json` | 5 / 0 / 0 / 0 / 0 | 5 / 0 / 0 / 0 / 0 | 5 / 0 / 0 / 0 / 0 |
| `convert.json` | 0 / 0 / 1 / 0 / 2 | 0 / 0 / 1 / 0 / 2 | 14 / 0 / 1 / 0 / 2 |
| `view.json` | 0 / 0 / 43 / 0 / 4 | 0 / 0 / 55 / 0 / 4 | 0 / 0 / 41 / 0 / 4 |
| Sum | 159 / 0 / 230 / 27 / 19 | 151 / 18 / 269 / 18 / 19 | 77 / 0 / 180 / 0 / 16 |

What the counts say:

- Sample records: the files of the converter hold project-relative paths of its inputs, working names of the project (also in IRIs and in `tier` values), the internal status text, and in the calibration records the reference text of the project. In the mode `rules` that text names 3 document numbers; 2 of them (375917, 549658) are not samples. These files are bytes of the converter with recorded SHA-256 values; they were not changed. This is decision 1 and 2 of chapter 9.
- Upload record: 0 document numbers of other documents and 0 hits of the reference text in the 11 files. The paths are relative paths of the code layout and of the scratch root of the run (inputs with their SHA-256; in `convert.json` the names of the reduced tables); the second skeptic counted 31 different paths in one record. The working names are `floor`, `tier` values, the word "candidate" in texts of the converter schema, and words of the calibration notes (for example "rule tier", "criteria 8.7"). The status words are in 5 files (chapter 4 point 15). The counts of the table are from the record before the change of chapter 10 (the calibration records then held the slot `in_sample`); they were not counted again.
- `view.json` holds no path and no reference text in each of the 3 records. It holds the status field, `converter_mode`, `tier` values and the English texts `calibrations[].note` and `measure_sets[].name` (chapter 4 point 14).
- Other numbers of 5 to 7 digits in the sample records (152 hits) are identifiers of the export record of the same document (for example the affair) and byte counts; they were not checked one by one.

### 6.4 Outside the scan

- The source files of the code layout (`build/layout/`, 72 files) are byte-equal copies of converter code; the converter compares their SHA-256. They hold working names of the project and internal notes. Reported by earlier steps and not scanned again in this step: 1 file with the name of the owner or a home path, 28 files with words of the hygiene rule, and one file (`m03_sub_assemble.py`) with a fixed home path; the 13 files that stage P0b added were not scanned. The finding X2-13 names 3 layout files with document numbers that are not samples.
- `data/samples/*/sample.json` and the JSON inputs hold internal project paths (keys `states_job`, `reference_run` and others; finding V-14).
- The scratch folders below `work/` hold logs and reports with absolute local paths. `work/` is not tracked and must not be published.

## 7 Changes of the correction round and of this step

The list by finding is in `EXAMINATION.md`. In short:

1. Worker and record of an own PDF: no document number of another document and no reference text in a file of the record; no statement that the PDF is outside the documents of the fit; new keys of `manifest.json`; no write into the home folder; the notes `out` and `scratch`; the search path entry of a converter copy is taken out; `layout.py` removes and reports compiled files that are not recorded.
2. View and schema: `note_code`, `note_params` and a filtered `note`; `reference_code`; `in_sample` with three states; the notice `not_a_sample`. The example view is made with `contract/tools/make_example_view.py`.
3. Build: path mapping for the server binary and the WebAssembly bundle, with a search step.
4. Page: plain words for a reader with no background (a list of words, names of the steps, of the cards, of the checks and of the sources), one number form, keyboard and accessibility points, the panel on narrow screens, a case for a wrong record address. 424 string keys of the page and 81 of the panel.
5. Gate tools: 100 rows (8 new); `check_wasm.mjs` handles a record with no export record.
6. This step: 5 places of the test file `rdfcheck/tests/samples.rs` (clippy); the documents `STATE.md`, `README.md`, `CONTRACT.md` (chapters 4.2, 6, 7, 10 in place; chapter 12), `EXAMINATION.md`, and smaller corrections of `worker/README.md`, `ui/README.md` and `container/BUILD-NOTES.md`.

## 8 Commands

All commands run from the folder `package/` with no network. cargo, `wasm-bindgen` 0.2.127, `wasm-opt` (optional), uv with the project packages, curl, unzip, node and python3 must be on the `PATH`.

Build:

```
make native-data
make native-server
make native-wasm
```

Start (builds what is absent, then listens on 127.0.0.1):

```
make run-native PORT=8894
```

The page is `http://127.0.0.1:8894/app/`. One server process uses one work folder (`work/`).

Check (in a second terminal, while the server runs with a work folder that holds no record; `<reference run>` is the folder of the project that holds `<doc>/` and `runs/run_1.json`):

```
make gate PORT=8894 GATE_REFERENCE=<reference run>
make test
node ui/tools/check_ui.mjs
node rdfcheck/tools/check_wasm.mjs <folder with one sub-folder for each document> 26171 879163 714840
```

Worker checks with no server, from the project folder:

```
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/check_worker.py
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/check_fresh.py --pdf-dir <folder with the 3 sample PDF files>
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/layout.py --check
```

Use `make native-server` and `make test` for the Rust builds: another set of compiler flags makes cargo build each crate again.

Stop: Ctrl-C in the terminal of the server, or the signal TERM to the server process.

## 9 Decisions for the owner

1. **Publication of the code copies.** The code layout (`build/layout/`, 72 files, not tracked) holds byte-equal copies of converter code with working names of the project, internal notes, and in a small number of files the name of the owner or a home path (chapter 6.4). The copies must stay byte-equal, because the converter compares their SHA-256. The image build needs the folder. The layout also holds ids and block labels of 193 development documents: a list of the 193 documents with the file names of their rule and label files (`daten/gj/calibration/floor_v1_fitset.json`), and an array file of 7,994,969 bytes with document ids, block ids and one label for each block (`daten/gj/design_b1s/oof/b1s_oof.npz`); it holds no text of these documents and no PDF (finding D-03; the two files were read in this package, the hygiene counts of the third check were not counted again). The source tree `dist-src/` holds the same files as `layout/`; the first push of the tree to a git server and the image build of `deploy/RUNBOOK.md` step 2 publish them to that server. Decide before that step: publish the copies as they are, publish cleaned source files with new recorded values (needs a new reference run), or give the layout only inside an image.
2. **The reference text in the download files of the samples.** The label file, the TriG file and the RDF/XML file of each sample record hold the reference text of the calibration records with the words "AI reference", 2 folder names of the project and, in the mode `rules`, 3 document numbers of which 2 are not samples (chapter 6.3). The record of an own PDF holds a neutral text in that place. Decide: keep the bytes of the converter for the samples, or change the converter output (new reference run), or select other samples. Also confirm the neutral sentence: "reference labels of the development documents, made by a language model and not checked by a human". The fixer took the wording from its order; it did not verify from project sources that no human checked the reference.
3. **The sample texts.** `data/samples/` holds the full text of 3 parliament documents with names of persons and the contact data of an office, internal project paths in `sample.json`, and states files with layers that the package does not use (findings X2-12, V-14). A change needs a new reference run (recorded SHA-256 values). Decide: publish these 3 texts, or select other samples.
4. **The form of the record of an own PDF.** (a) The eCH-0295 part is a container with no affair (1 statement); the text blocks are in the provenance part. (b) The conformance name `pdf_only_with_recorded_gaps`. (c) The IRI form `urn:parlpdfech:local:sha256:<hash>`. (d) The record keeps relative paths of the code layout and of the run (31 different paths in one record), the internal status text in 5 files and working words of the project in the calibration notes (chapter 4 point 15). If the record is to be shown as a download: replace the paths of the scratch root by neutral names in `worker/pdf_only.py`, as was done for the reference text. Not done: it changes the manifest that the gate reads, and it needs a decision on the names.
5. **The German texts.** About 110 new or changed keys of the page and 29 of the panel in the correction round (424 and 81 keys in all), and 31 changed and 7 new texts in the step of chapter 10 (430 and 83 keys in all) need the read of the owner; in particular the list of words, «Gemeinwesen» as the name of a row, the text of a rule card with another answer above, and the plain names of the checks (the meaning of `writer_check` and `C7_C8_labels` should be confirmed). Statements of the list of words to confirm: "Apertus: an open Swiss language model"; "eCH-0295 (a draft standard of the association eCH)"; "reference labels: labels that a language model gave to the development documents. No person checked them."
6. **One statement for "development document" (findings V-14 and S2-04 point 4).** For a sample in the mode `auto` the page gives three statements that do not say the same thing: the notice ("This sample is a development document. The project set the read-outs with it."), the row "Development document: yes" in the technical details of each card (from `labels[].in_sample`; for the labels `d1` and `r2` the view takes it from the decisions file), and the panel count "Labels whose number was set with documents that include this document" (13 of 15 for 26171, 24 of 26 for 879163: the labels with the statement `plb:inSample` in the TriG file; `d1` and `r2` have none there). The calibration records of the same view say `in_sample` false for the two read-out calibrations and true for one. Not changed: the values are converter bytes with recorded SHA-256 values. Decide which statement is the fact for a reader (the document was used to make the rules; the document is in the fit set of a calibration; the measures of a calibration were taken on its fit set), then the page gets one wording. A change of the label graph needs a new reference run.
7. **The first container build.** Build and run the image on a computer with Docker (`make run`, `make check-offline`, then `make run-full`). To check there: the layout stage and `layout.py --check` (an image must not hold compiled files that the manifest does not record); the two requirements files with pip; the new build lines (path mapping, search steps); the image bundle against the native bundle (the image stage calls `wasm-bindgen` with other arguments than `rdfcheck/build.sh`); the health check and the host rule with the compose port; the temporary files of Docling and torch in the 256 MB memory file system of `/work`; the Docling models with no hub cache in the target `full` (`container/BUILD-NOTES.md` chapters 7.4, 8 and 9).

Smaller points for the contract owner: the texts of a hosted site (chapter 10.5: 20 keys with the ending `.hosted`, 9 other new keys, the page texts for the codes `forbidden` and `internal`); the error codes `read_only` and `sample_runs_off`, the setting `PARLPDFECH_HOSTED` and the 4 new keys of `/api/health` (`modes.read_only`, `modes.sample_runs`, `site`, `hosted`; `CONTRACT.md` chapters 14 and 15) were added with no confirmation of the contract owner; the 12 contract keys that the page does not use; a code for HTTP 405; a time limit for the request header and a limit for open connections; the test of the states file in `/api/health`; `Cargo.toml` of the workspace lists 3 crates that no member uses (`serde-wasm-bindgen`, `tokio-util`, `futures-util`; reported by an earlier step, not checked again).

## 10 Changes after the second skeptic check (findings S2-01 to S2-10)

`EXAMINATION.md` chapter 9 has the row of each finding. One step changed the page, `worker/pdf_only.py`, `contract/strings.contract.json` and the documents. No Rust source changed in the step for the list S2; the server binary and the WebAssembly bundle were not built again in that step. After it, 3 server sources and the server tests changed for a hosted site, and the server binary was built again (chapter 10.4).

### 10.1 What changed

1. S2-01: the panel row for labels with a statement `plb:inSample` shows "not known" when no label has the statement (changed before this step; checked here in the code and in the browser).
2. S2-02: the calibration records of the record of an own PDF have no slot `in_sample`. `manifest.json` has the new key `calibration_in_sample`. `CONTRACT.md` chapter 10.3 says what the slot means on a calibration record.
3. S2-03: 13 contract texts and 18 other texts of the page have new wording (list in `CONTRACT.md` chapter 13). Open: chapter 10.3.
4. S2-04: (1) headline, page title, button note and the first sentence of "What is this?" say "a PDF of a Swiss parliament or government"; (2) for a sample the first two steps are named "Read the stored pages of the PDF" and "Read the stored lines of the PDF"; (3) the comparison text is "not found with the same letters in the text of the PDF" (the proposed text "not found as one line" is not what the code does: read in the converter code, the search merges white space and goes over line ends); (5) the size of a selected file shows in KB below 0.1 MB and in bytes below 1 KB. Point (4) is decision 6 of chapter 9. Point (6) is in decision 5.
5. S2-05: the stored names in the panel tables ("Labels by source", "Comparison with manifest.json") are in `title` attributes. Open: a `title` attribute does not show for a keyboard or a touch user; the messages of the query engine stay English.
6. S2-08: the one tab stop of the drawn page starts on the first line with text.
7. S2-06, S2-07, S2-10: sentences of this file (chapter 2 row `make test`, chapter 4 points 12 and 15, chapter 6.3, decision 4 (d)).

### 10.2 What was run after the changes (13.10.2026, one run each)

| Check | Result | Values (measured) |
|---|---|---|
| `node ui/tools/check_ui.mjs` | passed, 0 errors | 430 keys of the page, 83 of the panel, 108 contract keys with equal texts; the stop list of the preview site: no match (the check has no stop list note); 5 notes for contract keys that the page does not use |
| `worker/check_fresh.py --pdf-dir <copies of the 3 sample PDF files>` (variant `stored`) | passed, exit code 0 | the 3 sample PDF files as PDFs that are not in the package: valid, each check of `validation.json` that ran passed (C1 to C9); 0 lines with `in_sample` in the label file, 0 statements `plb:inSample` in the TriG file and the RDF/XML file; statements 2,021, 3,034 and 1,106; the 5 synthetic cases as expected |
| `contract/tools/validate_view.py` on the 3 views of that run | valid, 3 of 3 | `calibrations[].in_sample` null for each calibration record; `run.in_sample` null |
| Upload of `text_layer.pdf` through an own server instance (`127.0.0.1:8897`, binary of chapter 1, own empty work folder, real worker) | `done`, `valid` true | 14 labels, 1,307 statements (before the change: 1,311); 0 statements `plb:inSample` in the record; `manifest.json` key `calibration_in_sample` present |
| `node rdfcheck/tools/check_wasm.mjs` on that upload record | "ALL CHECKS PASSED" | 1,307 statements, 14 labels, 12 rows compared and equal, 14 of 14 labels with no `inSample` statement |
| Browser (the built-in browser pane of the desktop app, a Chromium engine; one width, about 1,000 px) | seen | the server of chapter 3 on port 8894 and the own instance: S0 (English), S1 (English), S2 (German; 3 files set with a script: "1.7 KB", "300 Bytes", "2.4 MB"), S3 of sample 26171 (English; the 6 step names captured during the conversion), S4 of `s-26171` (English), `s-879163` (English), `s-714840` (German) and of the upload record (German). The tab stop is on line B2.1 for `s-714840` and `s-879163`. The panel of the upload record shows «nicht bekannt». No table cell of the panel holds a stored name in its text. |

Not run in this step: `make gate` (the gate compares the manifest keys of an upload record; the new key and the absent slot were not run through it), `make test`, `check_worker.py`, `view/check_view.py`, the mode `rules` of an upload through the server, the widths 320 and 800 px, a screen reader, another browser engine, the fixture mode, the keyboard path on the drawn page (the attribute was read, no key was pressed), the hygiene scan of chapter 6 on the changed files (the home path search of `check_ui.mjs` ran on the page files). The browser console showed 3 answers with the status 404 during the pass; their addresses were not read.

### 10.3 Open after this step

1. Closed in chapter 10.4: `README.md` and `worker/README.md` give 1,307 statements for the synthetic PDF. Open: `ui/README.md` gives 424 and 81 keys (now 435 and 83).
2. S2-03: not changed: the texts `s1.card.in_sample`, `source.apertus_readout.*` and `unc.basis` (contract keys that the page does not use) keep the old words. The German texts of this step were not read by a second party (decision 5).
3. The meaning of the three values of `target_status` in the new texts ("the limit that the project set before the check", "the share of labels that agreed with the reference labels") is read from the label schema (the description of the slot: a target set before the calibration) and from the earlier text. It was not checked against the reports of the project.
4. `contract/strings.contract.json` changed in this step (13 texts). The contract owner did not confirm the new texts.

### 10.4 The source tree, the hosted site and the third check (findings D-01 to D-13)

`EXAMINATION.md` chapter 10 has the row of each finding. Date of each run: 13.10.2026, one Mac, no container, no network, one run each.

What changed:

1. Server (`server/src/lib.rs`, `jobs.rs`, `main.rs`, `errors.rs`, `server/tests/api.rs`): the setting `PARLPDFECH_READONLY=1` (made before the third check) refuses with the new error code `read_only` (403) in place of `forbidden`; the new setting `PARLPDFECH_SAMPLE_RUNS` (`on` or `off`); `/api/health` has the keys `modes.read_only` and `modes.sample_runs`. `contract/errors.json` has 21 codes. `CONTRACT.md` chapters 2.1 and 14 (D-05, D-06).
2. Page (`ui/app.js`, `ui/index.html`, `ui/strings.json`): with `modes.read_only` the page shows no upload form, no stop button and no delete part, and the start page says that the site takes no file; with `modes.sample_runs` false a ready record has one link and no convert button. A number with one decimal has the number form of the page language (D-05, D-06, D-12).
3. Deploy kit: the Kaniko call has `--skip-unused-stages=true` (D-01; read in the Kaniko documentation, NOT RUN); the Traefik route sends `/api/jobs` to the pod with no buffering middleware (D-02; NOT RUN); `deployment.yaml` sets `PARLPDFECH_SAMPLE_RUNS=off`; `RUNBOOK.md` step 6 reads the health keys first and uses a record id that does not exist for the DELETE check (D-08); `deploy/README.md` says that the folder is not part of the source tree and must stay out of a public copy (D-10).
4. Tools: `container/check_dist.py` compares exact names (D-04); `worker/make_dist.py` refuses each folder with content and no `DIST-MANIFEST.json` (D-11).
5. Documents (D-09, D-03): `CONTRACT.md`, `README.md`, `worker/README.md`, `container/BUILD-NOTES.md`, `container/dist/DIST.md`, this file (chapters 1, 2, 6.2, 9, 10), `EXAMINATION.md`.

What was run after the changes:

| Check | Result | Values (measured) |
|---|---|---|
| `make test` | passed, exit code 0 | server 16 unit tests and 30 integration tests; rdfcheck 7 tests; the example view valid; `view/check_view.py` passed |
| `cargo clippy -p parlpdfech-server --all-targets -- -D warnings` | passed | no finding |
| `make native-server` | built | binary 2,944,544 bytes; 0 paths of this computer |
| `node ui/tools/check_ui.mjs` | passed, 0 errors | 435 keys of the page; the fixtures equal the contract examples (also `health.json` and `errors.json`) |
| An instance on `127.0.0.1:8897`, profile `native`, `PARLPDFECH_READONLY=1`, own work folder, real worker | as expected | `/api/health`: `read_only` true, `sample_runs` true, `upload` false. Upload of the synthetic `text_layer.pdf`: 403 `read_only`, `detail.note` `upload`, the text "This site shows the samples only. It takes no file and deletes no result.", 0 entries in the jobs folder. DELETE of the record id `u-0123456789abcdef` (does not exist): 403 `read_only`. A sample run: 202, the record was made. DELETE of that record: 403, then GET 200 |
| The same work folder, profile `slim`, `PARLPDFECH_READONLY=1`, `PARLPDFECH_SAMPLE_RUNS=off` | as expected | `/api/health`: `sample_runs` false, reason `profile_slim`. POST of a sample run for the ready record (JSON and form): 403 `read_only`, `detail.note` `sample_run`, 0 entries in the jobs folder. A start with the value `x`: the server stops with "PARLPDFECH_SAMPLE_RUNS is not on or off" |
| Browser (the built-in browser pane of the desktop app, a Chromium engine; one width; the values read from the page with a script, one picture of S1) | seen | Read-only instance: S0 line "This site shows sample documents. It takes no file. No account." and the mode line with no sentence about an own PDF (English, and German in the profile `slim`); S2 (German): the form is hidden, the text and the link to the samples show; S4 of `s-26171`: the delete part and the stop button are hidden; S1: the link "Open the result: ..." for the ready record. With sample runs off: the card of 26171 shows the link in place of the convert button for the ready mode, and the convert button for the mode with no record |
| The gate: an instance on `127.0.0.1:8897`, profile `native`, no setting, own empty work folder (`work/kitfix/work`), real worker; `make gate PORT=8897 GATE_OUT=work/kitfix/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0 | 100 rows: 97 passed, 0 not passed, 3 rows of information not met (G2 plain SHA-256, as before); 114 s. One sample through the server: 3.19 to 3.88 s. The upload record: 14 labels, 1,307 statements, 10.1 s. The row "health: key form of the example" passed with the 2 new keys |
| `make dist-src`, then `make -C dist-src check-dist` | made; passed | 184 files; 0 absent, 0 different, 0 not in the manifest |
| D-04: a scratch copy of the tree with added files | as expected | reported as not in the manifest: `worker/extra_file.py`, `ui/extra.js`, `.gitfoo`, `workfile.txt`, `target.txt`, `workshop/a.py` (exit code 1); not counted: files below `work/`, `target-ci/`, `.git/`, `worker/__pycache__/`, `ui/pkg/` |
| D-11: `make_dist.py --out` on scratch folders | as expected | a folder `dist-src` with one file and no manifest: refused, the file stayed; a made tree whose manifest was removed: refused; an empty folder, a folder with only `.git`, a made tree: made |

The third check also ran the gate on its own instance with the files before these changes (its report: 100 rows, 0 not passed, 56 s + 45 s); this closed the open point "`make gate` not run after the change of `worker/pdf_only.py`" of chapter 10.2.

Not run in this step: a container, Kaniko, the pipeline, a cluster, a proxy (each statement of `deploy/` about them is read or an estimate); `cargo clippy` and the build of the rdfcheck module (no source of it changed); `check_worker.py`, `check_fresh.py`, `check_wasm.mjs`; a second browser engine, the widths 320 and 800 px, a screen reader, the keyboard path of the new S2 text; the fixture mode of the page; the hygiene scan of chapter 6 (run in its place: a search of the changed tracked files for the name of the user account, a home path and the forbidden words: 0 hits); `make test` inside `dist-src/` after these changes.

Open after this step:

1. Texts of a public site. At the end of this step: the headline of S0 (`s0.title`: "On this computer."), the footer sentence "This page loads no file from another computer", the text `s4.delete.note` (hidden on such a site) and the text of the code `forbidden` (names `localhost`) are not true or not helpful on a public site. Changed in chapter 10.5: with `PARLPDFECH_HOSTED=1` the page shows other texts in these places. The contract texts themselves were not changed.
2. The contract owner did not confirm the code `read_only`, the 2 health keys and the 5 new page texts. The German texts were not read by a second party (decision 5).
3. `PARLPDFECH_SAMPLE_RUNS=off` protects the job slot only for a record that is ready. The server still has no limit of open connections and no time limit for the request header (chapter 4 point 8); a rate limit at the edge stays open (`deploy/RUNBOOK.md`).
4. D-01 and D-02 are changes of files that never ran. D-03 is decision 1 of chapter 9. D-07 (the network policy uses `namespaceSelector`) is not changed.
5. Closed in chapter 10.5: `ui/README.md` describes the page of a read-only site and gives the key counts of now.

### 10.5 One site, the texts of a hosted site and the fourth check (findings E-01 to E-07)

`EXAMINATION.md` chapter 11 has the row of each finding. `CONTRACT.md` chapter 15 has the rules. Date of each run: 13.10.2026, one Mac, no container, no network, one run each. The static site of the runs is the folder `web/dist` of the project (27 files; built outside the package and only read by this step).

What changed:

1. Server (`server/src/lib.rs`, `statics.rs`, `jobs.rs`, `main.rs`, `errors.rs`, `server/tests/api.rs`). The static site below `/` is a supported part: its own `Content-Security-Policy` (one script file, one style sheet, pictures and data requests of this server; no WebAssembly, no font, no form), the page `404.html` of the site with the status 404, the media types `application/yaml` and `text/plain` for the list `SHA256SUMS`, and a site folder with no `index.html` is dropped at the start. `/api/health` has the keys `site` and `hosted`. New setting `PARLPDFECH_HOSTED` (`0` or `1`). New error code `sample_runs_off` (E-02); `contract/errors.json` has 22 codes.
2. Page (`ui/app.js`, `ui/index.html`, `ui/strings.json`, `ui/tools/check_ui.mjs`). The page asks `/api/health` before its first text. With `site` true the navigation has the link "About this project" / «Über das Projekt» to `/` (`/de/` in German). With `modes.read_only` no entry promises an upload (E-01): the second way of the start page and the navigation entry name the run on the own computer, and the screen behind them says how. With `hosted` true the page takes the texts with the ending `.hosted` (20 keys) and its own texts for the codes `forbidden` and `internal`. 463 keys.
3. Tools and build files. `make dist-src SITE_DIR=<folder>` and `worker/make_dist.py --site` copy a built site to `site/` of the tree; the Dockerfile of such a tree has `COPY site/ /app/site/`; each image sets `PARLPDFECH_SITE_DIR=/app/site`; `make run-native SITE_DIR=<folder>` (package and tree); `deploy/k8s/deployment.yaml` sets `PARLPDFECH_SITE_DIR` and `PARLPDFECH_HOSTED=1`. `container/check_dist.py` (E-05): the build folders are the exact names `target`, `target-server` and `target-wasm`; in a folder `__pycache__` only a file `*.pyc` is not counted.
4. Documents (E-03): `README.md` (binary size, the part on the site and the settings), `server/README.md`, `CONTRACT.md` (chapters 2.1, 2.2, 5.1, 5.2, 5.4, 7.1, 7.3, 11.1 point 3, 14 and the new chapter 15), `ui/README.md`, `container/BUILD-NOTES.md`, `container/dist/DIST.md`, `deploy/README.md`, `deploy/RUNBOOK.md`, this file, `EXAMINATION.md`.

The rule for `hosted`: the value is true if and only if the operator set `PARLPDFECH_HOSTED=1`. The other rule that was considered (true if the profile is `slim` and the server is read-only) is a guess: the container of `make run` with the read-only setting runs on the computer of the reader, and the trial instance of this step (profile `native`, read-only) would get the local texts on a hosted computer.

What was run after the changes:

| Check | Result | Values (measured) |
|---|---|---|
| `make test` | passed, exit code 0 | server 16 unit tests and 32 integration tests (2 new tests for the site, 1 changed, the test of the sample runs has a new part); rdfcheck 7 tests; the example view valid; `view/check_view.py` passed |
| `cargo clippy -p parlpdfech-server --all-targets -- -D warnings` | passed | no finding |
| `make native-server` | built | binary 2,961,168 bytes; 0 paths of this computer |
| `node ui/tools/check_ui.mjs` | passed, 0 errors | 463 keys of the page, 20 of them with the ending `.hosted`; 83 keys of the panel; the fixtures equal the contract files (also `health.json` and `errors.json`); 5 notes for contract keys that the page does not use |
| An instance on `127.0.0.1:8897`, profile `native`, `PARLPDFECH_SITE_DIR` = the site folder, no other setting | as expected | `/api/health`: `site` true, `hosted` false. Each of the 27 files of the site: 200, the bytes of the folder, media types `text/html`, `text/css`, `text/javascript`, `application/json`, `image/svg+xml`, `text/plain` (each with `charset=utf-8`) and `application/yaml` (9 files). `/`, `/de/`, `/numbers/`, `/de/numbers/`, `/about/`, `/de/about/`, `/id/`: 200. `/de`, `/about`, `/numbers`, `/id`: 307 to the address with the slash. `/nope`, `/de/nope`, `/static/`, `/data/`: 404 with the 404 page of the site. `/app/`, `/app/?lang=de`, `/app/app.js`, the WebAssembly file, `/healthz`, `/api/samples`: 200; `/app`: 308. The headers of `/`: the 6 headers of the contract, the policy of the site, `Cache-Control: no-cache`, `Last-Modified`; a request with `If-Modified-Since`: 304. The headers of `/app/`: the policy of the app. A foreign `Host` on `/` and on `/app/`: 403. POST, PUT and DELETE of `/`: 405 |
| The same work folder, no site | as expected | `site` false; `/` gives 307 to `/app/`, `/?lang=de` to `/app/?lang=de`; `/de/` and `/static/site.css`: 404 |
| `PARLPDFECH_SITE_DIR` = a folder that does not exist | as expected | one warning line in the log; `site` false; `/` redirects |
| `PARLPDFECH_SAMPLE_RUNS=off`, no read-only setting, 2 ready records (E-02) | as expected | `/api/health`: `sample_runs` false, `read_only` false, `upload` true. POST of a sample run for the ready record: 403 `sample_runs_off`, detail `record_id`, text "The result of this sample is ready. This server starts no new run for it." |
| `PARLPDFECH_HOSTED=x` | the server stops | "PARLPDFECH_HOSTED is not 0 or 1" |
| An instance with the site, `PARLPDFECH_READONLY=1`, `PARLPDFECH_SAMPLE_RUNS=off`, `PARLPDFECH_HOSTED=1` | as expected | `/api/health`: `read_only` true, `sample_runs` false, `site` true, `hosted` true. DELETE of `/`, `/de/` and `/app/`: 403; GET `/`: 200 |
| Browser (the built-in browser pane of the desktop app, a Chromium engine; one width; the values read from the page with a script) | seen | With the site and no setting: the navigation shows "About this project" with the address `/` (English) and «Über das Projekt» with `/de/` (German). The pages `/`, `/de/` and the 404 page have their style sheet (363 rules) and their script; a data file of the start page loads (200, `application/yaml`); the console has no message about a refused file (1 message: the status 404 of the address that was asked for the 404 page). With no site: `/` opens the app, the link is hidden. The hosted read-only instance, English and German, S0, S1, S2, S4 of `s-26171` and `s-26171-rules`: 0 visible texts with "this computer", `localhost`, "stays on", "another computer"; S0 headline "... Samples on this site.", the second way "Run it on your computer" / «Auf Ihrem Computer starten», navigation "On your computer"; S2 headline "Convert your own PDF on your computer", no form, the links to the samples and to `/de/`; S1 lead with "no new run starts for it" and the comparison line "on this site" |
| The gate: an instance on `127.0.0.1:8897`, profile `native`, no setting, own empty work folder (`work/site/work`), real worker, the binary of this chapter; `make gate PORT=8897 GATE_OUT=work/site/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0 | 100 rows: 97 passed, 0 not passed, 3 rows of information not met (G2 plain SHA-256, as before); 120 s. The row "health: key form of the example" passed with the keys `site` and `hosted` |
| `make dist-src DIST_OUT=<scratch>` with no `SITE_DIR`, then `make check-dist` in the tree | made; passed | 184 files; no folder `site/`; the Dockerfile has no `COPY site/` line; 0 absent, 0 different, 0 not in the manifest |
| The same with `SITE_DIR` = the site folder | made; passed | 211 files (27 below `site/`, 999,316 bytes; equal to the site folder); the Dockerfile has the line `COPY site/ /app/site/`; `make check-dist`: 0 absent, 0 different, 0 not in the manifest; `make_dist.py --check` with and without `--site`: 0 rows different |
| E-05: a scratch copy of the tree with added files | as expected, exit code 1 | counted: `layout/__pycache__/x.py`, `worker/__pycache__/note.txt`, `targeted-x/run.py`, `target-ci/a`, `target.txt`, `workshop/a.py`, `site/extra/new.html`; a changed `site/index.html` is reported as different; not counted: files below `target/`, `target-server/`, `target-wasm/`, `work/`, `.git/`, `ui/pkg/` and `worker/__pycache__/a.cpython-312.pyc` |
| Site folders that the tool refuses | refused, no tree written | a folder with no `index.html`; a folder with a dot file, a symbolic link and a file below `app/`; a folder with a file that holds a path of the home folder; a site folder inside the tree folder |
| Hygiene search of the 30 changed tracked files (the 27 files of the first search, then `server/README.md`, this file and `EXAMINATION.md`; name of the user account, home path, family name, first name, the 2 forbidden words, sharp s, private address patterns, 2 key patterns) | 0 hits | except the letter sharp s in 2 lines of `ui/tools/check_ui.mjs` that search for it |

Not run in this step: a container, Kaniko, the pipeline, a cluster, a proxy (the Dockerfile lines for the site, `deployment.yaml` and each statement of `deploy/` are written and read); an image or a `make run-native` of a tree with a site (only the command line of `make -n run-native` was read: it sets `PARLPDFECH_SITE_DIR`); the profile `slim` with the new settings; a hosted instance with no read-only setting in a browser (8 texts with the ending `.hosted` were read in the strings file only: `s0.line`, `s0.upload.note`, `s2.sending`, `mode.upload.yes`, `s4.delete`, `s4.delete.note`, `s4.headline.new`, `s3.time`); the case screens with the texts `err.hosted.*` and `case.network.*.hosted`; a second browser engine, the widths 320 and 800 px, a screen reader, the keyboard path of the new entries; the fixture mode; a file of the site with no extension other than `SHA256SUMS`; `cargo clippy` and the build of the rdfcheck module (no source of it changed); `check_worker.py`, `check_fresh.py`, `check_wasm.mjs`; `make test` inside a tree; the hygiene scan of chapter 6; the gate against an instance with a site or with a setting. The stop list of the preview site was applied to the page strings by `check_ui.mjs`, not to the 3 texts of the new error code.

Open after this step:

1. The contract owner did not confirm: the setting `PARLPDFECH_HOSTED`, the health keys `site` and `hosted`, the code `sample_runs_off`, the 29 new page keys and the changed text `s2.read_only`. The German texts were not read by a second party (decision 5). The new German texts say «Website» for the site; the German text of the code `read_only` still says «Diese Seite».
2. The error object of the API keeps the local texts of the codes `forbidden` ("on this computer", `localhost`) and `internal` ("start the package again") on a hosted server; only the page has other texts.
3. The text for an own PDF on a site that takes no file names the file `README.md` in the source of the package. `README.md` has the chapters "Start with no container" and "Start with a container (NOT YET RUN)"; it has no chapter with the name "Run it on your computer". The page gives no address of a source repository: the package holds none (hygiene rule). If the server has a static site, the page links to it.
4. The site folder is not part of the package. Its pages name the owner and the public repository (read: the pages of `web/dist`); `make dist-src SITE_DIR=...` copies them as they are, and the image then publishes them. The tool refuses only a path of a home folder, a dot file, a link and a PDF file.
5. The static pages do not yet link to the app; the site agent adds the links (`/app/`, `/app/?lang=de`, `/app/#/record/s-<document number>`; `CONTRACT.md` chapter 15 point 1). The site of the runs has no page `how1` to `how4`; it has the pages `/`, `/numbers/`, `/about/`, `/id/`, the German pages of the first three and `404.html`, with no German 404 page.
6. E-04 stays: D-01 and D-02 are changes of files that never ran. The pipeline of the tree uses the build folder `target-ci`; `check_dist.py` now counts a file in it. The job `tree` of the pipeline runs the check with no cache, so the folder is absent there (read, not run).
7. The folder `dist-src/` of the package was made again with no `SITE_DIR` at the end of this step (184 files). A tree with the site must be made after the site agent built the final pages.

## 11 The record with head values that are read from the PDF (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more.

### 11.1 What changed

| Part | Change |
|---|---|
| Goal | A PDF goes in and an eCH-0295 record comes out, read from the PDF. Before this step each head value came from the OpenParlData export, and a PDF with no export record got a container with no affair. |
| Worker | New file `worker/values_record.py`. `worker/serve_convert.py` (a sample) and `worker/fresh.py` (another PDF) call it after the block decisions. It calls the value readers, `m11_writer` and `m11_validate` of the code layout. |
| Value readers | Code rules with tiers for 7 fields: affair type, title, affair number, submission date, response date, responder, first author. They get the block file and the rule file only. |
| Export record | The cross-check only. No value of the eCH-0295 part comes from it. A PDF with no export record has no cross-check. |
| Absent value | The slot is absent. The manifest gives it the state `not_found_in_pdf`. An absent type or number is a recorded gap (`conformance` `i95_with_recorded_gaps`). |
| Block labels | Not changed. Measured for sample 879163: the labels of the blocks, of the boundaries and of the document are equal in the two record forms. The count is 25 labels in the mode `rules` and 26 in the mode `auto`. |
| Switch | `PARLPDFECH_VALUES=off` gives the earlier record form. |
| Hold list | `worker/values_hold.json` names the samples 26171 and 714840. They keep the earlier record form, and no value reader runs on them. |
| Code layout | 83 files (before: 72): the 10 files of the values and the stand-in calibration file. New tool `worker/layout_add.py`. |
| View | Version `parlpdfech-site-view/3`: the new keys `head_values`, `values[]` and `slots[]`. 2 new example views in `contract/examples/`. |
| Page | The result page starts with the part "The eCH-0295 record": 3 tables with 4 slot states. A sample has the column "OpenParlData". The button "Show on the page" draws a frame around the span. The block cards have the heading "The text parts". |
| Texts | 604 string keys of the page (before: 463). 10 texts changed (11.4). 1 text of the RDF panel changed. |
| Contract | New chapter 16 in `CONTRACT.md`. |
| Checks | New tools `worker/check_values.py` and `contract/tools/gate_values.py`. The earlier tools `worker/check_worker.py`, `worker/check_fresh.py` and `contract/tools/gate_compare.py` set the switch to off for their worker runs. |

No file of the server changed. The server binary is the binary of chapter 10.5.

### 11.2 What an unknown PDF gets now

1. One affair with a minted IRI below `urn:parlpdfech:local:sha256:<hash>/record`.
2. Each of the 7 values that the PDF prints and a rule accepts. Each value has its wording, page, span, rule tier and a label of the kind `pdf_value`.
3. The submission and the response step with their text blocks, if the PDF has them.
4. A recorded gap for an absent type or number. No invented value.
5. The manifest with one of 4 states for each of the 52 slots of the affair and of its two steps.
6. No comparison with a register: each value has the result `not_compared`.

The values are proposals of code rules. A rule can read a wrong value. 21 of the 52 slots have no rule (reason `no_rule_searched`).

### 11.3 The probabilities of the values are not measured in the package

This chapter is the state before chapter 12. It does not apply any more: the package uses the measured calibration file, and the layout holds no stand-in file.

1. The measured calibration file `daten/gj_values/calibration_values_dev.json` did not exist at the end of this step. The code layout holds the stand-in file. Its numbers are synthetic.
2. Thus each record of this step has `synthetic_values` true in `manifest.json`, and `convert.json` has `values.calibration.measured` false.
3. The view gives no number for a value (`probability` null, `value_status` `none`, `measured` false), and no count of a stand-in calibration record. The page says "not yet measured" (notice `values_not_measured`).
4. Limit: the 3 YAML files and the 4 RDF files of a result hold the stand-in numbers. They are in the labels of the kind `pdf_value` (for example in `<prefix>.labels.yaml`). The RDF panel of the page reads the TriG file, so a query in the panel can show such a number. The first comment line of the eCH-0295 YAML file says that the values are synthetic.
5. When the measured file exists: run `python package/worker/layout_add.py --values` and `make layout` from the project folder. The worker then uses the measured file, and the view gives the numbers. This path was not run with a measured file. One unit check covers the choice of the file.
6. The probability of a value will then be the measured precision of its rule tier on development documents, with the OpenParlData export as the reference. It is not a check by a human.

### 11.4 Texts that changed (each one said that head values come from the export, or it named the labels)

| Key | Change |
|---|---|
| `notice.no_export` (contract key) | before: the record has no number, title or date, and these values come from the export. Now: the text of the earlier record form of a PDF with no export record. |
| `about.p2` | the words "Values from the export" are removed. |
| `about.p5` | before: the number, the title and the dates come from the export. Now: code rules read the 7 values from the PDF, and the export is used only to check the values of a sample. |
| `words.export` | before: these values are not read from the PDF. Now: the package uses the export only to check the values that it reads from the PDF. |
| `words.probability` | one more sentence for a value that is read from the PDF. |
| `s4.labels.title` | "The labels" is now "The text parts". |
| `s4.head.title`, `s4.head.lead` | "Values of the eCH-0295 record" is now "Each value of the record with its source". |
| `s4.marked.start`, `s0.sample.note` | they name the values of the record. |
| `rdf.examples.no_head` (RDF panel) | before: the record has no head values, because it has no export. Now: the example query needs a record of the earlier form. |

New texts: `s0.values` on the start page, the words `words.value` and `words.states`, and the 6 notices of `CONTRACT.md` chapter 16.3. Also new: the texts of the record tables, 52 slot names and 9 check names. The texts for the export in the earlier record form stay (`source.export`, `origin.export`, `kind.export_value`, `group.export`, `note.value_derivation.*`, `unc.basis.no_export`): the page uses them for the earlier form only, or for the rule of the document label.

### 11.5 What was run (13.10.2026, one Mac, no container, no network)

| Check | Result | Values (measured) |
|---|---|---|
| `worker/layout.py --update`, then `--check` | passed | 83 files, 0 different; 51 compiled files |
| `worker/check_values.py` (run 3 times; the last run after the last change of a rule module) | passed, exit code 0 | 76 of 76 checks. Sample 879163 in the modes `rules` and `auto`; the same with the switch off; a trace of one run (1,905 paths, 0 paths of the project folders, 0 child processes, 1 bind to a loopback address); 3 synthetic PDF files |
| An instance on `127.0.0.1:8897`, profile `native`, values path on, own empty work folder, real worker; `contract/tools/gate_values.py --port 8897` | passed, exit code 0 | 36 of 36 rows, 5 records (table below) |
| The same port, an instance with `PARLPDFECH_VALUES=off` and an empty work folder; `make gate PORT=8897 GATE_OUT=work/values/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0 | 101 rows (100 of chapter 10.5 and 1 new row for the switch): 98 passed, 0 not passed, 3 rows of information not met (G2 plain SHA-256, as before) |
| `make test` | passed, exit code 0 | server 16 unit tests and 32 integration tests; rdfcheck 7 tests; the example view of the earlier form valid; `view/check_view.py` passed with one new check (the 3 example views are valid) |
| `worker/check_worker.py --reference-dir <reference run>` (switch off; no `--sample-pdf`) | passed | 79 of 79 checks |
| `node ui/tools/check_ui.mjs` | passed, 0 errors | 604 keys of the page, 20 with the ending `.hosted`; 5 notes for contract keys that the page does not use |
| `contract/tools/validate_view.py` on the 3 example views | valid | |
| Document checker on `CONTRACT.md` chapter 16 | 0 findings in the chapter | the earlier chapters keep their findings (73 in the file) |

Records of the instance with the values path on (one run each; time from the worker):

| Record | Input | Seconds | Values read | Recorded gaps | Statements (eCH-0295 graph / all) | Cross-check |
|---|---|---|---|---|---|---|
| `s-879163` | sample, mode `auto` | 3.91 | type, title, responder | affair number | 27 / 3,220 | equal, equal, no value there |
| `s-879163-rules` | sample, mode `rules` | 3.85 | type, title, responder | affair number | 42 / 3,762 | equal, equal, no value there |
| `u-e8e084e6e7c3509f` | synthetic `text_layer.pdf` | 10.28 | type, title, submission date, responder | affair number | 30 / 1,940 | not compared |
| `u-63f3760eee56ccc3` | synthetic `with_values.pdf` | 9.49 | number, type, title, 2 dates, responder | none (`i95`) | 32 / 1,900 | not compared |
| `u-f8d9883cc85ca167` | synthetic `no_type.pdf` | 9.59 | title | affair type, affair number | 15 / 893 | not compared |

Each of the 5 records: `valid` true; 18 checks passed and C10 skipped; the 10 files of `convert.json` served with the bytes of their SHA-256; `bundle.zip` with 12 entries and 11 correct `SHA256SUMS` lines; no register address in the eCH-0295 files. The cross-check column is the result of one record. No tool counted results over a set of documents.

Browser (the built-in browser pane of the desktop app, a Chromium engine; values read from the page with a script, and 4 screenshots):

| Page | Seen |
|---|---|
| `s-879163`, English, 1280 px | The part "The eCH-0295 record" is the first part after the head line. The line "These values were read from the PDF. The OpenParlData export is used only to check them." The line "not yet measured". The gap text names the affair number. 3 tables with the columns Entry, State and value, Probability, OpenParlData. Type: the wording `POSTULAT` as printed, "Value in the record: Postulate", equal. Title: equal, with the wording of OpenParlData below. Affair number: not found in the PDF, "OpenParlData has a value. The record does not take it." |
| "Show on the page" of the title | 1 line has the mark, and a frame is around the title in the line. The row of the table has the mark. The address ends with `/label/pdf-title`. |
| `s-879163`, German | the same content with the German texts; the 8 notices have their texts. |
| `u-63f3760eee56ccc3`, English and German | the line for a PDF with no OpenParlData record; no column "OpenParlData"; 6 values; "3. Mai 2021" with "Value in the record: 2021-05-03"; "Stadtrates" with the record value "Stadtrat"; the button marks the line of the submission date. |
| `s-879163`, 375 px | the tables are stacked; no horizontal scroll of the page. |
| Start page, English | the new line about the values; the changed text `about.p5`; the 2 new words at the top of the list. |
| `s-879163` on the instance with the switch off | the part "The eCH-0295 record" is hidden; the notice `head_from_export` shows; 20 head values with their source. |

Not run in this step: the samples 26171 and 714840 with the values path (hold list; a record of them was not made and not read); a record with the measured calibration file; `worker/check_fresh.py` (it needs the 3 sample PDF files); the check `P` of `check_worker.py` (it needs the PDF of sample 26171); `rdfcheck/tools/check_wasm.mjs` on a record of the new form; a build of the server or of the bundle; `make dist-src`; a container; Firefox, Safari, a screen reader, the keyboard path through the new tables; a PDF of a parliament that is not a sample.

### 11.6 Stubs and limits of this step

The items 1, 2, 6 and 11 are the state before chapter 12. Chapter 12 replaces them.

1. The stand-in calibration file (11.3). It is in the code layout until the measured file is added.
2. Hold list `worker/values_hold.json` (2 samples). It is a hold, not a result. To end it, set its key `hold` to an empty list. The file `daten/gj_values/opening.json` of the project existed at the end of this step; this step did not remove the hold.
3. The code layout pins the SHA-256 of each file. The 4 rule modules changed during this step (another work step of the project). The layout holds their state of 14:26 on 13.10.2026. After each later change of an `m11` file: `python package/worker/layout_add.py --values`, `make layout`, then `python package/worker/check_values.py`. If a file of the list differs from the project file, `make layout` stops with exit code 1.
4. `worker/make_layout_list.py` does not know the files of the values (they are not in its trace files). A new run of that tool drops them from the list; `layout_add.py --values` adds them again.
5. The gate of chapter 3 (`make gate`) is the gate of the earlier record form. On a server with the values path on, its rows for sample 879163 and for the upload record do not pass. The new row "the server of this gate runs with PARLPDFECH_VALUES=off" then says why.
6. `rdfcheck/tools/check_wasm.mjs` and the RDF panel know the conformance name `pdf_only_with_recorded_gaps` of the earlier form. For a record of the new form the panel hides the example query for the head values. The page gives it the same flag as for a record with no export. The Rust module was not changed. It was not run on a record of the new form outside the browser. In the browser the panel was not examined for the new form: only the page above it was read.
7. The view of a record of the new form passes no text of a value calibration record on (`calibrations[].note` null).
8. The slot states of the 21 slots with no rule have the state `not_found_in_pdf` with the reason `no_rule_searched`. A state of their own is a decision of the owner (record form, chapter 11).
9. The first author has the result `not_compared` in each record: the export records of the package have no contributor rows.
10. `Dockerfile`, `Makefile`, `container/` and `deploy/` were not changed. The image copies `worker/` and the layout as before; the new files were not run in an image. `worker/make_dist.py` leaves the 3 new project tools out of the source tree; the tree was not made again.
11. `EXAMINATION.md` was not changed. No examiner read the code of this step.

## 12 Corrections after the skeptic check of the values (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network.

A skeptic examined the work of chapter 11 (the record form, the writer, the validator, the package). Its findings and the decisions are in `EXAMINATION.md` chapter 12. The writer and the validator of the project were corrected first (`src/m11_writer.py` version `m11-writer-2`, `src/m11_validate.py` version `m11-validate-2`). This chapter is the package step.

### 12.1 What an unknown PDF gets

1. One eCH-0295 record with one affair, the two steps with their text blocks, the value labels and the manifest with the state of each of the 52 slots.
2. Code rules search 7 fields in the text of the PDF: the affair type, the title, the affair number, the submission date, the response date, the responder and the first author.
3. A value of the record is what the PDF prints at a recorded page and span: a name, a title or a number on one line; the list value of the printed type word; the calendar day of the printed date. The validator makes each value again from the wording (check C20).
4. Each value has a probability (stored decimal) and the word certain or unsure.
5. A value of a rule tier with a stored probability below 0.5 is not written. It is a weak candidate in the label file, and the page shows it as such.
6. A field for which the rules find no value is absent, with a reason. An absent affair type or affair number is a recorded gap (conformance `i95_with_recorded_gaps`).
7. No value comes from a register. An unknown PDF has no comparison with OpenParlData.
8. REPLACED (chapter 13). Earlier text: The first author is written only for a document with a submitted text (block labels).
9. No human checked a value. A rule can read a wrong value, and it can find no value where the PDF prints one.

### 12.2 Where the probabilities come from

REPLACED (chapter 13). Earlier text: The probabilities come from the development documents of the open part: 1,486 documents of 36 parliaments (`daten/gj_values/calibration_open.json` of the project). The project record `daten/gj_values/closed_table.md` gives the values on 8 parliaments that the authors of the rules did not read (307 documents). There the share of equal values was lower than the stated probability for two fields: affair number (94 values, mean stated probability 0.856, share equal 0.606) and submission date (126 values, 0.639 and 0.460). For the affair type, the title, the responder and the first author the difference was between -0.013 and +0.011. For the response date it was +0.085 with 19 values. That measurement was made before the floor: its counts include values of rule tiers that the package does not write now.

1. The reference is the OpenParlData export: a register value that no person of the project examined. It is not in each case the value that the PDF prints.
2. A probability is the Jeffreys mean (k + 0.5) / (n + 1) of the pair of field and rule tier, with the limits 0.005 and 0.995. The page shows k and n ("equal in k of n development documents").
3. The word certain needs a threshold of the field and a tier with 30 or more documents. Only the affair type and the responder have a threshold (0.6). Each value of the 5 other fields is unsure.
4. REPLACED (chapter 13). Earlier text: A sample of the open part (879163) gets the number without its own group of parliaments. Its affair type has 0.2143 in the label; the number of the tier from all development documents is 0.6071. The floor uses 0.6071, so the value is written. The page shows the two numbers. The writer report asks the main agent to confirm this rule.
5. REPLACED (chapter 13). Earlier text: The samples 26171 and 714840 are of a parliament of the closed part (`BS`). They are not in the calibration file, so they get the numbers from all development documents.
6. The calibration file was not released by a person. The status of the file is EXCEPTION, NOT RELEASED.

### 12.3 What changed in the package

| Part | Change |
|---|---|
| Layout | `worker/layout_add.py --values` puts `daten/gj_values/calibration_open.json` and the `m11` files of now into `worker/layout_files.json` and removes the stand-in file. `make layout`: 83 files, 0 different, 51 compiled files. The layout holds no stand-in file. |
| Worker | `worker/values_record.py` 0.2.0: the measured file or a stop; 19 check ids (C1 to C9, C11 to C21); `convert.json` keys `values.floor` and `values.author_rule`. `worker/values_hold.json` has an empty list. |
| View | `view/site_view.py`: the weak candidates, the new keys of `CONTRACT.md` chapter 17.4, the notice `weak_candidates`; no view for a record with stand-in numbers. `contract/view.schema.json` and `contract/tools/validate_view.py` follow. |
| Page | `ui/app.js`, `ui/strings.json` (639 keys), `ui/app.css`: the row texts of `CONTRACT.md` chapter 17.5. |
| RDF panel | The example query for the head values shows for each record with values from the PDF. The Rust module did not change; the WebAssembly bundle was not built again. |
| Check tools | `worker/check_values.py`, `contract/tools/gate_values.py`, `rdfcheck/tools/check_wasm.mjs`, 2 more synthetic PDF files in `worker/check_fresh.py`, 4 more lines in the target `test` of the `Makefile`. |
| Examples | `contract/examples/view_879163.json`, `view_unknown_pdf.json` (now the file `head_author.pdf`) and the new `view_26171_values.json` are views of the instance of 12.5. `view_26171.json` (earlier form) and its fixture copy got the 3 new keys of `head_values` with the value null. |

### 12.4 The 3 samples (mode `rules`; the head values are the same in the mode `auto`)

| Sample | Written values (printed wording, value of the record, stored decimal, word, comparison) | Not written | States of the other fields |
|---|---|---|---|
| 26171 | type: `Interpellation`, `interpellation`, 0.9688, certain, equal. Title: `der OECD-Steuerreform und den Folgen für den Kanton Basel-Stadt` (printed on 2 lines), 0.7878, unsure, equal by the comparison rule. First author: `Patricia von Falkenstein`, 0.9458, unsure, not compared. Responder: `Regierungsrat`, 0.8333, unsure, equal by the comparison rule. | affair number: weak candidate `121` (tier `number_type_cue`, 0.3909; equal in 21 of 54 development documents) | submission date: not found. Response date: not searched in this kind of document (`proposal`). Gap: affair number. |
| 714840 | type: `Regierungsratsbeschluss`, `draft_decree`, 0.9397, unsure, equal. | title: weak candidate `Swisslos-Fondsbeitrag; Verein MusikRaumBasel; Festival KlangBasel 2014 P140393` (tier `weak_first_heading`, 0.1651; 17 of 105) | affair number, submission date, responder: not found. First author, response date: not searched (kind `other`). Gap: affair number. |
| 879163 | type: `POSTULAT`, `postulate`, 0.2143 (tier 0.6071), unsure, equal. Title: `Fonds d'aide au maintien des petits commerces et cafés du villages`, 0.7874, unsure, equal by the comparison rule (OpenParlData has `... dans les villages`). Responder: `Conseil municipal`, 0.9921, certain, no value in OpenParlData. | none | affair number, submission date, response date: not found. First author: not searched (the block labels give no submitted text; the PDF prints the authors in its head). Gap: affair number. |

1. Each of the 3 samples has a recorded gap for the affair number.
2. Sample 26171: the export number `19.5497` stands in a text block of the record in the mode `rules`, because the PDF prints it in its text. The rules did not read it as the affair number. No head slot holds it.
3. In the mode `auto` the text blocks differ from the mode `rules` (block labels from the stored Apertus states). Sample 714840 has a submitted text in the mode `rules` and no text block in the mode `auto`.

### 12.5 What was run (13.10.2026, after the last code change if the row does not say more)

| Check | Result | Values |
|---|---|---|
| `python3 package/worker/layout_add.py --values`, `make -C package layout`, `python package/worker/layout.py --check` | passed | list written (1 file added, 2 changed, 1 removed); 83 files copied, 0 different; check: 0 different, 51 compiled |
| `python package/worker/check_values.py --work package/work/valuesfix/check_values` | exit code 0 | 193 of 193 checks: 4 unit checks; 3 samples in 2 modes, each also with the switch off; 1 trace run; 5 synthetic PDF files |
| An instance on `127.0.0.1:8897`, profile `native`, the values path on, empty work folder `work/valuesfix/work`; `python package/contract/tools/gate_values.py --port 8897 --out package/work/valuesfix/gate_values` | exit code 0 | 85 of 85 rows, 11 records: 6 sample records and 5 uploads. Each record: job done and valid; view valid against the schema with the link checks; 21 checks passed or C10 skipped; 10 files with their SHA-256; `bundle.zip` with 11 correct lines of `SHA256SUMS`; the truth row. For the 6 sample records the validator of the project ran again in its own process on a copy of the served files: passed, C1 to C21 (C10 skipped). For the 5 uploads the validator result is the run of the worker (`validation.json`): the server keeps no block file |
| An instance on `127.0.0.1:8897` with `PARLPDFECH_VALUES=off`, empty work folder `work/valuesfix/work_off2`; `make -C package gate PORT=8897 GATE_OUT=work/valuesfix/gate2 GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0 | 101 rows: 98 passed, 0 not passed, 3 rows of information not met (G2 plain SHA-256, as before). A first run (before the example `view_26171.json` got the 3 new keys) had 1 row not passed: the view of `s-26171` against the example |
| `make -C package test` | exit code 0 | server 16 unit tests and 32 integration tests; rdfcheck 7 tests; 4 example views valid; layout check; `check_ui.mjs`; `check_view.py` |
| `node ui/tools/check_ui.mjs` | PASSED, 0 errors | 639 keys |
| `python package/worker/check_worker.py --reference-dir daten/gj/fullrun_b1s_dev --sample-pdf daten/pdf/lehrer_stichprobe/26171.pdf` (it sets the switch off) | exit code 0 | 82 of 82 checks, 62 s; check P ran for the first time with the PDF of 26171 |
| `python package/worker/check_fresh.py --pdf-dir daten/pdf/lehrer_stichprobe` (it sets the switch off) | exit code 0 | each of the 7 runs with an expectation ended as expected. A first run gave exit code 1: a second copy of the script ran at the same time in the same work folder (an error of this step, not of the script) |
| `node rdfcheck/tools/check_wasm.mjs` on the 11 records of the instance (served files) and on 2 records of the earlier form | ALL CHECKS PASSED, each call | the example `ech_head` gives 1 to 18 rows for each record with values from the PDF; one affair; no register address in the eCH-0295 graph; 0 statements for the slot of each gap and each weak candidate; counts equal to the manifest |
| The 6 files of the opening | equal | SHA-256 of each file = `daten/gj_values/opening.json` |

Which checks run with `PARLPDFECH_VALUES=off`, and why: `make gate`, `worker/check_worker.py` and `worker/check_fresh.py`. They compare records with the reference run of the earlier record form (SHA-256 of files, label counts, the example view of 26171). A record with values from the PDF has other files and other labels of the kind value, so these comparisons do not apply to it. `check_values.py` and `gate_values.py` check the record form of now.

### 12.6 The page in a browser

Read in the built-in browser pane of the desktop app (Chromium), instance of 12.5 with the values path on. Pages: `s-26171` and `s-26171-rules`, `s-714840`, `s-879163` and the upload of `head_author.pdf`, each one in English and in German (`s-26171-rules` in English only). Each value row of the 3 tables was read as text.

1. Each written value shows the stored word and the stored decimal, then "equal in k of n development documents" (for example "certain · 0.9688", "equal in 666 of 687 development documents").
2. A list value shows "printed: Interpellation; in the record: interpellation (Interpellation)" and the sentence of the rule. A date shows "printed: 12. Juni 2023; in the record: 2023-06-12". The title of 26171 shows the printed wording on 2 lines and the value on one line.
3. A name shows as printed: "Patricia von Falkenstein", "Regula Beispielmann", "Conseil municipal".
4. The weak candidates show as "Weak candidate, not in the record: 121" (26171) and the heading of 714840, with "unsure · 0.3909", "equal in 21 of 54 development documents", "below 0.5: not written to the record". German: "Schwacher Kandidat, nicht im Datensatz: 121", "unter 0.5: nicht in den Datensatz geschrieben".
5. The title of 879163 shows "equal by the comparison rule" / "nach der Vergleichsregel gleich", the string of OpenParlData and the rule.
6. 879163 shows for each value the line that its number leaves out the group of parliaments of the document, with the number from all development documents.
7. The gap line says "In this PDF the rules found no value that they write to the record for: Affair number."
8. The state reads "Not searched in this kind of document" / "In dieser Dokumentart nicht gesucht" with the kind of the document, or with the rule of the submitted text for the first author.
9. The upload has no column OpenParlData and the lead "No OpenParlData record exists for this PDF: the values are not compared." Its conformance line says that the record has each required entry.
10. No page of the 5 records has the notice `head_from_export`. The RDF panel lists 5 example queries, the head query included.
11. An error of this step was found in the browser and corrected: a variable name stayed in `ui/app.js` after an edit, and the page showed "The answer of the server has an unknown form". After the correction each page has the title "Result" / "Ergebnis".

Not done in the browser: a click on "Show on the page" for a weak candidate; the list "Other entries" (the words "Made by the converter"); a run of the head query in the panel; the upload pages other than `head_author.pdf`; a small screen; the keyboard path; Firefox, Safari, a screen reader. The console has 404 lines that this step did not trace (as in chapter 11).

### 12.7 Limits and open points

1. The probabilities are lower on parliaments that the rule authors did not read for the affair number and the submission date (12.2). The page says so in one notice.
2. The floor rule for a development document (12.2 item 4) needs the confirmation of the main agent.
3. The slot states inside one step can look inconsistent (for example response date "not searched" and responder "not found" in one table). The page words the state as a decision of the rules. The states come from the writer; this step did not change them (finding U-3, second part).
4. The provenance file lists the export fields of a PDF value under `metadata_evidence` (finding W-4, second part). This is the writer; the package did not change it.
5. A document that is not an affair text still gets a submission step with a text of the kind `submitted`, by the block labels (finding W-5: no change by decision).
6. The 21 slots with no rule keep the state `not_found_in_pdf` with the reason `no_rule_searched`.
7. The first author has the result `not_compared` in each sample record: the export records of the package have no contributor rows.
8. The WebAssembly bundle, the server binary, the container files, `dist-src` and the deploy kit were not built again and not run. `worker/make_dist.py` was not run with the layout of now.
9. The server on port 8894 uses the same layout and the same page files. It was not stopped. `make layout` removed and wrote the layout folder once (about 1 s); a conversion on 8894 in that second would have failed.
10. The schema name of the view stays `parlpdfech-site-view/3` with added keys. A consumer that pins the key set of version 3 of chapter 16 must read chapter 17.4.
11. The document check of the project (`src/m00_pruefe_dokumente.py`) was not run on the documents of this step.
12. No commit, no push.

## 13 The cascade reader in the package and the decisions D1 to D7 (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network, no GPU, no commit.

A second skeptic examined the writer, the validator and the package (findings F-1 to F-6, `EXAMINATION.md` chapter 13). The main agent made the decisions D1 to D7. The project side changed the writer, the validator, the record form and the cascade files. This step changed the package. `CONTRACT.md` chapter 18 has the rules of now. Where this chapter and chapter 12 differ, this chapter applies; the replaced sentences of chapter 12 have the mark REPLACED.

### 13.1 What a record is now

1. The reader of a record is the cascade reader. The kind of the document selects which of the 7 values the rules search. Code rules decide the kind (the rule chain), for a sample and for an unknown PDF. eCH-0295 has no list of document kinds: this first step is a choice of the project.
2. A value that the cascade does not search is absent, with the state "not searched in this kind of document", the kind and the ids of the cascade rules.
3. A response document that prints the authors and the date of the proposal in its head states them: the record has a submission step with the sponsorship and the date and with no text block (cascade rule R30, a choice of the project).
4. A document of the kind proposal or executive proposal has no response step. The body that its text addresses is a candidate label only.
5. The probability of a value is the number of its rule tier over all folds of the calibration file, for every document, also a development document. The floor of 0.5 uses the same number. No fold value is shown.
6. The calibration file of the product is `daten/gj_values/round3/calibration_dev_all.json` (1,793 development documents). Origin: Development documents of 44 parliaments that the rule authors read. The values on 8 parliaments before the authors read them are lower for the affair number and the submission date: see the numbers of `daten/gj_values/closed_table.md`. A last run on documents that nobody read is planned. SUPERSEDED (chapter 18): the run took place on 13.10.2026, and AI agents had read a part of its documents before the run.
7. The validator runs the cascade reader again and compares value, span, tier and slot state of each field with the record (check C22).
8. For the kinds committee report, minutes and other document the rules search no submission date and no first author. The cost is in `crisp-dm/04-modeling/ech-cascade.md` chapter 6.3.1 of the project.

### 13.2 What changed in the package

| Part | Change |
|---|---|
| Layout | `worker/layout_add.py --values`: 14 paths (new: `src/m11_values_cascade.py`, `src/m11_cascade.py`, `src/m11_cascade.yaml`, `daten/gj_values/round3/calibration_dev_all.json`; removed: `daten/gj_values/calibration_open.json`). 86 files. |
| Worker | `worker/values_record.py` 0.3.0: the cascade reader with the kind from the rule chain, 20 check ids (C1 to C9, C11 to C22), the origin text, new keys of `convert.json` `values`. `worker/check_fresh.py`: one more synthetic file `response_head.pdf`. `worker/check_values.py`: cascade, D3 and D4 checks for each record, 6 synthetic files. |
| View | `view/site_view.py`: `head_values.cascade`, `values[].candidate`, `values[].in_sample`, `slots[].result`, `kind`, `cascade_rules`; no fold source. `contract/tools/make_schema.py`, `contract/view.schema.json`, `contract/tools/validate_view.py` (link checks of the cascade). |
| Page | The part "What this document can state" at the top of the eCH-0295 part; texts of decision D5; 42 new strings, 7 changed, 4 removed (`ui/README.md`). |
| Tools | `contract/tools/gate_values.py` (row `cascade`, 22 checks, 6 synthetic files, validator `m11-validate-3` with C22), `rdfcheck/tools/check_wasm.mjs` (the cascade of the manifest). |
| Examples | The 4 example views and `ui/fixtures/view_26171.json` are views of the instances of 13.3. |
| Not changed | The server, the WebAssembly module (`ui/pkg`), the container files, `dist-src`, the deploy kit, the `Makefile` (its test lines apply as they are). |

### 13.3 What was run

| Check | Result |
|---|---|
| `python package/worker/check_values.py --work package/work/cascade/cv3 --ocr none` | 244 of 244 checks passed |
| `python package/worker/check_worker.py --work package/work/cascade/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `make -C package test` (with `CARGO_TARGET_DIR=package/target-server`) | exit code 0: server 16 unit tests and 32 integration tests, rdfcheck 7 tests, the 4 example views valid, layout check (86 files, 0 different), `check_ui.mjs` "PASSED: 0 errors", `check_view.py` passed, "PASS: make test" |
| Instance on `127.0.0.1:8897`, profile `native`, values path on, empty work folder `work/cascade/work`; `python package/contract/tools/gate_values.py --port 8897 --out package/work/cascade/gate_values` | exit code 0, 104 of 104 rows passed: the 3 samples in the modes auto and rules, and 6 synthetic PDF files. Each job done and valid; each view valid against the schema with the link checks; 22 checks of each view passed (C10 skipped is possible); the row `cascade`; files and bundle; for the 6 sample records the validator of the project (`m11-validate-3`) passed again in its own process |
| `node rdfcheck/tools/check_wasm.mjs` on the 12 records of that instance | "ALL CHECKS PASSED" 12 times |
| Instance on `127.0.0.1:8897` with `PARLPDFECH_VALUES=off`, empty work folder `work/cascade/work_off`; `make -C package gate PORT=8897 GATE_OUT=work/cascade/gate GATE_REFERENCE=<reference run>` | first run: exit code 2, 101 checks, 1 not passed (the view of `s-26171` against `contract/examples/view_26171.json`: the example had the key set of chapter 12). The example was made again from this instance. Then `contract/tools/gate_compare.py` ran again on the saved answers of the same instance: exit code 0, 101 checks, 98 passed, 0 not passed, 3 rows of information not met (as before). `gate_api.sh` did not run a second time |
| `node ui/tools/check_ui.mjs` | PASSED, 0 errors |
| Browser (the built-in browser pane; the instance with the values path on): the result page of `s-26171`, `s-714840`, `s-879163` and of the 3 synthetic files `head_author.pdf`, `response_head.pdf`, `body_only.pdf`, in English and in German | each page shows the cascade part; table 13.4 has what it shows. German: no letter sharp s; no raw string key on the page |
| Document check of the project (`src/m00_pruefe_dokumente.py`) on the 7 changed documents | see 13.6 |

### 13.4 What the page shows (English page; the German page has the same values with German words)

| Record | Kind | Affair type | Title | Affair number | Date of submission | First author | Date of the response | Responding body |
|---|---|---|---|---|---|---|---|---|
| `s-26171` (auto; rules is equal) | proposal | read: interpellation, 0.9644, certain | read: "der OECD-Steuerreform und den Folgen für den Kanton Basel-Stadt", 0.8156, unsure | read: 19.5497, 0.875, unsure | searched, no value | read: Patricia von Falkenstein, 0.955, unsure | not searched (proposal) | not searched (proposal); addressed body "Regierungsrat" as a candidate, not written |
| `s-714840` | other document | read: draft_decree, 0.9568, certain | weak candidate, not written: "Swisslos-Fondsbeitrag; Verein MusikRaumBasel; Festival KlangBasel 2014 P140393", 0.1473 | read: P140393, 0.9706, unsure | not searched | not searched | not searched | not searched |
| `s-879163` | response of the executive | read: postulate, 0.6333, unsure | read: "Fonds d'aide au maintien des petits commerces et cafés du villages", 0.6333, unsure | searched, no value (recorded gap) | searched, no value | read: Tristan, 0.9521, unsure | searched, no value | read: Conseil municipal, 0.9937, certain |
| `head_author.pdf` | proposal | read: postulate, 0.9644, certain | read: Mehr Sitzbänke im Stadtpark, 0.8956, unsure | read: 2023/88, 0.9219, unsure | read: 2023-06-12, 0.788, unsure | read: Regula Beispielmann, 0.8648, unsure | not searched (proposal) | not searched (proposal); addressed body "Stadtrat" as a candidate, not written |
| `response_head.pdf` | response of the executive | read: interpellation, 0.9449, unsure | read: Sicherheit auf dem Schulweg, 0.8956, unsure | read: 2024/31, 0.9219, unsure | read: 2024-03-04, 0.8021, unsure | read: Hans Mustermann, 0.9521, unsure | read: 2024-05-20, 0.74, unsure | read: Stadtrates, 0.9896, certain |
| `body_only.pdf` | other document | searched, no value (gap) | searched, no value | searched, no value (gap) | not searched | not searched | not searched | not searched |

1. `response_head.pdf`: the eCH-0295 file has a submission step with the sponsorship and the date and with no text block, and a response step with its date, its body and 1 text block (decision D2).
2. `body_only.pdf`: the block labels give 1 submitted text block. The cascade gives no submission step to the kind other document. The text block stays (decision W-5), and the page says so in the row "Submitted text and reasoning".
3. `s-714840`, mode rules: the record has a submission step with 1 text block for the same cause; mode auto has none.
4. The 3 other synthetic files of the gate: `text_layer.pdf` and `with_values.pdf` have the kind combined (the affair number of `with_values.pdf` is a weak candidate, 0.3981); `no_type.pdf` has the kind other document.

### 13.5 An error of this step: the server on port 8894 was stopped

The server of the main agent on `127.0.0.1:8894` (process 68134) was stopped by this step on 13.10.2026 at 18:15:49 local time (16:15:49 UTC in the log of the own instance, which stopped in the same second). Cause: the command that stopped the own instance on port 8897 selected the processes by the path of the server binary, and the two servers had the same path. The rule of the task was not to stop that server. This step did not start it again: the task allowed port 8897 only, and the settings of the stopped process (site folder, switches) are not known to this step. The records of its work folder `work/records` were not changed. `STATE.md` chapter 3 gives the command of the earlier start: `make run-native PORT=8894`. After that error the own instance was stopped by its process number.

### 13.6 Limits and open points

1. SUPERSEDED (chapter 18). Earlier text: No measurement of the rules of now exists on documents that their authors did not read. The numbers of the 8 parliaments (`closed_table.md`) were measured with the rules and the calibration file of that time.
2. A wrong kind gives a wrong selection. The kind is a result of code rules; no person checked it.
3. The text blocks stay as the block labels give them (decision W-5), so a step that the cascade does not give to a kind can hold a text block (13.4, items 2 and 3).
4. Sample 879163: the first author of the record is "Tristan". It is the printed wording at the span. This step did not examine the rule.
5. `make layout` was not run (it removes the layout folder first). `worker/layout.py --update` ran, and the stale copy of `calibration_open.json` was removed from `build/layout` by hand. `layout.py --check` passed.
6. `worker/check_fresh.py` was not run. The forgeries of finding F-1 were not made again against the package.
7. The WebAssembly bundle, the server binary, the container files, `dist-src` and the deploy kit were not built again. `dist-src` holds the files of an earlier step.
8. Not done in the browser: a click on "Show on the page" in the cascade part; a small screen; the keyboard path; the 3 other synthetic files; the mode rules of the samples.
9. The view keeps the schema name `parlpdfech-site-view/3` with 2 keys removed and 1 enum value removed (`CONTRACT.md` chapter 18.4).
10. The server on port 8894 is stopped (13.5).
11. No commit, no push.

## 14 The findings S3-01 to S3-10, rule V5 and the calibration file of round 4 (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network, no GPU, no commit.

A third skeptic examined the cascade in the writer, the validator and the package (findings S3-01 to S3-10, `EXAMINATION.md` chapter 14). The project side changed the writer (`m11-writer-4`), the validator (`m11-validate-4`) and the record form. The reader has rule V5 (`m11-values-cascade-3`). This step changed the package. `CONTRACT.md` chapter 19 has the rules of now.

### 14.1 What a record is now (changes to 13.1)

1. The calibration file of the product is `daten/gj_values/round4/calibration_dev_all.json` (1,793 development documents, reader version 3). Origin: Development documents of 44 parliaments that the rule authors read. The rule files of the reader are made from the PDF alone. The values on 8 parliaments before the authors read them are lower for the affair number and the submission date: see the numbers of `daten/gj_values/closed_table.md`. A last run on documents that nobody read is in work. SUPERSEDED (chapter 18): the origin text of 14.10.2026 names the one fixed run of 13.10.2026.
2. Rule V5. If the rule chain made no decision (rule id D0), 2 facts of the PDF decide the kind. Fact 1 is a type word of a proposal of a member. Fact 2 is a responding body that a response rule finds. The 2 facts give the kind combined, fact 1 gives proposal, fact 2 gives response. With no fact, or with the type `draft_decree`, the kind stays other document.
3. Finding S3-01. A value that the cascade searches never has the state "not searched". If the rule of the value does not read the document, the slot has the state `not_found_in_pdf` with the reason `reader_scope`.
4. Finding S3-02. The validator opens the calibration file of the product by its own path below the scratch root. The worker gives it no other file and stops if the result does not say "the product file".
5. The cascade gives each kind its text slots. A text block of another text slot is not written to the eCH-0295 part. The block stays in the provenance file. This is a change of the project side that replaces decision W-5; the main agent must confirm it.
6. Finding S3-03. For a document of the kind proposal or executive proposal the worker runs the responder rule one more time. A sign is a candidate by a rule tier that is not the tier of an addressed body. A text block with a response label that is not written is a sign also. With a sign the view has the notice `response_signs`. The kind does not change.

### 14.2 What changed in the package

| Part | Change |
|---|---|
| Layout | `worker/layout_add.py --values`: the calibration file of round 4 replaces that of round 3; 5 code files changed (writer, validator, cascade reader, `m11_values_base.py`, `m11_value_reference.py`). 86 files, 14,980,658 bytes. |
| Worker | `worker/values_record.py` 0.4.0: `MEASURED_REL` and the texts name the file of round 4; the origin text of 4 sentences; `validate` gives no calibration file to the validator; new function `response_signs`; new keys of `convert.json` `values` (14.4 of `CONTRACT.md` chapter 19). `worker/serve_convert.py` and `worker/fresh.py` pass the signs to the view function. `worker/check_fresh.py`: 5 more synthetic files. `worker/check_values.py`: 4 more checks for each record and the checks of the 5 new files. |
| View | `view/site_view.py`: `kind_from` `rule_v5`, `kind_facts`, the entry state `reader_scope`, `texts[].not_written`, `head_values.response_signs`, the notice `response_signs`. `contract/tools/make_schema.py`, `contract/view.schema.json`, `contract/tools/validate_view.py` (link checks of rule V5, of the text slots and of the signs). |
| Page | The part "What this document can state" has the row "Where the kind comes from". For a document with no decision of the rule chain it shows the 2 facts and the result of rule V5. An entry with the reason `reader_scope` has its own text for the affair type, the first author and the response date. The notice of the signs of a response is at the top and in the cascade part. Corrected texts: the 2 sentences on the mode "code rules only" (S3-06) and the card heading "Addressed body (not in the record)" (S3-07). Also corrected: the sentence on a step that the kind does not have, and the sentence on the idea of the cascade (S3-08). 24 new strings, 10 changed, 2 removed; 699 keys. |
| Tools | `contract/tools/gate_values.py`: 11 synthetic files, the row "new file", validator `m11-validate-4` with no calibration argument. `rdfcheck/tools/check_wasm.mjs`: the example of the head values gives rows only if the eCH-0295 part holds a value or a text block. |
| Examples | The 4 example views and `ui/fixtures/view_26171.json` are views of the instances of 14.3. |
| Not changed | The server, the WebAssembly module (`ui/pkg`), the container files, `dist-src`, the deploy kit, the `Makefile`. |

### 14.3 What was run

The own server ran on `127.0.0.1:8896` (binary `target-server/release/parlpdfech-server` of 13.10. 12:32, profile `native`, the variables of the target `run-native`, the real worker). Two instances ran one after the other, each with an own empty work folder. Each one was stopped by its process number.

| Check | Result |
|---|---|
| `python package/worker/layout_add.py --values`, `python package/worker/layout.py --update`, then the stale copy of the round 3 file removed by hand | 1 path added, 5 changed, 1 removed; 6 files copied, 53 compiled files; `layout.py --check`: 86 files, 0 different |
| `python package/worker/check_values.py --work package/work/cascint/cv1 --ocr none` | 390 of 390 checks passed: the 3 samples in the two modes, each one with the switch off, one trace, 11 synthetic PDF files |
| `python package/worker/check_worker.py --work package/work/cascint/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `make -C package test` | exit code 0. Server: 16 unit tests and 32 integration tests. rdfcheck: 7 tests. The 4 example views are valid. Layout check: 86 files, 0 different. `check_ui.mjs`: 0 errors. `check_view.py` passed. Last line: "PASS: make test" |
| Instance with `PARLPDFECH_VALUES=off`, work folder `work/cascint/work_off`; `make -C package gate PORT=8896 GATE_OUT=work/cascint/gate GATE_REFERENCE=<reference run>` | first run: exit code 2, 101 checks, 1 not passed (the view of `s-26171` against the example: the example had no key `head_values.response_signs`). The example was made again from this instance. Then `contract/tools/gate_compare.py` ran again on the saved answers: exit code 0, 101 checks, 98 passed, 0 not passed, 3 rows of information not met (as before). `gate_api.sh` did not run a second time |
| Instance with the values path on, work folder `work/cascint/work_on`; `python package/contract/tools/gate_values.py --port 8896 --out package/work/cascint/gate_values` | exit code 0, 149 of 149 rows passed: the 3 samples in the modes auto and rules, and 11 synthetic PDF files. Each of the 17 jobs done and valid; each view valid against the schema with the link checks; 22 checks of each view passed (C10 skipped); for the 6 sample records the validator of the project (`m11-validate-4`) passed again in its own process with no calibration argument, and it said "the product file" |
| `node rdfcheck/tools/check_wasm.mjs` on the 17 records of that instance | first run: 15 times "ALL CHECKS PASSED", 2 records with 1 failed check (`body_only.pdf`, `no_type.pdf`: the example of the head values gave 0 rows, see 14.5 item 3). After the change of the tool: "ALL CHECKS PASSED" 17 times |
| `node ui/tools/check_ui.mjs` | passed, 0 errors |
| Browser (the built-in browser pane; the instance with the values path on): the result page of `v5_response.pdf` in English, of `proposal_signed.pdf` in German, of `s-26171-rules` in German | 14.4 has what the pages show. German: no letter sharp s; no raw string key on the page. No error in the console |

### 14.4 What the 17 records hold (view files of the instance; the numbers are those of the calibration file of round 4)

| Record | Kind (source, rule id of the rule chain) | The 7 entries |
|---|---|---|
| `s-26171` (auto and rules) | proposal (rule chain, P1) | type interpellation 0.9644 certain; title 0.8156; number 19.5497 0.875; submission date searched, no value; first author Patricia von Falkenstein 0.955; response not searched; addressed body "Regierungsrat" as a candidate (0.7727) |
| `s-714840` (auto and rules) | other document (rule chain, O1) | type draft_decree 0.9568 certain; title a weak candidate (0.1473); number P140393 0.9706; the 4 other entries not searched. Mode rules: 1 text block is not written |
| `s-879163` (auto and rules) | response (rule chain, A2) | type postulate 0.6333; title 0.6333; number, submission date and response date searched, no value; first author Tristan 0.9514; responder Conseil municipal 0.9912 certain |
| `text_layer.pdf`, `with_values.pdf` | combined (rule chain, A1) | as in chapter 13.4; the number of `with_values.pdf` is a weak candidate (0.3981) |
| `head_author.pdf` | proposal (rule chain, P1) | 5 values read; addressed body "Stadtrat" as a candidate |
| `response_head.pdf` | response (rule chain, A2) | 7 values read |
| `no_type.pdf`, `body_only.pdf` | other document (the rule chain made no decision, D0; rule V5 found none of the 2 facts) | no value is written; 1 text block is not written; the affair has an address only |
| `petition_head.pdf` | proposal (rule chain, P1) | type: searched, reason `reader_scope`; number "P 14" 0.9219; title 0.8476; addressed body "Stadtrat" as a candidate |
| `response_no_author.pdf` | response (rule chain, A2) | type, number, title, response date and responder read; first author: searched, reason `reader_scope` |
| `v5_proposal.pdf` | proposal (rule V5; D0; type word found, no response cue) | type postulate 0.8478; first author: reason `reader_scope`; a submission step with 1 text block |
| `v5_response.pdf` | response (rule V5; D0; no type word, a response cue) | responder Stadtrates 0.9912; first author and response date: reason `reader_scope`; title a weak candidate; 1 text block with the label of a submitted text is not written |
| `proposal_signed.pdf` | proposal (rule chain, P1) | type, title, submission date and first author read; no response step; notice `response_signs` (1 candidate of the tier `rsp_signature`) |

The pages. `v5_response.pdf` (English): the part "What this document can state" shows "Kind of this document: response of the executive", "Where the kind comes from: Rule V5 decided it: the rule chain made no decision; the type word and a response cue of the PDF decide.", "Fact 1 ... not found", "Fact 2 ... found" and the result of rule V5. `proposal_signed.pdf` (German): the notice of the signs of a response is below the kind and in the list of notices. `s-26171-rules` (German): the card of the addressed body has the heading "Angesprochene Behörde (nicht im Datensatz)"; the count line has the new sentence on the limit of the labels of the blocks.

### 14.5 Limits and open points

1. Decision D3 has a cost on the two head values of the response. The skeptic measured it on the 1,018 development documents of the kinds proposal and executive proposal (rules of round 3). The rules would find a responding body by a response rule in 193 documents: 176 equal to OpenParlData, 4 different, 13 with no value there. They would find a response date in 122 documents: 39 equal, 20 different, 63 with no value. These values are not read.
2. Decision D2. On the development documents (rules of round 3), the kind response has 195 first authors. 39 of them come from the address block of the reply letter, not from a head line (rule tiers `addressee_member` 35, `addressee_reply` 4).
3. The text block rule of 14.1 item 5 gives a record with no content for some documents: the kind other document with body text only. Its affair has an address and no other entry (`body_only.pdf`, `no_type.pdf`). The project side counts 159 such development documents. The main agent must confirm the rule. If the rule is taken back, the link check "a text block in a slot that the cascade does not give to the kind" of `validate_view.py` must go, and `check_wasm.mjs` needs no change.
4. A document with the kind proposal by rule V5 has the rule role other document in its rule file. The rules for a signature then do not read it: its first author often has the reason `reader_scope` (`v5_proposal.pdf`). The same applies to the response date of a response by rule V5 (`v5_response.pdf`). The project side counts 136 development documents with one or more such entries. Chapter 15.4 item 2 has the numbers of the fourth skeptic for the response date and the first author.
5. The rule file of a sample is the stored file of the project (`data/samples/<doc>/rules.json`), which names an export record. This step compared it with the file that is made from the PDF alone: for the 3 samples only the keys `body_key` and `export_record` differ. The rule result is equal. The sample data were not made again.
6. The signs of a response are a hint. A proposal that quotes a signature of the executive gets the notice also. The count of such notices on the development documents was not measured.
7. The numbers of D3 and D2 (items 1 and 2) are from the rules of round 3. They were not made again with the reader of version 3.
8. Not run: `worker/check_fresh.py`, `make layout`, a build of the server, of the WebAssembly bundle, of the container, of `dist-src` and of the deploy kit. `dist-src` holds the files of an earlier step.
9. Not done in the browser: the 14 other records, a small screen, the keyboard path, a click on "Show on the page".
10. The view keeps the schema name `parlpdfech-site-view/3` with new required keys (`CONTRACT.md` chapter 19.3).
11. No commit, no push. The own server on port 8896 is stopped.

## 15 The findings V4-01 to V4-07 of the fourth skeptic (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network, no GPU, no commit.

A fourth skeptic examined rule V5, the validator and the pages (findings V4-01 to V4-07, `EXAMINATION.md` chapter 15). This step changed the validator (`m11-validate-5`), its checks, the record form and the page. The reader `m11-values-cascade-3` is not changed: another step owns that file. `CONTRACT.md` chapter 20 has the rules of now.

### 15.1 What changed

| Finding | Part | Change |
|---|---|---|
| V4-01 (high) | Page | The reader is not changed. The page states the limit: a record with the kind response by rule V5 shows one more paragraph below the kind (string key `cascade.kind.v5.response_limit`). The patch for the reader is in 15.5. |
| V4-02 (medium) | Validator of the project | `m11_validate.calibration_choice` opens the product file below the code root first. A file at the product path below the root of the caller is used only if the code root has none. If the two files have different SHA-256 values, check C16 fails. `src/m11_validate_test.py` has the new case D2 (the forged record F5c). `daten/gj_values/record_form.md` chapter 7 (V6) states the rule. In the package the code root and the root are the same folder. |
| V4-03 (medium) | Documents | No code change. 15.4 item 2 states the limit with the numbers. |
| V4-04 (low) | Page | The card of the document label has one more sentence for a record with a kind by rule V5 (string key `unc.doclabel.v5`). |
| V4-05 (low) | Validator of the project | Check C22 has the new key `information`. It has one line for a written responder of the tier `rsp_addressee_cue`. `record_form.md` chapter 3.6 item 9 states the case. The package always gives a rule file, so it never writes such a record. |
| V4-06 (low) | Page | The German text of `slot_reason.reader_scope.response_date` is changed (`ui/strings.json` and `contract/strings.contract.json`). |
| V4-07 (information) | none | No change asked. |

More changes: `contract/tools/gate_values.py` expects the validator `m11-validate-5`. `worker/layout_files.json` and `build/layout` have the validator of now (86 files, 14,982,208 bytes). `ui/strings.json` has 701 keys (2 new, 1 changed). The view, its schema, the worker, the server, the WebAssembly module, the container files, `dist-src` and the deploy kit are not changed.

### 15.2 What was run

The own server ran on `127.0.0.1:8896` (binary `target-server/release/parlpdfech-server` of 13.10. 12:32, profile `native`, the variables of the target `run-native`, the real worker). Two instances ran one after the other, each with an own empty work folder. Each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_validate_test.py` | 88 of 88 checks passed (new: case D2) |
| `python src/m11_writer_test.py run` | 373 of 373 checks passed |
| `python src/m11_record_form_check.py check` | 70 of 70 checks passed |
| `python package/worker/layout_add.py --values`, `python package/worker/layout.py --update`, `python package/worker/layout.py --check` | 1 path changed (`src/m11_validate.py`); 1 file copied; 86 files, 0 different, 53 compiled files |
| `python package/worker/check_values.py --work package/work/v4/cv1 --ocr none` | 390 of 390 checks passed |
| `python package/worker/check_worker.py --work package/work/v4/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `make -C package test` | exit code 0. Server: 16 unit tests and 32 integration tests. rdfcheck: 7 tests. The 4 example views are valid. Layout check: 86 files, 0 different. `check_ui.mjs`: 0 errors. Last line: "PASS: make test" |
| Instance with the values path on, work folder `work/v4/work_on`; `python package/contract/tools/gate_values.py --port 8896 --out package/work/v4/gate_values` | exit code 0, 149 of 149 rows passed. For the 6 sample records the validator of the project (`m11-validate-5`) passed again in its own process with no calibration argument, and it said "the product file" |
| `node rdfcheck/tools/check_wasm.mjs` on the 17 records of that instance | "ALL CHECKS PASSED" 17 times |
| Instance with `PARLPDFECH_VALUES=off`, work folder `work/v4/work_off`; `make -C package gate PORT=8896 GATE_OUT=work/v4/gate GATE_REFERENCE=<reference run>` | exit code 0, 101 checks, 98 passed, 0 not passed, 3 rows of information not met (as before) |
| `node ui/tools/check_ui.mjs` | passed, 0 errors; 701 keys |
| Browser (the built-in browser pane; the instance with the values path on): the result page of `v5_response.pdf` in English and German, of `v5_proposal.pdf` in German | 15.3 has what the pages show. German: no letter sharp s; no raw string key on the page. No error in the console |
| `make -C package -n run-native PORT=8894` (a dry run, nothing started) | the target prints the commands of chapter 8 with the port 8894 |

### 15.3 What the pages show

1. `v5_response.pdf` (English): the paragraph "Limit of rule V5: the response cue can be a signature of the executive, the head of minutes or a decision of the executive. Such a document can be a proposal of the executive and no response. On the 1,793 development documents rule V5 gave this kind to 40 documents. For 22 of them the OpenParlData export names the type «Draft decree»." is below the affair type of the cascade part. The German page has the same paragraph in German.
2. The card of the document label, `v5_response.pdf`: "This label is the result of the rule chain. Rule V5 then gave the document the kind «response of the executive» (see the part What this document can state)." `v5_proposal.pdf` (German): the same sentence with the kind «Vorstoss». That page has no paragraph of item 1.
3. `v5_response.pdf` (German), response date: "Die Regeln haben diesen Eintrag gesucht. Für die Regelkette ist dieses Dokument keine Antwort, und die Labels der Blöcke ergeben keinen Text einer Antwort. Die Datumsregel liest dann kein Datum einer Antwort."

### 15.4 Limits and open points

1. Finding V4-01 is open. Rule V5 gives the kind response to a document that has a response cue and no type word. The cue is each responder tier that is not the tier of an addressed body. On the 1,793 development documents (round 4 values) 40 documents have the kind response by rule V5. Their responder tiers: `rsp_signature` 17, `rsp_minute_cue` 15, `rsp_response_block` 4, and 1 each of 4 more tiers. The export names the type `draft_decree` for 22 of the 40 documents. It names the type of a proposal of a member for 7 and no type for 11. This step made these counts again from `daten/gj_values/round4/values_dev_all.json` and `reference_dev_all.json`: they are equal. The record of such a document has a response step with a responding body that the PDF does not state as a responding body. The skeptic read 5 of the 40 documents: none is a response. The validator passes each such record.
2. Finding V4-03. A document with a kind by rule V5 keeps the rule role other document for the fixed rule modules. Counts on the 143 development documents with a kind by rule V5 (61 proposal, 42 combined, 40 response; made again by this step). The response date is found in 3 of the 82 documents of the kinds response and combined. 68 have the reason `reader_scope`, and 11 have no cue. The first author has the reason `reader_scope` in 54 of the 143 documents. The skeptic called the rule modules with the kind as the rule role. The result showed no clear gain: 44 more response dates, of them 6 equal to the export, 9 different and 29 with no value there. No code was changed.
3. Finding V4-05. A record with the kind "not known" (no rule file) can hold the addressed body of a proposal as the responding body. The package does not make such a record. The reader was not changed.
4. The paragraph of 15.3 item 1 holds 2 numbers of round 4 as fixed text. If the reader gets the patch of 15.5, the paragraph and its 2 lines of `ui/app.js` must go. The numbers of 15.4 item 1 change then.
5. The records of the work folder `work/records` are older than this step. A record that was made before the validator `m11-validate-5` keeps its stored validation result.
6. Not run: `worker/check_fresh.py`, `make layout`, a build of the server, of the WebAssembly bundle, of the container, of `dist-src` and of the deploy kit. `dist-src` holds the files of an earlier step. The example views were not made again: the view did not change.
7. Not done in the browser: the 14 other records, a small screen, the keyboard path.
8. The document check of the project gives old findings in the earlier chapters of this file, of `CONTRACT.md` and of `EXAMINATION.md`. The chapters of this step have 0 findings (see the report of this step).
9. No commit, no push. The own server on port 8896 is stopped. The package can start with `make -C package run-native PORT=8894`.

### 15.5 The patch for the reader (finding V4-01; file `src/m11_values_cascade.py`, not changed by this step)

```
V5_RESPONSE_TIERS = ("rsp_response_cue", "rsp_response_text")

    sub = affair_type in V5_PROPOSAL_TYPES
    rsp = response_tier is not None and response_tier not in ADDRESSEE_TIERS
    if sub and rsp:
        return "combined"
    if sub:
        return "proposal"
    if response_tier in V5_RESPONSE_TIERS:
        return "response"
    return kind
```

Effect that the skeptic counted on the development documents: the kind response by rule V5 falls from 40 documents to 2. 38 documents keep the kind other document. The patch needs 5 more steps. Make round 4 again. Change the header text of rule V5. Change the strings of fact 2 of the page. Remove the paragraph of 15.3 item 1. Change the example 22946 of `src/m11_writer_test.py`. The main agent must decide.

## 16 Rule V5 made narrower: reader version 4, round 4 made again, the rule files of the samples (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network, no GPU, no commit.

The main agent decided finding V4-01. The reader has the version `m11-values-cascade-4` (SHA-256 `91aed34f...`). Round 4 was made again with it. The product calibration file is the new file `daten/gj_values/round4/calibration_dev_all.json` (SHA-256 `e48e7a8d...`). This step brought the two files into the package and changed the page, the view, the checks and the samples. `CONTRACT.md` chapter 21 has the rules of now. The writer (`m11-writer-4`) and the validator (`m11-validate-5`) are not changed.

### 16.1 Rule V5 of now

A document with the rule id `D0` gets its kind from 2 reads of the PDF.

| Type word of a proposal of a member | Responder tier that the responder rule gives | Kind |
|---|---|---|
| found | each tier but `rsp_addressee_cue` and `rsp_response_text` | combined |
| found | none, `rsp_addressee_cue` or `rsp_response_text` | proposal |
| not found | `rsp_response_cue` (a phrase of the first lines or a heading; chapter 17 says what the pattern takes) | response |
| not found | each other tier, or none | other document (no change) |
| `draft_decree` | each | other document (no change) |

On the 1,793 development documents rule V5 changes the kind of 104 documents: 62 proposal, 41 combined, 1 response (document 903766). With reader version 3 the numbers were 61, 42 and 40.

### 16.2 What changed in the package

| Part | Change |
|---|---|
| Layout | `worker/layout_add.py --values` and `worker/layout.py --update`: 2 paths changed (`src/m11_values_cascade.py`, the calibration file), 2 files copied. 86 files, 14,963,773 bytes. |
| View | `view/site_view.py`: `head_values.cascade.kind_facts` has the new key `response_sign`. `response_cue` is true only for the tier `rsp_response_cue`. `response_sign` is true for each other tier that is not the tier of an addressed body and not `rsp_response_text`. `contract/tools/make_schema.py`, `contract/view.schema.json` and `contract/tools/validate_view.py` (the link check of rule V5) follow. |
| Page | The paragraph "Limit of rule V5" is removed: the string `cascade.kind.v5.response_limit` and its 2 lines of `renderCascade`. The string of fact 2 says: "a heading or a phrase of the first lines says that the executive answers". The result string says what a type word, a response cue and another sign of the executive give. 2 new strings: `cascade.kind.fact.response.sign` and `cascade.kind.fact.result.sign`. They are for a document with a signature or another sign of the executive and no response cue. `ui/strings.json` has 702 keys (2 new, 2 changed, 1 removed). |
| Synthetic files | `worker/check_fresh.py` writes 13 files for the values checks (11 before). `v5_response.pdf` is new text: a body line of the first lines says "Der Stadtrat erteilt folgende Antwort:". `v5_signature.pdf` is the earlier text of `v5_response.pdf`: a signature of the executive and no type word. `v5_combined.pdf` has a type word and a signature. |
| Checks | `worker/check_values.py` and `contract/tools/gate_values.py`: the lists of the 2 new files, new rows for them, the new key `response_sign`. |
| Worker | `worker/values_record.py`: 2 texts name reader version 4. No code path changed. `worker/layout_add.py`: 1 text. |
| Samples | `worker/make_samples.py` takes `rules.json` from `daten/gj/rules_pdf/<doc>.json` (finding A-F5 of an examiner). `sample.json` names the source path (`source_path`), the path in the scratch root (`project_path`, not changed) and the run record `daten/gj_values/round4/rules_pdf_build.json`. The tool stops if the file names an export record or if more keys than `body_key` and `export_record` differ from the stored file. The 3 samples were made again: 2 files changed in each folder (`rules.json`, `sample.json`). `index.json` did not change. |
| Examples | `contract/examples/view_26171_values.json`, `view_879163.json` and `view_unknown_pdf.json` are views of the instance of 16.3 (reader version 4). `view_26171.json` and `ui/fixtures/view_26171.json` did not change: the gate found them equal. The 4 example records of `daten/gj_values/record_examples/` were made again (`src/m11_record_form_check.py examples`). |
| Project side | `daten/gj_values/record_form.md`: rule 16 of chapter 2.3 and 4 counts. `src/m11_writer_test.py`: 1 sentence of the header. No check code changed. |
| Not changed | `src/m11_writer.py`, `src/m11_validate.py`, the server, the WebAssembly module (`ui/pkg`), the container files, `dist-src`, the deploy kit, the `Makefile`. |

### 16.3 What was run

The own server ran on `127.0.0.1:8896` (binary `target-server/release/parlpdfech-server` of 13.10. 12:32, profile `native`, the variables of the target `run-native`, the real worker). Two instances ran one after the other, each with an own empty work folder. Each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_writer_test.py run` | 373 of 373 checks passed. The 3 documents of rule V5 are 10995 (proposal), 903766 (response) and 2161 (combined). The tool takes the first id of each list; no code changed |
| `python src/m11_record_form_check.py examples`, then `check` | before the examples were made again: 61 of 70 (the examples named the earlier calibration file). After: 70 of 70 checks passed |
| `python src/m11_validate_test.py` | before the examples were made again: checks failed (C16, C22). After: 88 of 88 checks passed |
| `python package/worker/layout_add.py --values`, `python package/worker/layout.py --update`, `python package/worker/layout.py --check` | 2 paths changed; 2 files copied; 86 files, 0 different, 53 compiled files |
| `python package/worker/make_samples.py`, then `--check` | 3 samples, 28 files; 0 problems |
| `python package/worker/check_values.py --work package/work/v5n/cv1 --ocr none` | 434 of 434 checks passed: the 3 samples in the two modes, each one with the switch off, one trace, 13 synthetic PDF files |
| `python package/worker/check_worker.py --work package/work/v5n/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `make -C package test` | exit code 0. Server: 16 unit tests and 32 integration tests. rdfcheck: 7 tests. The 4 example views are valid. Layout check: 86 files, 0 different. `check_ui.mjs`: 0 errors. Last line: "PASS: make test". Run 2 times: before and after the examples were made again |
| Instance with the values path on, work folder `work/v5n/work_on`; `python package/contract/tools/gate_values.py --port 8896 --out package/work/v5n/gate_values` | exit code 0, 167 of 167 rows passed: the 3 samples in the modes auto and rules, and 13 synthetic PDF files. Each of the 19 jobs done and valid. For the 6 sample records the validator of the project (`m11-validate-5`) passed again in its own process, and it said "the product file" |
| `node rdfcheck/tools/check_wasm.mjs` on the 19 records of that instance | "ALL CHECKS PASSED" 19 times |
| Instance with `PARLPDFECH_VALUES=off`, work folder `work/v5n/work_off`; `make -C package gate PORT=8896 GATE_OUT=work/v5n/gate GATE_REFERENCE=<reference run>` | exit code 0, 101 checks, 0 not passed, 3 rows of information not met (as before). The records of the samples with the new rule files equal the reference run as before |
| `node ui/tools/check_ui.mjs` | passed, 0 errors; 702 keys |
| Browser (the built-in browser pane; the instance with the values path on): the cascade part of `v5_signature.pdf` in English and German, of `v5_response.pdf` in English, of `v5_combined.pdf` in German | 16.4 has what the pages show. German: no letter sharp s. No raw string key on the page. No error in the console |

### 16.4 What the 19 records hold (view files of the instance of 16.3)

The rows of chapter 14.4 apply, with these changes.

| Record | Kind (source, rule id of the rule chain) | The entries |
|---|---|---|
| `s-879163` (auto and rules) | response (rule chain, A2) | first author Tristan 0.95 (0.9514 before); the other entries as in 14.4 |
| `v5_proposal.pdf` | proposal (rule V5; D0; type word found, no cue, no sign) | as in 14.4 |
| `v5_response.pdf` | response (rule V5; D0; no type word, response cue of the tier `rsp_response_cue`) | responder Stadtrat 0.9895; first author: reason `reader_scope`; response date: searched, no value; title a weak candidate; a response step with 1 text block; 0 text blocks not written |
| `v5_signature.pdf` | other document (the rule chain made no decision, D0; rule V5 changed nothing: no type word, a sign of the tier `rsp_signature`) | no value is written; title a weak candidate; no submission step and no response step; no responding body; 1 text block is not written |
| `v5_combined.pdf` | combined (rule V5; D0; type word postulate, a sign of the tier `rsp_signature`) | type postulate 0.8478; responder Stadtrates 0.9912; first author and response date: reason `reader_scope`; a submission step and a response step |

The pages. `v5_signature.pdf` (English): "Kind of this document: other document". "Where the kind comes from: The rule chain made no decision. Rule V5 then looks for a type word and a response cue in the PDF." Fact 1: "not found". Fact 2: "not found. The rules found another sign of the executive, for example a signature or the head of minutes. With a type word this sign gives the kind «proposal with response». Alone it changes nothing." Result: "No type word and no response cue was found. A signature or another sign of the executive alone does not make the document a response. The kind stays «other document»." The German page has the same texts in German. `v5_response.pdf` (English): fact 2 "found"; the page has no paragraph "Limit of rule V5". `v5_combined.pdf` (German): fact 1 "gefunden: postulate (Postulat)", fact 2 with the sentence on the other sign, the kind "Vorstoss mit Antwort".

### 16.5 Limits and open points

1. A response heading in a larger font is no case of rule V5 in the package. The rule chain decides such a document: the heading "Antwort des Stadtrates" gave the rule id A1 or A2 in 4 synthetic texts of this step. The synthetic file of the kind response by rule V5 thus has its cue in a body line. No synthetic file has a response heading and the rule id D0.
2. Only 1 development document has the kind response by rule V5 (903766). The writer check has no second document for this kind. If a later reader gives this kind to no development document, check X12 of `src/m11_writer_test.py` fails: it asks for the 3 kinds.
3. The numbers of 14.5 items 1 to 4 and of 15.4 items 1 and 2 are those of reader version 3. Counts of this step for reader version 4, from `daten/gj_values/round4/values_dev_all.json`, on the 104 development documents with a kind by rule V5. The response date is found in 3 of the 42 documents of the kinds combined and response; 33 have the reason `reader_scope`, 6 have no cue. The first author has the reason `reader_scope` in 18 of the 104 documents. 44 of the 104 documents have 1 or more entries with that reason.
4. The text block rule (14.5 item 3). Count of this step with reader version 4: 194 development documents of the kind other document have 1 or more text blocks that are not written (159 with reader version 3). `daten/gj_values/record_form.md` chapter 2.3, rule 19, has the table.
5. The view keeps the schema name `parlpdfech-site-view/3` with one more required key (`kind_facts.response_sign`). A view that was stored before this step does not have it. The server makes the view again at each request, so a stored record of `work/records` is not a problem for the view. Its stored validation result and its values stay those of the earlier reader.
6. Chapter 14.5 item 5 is closed: the rule file of a sample is now the file from the PDF alone.
7. Not run: `worker/check_fresh.py`, `make layout`, and a build of the server, of the WebAssembly bundle, of the container, of `dist-src` and of the deploy kit. The tool `check_fresh.py` writes the 2 new files and has no check for them. `dist-src` holds the files of an earlier step: its page, its view function and its samples are older than this chapter.
8. Not done in the browser: the 15 other records, a small screen, the keyboard path.
9. The target `run-native` calls `native-data`. It makes the samples again with `worker/make_samples.py` and builds the layout. The tool needs the project files `daten/gj/rules_pdf/<doc>.json` and `daten/gj_values/round4/rules_pdf_build.json` for the 3 samples.
10. No commit, no push. The own server on port 8896 is stopped. The package can start with `make -C package run-native PORT=8894`. This step did not start it.
11. Added by the step of chapter 17: the decision on finding V4-01 made the finding smaller. It did not close it. Document 903766, the 1 development document with the kind response by rule V5, is a decree of the executive on a report. It answers no proposal.
12. Added by the step of chapter 17: A decree of the executive can name an earlier motion in its text. With a signature or a minutes cue it then gets the kind combined. A skeptic found 2 such documents: 82872 and 249082. Their reference type is `draft_decree`. The record then states the type of that motion and a response step that the PDF does not state. Nobody read the 41 combined and the 62 proposal documents of rule V5. No share of correct kinds is measured.

## 17 The findings V5-01 to V5-08 of the fifth skeptic on rule V5 of reader version 4 (13.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Each value is from one run if the text does not say more. Host as in the head of this file. No container, no network, no GPU, no commit.

A fifth skeptic examined rule V5 after chapter 16. `EXAMINATION.md` chapter 17 has the 8 findings and their states. The reader `src/m11_values_cascade.py` and the rule modules are design files since the entry record of the heads. This step did not change them. Thus the 2 high findings stay open: this step states the limits and gives the patch (17.4).

### 17.1 What changed

| Part | Change |
|---|---|
| Page strings | `ui/strings.json`: the strings `cascade.kind.fact.response` and `cascade.kind.fact.result.changed` say what the response cue is. They do not say any more that the executive answers. 3 new keys: `cascade.texts.v5_roles`, `cascade.texts.v5_roles.one`, `unc.card.v5_unsure`. 705 keys (702 before). |
| Page code | `ui/app.js`: 2 additions. Below the text entry of the submission step: one sentence, if the kind is combined by rule V5 and the entry has a text block. In the card of the responding body or of the response date: one sentence, if the kind is from rule V5, the word is «unsure» and the probability is at the limit or above. |
| Synthetic files | `worker/check_fresh.py` writes 14 files for the values checks (13 before). New: `v5_report.pdf`, a report of the executive on the accounts with the line "Bericht des Stadtrates". It has no type word and answers no proposal. |
| Checks | `worker/check_values.py` and `contract/tools/gate_values.py`: the lists and one row for `v5_report.pdf`. The row states a known limit: the kind is response by rule V5. `contract/tools/make_test_pdf.py`: 1 text. |
| Documents | `CONTRACT.md` chapter 22. `EXAMINATION.md` chapter 17 and the state of row V4-01 of chapter 16. This file: the table of 16.1, the items 11 and 12 of 16.5, this chapter. |
| Project side | `crisp-dm/04-modeling/ech-cascade.md` chapter 4.1: the items 10, 13 and 20, the new items 22 to 25, item 6 of the cause list. `daten/gj_values/round4/make_table_dev_all.py`: texts of chapter 1 item 20, chapter 8.2 and chapter 9 item 15. The script also has 2 checks on the counts and one more key of the record of rule V5. `table_dev_all.md` and `regressions_dev_all.json` were made again. |
| Not changed | Each design file of the entry record. The writer, the validator and the 3 check tools of the project side. The view, its schema, the server, the layout, the samples and the examples. `dist-src`, the container files and the deploy kit. `src/m11_numbers.py` and the 2 numbers files. |

### 17.2 What was run

The own server ran on `127.0.0.1:8896` (binary `target-server/release/parlpdfech-server` of 13.10. 12:32, profile `native`, the variables of the target `run-native`, the real worker). Two instances ran one after the other, each with an own empty work folder below `work/v5fix`. Each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_writer_test.py run` | 373 of 373 checks passed |
| `python src/m11_record_form_check.py check` | 70 of 70 checks passed |
| `python src/m11_validate_test.py` | exit code 0; 88 lines with the word PASS, 0 lines with the word FAIL |
| `python daten/gj_values/round4/make_table_dev_all.py --no-selection <diagnosis file of reader version 4>` | run 2 times. Run 1, before a change of the script: the table differed from the stored table in the line of the clock time only. Run 2, after the change: 3 places of text differ, and no count differs. `regressions_dev_all.json`: one more key, no other change |
| `python package/worker/layout.py --check` | 86 files, 0 different, 53 compiled files. No file of this step is a file of the layout |
| `python package/worker/make_samples.py --check` | 3 samples, 0 problems |
| `python package/worker/check_values.py --work package/work/v5fix/cv1 --ocr none` | 456 of 456 checks passed: the 3 samples in the two modes, each one with the switch off, one trace, 14 synthetic PDF files. A first run with no linkml package failed at the import of that package; it is no result |
| `python package/worker/check_worker.py --work package/work/v5fix/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `make -C package test` | exit code 0. Server: 16 unit tests and 32 integration tests. rdfcheck: 7 tests. The 4 example views are valid. Layout check: 0 different. `check_ui.mjs`: 0 errors. Last line: "PASS: make test" |
| Instance with the values path on, work folder `work/v5fix/work_on`; `python package/contract/tools/gate_values.py --port 8896 --out package/work/v5fix/gate_values` | exit code 0, 176 of 176 rows passed: the 3 samples in the modes auto and rules, and 14 synthetic PDF files. Each of the 20 jobs done and valid |
| `node rdfcheck/tools/check_wasm.mjs` on the 20 records of that instance | "ALL CHECKS PASSED" 20 times |
| Instance with `PARLPDFECH_VALUES=off`, work folder `work/v5fix/work_off`; `make -C package gate PORT=8896 GATE_OUT=work/v5fix/gate GATE_REFERENCE=<reference run>` | exit code 0, 101 checks, 0 not passed, 3 rows of information not met (as before) |
| `node ui/tools/check_ui.mjs` | passed, 0 errors; 705 keys |
| Document check `src/m00_pruefe_dokumente.py` | `ech-cascade.md` and `table_dev_all.md`: 0 findings of the rules 1 to 4. `CONTRACT.md`, `EXAMINATION.md` and this file: no finding in a line of this step; the earlier lines have findings as before |
| Browser (the built-in browser pane; the instance with the values path on): the record of `v5_report.pdf` in English, the record of `v5_combined.pdf` in German | 17.3 has what the pages show. German: no letter sharp s. No raw string key on the page. No error in the console |

Not run: `src/m11_numbers.py build` and `check` (finding V5-06). The tool opens the first tool file of the one last run. This step must not read a file of that run. Not run: `worker/check_fresh.py`, and a build of the server, of the WebAssembly bundle, of the container, of `dist-src` and of the deploy kit.

### 17.3 What the 2 new records and the pages show

| Record | Kind (source, rule id of the rule chain) | The entries |
|---|---|---|
| `v5_report.pdf` | response (rule V5; D0; no type word, the line "Bericht des Stadtrates" has the tier `rsp_response_cue`) | responder Stadtrates 0.9895, word «unsure»; first author: reason `reader_scope`; a response step with 1 text block; the recorded gaps are the affair type and the affair number. The PDF states no response: this record is the known limit of finding V5-01 |
| `v5_combined.pdf` | combined (rule V5; D0), as in 16.4 | no change of the record |

The page of `v5_report.pdf` (English). Fact 2: "response cue (a heading or a phrase of the first lines names the executive with a word for an answer, a statement or a report, or with a verb such as answers or submits). Such a phrase is also printed in a report or a proposal of the executive that answers no proposal." Value: "found". The card of the responding body has the sentence "The word is «unsure» because the rule chain made no decision on the kind of this document. The number was measured on documents with a decision."

The page of `v5_combined.pdf` (German). Below "Eingereichter Text und Begründung": "1 Textblock des PDF, aus den Labels der Blöcke." and "Regel V5 teilt den Text nicht auf. Der Text der Antwort kann in diesem Block stehen." The card of the responding body has the German sentence of `unc.card.v5_unsure`.

### 17.4 The patch for the reader (finding V5-01; file `src/m11_values_cascade.py`, a design file, not changed)

The skeptic gave a patch that gives `v5_kind` the tier `None` if the line of the cue has no answer word. A count of this step on `daten/gj_values/round4/values_dev_all.json` shows an effect that the skeptic did not name. 23 documents with a kind by rule V5 have the tier `rsp_response_cue`: 22 combined and 1 response. The line of the cue (record key `evidence`) has no answer word for 10 of them: 903766 and 9 combined documents. With the tier `None` these 9 documents get the kind proposal and lose the response step. Some of them are reports of the executive on a postulate ("Bericht des Gemeinderates Nr. P 16/2021"). Thus the patch below changes the branch response only.

```python
import re
V5_ANSWER_WORDS = re.compile(r"antwort|reponse|repond|rispost|rispond|scrivente|sottoscritto")

# in kind_of, after:  new = v5_kind(kind, a_type, tier)
    answer_word = bool(V5_ANSWER_WORDS.search(vb.fold(getattr(rsp, "evidence", None) or "")))
    if new == "response" and not answer_word:
        new = kind                                  # a report or a statement of the body alone is no response
    source["v5"] = {"kind_of_the_rule_chain": kind, "affair_type_read": a_type, "responder_tier_read": tier,
                    "answer_word_in_the_cue_line": answer_word, "changed": new != kind}
```

Effect on the 1,793 development documents (count of this step with the stored key `evidence`; the reader was not run): 903766 keeps the kind other document. Kind response by rule V5: 1 to 0. Combined 41 and proposal 62 do not change. By the text of its cue line, the synthetic file `v5_response.pdf` keeps the kind response ("erteilt folgende Antwort"), and `v5_report.pdf` gets the kind other document. This was not run.

The patch needs reader version 5 with a new header text. Round 4 must be made again: values, measures, second calculation, calibration file. The layout must be updated. The entry record of the heads holds the SHA-256 of the reader. In the package the view must not show fact 2 as found for such a record. The rows of `v5_report.pdf` in the 2 check tools must change to the kind other document. Check X12 of `src/m11_writer_test.py` asks for a development document of each of the 3 kinds. With the patch no development document has the kind response by rule V5: X12 must then take the kind response from a synthetic record. The attribute name `evidence` of the reader record must be confirmed in `src/m11_values_base.py` before the patch is applied.

No patch is known for the findings V5-02 and V5-03.

### 17.5 Limits and open points

1. Finding V4-01 is smaller, not closed. `EXAMINATION.md` chapter 17 has the 3 limits of rule V5. Limit 1: the kind response for a report of the executive. Limit 2: the kind combined for a decree that names an earlier motion. Limit 3: the kind proposal for a document that only names a proposal.
2. Nobody read the 41 combined and the 62 proposal documents of rule V5. The skeptic read 13 documents of a draw. No share of correct kinds is measured.
3. The row of fact 2 on the page has a long name now. On a narrow screen the name fills many lines. Not examined on a small screen.
4. The sentence of `unc.card.v5_unsure` shows only for a kind by rule V5. A document with the rule id `D0` and no change by rule V5 has no responding body in its record. Not examined: other causes for the word «unsure» at a number above the limit.
5. Finding V5-06: `public/track_2a/numbers.json` of 21:20 says "not measured yet" for 740 entries. The main agent must run `python src/m11_numbers.py build` and then `check --strict`. This file is a log source of that tool: the SHA-256 of this file changed with this chapter.
6. Finding V5-08, notes for the main agent. `src/m11_evidence.py` is a new file with no commit. The usage text of the reader names `round3` as the example path of `--out` (line 85; a design file). The files `make_table_dev_all.py`, `table_dev_all.md` and `regressions_dev_all.json` of round 4 are below a path of `.gitignore` and are not tracked.
7. The writer check wrote `package/work/t15/m11_writer_test.json`, and the form check wrote `daten/gj_values/record_form_check.json`, as each run does.
8. No commit, no push. The own server on port 8896 is stopped.

## 18 The texts of the package after the one fixed run (14.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter. Time: one laptop clock, 14.10.2026, 11:11 CEST.

The one fixed run of 13.10.2026 compared the values of 2 readers on 872 documents of 26 parliaments with the export, one time. Before this step, the record and the page said that a last run on documents that nobody read is in work. This step changed the texts. It changed no rule, no calibration file and no number of a record.

### 18.1 The origin text of now

The constant `CALIBRATION_ORIGIN` of `src/m11_writer.py` and `ORIGIN` of `worker/values_record.py` and `worker/layout_add.py` have this text (4 sentences):

> Development documents of 44 parliaments that the rule authors read; the rule files of the reader are made from the PDF alone. The one fixed run of 13.10.2026 used 872 documents of 26 other parliaments. There the share correct (correct / documents with an export value) was 0.2214 for the affair number and 0.2729 for the submission date. Before the run, AI agents had read 116 or more of these documents in earlier work.

1. Each number is a display value of `public/track_2a/numbers.json` of the project (made 14.10.2026 at 11:01). Ids: `values.last_run.rules_only.all.documents` (872), `values.last_run.parliaments.all` (26), `values.last_run.rules_only.all.affair_number.share_correct` (0.2214), `values.last_run.rules_only.all.submission_date.share_correct` (0.2729) and `values.last_run.contact.read_by_ai_agents.lower_limit` (116).
2. The reader of the 2 values is the reader with rules only. The reference is the export. No human checked a value.
3. `src/m11_writer_test.py` reads these 5 entries of `numbers.json` and looks for each display value in the text.
4. A first form of the text of this step gave the precision values (0.5275 and 0.5289) and no count of the contact. At that time `numbers.json` (13.10.2026, 22:11) had no entry for the share correct and for the contact. The checks of 18.4 ran with the text of now.

### 18.2 What changed

| File | Change |
|---|---|
| `src/m11_writer.py` | `CALIBRATION_ORIGIN` (18.1). Version of the writer: not changed |
| `src/m11_writer_test.py`, `src/m11_record_form_check.py` | The check of the origin text looks for the one fixed run, the values of `numbers.json` and the AI agents, and refuses "nobody read" and "in work" |
| `worker/values_record.py`, `worker/layout_add.py` | `ORIGIN` and the usage text (18.1) |
| `worker/layout_files.json`, `build/layout/` | Made again by `layout_add.py --values` and `layout.py --update`: the writer and the text of the calibration entry. The calibration file did not change |
| `ui/strings.json`, `contract/strings.contract.json` | `s4.record.measured` and `notice.values_measured`, English and German. The notice gives the precision of the run and of the development documents for the 7 fields. It also gives the share correct of 2 fields and the count of 116 |
| `README.md` | The limit on the probabilities names the run, the precision and the share correct of 2 fields, and the count of 116 |
| `CONTRACT.md` 19.1 item 1 | The origin text of now. 18.1 item 6 has the mark SUPERSEDED |
| `STATE.md` 13.1, 13.6, 14.1; `EXAMINATION.md` chapters 13, 14, 17; `worker/README.md` | The sentences on a planned last run have the mark SUPERSEDED or DONE. Finding V5-06 is closed: `numbers.json` was made again on 13.10.2026 at 22:11 and on 14.10.2026 at 11:01; each version has 0 entries with the status "not measured yet" |
| `daten/gj_values/record_examples/` of the project | The 4 examples were made again (command `examples`). The key `calibration.origin` of `strings_values.json` has the text of now |

`view/site_view.py` needed no change: the view does not pass on the note of a value calibration record.

### 18.3 The texts of the page

English, `notice.values_measured` (the part that changed):

> The one fixed run of 13.10.2026 compared the values of the rules with the OpenParlData export on 872 documents of 26 other parliaments. There the share of read values equal to the OpenParlData value was lower than on the development documents for each of the 7 fields. Values of the run, with the development documents in brackets: type of affair 0.9431 (0.9580), title 0.5179 (0.7607), affair number 0.5275 (0.7591), date of submission 0.5289 (0.6609). Date of the response 0.5116 (0.8402), responding body 0.9756 (0.9819), first author 0.8125 (0.8806). The share of documents with an OpenParlData value that got the equal value was 0.2214 for the affair number and 0.2729 for the date of submission. Before the run, AI agents had read 116 or more of these documents in earlier work.

The German text has the same content. The values of the run have the ids `values.last_run.rules_only.all.<field>.precision` and `.share_correct`, the values of the development documents `values.round4.<field>.precision`.

### 18.4 What was run (14.10.2026, one Mac, no container, no network)

The own server ran on `127.0.0.1:8896` (binary `target-server/release/parlpdfech-server` of 13.10. 12:32, the variables of the target `run-native`, the real worker). Two instances ran one after the other, each with an own empty work folder below `work/origin14`. Each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_writer_test.py run` | 373 of 373 checks passed |
| `python src/m11_record_form_check.py examples`, then `check` | the 4 examples made again; 70 of 70 checks passed |
| `python src/m11_validate_test.py` | exit code 0; 88 of 88 checks passed |
| `python package/worker/layout_add.py --values`, then `layout.py --update` | 86 files, 1 file copied, 0 different, 53 compiled files |
| `make -C package test` | exit code 0. Server: 16 unit tests and 32 integration tests. rdfcheck: 7 tests. The 4 example views are valid. Layout check: 0 different. `check_ui.mjs`: 0 errors. Last line: "PASS: make test" |
| `python package/worker/check_values.py --ocr none` | 456 of 456 checks passed |
| Instance with the values path on, work folder `work/origin14/work_on`; `python package/contract/tools/gate_values.py --port 8896 --out package/work/origin14/gate_values` | exit code 0, 176 of 176 rows passed. 97 files of its records have the origin text of now; 0 files have the words "nobody read" |
| Instance with `PARLPDFECH_VALUES=off`, work folder `work/origin14/work_off`; `make -C package gate PORT=8896 GATE_OUT=work/origin14/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0, 101 checks, 0 not passed, 3 rows of information not met (as before) |
| Browser (the built-in browser pane, the instance with the values path on): record `s-879163-rules` in German and in English | the 2 texts of 18.3 show; the old sentence is absent; no error in the console |
| `src/m11_hygiene.py --tree` on a copy of the 9 changed files of the package | no hit in a line of this step; the earlier lines have hits as before |
| Document check `src/m00_pruefe_dokumente.py` | no finding of the rules 1 to 4 in a line of this step; the earlier lines have findings as before |

Not run: a build of the server, of the WebAssembly bundle, of the container and of `dist-src`. The files of `dist-src` still have the old text until the next build.

### 18.5 Open points

1. `src/m11_values_sponsor.py` (a fixed file of the run) and `src/m11_value_folds_all.py` of the project have sentences on a last run on documents that no author read. This step did not change them. The code layout has a copy of `m11_values_sponsor.py`.
2. If a later build of `numbers.json` changes one of the 5 display values of 18.1, `src/m11_writer_test.py` fails. Then the text must change with it.
3. No commit, no push.

## 19 The start page, the result view, the page images and the file of the values (14.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Time: one laptop clock, 14.10.2026, about 12:30 CEST. Host as in the head of this file. No container, no network, no commit.

The owner said: a person must understand the page in 3 minutes; for each topic a link must lead to the place with more facts; the page needs a place with the PDF, a place with the RDF and a mark of each label with its probability. This step built these parts. The earlier result page stays as "the technical view" with all its parts.

### 19.1 What a person sees

| Route | Content |
|---|---|
| `#/` | One sentence on input and output: a PDF goes in, an eCH-0295 record in RDF comes out, and each value has a probability, a page and a place. A picture of the flow in HTML and CSS (PDF, 7 values with a probability, RDF). The 3 samples as large cards (title, parliament, kind, language) that open the result view. The box "How often correct?": the share correct of 4 fields in the one fixed run. Affair type 79 % (580 of 732), responding body 89 % (200 of 224), title 47 % (406 of 866), submission date 27 % (238 of 872). One sentence on the limits. The button for an own PDF. Each part has a link "more". Measured in the browser at 1440 x 900 px: 144 words above the fold without the texts of the 3 cards. The count includes the numbers such as "580 of 732". |
| `#/about/<part>` | The long texts of the earlier start page. The table of the 7 fields of the fixed run (share correct, counts, precision). 7 limit sentences from `public/track_2a/docs/limits.md` (L1 to L7) and from the limits of the README. The technical view and the modes, the notices, the list of the words. |
| `#/view/<record_id>` | Three places. The PDF: the image of each page, a coloured box on each written value, a grey dashed box on each text block, a download of the PDF. The values: field, value as printed, probability as a bar and the stored decimal, the word certain or unsure, page. Below the number: "in the fixed run this field was correct in N % of the documents". A link "Details" opens the card of the label in the technical view. One row for each field that was searched and not found or that has a weak candidate. One line "Not searched in a document of the kind ...". The RDF: tab 1 `<doc>.ech.ttl`, tab 2 `<doc>.values.ttl`, Turtle with colours, downloads. A row, a box and the triples of one value have the same colour. A click on one marks the 2 others. The help line "Click a row, a box or a triple." is at the top. A link opens the technical view. A finished job opens this route. |
| `#/record/<record_id>` | The technical view (no part removed); a link at the top goes back to the result view. |

### 19.2 How the page images are made

1. The renderer is pypdfium2 5.14.0 (PDFium 156.0.8076.0). It is in the project environment and in `container/requirements-full.txt`; it is not in `requirements-slim.txt`. Scale 2 (144 pixels for each inch), RGB, PNG.
2. The 3 samples: `worker/make_samples.py --pdf-only` copies `daten/pdf/lehrer_stichprobe/<doc>.pdf` to `data/samples/<doc>/source.pdf` (the SHA-256 must be the SHA-256 of the stored Docling output; it is) and writes `page-1.png`. `sample.json` has the entries with the roles `source_pdf` and `page_image`. A full run of the tool (`make native-data`) also makes them. Sizes (bytes): PDF 44,730, 106,481 and 221,387; image 358,631 (26171), 145,258 (714840) and 842,377 (879163, a scanned page). Two runs gave the same image bytes. The image target `slim` gets the images with the sample folders and needs no renderer.
3. A record of a sample: the worker copies the PDF and the images of the sample folder (SHA-256 check). An own PDF: the worker copies the PDF of the job and makes the images (`worker/values_record.py`, function `record_extras`). If pypdfium2 is absent or fails, the record has no image. Then `convert.json` key `page_images.state` says `no_renderer` or `renderer_error`. The result view then draws the lines of the text layer with the label "Drawn from the text layer" (seen in the fixture mode).
4. The server gives the files through the existing file route `GET /api/records/<id>/files/<name>` (new names `source.pdf`, `page-<n>.png`, `<doc>.values.ttl`; the Host and Origin rules are not changed). A foreign `Host` header gave 403 for `page-1.png`; `page-0.png` and `page-99.png` gave 404.
5. The box of a written value is the part of each line of its span. The part is the share of the characters of the line, as in the technical view. With no span, the box is the line frame. The grey boxes are the union of the line frames of each Docling block. On the 3 samples the boxes stand on the printed words (seen in the browser). The share of the characters is an estimate: the box can be a few characters too wide or too narrow.

### 19.3 The file of the values (`<doc>.values.ttl`, form `parlpdfech-values-ttl/1`)

`src/m11_writer.py` (now `m11-writer-5`, function `values_graph`, called by `rdf_step`) writes one node for each value of the eCH-0295 part from the facts of the label file. Vocabulary: `pvl:` = `https://schema.parlpdfech.example/values/`. Sample 26171: 4 nodes, 63 statements, 75 lines. Example (one node of 26171):

```turtle
<https://parlpdfech.ansv.ch/id/gj/record/doc-26171/value/affair_number> a pvl:ValueReading ;
    pvl:calibration <https://parlpdfech.ansv.ch/id/calibration/value.affair_number.number_docpart_last_line> ;
    pvl:charEnd 2552 ;
    pvl:charStart 2545 ;
    pvl:field "affair_number" ;
    pvl:label <https://parlpdfech.ansv.ch/id/gj/record/doc-26171/label/pdf-affair_number> ;
    pvl:page 1 ;
    pvl:printed "19.5497" ;
    pvl:probability 0.875 ;
    pvl:property aff:affairNumber ;
    pvl:resource <https://parlpdfech.ansv.ch/id/gj/record/doc-26171/affair> ;
    pvl:status "unsure" ;
    pvl:tier "number_docpart_last_line" ;
    pvl:value "19.5497" .
```

The manifest has the file in `outputs.values_ttl` and the facts in `rdf.values_ttl`; `rdf.triples` does not count it (the RDF panel compares `rdf.triples` with the TriG file). The validator (now `m11-validate-6`) parses the file in check C2 and compares each node with its label in check C3 (key `values_ttl_equals_label_file`): a copy of a record with the probability 0.875 changed to 0.9 failed C3 with "affair_number: probability differs from the label". `src/m11_writer_test.py` has the new check R11b for each record. The file is a download of the result view and of the technical view, and it is in `bundle.zip`.

### 19.4 What changed

| File | Change |
|---|---|
| `src/m11_writer.py` | `values_graph`, `written_value_labels`, the file in `rdf_step`; version `m11-writer-5`; docstring chapter 2 |
| `src/m11_validate.py` | `values_ttl_problems`; C2 and C3 read the file if the manifest names it; the texts of C2 and C3; version `m11-validate-6` |
| `src/m11_writer_test.py` | the list of the record files, R11 (8 outputs), new R11b |
| `worker/layout_files.json`, `build/layout/` | `layout_add.py --values` and `layout.py --update`: 2 files copied (writer, validator) |
| `worker/make_samples.py` | `add_pdf`, option `--pdf-only`; docstring |
| `data/samples/<doc>/` | `source.pdf`, `page-1.png`, the 2 new entries of `sample.json` |
| `worker/values_record.py` | `record_extras` |
| `worker/serve_convert.py`, `worker/fresh.py` | the extra files go to `--out`, to `convert.json` key `files` and to the new key `page_images` (values path only) |
| `view/site_view.py` | `files[]` with the roles `values_ttl`, `source_pdf`, `page_image`; `pages[].image` |
| `contract/view.schema.json`, `contract/tools/make_schema.py` | the optional key `pages[].image` |
| `server/src/ids.rs` | the 3 kinds of file in `file_media_type`, `file_rank` and `is_complete_record`; unit tests |
| `contract/tools/gate_values.py` | the validator version; the file count of a record; a new row for the file of the values and the images; the count of `SHA256SUMS` |
| `ui/index.html`, `ui/app.js`, `ui/app.css`, `ui/strings.json` | the start page, the page "About", the result view (`ui/README.md`, last chapter); 795 keys (705 before: 93 new, 3 removed) |
| `ui/run_numbers.json`, `ui/tools/make_run_numbers.py` | the display values of `public/track_2a/numbers.json` (made 14.10.2026 11:01) with their ids |
| `README.md`, `ui/README.md`, `CONTRACT.md` (chapter 23), this file | the 2 routes, the files, the checks |

### 19.5 What was run (14.10.2026, one Mac, no container, no network)

The own server ran on `127.0.0.1:8896` (binary of this step, `make native-server`: 2,961,184 bytes, 0 paths of this computer; the variables of the target `run-native`, the real worker). Three instances ran one after the other, each with an own empty work folder below `work/view14` (`work_on`, `work_gate`, `work_off`). Each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_writer_test.py run` | 398 of 398 checks passed (373 before; the new rows are R11b) |
| `python src/m11_validate_test.py` | exit code 0; 88 lines with the word PASS, 0 with the word FAIL |
| `python src/m11_record_form_check.py examples`, then `check` | the examples made again; 70 of 70 checks passed |
| `python package/worker/layout.py --check`; `make_samples.py --check` | 86 files, 0 different; 3 samples, 0 problems |
| `python package/worker/check_values.py --work package/work/view14/cv --ocr none` | 456 of 456 checks passed |
| `make -C package test` | exit code 0: server 16 unit tests and 32 integration tests, rdfcheck 7 tests, the 4 example views valid, layout 0 different, `check_ui.mjs` 0 errors, `check_view.py` passed; last line "PASS: make test" |
| `cargo clippy -p parlpdfech-server --all-targets -- -D warnings` | passed |
| Instance `work_on`: the 3 samples in the modes auto and rules through the API; the PDF of sample 879163 as an upload; the synthetic file `proposal_signed.pdf` as an upload | 8 jobs done and valid; 3.5 to 5.0 s for a sample; 4.6 s for the upload of the sample PDF (record `s-879163`, the files of the sample folder); 10.7 s for the synthetic PDF (record `u-b83d244cbaaace86`, its image made now by pypdfium2, 84,178 bytes). Each record has the 11 files, `<doc>.values.ttl`, `source.pdf` and `page-1.png`; `bundle.zip` has 15 entries and 14 correct lines of `SHA256SUMS` |
| Instance `work_gate`: `python package/contract/tools/gate_values.py --port 8896` | the first run stopped with a Python error of this step in the changed gate tool (a name was used two times); after the correction: exit code 0, 196 of 196 rows passed (the 3 samples in the 2 modes and 14 synthetic PDF files) |
| `node rdfcheck/tools/check_wasm.mjs` on the 20 records of that instance | "ALL CHECKS PASSED" 20 times |
| Instance `work_off` (`PARLPDFECH_VALUES=off`): `make -C package gate PORT=8896 GATE_OUT=work/view14/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0, 101 checks, 0 not passed, 3 rows of information not met (as before) |
| `python3 ui/tools/make_run_numbers.py --check` | equal |
| Browser: the built-in browser pane (Chromium) and Google Chrome headless (screenshots at 1440 px) on the instance `work_on`; a plain file server for the fixture mode | Start page and result view in English and German. The page "About": `#/about/numbers` sets the focus to its heading. A click on a row marked the box and the triple of the same value. A click on a box marked the row and the triple. A click on a triple marked the row and the box, in the 2 tabs. A sample card with no result ran the conversion and opened the result view. The technical view opens and links back. At 375 px: no horizontal scroll on the start page, the page "About" and the result view. No error in the console. |
| `src/m11_hygiene.py --tree` on a copy of the 18 changed files of the package | H1 to H4: 0 hits; H5: 2 hits in lines of `CONTRACT.md` that this step did not write. The tool reads id lists of the project itself (as in chapter 18.4) |

Not run: a build of the WebAssembly bundle (no source file of it changed), of the container and of `dist-src`. The files of `dist-src` have the earlier texts and no PDF until the next build. Also not run: `worker/check_worker.py`, `worker/check_fresh.py`, Firefox, Safari, a screen reader, a zoom of 200 %.

### 19.6 Limits and open points

1. The boxes are an estimate from the share of the characters of a line. They are not the boxes of the characters.
2. The image of a scanned page (879163) is 842,377 bytes. A PDF of 25 pages gives 25 images of about 0.1 to 0.9 MB each; this was not measured.
3. The share correct of the fixed run is a number of the reader with rules only on 26 parliaments together. The result view shows it next to the probability of each value; it is not a number of this document.
4. `ui/run_numbers.json` must be made again (`make_run_numbers.py`) if `numbers.json` changes; `--check` says if it is different.
5. The image target `slim` has the page images of the samples only; `full` has pypdfium2 for an own PDF (not run in a container).
6. The texts of the page "About" on the limits are short forms of `public/track_2a/docs/limits.md`. Nobody checked them against that file but the agent of this step.
7. No commit, no push. The own servers on port 8896 are stopped.

## 20 Corrections of the start page, the result view and the file of the values after two readers (14.10.2026)

Status: EXCEPTION, NOT RELEASED. No human checked this chapter, the code or a value. Time: one laptop clock, 14.10.2026, about 13:30 CEST. Host as in the head of this file. No container, no network, no commit.

The owner said again: a person must understand the page in 3 minutes and find more facts one click away. The person must also find the PDF, the RDF and the probability of each label. A jury reader and an examiner checked the work of chapter 19. Their main point: the result view gave a probability of 0.97 next to "correct in 22 %" and did not say which number to believe. This step closes their findings.

### 20.1 The findings and what changed

| Finding | Change |
|---|---|
| F1 (examiner): in `<doc>.values.ttl` the pair `pvl:resource` and `pvl:property` was no statement of the eCH-0295 record. This applied to the sponsor and the responder | `src/m11_writer.py` (`m11-writer-6`, form `parlpdfech-values-ttl/2`): `pvl:resource` is `label_subject`; the new property `pvl:entity` names `about_entity` if it is another resource (the actor whose `aff:name` holds the value). `src/m11_validate.py` (`m11-validate-7`): C3 expects this pair and checks that it is a statement of `<doc>.ech.ttl`. `src/m11_writer_test.py` R11b gives the eCH-0295 graph to the check. The example of 19.3 has the form 1 (SUPERSEDED) |
| F2 (examiner): the result view did not say that Apertus gives no value | A line under the heading: in the mode with Apertus "the values come from code rules; the stored Apertus results give only the labels of the text blocks"; own sentences for the mode "code rules only" and for an own PDF |
| F3 (examiner), jury 5: the body that a proposal addresses was in the line "not searched" | Own row with the value and the number ("Addressed body, not in the record"). The line of the fields that were not searched names the role of the document. It says that the role decides which steps the document can state |
| F4 (examiner), jury: 3 narrow columns at 1440 px; words broke in the middle; the page text was too small | The PDF and the values side by side (1 : 1.15), the RDF below across the width. Measured at 1440 x 900 (built-in browser pane): PDF place 564 px, values place 649 px, RDF place 1,232 px; the column "Value as printed" 219 px. A link opens each page image in full size |
| F5 (examiner): "correct in 79 % of the documents"; the column header; each PDF was saved as `source.pdf` | The row line gives the precision with counts (see jury 3); the About column says "with an OpenParlData value"; the server sends `filename="parlpdfech-<record_id>.pdf"` for `source.pdf` (`server/src/records.rs`; `CONTRACT.md` chapter 6) |
| Jury 1: "unsure" next to 0.9706, "certain" next to 0.9568 | One line above the table: «certain» is possible only for the type of affair and the responding body. The rule tier must be right in 95 % or more of 30 or more development documents (rule G7 item 4 of `src/m11_value_cal.py`). Only these 2 fields have a threshold a in `numbers.json` (`values.round4.<field>.calibration.threshold_a`). `about.p3` says the same |
| Jury 2: 0.875 rests on 3 development documents | Below each row: "{k} of {n} development documents right" (from `calibrations[].basis` of the view), "this sample is one of them" if `in_sample`, and for fewer than 30 documents a pale bar and "Few documents: the number is not stable." |
| Jury 3: "correct in 22 %" next to a value that was found | Below each row: "Fixed run: when the rules gave a value for this field, it was right in 53 % (182 of 345)". `ui/run_numbers.json` has the new value `given` (id `values.last_run.rules_only.all.<field>.given`). The share correct stays on the start page and the page "About" |
| Jury 4: heading "No title read from the PDF" while the card shows the title | With no title from the PDF, the heading is the OpenParlData title of the sample, or the weak candidate for an own PDF. A line says which one and gives the number of the weak candidate. The browser tab title follows the heading |
| Jury: the view did not show the match with OpenParlData | Below each row of a sample: "OpenParlData: equal", "equal by the comparison rule" with the OpenParlData value, "different" with the value, or "OpenParlData has no value" |
| Jury: the probability is shown as if it were the chance of a correct value | Line above the table: the probability comes from the development documents; on the documents of other parliaments in the fixed run the values were right less often. The start sentence says "each of its 7 head values"; the flow names the text parts of the PDF; the RDF note says that the text parts are HTML text with no row in the table |
| Jury: the start box shows 4 fields and counts the submission date twice; the run numbers are of "code rules only" | The box lists the 7 fields, one line each, and its lead says "code rules only"; the sentence "fewer than 3 in 10" is gone. The About lead says "reader «code rules only»" |
| Jury: About texts too long or not exact | `s0.values` removed (a repetition of `about.p5`); `about.p5` shorter; the paragraphs on labels and on certain follow the steps; `about.numbers.probability` says "the development documents in which the same rule tier gave a value" |
| Jury: the header of `values.ttl` names the script; `pvl:` has a placeholder domain | The 4 comment lines say what resource, property, entity and probability mean. The probability is (equal + 0.5) / (documents + 1). The lines also say that the domain is a placeholder and that the vocabulary is not published. The domain did not change (see 20.3) |
| Jury: triples not reachable by keyboard; cards with no accessible name; "Back to the overview" | The first line of the triples of each value is a button (Enter, space). Each card has `aria-label` (title, facts, action). The back link says "Back to the result"; the double arrow is gone |
| Jury: the link "Details" did not visibly reach the card | The link to one label jumps to its card with no smooth scroll. Measured in Google Chrome headless (CDP, 1440 x 900) on `s-26171`: after a click on "Details" of the affair number, `scrollY` 13,632 and the card heading 257 px below the top. A click on a row on a phone (375 x 812) brings its box to the middle of the screen (box top 408 px) |

### 20.2 What was run (14.10.2026, one Mac, no container, no network)

The own server ran on `127.0.0.1:8896` (binary of this step, `make native-server`: 2,961,168 bytes, 0 paths of this computer). Instances one after the other with own work folders below `work/fix14` (`work_on`, `work_gate`, `work_off`); each one was stopped by its process number. Port 8894 was not used.

| Check | Result |
|---|---|
| `python src/m11_writer_test.py run` | 398 of 398 checks passed (R11b with the eCH-0295 graph) |
| `python src/m11_validate_test.py` | exit code 0; 88 lines PASS, 0 FAIL |
| `python src/m11_record_form_check.py examples`, then `check` | examples made again; 70 of 70 checks passed |
| `layout_add.py --values`, `layout.py --update`, `layout.py --check` | 2 files copied (writer, validator); 86 files, 0 different |
| `make_samples.py --check`; `make_run_numbers.py --check` | 3 samples, 0 problems; equal (source `numbers.json` made 14.10.2026 12:31) |
| `make -C package test` | exit code 0; server 16 + 32 tests, rdfcheck 7, the 4 example views valid, `check_ui.mjs` 0 errors (808 keys), last line "PASS: make test" |
| `cargo clippy -p parlpdfech-server --all-targets -- -D warnings` | passed |
| `python package/worker/check_values.py --work package/work/fix14/cv --ocr none` | 456 of 456 checks passed |
| Instance `work_on`: the 3 samples in the modes auto and rules, and `with_values.pdf` as an upload | 7 jobs done; each validation passed with `m11-validate-7`. The comparison script of the examiner: each value of the table equals the label file and its node; the pair resource and property is a statement of the eCH-0295 file for each value. A second script: each of the 6 `pvl:entity` nodes (sponsor, responder) has the value in `aff:name/aff:text` and is linked from the pair. `?download=1` of `source.pdf` gives `filename="parlpdfech-s-26171.pdf"` |
| Instance `work_gate`: `python package/contract/tools/gate_values.py --port 8896` | exit code 0, 196 of 196 rows passed |
| Instance `work_off` (`PARLPDFECH_VALUES=off`): `make gate PORT=8896 GATE_OUT=work/fix14/gate GATE_REFERENCE=daten/gj/fullrun_b1s_dev` | exit code 0, 101 checks, 0 not passed, 3 rows of information not met (as before) |
| Browser: the built-in browser pane (hidden, so no scroll there) and Google Chrome headless | Start page and result view in English and German at 1440 x 900; the result views of the 3 samples and of the upload; 375 x 812 with no horizontal scroll on the start page, the page "About" and the result view; a click on a row, a box and a triple (also with Enter) marks the same value in the 3 places; no error in the console |

### 20.3 Limits and open points

1. The domain of `pvl:` stays `schema.parlpdfech.example`, as the label schema and the profile of the project. A real domain needs a decision of the owner; the file says that the domain is a placeholder.
2. The text "«certain» is possible only for the type of affair and the responding body" is a fact of the calibration of round 4. If the calibration changes, the strings `view.values.certain` and `about.p3` must change with it.
3. The mismatches of the title ("der OECD-…" against "Der OECD-…", "cafés du villages" against "dans les villages") are readings of the reader, not of the view. The view now shows the OpenParlData value next to them.
4. The HTML markup of the text blocks in `aff:text` is not changed; the view says that it is there.
5. Not run: a build of the WebAssembly bundle (no source changed), of the container and of `dist-src`; Firefox, Safari, a screen reader, a zoom of 200 %; `worker/check_worker.py`, `worker/check_fresh.py`.
6. No commit, no push.


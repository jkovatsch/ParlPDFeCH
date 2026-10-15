# ParlPDFeCH, Track 2A: a parliament PDF goes in, an eCH-0295 record comes out

What goes in: one PDF of a Swiss parliament. What comes out: one eCH-0295 record in Turtle and YAML, a second RDF file `<doc>.values.ttl` with the probability of each value, and the result of a validator. Each head value of the record (up to 7) is read from the PDF and has a probability. A value from the rules also has a page and a text span. Identifiers and constants of the record have no probability. The OpenParlData export is the reference of the measurement; at run time no export value goes into a record.

To start the app, use `make run`, the Docker way that the template asks for. It converts the 3 samples only. For your own PDF, run `make setup-pdf` one time, then `make run-native` (no container, chapter "Run it"). Both ways ran on one Mac on 14.10.2026.

In the one fixed run, linear heads on stored hidden states of Apertus-v1.5-8B gave values for 2 of the 7 fields. These fields are the affair type and the first author. A head tier gave a value where the rules found none, or where the rule value had a probability below 0.5. The rules gave all other values. In the app, the rules give each value of the record, in each mode. For its 3 samples, the app uses stored Apertus states for the block labels only.

No person has accepted the numbers of this text. The numbers of the run come from the one fixed run of 13.10.2026. The development numbers come from the documents that the rule authors read. AI agents made and examined them.

Three limits come first. [docs/limits.md](docs/limits.md) gives all 12.

1. Fewer than half of the documents with a reference get the export value. This applies to the affair number, the 2 dates, the title and the first author.
2. AI agents had read some of the 872 documents before the run: 116 or more, that is 48 validation documents and all 68 group-7 documents. The rule chain of the roles, from the earlier converter of 12.10.2026, was designed on a list with 38 documents of the run.
3. AI agents of one model family wrote the rules, the tools and the measures, and examined them. No human checked a value of the one fixed run. The reference is a register, not a hand-checked gold set.

Number ids: `values.last_run.contact.read_by_ai_agents.lower_limit` (116), `values.last_run.contact.kind1.validation` (48), `values.last_run.contact.kind1.group7` (68), `values.last_run.contact.rule_design_list.validation` (38).

Result of the one fixed run of 13.10.2026: 872 documents of 26 parliaments, each value compared one time with the export. The run has 804 validation documents of 18 parliaments and 68 documents of 8 more parliaments (group 7). AI agents had read each group-7 document before the run. Development: 1,793 documents of 44 other parliaments.

Reader with rules only:

| Field | Precision, run | Found rate, run | Share correct, run (correct of documents with a reference) | Precision, development | Share correct, development |
|---|---|---|---|---|---|
| affair type | 0.9431 | 0.8402 | 0.7923 (580 of 732) | 0.9580 | 0.8262 |
| title | 0.5179 | 0.9053 | 0.4688 (406 of 866) | 0.7607 | 0.6834 |
| affair number | 0.5275 | 0.4197 | 0.2214 (182 of 822) | 0.7591 | 0.3582 |
| submission date | 0.5289 | 0.5161 | 0.2729 (238 of 872) | 0.6609 | 0.4314 |
| response date | 0.5116 | 0.4057 | 0.2075 (22 of 106) | 0.8402 | 0.7762 |
| responder | 0.9756 | 0.9152 | 0.8929 (200 of 224) | 0.9819 | 0.9476 |
| first author | 0.8125 | 0.5607 | 0.4556 (195 of 428) | 0.8806 | 0.7474 |

Words of the table:

- Correct, wrong: equal or not equal to the export value, against the export, after the normalisation of the project.
- Precision: correct / (correct + wrong). Found rate: (correct + wrong) / documents with a reference.
- Share correct: correct / documents with a reference. It is the product of precision and found rate.
- The 2 response fields count only documents with the rule role response or combined.
- The measure counts each value of a reader, also a value below the floor of 0.5 that the writer does not put into the record.
- The development values come from the 1,793 documents that the rule authors read when they made the rules. Thus these values are optimistic.
- Reference: the OpenParlData export. No human checked a value of the one fixed run.
- Status: each entry of [numbers.json](numbers.json) has the status EXCEPTION, NOT RELEASED. This means that no person has accepted it.

Number ids (file [numbers.json](numbers.json)):

- Run: `values.last_run.rules_only.all.<field>.precision`, `.found_rate`, `.share_correct`, `.correct`, `.with_reference`.
- Sets of the run: `values.last_run.rules_only.<all|validation|group7>.documents`, `values.last_run.parliaments.<all|validation|group7>`.
- Development: `values.round4.<field>.precision` and `.recall` (the share correct); `values.round4.documents`, `values.round4.parliaments`.
- Field keys: `affair_type`, `title`, `affair_number`, `submission_date`, `response_date`, `responder_name`, `first_author`.
- `sets.parliaments.validation` (14) and `sets.parliaments.dev` (42) count other sets: the documents with an AI reference of the block roles. They are not the sets of the run.

## What this is

1. A PDF of a Swiss parliament goes in. An eCH-0295 record comes out.
2. Each head value of the record (up to 7) is read from the PDF and has a probability. A value from the rules also has a page and a text span. Identifiers and constants of the record have no probability.
3. The OpenParlData export is the reference of the measurement. On development documents it also gives the fit labels of the Apertus heads. At run time no export value goes into a record.
4. The one fixed run of 13.10.2026 compared the values of 872 documents of 26 parliaments with the export, one time.
5. No pass limit was fixed before the run. Thus this text gives the numbers and their plain meaning, and no statement that a field passes.

This folder is the project root for the judges of Hack Apertus. The front page of the repository is [../README.md](../README.md). The technical report is [technical_report.md](technical_report.md). The long version is [docs/report-long.md](docs/report-long.md). [docs/repository-map.md](docs/repository-map.md) gives each folder and its source.

## Run it

Run the commands in this folder (`track_2a/`). [docs/run-locally.md](docs/run-locally.md) gives the 2 ways to start the app in short form.

```bash
make run          # needs Docker only, not make setup; ran on one Mac on 14.10.2026; then open http://127.0.0.1:8080/app/
make setup        # one time, with network; for make run-native and make test
make setup-pdf    # one time, with network; only for your own PDF with make run-native; needs pdftotext
make run-native   # no container; needs cargo and Python 3.12; ran on one Mac; then open http://127.0.0.1:8080/app/
make test         # checks with no network
```

### The commands and their state

| Command | What it does | State on 14.10.2026 (`make setup-pdf`: 15.10.2026) |
|---|---|---|
| `make setup` | One time, with network. It installs Python 3.12 with uv (uv can also put the command `python3.12` into `~/.local/bin`) and the Python packages of the app into `.venv/`. It downloads the Rust crates of `app/Cargo.lock` (only if cargo is on the computer; if not, it prints a note), the packages of the earlier converter and the 2 eCH-0295 schema files (pinned commit and SHA-256). `make run` does not need it. | Run on one Mac (Apple silicon, macOS) in a fresh clone. uv and cargo took the packages from the local caches of that Mac. The 2 schema files agreed with the pinned SHA-256. |
| `make setup-pdf` | One time, with network, after `make setup`. Only for your own PDF with `make run-native`. It stops if the command `pdftotext` is absent and gives the install command. It installs the packages of `app/container/requirements-full.txt` (`docling` 2.133.0, `pypdfium2` 5.14.0, torch) into `.venv/`. It downloads the 2 Docling models into the Hugging Face cache if they are absent. It installs no text recognition (OCR). | Run on one Mac (Apple silicon, macOS) on 15.10.2026, in a fresh clone of GitHub at commit `3eff351`. The target `setup-pdf` was added to the clone as a patch. The packages came from the uv cache of that Mac. The 2 models came from its Hugging Face cache, and in 2 more runs with an empty cache from huggingface.co. Then `make run-native` converted 2 PDFs that are not in the sample index (copies of 2 samples with one added comment line), with 2 valid records. `make test` gave PASS. |
| `make run` | Needs Docker. It builds the image (target `slim`) from `app/` and starts it on `127.0.0.1:8080`. It waits for `/healthz`. Then open `http://127.0.0.1:8080/app/`. The target `slim` converts the 3 samples only. | Run one time on one Mac (Apple silicon, Docker server 29.2.1), in a clone of GitHub at commit `10e07b4`. The command was `make run PARLPDFECH_PORT=8082`, because a second check used port 8080. The 3 samples in the modes auto and rules gave 6 valid records. Not run: `run-full` and `check-offline` of `app/Makefile`. On 14.10.2026 a private build pipeline on Linux built a container image from the source tree of the package. Nobody started this image. |
| `make stop`, `make logs` | They stop the container of `make run`, or show its log. | Not run. |
| `make run-native` | No container. It builds the Rust server and the WebAssembly bundle with cargo. Then it starts the app on `127.0.0.1:8080` (`PORT=` sets another port). Stop it with Ctrl-C. | Run on one Mac (Apple silicon, macOS), with the offline flags of cargo: in this folder (port 8899) and in a fresh clone (port 8898). Each time, the 3 samples in the modes auto and rules gave 6 valid records. The server gave the page, the result data, `<doc>.values.ttl`, `source.pdf` and `page-1.png` with the status 200. |
| `make test` | Checks with no network and no Rust compiler. It compares each copied file with `SOURCES.json` and checks the prompt files of `gj_jev_v1_de`. It runs the validator on the 6 stored output files of the earlier converter and on `tests/invalid_instance.yaml`, which it must refuse. It checks the file list and the code layout of `app/`. | PASS on one Mac, in this folder and in a fresh clone. It does not compare the numbers of the texts with `numbers.json`. |
| `make test-app` | The checks of `app/`: `cargo test` of the server and of the RDF module, the example view, and a start of the seed script. It needs cargo and the crates of `make setup`. | PASS on one Mac. |
| `make clean` | It removes `build/` and the build outputs of `app/`. | in the `Makefile` |
| `make run-earlier` | The earlier converter of 12.10.2026 on the 3 samples. Its metadata values come from the export record, not from the PDF. Before 14.10.2026 this command had the name `make run`. | PASS on one Mac. |
| `make head-selftest` | A self-check of an earlier Apertus head code on synthetic data (no model). | in the `Makefile` |

- The template asks that `make run` starts the project in Docker on a clean checkout. This text records one such run, on commit `10e07b4` (next item). For your own PDF, use `make setup-pdf` one time, then `make run-native`.
- The 2 clones of GitHub: on 14.10.2026, 2 AI agents each made a `git clone` of commit `10e07b4` from GitHub, on one Mac. In clone 1, `make run PARLPDFECH_PORT=8082` ran. In clone 2, `make setup`, `make test` (PASS), `make run-earlier` (PASS) and `make run-native PORT=8080` ran. In each clone, the 3 samples in the modes auto and rules gave 6 valid records.
- The fresh clone: on 14.10.2026 an AI examiner made a `git clone` of the local repository and added the files of this version. Then the examiner ran `make setup`, `make test` and `make run-native` in it, on one Mac. It was not a clone of GitHub.
- The state lines in the files of `app/` (for example `DIST.md`, `README.md`, `STATE.md`, `Makefile` and `container/BUILD-NOTES.md`) are older than these runs. In this version, the files of `app/` are as in commit `10e07b4`. `make test` compares them with the list `DIST-MANIFEST.json`.
- An own PDF: `app/README.md` (chapter "The modes") records runs with synthetic PDF files and with the 3 sample PDF files. These ran on one Mac, with no container. The row `make setup-pdf` records 2 changed copies of samples on 15.10.2026. No other parliament PDF is recorded.
- In an earlier run on a copy of the files, the conversion of an own PDF stopped with the note `pdf_reader_absent`. `make setup-pdf` installs the absent packages (next chapter).

### What `make run-native` needs

- cargo with the target `wasm32-unknown-unknown`, and the command `wasm-bindgen` 0.2.127. With rustup, the file `app/rust-toolchain.toml` adds the target. To install the command: `cargo install wasm-bindgen-cli --version 0.2.127` (network).
- A Python 3.12 with the packages of `app/container/requirements-slim.txt`. `make setup` makes `.venv/`. Without it, the target uses `python3`, or `APP_PYTHON=<command>`.
- The 3 samples need nothing more.
- The conversion of your own PDF needs more: the Python packages `docling` 2.133.0 and `pypdfium2` 5.14.0, the 2 Docling models in the local Hugging Face cache and the command `pdftotext`.
- `make setup-pdf` installs these packages with their dependencies (`app/container/requirements-full.txt`) and downloads the 2 models. It does not install `pdftotext` (macOS with Homebrew: `brew install poppler`). Without the packages, the app stops with the note `pdf_reader_absent`.
- Size on a Mac with Apple silicon: 283.5 MB of packages (sizes from the PyPI data) and 530.0 MB of models. `.venv/` grows by about 1 GB.
- `make setup-pdf` installs no text recognition (OCR). A PDF with no text layer stops with the note `no_text_layer`. The page can say that the text recognition of macOS runs. It runs only if the Python package `ocrmac` is in `.venv/`.
- An unchanged PDF of a sample gives the stored result of that sample. Docling does not run for it.
- The server listens on `127.0.0.1`. Its API has no authentication.

## What you see

The page is `http://127.0.0.1:8080/app/` (`?lang=de` before the hash gives the German texts). It has these routes:

| Route | Content |
|---|---|
| `#/` (start page) | One sentence on what goes in and what comes out. A small picture of the flow: PDF, 7 values with a probability, RDF. The 3 samples as cards that open the result view. The box "How often correct?" gives the share correct of the 7 fields in the one fixed run of 13.10.2026 (code rules only). The button for your own PDF. Each topic has a link to the page "About". |
| `#/about/<part>` (page "About") | The long texts: `method`, `numbers` (the table of the 7 fields of the fixed run), `limits` (short forms of [docs/limits.md](docs/limits.md)) and `technical`. |
| `#/samples`, `#/upload`, `#/job/<job_id>` | The sample cards with one button for each mode (stored Apertus states, or code rules only); the form for your own PDF (`make run-native` only, with the packages of the chapter "What `make run-native` needs"); the 6 steps of a running conversion. |
| `#/view/<record_id>` (result view) | 3 places. The PDF: the image of each page (`page-<n>.png`) with a coloured box on each value and a grey box on each text block. The values: field, value as printed, probability (a bar and the stored decimal), the word certain or unsure, page. A line below each row gives the development documents behind the number and the precision of the field in the fixed run. For a sample, it also gives the comparison with OpenParlData. The RDF: the eCH-0295 record and the file of the values with probabilities (`<doc>.values.ttl`), as Turtle text. A click on a row, a box or a triple marks the same value in the other 2 places. A link opens the technical view. |
| `#/record/<record_id>` (technical view) | The full result page of the same record. Before the result view of 14.10.2026, it was the result page of the app. The part "What this document can state" gives the kind of the document, the source of the kind and the 7 head values. Then come the 3 tables of the affair and its 2 steps, and the page, drawn from the places of its lines. This is not an image of the PDF; the result view shows the image. Each label has a card. Then come the downloads, the checks and the RDF panel. |

Downloads of each result: TriG, Turtle, RDF/XML, and a ZIP file with all files and their SHA-256 values. A record with values from the PDF also has `<doc>.values.ttl`, `source.pdf` (the download has the name `parlpdfech-<record_id>.pdf`) and `page-<n>.png`. `app/README.md`, chapter "What you see", gives the details.

A value can also have one of these states: the rules found no value; the kind of the document has no such entry, so the field is not searched; a weak candidate below the floor of the calibration, which is not written to the record.

## Samples

The 3 samples are development documents. The rule authors read them, and the heads were fitted on them. Thus the probability of a value of a sample counts the sample itself. Two AI agents examined each sample for personal data of third persons, with the result PASS: they found only persons with a public role. No human checked this.

| Document | Parliament | Language | Content of the PDF | Affair type on the sample card (key) |
|---|---|---|---|---|
| 26171 | Grosser Rat Basel-Stadt (canton) | German | Text of an interpellation | `interpellation` |
| 879163 | Conseil général Val de Bagnes (municipality) | French | Statement of the executive on a postulate | `postulate` |
| 714840 | Basel-Stadt (canton) | German | Resolution of the executive in its own competence | `draft_decree` |

The sample card gives the affair type of the OpenParlData export, in the map of the project.

| Document | URL of the publisher | Copy of OpenParlData | SHA-256 of the PDF |
|---|---|---|---|
| 26171 | https://grosserrat.bs.ch/?dnr=19.5497.01 | https://files.openparldata.ch/doc/BS/983545420862d4d42f592e71918230f03e8a4cf46f90e7fd4a380c08e1cc7667 | `f2e5fe4ae6747a886d93bc753795611117fe11b4d23f4ae30d53866fcedb1493` |
| 879163 | https://www.valdebagnes.ch/_doc/4552844 | https://files.openparldata.ch/doc/6037/cc7eb17fcc026efde7c970a1e762e7b70538e06787859cbe44f4fb2b3de11a19 | `7b160c11fcf55c0b70d14c5287589c1bbf7e4e7da9d2e791ba715f667f4ba5d5` |
| 714840 | https://www.bs.ch/api/government-resolutions/document/e159ecf6d8a64510b698e6232b719538-332/5/Dokument | https://files.openparldata.ch/doc/BS/210f283a44ef070a6ac958970636bbf12900f44a6d97f687de9bad9a1b1827bf | `8bb01b408e55d4277550fa7521783392ddae4b8fe881d70165632e36f8391fe2` |

Outputs:

- App: `app/data/samples/<doc>/` has the stored inputs, the stored Apertus states (`states.npz`), the PDF (`source.pdf`) and one image of each page (`page-1.png`) of each sample. The app makes the record with probability, page and span.
- Earlier converter: `samples/<doc>/expected/` (eCH-0295 instance, provenance side file, answers of the rule stage). `samples/<doc>/input/` has the stored Docling output, the atoms and the export record.
- The folder `samples/` has no PDF. The PDF files of the 3 samples are in `app/data/samples/<doc>/source.pdf`, with the SHA-256 of the table above. They are public documents of the parliaments. `app/data/samples/index.json` gives the URL of the publisher of each PDF.

## The method

1. Docling gives the text blocks of the PDF, each with its page and position.
2. A rule chain gives the role of the document and of each block, from the PDF alone.
3. The cascade of eCH-0295 uses the kind of the document and the affair type. It selects the slots that a document can state. The cascade has 7 kinds of document.
4. Rule V5 gives a kind where the rule chain gives none.
5. Rule readers read 7 head values: affair type, title, affair number, submission date, response date, responder and first author. Each reader has tiers.
6. A calibration on 1,793 development documents of 44 parliaments gives each tier a probability (Jeffreys mean). A tier can give the status certain only with 30 or more values with a reference on the development documents. Its precision there must be 0.95 or more. A value of such a tier gets the status certain only if its probability is at or above the threshold a of its field. Only the affair type and the responder have a threshold a. Each other value gets the status unsure.
7. A value of a tier with a probability below 0.5 goes into the label file only, not into a slot.
8. Apertus-v1.5-8B generates no text. A linear head reads its hidden state at the last token of a question. In the run, these heads give values for the affair type and the first author: where the rules find none, or where the rule value has a probability below 0.5.
9. A writer makes the record in Turtle and YAML, a label file and `<doc>.values.ttl`. The label file and `<doc>.values.ttl` give the probability, status, page and span of each value. A validator checks the 3 files.
10. The app shows the record in a browser page. It gives each head value with the rules. For the 3 samples, it can also give block labels from stored Apertus states. A dropped PDF needs `make setup-pdf` and `make run-native`, and no GPU. The result view shows the page image with a box on each value, the values with their probability and the RDF.

Number ids: `cascade.kinds` (7), `design.fixed.addendum_g.certain_tier_units` (30), `design.fixed.addendum_g.certain_tier_precision` (0.95), `values.round4.<field>.calibration.threshold_a` (0.60 for `affair_type` and `responder_name`; no value for the other fields), `design.fixed.writer_floor` (0.5). The report ([technical_report.md](technical_report.md), chapter 2) shows the stages as a figure.

## Where the parts are

| Part | Path | State on 14.10.2026 |
|---|---|---|
| The code of the method of the report: rule chain, cascade, rule readers, combined reader, calibration, writer, validator of the RDF record, the questions to Apertus | [src/converter_gj/](src/converter_gj/README.md) | These files are copies for reading, with the licence line in line 1. The code checks the SHA-256 of its own files, and the licence line changes it. The app runs the files of `app/layout/src/`. |
| The rule for the first author (`m11_values_sponsor.py`) | `app/layout/src/` | This rule is only in `app/layout/src/`. The copy tool cannot make the edit that its copy in `src/converter_gj/` needs. |
| Modules that `src/converter_gj/` imports from other folders | `src/converter/` (21 modules and `m06_ech_profil.yaml`), `src/apertus_head/` (5 modules) | The same source SHA-256. |
| The app: Rust server, page, Python worker, view, contract, container files | [app/](app/DIST.md) | The source tree of the package, copied. `app/layout/src/` has the files that the app runs. 3 of them have a recorded edit: the licence line, a path and a role name. The app has no file of the combined reader. |
| Stored inputs, Apertus states, PDF files and page images of the 3 samples | `app/data/samples/` | Copied. The 3 PDF files are an addition to the source tree of the package ([SOURCES.md](SOURCES.md)). |
| Prompts of the value questions `Q0`, `Q1`, `Q2` | [src/prompts/gj_values_v1_de/](src/prompts/gj_values_v1_de/README.txt) | 6 text files with the licence line, and `template.json` (byte-equal). |
| Prompts of the block roles | [src/prompts/gj_jev_v1_de/](src/prompts/gj_jev_v1_de/README.md) | `src/check_prompts.py` compares them with the template. |
| Validator of the YAML instance | `src/validate_ech.py` | in this folder |
| Numbers | [numbers.json](numbers.json), [numbers.md](numbers.md) | in this folder |
| Limits | [docs/limits.md](docs/limits.md) | in this folder |
| Map of this folder, and the files that are not in it | [docs/repository-map.md](docs/repository-map.md) | in this folder |
| Earlier converter of 12.10.2026 | `src/converter/` | in this folder; [SOURCES.md](SOURCES.md) gives the SHA-256 of each copy |
| Scripts of the first public version (stages 1 to 3) | `src/m0*.py` | in this folder; [docs/stages-1-3.md](docs/stages-1-3.md) |

The files [`SOURCES.json`](SOURCES.json) and [`SOURCES.md`](SOURCES.md) give the source file, the SHA-256 and each edit of each copied file. The fit and measurement code of the value heads is not in this repository.

Validator of the YAML instance:

```bash
uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python src/validate_ech.py FILE [FILE ...]
```

It validates an instance against eCH-0295 version I95 (`ech-0295_affairs/input/schema.yaml` of https://github.com/swiss/political-affairs-ech-group, commit `3cab44d`), class `Container`, with `linkml-validate` of linkml 1.11.1. The exit code is 0 only if each file is valid.

## Results

All values: the one fixed run of 13.10.2026, all 872 documents. The reference is the export. No human checked a value of the run. Each interval is a 90 % interval of a bootstrap by parliament (26 parliaments).

The challenge asks for an evaluation against a hand-checked gold set. The one fixed run has none. Its reference is the export.

Reader with rules only (ids `values.last_run.rules_only.all.<field>.*`):

| Field | Precision (interval) | Found rate (interval) | Correct / documents with a reference | Found rate, development |
|---|---|---|---|---|
| affair type | 0.9431 (0.9139 to 0.9660) | 0.8402 (0.7809 to 0.8943) | 580 of 732 | 0.8624 |
| title | 0.5179 (0.4272 to 0.5972) | 0.9053 (0.8670 to 0.9407) | 406 of 866 | 0.8984 |
| affair number | 0.5275 (0.3493 to 0.6890) | 0.4197 (0.3135 to 0.5389) | 182 of 822 | 0.4719 |
| submission date | 0.5289 (0.4003 to 0.6855) | 0.5161 (0.4194 to 0.6308) | 238 of 872 | 0.6527 |
| response date | 0.5116 (0.3673 to 0.7143) | 0.4057 (0.2598 to 0.6111) | 22 of 106 | 0.9238 |
| responder | 0.9756 (0.9272 to 1.0000) | 0.9152 (0.8333 to 0.9721) | 200 of 224 | 0.9651 |
| first author | 0.8125 (0.7454 to 0.8879) | 0.5607 (0.4555 to 0.6713) | 195 of 428 | 0.8488 |

Combined reader: the rules and the 2 Apertus tiers that entered (ids `values.last_run.combined.all.<field>.*`; development `values.heads2.<field>.combined.*`). The other 5 fields have the values of the reader with rules only.

| Field | Precision (interval) | Found rate (interval) | Share correct (correct of documents with a reference) | Precision, development | Found rate, development | Share correct, development |
|---|---|---|---|---|---|---|
| affair type | 0.9421 (0.9168 to 0.9642) | 0.9208 (0.8952 to 0.9447) | 0.8675 (635 of 732) | 0.9562 | 0.9228 | 0.8823 |
| first author | 0.8243 (0.7597 to 0.8885) | 0.7313 (0.6635 to 0.8072) | 0.6028 (258 of 428) | 0.8756 | 0.8634 | 0.7560 |

Values with the status certain (reader with rules only):

- Affair type: 460 certain values, precision 0.9552. Responder: 175 certain values, precision 0.9714.
- The 5 other fields have 0 certain values.

Spread between the parliaments, reader with rules only (ids `values.last_run.spread.rules_only.<field>.*`). This is information: a tool made it after the run, when the result was known. A parliament counts if it has 5 or more given values with a reference.

| Field | Parliaments that count | Lowest precision | Median precision | Highest precision |
|---|---|---|---|---|
| affair type | 21 | 0.4286 | 0.9841 | 1.0000 |
| title | 25 | 0.0328 | 0.5714 | 1.0000 |
| affair number | 18 | 0.0000 | 0.5228 | 1.0000 |
| submission date | 21 | 0.0000 | 0.8000 | 1.0000 |
| response date | 2 | 0.2500 | 0.2750 | 0.3000 |
| responder | 15 | 0.0000 | 1.0000 | 1.0000 |
| first author | 17 | 0.2000 | 0.9091 | 1.0000 |

Plain meaning:

- For the affair type and the responder, the median precision of a parliament is 0.9841 and 1.0000. For the title, the affair number and the submission date it is 0.5228 to 0.8000, and the lowest parliament is at 0.0328 or less.
- For the title, the affair number and the 2 dates, about half of the given values are the export value. Fewer than half of the documents with a reference get the export value.
- The precision of the title, the affair number and the 2 dates is lower in the run than on the development documents.
- The found rate of the response date and of the first author is lower in the run than on the development documents: 0.4057 against 0.9238, and 0.5607 against 0.8488.
- The 2 Apertus tiers add found values for the affair type and the first author, at a precision near that of the rules.
- A pooled value does not describe one parliament. For the title, the affair number and the 2 dates, the precision of the parliaments is far apart.

Cross-parliament question of the challenge: the report ([technical_report.md](technical_report.md), chapter 6) gives one answer on development documents, with block labels from an Apertus head. These labels were compared with labels from an AI, not with human labels. The documents are a stratified sample of development parliaments; a share is not the share of all documents of a parliament. The answer is not a result of the one fixed run.

Limits of these results (short form; [docs/limits.md](docs/limits.md) gives each with its source and its number ids):

1. Fewer than half of the documents with a reference get the export value. This applies to the affair number, the 2 dates, the title and the first author. The share correct is 0.2214, 0.2729, 0.2075, 0.4688 and 0.4556 (L1).
2. The authors of the value rules of 13.10.2026 read the 44 development parliaments; the 26 parliaments of the run are other parliaments. Addendum I says that these authors opened no file of the 872 documents; no examination compared this statement with the work records. The precision of the title, the affair number and the 2 dates is lower in the run than on the development documents (L2).
3. In the check by eye, each of the 2 AI examiners named 12 of the 50 documents with a kind that looks wrong. Then the cascade does not search some fields. The run did not measure the kind (L3).
4. AI agents had read 116 or more of the 872 documents before the run: 48 validation documents and all 68 group-7 documents. An audit of the work records found a sign of earlier contact for 300 of them. For the other 572 it found none; this is no proof of no contact (L4).
5. The older rule chain, from the earlier converter of 12.10.2026, makes the rule files of the run. AI agents designed it on a list with 38 documents of the run, of 9 of the 18 validation parliaments (L5).
6. AI agents of one model family (Claude Opus 5.5) wrote the rules, the tools, the measures and the audits. AI agents of the same family examined them. No human checked a value of the one fixed run, a tool or a number (L6).
7. The reference is a register. A value can be correct as printed and differ from the register. The check by eye found differences in both directions (L7).
8. No pass limit was fixed before the run. Thus this text does not say that a field passes (L8).
9. The development values are design values. The rule authors read all 44 development parliaments. These values are optimistic (L9).
10. The reference of the affair type is a project map of the export type. The same value is the fit target of the `Q1` head (L10).
11. Group 7 has 68 documents of 8 parliaments, so its intervals are wide. There the responder has 5 wrong values of 25, all of 1 parliament (L11).
12. Each time comes from one laptop clock, and no outside time stamp exists (L12).

Ids of items 9 to 11: `values.round4.parliaments`, `values.last_run.rules_only.group7.documents`, `values.last_run.parliaments.group7`, `values.last_run.rules_only.group7.responder_name.wrong` and `.given`.

## One source of numbers

1. Each result number of the report, of this text and of the 2 texts of the root folder (`README.md`, `docs/about.md`) comes from [numbers.json](numbers.json). [numbers.md](numbers.md) has the same content as a table for a human reader. Other README files can have other numbers, for example `app/README.md`. The app reads the numbers of the fixed run from `app/ui/run_numbers.json`, a copy of display values of `numbers.json`. The app and its screenshots also show the probability of a value and its count of development documents. These come from the calibration file `app/layout/daten/gj_values/round4/calibration_dev_all.json`. Not all of them are in `numbers.json`.
2. An entry has an id, the value as a string, a display form, the unit, the set and n. It also has the reference, the status, the mark and the source file with its SHA-256 and key.
3. A value is a string, so that no tool rounds it again. The tables of this text use the display form.
4. A tool of the private project makes the file from aggregate result files only. Paths that start with `daten/` or `crisp-dm/` are files of the private project. They are not in this repository.
5. No script of this repository compares the numbers of the report or of the README files with `numbers.json`.

## Requirements

| Item | Requirement |
|---|---|
| `make run` | Docker with Compose. The build of the image needs the network. It does not need `make setup`. |
| `make run-native` | cargo with the target `wasm32-unknown-unknown`, `wasm-bindgen` 0.2.127, Python 3.12 with the packages of `app/container/requirements-slim.txt`. For your own PDF also: the Python packages `docling` 2.133.0 and `pypdfium2` 5.14.0 and the 2 Docling models in the local Hugging Face cache (`make setup-pdf` installs them), and `pdftotext`. |
| `make setup-pdf` | `make setup` before, the command `pdftotext`, the network. |
| `make test`, `make run-earlier` | uv 0.11 or later; Python 3.12 (uv installs it); PyYAML 6.0.3; linkml 1.11.1 (with `uvx`); a `python3` command for the checks of `app/`. |
| `make test-app` | cargo and the Rust crates of `make setup`. |
| Hardware | A normal computer. No GPU. |
| API keys | None. |
| Model weights | No Apertus weights. The app has the weights of 2 linear heads of the block labels (`app/layout/daten/gj/design/heads/`) and the stored Apertus states of the 3 samples. |
| Environment variables | The template names `LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY`. No command reads them: the heads of this project need the hidden states of a local model, not the text of an API. |

## Use of Apertus and of other models

1. Apertus-v1.5-8B in bf16 generates no token. A linear head reads the hidden state of layer 20 at the last token of a question (`design.fixed.addendum_i.layer_of_each_head`).
2. In the run, the Apertus heads give values for 2 of the 7 fields: the affair type and the first author. A head tier gives a value where the rules find none, or where the rule value has a probability below 0.5. In the run, the first-author tier replaced 6 such rule values (`values.last_run.combined.all.tier.apertus_q2_sponsor_hi.replaced_rule_values`). The rules give each other value.
3. Value questions ([src/prompts/gj_values_v1_de/](src/prompts/gj_values_v1_de/README.txt)): `Q0` (the kind of the document) did not enter the reader. `Q1` (the affair type where the rules find none) entered. Of `Q2`, only the first author with a high head probability entered.
4. In the run the 2 tiers gave 59 and 79 values with a reference, with precision 0.9322 and 0.8481. A type from `Q1` has no page and no span. Ids: `values.last_run.combined.all.tier.apertus_q1.*`, `values.last_run.combined.all.tier.apertus_q2_sponsor_hi.*`.
5. Apertus can also give each text block a role, for example submitted text or response of the executive. 2 variants of this were measured on 44 validation documents of the run (`sets.reference.validation.documents`). Their reference is a set of block-role labels from an AI. The 2 variants (B1-S and B1-L) were the second and third runs on the same 44 documents. B1-S was designed after the result of the first run was known. Thus their values are information, not values of one planned run. The rules saw 42 of the 44 documents during their design. The run did not use the 2 variants; it used the block roles of the rule chain.
6. One of these 2 variants adds a LoRA adapter to Apertus. The adapter is not published, and it did not enter the run. The value questions use the unchanged model with linear heads.
7. The states were made on one H100 GPU before the run. The app runs no language model on your computer.
8. The app does not apply the 2 tiers of item 4. Its 7 head values come from the rules ([app/README.md](app/README.md), chapter "The modes"). For the 3 samples, 2 linear heads and a sequence step give block labels from the stored states.

Model weights:

- This repository contains no Apertus weights.
- `app/layout/daten/gj/design/heads/` has the weights of the 2 linear heads `D1` and `B1` of the block labels. The weights of the value heads and the LoRA adapter are not published.
- Get access to the weights on https://huggingface.co/swiss-ai/Apertus-v1.5-8B with your own account. Agree to the license (Apache-2.0) and to the Apertus Acceptable Use Policy v1.5.
- The Apertus Acceptable Use Policy v1.5 has duties for each user: indemnity for ETH Zurich and EPFL; the role of an independent controller for personal data in the model output; the output filter of hash values of the Swiss National AI Institute (the policy advises to apply it every six months); the policy goes with each copy of Apertus.

Other models:

- AI agents (Claude Opus 5.5) wrote the code, the rules, the measures, the audits and the texts. AI agents of the same family examined them. No human checked a value of the one fixed run.
- Docling uses its own layout and table models. The OCR engine of the stored Docling output of the samples is Apple Vision (macOS only).
- The reference of the block roles on validation documents is an AI reference: labels that a language model gave. No human checked it.

## The earlier converter (12.10.2026)

The folder `src/converter/` has the earlier rule converter. It gives each line of a document a role and writes an eCH-0295 instance with a provenance side file. Its metadata values come from the export record, not from the PDF. The command `make run-earlier` runs it. `results/stored_results.json` has its values of 12.10.2026 as the earlier state. They are not results of the one fixed run. [docs/stages-1-3.md](docs/stages-1-3.md) and [SOURCES.md](SOURCES.md) describe it.

The public text of 12.10.2026 (commit `2fd48e2`) described this converter and an earlier Apertus head. It gave scores on 26 records of test documents that the author examined. These scores are not a part of the one fixed run, and this text does not use them.

## Licence

- Code in `src/`, the `Makefile` and the prompts in `src/prompts/`: Apache-2.0 (`../LICENSE`). Each code file and each prompt text file has the line `SPDX-License-Identifier: Apache-2.0`. A JSON template has no such line, because JSON has no comment lines; the `NOTICE` table applies to it.
- This text, `SOURCES.md`, the technical report, `numbers.json`, `numbers.md` and `docs/`: CC-BY-4.0 (`../LICENSES/CC-BY-4.0.txt`).
- `samples/`: data of OpenParlData under CC BY 4.0, and texts of the documents. See `samples/NOTICE.md`.
- `app/`: code under Apache-2.0; texts and derived data files (stored states, head weights, calibration files) under CC-BY-4.0, "Source: OpenParlData.ch". `app/layout/quellen/` has copies of 2 files of the eCH-0295 working draft; their licence is not clear. `../NOTICE` gives the rows.
- The full table and the attributions are in `../NOTICE`.
- Hack Apertus terms, chapter 6: https://hackapertus.ch/terms-and-conditions

## Text of the template

The text below is the text of the file `track_2a/README.md` of the Hack Apertus template (https://github.com/HackApertus/project-template, commit `7f23822`). Only the line "Requirements" is filled in.

> # Academia Challenges
>
> Submissions must use the Apertus model family.
> For Track 2 this means that submitted solutions must be built with Apertus. Other open-weights models can be used to support development, e.g. as automatic judges during evaluation. Their role must be clearly described in the submission report.
>
> 💬 In case you have questions, join the conversation on Discord or send an email to “hello@hackapertus.ch”
>
> ## How it works
> Pick from 5 academia challenges provided by Swiss academic institutions:
>
> - **FHGR:** AI-Powered Job Interview Coach
> - **OpenParlData:** Extracting Parliamentary Affairs from PDFs into One Common Structure
> - **OST:** Multilingual Natural Language Inference over Swiss Official Voting Booklets
> - **UZH:** Detecting Cross-Lingual Semantic Differences in Swiss Government Websites
> - **ZHAW:** See It, Say It, Pick It: Vision-Language Grounding for a Real Robot Arm
>
> The challenges incl. submission and judging criteria are described in our **Getting Started guide**:
> https://hackapertus.notion.site/getting-started-guide-onlinehack
>
> ## Run it
>
> Keep `track_2a/` as it is: don't rename it or move its files, just delete the
> other track directories.
>
> From the root of the project:
>
> ```bash
> make run
> ```
>
> Fill in the [Makefile](Makefile) so that it works on a clean checkout. It is
> expected to run the project in a Docker container, since that is how the judges
> will run it, without relying on anything already installed on your machine.
>
> Requirements: see the chapter "Requirements" above.
>
> ## Data
> The `data/` directory must not exceed 100 MB.
>
>
> ## 📦 Submission Requirements & Deliverables
> ❗️ Submissions are not handled on Devpost. Submit through our website only:
> http://hackapertus.ch/online-hack/submissions
>
> Requirements differ by challenge. See the description of the challenge you are entering for the exact deliverables.
>
>
> ## ⚖️ Judging Criteria
> Judging criteria also differ by challenge. See the respective challenge description.
>
>
> ## Support
>
> **Licensing requirements**
> Please check our Terms & Conditions (6. What you build is open source):
> https://hackapertus.ch/terms-and-conditions
>
> ## FAQ
> 💡 https://hackapertus.ch/faq
>
> ## Contact
> 💬 In case you have questions, join the conversation on Discord or send an email to “hello@hackapertus.ch”


## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 14.10.2026, from the records of the private project. An AI agent changed the chapter "Run it" in the afternoon of the same day. In the evening, an AI agent changed the states of `make run` and `make run-native`. On 15.10.2026 an AI agent added `make setup-pdf`. Later on 15.10.2026, an AI agent corrected sentences after an audit. The private project is the project folder of the author. It is not public.
- No human examined this version of the text.

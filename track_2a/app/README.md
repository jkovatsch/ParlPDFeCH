# ParlPDFeCH package: a parliament PDF becomes eCH-0295 data, on your computer

> **State of the commands on 15.10.2026.** The folder `track_2a/app` of the public repository is the source tree of this package (`make dist-src`).
> `make run` (Docker, target `slim`) ran one time on one Mac (Apple silicon, Docker server 29.2.1) on 14.10.2026. It ran in a clone of GitHub at commit `10e07b4`. The 3 samples in the 2 modes gave 6 valid records.
> `make run-native` ran in fresh clones of GitHub at commit `10e07b4` (14.10.2026) and `3eff351` (15.10.2026), each time with 6 valid records.
> On 14.10.2026 a private build pipeline on Linux built the image from the source tree of the package. The push to the registry failed. Nobody started this image.
> Not run: `make run-full`, `make check-offline`, `make stop` and `make logs`. Nothing was run on Windows.
> The file `track_2a/README.md` of the public repository (chapter "The commands and their state") gives the details.
> `STATE.md` is the work record of 13.10. and 14.10.2026. Its lines on the container, the pipeline and Linux are older than these runs.

## What this is

1. ParlPDFeCH converts a PDF document of a Swiss parliament into RDF data in the form of the working draft eCH-0295.
2. Each label that a code rule or a read-out decided has a probability, a page and a character range. The probability is the calculated probability that the label agrees with the reference labels of the project (labels that a language model gave to the development documents; the pages also name them "AI reference").
3. Code rules read the head values of the record from the PDF: the affair type, the title, the affair number, the submission date, the response date, the responder and the first author. Each value has the wording of the PDF, a page and its place in the text. The record holds a name or a title as the PDF prints it; an affair type is a value of the eCH-0295 list and a date is a calendar day, and the page shows the printed wording next to it. If the rules find no value, the entry is absent, and the record says "not found in the PDF" with a reason. The OpenParlData export is used only to check the values of a sample.
4. The probability of a head value is the share of development documents in which a value of the same rule tier was equal to the OpenParlData value. The page shows it as the stored decimal with the word certain or unsure. A value of a rule tier with a stored probability below 0.5 is not written to the record: the page shows it as a weak candidate (`STATE.md` chapter 12).
5. The package has a Rust web server, a Python worker and a browser page.
6. In the browser, a Rust module compiled to WebAssembly reads the RDF file a second time and counts its parts.
7. This version converts 3 sample documents with stored inputs. With `make run-native` and more packages (next chapter), it also converts a PDF that is not a sample, with code rules only. It runs no language model on your computer.

## Start with no container

```bash
make run-native PORT=8080
```

Then open this address in a browser:

```
http://127.0.0.1:8080/app/
```

- In the source tree (the folder `track_2a/app` of the public repository), the command checks the code layout of the folder `layout/`. Then it builds the server and the WebAssembly bundle with cargo and starts the server on `127.0.0.1`. Stop it with Ctrl-C.
- It needs cargo with the target `wasm32-unknown-unknown`, the command `wasm-bindgen` 0.2.127, `wasm-opt` (optional) and a Python 3.12 with the packages of `container/requirements-slim.txt`. In the public repository, `make setup` in the folder `track_2a` makes such a Python.
- In the package inside the private project, the command also makes the code layout and the sample data from the project folder. There it needs uv with the Python packages of the project.
- From the folder `track_2a` of the public repository, and in the private project, cargo runs with `--offline`: the command makes no download. `make setup` or `make fetch` downloads the crates before.
- The 3 samples need nothing more.
- The conversion of your own PDF needs more on the computer. It needs the Python packages of `container/requirements-full.txt` (`docling` 2.133.0, `pypdfium2` 5.14.0) and the command `pdftotext`. It also needs the two Docling models in the local model cache of the user account (the Hugging Face hub cache). Without the Python packages, the job stops with the note `pdf_reader_absent`. If a model is absent, the job ends with the message "The converter stopped".
- In the public repository, `make setup-pdf` in the folder `track_2a` installs these packages and the 2 models. It does not install `pdftotext`. On 15.10.2026 it ran on one Mac, in a clone of GitHub at commit `3eff351` (with the target added as a patch). Then `make run-native` converted 2 copies of sample PDFs with one added comment line, with 2 valid records.
- On macOS with the Python package `ocrmac`, the conversion decides for each page if it reads the text layer of the PDF or uses the text recognition of macOS (Apple OCR). The worker reads the hub cache of the user account, also the two token files of that cache; the trace of one run showed no connection to another host.
- The server answers a request only if its `Host` header names `localhost`, `127.0.0.1` or `[::1]` (another name: the variable `PARLPDFECH_ALLOWED_HOSTS`). The exception is `/healthz`, which answers for each host name. The server refuses a POST or DELETE that comes from a page of another site.
- The API has no authentication. The default listen address is a loopback address; the server writes a warning at the start for another address.
- One server process uses one work folder: a second start with the same work folder stops with exit code 2 and changes no file (lock file `.lock` in the work folder).

## Start with a container (run one time on one Mac)

On 14.10.2026, `make run` (target `slim`) ran one time on one Mac with Apple silicon, in a clone of GitHub at commit `10e07b4`. The 3 samples in the 2 modes gave 6 valid records. `make run-full` and `make check-offline` were not run. The chapter "Estimates and one run (container)" gives the time and the image size of this one run.

You need Docker (Engine 23 or later, with Compose 2.17 or later), `make` and a network connection for the build. In the source tree, the code layout is the folder `layout/`. In the private project, it is the folder `build/layout`, and `make layout` makes it.

```bash
make run
```

The address is then `http://localhost:8080/app/`.

- `make run` builds the image of the target `slim`, starts the container and prints one line with the address. The target `slim` converts the 3 samples only.
- `make run-full` builds the target `full`, which is prepared for the conversion of your own PDF with no OCR. It was not run.
- Another port: `PARLPDFECH_PORT=9090 make run`.
- `compose.yaml` publishes the port on `127.0.0.1` only. A start with `docker run -p 8080:8080` opens the API, which has no authentication, on all network interfaces of your computer; use `-p 127.0.0.1:8080:8080`.
- The build downloads files (chapter "Downloads at build time"). The run is written to make no request to another host.

## What you see

The app has two main routes (14.10.2026):

| Route | Content |
|---|---|
| `/app/#/` (start) | One sentence on what goes in and what comes out; a small picture of the flow (PDF, up to 7 values with a probability, RDF); the 3 samples as large cards that open the result view; the box "How often correct?" with the share correct of the 7 fields in the one fixed run of 13.10.2026 (code rules only; from `ui/run_numbers.json`); the button for your own PDF. Each topic has a link "more" to the page "About" (`#/about/method`, `#/about/numbers`, `#/about/limits`, `#/about/technical`), which holds the long texts. |
| `/app/#/view/<record_id>` (result view) | Three places: on a wide screen the PDF and the values side by side and the RDF below them, stacked on a narrow screen. A line under the heading says where the values come from (code rules; Apertus gives only the labels of the text blocks of a sample). With no title from the PDF, the heading is the OpenParlData title of a sample or the weak candidate, with a line that says so. The PDF: the image of each page with a coloured box on each value and a grey box on each text block. With no image, the page draws the lines of the text layer and says so. The values: field, value as printed, probability (a bar and the stored decimal), the word certain or unsure, page. A line below each row gives the development documents behind the number (a pale bar for fewer than 30). It also gives the precision of the field in the fixed run (correct of the given values) and, for a sample, the comparison with OpenParlData. A line for each field that was searched and not found, a weak candidate and the body that a proposal addresses. One line for the fields that the role of the document does not search. The RDF: the eCH-0295 record and the new file of the values with probabilities, as Turtle text with colours, each one for download. A row, a box and the triples of one value have the same colour; a click on one of them marks the other two. A link opens the technical view of the same record. |

The technical view (`#/record/<record_id>`, the result page of the app before 14.10.2026) keeps all its parts:

| Screen | Content |
|---|---|
| Start (before 14.10.2026) | Three buttons: try a sample, convert your own PDF, what is this. Some sentences say what this start of the package converts (from `/api/health`). A list explains the words of the pages. These texts are now on the page "About". |
| Samples | One card for each sample document. Each card has one button for each mode. If the two results of a sample are on the computer, the card shows the counts of the two results. |
| Own PDF | One file, the limits, the button "Convert". |
| Stages | The 6 steps of a conversion and the time of each step. |
| Result | First the eCH-0295 record. At its top the part "What this document can state" shows the cascade of this record in plain words: the kind of this document, where the kind comes from (the rule chain, or rule V5 with its 2 facts), the affair type, the steps that a document of this kind can state, and each of the 7 entries that the rules read with its state: read from the PDF (value, stored decimal, the word certain or unsure, the button "Show on the page"); the rules found no value; the rule of the entry does not read a document of this form; a weak candidate that is not written; not searched in this kind of document (with the kind). One line gives the count of the entries that are only in a register. The details part "The whole cascade" lists the 5 stages. Then 3 tables (the affair, the submission, the response step): each entry with its state (read from the PDF, not found in the PDF, not searched in this kind of document, only in the register). A value row has the value as printed (and the value of the record, if its form is different: a list value, a calendar day), the stored decimal with the word certain or unsure, the count of development documents behind the number, the button "Show on the page" and, for a sample, the comparison with OpenParlData. A weak candidate has its own row text: it is not in the record. The body that the text of a proposal addresses has its own row text also: it is a candidate, and the record has no response step. Then a drawing of the page from the places of its lines (not an image of the PDF; the result view shows the image), and one card for each label ("The text parts"). Then each stored value with its source, the downloads, the checks and the RDF panel. |

A label card shows the selected answer, the status word (certain or unsure), the stored probability as a decimal, all other answers with their numbers, and the part that made the decision (a code rule, or a read-out of Apertus).

Downloads of each result: TriG (all parts, with labels and probabilities), Turtle (the eCH-0295 record only), RDF/XML, and a ZIP file with all files and their SHA-256 values. A record with values from the PDF (since 14.10.2026) also has `<doc>.values.ttl` (the values with their probability, page and character span; form `parlpdfech-values-ttl/2`), `source.pdf` (the PDF; the download has the name `parlpdfech-<record_id>.pdf`) and `page-<n>.png` (one image of each page; made with pypdfium2).

The RDF panel runs in your browser. It parses the TriG file with Rust code (WebAssembly), counts the statements of each named graph and the labels of each source, compares the counts with the manifest of the record, and runs SPARQL queries. If WebAssembly does not start, only this panel shows a message.

The pages are in English and in German (`?lang=en`, `?lang=de`).

## The modes

| Mode | In this package | What it does |
|---|---|---|
| 1. Sample with stored Apertus results | yes (run) | The package holds the stored states of Apertus-v1.5-8B for the 3 samples. The states were made on an H100 GPU. On your computer, two read-out heads (linear models) and one sequence step calculate the block labels and the number of the document label from these states on the CPU. The label "response of the executive" is a stored value; the package does not calculate it. No language model runs. |
| 2. Sample with code rules only | yes (run) | The same 3 samples. All labels come from code rules. The probabilities come from counts of the rule on the development documents. No Apertus state is used. No label of a block has the word "certain" in this mode; a value that is read from the PDF has its own limit in each mode. |
| 3. Your own PDF with code rules only | `make run-native`: yes (run on one Mac with synthetic PDF files and with the 3 sample PDF files; on 15.10.2026 also after `make setup-pdf`, with 2 changed copies of sample PDFs). Image target `full`: prepared, not run. Image target `slim`: no | Docling reads the PDF on your computer; then the same code rules as in mode 2, and the value readers. The record has one affair with the values that the PDF prints, and the two steps with their text blocks. It has no comparison with a register (`CONTRACT.md` chapter 16). The kind of the document comes from the code rules and selects which values the rules search. A type or a number that the rules do not find in the PDF is a recorded gap. The record does not say if the PDF is a development document. The probabilities were not checked on such a document. |
| 4. Apertus on a GPU | no | Not implemented in this version. |

## Limits

- The package does not run Apertus on your computer. The weights of Apertus-v1.5-8B (17.2 GB, read in the package plan) are not in the package.
- The container path ran one time, on one Mac with Apple silicon (`make run`, target `slim`, 14.10.2026). The container ran in the Linux system (arm64) of the Docker server of that Mac. On 14.10.2026 a private build pipeline on Linux converted the 3 samples with the worker and built the image for x86_64. The push to the registry failed, and nobody started that image. Nothing else ran on Linux or on x86_64. Nothing ran on Windows.
- The image target `slim` does not convert a PDF that is not one of the 3 samples; the answer is "not in this package".
- The head values come from code rules. A rule can read a wrong value, and it can find no value where the PDF prints one.
- The probabilities come from the calibration file of the product, `daten/gj_values/round4/calibration_dev_all.json` of the project (1,793 development documents, reader version `m11-values-cascade-4`). Origin of this file: development documents of 44 parliaments that the rule authors read. The rule files of the reader are made from the PDF alone. The one fixed run of 13.10.2026 measured the rules on 872 documents of 26 other parliaments (`track_2a/README.md` of the public repository, chapter "Results"). AI agents had read some of these documents before the run: 116 or more. Precision is correct / (correct + wrong). For each of the 7 fields, the precision of the reader with rules only was lower than on the development documents. Two examples: affair number 0.5275 (development documents 0.7591), submission date 0.5289 (0.6609). The share correct (correct / documents with an export value) of the run was 0.2214 for the affair number and 0.2729 for the submission date. The values of all 7 fields are in `track_2a/numbers.json` of the public repository (ids `values.last_run.rules_only.all.<field>.precision` and `.share_correct`).
- The kind of the document selects which values the rules search (the cascade; its design text `crisp-dm/04-modeling/ech-cascade.md` is a file of the private project and is not published). Code rules decide the kind: the rule chain, or rule V5 if the rule chain made no decision. Rule V5 uses 2 facts of the PDF: a type word of a proposal of a member, and a responding body that a response rule finds. With no type word, rule V5 gives the kind response only for an explicit response cue: a heading or a phrase of the first lines says that the executive answers. A signature of the executive alone changes nothing. eCH-0295 has no list of document kinds: this first step is a choice of the project. A wrong kind gives a wrong selection: for example a document with a proposal and a response that the rules call a proposal gets no response step. If the rules find signs of a response in a document of the kind proposal, the page shows a notice; the kind does not change.
- A value that the rules search can have the reason "the rule of this entry does not read a document of this form". Examples: a head that starts with the word Petition; a response with no author in its head. It is a result of a search. The record has no value for it.
- A text block whose text entry the cascade does not give to the kind of the document is not written to the eCH-0295 record. It stays in the provenance file. A document of the kind other document with body text only then gets a record whose affair has an address and no other entry.
- A response document that prints the authors and the date of the proposal in its head states them: the record then has a submission step with the sponsorship and the date and with no text block. This is a choice of the project (cascade rule R30), not a rule of the standard. On the development documents (rules of round 3; the product uses the rules of round 4), the kind response has 195 first authors. 39 of them come from the address block of the reply letter (the member that the letter addresses), not from a head line.
- A document of the kind proposal gets no response step. The body that its text addresses is a candidate label only. This decision (D3) has a cost. An AI agent measured it on the 1,018 development documents of the kinds proposal and executive proposal (rules of round 3; the product uses the rules of round 4). The rules would find a responding body by a response rule in 193 documents: 176 equal to OpenParlData, 4 different, 13 with no value there. They would find a response date in 122 documents: 39 equal, 20 different, 63 with no value. These values are not read.
- For the kinds committee report, minutes and other document the rules search no submission date and no first author. On the development documents the rules would read 29 such dates (20 equal to OpenParlData, 9 different) and 32 such authors (20 equal, 3 different, 9 with no value in OpenParlData); these values are not read.
- The reference of these probabilities is the OpenParlData export. It is a register value. It is not in each case the value that the PDF prints. The one fixed run of 13.10.2026 has the same reference. This reference is not a hand-checked gold set.
- A sample is a development document. The probability that a record shows for a value is the number of its rule tier over all development documents, for every document, also a sample. Thus the number of a sample counts the sample itself; the page says so in the row of the value. The floor uses the same number.
- A value of a rule tier with a stored probability below 0.5 is not written. For the samples: the title of 714840 (tier probability 0.1473) is a weak candidate. Sample 879163 has no affair number (the rules found none: a recorded gap). Sample 26171 has no response step: the body that its text addresses ("Regierungsrat") is a candidate label.
- eCH-0295 requires the affair type and the affair number. A PDF for which the rules find none gets a record with a recorded gap (`conformance` `i95_with_recorded_gaps`). Such a record is not valid against eCH-0295 with no change.
- 21 of the 52 entries of the affair and of its two steps have no rule: the package does not search the PDF for them. The page lists them with the reason.
- Sample 879163 has a recorded gap for the affair number.
- The package holds the export records of the 3 samples only. Your own PDF has no comparison with a register.
- The probabilities of your own PDF were not checked on any document outside the development documents. For the document label of your own PDF, the counts of the rule come from runs of the rule with export values; for your PDF the rule had none.
- The image has no OCR engine. With no container on macOS, the conversion of your own PDF can use Apple OCR. The samples hold stored text; for 2 of the 3 samples a text recognition that ran before gave a part or all of this text.
- No PDF of a parliament other than the 3 samples was converted with this package. A scan with letters and a PDF of about 20 pages were not run.
- The SHACL check (C10) has the state "skipped" in each record.
- The sentence "the package sends no file and no result to another computer" rests on the code of the server and of the page (no address of another host), and for the worker on a trace of the Python process on one Mac (no connection to another host). The trace does not see native code of Docling, of torch or of the text recognition. The trace was not made in a container.
- One browser engine (Chromium) was used for the checks of the page. Firefox, Safari and a screen reader were not run.
- The download files of the samples are the files of the converter: they hold working names of the project, project-relative paths and the internal status text (`STATE.md` chapter 6).

## Status of the results

- Each label that a code rule or a read-out decided is a proposal with a probability. The other labels (identifiers, constants, copies of the PDF wording) have no probability.
- Each head value is a proposal of a code rule. Its probability comes from a measurement on development documents with the OpenParlData export as the reference: the file `daten/gj_values/round4/calibration_dev_all.json` of the code layout (development documents of 44 parliaments that the rule authors read; see "Limits").
- The 3 samples are development documents. The read-out heads were fitted on them. Thus their probabilities are not a result on a new document. The pages read this fact from the data field `in_sample` of each sample.

The machine fields `run.status` (view), `status` (`/api/health`) and `status` (`convert.json`) hold an internal status text of the work. The page does not show it.

## Values measured with this package (earlier record form, 13.10.2026)

Measured on 13.10.2026 on one Mac (Apple silicon, macOS, no container), through the server of the package, one run each. These values are history. They are of the earlier record form, before the records held the head values that are read from the PDF. The counts of a present record are different: its result view and its technical view give them. `STATE.md` has the full list.

| Value | Result |
|---|---|
| Sample 26171, mode 1: labels | 33; of these 15 with a probability (9 certain, 6 unsure) and 18 with none |
| Sample 879163, mode 1: labels | 42; of these 26 with a probability (12 certain, 14 unsure) and 16 with none |
| Sample 714840, mode 1: labels | 18; of these 10 with a probability (6 certain, 4 unsure) and 8 with none |
| Samples, mode 2: labels with a probability | 14 of 32, 25 of 47, 9 of 21; 0 certain |
| Mode 2: the selected answer is not the answer with the highest number | 13 of 14, 6 of 25, 5 of 9 labels |
| Time for one sample, from the request to the end of the event stream | 3.2 to 3.9 s (6 runs: 3 samples, 2 modes) |
| Own PDF: a synthetic PDF with 1 page and 13 lines | 14 labels (0 certain, 11 unsure, 3 with no probability), 1,307 statements (the gate run of `STATE.md` chapter 10.4; 10.1 s in that run). An earlier run: 9.6 s, of this 5.7 s for the start of Docling |
| The 3 sample PDF files as PDFs that are not in the package | the blocks equal the stored blocks (13 of 13, 24 of 24, 8 of 8); the labels with a probability equal the result of mode 2 (14 of 14, 25 of 25, 9 of 9) |
| The files of a sample against the reference run of the project | the 3 YAML files, the TriG file and the Turtle file are byte-equal after the replacement of the run time; the 2 RDF/XML files are isomorphic |
| Server binary; WebAssembly module | 2,961,168 bytes (the build of `STATE.md` chapter 10.5); 2,067,498 bytes |

## Values of the project runs (not measured with this package)

These values come from runs of the project, not from a run of this package. The column "Source" gives the source of each value. One source is `track_2a/numbers.json` of the public repository. The other source is the package plan of the private project (file `crisp-dm/06-deployment/package-plan.md`; it is not published), which names each value as measured. No check of this package covers them. The run records behind the values of the package plan were not opened for this file.

| Value | Result | Source |
|---|---|---|
| Decisions from stored states (heads and sequence step) | median 0.014 s for each document | package plan, chapter 2.2 |
| Batch conversion of 13.10.2026 from stored inputs, with stored Apertus states and the read-out B1-S (not code rules only) | median 1.73 s for each document in a worker (1,793 development documents, 6 worker processes) | `track_2a/numbers.json`: `conv.worker_seconds_median`, `conv.documents`, `conv.workers` |
| Apertus-v1.5-8B in bf16 on an H100 GPU (not a function of this package) | 18.6 to 21.0 GB of GPU memory at the peak; 1.77 to 2.34 s for each document | package plan, chapter 2.3 |
| Documents that are all OCR pages | 297 of 2,512 | package plan, chapters 2.4 and 5 |
| Docling models in a local cache | 506 MB | package plan |

## Estimates and one run (container)

The estimates were written before 14.10.2026. The last column gives the values of the one run of `make run` on 14.10.2026: one Mac with Apple silicon, an image for arm64.

| Value | Estimate | One run on 14.10.2026 |
|---|---|---|
| Image of the target `slim` | about 0.5 GB | 152,210,215 bytes (`docker image inspect`) |
| Image of the target `full` | 3 to 4 GB | not built |
| Time of `make run` | 10 to 25 minutes | 2 min 3 s from the start of the command to the healthy container (log of the run). No build step came from the build cache. |
| Memory of the container, target `slim` | less than 1 GB | not measured |

## Downloads at build time (container)

`make run` downloads these files one time. All sizes are estimates; none is measured. The exact list is in `container/BUILD-NOTES.md`.

| What | Source | Size (estimate) |
|---|---|---|
| Base image `rust:1-bookworm` | Docker Hub | 0.5 GB compressed |
| Base image `python:3.12-slim-bookworm` | Docker Hub | 30 to 50 MB compressed |
| Rust target `wasm32-unknown-unknown` | static.rust-lang.org | 20 to 40 MB |
| Rust crates of `Cargo.lock` and of the command `wasm-bindgen` 0.2.127 | crates.io | 50 to 150 MB |
| Python packages of `container/requirements-slim.txt` (87 packages) | pypi.org | 100 to 200 MB |

`make run-full` adds: 3 Debian packages with their dependencies (deb.debian.org, less than 100 MB), the Python packages of `container/requirements-full.txt` with the CPU build of torch (pypi.org and download.pytorch.org/whl/cpu, about 0.5 GB), and 2 Docling models (huggingface.co; 506 MB).

`make check-offline` is written to convert one sample in a container with no network. It was not run.

## Stop and remove (container, not run)

```bash
make stop      # stops the container; the results of the session are in memory and are lost
make remove    # also removes the images parlpdfech:slim and parlpdfech:full
```

To remove the base images and the build cache also:

```bash
docker image rm rust:1-bookworm python:3.12-slim-bookworm
docker builder prune
```

`docker builder prune` removes the build cache of all your Docker projects, not only of this one.

## Other commands

| Command | Function | Run |
|---|---|---|
| `make run-native` | No container: builds and starts the server on `127.0.0.1:8080` (another port: `PORT=8894`). | yes: in the private project (`STATE.md` chapter 3 says how the server of the last checks was started) and in fresh clones of GitHub |
| `make test` | Tests with no container. In the source tree: the layout check, the cargo tests of the two crates, the example view against its schema and one start of the seed script. In the private project also the static check of the page and the view check. | yes |
| `make check-dist`, `make check-layout` (source tree only) | They compare each file of the tree with `DIST-MANIFEST.json`, and each file of `layout/` with its manifest. | yes (`make test` in the folder `track_2a` of the public repository runs them) |
| `PARLPDFECH_VALUES=off make run-native` | Starts the server with the earlier record form (head values from the export; a PDF with no export record has no affair). `make gate` needs a server that was started this way. | yes, in the private project (the gate of `STATE.md` chapter 11) |
| `make logs` | Shows the log of the container. | no |
| `make check-offline` | Builds the target `slim` if necessary and converts one sample in a container with `--network none`. | no |
| `make run-full` | Builds and starts the target `full`. | no |

The commands below are tools of the package inside the private project. The source tree and the public repository do not have them (`DIST.md` of the source tree lists the tools that it leaves out).

| Command | Function | Run |
|---|---|---|
| `make gate PORT=8894` | Runs through the API of a started native server with curl and makes the comparisons of the gate (`contract/tools/gate_api.sh`, `contract/tools/gate_compare.py`). The work folder of the server must hold no record at the start. `GATE_REFERENCE=<folder>` adds the comparison with a reference run of the project. `GATE_OUT=<folder below package/>` sets the folder of the saved answers (default `work/gate`). | yes |
| `uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/check_values.py --ocr none` (from the project folder) | Checks of the record with values that are read from the PDF: the 3 samples in the two modes, each sample with the switch off, a trace, 6 synthetic PDF files (one of them a proposal that addresses the executive, one a response whose head prints the author and the date of the proposal). It checks the cascade, the response step rule and the probabilities of each record. | yes |
| `python package/contract/tools/gate_values.py --port 8894` (from the project folder, project Python) | The same record form through the API of a started server (values path on): view, checks, cascade, files, bundle, and the validator of the project in its own process. | yes |
| `python package/worker/layout_add.py --values`, then `make layout` | Puts the files of the value readers and the calibration file of the values into the list of the code layout. Then it makes the layout. Run the two commands after each change of one of these files. | yes |
| `make layout` | Makes the code layout `build/layout` (needs the project environment). | the script behind it, with `--update` and `--check` |
| `make dist-src` | Writes the self-contained source tree (next chapter). | yes |

The container (read in `compose.yaml`): user 10001, read-only root file system, no Linux capability, results in a memory file system of 256 MB.

## Source tree and hosted site

- In the private project, `make dist-src` writes the folder `dist-src/`: a self-contained source tree with the sources of the package, the code layout as plain files (`layout/`), the 3 samples and `DIST-MANIFEST.json`. The manifest gives the count of the files. The tree builds with no project folder around it; `dist-src/DIST.md` has the commands. `make -C dist-src check-dist` compares each file with the manifest. The tool refuses a target folder that has content and no `DIST-MANIFEST.json`. Run: yes (`STATE.md` chapter 10.4).
- The folder `track_2a/app` of the public repository is such a tree. Its `DIST-MANIFEST.json` records the changes for the publication (keys `publication_edits` and `publication_additions`).
- The tree holds the code layout: converter files with working names and internal notes, and ids and block labels of 193 development documents. `STATE.md` (chapter 9, decision 1) gives the question of 13.10.2026 on its publication. Since 14.10.2026 the public repository holds the tree.
- In the private project only: `deploy/` is a kit for one hosted site that shows the 3 samples only. It has a pipeline file (Kaniko) and Kubernetes manifests, with `deploy/RUNBOOK.md`. The folder is not in the source tree; the tree has a copy of its pipeline file (`.gitlab-ci.yml`). On 14.10.2026 this pipeline built the image on a private GitLab server, and the push to the registry failed. No manifest was applied. The folder names parts of a private infrastructure.
- Two settings of the server are for such a site (`CONTRACT.md` chapters 2.1 and 14): `PARLPDFECH_READONLY=1` (the server takes no file and refuses each DELETE; the page hides the upload form, the stop button and the delete button, and its entries for an own PDF name the run on the own computer) and `PARLPDFECH_SAMPLE_RUNS=off` (the server starts no run for a sample whose result is ready; error code `sample_runs_off`). Measured with no container on one Mac.
- A third setting, `PARLPDFECH_HOSTED=1`, says that the server is not on the computer of the reader. The page then uses its texts for a hosted site ("on the server of this site") in place of the texts that say "on this computer" (`CONTRACT.md` chapter 15). Without it each text describes a local run.
- One server can give the pages about the project and the app (`CONTRACT.md` chapter 15): `PARLPDFECH_SITE_DIR=<folder with a built static site>` puts the site at `/` (German pages at `/de/`), the app stays at `/app/` (`/app/?lang=de`), and the app shows a link "About this project". With no site folder `/` redirects to `/app/`. `make run-native SITE_DIR=<folder>` starts it so; `make dist-src SITE_DIR=<folder>` copies the site to `dist-src/site/`, and the image of that tree holds it. The site folder is not part of this package: the pages are built outside it. Measured with no container on one Mac (`STATE.md` chapter 10.5); the image lines were not run.

## Files

| Path | Content |
|---|---|
| `STATE.md` | What is built, what was run with which result, what does not work, the decisions for the owner (chapter 19: the start page and the result view of 14.10.2026) |
| `EXAMINATION.md` | Each finding of the examinations with its decision |
| `CONTRACT.md`, `contract/` | The interfaces of the parts, the view schema, the error codes, the gate tools (the gate tools are in the private project only) |
| `server/` | The Rust web server (axum) |
| `rdfcheck/` | The Rust crate for WebAssembly (oxigraph) |
| `ui/` | The page: HTML, CSS, one script, the texts in English and German. The server gives the page files only; it does not give `ui/README.md`, `ui/tools/` and `ui/fixtures/` (files of the development) |
| `worker/`, `view/` | The Python worker and the view function |
| `data/` | The stored inputs of the 3 samples, and the PDF and the page images of each sample (`source.pdf`, `page-<n>.png`; not inputs of the conversion) |
| `container/` | Requirements files, start script, build notes, the files of the source tree |
| `deploy/` | Private project only: kit for a hosted sample site (no manifest applied; not in the source tree) |
| `dist-src/` | Private project only: the self-contained source tree that `make dist-src` writes (not tracked) |

`STATE.md`, `EXAMINATION.md` and `CONTRACT.md` are package records that AI agents wrote during the work. They keep internal role names and status words of the work. They are not written to the STE rules. A state line in these records has the date of its chapter; the top of this file gives the later state of the commands.

## Licences

- Code of this package: Apache-2.0 (`Cargo.toml`). In the public repository, the file `NOTICE` gives the licence of each part.
- Rust crates: `Cargo.lock` names each crate and version. Python packages: `container/requirements-slim.txt` and `container/requirements-full.txt` name each package and version. Each has its own licence. A licence report on these lists was not run.
- Apertus-v1.5-8B: Apache-2.0 with a use policy (read on the model card). The package holds no weights.
- eCH-0295: a working draft of the association eCH.
- In the public repository, the derived data files of `data/` and `layout/daten/` have the licence CC-BY-4.0, with the source OpenParlData.ch (file `NOTICE`). These are the stored Apertus states, the head weights, the calibration files and the records of the 3 samples. The folders of `data/samples/` also hold the text, the PDF file and one page image of each of the 3 documents. These are not derived data. For these copies, `NOTICE` (chapter 3) says that the licence is not clear.
- In the public repository, the texts of this package (the `.md` files) have the licence CC-BY-4.0 (file `NOTICE`).

# ParlPDFeCH

Target: parliamentary affairs from PDF to eCH-0295, extracted with Apertus by readout, every value with its source.

- Author: Jonathan Kovatsch, as a private person. Copyright 2026 Jonathan Kovatsch (see `NOTICE`).
- Challenge: Track 2A (OpenParlData) of the Hack Apertus online hack, "Extracting Parliamentary Affairs from PDFs into One Common Structure". Challenge page: https://hackapertus.notion.site/track-2a-openparldata
- Project folder for the judges: [track_2a/](track_2a/README.md). Run: `make setup`, then `make run` in `track_2a/`.
- State of this text: 12.10.2026. It is the version for the submission of 13.10.2026.

## What ParlPDFeCH is

ParlPDFeCH is a converter for PDF documents of parliamentary affairs. The documents come from parliaments of the Swiss Confederation, the cantons, the municipalities and Liechtenstein, through OpenParlData. The output is data to the working draft eCH-0295 (version I95), with a provenance side file.

Principles:

1. The converter writes no text. The text of a value is the wording of the PDF.
2. Each value has evidence: for a text, the atoms of the PDF with page, frame and character range; for a metadata value, the record and the field of the OpenParlData export.
3. Docling converts the PDF into blocks. Code divides the blocks into atoms: one line of a block or one row of a table.
4. Code rules make most decisions. Apertus-v1.5-8B makes a decision by readout: code reads the probabilities of a fixed list of answers, or a trained head reads a hidden state. Apertus writes no text.
5. Each readout gets the whole document first and the question last.
6. A value with a low probability gets the value status `unsure`. The converter does not guess.
7. The project uses Apertus in bf16 and no quantized model. The CSCS inference API does not document its precision ([track_2a/README.md](track_2a/README.md)).

## Current status

Facts on 12.10.2026:

- The repository holds a converter that runs on 3 samples: a rule stage at isolation level L9 and an eCH-0295 writer. `make run` converts the samples from their stored Docling output, validates the output against I95 and the profile, and prints the stored results. It needs no network, no GPU and no model.
- The output of the 3 samples is valid against I95 and against the profile (`linkml-validate`).
- Path 1 (the converter): gate 3a version 4 is OPEN. The frozen converter ran once on 40 selected test documents and claimed 26. The author examined the 26 gold set records. The blind repetition and the acceptance of the reference did not take place, so the gate has no measurement.
- Path 2 (Apertus head, task R2): the gate is OPEN. On the validation set, the head has a balanced accuracy of 0.919, against 0.899 for the zero-shot Apertus readout and 0.932 for the best rule. The final run on the test parliaments is sealed and not measured.
- Path 2, task R1 (the recommendation of the executive): stopped, with a negative result.
- Scores after the freeze, on the records of the 26 test documents that the author reviewed: information, not a gate measurement. n = 26, one human reviewer, the claimed set of path 1 (not a random sample), from 11 parliaments.
  - R2: the head was correct for 24 of 26 documents, the best rule for 20. The 2 errors of the head are the 2 documents with an empty export text.
  - Path 1: 19 of the 26 claimed documents were exact. A converter that gives only the role got 17 of 26.
  - A head with 7,000 instead of 800 `dev` training rows gave the same decisions on the 26 documents.
  - Path 2 ran on these documents on the instruction of the author. This is a deviation from the criteria of its gate. The technical report (chapter 5.5) gives all values with their sources.
- Gate 3a on the full isolation task (06.10.2026): NOT MET.

[track_2a/README.md](track_2a/README.md) gives all values with their sources and limits. The technical report is [track_2a/technical_report.md](track_2a/technical_report.md).

## Deliverables of the challenge

| Deliverable | State on 12.10.2026 |
|---|---|
| 1 Representation model | eCH-0295 (I95, working draft) and the LinkML profile `track_2a/src/converter/m06_ech_profil.yaml` 0.2.0 for the provenance. The profile changes no eCH-0295 class. |
| 2 Converter: prompts and code | `track_2a/src/converter/` (rule stage and eCH-0295 writer), `track_2a/src/prompts/` (prompts for Apertus), `track_2a/src/validate_ech.py` (validator), `track_2a/src/apertus_head/` (head of path 2, code only) |
| 3 Evaluation against a gold set with human acceptance | 26 gold set records examined by the author. No gate measurement: the acceptance of the reference is OPEN. Scores after the freeze on these 26 records, as information: technical report, chapter 5.5. |
| 3 Cross-parliament question | Not answered. The selected question needed task R1, and R1 stopped. |

## What is in this repository

| Path | Content |
|---|---|
| `README.md` | This text |
| `LICENSE` | Apache-2.0, from the Hack Apertus template, not changed |
| `NOTICE` | Copyright, the licenses of the parts and the attributions |
| `LICENSES/` | The license texts Apache-2.0 and CC-BY-4.0 |
| `track_2a/README.md` | How to run, requirements, samples, results, Apertus use, limits |
| `track_2a/Makefile` | `setup`, `run`, `test`, `head-selftest`, `clean` |
| `track_2a/src/converter/` | The converter: copies of the frozen code of the private project (`track_2a/SOURCES.md`) |
| `track_2a/src/prompts/` | The prompts for Apertus |
| `track_2a/src/apertus_head/` | The code of the head of path 2 (no weights) |
| `track_2a/src/run_samples.py`, `validate_ech.py`, `fetch_schema.py`, `check_sources.py` | `make run`, the validator, the download of the schema files, the check of the copies |
| `track_2a/src/` (other files) | The 40 scripts of the first public version (06.10.2026): stages 1 to 3, corpus figures, split, gold set tools (`track_2a/docs/stages-1-3.md`) |
| `track_2a/samples/` | 3 samples: stored Docling output, atoms, export record, expected output |
| `track_2a/results/stored_results.json` | The stored results that `make run` prints |
| `track_2a/tests/` | A known invalid instance for the validator |
| `track_2a/SOURCES.md`, `SOURCES.json` | The SHA-256 of each source file and of each copy, and the edits |
| `track_2a/technical_report.md` | Method, values, causes, limits. The PDF of the submission form is made from this file. |
| `track_2a/technical_report_numbers.json` | Each number of the technical report with its source file and SHA-256, and the steps that make the PDF |
| `track_2a/.env.example` | The names of the settings, without values |
| `track_2a/data/` | Empty |

This repository has its own history. It starts with the publication. It is not the history of the private project.

## What is not in this repository, and why

| Item | Reason |
|---|---|
| PDF documents and OpenParlData exports | OpenParlData publishes them. The license of the PDF copies is not clear. The samples give the URLs and the SHA-256 of their PDF. |
| Test documents, the gold set records of the test documents, the sealed outputs | They are the material of the open gates. The repository gives counts only. |
| AI references and document lists | The AI references have no human acceptance. |
| Apertus weights | The Apertus use policy has duties for each redistribution. Each user downloads Apertus with an own account. |
| Weights of the head of path 2, LoRA adapters | The gate of path 2 is OPEN. The project publishes no weights, also not on Hugging Face. |
| Project notes and the protocol | They contain internal notes. The README files and the technical report give the facts from them, with the SHA-256 of the record files. |
| Copies of eCH-0295 files | The license version of the working draft is not clear. `make setup` downloads the two files from their pinned URLs. |

## eCH-0295

- ParlPDFeCH is an independent project. It is not a product of the association eCH.
- It uses the working draft eCH-0295 of the eCH expert group "Politische Geschäfte": https://github.com/swiss/political-affairs-ech-group, commit `3cab44d` of 30.09.2026.
- eCH-0295 is not approved. ParlPDFeCH does not claim conformity with an approved standard.
- This repository contains no copy of eCH-0295 files. The code uses the names of fields and values of eCH-0295. `make setup` downloads the two files below into `track_2a/.cache/` and examines their SHA-256 (`track_2a/src/fetch_schema.py`).

| File | URL at commit `3cab44d` | SHA-256 |
|---|---|---|
| I95 (`ech-0295_affairs/input/schema.yaml`) | https://raw.githubusercontent.com/swiss/political-affairs-ech-group/3cab44d6a07f60bd8211cccdcf948717ef8fba5c/ech-0295_affairs/input/schema.yaml | `7af4c7a712f16270b653a773179d08cbd1859de053b20fe0beac6b2c2ef30d20` |
| `ech-0292_meta/input/schema_common.yaml` (I95 imports it) | https://raw.githubusercontent.com/swiss/political-affairs-ech-group/3cab44d6a07f60bd8211cccdcf948717ef8fba5c/ech-0292_meta/input/schema_common.yaml | `ab6c097c41cd57c40ad175e9bb130d70f4d4d8eb85281d329bee8c53c8f08b11` |

## License

Copyright 2026 Jonathan Kovatsch. The file `NOTICE` gives the full table and the attributions.

| Part | License |
|---|---|
| Code: `track_2a/src/`, `track_2a/Makefile` | Apache-2.0 (files `LICENSE` and `LICENSES/Apache-2.0.txt`). Each code file has a line `SPDX-License-Identifier: Apache-2.0`. |
| Prompts for Apertus: `track_2a/src/prompts/` | Apache-2.0. Each prompt text file has the line `SPDX-License-Identifier: Apache-2.0`. The JSON template `r2_v1_de.template.json` has no such line, because JSON has no comment lines. The `NOTICE` table applies to it. |
| Documentation: `README.md`, `track_2a/README.md`, `track_2a/SOURCES.md`, `track_2a/technical_report.md`, `track_2a/technical_report_numbers.json`, `track_2a/docs/`, `NOTICE`, the `README.md` files in `track_2a/src/` | CC-BY-4.0 (file `LICENSES/CC-BY-4.0.txt`) |
| `track_2a/samples/` | Data of OpenParlData under CC BY 4.0 and texts of 3 documents (`track_2a/samples/NOTICE.md`) |
| `track_2a/data/` | Empty |

- Hack Apertus terms, chapter 6, "What you build is open source": https://hackapertus.ch/terms-and-conditions
- OpenParlData publishes its data under CC BY 4.0 (API description, read on 06.10.2026). Attribution: "Source: OpenParlData.ch". The API description and the project page do not say if this license applies to the PDF copies.
- Apertus is not in this repository. Its license is Apache-2.0, with the Apertus Acceptable Use Policy v1.5: https://huggingface.co/swiss-ai/Apertus-v1.5-8B

Text of the template:

> All Hack Apertus projects are open-sourced. Please check our Terms & Conditions for specific licensing details (6. What you build is open source): https://hackapertus.ch/terms-and-conditions

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: AI agents (Claude Opus 5.5) wrote this text for the author on 12.10.2026, from the records of the private project. The private project is the project folder of the author. It is not public.
- No human examined this version of the text.

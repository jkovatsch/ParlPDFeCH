# ParlPDFeCH

Target: parliamentary affairs from PDF to eCH-0295, extracted with Apertus by readout, every value with its source.

- Author: Jonathan Kovatsch, as a private person. Copyright 2026 Jonathan Kovatsch (see `NOTICE`).
- Challenge: Track 2A (OpenParlData) of the Hack Apertus online hack, "Extracting Parliamentary Affairs from PDFs into One Common Structure". Challenge page: https://hackapertus.notion.site/track-2a-openparldata
- This repository is not the final submission. Its content can change until the submission on 16.10.2026, 12:00.

## What ParlPDFeCH is

ParlPDFeCH develops a converter for PDF documents of parliamentary affairs. The documents come from parliaments of the Swiss Confederation, the cantons, the municipalities and Liechtenstein, through OpenParlData. The converter must give data to the working draft eCH-0295. In the design of the converter, the language model Apertus-v1.5-8B makes the decisions by readout, and it writes no text. Docling, code rules and code do the other pipeline stages. Each value must have its evidence: the document, the page and the position in the text.

## Approach

Principles of the converter (target):

1. Apertus makes each decision by readout. After a forward pass, code reads the probabilities of a fixed list of answer tokens. Apertus writes no text. The readout is Jev-style (source: https://openjev.com).
2. Each readout gets the whole document. The model reads the document first and the readout question after it.
3. The text of a value comes word for word from the PDF. Docling converts the PDF into blocks. Code divides the blocks into atoms. An atom is one line of a block or one row of a table, with its page, frame and character range.
4. Each value has evidence: the atoms that show it.
5. Code rules make values such as dates and numbers from the wording and from the metadata. Apertus selects among candidates only when the code rules give more than one.
6. A value with a low probability gets the value status `unsure`. The converter does not guess.
7. Apertus runs only in bf16. The converter uses no quantized model.

Target output: eCH-0295 data in LinkML, with JSON, YAML and RDF (Linked Data) as serializations. The project uses the version I95 of eCH-0295 (file `ech-0295_affairs/input/schema.yaml`). A LinkML profile must add provenance, probabilities and the value status. The profile is OPEN.

Pipeline stages (target):

| Stage | Task | Status on 06.10.2026 |
|---|---|---|
| 1 Docling | Convert the PDF into blocks with page, frame and text. | Code in this repository |
| 2 Atoms | Divide the blocks into atoms. Give each atom its features. | Code in this repository |
| 3 Isolation | Add layout hints. Give each atom an eCH-0295 text field, or "no text field". Remove the page furniture with fixed rules. | Code in this repository. The training needs AI references that are not in this repository. Gate 3a is NOT MET. |
| 4 Labeling | Give each segment its type and its values, for example submitters and dates. | No code |
| 5 Classification | Select one option for a whole document, for example the recommendation of the executive. | One pilot. Its code is not in this repository. |
| 6 Relations | Connect segments, for example an answer unit and its parliamentary question. | No code |
| 7 Normalization | Make dates, numbers and person identifiers with code rules. | No code |
| 8 Output | Write the eCH-0295 instance with the profile. Do the schema validation. | No code in this repository. An earlier prototype is not a basis. |

Page furniture is text that is not content, for example page numbers and headers that repeat on each page.

## Current status

Facts on 06.10.2026:

- The converter is not complete. Only the stages 1 to 3 have code in this repository. `make run` is not ready.
- The isolation gate (gate 3a) is NOT MET since 06.10.2026, 00:39 CEST.
- No human finished the check of a document. The author accepted no result. The gold set has 0 documents.
- No value in this repository is accuracy. The values of the method are agreement with AI references. The other agreement values are agreement between AI agents.

An AI reference is a set of answers for the atoms of a document. AI agents (Claude Opus 5.5) made it: AI coders, AI adjudicators and AI review coders (technical report, chapter 4.4). No human accepted it.

### Gates

Each part of the project plan ends with a gate. A gate has criteria and limits. The project writes the limits before the measurement. Only the author can accept a gate. The author accepted no gate until now.

### Isolation (gate 3a)

The isolation gives each atom one of 12 answers: one of 11 text answers, or "no text field". A fixed rule gives page furniture to some atoms. A text answer is a text field of eCH-0295 (I95), for some fields with a text type. Apertus-v1.5-8B with a LoRA adapter gives the probabilities of the 12 answers for each atom. A Viterbi decoder then decides the answers of the document.

Two sets were measured:

- The out-of-fold set has 39 development documents. The model that read a document did not learn from any document of its parliament.
- The final group has 8 documents of 8 parliaments. No model learned from a document of these parliaments. The project measured the final group one time.

| Value | Gate limit | Out-of-fold set (39 documents) | Final group (8 documents) |
|---|---|---|---|
| Labelled boundary F1 | 0.95 or more. Lower bound 0.90 or more (out-of-fold set). Not more than 2 false and 2 missed boundaries (final group). | 0.315 (lower bound 0.227) | 0.455 (5 false and 7 missed boundaries) |
| Text omission | 0.002 or less. Documents with an omission: 5 % or less, or 1 of 8. | 0.060 (25 of 39 documents) | 0.038 (5 of 8 documents) |
| Text intrusion | 0.01 or less | 0.041 | 0.014 |
| Document exact rate | 0.80 or more, or 7 of 8 | 0.103 (4 of 39) | 1 of 8 |
| Agreement of the two AI coders of the final group | 0.95 or more | – | 0.917 |

Both sets together: labelled boundary F1 0.336, lower bound 0.251 (limit: lower bound 0.90 or more).

How to read the values:

1. A boundary is a position where the answer changes. A boundary of the method is correct only when the answers on both sides agree with the AI reference.
2. Text omission is the share of text atoms of the AI reference that the method gives no text field. Text intrusion is the share of text atoms of the method that the AI reference gives no text field.
3. The document exact rate is the share of documents without an error.
4. The lower bound is a Jeffreys bound. It is the harmonic mean of the one-sided 95 % bounds of precision and recall. Together, the two bounds hold with about 90 %.

What the values mean:

1. No measured value of the method meets its gate limit.
2. Before the gate result, the two agreement values of AI agents that coded without an anchor under version 4 were below the limit 0.95. An AI agent with an anchor starts from an available AI reference. The two coders of the final group agreed at 0.917. For 7 documents, the blind answers of one more AI agent agreed with the AI reference at 0.944. Thus, the measurement cannot separate errors of the method from errors of the AI reference.
3. The labelled boundary F1 of the method is 0.629 (out-of-fold set) and 0.490 (final group) below the blind AI agreement of 0.944.
4. The main errors are whole blocks with the wrong author: text of the submitter as the response of the executive, and the opposite.

The technical report gives all values, the causes and the limits: [track_2a/technical_report.md](track_2a/technical_report.md).

### Gold set

The gold set is the test documents whose answers have human acceptance.

- On 06.10.2026, the author decided to make a human gold set with AI support.
- In the procedure, the author examines each document in a local review tool. The tool shows the PDF pages, a proposal of AI coders, and the atoms where the AI codings do not agree. For 4 pilot documents, the tool shows no proposal.
- Prepared on 06.10.2026: a pilot list of 20 development documents; 28 test documents from test parliaments, with an AI proposal; an extension list for more AI references for the training (150 of 151 documents prepared).
- The code that downloads and prepares two larger lists is in this repository (`track_2a/src/m03_gold_bulk.py`): 300 documents of test parliaments and 2,500 documents of training and validation parliaments. The code that selected the two lists is not in this repository.
- The human check of the test documents starts only after the author accepts the definition of the isolation task.
- No value in this repository uses a result of the human check.
- After clarifications of the task definition, two blind AI coders agreed at 0.983 (labelled boundary F1) on 48 development documents. Both coders are instances of the same model. Thus, a shared error is possible.

### Deliverables of the challenge

| Deliverable | Status on 06.10.2026 |
|---|---|
| 1 Representation model | The project builds on eCH-0295 (I95). A LinkML profile must add to it and must not relax a rule of it. The profile and the mapping table are OPEN. |
| 2 Converter: prompts and code | The stages 1 to 3 have code in this repository. The isolation gate is NOT MET. The stages 4 to 8 have no code in this repository. |
| 3 Evaluation against a gold set with human acceptance | The gold set has 0 documents. |
| 3 Cross-parliament question | Selected question: "Does the parliament follow the recommendation of the executive?", for motions and postulates. Not answered. |

## What is in this repository

| Path | Content |
|---|---|
| `README.md` | This text |
| `LICENSE` | Apache-2.0, from the Hack Apertus template, not changed |
| `NOTICE` | Copyright, the licenses of the parts and the attributions |
| `LICENSES/` | The license texts Apache-2.0 and CC-BY-4.0 |
| `track_2a/README.md` | How to run, requirements, settings, code, data |
| `track_2a/technical_report.md` | Method, values, causes, limits, next steps |
| `track_2a/src/` | 40 files: 39 files of the private project at commit `a1db1fb`, with edits for publication, and one new module. They make the current pipeline (stages 1 to 3), the corpus figures, the eCH-0295 comparison and the split. Others select documents, measure, prepare the gold set and check texts. |
| `track_2a/.env.example` | The names of the settings, without values |
| `track_2a/.dockerignore` | Files that a container image must not get |
| `track_2a/Makefile` | The target `run`. It is not ready and stops with a message. |
| `track_2a/data/` | Empty |
| `track_2a/docs/` | [pending: diagram of the pipeline] |

This repository has its own history. It starts with the publication. It is not the history of the private project.

## What is not in this repository, and why

| Item | Reason |
|---|---|
| PDF documents and OpenParlData exports | OpenParlData publishes them. The license of the PDF copies is not clear. The documents contain personal data. |
| AI references, document lists, token bundles, model outputs | The AI references have no human acceptance. The project keeps the test documents apart from the development until the final evaluation. [pending: decision of the author] |
| Apertus weights | The Apertus use policy has duties for each redistribution. Each user downloads Apertus with an own account. |
| Adapter weights | [pending: decision of the author] |
| Project notes and the protocol | They contain internal notes. This README and the technical report give the facts from them. |
| 70 of the 109 files in `src/` of the private project at commit `a1db1fb` (69 scripts and one profile file) | 64 of them are not part of the current pipeline: historical or replaced methods, analyses, work out of the planned order, the classification pilot, earlier trials and one MLX module. The other 6 make inputs of the current pipeline: the 5 scripts of the PDF inspection make a table that the current pipeline reads, and one module is the source of `track_2a/src/m03_render.py`. Two of the 70 read files of a repository of OpenParlData under GPL-3.0. |
| Copies of eCH-0295 files | The license version of the working draft is not clear. See the chapter eCH-0295. |

## How to follow the progress

- Use the function "Watch" of GitHub to get a message for each release. The commit history shows each change.
- The chapter "Current status" gives the date of its facts.
- Open items have the mark [pending: ...].
- A decision by delegation of 05.10.2026 sets a latest date for gate 3a: 10.10.2026, 18:00. The author did not confirm this date yet. If the author does not accept gate 3a by then, the paths that need the isolation stop, for example the labeling. The technical report then shows them as a negative result.
- Submission: 16.10.2026, 12:00.

## eCH-0295

- ParlPDFeCH is an independent project. It is not a product of the association eCH.
- It uses the working draft eCH-0295 of the eCH expert group "Politische Geschäfte": https://github.com/swiss/political-affairs-ech-group, commit `3cab44d` of 30.09.2026.
- eCH-0295 is not approved. ParlPDFeCH does not claim conformity with an approved standard.
- This repository contains no copy of eCH-0295 files. The code uses the names of fields and values of eCH-0295. [pending: download at the container build, with a SHA-256 check]

The two files of the working draft that the project uses:

| File | URL at commit `3cab44d` | SHA-256 |
|---|---|---|
| I95 (`ech-0295_affairs/input/schema.yaml`) | https://raw.githubusercontent.com/swiss/political-affairs-ech-group/3cab44d6a07f60bd8211cccdcf948717ef8fba5c/ech-0295_affairs/input/schema.yaml | `7af4c7a712f16270b653a773179d08cbd1859de053b20fe0beac6b2c2ef30d20` |
| `ech-0292_meta/input/schema_common.yaml` (I95 imports it) | https://raw.githubusercontent.com/swiss/political-affairs-ech-group/3cab44d6a07f60bd8211cccdcf948717ef8fba5c/ech-0292_meta/input/schema_common.yaml | `ab6c097c41cd57c40ad175e9bb130d70f4d4d8eb85281d329bee8c53c8f08b11` |

## License

Copyright 2026 Jonathan Kovatsch. The file `NOTICE` gives the full table and the attributions.

| Part | License |
|---|---|
| Code: `track_2a/src/`, `track_2a/Makefile` | Apache-2.0 (files `LICENSE` and `LICENSES/Apache-2.0.txt`). Each code file has a line `SPDX-License-Identifier: Apache-2.0`. |
| Readout questions and answer lists for Apertus (the Apertus prompts) in the code files | Apache-2.0, as a part of the code files. [pending: decision of the author about the license of the Apertus prompts] |
| Documentation: `README.md`, `track_2a/README.md`, `track_2a/technical_report.md`, `track_2a/docs/`, `NOTICE` | CC-BY-4.0 (file `LICENSES/CC-BY-4.0.txt`) |
| `track_2a/data/` | Empty. [pending: license, if the repository gets data] |

- Hack Apertus terms, chapter 6, "What you build is open source": https://hackapertus.ch/terms-and-conditions
- OpenParlData publishes its data under CC BY 4.0 (API description, read on 06.10.2026). Attribution: "Source: OpenParlData.ch". The API description and the project page do not say if this license applies to the PDF copies.
- Apertus is not in this repository. Its license is Apache-2.0, with the Apertus Acceptable Use Policy v1.5: https://huggingface.co/swiss-ai/Apertus-v1.5-8B

Text of the template:

> All Hack Apertus projects are open-sourced. Please check our Terms & Conditions for specific licensing details (6. What you build is open source): https://hackapertus.ch/terms-and-conditions

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: AI agents (Claude Opus 5.5) wrote this text for the author from the records of the private project. The private project is the project folder of the author. It is not public.
- Check of the facts: on 06.10.2026, two more AI agents compared each statement of fact with these records, one before and one after the assembly of this repository.
- Human check: no human examined this text yet. [pending: check of this text by the author]

# ParlPDFeCH: project folder for Track 2A

This folder is the project root for the judges of Hack Apertus. The front page of the repository is [../README.md](../README.md). The technical report is [technical_report.md](technical_report.md). The PDF of the submission form is made from this file ([technical_report_numbers.json](technical_report_numbers.json), key `pdf`).

ParlPDFeCH converts PDF documents of Swiss parliamentary affairs into the working draft eCH-0295 (version I95). The converter writes no text: each text value is the wording of the PDF. A provenance side file gives the page, the frame and the character range of each line.

State of this text: 12.10.2026. Both gates of the project are OPEN. No value of this repository is a gate measurement. After the freeze, the project scored both paths against the records of the 26 reviewed test documents, outside the gate criteria. The chapter "Results" and the technical report (chapter 5.5) give these values as counts and rates, with no value of a single document.

## Run it

Requirement: [uv](https://docs.astral.sh/uv/) 0.11 or later. Run the commands in this folder (`track_2a/`).

```bash
make setup   # one time, with network: Python 3.12, PyYAML, numpy, scipy, linkml, two eCH-0295 schema files
make run     # no network, no GPU, no model
make test    # optional
```

`make run` does these steps on the 3 samples in `samples/`:

1. It makes a work folder `build/layout/` with the copied code, the stored input of the samples and the schema files.
2. Stage 1, rule stage (`src/converter/m05_iso_runner.py`): the frozen method `nos4` at isolation level L9 gives each line (atom) of a document an answer. It then gives the document a claim flag.
3. Stage 2, eCH-0295 writer (`src/converter/m06_converter.py`): one eCH-0295 instance and one provenance side file for each document. The writer validates both files.
4. Validator (`src/validate_ech.py`): it validates each output file again with `linkml-validate`.
5. It compares the output with the stored output in `samples/<doc>/expected/`.
6. It prints the stored results table (`results/stored_results.json`). These values do not come from the run.

The output is in `build/layout/out/`. On a Mac with Apple M4, the run takes less than 15 seconds. It ends with `Result of make run: PASS` and the exit code 0.

`make test` runs these checks:

- `src/check_sources.py`: each copied file is equal to its source file in the private project, without the license line and the recorded edits ([SOURCES.md](SOURCES.md)).
- The validator accepts the 6 stored output files and rejects `tests/invalid_instance.yaml` (a value that is not in an enumeration of I95).

`make head-selftest` runs the self-check of the Apertus head code of path 2 on synthetic data (about 5 minutes, no model).

Docker: this version has no container file. `make run` needs uv on the computer. The template asks for a run in Docker.

## Requirements

| Item | Requirement |
|---|---|
| Runtime of `make run` | uv 0.11 or later; Python 3.12.13 (uv installs it); PyYAML 6.0.3; linkml 1.11.1 (with `uvx`). Tested on macOS (Apple silicon) on 12.10.2026. |
| Downloads of `make setup` | Python 3.12, PyYAML 6.0.3, numpy 2.5.3 and scipy 1.18.1 into the cache of uv; linkml 1.11.1 into the tool cache of uv; the two eCH-0295 schema files into `.cache/ech-0295/` (`src/fetch_schema.py`, pinned commit and SHA-256). |
| Hardware of `make run` | A normal computer. No GPU. |
| API keys | None for `make run`. |
| Model weights | None for `make run`. A run of Apertus needs the weights of Apertus-v1.5-8B in bf16 (own download, chapter "Use of Apertus"). |
| Environment variables | `make run` reads none. The template names `LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY`. The converter does not use them: the Apertus readouts of this project need token probabilities or hidden states of a local model. |

## Samples

The samples are 3 development documents of path 1 (`dev`). Two AI agents examined each of them for personal data of third parties, with the result PASS. The documents name only persons with a public role: members of a parliament or an executive, and officials who sign for an authority.

| Document | Parliament | Language | Content | Result of the converter |
|---|---|---|---|---|
| 26171 | Grosser Rat Basel-Stadt (canton) | German | Text of an interpellation | Claimed at L9: one TextBlock in `Submission.texts` |
| 879163 | Conseil général Val de Bagnes (municipality) | French | Statement of the executive on a postulate | Claimed at L9: one TextBlock in `ResponseStep.texts` |
| 714840 | Basel-Stadt (canton) | German | Resolution of the executive in its own competence | Not claimed: the S1 role is `other`, so the writer gives only the values from the export record |

Sources of the PDF documents:

| Document | URL of the publisher | Copy of OpenParlData | SHA-256 of the PDF |
|---|---|---|---|
| 26171 | https://grosserrat.bs.ch/?dnr=19.5497.01 | https://files.openparldata.ch/doc/BS/983545420862d4d42f592e71918230f03e8a4cf46f90e7fd4a380c08e1cc7667 | `f2e5fe4ae6747a886d93bc753795611117fe11b4d23f4ae30d53866fcedb1493` |
| 879163 | https://www.valdebagnes.ch/_doc/4552844 | https://files.openparldata.ch/doc/6037/cc7eb17fcc026efde7c970a1e762e7b70538e06787859cbe44f4fb2b3de11a19 | `7b160c11fcf55c0b70d14c5287589c1bbf7e4e7da9d2e791ba715f667f4ba5d5` |
| 714840 | https://www.bs.ch/api/government-resolutions/document/e159ecf6d8a64510b698e6232b719538-332/5/Dokument | https://files.openparldata.ch/doc/BS/210f283a44ef070a6ac958970636bbf12900f44a6d97f687de9bad9a1b1827bf | `8bb01b408e55d4277550fa7521783392ddae4b8fe881d70165632e36f8391fe2` |

Files of each sample (`samples/<doc>/`):

| File | Content |
|---|---|
| `source.json` | The source URLs, the SHA-256 of the PDF, the Docling versions, the S1 rule id and the claim flag |
| `input/docling.json` | The stored Docling output of the PDF (Docling 2.133.0, backend `docling-parse`, OCR with Apple Vision) |
| `input/atoms.json` | The stored atoms: one atom for each line of a block or each row of a table, with page, frame and character range |
| `input/export.json` | The export record of OpenParlData for the document: document, affair, events, councils, parliament (exports of 04.10.2026) |
| `expected/instance.yaml` | The eCH-0295 instance (I95, class `Container`) |
| `expected/provenance.yaml` | The provenance side file (profile 0.2.0, class `ExtractionRecord`) |
| `expected/runner_core.json` | The answers of the rule stage: one answer for each atom, the L9 answers, the claim flags, the S1 role |

`samples/pdf_index.csv` and `samples/languages.csv` hold the rows of the 3 samples of two tables of the private project: the PDF index (export fields) and the language of the document. The repository holds no PDF.

Evidence of a value: in `expected/provenance.yaml`, each TextBlock has a `TextBlockRecord`. It lists the atoms of the block with page, frame (`bbox`) and character range. For example, the TextBlock of document 26171 has 37 atoms on page 1. Each value from the export record has a `ValueRecord` with the export file, the record and the field. Each claimed TextBlock has `extent_value_status: unsure`: the converter does not claim which lines are body text.

## Results

`make run` prints these values from `results/stored_results.json`. Each part names its record in the private project and the SHA-256 of the record file. The private project is not public.

Path 1, rule stage at isolation level L9 (method `nos4`): gate 3a version 4 is OPEN. It has no gate measurement.

| Item | Value |
|---|---|
| Gate 3a on the full isolation task | NOT MET (06.10.2026). This result does not change. |
| Selected test documents | 40 of 13 parliaments (German 21, French 17, Italian 2), selected by a script with a fixed seed |
| Run of the frozen converter on the test documents | One run on 09.10.2026. Answers sealed with SHA-256. Claimed at L9: 26 of 40. |
| Human reference | The author examined the 26 gold set records (proposals of AI coders) on 11.10.2026. |
| Gate measurement | None. The blind repetition of 4 records (criterion G3a.16) and the acceptance of the reference (G3a.2) did not take place. |
| Scores after the freeze on the 26 review records (information) | Exact documents: 19 of 26 (Jeffreys lower bound 0.574). A converter that gives only the role: 17 of 26. Documents with an author switch: 2 of 7 exact. Labelled boundary F1: 0.308. Block omission: 0. Atom intrusion rate: 0.305. Agreement of the two AI coder proposals: 22 of 26. Not a gate measurement (technical report, chapter 5.5). |
| Development values (information) | `dev`: 124 of 183 documents claimed, 99 of 124 block exact. `eval`: 15 of 22 claimed, 15 of 15 block exact. |

The development values compare the converter with AI references, not with a human reference. On `dev`, they are in-sample: AI agents wrote the rules on these documents. The project measured `eval` several times before. These values are not accuracy.

Path 2, Apertus-v1.5-8B with a trained head, task R2 ("the document holds a response of the executive"): the gate is OPEN.

| Set | Head | Zero-shot Apertus readout | Best rule (`s1_answer`) |
|---|---|---|---|
| Validation, 920 documents (balanced accuracy) | 0.919 | 0.899 | 0.932 |
| Validation without the K7 categories, 714 documents | 0.980 | 0.953 | 0.965 |

- The source label of R2 comes from the local category of the document. The K7 categories are local categories that give only the name of an affair type, for example `Interpellation`. 78 of the 93 wrong decisions on all 920 documents are `no` documents with such a category.
- The final run on the test parliaments is sealed: 1,523 documents, 12.10.2026. It has no measurement, because the blind check of the reference did not take place.
- Information: a LoRA adapter on all layers (one H100 GPU) and a cascade of rules and head were tried and not chosen.

Path 2, task R2, scores after the freeze on the 26 reviewed test documents (information, not a gate measurement). The truth comes from the 26 review records: `yes` 15, `no` 11. A document without a value counts as wrong.

| Method | Correct of 26 | Balanced accuracy | McNemar p against `s1_answer` |
|---|---|---|---|
| Head H (800 `dev` training rows, frozen) | 24 | 0.933 | 0.125 |
| Head H7k (the recipe of H, 7,000 `dev` training rows) | 24 | 0.933 | 0.125 |
| LoRA L3 (7,000 `dev` rows) and LoRA L | 24 each | 0.933 | 0.125 |
| Zero-shot Apertus readout | 23 | 0.888 | 0.375 |
| Rule `s1_answer` | 20 | 0.800 | – |
| Rule `heading` | 18 | 0.733 | – |

- The 2 errors of H, H7k, L3 and L are the 2 documents with an empty export text (no value). Their truth is `yes`.
- H, H7k, L3 and L give the same decision on each of the 26 documents. Against `s1_answer`: 4 documents only H correct, 0 only the rule correct.
- n = 26, one human reviewer. The 26 documents are the claimed set of path 1 (not a random sample), from 11 parliaments.
- Path 2 ran on these documents on the instruction of the author. This is a deviation from criteria v2 of its gate, chapter 2.1, item 1.
- Head H7k against H: partition P of `dev` 0.996250 and 0.996250; validation 0.917 and 0.919; validation without K7 0.979 and 0.980.

Path 2, task R1 (the recommendation of the executive, for or against): stopped, negative result.

| Set | Head | Best rule | Zero-shot Apertus readout |
|---|---|---|---|
| Validation, 287 documents (correct decisions) | 250 | 186 | 196 |
| Date-linked validation set, 115 documents (correct decisions) | 98 | 104 | 94 |

Causes: the gain on all 287 documents comes from submitted texts without a recommendation. The head follows the reasons of a letter more than its formula. Without the option `none`, a head gives a confident value to a document without a recommendation.

Sources: the report of path 2, iteration 2 (SHA-256 `43d44910…`), chapters 0, 6.1, 6.2 and 12.1; the criteria of gate 3a version 4 (`1db4b2c2…`); the freeze manifest of path 1 (`440e4247…`); the results of the complexity ladder (`7491c0ed…`, isolation level L9, method `nos4`); the protocol of the private project. Scores after the freeze: the R2 score report (`d9285111…`), the path-1 values (`3078d95f…`), the H7k report (`50865daa…`) and their independent checks (`5e87ecdb…`, `0fe9443f…`). `results/stored_results.json` gives the full SHA-256 values and the dates of the protocol entries.

## Converter

Input of the converter: the stored Docling output of a PDF, its atoms and the export record of OpenParlData. The stages before (PDF to Docling output to atoms) are the scripts `src/m03_docling_zerlegen.py` and `src/m03_atome.py` of the first public version ([docs/stages-1-3.md](docs/stages-1-3.md)). `make run` starts from their stored output.

| Stage | Code | What it does |
|---|---|---|
| Fixed answers | `src/converter/m03_iso_v4.py`, `m03_iso_hilfe.py` | Page furniture and frame lines by fixed rules |
| S1 role | `src/converter/m03_sub_s1_role.py` | The role of the document from the atoms and three export fields: proposal, response, combined, minutes, committee or other. For the rule id R1 only, Apertus decides the role (prompt `src/prompts/s1_role.txt`). |
| S2 switch | `src/converter/m03_sub_s2_switch.py` | The points where the author changes (rule) |
| S5 type and composition | `src/converter/m03_sub_s5_type.py`, `m03_sub_assemble.py`, `m03_sub_common.py` | The answers of the atoms from the sub-task results |
| Isolation level L9 | `src/converter/m03_ladder.py` | The answers after the map `SLOT_NOTITLE` at the block unit. Scope rule `role_agreement`: the role of the answers and the S1 role must be author roles, and the role of the answers must be the S1 rule role. Else the converter does not claim the document. |
| Runner | `src/converter/m05_iso_runner.py` | Applies the chain to new documents, with guards, and seals each record with SHA-256 |
| eCH-0295 writer | `src/converter/m06_converter.py`, `m06_ech_ausgabe.py`, `m02_ech_regeln.py`, `m03_gold_record.py` | The instance and the provenance side file. Metadata values come from the export record. The text of a TextBlock is the wording of its atoms. |
| Profile | `src/converter/m06_ech_profil.yaml` | LinkML profile 0.2.0 of the provenance side file. It changes no eCH-0295 class. |
| Method data | `src/converter/method/ladder.json`, `s1_selection.json` | The collapse maps and the isolation levels; the rule ids that keep the rule role |

The code in `src/converter/` is a copy of the frozen code of the private project. [SOURCES.md](SOURCES.md) gives the SHA-256 of each source file and of each copy, and the few edits for publication. On 8 development documents, the copied converter gave the same eCH-0295 instances as the private converter, byte for byte ([SOURCES.md](SOURCES.md)).

The code has German names and some German comments. Names such as E20, G3a.2 or "process rule 6" refer to the decision list and the gate criteria of the private project. [docs/stages-1-3.md](docs/stages-1-3.md) (chapter "Names in the code") and the technical report explain the main ones.

## Validator

```bash
uv run --offline --no-project --python 3.12 --with pyyaml==6.0.3 python src/validate_ech.py FILE [FILE ...]
```

- An instance is validated against I95 (`ech-0295_affairs/input/schema.yaml` of https://github.com/swiss/political-affairs-ech-group, commit `3cab44d`), class `Container`.
- A provenance side file (a file with the key `describes_delivery`) is validated against the profile `src/converter/m06_ech_profil.yaml`, class `ExtractionRecord`.
- Tool: `linkml-validate` of linkml 1.11.1. The exit code is 0 only if each file is valid.
- The schema files are not in this repository. `make setup` downloads them from their pinned URLs and examines their SHA-256 (`src/fetch_schema.py`).

## Use of Apertus

| Item | Path 1 (converter) | Path 2 (head, not in the converter) |
|---|---|---|
| Model | Apertus-v1.5-8B on the CSCS inference API. CSCS does not document the precision. A comparison with the local bf16 model on synthetic text found no difference above the bf16 noise (05.10.2026). | Apertus-v1.5-8B, bf16, no quantization, all 32 decoder layers |
| Task | The S1 role of a document with the S1 rule id R1 | R2: does the document hold a response of the executive (yes or no) |
| Method | Readout of the token probabilities of a fixed list of answers. Apertus writes no text. | A softmax regression on the hidden state of decoder layer 16 at the last prompt token. The weights of Apertus do not change. |
| Prompt | `src/prompts/s1_role.txt` | `src/prompts/r2_v1_de.txt` (exact form: `r2_v1_de.template.json`) |
| Where it ran | CSCS inference API (Swiss National Supercomputing Centre), Hack Apertus access | Locally on a Mac with MLX; the final run in a VM with one H100 GPU of a Swiss provider (free capacity for Hack Apertus). An equality check of the two places gave PASS. |
| In `make run` | No question: the 3 samples have S1 rule ids that do not need Apertus. A document with the rule id R1 stops the run in the mode `cache-only`. | No. `src/apertus_head/README.md` describes the code. |

In both paths, the whole document comes first and the question comes last. [src/prompts/README.md](src/prompts/README.md) lists the prompts and which method uses them.

Model weights:

- This repository contains no Apertus weights and no weights of the head.
- Get access to the weights on https://huggingface.co/swiss-ai/Apertus-v1.5-8B with your own account. Agree to the license (Apache-2.0) and to the Apertus Acceptable Use Policy v1.5.
- The Apertus Acceptable Use Policy v1.5 has duties for each user: indemnity for ETH Zurich and EPFL; the role of an independent controller for personal data in the model output; the output filter of hash values of the Swiss National AI Institute (the policy advises to apply it every six months); the policy goes with each copy of Apertus.

Other models in the project: AI agents (Claude Opus 5.5) wrote the code, the rules and the proposals of the gold set records, and they checked texts. AI agents (Claude Haiku 5.5) gave a second look at the text blocks of the 26 records of test documents. Docling uses its own layout and table models (layout model `layout_heron`). The OCR engine of the stored Docling output is Apple Vision (`ocrmac`, macOS only). Sample 879163 is a scan: 43 of its 45 atoms come from OCR, and the side file marks them with `from_ocr: true`. The technical report describes the role of each model.

## Limits

1. Both gates are OPEN. No value of this repository is a gate measurement. The scores on the 26 reviewed test documents come after the freeze, from one human reviewer, with n = 26.
2. The converter isolates written affairs only. It does not isolate debate and committee texts, although eCH-0295 holds them.
3. At the block unit, the converter claims the author sequence and the switch points. It does not claim which lines are body text (`extent_value_status: unsure`).
4. The converter claims only a part of the documents. On `dev`, it claimed 124 of 183 documents.
5. The converter writes no value of path 2 (R1, R2), because neither task has an ACCEPTED gate.
6. The 3 samples are development documents. AI agents wrote the rules on these documents.
7. `make run` starts from the stored Docling output. A new PDF needs Docling first (`src/m03_docling_zerlegen.py`, `src/m03_atome.py`).
8. The runner needs the files of the private layout. `make run` makes this layout from the files of this repository, with guard files that hold no rows.
9. No container file. `make run` is tested on macOS only.

## Other code in `src/`

The 40 scripts at the top of `src/` are the first public version of 06.10.2026. They make the stages 1 to 3: Docling, atoms, and the isolation with a LoRA adapter. Other scripts give the corpus figures, the eCH-0295 comparison, the split and the tools of the gold set. [docs/stages-1-3.md](docs/stages-1-3.md) describes them, with their settings and their known limits.

## License

- Code in `src/`, the `Makefile` and the prompts in `src/prompts/`: Apache-2.0 (`../LICENSE`). Each code file and each prompt text file has the line `SPDX-License-Identifier: Apache-2.0`. The JSON template `src/prompts/r2_v1_de.template.json` has no such line, because JSON has no comment lines. The `NOTICE` table applies to it.
- This text, `SOURCES.md`, the technical report, `technical_report_numbers.json` and `docs/`: CC-BY-4.0 (`../LICENSES/CC-BY-4.0.txt`).
- `samples/`: data of OpenParlData under CC BY 4.0, and texts of the documents. See `samples/NOTICE.md`.
- Copyright 2026 Jonathan Kovatsch. The full table and the attributions are in `../NOTICE`.
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
- Authoring: AI agents (Claude Opus 5.5) wrote this text for the author on 12.10.2026, from the records and the code of the private project. The private project is the project folder of the author. It is not public.
- No human examined this version of the text.

# Stages 1 to 3 of the first public version

History: the scripts of stages 1 to 3 of the first public version, 06.10.2026. Not the product of this version; see the [README](../README.md).

This text describes the 40 stage scripts at the top of `src/` (`src/m0*`). They are the code of the first public version of 06.10.2026 (stages 1 to 3 of the pipeline: Docling, atoms, isolation with a LoRA adapter). The earlier converter of 12.10.2026 is in `src/converter/` (`make run-earlier`). The product reads the values from the PDF: `src/converter_gj/` and `app/` ([README](../README.md), chapters "The method" and "Where the parts are").

The text below comes from the README of 06.10.2026: the chapters "Run it" (from its third paragraph), "Requirements", "Data" and "Code". Its content did not change, except the edits in "About this text". The headings are one step lower.

## Order of the scripts

The scripts in `src/` come from the private project (commit `a1db1fb`), with edits for publication (chapter "Code"). They read and write below the data root (chapter "Settings").

The private project ran the current pipeline in this order:

| Order | Script | What it does |
|---|---|---|
| 1 | `src/m02_exporte_holen.sh` | Downloads the OpenParlData exports and records the time in UTC. |
| 2 | `src/m02_synthese_split.py` | Assigns whole parliaments to the training set, the validation set and the test set. |
| 3 | `src/m03_iso_gruppen.py`, `src/m03_iso_gruppe7.py`, `src/m03_iso_pool.py` | Select the measured groups and the training pool, with fixed seeds. |
| 4 | `src/m03_docling_zerlegen.py` | Converts each PDF document with Docling into blocks with page, frame and text. |
| 5 | `src/m03_atome.py` | Divides the blocks into atoms. Checks that the atoms cover the full text exactly one time. |
| 6 | `src/m03_iso_hints.py` | Makes the layout hints and the title anchor. |
| 7 | `src/m04_text_branch_extrahieren.py` | Takes the text weights out of the downloaded Apertus-v1.5-8B, with MLX. The values of the kept weights stay in bf16. |
| 8 | `src/m04_iso_bundle.py` | Makes the token bundle for the GPU: token ids only. |
| 9 | `src/m04_iso_torch.py` | Trains the LoRA adapter on a GPU. Reads out the documents with the adapter. |
| 10 | `src/m04_iso_import4.py` | Decides the answers of each document with the Viterbi decoder and the fixed answers. |
| 11 | `src/m03_iso_v4.py`, `src/m04_iso_report.py` | Measure the answers against an AI reference. |

Gaps in this order:

- Steps 3 and 6 read the list of a stratified sample, and steps 3 and 4 use its PDF documents. An earlier script selected and downloaded this sample, from an earlier version of the split. That script is not part of the current pipeline. It is not in this repository. The scripts find the list and the PDF files at the paths `SAMPLE_LIST` and `SAMPLE_PDF` of `src/m03_iso_paths.py` (settings `PARLPDFECH_SAMPLE_LIST` and `PARLPDFECH_SAMPLE_PDF`).
- Steps 2, 3 and 5 read the table of the PDF inspection (`augenschein.csv`). The scripts that make it are not in this repository.
- Step 2 also reads a table of `m02_texte_profil.py` and the training examples of earlier pilots. The scripts that make them are not in this repository.
- Steps 8 to 11 need the AI references and the list of the personal data examination. They are not in this repository.
- `src/m03_gold_bulk.py` has no selection step. The selection needs the code of a candidate pool that is not in this repository. The script starts from the two lists of the selection.
- The script that selected group 6 (seed 20261006) is not in this repository.

### Requirements

| Item | Requirement |
|---|---|
| Runtime | Python 3.12 with uv; Docling 2.133.0; Poppler (`pdftotext`, `pdfinfo`, `pdftoppm`); on macOS MLX 0.32.3 and mlx-lm 0.32.0. For the GPU: PyTorch 2.8.0, transformers 5.18.0, peft 0.21.2 (recorded on 05.10.2026 for the first rented GPU). |
| System | Two computers at this time. Docling with Apple Vision OCR (`ocrmac`), MLX in step 7 and the tokenizer of `mlx-lm` in step 8 need macOS. The training and the readout need Linux with a CUDA GPU. The version of 06.10.2026 had no container file. Since 14.10.2026 the app has one (`app/Dockerfile`, `make run`). |
| Hardware | Development: Mac mini M4 with 32 GB memory. Training and readout: rented H100 GPUs with 80 GB memory, one for each run, in European data centers. |
| API keys | `HF_TOKEN` for the download of Apertus with the Hugging Face tools. No script in this repository reads it. `RUNPOD_API_KEY` for `src/m04_runpod.py` (rented GPU), from the environment or from the file `.env.runpod` in this folder. The current pipeline does not use `LLM_BASE_URL` and `LLM_API_KEY`. `make run-earlier` does not read `LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY`. |
| Model weights | Apertus-v1.5-8B in bf16. Each user downloads the weights with an own account (see below). No weights are in this repository. |

#### Settings

The file `.env.example` gives the names of the settings without values. The scripts read the settings only from the environment. They do not read a file `.env`. To use a file `.env`, load it into the environment, for example with `set -a; . ./.env; set +a`. `.gitignore` excludes all files `.env*` except `.env.example` from the repository. `.dockerignore` excludes all files `.env*` from a container image.

| Name | Use |
|---|---|
| `PARLPDFECH_DATA` | The data root of all scripts, as an absolute path. Without it: the folder `data/` of this folder. All data paths of the scripts are below the data root. |
| `PARLPDFECH_SAMPLE_LIST`, `PARLPDFECH_SAMPLE_PDF` | Optional. The list of the stratified sample and the folder of its PDF files. Without them: `<data>/analyse/stichprobe/auswahl.csv` and `<data>/pdf/stichprobe`. |
| `HF_TOKEN` | The download of Apertus-v1.5-8B from Hugging Face. No script in this repository reads it. |
| `RUNPOD_API_KEY` | Optional. The key of the Runpod API for `src/m04_runpod.py` |
| `RUNPOD_SSH_KEY` | Optional. The private key file for the ssh command of `src/m04_runpod.py`. Without it: `~/.ssh/runpod_parlpdfech`. Use a key pair only for this project. The command `create` stops if the public half (`<key file>.pub`) does not exist. |
| `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` | The names of the template. The current pipeline does not use them. |
| `PDFTOTEXT` | Optional. The `pdftotext` program for `src/m03_docling_zerlegen.py`. Without it: `pdftotext` in the search path. `src/m03_atome.py` always uses `pdftotext` in the search path. Without it, `src/m03_atome.py` makes the atoms without the text layer and gives no message. |
| `ISO_DEVICE` | Optional. The device of `src/m04_iso_torch.py`. Without it: `cuda`. |

The sub-paths below the data root are the sub-paths of the private project, with German names, for example `iso/`, `gold/`, `analyse/` and `roh/exports/`. The two paths of the stratified sample are an exception. To use the private layout without a change, set `PARLPDFECH_DATA` to the data folder of the private project. Also set the two sample settings to the sample of the private project. `.gitignore` excludes the content of `data/` except the file `data/.gitkeep`. `.dockerignore` excludes `data/`.

Relative paths on the command line: these options are relative to the data root: `--ref` of `src/m03_iso_jev.py` and `src/m03_iso_jev4.py`, `--pool-ref` and `--group-ref` of `src/m04_iso_bundle.py`, `--ref-groups` and `--ref-pool` of `src/m04_iso_crf.py`, `--trans-ref-groups` and `--trans-ref-pool` of `src/m04_iso_import4.py`, and `--ausgabe` of `src/m03_docling_zerlegen.py`. All other relative paths on the command line are relative to the current folder.

#### Model weights

- This repository contains no Apertus weights. A container image of this project must also contain no Apertus weights.
- Get access to the weights on https://huggingface.co/swiss-ai/Apertus-v1.5-8B with your own account. Agree to the license (Apache-2.0) and to the Apertus Acceptable Use Policy v1.5.
- Download the weights with the Hugging Face tools into `<data>/modelle/Apertus-v1.5-8B`. `src/m04_text_branch_extrahieren.py` reads them there (option `--quelle`). No script in this repository downloads Apertus.
- The project uses only the text weights, in bf16. It uses no quantized model.

The Apertus Acceptable Use Policy v1.5 has these duties for each user:

1. The user indemnifies ETH Zurich and EPFL against claims of third parties from the use of Apertus.
2. The user is an independent controller for personal data in the model output.
3. The Swiss National AI Institute gives a file of hash values as an output filter. The policy advises to apply it every six months.
4. If you give Apertus to other persons, give them the policy too. Make this depend on their express agreement. Pass these duties on to all later recipients.

### Data

- Source: OpenParlData (https://openparldata.ch). API: https://api.openparldata.ch. Exports: https://files.openparldata.ch/exports/. PDF documents: https://files.openparldata.ch/doc/.
- The project used the exports of 04.10.2026, 13:26 UTC.
- OpenParlData publishes its data under CC BY 4.0 (API description, read on 06.10.2026). Attribution: "Source: OpenParlData.ch". The API description and the project page do not say if this license applies to the PDF copies.
- `data/` is empty. This repository contains no export. The only PDF documents are the 3 samples of the app (`app/data/samples/`).
- The documents contain names of persons, for example members of a parliament or of an executive. Some documents contain personal data of third parties.
- Some documents went to a rented GPU (Runpod) or to the CSCS inference API. Before that, two AI agents (Claude Opus 5.5) examined each of these documents for personal data of third parties. Only documents with the verdict PASS from both AI agents went to these services. Of 321 examined documents, 308 had PASS and 13 had FAIL.
- This examination did not apply to the AI agents (Claude Opus 5.5). Documents of the project went to them without this examination, for example development documents and the 28 test documents of the gold set.
- The planned eCH-0295 output has fields for submitters and co-signers. Thus, the output will contain names of persons with a public role.

### Code

The top of `src/` had 40 files on 06.10.2026: the stage scripts. 39 of them come from the 109 files in `src/` of the private project at commit `a1db1fb` of 06.10.2026 (108 scripts and one profile file). The new module `m03_render.py` contains a part of one more private module. Many file names, identifiers and comments are German. [repository-map.md](repository-map.md) describes the later files of `src/`.

| Part | Scripts | Content |
|---|---|---|
| Corpus | `m02_exporte_holen.sh`, `m02_korpus_basis.py`, `m02_korpus_geschaefte.py`, `m02_dokumente_extrakt.py`, `m02_dokumente_profil.py`, `m02_pdf_index.py` | Download of the exports. Figures of parliaments, affairs and documents, without full text and without file names. |
| eCH-0295 comparison | `m02_ech_regeln.py`, `m02_ech_abgleich.py` | Rules that relate OpenParlData values to eCH-0295 values. The coverage of the eCH-0295 fields. |
| Split and test set | `m02_synthese_split.py`, `m02_synthese_pilot_kandidaten.py`, `m00_pruefe_testset.py` | Split by whole parliaments, with the candidates of an earlier pilot that the split reads. A check that a document list contains no test document. |
| Selection | `m03_iso_gruppen.py`, `m03_iso_gruppe7.py`, `m03_iso_pool.py`, `m03_iso_paths.py` | Groups and training pool with fixed seeds. The data root, and the paths that keep the Docling files and the atoms of the test documents apart from the development files. |
| Docling and atoms | `m03_docling_zerlegen.py`, `m03_atome.py`, `m03_render.py` | PDF to blocks, blocks to atoms. The block form for the names of the Docling forms and for a token estimate of the atom script. |
| Isolation task | `m03_iso_hilfe.py`, `m03_iso_v4.py`, `m03_iso_jev4.py`, `m03_iso_hints.py`, `m03_iso_jev.py`, `m03_iso_mass.py` | Fixed answers, the 12 answers, the readout questions for Apertus, the layout hints, the measurement. The last two files are earlier versions that the current files import. |
| Model | `m04_text_branch_extrahieren.py`, `m04_iso_bundle.py`, `m04_iso_torch.py`, `m04_runpod.py` | Text weights, token bundle, training and readout, a client for the rented GPU. |
| Decoder and measurement | `m04_iso_import4.py`, `m04_iso_crf.py`, `m04_iso_report.py`, `m04_iso_errors.py` | Viterbi decoder, CRF decoder, gate values, error analysis. |
| Gold set | `m03_gold_select.py`, `m03_gold_bulk.py`, `m03_gold_prepare.py`, `m03_gold_review.py`, `m03_gold_report.py`, `m03_gold_freeze.py`, `m03_iso_review.py` | Lists with fixed seeds, the download of larger lists, preparation, the local review tool, reports, the record of the accepted task definition, the AI proposal. |
| Text rules | `m00_pruefe_dokumente.py` | A check of English text files against the text rules of the project. |

The readout questions for Apertus (the Apertus prompts) are in `src/m03_iso_jev4.py`. They are in German.

#### Edits for publication

An AI agent (Claude Opus 5.5) made these edits on 06.10.2026. No human examined them.

1. Each code file starts with the line `SPDX-License-Identifier: Apache-2.0`.
2. Data root: all data paths are below `PARLPDFECH_DATA` (`m03_iso_paths.DATA`). The scripts give paths in their records relative to the folder above the data root.
3. Fixed paths of the computer of the author are removed. Usage examples use the folder `data/`.
4. References to files of the private project are removed or replaced by a short explanation or by the technical report.
5. `m03_render.py` is the part of a private module that `m03_atome.py` needs. Its code is not changed. Only some comments are changed.
6. `m03_atome.py`: six short strings of its own check came from development documents. Invented values replace them. The other strings of the check contain no personal data. The usage examples use `DOC_ID` in place of document ids.
7. New options:
   - `m03_docling_zerlegen.py`: `--ocr-engine`.
   - `m04_text_branch_extrahieren.py`: `--quelle`, `--ziel`.
   - `m04_iso_import4.py`: the reference folders of the transitions. `run.json` records them.
   - `m04_iso_report.py`: the two agreement values of AI agents.
   - `m03_gold_freeze.py`: `--e20`, `--accepted-by`.
   - `m03_gold_review.py`: `--e20`, `--coder`.
8. New defaults: `m04_iso_bundle.py` uses the schema `v4b`. The default reference folders depend on the schema. `meta.json` records the reference folders relative to the folder above the data root, as in the private project.
9. `m03_iso_gruppen.py` and `m03_iso_pool.py` stop when their output file exists.
10. `m03_gold_bulk.py` has no selection step (chapter "Run it").
11. `m03_gold_report.py` writes the word "annotator" in its output keys.
12. `m04_runpod.py` reads the key and the ssh key file from the settings. The default key file is `~/.ssh/runpod_parlpdfech`. The command `create` stops if the public half of the key does not exist. Its text describes only the behaviour of the code.
13. `m03_docling_zerlegen.py` finds `pdftotext` in the search path and calculates the memory value correctly on Linux. A relative folder of `--ausgabe` is below the data root.
14. `m02_synthese_split.py`: two labels in its output table name the source "Phase 2" in place of a file of the private project.
15. The reference folders on the command line of `m03_iso_jev.py`, `m03_iso_jev4.py`, `m04_iso_bundle.py` and `m04_iso_crf.py` are relative to the data root.
16. `m02_exporte_holen.sh` makes its target folders. It downloads only files with simple names, and it writes the time of the download only when all files are downloaded without an error.
17. `m03_iso_paths.py`: the paths of the stratified sample have neutral names and two settings (chapter "Settings").
18. Each script shows its help text with `--help` and then stops. `m02_ech_abgleich.py` stops with a message when the exports are missing. `m03_iso_v4.py` stops with a message for an unknown command.
19. `m03_gold_freeze.py` records the E20 file relative to the folder above the data root. `m03_gold_review.py` finds it there from each working folder.
20. `m03_gold_review.py` answers only requests to `127.0.0.1` or `localhost` on its port. It saves only requests without an origin or from its own pages.
21. `m03_gold_bulk.py` and `m03_gold_prepare.py`: their texts state the known limits (chapter "Known limits of the code of the gold set").
22. `m04_iso_torch.py`: an empty `ISO_DEVICE` gives the default `cuda`.
23. `m00_pruefe_dokumente.py`: its list of German words has one word less.
24. On 12.10.2026, an AI agent changed the references to chapters of the technical report in `m03_iso_v4.py`, `m04_iso_crf.py` and `m04_iso_report.py`. They refer to version 1 of the report (commit `eaacef9`), because the report of 12.10.2026 has other chapters.

Checks of the edits (AI agent, Claude Opus 5.5, 06.10.2026):

- Each Python file compiles. `bash -n` accepts the shell script. Each import of a project module refers to a file in `src/`.
- The private modules and the public modules gave byte-identical outputs: the block form of `m03_render.py` and the atoms of `m03_atome.py`. The first run used 3 development documents and one synthetic document. A second run with the final code used 3 other development documents and one other synthetic document.
- The own check of `m03_atome.py` (option `--selbsttest`) gives the same result as the private version. Its printed output is the same, except one line with an invented value.
- Each script and the shell script ran with `--help` and an empty data root. Each one stopped with return code 0 and wrote no file.
- Small tests without project data examined these edits:
  - the host and origin check of `m03_gold_review.py` and the record of the E20 file;
  - the default reference folders of `m04_iso_bundle.py`;
  - the stop of `m04_runpod.py` without a key file;
  - `m02_exporte_holen.sh` with a fake download program.
- Apart from these checks, nobody ran the scripts again with the edited code.

#### Known limits of the code of the gold set

The private project changed five scripts of the gold set after commit `a1db1fb`. This repository has the code of `a1db1fb` with the edits above.

- `m03_gold_prepare.py`: the time limit applies to a chunk of up to 25 documents, not to each document. The script does not examine the content of a Docling result file.
- `m03_gold_bulk.py`: the hash in a URL of files.openparldata.ch is not the SHA-256 of the file. Thus, the column `sha_ok` of the download status has no meaning.
- `m03_gold_review.py`: the page images of all batches go to `<data>/gold/cache/pages_cropbox`. The batch `test_repeat` goes to `<data>/gold/test_repeat/`. Both folders are outside `<data>/gold/test`.
- The PDF files of the 28 test documents of `m03_gold_select.py` are in the folder of the stratified sample, together with development documents.

#### Names in the code

The code uses names of the private project. E15 to E32 are items of the decision list of the private project. Some of them are only proposed.

| Name | Meaning |
|---|---|
| E15 | Apertus only in bf16, no quantization. |
| E18 | Each readout gets the whole document. |
| E19 | The model writes no text. |
| E20 | The definition of the isolation task. Chapter 2.2 of version 1 of the technical report (commit `eaacef9`) gives a summary of version 4.1. |
| E26 | The split version 2, with the rule "no development document in the test set". |
| E29 | Cross-validation over groups of parliaments. |
| E32 | A human gold set by the author with AI support. |
| process rule 6 | The test documents stay apart from the development. A script examines each document list. |
| process rule 2.4 | The author checks 10 to 20 % of the documents a second time, blind and at least one day later. |
| G3a.1, G3a.3, G3a.11 | Criteria of gate 3a (version 1 of the technical report, commit `eaacef9`, chapter 5.3). |
| step 3.7, step 3.9 | Steps of the project plan: the groups and the pool, the readout. |
| `Gold` | The value of the test set in the split. |


## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: AI agents (Claude Opus 5.5) wrote the text on 06.10.2026 for the author, from the records and the code of the private project. On 12.10.2026, an AI agent moved it into this file. Later on 12.10.2026, an AI agent removed the open notes and changed the references to the technical report. On 14.10.2026, an AI agent changed the item on the PDF documents of the repository. On 15.10.2026, an AI agent (Claude Opus 5.5) added the history line and named the earlier converter and the product. It also dated 2 statements: the container file and the files of `src/`.

# Sources of the copied files

State: 12.10.2026, 15:30 CEST. The files below come from the private project of the author, commit `7efdc54`. The private project is not public. `SOURCES.json` holds the same data in a machine form.

## How to examine the copies

`make test` runs `src/check_sources.py`. For each file below, the script does these checks:

1. The file in this repository has the SHA-256 of the column "Copy".
2. Code and prompt files without edits: the script removes line 1 (the line `SPDX-License-Identifier: Apache-2.0`). The result must have the SHA-256 of the column "Source".
3. Code files with edits: the script removes line 1 and examines the new text on the recorded lines. Then it makes these lines empty in the copy. The result must have the SHA-256 of the source file with the same lines empty (`masked_source_sha256` in `SOURCES.json`). Each edit keeps the number of lines.
4. The R2 template: the SHA-256 of its canonical JSON must be the template SHA-256 that the frozen head records (`2a48e04b…`).

Thus the published code is the code of the private project, with only the recorded edits. `SOURCES.json` does not repeat the old text of an edit. The old text held paths of the private computer or quotations of internal notes. Other old text held the internal role names of the AI agents, the first name of the author or the name of a person.

## Same output as the private converter

On 12.10.2026, an AI agent ran the copied converter (this repository, `make run`) and the private converter on the same 8 development documents: the 3 samples and the 5 development documents of the check script of the private writer. Results:

| Item | Result |
|---|---|
| eCH-0295 instances | 8 of 8 equal, byte for byte |
| `nos4` answer files of the runner | 8 of 8 equal, byte for byte |
| Provenance side files | 8 of 8 equal, except 4 keys (see below) |
| Runner records | 8 of 8 equal, except 2 keys (see below) |

Differences and their causes:

1. `datetime_generated`: the time of the run.
2. `decomposition_source` and `candidate_source`: the paths and the SHA-256 of the runner record and of the export record. The private run used other folders, and its runner records differ in the 2 keys of item 4.
3. `file_sha256` (SHA-256 of the PDF): the writer calculates it from the PDF file. This repository contains no PDF. The file `source.json` of each sample gives the SHA-256 of the PDF.
4. Runner record, key `admission`: `known` in the private run (development document), `selected` in this repository (sealed selection of `make run`). Key `inputs`: this repository has no prompt text file of the document (`atome_prompt`), so its SHA-256 is empty. The runner needs that file only for a question to Apertus (rule id R1).

## Files

### Converter (path 1)

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/converter/m05_iso_runner.py` | `91df23fd92add336…` | `src/m05_iso_runner.py` | `352ee843635088bb…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 6 to 6: comment or docstring: the first name of the author is replaced by "the author" |
| `src/converter/m03_gold_record.py` | `9685820235f4e326…` | `src/m03_gold_record.py` | `15b77f5c7f9f0bd2…` | line 1 added; lines 14 to 14: comment or docstring: the first name of the author is replaced by "the author"; lines 22 to 22: comment or docstring: the first name of the author is replaced by "the author"; lines 1228 to 1228: comment or docstring: the first name of the author is replaced by "the author" |
| `src/converter/m03_iso_hilfe.py` | `8a804aacd8925dc6…` | `src/m03_iso_hilfe.py` | `54aef51933965ff7…` | line 1 added |
| `src/converter/m03_iso_jev.py` | `566aac9a907f7c28…` | `src/m03_iso_jev.py` | `142b1b23a336558d…` | line 1 added |
| `src/converter/m03_iso_mass.py` | `c8f4e6d119c333e8…` | `src/m03_iso_mass.py` | `01187a779a6082e9…` | line 1 added |
| `src/converter/m03_iso_paths.py` | `795316d8652092cc…` | `src/m03_iso_paths.py` | `7e726c76a29aadd1…` | line 1 added |
| `src/converter/m03_iso_v4.py` | `eecf84e954682021…` | `src/m03_iso_v4.py` | `f3327021cc4febd3…` | line 1 added |
| `src/converter/m03_ladder.py` | `65a1857d2fcd49f8…` | `src/m03_ladder.py` | `953d66ee13e88a7f…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 6 to 6: comment or docstring: the first name of the author is replaced by "the author"; lines 866 to 866: note text of the measurement record (not used by the converter): the first name of the author is replaced by "the author"; lines 1250 to 1251: report text of the command report (not used by the converter): a quotation from a chat (internal note) is replaced; lines 1254 to 1254: report text of the command report (not used by the converter): the first name of the author is replaced by "the author" |
| `src/converter/m03_sub_assemble.py` | `155b12a06cf6b771…` | `src/m03_sub_assemble.py` | `d706d707fdb4a8b8…` | line 1 added; lines 2 to 2: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 45 to 45: code: the absolute path of the private computer is replaced by the folder above src (same folder in the private layout) |
| `src/converter/m03_sub_common.py` | `7dc3147cb03ac470…` | `src/m03_sub_common.py` | `9b8f4b7df485fccc…` | line 1 added; lines 5 to 5: comment or docstring: the first name of the author is replaced by "the author"; lines 7 to 8: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter/m03_sub_s1_role.py` | `3b2ebce55044d424…` | `src/m03_sub_s1_role.py` | `af0aa97caf1d1d22…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter/m03_sub_s2_switch.py` | `9481e3ac9a66e4a1…` | `src/m03_sub_s2_switch.py` | `6517a9b4ca7489b2…` | line 1 added; lines 2 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter/m03_sub_s5_type.py` | `b6a44316150d4753…` | `src/m03_sub_s5_type.py` | `624de1593d009124…` | line 1 added; lines 3 to 3: comment or docstring: the first name of the author is replaced by "the author"; lines 5 to 5: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter/m04_iso_cscs.py` | `a1f368a8e604604a…` | `src/m04_iso_cscs.py` | `daa345d4f3d8349f…` | line 1 added |
| `src/converter/m06_converter.py` | `4776d97a7f2bc57e…` | `src/m06_converter.py` | `c0b9a9d383abeafe…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter/m06_ech_ausgabe.py` | `61fe809e8fdaaf3c…` | `src/m06_ech_ausgabe.py` | `19ec1cbc47d4ca5f…` | line 1 added; lines 3 to 4: docstring: a quotation from a chat (internal note) is replaced by the goal in neutral words |
| `src/converter/m02_ech_regeln.py` | `511aab179205b8c4…` | `src/m02_ech_regeln.py` | `e2e37098ea069ff2…` | line 1 added |
| `src/converter/m03_isolierung_taxonomie.py` | `a01f6b2e96abaf9c…` | `src/m03_isolierung_taxonomie.py` | `6399981d967c43aa…` | line 1 added |
| `src/converter/m03_atome.py` | `e02324e356d83709…` | `src/m03_atome.py` | `3988f7ae9bfc172a…` | line 1 added; lines 63 to 63: docstring: path of the private computer |
| `src/converter/m03_iter2_aufgabe.py` | `7762aee793320945…` | `src/m03_iter2_aufgabe.py` | `11694a2ecb16d22b…` | line 1 added |
| `src/converter/m03_lehrer_vorgaben.py` | `a1bab9d530c8c801…` | `src/m03_lehrer_vorgaben.py` | `6075bf8cc59fce17…` | line 1 added |
| `src/converter/m06_ech_profil.yaml` | `fe7e49a343ebe190…` | `src/m06_ech_profil.yaml` | `b8a2c343b903ab8d…` | line 1 added |

### Method data of the converter

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/converter/method/ladder.json` | `9a53760a485a6c0b…` | `daten/iso/ladder/ladder.json` | `1b040f8cde2c5bcb…` | only the keys that the code reads; values equal |
| `src/converter/method/s1_selection.json` | `341eb9984018c75c…` | `daten/iso/sub/s1_role/combined_dev.json` | `eedcb4aeefd85d9f…` | only the keys chosen, sure_ids and apertus_prompt_sha256; values equal |

### Apertus head (path 2)

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/apertus_head/m05_cls_it2_head.py` | `4f2814ca386fe114…` | `src/m05_cls_it2_head.py` | `d1ddeca2b5435549…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/apertus_head/m05_cls_it2_states.py` | `30096142c6ccd9f7…` | `src/m05_cls_it2_states.py` | `81b5e4b56e8b3fe2…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/apertus_head/m05_cls_apertus.py` | `a1243b2490ec6a9f…` | `src/m05_cls_apertus.py` | `f3677338ec95a2c5…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 74 to 74: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/apertus_head/m05_cls_data.py` | `222a6a76b57bcf16…` | `src/m05_cls_data.py` | `88a0207465bd6e6d…` | line 1 added |
| `src/apertus_head/m04_kern.py` | `a92da107e45dde9e…` | `src/m04_kern.py` | `2aa0aa14ccb9dcb7…` | line 1 added; lines 19 to 19: comment: the first name of the author is replaced by "des Autors" |
| `src/apertus_head/m05_cls_verify_critic_counts.py` | `cb5134bae4b3f2d2…` | `src/m05_cls_verify_critic_counts.py` | `4556b83b19edd64c…` | line 1 added |
| `src/apertus_head/m07_h_vm_states.py` | `f52de43fef7b8a89…` | `src/m07_h_vm_states.py` | `3d79ba6113dff82e…` | line 1 added; lines 3 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/apertus_head/m02_dokumente_extrakt.py` | `27c4f06bf50c4930…` | `src/m02_dokumente_extrakt.py` | `3bb74ee58e9e9ff7…` | line 1 added; lines 33 to 33: docstring: path of the private computer |
| `src/apertus_head/m02_dokumente_profil.py` | `da5cb82279a1cc21…` | `src/m02_dokumente_profil.py` | `4d84fd721bd224db…` | line 1 added; lines 21 to 21: docstring: path of the private computer |
| `src/apertus_head/m03_iso_hilfe.py` | `8a804aacd8925dc6…` | `src/m03_iso_hilfe.py` | `54aef51933965ff7…` | line 1 added |
| `src/apertus_head/m03_iso_jev.py` | `566aac9a907f7c28…` | `src/m03_iso_jev.py` | `142b1b23a336558d…` | line 1 added |
| `src/apertus_head/m03_iso_mass.py` | `c8f4e6d119c333e8…` | `src/m03_iso_mass.py` | `01187a779a6082e9…` | line 1 added |
| `src/apertus_head/m03_iso_paths.py` | `795316d8652092cc…` | `src/m03_iso_paths.py` | `7e726c76a29aadd1…` | line 1 added |
| `src/apertus_head/m03_iso_v4.py` | `eecf84e954682021…` | `src/m03_iso_v4.py` | `f3327021cc4febd3…` | line 1 added |

### Prompts

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/prompts/s1_role.txt` | `1b3b6dd3e22f8b71…` | `src/prompts/s1_role.txt` | `a458b4258d86c895…` | line 1 added |
| `src/prompts/s2_switch.txt` | `5556ece00cd29ee4…` | `src/prompts/s2_switch.txt` | `9e910a1b4dd43446…` | line 1 added |
| `src/prompts/s3_frame.txt` | `15802fb8f207b363…` | `src/prompts/s3_frame.txt` | `0d1b2a0be2811817…` | line 1 added |
| `src/prompts/s4_title.txt` | `3c3c1c74526ec0b4…` | `src/prompts/s4_title.txt` | `799455710a320eb1…` | line 1 added; lines 14 to 14: prompt example: the name of a real person is replaced by "X" |
| `src/prompts/s5_type.txt` | `93132a7cc56d18f6…` | `src/prompts/s5_type.txt` | `6949ca9cc36704a9…` | line 1 added |
| `src/prompts/r2_v1_de.template.json` | `8551d9fd0ce5eeb5…` | `src/m05_cls_apertus.py` (constants `SYSTEM`, `DOC_HEAD`, `SEP`, `Q_R2_DE`, `LETTERS_DE`, `OPTIONS`) | `f3677338ec95a2c5…` | none |

### Sample input

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `samples/26171/input/atoms.json` | `2ad0622a850dc22d…` | `daten/iso/atome/26171.json` | `2ad0622a850dc22d…` | none |
| `samples/26171/input/docling.json` | `febb52f3ac01b861…` | `daten/iso/docling/26171.json` | `febb52f3ac01b861…` | none |
| `samples/26171/input/export.json` | `fe3103ba9599225e…` | output of `src/m06_converter.py export` on the OpenParlData exports of 04.10.2026 | – | none |
| `samples/714840/input/atoms.json` | `0c3c74be512490f6…` | `daten/iso/atome/714840.json` | `0c3c74be512490f6…` | none |
| `samples/714840/input/docling.json` | `dfbb63375b3e15bf…` | `daten/iso/docling/714840.json` | `dfbb63375b3e15bf…` | none |
| `samples/714840/input/export.json` | `ebf5f2b6b755fbb8…` | output of `src/m06_converter.py export` on the OpenParlData exports of 04.10.2026 | – | none |
| `samples/879163/input/atoms.json` | `bec495c273a56baa…` | `daten/iso/atome/879163.json` | `bec495c273a56baa…` | none |
| `samples/879163/input/docling.json` | `4c1f7e5f288adcab…` | `daten/iso/docling/879163.json` | `4c1f7e5f288adcab…` | none |
| `samples/879163/input/export.json` | `d081d9005890cf93…` | output of `src/m06_converter.py export` on the OpenParlData exports of 04.10.2026 | – | none |
| `samples/pdf_index.csv` | `9a7246b9206abe89…` | `daten/analyse/pdf/docs_pdf_index.csv.gz` | `c7390de9c03012bb…` | the rows of the 3 samples only, not compressed |
| `samples/languages.csv` | `31647ee64cf05825…` | `daten/analyse/lehrer_stichprobe/auswahl_lehrer.csv` | `75887e61eecc02fd…` | the columns doc_id, sprache, sprache_quelle of the 3 samples only |

The full SHA-256 values are in `SOURCES.json`. The line numbers of an edit are the line numbers of the source file. In the copy, they are one higher, because of the added line 1.

Frozen files of path 1: the freeze records of gate 3a version 4 give a SHA-256 for each source file of the runner and of the writer. The source files above have these values, for example `352ee843…` for `src/m05_iso_runner.py` and `c0b9a9d3…` for `src/m06_converter.py`.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) made this file and `SOURCES.json` with a script, on 12.10.2026. No human examined it.

# Sources of the copied files

State: 14.10.2026, 13:45 CEST. The files below come from the private project of the author, commit `6c7fdee`. The files of the earlier converter (path 1) did not change after commit `7efdc54` of 12.10.2026. The private project is not public. `SOURCES.json` holds the same data in a machine form.

Product and history: the sections "Converter of the values read from the PDF", "Prompts of the values template" and "App tree" hold copies of the product. The other sections are history of 12.10.2026. "Converter (path 1)", "Method data of the converter" and "Sample input" are the earlier converter. "Apertus head (path 2)" is the earlier R2 head. "Prompts" holds the prompts S1 to S5 of the earlier converter and its studies, and the R2 prompt. The reader in `src/converter_gj/` imports 21 modules and the profile file of the earlier converter, and 5 modules of the earlier R2 head.

## How to examine the copies

`make test` runs `src/check_sources.py`. For each file below, the script does these checks:

1. The file in this repository has the SHA-256 of the column "Copy".
2. Code and prompt files without edits: the script removes line 1 (the line `SPDX-License-Identifier: Apache-2.0`). The result must have the SHA-256 of the column "Source".
3. Code files with edits: the script removes line 1 and examines the new text on the recorded lines. Then it makes these lines empty in the copy. The result must have the SHA-256 of the source file with the same lines empty (`masked_source_sha256` in `SOURCES.json`). Each edit keeps the number of lines.
4. The R2 template: the SHA-256 of its canonical JSON must be the template SHA-256 that the frozen earlier R2 head records (`2a48e04b…`).

Thus the published code is the code of the private project, with only the recorded edits. `SOURCES.json` does not repeat the old text of an edit. The old text held paths of the private computer or quotations of internal notes. Other old text held the internal role names of the AI agents, the first name of the author or the name of a person.

## Same output as the private earlier converter (12.10.2026)

On 12.10.2026, an AI agent ran the copied earlier converter (this repository, `make run`, now `make run-earlier`) and the private converter on the same 8 development documents: the 3 samples and the 5 development documents of the check script of the private writer. Results:

| Item | Result |
|---|---|
| eCH-0295 instances | 8 of 8 equal, byte for byte |
| `nos4` answer files of the runner | 8 of 8 equal, byte for byte |
| Provenance side files | 8 of 8 equal, except 4 keys (see below) |
| Runner records | 8 of 8 equal, except 2 keys (see below) |

Differences and their causes:

1. `datetime_generated`: the time of the run.
2. `decomposition_source` and `candidate_source`: the paths and the SHA-256 of the runner record and of the export record. The private run used other folders, and its runner records differ in the 2 keys of item 4.
3. `file_sha256` (SHA-256 of the PDF): the writer calculates it from the PDF file. The folder `samples/` contains no PDF. The file `source.json` of each sample gives the SHA-256 of the PDF. The app has a copy of the 3 PDF files with the same SHA-256 (`app/data/samples/<doc>/source.pdf`).
4. Runner record, key `admission`: `known` in the private run (development document), `selected` in this repository (sealed selection of `make run`, now `make run-earlier`). Key `inputs`: this repository has no prompt text file of the document (`atome_prompt`), so its SHA-256 is empty. The runner needs that file only for a question to Apertus (rule id R1).

This file records no output comparison of `src/converter_gj/` or of the app with the private project. `make test` compares their copies by the SHA-256 of each file.

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

### Converter of the values read from the PDF (`src/converter_gj/`)

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/converter_gj/m11_rules_pdf.py` | `b230ab46630f7412…` | `src/m11_rules_pdf.py` | `1ba501786fa361f2…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 97 to 97: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it); lines 472 to 472: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_values_base.py` | `ac9540f269e1a8bd…` | `src/m11_values_base.py` | `92a75106966ae917…` | line 1 added; lines 1 to 1: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 19 to 19: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 681 to 681: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 688 to 688: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it); lines 984 to 984: code string: the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_value_norm.py` | `6f9872e7891dd9b7…` | `src/m11_value_norm.py` | `0966639df3a425c1…` | line 1 added |
| `src/converter_gj/m11_values_dates_responder.py` | `f03f5603057dac1c…` | `src/m11_values_dates_responder.py` | `323406333d390da4…` | line 1 added; lines 1 to 1: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_values_title.py` | `7bec55cbf6c9a94e…` | `src/m11_values_title.py` | `e92f86226b8ef4f0…` | line 1 added; lines 1 to 1: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 1956 to 1956: code string: the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_values_type_number.py` | `e9e94346bb0a691b…` | `src/m11_values_type_number.py` | `8514d505e40b6de3…` | line 1 added; lines 1 to 1: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 1391 to 1391: code string: the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_cascade.py` | `d0b6b9fdb79f479f…` | `src/m11_cascade.py` | `b4fb41bab7905aff…` | line 1 added; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_cascade.yaml` | `75d094b22cd0d92b…` | `src/m11_cascade.yaml` | `ec8f7a51ae8e69ee…` | line 1 added; lines 3 to 3: text: the internal role names of the AI agents are replaced by "AI agent"; lines 11 to 11: text: the internal role names of the AI agents are replaced by "AI agent"; lines 660 to 660: text: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_values_cascade.py` | `be17463db876ff88…` | `src/m11_values_cascade.py` | `91aed34f49a7d0d8…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 30 to 30: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 41 to 41: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_values_combined.py` | `4c2f49354f082ac8…` | `src/m11_values_combined.py` | `4de6deaa7fd9ac91…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_writer.py` | `d8604eb054279878…` | `src/m11_writer.py` | `8a70b0f5574f6781…` | line 1 added; lines 2 to 2: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_validate.py` | `36eac021ec24871d…` | `src/m11_validate.py` | `9a2f3327ecf26947…` | line 1 added; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>"; lines 5 to 5: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 369 to 369: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_value_cal.py` | `90288805c33e5f7e…` | `src/m11_value_cal.py` | `b71331f89c1bffb8…` | line 1 added; lines 2 to 2: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 450 to 450: comment: the id of an internal workflow run or task is replaced by "<id>"; lines 822 to 822: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_prompts_values.py` | `2e5d9225094c8485…` | `src/m11_prompts_values.py` | `c32896531bb8ee6f…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m11_value_reference.py` | `d02f2f4953c3440b…` | `src/m11_value_reference.py` | `6c184b6888f16786…` | line 1 added; lines 444 to 444: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it); lines 480 to 480: code string: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m11_label_schema.yaml` | `e94273247aabd72b…` | `src/m11_label_schema.yaml` | `ace138c2a0cf9091…` | line 1 added; lines 1 to 1: text: the id of an internal workflow run or task is replaced by "<id>"; lines 2 to 2: text: the internal role names of the AI agents are replaced by "AI agent"; lines 3 to 3: text: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_guard.py` | `f551b87cbc443f0f…` | `src/m10_guard.py` | `1290d740ec49bb5b…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_rules.py` | `f9e05c2ee3e1caef…` | `src/m10_rules.py` | `9b349f855fd363c0…` | line 1 added; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 491 to 491: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it); lines 580 to 580: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m10_prompts.py` | `73725f6f5a24aadc…` | `src/m10_prompts.py` | `afa15e27806eb32d…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 5 to 5: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 18 to 18: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_vm_states.py` | `fa52615deec0864b…` | `src/m10_vm_states.py` | `3cd1eb9f1b66034e…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_calibrate.py` | `c1aba018bb27fe15…` | `src/m10_calibrate.py` | `03df26e311c3d31e…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>"; lines 5 to 5: docstring: the id of an internal workflow run or task is replaced by "<id>"; lines 165 to 165: code string: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m10_cascade.py` | `f905766b44e4b92f…` | `src/m10_cascade.py` | `21cea21a75fb2a16…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>" |
| `src/converter_gj/m10_pipeline.py` | `4f784aeb4d43e656…` | `src/m10_pipeline.py` | `329cc6e3778b9a7b…` | line 1 added; lines 5 to 5: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 6 to 6: docstring: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>"; lines 97 to 97: code string: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m10_design.py` | `234689e8576d094c…` | `src/m10_design.py` | `9e6b912ed0ba1f5b…` | line 1 added; lines 5 to 5: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 6 to 6: docstring: the internal role names of the AI agents are replaced by "AI agent"; the id of an internal workflow run or task is replaced by "<id>"; lines 1532 to 1532: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it); lines 1533 to 1533: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m10_docs.py` | `86171eb4133b2d8c…` | `src/m10_docs.py` | `80110478861dd413…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_gaps.py` | `5f27b102c3e2751f…` | `src/m10_gaps.py` | `58750027ed407962…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 5 to 5: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_rdf.py` | `e96ac2a5d096555a…` | `src/m10_rdf.py` | `e61face996fd44cb…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_validate.py` | `176735bcd23657c5…` | `src/m10_validate.py` | `20af9f10b3f7bde5…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_writer.py` | `5f547e946c2d3e00…` | `src/m10_writer.py` | `71830486948ab76d…` | line 1 added; lines 3 to 3: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m10_score.py` | `570d8940de8f16f7…` | `src/m10_score.py` | `aca5bd0997b7a5cb…` | line 1 added; lines 4 to 4: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 32 to 32: docstring: the first name of the owner is replaced by "the author"; lines 959 to 959: code string: the internal role names of the AI agents are replaced by "AI agent" (the string is a text of a record or a message; the code does not compare it) |
| `src/converter_gj/m10_label_schema.yaml` | `62eab07f9995f430…` | `src/m10_label_schema.yaml` | `07b779a759f55264…` | line 1 added; lines 2 to 2: text: the internal role names of the AI agents are replaced by "AI agent"; lines 3 to 3: text: the internal role names of the AI agents are replaced by "AI agent" |
| `src/converter_gj/m03_ech_export_schema.yaml` | `619f048bada5eb0d…` | `src/m03_ech_export_schema.yaml` | `69fccc1816c2e660…` | line 1 added |

### Prompts of the values template (`src/prompts/gj_values_v1_de/`)

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `src/prompts/gj_values_v1_de/README.txt` | `7c3d82ce89159a38…` | `daten/gj_values/prompts/gj_values_v1_de/README.txt` | `90cd22e449800aff…` | line 1 added |
| `src/prompts/gj_values_v1_de/system.txt` | `ccaf693cd225980b…` | `daten/gj_values/prompts/gj_values_v1_de/system.txt` | `1791a20972be0d8b…` | line 1 added |
| `src/prompts/gj_values_v1_de/prefix_format.txt` | `d2a986da6bcf0267…` | `daten/gj_values/prompts/gj_values_v1_de/prefix_format.txt` | `51726e9b38c5f58c…` | line 1 added |
| `src/prompts/gj_values_v1_de/q0_document_kind.txt` | `48979bbfe2709f89…` | `daten/gj_values/prompts/gj_values_v1_de/q0_document_kind.txt` | `3ef2421f237b7734…` | line 1 added |
| `src/prompts/gj_values_v1_de/q1_affair_type.txt` | `326a5ea40ce74f13…` | `daten/gj_values/prompts/gj_values_v1_de/q1_affair_type.txt` | `93dbbc3b33ec8cf2…` | line 1 added |
| `src/prompts/gj_values_v1_de/q2_block_values.txt` | `1003ed436175b014…` | `daten/gj_values/prompts/gj_values_v1_de/q2_block_values.txt` | `e22c095af34fba03…` | line 1 added |
| `src/prompts/gj_values_v1_de/template.json` | `ed0b8972fbc980ac…` | `daten/gj_values/prompts/gj_values_v1_de/template.json` | `ed0b8972fbc980ac…` | none |

### App tree (`app/`): files with an edit

| Copy | SHA-256 of the copy | Source | SHA-256 of the source | Edits |
|---|---|---|---|---|
| `app/layout/src/m03_atome.py` | `e02324e356d83709…` | `src/m03_atome.py` | `3988f7ae9bfc172a…` | line 1 added; lines 63 to 63: docstring: a path of the private computer is replaced by a neutral word |
| `app/layout/src/m03_docling_zerlegen.py` | `ae279267e2fec087…` | `src/m03_docling_zerlegen.py` | `b6401f6277027590…` | line 1 added; lines 38 to 38: docstring: a path of the private computer is replaced by a neutral word |
| `app/layout/src/m03_sub_assemble.py` | `155b12a06cf6b771…` | `src/m03_sub_assemble.py` | `d706d707fdb4a8b8…` | line 1 added; lines 2 to 2: docstring: the internal role names of the AI agents are replaced by "AI agent"; lines 45 to 45: code: the absolute path of the private computer is replaced by the folder above src (same folder in the private layout) |

The full SHA-256 values are in `SOURCES.json`. The line numbers of an edit are the line numbers of the source file. In the copy, they are one higher, because of the added line 1.

Frozen files of the earlier converter (path 1, gate 3a version 4, 12.10.2026): the freeze records give a SHA-256 for each source file of the runner and of the writer. The source files above have these values, for example `352ee843…` for `src/m05_iso_runner.py` and `c0b9a9d3…` for `src/m06_converter.py`.

The other files of `app/` come from the package of the private project, commit `6c7fdee`: the command `make -C package dist-src` makes the source tree, and `src/m11_public_app.py` copies it to `app/`. `app/DIST-MANIFEST.json` gives the SHA-256 and the size of each of the 211 files. `make test` compares each file with this list. The list has 2 more keys:

- `publication_edits`: the 3 files of the table above and the list of the code layout (`app/layout/layout_manifest.json`).
- `publication_additions`: the 3 PDF files of the samples (`app/data/samples/<doc>/source.pdf`). The tool that makes the source tree does not copy a PDF file. The app needs the PDF of a sample: it puts a copy into each sample result. The 3 PDF files are public documents of the parliaments. `app/data/samples/index.json` gives the URL of the publisher of each PDF, and the chapter "Samples" of `README.md` gives the URL of the copy of OpenParlData. `app/.gitignore` and `app/.dockerignore` have one line that lets these 3 files in.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) made this file and `SOURCES.json` with a script, on 12.10.2026. An AI agent made them again on 14.10.2026 and wrote the paragraph on the other files of `app/`. On 15.10.2026, an AI agent (Claude Opus 5.5) marked the earlier converter and the earlier R2 head as history, in the text outside the tables.

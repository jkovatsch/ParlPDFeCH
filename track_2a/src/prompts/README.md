# Prompts for Apertus

The prompts of the current method are in 2 folders. The text files at the top of this folder are history: the prompts of the earlier converter and of the earlier R2 head of 12.10.2026.

| Folder | Questions | Use |
|---|---|---|
| [`gj_values_v1_de/`](gj_values_v1_de/README.txt) | Value questions `Q0`, `Q1` and `Q2` | In the one fixed run of 13.10.2026, linear heads on these questions gave values for 2 of the 7 fields: `Q1` the affair type, `Q2` the first author (high head probability only). `Q0` did not enter. The app does not use these heads. |
| [`gj_jev_v1_de/`](gj_jev_v1_de/README.md) | Block-role questions `D1` and `B1`, and the prefix of the 2 templates | Block labels. The variants B1-S and B1-L were measured on 44 validation documents against labels from an AI. They did not enter the run. The app uses the heads `D1` and `B1` for the block labels of the 3 samples, from stored states. |

All prompts are for Apertus-v1.5-8B (bf16). The prompt text to the model is German. In each prompt, the whole document comes first and the question comes last. Apertus generates no text. In the current method, a linear head reads the hidden state of layer 20 at the last token of a question. The earlier converter read the probabilities of a fixed list of answers (S1). The earlier R2 head read the hidden state of layer 16.

License: Apache-2.0. Line 1 of each text file is `# SPDX-License-Identifier: Apache-2.0`. Line 1 is not a part of the prompt. A program removes it before use.

## Value questions: folder `gj_values_v1_de/`

These are the value questions `Q0`, `Q1` and `Q2` of the method of the technical report. They use the prefix of `gj_jev_v1_de`.

| File | Content |
|---|---|
| `gj_values_v1_de/README.txt` | The description: the prefix, the suffix of each question, the read-out and the heads. |
| `gj_values_v1_de/system.txt` | The system text. |
| `gj_values_v1_de/prefix_format.txt` | The chat frame and the format of a block line. |
| `gj_values_v1_de/q0_document_kind.txt` | Question `Q0`: the kind of the document (one time for each document). It did not enter the run. |
| `gj_values_v1_de/q1_affair_type.txt` | Question `Q1`: the affair type (one time for each document). It entered the run. |
| `gj_values_v1_de/q2_block_values.txt` | Question `Q2`: which head values a block states (one time for each block). Only the first author with a high head probability entered the run. |
| `gj_values_v1_de/template.json` | The full template record with the source of each option (byte-equal copy). |

## Block-role questions: folder `gj_jev_v1_de/`

| File | Content |
|---|---|
| `gj_jev_v1_de/README.md` | The description: the read-out, the layer, the meaning of each letter, the LoRA variant. |
| `gj_jev_v1_de/system.txt` | The system text, the document head, the separator and the answer start. |
| `gj_jev_v1_de/prefix_format.txt` | The chat frame and the format of a block line. |
| `gj_jev_v1_de/d1_question.txt` | Question D1: which text parts of eCH-0295 the document holds (4 options). |
| `gj_jev_v1_de/b1_question.txt` | Question B1: the part of eCH-0295 to which one block belongs (6 options). |
| `gj_jev_v1_de/template.json` | The exact template record, a byte-equal copy of the template file of the job records. |
| `gj_jev_v1_de/PROMPTS.sha256` | The SHA-256 of the 5 files above. |

Notes:

1. Apertus writes no text here. Each document has one prefix, and each decision has one short question.
2. A head reads the hidden state at the last token of the question. The heads D1 and B1 read layer 20.
3. The variant with a LoRA adapter (B1-L) uses the same template. It was measured on 13.10.2026. The adapter is not published, and B1-L did not enter the run or the app.
4. The template SHA-256 is `72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c`. `gj_jev_v1_de/README.md` gives its definition.
5. `python src/check_prompts.py` builds the template again from the text files and examines the SHA-256 values.

## Earlier converter and R2 head (12.10.2026, history)

History: the prompts of the earlier converter (path 1) and of the earlier R2 head (path 2), state of 12.10.2026. They are not prompts of the current method. Path 1 is the earlier rule converter in `../converter/` (`make run-earlier`). Path 2 is the earlier Apertus head of task R2 in `../apertus_head/`.

| File | Task | Used by | Part of the earlier method `nos4`? |
|---|---|---|---|
| `s1_role.txt` | S1: the role of a document (proposal, response, combined, minutes, committee, other) | Path 1, runner `src/converter/m05_iso_runner.py`, only for a document with the S1 rule id R1 | Yes: the frozen method `nos4` of path 1 (SHA-256 of the prompt without line 1: `a458b4258d86…`) |
| `s2_switch.txt` | S2: the points where the author changes | Sub-task study of 08.10.2026 | No. The method uses the S2 rule. |
| `s3_frame.txt` | S3: text line or frame line | Sub-task study of 08.10.2026 | No. The method `nos4` gives "text" to each atom without a fixed answer. |
| `s4_title.txt` | S4: the title of the affair | Sub-task study of 08.10.2026 | No. The method `nos4` uses no S4. |
| `s5_type.txt` | S5: the type of a paragraph in an author family | Sub-task study of 08.10.2026 | No. The method uses the S5 rule. |
| `r2_v1_de.txt`, `r2_v1_de.template.json` | R2: does the document hold a response of the executive (yes or no) | Path 2, head `src/apertus_head/` | No. On 12.10.2026, the gate of path 2 was OPEN. |

Notes:

1. `s1_role.txt` names development documents as examples (`[shots]`). The texts of these documents are not in this repository. The runner needs them only for a question to Apertus. `make run-earlier` asks no question.
2. `r2_v1_de.template.json` is the exact template. The SHA-256 of its canonical JSON is the template SHA-256 that the frozen head records (`2a48e04b…`). `make test` examines this.
3. The project tried more prompt variants for R1 and R2. They are in `src/apertus_head/m05_cls_apertus.py` (`VARIANTS`).

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026.
- The part for the folder `gj_jev_v1_de/`: an AI agent (Claude Opus 5.5) wrote it on 13.10.2026.
- The part for the folder `gj_values_v1_de/`: an AI agent (Claude Opus 5.5) wrote it on 14.10.2026.
- On 15.10.2026, an AI agent (Claude Opus 5.5) put the prompts of the current method first and marked the earlier prompts as history.

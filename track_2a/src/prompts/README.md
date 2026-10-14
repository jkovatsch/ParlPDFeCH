# Prompts for Apertus

All prompts are for Apertus-v1.5-8B (bf16). The prompt text to the model is German. In each prompt, the whole document comes first and the question comes last. Apertus writes no text: code reads the probabilities of a fixed list of answers, or the head of path 2 reads a hidden state.

License: Apache-2.0. Line 1 of each text file is `SPDX-License-Identifier: Apache-2.0`. Line 1 is not a part of the prompt. `make run-earlier` removes it before the runner reads the prompt.

| File | Task | Used by | Part of the frozen method? |
|---|---|---|---|
| `s1_role.txt` | S1: the role of a document (proposal, response, combined, minutes, committee, other) | Path 1, runner `src/converter/m05_iso_runner.py`, only for a document with the S1 rule id R1 | Yes: the frozen method `nos4` of path 1 (SHA-256 of the prompt without line 1: `a458b4258d86…`) |
| `s2_switch.txt` | S2: the points where the author changes | Sub-task study of 08.10.2026 | No. The method uses the S2 rule. |
| `s3_frame.txt` | S3: text line or frame line | Sub-task study of 08.10.2026 | No. The method `nos4` gives "text" to each atom without a fixed answer. |
| `s4_title.txt` | S4: the title of the affair | Sub-task study of 08.10.2026 | No. The method `nos4` uses no S4. |
| `s5_type.txt` | S5: the type of a paragraph in an author family | Sub-task study of 08.10.2026 | No. The method uses the S5 rule. |
| `r2_v1_de.txt`, `r2_v1_de.template.json` | R2: does the document hold a response of the executive (yes or no) | Path 2, head `src/apertus_head/` | Not a part of the converter. The gate of path 2 is OPEN. |

Notes:

1. `s1_role.txt` names development documents as examples (`[shots]`). The texts of these documents are not in this repository. The runner needs them only for a question to Apertus. `make run-earlier` asks no question.
2. `r2_v1_de.template.json` is the exact template. The SHA-256 of its canonical JSON is the template SHA-256 that the frozen head records (`2a48e04b…`). `make test` examines this.
3. The project tried more prompt variants for R1 and R2. They are in `src/apertus_head/m05_cls_apertus.py` (`VARIANTS`).

## Prompts of the new converter: folder `gj_jev_v1_de/`

The table above is for the earlier rule converter and for path 2. The new converter has its own template, `gj_jev_v1_de`. Status of the new converter and of each of its results: EXCEPTION, NOT RELEASED.

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
3. The candidate with a LoRA adapter uses the same template.
4. The template SHA-256 is `72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c`. `gj_jev_v1_de/README.md` gives its definition.
5. `python src/check_prompts.py` builds the template again from the text files and examines the SHA-256 values.

## Prompts of the value questions: folder `gj_values_v1_de/`

These are the value questions `Q0`, `Q1` and `Q2` of the method of the technical report. They use the prefix of `gj_jev_v1_de`. Status of each result: EXCEPTION, NOT RELEASED.

| File | Content |
|---|---|
| `gj_values_v1_de/README.txt` | The description: the prefix, the suffix of each question, the read-out and the heads. |
| `gj_values_v1_de/system.txt` | The system text. |
| `gj_values_v1_de/prefix_format.txt` | The chat frame and the format of a block line. |
| `gj_values_v1_de/q0_document_kind.txt` | Question `Q0`: the kind of the document (one time for each document). It did not enter the run. |
| `gj_values_v1_de/q1_affair_type.txt` | Question `Q1`: the affair type (one time for each document). It entered the run. |
| `gj_values_v1_de/q2_block_values.txt` | Question `Q2`: which head values a block states (one time for each block). Only the first author with a high head probability entered the run. |
| `gj_values_v1_de/template.json` | The full template record with the source of each option (byte-equal copy). |

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. No human examined it.
- The part for the folder `gj_jev_v1_de/`: an AI agent (Claude Opus 5.5) wrote it on 13.10.2026. No human examined it.
- The part for the folder `gj_values_v1_de/`: an AI agent (Claude Opus 5.5) wrote it on 14.10.2026. No human examined it.

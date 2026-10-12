# Prompts for Apertus

All prompts are for Apertus-v1.5-8B (bf16). The prompt text to the model is German. In each prompt, the whole document comes first and the question comes last. Apertus writes no text: code reads the probabilities of a fixed list of answers, or the head of path 2 reads a hidden state.

License: Apache-2.0. Line 1 of each text file is `SPDX-License-Identifier: Apache-2.0`. Line 1 is not a part of the prompt. `make run` removes it before the runner reads the prompt.

| File | Task | Used by | Part of the frozen method? |
|---|---|---|---|
| `s1_role.txt` | S1: the role of a document (proposal, response, combined, minutes, committee, other) | Path 1, runner `src/converter/m05_iso_runner.py`, only for a document with the S1 rule id R1 | Yes: the frozen method `nos4` of path 1 (SHA-256 of the prompt without line 1: `a458b4258d86…`) |
| `s2_switch.txt` | S2: the points where the author changes | Sub-task study of 08.10.2026 | No. The method uses the S2 rule. |
| `s3_frame.txt` | S3: text line or frame line | Sub-task study of 08.10.2026 | No. The method `nos4` gives "text" to each atom without a fixed answer. |
| `s4_title.txt` | S4: the title of the affair | Sub-task study of 08.10.2026 | No. The method `nos4` uses no S4. |
| `s5_type.txt` | S5: the type of a paragraph in an author family | Sub-task study of 08.10.2026 | No. The method uses the S5 rule. |
| `r2_v1_de.txt`, `r2_v1_de.template.json` | R2: does the document hold a response of the executive (yes or no) | Path 2, head `src/apertus_head/` | Not a part of the converter. The gate of path 2 is OPEN. |

Notes:

1. `s1_role.txt` names development documents as examples (`[shots]`). The texts of these documents are not in this repository. The runner needs them only for a question to Apertus. `make run` asks no question.
2. `r2_v1_de.template.json` is the exact template. The SHA-256 of its canonical JSON is the template SHA-256 that the frozen head records (`2a48e04b…`). `make test` examines this.
3. The project tried more prompt variants for R1 and R2. They are in `src/apertus_head/m05_cls_apertus.py` (`VARIANTS`).

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. No human examined it.

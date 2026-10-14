# Prompts of the new converter: template `gj_jev_v1_de`

Status of the new converter and of each of its results: EXCEPTION, NOT RELEASED.

This folder holds the exact text that the new converter gives to Apertus-v1.5-8B (bf16). The prompt text is German. The job builder of the project holds the same text as constants (`m10_prompts.py`, module version `m10-prompts-1`).

## 1. How the converter uses Apertus

1. Apertus writes no text. The converter starts no text generation.
2. Each document gets one prefix. The prefix holds the system text and the whole document, block by block.
3. Each decision gets one short question. The question is a suffix after the prefix.
4. The model reads the prefix and one suffix. The converter then reads the hidden states at the last token.
5. This step has the name read-out. The last token is the end of the answer start `Antwort:`.
6. A small classifier (a head) calculates one probability for each answer option from this state.
7. Code makes each value of the output from these probabilities. The text of the output comes from the PDF.

A document has two types of decision:

| Decision | Count for one document | Question file |
|---|---|---|
| D1 | 1 | `d1_question.txt` |
| B1 | 1 for each block | `b1_question.txt` |

The prefix is the same for all suffixes of a document. Thus the model reads the document one time, and each question is a short pass.

## 2. Which layer

The state extraction stores the state after the decoder layers 8, 12, 16, 20, 24, 28 and 32. Each state has 4,096 values.

The heads D1 and B1 read layer 20 (read from the design record of the project, keys `d1.layer` and `b1.layer`). The project selected this layer on development documents. The head is a logistic regression on the standardized state.

The letters of the options are a part of the question text only. The converter does not read a letter from the model. The classes of a head are the options in the order of the letters.

## 3. Files

| File | Content |
|---|---|
| `system.txt` | The system text, the document head, the separator and the answer start. They come from the template `r2_v1_de`. |
| `prefix_format.txt` | The chat frame, the format of a block line, the limit of 12 first words, and the option name of each letter. |
| `d1_question.txt` | The exact text of the question D1 with its 4 options. |
| `b1_question.txt` | The exact text of the question B1 with its 6 options and 3 placeholders. |
| `template.json` | The full template record. It is a byte-equal copy of the template file of the job records. |
| `PROMPTS.sha256` | The SHA-256 of the 5 files above. |

Line 1 of each text file is `# SPDX-License-Identifier: Apache-2.0`. Line 1 is not a part of the prompt. A program removes it before use.

Format of `system.txt` and `prefix_format.txt`: each line after line 1 is `<name> = <JSON value>`. Thus a line end in a value shows as `\n`.

Format of the two question files: the exact question text follows line 1. One line end follows the text and is not a part of it.

## 4. The prefix

The prefix has these parts in this order:

1. The chat frame `chat_head` with the system text. It holds the lines `Deliberation: disabled` and `Tool Capabilities: disabled`.
2. The document head `Dokument:` and one line end.
3. One line for each block in the order of reading: `[B<n> | S.<page> | <Docling label>] <block text>`.
4. Two line ends (`sep`).

Rules for a block line:

- `B<n>` is the block number. `S.<page>` is the page number. The label is the layout label of Docling.
- Each line break in the block text becomes one space.
- A block with no text gives only the part in square brackets.
- Headers and footers of a page stay in. The builder cuts no text.

The chat frame is equal to the output of the chat template of the model. The job builder examines this before each build.

A document with more than 32,768 prefix tokens gets no states.

## 5. The question D1 (document)

The question asks which text parts of eCH-0295 the document holds.

| Letter | Meaning |
|---|---|
| A | Only the submitted text, with or without a reasoning. |
| B | Only the response of the executive, with or without a recommendation. |
| C | The two: submitted text and response. |
| D | None of these text parts. |

## 6. The question B1 (one block)

The question asks to which part of eCH-0295 one block belongs. It names the block number, the page and the first 12 words of the block. A block with no words gets the words `(ohne Text)`.

| Letter | Option name | Meaning |
|---|---|---|
| A | `submitted` | The text that a member or a group submitted. |
| B | `reasoning` | The reasoning for the submitted text. |
| C | `response` | The response of the executive. |
| D | `recommendation` | The recommendation of the executive to the parliament. |
| E | `title` | The title of the affair. |
| F | `none` | No text part of eCH-0295. |

Placeholders of `b1_question.txt`: `{block}` (for example `B7`), `{page}` and `{first_words}`.

## 7. The suffix

A suffix has these parts in this order: the question text, the chat frame `chat_tail`, the answer start `Antwort:`.

The order of the suffixes of a document: D1, then one B1 suffix for each block in the order of reading.

Token ids: the tokenizer reads the prefix and the suffix one after the other, each with no added special tokens. The ids of the prefix come first.

## 8. The LoRA variant

The candidate with a LoRA adapter (B1-L) uses the same template and the same B1 items. Its two job records hold the same template SHA-256 (read: key `template_sha256` of the two manifest files).

Its model call is the prefix and one B1 suffix. Its head reads the output of the final norm at the last token. The LoRA weights are active in this call.

## 9. Template identity and check

| Item | Value |
|---|---|
| Template id | `gj_jev_v1_de` |
| Template SHA-256 | `72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c` |
| SHA-256 of the file `template.json` | `9a6d72a0b9577b13ce3a328e0e83dacdf60fb38796f1f9b964d0e6bfff545100` |

Definition of the template SHA-256:

1. Read `template.json` as JSON and remove the key `sha256`.
2. Write the JSON with sorted keys, with the separators `,` and `:` and with `ensure_ascii=False`.
3. Calculate the SHA-256 of the UTF-8 bytes of this text.

The job records and the state files of the project hold the template SHA-256.

Command, from the folder `track_2a/`:

```text
python src/check_prompts.py
python src/check_prompts.py --example
```

The program `check_prompts.py` builds the template again from the 4 text files only. The result must be equal to `template.json` in value and in bytes. The program also calculates the three SHA-256 values. The option `--example` prints the prefix and the suffixes of a small invented document.

Result of 13.10.2026 on one computer (measured): all checks pass, and the exit code is 0.

## 10. Two paths in `template.json`

`template.json` records two files with a path relative to the private project folder:

| Key | String | What it is |
|---|---|---|
| `system_text_source.file` | `src/m05_cls_apertus.py` | The code file with the system text. This repository has a copy with recorded edits: `src/apertus_head/m05_cls_apertus.py`. |
| `prefix_format.chat_template.file` | `daten/modelle/apertus-v1.5-8b-text-bf16/chat_template.jinja` | The chat template file in the local model folder. This repository holds no model file. |

The two SHA-256 values next to these paths are the values of the private files. `SOURCES.json` records the relation of the code copy to its source.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 13.10.2026. No human examined it.

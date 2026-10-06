# Technical report — ParlPDFeCH

Version of 06.10.2026. Written in English to the STE rules (ASD-STE100, Issue 9). AI agents (Claude Opus 5.5) wrote this report from the records and the code of the private project. On 06.10.2026, two more AI agents (Claude Opus 5.5) compared the statements of fact with these records and this code. One did this before and one after the assembly of the repository. An AI agent applied their corrections. No human examined this report. [pending: check of this report by the author]

Status: the converter is not complete. The isolation stage did not meet its gate. No value in this report is accuracy against a reference with human acceptance. The isolation values are agreement with AI references. No human finished the check of a document.

- **Track:** Track 2A — Extracting Parliamentary Affairs from PDFs into One Common Structure (OpenParlData)
- **Event:** Online
- **Team:** [pending: team name] — Jonathan Kovatsch
- **Demo:** [pending: demo link]

Terms of this report:

| Term | Meaning |
|---|---|
| atom | One line of a Docling block or one row of a table, with page, frame and character range. Code can divide a line at a column gap, a frame boundary or a sentence boundary. |
| page furniture | Text that is not content: page numbers, headers and footers that repeat, file names, folder paths. |
| readout | A forward pass, after which code reads the probabilities of fixed answer tokens at one position. The model writes no text. |
| AI reference | The answers for the atoms of a document that AI agents (Claude Opus 5.5) made. No human accepted it. |
| gate | A list of criteria with limits at the end of a part of the project plan. The project writes the limits before the measurement. Only the author can accept a gate. |
| gold set | The test documents whose answers have human acceptance. |
| fold | One part of the cross-validation. The fold model learns from no document of the parliaments of its measured groups. |
| out-of-fold set | The development documents that a fold model read but did not learn from. The model learned from no document of their parliaments. |
| final group | A group of 8 documents of 8 parliaments for one measurement. Before it, the AI agent that developed the method saw only counts of this group. |
| arm | One of two training settings that the project compared in fold Y before the choice of the final model (chapter 3.2). |
| private project | The project folder of the author. It is not public. |

## 1. Summary

The OpenParlData exports of 04.10.2026 contain the metadata of 325,599 parliamentary affairs from 89 parliaments. The challenge says that much content is only in PDF documents, for example the question, the response with its reasoning and the decision. ParlPDFeCH develops a converter from these PDF documents to the working draft eCH-0295. In its design, Apertus-v1.5-8B makes each decision by readout of fixed answer tokens and writes no text. Thus, each text value comes word for word from the PDF, with its page and its position. The first stage with Apertus is the isolation. It gives each atom of a document one of 12 answers: one of 11 text answers from the text fields of eCH-0295, or "no text field". A fixed rule gives page furniture to some atoms. A LoRA adapter on Apertus-v1.5-8B in bf16 did not meet the gate of this stage. On a final group of 8 documents, it got a labelled boundary F1 of 0.455. On 39 out-of-fold documents, it got 0.315. The gate limit is 0.95. These values are agreement with AI references from AI agents (Claude Opus 5.5). Before the gate result, the agreement between AI agents that coded without an anchor was 0.917 and 0.944. The gold set has 0 documents. The stages after the isolation have no code in this repository.

## 2. Architecture

### 2.1 Pipeline stages

| Stage | Component | Where it runs | Status on 06.10.2026 |
|---|---|---|---|
| 1 Docling | Docling 2.133.0 with its layout and table models. Apple Vision OCR (`ocrmac`) for scans. | Mac (macOS) | Code |
| 2 Atoms | Code divides each block into atoms. It checks that the atoms cover the full text exactly one time. | CPU | Code |
| 3 Isolation | Fixed answers by rules, layout hints, readout with Apertus and a LoRA adapter, Viterbi decoder | GPU for the training and the readout, CPU for the other parts | Code. The training needs AI references that are not in this repository. Gate 3a is NOT MET. |
| 4 Labeling | Type and values of each segment | – | No code |
| 5 Classification | One option for a whole document | Mac (MLX) | One pilot (chapter 5.6). Its code is not in this repository. |
| 6 Relations | Connections between segments, for example an answer unit and its parliamentary question | – | No code |
| 7 Normalization | Dates, numbers and person identifiers from code rules | – | No code |
| 8 Output | eCH-0295 instance (I95) with a LinkML profile for provenance; schema validation | – | No code in this repository |

The project uses I95: the file `ech-0295_affairs/input/schema.yaml` of the eCH working repository at commit `3cab44d`. [pending: diagram of the pipeline in `docs/`]

### 2.2 Isolation task

The isolation task has version 4.1 of 05.10.2026. Its text answers come only from the TextBlock fields of eCH-0295 (I95). The author did not accept this task definition yet.

| Answer | eCH-0295 (I95) field |
|---|---|
| `title` | `Affair.title`, text type `title` |
| `short_title` | `Affair.title`, text type `short_title` |
| `submitted` | `Submission.texts`, text type `submitted` |
| `reasoning` | `Submission.texts`, text type `reasoning` |
| `response` | `ResponseStep.texts`, text type `response` |
| `recommendation` | `ResponseStep.texts`, text type `recommendation` |
| `summary` | the texts of the step of its author, text type `summary` |
| `committee_recommendation` | `CommitteeDecision.text` |
| `speech` | `Speech.text` |
| `proposition` | `Proposition.text` |
| `vote` | `Vote.text` |
| `none` | no text field |

Fixed answers (`src/m03_iso_hilfe.py`). A method cannot change them:

| Rule | Answer | Condition |
|---|---|---|
| R1 | page furniture | A page number or a continuation mark |
| R3 | `none` | A picture atom, or a logo fragment of 1 or 2 characters |
| R4 | page furniture | A header or footer text that occurs in the same zone of another page |
| R5 | page furniture | File data: file name, path, document property field, underscore line, rotated line |

Project rules where I95 gives no decision:

| Rule | Content |
|---|---|
| T | The title is the printed heading of the affair. It includes a line directly above or below it with only the affair type, the document type or a number. |
| F | Only the body of a submitter text or of an executive answer fills a text field. Salutation, greetings, signatures, lists of co-signers, place and date, attachments and the resolution formula of the executive get `none`. |
| L | `reasoning`, `summary` and `short_title` need a label or a heading with the same meaning. `recommendation` needs its own paragraph with only the formal proposal. |
| H | A heading or a label belongs to the text that it introduces. |
| Q | A quotation belongs to the text that contains it. |
| O | In a protocol, the oral answer of the member of the executive is `response`. Other oral statements are `speech`. |
| N | A footnote belongs to the last text on the same page before it. A caption belongs to the text around it. |

The review of the AI references found cases that these rules did not decide. Seven clarifications decide most of them. Two points stay open (chapter 5.5). An example of a clarification: a decree that the executive brings before the parliament is `submitted`, because the executive is its sponsor in I95.

### 2.3 Readout

The readout format is `iso-jev4-v2` (`src/m03_iso_jev4.py`):

1. A system message and an instruction in German. The instruction names the eCH-0295 text fields and their meanings.
2. The whole document: one line for each atom, with its id, its page, the features from the atom script and its text.
3. Each atom line again, with its layout hints in square brackets, followed by `->`. This is the readout position.
4. The 12 answers are the letters A to L. Each letter is one token.
5. The sequence contains no answers. Thus, no decision depends on an earlier decision. One forward pass gives 12 log probabilities for each atom.
6. An atom with a fixed answer keeps it.

The layout hints (`src/m03_iso_hints.py`) are facts of the PDF or of the metadata of the own affair, never a decision:

- the zone: top 12 % or bottom 10 % of the page;
- the left edge, relative to the most frequent left edge of the document: indented, centered or right;
- a line height of 1.25 times the median or more, or of 0.8 times the median or less;
- a vertical gap of more than 1.6 times the median gap;
- the first atom of a page;
- a text of 4 or more characters that occurs in another atom of the document;
- the title anchor: atoms whose words are words of the affair title in the OpenParlData metadata. Against the AI references, the title anchor had a precision of 0.889 and a recall of 0.463.

### 2.4 Decoder

The Viterbi decoder (`src/m04_iso_import4.py`, version 2) decides the answers of a document:

1. The fixed answers stay.
2. The state is the last text answer. `none` and page furniture do not change the state.
3. A transition cost applies only where a text block starts. The cost is the log probability of the first answer, or of the change from one text answer to the next.
4. These probabilities come from the converted AI references of version 4 of the training documents of the same fold. These AI references are older than the later steps of chapter 4.4: the review of groups 1 to 6, the check of rule O and the seven clarifications. The training and the measurement use version 4.1. The documents of the parliaments of the final group are never counted.
5. The weight of the transition cost is 1. The project set it before the runs.

A CRF decoder (`src/m04_iso_crf.py`) is a second method. The rule: use it on the final group only if it is better on the out-of-fold set. It was not better (chapter 5.3).

## 3. Use of Apertus

- **Model:** `swiss-ai/Apertus-v1.5-8B`, text weights only, bf16
- **How it is used:** fine-tuning (LoRA adapter) and inference by readout of answer tokens
- **Where it runs:** local weights. Training and readout with PyTorch on rented H100 GPUs (80 GB, one for each run) in European data centers. Development with MLX on a Mac mini M4 (32 GB).

### 3.1 Text weights

Apertus-v1.5-8B has parts for text, image and audio. `src/m04_text_branch_extrahieren.py` keeps only the text weights. It renames them to the schema of Apertus 1.0 and cuts the embedding to the 131,072 text tokens. The values of the kept weights stay in bf16 and do not change. The project uses no quantized model.

### 3.2 Adapter and training

`src/m04_iso_torch.py`, version 2:

| Setting | Value |
|---|---|
| Adapter | LoRA on all linear layers of the upper 16 of 32 layers. Rank 16, scale 20. Adapter weights in float32. |
| Training | Learning rate 1e-4, 5 epochs, gradient accumulation 2, seed 42 |
| Loss | Cross entropy over the 12 answers at the readout positions. Atoms with a fixed answer have no loss. Mean over the atoms of a document, then over the documents of an update. |
| Checkpoint | The lowest loss on 19 monitor documents. The parliaments of the monitor documents have no training documents. |
| Arms | Arm 1: random order. Arm 2: epoch 1 in the order of increasing length. The arm with the lower monitor loss in fold Y wins. |

| Run | Training documents | Updates | Chosen checkpoint | Monitor loss |
|---|---|---|---|---|
| Fold Y, arm 1 | – | 400 | update 400 | 0.889 |
| Fold Y, arm 2 | – | 400 | update 360 | 0.992 |
| Fold X, arm 1 | 114 | 285 | update 171 | 1.208 |
| Final model, arm 1 | 184 | 460 | update 460 | 0.944 |

Arm 1 had the lower monitor loss and was chosen. On groups 3 and 5, arm 2 had the higher labelled boundary F1 (0.528 against 0.415). The rule did not use these values.

### 3.3 Precision and backends

The project compared next-token log probabilities on synthetic text: 2,620 positions in German, French and Italian. The code of this comparison is not in this repository.

| Comparison | Mean absolute difference | Top-1 agreement |
|---|---|---|
| Apertus-v1.5-8B on the CSCS inference API against the local bf16 model | 0.032 | 0.992 |
| Local bf16 model with a different order of calculation (noise) | 0.034 | 0.995 |
| Local model with 8-bit weights, only as a scale | 0.055 | 0.992 |
| PyTorch on the rented GPU against CSCS | 0.031 | 0.995 |

For the first three rows, the differences count only tokens with a log probability above -5. Result: the mean absolute differences of CSCS (0.032) and of PyTorch (0.031) are not larger than the noise of bf16 (0.034). The 8-bit and 4-bit models were only a scale. The project does not use them.

### 3.4 Apertus-v1.5-70B, in-context readout

On 05.10.2026, the project measured an in-context readout with Apertus-v1.5-70B on the CSCS inference API. The input was 0 or 4 annotated example documents and then the target document. A regular expression limited the output to the answer letters. There was no training. Only documents with the triage verdict PASS went to the API. The values are in chapter 5.2. The CSCS API was only for development. The converter does not need it. The code of this trial is not in this repository.

### 3.5 Other models

The template asks for a clear description of the role of each other model. This table names each other model whose output is in the code, the values or the texts of this repository. It also names each other model that runs in the converter.

| Model | Open weights | Role | In the converter |
|---|---|---|---|
| Claude Opus 5.5 (AI agents) | No | Code, analyses, AI references (coding, review, adjudication), triage of personal data, code reviews, literature search, text of this report and its fact check | No |
| Docling layout and table models | Yes | Stage 1 | Yes |
| Apple Vision OCR (`ocrmac`) | No | OCR of scans, only on macOS | Yes, at this time. [pending: an OCR engine with open weights for the container] |
| Apertus-v1.5-70B (CSCS API) | Yes | In-context readout trial | No |

The template permits other open-weights models to support the development. Claude Opus 5.5 and Apple Vision OCR have closed weights. [pending: question to the organizers about these two models]

### 3.6 Earlier attempts

This list gives earlier attempts with Apertus and with code rules. These attempts used earlier task definitions. The code of attempts 2 and 3 is not in this repository. `src/m03_iso_jev.py` and `src/m04_iso_bundle.py` still contain the sequence format of attempt 1.

1. Readout with the answers in the sequence, line by line: the model copied its own earlier answer. For example, after one `submitted` answer it kept `submitted` after the start of the response. The current format has no answers in the sequence.
2. Rule isolators with regular expressions and atom features: boundary F1 below 0.4 against an earlier AI reference. They could not cover the formats of many parliaments.
3. A readout head on the hidden states of Apertus (logistic regression, sequence head): labelled boundary F1 0.422 for the sequence head.

## 4. Data

### 4.1 Source and license

- OpenParlData exports of 04.10.2026, 13:26 UTC, and the PDF documents at https://files.openparldata.ch/doc/.
- 325,599 affairs in 89 parliaments: the Confederation, 26 cantons, 61 municipalities and Liechtenstein. 907,472 document rows, 84.5 % of them PDF. AI agents (Claude Opus 5.5) calculated these figures with scripts. Other scripts calculated the main figures again.
- OpenParlData publishes its data under CC BY 4.0. Attribution: "Source: OpenParlData.ch". The API description and the project page do not say if this license applies to the PDF copies.
- This repository contains no PDF document and no export. `data/` is empty.
- The project did not ask the persons in the documents for consent. The challenge page says that the corpus contains only material that the parliaments published.

### 4.2 Split

The split assigns whole parliaments to one set: training set 55, validation set 19, test set 15 parliaments.

- No parliament with a development document is in the test set.
- A text that is in more than one set is removed from the test set and from the validation set (417 documents).
- No affair of the test set has a structured text in the exports.
- The test set has no Confederation, no Romansh and no Italian canton.

### 4.3 Sets for the isolation

| Set | Documents | Selection | Use |
|---|---|---|---|
| Groups 1 to 5 | 40 documents of 28 parliaments of the training set and the validation set | Script with seed 20261005, balanced by state level, language, scans and document role | Measurement in the folds. Out-of-fold set: the 39 documents with triage PASS. |
| Group 6 | 8 documents | Seed 20261006 | Development group (see below) |
| Group 7, the final group | 8 documents of 8 parliaments | Seed 20261010 | One readout, one measurement |
| Training pool | 265 documents, not more than 6 for each parliament. 246 of them have not more than 16,384 tokens and an AI reference. | Seed 20261007 | Training |
| Token bundle `v4b` | 274 documents, 60 of them for readout only | Documents with triage PASS | Training and readout on the GPU |

Fold Y measures groups 3 and 5. Fold X measures groups 1, 2 and 4. A fold model never learns from a document of the parliaments of its measured groups.

Group 6 was an earlier final group. The project measured the agreement of the AI coders on it two times, with earlier task definitions. An AI agent also saw parts of its AI reference. Thus, group 6 became a development group, and a script with a new seed selected group 7.

No method learned from a document of the 8 parliaments of group 7: not for the training, not for the monitor and not for the decoder. 60 documents of these parliaments in groups 1 to 6 and in the pool are for readout only. Before the final measurement, the AI agent that developed the method (Claude Opus 5.5) saw only counts of group 7.

### 4.4 AI references

All AI agents were instances of Claude Opus 5.5. No human accepted an AI reference.

| Set | How the AI agents made the AI reference |
|---|---|
| Groups 1 to 6 | Two AI coders and one AI adjudicator for each group, in three rounds (group 6: two rounds) with earlier task definitions. Then a conversion to version 4. Then a review by two AI review coders and one AI adjudicator for each group. Then the seven clarifications. |
| Group 7 | Two AI coders and one AI adjudicator, with version 4. Then one AI agent applied the seven clarifications: 1 atom in 2 documents changed. |
| Training pool | One AI coder and one AI review agent for each batch of 8 or 9 documents. Then the conversion, a check of rule O on 36 documents and the clarifications. |

### 4.5 Personal data

- The documents contain names of persons, for example members of a parliament or of an executive. Some documents contain personal data of third parties.
- Some documents went to a rented GPU (Runpod) or to the CSCS inference API. Before that, two AI agents (Claude Opus 5.5) examined each of these documents for personal data of third parties. A document passed only with the verdict PASS from both AI agents.
- Result: 313 documents of groups 1 to 6 and of the pool, 300 PASS and 13 FAIL. Group 7: 8 of 8 PASS.
- A document gets FAIL when it has data about an identifiable third party of these kinds: sensitive data, private contact data, a date of birth, data about a minor, or a detailed personal case.
- This examination did not apply to the AI agents (Claude Opus 5.5). Documents of the project went to them without this examination, for example development documents and the 28 test documents of the gold set.
- The planned eCH-0295 output has fields for submitters and co-signers. Thus, the output will contain names of persons with a public role.

## 5. Evaluation

### 5.1 Task, metric and comparison basis

- Task: the isolation of chapter 2.2.
- Comparison basis: the AI references of version 4.1. They have no human acceptance. Thus, each isolation value is agreement with AI agents, not accuracy.
- Gate limits: written before the measurement. Version 3 of the criteria was written before the training runs. Version 3.1 was written before any method value on the out-of-fold set or on the final group.

| Value | Definition |
|---|---|
| labelled boundary F1 | A boundary is a position in the sequence of text atoms of the AI reference where the answer changes. A boundary of the method is correct only when the answers on both sides agree with the AI reference. |
| inner boundaries | Boundaries that do not start after the title. |
| text omission | Text atoms of the AI reference that the method gives `none` or page furniture, divided by all text atoms of the AI reference. |
| text intrusion | Text atoms of the method that the AI reference gives `none` or page furniture, divided by all text atoms of the method. |
| text class error | Atoms with a text answer on both sides but different answers, divided by all atoms with a text answer on both sides. |
| document exact rate | The share of documents with all boundaries correct and no omission, intrusion or class error. |
| lower bound | The harmonic mean of the one-sided Jeffreys 95 % bounds of precision and recall. Together, the two bounds hold with about 90 %. |

### 5.2 Results

| Setup | Metric | Result |
|---|---|---|
| Baseline: Apertus-v1.5-70B, in-context readout, 0 example documents, no training; groups 1 to 5 | labelled boundary F1 | 0.115 |
| Baseline: Apertus-v1.5-70B, in-context readout, 4 example documents, no training; groups 1 to 5 | labelled boundary F1 | 0.280 |
| Earlier LoRA adapter, trained on the classes of an earlier task definition; groups 3 and 5 | labelled boundary F1 | 0.512 |
| Ours: LoRA adapter, arm 1, fold Y; groups 3 and 5 | labelled boundary F1 | 0.415 |
| Ours: LoRA adapter, arm 1; out-of-fold set (39 documents) | labelled boundary F1 | 0.315 |
| Ours: final model; final group (8 documents) | labelled boundary F1 | 0.455 |
| Agreement of AI agents: blind coding of 7 documents against the AI reference | labelled boundary F1 | 0.944 |
| Agreement of AI agents: the two coders of the final group | labelled boundary F1 | 0.917 |

Notes:

1. The two baseline rows used the AI references before the review and before a later correction of the conversion. The records contain no later value for them. Thus, they are not strictly comparable with the other rows.
2. In the two baseline rows, a document without an output counts as "no text field" for all atoms. For example, the run with 0 example documents gave outputs for 35 documents.
3. The other method rows use the AI references of version 4.1.
4. The records contain no value of Apertus-v1.5-8B without training for this task. The readout head of chapter 3.6 used the hidden states of Apertus-v1.5-8B without an adapter, with a trained head.

### 5.3 Gate 3a

| Criterion | Gate limit | Out-of-fold set (39 documents) | Final group (8 documents) | Status |
|---|---|---|---|---|
| The author accepts the task definition. | acceptance | – | – | OPEN |
| The author accepts the version of the reference. | acceptance | – | – | OPEN |
| Agreement of the two AI coders of the final group | 0.95 or more | – | 0.917 | NOT MET |
| Each atom has exactly one answer. Page furniture only on fixed atoms. | all files | 166 files, 0 invalid | 8 files, 0 invalid | MET |
| Labelled boundary F1 | 0.95 or more. Lower bound 0.90 or more (out-of-fold set). Not more than 2 false and 2 missed boundaries (final group). | 0.315, lower bound 0.227. 20 correct, 46 false, 41 missed. | 0.455, lower bound 0.235. 5 correct, 5 false, 7 missed. | NOT MET |
| Labelled boundary F1, both sets together | lower bound 0.90 or more | 0.336, lower bound 0.251 | – | NOT MET |
| Text omission | 0.002 or less. Documents with an omission: 5 % or less, or 1 of 8. | 0.060 (25 of 39 documents) | 0.038 (5 of 8 documents) | NOT MET |
| Text intrusion | 0.01 or less | 0.041 | 0.014 | NOT MET |
| Document exact rate | 0.80 or more, or 7 of 8 | 0.103 (4 of 39) | 1 of 8 | NOT MET |
| Test documents in the development material | 0 | 0 in 603 items | – | MET |
| Documents sent to Runpod or CSCS without triage PASS | 0 | 0 | 0 | MET |
| Inner boundaries | information | 24, labelled recall 0.167 | 3, labelled recall 0.0 | – |
| Text class error | information | 0.237 | 0.125 | – |
| Scans | information | 12 documents: F1 0.313, omission 0.045 | 1 document: F1 0.5, omission 0.0 | – |
| Exact rate at a coverage of 100, 90, 80, 70 and 50 % (documents sorted by the lowest answer margin) | information | 0.10, 0.11, 0.10, 0.11, 0.15 | 0.13, 0.14, 0.17, 0.17, 0.25 | – |
| Method F1 minus the AI agreement 0.944, and minus 0.917 | information | -0.629, -0.602 | -0.490, -0.463 | – |

- Gate 3a result on 06.10.2026, 00:39: NOT MET. The gate is not ACCEPTED, because the two acceptance criteria are OPEN.
- Labelled boundary F1 for each group of the out-of-fold set: 0.19, 0.40, 0.21, 0.14, 0.64.
- The CRF decoder gave 0.280 on the out-of-fold set (omission 0.062, 1 of 39 documents exact). Thus, the final group used the Viterbi decoder.
- Number of final measurements: group 6 two times (agreement of the AI coders, earlier task definitions), group 7 one time.
- Before the runs, AI agents (Claude Opus 5.5) did a code review of the isolation pipeline. They found defects that changed measured values, for example a measurement that did not examine the class of a block. These defects were fixed before the runs of this chapter.

### 5.4 Agreement of the AI references

| Value | Labelled boundary F1 | Note |
|---|---|---|
| Two AI review coders, groups 1 to 6 | 0.993 | Both started from the converted AI references (anchored). |
| Converted against reviewed AI references, groups 1 to 6 | 0.910 | 33 of 48 documents exact. |
| Blind coding of 7 documents by one more AI agent, against the AI reference 4.1 | 0.944 | 5 of 7 documents exact. |
| Two AI coders of the final group | 0.917 | Coded before the seven clarifications. |
| Two blind AI coders, 48 documents of groups 1 to 6, after the clarifications (06.10.2026, after the gate result) | 0.983 | 41 of 48 documents equal. Against the AI reference 4.1: 0.949 and 0.932. |

The table gives no value on test documents. The project reports values on test documents only after all choices are fixed.

What follows from this table:

1. The two values of native codings of version 4 without an anchor before the gate result (0.917 and 0.944) are below the limit 0.95.
2. Thus, the gate limit was above the measured agreement of the AI references. The measurement cannot separate errors of the method from errors of the AI reference.
3. All AI coders are instances of one model. Their errors can be correlated. Their agreement can be higher than their accuracy.

### 5.5 Negative result: causes

This chapter gives the measured facts that limit the result. It does not rank them.

1. Size of the sets. The out-of-fold set has 61 boundaries in 39 documents. The final group has 12 boundaries. With 0 errors in 12 boundaries, the Jeffreys lower bound is 0.855. With one shifted boundary, the bound gets to 0.90 only with 38 or more boundaries.
2. Task definition. The task definition had six versions on 05.10.2026: 1, 2, 3, 3.1, 4 and 4.1. The seven clarifications changed the AI references of 56 documents. The coders of the final group worked before them. Two points stay open: where `reasoning` ends without a new label, and the position of a number line next to the title.
3. AI references. The AI references of groups 1 to 6 were converted from an earlier version and then reviewed. Of the measured documents, only group 7 has a native AI reference of version 4. The blind codings of 7 sample documents are native, but they are not the AI reference. After the conversion, four answers had no example in the AI references: `short_title`, `committee_recommendation`, `proposition` and `vote`, and `speech` had 13 atoms in 2 documents. The later review, the check of rule O and one clarification gave `vote` and other answers to some atoms. The AI reference of group 7 has `vote` atoms (item 6). The records contain no count of each answer in the AI references of version 4.1.
4. Conversion of the PDF. Text omission counts only atoms. Words that Docling does not give are not atoms. An AI agent (Claude Opus 5.5) compared Docling with `pdftotext` on 27 digital development documents: 65 of 26,409 words (0.25 %) were missing. The records contain no second count.
5. OCR. All scans of the development groups were converted with Apple Vision OCR. The atoms of a scan can change with another OCR engine.
6. Main errors. Whole blocks got the wrong author. In the final group, 55 atoms of `submitted` got `response`, and 17 atoms of `vote` got `submitted`. In the out-of-fold set, 358 atoms changed between `response` and `submitted`, and 161 atoms of `reasoning` got `response` or `submitted`.
7. Literature. On 05.10.2026, AI agents (Claude Opus 5.5) searched the literature. They found no published result with a boundary F1 of 0.95 for a comparable task on unseen sources.
8. Decoder. The transition probabilities of the Viterbi decoder come from the converted AI references of version 4, not from version 4.1 (chapter 2.4). The training and the measurement use version 4.1. The records contain no measurement of the effect of this difference.

Comparison with the earlier adapter, groups 3 and 5 (16 documents), Viterbi decoder:

| Method | AI reference before the review | AI reference 4.1 | Text class error (AI reference 4.1) |
|---|---|---|---|
| Earlier adapter (earlier classes, converted output) | 0.619 | 0.512 | 0.057 |
| Adapter of the gate runs, arm 1 (chosen) | 0.500 | 0.415 | 0.197 |
| Adapter of the gate runs, arm 2 | 0.549 | 0.528 | 0.246 |

1. The change of the AI reference lowers the earlier adapter from 0.619 to 0.512.
2. Against the same AI reference, the labelled boundary F1 values are in the same range (0.415 to 0.528).
3. The text class error of the adapters of the gate runs is 3.5 to 4.3 times the error of the earlier adapter.
4. The gate runs changed several items at the same time. No measurement separated them. Candidate causes: the frame classes of the earlier definition are now one answer `none`; one clarification gives `submitted` to texts of the executive in 11 pool documents; 60 documents of the parliaments of group 7 are not in the training; the layout hints; the loss for each document.
5. No training followed from this comparison. The gate rule stops the work after a gate that is NOT MET, until the author decides.

### 5.6 Pilot: classification of whole documents

This pilot is not a gate result. Its code is not in this repository.

- Task: the recommendation of the executive on a motion or a postulate. Seven options, for example accept, reject, or "none fits". The options relate to the eCH-0295 list `RecommendationEnum`.
- Comparison basis: silver labels from the OpenParlData events, made by a code rule. Two AI agents (Claude Opus 5.5) examined 80 examples. No human examined them.
- Setup: Apertus-v1.5-8B in bf16 with the whole document, on the Mac with MLX. Adapter on the upper 16 of 32 layers, rank 16, learning rate 1e-5, 800 of 1,957 training examples.

| Value against the silver labels (258 validation examples) | Baseline A (no adapter) | Adapter | Rule baseline |
|---|---|---|---|
| Share of answers equal to the silver label | 0.671 | 0.725 | 0.884 |
| Macro F1 | 0.619 | 0.739 | 0.886 |
| Share equal to the silver label, core subset (92 examples) | 0.783 | 0.641 | 1.000 |
| Calibration error (ECE) | 0.276 | 0.143 | – |

- The silver labels come from rules that are similar to the rule baseline. Thus, the rule baseline has an advantage. Without knowledge from the validation set, the rule baseline gives a share of 0.702.
- The core subset contains the examples where the document states the recommendation clearly. The rule baseline is equal to the silver label on it by construction.
- Against the silver labels, the adapter is better than baseline A in the share of equal answers, macro F1 and calibration. It is worse on the core subset. It is worse than the rule baseline in all values.
- These values are agreement with silver labels, not accuracy.

## 6. Limitations

1. No human finished the check of a document. The gold set has 0 documents. Each isolation value is agreement with AI agents of one model (Claude Opus 5.5).
2. The gate limit 0.95 is above the agreement of the AI references without an anchor before the gate result (0.917, 0.944).
3. One final measurement on 8 documents of 8 parliaments, with 12 boundaries.
4. One training seed for each run (seed 42). Two folds, not one fold for each group.
5. The arm choice and the checkpoints use 19 monitor documents.
6. The CRF decoder learns from the log probabilities of the fold models. On the final group, it would get the log probabilities of the final model, which learned from more documents.
7. The lower bound holds with about 90 %, not 95 %.
8. The test set has no Confederation, no Romansh and no Italian canton.
9. Text omission does not count words that Docling does not give.
10. Apple Vision OCR runs only on macOS and has closed weights. The atoms of scans can change with another OCR engine.
11. In the training pool, only documents with not more than 16,384 tokens have an AI reference. Each readout gets the whole document; the project does not cut documents.
12. After the conversion, four answers had no example in the AI references. The records contain no later count (chapter 5.5).
13. The converter has no code for the labeling, the relations, the normalization and the output. Thus, the converter gives no eCH-0295 output.
14. Some scripts in `src/` need data files or earlier outputs that are not in this repository (`README.md`, chapter "Run it").

## 7. Reproducibility

| Item | Value |
|---|---|
| Hardware | Mac mini M4 with 32 GB memory (Docling, atoms, text weights, token bundle). One rented H100 GPU with 80 GB memory for each training run, in European data centers. |
| Runtime | Python 3.12 with uv, Docling 2.133.0, `ocrmac`, MLX 0.32.3 and mlx-lm 0.32.0 on macOS, Poppler. On the GPU: PyTorch 2.8.0, transformers 5.18.0, peft 0.21.2 (recorded on 05.10.2026 for the first rented GPU). |
| Seeds | Groups 1 to 5: 20261005. Group 6: 20261006. Training pool: 20261007. Group 7: 20261010. Training: 42. Gold set lists: 20261006. Pilot documents without a proposal: 20261008. Bulk lists of the gold set: 20261007. |
| Code | The scripts in `src/` come from the private project at commit `a1db1fb` of 06.10.2026, with edits for publication (`README.md`, chapter "Code"). The gate 3a values were calculated before this commit. Nobody calculated them again with the edited code. |
| Token bundles (private files) | `v4b`: SHA-256 `8cd55bb32331240b67d136e0d3dfa1f82435c7ac3f0afbf72343f9802ba55409`. Final group: SHA-256 `264b59057892c5a5487607f0856a254f85a75683123090172bd201738da1f209`. |
| Gate criteria and task definition (private files) | Criteria version 3.1: SHA-256 `eb0db1d80843618e87cfd586c5633492df34c90ca55174101e39cbcd2e6c4ea0`. Task definition version 4.1: SHA-256 `afa1936f906a32942e401f52361bffc4dab601b6b2e4c1b7c877c2ac8097d6ad`. |
| `make run` | Not ready. It stops with a message. [pending: container and run target] |

The values of chapter 5 cannot be calculated again from this repository alone. The AI references, the document lists, the token bundles and the adapters are not public. [pending: decision of the author about the publication of the development document lists and the AI references]

Files in `src/` of the private project at commit `a1db1fb` that are not in this repository (70 of 109; 69 scripts and one profile file):

| Kind | Number | Reason |
|---|---|---|
| Historical | 12 | Earlier trials and one-time runs, for example with the 4-bit model or with extracts. |
| Replaced | 10 | A later method or format replaced them. |
| Work out of the planned order | 10 (9 scripts and the profile file of the eCH-0295 output prototype) | Their results are not a basis. |
| Role open | 11 | Scripts of the classification pilot and of earlier trials. |
| Analysis only | 20 | Analyses and checks of the data understanding and of the trials. |
| PDF inspection | 5 | Selection, download and examination of the inspection documents, and figures of the PDF index. They make the table `augenschein.csv` that the current pipeline reads. |
| MLX module | 1 | Shared training and readout code of the classification pilot. The current pipeline does not import it. |
| Source of `m03_render.py` | 1 | The atom script needs only a part of this module. `src/m03_render.py` contains this part, with the same code. |

## 8. Next steps

1. Pilot of the gold set: the author checks 20 development documents in the review tool. The tool measures the time for each document. The report gives the error of the AI references against the author.
2. The author accepts or changes the isolation task definition. A script records the accepted version.
3. The author checks the test documents. After 24 hours or more, he checks 15 % of them again, blind, for his agreement with himself.
4. New gate criteria, written before any method value on the test documents.
5. A decision by delegation of 05.10.2026 sets a latest date for gate 3a: 10.10.2026, 18:00. The author did not confirm this date yet. If the author does not accept gate 3a by then, the paths that need the isolation stop, for example the labeling. This report then shows them as a negative result.
6. [pending: decision of the author about more training runs and about the separation of the candidate causes of chapter 5.5]
7. A container for Linux with an OCR engine with open weights, and `make run`.
8. The output stage: eCH-0295 (I95) instances with a LinkML profile for provenance, and the schema validation.
9. The classification path and the cross-parliament question: "Does the parliament follow the recommendation of the executive?"
10. [pending: decision of the author about the publication of the adapter]

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced. Copyright 2026 Jonathan Kovatsch.

This license applies to this report. The code has the license Apache-2.0 (file `LICENSE` of the repository). The front page of the repository gives the full license table.

## References

- Hack Apertus, Track 2A (OpenParlData): https://hackapertus.notion.site/track-2a-openparldata
- Hack Apertus, terms and conditions, chapter 6: https://hackapertus.ch/terms-and-conditions
- Hack Apertus project template, commit `7f23822`: https://github.com/HackApertus/project-template
- OpenParlData: https://openparldata.ch; API: https://api.openparldata.ch; exports: https://files.openparldata.ch/exports/
- eCH working repository "Politische Geschäfte", commit `3cab44d`: https://github.com/swiss/political-affairs-ech-group
- Apertus-v1.5-8B: https://huggingface.co/swiss-ai/Apertus-v1.5-8B
- Apertus Acceptable Use Policy v1.5: https://github.com/swiss-ai/apertus-legal/blob/main/apertus_1.5/USAGE_POLICY.pdf
- Docling: https://github.com/docling-project/docling
- Jev readout principle: https://openjev.com
- ASD-STE100: https://asd-ste100.org

# Technical report, long version — ParlPDFeCH

- **Track:** Track 2A — Extracting Parliamentary Affairs from PDFs into One Common Structure (OpenParlData)
- **Version:** 15.10.2026. It replaces the texts of 13.10.2026 (block labels as the result) and 14.10.2026. The public report of 12.10.2026 was on the earlier converter.
- **Short version:** [`../technical_report.md`](../technical_report.md) (6 pages as a PDF). This file has no page limit.
- **Limits in one place:** [`limits.md`](limits.md). **Folders of the repository:** [`repository-map.md`](repository-map.md).

## How to read this file

1. A name in square brackets is the id of a number in [`../numbers.json`](../numbers.json). Example: 0.9431 [`R.affair_type.precision`].
2. The entry of an id gives the value, its set and its mark. It also gives its source file, the key in that file and the SHA-256 of that file. [`../numbers.md`](../numbers.md) lists the same entries for a person.
3. A table caption gives the id pattern of its cells. The id of a cell is that pattern with the field of its row.
4. An id can start with a short stem. Table 0 gives the stems.
5. Each chapter 1 to 8 has the number of the same chapter in the short version. Chapter 9 is the evidence. Chapter 10 lists the source files of the numbers.
6. A path that starts with `daten/` or `crisp-dm/` is a file of the private project. It is not in this repository.
7. This file names no document and no parliament of the run. It gives no value of a test document.

Table 0: the stems of the ids.

| Stem | Start of the full id | Numbers |
|:---|:---|:---|
| `R` | `values.last_run.rules_only.all` | the one fixed run, reader with rules only, all documents of the run |
| `RV`, `RG` | `values.last_run.rules_only.validation`, `values.last_run.rules_only.group7` | the same reader, validation documents and group 7 |
| `C`, `CV`, `CG` | `values.last_run.combined.all`, `.validation`, `.group7` | the combined reader in the 3 sets |
| `L` | `values.last_run` | other numbers of the run: sets, contact history, check by eye, spread |
| `D` | `values.round4` | development documents, round 4, reader with rules only |
| `H` | `values.heads2` | development documents, design of the Apertus heads |

Field keys: `affair_type`, `title`, `affair_number`, `submission_date`, `response_date`, `responder_name`, `first_author`.

Marks of an entry:

| Mark | Meaning |
|:---|:---|
| measured | A project script wrote the value into a result file. |
| derived | The numbers tool calculated the value from other entries, or counted the lines of a file. |
| read | The value is in a criteria file or in another document of the project. |
| protocol only | The value is only in the text of the work log. |
| reading check | An AI agent judged the value against the printed text of a document. |
| estimate | The source gives the value as an estimate. |

A table caption names the mark if it is not "measured".

Words of this file:

| Word | Meaning |
|:---|:---|
| the one fixed run of 13.10.2026 | The measurement on the documents of the sets validation and group 7. The values of each document were compared with the export one time. |
| correct, wrong | Equal or not equal to the export value, after the normalisation of addendum G of the criteria. |
| precision | correct / (correct + wrong) |
| found rate | (correct + wrong) / documents with a reference |
| share correct | correct / documents with a reference. It is the product of precision and found rate. |
| correct as printed | The judgement of an AI examiner in the check by eye. It is never mixed with "correct". |
| development documents | The documents that the rule authors read and that the heads were fitted on. |
| reader with rules only, combined reader | The 2 readers of the run. The combined reader adds the Apertus tiers that entered. |
| tier | One way to find a value, for example one rule or one Apertus head with one band. A tier has its own counts and its own probability. |
| unit | A value of a tier with the outcome equal or different against the export. |
| kind of the document | Stage 0 of the cascade, for example `proposal`, `response` or `combined`. |
| first author | The field `first_author`: the slot `Submission.sponsorship` with the role sponsor. |
| status certain, status unsure | The value status from the calibration on the development documents. |
| check by eye | 2 AI examiners read a sample of the run. The result is information only. |
| dossier | The evidence dossier of the run (chapter 9). It is a file of the private project. |

## 1. Summary

### 1.1 Goal

A PDF of a Swiss parliament goes in. An eCH-0295 record comes out. Each head value of the record (up to 7) is read from the PDF and has a probability. Each such value also has a page and a text span, except an affair type from an Apertus head. Identifiers and constants of the record have no probability. The OpenParlData export is the reference of the measurement. On development documents it also gives the fit labels of the Apertus heads. At run time no export value goes into a record.

### 1.2 Method

1. Docling gives the text blocks. A rule chain gives the role of the document and of each block, from the PDF alone.
2. The cascade of eCH-0295 uses the kind of the document and the affair type to select the slots that a document can state (chapter 2.3).
3. Rule readers read 7 head values: affair type, title, affair number, submission date, response date, responder and first author.
4. A calibration on 1,793 [`D.documents`] development documents of 44 [`D.parliaments`] parliaments gives each tier a probability and the status certain or unsure.
5. A value of a tier below 0.5 [`design.fixed.writer_floor`] goes into the label file only, not into a slot.
6. Apertus-v1.5-8B writes no text. Linear heads read its hidden state at the last token of a question.
7. 2 head tiers add values for 2 of the 7 fields: the affair type and the first author. The other values come from the rules.
8. A writer makes the record in Turtle and YAML, the label file and `<doc>.values.ttl` (chapter 2.1). A validator checks them.

### 1.3 The one fixed run and its main values

The one fixed run of 13.10.2026 compared the values of 872 [`R.documents`] documents of 26 [`L.parliaments.all`] parliaments with the export, one time. The documents are 804 [`L.documents.validation`] validation documents of 18 [`L.parliaments.validation`] parliaments and 68 [`L.documents.group7`] documents of 8 [`L.parliaments.group7`] more parliaments (group 7). AI agents had read each group-7 document before the run.

Table 1: the reader with rules only, all documents of the run. Ids: `R.<field>.precision`, `R.<field>.found_rate`, `R.<field>.share_correct`. Reference: the export.

| Field | Precision | Found rate | Share correct |
|:---|---:|---:|---:|
| `affair_type` | 0.9431 | 0.8402 | 0.7923 |
| `title` | 0.5179 | 0.9053 | 0.4688 |
| `affair_number` | 0.5275 | 0.4197 | 0.2214 |
| `submission_date` | 0.5289 | 0.5161 | 0.2729 |
| `response_date` | 0.5116 | 0.4057 | 0.2075 |
| `responder_name` | 0.9756 | 0.9152 | 0.8929 |
| `first_author` | 0.8125 | 0.5607 | 0.4556 |

The combined reader adds the 2 Apertus tiers. With them, the share correct of the affair type is 0.8675 [`C.affair_type.share_correct`], and that of the first author is 0.6028 [`C.first_author.share_correct`]. In the run the 2 tiers gave 59 [`C.tier.apertus_q1.units`] and 79 [`C.tier.apertus_q2_sponsor_hi.units`] values with a reference.

The block roles of the Apertus candidates B1-S and B1-L did not enter the run. The run used the block roles of the rule chain. In the app, the rules give each value. An own PDF needs `make setup-pdf` and `make run-native` (chapter 7.1).

AI agents wrote the method and examined it. No pass limit was fixed before the run. The main limit concerns 5 fields: the affair number, the 2 dates, the title and the first author. For each of them, fewer than half of the documents with a reference get the export value (chapter 6, L1).

### 1.4 What was measured, and what was not

| Item | Set | State |
|:---|:---|:---|
| The one fixed run | the documents of the sets validation and group 7 | measured one time against the export, with 2 readers (chapter 5) |
| Development values of round 4 and of the heads design | the development documents | design values with the mark "after the opening"; optimistic (chapters 5.5 and 3.5) |
| Block-role candidates B1-S and B1-L | 44 [`sets.reference.validation.documents`] validation documents with AI block labels | measured on 13.10.2026 before the run, against an AI reference; they did not enter the run (chapter 3.8) |
| Kind of the document | the documents of the run | not measured: no label of the kind was opened |
| Check by eye | 50 [`L.check_by_eye.documents`] documents of the run | information; 2 AI examiners (chapter 5.7) |
| Subsets and spread between parliaments | the documents of the run | information, made after the run (chapters 5.8 and 5.9) |
| Test set | 40 [`sets.test_set.selected`] selected documents; 26 [`sets.test_set.records`] records of them (protocol only). The author examined each record on the PDF. | not used in the one fixed run or in another value of this report; the earlier converter of 12.10.2026 was scored on the 26 records |
| An own PDF | a PDF with a text layer | the rules only, no Apertus value. Only with `make setup-pdf` and `make run-native`. Recorded: synthetic PDFs and the 3 sample PDFs (`app/README.md`, chapter "The modes"), and on 15.10.2026 2 changed copies of samples (chapter 7.1) |
| `make run` in a container | the app | one run on one Mac (chapter 7.1). The image converts the 3 samples only |

## 2. Architecture

![The pipeline from a PDF to a validated eCH-0295 record. The file type of each output is below its box.](fig1-pipeline.svg)

### 2.1 Input and output

Input: one PDF. Output: one eCH-0295 record in Turtle and YAML, a label file, `<doc>.values.ttl` and one validation result.

`<doc>.values.ttl` is RDF. It has one node for each value of the record. A node links the eCH-0295 resource and its property to the value. It also gives the printed wording, the probability, the value status, the rule tier, the page and the character span. The writer of the app makes this file (since 14.10.2026).

The label file gives, for each value, the probability, the value status, the page and the character span. It also keeps a value below the floor of 0.5, which the record does not get. A value with no printed wording has no page and no span. This is the case for an affair type from the `Q1` head (chapter 3.6).

### 2.2 The stages

The numbers are the boxes of figure 1.

1. **Text blocks.** Docling gives blocks with page, frame and text. For the stored Docling outputs, `ocrmac` read scanned pages (macOS only). `make setup-pdf` installs no OCR.
2. **Rule files.** The rule chain of the earlier converter (method `nos4`) gives the rule role of the document and the role of each block. It uses the rules S1, S2 and S5. In place of S3 it gives the answer "text", and it uses no S4. In the run, the rule files came from the PDF alone, with empty export fields.
3. **Cascade.** The kind of the document and the affair type select the slots that a document can state (chapter 2.3). A field outside these slots is not searched.
4. **Rule readers.** One reader for each group of fields gives a value, its tier, its page and its span (chapter 2.4).
5. **Calibration.** Each pair of field and tier gets a probability from the development documents (chapter 2.5).
6. **Apertus heads.** Two head tiers give a value where the rules find none, or where the rule value has a probability below 0.5 (chapter 3).
7. **Writer and validator.** The writer makes the record, the label file and `<doc>.values.ttl`. The validator checks the record, its labels and the values file.
8. **App.** A browser page shows the records. The result view (`/app/#/view/<record_id>`) shows the PDF page with a box on each value, the values with their probability and status, and the RDF. The app gives each head value from the rules only. For 3 [`pkg.samples.count`] samples (read) it gives block labels of B1-S from stored Apertus states. It does not apply the 2 Apertus value tiers of the run. An own PDF needs `make setup-pdf` and `make run-native`, and no GPU. `make run` converts the 3 samples only (chapter 7.1).

Why rules first: a rule value has a page, a span and a reason that a person can examine. A rule needs no GPU.

### 2.3 The cascade of eCH-0295

The cascade has 5 [`cascade.stages`] stages (read). The standard states conditions in some places, but not one decision for all slots. A first decision changes the selection of the later slots.

| Stage | Decision | What the decision selects |
|:---|:---|:---|
| 0 | the kind of the document | the process steps that the document can state |
| 1 | the affair type | the process steps that the type can have; values of stage 4 |
| 2 | the process steps of this path | the classes of the record |
| 3 | the slots of each step | required, optional or not applicable; the origin of each value |
| 4 | the values and the value lists | the options of each value question |

Counts of the cascade (all read from the machine form `src/m11_cascade.yaml`; a copy is in `../src/converter_gj/`):

1. Stage 0 has 7 [`cascade.kinds`] kinds. Stage 1 has 10 [`cascade.affair_types`] options: the list values and the option none. Stage 2 has 9 [`cascade.steps`] step types.
2. The cascade has 70 [`cascade.paths`] paths of kind and affair type.
3. The schema I95 that the writer uses has 35 [`cascade.i95.classes`] classes, 87 [`cascade.i95.slots`] slots and 20 [`cascade.i95.value_lists`] value lists.
4. The cascade has 53 [`cascade.rules`] rules: 24 [`cascade.rules.standard`] from a file of the standard, 7 [`cascade.rules.project_rule`] project rules and 22 [`cascade.rules.project_choice`] project choices.
5. 12 [`cascade.slots.register_only`] slots only a register can give. 6 [`cascade.slots.no_holder`] slots have no holder on a path.
6. The self-check of the cascade module has 32 [`cascade.self_check.checks`] checks, and 0 [`cascade.self_check.failed`] failed.

The standard does not name a kind of document. It describes an affair. Thus each rule of stage 0 is a project choice.

Table 2: the kinds of stage 0. The slots are slots of the 87 [`cascade.i95.slots`] slots of I95. Slot ids: `cascade.slots_by_kind.<kind>.low` and `.high` (read). Document ids: `D.kind.<kind>.documents`, the development documents of round 4 (mark "after the opening").

| Kind | Meaning | Rule role of the rule chain | Slots (lowest to highest over the affair types) | Documents, development |
|:---|:---|:---|:---|---:|
| `proposal` | a proposal of a member, a group or a committee, with the submitted text | `proposal` | 30 to 30 | 928 |
| `response` | a response or a statement of the executive on a proposal | `response` | 36 to 37 | 209 |
| `combined` | the proposal and the response in one PDF | `combined` | 36 to 37 | 315 |
| `executive_proposal` | a proposal of the executive: a message, a report with a request, a decree text | `proposal` (one rule id) | 27 to 27 | 47 |
| `committee_report` | a report or a request of a committee | `committee` | 23 to 35 | 75 |
| `minutes` | minutes or a decision text of the council | `minutes` | 61 to 61 | 13 |
| `other` | each other document: an attachment, a resolution of the government, a list | `other` | 18 to 18 | 206 |

The kind of the reader comes from the rule role of the rule chain. For a document with no decision of the rule chain, it comes from rule V5 (chapter 2.6).

What the standard does not state, and where the cascade has a project rule or a project choice:

1. the kind of a document;
2. the steps of the affair types with no profile;
3. which affair types have a recommendation of the executive;
4. which text types go with which step;
5. a map between the schema I95 and the kernel of the standard;
6. where a value comes from: the PDF or a register.

### 2.4 The rule readers

1. Rule readers read 7 head values. The reader of round 4 and of the run is the cascade reader of version `m11-values-cascade-4` [`D.reader_version`].
2. Each value comes from one rule tier, with its page and its character span. The development documents have 159 [`D.tiers`] rule tiers with a probability.
3. The primary set of a field is the set of documents that count for it. For the 2 response fields, only documents with the rule role `response` or `combined` count.
4. The rule files of round 4 and of the run come from the PDF alone. Their S1 rule got empty export fields.
5. On the development documents, the stored earlier rule files gave 213 [`D.kind.rules_compare.stored_rule_id_with_export_condition`] documents a rule id with a condition on export fields. The rule files from the PDF alone give that to 0 [`D.kind.export_condition`] documents.
6. The kind of 175 [`D.kind.rules_compare.kind_differs`] development documents differs between the 2 sets of rule files.

### 2.5 The calibration and the value status

1. The probability of a value is the Jeffreys mean of the precision of its tier on the development documents.
2. The folds keep the documents of one parliament together. A development document gets the value of the other folds.
3. A tier can give the status certain only with 30 [`design.fixed.addendum_g.certain_tier_units`] or more units on the development documents (read). Its precision there must be 0.95 [`design.fixed.addendum_g.certain_tier_precision`] or more (read).
4. A value gets the status certain if its probability is at or above the threshold a of its field. Else it gets the status unsure.
5. A tier is weak if its stored probability is below 0.5 [`design.fixed.combined_reader_weak_below`] (read).
6. The writer puts no value of a tier with a stored probability below 0.5 [`design.fixed.writer_floor`] (read) into a slot. Such a value goes into the label file only.

Table 3: the rule tiers and the calibration of round 4. Development documents, reader with rules only. Ids: `D.<field>.<key>`; the keys `tiers` and `certain_tiers` are derived. Mark "after the opening".

| Field | Documents of the primary set | With a reference | Correct / wrong / not found | Rule tiers | Tiers that can give certain | Threshold a | Mean probability | Brier score | Calibration error |
|:---|---:|---:|:---|---:|---:|:---|---:|---:|---:|
| `affair_type` | 1,793 | 1,657 | 1,369 / 60 / 228 | 15 | 6 | 0.60 | 0.9449 | 0.0423 | 0.0131 |
| `title` | 1,793 | 1,772 | 1,211 / 381 / 180 | 37 | 0 | no value | 0.7079 | 0.1756 | 0.1003 |
| `affair_number` | 1,793 | 1,636 | 586 / 186 / 864 | 41 | 2 | no value | 0.6568 | 0.2038 | 0.1676 |
| `submission_date` | 1,793 | 1,771 | 764 / 392 / 615 | 18 | 0 | no value | 0.6280 | 0.2636 | 0.1532 |
| `response_date` | 482 | 210 | 163 / 31 / 16 | 11 | 1 | no value | 0.6262 | 0.2849 | 0.3589 |
| `responder_name` | 482 | 401 | 380 / 7 / 14 | 11 | 2 | 0.60 | 0.9588 | 0.0227 | 0.0231 |
| `first_author` | 1,793 | 1,164 | 870 / 118 / 176 | 26 | 3 | no value | 0.8339 | 0.1203 | 0.0791 |

1. The threshold a exists for the affair type and the responder only. Thus the 5 other fields have no certain value, also where a tier can give the status certain.
2. No source that the author of this text read states the cause.

### 2.6 Rule V5: the kind of a document with no decision of the rule chain

1. With empty export fields, the rule chain makes no decision for some documents. Their rule role is `other` by default.
2. A kind by default must not stop the search of the submission step and of the response step.
3. Rule V5 of the reader gives a kind from 2 facts of the PDF: a type word of a proposal of a member, and an explicit response cue.
4. The 2 facts give the kind `combined`. The type word alone gives `proposal`. The response cue alone gives `response`, but only for the tier `rsp_response_cue`.
5. Each other case keeps the kind `other`. Rule V5 reads no export field.
6. Rule V5 does not change the rule role or the block roles. Thus it does not change the primary set of the 2 response fields.

On the development documents (round 4, mark "after the opening"): 280 [`D.kind.v5.rule_id_d0`] documents had no decision of the rule chain. Rule V5 changed the kind of 104 [`D.kind.v5.changed`] of them: 62 [`D.kind.v5.to_proposal`] to `proposal`, 41 [`D.kind.v5.to_combined`] to `combined` and 1 [`D.kind.v5.to_response`] to `response`. It changed nothing for 176 [`D.kind.v5.no_change`].

Table 4: rule V5 in the one fixed run, combined reader. Ids: `C.kind.<key>`, `CV.kind.<key>`, `CG.kind.<key>`; `v5.changed` is derived.

| Set | To `proposal` | To `combined` | To `response` | Changed | Kind `response` or `combined` outside the primary set | Kind changed by the `Q0` head |
|:---|---:|---:|---:|---:|---:|---:|
| all | 19 | 21 | 6 | 46 | 27 | 0 |
| validation | 19 | 17 | 6 | 42 | 23 | 0 |
| group 7 | 0 | 4 | 0 | 4 | 4 | 0 |

Limits of rule V5:

1. Rule V5 was written after the values of the new rule files were seen on the development documents. Its counts are design values.
2. The export has no reference of the kind. Thus the kind of rule V5 has no measured share of correct kinds.
3. The response cue can also be a heading of a report or a decree of the executive. Then the record states a response step that the PDF does not state.
4. A decree of the executive can name an earlier motion. With a signature or a minutes cue, it then gets the kind `combined`.
5. A type word in a document that only names a proposal gives the kind `proposal`. Then the text of a notice can go into the submitted text.
6. A skeptic agent read a sample of the documents with a kind of rule V5. The other documents were not read for this check.

## 3. Use of Apertus

### 3.1 Model and read-out

- `swiss-ai/Apertus-v1.5-8B` (form value `8B v1.5`), bf16, no quantization.
- Apertus generates no token. A linear head reads the hidden state at the last token of a question.
- A virtual machine with one H100 GPU made the states of the development documents and of the documents of the run. A Mac applied the heads to the stored states.
- The value questions use the unchanged model. Only the block-role candidate B1-L adds a LoRA adapter (chapter 3.8).

### 3.2 Prompt and questions

1. The value template is `gj_values_v1_de`. Its files are in [`../src/prompts/gj_values_v1_de/`](../src/prompts/gj_values_v1_de/).
2. The prompt is German. The prefix has a system text and the whole document, one line for each block: `[B<n> | S.<page> | <Docling label>] <block text>`.
3. The model reads the prefix one time. Each question then has its own suffix. After each suffix, the cache goes back to the prefix.
4. Thus each question sees the whole document and no other question.

| Question | Unit | What it asks |
|:---|:---|:---|
| `Q0` | document | the kind of the document |
| `Q1` | document | the affair type |
| `Q2.B<n>` | block | which values block n states: one of the value kinds, or none |

### 3.3 Targets and fit of the heads (addendum I)

The numbers of this chapter are fixed numbers of addendum I, table 1 (read). Addendum I fixed them before the first value of the new states.

1. Each head is a logistic regression with an L2 penalty on the state of layer 20 [`design.fixed.addendum_i.layer_of_each_head`]. No other layer was fitted.
2. The penalty grid is 0.001, 0.01, 0.1 [`design.fixed.addendum_i.penalty_grid`]. An inner fold selects the penalty. It uses the block labels only, not an outcome of a value.
3. The folds keep the documents of one parliament together. A development document is read with the head of the other folds (out-of-fold).
4. The final head is fitted on all development documents. It is the head of the run. The app of this repository has no file of the value heads (chapter 3.10).
5. `Q1`: one class for each affair type with 10 [`design.fixed.addendum_i.q1_lowest_documents_of_a_class`] or more development documents, and the class none. The target is the reference type of the export.
6. `Q2`: one head for each field but the affair type. Its 2 classes: the block prints the reference value of the field, or it does not.
7. A `Q2` label comes from the reference only, not from a rule value. Thus the head does not learn the errors of the rules.
8. A `Q2` fit has each positive block of a document. Negative blocks of one document: 30 at most [`design.fixed.addendum_i.negative_blocks_of_one_document`].
9. `Q0`: its classes come from the AI block labels of 193 [`H.entry.q0.labelled_documents`] development documents: A submitted text only, B response only, C both, D neither.

### 3.4 From the head to a value

1. For each `Q2` field the top block is the block with the highest head probability.
2. If that probability is below 0.50 [`design.fixed.addendum_i.lowest_block_probability`], the tier gives no value.
3. Else a span function reads the value in the top block only. The record has the page, the block and the span of the value.
4. The band of a value is `hi` if the head probability is 0.80 [`design.fixed.addendum_i.band_limit`] or more. Else it is `lo`.
5. `Q1` gives a type only if the probability of its top class is 0.80 [`design.fixed.addendum_i.lowest_class_probability_q1_q0`] or more. The class none gives no type.
6. The head probability is not the probability of the value. It selects the block and the band only.
7. The probability of a value of an Apertus tier is the Jeffreys mean of the precision of its tier on the development documents.

### 3.5 The entry decisions

The entry decisions were made one time, on development documents only, before the fix record of the run. Each value of this chapter is out-of-fold and has the marks "after the opening" and "after the design values of addendum I" [`H.mark`]. These values are optimistic.

Entry rules (addendum I, read):

1. A `Q2` tier enters if it has 20 [`design.fixed.addendum_i.lowest_units_of_a_tier`] or more units and a precision of 0.5 [`design.fixed.addendum_i.q2_lowest_precision`] or more.
2. If the bands `hi` and `lo` each have that number of units, each band is one tier. Else the 2 bands are one tier.
3. The `Q1` tier enters if it has the same lowest number of units and a precision of 0.80 [`design.fixed.addendum_i.q1_lowest_precision`] or more.
4. The `Q0` head enters with 3 conditions. Lowest accuracy and lowest number of documents: 0.90 and 50 [`design.fixed.addendum_i.q0_lowest_accuracy_and_documents`]. The head must also be correct as often as the rules.
5. A tier that does not meet its entry rule does not enter. No limit was changed to make a tier enter.

Table 5: the entry of the `Q0` head. Ids: `H.entry.q0.<key>`. Development documents with an AI label of the kind.

| Documents compared | Head correct | Rules correct | Condition a (documents) | Condition b (accuracy) | Condition c (head against rules) | Entered |
|---:|---:|---:|:---|:---|:---|:---|
| 140 | 106 | 106 | yes | no | yes | no |

Table 6: the entry of the `Q1` tier. Ids: `H.entry.q1.<key>`. The design set has the development documents where the rules found no affair type.

| Design set | Units equal | Units different | Types with no reference | Entered |
|---:|---:|---:|---:|:---|
| 332 | 93 | 7 | 28 | yes |

Information: 1,657 [`H.entry.q1.all.documents`] development documents have a reference type. For 1,439 [`H.entry.q1.all.correct`] of them the top class of the `Q1` head is the reference type (0.8684 [`H.entry.q1.all.accuracy`]). This value is not a value of the entry decision.

Table 7: the entry of the `Q2` tiers. Ids: `H.entry.q2.<field>.<key>` and `H.entry.q2.<field>.<tier>.<key>`. The design set has the development documents where the rules found no value or gave a value of a weak tier.

| Field | Design set: rules found no value | Design set: weak rule tier | Tier | Equal | Different | Entered |
|:---|---:|---:|:---|---:|---:|:---|
| `affair_number` | 950 | 157 | `apertus_q2_affair_number_hi` | 3 | 18 | no |
|  |  |  | `apertus_q2_affair_number_lo` | 9 | 58 | no |
| `title` | 184 | 154 | `apertus_q2_title_hi` | 15 | 35 | no |
|  |  |  | `apertus_q2_title_lo` | 16 | 63 | no |
| `submission_date` | 343 | 72 | `apertus_q2_submission_date_hi` | 7 | 18 | no |
|  |  |  | `apertus_q2_submission_date_lo` | 19 | 52 | no |
| `response_date` | 127 | 1 | `apertus_q2_response_date` | 0 | 6 | no |
| `responder_name` | 21 | 0 | `apertus_q2_responder` | 4 | 1 | no |
| `first_author` | 285 | 31 | `apertus_q2_sponsor_hi` | 15 | 9 | yes |
|  |  |  | `apertus_q2_sponsor_lo` | 8 | 13 | no |

1. Of `Q2`, only the tier `apertus_q2_sponsor_hi` of the first author entered.
2. For the affair number, the title and the submission date, the `Q2` tiers were wrong more often than correct on development documents.
3. For the response date and the responder, the tiers had fewer units than the entry rule asks for.

### 3.6 The combined reader

1. Stage 0: the `Q0` head did not enter. Thus the kind comes from the rules, rule V5 included.
2. Stage 1: the type reader of the rules runs first. If it finds no type, the `Q1` tier gives the type.
3. Where the rules give a type, a `Q1` class with a probability of 0.80 [`design.fixed.addendum_i.lowest_class_probability_q1_q0`] or more is a cross-check. A different class gives a mark in the record. The rule value stays.
4. Stage 3: for each field that the cascade searches, the rule reader runs first.
5. The Apertus tier of a field is called only if the rules found no value or gave a value of a weak tier.
6. A field that the cascade does not search gets no Apertus value.
7. A type from the `Q1` head has no printed wording. Its record has no page and no span. Its evidence says: answer of the model to question `Q1` on the whole document.

Table 8: the 2 readers on the development documents. Ids: `H.<field>.rules.<key>` and `H.<field>.combined.<key>`; `share_correct` is derived. Marks "after the opening" and "after the design values of addendum I". Reference: the export.

| Field | Reader | Correct / wrong / not found / no reference | Precision | Found rate | Share correct |
|:---|:---|:---|---:|---:|---:|
| `affair_type` | rules only | 1,369 / 60 / 228 / 136 | 0.9580 | 0.8624 | 0.8262 |
| `affair_type` | combined | 1,462 / 67 / 128 / 136 | 0.9562 | 0.9228 | 0.8823 |
| `first_author` | rules only | 870 / 118 / 176 / 629 | 0.8806 | 0.8488 | 0.7474 |
| `first_author` | combined | 880 / 125 / 159 / 629 | 0.8756 | 0.8634 | 0.7560 |

1. In the combined values file of the development documents, 128 [`H.types_from_q1`] affair types come from the tier `apertus_q1`.
2. For 12 [`H.marks_q1_differs`] documents the class of the `Q1` head differs from the type of the rules. The rule value stays.
3. 1 [`H.documents_with_no_states_file`] development document has no states file. It has no head value.
4. The 2 tiers that entered had these development values: `apertus_q1` 93 [`H.tier.apertus_q1.equal`] equal and 7 [`H.tier.apertus_q1.different`] different, precision 0.9300 [`H.tier.apertus_q1.precision`].
5. `apertus_q2_sponsor_hi`: 15 [`H.tier.apertus_q2_sponsor_hi.equal`] equal and 9 [`H.tier.apertus_q2_sponsor_hi.different`] different, precision 0.6250 [`H.tier.apertus_q2_sponsor_hi.precision`].
6. The share correct of the combined reader is also in the file of the combined measures: 0.8823 [`H.affair_type.combined.share_correct.dev_combined_file`] and 0.7560 [`H.first_author.combined.share_correct.dev_combined_file`]. The 2 values agree with the derived values of table 8.

### 3.7 The 2 Apertus tiers in the one fixed run

Table 9: the 2 tiers in the run. Ids: `C.tier.<tier>.<key>`, `CV.tier.<tier>.<key>`, `CG.tier.<tier>.<key>`. Reference: the export. The measures file has no interval for a tier.

| Tier | Set | Units | Correct | Precision | Stored probability |
|:---|:---|---:|---:|---:|---:|
| `apertus_q1` (affair type) | all | 59 | 55 | 0.9322 | 0.9257 |
| `apertus_q1` (affair type) | validation | 51 | 47 | 0.9216 | 0.9257 |
| `apertus_q1` (affair type) | group 7 | 8 | 8 | 1.0000 | 0.9257 |
| `apertus_q2_sponsor_hi` (first author) | all | 79 | 67 | 0.8481 | 0.6200 |
| `apertus_q2_sponsor_hi` (first author) | validation | 75 | 64 | 0.8533 | 0.6200 |
| `apertus_q2_sponsor_hi` (first author) | group 7 | 4 | 3 | 0.7500 | 0.6200 |

1. For 4 [`C.q1_differs`] documents of the run the `Q1` head and the rules give a different affair type. The reader keeps the rule value and marks the record.
2. Group 7 has few units in the 2 tiers. These counts are too small for a statement on group 7 alone.
3. The stored probability comes from the development documents. It includes the own fold of a development document. The development values of a tier that entered are optimistic.

The `Q0` head in the run (information). The head did not enter, so it changed the kind of 0 [`C.kind.changed`] documents. Its classes were recorded as a cross-check.

Table 10: the classes of the `Q0` head in the run. Ids: `L.heads.<set>.q0_class.<class>` and `L.heads.<set>.documents_with_no_states_file`. Information.

| Set | A | B | C | D | Not given | No head answer | No states file |
|:---|---:|---:|---:|---:|---:|---:|---:|
| all | 409 | 87 | 120 | 63 | 193 | 0 | 0 |
| validation | 389 | 74 | 109 | 60 | 172 | 0 | 0 |
| group 7 | 20 | 13 | 11 | 3 | 21 | 0 | 0 |

### 3.8 The block-role candidates B1-S and B1-L (not in the run; B1-S gives the block labels of the 3 samples in the app)

Apertus can also give each text block a role, for example submitted text, reasoning, response, recommendation, title or none. This was the result of text version 1 of this report. The readers of the one fixed run used the block roles of the rule chain, not the roles of B1-S or B1-L.

Set and reference: 44 [`sets.reference.validation.documents`] validation documents of 14 [`sets.parliaments.validation`] parliaments with AI block labels, 2,715 [`sets.reference.validation.blocks`] blocks. 2,325 [`rules.val.non_certain_blocks`] blocks are not decided by a certain rule. The reference is an AI reference: AI agents labelled each line to a fixed guide. No human label exists.

The 3 methods:

1. The first heads (B1 with B2): a frozen read-out head on Apertus states and a sequence step. The run of 04:17 on 13.10.2026 is run 1.
2. B1-S: the frozen B1 head and a new form of the sequence step, `switch_soft` with the strength 8.0 [`dev.b1s.strength`]. No Apertus weight changes. Run 2.
3. B1-L: a LoRA adapter on Apertus and a linear head, trained on the development documents. It is the LoRA-trained candidate. Run 3.

Table 11: the block-role candidates. Development: 7,801 [`rules.dev.non_certain_blocks`] blocks that no certain rule decides. Validation: the blocks above. Ids: `rules.dev.acc_noncertain`, `heads.dev.b12.acc_noncertain`, `dev.<b1s|b1l>.acc_noncertain`; `rules.val.<key>`, `heads.val.b12.<key>`, `val.<b1s|b1l>.<key>`. Exact block paths: of 44 [`sets.reference.validation.documents`] documents. Exact switch documents: of 10 [`sets.reference.validation.switch_documents`] switch documents. Reference: AI reference.

| Method | Development accuracy, out-of-fold | Validation accuracy | Gain over the rules (5 % bound) | Exact block paths | Exact switch documents | Enters |
|:---|---:|---:|:---|---:|---:|:---|
| Rules | 0.4198 | 0.4748 | no value | 27 | 4 | baseline |
| First heads | 0.7913 | 0.7419 | 0.2671 (0.1620) | 27 | 1 | no |
| B1-S | 0.7932 | 0.7372 | 0.2624 (0.1424) | 31 | 4 | yes |
| B1-L | 0.8441 | 0.7200 | 0.2452 (0.1283) | 30 | 4 | yes |

The development value of the rules is in-sample for the documents in the design set of the rules: 145 [`sets.rules_saw.dev`] documents (read). The rules saw 42 [`sets.rules_saw.validation`] of the validation documents with AI labels during their design (read). This favours the rules.

Entry rule of a candidate, fixed before run 1: the 5 % bound of the gain is above 0. Also, the exact block paths and the exact switch documents are not lower than those of the rules by more than 1.

The account of the 2 candidates:

1. B1-S: a frozen read-out head on Apertus states and a sequence step. No Apertus weight changes.
2. B1-L: a LoRA adapter (39,845,888 [`b1l.train.lora_values`] trained values, protocol only) and a linear head (24,582 [`b1l.train.head_values`] trained values, protocol only). It was trained on 193 [`b1l.train.documents`] development documents with 9,313 [`b1l.train.labels`] block labels (read).
3. Development, out-of-fold: B1-L 0.8441 [`dev.b1l.acc_noncertain`], B1-S 0.7932 [`dev.b1s.acc_noncertain`].
4. Validation: B1-L 0.7200 [`val.b1l.acc_noncertain`], B1-S 0.7372 [`val.b1s.acc_noncertain`]. The paired difference is -0.0172 [`val.pair.difference`], and its interval contains 0 [`val.pair.interval_holds_0`].
5. Calibration: table 12. The certain labels of B1-L have a lower accuracy on validation (0.8489 [`val.b1l.by_p.a0.85.accuracy`] against 0.9324 [`val.b1s.by_p.a0.8.accuracy`]).
6. The choice rule E3 of addendum E uses the development value. It gives B1-L [`dev.b1l.choice.result`].
7. The cause of the larger difference of B1-L between development and validation is not known.
8. The app, the conversion of the development documents and the cross-parliament analysis use B1-S.

Table 12: calibration of the written block labels on validation (criterion GJ.13). Ids: `val.gj13.<variant>.<key>`, `dev.<b1s|b1l>.threshold_a`, `val.status.<variant>.block_certain`, `val.<b1s|b1l>.certain.decided.<key>`. Limits of GJ.13: ECE 0.05 [`val.gj13.limit_ece`] and 95 % bound 0.08 [`val.gj13.limit_ece_high95`] (read). Reference: AI reference.

| Variant | Written accuracy | ECE | 95 % bound of the ECE | GJ.13 | Threshold a | Labels certain | Of these, decided by the candidate: labels, accuracy |
|:---|---:|---:|---:|:---|:---|---:|:---|
| Rules (`d1n_b12n`) | 0.5517 | 0.0240 | 0.0841 | NOT MET | none | none | no value |
| B1-S | 0.7750 | 0.0442 | 0.1158 | NOT MET | 0.80 | 1,168 | 778, 0.8985 |
| B1-L | 0.7602 | 0.0637 | 0.1412 | NOT MET | 0.85 | 1,456 | 1,066, 0.7936 |

1. The threshold of B1-L comes from addendum F. Addendum F was written after the development values of B1-L were known and before a validation value of B1-L was known.
2. On development documents the certain labels of the candidate alone had 0.9379 [`dev.b1s.certain_decided.accuracy`] (B1-S, protocol only) and 0.9376 [`dev.b1l.certain_decided.accuracy`] (B1-L, read). Thus this report does not say that a certain block label has the accuracy of the limit.

Table 13: the paired difference B1-L minus B1-S on the validation blocks that no certain rule decides. Ids: `val.pair.<key>`.

| Item | Value |
|:---|:---|
| Difference (5 % bound to 95 % bound) | -0.0172 (-0.0585 to 0.0229) |
| Blocks where only B1-L is correct | 130 |
| Blocks where only B1-S is correct | 170 |
| Blocks where the 2 are correct | 1,544 |
| Blocks where no candidate is correct | 481 |
| Blocks with the same written option | 1,735 |
| Difference on all validation blocks | -0.0147 (-0.0500 to 0.0195) |

Validity of the records of the 3 runs: 44 [`val.gj12.b1s.documents_valid`] of 44 [`val.gj12.b1s.documents`] records were valid in each run. The conformance was `i95` for 40 [`val.gj12.b1s.conformance_i95`] records and `i95_with_recorded_gaps` for 4 [`val.gj12.b1s.conformance_with_gaps`]. SHACL was skipped for 44 [`val.gj12.b1s.shacl_skipped`] records.

Limits of the candidates:

1. Each accuracy and each probability of this chapter refers to an AI reference, not to human labels.
2. The 3 methods ran on the same validation documents, as run 1, run 2 and run 3. B1-S was designed after the aggregate result of run 1 was known.
3. Thus the validation values of B1-S and B1-L are information, not values of one planned run.
4. The calibration target GJ.13 is NOT MET for each of the 3 variants.
5. The LoRA adapter is not published. It did not enter the one fixed run.

### 3.9 Models other than Apertus

| Model | Open weights | Role |
|:---|:---|:---|
| Docling layout and table models | yes | PDF to blocks. |
| Apple Vision OCR (`ocrmac`) | no | Text of scanned pages. It runs only on macOS. |
| Claude Opus 5.5 (AI agents) | no | Code, rules, the AI reference of the block roles, measurement scripts, audits, the check by eye, this text. |

### 3.10 Limits of the use of Apertus

1. Apertus values exist only for documents with stored states. The app gives each value from the rules, also for the 3 samples.
2. The app of this repository uses Apertus states for the block labels of its 3 samples. It has no file of the value heads `Q0`, `Q1` and `Q2`. Its values come from the rule readers.
3. The variables `LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY` are not read: the method needs hidden states.
4. The repository has no Apertus weights. The LoRA adapter is not published.
5. A type from `Q1` has no page and no span.

## 4. Data

### 4.1 Source, schema and personal data

- **Source:** the OpenParlData exports of 04.10.2026 and the PDF copies on <https://files.openparldata.ch>. Licence of the data: CC BY 4.0, "Source: OpenParlData.ch".
- **Schema:** eCH-0295, working draft at commit `3cab44d` of <https://github.com/swiss/political-affairs-ech-group> (version I95). It is not a released standard.
- **Personal data:** two AI agents examined each sample and found only persons with a public role. The repository has the PDF of the 3 samples only, and no text of a validation, group-7 or test document. The samples of the app are development documents.

### 4.2 Sets

Table 14: sets.

| Set | Documents | Parliaments | Use in this report |
|:---|---:|---:|:---|
| development | 1,793 [`D.documents`] | 44 [`D.parliaments`] | design of the value rules, fit of the heads, calibration, round 4 |
| of these, with AI block labels | 193 [`sets.reference.dev.documents`] | 42 [`sets.parliaments.dev`] | design of the block-role candidates, fit of the `Q0` head |
| validation | 804 [`L.documents.validation`] | 18 [`L.parliaments.validation`] | the one fixed run |
| of these, with AI block labels | 44 [`sets.reference.validation.documents`] | 14 [`sets.parliaments.validation`] | the runs of the block-role candidates |
| group 7 | 68 [`L.documents.group7`] | 8 [`L.parliaments.group7`] | the one fixed run |
| of these, with AI block labels | 57 [`sets.reference.group7.documents`] | | no run of a block-role candidate |
| test set | 40 [`sets.test_set.selected`] selected | 13 [`sets.test_set.parliaments`] | not used in this report (protocol only) |
| all Docling documents outside the test set | 2,665 [`sets.docling.all`] | | the sum of development, validation and group 7 |

1. The table has 2 different counts of parliaments for the validation side. 18 [`L.parliaments.validation`] is the count of the run. 14 [`sets.parliaments.validation`] counts the validation documents with AI block labels only.
2. In the same way, 42 [`sets.parliaments.dev`] counts the development documents with AI block labels, and 44 [`D.parliaments`] all development documents of round 4.
3. The split is by parliament. No parliament of the run is a development parliament.
4. The test set was not used in the one fixed run or in another value of this report. The public text of 12.10.2026 gave scores of an earlier converter on the 26 [`sets.test_set.records`] reviewed records.
5. The development documents had an open part and a closed part. The closed part was opened one time, on 13.10.2026 at 14:35 [`values.opening.time`].
6. After the opening, rules changed with knowledge of all development parliaments. Thus each value of round 4 has the mark "after the opening" [`D.mark`].

Languages of the 2,665 documents: German 1,699 [`sets.language.all.de`], French 676 [`sets.language.all.fr`], Italian 268 [`sets.language.all.it`], English 1 [`sets.language.all.en`], none 21 [`sets.language.all.none`]. The languages of the documents of the run by set have no entry in `numbers.json`.

### 4.3 The reference

1. The reference of a field is the export value after the normalisation of addendum G.
2. For the affair type it is the eCH type that a project map gives for the local type name of the export. The same value is the fit target of the `Q1` head.
3. The reference is a register. The outcome wrong can include a value that is correct in the PDF.
4. For 276 [`gaps.affair_type.all`] documents the export has no affair type of the I95 list (protocol only): development 136 [`gaps.affair_type.dev`], validation 127 [`gaps.affair_type.validation`], group 7 13 [`gaps.affair_type.group7`].
5. The challenge asks for an evaluation against a hand-checked gold set. The one fixed run has none. Its reference is the export.

## 5. Evaluation: the one fixed run

### 5.1 What ran

1. On 13.10.2026 at 21:30, 2 readers gave values for the documents of the run: the reader with rules only and the combined reader.
2. A tool compared each value with the export, one time. The rules, thresholds, heads and entry decisions were fixed before the run. No change after the run is known.
3. Before the run, tools converted each document, built its rule files and made its model states. "One run" means: the reader values were compared with the export one time.
4. The readers got the block files and the rule files of a sealed build. That build made the rule files from the PDF alone, with empty export fields.
5. An AI agent read in the code that the readers open no export file. Nobody measured this at run time.
6. The `Q0` head changed the kind of 0 [`C.kind.changed`] documents. Rule V5 changed the kind of 46 [`C.kind.v5.changed`] documents (table 4).

Measures:

1. A value is correct if it is equal to the export value after the normalisation of addendum G. Else it is wrong. This compares with the export only.
2. Precision is correct / (correct + wrong). Found rate is (correct + wrong) / documents with a reference.
3. Share correct is correct / documents with a reference: the product of precision and found rate. It was not a planned measure of addendum I.
4. The measure counts each value of a reader, also a value below the floor of 0.5 that the writer does not put into the record.
5. Each interval is a 90 % interval of a bootstrap by parliament: the 5 % bound and the 95 % bound. The sets have 26 [`L.parliaments.all`], 18 [`L.parliaments.validation`] and 8 [`L.parliaments.group7`] parliaments.
6. The measures file also has Jeffreys intervals for each cell, for example 0.9262 [`R.affair_type.precision.jeffreys_low5`] to 0.9569 [`R.affair_type.precision.jeffreys_high95`]. They do not include the spread between parliaments.
7. The 2 response fields count only documents with the rule role `response` or `combined`: 224 [`R.response_date.primary_set`] documents (198 [`RV.response_date.primary_set`] validation, 26 [`RG.response_date.primary_set`] group 7).

### 5.2 The reader with rules only

Table 15: reader with rules only, all documents of the run. Ids: `R.<field>.<key>` with the keys `correct`, `wrong`, `not_found`, `no_reference`, `precision`, `found_rate`, `share_correct` (derived) and `<measure>.bootstrap_low5`, `<measure>.bootstrap_high95`. Reference: the export.

| Field | Correct / wrong / not found / no reference | Precision (interval) | Found rate (interval) | Share correct (interval) |
|:---|:---|:---|:---|:---|
| `affair_type` | 580 / 35 / 117 / 140 | 0.9431 (0.9139 to 0.9660) | 0.8402 (0.7809 to 0.8943) | 0.7923 (0.7213 to 0.8581) |
| `title` | 406 / 378 / 82 / 6 | 0.5179 (0.4272 to 0.5972) | 0.9053 (0.8670 to 0.9407) | 0.4688 (0.3772 to 0.5573) |
| `affair_number` | 182 / 163 / 477 / 50 | 0.5275 (0.3493 to 0.6890) | 0.4197 (0.3135 to 0.5389) | 0.2214 (0.1358 to 0.3207) |
| `submission_date` | 238 / 212 / 422 / 0 | 0.5289 (0.4003 to 0.6855) | 0.5161 (0.4194 to 0.6308) | 0.2729 (0.2027 to 0.3603) |
| `response_date` | 22 / 21 / 63 / 118 | 0.5116 (0.3673 to 0.7143) | 0.4057 (0.2598 to 0.6111) | 0.2075 (0.1119 to 0.3636) |
| `responder_name` | 200 / 5 / 19 / 0 | 0.9756 (0.9272 to 1.0000) | 0.9152 (0.8333 to 0.9721) | 0.8929 (0.7974 to 0.9610) |
| `first_author` | 195 / 45 / 188 / 444 | 0.8125 (0.7454 to 0.8879) | 0.5607 (0.4555 to 0.6713) | 0.4556 (0.3690 to 0.5611) |

Table 16: reader with rules only, validation documents. Ids: `RV.<field>.<key>`, the keys of table 15.

| Field | Correct / wrong / not found / no reference | Precision (interval) | Found rate (interval) | Share correct (interval) |
|:---|:---|:---|:---|:---|
| `affair_type` | 549 / 29 / 99 / 127 | 0.9498 (0.9244 to 0.9709) | 0.8538 (0.7933 to 0.9138) | 0.8109 (0.7379 to 0.8824) |
| `title` | 375 / 355 / 71 / 3 | 0.5137 (0.4205 to 0.5997) | 0.9114 (0.8707 to 0.9490) | 0.4682 (0.3709 to 0.5619) |
| `affair_number` | 162 / 148 / 444 / 50 | 0.5226 (0.3174 to 0.7104) | 0.4111 (0.3022 to 0.5394) | 0.2149 (0.1203 to 0.3170) |
| `submission_date` | 212 / 208 / 384 / 0 | 0.5048 (0.3700 to 0.6544) | 0.5224 (0.4172 to 0.6422) | 0.2637 (0.1892 to 0.3536) |
| `response_date` | 14 / 19 / 60 / 105 | 0.4242 (0.2830 to 0.6400) | 0.3548 (0.2000 to 0.5702) | 0.1505 (0.0714 to 0.2969) |
| `responder_name` | 180 / 0 / 18 / 0 | 1.0000 (1.0000 to 1.0000) | 0.9091 (0.8216 to 0.9722) | 0.9091 (0.8216 to 0.9722) |
| `first_author` | 166 / 38 / 167 / 433 | 0.8137 (0.7432 to 0.8983) | 0.5499 (0.4342 to 0.6834) | 0.4474 (0.3529 to 0.5740) |

Table 17: reader with rules only, group 7. Ids: `RG.<field>.<key>`, the keys of table 15.

| Field | Correct / wrong / not found / no reference | Precision (interval) | Found rate (interval) | Share correct (interval) |
|:---|:---|:---|:---|:---|
| `affair_type` | 31 / 6 / 18 / 13 | 0.8378 (0.6429 to 1.0000) | 0.6727 (0.5000 to 0.8421) | 0.5636 (0.3616 to 0.7500) |
| `title` | 31 / 23 / 11 / 3 | 0.5741 (0.4000 to 0.7500) | 0.8308 (0.6818 to 0.9531) | 0.4769 (0.3284 to 0.6291) |
| `affair_number` | 20 / 15 / 33 / 0 | 0.5714 (0.1997 to 0.8810) | 0.5147 (0.3188 to 0.7164) | 0.2941 (0.0735 to 0.5362) |
| `submission_date` | 26 / 4 / 38 / 0 | 0.8667 (0.7000 to 0.9535) | 0.4412 (0.2899 to 0.6057) | 0.3824 (0.2090 to 0.5672) |
| `response_date` | 8 / 2 / 3 / 13 | 0.8000 (0.5000 to 1.0000) | 0.7692 (0.5455 to 1.0000) | 0.6154 (0.2857 to 0.9000) |
| `responder_name` | 20 / 5 / 1 / 0 | 0.8000 (0.5000 to 1.0000) | 0.9615 (0.9048 to 1.0000) | 0.7692 (0.4848 to 1.0000) |
| `first_author` | 29 / 7 / 21 / 11 | 0.8056 (0.5640 to 0.9556) | 0.6316 (0.4463 to 0.8000) | 0.5088 (0.2856 to 0.72735) |

1. Group 7 has 68 [`L.documents.group7`] documents of 8 [`L.parliaments.group7`] parliaments. Its intervals are wide.
2. For the responder of the validation set, the interval of the precision is 1.0000 to 1.0000: no validation parliament has a wrong value.
3. In group 7 the responder has 5 [`RG.responder_name.wrong`] wrong values of 25 [`RG.responder_name.given`]. The dossier gives that the 5 are of 1 parliament.
4. The 95 % bound of the share correct of the first author in group 7 is 0.72735 [`RG.first_author.share_correct.bootstrap_high95`]. The stored value is at the half step of 4 decimals, so the display keeps each decimal.

### 5.3 The combined reader

The combined reader has the counts of the reader with rules only for 5 fields. No Apertus tier entered for them.

Table 18: combined reader, the 2 fields with an Apertus tier. Ids: `C.<field>.<key>`, `CV.<field>.<key>`, `CG.<field>.<key>`, the keys of table 15. Reference: the export.

| Field | Set | Correct / wrong / not found / no reference | Precision (interval) | Found rate (interval) | Share correct (interval) |
|:---|:---|:---|:---|:---|:---|
| `affair_type` | all | 635 / 39 / 58 / 140 | 0.9421 (0.9168 to 0.9642) | 0.9208 (0.8952 to 0.9447) | 0.8675 (0.8249 to 0.9039) |
| `affair_type` | validation | 596 / 33 / 48 / 127 | 0.9475 (0.9247 to 0.9687) | 0.9291 (0.9063 to 0.9527) | 0.8804 (0.8433 to 0.9182) |
| `affair_type` | group 7 | 39 / 6 / 10 / 13 | 0.8667 (0.6842 to 1.0000) | 0.8182 (0.6557 to 0.9474) | 0.7091 (0.4815 to 0.8966) |
| `first_author` | all | 258 / 55 / 115 / 444 | 0.8243 (0.7597 to 0.8885) | 0.7313 (0.6635 to 0.8072) | 0.6028 (0.5195 to 0.6984) |
| `first_author` | validation | 226 / 47 / 98 / 433 | 0.8278 (0.7589 to 0.8990) | 0.7358 (0.6610 to 0.8269) | 0.6092 (0.5201 to 0.7179) |
| `first_author` | group 7 | 32 / 8 / 17 / 11 | 0.8000 (0.5588 to 0.9556) | 0.7018 (0.5246 to 0.8730) | 0.5614 (0.3197 to 0.8033) |

The 2 tiers raise the found rate of the affair type from 0.8402 [`R.affair_type.found_rate`] to 0.9208 [`C.affair_type.found_rate`]. For the first author it goes from 0.5607 [`R.first_author.found_rate`] to 0.7313 [`C.first_author.found_rate`]. The precision changes from 0.9431 [`R.affair_type.precision`] to 0.9421 [`C.affair_type.precision`] and from 0.8125 [`R.first_author.precision`] to 0.8243 [`C.first_author.precision`].

### 5.4 Values with the status certain

Table 19: values with the status certain, reader with rules only. Ids: `R.<field>.certain.<key>`, `RV.<field>.certain.<key>`, `RG.<field>.certain.<key>`. Reference: the export. The measures file has no interval for these values.

| Field | Set | Given values | Certain values | Certain with a reference | Certain and correct | Precision of the certain values |
|:---|:---|---:|---:|---:|---:|---:|
| `affair_type` | all | 676 | 460 | 446 | 426 | 0.9552 |
| `affair_type` | validation | 636 | 426 | 415 | 397 | 0.9566 |
| `affair_type` | group 7 | 40 | 34 | 31 | 29 | 0.9355 |
| `responder_name` | all | 205 | 175 | 175 | 170 | 0.9714 |
| `responder_name` | validation | 180 | 154 | 154 | 154 | 1.0000 |
| `responder_name` | group 7 | 25 | 21 | 21 | 16 | 0.7619 |

1. The 5 other fields have 0 certain values in each set, for example 0 [`R.title.certain.values`].
2. The combined reader has the same certain values. For the affair type it has 744 [`C.affair_type.certain.given_values`] given values.
3. The limit of a certain tier on the development documents is a precision of 0.95 [`design.fixed.addendum_g.certain_tier_precision`].
4. On the development documents (round 4) the affair type had 1,186 [`D.affair_type.certain.values`] certain values with a precision of 0.9699 [`D.affair_type.certain.precision`]. The responder had 333 [`D.responder_name.certain.values`] with 0.9932 [`D.responder_name.certain.precision`].
5. In group 7 the certain values of the responder have a precision of 0.7619 [`RG.responder_name.certain.precision`]: 16 [`RG.responder_name.certain.correct`] of 21 [`RG.responder_name.certain.with_reference`] are correct against the export.

### 5.5 The development values of round 4 beside the run

The development values are design values with the mark "after the opening" [`D.mark`]. The authors of the value rules read all 44 [`D.parliaments`] development parliaments. The run values are those of tables 15 and 18.

Table 20: development against run. Ids: development `D.<field>.precision`, `D.<field>.found_rate`, `D.<field>.recall` (share correct); combined reader `H.<field>.combined.<key>`. Run: `R.<field>.<key>` and `C.<field>.<key>`. Reference: the export.

| Field | Precision: development | Precision: run | Found rate: development | Found rate: run | Share correct: development | Share correct: run |
|:---|---:|---:|---:|---:|---:|---:|
| `affair_type` | 0.9580 | 0.9431 | 0.8624 | 0.8402 | 0.8262 | 0.7923 |
| `title` | 0.7607 | 0.5179 | 0.8984 | 0.9053 | 0.6834 | 0.4688 |
| `affair_number` | 0.7591 | 0.5275 | 0.4719 | 0.4197 | 0.3582 | 0.2214 |
| `submission_date` | 0.6609 | 0.5289 | 0.6527 | 0.5161 | 0.4314 | 0.2729 |
| `response_date` | 0.8402 | 0.5116 | 0.9238 | 0.4057 | 0.7762 | 0.2075 |
| `responder_name` | 0.9819 | 0.9756 | 0.9651 | 0.9152 | 0.9476 | 0.8929 |
| `first_author` | 0.8806 | 0.8125 | 0.8488 | 0.5607 | 0.7474 | 0.4556 |
| `affair_type`, combined reader | 0.9562 | 0.9421 | 0.9228 | 0.9208 | 0.8823 | 0.8675 |
| `first_author`, combined reader | 0.8756 | 0.8243 | 0.8634 | 0.7313 | 0.7560 | 0.6028 |

1. For the title, the affair number and the 2 dates, the precision of the run is lower than on the development documents.
2. The found rate also drops for 2 fields: the response date from 0.9238 [`D.response_date.found_rate`] to 0.4057 [`R.response_date.found_rate`], and the first author from 0.8488 [`D.first_author.found_rate`] to 0.5607 [`R.first_author.found_rate`].
3. For the first author, fewer than half of the documents with a reference get the export value: 195 [`R.first_author.correct`] of 428 [`R.first_author.with_reference`].

### 5.6 What the result means, in plain words

Reader with rules only, all documents of the run. Ids: `R.<field>.precision` and `R.<field>.share_correct` (table 15). "Given values" are given values with a reference.

1. Affair type: 0.9431 of the given values are the export value. The reader gives the export value for 0.7923 of the documents with a reference.
2. Responder: 0.9756 of the given values; 0.8929 of the documents with a reference. In group 7 the precision is 0.8000 [`RG.responder_name.precision`].
3. First author: 0.8125 of the given values; 0.4556 of the documents with a reference.
4. Title: 0.5179 of the given values; 0.4688 of the documents with a reference.
5. Affair number: 0.5275 of the given values; 0.2214 of the documents with a reference.
6. Submission date: 0.5289 of the given values; 0.2729 of the documents with a reference.
7. Response date: 0.5116 of the given values, from 43 [`R.response_date.given`] values; 0.2075 of the documents with a reference.

Thus for the affair number and the 2 dates, about 1 of 4 or 5 documents with a reference gets the export value. For the title and the first author, fewer than 1 of 2 such documents get the export value.

The 2 Apertus tiers add found values at about the same precision. The share correct goes from 0.7923 to 0.8675 and from 0.4556 to 0.6028 (table 20).

### 5.7 The check by eye (information)

1. The sample has 50 [`L.check_by_eye.documents`] documents of the run (protocol only). A tool drew them with a fixed seed from the sorted ids.
2. 2 AI examiners each read the same sheets. A sheet has the lines of the document and the values of the combined reader, and no export value. The content of the sheets was not examined for this rule.
3. An examiner read the first lines, the last lines and the lines near each value, not the full document.
4. The check is information. It changes no outcome. The 2 examiners are AI agents of one model with one order.

Codes of a judgement: C correct as printed; P partly correct; W wrong; M not found, but the lines read print the value; N not found and not printed in the lines read; X the field does not apply to this kind of document. "Given" is C + P + W.

Table 21: the check by eye by field. Ids: `L.check_by_eye.<a|b>.<field>.<code>`, `.given` (derived) and `L.check_by_eye.pairs_that_differ.<field>`. Mark: reading check.

| Field | Given values (A, B) | C (A, B) | P (A, B) | W (A, B) | M (A, B) | N (A, B) | X (A, B) | Pairs that differ |
|:---|:---|:---|:---|:---|:---|:---|:---|---:|
| `affair_type` | 40, 40 | 31, 33 | 4, 4 | 5, 3 | 8, 8 | 2, 2 | 0, 0 | 4 |
| `title` | 45, 45 | 20, 20 | 9, 10 | 16, 15 | 3, 3 | 2, 2 | 0, 0 | 1 |
| `affair_number` | 15, 15 | 12, 12 | 0, 0 | 3, 3 | 14, 14 | 21, 21 | 0, 0 | 0 |
| `submission_date` | 21, 21 | 18, 18 | 0, 0 | 3, 3 | 15, 15 | 10, 10 | 4, 4 | 0 |
| `response_date` | 7, 7 | 3, 3 | 0, 0 | 4, 4 | 7, 8 | 9, 7 | 27, 28 | 2 |
| `responder_name` | 17, 17 | 17, 17 | 0, 0 | 0, 0 | 3, 4 | 3, 1 | 27, 28 | 3 |
| `first_author` | 31, 31 | 25, 25 | 2, 2 | 4, 4 | 13, 10 | 2, 2 | 4, 7 | 3 |

The check by eye has 350 [`L.check_by_eye.pairs`] pairs of document and field. The 2 examiners differ in 13 [`L.check_by_eye.pairs_that_differ`] of them.

Table 22: the check by eye beside the precision against the export. The 2 numbers are different measures on different samples. This comparison was not planned before the run. Ids: as table 21; `C.<field>.precision`.

| Field | Correct as printed / given: examiner A | Correct as printed / given: examiner B | Precision against the export, combined reader, all documents of the run |
|:---|:---|:---|---:|
| `affair_type` | 31 of 40 | 33 of 40 | 0.9421 |
| `title` | 20 of 45 | 20 of 45 | 0.5179 |
| `affair_number` | 12 of 15 | 12 of 15 | 0.5275 |
| `submission_date` | 18 of 21 | 18 of 21 | 0.5289 |
| `response_date` | 3 of 7 | 3 of 7 | 0.5116 |
| `responder_name` | 17 of 17 | 17 of 17 | 0.9756 |
| `first_author` | 25 of 31 | 25 of 31 | 0.8243 |

1. For the affair type, the AI examiners found fewer values correct as printed than the precision against the export gives. The cause is not examined. The reference of this field is a derived value (chapter 4.3).
2. For the affair number and the submission date, the examiners found more values correct as printed than the precision against the export gives.
3. The criteria name cases where the export has another form or another day than the PDF. The run has no count of such cases. Thus the share of wrong values that are correct in the PDF is not known.
4. For the response date the sample has few given values.
5. Each examiner named 12 [`L.check_by_eye.kind_looks_wrong`] of the 50 documents with a kind that looks wrong (protocol only): 6 [`L.check_by_eye.kind_looks_wrong.committee_report`] with the kind `committee_report` and 6 [`L.check_by_eye.kind_looks_wrong.proposal`] with the kind `proposal`.
6. The work log says that the 2 examiners name the same documents. The dossier did not compare the 2 lists.
7. For a document with a wrong kind, the cascade does not search some fields. The run did not measure the kind: no label of the kind was opened.

### 5.8 Information measures on subsets (after the run)

A tool made these numbers after the run, and after the result was known, from the values files and the reference file of the run. No document was read again. They are not measures of addendum I, and they decide nothing.

The subsets come from the contact history of the documents (chapter 9.3). Ids: `L.contact.<subset>.<set>`; the values of the set all are derived (line counts).

| Subset | Rule | All | Validation | Group 7 |
|:---|:---|---:|---:|---:|
| S1 | the document has no AI block label | 771 | 760 | 11 |
| S2 | the id is in no id list of earlier work | 615 | 615 | 0 |
| S3 | the audit of the transcripts found no text and no values of the document | 572 | 572 | 0 |
| S4 | the documents that are not in S3: a sign of earlier contact | 300 | 232 | 68 |

1. S1 does not mean no AI contact. S2 does not mean no contact with an AI agent. S3 is no proof of no contact.
2. On S2 and on S3, the precision of the title and of the submission date is lower than on the other documents. This is also true in the validation set alone.
3. On S2 and on S3, the precision of the first author is higher than on the other documents.
4. On S2 and on S3, the found rate of the response date is lower than on the other validation documents. The counts are small.
5. No cause of a difference is shown. The subsets have other shares of the parliaments than the other documents. No significance calculation was made.
6. The precision values of the subsets have no entry in `numbers.json`. They are in the dossier, chapter 5.8.

### 5.9 The spread between the parliaments (information, after the run)

A parliament counts for a field with 5 or more given values with a reference. The same tool as in chapter 5.8 made these numbers after the run.

Table 23: spread between the parliaments, all documents of the run. Ids: `L.spread.<rules_only|combined>.<field>.<key>`. Information.

| Field | Reader | Parliaments that count | Given values that count | Lowest | Median | Highest | Parliaments at 1.0000 | Parliaments below 0.9 | Pooled precision |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| `affair_type` | rules only | 21 | 605 | 0.4286 | 0.9841 | 1.0000 | 10 | 4 | 0.9431 |
| `affair_type` | combined | 22 | 667 | 0.4286 | 0.9853 | 1.0000 | 11 | 4 | 0.9421 |
| `title` | rules only | 25 | 781 | 0.0328 | 0.5714 | 1.0000 | 1 | 24 | 0.5179 |
| `affair_number` | rules only | 18 | 337 | 0.0000 | 0.5228 | 1.0000 | 4 | 14 | 0.5275 |
| `submission_date` | rules only | 21 | 440 | 0.0000 | 0.8000 | 1.0000 | 3 | 16 | 0.5289 |
| `response_date` | rules only | 2 | 18 | 0.2500 | 0.2750 | 0.3000 | 0 | 2 | 0.5116 |
| `responder_name` | rules only | 15 | 173 | 0.0000 | 1.0000 | 1.0000 | 14 | 1 | 0.9756 |
| `first_author` | rules only | 17 | 218 | 0.2000 | 0.9091 | 1.0000 | 7 | 7 | 0.8125 |
| `first_author` | combined | 19 | 297 | 0.2857 | 0.9091 | 1.0000 | 8 | 7 | 0.8243 |

1. The spread is large for the title, the affair number and the 2 dates. A pooled value does not describe one parliament.
2. For the responder, 14 [`L.spread.rules_only.responder_name.parliaments_with_a_precision_of_1`] of the 15 [`L.spread.rules_only.responder_name.parliaments_that_count`] parliaments that count have the precision 1.0000.
3. For the response date, only 2 [`L.spread.rules_only.response_date.parliaments_that_count`] parliaments count.
4. For the 5 fields with no Apertus tier, the combined reader has the values of the reader with rules only.

### 5.10 Second and third calculations

1. A second tool, written by a different AI agent from the text of addendum I, made the measures of the run again. The 2 files agree with no different value.
2. A third calculation in the check tool of the evidence made the counts again for the 2 readers, the 3 sets and the 7 fields. No number differs.
3. The 3 calculations use the same 3 files. An error that is common to the reader output or to the reference file is in each of them.
4. Thus the agreement does not show that a value is true.
5. AI agents wrote each of the 3 calculations.
6. Round 4 also has a second calculation: 363 [`D.second.cells_compared`] cells compared, 0 [`D.second.differences`] different.

## 6. Limitations

### 6.1 The 12 limit sentences

| No. | Limit | Number ids |
|:---|:---|:---|
| L1 | Fewer than half of the documents with a reference get the export value. This applies to the affair number, the 2 dates, the title and the first author. Affair number: 182 of 822 documents with a reference (0.2214). Submission date: 238 of 872 (0.2729). Response date: 22 of 106 (0.2075). Title: 406 of 866 (0.4688). First author: 195 of 428 (0.4556). | `R.<field>.correct`, `R.<field>.with_reference`, `R.<field>.share_correct` (table 15), for example 0.4556 [`R.first_author.share_correct`] |
| L2 | The authors of the value rules of 13.10.2026 read the 44 development parliaments; the 26 parliaments of the run are other parliaments. Addendum I says that these authors opened no file of the 872 documents; no examination compared this statement with the work records. For the title, the affair number and the 2 dates, the precision of the run is lower than on the development documents. The found rate of the response date is 0.4057 in the run and 0.9238 on the development documents. For the first author it is 0.5607 and 0.8488. | `R.<field>.precision`, `R.<field>.found_rate`, `D.<field>.precision`, `D.<field>.found_rate` (table 20) |
| L3 | In the check by eye, each AI examiner named 12 of 50 documents with a kind that looks wrong. Where the kind is wrong, the cascade does not search some fields. The run did not measure the kind. | `L.check_by_eye.kind_looks_wrong`, `L.check_by_eye.documents` |
| L4 | AI agents read 116 or more of the 872 documents in earlier work. For 300 of the 872 documents, an audit found a sign of earlier contact: text or values next to the id, or the id in a list of earlier work. For the other 572 it found no such sign; this is no proof of no contact. | `L.contact.s4.all`, `L.contact.s3.all` |
| L5 | The older rule chain is from the earlier converter. It was designed on a list with 38 documents of the run, of 9 of the 18 validation parliaments. For this part the run is not a measure on new parliaments. | `L.contact.rule_design_list.validation`, `L.contact.rule_design_list.validation_parliaments`, `L.parliaments.validation` |
| L6 | AI agents of one model family (Claude Opus 5.5) wrote the rules, the tools, the measures and the audits. AI agents of the same family examined them. | none |
| L7 | The reference is a register. A value can be correct as printed and differ from the register: affair number 12 of 15, submission date 18 of 21 in the check by eye. | `L.check_by_eye.a.affair_number.C`, `.given`; `L.check_by_eye.a.submission_date.C`, `.given`; table 22 |
| L8 | No pass limit was fixed before the run. Thus no text says that a field passes. The text gives the numbers and their plain meaning. | none |
| L9 | The development values are design values. The authors of the value rules read all 44 development parliaments. These values are optimistic. | `D.mark`, `D.parliaments` |
| L10 | The reference of the affair type is a project map of the export type. The same value is the fit target of the `Q1` head. | none |
| L11 | Group 7 has 68 documents of 8 parliaments, so its intervals are wide. There the certain responder values have 5 wrong values, all of 1 parliament. | `L.documents.group7`, `L.parliaments.group7`, `RG.responder_name.certain.with_reference`, `RG.responder_name.certain.correct` |
| L12 | Each time comes from one laptop clock, and no outside time stamp exists. | none |

Plain forms of 3 limits:

1. L4: AI agents had read some of the documents of the run before the run. The lower limit from id lists is 116 [`L.contact.read_by_ai_agents.lower_limit`] documents (48 [`L.contact.kind1.validation`] validation, 68 [`L.contact.kind1.group7`] group 7).
2. L5: the rule chain (method `nos4`) gives the rule role and the block roles of each document of the run. Its authors wrote it on a list with documents of the run.
3. L7: for the affair type the direction is the other one (chapter 5.7, item 1).

Two more facts:

1. The share correct was not a planned measure of addendum I.
2. The 3 calculations agree on the counts. This does not show that a value is true.

### 6.2 More limits

1. The found rate of the response date and of the first author is much lower in the run than on the development documents (chapter 5.5).
2. The challenge asks for a hand-checked gold set. The one fixed run has none; its reference is the export.
3. The kind of the document comes from the rule chain and from rule V5. No kind of the run was compared with a label.
4. The stored probability of an Apertus tier includes the own fold of a development document. It is optimistic.
5. 2 design files and the result files of the run do not carry each mark that the addenda ask for (dossier, chapter 6.1).
6. The app gives each value from the rules. It has no file of the value heads. On 15.10.2026, with `make setup-pdf`, it converted 2 changed copies of samples. Earlier runs used synthetic PDFs and the 3 sample PDFs (`app/README.md`, chapter "The modes"). No other PDF of a parliament is recorded.
7. `make run` ran one time, on one Mac, with the 3 samples only (target `slim`). The targets `run-full` and `check-offline` of `app/Makefile` did not run.
8. The block-role candidates were measured against an AI reference on validation documents only, before the run. They did not enter the run.

### 6.3 The criterion insight

Table 24: criterion Insight, the head values against eCH-0295.

| Question | Answer |
|:---|:---|
| Does eCH-0295 say which slots a document can state? | The working draft states no condition by affair type. The cascade has 53 [`cascade.rules`] rules: 24 [`cascade.rules.standard`] from the standard, 22 [`cascade.rules.project_choice`] project choices, 7 [`cascade.rules.project_rule`] project rules. |
| How many slots can one document state? | The kind of the document selects 18 [`cascade.slots_by_kind.other.low`] to 61 [`cascade.slots_by_kind.minutes.high`] of 87 [`cascade.i95.slots`] slots. 12 [`cascade.slots.register_only`] slots only a register can give. |
| Which head values can one reader take from PDFs of many parliaments? | The median precision over the parliaments is high for the affair type (0.9841 [`L.spread.rules_only.affair_type.median_precision`]), the responder (1.0000 [`L.spread.rules_only.responder_name.median_precision`]) and the first author (0.9091 [`L.spread.rules_only.first_author.median_precision`]). It is lower for the submission date (0.8000 [`L.spread.rules_only.submission_date.median_precision`]), the title (0.5714 [`L.spread.rules_only.title.median_precision`]) and the affair number (0.5228 [`L.spread.rules_only.affair_number.median_precision`]). For the response date only 2 [`L.spread.rules_only.response_date.parliaments_that_count`] parliaments count. For each field except the response date the lowest value is far below the median (table 23). |
| Where do the PDF and the register differ? | Table 22: a value can be correct as printed and differ from the export. The run has no count of such cases. |
| Where does the export have a gap? | For 276 [`gaps.affair_type.all`] of 2,665 [`sets.docling.all`] documents the export has no affair type of the I95 list. |

Cross-parliament question (development documents, information): in which parliaments does the PDF with the response of the executive also contain the submitted text?

1. The export does not give this answer.
2. With the B1-S block labels, 300 [`xp.written.with_both`] of 719 [`xp.written.with_response`] development documents with response text also have submitted text.
3. The share is 0.417 [`xp.written.share_both`] (0.387 [`xp.written.share_low5`] to 0.448 [`xp.written.share_high95`]). The interval is the 5 % to 95 % quantile of a document bootstrap. 3 other views of the same labels give 0.503 [`xp.expected_d1.share_both`], 0.512 [`xp.expected_r2.share_both`] and 0.548 [`xp.d1_label.share_both`].
4. 32 [`xp.parliaments_with_statement`] of 44 [`xp.parliaments`] parliaments get a statement. The first response block is on page 1 for 450 [`xp.first_response.on_page_1`] documents.
5. Limits: the labels are B1-S labels, measured against an AI reference only. The 1,793 documents are a sample that is stratified by export role. A share is not the share of all documents of a parliament. The labels of the 193 labelled documents are in-sample. The share differs between the views. It is not a result of the one fixed run.

### 6.4 The criterion breadth

1. Parliaments: 26 [`L.parliaments.all`] in the run, 44 [`D.parliaments`] in development.
2. Languages: chapter 4.2 gives the languages of all documents. The languages of the documents of the run have no entry.
3. Kinds of documents: 7 [`cascade.kinds`] kinds of the cascade. The cascade searches each head value only for some kinds.
4. State levels (federal, cantonal, communal): this report gives no count.

## 7. Reproducibility

### 7.1 Commands

The commands are in the folder `track_2a/`. The states are those of 14.10.2026 (`make setup-pdf`: 15.10.2026), on one Mac (Apple silicon, macOS).

| Command | What it does | State |
|:---|:---|:---|
| `make setup` | downloads Python 3.12, the Python packages of the app and the Rust crates (network) | ran on one Mac in a fresh clone; uv and cargo used the local caches |
| `make run` | builds the image of `app/` with Docker and starts the app on 127.0.0.1:8080 | ran one time on one Mac (Docker server 29.2.1), in a clone of GitHub at commit `10e07b4`, as `make run PARLPDFECH_PORT=8082` (a second check used port 8080); the 3 samples in the modes auto and rules gave 6 valid records; a private build pipeline on Linux built a container image from the source tree of the package, and nobody started it |
| `make run-native` | builds the Rust server and the browser bundle with cargo, then starts the app with no container | ran on one Mac, also in a fresh clone; the 3 samples in the modes auto and rules gave 6 valid records |
| `make setup-pdf` | for an own PDF with `make run-native`, after `make setup`: installs Docling and its 2 models (network); needs the command `pdftotext` | ran on one Mac in a fresh clone; then `make run-native` converted 2 changed copies of samples, with 2 valid records. No other PDF of a parliament was converted |
| `make test` | checks with no network: the copies against `SOURCES.json`, the prompt files, the file list and code layout of `app/`. Its YAML validator reads the 6 stored outputs of the earlier converter (`samples/*/expected/`) and `tests/invalid_instance.yaml` | PASS, also in a fresh clone |
| `make test-app` | the checks of `app/`: the cargo checks of the 2 crates, the example view and a start of the seed script | PASS |
| `make run-earlier` | the earlier converter of 12.10.2026. It takes its metadata from the export record, not from the PDF | PASS |
| `make head-selftest` | a synthetic self-check of an earlier Apertus head code of 12.10.2026 | not run for this text |

`make test` has no check of `numbers.json`.

### 7.2 What a person can repeat

1. The app gives the values of the 3 samples from the rules, and block labels from their stored Apertus states. These samples are development documents and were in the fit.
2. The app converts an own PDF with the rules only. It needs `make setup-pdf` and `make run-native`; `make run` converts the 3 samples only. On 15.10.2026, with `make setup-pdf`, the app converted 2 changed copies of samples. Earlier runs used synthetic PDFs and the 3 sample PDFs (`app/README.md`, chapter "The modes"). No other PDF of a parliament is recorded.
3. A person cannot repeat the values of chapter 5 from this repository alone. The states, the reference files and the ids of the run are not published.

### 7.3 Hardware and software

- An Apple M4: Docling, the readers, the measures and the validation.
- A virtual machine with one H100 GPU: the states of Apertus and the training of B1-L.
- LinkML 1.11.1 [`val.gj12.linkml_version`] and rdflib 7.6.0 [`val.gj12.rdflib_version`] (read).
- Apertus in bf16 only.

## 8. Next steps

1. A hand-checked gold set: a sample of reference values and of the kind of the document.
2. A measure of the kind against labels, and value rules for more parliaments. Then a run on documents that no agent read.
3. Apertus states for an own PDF, and the value heads in the app.
4. A start of the container image on Linux, with an open OCR engine.

## 9. Evidence

### 9.1 The dossier

1. The dossier of the run is the file `crisp-dm/05-evaluation/last-run-evidence.md` of the private project. It is not in this repository.
2. Its version 2 has the date 13.10.2026, 23:22. One item was added on 14.10.2026. AI agents wrote it.
3. It names a source for each fact: a file, a git commit or a line of a transcript. 2 skeptic agents examined version 1. No agent compared version 2 with the files.
4. `numbers.json` gives the SHA-256 of the dossier file of 14.10.2026, 10:29, in the source of the id `L.contact.rule_design_list.validation_parliaments`.

### 9.2 What the dossier shows

1. A timeline of the run from git commits, file times, time keys and an access record.
2. A fix record, made before the start of the tool that read the export values for the reference. Its SHA-256 is in the evidence commits and in each result file.
3. The fixed files: the rule modules, the cascade, the readers, the heads, the entry decisions, the measure tools and the criteria.
4. Most fixed files are in a git commit with their exact bytes before the fix record. Some are first in a commit after it. One file is not in git, and one file was not hashed.
5. The block files and the rule files of the documents of the run: on the disk each file has the SHA-256 of the fix record.
6. The entry decisions have a time before the fix record.
7. The access record has one entry for each tool call after the fix record, and no second start of the run.
8. The 3 calculations of the counts agree (chapter 5.10).
9. The contact history of the documents of the run before the fix record (chapter 9.3).
10. The sample of the check by eye is the draw of the fixed seed.
11. The commands with which a person with the private project can repeat these checks.

### 9.3 The contact history

Ids: `L.contact.<key>.<set>` (read; counts from id lists of the contact history). A count from an id list is a lower limit of the contact.

| Kind of contact | All | Validation | Group 7 |
|:---|---:|---:|---:|
| AI agents read the document and gave labels or a verdict (05.10. to 07.10.2026) | 116 | 48 | 68 |
| The document has an AI block label | 101 | 44 | 57 |
| In a list of the authors of the rule chain S1 to S5 | 98 | 43 | 55 |
| Of these, in the design list of the rule chain S1 to S5 | | 38 | 0 |
| In an id source of a measurement | 250 | 185 | 65 |
| In one or more of these 3 kinds of id lists | 257 | 189 | 68 |
| In none of these id lists | 615 | 615 | 0 |

1. The lower limit of the documents that AI agents read is 116 [`L.contact.read_by_ai_agents.lower_limit`]. With the documents that a transcript of 07.10.2026 names, it is 121 [`L.contact.read_by_ai_agents.lower_limit_with_k1_9`].
2. The documents of the design list of the rule chain are of 9 [`L.contact.rule_design_list.validation_parliaments`] of the 18 [`L.parliaments.validation`] validation parliaments.
3. Tools converted each document, made its rule files and its model states before the run. The job folder with the prompts of the documents went to the GPU machine.
4. A search by id does not find a text with no id next to it. Some transcripts were not read. A human, the GPU machine and an outside service are not covered.

### 9.4 What the dossier cannot show

1. An outside time. Each time comes from one laptop clock. The repository of the project has no remote, no tag and no signed commit. A person with access to the laptop can write each commit again.
2. That no program read a result before the fix record. From 18:18 to 21:18 on 13.10.2026, the states of the documents of the run were on the disk. No record of a read exists, and a read with no record cannot be excluded.
3. That the documents of the run were new to the authors. They were not (chapter 9.3).
4. Which files the command of the 2 readers opened at run time.
5. That a reference value is true, or that a value of a reader is the value that the PDF prints.
6. That the sheets of the check by eye had no export value. Their content was not examined for this rule.
7. The check tool of the dossier gives FAIL for the marks of some design files and result files (chapter 6.2, item 5).

### 9.5 What a reader of this repository can check

1. **The code.** `../src/converter_gj/` has copies of the code of the method with a licence line. `../SOURCES.json` gives, for each copy, the source file, its SHA-256, the SHA-256 of the copy and each edit of a line. `make test` compares each copy with `SOURCES.json`.
2. **The code of the app.** `../app/layout/src/` has the files that the app runs. They are byte-equal to the files of the private project, except 3 files with a recorded edit. `../app/DIST-MANIFEST.json` lists each file with its SHA-256.
3. **The code of the run.** The author of this text compared 2 lists of SHA-256 values: the source values of `SOURCES.json` and the values of the fix record of the run. For each fixed code file with a public copy, the 2 values are equal.
4. Some fixed code files have no public copy. These are the design and apply tool of the heads (`m11_value_heads2.py`) and the span functions (`m11_value_heads.py`). Also: the 2 label modules of the heads and the converter of the head outputs. Also: the 2 measure tools of the run and the second calculation of addendum G. Also: the reference tool of the run and the tool of the review sheets.
5. The rule of the first author (`m11_values_sponsor.py`) is not in `../src/converter_gj/`. `../app/layout/src/` has a copy that is byte-equal to the fixed file.
6. A reader cannot repeat the comparison of items 3 to 5: the fix record is a file of the private project. The dossier gives its SHA-256: `f70322721f64f59ce291f8ccc983cec7ce5a35d9130a0e66ecf5f1f176dea468`.
7. **The prompts.** `../src/prompts/gj_values_v1_de/` has the questions `Q0`, `Q1` and `Q2` of the value heads.
8. **The numbers.** Each entry of `numbers.json` gives its source file, the key and the mark. It also gives the SHA-256 of the file or of the line, and the time of the source. A reader can check each derived entry against its parts, and each number of this text against its id.
9. The dossier gives the SHA-256 of 3 files in an evidence commit: the measures file of the run, the review counts and the entry record. `numbers.json` has the same SHA-256 for each of them.
10. **What a reader cannot check.** These parts are not published: the source files of the numbers, the model states and the reference files. Also not published: the ids of the documents of the run and the transcripts. The PDFs and the export are public at OpenParlData.

## 10. Sources of the numbers

Paths are files of the private project. `numbers.json` gives the full SHA-256 of each file and the time of the source. For some files `numbers.json` gives the SHA-256 of the one line that has the value, because these files change often.

| Source file | SHA-256 (first 12 characters) |
|:---|:---|
| (derived from other entries) | no file |
| `crisp-dm/00-cross-cutting/protocol.md` | the SHA-256 of the line of each value (see `numbers.json`) |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-f.md` | `bb04a27aa096` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-g.md` | `8d639546131b` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-i.md` | `db1e48d6e18d` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria.md` | `6f6d15c0562c` |
| `crisp-dm/05-evaluation/evidence/contact-history.json` | `b75bb71b7b0c` |
| `crisp-dm/05-evaluation/evidence/contact-history.md` | `bf09445c1de3` |
| `crisp-dm/05-evaluation/evidence/ids_content_or_values_shown.txt` | `c3563172d35b` |
| `crisp-dm/05-evaluation/evidence/ids_no_ai_block_label.txt` | `1a23ad12f272` |
| `crisp-dm/05-evaluation/evidence/ids_no_earlier_label.txt` | `63aa368717bb` |
| `crisp-dm/05-evaluation/evidence/ids_no_known_contact.txt` | `f1299081e7bd` |
| `crisp-dm/05-evaluation/last-run-evidence.md` | `331c660a07e5` |
| `daten/gj/crossparl_b1s_dev/crossparl.json` | `3004ad8e733d` |
| `daten/gj/design_b1s/design_b1s.json` | `3a78badab1cc` |
| `daten/gj/design_lora_f/design_lora.json` | `2cbcdd666aef` |
| `daten/gj/docs_build.json` | `08c6ae8e2005` |
| `daten/gj/jobs/lora_b1/manifest.json` | `b7b541c7f339` |
| `daten/gj/labels_build.json` | `7655ad8a4d77` |
| `daten/gj/validation/result.json` | `d568a9a453dd` |
| `daten/gj/validation_b1s/result.json` | `13835d1aee23` |
| `daten/gj/validation_lora/result.json` | `b37fb62fd0e3` |
| `daten/gj/verify/validation_lora_gj19/recalc.json` | `391950227059` |
| `daten/gj_values/heads2/entry.json` | `49f554ecf366` |
| `daten/gj_values/heads2/last/measures_first.json` | `16dab6156e3e` |
| `daten/gj_values/heads2/last_review/review_counts.json` | `214f9cab346d` |
| `daten/gj_values/heads2/last_subsets/measures_subsets.json` | `fb79c3360518` |
| `daten/gj_values/heads2/measures_dev.json` | `15282e7fd0c5` |
| `daten/gj_values/heads2/measures_dev_combined.json` | `44c01f9d1c5b` |
| `daten/gj_values/round4/calibration_dev_all.json` | `e48e7a8d8efd` |
| `daten/gj_values/round4/measures_dev_all.json` | `0c55d8bf36ea` |
| `daten/gj_values/round4/rules_compare.json` | `3a683c98ac4a` |
| `daten/gj_values/round4/second_compare_dev_all.json` | `75e7d79d6cf2` |
| `daten/gj_values/round4/values_dev_all.json` | `f428f57f09e5` |
| `package/STATE.md` | the SHA-256 of the line of each value (see `numbers.json`) |
| `src/m11_cascade.yaml` | `ec8f7a51ae8e` |
| `src/m11_values_combined.py` | the SHA-256 of the line of each value (see `numbers.json`) |
| `src/m11_writer.py` | the SHA-256 of the line of each value (see `numbers.json`) |

## Licence

Copyright 2026 the author (see `NOTICE`). This report and the documentation: CC-BY-4.0. Code and prompt files: Apache-2.0. OpenParlData data: CC BY 4.0. Apertus: Apache-2.0 with the Apertus Acceptable Use Policy v1.5.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 14.10.2026, from the evidence dossier of the run, the criteria, the cascade file and `numbers.json`. In the afternoon of the same day, an AI agent changed the states of chapter 7.1. In the evening, an AI agent changed the states of `make run` (chapters 1.4, 6.2 and 7.1). On 15.10.2026 an AI agent added `<doc>.values.ttl`, `make setup-pdf` and the full limits L1 and L2, and narrowed other sentences, after an audit of the submission. In the evening of 15.10.2026, an AI agent shortened some sentences.

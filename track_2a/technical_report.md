# Technical report — ParlPDFeCH

- **Track:** Track 2A — Extracting Parliamentary Affairs from PDFs into One Common Structure (OpenParlData)
- **Event:** Online
- **Team:** ParlPDFeCH — 1 member (the author)
- **Demo:** no demo. Repository: <https://github.com/jkovatsch/ParlPDFeCH>, folder `track_2a/`, command `make run`.
- **Version:** 12.10.2026. Both gates of the project are OPEN. This report gives no gate measurement. For test documents, it gives counts only, no value of a single document.

Each number has a source tag, for example [S7]. The table "Sources of the numbers" at the end gives the file and its SHA-256. The file `technical_report_numbers.json` (in the same folder) gives each number with its source.

## 1. Summary

The OpenParlData exports of 04.10.2026 hold the metadata of 325,599 parliamentary affairs from 89 parliaments [S1]. The challenge says that much content is only in PDF documents [S14]. In a pilot sample of 5 records of development documents, 65 % of the values came from the export and 23 % needed the PDF [S2]. ParlPDFeCH converts these PDF documents into the working draft eCH-0295 (version I95). Apertus writes no text. Each text value is the wording of the PDF, with its page and its position.

The project has two paths. Path 1 is a converter with rules at the isolation level L9. It divides a document into blocks of the submitted text and of the response of the executive. It takes the other values from the export record. Path 2 is an Apertus classification. A trained head on the hidden states of Apertus-v1.5-8B (bf16) decides if a document holds a response of the executive (task R2). Balanced accuracy on 920 validation documents: 0.919 for the head, 0.899 for the zero-shot readout of Apertus, 0.932 for the best rule [S9]. Without the K7 categories (714 documents), the head has 0.980 and the best rule 0.965 [S9]. The task R1 (recommendation of the executive) stopped with a negative result. The converter ran once on 40 test documents, and the head ran once on 1,523 test documents [S7]. The steps of the human reference did not end before the submission. Thus both gates are OPEN, and the two sealed runs have no gate measurement. After the freeze, the project scored both paths against the records of the 26 test documents that the author reviewed (chapter 5.5). This is information, with n = 26, outside the gate criteria. Path 2 ran on these documents on the instruction of the author, as a deviation from its criteria [S7]. R2: the head was correct for 24 of 26 documents, the better rule for 20 [S17]. The 2 errors of the head are the 2 documents with an empty export text [S17]. Path 1: 19 of the 26 claimed documents were exact; a converter that gives only the role got 17 [S18].

## 2. Architecture

| Stage | Path 1: converter (rules, isolation level L9) | Path 2: classification (Apertus head) |
|:-----------|:----------------------------------------------|:----------------------------------------------|
| Input | The PDF and the export record of the same affair. | The text of the whole document (`docs.text` of the export). No metadata field. |
| 1 | Docling converts the PDF into blocks with page, frame and text. `ocrmac` reads scanned pages. | The prompt holds the whole document first and the question last. |
| 2 | Code divides the blocks into atoms: one line of a block or one row of a table, with page, frame and character range. | One forward pass of Apertus-v1.5-8B in bf16 through all 32 decoder layers. Prefill in chunks of 2,048 tokens. |
| 3 | Fixed rules mark the page furniture. Five sub-task rules give the role (S1), the author switch points (S2), frame or text (S3), the title (S4) and the type (S5). The rule composite is the method `nos4`. | Code reads the state of decoder layer 16 at the last prompt token. |
| 4 | The claim rule: the converter claims a document only if it is a written affair and its rule role agrees with its blocks. Else it abstains. | A regression head with an L2 penalty gives q(`yes`). Decision threshold 0.5, acceptance threshold 0.6. |
| Output | An eCH-0295 instance (I95, LinkML) with a provenance profile. The title comes from the export record. The extent of each block has the value status `unsure`. | `yes` or `no` with q. While the gate is OPEN, the converter writes no R2 value. |

At L9, the converter claims the order of the author blocks and the switch points of each claimed document. An author block is a submitted text or a response of the executive. The converter does not claim which lines are body text, and it gives no text type inside a block [S6]. Apertus-v1.5-8B gives the role (S1) only for documents with the S1 rule id R1. All other decisions of path 1 come from rules.

A document with more than 32,768 text tokens gets no R2 output and counts as wrong [S9].

## 3. Use of Apertus

- **Model:** `swiss-ai/Apertus-v1.5-8B`, bf16, no quantization, no merge.
- **How it is used:** readout of fixed answer tokens after a forward pass (Jev-style readout); a trained head on the hidden states; LoRA fine-tuning as a comparison (information only). Apertus generates no text.
- **Where it runs:** a local Mac (MLX), a virtual machine with one H100 GPU at Phoeniqs, and the CSCS inference API. CSCS was for development trials and for the S1 role questions of path 1.

### 3.1 Prompts and head

The prompt files are in `track_2a/src/prompts/` under Apache-2.0. Path 1 uses only the S1 role question (`s1_role.txt`). The R2 question (variant `r2_v1_de`) is in `track_2a/src/apertus_head/m05_cls_apertus.py`. It asks in German, also for French documents [S8]. The zero-shot readout of iteration 1 reads the probabilities of the answer tokens of this prompt [S8]. The head reads the hidden states of the same prompt [S9].

Iteration 2 trained a head on the hidden states. The design used `dev` documents only, with one parliament held out at a time: 48 variants for R2 [S9]. The choice was layer 16 and a regression with C = 0.001. The frozen head trained on 800 `dev` documents of 13 parliaments: 400 `yes` and 400 `no` [S9].

Two more candidates were made and not chosen (information only):

1. LoRA L: LoRA on all 32 layers with a classification head, on the Phoeniqs H100, in bf16, 1.73 GPU hours [S7]. On `dev` (partition P, out of fold), the R2 value was 0.979 for L and 0.996 for the head [S9]. The selection rule, fixed before the values, chose the head.
2. Cascade C: rule answers with a precision of 0.99 or more decide first, and the head decides the rest. On `dev`, the best rule answer had a precision of 0.985 [S9]. Thus C gives the decision of the head for each document.

### 3.2 Infrastructure

| Place | Hardware and software | Use |
|:------------|:-----------------------------------------|:------------------------------------|
| Local Mac | Apple M4, 32 GB memory [S16]; MLX 0.32.3, mlx-lm 0.32.0, Docling 2.133.0, ocrmac 1.0.1 [S15]; Apertus in bf16 | Hidden states of `dev` and validation documents; zero-shot readouts; Docling and the converter |
| Phoeniqs (Swiss cloud, Basel; capacity at no cost for Hack Apertus) | Virtual machine with one H100 SXM5 80 GB (GPU passthrough), 4 vCPU, CentOS Stream 9; PyTorch 2.11.0 with CUDA 12.8, transformers 5.19.0 [S7] | LoRA L; the equality check; the R2 final run; the hidden states of H7k and the scores after the freeze (chapter 5.5) |
| CSCS inference API (development only) | Apertus-v1.5-8B and Apertus-v1.5-70B. Only documents with a personal-data triage PASS. | Development trials; the S1 role questions of path 1 |

Equality check, with a rule fixed before the check: 10 R1 and 10 R2 `dev` documents. The frozen heads read the hidden states of the Mac and of the virtual machine. PASS needs the same decision for 10 of 10 documents and a largest difference of q of 0.02 or less. Result: R1 10 of 10, largest difference 0.000056; R2 10 of 10, largest difference 0.011279. Both PASS [S12]. A second run on 10 long R2 `dev` documents (7,793 to 17,249 prompt tokens) gave 10 of 10 equal decisions, largest difference 0.01297 [S7]. For the 8B on CSCS, the mean difference to the local bf16 model was 0.032, against a bf16 noise of 0.034 [S13]. `make run` does not need CSCS.

### 3.3 Models other than Apertus (track rule)

| Model | Open weights | Role |
|:-----------------------|:-----|:-------------------------------------------------------------|
| Apertus-v1.5-70B (CSCS) | yes | Development trials of an in-context readout. No number in this report comes from it. |
| Docling layout and table models | yes | PDF to blocks in the converter. |
| Apple Vision OCR (`ocrmac`) | no | Text of scanned pages in the converter. It runs only on macOS. |
| Claude Opus 5.5 (AI agents) | no | Code, rules, analysis, measurement scripts, proposals of the gold set records (2 coders and 1 adjudicator for each record), verification, the text of this report. |
| Claude Haiku 5.5 (AI agents) | no | A second look at the text blocks of the 26 records of test documents. |

### 3.4 Apertus use policy

1. The repository holds no Apertus weights. The project publishes no merged and no quantized Apertus. Each user downloads Apertus with an own account.
2. The project publishes no head weights and no adapter, also not on Hugging Face.
3. The user of Apertus is responsible for personal data in the output. The Swiss AI Initiative gives a hash list as an output filter. The converter does not apply this list, because Apertus writes no text: each text value is the wording of a public PDF. Persons are in the output only with a public role.

## 4. Data

- **Source:** the OpenParlData exports of 04.10.2026 and the PDF copies on <https://files.openparldata.ch>. License of the data: CC BY 4.0, "Source: OpenParlData.ch". The API description does not say if this license applies to the PDF copies.
- **Schema:** eCH-0295, working draft at commit `3cab44d` (30.09.2026) of <https://github.com/swiss/political-affairs-ech-group>. It is not approved. The repository holds no copy of it.
- **Split:** by parliament, into development (`dev`), validation and test parliaments. No parliament with a development document is in the test set. The test set has no document of the Confederation, no document in Romansh and no Italian-speaking canton [S13].
- **Personal data:** the documents hold names of persons. A triage of personal data comes before each call to CSCS [S13]. The repository holds no PDF, no text of a test document and no record of a test document. The samples come from development documents and show persons only with a public role.

Path 1. A script with a fixed seed selected 40 test documents of 13 parliaments: German 21, French 17, Italian 2 [S5, S7]. For each of the 26 claimed documents, two AI coders and one AI adjudicator made a complete eCH-0295 record, without the converter answers [S5, S7]. The author examined each record on the PDF in a local review tool, in 2 batches of 13 records. The active review time was 81.2 and 18.1 minutes [S7]. The author examined the parts with evidence in the PDF. A program compared the values that come only from the export with the export record [S7]. A second look by AI agents examined 229 findings: 223 refuted, 5 confirmed in 4 records, 1 not decided [S7]. The author decided all 6 notes. None changes a block order, a switch point or the existence of a block at L9 [S7].

Path 2. The source label of R2 is the role of the local document category in the export (a silver label). K7 removes the documents whose local category is only the name of an affair type [S10]. Sets: 800 `dev` documents; 920 validation documents (a stratified sample of 2,328) [S8]; for R1, 287 validation documents [S8]. The R2 final list has 1,523 documents of the test parliaments, from a population of 9,502 [S7]. Before any text was read, 61 documents of the lists of test documents of path 1 left the list. The list has 0 exact copies and 0 near copies of a `dev` or validation text. By the source label, 1,265 are `yes` and 258 are `no` [S7].

## 5. Evaluation

### 5.1 Path 1: development values

The feasibility check compared each rule with a constrained question to Apertus-v1.5-8B on 22 `eval` documents of development parliaments [S3]. The rules were written on `dev`.

| Sub-task (22 `eval` documents) | Metric | Apertus question (baseline) | Rule (ours) |
|:-----------------------------|:---------------------|:------------|:------------|
| S1 role | accuracy | 0.591 | 0.773 |
| S2 author switch points | labelled F1 | 0.658 | 0.845 |
| S3 frame or text | accuracy | 0.616 | 0.757 |
| S4 exact title | documents | 4 of 22 | 8 of 22 |
| S5 type splits | labelled F1 | 0.194 | 0.875 |

At L9 with `nos4`, 99 of 124 claimed `dev` documents were exact (in sample) and 15 of 15 claimed `eval` documents [S4]. AI references were the comparison basis of these values, not human records. On `dev`, 80 of 86 documents with one author block were exact, and the role alone gives the same 80 [S4]. Only the documents with an author switch examine the isolation: 19 of 30 were exact [S4]. Apertus gave the role of 3 of 124 claimed `dev` documents and 1 of 15 claimed `eval` documents [S5].

Gate 3a on the full task (one of 12 answers for each atom) is NOT MET (06.10.2026). A LoRA isolation got a labelled boundary F1 of 0.455 on a final group of 8 documents, against a limit of 0.95 [S14].

### 5.2 Path 2: task R2 (the document holds a response of the executive)

Metric: balanced accuracy. Baseline: the two rules `heading` and `s1_answer`, and the zero-shot readout of Apertus (iteration 1).

| Method | `dev`, one parliament held out (800) | Validation (920) | Validation without K7 (714) |
|:--------------------------------|:-------------|:-------------|:-------------|
| Rule `heading` (baseline) | 0.718 | 0.732 | 0.733 |
| Rule `s1_answer` (baseline) | 0.845 | 0.932 | 0.965 |
| Zero-shot readout of Apertus, iteration 1 (baseline) | 0.986 | 0.899 | 0.953 |
| Head on the hidden states (ours) | 0.996 | 0.919 | 0.980 |

Sources: [S9], chapters 5.2 and 6.2. The validation values are information: the validation set is the set of iteration 1, and the choices of iteration 2 came after its values.

1. Head minus the better rule, with the 5 % bound of 10,000 paired bootstrap resamples: all validation documents −0.012 (−0.025); without K7 +0.015 (+0.003) [S9].
2. Head minus the zero-shot readout: +0.021 (+0.014) [S9]. LoRA L got 0.923 on validation [S11].
3. 78 of the 93 wrong decisions of the head are `no` documents of one parliament with a K7 category. A critic of iteration 1 found label noise there [S9].
4. Control: a French text with no content got `yes` with q 0.784 from the head. The zero-shot readout of the same pass gave `no` [S9].

### 5.3 Path 2: task R1, negative result

R1 asks for the formal recommendation of the executive on a motion or a postulate. On all 287 validation documents, the head had 250 correct decisions, the zero-shot readout 196 and the better rule 186 [S9]. The gain came from one parliament. There, a guard designed on `dev` only found no stated recommendation in 110 of 174 documents [S9]. With this guard, the method was correct for 146 of 287 documents [S9]. On the documents with the form of the decisive set, the head was below the rules: 98 against 104 of 115 date-linked documents, and 79 against 94 of 94 letters of one parliament [S9]. LoRA L got 148 of 287 [S11]. The author stopped R1 on 12.10.2026 [S7]. Causes [S9]:

1. Label source. In one parliament, the label comes from the title of the source document. A rule can read the same title in the text.
2. Reasons before formula. The head follows the reasons of a letter more than the formula of the recommendation.
3. Training data. No `dev` document with a stated recommendation is in French or from that parliament.
4. No option `none`. The head gives a confident value to a document without a recommendation.

### 5.4 Status of the gates

The table gives the state of both gates on 12.10.2026 and the steps that did not take place.

| Item | Gate 3a version 4 (path 1) | Gate of the Apertus classification, R2 (path 2) |
|:--------------------|:-------------------------------------|:-------------------------------------|
| Criteria | Fixed on 09.10.2026, before the converter run [S7] | Accepted by the author (GC.1) on 12.10.2026, after the validation values [S7] |
| Frozen run on test documents | 09.10.2026: 40 selected, 26 claimed at L9; answers sealed [S7] | 12.10.2026: 1,523 of 1,523 documents with an output; outputs sealed, not opened [S7] |
| Human reference | 26 records examined by the author [S7] | 26 values drawn for a blind check [S7] |
| Not done | Blind repetition of 4 records (G3a.16); acceptance of the reference (G3a.2); measurement | Blind check of the 26 values; acceptance of the reference (GC.2); measurement |
| Decisive limits | Exact documents at least 0.80 × n of n claimed; claimed share 0.50 or more [S5] | Recalls min(0.80, A − 0.05) or more; gain 0.05 or more over the better rule [S10] |
| Status | OPEN | OPEN |

Why: on 12.10.2026, the project chose to submit a minimum version on 13.10.2026, because of time [S7]. The steps that need the author did not take place. Without them, the criteria permit no measurement. Nobody opened the sealed outputs of the R2 final run. On validation without K7, the gain of the head over `s1_answer` was 0.015; GC.16 asks for 0.05 [S9, S10].

Statements of the criteria of gate 3a version 4 [S5]: (1) Gate 3a on the full task is NOT MET, and this result does not change. (4) At the block unit, the converter claims the author sequence and the switch points; it does not claim which lines are body text. (8) The converter does not isolate debate and committee texts, although eCH-0295 holds them.

Two deviations of path 2 [S7]: (a) the protocol did not hold the SHA-256 of the criteria before the first value of the head; two run logs and a git commit hold it before the first value (GC.23). (b) The author accepted the criteria after the validation values.

### 5.5 Scores after the freeze on the 26 reviewed test documents (information)

These values are not a gate measurement. Both gates stay OPEN, because G3a.2, G3a.16 and GC.2 did not take place [S7, S18]. The reference is the 26 records of one human reviewer, the author, with no second review [S17]. The 26 documents are the claimed set of path 1, not a random sample of the test set. They come from 11 parliaments; one parliament has 6 of them [S17]. The R2 final list left out the lists of test documents of path 1 (chapter 4). Thus these 26 documents are not the 26 values of the R2 blind check (chapter 5.4) [S7]. Path 2 ran on these documents on the instruction of the author. This is a deviation from criteria v2, chapter 2.1, item 1 [S7]. No model, head, template or rule of H, L3, L, the zero-shot readout and the two rules changed for these scores. No design choice can use them [S17]. An independent check calculated all R2 scores again with its own code [S20]. A second check calculated values of each H7k table again with its own code [S21]. For path 1, the first check calculated 5 values again with the functions of the gate script: exact documents, switch documents, claimed documents, coder pair and role only. The other path-1 values have no independent check [S20]. Both checks found 0 FAIL [S20, S21].

R2 truth: `yes` if the record holds a text block of the response of the executive with content. Counts: `yes` 15, `no` 11 [S17]. A document without a value counts as wrong. H7k is a new head: the frozen recipe of H, trained on the 7,000 `dev` rows of L3 instead of 800 rows. Only the training rows change, and nobody chose a variant on its values [S19, S21]. L3 is a LoRA model of iteration 3 on the same 7,000 rows [S7].

| R2, 26 documents | Correct of 26 | Balanced accuracy | Recall `yes` | Recall `no` | McNemar p against `s1_answer` |
|:--------------------------------|:-----|:------|:------|:------|:----------|
| Head H (800 `dev` rows, frozen) | 24 | 0.933 | 0.867 | 1.000 | 0.125 |
| Head H7k (7,000 `dev` rows) | 24 | 0.933 | 0.867 | 1.000 | 0.125 |
| LoRA L3 (7,000 `dev` rows), LoRA L | 24 | 0.933 | 0.867 | 1.000 | 0.125 |
| Zero-shot readout, iteration 1 | 23 | 0.888 | 0.867 | 0.909 | 0.375 |
| Rule `s1_answer` (baseline) | 20 | 0.800 | 0.600 | 1.000 | – |
| Rule `heading` (baseline) | 18 | 0.733 | 0.467 | 1.000 | – |

Sources: [S17, S19]. The Wilson 95 % interval of 24 of 26 is 0.759 to 0.979 [S17].

1. 2 documents have an empty export text, and their truth is `yes`. No method has a value for them. They are the 2 errors of H, H7k, L3 and L [S17, S19].
2. H, H7k, L3 and L give the same decision on each of the 26 documents [S19].
3. H is correct on 4 documents where `s1_answer` is wrong, and `s1_answer` on 0 where H is wrong. With n = 26, the exact two-sided McNemar p is 0.125. This difference is not statistically significant at 0.05 [S17].

H7k against H [S19]. The H100 made the hidden states of the 7,000 rows (GPU lock held 129.82 minutes). `dev`, partition P, out of fold: 0.996250 for both. Validation: 0.917 against 0.919; without K7: 0.979 against 0.980. H7k minus H on validation: −0.0026, 5 % bound −0.0076. The decisions differ on 0 of 800 rows of partition P and on 5 of 920 validation documents. Thus, more training rows did not change the decisions of the head on partition P and on the 26 documents.

Path 1 [S18]: the frozen converter output at L9 against the same 26 records. A script used the functions of the gate script, but not the gate command. Thus there is no gate result.

| Path 1, L9 with `nos4` | Value |
|:--------------------------------------------------------|:------------------------------|
| Claimed of the 40 selected test documents | 26 of 40 |
| Exact documents (`exact_block`) | 19 of 26, Jeffreys lower bound 0.574 |
| Exact documents of a converter that gives only the role | 17 of 26 |
| Documents with one reference block: exact (role only) | 17 of 18 (17 of 18) |
| Documents with an author switch: exact (role only) | 2 of 7 (0 of 7) |
| Labelled boundary F1 | 0.308 |
| Block omission (reference blocks without a converter text atom) | 0 |
| Atom intrusion (frame atoms in the converter text) | 676 atoms, rate 0.305 |
| Agreement of the two AI coder proposals: exact documents, worse direction | 22 of 26 |

Apertus gave the S1 role of 1 of the 26 claimed documents [S18].

## 6. Limitations

1. No value in this report is a gate measurement. The values of chapter 5.5 come after the freeze, from n = 26 records of one human reviewer. These 26 documents are the claimed set of path 1, not a random sample. All other values of path 2 come from `dev` and validation parliaments.
2. The path-1 development values use AI references. The records of the test documents are AI proposals that one person examined. The blind repetition did not take place.
3. The R2 labels are silver labels from the export categories.
4. The head gave a confident `yes` to a French text with no content (chapter 5.2).
5. Path 1 is a rule stage. It claims 26 of 40 selected test documents. It gives no text type inside a block, and the extent of each block is `unsure`.
6. The test set has no document of the Confederation, no document in Romansh and no Italian-speaking canton.
7. `ocrmac` runs only on macOS. A converter run on Linux needs another OCR engine, and its text can differ.
8. AI agents (Claude Opus 5.5) wrote the code, the rules, the measurement scripts and this report.

## 7. Reproducibility

- **Hardware and runtime:** chapter 3.2. Apertus in bf16 only.
- **Seeds:** path-1 selection 20261009 [S5]; R2 blind check draw `cls-check-1` [S9]; bootstrap seed 20261013 with 10,000 resamples [S9]; equality check rows in the order of the SHA-256 of `cls-it2-eq|` and the document id [S12].
- **Frozen files (SHA-256 prefix):** path 1 freeze manifest `440e4247`, sealed answers `1ed2e987` [S7]; R2 head `d6a9667f`, freeze record `9517c31d` [S9]; seal of the R2 final run `312f27da` [S7]; R2 truth of the 26 records `95fda857` [S17].
- **Commits:** the private project commit `7efdc54` holds S1 to S10, S13 and S15 without a change. S11 and S12 are not in this commit or differ from it. S17 to S21 are data files of the private project; no commit holds them. `technical_report_numbers.json` gives the SHA-256 of each source file. The public commit is the commit of the submission.
- **Run:** `make run` needs no GPU and no network after the downloads that the README lists.
- **Limit:** a reader cannot repeat the path-2 values from this repository alone. The head weights, the document lists and the hidden states are not published.

## 8. Next steps

1. Do the blind repetition, the acceptance and the one measurement of gate 3a version 4 with the frozen script.
2. Do the blind check of the 26 R2 values, the acceptance and the one measurement of the sealed R2 run.
3. Use an OCR engine with open weights that runs on Linux.
4. Add to the profile a value status and an origin `classified` for each Apertus value.
5. R1: an option `none`, training data in French and from more parliaments, and labels that do not come from the title.
6. Answer the cross-parliament question "Does the parliament follow the recommendation of the executive?". It needs R1.

## License

Copyright 2026 the author (see `NOTICE`). This report and the documentation: CC-BY-4.0. Code and prompt files: Apache-2.0. OpenParlData data: CC BY 4.0. Apertus: Apache-2.0 with the Apertus Acceptable Use Policy v1.5. Hack Apertus terms, chapter 6: <https://hackapertus.ch/terms-and-conditions>

## References

1. Challenge: <https://hackapertus.notion.site/track-2a-openparldata>
2. OpenParlData: <https://openparldata.ch>; exports <https://files.openparldata.ch/exports/>
3. eCH-0295 working draft: <https://github.com/swiss/political-affairs-ech-group> (commit `3cab44d`)
4. Apertus-v1.5-8B: <https://huggingface.co/swiss-ai/Apertus-v1.5-8B>
5. Apertus Acceptable Use Policy v1.5: <https://github.com/swiss-ai/apertus-legal/blob/main/apertus_1.5/USAGE_POLICY.pdf>
6. Docling: <https://github.com/docling-project/docling>
7. Readout principle (Jev): <https://openjev.com>
8. ASD-STE100 Simplified Technical English: <https://asd-ste100.org>

## Sources of the numbers

Paths are files of the private project (not in this repository), except S14. SHA-256 on 12.10.2026; the full values are in `technical_report_numbers.json`.

| Tag | File | SHA-256 (prefix) |
|:----|:----------------------------------------------------------------|:------------|
| S1 | `crisp-dm/02-data-understanding/abschnitte/korpus.md` | `17a96f629e7b` |
| S2 | `crisp-dm/02-data-understanding/openparldata-connection-points-2026-10-08.md` | `d72d40ef2d2e` |
| S3 | `crisp-dm/03-data-preparation/isolation-decomposition-feasibility.md` | `d32e8ef37383` |
| S4 | `crisp-dm/03-data-preparation/isolation-complexity-ladder.md` | `a419b1533204` |
| S5 | `crisp-dm/03-data-preparation/gate-3a-criteria-v4.md` | `1db4b2c2a03c` |
| S6 | `crisp-dm/03-data-preparation/isolation-level-e20.md` | `626a7ae64a78` |
| S7 | `crisp-dm/00-cross-cutting/protocol.md` (entries of 08.10. to 12.10.2026) | `067da2852c6c` |
| S8 | `crisp-dm/04-modeling/apertus-classification-r1-r2.md` | `2634431786b7` |
| S9 | `crisp-dm/04-modeling/apertus-classification-iteration2.md` | `43d4491084d5` |
| S10 | `crisp-dm/04-modeling/gate-apertus-classification-criteria-v2.md` | `82891c653633` |
| S11 | `daten/cls/it2_lora/validation_lora.md` | `e4ad39a63c5f` |
| S12 | `daten/cls/it2/vm_equality/equality.md` | `19d7eaf06038` |
| S13 | `crisp-dm/00-cross-cutting/decisions.md` (E26, E31, scope of the test set) | `23aa12cf22b6` |
| S14 | Version 1 of this report: `track_2a/technical_report.md` at commit `eaacef9` of this repository | `5c9cb7ea3018` |
| S15 | `uv.lock` | `09800a0c2910` |
| S16 | output of `sysctl -n machdep.cpu.brand_string hw.memsize` | `f0117d88c822` |
| S17 | `daten/score26/score26_report.md` (R2 on the 26 records) | `d92851113dcb` |
| S18 | `daten/score26/path1_info.md` (path 1 on the 26 records) | `3078d95f9a77` |
| S19 | `daten/cls/h7k/h7k_report.md` (head H7k) | `50865daad2c1` |
| S20 | `daten/score26/verify.md` (independent check of S17 and S18) | `5e87ecdb2b79` |
| S21 | `daten/cls/h7k/verify.md` (independent check of S19) | `0fe9443f5b84` |

About this report: AI agents (Claude Opus 5.5) wrote it from the records of the private project, in English to the rules of ASD-STE100 (Issue 9). A script compared each number with its source file. No human examined this version.

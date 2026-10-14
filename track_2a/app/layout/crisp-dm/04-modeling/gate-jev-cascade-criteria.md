# Gate GJ: criteria for the conversion from PDF to RDF with calibrated probabilities

Version 1, 12.10.2026, 19:40 CEST (time from the clock). The main agent examined it and changed it on 12.10.2026 before any value of a new method (changes: chapter 16). Status: working draft (PROPOSED), NOT RELEASED. Jonathan accepts the criteria (criterion GJ.1). GJ.1 is OPEN. The gate result is OPEN. All work and all values under gate GJ have the status EXCEPTION (process rule 10; protocol 12.10.2026, 18:40 and 19:29). Actor: workflow sub-agent (Claude Opus 5.5), stream `CRIT` of workflow wf_fd559705-63e, for the main agent. No human checked the content of this file.

Written in English to the STE rules (ASD-STE100, Issue 9).

Sources: the plan to the full conversion ([plan-full-conversion.md](../00-cross-cutting/plan-full-conversion.md), version 1, chapters 2, 3, 4 and 6); the [process rules](../00-cross-cutting/process-rules.md); criteria v2 of the Apertus classification ([gate-apertus-classification-criteria-v2.md](gate-apertus-classification-criteria-v2.md)) and its addenda L, C and VM; the isolation level E20 ([isolation-level-e20.md](../03-data-preparation/isolation-level-e20.md)). Chapter 15 gives the SHA-256 of each source.

The terms of gate GJ are in chapter 6 of the glossary (version 4).

## 0 Order of the records and facts known at writing

1. This file was written before any value of a new method. At 19:40 on 12.10.2026, no hidden state of the new prompts existed. No head, no temperature, no Platt map and no HMM existed. GPU-0 had not started.
2. Step 0a (Platt scaling of R2) waits for the SHA-256 of this file in the protocol (plan, chapter 6.1).
3. The author knows these values:
   - The counts of chapter 3 for `dev` and validation. The author calculated them again from the AI reference files. The author did not open the AI reference files of group 7. The group-7 counts come from the plan.
   - The stored values of the frozen rules `nos4`: `dev` 99 of 124 exact, labelled boundary F1 0.655 on `dev`, `eval` 15 of 15 (`daten/iso/ladder/results.md`).
   - The aggregate values of path 1 on the 26 reviewed records of test documents: 19 of 26 exact, switch 2 of 7, labelled boundary F1 0.308, coder pair 22 of 26. Source: key `main_values_L9` of `daten/score26/path1_info.json` only.
   - The stored R2 values of the head H: validation 920 documents and 714 documents without K7; the 26 records (handoff, chapter 2.2).
4. The author knows no text and no label of a test document. The author did not open a per-document key of `daten/score26/`.
5. The main agent saw content of 5 test documents (protocol 11.10.2026, 12:13 and 12.10.2026, 14:18). Chapter 10.4 records this as a deviation.

## 1 Target, scope and status

1. Target (plan, chapter 1.2): one RDF file set for each parliament PDF and its OpenParlData doc id. The set holds the eCH-0295 record, the provenance, the PDF atoms and a label graph.
2. Each label from the PDF has a calibrated probability, a calibration record, its page and its character span.
3. Code decides where rules have measured certainty (chapter 8.7). A trained Apertus decides the other labels with fixed options. Apertus writes no text. Code makes each value and the RDF.
4. Phases: 4 (modeling) and 6 (deployment). Gate: GJ.
5. All new work under gate GJ has the status EXCEPTION. Each value is NOT RELEASED. No gate can become ACCEPTED by 16.10.2026 (chapter 11).

Label kinds of gate GJ (plan, chapter 2):

| Label kind | Unit | Options or value | Decided by |
|---|---|---|---|
| D1: text parts of the document | document | A, B, C, D (chapter 2.4) | The D1 head if D1 enters (GJ.15). Else the S1 rule with the D1 verifier probability; documents with the S1 rule id R1 always take D1. |
| Block option | Docling block | `submitted`, `reasoning`, `response`, `recommendation`, `title`, `none` | A certain tier (chapter 8.7). Else B1 and B2 if they enter (GJ.16, GJ.17). Else the rule option with the B2 verifier probability. |
| Switch boundary | gap between two blocks | switch or no switch | Code step B2 |
| R2: the document holds a response of the executive | document | yes, no | The frozen head H with a Platt map (GJ.14) |
| Furniture and pictures | atom, block | `none` | The fixed rules R1, R3, R4 and R5 |

The segment probability of an author block and the probability that the whole document is exact are should-have values. They are information.

## 2 Label derivation

### 2.1 Reference

1. The reference of gate GJ is the AI reference E20 v4.1: `daten/iso/v4/ref41/` (48 documents) and `daten/iso/v4/pool_ref41/` (246 documents). Of these 294 documents, 193 are `dev`, 44 are validation and 57 are group 7 (chapter 3).
2. In this file, «the reference» means this AI reference, as in the plan. In the meaning of the glossary, it is draft labels, because it has no human acceptance.
3. The blind pair of the AI reference is exact at isolation level L9 on 0.967 of 30 documents. The documents of `pool_ref41` have one coder. Their answers were converted from E20 v3.1.
4. Pilot overrides: for the 3 `dev` documents 879163, 375917 and 549658, the answers of Jonathan's review replace the AI answers. The source is `e20_answers.json` in `daten/gold/records/review/<doc_id>/`.
5. The author compared the 3 pilots with their AI answers. The atom ids are equal. The block options and D1 do not change (0 differences). Thus the counts of chapter 3 are the same before and after the overrides.
6. The reviewed records of 465245 (validation) and 368972 (group 7) do not replace AI answers. The plan (chapter 2.1, item 3) names only the 3 `dev` pilots.
7. Each label file names its source in the field `reference`: `ref41`, `pool_ref41` or `pilot`. The report gives each value for each source.
8. A probability of gate GJ is the probability that the label agrees with this reference. It is not the probability of the human truth.

### 2.2 Option of each atom answer

The E20 answers map to the 6 options as follows (plan, chapter 3.4). The letter is the letter of the B1 question.

| E20 answer | Option | Letter | Author family |
|---|---|---|---|
| `submitted` | `submitted` | A | Submission |
| `reasoning` | `reasoning` | B | Submission |
| `response` | `response` | C | Response |
| `recommendation` | `recommendation` | D | Response |
| `title`, `short_title` | `title` | E | – |
| `none`, `furniture`, `committee_recommendation`, `speech`, `vote`, `proposition`, `summary` | `none` | F | – |

1. The plan does not name `short_title`, `proposition` and `summary`. This file maps them as the table shows (proposal P1).
2. In `dev` and validation, only `summary` of these 3 answers occurs: 37 atoms in 2 validation documents.

### 2.3 Option of each block

1. A block is one Docling block of the stored Docling output, with the id `B<n>`. The atoms of block `B<n>` are the atoms with an id that starts with `B<n>.`.
2. The option of a block is the option with the most atoms of the block, after the map of chapter 2.2.
3. If two or more options have the same highest count, the option with more atom characters wins. If this count is also equal, the first option in the order A to F wins (proposal P2). `src/m10_labels.py`, `src/m10_rules.py` and `src/m10_score.py` use this rule.
4. In `dev`, 15 blocks have such a tie. In validation, 7 blocks have such a tie. Each tie is between `none` and one other option.
5. The flag `mixed` is true if the atoms of the block have 2 or more different E20 answers before the map. `dev` has 61 such blocks with the pilot overrides (62 without them). Validation has 15 such blocks.
6. No block of `dev` or validation mixes the Submission family and the Response family.
7. A block without an atom in the reference file gets no label. It is not a unit of a block measure. The block counts of chapter 3 count only blocks with 1 or more atoms (proposal P13).

### 2.4 Option of the document (D1)

1. D1 comes from the author families of the atom answers of the reference, before the block majority. Answers of committee, vote and speech do not force D.
2. A: atoms of the Submission family only. B: atoms of the Response family only. C: atoms of both families. D: no atom of these two families.
3. In 1 `dev` document, D1 is A, but no block has a Submission option after the block majority. Thus a D1 option permits the states of its families in B2. It does not require them.

### 2.5 Switch documents and the switch boundary

1. A switch is a change between the Submission family and the Response family in reading order. Blocks with the option `none` or `title` do not change the family.
2. The switch boundary is the gap directly before the first block of the new family.
3. A switch document has 1 or more switches in the reference.
4. The count "with all families" uses the families of `m03_sub_common.role_of`: Submission, Response, committee, plenary and summary. Title is not an author family.
5. The author got the same switch counts from the atom answers and from the block options (chapter 3).

### 2.6 Reference value of R2

1. On an AI reference document: yes if the reference has 1 or more atoms with the answer `response` or `recommendation`. Else no (plan, chapter 3.2, item 4).
2. On the export-labelled set of GJ.14: the field `label` of `daten/cls/r2_dataset.csv`.

## 3 Sets

The author calculated the `dev` and validation values of this table again from the AI reference files on 12.10.2026 (read only). The group-7 values come from the plan, chapter 6.2.

| Set | Documents | Parliaments | Blocks | Switch documents (with all families) | D1 A/B/C/D | Use |
|---|---|---|---|---|---|---|
| `dev` | 193 | 42 | 9,313 | 39 (42) | 67/52/39/35 | All fits and all choices. Grouped cross-validation with 5 folds by parliament. |
| `dev` outside the `nos4` design set | 48 | – | – | – | – | Second condition of rule certainty, fit of the verifier maps, LoRA trigger |
| validation | 44 | 14 | 2,715 | 10 (12) | 19/11/10/4 | Entry decisions; GJ.12 to GJ.17 (one run for each candidate) |
| group 7 | 57 | 8 | 2,142 | 14 (14) | 16/20/14/7 | One run after the method freeze, report only (JD3) |
| 26 reviewed records of test documents | 26 | – | – | 7 | – | Information only, one run after the method freeze, only if JD3 = a |
| other Docling documents (no test documents) | 2,371 | – | – | – | – | No labels. Full run and the cross-parliament question only. |

1. Split: `daten/cls/splits.json` (key `parliaments`) and `daten/analyse/synthese/split.csv`. Group 7 is ZH, AG, GR, LU, VD, JU, 5192 and 6621.
2. Parliament of a document: the field `body_key` of `daten/iso/pool.csv` or `daten/iso/gruppen.csv`.
3. The `nos4` design set is the list `dev` of `daten/iso/sub/splits.json` (183 documents). Of the 193 `dev` documents, 145 are in this list. The other 48 make the set `dev_out_of_design`.
4. The rules saw 42 of the 44 validation documents: 38 in the design set and 4 in the list `eval`. Thus the comparison favours the rules.
5. The rules saw 8 of the 57 group-7 documents: 7 in the list `eval` and 1 in the list `gold` of `daten/iso/sub/splits.json`.
6. The `dev` count of 193 documents and 9,313 blocks holds the 3 pilots. The B1 suffixes of GPU-1 are 9,313 + 2,715 + 2,142 = 14,170.
7. Stream B writes the sets to `daten/gj/sets.json`. GJ.7 compares its counts with this table.

Rules for the use of the sets:

1. `dev`: all fits and all choices of chapters 5 and 8.
2. Validation: one run for each candidate after the design freeze (chapter 10). Before the design freeze, nobody reads a model output of a validation document. The developer gets counts and SHA-256 values only.
3. Group 7: never training data and never the basis of a choice. Before the method freeze, nobody reads a model output of a group-7 document.
4. GPU-1 makes states for validation and group-7 documents before the freezes. These outputs are sealed as items 2 and 3 say.
5. The 26 reviewed records: chapter 10.4.
6. Other test documents: never read and never run. Exception: the sealed GPU-3 run on the 40 selected test documents, only if JD3 = a (chapter 10.4).
7. No silver label and no rule output is a training label (plan, chapter 9, item 13).

## 4 Model input and template

1. Model: Apertus-v1.5-8B in bf16 in the Phoeniqs VM. All 32 decoder layers run. No quantization (E15).
2. Shared prefix: the chat template, the frozen system text, `Dokument:` and all Docling blocks in reading order. Each block is one line: `[B<n> | S.<page> | <Docling label>] <block text>`. Furniture stays in. Nothing is cut.
3. One suffix for each decision: the question with lettered options, the end of the user turn, and `Antwort:`. The extractor crops the cache back to the prefix after each suffix. Thus each suffix sees the whole document and only its own question.
4. Readout: the residual state after decoder layer k at the last suffix token. The letter log-probabilities A to F are a zero-shot diagnostic only (information).
5. Training and inference use the same code path: `src/m10_prompts.py` and the VM extractor (shared interfaces 5 and 6).
6. Questions and options: plan, chapter 3.3, item 1 (D1) and chapter 3.4, item 1 (B1).
7. A document with more than 32,768 tokens in its shared prefix and one suffix gets no Apertus value. Its labels are the labels of the floor converter with the value status unsure. The measures of a method use these labels for the document.

Template rule:

1. The template SHA-256 is the value of the key `sha256` in `template.json` of the prompt job. `src/m10_prompts.py` calculates it.
2. T0 is the template SHA-256 of GPU-1. The protocol entry before GPU-1 records T0 and the SHA-256 of `items.jsonl`. This file does not hold T0, because the prompt job did not exist at writing.
3. One prompt change is permitted before 13.10.2026, 08:00 (clock).
4. Conditions of the change: the evidence comes from `dev` documents only (GPU-0 smoke, `dev` states, `dev` out-of-fold values). A protocol entry before the change gives the evidence, T0, the new value T1 and the changed text.
5. After a change, all states that use the template are made again with T1. This includes validation and group 7.
6. After 13.10.2026, 08:00 or after the one change, the template is frozen. The design freeze file names it.
7. Before each measurement, a script makes `items.jsonl` again from the frozen template and the stored document files. The SHA-256 must be equal to the run record (0 differences).

## 5 Design on `dev`

1. Each fit and each choice uses `dev` only. A choice uses out-of-fold values only. In-sample values are information.
2. Folds: 5 folds by parliament (proposal P8). Sort the 42 `dev` parliaments by their count of `dev` documents, high to low. Equal counts: order by `body_key`.
3. Put each parliament into the fold with the fewest documents. Equal counts: the lower fold number.
4. All blocks of a document are in the fold of its parliament. D1, B1, B2, the temperatures, P17 and the LoRA trigger use the same folds.
5. The head, the B2 transitions and the B2 priors of an out-of-fold value are fitted on the training folds only. The temperatures and the Platt maps are fitted on pooled out-of-fold values (chapter 8).
6. Each design script holds the folds, the seeds, the grids and each selection rule before its first out-of-fold value. Its SHA-256 goes into its run record before that value (GJ.2).
7. D1 head: L2 multinomial logistic regression, K = 4, natural priors (chapter 8.1). Layer k is one of 8, 12, 16, 20, 24, 28 and 32 that GPU-1 and GPU-2 both store. C comes from the grid of the design script.
8. The choice of k and C is the lowest out-of-fold NLL. If two choices differ by less than 0.0001, the smaller C wins, then the lower k.
9. B1 head: the same as the D1 head, with K = 6. The design script fixes the training units before its first out-of-fold value.
10. Temperature: chapter 8.3.
11. Code step B2: the HMM of the plan, chapter 3.4, item 5. The transitions are add-one counts of the reference sequences of the training folds. The emissions are the calibrated B1 posterior divided by the prior of the training folds.
12. B2 form: the joint form with D1 or the free form without D1. The lower out-of-fold NLL of the block options wins. A difference of less than 0.0001 gives the free form.
13. Acceptance threshold a: chapter 8.6. Rule certainty: chapter 8.7. Verifier maps: chapter 8.4.
14. LoRA trigger (13.10.2026, 07:30, `dev` only): chapter 7.3, item 1.
15. The design writes `design_dev.md` and the design freeze file (chapter 10.1).

## 6 Measures

### 6.1 Definitions

1. Accuracy: correct units divided by all units of the set. Each unit counts, also a unit without an Apertus value (it has the floor label).
2. Macro F1: the mean of the F1 values of all options (D1: 4 options; blocks: 6 options). An option with no reference unit and no decision in the set is not in the mean.
3. Recall of an option: correct units with this reference option, divided by all units with this reference option.
4. L9 families: Submission (`submitted`, `reasoning`), Response (`response`, `recommendation`) and none (`title`, `none`). This is the map `SLOT_NOTITLE` of `src/m03_ladder.py`.
5. Certain block: a block that a certain (tier, option) pair of the design freeze decides (chapter 8.7). Each other block is a non-certain block. The set of non-certain blocks is the same for each method and for the rules.
6. L9 exact document: the value `exact_block` at isolation level L9 of `m05_gate3a_v4_measure.measure_level`, through `src/m10_score.py` (plan, chapter 6.3, item 6).
7. L9 exact is measured on all documents (no abstention) and on the subset that the claim flag of `nos4` claims.
8. Switch-document exact: the L9 exact documents among the switch documents of the reference (chapter 2.5).
9. Labelled boundary F1 and text intrusion: the values `labelled_boundary_f1` and `text_intrusion` of the same functions.
10. Rule option of a block: the option that `src/m10_rules.py` gives (the `nos4` chain by import, without CSCS; plan, chapter 4.3).
11. Rule option of a document (S1 baseline): the S1 rule role, with the cached CSCS answers where they exist. Map: proposal A, response B, combined C; minutes, committee and other D (proposal P3).

### 6.2 Calibration measures

Each measure uses the probabilities as written, after the clip of chapter 8.5.

1. ECE: top-label calibration error with 10 bins of equal width of max q on [0, 1]. The last bin holds 1.0.
2. ECE = sum over the bins of (n_b / N) × |accuracy_b − mean of max q_b|.
3. ECE with equal mass: 10 bins of units sorted by max q. The bin sizes differ by 1 or less. This is information.
4. Class-wise ECE: for each option c, 10 bins of equal width of q_c over all units. ECE_c = sum over the bins of (n_b / N) × |s_b − m_b|. s_b is the share of the units in bin b with the reference option c. m_b is the mean of q_c in bin b. The class-wise ECE is the mean of ECE_c over the options.
5. Brier score: the mean over the units of the sum over the options of (q_c − y_c)².
6. NLL: the mean over the units of −ln q(reference option).
7. Reliability table: n, mean max q and accuracy for each bin.
8. Coverage against error: for each a of chapter 8.6, the coverage and the error of the units with max q ≥ a.
9. Wrong labels with max q ≥ 0.99: count.
10. A binary label kind (switch boundary, R2, verifier) has q = (p, 1 − p).
11. Units of the switch boundary: each gap between two blocks of a document. The reference value is 1 at the switch boundary of chapter 2.5, item 2.

### 6.3 Intervals and bootstrap (proposal P4)

1. Jeffreys interval: the 5 % and 95 % quantiles of Beta(k + 0.5, n − k + 0.5). Jeffreys posterior mean: (k + 0.5) / (n + 1).
2. Document bootstrap: 2,000 resamples of the documents of the set, with replacement. Seed 20261013 (`numpy.random.default_rng`).
3. Each resample calculates the value again from all units of the drawn documents. A document that is drawn twice counts twice.
4. The 95 % lower bound is the 5 % quantile of the 2,000 values. The 95 % upper bound is the 95 % quantile.
5. Paired document bootstrap: both methods use the same resamples. The value is the difference: method minus baseline.

### 6.4 Reproduction before a comparison

1. Before any comparison value, `src/m10_score.py` reproduces the stored `nos4` values: `dev` 99 of 124 exact, labelled boundary F1 0.655 on `dev`, `eval` 15 of 15 (GJ.6).
2. Before a value on the 26 reviewed records, it reproduces 19 of 26 exact, switch 2 of 7 and labelled boundary F1 0.308.
3. If a reproduction fails, no comparison value exists until it passes (plan, chapter 11, item 9).

## 7 Entry rules (V4)

Each step has one pooled entry decision on the 44 validation documents, from one run (chapter 10.3). A script makes the decision from the counts. Each decision is fixed now, before any value.

### 7.1 D1

1. Baseline: the S1 rule role of chapter 6.1, item 11, on the same 44 documents.
2. D1 enters if both conditions are true:
   - the 95 % lower bound of the paired document bootstrap of the gain in accuracy is more than 0;
   - the count of correct D1 decisions on the 10 C documents is not lower than the count of the S1 rule minus 1.
3. If D1 enters, the D1 head decides the document option of each document.
4. If D1 does not enter, the S1 rule without CSCS decides. The D1 verifier probability is the probability (chapter 8.4).
5. A document with the S1 rule id R1 always takes the D1 decision (plan, chapter 2).

### 7.2 B1 and B2

1. Baseline: the rule option of each block, and the `nos4` answers through `src/m10_score.py`, on the same 44 documents.
2. B1 and B2 enter if all 3 conditions are true:
   - the 95 % lower bound of the paired document bootstrap of the gain in 6-option block accuracy on the non-certain blocks is more than 0;
   - the count of L9 exact documents (all 44, no abstention) is not lower than the count of the rules minus 1;
   - the count of switch-document exact (10 documents) is not lower than the count of the rules minus 1.
3. If B1 and B2 enter, the B2 path decides the non-certain blocks. A certain block keeps the option of its tier.
4. If B1 and B2 do not enter, the rule option decides each block. B2 gives the verifier probability of each rule label (chapter 8.4). The report gives the negative result.

### 7.3 B1-L (conditional LoRA)

1. Trigger at 13.10.2026, 07:30, on `dev` out-of-fold values only. B1-L starts if one of these conditions is true:
   - on the non-certain blocks of the 48 out-of-design documents, the B1 and B2 accuracy is not more than the rule accuracy;
   - the ECE of the B2 block marginals after temperature on all `dev` blocks is more than 0.05.
2. Recipe: plan, chapter 3.5, items 1 and 2.
3. Entry: the rule of chapter 7.2 with B1-L in place of B1, on the same 44 documents.
4. Cut: if B1-L has no validation value at 14.10.2026, 08:00, B1-L does not enter.
5. If B1-L and B1 both enter, the choice uses `dev` out-of-fold values only (proposal P5). The higher 6-option accuracy on the non-certain `dev` blocks wins. A difference of 0.005 or less gives B1.
6. If B1-L runs, the block step has two validation runs. The report says this.

### 7.4 Floor converter F1

1. The floor converter F1 uses no Apertus state. Each rule label has its rule-tier probability (chapter 8.7, item 5).
2. F1 has one validation run on 13.10.2026. Its group-7 value comes only from the one group-7 run after the method freeze.
3. F1 has no entry rule. It is the fallback of chapter 10.6.

## 8 Calibration rules

### 8.1 Natural priors

1. No class weights, no change of the class shares and no prior correction. The B2 emission of chapter 5, item 11 is the only division by a prior.

### 8.2 Selection

1. Each choice of a head (layer k, C) and of the B2 form uses the out-of-fold NLL on `dev` with the folds of chapter 5.

### 8.3 Temperature

1. D1 and B1: one temperature T > 0 for each head. The fit minimizes the NLL of the pooled out-of-fold logits of `dev`.
2. B2: one more temperature on the out-of-fold B2 marginals of `dev`, after the B1 temperature.

### 8.4 Platt maps (verifier and R2)

1. Platt map: p' = 1 / (1 + exp(−(α × logit(p) + β))). The fit minimizes the NLL.
2. R2 (step 0b, shipped): input the H readout on Docling text. Fit set: the 193 `dev` AI reference documents. Reference value: chapter 2.6, item 1.
3. R2 (step 0a, information): fit on the 7,000 stored out-of-fold values of H7k (`daten/cls/h7k/oof_p_r2.csv`). Its values come from export text.
4. D1 verifier: input the calibrated D1 out-of-fold probability of the option of the S1 rule. Reference value: the S1 option is equal to the reference D1. Fit set: the 48 out-of-design `dev` documents.
5. B2 verifier: input the out-of-fold B2 marginal of the rule option of each non-certain block. Reference value: the rule option is equal to the reference option. Fit set: the non-certain blocks of the 48 out-of-design `dev` documents.

### 8.5 Clip to [0.005, 0.995]

1. Each probability of a label from the PDF is clipped to [0.005, 0.995] after the calibration, because the reference is not perfect.
2. Each value of an option distribution is clipped in the same way. The values are not divided by their sum again (proposal P7).
3. The measures of chapter 6.2 use the clipped values.
4. The RDF stores each probability as a decimal. Percent values occur only in display text (plan, chapter 2.1, item 5).

### 8.6 Value status and acceptance threshold a

1. A label is certain if p ≥ a of its label kind. Else it is unsure. No label is dropped.
2. Acceptance threshold a (criteria v2, P17): the smallest a of {0.6, 0.7, 0.8, 0.9, 0.95, 0.99} that meets 2 conditions on the `dev` values of the label kind.
3. Condition 1: the labels with p ≥ a have an accuracy of 0.95 or more. Condition 2: their coverage is 0.50 or more.
4. The `dev` values are the out-of-fold values for Apertus labels. For rule labels and verifier probabilities, they are in-sample values.
5. If no a meets the conditions, each label of the kind is unsure.
6. Final check (plan, chapter 3.2, item 6): if R2 and the block path do not agree, the affected author blocks and the document label are unsure.

### 8.7 Rule certainty and rule labels

1. Addendum C (precision 0.99 or more on 30 or more `dev` documents) was written for the document tasks R1 and R2. Gate GJ applies it by analogy to rule tiers of blocks. This is a new application.
2. A (tier, option) pair decides alone only if both conditions are true:
   - the precision on the `dev` blocks of the pair is 0.99 or more, and the pair occurs in 30 or more `dev` documents;
   - the precision on the blocks of the pair in the 48 out-of-design `dev` documents is 0.99 or more.
3. Precision: blocks of the pair whose reference option is the option of the pair, divided by all blocks of the pair.
4. If the pair has no block in the 48 out-of-design documents, the second condition is not met (proposal P9).
5. A rule label has the Jeffreys posterior mean of its pair on the `dev` blocks, with the in-sample flag. It never has 1.0.
6. The fixed rules R1, R3, R4 and R5 have the Jeffreys posterior mean of their tier precision.
7. Expected result (plan, chapter 2.2): only fixed furniture tiers qualify. No S1 rule id and no S2 rule qualify.

### 8.8 Calibration record

1. Each label refers to one calibration record (plan, chapter 5.6, item 5).
2. The record holds the method and the fit set (file and SHA-256).
3. It also holds the measure sets with n, ECE, class-wise ECE, Brier score, NLL and intervals.
4. It also holds the reference, the in-sample flag, and «target met» or «target not met» (GJ.13).
5. After a held-out run, there is no new fit.

## 9 Criteria

V1 to V6 are the pre-registered criteria of the plan, chapter 6.4.

| ID | Kind | Criterion | Limit or rule | Reason |
|---|---|---|---|---|
| GJ.1 | acceptance | Jonathan accepts this file (path and SHA-256). | Proposal JD1 b: before 13.10.2026, 09:00. Without GJ.1, the gate stays OPEN, and the work continues as EXCEPTION. | Process rule 1.5 |
| GJ.2 | check | Order of the records. The SHA-256 of this file is in the protocol before the first value of a new method, also before step 0a. The SHA-256 of each design script is in its run record before its first out-of-fold value. | Both before, by the clock times | Plan, chapter 6.1 |
| GJ.3 | check (V6) | Split check before each GPU job and each measurement, with `src/m10_guard.py` and `src/m00_pruefe_testset.py`. Explicit paths only, no fallback of `m03_iso_paths`. | 0 test documents in development material; 0 group-7 documents in a fit | Process rule 6 |
| GJ.4 | check (V6) | SHA-256 of each FROZEN_FILE before each measurement and at each freeze. | 0 changes | Plan, chapter 5.5 |
| GJ.5 | check (V6) | Identity of `src/m10_rules.py` with the stored `nos4` answers of the 205 documents. | 0 differences, except the documents with the S1 rule id R1 (CSCS). The protocol records their count. | Plan, chapter 5.2, item 3 |
| GJ.6 | check (V6) | Reproduction of the scorer (chapter 6.4). | Equal to the stored values | Plan, chapter 6.3, item 6 |
| GJ.7 | check | Sets and labels: counts of `daten/gj/sets.json` and of the label files against chapter 3. Pilot overrides as chapter 2.1. | Equal counts | Shared interfaces 3 and 4 |
| GJ.8 | check | Template rule of chapter 4. | T0 in the protocol before GPU-1; 1 change or less before 13.10.2026, 08:00; 0 differences at each measurement | Plan, chapter 3.1, item 9 |
| GJ.9 | check | Each GPU job: protocol entry before its start; one job at a time (GPU lock); bf16; all 32 decoder layers; offline settings; run record with the SHA-256 of inputs and outputs. | All jobs | Process rule 7 |
| GJ.10 | check | Training material: each fit uses `dev` rows only. | 0 rows from validation, group 7 or test documents; 0 silver labels | Plan, chapter 9, item 13 |
| GJ.11 | check | Freezes and the one-run rule (chapter 10). | 0 changes after a freeze; 1 run for each candidate and set | Plan, chapter 9, item 15 |
| GJ.12 | measurement (V1) | Validity on all 101 validation and group-7 documents, the 5 pilots and the 3 samples. | Each document gives all files of the plan, chapter 5.3. linkml: 0 errors. All checks of the plan, chapter 5.4, items 2 to 6 pass. 100 % of the labels from the PDF have p, a calibration IRI, a page and a span. | Plan, chapter 6.4, item 1 |
| GJ.13 | measurement (V2) | ECE of the shipped block labels on validation: all blocks of the 44 documents, p of the written option, in the variant that the entry decisions give. | ECE 0.05 or less, and the 95 % upper bound of the document bootstrap 0.08 or less | Plan, chapter 6.4, item 2 |
| GJ.14 | measurement (V3) | R2 after the Platt map of step 0b, on the export-labelled set of validation without K7 (chapter 13, P6). | ECE 0.05 or less, and a Brier score lower than H without the Platt map | Plan, chapter 3.2, item 5 |
| GJ.15 | entry (V4) | D1 | Chapter 7.1 | Plan, chapter 3.3, item 7 |
| GJ.16 | entry (V4) | B1 and B2 | Chapter 7.2 | Plan, chapter 3.4, item 10 |
| GJ.17 | entry (V4) | B1-L | Chapter 7.3 | Plan, chapter 3.5, item 6 |
| GJ.18 | check (V5) | Each absolute gate limit of agreement with the reference. | Not above the reference reliability minus 0.05 (L9: 0.967 − 0.05 = 0.917) | Process rule 2.3 |
| GJ.19 | check | A second AI agent calculates each value of GJ.5, GJ.6 and GJ.12 to GJ.17 again, from the stored inputs. | Counts equal. Other values: difference 0.0005 or less; bootstrap bounds: difference 0.005 or less and the same entry decision. | Plan, chapter 6.4, item 7 |
| GJ.20 | information | Rule certainty table: for each (tier, option) pair, the `dev` precision, the document count, the precision on the 48 out-of-design documents, the Jeffreys mean and the result. | Reported | Plan, chapter 2.2 |
| GJ.21 | information | All measures of chapter 6 on validation for each label kind: for each reference source, parliament and language. Also on the non-certain blocks only, and for the floor converter F1. | Reported | Plan, chapter 6.3 |
| GJ.22 | information | Group 7: the values of GJ.12, GJ.13 and GJ.21 from the one run after the method freeze. If the group-7 ECE is above 0.08, the calibration record says «not met on unseen parliaments». | Reported; no new fit | Plan, chapter 6.4, item 2 |
| GJ.23 | information | The 26 reviewed records (chapter 10.4). | Reported with the deviation | Plan, chapter 6.5 |
| GJ.24 | information | R2 step 0a on export text (920 and 714 validation documents). R2 on the 44 validation AI reference documents. Zero-shot letter diagnostic. Cross-parliament question (plan, chapter 6.6). | Reported | Plan, chapters 3.2 and 6.6 |
| GJ.25 | information | Result of the stop rule check and the submission variant (chapter 10.6). | Reported in the protocol | Plan, chapter 9, item 20 |

Notes:

1. GJ.13: if it is not met, the probabilities are still written. The calibration record says «target not met». There is no new fit.
2. GJ.14: if it is not met, R2 is information only.
3. GJ.14: the set holds the validation rows of `daten/cls/r2_dataset.csv` (subset `validation`) with a Docling output and without a K7 category. 136 rows have a Docling output before K7. A script gives the count after K7 at the design freeze. The R2 readouts of these rows come from GPU-2. If they do not exist, GJ.14 is NOT MET, and R2 is information only.
4. GJ.18: this file holds no absolute limit of agreement with the reference. The entry rules compare two methods on the same reference.
5. The thresholds 0.95 (chapter 8.6) and 0.99 (chapter 8.7) are not gate limits. They set the value status only.

## 10 Freezes, one-run rule, held-out runs and stop rule

### 10.1 Design freeze (13.10.2026, 07:30 to 08:00)

1. The design freeze comes before the validation run.
2. The design freeze file (`daten/gj/design_freeze.json`, proposal P12) records the SHA-256 of these files and values:
   - the template (T0 or T1), the `src/m10_*` code, this file, `daten/gj/sets.json` and the label files;
   - the head parameter files, the layer k and C, the temperatures, the HMM transitions and priors, the B2 form and the Platt maps;
   - the tier table with the certain pairs, the values a, the LoRA trigger result;
   - the FROZEN_FILES and the model fingerprint.

### 10.2 Method freeze (14.10.2026, 08:00 to 09:00)

1. The method freeze manifest (`daten/gj/freeze_manifest.json`) holds each file of the design freeze with the same SHA-256 (0 changes).
2. It adds the entry decisions, the B1-L files (if B1-L ran) and the code of the cascade, the writer and the RDF step.
3. After the method freeze, nothing changes. The group-7 run, the run on the 26 records and the full run use it.

### 10.3 One-run rule

1. Validation: one run of the candidates of the design freeze (D1, B1 and B2, R2, floor converter F1). One more run of B1-L only if the trigger started it.
2. Group 7: one run after the method freeze.
3. The 26 reviewed records: one run after the method freeze, only if JD3 = a.
4. If a run stops for a technical cause, continue it only for the documents without an output, with the same frozen files.
5. A second run of a set with changed files is not permitted. If it occurs, the protocol records it. The values of the second run are information only. The decisions use the first run.
6. No value of a held-out run changes a frozen file, a threshold, a limit or a choice.

### 10.4 The 26 reviewed records of test documents

1. Use them only if Jonathan says yes (JD3 = a), only after the method freeze, and in one run.
2. Their values are information with a recorded deviation: no G3a.2, no blind repetition, coder pair 22 of 26, 5 test documents seen by the main agent, and earlier scores on these records.
3. `src/m10_score.py` first reproduces 19 of 26 exact, switch 2 of 7 and labelled boundary F1 0.308.
4. The design uses `dev` and validation values only. Known values: S1 `dev` 0.721, `dev` switch 19 of 30, S2 `dev` recall 0.49. A value on test documents is a comparison only. It is never an argument for a choice.
5. GPU-3 (only if JD3 = a): one sealed run on the 40 selected test documents at 13.10.2026, 08:00, with the frozen template. The developer gets counts and SHA-256 values only, until the method freeze.

### 10.5 Group 7

1. One run after the method freeze, report only (JD3).
2. Group 7 is never training data and never the basis of a choice.
3. The rules saw 8 of the 57 documents. The report says this.

### 10.6 Stop rule (14.10.2026, 12:00)

1. At 14.10.2026, 12:00 (clock), the work on the method stops. After this time, only the full run, the writer, the RDF step, the report and the package continue. No frozen file changes.
2. A step without a validation value at this time does not enter.
3. The submission variant is fixed at this time by the entry decisions. A step that entered decides with Apertus. A step that did not enter gives the rule label with the verifier probability.
4. A document without states gets the labels of the floor converter F1.
5. If the floor converter F1 does not meet GJ.12 on 15.10.2026, 08:00, the MVP (commit `2fd48e2`) is the last fallback for the form.
6. The protocol records the check, the submission variant and the SHA-256 of the method freeze manifest (GJ.25).

## 11 Gate result and status

1. The main agent sets each criterion to MET or NOT MET with the script output (process rule 2.5).
2. The comparison basis is the AI reference. It has no human acceptance (process rule 2.1).
3. Process rule 2.4 needs a blind second annotation by Jonathan, at least one day later. It did not take place. Thus no gate can become ACCEPTED by 16.10.2026.
4. All values of gate GJ have the status EXCEPTION and NOT RELEASED. The report says this.
5. If a check criterion (GJ.2 to GJ.11, GJ.18, GJ.19) fails, no value of the affected step goes into the submission variant. The main agent stops the step and reports the cause (process rule 3).
6. An entry decision does not change the gate status. A step that does not enter is a negative result.
7. A value without the recalculation of GJ.19 is not a value of gate GJ in the report.
8. Only Jonathan sets a gate to ACCEPTED (process rule 2.6).

## 12 Plan to the latest date

The order is fixed. The times are plan values (plan, chapter 7).

| Step | Actor | Latest time |
|---|---|---|
| SHA-256 of this file in the protocol | main agent | 12.10.2026, 21:30 |
| T0 in the protocol | main agent | Before GPU-1 |
| GJ.1 (proposal JD1 b) | Jonathan | 13.10.2026, 09:00 |
| One prompt change (optional) | main agent | 13.10.2026, 08:00 |
| Design freeze and LoRA trigger | AI agents | 13.10.2026, 08:00 |
| Validation run and entry decisions | main agent | 13.10.2026, 12:00 |
| B1-L validation value (if triggered) | main agent | 14.10.2026, 08:00 |
| Method freeze manifest | main agent | 14.10.2026, 09:00 |
| Group-7 run and the run on the 26 records (JD3 = a) | main agent | 14.10.2026, 11:00 |
| Stop rule check, submission variant | main agent | 14.10.2026, 12:00 |
| Technical freeze | main agent | 15.10.2026, 12:00 |

## 13 Proposals for Jonathan

These are choices of this file where the plan is silent or not exact.

| ID | Proposal | Reason | Alternative |
|---|---|---|---|
| P1 | `short_title` maps to `title`. `proposition` and `summary` map to `none` (chapter 2.2). | `short_title` is a title. `proposition` is plenary text like `speech` and `vote`. `summary` is out of scope (plan, chapter 10, item 5). | `summary` as the option of its author family |
| P2 | Ties of the block majority: more atom characters, then the order A to F (chapter 2.3). | Deterministic. The label files and the scorer use it. 22 blocks of `dev` and validation have a tie. | The option of the first atom in reading order |
| P3 | Map of the S1 role to D1: proposal A, response B, combined C; minutes, committee and other D. | The S1 roles have no other D1 meaning. | No D1 baseline from S1 |
| P4 | Each bound is one-sided: 5 % or 95 % quantile; seed 20261013 (chapter 6.3). | As criteria v2, chapter 4.1, items 7 and 15. | 2.5 % and 97.5 % quantiles |
| P5 | If B1-L and B1 both enter, `dev` out-of-fold accuracy chooses; 0.005 or less gives B1 (chapter 7.3). | The choice uses no validation value. B1 is simpler. | B1-L only if B1 does not enter |
| P6 | Set of GJ.14: validation rows of the export-labelled set with a Docling output, without K7 (note 3 of chapter 9). | Shipped R2 reads Docling text. Only 106 of the 920 documents of the step-0a sample have a Docling output. | The 44 validation AI reference documents |
| P7 | Clip without a new sum (chapter 8.5). | The plan says «clipped». | Clip, then divide by the sum |
| P8 | Fold rule of chapter 5, items 2 to 4. | One fold assignment for documents and blocks. | `GroupKFold` of scikit-learn on blocks |
| P9 | A pair without a block in the 48 out-of-design documents does not qualify (chapter 8.7). | The second condition cannot be examined. | The first condition alone |
| P10 | B2 form: equal NLL gives the free form (chapter 5, item 12). | The free form is simpler. | The joint form |
| P11 | Tolerance of GJ.19. | A second script can use another bootstrap code. | The same script and seed, exact values |
| P12 | File names `daten/gj/design_freeze.json` and `daten/gj/freeze_manifest.json`. | The plan names a freeze file and `freeze_manifest.json`. | Other names, before the design freeze |
| P13 | A block without an atom gets no label (chapter 2.3, item 7). | It has no reference answer. | Option `none` |

## 14 Limits

1. The reference is an AI reference, not a human reference. Its L9 reliability (0.967 on 30 documents) has no human acceptance.
2. The sets are small: 44 validation documents and 10 validation switch documents. The intervals are wide.
3. The rules saw 42 of the 44 validation documents. This favours the rules.
4. The thresholds 0.95 and 0.99 are above 0.917. Thus «certain» means agreement with the AI reference only.
5. The temperatures and a come from the same `dev` out-of-fold values. Thus the `dev` values are a little too good.
6. If B1-L runs, the block step has two validation runs.
7. Rule certainty applies addendum C by analogy. Addendum C was written for whole documents.
8. Group 7 is mostly new for the rules (49 of 57 documents).
9. The `dev` AI references and the human records of test documents do not agree in the same way (L9: `dev` 99 of 124, test documents 19 of 26).
10. The set of GJ.14 is small: 136 rows or fewer. Its reference values are export labels, not AI reference values.
11. GPU-1 makes states of validation and group-7 documents before the freezes. Only the seal of chapter 3 keeps them out of the design.

## 15 Files and SHA-256

SHA-256 values on 12.10.2026, 19:40 CEST. Paths from the project folder.

| File | SHA-256 |
|---|---|
| `crisp-dm/00-cross-cutting/plan-full-conversion.md` (plan, version 1) | `9356397c539e6afe13ce5b46d0eed2d4569c67bd4325beda44b5d1736323a68e` |
| `crisp-dm/00-cross-cutting/process-rules.md` | `37ad0fe7992f7023382654ce2d4b1397129bc06ada2b410afec6356b4b6e03de` |
| `crisp-dm/00-cross-cutting/glossary.md` (version 4) | `8df6a4b466b8f3fe0da3ba83e4166d5831072d39d0e684bac08b78a42e6a33c8` |
| `crisp-dm/00-cross-cutting/handoff-2026-10-12.md` | `7759b203892413ea767629650114d5e9145a6fbf77cb16b14e36a40fcf1ef09b` |
| `crisp-dm/04-modeling/gate-apertus-classification-criteria-v2.md` | `82891c653633f98ef5fde2d44bba442d9372d1d774fc13e2ec213246c3316ef0` |
| `crisp-dm/04-modeling/gate-apertus-classification-criteria-v2-addendum-cascade.md` | `a88433109c961d5063e7546cd92277cf032924fa4f907b597c23d51b1efc0068` |
| `crisp-dm/04-modeling/gate-apertus-classification-criteria-v2-addendum-lora.md` | `d2d9781d58aa21dca0dc58d737a379c58728f838ca36223067f76ce98a689e01` |
| `crisp-dm/04-modeling/gate-apertus-classification-criteria-v2-addendum-vm.md` | `a58e09f7360e6d24ae69900f54b5ac5b2f3d29ef44354c4ddb6e70c976481d3e` |
| `crisp-dm/03-data-preparation/isolation-level-e20.md` | `626a7ae64a78e6fd47cc82d0e50935b8ed2aa6febb11675a4568ea97f60282b5` |
| `daten/cls/splits.json` | `d86bd45feb2de77190dc836ca704837c894e4332f0cff393562f9617c6d20930` |
| `daten/analyse/synthese/split.csv` | `3369609a06df1981b6ec19f5e4b9f9e8cbd4a31bf80d44eda358319acdc2596c` |
| `daten/iso/sub/splits.json` (`nos4` design set) | `6b96f3c3c6302f17f6dc14dbf1884752046759b3e8e36416d767890f7db6d4ff` |
| `daten/iso/pool.csv` | `6756b9e6b16f2449c0aaae649d1068a12c26b2e5da6369187e51fa5400f8e616` |
| `daten/iso/gruppen.csv` | `b551722db1907fb25b6b21600c85980fc4f42eb4810f149d0d8100a3592e0917` |
| `daten/iso/ladder/results.md` (stored `nos4` values) | `46e0088b224f020ee756667697ff0e550f7f2411d7379b2a5d31f82f85532a90` |
| `daten/score26/path1_info.json` (key `main_values_L9` only) | `17df25cb9150a8b671dea1cac9731e20ace538a7508b4db355a4bb9ea173e27d` |
| `daten/cls/r2_dataset.csv` | `1dc2b332e269e583782d832998d73a325aa54cce3121713ab84a50a6385b6f2d` |
| `daten/cls/h7k/oof_p_r2.csv` (7,000 rows) | `4de89ddccc39c765754565c482c4e07af969514b22f62de6ddd532be028cf180` |
| `daten/cls/it2/extract_r2_sample.csv` (training rows of H; 0 of the 294 documents) | `2a60554410e30207908acab1b2b39d4b9769c825709ffc544980da2d73dc8b02` |
| `src/m05_gate3a_v4_measure.py` (FROZEN_FILES) | `6de97312a7ea7fa730b8837141a53bf7c6e8e883e7efc9db5d673de544e7d641` |
| `src/m03_ladder.py` (`SLOT_NOTITLE`) | `953d66ee13e88a7fbabfb2d11d8de1aa3476a3bd76b29211d1121923f3304567` |
| `src/m03_sub_common.py` (`role_of`) | `9b8f4b7df485fcccba4ed329001412eecb5210178c5ce4681e2a6fec1cedbfb1` |

This step changed no existing file and made no git commit. It ran no model, used no GPU and made no connection to the VM.

## 16 Changes by the main agent (12.10.2026, before any value of a new method)

1. Chapter 2.3, item 3 and proposal P2: the tie rule is the rule of the code (more atom characters, then the order A to F). The interface examination found that the code and version 1 of this file did not agree. Under the earlier rule, 5 `dev` blocks and 5 validation blocks had another option.
2. Chapter 2.3, item 5: the count of mixed blocks in `dev` is 61 with the pilot overrides.
3. Chapter 15: the SHA-256 of the plan and of the glossary (version 4, with the terms of gate GJ).
4. Template: the shared prefix ends with the separator `\n\n`, and each suffix starts with `Frage: `. Thus tokens(prefix) + tokens(suffix) are equal to the tokens of the joined text. This is true in 5,340 of 5,340 examined cases: the first and the last suffix of each document of the 3 jobs. The template SHA-256 of the 3 jobs is T0 = `72d2eafcc54c0e07d3abeb23c649988c93ccd32147cad14f65c63bc06c3ae70c`.
5. Layers: GPU-1 and GPU-2 both store the layers 8, 12, 16, 20, 24, 28 and 32. Thus chapter 5, item 7 permits each of these layers.


# Limits of the one fixed run of 13.10.2026

This file gives the 12 main limits of the one fixed run. The long report gives more limits ([report-long.md](report-long.md), chapter 6.2). A short form of a limit in another text must not say more than the sentence of this file.

No person has accepted these limits or the numbers of the run. No human checked a value of the run, a tool or a number.

## Words of this file

| Word | Meaning |
|---|---|
| the one fixed run of 13.10.2026 | The measurement on 872 documents of 26 parliaments: 804 validation documents of 18 parliaments and 68 documents of 8 more parliaments (group 7). AI agents had read each group-7 document before the run. The values of each document were compared with the export one time. |
| correct, wrong | Equal or not equal to the export value, after the normalisation of the project. |
| precision | correct / (correct + wrong) |
| found rate | (correct + wrong) / documents with a reference |
| share correct | correct / documents with a reference: the product of precision and found rate |
| correct as printed | The judgement of an AI examiner in the check by eye. It is never mixed with "correct". |
| development documents | 1,793 documents of 44 other parliaments. The rule authors read them, and the heads were fitted on them. |
| check by eye | 2 AI examiners read the same 50 documents of the run. They read the first lines, the last lines and the lines near each value. The result is information only. |
| dossier | The evidence dossier of the run, version 2, a file of the private project (`crisp-dm/05-evaluation/last-run-evidence.md`). It is not in this repository. |

Numbers: each number of this file is an entry of [../numbers.json](../numbers.json). Id stems of this file:

- `R` is `values.last_run.rules_only.all.<field>`, and `C` is `values.last_run.combined.all.<field>`.
- `G7` is `values.last_run.rules_only.group7`.
- `K` is `values.last_run.contact`, and `E` is `values.last_run.check_by_eye`.
- Sets of the run: `values.last_run.parliaments.<all|validation|group7>`. The entries `sets.parliaments.validation` (14) and `sets.parliaments.dev` (42) count other sets: the documents with an AI reference of the block roles.

## The 12 limit sentences

| No. | Limit | Source | Number ids |
|---|---|---|---|
| L1 | Fewer than half of the documents with a reference get the export value. This applies to the affair number, the 2 dates, the title and the first author. Affair number: 182 of 822 documents with a reference (0.2214). Submission date: 238 of 872 (0.2729). Response date: 22 of 106 (0.2075). Title: 406 of 866 (0.4688). First author: 195 of 428 (0.4556). | dossier, chapter 5.9, item 3 | `R.correct`, `R.with_reference`, `R.share_correct` |
| L2 | The authors of the value rules of 13.10.2026 read the 44 development parliaments; the 26 parliaments of the run are other parliaments. Addendum I says that these authors opened no file of the 872 documents; no examination compared this statement with the work records. For the title, the affair number and the 2 dates, the precision of the run is lower than on the development documents. The found rate of the response date is 0.4057 in the run and 0.9238 on the development documents. For the first author it is 0.5607 and 0.8488. | dossier, chapters 5.5 and 5.9, items 1 and 3 | `R.precision`, `R.found_rate`, `values.round4.<field>.precision`, `values.round4.<field>.found_rate` |
| L3 | In the check by eye, each of the 2 AI examiners named 12 of the 50 documents with a kind that looks wrong. Where the kind is wrong, the cascade does not search some fields. The run did not measure the kind. | dossier, chapter 5.7, items 6 and 7; chapter 5.9, item 10 | `E.documents`, `E.kind_looks_wrong` (protocol only) |
| L4 | AI agents had read some of the 872 documents before the run: 116 or more, that is 48 validation documents and all 68 group-7 documents. 116 is a lower limit from id lists. For 300 documents, an audit of the work records found a sign of earlier contact: text or values next to the id, or the id in an earlier list. For the other 572 it found no such sign. This is no proof of no contact. | dossier, chapters 1.3 and 4.2 | `K.read_by_ai_agents.lower_limit`, `K.kind1.validation`, `K.kind1.group7`, `K.s4.all`, `K.s3.all` |
| L5 | The older rule chain (method `nos4` of the earlier converter of 12.10.2026) gives the rule role and the block roles of each document. AI agents designed it on a list with 38 validation documents of the run. These are of 9 of the 18 validation parliaments. For this part of the pipeline, the run is not a measure on new parliaments. | dossier, chapter 1.3, item 24; chapter 5.9, item 1 | `K.rule_design_list.validation`, `K.rule_design_list.validation_parliaments`, `values.last_run.parliaments.validation` |
| L6 | AI agents of one model family (Claude Opus 5.5) wrote the rules, the tools, the measures and the audits. AI agents of the same family examined them. No human checked a value of the one fixed run, a tool or a number. | dossier, chapter 1.6, items 33 and 34 | none |
| L7 | The reference is a register. A value can be correct as printed and differ from the register. In the check by eye, the AI examiners found 12 of 15 given affair numbers and 18 of 21 given submission dates correct as printed. The precision against the export is 0.5275 and 0.5289. For the affair type they found fewer: 31 and 33 of 40, against a precision of 0.9421. The cause is not examined. The 2 numbers are different measures on different samples: 50 documents against all 872. | dossier, chapter 5.9, items 5 to 7 | `E.a.<field>.C`, `E.b.<field>.C`, `E.a.<field>.given`, `C.precision` |
| L8 | No pass limit was fixed before the run. Thus no text of the submission says that a field passes. The texts give the numbers and their plain meaning. | dossier, chapter 1.6, item 37 | none |
| L9 | The development values are design values with the mark "after the opening". The authors of the value rules read all 44 development parliaments. These values are optimistic. | dossier, chapter 5.5 | `values.round4.mark`, `values.round4.parliaments` |
| L10 | The reference of the affair type is a project map of the export type to a type of eCH-0295. The same value is the fit target of the `Q1` head. | dossier, chapter 1.6, item 36 | none |
| L11 | Group 7 has 68 documents of 8 parliaments, so its intervals are wide. In group 7, 5 of the 25 responder values of the reader with rules only are wrong, and the 5 are of 1 parliament. The certain responder values of group 7 have a precision of 0.7619, with 21 values. | dossier, chapters 5.2, 5.4 and 5.9, items 3 and 9 | `G7.documents`, `values.last_run.parliaments.group7`, `G7.responder_name.wrong`, `G7.responder_name.given`, `G7.responder_name.certain.precision`, `G7.responder_name.certain.values` |
| L12 | Each time comes from one laptop clock, and no outside time stamp exists. Each value has the status EXCEPTION, NOT RELEASED: no human accepted the criteria of the run. | dossier, chapter 1.1; chapter 5.9, item 12 | none |

## Two more facts

1. The share correct was not a planned measure of the criteria of the run. The criteria of the run do not name it (dossier, chapter 5.1, items 6 and 19).
2. 3 calculations of the counts agree. This does not show that a value is true. They use the same files. Thus an error of the reader output or of the reference file is in each of them. Source: dossier, chapter 5.6, items 11 and 12.

## What these limits mean for a reader

1. A number of the run describes the 26 parliaments of the run together. A pooled value does not describe one parliament (dossier, chapter 5.9, item 11).
2. The spread between the parliaments is large for the title, the affair number and the 2 dates. The median precision of the parliaments is 0.5714 for the title and 0.5228 for the affair number. For the affair type it is 0.9841. A tool made these values after the run (dossier, chapter 5.8, item 6). Ids: `values.last_run.spread.rules_only.<field>.median_precision`.
3. A wrong value against the export is not always a wrong value of the PDF (L7). The run has no count of such cases.
4. The run as a whole is not a measure on documents that no AI agent read, and not a measure on new parliaments (L4, L5).
5. The challenge asks for an evaluation against a hand-checked gold set. The one fixed run has none. Its reference is the export.
6. No person accepted the criteria of the run, a number or a limit of this repository.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 14.10.2026, from the evidence dossier of the run. On 15.10.2026 an AI agent changed the first paragraph and L5, after an audit of the submission. No human examined it.

# Gate GJ: addendum C to the criteria (B2 forms for B1-L)

Version 1, 13.10.2026, 04:34 CEST (time from the clock). Status: working draft (PROPOSED), NOT RELEASED. Actor: workflow sub-agent (Claude Opus 5.5), stream `D1`, for the main agent. No human checked the content of this file.

Written in English to the STE rules (ASD-STE100, Issue 9).

This file adds rules to [gate-jev-cascade-criteria.md](gate-jev-cascade-criteria.md) (SHA-256 `6f6d15c0…`) and to [addendum B](gate-jev-cascade-criteria-addendum-b.md) (SHA-256 `af77c2ac…`). Those files do not change. The rules of this file apply to B1-L only. They do not change the frozen design of the heads.

## 1 Cause

1. The `dev` design of the heads gave a weak result for the switch boundaries of B2. B2 wrote 46 switch boundaries, and 7 were correct. The rules wrote 38, and 19 were correct.
2. The protocol recorded this result on 12.10.2026, 22:16. Addendum B names it as fact 2.
3. Criteria chapter 5, item 12, permits two B2 forms: `free` and `joint`. The two forms do not use the rule chain.
4. Stream `D1` examined the cause on `dev` out-of-fold values (`daten/gj/design_lora/dev_switch_analysis.md`). Chapter 7 gives the result.
5. Thus the design of B1-L can choose from 5 B2 forms. This file defines the forms and the selection rule before any value of B1-L.

## 2 Terms

1. Gap t is the gap after block t in reading order.
2. Rule view: the rule options and the rule tiers of the blocks of a document (`m10_design.rule_view`). A document with the S1 rule id R1 gets the variant of the highest D1 option of the D1 head.
3. Certain block: a block whose pair of tier and option in the rule view is a certain pair of the tier table (criteria chapter 8.7).
4. Rule gap: a switch boundary of the rule options of the rule view, by criteria chapter 2.5. It is the gap directly before the first block of the new author family.
5. Hidden states: the 10 states of the frozen design (option and last text family).
6. Switch transition at gap t: block t has a last text family, and block t + 1 has a text option of the other family.
7. Posterior: the block posterior of B1-L for the 6 options, after the temperature of B1-L.

## 3 Rule C1: the B2 forms

1. Each form uses the HMM of the frozen design: add-one counts of the reference sequences of the folds that are permitted for the value.
2. Each form gives the path with the highest weight, the block marginals and the switch probability of each gap.
3. Each form writes the rule option at a certain block, as the frozen design does.
4. `free`: the free form of the frozen design, without a change.
5. `joint`: the joint form of the frozen design, without a change. It uses the stored D1 posterior of the D1 head.
6. The 3 new forms use this emission. The emission of a state is the posterior of its option divided by the prior of its option.
7. In a new form, a certain block permits only the states with its rule option.
8. `switch_rule`: a switch transition is permitted only at a rule gap. At each other gap, its weight is 0.
9. `switch_soft`: this form has one strength value w from the grid 1, 2, 4 and 8. At a rule gap, the weight of a switch transition is multiplied by exp(w). At each other gap, it is multiplied by exp(−w).
10. `switch_anchor`: at a rule gap, only a switch transition is permitted. At each other gap, no switch transition is permitted. Thus the path has a switch at each rule gap and at no other gap.
11. The transition weights of a new form are not divided by their sum again. The joint form of the frozen design has the same property.
12. In each new form, the posterior decides the option inside an author family. It also decides the blocks with the options `title` and `none`.
13. In a document without a rule gap, the posterior also decides the author family. `switch_rule` and `switch_anchor` write no switch in such a document.
14. The code of the forms is the function `b2x_document` of `src/m10_b2x.py`. `src/m10_b2x_test.py` compares it with the frozen design and with a full count of all paths.

## 4 Rule C2: the strength value of `switch_soft`

1. The strength value of a held-out fold comes from the other folds only (criteria chapter 5, item 5).
2. For the held-out fold f, each grid value is applied to the `dev` documents of the other 4 folds.
3. A document of fold g gets the HMM of the folds without f and g. It gets its own out-of-fold posterior.
4. The order of the grid values has 4 steps. Step 1: the higher count of switch documents exact. Step 2: the higher count of L9 exact documents.
5. Step 3: the higher 6-option accuracy on the non-certain blocks. Step 4: the smaller value.
6. The first value in this order is applied to fold f, with the HMM of the folds without f.
7. The value of the final B1-L model uses the same order on the out-of-fold results of all `dev` documents.

## 5 Rule C3: the selection of the B2 form of B1-L

1. The selection uses `dev` out-of-fold values of B1-L only. It uses no value of a validation document and no value of group 7.
2. For B1-L, this rule replaces criteria chapter 5, item 12.
3. Values of each form, on the written paths of all 193 `dev` documents: the count of switch documents exact, the count of L9 exact documents, and the 6-option accuracy on the non-certain blocks.
4. The two counts come from `src/m10_score.py`, on all documents without abstention (criteria chapter 6.1, items 6 to 8).
5. The counts of the rules come from the plain rule output of `daten/gj/rules` on the same documents, through the same functions.
6. A form is permitted if two conditions are true. Condition 1: its count of switch documents exact is not lower than the count of the rules minus 1.
7. Condition 2: its count of L9 exact documents is not lower than the count of the rules minus 1.
8. Among the permitted forms, the form with the highest accuracy wins.
9. A form with an accuracy of 0.005 or less below the highest accuracy is equal to the highest form. Of the equal forms, the first form in this order wins: `free`, `joint`, `switch_rule`, `switch_soft`, `switch_anchor`.
10. If no form is permitted, only the forms with the highest count of switch documents exact stay. Items 8 and 9 then decide among them.
11. The code of this rule is the function `select_form` of `src/m10_b2x.py`.
12. The design script of B1-L holds this rule before its first out-of-fold value (addendum B, rule B1, item 4).

## 6 Rule C4: rules that do not change

1. The entry rule of B1-L, its cut and the choice between B1-L and B1 do not change (criteria chapter 7.3, items 3 to 5).
2. The B2 temperature is fitted on the out-of-fold block marginals of the form that rule C3 gives (criteria chapter 8.3, item 2).
3. The threshold a, the clip and the calibration record do not change (criteria chapters 8.5, 8.6 and 8.8).
4. The form of B1-L is fixed before the validation run of B1-L. That run measures one form only.

## 7 Development evidence on `dev` (information)

All values of this chapter are `dev` out-of-fold values with the posteriors of the B1 head. They are not values of B1-L. Sources: `daten/gj/design_lora/dev_switch_analysis.md` and `daten/gj/design_lora/b2_forms_dev_heads.md`.

1. `dev` has 40 reference switches in 39 documents. The free form gives 7 exactly. It gives 12 with a shift of 1 or 2 blocks and 10 with a larger shift. It misses 11.
2. In 10 of the 11 missed cases, the written path has text of the Response family only.
3. The free form writes 17 switches in 15 documents without a reference switch. For 11 of the 17 switches, the reference D1 of the document is B.
4. The rules give 19 of the 40 reference switches exactly. They mark the right gap for 13 switches that the free form does not give exactly.
5. The free form is exact and the rules are not exact for 1 reference switch.
6. The first block of the new family is often a short heading. Its option decides the exact gap.

Table: 7,801 non-certain blocks, 193 documents, 39 switch documents. The strength value of `switch_soft` was 8 for 4 folds and 4 for 1 fold.

| Form | 6-option accuracy on the non-certain blocks | L9 exact documents | Switch documents exact | Labelled boundary F1 | NLL of the block marginals | ECE after a pooled B2 temperature |
|---|---|---|---|---|---|---|
| rules | 0.4198 | 128 | 21 | 0.6118 | – | – |
| `free` | 0.7913 | 124 | 12 | 0.2667 | 0.8994 | 0.0153 |
| `joint` | 0.7937 | 125 | 12 | 0.2759 | 0.9112 | 0.0164 |
| `switch_rule` | 0.7894 | 135 | 15 | 0.4776 | 2.4186 | 0.1854 |
| `switch_soft` | 0.7932 | 134 | 20 | 0.5432 | 1.1375 | 0.0526 |
| `switch_anchor` | 0.7876 | 137 | 20 | 0.5432 | 3.6287 | 0.2899 |

On these head values, rule C3 permits `switch_soft` and `switch_anchor`, and it gives `switch_soft`. This result does not bind B1-L.

## 8 Limits

1. The forms were designed after the aggregate result of the validation run of the heads was known.
2. That aggregate result is: B1 and B2 do not enter, because the count of switch documents exact was 1 of 10 against 4 of 10 for the rules.
3. The weakness was recorded on `dev` before that run (protocol 12.10.2026, 22:16; addendum B).
4. No per-document value of validation was used. Stream `D1` opened no file of `daten/gj/validation` and no validation decision.
5. The 3 new forms were designed after the `dev` switch analysis of the same documents. Thus the `dev` values of chapter 7 are too good.
6. A new form takes the errors of the rules. On `dev`, the rules miss 8 of the 40 reference switches and write 6 switches in documents without a reference switch.
7. The rules saw 145 of the 193 `dev` documents and 42 of the 44 validation documents in their design. This favours each form that uses the rule gaps.
8. The block marginals of `switch_rule` and `switch_anchor` have a high NLL and a high ECE on the head values. GJ.13 measures this for the shipped labels. This file adds no rule for it.
9. Rule C3 changes a choice rule of the criteria after `dev` values of the heads were known. No value of B1-L was known.
10. The switch counts are small. A difference of 1 or 2 documents is not a sure difference.
11. The strength value of a fold uses posteriors of a model that saw the labels of that fold. Each HMM of the choice does not use that fold.
12. Jonathan did not accept this file. All values under gate GJ keep the status EXCEPTION.

## 9 Files and SHA-256

SHA-256 values on 13.10.2026, 04:34 CEST. Paths from the project folder.

| File | SHA-256 |
|---|---|
| `src/m10_b2x.py` | `86c990ac7c1ef282dc1949f27fae47eac6c604e88f5a2bb5b4bfb3869df509d0` |
| `src/m10_b2x_test.py` | `c5f97748ee51d1ee255c6bae47d611aabe81e4ab7f92643ef1c1c6407877bf56` |
| `daten/gj/design_lora/dev_switch_analysis.json` | `a46e51543f454308ae865d257aaf5a64467038586f0faf72dfb771e642fc3914` |
| `daten/gj/design_lora/dev_switch_analysis.md` | `79702c13f99f6594276ca47dc9652afd7af541ba12095dbb6275a0a25be77984` |
| `daten/gj/design_lora/b2_forms_dev_heads.json` | `f43e08b93e7f55cbe50d32d1360640f13e51a6133f811ba5252c64f7e840f53f` |
| `daten/gj/design_lora/b2_forms_dev_heads.md` | `0eba3ee4849a23bc17360e18c1ced47fd74759ad4865adafe6d7ad6b1c4c5f97` |
| `src/m10_design.py` (frozen, imported) | `9e6b912ed0ba1f5b773a12c572eef991da24c4788c40875f7889f1de40cf2adb` |
| `src/m10_score.py` (frozen, imported) | `aca5bd0997b7a5cb7ce7a5fed9d8902a4da79639a686ba5a3f5d43b454bf8bd2` |
| `daten/gj/design/oof/b1_oof.npz` | `0b680699a0bd9217b081450d2abe9c8b2cddbe2fd2864c3cbd0df8f9ff9c7b29` |
| `daten/gj/design/oof/d1_oof.npz` | `2465071fa18d0323594ff7c53cfbb4c1a111b01e672611ae80c92bebb9c1238b` |
| `daten/gj/design/tier_table.json` | `49ed195358bbf6b9e0627d6eaec47fc84051cd40240b98fc4722159c4dd545db` |
| `daten/gj/design/folds.json` | `b61f8f214e0901c5432143a64174d8cca3afea3b3927d0bbdf2e34c86ff4ef5c` |

This step changed no existing file and made no git commit. It ran no model, used no GPU and made no connection to the VM.

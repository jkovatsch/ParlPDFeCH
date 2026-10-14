# Gate GJ: design of B1-S on `dev` (B2 form, second temperature, threshold a)

Run of 2026-10-13T05:27:29+02:00 (time from the clock). Script `src/m10_b1s.py`, SHA-256 `4cdd9ac8a7a74e73ab4cb7e44a039ab7adaf967b86c7a483683c46174d3d90ac`. Status: EXCEPTION (process rule 10), NOT RELEASED. Gate GJ is OPEN. Actor: workflow sub-agent (Claude Opus 5.5), for the main agent. No human checked the content of this file.

Written in English to the STE rules (ASD-STE100, Issue 9).

B1-S is the candidate of addendum D to the criteria: the block posteriors of the frozen B1 head with its frozen temperature, and one B2 form of addendum C.

## 1 Order of the records

1. The script wrote its SHA-256 into `design_b1s.json` at 2026-10-13T05:27:29+02:00.
2. The script read the first out-of-fold value at 2026-10-13T05:27:34+02:00.
3. All values of this file are `dev` out-of-fold values. They are information. Each choice uses them only.
4. This file holds no value of a validation document and no value of a group-7 document.
5. The posteriors are the stored out-of-fold values of the frozen design (`daten/gj/design/oof/`). They are the values of addendum C, chapter 7. Each file has the SHA-256 of addendum C, chapter 9.
6. Documents: 193. Blocks: 9313. Documents of `dev_out_of_design`: 48.

## 2 Choices

1. First temperature (addendum D, rule D1, item 1): T = 1.1050. This is the frozen temperature of the B1 head. The script fitted no first temperature.
2. B2 form (addendum C, rule C3): `switch_soft`. Permitted forms: `switch_soft`, `switch_anchor`. Limits: 20 switch documents exact and 127 L9 exact documents.
3. Forms with an accuracy of 0.005 or less below the highest value: `switch_soft`. Reason of the pool: permitted forms.
4. Strength of `switch_soft` (addendum C, rule C2): for each held-out fold 1: 8, 2: 8, 3: 8, 4: 8, 5: 4. Value for a document of the validation run: 8.
5. Second temperature (criteria 8.3, item 2): T2 = 3.0309. NLL before T2: 1.1375. NLL after T2: 0.6414.
6. Verifier map (criteria 8.4): alpha 0.9046, beta 0.7674, fitted on 1767 non-certain blocks of `dev_out_of_design`. Only the information variant uses it.
7. Threshold a (criteria 8.6). Block labels: 0.8000 if B1-S decides, – if the rules decide. Switch boundaries: – and –. The sign – means: no value of the grid meets the conditions, and each label of the kind is unsure.
8. Value of addendum D, rule D2, item 3: the accuracy of the selected form on the 7801 non-certain blocks is 0.793232 (6188 correct blocks). If B1-S and B1-L both enter, the higher value wins. A difference of 0.005 or less gives B1-S. This script does not make that choice.

## 3 Values on `dev` (out-of-fold) of the rules and of the 5 forms

| Method | 6-option accuracy on the non-certain blocks | L9 exact documents | Switch documents exact | Labelled boundary F1 | Written switch boundaries correct | ECE of the block marginals after the second temperature |
|---|---|---|---|---|---|---|
| rules | 0.4198 | 128 | 21 of 39 | 0.6118 | 19 of 38 | – |
| B1 head, `free` (frozen design) | 0.7913 | 124 | 12 of 39 | 0.2667 | 7 of 46 | 0.0153 |
| B1 head, `joint` | 0.7937 | 125 | 12 of 39 | 0.2759 | 7 of 42 | 0.0164 |
| B1 head, `switch_rule` | 0.7894 | 135 | 15 of 39 | 0.4776 | 12 of 20 | 0.1854 |
| B1 head, `switch_soft` (selected: B1-S) | 0.7932 | 134 | 20 of 39 | 0.5432 | 16 of 38 | 0.0526 |
| B1 head, `switch_anchor` | 0.7876 | 137 | 20 of 39 | 0.5432 | 19 of 38 | 0.2899 |

1. Documents: 193. Non-certain blocks: 7801. Switch documents: 39.
2. The ECE of each form uses a pooled second temperature of that form. For a form that is not selected, the value is information.
3. The L9 values and the switch counts come from `src/m10_score.py`, on all documents without abstention.
4. The stored table `daten/gj/design_lora/b2_forms_dev_heads.json` has the same head values. Rows compared: 6. Equal: yes. Selection equal: yes.

## 4 Calibration of the written labels on `dev`

| Label set | B1-S: n | B1-S: accuracy | B1-S: ECE | B1-S: 95 % bound | Frozen design: accuracy | Frozen design: ECE |
|---|---|---|---|---|---|---|
| all blocks, the method decides | 9313 | 0.8268 | 0.0553 | 0.0800 | 0.8252 | 0.0171 |
| non-certain blocks, the method decides | 7801 | 0.7932 | 0.0651 | 0.0943 | 0.7913 | 0.0195 |
| all blocks, the rules decide (verifier probability) | 9313 | 0.5140 | 0.0398 | 0.0694 | 0.5140 | 0.0230 |
| non-certain blocks, the rules decide | 7801 | 0.4198 | 0.0465 | 0.0816 | 0.4198 | 0.0285 |
| certain blocks (rule tier) | 1512 | 1.0000 | 0.0050 | 0.0050 | 1.0000 | 0.0050 |
| switch boundaries, the method decides | 38 | 0.4211 | 0.4071 | 0.5382 | 0.1522 | 0.4052 |
| switch boundaries of the rules | 38 | 0.5000 | 0.3971 | 0.5316 | 0.5000 | 0.3330 |

1. Block marginals of B1-S after T2, all blocks: ECE 0.0526, 95 % bound 0.0772, Brier score 0.2666, NLL 0.6019. Frozen design (free form): ECE 0.0153.
2. Posterior of the B1 head after T, all blocks: accuracy 0.8577, ECE 0.0125, NLL 0.4093.
3. The limit of GJ.13 is an ECE of 0.05 or less on validation. The values of this chapter are `dev` values.

## 5 Limits

1. The reference is an AI reference without a human acceptance.
2. B1-S was designed after the aggregate result of the validation run of the heads was known (addendum D, limit 1).
3. The 3 new forms were designed after the `dev` switch analysis of the same posteriors (addendum C, chapter 8). Thus their `dev` values are too good.
4. The form, the strength, the second temperature and a come from the same `dev` out-of-fold values.
5. The strength of a fold uses posteriors of heads that saw the labels of that fold (addendum C, limit 11).
6. The rules saw 145 of the 193 `dev` documents in their design. This favours each form with rule gaps.
7. The switch counts are small. A difference of 1 or 2 documents is not a sure difference.
8. Jonathan did not accept the criteria or the addenda B, C and D. All values have the status EXCEPTION.

## 6 Inputs

| File or digest | SHA-256 |
|---|---|
| `daten/gj/design_freeze.json` | `add6fdad843cf24c08c0cf69992d610c0017cb8f77ae7e28f6c1aef0770e5e52` |
| `daten/gj/design/oof/b1_oof.npz` | `0b680699a0bd9217b081450d2abe9c8b2cddbe2fd2864c3cbd0df8f9ff9c7b29` |
| `daten/gj/design/oof/b2_oof.npz` | `4acaecd27c331b2bf3590747ae0bf87c65ccecbbffe91ad56b1210781353de1b` |
| `daten/gj/design/oof/d1_oof.npz` | `2465071fa18d0323594ff7c53cfbb4c1a111b01e672611ae80c92bebb9c1238b` |
| `daten/gj/design/heads/d1_head.npz` | `c583c7aaf79564af87092585f24cc0c3faf1d9df9ea2b7d65a3887f884220bd3` |
| `daten/gj/design/heads/b1_head.npz` | `eea315eef8fa9df77385847b34d307ef2c9e4ad4140ca1b23a3cff5d715a4eb7` |
| `daten/gj/design/b2_hmm.json` | `1a1c1106b6347e94fbca8952aec77158606742202dd0a1142cf5a871debdd73a` |
| `daten/gj/design/verifiers.json` | `638a3b3cc0c5dbc2aa32d842baa57a529fd359a828d9849d45f44c1e78e8a527` |
| `daten/gj/design/tier_table.json` | `49ed195358bbf6b9e0627d6eaec47fc84051cd40240b98fc4722159c4dd545db` |
| `daten/gj/design/thresholds.json` | `b04ef908aa97511094a9c9a5eb50c0caccee96224fcec3b65cff1ee3febcd5aa` |
| `daten/gj/design/lora_trigger.json` | `ea692af4278821aa9b99ffe6c594c9dec50c10a333bc94a0d01f23600f3333dc` |
| `daten/gj/design/calibration_records.json` | `859a7965617b4bd7ce054e78664af9a01fa030e30b1937efd9f32d936057df9e` |
| `daten/gj/design/design.json` | `aae764085e46cabe9a7e10a6862137be4ca4f301b617aa85ba76e67adc58f3b7` |
| `daten/gj/sets.json` | `e5e4f80ffce0c7d5157ae0f6ff5e67eef6a2da1058f57423f9c51606d0ca8f19` |
| `daten/gj/design/folds.json` | `b61f8f214e0901c5432143a64174d8cca3afea3b3927d0bbdf2e34c86ff4ef5c` |
| `labels_digest` | `6146093cdba1068be548e2228843256f00c23cf82a7918a3c68ebb48447690b7` |
| `rules_digest` | `76ec54a1620fb4a30ac063d61b72c3f81f1ef90b2041cf7f04e0efbaa089f200` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-b.md` | `af77c2ac8573ee1c08bba9c75cd7e46739c8850f5988d066b3254a557153d651` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-c.md` | `264a3810d7637aa3c6c6e39fbab82068d9c15f59ca4f6b88a820b7cc2cc41d5c` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria.md` | `6f6d15c0562cba2070995c302080a9aaedfe665f8d746ed5b0fdd9248bc20bfe` |
| `crisp-dm/04-modeling/gate-jev-cascade-criteria-addendum-d.md` | `43e8414dd3f00fbf9111fa167c22a3c09617651d47540b8c9f1ee187f31bad10` |

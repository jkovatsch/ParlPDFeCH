# Gate GJ: addendum B to the criteria (B1-L runs by a decision of Jonathan)

Version 1, 13.10.2026, 04:02 CEST (time from the clock). Status: working draft (PROPOSED), NOT RELEASED. Actor: main agent (Claude Opus 5.5), session d6d8d38e, by an order of Jonathan. No human checked the content of this file.

Written in English to the STE rules (ASD-STE100, Issue 9).

This file adds rules to [gate-jev-cascade-criteria.md](gate-jev-cascade-criteria.md) (SHA-256 `6f6d15c0…`). That file does not change. The main agent wrote this addendum before the design freeze and before any value of a validation or group-7 document.

## 1 Cause

1. The LoRA trigger of criteria chapter 7.3, item 1, gave the value false on 12.10.2026 (protocol 22:16; `daten/gj/design/lora_trigger.json`). By that rule, B1-L does not start.
2. The `dev` design shows two facts that the trigger does not examine. These are out-of-fold values on `dev` (information).
3. Fact 1: no acceptance threshold a exists for the block labels and for the switch boundaries. Thus each such label has the value status unsure.
4. Fact 2: the written switch boundaries of B2 are correct in 7 of 46 cases. The rules are correct in 19 of 38 cases.
5. The main agent told Jonathan these facts and asked for his decision (chat, 13.10.2026, about 04:00). Jonathan: "ja dann los weg mit dem freez und weiter".
6. The main agent reads this answer as two decisions: B1-L runs as a second path, and the design freeze is written now.
7. The plan (chapter 10, item 10) had LoRA without the trigger out of scope. This addendum changes that item.

## 2 Rule B1: B1-L runs

1. B1-L runs although the trigger value is false. The trigger value does not change. The design freeze file records the value false.
2. Recipe: plan, chapter 3.5, items 1 and 2. The template is T0.
3. Training data: `dev` documents only, with the labels of criteria chapter 2. The folds are the folds of criteria chapter 5.
4. The design script of B1-L holds each other value before its first out-of-fold value: the learning rate, the epochs, the batch rule, the seeds and the rule for a document that is too long for the training.
5. The SHA-256 of that script goes into its run record before the first out-of-fold value (GJ.2).
6. Each choice of B1-L uses `dev` out-of-fold values only. No value of the validation run of the heads changes a choice of B1-L.

## 3 Rule B2: entry, cut and choice

1. The entry rule, the cut and the choice do not change: criteria chapter 7.3, items 3 to 5.
2. Cut: if B1-L has no validation value at 14.10.2026, 08:00, B1-L does not enter.
3. B1-L has one validation run of its own (criteria chapter 10.3, item 1), with a new script. The script writes its SHA-256 into its run record before the first value.
4. The method freeze manifest adds the files of B1-L (criteria chapter 10.2, item 2).
5. The block step then has two validation runs. The report says this (criteria chapter 7.3, item 6).
6. If B1-L does not enter, the report gives it as a negative result.

## 4 Limits

1. This addendum changes a rule after `dev` values were known. No value of a validation document was known.
2. The validation run of the heads comes before the run of B1-L. Rule B1, item 6, keeps the choices of B1-L independent of it.
3. Jonathan gave the order in the chat. He did not accept this file as a criteria file. All values under gate GJ keep the status EXCEPTION.

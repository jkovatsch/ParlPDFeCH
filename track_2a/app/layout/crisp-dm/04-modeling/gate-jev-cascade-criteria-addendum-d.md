# Gate GJ: addendum D to the criteria (candidate B1-S: the B1 head with a B2 form of addendum C)

Version 1, 13.10.2026, 05:02 CEST (time from the clock). Status: working draft (PROPOSED), NOT RELEASED. Actor: main agent (Claude Opus 5.5), session d6d8d38e. No human checked the content of this file.

Written in English to the STE rules (ASD-STE100, Issue 9).

This file adds rules to [gate-jev-cascade-criteria.md](gate-jev-cascade-criteria.md) (SHA-256 `6f6d15c0…`) and to the addenda B and C. Those files do not change. The main agent wrote this addendum before any value of B1-L and before any value of B1-S on a validation document.

## 1 Cause

1. The one validation run of the heads gave this aggregate result: B1 and B2 do not enter. The block accuracy on the non-certain blocks was 0.7419 against 0.4748 for the rules. The count of switch documents exact was 1 of 10 against 4 of 10.
2. Addendum C defines B2 forms that take the switch between the author families from the rule chain. They apply to B1-L only.
3. The development evidence of addendum C (chapter 7) uses the `dev` out-of-fold posteriors of the B1 head. On these values, the form `switch_soft` meets the two conditions of rule C3.
4. The LoRA training of B1-L needs about 7 hours and can fail. The B1 head needs no training and no GPU.
5. Jonathan ordered work at full speed and without questions for 6 hours (chat, 13.10.2026, 04:15). This addendum is a decision of the main agent under that order.

## 2 Rule D1: candidate B1-S

1. B1-S uses the block posteriors of the frozen B1 head, with its frozen temperature (design freeze file `add6fdad…`). The head and its values do not change.
2. The B2 form of B1-S comes from rule C3 of addendum C, on the `dev` out-of-fold values of the B1 head. The strength value comes from rule C2.
3. The second temperature, the threshold a and the calibration record follow rule C4 of addendum C.
4. Each choice of B1-S uses `dev` out-of-fold values only.

## 3 Rule D2: entry, run and choice

1. B1-S has one validation run of its own on the 44 validation documents. The script writes its SHA-256 into its run record before the first value.
2. Entry: the three conditions of criteria chapter 7.2, with B1-S in place of B1 and B2. The baseline is the rule option of criteria chapter 6.1, item 10.
3. If B1-S and B1-L both enter, the higher 6-option accuracy on the non-certain `dev` blocks (out-of-fold) wins. A difference of 0.005 or less gives B1-S, because it needs no adapter.
4. If only one of the two candidates enters, it decides the non-certain blocks. If no candidate enters, the rules decide, as the run of the heads gave.
5. The cut of criteria chapter 7.3, item 4, applies to B1-S too.

## 4 Limits

1. B1-S was designed after the aggregate result of the validation run of the heads was known. Its B2 form exists because that run showed the weakness at the switch. The same weakness was recorded on `dev` before the run.
2. The 44 validation documents then have three runs for the block step: B1 with B2, B1-S and B1-L. Thus a value of B1-S or B1-L on validation is too good as an estimate for new documents.
3. By criteria chapter 10.3, item 5, a strict reader takes the values of the later runs as information only. The report gives each run and says this.
4. Group 7 has no run yet. It is the check on documents that no choice used. It needs a method freeze manifest, and Jonathan decides about that step.
5. Jonathan did not accept this file. All values under gate GJ keep the status EXCEPTION.

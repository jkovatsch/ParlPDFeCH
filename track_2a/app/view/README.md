# view: the view function of the package

`site_view.py` makes the view `parlpdfech-site-view/3` of one record folder of the converter. The pages read this
view. The reference is `../CONTRACT.md` chapter 4.5 and chapter 6, and the schema `../contract/view.schema.json`.

## Files

| File | Content |
|---|---|
| `site_view.py` | `make_view(record_dir, inputs_dir, run_info) -> dict`, the error `ViewError`, a command line |
| `check_view.py` | check script for 4 stored records; writes only below `../work/view_check/` |
| `README.md` | this file |

## Call

```python
import site_view
view = site_view.make_view(record_dir, inputs_dir, run_info)
```

- `record_dir`: a folder with the 9 converter files (`<doc>.labels.yaml`, `<doc>.ech.yaml`,
  `<doc>.provenance.yaml`, `manifest.json`, `validation.json` and the 4 RDF files).
- `inputs_dir`: a folder with `docling.json`, `atoms.json`, `blocks.json` (required) and `decisions.json`
  (optional). One function reads this folder: `site_view.read_inputs`.
- `run_info`: `{"record_id", "origin", "mode", "apertus", "profile", "seconds"}`; `seconds` is optional.
- The function reads the two folders. It writes no file. It uses the standard library and PyYAML.
- It raises `site_view.ViewError` (a `ValueError`) with a short text and no path if a file is absent, if
  `run_info` has a wrong value, or if a link between the files is broken.

Command line, from the project folder:

```
python package/view/site_view.py --record DIR --inputs DIR [--run-info FILE] --out view.json
```

With no `--run-info` the command reads the run data from the files: the record id is `s-<doc id>`, with the
suffix `-rules` if `manifest.json` has the mode `floor`; `apertus` is `stored` if the decisions file has the key
`states`; `origin` is `stored`; `profile` is `native`. The command prints one JSON line with the counts.

## What the function reads

| Part of the view | File |
|---|---|
| `labels[]`, `calibrations[]`, `run.generated_at` | `<doc>.labels.yaml` |
| `document.head[]`, `document.text_blocks[]`, source document | `<doc>.provenance.yaml` |
| the value of each head entry | `<doc>.ech.yaml` at the instance path |
| `run`, `counts.triples`, `counts.record`, `files[]`, `checks[0]` | `manifest.json` |
| `checks[1..9]` | `validation.json` |
| `pages[]` (size, text source) | `docling.json` |
| `pages[].lines[]` (frame, text, character span) | `atoms.json` |
| `blocks[]`, `document.parliament` | `blocks.json` |
| `in_sample` of the labels `d1` and `r2`, `source.head` `B1`, `run.candidate` | `decisions.json` |

The function does not read the TriG file or an RDF/XML file. Each value of the view is in another file.

## Rules of the labels

- `value` is the selected option. `options[]` holds all options with their stored probabilities, in the sequence
  of the record.
- A probability is the number of the labels file. The function does not round it and does not calculate with it.
- `chosen_is_top` is true if no option has a higher probability than the selected option. If it is false,
  `top_option` holds the option with the highest probability.
- `value_status` is `certain` or `unsure` from the record, or `none` for a label with no probability.
- `source.kind` is the source of the record, not changed. `source.group` is the plain class: `rule`,
  `apertus_readout`, `export`, `constant`, `copy`. A code step counts as `apertus_readout` only if
  `run_info.apertus` is `stored`.
- `source.tier`, `source.rule_id` and `calibration_id` come from the record. `source.head` is `R2`, `B1` or `D1`
  by the rule of the contract.
- `in_sample` is the flag of the record. The function has no list of document numbers. `run.in_sample` is true if
  1 or more labels have the flag true. For `origin: new` the value is `null` for the record and for each label
  (not known): see the chapter "Changes of the correction step".
- `target` holds the block, the lines, the page and the character span of the record.
- `calibrations[].basis` holds the counts `dev_blocks`, `dev_correct` and `dev_documents` if the calibration
  record holds the first two.
- `notices[]` holds codes and parameters. The texts are in the strings file of the UI (`notice.<code>`).
- `document.has_export`: for the record form of now it is the key `has_export` of `manifest.json` (an export record was at hand for the cross-check; no value of the record comes from it). For the earlier record form (`PARLPDFECH_VALUES=off`) it is true if 1 or more head values or labels have the source export.

## Check

From the project folder:

```
uv run --offline --frozen --no-sync python package/view/check_view.py
```

The script needs the package `jsonschema`. It makes the 4 views, writes them to `package/work/view_check/` and
prints a report. One function, `input_sources`, names the place of the stored inputs: the folder
`package/data/samples/<doc>/` if it holds the three files, else the stored files of the project data. The
decisions file comes from the path that `manifest.json` names.

Checks of each view: `schema` (the schema and the link checks of `contract/tools/validate_view.py`),
`label_count`, `status_count`, `targets`, `probabilities`, `files`, `inputs`, `repeat`. The top of
`check_view.py` says what each check compares.

Measured on 13.10.2026 (jsonschema 4.26.0, PyYAML 6.0.3 with the C loader); inputs from the project data,
because the samples folder did not exist:

| Record id | Record | Checks | Labels | With probability (certain, unsure) | None | Selected option not the top option | Decimals compared | Seconds of one call |
|---|---|---|---|---|---|---|---|---|
| `s-26171` | reference run | 8 of 8 passed | 33 | 15 (9, 6) | 18 | 0 | 99 | 0.005 |
| `s-879163` | reference run | 8 of 8 passed | 42 | 26 (12, 14) | 16 | 0 | 176 | 0.006 |
| `s-714840` | reference run | 8 of 8 passed | 18 | 10 (6, 4) | 8 | 1 | 64 | 0.003 |
| `s-26171-rules` | floor record | 8 of 8 passed | 32 | 14 (0, 14) | 18 | 13 | 96 | 0.005 |

- The 4 views are also valid with `contract/tools/validate_view.py` (measured, exit code 0).
- The view of `s-26171` is equal to `contract/examples/view_26171.json` as JSON data (measured: 0 differences,
  also in `run.seconds` and `run.profile`).
- A test with a changed view function (each probability rounded to 2 digits, one target set to a block that does
  not exist) made the checks `schema`, `targets` and `probabilities` fail (measured: 100 problems named).

## The floor record (mode rules)

The folder of the floor record has the same 9 files as the folder of the reference run. Read differences of the
content:

- `manifest.json` has no keys `conformance` and `i95_gaps`. Thus `document.conformance` is null.
- The labels have no label `r2` and no source `apertus_head` or `code_step`.
- The calibrations have no `certain_threshold`. The block calibration holds `dev_blocks`, `dev_correct` and
  `dev_documents`; the view gives them as `basis`. The calibration of the label `d1` holds `dev_correct` and
  `dev_documents`, but no `dev_blocks`; its `basis` is null by the rule of the contract.
- In the floor record of 26171, 13 block labels have a selected option whose probability is lower than the
  probability of another option. The view shows this with `chosen_is_top: false` and the notice `chosen_not_top`.

## Limits

- The check uses stored records. A view of a record that the worker makes was not checked here.
- A record of a PDF with no export record (stage P0b) was not available. The codes `no_export`,
  `not_a_sample` (before the correction step: `outside_fit_population`) and `not_examined_pipeline` follow the rules of the contract; only the two codes for
  `origin: new` were run, with a changed `run_info` on a stored record.
- The label kind `author_switch` does not occur in the 4 records. Its path in the function was not run.

## Stage P0b: a PDF with no export record

The reference is `../CONTRACT.md` chapter 10.4.

- `run_info` has the optional key `ocr` (`apple` or `none`). With it, and with `origin` `new`, the view gets the notice `ocr_apple` or `ocr_none`. The schema file of the contract does not have these 2 codes yet.
- A text block that is in the provenance file only (`mapping_status: profile_only`) has empty strings for `ech_slot` and `instance_path`. Its `text_type` is the section key. Its `label_id` is the copy label whose subject is the text block.
- A label of the kind `author_switch` has `target.block_id` null. Its lines are the last line before the boundary and the first line after it. Before, the function stopped for such a label.
- With no `--run-info`, the command line gives a record with no document number the record id `u-<first 16 hex of manifest.json key pdf_sha256>`, `origin` `new` and `apertus` `none`.
- Run after the change: `check_view.py` passed (4 views of stored sample records). The check script has no record of an own PDF; `../worker/check_fresh.py` reads the notices and the label `d1` of such a view.

## Changes of the examination step (13.10.2026)

- `document.parliament_name`: the key `body.name` of the optional input `export.json` (the export record of a sample); null with no export record. The function holds no table of names.
- `labels[].source.head` is `D1` also for a document label with the source `rule` whose calibration record has the method `verifier_platt`: a code rule selects the answer, and the number is the value of the read-out head D1 for that answer.
- `calibrations[].basis` comes from 3 forms of parameters: `dev_blocks` and `dev_correct`; `blocks` and `precision` (agreed = precision times blocks, rounded); `dev_correct` and `dev_documents` with no block count (`n` is null).
- `checks[]`: a check that `validation.json` does not hold has the state `skipped` with the reason `earlier_check_failed` (the validator stops after a failed parse check). Before, the state was `failed`.
- The notice `shacl_not_run` comes only if the check `C10_shacl` did not run. New notice `rdfxml_not_readable` (`params.n`): the parse check of `validation.json` did not read `n` RDF/XML files.
- `check_view.py` after these changes: passed (in `make test`).

## Changes of the correction step (13.10.2026)

- Notes of the labels. The labels file holds, for each label, an English working text of the converter (`label_note`). The view does not pass it on as it is. A note that the function knows becomes `labels[].note_code` with `labels[].note_params`; then `labels[].note` is `null`. The page needs one text for each code in its strings file (proposed keys `note.<code>`). A note that the function does not know goes to `labels[].note` after a filter that removes paths, document numbers and working words of the project (mark `[…]`); it is for the technical details only, as "note of the converter (English)".

  | Code | Note of the converter | `note_params` |
  |---|---|---|
  | `switch_between_blocks` | "switch between block B4 and block B5" | `before`, `after` (block ids) |
  | `value_derivation` | "derivation copied_from_metadata (ValueRecord of the provenance side file)" | `derivation` (the value of the provenance file) |
  | `wording_copy` | "verbatim copy of the atoms of the author block (check E19); the text changes are in the TextBlockRecord" (2 forms) | none |
  | `final_check` | "final check R2 (frozen head H): the document holds a response of the executive; it agrees with the block path" (2 forms). The converter writes the words "holds a response" also for the value `no`; the page must use the value of the label and `agrees`. | `agrees` (boolean) |
  | `unsure_final_check_differs` | "unsure: the final check R2 does not agree with the block path" | none |

  Measured (labels with a code): `s-26171` 19 (`final_check` 1, `value_derivation` 17, `wording_copy` 1); `s-879163` 17 (1, 14, 2); `s-714840` 9 (1, 8, 0); `s-26171-rules` 18 (`value_derivation` 17, `wording_copy` 1); `s-879163-rules` 22 (17, 5); `s-714840-rules` 12 (11, 1); the upload record of the synthetic PDF, the two modes: 4 (`switch_between_blocks` 1, `value_derivation` 1, `wording_copy` 2). No note of these 8 records is unknown; `unsure_final_check_differs` does not occur in them.
- `calibrations[].reference_code` replaces `calibrations[].reference_source`. The text of the calibration record names folders of the project and document numbers. Codes: `model_labels_not_human_checked` (reference labels of the development documents, made by a language model), `other`, `null`. `calibrations[].note` is the text of the record, not changed; the pages do not show it.
- `origin: new`: `run.in_sample` and each `labels[].in_sample` are `null` (three states: true, false, null = not known). The notice code `outside_fit_population` is replaced by `not_a_sample`.
- `check_view.py` has 2 new checks for each record (`notes`; `origin_new` for the floor record) and 1 check with no record (`note_filter`). It gives `export.json` of the sample folder to the function, so the view of `s-26171` equals the example in each key of the rule.
- `contract/examples/view_26171.json` is made again by `contract/tools/make_example_view.py` (the tool has the new fields and the argument `--export`). The view function and the tool give equal data for `s-26171` under the rule of gate G4.

## Values that are read from the PDF (13.10.2026)

The view has the version 3 (`CONTRACT.md` chapter 16.3). The function knows the record form by the key `schema` of `manifest.json`.

1. New keys at the top: `head_values`, `values[]` and `slots[]`. For the earlier record form the two lists are empty.
2. A label of the kind `pdf_value` has no options. Its lines come from the key `pdf_evidence` of the provenance file.
3. `values[].spans[]` gives the part of each line that holds the value (keys `match_start` and `match_end` of the provenance file).
4. `slots[].export_has_value` comes from the gap record of the label file. The value of the export is not in the view.
5. The function gives no view of a record with stand-in numbers (`ViewError`). Each value has its stored decimal and its stored word.
6. The optional key `values` of `run_info` is `pdf`, `off` or `held` (the hold list is empty). With no such key the function reads the state from the record form.
7. `check_view.py` reads the 4 stored records of the earlier form. It also validates each example view of `contract/examples/`.
8. The view of a record of the new form is checked by `worker/check_values.py` and by `contract/tools/gate_values.py`.

## Corrections after the skeptic check of the values (13.10.2026)

Contract: `CONTRACT.md` chapter 17.

1. `values[]` has one entry for each label of the kind `pdf_value`: the values of the record (label id `pdf-<field>`, `written` true) and the weak candidates (label id `candidate-<field>`, `written` false, no `instance_path`). The lines of a weak candidate come from its span and the atoms file.
2. New keys of `values[]`: `written`, `value_form` (`printed`, `list_value`, `iso_day`), `differs_from_printed`, `comparison_value`, `tier_probability`, `probability_source` (`all_folds`, `without_own_fold`), `export_match` (`exact`, `after_normalisation`).
3. New keys of `head_values`: `document_kind` (manifest key `s1_rule_role`), `submitted_text`, `floor` (`threshold`, `not_written`).
4. New notice `weak_candidates`. The notice `values_not_measured` does not exist any more.
5. New note codes of a label: `comparison_value`, `weak_candidate`, `fold_value`.
6. `checks[]` has the ids `C20_value_follows_from_wording` and `C21_floor`.
7. `contract/tools/validate_view.py` has link checks for a weak candidate (slot reason, no path, tier probability below the floor, not a head value of the record).

## The cascade of a record (13.10.2026)

`../CONTRACT.md` chapter 18.4 has the keys. Changes of `site_view.py`:

1. New key `head_values.cascade` (function `_cascade`). It holds the kind of the document and the source of the kind. It holds the affair type of stage 1, the 2 steps and the 7 entries with their states. It holds the text slot of each step and 2 counts. It comes from the manifest key `cascade`, from `values[]` and from `slots[]`.
2. `head_values.document_kind` is the kind of the cascade. `head_values.submitted_text` is removed. New key `head_values.addressee_candidates`.
3. `values[]`: new keys `candidate` (null, `weak`, `addressee`) and `in_sample`. `probability_source` is `all_folds`, `no_unit` or null. The function refuses a record with a fold value as the source of a probability.
4. `slots[]`: new keys `result` (`not_searched` or null), `kind`, `cascade_rules`.
5. Note codes of a label: `addressee_candidate` is new, `fold_value` is removed. Notice codes: `cascade_selection` and `addressee_candidate` are new.
6. Checks: `C22_values_from_the_readers` is the 12th id of `VALUE_CHECKS`.
7. The function raises `ViewError` in 4 cases. The manifest has no cascade. The kind is not one of the 7 kinds. The selection of the cascade and the state of a slot do not agree. A candidate of a slot that is not searched has not the mark of an addressed body.

## Rule V5, the reason `reader_scope` and the signs of a response (13.10.2026)

`../CONTRACT.md` chapter 19.3 has the keys. Changes of `site_view.py`:

1. `head_values.cascade.kind_from` has the new value `rule_v5`. New key `kind_facts`: the 2 facts of rule V5 for a document with no decision of the rule chain.
2. New entry state `reader_scope`: the slot has the state `not_found_in_pdf` and the reason `reader_scope`. The function does not stop for such a record.
3. `head_values.cascade.texts[]`: new key `not_written`.
4. New key `head_values.response_signs` and new notice code `response_signs`. The optional key `response_signs` of `run_info` gives the tiers of the responder candidates.
5. The function raises `ViewError` if the kind source of the manifest and the facts of rule V5 do not agree.

## Rule V5 made narrower (13.10.2026)

`../CONTRACT.md` chapter 21.2 has the keys. Changes of `site_view.py`:

1. `head_values.cascade.kind_facts.response_cue` is true only for the responder tier `rsp_response_cue`.
2. New key `kind_facts.response_sign`: true for each other responder tier that is not the tier of an addressed body and not the tier `rsp_response_text`.

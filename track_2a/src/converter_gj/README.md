# The reader of the values from the PDF

This folder holds the code of the method that the technical report measures. A PDF of a Swiss parliament goes in. Each head value of the record (up to 7) is read from the PDF and has a probability. A value from the rules also has a page and a text span. Identifiers and constants of the record have no probability. The export is the reference of the measurement. No export value goes into a record.

Status: EXCEPTION, NOT RELEASED. No human examined the code or this file.

## How to use this folder

- This folder is for a reader of the code. To run the rule readers, use the app: `make run-native` or `make run` in `track_2a/` (`../../app/`). The app does not run the combined reader or the value heads.
- Line 1 of each file is the licence line. `../../SOURCES.json` gives the source file, its SHA-256 and each edit of a line.
- The code compares the SHA-256 of some files with stored records. A copy with a licence line does not agree with these records. Thus a run from this folder does not pass these comparisons.
- `../../app/layout/src/` holds the files that the app runs. They are byte-equal to the files of the private project, except 3 files with a recorded edit.

## Files

| File | Part of the method |
|---|---|
| `m11_rules_pdf.py` | the rule chain of the block roles (`m10_rules.py`), run on the PDF alone with empty export fields |
| `m11_values_base.py` | the common interface of the value rules |
| `m11_values_type_number.py`, `m11_values_title.py`, `m11_values_dates_responder.py` | the rules for the affair type and number, the title, the 2 dates and the responder |
| `m11_value_norm.py` | the normalisation of a value before the comparison with the export |
| `m11_cascade.py`, `m11_cascade.yaml` | the cascade over eCH-0295: which entries a kind of document can have |
| `m11_values_cascade.py`, `m11_values_combined.py` | the cascade reader and the combined reader (rules and Apertus heads) |
| `m11_value_cal.py` | the measurement of the values and the calibration of their probability |
| `m11_prompts_values.py` | the questions Q0, Q1 and Q2 to Apertus (folder `../prompts/gj_values_v1_de/`) |
| `m11_writer.py`, `m11_label_schema.yaml` | the writer of the eCH-0295 record |
| `m11_validate.py` | the validator of a record |
| `m11_value_reference.py` | the reference table from the export for the development documents, for the measurement only |
| `m10_*.py`, `m10_label_schema.yaml`, `m03_ech_export_schema.yaml` | the block roles: rule chain, Apertus prompts and states, calibration. Also the document access, the guard of the document sets, the RDF writer. |

## Imports from other folders

The code imports these modules by their names. Their copies have the same source SHA-256 as the files of the private project.

| Folder | Modules |
|---|---|
| `../converter/` | `m02_ech_regeln`, `m03_atome`, `m03_gold_record`, `m03_iso_hilfe`, `m03_iso_jev`, `m03_iso_mass`, `m03_iso_paths`, `m03_iso_v4`, `m03_isolierung_taxonomie`, `m03_iter2_aufgabe`, `m03_ladder`, `m03_lehrer_vorgaben`, `m03_sub_assemble`, `m03_sub_common`, `m03_sub_s1_role`, `m03_sub_s2_switch`, `m03_sub_s5_type`, `m04_iso_cscs`, `m05_iso_runner`, `m06_converter`, `m06_ech_ausgabe`, and the file `m06_ech_profil.yaml` |
| `../apertus_head/` | `m02_dokumente_extrakt`, `m02_dokumente_profil`, `m04_kern`, `m05_cls_apertus`, `m05_cls_data` |

Not in this folder: `m11_values_sponsor.py`, the rule for the first author. This rule is only in `../../app/layout/src/`. The copy tool cannot make the edit that its copy here needs.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 14.10.2026. On 15.10.2026 an AI agent narrowed the sentence on the 7 head values after an audit. No human examined it.

# Worker of the ParlPDFeCH package

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file or its results.

Each value has one of three marks: measured, read or estimate. The measured values are from 13.10.2026 on one Mac (Apple silicon, macOS, Python 3.12.13, numpy 2.5.3, rdflib 7.6.0, linkml 1.11.1). No value is measured on Linux or in a container.

## Files

| File | Function |
|---|---|
| `serve_convert.py` | The worker. One process makes one conversion. Protocol: `CONTRACT.md` chapter 4. |
| `fresh.py` | Stage P0b. The conversion of a PDF that is not a sample, with code rules only (chapter "Stage P0b"). |
| `pdf_only.py` | Stage P0b. The record of a PDF with no export record: writer, RDF step, checks (`CONTRACT.md` chapter 10). |
| `states_provider.py` | Stage P0b. The interface of a states provider. Only the kind `none` exists. |
| `fresh_tables.json` | Stage P0b. The tables of the rule chain with no row. `make_fresh_tables.py` makes the file. |
| `layout_files.json` | The list of the converter files that the three modes read: path, bytes, SHA-256, reason, modes. |
| `make_layout_list.py` | Build tool. It makes `layout_files.json` from three traced runs of the worker. |
| `layout.py` | Build tool. It copies the files of the list into `build/layout/` and checks each SHA-256. `--update` keeps a layout that is in use. |
| `make_samples.py` | Build tool. It writes `data/samples/<doc>/` and `data/samples/index.json`. |
| `check_worker.py` | Check script. It repeats the gate of the worker. |
| `check_fresh.py` | Check script of stage P0b. Fresh runs of the sample PDF files against the stored inputs, and cases with files that the script writes. |
| `requirements-slim.txt`, `imported-distributions.txt` | The Python packages of the worker and the measured list of the imported distributions. |

## What the worker does

1. It reads the sample index `data/samples/index.json`.
2. It makes a scratch root in the parent folder of `--out` (or in `PARLPDFECH_SCRATCH_DIR`). The scratch root holds copies of the converter files from the code layout (`PARLPDFECH_CODE_DIR`, default `build/layout`) and the stored inputs of the sample, each under its project path. The worker checks the SHA-256 of each copy.
3. It writes 5 small registry files for the run and gives the split guard one table in memory (chapter "Reduced tables").
4. It imports the converter from the scratch root and calls its functions. It changes no converter file.
5. It copies the 9 converter files to `--out`, calls the view function, writes `convert.json` and deletes the scratch root.

The converter takes the project root from the path of its code files. Thus the code must be a copy in the scratch root. A link to the layout is not sufficient.

Standard output holds only JSON lines. Each other print of the converter goes to standard error.

## Modes

| Worker mode | Decisions | Converter functions | Record folder in the scratch root |
|---|---|---|---|
| `auto` (a sample) | Candidate B1-S from the stored Apertus states of the sample | `worker_state`, `decisions_of`, `document_state` of `m10_fullrun2`; these call `b1s_decisions` of `m10_b1s` | `daten/gj/fullrun_b1s_dev/` |
| `rules` | Floor probabilities from the stored rule record; no Apertus state | `worker_state`, `valid_output` of `m10_fullrun`; `decide` of `m10_pipeline` with the mode `floor` | `daten/gj/package_rules/` |

Then, in the two modes: `write_one` of `m10_writer`, `convert_record` of `m10_rdf`, `validate_record` of `m10_validate`.

In the mode `auto` the worker uses the folder name of the reference run. The writer puts the project paths of its inputs into the output files. With the same folder name, the output files are equal to the files of the reference run except for the run time.

No model runs. The states of the samples were made before, in bf16 on a GPU (read in the package plan). The read-out heads and the sequence step run in numpy on the CPU.

## Stages

| Stage | A sample, mode `auto` | A sample, mode `rules` |
|---|---|---|
| `read_pdf` | reads the stored Docling output; origin `stored` | same |
| `lines` | reads the stored atoms and the stored block file; origin `stored` | same |
| `rules` | reads the stored rule record; origin `stored` | same, then the floor decisions |
| `apertus` | the decisions of B1-S from the stored states; origin `stored` | `skipped`, reason `mode_rules` |
| `write` | writer and RDF step; origin `new` | same |
| `check` | validator, copy of the record, view function; origin `new` | same |

The time to make the scratch root is not a stage. It is in `convert.json`, key `seconds.setup`.

## Commands

From the project folder, with the project Python:

```
uv run --offline --frozen --no-sync python package/worker/make_samples.py
uv run --offline --frozen --no-sync python package/worker/layout.py
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/serve_convert.py --sample 26171 --mode auto --out package/work/s-26171
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/check_worker.py
```

To make the file list again (after a change of the converter):

```
PARLPDFECH_TRACE=package/build/trace/trace_rules.json <python> package/worker/serve_convert.py --sample 26171 --mode rules --out package/build/trace/out_rules
PARLPDFECH_TRACE=package/build/trace/trace_auto.json  <python> package/worker/serve_convert.py --sample 26171 --mode auto  --out package/build/trace/out_auto
python package/worker/make_layout_list.py --trace package/build/trace/trace_rules.json package/build/trace/trace_auto.json
python package/worker/layout.py
```

Environment variables of the worker: `PARLPDFECH_CODE_DIR`, `PARLPDFECH_DATA_DIR`, `PARLPDFECH_VIEW_DIR`, `PARLPDFECH_PROFILE` (contract chapter 2.1), and `PARLPDFECH_SCRATCH_DIR`, `PARLPDFECH_TRACE`, `PARLPDFECH_KEEP_SCRATCH=1` (this file).

The Python of the worker needs numpy, scipy, PyYAML, rdflib 7.6.0 and linkml 1.11.1 (`requirements-slim.txt`; not tested with pip). Measured in the traced runs: the two modes import 53 distributions (`imported-distributions.txt`); Docling and torch are not among them.

## The code layout

Measured with two traced runs of sample 26171 and one traced fresh run (`layout_files.json`; 72 files, 11,391,029 bytes):

| Mode | Files | Bytes |
|---|---|---|
| 1, rules only | 32 | 1,412,999 |
| 2, stored Apertus states | 59 | 10,799,367 |
| 3, fresh conversion of a PDF that is not a sample | 45 | 2,026,544 |

Mode 3 adds 13 files to the list: 10 code files (`m10_convert`, `m03_docling_zerlegen`, `m05_cls_data`, `m10_rules`, `m05_iso_runner`, `m03_ladder`, `m03_sub_assemble`, `m03_sub_s1_role`, `m03_sub_s2_switch`, `m03_sub_s5_type`), the S1 prompt text (its SHA-256 is a self-check; the text is not sent), the ladder definitions and the identity record of the rule step. The numbers below are for the modes 1 and 2.

- 35 files are converter code and schemas in `src/` (28 for mode 1).
- 2 files are the eCH-0295 schema and the eCH-0292 common schema.
- 18 files are data of mode 2: the design freeze file, 9 files of the frozen design (2 read-out heads), 4 files of the B1-S design, the calibration file of the reference run, the R2 calibration records, and the 2 floor files (the 2 floor files are also data of mode 1).
- 4 files are the criteria text and its addenda B, C and D. The converter reads them only to compare their SHA-256.
- The largest file is `daten/gj/design_b1s/oof/b1s_oof.npz` (7,994,969 bytes). The converter reads it only to compare its SHA-256.

`build/layout/` is not tracked by git. Measured: 13 files of the layout hold a personal name or a home path (8 code files and 5 text files), and 30 files name the actor of a work step. The copies must stay byte-equal, because the converter compares their SHA-256. Their publication is a decision of the owner.

## The sample folder

`data/samples/<doc>/` holds 9 files: `docling.json`, `atoms.json`, `blocks.json`, `rules.json`, `export.json`, `states.npz` (byte-equal copies of the stored files), `r2.json` (the R2 entry of this document), `sample.json` (index entry, sets, the SHA-256 of each file) and `reference.json` (SHA-256 values, counts and run time of the reference run). Since 13.10.2026 the file `rules.json` is the rule file from the PDF alone (`daten/gj/rules_pdf/<doc>.json`). It names no export record.

Measured: the 3 sample folders have 3.0 MB. No PDF file is in the package.

The value `in_sample` of the index comes from the decisions file of the reference run: true if 1 or more block decisions or document decisions have `in_sample: true`. Measured: true for the 3 samples.

## Reduced tables

The converter reads tables that hold rows of all documents. The package does not hold them. The worker makes these forms for each run:

| Path in the scratch root | Form in the package | The project file holds |
|---|---|---|
| `daten/gj/sets.json` | the 5 set keys; a list holds only the id of the sample | the ids of all labelled documents |
| `daten/gj/docs_build.json` | one entry: the block file of the sample and its SHA-256 | the block files of 2,665 documents |
| `daten/gj/runs/m10_rules_run.json` | one entry: the rule file of the sample and its SHA-256 | the rule files of all documents |
| `daten/gj/labels_build.json` | no entry | the label files of the AI reference |
| the R2 value file | one entry: the R2 value of the sample | the values of 193 or 1,600 documents |
| guard table (memory only) | the parliament of the sample, role Training, split dev | split tables and the lists of protected test ids |

`make_samples.py` compares the SHA-256 of the block file and of the rule file with the run records of the project. Thus the SHA-256 check of the converter for the rule file uses the same value as in the project.

The split guard of the converter has no protecting function in the package: its table says only that the sample is a development document. The worker stops if the block file of a sample has another split than `dev`.

## Limits

- Stage P0a had no conversion of a PDF that is not a sample. Stage P0b adds it (chapter "Stage P0b"): `convert_fresh()` calls `fresh.py`. The profile `slim` refuses such a PDF with the code `not_in_package`.
- The worker does not read the PDF of a sample. A PDF whose SHA-256 is in the index uses the stored inputs.
- The samples are development documents. The read-out heads were fitted on them (data flag `in_sample`).
- Word counts for line-end hyphens. The wording function of the converter (`m03_gold_record.hyphen_vocab`) counts words in the atoms of all development documents. The package has only the atoms of the sample. Thus the counts come from the sample document only. Measured for the 3 samples: 3 line-end hyphen decisions (all in 26171), 0 decided by the word counts, and the eCH-0295 YAML file is byte-equal to the reference run. For another document this difference can change the text of a text block. `convert.json` key `hyphen_word_counts` gives the counts of each run.
- Check C10 (SHACL) has the state `skipped`: pyshacl is not in the environment.
- The mode `rules` has no stored record with the same writer version. Read: the stored floor records of the project were written with an earlier writer file. Measured for 26171: the eCH-0295 YAML file and the Turtle file of the mode `rules` have the SHA-256 of that stored floor record.
- The view function is another part (`view/site_view.py`). If the file is absent or the function fails, the record has no `view.json`, the stage `check` has the key `note` (`view_absent` or `view_failed`), and the exit code does not change.

## RDF/XML and characters that XML 1.0 cannot hold

Read in the run record of the reference run: 2 of 1,793 development documents are not valid, because check C2 fails. An atom text holds the control character U+0007. XML 1.0 cannot hold this character, so no XML parser reads the RDF/XML file. The TriG file parses.

The worker does not change the RDF step and does not change its files. New code in `serve_convert.py`:

- `xml10_forbidden(text)` gives the characters of a text that XML 1.0 cannot hold.
- `rdfxml_report()` reads each of the two RDF/XML files with an XML parser (expat) and searches the atoms and the export record for such characters.
- `convert.json` key `rdfxml`: `representable` (true or false), the state of each file, the atom ids and the code points, `reference_form` (the TriG file), and a note.

For such a document the record is written, `valid` is false and the exit code is 2. The TriG file is the reference form. No sample has such a character (measured: `representable` is true for the 3 samples). The check script tests the functions with a synthetic string and a synthetic record.

The view has the notice `rdfxml_not_readable` for this case (added in the examination step).

## Measured results of the gate (13.10.2026, `check_worker.py`, 76 checks, 76 passed, 49 s)

The tables of this chapter are the values of the first run of the check script. The last run (document and gate step, after the correction round): 82 of 82 checks passed, 59.2 s; `../STATE.md` chapter 2.

Mode `auto` against the reference run of candidate B1-S (`runs/run_1.json`):

| File | 714840 | 879163 | 26171 |
|---|---|---|---|
| decisions file | equal SHA-256 | equal SHA-256 | equal SHA-256 |
| `<doc>.ech.yaml` | equal SHA-256 | equal SHA-256 | equal SHA-256 |
| `<doc>.ech.ttl` | equal SHA-256 | equal SHA-256 | equal SHA-256 |
| `<doc>.labels.yaml` | different; equal SHA-256 after the replacement of the run time | same | same |
| `<doc>.provenance.yaml` | different; equal SHA-256 after the replacement of the run time | same | same |
| `<doc>.gesamt.trig` | different; equal SHA-256 after the replacement of the run time | same | same |
| `<doc>.gesamt.rdf.xml` | different; isomorphic to the reference file | same | same |
| `<doc>.ech.rdf.xml` | different; isomorphic to the reference file | same | same |

Causes of the differences (measured):

- Time stamp. The labels file and the provenance file each hold one run time; the TriG file holds two.
- RDF/XML. The RDF step writes the XML elements and the namespace declarations in another sequence in each run, also with an equal `PYTHONHASHSEED`. The blank node names are equal except 1 name in the file `gesamt.rdf.xml` (26171: 268 of 269 in common). No real difference: the graphs are isomorphic (rdflib `to_isomorphic`), 1,182, 3,122 and 2,577 triples.
- The two run times of one record can differ by 1 s (measured in one run: the labels file and the provenance file had different seconds). A comparison must replace the two values.

Counts, checks C1 to C9 and conformance are equal to the reference for the 3 samples.

| Sample | Mode | Valid | Labels | certain | unsure | Seconds in the worker | Seconds of the process |
|---|---|---|---|---|---|---|---|
| 714840 | auto | yes | 18 | 6 | 4 | 2.81 | 3.20 |
| 879163 | auto | yes | 42 | 12 | 14 | 3.37 | 3.79 |
| 26171 | auto | yes | 33 | 9 | 6 | 3.80 | 4.22 |
| 714840 | rules | yes | 21 | 0 | 9 | 2.75 | 3.13 |
| 879163 | rules | yes | 47 | 0 | 25 | 3.36 | 3.76 |
| 26171 | rules | yes | 32 | 0 | 14 | 3.09 | 3.48 |

- One run of each row. About 2 s of each run are the first import of linkml and rdflib and the compile of the LinkML schemas in the stage `write`.
- Peak memory (`convert.json` key `resources.max_rss_bytes`): 232 to 243 MB in the mode `auto`. `ru_maxrss` is in bytes on macOS and in kilobytes on Linux; the worker converts by platform. The Linux branch is not measured.
- The mode `rules` has no label with the source `apertus_head` or `code_step`.

Trace of one run of each mode (26171): no opened and no listed path in the project folders `src`, `daten`, `web`, `public`, `crisp-dm` and `quellen`; no subprocess; 1 network event: a bind to the loopback address `::1`, port 0, at the import of urllib3 (function `_has_ipv6`); no connect event and no address lookup.

## Stage P0b: a PDF that is not a sample (`fresh.py`, `pdf_only.py`)

All values of this chapter are measured on 13.10.2026 on one Mac (Apple silicon, macOS; docling 2.133.0, docling-parse 7.22.1, torch 2.14.1, ocrmac 1.0.1, pdftotext 26.04.0, pypdfium2 5.14.0), profile `native`, if not said differently. Nothing was run on Linux or in a container. One run of each row.

### What runs

`serve_convert.py --pdf FILE` with a SHA-256 that is not in the sample index calls `fresh.convert_fresh()`. No Apertus state is read and no model of Apertus runs. The modes `auto` and `rules` give the same labels; only the record id differs (`u-<16 hex>` and `u-<16 hex>-rules`).

| Stage | Step | Function of the converter copy in the code layout |
|---|---|---|
| `read_pdf` | PDF checks (new code, pypdfium2), scratch root, imports, Docling | `docling_main` of `m10_convert` (it calls `main` of `m03_docling_zerlegen`) |
| `lines` | atoms and block file | `atoms_of_docling` and `block_file` of `m10_convert` |
| `rules` | rule record, floor decisions | `check_identity_record` and `run_document` of `m10_rules`, `check_frozen_method` of `m05_iso_runner`, `load_floor` and `checked` of `m10_pipeline`, `floor_decisions` of `m10_cascade` |
| `apertus` | `skipped`; reason `not_in_package` (mode `auto`) or `mode_rules` | the states provider of the kind `none` |
| `write` | the three YAML files, the manifest, the 4 RDF files | `pdf_only.write_record`, `pdf_only.rdf_step` |
| `check` | checks C1 to C10, copy of the record, view function | `pdf_only.validate` with the functions of `m10_validate` |

The scratch root and the import of the converter modules are in the stage `read_pdf` (0.15 s in one run, `convert.json` key `seconds.setup`). Thus the stage `rules` shows 0.003 to 0.006 s.

PDF checks, in this sequence, before Docling:

| Case | Line `failed` | Exit code |
|---|---|---|
| profile `slim` | `not_in_package` | 3 |
| a document number is given (`--doc-id`) | `doc_id_unknown`; `pdf_differs_from_doc_id` if the number is a sample | 3 |
| no PDF mark in the first 1024 bytes | `bad_request`, field `file` (the server refuses such a file before with `not_pdf`) | 3 |
| pypdfium2 does not open the file, or the file has 0 pages | `pdf_unreadable` | 3 |
| the file needs a password | `protected_pdf` | 3 |
| more pages than `PARLPDFECH_MAX_PAGES` | `too_long` with `pages` and `max_pages` | 3 |
| no page has a text layer and no OCR engine runs | `no_text_layer` | 3 |
| Docling gives no block with text (after OCR, if OCR runs) | `no_text_layer` | 3 |

A PDF that does not open or has 0 pages gives the error code `pdf_unreadable` (exit code 3). The examination step added this code to `contract/errors.json`; before, the branch used `converter_stopped` with the note `pdf_unreadable`.

### Profiles and OCR

| Profile | OCR | Docling call | What differs from the stored settings |
|---|---|---|---|
| `native` on macOS with the package `ocrmac` | Apple OCR (`ocr: apple`) | `docling_main` of `m10_convert`, not changed: `--ocr auto --geraet auto`, 4 threads, accurate tables, cell matching on | nothing (measured: `settings_equal_to_stored` and `tools_equal_to_stored` are `equal` in `convert.json`) |
| `native` with no `ocrmac`, and `full` | none (`ocr: none`) | `fresh.docling_no_ocr`: the same function `main` with `--ocr aus` | no OCR; in the profile `full` also `--geraet cpu`, Poppler of Debian, the CPU build of torch |
| `slim` | not applicable | none | the PDF is refused |

`HF_HUB_OFFLINE` is set to `1` if it has no value. In the profile `native` Docling reads its two models from the model cache of the user account (the folder that the project uses). In the profile `full` the path comes from `DOCLING_ARTIFACTS_PATH`; the branch stops with the note `docling_models` if the variable has no value. The pdftotext command is the one that the search path gives, else `/usr/bin/pdftotext`, `/opt/homebrew/bin/pdftotext` or `/usr/local/bin/pdftotext`.

`PARLPDFECH_FRESH_OCR=none` and `PARLPDFECH_FRESH_DEVICE=cpu` give the two arguments of the profile `full` in the profile `native` (a measurement aid).

### Reduced tables of the rule chain

The rule modules read project tables at import: the document groups, the pool, the triage table, the split table, 6 role files of the S1 step, 2 answer files of the ladder and the folder of the review records. The package holds none of these rows. `fresh_tables.json` holds each table with no row (the header line of a CSV file, an empty document map). The S1 selection file keeps its 3 selection keys; `make_fresh_tables.py` reads them and the 4 header lines from the project files. The worker writes these forms into the scratch root.

Consequences:

- The guards of the rule chain have no function in the package. The split guard of `m10_pipeline.decide` is not called: it refuses each id that is not a document number. The branch calls `floor_decisions` and `checked` directly.
- The S1 rule gets empty export fields (`category_de`, `category_harmonized`, `name_klasse`) and the admission kind `loader`. Read: the rule ids P2 and R1 read export fields. For the 3 samples the S1 result is equal with and without the fields (measured, table below).
- One converter file (`m03_sub_assemble.py`) puts a fixed folder of its author at the start of the module search path. `fresh.LayoutFinder` makes each converter module come from the scratch root, and the branch stops with the note `layout` if one module is from another folder. Measured in the traced run: 0 project paths opened (code or data); the Python packages of the environment are the only files outside the package.
- The word counts for line-end hyphens come from the document only (same limit as in stage P0a).

### The record (`pdf_only.py`): the earlier record form (`PARLPDFECH_VALUES=off`)

This chapter describes the earlier record form. The record form of now has one affair for each PDF (last chapters of this file).

The writer of the converter was not used. Measured: `m10_writer.write_one` stops for the document id `local` ("a document id has digits only"), and `m10_writer.build` with a minimal export record (`doc.id`, no affair) stops in the metadata check with a missing key. Read: the writer makes the source IRI `https://api.openparldata.ch/v1/docs/<id>` and puts the path of the export record into the label file and the provenance file. A number and an export record that do not exist give an IRI and texts that are not true. Thus `pdf_only.py` is new code. It calls the converter functions that apply without a change (the list is in the file head): the input checks, the author blocks, the wording and check E19, the YAML writer, `layout_record`, `to_graph`, `trig_text`, and the check functions of `m10_validate`.

The form of the record is `CONTRACT.md` chapter 10. In short, for the earlier record form (`PARLPDFECH_VALUES=off`): document IRI `urn:parlpdfech:local:sha256:<64 hex>`; the eCH-0295 part is one Container with no affair; each text block is a TextBlockRecord of the provenance graph; conformance `pdf_only_with_recorded_gaps`; `manifest.json` key `recorded_gaps`.

The LinkML dumper reads an IRI with no `//` as a CURIE and stops for the prefix `urn`. `pdf_only.accept_urn` adds the prefix `urn` to the prefix map of the three schema views in memory. No schema file changes.

Search for invented values (`check_fresh.py`, function `placeholder_search`, 11 files of each record): 0 files with the document number of the sample as a number of its own, 0 with an IRI of the export API, 0 with an export folder, 0 with an affair IRI, 0 with a home folder. The values of this sentence are from the run before the correction step. After the correction step the search has more words and takes out one text only (the name of the input file in `convert.json`): see the chapter "Changes of the correction step".

### Measured: the 3 sample PDF files as PDFs that are not in the package

Run with an empty sample index (`check_fresh.py`, variant `stored`). Each run: exit code 0, `valid` true, 9 of 10 checks passed, C10 skipped.

| | 26171 | 879163 | 714840 |
|---|---|---|---|
| Seconds of the process | 10.13 | 11.28 | 10.00 |
| Stage `read_pdf` (of it: Docling start; Docling convert) | 6.60 (5.71; 0.65) | 7.51 (5.74; 1.48) | 6.72 (5.75; 0.71) |
| Stage `lines` | 0.054 | 0.053 | 0.049 |
| Stage `rules` | 0.005 | 0.005 | 0.004 |
| Stage `write` | 1.90 | 1.94 | 1.73 |
| Stage `check` | 0.76 | 0.94 | 0.64 |
| Pages; lines; blocks | 1; 36; 13 | 1; 45; 24 | 1; 11; 8 |
| Text source of the page | text layer | OCR | mixed |
| Labels (rule; constant; copy) | 16 (14; 1; 1) | 31 (25; 1; 5) | 11 (9; 1; 1) |
| Labels with a probability: certain; unsure | 0; 14 | 0; 25 | 0; 9 |
| Text blocks | 1 | 5 | 1 |
| Statements (eCH; provenance; atoms; labels) | 2,037 (1; 611; 684; 741) | 3,063 (1; 777; 910; 1,375) | 1,119 (1; 195; 240; 683) |

Peak memory of the process (first run of the script): 1,211, 1,288 and 1,196 MB.

Equality with the stored inputs of the same sample (`data/samples/<doc>/`) and with the record of the mode `rules` of the same sample (made in the same script run from the stored inputs):

| Comparison | 26171 | 879163 | 714840 |
|---|---|---|---|
| Docling settings and tool versions | equal | equal | equal |
| Docling blocks equal in text, label, page, span, frame and text source | 13 of 13 | 24 of 24 | 8 of 8 |
| Whole text | equal (2,555 characters) | equal (2,327) | equal (342) |
| Lines (atoms) equal in id, text, span, page, line frame, features | 36 of 36 | 45 of 45 | 11 of 11 |
| Block file (without `doc_id`, `split`, `parliament`, `source_files`) | equal | equal | equal |
| Rule record: keys `document`, `blocks`, `by_d1`, `atoms` | equal | equal | equal |
| S1 rule role and rule id (fresh: no export fields) | proposal, P1; equal | response, A2; equal | other, O1; equal |
| Labels with a probability: equal in option, probability, all option probabilities, value status, calibration id, tier, page, span | 14 of 14 | 25 of 25 | 9 of 9 |
| Text blocks: equal in text type, blocks and text | 1 of 1 | 5 of 5 | 1 of 1 |

Different by design: `in_sample` (fresh: no label has the slot, see the chapter "Changes of the correction step"; sample record: true), the IRIs, the head values (the sample record has 17, 17 and 11 labels from the export and from constants; the fresh record has 1 constant label), the place of the text (sample record: TextBlock of the eCH-0295 record; fresh record: TextBlockRecord).

The same script with the two arguments of the profile `full` on this host (variant `full_settings`: no OCR, device `cpu`; the tools are the tools of the Mac). Each run: `valid` true.

| Comparison | 26171 | 879163 | 714840 |
|---|---|---|---|
| Blocks (fresh; stored) | 13; 13 | 23; 24 | 7; 8 |
| Block entries of the block file that are equal | 13 of 13 | 4 of 24 | 6 of 8 |
| Lines (fresh; stored) | 36; 36 | 46; 45 | 10; 11 |
| Whole text, characters (fresh; stored) | 2,555; 2,555 | 2,298; 2,327 | 330; 342 |
| Labels with a probability that are equal | 14 of 14 | 4 of 25 | 6 of 9 |
| Cause | no difference | the stored text of the page is all from OCR; with no OCR the text layer gives other lines | 1 block of the stored output is from OCR |

Thus 1 of 3 block files is equal with no OCR. This is a measurement on macOS, not in the image. Poppler of Debian and torch on a Linux CPU are not measured.

### Measured: files that the check script writes

| File | How it is made | Result |
|---|---|---|
| `text_layer.pdf` (1,789 bytes, 1 page, 13 lines) | PDF 1.4 written by hand in `check_fresh.py`: Helvetica, WinAnsi encoding, 13 invented German lines (a question part and an answer part) | `done`, `valid` true, 9.8 s; 9 blocks, 13 lines, 14 labels; D1 "both" 0.6795; 6 blocks submitted text 0.3043 (tier `s2_start_sponsor_evidence`); 3 blocks response 0.7844 (tier `s2_switch:answer_label`); 1 switch label 0.5; 2 text blocks; 1,307 statements (measured through the server in the gate run of `STATE.md` chapter 10.4; earlier states of the record gave 1,322 and then 1,311: the statements `in_sample` of the labels and of the 4 calibration records are gone) |
| `broken.pdf` (55 bytes) | the PDF mark and one text line | `pdf_unreadable`, exit code 3 (after the examination step; before: `converter_stopped`, exit code 4, 0.07 s) |
| `zero_pages.pdf` (356 bytes) | written by hand, page tree with 0 pages | `pdf_unreadable`, exit code 3 |
| `too_long.pdf` (26 pages) | written by hand | `too_long` with `pages` 26, `max_pages` 25, exit code 3, 0.06 s |
| `picture_only.pdf` (882 bytes) | written by hand: one page that is one grey picture (a bar pattern, no letters) | profile `full` (the PDF check only): `no_text_layer`, exit code 3, 0.06 s. Profile `native`: `no_text_layer` after Docling with Apple OCR (7.0 s): no block with text |
| `protected.pdf` (3,253 bytes) | Ghostscript 10.05.1 (`-sUserPassword`) from `text_layer.pdf`; not a part of the script | `protected_pdf`, exit code 3, 0.03 s |

Not made: a scan with letters (a picture of a text). Thus the path "Apple OCR reads a page with no text layer of a new PDF" is measured only through sample 879163, whose stored text is all from OCR.

### Commands

From the project folder, with the Python of the project:

```
python package/worker/make_fresh_tables.py
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/serve_convert.py --pdf FILE --mode auto --out DIR
uv run --offline --frozen --no-sync --with linkml==1.11.1 python package/worker/check_fresh.py --pdf-dir DIR [--variant full_settings]
```

To make the layout list again: one traced run of each mode (the third one is `--pdf FILE` with an empty sample index and `PARLPDFECH_TRACE`), then `make_layout_list.py --trace` with the 3 trace files, then `layout.py` (with `--update` if a server uses the layout).

### Limits of stage P0b

- Nothing ran on Linux. The profile `full` is code that was read and, for its two Docling arguments, run on macOS.
- The probabilities of an own PDF were not checked on other documents. The floor probabilities come from development documents with an export record. The record does not say if the PDF is a development document: the package cannot know it. No label has the slot `in_sample`, `manifest.json` has `development_document: null`, the view has `in_sample: null` and the notices `not_a_sample` and `not_examined_pipeline`.
- Earlier record form (`PARLPDFECH_VALUES=off`) only: the record is not a full eCH-0295 record: no affair, no title, no date. In the two record forms a document number is refused (`doc_id_unknown`): the package holds export records for the samples only.
- A page with pictures only and a PDF with a password are refused. A PDF with a damaged cross-reference table that pypdfium2 repairs is converted; this case is not measured.
- The time of one run is about 10 s on this Mac for 1 page; 5.7 s of it is the start of Docling in each process. A PDF with many pages is not measured in this branch (the plan measured 36 s for 6 pages with the project command).
- Peak memory is 1.2 to 1.3 GB. The memory limit of a container is not set against this value.

## The states provider (interface only)

`states_provider.py` names what a later stage needs to add Apertus for an own PDF with no change of the HTTP API. Kinds: `none` (the only one that exists), `stored`, `remote`. `provider("stored")` and `provider("remote")` stop with `NotImplementedError`. No model starts.

A provider gets the block file of the document and its SHA-256. It must:

1. build the prompt item as `m10_prompts` of the converter does (template `r2_v1_de`): one prefix (the chat template text with one line `[B<n> | S.<page> | <Docling label>] <block text>` for each Docling block) and the suffixes `D1`, then `B<n>` for each block;
2. run Apertus-v1.5-8B in bf16: token ids = tokens(prefix) + tokens(suffix) with no added special token, one prefill of the prefix, one forward pass for each suffix, and read the residual state after decoder layer k at the last suffix token (a hook on the layer, as `m10_vm_states` does);
3. return one file `<doc>.npz` in the form of `m10_vm_states` (interface 6): `suffix_ids` (`D1`, `B1` to `Bn`), `layers` (int16; layer 20 must be one of them, because the read-out heads of the frozen design read layer 20), `states` (float16, `[n_suffix, n_layers, hidden]`, finite), `letter_logprobs`, the token counts, the SHA-256 values of the texts and of the token ids, the template id, the model name and fingerprint, the dtype.

The worker of a later stage checks the file (function `read_states` of the design module), calls the decision function of the candidate in place of the floor decisions, and writes the kind of the provider into `convert.json` (key `fresh.states_provider`, today `{"kind": "none"}`). The R2 value needs a second request of the same kind (another prompt, layer 16). Not examined: a read-out head on a document with no export record, and a states file of another computer.

## Changes of the examination step (13.10.2026)

Each point is measured on one Mac in this step.

- Compiled files. `layout.py` records the SHA-256 of each compiled Python file in `layout_manifest.json` (key `compiled`, 42 files). The worker copies a compiled file into the scratch root only if it has this SHA-256 (`copy_compiled` in `serve_convert.py`, also used by `fresh.py`). Measured: a compiled file of `m10_guard.py` that was replaced after the build (same header, other code) was not run; the log has the line "not the file of the layout build; not used"; the record was valid; `layout.py --check` names the file under `different_compiled`.
- Checks that did not run. The validator stops after a failed parse check. `convert.json` key `checks` then has `null` for the later checks, and the stage event of `check` counts them under `skipped`. Before, they counted as failed.
- Paths in `validation.json`. A parse error text of the validator holds the absolute path of the scratch root. The worker removes the text of the scratch root from `validation.json` after the copy (`relative_paths`); `convert.json` key `validation_paths_made_relative` has the number of places. No other byte of a converter file changes. A record with no such path is not written again (0 for the 6 sample records).
- Measured with a synthetic copy of sample 26171 that holds one character U+0007 in a line (written by the examiner of the data part, read from its scratch folder): exit code 2, `valid` false; stage `check` counts `{passed 2, total 10, skipped 7}`; the view has `C3_isomorphism` to `C9_e19` as `skipped` with the reason `earlier_check_failed` and the notice `rdfxml_not_readable` with `n` 2; `validation.json` holds no absolute path (2 places made relative); the view is valid against the schema.
- The export record goes into the inputs folder of the view (`export.json`), so that the view can give the name of the body.
- `pdf_unreadable` is a refusal code (exit code 3), see above.
- `check_worker.py` with `--reference-dir` and `--sample-pdf` of sample 26171: 76 of 76 checks passed, 53.1 s. `check_fresh.py` (variant `stored`): see `../STATE.md` chapter 2.
- Not changed in that step: the hyphen word counts (limit of chapter "Limits"). The write into the home folder (finding X2-09) is corrected in the next chapter.

## Changes of the correction step (13.10.2026)

Each point is measured on one Mac in this step, each value from one run.

- A record of a PDF that is not a sample holds no document number of another document and no reference text of the project. The calibration file of the code layout has, in each record, the text `reference_source` with 3 document numbers and 2 folder names of the project. `pdf_only.py` writes the calibration records with the text `REFERENCE_TEXT` of that file in this slot ("reference labels of the development documents, made by a language model and not checked by a human"); `manifest.json` key `calibration_reference_source` records the replacement. The calibration file itself is a byte-equal copy and is not changed. The records of the SAMPLES are the bytes of the converter: their label file, TriG file and RDF/XML file keep the text of the converter (in the mode `rules` with the 3 document numbers). The view of each record holds a code in place of the text (`calibrations[].reference_code`).
- A record of a PDF that is not a sample does not say if the PDF is a development document. The package knows the SHA-256 of its 3 samples and nothing about other documents. No label has the slot `in_sample` (the slot is optional in the label schema; the checks C1 and C7/C8 pass without it). `manifest.json`: `sample_of_the_package: false`, `development_document: null`, `development_document_note`. `convert.json` key `fresh`: the same two keys and a changed text `not_measured`. The decisions file in the scratch root holds `in_sample: false` (the form of the converter function `floor_decisions`); it is not a file of the record.
- `manifest.json` of such a record says more: `apertus: "none"` with `apertus_note`, `probabilities_checked_on_other_documents: false` with `probabilities_note`.
- Nothing is written into the home folder. Cause (traced): the import of `linkml_runtime` imports `prefixmaps`, `curies` and `pystow`; `pystow` makes its data folder and one `README.md` at import, by default `.data` in the home folder. The worker sets `PYSTOW_HOME` and `TMPDIR` to folders below the scratch folder of the job before the first import of a converter file, of Docling or of torch (`keep_home_clean` in `serve_convert.py`). The scratch folder is deleted at the end of the job. Measured with `HOME` = an empty folder and an audit hook for each write of the process: sample 26171 in the two modes and a synthetic PDF as an own PDF: 0 files in the home folder and 0 writes outside the folder of `--out` and the scratch folder. Before the change the fresh run made 2 folders and 1 file in the system folder for temporary files (one folder name holds the name of the user account). Not covered by the audit hook: writes of child processes (`pdftotext`) and of system services (Apple OCR). In the profile `native` Docling reads its 2 models from the hub cache of the user (`HF_HOME`, default `.cache/huggingface` in the home folder); the hub library opens the two token files of that cache for reading. The worker sets `HF_HUB_OFFLINE=1`, `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` and `HF_HUB_DISABLE_TELEMETRY=1` if they are not set. `check_worker.py` has the new check group `H`.
- A record that cannot be written. The copy to `--out`, the write of `view.json` and the write of `convert.json` end with the note `out` (before: `validator`, the note of the stage). A parent folder of `--out` that cannot be made, or a scratch folder with no write permission, gives the note `out` (or `scratch` if `PARLPDFECH_SCRATCH_DIR` names another folder) with no stage line (before: `internal`). `check_worker.py` has the new check group `O` (2 checks).
- The module search path of the fresh branch. One converter file adds a fixed folder of its author with the name `src` to the module search path. `LayoutFinder` takes each such entry out before the next import reads it. Measured with the trace of a fresh run: 1 entry removed; 0 opened or listed paths below the project folders `src`, `daten`, `web`, `public`, `crisp-dm`, `quellen` (13,296 paths; before: 1 listed path). `convert.json` key `fresh.search_path_entries_removed` has the count.
- The D1 label of an own PDF comes from the S1 rule with empty export fields. The counts of its calibration record ("this rule gave this answer for n development documents") come from runs of the rule WITH export fields. The record states this in `convert.json` (`fresh.rules.export_fields`); the notice `not_examined_pipeline` covers it in general words.
- The pattern of the XML 1.0 character test is written with escapes only (the 3 raw characters U+D7FF, U+E000, U+FFFD are gone from the source line). Equal results for the code points U+0000 to U+2FFF and 11 edge code points (compared before the replacement); 2 new unit checks.
- `layout.py`: a build and `--update` remove compiled files that the manifest does not record; `--check` reports them (`not_recorded_compiled`, exit code 1). Measured: 42 files of another Python version (cpython-313) found and removed; 42 recorded files stay; the SHA-256 of the manifest is not changed.
- `check_fresh.py`: the search has the document numbers of the 3 samples and each 5 to 7 digit number of the reference texts of the calibration files (5 numbers), the words of the reference text, and takes out only the name of the input file. A hit, a label with the slot `in_sample` or a view that says `in_sample` true or false now changes the exit code.
- Results of this step: `check_worker.py --reference-dir <reference run> --sample-pdf <PDF of 26171>`: 82 of 82 checks passed, 58.8 s. `check_fresh.py --pdf-dir <folder of the 3 sample PDF files>` (variant `stored`): each run as expected; the 3 sample PDF files as PDFs that are not in the package: 0 hits in the 11 files of each record, labels with a probability equal to the rules-mode record 14 of 14, 25 of 25, 9 of 9, blocks equal 13 of 13, 24 of 24, 8 of 8. The variant `full_settings` was not run.
- Not changed: `/api/health` does not test that the states file of a sample exists (finding X2-14 point 5); the sample data (`data/samples/`) with the internal paths in `sample.json` (finding V-14) and the facts of findings X2-12 and X2-13: they are decisions of the owner.

## The record with values that are read from the PDF (13.10.2026)

The record form of now is in `CONTRACT.md` chapter 16. `STATE.md` chapter 11 has what was run. The chapters above describe the earlier record form, which runs with `PARLPDFECH_VALUES=off`.

| File | Function |
|---|---|
| `values_record.py` | The record path of now for a sample and for another PDF: the value readers, `m11_writer` and `m11_validate` of the code layout. It also holds the switch and the choice of the calibration file. |
| `values_hold.json` | The samples that keep the earlier record form (document number and SHA-256 of the PDF). The list is empty since 13.10.2026. |
| `layout_add.py` | Build tool. `--values` puts the 10 files of the values and the calibration file into `layout_files.json` with their SHA-256 of now. |
| `check_values.py` | Check script of the record form of now (76 checks in the run of `STATE.md` chapter 11). |

1. The value readers get the block file and the rule file. They read no export record and no model state.
2. The export record of a sample goes to the writer for the cross-check only.
3. An error of one reader does not stop the conversion. The field gets the reason `reader_error`.
4. `check_worker.py` and `check_fresh.py` check the earlier record form. They start each worker with the switch off.
5. `check_fresh.py` writes 2 more synthetic PDF files: `with_values.pdf` and `no_type.pdf`.
6. After a change of an `m11` file of the project: `layout_add.py --values`, then `layout.py`, then `check_values.py`.
7. Replaced on 13.10.2026 (next chapter): the calibration file of the values is the measured file `daten/gj_values/calibration_open.json`. The layout holds no stand-in file.

## Corrections after the skeptic check of the values (13.10.2026)

`EXAMINATION.md` chapter 12 has the findings and the decisions. `STATE.md` chapter 12 has what was run.

1. REPLACED (next chapter). Earlier text: Calibration. `values_record.py` and `layout_add.py` use `daten/gj_values/calibration_open.json`. `layout_add.py --values` stops if that file is absent, and it removes the entry of the stand-in file. `values_record.calibration_file` stops if the layout has no such file. `summary` stops for a record with stand-in numbers.
2. Hold. `values_hold.json` has an empty list. The 3 samples get the record with values from the PDF in the two modes.
3. REPLACED (next chapter). Earlier text: Checks of the validator. `values_record.CHECK_IDS` has 19 ids: C1 to C9 and C11 to C21 (C7 and C8 are one id). C20 makes each value again from the wording at its span. C21 is the floor. `convert.json` key `checks` has these ids and `writer_check`.
4. `convert.json` key `values`: new keys `floor` (threshold, the fields that are not written, with tier and tier probability) and `author_rule`; `calibration.stand_in` is always false.
5. `check_fresh.py` writes 2 more synthetic PDF files: `head_author.pdf` (a head with type, number, title, author and date) and `body_only.pdf` (body text only).
6. `check_values.py` runs the 3 samples in the two modes, each one also with the switch off, one trace run and 5 synthetic PDF files: 193 checks in the run of `STATE.md` chapter 12.
7. `check_worker.py` and `check_fresh.py` run with `PARLPDFECH_VALUES=off` (they set it for each worker): they compare with the reference run of the earlier record form.

| Synthetic file | Record |
|---|---|
| `text_layer.pdf` | type, title, submission date, responder; gap: affair number |
| `with_values.pdf` | type, title, 2 dates, responder (`Stadtrates`, as printed); the number `2021/147` is a weak candidate (tier `number_type_cue`, 0.3909) and is not written; gap: affair number |
| `no_type.pdf` | no value; the heading is a weak candidate of the title (tier `weak_first_heading`, 0.1651); gaps: affair type, affair number |
| `head_author.pdf` | type `postulate` (printed `Postulat`), number `2023/88`, title, submission date `2023-06-12` (printed `12. Juni 2023`), first author `Regula Beispielmann`, responder `Stadtrat`; no gap, conformance `i95` |
| `body_only.pdf` | no value, no weak candidate; gaps: affair type, affair number |

## The cascade reader and the decisions D1 to D7 (13.10.2026)

This chapter changes the two chapters before it. `../CONTRACT.md` chapter 18 has the rules, `../EXAMINATION.md` chapter 13 the findings.

1. Reader. `values_record.py` (version `parlpdfech-values/0.3.0`) calls `m11_writer.read_values(block file, rule file, strict=False, kind="from_rule_chain")`. That is the cascade reader `m11_values_cascade.read_document`: the kind of the document selects which of the 7 values are searched. The kind comes from the rule chain (the rule role and the rule id of the rule file), for a sample and for an unknown PDF. `write_record` and `validate_record` get the same `kind`.
2. Layout. `layout_add.py --values` lists 14 paths: the writer, the validator, the cascade reader, `m11_cascade.py`, `m11_cascade.yaml`, the label schema, `m11_values_base.py`, the 4 rule modules of round 3, `m11_value_norm.py`, `m11_value_reference.py` and the calibration file. It removes the entries of the stand-in file and of `daten/gj_values/calibration_open.json`. The layout has 86 files, 53 compiled files.
3. Calibration. The calibration file of the product is `daten/gj_values/round3/calibration_dev_all.json`. Origin: Development documents of 44 parliaments that the rule authors read. The values on 8 parliaments before the authors read them are lower for the affair number and the submission date: see the numbers of `daten/gj_values/closed_table.md`. A last run on documents that nobody read is planned. SUPERSEDED (14.10.2026; `../STATE.md` chapter 18): the origin text of now names the one fixed run of 13.10.2026. `values_record.ORIGIN` holds this text; `write` stops if the path or the text of the writer differs.
4. Probability. The number of a value is `p_all_folds` of its rule tier, for every document. No fold value is read for it.
5. Checks of the validator. `values_record.CHECK_IDS` has 20 ids: C1 to C9 and C11 to C22. C22 runs the cascade reader again and compares value, span, tier and slot state of each field with the record.
6. `convert.json` key `values`: new keys `cascade` (`version`, `reader`, `kind`, `kind_from`, `affair_type`, `not_searched`), `calibration.origin` and `addressee_candidates`.
7. `check_fresh.py` writes one more synthetic file, `response_head.pdf` (a response whose head prints the type, the number, the author and the date of the proposal and whose last line prints the date of the decision of the executive). `check_values.py` uses it.

Run in this step (13.10.2026, one run each):

| Command | Result |
|---|---|
| `python package/worker/layout_add.py --values` | 4 paths added, 6 changed, 1 removed; 86 files, 14,955,796 bytes |
| `python package/worker/layout.py --update`, then the stale copy `build/layout/daten/gj_values/calibration_open.json` removed by hand | 10 files copied, 53 compiled files; `layout.py --check` (in `make test`): 86 files, 0 different |
| `python package/worker/check_values.py --work package/work/cascade/cv3 --ocr none` | 244 of 244 checks passed: the 3 samples in the two modes, each one with the switch off, one trace, 6 synthetic PDF files |
| `python package/worker/check_worker.py --work package/work/cascade/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed, 51.3 s (the earlier record form) |
| `python package/worker/check_fresh.py` | not run |

`make layout` was not run in this step: it removes the layout folder first, and another server used the folder. `layout.py --update` gives the same files; the file that the list no longer names was removed by hand.

## Rule V5, the reason `reader_scope` and the calibration file of round 4 (13.10.2026)

This chapter changes the chapter before it. `../CONTRACT.md` chapter 19 has the rules, `../EXAMINATION.md` chapter 14 the findings.

1. Calibration. The calibration file of the product is `daten/gj_values/round4/calibration_dev_all.json`. `layout_add.py --values` puts it into the list and removes the entry of the round 3 file. The origin text has 4 sentences (`values_record.ORIGIN`).
2. `values_record.py` version `parlpdfech-values/0.4.0`. `validate` gives no calibration file to the validator: the validator opens the product file by its own path. The call stops if the validator did not use the product file.
3. New function `values_record.response_signs(block file, rule file, manifest)`. For the kinds proposal and executive_proposal it runs the responder rule one more time. It returns the rule tiers of the candidates that are not an addressed body. `serve_convert.py` and `fresh.py` put the result into `run_info` and into `convert.json`.
4. `convert.json` key `values`: new keys `cascade.kind_rule`, `cascade.rule_chain_id`, `cascade.v5`, `cascade.searched_out_of_scope`, `cascade.text_blocks_not_written` and `response_signs`.
5. `check_fresh.py` writes 5 more synthetic files: `petition_head.pdf`, `response_no_author.pdf`, `v5_proposal.pdf`, `v5_response.pdf`, `proposal_signed.pdf`. `check_values.py` uses the 11 files.

Run in this step (13.10.2026, one run each):

| Command | Result |
|---|---|
| `python package/worker/layout_add.py --values` | 1 path added, 5 changed, 1 removed; 86 files, 14,980,658 bytes |
| `python package/worker/layout.py --update`, then the stale copy of the round 3 file removed by hand | 6 files copied, 53 compiled files; `layout.py --check`: 86 files, 0 different |
| `python package/worker/check_values.py --work package/work/cascint/cv1 --ocr none` | 390 of 390 checks passed |
| `python package/worker/check_worker.py --work package/work/cascint/cw --reference-dir daten/gj/fullrun_b1s_dev` | 79 checks, 0 failed |
| `python package/worker/check_fresh.py` | not run |

# Ids and sources of the numbers of the technical report

This file belongs to the technical report, [../technical_report.md](../technical_report.md). Each number of the report is an entry of [../numbers.json](../numbers.json). [../numbers.md](../numbers.md) gives the same entries as a table. A name in square brackets in the report, for example [`sets.docling.all`], is the id of an entry.

## Short forms of the ids

| Short | Id stem |
|:------|:----------------------------------------------|
| `R` | `values.last_run.rules_only.all` |
| `C` | `values.last_run.combined.all` |
| `V` | `values.last_run.rules_only.validation` |
| `G7` | `values.last_run.rules_only.group7` |
| `P` | `values.last_run.parliaments` |
| `D` | `values.round4` |
| `H` | `values.heads2` |
| `F` | `design.fixed` |
| `E` | `values.last_run.check_by_eye` |
| `K` | `values.last_run.contact` |
| `KD` | `values.last_run.contact.rule_design_list` |
| `S` | `values.last_run.spread.rules_only` |

## Ids of table cells and figures

A table gives its stems in its caption. The id of a cell is `<stem>.<field>.<key>`. In Table 1 it is `<stem>.<tier>.<key>`, and the caption of Table 1 gives the keys of each stem. The field keys are `affair_type`, `title`, `affair_number`, `submission_date`, `response_date`, `responder_name` and `first_author`. An interval has the keys `<key>.bootstrap_low5` and `<key>.bootstrap_high95`.

The figures have no numbers. Only the bars come from numbers: the bars of Table 2 and of Figure 4 (right) show `R.<field>.share_correct` and `C.<field>.share_correct`.

## Numbers with no id

Some numbers of the report are not entries of `numbers.json`:

- Dates and times, for example 13.10.2026 at 21:30, and version names, for example I95.
- The hardware in chapters 3 and 7: Apple M4, 32 GB, 24 GB and one H100 GPU. Also the 31 development documents in chapter 7. Source: [apertus-gpu.md](apertus-gpu.md).
- "All of 1 parliament" in item 11 of chapter 6. Source: [limits.md](limits.md), limit L11.
- Counts of the text, for example the 7 head values, the 2 readers, the 2 Apertus tiers and the 4 panels of Figure 1.

## Marks

No mark word means measured: a project script wrote the value into a result file. "Derived": calculated from measured counts, for example each share correct. "Read" and "protocol only": from a work log, a criteria file, an evidence text or a state file. "Reading check": a count of the check by eye. Development values carry the mark of their source file, for example "after the opening": they are design values.

## Source files

Paths are files of the private project. `numbers.json` gives the SHA-256 of each file, or of the one line with the value.

| Ids | File |
|:----------------|:----------------------------------------------------------------|
| `R.*`, `V.*`, `G7.*`, `C.*`, `P.*` | `daten/gj_values/heads2/last/measures_first.json` |
| `D.*` | `daten/gj_values/round4/measures_dev_all.json` |
| `H.*` | `daten/gj_values/heads2/measures_dev.json`; `H.entry.*`: `entry.json` |
| `E.documents`, `E.kind_looks_wrong`, `sets.test_set.*`, `gaps.*` | `crisp-dm/00-cross-cutting/protocol.md` (protocol only) |
| `pkg.*` | `package/STATE.md` |
| `S.*` | `daten/gj_values/heads2/last_subsets/measures_subsets.json` |
| `K.s3.all`, `K.s4.all` | the line count of 2 id files in `crisp-dm/05-evaluation/evidence/` (no id is published) |
| `K.*` (other), `KD.*` | `crisp-dm/05-evaluation/`: the contact history and the evidence dossier |
| `F.*`, `cascade.*` | addenda G and I of the criteria, `src/m11_writer.py`, `src/m11_values_combined.py`; `src/m11_cascade.yaml` |
| `sets.*` (other) | `daten/gj/docs_build.json`, `daten/gj/labels_build.json` |
| `xp.*` | `daten/gj/crossparl_b1s_dev/crossparl.json` |

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 16.10.2026. It is the chapter "Ids and sources of the numbers" of the technical report of 16.10.2026, 04:28, moved into this file. The rows of ids that the short report no longer uses are not in it. The rows of `F.*`, `E.*`, `pkg.*` and the protocol now name the source file of each id that the report uses. Later on 16.10.2026, an AI agent added the chapter "Numbers with no id" and the sentence on Table 1.

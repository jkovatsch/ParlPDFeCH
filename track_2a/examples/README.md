# Example records of the app

This folder holds stored record files of the app (`../app/`) for the 3 samples 26171, 879163 and 714840. The page "Example" of the site parlpdfech.ansv.ch shows them step by step. The page calculates nothing: each value, probability and line of RDF on it comes from these files.

Limit first: the 3 samples are development documents. Their probabilities are not a result on a document that the project did not see.

## Origin

- The app at public commit `e42d62d` made the files on 15.10.2026, with the mode `auto`: code rules read the values; stored Apertus results give a part of the labels of the blocks and of the document.
- Record `s-26171`: run from 16:27:52 to 16:28:05 UTC. Record `s-879163`: 16:28:12 to 16:28:19 UTC. Record `s-714840`: 17:34:59 to 17:35:04 UTC.
- The files are copies of the folder `work/records/<record>/` of that run. Nobody edited them. The SHA-256 of each file is the SHA-256 that `convert.json` of the run gives. `SHA256SUMS` lists them.
- `../app/CONTRACT.md` (chapters 3, 6, 16 to 19) gives the meaning of each key.

## Files of each record folder

| File | Content |
|---|---|
| `<doc>.ech.ttl` | the eCH-0295 record (working draft I95) as RDF in Turtle |
| `<doc>.values.ttl` | each value of the record with its probability, page and place in the text (RDF, Turtle) |
| `<doc>.ech.yaml` | the eCH-0295 record as YAML |
| `<doc>.labels.yaml` | the label of each block and of each value, with its probability and its source |
| `validation.json` | the result of each check of the validator |
| `view.json` | the view of the app: pages, lines, blocks, labels, values and checks (form `parlpdfech-site-view/3`) |

The other files of a record of the app are not in this folder:

- `<doc>.gesamt.trig`, `<doc>.gesamt.rdf.xml`, `<doc>.provenance.yaml` and `manifest.json` hold a code name of the project that the public files must not hold.
- The page does not need `<doc>.ech.rdf.xml` (the same record as RDF/XML), `convert.json` (the summary of the run: times, checks and the SHA-256 of each file), `source.pdf` and `page-1.png`. The page image of each sample is `../app/data/samples/<doc>/page-1.png`.

The copied files `<doc>.labels.yaml` and `validation.json` name the input files of the run with the paths of the working folders of the project. Nobody changed these paths.

## Licence

Derived data, CC-BY-4.0. Source: OpenParlData.ch. The files also hold texts of the 3 documents. The parliaments and executives published these documents. See `../../NOTICE`, chapter 3.

## About this text

Language: English, to the rules of ASD-STE100 (Issue 9). An AI agent (Claude Opus 5.5) wrote this text on 15.10.2026, and shortened its limits in the evening.

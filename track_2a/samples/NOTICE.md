# Notice for the samples

History: input and output of the earlier converter of 12.10.2026 (`make run-earlier`). Not the product of this version; see [../README.md](../README.md), chapter "Samples".

The app does not read this folder. The app has its own files of the 3 samples in `../app/data/samples/` and makes the records of the product from them. The earlier converter took its metadata values from the export record, not from the PDF.

Source: OpenParlData.ch

License of the data of OpenParlData: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Attribution: "Source: OpenParlData.ch".

## What the samples contain

| Content | Origin | Changes by this project |
|---|---|---|
| `*/input/export.json`, `pdf_index.csv` | Fields of the OpenParlData exports of 04.10.2026 (https://files.openparldata.ch/exports/): document, affair, events, councils and parliament | Selection of the records of the 3 documents. The full text field of the document is removed. |
| `*/input/docling.json`, `*/input/atoms.json` | The text of 3 PDF documents. The parliaments and executives published the documents. OpenParlData gives copies (https://files.openparldata.ch/doc/). | Conversion with Docling 2.133.0 into blocks, and division of the blocks into atoms (lines with page, frame and character range) |
| `*/expected/` | The output of the earlier converter of 12.10.2026. It is not the output of the product. | eCH-0295 instance (YAML), provenance side file, answers of the rule stage |
| `languages.csv` | The language of each document from the export field, or from a rule on the export text | Selection of 3 rows and 3 columns |

- `*/input/` is the stored input of the earlier converter. No export value goes into a record of the product.
- In `source.json`, the keys `split_path_1`, `s1_rule_id`, `s1_role`, `s1_source`, `claimed_L9` and `abstention_reason_L9` are values of the earlier converter of 12.10.2026 (path 1). They say nothing about the product.
- The API description of OpenParlData (read on 06.10.2026) does not say if CC BY 4.0 applies to the copies of the PDF documents.
- The documents name persons with a public role: members of a parliament or an executive, and officials who sign for an authority.
- Before the publication, two AI agents (Claude Opus 5.5) examined each of the 3 documents for personal data of third parties. Both gave PASS.
- This folder contains no PDF document. `source.json` of each sample gives the URL of the publisher, the URL of the copy of OpenParlData and the SHA-256 of the PDF.
- The app folder contains the PDF of the 3 documents with the same SHA-256 (`track_2a/app/data/samples/<doc>/source.pdf`) and one image of each page (`page-1.png`, made with pypdfium2). The app shows them in the result view.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. On 14.10.2026, an AI agent added the item on the PDF files of the app folder. On 15.10.2026, an AI agent (Claude Opus 5.5) marked the folder as input and output of the earlier converter and explained the keys of `source.json`.

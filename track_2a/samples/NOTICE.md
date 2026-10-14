# Notice for the samples

Source: OpenParlData.ch

License of the data of OpenParlData: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Attribution: "Source: OpenParlData.ch".

## What the samples contain

| Content | Origin | Changes by this project |
|---|---|---|
| `*/input/export.json`, `pdf_index.csv` | Fields of the OpenParlData exports of 04.10.2026 (https://files.openparldata.ch/exports/): document, affair, events, councils and parliament | Selection of the records of the 3 documents. The full text field of the document is removed. |
| `*/input/docling.json`, `*/input/atoms.json` | The text of 3 PDF documents. The parliaments and executives published the documents. OpenParlData gives copies (https://files.openparldata.ch/doc/). | Conversion with Docling 2.133.0 into blocks, and division of the blocks into atoms (lines with page, frame and character range) |
| `*/expected/` | The output of the converter of this project | eCH-0295 instance and provenance side file |
| `languages.csv` | The language of each document from the export field, or from a rule on the export text | Selection of 3 rows and 3 columns |

- The API description of OpenParlData (read on 06.10.2026) does not say if CC BY 4.0 applies to the copies of the PDF documents.
- The documents name persons with a public role: members of a parliament or an executive, and officials who sign for an authority.
- Before the publication, two AI agents (Claude Opus 5.5) examined each of the 3 documents for personal data of third parties. Both gave PASS.
- This folder contains no PDF document. `source.json` of each sample gives the URL of the publisher, the URL of the copy of OpenParlData and the SHA-256 of the PDF.
- The app folder contains the PDF of the 3 documents with the same SHA-256 (`track_2a/app/data/samples/<doc>/source.pdf`) and one image of each page (`page-1.png`, made with pypdfium2). The app shows them in the result view.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. On 14.10.2026, an AI agent added the item on the PDF files of the app folder. No human examined it.

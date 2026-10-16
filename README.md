# ParlPDFeCH

A PDF of a Swiss parliament goes in. An eCH-0295 record in RDF comes out. Code rules read the values. On a GPU, Apertus-v1.5-8B decides 2 of them: the affair type if the rules found none, and the first author if the rule value is absent or weak. Each value has a probability, a page and a place in the PDF.

Track 2A (OpenParlData) of the Hack Apertus online hack. The [technical report](track_2a/technical_report.md) gives the method and the result.

## Try it

### Convert a PDF with Apertus (needs a GPU)

Clone this repository (button "Code" on its GitHub page) and run the commands in `track_2a/`. You need make, uv, jq, curl and `pdftotext`, and for `make view` also cargo and `wasm-bindgen` 0.2.127 ([all details](track_2a/docs/run-locally.md)). The Apertus step needs a GPU: a Mac with Apple silicon and 32 GB or more, or an NVIDIA GPU with 24 GB or more. Before `make setup-apertus`, accept the conditions of the model on Hugging Face, then log in with `.venv/bin/hf auth login`. It downloads about 17.3 GB and needs about 40 GB of free disk.

```bash
cd ParlPDFeCH/track_2a
make setup               # one time
make setup-pdf           # one time: Docling and 2 models (about 0.8 GB on a Mac); on macOS also text recognition (OCR)
make setup-apertus       # one time: Apertus-v1.5-8B and the value heads
make convert PDF=<file>  # or PDF=<URL>, DIR=<folder>, LIST=<file of paths and URLs>
make list                # all IDs as a table
make view ID=0001        # on request: opens result 0001 at http://127.0.0.1:8080/app/ (or the next free port)
```

- Each PDF gets an ID, and the same PDF keeps its ID. The terminal shows each value with its probability, its source (rules or Apertus), and valid yes or no. Valid means that the record passed the validator, not that each value is correct. A PDF can have up to 25 pages and 20 MB.
- A sample to try: `make convert PDF=app/data/samples/26171/source.pdf`. In the 3 samples, Apertus writes no value. The terminal still shows the head probabilities of Apertus.
- The GPU can also be on another computer, for example a rented GPU in the cloud. That computer runs `make serve-apertus`. Your computer runs `make setup-apertus APERTUS_MODEL=none` (the heads only) and `make convert APERTUS_URL=...` through an ssh tunnel ([the GPU for the Apertus step](track_2a/docs/apertus-gpu.md)).
- With no GPU, `make convert` writes a note and makes the record with the code rules only. `APERTUS=0` gives the code rules only on purpose.
- On macOS, `make setup-pdf` installs the text recognition (OCR) of Apple Vision. On Linux there is no OCR, so the PDF needs a text layer.
- Tested only on one Mac. On 15.10.2026, with the code rules: 3 samples and 5 development PDFs of 5 parliaments gave 8 valid records. On 16.10.2026, with the Apertus step (Apple M4, 32 GB, MLX): 3 samples and 4 development PDFs gave valid records, in 30 to 115 s for each PDF. On the stored text blocks of 31 development documents, the read-out gave the same decisions as the stored states of one H100 GPU. Not tested: an NVIDIA GPU, Linux, Windows, a second computer, an ssh tunnel, the model download of `make setup-apertus`. The development documents are not new to the method: the rule authors read them, and the heads were fitted on development documents.

### Only look at 3 results (Docker, no GPU)

`make run` starts the app in Docker. It converts only the 3 sample PDFs, from stored inputs. It does not run Apertus. You need git, make and Docker with Compose. On one Mac, the first build and start took about 2 minutes. Not tested on Windows or Linux.

```bash
cd ParlPDFeCH/track_2a
make run
```

Open http://127.0.0.1:8080/app/ and click "Open the result" on a sample card. You see 3 places: the PDF page with a box on each value, the values with their probability, and the RDF below them. A click on a value marks it in all 3 places. `make stop` stops the app.

<img src="docs/img/result-view.png" width="560" alt="Screenshot of the app for sample 26171. Left: the PDF page with a coloured box on each value. Right: the values, each with a probability bar, the word certain or unsure, and the page. The RDF is below them, not in the screenshot.">

With `make run-native`, the app page also converts a PDF with the code rules only (button "Convert your own PDF").

## How it works

<table>
<tr>
<td width="340"><img src="docs/img/step-1.svg" width="320" alt="Drawing: a PDF page with three dashed text blocks, an arrow, and five lines, each in square brackets."></td>
<td>
<strong>1. The page becomes lines.</strong><br>
Docling finds the text blocks of a PDF page (the dashed boxes).
Code cuts them into lines. Each line keeps its page, its box and its character range (the brackets).
</td>
</tr>
<tr>
<td width="340"><img src="docs/img/step-2.svg" width="320" alt="Drawing: three lines go into a box with curly braces. Three marks come out: a small page with yellow top and bottom ends, a tag, and one person who changes to a second person."></td>
<td>
<strong>2. Code rules decide first.</strong><br>
A rule chain (the braces) reads the lines, from the PDF alone.
It marks the head and foot of each page (the small page) and the role of each block (the tag). It finds a change of author (the 2 persons).
</td>
</tr>
<tr>
<td width="340"><img src="docs/img/step-3.svg" width="320" alt="Drawing: a document and a speech bubble with a question mark go into a box with a grid of squares. One square is yellow. A small funnel gives a long bar for a check mark and a short bar for a cross. A speech bubble with lines is crossed out."></td>
<td>
<strong>3. Apertus decides and writes no text.</strong><br>
Apertus-v1.5-8B (the grid) gets the whole document and one question (the bubble).
A linear head (the funnel) reads its hidden state after layer 20 (the yellow square) and gives a probability for each option (the bars). No text comes out.
Apertus decides only 2 values: the affair type, if the rules found none, and the first author, if the rule value is absent or weak.
<code>make convert</code> runs this step on a GPU. The app (<code>make run</code>) does not run Apertus. For the 3 samples, it shows stored Apertus block labels.
</td>
</tr>
<tr>
<td width="340"><img src="docs/img/step-4.svg" width="320" alt="Drawing: a card with three values, each with a dark bar. A yellow marker joins the first value to one line on a PDF page. The third value has a dashed border."></td>
<td>
<strong>4. Data with its source.</strong><br>
A writer makes the record in Turtle and YAML, and a second RDF file with each value (the card).
Each value has a probability (the bar), a page and a place in the PDF (the yellow marker). For the first author from Apertus, the place is the block that the head picked. For the affair type from Apertus, code finds the first type word of that type; with no such word, the type is not written. A dashed border means unsure.
</td>
</tr>
</table>

## Result

The one fixed run of 13.10.2026 compared 872 documents of 26 parliaments with the OpenParlData register. The register is not a hand-checked gold set ([all limits](track_2a/docs/limits.md)). By field, 0.2075 (response date) to 0.8929 (responding body) of the documents with a register value got the register value.

## More

- [Full description for the judges](track_2a/README.md)
- [Run the app: all details](track_2a/docs/run-locally.md)
- [Technical report](track_2a/technical_report.md)
- [Technical report, long version](track_2a/docs/report-long.md)
- [All limits of the result](track_2a/docs/limits.md)
- [All numbers with their sources](track_2a/numbers.json) ([as text](track_2a/numbers.md))
- [Map of the folder track_2a](track_2a/docs/repository-map.md)
- [About: challenge, deliverables, results, eCH-0295, licenses](docs/about.md)

Code: Apache-2.0. Texts: CC-BY-4.0. See `NOTICE`.

Copyright 2026 Jonathan Kovatsch, as a private person.

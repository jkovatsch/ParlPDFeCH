# Run the app on your computer

The app converts a PDF of a Swiss parliament into an eCH-0295 record. It runs on your computer. The app (ways 1 and 2) uses no GPU. Run the commands in the folder `track_2a/`. Ways 1 and 2 ran on one Mac on 14.10.2026, way 3 on 15.10.2026. Way 3 can also run the Apertus step, which needs a GPU on your computer or on another computer ([apertus-gpu.md](apertus-gpu.md)). The Apertus step ran on one Mac on 16.10.2026.

## Way 1: container (`make run`)

```bash
make run
```

- You need Docker with Compose. The build of the image needs the network one time. You do not need `make setup`.
- The command builds the image (target `slim`) from `app/` and starts it on `127.0.0.1:8080`.
- Open `http://127.0.0.1:8080/app/`. `make stop` stops the container. `make logs` shows its log.
- This image converts the 3 samples only. It does not convert your own PDF.
- State on 14.10.2026: run one time on one Mac (Apple silicon, Docker server 29.2.1), in a clone of GitHub at commit `10e07b4`. A second check used port 8080, so the command was `make run PARLPDFECH_PORT=8082`. The 3 samples in the modes auto and rules gave 6 valid records. Not run: `make stop`, `make logs`, and the targets `run-full` and `check-offline` of `app/Makefile`. On the same day a private build pipeline on Linux built a container image from the source tree of the package. Nobody started this image.

## Way 2: no container (`make run-native`)

```bash
make setup
make setup-pdf    # only for your own PDF
make run-native
```

- You need [uv](https://docs.astral.sh/uv/) 0.11 or later, git, make, and cargo with `wasm-bindgen` (see below). For your own PDF, you also need the command `pdftotext`.
- `make setup` needs the network one time. It installs Python 3.12 with uv, and uv can also put the command `python3.12` into `~/.local/bin`. It installs the Python packages of `app/container/requirements-slim.txt` into `.venv/`. If cargo is on the computer, it downloads the Rust crates; if not, it prints a note.
- You need cargo with the target `wasm32-unknown-unknown`, and the command `wasm-bindgen` 0.2.127. With rustup, the file `app/rust-toolchain.toml` adds the target. To install the command: `cargo install wasm-bindgen-cli --version 0.2.127` (network).
- The command builds the server and the WebAssembly bundle, then starts the app on `127.0.0.1:8080`. `make run-native PORT=9090` sets another port. Stop it with Ctrl-C.
- Open `http://127.0.0.1:8080/app/`.
- The 3 samples need nothing more.
- Your own PDF needs `make setup-pdf` one time, after `make setup`. It needs the command `pdftotext` (macOS with Homebrew: `brew install poppler`). If `pdftotext` is absent, it stops before the download and gives the install command.
- `make setup-pdf` needs the network. It installs the packages of `app/container/requirements-full.txt` (`docling` 2.133.0, `pypdfium2` 5.14.0, torch) into `.venv/`. On macOS it also installs `ocrmac` 1.0.1 (text recognition of Apple Vision, as for the stored Docling files of the project; `tools/requirements-macos-ocr.txt`). It downloads the 2 Docling models into the Hugging Face cache if they are absent.
- Size on a Mac with Apple silicon: 283.5 MB of packages (sizes from the PyPI data) and 530.0 MB of models. `.venv/` grows by about 1 GB.
- Without these packages, the app stops with the note `pdf_reader_absent`.
- State on 14.10.2026: `make setup` and `make run-native` ran on one Mac (Apple silicon, macOS), also in a fresh clone, with the offline flags of cargo. The 3 samples in the modes auto and rules gave 6 valid records.
- State on 15.10.2026: `make setup-pdf` ran on one Mac (Apple silicon, macOS), in a fresh clone of GitHub at commit `3eff351`, with the target `setup-pdf` added as a patch. The packages came from the uv cache of that Mac. The 2 models came from its Hugging Face cache, and in 2 more runs with an empty cache from huggingface.co.
- Then `make run-native` converted 2 PDFs that are not in the sample index (copies of 2 samples with one added comment line). Both records were valid. `make test` gave PASS.
- Earlier checks of an own PDF used synthetic PDF files and the 3 sample PDF files (`app/README.md`, chapter "The modes"). No other parliament PDF is recorded.
- Times of that check: the first start of `make run-native` in the fresh clone took 49 s, most of it for the 2 cargo builds. The first PDF took 53 s, of which 45.6 s for the start of Docling. The second PDF took 18 s.
- Not tested: Windows, Linux, x86_64, and the line for Debian or Ubuntu that `make setup-pdf` gives.

## Way 3: own PDFs in the terminal (`make convert`)

```bash
make setup
make setup-pdf                   # one time, as in way 2
make setup-apertus               # one time, only for the Apertus step; needs a GPU and your own Hugging Face account
make convert PDF=<file or URL>   # one PDF
make convert DIR=<folder>        # each *.pdf of the folder, no subfolder
make convert LIST=<file>         # one path or http(s) URL in each line; a line that starts with # is a comment
make list                        # the IDs as a table
make view ID=0002                # on request: this one result in the browser; Ctrl-C stops it
```

- Limits first. With `APERTUS=0`, or with no `make setup-apertus`, your PDF gets the code rules only (no language model, no GPU). The Apertus step needs `make setup-apertus` and a GPU. It runs with `APERTUS=auto` (the default) or `APERTUS=1`. Then Apertus-v1.5-8B also reads out the PDF on a GPU of this computer or of another computer. The Apertus heads can give the affair type and the first author ([apertus-gpu.md](apertus-gpu.md)). As in the app, the limits are 25 pages and 20 MB, and the first 1024 bytes must have the mark `%PDF-`. On Linux the PDF needs a text layer (no OCR); on macOS `make setup-pdf` installs `ocrmac`.
- Not run: Windows, Linux, Ctrl-C typed in a terminal, the full time limit of 600 s and a PDF with a password. The downloads came only from GitHub and from servers on the same computer. No PDF gave a record with valid no.
- You need `make setup` and `make setup-pdf` of way 2, the commands jq and `pdftotext`, and curl for a URL. `make view` also needs cargo and `wasm-bindgen` 0.2.127, as way 2.
- A URL must be http or https. A download has a limit of 20 MB and 120 s. The result keeps the source (path or URL) and the SHA-256 of the PDF.
- A relative path of `PDF=` or `DIR=` starts in `track_2a/`. A relative path in a `LIST` file starts in the folder of that file. `~/` is expanded.
- The worker of the app converts each PDF in the mode rules, with the arguments and the environment of the server. Its time limit is 600 s for each PDF. With the Apertus step it runs in the mode auto, and the time limit is `APERTUS_TIMEOUT` (1800 s). No file below `app/` changes.
- Each PDF gets an ID: `0001`, `0002`, and so on. The same PDF (same SHA-256) keeps its ID.
- A PDF that the app refuses also gets an ID, with valid `failed:<code>` (for example `failed:too_long` for more than 25 pages). A missing file, a file that is not a PDF, a file of more than 20 MB and a failed download get no ID.
- A PDF with a stored result is not converted again. The terminal shows the stored result. `AGAIN=1` converts it again. If that conversion fails, the old result stays. A stored result is also converted again if the Apertus step was on for it and is off now, or the other way.
- For each PDF the terminal shows the ID, valid yes or no, and each value with its probability and status (certain or unsure). With the Apertus step, it also shows the source of each value (rules or Apertus) and the head probabilities of Apertus ([apertus-gpu.md](apertus-gpu.md), chapter "What the terminal shows"). It also gives the fields with no value and the folder `out/<ID>/`.
- `make list` shows the IDs as a table: ID, valid, time, affair type, title, source and SHA-256. The file `out/catalog.tsv` has all columns.
- `make view ID=0002` (also `ID=2` or `ID=ID-0002`) starts the server of the app for this one result. The server is read-only and listens on `127.0.0.1`.
- The port is 8080 or the next free port up to 8179. `PORT=<n>` sets it. The command opens `http://127.0.0.1:<port>/app/#/view/<record_id>` in the browser. `OPEN=no` shows the address only.
- `make view` does the build steps of way 2 first. cargo builds only the parts that changed. It shows a copy of the record, made at its start. The online website does not have this view.
- Only one `make convert` can run at a time.
- State on 15.10.2026: way 3 ran on one Mac (Apple silicon, macOS). The run used a clone of the local repository at commit `e42d62d`, with the files of `make convert` added.
- In that clone, 3 samples (a copy, a URL of GitHub, a folder) and 5 development PDFs of 5 parliaments gave 8 valid records. The 5 PDFs are in German, French and Italian, with 4 to 14 pages. The rule authors read the development documents.
- The values of the 8 records were equal to those of an upload of the same PDFs to the app (mode rules). After changes to `tools/convert.sh`, a second run gave the same values. `make test` gave PASS.
- Bad inputs stopped with a message, and the next input continued: no PDF, more than 20 MB, more than 25 pages, no text layer, a damaged PDF, a URL with the status 404.
- An earlier version of the script converted 5 other development PDFs, with 5 valid records.
- `make view` ran each time with `OPEN=no`. The server gave the page and each file of the record with the status 200. It refused an upload and a delete (403), and a record of another ID (404).
- A headless Chrome showed the values with the probabilities of the terminal. A signal from a script stopped the server. Not run: the start of the browser by the command.
- Times on one Mac: a development PDF took 18 to 35 s. After a new setup, the first PDF that Docling read took 64 s or 67 s. A copy of a sample took 4 to 11 s.
- The first `make view` built the server in about 23 s and the WebAssembly bundle in about 25 s.
- The runs of 15.10.2026 had the code rules only and no `ocrmac`.
- State on 16.10.2026: the Apertus step ran on one Mac (Apple M4, 32 GB), in clones. With MLX on this computer, 3 samples and 4 development PDFs gave valid records; in the 3 samples, Apertus wrote no value. Through `make serve-apertus` on the same computer, 3 of these development PDFs gave the same values as the local run. On the 3 samples, `APERTUS=0` gave the same records as before the Apertus step. [apertus-gpu.md](apertus-gpu.md), chapter "What was tested", gives the details.
- Times with the Apertus step on that Mac, with MLX: a sample took 35 to 57 s, and a development PDF took 46 to 115 s (115 s: the first PDF in a new clone). Through the service on the same computer, a development PDF took 30 to 75 s.

## What the app does with your PDF

- Way 2: on the start page, click "Convert your own PDF" (or "Own PDF" at the top). Drop the PDF on the box, or click "Choose a PDF". Then click "Convert".
- Way 3: `make convert` gives the PDF to the same worker of the app, in the mode rules; with the Apertus step in the mode auto.
- In the app (way 2), your PDF gets the code rules only. The app runs no language model and uses no GPU. Only `make convert` with the Apertus step runs Apertus.
- Only the 3 samples have block labels from stored Apertus states.
- The record has no comparison with a register.
- Text recognition (OCR): on macOS, `make setup-pdf` installs the Python package `ocrmac`, and Docling then runs the text recognition of Apple Vision (the record has the notice `ocr_apple`). Text in a picture can then be in the record, and a page with no text layer can give text (not tested with a scan). On Linux, `make setup-pdf` installs no OCR: your PDF needs a text layer, a PDF with no text layer stops with the note `no_text_layer`, and the record has the notice `ocr_none`.
- An unchanged PDF of a sample gives the stored result of that sample. Docling does not run for it.
- Docling loads its layout model at the revision `main`. A later change of that model can give other text blocks.

## Where you see the result

- Way 2: after the conversion, the page opens the result view: `/app/#/view/<record_id>`.
- Way 3: `make view ID=<n>` opens the same result view for one result of `make convert`.
- The result view has 3 places. The PDF: the image of each page with a box on each value. The values: each value with its probability. The RDF: the eCH-0295 record (no probabilities) and the file of the values with probabilities `<doc>.values.ttl`, each with a download link.
- A link in the result view opens the technical view: `/app/#/record/<record_id>`. Its downloads include one TriG file with all parts, labels and probabilities.
- With `make run-native`, each result is in the folder `app/work/records/<record_id>/`.
- With `make convert`, each result is in the folder `out/<ID>/record/`. git ignores the folder `out/`.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 14.10.2026 and changed the state lines in the afternoon and evening of that day. On 15.10.2026 an AI agent added `make setup-pdf`, and later corrected sentences after an audit. In the evening of 15.10.2026, an AI agent added way 3 and shortened the start of the file. On 16.10.2026, AI agents added the Apertus step and the OCR of macOS, and an AI agent corrected the texts to the new state.

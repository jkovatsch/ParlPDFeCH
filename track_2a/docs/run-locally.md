# Run the app on your computer

The app converts a PDF of a Swiss parliament into an eCH-0295 record. It runs on your computer and uses no GPU. Run the commands in the folder `track_2a/`. Both ways ran on one Mac on 14.10.2026.

Status: EXCEPTION, NOT RELEASED. No human examined this file.

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
- `make setup-pdf` needs the network. It installs the packages of `app/container/requirements-full.txt` (`docling` 2.133.0, `pypdfium2` 5.14.0, torch) into `.venv/`. It downloads the 2 Docling models into the Hugging Face cache if they are absent.
- Size on a Mac with Apple silicon: 283.5 MB of packages (sizes from the PyPI data) and 530.0 MB of models. `.venv/` grows by about 1 GB.
- Without these packages, the app stops with the note `pdf_reader_absent`.
- State on 14.10.2026: `make setup` and `make run-native` ran on one Mac (Apple silicon, macOS), also in a fresh clone, with the offline flags of cargo. The 3 samples in the modes auto and rules gave 6 valid records.
- State on 15.10.2026: `make setup-pdf` ran on one Mac (Apple silicon, macOS), in a fresh clone of GitHub at commit `3eff351`, with the target `setup-pdf` added as a patch. The packages came from the uv cache of that Mac. The 2 models came from its Hugging Face cache, and in 2 more runs with an empty cache from huggingface.co.
- Then `make run-native` converted 2 PDFs that are not in the sample index (copies of 2 samples with one added comment line). Both records were valid. `make test` gave PASS.
- Earlier checks of an own PDF used synthetic PDF files and the 3 sample PDF files (`app/README.md`, chapter "The modes"). No other parliament PDF is recorded.
- Times of that check: the first start of `make run-native` in the fresh clone took 49 s, most of it for the 2 cargo builds. The first PDF took 53 s, of which 45.6 s for the start of Docling. The second PDF took 18 s.
- Not tested: Windows, Linux, x86_64, and the line for Debian or Ubuntu that `make setup-pdf` gives.

## What the app does with your PDF

- On the start page, click "Convert your own PDF" (or "Own PDF" at the top). Drop the PDF on the box, or click "Choose a PDF". Then click "Convert".
- Your PDF gets the code rules only. The app runs no language model and uses no GPU.
- Only the 3 samples have block labels from stored Apertus states.
- The record has no comparison with a register.
- Your PDF needs a text layer. `make setup-pdf` installs no text recognition (OCR). A PDF with no text layer stops with the note `no_text_layer`. Text that is only in a picture is not in the record.
- The page can say that the text recognition of macOS (Apple OCR) runs. It runs only if the Python package `ocrmac` is in `.venv/`, and `make setup-pdf` does not install it. The record then has the notice `ocr_none`: no text recognition ran.
- An unchanged PDF of a sample gives the stored result of that sample. Docling does not run for it.
- Docling loads its layout model at the revision `main`. A later change of that model can give other text blocks.

## Where you see the result

- After the conversion, the page opens the result view: `/app/#/view/<record_id>`.
- The result view has 3 places. The PDF: the image of each page with a box on each value. The values: each value with its probability. The RDF: the eCH-0295 record (no probabilities) and the file of the values with probabilities `<doc>.values.ttl`, each with a download link.
- A link in the result view opens the technical view: `/app/#/record/<record_id>`. Its downloads include one TriG file with all parts, labels and probabilities.
- With `make run-native`, each result is in the folder `app/work/records/<record_id>/`.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 14.10.2026 and changed the state lines in the afternoon and evening of that day. On 15.10.2026 an AI agent added `make setup-pdf`, and later corrected sentences after an audit. No human examined it.

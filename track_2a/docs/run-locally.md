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
make run-native
```

- `make setup` needs the network one time. It installs Python 3.12 with uv, and uv can also put the command `python3.12` into `~/.local/bin`. It installs the Python packages of `app/container/requirements-slim.txt` into `.venv/`, and it downloads the Rust crates.
- You need cargo with the target `wasm32-unknown-unknown`, and the command `wasm-bindgen` 0.2.127. With rustup, the file `app/rust-toolchain.toml` adds the target. To install the command: `cargo install wasm-bindgen-cli --version 0.2.127` (network).
- The command builds the server and the WebAssembly bundle, then starts the app on `127.0.0.1:8080`. `make run-native PORT=9090` sets another port. Stop it with Ctrl-C.
- Open `http://127.0.0.1:8080/app/`.
- The 3 samples need nothing more.
- Your own PDF needs more: the Python packages `docling` 2.133.0 and `pypdfium2` 5.14.0, the 2 Docling models in the local Hugging Face cache and the command `pdftotext` (`app/container/requirements-full.txt`). Without them, the app stops with the note `pdf_reader_absent`.
- State on 14.10.2026: `make setup` and `make run-native` ran on one Mac (Apple silicon, macOS), also in a fresh clone, with the offline flags of cargo. The 3 samples in the modes auto and rules gave 6 valid records.

## What the app does with your PDF

- Drop a PDF on the page, or select it with the button for your own PDF.
- Your PDF gets the code rules only. The app runs no language model and uses no GPU.
- Only the 3 samples have block labels from stored Apertus states.
- The record has no comparison with a register.

## Where you see the result

- After the conversion, the page opens the result view: `/app/#/view/<record_id>`.
- The result view has 3 places. The PDF: the image of each page with a box on each value. The values: the 7 values with their probability. The RDF: the eCH-0295 record and the file of the values `<doc>.values.ttl`.
- A link in the result view opens the technical view: `/app/#/record/<record_id>`.
- With `make run-native`, each result is in the folder `app/work/records/<record_id>/`.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 14.10.2026 and changed the state lines in the afternoon and evening of that day. No human examined it.

# The GPU for the Apertus step

The Apertus step of `make convert` runs Apertus-v1.5-8B (bf16) on each PDF. Linear heads read its hidden state after layer 20 and decide 2 values: the affair type, if the code rules found no type, and the first author, if the rule value is absent or weak. An Apertus value enters the record only with a head probability of 0.80 or more. No text comes out. This step needs a GPU. The GPU can be on this computer or on another computer, for example a rented GPU in the cloud. With no GPU, `make convert` writes a note and makes the record with the code rules only. `APERTUS=0` gives the code rules only.

## What you need

- A GPU: a Mac with Apple silicon and 32 GB memory or more (backend `mlx`), or an NVIDIA GPU with 24 GB memory or more (backend `cuda`). The model needs 16.1 GB. A Mac with less than 32 GB or an NVIDIA GPU with less than 20 GiB gets the reason `memory_too_small`. Then `make setup-apertus` stops before the download (in `make setup`: a note, no stop). `memory_low` means that too little memory is free now: close other programs and try again.
- macOS or Linux. On Windows, use WSL 2 (Ubuntu) with the NVIDIA driver for WSL, and do the Linux steps in WSL. The make targets need a POSIX shell.
- About 40 GB of free disk on the computer with the GPU: the download (17.3 GB) and the text branch of the model (16.1 GB).
- Your own Hugging Face account on the computer with the GPU. Accept the conditions of the model on https://huggingface.co/swiss-ai/Apertus-v1.5-8B yourself. If you are not logged in, `make setup` stops before the download of the model and gives the steps. Run `.venv/bin/hf auth login` in `track_2a/` with your own token, then run `make setup` again. No code of this repository prints or stores your Hugging Face token. The `hf` command and the Hugging Face library read it for the download. The head files are public and need no token.

A normal chat service of Apertus (for example Public AI, Swisscom or a Hugging Face inference endpoint) does not work for this step. Such a service gives text. The heads need the hidden state after layer 20 at the last token of each question. Only a run of the model with the code of this project gives this state.

## What `make setup-apertus` does (one time, part 3 of `make setup`)

1. It checks the computer: the Python of `make setup-pdf`, the memory, the GPU and the free disk. With no GPU, it stops and names the ways out. In `make setup`, it writes a note in place of the stop and downloads no model.
2. On a Mac with Apple silicon, it installs MLX 0.32.3.
3. It downloads `swiss-ai/Apertus-v1.5-8B` at a pinned revision (about 17.3 GB). `tools/text_branch.py` cuts out the text branch (16.1 GB) and checks it. A text branch that is already there gets a full SHA-256 check (`APERTUS_VERIFY=0` skips it).
4. It downloads the 3 head files from the Hugging Face repository `JonathanKovatsch/parlpdfech-heads` at a pinned revision and checks their SHA-256 (`tools/apertus/heads.sha256`).
5. It writes `data/apertus/setup.json`. `make convert` reads this file.

The download stays in the Hugging Face cache (about 17 GB). `hf cache` can remove it; the tool deletes nothing.

## If `make setup` found no GPU: `make gpu`

`make gpu` shows what this computer has (system, memory, Apple silicon, NVIDIA GPU), the check of the backend, the state of the Apertus step and the next command. It changes nothing and downloads nothing. With no GPU, it names 3 ways: install the driver of the GPU (NVIDIA: the driver and torch with CUDA), then `make gpu` again; a GPU of another computer (way 2); or `APERTUS=0` for the code rules only. If the GPU has too little memory or no bf16, way 1 says that it is not possible with this GPU.

- `make gpu BACKEND=mlx` (or `cuda`, `mps`) sets up the Apertus step with this backend, for example after you installed a driver. First it checks the backend. If the check fails, it stops with a message, and nothing is downloaded. Else it runs `make setup-apertus APERTUS_BACKEND=<backend>`. One exception: on a Mac with Apple silicon and 32 GB, `BACKEND=mlx` continues when only the MLX packages are absent, because `make setup-apertus` installs them. `BACKEND=cpu` is very slow: use it only for checks.
- `make gpu URL=http://127.0.0.1:8090` checks a read-out service of way 2: its health and its model fingerprint. If the heads are absent on this computer, it runs `make setup-apertus APERTUS_MODEL=none`. Then it gives the command `make convert APERTUS_URL=...`. The token stays in the environment variable `APERTUS_TOKEN`. `make gpu` does not show it and stores no address.

Tested on 16.10.2026, only on one Mac (Apple M4, 32 GB): the report with no setup, with the heads only and with MLX; `BACKEND=cuda` with no NVIDIA GPU (a message, no download); `URL=` with no service and with `make serve-apertus` on this one computer (only the health request). For Linux and an NVIDIA GPU, `make test` checks the messages only with fake commands (`tools/check_gpu.sh`).

## Way 1: all on the computer with the GPU

```bash
git clone https://github.com/jkovatsch/ParlPDFeCH.git
cd ParlPDFeCH/track_2a
make setup            # one time; needs pdftotext and jq; the model (your Hugging Face account) and the heads
make convert PDF=<file or URL>
```

The PDF, the read-out, the heads and the record stay on this one computer.

## Way 2: the read-out on another computer

The GPU computer runs a small read-out service with the same code. Your own computer reads the PDF, makes the questions and sends their text to the service. The service answers with the states of layer 20. The heads, the writer and the validator run on your own computer. The fixed run of 13.10.2026 had the same split: one H100 GPU made the states (torch CUDA, bf16), and a Mac applied the heads ([../technical_report.md](../technical_report.md), chapter 3).

On the GPU computer (Linux with an NVIDIA GPU, or a Mac):

```bash
git clone https://github.com/jkovatsch/ParlPDFeCH.git
cd ParlPDFeCH/track_2a
make setup            # one time; needs pdftotext and jq; the model (your Hugging Face account) and the heads
make serve-apertus    # listens on 127.0.0.1:8090 (this computer only); Ctrl-C ends it
```

On your own computer (no GPU needed):

```bash
cd ParlPDFeCH/track_2a
make setup                                            # with no GPU here: a note, and no model download
make setup-apertus APERTUS_MODEL=none                 # the heads only, no model download
ssh -N -L 8090:127.0.0.1:8090 <user>@<GPU computer>   # the tunnel; keep it open in a second terminal
make convert APERTUS_URL=http://127.0.0.1:8090 PDF=<file or URL>
```

- If another program uses the port 8090 on your own computer, take another local port: `ssh -N -L 18090:127.0.0.1:8090 <user>@<GPU computer>`, then `APERTUS_URL=http://127.0.0.1:18090`. On the GPU computer, `make serve-apertus PORT=<n>` sets the port of the service.
- Privacy: the text of each PDF goes to the GPU computer. The terminal says so at the start of `make convert`. Use only a computer that may get this text.
- With `APERTUS_URL`, `make convert` takes the service first. If the service does not answer, `APERTUS=1` stops with a message, and `APERTUS=auto` writes a note and uses the code rules only.
- The service reads out one PDF at a time. If it is busy, your computer asks again every 5 s, for at most `APERTUS_BUSY_WAIT` seconds (default 120). Then the PDF gets the code rules only (`remote_busy`).
- `APERTUS_TIMEOUT` (default 1800 s) is the time limit of one PDF. The read-out ends at the latest 90 s before it, so that a record is still written.
- Before each PDF, your computer asks the service for its model fingerprint. It refuses a service with another model than the model of the heads.
- The record names the backend `remote:<backend of the service>` (for example `remote:cuda`) and only the host name of the URL.

### A token

The service listens on `127.0.0.1` by default. Then only programs on the GPU computer reach it, and the ssh tunnel brings your requests there. A token also protects it from other users of the GPU computer. `HOST=<address>` lets the service listen on another address; then it starts only with a token of 32 characters or more.

```bash
# on the GPU computer: make a token one time, outside the project folder
openssl rand -hex 32 > ~/.apertus-token && chmod 600 ~/.apertus-token
APERTUS_TOKEN="$(cat ~/.apertus-token)" make serve-apertus
# on your own computer: the same token (for example copied with scp), in the environment only
APERTUS_TOKEN="$(cat ~/.apertus-token)" make convert APERTUS_URL=http://127.0.0.1:8090 PDF=<file>
```

White space at the start and at the end of the token is removed. A token with another character than visible ASCII is refused before a request (`remote_token_bad`). No message shows the token.

### Rules of the service

- With a token, each request needs it (header `Authorization: Bearer`). A wrong token gives HTTP 401.
- One PDF at a time. A second request gets HTTP 503.
- A body limit of 8 MiB, and a time limit of 1500 s for one read-out (HTTP 504).
- The log has one line for each request: time, address, status, counts and seconds. It has no text of a PDF and no token. The service keeps no text after its answer.
- The service speaks plain HTTP. Between 2 computers, use the ssh tunnel. `make convert` refuses plain `http://` to another computer, unless `APERTUS_ALLOW_HTTP=1` (only for a private network, for example WireGuard).
- `APERTUS_IDLE_EXIT=<seconds>` ends the service after that time with no request. `APERTUS_MAX_REQUESTS=<n>` ends it after n read-outs. This ends only the service: a rented machine costs money until you stop it at its provider.

### Messages of way 2

| Code | Meaning |
|---|---|
| `remote_unreachable` | No service answers at `APERTUS_URL`: start `make serve-apertus` and the tunnel. |
| `remote_unauthorized` | HTTP 401: `APERTUS_TOKEN` is absent or is not the token of the service. |
| `remote_busy` | The service reads out another PDF. Try again when it is free. |
| `remote_fingerprint_differs` | The service has another model. Run `make setup-apertus` on the GPU computer. |
| `remote_plain_http` | Plain `http://` to another computer: use the tunnel (`http://127.0.0.1:<port>`) or `https://`. |
| `remote_token_bad` | `APERTUS_TOKEN` has a character that is not visible ASCII. Set it again. |
| `remote_time_limit`, `remote_timeout` | The read-out took too long. |
| `remote_bad_answer` | An answer failed a check of its form or of its SHA-256. |

## What the terminal shows

- The table has one row for each field, also for a field with no value. The columns are Field, Value, Prob., Status, Source and Page.
- Each value row gives the source: `rules` or `Apertus`. With a GPU of another computer, the first line of the run names that computer. If `APERTUS_URL` has the host `127.0.0.1` (a service on this computer, or the end of an ssh tunnel), it names the service at that address. The number in the column Prob. is the calibrated probability of the tier, from the development documents.
- The table needs a terminal of 100 columns. In a narrower terminal, a grey line says so.
- The lines below the table start with `Apertus`. The line `type:` gives the class of the type head. Each other line gives the block that a head picked for one field, with the head probability: the output of the head for this PDF. This is a different number.
- A head probability within 0.10 of a threshold gets the mark `*`. A gap of less than 0.10 to the second class (`Q1`) or to the second block (`Q2`) also gets it. Then another computer can give another decision.
- A row with the status `below` is an Apertus suggestion below the entry limit. The rules found no value or a weak value, and the head picked a block with a head probability of 0.50 or more. On the development documents, values of this kind were too few or too often different from OpenParlData. The row gives the value, the probability of its tier and the page. The value is not in the eCH-0295 record. Of the RDF files, only the values file has it (`values.ttl`, class `pvl:Suggestion`). With fewer than 30 development documents (the same limit as `make view`), the row also gives `n` (for example `values file n=5`): the number is not stable. `make view` shows these suggestions in a separate table, with dashed boxes on the page.
- A row with the status `weak` (a rule value below 0.50) or `–` (the note `addressed body`: the body that a proposal addresses) is only in the label file, not in the eCH-0295 record.
- A stored result of an earlier version has no suggestion. If such a result has a field below the entry limit, a grey line says that `AGAIN=1` converts it again with the suggestions.
- `VERBOSE=1` also shows the full path or URL, the SHA-256 and the record id. It also shows the details of the read-out and each full value that the table cuts. Colours are only for a terminal. `NO_COLOR=1` gives no colours.
- The first author from Apertus: the head picks the block, and code reads the name from that block.
- The affair type from Apertus: code finds the first type word of that type in reading order and gives its page and span ("place found by code, decision by Apertus"). If that word is in a list of 2 or more type words (for example boxes to tick on a form), the terminal says so: the place shows the word, not the choice.
- With no type word in the text, the type is not written. The terminal gives the reason "no type word of this type in the text: not written".

## Same decisions as on the H100 GPU?

The heads were fitted on states of torch CUDA bf16 from one H100 GPU. Other kernels (MLX, torch MPS, another GPU) give other bf16 noise.

- The read-out with MLX on one Mac used the stored text blocks of 31 development documents. It gave the same 21 Apertus decisions as the stored H100 states. No field differed.
- The largest change of a head probability was 0.097 for the type (one document: 0.7988 on the H100, 0.7021 on MLX, both below the threshold 0.80) and 0.055 for a first-author block.
- The margin of the mark `*` (near a threshold) is 0.10 for each backend that runs the model. It covers the largest change measured on MLX and on torch MPS (0.073 on 14 documents). CUDA was not measured with this code. The mark is a warning, not a guarantee.

## What was tested

Tested on 16.10.2026, only on one Mac (Apple M4, 32 GB):

- The read-out with MLX on 31 development documents: the same decisions as the stored H100 states (previous chapter). torch with MPS and on the CPU on one sample: the same decisions.
- `make convert` with the Apertus step (MLX) on 3 samples and 4 development PDFs: all records valid. In the 3 samples, Apertus wrote no value into the eCH-0295 record.
- `make serve-apertus` and `make convert APERTUS_URL=...`, both on this one computer (`127.0.0.1`), on 3 development PDFs, 2 of them with a token: the values were equal to the local run. A wrong token gave HTTP 401. The log had no text and no token. `HOST=0.0.0.0` with no token did not start.
- `make convert APERTUS=0` on the 3 samples: the same records as before the Apertus step.
- `make test` runs 29 checks of the service and of the client, with a backend that loads no model. They include the token rules, 401, 503 and the fingerprint. In these checks, the client refused a service with another model fingerprint before it sent text.
- `make setup-apertus`: the 3 head files came from Hugging Face at the pinned revision, and their SHA-256 agreed. The model came from the local Hugging Face cache.
- `make setup` in a clone: with MLX, PASS. With `APERTUS_BACKEND=cuda`, as on a computer with no GPU: a note, no stop, then PASS.
- The suggestions below the entry limit, with MLX in a clone: 3 samples and 5 development PDFs gave 8 valid records, 5 of them with suggestions. The files `ech.ttl` and `ech.yaml` were byte-equal to a run of the same PDFs before this change. The values file, the manifest and the view gave the same suggestions. `make view` showed them in a headless browser, in English and in German.
- After the changes of the terminal texts: 3 samples and 2 development PDFs again with MLX. `ech.ttl`, `ech.yaml` and `values.ttl` were byte-equal to the run before. With `APERTUS=auto` and `APERTUS_BACKEND=cuda` (no such GPU on the Mac), 4 stored Apertus results stayed and the terminal showed them.

Not tested: an NVIDIA GPU with this code; Linux and Windows (WSL 2); a second computer, the ssh tunnel and `https`; a scan with OCR; the model download of `make setup-apertus` (17.3 GB); `make setup` on a computer with no GPU, and its stop with no Hugging Face login. The states of the fixed run came from torch CUDA on one H100 in the cloud. On an NVIDIA GPU, the read-out uses the engine of the fixed run (`app/layout/src/m10_vm_states.py`).

## Limits

- `make view` of a record with Apertus values shows a notice that Apertus read-out heads chose these values. Each such value has the source text "Chosen by: an Apertus read-out head for values". The view data were checked against the schema of the view. The page of such a record was opened only in a headless browser.
- An Apertus type with no type word in the text is not written. On the development documents, this was so for 33 of 128 types from `Q1`.
- Each PDF loads the model again (about 8 to 11 s with MLX). The service of way 2 loads it one time.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 16.10.2026, and an AI agent made it shorter on the same day. After that, an AI agent changed the steps to the one command `make setup`. Then an AI agent added the suggestions below the entry limit, and an AI agent changed the terminal texts after a check by AI agents.

# The GPU for the Apertus step

The Apertus step of `make convert` runs Apertus-v1.5-8B (bf16) on each PDF. Linear heads read its hidden state after layer 20 and decide 2 values: the affair type, if the code rules found no type, and the first author, if the rule value is absent or weak. An Apertus value enters the record only with a head probability of 0.80 or more. No text comes out. This step needs a GPU. The GPU can be on this computer or on another computer, for example a rented GPU in the cloud. With no GPU, `make convert` writes a note and makes the record with the code rules only. `APERTUS=0` gives the code rules only.

## What you need

- A GPU: a Mac with Apple silicon and 32 GB memory or more (backend `mlx`), or an NVIDIA GPU with 24 GB memory or more (backend `cuda`). The model needs 16.1 GB. A Mac with less than 32 GB or an NVIDIA GPU with less than 20 GiB gets the reason `memory_too_small`. Then `make setup-apertus` stops before the download. `memory_low` means that too little memory is free now: close other programs and try again.
- macOS or Linux. On Windows, use WSL 2 (Ubuntu) with the NVIDIA driver for WSL, and do the Linux steps in WSL. The make targets need a POSIX shell.
- About 40 GB of free disk on the computer with the GPU: the download (17.3 GB) and the text branch of the model (16.1 GB).
- Your own Hugging Face account on the computer with the GPU. Accept the conditions of the model on https://huggingface.co/swiss-ai/Apertus-v1.5-8B yourself. Then, in `track_2a/` after `make setup-pdf`, run `.venv/bin/hf auth login` with your own token. No code of this repository prints or stores your Hugging Face token. The `hf` command and the Hugging Face library read it for the download. The head files are public and need no token.

A normal chat service of Apertus (for example Public AI, Swisscom or a Hugging Face inference endpoint) does not work for this step. Such a service gives text. The heads need the hidden state after layer 20 at the last token of each question. Only a run of the model with the code of this project gives this state.

## What `make setup-apertus` does (one time)

1. It checks the computer: the Python of `make setup-pdf`, the memory, the GPU and the free disk. With no GPU, it stops and names the ways out.
2. On a Mac with Apple silicon, it installs MLX 0.32.3.
3. It downloads `swiss-ai/Apertus-v1.5-8B` at a pinned revision (about 17.3 GB). `tools/text_branch.py` cuts out the text branch (16.1 GB) and checks it. A text branch that is already there gets a full SHA-256 check (`APERTUS_VERIFY=0` skips it).
4. It downloads the 3 head files from the Hugging Face repository `JonathanKovatsch/parlpdfech-heads` at a pinned revision and checks their SHA-256 (`tools/apertus/heads.sha256`).
5. It writes `data/apertus/setup.json`. `make convert` reads this file.

The download stays in the Hugging Face cache (about 17 GB). `hf cache` can remove it; the tool deletes nothing.

## Way 1: all on the computer with the GPU

```bash
git clone https://github.com/jkovatsch/ParlPDFeCH.git
cd ParlPDFeCH/track_2a
make setup
make setup-pdf        # needs the command pdftotext
make setup-apertus    # the model (your Hugging Face account) and the heads
make convert PDF=<file or URL>
```

The PDF, the read-out, the heads and the record stay on this one computer.

## Way 2: the read-out on another computer

The GPU computer runs a small read-out service with the same code. Your own computer reads the PDF, makes the questions and sends their text to the service. The service answers with the states of layer 20. The heads, the writer and the validator run on your own computer. The fixed run of 13.10.2026 had the same split: one H100 GPU made the states (torch CUDA, bf16), and a Mac applied the heads ([../technical_report.md](../technical_report.md), chapter 3).

On the GPU computer (Linux with an NVIDIA GPU, or a Mac):

```bash
git clone https://github.com/jkovatsch/ParlPDFeCH.git
cd ParlPDFeCH/track_2a
make setup
make setup-pdf        # needs the command pdftotext
make setup-apertus
make serve-apertus    # listens on 127.0.0.1:8090 (this computer only); Ctrl-C ends it
```

On your own computer (no GPU needed):

```bash
cd ParlPDFeCH/track_2a
make setup
make setup-pdf
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

- Each value row gives the source: `rules`, `Apertus` or `Apertus (remote GPU)`. The number is the calibrated probability of the tier, from the development documents.
- The lines "Apertus type (Q1)" and "Apertus first author (Q2)" give the head probability: the output of the head for this PDF. This is a different number.
- A head probability within 0.10 of a threshold gets the mark `near`. A gap of less than 0.10 to the second class (`Q1`) or to the second block (`Q2`) also gets it. Then another computer can give another decision.
- The first author from Apertus: the head picks the block, and code reads the name from that block.
- The affair type from Apertus: code finds the first type word of that type in reading order and gives its page and span ("place found by code, decision by Apertus"). If that word is in a list of 2 or more type words (for example boxes to tick on a form), the terminal says so: the place shows the word, not the choice.
- With no type word in the text, the type is not written. The terminal gives the reason "no evidence in the text (not written)".

## Same decisions as on the H100 GPU?

The heads were fitted on states of torch CUDA bf16 from one H100 GPU. Other kernels (MLX, torch MPS, another GPU) give other bf16 noise.

- The read-out with MLX on one Mac used the stored text blocks of 31 development documents. It gave the same 21 Apertus decisions as the stored H100 states. No field differed.
- The largest change of a head probability was 0.097 for the type (one document: 0.7988 on the H100, 0.7021 on MLX, both below the threshold 0.80) and 0.055 for a first-author block.
- The margin of the mark `near` is 0.10 for each backend that runs the model. It covers the largest change measured on MLX and on torch MPS (0.073 on 14 documents). CUDA was not measured with this code. The mark is a warning, not a guarantee.

## What was tested

Tested on 16.10.2026, only on one Mac (Apple M4, 32 GB):

- The read-out with MLX on 31 development documents: the same decisions as the stored H100 states (previous chapter). torch with MPS and on the CPU on one sample: the same decisions.
- `make convert` with the Apertus step (MLX) on 3 samples and 4 development PDFs: all records valid. In the 3 samples, Apertus wrote no value.
- `make serve-apertus` and `make convert APERTUS_URL=...`, both on this one computer (`127.0.0.1`), on 3 development PDFs, 2 of them with a token: the values were equal to the local run. A wrong token gave HTTP 401. The log had no text and no token. `HOST=0.0.0.0` with no token did not start.
- `make convert APERTUS=0` on the 3 samples: the same records as before the Apertus step.
- `make test` runs 29 checks of the service and of the client, with a backend that loads no model. They include the token rules, 401, 503 and the fingerprint. In these checks, the client refused a service with another model fingerprint before it sent text.
- `make setup-apertus`: the 3 head files came from Hugging Face at the pinned revision, and their SHA-256 agreed. The model came from the local Hugging Face cache.

Not tested: an NVIDIA GPU with this code; Linux and Windows (WSL 2); a second computer, the ssh tunnel and `https`; a scan with OCR; the model download of `make setup-apertus` (17.3 GB). The states of the fixed run came from torch CUDA on one H100 in the cloud. On an NVIDIA GPU, the read-out uses the engine of the fixed run (`app/layout/src/m10_vm_states.py`).

## Limits

- `make view` of a record with Apertus values shows a notice that Apertus read-out heads chose these values. Each such value has the source text "Chosen by: an Apertus read-out head for values". The view data were checked against the schema of the view. The page of such a record was not opened in a browser.
- An Apertus type with no type word in the text is not written. On the development documents, this was so for 33 of 128 types from `Q1`.
- Each PDF loads the model again (about 8 to 11 s with MLX). The service of way 2 loads it one time.

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- AI agents (Claude Opus 5.5) wrote this text on 16.10.2026, and an AI agent made it shorter on the same day.

#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: 'make serve-apertus' (the Makefile calls this file). Orchestration only.
#
# Starts the Apertus read-out service (app/worker/apertus_serve.py) on a computer with a GPU: this computer,
# another computer, or a rented GPU in the cloud. 'make convert' on your own computer then uses it with
# APERTUS_URL (docs/apertus-gpu.md, way 2). The service loads Apertus-v1.5-8B one time, answers with the states
# of layer 20 for the prompt texts of one document at a time, and keeps no text.
#   1. checks the code layout of app/layout/ (as 'make convert');
#   2. takes the model folder and the Python of 'make setup-apertus' (data/apertus/setup.json), or
#      APERTUS_MODEL_DIR and APERTUS_PYTHON;
#   3. starts the service. It binds 127.0.0.1 (this computer only) unless APERTUS_HOST is another address;
#      another address needs a token in the environment variable APERTUS_TOKEN (32 characters or more). This file
#      never reads, prints or stores the token: the service reads it from the environment.
#
# Environment (the Makefile sets it): PYTHON (the Python of .venv/), APERTUS_PYTHON, APERTUS_MODEL_DIR,
# APERTUS_BACKEND (auto, mlx, cuda, mps, cpu), APERTUS_HOST (default 127.0.0.1), APERTUS_PORT (default 8090),
# APERTUS_MAX_REQUESTS and APERTUS_IDLE_EXIT (the service ends by itself after N read-outs or S idle seconds;
# empty: no end), APERTUS_REQUEST_TIMEOUT (seconds for one read-out, default 1500).
# Tested only on one Mac (Apple M4, 32 GB) on 16.10.2026, with the service and the client on this one computer.
# CUDA, Linux, Windows and a second computer are NOT tested.

set -eu
umask 022

HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
APP=$TRACK/app
PY=${PYTHON:-python3}
APY=${APERTUS_PYTHON:-$PY}
MODEL_DIR=${APERTUS_MODEL_DIR:-data/apertus/apertus-v1.5-8b-text-bf16}
BACKEND=${APERTUS_BACKEND:-auto}
HOST=${APERTUS_HOST:-127.0.0.1}
PORT=${APERTUS_PORT:-8090}
MAX_REQUESTS=${APERTUS_MAX_REQUESTS:-}
IDLE_EXIT=${APERTUS_IDLE_EXIT:-}
REQUEST_TIMEOUT=${APERTUS_REQUEST_TIMEOUT:-1500}
SETUP_JSON=$TRACK/data/apertus/setup.json
GPU_DOC=docs/apertus-gpu.md

err() { printf 'ERROR: %s\n' "$*" >&2; }
note() { printf 'NOTE: %s\n' "$*" >&2; }
abs() { case $1 in /*) printf '%s\n' "$1" ;; *) printf '%s\n' "$TRACK/$1" ;; esac; }
num() { case $2 in ''|*[!0-9]*) err "$1=$2: give a whole number"; exit 1 ;; esac; }

num APERTUS_PORT "$PORT"
[ -z "$MAX_REQUESTS" ] || num APERTUS_MAX_REQUESTS "$MAX_REQUESTS"
[ -z "$IDLE_EXIT" ] || num APERTUS_IDLE_EXIT "$IDLE_EXIT"
num APERTUS_REQUEST_TIMEOUT "$REQUEST_TIMEOUT"

# 1. the code layout (SHA-256 of each file of app/layout/; the service reads src/m10_vm_states.py there)
if ! { [ -x "$PY" ] || command -v "$PY" >/dev/null 2>&1; }; then
  err "the Python $PY is absent. Run 'make setup', 'make setup-pdf' and 'make setup-apertus' first."
  exit 1
fi
if ! (cd "$APP" && "$PY" -B worker/layout.py --check --out layout) >/dev/null 2>&1; then
  err "the code layout of app/layout/ differs from its list (app/worker/layout.py --check)."
  exit 1
fi

# 2. the model folder and the Python of the read-out
if [ -f "$SETUP_JSON" ] && command -v jq >/dev/null 2>&1; then
  sd=$(jq -r '.model.text_branch_dir // ""' "$SETUP_JSON" 2>/dev/null || true)
  if [ -n "$sd" ] && [ -f "$sd/config.json" ]; then MODEL_DIR=$sd; fi
  sp=$(jq -r '.python // ""' "$SETUP_JSON" 2>/dev/null || true)
  if [ "$APY" = "$PY" ] && [ -n "$sp" ] && [ -x "$sp" ]; then APY=$sp; fi
fi
MODEL_DIR=$(abs "$MODEL_DIR")
if [ ! -f "$MODEL_DIR/config.json" ]; then
  err "no model folder at $MODEL_DIR. On this GPU computer run 'make setup', 'make setup-pdf' and 'make setup-apertus' first ($GPU_DOC)."
  exit 1
fi
if ! { [ -x "$APY" ] || command -v "$APY" >/dev/null 2>&1; }; then
  err "the Python $APY of the read-out is absent: run 'make setup-apertus'."
  exit 1
fi

# 3. the service (exec: Ctrl-C reaches it; the token goes to it through the environment only)
set -- --root layout --model-dir "$MODEL_DIR" --backend "$BACKEND" --host "$HOST" --port "$PORT" \
  --request-timeout "$REQUEST_TIMEOUT"
[ -z "$MAX_REQUESTS" ] || set -- "$@" --max-requests "$MAX_REQUESTS"
[ -z "$IDLE_EXIT" ] || set -- "$@" --idle-exit "$IDLE_EXIT"
printf 'apertus-serve: model %s, backend %s, address %s:%s (docs/apertus-gpu.md). Ctrl-C ends it.\n' \
  "$MODEL_DIR" "$BACKEND" "$HOST" "$PORT"
cd "$APP"
exec "$APY" -I -B worker/apertus_serve.py "$@"

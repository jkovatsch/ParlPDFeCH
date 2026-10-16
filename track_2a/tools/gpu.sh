#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: 'make gpu' (the Makefile calls this file). Orchestration only.
#
# The GPU of the Apertus step of 'make convert'. If 'make setup' found no GPU, this file shows why and the ways to
# a GPU. After a manual change (for example a new driver, or a GPU of another computer), it sets up the step:
#   make gpu                  a report: the computer (system, memory, Apple silicon, NVIDIA GPU), the check of
#                             app/worker/apertus_states.py (backend, model fingerprint, memory; no model load), the
#                             record data/apertus/setup.json, the SHA-256 of the 3 head files, and a verdict with
#                             the next command. It changes nothing and downloads nothing. With APERTUS_URL in the
#                             environment, it also asks that service for its health, as 'make convert' does.
#   make gpu BACKEND=<name>   sets up the Apertus step with this backend: auto, mlx, cuda or mps (cpu: very slow,
#                             for checks only). First the check of this backend (no model load). If it fails: a
#                             message with the ways, an exit code that is not 0, and no download. Else 'make
#                             setup-apertus APERTUS_BACKEND=<name>' (it downloads the model if it is absent: about
#                             17.3 GB, your own Hugging Face account), then the report.
#   make gpu URL=<address>    a GPU of another computer ('make serve-apertus' there; docs/apertus-gpu.md, way 2):
#                             checks the service (GET /v1/health and the model fingerprint, with the backend remote
#                             of apertus_states.py check), sets up the heads here if they are absent ('make
#                             setup-apertus APERTUS_MODEL=none'), and prints the command 'make convert APERTUS_URL=...'.
# This file never reads, prints or stores a token: APERTUS_TOKEN goes from the environment to apertus_states.py
# only. It stores no address: 'make convert' needs APERTUS_URL each time.
#
# Environment (the Makefile sets it): PYTHON (the Python of .venv/), APERTUS_PYTHON, APERTUS_MODEL_DIR,
# APERTUS_BACKEND (the backend of the report, as for 'make convert'), GPU_MAKE (the make command for 'make
# setup-apertus'), NO_COLOR (no colors; an output to a pipe or to a file also has no colors).
# Arguments: --backend <name> and --url <address> (BACKEND and URL of the make command line; empty: not given).
# Exit codes: the report 0. BACKEND and URL: 0 ready; 1 error; else the exit code of apertus_states.py check
# (5 no GPU or backend absent, 6 memory, 8 a reason of the service) or of 'make setup-apertus'.
# Tested only on one Mac (Apple M4, 32 GB) on 16.10.2026. Linux, Windows and an NVIDIA GPU are NOT tested: 'make
# test' checks their messages only with fake commands (tools/check_gpu.sh).

set -eu
umask 022

HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
APP=$TRACK/app
PY=${PYTHON:-python3}
APY=${APERTUS_PYTHON:-$PY}
MODEL_DIR_DEFAULT=${APERTUS_MODEL_DIR:-data/apertus/apertus-v1.5-8b-text-bf16}
REPORT_BACKEND=${APERTUS_BACKEND:-auto}
MAKE_CMD=${GPU_MAKE:-make}
SETUP_JSON=$TRACK/data/apertus/setup.json
HEADS_SUMS=$HERE/apertus/heads.sha256
LAYOUT=$HERE/apertus/text_branch_layout.json
GPU_DOC=docs/apertus-gpu.md
# 32 GiB: the rule MIN_RAM_TOTAL_APPLE of app/worker/apertus_states.py (a Mac for MLX).
MIN_MAC_BYTES=34359738368
SERVICE_EXAMPLE=http://127.0.0.1:8090
# The sentences of apertus_states.py that name the ways out; this file gives its own list of ways.
STRIP='sub(" ?Use a GPU in the cloud \\(see docs/apertus-gpu\\.md\\), or APERTUS=0 for code rules only\\."; "")
  | sub(" ?APERTUS_BACKEND=cpu forces the CPU \\(very slow, for checks only\\)\\."; "")'
# The reason of a forced backend only, for example "torch finds no NVIDIA GPU (CUDA)".
WHY_JQ="(.message // \"\") | $STRIP | sub(\"^APERTUS_BACKEND=[a-z]+: not available on this computer \\\\(\"; \"\") | sub(\"\\\\)\\\\.\$\"; \"\")"
# The folder of HEADS_DIR (a local folder with the 3 head files) as the user gave it. This file does not change
# HEADS_DIR: the call of 'make setup-apertus' gets it as it is.
USER_HEADS_DIR=${HEADS_DIR:-}

BACKEND=
URL=
while [ $# -gt 0 ]; do
  case $1 in
    --backend|--url)
      [ $# -ge 2 ] || { printf 'ERROR: %s needs a value\n' "$1" >&2; exit 1; }
      if [ "$1" = --backend ]; then BACKEND=$2; else URL=$2; fi
      shift 2 ;;
    *) printf 'ERROR: unknown argument (tools/gpu.sh takes --backend and --url)\n' >&2; exit 1 ;;
  esac
done

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != dumb ]; then
  ESC=$(printf '\033')
  BOLD="$ESC[1m"; GREEN="$ESC[32m"; YELLOW="$ESC[33m"; RED="$ESC[31m"; OFF="$ESC[0m"
else
  BOLD=; GREEN=; YELLOW=; RED=; OFF=
fi

say() { printf '%s\n' "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; }
note() { printf 'NOTE: %s\n' "$*" >&2; }
# One row of the report: a label and a text. crow: the text in a color.
row() { printf '  %-9s  %s\n' "$1" "$2"; }
crow() { printf '  %-9s  %s%s%s\n' "$1" "$2" "$3" "$OFF"; }
# A text from another program for the terminal: no control characters.
plain() { printf '%s' "$1" | LC_ALL=C tr -d '\000-\010\013-\037\177'; }
# A value as one word for sh (single quotes if it has other characters than these).
word() {
  case $1 in
    *[!A-Za-z0-9:/._~%@+=,-]*) printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")" ;;
    *) printf '%s' "$1" ;;
  esac
}
abs() { case $1 in /*) printf '%s\n' "$1" ;; *) printf '%s\n' "$TRACK/$1" ;; esac; }
rel() { case $1 in "$TRACK"/*) printf '%s' "${1#"$TRACK"/}" ;; *) printf '%s' "$1" ;; esac; }
jq_of() { printf '%s' "$1" | jq -r "$2" 2>/dev/null | LC_ALL=C tr -d '\000-\010\013-\037\177' || true; }
sums_ok() {
  if command -v shasum >/dev/null 2>&1; then (cd "$1" && shasum -a 256 -c "$HEADS_SUMS") >/dev/null 2>&1
  else (cd "$1" && sha256sum -c "$HEADS_SUMS") >/dev/null 2>&1; fi
}

command -v jq >/dev/null 2>&1 || { err "the command jq is absent (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."; exit 1; }

# ------------------------------------------------------------------------------------------------ the facts
# The computer, with no Python: OS, ARCH, RAM (bytes), RAM_GIB, NV (none, driver, smi_error, device) and NV_TXT.
facts() {
  OS=$(uname -s); ARCH=$(uname -m)
  case $OS in
    Darwin) RAM=$(sysctl -n hw.memsize 2>/dev/null || echo 0) ;;
    Linux) RAM=$(awk '/^MemTotal:/ { printf "%.0f", $2 * 1024 }' /proc/meminfo 2>/dev/null || echo 0) ;;
    *) RAM=0 ;;
  esac
  case $RAM in ''|*[!0-9]*) RAM=0 ;; esac
  RAM_GIB=$(awk -v b="$RAM" 'BEGIN { printf "%.0f", b / 1073741824 }')
  NV=none; NV_TXT=none; NV_CUDA=
  if command -v nvidia-smi >/dev/null 2>&1; then
    q=$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null | head -n 1 || true)
    if [ -n "$q" ]; then
      NV=driver; NV_TXT="$(plain "$q") (name, memory, driver)"
      NV_CUDA=$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: *\([0-9.]*\).*/\1/p' | head -n 1 || true)
    else
      NV=smi_error; NV_TXT="nvidia-smi is there, but it shows no GPU (the driver does not start)"
    fi
  elif [ "$OS" = Linux ] && command -v lspci >/dev/null 2>&1 && lspci 2>/dev/null | grep -qi nvidia; then
    NV=device; NV_TXT="a device is there (lspci), but no driver (no nvidia-smi)"
  fi
}

# The record of 'make setup-apertus': ST (none, bad, heads, model), REC_MODEL, REC_PY, REC_BACKEND, REC_HEADS_DIR,
# HEADS_SHORT, HEADS_OK (yes: the 3 files have the SHA-256 of tools/apertus/heads.sha256). The names are not the
# names of make variables (for example HEADS_DIR): an exported variable goes on to 'make setup-apertus'.
# A record with another structure (for example "model": "x") is ST=bad.
read_setup() {
  ST=none; REC_MODEL=; REC_PY=; REC_BACKEND=; REC_HEADS_DIR=; HEADS_SHORT=; HEADS_OK=no
  [ -f "$SETUP_JSON" ] || return 0
  if ! jq -e '.schema == "parlpdfech-apertus-setup/1"
      and ((.model // {}) | type == "object") and ((.model.text_branch_dir // "") | type == "string")
      and ((.heads // {}) | type == "object") and ((.heads.dir // "") | type == "string")
      and ((.heads.source // "") | type == "string") and ((.python // "") | type == "string")
      and ((.backend_check // {}) | type == "object") and ((.backend_check.backend // "") | type == "string")' \
      "$SETUP_JSON" >/dev/null 2>&1; then ST=bad; return 0; fi
  REC_MODEL=$(jq -r '.model.text_branch_dir // ""' "$SETUP_JSON")
  REC_PY=$(jq -r '.python // ""' "$SETUP_JSON")
  REC_BACKEND=$(jq -r '.backend_check.backend // ""' "$SETUP_JSON")
  REC_HEADS_DIR=$(jq -r '.heads.dir // ""' "$SETUP_JSON")
  src=$(jq -r '.heads.source // ""' "$SETUP_JSON")
  case $src in
    hf:*@*) HEADS_SHORT=$(printf '%.7s' "${src##*@}") ;;
    local:*) HEADS_SHORT="from a local folder" ;;
    *) HEADS_SHORT="of an unknown source" ;;
  esac
  if [ -n "$REC_MODEL" ]; then ST=model; else ST=heads; fi
  if [ -n "$REC_HEADS_DIR" ] && [ -d "$REC_HEADS_DIR" ] && sums_ok "$REC_HEADS_DIR"; then HEADS_OK=yes; fi
}

# The Python of the read-out (as tools/convert.sh: the Python of the record if APERTUS_PYTHON is not given), and
# PKG=yes if it has the packages of 'make setup'.
pick_python() {
  if [ "$APY" = "$PY" ] && [ -n "$REC_PY" ] && [ -x "$REC_PY" ]; then APY=$REC_PY; fi
  PKG=no
  if { [ -x "$APY" ] || command -v "$APY" >/dev/null 2>&1; } \
    && "$APY" -I -c "import torch, transformers, tokenizers, numpy" >/dev/null 2>&1; then PKG=yes; fi
}

# The check of the GPU of this computer (apertus_states.py check; no model load). $1: the backend; $2: the model
# folder, or empty (--no-model). APERTUS_URL is removed for this check. Sets CK, CK_RC, CK_REQ (the backend of the
# check: auto, or a forced backend) and the CK_* fields.
local_check() {
  CK_REQ=$1
  if [ -n "$2" ]; then
    CK=$(unset APERTUS_URL; cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend "$1" \
      --model-dir "$2" 2>/dev/null) && CK_RC=0 || CK_RC=$?
  else
    CK=$(unset APERTUS_URL; cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend "$1" \
      --no-model 2>/dev/null) && CK_RC=0 || CK_RC=$?
  fi
  parse_check
}

parse_check() {
  CK_BACKEND=$(jq_of "$CK" '.backend // ""')
  CK_REASON=$(jq_of "$CK" '.reason // ""')
  CK_MSG=$(jq_of "$CK" "(.message // \"\") | $STRIP")
  CK_WHY=$(jq_of "$CK" "$WHY_JQ")
  CK_DEVICE=$(jq_of "$CK" '(.backend // "") as $b | .tests[$b].device // ""')
  CK_GPUNAME=$(jq_of "$CK" '(.backend // "") as $b | .tests[$b].gpu // ""')
  CK_MEMCHECK=$(jq_of "$CK" '.memory.check // ""')
  CK_FREE=$(jq_of "$CK" '.memory.free_bytes // null | if . == null then "" else ((. / 1e8 | floor) / 10 | tostring) end')
  MLX=unknown
  case $(jq_of "$CK" '.tests.mlx.available // "" | tostring') in
    true) MLX=yes ;;
    false) case $(jq_of "$CK" '.tests.mlx.why // ""') in "Python package absent"*) MLX=absent ;; *) MLX=no ;; esac ;;
  esac
  if [ -z "$CK" ]; then
    CK_REASON=error; CK_MSG="the check gave no answer (app/worker/apertus_states.py check)"; CK_WHY=$CK_MSG
    [ "$CK_RC" -ne 0 ] || CK_RC=1
  fi
}

# The check of a read-out service (the backend remote of apertus_states.py check: GET /v1/health and the model
# fingerprint). $1: the address. The token goes on in the environment only. Sets RK_RC and the RK_* fields.
remote_check() {
  RK=$(APERTUS_URL=$1; export APERTUS_URL; cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout \
    --backend auto --no-model 2>/dev/null) && RK_RC=0 || RK_RC=$?
  RK_BACKEND=$(jq_of "$RK" '.backend // ""')
  RK_REASON=$(jq_of "$RK" '.reason // ""')
  RK_MSG=$(jq_of "$RK" "(.message // \"\") | sub(\"^backend remote: \"; \"\") | $STRIP")
  RK_SB=$(jq_of "$RK" '.tests.remote.server_backend // ""')
  RK_DEV=$(jq_of "$RK" '.tests.remote.health.device // ""')
  RK_BUSY=$(jq_of "$RK" '.tests.remote.busy // false | tostring')
  RK_AUTH=$(jq_of "$RK" '.tests.remote.health.auth // ""')
  if [ -z "$RK" ]; then
    RK_REASON=error; RK_MSG="the check gave no answer (app/worker/apertus_states.py check)"
    [ "$RK_RC" -ne 0 ] || RK_RC=1
  elif [ "$RK_RC" -eq 0 ] && [ "$RK_BACKEND" != remote ]; then
    RK_RC=1; RK_REASON=error; RK_MSG="the check did not take the backend remote"
  fi
}

# ------------------------------------------------------------------------------------------------ the rows
header() { say "${BOLD}GPU check · ParlPDFeCH${OFF}"; }

computer_row() {
  t="$OS $ARCH, $RAM_GIB GiB"
  if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ]; then
    case $MLX in
      yes) t="$t · Apple silicon (MLX)" ;;
      absent) t="$t · Apple silicon (MLX not installed)" ;;
      *) t="$t · Apple silicon" ;;
    esac
  fi
  row computer "$t · NVIDIA: $NV_TXT"
}

gpu_row() {
  if [ "$PKG" != yes ]; then
    row GPU "not checked: the Python packages of 'make setup' are absent"
    return 0
  fi
  # The device and the GPU name in brackets, but not a device with the name of the backend (mps, cpu).
  dev=$CK_DEVICE
  [ "$dev" != "$CK_BACKEND" ] || dev=
  if [ -n "$dev" ] && [ -n "$CK_GPUNAME" ]; then dev="$dev, $CK_GPUNAME"; elif [ -z "$dev" ]; then dev=$CK_GPUNAME; fi
  b="$CK_BACKEND${dev:+ ($dev)}"
  case $CK_REASON in
    '') row GPU "$b · memory check ${CK_MEMCHECK:-?}${CK_FREE:+, $CK_FREE GB free}" ;;
    memory_low|memory_too_small) row GPU "$b, but $CK_MSG" ;;
    model_absent|fingerprint_differs) row GPU "$b" ;;
    *)
      # A forced backend (APERTUS_BACKEND=<name>): the message names it.
      if [ "$CK_REQ" != auto ]; then row GPU "$CK_MSG"; else row GPU "none: $CK_MSG"; fi ;;
  esac
}

apertus_row() {
  case $ST in
    none) t="not set up (no record data/apertus/setup.json)" ;;
    bad) t="the record data/apertus/setup.json is not readable" ;;
    heads) t="heads only: no model in the record ('make setup-apertus APERTUS_MODEL=none')" ;;
    model)
      case $CK_REASON in
        ''|memory_low)
          if [ "$CK_REQ" != auto ] && [ -n "$REC_BACKEND" ] && [ "$REC_BACKEND" != "$CK_BACKEND" ]; then
            t="set up: backend $CK_BACKEND (APERTUS_BACKEND=$CK_REQ; the record has $REC_BACKEND), model checked (fingerprint)"
          else
            t="set up: backend $CK_BACKEND, model checked (fingerprint)"
          fi ;;
        model_absent) t="set up, but the model folder $(rel "$REC_MODEL") is absent" ;;
        fingerprint_differs) t="set up, but the model folder $(rel "$REC_MODEL") has another fingerprint" ;;
        *)
          if [ "$CK_REQ" != auto ] && [ "$CK_REASON" = backend_absent ]; then
            t="set up with the backend ${REC_BACKEND:-?}; the forced APERTUS_BACKEND=$CK_REQ is not on this computer (row GPU)"
          else
            t="set up with the backend ${REC_BACKEND:-?}, but this computer has no GPU for it now (row GPU)"
          fi ;;
      esac ;;
  esac
  if [ "$ST" = heads ] || [ "$ST" = model ]; then
    if [ "$HEADS_OK" = yes ]; then t="$t, heads $HEADS_SHORT"
    else t="$t; a head file is absent or has another SHA-256 (tools/apertus/heads.sha256)"; fi
  fi
  if [ "$MFP" = yes ]; then t="$t; the model folder $(rel "$MFP_DIR") is there (fingerprint checked), not in the record"; fi
  row Apertus "$t"
}

# The backend to suggest for 'make gpu BACKEND=...': mlx on a Mac with Apple silicon and 32 GB ('make
# setup-apertus' installs MLX), else the backend of the check.
suggest_backend() {
  if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$RAM" -ge "$MIN_MAC_BYTES" ]; then printf 'mlx'
  else printf '%s' "${CK_BACKEND:-auto}"; fi
}

torch_cuda() {
  "$APY" -I -c 'import torch; print("torch", torch.__version__, "for CUDA", torch.version.cuda or "none (a CPU build)")' \
    2>/dev/null || printf 'torch does not start'
}

# The result of the backend cuda on this computer: CU_REASON (empty: cuda passes) and CU_WHY. From the check of
# the report if it was a check of cuda, else from 'apertus_states.py check --backend cuda' (no model load).
cuda_facts() {
  if [ "$CK_REQ" = cuda ]; then CU_REASON=$CK_REASON; CU_WHY=${CK_WHY:-$CK_MSG}; return 0; fi
  c=$(unset APERTUS_URL; cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend cuda \
    --no-model 2>/dev/null) && cu_rc=0 || cu_rc=$?
  CU_REASON=$(jq_of "$c" '.reason // ""')
  CU_WHY=$(jq_of "$c" "$WHY_JQ")
  if [ -z "$c" ] || { [ "$cu_rc" -ne 0 ] && [ -z "$CU_REASON" ]; }; then
    CU_REASON=error; CU_WHY="the check of the backend cuda gave no answer"
  fi
}

# Way 1 of the list: what can change on this computer.
hint_local() {
  if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$RAM" -lt "$MIN_MAC_BYTES" ]; then
    printf 'not possible on this Mac (%s GiB memory; Apertus needs a Mac with 32 GB)' "$RAM_GIB"; return 0
  fi
  if [ "$CK_REASON" = memory_too_small ]; then printf 'not possible with this GPU (%s)' "$CK_MSG"; return 0; fi
  case $OS:$NV in
    Linux:device) printf "install the NVIDIA driver (then nvidia-smi shows the GPU) and torch with CUDA, then 'make gpu' again" ;;
    Linux:smi_error) printf "install the NVIDIA driver again (nvidia-smi gives no GPU now), then 'make gpu' again" ;;
    Linux:driver)
      # nvidia-smi shows a GPU. The probe of the backend cuda gives the cause: torch, the memory or bf16.
      cuda_facts
      case $CU_REASON:$CU_WHY in
        :*) printf 'the backend cuda passes the check now: make gpu BACKEND=cuda' ;;
        memory_too_small:*|*"has no bf16"*|*"Apertus bf16 needs 24 GB"*)
          printf 'not possible with this GPU (%s)' "$CU_WHY" ;;
        memory_low:*)
          printf "too little GPU memory is free now (%s). Stop other programs on the GPU, then 'make gpu' again" "$CU_WHY" ;;
        *"torch finds no NVIDIA GPU"*)
          printf "nvidia-smi shows the GPU%s, but %s finds no GPU. Install torch with a CUDA version for this driver in .venv/ (or a newer driver), then 'make gpu' again" \
            "${NV_CUDA:+ (the driver supports CUDA $NV_CUDA)}" "$(torch_cuda)" ;;
        *) printf "nvidia-smi shows the GPU, but the backend cuda does not start (%s). Examine the driver and torch, then 'make gpu' again" "$CU_WHY" ;;
      esac ;;
    Darwin:*)
      if [ "$ARCH" = arm64 ]; then printf 'make gpu BACKEND=mlx (this Mac has Apple silicon and 32 GB)'
      else printf 'not possible on this Mac (Apertus needs a Mac with Apple silicon and 32 GB, for MLX)'; fi ;;
    *) printf "install the driver of the GPU (NVIDIA, 24 GB or more: the NVIDIA driver and torch with CUDA), then 'make gpu' again" ;;
  esac
}

# The list of ways to a GPU. $1 (optional): the text of way 1.
ways() {
  w1=${1:-}
  [ -n "$w1" ] || w1="a GPU in this computer: $(hint_local)"
  row ways "1. $w1"
  row "" "2. a GPU of another computer: there 'make setup' and 'make serve-apertus', here an ssh tunnel to it,"
  row "" "   then make gpu URL=$SERVICE_EXAMPLE ($GPU_DOC, way 2)"
  row "" "3. code rules only: make convert APERTUS=0 PDF=<file>"
}

# The command of 'make convert' for the backend of the check: with APERTUS_BACKEND=<name> if the choice 'auto'
# takes another backend. With APERTUS_URL in the environment, the choice 'auto' takes that service first: then a
# forced backend is always in the command.
convert_cmd() {
  if [ "$CHECK_BACKEND" != auto ] && [ -n "${APERTUS_URL:-}" ]; then
    printf 'make convert APERTUS_BACKEND=%s PDF=<file>' "$CK_BACKEND"; return 0
  fi
  if [ "$CHECK_BACKEND" != auto ]; then
    a=$(unset APERTUS_URL; cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend auto \
      --no-model 2>/dev/null | jq -r '.backend // ""' 2>/dev/null || true)
    if [ "$a" != "$CK_BACKEND" ]; then printf 'make convert APERTUS_BACKEND=%s PDF=<file>' "$CK_BACKEND"; return 0; fi
  fi
  printf 'make convert PDF=<file>'
}

ready() { VERDICT=ready; crow verdict "$GREEN" "ready: $1"; }
notready() { VERDICT=not_ready; crow verdict "$YELLOW" "$1"; }

# The verdict of the report for the GPU of this computer.
verdict_local() {
  if [ "$PKG" != yes ]; then
    if [ "$PY" = python3 ] && [ ! -x "$TRACK/.venv/bin/python" ]; then why="the folder .venv/ is absent"
    else why="torch, transformers or tokenizers is absent in $(plain "$APY")"; fi
    notready "not ready: $why. Run 'make setup' one time (with a GPU it also sets up the Apertus step), then 'make gpu' again."
    return 0
  fi
  # A forced backend (APERTUS_BACKEND=<name>) that this computer does not have: the verdict is about that backend
  # only. The report of the choice auto tells what a plain 'make convert' does.
  if [ "$CK_REQ" != auto ] && [ "$CK_REASON" = backend_absent ]; then
    notready "not ready with APERTUS_BACKEND=$CK_REQ: this computer does not have this backend. 'make convert' with it uses the code rules only."
    row "" "Remove APERTUS_BACKEND, or give APERTUS_BACKEND=auto: 'make gpu APERTUS_BACKEND=auto' shows the state and the ways for the choice auto."
    return 0
  fi
  sb=$(suggest_backend)
  gpu_ok=no
  case $CK_REASON in ''|memory_low|model_absent|fingerprint_differs) [ -z "$CK_BACKEND" ] || gpu_ok=yes ;; esac
  case $ST in
    model)
      if [ "$HEADS_OK" != yes ]; then
        notready "not ready: a head file is absent or changed. Run 'make setup-apertus' (it keeps the model), then 'make gpu' again."
      elif [ -z "$CK_REASON" ]; then
        ready "$(convert_cmd)"
        if [ "$CK_BACKEND" = cpu ]; then note "the backend cpu is very slow (many minutes for one page). Use it only for checks."; fi
      elif [ "$CK_REASON" = memory_low ]; then
        notready "not ready now: too little memory is free. Close other programs, then 'make gpu' again. Until then, make convert uses the code rules only."
      elif [ "$CK_REASON" = model_absent ] || [ "$CK_REASON" = fingerprint_differs ]; then
        notready "not ready: the model folder is absent or changed. 'make gpu BACKEND=$CK_BACKEND' sets it up again (a download if it is not in the Hugging Face cache)."
      else
        notready "not ready: no GPU for the Apertus step on this computer now. make convert uses the code rules only."
        ways
      fi ;;
    heads)
      if [ "$gpu_ok" = yes ] && [ "$MFP" = yes ]; then
        notready "not ready on this computer: the record has no model. This computer has a GPU, and the model folder is there: 'make gpu BACKEND=$sb' puts it in the record (no model download; a full SHA-256 check of the folder)."
        row "" "Or a GPU of another computer: make gpu URL=$SERVICE_EXAMPLE ($GPU_DOC, way 2)."
      elif [ "$gpu_ok" = yes ]; then
        notready "not ready on this computer: no model. This computer has a GPU: 'make gpu BACKEND=$sb' sets up the model (download about 17.3 GB; your own Hugging Face account)."
        row "" "Or a GPU of another computer: make gpu URL=$SERVICE_EXAMPLE ($GPU_DOC, way 2)."
      else
        notready "not ready on this computer: no model and no GPU. make convert uses the code rules only."
        ways
      fi ;;
    none|bad)
      if [ "$gpu_ok" = yes ]; then
        if [ "$MFP" = yes ]; then dl="no model download: the model folder is there"
        else dl="it downloads the model if it is absent: about 17.3 GB, your own Hugging Face account"; fi
        notready "not set up. This computer has a GPU: 'make gpu BACKEND=$sb' sets up the Apertus step ($dl; $GPU_DOC)."
      else
        notready "no GPU for the Apertus step on this computer. make convert uses the code rules only."
        ways
      fi ;;
  esac
}

# ------------------------------------------------------------------------------------------------ the forms
# make gpu: the report. $1: the backend of the check. It changes nothing.
report() {
  CHECK_BACKEND=$1; CK_REQ=$1
  facts; read_setup; pick_python
  MFP=no; MFP_DIR=
  CK=; CK_RC=1
  if [ "$PKG" = yes ]; then
    if [ "$ST" = model ]; then local_check "$CHECK_BACKEND" "$REC_MODEL"; else local_check "$CHECK_BACKEND" ""; fi
    if [ "$ST" != model ]; then
      d=$(abs "$MODEL_DIR_DEFAULT")
      want=$(jq -r '.fingerprint // ""' "$LAYOUT" 2>/dev/null || true)
      if [ -f "$d/config.json" ] && [ -n "$want" ] \
        && [ "$("$APY" -I "$HERE/text_branch.py" fingerprint --model-dir "$d" 2>/dev/null || true)" = "$want" ]; then
        MFP=yes; MFP_DIR=$d
      fi
    fi
  else
    parse_check
  fi
  header
  computer_row
  gpu_row
  apertus_row
  # With APERTUS_URL in the environment, 'make convert' (APERTUS_BACKEND=auto) takes that service first.
  if [ -n "${APERTUS_URL:-}" ] && [ "$CHECK_BACKEND" = auto ] && [ "$PKG" = yes ]; then
    remote_check "$APERTUS_URL"
    if [ "$RK_RC" -eq 0 ]; then
      row remote "APERTUS_URL of the environment: the service answers (backend $RK_SB, $RK_DEV), model fingerprint checked"
      if [ "$HEADS_OK" = yes ]; then
        ready "make convert PDF=<file> (the read-out on the GPU of APERTUS_URL; the text of each PDF goes to that computer)"
      else
        notready "not ready: the heads are absent here. 'make gpu URL=\"\$APERTUS_URL\"' sets them up."
      fi
    else
      row remote "APERTUS_URL of the environment: $RK_MSG"
      notready "not ready: make convert takes APERTUS_URL first, and its service is not ready ($RK_REASON). Then make convert uses the code rules only."
      row "" "Start the service and the ssh tunnel, or remove APERTUS_URL from the environment for the GPU of this computer."
    fi
    return 0
  fi
  verdict_local
}

# make gpu BACKEND=<name>: the check of this backend, then 'make setup-apertus APERTUS_BACKEND=<name>'.
backend_mode() {
  case $BACKEND in
    auto|mlx|cuda|mps|cpu) ;;
    remote) err "BACKEND=remote: for a GPU of another computer, give its address: make gpu URL=$SERVICE_EXAMPLE"; exit 1 ;;
    *) err "BACKEND=$(plain "$BACKEND"): use auto, mlx, cuda or mps (cpu: very slow, for checks only)."; exit 1 ;;
  esac
  facts; read_setup; pick_python
  if [ "$PKG" != yes ]; then
    CK=; CK_RC=1; parse_check
    header; computer_row
    err "the Python packages of 'make setup' are absent ($(plain "$APY")). Run 'make setup' first, then 'make gpu BACKEND=$BACKEND' again."
    exit 1
  fi
  local_check "$BACKEND" ""
  go=no; mlx_new=no
  if [ "$CK_RC" -eq 0 ] || [ "$CK_REASON" = memory_low ]; then go=yes
  elif [ "$BACKEND" = mlx ] && [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$CK_REASON" = backend_absent ]; then
    # MLX is not installed yet: 'make setup-apertus' installs it, if the Mac has the memory for the model.
    case $CK_WHY in "Python package absent"*) if [ "$RAM" -ge "$MIN_MAC_BYTES" ]; then go=yes; mlx_new=yes; fi ;; esac
  fi
  header; computer_row
  if [ "$go" != yes ]; then
    row GPU "$BACKEND: ${CK_WHY:-$CK_MSG}"
    err "BACKEND=$BACKEND cannot be used on this computer (${CK_REASON:-error}). Nothing is set up, and nothing is downloaded."
    if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$RAM" -ge "$MIN_MAC_BYTES" ] && [ "$BACKEND" != mlx ]; then
      ways "this Mac has Apple silicon: make gpu BACKEND=mlx"
    elif [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$RAM" -ge "$MIN_MAC_BYTES" ]; then
      ways "MLX does not start on this Mac: make gpu BACKEND=mps (torch MPS) after a look at the reason above"
    else
      ways
    fi
    [ "$CK_RC" -ne 0 ] || CK_RC=1
    exit "$CK_RC"
  fi
  if [ "$mlx_new" = yes ]; then row GPU "mlx: MLX is not installed yet ('make setup-apertus' installs it)"; else gpu_row; fi
  if [ "$BACKEND" = cpu ]; then note "BACKEND=cpu: torch on the CPU is very slow (many minutes for one page). Use it only for checks."; fi
  if [ "$CK_REASON" = memory_low ]; then note "$CK_MSG"; fi
  say "Next: make setup-apertus APERTUS_BACKEND=$BACKEND. If the model is not on this computer, it downloads it (about"
  say "17.3 GB; your own Hugging Face account) and writes its text branch (16.1 GB)."
  if [ -n "${APERTUS_URL:-}" ]; then note "BACKEND= sets up the GPU of this computer: APERTUS_URL is not given to make setup-apertus."; fi
  say ""
  rc=0
  # The GPU of this computer: with APERTUS_URL, the check of setup-apertus would take that service.
  (unset APERTUS_URL; exec "$MAKE_CMD" -C "$TRACK" --no-print-directory setup-apertus APERTUS_BACKEND="$BACKEND") || rc=$?
  if [ "$rc" -ne 0 ]; then err "make setup-apertus stopped (exit code $rc). The messages above give the reason."; exit "$rc"; fi
  say ""
  APY=${APERTUS_PYTHON:-$PY}
  report "$BACKEND"
  [ "$VERDICT" = ready ] || exit 1
}

# make gpu URL=<address>: the check of the service, the heads here, the command of 'make convert'.
url_mode() {
  if [ -n "$BACKEND" ]; then err "give BACKEND or URL, not both (URL: the GPU of another computer)."; exit 1; fi
  facts; read_setup; pick_python
  MLX=unknown
  header; computer_row
  if ! { [ -x "$APY" ] || command -v "$APY" >/dev/null 2>&1; }; then
    err "the Python $(plain "$APY") is absent. Run 'make setup' first."
    exit 1
  fi
  remote_check "$URL"
  if [ "$RK_RC" -ne 0 ]; then
    crow service "$RED" "not ready ($RK_REASON): $RK_MSG"
    err "the service is not ready ($RK_REASON). Nothing is changed on this computer."
    case $RK_REASON in
      remote_unreachable|remote_timeout|remote_not_service)
        row next "on the GPU computer: 'make setup', then 'make serve-apertus' (default 127.0.0.1:8090);"
        row "" "here: an ssh tunnel to it, for example ssh -N -L 8090:127.0.0.1:8090 <user>@<GPU computer>;"
        row "" "then make gpu URL=<the local address of the tunnel> again ($GPU_DOC, way 2)" ;;
      remote_unauthorized)
        row next "give the token of the service in the environment variable APERTUS_TOKEN, then make gpu URL=... again" ;;
      remote_plain_http)
        row next "use the ssh tunnel (URL=http://127.0.0.1:<port>), https, or APERTUS_ALLOW_HTTP=1 (a private network only)" ;;
      remote_fingerprint_differs)
        row next "on the GPU computer: 'make setup-apertus' (the model of the heads), then 'make serve-apertus' again" ;;
      remote_busy)
        row next "the service reads out another PDF now. Try again when it is free" ;;
    esac
    exit "$RK_RC"
  fi
  if [ "$RK_BUSY" = true ]; then state="busy now (one read-out at a time)"; else state="free"; fi
  row service "answers: backend $RK_SB ($RK_DEV) · model fingerprint checked · $state"
  if [ "$HEADS_OK" = yes ]; then
    row heads "present: $HEADS_SHORT (SHA-256 checked)"
  elif [ "$ST" = model ]; then
    err "a head file is absent or changed. Run 'make setup-apertus' (it keeps the model), then make gpu URL=... again."
    exit 1
  else
    if [ "$PKG" != yes ]; then
      err "the heads are absent, and the Python packages of 'make setup' are absent. Run 'make setup' first (no GPU needed), then make gpu URL=... again."
      exit 1
    fi
    if [ -n "$USER_HEADS_DIR" ]; then hsrc="from HEADS_DIR=$(plain "$USER_HEADS_DIR")"; else hsrc="from Hugging Face"; fi
    if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ]; then hsrc="$hsrc; on a Mac with Apple silicon also ocrmac"; fi
    row heads "absent or changed: make setup-apertus APERTUS_MODEL=none (the 3 head files $hsrc)"
    say ""
    rc=0
    "$MAKE_CMD" -C "$TRACK" --no-print-directory setup-apertus APERTUS_MODEL=none || rc=$?
    if [ "$rc" -ne 0 ]; then err "make setup-apertus APERTUS_MODEL=none stopped (exit code $rc). The messages above give the reason."; exit "$rc"; fi
    say ""
    read_setup
    if [ "$HEADS_OK" != yes ]; then err "the heads are not in the record after make setup-apertus APERTUS_MODEL=none."; exit 1; fi
    row heads "set up: $HEADS_SHORT (SHA-256 checked)"
  fi
  ready "make convert APERTUS_URL=$(word "$(plain "$URL")") PDF=<file>"
  row privacy "the text of each PDF goes to the computer of the service. The heads and the record stay on this computer."
  if [ "$RK_AUTH" = bearer ]; then
    row token "the service needs one. Give make convert the same APERTUS_TOKEN in the environment (this tool does not show it)."
  fi
  row note "make gpu stores no address: give APERTUS_URL to each make convert."
}

VERDICT=; CK_REQ=auto
if [ -n "$URL" ]; then
  url_mode
elif [ -n "$BACKEND" ]; then
  backend_mode
else
  report "$REPORT_BACKEND"
fi

#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: 'make setup-apertus' (the Makefile calls this file). Orchestration only.
#
# It makes the Apertus step of 'make convert' ready on this computer:
#   1. checks the computer (Python of 'make setup-pdf', system, memory, NVIDIA GPU, free disk);
#   2. macOS with Apple silicon: installs MLX and ocrmac (tools/apertus/requirements-macos.txt,
#      tools/requirements-macos-ocr.txt); with APERTUS_MODEL=none (a GPU of another computer makes the read-out)
#      only ocrmac. Linux and Windows: no extra package (torch of 'make setup-pdf');
#   3. checks that a GPU is there (app/worker/apertus_states.py check; no model load). With no GPU it stops and
#      names the ways out: a GPU in the cloud (docs/apertus-gpu.md) or APERTUS=0 (code rules only);
#   4. the model: the text branch of swiss-ai/Apertus-v1.5-8B at a pinned revision. The download needs your own
#      Hugging Face account (you accept the conditions of the model on its page; 'hf auth login' with your own
#      token). This file never reads, prints or stores a token. tools/text_branch.py cuts the text branch from
#      the download (no MLX needed) and checks the model fingerprint. A text branch folder that is already
#      present gets the full SHA-256 check of each file (text_branch.py check-dir, about 10 to 60 s;
#      APERTUS_VERIFY=0 skips it);
#   5. the heads (3 files) from the local folder HEADS_DIR if it is given, else from the Hugging Face repository
#      HEADS_REPO at the pinned HEADS_REVISION (a commit id of 40 hex characters); SHA-256 of
#      tools/apertus/heads.sha256;
#   6. writes data/apertus/setup.json (make convert reads it).
#
# Environment (the Makefile sets it): PYTHON, APERTUS_REPO, APERTUS_REVISION, APERTUS_MODEL_DIR, APERTUS_MODEL
# (auto: set up the model; none: the heads only, for a GPU of another computer), APERTUS_SOURCE_DIR (optional: a
# folder with a download of the omni model), APERTUS_BACKEND, HEADS_REPO, HEADS_REVISION, HEADS_DIR.
# Tested only on one Mac (Apple M4, 32 GB) on 16.10.2026, with HF_HUB_OFFLINE=1 against a local Hugging Face
# cache. Linux and Windows are NOT tested.

set -eu
umask 022

HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
APP=$TRACK/app
PY=${PYTHON:-python3}
REPO=${APERTUS_REPO:-swiss-ai/Apertus-v1.5-8B}
REV=${APERTUS_REVISION:?APERTUS_REVISION is not set}
MODEL_DIR=${APERTUS_MODEL_DIR:-data/apertus/apertus-v1.5-8b-text-bf16}
MODEL_MODE=${APERTUS_MODEL:-auto}
SOURCE_DIR=${APERTUS_SOURCE_DIR:-}
BACKEND=${APERTUS_BACKEND:-auto}
HEADS_REPO=${HEADS_REPO:-JonathanKovatsch/parlpdfech-heads}
HEADS_REVISION=${HEADS_REVISION:-}
HEADS_DIR=${HEADS_DIR:-}
VERIFY=${APERTUS_VERIFY:-1}
OUT=$TRACK/data/apertus
HEADS_DEST=$OUT/heads
LAYOUT=$HERE/apertus/text_branch_layout.json
WANT_FP=apertus-v1.5-8b-text-bf16:c10cd28db5bd3adf6043a5047a1435dedc5c3e55c45d5abc2ca82baf2a7786c3
GPU_DOC=docs/apertus-gpu.md
FILES="config.json model.safetensors.index.json model-apertus-model-00001-of-00004.safetensors
model-apertus-model-00002-of-00004.safetensors model-apertus-model-00003-of-00004.safetensors
model-apertus-model-00004-of-00004.safetensors tokenizer.json tokenizer_config.json special_tokens_map.json
chat_template.jinja generation_config.json LICENSE.txt"
OPTIONAL_FILES="USAGE_POLICY.pdf PRIVACY_POLICY.pdf"
HEAD_FILES="heads2.npz entry.json calibration_dev_combined.json"

say() { printf '%s\n' "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; }
note() { printf 'NOTE: %s\n' "$*" >&2; }
abs() {
  case $1 in /*) a=$1 ;; *) a=$TRACK/$1 ;; esac
  if [ -d "$a" ]; then (cd "$a" && pwd); else printf '%s\n' "$a"; fi
}
free_kb() { d=$1; while [ ! -d "$d" ]; do d=$(dirname "$d"); done; df -Pk "$d" | awk 'NR == 2 { print $4 }'; }
sha_check() {
  if command -v shasum >/dev/null 2>&1; then (cd "$1" && shasum -a 256 -c "$2")
  else (cd "$1" && sha256sum -c "$2"); fi
}

MODEL_DIR=$(abs "$MODEL_DIR")
case $MODEL_MODE in auto|none) ;; *) err "APERTUS_MODEL=$MODEL_MODE: use auto or none"; exit 1 ;; esac
if [ -n "$HEADS_REVISION" ] && ! printf '%s' "$HEADS_REVISION" | grep -Eq '^[0-9a-f]{40}$'; then
  err "HEADS_REVISION=$HEADS_REVISION: give the commit id of the heads repository (40 hex characters), not a branch name."
  exit 1
fi

# ---------------------------------------------------------------------------------------- 1. the computer
if ! { [ -x "$PY" ] || command -v "$PY" >/dev/null 2>&1; }; then
  err "the Python $PY is absent. Run 'make setup', then 'make setup-pdf', then 'make setup-apertus'."
  exit 1
fi
command -v jq >/dev/null 2>&1 || { err "the command jq is absent (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."; exit 1; }
command -v uv >/dev/null 2>&1 || { err "the command uv is absent (https://docs.astral.sh/uv/)."; exit 1; }
if ! "$PY" -c "import torch, transformers, tokenizers, numpy" >/dev/null 2>&1; then
  err "torch, transformers or tokenizers is absent in $PY. Run 'make setup-pdf' first."
  exit 1
fi
OS=$(uname -s); ARCH=$(uname -m)
case $OS in
  Darwin) RAM=$(sysctl -n hw.memsize 2>/dev/null || echo 0) ;;
  Linux) RAM=$(awk '/^MemTotal:/ { print $2 * 1024 }' /proc/meminfo 2>/dev/null || echo 0) ;;
  *) RAM=0 ;;
esac
GPU=none
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -n 1 || true)
  [ -n "$GPU" ] || GPU=none
fi
say "computer: $OS $ARCH, $(awk -v b="$RAM" 'BEGIN { printf "%.0f", b / 1e9 }') GB memory; NVIDIA GPU: $GPU"

# ---------------------------------------------------------------------------------------- 2. packages
if [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ] && [ "$MODEL_MODE" = none ]; then
  say "packages for Apple silicon: ocrmac only (exact version; APERTUS_MODEL=none: no MLX, the read-out runs on another computer)"
  uv pip install --python "$PY" -r "$HERE/requirements-macos-ocr.txt"
elif [ "$OS" = Darwin ] && [ "$ARCH" = arm64 ]; then
  say "packages for Apple silicon: MLX and ocrmac (exact versions)"
  uv pip install --python "$PY" -r "$HERE/apertus/requirements-macos.txt" -r "$HERE/requirements-macos-ocr.txt"
else
  say "packages: no extra package on $OS $ARCH (the read-out uses torch of 'make setup-pdf'; OCR stays off here)"
fi

# ---------------------------------------------------------------------------------------- 3. a GPU?
check_json() {
  # $@: more arguments of 'apertus_states.py check'. Prints the JSON line; the exit code is kept.
  (cd "$APP" && "$PY" -I -B worker/apertus_states.py check --root layout --backend "$BACKEND" "$@")
}
set +e
CHECK=$(check_json --no-model)
rc=$?
set -e
REASON=$(printf '%s' "$CHECK" | jq -r '.reason // ""' 2>/dev/null || echo error)
AUTO_BACKEND=$(printf '%s' "$CHECK" | jq -r '.backend // ""' 2>/dev/null || true)
if [ "$rc" -ne 0 ] && [ "$REASON" != memory_low ]; then
  MSG=$(printf '%s' "$CHECK" | jq -r '.message // "the check of the backend failed"' 2>/dev/null || echo "the check of the backend failed")
  if [ "$MODEL_MODE" = none ]; then
    note "$MSG"
    note "APERTUS_MODEL=none: only the heads are set up. A GPU of another computer can make the read-out ($GPU_DOC)."
  else
    err "$MSG"
    err "No model is downloaded. Ways out: (1) use a GPU in the cloud or on another computer ($GPU_DOC);"
    err "    'make setup-apertus APERTUS_MODEL=none' then sets up only the heads on this computer;"
    err "    (2) APERTUS=0 for code rules only (make convert APERTUS=0 ...)."
    exit 1
  fi
fi
[ -z "$AUTO_BACKEND" ] || say "backend: $AUTO_BACKEND (APERTUS_BACKEND=$BACKEND)"
if [ "$REASON" = memory_low ]; then note "$(printf '%s' "$CHECK" | jq -r '.message')"; fi

# ---------------------------------------------------------------------------------------- 4. the model
HF=$(dirname "$PY")/hf
if [ "$MODEL_MODE" != none ] || { [ -z "$HEADS_DIR" ] && [ -n "$HEADS_REVISION" ]; }; then
  [ -x "$HF" ] || { err "the command hf is absent next to $PY ('make setup-pdf' installs huggingface-hub)."; exit 1; }
fi
fingerprint() { "$PY" -I "$HERE/text_branch.py" fingerprint --model-dir "$1" 2>/dev/null || true; }
if [ "$MODEL_MODE" = none ]; then
  say "model: not set up (APERTUS_MODEL=none)"
elif [ "$(fingerprint "$MODEL_DIR")" = "$WANT_FP" ]; then
  say "model: present in $MODEL_DIR (fingerprint ${WANT_FP#*:})"
  if [ "$VERIFY" = 0 ]; then
    note "APERTUS_VERIFY=0: the full SHA-256 check of the present text branch is skipped (the fingerprint has only the name and the size of each shard)."
  else
    say "model: full SHA-256 check of each file (tools/text_branch.py check-dir; APERTUS_VERIFY=0 skips it)"
    "$PY" -I "$HERE/text_branch.py" check-dir --model-dir "$MODEL_DIR" --layout "$LAYOUT" || {
      err "a file of the text branch in $MODEL_DIR has another SHA-256 than tools/apertus/text_branch_layout.json."
      err "Remove the folder (or set APERTUS_MODEL_DIR to a new folder), then run 'make setup-apertus' again."
      exit 1; }
  fi
else
  need_kb=$((17 * 1000 * 1000))
  if [ -z "$SOURCE_DIR" ]; then
    # first the local Hugging Face cache (no network, no account); one call for each file
    snap=
    for f in $FILES; do
      p=$(HF_HUB_OFFLINE=1 "$HF" download "$REPO" "$f" --revision "$REV" --quiet 2>/dev/null) || { snap=; break; }
      snap=$(dirname "$p")
    done
    if [ -n "$snap" ]; then
      say "model download: in the Hugging Face cache ($REPO, revision $REV)"
    else
      if [ "${HF_HUB_OFFLINE:-0}" = 1 ]; then
        err "the model $REPO (revision $REV) is not in the Hugging Face cache, and HF_HUB_OFFLINE=1 forbids the download."
        exit 1
      fi
      need_kb=$((40 * 1000 * 1000))
      if [ "$(free_kb "$HOME")" -lt "$need_kb" ] || [ "$(free_kb "$MODEL_DIR")" -lt $((17 * 1000 * 1000)) ]; then
        err "not enough free disk: the download needs 17.3 GB (Hugging Face cache) and the text branch 16.1 GB."
        exit 1
      fi
      if ! "$HF" auth whoami >/dev/null 2>&1; then
        err "the model $REPO needs a Hugging Face account. Do these steps yourself, then run 'make setup-apertus' again:"
        err "  1. make an account on https://huggingface.co and open https://huggingface.co/$REPO"
        err "  2. read and accept the conditions of the model on that page"
        err "  3. run: $HF auth login   (with your own access token; nobody else types it)"
        exit 1
      fi
      say "model download (network, about 17.3 GB): $REPO, revision $REV"
      for f in $FILES; do
        p=$(HF_HUB_DISABLE_TELEMETRY=1 "$HF" download "$REPO" "$f" --revision "$REV" --quiet) || {
          err "the download of $f failed. Check that you accepted the conditions on https://huggingface.co/$REPO"; exit 1; }
        snap=$(dirname "$p")
      done
      for f in $OPTIONAL_FILES; do
        HF_HUB_DISABLE_TELEMETRY=1 "$HF" download "$REPO" "$f" --revision "$REV" --quiet >/dev/null 2>&1 \
          || note "$f is not in the repository at this revision (it is not in the fingerprint)"
      done
    fi
    SOURCE_DIR=$snap
  fi
  if [ "$(free_kb "$MODEL_DIR")" -lt $((17 * 1000 * 1000)) ]; then
    err "not enough free disk at $MODEL_DIR: the text branch needs 16.1 GB."
    exit 1
  fi
  say "text branch: $SOURCE_DIR -> $MODEL_DIR (tools/text_branch.py; about 16 GB to write)"
  "$PY" -I "$HERE/text_branch.py" extract --source "$SOURCE_DIR" --target "$MODEL_DIR" --layout "$LAYOUT"
  [ "$(fingerprint "$MODEL_DIR")" = "$WANT_FP" ] || { err "the model fingerprint of $MODEL_DIR is not $WANT_FP"; exit 1; }
  say "NOTE: the download stays in the Hugging Face cache (about 17 GB). 'hf cache' can remove it; this tool deletes nothing."
fi

# ---------------------------------------------------------------------------------------- 5. the heads
mkdir -p "$HEADS_DEST"
if [ -n "$HEADS_DIR" ]; then
  [ -d "$HEADS_DIR" ] || { err "HEADS_DIR=$HEADS_DIR is not a folder."; exit 1; }
  for f in $HEAD_FILES; do rm -f "$HEADS_DEST/$f"; cp "$HEADS_DIR/$f" "$HEADS_DEST/$f"; chmod 0644 "$HEADS_DEST/$f"; done
  HEADS_SOURCE="local:$(cd "$HEADS_DIR" && pwd)"
  note "heads from the local folder $(cd "$HEADS_DIR" && pwd) (HEADS_DIR), not from Hugging Face."
elif [ -n "$HEADS_REVISION" ]; then
  say "heads: $HEADS_REPO, revision $HEADS_REVISION (Hugging Face; public, no token)"
  for f in $HEAD_FILES; do
    p=$(HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1 "$HF" download "$HEADS_REPO" "$f" \
      --revision "$HEADS_REVISION" --quiet) || { err "the download of the head file $f failed."; exit 1; }
    rm -f "$HEADS_DEST/$f"; cp "$p" "$HEADS_DEST/$f"; chmod 0644 "$HEADS_DEST/$f"
  done
  HEADS_SOURCE="hf:$HEADS_REPO@$HEADS_REVISION"
else
  err "no source for the 3 head files: give HEADS_REVISION (a commit of $HEADS_REPO) or HEADS_DIR (a folder with the 3 files)."
  exit 1
fi
sha_check "$HEADS_DEST" "$HERE/apertus/heads.sha256" >/dev/null || { err "a head file has another SHA-256 than tools/apertus/heads.sha256."; exit 1; }
say "heads: SHA-256 of the 3 files equal to tools/apertus/heads.sha256"

# ---------------------------------------------------------------------------------------- 6. the record
if [ "$MODEL_MODE" = none ]; then
  set +e; FINAL=$(check_json --no-model); set -e
  MODEL_JSON=null
else
  set +e; FINAL=$(check_json --model-dir "$MODEL_DIR"); frc=$?; set -e
  if [ "$frc" -ne 0 ] && [ "$(printf '%s' "$FINAL" | jq -r '.reason // ""')" != memory_low ]; then
    err "$(printf '%s' "$FINAL" | jq -r '.message // "the final check failed"')"
    exit 1
  fi
  MODEL_JSON=$(jq -n --arg d "$MODEL_DIR" '$d')
fi
mkdir -p "$OUT"
jq -n --arg made "$(date '+%Y-%m-%dT%H:%M:%S%z')" --arg py "$PY" --argjson model_dir "$MODEL_JSON" \
  --arg fp "$WANT_FP" --arg repo "$REPO" --arg rev "$REV" --arg heads_dir "$HEADS_DEST" --arg heads_source "$HEADS_SOURCE" \
  --arg os "$OS" --arg arch "$ARCH" --arg gpu "$GPU" --argjson check "$FINAL" \
  --arg h1 "$(sed -n 's/  heads2.npz$//p' "$HERE/apertus/heads.sha256")" \
  --arg h2 "$(sed -n 's/  entry.json$//p' "$HERE/apertus/heads.sha256")" \
  --arg h3 "$(sed -n 's/  calibration_dev_combined.json$//p' "$HERE/apertus/heads.sha256")" \
  '{schema: "parlpdfech-apertus-setup/1", made: $made, python: $py, model: {repo: $repo, revision: $rev,
    text_branch_dir: $model_dir, fingerprint: (if $model_dir == null then null else $fp end)},
    heads: {dir: $heads_dir, source: $heads_source, sha256: {"heads2.npz": $h1, "entry.json": $h2,
    "calibration_dev_combined.json": $h3}}, backend_check: $check, platform: {os: $os, arch: $arch, nvidia: $gpu},
    tested_on: "only macOS arm64 (Apple M4, 32 GB) on 15./16.10.2026; Linux and Windows not tested"}' \
  > "$OUT/setup.json.new"
mv -f "$OUT/setup.json.new" "$OUT/setup.json"
say "PASS: make setup-apertus. Record: data/apertus/setup.json. Next: make convert PDF=<file or URL> (APERTUS=0: code rules only)."

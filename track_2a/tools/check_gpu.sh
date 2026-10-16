#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: the checks of tools/gpu.sh ('make gpu') for 'make test'. Orchestration only.
#
# A copy of tools/gpu.sh runs in a temporary folder with fake commands on PATH: uname, sysctl, nvidia-smi, lspci,
# a fake Python (the answers of 'apertus_states.py check' for a scenario) and a fake make (it writes a record in
# place of 'make setup-apertus'). No model, no GPU, no network, no Python. Thus the branches for Linux and an
# NVIDIA GPU are checked on each computer, also on a Mac.
# The fake answers use the texts of app/worker/apertus_states.py and apertus_backend_remote.py. Check 0 finds each
# text that tools/gpu.sh reads in these files: if a text changes there, this check fails.
# Needs jq (as 'make gpu'). With no jq: SKIP and exit code 0. Exit code: 0 all checks pass, 1 a check failed.
# Written on 16.10.2026 and run only on one Mac (Apple M4, 32 GB).

set -eu
umask 022

HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
WORKER=$TRACK/app/worker

if ! command -v jq >/dev/null 2>&1; then
  printf 'SKIP: tools/check_gpu.sh (the command jq is absent; make gpu needs it)\n'
  exit 0
fi

T=$(mktemp -d "${TMPDIR:-/tmp}/check_gpu.XXXXXX")
trap 'rm -rf "$T"' EXIT INT TERM
SH=$(command -v sh)
ESC=$(printf '\033')
PASSN=0
FAILN=0

pass() { PASSN=$((PASSN + 1)); printf 'PASS %s\n' "$1"; }
fail() { FAILN=$((FAILN + 1)); printf 'FAIL %s\n' "$1"; }

# ------------------------------------------------------------------------------------------- 0. the texts
# The texts of the worker that tools/gpu.sh reads (its STRIP and WHY_JQ, and the patterns of hint_local).
texts_ok=yes
for s in 'Use a GPU in the cloud (see {GPU_DOC}), or APERTUS=0 for code rules only.' \
  'GPU_DOC = "docs/apertus-gpu.md"' \
  'APERTUS_BACKEND=cpu forces the CPU (very slow, for checks only).' \
  ': not available on this computer ' \
  'torch finds no NVIDIA GPU (CUDA)' \
  'has no bf16' \
  'Apertus bf16 needs 24 GB' \
  'Python package absent: ' \
  'f"backend {name}: ' \
  '"memory_too_small"' '"memory_low"' '"backend_absent"' '"no_gpu"' '"fingerprint_differs"'; do
  if ! grep -qF -- "$s" "$WORKER/apertus_states.py"; then
    texts_ok=no; fail "0 the text [$s] is not in app/worker/apertus_states.py"
  fi
done
for s in '"remote_unreachable"' '"remote_unauthorized"' '"remote_plain_http"' '"remote_fingerprint_differs"' \
  '"remote_busy"' '"server_backend"' '"health": small_health(h)' '"auth"'; do
  if ! grep -qF -- "$s" "$WORKER/apertus_backend_remote.py"; then
    texts_ok=no; fail "0 the text [$s] is not in app/worker/apertus_backend_remote.py"
  fi
done
[ "$texts_ok" = no ] || pass "0 the texts that tools/gpu.sh reads are in the worker"

# ------------------------------------------------------------------------------------------- the fake folder
mkdir -p "$T/track/tools/apertus" "$T/track/app/worker" "$T/track/data/apertus" "$T/bin" "$T/smi" "$T/pci" \
  "$T/sys" "$T/heads" "$T/userheads" "$T/model"
cp "$HERE/gpu.sh" "$T/track/tools/gpu.sh"
cp "$HERE/apertus/text_branch_layout.json" "$T/track/tools/apertus/"
for f in heads2.npz entry.json calibration_dev_combined.json; do printf 'test file %s\n' "$f" > "$T/heads/$f"; done
if command -v shasum >/dev/null 2>&1; then (cd "$T/heads" && shasum -a 256 heads2.npz entry.json calibration_dev_combined.json)
else (cd "$T/heads" && sha256sum heads2.npz entry.json calibration_dev_combined.json); fi > "$T/track/tools/apertus/heads.sha256"

# The system commands of tools/gpu.sh and of the fakes, and nothing more: a real nvidia-smi or lspci of this
# computer must not be on PATH.
for c in jq awk sed tr head grep cat dirname shasum sha256sum env mkdir rm cp wc cut touch; do
  p=$(command -v "$c" 2>/dev/null || true)
  case $p in /*) ln -s "$p" "$T/sys/$c" ;; esac
done

# The scenarios (FAKE_SCEN): lin16 (Linux, NVIDIA 16 GB), linv100 (Linux, NVIDIA with no bf16), lincpu (Linux,
# a driver, torch of a CPU build), lindev (Linux, an NVIDIA device with no driver), lin24 (Linux, NVIDIA 24 GB),
# mac32 (a Mac with Apple silicon, 32 GB), mac16 (16 GB), macnomlx (32 GB, MLX not installed).
cat > "$T/bin/uname" <<'EOF'
#!/bin/sh
case ${FAKE_SCEN:-} in mac*) os=Darwin; arch=arm64 ;; *) os=Linux; arch=x86_64 ;; esac
case ${1:-} in -s) echo "$os" ;; -m) echo "$arch" ;; *) echo "$os" ;; esac
EOF
cat > "$T/bin/sysctl" <<'EOF'
#!/bin/sh
case ${FAKE_SCEN:-} in mac16) echo 17179869184 ;; *) echo 34359738368 ;; esac
EOF
cat > "$T/smi/nvidia-smi" <<'EOF'
#!/bin/sh
case "$*" in
  *--query-gpu*)
    case ${FAKE_SCEN:-} in
      lin16) echo "NVIDIA GeForce RTX 4080, 16376 MiB, 550.54" ;;
      linv100) echo "Tesla V100-SXM2-32GB, 32768 MiB, 550.54" ;;
      *) echo "NVIDIA GeForce RTX 4090, 24564 MiB, 550.54" ;;
    esac ;;
  *) echo "| NVIDIA-SMI 550.54       Driver Version: 550.54       CUDA Version: 12.4     |" ;;
esac
EOF
cat > "$T/pci/lspci" <<'EOF'
#!/bin/sh
echo "01:00.0 VGA compatible controller: NVIDIA Corporation AD102 [GeForce RTX 4090] (rev a1)"
EOF
# The fake Python. The messages are built as in apertus_states.py (choose_backend, the probes, memory_check).
cat > "$T/bin/python" <<'EOF'
#!/bin/sh
case "$*" in
  *"import torch, transformers"*) exit 0 ;;
  *"import torch; print"*)
    case ${FAKE_SCEN:-} in lincpu|lindev) echo "torch 2.9.1 for CUDA none (a CPU build)" ;; *) echo "torch 2.9.1 for CUDA 12.8" ;; esac
    exit 0 ;;
  *text_branch.py*) exit 1 ;;
  *" check "*) ;;
  *) exit 1 ;;
esac
be=auto; prev=
for a in "$@"; do [ "$prev" = --backend ] && be=$a; prev=$a; done
W='Use a GPU in the cloud (see docs/apertus-gpu.md), or APERTUS=0 for code rules only.'
C='APERTUS_BACKEND=cpu forces the CPU (very slow, for checks only).'
if [ "$be" = auto ] && [ -n "${APERTUS_URL:-}" ]; then
  case ${FAKE_REMOTE:-ok} in
    ok|bearer)
      [ "$FAKE_REMOTE" = bearer ] && auth=bearer || auth=none
      printf '{"backend":"remote","reason":null,"message":null,"tests":{"remote":{"available":true,"host":"127.0.0.1","device":"remote:cuda:0","server_backend":"cuda","busy":false,"health":{"device":"cuda:0","auth":"%s"}}}}\n' "$auth"
      exit 0 ;;
    *) printf '{"backend":null,"reason":"remote_unreachable","message":"backend remote: no read-out service answers at 127.0.0.1:18297 (Connection refused). %s"}\n' "$W"
      exit 8 ;;
  esac
fi
scen=$FAKE_SCEN
[ "$scen" != macnomlx ] || [ ! -f "$FAKE_T/mlx_installed" ] || scen=mac32
ok() {  # $1 backend, $2 device, $3 GPU name (optional)
  printf '{"backend":"%s","reason":null,"message":null,"tests":{"%s":{"available":true,"device":"%s"%s}},"memory":{"check":"pass","free_bytes":25000000000}}\n' \
    "$1" "$1" "$2" "${3:+,\"gpu\":\"$3\"}"
  exit 0
}
absent() {  # $1 backend, $2 why
  printf '{"backend":null,"reason":"backend_absent","message":"APERTUS_BACKEND=%s: not available on this computer (%s). %s"}\n' "$1" "$2" "$W"
  exit 5
}
nogpu() {  # $1 mlx why, $2 cuda why, $3 mps why
  printf '{"backend":null,"reason":"no_gpu","message":"no GPU for Apertus on this computer (mlx: %s; cuda: %s; mps: %s). %s %s"}\n' "$1" "$2" "$3" "$W" "$C"
  exit 5
}
case $scen in
  lin16) cw='the GPU NVIDIA GeForce RTX 4080 has 17.2 GB; Apertus bf16 needs 24 GB' ;;
  linv100) cw='the GPU Tesla V100-SXM2-32GB has no bf16' ;;
  lincpu|lindev) cw='torch finds no NVIDIA GPU (CUDA)' ;;
  *) cw= ;;
esac
case $scen:$be in
  lin24:auto|lin24:cuda) ok cuda cuda:0 "NVIDIA GeForce RTX 4090" ;;
  lin*:auto) nogpu "not a Mac with Apple silicon" "$cw" "not a Mac" ;;
  lin*:cuda) absent cuda "$cw" ;;
  lin*:mlx) absent mlx "not a Mac with Apple silicon" ;;
  lin*:mps) absent mps "not a Mac" ;;
  *:cpu) ok cpu cpu ;;
  mac32:auto|mac32:mlx) ok mlx metal ;;
  mac*:mps) ok mps mps ;;
  mac*:cuda) absent cuda "torch finds no NVIDIA GPU (CUDA)" ;;
  mac16:auto|mac16:mlx)
    printf '{"backend":"mlx","reason":"memory_too_small","message":"this Mac has 17.2 GB memory; Apertus bf16 needs a Mac with 32 GB. %s","tests":{"mlx":{"available":true,"device":"metal"}}}\n' "$W"
    exit 6 ;;
  macnomlx:auto)
    printf '{"backend":"mps","reason":null,"message":null,"tests":{"mlx":{"available":false,"why":"Python package absent: mlx, mlx_lm (make setup-apertus)"},"mps":{"available":true,"device":"mps"}},"memory":{"check":"pass","free_bytes":25000000000}}\n'
    exit 0 ;;
  macnomlx:mlx) absent mlx "Python package absent: mlx, mlx_lm (make setup-apertus)" ;;
esac
printf '{"backend":null,"reason":"error","message":"fake: no answer for %s"}\n' "$scen:$be"
exit 1
EOF
# The fake make: it writes the call and a part of its environment to make.log, and a record as
# 'make setup-apertus' does. It never writes a token.
cat > "$T/bin/make" <<'EOF'
#!/bin/sh
printf 'args: %s\n' "$*" >> "$FAKE_T/make.log"
printf 'env HEADS_DIR=[%s]\n' "${HEADS_DIR-unset}" >> "$FAKE_T/make.log"
printf 'env APERTUS_URL=[%s]\n' "${APERTUS_URL-unset}" >> "$FAKE_T/make.log"
rec=$FAKE_T/track/data/apertus/setup.json
case "$*" in
  *APERTUS_MODEL=none*)
    printf '{"schema":"parlpdfech-apertus-setup/1","python":"%s","model":{"text_branch_dir":null},"heads":{"dir":"%s","source":"hf:JonathanKovatsch/parlpdfech-heads@09a794393ed9dfc6c58c4350620454c9a9292081"},"backend_check":null}\n' \
      "$FAKE_T/bin/python" "$FAKE_T/heads" > "$rec" ;;
  *APERTUS_BACKEND=*)
    all="$*"; b=${all##*APERTUS_BACKEND=}; b=${b%% *}
    [ "$b" != mlx ] || touch "$FAKE_T/mlx_installed"
    printf '{"schema":"parlpdfech-apertus-setup/1","python":"%s","model":{"text_branch_dir":"%s"},"heads":{"dir":"%s","source":"hf:JonathanKovatsch/parlpdfech-heads@09a794393ed9dfc6c58c4350620454c9a9292081"},"backend_check":{"backend":"%s"}}\n' \
      "$FAKE_T/bin/python" "$FAKE_T/model" "$FAKE_T/heads" "$b" > "$rec" ;;
esac
exit 0
EOF
chmod 0755 "$T/bin/"* "$T/smi/"* "$T/pci/"*

# A record: $1 none (no file), heads, model <backend>, or text (the content as it is).
record() {
  r=$T/track/data/apertus/setup.json
  case $1 in
    none) rm -f "$r" ;;
    heads) printf '{"schema":"parlpdfech-apertus-setup/1","python":"%s","model":{"text_branch_dir":null},"heads":{"dir":"%s","source":"hf:JonathanKovatsch/parlpdfech-heads@09a794393ed9dfc6c58c4350620454c9a9292081"},"backend_check":null}\n' \
      "$T/bin/python" "$T/heads" > "$r" ;;
    model) printf '{"schema":"parlpdfech-apertus-setup/1","python":"%s","model":{"text_branch_dir":"%s"},"heads":{"dir":"%s","source":"hf:JonathanKovatsch/parlpdfech-heads@09a794393ed9dfc6c58c4350620454c9a9292081"},"backend_check":{"backend":"%s"}}\n' \
      "$T/bin/python" "$T/model" "$T/heads" "$2" > "$r" ;;
    text) printf '%s\n' "$2" > "$r" ;;
  esac
}

# One case: $1 the name, $2 the scenario, $3 the expected exit code, the rest: the arguments of tools/gpu.sh.
# Optional variables of the case: E_BACKEND (APERTUS_BACKEND), E_URL (APERTUS_URL), E_HEADS (HEADS_DIR),
# E_TOKEN (APERTUS_TOKEN), REMOTE (the answer of the fake service: ok, bearer or down).
# Sets OUT (stdout and stderr) and RC. The checks after it: has, hasnot, made, notmade.
run_case() {
  NAME=$1; scen=$2; want=$3; shift 3
  : > "$T/make.log"
  rm -f "$T/mlx_installed"
  case $scen in
    lindev) p=$T/bin:$T/pci:$T/sys ;;
    lin*) p=$T/bin:$T/smi:$T/sys ;;
    *) p=$T/bin:$T/sys ;;
  esac
  OUT=$(
    unset APERTUS_URL APERTUS_TOKEN APERTUS_BACKEND HEADS_DIR APERTUS_PYTHON APERTUS_MODEL_DIR NO_COLOR
    PATH=$p; FAKE_SCEN=$scen; FAKE_REMOTE=${REMOTE:-ok}; FAKE_T=$T; PYTHON=$T/bin/python; GPU_MAKE=$T/bin/make
    export PATH FAKE_SCEN FAKE_REMOTE FAKE_T PYTHON GPU_MAKE
    if [ -n "${E_BACKEND:-}" ]; then APERTUS_BACKEND=$E_BACKEND; export APERTUS_BACKEND; fi
    if [ -n "${E_URL:-}" ]; then APERTUS_URL=$E_URL; export APERTUS_URL; fi
    if [ -n "${E_HEADS:-}" ]; then HEADS_DIR=$E_HEADS; export HEADS_DIR; fi
    if [ -n "${E_TOKEN:-}" ]; then APERTUS_TOKEN=$E_TOKEN; export APERTUS_TOKEN; fi
    cd "$T/track" && "$SH" tools/gpu.sh "$@" 2>&1
  ) && RC=0 || RC=$?
  E_BACKEND=; E_URL=; E_HEADS=; E_TOKEN=; REMOTE=
  if [ "$RC" = "$want" ]; then pass "$NAME: exit code $RC"; else fail "$NAME: exit code $RC, not $want"; show; fi
  case $OUT in *"$ESC"*) fail "$NAME: a color in an output that is not a terminal" ;; esac
}
show() { printf '%s\n' "$OUT" | sed 's/^/    | /'; }
has() { case $OUT in *"$1"*) pass "$NAME: [$1]" ;; *) fail "$NAME: no [$1]"; show ;; esac; }
hasnot() { case $OUT in *"$1"*) fail "$NAME: [$1] is in the output"; show ;; *) pass "$NAME: not [$1]" ;; esac; }
made() { if grep -qF -- "$1" "$T/make.log"; then pass "$NAME: make got [$1]"; else fail "$NAME: make did not get [$1]"; sed 's/^/    make.log | /' "$T/make.log"; fi; }
notmade() { if [ -s "$T/make.log" ]; then fail "$NAME: make ran"; sed 's/^/    make.log | /' "$T/make.log"; else pass "$NAME: make did not run"; fi; }

# ------------------------------------------------------------------------------------------- 1. Linux, NVIDIA
record none
run_case "1a Linux, NVIDIA 16 GB, report" lin16 0
has "not possible with this GPU (the GPU NVIDIA GeForce RTX 4080 has 17.2 GB; Apertus bf16 needs 24 GB)"
hasnot "Install torch"
notmade
run_case "1b Linux, NVIDIA 16 GB, BACKEND=cuda" lin16 5 --backend cuda
has "not possible with this GPU"
hasnot "Install torch"
notmade
run_case "1c Linux, NVIDIA with no bf16, report" linv100 0
has "not possible with this GPU (the GPU Tesla V100-SXM2-32GB has no bf16)"
run_case "1d Linux, driver, torch of a CPU build, report" lincpu 0
has "(the driver supports CUDA 12.4), but torch 2.9.1 for CUDA none (a CPU build) finds no GPU"
has "Install torch with a CUDA version"
run_case "1e Linux, a device with no driver, report" lindev 0
has "install the NVIDIA driver (then nvidia-smi shows the GPU)"
run_case "1f Linux, NVIDIA 24 GB, no record, report" lin24 0
has "cuda (cuda:0, NVIDIA GeForce RTX 4090) · memory check pass"
has "'make gpu BACKEND=cuda' sets up the Apertus step"
notmade

# An exported HEADS_DIR goes to 'make setup-apertus' as it is (also with a record that names another folder).
record heads
E_HEADS=$T/userheads E_URL=http://127.0.0.1:18297
run_case "1g Linux, NVIDIA 24 GB, BACKEND=cuda, HEADS_DIR and APERTUS_URL exported" lin24 0 --backend cuda
made "setup-apertus APERTUS_BACKEND=cuda"
made "env HEADS_DIR=[$T/userheads]"
made "env APERTUS_URL=[unset]"
has "ready: make convert APERTUS_BACKEND=cuda PDF=<file>"

# ------------------------------------------------------------------------------------------- 2. a Mac
record model mlx
run_case "2a Mac 32 GB, MLX set up, report" mac32 0
has "mlx (metal) · memory check pass"
has "set up: backend mlx, model checked (fingerprint), heads 09a7943"
has "ready: make convert PDF=<file>"
E_BACKEND=cuda
run_case "2b Mac, MLX set up, APERTUS_BACKEND=cuda (forced, absent), report" mac32 0
has "the forced APERTUS_BACKEND=cuda is not on this computer"
has "not ready with APERTUS_BACKEND=cuda"
hasnot "make gpu BACKEND=mlx"
hasnot "no GPU"
E_BACKEND=mlx E_URL=http://127.0.0.1:18297
run_case "2c Mac, APERTUS_BACKEND=mlx with APERTUS_URL, report" mac32 0
has "ready: make convert APERTUS_BACKEND=mlx PDF=<file>"
E_BACKEND=mps
run_case "2d Mac, APERTUS_BACKEND=mps, report" mac32 0
has "  GPU        mps · memory check pass"
hasnot "mps (mps)"
has "set up: backend mps (APERTUS_BACKEND=mps; the record has mlx), model checked"
has "ready: make convert APERTUS_BACKEND=mps PDF=<file>"
record text '{"schema":"parlpdfech-apertus-setup/1","model":"x"}'
run_case "2e a record with another structure" mac32 0
has "the record data/apertus/setup.json is not readable"
record none
run_case "2f Mac 16 GB, report" mac16 0
has "not possible on this Mac (16 GiB memory; Apertus needs a Mac with 32 GB)"
run_case "2g Mac 32 GB, MLX not installed, BACKEND=mlx" macnomlx 0 --backend mlx
has "mlx: MLX is not installed yet"
made "setup-apertus APERTUS_BACKEND=mlx"
has "ready: make convert PDF=<file>"
record none
run_case "2h Mac 16 GB, BACKEND=mlx" mac16 6 --backend mlx
notmade
run_case "2i a backend that is not one" mac32 1 --backend gpu
notmade

# ------------------------------------------------------------------------------------------- 3. URL=
TOKEN=check-gpu-$$-$(awk 'BEGIN { srand(); printf "%d", rand() * 1000000000 }')
record none
REMOTE=bearer E_TOKEN=$TOKEN E_HEADS=$T/userheads
run_case "3a URL=, the service answers, no heads here, HEADS_DIR given" mac32 0 --url http://127.0.0.1:18297
has "answers: backend cuda (cuda:0) · model fingerprint checked · free"
has "absent or changed: make setup-apertus APERTUS_MODEL=none (the 3 head files from HEADS_DIR=$T/userheads; on a Mac with Apple silicon also ocrmac)"
made "setup-apertus APERTUS_MODEL=none"
has "ready: make convert APERTUS_URL=http://127.0.0.1:18297 PDF=<file>"
has "Give make convert the same APERTUS_TOKEN in the environment"
hasnot "$TOKEN"
if grep -qF -- "$TOKEN" "$T/make.log" "$T/track/data/apertus/setup.json"; then fail "3a the token is in a file"; else pass "3a the token is in no file"; fi
run_case "3b URL=, the heads are there now" mac32 0 --url http://127.0.0.1:18297
has "present: 09a7943 (SHA-256 checked)"
notmade
REMOTE=down
run_case "3c URL=, no service" lin16 8 --url http://127.0.0.1:18297
has "not ready (remote_unreachable)"
has "make serve-apertus"
notmade
run_case "3d BACKEND= and URL= together" mac32 1 --backend mlx --url http://127.0.0.1:18297
notmade

printf '%s: tools/check_gpu.sh, %s checks passed, %s failed (fake commands; no model, no GPU, no network)\n' \
  "$([ "$FAILN" -eq 0 ] && echo PASS || echo FAIL)" "$PASSN" "$FAILN"
[ "$FAILN" -eq 0 ]

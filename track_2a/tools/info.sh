#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: 'make info', also the default of 'make' with no target. Orchestration only.
#
# An overview in one screen: the commit, the parts of 'make setup', the report of tools/gpu.sh (the computer, the
# GPU, the Apertus step and a verdict with the next command), the results in out/, and the main commands. It
# changes nothing and downloads nothing. If the verdict is not "ready", a last row points to 'make gpu'.
#
# Environment (the Makefile sets it, as for 'make gpu'): PYTHON, APERTUS_PYTHON, APERTUS_MODEL_DIR, APERTUS_BACKEND,
# GPU_MAKE. Written by an AI agent (Claude Opus 5.5) on 16.10.2026. Tested only on one Mac.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
cd "$TRACK" || exit 1

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then BOLD=$(printf '\033[1m'); OFF=$(printf '\033[0m'); else BOLD=; OFF=; fi

commit=$(git log -1 --format='%h, %cd' --date=format:%d.%m.%Y 2>/dev/null || true)
printf '%sParlPDFeCH · track_2a%s%s\n\n' "$BOLD" "${commit:+ · commit $commit}" "$OFF"

mark() { if [ "$1" = 1 ]; then printf 'yes'; else printf 'no'; fi; }
base=0
[ -x .venv/bin/python ] && base=1
pdf=0
for d in .venv/lib/python3*/site-packages/docling; do [ -d "$d" ] && pdf=1; done
printf '  setup      base: %s · PDF reader: %s · Apertus step: see the rows below\n' "$(mark $base)" "$(mark $pdf)"

# The rows of the GPU report, with no title line and no colors.
report=$(NO_COLOR=1 sh "$HERE/gpu.sh" --backend '' --url '' 2>&1 | sed '1d')
printf '%s\n' "$report"
if [ "$base" = 0 ] || [ "$pdf" = 0 ]; then
  printf '  next       make setup    one time: the packages, the PDF reader and the Apertus step (with a GPU)\n'
elif ! printf '%s\n' "$report" | grep -q '^  verdict    ready:'; then
  printf '  next       make gpu      the GPU check with the ways to a GPU (a driver, or a GPU of another computer)\n'
fi

if [ -f out/catalog.tsv ] && [ "$(wc -l < out/catalog.tsv)" -gt 1 ]; then
  n=$(( $(wc -l < out/catalog.tsv) - 1 ))
  last=$(tail -n 1 out/catalog.tsv | awk -F '\t' '{ n = split($3, p, "/"); printf "%s %s, valid %s", $1, p[n], $5 }')
  printf '  results    %s ID(s) in out/ · last: %s · all: make list\n' "$n" "$last"
else
  printf '  results    none yet · make convert PDF=<file>\n'
fi

cat <<'EOF'

  commands
    make setup               one time: the packages, the PDF reader and the Apertus step (with a GPU)
    make convert PDF=<file>  PDF in, RDF out (also PDF=<URL>, DIR=<folder>, LIST=<file>)
    make list                all results as a table
    make view ID=<ID>        one result in the browser
    make gpu                 the GPU check and the ways to a GPU
    make test                checks with no network
EOF

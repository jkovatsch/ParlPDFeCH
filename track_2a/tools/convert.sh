#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# ParlPDFeCH, track_2a: the commands 'make convert', 'make list' and 'make view' (the Makefile calls this file).
#
# This file is orchestration only. It starts the worker of the app (app/worker/serve_convert.py) for an own PDF
# in the mode rules (code rules only), or in the mode auto with the Apertus step (APERTUS=auto or 1, after
# 'make setup-apertus'). The arguments and the environment are the same as the server of the app gives them.
# It checks the end of the worker and its output folder with the rules of the server (app/server/src/jobs.rs).
# 'view' starts the server of the app (app/target-server/release/parlpdfech-server) with its own work folder.
# The file changes no file below app/. All results go to out/ of track_2a (git ignores out/).
#
#   convert.sh convert [--pdf <file or URL>] [--dir <folder>] [--list <file>] [--again 1]
#   convert.sh list
#   convert.sh view-check --id <ID>
#   convert.sh view --id <ID> [--port <port>] [--open no]
#
# Environment (the Makefile sets it): PYTHON (the Python of .venv/), DOCLING_MODELS, PDFTOTEXT_PLACES, APERTUS
# (auto: Apertus if 'make setup-apertus' is done and a GPU is there, else a NOTE and code rules only; 1: Apertus
# or stop; 0: code rules only), APERTUS_BACKEND (auto, mlx, cuda, mps, cpu), APERTUS_TIMEOUT (seconds for one
# PDF with Apertus), APERTUS_PYTHON (the Python of the read-out). The file data/apertus/setup.json of
# 'make setup-apertus' gives the model folder and the heads folder. APERTUS_URL and APERTUS_TOKEN (a GPU of
# another computer, docs/apertus-gpu.md) reach app/worker/apertus_states.py through the environment; this file
# never reads the token.
# Commands that this file needs: jq, shasum or sha256sum, readlink, uv, curl (for a URL and for 'view').
#
# Files of out/:
#   <ID>/source.txt      the data of the ID: source (path or URL), SHA-256, size, time, record id, valid,
#                        affair type and title. This file is the reference for the ID.
#   <ID>/record/         the record files, as the server writes them to work/records/<record id>/
#   <ID>/worker.log      the log of the last worker run of this ID (standard error of the worker)
#   <ID>/worker.events.jsonl   the JSON lines of the last worker run of this ID (standard output)
#   catalog.tsv          one row for each ID, made again from the files <ID>/source.txt after each change
#   .jobs/, .view/, .lock      temporary files of a command that runs now

set -u
umask 022

HERE=$(cd "$(dirname "$0")" && pwd)
TRACK=$(dirname "$HERE")
APP=$TRACK/app
OUT=$TRACK/out
CATALOG=$OUT/catalog.tsv
LOCK=$OUT/.lock
PY=${PYTHON:-python3}
TAB=$(printf '\t')
NL=$(printf '\nx')
NL=${NL%x}
# The limits of the server of the app (app/server/src/lib.rs): PARLPDFECH_MAX_BYTES, PARLPDFECH_MAX_PAGES,
# PARLPDFECH_JOB_TIMEOUT and the grace time before the signal KILL, with their default values.
MAX_BYTES=20971520
MAX_PAGES=25
JOB_TIMEOUT=600
KILL_GRACE=3
# The limit of a download (seconds).
DOWNLOAD_TIMEOUT=120
SERVER_BIN=$APP/target-server/release/parlpdfech-server
# The Apertus step (tools/setup_apertus.sh writes SETUP_JSON). AP is local (Apertus reads out the PDF: worker
# mode auto) or none (code rules only: worker mode rules, as before the Apertus step).
APERTUS=${APERTUS:-auto}
APERTUS_BACKEND=${APERTUS_BACKEND:-auto}
APERTUS_TIMEOUT=${APERTUS_TIMEOUT:-1800}
APY=${APERTUS_PYTHON:-$PY}
SETUP_JSON=$TRACK/data/apertus/setup.json
GPU_DOC=docs/apertus-gpu.md
AP=none
AP_BACKEND=
# Seconds of the job after the end of the read-out at the latest: heads, record, checks and view of the worker.
AP_TAIL=90
AP_MODEL_DIR=
AP_HEADS_DIR=
AP_HEADS_SOURCE=
RECORD_ID_RE='^(s-[0-9]{1,12}|u-[0-9a-f]{16})(-rules)?$'
# The codes that the server accepts with the exit code 3 of the worker (app/server/src/jobs.rs, REFUSED).
REFUSED_CODES='pdf_unreadable protected_pdf too_long no_text_layer not_in_package doc_id_unknown pdf_differs_from_doc_id sample_unknown bad_request'

say() { printf '%s\n' "$*"; }
err() { printf 'ERROR: %s\n' "$*" >&2; }
note() { printf 'NOTE: %s\n' "$*" >&2; }
now() { date '+%Y-%m-%dT%H:%M:%S%z'; }
# A text for one cell of the catalog: no tab and no line break.
cell() { printf '%s' "$1" | tr '\t\r\n' '   '; }

# A text for the terminal: each control character and each format character (for example the right-to-left
# override) becomes '?'. The function display_file_name of the server (app/server/src/ids.rs) removes the
# same characters. The text can come from a file name, a line of LIST, a URL or the text of a PDF.
SAFE_JQ='gsub("[\u0000-\u001f\u007f-\u009f­؜​-‏‪-‮⁠-⁯﻿]"; "?")'
clean() {
  printf '%s' "$1" | jq -Rrs "$SAFE_JQ" 2>/dev/null || printf '%s' "$1" | LC_ALL=C tr '\000-\037\177' '?'
}

need() {
  command -v "$1" >/dev/null 2>&1 && return 0
  err "the command '$1' is absent. $2"
  exit 1
}

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

file_bytes() { wc -c < "$1" | tr -d ' '; }

# True if the mark '%PDF-' is in the first 1024 bytes. This is the rule of the app (app/server/src/ids.rs,
# has_pdf_mark). A zero byte becomes a line break, so that it cannot join 2 parts of the mark.
has_pdf_mark() { head -c 1024 "$1" 2>/dev/null | LC_ALL=C tr '\000' '\n' | LC_ALL=C grep -q '%PDF-'; }

is_url() {
  case $1 in
    [Hh][Tt][Tt][Pp]://*|[Hh][Tt][Tt][Pp][Ss]://*) return 0 ;;
  esac
  return 1
}

# A path that starts with ~/ starts in the home folder (zsh does not expand ~ in 'make convert PDF=~/...').
home_path() {
  case $1 in
    '~') printf '%s\n' "$HOME" ;;
    '~/'*) printf '%s/%s\n' "$HOME" "${1#'~/'}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

# A relative path that starts with '-' gets './' in front. Then no command reads the path as an option.
safe_path() {
  case $1 in
    -*) printf './%s\n' "$1" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

# Moves the file or the folder $1 to the name $2 (a rename). If the first try did not move it, a second try
# follows. The result is true only if $1 is gone.
move() {
  mv -f "$1" "$2" 2>/dev/null
  [ -e "$1" ] || [ -L "$1" ] || return 0
  mv -f "$1" "$2" 2>/dev/null
  ! { [ -e "$1" ] || [ -L "$1" ]; }
}

# ---------------------------------------------------------------------------------------------------- the ID
# An ID is a sequential number with 4 digits (0001, 0002, ...). The forms 2, 0002 and ID-0002 are the same ID.
# The reference for an ID is its file out/<ID>/source.txt. The catalog is made from these files.
normal_id() {
  raw=$(printf '%s' "$1" | sed 's/^[Ii][Dd]-//')
  case $raw in
    ''|*[!0-9]*) return 1 ;;
  esac
  digits=$(printf '%s' "$raw" | sed 's/^0*//')
  [ -n "$digits" ] || return 1
  printf '%04d\n' "$digits"
}

# The folders of the IDs (out/<ID>/, a name of 4 or more digits), one line for each folder.
id_folders() {
  for d in "$OUT"/[0-9][0-9][0-9][0-9]*; do
    [ -d "$d" ] || continue
    case ${d##*/} in *[!0-9]*) continue ;; esac
    printf '%s\n' "$d"
  done
}

# The files out/<ID>/source.txt, one line for each file.
info_files() {
  id_folders | while IFS= read -r d; do
    if [ -f "$d/source.txt" ]; then printf '%s/source.txt\n' "$d"; fi
  done
}

# One value of a file source.txt: info_value <file> <name>.
info_value() { sed -n "s/^$2: //p" "$1" 2>/dev/null | head -n 1; }

# The ID whose file source.txt has this SHA-256 (the lowest ID if there are more), or no text.
id_of_sha() {
  info_files | awk -v want="sha256: $1" '
    { f = $0
      while ((getline line < f) > 0) {
        if (line == want) { id = f; sub("/source\\.txt$", "", id); sub(".*/", "", id); print id; break }
      }
      close(f) }' | sort -n | head -n 1
}

# The next ID: the highest ID of a folder out/<ID>/, plus 1. A folder without a catalog row counts too.
next_id() {
  id_folders | awk -F/ '{ n = $NF + 0; if (n > m) m = n } END { printf "%04d\n", m + 1 }'
}

# Writes out/<ID>/source.txt in one step: a new file, then a rename. The arguments: the folder, then the values
# source, sha256, bytes, converted, seconds, record_id, valid, affair_type, title. The caller gives values with
# no tab and no line break. This function starts no command other than mv, so a signal cannot stop it half way.
write_info() {
  wi=$1/source.txt
  {
    printf 'source: %s\n' "$2"
    printf 'sha256: %s\n' "$3"
    printf 'bytes: %s\n' "$4"
    printf 'converted: %s\n' "$5"
    printf 'seconds: %s\n' "$6"
    printf 'record_id: %s\n' "$7"
    printf 'valid: %s\n' "$8"
    printf 'affair_type: %s\n' "$9"
    printf 'title: %s\n' "${10}"
  } > "$wi.new" && move "$wi.new" "$wi"
}

# The rows of the catalog (no header), in the order of the ID, made from the files out/<ID>/source.txt.
catalog_rows() {
  info_files | awk -v tab="$TAB" '
    { f = $0; id = f; sub("/source\\.txt$", "", id); sub(".*/", "", id)
      split("", v); v["affair_type"] = "-"; v["title"] = "-"
      while ((getline line < f) > 0) {
        i = index(line, ": ")
        if (i > 0) v[substr(line, 1, i - 1)] = substr(line, i + 2)
      }
      close(f)
      print id tab v["sha256"] tab v["source"] tab v["converted"] tab v["valid"] tab v["affair_type"] tab v["title"] tab "out/" id "/" }' \
    | sort -t "$TAB" -k1,1n
}

# Writes out/catalog.tsv again from the files out/<ID>/source.txt (a new file, then a rename).
catalog_write() {
  {
    printf 'id\tsha256\tsource\ttime\tvalid\taffair_type\ttitle\tfolder\n'
    catalog_rows
  } > "$CATALOG.new" && move "$CATALOG.new" "$CATALOG"
}

# ---------------------------------------------------------------------------------------------------- the lock
# The lock is the symbolic link out/.lock with the target pid-<process id>. One call of 'ln -s' makes the link
# and its content in one step, and the call fails if the link exists.
LOCKED=0
take_lock() {
  mkdir -p "$OUT"
  tries=0
  while :; do
    if [ -d "$LOCK" ] && [ ! -L "$LOCK" ]; then
      # A lock folder of an earlier form of this file (out/.lock/pid).
      other=$(cat "$LOCK/pid" 2>/dev/null || true)
      if [ -n "$other" ] && kill -0 "$other" 2>/dev/null; then
        err "another 'make convert' runs (process $other). Wait for its end, then start again."
        exit 1
      fi
      rm -rf "$LOCK"
    fi
    if ln -s "pid-$$" "$LOCK" 2>/dev/null; then
      LOCKED=1
      return 0
    fi
    holder=$(readlink "$LOCK" 2>/dev/null || true)
    other=${holder#pid-}
    case $other in ''|*[!0-9]*) other= ;; esac
    if [ -n "$other" ] && kill -0 "$other" 2>/dev/null; then
      err "another 'make convert' runs (process $other). Wait for its end, then start again."
      exit 1
    fi
    tries=$((tries + 1))
    if [ "$tries" -gt 3 ]; then
      err "the lock out/.lock cannot be taken. If no 'make convert' runs, delete out/.lock."
      exit 1
    fi
    # The process of the lock ended. One rename moves the lock aside. Only a lock with the same target is deleted.
    # If another process took the lock in the meantime, its lock goes back.
    aside=$OUT/.lock.old.$$
    if mv "$LOCK" "$aside" 2>/dev/null; then
      got=$(readlink "$aside" 2>/dev/null || true)
      if [ "$got" != "$holder" ] && [ -n "$got" ]; then ln -s "$got" "$LOCK" 2>/dev/null; fi
      rm -f "$aside"
    fi
  done
}
drop_lock() {
  if [ "$LOCKED" = 1 ] && [ "$(readlink "$LOCK" 2>/dev/null)" = "pid-$$" ]; then rm -f "$LOCK"; fi
  LOCKED=0
}

# ---------------------------------------------------------------------------------------------------- summary
# The jq program for the summary of one record (view.json, schema parlpdfech-site-view/3).
SUMMARY_JQ='
def safe: '"$SAFE_JQ"';
def name: ({"affair_type":"affair type","title":"title","affair_number":"affair number",
  "submission_date":"submission date","sponsor":"first author","response_date":"response date",
  "responder":"responder"}[.] // .) | tostring | safe;
def rank: . as $f
  | ["affair_type","title","affair_number","submission_date","sponsor","response_date","responder"]
  | index($f) // 99;
def flat: tostring | gsub("[[:space:]]+"; " ") | safe;
def short($n): if length > $n then .[0:($n - 3)] + "..." else . end;
def pad($n): if length < $n then . + (" " * ($n - length)) else . end;
def where: if .written then "in the record"
  elif .candidate == "addressee" then "not in the record (addressed body)"
  else "not in the record (weak candidate)" end;
(.values // []) as $v
| ([.head_values.cascade.entries[]? | select(.state == "not_found_in_pdf") | .field | name] | join(", ")) as $nf
| ([.head_values.cascade.entries[]? | select(.state == "not_searched") | .field | name] | join(", ")) as $ns
| (if ($v | length) == 0 then "  values read from the PDF: none"
   else "  values read from the PDF (value, probability, status):" end),
  ($v | sort_by(.field | rank) | .[]
   | "    " + (.field | name | pad(16)) + ((.value // .value_printed // "") | flat | short(46) | pad(48))
     + ((.probability // "-") | flat | pad(8)) + ((.value_status // "-") | flat | pad(9)) + where),
  (if $nf != "" then "  searched, no value found: " + $nf else empty end),
  (if $ns != "" then "  not searched in this kind of document: " + $ns else empty end)
'

# The jq program for the summary of a record of the Apertus mode: view.json, and convert.json of the record with
# --slurpfile c (key apertus_values, made by the worker: app/worker/values_apertus.py). The column source gives the
# origin of the choice of each value: "rules", "Apertus" (an Apertus head chose it; code read the value from the
# wording at its span), "Apertus (remote GPU)" (the states came from a GPU of another computer), plus " near" if
# the head probability is near a threshold (another runtime can give another decision). The column probability is
# the calibrated probability of the tier of the value (the probability of the record); the lines of Q1 and Q2 give
# the head probability (the output of the head), a different number. Then one line for the Apertus step, one for
# the type (Q1) and one for the first author (Q2). A record with no Apertus step (APERTUS=0) uses SUMMARY_JQ above
# with no change.
SUMMARY_AP_JQ='
def safe: '"$SAFE_JQ"';
def name: ({"affair_type":"affair type","title":"title","affair_number":"affair number",
  "submission_date":"submission date","sponsor":"first author","response_date":"response date",
  "responder":"responder"}[.] // .) | tostring | safe;
def rank: . as $f
  | ["affair_type","title","affair_number","submission_date","sponsor","response_date","responder"]
  | index($f) // 99;
def flat: tostring | gsub("[[:space:]]+"; " ") | safe;
def short($n): if length > $n then .[0:($n - 3)] + "..." else . end;
def pad($n): if length < $n then . + (" " * ($n - length)) else . end;
def where: if .written then "in the record"
  elif .candidate == "addressee" then "not in the record (addressed body)"
  else "not in the record (weak candidate)" end;
def ap: ($c[0].apertus_values // {});
def remote: (((ap.backend // "") | tostring | startswith("remote")) or ap.state == "remote");
def near($f): if $f == "affair_type" then (ap.q1.near // false) else (ap.q2[$f].near // false) end;
def source: . as $x
  | if (($x.tier // "") | tostring | startswith("apertus_")) then
      (if remote then "Apertus (remote GPU)" else "Apertus" end) + (if near($x.field) then " near" else "" end)
    else "rules" end;
def p2: if type != "number" then "-"
  else (. * 100 | round) as $n | (($n / 100) | floor | tostring) + "."
       + (($n % 100) | tostring | if length < 2 then "0" + . else . end) end;
def band: if type != "number" then "-" elif . >= 0.8 then "hi" else "lo" end;
def q1state: ({"used": ("used, place p." + ((ap.q1.page // "?") | tostring) + " " + ((ap.q1.block // "?") | flat)
                        + " found by code"
                        + (if ((ap.q1.place_option_types // []) | length) >= 2
                           then " (in a list of " + ((ap.q1.place_option_types | length) | tostring)
                                + " types, for example boxes to tick: the word is there, the choice is not shown)"
                           else "" end)),
               "no_evidence": "no evidence in the text (not written)",
               "rules_gave_the_type": "rules gave the type (Apertus not used)",
               "rules_gave_the_type_apertus_differs": "rules gave the type, Apertus differs (not used)",
               "below_threshold": "below 0.80 (not used)", "class_none": "class none (not used)",
               "not_used": "not used"}[ap.q1.state // "not_used"]) // ((ap.q1.state // "-") | flat);
def q2state: ({"used": "used", "not_called_rule_value_not_weak": "not called: rule value not weak",
               "not_searched_in_this_kind": "not searched in this kind of document",
               "below_band_hi": "below band hi (not used)", "below_0_50": "below 0.50 (no cue)",
               "no_value": "no value in the top block", "tier_not_entered": "tier not entered (not used)"}[.]) // flat;
(.values // []) as $v
| (ap.state // "none") as $st
| (if remote then 27 else 14 end) as $w
| ([.head_values.cascade.entries[]? | select(.state == "not_found_in_pdf") | .field | name] | join(", ")) as $nf
| ([.head_values.cascade.entries[]? | select(.state == "not_searched") | .field | name] | join(", ")) as $ns
| (if ($v | length) == 0 then "  values read from the PDF: none"
   else "  values read from the PDF (value, calibrated probability of the tier, status, source):" end),
  ($v | sort_by(.field | rank) | .[]
   | "    " + (.field | name | pad(16)) + ((.value // .value_printed // "") | flat | short(46) | pad(48))
     + ((.probability // "-") | flat | pad(8)) + ((.value_status // "-") | flat | pad(9)) + (source | pad($w))
     + where),
  (if $nf != "" then "  searched, no value found: " + $nf else empty end),
  (if $ns != "" then "  not searched in this kind of document: " + $ns else empty end),
  (if $st == "failed" then "  Apertus: not run (" + ((ap.reason // "unknown") | flat) + "). The values come from code rules."
   else
     (if $st == "stored" then "  Apertus-v1.5-8B (stored states of this block file, layer 20): no model ran for this record."
      else "  Apertus-v1.5-8B ("
        + (if remote then "remote GPU" + (if ap.remote_host then " " + (ap.remote_host | flat) else "" end)
           else "on this computer" end)
        + ", backend " + ((ap.backend // "-") | flat) + ", bf16, layer 20)"
        + ([(if ap.passes then (ap.passes | flat) + " passes" else empty end),
            ((ap.seconds.seconds // ap.seconds.total) as $s | if $s then ($s | flat) + " s" else empty end)]
           | if length > 0 then ": " + join(", ") else "" end) + "." end),
     ("  Apertus type (Q1): " + ((ap.q1.class // "-") | flat) + ", head probability " + (ap.q1.probability | p2)
      + " - " + q1state + (if ap.q1.near then " [near]" else "" end)),
     ("  Apertus first author (Q2): top block " + ((ap.q2.sponsor.top_block // "-") | flat) + ", head probability "
      + (ap.q2.sponsor.head_probability | p2) + " " + (ap.q2.sponsor.head_probability | band) + " - "
      + ((ap.q2.sponsor.state // "-") | q2state) + (if ap.q2.sponsor.near then " [near]" else "" end))
   end)
'

# 0: the record of this ID has facts of an Apertus step (convert.json key apertus_values with the state local,
# remote, stored or failed). Else 1: the summary of the rules (SUMMARY_JQ).
has_apertus_facts() {
  [ -f "$1" ] && jq -e '(.apertus_values.state // "none") as $s
    | ($s == "local" or $s == "remote" or $s == "stored" or $s == "failed")' "$1" >/dev/null 2>&1
}

# Prints the summary of the stored record of one ID.
print_summary() {
  sid=$1; snote=$2
  sdir=$OUT/$sid
  sinfo=$sdir/source.txt
  svalid=$(info_value "$sinfo" valid)
  srid=$(info_value "$sinfo" record_id)
  say "ID $sid   valid: $(clean "${svalid:-?}")   record: $(clean "${srid:-?}")${snote:+   ($snote)}"
  say "  source: $(clean "$(info_value "$sinfo" source)")"
  say "  sha256: $(clean "$(info_value "$sinfo" sha256)")"
  if has_apertus_facts "$sdir/record/convert.json"; then
    jq -r --slurpfile c "$sdir/record/convert.json" "$SUMMARY_AP_JQ" "$sdir/record/view.json" 2>/dev/null \
      || say "  (the values cannot be read from out/$sid/record/view.json and convert.json)"
  else
    jq -r "$SUMMARY_JQ" "$sdir/record/view.json" 2>/dev/null || say "  (the values cannot be read from out/$sid/record/view.json)"
  fi
  say "  folder: out/$sid/ (record files in out/$sid/record/)"
  say "  open it in the browser: make view ID=$sid"
}

# Plain words for a code of the worker (app/CONTRACT.md chapter 4.2).
reason_text() {
  case $1 in
    too_long) printf 'the PDF has more than %s pages' "$MAX_PAGES" ;;
    no_text_layer) printf 'no page has a text layer, and no OCR engine runs' ;;
    protected_pdf) printf 'the PDF has a password' ;;
    pdf_unreadable) printf 'the PDF does not open or has no page' ;;
    not_in_package) printf 'this profile converts no own PDF' ;;
    bad_request) printf 'the worker refused the arguments or the file' ;;
    converter_stopped) printf 'the converter stopped' ;;
    timeout) printf 'the worker took more than %s seconds' "$JOB_TIMEOUT" ;;
    *) printf '%s' "$(clean "$1")" ;;
  esac
}

# ---------------------------------------------------------------------------------------------- the Apertus step
# Without Apertus: APERTUS=1 stops here with the reason and the ways out; APERTUS=auto writes a NOTE and the
# records are made with the code rules only.
apertus_off() {
  why=$1
  case $why in
    *APERTUS=0*) ways= ;;
    *) ways=" Ways out: use a GPU in the cloud (see $GPU_DOC), or APERTUS=0 for code rules only." ;;
  esac
  if [ "$APERTUS" = 1 ]; then
    err "$why$ways"
    exit 1
  fi
  note "$why The records get the code rules only.$ways"
  AP=none
  AP_BACKEND=
}

# Sets AP (local or none) and AP_BACKEND. The check runs app/worker/apertus_states.py check (no model load): the
# backend (a GPU), the model fingerprint and the free memory.
apertus_mode() {
  AP=none
  AP_BACKEND=
  AP_REMOTE_HOST=
  AP_REMOTE_BACKEND=
  case $APERTUS in
    0) return 0 ;;
    1|auto) ;;
    *) err "APERTUS=$(clean "$APERTUS"): use auto, 1 or 0."; exit 1 ;;
  esac
  case $APERTUS_TIMEOUT in
    ''|*[!0-9]*) err "APERTUS_TIMEOUT=$(clean "$APERTUS_TIMEOUT"): give a number of seconds (300 or more)."; exit 1 ;;
  esac
  if [ "$APERTUS_TIMEOUT" -lt 300 ]; then err "APERTUS_TIMEOUT=$APERTUS_TIMEOUT: give 300 seconds or more."; exit 1; fi
  if [ ! -f "$SETUP_JSON" ]; then
    if [ "$APERTUS" = 1 ]; then
      err "Apertus is not set up on this computer: run 'make setup-apertus' (or APERTUS=0 for code rules only)."
      exit 1
    fi
    note "Apertus is not set up on this computer ('make setup-apertus'): code rules only."
    return 0
  fi
  AP_MODEL_DIR=$(jq -r '.model.text_branch_dir // ""' "$SETUP_JSON" 2>/dev/null)
  AP_HEADS_DIR=$(jq -r '.heads.dir // ""' "$SETUP_JSON" 2>/dev/null)
  AP_HEADS_SOURCE=$(jq -r '.heads.source // "" | split(":")[0]' "$SETUP_JSON" 2>/dev/null)
  # The Python of the read-out: APERTUS_PYTHON if it is not the Python of the worker, else the Python that
  # 'make setup-apertus' prepared (on macOS the one with MLX).
  sp=$(jq -r '.python // ""' "$SETUP_JSON" 2>/dev/null)
  if [ "$APY" = "$PY" ] && [ -n "$sp" ] && [ -x "$sp" ]; then APY=$sp; fi
  for hf in heads2.npz entry.json calibration_dev_combined.json; do
    if [ -z "$AP_HEADS_DIR" ] || [ ! -f "$AP_HEADS_DIR/$hf" ]; then
      apertus_off "the head file $hf is absent: run 'make setup-apertus'."
      return 0
    fi
  done
  if ! { [ -x "$APY" ] || command -v "$APY" >/dev/null 2>&1; }; then
    apertus_off "the Python $(clean "$APY") of the Apertus step is absent: run 'make setup-apertus'."
    return 0
  fi
  if [ -n "$AP_MODEL_DIR" ]; then
    chk=$(cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend "$APERTUS_BACKEND" \
      --model-dir "$AP_MODEL_DIR" 2>/dev/null)
  else
    chk=$(cd "$APP" && "$APY" -I -B worker/apertus_states.py check --root layout --backend "$APERTUS_BACKEND" \
      --no-model 2>/dev/null)
  fi
  AP_BACKEND=$(printf '%s' "$chk" | jq -r '.backend // ""' 2>/dev/null)
  # The backend remote (APERTUS_URL, docs/apertus-gpu.md): the host of the URL and the backend of the service.
  AP_REMOTE_HOST=$(printf '%s' "$chk" | jq -r '.tests.remote.host // ""' 2>/dev/null)
  AP_REMOTE_BACKEND=$(printf '%s' "$chk" | jq -r '.tests.remote.server_backend // ""' 2>/dev/null)
  creason=$(printf '%s' "$chk" | jq -r '.reason // ""' 2>/dev/null)
  if [ -z "$AP_BACKEND" ] || [ -n "$creason" ]; then
    cmsg=$(printf '%s' "$chk" | jq -r '.message // ""' 2>/dev/null)
    apertus_off "${cmsg:-the check of the Apertus step failed (app/worker/apertus_states.py check).}"
    return 0
  fi
  case $AP_BACKEND in
    mlx|cuda|mps|cpu)
      if [ -z "$AP_MODEL_DIR" ]; then
        apertus_off "this computer has no model folder ('make setup-apertus APERTUS_MODEL=none'), and the read-out needs a GPU of another computer: set APERTUS_URL (see $GPU_DOC), or run 'make setup-apertus'."
        return 0
      fi ;;
  esac
  if [ "$AP_BACKEND" = cpu ]; then
    note "APERTUS_BACKEND=cpu: torch on the CPU is very slow (many minutes for one page). Use it only for checks."
  fi
  AP=local
  JOB_TIMEOUT=$APERTUS_TIMEOUT
}

# ---------------------------------------------------------------------------------------------------- convert
check_convert_tools() {
  need jq "Install jq (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."
  command -v shasum >/dev/null 2>&1 || need sha256sum "Install shasum or sha256sum."
  if [ ! -x "$TRACK/.venv/bin/python" ] && [ "$PY" = python3 ]; then
    err "the folder .venv/ is absent. Run 'make setup', then 'make setup-pdf'."
    exit 1
  fi
  if ! { [ -x "$PY" ] || command -v "$PY" >/dev/null 2>&1; }; then
    err "the Python $PY is absent. Run 'make setup', then 'make setup-pdf'."
    exit 1
  fi
  need uv "Install uv (https://docs.astral.sh/uv/), then run 'make setup' and 'make setup-pdf'."
  # The 3 packages that the worker needs for an own PDF, as 'make setup-pdf' installs them (no Python code here).
  found=$(uv pip show --python "$PY" pyyaml docling pypdfium2 2>/dev/null | grep -c '^Name: ')
  if [ "$found" != 3 ]; then
    err "docling, pypdfium2 or pyyaml is absent in $PY. Run 'make setup-pdf' (after 'make setup')."
    exit 1
  fi
  found=$(command -v pdftotext 2>/dev/null || true)
  for p in ${PDFTOTEXT_PLACES:-}; do [ -n "$found" ] || { [ -x "$p" ] && found=$p; }; done
  if [ -z "$found" ]; then
    err "the command pdftotext is absent. Install it (macOS: brew install poppler), then run 'make setup-pdf'."
    exit 1
  fi
  hf=$(dirname "$PY")/hf
  if [ -x "$hf" ]; then
    for m in ${DOCLING_MODELS:-}; do
      repo=${m%@*}; rev=${m#*@}
      if ! HF_HUB_OFFLINE=1 "$hf" download "$repo" --revision "$rev" --quiet >/dev/null 2>&1; then
        err "the Docling model $repo ($rev) is not in the Hugging Face cache. Run 'make setup-pdf'."
        exit 1
      fi
    done
  fi
  # The same check as 'make run-native' before the start: the code layout of app/layout/ (SHA-256 of each file).
  mkdir -p "$OUT/.jobs"
  clog=$OUT/.jobs/check-layout.$$.log
  if ! (cd "$APP" && "$PY" -B worker/layout.py --check --out layout) > "$clog" 2>&1; then
    err "the code layout of app/layout/ differs from app/layout/layout_manifest.json. Log: out/.jobs/${clog##*/}"
    exit 1
  fi
  rm -f "$clog"
}

# Writes the inputs, one for each line, to the file $1.
collect_inputs() {
  list_out=$1
  : > "$list_out"
  if [ -n "$ARG_PDF" ]; then
    printf '%s\n' "$ARG_PDF" >> "$list_out"
  fi
  if [ -n "$ARG_DIR" ]; then
    if [ ! -d "$ARG_DIR" ]; then
      err "DIR=$(clean "$ARG_DIR") is not a folder."
      exit 1
    fi
    dir=$ARG_DIR
    while [ "$dir" != / ] && [ "${dir%/}" != "$dir" ]; do dir=${dir%/}; done
    before=$(wc -l < "$list_out")
    # The files of the folder (also hidden files, no subfolder) whose name ends with .pdf (upper or lower case).
    for f in "$dir"/* "$dir"/.[!.]* "$dir"/..?*; do
      [ -f "$f" ] || continue
      case ${f##*/} in *.[Pp][Dd][Ff]) ;; *) continue ;; esac
      case $f in
        *"$NL"*) note "a file name with a line break is not read: $(clean "$f")"; continue ;;
      esac
      printf '%s\n' "$f"
    done | LC_ALL=C sort >> "$list_out"
    if [ "$(wc -l < "$list_out")" -eq "$before" ]; then
      err "the folder $(clean "$ARG_DIR") has no file whose name ends with .pdf (subfolders are not read)."
      exit 1
    fi
  fi
  if [ -n "$ARG_LIST" ]; then
    if [ ! -f "$ARG_LIST" ]; then
      err "LIST=$(clean "$ARG_LIST") is not a file."
      exit 1
    fi
    base=$(cd "$(dirname "$ARG_LIST")" && pwd)
    tr -d '\r' < "$ARG_LIST" | while IFS= read -r line || [ -n "$line" ]; do
      line=$(printf '%s' "$line" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
      case $line in ''|'#'*) continue ;; esac
      line=$(home_path "$line")
      if is_url "$line"; then printf '%s\n' "$line"
      else case $line in /*|*://*) printf '%s\n' "$line" ;; *) printf '%s/%s\n' "$base" "$line" ;; esac
      fi
    done >> "$list_out"
  fi
}

# Gets one input to the file $2. A local file is copied, a URL is downloaded. Returns 1 with a reason in GET_WHY.
GET_WHY=
get_input() {
  src=$1; dst=$2
  GET_WHY=
  rm -f "$dst" "$dst.curl" "$dst.rc"
  if is_url "$src"; then
    # -q: no ~/.curlrc. --globoff: the URL is used as it is ([ ] and { } are not a URL list).
    # 'head -c' keeps at most MAX_BYTES + 1 bytes on the disk. Some versions of curl cannot stop a download
    # of unknown size at --max-filesize, and this limit also applies to them.
    {
      curl -q --globoff --fail --location --silent --show-error --proto '=http,https' --proto-redir '=http,https' \
        --max-filesize "$MAX_BYTES" --max-time "$DOWNLOAD_TIMEOUT" --output - "$src" < /dev/null 2> "$dst.curl"
      printf '%s\n' "$?" > "$dst.rc"
    } | head -c "$((MAX_BYTES + 1))" > "$dst"
    rc=$(cat "$dst.rc" 2>/dev/null || true)
    case $rc in ''|*[!0-9]*) rc=99 ;; esac
    text=$(tr '\n' ' ' < "$dst.curl" 2>/dev/null | sed 's/^curl: ([0-9]*) //; s/ *$//')
    rm -f "$dst.curl" "$dst.rc"
    if [ "$rc" -eq 63 ] || [ "$(file_bytes "$dst")" -gt "$MAX_BYTES" ]; then
      GET_WHY="download refused: the file is larger than $MAX_BYTES bytes (20 MB)"
      rm -f "$dst"; return 1
    fi
    if [ "$rc" -ne 0 ]; then
      case $rc in
        28) GET_WHY="download stopped: no complete file in $DOWNLOAD_TIMEOUT seconds" ;;
        22) GET_WHY="download failed: $text" ;;
        1) GET_WHY="download refused: only http and https are allowed (also for a redirect)" ;;
        *) GET_WHY="download failed (curl exit code $rc): $text" ;;
      esac
      rm -f "$dst"; return 1
    fi
  else
    case $src in
      *://*) GET_WHY="only a path or an http or https URL is allowed"; return 1 ;;
    esac
    if [ -d "$src" ]; then GET_WHY="this is a folder (use DIR=<folder>)"; return 1; fi
    if [ ! -f "$src" ]; then GET_WHY="no file at this path"; return 1; fi
    if [ ! -r "$src" ]; then GET_WHY="the file cannot be read"; return 1; fi
    if ! cp "$(safe_path "$src")" "$dst" 2>/dev/null; then GET_WHY="the file cannot be copied"; rm -f "$dst"; return 1; fi
  fi
  if [ "$(file_bytes "$dst")" -gt "$MAX_BYTES" ]; then
    GET_WHY="the file is larger than $MAX_BYTES bytes (20 MB, the limit of the app)"
    rm -f "$dst"; return 1
  fi
  if ! has_pdf_mark "$dst"; then
    GET_WHY="the first 1024 bytes have no mark %PDF- (not a PDF file)"
    rm -f "$dst"; return 1
  fi
  return 0
}

# ------------------------------------------------------------------------------------------- the worker process
# The worker runs as the server runs it (app/server/src/jobs.rs, function execute; app/Makefile run-native).
WORKER_PID=
DOG_PID=

# Sends the signal $1 to the processes that the worker started (for example pdftotext).
signal_worker_children() {
  if [ -n "$WORKER_PID" ] && command -v pkill >/dev/null 2>&1; then pkill "-$1" -P "$WORKER_PID" 2>/dev/null; fi
  return 0
}

# Starts a timer in the background. After $1 seconds it writes the file $2 (if $2 is not empty) and sends TERM
# to the worker and its child processes. KILL_GRACE seconds later it sends KILL to them, as the server does.
start_dog() {
  (
    sp=
    trap '[ -n "$sp" ] && kill "$sp" 2>/dev/null; exit 0' TERM
    sleep "$1" &
    sp=$!
    wait "$sp"
    if [ -n "$2" ]; then : > "$2"; fi
    signal_worker_children TERM
    kill -TERM "$WORKER_PID" 2>/dev/null
    sleep "$KILL_GRACE" &
    sp=$!
    wait "$sp"
    signal_worker_children KILL
    kill -KILL "$WORKER_PID" 2>/dev/null
  ) &
  DOG_PID=$!
}

stop_dog() {
  if [ -n "$DOG_PID" ]; then
    kill -TERM "$DOG_PID" 2>/dev/null
    wait "$DOG_PID" 2>/dev/null
  fi
  DOG_PID=
}

# Runs the worker for one PDF. Sets WORKER_CODE (the exit code, or 'timeout').
run_worker() {
  wjob=$1
  if [ "$AP" = local ]; then
    # The Apertus step: worker mode auto; the worker starts app/worker/apertus_states.py for the read-out. The
    # read-out ends at the latest AP_TAIL seconds before the time limit of the job (PARLPDFECH_APERTUS_DEADLINE),
    # so that the worker can still write the record (of the rules, if the read-out did not end in time).
    ap_deadline=$(( $(date +%s) + JOB_TIMEOUT - AP_TAIL ))
    (
      cd "$APP" && exec env PARLPDFECH_PROFILE=native PARLPDFECH_MAX_PAGES="$MAX_PAGES" \
        PARLPDFECH_DATA_DIR="$APP/data" PARLPDFECH_CODE_DIR="$APP/layout" PARLPDFECH_VIEW_DIR="$APP/view" \
        PYTHONUNBUFFERED=1 PARLPDFECH_APERTUS=local PARLPDFECH_APERTUS_PYTHON="$APY" \
        PARLPDFECH_APERTUS_MODEL_DIR="$AP_MODEL_DIR" PARLPDFECH_APERTUS_HEADS_DIR="$AP_HEADS_DIR" \
        PARLPDFECH_APERTUS_HEADS_SOURCE="$AP_HEADS_SOURCE" PARLPDFECH_APERTUS_BACKEND="$AP_BACKEND" \
        PARLPDFECH_APERTUS_TIMEOUT="$((JOB_TIMEOUT - 120))" PARLPDFECH_APERTUS_DEADLINE="$ap_deadline" \
        "$PY" "$APP/worker/serve_convert.py" --pdf "$wjob/input.pdf" --mode auto --out "$wjob/out" \
        --data-dir "$APP/data" < /dev/null > "$wjob/events.jsonl" 2> "$wjob/worker.log"
    ) &
  else
  (
    cd "$APP" && exec env PARLPDFECH_PROFILE=native PARLPDFECH_MAX_PAGES="$MAX_PAGES" \
      PARLPDFECH_DATA_DIR="$APP/data" PARLPDFECH_CODE_DIR="$APP/layout" PARLPDFECH_VIEW_DIR="$APP/view" \
      PYTHONUNBUFFERED=1 \
      "$PY" "$APP/worker/serve_convert.py" --pdf "$wjob/input.pdf" --mode rules --out "$wjob/out" \
      --data-dir "$APP/data" < /dev/null > "$wjob/events.jsonl" 2> "$wjob/worker.log"
  ) &
  fi
  WORKER_PID=$!
  start_dog "$JOB_TIMEOUT" "$wjob/timeout"
  wait "$WORKER_PID"
  WORKER_CODE=$?
  stop_dog
  WORKER_PID=
  if [ -f "$wjob/timeout" ]; then WORKER_CODE=timeout; fi
}

# Stops a worker that runs: TERM now, KILL after KILL_GRACE seconds (the timer of start_dog with 0 seconds).
stop_worker() {
  [ -n "$WORKER_PID" ] || return 0
  stop_dog
  start_dog 0 ""
  wait "$WORKER_PID" 2>/dev/null
  stop_dog
  WORKER_PID=
}

is_refused() {
  [ -n "$1" ] || return 1
  case " $REFUSED_CODES " in *" $1 "*) return 0 ;; esac
  return 1
}

# A document prefix of a record file: the word 'local' or a document number with 1 to 12 digits.
is_doc_prefix() {
  case $1 in
    local) return 0 ;;
    ''|*[!0-9]*) return 1 ;;
  esac
  [ "${#1}" -le 12 ]
}

# True if the name is the name of a record file (app/server/src/ids.rs, function file_media_type).
is_record_file_name() {
  case $1 in
    manifest.json|validation.json|view.json|convert.json|source.pdf) return 0 ;;
    page-*.png)
      pn=${1#page-}; pn=${pn%.png}
      case $pn in ''|0*|*[!0-9]*) return 1 ;; esac
      [ "${#pn}" -le 3 ]
      return ;;
  esac
  for sfx in .values.ttl .gesamt.trig .ech.ttl .gesamt.rdf.xml .ech.rdf.xml .ech.yaml .labels.yaml .provenance.yaml; do
    case $1 in
      *"$sfx") if is_doc_prefix "${1%"$sfx"}"; then return 0; fi ;;
    esac
  done
  return 1
}

# Checks the output folder of the worker with the rules of the server before it stores a record
# (app/server/src/jobs.rs, function install_record; app/server/src/ids.rs, function is_complete_record):
# an entry that is not a record file is deleted. Then view.json and the 11 files of app/CONTRACT.md chapter 3
# must be there, with one document prefix. The only other files are source.pdf, page-<n>.png and
# <prefix>.values.ttl. Prints the note of the server (no_output, no_view or output), or no text if all is correct.
record_check() {
  rdir=$1
  if [ ! -d "$rdir" ] || [ -L "$rdir" ]; then printf 'no_output'; return 0; fi
  kept=0; pages=0; prefix=
  for f in "$rdir"/* "$rdir"/.[!.]* "$rdir"/..?*; do
    [ -e "$f" ] || [ -L "$f" ] || continue
    fname=${f##*/}
    if [ -f "$f" ] && [ ! -L "$f" ] && is_record_file_name "$fname"; then
      kept=$((kept + 1))
      case $fname in
        page-*.png) pages=$((pages + 1)) ;;
        *.gesamt.trig) [ -n "$prefix" ] || prefix=${fname%.gesamt.trig} ;;
      esac
    else
      rm -rf "$f"
    fi
  done
  if [ ! -f "$rdir/view.json" ]; then printf 'no_view'; return 0; fi
  if [ -z "$prefix" ]; then printf 'output'; return 0; fi
  optional=$pages
  [ -f "$rdir/source.pdf" ] && optional=$((optional + 1))
  [ -f "$rdir/$prefix.values.ttl" ] && optional=$((optional + 1))
  if [ "$kept" -ne $((11 + optional)) ]; then printf 'output'; return 0; fi
  for fixed in manifest.json validation.json view.json convert.json; do
    if [ ! -f "$rdir/$fixed" ]; then printf 'output'; return 0; fi
  done
  for sfx in .gesamt.trig .ech.ttl .gesamt.rdf.xml .ech.rdf.xml .ech.yaml .labels.yaml .provenance.yaml; do
    if [ ! -f "$rdir/$prefix$sfx" ]; then printf 'output'; return 0; fi
  done
  return 0
}

# Judges the end of the worker with the rules of the server (app/server/src/jobs.rs, function execute).
# Arguments: the exit code (or 'timeout'), the file of the JSON lines, the output folder, the expected record id.
# Sets OK (1 or 0), WHY (a code and a note), RID and LVALID (yes or no).
judge_worker() {
  jcode=$1; jevents=$2; jout=$3; jwant=$4
  OK=0; WHY=; RID=; LVALID=
  if [ "$jcode" = timeout ]; then WHY=timeout; return 0; fi
  # The answer of the worker is the last JSON line with the event 'done' or 'failed'.
  last=$(jq -R -c 'fromjson? | select(type == "object" and (.event == "done" or .event == "failed"))' \
    "$jevents" 2>/dev/null | tail -n 1)
  if [ -z "$last" ]; then WHY="converter_stopped (exit_$jcode)"; return 0; fi
  event=$(printf '%s' "$last" | jq -r '.event' 2>/dev/null)
  RID=$(printf '%s' "$last" | jq -r 'if (.record_id | type) == "string" then .record_id else "" end' 2>/dev/null)
  LVALID=$(printf '%s' "$last" | jq -r 'if .valid == true then "yes" elif .valid == false then "no" else "" end' 2>/dev/null)
  wcode=$(printf '%s' "$last" | jq -r 'if (.code | type) == "string" then .code else "" end' 2>/dev/null)
  detail=$(printf '%s' "$last" | jq -r '(.detail // {}) | to_entries | map("\(.key) \(.value)") | join(", ")' 2>/dev/null)
  case $event:$jcode in
    done:0|done:2)
      if { [ "$jcode" = 0 ] && [ "$LVALID" != yes ]; } || { [ "$jcode" = 2 ] && [ "$LVALID" != no ]; }; then
        WHY="converter_stopped (protocol)"
      elif [ "$RID" != "$jwant" ] || ! printf '%s' "$RID" | grep -Eq "$RECORD_ID_RE"; then
        WHY="converter_stopped (record_id)"
      else
        rnote=$(record_check "$jout")
        if [ -n "$rnote" ]; then WHY="converter_stopped ($rnote)"; else OK=1; fi
      fi ;;
    failed:3)
      if is_refused "$wcode"; then WHY="$wcode${detail:+ ($detail)}"; else WHY="converter_stopped (protocol)"; fi ;;
    failed:4)
      if [ "$wcode" = converter_stopped ]; then WHY="converter_stopped${detail:+ ($detail)}"
      else WHY="converter_stopped (protocol)"; fi ;;
    *) WHY="converter_stopped (exit_$jcode)" ;;
  esac
  return 0
}

# --------------------------------------------------------------------------------------------- convert: the loop
JOB=
NEW_DEST=
WORK_OPEN=0
COMMIT=0
STOP_ASKED=0
inputs=

on_convert_signal() {
  # A signal while out/<ID>/ changes: the change ends first, then the command stops.
  if [ "$COMMIT" = 1 ]; then STOP_ASKED=1; return 0; fi
  trap '' INT TERM HUP
  stop_worker
  if [ -n "$JOB" ]; then rm -rf "$JOB"; fi
  # The folder of a new ID is still empty here. Without it, the ID is free again.
  if [ -n "$NEW_DEST" ]; then rmdir "$NEW_DEST" 2>/dev/null; fi
  say ""
  if [ "$WORK_OPEN" = 1 ]; then say "Stopped. The PDF of this moment has no new result. The earlier results stay."
  else say "Stopped."; fi
  exit 130
}

# The end of 'convert'. Only the holder of the lock deletes files in out/.jobs/.
convert_exit() {
  if [ "$LOCKED" = 1 ]; then
    if [ -n "$inputs" ]; then rm -f "$inputs"; fi
    rmdir "$OUT/.jobs" 2>/dev/null
  fi
  drop_lock
  return 0
}

convert_cmd() {
  if [ -z "$ARG_PDF$ARG_DIR$ARG_LIST" ]; then
    err "give PDF=<file or URL>, DIR=<folder> or LIST=<file>. Example: make convert PDF=~/Downloads/motion.pdf"
    exit 1
  fi
  for v in "$ARG_PDF" "$ARG_DIR" "$ARG_LIST"; do
    case $v in
      *"$NL"*) err "a value of PDF, DIR or LIST has a line break. Give a path or a URL with no line break."; exit 1 ;;
    esac
  done
  ARG_PDF=$(home_path "$ARG_PDF"); ARG_DIR=$(home_path "$ARG_DIR"); ARG_LIST=$(home_path "$ARG_LIST")
  is_url "$ARG_PDF" || ARG_PDF=$(safe_path "$ARG_PDF")
  ARG_DIR=$(safe_path "$ARG_DIR"); ARG_LIST=$(safe_path "$ARG_LIST")
  trap convert_exit EXIT
  trap on_convert_signal INT TERM HUP
  # First the lock: a second 'make convert' stops here and writes no file.
  need readlink "Install readlink (GNU coreutils or the BSD tools)."
  take_lock
  check_convert_tools
  mkdir -p "$OUT/.jobs"
  inputs=$OUT/.jobs/inputs.$$
  collect_inputs "$inputs"
  total=$(wc -l < "$inputs" | tr -d ' ')
  if [ "$total" -eq 0 ]; then
    err "no input (the list has no path and no URL)."
    exit 1
  fi
  if grep -Eiq '^https?://' "$inputs"; then need curl "Install curl to download a PDF."; fi
  # The catalog again from the files out/<ID>/source.txt (for example after a deletion of out/catalog.tsv).
  catalog_write || note "out/catalog.tsv was not written. The files out/<ID>/source.txt hold the data."
  apertus_mode
  if [ "$AP" = local ] && [ "$AP_BACKEND" = remote ]; then
    say "Inputs: $total. Code rules and Apertus-v1.5-8B on the GPU of another computer (APERTUS_URL, host $(clean "${AP_REMOTE_HOST:-?}"), backend $(clean "${AP_REMOTE_BACKEND:-?}"), bf16, layer 20). Results: out/<ID>/."
    say "The text of each PDF goes to that computer for the read-out. The heads and the record stay on this computer."
  elif [ "$AP" = local ]; then
    say "Inputs: $total. Code rules and Apertus-v1.5-8B (backend $AP_BACKEND, bf16, layer 20). Results: out/<ID>/."
  else
    say "Inputs: $total. Code rules only (no GPU, no Apertus). Results: out/<ID>/."
  fi
  n_valid=0; n_not_valid=0; n_stored=0; n_failed=0; i=0
  while IFS= read -r src; do
    i=$((i + 1))
    say ""
    say "[$i/$total] $(clean "$src")"
    WORK_OPEN=1
    JOB=$OUT/.jobs/job.$$
    NEW_DEST=
    rm -rf "$JOB"
    mkdir -p "$JOB"
    if ! get_input "$src" "$JOB/input.pdf"; then
      say "  FAIL: $(clean "$GET_WHY"). No ID."
      n_failed=$((n_failed + 1))
      rm -rf "$JOB"; JOB=; WORK_OPEN=0
      continue
    fi
    sha=$(sha256_of "$JOB/input.pdf")
    bytes=$(file_bytes "$JOB/input.pdf")
    id=$(id_of_sha "$sha")
    if [ -z "$id" ]; then
      id=$(next_id)
      if ! mkdir "$OUT/$id" 2>/dev/null; then
        say "  FAIL: the folder out/$id/ cannot be made. No ID."
        n_failed=$((n_failed + 1))
        rm -rf "$JOB"; JOB=; WORK_OPEN=0
        continue
      fi
      NEW_DEST=$OUT/$id
      say "  new ID $id (SHA-256 $sha)"
    else
      say "  same PDF as ID $id (the SHA-256 is equal)"
    fi
    dest=$OUT/$id
    # The record id that the server expects (app/server/src/jobs.rs, POST /api/jobs, mode rules).
    doc=$(jq -r --arg s "$sha" 'first(.samples[] | select(.pdf_sha256 == $s) | .doc_id | tostring) // ""' \
      "$APP/data/samples/index.json" 2>/dev/null)
    if [ -n "$doc" ]; then want=s-$doc-rules; else want=u-$(printf '%s' "$sha" | cut -c1-16)-rules; fi
    # The mode auto (Apertus step) has the record ids with no suffix -rules (app/server/src/jobs.rs).
    if [ "$AP" = local ]; then want=${want%-rules}; fi
    # A stored result of the other Apertus state (made with Apertus, asked without it, or the other way; or a
    # record id of the other worker mode) is converted again (same ID; the record is replaced).
    stored_ap=none
    if [ -f "$dest/record/convert.json" ]; then
      stored_ap=$(jq -r '.apertus_values.state // "none" | tostring' "$dest/record/convert.json" 2>/dev/null || echo none)
    fi
    case $stored_ap in local|remote|stored) stored_ap=local ;; *) stored_ap=none ;; esac
    stored_rid=$(info_value "$dest/source.txt" record_id)
    again=$ARG_AGAIN
    if [ -f "$dest/record/view.json" ] && [ "$again" != 1 ] && { [ "$stored_ap" != "$AP" ] || [ "$stored_rid" != "$want" ]; }; then
      if [ "$AP" = local ]; then say "  the stored result (record $(clean "${stored_rid:-?}")) was made without Apertus; it is converted again with Apertus"
      else say "  the stored result (record $(clean "${stored_rid:-?}")) was made with the Apertus step; it is converted again with the code rules only"; fi
      again=1
    fi
    if [ -f "$dest/record/view.json" ] && [ "$again" != 1 ]; then
      rm -rf "$JOB"; JOB=; WORK_OPEN=0
      # The stored record must be the record of this PDF: the SHA-256 in its convert.json is the SHA-256 of this PDF.
      rsha=$(jq -r '.pdf_sha256 // "" | tostring' "$dest/record/convert.json" 2>/dev/null)
      if [ "$rsha" = "$sha" ]; then
        say ""
        print_summary "$id" "stored result; AGAIN=1 converts it again"
        n_stored=$((n_stored + 1))
      else
        say "  FAIL: out/$id/record/ holds a record whose SHA-256 is not the SHA-256 of this PDF. AGAIN=1 replaces it."
        n_failed=$((n_failed + 1))
      fi
      continue
    fi
    say "  conversion starts (record $want) ..."
    started=$(date +%s)
    run_worker "$JOB"
    seconds=$(( $(date +%s) - started ))
    judge_worker "$WORKER_CODE" "$JOB/events.jsonl" "$JOB/out" "$want"
    # All values for out/<ID>/source.txt are ready before the change of out/<ID>/ starts.
    c_src=$(cell "$src")
    c_type=-; c_title=-
    if [ "$OK" = 1 ]; then
      c_type=$(cell "$(jq -r '.document.affair_type // "-" | tostring' "$JOB/out/view.json" 2>/dev/null)")
      c_title=$(cell "$(jq -r '.document.title // "-" | tostring' "$JOB/out/view.json" 2>/dev/null)")
    fi
    when=$(now)
    word=${WHY%% *}
    # The change of out/<ID>/. A signal now waits until the change ends. First the data of the ID, then the
    # record: after a stop at any step, the ID and its SHA-256 stay together.
    COMMIT=1
    mv -f "$JOB/worker.log" "$dest/worker.log" 2>/dev/null
    mv -f "$JOB/events.jsonl" "$dest/worker.events.jsonl" 2>/dev/null
    if [ "$OK" = 1 ]; then
      rm -rf "$dest/record.old"
      rm -f "$dest/source.txt.old"
      if [ -f "$dest/source.txt" ]; then
        ln "$dest/source.txt" "$dest/source.txt.old" 2>/dev/null || cp -p "$dest/source.txt" "$dest/source.txt.old"
      fi
      write_info "$dest" "$c_src" "$sha" "$bytes" "$when" "$seconds" "$RID" "$LVALID" "${c_type:--}" "${c_title:--}"
      if [ -e "$dest/record" ]; then move "$dest/record" "$dest/record.old"; fi
      if [ ! -e "$dest/record" ]; then move "$JOB/out" "$dest/record"; fi
      if [ -f "$dest/record/view.json" ] && [ ! -e "$JOB/out" ]; then
        rm -rf "$dest/record.old"
        rm -f "$dest/source.txt.old"
      else
        if [ ! -e "$dest/record" ] && [ -d "$dest/record.old" ]; then move "$dest/record.old" "$dest/record"; fi
        if [ -f "$dest/source.txt.old" ]; then move "$dest/source.txt.old" "$dest/source.txt"; fi
        OK=0; WHY="converter_stopped (record_move)"; word=converter_stopped
      fi
    fi
    if [ "$OK" != 1 ] && [ ! -f "$dest/record/view.json" ]; then
      write_info "$dest" "$c_src" "$sha" "$bytes" "$when" "$seconds" "-" "failed:$word" "-" "-"
    fi
    NEW_DEST=
    WORK_OPEN=0
    COMMIT=0
    rm -rf "$JOB"; JOB=
    catalog_write || note "out/catalog.tsv was not written. The files out/<ID>/source.txt hold the data."
    if [ "$OK" = 1 ]; then
      say ""
      print_summary "$id" "converted in $seconds s"
      if [ "$LVALID" = yes ]; then n_valid=$((n_valid + 1)); else n_not_valid=$((n_not_valid + 1)); fi
    else
      say "  FAIL: $(reason_text "$word")$(clean "${WHY#"$word"}"). Log: out/$id/worker.log"
      if [ -f "$dest/record/view.json" ]; then say "  The stored result of ID $id stays (out/$id/record/)."; fi
      n_failed=$((n_failed + 1))
    fi
    if [ "$STOP_ASKED" = 1 ]; then
      say ""
      say "Stopped after the change of out/$id/ ended."
      exit 130
    fi
  done < "$inputs"
  rm -f "$inputs"
  rmdir "$OUT/.jobs" 2>/dev/null
  drop_lock
  trap - INT TERM HUP
  say ""
  say "End. Inputs: $total. Valid: $n_valid. Not valid (record written, a check failed): $n_not_valid."
  say "Stored results shown again: $n_stored. Failed: $n_failed. All IDs: make list"
  if [ "$AP" = local ]; then say "The values come from code rules and Apertus read-outs. Each value can be wrong."
  else say "The values come from code rules. Each value can be wrong."; fi
  [ "$n_failed" -eq 0 ]
}

# ---------------------------------------------------------------------------------------------------- list
# 'make list' reads the files out/<ID>/source.txt (the reference), not out/catalog.tsv.
list_cmd() {
  need jq "Install jq (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."
  if [ -z "$(info_files | head -n 1)" ]; then
    say "No result yet. Convert a PDF with: make convert PDF=<file or URL>"
    return 0
  fi
  catalog_rows | jq -R -r -s '
    def safe: '"$SAFE_JQ"';
    def short($n): if length > $n then .[0:($n - 3)] + "..." else . end;
    def tail($n): if length > $n then "..." + .[(length - $n + 3):] else . end;
    def pad($n): if length < $n then . + (" " * ($n - length)) else . end;
    [split("\n")[] | select(length > 0) | split("\t") | map(safe)]
    | map({id: .[0], sha: (.[1] // "" | .[0:12]), src: (.[2] // "" | tail(40)),
           time: (.[3] // "" | .[0:16] | sub("T"; " ")), valid: (.[4] // ""), type: (.[5] // ""),
           title: (.[6] // "" | short(40))}) as $rows
    | ["ID", "VALID", "TIME", "AFFAIR TYPE", "TITLE", "SOURCE", "SHA-256"] as $head
    | ($rows | map([.id, .valid, .time, .type, .title, .src, .sha])) as $cells
    | [range(0; 7) as $c | ([$head[$c]] + ($cells | map(.[$c])) | map(length) | max)] as $w
    | ([$head] + $cells)[] | [range(0; 7) as $c | .[$c] | pad($w[$c])] | join("  ") | sub(" +$"; "")
  '
  say ""
  say "Folder of an ID: out/<ID>/. All columns (full SHA-256 and source): out/catalog.tsv"
  say "Open one result in the browser: make view ID=<ID>"
}

# ---------------------------------------------------------------------------------------------------- view
# Checks the ID and prints the record id of its stored result.
view_record_id() {
  need jq "Install jq (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."
  vid=$(normal_id "$1") || { err "ID=$(clean "$1") is not an ID. An ID is a number, for example ID=0001. 'make list' shows the IDs."; return 1; }
  vrec=$OUT/$vid/record
  if [ ! -f "$vrec/view.json" ]; then
    err "ID $vid has no stored result in out/$vid/record/. 'make list' shows the IDs."
    return 1
  fi
  vrid=$(jq -r '.record_id // ""' "$vrec/view.json" 2>/dev/null)
  if ! printf '%s' "$vrid" | grep -Eq "$RECORD_ID_RE"; then
    err "out/$vid/record/view.json has no valid record id."
    return 1
  fi
  printf '%s %s\n' "$vid" "$vrid"
}

# The local calls of curl: -q (no ~/.curlrc) and --noproxy '*' (127.0.0.1 never goes through a proxy).
local_curl() { curl -q --noproxy '*' "$@" < /dev/null; }

# True if a process answers on 127.0.0.1:<port> (curl exit code 7 = no connection).
port_busy() {
  local_curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$1/" 2>/dev/null
  [ $? -ne 7 ]
}

SERVER_PID=
VIEW_WORK=
stop_server() {
  if [ -n "$SERVER_PID" ]; then
    kill -TERM "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
  SERVER_PID=
  [ -n "$VIEW_WORK" ] && rm -rf "$VIEW_WORK"
}
on_view_signal() {
  stop_server
  say ""
  say "The view server stopped."
  exit 0
}

view_cmd() {
  need curl "Install curl."
  pair=$(view_record_id "$ARG_ID") || exit 1
  id=${pair%% *}; rid=${pair#* }
  if [ ! -x "$SERVER_BIN" ]; then
    err "the server of the app is not built ($SERVER_BIN). 'make view' builds it with cargo, as 'make run-native' does."
    exit 1
  fi
  # Folders of earlier view servers whose process ended (the name ends with the process id).
  for d in "$OUT"/.view/*-*; do
    [ -d "$d" ] || continue
    p=${d##*-}
    case $p in ''|*[!0-9]*) continue ;; esac
    kill -0 "$p" 2>/dev/null || rm -rf "$d"
  done
  # The work folder of this server holds only the record of this ID (a copy). It is not app/work/.
  VIEW_WORK=$OUT/.view/$id-$$
  rm -rf "$VIEW_WORK"
  mkdir -p "$VIEW_WORK/records"
  cp -R "$OUT/$id/record" "$VIEW_WORK/records/$rid"
  trap on_view_signal INT TERM HUP
  if [ -n "$ARG_PORT" ]; then
    case $ARG_PORT in ''|*[!0-9]*) err "PORT=$(clean "$ARG_PORT") is not a number."; rm -rf "$VIEW_WORK"; exit 1 ;; esac
    ports=$ARG_PORT
  else
    ports=$(seq 8080 8179)
  fi
  worker_cmd=$(jq -cn --arg a "$PY" --arg b "$APP/worker/serve_convert.py" '[$a, $b]')
  port=
  for p in $ports; do
    if port_busy "$p"; then
      [ -n "$ARG_PORT" ] && { err "the port $p is in use. Give another port (PORT=<n>) or no PORT."; rm -rf "$VIEW_WORK"; exit 1; }
      continue
    fi
    # The variables of 'make run-native' (app/Makefile), with a read-only server: it takes no PDF and deletes nothing.
    env -u PARLPDFECH_SITE_DIR -u PARLPDFECH_HOSTED -u PARLPDFECH_ALLOWED_HOSTS \
      PARLPDFECH_PROFILE=native PARLPDFECH_BIND="127.0.0.1:$p" PARLPDFECH_UI_DIR="$APP/ui" \
      PARLPDFECH_DATA_DIR="$APP/data" PARLPDFECH_WORK_DIR="$VIEW_WORK" PARLPDFECH_CODE_DIR="$APP/layout" \
      PARLPDFECH_VIEW_DIR="$APP/view" PARLPDFECH_WORKER_CMD="$worker_cmd" PARLPDFECH_WORKER_CWD="$APP" \
      PARLPDFECH_READONLY=1 PARLPDFECH_SAMPLE_RUNS=off \
      "$SERVER_BIN" < /dev/null > "$VIEW_WORK/server.log" 2>&1 &
    SERVER_PID=$!
    up=0
    t=0
    while [ "$t" -lt 30 ]; do
      if ! kill -0 "$SERVER_PID" 2>/dev/null; then break; fi
      if [ "$(local_curl -s --max-time 2 "http://127.0.0.1:$p/healthz" 2>/dev/null)" = ok ]; then up=1; break; fi
      sleep 1
      t=$((t + 1))
    done
    if [ "$up" = 1 ] && kill -0 "$SERVER_PID" 2>/dev/null; then
      code=$(local_curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$p/api/records/$rid")
      if [ "$code" = 200 ]; then port=$p; break; fi
      err "the server on port $p gave the HTTP status $code for the record $rid."
      tail -n 5 "$VIEW_WORK/server.log" >&2
      stop_server
      exit 1
    fi
    if kill -0 "$SERVER_PID" 2>/dev/null; then
      err "the server gave no answer on /healthz in 30 seconds. The last lines of its log:"
      tail -n 5 "$VIEW_WORK/server.log" >&2
      stop_server
      exit 1
    fi
    wait "$SERVER_PID" 2>/dev/null
    SERVER_PID=
    if grep -q 'bind failed' "$VIEW_WORK/server.log" && [ -z "$ARG_PORT" ]; then continue; fi
    err "the server did not start. The last lines of its log:"
    tail -n 5 "$VIEW_WORK/server.log" >&2
    rm -rf "$VIEW_WORK"
    exit 1
  done
  if [ -z "$port" ]; then
    err "no free port from 8080 to 8179. Give one with PORT=<n>."
    rm -rf "$VIEW_WORK"
    exit 1
  fi
  url="http://127.0.0.1:$port/app/#/view/$rid"
  say "ID $id: $url"
  say "A local server shows this result only (read-only, on 127.0.0.1). Process $SERVER_PID. Stop it with Ctrl-C."
  if [ "$ARG_OPEN" != no ]; then
    if [ "$(uname -s)" = Darwin ] && command -v open >/dev/null 2>&1; then open "$url"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1
    else say "Open the address above in a browser."; fi
  fi
  wait "$SERVER_PID"
  rc=$?
  SERVER_PID=
  rm -rf "$VIEW_WORK"
  say "The view server stopped (exit code $rc)."
  exit "$rc"
}

# ---------------------------------------------------------------------------------------------------- arguments
ARG_PDF=; ARG_DIR=; ARG_LIST=; ARG_AGAIN=; ARG_ID=; ARG_PORT=; ARG_OPEN=
command=${1:-}
[ $# -gt 0 ] && shift
while [ $# -gt 0 ]; do
  [ $# -ge 2 ] || { err "the option $1 has no value."; exit 2; }
  case $1 in
    --pdf) ARG_PDF=$2 ;;
    --dir) ARG_DIR=$2 ;;
    --list) ARG_LIST=$2 ;;
    --again) ARG_AGAIN=$2 ;;
    --id) ARG_ID=$2 ;;
    --port) ARG_PORT=$2 ;;
    --open) ARG_OPEN=$2 ;;
    *) err "unknown option $1"; exit 2 ;;
  esac
  shift 2
done

case $command in
  convert) convert_cmd ;;
  list) list_cmd ;;
  view-check)
    if [ -z "$ARG_ID" ]; then err "give the ID, for example 'make view ID=0001'. 'make list' shows the IDs."; exit 1; fi
    view_record_id "$ARG_ID" > /dev/null ;;
  view)
    if [ -z "$ARG_ID" ]; then err "give the ID, for example 'make view ID=0001'. 'make list' shows the IDs."; exit 1; fi
    view_cmd ;;
  *) err "usage: convert.sh convert|list|view-check|view [options]"; exit 2 ;;
esac

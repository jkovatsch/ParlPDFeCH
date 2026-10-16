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
#   convert.sh show --id <ID>        (the table of a stored result again, as 'make convert' shows it; no worker)
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
# The terminal: VERBOSE=1 (only the value 1) also shows the full path or URL, the SHA-256, the record id, the
# details of the read-out and each full value that the table cuts. Colours only if the standard output is a
# terminal, NO_COLOR is not set or empty, and TERM is set and is not 'dumb' (https://no-color.org). The table needs
# a terminal of 100 columns; a narrower terminal gets a grey line that says so.
# APERTUS=auto with no Apertus step at this moment (a NOTE) keeps a stored Apertus result of the same PDF and shows
# it again; AGAIN=1 or APERTUS=0 converts it again with the code rules only.
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
AP_AUTO_OFF=0
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

# ---------------------------------------------------------------------------------------------------- the terminal
# The output of 'make convert' and of 'convert.sh show'. For each PDF: a head line, a status line, a table of the
# values and the lines of the Apertus step. At the end: one line with the counts and the explanation of the marks.
# The jq programs read view.json of the record (the values, the Apertus suggestions below the entry limit with their
# wording, the entries of the cascade, valid) and its convert.json with --slurpfile c (the facts of the Apertus step,
# the times, the checks; [] if the file is absent). The same programs show a new record, a stored record and a
# record of an earlier version of the worker (it has no suggestion). jq counts the width in characters (sh counts
# bytes), thus each width and each cut is made in jq. The function safe changes each control character of a text
# before a colour code is added: no text of a PDF, a file name or a URL can put its own escape sequence on the
# terminal.
case ${VERBOSE:-0} in 1) VERBOSE=1 ;; *) VERBOSE=0 ;; esac
ESC=$(printf '\033')
# ERASE: the line 'converting ...' goes away after the worker (only on a terminal). COLOR: the rule of no-color.org.
ERASE=0
COLOR=0
if [ -t 1 ] && [ "${TERM:-dumb}" != dumb ]; then
  ERASE=1
  if [ -z "${NO_COLOR:-}" ]; then COLOR=1; fi
fi
if [ "$COLOR" = 1 ]; then CJ=true; else CJ=false; fi
if [ "$VERBOSE" = 1 ]; then VJ=true; else VJ=false; fi
# The word for this computer in the run head line and in the read-out line of a block.
if [ "$(uname -s 2>/dev/null)" = Darwin ]; then HERE_NAME="this Mac"; else HERE_NAME="this computer"; fi
# The marks that the printed tables use (the words of the last line of BLOCK_JQ), the number of printed tables, and
# the lines of the list 'Not valid or failed' at the end.
MARKS=
N_TABLES=0
TROUBLE=

# The colour code $1 around the text $2 (green 32, yellow 33, red 31, grey 90), for a line that sh prints.
paint() {
  if [ "$COLOR" = 1 ] && [ -n "$2" ]; then printf '%s[%sm%s%s[0m' "$ESC" "$1" "$2" "$ESC"; else printf '%s' "$2"; fi
}

# jq with the argument color (true or false), which the function paint of LIB_JQ needs.
jqt() { jq --argjson color "$CJ" "$@"; }

# The jq functions of all programs of the terminal. The table has these columns after an indent of 6: field 15,
# value 27, probability 5, status 7, source 8, page 4, with 2 spaces between them. A note of at most 16 characters
# follows at column 84 (it ends at column 100). The right part of a head line ends at column 84. No line is longer
# than 100 characters, except the full values of VERBOSE=1.
LIB_JQ='
def safe: '"$SAFE_JQ"';
def flat: tostring | gsub("[[:space:]]+"; " ") | sub("^ "; "") | sub(" $"; "") | safe;
def sp($n): if $n > 0 then " " * $n else "" end;
def pad($n): . + sp($n - length);
def cut($n): if length > $n then .[0:($n - 1)] + "…" else . end;
def mid($n): if length <= $n then . elif $n < 3 then .[0:$n]
  else (($n / 2) | floor) as $a | (($n - 1) - $a) as $b | .[0:$a] + "…" + .[(length - $b):] end;
def wrap($w): reduce (split(" ")[]) as $t ([];
  if length == 0 then [$t]
  elif (.[length - 1] | length) + 1 + ($t | length) <= $w then (length - 1) as $l | .[$l] += " " + $t
  else . + [$t] end);
def paint($k): if $color and $k != "" and . != "" then "\u001b[" + $k + "m" + . + "\u001b[0m" else . end;
def p2: if type != "number" then ""
  else (. * 100 | round) as $n | (($n / 100) | floor | tostring) + "."
       + (($n % 100) | tostring | if length < 2 then "0" + . else . end) end;
def fname: {"affair_type": "affair type", "title": "title", "affair_number": "affair number",
  "submission_date": "submission date", "sponsor": "first author", "response_date": "response date",
  "responder": "responder"}[.] // (tostring | safe);
def rank: . as $f | ["affair_type", "title", "affair_number", "submission_date", "sponsor", "response_date",
  "responder"] | index($f) // 99;
def dname: tostring
  | if test("^[A-Za-z][A-Za-z0-9+.-]*://") then
      sub("^[^:]*://"; "") | sub("[?#].*$"; "") | sub("/+$"; "") | split("/") as $p
      | ($p[0] | sub("^.*@"; "")) as $h
      | if ($p | length) <= 1 then $h elif ($p | length) == 2 then $h + "/" + $p[1] else $h + "/…/" + $p[-1] end
    else sub("/+$"; "") | split("/") as $p | ($p[-1] // "") as $b
      | if ($b | ascii_downcase) == "source.pdf" and ($p | length) >= 2
           and ([".", "..", ""] | any(.[]; . == $p[-2]) | not) then $p[-2] + "/" + $b else $b end end
  | safe;
'

# The head line of one input: "[i/N] <file name or host/.../last part of the URL>" and the right part at column 84.
# The file name source.pdf (the name of the samples, app/data/samples/<doc>/source.pdf) keeps its folder:
# "26171/source.pdf". A long name is cut in the middle.
HEAD_JQ='
($src | dname) as $n
| ([84 - ($left | length) - 3 - ($right | length), 12] | max) as $room
| ($n | mid($room)) as $m
| $left + " " + $m + sp([84 - ($left | length) - 1 - ($m | length) - ($right | length), 2] | max) + $right
'

# The list "Not valid or failed" at the end. Input: the lines of TROUBLE ("[i/N]", source, text; a tab between).
TROUBLE_JQ='
[split("\n")[] | select(length > 0) | split("\t")
 | {left: (.[0] // ""), name: ((.[1] // "") | dname | mid(40)), text: ((.[2] // "") | flat)}] as $t
| ([$t[] | .left | length] | max) as $lw | ([$t[] | .name | length] | max) as $nw
| $t[] | "  " + (.left | pad($lw)) + " " + (.name | pad($nw)) + "   " + (.text | cut([95 - $lw - $nw - 3, 20] | max))
'

# The line "✗ failed: <text>" (the mark in red), in lines of at most 100 characters.
FAIL_JQ='
("✗ failed: " + ($t | flat)) | wrap(92) as $w | range(0; $w | length) as $j
| if $j == 0 then "      " + ($w[0] | sub("^✗ failed"; ("✗ failed" | paint("31")))) else "        " + $w[$j] end
'

# The block of one record. Input: view.json. Arguments: $c (convert.json, [] if absent), $state (new, again or
# stored), $wall (seconds of the worker), $when and $rid (of out/<ID>/source.txt), $id, $verbose, and the optional
# $here ("this Mac" or "this computer"). The last line of the output holds the words of the marks that the block
# uses ("marks table below weak addr few head near cut"); print_block does not print it. The column Prob. is the
# probability of the value in the record (or of the tier of a suggestion); the lines of the Apertus step give the
# head probability, another number. A suggestion with fewer than 30 development documents gets "n=<n>": the same
# limit as make view (FEW_DOCS of app/ui/app.js, rule G6 item 14).
BLOCK_JQ='
def ap: ($c[0].apertus_values // {});
def here: ($ARGS.named.here // "this computer");
def loopback($h): ["127.0.0.1", "localhost", "::1", "[::1]"] | any(.[]; . == $h);
def apon: (ap.state // "none") as $s | ($s == "local" or $s == "remote" or $s == "stored");
def near($f): if $f == "affair_type" then (ap.q1.near // false) else (ap.q2[$f].near // false) end;
def pg($a; $b): if ($a | type) != "number" then ""
  elif ($b | type) == "number" and $b != $a then
    (($a | tostring) + "-" + ($b | tostring)) as $s | (if ($s | length) <= 4 then $s else ($a | tostring) + "+" end)
  else ($a | tostring) end;
def scol: {"certain": "32", "unsure": "33", "weak": "33", "below": "33"}[.] // "";
def rows:
  (.values // []) as $v | (.apertus_suggestions // []) as $s | (($v | map(.field)) + ($s | map(.field))) as $sf
  | [ $v[] | {field, g: (if .written then 0 else 1 end), sub: 0,
        value: ((.value // .value_printed // "") | flat), p: .probability,
        status: (if .written then ((.value_status // "") | flat) elif .candidate == "addressee" then "–" else "weak" end),
        source: (if ((.tier // "") | tostring | startswith("apertus_")) then "Apertus" + (if near(.field) then "*" else "" end)
                 else "rules" end),
        page: pg(.page; .last_page), few: false,
        note: (if .written then "" elif .candidate == "addressee" then "addressed body" else "label file only" end)} ]
  + [ $s[] | {field, g: 1, sub: 1, value: ((.value // .value_printed // "") | flat), p: .probability,
        status: "below", source: ("Apertus" + (if .near then "*" else "" end)), page: pg(.page; .last_page),
        few: ((.n | type) == "number" and .n < 30),
        note: (if (.n | type) == "number" and .n < 30 then "values file n=" + (.n | tostring) else "values file only" end)} ]
  + [ (.head_values.cascade.entries // [])[] | select(.state == "not_found_in_pdf" or .state == "reader_scope")
        | select(.field as $f | ($sf | any(.[]; . == $f)) | not)
        | {field, g: 2, sub: 0, mark: "–", text: "not found"} ]
  + [ (.head_values.cascade.entries // [])[] | select(.state == "not_searched")
        | select(.field as $f | ($sf | any(.[]; . == $f)) | not)
        | {field, g: 3, sub: 0, mark: "·", text: "not in this kind of document"} ]
  | sort_by(.g, (.field | rank), .sub);
def table($r):
  if ($r | length) == 0 then "      no values read from the PDF"
  else
    ("      " + ("Field" | pad(15)) + "  " + ("Value" | pad(27)) + "  " + ("Prob." | pad(5)) + "  "
     + ("Status" | pad(7)) + "  " + ("Source" | pad(8)) + "  " + "Page"),
    ("      " + ([15, 27, 5, 7, 8, 4] | map("─" * .) | join("  ") | paint("90"))),
    (range(0; $r | length) as $i | $r[$i] as $x
     | (if $i > 0 and $r[$i - 1].field == $x.field then "" else ($x.field | fname | cut(15)) end) as $fn
     | if $x.text then ("      " + ($fn | pad(15)) + "  " + ($x.mark | pad(45)) + $x.text) | paint("90")
       else ("      " + ($fn | pad(15)) + "  " + ($x.value | cut(27) | pad(27)) + "  " + ($x.p | p2 | pad(5)) + "  "
         + ($x.status | pad(7) | paint($x.status | scol)) + "  " + ($x.source | pad(8)) + "  "
         + (if $x.note == "" then $x.page else ($x.page | pad(4)) + "  " + ($x.note | paint("90")) end))
         | sub(" +$"; "")
       end)
  end;
def secs: if type == "number" then (round | tostring) + " s" else "" end;
def tsplit:
  ($c[0] // {}) as $k | ($k.seconds // {}) as $t | ($k.stages // []) as $st
  | (($st | map(select(.id == "read_pdf")) | .[0].origin) == "stored") as $pdfstored
  | [ (if $pdfstored then "PDF stored" else "PDF " + ((($t.read_pdf // 0) + ($t.lines // 0) + ($t.rules // 0)) | secs) end),
      (($st | map(select(.id == "apertus")) | .[0].state // "skipped") as $a
       | if $a == "done" or $a == "failed" then "Apertus " + (($t.apertus // 0) | secs) else empty end),
      ("RDF " + ((($t.write // 0) + ($t.check // 0)) | secs)) ]
  | join(" · ");
def check_id: ([splits("_")] | map(select(test("^C[0-9]+$")))) as $ids
  | if ($ids | length) > 0 then ($ids | join("/")) else gsub("_"; " ") end;
def failed_checks($v):
  (if ($c | length) > 0 and ($c[0].checks | type) == "object" then
     [$c[0].checks | to_entries[] | select(.value == false) | .key | check_id]
   else [($v.checks // [])[] | select(.state == "failed") | .id | tostring | check_id] end) | join(", ");
def status_line($v):
  ($v.run.valid // false) as $ok
  | failed_checks($v) as $fc
  | (if $ok then ["✓ valid", "32", " eCH-0295 record"]
     else ["✗ NOT valid", "31", ": record written, a check failed" + (if $fc != "" then " (" + $fc + ")" else "" end)]
     end) as $h
  | (if $state == "stored" then
       "stored result" + (if $when != "" then " of " + ($when | flat | .[0:16] | sub("T"; " ")) else "" end)
       + " · AGAIN=1 converts it again"
     else (if $wall != "" then $wall + " s" else "" end)
          + (if ($c | length) > 0 then (if $wall != "" then "  " else "" end) + "(" + tsplit + ")" else "" end) end) as $tail
  | ("      " + ($h[0] | paint($h[1])) + $h[2]) as $first
  | if $tail == "" then $first
    elif 6 + (($h[0] + $h[2]) | length) + 3 + ($tail | length) <= 100 then $first + " · " + $tail
    else $first, ("        " + $tail) end;
def bname: {"mlx": "MLX", "cuda": "CUDA", "mps": "torch MPS", "cpu": "CPU"}[. // ""] // ((. // "-") | flat);
def readout:
  (ap.state // "none") as $s
  | "read-out: "
    + (if $s == "stored" then "stored states (no model ran)"
       elif $s == "remote" then ((ap.remote_host // "?") | flat) as $h
         | (if loopback($h) then "Apertus service at " + $h else "GPU of " + $h end)
           + " (" + ((ap.backend // "-") | tostring | sub("^remote:"; "") | bname) + ")"
       else (ap.backend | bname) + (if $verbose then "" else ", " + here end) end)
    + (if $verbose then
         ([ (if $s != "stored" then
               ([(ap.device // empty | flat), (ap.dtype // empty | flat | sub("^bfloat16$"; "bf16"))] | join(", "))
             else empty end),
            ("layer " + ((ap.heads.layer // 20) | tostring)) ] | map(select(. != "")) | ", " + join(", "))
         + ([ (if (ap.passes | type) == "number" then (ap.passes | tostring) + " passes" else empty end),
              ((ap.seconds.seconds // ap.seconds.read_out) | if type == "number" then (round | tostring) + " s" else empty end),
              (ap.peak_bytes | if type == "number" then "peak " + ((. / 1e9 * 10 | round) / 10 | tostring) + " GB"
                               else empty end) ] | map(" · " + .) | join(""))
       else "" end);
def q1lines($v):
  (ap.q1 // {}) as $q | (($q.class // "-") | flat) as $k
  | (if ($q.probability | type) == "number" then " (head " + ($q.probability | p2) + ")" else "" end) as $h
  | ($v.document.affair_type // null) as $rt
  | ["type: " + $k + $h + ", "
     + ({"used": ("used, place p." + (($q.page // "?") | tostring) + " " + (($q.block // "?") | flat) + " found by code"
                  + (if (($q.place_option_types // []) | length) >= 2
                     then " (in a list of types: the choice is not shown)" else "" end)),
         "no_evidence": "no type word of this type in the text: not written",
         "rules_gave_the_type": (if $k == $rt then "same as the rules" elif $k == "none" then "class none: the rules decide"
                                 else "below 0.80: the rules decide" end),
         "rules_gave_the_type_apertus_differs": ("differs from the rules (" + (($rt // "-") | flat) + "): the rules decide"),
         "below_threshold": "below 0.80: not used (no measured tier)",
         "class_none": "class none: not used (no measured tier)"}[$q.state // ""] // "not used")
     + (if $q.near then " *" else "" end)];
def q2lines($v):
  ((ap.suggestions // []) + ($v.apertus_suggestions // [])) as $sg
  | (ap.q2 // {}) | to_entries | map(select(.value.called_because != null)) | sort_by(.key | rank)
  | if length == 0 then ["fields: not asked (the rules found each searched value)"]
    else map(.key as $f | .value as $x
      | ($f | fname) + ": block " + (($x.top_block // "-") | flat)
        + (if ($x.head_probability | type) == "number" then " (head " + ($x.head_probability | p2) + ")" else "" end)
        + ", "
        + (if $x.state == "used" then "used"
           elif $x.state == "below_band_hi" or $x.state == "tier_not_entered" then
             (if any($sg[]; .field == $f) then "below the entry limit: values file only"
              else "below the entry limit: not used" end)
           elif $x.state == "below_0_50" then "below 0.50: no value"
           elif $x.state == "no_value" then "no value in this block"
           else (($x.state // "-") | flat) end)
        + (if $x.near then " *" else "" end)) end;
# A record of a worker of before the suggestions (16.10.2026): no key of the suggestions in view.json and in
# convert.json, and a called field below the entry limit. AGAIN=1 converts it again with the suggestions.
def older($v):
  ($v | has("apertus_suggestions") | not) and ((ap | has("suggestions")) | not)
  and ((ap.q2 // {}) | to_entries | any(.[]; .value.called_because != null
       and (.value.state == "below_band_hi" or .value.state == "tier_not_entered")));
def apblock($v):
  (ap.state // "none") as $s
  | (if $s == "failed" then
       [((ap.message // ap.reason // "unknown") | flat | sub("[.;:, ]+$"; "") | cut(60)
         | if endswith("…") then (.[0:(length - 1)] | sub("[.;:, ]+$"; "")) + "…" else . end) as $m
        | "not run: " + $m + (if $m | endswith("…") then " " else ". " end) + "The values come from code rules."]
     elif apon then
       [ (if $state == "stored" or $s == "stored" or $s == "remote" or $verbose then readout else empty end) ]
       + q1lines($v) + q2lines($v)
       + (if older($v) then ["older result with no suggestions: AGAIN=1 converts it again with them" | paint("90")]
          else [] end)
     else [] end) as $l
  | range(0; $l | length) as $i | ($l[$i] | wrap(83)) as $w | range(0; $w | length) as $j
  | "      " + ((if $i == 0 and $j == 0 then "Apertus" else "" end) | pad(9)) + (if $j > 0 then "  " else "" end)
    + (if $i == 0 and $j == 0 and $s == "failed" then ($w[0] | sub("^not run"; ("not run" | paint("33")))) else $w[$j] end);
. as $v
| rows as $r
| ((ap.state // "none") as $s | apon or $s == "failed") as $apb
| status_line($v),
  (if $verbose then "      " + ("record" | pad(9)) + ($rid | flat) else empty end),
  "",
  table($r),
  (if $verbose then
     # each cut value one time; 2 different values of one field (a rule value and a suggestion) get their source
     ($r | map(select(.text == null and (.value | length) > 27))) as $cv
     | range(0; $cv | length) as $i | $cv[$i] as $x
     | select(any($cv[0:$i][]; .field == $x.field and .value == $x.value) | not)
     | ([$cv[] | select(.field == $x.field) | .value] | unique | length) as $nv
     | "      " + ("full" | pad(9)) + ($x.field | fname)
       + (if $nv > 1 then " (" + ($x.source | sub("[*]$"; "")) + ")" else "" end) + ": " + $x.value
   else empty end),
  (if $apb then "", apblock($v) else empty end),
  "",
  "      " + ("Result" | pad(9)) + "out/" + $id + "/record/    ·    look at it: make view ID=" + $id,
  ("marks" + ([ (if ($r | length) > 0 then "table" else empty end),
                (if any($r[]; .status == "below") then "below" else empty end),
                (if any($r[]; .status == "weak") then "weak" else empty end),
                (if any($r[]; .status == "–") then "addr" else empty end),
                (if any($r[]; .few == true) then "few" else empty end),
                (if $apb and ([apblock($v)] | any(.[]; test("[(]head [0-9]"))) then "head" else empty end),
                (if any($r[]; ((.source // "") | endswith("*")))
                    or ($apb and ([apblock($v)] | any(.[]; endswith(" *")))) then "near" else empty end),
                (if any($r[]; .text == null and (.value | length) > 27) then "cut" else empty end) ]
               | map(" " + .) | join("")))
'

# Prints the head line of one input: print_head <i> <N> <source> <right part>.
print_head() {
  jqt -nr --arg left "[$1/$2]" --arg src "$3" --arg right "$4" "$LIB_JQ$HEAD_JQ" 2>/dev/null \
    || say "[$1/$2] $(clean "$3")   $4"
}

# Prints the line "✗ failed: <text>" of one input.
fail_line() {
  jqt -nr --arg t "$1" "$LIB_JQ$FAIL_JQ" 2>/dev/null || say "      ✗ failed: $(clean "$1")"
}

# Prints a grey information line of one input.
info_line() { say "      $(paint 90 "$1")"; }

# Adds one line to the list "Not valid or failed" of the end: add_trouble <i> <N> <source> <text>.
add_trouble() { TROUBLE="$TROUBLE[$1/$2]$TAB$(cell "$3")$TAB$(cell "$4")$NL"; }

# The output of BLOCK_JQ for one ID: block_out <ID> <state> <seconds> <convert.json or /dev/null>.
block_out() {
  jqt -r --slurpfile c "$4" --arg state "$2" --arg wall "$3" \
    --arg when "$(info_value "$OUT/$1/source.txt" converted)" --arg rid "$(info_value "$OUT/$1/source.txt" record_id)" \
    --arg id "$1" --argjson verbose "$VJ" --arg here "$HERE_NAME" "$LIB_JQ$BLOCK_JQ" "$OUT/$1/record/view.json" 2>/dev/null
}

# Prints the block of the stored record of one ID (status line, table, Apertus lines, result line), from
# out/<ID>/record/view.json and convert.json: print_block <ID> <new, again or stored> <seconds of the worker>.
# If convert.json is absent or cannot be read, the block has no times and no lines of the Apertus step.
print_block() {
  bc=$OUT/$1/record/convert.json
  [ -f "$bc" ] || bc=/dev/null
  bout=$(block_out "$1" "$2" "$3" "$bc") || bout=
  if [ -z "$bout" ] && [ "$bc" != /dev/null ]; then bout=$(block_out "$1" "$2" "$3" /dev/null) || bout=; fi
  case $bout in
    *"$NL"marks*) ;;
    *) say "      (the values cannot be read from out/$1/record/view.json)"; return 0 ;;
  esac
  bmarks=${bout##*"$NL"}
  printf '%s\n' "${bout%"$NL"*}"
  MARKS="$MARKS ${bmarks#marks}"
  case "$bmarks " in *" table "*) N_TABLES=$((N_TABLES + 1)) ;; esac
}

# 0 if a printed block used the mark $1.
has_mark() {
  case " $MARKS " in *" $1 "*) return 0 ;; esac
  return 1
}

# The explanation of the marks, after the last line (only if a table was printed).
print_footer() {
  [ "$N_TABLES" -gt 0 ] || return 0
  say "Prob. = share of correct values of this kind on the development documents. Each value can be wrong."
  if has_mark below; then
    say "below = an Apertus suggestion below the entry limit: in the values file, not in the eCH-0295 record."
  fi
  if has_mark weak; then say "weak = a rule value below 0.50: label file only, not in the eCH-0295 record."; fi
  if has_mark addr; then
    say "addressed body = the body that a proposal addresses: label file only, not in the eCH-0295 record."
  fi
  if has_mark few; then
    say "n = the number of development documents of a suggestion; below 30 the number is not stable."
  fi
  if has_mark head; then
    say "head = the probability that the Apertus head gives for this PDF. It is not the Prob. of a value."
  fi
  if has_mark near; then
    say "* = near a threshold of the Apertus head, or a second block or class is near the first."
    say "    Another computer can give another decision."
  fi
  if has_mark cut; then
    say "… = the value is longer than the column: the record has the full value (VERBOSE=1 shows it)."
  fi
  return 0
}

# The first line of 'make convert': the number of inputs and the way of the read-out (after apertus_mode).
run_head() {
  np="$1 PDF"
  [ "$1" = 1 ] || np="${np}s"
  if [ "$AP" = local ] && [ "$AP_BACKEND" = remote ]; then
    rh=$(clean "${AP_REMOTE_HOST:-?}")
    rb=$(backend_name "${AP_REMOTE_BACKEND:-?}")
    # 127.0.0.1 can be a service on this computer or the end of an ssh tunnel to another computer.
    case $rh in
      127.0.0.1|localhost|::1|'[::1]')
        say "ParlPDFeCH · $np · code rules + Apertus-v1.5-8B (Apertus service at $rh, $rb)"
        say "The text of each PDF goes to that service for the read-out."
        say "With an ssh tunnel, the text goes to the computer at the other end of the tunnel." ;;
      *)
        say "ParlPDFeCH · $np · code rules + Apertus-v1.5-8B (GPU of $rh, $rb)"
        say "The text of each PDF goes to that computer for the read-out." ;;
    esac
    say "The heads and the record stay on this computer."
  elif [ "$AP" = local ]; then
    say "ParlPDFeCH · $np · code rules + Apertus-v1.5-8B ($(backend_name "$AP_BACKEND"), $HERE_NAME)"
  else
    say "ParlPDFeCH · $np · code rules only (no Apertus)"
  fi
  # The table needs 100 columns. stty reads the size of the terminal (only on a terminal; no guess).
  if [ "$ERASE" = 1 ]; then
    tc=$(stty size 2>/dev/null < /dev/tty | awk '{ print $2 }')
    case $tc in ''|*[!0-9]*) tc=0 ;; esac
    if [ "$tc" -gt 0 ] && [ "$tc" -lt 100 ]; then
      say "$(paint 90 "This terminal has $tc columns. The table needs 100: make the window wider.")"
    fi
  fi
}

# The name of a backend of the read-out: backend_name <mlx, cuda, mps, cpu or another word>.
backend_name() {
  case $1 in
    mlx) printf 'MLX' ;; cuda) printf 'CUDA' ;; mps) printf 'torch MPS' ;; cpu) printf 'CPU' ;;
    *) printf '%s' "$(clean "$1")" ;;
  esac
}

# The last lines of 'make convert': the counts, the list "Not valid or failed" (more than one input), the marks.
print_end() {
  pl=PDFs
  [ "$total" = 1 ] && pl=PDF
  el="Done: $total $pl · $n_valid valid · $n_not_valid not valid · $n_failed failed"
  [ "$n_stored" -gt 0 ] && el="$el · $n_stored shown again"
  say ""
  jqt -nr --arg l "$el" --arg r "All IDs: make list" "$LIB_JQ"'$l + sp([84 - ($l | length) - ($r | length), 2] | max) + $r' \
    2>/dev/null || say "$el   All IDs: make list"
  if [ "$total" -gt 1 ] && [ $((n_not_valid + n_failed)) -gt 0 ]; then
    say "Not valid or failed:"
    printf '%s' "$TROUBLE" | jqt -Rrs "$LIB_JQ$TROUBLE_JQ" 2>/dev/null || printf '%s' "$TROUBLE" | tr '\t' ' '
  fi
  print_footer
}

# 'convert.sh show --id <ID>': the block of a stored result, as 'make convert' shows it (only jq; no lock, no
# worker, no change of a file).
show_cmd() {
  need jq "Install jq (macOS: brew install jq; Debian or Ubuntu: sudo apt install jq)."
  pair=$(view_record_id "$ARG_ID") || exit 1
  sid=${pair%% *}
  ssrc=$(info_value "$OUT/$sid/source.txt" source)
  print_head 1 1 "$ssrc" "ID $sid · stored result"
  if [ "$VERBOSE" = 1 ]; then
    say "      source   $(clean "$ssrc")"
    say "      sha256   $(clean "$(info_value "$OUT/$sid/source.txt" sha256)")"
  fi
  print_block "$sid" stored ""
  if [ "$N_TABLES" -gt 0 ]; then
    say ""
    print_footer
  fi
  exit 0
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
  AP_AUTO_OFF=1
}

# Sets AP (local or none) and AP_BACKEND. The check runs app/worker/apertus_states.py check (no model load): the
# backend (a GPU), the model fingerprint and the free memory. AP_AUTO_OFF is 1 if APERTUS=auto and the step cannot
# run now (then a stored Apertus result stays and is shown again).
apertus_mode() {
  AP=none
  AP_BACKEND=
  AP_REMOTE_HOST=
  AP_REMOTE_BACKEND=
  AP_AUTO_OFF=0
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
    AP_AUTO_OFF=1
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
  run_head "$total"
  n_valid=0; n_not_valid=0; n_stored=0; n_failed=0; i=0
  while IFS= read -r src; do
    i=$((i + 1))
    say ""
    WORK_OPEN=1
    JOB=$OUT/.jobs/job.$$
    NEW_DEST=
    rm -rf "$JOB"
    mkdir -p "$JOB"
    if ! get_input "$src" "$JOB/input.pdf"; then
      print_head "$i" "$total" "$src" "no ID"
      fail_line "$GET_WHY."
      add_trouble "$i" "$total" "$src" "failed: $GET_WHY"
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
        print_head "$i" "$total" "$src" "no ID"
        fail_line "the folder out/$id/ cannot be made."
        add_trouble "$i" "$total" "$src" "failed: the folder out/$id/ cannot be made"
        n_failed=$((n_failed + 1))
        rm -rf "$JOB"; JOB=; WORK_OPEN=0
        continue
      fi
      NEW_DEST=$OUT/$id
    fi
    dest=$OUT/$id
    # The record id that the server expects (app/server/src/jobs.rs, POST /api/jobs, mode rules).
    doc=$(jq -r --arg s "$sha" 'first(.samples[] | select(.pdf_sha256 == $s) | .doc_id | tostring) // ""' \
      "$APP/data/samples/index.json" 2>/dev/null)
    if [ -n "$doc" ]; then want=s-$doc-rules; else want=u-$(printf '%s' "$sha" | cut -c1-16)-rules; fi
    # The mode auto (Apertus step) has the record ids with no suffix -rules (app/server/src/jobs.rs).
    if [ "$AP" = local ]; then want=${want%-rules}; fi
    # A stored result of the other Apertus state (made with Apertus, asked without it, or the other way; or a
    # record id of the other worker mode) is converted again (same ID; the record is replaced). Not so with
    # APERTUS=auto when the Apertus step cannot run now (AP_AUTO_OFF): a stored Apertus result stays.
    stored_ap=none
    if [ -f "$dest/record/convert.json" ]; then
      stored_ap=$(jq -r '.apertus_values.state // "none" | tostring' "$dest/record/convert.json" 2>/dev/null || echo none)
    fi
    case $stored_ap in local|remote|stored) stored_ap=local ;; *) stored_ap=none ;; esac
    stored_rid=$(info_value "$dest/source.txt" record_id)
    again=$ARG_AGAIN
    changed=
    if [ -f "$dest/record/view.json" ] && [ "$again" != 1 ] && { [ "$stored_ap" != "$AP" ] || [ "$stored_rid" != "$want" ]; }; then
      if [ "$AP" = none ] && [ "$AP_AUTO_OFF" = 1 ] && [ "$stored_ap" = local ]; then
        changed="Apertus is off now (see the NOTE): the stored Apertus result stays. AGAIN=1: code rules only."
      elif [ "$AP" = local ]; then
        changed="the stored result was made without Apertus: it is converted again with Apertus"
        again=1
      else
        changed="the stored result was made with the Apertus step: it is converted again with code rules only"
        again=1
      fi
    fi
    # The right part of the head line: a new ID, a stored result shown again, or a conversion of a known PDF again.
    show_stored=0
    rsha=
    if [ -n "$NEW_DEST" ]; then
      right="ID $id · new"; bstate=new
    elif [ -f "$dest/record/view.json" ] && [ "$again" != 1 ]; then
      show_stored=1
      # The stored record must be the record of this PDF: the SHA-256 in its convert.json is the SHA-256 of this PDF.
      rsha=$(jq -r '.pdf_sha256 // "" | tostring' "$dest/record/convert.json" 2>/dev/null)
      if [ "$rsha" = "$sha" ]; then right="ID $id · stored result"; else right="ID $id"; fi
    else
      right="ID $id · converted again"; bstate=again
    fi
    print_head "$i" "$total" "$src" "$right"
    if [ -n "$changed" ]; then info_line "$changed"; fi
    if [ "$VERBOSE" = 1 ]; then
      say "      source   $(clean "$src")"
      say "      sha256   $sha"
    fi
    if [ "$show_stored" = 1 ]; then
      rm -rf "$JOB"; JOB=; WORK_OPEN=0
      if [ "$rsha" = "$sha" ]; then
        print_block "$id" stored ""
        n_stored=$((n_stored + 1))
        # A stored result counts as valid or not valid, as its status line says (view.json run.valid).
        if [ "$(jq -r '.run.valid == true' "$dest/record/view.json" 2>/dev/null)" = true ]; then n_valid=$((n_valid + 1))
        else
          n_not_valid=$((n_not_valid + 1))
          add_trouble "$i" "$total" "$src" "ID $id · not valid"
        fi
      else
        fail_line "out/$id/record/ holds the record of another PDF (another SHA-256). AGAIN=1 replaces it."
        add_trouble "$i" "$total" "$src" "failed: out/$id/record/ holds the record of another PDF"
        n_failed=$((n_failed + 1))
      fi
      continue
    fi
    # The line of the conversion, with its start time: on a terminal it goes away after the worker (a carriage
    # return, 40 spaces, and a carriage return again: no escape sequence, also with NO_COLOR); else it stays (for
    # example in a log file).
    if [ "$ERASE" = 1 ]; then printf '      converting … (start %s)' "$(date '+%H:%M:%S')"
    else say "      converting (start $(date '+%H:%M:%S')) ..."; fi
    started=$(date +%s)
    run_worker "$JOB"
    seconds=$(( $(date +%s) - started ))
    if [ "$ERASE" = 1 ]; then printf '\r%40s\r' ''; fi
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
      print_block "$id" "$bstate" "$seconds"
      if [ "$LVALID" = yes ]; then n_valid=$((n_valid + 1))
      else
        n_not_valid=$((n_not_valid + 1))
        add_trouble "$i" "$total" "$src" "ID $id · not valid"
      fi
    else
      fail_line "$(reason_text "$word")$(clean "${WHY#"$word"}"). Log: out/$id/worker.log"
      if [ -f "$dest/record/view.json" ]; then info_line "The stored result of ID $id stays (out/$id/record/)."; fi
      add_trouble "$i" "$total" "$src" "failed: $(reason_text "$word")"
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
  print_end
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
  show)
    if [ -z "$ARG_ID" ]; then err "give the ID, for example 'convert.sh show --id 0001'. 'make list' shows the IDs."; exit 1; fi
    show_cmd ;;
  view-check)
    if [ -z "$ARG_ID" ]; then err "give the ID, for example 'make view ID=0001'. 'make list' shows the IDs."; exit 1; fi
    view_record_id "$ARG_ID" > /dev/null ;;
  view)
    if [ -z "$ARG_ID" ]; then err "give the ID, for example 'make view ID=0001'. 'make list' shows the IDs."; exit 1; fi
    view_cmd ;;
  *) err "usage: convert.sh convert|list|show|view-check|view [options]"; exit 2 ;;
esac

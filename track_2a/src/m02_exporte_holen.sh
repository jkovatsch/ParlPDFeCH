#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Downloads all OpenParlData exports (without votes) from files.openparldata.ch, in parallel, and
# records the retrieval time in UTC. Data: "Source: OpenParlData.ch" (CC BY 4.0).
# Target: $PARLPDFECH_DATA/roh/exports; without PARLPDFECH_DATA: track_2a/data/roh/exports.
# Only file names with the characters A-Z a-z 0-9 . _ / - are downloaded. The retrieval time
# (abgerufen_utc.txt) is written only when all files are downloaded without an error.
# Usage: bash src/m02_exporte_holen.sh
set -u
case "${1:-}" in
  -h|--help) sed -n '3,8p' "$0" | sed 's/^# //'; exit 0 ;;
esac
DATEN="${PARLPDFECH_DATA:-$(cd "$(dirname "$0")/.." && pwd)/data}"
DATEN="${DATEN/#\~/$HOME}"
mkdir -p "$DATEN/roh/exports/texts" "$DATEN/roh/exports/docs"
cd "$DATEN/roh/exports" || exit 1
BASIS=https://files.openparldata.ch/exports
liste() { curl -sS -m 60 "$BASIS/$1" | grep -o 'href="[^"/]*\.\(gz\|json\)"' | sed 's/href="//;s/"$//'; }
{
  liste "" | grep -v '^votes\.ndjson\.gz$' | sed 's#^#./#'
  liste "texts/" | sed 's#^#texts/#'
  liste "docs/" | sed 's#^#docs/#'
} | grep -E '^[A-Za-z0-9._/-]+$' > dateiliste.txt
# The file name is an argument of sh, not a part of the command text.
xargs -P 6 -I{} sh -c 'curl -sS -f -m 1800 --retry 3 -o "$1" "$2/$1" && echo "ok $1" || echo "FEHLER $1"' sh {} "$BASIS" \
  < dateiliste.txt > download.log 2>&1
ok=$(grep -c '^ok' download.log)
fehler=$(grep -c '^FEHLER' download.log)
echo "fertig: $ok ok, $fehler Fehler"
if [ "$ok" -eq 0 ] || [ "$fehler" -ne 0 ]; then
  echo "abgerufen_utc.txt not written: no file or not all files downloaded" >&2
  exit 1
fi
date -u +%Y-%m-%dT%H:%M:%SZ > abgerufen_utc.txt

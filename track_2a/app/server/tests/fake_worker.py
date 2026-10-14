#!/usr/bin/env python3
"""Fake worker for the tests of the server.

It follows the worker protocol of CONTRACT.md chapter 4 (arguments, JSON lines on standard
output, exit codes). It converts nothing. The files that it writes hold fixed test text.

Extra arguments, put before the arguments of the server:
  --case auto|valid|not_valid|refused|stopped|crash|hang|hang_hard|garbage|wrong_id|no_view|extra_file
              (hang_hard ignores the signal TERM)
  --delay SECONDS   wait after each stage
"""
import argparse
import hashlib
import json
import os
import signal
import sys
import time

STAGES = ["read_pdf", "lines", "rules", "apertus", "write", "check"]
DOC_SUFFIXES = [
    ".gesamt.trig", ".ech.ttl", ".gesamt.rdf.xml", ".ech.rdf.xml",
    ".ech.yaml", ".labels.yaml", ".provenance.yaml",
]
FIXED = ["manifest.json", "validation.json", "view.json", "convert.json"]


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", default="auto")
    p.add_argument("--delay", type=float, default=0.0)
    p.add_argument("--sample")
    p.add_argument("--pdf")
    p.add_argument("--doc-id")
    p.add_argument("--mode", default="auto")
    p.add_argument("--out", required=True)
    p.add_argument("--data-dir")
    a = p.parse_args()

    index = []
    if a.data_dir:
        path = os.path.join(a.data_dir, "samples", "index.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                index = json.load(f)["samples"]

    sha = None
    doc = a.sample
    in_index = False
    if a.pdf:
        with open(a.pdf, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        for s in index:
            if s.get("pdf_sha256") == sha:
                doc, in_index = str(s["doc_id"]), True
    else:
        for s in index:
            if str(s.get("doc_id")) == a.sample:
                sha, in_index = s.get("pdf_sha256"), True

    case = a.case
    if case == "auto":
        case = "valid" if in_index else "refused"

    if case == "crash":
        emit({"event": "stage", "id": "read_pdf", "state": "running"})
        raise RuntimeError("fake crash with a trace on standard error: /fake/path/of/the/worker.py")

    if case in ("hang", "hang_hard"):
        if case == "hang_hard":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        emit({"event": "stage", "id": "read_pdf", "state": "running"})
        emit({"event": "stage", "id": "read_pdf", "state": "done", "origin": "stored", "seconds": 0.001,
              "counts": {"pages": 1, "pid": os.getpid()}})
        emit({"event": "stage", "id": "lines", "state": "running"})
        time.sleep(3600)
        return 1

    if case == "refused":
        emit({"event": "stage", "id": "read_pdf", "state": "running"})
        emit({"event": "stage", "id": "read_pdf", "state": "failed", "seconds": 0.012, "reason": "not_in_package"})
        emit({"event": "failed", "code": "not_in_package",
              "detail": {"pdf_sha256": sha or "0" * 64, "profile": os.environ.get("PARLPDFECH_PROFILE", "")}})
        return 3

    if case == "stopped":
        emit({"event": "stage", "id": "read_pdf", "state": "running"})
        emit({"event": "failed", "code": "converter_stopped",
              "detail": {"note": "writer", "trace": "File \"/fake/path/x.py\", line 1"}})
        return 4

    garbage = case == "garbage"
    if garbage:
        sys.stdout.write("this line is not JSON: /fake/secret/path\n")
        sys.stdout.buffer.write(b"\xff\xfe\x00 binary bytes\n")
        sys.stdout.write("[1, 2, 3]\n")
        sys.stdout.write('"a JSON string"\n')
        sys.stdout.write('{"event":"unknown_event","leak":"/fake/secret/path"}\n')
        sys.stdout.write('{"event":"stage","id":"no_such_stage","state":"running"}\n')
        sys.stdout.write('{"event":"stage","id":"read_pdf","state":"no_such_state"}\n')
        sys.stdout.write("x" * (2 * 1024 * 1024) + "\n")
        sys.stdout.write("\n")
        sys.stdout.flush()
        sys.stderr.write("fake text on standard error: /fake/secret/path\n")
        sys.stderr.flush()

    doc_name = doc if doc else "local"
    base = "s-%s" % doc if doc and in_index else "u-%s" % (sha or "0" * 64)[:16]
    record_id = base + ("-rules" if a.mode == "rules" else "")
    if case == "wrong_id":
        record_id = "s-1"
    apertus = "stored" if (a.mode == "auto" and in_index) else "none"

    seconds = {}
    for stage in STAGES:
        if stage == "apertus" and apertus == "none":
            emit({"event": "stage", "id": stage, "state": "skipped", "reason": "mode_rules"})
            seconds[stage] = 0
            continue
        emit({"event": "stage", "id": stage, "state": "running"})
        if garbage:
            sys.stdout.write("garbage between two stage lines\n")
            sys.stdout.flush()
        if a.delay:
            time.sleep(a.delay)
        counts = {"read_pdf": {"pages": 1}, "lines": {"lines": 3, "blocks": 2}, "rules": {"blocks": 2},
                  "apertus": {"labels": 2}, "write": {"labels": 4, "triples": 40},
                  "check": {"passed": 9, "total": 10, "skipped": 1}}[stage]
        origin = "new" if stage in ("write", "check") else "stored"
        seconds[stage] = 0.001
        row = {"event": "stage", "id": stage, "state": "done", "origin": origin, "seconds": 0.001, "counts": counts}
        if case == "dirty_stage" and stage == "read_pdf":
            # values that the server must not pass on: a path, a trace, a nested value, an extra key
            row.update({"reason": "Traceback: File \"/fake/secret/app.py\", line 7", "origin": {"path": "/fake/secret"},
                        "counts": {"pages": 1, "note": "/fake/secret/counts", "nested": {"a": 1}},
                        "extra_key": "/fake/secret/extra", "note": "view_absent"})
        emit(row)
        if case == "flood" and stage == "read_pdf":
            for _ in range(500):
                emit({"event": "stage", "id": "lines", "state": "running"})
    seconds["total"] = 0.006

    os.makedirs(a.out, exist_ok=True)
    names = [doc_name + s for s in DOC_SUFFIXES] + FIXED
    valid = case != "not_valid"
    for name in names:
        if case == "no_view" and name == "view.json":
            continue
        if case == "few_files" and name in ("convert.json", doc_name + ".ech.ttl"):
            continue
        if name == "view.json":
            body = json.dumps({"schema": "parlpdfech-site-view/2", "record_id": record_id, "doc_id": doc,
                               "run": {"mode": a.mode, "valid": valid}}, ensure_ascii=False, indent=1) + "\n"
        elif name.endswith(".json"):
            body = json.dumps({"fake": name, "record_id": record_id}) + "\n"
        else:
            body = "# fake test content of %s\n# umlaut: äöü\n" % name
        with open(os.path.join(a.out, name), "w", encoding="utf-8", newline="") as f:
            f.write(body)
    if case == "extra_file":
        with open(os.path.join(a.out, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("not a record file\n")

    emit({"event": "done", "record_id": record_id, "doc_id": doc, "valid": valid, "mode": a.mode,
          "apertus": apertus, "origin": "stored" if in_index else "new", "pdf_sha256": sha,
          "seconds": seconds, "counts": {"pages": 1, "lines": 3, "blocks": 2, "labels": 4}, "files": names})
    return 0 if valid else 2


if __name__ == "__main__":
    sys.exit(main())

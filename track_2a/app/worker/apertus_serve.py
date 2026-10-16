#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the Apertus read-out service for a computer with a GPU ('make serve-apertus').

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude
Opus 5.5), builder C of the Apertus build of 16.10.2026, for the main agent of session ad54858c.

Task
  The value heads (daten/gj_values/heads2/heads2.npz) read the hidden state of Apertus-v1.5-8B (text branch, bf16)
  after decoder layer 20 at the last token of each question (suffix). A normal chat service of Apertus (for
  example Public AI, Swisscom or a Hugging Face inference endpoint) gives text, not this state, so it cannot serve
  the heads. This file is a small HTTP service for a computer with a GPU: this computer, another computer, or a
  rented GPU in the cloud. It loads the model ONE time with a local backend of worker/apertus_states.py (mlx,
  cuda, mps or cpu: the same code as a local run on that computer), and for each request it
    - takes the prompt texts of one document: the prefix and the suffixes, exactly as worker/apertus_states.py
      makes them (m11_prompts_values.item) on the computer of the user. The service makes no prompt;
    - tokenizes them with the tokenizer of its model folder (the one token rule of the fixed run) and runs the
      passes of its backend (prefill of the prefix, one pass for each suffix);
    - answers with the states after layer 20 at the last token of each suffix, rounded to float16, the letter
      log-probabilities, the token counts and token SHA-256 values, the model fingerprint, the backend name and
      the library versions.
  The heads, the combined reader, the page finder, the writer and the validator stay on the computer of the user.
  The client is worker/apertus_backend_remote.py (backend 'remote' of apertus_states.py; APERTUS_URL).

Protocol 1 (JSON over HTTP/1.0; one request for each connection)
  GET  /v1/health    the facts of the service: service, protocol, backend, device, dtype, model_fingerprint,
                     model, versions, loaded, busy, max_body_bytes, auth (bearer or none), read_outs.
  POST /v1/readout   body (Content-Type application/json, Content-Length required):
                       {"protocol": 1, "prefix": "<text>", "suffixes": [{"id": "Q0", "text": "<text>"}, ...],
                        "layers": [20]}
                     answer 200: {"protocol": 1, "suffix_ids": [...], "layers": [20],
                       "states": {"dtype": "float16", "byteorder": "little", "shape": [n, 1, 4096],
                                  "sha256": "<of the bytes>", "base64": "..."},
                       "letter_logprobs": {"dtype": "float32", ..., "shape": [n, 6], "base64": "..."},
                       "n_prefix_tokens", "n_suffix_tokens", "prefix_tokens_sha256", "suffix_tokens_sha256",
                       "boundary_equal_first_suffix", "timing", "peak_bytes", "peak_kind", "queue_seconds",
                       "backend", "device", "model_fingerprint", "versions", "service_version"}
                     other answers: {"error": "<code>", "message": "<text>"} with 400 bad_request, 401
                     unauthorized, 403 host_refused, 404, 411 length_required, 413 too_large, 415 not_json, 422
                     (prefix_too_long, token_problems, not_finite), 500 error, 503 busy or ending, 504 time_limit.

Security
  - The service binds 127.0.0.1 by default (this computer only). Another address only with a token in the
    environment variable APERTUS_TOKEN (32 characters or more, visible ASCII). The token is never a command line
    argument (other users of the computer could read it in the process list), and this file never prints, logs
    or stores it.
  - With a token, each request (also /v1/health) needs the header 'Authorization: Bearer <token>'. The check is
    hmac.compare_digest. Without a token (127.0.0.1 only), the Host header must name this computer (127.0.0.1,
    localhost or ::1): a web page in a browser of this computer cannot use the service through another name.
  - A body limit (--max-body, default 8 MiB); a read time limit for the request (60 s for each read, and 120 s
    for the whole request line, headers and body: a slow sender is cut off); at most 8 open connections (more are
    closed at once); one
    read-out at a time (a second one gets 503 busy at once, no queue); a time limit for each read-out
    (--request-timeout, default 1500 s: the answer is then 504 time_limit; the GPU work of that request ends by
    itself, and the service stays busy until then).
  - The log (standard error, or --log FILE) has one JSON line for each request: time, client address, method,
    path, status, error code, counts, seconds, bytes. It has no document text, no token and no header.
  - The service speaks plain HTTP. Outside this computer use an ssh tunnel (docs/apertus-gpu.md): the text of
    the PDF and the token then go through ssh. The client refuses plain http to another computer unless
    APERTUS_ALLOW_HTTP=1 (for a private network such as WireGuard).
  - The text of each PDF goes to the computer of this service. The user chooses that computer.

Self-end (tests never need to stop the process): --max-requests N ends the service after N read-out requests
(POST /v1/readout that passed the host and token checks, any status). --idle-exit S ends it after S seconds with
no request. Ctrl-C or SIGTERM end it too.

Command (python -I: the file puts its own folder and ROOT/src at the start of the module search path)
  [APERTUS_TOKEN=...] python -I -B apertus_serve.py --root ROOT --model-dir D [--backend auto|mlx|cuda|mps|cpu]
      [--host 127.0.0.1] [--port 8090] [--max-requests N] [--idle-exit S] [--request-timeout S]
      [--max-body BYTES] [--log FILE]
  ROOT is a folder with the converter files below src/ (app/layout/ of the public tree). --port 0 takes a free
  port; the line 'apertus-serve: ready on http://HOST:PORT' names it. The choice 'auto' takes mlx, cuda or mps
  (never the CPU; --backend cpu only for checks, very slow).

Exit codes: 0 end (max_requests, idle_exit, signal); 1 error; 2 refused before the start (address, token,
options); 4 model_absent or fingerprint_differs; 5 no_gpu or backend_absent; 6 memory_too_small or memory_low.
APERTUS_TOKEN is stripped of white space at both ends (for example the line end of a token file).

Tested: only on one Mac (Apple M4, 32 GB, macOS), 16.10.2026: service and client on this one computer
(127.0.0.1), backend mlx, and the HTTP code with a test backend that loads no model. NOT tested: CUDA, Linux,
Windows, a second computer, an ssh tunnel, IPv6.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import queue
import re
import signal
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import apertus_states as api  # noqa: E402  (the backends of a local run; worker folder)

VERSION = "m12-apertus-serve-1"
SERVICE = "parlpdfech-apertus-readout"
PROTOCOL = 1
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090
MIN_TOKEN_CHARS = 32
DEFAULT_MAX_BODY = 8 * 1024 * 1024        # a document of 25 pages has a prefix of about 0.1 MB
DEFAULT_REQUEST_TIMEOUT = 1500.0          # below the time limit of the worker (APERTUS_TIMEOUT - 120 = 1680 s)
READ_TIMEOUT = 60.0                       # seconds for each read of the request (headers and body)
REQUEST_READ_DEADLINE = 120.0             # seconds for the whole request line, the headers and the body
MAX_CONNECTIONS = 8                       # open connections at a time; more are closed at once
SEND_TIMEOUT = 600.0                      # seconds to send one answer
# The frozen engine and token rule of the fixed run (src/m10_vm_states.py, SHA-256 of 13.10.2026). The service
# reads out only with this file.
ENGINE_REL = "src/m10_vm_states.py"
ENGINE_SHA256 = "3cd1eb9f1b66034e8c8289ca292adb6663d8a6794a3c6d165656ff3ab5e8c53b"
MAX_SUFFIXES = 4096
RX_SUFFIX = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")      # the rule of m10_vm_states.RX_SUFFIX
INPUT_REASONS = ("prefix_too_long", "token_problems", "not_finite", "block_file_bad")
REQUEST_KEYS = {"protocol", "prefix", "suffixes", "layers"}
TESTED_ON = ("only one Mac (Apple M4, 32 GB, macOS), 16.10.2026: service and client on one computer, backend mlx; "
             "CUDA, Linux, Windows and a second computer not tested")
EXIT = {"refused": 2}


class StartRefused(Exception):
    """A stop before the start (exit 2): address, token or options."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def say(msg: str) -> None:
    """A line for the person who started the service (standard output; no document text, no token)."""
    print(f"apertus-serve: {msg}", flush=True)


def is_loopback(host: str) -> bool:
    h = str(host or "").strip().strip("[]").lower()
    if h == "localhost":
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def url_host(host: str) -> str:
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def start_rule(host: str, token: str | None) -> None:
    """The rule of the address and the token (before anything else; no model is read)."""
    if token is not None:
        if len(token) < MIN_TOKEN_CHARS:
            raise StartRefused("token_short", f"APERTUS_TOKEN has fewer than {MIN_TOKEN_CHARS} characters. Make a "
                                              "long random token, for example: python3 -c \"import secrets; "
                                              "print(secrets.token_hex(32))\"")
        if any(not (33 <= ord(c) < 127) for c in token):
            raise StartRefused("token_form", "APERTUS_TOKEN must have visible ASCII characters only (no space)")
    if not is_loopback(host) and token is None:
        raise StartRefused("token_needed", f"HOST={host} is not this computer only (127.0.0.1). The service answers "
                                           f"another address only with a token: set APERTUS_TOKEN (32 characters or "
                                           f"more). Or keep 127.0.0.1 and use an ssh tunnel (docs/apertus-gpu.md).")


# ---------------------------------------------------------------------------------------------- requests

class BadRequest(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def parse_readout(body: bytes, layers_ok: tuple[int, ...]) -> tuple[dict, tuple[int, ...]]:
    """The prompt item of the request (the form of m11_prompts_values.item: doc_id, prefix, suffixes) and the
    asked layers. The service never keeps the texts after the answer."""
    try:
        x = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise BadRequest(400, "bad_request", "the body is not JSON in UTF-8") from e
    if not isinstance(x, dict):
        raise BadRequest(400, "bad_request", "the body is not a JSON object")
    extra = sorted(set(x) - REQUEST_KEYS)
    if extra:
        raise BadRequest(400, "bad_request", f"unknown keys: {', '.join(extra)[:120]}")
    if x.get("protocol") != PROTOCOL:
        raise BadRequest(400, "protocol", f"protocol {x.get('protocol')!r}: this service speaks protocol {PROTOCOL}")
    pre, sufs = x.get("prefix"), x.get("suffixes")
    if not isinstance(pre, str) or not pre:
        raise BadRequest(400, "bad_request", "prefix: a text is needed")
    if not isinstance(sufs, list) or not 1 <= len(sufs) <= MAX_SUFFIXES:
        raise BadRequest(400, "bad_request", f"suffixes: a list of 1 to {MAX_SUFFIXES} entries is needed")
    seen, out = set(), []
    for s in sufs:
        if not isinstance(s, dict) or set(s) != {"id", "text"}:
            raise BadRequest(400, "bad_request", "each suffix is an object with the keys id and text")
        sid, txt = s["id"], s["text"]
        if not isinstance(sid, str) or not RX_SUFFIX.match(sid) or sid in seen:
            raise BadRequest(400, "bad_request", "a suffix id is not of the form [A-Za-z0-9_.-]{1,40} or not unique")
        if not isinstance(txt, str) or not txt:
            raise BadRequest(400, "bad_request", "a suffix has no text")
        seen.add(sid)
        out.append({"id": sid, "text": txt})
    lay = x.get("layers", [20])
    if (not isinstance(lay, list) or not lay or any(type(k) is not int for k in lay)
            or any(k not in layers_ok for k in lay) or len(set(lay)) != len(lay)):
        raise BadRequest(400, "bad_request", f"layers: a list of distinct layers of {list(layers_ok)}")
    # doc_id: the backends use it only in messages; the service gets no document id
    return {"doc_id": "request", "prefix": pre, "suffixes": out}, tuple(lay)


def b64_array(a, dtype: str) -> dict:
    import numpy as np  # noqa: PLC0415
    b = np.ascontiguousarray(a, dtype=np.dtype(dtype).newbyteorder("<")).tobytes()
    return {"dtype": np.dtype(dtype).name, "byteorder": "little", "shape": list(a.shape),
            "sha256": hashlib.sha256(b).hexdigest(), "base64": base64.b64encode(b).decode("ascii")}


def encode_answer(r: dict, desc: dict, queue_seconds: float) -> dict:
    lets = r.get("letter_logprobs")
    return {"protocol": PROTOCOL, "service": SERVICE, "service_version": VERSION,
            "backend": desc.get("backend"), "device": desc.get("device"), "dtype": desc.get("dtype"),
            "model_fingerprint": desc.get("model_fingerprint"), "versions": desc.get("versions"),
            "suffix_ids": list(r["suffix_ids"]), "layers": [int(k) for k in r["layers"]],
            "states": b64_array(r["states"], "float16"),
            "letter_logprobs": None if lets is None else b64_array(lets, "float32"),
            "n_prefix_tokens": int(r["n_prefix_tokens"]), "n_suffix_tokens": [int(n) for n in r["n_suffix_tokens"]],
            "prefix_tokens_sha256": r["prefix_tokens_sha256"], "suffix_tokens_sha256": list(r["suffix_tokens_sha256"]),
            "boundary_equal_first_suffix": r.get("boundary_equal_first_suffix"), "timing": r.get("timing"),
            "peak_bytes": r.get("peak_bytes"), "peak_kind": r.get("peak_kind"),
            "queue_seconds": round(queue_seconds, 3)}


# ---------------------------------------------------------------------------------------------- the service

class Job:
    def __init__(self, item: dict, layers: tuple[int, ...]):
        self.item, self.layers = item, layers
        self.done = threading.Event()
        self.result: dict | None = None
        self.error: tuple[str, str] | None = None
        self.t_queued = time.monotonic()
        self.t_start: float | None = None


class Service:
    """The state of the service. The model work runs in loop(), in the thread that loaded the model (MLX and torch
    MPS keep their streams in that thread); the HTTP threads only check, parse, wait and encode."""

    def __init__(self, backend, desc: dict, token: str | None, max_body: int = DEFAULT_MAX_BODY,
                 request_timeout: float = DEFAULT_REQUEST_TIMEOUT, max_requests: int | None = None,
                 idle_exit: float | None = None, log_stream=None, load_facts: dict | None = None):
        self.backend, self.desc = backend, dict(desc)
        self._token = None if token is None else token.encode("ascii")
        self.max_body, self.request_timeout = int(max_body), float(request_timeout)
        self.max_requests = int(max_requests) if max_requests else None
        self.idle_exit = float(idle_exit) if idle_exit else None
        self.log_stream = log_stream if log_stream is not None else sys.stderr
        self.load_facts = dict(load_facts or {})
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.jobs: queue.Queue[Job] = queue.Queue()
        self.busy = False
        self.in_flight = 0
        self.read_outs = 0                  # POST /v1/readout after the host and token checks (any status)
        self.last_activity = time.monotonic()
        self.ending: str | None = None
        self.stop = threading.Event()
        try:
            self.layers_ok = tuple(int(k) for k in backend.vm.DEFAULT_LAYERS)
        except AttributeError:
            self.layers_ok = (8, 12, 16, 20, 24, 28, 32)

    @property
    def auth(self) -> str:
        return "bearer" if self._token is not None else "none"

    def token_ok(self, header: str | None) -> bool:
        if self._token is None:
            return True
        if not header or not header.startswith("Bearer "):
            return False
        return hmac.compare_digest(header[7:].strip().encode("latin-1", "replace"), self._token)

    def log(self, **kv) -> None:
        line = json.dumps({"time": now(), **kv}, ensure_ascii=True, separators=(",", ":"))
        with self.log_lock:
            try:
                self.log_stream.write(line + "\n")
                self.log_stream.flush()
            except (OSError, ValueError):
                pass

    def health(self) -> dict:
        d = self.desc
        with self.lock:
            busy, n = self.busy, self.read_outs
        return {"protocol": PROTOCOL, "service": SERVICE, "service_version": VERSION, "backend": d.get("backend"),
                "device": d.get("device"), "dtype": d.get("dtype"), "attn": d.get("attn"), "sdpa": d.get("sdpa"),
                "engine": d.get("engine"), "model": d.get("model"), "model_fingerprint": d.get("model_fingerprint"),
                "versions": d.get("versions"), "engine_code_sha256": ENGINE_SHA256, "loaded": True,
                "load_seconds": self.load_facts.get("load_seconds"),
                "busy": busy, "layers": list(self.layers_ok), "max_body_bytes": self.max_body,
                "request_timeout_seconds": self.request_timeout, "auth": self.auth, "read_outs": n,
                "max_requests": self.max_requests, "idle_exit_seconds": self.idle_exit, "tested_on": TESTED_ON}

    def enter(self) -> str | None:
        with self.lock:
            self.in_flight += 1
            self.last_activity = time.monotonic()
            return self.ending

    def leave(self, counted: bool) -> None:
        with self.lock:
            self.in_flight -= 1
            if counted:
                self.read_outs += 1
            self.last_activity = time.monotonic()

    def try_submit(self, job: Job) -> bool:
        with self.lock:
            if self.busy or self.ending:
                return False
            self.busy = True
        self.jobs.put(job)
        return True

    def end_reason(self) -> str | None:
        with self.lock:
            if self.ending:
                return self.ending
            if self.busy or self.in_flight:
                return None
            reason = None
            if self.stop.is_set():
                reason = "signal"
            elif self.max_requests and self.read_outs >= self.max_requests:
                reason = "max_requests"
            elif self.idle_exit and time.monotonic() - self.last_activity >= self.idle_exit:
                reason = "idle_exit"
            if reason:
                self.ending = reason
            return reason

    def run_job(self, job: Job) -> None:
        job.t_start = time.monotonic()
        try:
            job.result = self.backend.readout(job.item, job.layers)
        except api.Refused as e:
            job.error = (e.code, e.message)
        except Exception as e:  # noqa: BLE001  (the message goes back to the sender only, never to the log)
            job.error = ("error", f"{type(e).__name__}: {str(e)[:200]}")
        except BaseException:
            job.error = ("ending", "the service was stopped during the read-out")
            raise
        finally:
            job.item = None                 # the texts are not kept after the read-out
            with self.lock:
                self.busy = False
                self.last_activity = time.monotonic()
            job.done.set()

    def loop(self, poll: float = 0.25) -> str:
        """Runs the read-outs one after the other until an end reason holds. Returns the reason."""
        while True:
            try:
                job = self.jobs.get(timeout=poll)
            except queue.Empty:
                reason = self.end_reason()
                if reason:
                    self.drain()
                    return reason
                continue
            self.run_job(job)

    def drain(self) -> None:
        while True:
            try:
                job = self.jobs.get_nowait()
            except queue.Empty:
                return
            job.error = ("ending", "the service ends")
            with self.lock:
                self.busy = False
            job.done.set()


class Handler(BaseHTTPRequestHandler):
    server_version = "parlpdfech-apertus-readout/1"
    sys_version = ""
    protocol_version = "HTTP/1.0"
    timeout = READ_TIMEOUT
    read_deadline = REQUEST_READ_DEADLINE

    def setup(self):
        super().setup()
        # the whole request (request line, headers, body) must arrive within read_deadline seconds: else the
        # connection is shut down (the read then ends), so that a slow sender cannot hold a thread
        self._read_timer = threading.Timer(self.read_deadline, self._cut)
        self._read_timer.daemon = True
        self._read_timer.start()

    def _cut(self) -> None:
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def _read_done(self) -> None:
        t = getattr(self, "_read_timer", None)
        if t is not None:
            t.cancel()

    def finish(self):
        self._read_done()
        super().finish()

    def log_message(self, format, *args):  # noqa: A002  (the service writes its own log lines; no request text)
        return

    def log_error(self, format, *args):  # noqa: A002
        return

    @property
    def svc(self) -> Service:
        return self.server.service  # type: ignore[attr-defined]

    def _send(self, status: int, obj: dict, headers: dict | None = None) -> int:
        body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        try:
            self.connection.settimeout(SEND_TIMEOUT)      # an answer of some MB through a slow tunnel
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        except OSError:                 # a closed connection or a send time limit
            return 0
        return len(body)

    def _err(self, status: int, code: str, message: str, headers: dict | None = None) -> tuple[int, str, int]:
        return status, code, self._send(status, {"error": code, "message": message}, headers)

    def _host_ok(self) -> bool:
        """Without a token: the Host header must name this computer (no use through another name)."""
        if self.svc.auth == "bearer":
            return True
        h = (self.headers.get("Host") or "").strip()
        if h.startswith("["):
            name = h[1:].split("]", 1)[0]
        else:
            name = h.rsplit(":", 1)[0] if h.count(":") == 1 else h
        return is_loopback(name)

    def _path(self) -> str:
        return self.path.split("?", 1)[0]

    def do_GET(self):  # noqa: N802
        self._read_done()                    # a GET has no body: the request is read
        t0 = time.monotonic()
        ending = self.svc.enter()
        status, code, nout = 500, "error", 0
        try:
            if not self._host_ok():
                status, code, nout = self._err(403, "host_refused", "the Host header does not name this computer")
            elif not self.svc.token_ok(self.headers.get("Authorization")):
                status, code, nout = self._err(401, "unauthorized", "a valid bearer token is needed",
                                               {"WWW-Authenticate": 'Bearer realm="apertus-readout"'})
            elif self._path() == "/v1/health":
                h = self.svc.health()
                if ending:
                    h["ending"] = ending
                status, code, nout = 200, None, self._send(200, h)
            else:
                status, code, nout = self._err(404, "not_found", "GET /v1/health or POST /v1/readout")
        finally:
            self.svc.leave(False)
            self.svc.log(event="request", client=self.client_address[0], method="GET", path=self._path()[:40],
                         status=status, error=code, seconds=round(time.monotonic() - t0, 3), bytes_out=nout)

    def do_POST(self):  # noqa: N802
        t0 = time.monotonic()
        ending = self.svc.enter()
        status, code, nout, nin, counted = 500, "error", 0, 0, False
        facts: dict = {}
        try:
            if not self._host_ok():
                status, code, nout = self._err(403, "host_refused", "the Host header does not name this computer")
                return
            if not self.svc.token_ok(self.headers.get("Authorization")):
                status, code, nout = self._err(401, "unauthorized", "a valid bearer token is needed",
                                               {"WWW-Authenticate": 'Bearer realm="apertus-readout"'})
                return
            if self._path() != "/v1/readout":
                status, code, nout = self._err(404, "not_found", "GET /v1/health or POST /v1/readout")
                return
            counted = True
            if ending:
                status, code, nout = self._err(503, "ending", f"the service ends ({ending})")
                return
            ctype = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            if ctype != "application/json":
                status, code, nout = self._err(415, "not_json", "Content-Type must be application/json")
                return
            if self.headers.get("Transfer-Encoding"):
                status, code, nout = self._err(411, "length_required", "no Transfer-Encoding; give Content-Length")
                return
            try:
                n = int(self.headers.get("Content-Length") or "")
            except ValueError:
                status, code, nout = self._err(411, "length_required", "Content-Length is needed")
                return
            if n < 0 or n > self.svc.max_body:
                status, code, nout = self._err(413, "too_large", f"the body has {n} bytes; the limit is "
                                                                 f"{self.svc.max_body}")
                return
            body = self.rfile.read(n)
            self._read_done()                # the request is read; the wait for the read-out has its own limit
            nin = len(body)
            if nin != n:
                status, code, nout = self._err(400, "bad_request", "the body is shorter than Content-Length")
                return
            try:
                item, layers = parse_readout(body, self.svc.layers_ok)
            except BadRequest as e:
                status, code, nout = self._err(e.status, e.code, e.message)
                return
            del body
            facts["n_suffixes"] = len(item["suffixes"])
            job = Job(item, layers)
            del item
            if not self.svc.try_submit(job):
                status, code, nout = self._err(503, "busy", "the service reads out another document (one at a "
                                                            "time); try again later", {"Retry-After": "30"})
                return
            if not job.done.wait(self.svc.request_timeout):
                status, code, nout = self._err(504, "time_limit", f"the read-out took more than "
                                                                  f"{self.svc.request_timeout:.0f} s; the service "
                                                                  f"stays busy until it ends")
                return
            facts["queue_seconds"] = round((job.t_start or job.t_queued) - job.t_queued, 3)
            if job.error is not None:
                ec, em = job.error
                st = 422 if ec in INPUT_REASONS else (503 if ec == "ending" else 500)
                status, code, nout = self._err(st, ec, em)
                return
            r = job.result or {}
            facts.update(n_prefix_tokens=r.get("n_prefix_tokens"),
                         n_suffix_tokens=int(sum(r.get("n_suffix_tokens") or [])),
                         readout_seconds=(r.get("timing") or {}).get("seconds"))
            status, code = 200, None
            nout = self._send(200, encode_answer(r, self.svc.desc, facts["queue_seconds"]))
        finally:
            self.svc.leave(counted)
            self.svc.log(event="request", client=self.client_address[0], method="POST", path=self._path()[:40],
                         status=status, error=code, seconds=round(time.monotonic() - t0, 3), bytes_in=nin,
                         bytes_out=nout, **facts)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 16
    max_connections = MAX_CONNECTIONS
    service: Service

    def server_activate(self):
        super().server_activate()
        self._slots = threading.BoundedSemaphore(self.max_connections)
        self._held: set = set()
        self._held_lock = threading.Lock()

    def verify_request(self, request, client_address):
        """At most max_connections open connections: a connection over the limit is closed at once."""
        if not self._slots.acquire(blocking=False):
            return False
        with self._held_lock:
            self._held.add(request)
        return True

    def shutdown_request(self, request):
        try:
            super().shutdown_request(request)
        finally:
            with self._held_lock:
                held = request in self._held
                self._held.discard(request)
            if held:
                self._slots.release()


def make_server(host: str, port: int) -> Server:
    cls = Server
    if ":" in host.strip("[]"):
        cls = type("Server6", (Server,), {"address_family": socket.AF_INET6})
    return cls((host.strip("[]"), int(port)), Handler)


def serve(server: Server, service: Service) -> str:
    """Serves in a background thread and runs the read-outs in THIS thread until an end reason holds."""
    server.service = service
    t = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.25}, name="http", daemon=True)
    t.start()
    try:
        reason = service.loop()
    except KeyboardInterrupt:
        with service.lock:
            service.ending = "signal"
        reason = "signal"
    finally:
        server.shutdown()
        server.server_close()
    return reason


# ---------------------------------------------------------------------------------------------- start

def _term(signum, frame):  # noqa: ARG001
    raise KeyboardInterrupt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Apertus read-out service for a computer with a GPU (protocol 1)")
    ap.add_argument("--root", required=True, help="folder with the converter files below src/ (app/layout)")
    ap.add_argument("--model-dir", required=True, help="the text branch folder of 'make setup-apertus'")
    ap.add_argument("--backend", default="auto", help="auto (mlx, cuda, mps; never cpu) or mlx, cuda, mps, cpu")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--max-requests", type=int, default=0, help="end after N read-out requests (0: no limit)")
    ap.add_argument("--idle-exit", type=float, default=0, help="end after S seconds with no request (0: never)")
    ap.add_argument("--request-timeout", type=float, default=DEFAULT_REQUEST_TIMEOUT)
    ap.add_argument("--max-body", type=int, default=DEFAULT_MAX_BODY)
    ap.add_argument("--log", default=None, help="the request log (JSON lines); default: standard error")
    a = ap.parse_args(argv)
    token = (os.environ.get("APERTUS_TOKEN") or "").strip() or None     # a line end of a token file is removed
    log_stream = open(a.log, "a", encoding="utf-8") if a.log else sys.stderr  # noqa: SIM115

    def refuse(code: str, message: str, rc: int) -> int:
        say(f"not started ({code}): {message}")
        print(json.dumps({"time": now(), "event": "refused", "reason": code}), file=log_stream, flush=True)
        return rc

    try:
        start_rule(a.host, token)
        if not 0 <= a.port <= 65535 or a.max_requests < 0 or a.idle_exit < 0 or a.max_body < 1024 \
                or a.request_timeout < 10:
            raise StartRefused("options", "port 0 to 65535, max-requests and idle-exit 0 or more, max-body 1024 or "
                                          "more, request-timeout 10 s or more")
        if a.backend not in ("auto",) + api.LOCAL_BACKENDS:
            raise StartRefused("options", f"--backend {a.backend}: the service runs a local backend "
                                          f"(auto, {', '.join(api.LOCAL_BACKENDS)})")
    except StartRefused as e:
        return refuse(e.code, e.message, EXIT["refused"])
    if sys.platform == "darwin":
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "1.0"
        os.environ["PYTORCH_MPS_LOW_WATERMARK_RATIO"] = "0.9"
        os.environ.pop("PYTORCH_ENABLE_MPS_FALLBACK", None)
    # the address first: a port in use stops before the model load
    try:
        server = make_server(a.host, a.port)
    except OSError as e:
        return refuse("address", f"{a.host}:{a.port} cannot be used ({e.strerror or type(e).__name__})",
                      EXIT["refused"])
    signal.signal(signal.SIGTERM, _term)
    backend = None
    try:
        eng = Path(a.root).resolve() / ENGINE_REL
        if not eng.is_file() or api.sha256_file(eng) != ENGINE_SHA256:
            raise api.Refused("engine_differs", f"{ENGINE_REL} below --root is absent or is not the frozen file of "
                                                f"the fixed run (SHA-256 {ENGINE_SHA256[:12]}...)", 4)
        # only the local backends of apertus_states.py (no file apertus_backend_*.py: the service never calls
        # another service); env={} keeps APERTUS_URL of this shell out of the choice
        name, tests = api.choose_backend(a.backend, env={})
        api.local_environment(name)
        backend = api.open_backend(name, Path(a.model_dir), Path(a.root).resolve(), tests.get(name))
        desc = backend.describe()
        if desc["model_fingerprint"] != api.WANT_FP:
            raise api.Refused("fingerprint_differs", f"the model folder has the fingerprint "
                                                     f"{desc['model_fingerprint']}, not {api.WANT_FP}: run "
                                                     f"'make setup-apertus'")
        mem = api.memory_check(name)
        say(f"backend {name} ({desc.get('device')}), model fingerprint {api.WANT_FP.split(':')[1][:8]}... ok, "
            f"memory {mem.get('check')}; loading the model (one time)")
        if name == "cpu":
            say("NOTE: torch on the CPU is very slow (many minutes for one page); use it only for checks")
        load = backend.load()
    except api.Refused as e:
        server.server_close()
        if backend is not None:
            backend.close()
        return refuse(e.code, e.message, e.exit_code)
    except KeyboardInterrupt:
        server.server_close()
        return refuse("signal", "stopped during the load", 0)
    svc = Service(backend, desc, token, a.max_body, a.request_timeout, a.max_requests or None, a.idle_exit or None,
                  log_stream, load)
    host, port = server.server_address[0], server.server_address[1]
    svc.log(event="ready", backend=desc.get("backend"), host=host, port=port, auth=svc.auth,
            load_seconds=load.get("load_seconds"), max_requests=svc.max_requests, idle_exit=svc.idle_exit)
    say(f"loaded in {load.get('load_seconds')} s")
    say(f"ready on http://{url_host(host)}:{port} (token {'required' if token else 'not required'}; "
        f"one read-out at a time; the text of each request is not stored)")
    if is_loopback(host):
        say(f"on your own computer: ssh -N -L {port}:127.0.0.1:{port} <user>@<this computer>, then "
            f"APERTUS_URL=http://127.0.0.1:{port} make convert PDF=<file> (docs/apertus-gpu.md)")
    try:
        reason = serve(server, svc)
    finally:
        try:
            backend.close()
        except Exception:  # noqa: BLE001
            pass
    svc.log(event="end", reason=reason, read_outs=svc.read_outs)
    say(f"end ({reason}; {svc.read_outs} read-out requests)")
    if a.log:
        log_stream.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

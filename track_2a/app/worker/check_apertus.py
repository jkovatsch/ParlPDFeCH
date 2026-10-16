#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the checks of the Apertus read-out service and its client (no model, no network).

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude
Opus 5.5), fix step of the Apertus build of 16.10.2026, for the main agent of session ad54858c.

Task
  'make test' runs this file. It checks the rules of worker/apertus_states.py (choice of the backend),
  worker/apertus_serve.py (the read-out service) and worker/apertus_backend_remote.py (its client) with a test
  backend that loads no model. The service runs in a thread of this process on 127.0.0.1 with a free port, and
  each service of this file ends before the file ends. No file is written, no text of a PDF is used, and no
  token is printed (the test tokens are random values of this run).

  C1  the choice 'auto' never takes the CPU: with no GPU it stops with no_gpu, and the message names the 2 ways out
  C2  the choice 'auto' takes the backend remote first when APERTUS_URL is set
  C3  the start rule of the service: another address than 127.0.0.1 needs a token of 32 or more visible ASCII
      characters
  C4  the service with a token: 401 without the token and with a wrong token, 200 with the token
  C5  the service with no token: the Host header must name this computer (403 for another name)
  C6  one read-out at a time: a second POST gets 503 busy; the client waits for a busy service up to
      APERTUS_BUSY_WAIT, and with APERTUS_BUSY_WAIT=0 it stops at once with remote_busy
  C7  the client refuses a service with another model fingerprint (remote_fingerprint_differs)
  C8  a token with a line end at its end works (white space is removed); a token with a line end inside it gives
      remote_token_bad, and no message, record line or JSON line of 'apertus_states.py check' holds the token
  C9  at most 8 open connections; a request that is not complete after the read deadline is cut off

Command: python -I -B worker/check_apertus.py   (exit code 0: each check passed)
Needs: Python 3.10 or later and numpy (the Python of 'make setup'). Runs in about 15 s.
"""

from __future__ import annotations

import contextlib
import hashlib
import http.client
import io
import json
import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import apertus_serve as srv  # noqa: E402
import apertus_states as api  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, facts: str = "") -> None:
    RESULTS.append((name, bool(ok), facts))
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f" ({facts})" if facts and not ok else ""), flush=True)


class FakeBackend(api.Backend):
    """Loads no model. The states are a function of the texts. A prefix with SLOW<s> waits s seconds."""

    name = "fake"

    def __init__(self, fingerprint: str = api.WANT_FP):
        self.fp = fingerprint

    def describe(self) -> dict:
        return {"backend": "fake", "device": "none", "dtype": "bfloat16", "attn": "none", "sdpa": "none",
                "versions": {"python": sys.version.split()[0]}, "model_fingerprint": self.fp, "model": "no-model",
                "engine": "test backend of worker/check_apertus.py"}

    def load(self) -> dict:
        return {"load_seconds": 0.0}

    def readout(self, item: dict, layers) -> dict:
        import numpy as np  # noqa: PLC0415
        pre = item["prefix"]
        if "SLOW" in pre:
            time.sleep(float(pre.split("SLOW", 1)[1].split()[0]))
        n = len(item["suffixes"])
        seed = int(hashlib.sha256(pre.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        return {"suffix_ids": [s["id"] for s in item["suffixes"]], "layers": list(layers),
                "states": rng.standard_normal((n, len(layers), 4096)).astype(np.float16),
                "letter_logprobs": rng.standard_normal((n, 6)).astype(np.float32),
                "n_prefix_tokens": 3, "n_suffix_tokens": [2] * n,
                "prefix_tokens_sha256": hashlib.sha256(pre.encode()).hexdigest(),
                "suffix_tokens_sha256": [hashlib.sha256(s["text"].encode()).hexdigest() for s in item["suffixes"]],
                "boundary_equal_first_suffix": True,
                "timing": {"prefill_seconds": 0.0, "suffix_seconds": 0.0, "seconds": 0.0},
                "peak_bytes": 1, "peak_kind": "none"}


class Running:
    """The real service code with a test backend, in a thread of this process (127.0.0.1, a free port)."""

    def __init__(self, token: str | None, fingerprint: str = api.WANT_FP):
        self.server = srv.make_server("127.0.0.1", 0)
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        b = FakeBackend(fingerprint)
        self.svc = srv.Service(b, b.describe(), token, log_stream=io.StringIO())
        self.thread = threading.Thread(target=srv.serve, args=(self.server, self.svc), daemon=True)
        self.thread.start()

    def end(self) -> None:
        self.svc.stop.set()                 # the loop ends when the service is not busy (reason 'signal')
        self.thread.join(timeout=30)


def req(port: int, method: str, path: str, body: dict | None = None, headers: dict | None = None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    h = dict(headers or {})
    data = None if body is None else json.dumps(body).encode()
    if data is not None:
        h.setdefault("Content-Type", "application/json")
    c.request(method, path, body=data, headers=h)
    r = c.getresponse()
    raw = r.read()
    c.close()
    try:
        obj = json.loads(raw)
    except ValueError:
        obj = None
    return r.status, obj


def item(prefix: str) -> dict:
    return {"protocol": 1, "prefix": prefix, "suffixes": [{"id": "Q0", "text": "q0"}, {"id": "Q1", "text": "q1"}],
            "layers": [20]}


@contextlib.contextmanager
def env(**kv):
    """Environment variables for the time of the block (None: removed)."""
    old = {k: os.environ.get(k) for k in kv}
    try:
        for k, v in kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def remote_backend():
    if "remote" not in api.BACKENDS:
        api.load_extra_backends()
    return api.BACKENDS["remote"]


def check_choice() -> None:
    saved = {k: dict(v) for k, v in api.BACKENDS.items()}
    try:
        for name in ("mlx", "cuda", "mps"):
            api.BACKENDS[name]["probe"] = lambda name=name: {"available": False, "why": f"test: no {name}"}
        api.BACKENDS["cpu"]["probe"] = lambda: {"available": True, "why": None, "device": "cpu"}
        try:
            got = api.choose_backend("auto", env={})
            check("C1 auto never takes the CPU", False, f"auto took {got[0]}")
        except api.Refused as e:
            check("C1 auto never takes the CPU (no_gpu)", e.code == "no_gpu" and e.exit_code == 5, e.code)
            check("C1 the no_gpu message names the 2 ways out",
                  api.GPU_DOC in e.message and "APERTUS=0" in e.message)
        check("C1 the CPU only when forced", api.choose_backend("cpu", env={})[0] == "cpu")
        remote_backend()
        api.BACKENDS["remote"]["probe"] = lambda: {"available": True, "why": None, "host": "127.0.0.1"}
        check("C2 auto takes remote first with APERTUS_URL",
              api.choose_backend("auto", env={"APERTUS_URL": "http://127.0.0.1:9"})[0] == "remote")
        api.BACKENDS["mlx"]["probe"] = lambda: {"available": True, "why": None}
        check("C2 auto takes mlx with no APERTUS_URL", api.choose_backend("auto", env={})[0] == "mlx")
    finally:
        api.BACKENDS.clear()
        api.BACKENDS.update(saved)


def check_start_rule() -> None:
    def refused(host, token):
        try:
            srv.start_rule(host, token)
            return None
        except srv.StartRefused as e:
            return e.code
    check("C3 127.0.0.1 with no token starts", refused("127.0.0.1", None) is None)
    check("C3 0.0.0.0 with no token is refused", refused("0.0.0.0", None) == "token_needed")
    check("C3 a short token is refused", refused("0.0.0.0", "x" * 31) == "token_short")
    check("C3 a token with a line end inside is refused", refused("0.0.0.0", "x" * 20 + "\r" + "y" * 20) == "token_form")
    check("C3 another address with a long token starts", refused("0.0.0.0", secrets.token_hex(24)) is None)


def check_service_and_client() -> None:
    token = secrets.token_hex(24)
    s = Running(token)
    try:
        st, _ = req(s.port, "GET", "/v1/health")
        check("C4 health without the token: 401", st == 401, str(st))
        st, _ = req(s.port, "GET", "/v1/health", headers={"Authorization": "Bearer " + "z" * 48})
        check("C4 health with a wrong token: 401", st == 401, str(st))
        st, h = req(s.port, "GET", "/v1/health", headers={"Authorization": "Bearer " + token})
        check("C4 health with the token: 200", st == 200 and h and h.get("auth") == "bearer", str(st))

        # C6: one read-out at a time
        res: dict = {}
        slow = threading.Thread(target=lambda: res.update(st=req(s.port, "POST", "/v1/readout", item("SLOW4 a"),
                                                                 {"Authorization": "Bearer " + token})[0]))
        slow.start()
        time.sleep(0.8)
        st, o = req(s.port, "POST", "/v1/readout", item("b"), {"Authorization": "Bearer " + token})
        check("C6 a second POST while busy: 503 busy", st == 503 and o and o.get("error") == "busy", str(st))
        mk = remote_backend()
        with env(APERTUS_URL=s.url, APERTUS_TOKEN=token, APERTUS_BUSY_WAIT="0"):
            b = mk["open"](None, HERE, mk["probe"]())
            try:
                b.load()
                check("C6 the client with APERTUS_BUSY_WAIT=0 stops at once", False, "load passed")
            except api.Refused as e:
                check("C6 the client with APERTUS_BUSY_WAIT=0 stops at once (remote_busy)", e.code == "remote_busy",
                      e.code)
        with env(APERTUS_URL=s.url, APERTUS_TOKEN=token, APERTUS_BUSY_WAIT="20"):
            b = mk["open"](None, HERE, mk["probe"]())
            t0 = time.time()
            try:
                b.load()
                r = b.readout({"doc_id": "x", "prefix": "c", "suffixes": [{"id": "Q0", "text": "q"}]}, (20,))
                check("C6 the client waits for the busy service, then reads out",
                      r["states"].shape == (1, 1, 4096) and time.time() - t0 >= 1.0, f"{time.time() - t0:.1f} s")
            except api.Refused as e:
                check("C6 the client waits for the busy service, then reads out", False, e.code)
        slow.join(timeout=30)
        check("C6 the slow read-out ends with 200", res.get("st") == 200, str(res.get("st")))

        # C8: a token with a line end
        with env(APERTUS_URL=s.url, APERTUS_TOKEN=token + "\r\n", APERTUS_BUSY_WAIT="0"):
            p = mk["probe"]()
            check("C8 a token with a line end at its end works (stripped)", p.get("available") is True,
                  str(p.get("code")))
        bad = token[:20] + "\r" + token[20:]
        with env(APERTUS_URL=s.url, APERTUS_TOKEN=bad):
            p = mk["probe"]()
            check("C8 a token with a line end inside: remote_token_bad", p.get("code") == "remote_token_bad",
                  str(p.get("code")))
            check("C8 the message holds no part of the token", token[:20] not in str(p) and token[20:] not in str(p))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = api.cmd_check(type("A", (), {"backend": "auto", "root": str(HERE), "model_dir": None,
                                                  "no_model": True})())
            out = buf.getvalue()
            check("C8 'check' stops with exit 8 and remote_token_bad",
                  rc == 8 and json.loads(out).get("reason") == "remote_token_bad", f"rc {rc}")
            check("C8 the JSON line of 'check' holds no part of the token",
                  token[:20] not in out and token[20:] not in out)
        with env(APERTUS_TOKEN=token):
            msg = api.scrub(f"ValueError: Invalid header value b'Bearer {token}\\r'")
            check("C8 scrub replaces the token in a message", token not in msg and "<APERTUS_TOKEN>" in msg)
    finally:
        s.end()

    # C5: no token, the Host header
    s = Running(None)
    try:
        st, _ = req(s.port, "GET", "/v1/health", headers={"Host": "evil.example"})
        check("C5 no token: Host of another name gives 403", st == 403, str(st))
        st, _ = req(s.port, "GET", "/v1/health")
        check("C5 no token: Host 127.0.0.1 gives 200", st == 200, str(st))
    finally:
        s.end()

    # C7: another model fingerprint
    s = Running(None, fingerprint="apertus-v1.5-8b-text-bf16:" + "0" * 64)
    try:
        with env(APERTUS_URL=s.url, APERTUS_TOKEN=None):
            p = remote_backend()["probe"]()
            check("C7 another model fingerprint: remote_fingerprint_differs",
                  p.get("code") == "remote_fingerprint_differs", str(p.get("code")))
    finally:
        s.end()


def check_connections() -> None:
    old = srv.Handler.read_deadline
    srv.Handler.read_deadline = 2.0
    s = Running(None)
    held = []
    try:
        for _ in range(srv.MAX_CONNECTIONS):
            c = socket.create_connection(("127.0.0.1", s.port), timeout=10)
            c.sendall(b"GET /v1/health HTTP/1.0\r\n")       # no end of the headers: a slow sender
            held.append(c)
        time.sleep(0.5)
        extra = socket.create_connection(("127.0.0.1", s.port), timeout=10)
        extra.sendall(b"GET /v1/health HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n")
        try:
            got = extra.recv(64)
        except (ConnectionResetError, OSError):
            got = b""
        extra.close()
        check("C9 a connection over the limit of 8 is closed at once", got == b"", repr(got[:20]))
        time.sleep(srv.Handler.read_deadline + 1.5)
        cut = 0
        for c in held:
            try:
                c.settimeout(2)
                cut += c.recv(64) == b""
            except OSError:
                cut += 1
        check("C9 an incomplete request is cut off after the read deadline", cut == len(held), f"{cut} of {len(held)}")
        st, _ = req(s.port, "GET", "/v1/health")
        check("C9 after the cut, a request is served again", st == 200, str(st))
    finally:
        for c in held:
            c.close()
        s.end()
        srv.Handler.read_deadline = old


def main() -> int:
    for k in ("APERTUS_URL", "APERTUS_TOKEN", "APERTUS_BUSY_WAIT", "APERTUS_REMOTE_TIMEOUT"):
        os.environ.pop(k, None)
    t0 = time.time()
    check_choice()
    check_start_rule()
    check_service_and_client()
    check_connections()
    bad = [n for n, ok, _ in RESULTS if not ok]
    print(f"{'PASS' if not bad else 'FAIL'}: worker/check_apertus.py, {len(RESULTS) - len(bad)} of {len(RESULTS)} "
          f"checks passed ({time.time() - t0:.0f} s; no model, no network)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

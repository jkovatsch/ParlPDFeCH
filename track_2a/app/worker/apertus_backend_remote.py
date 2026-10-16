#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the backend 'remote' of worker/apertus_states.py (a GPU of another computer).

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file. Actor: workflow sub-agent (Claude
Opus 5.5), builder C of the Apertus build of 16.10.2026, for the main agent of session ad54858c.

Task
  The client of the read-out service worker/apertus_serve.py ('make serve-apertus' on a computer with a GPU; this
  computer, another computer, or a rented GPU in the cloud). apertus_states.load_extra_backends() imports this
  file and calls register(api). The backend sends the prompt texts of one document (prefix and suffixes of
  m11_prompts_values.item, made on THIS computer after the template check) to the service and gets back the
  states after layer 20 at the last token of each suffix (float16). This computer needs no model files and no GPU.
  The heads, the combined reader, the page finder, the writer and the validator stay on this computer.

  Before each read-out the client asks GET /v1/health. It refuses a service whose model fingerprint is not the
  fingerprint of the heads (c10cd28d...786c3), a service that speaks another protocol, and an answer whose states
  have another form or another SHA-256 than the answer says. The record names the backend 'remote:<backend of the
  service>' (for example remote:cuda) and only the host of the URL (no path, no port, no token).

Environment
  APERTUS_URL      the address of the service: http://127.0.0.1:8090 through an ssh tunnel (docs/apertus-gpu.md),
                   or https://<host>[:port][/path]. With it, the choice 'auto' of apertus_states.py takes this
                   backend first. No user name or password in the URL, no query.
  APERTUS_TOKEN    the token of the service. This file reads it only to send it in the header Authorization of
                   each request. It never prints, logs or stores it, and it puts it in no file and no record.
                   White space at the start and at the end (for example the line end of a token file with
                   Windows line ends) is removed. A token with another character than visible ASCII (33 to 126,
                   the rule of the service) is refused with remote_token_bad before any request; the message
                   does not hold the value.
  APERTUS_ALLOW_HTTP=1  allows plain http to an address that is not this computer (only for a private network,
                   for example WireGuard). Without it the client refuses: the text of the PDF and the token would
                   go in clear text over the network.
  APERTUS_REMOTE_TIMEOUT  seconds for one document: the wait for a busy service plus the wait for the answer of
                   the read-out (default 1560). worker/apertus_provider.py sets a lower value when the time limit
                   of its subprocess is lower, so that this client ends by itself first.
  APERTUS_BUSY_WAIT  seconds to wait for a busy service (one read-out at a time) before the reason remote_busy
                   (default 120; 0: no wait). The wait asks GET /v1/health again every few seconds.
  The client uses no proxy of the environment and follows no redirect (the text goes only to APERTUS_URL).

Reason codes (exit code 8 of apertus_states.py; the record key 'exit')
  remote_url_absent, remote_url_bad, remote_plain_http, remote_token_bad, remote_unreachable, remote_timeout,
  remote_unauthorized, remote_forbidden, remote_busy, remote_ending, remote_time_limit, remote_too_large,
  remote_redirect, remote_not_service, remote_protocol, remote_fingerprint_differs, remote_bad_answer,
  remote_error.
  The input reasons of the service (prefix_too_long, token_problems, not_finite) keep their own codes.

Python standard library only (urllib, json, base64); numpy for the states (as every backend).
Tested: only on one Mac (Apple M4, 32 GB), 16.10.2026: client and service on this one computer (127.0.0.1),
and test services of the test script. NOT tested: a second computer, an ssh tunnel, https, CUDA.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import http.client
import ipaddress
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

NAME = "remote"
PROTOCOL = 1
SERVICE = "parlpdfech-apertus-readout"
HEALTH_TIMEOUT = 30.0
DEFAULT_READOUT_TIMEOUT = 1560.0
DEFAULT_BUSY_WAIT = 120.0
BUSY_POLL = 5.0                     # seconds between 2 questions to a busy service
MIN_READOUT_SECONDS = 10.0          # a read-out with less time left is not started
MAX_ANSWER_BYTES = 256 * 1024 * 1024
MAX_ERROR_BYTES = 64 * 1024
HIDDEN = 4096
ASK_LAYERS = (20,)                  # the layer of the heads; the other layers do not travel
N_LETTERS = 6
RX_HEX64 = re.compile(r"^[0-9a-f]{64}$")
RX_TOKEN = re.compile(r"[\x21-\x7e]+")      # visible ASCII: the token rule of the service (apertus_serve.start_rule)
GPU_DOC = "docs/apertus-gpu.md"
API = None                          # the module apertus_states (set by register)
_CLS = None


def _clean(s, n: int = 300) -> str:
    """A text of the service for a message: printable characters only, at most n characters."""
    t = "".join(c if c.isprintable() else " " for c in str(s or ""))
    return t if len(t) <= n else t[: n - 3] + "..."


def _refused(code: str, message: str):
    return API.Refused(code, message, API.EXIT_CODES.get(code, API.REMOTE_EXIT))


def is_loopback(host: str) -> bool:
    h = str(host or "").strip("[]").lower()
    if h == "localhost":
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


class Url:
    """APERTUS_URL after the checks. host: the host only (for the record); where: host and port (for messages)."""

    def __init__(self, raw: str, env=None):
        env = os.environ if env is None else env
        raw = str(raw or "").strip()
        if not raw:
            raise _refused("remote_url_absent", f"APERTUS_URL is not set (the address of the read-out service of a "
                                                f"GPU computer, see {GPU_DOC})")
        try:
            p = urllib.parse.urlsplit(raw)
            port = p.port
        except ValueError as e:
            raise _refused("remote_url_bad", f"APERTUS_URL is not a URL ({_clean(e, 80)})") from e
        if p.scheme not in ("http", "https") or not p.hostname:
            raise _refused("remote_url_bad", "APERTUS_URL must start with http:// or https:// and name a host")
        if p.username is not None or p.password is not None:
            raise _refused("remote_url_bad", "APERTUS_URL must not hold a user name or a password (the token goes "
                                             "in APERTUS_TOKEN)")
        if p.query or p.fragment:
            raise _refused("remote_url_bad", "APERTUS_URL must not have a query (?) or a fragment (#)")
        self.scheme, self.host = p.scheme, p.hostname
        self.port = port or (443 if p.scheme == "https" else 80)
        self.path = p.path.rstrip("/")
        self.where = f"{'[' + self.host + ']' if ':' in self.host else self.host}:{self.port}"
        self.base = f"{p.scheme}://{self.where}{self.path}"
        if self.scheme == "http" and not is_loopback(self.host) and env.get("APERTUS_ALLOW_HTTP") != "1":
            raise _refused("remote_plain_http", f"APERTUS_URL is plain http to {self.where}, which is not this "
                                                f"computer: the text of the PDF and the token would go in clear "
                                                f"text. Use an ssh tunnel (APERTUS_URL=http://127.0.0.1:<port>), "
                                                f"or https, or APERTUS_ALLOW_HTTP=1 for a private network "
                                                f"({GPU_DOC})")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: PLR0913
        return None                  # urllib then raises HTTPError with the code 3xx


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def _token() -> str | None:
    """APERTUS_TOKEN for the header Authorization, or None. The value is stripped of white space at both ends. A
    value with another character than visible ASCII is refused (remote_token_bad); the message never holds it. The
    check comes before any request: http.client would otherwise refuse the header with a message that holds it."""
    tok = (os.environ.get("APERTUS_TOKEN") or "").strip()
    if not tok:
        return None
    if not RX_TOKEN.fullmatch(tok):
        raise _refused("remote_token_bad", "APERTUS_TOKEN has a character that is not visible ASCII (for example a "
                                           "space or a line end inside it). The value is not shown. Set it again "
                                           "from the token of the service, with no other character")
    return tok


def _token_set() -> bool:
    """True if APERTUS_TOKEN has a value (for the text of a 401 answer; no check, no exception)."""
    return bool((os.environ.get("APERTUS_TOKEN") or "").strip())


def _float_env(name: str, default: float) -> float:
    try:
        v = float(os.environ.get(name) or default)
    except ValueError:
        return default
    return v if v >= 0 else default


def _http_refused(u: Url, status: int, obj: dict | None):
    obj = obj if isinstance(obj, dict) else {}
    code, msg = str(obj.get("error") or ""), _clean(obj.get("message") or "")
    w = u.where
    if status == 401:
        if not _token_set():
            return _refused("remote_unauthorized", f"the service at {w} needs a token (HTTP 401): set APERTUS_TOKEN "
                                                   f"to the token of the service")
        return _refused("remote_unauthorized", f"the service at {w} refused the token (HTTP 401): APERTUS_TOKEN is "
                                               f"not the token of that service")
    if status == 403:
        return _refused("remote_forbidden", f"the service at {w} refused the request (HTTP 403, {code or 'forbidden'}"
                                            f"): without a token it answers only to http://127.0.0.1:<port>")
    if status == 503 and code == "ending":
        return _refused("remote_ending", f"the service at {w} is ending (HTTP 503); start it again")
    if status == 503:
        return _refused("remote_busy", f"the service at {w} is busy with another document (HTTP 503; one read-out "
                                       f"at a time). Try again when it is free")
    if status == 504:
        return _refused("remote_time_limit", f"the service at {w} stopped waiting for the read-out (HTTP 504, time "
                                             f"limit of the service)")
    if status == 413:
        return _refused("remote_too_large", f"the service at {w} refused the size of the prompt texts (HTTP 413): "
                                            f"{msg}")
    if status == 422 and code in API.EXIT_CODES:
        return API.Refused(code, f"the service at {w}: {msg or code}")
    if 300 <= status < 400:
        return _refused("remote_redirect", f"the service at {w} answered with a redirect (HTTP {status}); the client "
                                           f"follows no redirect (the text would go to another address)")
    if status == 404:
        return _refused("remote_not_service", f"{w} has no read-out service at this path (HTTP 404): check "
                                              f"APERTUS_URL ('make serve-apertus' on the GPU computer)")
    extra = f" ({code}: {msg})" if code else ""
    return _refused("remote_error", f"the service at {w} answered HTTP {status}{extra}")


def call(u: Url, method: str, path: str, body: bytes | None = None, timeout: float = HEALTH_TIMEOUT,
         limit: int = MAX_ANSWER_BYTES) -> tuple[dict, int]:
    """One request. Returns (JSON object, number of bytes of the answer). Raises Refused for each problem."""
    headers = {"Accept": "application/json", "User-Agent": "parlpdfech-apertus-client/1"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    tok = _token()
    if tok is not None:
        headers["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(u.base + path, data=body, method=method, headers=headers)
    del tok
    try:
        with _opener().open(req, timeout=timeout) as resp:
            raw = resp.read(limit + 1)
    except urllib.error.HTTPError as e:
        try:
            obj = json.loads(e.read(MAX_ERROR_BYTES).decode("utf-8", "replace"))
        except (ValueError, OSError):
            obj = None
        raise _http_refused(u, e.code, obj) from None
    except TimeoutError:
        raise _refused("remote_timeout", f"the service at {u.where} gave no answer within {timeout:.0f} s") from None
    except urllib.error.URLError as e:
        why = e.reason
        if isinstance(why, TimeoutError):
            raise _refused("remote_timeout", f"the service at {u.where} gave no answer within {timeout:.0f} s") \
                from None
        raise _refused("remote_unreachable", f"no read-out service answers at {u.where} "
                                             f"({_clean(getattr(why, 'strerror', None) or why, 100)}). Start "
                                             f"'make serve-apertus' on the GPU computer and the ssh tunnel") \
            from None
    except (ConnectionError, OSError) as e:
        raise _refused("remote_unreachable", f"the connection to {u.where} failed ({type(e).__name__})") from None
    except (ValueError, http.client.HTTPException) as e:
        # for example a header value that http.client refuses, or an answer that is not HTTP: the type name only
        # (the text of such an exception can hold a header value)
        raise _refused("remote_error", f"the request to {u.where} failed ({type(e).__name__})") from None
    if len(raw) > limit:
        raise _refused("remote_bad_answer", f"the answer of {u.where} is larger than {limit} bytes")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise _refused("remote_not_service", f"{u.where} gave no JSON answer: is it the read-out service?") from None
    if not isinstance(obj, dict):
        raise _refused("remote_not_service", f"{u.where} gave no JSON object")
    return obj, len(raw)


def health(u: Url) -> dict:
    h, _ = call(u, "GET", "/v1/health", timeout=HEALTH_TIMEOUT, limit=MAX_ERROR_BYTES * 4)
    if h.get("service") != SERVICE:
        raise _refused("remote_not_service", f"{u.where} is not the ParlPDFeCH read-out service")
    if h.get("protocol") != PROTOCOL:
        raise _refused("remote_protocol", f"the service at {u.where} speaks protocol {_clean(h.get('protocol'), 20)}, "
                                          f"this client protocol {PROTOCOL}")
    return h


def check_fingerprint(u: Url, h: dict) -> None:
    fp = str(h.get("model_fingerprint") or "")
    if fp != API.WANT_FP:
        raise _refused("remote_fingerprint_differs", f"the service at {u.where} has the model fingerprint "
                                                     f"{_clean(fp, 120) or '(none)'}, not {API.WANT_FP}: the heads "
                                                     f"are valid for that model only. Run 'make setup-apertus' on "
                                                     f"the GPU computer")


def small_health(h: dict) -> dict:
    keys = ("service_version", "backend", "device", "dtype", "attn", "sdpa", "engine", "model", "model_fingerprint",
            "versions", "engine_code_sha256", "loaded", "busy", "max_body_bytes", "auth", "load_seconds")
    return {k: h.get(k) for k in keys}


def probe() -> dict:
    """Available: APERTUS_URL is set and right, the service answers, speaks protocol 1 and has the model of the
    heads. A busy service is available (the check of 'make convert' must not stop for it); load() asks again."""
    try:
        u = Url(os.environ.get("APERTUS_URL", ""))
    except API.Refused as e:
        return {"available": False, "why": e.message, "code": e.code, "exit_code": e.exit_code}
    try:
        h = health(u)
        check_fingerprint(u, h)
    except API.Refused as e:
        return {"available": False, "why": e.message, "code": e.code, "exit_code": e.exit_code, "host": u.host}
    return {"available": True, "why": None, "host": u.host, "device": f"remote:{h.get('device')}",
            "server_backend": h.get("backend"), "busy": bool(h.get("busy")), "health": small_health(h),
            "note": f"the text of each PDF goes to the read-out service at {u.where} (APERTUS_URL)"}


def _arr(u: Url, spec, n: int, width: tuple[int, ...], dtype: str):
    """One array of the answer (base64), checked: dtype, byte order, shape, length and (if given) SHA-256."""
    import numpy as np  # noqa: PLC0415
    if not isinstance(spec, dict):
        raise _refused("remote_bad_answer", f"the answer of {u.where} has no array")
    shape = [n, *width]
    if spec.get("dtype") != dtype or spec.get("byteorder") != "little" or spec.get("shape") != shape:
        raise _refused("remote_bad_answer", f"the answer of {u.where} has an array of the form "
                                            f"{_clean(spec.get('dtype'), 20)} {_clean(spec.get('shape'), 40)}, not "
                                            f"{dtype} {shape}")
    try:
        raw = base64.b64decode(str(spec.get("base64") or ""), validate=True)
    except (binascii.Error, ValueError):
        raise _refused("remote_bad_answer", f"the answer of {u.where} has an array that is not base64") from None
    want = int(np.prod(shape)) * np.dtype(dtype).itemsize
    if len(raw) != want:
        raise _refused("remote_bad_answer", f"the answer of {u.where} has {len(raw)} bytes for an array of {want}")
    if spec.get("sha256") is not None and hashlib.sha256(raw).hexdigest() != spec.get("sha256"):
        raise _refused("remote_bad_answer", f"the SHA-256 of an array of {u.where} is not the SHA-256 of its bytes")
    a = np.frombuffer(raw, dtype=np.dtype(dtype).newbyteorder("<")).reshape(shape).astype(dtype)
    if not np.isfinite(a).all():
        raise _refused("not_finite", f"the service at {u.where} gave values that are not finite")
    return a


def _make_class(api):
    class RemoteBackend(api.Backend):
        """A read-out service of a GPU computer (protocol 1). describe(), load() and readout() as the interface of
        apertus_states.Backend; readout gives the layer 20 only."""

        name = NAME
        remote = True

        def __init__(self, model_dir, root, facts):
            self.u = Url(os.environ.get("APERTUS_URL", ""))
            self.h = (facts or {}).get("health") or small_health(health(self.u))
            check_fingerprint(self.u, self.h)
            self.deadline = None             # set by load(): the end of the time for this document
            self.busy_until = None           # set by load(): the end of the wait for a busy service
            self.busy_waited = 0.0

        def _left(self) -> float:
            """Seconds left for this document (APERTUS_REMOTE_TIMEOUT from the start of load())."""
            if self.deadline is None:
                return _float_env("APERTUS_REMOTE_TIMEOUT", DEFAULT_READOUT_TIMEOUT)
            return self.deadline - time.time()

        def _free_health(self) -> dict:
            """GET /v1/health until the service has loaded the model and is not busy, at most until busy_until.
            Raises remote_busy after that time (the service reads out one document at a time)."""
            u = self.u
            while True:
                h = health(u)
                check_fingerprint(u, h)
                free = bool(h.get("loaded")) and not h.get("busy")
                if free:
                    return h
                now = time.time()
                if self.busy_until is None or now + BUSY_POLL > self.busy_until:
                    why = "has not loaded the model yet" if not h.get("loaded") else \
                        "is busy with another document (one read-out at a time)"
                    waited = f" after a wait of {self.busy_waited:.0f} s" if self.busy_waited >= 1 else ""
                    raise _refused("remote_busy", f"the service at {u.where} {why}{waited}. Try again when it is "
                                                  f"free (APERTUS_BUSY_WAIT sets the wait)")
                time.sleep(BUSY_POLL)
                self.busy_waited += time.time() - now

        def describe(self) -> dict:
            h = self.h
            from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415
            try:
                np_v = version("numpy")
            except PackageNotFoundError:
                np_v = None
            return {"backend": f"remote:{h.get('backend')}", "device": f"remote:{h.get('device')}",
                    "dtype": h.get("dtype"), "attn": h.get("attn"), "sdpa": h.get("sdpa"),
                    "versions": h.get("versions"), "model_fingerprint": h.get("model_fingerprint"),
                    "model": h.get("model"),
                    "engine": f"read-out service worker/apertus_serve.py, protocol {PROTOCOL}, "
                              f"{h.get('service_version')}: {h.get('engine')}",
                    "engine_code_sha256": h.get("engine_code_sha256"), "host": self.u.host,
                    "server_backend": h.get("backend"),
                    "client_versions": {"python": sys.version.split()[0], "numpy": np_v}}

        def load(self) -> dict:
            """No model load on this computer: the service loaded the model one time at its start. The health is
            asked again: fingerprint, loaded, busy."""
            t0 = time.time()
            budget = _float_env("APERTUS_REMOTE_TIMEOUT", DEFAULT_READOUT_TIMEOUT)
            self.deadline = t0 + budget
            self.busy_until = t0 + min(_float_env("APERTUS_BUSY_WAIT", DEFAULT_BUSY_WAIT),
                                       max(0.0, budget - MIN_READOUT_SECONDS))
            h = self._free_health()
            self.h = small_health(h)
            return {"load_seconds": 0.0, "health_seconds": round(time.time() - t0, 3),
                    "busy_wait_seconds": round(self.busy_waited, 1),
                    "service_load_seconds": h.get("load_seconds"),
                    "note": "the service loaded the model one time at its start"}

        def readout(self, item: dict, layers=None) -> dict:
            u = self.u
            ids = [str(s["id"]) for s in item["suffixes"]]
            n = len(ids)
            body = json.dumps({"protocol": PROTOCOL, "prefix": item["prefix"],
                               "suffixes": [{"id": str(s["id"]), "text": s["text"]} for s in item["suffixes"]],
                               "layers": list(ASK_LAYERS)}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            lim = self.h.get("max_body_bytes")
            if isinstance(lim, int) and len(body) > lim:
                raise _refused("remote_too_large", f"the prompt texts have {len(body)} bytes; the service at "
                                                   f"{u.where} takes at most {lim}")
            while True:
                tmo = self._left()
                if tmo < MIN_READOUT_SECONDS:
                    raise _refused("remote_timeout", f"less than {MIN_READOUT_SECONDS:.0f} s are left for the "
                                                     f"read-out at {u.where} (APERTUS_REMOTE_TIMEOUT)")
                t0 = time.time()
                try:
                    a, nbytes = call(u, "POST", "/v1/readout", body, timeout=tmo)
                    break
                except API.Refused as e:
                    # HTTP 503 busy at the POST (another client came between the health and the POST): wait for
                    # the service as load() does, then send again
                    if e.code != "remote_busy" or self.busy_until is None or time.time() + BUSY_POLL > self.busy_until:
                        raise
                    time.sleep(BUSY_POLL)
                    self.busy_waited += BUSY_POLL
                    self._free_health()
            http_s = time.time() - t0
            if a.get("protocol") != PROTOCOL:
                raise _refused("remote_protocol", f"the answer of {u.where} is not of protocol {PROTOCOL}")
            check_fingerprint(u, a)
            if a.get("suffix_ids") != ids:
                raise _refused("remote_bad_answer", f"the answer of {u.where} has other suffix ids than the request")
            if a.get("layers") != list(ASK_LAYERS):
                raise _refused("remote_bad_answer", f"the answer of {u.where} has the layers "
                                                    f"{_clean(a.get('layers'), 40)}, not {list(ASK_LAYERS)}")
            states = _arr(u, a.get("states"), n, (len(ASK_LAYERS), HIDDEN), "float16")
            lets = None if a.get("letter_logprobs") is None else _arr(u, a["letter_logprobs"], n, (N_LETTERS,),
                                                                      "float32")
            nst, npt = a.get("n_suffix_tokens"), a.get("n_prefix_tokens")
            pts, sts = a.get("prefix_tokens_sha256"), a.get("suffix_tokens_sha256")
            if (type(npt) is not int or npt < 1 or not isinstance(nst, list) or len(nst) != n
                    or any(type(k) is not int or k < 1 for k in nst) or not isinstance(pts, str)
                    or not RX_HEX64.match(pts) or not isinstance(sts, list) or len(sts) != n
                    or any(not isinstance(s, str) or not RX_HEX64.match(s) for s in sts)):
                raise _refused("remote_bad_answer", f"the answer of {u.where} has no right token counts or token "
                                                    f"SHA-256 values")
            tm = a.get("timing") if isinstance(a.get("timing"), dict) else {}
            timing = {k: float(tm.get(k) or 0.0) for k in ("prefill_seconds", "suffix_seconds", "seconds")}
            pk = a.get("peak_kind")
            return {"suffix_ids": ids, "layers": list(ASK_LAYERS), "states": states, "letter_logprobs": lets,
                    "n_prefix_tokens": npt, "n_suffix_tokens": nst, "prefix_tokens_sha256": pts,
                    "suffix_tokens_sha256": sts,
                    "boundary_equal_first_suffix": a.get("boundary_equal_first_suffix"), "timing": timing,
                    "peak_bytes": a.get("peak_bytes") if type(a.get("peak_bytes")) is int else None,
                    "peak_kind": f"{_clean(pk, 60)} (on the computer of the service)" if pk else None,
                    "remote": {"host": u.host, "server_backend": _clean(a.get("backend"), 40),
                               "device": _clean(a.get("device"), 40),
                               "service_version": _clean(a.get("service_version"), 40),
                               "versions": a.get("versions") if isinstance(a.get("versions"), dict) else None,
                               "http_seconds": round(http_s, 3), "queue_seconds": a.get("queue_seconds"),
                               "busy_wait_seconds": round(self.busy_waited, 1),
                               "bytes_sent": len(body), "bytes_received": nbytes}}

        def close(self) -> None:
            return None

    return RemoteBackend


def _open(model_dir, root, facts):
    return _CLS(model_dir, root, facts)


def register(api) -> None:
    """Called by apertus_states.load_extra_backends(): the backend 'remote', the first choice of 'auto' when
    APERTUS_URL is set."""
    global API, _CLS
    API = api
    _CLS = _make_class(api)
    api.register_backend(NAME, probe, _open, auto_when=lambda env: bool((env or {}).get("APERTUS_URL")))

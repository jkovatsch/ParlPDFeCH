# SPDX-License-Identifier: Apache-2.0
"""Path 2 (E34), step "Design on dev": local Apertus-v1.5-8B (bf16, MLX) for R1 and R2.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5).
Data: src/m05_cls_data.py (datasets, text cache, lock, assert_allowed).

1 Tasks (labels only from I95)
  R1  ProcedureState.decision at the stage executive_response: recommended_for or recommended_against.
  R2  The document holds a response of the executive (ResponseStep.texts): yes or no.

2 Method (E18, E19, E31 point 4, E34)
  Input: the system text, [few-shot turns], then the user turn "Dokument:\n" + whole document text +
  "\n\n" + question (whole document first, question last), then the assistant prefix. The document text
  is the text cache daten/cls/text/<doc_id>.txt (model input text only: no category, no name, no URL,
  no date, no export field). The language of a variant with language-dependent wording comes from the
  text only (m05_cls_data.language()).
  Output: a constrained choice between the 2 option strings. The script feeds the option tokens after
  the prompt and reads the token log-probabilities. At each token position, the probability is
  normalized over the tokens that continue at least one option (constrained decoder, as
  m03_sub_common.choice_probs). p = probability of the first option (recommended_for, yes).
  Decision: first option if p >= t. Value status: certain if max(p, 1 - p) >= a, else unsure.
  Local model only: daten/modelle/apertus-v1.5-8b-text-bf16 (mlx), memory limits of
  m04_kern.speicher_begrenzen(), lock daten/cls/model.lock (m05_cls_data.model_lock), no Docling
  process at the same time (process rule 7.4), socket connections refused in the process (no network).
  Documents with more than MAX_TEXT_TOKENS text tokens get no readout (memory limit); they count as
  wrong and unsure.
  Disk cache: daten/cls/cache/<k[:2]>/<k>.json, k = SHA-256 of (model fingerprint, prompt token ids,
  option token ids). It holds probabilities and token counts, no text.
  Log (GC.4): daten/cls/apertus/score_log.jsonl, one line for each scored prompt: doc_id, variant,
  SHA-256 of the prompt token ids, of the document text and of the variant template.

3 Variants (VARIANTS below)
  r1_v1_i95_de       zero-shot, German question with the I95 meaning of the 2 values, letters A/B
  r1_v2_words_lang   zero-shot, question and option words in the language of the document
                     (de dafür/dagegen, fr pour/contre, it favorevole/contrario; other languages: de)
  r1_v3_i95_en       zero-shot, English question with the literal I95 descriptions, letters A/B
  r1_v4_fewshot_de   r1_v1 with 2 short dev design examples before the document (SHOTS)
  r2_v1_de           zero-shot, German question, letters A/B
  r2_v2_words_lang   zero-shot, question and words in the language of the document (ja/nein, oui/non, sì/no)
  r2_v3_author_de    zero-shot, German question on the author of the main text, letters A/B
  r2_v4_fewshot_de   r2_v1 with 2 short dev design examples
  The zero-shot variants of a task share one prefill of the document (same system text and document
  head). A few-shot variant has its own prefill; the prefill of the examples is made one time and kept.
  Examples: a target document that is an example gets the alternate example (as S1).

4 Selection rules (written before the first model value; dev design only)
  a) Primary value at t = 0.5: R1 macro F1 of the 2 options; R2 balanced accuracy.
  b) The variant with the highest primary value wins. A variant within TIE (0.01) of the best value is
     equal; among equal variants: fewer prefills (zero-shot before few-shot), then higher accuracy, then
     the lower variant number.
  c) Decision threshold t: grid T_GRID; t* = the grid value with the highest primary value (tie: the
     value nearest to 0.5). t = t* only if the primary value at t* is T_MIN_GAIN (0.03) or more above
     the value at 0.5; else t = 0.5.
  d) Acceptance threshold a: grid A_GRID; the smallest a for which, on design, the values with status
     certain have accuracy (R1) or balanced accuracy (R2) of 0.90 or more and the coverage is 0.50 or
     more (R2: in each class of the source label). If no a meets this: a = null (each value unsure).
  e) Freeze: daten/cls/design_choice.json (template, t, a, SHA-256 of this file and of the inputs).
     The check run refuses to start if the SHA-256 of this file differs from the frozen value.

5 Baselines (same documents)
  majority   the majority source label of the dev design set (R1 recommended_against, R2 no).
  keyword    R1: last match of m05_cls_data.RX_REC in the whole text; no match gives recommended_against
             (criteria file, chapter 4.1, item 12).
  heading    R2: m05_cls_data.RX_EXEC_RESPONSE in the first 3,000 characters gives yes, else no
             (criteria file, chapter 4.1, item 13).
  s1_answer  R2, information: the answer marks of the S1 role rule (src/m03_sub_s1_role.py, RX_ANSWER_START
             without RX_CONSULT) on text lines of 90 characters or fewer; a mark gives yes. The full S1
             rule needs Docling atoms and export categories (the label source), and rolle() is the label
             source itself. Thus they are not baselines here.

6 Sets
  design  dev rows with subset design (R1 150, R2 150).
  check   dev rows with subset check: R1 all (160); R2 the first CHECK_R2_N (1,000) by rank.
  validation  not part of this step. score_set(task, "validation", [frozen variant]) is the function for
              the one validation run (assert_allowed with the split validation).

Usage:
  .venv/bin/python src/m05_cls_apertus.py design [--task r1|r2] [--limit N]   (model: all variants, design)
  .venv/bin/python src/m05_cls_apertus.py choose                             (no model: selection, freeze)
  .venv/bin/python src/m05_cls_apertus.py check [--task r1|r2]               (model: frozen variant, check)
  .venv/bin/python src/m05_cls_apertus.py show-prompt TASK VARIANT DOC_ID    (terminal only, dev only)
Outputs: daten/cls/apertus/ (scores, metrics, logs), daten/cls/design_choice.json, daten/cls/cache/.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m05_cls_data as cd  # noqa: E402

ROOT = cd.ROOT
OUT = cd.OUT / "apertus"
CACHE = cd.OUT / "cache"
CHOICE_FILE = cd.OUT / "design_choice.json"
LOG = OUT / "score_log.jsonl"
RUNS = OUT / "runs.jsonl"
VERSION = "cls-apertus-1"
PREFILL_CHUNK = 2048
MAX_TEXT_TOKENS = 32768
DOCLING_CHECK_EVERY = 20
CHECK_R2_N = 1000
BOOT_N = 10000
BOOT_SEED = 20261009
T_GRID = [round(0.05 * i, 2) for i in range(1, 20)]
A_GRID = [0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999]
T_MIN_GAIN = 0.03
TIE = 0.01
A_MIN_ACC = 0.90
A_MIN_COVERAGE = 0.50

OPTIONS = {"r1": ("recommended_for", "recommended_against"), "r2": ("yes", "no")}
PRIMARY = {"r1": "macro_f1", "r2": "balanced_accuracy"}
MAJORITY = {"r1": "recommended_against", "r2": "no"}

SYSTEM = "Du liest ein Dokument aus einem Schweizer Parlament und beantwortest eine Frage dazu."
DOC_HEAD = "Dokument:\n"
SEP = "\n\n"

Q_R1_DE = (
    "Frage: Welche formelle Empfehlung gibt die Exekutive (Regierung, Regierungsrat, Stadtrat oder Gemeinderat) "
    "dem Parlament zu diesem Vorstoss (Motion oder Postulat)?\n"
    "A = Die Exekutive empfiehlt Annahme (dafür): annehmen, überweisen, erheblich erklären, oder annehmen und "
    "zugleich abschreiben.\n"
    "B = Die Exekutive empfiehlt Ablehnung (dagegen): ablehnen, nicht überweisen, nicht erheblich erklären, "
    "nicht entgegennehmen.\n"
    "Antworte nur mit dem Buchstaben.")
Q_R1_EN = (
    "Question: What formal recommendation does the executive (government, cantonal government, city council or "
    "municipal council) give to the parliament on this motion or postulate?\n"
    "A = recommended_for: Executive recommends adoption (dafür).\n"
    "B = recommended_against: Executive recommends rejection (dagegen).\n"
    "Answer with the letter only.")
Q_R2_DE = (
    "Frage: Enthält dieses Dokument eine Antwort oder Stellungnahme der Exekutive (Regierung, Regierungsrat, "
    "Stadtrat, Gemeinderat, Conseil d'État, Municipalité, Consiglio di Stato, Municipio) auf einen "
    "parlamentarischen Vorstoss (Motion, Postulat, Interpellation, Anfrage oder Frage)?\n"
    "A = ja: Das Dokument enthält die Antwort oder Stellungnahme der Exekutive. Es kann zusätzlich den Text des "
    "Vorstosses oder einzelne Fragen wiederholen.\n"
    "B = nein: Das Dokument enthält keine Antwort der Exekutive, zum Beispiel nur den eingereichten Vorstoss.\n"
    "Antworte nur mit dem Buchstaben.")
Q_R2_AUTHOR = (
    "Frage: Wer hat den Haupttext dieses Dokuments verfasst?\n"
    "A = die Exekutive (Regierung, Regierungsrat, Stadtrat, Gemeinderat, Conseil d'État, Municipalité, "
    "Consiglio di Stato, Municipio): eine Antwort oder Stellungnahme auf einen Vorstoss, auch wenn sie den "
    "Vorstoss wiederholt.\n"
    "B = Mitglieder des Parlaments oder andere Einreichende: nur der eingereichte Vorstoss (Motion, Postulat, "
    "Interpellation, Anfrage oder Frage), ohne Antwort.\n"
    "Antworte nur mit dem Buchstaben.")

LETTERS_DE = {"prefix": "Antwort:", "choices": (" A", " B")}

VARIANTS: dict[str, dict[str, dict]] = {
    "r1": {
        "r1_v1_i95_de": {"shots": None, "lang": {"*": {"question": Q_R1_DE, **LETTERS_DE}}},
        "r1_v2_words_lang": {"shots": None, "lang": {
            "de": {"question": "Frage: Empfiehlt die Exekutive (Regierung, Regierungsrat, Stadtrat oder Gemeinderat) "
                               "dem Parlament, diesen Vorstoss (Motion oder Postulat) anzunehmen oder abzulehnen? "
                               "Antworte mit «dafür» (Annahme, Überweisung, Erheblicherklärung) oder «dagegen» "
                               "(Ablehnung, Nichtüberweisung, Nichterheblicherklärung).",
                   "prefix": "Antwort:", "choices": (" dafür", " dagegen")},
            "fr": {"question": "Question : L'exécutif (Conseil d'État, Conseil communal, Municipalité ou Conseil "
                               "administratif) recommande-t-il au parlement d'accepter ou de rejeter cette "
                               "intervention (motion ou postulat) ? Réponds par « pour » (accepter, prendre en "
                               "considération, transmettre) ou « contre » (rejeter, refuser, ne pas prendre en "
                               "considération).",
                   "prefix": "Réponse :", "choices": (" pour", " contre")},
            "it": {"question": "Domanda: L'esecutivo (Consiglio di Stato o Municipio) raccomanda al parlamento di "
                               "accogliere o di respingere questo atto parlamentare (mozione o postulato)? Rispondi "
                               "con «favorevole» (accogliere, accettare) o «contrario» (respingere, non accogliere).",
                   "prefix": "Risposta:", "choices": (" favorevole", " contrario")}}},
        "r1_v3_i95_en": {"shots": None, "lang": {"*": {"question": Q_R1_EN, "prefix": "Answer:",
                                                       "choices": (" A", " B")}}},
        "r1_v4_fewshot_de": {"shots": "r1", "lang": {"*": {"question": Q_R1_DE, **LETTERS_DE}}},
    },
    "r2": {
        "r2_v1_de": {"shots": None, "lang": {"*": {"question": Q_R2_DE, **LETTERS_DE}}},
        "r2_v2_words_lang": {"shots": None, "lang": {
            "de": {"question": "Frage: Enthält dieses Dokument eine Antwort oder Stellungnahme der Exekutive "
                               "(Regierung, Regierungsrat, Stadtrat oder Gemeinderat) auf einen parlamentarischen "
                               "Vorstoss? Antworte mit ja oder nein.",
                   "prefix": "Antwort:", "choices": (" ja", " nein")},
            "fr": {"question": "Question : Ce document contient-il une réponse ou une prise de position de l'exécutif "
                               "(Conseil d'État, Conseil communal, Municipalité ou Conseil administratif) à une "
                               "intervention parlementaire ? Réponds par oui ou non.",
                   "prefix": "Réponse :", "choices": (" oui", " non")},
            "it": {"question": "Domanda: Questo documento contiene una risposta o una presa di posizione "
                               "dell'esecutivo (Consiglio di Stato o Municipio) a un atto parlamentare? Rispondi "
                               "con sì o no.",
                   "prefix": "Risposta:", "choices": (" sì", " no")}}},
        "r2_v3_author_de": {"shots": None, "lang": {"*": {"question": Q_R2_AUTHOR, **LETTERS_DE}}},
        "r2_v4_fewshot_de": {"shots": "r2", "lang": {"*": {"question": Q_R2_DE, **LETTERS_DE}}},
    },
}

# (example doc_id, source label, alternate doc_id): dev design documents, chosen on dev (short documents
# that state the value: R1 against = a 261 letter with "lehnt ... ab", R1 for = a 1059 statement with
# "Antrag des Stadtrates: Überweisung"; R2 yes = a 351 response, R2 no = a 230 proposal).
SHOTS = {
    "r1": (("384894", "recommended_against", "9774"), ("888691", "recommended_for", "888160")),
    "r2": (("651843", "yes", "394092"), ("329791", "no", "559045")),
}

# S1 answer marks (copied from src/m03_sub_s1_role.py, version s1-role-1; that file is not changed)
RX_ANSWER = re.compile(r"\b(?:antwort|beantwortung|stellungnahme|r[ée]ponses?|risposta|r\s?i\s?s\s?p\s?o\s?s\s?t\s?a|"
                       r"pr[ée]avis|prise de position|presa di posizione)\b", re.I)
RX_ANSWER_START = re.compile(r"^(?:[\dIVX]{1,4}[.)]\s*|[A-Z]\)\s*)?" + RX_ANSWER.pattern, re.I)
RX_CONSULT = re.compile(r"stellungnahme\s+(?:zu[mr]?|des\s+datenschutz)\b(?!\s+(?:den\s+)?(?:antrag|vorstoss|motion|"
                        r"postulat|interpellation|anfrage))", re.I)


# ---------------------------------------------------------------- small helpers

def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha256_json(x) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def code_sha() -> str:
    return sha256_file(Path(__file__))


def model_fingerprint() -> str:
    """SHA-256 of the small model files and of the names and sizes of the weight files (no 16 GB read)."""
    h = hashlib.sha256()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                 "model.safetensors.index.json"):
        p = cd.MODEL_DIR / name
        if p.exists():
            h.update(name.encode() + b"\0" + p.read_bytes())
    for p in sorted(cd.MODEL_DIR.glob("*.safetensors")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    return "apertus-v1.5-8b-text-bf16:" + h.hexdigest()


def network_guard() -> None:
    """Refuse each socket connection of this process (except Unix sockets): no network request."""
    orig = socket.socket.connect

    def deny(self, addr, *a, **k):
        if self.family == getattr(socket, "AF_UNIX", None):
            return orig(self, addr, *a, **k)
        raise RuntimeError(f"m05_cls_apertus: network connection refused ({addr})")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = lambda *a, **k: deny(socket.socket(), a[0] if a else None)


def docling_running() -> list[str]:
    p = subprocess.run(["pgrep", "-fl", "docling"], capture_output=True, text=True)
    return [x for x in p.stdout.splitlines() if "pgrep" not in x]


_TOK = None


def tokenizer():
    global _TOK
    if _TOK is None:
        from mlx_lm.utils import load_tokenizer
        _TOK = load_tokenizer(cd.MODEL_DIR)
    return _TOK


# ---------------------------------------------------------------- prompts

def lang_of(text: str) -> str:
    return cd.language(text)


def spec_for(task: str, variant: str, text: str) -> tuple[str, dict]:
    """(language key, {question, prefix, choices}) of a variant for a document text."""
    lang = VARIANTS[task][variant]["lang"]
    if "*" in lang:
        return "*", lang["*"]
    k = lang_of(text)
    k = k if k in lang else "de"
    return k, lang[k]


def shots_for(task: str, variant: str, doc_id: str) -> list[tuple[str, str]]:
    key = VARIANTS[task][variant]["shots"]
    if not key:
        return []
    return [(alt if str(doc_id) == d else d, lab) for d, lab, alt in SHOTS[key]]


def build(task: str, variant: str, doc_id: str, text: str | None = None) -> dict:
    """Token ids of the prompt (chat template, whole document first, question last, assistant prefix),
    the token ids of the options, the token ids of the example part, and the hashes for the log."""
    tok = tokenizer()
    text = cd.text(doc_id) if text is None else text
    lk, sp = spec_for(task, variant, text)
    shots = shots_for(task, variant, doc_id)
    msgs = [{"role": "system", "content": SYSTEM}]
    for sd, lab in shots:
        st = cd.text(sd)
        _, ss = spec_for(task, variant, st)
        msgs += [{"role": "user", "content": DOC_HEAD + st + SEP + ss["question"]},
                 {"role": "assistant", "content": ss["prefix"] + ss["choices"][OPTIONS[task].index(lab)]}]
    shot_ids = (list(tok.apply_chat_template(msgs, add_generation_prompt=False, enable_thinking=False,
                                             return_dict=False)) if shots else [])
    msgs.append({"role": "user", "content": DOC_HEAD + text + SEP + sp["question"]})
    ids = list(tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, return_dict=False))
    ids += tok.encode(sp["prefix"], add_special_tokens=False)
    if shots:
        assert ids[:len(shot_ids)] == shot_ids, "example part is not a token prefix"
    ch = [tok.encode(c, add_special_tokens=False) for c in sp["choices"]]
    for i, a in enumerate(ch):
        for j, b in enumerate(ch):
            assert i == j or a[:len(b)] != b, f"option {sp['choices'][j]!r} is a token prefix of another option"
    tmpl = {"system": SYSTEM, "doc_head": DOC_HEAD, "sep": SEP, "spec": sp, "lang_key": lk,
            "shots": [[sd, lab] for sd, lab in shots], "options": list(OPTIONS[task])}
    return {"ids": ids, "choice_ids": ch, "shot_ids": shot_ids, "shots": tuple(sd for sd, _ in shots),
            "lang_key": lk, "template_sha256": sha256_json(tmpl), "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "prompt_sha256": sha256_json(ids)}


def cache_key(model_fp: str, ids: list[int], choice_ids: list[list[int]]) -> str:
    return sha256_json({"model": model_fp, "prompt": ids, "choices": choice_ids})


def cache_path(k: str) -> Path:
    return CACHE / k[:2] / f"{k}.json"


def cache_get(k: str) -> dict | None:
    p = cache_path(k)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def cache_put(k: str, v: dict) -> None:
    p = cache_path(k)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.stem}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def constrained(choice_ids: list[list[int]], lps: dict) -> tuple[list[float], float]:
    """Probabilities of the options under the constrained decoder, and the unconstrained mass of the options.
    lps: {token prefix (tuple): {token id: log-probability}} for each node of the option tree."""
    logp, raw = [], []
    for c in choice_ids:
        s, r = 0.0, 0.0
        for j, t in enumerate(c):
            node = tuple(c[:j])
            allowed = sorted({d[j] for d in choice_ids if len(d) > j and tuple(d[:j]) == node})
            la = [lps[node][a] for a in allowed]
            m = max(la)
            z = m + math.log(sum(math.exp(x - m) for x in la))
            s += lps[node][t] - z
            r += lps[node][t]
        logp.append(s)
        raw.append(r)
    m = max(logp)
    e = [math.exp(x - m) for x in logp]
    return [x / sum(e) for x in e], sum(math.exp(x) for x in raw)


# ---------------------------------------------------------------- model

class Engine:
    """The local bf16 model with a KV cache; prefill in chunks; constrained choice readout."""

    def __init__(self):
        from m04_kern import speicher_begrenzen

        self.limits = speicher_begrenzen()
        import mlx.core as mx
        from mlx_lm import load
        from mlx_lm.models.cache import make_prompt_cache, trim_prompt_cache

        self.mx, self.make, self.trim = mx, make_prompt_cache, trim_prompt_cache
        t0 = time.perf_counter()
        self.model, self.tok = load(str(cd.MODEL_DIR))
        self.model.eval()
        mx.eval(self.model.parameters())
        self.load_s = round(time.perf_counter() - t0, 1)
        self.mem_after_load_gb = round(mx.get_active_memory() / 1e9, 2)
        c = self.make(self.model)
        self.model.model(mx.array([list(range(1000, 1064))]), cache=c)
        mx.eval([x.state for x in c])
        del c
        mx.reset_peak_memory()
        self.shot_cache: dict = {}

    def head(self, h):
        m = self.model
        if hasattr(m, "lm_head"):
            return m.lm_head(h)
        return m.model.embed_tokens.as_linear(h)

    def feed(self, cache, ids: list[int], k: int = 0):
        """Feed ids into the cache (chunks of PREFILL_CHUNK). Return the log-probabilities (numpy, float32)
        at the last k positions (k <= length of the last chunk)."""
        mx = self.mx
        out = None
        for s in range(0, len(ids), PREFILL_CHUNK):
            piece = ids[s:s + PREFILL_CHUNK]
            h = self.model.model(mx.array([piece]), cache=cache)
            if k and s + len(piece) >= len(ids):
                assert k <= len(piece)
                lg = self.head(h[0, -k:]).astype(mx.float32)
                lp = lg - mx.logsumexp(lg, axis=-1, keepdims=True)
                mx.eval(lp, [c.state for c in cache])
                import numpy as np
                out = np.array(lp)
            else:
                mx.eval([c.state for c in cache])
        return out

    def score(self, cache, L: int, ids: list[int], choice_ids: list[list[int]]) -> dict:
        """The cache holds ids[:L]. Read the options; the cache is set back to L."""
        suffix = ids[L:]
        assert suffix, "empty suffix"
        lps = {(): self.feed(cache, suffix, 1)[0]}
        for c in choice_ids:
            if len(c) > 1 and any(tuple(c[:j]) not in lps for j in range(1, len(c))):
                lpc = self.feed(cache, c[:-1], len(c) - 1)
                for j in range(1, len(c)):
                    lps[tuple(c[:j])] = lpc[j - 1]
                self.trim(cache, len(c) - 1)
        self.trim(cache, len(suffix))
        small = {node: {int(t): float(v[t]) for t in {d[len(node)] for d in choice_ids
                                                      if len(d) > len(node) and tuple(d[:len(node)]) == node}}
                 for node, v in lps.items()}
        probs, mass = constrained(choice_ids, small)
        return {"probs": probs, "mass": mass}

    def run_group(self, items: list[dict], base_ids: list[int]) -> list[dict]:
        """items: built prompts of one document that share base_ids (the example part, or nothing).
        One prefill to the longest common prefix, then one readout for each item."""
        mx = self.mx
        ids_list = [it["ids"] for it in items]
        L = min(len(x) for x in ids_list) - 1
        for x in ids_list[1:]:
            L = min(L, next((i for i, (a, b) in enumerate(zip(ids_list[0], x)) if a != b), L))
        nb = len(base_ids)
        if nb:
            key = tuple(base_ids)
            if key not in self.shot_cache:
                c = self.make(self.model)
                self.feed(c, base_ids)
                self.shot_cache[key] = c
            cache = self.shot_cache[key]
            assert cache[0].offset == nb
        else:
            cache = self.make(self.model)
        assert L >= nb
        t0 = time.perf_counter()
        self.feed(cache, ids_list[0][nb:L])
        pre_s = time.perf_counter() - t0
        res = []
        for it in items:
            t1 = time.perf_counter()
            r = self.score(cache, L, it["ids"], it["choice_ids"])
            r.update(prefill_tokens=L - nb, prefill_seconds=round(pre_s, 3),
                     readout_seconds=round(time.perf_counter() - t1, 3))
            res.append(r)
        if nb:
            self.trim(cache, L - nb)
        else:
            del cache
        mx.clear_cache()
        return res


# ---------------------------------------------------------------- scoring of a set

def subset_rows(task: str, subset: str, with_excluded: bool = False):
    """Rows of a subset in rank order, without the documents that the protected lists hold NOW
    (m05_cls_data.protected_doc_ids(): the path 1 workflow can add files to daten/gold/final_v4 after the
    data step). R2 check: the first CHECK_R2_N rows by rank after this filter."""
    rs = [r for r in cd.rows(task) if r["split"] == "dev" and r["subset"] == subset] if subset in ("design", "check") \
        else [r for r in cd.rows(task) if r["split"] == "validation" and r["subset"] == "validation"]
    rs.sort(key=lambda r: r["rank"])
    prot = cd.protected_doc_ids()
    excluded = [r for r in rs if r["doc_id"] in prot]
    rs = [r for r in rs if r["doc_id"] not in prot]
    if task == "r2" and subset == "check":
        rs = rs[:CHECK_R2_N]
        excluded = [r for r in excluded if r["rank"] < rs[-1]["rank"]]     # only the rank window of the sample
    excluded = [r["doc_id"] for r in excluded]
    return (rs, excluded) if with_excluded else rs


def score_set(task: str, subset: str, variants: list[str], limit: int | None = None, run: str = "") -> dict:
    """Score the variants on the rows of a subset (cache first; the model loads only if a value is missing).
    Returns {doc_id: {variant: result}} and the run facts."""
    rows_, excluded = subset_rows(task, subset, with_excluded=True)
    rows_ = rows_[:limit] if limit else rows_
    allowed = ("dev",) if subset in ("design", "check") else ("validation",)
    ids_all = [r["doc_id"] for r in rows_]
    cd.assert_allowed(ids_all, allowed)
    shot_docs = {d for v in variants for x in (SHOTS.get(VARIANTS[task][v]["shots"] or "", ())) for d in (x[0], x[2])}
    cd.assert_allowed(sorted(shot_docs), ("dev",))
    if shot_docs:
        design_ids = {r["doc_id"]: r["label"] for r in subset_rows(task, "design")}
        for v in variants:
            for d, lab, alt in SHOTS.get(VARIANTS[task][v]["shots"] or "", ()):
                assert design_ids.get(d) == lab and design_ids.get(alt) == lab, (d, alt, lab)
    mfp = model_fingerprint()
    facts = {"run": run, "task": task, "subset": subset, "variants": variants, "documents": len(rows_),
             "excluded_protected_now": excluded,
             "start": now(), "model": str(cd.MODEL_DIR.relative_to(ROOT)), "model_fingerprint": mfp,
             "precision": "bf16", "code_sha256": code_sha(), "network_guard": True,
             "cache_hits": 0, "model_readouts": 0, "no_readout_length": 0, "prefill_tokens": 0,
             "prefill_seconds": 0.0, "readout_seconds": 0.0}
    # plan: build prompts, look up the cache
    plan = []
    for r in rows_:
        if int(r["n_tokens"]) > MAX_TEXT_TOKENS:
            plan.append((r, None))
            continue
        built = {v: build(task, v, r["doc_id"]) for v in variants}
        for v, b in built.items():
            b["key"] = cache_key(mfp, b["ids"], b["choice_ids"])
            b["hit"] = cache_get(b["key"])
        plan.append((r, built))
    need = sum(1 for _, b in plan if b and any(x["hit"] is None for x in b.values()))
    out: dict = {}
    eng = None
    lock_cm = None
    t_run = time.perf_counter()
    try:
        if need:
            if docling_running():
                raise SystemExit(f"a Docling process runs (process rule 7.4): {docling_running()}")
            network_guard()
            cm = cd.model_lock(f"m05_cls_apertus {run}: {task} {subset} {','.join(variants)}")
            facts["lock"] = cm.__enter__()
            lock_cm = cm
            eng = Engine()
            facts.update(model_load_seconds=eng.load_s, memory_after_load_gb=eng.mem_after_load_gb,
                         memory_limits=eng.limits)
        done = 0
        for r, built in plan:
            d = r["doc_id"]
            out[d] = {}
            if built is None:
                facts["no_readout_length"] += 1
                for v in variants:
                    out[d][v] = {"no_readout": "length", "n_text_tokens": int(r["n_tokens"])}
                continue
            groups = collections.defaultdict(list)
            for v, b in built.items():
                if b["hit"] is not None:
                    facts["cache_hits"] += 1
                    continue
                groups[b["shots"]].append((v, b))
            for shots, items in groups.items():
                base = items[0][1]["shot_ids"]
                res = eng.run_group([b for _, b in items], base)
                facts["prefill_tokens"] += res[0]["prefill_tokens"]
                facts["prefill_seconds"] += res[0]["prefill_seconds"]
                for (v, b), x in zip(items, res):
                    facts["model_readouts"] += 1
                    facts["readout_seconds"] += x["readout_seconds"]
                    val = {"key": b["key"], "model_fingerprint": mfp, "prompt_sha256": b["prompt_sha256"],
                           "n_prompt_tokens": len(b["ids"]), "choice_ids": b["choice_ids"],
                           "probs": [round(p, 6) for p in x["probs"]], "mass": round(x["mass"], 6),
                           "prefill_tokens": x["prefill_tokens"], "prefill_seconds": x["prefill_seconds"],
                           "readout_seconds": x["readout_seconds"], "made": now(), "version": VERSION}
                    cache_put(b["key"], val)
                    b["hit"] = val
                    b["fresh"] = True
            for v, b in built.items():
                x = b["hit"]
                out[d][v] = {"p": x["probs"][0], "probs": x["probs"], "mass": x["mass"],
                             "prompt_sha256": b["prompt_sha256"], "template_sha256": b["template_sha256"],
                             "text_sha256": b["text_sha256"], "n_prompt_tokens": len(b["ids"]),
                             "lang_key": b["lang_key"], "shots": list(b["shots"]), "cache_key": b["key"]}
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                        "run": run, "task": task, "subset": subset, "doc_id": d, "variant": v,
                                        "cache_hit": not b.get("fresh", False), **{k: out[d][v][k] for k in (
                                            "p", "mass", "prompt_sha256", "template_sha256", "text_sha256",
                                            "n_prompt_tokens", "cache_key")}}, ensure_ascii=False) + "\n")
            done += 1
            if eng and done % DOCLING_CHECK_EVERY == 0:
                if docling_running():
                    raise SystemExit("a Docling process started: run stopped (process rule 7.4); "
                                     "the cache keeps the values, a new run continues")
                print(f"{task} {subset}: {done}/{len(plan)} documents, {round(time.perf_counter() - t_run)} s",
                      flush=True)
        if eng:
            facts["peak_memory_gb"] = round(eng.mx.get_peak_memory() / 1e9, 2)
    finally:
        if lock_cm is not None:
            lock_cm.__exit__(None, None, None)
        facts["end"] = now()
        facts["seconds"] = round(time.perf_counter() - t_run, 1)
        facts["prefill_seconds"] = round(facts["prefill_seconds"], 1)
        facts["readout_seconds"] = round(facts["readout_seconds"], 1)
        OUT.mkdir(parents=True, exist_ok=True)
        with open(RUNS, "a", encoding="utf-8") as f:
            f.write(json.dumps(facts, ensure_ascii=False) + "\n")
    return {"scores": out, "facts": facts}


# ---------------------------------------------------------------- baselines and metrics

def baseline_preds(task: str, rows_: list[dict]) -> dict[str, dict[str, str]]:
    out = {"majority": {}}
    if task == "r1":
        out["keyword"] = {}
        out["keyword_answered"] = {}
    else:
        out["heading"] = {}
        out["s1_answer"] = {}
    for r in rows_:
        d = r["doc_id"]
        t = cd.text(d)
        out["majority"][d] = MAJORITY[task]
        if task == "r1":
            ms = list(cd.RX_REC.finditer(t))
            p = None if not ms else ("recommended_against" if ms[-1].group("against") else "recommended_for")
            out["keyword"][d] = p or "recommended_against"
            out["keyword_answered"][d] = p
        else:
            out["heading"][d] = "yes" if cd.RX_EXEC_RESPONSE.search(t[:3000]) else "no"
            hit = any(len(x.strip()) <= 90 and RX_ANSWER_START.match(x.strip()) and not RX_CONSULT.search(x)
                      for x in t.splitlines() if x.strip())
            out["s1_answer"][d] = "yes" if hit else "no"
    return out


def jeffreys(k: int, n: int) -> float | None:
    if n == 0:
        return None
    from scipy.stats import beta
    return float(beta.ppf(0.05, k + 0.5, n - k + 0.5))


def metrics(task: str, rows_: list[dict], pred: dict[str, str | None], p: dict[str, float | None] | None = None,
            a: float | None = None) -> dict:
    """Values of a prediction (None = no readout: wrong and unsure). Only rows with a value in pred."""
    opts = OPTIONS[task]
    rs = [r for r in rows_ if r["doc_id"] in pred]
    n = len(rs)
    y = [r["label"] for r in rs]
    yh = [pred[r["doc_id"]] for r in rs]
    k = sum(a_ == b_ for a_, b_ in zip(y, yh))
    m: dict = {"n": n, "correct": k, "accuracy": round(k / n, 4) if n else None, "accuracy_jeffreys": jeffreys(k, n),
               "no_readout": sum(x is None for x in yh)}
    f1s, recs = [], []
    for o in opts:
        tp = sum(1 for a_, b_ in zip(y, yh) if a_ == o and b_ == o)
        n_o = sum(1 for a_ in y if a_ == o)
        pp = sum(1 for b_ in yh if b_ == o)
        rec = tp / n_o if n_o else None
        prec = tp / pp if pp else None
        f1 = (2 * prec * rec / (prec + rec) if prec and rec else 0.0) if n_o else None
        m[f"n_{o}"] = n_o
        m[f"recall_{o}"] = round(rec, 4) if rec is not None else None
        m[f"recall_{o}_jeffreys"] = jeffreys(tp, n_o)
        m[f"precision_{o}"] = round(prec, 4) if prec is not None else None
        m[f"f1_{o}"] = round(f1, 4) if f1 is not None else None
        if f1 is not None:
            f1s.append(f1)
        if rec is not None:
            recs.append(rec)
    m["macro_f1"] = round(sum(f1s) / len(f1s), 4) if len(f1s) == 2 else None
    m["balanced_accuracy"] = round(sum(recs) / len(recs), 4) if len(recs) == 2 else None
    m["confusion"] = dict(collections.Counter(f"{a_}->{b_}" for a_, b_ in zip(y, yh)))
    maj = max(collections.Counter(y).values()) / n if n else None
    m["majority_share"] = round(maj, 4) if maj is not None else None
    if p is not None and a is not None:
        cert = [r for r in rs if p.get(r["doc_id"]) is not None and max(p[r["doc_id"]], 1 - p[r["doc_id"]]) >= a]
        m["a"] = a
        m["coverage"] = round(len(cert) / n, 4) if n else None
        sub = {r["doc_id"]: pred[r["doc_id"]] for r in cert}
        mc = metrics(task, cert, sub) if cert else {"accuracy": None, "balanced_accuracy": None, "n": 0}
        m["certain_n"] = len(cert)
        m["certain_accuracy"] = mc["accuracy"]
        m["certain_accuracy_jeffreys"] = mc.get("accuracy_jeffreys")
        m["certain_balanced_accuracy"] = mc["balanced_accuracy"]
        for o in opts:
            n_o = sum(1 for r in rs if r["label"] == o)
            m[f"coverage_{o}"] = round(sum(1 for r in cert if r["label"] == o) / n_o, 4) if n_o else None
    return m


def decide(task: str, p: dict[str, float | None], t: float) -> dict[str, str | None]:
    o = OPTIONS[task]
    return {d: (None if x is None else (o[0] if x >= t else o[1])) for d, x in p.items()}


def ece(task: str, rows_: list[dict], p: dict[str, float | None], bins: int = 10) -> float | None:
    """Expected calibration error of p (probability of the first option) against the source label."""
    xs = [(p[r["doc_id"]], 1.0 if r["label"] == OPTIONS[task][0] else 0.0) for r in rows_ if p.get(r["doc_id"]) is not None]
    if not xs:
        return None
    tot = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        g = [(q, y) for q, y in xs if (lo <= q < hi) or (b == bins - 1 and q == 1.0)]
        if g:
            tot += len(g) / len(xs) * abs(sum(q for q, _ in g) / len(g) - sum(y for _, y in g) / len(g))
    return round(tot, 4)


def breakdown(task: str, rows_: list[dict], pred: dict, key: str) -> dict:
    g = collections.defaultdict(list)
    for r in rows_:
        g[r[key]].append(r)
    return {k: {x: metrics(task, v, pred)[x] for x in ("n", "correct", "accuracy", "accuracy_jeffreys",
                                                         f"recall_{OPTIONS[task][0]}", f"recall_{OPTIONS[task][1]}")}
            for k, v in sorted(g.items())}


def bootstrap_diff(task: str, rows_: list[dict], pred_a: dict, pred_b: dict, n: int = BOOT_N,
                   seed: int = BOOT_SEED) -> dict:
    """Paired bootstrap of (value of a) - (value of b): accuracy for R1, balanced accuracy for R2."""
    import numpy as np
    opts = OPTIONS[task]
    y = np.array([1 if r["label"] == opts[0] else 0 for r in rows_])
    ca = np.array([pred_a[r["doc_id"]] == r["label"] for r in rows_], dtype=float)
    cb = np.array([pred_b[r["doc_id"]] == r["label"] for r in rows_], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(rows_), size=(n, len(rows_)))
    if task == "r1":
        d = ca[idx].mean(1) - cb[idx].mean(1)
        point = ca.mean() - cb.mean()
    else:
        yy = y[idx]

        def bal(c):
            cc = c[idx]
            r1 = (cc * yy).sum(1) / np.maximum(yy.sum(1), 1)
            r0 = (cc * (1 - yy)).sum(1) / np.maximum((1 - yy).sum(1), 1)
            return (r1 + r0) / 2
        d = bal(ca) - bal(cb)
        rec = lambda c, v: c[y == v].mean()  # noqa: E731
        point = (rec(ca, 1) + rec(ca, 0)) / 2 - (rec(cb, 1) + rec(cb, 0)) / 2
    return {"value": PRIMARY[task] if task == "r2" else "accuracy", "point": round(float(point), 4),
            "bound_5pct": round(float(np.quantile(d, 0.05)), 4), "resamples": n, "seed": seed}


# ---------------------------------------------------------------- commands

def scores_path(task: str, subset: str) -> Path:
    return OUT / f"{subset}_scores_{task}.json"


def cmd_design(tasks: list[str], limit: int | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        vs = list(VARIANTS[task])
        res = score_set(task, "design", vs, limit=limit, run=f"design-{task}")
        if limit:
            print(json.dumps(res["facts"], indent=1, ensure_ascii=False))
            continue
        scores_path(task, "design").write_text(json.dumps({"task": task, "subset": "design", "variants": vs,
                                                           "facts": res["facts"], "scores": res["scores"]},
                                                          ensure_ascii=False, indent=0), encoding="utf-8")
        print(json.dumps(res["facts"], indent=1, ensure_ascii=False))


def evaluate_variant(task: str, rows_: list[dict], scores: dict, v: str, t: float, a: float | None) -> dict:
    p = {d: (s[v].get("p")) for d, s in scores.items()}
    pred = decide(task, p, t)
    m = metrics(task, rows_, pred, p, a)
    m["t"] = t
    m["ece"] = ece(task, rows_, p)
    masses = [s[v]["mass"] for s in scores.values() if s[v].get("mass") is not None]
    m["option_mass_min"] = round(min(masses), 4) if masses else None
    m["option_mass_mean"] = round(sum(masses) / len(masses), 4) if masses else None
    return m


def choose_t(task: str, rows_: list[dict], p: dict) -> tuple[float, dict]:
    prim = PRIMARY[task]
    vals = {t: metrics(task, rows_, decide(task, p, t))[prim] or 0.0 for t in T_GRID}
    best = max(vals.values())
    tstar = min((t for t in T_GRID if vals[t] == best), key=lambda t: (abs(t - 0.5), t))
    t = tstar if vals[tstar] - vals[0.5] >= T_MIN_GAIN - 1e-9 else 0.5
    return t, {"grid": vals, "t_star": tstar, "chosen": t}


def choose_a(task: str, rows_: list[dict], p: dict, t: float) -> tuple[float | None, dict]:
    pred = decide(task, p, t)
    tab = {}
    chosen = None
    for a in A_GRID:
        m = metrics(task, rows_, pred, p, a)
        acc = m["certain_accuracy"] if task == "r1" else m["certain_balanced_accuracy"]
        cov_ok = (m["coverage"] or 0) >= A_MIN_COVERAGE if task == "r1" else all(
            (m[f"coverage_{o}"] or 0) >= A_MIN_COVERAGE for o in OPTIONS[task])
        ok = acc is not None and acc >= A_MIN_ACC and cov_ok
        tab[a] = {"coverage": m["coverage"], **{f"coverage_{o}": m[f"coverage_{o}"] for o in OPTIONS[task]},
                  "certain_n": m["certain_n"], "certain_value": acc, "meets": ok}
        if ok and chosen is None:
            chosen = a
    return chosen, tab


def cmd_choose() -> None:
    """Selection on dev design (rules of chapter 4), freeze in daten/cls/design_choice.json."""
    result = {"made": now(), "version": VERSION, "code_sha256": code_sha(),
              "data_code_sha256": sha256_file(ROOT / "src/m05_cls_data.py"),
              "model": str(cd.MODEL_DIR.relative_to(ROOT)), "model_fingerprint": model_fingerprint(),
              "precision": "bf16", "rules": {
                  "primary": PRIMARY, "tie": TIE, "t_grid": T_GRID, "t_min_gain": T_MIN_GAIN, "a_grid": A_GRID,
                  "a_min_value": A_MIN_ACC, "a_min_coverage": A_MIN_COVERAGE,
                  "order_on_tie": "fewer prefills (zero-shot before few-shot), higher accuracy, lower variant number"},
              "inputs": {}, "tasks": {}}
    allm = {"made": result["made"], "code_sha256": result["code_sha256"], "tasks": {}}
    for task in ("r1", "r2"):
        sp = scores_path(task, "design")
        sj = json.loads(sp.read_text(encoding="utf-8"))
        result["inputs"][str(sp.relative_to(ROOT))] = sha256_file(sp)
        rows_ = subset_rows(task, "design")
        assert {r["doc_id"] for r in rows_} <= set(sj["scores"]), "design scores do not cover the design set"
        scores = {r["doc_id"]: sj["scores"][r["doc_id"]] for r in rows_}
        tab = {}
        for v in VARIANTS[task]:
            tab[v] = evaluate_variant(task, rows_, scores, v, 0.5, None)
        prim = PRIMARY[task]
        best = max(tab[v][prim] or 0 for v in tab)
        order = list(VARIANTS[task])
        equal = [v for v in order if (tab[v][prim] or 0) >= best - TIE - 1e-12]
        win = min(equal, key=lambda v: (1 if VARIANTS[task][v]["shots"] else 0, -(tab[v]["accuracy"] or 0),
                                        order.index(v)))
        p = {d: s[win].get("p") for d, s in scores.items()}
        t, t_tab = choose_t(task, rows_, p)
        a, a_tab = choose_a(task, rows_, p, t)
        chosen_m = evaluate_variant(task, rows_, scores, win, t, a)
        chosen_m["by_body"] = breakdown(task, rows_, decide(task, p, t), "body_key")
        chosen_m["by_language"] = breakdown(task, rows_, decide(task, p, t), "language")
        base = baseline_preds(task, rows_)
        bm = {}
        for name, pred in base.items():
            if name == "keyword_answered":
                ans = {d: x for d, x in pred.items() if x is not None}
                bm[name] = metrics(task, [r for r in rows_ if r["doc_id"] in ans], ans)
                bm[name]["coverage"] = round(len(ans) / len(rows_), 4)
                bm["method_on_keyword_answered"] = metrics(task, [r for r in rows_ if r["doc_id"] in ans],
                                                           {d: decide(task, p, t)[d] for d in ans})
            else:
                bm[name] = metrics(task, rows_, pred)
                bm[name]["by_body"] = breakdown(task, rows_, pred, "body_key")
        for v in tab:
            tab[v]["by_body"] = breakdown(task, rows_, decide(task, {d: s[v].get("p") for d, s in scores.items()}, 0.5),
                                          "body_key")
        tmpl = VARIANTS[task][win]
        shots = []
        if tmpl["shots"]:
            shots = [{"doc_id": d, "label": lab, "alternate": alt} for d, lab, alt in SHOTS[tmpl["shots"]]]
        result["tasks"][task] = {
            "variant": win, "t": t, "a": a,
            "template": {"system": SYSTEM, "user": "Dokument:\\n{document text}\\n\\n{question}",
                         "doc_head": DOC_HEAD, "sep": SEP, "assistant_prefix_then_option": True,
                         "lang": {k: {"question": x["question"], "prefix": x["prefix"], "choices": list(x["choices"])}
                                  for k, x in tmpl["lang"].items()},
                         "language_rule": "m05_cls_data.language(text); a key not in lang gives de"
                         if "*" not in tmpl["lang"] else "one wording for all languages",
                         "options_in_order": list(OPTIONS[task]), "shots": shots,
                         "chat_template": "tokenizer chat template of the model, enable_thinking=False, "
                                          "add_generation_prompt=True, then the assistant prefix tokens"},
            "template_sha256": sha256_json({k: tmpl[k] for k in ("shots", "lang")} | {"system": SYSTEM,
                                                                                         "doc_head": DOC_HEAD,
                                                                                         "sep": SEP}),
            "design_values_chosen": {k: chosen_m[k] for k in ("n", "accuracy", "accuracy_jeffreys", "macro_f1",
                                                             "balanced_accuracy", "coverage", "certain_accuracy",
                                                             "certain_balanced_accuracy") if k in chosen_m},
        }
        allm["tasks"][task] = {"variants_t05": tab, "chosen": win, "chosen_values": chosen_m, "t_selection": t_tab,
                               "a_selection": {str(k): v for k, v in a_tab.items()}, "baselines": bm,
                               "rows": len(rows_), "labels": dict(collections.Counter(r["label"] for r in rows_))}
    (OUT / "design_metrics.json").write_text(json.dumps(allm, indent=1, ensure_ascii=False), encoding="utf-8")
    result["inputs"]["daten/cls/apertus/design_metrics.json"] = sha256_file(OUT / "design_metrics.json")
    for name in ("r1_dataset.csv", "r2_dataset.csv"):
        result["inputs"][f"daten/cls/{name}"] = sha256_file(cd.OUT / name)
    CHOICE_FILE.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({t: {k: result["tasks"][t][k] for k in ("variant", "t", "a", "design_values_chosen")}
                      for t in result["tasks"]}, indent=1, ensure_ascii=False))
    print("frozen:", CHOICE_FILE, sha256_file(CHOICE_FILE))


def cmd_check(tasks: list[str]) -> None:
    """One run of the frozen variant on the dev check set; values with the baselines."""
    ch = json.loads(CHOICE_FILE.read_text(encoding="utf-8"))
    if ch["code_sha256"] != code_sha():
        raise SystemExit("the code changed after the freeze: check refused")
    mpath = OUT / "check_metrics.json"
    allm = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"tasks": {}}
    for task in tasks:
        if task in allm["tasks"]:
            raise SystemExit(f"{task}: the check values exist (one check run only)")
        c = ch["tasks"][task]
        v, t, a = c["variant"], c["t"], c["a"]
        res = score_set(task, "check", [v], run=f"check-{task}")
        rows_ = subset_rows(task, "check")
        assert {r["doc_id"] for r in rows_} <= set(res["scores"])
        scores = {r["doc_id"]: res["scores"][r["doc_id"]] for r in rows_}
        p = {d: s[v].get("p") for d, s in scores.items()}
        pred = decide(task, p, t)
        m = evaluate_variant(task, rows_, scores, v, t, a)
        for key in ("body_key", "language", "length_class", "text_source"):
            m[f"by_{key}"] = breakdown(task, rows_, pred, key)
        base = baseline_preds(task, rows_)
        bm = {}
        for name, bp in base.items():
            if name == "keyword_answered":
                ans = {d: x for d, x in bp.items() if x is not None}
                rr = [r for r in rows_ if r["doc_id"] in ans]
                bm[name] = metrics(task, rr, ans)
                bm[name]["coverage"] = round(len(ans) / len(rows_), 4)
                bm["method_on_keyword_answered"] = metrics(task, rr, {d: pred[d] for d in ans})
            else:
                bm[name] = metrics(task, rows_, bp)
                bm[name]["by_body"] = breakdown(task, rows_, bp, "body_key")
        rule = "keyword" if task == "r1" else "heading"
        boot = {f"method_minus_{rule}": bootstrap_diff(task, rows_, pred, base[rule]),
                "method_minus_majority": bootstrap_diff(task, rows_, pred, base["majority"])}
        sp = scores_path(task, "check")
        sp.write_text(json.dumps({"task": task, "subset": "check", "variants": [v], "facts": res["facts"],
                                  "scores": scores}, ensure_ascii=False, indent=0), encoding="utf-8")
        allm["tasks"][task] = {"variant": v, "t": t, "a": a, "values": m, "baselines": bm, "bootstrap": boot,
                               "rows": len(rows_), "labels": dict(collections.Counter(r["label"] for r in rows_)),
                               "facts": res["facts"], "scores_sha256": sha256_file(sp),
                               "design_choice_sha256": sha256_file(CHOICE_FILE)}
        allm["code_sha256"] = code_sha()
        mpath.write_text(json.dumps(allm, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({task: {k: m.get(k) for k in ("n", "accuracy", "accuracy_jeffreys", "macro_f1",
                                                        "balanced_accuracy", "coverage", "certain_accuracy")}},
                         indent=1))


def cmd_show(task: str, variant: str, doc_id: str) -> None:
    cd.assert_allowed([doc_id], ("dev",))
    b = build(task, variant, doc_id)
    print(tokenizer().decode(b["ids"]))
    print("options:", b["choice_ids"], "tokens:", len(b["ids"]), "prompt sha256:", b["prompt_sha256"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["design", "choose", "check", "show-prompt"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--task", choices=["r1", "r2"])
    ap.add_argument("--limit", type=int)
    x = ap.parse_args()
    tasks = [x.task] if x.task else ["r1", "r2"]
    if x.cmd == "design":
        cmd_design(tasks, x.limit)
    elif x.cmd == "choose":
        cmd_choose()
    elif x.cmd == "check":
        cmd_check(tasks)
    else:
        cmd_show(*x.args)


if __name__ == "__main__":
    main()

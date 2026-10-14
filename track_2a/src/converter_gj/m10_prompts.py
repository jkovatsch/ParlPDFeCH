# SPDX-License-Identifier: Apache-2.0
"""Gate GJ (status EXCEPTION), plan chapters 3.1, 3.3, 3.4 and 3.6: the prompt jobs of interface 5 for the VM.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), stream B,
for the AI agent; the special token check (special_texts(), SpecialFinder, item_special_texts()): stream D of
workflow <id> (wave 3). This file does not change an existing file. It writes only under
daten/gj/jobs/. It does not load a model. It loads only the tokenizer files of the local model (chat template check,
token counts, special token texts).

1 Layout (plan 3.1, E18, JEV)
  prefix  = chat template text up to the end of the document part:
            CHAT_HEAD (BOS, the frozen system text of the R2 path, the developer part of the Apertus template with
            deliberation and tools disabled, the start of the user turn) + DOC_HEAD "Dokument:\\n" + one line for
            each Docling block in reading order, joined by "\\n":
            "[B<n> | S.<page> | <Docling label>] <block text>"
            The block text is the Docling text with its line breaks replaced by one space (the lines are stripped,
            empty lines are left out). A block without text gives "[B<n> | S.<page> | <Docling label>]".
            Furniture stays in. Nothing is cut. The prefix ends with SEP "\\n\\n", so that the token ids of
            tokens(prefix) + tokens(suffix) equal the ids of the joined text (AI agent, 12.10.2026: with SEP at
            the start of the suffix, 406 of 2,670 documents had other ids at the first suffix token).
  suffix  = the question with lettered options + CHAT_TAIL (end of the user turn, start of the assistant
            turn) + "Antwort:" (the assistant prefix of the R2 path).
  One suffix for the document step D1 (id "D1") and one for each block (id "B<n>", step B1), in this order.
  Token ids on the VM = tokens(prefix) + tokens(suffix), both with add_special_tokens=False (the prefix text
  holds the BOS text and the special token texts). Training and inference use the same code path.
  The system text, DOC_HEAD, SEP and "Antwort:" are imported from src/m05_cls_apertus.py (frozen R2 path,
  template r2_v1_de). CHAT_HEAD and CHAT_TAIL are checked against the chat template of the local model
  (transformers apply_chat_template, tokenize=False) before each build.

2 Questions (German, plan 3.3 and 3.4)
  D1  "Welche Textteile nach eCH-0295 enthält das Dokument?" A nur den eingereichten Text (mit oder ohne
      Begründung), B nur die Antwort der Exekutive (mit oder ohne Antrag), C beides, D keinen dieser Textteile.
  B1  "Zu welchem Teil nach eCH-0295 gehört Block [B<n>] auf Seite <p>, der mit «<erste 12 Wörter>» beginnt?"
      A eingereichter Text (submitted), B Begründung (reasoning), C Antwort der Exekutive (response), D Antrag der
      Exekutive (recommendation), E Titel (title), F kein Textteil (none). The first 12 words are the first 12
      whitespace-separated words of the block text, joined by one space; a block without words gives
      «(ohne Text)».
  Frame of a question (as the R2 question): "Frage: <question>\\n<letter> = <option text>\\n...\\nAntworte nur mit
  dem Buchstaben."
  The template SHA-256 is the SHA-256 of the canonical JSON (sort_keys, no spaces) of template.json without
  the key sha256.

3 Jobs (daten/gj/jobs/<job>/template.json and items.jsonl; run record daten/gj/jobs/<job>.build.json)
  gpu1_labelled  the 294 AI-reference documents of daten/gj/sets.json (dev, validation, group7)
  gpu2_bulk      all other documents of daten/gj/docs (no test document; guard first)
  gpu0_smoke     5 documents: the dev document with the most prefix tokens up to 32,768 (memory, plan 11 item 6),
                 the labelled document with the most prefix tokens (plan 3.6), and the 3 dev pilots; never group 7.
                 Note: the longest labelled document is a validation document, thus the smoke is not dev only.
  A document with more than 32,768 prefix tokens stays in its job; the record lists it (the VM gives it no states).
  Token estimates: characters / 3.69 (plan 3.6 note 1). With --count-tokens: exact counts with the tokenizer of
  the local model (tokenizers library, CPU).

Usage:
  uv run --offline --frozen --no-sync python src/m10_prompts.py template
  uv run --offline --frozen --no-sync python src/m10_prompts.py build --job all [--count-tokens]
  uv run --offline --frozen --no-sync python src/m10_prompts.py check --job all
  The command check builds the items again in memory (no file is written) and compares their SHA-256 with
  items.jsonl and the build record. Information: the count of the documents whose items hold the text of a special
  token outside the frame (tokenizer.json added tokens with special true, and all_special_tokens).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import functools
import hashlib
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m05_cls_apertus as r2  # noqa: E402
import m10_docs as docs  # noqa: E402
import m10_guard as guard  # noqa: E402

VERSION = "m10-prompts-1"
ROOT = guard.ROOT
JOBS = docs.GJ / "jobs"
SETS = docs.GJ / "sets.json"
MODEL_DIR = ROOT / "daten/modelle/apertus-v1.5-8b-text-bf16"
CHARS_PER_TOKEN = 3.69
MAX_TOKENS = 32768
TEMPLATE_ID = "gj_jev_v1_de"
SYSTEM = r2.SYSTEM
DOC_HEAD = r2.DOC_HEAD
SEP = r2.SEP
ANSWER_PREFIX = r2.LETTERS_DE["prefix"]
CHAT_HEAD = ("<s><|system_start|>" + SYSTEM + "<|system_end|><|developer_start|>Deliberation: disabled\n"
             "Tool Capabilities: disabled<|developer_end|><|user_start|>")
CHAT_TAIL = "<|user_end|><|assistant_start|>"
LINE_FORMAT = "[B<n> | S.<page> | <Docling label>] <block text>"
FIRST_WORDS = 12
NO_TEXT = "(ohne Text)"
D1_QUESTION = "Welche Textteile nach eCH-0295 enthält das Dokument?"
D1_OPTIONS = (("A", "A", "nur den eingereichten Text (mit oder ohne Begründung)"),
              ("B", "B", "nur die Antwort der Exekutive (mit oder ohne Antrag)"),
              ("C", "C", "beides"),
              ("D", "D", "keinen dieser Textteile"))
B1_QUESTION = "Zu welchem Teil nach eCH-0295 gehört Block [{block}] auf Seite {page}, der mit «{first_words}» beginnt?"
B1_OPTIONS = (("A", "submitted", "eingereichter Text"),
              ("B", "reasoning", "Begründung"),
              ("C", "response", "Antwort der Exekutive"),
              ("D", "recommendation", "Antrag der Exekutive"),
              ("E", "title", "Titel"),
              ("F", "none", "kein Textteil"))
ANSWER_LINE = "Antworte nur mit dem Buchstaben."
JOB_NAMES = ("gpu0_smoke", "gpu1_labelled", "gpu2_bulk")
SMOKE_PILOTS = ("879163", "375917", "549658")
SPLIT_CHECK_MAX = 60


# ---------------------------------------------------------------- template

def question_text(question: str, options) -> str:
    return "Frage: " + question + "\n" + "\n".join(f"{l} = {t}" for l, _, t in options) + "\n" + ANSWER_LINE


def sha256_json(x) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def template() -> dict:
    src = Path(r2.__file__)
    ct = MODEL_DIR / "chat_template.jinja"
    t = {
        "template_id": TEMPLATE_ID,
        "system_text_source": {
            "file": guard.rel(src), "file_sha256": guard.sha256_file(src),
            "constants": "SYSTEM, DOC_HEAD, SEP, LETTERS_DE['prefix'] (R2 path, frozen template r2_v1_de)",
            "system": SYSTEM, "doc_head": DOC_HEAD, "sep": SEP, "answer_prefix": ANSWER_PREFIX},
        "prefix_format": {
            "chat_head": CHAT_HEAD, "doc_head": DOC_HEAD, "line": LINE_FORMAT, "line_join": "\n",
            "line_rules": "block text: Docling text, line breaks replaced by one space, lines stripped, empty lines "
                          "left out; a block without text gives the marker only; furniture stays in; nothing is cut",
            "prefix_end": SEP, "suffix": "question + chat_tail + answer_prefix", "suffix_start": "Frage: ",
            "chat_tail": CHAT_TAIL,
            "answer_prefix": ANSWER_PREFIX, "suffix_order": "D1, then one B1 suffix for each block in reading order",
            "tokenization": "ids = tokens(prefix, add_special_tokens=False) + tokens(suffix, add_special_tokens=False)",
            "chat_template": {"file": guard.rel(ct), "sha256": guard.sha256_file(ct),
                              "call": "apply_chat_template(add_generation_prompt=True, enable_thinking=False)"}},
        "d1_question": question_text(D1_QUESTION, D1_OPTIONS),
        "b1_question": question_text(B1_QUESTION, B1_OPTIONS),
        "options": {
            "d1": [{"letter": l, "option": o, "text": t} for l, o, t in D1_OPTIONS],
            "b1": [{"letter": l, "option": o, "text": t} for l, o, t in B1_OPTIONS],
            "first_words": FIRST_WORDS, "no_text": NO_TEXT},
    }
    t["sha256"] = sha256_json(t)
    return {k: t[k] for k in ("template_id", "sha256", "system_text_source", "prefix_format", "d1_question",
                              "b1_question", "options")}


def template_sha(t: dict) -> str:
    return sha256_json({k: v for k, v in t.items() if k != "sha256"})


def check_chat_frame() -> dict:
    """CHAT_HEAD + content + CHAT_TAIL must equal the chat template of the local model for any user content."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    out = {}
    for probe in ("@@U@@", DOC_HEAD + "[B1 | S.1 | text] x" + SEP + question_text(D1_QUESTION, D1_OPTIONS)):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": probe}]
        s = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if s != CHAT_HEAD + probe + CHAT_TAIL:
            raise ValueError("CHAT_HEAD or CHAT_TAIL differs from the chat template of the local model")
    out["chat_frame"] = "equal to apply_chat_template(tokenize=False) of the local model"
    out["transformers_class"] = type(tok).__name__
    return out


# ---------------------------------------------------------------- prompts

def one_line(text: str) -> str:
    return " ".join(p.strip() for p in (text or "").splitlines() if p.strip())


def prompt_line(b: dict) -> str:
    t = one_line(b["text"])
    head = f"[{b['block']} | S.{b['page']} | {b['docling_label']}]"
    return head + " " + t if t else head


def first_words(text: str) -> str:
    w = (text or "").split()
    return " ".join(w[:FIRST_WORDS]) if w else NO_TEXT


def prefix_of(doc: dict) -> str:
    return CHAT_HEAD + DOC_HEAD + "\n".join(prompt_line(b) for b in doc["blocks"]) + SEP


def d1_suffix() -> str:
    return question_text(D1_QUESTION, D1_OPTIONS) + CHAT_TAIL + ANSWER_PREFIX


def b1_suffix(b: dict) -> str:
    q = B1_QUESTION.format(block=b["block"], page=b["page"], first_words=first_words(b["text"]))
    return question_text(q, B1_OPTIONS) + CHAT_TAIL + ANSWER_PREFIX


def item(doc: dict) -> dict:
    p = prefix_of(doc)
    sfx = [{"id": "D1", "text": d1_suffix()}] + [{"id": b["block"], "text": b1_suffix(b)} for b in doc["blocks"]]
    return {"doc_id": doc["doc_id"], "prefix": p, "suffixes": sfx, "n_prefix_chars": len(p)}


@functools.lru_cache(maxsize=1)
def special_texts() -> tuple[str, ...]:
    """The texts of the special tokens of the local tokenizer: the added tokens of tokenizer.json with special true,
    and all_special_tokens of the transformers tokenizer (offline). The tokenizer reads such a text in a block text
    as one special token. An empty result stops (the check would check nothing). Wave 3, stream D: the earlier
    version read added_tokens_decoder of tokenizer_config.json, which the local model does not have (0 texts)."""
    tj = json.loads((MODEL_DIR / "tokenizer.json").read_text(encoding="utf-8"))
    out = {x["content"] for x in tj.get("added_tokens") or [] if x.get("special")}
    from transformers import AutoTokenizer
    out |= set(AutoTokenizer.from_pretrained(str(MODEL_DIR)).all_special_tokens)
    out = tuple(sorted(x for x in out if x))
    if not out:
        raise ValueError("the tokenizer of the local model gives no special token text")
    return out


class SpecialFinder:
    """Finds the texts of special tokens in a text: only at the positions of their first characters, with a set of
    the texts for each length (fast for 136,360 texts)."""

    def __init__(self, texts):
        self.texts = frozenset(texts)
        by_first: dict[str, set[int]] = collections.defaultdict(set)
        for t in self.texts:
            by_first[t[0]].add(len(t))
        self.lengths = {c: tuple(sorted(n)) for c, n in by_first.items()}
        self.rx = re.compile("[" + "".join(re.escape(c) for c in sorted(self.lengths)) + "]")

    def find(self, text: str) -> list[str]:
        hits = []
        for m in self.rx.finditer(text or ""):
            i = m.start()
            for n in self.lengths[text[i]]:
                if i + n > len(text):
                    break
                if text[i:i + n] in self.texts:
                    hits.append(text[i:i + n])
        return hits


def item_special_texts(it: dict, finder: SpecialFinder) -> list[str]:
    """The special token texts in the parts of an item that come from the document: the prefix after CHAT_HEAD (the
    block lines) and each suffix before CHAT_TAIL (the question with the first words of a block). The frame texts
    (CHAT_HEAD, CHAT_TAIL, the answer prefix) hold special tokens by design and are not examined."""
    tail = CHAT_TAIL + ANSWER_PREFIX
    if not it["prefix"].startswith(CHAT_HEAD) or any(not s["text"].endswith(tail) for s in it["suffixes"]):
        raise ValueError(f"{it['doc_id']}: the item does not have the frame of chapter 1")
    parts = [it["prefix"][len(CHAT_HEAD):]] + [s["text"][:-len(tail)] for s in it["suffixes"]]
    return sorted({h for p in parts for h in finder.find(p)})


# ---------------------------------------------------------------- jobs

def job_docs() -> dict:
    """The doc ids of each job. Smoke: the dev document with the most prefix tokens up to MAX_TOKENS (memory, plan
    11 item 6; a longer document gets no states on the VM), the labelled document with the most prefix tokens (plan
    3.6), and the 3 dev pilots; a gap is filled with the labelled dev document with the most prefix tokens. Group 7
    is never in the smoke."""
    sets = json.loads(SETS.read_text(encoding="utf-8"))
    labelled = sorted(set(sets["dev"]) | set(sets["validation"]) | set(sets["group7"]), key=int)
    all_ids = sorted((p.stem for p in docs.DOCS_DIR.glob("*.json")), key=int)
    bulk = [d for d in all_ids if d not in set(labelled)]
    count = token_counter()
    ntok = {}
    for d in all_ids:
        ntok[d] = count([prefix_of(json.loads(docs.doc_path(d).read_text(encoding="utf-8")))])[0]
    key = lambda d: (ntok[d], int(d))  # noqa: E731
    no_g7 = [d for d in all_ids if d not in set(sets["group7"])]
    split_of = {d: json.loads(docs.doc_path(d).read_text(encoding="utf-8"))["split"] for d in no_g7}
    longest_all = max([d for d in no_g7 if ntok[d] <= MAX_TOKENS and split_of[d] == "dev"], key=key)
    longest_lab = max([d for d in labelled if d not in set(sets["group7"])], key=key)
    smoke: list[str] = []
    for d in [longest_all, longest_lab, *SMOKE_PILOTS]:
        if d not in smoke:
            smoke.append(d)
    for d in sorted(sets["dev"], key=key, reverse=True):
        if len(smoke) >= 5:
            break
        if d not in smoke:
            smoke.append(d)
    sel = {"rule": "the dev document with the most prefix tokens up to 32,768, the labelled document with the most "
                   "prefix tokens (not group 7), the 3 dev pilots; a gap: the labelled dev document with the most "
                   "prefix tokens",
           "documents_above_32768_prefix_tokens": {d: ntok[d] for d in all_ids if ntok[d] > MAX_TOKENS},
           "longest_dev_document_up_to_32768": {"doc_id": longest_all, "prefix_tokens": ntok[longest_all]},
           "longest_document_up_to_32768": {"doc_id": max([d for d in no_g7 if ntok[d] <= MAX_TOKENS], key=key),
                                            "prefix_tokens": ntok[max([d for d in no_g7 if ntok[d] <= MAX_TOKENS],
                                                                      key=key)]},
           "longest_labelled_document": {"doc_id": longest_lab, "prefix_tokens": ntok[longest_lab]},
           "longest_labelled_document_of_all_294": {"doc_id": max(labelled, key=key),
                                                    "prefix_tokens": ntok[max(labelled, key=key)]}}
    return {"gpu0_smoke": smoke, "gpu1_labelled": labelled, "gpu2_bulk": bulk, "_selection": sel}


def allowed_of(job: str) -> tuple[str, ...]:
    """Splits that the guard allows for a job: no group 7 in the smoke."""
    return ("dev", "validation") if job == "gpu0_smoke" else guard.DEFAULT_ALLOWED


def token_counter():
    from tokenizers import Tokenizer
    tk = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))

    def count(texts: list[str]) -> list[int]:
        return [len(e.ids) for e in tk.encode_batch(texts, add_special_tokens=False)]
    return count


def split_check(items: list[dict]) -> dict:
    """Information for the VM: tokens(prefix) + tokens(suffix) against tokens(prefix + suffix) (joint text), with
    the transformers tokenizer of the local model, and the joint text against apply_chat_template. For each
    document: all suffixes, or the first SPLIT_CHECK_MAX - 1 and the last suffix."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    n = same = text_same = 0
    diff_examples = []
    for it in items:
        pid = tok.encode(it["prefix"], add_special_tokens=False)
        sfx = it["suffixes"] if len(it["suffixes"]) <= SPLIT_CHECK_MAX else \
            it["suffixes"][:SPLIT_CHECK_MAX - 1] + it["suffixes"][-1:]
        for s in sfx:
            n += 1
            sid = tok.encode(s["text"], add_special_tokens=False)
            joint = tok.encode(it["prefix"] + s["text"], add_special_tokens=False)
            same += (pid + sid) == joint
            user = it["prefix"][len(CHAT_HEAD):] + s["text"][:-len(CHAT_TAIL + ANSWER_PREFIX)]
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
            full = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            text_same += full + ANSWER_PREFIX == it["prefix"] + s["text"]
            if (pid + sid) != joint and len(diff_examples) < 3:
                k = next((i for i, (a, b) in enumerate(zip(pid + sid, joint)) if a != b), min(len(pid + sid), len(joint)))
                diff_examples.append({"doc_id": it["doc_id"], "suffix": s["id"], "first_different_token": k,
                                      "n_prefix_tokens": len(pid)})
    return {"suffixes": n, "split_ids_equal_joint_ids": same, "text_equal_chat_template": text_same,
            "examples_of_differences": diff_examples}


def build_job(job: str, ids: list[str], tpl: dict, count_tokens: bool, extra: dict) -> dict:
    g = guard.assert_allowed(ids, allowed_of(job))
    folder = JOBS / job
    folder.mkdir(parents=True, exist_ok=True)
    tpl_raw = (json.dumps(tpl, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    (folder / "template.json").write_bytes(tpl_raw)
    count = token_counter() if count_tokens else None
    finder = SpecialFinder(special_texts())
    h = hashlib.sha256()
    n_suffix = collections.Counter()
    pchars, schars, ptok, stok = {}, [], {}, []
    special_hits = []
    input_sha = {}
    smoke_items = []
    with open(folder / "items.jsonl", "wb") as f:
        for d in ids:
            dp = docs.doc_path(d)
            raw = dp.read_bytes()
            input_sha[guard.rel(dp)] = hashlib.sha256(raw).hexdigest()
            doc = json.loads(raw)
            docs.check_doc(doc)
            it = item(doc)
            line = (json.dumps(it, ensure_ascii=False) + "\n").encode("utf-8")
            f.write(line)
            h.update(line)
            pchars[d] = it["n_prefix_chars"]
            for s in it["suffixes"]:
                n_suffix["D1" if s["id"] == "D1" else "B1"] += 1
                schars.append(len(s["text"]))
            if item_special_texts(it, finder):
                special_hits.append(d)
            if count:
                ptok[d] = count([it["prefix"]])[0]
                stok += count([s["text"] for s in it["suffixes"]])
            if job == "gpu0_smoke":
                smoke_items.append(it)
    longest = max(ids, key=lambda d: (pchars[d], int(d)))
    est = {d: c / CHARS_PER_TOKEN for d, c in pchars.items()}
    rec = {
        "version": VERSION, "made": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "EXCEPTION (process rule 10, gate GJ)", "job": job,
        "script": {guard.rel(Path(__file__)): guard.sha256_file(Path(__file__)),
                   guard.rel(Path(docs.__file__)): guard.sha256_file(Path(docs.__file__)),
                   guard.rel(Path(guard.__file__)): guard.sha256_file(Path(guard.__file__))},
        "template_id": tpl["template_id"], "template_sha256": tpl["sha256"],
        "guard": {k: v for k, v in g.items() if k not in ("split_of", "parliament_of")},
        "documents": len(ids), "documents_by_split": dict(collections.Counter(g["split_of"][d] for d in ids)),
        "suffixes": {"D1": n_suffix["D1"], "B1": n_suffix["B1"], "all": sum(n_suffix.values())},
        "prefix_chars": {"sum": sum(pchars.values()), "max": pchars[longest], "max_doc": longest},
        "prefix_tokens_estimate": {"chars_per_token": CHARS_PER_TOKEN, "sum": round(sum(est.values())),
                                   "max": round(est[longest]), "docs_above_32768": sum(v > MAX_TOKENS for v in est.values())},
        "suffix_chars": {"sum": sum(schars), "max": max(schars), "mean": round(sum(schars) / len(schars), 1)},
        "suffix_tokens_estimate": {"sum": round(sum(schars) / CHARS_PER_TOKEN),
                                   "mean": round(sum(schars) / len(schars) / CHARS_PER_TOKEN, 1)},
        "docs_with_special_token_text_in_blocks": special_hits,
        "special_token_texts": {"count": len(finder.texts), "sha256": sha256_json(sorted(finder.texts)),
                                "source": "tokenizer.json added_tokens with special true, and all_special_tokens"},
        "files": {guard.rel(folder / "template.json"): hashlib.sha256(tpl_raw).hexdigest(),
                  guard.rel(folder / "items.jsonl"): h.hexdigest()},
        "inputs": {guard.rel(SETS): guard.sha256_file(SETS), guard.rel(docs.RECORD): guard.sha256_file(docs.RECORD),
                   **input_sha},
        "doc_ids": ids,
        **extra,
    }
    if count:
        lt = max(ids, key=lambda d: (ptok[d], int(d)))
        rec["prefix_tokens_exact"] = {"sum": sum(ptok.values()), "max": ptok[lt], "max_doc": lt,
                                      "docs_above_32768": sorted((d for d in ids if ptok[d] > MAX_TOKENS), key=int),
                                      "chars_per_token_measured": round(sum(pchars.values()) / sum(ptok.values()), 3)}
        rec["suffix_tokens_exact"] = {"sum": sum(stok), "max": max(stok), "mean": round(sum(stok) / len(stok), 1)}
        rec["prefix_tokens_by_doc"] = {d: ptok[d] for d in ids}
    if job == "gpu0_smoke":
        rec["tokenization_check"] = split_check(smoke_items)
    (JOBS / f"{job}.build.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def cmd_build(args) -> int:
    tpl = template()
    if template_sha(tpl) != tpl["sha256"]:
        raise ValueError("template SHA-256 is not stable")
    frame = check_chat_frame() if not args.no_render_check else {"chat_frame": "not checked (--no-render-check)"}
    jd = job_docs()
    jobs = JOB_NAMES if args.job == "all" else (args.job,)
    out = {}
    for j in jobs:
        extra = {"chat_frame_check": frame}
        if j == "gpu0_smoke":
            extra["smoke_selection"] = jd["_selection"]
        rec = build_job(j, jd[j], tpl, args.count_tokens, extra)
        keep = ("documents", "documents_by_split", "suffixes", "prefix_chars", "prefix_tokens_estimate",
                "suffix_tokens_estimate", "prefix_tokens_exact", "suffix_tokens_exact", "template_sha256", "files",
                "docs_with_special_token_text_in_blocks", "tokenization_check", "smoke_selection")
        out[j] = {k: rec[k] for k in keep if k in rec}
        if j == "gpu0_smoke":
            out[j]["doc_ids"] = rec["doc_ids"]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_check(args) -> int:
    """Build the items again in memory and compare the SHA-256 with the written files (determinism). Information:
    the documents whose items hold the text of a special token (item_special_texts(); doc ids and counts only)."""
    tpl = template()
    finder = SpecialFinder(special_texts())
    bad = 0
    jobs = JOB_NAMES if args.job == "all" else (args.job,)
    for j in jobs:
        rec = json.loads((JOBS / f"{j}.build.json").read_text(encoding="utf-8"))
        guard.assert_allowed(rec["doc_ids"], allowed_of(j))
        h = hashlib.sha256()
        special_docs = []
        for d in rec["doc_ids"]:
            doc = json.loads(docs.doc_path(d).read_text(encoding="utf-8"))
            it = item(doc)
            h.update((json.dumps(it, ensure_ascii=False) + "\n").encode("utf-8"))
            if item_special_texts(it, finder):
                special_docs.append(d)
        folder = JOBS / j
        ok = (h.hexdigest() == rec["files"][guard.rel(folder / "items.jsonl")]
              == guard.sha256_file(folder / "items.jsonl")
              and tpl["sha256"] == rec["template_sha256"]
              == json.loads((folder / "template.json").read_text(encoding="utf-8"))["sha256"])
        bad += not ok
        print(json.dumps({"job": j, "documents": len(rec["doc_ids"]), "rebuild_equal": ok,
                          "items_sha256": h.hexdigest(), "special_token_texts": len(finder.texts),
                          "documents_with_special_token_text": len(special_docs),
                          "doc_ids_with_special_token_text": special_docs}))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template")
    b = sub.add_parser("build")
    b.add_argument("--job", choices=JOB_NAMES + ("all",), default="all")
    b.add_argument("--count-tokens", action="store_true")
    b.add_argument("--no-render-check", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--job", choices=JOB_NAMES + ("all",), default="all")
    args = ap.parse_args()
    if args.cmd == "template":
        print(json.dumps(template(), ensure_ascii=False, indent=1))
        return 0
    return cmd_build(args) if args.cmd == "build" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())

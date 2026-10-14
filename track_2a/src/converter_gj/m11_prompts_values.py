# SPDX-License-Identifier: Apache-2.0
"""Value cascade, task B: the template gj_values_v1_de (the Apertus questions along the cascade).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: AI agent (Claude Opus 5.5), for the
AI agent. No human checked this file. This file does not change an existing file. It does not load a model. It
loads only the tokenizer files of the local model. Status of all outputs: EXCEPTION (process rule 10), NOT RELEASED.

1 Relation to the template gj_jev_v1_de (src/m10_prompts.py, not changed)
  The prefix is the SAME text: this file calls m10_prompts.prefix_of(). So the prefix tokens, the prefill rate and
  the GPU memory of the stored runs apply. The frame of a question is the same (m10_prompts.question_text form,
  CHAT_TAIL, the answer prefix "Antwort:"). Only the questions and the suffix ids are new.

2 Questions (German, as the measured read-outs)
  Q0  one for each document, suffix id "Q0": the kind of the document, 7 lettered options.
      Source: no rule in the standard: project choice. eCH-0295 has no list of document kinds. The options A, B
      and C are the options A, B and C of the question D1 of gj_jev_v1_de.
  Q1  one for each document, suffix id "Q1": the affair type. Options A to I are the 9 values of the list
      AffairTypeEnum of eCH-0295 (schema file quellen/political-affairs-ech-group/ech-0295_affairs/input/
      schema.yaml, class Affair, slot affair_type, range AffairTypeEnum), in the order of the schema, with the
      German names of the schema. The standard keeps `request` and `question` apart; this template does too.
      Options J (another type, for example a petition) and K (no affair type) are not values of the standard:
      project choice. The standard has no list value for a petition and no rule that gives a proposal of the
      executive the value `draft_decree`: the option G has only the German name of the schema.
  Q2  one for each block, suffix id "Q2.B<n>": which values of the affair does the block state. 7 value kinds
      and "none". A block can state 2 or more values. Thus the read-out is NOT the letter: one binary head for
      each value kind is fitted on the state of this ONE question (multi-label heads). The letters stay for the
      form of the question.
  The read-out for each question is the hidden state at the last suffix token (layers 8 to 32 in steps of 4).

3 The frozen extractor src/m10_vm_states.py and this template
  The extractor accepts any suffix id of 1 to 40 characters of A-Z, a-z, 0-9, _, . and -. It needs the keys
  d1_question and b1_question in template.json: this template has them (the texts of Q0 and Q2) and adds the key
  questions with all 3 texts. The extractor stores letter_logprobs only for the letters A to F: the letters G to
  K of this template get no letter value. The heads do not use letter values.

Usage:
  uv run --offline --frozen --no-sync python src/m11_prompts_values.py template
  uv run --offline --frozen --no-sync python src/m11_prompts_values.py check      (self-check, token counts)
  uv run --offline --frozen --no-sync python src/m11_prompts_values.py write      (the prompt text files)
"""

from __future__ import annotations

import argparse
import json
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_guard as guard  # noqa: E402
import m10_prompts as base  # noqa: E402

VERSION = "m11-prompts-values-1"
ROOT = guard.ROOT
TEMPLATE_ID = "gj_values_v1_de"
PROMPT_DIR = ROOT / "daten/gj_values/prompts" / TEMPLATE_ID
SCHEMA = ROOT / "quellen/political-affairs-ech-group/ech-0295_affairs/input/schema.yaml"
STORED_TOKENS_PER_CHAR = 1 / 3.286          # gpu2_bulk.build.json: chars_per_token_measured (fallback only)
ANSWER_ONE = base.ANSWER_LINE
ANSWER_MULTI = "Antworte mit den Buchstaben aller Angaben, die der Block nennt."

Q0_ID, Q1_ID, Q2_PREFIX = "Q0", "Q1", "Q2."
Q0_QUESTION = "Was für ein Dokument ist das?"
Q0_OPTIONS = (("A", "proposal", "nur ein Vorstoss eines Ratsmitglieds oder einer Fraktion"),
              ("B", "response", "nur die Antwort der Exekutive auf einen Vorstoss"),
              ("C", "proposal_and_response", "Vorstoss und Antwort der Exekutive zusammen"),
              ("D", "executive_proposal", "Vorlage der Exekutive (Botschaft, Bericht mit Antrag an den Rat)"),
              ("E", "committee_report", "Bericht einer Kommission"),
              ("F", "minutes", "Protokoll"),
              ("G", "other", "ein anderes Dokument"))
Q1_QUESTION = "Welchen Geschäftstyp nach eCH-0295 hat das Geschäft dieses Dokuments?"
# letters A to I: the 9 values of AffairTypeEnum in the order of the schema, German names of the schema
Q1_OPTIONS = (("A", "motion", "Motion"),
              ("B", "postulate", "Postulat"),
              ("C", "interpellation", "Interpellation"),
              ("D", "request", "(Einfache) Anfrage"),
              ("E", "question", "Frage für die Fragestunde"),
              ("F", "parliamentary_initiative", "Parlamentarische Initiative"),
              ("G", "draft_decree", "Beschlussesentwurf oder Erlassentwurf"),
              ("H", "motion_and_postulate", "Motion und Postulat (kombiniert)"),
              ("I", "motion_then_postulate", "ursprünglich Motion, später als Postulat behandelt"),
              ("J", "other", "ein anderer Geschäftstyp (zum Beispiel Petition)"),
              ("K", "none", "kein Geschäftstyp"))
Q1_SCHEMA_VALUES = tuple(o for _, o, _ in Q1_OPTIONS[:9])
Q2_QUESTION = ("Welche dieser Angaben zum Geschäft nennt Block [{block}] auf Seite {page}, der mit «{first_words}» "
               "beginnt? Mehrere sind möglich.")
Q2_OPTIONS = (("A", "affair_number", "Geschäftsnummer"),
              ("B", "title", "Titel des Geschäfts"),
              ("C", "submission_date", "Datum der Einreichung"),
              ("D", "sponsor", "Name der Person oder Gruppe, die das Geschäft einreicht"),
              ("E", "response_date", "Datum der Antwort oder des Beschlusses der Exekutive"),
              ("F", "responder", "Name der antwortenden Stelle"),
              ("G", "recommendation", "Antrag oder Empfehlung der Exekutive (annehmen, ablehnen usw.)"),
              ("H", "none", "keine dieser Angaben"))
Q2_VALUE_KINDS = tuple(o for _, o, _ in Q2_OPTIONS[:7])
FIELDS_FILE = "src/m11_values_base.py"
SCHEMA_REL = "quellen/political-affairs-ech-group/ech-0295_affairs/input/schema.yaml"
Q2_SOURCES = {
    "affair_number": f"{SCHEMA_REL}: class Affair, slot affair_number",
    "title": f"{SCHEMA_REL}: class Affair, slot title",
    "submission_date": f"{SCHEMA_REL}: class Submission, slot submission_date",
    "sponsor": f"{SCHEMA_REL}: class Submission, slot sponsorship (class Sponsorship, slots actor and sponsor_role)",
    "response_date": f"project rule ({FIELDS_FILE}, FIELDS: ResponseStep.date_end_actual)",
    "responder": f"{SCHEMA_REL}: class ResponseStep, slot responder",
    "recommendation": f"{SCHEMA_REL}: class ResponseStep, slot recommendation (range RecommendationEnum)",
    "none": "no rule in the standard: project choice (a block that states none of the 7 value kinds)",
}


# ---------------------------------------------------------------- template

def question_text(question: str, options, answer_line: str) -> str:
    """The frame of m10_prompts.question_text with a free answer line."""
    return "Frage: " + question + "\n" + "\n".join(f"{l} = {t}" for l, _, t in options) + "\n" + answer_line


def q0_text() -> str:
    return question_text(Q0_QUESTION, Q0_OPTIONS, ANSWER_ONE)


def q1_text() -> str:
    return question_text(Q1_QUESTION, Q1_OPTIONS, ANSWER_ONE)


def q2_text_form() -> str:
    return question_text(Q2_QUESTION, Q2_OPTIONS, ANSWER_MULTI)


def template() -> dict:
    b = base.template()
    pf = dict(b["prefix_format"])
    pf["suffix_order"] = "Q0, Q1, then one Q2 suffix for each selected block in reading order (id Q2.B<n>)"
    opts = lambda o: [{"letter": l, "option": v, "text": t} for l, v, t in o]  # noqa: E731
    t = {
        "template_id": TEMPLATE_ID,
        "system_text_source": b["system_text_source"],
        "prefix_format": pf,
        "d1_question": q0_text(),
        "b1_question": q2_text_form(),
        "questions": {"q0": q0_text(), "q1": q1_text(), "q2": q2_text_form()},
        "options": {
            "q0": opts(Q0_OPTIONS), "q1": opts(Q1_OPTIONS), "q2": opts(Q2_OPTIONS),
            "first_words": base.FIRST_WORDS, "no_text": base.NO_TEXT},
        "suffix_ids": {"q0": Q0_ID, "q1": Q1_ID, "q2": Q2_PREFIX + "B<n>"},
        "readout": {
            "state": "the hidden state at the last suffix token (layers 8 to 32 in steps of 4); no text generation",
            "q0": "one head with one class for each option (single label)",
            "q1": "one head with one class for each option (single label)",
            "q2": "MULTI-LABEL: one binary head for each of the 7 value kinds, all fitted on the state of this one "
                  "question; a block can state 2 or more values; the letter is not the read-out",
            "q2_value_kinds": list(Q2_VALUE_KINDS),
            "letter_logprobs": "m10_vm_states.py stores them for the letters A to F only; the heads do not use them"},
        "sources": {
            "q0": "no rule in the standard: project choice (eCH-0295 has no list of document kinds); the options A, "
                  "B and C are the options A, B and C of the question D1 of the template gj_jev_v1_de",
            "q1": {"A_to_I": f"{SCHEMA_REL}: class Affair, slot affair_type, range AffairTypeEnum (9 values, order "
                             "and German names of the schema)",
                   "J_and_K": "no rule in the standard: project choice (the list has no value for a petition, for "
                              "another type or for no type)",
                   "schema_sha256": guard.sha256_file(SCHEMA)},
            "q2": Q2_SOURCES},
        "extractor_keys": "d1_question and b1_question exist because src/m10_vm_states.py (frozen) needs these keys: "
                          "d1_question = the text of Q0, b1_question = the text form of Q2",
        "same_prefix_as": {"template_id": b["template_id"], "template_sha256": b["sha256"],
                           "function": "m10_prompts.prefix_of"},
    }
    t["sha256"] = base.sha256_json(t)
    return {"template_id": t["template_id"], "sha256": t["sha256"], **{k: v for k, v in t.items()
                                                                       if k not in ("template_id", "sha256")}}


def template_sha(t: dict) -> str:
    """The rule of m10_prompts: SHA-256 of the canonical JSON of the template without the key sha256."""
    return base.template_sha(t)


# ---------------------------------------------------------------- suffixes and items

TAIL = base.CHAT_TAIL + base.ANSWER_PREFIX


def q0_suffix() -> str:
    return q0_text() + TAIL


def q1_suffix() -> str:
    return q1_text() + TAIL


def q2_suffix(b: dict) -> str:
    q = Q2_QUESTION.format(block=b["block"], page=b["page"], first_words=base.first_words(b["text"]))
    return question_text(q, Q2_OPTIONS, ANSWER_MULTI) + TAIL


def select_blocks(doc: dict, limit: str = "all") -> list[dict]:
    """The blocks that get a Q2 suffix. all: each block. pages3_last: the blocks of the first 3 pages and of the
    last page of the document (pages = the Docling page numbers of the blocks). The prefix always holds all blocks."""
    bl = doc["blocks"]
    if limit == "all" or not bl:
        return list(bl)
    if limit != "pages3_last":
        raise ValueError(f"limit {limit!r}: use all or pages3_last")
    pages = sorted({b["page"] for b in bl})
    keep = set(pages[:3]) | {pages[-1]}
    return [b for b in bl if b["page"] in keep]


def item(doc: dict, limit: str = "all") -> dict:
    """One line of items.jsonl in the form of m10_prompts.item (interface 5 of src/m10_vm_states.py)."""
    p = base.prefix_of(doc)
    sfx = [{"id": Q0_ID, "text": q0_suffix()}, {"id": Q1_ID, "text": q1_suffix()}]
    sfx += [{"id": Q2_PREFIX + b["block"], "text": q2_suffix(b)} for b in select_blocks(doc, limit)]
    return {"doc_id": doc["doc_id"], "prefix": p, "suffixes": sfx, "n_prefix_chars": len(p)}


# ---------------------------------------------------------------- self-check

def synthetic_doc() -> dict:
    """A document of invented text (no project document) for the self-check and the token counts."""
    texts = ["Grosser Rat", "Motion 24.999 von Anna Muster vom 3. März 2024 betreffend ein erfundenes Beispiel zur "
             "Prüfung der Fragen", "Der Regierungsrat wird beauftragt, ein Beispiel vorzulegen.", "",
             "Antwort des Regierungsrates vom 5. Juni 2024. Der Regierungsrat beantragt die Ablehnung der Motion."]
    return {"doc_id": "0", "blocks": [{"block": f"B{i + 1}", "page": 1 + i // 3, "docling_label": "text", "text": t}
                                      for i, t in enumerate(texts)]}


def schema_values() -> list[str]:
    """The permissible values of AffairTypeEnum in the order of the schema (PyYAML)."""
    import yaml
    s = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    return list(s["enums"]["AffairTypeEnum"]["permissible_values"])


def token_counts() -> dict:
    """Token counts of the suffixes with the tokenizer of the local model (the function of m10_prompts); if the
    tokenizer file is absent: the stored rate of the job gpu2_bulk."""
    doc = synthetic_doc()
    texts = {"Q0": q0_suffix(), "Q1": q1_suffix(), "Q2 (12 first words)": q2_suffix(doc["blocks"][1]),
             "Q2 (block without text)": q2_suffix(doc["blocks"][3]),
             "B1 of gj_jev_v1_de (12 first words, for comparison)": base.b1_suffix(doc["blocks"][1]),
             "D1 of gj_jev_v1_de (for comparison)": base.d1_suffix()}
    if (base.MODEL_DIR / "tokenizer.json").exists():
        n = base.token_counter()(list(texts.values()))
        return {"source": "tokenizer.json of the local model (tokenizers library)",
                "tokens": dict(zip(texts, n)), "chars": {k: len(v) for k, v in texts.items()}}
    return {"source": f"stored rate {STORED_TOKENS_PER_CHAR:.4f} tokens per character (gpu2_bulk.build.json)",
            "tokens": {k: round(len(v) * STORED_TOKENS_PER_CHAR) for k, v in texts.items()},
            "chars": {k: len(v) for k, v in texts.items()}}


def self_check(render: bool = True) -> dict:
    t = template()
    res: dict = {"template_id": t["template_id"], "template_sha256": t["sha256"], "checks": {}}
    c = res["checks"]
    c["sha256_stable"] = template_sha(t) == t["sha256"] == template()["sha256"]
    c["extractor_template_keys"] = all(k in t for k in ("template_id", "sha256", "system_text_source",
                                                         "prefix_format", "d1_question", "b1_question", "options"))
    for name, o in (("q0", Q0_OPTIONS), ("q1", Q1_OPTIONS), ("q2", Q2_OPTIONS)):
        c[f"{name}_letters_in_order"] = [l for l, _, _ in o] == list(string.ascii_uppercase[:len(o)])
        c[f"{name}_options_unique"] = len({v for _, v, _ in o}) == len(o) == len({x for _, _, x in o})
    c["q1_schema_values_equal_schema_file"] = list(Q1_SCHEMA_VALUES) == schema_values()
    c["q2_question_names_all_value_kinds"] = all(x in q2_text_form() for _, _, x in Q2_OPTIONS)
    c["q2_sources_for_all_kinds"] = set(Q2_SOURCES) == {v for _, v, _ in Q2_OPTIONS}
    doc = synthetic_doc()
    it = item(doc)
    ref = base.item(doc)
    c["prefix_equal_gj_jev_v1_de"] = it["prefix"] == ref["prefix"]
    c["suffix_ids"] = [s["id"] for s in it["suffixes"]] == ["Q0", "Q1"] + ["Q2." + b["block"] for b in doc["blocks"]]
    import m10_vm_states as vm
    c["extractor_item_format"] = vm.check_item(it, 1) == []
    c["suffix_ends_with_frame"] = all(s["text"].endswith(TAIL) and s["text"].startswith("Frage: ")
                                      for s in it["suffixes"])
    c["limit_keeps_first_3_pages_and_last"] = (
        [b["block"] for b in select_blocks({"blocks": [{"block": f"B{i}", "page": p} for i, p in
                                                       enumerate([1, 2, 3, 4, 5, 6])]}, "pages3_last")]
        == ["B0", "B1", "B2", "B5"])
    if render:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(str(base.MODEL_DIR))
        frame = ids = 0
        for s in it["suffixes"]:
            user = it["prefix"][len(base.CHAT_HEAD):] + s["text"][:-len(TAIL)]
            msgs = [{"role": "system", "content": base.SYSTEM}, {"role": "user", "content": user}]
            full = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            frame += full + base.ANSWER_PREFIX == it["prefix"] + s["text"]
            ids += (tok.encode(it["prefix"], add_special_tokens=False) + tok.encode(s["text"], add_special_tokens=False)
                    == tok.encode(it["prefix"] + s["text"], add_special_tokens=False))
        n = len(it["suffixes"])
        c["text_equal_chat_template"] = frame == n
        c["split_ids_equal_joint_ids"] = ids == n
        pre, suf = vm.tokenize_item(tok, it)
        c["extractor_token_problems"] = vm.token_problems(tok, pre, suf) == []
        res["letter_tokens"] = {l: len(tok.encode(vm.LETTER_FORM.format(l), add_special_tokens=False))
                                for l in string.ascii_uppercase[:11]}
        c["letters_A_to_K_one_token_each"] = set(res["letter_tokens"].values()) == {1}
    res["suffix_tokens"] = token_counts()
    res["result"] = "PASS" if all(v is True for v in c.values()) else "FAIL"
    return res


# ---------------------------------------------------------------- prompt text files

def write_prompt_files() -> dict:
    """The public-ready prompt texts as plain text. No document text: the block lines are a format line."""
    t = template()
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    pf = t["prefix_format"]
    files = {
        "system.txt": base.SYSTEM + "\n",
        "prefix_format.txt": (pf["chat_head"] + pf["doc_head"] + pf["line"] + "\n" + pf["line"] + "\n...") + pf["prefix_end"],
        "q0_document_kind.txt": q0_suffix() + "\n",
        "q1_affair_type.txt": q1_suffix() + "\n",
        "q2_block_values.txt": q2_text_form() + TAIL + "\n",
        "template.json": json.dumps(t, ensure_ascii=False, indent=1) + "\n",
        "README.txt": (
            f"Template {TEMPLATE_ID}, SHA-256 {t['sha256']}.\n"
            "Model: Apertus-v1.5-8B, bf16. No text generation.\n"
            "One prompt = the prefix (system.txt in the chat frame, then the document as block lines:\n"
            "prefix_format.txt) + one suffix (one question). The read-out is the hidden state at the last\n"
            "token of the suffix. Small heads are fitted on this state.\n"
            "q0_document_kind.txt: one time for each document. Single label.\n"
            "q1_affair_type.txt: one time for each document. Single label. Options A to I are the values of\n"
            "the list AffairTypeEnum of eCH-0295. Options J and K are a project choice.\n"
            "q2_block_values.txt: one time for each block. The places {block}, {page} and {first_words} get\n"
            "the block id, the page and the first 12 words of the block. MULTI-LABEL: one binary head for\n"
            "each of the 7 value kinds reads the same state. The letter is not the read-out.\n"
            "template.json: the full record with the source of each option.\n"
            "Code: src/m11_prompts_values.py (questions), src/m10_prompts.py (prefix).\n"),
    }
    out = {}
    for n, s in files.items():
        (PROMPT_DIR / n).write_text(s, encoding="utf-8")
        out[guard.rel(PROMPT_DIR / n)] = guard.sha256_file(PROMPT_DIR / n)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template")
    c = sub.add_parser("check")
    c.add_argument("--no-render-check", action="store_true")
    sub.add_parser("write")
    a = ap.parse_args()
    if a.cmd == "template":
        print(json.dumps(template(), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "check":
        r = self_check(render=not a.no_render_check)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["result"] == "PASS" else 1
    r = self_check()
    if r["result"] != "PASS":
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 1
    print(json.dumps({"template_sha256": r["template_sha256"], "files": write_prompt_files()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

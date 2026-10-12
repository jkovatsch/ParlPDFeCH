# SPDX-License-Identifier: Apache-2.0
"""Isolation at the level of E20 (step 3.9) with Apertus v1.5 on the CSCS inference API: in-context readout.

Apertus (default 70B) reads K annotated example documents and then the whole target document (E18).
Then, for each atom of the target, it gives one of the 13 answers of `m03_iso_jev.py`. The output is
constrained by a regular expression (vLLM structured_outputs): the atom ids, the colons, the spaces and
the newlines are fixed; only the answer letter of each atom is free, and only among the allowed
letters. With temperature 0, the server takes the letter with the highest probability. This is the
same computation as the local readout (`m04_iso_auslesen.py`): no free text (E19). The response gives
the probabilities of the allowed letters at each answer position (masked and renormalized).

- Fixed roles (E20 chapter 3.1, `m03_iso_hilfe.py`): the regex fixes their letters.
- Page furniture only by a fixed role: for the other atoms the letter A (furniture) is not allowed.
- Examples: documents of the training pool with a reference (`daten/iso/pool_ref`), whose parliament
  is not in the evaluated group and not in group 6 (cross-validation over groups, E29), with triage
  PASS. Selection: same language first, then same document role, then length near 4,000 tokens; one
  document for each parliament.
- Each document goes to CSCS only with triage PASS (`daten/iso/triage.csv`, process rule 13.3).
- The key comes from `.env.cscs`. The script never prints it.
- The prompt is assembled locally with the chat template of the local tokenizer (same tokenizer as on
  the server) and sent as token ids to /v1/completions.

Output: segmentation files (format of m03_iso_mass.py) with "readout" (the probabilities of the
13 answers for each atom) in --out, and run.json (model, examples, tokens, seconds for each document).

Usage:  uv run python src/m04_iso_cscs.py --groups 1,2,3,4,5 --shots 6 --out daten/iso/hyp_cscs70_k6
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_hilfe as hf  # noqa: E402
import m03_iso_jev as jev  # noqa: E402
import m03_iso_mass as ms  # noqa: E402

ROOT = jev.ROOT
ENV = ROOT / ".env.cscs"
TRIAGE = ROOT / "daten/iso/triage.csv"
with open(ms.GROUPS, newline="", encoding="utf-8") as _f:
    FINAL_PARL = {r["body_key"] for r in csv.DictReader(_f) if r["group"] == "7"}   # no example of these parliaments
LETTERS = [o[0] for o in jev.OPTIONS]
SYSTEM_ICL = jev.SYSTEM + "\n\n" + jev.INSTRUCTION


def env() -> dict:
    out = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def triage_pass() -> set[str]:
    if not TRIAGE.exists():
        return set()
    with open(TRIAGE, newline="", encoding="utf-8") as f:
        return {r["doc_id"] for r in csv.DictReader(f) if r["final"] == "PASS"}


def answer_block(doc_id: str, ids: list[str], answers: list[str]) -> str:
    return "Zuordnung:\n" + "".join(f"{a}: {LETTERS[jev.ANSWERS.index(x)]}\n" for a, x in zip(ids, answers))


def document_text(doc_id: str) -> str:
    return "Dokument:\n" + (jev.PROMPTS / f"{doc_id}.txt").read_text(encoding="utf-8")


def regex_for(ids: list[str], fixed: dict) -> str:
    free = "[" + "".join(LETTERS[1:]) + "]"            # no page furniture without a fixed role
    parts = []
    for a in ids:
        letter = LETTERS[jev.ANSWERS.index(fixed[a][0])] if a in fixed else None
        parts.append(re.escape(f"{a}: ") + (letter if letter else free) + r"\n")
    return "".join(parts)


def choose_examples(target: dict, pool: list[dict], k: int, lengths: dict[str, int]) -> list[str]:
    def score(r):
        return (r["sprache"] != target["sprache"], r["dokumentrolle"] != target["dokumentrolle"],
                abs(lengths.get(r["doc_id"], 10 ** 6) - 4000), int(r["doc_id"]))
    out, parls = [], set()
    if k <= 0:
        return out
    for r in sorted(pool, key=score):
        if r["body_key"] in parls:
            continue
        out.append(r["doc_id"])
        parls.add(r["body_key"])
        if len(out) == k:
            break
    return out


def parse_readout(text: str, tokens: list[str], top: list[dict], ids: list[str]) -> tuple[list[str], dict]:
    """Answers and the distribution over the 13 letters at each answer position."""
    expect = "".join(f"{a}: X\n" for a in ids)
    if len(text) != len(expect):
        raise ValueError(f"output length {len(text)} != expected {len(expect)}")
    offsets, pos = [], 0
    for t in tokens:
        offsets.append(pos)
        pos += len(t)
    answers, readout, cursor = [], {}, 0
    for a in ids:
        cursor += len(f"{a}: ")
        letter = text[cursor]
        assert letter in LETTERS, (a, letter)
        k = max(i for i, o in enumerate(offsets) if o <= cursor)
        dist = {}
        for tok, lp in (top[k] or {}).items():
            s = tok.strip()
            if s in LETTERS and lp > -9000:
                dist[s] = max(dist.get(s, -1e9), lp)
        z = sum(math.exp(v) for v in dist.values()) or 1.0
        probs = {jev.ANSWERS[LETTERS.index(s)]: round(math.exp(v) / z, 4) for s, v in dist.items()}
        ans = jev.ANSWERS[LETTERS.index(letter)]
        answers.append(ans)
        readout[a] = {"answer": ans, "p": probs.get(ans, 1.0), "probs": probs}
        cursor += 2
    return answers, readout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", default="1,2,3,4,5")
    ap.add_argument("--model", default="swiss-ai/Apertus-v1.5-70B")
    ap.add_argument("--shots", type=int, default=6)
    ap.add_argument("--max-example-tokens", type=int, default=12000)
    ap.add_argument("--pool-ref", default="daten/iso/pool_ref")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=120, help="atoms for each request (long documents: several requests)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--e20", action="store_true", help="put E20 (chapters 3 to 5 and 9) into the system message")
    args = ap.parse_args()

    groups = [g for g in args.groups.split(",") if g]
    if {"6", "7"} & set(groups) and not args.final:
        sys.exit("groups 6 and 7 are protected (7 = final group; 6 = development group for E20 v4 only): use --final only for the final measurement")
    allowed = triage_pass()
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        grp = list(csv.DictReader(f))
    with open(ROOT / "daten/iso/pool.csv", newline="", encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    with open(ROOT / "daten/analyse/iso/jev_lengths.csv", newline="", encoding="utf-8") as f:
        lengths = {r["doc_id"]: int(r["tokens_total"]) for r in csv.DictReader(f)}
    pool_ref = ROOT / args.pool_ref

    from mlx_lm.utils import load_tokenizer

    tok = load_tokenizer(jev.MODEL)
    e = env()
    url = e["CSCS_BASE_URL"].rstrip("/") + "/completions"
    headers = {"Authorization": "Bearer " + e["CSCS_API_KEY"], "Content-Type": "application/json"}
    out = ROOT / args.out
    (out / "raw").mkdir(parents=True, exist_ok=True)
    system = SYSTEM_ICL
    if args.e20:
        e20 = (ROOT / "crisp-dm/03-data-preparation/isolation-level-e20.md").read_text(encoding="utf-8")
        keep = [c for c in e20.split("\n## ") if c[:2] in ("3 ", "4 ", "5 ", "9 ")]
        system += ("\n\nDefinition (E20, English). The answer letters map to the roles and classes: "
                   + ", ".join(f"{l} = {a}" for l, a, _ in jev.OPTIONS) + ".\n\n## " + "\n## ".join(keep))
    run = {"model": args.model, "shots": args.shots, "e20": args.e20, "task": jev.VERSION,
           "fixed_roles": hf.VERSION, "documents": [], "skipped": []}

    def one(r: dict) -> dict:
        d = r["doc_id"]
        if d not in allowed:
            return {"doc_id": d, "skipped": "triage not PASS"}
        cand = [p for p in pool if p["home"] not in (r["group"], "6") and p["doc_id"] in allowed
                and p["body_key"] not in FINAL_PARL
                and (pool_ref / f"{p['doc_id']}.json").exists()
                and lengths.get(p["doc_id"], 10 ** 6) <= args.max_example_tokens]
        shots = choose_examples(r, cand, args.shots, lengths)
        msgs = [{"role": "system", "content": system}]
        for s in shots:
            ids_s, ans_s = jev.reference(pool_ref, s)
            msgs += [{"role": "user", "content": document_text(s)},
                     {"role": "assistant", "content": answer_block(s, ids_s, ans_s)}]
        msgs.append({"role": "user", "content": document_text(d)})
        prompt = list(tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False,
                                              return_dict=False))
        prompt += tok.encode("Zuordnung:\n", add_special_tokens=False)
        ids = ms.atom_ids(d)
        fixed = hf.fixed_roles(d)[0]
        t0 = time.perf_counter()
        answers, readout, raws, usage = [], {}, [], {"prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0}
        fingerprint = None
        for c0 in range(0, len(ids), args.chunk):
            part = ids[c0: c0 + args.chunk]
            done = "".join(f"{a}: {LETTERS[jev.ANSWERS.index(x)]}\n" for a, x in zip(ids[:c0], answers))
            ptoks = prompt + (tok.encode(done, add_special_tokens=False) if done else [])
            body = {"model": args.model, "prompt": ptoks, "max_tokens": 12 * len(part) + 16, "temperature": 0,
                    "logprobs": 13, "structured_outputs": {"regex": regex_for(part, fixed)}}
            res = None
            # HTTP 500 comes back when a top token cannot be decoded (seen with logprobs 13 and 20);
            # then fewer top tokens. The allowed letters are the top tokens, so 8 still covers most of them.
            ladder = [13, 12, 10, 8, 5]
            for attempt in range(6):
                try:
                    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=900) as resp:
                        res = json.loads(resp.read())
                    break
                except Exception as ex:  # noqa: BLE001
                    msg = str(ex)[:200]
                    if attempt == 5:
                        return {"doc_id": d, "error": msg, "chunk": c0}
                    if "500" in msg and body["logprobs"] in ladder[:-1]:
                        body["logprobs"] = ladder[ladder.index(body["logprobs"]) + 1]
                    else:
                        time.sleep(10 * (attempt + 1))
            raws.append({"request": {k: v for k, v in body.items() if k != "prompt"}, "prompt_tokens": len(ptoks),
                         "response": res})
            ch = res["choices"][0]
            lp = ch["logprobs"]
            a_part, r_part = parse_readout(ch["text"], lp["tokens"], lp["top_logprobs"], part)
            answers += a_part
            readout.update(r_part)
            u = res["usage"]
            usage["prompt_tokens"] += u["prompt_tokens"]
            usage["completion_tokens"] += u["completion_tokens"]
            usage["cached_tokens"] += (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
            fingerprint = res.get("system_fingerprint")
        (out / "raw" / f"{d}.json").write_text(json.dumps({"examples": shots, "chunks": raws}, ensure_ascii=False),
                                              encoding="utf-8")
        seg = jev.segmentation_from_answers(d, ids, answers, f"cscs:{args.model}:k{args.shots}")
        seg["readout"] = readout
        (out / f"{d}.json").write_text(json.dumps(seg, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"doc_id": d, "examples": shots, **usage, "chunks": len(raws),
                "seconds": round(time.perf_counter() - t0, 1), "fingerprint": fingerprint}

    rows = [r for r in grp if r["group"] in groups]
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for res in ex.map(one, rows):
            key = "documents" if "prompt_tokens" in res else "skipped"
            run[key].append(res)
            print(json.dumps({k: v for k, v in res.items() if k != "examples"}), flush=True)
    run["prompt_tokens"] = sum(x["prompt_tokens"] for x in run["documents"])
    run["completion_tokens"] = sum(x["completion_tokens"] for x in run["documents"])
    (out / "run.json").write_text(json.dumps(run, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

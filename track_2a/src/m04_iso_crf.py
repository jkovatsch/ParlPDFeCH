# SPDX-License-Identifier: Apache-2.0
"""CRF decoder on out-of-fold (OOF) emissions for E20 version 4 (step 3.9, second decoder of gate 3a).

The rule of gate 3a: use the CRF on the final group only if it is better than the Viterbi decoder of
`m04_iso_import4.py` on the out-of-fold set. It was not better (technical report, chapter 5.3).

The model readout (`m04_iso_torch.py`) gives log probabilities of the 12 answers for each atom. The
CRF learns how to combine them with the block structure. State = the last text answer of the
document (or "start"); "none" and "furniture" do not change the state (E20 v4). Score
of answer y at atom t in state s:
  non-fixed atom:  a * logp[t][y] + b[y]          (furniture not allowed)
  fixed atom:      0 for the fixed answer, not allowed for other answers
  plus, for a text answer y:  start[y] if s = start; stay[y] if s = y; change[s][y] else
        for none:             none_in[s]
Training: maximum likelihood of the reference answers (forward algorithm), L2 0.01, Adam, CPU.
Training documents: OOF readout files with learn = true and a reference; never a document with
learn = false (parliaments of the final groups) and never a document of the measured groups
(cross-fit: the CRF for fold X learns from the readout of fold Y and the other way round).

Usage:
  python3 src/m04_iso_crf.py --train data/iso/pod/foldY_a1 --apply data/iso/pod/foldX_a1 --name crf_foldX_a1
  python3 src/m04_iso_crf.py --train data/iso/pod/foldY_a1,data/iso/pod/foldX_a1 --apply DIR --name crf_g7 --final
  (--train and --apply are relative to the working folder; --ref-groups and --ref-pool to the data root)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m03_iso_jev4 as j4  # noqa: E402
import m03_iso_mass as ms  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402
from m03_iso_paths import DATA  # noqa: E402

V4 = DATA / "iso/v4"
TEXT = list(v4.TEXT)
ALL = list(v4.ANSWERS)             # 13: TEXT, none, furniture
NS = len(TEXT) + 1                 # states: TEXT and start (index len(TEXT))
START = len(TEXT)
VERSION = "crf-v1"


def reference_dirs(ref_groups: str, ref_pool: str):
    with open(ms.GROUPS, newline="", encoding="utf-8") as f:
        group_of = {r["doc_id"]: r["group"] for r in csv.DictReader(f)}
    return group_of, DATA / ref_groups, DATA / ref_pool


def load(dirs: list[str], group_of, ref_g: Path, ref_p: Path, need_ref: bool):
    docs = []
    for d in dirs:
        for p in sorted(Path(d).glob("*.json")):
            if p.name in ("run.json", "config.json"):
                continue
            x = json.loads(p.read_text())
            if x.get("format") != "e20-v4-readout":
                raise SystemExit(f"{p}: not an e20-v4-readout file")
            ref = (ref_g if x["doc_id"] in group_of else ref_p) / f"{x['doc_id']}.json"
            if need_ref and (not x.get("learn", True) or not ref.exists()):
                continue
            ids = ms.atom_ids(x["doc_id"])
            if ids != x["ids"]:
                raise SystemExit(f"{p}: atom ids differ")
            fixed = j4.fixed_answers(x["doc_id"])
            gold = json.loads(ref.read_text())["answers"] if ref.exists() else None
            cols = [ALL.index(a) for a in x["answers"]]
            docs.append({"doc_id": x["doc_id"], "ids": ids, "lp": x["logprobs"], "cols": cols,
                         "fixed": [ALL.index(fixed[a]) if a in fixed else -1 for a in ids], "gold": gold, "src": str(p)})
    return docs


class CRF:
    def __init__(self, torch):
        self.t = torch
        z = lambda *s: torch.zeros(*s, requires_grad=True)  # noqa: E731
        self.a = torch.ones(1, requires_grad=True)
        self.b = z(len(ALL))
        self.start = z(len(TEXT))
        self.stay = z(len(TEXT))
        self.change = z(len(TEXT), len(TEXT))
        self.none_in = z(NS)

    def params(self):
        return [self.a, self.b, self.start, self.stay, self.change, self.none_in]

    def step_scores(self, doc):
        """scores[t][s][y]: score of answer y (index in ALL) at atom t from state s; -inf if not allowed."""
        torch = self.t
        T = len(doc["ids"])
        neg = -1e9
        em = torch.full((T, len(ALL)), neg)
        lp = torch.tensor(doc["lp"], dtype=torch.float32)
        cols = torch.tensor(doc["cols"])
        for t in range(T):
            f = doc["fixed"][t]
            if f >= 0:
                em[t, f] = 0.0
        free = torch.tensor([f < 0 for f in doc["fixed"]])
        e_free = torch.full((T, len(ALL)), neg).index_copy(1, cols, self.a * lp) + self.b
        e_free[:, ALL.index("furniture")] = neg
        em = torch.where(free[:, None], e_free, em)
        k = len(TEXT)
        tr_text = torch.cat([self.change, self.start[None, :]], 0)            # [NS, k]
        eye = torch.zeros(NS, k)
        eye[:k, :k] = torch.eye(k)
        tr_text = tr_text * (1 - eye) + eye * self.stay[None, :]
        tr = torch.cat([tr_text, self.none_in[:, None], torch.zeros(NS, 1)], 1)  # [NS, 13]
        return em[:, None, :] + tr[None, :, :]                                # [T, NS, 13]

    @staticmethod
    def next_state(s: int, y: int) -> int:
        return y if y < len(TEXT) else s

    def logz(self, sc):
        torch = self.t
        k = len(TEXT)
        alpha = torch.full((NS,), -1e9)
        alpha = alpha.index_fill(0, torch.tensor([START]), 0.0)
        for t in range(sc.shape[0]):
            m = alpha[:, None] + sc[t]                       # [NS, 13]
            to_text = torch.logsumexp(m[:, :k], 0)           # new state = y
            stay = torch.logsumexp(m[:, k:], 1)              # new state = s
            alpha = torch.logaddexp(torch.cat([to_text, torch.tensor([-1e9])]), stay)
        return torch.logsumexp(alpha, 0)

    def gold_score(self, sc, gold):
        s, total = START, 0.0
        for t, y in enumerate(gold):
            total = total + sc[t, s, y]
            s = self.next_state(s, y)
        return total

    def viterbi(self, sc) -> list[int]:
        torch = self.t
        k = len(TEXT)
        with torch.no_grad():
            delta = torch.full((NS,), -1e18)
            delta[START] = 0.0
            back = []
            for t in range(sc.shape[0]):
                m = delta[:, None] + sc[t]
                new = torch.full((NS,), -1e18)
                ptr = [None] * NS
                for s2 in range(NS):
                    cands = []
                    if s2 < k:
                        v, i = m[:, s2].max(0)
                        cands.append((v.item(), int(i), s2))
                    for y in range(k, len(ALL)):
                        cands.append((m[s2, y].item(), s2, y))
                    best = max(cands)
                    new[s2] = best[0]
                    ptr[s2] = (best[1], best[2])
                delta = new
                back.append(ptr)
            s = int(delta.argmax())
            out = []
            for ptr in reversed(back):
                prev, y = ptr[s]
                out.append(y)
                s = prev
            return out[::-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True, help="readout directories (comma list)")
    ap.add_argument("--apply", required=True, help="readout directory to decode")
    ap.add_argument("--name", required=True)
    ap.add_argument("--ref-groups", default="iso/v4/ref41")
    ap.add_argument("--ref-pool", default="iso/v4/pool_ref41")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args()
    import torch

    torch.manual_seed(0)
    group_of, ref_g, ref_p = reference_dirs(args.ref_groups, args.ref_pool)
    train = load(args.train.split(","), group_of, ref_g, ref_p, need_ref=True)
    apply = load([args.apply], group_of, ref_g, ref_p, need_ref=False)
    overlap = {d["doc_id"] for d in train} & {d["doc_id"] for d in apply}
    if overlap:
        raise SystemExit(f"documents in train and apply: {sorted(overlap)[:5]}")
    final_docs = v4.final_docs()
    if any(d["doc_id"] in final_docs for d in apply) and not args.final:
        raise SystemExit("final group: only with --final")
    crf = CRF(torch)
    opt = torch.optim.Adam(crf.params(), lr=0.05)
    for ep in range(args.epochs):
        total = 0.0
        for d in train:
            gold = [ALL.index(a) for a in d["gold"]]
            sc = crf.step_scores(d)
            nll = crf.logz(sc) - crf.gold_score(sc, gold)
            loss = nll / len(gold) + 0.01 * sum((p ** 2).sum() for p in crf.params()[1:])
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += nll.item()
        if ep % 5 == 0 or ep == args.epochs - 1:
            print(f"epoch {ep + 1}: nll per document {total / max(len(train), 1):.3f}", flush=True)
    out = V4 / f"hyp_{args.name}"
    for d in apply:
        ys = crf.viterbi(crf.step_scores(d))
        v4.write(out, d["doc_id"], [ALL[y] for y in ys], f"crf:{args.name}", d["src"])
    (out / "run.json").write_text(json.dumps({
        "version": VERSION, "train": args.train, "apply": args.apply, "train_documents": len(train),
        "applied_documents": len(apply), "epochs": args.epochs, "a": crf.a.item(),
        "b": [round(v, 4) for v in crf.b.tolist()]}, indent=1), encoding="utf-8")
    print(f"CRF: {len(train)} training documents; {len(apply)} documents -> {out}")


if __name__ == "__main__":
    main()

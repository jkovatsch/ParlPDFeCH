# SPDX-License-Identifier: Apache-2.0
"""Isolation readout at the level of E20 version 4 on a rented GPU (PyTorch, step 3.9).

Version 2 (bundle v4b, 05.10.2026). The earlier version for the bundles v1 to v4a is not in this
repository.
The input is a bundle of token ids (`m04_iso_bundle.py --schema v4b`), so this script needs no
tokenizer and no document text. Apertus-v1.5-8B text branch in bf16 (E15); LoRA adapters in float32.
LoRA on all linear layers of the upper --num-layers layers, rank --rank, output scale --scale
(PEFT lora_alpha = scale * rank).

Commands:
  env       versions and GPU
  logprobs  next-token log probabilities for token sequences (equivalence check with other backends)
  train     train, monitor, choose a checkpoint, and read out the fold documents with it
  readout   read out documents of a bundle with an adapter

Selection of the documents (E29; rule of the project: no method learns from a document of a
parliament of the final group):
  readout   documents of the excluded groups (--exclude-homes 3,5: pool home 3 or 5, group documents
            of groups 3 and 5), also documents with learn = false (parliaments of the final groups)
  monitor   documents with learn = true, part V and home "free" (no group document and no training
            document of the same parliament; the script stops if a parliament is in two sets)
  train     documents with learn = true, part T or G, not readout
Loss: cross entropy over the 12 answers at the readout positions; fixed atoms (target -1) have no
loss; the mean over the atoms of a document, then the mean over the documents of an update.
--curriculum: epoch 1 in the order of increasing length, the other epochs in random order.
Checkpoint rule (fixed before the runs): the monitor loss after each --monitor-every updates and
at the end of each epoch; the checkpoint with the lowest monitor loss is used (on a tie the earlier
one). Only this checkpoint reads out the fold documents.

Readout file (one per document): format "e20-v4-readout", answers (the 12 answers), ids, logprobs
(one row of 12 log probabilities for each atom), fixed, learn, checkpoint, bundle SHA-256.

Usage on the pod:
  python m04_iso_torch.py train --bundle bundle/v4b --model model --name foldY_a1 --exclude-homes 3,5
  python m04_iso_torch.py readout --bundle bundle/v4b_g7 --model model --adapter adapters/final/u0400 --out out/g7 --final
  (the adapter folder name is an example)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

FORMAT = "e20-v4-readout"
DEVICE = os.environ.get("ISO_DEVICE") or "cuda"   # "cpu" only for the local test with a small random model


def load_jsonl(p: Path) -> list[dict]:
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def load_model(path: str):
    import torch
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, attn_implementation="sdpa",
                                                 device_map=DEVICE)
    model.eval()
    return model


def lora_targets(model) -> list[str]:
    import torch

    names = {n.split(".")[-1] for n, m in model.model.layers[0].named_modules() if isinstance(m, torch.nn.Linear)}
    return sorted(names)


def cmd_env(args) -> None:
    import peft
    import torch
    import transformers

    print(json.dumps({"torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__,
                      "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                      "memory_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)}))


def cmd_logprobs(args) -> None:
    import torch

    model = load_model(args.model)
    seqs = json.loads(Path(args.ids).read_text())
    res = []
    with torch.no_grad():
        for ids in seqs:
            lg = model(input_ids=torch.tensor([ids], device=DEVICE)).logits[0].float()
            lp = torch.log_softmax(lg, dim=-1)
            top = torch.topk(lp, 10, dim=-1)
            res.append({"top_ids": top.indices.tolist(), "top_lp": top.values.tolist(),
                        "actual": [lp[i, ids[i + 1]].item() for i in range(len(ids) - 1)]})
    Path(args.out).write_text(json.dumps(res))
    print(f"wrote {args.out}")


def schedule(warmup: int, total: int):
    def f(step: int) -> float:
        if step < warmup:
            return (step + 1) / max(warmup, 1)
        t = min(step - warmup, total) / max(total, 1)
        return 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * t))
    return f


def select(items: list[dict], exclude: set[str]):
    ev = exclude | {"g" + h for h in exclude}
    readout = [x for x in items if x["home"] in ev]
    monitor = [x for x in items if x["learn"] and x["part"] == "V" and x["home"] == "free"]
    train = [x for x in items if x["learn"] and x["part"] != "V" and x["home"] not in ev]
    tb = {x["body_key"] for x in train}
    for name, part in (("monitor", monitor), ("readout", readout)):
        both = tb & {x["body_key"] for x in part}
        if both:
            sys.exit(f"parliaments in train and {name}: {sorted(both)}")
    return train, monitor, readout


def write_readout(out: Path, x: dict, lp, answers: list[str], checkpoint: str, sha: str) -> None:
    (out / f"{x['doc_id']}.json").write_text(json.dumps({
        "doc_id": x["doc_id"], "format": FORMAT, "answers": answers, "ids": x["ids"],
        "logprobs": [[round(v, 5) for v in row] for row in lp], "fixed": x["fixed"], "learn": x.get("learn", True),
        "home": x.get("home"), "group": x.get("group"), "checkpoint": checkpoint, "bundle_sha256": sha}))


def cmd_train(args) -> None:
    import torch
    from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
    from safetensors.torch import load_file

    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("format") != "v3h" or len(meta["answers"]) != 12:
        sys.exit(f"bundle {bundle}: format {meta.get('format')}, {len(meta['answers'])} answers; expected v3h and 12")
    excluded = {h for h in args.exclude_homes.split(",") if h}
    items = load_jsonl(bundle / "docs.jsonl")
    long = [x["doc_id"] for x in items if len(x["seq"]) > args.max_length]
    if long:
        sys.exit(f"documents longer than --max-length {args.max_length}: {long} (E18: never cut)")
    train, monitor, readout = select(items, excluded)
    out = Path(args.out_root) / args.name
    out.mkdir(parents=True, exist_ok=True)
    per_epoch = math.ceil(len(train) / args.grad_accum)
    updates = per_epoch * args.epochs
    config = {**vars(args), "version": 2, "excluded_homes": sorted(excluded), "bundle_sha256": meta["sha256"],
              "bundle_task": meta.get("task"), "hints": meta.get("hints"), "answers": meta["answers"],
              "train_documents": [x["doc_id"] for x in train], "monitor_documents": [x["doc_id"] for x in monitor],
              "readout_documents": [x["doc_id"] for x in readout],
              "train_tokens": sum(len(x["seq"]) for x in train), "updates": updates,
              "checkpoint_rule": "lowest monitor loss (document mean of the atom mean cross entropy); tie: earlier"}
    (out / "config.json").write_text(json.dumps(config, indent=1))
    print(f"training {len(train)} documents / {config['train_tokens']} tokens / {updates} updates; "
          f"monitor {len(monitor)}; readout {len(readout)}", flush=True)

    model = load_model(args.model)
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    n_layers = model.config.num_hidden_layers
    cfg = LoraConfig(r=args.rank, lora_alpha=args.scale * args.rank, lora_dropout=0.0, bias="none",
                     target_modules=lora_targets(model), layers_to_transform=list(range(n_layers - args.num_layers, n_layers)),
                     layers_pattern="layers")
    pm = get_peft_model(model, cfg)
    pm.print_trainable_parameters()
    base = pm.base_model.model
    w_ans = base.lm_head.weight[torch.tensor(meta["answer_ids"], device=DEVICE)].detach().float()

    def option_logits(x):
        h = base.model(input_ids=torch.tensor([x["seq"][:-1]], device=DEVICE)).last_hidden_state[0]
        return h[torch.tensor(x["pos"], device=DEVICE)].float() @ w_ans.T

    def doc_loss(x):
        t = torch.tensor(x["target"], device=DEVICE)
        m = t >= 0
        lg = option_logits(x)
        return torch.nn.functional.cross_entropy(lg[m], t[m], reduction="mean"), lg, t, m

    train = [x for x in train if any(t >= 0 for t in x["target"])]
    params = [p for p in pm.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=args.lr)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, schedule(args.warmup, updates))
    log = open(out / "protocol.jsonl", "w")

    def write(kind: str, info: dict) -> None:
        log.write(json.dumps({"kind": kind, **info}) + "\n")
        log.flush()
        print(kind, json.dumps(info), flush=True)

    def run_monitor() -> dict:
        pm.eval()
        losses, right, n = [], 0, 0
        with torch.no_grad():
            for x in monitor:
                if not any(t >= 0 for t in x["target"]):
                    continue
                loss, lg, t, m = doc_loss(x)
                losses.append(loss.item())
                right += (lg[m].argmax(-1) == t[m]).sum().item()
                n += int(m.sum().item())
        pm.train()
        return {"val_loss": sum(losses) / max(len(losses), 1), "val_accuracy": right / max(n, 1), "val_atoms": n}

    checkpoints = []

    def checkpoint(upd: int, ep: int) -> None:
        r = run_monitor()
        name = f"u{upd:04d}"
        pm.save_pretrained(str(out / name))
        checkpoints.append({"name": name, "update": upd, "epoch": ep, **r})
        write("monitor", {"update": upd, "epoch": ep, "checkpoint": name, **r})

    write("monitor", {"update": 0, **run_monitor()})
    pm.train()
    t0, upd = time.time(), 0
    for ep in range(args.epochs):
        order = train[:]
        if args.curriculum and ep == 0:
            order.sort(key=lambda x: (len(x["seq"]), x["doc_id"]))
        else:
            rng.shuffle(order)
        for s in range(0, len(order), args.grad_accum):
            batch = order[s: s + args.grad_accum]
            total = 0.0
            for x in batch:
                loss = doc_loss(x)[0]
                (loss / len(batch)).backward()
                total += loss.item()
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            upd += 1
            if upd % 10 == 0 or upd == 1:
                write("train", {"update": upd, "epoch": ep + 1, "loss": total / len(batch), "lr": sched.get_last_lr()[0],
                                "seconds": round(time.time() - t0, 1),
                                "peak_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2) if DEVICE == "cuda" else 0})
            if upd % args.monitor_every == 0:
                checkpoint(upd, ep + 1)
        if upd % args.monitor_every != 0:
            checkpoint(upd, ep + 1)
    train_seconds = round(time.time() - t0, 1)
    best = min(checkpoints, key=lambda c: (c["val_loss"], c["update"]))
    write("chosen", best)
    set_peft_model_state_dict(pm, load_file(str(out / best["name"] / "adapter_model.safetensors")))
    pm.eval()
    rdir = out / f"readout_{best['name']}"
    rdir.mkdir(exist_ok=True)
    with torch.no_grad():
        for x in readout:
            lp = torch.log_softmax(option_logits(x), dim=-1).tolist()
            write_readout(rdir, x, lp, meta["answers"], f"{args.name}/{best['name']}", meta["sha256"]["docs.jsonl"])
    config.update({"train_seconds": train_seconds, "seconds": round(time.time() - t0, 1), "checkpoints": checkpoints,
                   "chosen": best, "readout_dir": str(rdir), "lora_targets": lora_targets(model)})
    (out / "config.json").write_text(json.dumps(config, indent=1))
    print(f"chosen {best['name']} (val_loss {best['val_loss']:.4f}); readout {len(readout)} documents -> {rdir}", flush=True)


def cmd_readout(args) -> None:
    import torch

    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("final") and not args.final:
        sys.exit("bundle of a final group: only with --final (final measurement)")
    items = load_jsonl(bundle / "docs.jsonl")
    model = load_model(args.model)
    from peft import PeftModel

    model = PeftModel.from_pretrained(model, args.adapter)
    inner = model.base_model.model.model
    lm_head = model.base_model.model.lm_head
    model.eval()
    w_ans = lm_head.weight[torch.tensor(meta["answer_ids"], device=DEVICE)].detach().float()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with torch.no_grad():
        for x in items:
            h = inner(input_ids=torch.tensor([x["seq"][:-1]], device=DEVICE)).last_hidden_state[0]
            lp = torch.log_softmax(h[torch.tensor(x["pos"], device=DEVICE)].float() @ w_ans.T, dim=-1).tolist()
            write_readout(out, x, lp, meta["answers"], args.adapter, meta["sha256"]["docs.jsonl"])
    (out / "run.json").write_text(json.dumps({**vars(args), "documents": len(items), "seconds": round(time.time() - t0, 1),
                                              "bundle_sha256": meta["sha256"]}, indent=1))
    print(f"readout {len(items)} documents -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("env")
    p = sub.add_parser("logprobs")
    p.add_argument("--model", required=True)
    p.add_argument("--ids", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("train")
    p.add_argument("--bundle", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--out-root", default="adapters")
    p.add_argument("--exclude-homes", required=True, help="groups of the fold; '' for the final model")
    p.add_argument("--max-length", type=int, default=40000)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--grad-accum", type=int, default=2)
    p.add_argument("--monitor-every", type=int, default=40)
    p.add_argument("--curriculum", action="store_true")
    p.add_argument("--num-layers", type=int, default=16)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--scale", type=float, default=20.0)
    p.add_argument("--seed", type=int, default=42)
    p = sub.add_parser("readout")
    p.add_argument("--bundle", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--final", action="store_true")
    args = ap.parse_args()
    {"env": cmd_env, "logprobs": cmd_logprobs, "train": cmd_train, "readout": cmd_readout}[args.cmd](args)


if __name__ == "__main__":
    main()

# Earlier Apertus head of task R2 (path 2), 12.10.2026

History: the Apertus head of task R2 (path 2), state of 12.10.2026. Not the product of this version; see [../../README.md](../../README.md), chapter "Use of Apertus and of other models", and [../prompts/](../prompts/README.md).

This folder holds the code of the trained head of path 2: code only. It holds no weights of Apertus, no weights of the head, no hidden states and no document text. The earlier converter of 12.10.2026 does not use the R2 head. The reader copy in `../converter_gj/` imports 5 modules of this folder: `m02_dokumente_extrakt`, `m02_dokumente_profil`, `m04_kern`, `m05_cls_apertus` and `m05_cls_data`.

## What the head does

- Task R2: does the document hold a response of the executive to a parliamentary affair (yes or no)? In eCH-0295 (I95), "yes" makes the document a source of `ResponseStep.texts`.
- Apertus-v1.5-8B in bf16 reads the whole document and then the question (`../prompts/r2_v1_de.txt`). All 32 decoder layers run. There is no quantization, and the weights of Apertus do not change.
- The code keeps the hidden state after decoder layer 16 at the last prompt token (4,096 values, stored as float16).
- The head is a softmax regression with an L2 penalty (C = 0.001) on this state, after a z-score. q is the probability of "yes".
- Decision: "yes" if q is 0.5 or more. Value status: `certain` if the larger of q and 1 − q is 0.6 or more, else `unsure`.
- Design on development documents only (`dev`, 800 rows), with cross-validation by parliament.

## What it reads

| Input | Where | In this repository? |
|---|---|---|
| Weights of Apertus-v1.5-8B, bf16 | Own download (https://huggingface.co/swiss-ai/Apertus-v1.5-8B) | No |
| Text of each document | The text of the Docling atoms if they exist, else the text field `docs.text` of the OpenParlData export. No other export field goes into the model. | No |
| Hidden states | Output of `m05_cls_it2_states.py` (Mac, MLX) or `m07_h_vm_states.py` (VM, PyTorch, CUDA GPU) | No |
| Head weights | `heads/r2_head.npz` of the private project (SHA-256 `d6a9667f…`) | No |
| Freeze record | `frozen_it2.json` of the private project (SHA-256 `9517c31d…`) | No |

The code reads its files below the folder layout of the private project (`daten/cls/...`).

## Files

| File | Content |
|---|---|
| `m05_cls_it2_head.py` | Design, training, freeze and prediction of the head (`predict --task r2 --states DIR --out FILE`); self-check on synthetic data (`selftest`) |
| `m05_cls_it2_states.py` | Hidden states with MLX on a Mac: one forward pass for each document, prefill in chunks of 2,048 tokens |
| `m07_h_vm_states.py` | The same hidden states with PyTorch in the VM; equality check against the Mac |
| `m05_cls_apertus.py` | Prompt templates, prompt build with the chat template, constrained readout (zero-shot comparison) |
| `m05_cls_data.py` | Data sets, splits and guards |
| other files | Modules that these files import |

`make head-selftest` (in `track_2a/`) runs the self-check on synthetic data. It needs numpy and scipy (`make setup` downloads them). A run on documents needs the weights of Apertus and of the head, and a Mac with MLX or a CUDA GPU.

## Gate state on 12.10.2026

On 12.10.2026, the gate of path 2 was OPEN. The final run of the head on the test parliaments was sealed on 12.10.2026. It has no measurement, because the blind check of the reference did not take place.

The values of 12.10.2026 are in [`../../results/stored_results.json`](../../results/stored_results.json): the validation values and the K7 categories (part of task R2), and the equality check of the VM and the Mac (part "Infrastructure"). They are history, not results of the one fixed run of 13.10.2026.

The K7 categories are local document categories that give only the name of an affair type. The source label of R2 comes from the local category, and these documents have label noise in the class `no`.

Task R1 (the recommendation of the executive) stopped with a negative result. The part "Path 2: task R1" of the same file gives the values and the causes.

Sources: the report of path 2, iteration 2, of the private project (SHA-256 `43d4491084d57d8c3d5897bbd46b6ca4dcd925372916b61f3cd08d18b5fde7a2`), chapters 0, 3, 6.2 and 10; the equality check (`19d7eaf0…`).

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. No human examined it.
- On 15.10.2026, an AI agent (Claude Opus 5.5) marked the text as history and corrected 2 references. It removed the value table; its values are in the stored results. No human examined it.

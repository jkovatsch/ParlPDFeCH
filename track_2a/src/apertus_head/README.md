# Apertus head of path 2 (task R2)

This folder holds the code of the trained head of path 2: code only. It holds no weights of Apertus, no weights of the head, no hidden states and no document text. The converter does not use this code.

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

## Gate state and values

The gate of path 2 is OPEN. The final run of the head on the test parliaments (1,523 documents, 12.10.2026) is sealed. It has no measurement, because the blind check of the reference did not take place.

Values on the validation set (information, balanced accuracy):

| Set | Head | Zero-shot Apertus readout | Best rule (`s1_answer`) |
|---|---|---|---|
| All validation documents (920) | 0.919 | 0.899 | 0.932 |
| Without the K7 categories (714) | 0.980 | 0.953 | 0.965 |

The K7 categories are local document categories that give only the name of an affair type. The source label of R2 comes from the local category, and these documents have label noise in the class `no`.

Equality check of the two places: on 10 R2 rows, the VM and the Mac gave 10 of 10 equal decisions. The largest difference of q was 0.011279 (limit 0.02).

Task R1 (the recommendation of the executive) stopped with a negative result. `../../README.md` gives the values and the causes.

Sources: the report of path 2, iteration 2, of the private project (SHA-256 `43d4491084d57d8c3d5897bbd46b6ca4dcd925372916b61f3cd08d18b5fde7a2`), chapters 0, 3, 6.2 and 10; the equality check (`19d7eaf0…`).

## About this text

- Language: English, to the rules of ASD-STE100 (Issue 9).
- Authoring: an AI agent (Claude Opus 5.5) wrote this text on 12.10.2026. No human examined it.

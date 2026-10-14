#!/usr/bin/env python3
"""Worker of the ParlPDFeCH package: the interface of a states provider (an interface only).

Status of all results: EXCEPTION, NOT RELEASED. No human checked this file.

A states provider gives the Apertus states of one new document to the worker. The worker of stage P0b
uses the kind "none" only. The kinds "stored" and "remote" are NOT IMPLEMENTED: this file names what
they must deliver, so that a later stage can add them with no change of the HTTP API and of the worker
command. This file starts no model and opens no connection.

Kinds
  none    No states. The stage apertus has the state skipped. Each label comes from a code rule.
  stored  NOT IMPLEMENTED. A states file that was made before for exactly this block file.
  remote  NOT IMPLEMENTED. A service of the user that runs Apertus-v1.5-8B and returns a states file.

What a provider gets (the request)
  block_file        the block file of the document (interface 2 of the converter): doc_id, pdf_sha256,
                    blocks[{block, page, docling_label, text, atoms, char_start, char_end}]
  block_file_sha256 the SHA-256 of the block file bytes. States belong to one block file: another block
                    list gives other prompts.
  layers            the decoder layers that the read-out heads use. The frozen design reads layer 20.
                    The states files of the project hold the layers 8, 12, 16, 20, 24, 28 and 32.

What a provider must do with the request
  1. Build the prompt item of the document as the converter does it (module m10_prompts of the
     converter, version m10-prompts-1, template r2_v1_de): one prefix (the chat template text with one
     line for each Docling block: "[B<n> | S.<page> | <Docling label>] <block text>") and the
     suffixes in this sequence: "D1" (the document question), then "B<n>" for each block (the block
     question with the first 12 words of the block).
  2. Run Apertus-v1.5-8B in bf16 with no quantization: token ids = tokens(prefix) + tokens(suffix),
     each with no added special token; prefill of the prefix one time; one forward pass for each
     suffix on the prefix cache; read the residual state after decoder layer k at the last suffix
     token (a hook on the layer k - 1 of the layer list; not the key output_hidden_states).
  3. Return one states file in the form of the converter (module m10_vm_states, interface 6).

What a provider must deliver (the result)
  One file <doc>.npz with these keys (numpy):
    suffix_ids                str      ["D1", "B1", ..., "Bn"], the sequence of the block file
    layers                    int16    the layers of the states; layer 20 must be one of them
    states                    float16  [n_suffix, n_layers, hidden]; each value is finite
    letter_logprobs           float32  [n_suffix, 6]
    n_prefix_tokens, n_suffix_tokens, prefix_text_sha256, suffix_text_sha256, prefix_tokens_sha256,
    suffix_tokens_sha256, template_id, template_sha256, model, model_fingerprint, code_sha256, dtype
  and these facts for the record: the kind of the provider, the model name and revision, the dtype,
  the device, the seconds, and the SHA-256 of the states file.
  A document with more than 32,768 prefix tokens gets no states (the rule of the converter).

What the worker does with the result (a later stage; not built)
  It checks suffix_ids against the block file, the layers, the form and the finite values (function
  read_states of the design module of the converter), then it calls the decision function of the
  candidate in place of the floor decisions, and it writes apertus "stored" or a new value into the
  last line and into convert.json. The R2 value (final check, another prompt and layer 16) is a second
  request of the same kind. The view then names the source of each label as it does for a sample.

Open points for that stage: the read-out heads were fitted on documents with an export record and on
block files of the measured Docling settings; a states file of another computer is not examined.
"""

from __future__ import annotations

from pathlib import Path

KINDS = ("none", "stored", "remote")
DESIGN_LAYER = 20
STATE_KEYS = ("suffix_ids", "layers", "states", "letter_logprobs")


class StatesProvider:
    """The interface. states_for() returns None (no states) or a dict
    {"kind", "states_file": Path, "sha256", "layers", "model", "dtype", "device", "seconds"}."""

    kind = "none"

    def states_for(self, block_file: Path, block_file_sha256: str, work_dir: Path, layers: tuple[int, ...] = (DESIGN_LAYER,)):
        raise NotImplementedError


class NoStates(StatesProvider):
    """Kind none: the package runs no model and holds no states of a new document."""

    kind = "none"

    def states_for(self, block_file: Path, block_file_sha256: str, work_dir: Path, layers: tuple[int, ...] = (DESIGN_LAYER,)):
        return None


def provider(kind: str = "none") -> StatesProvider:
    """The provider of a kind. Only the kind none exists. Each other kind stops with NotImplementedError."""
    if kind == "none":
        return NoStates()
    if kind in KINDS:
        raise NotImplementedError(f"states provider {kind}: NOT IMPLEMENTED in stage P0b (an interface only)")
    raise ValueError(f"states provider {kind!r}: not one of {KINDS}")

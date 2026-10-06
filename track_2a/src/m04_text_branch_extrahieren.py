# SPDX-License-Identifier: Apache-2.0
"""Löst den Text-Teil aus swiss-ai/Apertus-v1.5-8B heraus.

Apertus 1.5 ist ein Omni-Modell (Text, Bild, Ton, model_type «apertus1p5»), das
mlx-lm nicht direkt lädt. Der Text-Teil hat dieselbe Architektur wie Apertus 1.0
(model_type «apertus»), die mlx-lm kennt. Das Skript

- übernimmt nur die Gewichte unter model.language_model.* und lm_head.weight,
- benennt sie in das Schema von Apertus 1.0 um (model.language_model.* -> model.*),
- kürzt die Einbettung auf die 131'072 Text-Tokens (darüber liegen nur Bild- und
  Ton-Tokens; der Ausgabekopf hat schon 131'072 Ausgaben),
- schreibt eine Konfiguration mit model_type «apertus» und übernimmt Tokenizer,
  Chat-Vorlage, Lizenz und Nutzungsbedingungen.

Ergebnis: <data>/modelle/apertus-v1.5-8b-text-bf16 im Hugging-Face-Format. Die Gewichte bleiben
unverändert (bf16); das Projekt quantisiert sie nicht.

Quelle: der Download von swiss-ai/Apertus-v1.5-8B (Hugging Face, eigenes Konto, Zustimmung zur
Lizenz und zur Acceptable Use Policy). Weder die Quelle noch das Ergebnis gehören ins Repository
(.gitignore und .dockerignore schliessen data/ aus).

Aufruf (im Ordner track_2a): python src/m04_text_branch_extrahieren.py [--quelle ORDNER] [--ziel ORDNER]
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

import mlx.core as mx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, MODEL  # noqa: E402

QUELLE = DATA / "modelle/Apertus-v1.5-8B"
ZIEL = MODEL
TEXT_VOKABULAR = 131072
PRAEFIX = "model.language_model."
BEIZULEGEN = [
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "chat_template.jinja",
    "generation_config.json",
    "LICENSE.txt",
    "USAGE_POLICY.pdf",
    "PRIVACY_POLICY.pdf",
]


def text_konfiguration(omni: dict) -> dict:
    tc = dict(omni["text_config"])
    rope = tc.pop("rope_parameters")
    tc.pop("output_vocab_size", None)
    tc.update(
        model_type="apertus",
        architectures=["ApertusForCausalLM"],
        vocab_size=TEXT_VOKABULAR,
        # Ohne transformers_version hält transformers den Tokenizer für einen alten
        # Mistral-Tokenizer und warnt fälschlich. Wert aus der
        # Omni-Konfiguration bzw. dem Stand, mit dem swiss-ai die Datei erzeugt hat.
        transformers_version=omni.get("transformers_version", "5.14.0.dev0"),
        rope_theta=rope["rope_theta"],
        rope_scaling={k: v for k, v in rope.items() if k != "rope_theta"},
        text_branch_source=(
            "Text-Teil von swiss-ai/Apertus-v1.5-8B, unverändert in bf16; Einbettung "
            "auf die 131072 Text-Zeilen gekürzt, Bild- und Ton-Teile weggelassen."
        ),
    )
    return tc


def neuer_name(alt: str) -> str | None:
    if alt.startswith(PRAEFIX):
        return "model." + alt[len(PRAEFIX):]
    if alt == "lm_head.weight":
        return alt
    return None


def main() -> None:
    global QUELLE, ZIEL
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quelle", type=Path, default=QUELLE, help="Ordner des Downloads von Apertus-v1.5-8B")
    ap.add_argument("--ziel", type=Path, default=ZIEL, help="Ordner für den Text-Teil")
    args = ap.parse_args()
    QUELLE, ZIEL = args.quelle, args.ziel
    omni = json.loads((QUELLE / "config.json").read_text())
    index = json.loads((QUELLE / "model.safetensors.index.json").read_text())
    teile = sorted(
        {f for k, f in index["weight_map"].items() if neuer_name(k) is not None}
    )
    ZIEL.mkdir(parents=True, exist_ok=True)

    gewichtskarte: dict[str, str] = {}
    gesamt_bytes = 0
    for nr, teil in enumerate(teile, 1):
        gewichte = mx.load(str(QUELLE / teil))
        aus = {}
        for alt, wert in gewichte.items():
            neu = neuer_name(alt)
            if neu is None:
                continue
            if neu == "model.embed_tokens.weight":
                wert = wert[:TEXT_VOKABULAR]
            aus[neu] = wert
        name = f"model-{nr:05d}-of-{len(teile):05d}.safetensors"
        mx.save_safetensors(str(ZIEL / name), aus, metadata={"format": "pt"})
        for k, v in aus.items():
            gewichtskarte[k] = name
            gesamt_bytes += v.nbytes
        print(f"{teil} -> {name}: {len(aus)} Tensoren")
        del gewichte, aus

    erwartet = 1 + 1 + 1 + 14 * omni["text_config"]["num_hidden_layers"]
    assert len(gewichtskarte) == erwartet, (len(gewichtskarte), erwartet)
    for k in ("model.embed_tokens.weight", "lm_head.weight", "model.norm.weight"):
        assert k in gewichtskarte, k

    (ZIEL / "model.safetensors.index.json").write_text(
        json.dumps(
            {"metadata": {"total_size": gesamt_bytes}, "weight_map": gewichtskarte},
            indent=2,
        )
    )
    (ZIEL / "config.json").write_text(
        json.dumps(text_konfiguration(omni), indent=2, ensure_ascii=False)
    )
    for datei in BEIZULEGEN:
        shutil.copy2(QUELLE / datei, ZIEL / datei)

    form = {
        k: mx.load(str(ZIEL / gewichtskarte[k]))[k].shape
        for k in ("model.embed_tokens.weight", "lm_head.weight")
    }
    print(f"{len(gewichtskarte)} Tensoren, {gesamt_bytes / 1e9:.2f} GB, Formen: {form}")


if __name__ == "__main__":
    main()

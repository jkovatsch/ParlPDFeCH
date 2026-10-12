# SPDX-License-Identifier: Apache-2.0
"""Gemeinsame Bausteine für Training und Auswertung, für alle Iterationen (ab Iteration 2).

Verallgemeinerung von m04_iter1_kern.py (das für den Lauf iter1/lauf1 unverändert bleibt):
- Iteration wählbar (Beispiel-, Adapter- und Laufordner aus ordner())
- variable Anzahl Optionen (bis zu len(BUCHSTABEN), jeder Buchstabe ein Token)
- mlx wird erst beim Auslesen geladen, damit Prüfungen und das Neurechnen aus Logits ohne
  Modell und ohne GPU laufen

Training und Auslesen müssen dieselbe Eingabe sehen. Deshalb wird die Chat-Vorlage nur
hier angewendet: eigener kurzer Systemprompt (steht in jedem Beispiel), Denkmodus
ausdrücklich aus (enable_thinking=False; mlx-lm würde ihn sonst einschalten,
abschnitte/technik.md).
"""

import json
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
# Volle Präzision (bf16), keine Quantisierung: Entscheid des Autors 05.10.2026 (E15).
# Die 4-bit-Fassung (apertus-v1.5-8b-text-mlx-4bit) diente nur Rauchtest und Iteration 1.
MODELL = WURZEL / "daten/modelle/apertus-v1.5-8b-text-bf16"
BUCHSTABEN = "ABCDEFGHIJKLMNOP"
# max_seq_length im Training; längere Beispiele werden abgewiesen (nie gekürzt).
# Über PARL_MAX_LAENGE einstellbar: ganze Dokumente brauchen mehr als 1024 (E18).
MAX_LAENGE = int(__import__("os").environ.get("PARL_MAX_LAENGE", "1024"))



# Speicherobergrenzen für MLX. Hintergrund: Am 04.10.2026 löste ein Training einen Kernel-Panic
# im Grafiktreiber aus («completeMemory() prepare count underflow», IOGPUMemory.cpp:550).
# mlx-lm sperrt sonst rund 75 % des Arbeitsspeichers als nicht auslagerbaren «wired»-Speicher;
# wird der Rest knapp, kann macOS nichts freigeben und der Treiber stürzt ab (mlx-lm Issue 883,
# mlx Issue 3186). Mit tieferer Wired-Grenze und Speichergrenze bricht MLX stattdessen ab.
# bf16: Gewichte 16,1 GB. Speichergrenze so, dass dem System rund 5 GB bleiben (32 GB Mac mini);
# Training und grosse Auswertungen nur allein laufen lassen.
WIRED_GB = 10.0
SPEICHER_GB = 27.0
CACHE_GB = 1.0


def speicher_begrenzen(wired_gb: float = WIRED_GB, speicher_gb: float = SPEICHER_GB,
                       cache_gb: float = CACHE_GB) -> dict:
    """Setzt Wired-, Speicher- und Cache-Grenze und verhindert, dass mlx-lm sie wieder anhebt."""
    import mlx.core as mx
    import mlx_lm.tuner.trainer as trainer
    import mlx_lm.generate as generate

    gb = 1024 ** 3
    mx.set_wired_limit(int(wired_gb * gb))
    mx.set_memory_limit(int(speicher_gb * gb))
    mx.set_cache_limit(int(cache_gb * gb))
    for modul in (trainer, generate):
        if hasattr(modul, "maybe_set_recommended_wired_limit"):
            modul.maybe_set_recommended_wired_limit = lambda *a, **k: None
    return {"wired_gb": wired_gb, "speicher_gb": speicher_gb, "cache_gb": cache_gb}


def ordner(iteration: str) -> dict[str, Path]:
    """Standardordner einer Iteration (z. B. 'iter1', 'iter2')."""
    return {
        "beispiele": WURZEL / "daten/beispiele" / iteration,
        "adapter": WURZEL / "daten/adapter" / iteration,
        "laeufe": WURZEL / "daten/laeufe" / iteration,
    }


def lies_jsonl(pfad: Path) -> list[dict]:
    with open(pfad, encoding="utf-8") as f:
        return [json.loads(z) for z in f if z.strip()]


def nachrichten(b: dict, mit_antwort: bool) -> list[dict]:
    m = [
        {"role": "system", "content": b["system"]},
        {"role": "user", "content": b["prompt"]},
    ]
    if mit_antwort:
        m.append({"role": "assistant", "content": b["completion"]})
    return m


def prompt_ids(tok, b: dict) -> list[int]:
    return list(
        tok.apply_chat_template(
            nachrichten(b, False),
            add_generation_prompt=True,
            enable_thinking=False,
            return_dict=False,
        )
    )


def buchstaben_ids(tok, n: int = len(BUCHSTABEN)) -> list[int]:
    """Token-IDs der ersten n Buchstaben; prüft, dass jeder Buchstabe genau ein Token ist."""
    assert n <= len(BUCHSTABEN), f"höchstens {len(BUCHSTABEN)} Optionen"
    ids = []
    for b in BUCHSTABEN[:n]:
        t = tok.encode(b, add_special_tokens=False)
        assert len(t) == 1, (b, t)
        ids.append(t[0])
    return ids


def trainingsbeispiel(tok, b: dict, bids: list[int]) -> tuple[list[int], int]:
    """Gibt (Tokens, Offset) zurück. Offset = Position des Antwortbuchstabens.

    Prüft, dass die vollständige Folge mit der Auslese-Eingabe beginnt und direkt danach
    der richtige Buchstabe steht, dass der Buchstabe zu einer angebotenen Option gehört,
    dass diese Option das Label ist (wenn das Beispiel ein Feld «label» hat) und dass die
    Folge höchstens MAX_LAENGE Tokens hat.
    """
    n = len(b["optionen"])
    i = BUCHSTABEN.index(b["completion"])
    assert i < n, (b.get("id"), b["completion"], n)
    if "label" in b:
        assert b["optionen"][i] == b["label"], (b.get("id"), b["completion"], b["label"])
    p = prompt_ids(tok, b)
    voll = list(
        tok.apply_chat_template(
            nachrichten(b, True), enable_thinking=False, return_dict=False
        )
    )
    assert voll[: len(p)] == p, "Trainingsfolge beginnt nicht mit der Auslese-Eingabe"
    richtig = bids[BUCHSTABEN.index(b["completion"])]
    assert voll[len(p)] == richtig, (voll[len(p)], richtig)
    assert len(voll) <= MAX_LAENGE, f"Beispiel {b.get('id')} hat {len(voll)} Tokens"
    return voll, len(p)


def options_logits(model, ids: list[int], bids: list[int], n: int):
    """Logits der n Optionsbuchstaben an der Antwortstelle und Anteil der Gesamtmasse."""
    import mlx.core as mx

    # Ausgabekopf nur an der Antwortstelle (gleiche Werte wie model(...)[0, -1]); bei ganzen
    # Dokumenten (E18, bis 8192 Tokens) spart das rund 2 GB Logits über alle Positionen.
    # Ausgabekopf in float32 (05.10.2026): in bf16 sind Logits um 16-32 nur auf 0,125 genau,
    # das vergröbert die ausgelesenen Wahrscheinlichkeiten. Kostet nur eine Gewichtskopie (2 GB).
    h = model.model(mx.array([ids]))[:, -1].astype(mx.float32)
    logits = (h @ model.lm_head.weight.astype(mx.float32).T)[0]
    auswahl = logits[mx.array(bids[:n])]
    masse = mx.sum(mx.softmax(logits)[mx.array(bids[:n])])
    mx.eval(auswahl, masse)
    return auswahl, float(masse)


def attention_in_stuecken(stueck: int = 512) -> None:
    """Attention im Training in Abfrage-Stücken rechnen (E18, ganze Dokumente).

    MLX rechnet die Attention vorwärts speichersparend, fällt aber beim Rückwärtsrechnen auf
    eine Fassung zurück, die alle Scores hält: 32 Köpfe x L x L, bei 8'192 Tokens rund 14 GB.
    Hier werden die Abfragen in Stücke zu `stueck` Positionen geteilt; jedes Stück sieht alle
    Schlüssel bis zu seinem Ende (kausale Maske unten rechts ausgerichtet). Das ist dieselbe
    Rechnung, keine Näherung: vorwärts bitgleich, Gradienten bis auf bf16-Rundung gleich
    (Prüfung 05.10.2026, L = 4'096: max. Abweichung dq 0,0078 bei |dq| bis 3,36).
    Gilt nur ohne Cache und mit kausaler Maske, also im Training; Auslesen bleibt unverändert.
    """
    import mlx.core as mx
    import mlx_lm.models.apertus as apertus

    original = apertus.scaled_dot_product_attention

    def sdpa(queries, keys, values, cache, scale, mask, sinks=None):
        L = queries.shape[2]
        if (cache is not None or sinks is not None or not isinstance(mask, str) or mask != "causal"
                or L <= stueck or keys.shape[2] != L):
            return original(queries, keys, values, cache=cache, scale=scale, mask=mask, sinks=sinks)
        teile = []
        for s in range(0, L, stueck):
            e = min(L, s + stueck)
            teile.append(mx.fast.scaled_dot_product_attention(
                queries[:, :, s:e], keys[:, :, :e], values[:, :, :e], scale=scale, mask="causal"))
        return mx.concatenate(teile, axis=2)

    apertus.scaled_dot_product_attention = sdpa

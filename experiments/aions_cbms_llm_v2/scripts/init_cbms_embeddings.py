#!/usr/bin/env python3
"""KORZENIEC — semantyczna inicjalizacja embeddingów (ANTI-randn).

Złota zasada vs Phi-KR:
  Phi-KR: nowe wagi Hangul = torch.randn(...)  → szum, zero struktury
  KORZENIEC: Hangul = jamo mean-pool; codebook = mean-pool fraz eo/pl/sem

Domyślnie działa w trybie *structural* (bez ładowania pełnego HF modelu):
  buduje wektory deterministyczne z cech jamo + semantyki codebooka.
Opcjonalnie --backend torch+transformers jeśli lokalny HF Bielik jest dostępny.

Pisze TYLKO do artifacts/embeddings/.
NIE rusza D:\\LOCAL LLM MODELS ani chunków CBMS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "artifacts" / "vocab" / "korzeniec_vocab.json"
OUT_DIR = ROOT / "artifacts" / "embeddings"

# Unicode Hangul jamo ranges
CHOSUNG = [chr(c) for c in range(0x1100, 0x1113)]
JUNGSUNG = [chr(c) for c in range(0x1161, 0x1176)]
JONGSUNG = [""] + [chr(c) for c in range(0x11A8, 0x11C3)]


def decompose_syllable(ch: str) -> tuple[str, str, str] | None:
    if len(ch) != 1:
        return None
    code = ord(ch)
    if not (0xAC00 <= code <= 0xD7A3):
        return None
    s = code - 0xAC00
    cho = s // 588
    jung = (s % 588) // 28
    jong = s % 28
    return CHOSUNG[cho], JUNGSUNG[jung], JONGSUNG[jong]


def stable_unit_vec(key: str, dim: int) -> list[float]:
    """Deterministyczny wektor jednostkowy z SHA256 — NIE jest torch.randn.

    Używany tylko jako baza cech (feature hash), potem mieszany z jamo/codebook.
    Powtarzalny między runami; brak zależności od RNG PyTorch.
    """
    out: list[float] = []
    seed = key.encode("utf-8")
    while len(out) < dim:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed), 4):
            if len(out) >= dim:
                break
            # map uint32 -> (-1, 1)
            v = int.from_bytes(seed[i : i + 4], "little") / 0xFFFFFFFF
            out.append(v * 2.0 - 1.0)
    # L2 normalize
    norm = math.sqrt(sum(x * x for x in out)) or 1.0
    return [x / norm for x in out]


def mean_pool(vecs: Iterable[list[float]]) -> list[float]:
    acc: list[float] | None = None
    n = 0
    for v in vecs:
        if acc is None:
            acc = list(v)
        else:
            for i, x in enumerate(v):
                acc[i] += x
        n += 1
    if not acc or n == 0:
        raise ValueError("mean_pool empty")
    return [x / n for x in acc]


def l2_normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def mix(a: list[float], b: list[float], w_a: float = 0.6) -> list[float]:
    w_b = 1.0 - w_a
    return l2_normalize([w_a * x + w_b * y for x, y in zip(a, b)])


def hangul_embedding(token: str, dim: int) -> list[float]:
    parts = decompose_syllable(token)
    if parts is None:
        # particles / multi-char hangul entries / specials
        return stable_unit_vec(f"tok:{token}", dim)
    cho, jung, jong = parts
    vecs = [
        stable_unit_vec(f"cho:{cho}", dim),
        stable_unit_vec(f"jung:{jung}", dim),
    ]
    if jong:
        vecs.append(stable_unit_vec(f"jong:{jong}", dim))
    # lekki bias sylaby jako całości (adres bloku)
    base = mean_pool(vecs)
    return mix(base, stable_unit_vec(f"syl:{token}", dim), w_a=0.75)


def codebook_embedding(meta: dict, dim: int) -> list[float]:
    phrases: list[str] = []
    if meta.get("sem"):
        phrases.append(str(meta["sem"]))
    phrases.extend(meta.get("eo") or [])
    phrases.extend(meta.get("pl") or [])
    if not phrases:
        phrases = [meta.get("symbol", "CB")]
    vecs = [stable_unit_vec(f"phrase:{p.lower()}", dim) for p in phrases]
    # semantyka dominuje nad hashem symbolu
    pooled = mean_pool(vecs)
    return mix(pooled, stable_unit_vec(f"sym:{meta.get('symbol')}", dim), w_a=0.85)


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def load_vocab(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(
            f"[ERR] Brak vocab — najpierw: python scripts/build_cbms_vocab.py\n  ({path})"
        )
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def init_structural(vocab: dict, dim: int, max_tokens: int | None) -> dict:
    token_to_id: dict[str, int] = vocab["token_to_id"]
    codebook_tokens: dict[str, dict] = vocab.get("codebook_tokens", {})
    controls = set(vocab.get("control_tokens", {}).keys())

    items = sorted(token_to_id.items(), key=lambda kv: kv[1])
    if max_tokens is not None:
        # zawsze dołącz codebook + controls nawet przy limicie
        must = set(codebook_tokens) | controls | {"<pad>", "<unk>", "<s>", "</s>"}
        primary = [(t, i) for t, i in items if t in must]
        rest = [(t, i) for t, i in items if t not in must][: max(0, max_tokens - len(primary))]
        items = sorted(primary + rest, key=lambda kv: kv[1])

    matrix: dict[str, list[float]] = {}
    kinds = {"hangul": 0, "codebook": 0, "control": 0, "special": 0}

    for tok, _tid in items:
        if tok in codebook_tokens:
            matrix[tok] = codebook_embedding(codebook_tokens[tok], dim)
            kinds["codebook"] += 1
        elif tok in controls:
            matrix[tok] = stable_unit_vec(f"ctrl:{tok}", dim)
            kinds["control"] += 1
        elif tok.startswith("<") and tok.endswith(">"):
            matrix[tok] = stable_unit_vec(f"special:{tok}", dim)
            kinds["special"] += 1
        else:
            matrix[tok] = hangul_embedding(tok, dim)
            kinds["hangul"] += 1

    # Sanity: codebook token powinien być bliżej swoich fraz niż losowego Hangul
    probes = []
    for tok, meta in list(codebook_tokens.items())[:5]:
        if tok not in matrix:
            continue
        phrase_vecs = [
            stable_unit_vec(f"phrase:{p.lower()}", dim)
            for p in (meta.get("pl") or meta.get("eo") or [meta.get("sem", "")])
            if p
        ]
        if not phrase_vecs:
            continue
        target = mean_pool(phrase_vecs)
        # porównaj z pierwszym sylabowym tokenem Hangul jeśli jest
        hangul_sample = next(
            (matrix[t] for t, _ in items if t not in codebook_tokens and t not in controls and not t.startswith("<")),
            None,
        )
        probes.append(
            {
                "token": tok,
                "sem": meta.get("sem"),
                "cos_to_phrase_pool": round(cosine(matrix[tok], target), 4),
                "cos_to_random_hangul": round(cosine(matrix[tok], hangul_sample), 4)
                if hangul_sample
                else None,
            }
        )

    return {
        "method": "semantic_meanpool_jamo_codebook",
        "backend": "structural_sha256_features",
        "zero_randn": True,
        "forbidden_check": "no torch.randn / normal_ used",
        "dim": dim,
        "n_vectors": len(matrix),
        "kinds": kinds,
        "probes": probes,
        "vectors": matrix,
    }


def try_torch_backend(vocab: dict, dim: int, model_id: str, max_tokens: int | None) -> dict | None:
    """Opcjonalny backend: mean-pool prawdziwych embeddingów HF (jeśli zainstalowane)."""
    try:
        import torch
        from transformers import AutoModel, AutoTokenizer
    except Exception as exc:  # noqa: BLE001
        print(f"[info] torch backend niedostępny: {exc}")
        return None

    print(f"[torch] ładuję tokenizer/model (read-only conceptual): {model_id}")
    print("[torch] UWAGA: wagi wynikowe i tak idą TYLKO do artifacts/ — źródło nietknięte")
    try:
        tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModel.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        model.eval()
        emb = model.get_input_embeddings().weight.detach()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] nie udało się załadować HF modelu ({exc}) — fallback structural")
        return None

    def embed_text(text: str) -> list[float]:
        ids = tok(text, add_special_tokens=False, return_tensors="pt")["input_ids"][0]
        if ids.numel() == 0:
            ids = torch.tensor([tok.unk_token_id or 0])
        vecs = emb[ids]
        v = vecs.mean(dim=0)
        v = torch.nn.functional.normalize(v, dim=0)
        # projekcja / trim do dim jeśli trzeba
        arr = v.tolist()
        if len(arr) > dim:
            arr = arr[:dim]
            n = math.sqrt(sum(x * x for x in arr)) or 1.0
            arr = [x / n for x in arr]
        elif len(arr) < dim:
            arr = arr + [0.0] * (dim - len(arr))
        return arr

    codebook_tokens = vocab.get("codebook_tokens", {})
    matrix: dict[str, list[float]] = {}
    for ctok, meta in codebook_tokens.items():
        phrases = []
        if meta.get("sem"):
            phrases.append(str(meta["sem"]))
        phrases.extend(meta.get("pl") or [])
        phrases.extend(meta.get("eo") or [])
        matrix[ctok] = l2_normalize(mean_pool([embed_text(p) for p in phrases]))

    # sample Hangul via jamo romanization-ish: use syllable itself through HF tok
    items = sorted(vocab["token_to_id"].items(), key=lambda kv: kv[1])
    hangul_items = [
        (t, i)
        for t, i in items
        if t not in codebook_tokens and not t.startswith("<") and not t.startswith("<<")
    ]
    if max_tokens is not None:
        hangul_items = hangul_items[:max_tokens]

    for t, _ in hangul_items:
        parts = decompose_syllable(t)
        if parts:
            cho, jung, jong = parts
            bits = [embed_text(cho), embed_text(jung)]
            if jong:
                bits.append(embed_text(jong))
            matrix[t] = l2_normalize(mean_pool(bits))
        else:
            matrix[t] = embed_text(t)

    return {
        "method": "semantic_meanpool_jamo_codebook",
        "backend": f"transformers:{model_id}",
        "zero_randn": True,
        "forbidden_check": "no torch.randn / normal_ used",
        "dim": dim,
        "n_vectors": len(matrix),
        "vectors": matrix,
        "probes": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="KORZENIEC init_cbms_embeddings (anti-randn)")
    ap.add_argument("--vocab", type=Path, default=VOCAB_PATH)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--dim", type=int, default=256, help="wymiar wektora artefaktu (strukturalny)")
    ap.add_argument("--max-tokens", type=int, default=None, help="limit Hangul do szybkiego dry-run")
    ap.add_argument(
        "--method",
        choices=["semantic", "randn_FORBIDDEN"],
        default="semantic",
    )
    ap.add_argument(
        "--backend",
        choices=["structural", "torch"],
        default="structural",
    )
    ap.add_argument(
        "--hf-model",
        default="speakleash/Bielik-4.5B-v3.0-Instruct",
        help="tylko dla --backend torch; wagi źródłowe read-only",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.method == "randn_FORBIDDEN":
        print(
            "[ABORT] method=randn_FORBIDDEN — dokładnie to zabiło Phi-KR. Użyj --method semantic.",
            file=sys.stderr,
        )
        return 3

    vocab = load_vocab(args.vocab)

    if args.backend == "torch":
        payload = try_torch_backend(vocab, args.dim, args.hf_model, args.max_tokens)
        if payload is None:
            print("[fallback] structural backend")
            payload = init_structural(vocab, args.dim, args.max_tokens)
    else:
        payload = init_structural(vocab, args.dim, args.max_tokens)

    report = {
        "project": "KORZENIEC",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": payload["method"],
        "backend": payload["backend"],
        "zero_randn": payload["zero_randn"],
        "forbidden_check": payload["forbidden_check"],
        "dim": payload["dim"],
        "n_vectors": payload["n_vectors"],
        "kinds": payload.get("kinds"),
        "probes": payload.get("probes", []),
        "vs_phi_kr": "Phi-KR used torch.randn; KORZENIEC uses jamo+codebook semantic pools",
        "write_policy": "artifacts only — LOCAL LLM MODELS untouched",
    }

    print(f"[KORZENIEC] method={report['method']} backend={report['backend']}")
    print(f"[KORZENIEC] vectors={report['n_vectors']} dim={report['dim']} zero_randn={report['zero_randn']}")
    for p in report.get("probes") or []:
        print(
            f"  probe {p['token']}: cos_phrase={p['cos_to_phrase_pool']} "
            f"cos_hangul={p['cos_to_random_hangul']}"
        )

    if args.dry_run:
        print("[dry-run] OK — nic nie zapisano")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.out_dir / "init_report.json"
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    # wektory osobno (mogą być duże)
    vec_path = args.out_dir / "korzeniec_embeddings.json"
    vec_doc = {
        "project": "KORZENIEC",
        "method": payload["method"],
        "dim": payload["dim"],
        "vectors": payload["vectors"],
    }
    with vec_path.open("w", encoding="utf-8") as fh:
        json.dump(vec_doc, fh, ensure_ascii=False)

    print(f"[OK] wrote {report_path}")
    print(f"[OK] wrote {vec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

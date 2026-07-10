#!/usr/bin/env python3
"""KORZENIEC Faza 2 — przygotowanie HF Bielik + vocab CBMS (stub-safe).

Ładuje HF Bielik TYLKO jeśli lokalnie dostępny / z cache HuggingFace.
Dodaje tokeny z korzeniec_vocab.json jako added_tokens.
Inicjalizuje embeddingi z korzeniec_embeddings.json (semantic init, NIE randn).
Zapisuje KOPIĘ do artifacts/hf_bielik_cbms_stub/ — NIGDY nie nadpisuje
D:\\LOCAL LLM MODELS\\.

Jeśli HF niedostępny: zapisuje manifest stub + wskazuje NEXT.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "artifacts" / "vocab" / "korzeniec_vocab.json"
EMBED_JSON = ROOT / "artifacts" / "embeddings" / "korzeniec_embeddings.json"
EMBED_PT = ROOT / "artifacts" / "embeddings" / "korzeniec_embed_init.pt"
OUT_DIR = ROOT / "artifacts" / "hf_bielik_cbms_stub"

DEFAULT_HF_ID = "speakleash/Bielik-4.5B-v3.0-Instruct"
LOCAL_HF_CANDIDATES = [
    Path(r"D:\LOCAL LLM MODELS\Bielik-4.5B-v3.0-Instruct"),
    Path(r"D:\LOCAL LLM MODELS\Bielik-4.5B-HF"),
    Path.home() / ".cache" / "huggingface" / "hub",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_local_hf_model(hf_id: str) -> Path | None:
    """Szuka lokalnej kopii HF (nie GGUF)."""
    env = os.environ.get("KORZENIEC_HF_MODEL_PATH")
    if env:
        p = Path(env)
        if (p / "config.json").is_file():
            return p
    for cand in LOCAL_HF_CANDIDATES:
        if not cand.exists():
            continue
        if cand.name == "hub":
            # snapshot w cache HF
            safe = hf_id.replace("/", "--")
            for sub in cand.glob(f"models--{safe}*"):
                snap = sub / "snapshots"
                if snap.is_dir():
                    for s in snap.iterdir():
                        if (s / "config.json").is_file():
                            return s
            continue
        if (cand / "config.json").is_file():
            return cand
    return None


def korzeniec_added_tokens(vocab: dict) -> list[dict[str, Any]]:
    """Tokeny CBMS/Hangul/control poza bazowym tokenizerem Bielika."""
    base_skip = {"<pad>", "<unk>", "<s>", "</s>"}
    codebook = set(vocab.get("codebook_tokens", {}))
    controls = set(vocab.get("control_tokens", {}))
    out: list[dict[str, Any]] = []
    for tok, tid in sorted(vocab.get("token_to_id", {}).items(), key=lambda x: x[1]):
        if tok in base_skip:
            continue
        if tok in codebook or tok in controls or tok.startswith("<<CB:"):
            out.append({"content": tok, "lstrip": False, "rstrip": False, "single_word": True, "normalized": False})
        elif len(tok) == 1 and "\uac00" <= tok <= "\ud7a3":
            out.append({"content": tok, "lstrip": False, "rstrip": False, "single_word": True, "normalized": False})
    return out


def _matrix_to_vectors(matrix: Any, vocab: dict) -> dict[str, list[float]]:
    """Mapuje wiersze [N,D] → {token: list} przez token_to_id (read-only)."""
    id_to_tok = {int(i): t for t, i in (vocab.get("token_to_id") or {}).items()}
    out: dict[str, list[float]] = {}
    n = int(matrix.shape[0]) if hasattr(matrix, "shape") else len(matrix)
    for i in range(n):
        tok = id_to_tok.get(i)
        if not tok:
            continue
        row = matrix[i]
        if hasattr(row, "tolist"):
            out[tok] = [float(x) for x in row.tolist()]
        else:
            out[tok] = [float(x) for x in row]
    return out


def load_init_vectors(vocab: dict | None = None) -> tuple[dict[str, list[float]], int, str]:
    """Ładuje semantic init — NIGDY randn. Preferuje .pt (dim modelu), potem JSON."""
    vocab = vocab or (load_json(VOCAB_PATH) if VOCAB_PATH.is_file() else {})

    if EMBED_PT.is_file():
        try:
            import torch

            data = torch.load(EMBED_PT, map_location="cpu", weights_only=False)
            if isinstance(data, dict) and "vectors" in data:
                vecs = data["vectors"]
                dim = int(data.get("dim") or (len(next(iter(vecs.values()))) if vecs else 0))
                return vecs, dim, "korzeniec_embed_init.pt:vectors"
            if isinstance(data, dict) and "embeddings" in data:
                mat = data["embeddings"]
                # .pt mógł powstać ze starszego vocab (4044) — spróbuj dopasować
                alt_vocab_path = ROOT / "artifacts" / "korzeniec_vocab.json"
                use_vocab = vocab
                if alt_vocab_path.is_file() and int(mat.shape[0]) != len(vocab.get("token_to_id") or {}):
                    try:
                        use_vocab = load_json(alt_vocab_path)
                    except Exception:
                        use_vocab = vocab
                vecs = _matrix_to_vectors(mat, use_vocab)
                dim = int(mat.shape[1])
                if vecs:
                    return vecs, dim, "korzeniec_embed_init.pt:embeddings"
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] nie udało się wczytać {EMBED_PT}: {exc}")

    if not EMBED_JSON.is_file():
        raise SystemExit(
            f"[ERR] Brak embeddingów — uruchom: python scripts/init_cbms_embeddings.py\n  ({EMBED_JSON})"
        )
    doc = load_json(EMBED_JSON)
    return doc["vectors"], int(doc["dim"]), "korzeniec_embeddings.json"


def write_stub_manifest(
    *,
    hf_id: str,
    vocab: dict,
    n_added: int,
    init_source: str,
    reason: str,
    out_dir: Path = OUT_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "project": "KORZENIEC",
        "phase": "2-hf-stub",
        "status": "STUB_ONLY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hf_model_id": hf_id,
        "local_hf_found": False,
        "reason": reason,
        "vocab_source": str(VOCAB_PATH),
        "n_added_tokens_planned": n_added,
        "embedding_init_source": init_source,
        "embedding_policy": "semantic_meanpool_jamo_codebook — zero torch.randn",
        "output_dir": str(out_dir),
        "write_policy": "NEVER touch D:\\LOCAL LLM MODELS\\",
        "next_steps": [
            "Zobacz NEXT.md w tym katalogu eksperymentu",
            f"huggingface-cli download {hf_id} --local-dir ./hf_cache/bielik",
            "Ustaw KORZENIEC_HF_MODEL_PATH na ścieżkę z config.json",
            "Ponów: python scripts/prepare_hf_bielik_cbms.py",
        ],
        "added_token_sample": [t["content"] for t in korzeniec_added_tokens(vocab)[:8]],
    }
    path = out_dir / "stub_manifest.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"[STUB] wrote {path}")
    print(f"[STUB] {reason}")


def prepare_hf(
    hf_id: str,
    vocab: dict,
    vectors: dict[str, list[float]],
    dim: int,
    init_source: str,
    local_path: Path,
    dry_run: bool,
    out_dir: Path = OUT_DIR,
) -> dict[str, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(f"[ERR] transformers+torch wymagane: {exc}") from exc

    print(f"[HF] ładuję tokenizer z {local_path}")
    tokenizer = AutoTokenizer.from_pretrained(str(local_path), trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(local_path),
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )

    added = korzeniec_added_tokens(vocab)
    n_before = len(tokenizer)
    added_strings = [t["content"] for t in added]
    n_new = tokenizer.add_tokens(added_strings, special_tokens=False)
    model.resize_token_embeddings(len(tokenizer))

    emb = model.get_input_embeddings().weight.detach().cpu()
    emb_dim = emb.shape[1]
    initialized = 0
    fallback = 0

    for tok in added_strings:
        tid = tokenizer.convert_tokens_to_ids(tok)
        if tid is None or tid < 0:
            continue
        vec = vectors.get(tok)
        if vec is None:
            fallback += 1
            continue
        arr = vec[:emb_dim] if len(vec) >= emb_dim else vec + [0.0] * (emb_dim - len(vec))
        t = torch.tensor(arr, dtype=emb.dtype)
        t = torch.nn.functional.normalize(t, dim=0)
        with torch.no_grad():
            emb[tid] = t
        initialized += 1

    report = {
        "project": "KORZENIEC",
        "phase": "2-hf-prepared",
        "status": "PREPARED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hf_model_id": hf_id,
        "local_hf_path": str(local_path),
        "vocab_tokens_before": n_before,
        "added_tokens": n_new,
        "embedding_init_source": init_source,
        "embedding_dim_artifact": dim,
        "embedding_dim_model": emb_dim,
        "vectors_initialized": initialized,
        "vectors_fallback": fallback,
        "zero_randn": True,
        "write_policy": "copy to artifacts/hf_bielik_cbms_stub only",
    }

    if dry_run:
        print(f"[dry-run] added={n_new} initialized={initialized} fallback={fallback}")
        return report

    out_dir.mkdir(parents=True, exist_ok=True)
    out_model = out_dir / "model"
    out_tok = out_dir / "tokenizer"
    print(f"[HF] zapisuję kopię do {out_dir}")
    model.save_pretrained(out_model)
    tokenizer.save_pretrained(out_tok)

    # zapisz tylko nowe wiersze embeddingów (lekki artefakt)
    new_ids = [tokenizer.convert_tokens_to_ids(t) for t in added_strings]
    new_rows = emb[new_ids].clone()
    torch.save(
        {
            "added_tokens": added_strings,
            "token_ids": new_ids,
            "rows": new_rows,
            "init_source": init_source,
            "zero_randn": True,
        },
        out_dir / "korzeniec_embed_init.pt",
    )

    report_path = out_dir / "prepare_report.json"
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"[OK] wrote {report_path}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="KORZENIEC prepare_hf_bielik_cbms")
    ap.add_argument("--hf-model", default=DEFAULT_HF_ID)
    ap.add_argument("--vocab", type=Path, default=VOCAB_PATH)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = args.out_dir

    if not args.vocab.is_file():
        print(f"[ERR] Brak vocab: {args.vocab}", file=sys.stderr)
        print("  Uruchom: python scripts/build_cbms_vocab.py", file=sys.stderr)
        return 2

    vocab = load_json(args.vocab)
    vectors, dim, init_source = load_init_vectors(vocab)
    added = korzeniec_added_tokens(vocab)
    print(f"[KORZENIEC] vocab tokens={len(vocab.get('token_to_id', {}))} added_planned={len(added)}")
    print(f"[KORZENIEC] init vectors={len(vectors)} dim={dim} source={init_source}")

    local = find_local_hf_model(args.hf_model)
    if local is None:
        write_stub_manifest(
            hf_id=args.hf_model,
            vocab=vocab,
            n_added=len(added),
            init_source=init_source,
            reason="Brak lokalnego HF Bielik (tylko GGUF w LOCAL LLM MODELS jest OK). Gate Fazy 1 działa bez tego.",
            out_dir=out_dir,
        )
        return 0

    print(f"[HF] znaleziono lokalny model: {local}")
    try:
        prepare_hf(
            args.hf_model,
            vocab,
            vectors,
            dim,
            init_source,
            local,
            args.dry_run,
            out_dir=out_dir,
        )
    except Exception as exc:  # noqa: BLE001
        write_stub_manifest(
            hf_id=args.hf_model,
            vocab=vocab,
            n_added=len(added),
            init_source=init_source,
            reason=f"Ładowanie HF failed: {exc}",
            out_dir=out_dir,
        )
        print(f"[WARN] HF prepare failed → stub: {exc}", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

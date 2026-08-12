"""
export_model.py — M7. Jednorazowy eksport statycznego embeddingu do przypietego artefaktu.

DLACZEGO EKSPORT, A NIE UZYCIE BIBLIOTEKI WPROST
------------------------------------------------
`model2vec` i `torch` sa potrzebne TYLKO tutaj. Po eksporcie warstwa zapytania czyta
macierz `int16` i tokenizer, i liczy wylacznie na liczbach calkowitych. Dzieki temu:

- wersja `torch` nie moze zmienic wyniku, bo `torch` nie jest importowany przy zapytaniu,
- model nie jest pobierany w locie, wiec zmiana repozytorium HF nie zmieni wyniku po cichu,
- karta modelu przypina oba pliki przez `blake2b256` — rozjazd jest wykrywalny, nie cichy.

KWANTYZACJA — JEDNA GLOBALNA SKALA
----------------------------------
`skala = 32767 / max|E|`, zaokraglenie do parzystego (`np.round`, reguła banker's rounding).
Skala globalna, nie per-wiersz: per-wiersz znormalizowalby dlugosci wektorow i zniszczyl
proporcje miedzy nimi, a to wlasnie te proporcje niosa podobienstwo.

Artefakt NIE jest commitowany (15 MB). Commitowana jest karta z hashami — kazdy moze
odtworzyc eksport i porownac 64 znaki.

Uruchomienie (z katalogu repo):
    python acae/scripts/export_model.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

MODEL_ID = "minishlab/potion-base-8M"
INT16_MAX = 32767
SCHEMA = "acae.model_card.v1"


def blake2b256(path: pathlib.Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return f"blake2b256:{h.hexdigest()}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ACAE M7 — eksport statycznego embeddingu")
    ap.add_argument("--out", default="acae/_model", help="katalog artefaktu (wzglednie do repo)")
    ap.add_argument("--model", default=MODEL_ID, help="identyfikator modelu zrodlowego")
    args = ap.parse_args(argv)

    try:
        import numpy as np
        from model2vec import StaticModel
    except ImportError as exc:
        print(f"BLAD: brak zaleznosci eksportu ({exc}). To narzedzie budujace, nie runtime.",
              file=sys.stderr)
        return 2

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    model = StaticModel.from_pretrained(args.model)
    E = np.asarray(model.embedding, dtype=np.float64)
    if E.ndim != 2:
        print(f"BLAD: oczekiwano macierzy 2D, jest {E.shape}", file=sys.stderr)
        return 2

    max_abs = float(np.abs(E).max())
    if max_abs <= 0.0:
        print("BLAD: macierz zerowa", file=sys.stderr)
        return 2

    scale = INT16_MAX / max_abs
    Q = np.round(E * scale).astype(np.int16)   # np.round = zaokraglenie do parzystego

    matrix_path = out / "vectors_int16.npy"
    tokenizer_path = out / "tokenizer.json"
    np.save(matrix_path, Q, allow_pickle=False)
    model.tokenizer.save(str(tokenizer_path))

    # Kontrola strat kwantyzacji — informacyjna, nie bramka.
    odtworzone = Q.astype(np.float64) / scale
    max_blad = float(np.abs(odtworzone - E).max())

    card = {
        "schema": SCHEMA,
        "source_model": args.model,
        "shape": [int(Q.shape[0]), int(Q.shape[1])],
        "dtype": "int16",
        "quantization": {
            "rule": "global_scale_round_half_even",
            "int16_max": INT16_MAX,
            "max_abs_source": repr(max_abs),
            "scale": repr(scale),
            "max_abs_error": repr(max_blad),
        },
        "files": {
            "vectors_int16.npy": blake2b256(matrix_path),
            "tokenizer.json": blake2b256(tokenizer_path),
        },
        "runtime_note": (
            "Warstwa zapytania nie importuje model2vec ani torch. "
            "Iloczyn skalarny w int64, normalizacja przez math.isqrt, wynik w promilach."
        ),
    }
    (out / "model_card.json").write_text(
        json.dumps(card, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"macierz    {matrix_path}  {Q.shape}  {matrix_path.stat().st_size} B")
    print(f"tokenizer  {tokenizer_path}  {tokenizer_path.stat().st_size} B")
    print(f"skala      {scale!r}   max blad kwantyzacji {max_blad!r}")
    print(f"karta      {out / 'model_card.json'}")
    for name, digest in card["files"].items():
        print(f"  {name:20} {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Jednorazowe wystawienie ocen przesiewacza (M15) i zamrozenie ich w `_desc/rerank_cache.json`.

To JEDYNE miejsce w projekcie, ktore uruchamia cross-encoder. Warstwa pomiarowa
(`acae/rerank.py`) czyta juz tylko gotowy plik i modelu nie dotyka — dzieki temu
pomiar odtwarza sie bit w bit takze na maszynie, ktora modelu nie ma.

Ta sama granica co przy M7: `export_model.py` wolno zalezec od `torch`, warstwie
zapytania nie wolno.

CO DOKLADNIE JEST OCENIANE
--------------------------
Dla kazdego pytania ze zbioru roboczego bierzemy czolowa `DEPTH` symboli wg `embed_desc`
i dla kazdego liczymy ocene pary (pytanie, tekst symbolu). Tekst symbolu to DOKLADNIE
ten sam `symbol_text_with_description`, ktory widzi embedding — decyzja z prerejestracji,
zeby roznica byla przypisywalna do SEDZIEGO, a nie do materialu.

SKALA
-----
`sentence_transformers` przy jednym neuronie wyjsciowym przepuszcza wynik przez sigmoide,
wiec dostajemy 0..1. Zapisujemy w promilach jako liczbe calkowita (0..1000).
Granica decyzyjna modelu to 0,5, czyli 500 promili.
"""

import datetime
import json
import math
import os
import pathlib
import tomllib

ACAE = pathlib.Path("acae")
DEPTH = 25          # ta sama glebokosc co `DEPTH` w measure_m4.py, od poczatku ablacji M4
MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def main():
    os.environ.setdefault("HF_HOME", str(pathlib.Path("_models_hf").resolve()))

    from acae.canon import content_hash
    from acae.core import PackRequest, build_pack, collect_entries
    from acae.describe import load_descriptions
    from acae.embed import StaticEmbedder, symbol_text_with_description
    from acae.pack import FsLocator, FsReader
    from acae.rerank import candidate_key, question_key

    root = pathlib.Path(".").resolve()
    cfg = tomllib.load(open(ACAE / "config" / "acae.toml", "rb"))
    loc = FsLocator(
        root=str(root), roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    reader = FsReader(str(root))
    entries, _ = collect_entries(loc, reader)

    pack_hash = build_pack(PackRequest(root=root.name), loc, reader).pack_hash
    opisy, opisy_prov = load_descriptions(ACAE / "_desc" / "descriptions.json",
                                          expected_pack_hash=pack_hash)
    pytania = json.loads((ACAE / "tests" / "dev_questions.json").read_bytes())["queries"]

    import numpy as np
    embedder = StaticEmbedder(ACAE / "_model")
    items, teksty, wektory = [], [], []
    for e in entries:
        p = str(e["path"])
        for row in e["symbols"]:
            t = symbol_text_with_description(p, row, opisy.get(p, ""))
            items.append((p, row))
            teksty.append(t)
            wektory.append(embedder.vector(t))
    M = np.vstack(wektory)
    normy = [int(np.dot(v, v)) for v in M]
    print(f"symboli: {len(items)}   pack_hash: {pack_hash[:24]}...")

    def czolowka(pytanie):
        """Czolowa DEPTH wg embed_desc, z tym samym rozstrzyganiem remisow co w mierniku."""
        qv = embedder.vector(pytanie)
        nq = int(np.dot(qv, qv))
        il = M @ qv
        oceny = []
        for d, nd in zip(il, normy):
            d = int(d)
            oceny.append(0 if nq == 0 or d <= 0 or nd == 0
                         else math.isqrt((10**6 * d * d) // (nq * nd)))
        numery = sorted(range(len(items)),
                        key=lambda i: (-oceny[i], items[i][0], items[i][1]["line"],
                                       items[i][1]["name_path"]))
        return numery[:DEPTH]

    print(f"laduje model {MODEL}...")
    from sentence_transformers import CrossEncoder
    model = CrossEncoder(MODEL, max_length=512)

    scores: dict[str, dict[str, int]] = {}
    pary_total = 0
    for nr, q in enumerate(pytania, 1):
        numery = czolowka(q["question"])
        pary = [(q["question"], teksty[i]) for i in numery]
        surowe = model.predict(pary)   # sigmoid, bo model ma jeden neuron wyjsciowy
        wpis = {}
        for i, s in zip(numery, surowe):
            p, row = items[i]
            # Kwantyzacja do promili. Zaokraglenie w gore od polowy, deterministyczne.
            wpis[candidate_key(p, str(row["name_path"]))] = int(float(s) * 1000 + 0.5)
        scores[question_key(q["question"])] = wpis
        pary_total += len(pary)
        print(f"  [{nr:>2}/{len(pytania)}] {q['id']:<8} {len(pary)} par")

    artefakt = {
        "provenance": {
            "model": MODEL,
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0).isoformat(),
            "pack_hash": pack_hash,
            "descriptions_hash": content_hash((ACAE / "_desc" / "descriptions.json").read_bytes()),
            "depth": DEPTH,
            "activation": "sigmoid",
            "unit": "permille",
            "decision_boundary": 500,
            "questions": len(pytania),
            "pairs": pary_total,
        },
        "scores": scores,
    }
    cel = ACAE / "_desc" / "rerank_cache.json"
    cel.write_text(json.dumps(artefakt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"\nzapisano {cel} ({cel.stat().st_size} bajtow)")
    print(f"par ocenionych: {pary_total}   pytan: {len(pytania)}")
    wszystkie = [v for d in scores.values() for v in d.values()]
    w = sorted(wszystkie)
    print(f"oceny w promilach: min {w[0]}  mediana {w[len(w)//2]}  max {w[-1]}")
    print(f"powyzej granicy 500: {sum(1 for x in w if x >= 500)} z {len(w)}")


if __name__ == "__main__":
    main()

"""
embedindex.py — ranking po znaczeniu, przeniesiony ze skryptu pomiarowego do BIBLIOTEKI.

PO CO TO PRZENIESIENIE
----------------------
`EmbedIndex` mieszkal w `scripts/measure_m4.py`, wiec korzystal z niego **wylacznie
pomiar**. Narzedzie, po ktore siega czlowiek (`acae ask`), szukalo dalej samymi slowami.

Roznica jest zmierzona i duza — na 306 pytaniach zadanych po ludzku:

    samo szukanie po slowach : recall@10 25,1%   MRR 0,136
    znaczenie + opisy        : recall@10 62,0%   MRR 0,451

Czyli produkcja dostawala **dwuipolkrotnie gorszy** wynik niz to, co mierzylismy.
Modul jest tu po to, zeby CLI i przyszly `acae_ask` uzywaly DOKLADNIE tego samego kodu,
ktory przechodzi pomiary — a nie jego ubozszej kuzynki.

DETERMINIZM
-----------
Wszystko w `int64`: mnozenie macierzowe liczb calkowitych jest dokladne i niezalezne
od kolejnosci sumowania, wiec liczba watkow BLAS nie zmienia wyniku. Podobienstwo
w promilach przez `math.isqrt`, pierwiastek brany RAZ na koncu — dwa obciecia po drodze
potrafily dac wynik powyzej 1000 promili (blad znaleziony testem w M7, patrz `embed.py`).

Remisy rozstrzygane jak wszedzie w tym projekcie: (sciezka, linia, name_path).
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from .embed import symbol_text_with_description


class EmbedIndex:
    """
    Wektory wszystkich symboli policzone RAZ. Kolejnosc `items` jest kolejnoscia
    wierszy macierzy.

    Gdy `descriptions` jest puste, wynik jest identyczny z golym M7 —
    `symbol_text_with_description` z pustym opisem zwraca doslownie `symbol_text`.
    """

    def __init__(self, embedder, entries, descriptions: Mapping[str, str] | None = None,
                 vectors=None):
        import numpy as np

        opisy = descriptions or {}
        self.embedder = embedder
        self.items: list[tuple[str, Mapping, object]] = []
        self.texts: list[str] = []
        for entry in entries:
            path = str(entry["path"])
            for row in entry["symbols"]:  # type: ignore[index]
                self.items.append((path, row, entry.get("lang")))
                self.texts.append(symbol_text_with_description(path, row, opisy.get(path, "")))

        # Liczenie 1598 wektorow zajmuje ~3,2 s i jest identyczne, dopoki nie zmieni sie
        # ani tresc plikow, ani opisy, ani model. `vectors` pozwala podac je z cache.
        if vectors is not None:
            self.M = vectors
        else:
            w = [embedder.vector(t) for t in self.texts]
            self.M = np.vstack(w) if w else np.zeros((0, embedder.dim), dtype=np.int64)
        # Kwadraty norm, NIE normy. Pierwiastek raz, na koncu.
        self.norms2 = [int(np.dot(v, v)) for v in self.M]

    def scores(self, question: str) -> list[int]:
        """Podobienstwo kazdego symbolu do pytania, w promilach, jako liczby calkowite."""
        import numpy as np

        qv = self.embedder.vector(question)
        nq2 = int(np.dot(qv, qv))
        if nq2 == 0:
            return [0] * len(self.items)
        iloczyny = self.M @ qv
        out = []
        for d, nd2 in zip(iloczyny, self.norms2):
            d = int(d)
            out.append(0 if d <= 0 or nd2 == 0
                       else math.isqrt((1000 * 1000 * d * d) // (nq2 * nd2)))
        return out

    def order(self, question: str) -> list[int]:
        """Numery symboli od najlepszego. Remisy: (sciezka, linia, name_path)."""
        w = self.scores(question)
        return sorted(
            range(len(self.items)),
            key=lambda i: (-w[i], self.items[i][0], self.items[i][1]["line"],
                           self.items[i][1]["name_path"]),
        )

    def ranked(self, question: str, limit: int) -> list[dict]:
        """
        Najlepsze `limit` symboli w ksztalcie, ktorego oczekuje `retrieve.build_slice`:
        `{"score", "path", "lang", "row"}` — ten sam co zwraca `retrieve.select`.
        """
        w = self.scores(question)
        out = []
        for i in self.order(question)[:limit]:
            path, row, lang = self.items[i]
            out.append({"score": int(w[i]), "path": path, "lang": lang, "row": row})
        return out


def build_index(embedder, entries: Sequence[Mapping[str, object]],
                descriptions: Mapping[str, str] | None = None) -> EmbedIndex:
    return EmbedIndex(embedder, entries, descriptions)


# --------------------------------------------------------------- cache wektorow

def index_key(entries: Sequence[Mapping[str, object]],
              descriptions: Mapping[str, str] | None,
              model_dir) -> str:
    """
    Klucz cache wektorow. Musi objac WSZYSTKO, co wplywa na tekst symbolu:
    tresc plikow, opisy i sam model. Pominiecie ktoregokolwiek dalo by ciche
    podanie wektorow policzonych dla czegos innego.
    """
    from pathlib import Path

    from .canon import canonical_json, content_hash

    skladniki = {
        "files": sorted((str(e["path"]), str(e["content_hash"])) for e in entries),
        "descriptions": content_hash(
            canonical_json({k: v for k, v in sorted((descriptions or {}).items())})
        ),
        "model_card": content_hash((Path(model_dir) / "model_card.json").read_bytes()),
    }
    return content_hash(canonical_json(skladniki))


def load_vectors(path, key: str):
    """Wektory z cache albo `None`. Kazdy blad to `None` — cache to tylko szybkosc."""
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return None
    try:
        import numpy as np

        with np.load(p, allow_pickle=False) as z:
            if str(z["key"]) != key:
                return None
            return z["M"]
    except Exception:
        return None


def save_vectors(path, key: str, M) -> None:
    from pathlib import Path

    try:
        import numpy as np

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez(p, key=np.array(key), M=M)
    except Exception:
        pass

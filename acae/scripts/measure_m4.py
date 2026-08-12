#!/usr/bin/env python
"""
measure_m4.py — ablacja M4. Kazdy etap mierzony OSOBNO, wobec kryterium zapisanego wczesniej.

CO MIERZY
---------
recall@10 / recall@25 — czy prawdziwy symbol w ogole wpadl do wycinka
MRR                   — jak wysoko; symbol na 24. pozycji jest formalnie trafiony,
                        a praktycznie nie, i tylko MRR to widzi
kontrola negatywna    — 6 pytan o funkcjonalnosc, ktorej w repo NIE MA. Mierzymy stosunek
                        sredniego najlepszego wyniku na negatywach do tego na pozytywach.
                        Bez tej liczby „semantic retrieval" i „rozszerzam agresywnie, wiec
                        cos zawsze trafie" wygladaja identycznie.

DLACZEGO STOSUNEK, A NIE SUROWY WYNIK
-------------------------------------
Warianty rankera maja rozne skale (BM25F liczy logarytmy, poprzedni scoring sumowal wagi
calkowite). Porownywanie surowych wynikow miedzy wariantami nie znaczy nic. Stosunek
negatywy/pozytywy jest bezwymiarowy, wiec porownywalny.

URUCHOMIENIE
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant baseline
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant bm25f
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant bm25f --set heldout   # RAZ, na koncu
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from importlib import metadata
from pathlib import Path

ACAE_DIR = Path(__file__).resolve().parent.parent

from acae.bm25f import Bm25fIndex  # noqa: E402
from acae.canon import canonical_json, content_hash  # noqa: E402
from acae.concepts import Codebook, SymbolTokens  # noqa: E402
from acae.core import PackRequest, build_pack, collect_entries  # noqa: E402
from acae.describe import (  # noqa: E402
    load_descriptions, rank_all as rank_desc_all, receipt as desc_receipt,
    score_with_description, term_rarity_with_descriptions,
)
from acae.expand import (  # noqa: E402
    Corpus, code_window_documents, description_documents, docstring_documents, expand,
    prose_documents, symbol_vocabulary,
)
from acae.embed import (  # noqa: E402
    StaticEmbedder, receipt as embed_receipt, symbol_text, symbol_text_with_description,
)
from acae.graph import DAMP_PERMILLE, HOPS, SEED_K, build_graph  # noqa: E402
from acae.pack import FsLocator, FsReader  # noqa: E402
from acae.scope import ScopeIndex  # noqa: E402
from acae.retrieve import query_terms, score_symbol, select, term_rarity  # noqa: E402

SCHEMA = "acae.m4.v1"
TOP_K = (10, 25)
DEPTH = 25

# Skala premii z propagacji, wzgledem czolowego wyniku DANEGO zapytania.
# 500 promili = symbol o pelnej propagacji dostaje polowe czolowego wyniku, czyli
# propagacja moze wypchnac symbol w gore, ale nie postawi na czele czegos, czego
# ranker leksykalny w ogole nie widzial. Wartosc wynika z projektu `rank_graph`
# (patrz jej docstring) i jest ustalona PRZED pomiarem.
BOOST_PERMILLE = 500

# Ile paragonow na zapytanie i ile zrodel na paragon trafia do artefaktu.
RECEIPT_LIMIT = 5

SETS = {"dev": "tests/dev_questions.json", "heldout": "tests/heldout_questions.json"}


def run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.decode("utf-8", "replace").strip()


def rank_baseline(entries, terms, depth):
    """Obecny ranker z M2: wagi pol + `term_rarity` z sufitem. Punkt odniesienia."""
    rarity = term_rarity(entries, terms)
    outline, _ = select(entries, terms, depth, 0)
    del rarity
    return outline


def rank_with_expansion(entries, terms, depth, corpus, vocabulary, pack_hash, rule):
    """
    Baseline ranker + terminy rozszerzone, wazone o polowe slabiej niz oryginalne.

    Rozszerzenia sa wazone slabiej, bo sa HIPOTEZA o slownictwie, a nie tym, o co
    czlowiek zapytal. Zrownanie ich z terminami oryginalnymi sprawialoby, ze symbol
    nazwany dokladnie jak termin rozszerzony bilby symbol nazwany jak samo pytanie.

    Zwraca (ranking, paragony) — paragony ida do artefaktu, zeby dalo sie odtworzyc,
    DLACZEGO kazdy termin wszedl.
    """
    pairs = expand(terms, corpus, vocabulary, pack_hash, rule)
    extra = [t for t, _ in pairs if t not in terms]
    rarity = term_rarity(entries, list(terms) + extra)

    ranked = []
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:
            score = score_symbol(path, row, terms, rarity)
            if extra:
                score += score_symbol(path, row, extra, rarity) // 2
            if score > 0:
                ranked.append({"score": score, "path": path, "lang": entry.get("lang"), "row": row})
    ranked.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))
    return ranked[:depth], [receipt.as_dict() for _, receipt in pairs]


def rank_graph(entries, terms, depth, graph, seed_k=SEED_K, boost_permille=BOOST_PERMILLE,
               descriptions=None):
    """
    Baseline ranker + propagacja Suade po grafie wywolan (M4.4).

    Zbior zainteresowania to `seed_k` najlepszych z rankera leksykalnego — to, w co
    ranker JUZ wierzy. Propagacja dokłada punkty symbolom, ktorych ranker nie trafil
    leksykalnie, ale ktore leza o skok lub dwa od tego, co trafil.

    SKALA PREMII
    ------------
    Wynik propagacji jest w promilach [0,1000], a wyniki baseline'u to sumy wag
    rzadkosci o zupelnie innej skali (tysiace). Zderzenie ich wprost nie znaczyloby
    nic. Premia jest wiec liczona WZGLEDEM czolowego wyniku TEGO zapytania:

        premia = propagacja_promile * top1 * BOOST_PERMILLE / 1000 / 1000

    czyli symbol o pelnej propagacji (1000 promili) dostaje polowe czolowego wyniku.
    Propagacja moze wiec WYPCHNAC symbol w gore rankingu, ale nie moze sama z siebie
    postawic na czele czegos, czego ranker w ogole nie widzial.

    Zasiew premii nie dostaje — patrz `CallGraph.propagate`.

    Zwraca (ranking, paragony). Paragony ida do artefaktu: dla kazdego wypromowanego
    symbolu zapisujemy, z ktorych symbolow zasiewu przyszedl wklad.
    """
    # M9d: ziarnem propagacji jest ranking Z OPISAMI zamiast golego baseline'u.
    # Propagacja wzmacnia to, w co ranker juz wierzy — a M4.4 przegral m.in. dlatego,
    # ze ranker wierzyl w niewiele. Sam mechanizm propagacji zostaje nietkniety.
    opisy = descriptions or {}
    rarity = (term_rarity_with_descriptions(entries, terms, opisy) if opisy
              else term_rarity(entries, terms))
    scored = []
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:
            scored.append({
                "score": score_with_description(path, row, terms, rarity, opisy.get(path, "")),
                "path": path, "lang": entry.get("lang"), "row": row,
            })
    scored.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))

    hits = [d for d in scored if d["score"] > 0]
    if not hits:
        return [], []

    seeds = {(d["path"], str(d["row"]["name_path"])) for d in hits[:seed_k]}
    spread = graph.propagate_with_sources(seeds)
    scale = (hits[0]["score"] * boost_permille) // 1000

    ranked = []
    for d in scored:
        key = (d["path"], str(d["row"]["name_path"]))
        permille = 0 if key in seeds else spread.get(key, (0, []))[0]
        bonus = (permille * scale) // 1000
        total = d["score"] + bonus
        if total > 0:
            ranked.append({
                "score": total, "path": d["path"], "lang": d["lang"], "row": d["row"],
                "base_score": d["score"], "graph_permille": permille,
            })
    ranked.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))

    promoted = sorted(
        ((k, v) for k, v in spread.items() if v[0] > 0),
        key=lambda it: (-it[1][0], it[0]),
    )[:RECEIPT_LIMIT]
    receipts = [
        {
            "rule": "suade_call_graph",
            "target": {"path": key[0], "name_path": key[1]},
            "score_permille": value,
            "from_seeds": [{"path": p, "name_path": n} for p, n in sources[:RECEIPT_LIMIT]],
            "stats": {"seeds": len(seeds), "hops": HOPS, "damp_permille": DAMP_PERMILLE},
        }
        for key, (value, sources) in promoted
    ]
    return ranked[:depth], receipts


def rank_codebook(entries, terms, depth, codebook, symtok):
    """
    Ranker bazowy + tokeny z semantycznego codebooka, wazone o polowe slabiej.

    Rozszerzenie jest tu WIEDZA, nie hipoteza — ktos wpisal, ze „machine" oznacza `host`.
    Ale wazymy je i tak slabiej niz terminy oryginalne, bo pytanie zadal czlowiek,
    a rozszerzenie tylko domysla sie, o ktore pojecie mu chodzilo.

    Dopasowanie tokenow idzie przez `SymbolTokens` — cale tokeny, nie podciagi.
    """
    pairs = codebook.lookup(terms)
    tokens = [t for t, _ in pairs]
    rarity = term_rarity(entries, terms)

    ranked = []
    index = 0
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:
            score = score_symbol(path, row, terms, rarity)
            if tokens:
                score += symtok.score(index, tokens) // 2
            if score > 0:
                ranked.append({"score": score, "path": path, "lang": entry.get("lang"), "row": row})
            index += 1
    ranked.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))

    widziane, receipts = set(), []
    for _, hit in pairs:
        if hit.concept not in widziane:
            widziane.add(hit.concept)
            receipts.append(hit.as_dict())
    return ranked[:depth], receipts


def rank_gate(entries, terms, depth, scope_index):
    """
    M6: bramka zakresu, potem NIEZMIENIONY ranking bazowy wylacznie w jej wnetrzu.

    Do zapytania nie trafia ani jedno dodatkowe slowo. Jedyna zmiana wobec baseline
    to zbior, po ktorym ranking chodzi — a to jest dokladnie ta dzwignia, ktorej
    siedem poprzednich mechanizmow nie ruszalo.

    Zwraca (ranking, paragony, pliki w bramce, czy fallback).
    """
    pliki, hits, fallback = scope_index.gate(terms)
    rarity = term_rarity(entries, terms)

    ranked = []
    for entry in entries:
        path = str(entry["path"])
        if path not in pliki:
            continue
        for row in entry["symbols"]:
            score = score_symbol(path, row, terms, rarity)
            if score > 0:
                ranked.append({"score": score, "path": path, "lang": entry.get("lang"), "row": row})
    ranked.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))

    receipts = [hit.as_dict() for hit in hits]
    if fallback:
        receipts.append({"rule": "scope_gate", "fallback": True,
                         "reason": "zaden zakres nie trafil — przeszukano cala przestrzen"})
    return ranked[:depth], receipts, pliki, fallback


def is_hit(item, question) -> bool:
    """
    Trafienie: dokladny `name_path` albo sama nazwa liscia przy zgodnym pliku.

    Sama nazwa liscia bez zgodnosci pliku bylaby zbyt hojna — `__init__` trafialby wszedzie.
    """
    name = str(item["row"]["name_path"])
    path = str(item["path"])
    for target in question["answer_symbols"]:
        if name == target:
            return True
        if name.split("/")[-1] == target.split("/")[-1] and path in question["answer_files"]:
            return True
    return False


class EmbedIndex:
    """
    Wektory wszystkich symboli policzone RAZ. Kolejnosc `items` jest kolejnoscia
    wierszy macierzy — na niej opieraja sie wszystkie trzy warianty M7.

    Wszystko w `int64`: mnozenie macierzowe liczb calkowitych jest dokladne i niezalezne
    od kolejnosci sumowania, wiec liczba watkow BLAS nie zmienia wyniku.
    """

    def __init__(self, embedder, entries, descriptions=None):
        import numpy as np

        opisy = descriptions or {}
        self.embedder = embedder
        self.items = []
        self.texts = []
        wektory = []
        for entry in entries:
            path = str(entry["path"])
            for row in entry["symbols"]:
                # M9b: gdy podano opisy, tekst symbolu to regula M7 PLUS opis jego pliku.
                # Bez opisow wynik jest identyczny z M7 — `symbol_text_with_description`
                # z pustym opisem zwraca doslownie `symbol_text`.
                tekst = symbol_text_with_description(path, row, opisy.get(path, ""))
                self.items.append((path, row, entry.get("lang")))
                self.texts.append(tekst)
                wektory.append(embedder.vector(tekst))
        self.M = (np.vstack(wektory) if wektory
                  else np.zeros((0, embedder.dim), dtype=np.int64))
        # Kwadraty norm, NIE normy. Pierwiastek brany raz, na koncu — dwa obciecia
        # `isqrt` po drodze potrafily dac wynik powyzej 1000 promili (patrz embed.py).
        self.norms2 = [int(np.dot(v, v)) for v in self.M]

    def scores(self, question):
        import math

        import numpy as np

        qv = self.embedder.vector(question)
        nq2 = int(np.dot(qv, qv))
        if nq2 == 0:
            return [0] * len(self.items)
        iloczyny = self.M @ qv
        out = []
        for d, nd2 in zip(iloczyny, self.norms2):
            d = int(d)
            if d <= 0 or nd2 == 0:
                out.append(0)
            else:
                out.append(math.isqrt((1000 * 1000 * d * d) // (nq2 * nd2)))
        return out


def _lexical_scores(index, entries, terms):
    """Wynik leksykalny w TEJ SAMEJ kolejnosci co `index.items`."""
    rarity = term_rarity(entries, terms)
    return [score_symbol(path, row, terms, rarity) for path, row, _ in index.items]


def _order(index, klucze):
    """
    Pozycje symboli wg podanych kluczy, malejaco, z tym samym rozstrzyganiem remisow
    co ranking bazowy: wynik, sciezka, linia, nazwa.
    """
    numery = sorted(
        range(len(index.items)),
        key=lambda i: (-klucze[i], index.items[i][0], index.items[i][1]["line"],
                       index.items[i][1]["name_path"]),
    )
    pozycje = [0] * len(index.items)
    for miejsce, i in enumerate(numery, 1):
        pozycje[i] = miejsce
    return numery, pozycje


def _pack(index, numery, wyniki, depth):
    out = []
    for i in numery[:depth]:
        path, row, lang = index.items[i]
        out.append({"score": int(wyniki[i]), "path": path, "lang": lang, "row": row})
    return out


def rank_embed(index, question, depth):
    """M7a: ranking wylacznie po podobienstwie semantycznym."""
    sims = index.scores(question)
    numery, _ = _order(index, sims)
    ranked = _pack(index, numery, sims, depth)
    paragony = []
    for pozycja in numery[:3]:
        path, row, _ = index.items[pozycja]
        # Paragon MUSI liczyc na tym samym tekscie, z ktorego powstal wektor — inaczej
        # rozklad nie sumuje sie do wyniku. Przy M7 `texts` to doslownie `symbol_text`.
        pary = embed_receipt(index.embedder, question, index.texts[pozycja])
        if pary:
            paragony.append({
                "rule": "embed_similarity",
                "symbol": f"{path}:{row['name_path']}",
                "permille": int(sims[pozycja]),
                "pairs": [p.as_dict() for p in pary],
            })
    return ranked, paragony


def rank_embed_tie(index, entries, question, terms, depth):
    """
    M7b: leksyka glowna, embedding WYLACZNIE jako rozstrzygniecie remisow.

    Z konstrukcji nie moze zmienic kolejnosci miedzy roznymi wynikami leksykalnymi,
    wiec nie moze zepsuc tych pytan, ktore juz dzialaja. Dziala tylko tam, gdzie leksyka
    milczy — a tam wlasnie lezy 36% przypadkow z pomiaru diagnostycznego.
    """
    lex = _lexical_scores(index, entries, terms)
    sims = index.scores(question)
    numery = sorted(
        range(len(index.items)),
        key=lambda i: (-lex[i], -sims[i], index.items[i][0], index.items[i][1]["line"],
                       index.items[i][1]["name_path"]),
    )
    ranked = _pack(index, numery, lex, depth)
    paragony = [{
        "rule": "embed_tiebreak",
        "note": "embedding rozstrzyga wylacznie remisy leksykalne",
        "lexical_zero_in_top": sum(1 for i in numery[:depth] if lex[i] == 0),
    }]
    return ranked, paragony


def rank_embed_borda(index, entries, question, terms, depth):
    """M7c: suma rang z obu list. Fuzja bez ani jednego pokretla."""
    lex = _lexical_scores(index, entries, terms)
    sims = index.scores(question)
    _, poz_lex = _order(index, lex)
    _, poz_emb = _order(index, sims)
    borda = [-(poz_lex[i] + poz_emb[i]) for i in range(len(index.items))]
    numery, _ = _order(index, borda)
    ranked = _pack(index, numery, borda, depth)
    paragony = [{
        "rule": "embed_borda",
        "note": "wynik = -(pozycja leksykalna + pozycja semantyczna)",
        "top": [
            {
                "symbol": f"{index.items[i][0]}:{index.items[i][1]['name_path']}",
                "rank_lexical": poz_lex[i],
                "rank_embed": poz_emb[i],
            }
            for i in numery[:3]
        ],
    }]
    return ranked, paragony


def evaluate(entries, ctx, queries, variant, depth=DEPTH):
    positives, negatives, per_query = [], [], []
    diagnostyka = {
        "gate_cut": 0, "gate_fallback": 0, "gate_sizes": [],
        "m7_zero_bucket": 0, "m7_zero_reached_25": 0, "m7_zero_ranks": [],
        "desc_zero_bucket": 0, "desc_zero_nonzero": 0,
        "desc_zero_reached_25": 0, "desc_zero_ranks": [],
    }
    for q in queries:
        terms = query_terms(q["question"])
        receipts: list[dict] = []
        if variant == "baseline":
            ranked = rank_baseline(entries, terms, depth)
        elif variant == "bm25f":
            ranked = ctx["index"].rank(terms, depth)
        elif variant in ("prf_code", "prf_prose", "assoc", "prf_desc"):
            rule = {
                "prf_code": "code_window",
                "prf_prose": "prose_cooccurrence",
                "assoc": "docstring_cooccurrence",
                "prf_desc": "description_cooccurrence",
            }[variant]
            ranked, receipts = rank_with_expansion(
                entries, terms, depth, ctx["corpus"], ctx["vocabulary"], ctx["pack_hash"], rule,
            )
        elif variant in ("graph", "graph_desc"):
            ranked, receipts = rank_graph(
                entries, terms, depth, ctx["graph"],
                descriptions=ctx["descriptions"] if variant == "graph_desc" else None,
            )
        elif variant == "codebook":
            ranked, receipts = rank_codebook(
                entries, terms, depth, ctx["codebook"], ctx["symtok"],
            )
        elif variant in ("gate", "gate_desc"):
            # `ctx["scope"]` jest juz zbudowany na wlasciwym zrodle prozy — dla `gate_desc`
            # na opisach, dla `gate` na commitach i chunkach CBMS. Sama bramka bez zmian.
            ranked, receipts, pliki, fallback = rank_gate(entries, terms, depth, ctx["scope"])
            diagnostyka["gate_sizes"].append(len(pliki))
            if fallback:
                diagnostyka["gate_fallback"] += 1
            elif q["kind"] == "positive" and not (set(q["answer_files"]) & pliki):
                # Warunek diagnostyczny (propozycja GPT): bramka wyciela wlasciwy plik.
                diagnostyka["gate_cut"] += 1
        elif variant == "desc":
            opisy = ctx["descriptions"]
            pelny, rarity_desc = rank_desc_all(entries, terms, opisy)
            ranked = pelny[:depth]
            receipts = desc_receipt(pelny, terms, opisy, rarity_desc, RECEIPT_LIMIT)

            # WARUNEK DIAGNOSTYCZNY M8 — czy most w ogole zostal zbudowany.
            # Wsrod pytan, gdzie wlasciwy symbol ma leksykalne ZERO: ilu z nich opis
            # daje wynik niezerowy? Zadna metoda przeliczajaca nie ruszy zera (0*x=0),
            # wiec to jest jedyna liczba mowiaca wprost, czy opisy niosa slowa, ktorymi
            # pyta czlowiek. Niezaleznie od werdyktu pass/fail.
            if q["kind"] == "positive":
                rarity_bazowa = term_rarity(entries, terms)
                cele = [
                    (str(e["path"]), row)
                    for e in entries
                    for row in e["symbols"]
                    if is_hit({"path": str(e["path"]), "row": row, "lang": e.get("lang")}, q)
                ]
                if cele and max(score_symbol(p, r, terms, rarity_bazowa) for p, r in cele) == 0:
                    diagnostyka["desc_zero_bucket"] += 1
                    najlepszy = max(
                        score_with_description(p, r, terms, rarity_desc, opisy.get(p, ""))
                        for p, r in cele
                    )
                    if najlepszy > 0:
                        diagnostyka["desc_zero_nonzero"] += 1
                        pozycja = next((i for i, it in enumerate(pelny, 1) if is_hit(it, q)), 0)
                        if pozycja:
                            diagnostyka["desc_zero_ranks"].append(pozycja)
                            if pozycja <= 25:
                                diagnostyka["desc_zero_reached_25"] += 1
        elif variant in ("embed", "embed_tie", "embed_borda",
                         "embed_desc", "embed_desc_tie", "embed_desc_borda"):
            # `ctx["embed"]` zbudowany z opisami albo bez — sam sposob laczenia identyczny.
            index = ctx["embed"]
            if variant in ("embed", "embed_desc"):
                ranked, receipts = rank_embed(index, q["question"], depth)
            elif variant in ("embed_tie", "embed_desc_tie"):
                ranked, receipts = rank_embed_tie(index, entries, q["question"], terms, depth)
            else:
                ranked, receipts = rank_embed_borda(index, entries, q["question"], terms, depth)

            # WARUNEK DIAGNOSTYCZNY M7 — najwazniejsza liczba tego etapu.
            # Wsrod pytan, gdzie wlasciwy symbol ma leksykalne ZERO: ile embedding
            # wciaga do top-25? Zadna metoda leksykalna ich nie tknie, bo 0*x = 0.
            if q["kind"] == "positive":
                lex = _lexical_scores(index, entries, terms)
                cele = [
                    i for i, (path, row, lang) in enumerate(index.items)
                    if is_hit({"path": path, "row": row, "lang": lang}, q)
                ]
                if cele and max(lex[i] for i in cele) == 0:
                    diagnostyka["m7_zero_bucket"] += 1
                    sims = index.scores(q["question"])
                    numery, pozycje = _order(index, sims)
                    najlepsza = min(pozycje[i] for i in cele)
                    diagnostyka["m7_zero_ranks"].append(najlepsza)
                    if najlepsza <= 25:
                        diagnostyka["m7_zero_reached_25"] += 1
        else:
            raise SystemExit(f"nieznany wariant: {variant}")

        top1 = ranked[0]["score"] if ranked else 0
        if q["kind"] == "negative":
            negatives.append(top1)
            per_query.append({
                "id": q["id"], "kind": "negative", "top1_score": top1,
                "returned": len(ranked), "expansion": receipts,
            })
            continue

        rank_of_hit = 0
        for position, item in enumerate(ranked, 1):
            if is_hit(item, q):
                rank_of_hit = position
                break

        # DIAGNOSTYKA WSPOLNA M9 (prerejestracja 2026-08-12T23:53).
        # Wsrod pytan, gdzie wlasciwy symbol ma w BASELINIE wynik leksykalny ZERO —
        # ile wchodzi do top-25 w TYM wariancie. Punkt odniesienia: M8 dal 0 z 11
        # przy medianie rangi 200. Liczone identycznie dla kazdego wariantu, zeby
        # cztery powtorki byly porownywalne miedzy soba i z M8.
        rarity_bazowa = term_rarity(entries, terms)
        cele_bazowe = [
            (str(e["path"]), row)
            for e in entries
            for row in e["symbols"]
            if is_hit({"path": str(e["path"]), "row": row, "lang": e.get("lang")}, q)
        ]
        if cele_bazowe and max(
            score_symbol(p, r, terms, rarity_bazowa) for p, r in cele_bazowe
        ) == 0:
            diagnostyka["m9_zero_bucket"] += 1
            if rank_of_hit:
                diagnostyka["m9_zero_in_top25"] += 1

        positives.append({"id": q["id"], "rank": rank_of_hit, "top1": top1})
        per_query.append({
            "id": q["id"], "kind": "positive", "rank": rank_of_hit, "top1_score": top1,
            "hit_at_10": bool(rank_of_hit and rank_of_hit <= 10),
            "hit_at_25": bool(rank_of_hit and rank_of_hit <= 25),
            "expansion": receipts,
        })

    n = max(1, len(positives))
    recall = {f"recall_at_{k}_permille": sum(1000 for p in positives if p["rank"] and p["rank"] <= k) // n for k in TOP_K}
    mrr_permille = sum((1000 // p["rank"]) for p in positives if p["rank"]) // n
    mean_pos_top1 = sum(p["top1"] for p in positives) // n
    mean_neg_top1 = sum(negatives) // max(1, len(negatives))
    neg_ratio = (mean_neg_top1 * 1000) // max(1, mean_pos_top1)

    return {
        "counts": {"positive": len(positives), "negative": len(negatives)},
        **recall,
        "mrr_permille": mrr_permille,
        "mean_top1_positive": mean_pos_top1,
        "mean_top1_negative": mean_neg_top1,
        "negative_ratio_permille": neg_ratio,
        "gate_cut": diagnostyka["gate_cut"],
        "gate_fallback": diagnostyka["gate_fallback"],
        "gate_size_median": (
            sorted(diagnostyka["gate_sizes"])[len(diagnostyka["gate_sizes"]) // 2]
            if diagnostyka["gate_sizes"] else 0
        ),
        "m7_zero_bucket": diagnostyka["m7_zero_bucket"],
        "m7_zero_reached_25": diagnostyka["m7_zero_reached_25"],
        "m7_zero_rank_median": (
            sorted(diagnostyka["m7_zero_ranks"])[len(diagnostyka["m7_zero_ranks"]) // 2]
            if diagnostyka["m7_zero_ranks"] else 0
        ),
        "desc_zero_bucket": diagnostyka["desc_zero_bucket"],
        "desc_zero_nonzero": diagnostyka["desc_zero_nonzero"],
        "desc_zero_reached_25": diagnostyka["desc_zero_reached_25"],
        "desc_zero_rank_median": (
            sorted(diagnostyka["desc_zero_ranks"])[len(diagnostyka["desc_zero_ranks"]) // 2]
            if diagnostyka["desc_zero_ranks"] else 0
        ),
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablacja M4 dla ACAE.")
    parser.add_argument(
        "--variant", required=True,
        choices=("baseline", "bm25f", "prf_code", "prf_prose", "graph", "assoc", "codebook",
                 "gate", "embed", "embed_tie", "embed_borda", "desc"),
    )
    parser.add_argument("--set", dest="qset", default="dev", choices=tuple(SETS))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    repo_root = ACAE_DIR.parent
    with (ACAE_DIR / "config" / "acae.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    qpath = ACAE_DIR / SETS[args.qset]
    queries = json.loads(qpath.read_bytes())["queries"]

    locator = FsLocator(
        root=str(repo_root), roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    reader = FsReader(str(repo_root))
    entries, _ = collect_entries(locator, reader)

    ctx: dict = {"index": None, "corpus": None, "vocabulary": None, "pack_hash": ""}
    if args.variant == "bm25f":
        ctx["index"] = Bm25fIndex(entries)
    elif args.variant == "graph":
        ctx["graph"] = build_graph(entries, reader)
    elif args.variant == "codebook":
        ctx["codebook"] = Codebook()
        ctx["symtok"] = SymbolTokens(entries)
    elif args.variant == "gate":
        ctx["scope"] = ScopeIndex(entries, reader, str(repo_root))
    elif args.variant in ("embed", "embed_tie", "embed_borda"):
        # Weryfikacja hashy jest wlaczona: podmieniony artefakt ma zatrzymac pomiar,
        # a nie po cichu wyprodukowac liczby, ktore wygladaja sensownie.
        ctx["embed"] = EmbedIndex(StaticEmbedder(ACAE_DIR / "_model"), entries)
    elif args.variant == "desc":
        # pack_hash liczony TERAZ i porownywany z tym, dla ktorego powstaly opisy.
        # Rozjazd przerywa pomiar: opisy nieaktualnego kodu daja liczby, ktore wygladaja
        # sensownie i nie znacza nic. Ta sama regula co weryfikacja hashy modelu w M7.
        pack_hash = build_pack(PackRequest(root=repo_root.name), locator, reader).pack_hash
        ctx["descriptions"], ctx["desc_provenance"] = load_descriptions(
            ACAE_DIR / "_desc" / "descriptions.json", expected_pack_hash=pack_hash,
        )
        ctx["pack_hash"] = pack_hash
    elif args.variant in ("prf_code", "prf_prose", "assoc"):
        if args.variant == "prf_code":
            documents = code_window_documents(entries, reader)
        elif args.variant == "prf_prose":
            documents = prose_documents(str(repo_root))
        else:
            documents = docstring_documents()
        ctx["corpus"] = Corpus(documents)
        ctx["vocabulary"] = symbol_vocabulary(entries)
        # pack_hash trafia do kazdego paragonu jako warunek waznosci — krawedz
        # wyprowadzona dla jednego stanu repo nie moze cicho przezyc jego zmiany.
        ctx["pack_hash"] = build_pack(PackRequest(root=repo_root.name), locator, reader).pack_hash

    result = evaluate(entries, ctx, queries, args.variant)

    payload = {
        "schema": SCHEMA,
        "variant": args.variant,
        "question_set": {
            "name": args.qset,
            "file": qpath.name,
            "content_hash": content_hash(qpath.read_bytes()),
        },
        "head": run_git(["rev-parse", "--short", "HEAD"], repo_root),
        "scope": {"files": len(entries), "symbols": sum(len(e["symbols"]) for e in entries)},
        "depth": DEPTH,
        "packages": {"tiktoken": metadata.version("tiktoken")},
        "metrics": {k: v for k, v in result.items() if k != "per_query"},
        "per_query": result["per_query"],
    }
    if args.variant == "desc":
        # Prowieniencja opisow w wyniku pomiaru: model, data, pack_hash zrodla.
        # Bez tego po miesiacu nie da sie powiedziec, ktore opisy dały te liczby.
        payload["descriptions"] = ctx["desc_provenance"]

    payload["result_hash"] = content_hash(canonical_json(payload))

    out_rel = args.out or f"_baseline/m4_{args.variant}_{args.qset}_{payload['head']}.json"
    out_path = ACAE_DIR / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_json(payload, indent=2))

    m = payload["metrics"]
    print(f"wariant   {args.variant}   zbior {args.qset} ({m['counts']['positive']}+/{m['counts']['negative']}-)")
    print(f"recall@10 {m['recall_at_10_permille']/10:.1f}%")
    print(f"recall@25 {m['recall_at_25_permille']/10:.1f}%")
    print(f"MRR       {m['mrr_permille']/1000:.3f}")
    print(f"kontrola  negatywy/pozytywy = {m['negative_ratio_permille']/10:.1f}%  (nizej = lepiej)")
    print(f"zapis     {out_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

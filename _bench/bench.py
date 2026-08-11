# -*- coding: utf-8 -*-
"""AIONS 2 / Faza 0 - pomiar latencji Chroma.

Rozdziela trzy koszty:
  A) query(query_texts=...)      = embedding zapytania + przeszukanie indeksu
  B) ef([tekst])                 = SAM embedding zapytania (ONNX MiniLM)
  C) query(query_embeddings=...) = SAMO przeszukanie indeksu (bez embeddingu)

Uzycie:
  python bench.py --mode embedded --path <chroma_dir> --collection <name>
  python bench.py --mode http --host 127.0.0.1 --port 8000 --collection <name>
"""
import argparse, json, random, statistics, sys, time
import chromadb
from chromadb.utils import embedding_functions

P = argparse.ArgumentParser()
P.add_argument("--mode", default="embedded", choices=["embedded", "http"])
P.add_argument("--path", default=r"E:\server wiedzy\data\chroma")
P.add_argument("--host", default="127.0.0.1")
P.add_argument("--port", type=int, default=8000)
P.add_argument("--collection", required=True)
P.add_argument("--n-queries", type=int, default=50)
P.add_argument("--seed", type=int, default=42)
A = P.parse_args()


def pct(vals_ms, q):
    """Percentyl metoda nearest-rank (bez interpolacji) - jawnie zdefiniowany."""
    s = sorted(vals_ms)
    if not s:
        return None
    idx = max(0, min(len(s) - 1, int(round(q / 100.0 * len(s) + 0.5)) - 1))
    return s[idx]


def summary(vals_ms):
    return {
        "n": len(vals_ms),
        "min": round(min(vals_ms), 3),
        "p50": round(pct(vals_ms, 50), 3),
        "p95": round(pct(vals_ms, 95), 3),
        "max": round(max(vals_ms), 3),
        "mean": round(statistics.fmean(vals_ms), 3),
    }


# --- cold start klienta ---
t0 = time.perf_counter()
if A.mode == "embedded":
    client = chromadb.PersistentClient(path=A.path)
else:
    client = chromadb.HttpClient(host=A.host, port=A.port)
coll = client.get_collection(name=A.collection)
t_client_ms = (time.perf_counter() - t0) * 1000.0

total = coll.count()

# --- 50 REALNYCH dokumentow z kolekcji jako zapytania ---
got = coll.get(include=["documents"])
docs = [d for d in (got.get("documents") or []) if d and d.strip()]
random.seed(A.seed)
queries = random.sample(docs, min(A.n_queries, len(docs)))

# --- embedding function: dokladnie ta, ktorej uzywa Chroma domyslnie ---
ef = embedding_functions.ONNXMiniLM_L6_V2()
t0 = time.perf_counter()
_warm = ef(["warmup"])
t_ef_coldstart_ms = (time.perf_counter() - t0) * 1000.0
dim = len(_warm[0])

# --- warmup indeksu (pierwszy query laduje HNSW do RAM - nie liczymy go) ---
t0 = time.perf_counter()
coll.query(query_texts=[queries[0]], n_results=5)
t_first_query_ms = (time.perf_counter() - t0) * 1000.0
for q in queries[:5]:
    coll.query(query_texts=[q], n_results=5)

out = {
    "mode": A.mode,
    "collection": A.collection,
    "count": total,
    "embed_dim": dim,
    "n_queries": len(queries),
    "cold_client_init_ms": round(t_client_ms, 3),
    "cold_ef_first_call_ms": round(t_ef_coldstart_ms, 3),
    "cold_first_query_ms": round(t_first_query_ms, 3),
    "results": {},
}

# --- B) SAM embedding zapytania (niezalezny od n_results) ---
t_embed = []
for q in queries:
    t0 = time.perf_counter()
    ef([q])
    t_embed.append((time.perf_counter() - t0) * 1000.0)
out["results"]["B_embed_only"] = summary(t_embed)

# precompute wektorow do pomiaru C
vecs = [ef([q])[0] for q in queries]

for k in (5, 20):
    # --- A) pelny query: embedding + indeks ---
    t_full = []
    for q in queries:
        t0 = time.perf_counter()
        coll.query(query_texts=[q], n_results=k)
        t_full.append((time.perf_counter() - t0) * 1000.0)

    # --- C) SAM indeks: podajemy gotowy wektor ---
    t_idx = []
    for v in vecs:
        t0 = time.perf_counter()
        coll.query(query_embeddings=[v], n_results=k)
        t_idx.append((time.perf_counter() - t0) * 1000.0)

    out["results"]["A_full_query_texts_n%d" % k] = summary(t_full)
    out["results"]["C_index_only_n%d" % k] = summary(t_idx)

print(json.dumps(out, ensure_ascii=False, indent=1))

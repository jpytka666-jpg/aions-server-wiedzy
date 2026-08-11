# -*- coding: utf-8 -*-
"""AIONS 2 / Faza 0 - inwentaryzacja Chroma (lokalnie, Windows venv)."""
import json, os, sqlite3, sys, traceback
import chromadb

CHROMA = r"E:\server wiedzy\data\chroma"
SQLITE = os.path.join(CHROMA, "chroma.sqlite3")

print("python", sys.version.split()[0])
print("chromadb", chromadb.__version__)
print("path", CHROMA)

# --- 1. surowy schemat sqlite: wymiar per kolekcja (autorytatywne zrodlo) ---
meta_by_name = {}
try:
    con = sqlite3.connect(SQLITE)
    cols_info = [r[1] for r in con.execute("PRAGMA table_info(collections)")]
    print("SQLITE collections columns:", cols_info)
    sel = ",".join(cols_info)
    for row in con.execute("SELECT %s FROM collections" % sel):
        d = dict(zip(cols_info, row))
        meta_by_name[d.get("name")] = d
except Exception as e:
    print("SQLITE_ERR", repr(e))
    traceback.print_exc()

# --- 2. klient Chroma + lista kolekcji ---
client = chromadb.PersistentClient(path=CHROMA)
cols = client.list_collections()
print("num_collections", len(cols))

rows = []
for c in cols:
    try:
        n = c.count()
    except Exception as e:
        n = "ERR:%r" % (e,)
    ef = getattr(c, "_embedding_function", None)
    sq = meta_by_name.get(c.name, {})
    rows.append({
        "name": c.name,
        "count": n,
        "dim_sqlite": sq.get("dimension"),
        "config_json": sq.get("config_json_str"),
        "metadata": c.metadata,
        "ef_class_runtime": type(ef).__name__ if ef is not None else None,
        "ef_module_runtime": type(ef).__module__ if ef is not None else None,
    })

rows.sort(key=lambda r: -(r["count"] if isinstance(r["count"], int) else -1))
print("=== COLLECTIONS (sorted by count desc) ===")
print(json.dumps(rows, ensure_ascii=False, indent=1, default=str))

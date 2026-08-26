#!/usr/bin/env python3
# ==========================================
# AUTHOR: M. SZUL
# AI MODEL: Claude Opus 5
# TIMESTAMP: 2026-08-26 00:00:00
# REASON FOR CREATION: The CBMS discovery record is worth little if the only way to
#   consult it is to read it end to end. This turns the record into a searchable index
#   so a later session can ask "was the Korean injection real?" and get the finding
#   with its evidence, instead of re-deriving it for the fourth time.
# MECHANICS: Reads findings.json, measurements.json and the ARCHITECTURE.md sections,
#   turns each into one document with flat metadata, and upserts them into a Chroma
#   collection held in a directory belonging to this project alone. Refuses to run
#   against the live AIONS store: a second writer on that file is exactly the
#   corruption the conductor exists to prevent.
# SYSTEM PART: discovery/ - CBMS structure recovery
# ARCHITECTURE FUNCTION: Derived index, never the source. Git holds the truth; this
#   database is disposable and can be rebuilt from the JSON and Markdown at any time.
# DEPENDENCIES/LINKS: chromadb 0.5.3 (present in the project venv); reads
#   discovery/cbms/findings.json, discovery/cbms/measurements.json,
#   discovery/cbms/ARCHITECTURE.md
# TECH STACK: Python 3 + Chroma. Chroma because the rest of the knowledge server
#   already runs on it - a second vector store would be a second thing to keep alive
#   on a machine that is already short of memory. Its default embedding model is
#   cached locally, so ingest works with the network down.
# LOCAL WORKSPACE: worktree of aions-server-wiedzy, branch discovery/cbms-structure
# GIT COMMIT: PENDING
# GITHUB METADATA: jpytka666-jpg/aions-server-wiedzy, branch discovery/cbms-structure
# ==========================================
"""Build the CBMS discovery index. Own database, never the live one."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CBMS = HERE / "cbms"
COLLECTION = "cbms_discovery"


def refuse_live_store(target: Path) -> None:
    """Never open the running server's database. Two writers corrupt it.

    The check is deliberately blunt: any path the environment points the live
    server at, and any path that simply looks like the live store, is refused.
    A false refusal costs one command-line flag; a false pass costs the store.
    """
    resolved = target.resolve()
    forbidden = []
    for var in ("CHROMA_PATH", "AIONS_CHROMA_PATH"):
        val = os.environ.get(var)
        if val:
            forbidden.append(Path(val).resolve())
    for bad in forbidden:
        if resolved == bad or bad in resolved.parents or resolved in bad.parents:
            raise SystemExit(
                f"refusing: {resolved} overlaps the live store at {bad}.\n"
                f"Pass --db with a directory of this project's own."
            )
    parts = [p.lower() for p in resolved.parts]
    if "chroma" in parts and "data" in parts:
        raise SystemExit(
            f"refusing: {resolved} looks like the live AIONS store (…/data/chroma).\n"
            f"Pass --db with a directory of this project's own."
        )


def split_markdown(path: Path):
    """One document per '## ' section - a section is the unit somebody would quote."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    docs = []
    preamble = parts[0].strip()
    if preamble:
        docs.append(("intro", preamble))
    for chunk in parts[1:]:
        title, _, body = chunk.partition("\n")
        docs.append((title.strip(), ("## " + chunk).strip()))
    return docs


def flatten(value) -> str:
    """Chroma metadata takes scalars only; anything richer is stored as JSON text."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return json.dumps(value, ensure_ascii=False)


def build_documents():
    ids, docs, metas = [], [], []

    findings_path = CBMS / "findings.json"
    if not findings_path.exists():
        raise SystemExit(f"missing {findings_path} - the record is the input, build it first")
    record = json.loads(findings_path.read_text(encoding="utf-8"))

    for f in record.get("findings", []):
        ids.append(f"finding:{f['id']}")
        docs.append(
            f"[{f['status']}] {f['claim']}\n\nEvidence:\n"
            + json.dumps(f.get("evidence", {}), indent=2, ensure_ascii=False)
        )
        metas.append({
            "kind": "finding",
            "finding_id": f["id"],
            "status": f["status"],
            "claim": f["claim"][:400],
            "source": "discovery/cbms/findings.json",
        })

    structure = record.get("structure", {})
    for key, value in structure.items():
        ids.append(f"structure:{key}")
        docs.append(f"CBMS structure - {key}\n\n" + json.dumps(value, indent=2, ensure_ascii=False))
        metas.append({"kind": "structure", "section": key, "source": "discovery/cbms/findings.json"})

    for i, q in enumerate(record.get("open_questions", []), 1):
        ids.append(f"open:{i:02d}")
        docs.append(f"OPEN QUESTION: {q}")
        metas.append({"kind": "open_question", "source": "discovery/cbms/findings.json"})

    for i, (title, body) in enumerate(split_markdown(CBMS / "ARCHITECTURE.md")):
        ids.append(f"arch:{i:02d}")
        docs.append(body)
        metas.append({"kind": "architecture", "section": title[:200], "source": "discovery/cbms/ARCHITECTURE.md"})

    measurements = CBMS / "measurements.json"
    if measurements.exists():
        m = json.loads(measurements.read_text(encoding="utf-8"))
        for key in ("stores", "manifest", "addressing", "codebook_layer", "reference_graph"):
            if key not in m:
                continue
            ids.append(f"measure:{key}")
            docs.append(f"Measurement of the live CBMS store - {key}\n\n"
                        + json.dumps(m[key], indent=2, ensure_ascii=False))
            metas.append({
                "kind": "measurement",
                "section": key,
                "measured_from": flatten(m.get("measured_from")),
                "source": "discovery/cbms/measurements.json",
            })
        ids.append("measure:concepts")
        docs.append("Concept histogram of the live CBMS store\n\n"
                    + json.dumps(m.get("concepts", {}), indent=2, ensure_ascii=False))
        metas.append({"kind": "measurement", "section": "concepts",
                      "source": "discovery/cbms/measurements.json"})

    return ids, docs, metas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=HERE / ".chroma",
                    help="directory for this project's own Chroma database")
    ap.add_argument("--embed", choices=("default", "multilingual"), default="default",
                    help="'default' uses Chroma's bundled model (cached locally); "
                         "'multilingual' uses a locally cached sentence-transformers model, "
                         "better on Polish text")
    ap.add_argument("--query", type=str, default=None,
                    help="after ingest, run this question against the index as a smoke test")
    args = ap.parse_args()

    refuse_live_store(args.db)

    try:
        import chromadb
    except ImportError:
        raise SystemExit("chromadb is not importable - run this with the project venv interpreter")

    ids, docs, metas = build_documents()

    embedding_fn = None
    if args.embed == "multilingual":
        from chromadb.utils import embedding_functions
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

    args.db.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(args.db))
    kwargs = {"name": COLLECTION, "metadata": {"hnsw:space": "cosine"}}
    if embedding_fn is not None:
        kwargs["embedding_function"] = embedding_fn
    collection = client.get_or_create_collection(**kwargs)

    collection.upsert(ids=ids, documents=docs, metadatas=metas)

    print(f"db         : {args.db}")
    print(f"collection : {COLLECTION}")
    print(f"documents  : {collection.count()}")
    by_kind = {}
    for m in metas:
        by_kind[m["kind"]] = by_kind.get(m["kind"], 0) + 1
    for kind, n in sorted(by_kind.items()):
        print(f"  {kind:<14} {n}")

    if args.query:
        print(f"\nquery: {args.query}")
        res = collection.query(query_texts=[args.query], n_results=3)
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            label = meta.get("finding_id") or meta.get("section") or meta["kind"]
            print(f"\n  [{dist:.3f}] {meta['kind']} / {label}")
            print("  " + doc[:300].replace("\n", "\n  "))
    return 0


if __name__ == "__main__":
    sys.exit(main())

import json
import os
import re
import hashlib
from pathlib import Path
from typing import List

try:
    from korean_keys import build_keys
except Exception as exc:
    raise SystemExit(f"Missing korean_keys module: {exc}")


SENT_SPLIT = re.compile(r"(?<=[\.!?])\s+")


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    parts = SENT_SPLIT.split(text)
    out = []
    for s in parts:
        s = s.strip()
        if 30 <= len(s) <= 240:
            out.append(s)
    return out


def make_id(prefix: str, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12].upper()
    return prefix + h


def main():
    # Resolve memory directory from env or repo root
    root = Path(__file__).resolve().parent.parent
    mem = Path(os.environ.get('CBMS_MEMORY_DIR', str(root / 'memory')))
    chunks_dir = mem / "chunks"
    if not chunks_dir.exists():
        raise SystemExit(f"Chunks dir not found: {chunks_dir}")
    out_facts = mem / "facts.jsonl"
    out_index = mem / "facts_index.json"
    facts = []
    inv = {}

    # Read all chunks (CBMS memory)
    for f in sorted(chunks_dir.glob("*.json")):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        cid = obj.get("id") or f.stem
        content = obj.get("content", "")
        for sent in split_sentences(content):
            fid = make_id("F", cid + "|" + sent)
            keys = list(build_keys(sent))
            rec = {"id": fid, "chunk_id": cid, "text": sent, "keys": keys}
            facts.append(rec)
            for k in keys:
                inv.setdefault(k, []).append(fid)

    # Also read RAG chunks from AGI_CODex if available
    rag_dir = Path(r"D:/AGI_CODex/chunks")
    if rag_dir.exists():
        for rf in sorted(rag_dir.glob("chunk_*.bin")):
            try:
                text = rf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            rcid = rf.stem.upper()
            for sent in split_sentences(text):
                fid = make_id("R", rcid + "|" + sent)
                keys = list(build_keys(sent))
                rec = {"id": fid, "chunk_id": rcid, "text": sent, "keys": keys}
                facts.append(rec)
                for k in keys:
                    inv.setdefault(k, []).append(fid)

    # Ingest additional local knowledge (text/markdown/json summaries)
    extra_dirs = [
        Path(r"D:/phi3"),
        Path(r"E:/CBMS_EXTRACT/AIONS_COMPLETE_BACKUP_20250912_231853/AIONS_DATA"),
        Path(r"E:/AI DEVELOPMENT/WORK SPACE/IMPORT FROM_E/BIELIK_KOREAN_CBMS"),
        Path(r"E:/AI DEVELOPMENT/WORK SPACE/IMPORT FROM_E/AIONS_RIGOROUS_BENCHMARKS"),
    ]
    for ed in extra_dirs:
        if not ed.exists():
            continue
        for pf in ed.rglob("*.md"):
            try:
                text = pf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for sent in split_sentences(text):
                fid = make_id("D", str(pf) + "|" + sent)
                keys = list(build_keys(sent))
                rec = {"id": fid, "chunk_id": pf.name, "text": sent, "keys": keys}
                facts.append(rec)
                for k in keys:
                    inv.setdefault(k, []).append(fid)
        for pf in ed.rglob("*.txt"):
            try:
                text = pf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for sent in split_sentences(text):
                fid = make_id("D", str(pf) + "|" + sent)
                keys = list(build_keys(sent))
                rec = {"id": fid, "chunk_id": pf.name, "text": sent, "keys": keys}
                facts.append(rec)
                for k in keys:
                    inv.setdefault(k, []).append(fid)
        for pf in ed.rglob("*.json"):
            try:
                raw = pf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # Try to extract short sentences from JSON as plain text
            try:
                obj = json.loads(raw)
                text = json.dumps(obj, ensure_ascii=False)
            except Exception:
                text = raw
            for sent in split_sentences(text):
                fid = make_id("J", str(pf) + "|" + sent)
                keys = list(build_keys(sent))
                rec = {"id": fid, "chunk_id": pf.name, "text": sent, "keys": keys}
                facts.append(rec)
                for k in keys:
                    inv.setdefault(k, []).append(fid)

    # Write outputs (UTF-8 no BOM)
    with out_facts.open("w", encoding="utf-8") as fh:
        for rec in facts:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out_index.write_text(json.dumps({"index": inv}, ensure_ascii=False), encoding="utf-8")
    print(f"Built facts: {len(facts)} records; keys: {len(inv)} -> {out_facts}")


if __name__ == "__main__":
    main()

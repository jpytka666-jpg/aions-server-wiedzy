import json
from pathlib import Path
from typing import Dict, Set, Any

try:
    from korean_keys import build_keys
except Exception:
    def build_keys(text: str):
        return set()


class Facts:
    def __init__(self, mem_root: str):
        self.mem = Path(mem_root)
        self.index_path = self.mem / "facts_index.json"
        self.facts_path = self.mem / "facts.jsonl"
        self.index: Dict[str, Any] = {}
        if self.index_path.exists():
            try:
                self.index = json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                self.index = {}

    def coverage(self, query: str) -> int:
        """Return number of unique facts touched by query keys."""
        if not self.index:
            return 0
        qks: Set[str] = set(build_keys(query))
        inv = self.index.get("index", {})
        seen: Set[str] = set()
        for k in qks:
            for fid in inv.get(k, []):
                seen.add(fid)
        return len(seen)

    def coverage_hashed(self, query: str) -> int:
        """Return facts coverage using only hashed keys (prefix 'h:')."""
        if not self.index:
            return 0
        qks: Set[str] = set(build_keys(query))
        inv = self.index.get("index", {})
        seen: Set[str] = set()
        for k in qks:
            if not k.startswith('h:'):
                continue
            for fid in inv.get(k, []):
                seen.add(fid)
        return len(seen)

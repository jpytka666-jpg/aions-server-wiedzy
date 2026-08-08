"""
ts_symbols.py — warstwa wzroku symbolicznego dla CBMS.

CZYM TO NIE JEST
----------------
To nie jest przepisana Serena. Serena wystawia symbole PO TO, zeby agent je czytal:
jej wyjscie to odpowiedz na pytanie "pokaz mi ten symbol". Tutaj wyjsciem sa
KANDYDACI NA CHUNKI CBMS — jednostki wiedzy gotowe do wejscia do magazynu, z miekkimi
referencjami zgodnymi z resolverem z refgraph v2.

Roznica jest zasadnicza: Serena zyje w czasie sesji agenta, ts_symbols zyje w czasie
zycia pamieci. Dlatego kazdy symbol dostaje:
  - `name_path`  — adres logiczny (Klasa/metoda), NIE numer linii
  - `body_hash`  — zeby wykryc dryf bez reparsowania calego drzewa
  - `outline`    — sam szkielet, bez cial; do wzorca outline-then-drill
  - `references` — miekkie wskazowki (wywolania, dziedziczenie, importy) do pozniejszego
                   rozstrzygniecia przez SoftGraph, a nie twarde wskazniki

ZALEZNOSCI
    tree-sitter>=0.26, tree-sitter-language-pack>=1.14   (zainstalowane w venv AIONS)

CLI
    python ts_symbols.py --file server/crla_core.py --outline
    python ts_symbols.py --file server/crla_core.py --symbol CRLACore/evaluate
    python ts_symbols.py --dir server --outline --json
    python ts_symbols.py --dir server --as-chunks out/code_chunks.json
    python ts_symbols.py --file x.py --drift out/prev_hashes.json

MODUL
    from ts_symbols import SymbolIndex
    idx = SymbolIndex.from_file("server/crla_core.py")
    idx.outline()                      -> [{name_path, kind, line, signature}]
    idx.get("CRLACore/evaluate")       -> Symbol z cialem
    idx.as_chunk_candidates()          -> [dict gotowy do CBMS]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

try:
    from tree_sitter_language_pack import get_parser
except ImportError:  # pragma: no cover
    get_parser = None

# Mapowanie rozszerzenie -> jezyk tree-sittera. Rozszerzalne bez dotykania logiki.
LANGS = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".go": "go", ".rs": "rust",
    ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".rb": "ruby", ".php": "php", ".cs": "c_sharp", ".sh": "bash",
    ".lua": "lua", ".kt": "kotlin", ".swift": "swift",
}

# Wezly, ktore uznajemy za symbol. Nazwy typow sa wspolne dla wiekszosci gramatyk.
DEF_NODES = {
    "function_definition": "function",
    "function_declaration": "function",
    "method_definition": "method",
    "method_declaration": "method",
    "class_definition": "class",
    "class_declaration": "class",
    "struct_item": "struct",
    "impl_item": "impl",
    "interface_declaration": "interface",
    "type_alias_declaration": "type",
    "decorated_definition": "decorated",
}

# Wezly niosace potencjalna referencje wychodzaca.
REF_NODES = {"call", "call_expression", "identifier", "attribute",
             "import_statement", "import_from_statement", "type_identifier"}

BUILTINS = {
    "print", "len", "str", "int", "float", "dict", "list", "set", "tuple", "bool",
    "range", "open", "isinstance", "super", "self", "type", "sorted", "enumerate",
    "min", "max", "sum", "any", "all", "zip", "map", "filter", "repr", "format",
    "getattr", "setattr", "hasattr", "append", "get", "items", "keys", "values",
    "join", "split", "strip", "lower", "upper", "replace", "startswith", "endswith",
}


def sha12(data: str) -> str:
    return hashlib.sha1(data.encode("utf-8", "replace")).hexdigest()[:12]


class Symbol:
    __slots__ = ("name", "name_path", "kind", "start_line", "end_line",
                 "signature", "body", "body_hash", "refs", "file", "docstring")

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw.get(s))

    def outline_row(self) -> dict:
        return {"name_path": self.name_path, "kind": self.kind,
                "line": self.start_line, "lines": (self.end_line or 0) - (self.start_line or 0) + 1,
                "signature": self.signature, "body_hash": self.body_hash,
                "n_refs": len(self.refs or [])}

    def as_dict(self, with_body=False) -> dict:
        d = self.outline_row()
        d.update({"file": self.file, "docstring": self.docstring, "refs": sorted(self.refs or [])})
        if with_body:
            d["body"] = self.body
        return d


class SymbolIndex:
    def __init__(self, path: str, source: str, lang: str):
        self.path = path
        self.source = source
        self.lang = lang
        self.symbols: dict[str, Symbol] = {}

    # --------------------------------------------------------------- parsing

    @classmethod
    def from_file(cls, path: str) -> "SymbolIndex":
        if get_parser is None:
            raise RuntimeError("brak tree_sitter_language_pack — zainstaluj w venv")
        ext = os.path.splitext(path)[1].lower()
        lang = LANGS.get(ext)
        if not lang:
            raise ValueError(f"nieobslugiwane rozszerzenie: {ext}")
        with open(path, "rb") as fh:
            raw = fh.read()
        idx = cls(path, raw.decode("utf-8", "replace"), lang)
        tree = get_parser(lang).parse(raw)
        idx._walk(tree.root_node, [], raw)
        return idx

    def _node_name(self, node, raw: bytes) -> str | None:
        for field in ("name", "declarator", "type"):
            child = node.child_by_field_name(field)
            if child is not None:
                txt = raw[child.start_byte:child.end_byte].decode("utf-8", "replace")
                m = re.match(r"[A-Za-z_][\w]*", txt.strip())
                if m:
                    return m.group(0)
        for child in node.children:
            if child.type in ("identifier", "type_identifier", "field_identifier"):
                return raw[child.start_byte:child.end_byte].decode("utf-8", "replace")
        return None

    def _walk(self, node, stack, raw: bytes):
        kind = DEF_NODES.get(node.type)
        pushed = False

        if kind:
            # decorated_definition owija wlasciwa definicje — schodzimy glebiej
            if kind == "decorated":
                for child in node.children:
                    if child.type in DEF_NODES:
                        self._walk(child, stack, raw)
                return
            name = self._node_name(node, raw)
            if name:
                path = "/".join(stack + [name])
                body = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")
                first = body.split("\n", 1)[0].strip()
                self.symbols[path] = Symbol(
                    name=name, name_path=path, kind=kind,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=first[:200],
                    body=body, body_hash=sha12(body),
                    refs=self._collect_refs(node, raw, skip=name),
                    file=self.path, docstring=self._docstring(body),
                )
                stack = stack + [name]
                pushed = True

        for child in node.children:
            self._walk(child, stack, raw)
        if pushed:
            stack.pop()

    @staticmethod
    def _docstring(body: str) -> str | None:
        m = re.search(r'"""(.*?)"""', body, re.S)
        if m:
            return " ".join(m.group(1).split())[:300]
        return None

    def _collect_refs(self, node, raw: bytes, skip=None) -> set:
        """Miekkie wskazowki wychodzace. Nie rozstrzygamy ich tutaj — od tego jest SoftGraph."""
        found = set()

        def rec(n, depth=0):
            if depth > 40:
                return
            if n.type in ("call", "call_expression"):
                fn = n.child_by_field_name("function")
                if fn is not None:
                    txt = raw[fn.start_byte:fn.end_byte].decode("utf-8", "replace")
                    txt = txt.split("(")[0].strip()
                    if txt and txt not in BUILTINS and len(txt) > 2:
                        found.add(txt.replace("self.", ""))
            elif n.type in ("import_statement", "import_from_statement"):
                txt = raw[n.start_byte:n.end_byte].decode("utf-8", "replace")
                for m in re.finditer(r"[\w.]+", txt):
                    tok = m.group(0)
                    if tok not in ("import", "from", "as") and len(tok) > 2:
                        found.add(tok)
            for c in n.children:
                rec(c, depth + 1)

        rec(node)
        found.discard(skip)
        return {f for f in found if f not in BUILTINS}

    # --------------------------------------------------------------- queries

    def outline(self) -> list:
        """Sam szkielet — bez cial. To jest polowa wzorca outline-then-drill."""
        return [s.outline_row() for s in
                sorted(self.symbols.values(), key=lambda x: x.start_line)]

    def get(self, name_path: str):
        if name_path in self.symbols:
            return self.symbols[name_path]
        low = name_path.lower()
        for k, v in self.symbols.items():          # miekkie dopasowanie po sufiksie
            if k.lower().endswith(low):
                return v
        return None

    def hashes(self) -> dict:
        return {p: s.body_hash for p, s in self.symbols.items()}

    def drift(self, previous: dict) -> dict:
        """Co sie zmienilo od poprzedniego skanu — bez reparsowania calosci projektu."""
        now = self.hashes()
        return {
            "added": sorted(set(now) - set(previous)),
            "removed": sorted(set(previous) - set(now)),
            "changed": sorted(p for p in set(now) & set(previous) if now[p] != previous[p]),
            "unchanged": len([p for p in set(now) & set(previous) if now[p] == previous[p]]),
        }

    def as_chunk_candidates(self) -> list:
        """Wyjscie w ksztalcie chunka CBMS. To jest to, czego Serena nie robi."""
        out = []
        for s in sorted(self.symbols.values(), key=lambda x: x.start_line):
            if s.kind in ("impl", "decorated"):
                continue
            rel = self.path.replace("\\", "/")
            content = (s.docstring + "\n\n" if s.docstring else "") + (s.body or "")
            out.append({
                "id": "KTS" + sha12(rel + "#" + s.name_path).upper(),
                "concept": "code_symbol",
                "content": content[:4000],
                "size": len(content[:4000]),
                "source": "ts_symbols",
                "provenance": "parsed",          # brakujace pole, o ktore krzyczy cbms_doctor
                "symbol": {"name_path": s.name_path, "kind": s.kind,
                           "file": rel, "line": s.start_line,
                           "body_hash": s.body_hash, "signature": s.signature},
                "references": sorted(s.refs or []) + [rel],
            })
        return out


def scan_dir(root: str, exts=None) -> dict:
    exts = exts or set(LANGS)
    skip = {".git", "__pycache__", "venv", "node_modules", ".mypy_cache", "chunks",
            "chunks_quarantine", "backups"}
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in exts:
                fp = os.path.join(dirpath, fn)
                try:
                    result[fp] = SymbolIndex.from_file(fp)
                except (OSError, ValueError, RuntimeError):
                    continue
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Wzrok symboliczny dla CBMS (tree-sitter)")
    ap.add_argument("--file")
    ap.add_argument("--dir")
    ap.add_argument("--outline", action="store_true")
    ap.add_argument("--symbol", metavar="NAME_PATH")
    ap.add_argument("--as-chunks", metavar="OUT_JSON")
    ap.add_argument("--drift", metavar="PREV_HASHES_JSON")
    ap.add_argument("--save-hashes", metavar="OUT_JSON")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-items", type=int, default=25)
    a = ap.parse_args(argv)

    if get_parser is None:
        print("BLAD: brak tree_sitter_language_pack w tym interpreterze", file=sys.stderr)
        return 2
    if not a.file and not a.dir:
        ap.error("podaj --file albo --dir")

    if a.file:
        idx = SymbolIndex.from_file(a.file)
        indexes = {a.file: idx}
    else:
        indexes = scan_dir(a.dir)

    out = {}
    if a.symbol:
        for path, idx in indexes.items():
            s = idx.get(a.symbol)
            if s:
                out["symbol"] = s.as_dict(with_body=True)
                break
        else:
            out["symbol"] = None
    if a.outline or (not a.symbol and not a.as_chunks and not a.drift):
        rows = []
        for path, idx in indexes.items():
            for r in idx.outline():
                r["file"] = path.replace("\\", "/")
                rows.append(r)
        out["outline"] = rows
        out["summary"] = {"files": len(indexes), "symbols": len(rows)}
    if a.drift:
        with open(a.drift, encoding="utf-8") as fh:
            prev = json.load(fh)
        merged = {}
        for idx in indexes.values():
            merged.update(idx.hashes())
        tmp = SymbolIndex("", "", "")
        tmp.symbols = {k: Symbol(name_path=k, body_hash=v) for k, v in merged.items()}
        out["drift"] = tmp.drift(prev)
    if a.save_hashes:
        merged = {}
        for idx in indexes.values():
            merged.update(idx.hashes())
        with open(a.save_hashes, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, ensure_ascii=False, indent=2)
        out["hashes_written"] = a.save_hashes
    if a.as_chunks:
        cands = []
        for idx in indexes.values():
            cands.extend(idx.as_chunk_candidates())
        os.makedirs(os.path.dirname(os.path.abspath(a.as_chunks)) or ".", exist_ok=True)
        with open(a.as_chunks, "w", encoding="utf-8") as fh:
            json.dump(cands, fh, ensure_ascii=False, indent=2)
        out["chunk_candidates"] = {"count": len(cands), "written_to": a.as_chunks}

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    for section, payload in out.items():
        print("== " + section.upper() + " ==")
        if isinstance(payload, list):
            for row in payload[:a.max_items]:
                if isinstance(row, dict) and "name_path" in row:
                    print("  %-42s %-9s L%-5s %3s ln  refs=%-3s %s"
                          % (row["name_path"], row["kind"], row["line"],
                             row["lines"], row["n_refs"], row["body_hash"]))
                else:
                    print("  " + str(row))
            if len(payload) > a.max_items:
                print("  ... i %d wiecej" % (len(payload) - a.max_items))
        elif isinstance(payload, dict):
            for k, v in payload.items():
                sv = str(v)
                print("  %-16s %s" % (k, sv[:300] + ("..." if len(sv) > 300 else "")))
        else:
            print("  " + str(payload))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

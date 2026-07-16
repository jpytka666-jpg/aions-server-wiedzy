"""
TURBO PROJECT SCANNER v1.0
==========================
Uzywa Everything CLI do BLYSKLAWICZNEGO znajdowania plikow.
Zamiast godzin -> minuty!

Autor: Marcin Szul / AIONS Project
"""

import os
import sys
import re
import json
import hashlib
import ast
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import concurrent.futures
import threading

# =============================================================================
# CONFIG
# =============================================================================

EVERYTHING_CLI = Path("C:/Program Files/Everything/es.exe")

CODE_EXTENSIONS = "py;pyw;js;jsx;ts;tsx;mjs;cjs;java;kt;c;cpp;h;hpp;cs;go;rs;rb;php;lua;pl;sh;bash;ps1;psm1;bat;cmd"
CONFIG_EXTENSIONS = "json;yaml;yml;toml;ini;cfg;conf;xml;env"
DOC_EXTENSIONS = "md;markdown;rst;txt;adoc;html;htm"

ALL_EXTENSIONS = f"{CODE_EXTENSIONS};{CONFIG_EXTENSIONS};{DOC_EXTENSIONS}"

IGNORE_PATTERNS = [
    "__pycache__", "node_modules", ".git", ".svn", 
    "venv", ".venv", "env", "site-packages",
    "dist", "build", ".idea", ".vscode",
    "\\windows\\winsxs\\", "\\windows\\system32\\",
    "$recycle.bin", "system volume information",
]

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    size: int
    modified: str
    hash_md5: str
    line_count: int
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: str = ""

@dataclass 
class ScanResult:
    scan_id: str
    timestamp: str
    total_files: int
    total_size: int
    scan_time_seconds: float
    files: Dict[str, FileInfo] = field(default_factory=dict)
    duplicates: Dict[str, List[str]] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    reverse_graph: Dict[str, List[str]] = field(default_factory=dict)
    orphans: List[str] = field(default_factory=list)
    hubs: List[str] = field(default_factory=list)
    broken_imports: List[Tuple[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

# =============================================================================
# EVERYTHING SEARCH
# =============================================================================

def everything_search(extensions: str = ALL_EXTENSIONS, folders: List[str] = None) -> List[str]:
    """Use Everything CLI to find all files INSTANTLY"""
    
    if not EVERYTHING_CLI.exists():
        raise FileNotFoundError(f"Everything CLI not found at {EVERYTHING_CLI}")
    
    ALLOWED_EXT = {e.strip().lower().lstrip(".") for e in extensions.split(";") if e.strip()}

    if folders:
        all_files: List[str] = []
        seen: Set[str] = set()
        for folder in folders:
            prefix = folder.strip().strip('"').replace("/", "\\")
            if not prefix.endswith("\\"):
                prefix += "\\"
            query = f"{prefix}*"
            print(f"[TURBO] Everything query: {query}")
            cmd = [str(EVERYTHING_CLI), "-n", "999999", query]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            if result.returncode != 0:
                print(f"[WARN] Everything failed for {folder}: {result.stderr[:200]}")
                continue
            for f in result.stdout.strip().split("\n"):
                f = f.strip()
                if f and f not in seen:
                    seen.add(f)
                    all_files.append(f)
    else:
        query = f"ext:{extensions}"
        print(f"[TURBO] Everything query: {query}")
        cmd = [str(EVERYTHING_CLI), "-n", "999999", query]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"Everything search failed: {result.stderr}")
        all_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    
    # Filter out ignored patterns and (when scoped) non-target extensions
    filtered = []
    for f in all_files:
        f_lower = f.lower()
        if any(ign in f_lower for ign in IGNORE_PATTERNS):
            continue
        if folders:
            ext = Path(f).suffix.lower().lstrip(".")
            if ext not in ALLOWED_EXT:
                continue
        filtered.append(f)
    
    print(f"[TURBO] Found {len(filtered)} files (filtered from {len(all_files)})")
    return filtered

# =============================================================================
# FILE PROCESSING
# =============================================================================

def hash_file_fast(path: str) -> str:
    """Quick MD5 hash"""
    try:
        with open(path, 'rb') as f:
            # Read only first 64KB for speed (good enough for duplicate detection)
            data = f.read(65536)
            return hashlib.md5(data).hexdigest()
    except:
        return ""

def count_lines_fast(path: str) -> int:
    """Fast line count"""
    try:
        with open(path, 'rb') as f:
            return sum(1 for _ in f)
    except:
        return 0

def parse_python_imports(path: str) -> List[str]:
    """Parse Python imports"""
    imports = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError:
            # Fallback to regex
            for match in re.finditer(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE):
                imports.append(match.group(1))
    except:
        pass
    
    return list(set(imports))

def parse_js_imports(path: str) -> List[str]:
    """Parse JavaScript imports"""
    imports = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        patterns = [
            r'require\(["\']([^"\']+)["\']\)',
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
            r'import\s+["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                imports.append(match.group(1))
    except:
        pass
    
    return list(set(imports))

def parse_file_imports(path: str) -> List[str]:
    """Parse imports based on file type"""
    ext = Path(path).suffix.lower()
    
    if ext in {'.py', '.pyw'}:
        return parse_python_imports(path)
    elif ext in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}:
        return parse_js_imports(path)
    
    return []

def categorize_file(path: str) -> List[str]:
    """Auto-categorize file"""
    categories = []
    path_lower = path.lower()
    
    if 'test' in path_lower:
        categories.append('test')
    if 'doc' in path_lower or 'readme' in path_lower:
        categories.append('documentation')
    if 'config' in path_lower or 'setting' in path_lower:
        categories.append('config')
    if 'util' in path_lower or 'helper' in path_lower:
        categories.append('utility')
    if 'server' in path_lower or 'api' in path_lower:
        categories.append('server')
    if 'aions' in path_lower or 'cbms' in path_lower:
        categories.append('aions')
    
    return categories if categories else ['general']

def process_file(path: str) -> Optional[FileInfo]:
    """Process single file"""
    try:
        p = Path(path)
        if not p.exists():
            return None
        
        stat = p.stat()
        
        return FileInfo(
            path=str(p.absolute()),
            name=p.name,
            extension=p.suffix.lower(),
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            hash_md5=hash_file_fast(path),
            line_count=count_lines_fast(path),
            imports=parse_file_imports(path),
            categories=categorize_file(path),
        )
    except Exception as e:
        return None

# =============================================================================
# TURBO SCANNER
# =============================================================================

class TurboScanner:
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("scan_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.result: Optional[ScanResult] = None
        self.lock = threading.Lock()
        self.processed = 0
        self.scan_folders: List[str] = []
        
    def scan(self, folders: List[str] = None) -> ScanResult:
        """TURBO SCAN - uses Everything + parallel processing"""
        
        start_time = datetime.now()
        scan_id = start_time.strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*60}")
        print(f"TURBO SCANNER - Starting {scan_id}")
        print(f"{'='*60}\n")
        
        self.result = ScanResult(
            scan_id=scan_id,
            timestamp=start_time.isoformat(),
            total_files=0,
            total_size=0,
            scan_time_seconds=0,
        )
        
        self.scan_folders = folders or []
        
        # Phase 1: Everything search (INSTANT)
        print("[PHASE 1] Finding files with Everything...")
        phase1_start = datetime.now()
        
        try:
            all_files = everything_search(ALL_EXTENSIONS, folders)
        except Exception as e:
            self.result.errors.append(f"Everything search failed: {e}")
            print(f"[ERROR] {e}")
            return self.result
        
        phase1_time = (datetime.now() - phase1_start).total_seconds()
        print(f"[PHASE 1] Complete in {phase1_time:.2f}s - Found {len(all_files)} files")
        
        # Phase 2: Process files in parallel
        print(f"\n[PHASE 2] Processing files (parallel)...")
        phase2_start = datetime.now()
        
        hash_to_paths: Dict[str, List[str]] = defaultdict(list)
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_file, f): f for f in all_files}
            
            for future in concurrent.futures.as_completed(futures):
                file_info = future.result()
                if file_info:
                    with self.lock:
                        self.result.files[file_info.path] = file_info
                        self.result.total_files += 1
                        self.result.total_size += file_info.size
                        
                        if file_info.hash_md5:
                            hash_to_paths[file_info.hash_md5].append(file_info.path)
                        
                        self.processed += 1
                        if self.processed % 500 == 0:
                            print(f"[PHASE 2] Processed {self.processed}/{len(all_files)} files...")
        
        phase2_time = (datetime.now() - phase2_start).total_seconds()
        print(f"[PHASE 2] Complete in {phase2_time:.2f}s")
        
        # Phase 3: Detect duplicates
        print(f"\n[PHASE 3] Detecting duplicates...")
        for hash_val, paths in hash_to_paths.items():
            if len(paths) > 1:
                self.result.duplicates[hash_val] = paths
                for dup_path in paths[1:]:
                    if dup_path in self.result.files:
                        self.result.files[dup_path].is_duplicate = True
                        self.result.files[dup_path].duplicate_of = paths[0]
        
        print(f"[PHASE 3] Found {len(self.result.duplicates)} duplicate groups")
        
        # Phase 4: Build dependency graph
        print(f"\n[PHASE 4] Building dependency graph...")
        self._build_dependency_graph()
        print(f"[PHASE 4] Complete")
        
        # Phase 5: Analyze
        print(f"\n[PHASE 5] Analyzing...")
        self._analyze_graph()
        print(f"[PHASE 5] Complete")
        
        # Calculate total time
        total_time = (datetime.now() - start_time).total_seconds()
        self.result.scan_time_seconds = total_time
        
        # Save results
        self._save_results()
        
        print(f"\n{'='*60}")
        print(f"TURBO SCAN COMPLETE!")
        print(f"{'='*60}")
        print(f"Files: {self.result.total_files}")
        print(f"Size: {self.result.total_size / 1024 / 1024:.2f} MB")
        print(f"Duplicates: {len(self.result.duplicates)} groups")
        print(f"Hubs: {len(self.result.hubs)}")
        print(f"Orphans: {len(self.result.orphans)}")
        print(f"Time: {total_time:.2f} seconds")
        print(f"Results: {self.output_dir / self.result.scan_id}")
        
        return self.result
    
    def _build_dependency_graph(self):
        """Build dependency graph"""
        for file_path, file_info in self.result.files.items():
            resolved_deps = []
            
            for imp in file_info.imports:
                resolved = self._resolve_import(imp, file_path)
                if resolved:
                    resolved_deps.append(resolved)
                    if resolved not in self.result.reverse_graph:
                        self.result.reverse_graph[resolved] = []
                    self.result.reverse_graph[resolved].append(file_path)
                else:
                    self.result.broken_imports.append((file_path, imp))
            
            self.result.dependency_graph[file_path] = resolved_deps
    
    def _resolve_import(self, import_name: str, from_file: str) -> Optional[str]:
        """Try to resolve import to actual file"""
        if '.' in import_name and not import_name.endswith(('.py', '.js')):
            py_path = import_name.replace('.', os.sep) + '.py'
        else:
            py_path = import_name
        
        # Search in scanned files
        for scanned_path in self.result.files:
            if scanned_path.endswith(py_path) or import_name in scanned_path:
                return scanned_path
        
        return None
    
    def _analyze_graph(self):
        """Analyze dependency graph"""
        all_files = set(self.result.files.keys())
        imported_files = set()
        
        for deps in self.result.dependency_graph.values():
            imported_files.update(deps)
        
        # Orphans
        self.result.orphans = list(all_files - imported_files)
        
        # Hubs
        import_counts = [(f, len(importers)) for f, importers in self.result.reverse_graph.items()]
        import_counts.sort(key=lambda x: x[1], reverse=True)
        self.result.hubs = [f for f, c in import_counts[:50] if c > 1]
    
    def _save_results(self):
        """Save results"""
        scan_dir = self.output_dir / self.result.scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        
        # Summary
        summary = {
            "scan_id": self.result.scan_id,
            "timestamp": self.result.timestamp,
            "scan_paths": self.scan_folders or ["(all indexed by Everything)"],
            "total_files": self.result.total_files,
            "total_size": self.result.total_size,
            "total_size_mb": round(self.result.total_size / 1024 / 1024, 2),
            "scan_time_seconds": round(self.result.scan_time_seconds, 2),
            "duplicates": len(self.result.duplicates),
            "hubs": len(self.result.hubs),
            "orphans": len(self.result.orphans),
            "broken_imports": len(self.result.broken_imports),
        }
        
        with open(scan_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        
        # Files
        files_data = {p: asdict(info) for p, info in self.result.files.items()}
        with open(scan_dir / "files.json", "w", encoding="utf-8") as f:
            json.dump(files_data, f, indent=2, ensure_ascii=False)
        
        # Duplicates
        with open(scan_dir / "duplicates.json", "w", encoding="utf-8") as f:
            json.dump(self.result.duplicates, f, indent=2)
        
        # Dependencies
        with open(scan_dir / "dependencies.json", "w", encoding="utf-8") as f:
            json.dump({
                "forward": self.result.dependency_graph,
                "reverse": self.result.reverse_graph,
            }, f, indent=2)
        
        # Analysis
        with open(scan_dir / "analysis.json", "w", encoding="utf-8") as f:
            json.dump({
                "hubs": self.result.hubs,
                "orphans": self.result.orphans[:500],  # Limit size
                "broken_imports": self.result.broken_imports[:200],
            }, f, indent=2)
        
        # Markdown report
        self._generate_report(scan_dir)
    
    def _generate_report(self, scan_dir: Path):
        """Generate markdown report"""
        r = self.result
        
        report = f"""# TURBO Scan Report

**Scan ID:** {r.scan_id}  
**Date:** {r.timestamp}  
**Scan Time:** {r.scan_time_seconds:.2f} seconds

## Summary

| Metric | Value |
|--------|-------|
| Total Files | {r.total_files} |
| Total Size | {r.total_size / 1024 / 1024:.2f} MB |
| Duplicates | {len(r.duplicates)} groups |
| Hub Files | {len(r.hubs)} |
| Orphan Files | {len(r.orphans)} |
| Broken Imports | {len(r.broken_imports)} |

## Hub Files (Most Imported)

"""
        for hub in r.hubs[:30]:
            count = len(r.reverse_graph.get(hub, []))
            name = Path(hub).name
            report += f"- **{name}** ({count} importers): `{hub}`\n"
        
        report += f"\n## Duplicate Groups ({len(r.duplicates)})\n\n"
        
        for i, (h, paths) in enumerate(list(r.duplicates.items())[:20]):
            report += f"### Group {i+1}\n"
            for p in paths:
                info = r.files.get(p)
                mod = info.modified[:10] if info else "?"
                report += f"- `{p}` ({mod})\n"
            report += "\n"
        
        report += f"\n## AIONS Related Files\n\n"
        aions_files = [p for p in r.files if 'aions' in p.lower() or 'cbms' in p.lower()]
        for f in aions_files[:50]:
            report += f"- `{f}`\n"
        
        with open(scan_dir / "REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TURBO Project Scanner (Everything-powered)")
    parser.add_argument("folders", nargs="*", help="Folders to scan (optional, scans all if empty)")
    parser.add_argument("-o", "--output", default="scan_results", help="Output directory")
    
    args = parser.parse_args()
    
    scanner = TurboScanner(output_dir=Path(args.output))
    
    folders = args.folders if args.folders else None
    result = scanner.scan(folders)
    
    return 0 if result.total_files > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

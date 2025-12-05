"""
UNIVERSAL PROJECT SCANNER v1.0
==============================
Skanuje WSZYSTKO, buduje graf zależności, wykrywa duble.
Działa OFFLINE bez AI - zapisuje wyniki do ChromaDB i plików.

Nie fixuje się na żadnej nazwie projektu - skanuje co dostanie.

Autor: Marcin Szul / AIONS Project
"""

import os
import sys
import re
import json
import hashlib
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import traceback

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FileInfo:
    """Information about a scanned file"""
    path: str
    name: str
    extension: str
    size: int
    modified: str
    hash_md5: str
    hash_sha256: str
    line_count: int
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: str = ""
    
@dataclass
class ScanResult:
    """Complete scan result"""
    scan_id: str
    timestamp: str
    paths_scanned: List[str]
    total_files: int
    total_size: int
    files: Dict[str, FileInfo] = field(default_factory=dict)
    duplicates: Dict[str, List[str]] = field(default_factory=dict)  # hash -> [paths]
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)  # file -> [imports]
    reverse_graph: Dict[str, List[str]] = field(default_factory=dict)  # file -> [imported_by]
    orphans: List[str] = field(default_factory=list)  # files nothing imports
    hubs: List[str] = field(default_factory=list)  # files imported by many
    broken_imports: List[Tuple[str, str]] = field(default_factory=list)  # (file, missing_import)
    circular_deps: List[List[str]] = field(default_factory=list)  # cycles
    errors: List[str] = field(default_factory=list)

# =============================================================================
# FILE EXTENSIONS
# =============================================================================

CODE_EXTENSIONS = {
    '.py', '.pyw',
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.java', '.kt', '.scala',
    '.c', '.cpp', '.h', '.hpp', '.cc',
    '.cs', '.fs',
    '.go',
    '.rs',
    '.rb',
    '.php',
    '.swift',
    '.r', '.R',
    '.lua',
    '.pl', '.pm',
    '.sh', '.bash', '.zsh',
    '.ps1', '.psm1', '.psd1',
    '.bat', '.cmd',
}

CONFIG_EXTENSIONS = {
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.plist',
    '.env', '.properties',
}

DOC_EXTENSIONS = {
    '.md', '.markdown', '.rst', '.txt', '.adoc',
    '.html', '.htm',
}

ALL_EXTENSIONS = CODE_EXTENSIONS | CONFIG_EXTENSIONS | DOC_EXTENSIONS

# =============================================================================
# IGNORE PATTERNS
# =============================================================================

IGNORE_DIRS = {
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', 'bower_components',
    '.venv', 'venv', 'env', '.env',
    'dist', 'build', 'target', 'out',
    '.idea', '.vscode', '.vs',
    'eggs', '*.egg-info',
    '.tox', '.pytest_cache', '.mypy_cache',
    'site-packages',
}

IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    '*.pyc', '*.pyo', '*.pyd',
    '*.so', '*.dll', '*.dylib',
    '*.exe', '*.bin',
    '*.log', '*.tmp', '*.temp',
}

# =============================================================================
# HASH FUNCTIONS
# =============================================================================

def hash_file(path: Path, algorithms: List[str] = ['md5', 'sha256']) -> Dict[str, str]:
    """Calculate file hashes"""
    hashes = {alg: hashlib.new(alg) for alg in algorithms}
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                for h in hashes.values():
                    h.update(chunk)
        return {alg: h.hexdigest() for alg, h in hashes.items()}
    except Exception:
        return {alg: "" for alg in algorithms}

def count_lines(path: Path) -> int:
    """Count lines in file"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

# =============================================================================
# IMPORT PARSERS
# =============================================================================

def parse_python_imports(content: str, file_path: Path) -> List[str]:
    """Parse Python imports"""
    imports = []
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
        patterns = [
            r'^import\s+([\w.]+)',
            r'^from\s+([\w.]+)\s+import',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
    
    # Also catch sys.path manipulations
    sys_path_pattern = r'sys\.path\.\w+\(["\']([^"\']+)["\']\)'
    for match in re.finditer(sys_path_pattern, content):
        imports.append(f"PATH:{match.group(1)}")
    
    return list(set(imports))

def parse_javascript_imports(content: str, file_path: Path) -> List[str]:
    """Parse JavaScript/TypeScript imports"""
    imports = []
    patterns = [
        r'require\(["\']([^"\']+)["\']\)',
        r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
        r'import\s+["\']([^"\']+)["\']',
        r'export\s+.*?\s+from\s+["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            imports.append(match.group(1))
    return list(set(imports))

def parse_json_references(content: str, file_path: Path) -> List[str]:
    """Parse JSON file references"""
    refs = []
    try:
        data = json.loads(content)
        refs = extract_paths_from_dict(data)
    except json.JSONDecodeError:
        pass
    return refs

def extract_paths_from_dict(obj, refs=None) -> List[str]:
    """Recursively extract path-like strings from dict"""
    if refs is None:
        refs = []
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and looks_like_path(v):
                refs.append(v)
            else:
                extract_paths_from_dict(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            extract_paths_from_dict(item, refs)
    elif isinstance(obj, str) and looks_like_path(obj):
        refs.append(obj)
    
    return refs

def looks_like_path(s: str) -> bool:
    """Check if string looks like a file path"""
    if len(s) < 3 or len(s) > 500:
        return False
    path_indicators = ['/', '\\', '.py', '.js', '.json', '.md', '.yaml', '.txt']
    return any(ind in s for ind in path_indicators)

def parse_markdown_links(content: str, file_path: Path) -> List[str]:
    """Parse Markdown links and references"""
    refs = []
    patterns = [
        r'\[.*?\]\(([^)]+)\)',  # [text](link)
        r'\[.*?\]:\s*(\S+)',     # [ref]: url
        r'`([^`]*(?:\.py|\.js|\.json|\.md|\.yaml)[^`]*)`',  # inline code with paths
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            ref = match.group(1)
            if not ref.startswith(('http://', 'https://', 'mailto:')):
                refs.append(ref)
    return list(set(refs))

def parse_shell_references(content: str, file_path: Path) -> List[str]:
    """Parse shell script references"""
    refs = []
    patterns = [
        r'source\s+["\']?([^"\';\s]+)["\']?',
        r'\.\s+["\']?([^"\';\s]+)["\']?',
        r'python\s+["\']?([^"\';\s]+\.py)["\']?',
        r'node\s+["\']?([^"\';\s]+\.js)["\']?',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            refs.append(match.group(1))
    return list(set(refs))

def parse_powershell_references(content: str, file_path: Path) -> List[str]:
    """Parse PowerShell script references"""
    refs = []
    patterns = [
        r'\.\s+["\']?([^"\';\s]+\.ps1)["\']?',
        r'Import-Module\s+["\']?([^"\';\s]+)["\']?',
        r'-File\s+["\']?([^"\';\s]+)["\']?',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            refs.append(match.group(1))
    return list(set(refs))

# =============================================================================
# MAIN PARSER
# =============================================================================

def parse_file_imports(path: Path) -> Tuple[List[str], List[str]]:
    """Parse imports/references from any file type"""
    imports = []
    references = []
    
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return [], []
    
    ext = path.suffix.lower()
    
    if ext in {'.py', '.pyw'}:
        imports = parse_python_imports(content, path)
    elif ext in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}:
        imports = parse_javascript_imports(content, path)
    elif ext == '.json':
        references = parse_json_references(content, path)
    elif ext in {'.md', '.markdown', '.rst', '.txt'}:
        references = parse_markdown_links(content, path)
    elif ext in {'.sh', '.bash', '.zsh'}:
        references = parse_shell_references(content, path)
    elif ext in {'.ps1', '.psm1', '.psd1'}:
        references = parse_powershell_references(content, path)
    elif ext in {'.yaml', '.yml', '.toml'}:
        references = parse_json_references(content, path)  # Similar logic works
    
    return imports, references

# =============================================================================
# CATEGORIZATION
# =============================================================================

def categorize_file(path: Path, content: str = "") -> List[str]:
    """Auto-categorize file based on path and content"""
    categories = []
    path_lower = str(path).lower()
    name_lower = path.name.lower()
    
    # By directory
    if 'test' in path_lower or 'spec' in path_lower:
        categories.append('test')
    if 'doc' in path_lower or 'readme' in name_lower:
        categories.append('documentation')
    if 'config' in path_lower or 'setting' in path_lower:
        categories.append('config')
    if 'script' in path_lower or 'bin' in path_lower:
        categories.append('script')
    if 'util' in path_lower or 'helper' in path_lower or 'lib' in path_lower:
        categories.append('utility')
    if 'model' in path_lower:
        categories.append('model')
    if 'server' in path_lower or 'api' in path_lower:
        categories.append('server')
    if 'client' in path_lower or 'ui' in path_lower or 'frontend' in path_lower:
        categories.append('frontend')
    
    # By extension
    ext = path.suffix.lower()
    if ext in CODE_EXTENSIONS:
        categories.append('code')
    if ext in CONFIG_EXTENSIONS:
        categories.append('config')
    if ext in DOC_EXTENSIONS:
        categories.append('doc')
    
    return categories if categories else ['unknown']

# =============================================================================
# SCANNER
# =============================================================================

class ProjectScanner:
    """Universal project scanner"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("scan_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.result: Optional[ScanResult] = None
        self.progress_callback = None
        
    def should_ignore_dir(self, dir_name: str) -> bool:
        """Check if directory should be ignored"""
        return dir_name in IGNORE_DIRS or dir_name.startswith('.')
    
    def should_ignore_file(self, file_name: str) -> bool:
        """Check if file should be ignored"""
        if file_name in IGNORE_FILES:
            return True
        for pattern in IGNORE_FILES:
            if '*' in pattern:
                if file_name.endswith(pattern.replace('*', '')):
                    return True
        return False
    
    def should_scan_file(self, path: Path) -> bool:
        """Check if file should be scanned"""
        return path.suffix.lower() in ALL_EXTENSIONS
    
    def scan(self, paths: List[str], extensions: Set[str] = None) -> ScanResult:
        """Scan given paths"""
        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result = ScanResult(
            scan_id=scan_id,
            timestamp=datetime.now().isoformat(),
            paths_scanned=paths,
            total_files=0,
            total_size=0,
        )
        
        if extensions:
            global ALL_EXTENSIONS
            ALL_EXTENSIONS = extensions
        
        hash_to_paths: Dict[str, List[str]] = defaultdict(list)
        
        # Phase 1: Scan files
        print(f"[SCAN] Starting scan of {len(paths)} paths...")
        
        for base_path in paths:
            base = Path(base_path)
            if not base.exists():
                self.result.errors.append(f"Path not found: {base_path}")
                continue
            
            if base.is_file():
                self._scan_file(base, hash_to_paths)
            else:
                for root, dirs, files in os.walk(base):
                    # Filter ignored directories
                    dirs[:] = [d for d in dirs if not self.should_ignore_dir(d)]
                    
                    for file_name in files:
                        if self.should_ignore_file(file_name):
                            continue
                        
                        file_path = Path(root) / file_name
                        if self.should_scan_file(file_path):
                            self._scan_file(file_path, hash_to_paths)
        
        # Phase 2: Detect duplicates
        print(f"[SCAN] Detecting duplicates...")
        for hash_val, file_paths in hash_to_paths.items():
            if len(file_paths) > 1:
                self.result.duplicates[hash_val] = file_paths
                # Mark duplicates (first one is "original")
                for dup_path in file_paths[1:]:
                    if dup_path in self.result.files:
                        self.result.files[dup_path].is_duplicate = True
                        self.result.files[dup_path].duplicate_of = file_paths[0]
        
        # Phase 3: Build dependency graph
        print(f"[SCAN] Building dependency graph...")
        self._build_dependency_graph()
        
        # Phase 4: Analyze graph
        print(f"[SCAN] Analyzing dependencies...")
        self._analyze_graph()
        
        # Phase 5: Save results
        print(f"[SCAN] Saving results...")
        self._save_results()
        
        print(f"[SCAN] Complete! {self.result.total_files} files scanned.")
        return self.result
    
    def _scan_file(self, path: Path, hash_to_paths: Dict[str, List[str]]):
        """Scan a single file"""
        try:
            stat = path.stat()
            hashes = hash_file(path)
            imports, refs = parse_file_imports(path)
            
            file_info = FileInfo(
                path=str(path.absolute()),
                name=path.name,
                extension=path.suffix.lower(),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                hash_md5=hashes.get('md5', ''),
                hash_sha256=hashes.get('sha256', ''),
                line_count=count_lines(path),
                imports=imports,
                references=refs,
                categories=categorize_file(path),
            )
            
            self.result.files[str(path.absolute())] = file_info
            self.result.total_files += 1
            self.result.total_size += stat.st_size
            
            # Track for duplicate detection
            if hashes.get('sha256'):
                hash_to_paths[hashes['sha256']].append(str(path.absolute()))
            
            if self.result.total_files % 100 == 0:
                print(f"[SCAN] Scanned {self.result.total_files} files...")
                
        except Exception as e:
            self.result.errors.append(f"Error scanning {path}: {e}")
    
    def _build_dependency_graph(self):
        """Build forward and reverse dependency graphs"""
        for file_path, file_info in self.result.files.items():
            # Forward graph
            all_deps = file_info.imports + file_info.references
            resolved_deps = []
            
            for dep in all_deps:
                resolved = self._resolve_import(dep, file_path)
                if resolved:
                    resolved_deps.append(resolved)
                    # Reverse graph
                    if resolved not in self.result.reverse_graph:
                        self.result.reverse_graph[resolved] = []
                    self.result.reverse_graph[resolved].append(file_path)
                else:
                    # Broken import
                    self.result.broken_imports.append((file_path, dep))
            
            self.result.dependency_graph[file_path] = resolved_deps
    
    def _resolve_import(self, import_name: str, from_file: str) -> Optional[str]:
        """Try to resolve import to actual file path"""
        # Check if it's already a path
        if import_name.startswith('PATH:'):
            import_name = import_name[5:]
        
        # Python module to path
        possible_paths = []
        
        # Direct path
        possible_paths.append(import_name)
        
        # Python style (dots to slashes)
        if '.' in import_name and not any(import_name.endswith(ext) for ext in ALL_EXTENSIONS):
            py_path = import_name.replace('.', os.sep)
            possible_paths.append(py_path + '.py')
            possible_paths.append(os.path.join(py_path, '__init__.py'))
        
        # Relative to file
        from_dir = Path(from_file).parent
        for pp in possible_paths:
            candidate = from_dir / pp
            if str(candidate.absolute()) in self.result.files:
                return str(candidate.absolute())
        
        # Absolute match
        for pp in possible_paths:
            for scanned_path in self.result.files:
                if scanned_path.endswith(pp) or pp in scanned_path:
                    return scanned_path
        
        return None
    
    def _analyze_graph(self):
        """Analyze dependency graph for orphans, hubs, cycles"""
        all_files = set(self.result.files.keys())
        imported_files = set()
        
        for deps in self.result.dependency_graph.values():
            imported_files.update(deps)
        
        # Orphans - files that nothing imports
        self.result.orphans = list(all_files - imported_files)
        
        # Hubs - files imported by many (top 10%)
        import_counts = [(f, len(importers)) for f, importers in self.result.reverse_graph.items()]
        import_counts.sort(key=lambda x: x[1], reverse=True)
        top_count = max(1, len(import_counts) // 10)
        self.result.hubs = [f for f, c in import_counts[:top_count] if c > 1]
        
        # Circular dependencies (simplified DFS)
        self._detect_cycles()
    
    def _detect_cycles(self):
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.result.dependency_graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        for node in self.result.files:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle and len(cycle) > 2:
                    self.result.circular_deps.append(cycle)
    
    def _save_results(self):
        """Save scan results to files"""
        scan_dir = self.output_dir / self.result.scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        
        # Summary JSON
        summary = {
            "scan_id": self.result.scan_id,
            "timestamp": self.result.timestamp,
            "paths_scanned": self.result.paths_scanned,
            "total_files": self.result.total_files,
            "total_size": self.result.total_size,
            "total_duplicates": len(self.result.duplicates),
            "total_orphans": len(self.result.orphans),
            "total_hubs": len(self.result.hubs),
            "total_broken_imports": len(self.result.broken_imports),
            "total_circular_deps": len(self.result.circular_deps),
            "total_errors": len(self.result.errors),
        }
        
        with open(scan_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Full files data
        files_data = {path: asdict(info) for path, info in self.result.files.items()}
        with open(scan_dir / "files.json", "w", encoding="utf-8") as f:
            json.dump(files_data, f, indent=2, ensure_ascii=False)
        
        # Duplicates
        with open(scan_dir / "duplicates.json", "w", encoding="utf-8") as f:
            json.dump(self.result.duplicates, f, indent=2, ensure_ascii=False)
        
        # Dependency graph
        with open(scan_dir / "dependencies.json", "w", encoding="utf-8") as f:
            json.dump({
                "forward": self.result.dependency_graph,
                "reverse": self.result.reverse_graph,
            }, f, indent=2, ensure_ascii=False)
        
        # Analysis
        with open(scan_dir / "analysis.json", "w", encoding="utf-8") as f:
            json.dump({
                "orphans": self.result.orphans,
                "hubs": self.result.hubs,
                "broken_imports": self.result.broken_imports,
                "circular_deps": self.result.circular_deps,
            }, f, indent=2, ensure_ascii=False)
        
        # Errors
        if self.result.errors:
            with open(scan_dir / "errors.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.result.errors))
        
        # Human-readable markdown report
        self._generate_markdown_report(scan_dir)
        
        print(f"[SCAN] Results saved to: {scan_dir}")
    
    def _generate_markdown_report(self, scan_dir: Path):
        """Generate human-readable markdown report"""
        r = self.result
        
        report = f"""# Project Scan Report

**Scan ID:** {r.scan_id}  
**Date:** {r.timestamp}  
**Paths Scanned:** {', '.join(r.paths_scanned)}

## Summary

| Metric | Value |
|--------|-------|
| Total Files | {r.total_files} |
| Total Size | {r.total_size / 1024 / 1024:.2f} MB |
| Duplicates | {len(r.duplicates)} groups |
| Orphan Files | {len(r.orphans)} |
| Hub Files | {len(r.hubs)} |
| Broken Imports | {len(r.broken_imports)} |
| Circular Dependencies | {len(r.circular_deps)} |
| Errors | {len(r.errors)} |

## Hub Files (Most Imported)

These files are imported by many others - likely core modules:

"""
        for hub in r.hubs[:20]:
            importers = len(r.reverse_graph.get(hub, []))
            report += f"- `{hub}` ({importers} importers)\n"
        
        report += f"""

## Duplicate Files

Found {len(r.duplicates)} groups of duplicate files:

"""
        for i, (hash_val, paths) in enumerate(list(r.duplicates.items())[:20]):
            report += f"### Duplicate Group {i+1}\n"
            for p in paths:
                info = r.files.get(p)
                mod = info.modified if info else "?"
                report += f"- `{p}` (modified: {mod})\n"
            report += "\n"
        
        report += f"""

## Broken Imports

These imports could not be resolved:

"""
        for file_path, imp in r.broken_imports[:50]:
            report += f"- `{file_path}` → `{imp}`\n"
        
        report += f"""

## Circular Dependencies

"""
        if r.circular_deps:
            for i, cycle in enumerate(r.circular_deps[:10]):
                report += f"### Cycle {i+1}\n"
                report += " → ".join([Path(p).name for p in cycle]) + "\n\n"
        else:
            report += "No circular dependencies detected.\n"
        
        report += f"""

## Orphan Files (Not Imported by Anything)

These {len(r.orphans)} files are not imported by anything else.
They might be entry points, standalone scripts, or dead code:

"""
        # Group orphans by category
        orphan_categories = defaultdict(list)
        for o in r.orphans:
            info = r.files.get(o)
            cats = info.categories if info else ['unknown']
            orphan_categories[cats[0] if cats else 'unknown'].append(o)
        
        for cat, files in orphan_categories.items():
            report += f"### {cat.title()} ({len(files)})\n"
            for f in files[:10]:
                report += f"- `{Path(f).name}`\n"
            if len(files) > 10:
                report += f"- ... and {len(files) - 10} more\n"
            report += "\n"
        
        with open(scan_dir / "REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Project Scanner")
    parser.add_argument("paths", nargs="+", help="Paths to scan")
    parser.add_argument("-o", "--output", default="scan_results", help="Output directory")
    parser.add_argument("--ext", nargs="*", help="Limit to specific extensions")
    
    args = parser.parse_args()
    
    scanner = ProjectScanner(output_dir=Path(args.output))
    extensions = set(args.ext) if args.ext else None
    
    result = scanner.scan(args.paths, extensions)
    
    print(f"\n{'='*50}")
    print(f"SCAN COMPLETE")
    print(f"{'='*50}")
    print(f"Files: {result.total_files}")
    print(f"Size: {result.total_size / 1024 / 1024:.2f} MB")
    print(f"Duplicates: {len(result.duplicates)} groups")
    print(f"Hubs: {len(result.hubs)}")
    print(f"Orphans: {len(result.orphans)}")
    print(f"Broken imports: {len(result.broken_imports)}")
    print(f"Circular deps: {len(result.circular_deps)}")
    print(f"\nResults saved to: {scanner.output_dir / result.scan_id}")


if __name__ == "__main__":
    main()

import json
import sys
import time
import ssl
import re
import hashlib
import urllib.parse as up
import urllib.request as ur
from html.parser import HTMLParser
from pathlib import Path
import os
from typing import List, Set, Dict

try:
    from korean_keys import build_keys
except Exception as exc:
    raise SystemExit(f"Missing korean_keys module: {exc}")


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_ign = False
        self.buf: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.in_ign = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.in_ign = False
        if tag in ("p", "br", "div", "li", "section", "article"):
            self.buf.append("\n")

    def handle_data(self, data):
        if not self.in_ign:
            self.buf.append(data)

    def text(self) -> str:
        raw = "".join(self.buf)
        raw = re.sub(r"\s+", " ", raw)
        return raw.strip()


SENT_SPLIT = re.compile(r"(?<=[\.!?])\s+")


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    parts = SENT_SPLIT.split(text)
    out = []
    for s in parts:
        s = s.strip()
        if 40 <= len(s) <= 280:
            out.append(s)
    return out


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def crawl(seeds: List[str], allow_domains: Set[str], max_pages: int, max_mb: int, out_root: Path) -> Dict[str, int]:
    out_facts = out_root / "facts.jsonl"
    out_index = out_root / "facts_index.json"
    inv: Dict[str, List[str]] = {}
    seen_sent: Set[str] = set()
    seen_url: Set[str] = set()
    added = 0

    # Load existing index to extend
    if out_index.exists():
        try:
            inv = json.loads(out_index.read_text(encoding="utf-8")).get("index", {})
        except Exception:
            inv = {}
    if out_facts.exists():
        for line in out_facts.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
                seen_sent.add(sha1(obj.get("text", "")))
            except Exception:
                pass

    ctx = ssl.create_default_context()
    q: List[str] = []
    for s in seeds:
        if s and s not in seen_url:
            q.append(s)
            seen_url.add(s)

    fetched = 0
    bytes_total = 0

    def allowed(url: str) -> bool:
        try:
            host = up.urlparse(url).hostname or ""
        except Exception:
            return False
        return any(host.endswith(d) for d in allow_domains)

    def normalize(url: str, base: str) -> str:
        try:
            r = up.urljoin(base, url)
            u = up.urlparse(r)
            if u.scheme in ("http", "https"):
                return up.urlunparse((u.scheme, u.netloc, u.path, "", "", ""))
        except Exception:
            return ""
        return r

    with out_facts.open("a", encoding="utf-8") as fh:
        while q and fetched < max_pages and bytes_total < max_mb * 1024 * 1024:
            url = q.pop(0)
            if not allowed(url):
                continue
            try:
                req = ur.Request(url, headers={"User-Agent": "AIONS-CRAWLER/1.0"})
                with ur.urlopen(req, context=ctx, timeout=10) as resp:
                    ctype = resp.headers.get("Content-Type", "")
                    if "text/html" not in ctype:
                        continue
                    data = resp.read()
                    bytes_total += len(data)
                    if bytes_total > max_mb * 1024 * 1024:
                        break
                    html = data.decode("utf-8", errors="ignore")
                    parser = TextExtractor()
                    parser.feed(html)
                    text = parser.text()
                    for sent in split_sentences(text):
                        sid = sha1(sent)
                        if sid in seen_sent:
                            continue
                        keys = list(build_keys(sent))
                        fid = ("W" + sha1(url + "|" + sent))[:13].upper()
                        rec = {"id": fid, "chunk_id": url, "text": sent, "keys": keys}
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        for k in keys:
                            inv.setdefault(k, []).append(fid)
                        seen_sent.add(sid)
                        added += 1

                    # Discover same-domain links
                    for href in re.findall(r"href=\"(.*?)\"", html):
                        nu = normalize(href, url)
                        if nu and allowed(nu) and nu not in seen_url and len(q) < max_pages * 4:
                            seen_url.add(nu)
                            q.append(nu)
                fetched += 1
                time.sleep(0.2)
            except Exception:
                continue

    out_index.write_text(json.dumps({"index": inv}, ensure_ascii=False), encoding="utf-8")
    return {"pages": fetched, "facts_added": added, "bytes": bytes_total}


def main(argv: List[str]):
    # Defaults: user should pass seeds & allow list explicitly
    seeds = []
    allow = []
    max_pages = 200
    max_mb = 50
    # Default output to repo-local memory unless overridden by env/arg
    out_root = Path(os.environ.get('CBMS_MEMORY_DIR', str(Path(__file__).resolve().parent.parent / 'memory')))

    # Simple arg parse
    for a in argv:
        if a.startswith("--seeds="):
            seeds = [s.strip() for s in a.split("=",1)[1].split(",") if s.strip()]
        elif a.startswith("--allow="):
            allow = [s.strip() for s in a.split("=",1)[1].split(",") if s.strip()]
        elif a.startswith("--max-pages="):
            max_pages = int(a.split("=",1)[1])
        elif a.startswith("--max-mb="):
            max_mb = int(a.split("=",1)[1])
        elif a.startswith("--out-root="):
            out_root = Path(a.split("=",1)[1])

    if not seeds or not allow:
        print("Usage: py web_crawler_import.py --seeds=https://example.com/docs,... --allow=example.com,example.org [--max-pages=200 --max-mb=50]")
        sys.exit(2)

    res = crawl(seeds, set(allow), max_pages, max_mb, out_root)
    print(json.dumps(res))


if __name__ == "__main__":
    main(sys.argv[1:])

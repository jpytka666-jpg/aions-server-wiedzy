import json
import time
import statistics as stats
from urllib import request
from pathlib import Path

API = "http://127.0.0.1:9000/api/chat"
# Write results under repo-local logs directory by default
_ROOT = Path(__file__).resolve().parent.parent
_LOGS = _ROOT / 'logs'
_LOGS.mkdir(parents=True, exist_ok=True)
OUT_JSONL = str(_LOGS / 'bench_latency.jsonl')
OUT_SUMMARY = str(_LOGS / 'bench_summary.json')

QUERIES = [
    "Opisz CRLA i dlaczego unika halucynacji",
    "Wyjaśnij Korean-CBMS segmentację kluczy",
    "STATUS SYSTEMU",
    "Ile masz teraz chunków?",
    "asdkj asd 129387 !@# nonsens",
]

ROUNDS = 50


def post_chat(q: str) -> tuple[float, int, str]:
    payload = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": q}],
    }).encode("utf-8")
    req = request.Request(API, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with request.urlopen(req, timeout=10) as resp:
            lat = (time.time() - t0) * 1000.0
            data = resp.read().decode("utf-8", errors="ignore")
            return lat, resp.getcode(), data
    except Exception as exc:
        lat = (time.time() - t0) * 1000.0
        return lat, 500, str(exc)


def is_refusal(text: str) -> bool:
    return "NIE WIEM" in text


def main():
    rows = []
    for q in QUERIES:
        for _ in range(ROUNDS):
            lat, code, data = post_chat(q)
            row = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "query": q,
                "latency_ms": round(lat, 2),
                "status": code,
                "refusal": is_refusal(data),
                "size": len(data),
            }
            rows.append(row)
            with open(OUT_JSONL, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # summary
    summary = {}
    for q in QUERIES:
        lats = [r["latency_ms"] for r in rows if r["query"] == q and r["status"] == 200]
        if lats:
            summary[q] = {
                "count": len(lats),
                "p50": round(float(stats.median(lats)), 2),
                "p95": round(float(stats.quantiles(lats, n=100)[94]), 2) if len(lats) > 1 else lats[0],
            }
        else:
            summary[q] = {"count": 0, "p50": None, "p95": None}

    with open(OUT_SUMMARY, "w", encoding="utf-8") as fh:
        json.dump({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rounds": ROUNDS,
            "summary": summary,
        }, fh, indent=2, ensure_ascii=False)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

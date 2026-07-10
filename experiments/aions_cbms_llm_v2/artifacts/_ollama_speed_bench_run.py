import json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://localhost:11434"
OUT = Path(r"E:\server wiedzy\experiments\aions_cbms_llm_v2\artifacts\ollama_speed_bench.json")
PROMPT = "Reply in one short sentence: What is 2+2?"
NUM_PREDICT = 64
MODEL_TIMEOUT_S = 600  # 10 min

def http_json(method, path, body=None, timeout=60):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def chat(model, content, num_predict, temperature=None, timeout=MODEL_TIMEOUT_S):
    opts = {"num_predict": num_predict}
    if temperature is not None:
        opts["temperature"] = temperature
    body = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "stream": False,
        "options": opts,
    }
    return http_json("POST", "/api/chat", body, timeout=timeout)

def metrics(r, wall_s):
    eval_count = float(r.get("eval_count") or 0)
    eval_dur = float(r.get("eval_duration") or 0)
    prompt_count = float(r.get("prompt_eval_count") or 0)
    prompt_dur = float(r.get("prompt_eval_duration") or 0)
    total_ns = float(r.get("total_duration") or 0)
    load_ns = float(r.get("load_duration") or 0)
    gen_tok_s = round(eval_count / (eval_dur / 1e9), 2) if eval_dur > 0 else None
    prompt_tok_s = round(prompt_count / (prompt_dur / 1e9), 2) if prompt_dur > 0 else None
    reply = (r.get("message") or {}).get("content") or ""
    return {
        "ok": True,
        "wall_s": round(wall_s, 2),
        "total_s": round(total_ns / 1e9, 2) if total_ns else None,
        "eval_tokens": int(eval_count) if eval_count else 0,
        "gen_tok_s": gen_tok_s,
        "prompt_tokens": int(prompt_count) if prompt_count else 0,
        "prompt_tok_s": prompt_tok_s,
        "load_s": round(load_ns / 1e9, 2) if load_ns else None,
        "reply": reply[:120],
    }

tags = http_json("GET", "/api/tags", timeout=30)
models = [m["name"].replace(":latest", "") if m["name"].endswith(":latest") else m["name"] for m in tags.get("models", [])]
models = sorted(set(models))
print(f"MODELS: {models}", flush=True)

results = []
for m in models:
    print(f"=== WARMUP {m} ===", flush=True)
    warm_ok = False
    warm_err = None
    t0 = time.perf_counter()
    try:
        chat(m, "Hi", num_predict=8, timeout=MODEL_TIMEOUT_S)
        warm_ok = True
        print(f"WARMUP OK {m} wall={time.perf_counter()-t0:.1f}s", flush=True)
    except Exception as e:
        warm_err = str(e)
        print(f"WARMUP FAIL {m} wall={time.perf_counter()-t0:.1f}s : {warm_err}", flush=True)

    print(f"=== BENCH {m} ===", flush=True)
    sw = time.perf_counter()
    try:
        r = chat(m, PROMPT, num_predict=NUM_PREDICT, temperature=0, timeout=MODEL_TIMEOUT_S)
        wall = time.perf_counter() - sw
        row = {"model": m, "warmup_ok": warm_ok, "warmup_error": warm_err, **metrics(r, wall)}
        print(json.dumps(row, ensure_ascii=False), flush=True)
    except Exception as e:
        wall = time.perf_counter() - sw
        status = "FAIL"
        err = str(e)
        if wall >= MODEL_TIMEOUT_S - 5 or "timed out" in err.lower() or "timeout" in err.lower():
            status = "FAIL_TIMEOUT"
        row = {
            "model": m,
            "ok": False,
            "status": status,
            "warmup_ok": warm_ok,
            "warmup_error": warm_err,
            "wall_s": round(wall, 2),
            "error": err,
        }
        print(json.dumps(row, ensure_ascii=False), flush=True)
    results.append(row)

report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "prompt": PROMPT,
    "num_predict": NUM_PREDICT,
    "temperature": 0,
    "model_timeout_s": MODEL_TIMEOUT_S,
    "gpu_note": "Quadro M2000M 4GB VRAM",
    "note": "killed prior hung PS bench; sequential warmup+timed chat; read-only weights",
    "results": results,
}
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"WROTE {OUT}", flush=True)
oks = [r for r in results if r.get("ok")]
print("SUMMARY:", flush=True)
for r in results:
    if r.get("ok"):
        print(f"  PASS {r['model']}: gen_tok_s={r.get('gen_tok_s')} prompt_tok_s={r.get('prompt_tok_s')} wall_s={r.get('wall_s')} load_s={r.get('load_s')}", flush=True)
    else:
        print(f"  FAIL {r['model']}: wall_s={r.get('wall_s')} err={r.get('error','')[:120]}", flush=True)
print("BENCH_PASS" if oks else "BENCH_FAIL", flush=True)

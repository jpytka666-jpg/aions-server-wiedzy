"""Skill text.find_in_file — find lines containing a substring."""


def run(inputs, ctx):
    needle = inputs["text"].lower()
    top = int(inputs.get("top", 20))
    try:
        hits = []
        with open(inputs["path"], encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if needle in line.lower():
                    hits.append({"line": i, "text": line.strip()[:120]})
        return {"ok": True, "hits": hits[:top], "count": len(hits)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

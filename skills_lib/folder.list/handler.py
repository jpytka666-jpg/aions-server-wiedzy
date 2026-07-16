"""Skill folder.list — list a directory's contents."""
import os


def run(inputs, ctx):
    try:
        items = os.listdir(inputs["path"])
        top = int(inputs.get("top", 50))
        return {"ok": True, "items": items[:top], "count": len(items)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

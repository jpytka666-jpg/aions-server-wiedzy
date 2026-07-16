"""Skill file.write_text — write text to a file on disk."""
import os


def run(inputs, ctx):
    path = inputs["path"]
    text = inputs.get("text", "")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        mode = "a" if inputs.get("append") else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(text)
        return {"ok": True, "path": path, "bytes": len(text.encode("utf-8"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

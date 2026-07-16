"""Skill folder.create — create a directory."""
import os


def run(inputs, ctx):
    try:
        os.makedirs(inputs["path"], exist_ok=True)
        return {"ok": True, "path": inputs["path"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

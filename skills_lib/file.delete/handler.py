"""Skill file.delete — delete a file (high risk: irreversible)."""
import os


def run(inputs, ctx):
    try:
        os.remove(inputs["path"])
        return {"ok": True, "deleted": inputs["path"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

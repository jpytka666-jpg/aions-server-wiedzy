"""Skill file.copy — copy a file."""
import shutil


def run(inputs, ctx):
    try:
        shutil.copy2(inputs["src"], inputs["dst"])
        return {"ok": True, "dst": inputs["dst"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

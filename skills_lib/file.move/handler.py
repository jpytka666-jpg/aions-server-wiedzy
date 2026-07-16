"""Skill file.move — move or rename a file."""
import shutil


def run(inputs, ctx):
    try:
        shutil.move(inputs["src"], inputs["dst"])
        return {"ok": True, "dst": inputs["dst"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill folder.unzip — extract a .zip archive."""
import shutil


def run(inputs, ctx):
    try:
        shutil.unpack_archive(inputs["zip"], inputs["dest"])
        return {"ok": True, "dest": inputs["dest"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

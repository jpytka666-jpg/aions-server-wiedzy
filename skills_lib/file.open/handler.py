"""Skill file.open — open a file with its default Windows app."""
import os


def run(inputs, ctx):
    try:
        os.startfile(inputs["path"])
        if str(inputs["path"]).lower().endswith(".txt"):
            ctx["state_set"]("notepad", "open")
        return {"opened": True, "path": inputs["path"]}
    except Exception as e:
        return {"opened": False, "error": str(e)}

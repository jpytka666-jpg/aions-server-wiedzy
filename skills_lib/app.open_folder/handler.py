"""Skill app.open_folder — open a folder in Windows Explorer."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.Popen(["explorer.exe", inputs["path"]])
        return {"ok": True, "path": inputs["path"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

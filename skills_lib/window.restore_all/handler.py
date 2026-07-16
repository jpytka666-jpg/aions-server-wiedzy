"""Skill window.restore_all — undo minimize-all."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object -ComObject Shell.Application).UndoMinimizeALL()"], timeout=8)
        return {"ok": True, "action": "restore_all"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

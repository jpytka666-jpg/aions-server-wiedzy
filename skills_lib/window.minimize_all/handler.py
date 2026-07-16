"""Skill window.minimize_all — minimize all windows (show desktop)."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object -ComObject Shell.Application).MinimizeAll()"], timeout=8)
        return {"ok": True, "action": "minimize_all"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill clip.get_text — read the Windows clipboard text."""
import subprocess


def run(inputs, ctx):
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                             capture_output=True, text=True, timeout=10)
        return {"ok": True, "text": out.stdout.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill clip.set_text — copy text into the Windows clipboard."""
import subprocess


def run(inputs, ctx):
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                           input=inputs["text"], text=True, timeout=10)
        return {"ok": p.returncode == 0}
    except Exception as e:
        return {"ok": False, "error": str(e)}

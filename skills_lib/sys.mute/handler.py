"""Skill sys.mute — toggle system mute via media key."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], timeout=8)
        return {"ok": True, "action": "mute_toggle"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

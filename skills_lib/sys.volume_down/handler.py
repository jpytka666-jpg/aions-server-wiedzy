"""Skill sys.volume_down — lower system volume via media key."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"], timeout=8)
        return {"ok": True, "action": "volume_down"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

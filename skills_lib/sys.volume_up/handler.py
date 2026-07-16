"""Skill sys.volume_up — raise system volume via media key."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], timeout=8)
        return {"ok": True, "action": "volume_up"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill sys.uptime — time since last boot."""
import subprocess


def run(inputs, ctx):
    ps = "$o=Get-CimInstance Win32_OperatingSystem; ((Get-Date)-$o.LastBootUpTime).ToString('dd\\.hh\\:mm\\:ss')"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10)
        return {"ok": True, "uptime": out.stdout.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

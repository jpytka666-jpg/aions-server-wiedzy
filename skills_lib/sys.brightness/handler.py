"""Skill sys.brightness — set screen brightness (laptops)."""
import subprocess


def run(inputs, ctx):
    lvl = int(inputs.get("level", 70))
    ps = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{lvl})"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10)
        ok = out.returncode == 0 and "Exception" not in (out.stderr or "")
        return {"ok": ok, "level": lvl, "note": (out.stderr.strip()[:120] or None)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill sys.battery — battery charge percent (laptops)."""
import subprocess


def run(inputs, ctx):
    ps = "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10)
        v = out.stdout.strip()
        if not v:
            return {"ok": True, "battery_pct": None, "note": "brak baterii (komputer stacjonarny)"}
        return {"ok": True, "battery_pct": int(v.splitlines()[0])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

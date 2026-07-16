"""Skill sys.resources — free/total RAM in GB."""
import subprocess


def run(inputs, ctx):
    ps = ("$o=Get-CimInstance Win32_OperatingSystem; "
          "'{0};{1}' -f $o.FreePhysicalMemory,$o.TotalVisibleMemorySize")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10)
        free_kb, total_kb = out.stdout.strip().split(";")
        return {"ok": True, "ram_free_gb": round(int(free_kb) / 1048576, 1),
                "ram_total_gb": round(int(total_kb) / 1048576, 1)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

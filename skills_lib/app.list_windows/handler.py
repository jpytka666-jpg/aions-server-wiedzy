"""Skill app.list_windows — titles of open windows."""
import subprocess


def run(inputs, ctx):
    ps = "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -ExpandProperty MainWindowTitle"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10)
        titles = [t.strip() for t in out.stdout.strip().splitlines() if t.strip()]
        return {"ok": True, "windows": titles, "count": len(titles)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

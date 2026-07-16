"""Skill app.focus — bring a window to front by (partial) title."""
import subprocess


def run(inputs, ctx):
    title = inputs["title"]
    ps = f"$r=(New-Object -ComObject WScript.Shell).AppActivate('{title}'); $r"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=8)
        return {"ok": "True" in out.stdout, "title": title}
    except Exception as e:
        return {"ok": False, "error": str(e)}

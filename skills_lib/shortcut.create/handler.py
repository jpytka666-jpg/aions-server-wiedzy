"""Skill shortcut.create — create a .lnk shortcut."""
import subprocess


def run(inputs, ctx):
    target = inputs["target"]
    link = inputs["link"]
    ps = (f"$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut('{link}'); "
          f"$s.TargetPath='{target}'; $s.Save()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=10)
        return {"ok": True, "link": link}
    except Exception as e:
        return {"ok": False, "error": str(e)}

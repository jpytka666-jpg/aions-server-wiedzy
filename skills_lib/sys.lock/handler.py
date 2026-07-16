"""Skill sys.lock — lock the workstation."""
import subprocess


def run(inputs, ctx):
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return {"ok": True, "locked": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill app.launch — launch any Windows app by name/path."""
import subprocess


def run(inputs, ctx):
    try:
        p = subprocess.Popen([inputs["name"]], creationflags=0x00000008, close_fds=True)
        return {"launched": True, "pid": p.pid, "app": inputs["name"]}
    except Exception as e:
        return {"launched": False, "error": str(e)}

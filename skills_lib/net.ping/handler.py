"""Skill net.ping — check if a host responds."""
import subprocess


def run(inputs, ctx):
    host = inputs["host"]
    try:
        out = subprocess.run(["ping", "-n", "2", host], capture_output=True, text=True, timeout=15)
        return {"ok": True, "reachable": out.returncode == 0, "host": host}
    except Exception as e:
        return {"ok": False, "error": str(e)}

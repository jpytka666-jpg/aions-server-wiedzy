"""Skill proc.kill — force-terminate a process by image name."""
import subprocess


def run(inputs, ctx):
    img = inputs["image"]
    try:
        out = subprocess.run(["taskkill", "/IM", img, "/F"],
                             capture_output=True, text=True, timeout=10)
        return {"ok": out.returncode == 0, "detail": (out.stdout or out.stderr).strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

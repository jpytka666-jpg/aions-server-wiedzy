"""Skill app.close — close a Windows app by image name."""
import subprocess


def run(inputs, ctx):
    img = inputs["image"]
    try:
        out = subprocess.run(["taskkill", "/IM", img, "/F"],
                             capture_output=True, text=True, timeout=10)
        ok = out.returncode == 0
        if ok and "notepad" in img.lower():
            ctx["state_set"]("notepad", "closed")
        return {"closed": ok, "detail": (out.stdout or out.stderr).strip()}
    except Exception as e:
        return {"closed": False, "error": str(e)}

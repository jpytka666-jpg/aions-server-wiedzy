"""Skill sys.open_settings — open Windows Settings (optionally a page)."""
import subprocess


def run(inputs, ctx):
    uri = "ms-settings:" + inputs.get("page", "")
    try:
        subprocess.Popen(["cmd", "/c", "start", "", uri], creationflags=0x00000008)
        return {"ok": True, "opened": uri}
    except Exception as e:
        return {"ok": False, "error": str(e)}

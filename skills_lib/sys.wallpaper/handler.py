"""Skill sys.wallpaper — set the desktop wallpaper."""
import subprocess


def run(inputs, ctx):
    img = inputs["path"]
    try:
        subprocess.run(["reg", "add", "HKCU\\Control Panel\\Desktop", "/v", "Wallpaper",
                        "/t", "REG_SZ", "/d", img, "/f"], capture_output=True, timeout=10)
        subprocess.run(["RUNDLL32.EXE", "user32.dll,UpdatePerUserSystemParameters", "1", "True"], timeout=10)
        return {"ok": True, "wallpaper": img}
    except Exception as e:
        return {"ok": False, "error": str(e)}

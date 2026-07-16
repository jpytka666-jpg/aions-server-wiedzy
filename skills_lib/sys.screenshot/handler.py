"""Skill sys.screenshot — capture the full screen to a PNG via PowerShell/.NET."""
import os
import subprocess


def run(inputs, ctx):
    path = inputs.get("path") or r"E:\AI_WORKSPACE\AIONS_workspace\aions_screenshot.png"
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b=[System.Windows.Forms.SystemInformation]::VirtualScreen; "
        "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height; "
        "$g=[System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); "
        f"$bmp.Save('{path}'); $g.Dispose(); $bmp.Dispose()"
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=25)
        ok = os.path.exists(path)
        return {"ok": ok, "path": path if ok else None, "error": (r.stderr.strip()[:200] or None)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

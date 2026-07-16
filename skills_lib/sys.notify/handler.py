"""Skill sys.notify — show a balloon notification (auto-dismisses)."""
import subprocess


def run(inputs, ctx):
    title = str(inputs.get("title", "AIONS")).replace("'", "")
    msg = str(inputs.get("message", "")).replace("'", "")
    ps = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
          "$n=New-Object System.Windows.Forms.NotifyIcon; "
          "$n.Icon=[System.Drawing.SystemIcons]::Information; $n.Visible=$true; "
          f"$n.ShowBalloonTip(4000,'{title}','{msg}',[System.Windows.Forms.ToolTipIcon]::Info); "
          "Start-Sleep -Seconds 4; $n.Dispose()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=10)
        return {"ok": True, "title": title, "message": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill net.wifi_list — list visible WiFi networks."""
import subprocess


def run(inputs, ctx):
    try:
        out = subprocess.run(["netsh", "wlan", "show", "networks"],
                             capture_output=True, text=True, timeout=12)
        ssids = []
        for ln in out.stdout.splitlines():
            s = ln.strip()
            if s.startswith("SSID") and ":" in s:
                val = s.split(":", 1)[1].strip()
                if val:
                    ssids.append(val)
        return {"ok": True, "networks": ssids, "count": len(ssids)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

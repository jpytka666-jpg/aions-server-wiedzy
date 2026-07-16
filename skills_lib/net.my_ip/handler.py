"""Skill net.my_ip — local IP address and hostname."""
import socket


def run(inputs, ctx):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return {"ok": True, "ip": ip, "host": socket.gethostname()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

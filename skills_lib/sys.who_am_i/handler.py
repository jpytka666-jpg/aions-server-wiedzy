"""Skill sys.who_am_i — current user, host, home folder."""
import os
import socket


def run(inputs, ctx):
    return {"ok": True,
            "user": os.environ.get("USERNAME"),
            "host": socket.gethostname(),
            "home": os.environ.get("USERPROFILE")}

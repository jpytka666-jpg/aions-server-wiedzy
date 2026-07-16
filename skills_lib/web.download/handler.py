"""Skill web.download — download a file from a URL."""
import os
import urllib.request


def run(inputs, ctx):
    try:
        path = inputs["path"]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        urllib.request.urlretrieve(inputs["url"], path)
        return {"ok": True, "path": path, "bytes": os.path.getsize(path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

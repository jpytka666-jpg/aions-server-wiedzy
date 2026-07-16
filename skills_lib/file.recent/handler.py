"""Skill file.recent — most recently modified files in a folder."""
import os


def run(inputs, ctx):
    folder = inputs["folder"]
    top = int(inputs.get("top", 10))
    try:
        files = []
        for name in os.listdir(folder):
            p = os.path.join(folder, name)
            if os.path.isfile(p):
                files.append((os.path.getmtime(p), name))
        files.sort(reverse=True)
        return {"ok": True, "recent": [n for _, n in files[:top]], "count": len(files)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

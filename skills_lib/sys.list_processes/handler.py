"""Skill sys.list_processes — list running process image names."""
import subprocess


def run(inputs, ctx):
    top = int(inputs.get("top", 12))
    try:
        out = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                             capture_output=True, text=True, timeout=10)
        names = []
        for row in out.stdout.strip().splitlines():
            if row.startswith('"'):
                names.append(row.split('","')[0].strip('"'))
        return {"processes": names[:top], "count": len(names)}
    except Exception as e:
        return {"error": str(e)}

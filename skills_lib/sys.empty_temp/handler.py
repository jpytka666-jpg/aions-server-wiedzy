"""Skill sys.empty_temp — delete user TEMP files to free disk space (in-use skipped)."""
import glob
import os
import shutil


def run(inputs, ctx):
    tmp = os.environ.get("TEMP") or r"C:\Windows\Temp"
    freed = 0
    removed = 0
    for item in glob.glob(os.path.join(tmp, "*")):
        try:
            if os.path.isfile(item):
                sz = os.path.getsize(item)
                os.remove(item)
                freed += sz
                removed += 1
            elif os.path.isdir(item):
                sz = 0
                for dp, _, files in os.walk(item):
                    for f in files:
                        try:
                            sz += os.path.getsize(os.path.join(dp, f))
                        except Exception:
                            pass
                shutil.rmtree(item, ignore_errors=True)
                freed += sz
                removed += 1
        except Exception:
            pass
    return {"ok": True, "removed": removed, "freed_mb": round(freed / 1e6, 1), "temp": tmp}

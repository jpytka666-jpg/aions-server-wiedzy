"""Skill sys.free_space — free disk space in GB."""
import shutil


def run(inputs, ctx):
    drive = inputs.get("drive", "E:\\")
    try:
        u = shutil.disk_usage(drive)
        return {"free_gb": round(u.free / 1e9, 1), "total_gb": round(u.total / 1e9, 1), "drive": drive}
    except Exception as e:
        return {"error": str(e)}

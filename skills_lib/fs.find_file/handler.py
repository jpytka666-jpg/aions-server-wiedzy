"""Skill fs.find_file — locate files on disk via the AIONS context helper."""


def run(inputs, ctx):
    res = ctx["find_files"](
        inputs["query"],
        inputs.get("folder", ""),
        inputs.get("max_results", 50),
    )
    files = res.get("files", [])
    return {"files": files, "count": len(files), "first": files[0] if files else None}

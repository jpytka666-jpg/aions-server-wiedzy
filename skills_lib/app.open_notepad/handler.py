"""Skill app.open_notepad — launches Windows Notepad and marks world state."""


def run(inputs, ctx):
    res = ctx["launch_app"]("notepad.exe")
    if res.get("ok"):
        ctx["state_set"]("notepad", "open")
    return {"launched": bool(res.get("ok")), "pid": res.get("pid"), "error": res.get("error")}

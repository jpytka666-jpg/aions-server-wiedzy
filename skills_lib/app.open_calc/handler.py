"""Skill app.open_calc — launches Windows Calculator and marks world state."""


def run(inputs, ctx):
    res = ctx["launch_app"]("calc.exe")
    if res.get("ok"):
        ctx["state_set"]("calc", "open")
    return {"launched": bool(res.get("ok")), "error": res.get("error")}

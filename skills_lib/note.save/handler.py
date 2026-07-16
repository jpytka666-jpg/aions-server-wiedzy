"""Skill note.save — persist a short note/conclusion via the AIONS context helper."""


def run(inputs, ctx):
    res = ctx["save_note"](inputs["text"], inputs.get("session", "skill_engine"))
    return {"saved": bool(res.get("ok")), "note_id": res.get("note_id")}

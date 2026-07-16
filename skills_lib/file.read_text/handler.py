"""Skill file.read_text — read a text file's content."""


def run(inputs, ctx):
    try:
        with open(inputs["path"], encoding="utf-8", errors="replace") as f:
            return {"ok": True, "text": f.read()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill file.word_count — count chars/words/lines in a text file."""


def run(inputs, ctx):
    try:
        with open(inputs["path"], encoding="utf-8", errors="replace") as f:
            t = f.read()
        return {"ok": True, "chars": len(t), "words": len(t.split()), "lines": t.count("\n") + 1}
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""Skill input.type_text — type text into the active window via SendKeys."""
import subprocess


def _escape(t):
    for a, b in [("'", "''"), ("{", "{{"), ("}", "}}"), ("+", "{+}"), ("^", "{^}"),
                 ("%", "{%}"), ("~", "{~}"), ("(", "{(}"), (")", "{)}"), ("[", "{[}"), ("]", "{]}")]:
        t = t.replace(a, b)
    return t


def run(inputs, ctx):
    try:
        text = _escape(inputs["text"])
        ps = f"(New-Object -ComObject WScript.Shell).SendKeys('{text}')"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=10)
        return {"ok": r.returncode == 0, "typed": inputs["text"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

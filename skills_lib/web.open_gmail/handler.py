"""Skill web.open_gmail — open Gmail in the browser."""
import webbrowser


def run(inputs, ctx):
    try:
        webbrowser.open("https://mail.google.com")
        ctx["state_set"]("browser", "open")
        return {"opened": True}
    except Exception as e:
        return {"opened": False, "error": str(e)}

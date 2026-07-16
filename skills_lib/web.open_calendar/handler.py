"""Skill web.open_calendar — open Google Calendar."""
import webbrowser


def run(inputs, ctx):
    try:
        webbrowser.open("https://calendar.google.com")
        ctx["state_set"]("browser", "open")
        return {"opened": True}
    except Exception as e:
        return {"opened": False, "error": str(e)}

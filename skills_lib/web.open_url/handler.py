"""Skill web.open_url — open a URL in the default browser."""
import webbrowser


def run(inputs, ctx):
    try:
        webbrowser.open(inputs["url"])
        ctx["state_set"]("browser", "open")
        return {"opened": True, "url": inputs["url"]}
    except Exception as e:
        return {"opened": False, "error": str(e)}

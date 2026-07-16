"""Skill web.open_maps — open Google Maps (optionally a place)."""
import urllib.parse
import webbrowser


def run(inputs, ctx):
    try:
        q = inputs.get("query", "")
        url = "https://www.google.com/maps"
        if q:
            url += "/search/" + urllib.parse.quote(q)
        webbrowser.open(url)
        ctx["state_set"]("browser", "open")
        return {"opened": True, "query": q or None}
    except Exception as e:
        return {"opened": False, "error": str(e)}

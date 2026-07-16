"""Skill web.search — open a Google search for a query."""
import urllib.parse
import webbrowser


def run(inputs, ctx):
    try:
        url = "https://www.google.com/search?q=" + urllib.parse.quote(inputs["query"])
        webbrowser.open(url)
        ctx["state_set"]("browser", "open")
        return {"opened": True, "query": inputs["query"]}
    except Exception as e:
        return {"opened": False, "error": str(e)}

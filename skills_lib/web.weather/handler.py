"""Skill web.weather — current weather via free wttr.in (no key, no infra)."""
import re
import urllib.parse
import urllib.request


def _city(inputs):
    q = (inputs.get("city") or inputs.get("query") or "").strip()
    m = re.search(r"\bw(?:e)?\s+([A-Za-zÀ-ż\-\s]{2,})$", q, re.IGNORECASE)
    city = (m.group(1).strip() if m else q).strip()
    # jeśli to całe zdanie bez 'w miasto', spróbuj ostatniego słowa
    if not city or " " in city and not m:
        city = q.split()[-1] if q.split() else "Leeds"
    return city or "Leeds"


def run(inputs, ctx):
    city = _city(inputs)
    url = "https://wttr.in/" + urllib.parse.quote(city) + "?format=3&m"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
        txt = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "replace").strip()
        return {"ok": True, "weather": txt, "city": city}
    except Exception as e:
        return {"ok": False, "error": str(e), "city": city}

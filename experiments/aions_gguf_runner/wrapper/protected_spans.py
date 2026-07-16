"""Protected spans: <addr>…</addr> and <<CB:*>> must not be mutated."""

from __future__ import annotations

import re
from typing import Any

ADDR_RE = re.compile(r"<addr>[\s\S]*?</addr>")
CB_RE = re.compile(r"<<CB:[A-Za-z0-9_-]+>>")


def find_addrs(text: str) -> list[str]:
    return ADDR_RE.findall(text or "")


def find_cbs(text: str) -> list[str]:
    return CB_RE.findall(text or "")


def extract(text: str) -> dict[str, list[str]]:
    return {"addrs": find_addrs(text), "cbs": find_cbs(text)}


def spans_ok(context: str, reply: str) -> dict[str, Any]:
    ctx = extract(context)
    ok_addr = all(a in (reply or "") for a in ctx["addrs"]) if ctx["addrs"] else True
    ok_cb = all(c in (reply or "") for c in ctx["cbs"]) if ctx["cbs"] else True
    banned = ("안녕하세요", "감사합니다", "입니다.")
    no_kr_nlg = not any(b in (reply or "") for b in banned)
    return {
        "ok": ok_addr and ok_cb and no_kr_nlg,
        "ok_addr": ok_addr,
        "ok_cb": ok_cb,
        "no_kr_nlg": no_kr_nlg,
        "ctx_addrs": ctx["addrs"],
        "ctx_cbs": ctx["cbs"],
    }


def ensure_preserved(context: str, reply: str) -> tuple[str, dict[str, Any]]:
    """If model dropped/mutated protected spans, append originals (wrapper post-process)."""
    check = spans_ok(context, reply)
    out = (reply or "").strip()
    if check["ok"]:
        return out, {**check, "restored": False}

    missing_addrs = [a for a in check["ctx_addrs"] if a not in out]
    missing_cbs = [c for c in check["ctx_cbs"] if c not in out]

    extras: list[str] = []
    if missing_addrs:
        extras.append("Adresy (opaque): " + " ".join(missing_addrs))
    if missing_cbs:
        extras.append("Codebook: " + " ".join(missing_cbs))
    if extras:
        out = (out + " " + " ".join(extras)).strip()

    final = spans_ok(context, out)
    return out, {**final, "restored": True, "missing_before": missing_addrs + missing_cbs}

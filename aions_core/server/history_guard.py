#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "AIONS_CATALOG" / "architecture_history.json"

def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", " ", (value or "").casefold()).strip()

def load_ledger() -> dict[str, Any]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))

def _hay(item: dict[str, Any]) -> list[str]:
    vals=[item.get("id",""),item.get("name",""),item.get("title",""),item.get("statement","")]
    vals.extend(item.get("aliases") or [])
    return [_norm(str(v)) for v in vals if v]

def lookup(text: str) -> list[dict[str, Any]]:
    q=_norm(text)
    if not q: return []
    qt=set(q.split())
    out=[]
    data=load_ledger()
    for section in ("mechanisms","defects","decisions"):
        for item in data.get(section,[]):
            best=0
            for h in _hay(item):
                if not h: continue
                if q == h: best=max(best,100)
                elif q in h or h in q: best=max(best,80)
                else:
                    ht=set(h.split())
                    if qt and ht:
                        overlap=len(qt & ht)
                        if overlap:
                            best=max(best,int(60*overlap/max(len(qt),1)))
            if best >= 25:
                row=dict(item); row["section"]=section; row["match_score"]=best
                out.append(row)
    return sorted(out,key=lambda x:(-x["match_score"],x.get("id","")))

def classify(text: str) -> dict[str, Any]:
    hits=lookup(text)
    if hits:
        top=hits[0]
        return {"history_status":"KNOWN","id":top.get("id"),"section":top.get("section"),
                "status":top.get("status"),"known_since":top.get("known_since") or top.get("first_known"),
                "evidence":top.get("evidence",[]),"match_score":top.get("match_score")}
    return {"history_status":"UNKNOWN_NOT_PROVEN_NEW","evidence":[]}

def validate() -> list[str]:
    errors=[]
    data=load_ledger()
    for section in ("mechanisms","defects","decisions"):
        ids=set()
        for item in data.get(section,[]):
            iid=item.get("id")
            if not iid: errors.append(f"{section}: missing id"); continue
            if iid in ids: errors.append(f"{section}: duplicate id {iid}")
            ids.add(iid)
            ev=item.get("evidence") or []
            if not ev: errors.append(f"{iid}: no evidence")
            for rel in ev:
                if rel.startswith("commit "): continue
                if not (ROOT/rel).exists():
                    errors.append(f"{iid}: missing evidence path: {rel}")
    return errors

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"server"))
from history_guard import classify, load_ledger, validate

def main():
    ap=argparse.ArgumentParser(description="AIONS historical preflight: KNOWN BEFORE NEW")
    ap.add_argument("text",nargs="*")
    ap.add_argument("--boot",action="store_true")
    ap.add_argument("--claim-new",action="store_true")
    ap.add_argument("--validate",action="store_true")
    a=ap.parse_args()
    if a.validate:
        errs=validate()
        print(json.dumps({"ok":not errs,"errors":errs},ensure_ascii=False,indent=2))
        return 0 if not errs else 20
    if a.boot:
        d=load_ledger()
        print(json.dumps({
            "rule":d["rule"],
            "mechanisms":[{"id":x["id"],"status":x.get("status")} for x in d["mechanisms"]],
            "active_or_historical_defects":[{"id":x["id"],"status":x.get("status"),"known_since":x.get("known_since")} for x in d["defects"]]
        },ensure_ascii=False,indent=2))
        return 0
    text=" ".join(a.text).strip()
    if not text:
        ap.error("give text, --boot, or --validate")
    r=classify(text)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    if a.claim_new:
        if r["history_status"]=="KNOWN":
            print("BLOCKED: this is already known; do not label it NEW.",file=sys.stderr)
            return 12
        print("BLOCKED: ledger miss is UNKNOWN_NOT_PROVEN_NEW. Search history and add evidence before novelty claim.",file=sys.stderr)
        return 13
    return 10 if r["history_status"]=="KNOWN" else 0
if __name__=="__main__":
    raise SystemExit(main())

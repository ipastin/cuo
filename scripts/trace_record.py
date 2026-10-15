#!/usr/bin/env python3
"""Append a strictly allowlisted, minimal, non-content execution trace (opt-in).

No prompts, retrieved content, tool responses, credentials, token data or telemetry.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import sys

FIELDS={"run_id","task_id","mode","agent","model","skills_selected","skills_reported","verification_status","attempt"}
ID=re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,79}$")


def minimal(p):
    if not isinstance(p,dict):raise ValueError("trace payload must be object")
    for k in ("run_id","task_id"):
        if not isinstance(p.get(k),str) or not ID.fullmatch(p[k]):raise ValueError(f"invalid {k}")
    if p.get("mode") not in ("direct","planned","orchestrated"):raise ValueError("invalid mode")
    if p.get("verification_status") not in ("accepted","needs_review","blocked","not_run"):
        raise ValueError("invalid verification_status")
    if type(p.get("attempt")) is not int or not 1 <= p["attempt"] <= 100:
        raise ValueError("attempt must be 1..100")
    for k in ("agent","model"):
        if p.get(k) is not None and (not isinstance(p[k],str) or not ID.fullmatch(p[k])):
            raise ValueError(f"invalid {k}")
    for k in ("skills_selected","skills_reported"):
        if not isinstance(p.get(k),list):raise ValueError(f"{k} must be list")
        if len(p[k])>64 or any(not isinstance(n,str) or not ID.fullmatch(n) for n in p[k]):
            raise ValueError(f"invalid {k} identifiers")
    d={k:p.get(k) for k in sorted(FIELDS)}
    d["timestamp_utc"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    return d


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace_event",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--apply",action="store_true",help="Append event; default dry run")
    ns=ap.parse_args()
    try:
        item=minimal(json.loads(ns.trace_event.read_text(encoding="utf-8")))
        if ns.out.is_symlink():raise ValueError("symlink output refused")
        if ns.out.exists() and not ns.out.is_file():raise ValueError("output must be regular file")
        print(json.dumps(item,ensure_ascii=False))
        if ns.apply:
            ns.out.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(ns.out,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
            with os.fdopen(fd,"a",encoding="utf-8") as f:f.write(json.dumps(item,ensure_ascii=False)+"\n")
    except (OSError,ValueError,json.JSONDecodeError) as ex:
        print(f"TRACE ERROR: {ex}",file=sys.stderr);return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a structured verification report, NOT the semantic correctness of claims.

Passing a JSON report does not establish that an artifact genuinely solves the task.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def validate(p):
    if not isinstance(p,dict) or p.get("schema_version")!="1.0":raise ValueError("schema_version must be 1.0")
    if not isinstance(p.get("task_id"),str) or not p["task_id"].strip():raise ValueError("task_id required")
    state=p.get("status")
    if state not in ("accepted","needs_review","blocked"):raise ValueError("invalid status")
    for fld in ("artifacts","criteria","checks","skills_used","open_issues"):
        if not isinstance(p.get(fld),list):raise ValueError(f"{fld} must be a list")
    if not p["criteria"]:raise ValueError("at least one acceptance criterion required")
    if state=="accepted" and not p["artifacts"]:raise ValueError("accepted status requires artifact references")
    for i,a in enumerate(p["artifacts"]):
        if not isinstance(a,str) or not a.strip():raise ValueError(f"artifacts[{i}] invalid")
    for i,c in enumerate(p["criteria"]):
        if not isinstance(c,dict) or c.get("status") not in ("pass","fail","pending"):
            raise ValueError(f"criterion[{i}] invalid status")
        if not isinstance(c.get("name"),str) or not c["name"].strip():
            raise ValueError(f"criterion[{i}] requires name")
        evidence=c.get("evidence")
        if not isinstance(evidence,list):raise ValueError(f"criterion[{i}] evidence must be list")
        if c["status"]=="pass" and not evidence:raise ValueError(f"criterion[{i}] pass without evidence")
        if state=="accepted" and c["status"]!="pass":
            raise ValueError("accepted requires all criteria passed")
    for i,c in enumerate(p["checks"]):
        if not isinstance(c,dict) or c.get("status") not in ("pass","fail","not_run"):
            raise ValueError(f"check[{i}] must have status pass/fail/not_run")
        if not isinstance(c.get("name"),str) or not c["name"].strip():raise ValueError(f"check[{i}] requires name")
        if state=="accepted" and c["status"]!="pass":
            raise ValueError("accepted cannot include failed or unrun checks")
    if state=="accepted" and p["open_issues"]:
        raise ValueError("accepted cannot conceal open issues; use needs_review")
    if type(p.get("human_approval_required")) is not bool or type(p.get("human_approved")) is not bool:
        raise ValueError("approval booleans required")
    if p["human_approval_required"] and state=="accepted" and not p["human_approved"]:
        raise ValueError("accepted requires recorded human approval")
    return {"structurally_valid":True,"status":state,
            "warning":"Evidence strings and skill_used are agent assertions: review source/artifact and runtime records independently."}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("verification_json",type=Path)
    args=ap.parse_args()
    try:r=validate(json.loads(args.verification_json.read_text(encoding="utf-8")))
    except (ValueError,OSError,json.JSONDecodeError) as ex:
        print(f"INVALID VERIFICATION: {ex}",file=sys.stderr);return 2
    print(json.dumps(r,ensure_ascii=False,indent=2));return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Advisory Skill eligibility: local inventory + optional runtime-verified names.

Not a replacement for Codex runtime Skill discovery or actual tool permissions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from skills_inventory import inventory


def assess(plan, found, runtime_verified=()):
    runtime=set(runtime_verified)
    byname={}
    for s in found.get("skills",[]):
        if s.get("name"):
            byname.setdefault(s["name"],[]).append(s)
    results=[]
    for task in plan.get("tasks",[]):
        names=task.get("skills",{})
        required=names.get("required",[])
        optional=names.get("optional",[])
        for name in dict.fromkeys(required + optional):
            local=byname.get(name,[])
            if len(local)>1: status="ambiguous_duplicate"
            elif len(local)==1 and local[0].get("issues"):status="invalid_metadata"
            elif len(local)==1:status="available_locally"
            elif name in runtime:status="runtime_reported"
            else:status="not_found_locally"
            results.append({"task_id":task.get("id"),"skill":name,"required":name in required,"status":status})
    pending=[x for x in results if x["required"] and x["status"] not in {"available_locally","runtime_reported"}]
    ambiguous=[x for x in results if x["status"]=="ambiguous_duplicate"]
    return {"eligible_to_attempt":not pending and not ambiguous,"matches":results,
            "pending":pending,"note":"Filesystem scan incomplete for plugin/built-in Skills. Runtime-reported availability must be checked in the actual Codex thread. Model may still fail to load/apply a Skill."}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan",type=Path)
    ap.add_argument("--project",type=Path)
    ap.add_argument("--inventory-file",type=Path,help="JSON output of skills_inventory.py, for reproducible testing")
    ap.add_argument("--runtime-verified",action="append",default=[],help="Name observed in the active Codex Skill picker, not automatically verified")
    ns=ap.parse_args()
    try:
        task_plan=json.loads(ns.plan.read_text(encoding="utf-8"))
        skills=json.loads(ns.inventory_file.read_text(encoding="utf-8")) if ns.inventory_file else inventory(project=ns.project)
        result=assess(task_plan,skills,ns.runtime_verified)
    except (OSError,ValueError,json.JSONDecodeError) as ex:
        print(f"SKILL ELIGIBILITY ERROR: {ex}");return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["eligible_to_attempt"] else 3

if __name__=="__main__":
    raise SystemExit(main())

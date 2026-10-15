#!/usr/bin/env python3
"""Preview/rewrite user-owned v5.0 JSON plan preset IDs to CUO v6.0 names.

Never edits an input plan in place; output requires explicit --apply.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

NAMES = {f"orch_{name}":f"cuo-{name}" for name in ("scout", "analyst", "executor", "reviewer", "expert")}
OLD_SKILL = "codex-hybrid-orchestrate"
NEW_SKILL = "codex-universal-orchestrate"


def migrate(plan):
    p=deepcopy(plan)
    count=0
    for task in p.get("tasks",[]):
        ex=task.get("executor",{})
        if ex.get("agent") in NAMES:
            ex["agent"]=NAMES[ex["agent"]];count+=1
        skills=task.get("skills",{})
        for category in ("required","optional"):
            if OLD_SKILL in skills.get(category,[]):
                skills[category]=[NEW_SKILL if s==OLD_SKILL else s for s in skills[category]]
                count+=1
    # Reuse optional plan schema 5.0; changing identifier names is not a schema change.
    return p,count


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--apply",action="store_true")
    ns=ap.parse_args()
    try:
        if ns.input.resolve()==ns.out.resolve():raise ValueError("In-place overwrite refused")
        if ns.out.exists():raise ValueError("Output exists; choose a new path")
        plan=json.loads(ns.input.read_text(encoding="utf-8"))
        migrated,count=migrate(plan)
        print(f"{'APPLY' if ns.apply else 'DRY-RUN'}: {count} identifiers changed; target={ns.out}")
        if ns.apply:
            from validate_plan import validate
            validate(migrated)
            ns.out.parent.mkdir(parents=True,exist_ok=True)
            ns.out.write_text(json.dumps(migrated,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except (OSError,ValueError,json.JSONDecodeError) as ex:
        print(f"PLAN MIGRATION FAILED: {ex}",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())

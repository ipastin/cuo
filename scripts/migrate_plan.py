#!/usr/bin/env python3
"""Migrate CUO plan identifiers and model pins from earlier kit versions.

Never edits an input plan in place; output requires explicit --apply.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from validate_plan import preset_catalog, validate

NAMES = {f"orch_{name}":f"cuo-{name}" for name in ("scout", "analyst", "executor", "reviewer", "expert")}
V6_0_PINS = {
    "cuo-analyst": ("gpt-6.1-sol", "high"),
    "cuo-executor": ("gpt-6.1-sol", "medium"),
    "cuo-reviewer": ("gpt-6.1-sol", "high"),
    "cuo-expert": ("gpt-6-astra", "low"),
}
OLD_SKILL = "codex-hybrid-orchestrate"
NEW_SKILL = "codex-universal-orchestrate"


def migrate(plan):
    p=deepcopy(plan)
    count=0
    presets = preset_catalog()
    for task in p.get("tasks",[]):
        ex=task.get("executor",{})
        if ex.get("agent") in NAMES:
            ex["agent"]=NAMES[ex["agent"]];count+=1
        agent = ex.get("agent")
        pin = (ex.get("model"), ex.get("effort"))
        if ex.get("mode") == "subagent" and pin == V6_0_PINS.get(agent):
            ex["model"] = presets[agent]["model"]
            ex["effort"] = presets[agent]["model_reasoning_effort"]
            count += 1
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
        validate(migrated)
        print(f"{'APPLY' if ns.apply else 'DRY-RUN'}: {count} changes; target={ns.out}")
        if ns.apply:
            ns.out.parent.mkdir(parents=True,exist_ok=True)
            with ns.out.open("x", encoding="utf-8") as output:
                output.write(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n")
    except (OSError,ValueError,json.JSONDecodeError) as ex:
        print(f"PLAN MIGRATION FAILED: {ex}",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())

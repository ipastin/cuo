#!/usr/bin/env python3
"""Validate an advisory Codex task triage decision; no models or tools launched."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

MODES = {"direct", "planned", "orchestrated"}
RISKS = {"low", "moderate", "high", "critical"}


def validate(p):
    if not isinstance(p, dict) or p.get("schema_version") != "1.0":
        raise ValueError("triage schema_version must be 1.0")
    mode, risk = p.get("mode"), p.get("risk")
    if mode not in MODES or risk not in RISKS:
        raise ValueError("invalid mode/risk")
    for f in ("goal", "expected_deliverable", "decision_reason"):
        if not isinstance(p.get(f), str) or not p[f].strip():
            raise ValueError(f"{f} is required")
    count = p.get("proposed_subagents")
    if type(count) is not int or not 0 <= count <= 5:
        raise ValueError("proposed_subagents must be an integer 0..5")
    if mode == "direct" and count:
        raise ValueError("direct requires no subagents")
    if mode == "planned" and count > 2:
        raise ValueError("planned mode may use at most 2 subagents")
    if type(p.get("approval_required")) is not bool or type(p.get("irreversible_operation")) is not bool:
        raise ValueError("approval_required and irreversible_operation must be bool")
    if (risk in {"high", "critical"} or p["irreversible_operation"]) and not p["approval_required"]:
        raise ValueError("approval_required for high-risk or irreversible operations")
    if count:
        why = p.get("delegation_benefit")
        if not isinstance(why, str) or not why.strip():
            raise ValueError("delegation_benefit required when using subagents")
    if mode == "orchestrated":
        deps = p.get("dependency_rationale")
        if not isinstance(deps, str) or not deps.strip():
            raise ValueError("dependency_rationale required in orchestrated mode")
    return {"valid": True, "mode": mode, "proposed_subagents": count,
            "note": "Structural checks only; triage accuracy and actual permissions are not verified."}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("triage_json", type=Path)
    args=ap.parse_args()
    try:
        result=validate(json.loads(args.triage_json.read_text(encoding="utf-8")))
    except (OSError,ValueError,json.JSONDecodeError) as ex:
        print(f"INVALID TRIAGE: {ex}",file=sys.stderr);return 2
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__=="__main__":
    raise SystemExit(main())

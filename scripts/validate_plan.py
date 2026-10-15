#!/usr/bin/env python3
"""Validate v5 optional domain-neutral plan JSON; no model call or network access.

This is NOT a Codex plan API or a replacement for human acceptance/evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,31}$")
SKILL = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")
VALID_MODES = {"main", "subagent", "tool_only", "worktree"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
VALID_RISKS = {"low", "moderate", "high", "critical"}


def nonempty(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty string")
    return value


def list_of_str(value, label: str, *, min_len=0) -> list[str]:
    if not isinstance(value, list) or len(value) < min_len:
        raise ValueError(f"{label} must be a list with at least {min_len} items")
    for i, v in enumerate(value):
        nonempty(v, f"{label}[{i}]")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} has duplicate entries")
    return value


def safe_scope(raw: str) -> str:
    nonempty(raw, "write scope")
    s = raw.replace("\\", "/")
    p = PurePosixPath(s)
    if s.startswith(("/", "~")) or p.is_absolute() or ":" in s.split("/")[0]:
        raise ValueError(f"Invalid write scope: {raw!r}; use a relative path")
    if any(part in ("..", ".git") for part in p.parts) or str(p) == ".":
        raise ValueError(f"Unsafe write scope: {raw!r}")
    if any(x in s for x in "*?[]"):
        raise ValueError(f"No globs in write scope: {raw!r}")
    return str(p).rstrip("/")


def overlaps(a: str, b: str) -> bool:
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def preset_catalog() -> dict[str, dict]:
    out = {}
    for path in sorted((ROOT / "agents").glob("*.toml")):
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        out[payload["name"]] = payload
    return out


def validate(payload: dict) -> dict:
    if not isinstance(payload, dict) or payload.get("schema_version") != "5.0":
        raise ValueError("Expected schema_version='5.0' object")
    nonempty(payload.get("goal"), "goal")
    list_of_str(payload.get("project_context", []), "project_context")
    list_of_str(payload.get("constraints", []), "constraints")

    dels = payload.get("deliverables")
    if not isinstance(dels, list) or not dels:
        raise ValueError("deliverables must be a nonempty array")
    deliverable_ids = set()
    for d in dels:
        if not isinstance(d, dict):
            raise ValueError("deliverable must be object")
        did = nonempty(d.get("id"), "deliverable.id")
        if did in deliverable_ids:
            raise ValueError(f"Duplicate deliverable id: {did}")
        deliverable_ids.add(did)
        nonempty(d.get("kind"), f"deliverable {did} kind")
        nonempty(d.get("description"), f"deliverable {did} description")

    execpol = payload.get("execution_policy")
    if not isinstance(execpol, dict):
        raise ValueError("execution_policy must be object")
    limit = execpol.get("max_parallel_agents")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 5:
        raise ValueError("max_parallel_agents must be an integer in range 1..5")
    if not isinstance(execpol.get("worktrees_enabled"), bool):
        raise ValueError("worktrees_enabled must be bool")
    list_of_str(execpol.get("approval_gates"), "approval_gates")

    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a nonempty array")
    seen = set()
    parents: dict[str, set[str]] = {}
    specs: dict[str, list[str]] = {}
    models = preset_catalog()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("task must be an object")
        tid = task.get("id")
        if not isinstance(tid, str) or not ID.fullmatch(tid) or tid in seen:
            raise ValueError(f"Invalid/duplicate task id: {tid!r}")
        seen.add(tid)
        nonempty(task.get("goal"), f"{tid}.goal")
        parents[tid] = set(list_of_str(task.get("depends_on"), f"{tid}.depends_on"))
        if tid in parents[tid]:
            raise ValueError(f"Self-dependency: {tid}")
        list_of_str(task.get("capabilities"), f"{tid}.capabilities", min_len=1)
        list_of_str(task.get("evidence", []), f"{tid}.evidence")
        list_of_str(task.get("acceptance_criteria"), f"{tid}.acceptance_criteria", min_len=1)
        scopes = list_of_str(task.get("write_scopes"), f"{tid}.write_scopes")
        specs[tid] = [safe_scope(x) for x in scopes]
        risk = task.get("risk")
        if risk not in VALID_RISKS:
            raise ValueError(f"{tid}: invalid risk {risk!r}")

        skills = task.get("skills")
        if not isinstance(skills, dict):
            raise ValueError(f"{tid}.skills must be object")
        required = list_of_str(skills.get("required"), f"{tid}.skills.required")
        optional = list_of_str(skills.get("optional"), f"{tid}.skills.optional")
        list_of_str(skills.get("discovery_hint"), f"{tid}.skills.discovery_hint")
        if set(required) & set(optional):
            raise ValueError(f"{tid}: required and optional Skills overlap")
        if any(not SKILL.fullmatch(s) for s in required + optional):
            raise ValueError(f"{tid}: Skill names must be exact identifiers, not prose/hints")

        exe = task.get("executor")
        if not isinstance(exe, dict) or exe.get("mode") not in VALID_MODES:
            raise ValueError(f"{tid}: invalid executor.mode")
        mode = exe["mode"]
        if mode == "subagent" and "codex-universal-orchestrate" in required + optional:
            raise ValueError(f"{tid}: orchestration Skill is main-thread only; do not assign to child")
        agent = exe.get("agent")
        model = exe.get("model")
        effort = exe.get("effort")
        if mode == "tool_only":
            if any(x is not None for x in (agent, model, effort)):
                raise ValueError(f"{tid}: tool_only requires null agent/model/effort")
        elif mode == "subagent":
            if agent not in models:
                raise ValueError(f"{tid}: unknown installed preset {agent!r}")
            conf = models[agent]
            if model != conf["model"] or effort != conf["model_reasoning_effort"]:
                raise ValueError(f"{tid}: agent preset pins {conf['model']}/{conf['model_reasoning_effort']}; plan disagrees")
            if conf.get("sandbox_mode") == "read-only" and specs[tid]:
                raise ValueError(f"{tid}: read-only preset assigned write_scopes")
        else:
            if agent not in (None, ""):
                raise ValueError(f"{tid}: main/worktree mode cannot assign native child preset")
            nonempty(model, f"{tid}.executor.model")
            if effort not in VALID_EFFORTS:
                raise ValueError(f"{tid}: invalid effort")
            if mode == "worktree" and not execpol["worktrees_enabled"]:
                raise ValueError(f"{tid}: worktree requires worktrees_enabled=true")

        per = task.get("permissions")
        if not isinstance(per, dict):
            raise ValueError(f"{tid}.permissions must be object")
        for k in ("external_write", "irreversible", "human_gate"):
            if not isinstance(per.get(k), bool):
                raise ValueError(f"{tid}.permissions.{k} must be bool")
        if (per["external_write"] or per["irreversible"] or risk == "critical" or mode == "worktree") and not per["human_gate"]:
            raise ValueError(f"{tid}: user approval gate required for risky/external/worktree operation")

    if any(d not in seen for pp in parents.values() for d in pp):
        missing = sorted(set().union(*parents.values()) - seen)
        raise ValueError(f"Unknown dependencies: {missing}")

    # Kahn graph layers for inspectable candidate concurrency waves.
    done = set()
    waves = []
    while len(done) < len(tasks):
        ready = sorted(t for t, p in parents.items() if t not in done and p <= done)
        if not ready:
            raise ValueError("Dependency cycle detected")
        waves.append(ready)
        done.update(ready)

    def reachable(a: str, b: str) -> bool:
        stack = list(parents[b])
        visited = set()
        while stack:
            x = stack.pop()
            if x == a:
                return True
            if x in visited:
                continue
            visited.add(x)
            stack.extend(parents[x])
        return False

    # If two tasks can execute concurrently (no dependency path), disallow shared write scopes.
    ids = list(parents)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if reachable(a, b) or reachable(b, a):
                continue
            for x in specs[a]:
                for y in specs[b]:
                    if overlaps(x, y):
                        raise ValueError(f"Concurrent write-scope conflict: {a}:{x} vs {b}:{y}; serialize via depends_on")

    return {"task_count": len(tasks), "deliverable_count": len(dels), "candidate_waves": waves,
            "max_parallel_agents": limit, "warnings": ["This is structural validation only; Skills, model entitlement, actual execution and quality were not verified."]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="Optional v5 JSON task plan")
    ap.add_argument("--json", action="store_true", help="Machine-readable result")
    ns = ap.parse_args(argv)
    try:
        result = validate(json.loads(ns.path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    if ns.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"VALID STRUCTURE: {result['task_count']} tasks, {result['deliverable_count']} deliverables")
        for i, wave in enumerate(result["candidate_waves"], start=1):
            print(f"  Dependency wave {i}: {', '.join(wave)}")
        print(f"Concurrency cap (not a target): {result['max_parallel_agents']}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Advisory inventory of filesystem-installed Codex Skills; does not discover plugins/built-ins.

Never assumes a Skill is activated merely because its SKILL.md exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


def skill_info(path: Path) -> dict:
    result = {"path": str(path), "name": None, "description": None, "issues": []}
    try:
        txt = path.read_text(encoding="utf-8")
    except (UnicodeError, OSError) as exc:
        result["issues"].append(f"read error: {exc}")
        return result
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if not m:
        result["issues"].append("missing YAML frontmatter")
        return result
    header = m.group(1)
    # Intentionally shallow: recognizes simple 'name:' and 'description:' scalars only.
    for key in ("name", "description"):
        hit = re.search(r"(?m)^" + key + r":\s*(.*)$", header)
        if hit:
            value = hit.group(1).strip().strip('"\'')
            result[key] = value if value and value not in ('|', '>') else None
        if not result[key]:
            result["issues"].append(f"missing/simple-scalar parse failed for {key}; review manually")
    return result


def inventory(project: Path | None = None, extra_roots: list[Path] | None = None, home: Path | None = None) -> dict:
    home = home or Path.home()
    roots = [home / ".agents" / "skills", Path("/etc/codex/skills")]
    if project:
        project = project.resolve()
        if project.is_file():
            project = project.parent
        # Repositories can contain skills under the current directory and ancestor paths.
        try:
            cmd = subprocess.run(["git", "-C", str(project), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            repo_root = Path(cmd.stdout.strip()).resolve() if cmd.returncode == 0 else project
        except OSError:
            repo_root = project
        current = project
        while True:
            roots.append(current / ".agents" / "skills")
            if current == repo_root or current == current.parent:
                break
            current = current.parent
    roots.extend(extra_roots or [])
    unique = []
    seen_path = set()
    for root in roots:
        key = str(root.resolve())
        if key not in seen_path:
            seen_path.add(key)
            unique.append(root)
    found = []
    for root in unique:
        if root.is_dir():
            for p in root.rglob("SKILL.md"):
                found.append(skill_info(p))
    names: dict[str, list[str]] = {}
    for item in found:
        if item["name"]:
            names.setdefault(item["name"], []).append(item["path"])
    duplicates = {name: paths for name, paths in names.items() if len(paths) > 1}
    return {"roots_checked": [str(p) for p in unique], "skills": found,
            "duplicate_names": duplicates,
            "note": "Filesystem-only advisory scan. Check /skills or $ picker for runtime/plugin/system Skills."}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, help="Current project or repository subdirectory (optional)")
    ap.add_argument("--extra-root", type=Path, action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    data = inventory(args.project, args.extra_root)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("LOCAL SKILL INVENTORY — advisory, not Codex runtime registry")
        for s in data["skills"]:
            print(f"- {s['name'] or '[unknown]'}: {s['description'] or '[description unavailable]'}  [{s['path']}]")
            for issue in s["issues"]:
                print(f"  ISSUE {issue}")
        for name, paths in data["duplicate_names"].items():
            print(f"WARNING duplicate name: {name} ({len(paths)} paths)")
        print(data["note"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Safe Codex Universal Orchestration v6.0 installer/migrator.

No external calls. Dry run by default. Preflight before mutation, preserve unrelated
Codex configuration and back up every legacy file before opt-in retirement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.0.0"
V4_BEGIN = "<!-- codex-hybrid-routing:v4 BEGIN -->"
V4_END = "<!-- codex-hybrid-routing:v4 END -->"
V5_BEGIN = "<!-- codex-universal-routing:v5 BEGIN -->"
V5_END = "<!-- codex-universal-routing:v5 END -->"
OLD_SKILL = "codex-hybrid-orchestrate"  # previous actual on-disk name
NEW_SKILL = "codex-universal-orchestrate"
OLD_V5_AGENTS = tuple(f"orch_{role}.toml" for role in
                      ("scout", "analyst", "executor", "reviewer", "expert"))
OLD_V4_AGENTS = (
    "hy_advisor.toml", "hy_advisor_deep.toml", "hy_docs_researcher.toml",
    "hy_implementer.toml", "hy_repo_explorer.toml", "hy_reviewer.toml",
    "hy_test_mapper.toml",
)
BASELINE = json.loads((ROOT / "migration" / "v5.0-baseline.json").read_text(encoding="utf-8"))["files"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup(path: Path, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    target = directory / f"{path.name}.{stamp}.bak"
    if path.is_dir():
        shutil.copytree(path, target)
    else:
        shutil.copy2(path, target)
    print(f"BACKUP {path} -> {target}")
    return target


def marked_contents(path: Path) -> str:
    s = path.read_text(encoding="utf-8") if path.exists() else ""
    matches = list(ROOT.glob("AGENTS_ROUTING_ADDENDUM__*.md"))
    if len(matches) != 1:
        raise ValueError("Expected exactly one AGENTS routing addendum")
    txt = matches[0].read_text(encoding="utf-8")
    m = re.match(r"(?s)\A---\n.*?\n---\n(.*)\Z", txt)
    if not m:
        raise ValueError("Missing addendum YAML frontmatter")
    new = f"{V5_BEGIN}\n{m.group(1).strip()}\n{V5_END}"
    v4 = V4_BEGIN in s or V4_END in s
    v5 = V5_BEGIN in s or V5_END in s
    if v4 and v5:
        raise ValueError("Both v4 and v5 AGENTS markers present")
    if v4:
        old_b, old_e = V4_BEGIN, V4_END
    elif v5:
        old_b, old_e = V5_BEGIN, V5_END
    else:
        return s.rstrip() + ("\n\n" if s.strip() else "") + new + "\n"
    if s.count(old_b) != 1 or s.count(old_e) != 1:
        raise ValueError("Malformed or duplicate AGENTS markers")
    a = s.index(old_b)
    b = s.index(old_e) + len(old_e)
    if a >= b:
        raise ValueError("AGENTS markers in wrong order")
    return s[:a] + new + s[b:]


def pristine_v5_file(installed: Path, old_rel: str) -> bool:
    expected = BASELINE.get(old_rel)
    return bool(expected) and installed.is_file() and digest(installed) == expected


def pristine_v5_skill(installed: Path) -> bool:
    prefix = "skill/" + OLD_SKILL + "/"
    expected = {Path(key[len(prefix):]): val for key, val in BASELINE.items()
                if key.startswith(prefix)}
    if not installed.is_dir():
        return False
    present = {p.relative_to(installed): digest(p) for p in installed.rglob("*") if p.is_file()}
    return bool(expected) and present == expected


def install_copy(src: Path, target: Path, ns, backups: Path):
    if target.exists():
        if src.is_dir() and target.is_dir():
            lhs = {p.relative_to(src): digest(p) for p in src.rglob("*") if p.is_file()}
            rhs = {p.relative_to(target): digest(p) for p in target.rglob("*") if p.is_file()}
            identical = lhs == rhs
        else:
            identical = src.is_file() and target.is_file() and digest(src) == digest(target)
        if identical:
            print(f"SKIP identical {target}")
            return
        if not ns.replace_managed:
            print(f"BLOCKED existing differs: {target} (review before --replace-managed)")
            raise ValueError(f"Existing managed target differs: {target}")
        print(f"{'APPLY' if ns.apply else 'PLAN '} replace with backup {target}")
        if ns.apply:
            backup(target, backups)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
    else:
        print(f"{'APPLY' if ns.apply else 'PLAN '} copy {target}")
    if ns.apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)


def install_config(src: Path, dst: Path, ns):
    desired = tomllib.loads(src.read_text(encoding="utf-8"))
    if not dst.exists():
        print(f"{'APPLY' if ns.apply else 'PLAN '} create config: {dst}")
        if ns.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return
    existing = tomllib.loads(dst.read_text(encoding="utf-8"))
    mismatch = [k for k in ("model", "model_reasoning_effort", "review_model") if existing.get(k) != desired[k]]
    mismatch += [f"agents.{key}" for key, val in desired["agents"].items()
                 if existing.get("agents", {}).get(key) != val]
    if mismatch:
        pending = dst.parent / "routing-v6.0.fragment.toml"
        print(f"{'APPLY' if ns.apply else 'PLAN '} manual merge: {pending}")
        print("NOTE config.toml untouched. Differences: " + ", ".join(mismatch))
        if ns.apply:
            pending.parent.mkdir(parents=True, exist_ok=True)
            if pending.exists() and digest(pending) != digest(src) and not ns.replace_managed:
                raise ValueError(f"Unrelated merge fragment exists at {pending}")
            shutil.copy2(src, pending)
    else:
        print(f"SKIP config already matches: {dst}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    parser.add_argument("--scope", choices=("global", "project"), default="global")
    parser.add_argument("--project", type=Path, help="Existing project root for project scope")
    version = parser.add_mutually_exclusive_group()
    version.add_argument("--upgrade-v5", action="store_true", help="Migrate old v5 Skill and orch_* agents")
    version.add_argument("--upgrade-v4", action="store_true", help="Migrate old v4 Skill / policy")
    parser.add_argument("--archive-v4-agents", action="store_true", help="Retire known hy_* presets; requires --upgrade-v4")
    parser.add_argument("--archive-modified-legacy", action="store_true", help="Also archive edited v5 legacy files; requires --upgrade-v5 and careful review")
    parser.add_argument("--replace-managed", action="store_true", help="Replace differing destination managed files with backups")
    parser.add_argument("--active-override", action="store_true", help="Edit pre-existing AGENTS.override.md")
    ns = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error("Python 3.11+ required")
    if ns.archive_v4_agents and not ns.upgrade_v4:
        parser.error("--archive-v4-agents requires --upgrade-v4")
    if ns.archive_modified_legacy and not ns.upgrade_v5:
        parser.error("--archive-modified-legacy requires --upgrade-v5")
    if ns.scope == "project":
        if not ns.project or not ns.project.is_dir():
            parser.error("--scope project requires --project EXISTING_DIR")
        home_dir = ns.project.resolve()
        config_root = home_dir / ".codex"
        skills_root = home_dir / ".agents" / "skills"
        instr_root = home_dir
    else:
        config_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
        skills_root = Path.home() / ".agents" / "skills"
        instr_root = config_root
    override = instr_root / "AGENTS.override.md"
    if override.exists() and not ns.active_override:
        print("BLOCKED: AGENTS.override.md takes precedence; use --active-override after review", file=sys.stderr)
        return 2
    if ns.active_override and not override.is_file():
        print("BLOCKED: --active-override requires pre-existing AGENTS.override.md", file=sys.stderr)
        return 2
    instr = override if ns.active_override else instr_root / "AGENTS.md"
    new_skill = skills_root / NEW_SKILL
    old_skill = skills_root / OLD_SKILL
    old_v5 = [config_root / "agents" / f for f in OLD_V5_AGENTS if (config_root / "agents" / f).exists()]
    old_v4 = [config_root / "agents" / f for f in OLD_V4_AGENTS if (config_root / "agents" / f).exists()]
    backups = config_root / "routing-v6.0-backups"
    try:
        tomllib.loads((ROOT / "config-fragment.toml").read_text(encoding="utf-8"))
        for src in (ROOT / "agents").glob("*.toml"):
            agent = tomllib.loads(src.read_text(encoding="utf-8"))
            if not all(k in agent for k in ("name", "description", "developer_instructions")):
                raise ValueError(f"Invalid custom agent: {src.name}")
        if (config_root / "config.toml").exists():
            tomllib.loads((config_root / "config.toml").read_text(encoding="utf-8"))
        content = marked_contents(instr)
        if V4_BEGIN in (instr.read_text(encoding="utf-8") if instr.exists() else "") and not ns.upgrade_v4:
            raise ValueError("v4 AGENTS policy detected: explicitly use --upgrade-v4")
        if old_skill.exists() or old_v5:
            if not (ns.upgrade_v5 or ns.upgrade_v4):
                raise ValueError("Legacy skill/presets installed: explicitly use --upgrade-v5 or --upgrade-v4")
        if ns.upgrade_v5:
            legacy = ([old_skill] if old_skill.exists() else []) + old_v5
            for path in legacy:
                ok = pristine_v5_skill(path) if path == old_skill else pristine_v5_file(path, "agents/" + path.name)
                if not ok and not ns.archive_modified_legacy:
                    raise ValueError(f"Modified/unrecognized v5 legacy file: {path}; review then use --archive-modified-legacy if intended")
        if ns.upgrade_v4 and old_skill.exists():
            txt = (old_skill / "SKILL.md").read_text(encoding="utf-8")
            if 'version: "5.0.0"' in txt:
                raise ValueError("Installed previous Skill appears to be v5, not v4; use --upgrade-v5")
        if ns.upgrade_v4 and old_v5:
            raise ValueError("v5 orch_* agents detected: use --upgrade-v5 (or resolve mixed install manually)")
        if old_v4 and not ns.archive_v4_agents:
            print(f"NOTE: {len(old_v4)} previous hy_* agents remain; use --upgrade-v4 --archive-v4-agents after reviewing")
        if ns.upgrade_v5 and old_v4:
            raise ValueError("Old hy_* presets also found; resolve duplicate v4 presets before v5 migration")
        # Preflight all new targets, so a later conflict cannot cause partial migration.
        all_sources = [(src, config_root / "agents" / src.name) for src in sorted((ROOT / "agents").glob("*.toml"))]
        all_sources += [(ROOT / "skill" / NEW_SKILL, new_skill)]
        for src, dest in all_sources:
            if dest.exists() and not ns.replace_managed:
                if src.is_dir() and dest.is_dir():
                    a = {p.relative_to(src): digest(p) for p in src.rglob("*") if p.is_file()}
                    b = {p.relative_to(dest): digest(p) for p in dest.rglob("*") if p.is_file()}
                    if a != b:
                        raise ValueError(f"Existing managed target differs: {dest}; use --replace-managed after review")
                elif not (src.is_file() and dest.is_file() and digest(src) == digest(dest)):
                    raise ValueError(f"Existing managed target differs: {dest}")
        if (config_root / "routing-v6.0.fragment.toml").exists() and not ns.replace_managed:
            pending = config_root / "routing-v6.0.fragment.toml"
            if digest(pending) != digest(ROOT / "config-fragment.toml"):
                raise ValueError("Existing merge fragment differs; review before --replace-managed")
    except (OSError, ValueError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        print(f"BLOCKED preflight: {exc}", file=sys.stderr)
        return 2

    print(f"Codex Universal Orchestration v{VERSION} | {'APPLY' if ns.apply else 'DRY-RUN'} | {ns.scope} scope")
    print("No Codex sessions, API keys, Git worktrees or external writes are touched.")
    # For v5 migrations legacy retirement happens first, after full preflight.
    legacy_to_archive = []
    if ns.upgrade_v5:
        legacy_to_archive += ([old_skill] if old_skill.exists() else []) + old_v5
    if ns.upgrade_v4:
        legacy_to_archive += ([old_skill] if old_skill.exists() else [])
        if ns.archive_v4_agents:
            legacy_to_archive += old_v4
    for path in legacy_to_archive:
        print(f"{'APPLY' if ns.apply else 'PLAN '} backup + retire legacy: {path}")
        if ns.apply:
            backup(path, backups)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    try:
        install_config(ROOT / "config-fragment.toml", config_root / "config.toml", ns)
        for src in sorted((ROOT / "agents").glob("*.toml")):
            install_copy(src, config_root / "agents" / src.name, ns, backups)
        install_copy(ROOT / "skill" / NEW_SKILL, new_skill, ns, backups)
        if not instr.exists() or content != instr.read_text(encoding="utf-8"):
            print(f"{'APPLY' if ns.apply else 'PLAN '} update AGENTS with backup: {instr}")
            if ns.apply:
                if instr.exists():
                    backup(instr, backups)
                instr.parent.mkdir(parents=True, exist_ok=True)
                instr.write_text(content, encoding="utf-8")
        else:
            print(f"SKIP instructions unchanged: {instr}")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Only one orchestration Skill installed: codex-universal-orchestrate. Other Skills unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Optional worktree + `codex exec` launcher for ChatGPT-authenticated Codex CLI.

Default is --plan (zero mutations). --prepare creates isolated Git worktrees.
--run starts independent Codex CLI sessions, waits, audits paths, and writes a report.
Does NOT merge, commit, push, deploy, delete worktrees, or call the OpenAI API.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

VALID_MODELS = {"gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra", "gpt-5.6-terra"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
VALID_SANDBOXES = {"read-only", "workspace-write"}
ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"Git failed: {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def validated_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("allowed_paths must have non-empty string entries")
    raw = value.replace("\\", "/")
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or any(p in ("..", ".git") for p in candidate.parts) or raw.startswith("~"):
        raise ValueError(f"Unsafe owned path: {value!r}")
    if "*" in raw or "?" in raw or "[" in raw or "]" in raw:
        raise ValueError(f"Glob syntax is unsupported for owned paths: {value!r}")
    canonical = str(candidate)
    if canonical == ".":
        raise ValueError("Whole repo cannot be owned by an isolated task")
    return canonical + ("/" if raw.endswith("/") else "")


def overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if a.endswith("/") and b.startswith(a):
        return True
    if b.endswith("/") and a.startswith(b):
        return True
    return False


def covers(allowed: list[str], path: str) -> bool:
    return any(path.startswith(spec) if spec.endswith("/") else path == spec for spec in allowed)


def load_manifest(path: Path) -> tuple[dict, Path, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != "1":
        raise ValueError("Manifest must be an object with version='1'")
    repo_str = payload.get("repo")
    if not isinstance(repo_str, str):
        raise ValueError("repo must be an absolute path")
    repo = Path(repo_str).expanduser().resolve()
    if not Path(repo_str).expanduser().is_absolute() or not repo.is_dir():
        raise ValueError("repo must be an existing absolute directory")
    if not shutil.which("git"):
        raise ValueError("git executable not found")
    root = Path(git(repo, "rev-parse", "--show-toplevel")).resolve()
    if root != repo:
        raise ValueError(f"repo must point to the git root ({root})")
    base_ref = payload.get("base_ref", "HEAD")
    if not isinstance(base_ref, str) or not base_ref or base_ref.startswith("-"):
        raise ValueError("base_ref must be an existing safe git ref")
    base_sha = git(repo, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 5:
        raise ValueError("tasks must contain 1–5 independent entries")
    ids: set[str] = set()
    write_paths: list[tuple[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Each task must be an object")
        tid = task.get("id")
        if not isinstance(tid, str) or not ID_RE.fullmatch(tid) or tid in ids:
            raise ValueError(f"Invalid/duplicate task id: {tid!r}")
        ids.add(tid)
        if task.get("depends_on"):
            raise ValueError(f"Task {tid} has dependencies: separate worktree lanes must be independent")
        if task.get("model") not in VALID_MODELS:
            raise ValueError(f"Unsupported model in {tid}: {task.get('model')!r}")
        if task.get("effort") not in VALID_EFFORTS:
            raise ValueError(f"Unsupported effort in {tid}")
        if task.get("sandbox") not in VALID_SANDBOXES:
            raise ValueError(f"Unsupported sandbox in {tid}")
        if not isinstance(task.get("prompt"), str) or len(task["prompt"].strip()) < 12:
            raise ValueError(f"Task {tid} needs a meaningful prompt")
        allowed = task.get("allowed_paths", [])
        if not isinstance(allowed, list):
            raise ValueError(f"allowed_paths must be list in {tid}")
        normalized = [validated_path(p) for p in allowed]
        task["allowed_paths"] = normalized
        if task["sandbox"] == "workspace-write":
            if not normalized:
                raise ValueError(f"Writable task {tid} requires explicit allowed_paths")
            for spec in normalized:
                write_paths.append((tid, spec))
    for i, (t1, p1) in enumerate(write_paths):
        for t2, p2 in write_paths[i + 1:]:
            if t1 != t2 and overlap(p1, p2):
                raise ValueError(f"Overlapping write ownership: {t1} {p1} versus {t2} {p2}")
    return payload, repo, base_sha


def changed_paths(worktree: Path) -> list[str]:
    tracked = git(worktree, "diff", "--name-only", "HEAD", "--")
    untracked = git(worktree, "ls-files", "--others", "--exclude-standard")
    return sorted(set([p for p in tracked.splitlines() + untracked.splitlines() if p]))


def build_prompt(task: dict, sha: str) -> str:
    mode = task["sandbox"]
    allowed = task["allowed_paths"]
    return f"""INDEPENDENT CODEX WORKTREE LANE: {task['id']}
BASE_COMMIT: {sha}
MODEL: {task['model']}
SANDBOX: {mode}
OWNED_PATHS: {', '.join(allowed) if allowed else '(read-only; no writes permitted)'}

{task['prompt']}

RULES:
- Do not spawn further subagents, call another Codex process or start concurrent jobs inside this lane.
- Work only in this isolated checkout. No branch/commit/push/merge/deployment/destructive operations.
- Never disclose secrets in your output. Do not modify .env, credentials, production configuration or tracked data outside assigned scope.
- For writable tasks, do not change files outside OWNED_PATHS. For read-only tasks, do not change any files.
- Return: outcome, files read/changed, evidence, tests run/not-run, blockers, remaining risks.
- Never imply that integration with the parent branch or another worktree occurred.
"""


def run_lane(task: dict, worktree: Path, run_dir: Path, sha: str) -> dict:
    tid = task["id"]
    outfile = run_dir / f"{tid}.stdout.txt"
    errfile = run_dir / f"{tid}.stderr.log"
    args = ["codex", "exec", "-m", task["model"], "-c", f'model_reasoning_effort="{task["effort"]}"', "--sandbox", task["sandbox"], "-"]
    try:
        env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "CODEX_API_KEY")}
        with outfile.open("w", encoding="utf-8") as stdout, errfile.open("w", encoding="utf-8") as stderr:
            proc = subprocess.run(args, cwd=worktree, input=build_prompt(task, sha), stdout=stdout, stderr=stderr, text=True, env=env)
        code = proc.returncode
        failure = None
    except Exception as exc:
        code = -1
        failure = f"{type(exc).__name__}: {exc}"
        errfile.write_text(failure, encoding="utf-8")
    changed = changed_paths(worktree)
    unexpected = [p for p in changed if task["sandbox"] == "read-only" or not covers(task["allowed_paths"], p)]
    return {"task_id": tid, "model": task["model"], "effort": task["effort"], "sandbox": task["sandbox"], "returncode": code, "error": failure,
            "changed_paths": changed, "out_of_scope_paths": unexpected, "worktree": str(worktree), "stdout": str(outfile), "stderr": str(errfile),
            "status": "pass" if code == 0 and not unexpected else "review_required"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Only describe the validated tasks (default)")
    mode.add_argument("--prepare", action="store_true", help="Create isolated detached Git worktrees, do not start Codex")
    mode.add_argument("--run", action="store_true", help="Create worktrees and start independent codex exec sessions")
    parser.add_argument("--allow-writes", action="store_true", help="Explicitly approve workspace-write lanes during --run")
    parser.add_argument("--concurrency", type=int, default=2, help="Maximum concurrent Codex CLI sessions (1..5; default 2)")
    parser.add_argument("--output-root", type=Path, default=Path.home()/".codex"/"worktree-lanes", help="Worktrees and local logs root, outside repo")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error("Python 3.11+ required")
    if not 1 <= args.concurrency <= 5:
        parser.error("--concurrency must be 1..5")
    try:
        manifest, repo, sha = load_manifest(args.manifest)
        dirty = git(repo, "status", "--porcelain", "--untracked-files=all")
        if dirty:
            raise RuntimeError("Git repo has staged, modified or untracked files; clean/commit intentionally before worktree lanes")
        if args.run and any(t["sandbox"] == "workspace-write" for t in manifest["tasks"]) and not args.allow_writes:
            raise RuntimeError("Writable lanes need explicit --allow-writes")
        if args.run and any(os.environ.get(key) for key in ("OPENAI_API_KEY", "CODEX_API_KEY")):
            raise RuntimeError("This Kit uses ChatGPT Pro sign-in only: unset OPENAI_API_KEY and CODEX_API_KEY before --run")
        if args.run and not shutil.which("codex"):
            raise RuntimeError("codex CLI not in PATH; install and sign in with ChatGPT before --run")
        stamp = dt.datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{repo.name}-{stamp}"
        root = args.output_root.expanduser().resolve() / run_id
        print(f"REPO: {repo}\nBASE: {sha}\nMODE: {'RUN' if args.run else 'PREPARE' if args.prepare else 'DRY RUN'}")
        for task in manifest["tasks"]:
            print(f"  {task['id']}: {task['model']} ({task['effort']}), {task['sandbox']} → {root/task['id']}")
        if not args.prepare and not args.run:
            print("No files, worktrees, sessions, or API calls were created.")
            return 0
        root.mkdir(parents=True, exist_ok=False)
        (root/"manifest.snapshot.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        worktrees: dict[str, Path] = {}
        for task in manifest["tasks"]:
            path = root/task["id"]
            subprocess.run(["git", "-C", str(repo), "worktree", "add", "--detach", str(path), sha], check=True, text=True, capture_output=True)
            worktrees[task["id"]] = path
            print(f"CREATED worktree {path}")
        if args.prepare:
            print("Prepared only. Worktrees remain for manual inspection; nothing was executed or merged.")
            return 0
        results=[]
        with ThreadPoolExecutor(max_workers=min(args.concurrency, len(worktrees))) as executor:
            jobs={executor.submit(run_lane, task, worktrees[task["id"]], root, sha): task["id"] for task in manifest["tasks"]}
            for future in as_completed(jobs):
                result=future.result()
                results.append(result)
                print(f"DONE {result['task_id']}: {result['status']} (Codex exit {result['returncode']})")
        summary={"run_id":run_id,"repo":str(repo),"base_sha":sha,"results":sorted(results,key=lambda r:r["task_id"]),"note":"Manual review and integration only; no merge, commit, push, cleanup or deploy"}
        (root/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False), encoding="utf-8")
        ts=dt.datetime.now(ZoneInfo("UTC")).strftime("%d-%m-%y_%H-%M-%S")
        md=f"---\ntitle: Codex Isolated Worktree Run\ncreated: '{ts.replace('_',' ')}'\nupdated: '{ts.replace('_',' ')}'\nversion: '6.0.0'\ncommit: 'docs(codex): record isolated worktree lane run'\n---\n\n# Worktree Run {run_id}\n\nBase: `{sha}`; no merges executed.\n\n"
        for r in summary["results"]:
            md+=f"## {r['task_id']} — {r['status']}\n\nModel: `{r['model']}`; exit `{r['returncode']}`; worktree `{r['worktree']}`.\n\nChanged paths: {r['changed_paths']}\n\nOut of scope: {r['out_of_scope_paths']}\n\nLog: `{r['stderr']}`; result: `{r['stdout']}`\n\n"
        md+="Review each lane, integrate manually and run tests before finalizing. Do not assume agent success means acceptance.\n"
        (root/f"RUN_REPORT__created-{ts}__updated-{ts}__v6.0.0.md").write_text(md,encoding="utf-8")
        print(f"REPORT {root/'summary.json'}")
        print("Worktrees retained; no auto-merge, branch push, deletion or app deployment.")
        return 0 if all(r["status"] == "pass" for r in results) else 2
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        print("No automatic cleanup or reset is performed. Inspect partially created worktrees if preparation failed.",file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

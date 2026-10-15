---
title: "Isolated Codex Worktree Guidelines"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Optional isolated worktree execution

Native subagent threads share a working directory. Worktrees can isolate repository files for independent, long-running, write-heavy tasks, but are **not** the same as a native `spawn_agent`.

The optional `worktree_lanes.py` is preserved from v4 for compatibility: it launches separate `codex exec -m ...` CLI processes using existing ChatGPT sign-in. It does **not** implement an always-on scheduler or translate the universal v5 task DAG automatically.

Before `--prepare` or `--run`, require user authorization. Default to `--plan`; use 1–2 concurrent processes initially. Ensure the base is clean and write scopes are disjoint. Review each independent result and merge manually. Never automatically push, force reset, delete source files, deploy or write external system records.

Do not treat worktrees as isolation for Figma documents, cloud shared files, data stores, tasks, or SaaS APIs. Permission policies and human signoff remain outside version control.

Example commands:

```bash
python3 optional/scripts/worktree_lanes.py --manifest optional/examples/worktree-lanes.example.json --plan
# After editing the JSON manifest to an absolute local repository path, and only when authorized:
python3 optional/scripts/worktree_lanes.py --manifest /path/to/my-lanes.json --run --concurrency 2
```

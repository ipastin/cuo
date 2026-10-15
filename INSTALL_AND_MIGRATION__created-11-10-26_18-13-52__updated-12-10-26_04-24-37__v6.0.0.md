---
title: "Installation and Safe Naming Migration"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Installation / v4 & v5 migration

All commands below run **locally** and do not call API services or consume Pro usage. Python 3.11+ is required for `tomllib`.

## Before first install

1. Ensure Codex CLI is signed in via **ChatGPT** (`codex login` if necessary), not an API key.
2. Back up your existing `~/.codex` configuration and identify any v3/v4 AGENTS instructions.
3. Unzip Kit; from its root run `python3 scripts/install.py` (dry-run). Review proposed actions.

## New installation

```bash
python3 scripts/install.py
python3 scripts/install.py --apply
```

If `~/.codex/config.toml` already exists, it will **never be overwritten**. Review the new `routing-v6.0.fragment.toml` and merge relevant keys manually. Don't create a duplicate `[agents]` block; preserve existing MCP, permissions and profiles.

## Upgrade an installed v4

```bash
python3 scripts/install.py --upgrade-v4
python3 scripts/install.py --apply --upgrade-v4
```

`--upgrade-v4` explicitly permits backing up and retiring the previous `codex-hybrid-orchestrate` Skill, replacing the v4-marked AGENTS block, and installing the new `codex-universal-orchestrate` Skill and `cuo-*` presets. **Old `hy_*` agents remain** unless you explicitly use `--archive-v4-agents`, which moves only recognized legacy filenames into dated backup storage; inspect for custom edits first.

```bash
python3 scripts/install.py --apply --upgrade-v4 --archive-v4-agents
```

For a project-scoped setup:

```bash
python3 scripts/install.py --scope project --project /absolute/path/to/repo
python3 scripts/install.py --scope project --project /absolute/path/to/repo --apply
```

If `AGENTS.override.md` exists, it shadows same-directory AGENTS instructions. Use `--active-override` only when that file exists and should receive the v5 block.

## Why the new Skill name?

This is an intentional change from `$codex-hybrid-orchestrate` to `$codex-universal-orchestrate`. The old name is not left installed as a second orchestration Skill after an approved migration. Update user-owned shortcuts manually; unrelated Skills remain untouched.

## Verify in Codex

- `codex --version`; open Codex and check `/model` and `/agent`.
- `/skills` or `$` picker shows `codex-universal-orchestrate` and intended existing Skills.
- Explicitly invoke `$codex-universal-orchestrate` on a safe read-only mixed task.
- Inspect child threads and verify actual models + Skill usage; static TOML syntax doesn't prove runtime access.

## Rollback

Install logs backup paths for changed v4 Skill and AGENTS files. Restore from `~/.codex/routing-v6.0-backups/` manually; do not delete unrelated config or secrets. If old agents were archived, move them back explicitly. Don't remove all of `~/.codex`.

## v6.0 naming migration (recommended if v5.0 installed)

The v5.0 Skill was `$codex-hybrid-orchestrate` and agent presets were `orch_*`. v6.0 uses **`$codex-universal-orchestrate`** and **`cuo-*`**. These are actual Codex IDs (`SKILL.md` frontmatter `name`, and TOML `name`) as well as directory/file names.

```bash
python3 scripts/install.py --upgrade-v5
python3 scripts/install.py --upgrade-v5 --apply
```

Installer validates the known v5.0 source fingerprints before retiring old files, makes backup copies under `~/.codex/routing-v6.0-backups/`, and does not rewrite `config.toml`. It blocks edited old Skills/presets; manually inspect them and only if intentional use `--archive-modified-legacy` to archive with backup. The old v4 migration still uses `--upgrade-v4 --archive-v4-agents`. Both migrations are explicit, never the default fresh install.

The routing addendum retains the `codex-universal-routing:v5` markers for safe in-place policy updates. This is a **marker format**, not an obsolete Skill name.

Update any personal prompts that use the old `$codex-hybrid-orchestrate` invocation to `$codex-universal-orchestrate`. Arbitrary user-owned files are not silently rewritten.

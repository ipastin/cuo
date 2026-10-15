---
title: "Universal Orchestration v6 Offline Validation Report"
created: "11-10-26 18-23-01"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "validated-offline"
commit: "test(codex): validate v6 offline reliability and migration"
---

# Offline Validation Report — v6.0.0

## Result

**60 / 60 offline tests PASSED** (`python3 -m unittest discover -s tests -v`). No network requests, model calls, API credits or Codex Pro allowance used.

### Covered

- Configuration TOML parsing; unique agent names, correct new Skill metadata and user-requested Markdown naming/version metadata.
- Default fallback is Sol Medium, not implicit Luna for unknown subtask; five `cuo-*` presets pin their own models.
- Four structurally valid example plans (simple deterministic, research, engineering, cross-domain).
- DAG validation: unknown edges, self/cyclic dependencies, duplicate tasks.
- Parallel ownership: conflicts between independent writers, safe sequential writes, read-only agent write rejection, traversal path rejection.
- Skill handoff: syntax, required vs optional conflict, prevention of orchestration Skill recursion into child threads.
- High-impact and external mutation approval declarations; worktree opt-in gates.
- Installer: dry-run, idempotency, existing config preservation, explicit v4 and v5 naming migration/backups, modified legacy preflight, AGENTS.override, and project-scope install.
- Local Skill inventory duplicate detection and malformed header warnings.
- Optional worktree launcher safe path validation.
- Adaptive Triage, Skill Eligibility, Verification Contract, minimal privacy-filtered Execution Trace.
- Breaking ID rename verified in both SKILL.md and agent TOML; v5.0 legacy fixture migrated with backups.
- CLI scripts are standalone offline tools: none launches a model or runs external API routing.

## Not tested / no claims made

- Signed-in ChatGPT Pro account entitlement to Astra, Luna, Sol, or Terra.
- Actual Codex thread spawning, child model/routing selection, live reasoning-effort support in the installed version.
- Whether an assigned Skill was truly selected, loaded and followed by any real model.
- Correctness of open-ended UX/research/engineering/business outcomes or objective savings in Pro usage.
- Actual CLI worktree `--run`, external tools, Figma writes or project integration.
- Runtime sandboxing/human approvals. `human_gate=true` in plan JSON expresses a *required policy*, not automatic authorization enforcement.

## Acceptance steps on user's machine

1. Dry-run installer; review diffs and possible v4/v5 legacy names.
2. Apply install/migration explicitly; merge relevant TOML keys preserving MCP and unrelated settings.
3. Confirm actual model access (`/model`), custom agents (`/agent`) and Skills (`/skills` or `$`).
4. Run a read-only 2-subagent task and inspect each worker's actual model + skills_used.
5. Run one simple task to ensure no unnecessary delegation and one cross-domain task with different quality criteria.
6. Compare at least 30 representative tasks to Sol-alone baseline using the evaluation guide. Mark unavailable tools and missing Skills rather than guessing.

## Source documentation

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/non-interactive-mode


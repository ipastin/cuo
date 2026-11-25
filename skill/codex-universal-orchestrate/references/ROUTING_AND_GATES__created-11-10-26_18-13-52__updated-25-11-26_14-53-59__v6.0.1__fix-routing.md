---
title: "Adaptive Routing and Quality Gates"
created: "11-10-26 18-13-52"
updated: "25-11-26 14-53-59"
version: "6.0.1"
status: "proposed"
commit: "fix(routing): select GPT-6.2 models by task"
---

# Routing & Quality Gates

## Dispatch

| Condition | Preferred execution | Preset/model |
| --- | --- | --- |
| Calculation, validation or formatting with an existing tool | Run the tool directly | none |
| Small request or work tightly coupled to the current chat | Main | User's current model and effort |
| Find source files, extract facts or inventory states | Bounded discovery | `cuo-scout` / `gpt-6-luna` high |
| Compare design alternatives or explain conflicting observations | Synthesis | `cuo-analyst` / `gpt-6.2-sol` high |
| Implement an agreed change with an owned scope and acceptance criteria | Bounded execution | `cuo-executor` / `gpt-6.2-sol` medium |
| Check an artifact against a rubric, including failure cases | Independent review | `cuo-reviewer` / `gpt-6.2-sol` high |
| A material uncertainty could change a costly, hard-to-reverse decision | Independent advice on that decision | `cuo-expert` / `gpt-6.2-astra` high |
| Terra | A/B candidate only | `cuo-terra-candidate` is not installed |

## Necessary preconditions for delegation

At least one: true independence, material context-isolation benefit, parallel wall-time savings, or independent review of meaningful risk. Otherwise do work in main. Strongly prefer fewer better-scoped agents.

## DAG/ownership

- All dependencies explicit; no cycles, no tasks lacking their prerequisite results.
- Concurrent writes to the same files are prohibited. A file-scoped ownership policy is a *soft agent instruction*: actual Codex sandbox and user approvals govern real permission.
- Write scopes apply to local file artifacts only. Shared Figma, Docs, production APIs and other external resources require separate collision controls and authorization; Git worktrees do not isolate them.
- Cross-cutting contracts or source-of-truth changes should be made or approved centrally before dependent execution.
- Separate worktree CLI sessions are optional and require explicit user request/authorization; no automatic merge/deploy/cleanup.

## Gate sequence

G0: Inputs / permission and privacy scope clear. G1: Task-level criteria defined. G2: Dependencies and capabilities resolved. G3: Scope-compliant results or explicit blockers. G4: Domain-appropriate objective verification. G5: Findings resolved / exceptions labeled. G6: Human approvals obtained before irreversible/external changes.

## Routing failure modes

- Model unavailable: surface limitation; use an *available, authorized* alternative only if allowed. Never default to API key or silently weaken privacy conditions.
- Skill unavailable: search via actual Codex catalog; then report missing and propose direct execution or suitable existing alternative. Never invent activation.
- Conflicting agent conclusions: compare evidence and scope. Main resolves; Astra only if consequential uncertainty remains.
- Test/check can't run: mark **not run** with blocker.
- Missing source data: label unknown; do not replace with guesses.
- Subagent runtime permission overrides may differ from profile defaults. Confirm active permission mode before risky steps.

## Model choices

For example, a reviewer can check a migration against its rollback criteria. If two credible sources disagree about whether rollback can recover existing records, give the expert that question and both sources. Ask the user for any missing business requirement before acting on the advice.

Adaptive Triage chooses an execution mode and whether a bounded child task benefits from a preset. A child agent's configured model applies to that child; it does not change the model of the running main chat or current turn. The Codex runtime selects the main chat's model. Check the active client's capabilities before describing a model choice for a future chat. Where native chat creation supports a model option, set it only when the user explicitly requested that specific model; otherwise use the user's configured default. If a model cannot be selected or verified, state that limitation rather than promising a switch.

The kit's config fragment proposes Sol 6.2 medium for unnamed children. An existing installation uses its active Codex settings. Select a named preset when the choice matters. Where a full-history fork inherits the parent's model and effort, use `fork_turns="none"` and include the goal, evidence, permissions and acceptance criteria in the handoff.

Check the signed-in client's model picker or App Server `model/list` for the model ID and supported effort. An actual child run verifies dispatch. Compare accepted outcomes and Pro usage on representative tasks before changing a role for a future model release.

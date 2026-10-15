---
title: "Skill Selection and Handoff Policy"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Skill Selection & Execution Policy

## Responsibility boundary

**Main Sol** owns task outcome, planning and capability-to-Skill matching using *visible metadata*. The **executing agent** (which may be main Sol) owns loading `SKILL.md`, selecting relevant references/scripts and applying the method. Final verification belongs to main Sol.

1. Discover names/descriptions visible to *the current Codex environment*. Do not assume a Skill visible in ChatGPT UI is installed in CLI/IDE, or vice versa.
2. Assign **exact, currently verified Skill names** in `skills.required`; these are handoff obligations. If none are available or appropriate, use `[]` and execute normally.
3. Put eligible alternatives in `skills.optional` only after checking availability; any tool-specific prerequisites remain in force.
4. Use `skills.discovery_hint` to express needed capabilities when exact Skills are not yet known. **Hints are not invocations.**
5. Do not assign the global `$codex-universal-orchestrate` orchestration Skill as a task-level required Skill for a child. In a delegated agent, explicitly load and follow the required *task-level* Skill instructions. Parent must not copy the entire contents into handoff. Parent-loaded Skill content is not guaranteed to transfer to child context.
6. The child may invoke extra installed Skills within its assigned scope but may not widen permissions, modify unrelated resources or bypass approval.
7. Each worker returns `skills_used`, `skills_unavailable` and whether key checks ran. Parent reports missing mandatory Skills rather than pretending compliance.
8. Local path inventory is advisory only: Codex plugins and built-in Skills may not appear in its filesystem scan. Verify actual Skills through Codex `/skills` or `$` suggestions.

## Skill selection independence

A Skill defines **method**; a preset defines **agent execution behavior**; a model controls **reasoning resources**; MCP/CLI/Figma/etc. defines **tool access**. None implies the others automatically.

## Hand-off snippet

```text
TASK_ID / GOAL / SCOPE / INPUT REFERENCES / DEPENDENCIES (completed)
REQUIRED_SKILLS: exact names, or none
OPTIONAL_SKILLS: exact names, or none
DISCOVERY_HINTS: capabilities, not invented skill IDs
EXECUTOR + MODEL: resolved preset / actual availability
WRITE SCOPE / TOOL PERMISSIONS / HUMAN APPROVALS
ACCEPTANCE CRITERIA / EXPECTED ARTIFACT(S)
RETURN: status, artifact refs, evidence, skills_used, skills_unavailable,
        checks, limitations, changed paths or external actions
```

Do not claim a Skill was invoked solely because its name was mentioned. Runtime behavior is model-driven; confirmation requires reading the thread and inspecting actual deliverables.

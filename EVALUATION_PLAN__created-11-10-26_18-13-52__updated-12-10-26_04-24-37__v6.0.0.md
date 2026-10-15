---
title: "Universal Orchestration Eval Protocol"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Evaluation Protocol for Codex Universal Orchestration

## Offline != model evaluation

`unittest` validates TOML structure, plan graph, ownership, installer and helpers. It does **not** measure whether Sol selected correct Skills or Luna actually followed them. Live tests require a signed-in user's Codex client and count against the user's Pro allowance.

## Pilot design

Compare three variants on 30 representative tasks (suggested):

A. Sol alone, normal project instructions.
B. v4 Engineering-first routing (baseline comparison only, if available).
C. v5 Universal routing.

Balance simple, research, UX, engineering, business, strategy, documents, and cross-domain workflows. Avoid cherry-picking only cases with high parallelism.

For each case, human annotator (user) labels:
- expected deliverable(s) and hard constraints;
- which existing Skills are relevant/available;
- expected dependency edges, expected approvals and allowable parallelism;
- evaluation rubric / evidence references.

## Metrics

- Goal & constraint adherence, pass/fail with reasons.
- Skill selection precision/recall against actual installed Skills.
- Dependency violation count, concurrent mutable-resource overlap count.
- Unnecessary agent launches / Pro usage / latency when visible.
- Evidence traceability, fabricated citations or tools, unrun-check disclosures.
- User rework time and quality of accepted deliverable.
- Human approval policy compliance (target 100%).

**Accept v5 only if it beats Sol-alone baseline on significant multi-stage tasks without harming simple tasks.** No benchmark score is claimed before live evaluation.

## Reference cases

The `evals/eval_cases.json` file contains scenario descriptions and expected capabilities/human gates. These are *human-authored labels*, not proof of runtime behavior.

## v6.0 live evaluation addendum

For each representative task compare vanilla Sol versus `$codex-universal-orchestrate` at equal starting permissions, context and model access. Record: triage mode correctness; unnecessary subagent launches; required Skill eligibility; accepted deliverable quality; independent verifier findings; human rework; actual usage/latency if exposed by Codex. Do **not** score JSON schema passing as UX or implementation success.

Use `triage_check.py`, `skill_eligibility.py`, `verify_result.py` and optional `trace_record.py` as **evidence aids only**. Before promoting policy changes, inspect at least 10 single-domain and 10 cross-domain task runs plus adverse conditions.

---
title: "Verification Contract & Minimal Execution Trace"
created: "12-10-26 04-21-24"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "feat(codex): add outcome contracts and privacy-conscious traces"
---

# Verification Contract & Minimal Execution Trace

Verification is distinct from policy compliance. Every significant deliverable needs an appropriate method:

1. **Process:** selected Skills, tools, permissions and human gates were observed.
2. **Artifact:** the deliverable exists and meets format, coverage and structural requirements.
3. **Outcome:** the deliverable addresses the original user goal; use domain-specific evidence, independent review or human judgment where necessary.

No universal self-assigned quality score. A passing local JSON validator does **not** verify whether claims are true, sources genuine, or UX good. For research use provenance/contradictions; for UX use flow/state coverage and design-owner approval; for code use tests/runtime checks; for strategy use assumptions and sensitivity.

For substantial work, a bounded verification report uses `examples/verification/ux-review.json` shape. Run `python3 scripts/verify_result.py <file>` to check structural consistency, evidence references for `pass`, and approval status. `needs_review` is a valid outcome, not a failure to report.

### Minimal Execution Trace

Opt-in `scripts/trace_record.py`: only `run_id`, `task_id`, `mode`, `agent`, `model`, `skills_selected`, `skills_reported`, `verification_status`, `attempt` and `timestamp_utc`. Extra fields, including any prompts/PHI/tool outputs, are **excluded** from stored output. File permissions begin at 0600. Do not store sensitive data even in permitted identifier fields.

```bash
python3 scripts/trace_record.py examples/trace/event.json --out ./cuo-trace.jsonl
python3 scripts/trace_record.py examples/trace/event.json --out ./cuo-trace.jsonl --apply
```

Never claim real model/Skill execution from an agent self-report alone. Compare with actual Codex threads or logs where available. No hooks are enabled by default; installing unreviewed hooks would expand execution privileges and privacy risk.

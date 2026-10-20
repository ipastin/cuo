<!--
created: "15-10-26 08-52-37"
updated: "20-10-26 17-38-40"
version: "6.0.0"
commit: "docs(readme): explain adoption, routing, and verification"
-->

# Codex Universal Orchestrator (CUO)

CUO helps Codex turn substantial tasks into verifiable results: reuse installed Skills, delegate independent work when it helps, and check the evidence before calling a task complete.

It is a local kit for Codex clients using **ChatGPT Pro sign-in**, with one orchestration Skill, five agent presets, and offline validation tools. Use it for engineering, design, research, writing, business analysis, or work spanning several of these.

- **Keep small tasks small.** Handle clear, bounded work directly; use tools without an LLM when practical.
- **Delegate with a reason.** Give each independent subtask its own inputs, Skills, write scope, and acceptance criteria.
- **Keep responsibility in the main chat.** Integrate results and distinguish a valid artifact from a successful outcome.

**Status:** Kit v6.0.0; source policies are marked `proposed`. Offline checks are included; a quality or usage advantage over a single-agent baseline has not been established. See [verification and limits](#verification-and-limits).

## Quickstart

You need **Python 3.11+**, Git, and a local Codex client signed in with ChatGPT Pro. Model and custom-agent availability depend on your account and client. The Python tools use the standard library; no additional Python packages are needed.

For an existing installation, see [updates and migration](#updates-and-migration). For a new installation:

**1. Clone the kit and preview the installation.**

```bash
git clone https://github.com/ipastin/cuo.git
cd cuo
python3 scripts/install.py
```

The installer prints `Codex Universal Orchestration v6.0.0 | DRY-RUN | global scope` and proposed changes. This command writes no installation files.

**2. Review the plan, then apply it.**

```bash
python3 scripts/install.py --apply
```

The default global installation manages these locations:

| Location | Change |
| --- | --- |
| `~/.agents/skills/codex-universal-orchestrate/` | Installs the orchestration Skill and its references. |
| `~/.codex/agents/cuo-*.toml` | Installs five agent presets. |
| `~/.codex/AGENTS.md` | Adds or updates a marked routing-policy block; backs up an existing file before changing it. |
| `~/.codex/config.toml` | Creates a config if absent. An existing config is preserved; differing settings produce `routing-v6.0.fragment.toml` for manual merging. |

Review a generated config fragment before proceeding: merge the needed settings without duplicating `[agents]` or removing your other configuration. See the [installation guide](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) for project scope and `AGENTS.override.md` handling.

<details>
<summary>Custom Codex directory</summary>

`CODEX_HOME`, if set, replaces `~/.codex` for config, agents, instructions, and backups. The global Skill stays under `~/.agents/skills/`.

</details>

**3. Confirm the Skill is available in Codex, then give it a task.**

In clients with slash commands, check `/skills` for `codex-universal-orchestrate`, `/model` for model availability, and `/agent` to inspect child agents. Other clients may expose these through their UI. Discovery is a setup check; it does not prove that a Skill was used in a run.

## Use in Codex

Include the task's source material and expected result. For example, in an existing frontend repository:

```text
$codex-universal-orchestrate
Review this repository's checkout flow for accessibility issues.
Use the current source and installed Skills. Return prioritized findings
with file references, user impact, and suggested fixes. Keep this read-only.
Delegate only if an independent subtask benefits from it.
```

The expected response is a source-backed review with prioritized findings and a clear account of checks performed and checks not run. If essential inputs are missing, CUO should request them before delegating. A small review may stay entirely in the main chat; launching agents is not a success criterion.

For a shorter writing task, the same Skill can work directly:

```text
$codex-universal-orchestrate
Rewrite this sentence in plain English, preserving its meaning:
"The implementation facilitates the utilization of existing capabilities."
```

Task-specific expertise comes from the Skills available in your environment. CUO provides the coordination policy; it does not bundle accessibility, design, research, or other domain Skills.

## How work is routed

CUO assesses scope, dependencies, risk, permissions, and the benefit of delegation before choosing direct work or bounded subtasks. Each child loads its own required Skills. Children do not recursively orchestrate more agents.

The included presets define these model preferences:

| Preset | Responsibility | Model / effort |
| --- | --- | --- |
| `cuo-scout` | Bounded discovery, extraction, inventory, and source mapping | `gpt-6-luna` / high |
| `cuo-analyst` | Analytical, conceptual, or architecture reasoning | `gpt-6.1-sol` / high |
| `cuo-executor` | Approved implementation within an exclusive write scope | `gpt-6.1-sol` / medium |
| `cuo-reviewer` | Independent review against task-specific acceptance criteria | `gpt-6.1-sol` / high |
| `cuo-expert` | Advice on consequential uncertainty or conflicting evidence | `gpt-6-astra` / low |

The [config fragment](config-fragment.toml) proposes Sol Medium for the main model and unnamed children, with a concurrency cap of five. The cap is not a target. Presets do not switch the model of an already running main chat; actual model selection and permissions must be checked in the active runtime. The optional Terra candidate is not installed by default.

### Continuing here or opening another chat

Related fixes, review, and merge checks stay with their current PR and decisions. For a substantial independent stage, explicit permission to create a chat—including standing permission—allows CUO to check for a suitable existing chat in the same turn, then create one if none exists. This applies even when enough context remains. An incomplete chat list must be disclosed; a plausible duplicate requires clarification before creation.

Creating a chat requires client support. A handoff should carry the stage's goal, source references, permissions, and acceptance criteria. When reliable remaining-context telemetry is unavailable, capacity is `unknown`; CUO must not infer a percentage from transcript length, token usage, or context-tool statistics. See [Adaptive Triage](skill/codex-universal-orchestrate/references/ADAPTIVE_TRIAGE__created-12-10-26_04-21-24__updated-20-10-26_15-28-55__v6.0.0.md).

## Updates and migration

From a clean checkout, fetch the latest kit with `git pull --ff-only`, then preview the installer. An unchanged v6 installation is skipped. If installed managed files differ, the installer stops; review your local customizations before replacing them:

```bash
python3 scripts/install.py --replace-managed
python3 scripts/install.py --replace-managed --apply
```

The first command previews replacement; the second replaces differing managed Skills and presets with backups under `~/.codex/routing-v6.0-backups/`. Existing `config.toml` settings still require a manual merge when they differ.

<details>
<summary>Migrating from v4 or v5</summary>

Version 6 renamed `codex-hybrid-orchestrate` to `codex-universal-orchestrate` and `orch_*` presets to `cuo-*`. For a v5 installation:

```bash
python3 scripts/install.py --upgrade-v5
python3 scripts/install.py --upgrade-v5 --apply
```

The installer checks known v5 fingerprints and backs up legacy files before retiring them. Edited or unrecognized legacy files block the default migration. Follow the [migration guide](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) for v4, modified installations, and rollback.

</details>

## Verification and limits

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_plan.py examples/plans/cross-domain.json
```

The example prints `VALID STRUCTURE: 4 tasks, 3 deliverables`, dependency waves, and a structural-validation warning. JSON task plans are optional inspectable artifacts; they are not a native orchestration API.

| Evidence | What it establishes |
| --- | --- |
| Tests and offline validators | Configuration parsing, installer behavior, plan dependencies, declared write conflicts, and declared approval gates. They do not enforce permissions in a live client. |
| [MANIFEST.json](MANIFEST.json) | SHA-256 hashes for listed Kit files. Its scope excludes this repository README and `LICENSE`. |
| [Input-sufficiency cases](evals/triage_needs_input.json) | Expected `needs_input` labels for E01, E07, and E12, and a maximum of zero delegated launches. These labels do not establish task execution or outcome quality. |
| [Evaluation protocol](EVALUATION_PLAN__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) | A method for comparison with a single-agent baseline; it is not a published benchmark result. |

Runtime evidence is still needed to establish model availability, actual Skill use, delegation behavior, and result quality. CUO does not install or require lifecycle hooks. Its non-content Execution Trace is opt-in. The standard installation makes no API calls and does not configure API keys or product-runtime routing. Optional worktree execution requires explicit authorization.

## Documentation

- [Original Kit README](README__created-11-10-26_18-13-52__updated-20-10-26_15-28-55__v6.0.0.md) — capabilities, files, and routing defaults.
- [Installation and migration](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — v4/v5 upgrades, project scope, and rollback.
- [Architecture](ARCHITECTURE__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — roles and task flow.
- [Task contract template](TASK_CONTRACT_TEMPLATE__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — bounded agent handoffs.
- [Verification contract](skill/codex-universal-orchestrate/references/VERIFICATION_TRACE__created-12-10-26_04-21-24__updated-12-10-26_04-24-37__v6.0.0.md) — process, artifact, and outcome evidence.

## Contributing and support

Use [GitHub Issues](https://github.com/ipastin/cuo/issues) for reproducible bugs and documentation gaps, or open a pull request with a focused change. Include the relevant command, Python version, client, expected behavior, and actual behavior; remove secrets and private task content. Before submitting, run the checks above. If you change a file listed in `MANIFEST.json`, update its hash and keep renamed documentation links consistent.

## License

[MIT](LICENSE) © 2026 Igor Pastin. CUO is an independent project for Codex and is not affiliated with OpenAI.

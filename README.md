<!--
created: "15-10-26 08-52-37"
updated: "16-10-26 09-09-10"
version: "6.0.0"
commit: "docs(codex): account for context capacity in triage"
-->

# Codex Universal Orchestrator (CUO)

CUO is a local orchestration kit for Codex. It provides a Skill, five agent presets, and validation tools for breaking work into verifiable tasks, reusing installed Skills, and delegating only when a subtask benefits from it.

**Status:** Kit v6.0.0 is marked `proposed` in its [source documentation](README__created-11-10-26_18-13-52__updated-16-10-26_09-09-10__v6.0.0.md). The included validators check structure; they cannot prove that a model is available to your account or that an orchestration run succeeded.

CUO is for local Codex clients signed in with ChatGPT Pro. It does not configure product runtime model routing, API keys, or an external orchestration service.

## Quickstart

You need **Python 3.11+**, Git, and a Codex installation signed in with ChatGPT. If you have an existing v4/v5 CUO installation, go to [Existing installations](#existing-installations) instead. For a new installation, start from a terminal:

```bash
git clone https://github.com/ipastin/cuo.git
cd cuo
python3 scripts/install.py
```

The last command prints a **dry-run** plan; it does not install anything. Review its proposed changes before applying them. If this is your first CUO installation, run:

```bash
python3 scripts/install.py --apply
```

The installer adds the `codex-universal-orchestrate` Skill and `cuo-*` agent presets. If `~/.codex/config.toml` already exists, the installer leaves it intact and writes a fragment for manual merging. It does not start a Codex session or use an API key. See [installation and migration](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) before changing an existing setup.

## Use in Codex

Check that the Skill appears in `/skills`, then invoke it with a real task. For example:

```text
$codex-universal-orchestrate — break this task into verifiable deliverables, reuse installed Skills, delegate only independent work that benefits from it, and check the results.
```

Use `/agent` to inspect child agents and `/model` to check model availability. Agent configuration is guidance, not proof of the model or Skill that ran. The main thread remains responsible for integration and verification.

## Existing installations

Version 6 renamed the earlier `codex-hybrid-orchestrate` Skill to `codex-universal-orchestrate` and the `orch_*` presets to `cuo-*`. An existing v5 installation needs an explicit migration:

```bash
python3 scripts/install.py --upgrade-v5
python3 scripts/install.py --upgrade-v5 --apply
```

Run the first command to review the migration. The installer checks known v5 file fingerprints and makes backups before retiring them; it stops if legacy files were edited. For v4 installations, project-scoped setup, and rollback, follow the [migration guide](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md).

## Validate the Kit

From the repository root, run the included tests and validate an example plan:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_plan.py examples/plans/cross-domain.json
```

The validators check plan structure, dependency references, write conflicts, and approval gates. They do not launch agents or validate live runtime behavior. The 49 files listed in [MANIFEST.json](MANIFEST.json) match their SHA-256 hashes in this checkout. To support the conventional `README.md` name, the Markdown metadata test and its manifest hash were updated; the remaining Kit files retain their imported content. The manifest covers Kit files, not the additional repository README and license files.

## Read more

- [Original Kit README](README__created-11-10-26_18-13-52__updated-16-10-26_09-09-10__v6.0.0.md) — capabilities, files, and routing defaults.
- [Installation and migration](INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — v4/v5 upgrades, project scope, and rollback.
- [Architecture](ARCHITECTURE__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — roles and task flow.
- [Task contract template](TASK_CONTRACT_TEMPLATE__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md) — bounded agent handoffs.
- [Verification contract](skill/codex-universal-orchestrate/references/VERIFICATION_TRACE__created-12-10-26_04-21-24__updated-12-10-26_04-24-37__v6.0.0.md) — process, artifact, and outcome evidence.

## License

[MIT](LICENSE) © 2026 Igor Pastin. CUO is an independent project for Codex and is not affiliated with OpenAI.

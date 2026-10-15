"""Offline regression suite. No internet, authentication, model calls, or API usage."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

PLAN = module("validate_plan", ROOT / "scripts/validate_plan.py")
INVENTORY = module("skills_inventory", ROOT / "scripts/skills_inventory.py")
LEGACY = module("worktree_lanes", ROOT / "optional/scripts/worktree_lanes.py")


def example(name):
    return json.loads((ROOT / "examples/plans" / name).read_text(encoding="utf-8"))


class ConfigurationTests(unittest.TestCase):
    def test_toml_valid(self):
        paths = [ROOT/"config-fragment.toml", *sorted((ROOT/"agents").glob("*.toml")), ROOT/"optional/cuo-terra-candidate.toml"]
        for p in paths:
            with self.subTest(file=p.name):
                d = tomllib.loads(p.read_text(encoding="utf-8"))
                if p.name != "config-fragment.toml":
                    for k in ("name", "description", "model", "model_reasoning_effort", "developer_instructions"):
                        self.assertIn(k, d)

    def test_unnamed_subagent_has_safe_generalist_fallback(self):
        d=tomllib.loads((ROOT/"config-fragment.toml").read_text(encoding="utf-8"))
        self.assertEqual(d["agents"]["default_subagent_model"],"gpt-6.1-sol")
        self.assertEqual(d["agents"]["default_subagent_reasoning_effort"],"medium")

    def test_agent_unique_names_and_no_builtin_shadow(self):
        vals = [tomllib.loads(p.read_text(encoding="utf-8"))["name"] for p in (ROOT/"agents").glob("*.toml")]
        self.assertEqual(len(vals),len(set(vals)))
        self.assertFalse(set(vals) & {"explorer", "worker", "default"})
        self.assertTrue(all(v.startswith("cuo-") for v in vals))

    def test_skill_compatibility_name_and_metadata(self):
        txt = (ROOT/"skill/codex-universal-orchestrate/SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(txt, r"(?m)^name: codex-universal-orchestrate$")
        for k in ("description", "created", "updated", "version", "commit"):
            self.assertRegex(txt, f"(?m)^{k}:")
        self.assertIn('version: "6.0.0"',txt)

    def test_md_artifact_metadata_and_filename(self):
        for p in ROOT.rglob("*.md"):
            text = p.read_text(encoding="utf-8")
            with self.subTest(file=p.name):
                self.assertTrue(text.startswith("---\n"))
                for k in ("created", "updated", "version"):
                    self.assertRegex(text, f"(?m)^{k}:")
                if p.name != "SKILL.md":
                    self.assertRegex(p.name, r"__created-\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}__updated-\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}__v6\.0\.0\.md$")

    def test_only_one_orchestrator_skill(self):
        skills=list((ROOT/"skill").rglob("SKILL.md"))
        self.assertEqual(len(skills),1)


class PlanTests(unittest.TestCase):
    def test_examples_validate(self):
        for p in (ROOT/"examples/plans").glob("*.json"):
            with self.subTest(file=p.name):
                self.assertGreater(PLAN.validate(example(p.name))["task_count"],0)

    def test_dependency_cycle_rejected(self):
        p=example("cross-domain.json")
        p["tasks"][0]["depends_on"]=["T4"]
        with self.assertRaisesRegex(ValueError,"cycle"):
            PLAN.validate(p)

    def test_unknown_dependency_rejected(self):
        p=example("research.json")
        p["tasks"][1]["depends_on"]=["THERE_IS_NO_TASK"]
        with self.assertRaisesRegex(ValueError,"Unknown dependencies"):
            PLAN.validate(p)

    def test_duplicate_task_rejected(self):
        p=example("research.json")
        p["tasks"][1]["id"]="T1"
        with self.assertRaisesRegex(ValueError,"duplicate"):
            PLAN.validate(p)

    def test_conflicting_parallel_writes_rejected(self):
        p=example("engineering.json")
        p["tasks"][2]["depends_on"]=[]
        p["tasks"][2]["executor"]={"mode":"subagent","agent":"cuo-executor","model":"gpt-6.1-sol","effort":"medium"}
        p["tasks"][2]["write_scopes"]=["src/components/"]
        with self.assertRaisesRegex(ValueError,"write-scope conflict"):
            PLAN.validate(p)

    def test_serialized_writes_allowed(self):
        p=example("engineering.json")
        p["tasks"][2]["executor"]={"mode":"subagent","agent":"cuo-executor","model":"gpt-6.1-sol","effort":"medium"}
        p["tasks"][2]["write_scopes"]=["src/components/"]
        self.assertEqual(PLAN.validate(p)["task_count"],3)

    def test_readonly_scout_cannot_write(self):
        p=example("research.json")
        p["tasks"][0]["write_scopes"]=["report.md"]
        with self.assertRaisesRegex(ValueError,"read-only"):
            PLAN.validate(p)

    def test_model_profile_mismatch_rejected(self):
        p=example("research.json")
        p["tasks"][0]["executor"]["model"]="gpt-6.1-sol"
        with self.assertRaisesRegex(ValueError,"preset pins"):
            PLAN.validate(p)

    def test_skill_name_identifier_rejected(self):
        p=example("research.json")
        p["tasks"][0]["skills"]["required"]=["invented vague UX skill"]
        with self.assertRaisesRegex(ValueError,"exact identifiers"):
            PLAN.validate(p)

    def test_orchestration_skill_cannot_be_delegated_to_child(self):
        p=example("research.json")
        p["tasks"][0]["skills"]["required"]=["codex-universal-orchestrate"]
        with self.assertRaisesRegex(ValueError,"main-thread only"):
            PLAN.validate(p)

    def test_required_optional_overlap_rejected(self):
        p=example("research.json")
        p["tasks"][0]["skills"]["required"]=["actual-skill"]
        p["tasks"][0]["skills"]["optional"]=["actual-skill"]
        with self.assertRaisesRegex(ValueError,"overlap"):
            PLAN.validate(p)

    def test_external_write_gate_required(self):
        p=example("research.json")
        p["tasks"][0]["permissions"]["external_write"]=True
        with self.assertRaisesRegex(ValueError,"approval gate"):
            PLAN.validate(p)

    def test_irreversible_gate_required(self):
        p=example("research.json")
        p["tasks"][0]["permissions"]["irreversible"]=True
        with self.assertRaisesRegex(ValueError,"approval gate"):
            PLAN.validate(p)

    def test_critical_gate_required(self):
        p=example("research.json")
        p["tasks"][0]["risk"]="critical"
        with self.assertRaisesRegex(ValueError,"approval gate"):
            PLAN.validate(p)

    def test_worktree_gate_and_flag_required(self):
        p=example("research.json")
        p["tasks"][0]["executor"]={"mode":"worktree","agent":None,"model":"gpt-6.1-sol","effort":"medium"}
        with self.assertRaisesRegex(ValueError,"worktrees_enabled"):
            PLAN.validate(p)
        p["execution_policy"]["worktrees_enabled"]=True
        with self.assertRaisesRegex(ValueError,"approval gate"):
            PLAN.validate(p)
        p["tasks"][0]["permissions"]["human_gate"]=True
        self.assertEqual(PLAN.validate(p)["task_count"],2)

    def test_tool_only_must_not_call_model(self):
        p=example("simple-deterministic.json")
        p["tasks"][0]["executor"]["model"]="gpt-6-luna"
        with self.assertRaisesRegex(ValueError,"null agent/model/effort"):
            PLAN.validate(p)

    def test_scope_traversal_rejected(self):
        p=example("engineering.json")
        p["tasks"][1]["write_scopes"]=["../private/"]
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            PLAN.validate(p)

    def test_scope_file_vs_parent_dir_overlaps(self):
        self.assertTrue(PLAN.overlaps("docs/brief.md", "docs"))
        self.assertFalse(PLAN.overlaps("docs/a", "docs/b"))

    def test_eval_cases_are_diverse(self):
        cases=json.loads((ROOT/"evals/eval_cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases),12)
        self.assertGreaterEqual(len({c["domain"] for c in cases}),8)


class SkillInventoryTests(unittest.TestCase):
    def test_skill_inventory_duplicate_name(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            home=td/"home"
            s1=home/".agents"/"skills"/"one"/"SKILL.md"
            s2=td/"extra"/"two"/"SKILL.md"
            for s in (s1,s2):
                s.parent.mkdir(parents=True)
                s.write_text('---\nname: sample-skill\ndescription: Analyze samples\n---\nHello\n')
            data=INVENTORY.inventory(extra_roots=[td/"extra"],home=home)
            self.assertEqual(len(data["skills"]),2)
            self.assertIn("sample-skill",data["duplicate_names"])

    def test_skill_inventory_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"SKILL.md"
            p.write_text("Nothing")
            self.assertIn("missing YAML frontmatter", INVENTORY.skill_info(p)["issues"])


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)/"home"
        self.home.mkdir()
        self.codex=self.home/".codex"
        self.env={**os.environ,"HOME":str(self.home),"CODEX_HOME":str(self.codex)}
        self.script=str(ROOT/"scripts/install.py")

    def install(self,*args):
        return subprocess.run([sys.executable,self.script,*args],env=self.env,capture_output=True,text=True)

    def test_default_dryrun_no_files(self):
        r=self.install()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse(self.codex.exists())
        self.assertFalse((self.home/".agents").exists())

    def test_new_install_idempotent(self):
        r=self.install("--apply")
        self.assertEqual(r.returncode,0,r.stderr)
        orig=(self.codex/"AGENTS.md").read_bytes()
        r=self.install("--apply")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(orig,(self.codex/"AGENTS.md").read_bytes())
        self.assertTrue((self.home/".agents/skills/codex-universal-orchestrate/SKILL.md").exists())
        self.assertEqual(len(list((self.codex/"agents").glob("cuo-*.toml"))),5)

    def test_preserve_unrelated_existing_config(self):
        self.codex.mkdir()
        existing='model = "gpt-5.6-terra"\n[mcp_servers.foo]\nurl = "https://example.test/mcp"\n'
        (self.codex/"config.toml").write_text(existing)
        r=self.install("--apply")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((self.codex/"config.toml").read_text(),existing)
        self.assertTrue((self.codex/"routing-v6.0.fragment.toml").exists())

    def test_upgrade_v4_requires_flag(self):
        self.codex.mkdir()
        old=f"header\n\n<!-- codex-hybrid-routing:v4 BEGIN -->\nold\n<!-- codex-hybrid-routing:v4 END -->\n"
        (self.codex/"AGENTS.md").write_text(old)
        r=self.install("--apply")
        self.assertNotEqual(r.returncode,0)
        self.assertEqual(old,(self.codex/"AGENTS.md").read_text())
        self.assertFalse((self.codex/"agents").exists())

    def test_explicit_v4_upgrade_backup_and_archive(self):
        self.codex.mkdir()
        (self.codex/"AGENTS.md").write_text("other instructions\n\n<!-- codex-hybrid-routing:v4 BEGIN -->\nold\n<!-- codex-hybrid-routing:v4 END -->\n")
        skill=self.home/".agents/skills/codex-hybrid-orchestrate/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: codex-hybrid-orchestrate\ndescription: v4\n---\nold\n")
        hy=self.codex/"agents/hy_repo_explorer.toml"
        hy.parent.mkdir()
        hy.write_text('name = "hy_repo_explorer"\n')
        r=self.install("--apply","--upgrade-v4","--archive-v4-agents")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("codex-universal-routing:v5",(self.codex/"AGENTS.md").read_text())
        self.assertNotIn("codex-hybrid-routing:v4",(self.codex/"AGENTS.md").read_text())
        self.assertFalse(skill.exists())
        self.assertIn('version: "6.0.0"', (self.home/".agents/skills/codex-universal-orchestrate/SKILL.md").read_text())
        self.assertFalse(hy.exists())
        self.assertGreaterEqual(len(list((self.codex/"routing-v6.0-backups").glob("*"))),3)

    def test_active_override_gate(self):
        self.codex.mkdir()
        (self.codex/"AGENTS.override.md").write_text("override preexisting\n")
        self.assertNotEqual(self.install("--apply").returncode,0)
        r=self.install("--apply","--active-override")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("codex-universal-routing:v5",(self.codex/"AGENTS.override.md").read_text())

    def test_project_scope_writes_only_scoped_dirs(self):
        project=Path(self.tmp.name)/"test_project"
        project.mkdir()
        r=self.install("--scope","project","--project",str(project),"--apply")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue((project/".agents/skills/codex-universal-orchestrate/SKILL.md").is_file())
        self.assertTrue((project/"AGENTS.md").is_file())
        self.assertFalse(self.codex.exists())


class OptionalWorktreeTests(unittest.TestCase):
    def test_v4_launcher_safe_paths(self):
        with self.assertRaises(ValueError):
            LEGACY.validated_path("../../outside")
        self.assertTrue(LEGACY.overlap("src/", "src/ui.tsx"))
        self.assertFalse(LEGACY.overlap("src/ui.tsx", "docs/readme.md"))


if __name__ == "__main__":
    unittest.main()

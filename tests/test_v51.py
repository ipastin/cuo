"""v6.0 reliability and explicit naming-migration tests (offline)."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import triage_check as TRIAGE
import skill_eligibility as ELIG
import verify_result as VERIFY
import trace_record as TRACE
import migrate_plan as MIGRATE


def example(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))


class NamingTests(unittest.TestCase):
    def test_new_skill_name_and_one_real_skill(self):
        p=ROOT/'skill/codex-universal-orchestrate/SKILL.md'
        self.assertTrue(p.is_file())
        self.assertIn('name: codex-universal-orchestrate',p.read_text())
        self.assertEqual(len(list((ROOT/'skill').rglob('SKILL.md'))),1)
        self.assertFalse((ROOT/'skill/codex-hybrid-orchestrate').exists())

    def test_presets_filenames_and_names(self):
        import tomllib
        paths=list((ROOT/'agents').glob('*.toml'))
        self.assertEqual(len(paths),5)
        for p in paths:
            name=tomllib.loads(p.read_text())['name']
            self.assertTrue(name.startswith('cuo-'))
            self.assertEqual(p.stem,name)
        self.assertFalse(list((ROOT/'agents').glob('orch_*.toml')))

    def test_all_plans_use_new_names(self):
        for p in (ROOT/'examples/plans').glob('*.json'):
            s=p.read_text()
            self.assertNotIn('orch_',s)
            self.assertNotIn('codex-hybrid-orchestrate',s)


class TriageTests(unittest.TestCase):
    def test_all_examples(self):
        for p in (ROOT/'examples/triage').glob('*.json'):
            self.assertTrue(TRIAGE.validate(json.loads(p.read_text()))['valid'])

    def test_direct_cannot_spawn(self):
        t=example('examples/triage/simple.json')
        t['proposed_subagents']=1
        with self.assertRaisesRegex(ValueError,'direct requires no'):TRIAGE.validate(t)

    def test_elevated_risk_requires_approval(self):
        t=example('examples/triage/cross-domain.json')
        t['approval_required']=False
        with self.assertRaisesRegex(ValueError,'approval_required'):TRIAGE.validate(t)

    def test_delegation_needs_benefit(self):
        t=example('examples/triage/design-review.json')
        t['delegation_benefit']=' '
        with self.assertRaisesRegex(ValueError,'delegation_benefit'):TRIAGE.validate(t)

    def test_full_orchestration_needs_dependency_rationale(self):
        t=example('examples/triage/cross-domain.json')
        t.pop('dependency_rationale')
        with self.assertRaisesRegex(ValueError,'dependency_rationale'):TRIAGE.validate(t)


class SkillEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.plan={'tasks':[{'id':'T1','skills':{'required':['my-research'],'optional':['nice-to-have']}}]}
        self.found={'skills':[{'name':'my-research','description':'Research','issues':[], 'path':'a/SKILL.md'}]}

    def test_single_match_succeeds_optional_unavailable(self):
        r=ELIG.assess(self.plan,self.found)
        self.assertTrue(r['eligible_to_attempt'])
        self.assertEqual(r['matches'][0]['status'],'available_locally')

    def test_missing_required_is_pending(self):
        r=ELIG.assess(self.plan,{'skills':[]})
        self.assertFalse(r['eligible_to_attempt'])
        self.assertEqual(r['pending'][0]['status'],'not_found_locally')

    def test_runtime_reported_is_advisory(self):
        r=ELIG.assess(self.plan,{'skills':[]},['my-research'])
        self.assertTrue(r['eligible_to_attempt'])
        self.assertEqual(r['matches'][0]['status'],'runtime_reported')

    def test_duplicate_cannot_silently_pass(self):
        found=deepcopy(self.found)
        found['skills'].append(dict(found['skills'][0],path='b/SKILL.md'))
        r=ELIG.assess(self.plan,found)
        self.assertFalse(r['eligible_to_attempt'])
        self.assertEqual(r['pending'][0]['status'],'ambiguous_duplicate')

    def test_invalid_metadata_is_pending(self):
        found=deepcopy(self.found)
        found['skills'][0]['issues']=['missing description']
        self.assertFalse(ELIG.assess(self.plan,found)['eligible_to_attempt'])


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.report=example('examples/verification/ux-review.json')

    def test_needs_review_valid(self):
        self.assertTrue(VERIFY.validate(self.report)['structurally_valid'])

    def test_accepted_requires_all_criteria(self):
        p=deepcopy(self.report);p['status']='accepted';p['human_approved']=True;p['open_issues']=[]
        with self.assertRaisesRegex(ValueError,'all criteria passed'):VERIFY.validate(p)

    def test_pass_needs_evidence(self):
        p=deepcopy(self.report);p['criteria'][0]['evidence']=[]
        with self.assertRaisesRegex(ValueError,'without evidence'):VERIFY.validate(p)

    def test_accepted_must_be_approved(self):
        p=deepcopy(self.report);p['status']='accepted';p['open_issues']=[]
        for c in p['criteria']:
            c['status']='pass';c['evidence']=['doc#ref']
        for c in p['checks']:c['status']='pass'
        with self.assertRaisesRegex(ValueError,'human approval'):VERIFY.validate(p)
        p['human_approved']=True
        self.assertTrue(VERIFY.validate(p)['structurally_valid'])

    def test_claims_are_structural_not_semantic(self):
        p=deepcopy(self.report)
        p['criteria'][0]['evidence']=['invented-url']
        self.assertIn('independently',VERIFY.validate(p)['warning'])


class TraceTests(unittest.TestCase):
    def test_extra_content_is_not_retained(self):
        p=example('examples/trace/event.json')
        d=TRACE.minimal(p)
        self.assertNotIn('prompt',d)
        self.assertIn('timestamp_utc',d)
        self.assertEqual(d['agent'],'cuo-scout')

    def test_malformed_ids_rejected(self):
        p=example('examples/trace/event.json')
        p['run_id']='PRIVATE user name and prompt!'
        with self.assertRaisesRegex(ValueError,'invalid run_id'):TRACE.minimal(p)

    def test_cli_dryrun_and_apply_file_permissions(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'trace.jsonl'
            cli=[sys.executable,str(ROOT/'scripts/trace_record.py'),str(ROOT/'examples/trace/event.json'),'--out',str(target)]
            self.assertEqual(subprocess.run(cli,capture_output=True).returncode,0)
            self.assertFalse(target.exists())
            self.assertEqual(subprocess.run([*cli,'--apply'],capture_output=True).returncode,0)
            stored=target.read_text()
            self.assertNotIn('THIS FIELD MUST NEVER BE STORED',stored)
            self.assertEqual(len(stored.splitlines()),1)
            self.assertEqual(target.stat().st_mode & 0o777,0o600)

    def test_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);a=root/'private.txt';a.write_text('do not touch');link=root/'x.jsonl';link.symlink_to(a)
            cli=[sys.executable,str(ROOT/'scripts/trace_record.py'),str(ROOT/'examples/trace/event.json'),'--out',str(link),'--apply']
            self.assertNotEqual(subprocess.run(cli,capture_output=True).returncode,0)
            self.assertEqual(a.read_text(),'do not touch')


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)/'home';self.home.mkdir()
        self.codex=self.home/'.codex'
        self.env={**os.environ,'HOME':str(self.home),'CODEX_HOME':str(self.codex)}
        self.exe=str(ROOT/'scripts/install.py')

    def call(self,*argv):
        return subprocess.run([sys.executable,self.exe,*argv],env=self.env,capture_output=True,text=True)

    def write_old(self):
        with zipfile.ZipFile(ROOT/'tests/fixtures/v5-legacy.zip') as z:
            for member in z.namelist():
                contents=z.read(member)
                if member.startswith('skill/'):
                    path=self.home/'.agents/skills'/member[len('skill/'):]
                elif member.startswith('agents/'):
                    path=self.codex/member
                else:continue
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(contents)
        self.codex.mkdir(exist_ok=True)
        (self.codex/'AGENTS.md').write_text('My instructions\n\n<!-- codex-universal-routing:v5 BEGIN -->\nOLD POLICY\n<!-- codex-universal-routing:v5 END -->\n')

    def test_v5_upgrade_optin_and_retire_names(self):
        self.write_old()
        before=(self.codex/'AGENTS.md').read_bytes()
        failed=self.call('--apply')
        self.assertNotEqual(failed.returncode,0)
        self.assertEqual((self.codex/'AGENTS.md').read_bytes(),before)
        dry=self.call('--upgrade-v5')
        self.assertEqual(dry.returncode,0,dry.stderr)
        self.assertTrue((self.home/'.agents/skills/codex-hybrid-orchestrate').exists())
        migrated=self.call('--apply','--upgrade-v5')
        self.assertEqual(migrated.returncode,0,migrated.stderr)
        self.assertFalse((self.home/'.agents/skills/codex-hybrid-orchestrate').exists())
        self.assertTrue((self.home/'.agents/skills/codex-universal-orchestrate/SKILL.md').exists())
        self.assertFalse((self.codex/'agents/orch_scout.toml').exists())
        self.assertTrue((self.codex/'agents/cuo-scout.toml').exists())
        self.assertIn('cuo-scout',(self.codex/'AGENTS.md').read_text())
        self.assertIn('My instructions',(self.codex/'AGENTS.md').read_text())
        self.assertGreaterEqual(len(list((self.codex/'routing-v6.0-backups').glob('*'))),3)
        self.assertEqual(self.call('--apply').returncode,0)  # idempotent after upgrade

    def test_modified_legacy_is_blocked_and_preserved(self):
        self.write_old()
        path=self.codex/'agents/orch_scout.toml'
        path.write_text(path.read_text()+'\n# user adjustment')
        result=self.call('--apply','--upgrade-v5')
        self.assertNotEqual(result.returncode,0)
        self.assertTrue(path.exists())
        self.assertFalse((self.codex/'agents/cuo-scout.toml').exists())
        self.assertEqual(self.call('--apply','--upgrade-v5','--archive-modified-legacy').returncode,0)
        self.assertFalse(path.exists())
        self.assertGreaterEqual(len(list((self.codex/'routing-v6.0-backups').glob('*'))),3)

    def test_plan_migration_dryrun_and_output(self):
        p=example('examples/plans/research.json')
        p['tasks'][0]['executor']['agent']='orch_scout'
        out,changes=MIGRATE.migrate(p)
        self.assertEqual(changes,1)
        self.assertEqual(out['tasks'][0]['executor']['agent'],'cuo-scout')
        self.assertEqual(p['tasks'][0]['executor']['agent'],'orch_scout')
        from validate_plan import validate
        self.assertEqual(validate(out)['task_count'],2)


if __name__=='__main__':unittest.main()

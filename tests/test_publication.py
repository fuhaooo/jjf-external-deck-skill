"""Offline safeguards. These tests do not create a GitHub repository."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'publish_github.py'

def load_module():
    if not SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location('publish_github', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.assertIsNotNone(self.mod, 'publication helper must exist')

    def test_valid_repo_identity(self):
        self.assertEqual(self.mod.repo_identity('fuhaooo', 'jjf-external-deck-skill'),
                         'fuhaooo/jjf-external-deck-skill')

    def test_invalid_repo_identity(self):
        for owner, name in [('bad/name','deck'), ('-invalid','deck'),
                            ('fuhaooo','../deck'), ('fuhaooo',''),
                            ('fuhaooo','deck; rm -rf x')]:
            with self.subTest(owner=owner,name=name):
                with self.assertRaises(ValueError):
                    self.mod.repo_identity(owner,name)

    def test_visibility_is_explicit(self):
        result = subprocess.run([sys.executable,str(SCRIPT),'--owner','fuhaooo'],
                                text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)

    def test_default_is_dry_run(self):
        result = subprocess.run([sys.executable,str(SCRIPT),'--owner','fuhaooo','--public'],
                                text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('DRY RUN',result.stdout)
        self.assertIn('--execute',result.stdout)

    def test_no_force_push_or_shell_execution(self):
        code = SCRIPT.read_text()
        self.assertNotIn('shell=True',code)
        self.assertNotIn('"--force"',code)
        self.assertNotIn("'--force'",code)
        self.assertNotIn('gh auth token',code)
        self.assertNotIn('ghp_',code)

    def test_remote_verification_matches(self):
        info = {'nameWithOwner':'fuhaooo/jjf-external-deck-skill',
                'isPrivate':False,'url':'https://github.com/fuhaooo/jjf-external-deck-skill',
                'defaultBranchRef':{'name':'main'}}
        self.mod.verify_remote(info,'fuhaooo/jjf-external-deck-skill',False,
                               'a'*40,'a'*40,'b'*40,'b'*40)

    def test_mismatched_commit_rejected(self):
        info = {'nameWithOwner':'fuhaooo/jjf-external-deck-skill',
                'isPrivate':False,'url':'https://github.com/fuhaooo/jjf-external-deck-skill',
                'defaultBranchRef':{'name':'main'}}
        with self.assertRaises(ValueError):
            self.mod.verify_remote(info,'fuhaooo/jjf-external-deck-skill',False,
                                   'a'*40,'c'*40,'b'*40,'b'*40)

    def test_mismatched_visibility_rejected(self):
        info = {'nameWithOwner':'fuhaooo/jjf-external-deck-skill',
                'isPrivate':True,'url':'https://github.com/fuhaooo/jjf-external-deck-skill',
                'defaultBranchRef':{'name':'main'}}
        with self.assertRaises(ValueError):
            self.mod.verify_remote(info,'fuhaooo/jjf-external-deck-skill',False,
                                   'a'*40,'a'*40,'b'*40,'b'*40)

    def test_mismatched_readme_rejected(self):
        info = {'nameWithOwner':'fuhaooo/jjf-external-deck-skill',
                'isPrivate':False,'url':'https://github.com/fuhaooo/jjf-external-deck-skill',
                'defaultBranchRef':{'name':'main'}}
        with self.assertRaises(ValueError):
            self.mod.verify_remote(info,'fuhaooo/jjf-external-deck-skill',False,
                                   'a'*40,'a'*40,'b'*40,'c'*40)

    def test_publisher_does_not_cross_account(self):
        with self.assertRaises(ValueError):
            self.mod.verify_account('some-other-account','fuhaooo')

    def test_same_account_permitted(self):
        self.mod.verify_account('fuhaooo','fuhaooo')

if __name__ == '__main__':
    unittest.main()

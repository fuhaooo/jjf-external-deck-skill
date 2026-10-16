"""Release regression checks using temporary packages; no external services."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_release
import sync_package_metadata


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / 'skills' / 'jjf-external-deck'
        self.skill.mkdir(parents=True)
        (self.root / 'docs').mkdir()
        (self.skill / 'tests').mkdir()
        for parent in (self.root, self.skill):
            (parent / 'VERSION').write_bytes(b'1.0.4\r\n')
            (parent / 'NOTICE.md').write_bytes(b'# Rights\r\nKeep the brand restrictions.\r\n')
            (parent / 'README.md').write_text('# JJF External Deck Skill\n', encoding='utf-8')
        (self.root / 'README.en.md').write_text('# JJF External Deck Skill\n', encoding='utf-8')
        self.reports = [self.root / 'docs' / 'verification-report.json', self.skill / 'tests' / 'verification-report.json']
        for report in self.reports:
            report.write_text(json.dumps({'version': '1.0.4'}), encoding='utf-8')

    def test_consistent_package_metadata_passes(self):
        self.assertEqual(check_release.metadata_problems(self.root), [])

    def test_missing_skill_version_is_rejected(self):
        (self.skill / 'VERSION').unlink()
        self.assertTrue(any('skill VERSION' in problem for problem in check_release.metadata_problems(self.root)))

    def test_version_drift_and_invalid_canonical_version_are_rejected(self):
        (self.skill / 'VERSION').write_text('1.0.1', encoding='utf-8')
        self.assertTrue(any('does not match root VERSION' in problem for problem in check_release.metadata_problems(self.root)))
        (self.root / 'VERSION').write_text('latest', encoding='utf-8')
        self.assertTrue(any('canonical release version' in problem for problem in check_release.metadata_problems(self.root)))

    def test_stale_overview_titles_are_rejected(self):
        for overview in (self.root / 'README.md', self.root / 'README.en.md', self.skill / 'README.md'):
            with self.subTest(overview=overview):
                overview.write_text('# JJF External Deck Skill v1.0.1\n', encoding='utf-8')
                self.assertTrue(any('Stale release version' in problem for problem in check_release.metadata_problems(self.root)))
                overview.write_text('# JJF External Deck Skill\n', encoding='utf-8')

    def test_rights_must_match_exact_bytes(self):
        (self.skill / 'NOTICE.md').write_bytes(b'# Rights\nKeep the brand restrictions.\n')
        self.assertTrue(any('NOTICE.md does not match' in problem for problem in check_release.metadata_problems(self.root)))

    def test_current_reports_require_matching_version(self):
        for report in self.reports:
            for contents in ({'version': '1.0.1'}, {}, [], 'not json'):
                with self.subTest(report=report, contents=contents):
                    report.write_text(contents if isinstance(contents, str) else json.dumps(contents), encoding='utf-8')
                    self.assertTrue(any('report' in problem for problem in check_release.metadata_problems(self.root)))
            report.write_text(json.dumps({'version': '1.0.4'}), encoding='utf-8')

    def test_historical_versions_are_allowed(self):
        (self.skill / 'README.md').write_text('# JJF External Deck Skill\n\n## Since v1.0.2\nMigration notes.\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text('# Changelog\n\n## v1.0.1\nInitial release.\n', encoding='utf-8')
        self.assertEqual(check_release.metadata_problems(self.root), [])

    def test_sync_changes_only_canonical_copies(self):
        (self.skill / 'VERSION').write_bytes(b'1.0.1\n')
        (self.skill / 'NOTICE.md').unlink()
        unrelated = self.root / 'REPOSITORY.sha256'
        unrelated.write_bytes(b'reviewed checksum list remains untouched\n')
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        updated = sync_package_metadata.sync_metadata(self.root)
        self.assertEqual(set(updated), {'skills/jjf-external-deck/VERSION', 'skills/jjf-external-deck/NOTICE.md'})
        for name in ('VERSION', 'NOTICE.md'):
            self.assertEqual((self.root / name).read_bytes(), (self.skill / name).read_bytes())
        for relative, payload in before.items():
            if relative != Path('skills/jjf-external-deck/VERSION'):
                self.assertEqual((self.root / relative).read_bytes(), payload)
        self.assertEqual(sync_package_metadata.sync_metadata(self.root), [])

    def test_check_mode_is_read_only_and_fails_on_drift(self):
        (self.skill / 'VERSION').write_bytes(b'1.0.1\n')
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        with patch.object(sync_package_metadata, 'ROOT', self.root), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sync_package_metadata.main(['--check']), 2)
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()

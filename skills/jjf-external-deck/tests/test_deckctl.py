import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts' / 'deckctl.py'

class DeckTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.is_file(), 'RED: deterministic page/version guards have not been implemented')
        spec = importlib.util.spec_from_file_location('deckctl', PATH)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'project'
        self.m.init_project(self.work, ROOT)
        fixture_lock = self.m.load_json(self.work/'content-lock.json')
        for page in fixture_lock['pages']:
            page['visible_text'] = [page['headline'], page['subtitle'], page['thesis']] + page['required_content']
            page['visible_text_status'] = 'locked'
        self.m.save_json(self.work/'content-lock.json', fixture_lock)
        self.m.freeze_content(self.work, 'Test fixture content approval, not a real user approval')

    def test_canonical_six_seven_topics(self):
        lock = self.m.load_json(self.work/'content-lock.json')
        self.assertEqual(lock['pages'][5]['topic_key'], 'two-core-engines')
        self.assertEqual(lock['pages'][6]['topic_key'], 'opc-growth-loop')
        self.assertIn('Hacker House', json.dumps(lock['pages'][5], ensure_ascii=False))

    def test_init_does_not_overwrite(self):
        with self.assertRaises(FileExistsError): self.m.init_project(self.work, ROOT)
        fixture_lock = self.m.load_json(self.work/'content-lock.json')
        for page in fixture_lock['pages']:
            page['visible_text'] = [page['headline'], page['subtitle'], page['thesis']] + page['required_content']
            page['visible_text_status'] = 'locked'
        self.m.save_json(self.work/'content-lock.json', fixture_lock)
        self.m.freeze_content(self.work, 'Test fixture content approval, not a real user approval')

    def test_draft_validation(self):
        report = self.m.validate(self.work)
        self.assertEqual(report['errors'], [])
        self.assertFalse(report['ready_for_conversion'])

    def test_content_drift_fails(self):
        p = self.work/'content-lock.json'; lock = self.m.load_json(p)
        lock['pages'][5]['topic_key'] = 'space-planning'
        self.m.save_json(p, lock)
        self.assertTrue(any('CONTENT_LOCK_HASH' in e for e in self.m.validate(self.work)['errors']))

    def test_missing_image_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.m.register_preview(self.work, 6, self.work/'missing.png')

    def test_unknown_approval_rejected(self):
        from PIL import Image
        img=self.work/'test.png'; Image.new('RGB',(1920,1080)).save(img)
        self.m.register_preview(self.work,6,img)
        with self.assertRaises(ValueError):
            self.m.approve_preview(self.work,6,'','user',True)

    def test_approval_requires_visual_review(self):
        from PIL import Image
        img=self.work/'test.png'; Image.new('RGB',(1920,1080)).save(img)
        self.m.register_preview(self.work,6,img)
        with self.assertRaises(ValueError):
            self.m.approve_preview(self.work,6,'User confirmed current candidate','user',False)

    def test_missing_approvals_blocks_handoff(self):
        with self.assertRaises(ValueError): self.m.make_handoff(self.work,[6])

    def test_preview_revision_is_unique(self):
        from PIL import Image
        img=self.work/'test.png'; Image.new('RGB',(1920,1080)).save(img)
        a=self.m.register_preview(self.work,6,img)
        b=self.m.register_preview(self.work,6,img)
        self.assertNotEqual(a['path'],b['path'])
        self.assertEqual(b['revision'],2)

    def test_approval_and_handoff_preserve_mapping(self):
        from PIL import Image
        for n in (6,7):
            img=self.work/f'test{n}.png'; Image.new('RGB',(1920,1080),(n,0,0)).save(img)
            self.m.register_preview(self.work,n,img)
            self.m.approve_preview(self.work,n,'Fixture explicitly authorizes this exact revision','user',True)
        result=self.m.make_handoff(self.work,[7,6])
        self.assertEqual([p['source_page_number'] for p in result['pages']],[6,7])
        self.assertTrue(all(Path(p['source_image']).is_file() for p in result['pages']))
        self.assertFalse(result['conversion_executed'])

    def test_new_candidate_does_not_replace_approved(self):
        from PIL import Image
        img=self.work/'test.png'; Image.new('RGB',(1920,1080)).save(img)
        first=self.m.register_preview(self.work,6,img)
        self.m.approve_preview(self.work,6,'User chose revision 1','user',True)
        self.m.register_preview(self.work,6,img)
        manifest=self.m.load_json(self.work/'deck.manifest.json')
        self.assertEqual(manifest['pages'][5]['approved_preview']['path'],first['path'])
        self.assertFalse(self.m.validate(self.work)['ready_for_conversion'])

    def test_changed_approved_image_fails_hash(self):
        from PIL import Image
        img=self.work/'test.png'; Image.new('RGB',(1920,1080)).save(img)
        a=self.m.register_preview(self.work,6,img)
        self.m.approve_preview(self.work,6,'User chose revision 1','user',True)
        Image.new('RGB',(1920,1080),(255,0,0)).save(self.work/a['path'])
        self.assertTrue(any('PREVIEW_HASH' in e for e in self.m.validate(self.work)['errors']))

    def test_no_fonts_in_package(self):
        self.assertFalse([p for p in ROOT.rglob('*') if p.suffix.lower() in ('.ttf','.otf','.woff','.woff2','.ttc')])

    def approve_fixture(self, number):
        from PIL import Image
        img = self.work/f'test{number}.png'
        Image.new('RGB',(1920,1080),(number,0,0)).save(img)
        self.m.register_preview(self.work,number,img)
        self.m.approve_preview(self.work,number,'Fixture authorizes this exact revision','user',True)

    def test_one_page_content_fix_preserves_other_approved_page(self):
        self.approve_fixture(6); self.approve_fixture(7)
        before = self.m.load_json(self.work/'deck.manifest.json')['pages'][6]['approved_preview']
        lock = self.m.load_json(self.work/'content-lock.json')
        lock['pages'][5]['visible_text'][0] += '（已校正）'
        self.m.save_json(self.work/'content-lock.json',lock)
        self.m.freeze_content(self.work,'Fixture authorizes the page 6 correction')
        after = self.m.load_json(self.work/'deck.manifest.json')
        self.assertIsNone(after['pages'][5]['approved_preview'])
        self.assertEqual(after['pages'][6]['approved_preview'],before)
        self.assertEqual(self.m.validate(self.work)['errors'],[])
        self.assertEqual(self.m.make_handoff(self.work,[7])['pages'][0]['source_page_number'],7)
        with self.assertRaises(ValueError): self.m.make_handoff(self.work,[6])

    def test_relocking_identical_content_keeps_approved_previews(self):
        self.approve_fixture(6)
        before = self.m.load_json(self.work/'deck.manifest.json')['pages'][5]['approved_preview']
        self.m.freeze_content(self.work,'Fixture reconfirms unchanged content')
        self.assertEqual(self.m.load_json(self.work/'deck.manifest.json')['pages'][5]['approved_preview'],before)

    def test_legacy_relock_does_not_invent_per_page_approval(self):
        self.approve_fixture(6)
        manifest = self.m.load_json(self.work/'deck.manifest.json')
        for page in manifest['pages']: page.pop('content_sha256',None)
        self.m.save_json(self.work/'deck.manifest.json',manifest)
        self.m.freeze_content(self.work,'Fixture authorizes migration from legacy project')
        self.assertIsNone(self.m.load_json(self.work/'deck.manifest.json')['pages'][5]['approved_preview'])

    def test_vector_logo_handoff_and_tamper_detection(self):
        self.approve_fixture(6)
        result = self.m.make_handoff(self.work,[6])
        vector = Path(result['logo_vector_path'])
        self.assertTrue(vector.is_file())
        self.assertEqual(self.m.digest(vector.read_bytes()),result['logo_vector_sha256'])
        (self.work/'assets/jjf-logo-primary.svg').write_text('<svg/>',encoding='utf-8')
        self.assertIn('LOGO_VECTOR_HASH',self.m.validate(self.work)['errors'])

if __name__ == '__main__': unittest.main()

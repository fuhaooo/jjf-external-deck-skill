"""Verify bundled official SVGs remain self-contained, intact brand assets."""
import hashlib
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class BrandAssetTests(unittest.TestCase):
    def test_official_vectors_are_intact_and_self_contained(self):
        provenance = json.loads((ROOT/'assets/logo/provenance.json').read_text(encoding='utf-8'))
        self.assertEqual(len(provenance['vectors']),3)
        for item in provenance['vectors']:
            with self.subTest(file=item['file']):
                data = (ROOT/'assets/logo'/item['file']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),item['sha256'])
                root = ET.fromstring(data)
                self.assertEqual(root.get('viewBox'),item['view_box'])
                for node in root.iter():
                    self.assertNotIn(node.tag.rsplit('}',1)[-1],{'script','image','foreignObject'})
                    for key,value in node.attrib.items():
                        self.assertFalse(key.lower().startswith('on'))
                        if key.rsplit('}',1)[-1]=='href': self.assertTrue(value.startswith('#'))

    def test_monochrome_variants_keep_the_primary_glyph_geometry(self):
        def paths(name):
            tree = ET.parse(ROOT/'assets/logo'/name)
            return [''.join(n.get('d','').split()) for n in tree.iter() if n.tag.endswith('}path')]
        primary = paths('jjf-logo-primary.svg')
        self.assertTrue(primary)
        self.assertEqual(primary,paths('jjf-logo-white.svg'))
        self.assertEqual(primary,paths('jjf-logo-white-on-black.svg'))


if __name__=='__main__':
    unittest.main()

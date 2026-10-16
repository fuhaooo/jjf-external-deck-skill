import copy
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/audit_typography.py'
spec = importlib.util.spec_from_file_location('audit_typography', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TypographyTests(unittest.TestCase):
    def setUp(self):
        self.style = {'font_family_latin': 'Arial', 'font_family_cjk': 'Microsoft YaHei',
                      'font_size_px': 22, 'font_weight': 'normal', 'letter_spacing_px': 0,
                      'line_height': 1.1, 'text_align': 'start', 'color': '#FFFFFF'}
        self.box = {'x': 48, 'y': 1010, 'height': 30}
        self.contract = {'schema_version': '1.0', 'coordinate_canvas_px': [1920, 1080],
                         'roles': {'page_footer': {'style': self.style, 'box': self.box,
                                                  'expected_pages': ['p002', 'p003'],
                                                  'tolerances': {'font_size_px': 0.5, 'box_px': 2}}}}
        self.inventory = {'schema_version': '1.0', 'elements': [
            {'page_id': page, 'element_id': 'footer', 'role': 'page_footer',
             'text': '第二页 | Why OPC, Why Now',
             'native_text': True, 'canvas_px': [1920, 1080], 'source': 'PPTX run properties + transform',
             'style': copy.deepcopy(self.style), 'box': copy.deepcopy(self.box)}
            for page in ['p002', 'p003']]}

    def audit(self):
        return module.audit(self.contract, self.inventory)

    def test_same_role_measured_styles_pass(self):
        self.assertEqual(self.audit()['status'], 'pass')

    def test_family_drift_fails_even_when_size_matches(self):
        self.inventory['elements'][1]['style']['font_family_latin'] = 'Roboto Condensed'
        report = self.audit()
        self.assertEqual(report['status'], 'fail')
        self.assertTrue(any('font_family_latin' in e for e in report['errors']))

    def test_missing_or_inherited_font_is_unknown_not_pass(self):
        del self.inventory['elements'][1]['style']['font_family_cjk']
        report = self.audit()
        self.assertEqual(report['status'], 'unknown')
        self.assertFalse(report['passed'])

    def test_different_canvas_normalizes_geometry_and_font_pixels(self):
        item = self.inventory['elements'][1]
        item['canvas_px'] = [960, 540]
        item['style']['font_size_px'] = 11
        item['box'] = {k: v / 2 for k, v in self.box.items()}
        self.assertEqual(self.audit()['status'], 'pass')

    def test_intentional_cover_role_can_have_different_hierarchy(self):
        cover = copy.deepcopy(self.contract['roles']['page_footer'])
        cover['expected_pages'] = ['p001']
        cover['style']['font_size_px'] = 36
        cover['style']['font_weight'] = 'bold'
        self.contract['roles']['cover_website'] = cover
        item = copy.deepcopy(self.inventory['elements'][0])
        item.update(page_id='p001', role='cover_website')
        item['style'] = copy.deepcopy(cover['style'])
        self.inventory['elements'].append(item)
        self.assertEqual(self.audit()['status'], 'pass')

    def test_outlined_or_raster_text_does_not_pass_editability(self):
        self.inventory['elements'][1]['native_text'] = False
        self.assertTrue(any('NOT_NATIVE_TEXT' in e for e in self.audit()['errors']))

    def test_missing_expected_page_and_duplicate_footer_fail(self):
        self.inventory['elements'][1]['page_id'] = 'p002'
        self.inventory['elements'][1]['element_id'] = 'second-footer'
        errors = self.audit()['errors']
        self.assertTrue(any('MISSING_ROLE:p003' in e for e in errors))
        self.assertTrue(any('DUPLICATE_ROLE:p002' in e for e in errors))

    def test_geometry_drift_fails(self):
        self.inventory['elements'][1]['box']['y'] += 15
        self.assertTrue(any('GEOMETRY_MISMATCH' in e for e in self.audit()['errors']))

    def test_missing_scope_and_measurement_cannot_pass(self):
        self.contract['roles']['page_footer']['expected_pages'] = []
        self.inventory['elements'][0].pop('source')
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_mixed_same_script_families_fail(self):
        self.inventory['elements'][1]['style']['font_family_latin'] = ['Arial', 'Aptos']
        self.assertEqual(self.audit()['status'], 'fail')

    def test_distorted_canvas_fails(self):
        self.inventory['elements'][1]['canvas_px'] = [1920, 1000]
        self.assertTrue(any('CANVAS_ASPECT_RATIO' in e for e in self.audit()['errors']))

    def test_nonfinite_measurement_is_rejected(self):
        self.inventory['elements'][0]['style']['font_size_px'] = float('nan')
        self.assertEqual(self.audit()['status'], 'fail')

    def test_chinese_requires_contract_and_observed_cjk_font(self):
        del self.contract['roles']['page_footer']['style']['font_family_cjk']
        del self.inventory['elements'][0]['style']['font_family_cjk']
        report = self.audit()
        self.assertEqual(report['status'], 'unknown')
        self.assertTrue(any('CONTRACT_STYLE_UNKNOWN' in e and 'font_family_cjk' in e for e in report['unknowns']))
        self.assertTrue(any(e.startswith('STYLE_UNKNOWN:') and 'font_family_cjk' in e for e in report['unknowns']))

    def test_latin_only_website_does_not_require_cjk_font(self):
        del self.contract['roles']['page_footer']['style']['font_family_cjk']
        for item in self.inventory['elements']:
            item['text'] = 'JJF-TECH.CN'
            del item['style']['font_family_cjk']
        self.assertEqual(self.audit()['status'], 'pass')

    def test_missing_color_contract_cannot_pass(self):
        del self.contract['roles']['page_footer']['style']['color']
        report = self.audit()
        self.assertEqual(report['status'], 'unknown')
        self.assertIn('CONTRACT_STYLE_UNKNOWN:page_footer:color', report['unknowns'])

    def test_missing_observed_color_cannot_pass(self):
        del self.inventory['elements'][0]['style']['color']
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_missing_measured_text_cannot_pass_script_coverage(self):
        del self.inventory['elements'][0]['text']
        self.assertEqual(self.audit()['status'], 'unknown')

    def test_nonpositive_sizes_are_invalid_in_contract_and_measurement(self):
        original_contract, original_inventory = copy.deepcopy(self.contract), copy.deepcopy(self.inventory)
        for location in ('contract', 'measurement', 'both'):
            for field in ('font_size_px', 'line_height', 'width', 'height'):
                for value in (0, -1):
                    with self.subTest(location=location, field=field, value=value):
                        self.contract, self.inventory = copy.deepcopy(original_contract), copy.deepcopy(original_inventory)
                        targets = []
                        if location in ('contract', 'both'):
                            targets.append(self.contract['roles']['page_footer'])
                        if location in ('measurement', 'both'):
                            targets.append(self.inventory['elements'][0])
                        for target in targets:
                            target['box' if field in ('width', 'height') else 'style'][field] = value
                        report = self.audit()
                        self.assertEqual(report['status'], 'fail')
                        self.assertTrue(any(e.startswith('INVALID_INPUT:') for e in report['errors']))


if __name__ == '__main__':
    unittest.main()

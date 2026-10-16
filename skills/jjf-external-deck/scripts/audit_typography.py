#!/usr/bin/env python3
"""Check measured repeated-label styles against a project contract; never infer missing fonts."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re


STYLE_FIELDS = {
    'font_family_latin', 'font_family_cjk', 'font_size_px', 'font_weight',
    'letter_spacing_px', 'line_height', 'text_align', 'color',
}
REQUIRED_STYLE = {
    'font_family_latin', 'font_size_px', 'font_weight', 'letter_spacing_px',
    'line_height', 'text_align', 'color',
}
BOX_FIELDS = {'x', 'y', 'width', 'height'}
NUMERIC_STYLE = {'font_size_px', 'letter_spacing_px', 'line_height'}
POSITIVE_STYLE = {'font_size_px', 'line_height'}
CJK_TEXT = re.compile('[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff\U00020000-\U0003134f]')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def canvas(value):
    if not isinstance(value, list) or len(value) != 2 or not all(number(v) and v > 0 for v in value):
        raise ValueError('canvas must contain two positive finite pixel dimensions')
    return value


def audit(contract: dict, inventory: dict) -> dict:
    result = {'status': 'unknown', 'passed': False, 'errors': [], 'unknowns': [],
              'checked_elements': 0, 'normalized_canvas_px': None,
              'unperformed_checks': ['visual_overlap', 'font_rendering', 'actual_edit_smoke_test'],
              'scope': 'Measured typography contract only; not full visual or editable-PPT acceptance.'}
    errors, unknowns = result['errors'], result['unknowns']
    try:
        if contract.get('schema_version') != '1.0' or inventory.get('schema_version') != '1.0':
            raise ValueError('unsupported schema_version')
        reference = canvas(contract.get('coordinate_canvas_px'))
        result['normalized_canvas_px'] = reference
        roles = contract.get('roles')
        elements = inventory.get('elements')
        if not isinstance(roles, dict) or not roles or not isinstance(elements, list):
            raise ValueError('nonempty roles and an elements list are required')
        counts = Counter()
        identities = set()
        for role, spec in roles.items():
            if not isinstance(spec, dict):
                raise ValueError('each role must be an object')
            style = spec.get('style', {})
            if not isinstance(style, dict) or set(style) - STYLE_FIELDS:
                raise ValueError(f'{role}: invalid style fields')
            for field in REQUIRED_STYLE - style.keys():
                unknowns.append(f'CONTRACT_STYLE_UNKNOWN:{role}:{field}')
            for field, value in style.items():
                if value is None:
                    unknowns.append(f'CONTRACT_STYLE_UNKNOWN:{role}:{field}')
                elif field in NUMERIC_STYLE and not number(value):
                    raise ValueError(f'{role}: {field} must be a finite number')
                elif field in POSITIVE_STYLE and value <= 0:
                    raise ValueError(f'{role}: {field} must be positive')
                elif field not in NUMERIC_STYLE and not isinstance(value, str):
                    raise ValueError(f'{role}: {field} must be a string')
            box = spec.get('box', {})
            if not isinstance(box, dict) or set(box) - BOX_FIELDS or not all(number(v) for v in box.values()):
                raise ValueError(f'{role}: invalid box')
            if any(box.get(field, 1) <= 0 for field in ('width', 'height')):
                raise ValueError(f'{role}: box width and height must be positive')
            if not box:
                unknowns.append(f'CONTRACT_GEOMETRY_UNKNOWN:{role}')
            pages = spec.get('expected_pages')
            if not isinstance(pages, list) or not pages:
                unknowns.append(f'CONTRACT_SCOPE_UNKNOWN:{role}')
            elif any(not isinstance(p, str) or not p for p in pages) or len(pages) != len(set(pages)):
                raise ValueError(f'{role}: expected_pages must contain unique nonempty string IDs')
            for key, value in spec.get('tolerances', {}).items():
                if key not in NUMERIC_STYLE | {'box_px'} or not number(value) or value < 0:
                    raise ValueError(f'{role}: invalid tolerance {key}')
        if not elements:
            unknowns.append('NO_MEASURED_ELEMENTS')
        for item in elements:
            if not isinstance(item, dict):
                raise ValueError('each inventory element must be an object')
            page, element, role = item.get('page_id'), item.get('element_id'), item.get('role')
            if not all(isinstance(v, str) and v for v in (page, element, role)):
                raise ValueError('page_id, element_id and role are required')
            identity = (page, element)
            if identity in identities:
                errors.append(f'DUPLICATE_ELEMENT:{page}:{element}')
            identities.add(identity)
            label = f'{page}:{element}:{role}'
            if role not in roles:
                unknowns.append(f'UNMAPPED_ROLE:{label}')
                continue
            spec = roles[role]
            counts[(role, page)] += 1
            if spec.get('expected_pages') and page not in spec['expected_pages']:
                errors.append(f'OUT_OF_SCOPE_ELEMENT:{label}')
            if item.get('native_text') is False:
                errors.append(f'NOT_NATIVE_TEXT:{label}')
            elif item.get('native_text') is not True:
                unknowns.append(f'EDITABILITY_UNKNOWN:{label}')
            if not item.get('source'):
                unknowns.append(f'MEASUREMENT_SOURCE_UNKNOWN:{label}')
            measured_text = item.get('text')
            if measured_text is None or isinstance(measured_text, str) and not measured_text.strip():
                unknowns.append(f'MEASURED_TEXT_UNKNOWN:{label}')
            elif not isinstance(measured_text, str):
                raise ValueError(f'{label}: measured text must be a string')
            if item.get('canvas_px') is None:
                unknowns.append(f'CANVAS_UNKNOWN:{label}')
                continue
            actual = canvas(item['canvas_px'])
            sx, sy = reference[0] / actual[0], reference[1] / actual[1]
            if not math.isclose(sx, sy, rel_tol=0.002):
                errors.append(f'CANVAS_ASPECT_RATIO:{label}')
            style, box = item.get('style', {}), item.get('box', {})
            if not isinstance(style, dict) or not isinstance(box, dict):
                raise ValueError('measured style and box must be objects')
            for field in POSITIVE_STYLE:
                value = style.get(field)
                if value is not None and (not number(value) or value <= 0):
                    raise ValueError(f'{label}: measured {field} must be positive and finite')
            for field in ('width', 'height'):
                value = box.get(field)
                if value is not None and (not number(value) or value <= 0):
                    raise ValueError(f'{label}: measured box {field} must be positive and finite')
            if isinstance(measured_text, str) and CJK_TEXT.search(measured_text):
                if not spec.get('style', {}).get('font_family_cjk'):
                    unknowns.append(f'CONTRACT_STYLE_UNKNOWN:{label}:font_family_cjk')
                if not style.get('font_family_cjk'):
                    unknowns.append(f'STYLE_UNKNOWN:{label}:font_family_cjk')
            tolerances = spec.get('tolerances', {})
            for field, expected in spec.get('style', {}).items():
                if expected is None:
                    continue
                observed = style.get(field)
                if observed is None:
                    unknowns.append(f'STYLE_UNKNOWN:{label}:{field}')
                    continue
                if field in NUMERIC_STYLE:
                    if not number(observed):
                        errors.append(f'STYLE_MISMATCH:{label}:{field}')
                        continue
                    scale = sy if field == 'font_size_px' else sx if field == 'letter_spacing_px' else 1
                    if abs(observed * scale - expected) > tolerances.get(field, 0):
                        errors.append(f'STYLE_MISMATCH:{label}:{field}')
                elif not isinstance(observed, str) or observed.casefold().strip() != expected.casefold().strip():
                    errors.append(f'STYLE_MISMATCH:{label}:{field}')
            for field, expected in spec.get('box', {}).items():
                observed = box.get(field)
                if observed is None:
                    unknowns.append(f'GEOMETRY_UNKNOWN:{label}:{field}')
                elif not number(observed) or abs(observed * (sx if field in {'x', 'width'} else sy) - expected) > tolerances.get('box_px', 0):
                    errors.append(f'GEOMETRY_MISMATCH:{label}:{field}')
            result['checked_elements'] += 1
        for role, spec in roles.items():
            for page in spec.get('expected_pages') or []:
                if counts[(role, page)] == 0:
                    errors.append(f'MISSING_ROLE:{page}:{role}')
                elif counts[(role, page)] > 1:
                    errors.append(f'DUPLICATE_ROLE:{page}:{role}')
    except (ValueError, TypeError, AttributeError) as exc:
        errors.append('INVALID_INPUT:' + str(exc))
    result['status'] = 'fail' if errors else 'unknown' if unknowns else 'pass'
    result['passed'] = result['status'] == 'pass'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', type=Path)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        report = audit(json.loads(args.contract.read_text(encoding='utf-8')),
                       json.loads(args.inventory.read_text(encoding='utf-8')))
    except (OSError, json.JSONDecodeError) as exc:
        report = {'status': 'fail', 'passed': False, 'errors': ['INVALID_INPUT:' + str(exc)], 'unknowns': []}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + '\n', encoding='utf-8')
    print(text)
    return {'pass': 0, 'fail': 1, 'unknown': 2}[report['status']]


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check the reviewed file boundary and checksums; does not call external services."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache'}
IGNORED_FILES = {'REPOSITORY.sha256', '.publication.json', '.DS_Store'}
PROHIBITED_SUFFIXES = {'.pdf', '.pptx', '.ppt', '.docx', '.doc', '.xlsx', '.xls', '.ttf', '.otf', '.woff', '.woff2', '.pem', '.key'}


def main():
    problems = []
    manifest = ROOT / 'REPOSITORY.sha256'
    if not manifest.is_file():
        print('Missing REPOSITORY.sha256', file=sys.stderr)
        return 2
    expected = {}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line:
            continue
        sha, name = line.split('  ', 1)
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or not re.fullmatch('[0-9a-f]{64}', sha) or name in expected:
            problems.append('Invalid/duplicate checksum entry: ' + name)
            continue
        expected[name] = sha
    actual = set()
    for file in ROOT.rglob('*'):
        rel = file.relative_to(ROOT)
        if set(rel.parts).intersection(IGNORED_DIRS) or file.name in IGNORED_FILES:
            continue
        if file.is_symlink():
            problems.append('Symlink is not part of this distribution: ' + rel.as_posix())
            continue
        if not file.is_file():
            continue
        name = rel.as_posix()
        actual.add(name)
        if file.suffix.lower() in PROHIBITED_SUFFIXES or file.name.startswith('.env') or file.name in {'credentials.json', 'hosts.yml', '.git-credentials'}:
            problems.append('Forbidden publication file: ' + name)
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if expected.get(name) != digest:
            problems.append('Unreviewed or modified file: ' + name)
        if file.suffix in {'.md', '.json', '.yaml', '.yml', '.txt', '.csv', '.py'}:
            text = file.read_text(encoding='utf-8')
            if re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', text):
                problems.append('Potential credential in ' + name)
    for name in sorted(set(expected) - actual):
        problems.append('Missing release file: ' + name)
    skill = ROOT / 'skills' / 'jjf-external-deck'
    if 'name: jjf-external-deck' not in (skill / 'SKILL.md').read_text(encoding='utf-8'):
        problems.append('Skill discovery name is incorrect.')
    provenance = json.loads((skill / 'assets/logo/provenance.json').read_text(encoding='utf-8'))
    logo_sha = hashlib.sha256((skill / 'assets/logo/jjf-logo-master.png').read_bytes()).hexdigest()
    if logo_sha != provenance['sha256']:
        problems.append('Official logo hash does not match recorded master.')
    for vector in provenance.get('vectors', []):
        path = skill / 'assets/logo' / vector['file']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != vector['sha256']:
            problems.append('Official vector logo hash mismatch: ' + vector['file'])
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 2
    print(f'PASS: {len(actual)} reviewed files; hashes match; skill layout and official logo verified.')
    print('This is not a complete security audit or an image/PPT/Canva quality guarantee.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

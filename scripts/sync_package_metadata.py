#!/usr/bin/env python3
"""Mirror reviewed root VERSION/NOTICE into the installable skill; no checksum updates."""
import argparse
from pathlib import Path
import sys

from check_release import metadata_problems, read_release_version

ROOT = Path(__file__).resolve().parents[1]


def sync_metadata(root: Path) -> list[str]:
    """Copy only the two canonical metadata files, preserving their exact bytes."""
    read_release_version(root)
    skill = root / 'skills' / 'jjf-external-deck'
    if not skill.is_dir() or skill.is_symlink():
        raise ValueError('Expected a real skills/jjf-external-deck directory.')
    copies = [(root / name, skill / name) for name in ('VERSION', 'NOTICE.md')]
    # Read both inputs and check destinations before writing either file.
    payloads = [(target, source.read_bytes()) for source, target in copies]
    if any(target.is_symlink() for target, _ in payloads):
        raise ValueError('Refusing to replace a symlink in package metadata.')
    updated = []
    for target, payload in payloads:
        if not target.exists() or target.read_bytes() != payload:
            target.write_bytes(payload)
            updated.append(target.relative_to(root).as_posix())
    return updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check current metadata without writing any files')
    args = parser.parse_args(argv)
    try:
        if not args.check:
            updated = sync_metadata(ROOT)
            print('Synchronized: ' + ', '.join(updated) if updated else 'Package metadata already synchronized.')
        problems = metadata_problems(ROOT)
        if problems:
            print('\n'.join(problems), file=sys.stderr)
            return 2
        print('PASS: current package versions, overview titles and rights metadata are consistent.')
        if not args.check:
            print('No README, verification report or checksum was rewritten. Review those files before release.')
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print('Package metadata synchronization failed: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

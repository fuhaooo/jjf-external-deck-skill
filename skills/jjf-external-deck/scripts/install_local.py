#!/usr/bin/env python3
"""Copy this local skill into a Codex skill directory; never download or overwrite."""
import argparse
from pathlib import Path
import shutil
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scope',choices=['user','project'],required=True)
    p.add_argument('--project',type=Path)
    a=p.parse_args(); source=Path(__file__).resolve().parents[1]
    if a.scope=='project' and a.project is None: p.error('--project is required for project scope')
    base=Path.home() if a.scope=='user' else a.project.resolve()
    dest=base/'.agents'/'skills'/'jjf-external-deck'
    if dest.resolve().is_relative_to(source): p.error('Destination cannot be inside the source skill directory')
    if dest.exists():
        print(f'Refusing to overwrite existing skill: {dest}. Back up/review it first.',file=sys.stderr); return 2
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
    print(f'Installed local skill directory: {dest}')
    print('External conversion skill was not downloaded or installed. No user settings were changed.')
    return 0
if __name__=='__main__': raise SystemExit(main())

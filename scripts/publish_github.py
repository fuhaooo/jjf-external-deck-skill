#!/usr/bin/env python3
"""Create a NEW personal GitHub repository, push this reviewed tree, then verify it.

Dry-run by default. Uses an existing `gh auth login` session; never reads tokens.
Existing remotes/repositories are not overwritten. No force pushes or deletions.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = 'JJF external-deck skill: brand-consistent storytelling, visual design, editable PowerPoint and Canva handoff.'


def repo_identity(owner: str, name: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', owner):
        raise ValueError('Invalid GitHub owner.')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}', name) or name in {'.', '..'}:
        raise ValueError('Invalid repository name.')
    return f'{owner}/{name}'


def verify_account(login: str, owner: str) -> None:
    if login.casefold() != owner.casefold():
        raise ValueError(f'Logged in as {login}, but requested owner is {owner}. Switch accounts first. This helper supports personal accounts only.')


def verify_remote(info: dict, target: str, private: bool, local_sha: str,
                  remote_sha: str, local_readme: str, remote_readme: str) -> None:
    if info.get('nameWithOwner', '').casefold() != target.casefold():
        raise ValueError('Remote repository identity does not match the requested target.')
    if info.get('isPrivate') is not private:
        raise ValueError('Remote visibility does not match the selected visibility.')
    if (info.get('defaultBranchRef') or {}).get('name') != 'main':
        raise ValueError('Remote default branch is not main. Verify the repository before publishing installation instructions.')
    if not re.fullmatch(r'[0-9a-f]{40,64}', local_sha) or local_sha != remote_sha:
        raise ValueError('Remote main commit does not match local HEAD.')
    if not re.fullmatch(r'[0-9a-f]{40,64}', local_readme) or local_readme != remote_readme:
        raise ValueError('Remote README does not match the reviewed local README.')


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f'{args[0]} command failed ({result.returncode}): {detail}')
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True, help='GitHub personal account; must match the authenticated user')
    parser.add_argument('--name', default='jjf-external-deck-skill')
    vis = parser.add_mutually_exclusive_group(required=True)
    vis.add_argument('--public', action='store_true')
    vis.add_argument('--private', action='store_true')
    parser.add_argument('--execute', action='store_true', help='Perform the remote creation and push; omitted means dry-run')
    args = parser.parse_args(argv)
    try:
        target = repo_identity(args.owner, args.name)
        visibility = '--private' if args.private else '--public'
        if not args.execute:
            print(f'DRY RUN: target={target}; visibility={visibility[2:]}')
            print('Will check the release manifest, existing authentication, account, and repository name.')
            print('Will initialize a local main branch, commit the reviewed files, create a NEW repo, and push.')
            print('Will verify remote identity, visibility, default branch, HEAD, and README.')
            print('No GitHub request or repository write was performed. Add --execute to publish.')
            return 0
        for executable in ['git', 'gh']:
            if shutil.which(executable) is None:
                raise RuntimeError(f'{executable} is not installed. Install it locally; see docs/PUBLISHING.md.')
        # Audit before staging any files. No private files are copied by this tool.
        print('Checking reviewed release files...', flush=True)
        print(run([sys.executable, str(ROOT / 'scripts' / 'check_release.py')]).stdout.strip())
        if target not in (ROOT / 'README.md').read_text(encoding='utf-8'):
            raise ValueError('README install instructions do not contain this repository name. Update and review the docs/checksums first.')
        auth = run(['gh', 'auth', 'status', '--hostname', 'github.com'], check=False)
        if auth.returncode:
            raise RuntimeError('GitHub CLI is not authenticated. Run: gh auth login --hostname github.com --git-protocol https --web')
        login = run(['gh', 'api', 'user', '--jq', '.login']).stdout.strip()
        verify_account(login, args.owner)
        existing = run(['gh', 'repo', 'view', target, '--json', 'nameWithOwner'], check=False)
        if existing.returncode == 0:
            raise ValueError('Target repository already exists; refusing to overwrite it. For a partial publish, use the recovery steps in docs/PUBLISHING.md.')
        missing_msg = existing.stderr + existing.stdout
        if not re.search(r'HTTP 404|Could not resolve to a Repository|Not Found.*404', missing_msg, re.IGNORECASE | re.DOTALL):
            raise RuntimeError('Could not establish whether the repository exists. Resolve the GitHub/network error first: ' + missing_msg.strip())
        if (ROOT / '.git').exists():
            top = run(['git', 'rev-parse', '--show-toplevel']).stdout.strip()
            if Path(top).resolve() != ROOT:
                raise ValueError('Unexpected git root; use a clean extracted copy.')
            if run(['git', 'remote']).stdout.strip():
                raise ValueError('Local repository already has a remote. Refusing to replace it.')
            if run(['git', 'rev-parse', '--verify', 'HEAD'], check=False).returncode == 0:
                raise ValueError('Local repository already has commits. Review and publish it manually; this helper initializes a fresh repository only.')
        print(f'Creating {visibility[2:]} repository {target}...', flush=True)
        run(['git', 'init', '-b', 'main', str(ROOT)])
        # Use exact reviewed file paths, not a broad `git add .`.
        files = [line.split('  ', 1)[1] for line in (ROOT / 'REPOSITORY.sha256').read_text().splitlines() if line]
        run(['git', 'add', '--', *files, 'REPOSITORY.sha256'])
        user_id = run(['gh', 'api', 'user', '--jq', '.id']).stdout.strip()
        if not user_id.isdigit():
            raise ValueError('Invalid authenticated GitHub user id.')
        name = run(['git', 'config', '--get', 'user.name'], check=False).stdout.strip() or login
        # Always use the authenticated account's noreply email, not a private profile email.
        email = f'{user_id}+{login}@users.noreply.github.com'
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        run(['git', '-c', f'user.name={name}', '-c', f'user.email={email}', 'commit', '-m', f'Publish JJF external deck skill v{version}'])
        result = run(['gh', 'repo', 'create', target, visibility, '--source', str(ROOT),
                      '--remote', 'origin', '--push', '--description', DESCRIPTION, '--disable-wiki'])
        if result.stdout.strip():
            print(result.stdout.strip())
        info = json.loads(run(['gh', 'repo', 'view', target, '--json',
                               'nameWithOwner,isPrivate,url,defaultBranchRef']).stdout)
        local_sha = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        remote_ref = run(['git', 'ls-remote', 'origin', 'refs/heads/main']).stdout.strip()
        remote_sha = remote_ref.split()[0] if remote_ref else ''
        local_readme = run(['git', 'hash-object', 'README.md']).stdout.strip()
        remote_readme = run(['gh', 'api', f'repos/{target}/contents/README.md?ref=main', '--jq', '.sha']).stdout.strip()
        verify_remote(info, target, args.private, local_sha, remote_sha, local_readme, remote_readme)
        report = {'remote_created': True, 'verified': True, 'url': info['url'],
                  'repository': target, 'visibility': visibility[2:], 'commit': local_sha,
                  'readme_blob': remote_readme, 'default_branch': 'main'}
        (ROOT / '.publication.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print('VERIFIED: ' + info['url'])
        print('Commit: ' + local_sha)
        if args.private:
            print('Private repository: installation requires authorized GitHub access.')
        print(f'Install: npx skills@latest add {target} --skill jjf-external-deck --agent codex --global')
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f'Publication not completed/verified: {exc}', file=sys.stderr)
        print('Existing local/remote progress has NOT been deleted. See docs/PUBLISHING.md before retrying.', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

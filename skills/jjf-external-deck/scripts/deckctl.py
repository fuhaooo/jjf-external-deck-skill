#!/usr/bin/env python3
"""Local JJF page/version guards. No network, image generation, OCR, or fake conversion."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def content_hash(lock: dict) -> str:
    return digest(json.dumps(lock['pages'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def page_content_hash(page: dict) -> str:
    return digest(json.dumps(page, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def preview_matches_content(item: dict, page: dict, manifest: dict) -> bool:
    if item.get('page_content_sha256') is not None:
        return item['page_content_sha256'] == page.get('content_sha256')
    # Older projects used a deck-wide hash. Never infer per-page approval from it.
    return item.get('content_sha256') == manifest['content_sha256']

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def inside(root: Path, relative: str) -> Path:
    p = (root / relative).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('Path escapes project directory')
    return p

def find_page(manifest: dict, number: int) -> dict:
    matches = [p for p in manifest['pages'] if p['page_number'] == number]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one page {number}, got {len(matches)}')
    return matches[0]

def init_project(project: Path, skill_root: Path = SKILL_ROOT) -> dict:
    project = project.resolve()
    if project.exists() and any(project.iterdir()):
        raise FileExistsError(f'Refusing to overwrite nonempty project: {project}')
    project.mkdir(parents=True, exist_ok=True)
    for folder in ['sources', 'assets', 'previews', 'qa', 'handoff', 'final']:
        (project / folder).mkdir(exist_ok=True)
    for source, target in [('templates/opc19-content-lock.json', 'content-lock.json'),
                           ('templates/project-brief.md', 'brief.md'),
                           ('templates/claim-ledger.csv', 'claim-ledger.csv'),
                           ('templates/budget.json', 'budget.json'),
                           ('assets/logo/jjf-logo-master.png', 'assets/jjf-logo-master.png')]:
        shutil.copy2(skill_root / source, project / target)
    lock = load_json(project / 'content-lock.json')
    manifest = {'schema_version': '1.0', 'deck_id': 'jjf-' + uuid.uuid4().hex[:10],
        'created_at': now(), 'state': 'draft', 'content_sha256': content_hash(lock),
        'content_approval': None,
        'logo': {'path': 'assets/jjf-logo-master.png', 'sha256': digest((project/'assets/jjf-logo-master.png').read_bytes())},
        'pages': [{'page_number': p['page_number'], 'page_id': p['page_id'], 'topic_key': p['topic_key'],
                   'visual': p['visual'], 'content_sha256': page_content_hash(p),
                   'candidate': None, 'approved_preview': None, 'history': []} for p in lock['pages']]}
    vector = skill_root / 'assets/logo/jjf-logo-primary.svg'
    if vector.is_file():
        shutil.copy2(vector, project/'assets/jjf-logo-primary.svg')
        manifest['logo'].update({'vector_path': 'assets/jjf-logo-primary.svg',
                                 'vector_sha256': digest(vector.read_bytes())})
    save_json(project / 'deck.manifest.json', manifest)
    return manifest

def freeze_content(project: Path, evidence: str) -> dict:
    if not evidence.strip(): raise ValueError('Real approval evidence is required')
    lock = load_json(project/'content-lock.json')
    for page in lock['pages']:
        if not page.get('visible_text') or page.get('visible_text_status') != 'locked':
            raise ValueError(f"{page['page_id']}: write exact visible_text and set visible_text_status=locked first")
    manifest = load_json(project/'deck.manifest.json')
    # Explicit content-authority change; drafts and historical assets remain in history.
    old = {p['page_id']: p for p in manifest['pages']}
    manifest['pages'] = []
    for p in lock['pages']:
        current = old.get(p['page_id'], {'history': []})
        page_sha = page_content_hash(p)
        unchanged = current.get('content_sha256') == page_sha
        # A local text fix invalidates only its own preview. Legacy projects without
        # per-page hashes conservatively invalidate once when first re-locked.
        if not unchanged:
            current.update({'candidate': None, 'approved_preview': None})
        current.update({'page_id': p['page_id'], 'page_number': p['page_number'], 'topic_key': p['topic_key'],
                        'visual': p['visual'], 'content_sha256': page_sha})
        manifest['pages'].append(current)
    manifest['content_sha256'] = content_hash(lock)
    manifest['content_approval'] = {'evidence': evidence, 'at': now()}
    manifest['state'] = 'content-locked'
    save_json(project/'deck.manifest.json', manifest)
    return manifest

def validate(project: Path) -> dict:
    errors: list[str] = []; warnings: list[str] = []
    manifest = load_json(project/'deck.manifest.json')
    lock = load_json(project/'content-lock.json')
    if manifest.get('content_sha256') != content_hash(lock): errors.append('CONTENT_LOCK_HASH: content changed without explicit re-lock')
    pages = manifest.get('pages', [])
    numbers = [p['page_number'] for p in pages]
    ids = [p['page_id'] for p in pages]
    if len(set(numbers)) != len(numbers) or len(set(ids)) != len(ids): errors.append('DUPLICATE_PAGE')
    if numbers != sorted(numbers): errors.append('PAGE_ORDER')
    locked = {p['page_id']: p for p in lock['pages']}
    if set(locked) != set(ids): errors.append('PAGE_SET_MISMATCH')
    logo = inside(project, manifest['logo']['path'])
    if not logo.is_file() or digest(logo.read_bytes()) != manifest['logo']['sha256']: errors.append('LOGO_HASH')
    if manifest['logo'].get('vector_path'):
        vector = inside(project, manifest['logo']['vector_path'])
        if not vector.is_file() or digest(vector.read_bytes()) != manifest['logo'].get('vector_sha256'):
            errors.append('LOGO_VECTOR_HASH')
    ready = bool(manifest.get('content_approval')) and bool(pages)
    for page in pages:
        spec = locked.get(page['page_id'], {})
        if page['topic_key'] != spec.get('topic_key') or page['page_number'] != spec.get('page_number'):
            errors.append(f"TOPIC_MISMATCH:{page['page_id']}")
        if page.get('content_sha256') is not None and page['content_sha256'] != page_content_hash(spec):
            errors.append(f"PAGE_CONTENT_HASH:{page['page_id']}")
        a = page.get('approved_preview'); c = page.get('candidate')
        if not a or not c or a['revision'] != c['revision']: ready = False
        for role in ['candidate', 'approved_preview']:
            item = page.get(role)
            if not item: continue
            try:
                path = inside(project, item['path'])
                if not path.is_file(): errors.append(f"MISSING_PREVIEW:{page['page_id']}:{role}")
                elif digest(path.read_bytes()) != item['sha256']: errors.append(f"PREVIEW_HASH:{page['page_id']}:{role}")
            except (KeyError, ValueError): errors.append(f"INVALID_PREVIEW_PATH:{page['page_id']}:{role}")
            if not preview_matches_content(item, page, manifest): errors.append(f"STALE_PREVIEW:{page['page_id']}")
        if a and (not a.get('approval', {}).get('evidence') or not a.get('approval', {}).get('visual_reviewed')):
            errors.append(f"APPROVAL_EVIDENCE:{page['page_id']}")
    for before, after in zip(pages, pages[1:]):
        same = [key for key in ('family', 'layout', 'motif') if before.get('visual', {}).get(key) == after.get('visual', {}).get(key)]
        if len(same) >= 2: warnings.append(f"RHYTHM_REVIEW:{before['page_id']}->{after['page_id']}:{','.join(same)}")
    for i in range(len(pages)-2):
        if all(p.get('visual', {}).get('density') == 'high' for p in pages[i:i+3]): warnings.append(f"DENSE_RUN:{pages[i]['page_id']}")
    return {'errors': errors, 'warnings': warnings, 'ready_for_conversion': ready and not errors,
            'checks': 'Hash/schema/version checks only; no automatic visual or factual approval.'}

def register_preview(project: Path, number: int, image: Path) -> dict:
    if not image.is_file(): raise FileNotFoundError(image)
    report = validate(project)
    if report['errors']: raise ValueError('; '.join(report['errors']))
    from PIL import Image
    with Image.open(image) as im:
        w, h = im.size
        if w < 960 or h < 540 or abs(w/h - 16/9) > 0.01:
            raise ValueError('Expected a readable approximately 16:9 single slide (at least 960x540)')
        im.verify()
    manifest = load_json(project/'deck.manifest.json')
    page = find_page(manifest, number)
    revision = max([x['revision'] for x in page['history']], default=0)+1
    ext = image.suffix.lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.webp'}: raise ValueError('Unsupported image format')
    rel = f"previews/{page['page_id']}-{page['topic_key']}-r{revision:03d}-preview{ext}"
    target = inside(project, rel)
    if target.exists(): raise FileExistsError(target)
    shutil.copy2(image, target)
    item = {'revision': revision, 'path': rel, 'sha256': digest(target.read_bytes()),
            'width': w, 'height': h, 'content_sha256': manifest['content_sha256'],
            'page_content_sha256': page.get('content_sha256'), 'status': 'candidate', 'created_at': now()}
    page['history'].append(item.copy()); page['candidate'] = item
    manifest['state'] = 'preview-candidate'
    save_json(project/'deck.manifest.json', manifest)
    return item

def approve_preview(project: Path, number: int, evidence: str, reviewer: str, visual_reviewed: bool, revision: int | None = None) -> dict:
    if not evidence.strip(): raise ValueError('Approval requires specific real evidence, not silence or the next-page request')
    if reviewer not in {'user', 'delegated-design-lead'}: raise ValueError('Unknown reviewer')
    if not visual_reviewed: raise ValueError('Actual visual review is required')
    report = validate(project)
    if report['errors']: raise ValueError('; '.join(report['errors']))
    manifest = load_json(project/'deck.manifest.json')
    if not manifest.get('content_approval'): raise ValueError('Lock exact content with approval evidence before approving an image')
    page = find_page(manifest, number)
    item = page.get('candidate') if revision is None else next((i for i in page['history'] if i['revision'] == revision), None)
    if not item: raise ValueError('Requested candidate does not exist')
    if not preview_matches_content(item, page, manifest): raise ValueError('Cannot approve image from a stale content lock')
    item = json.loads(json.dumps(item))
    item['status'] = 'approved'
    item['approval'] = {'by': reviewer, 'evidence': evidence, 'visual_reviewed': True, 'at': now()}
    page['candidate'] = item.copy(); page['approved_preview'] = item
    manifest['state'] = 'preview-approved-partial'
    save_json(project/'deck.manifest.json', manifest)
    return item

def make_handoff(project: Path, selected: list[int] | None = None) -> dict:
    report = validate(project)
    if report['errors']: raise ValueError('; '.join(report['errors']))
    manifest = load_json(project/'deck.manifest.json'); lock=load_json(project/'content-lock.json')
    if not manifest.get('content_approval'): raise ValueError('Content approval is missing')
    selected = sorted(set(selected if selected is not None else [p['page_number'] for p in manifest['pages']]))
    if not selected: raise ValueError('No pages selected')
    items=[]
    for n in selected:
        page=find_page(manifest,n); a=page.get('approved_preview'); c=page.get('candidate')
        if not a or not c or a['revision'] != c['revision']: raise ValueError(f'Page {n} has no unambiguous current approval')
        items.append((page,a))
    job = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    out=project/'handoff'/job; (out/'inputs').mkdir(parents=True)
    shutil.copy2(project/'content-lock.json',out/'content-lock.json')
    shutil.copy2(inside(project,manifest['logo']['path']),out/'jjf-logo-master.png')
    mapping=[]
    for i,(page,a) in enumerate(items,1):
        src=inside(project,a['path']); dest=out/'inputs'/f"{page['page_id']}{src.suffix}"
        shutil.copy2(src,dest)
        spec=next(p for p in lock['pages'] if p['page_id']==page['page_id'])
        mapping.append({'converter_page_id':f'page_{i:03d}','source_page_number':page['page_number'],'source_page_id':page['page_id'],
                        'topic_key':page['topic_key'],'source_image':str(dest.resolve()),'source_sha256':a['sha256'],
                        'visible_text':spec['visible_text'],'required_content':spec['required_content']})
    result={'schema_version':'1.0','handoff_dir':str(out.resolve()),'conversion_executed':False,
            'required_skill':'image-to-editable-ppt','content_sha256':manifest['content_sha256'],
            'logo_path':str((out/'jjf-logo-master.png').resolve()),'logo_sha256':manifest['logo']['sha256'],
            'pages':mapping,'instruction':'Read the installed upstream SKILL.md and execute its real prepare/dispatch/record/finalize workflow. This JSON is a JJF handoff, not an upstream manifest. Preserve original JJF page numbers.'}
    if manifest['logo'].get('vector_path'):
        vector = inside(project, manifest['logo']['vector_path'])
        shutil.copy2(vector, out/'jjf-logo-primary.svg')
        result.update({'logo_vector_path': str((out/'jjf-logo-primary.svg').resolve()),
                       'logo_vector_sha256': manifest['logo']['vector_sha256']})
    save_json(out/'page_map.json',result)
    shutil.copy2(SKILL_ROOT/'prompts/conversion-handoff.md',out/'conversion-request.md')
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['init','validate','lock-content','register-preview','approve-preview','handoff']:
        p=sub.add_parser(name); p.add_argument('--project',required=True,type=Path)
        if name in ['lock-content','approve-preview']: p.add_argument('--evidence',required=True)
        if name in ['register-preview','approve-preview']: p.add_argument('--page',required=True,type=int)
        if name=='register-preview': p.add_argument('--image',required=True,type=Path)
        if name=='approve-preview':
            p.add_argument('--reviewer',choices=['user','delegated-design-lead'],required=True)
            p.add_argument('--visual-reviewed',action='store_true'); p.add_argument('--revision',type=int)
        if name=='handoff': p.add_argument('--pages',type=int,nargs='+')
    a=parser.parse_args(); project=a.project.resolve()
    try:
        if a.command=='init': result=init_project(project)
        elif a.command=='validate': result=validate(project)
        elif a.command=='lock-content': result=freeze_content(project,a.evidence)
        elif a.command=='register-preview': result=register_preview(project,a.page,a.image.resolve())
        elif a.command=='approve-preview': result=approve_preview(project,a.page,a.evidence,a.reviewer,a.visual_reviewed,a.revision)
        else: result=make_handoff(project,a.pages)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get('errors') else 0
    except (OSError,ValueError,KeyError,ImportError) as exc:
        print(json.dumps({'error':str(exc),'command':a.command},ensure_ascii=False),file=sys.stderr); return 2

if __name__=='__main__': raise SystemExit(main())

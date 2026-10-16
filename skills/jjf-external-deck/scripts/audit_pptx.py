#!/usr/bin/env python3
"""Inspect PPTX structure and known text. This never grants visual/edit interaction approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
import unicodedata
from xml.etree import ElementTree as ET
import zipfile

NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel':'http://schemas.openxmlformats.org/package/2006/relationships'}

def norm(text: str) -> str:
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',text))

def resolve_part(part: str,target: str) -> str:
    result=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(posixpath.dirname(part),target))
    if result.startswith('../'): raise ValueError('Invalid relationship target')
    return result

def relationships(z: zipfile.ZipFile,part: str) -> dict:
    name=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')
    if name not in z.namelist(): return {}
    root=ET.fromstring(z.read(name));items={}
    for rel in root:
        if rel.get('TargetMode')=='External': continue
        items[rel.get('Id')]={'target':resolve_part(part,rel.get('Target','')),'type':rel.get('Type','')}
    return items

def audit(path: Path,handoff: dict | None=None) -> dict:
    result={'input':str(path.resolve()),'structure_passed':False,'content_parity_passed':None,
            'release_ready':False,'errors':[],'warnings':[],'pages':[],
            'unperformed_checks':['visual_fidelity','logo_geometry','actual_edit_smoke_test','Canva_import'],
            'scope':'Supplementary structural check, not a full editable-PPT or design acceptance.'}
    errors=result['errors'];warnings=result['warnings']
    try:
        with zipfile.ZipFile(path) as z:
            bad=z.testzip()
            if bad: raise ValueError(f'Invalid compressed member: {bad}')
            for required in ['[Content_Types].xml','ppt/presentation.xml','_rels/.rels']:
                if required not in z.namelist(): raise ValueError(f'Missing package part: {required}')
            presentation=ET.fromstring(z.read('ppt/presentation.xml'))
            size=presentation.find('p:sldSz',NS)
            width,height=int(size.get('cx')),int(size.get('cy'))
            rels=relationships(z,'ppt/presentation.xml')
            ids=presentation.findall('p:sldIdLst/p:sldId',NS)
            expected=handoff.get('pages',[]) if handoff else None
            if expected is not None and len(expected)!=len(ids): errors.append('PAGE_COUNT_MISMATCH')
            missing_text=False
            for i,element in enumerate(ids):
                rid=element.get('{'+NS['r']+'}id')
                if rid not in rels: raise ValueError(f'Missing slide relationship: {rid}')
                part=rels[rid]['target'];root=ET.fromstring(z.read(part));srels=relationships(z,part)
                texts=[x.text or '' for x in root.findall('.//a:t',NS)]
                joined=''.join(texts)
                spec=expected[i] if expected is not None and i<len(expected) else {}
                p={'index':i+1,'source_page_id':spec.get('source_page_id'),
                   'native_text_shape_count':sum(1 for s in root.findall('.//p:sp',NS) if s.findall('.//a:t',NS)),
                   'shape_count':len(root.findall('.//p:sp',NS)),
                   'connector_count':len(root.findall('.//p:cxnSp',NS)),
                   'table_count':len(root.findall('.//a:tbl',NS)),
                   'picture_count':len(root.findall('.//p:pic',NS)),
                   'text':texts,'fonts':sorted({x.get('typeface') for tag in ['latin','ea','cs'] for x in root.findall('.//a:'+tag,NS) if x.get('typeface')}),
                   'missing_locked_text':[],'full_frame_images':[]}
                if not joined.strip(): errors.append(f'NO_NATIVE_TEXT:page_{i+1:03d}')
                for entry in root.findall('.//p:pic',NS):
                    blip=entry.find('.//a:blip',NS);xfrm=entry.find('p:spPr/a:xfrm',NS)
                    if blip is None: continue
                    image_id=blip.get('{'+NS['r']+'}embed')
                    rel=srels.get(image_id)
                    if not rel: errors.append(f'IMAGE_RELATIONSHIP:page_{i+1:03d}');continue
                    target=rel['target']
                    if target not in z.namelist():errors.append(f'MISSING_MEDIA:{target}');continue
                    media_sha=hashlib.sha256(z.read(target)).hexdigest()
                    full=False
                    if xfrm is not None:
                        ext=xfrm.find('a:ext',NS);off=xfrm.find('a:off',NS)
                        if ext is not None:
                            full=int(ext.get('cx'))/width>=.9 and int(ext.get('cy'))/height>=.9
                        if full and off is not None:
                            full=abs(int(off.get('x')))/width<=.1 and abs(int(off.get('y')))/height<=.1
                    if full:
                        p['full_frame_images'].append({'media':target,'sha256':media_sha})
                        if joined.strip() and media_sha==spec.get('source_sha256'):
                            errors.append(f'SOURCE_RASTER_OVERLAY:page_{i+1:03d}')
                        else:
                            warnings.append(f'FULL_FRAME_REQUIRES_VISUAL_REVIEW:page_{i+1:03d}')
                if expected is not None:
                    for t in spec.get('visible_text',[]):
                        if norm(t) and norm(t) not in norm(joined): p['missing_locked_text'].append(t)
                    if p['missing_locked_text']:
                        errors.append(f'CONTENT_PARITY:page_{i+1:03d}');missing_text=True
                result['pages'].append(p)
            if not ids: errors.append('EMPTY_DECK')
            if expected is None: warnings.append('NO_TEXT_LOCK:content parity not checked')
            else: result['content_parity_passed']=not missing_text and len(expected)==len(ids)
            result['structure_passed']=not [e for e in errors if not e.startswith('CONTENT_PARITY')]
    except (OSError,zipfile.BadZipFile,ET.ParseError,ValueError,KeyError,AttributeError,TypeError) as e:
        errors.append('INVALID_PPTX:'+str(e))
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pptx',type=Path)
    p.add_argument('--handoff',type=Path,help='JJF page_map.json from a real handoff')
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    h=json.loads(a.handoff.read_text(encoding='utf-8')) if a.handoff else None
    r=audit(a.pptx,h);text=json.dumps(r,ensure_ascii=False,indent=2)
    if a.out: a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text+'\n',encoding='utf-8')
    print(text)
    return 1 if r['errors'] else 0
if __name__=='__main__': raise SystemExit(main())

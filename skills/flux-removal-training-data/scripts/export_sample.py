"""Validate a local-paste result and export a lossless training triple."""
from pathlib import Path
import argparse,json,shutil,hashlib
import numpy as np
from PIL import Image
from local_paste import load_rgb,load_mask

def validate(original,target,obj,support):
    if original.shape!=target.shape: raise ValueError('Image dimensions differ')
    if obj.shape!=original.shape[:2] or support.shape!=obj.shape: raise ValueError('Mask dimensions differ')
    if not obj.any(): raise ValueError('Empty object mask')
    if np.any(obj & ~support): raise ValueError('Object not covered by paste support')
    if not np.array_equal(original[~support],target[~support]): raise ValueError('Exterior pixels changed')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True);p.add_argument('--paste-dir',required=True)
    p.add_argument('--out-dir',required=True);p.add_argument('--source-group',required=True)
    p.add_argument('--reviewed',action='store_true');p.add_argument('--provenance-json')
    a=p.parse_args();s=Path(a.paste_dir);d=Path(a.out_dir)
    if d.exists(): raise FileExistsError('Use a new sample directory')
    original=load_rgb(a.input);target=load_rgb(s/'target.png')
    obj=load_mask(s/'object_mask.png',original.shape[:2]);support=load_mask(s/'paste_support.png',original.shape[:2])
    for name in ['object_mask.png','paste_support.png']:
        with Image.open(s/name) as im:
            if not set(np.unique(np.asarray(im))).issubset({0,255}): raise ValueError('Mask is not binary')
    validate(original,target,obj,support)
    provenance=json.loads(Path(a.provenance_json).read_text(encoding='utf-8-sig')) if a.provenance_json else {}
    d.mkdir(parents=True)
    Image.fromarray(original).save(d/'input.png')
    for name in ['target.png','object_mask.png','shadow_mask.png','paste_core.png','paste_support.png','alpha.png','preview.jpg','report.json']:
        if (s/name).exists(): shutil.copyfile(s/name,d/name)
    hashes={n:hashlib.sha256((d/n).read_bytes()).hexdigest() for n in ['input.png','object_mask.png','target.png']}
    meta=dict(source_group=a.source_group,status='accepted' if a.reviewed else 'pending_review',
              width=original.shape[1],height=original.shape[0],outside_changed_pixels=0,hashes=hashes,provenance=provenance)
    (d/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False))
if __name__=='__main__':main()

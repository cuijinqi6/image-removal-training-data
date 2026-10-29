"""Prepare an EXIF-oriented working image and nearest-neighbor instance mask."""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
from PIL import Image, ImageOps
from local_paste import load_mask

def choose_size(w,h):
    ratio=4/3 if w>=h else 3/4
    if abs(w/h/ratio-1)>0.01:
        raise ValueError('Unvalidated aspect ratio; test stable output size before preparation')
    choices=[(875,656),(1168,876),(1771,1328),(2347,1760)]
    if w<h: choices=[(h,w) for w,h in choices]
    return min(choices,key=lambda s:(abs(s[0]*s[1]-w*h),s[0]*s[1]))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',required=True);p.add_argument('--annotation',required=True)
    p.add_argument('--instance-ids',type=int,nargs='+')
    p.add_argument('--size',type=int,nargs=2,metavar=('WIDTH','HEIGHT'),help='Explicit experimental size, not certified')
    p.add_argument('--out-dir',required=True);a=p.parse_args()
    with Image.open(a.image) as im: image=ImageOps.exif_transpose(im).convert('RGB')
    mask=load_mask(a.annotation,(image.height,image.width),a.instance_ids)
    if not mask.any(): raise ValueError('No pixels selected')
    size=tuple(a.size) if a.size else choose_size(image.width,image.height)
    if min(size)<1: raise ValueError('Positive size required')
    d=Path(a.out_dir);d.mkdir(parents=True,exist_ok=True)
    for name in ['input.png','object_mask.png','prepare.json']:
        if (d/name).exists(): raise FileExistsError(f'Refusing to overwrite {d/name}')
        if (d/name).resolve() in [Path(a.image).resolve(),Path(a.annotation).resolve()]: raise ValueError('Input collision')
    image.resize(size,Image.Resampling.LANCZOS).save(d/'input.png')
    Image.fromarray(mask.astype('uint8')*255).resize(size,Image.Resampling.NEAREST).save(d/'object_mask.png')
    meta=dict(source_size=list(image.size),working_size=list(size),scale_xy=[size[0]/image.width,size[1]/image.height],
        instance_ids=a.instance_ids,explicit_experimental_size=bool(a.size),annotation_coordinates='EXIF-oriented input',
        source_sha256=hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),annotation_sha256=hashlib.sha256(Path(a.annotation).read_bytes()).hexdigest())
    (d/'prepare.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps(meta))
if __name__=='__main__': main()

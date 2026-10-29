"""Composite a reviewed object+shadow removal into the unchanged source image.

Dependencies: pip install pillow numpy
Masks: white=selected, black=unselected. Coordinates must match the source.
No shadow detection or geometric registration is performed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def load_rgb(path):
    with Image.open(path) as im:
        return np.asarray(ImageOps.exif_transpose(im).convert('RGB')).copy()


def load_mask(path, shape, ids=None):
    with Image.open(path) as im:
        a = np.asarray(im)
    if a.shape[:2] != shape:
        raise ValueError(f'Mask dimensions {a.shape[:2]} do not match image {shape}: {path}')
    if ids is not None:
        # COCO RGB panoptic encoding, or a single-channel integer ID image.
        if a.ndim == 3:
            a = a.astype(np.int64)
            a = a[..., 0] + 256*a[..., 1] + 65536*a[..., 2]
        return np.isin(a, ids)
    if a.ndim == 3:
        if not np.all(a[..., :3] == a[..., :1]):
            raise ValueError('Colored label image requires --instance-ids; binary masks must be grayscale.')
        a = a[..., 0]
    return a >= 128


def grow(mask, radius):
    """Square/Chebyshev dilation in pixels; image boundaries are clipped."""
    if radius == 0:
        return mask.copy()
    im = Image.fromarray(mask.astype('uint8')*255)
    return np.asarray(im.filter(ImageFilter.MaxFilter(2*radius+1))) > 0


def make_alpha(core, padding, feather):
    # Entire supplied mask + padding is replaced at full opacity.
    core = grow(core, padding)
    alpha = core.astype(np.float32)
    # Feather ONLY outwards: never restore the old object/shadow inside core.
    if feather:
        expanded = core
        for radius in range(1, feather+1):
            expanded = grow(expanded, 1)
            shell = expanded & (alpha == 0)
            alpha[shell] = (feather+1-radius)/(feather+1)
    return core, alpha


def composite(original, generated, object_mask, shadow_mask, *, edit_mask=None,
              protect_mask=None, padding=4, feather=12, color_match=False):
    if original.shape != generated.shape or original.ndim != 3 or original.shape[2] != 3:
        raise ValueError('Original and FLUX images must have identical RGB dimensions; no implicit resize.')
    shape = original.shape[:2]
    for name, m in [('object', object_mask), ('shadow', shadow_mask),
                    ('edit', edit_mask), ('protect', protect_mask)]:
        if m is not None and m.shape != shape:
            raise ValueError(f'{name} mask size mismatch')
    if not object_mask.any():
        raise ValueError('Object mask is empty')
    if not 0 <= padding <= 128 or not 0 <= feather <= 128:
        raise ValueError('Padding and feather must be in [0,128]')
    required = object_mask | shadow_mask
    if edit_mask is not None and np.any(required & ~edit_mask):
        raise ValueError('Edit mask must contain all selected object and shadow pixels')
    core, alpha = make_alpha(required if edit_mask is None else edit_mask, padding, feather)
    if protect_mask is not None:
        if np.any(core & protect_mask):
            raise ValueError('Protected region overlaps full-replacement region; revise masks/padding')
        alpha[protect_mask] = 0
    support = alpha > 0
    # Background ring is diagnostic and optionally used for a robust RGB offset.
    ring = grow(support, max(8, feather)) & ~support
    if protect_mask is not None:
        ring &= ~protect_mask
    donor = generated.astype(np.float32)
    offset = np.zeros(3, dtype=np.float32)
    if color_match:
        if np.count_nonzero(ring) < 100:
            raise ValueError('Insufficient background pixels for color matching')
        offset = np.median(original[ring].astype(np.float32)-donor[ring], axis=0)
        offset = np.clip(offset, -20, 20)
        donor = np.clip(donor+offset, 0, 255)
    out = original.copy()
    a = alpha[support, None]
    out[support] = np.clip(np.rint(original[support]*(1-a)+donor[support]*a), 0, 255).astype('uint8')
    outside = ~support
    changed_outside = int(np.count_nonzero(np.any(out[outside] != original[outside], axis=1)))
    if changed_outside:
        raise AssertionError('Pixels outside composite support changed')
    ring_mae = float(np.abs(original[ring].astype(np.float32)-generated[ring]).mean()) if ring.any() else None
    report = dict(width=shape[1], height=shape[0], object_pixels=int(object_mask.sum()),
                  shadow_pixels=int(shadow_mask.sum()), full_replacement_pixels=int(core.sum()),
                  support_pixels=int(support.sum()), outside_changed_pixels=changed_outside,
                  original_flux_ring_rgb_mae=ring_mae, color_offset=offset.tolist(),
                  padding=padding, feather=feather,
                  alignment='Not automatically registered or certified; inspect edges and preview.',
                  shadow_annotation='Provided externally; no automatic shadow attribution.')
    return out, alpha, core, report


def save_preview(original, generated, target, obj, shadow, alpha, output):
    overlay = original.astype(np.float32)
    for m, color in [(obj, (255,70,70)), (shadow & ~obj, (70,120,255))]:
        overlay[m] = .55*overlay[m]+.45*np.array(color)
    from PIL import ImageDraw
    panels = [original, generated, overlay.astype('uint8'), target]
    labels = ['INPUT', 'FLUX RAW', 'RED: OBJECT / BLUE: SHADOW', 'LOCAL COMPOSITE']
    thumb_w = 360
    thumb_h = round(original.shape[0]*thumb_w/original.shape[1])
    sheet = Image.new('RGB', (thumb_w*4, thumb_h+34), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (panel, label) in enumerate(zip(panels, labels)):
        sheet.paste(Image.fromarray(panel).resize((thumb_w,thumb_h), Image.Resampling.LANCZOS), (i*thumb_w,34))
        draw.text((i*thumb_w+6,10),label,fill='black')
    sheet.save(output)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', required=True)
    p.add_argument('--flux', required=True)
    p.add_argument('--object-mask', required=True)
    p.add_argument('--instance-ids', type=int, nargs='+', help='IDs from integer or COCO RGB panoptic PNG')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--shadow-mask', help='Reviewed target shadow binary mask (can be empty for no shadow)')
    g.add_argument('--edit-mask', help='Reviewed object+shadow union mask')
    p.add_argument('--protect-mask', help='Optional binary mask of other instances/shadows to preserve')
    p.add_argument('--padding', type=int, default=4)
    p.add_argument('--feather', type=int, default=12)
    p.add_argument('--color-match', action='store_true', help='Optional clipped median RGB offset from outer ring')
    p.add_argument('--out-dir', required=True)
    args = p.parse_args()
    original, generated = load_rgb(args.original), load_rgb(args.flux)
    obj = load_mask(args.object_mask, original.shape[:2], args.instance_ids)
    shadow = load_mask(args.shadow_mask, original.shape[:2]) if args.shadow_mask else np.zeros_like(obj)
    edit = load_mask(args.edit_mask, original.shape[:2]) if args.edit_mask else None
    protect = load_mask(args.protect_mask, original.shape[:2]) if args.protect_mask else None
    target, alpha, core, report = composite(original, generated, obj, shadow, edit_mask=edit,
        protect_mask=protect, padding=args.padding, feather=args.feather, color_match=args.color_match)
    dest = Path(args.out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    # Do not overwrite any supplied input, even if it has an output filename.
    inputs = {Path(v).resolve() for v in [args.original,args.flux,args.object_mask,args.shadow_mask,args.edit_mask,args.protect_mask] if v}
    names = ['target.png','object_mask.png','shadow_mask.png','paste_core.png','paste_support.png','alpha.png','preview.jpg','report.json']
    if any((dest/n).resolve() in inputs for n in names):
        raise ValueError('Output directory would overwrite an input file; choose another directory')
    Image.fromarray(target).save(dest/'target.png')
    for name, mask in [('object_mask',obj),('shadow_mask',shadow),('paste_core',core),('paste_support',alpha>0)]:
        Image.fromarray(mask.astype('uint8')*255).save(dest/(name+'.png'))
    Image.fromarray(np.rint(alpha*255).astype('uint8')).save(dest/'alpha.png')
    # Reload lossless PNG and verify the invariant on the serialized artifact too.
    saved = load_rgb(dest/'target.png')
    assert np.array_equal(saved[alpha == 0],original[alpha == 0])
    report['inputs'] = {k:str(getattr(args,k)) for k in ['original','flux','object_mask','shadow_mask','edit_mask','protect_mask']}
    report['target_sha256'] = hashlib.sha256((dest/'target.png').read_bytes()).hexdigest()
    report['saved_png_outside_exact'] = True
    save_preview(original, generated, target, obj, shadow, alpha, dest/'preview.jpg')
    (dest/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()

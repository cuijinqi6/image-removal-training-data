"""Read-only batch inventory; file checks never imply visual acceptance."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json
import numpy as np
from PIL import Image

ACTIVE = {'prepared','awaiting_upload','uploaded','submitting','generating','downloaded',
          'pending_visual_review','pending_shadow_audit','generation_error_pending_retry'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect_batch(state_dir, output_dir, verify_files=False):
    state_dir, output_dir = Path(state_dir), Path(output_dir)
    if not state_dir.is_dir():
        raise FileNotFoundError(state_dir)
    rows, errors = [], []
    for path in sorted(state_dir.glob('*.json')):
        if not path.stem.isdigit():
            continue
        s = json.loads(path.read_text(encoding='utf-8-sig'))
        sid = str(s.get('id', path.stem))
        if sid != path.stem:
            errors.append(f'{path.name}: id mismatch')
            continue
        row = dict(id=sid, stage=s.get('stage','missing_stage'), attempt=s.get('attempt'),
                   raw_candidate_attempt=s.get('raw_candidate_attempt'),
                   reason=s.get('review_status',s.get('last_error','')))
        rows.append(row)
        if row['stage'] != 'accepted' or not verify_files:
            continue
        problems = []
        try:
            files = {d:output_dir/d/(sid+('.jpg' if d=='comparison' else '.png'))
                     for d in ['input','mask','target','comparison']}
            if not all(p.is_file() for p in files.values()):
                raise ValueError('Incomplete four-directory sample')
            hashes = {d:digest(files[d]) for d in ['input','mask','target']}
            if hashes != {d:s.get('hashes',{}).get(d) for d in hashes}:
                problems.append('Current file hashes differ from recorded hashes')
            for flag in ['association_ambiguity_pending','shadow_identity_ambiguity_pending','mask_identity_ambiguity_pending']:
                if s.get(flag):problems.append(flag)
            audit = s.get('mask_audit',{})
            if audit.get('input_sha256')!=hashes['input'] or audit.get('mask_sha256')!=hashes['mask']:
                problems.append('Source-mask audit absent or stale')
            for name in ['shadow_audit','residual_check']:
                if s.get(name,{}).get('target_sha256')!=hashes['target']:
                    problems.append(name+' absent or stale')
            if s.get('outside_changed_pixels')!=0:problems.append('Recorded exterior invariant absent or nonzero')
            a=np.asarray(Image.open(files['input']).convert('RGB'))
            t=np.asarray(Image.open(files['target']).convert('RGB'))
            m=np.asarray(Image.open(files['mask']))
            support_path=state_dir/(sid+'-support.png')
            if not support_path.is_file():raise ValueError('Missing support evidence')
            support=np.asarray(Image.open(support_path).convert('L'))>0
            if a.shape!=t.shape or m.shape!=a.shape[:2] or support.shape!=m.shape:
                raise ValueError('Dimensions differ')
            if not set(np.unique(m)).issubset({0,255}) or not np.any(m):
                problems.append('Entity mask is nonbinary or empty')
            if np.any((m>0)&~support):problems.append('Entity mask outside support')
            if not np.array_equal(a[~support],t[~support]):problems.append('Exterior pixels changed')
        except (OSError, ValueError, KeyError) as exc:
            problems.append(str(exc))
        errors.extend(f'{sid}: {problem}' for problem in problems)
    if not rows:raise ValueError('No numeric per-sample state files found')
    return dict(samples=len(rows), states=dict(Counter(r['stage'] for r in rows)),
                active_ids=[r['id'] for r in rows if r['stage'] in ACTIVE],
                unknown_submission_ids=[r['id'] for r in rows if r['stage']=='unknown_submission'],
                accepted_ids=[r['id'] for r in rows if r['stage']=='accepted'],
                verified_files=verify_files, errors=errors, samples_detail=rows,
                limitation='Checks existing records and pixels only; does not establish visual quality or reclassify samples.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir',required=True);p.add_argument('--output-dir',required=True)
    p.add_argument('--verify-files',action='store_true');p.add_argument('--report')
    a=p.parse_args();report=inspect_batch(a.state_dir,a.output_dir,a.verify_files)
    if a.report:
        path=Path(a.report)
        # A report may never overwrite inputs, state or training images.
        if path.suffix.lower()!='.json':raise ValueError('Report must use a .json extension')
        state_root=Path(a.state_dir).resolve();data_root=Path(a.output_dir).resolve()
        if path.resolve().is_relative_to(state_root) or path.resolve().is_relative_to(data_root):
            raise ValueError('Write report outside state and dataset directories')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='samples_detail'},ensure_ascii=False))
    if report['errors']:raise SystemExit(1)

if __name__=='__main__':main()

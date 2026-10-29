from pathlib import Path
import sys,tempfile,subprocess,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_sample import choose_size
from local_paste import composite,load_mask
from export_sample import validate
from audit_resume import inspect_batch, digest

def run():
    assert choose_size(1707,1280)==(1771,1328)
    assert choose_size(1280,1707)==(1328,1771)
    try:choose_size(1920,1080)
    except ValueError:pass
    else:raise AssertionError('unsupported aspect accepted')
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);ids=np.zeros((60,80),np.uint16);ids[10:25,20:30]=12;ids[30:40,40:50]=18
        Image.fromarray(ids).save(d/'ids.png')
        mask=load_mask(d/'ids.png',ids.shape,[12,18]);assert mask.sum()==250
        rgb=np.stack([ids%256,ids//256,ids*0],axis=-1).astype('uint8');Image.fromarray(rgb).save(d/'rgb.png')
        assert np.array_equal(load_mask(d/'rgb.png',ids.shape,[12,18]),mask)
        a=np.full((60,80,3),60,np.uint8);b=np.full_like(a,180)
        shadow=np.zeros_like(mask);shadow[40:48,20:50]=1
        out,alpha,core,report=composite(a,b,mask,shadow,padding=2,feather=4)
        assert np.array_equal(out[core],b[core]);assert np.all(alpha[mask|shadow]==1)
        assert np.any((alpha>0)&(alpha<1));validate(a,out,mask,alpha>0)
        Image.fromarray(out).save(d/'saved.png');assert np.array_equal(np.asarray(Image.open(d/'saved.png'))[alpha==0],a[alpha==0])
        for opts in [dict(protect_mask=mask),dict(generated=b[:30]),dict(object_mask=np.zeros_like(mask))]:
            kw=dict(original=a,generated=b,object_mask=mask,shadow_mask=shadow);kw.update(opts)
            try:composite(**kw)
            except ValueError:pass
            else:raise AssertionError('invalid inputs accepted')
        Image.fromarray(a).save(d/'source.png');Image.fromarray(b).save(d/'flux.png')
        Image.fromarray(mask.astype('uint8')*255).save(d/'object.png');Image.fromarray(shadow.astype('uint8')*255).save(d/'shadow.png')
        def cli(script,*args):subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],check=True,stdout=subprocess.PIPE)
        cli('prepare_sample.py','--image',d/'source.png','--annotation',d/'ids.png','--instance-ids','12','18','--size','40','30','--out-dir',d/'prepared')
        assert set(np.unique(np.asarray(Image.open(d/'prepared/object_mask.png'))))=={0,255}
        cli('local_paste.py','--original',d/'source.png','--flux',d/'flux.png','--object-mask',d/'object.png','--shadow-mask',d/'shadow.png','--out-dir',d/'paste')
        cli('export_sample.py','--input',d/'source.png','--paste-dir',d/'paste','--out-dir',d/'sample','--source-group','synthetic')
        assert json.loads((d/'sample/metadata.json').read_text())['status']=='pending_review'
        states=d/'states';data=d/'batch';states.mkdir();data.mkdir()
        for kind in ['input','mask','target','comparison']:(data/kind).mkdir()
        Image.fromarray(a).save(data/'input/001.png');Image.fromarray(mask.astype('uint8')*255).save(data/'mask/001.png')
        Image.fromarray(out).save(data/'target/001.png');Image.fromarray(out).save(data/'comparison/001.jpg')
        Image.fromarray((alpha>0).astype('uint8')*255).save(states/'001-support.png')
        hashes={k:digest(data/k/'001.png') for k in ['input','mask','target']}
        st=dict(id='001',stage='accepted',hashes=hashes,outside_changed_pixels=0,
                mask_audit=dict(input_sha256=hashes['input'],mask_sha256=hashes['mask']),
                residual_check=dict(target_sha256=hashes['target']),shadow_audit=dict(target_sha256=hashes['target']))
        state_file=states/'001.json';state_file.write_text(json.dumps(st))
        assert not inspect_batch(states,data,True)['errors']
        st['shadow_audit']['target_sha256']='stale';state_file.write_text(json.dumps(st))
        assert any('shadow_audit' in x for x in inspect_batch(states,data,True)['errors'])
        assert json.loads(state_file.read_text())['stage']=='accepted','Audit must not mutate states'
        st['stage']='unknown_submission';state_file.write_text(json.dumps(st))
        assert inspect_batch(states,data,True)['unknown_submission_ids']==['001']
    print('PASS: masks, resize, compositing, rejected inputs, CLI export, read-only resume checks')
if __name__=='__main__':run()

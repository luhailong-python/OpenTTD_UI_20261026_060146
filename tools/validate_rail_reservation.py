"""Verify true track ownership,unchanged ground,Alpha and reservation state matrix."""
from pathlib import Path
from PIL import Image
import json,numpy as np
import world_pack as wp
from build_rail_reservation import normalized,ground,KINDS,TRACKS,CODES
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 mp=R/'assets/world/overlays/rail-reservation/manifest.json';m=load(mp);checks=[];vrp=R/'records/rail-reservation-visual-review.json';vr=load(vrp)if vrp.is_file()else{};reviewed={a['file']:a['sha256']for a in vr.get('reviewedAssets',[])}
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 actual={(a['sourceRequirementIds'][0].removeprefix('rail-'),a['trackBit'],a['slopeCode'])for a in m['assets']};test('complete120track-tech-slope-matrix',actual=={(k,b,c)for k in KINDS for b in range(6)for c in CODES}and len(m['assets'])==120)
 for s in m['sourceFiles']:test('current-code-source',wp.sha(R/s['file'])==s['sha256'],file=s['file'])
 for a in m['assets']:
  p=R/a['image'];im=Image.open(p);ar=np.array(im);src=np.array(normalized(a['sourceOverlay']['file'],a['slopeCode']));alpha=src[...,3];lum=np.rint((.2126*src[...,0]+.7152*src[...,1]+.0722*src[...,2])*.58).astype('uint8');test(a['id']+'.only-track-overlay-input',a['sourceLayer']=='track-overlay'and'composite'not in a['sourceOverlay']['file']);test(a['id']+'.source-current-sha',wp.sha(R/a['sourceOverlay']['file'])==a['sourceOverlay']['sha256']);test(a['id']+'.output-current-sha',wp.sha(p)==a['sha256']);test(a['id']+'.fixedRGBAcanvas-anchor',im.mode=='RGBA'and im.size==(256,192)and a['anchorPx']==[128,128]);test(a['id']+'.exact-sourceAlpha-ownership',np.array_equal(ar[...,3],alpha));test(a['id']+'.no-fill-outside-ownership',np.all(ar[alpha==0]==0));test(a['id']+'.exact-gray-material',all(np.array_equal(ar[alpha>0,c],lum[alpha>0])for c in range(3)))
  g,_=ground(a['slopeCode']);normal=g.copy();normal.alpha_composite(Image.fromarray(src));reserved=normal.copy();reserved.alpha_composite(im);test(a['id']+'.terrain-unchanged-outside-track',np.array_equal(np.array(normal)[alpha==0],np.array(reserved)[alpha==0]));test(a['id']+'.current-actual-visual-review',reviewed.get(a['image'])==a['sha256'])
 fail=[x for x in checks if not x['passed']];r={'createdAt':wp.now(),'formalPNGCount':120,'passed':sum(x['passed']for x in checks),'failed':len(fail),'failures':fail,'complete':not fail,'manifest':wp.rel(mp),'manifestSHA256':wp.sha(mp),'scope':'4technologies×6actual source track overlays×5surfaces;exact source Alpha,gray-only-ownedRGB,ground unchanged outside ownership,current source/output/visual hashes;no new native painting','visualRecord':'records/rail-reservation-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/rail-reservation-validation.json',r);print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()

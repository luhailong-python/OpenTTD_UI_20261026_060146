"""Check current service art pixels, source hashes, assembly and frame contracts."""
from pathlib import Path
from PIL import Image
import json, collections, hashlib
import world_pack as wp
R=wp.ROOT
PACKS=['objects','waterworks','signals','signal-views','fences-shore','object-states','signal-states','fence-foundation-states','foundations','water-states','mechanics','fountain-animation','water-stations']
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 checks=[];packs=[];assets={};clips=[];sources={}
 def check(test,ok,**extra):checks.append({'test':test,'passed':bool(ok),**extra})
 def source(v,owner):
  if isinstance(v,list):
   for z in v:source(z,owner)
  elif isinstance(v,dict):
   if v.get('file') and v.get('sha256'):
    p=R/v['file'];key=(v['file'],v['sha256'])
    if key not in sources:
     sources[key]=True;check('current-source-sha',p.is_file() and wp.sha(p)==v['sha256'],file=v['file'],owner=owner)
   for key in ['derivedFrom','sources']:source(v.get(key,[]),owner)
 for name in PACKS:
  mp=R/'assets/world/infrastructure'/name/'manifest.json';q=load(mp);packs.append({'file':wp.rel(mp),'sha256':wp.sha(mp),'assets':len(q.get('assets',[]))});clips+=q.get('animations',[])
  for a in q.get('assets',[]):
   f=a['image'];p=R/f;im=Image.open(p);alpha=im.getchannel('A') if im.mode=='RGBA' else None;assets[f]=a
   for test,ok in [('PNG',im.format=='PNG'),('RGBA',im.mode=='RGBA'),('canvas',im.size==(a['width'],a['height'])),('sha',wp.sha(p)==a['sha256']),('transparent',alpha is not None and alpha.getextrema()[0]==0),('nonempty',alpha is not None and alpha.getbbox() is not None),('anchor',len(a['anchorPx'])==2 and 0<=a['anchorPx'][0]<=im.width and 0<=a['anchorPx'][1]<=im.height),('no-native-upscale',not a.get('nativeUpscale')),('no-false-model',a.get('actualModel') is None and a.get('actualQuality') is None)]:check(test,ok,file=f)
   source(a.get('derivedFrom',[]),f)
   dp=Path(str(p)+'.derivation.json');check('derivation-record',dp.is_file(),file=f)
   if dp.is_file():
    d=load(dp);check('derivation-current-sha',d.get('sha256')==a['sha256'],file=f)
  for z in q.get('qa',[]):
   if z.get('level') in ['WARN','FAIL']:check('inherited-pack-qa',False,manifest=wp.rel(mp),detail=z)
 for c in clips:
  frames=c['frames'];ims=[Image.open(R/f) for f in frames];shas=[wp.sha(R/f) for f in frames];dur=c.get('durationsMs',[])
  check('frame-existence',all((R/f).is_file() for f in frames),clip=c['id'])
  check('frame-canvas',len({i.size for i in ims})==1 and (not c.get('frameSize')or list(ims[0].size)==c['frameSize']),clip=c['id'])
  check('frame-timing',len(dur)==len(frames) and all(x>0 for x in dur),clip=c['id'])
  check('real-changing-frames',len(set(shas))>1,clip=c['id'])
  check('fixed-anchor',bool(c.get('fixedAnchorPx')),clip=c['id'])
  for f in frames:
   if f in assets:check('frame-anchor-equal',list(assets[f]['anchorPx'])==list(c['fixedAnchorPx']),clip=c['id'],file=f)
 for name in ['object-states','mechanics']:
  q=load(R/'assets/world/infrastructure'/name/'manifest.json')
  for m in q.get('coverageMappings',[]):
   if m.get('requirementId')=='water-lock' and m.get('whole'):
    whole=m['whole'];parts=[f for f in m['files'] if f!=whole]
   elif m.get('requirementId')=='object-headquarters' and m.get('level'):
    whole=m['files'][0];parts=m['files'][1:]
   else:continue
   target=Image.open(R/whole).convert('RGBA');assembled=Image.new('RGBA',target.size)
   for f in parts:assembled.alpha_composite(Image.open(R/f).convert('RGBA'))
   check('exact-complementary-RGBA',assembled.tobytes()==target.tobytes(),whole=whole,parts=parts)
 q=load(R/'assets/world/infrastructure/foundations/manifest.json');cases=q['coverageMappings'][0]['caseBindings']
 check('Foundation14modes',len({c['mode'] for c in cases})==14)
 for c in cases:
  if not c.get('whole'):continue
  for f in c.get('supportFaces',[]):check('foundation-nonnegative-support',all(h>=0 for h in f['heightPixels']),mode=c['mode'],slopeCode=c['slopeCode'])
 counts=collections.Counter(x['passed'] for x in checks)
 report={'createdAt':wp.now(),'scope':'Current service PNGs, true Alpha, source SHA, fixed canvases/anchors, changing frame clips, exact HQ/lock complementary RGBA reassembly and Foundation mode geometry. Manual artwork review is separate.','formalPNGCount':len(assets),'animationCount':len(clips),'passed':counts[True],'failures':counts[False],'warnings':0,'issues':[x for x in checks if not x['passed']],'sourceManifests':packs,'sourceChecks':len(sources),'unityValidated':False,'actualModel':None,'actualQuality':None}
 wp.writej(R/'records/world-production/services-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

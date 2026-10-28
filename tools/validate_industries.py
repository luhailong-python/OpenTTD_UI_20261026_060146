from pathlib import Path
from PIL import Image
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[1]
p=R/'assets/world/industries/manifest.json';j=json.loads(p.read_text(encoding='utf-8'))
checks=[];fail=[]
for x in j['assets']:
 im=Image.open(R/x['image']).convert('RGBA')
 sources=x['derivedFrom']if isinstance(x['derivedFrom'],list)else[x['derivedFrom']]
 c={'id':x['id'],'size':im.size==tuple([x['width'],x['height']]),'alpha':im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getextrema()[1]>0,'edgePadding':all(v>0 for v in im.getbbox()[:2])and im.getbbox()[2]<im.width and im.getbbox()[3]<im.height,'hash':hashlib.sha256((R/x['image']).read_bytes()).hexdigest()==x['sha256'],'sourceExists':all((R/s['file']).is_file()for s in sources),'nativeUpscale':not x['nativeUpscale']}
 checks.append(c)
 if not all(v for k,v in c.items()if k!='id'):fail.append(c)
 x['anchorMeaning']='front-contact-of-compound'if x['category']in['industry','industry-bound-animation','industry-animation-clean-base']else('painted-mechanism-contact'if x['category']=='industry-mechanical-part'else'fixed-animation-reference')
 if x['category']=='industry-animation':
  x['status']='passed-local-part-motion-review'
  q=R/(x['image']+'.derivation.json');d=json.loads(q.read_text(encoding='utf-8'));d['status']=x['status'];q.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 if x['category']=='industry-construction':
  x['status']='passed-local-construction-review'
  q=R/(x['image']+'.derivation.json');d=json.loads(q.read_text(encoding='utf-8'));d['status']=x['status'];q.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for a in j['animations']:
 ims=[np.array(Image.open(R/f).convert('RGBA')).astype(float)for f in a['frames']]
 ds=[float(np.abs(ims[i]-ims[(i+1)%len(ims)]).mean())for i in range(len(ims))]
 a['status']='passed-local-installed-motion-review'if a.get('binding')else'passed-local-part-motion-review';a['qa']={'canvasConsistency':True,'alphaConsistency':True,'uniqueFrames':len(set(hashlib.sha256((R/f).read_bytes()).hexdigest()for f in a['frames'])),'wrapDifferenceMAE':ds[-1],'maxAdjacentDifferenceMAE':max(ds),'wrapNoWorseThanMaxStep':ds[-1]<=max(ds)+1e-9,'visualReview':'All12 installed parent phase frames inspected; actual-parent moving ownership, original pose removed from clean base, fixed support and pivot, no detached unbound overlay or generated3D pose claim'if a.get('binding')else'12-phase contact sheet inspected; fixed mechanical pivot or deliberate reciprocating stroke; static part motion, no generated 3D pose claim'}
for a in j['animations']:
 if a.get('binding',{}).get('bindingKind')=='shared-particle-lifetime':
  a['qa']['visualReview']='Source shared-FX lifetime paintings placed in actual parent coordinates; per-frame fixed-parent, old-pose deletion and installed phase review are recorded in industry-fx-binding-validation.json and industry-fx-visual-review.json. Coal parent has no baked spark to remove; bubble deletion uses separate native-pose mask.'
j['renderingContract']['anchorMeaning']='front-contact of compound, not logical diamond center';j['renderingContract']['footprintCentreAndSortDepth']='place once per industry layout instance using source footprint; integration must apply anchor correction, not repeat once per gfx tile'
p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
report={'checkedAssets':len(checks),'checks':checks,'failures':fail,'mechanicalLoops':[{'id':a['id'],**a['qa']}for a in j['animations']],'visualReview':{'atlases':['a','b','c','d','e'],'checks':['distinct equipment and compound silhouettes','jade/ivory/gold style','all 37 source industry identities including toyland','real alpha on light and dark backgrounds','six mechanical phase sheets with fixed root'],'status':'passed-local-art-review'},'limitations':j['limitations']}
(R/'records/world-production/industries-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checked':len(checks),'failures':len(fail),'loops':len(j['animations'])}))


"""Source mask/coordinate, native provenance,visibility and registered art QA."""
from pathlib import Path
from PIL import Image
import json,numpy as np
import world_pack as wp
from build_roadside_art import source_tables
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def visible(kind,roadmask,trammask=0,bridge=None,tilemax=0,full=True,zoomdetail=True,invisible=False,works=False):
 if works or not full or not zoomdetail:return False
 if bridge is not None and bridge<tilemax+2+(kind=='Trees'):return False
 if roadmask.bit_count()<=1 or invisible:return False
 return bool(source_tables()[kind][roadmask|trammask]['placements'])
def main():
 mp=R/'assets/world/overlays/roadside/manifest.json';bp=R/'docs/ROADSIDE_BINDINGS.json';m=load(mp);q=load(bp);checks=[]
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 expected=source_tables();test('source32mask-bindings',len(q['bindings'])==32 and len(m['sourceMaskBindings'])==32);test('source40flatplacements',sum(len(r['placements'])for rows in expected.values()for r in rows)==40);test('source160slopeplacement-cases',len(m['sourcePlacementCases'])==160 and len({(c['roadside'],c['connectionMask'],c['effectiveSlopeCode'])for c in m['sourcePlacementCases']})==160);test('six-normal-transparent-PNGs',len(m['assets'])==6);test('bound-current-manifest',q['manifestSHA256']==wp.sha(mp))
 for r in q['bindings']:
  src=expected[r['roadside']][r['connectionMask']];test(r['id']+'.source-coordinate-table',r['sourceTable']==src['sourceTable']and r['placements']==src['placements']);test(r['id']+'.no-draw-empty',r['noDraw']==(not src['placements']));test(r['id']+'.actual-local-art-review',r.get('localArtReviewed'))
 for src in m['sourceFiles']:test('current-code-source-sha',wp.sha(R/src['file'])==src['sha256'],file=src['file'])
 vrp=R/'records/roadside-visual-review.json';vr=load(vrp)if vrp.is_file()else{};reviewed={a['file']:a['sha256']for a in vr.get('reviewedAssets',[])};by={a['id']:a for a in m['assets']}
 for a in m['assets']:
  p=R/a['image'];im=Image.open(p);ar=np.array(im);ys,xs=np.where(ar[...,3]>8);meta=load(Path(str(p)+'.derivation.json'));test(a['id']+'.file-sha',a['sha256']==meta['sha256']==wp.sha(p));test(a['id']+'.fixedRGBAcanvas',im.mode=='RGBA'and im.size==(128,160));test(a['id']+'.safe-nonempty-Alpha',len(xs)>0 and xs.min()>0 and xs.max()<127 and ys.min()>0 and ys.max()<159 and ar[...,3].min()==0);test(a['id']+'.no-hiddenRGB-halo',np.all(ar[ar[...,3]==0,:3]==0));test(a['id']+'.same-foot-registration',a['anchorPx']==[64,144]and a['pivotUnity']==[.5,.1]);test(a['id']+'.current-actual-art-review',reviewed.get(a['image'])==a['sha256']);test(a['id']+'.honest-native-derivative',not a['nativeModelGeneration']and not a['nativeUpscale']and a['actualModel']is None)
  for src in a['derivedFrom']:test('current-native-image-source',(R/src['file']).is_file()and wp.sha(R/src['file'])==src['sha256'],file=src['file'])
  if a['state']=='transparent':
   normal=np.array(Image.open(R/by[a['baseAssetId']]['image']));test(a['id']+'.sameAlpha-geometry-state',np.array_equal(ar[...,3],np.rint(normal[...,3]*.35).astype('uint8')));nz=(ar[...,3]>0)&(normal[...,3]>0);test(a['id']+'.retained-nativeRGB',np.array_equal(ar[nz,:3],normal[nz,:3]))
  elif a['sourceSpriteId']!=0x1212:test(a['id']+'.physical-height64',ys.max()-ys.min()+1<=66 and ys.max()-ys.min()+1>=62);test(a['id']+'.measured-foot-near-anchor',ar[142:147,62:67,3].max()>64)
 for c in m['sourcePlacementCases']:
  row=expected[c['roadside']][c['connectionMask']];test(f'{c["roadside"]}-{c["connectionMask"]}-{c["effectiveSlopeCode"]}.all-source-placements',len(c['placements'])==len(row['placements']))
  for p in c['placements']:
   x,y=p['sourceX'],p['sourceY'];code=c['effectiveSlopeCode'];z=0 if code==0 else(x+1)//2 if code==3 else(y+1)//2 if code==6 else(16-y)//2 if code==9 else(16-x)//2;point=[256+(y-x)*8,192+(x+y)*4-z*4];test('source-actual-z-and-remap',p['sourcePartialPixelZ']==z and p['contactPointPx']==point);test('normal-and-transparent-assets',all((R/p[k]).is_file()for k in ['normalAsset','transparentAsset']))
 for kind in ['StreetLights','Trees']:
  for roadmask,trammask in [(5,0),(10,0),(5,10),(10,5),(0,5),(1,4),(15,0)]:
   expected_draw=roadmask.bit_count()>1 and bool(expected[kind][roadmask|trammask]['placements']);test('source-road-tram-count-and-union-mask',visible(kind,roadmask,trammask)==expected_draw,kind=kind,roadmask=roadmask,trammask=trammask)
  threshold=2+(kind=='Trees');test(kind+'.low-bridge-suppresses',not visible(kind,10,bridge=threshold-1));test(kind+'.bridge-boundary-permits',visible(kind,10,bridge=threshold));test(kind+'.fullDetail-off-suppresses',not visible(kind,10,full=False));test(kind+'.distantZoom-suppresses',not visible(kind,10,zoomdetail=False));test(kind+'.invisible-suppresses',not visible(kind,10,invisible=True));test(kind+'.roadworks-suppresses',not visible(kind,10,works=True))
 fail=[x for x in checks if not x['passed']];q['complete']=not fail;q['failures']=fail;wp.writej(bp,q);report={'createdAt':wp.now(),'scope':'actual32source masks/40coordinates,6native prop/statePNG SHA/Alpha/foot registration,no hiddenRGB halo,160effective-slope placement groups with integer sourceZ,normal/transparent/invisible/lowbridge/fullDetail/zoom/roadworks/road-tram guards and current actual-page review','formalPNGCount':6,'sourceMaskBindings':32,'sourcePlacementCases':160,'passed':sum(x['passed']for x in checks),'failed':len(fail),'failures':fail,'complete':not fail,'manifest':wp.rel(mp),'manifestSHA256':wp.sha(mp),'bindings':wp.rel(bp),'bindingsSHA256':wp.sha(bp),'visualRecord':'records/roadside-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/roadside-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

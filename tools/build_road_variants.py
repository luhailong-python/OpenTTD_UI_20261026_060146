"""Current native road/tram paint on four painted ground contexts and four slopes.
All colour pixels are sampled from adopted paintings; geometry/Alpha are derivatives.
"""
from pathlib import Path
from PIL import Image,ImageFilter
import json,numpy as np
import world_pack as wp
import build_world_terrain as t
import build_world_services as s
R=wp.ROOT;OUT='assets/world/infrastructure/road-variants';CONTEXTS=['rural','town-pavement','snow','desert'];SLOPES=[(0,'flat'),(3,'sw'),(6,'se'),(9,'nw'),(12,'ne')]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(a):return{'file':a['image'],'sha256':a['sha256'],'record':a['image']+'.derivation.json'}
def raw_uv(path,under):
 raw=Image.open(path).convert('RGBA').transform((192,192),Image.Transform.QUAD,(128,1,1,64,128,127,255,64),Image.Resampling.BICUBIC)
 b=under.copy().convert('RGBA');b.alpha_composite(raw);return b
def main():
 road=load(R/'assets/world/infrastructure/roads/manifest.json');terrain=load(R/'assets/world/terrain/manifest.json');ground={a['id']:a for a in terrain['assets']};by={a['id']:a for a in road['assets']};grass=ground['terrain-grass-flat'];grassUV=t.unwrap(Image.open(R/grass['image']).convert('RGBA'),[[128,1],[255,64],[128,127],[1,64]])
 # A literal2x2 repeat of an unmarked native paving region, never enlarged.
 plaza=raw_uv(R/by['road-mask-00']['image'],grassUV).crop((48,48,144,144));paving=Image.new('RGBA',(192,192))
 for x in [0,96]:
  for y in [0,96]:paving.alpha_composite(plaza,(x,y))
 grounds={'rural':grassUV.convert('RGBA'),'town-pavement':paving,'snow':raw_uv(R/ground['terrain-snow-flat']['image'],grassUV),'desert':raw_uv(R/ground['terrain-desert-flat']['image'],grassUV)}
 greferences={'rural':ref(grass),'town-pavement':ref(by['road-mask-00']),'snow':ref(ground['terrain-snow-flat']),'desert':ref(ground['terrain-desert-flat'])}
 foundations=load(R/'assets/world/infrastructure/foundations/manifest.json')['coverageMappings'][0]['caseBindings'];assets=[];maps=[];qa=[];records=[]
 wire=load(R/'assets/world/infrastructure/rail/manifest.json');overhead=[a['image']for a in wire['assets']if a['id']in ['rail-catenary-post-left','rail-catenary-post-right','rail-catenary-wire-left','rail-catenary-wire-right']]
 for kind in ['road','tram']:
  req='road-'+kind;states=[];laneAssets=[];masks=range(16)if kind=='road'else range(1,16)
  for mask in masks:
   native=by[kind+'-mask-'+format(mask,'02d')];uv=raw_uv(R/native['image'],grassUV);rgb=np.asarray(uv)[...,:3].astype(float);rr,gg,bb=np.moveaxis(rgb,-1,0)
   # Only green vegetation becomes transparent; warm stone, gold rails,
   # road markings, flowers and native curb pixels keep their original RGB.
   vegetation=np.clip((gg-np.maximum(rr,bb)-1)/12,0,1);lane=uv.copy();lane.putalpha(Image.fromarray(np.uint8(np.rint((1-vegetation)*255))).filter(ImageFilter.GaussianBlur(.45)))
   lp=t.project(lane);canvas=Image.new('RGBA',(256,192));canvas.alpha_composite(lp,(0,64));la=s.emit(OUT,kind+'-lane-mask-'+format(mask,'02d'),canvas,[ref(native)],'actual native road/tram colour pixels; green-vegetation Alpha separation only; original native paint RGB unchanged; UV reprojection, fixed256x192canvas; no new painting',{'category':'road-lane','connectionMask':mask,'sourceRequirementIds':[req],'layer':'lane','slopeCode':0,'status':'produced-needs-context-review'},[128,128]);assets.append(la);laneAssets.append(la['image'])
   for context in CONTEXTS:
    composed=grounds[context].copy();composed.alpha_composite(lane);flat=t.project(composed)
    for code,name in SLOPES:
     if code:im,points,heights=wp.projected_slope(flat,code)
     else:im=Image.new('RGBA',(256,192));im.alpha_composite(flat,(0,64));points={k:[x,y+64]for k,(x,y)in wp.FLAT_POINTS.items()};heights=wp.corner_heights(0)
     ident=kind+'-'+context+'-mask-'+format(mask,'02d')+'-slope-'+name
     op='actual native road/tram lane Alpha over actual painted '+context+' ground; '+('native unmarked paving96x96UV region repeated2x2 without enlargement; 'if context=='town-pavement'else '')+'piecewise-affine source-corner height projection, shared fixedcanvas/anchor; no new native detail'
     en=s.emit(OUT,ident,im,[ref(native),greferences[context]],op,{'category':'road-context','sourceRequirementIds':[req],'connectionMask':mask,'connectedPorts':native.get('connectedPorts',[]),'surfaceContext':context,'slopeCode':code,'slopeName':name,'cornerHeightUnits':heights,'cornerPixels':{k:list(v)for k,v in points.items()},'heightStepPixels':32,'laneSource':la['image'],'status':'produced-needs-context-review','drawRule':'draw whole context tile OR separate source lane over matching ground; do not double-render','nativeUpscale':False},[128,128]);assets.append(en)
     support=[{'mode':c['mode'],'whole':c['whole'],'sideLayer':c.get('sideLayer')}for c in foundations if c['slopeCode']==code and c.get('whole')and c['mode']in ['InclinedX','InclinedY','Leveled']]
     states.append({'connectionMask':mask,'surfaceContext':context,'slopeCode':code,'image':en['image'],'layer':'ground+lane','anchorPx':[128,128],'foundationCandidates':support,'foundationUse':'When a world height boundary exposes a side, choose matching Foundation source mode; terrain height and neighbour adjacency decide, Unity pending.'})
  maps.append({'requirementId':req,'files':[a['image']for a in assets if req in a['sourceRequirementIds']],'states':states,'connectivityMasks':list(masks),'surfaceContexts':CONTEXTS,'slopeCodes':[c for c,n in SLOPES],'slopeDirections':4,'layerCanvas':[256,192],'anchorPx':[128,128],'overheadSeparateAssets':overhead if kind=='tram'else[],'overheadPlacement':'native independent left/right poles and wires; use world anchor, track axis and source direction; camera sorting/PPU await Unity','completeVariantCoverage':True,'operations':'green vegetation Alpha separation; existing lane/curb/marking pixels over painted context; geometric slope projection; no new native paintings'})
  expected={(m,c,sl)for m in masks for c in CONTEXTS for sl,n in SLOPES};actual={(x['connectionMask'],x['surfaceContext'],x['slopeCode'])for x in states};qa.append({'id':req+'.mask-context-slope-matrix','level':'OK'if expected==actual else'FAIL','expected':len(expected),'actual':len(actual),'missing':sorted(expected-actual)})
 for a in assets:
  im=Image.open(R/a['image']);ok=im.mode=='RGBA'and im.size==(256,192)and im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getbbox()is not None and wp.sha(R/a['image'])==a['sha256'];qa.append({'id':a['id']+'.PNG-contract','level':'OK'if ok else'FAIL'})
 wp.writej(R/OUT/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':assets,'animations':[],'coverageMappings':maps,'qa':qa,'unityValidated':False,'limitations':['Context and slope variants reuse recorded painted native lanes/grounds, not new original images.','Tram overhead uses separately delivered real native catenary modules, not paint baked into the lane.','Foundation selection, route permissions and vehicle path following are next-stage engine work.']})
 # Show every context/slope with straight road and curved tram, then all masks.
 sample=[a for a in assets if a.get('surfaceContext')and a['connectionMask']==(5 if a['id'].startswith('road-')else 3)]
 t.contact(sample,'road-context-slope-contact.jpg',5,220)
 t.contact([a for a in assets if a.get('surfaceContext')=='snow'and a.get('slopeCode')==0],'road-snow-masks-contact.jpg',4,220)
 report={'createdAt':wp.now(),'formalPNGCount':len(assets),'matrixChecks':qa[:2],'passed':sum(c['level']=='OK'for c in qa),'failures':[c for c in qa if c['level']!='OK'],'sourceManifestSha256':wp.sha(R/OUT/'manifest.json'),'visualReview':'pending actual contact sheets','unityValidated':False}
 wp.writej(R/'records/world-production/road-variants-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

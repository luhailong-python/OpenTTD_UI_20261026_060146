"""Check actual source offsets,all farm corner joins,rail positions and native provenance."""
from pathlib import Path
from PIL import Image
import json,numpy as np
import world_pack as wp
from build_fence_adapter import source_specs,EDGES,ANCHOR
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 mp=R/'assets/world/overlays/fence-adapter/manifest.json';m=load(mp);families,mods,positions=source_specs();by={a['image']:a for a in m['assets']};checks=[];vrp=R/'records/fence-adapter-visual-review.json';vr=load(vrp)if vrp.is_file()else{};seen={a['file']:a['sha256']for a in vr.get('reviewedAssets',[])}
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 test('6actual-farm-families',len(families)==6 and m['farmSourceFamilies']==families);test('actual-source-offset-tables',m['farmSlopeOffsetTables']==mods);test('456full-farm-bindings',len(m['farmBindings'])==456 and len({(b['fenceValue'],b['slopeCode'],b['edge'])for b in m['farmBindings']})==456);test('44shared-native-prop-PNGs',len(m['assets'])==44);test('source-implicit0-no-image',{b['fenceValue']for b in m['noImageSourceValues']if b['noDraw']}=={0,7});test('source16rail-positions',len(m['railSourcePositions'])==16);test('4no-fence-RailGroundTypes',{x['railGroundType']for x in m['railNoFenceGroundTypes']if x['noDraw']}=={'Barren','Grass','SnowOrDesert','HalfTileSnow'});test('4HalfTileWater-corners',{h['trackCorner']for h in m['railHalfTileWaterBindings']}=={'W','N','E','S'})
 for src in m['sourceFiles']:test('current-source-code-sha',wp.sha(R/src['file'])==src['sha256'],file=src['file'])
 images={}
 for a in m['assets']:
  p=R/a['image'];im=Image.open(p);ar=np.array(im);images[a['image']]=ar;mask=ar[...,3]>8;ys,xs=np.where(mask);test(a['id']+'.output-current-sha',wp.sha(p)==a['sha256']==load(Path(str(p)+'.derivation.json'))['sha256']);test(a['id']+'.safe-trueAlpha',im.mode=='RGBA'and im.size==(320,320)and len(xs)>0 and xs.min()>0 and xs.max()<319 and ys.min()>0 and ys.max()<319 and ar[...,3].min()==0);test(a['id']+'.fixed-anchor',a['anchorPx']==[160,192]and a['pivotUnity']==[.5,.4]);test(a['id']+'.no-hiddenRGB',np.all(ar[ar[...,3]==0,:3]==0));test(a['id']+'.native-provenance-disclosure',not a['nativeModelGeneration']and not a['nativeUpscale']and a['actualModel']is None and bool(a['derivedFrom']));test(a['id']+'.current-actual-art-review',seen.get(a['image'])==a['sha256'])
  for s in a['derivedFrom']:test('current-painting-source-sha',wp.sha(R/s['file'])==s['sha256'],file=s['file'])
 for b in m['farmBindings']:
  a=by[b['file']];h=wp.corner_heights(b['slopeCode']);c0,c1=EDGES[b['edge']];p=[[wp.FLAT_POINTS[c][0]+128,wp.FLAT_POINTS[c][1]+160-h[c]*32]for c in [c0,c1]];off=mods[b['edge']][b['slopeCode']];test('actual-source-farm-sprite-id',b['sourceSpriteOffset']==off and b['sourceSpriteId']==families[b['fenceValue']-1]['spriteBase']+off);test('exact-farm-corner-heights',b['endpointPx']==p and b['sourceReferencePixelZ']==h[b['sourceReferenceCorner']]*8);placed=[[a['localEndpointPx'][i][j]+b['pasteXY'][j]for j in range(2)]for i in range(2)];test('exact-native-sprite-placement-to-endpoints',placed==p);test('current-bound-farm-PNG',a['sha256']==b['sha256'])
  for pt in a['localEndpointPx']:
   x,y=map(round,pt);test('native-paint-near-logical-contact',images[b['file']][max(0,y-10):y+11,max(0,x-10):x+11,3].max()>20)
 for i,r in enumerate(m['railSourcePositions']):
  src=positions[i];test('actual-rail-source-position-and-mod8',all(r[k]==src[k]for k in ['index','role','heightRef','originWorld','extentWorld','sourceName'])and r['sourceSpriteId']==1301+i%8);a=by[r['file']];p=[[a['logicalEndpointPx'][j][k]+r['pasteXYAtBaseZ'][k]for k in range(2)]for j in range(2)];test('exact-rail-role-placement',p==r['baselineEndpointPxAtBaseZ']);test('source-rail-current-PNG',a['sha256']==r['sha256'])
 for s in m['railGroundSelectors']:
  c=s['slopeCode'];nw=(4 if c&1 else 6)if c&9 else 0;se=(12 if c&2 else 14)if c&6 else 8;ne=(5 if c&4 else 7)if c&12 else 1;sw=(13 if c&2 else 15)if c&3 else 9;expect={'FenceNW':[nw],'FenceSE':[se],'FenceSENW':[nw,se],'FenceNE':[ne],'FenceSW':[sw],'FenceNESW':[ne,sw],'FenceVert1':[2],'FenceVert2':[10],'FenceHoriz1':[3],'FenceHoriz2':[11]};test('actual-source-RailGroundType-selector',s['sourcePositionIndices']==expect[s['railGroundType']])
 test('HalfTileWater-source-corner-selection',{h['trackCorner']:h['sourcePositionIndex']for h in m['railHalfTileWaterBindings']}=={'W':2,'N':3,'E':10,'S':11})
 for off in range(6):
  normal=next(a for a in m['assets']if a['id']==f'farm-bushes-offset-{off}');red=next(a for a in m['assets']if a['id']==f'farm-red-bloom-offset-{off}');yellow=next(a for a in m['assets']if a['id']==f'farm-yellow-bloom-offset-{off}');test('flower-palette-keeps-nativeAlpha',np.array_equal(images[normal['image']][...,3],images[red['image']][...,3])and np.array_equal(images[normal['image']][...,3],images[yellow['image']][...,3]));test('gate-is-distinct-native-composite',next(a['sha256']for a in m['assets']if a['id']==f'farm-bushes-gate-offset-{off}')!=normal['sha256'])
 fail=[a for a in checks if not a['passed']];report={'createdAt':wp.now(),'formalPNGCount':44,'farmBindings':456,'railRoles':8,'railPositions':16,'halfWaterCorners':4,'passed':sum(a['passed']for a in checks),'failed':len(fail),'failures':fail,'complete':not fail,'manifest':wp.rel(mp),'manifestSHA256':wp.sha(mp),'scope':'actual6sourcefamilies/6offsets,45619slope4edge contact/endpoint mappings,16railposition/mod8/190selector/4halfwater bindings,sourceRGBA/Alpha/provenance and current actual-page review;no new native painting','visualRecord':'records/fence-adapter-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/fence-adapter-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

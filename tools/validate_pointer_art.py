"""PNG/source/hotspot/selection-matrix validation and assembled review previews."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
import world_pack as wp
import build_pointer_overlays as b
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 manifests=[R/'assets/common/pointers/components/manifest.json',R/'assets/common/pointers/manifest.json',R/'assets/common/pointers/markers/manifest.json',R/'assets/world/overlays/manifest.json'];assets=[a for p in manifests for a in load(p)['assets']];checks=[];unique=set();sources=set()
 def test(id,ok,**extra):checks.append({'id':id,'passed':bool(ok),**extra})
 for a in assets:
  p=R/a['image'];im=Image.open(p).convert('RGBA');alpha=np.asarray(im.getchannel('A'));ys,xs=np.where(alpha>20);test(a['id']+'.hash',wp.sha(p)==a['sha256']);test(a['id']+'.canvas',im.size==(a['width'],a['height']));test(a['id']+'.Alpha',alpha.min()==0 and alpha.max()>20);test(a['id']+'.safe-visible-bound',len(xs)>0 and xs.min()>0 and ys.min()>0 and xs.max()<im.width-1 and ys.max()<im.height-1);test(a['id']+'.unique-file',a['image']not in unique);unique.add(a['image']);test(a['id']+'.not-native-upscaled',not a.get('nativeUpscale'));test(a['id']+'.metadata-current',load(Path(str(p)+'.derivation.json'))['sha256']==a['sha256'])
  for src in a.get('derivedFrom',[]):
   key=(src['file'],src['sha256'])
   if key in sources:continue
   sources.add(key);test('source-current-sha', (R/src['file']).is_file()and wp.sha(R/src['file'])==src['sha256'],file=src['file'])
 # Independent literal recipe reconstruction: do not call the production builder.
 white=next(a for a in assets if a['id']=='SPR_WHITE_POINT');actual=Image.open(R/white['image']);expected=Image.new('RGBA',(32,32),(0,0,0,0));expected.putpixel((16,16),(250,242,217,255));recipe={'id':'SPR_WHITE_POINT.v1','sourceSymbol':'SPR_WHITE_POINT','sourceSpriteId':4079,'canvasPx':[32,32],'mode':'RGBA','backgroundRGBA':[0,0,0,0],'pointPx':[16,16],'pointRGBA':[250,242,217,255],'coordinateOrigin':'top-left','paintedArtworkParent':False};recipeSource='tools/build_pointer_overlays.py';pointChecks={'exact-independent-RGBA-recipe':actual.mode=='RGBA'and actual.size==(32,32)and actual.tobytes()==expected.tobytes(),'PNG-bytes-unchanged':wp.sha(R/white['image'])=='c041e7549e409668879fdaa9805092c82472176eb094c29e7ada38cd315602ce','exact-recipe-metadata':white.get('functionalGeometryRecipe')==recipe,'current-functional-geometry-source':white.get('derivedFrom')==[{'file':recipeSource,'sha256':wp.sha(R/recipeSource),'sourceType':'functional-geometry-recipe','recipeId':'SPR_WHITE_POINT.v1'}]}
 for key,passed in pointChecks.items():test('SPR_WHITE_POINT.'+key,passed)
 wp.writej(R/'records/pointer-white-point-recipe-validation.json',{'createdAt':wp.now(),'image':white['image'],'sha256':wp.sha(R/white['image']),'PNGBytesUnchanged':pointChecks['PNG-bytes-unchanged'],'recipe':recipe,'recipeSource':{'file':recipeSource,'sha256':wp.sha(R/recipeSource),'sourceType':'functional-geometry-recipe'},'validationMethod':'Independent PIL RGBA canvas filled with zero;one literal point;byte-for-byte decoded RGBA comparison,not builder helper invocation;PNG SHA compared to frozen original.','checks':[{'id':k,'passed':v}for k,v in pointChecks.items()],'passed':sum(pointChecks.values()),'failed':sum(not v for v in pointChecks.values()),'complete':all(pointChecks.values()),'failures':[k for k,v in pointChecks.items()if not v],'userArtAcceptance':'pending','unityValidated':False})
 curs=load(manifests[1]);hot=curs['hotspotEvidence']['hotspotPx'];tipbase=np.asarray(Image.open(R/'assets/common/pointers/cursors/SPR_CURSOR_MOUSE.png'))[:32,:32]
 for a in curs['assets']:
  im=Image.open(R/a['image']);test(a['id']+'.tip-alpha',im.getpixel(tuple(hot))[3]>=128);test(a['id']+'.same-measured-tip-registration',np.array_equal(np.asarray(im)[:32,:32],tipbase));test(a['id']+'.fixed96canvas',im.size==(96,96))
 for clip in curs['animations']:
  test(clip['id']+'.distinct-real-frames',len({wp.sha(R/f)for f in clip['frames']})==len(clip['frames']));test(clip['id']+'.source-timing',clip['durationsMs']==[x*27 for x in clip['sourceTicks']]);test(clip['id']+'.fixed-hotspot',clip['fixedHotspotPx']==hot)
 overlays=load(manifests[3]);by= {}
 for a in overlays['assets']:by.setdefault(a['sourceRequirementId'],[]).append(a)
 test('normal19',len([k for k in by if k.startswith('selection-normal')])==19);test('half12',len([k for k in by if k.startswith('selection-half')])==12);test('autorail114',len([k for k in by if k.startswith('selection-autorail')])==114)
 for req,aa in by.items():
  points=[a['geometryPointsPx']for a in aa];test(req+'.palette-keeps-identical-geometry',all(p==points[0]for p in points))
  if req.startswith('selection-autorail'):
   states={a['paletteRole']for a in aa};test(req+'.forced-red-present','invalid-red'in states)
   if len(aa)==2:test(req+'.palette-only-identical-Alpha',np.array_equal(np.asarray(Image.open(R/aa[0]['image']).getchannel('A')),np.asarray(Image.open(R/aa[1]['image']).getchannel('A'))))
 # Actual matching-height terrain assembly: all5palette roles on flat and19slopes.
 ground=load(R/'assets/world/terrain/manifest.json')['assets'];flat=next(a for a in ground if a['id']=='terrain-grass-slope-flat');scene=Image.new('RGB',(1440,448),'#214638');d=ImageDraw.Draw(scene)
 for i,role in enumerate(b.COL):
  ov=next(a for a in overlays['assets']if a['sourceRequirementId']=='selection-normal-slope-0'and a['paletteRole']==role);pic=Image.new('RGBA',(288,224));pic.alpha_composite(Image.open(R/flat['image']).convert('RGBA'),(16,16));pic.alpha_composite(Image.open(R/ov['image']).convert('RGBA'));scene.paste(pic,(i*288,0),pic);d.text((i*288+8,216),role,font=b.t.font(12),fill='#f3e7ca')
 for i,code in enumerate([3,6,9,12,29]):
  gr=next(a for a in ground if a.get('materialId')=='grass'and a.get('slopeCode')==code and a.get('variant')==0);ov=next(a for a in overlays['assets']if a['sourceRequirementId']=='selection-normal-slope-'+str(code)and a['paletteRole']=='invalid-red');pic=Image.new('RGBA',(288,224));pic.alpha_composite(Image.open(R/gr['image']).convert('RGBA'),(16,16));pic.alpha_composite(Image.open(R/ov['image']).convert('RGBA'));scene.paste(pic,(i*288,224),pic)
 path=R/'previews/pointers/selection-terrain-assembly.jpg';scene.save(path,quality=95)
 bindings=load(R/'docs/POINTER_OVERLAY_BINDINGS.json')['bindings'];markers=[]
 for x in bindings[-10:]:
  for f in ([x['file']]if x.get('file')else[])+[s['file']for s in x.get('layers',[])]:
   if f.endswith('.png'):markers.append({'id':x['id']+'-'+Path(f).stem,'image':f})
 b.contact(markers,'pointer-marker-reuse',6);components=load(manifests[0])['assets'];b.gallery(curs['assets'],overlays['assets'],components,curs['animations'],bindings)
 report={'createdAt':wp.now(),'scope':'Current individual PNG/source SHA,Alpha/safe bounds,96px measured hotspot across87frames,5source animation timings,all selection cases/palettes and forced-red override Alpha. User art approval/Unity separate.','formalPNGCount':len(assets),'sourceDependencyCount':len(sources),'passed':sum(x['passed']for x in checks),'failures':[x for x in checks if not x['passed']],'sourceManifests':[{'file':wp.rel(p),'sha256':wp.sha(p)}for p in manifests],'previewAssembly':{'file':wp.rel(path),'sha256':wp.sha(path)},'unityValidated':False,'userArtAcceptance':'pending'};wp.writej(R/'records/pointer-art-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

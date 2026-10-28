"""Re-read source semantics and verify real composable art + preview states."""
from PIL import Image
import numpy as np,json,hashlib
import manager_face_parts as p
from audit_manager_faces import audit
R=p.R;OUT=p.OUT
def main():
 if not(OUT/'manifest.json').is_file():
  result={'createdAt':p.now(),'complete':False,'failures':[{'id':'real-part-manifest','reason':'Native parts and actual layered outputs not yet delivered'}],'unityValidated':False};p.savej(R/'records/manager-customization-validation.json',result);print(json.dumps(result));return
 m=p.load(OUT/'manifest.json');spec=p.extract(R);checks=[];assets={a['id']:a for a in m['assets']};binding={b['requirementId']:b for b in m['bindings']}
 def check(k,v,**x):checks.append({'id':k,'level':'OK'if v else'FAIL',**x})
 check('exact235-source-bindings',set(binding)=={r['requirementId']for r in spec['requirements']})
 for r in spec['requirements']:
  b=binding.get(r['requirementId'],{});key=r['requirementId'];check(key+'.kind',b.get('kind')==r['kind'])
  if r['kind']=='Sprite':check(key+'.source-and-parts',b.get('sourceSpriteId')==r['sourceSpriteId']and bool(b.get('assetIds'))and all(i in assets for i in b.get('assetIds',[])))
  elif r['kind']=='Toggle':check(key+'.source-hidden',b.get('hiddenSourceVarIndices')==r['hiddenSourceVarIndices'])
  else:check(key+'.source-palette',b.get('affectedSourceVarIndices')==r['affectedSourceVarIndices']and bool(b.get('paletteRule')))
 for a in m['assets']:
  path=R/a['image'];im=Image.open(path).convert('RGBA');ar=np.asarray(im);bb=im.getbbox();check(a['id']+'.512-registration',im.size==(512,512)and a['anchorPx']==[256,496]);check(a['id']+'.real-alpha',im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getextrema()[1]>0);check(a['id']+'.inside-canvas',bb and bb[0]>0 and bb[1]>0 and bb[2]<512 and bb[3]<512)
  check(a['id']+'.file-sha',p.sha(path)==a['sha256']);check(a['id']+'.native-scale',not a.get('nativeUpscale')and a.get('scaleApplied',1)<=1)
  check(a['id']+'.provenance',all((R/s['file']).is_file()and p.sha(R/s['file'])==s['sha256']and(R/s['record']).is_file()for s in a['derivedFrom']))
  if a.get('irisMask'):
   src=Image.open(R/a['derivedFrom'][0]['file']).convert('RGBA');mask=np.asarray(Image.open(R/a['irisMask']).convert('RGBA'))[:,:,3]>0;check(a['id']+'.palette-owned',np.array_equal(ar[~mask],np.asarray(src)[~mask]))
  family=a['family'];limits={'eyes':(260,110),'eyes-palette':(260,110),'nose':(100,100),'mouth':(150,90),'glasses':(280,100)}
  if family in limits:mw,mh=limits[family];check(a['id']+'.independent-component-bounds',bb and bb[2]-bb[0]<=mw and bb[3]-bb[1]<=mh)
 covered=set();samples={s['id']:s for s in m['compositionSamples']}
 for s in m['compositionSamples']:
  values={int(k):v for k,v in s['selectedSourceValues'].items()};order=p.source_order(s['sourceStyle'],values,spec);check(s['id']+'.source-order',s['sourceDrawOrder']==order)
  target=Image.open(R/s['image']).convert('RGBA');out=Image.new('RGBA',(512,512))
  for l in s['layers']:out.alpha_composite(Image.open(R/assets[l['assetId']]['image']).convert('RGBA'),tuple(l['offsetPx']))
  check(s['id']+'.actual-layer-rgba',out.tobytes()==target.tobytes());check(s['id']+'.current-sha',p.sha(R/s['image'])==s['sha256'])
  if s.get('coveredRequirementId'):
   covered.add(s['coveredRequirementId']);b=binding[s['coveredRequirementId']];check(s['id']+'.tested-field-active',b['sourceVarIndex']in order)
 check('all213-sprite-values-actually-composed',covered=={r['requirementId']for r in spec['requirements']if r['kind']=='Sprite'})
 for style in[0,2]:
  fields=spec['styles'][style]['fields'];active=p.active_indices(style,{0:1},spec);nose=next(f['sourceVarIndex']for f in fields if f['name']=='STR_FACE_NOSE');lips=next(f['sourceVarIndex']for f in fields if f['name']=='STR_FACE_LIPS');check('style'+str(style)+'.beard-removes-nose-mouth',nose not in active and lips not in active)
 if all(i in samples for i in['cancel-original','cancel-restored']):check('cancel-original-exact',samples['cancel-original']['sha256']==samples['cancel-restored']['sha256'])
 for state in m.get('previewStates',[]):
  im=Image.open(R/state['image']);layout=p.load(R/state['layoutRecord']);check(state['id']+'.screen-size',im.size==(1920,1080));check(state['id']+'.image-current',p.sha(R/state['image'])==state['sha256']);check(state['id']+'.layout-no-errors',not layout['layoutIssues']);check(state['id']+'.dynamic-text-independent',not layout['nativePaintedText'])
  if state['id'].startswith('facecode-'):
   field=layout.get('facecodeField',{});check(state['id']+'.typed-text-field',field.get('kind')=='single-line-text'and field.get('dropdown')is False and not any(x.get('asset')=='reference-dropdown'for x in layout['placements']))
   check(state['id']+'.full-raw-code-retained',bool(state.get('facecodeInputText'))and state['facecodeInputText']==layout.get('facecodeInputText'))
 upstream=audit(R);check('independent-upstream-contract',upstream['complete'],gaps=upstream['gaps']);fail=[c for c in checks if c['level']=='FAIL']
 result={'schema':'manager-customization-production-QA.v1','createdAt':p.now(),'manifest':'assets/portraits/customization/manifest.json','manifestSHA256':p.sha(OUT/'manifest.json'),'registeredAssets':len(assets),'sourceBindings':len(binding),'compositionSamples':len(m['compositionSamples']),'advancedPreviewStates':len(m.get('previewStates',[])),'checks':len(checks),'failures':fail,'checksDetail':checks,'mechanicalPassed':not fail,'actualVisualReview':'Pending actual current-hash source/part/combination/UI page inspection; this script cannot declare visual acceptance','complete':False,'unityValidated':False,'userAccepted':False}
 p.savej(R/'records/manager-customization-validation.json',result);p.savej(R/'records/manager-customization-audit.json',upstream);print(json.dumps({k:v for k,v in result.items()if k not in['checksDetail']},ensure_ascii=False))
if __name__=='__main__':main()

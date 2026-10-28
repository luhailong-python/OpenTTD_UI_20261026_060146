"""Validate source symbols, actual painted dependency hashes, Alpha and semantic states."""
from pathlib import Path
from PIL import Image
import json,re,collections
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 mp=R/'assets/common/micro-ui/manifest.json';bp=R/'docs/MICRO_UI_BINDINGS.json';m=load(mp);q=load(bp);checks=[]
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 aa={a['id']:a for a in m['assets']};bb={a['id']:a for a in q['bindings']};source=(R/q['sourceFile']['file']).read_text(encoding='utf8').splitlines();expected=[]
 for i,line in enumerate(source,1):
  match=re.search(r'static const SpriteID\s+(SPR_\w+)\s*=',line)
  if 56<=i<=193 and match and not any(k in match[1]for k in ['OPENTTD_BASE','HALFTILE_','SIGNALS_BASE']):expected.append(match[1])
 primary={k:a for k,a in aa.items()if a['category']!='palette-variant'}
 test('actual-source-symbol-set',set(expected)==set(primary)==set(bb));test('actual-source-file-sha',q['sourceFile']['sha256']==wp.sha(R/q['sourceFile']['file']));test('current-manifest-binding-sha',q['manifestSHA256']==wp.sha(mp));test('no-duplicate-symbols',len(expected)==len(primary)==len(q['bindings'])and len(aa)==len(m['assets']))
 sources=set();seen={}
 vrp=R/'records/micro-ui-visual-review.json';vr=load(vrp)if vrp.is_file()else{};reviewed={a['file']:a['sha256']for a in vr.get('reviewedAssets',[])}
 for sym,a in aa.items():
  p=R/a['image'];im=Image.open(p);d=load(Path(str(p)+'.derivation.json'));b=bb[a['sourceSymbol']];alpha=im.getchannel('A');bbx=alpha.point(lambda x:255 if x>20 else 0).getbbox()
  test(sym+'.file-sha',a['sha256']==d['sha256']==wp.sha(p)and(a['category']=='palette-variant'or a['sha256']==b['sha256']));test(sym+'.fixed96-RGBA',im.mode=='RGBA'and im.size==(96,96));test(sym+'.true-safe-Alpha',alpha.getextrema()[0]==0 and bbx and min(bbx[:2])>0 and max(bbx[2:])<96);test(sym+'.fixed-pivot',a['anchorPx']==[48,48]and a['pivotUnity']==[.5,.5]);test(sym+'.source-expression',a['sourceSymbol']in source[b['source']['line']-1]and b['source']['spriteId']==a['sourceSpriteId']);test(sym+'.clear-native-derivative-claim',a['nativeModelGeneration']is False and a['nativeUpscale']is False and a['actualModel']is None);test(sym+'.required-control-states',set(a['statesContract'])=={'normal','pressed','selected','disabled','locked'});test(sym+'.current-actual-review',reviewed.get(a['image'])==a['sha256']and b.get('localArtReviewed'))
  for src in a['derivedFrom']:
   key=(src['file'],src['sha256'])
   if key in sources:continue
   sources.add(key);test('source-current-sha',(R/src['file']).is_file()and wp.sha(R/src['file'])==src['sha256'],file=src['file'])
   if src.get('sourceType')=='functional-vector-geometry':test('svg-source-not-painting','<svg'in(R/src['file']).read_text(encoding='utf8')and '<image'not in(R/src['file']).read_text(encoding='utf8'),file=src['file'])
   elif src.get('record'):test('painted-source-record-exists',(R/src['record']).is_file(),file=src['record'])
 for prefix in ['SPR_PROFIT_','SPR_TOWN_RATING_','SPR_ARROW_']:
  group=[a for a in aa.values()if a['id'].startswith(prefix)];test(prefix+'.distinct-semantic-state-images',len({a['sha256']for a in group})==len(group)==4)
 for v in ['TRAIN','ROADVEH','SHIP','AIRCRAFT']:
  group=[aa[f'SPR_GROUP_{act}_{v}']for act in ['CREATE','DELETE','RENAME','REPLACE_ON','REPLACE_OFF','LIVERY']];test(v+'.6distinct-group-actions',len({a['sha256']for a in group})==6)
  symbols=[f'SPR_SELL_{v}',f'SPR_SELL_ALL_{v}']+(['SPR_SELL_CHAIN_TRAIN']if v=='TRAIN'else[]);test(v+'.distinct-sale-scopes',len({aa[s]['sha256']for s in symbols})==len(symbols))
 for sym,count in [('SPR_SQUARE',16),('SPR_BLOT',3)]:
  variants=bb[sym]['paletteVariants'];test(sym+'.required-palette-count',len(variants)==count and len({v['sha256']for v in variants})==count)
  base=Image.open(R/aa[sym]['image']);test(sym+'.palette-identical-Alpha',all(Image.open(R/v['file']).getchannel('A').tobytes()==base.getchannel('A').tobytes()for v in variants))
 failures=[a for a in checks if not a['passed']];q['complete']=not failures;q['failed']=failures;q['manifestSHA256']=wp.sha(mp);wp.writej(bp,q)
 result={'createdAt':wp.now(),'scope':'96 source UI Sprite symbols; exact native painted source provenance,UI vector overlays,RGBA/current SHA,fixed canvas/pivot,control-state recipes,distinct profit/rating/vehicle operations,current visual-review hashes. No Unity or user approval.','sourceRequirements':len(expected),'bound':len(bb),'formalPNGCount':len(aa),'passed':sum(x['passed']for x in checks),'failed':len(failures),'failures':failures,'complete':not failures,'manifest':'assets/common/micro-ui/manifest.json','manifestSHA256':wp.sha(mp),'bindings':'docs/MICRO_UI_BINDINGS.json','bindingsSHA256':wp.sha(bp),'visualRecord':'records/micro-ui-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/micro-ui-validation.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()

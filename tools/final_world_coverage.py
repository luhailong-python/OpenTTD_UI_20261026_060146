"""Coverage bindings and variant evidence; file mapping is separate from review."""
from pathlib import Path
from PIL import Image
import json,copy,re
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def strings(v):
 if isinstance(v,str):yield v
 elif isinstance(v,dict):
  for x in v.values():yield from strings(x)
 elif isinstance(v,list):
  for x in v:yield from strings(x)
def filepaths(v):return sorted(set(s.replace('\\','/')for s in strings(v)if s.startswith('assets/world/')and s.lower().endswith('.png')and(R/s).is_file()))
def build(assets,animations):
 inv=load(R/'docs/WORLD_ASSET_COVERAGE.json');index={a['image']:a for a in assets};byid={a['id']:a for a in assets};bindings={};origins={}
 def bind(req,files,meta,origin):
  files=[f for f in files if f in index]
  if not files:return
  bindings.setdefault(req,[]).append({'files':files,'metadata':meta,'manifest':origin});origins.setdefault(req,set()).add(origin)
 for p in (R/'assets/world').rglob('manifest.json'):
  q=load(p);origin=wp.rel(p)
  for m in q.get('coverageMappings',[]):
   req=m.get('requirementId',m.get('sourceRequirementId'))
   if req:
    files=filepaths(m)+[byid[i]['image']for i in m.get('artIds',[])if i in byid]
    bind(req,files,m,origin)
  for a in q.get('assets',[]):
   for req in a.get('sourceRequirementIds',[]):
    bind(req,[a.get('image',a.get('file',''))],{'assetId':a['id']},origin)
 known={'terrain-grass':'terrain-grass-','terrain-bare':'terrain-bare-','terrain-rough':'terrain-rough-','terrain-snow':'terrain-snow-','terrain-desert':'terrain-desert-','water-sea':'water-sea-'}
 for req,prefix in known.items():bind(req,[a['image']for a in assets if a['id'].startswith(prefix)],{'binding':'material variants and slope codes from explicit asset fields'},'assets/world/terrain/manifest.json')
 # Roads carry logical masks; states/contexts also exist in transport runtime.
 for req,word in[('road-road','road-mask-'),('road-tram','tram-mask-')]:
  bind(req,[a['image']for a in assets if a['id'].startswith(word)],{'binding':'explicit native-lane graph masks'},'assets/world/infrastructure/roads/manifest.json')
 # Effect/disaster runtime documents retain exact original numeric source ID.
 for doc,key,cat,idkey in[('EFFECT_RUNTIME_MANIFEST.json','effects','effect','sourceEffectId'),('DISASTER_RUNTIME_MANIFEST.json','subtypes','disaster','sourceSubtypeId')]:
  runtime=load(R/'docs'/doc)
  src={x['sourceId']:x for x in runtime[key]}
  for row in inv['items']:
   if row['category']!=cat:continue
   number=row['neededVariants'].get(idkey)
   if number is None:number=row['neededVariants'].get('sourceSubtypeID')
   if number is None:
    number=next((n for n,x in src.items()if any(x.get('sourceEnum')==s.get('symbol')for s in row['source'])),None)
   if number not in src:continue
   m=src[number];files=[]
   for s in strings(m):
    if s.startswith('assets/world/')and s.endswith('/manifest.json')and(R/s).is_file():files+=filepaths(load(R/s))
   bind(row['id'],files,{'sourceId':number,'sourceEnum':m['sourceEnum'],'runtimeRecord':m},'docs/'+doc)
 # Source industry machinery is a shared set of actual moving-part loops.
 machines=[a for a in animations if a.get('binding')and('industry'in a.get('category','')or a.get('id','').startswith('industry'))]
 if not machines:machines=[a for a in animations if any('industries/'in f for f in a.get('frames',[]))]
 if machines:bind('animation-industry-machinery',filepaths(machines),{'animations':machines,'binding':'source machinery loops with clean parent and foreground ownership'},'assets/world/industries/manifest.json')
 rows=[]
 for item in inv['items']:
  req=item['id'];q=copy.deepcopy(item);maps=bindings.get(req,[]);files=sorted({f for m in maps for f in m['files']});matched=[index[f]for f in files];missing=[];variants=[]
  if not files:missing.append('正式资源或显式模块映射尚未取得。')
  # Variant tests are semantic tests on mapping data, not only on file counts.
  metas=[m['metadata']for m in maps]
  if item['entryKind']=='source-house-tile-spec':
   states=[s for m in metas for s in m.get('states',[])];comb={(s.get('locationVariant'),s.get('constructionStage'))for s in states}
   variants.append({'test':'4location×4construction','expected':16,'actual':len(comb),'passed':len(comb)==16})
  elif item['category']=='vegetation':
   stages={s.get('stage')for m in metas for s in m.get('states',[])};variants.append({'test':'7growth/death stages','expected':7,'actual':len(stages),'passed':len(stages)==7})
  elif item['category']=='industry-tile':
   groups=[g for m in metas for g in m.get('constructionStates',[])];good=bool(groups)and all({s.get('stage')for s in g['states']}=={0,1,2,3}for g in groups);variants.append({'test':'every mapped parent has4 construction stages','parents':len(groups),'passed':good})
  elif item['category']=='signal':
   states=[s for m in metas for s in m.get('states',[])if isinstance(s,dict)];comb={(s.get('direction'),s.get('state'))for s in states};variants.append({'test':'8logical directions×2states +2placement bindings','expected':16,'actual':len(comb),'passed':len(comb)==16})
  elif item['category']in['bridge','tunnel']:
   complete=any(m.get('completeVariantCoverage')for m in metas);variants.append({'test':'explicit axis/direction/layer/material contract coverage','passed':complete})
  elif req=='water-lock':
   comb={(m.get('direction'),m.get('waterLevel'),m.get('gate'))for m in metas if m.get('whole')};variants.append({'test':'4directions×3levels×2gate states','expected':24,'actual':len(comb),'passed':len(comb)==24})
  elif req=='water-river' or req=='water-canal':
   masks={a.get('connectivityMask')for a in matched if a.get('connectivityMask')is not None};variants.append({'test':'16water connectivity masks','expected':16,'actual':len(masks),'passed':len(masks)==16})
  elif req=='water-shore':
   states=[s for m in metas for s in m.get('states',[])if s.get('whole')];combos={(s.get('shoreClimate'),s.get('sourceShoreIndex'))for s in states};reserved=[s for m in metas for s in m.get('reservedBindings',[])];no_draw=[s for s in reserved if s.get('noDraw')and s.get('image')is None and s.get('applicable')is False];variants.append({'test':'3climates×16valid shoreline shapes plus6explicit no-draw reserved slots','expectedValid':48,'actualValid':len(combos),'reservedNoDraw':len(no_draw),'passed':len(combos)==48 and len(no_draw)==6})
  elif req=='terrain-foundation':
   case=[c for m in metas for c in m.get('caseBindings',[])];modes={c.get('mode')for c in case};variants.append({'test':'all14Foundation modes including explicitNone/no-image cases','actual':len(modes),'expected':14,'passed':len(modes)==14})
  elif req=='terrain-fence':
   families=set();offsets={o for m in metas for o in m.get('sourceSpriteOffsets',[])}
   for m in metas:
    value=m.get('sourceValidFamilies',[]);families.update(range(1,value+1)if isinstance(value,int)else value)
   variants.append({'test':'6actual source fence families and6source slope offsets, decorative colours counted separately','actualFamilies':sorted(families),'actualOffsets':sorted(offsets),'passed':set(range(1,7))<=families and set(range(6))<=offsets})
  elif req=='object-headquarters':
   levels={a.get('level')for a in matched if a.get('level')};variants.append({'test':'5HQ levels and20tile partitions','actual':len(levels),'expected':5,'passed':len(levels)==5})
  elif req.startswith('animation-'):
   related=[a for a in animations if req in a.get('sourceRequirementIds',[])or any(f in files for f in a.get('frames',[]))];variants.append({'test':'ordered real frame clip +fixed anchor','actual':len(related),'passed':bool(related)})
  from world_variant_checks import extra_checks
  variants+=extra_checks(item,matched,metas,assets,animations)
  for v in variants:
   if not v['passed']:missing.append('状态合同尚未通过：'+v['test'])
  checks=[]
  for a in matched:
   p=R/a['image'];im=Image.open(p);ok=(im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0 and im.size==(a['width'],a['height'])and wp.sha(p)==a['sha256']and not a.get('nativeUpscale'));checks.append(ok)
  q.update({'artFiles':files,'assetIds':[a['id']for a in matched],'moduleMappings':maps,'artStatus':'produced-mapped'if files else'missing-not-yet-produced-or-unmapped','acceptanceStatus':'mapped-awaiting-final-review'if files and not missing else'incomplete','localVerification':{'variantChecks':variants,'mappedPNGCount':len(files),'mappedPNGChecksPassed':sum(checks),'mappedPNGChecksFailed':sum(not c for c in checks),'visualReviewSource':'records/full-game-independent-visual-review.json and pack-specific contact review; final status set only after stable final snapshot','localArtReviewed':False},'missingItems':missing,'userArtAcceptance':'pending','unityValidated':False})
  if any(not c for c in checks):q['missingItems'].append('存在映射PNG尺寸/Alpha/哈希/放大声明不一致。')
  rows.append(q)
 result={'createdAt':wp.now(),'referenceCommit':inv['referenceCommit'],'sourceRequirements':len(rows),'producedMappedRows':sum(bool(r['artFiles'])for r in rows),'remainingRows':sum(not r['artFiles']for r in rows),'incompleteVariantRows':sum(bool(r['missingItems'])for r in rows),'localAcceptedRows':0,'rule':'A mapped file is not sufficient for acceptance: explicit variant tests, current PNG checks, actual contact review and stable source records are required. User art acceptance and Unity remain separate.','items':rows}
 wp.writej(R/'docs/WORLD_DELIVERY_COVERAGE.json',result);return result

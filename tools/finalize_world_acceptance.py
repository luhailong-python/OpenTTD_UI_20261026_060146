"""Freeze source-specific local artwork acceptance after actual review and QA.
Never treats a mapped path alone as acceptance; user and Unity remain pending.
"""
from pathlib import Path
import copy,json,os
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def entry(p):return{'file':p,'sha256':wp.sha(R/p)}
def number(v):return len(v)if isinstance(v,(list,dict))else int(v or 0)
def goodqa(p):
 q=load(R/p)
 if number(q.get('failures',q.get('failed',0)))or number(q.get('warnings',0)):raise ValueError('QA has unresolved issue: '+p)
 return entry(p)
def reviewed(p):
 q=load(R/p)
 if q.get('manifest')and q.get('manifestSHA256')!=wp.sha(R/q['manifest']):raise ValueError('stale visual manifest: '+p)
 for a in q.get('pages',[])+q.get('layoutPNGs',[]):
  if a.get('file')and a.get('sha256')and wp.sha(R/a['file'])!=a['sha256']:raise ValueError('stale actual visual page: '+a['file'])
 return entry(p)
def main():
 pack=load(R/'docs/WORLD_ASSET_MANIFEST.json');cov=load(R/'docs/WORLD_DELIVERY_COVERAGE.json');worldqa=load(R/'records/world-production/world-validation.json');own=load(R/'records/world-production/world-final-visual-review.json');ind=load(R/'records/full-game-independent-visual-review.json')
 if worldqa['failures']or worldqa['warnings']or worldqa['assetCount']!=len(pack['assets']):raise ValueError('Current complete PNG QA must pass.')
 for src in pack['packSources']:
  if wp.sha(R/src['file'])!=src['sha256']:raise ValueError('Production changed after aggregation: '+src['file'])
 browser=load(R/'records/world-production/browser-validation.json')
 if browser['failed']or browser['manifestSha256']!=wp.sha(R/'docs/WORLD_ASSET_MANIFEST.json'):raise ValueError('Run browser validation on current world manifest before finalizing.')
 visuals={}
 for q,origin in [(ind,'records/full-game-independent-visual-review.json'),(own,'records/world-production/world-final-visual-review.json')]:
  for a in q['items']:
   if a['status'].startswith('passed')and(R/a['file']).is_file()and wp.sha(R/a['file'])==a['sha256']:visuals[a['file']]={**a,'reviewRecord':origin}
 for a in own.get('effectAssetSnapshot',[]):
  if wp.sha(R/a['file'])!=a['sha256']:raise ValueError('Effect PNG changed after actual review: '+a['file'])
 qa={}
 for p in ['world-validation','services-validation','terrain-validation','houses-family-validation','houses-state-validation','industries-validation','industry-binding-validation','vegetation-validation','airport-validation','transport-runtime-validation','transport-lane-validation','road-variants-validation']:
  qa[p]=goodqa('records/world-production/'+p+'.json')
 qa['vehicle-fx']=goodqa('records/vehicle-fx-validation.json')
 airport=reviewed('records/world-production/airport-visual-review.json');lane=reviewed('records/world-production/transport-lane-visual-review.json')
 # Producer reviews explicitly describe actual painted atlas/lifecycle inspections.
 for k,field in [('houses-family-validation','visualReview'),('industries-validation','visualReview'),('vegetation-validation','visualReview')]:
  v=load(R/qa[k]['file']).get(field)
  if not v or isinstance(v,dict)and not v.get('status','').startswith('passed'):raise ValueError('No actual producer visual review: '+k)
 pending=[];reviewRows=[]
 def contact(paths):return[{'file':p,'sha256':visuals[p]['sha256'],'reviewRecord':visuals[p]['reviewRecord'],'finding':visuals[p]['finding']}for p in paths if p in visuals]
 for row in cov['items']:
  req=row['id'];cat=row['category'];qs=[qa['world-validation']];vs=[]
  if cat in ['effect','disaster']:
   qs+=[qa['vehicle-fx']];vs=contact(['previews/world/effects/all-formal-contact-'+str(i)+'.jpg'for i in range(1,5)])
  elif cat=='vegetation':qs+=[qa['vegetation-validation']];vs=[{'producerRecord':qa['vegetation-validation'],'claim':'actual4climate/11lifecycle/special lifecycle pages inspected; current derivative PNG/source checks retained'}]
  elif cat in ['industry','industry-tile']:
   qs+=[qa['industries-validation'],qa['industry-binding-validation']];vs=[{'producerRecord':qa['industries-validation'],'claim':'actual5native atlases and6moving-part phase sheets reviewed; clean-base/foreground assembly validated'}]
  elif cat in ['airport','airport-tile']:
   qs+=[qa['airport-validation']];vs=[{'visualRecord':airport,'claim':'actual10layouts,74source tiles,radar/windsock cycles; current recorded image hashes verified'}]
  elif cat in ['bridge','tunnel']:
   qs+=[qa['transport-runtime-validation'],qa['transport-lane-validation']];vs=[{'visualRecord':lane,'claim':'actual72tunnel states,156unique flat/rising/falling bridge images and native material UV; current17pages hashes verified'}]
  elif cat=='station':
   if req in ['station-dock','station-buoy']:qs+=[qa['services-validation']];vs=contact(['previews/world/water-station-layouts-contact.jpg'])
   else:qs+=[qa['transport-runtime-validation']];vs=contact(['previews/world/runtime-station.jpg','previews/world/runtime-depot.jpg'])
  elif cat=='signal':qs+=[qa['services-validation']];vs=contact(['previews/world/signal-states-contact.jpg','previews/world/signal-directions-state-contact.jpg'])
  elif cat=='rail':vs=contact(['previews/world/rail-contact.jpg'])
  elif cat=='road':
   if req in ['road-road','road-tram']:qs+=[qa['road-variants-validation']];vs=contact(['previews/world/road-context-slope-contact.jpg','previews/world/road-snow-masks-contact.jpg'])
   else:qs+=[qa['services-validation']];vs=contact(['previews/world/crossing-states-contact.jpg'])
  elif cat=='terrain':
   if req=='terrain-foundation':qs+=[qa['services-validation']];vs=contact(['previews/world/foundation-slopes-contact.jpg'])
   elif req=='terrain-fence':qs+=[qa['services-validation']];vs=contact(['previews/world/fence-styles-contact.jpg'])
   else:qs+=[qa['terrain-validation']];vs=contact(['previews/world/terrain-repeat.jpg','previews/world/terrain-slopes.jpg'])
  elif cat=='water':
   if req=='water-aqueduct':qs+=[qa['transport-runtime-validation']];vs=contact(['previews/world/aqueduct-joins.jpg'])
   elif req=='water-lock':qs+=[qa['services-validation']];vs=contact(['assets/world/infrastructure/mechanics/lock-NW-low-closed.png','assets/world/infrastructure/mechanics/lock-SW-high-open.png'])
   elif req=='water-shore':qs+=[qa['services-validation']];vs=contact(['previews/world/shore-postures-contact.jpg'])
   elif req=='water-sea':qs+=[qa['terrain-validation']];vs=contact(['previews/world/terrain-repeat.jpg'])
   else:qs+=[qa['services-validation']];vs=contact(['previews/world/water-connectivity-contact.jpg'])
  elif cat=='object':qs+=[qa['services-validation'],qa['houses-family-validation']];vs=contact(['previews/world/object-states-contact.jpg'])
  elif cat=='town':
   if req=='animation-fountain':qs+=[qa['services-validation']];vs=contact(['previews/world/fountain-loop-contact.jpg'])
   elif req.startswith('animation-'):qs+=[qa['services-validation']];vs=contact(['previews/world/object-states-contact.jpg'])
   else:qs+=[qa['houses-family-validation'],qa['houses-state-validation']];vs=[{'producerRecord':qa['houses-family-validation'],'claim':'actual45native house family paintings on5contact sheets checked;110source tile IDs×16state matrix and exact multicell reassembly validated'}]
  from additional_world_acceptance import for_row
  extra_qa,extra_visual=for_row(row);qs+=extra_qa;vs+=extra_visual
  checks=row['localVerification'];variants=checks.get('variantChecks',[]);ok=bool(row['artFiles'])and not row['missingItems']and bool(variants)and all(v['passed']for v in variants)and checks['mappedPNGChecksFailed']==0 and bool(vs)
  checks.update({'localArtReviewed':bool(vs),'qaEvidence':qs,'actualVisualEvidence':vs,'localReviewScope':'current artwork pixel/style samples and source-specific state/layout contracts with PNG/source hashes; no game runtime or user approval inferred'})
  row['acceptanceStatus']='passed-local-static-check-passed'if ok else'mapped-awaiting-final-review';row['artStatus']='locally-checked-user-review-pending'if ok else row['artStatus'];row['localAcceptedAt']=wp.now()if ok else None
  if not ok:pending.append({'id':req,'semanticMissing':row['missingItems'],'hasVariantChecks':bool(variants),'hasCurrentActualVisualEvidence':bool(vs)})
  reviewRows.append({'requirementId':req,'passed':ok,'qaEvidence':qs,'actualVisualEvidence':vs,'variantTests':len(variants),'PNGCount':len(row['artFiles'])})
 cov['localAcceptedRows']=len(cov['items'])-len(pending);cov['localAcceptanceAt']=wp.now();cov['userArtAcceptance']='pending';cov['unityValidated']=False;cov['pendingLocalReview']=pending
 wp.writej(R/'docs/WORLD_DELIVERY_COVERAGE.json',cov)
 report={'createdAt':wp.now(),'sourceRequirements':len(cov['items']),'locallyAccepted':cov['localAcceptedRows'],'pending':pending,'sourceManifests':pack['packSources'],'worldAssetCount':len(pack['assets']),'scope':'local artwork/state/layout review only; user acceptance and Unity remain pending','rows':reviewRows,'unityValidated':False,'userArtAcceptance':'pending'}
 wp.writej(R/'records/world-production/final-source-acceptance.json',report)
 if pending:print(json.dumps({'accepted':cov['localAcceptedRows'],'pending':pending},ensure_ascii=False));return
 pack['status']='本地美术、状态与资源检查通过；待用户美术验收';pack['coverageSummary']=f"{len(cov['items'])}项上游世界需求已完成显式映射、具体状态／布局核验及本地美术检查。用户美术验收与Unity运行验证待后续开展。";pack['coverage']['locallyAccepted']=cov['localAcceptedRows'];pack['localAcceptanceRecord']='records/world-production/final-source-acceptance.json';wp.writej(R/'docs/WORLD_ASSET_MANIFEST.json',pack)
 status=load(R/'docs/WORLD_PRODUCTION_STATUS.json');status.update({'phase':'local-art-delivery','worldArt':'local-art-and-state-checks-passed-user-review-pending','locallyAcceptedSourceRows':cov['localAcceptedRows'],'userArtAcceptance':'pending','incompleteVariantRows':0});wp.writej(R/'docs/WORLD_PRODUCTION_STATUS.json',status)
 preview=R/'previews/world/index.html';view=copy.deepcopy(pack)
 for a in view['assets']:a['previewImage']=Path(os.path.relpath(R/a['image'],preview.parent)).as_posix()
 for a in view['animations']:
  a['previewFrames']=[Path(os.path.relpath(R/f,preview.parent)).as_posix()for f in a.get('frames',[])];assembly=a.get('binding',{}).get('assemblyPreviewFrames',[])
  if assembly:a['previewAssemblyFrames']=[Path(os.path.relpath(R/f,preview.parent)).as_posix()for f in assembly]
 template=(R/'tools/world_preview_template.html').read_text(encoding='utf8');preview.write_text(template.replace('__WORLD_MANIFEST__',json.dumps(view,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
 print(json.dumps({'locallyAccepted':cov['localAcceptedRows'],'pending':pending,'formalPNGCount':len(pack['assets']),'userArtAcceptance':'pending','unityValidated':False},ensure_ascii=False))
if __name__=='__main__':main()

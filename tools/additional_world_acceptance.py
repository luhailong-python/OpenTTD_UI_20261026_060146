"""Require current dedicated evidence for each newly repaired source variant."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]

SPECS=[
 ('foundation','records/world-production/foundation-geometry-validation.json','records/world-production/foundation-visual-review.json',lambda r:r['id']=='terrain-foundation'),
 ('bridge-railtypes','records/world-production/bridge-railtypes-validation.json','records/world-production/bridge-railtypes-visual-review.json',lambda r:r['category']=='bridge'),
 ('industry-particles','records/world-production/industry-fx-binding-validation.json','records/world-production/industry-fx-visual-review.json',lambda r:r['id'] in ['animation-industry-machinery','industry-01-power-station','industry-34-bubble-generator']),
 ('field-stages','records/world-production/field-stages-validation.json','records/world-production/field-stages-visual-review.json',lambda r:r['id']=='terrain-field'),
 ('snow-desert-coverage','records/world-production/terrain-density-quarter-repair.json','records/world-production/terrain-density-quarter-visual.json',lambda r:r['id'] in ['terrain-snow','terrain-desert']),
 ('shore-geometry','records/world-production/shore-geometry-validation.json','records/world-production/shore-geometry-visual-review.json',lambda r:r['id']=='water-shore'),
 ('rocks-overlay','records/world-production/rocks-overlay-validation.json','records/world-production/rocks-overlay-visual-review.json',lambda r:r['id']=='terrain-rocks'),
 ('road-oneway','records/road-oneway-validation.json','records/road-oneway-visual-review.json',lambda r:r['id']=='road-oneway-markings'),
 ('roadside','records/roadside-validation.json','records/roadside-visual-review.json',lambda r:r['id'] in ['road-road','road-tram']),
 ('rail-reservation','records/rail-reservation-validation.json','records/rail-reservation-visual-review.json',lambda r:r['id'] in ['rail-rail','rail-electric','rail-monorail','rail-maglev']),
 ('fence-adapter','records/fence-adapter-validation.json','records/fence-adapter-visual-review.json',lambda r:r['id'] in ['terrain-fence','rail-rail','rail-electric','rail-monorail','rail-maglev']),
]

def load(name):return json.loads((R/name).read_text(encoding='utf-8-sig'))
def sha(name):return hashlib.sha256((R/name).read_bytes()).hexdigest()
def snapshot(name):return {'file':name,'sha256':sha(name)}

def checked_evidence(qa_name,visual_name):
 q=load(qa_name)
 if q.get('failures') or q.get('failed') or q.get('warnings') or q.get('complete') is False:
  raise ValueError('Unresolved dedicated package QA: '+qa_name)
 v=load(visual_name)
 if not(v.get('localVisualPassed')is True or str(v.get('result','')).startswith('local-')):
  raise ValueError('No actual local artwork review: '+visual_name)
 if v.get('manifest') and sha(v['manifest'])!=v.get('manifestSHA256'):
  raise ValueError('Stale dedicated visual manifest: '+visual_name)
 pages=v.get('items',v.get('pages',v.get('reviewedPages',[])))
 if not pages:raise ValueError('Actual visual pages missing: '+visual_name)
 for page in pages:
  file=page.get('file',page.get('image'))
  if not file or not page.get('sha256') or sha(file)!=page['sha256']:
   raise ValueError('Stale actual review page: '+str(file))
 dependency=q.get('manifest')
 if isinstance(dependency,dict):
  file=dependency.get('file',dependency.get('path'));digest=dependency.get('sha256')
 elif isinstance(dependency,str):file=dependency;digest=q.get('manifestSHA256')
 else:file=None;digest=None
 if file and digest and sha(file)!=digest:raise ValueError('Stale dedicated QA manifest: '+qa_name)
 return snapshot(qa_name),{'visualRecord':snapshot(visual_name),'actualCurrentPages':len(pages),'claim':'Dedicated current-hash source-state/geometry QA and actual artwork inspection; user and Unity pending.'}

def for_row(row):
 qa=[];visual=[]
 for _,qn,vn,predicate in SPECS:
  if predicate(row):
   a,b=checked_evidence(qn,vn);qa.append(a);visual.append(b)
 return qa,visual

def all_evidence():
 return {name:checked_evidence(qn,vn)for name,qn,vn,_ in SPECS}

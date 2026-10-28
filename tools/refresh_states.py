from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
import render_screens as r
m=r.readj('docs/UI_MASTER_MANIFEST.json')
s=next(s for s in m['screens']if s['id']=='54-vehicle-groups')
im,regs=r.make(s);p=s['designPath'];im.convert('RGB').save(r.ROOT/p,optimize=True);pr=r.readj(p+'.generation.json');r.record_derived(p,s,pr['operation'],pr['derivedFrom'])
r.savej('docs/layouts/'+s['id']+'.json',{'screenId':s['id'],'referenceResolution':[1920,1080],'textRegions':regs,'spritePlacements':r.placements.copy()})
im.thumbnail((480,270));im.convert('RGB').save(r.ROOT/s['thumbnailPath'],quality=85)
for s in m['screens']:
 for st in s['states']:
  im=r.statepreview(s,st);p=st['previewPath'];im.convert('RGB').save(r.ROOT/p,optimize=True)
  pr=r.readj(p+'.generation.json');r.record_derived(p,s,pr['operation'],pr['derivedFrom'])
  r.savej('docs/layouts/states/'+s['id']+'--'+st['id']+'.json',{'screenId':s['id'],'stateId':st['id'],'referenceResolution':[960,600],'textRegions':r.regions.copy(),'spritePlacements':r.placements.copy()})
r.savej('docs/UI_MASTER_MANIFEST.json',m);print('state buttons moved above border; missing glyph repaired',r.issues)


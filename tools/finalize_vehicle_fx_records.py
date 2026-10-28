from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rt=read(R/'docs/VEHICLE_RUNTIME_MANIFEST.json');rot='assets/world/vehicles/rotor/manifest.json'
for m in rt['models']:
 for e in m['sprites']:
  for s in e['states']:
   s['usesBaseBody']=s['file']==e['body'];s['sharedBodyWhenClosed']=s['state']in['empty','loaded']and m['familyId']not in['wagon-hopper','wagon-flat','road-open','road-flat','ship-cargo']
 if m['familyId']=='air-helicopter':m['effectManifest']=rot
 save(R/'assets/world/vehicles/models'/str(m['id']).zfill(3)/'manifest.json',m)
save(R/'docs/VEHICLE_RUNTIME_MANIFEST.json',rt)
fx=read(R/'docs/EFFECT_RUNTIME_MANIFEST.json')
for f in fx['effects']:
 if f['sourceId']in[0,1,2,4,6,10,11]:
  p=R/f['manifest'];j=read(p);j['emitterPx']=[256,408];j['pivot']=[.5,1-408/512]
  for e in j['frames']:
   e['pivot']=j['pivot'];e['emitterPx']=j['emitterPx'];save(R/(e['file']+'.derivation.json'),e)
  save(p,j)
fx['effects'][9]['sourceImageMapping']={'generate0-2':'bubble-generation frames0-2;tick switches tofloat whenSprite reachesGENERATE_3','float0-2':'bubble-float','burst7-9':'bubble-burst;extra terminal paintedkey available','absorb10-14':'bubble-absorb'}
save(R/'docs/EFFECT_RUNTIME_MANIFEST.json',fx)
p=R/'assets/world/effects/furnace-flame/manifest.json';j=read(p);j['emitterPx']=[256,408]
for e in j['frames']:e['pivot']=[.5,1-408/512];e['emitterPx']=[256,408];save(R/(e['file']+'.derivation.json'),e)
save(p,j)
source=(R/'reference/OpenTTD/src/effectvehicle.cpp').read_text(encoding='utf-8');block=source.split('static const BulldozerMovement _bulldozer_movement[] = {')[1].split('};',1)[0];moves=[list(map(int,m))for m in re.findall(r'\{\s*(\d+),\s*(\d+),\s*(\d+)\s*\}',block)]
p=R/'assets/world/effects/bulldozer-directions/manifest.json';j=read(p);j['sourceMovementTable']={'source':'src/effectvehicle.cpp:270','columns':['worldDirectionIndex','bodyImageIndex','durationSteps'],'rows':moves,'movementWorldIncrements':[[-1,0],[0,1],[1,0],[0,-1]],'sourceTickInterval':8,'implementation':'data for later integration only; preview does not execute game rules'};save(p,j)
p=R/'docs/DISASTER_RUNTIME_MANIFEST.json';j=read(p);j['newIndependentNativeProps']=11;j['nativePropFacingImages']=17;j['countExplanation']='9 native airship/UFO/aircraft state paintings +8 submarine view paintings represent11 body/state subjects; shadows androtor are derivatives/reuse, not15 unrelated nativepaintings.';save(p,j)
# Normalize only metadata purpose; never rewrite historical model evidence.
for p in (R/'assets/world/vehicles/families').glob('*/atlas.png.generation.json'):
 j=read(p);pr=j.get('promptFile')or(j.get('prompt')if len(j.get('prompt',''))<200 else None)
 if pr and(R/pr).is_file():j['promptFile']=pr;j['prompt']=(R/pr).read_text(encoding='utf-8')
 for i,x in enumerate(j.get('references',[])):x['purpose']='confirmed Taoist chibi style painting'if i<2 else'world camera and visual setting'if'world-viewport'in x['path']else'heading/layout guide; code diagram,not painted art'
 save(p,j)
# Every derived review/contact/GIF is indexed to explicit images or clip manifests.
preview=[]
allfamilies=[read(p)for p in sorted((R/'assets/world/vehicles/families').glob('*/manifest.json'))]
for p in (R/'previews/vehicles').glob('*'):
 if p.suffix.lower()not in['.jpg','.gif','.png']:continue
 preview.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p),'operation':'downscaled contact/painted body and mechanical rotor assembly preview; no modelcall','sources':[{'manifest':f'assets/world/vehicles/families/{f["familyId"]}/manifest.json'}for f in allfamilies]})
for p in (R/'previews/world/effects').glob('*.gif'):
 m=next((f for f in (R/'assets/world/effects').rglob('manifest.json')if read(f)['id'].replace('/','-')==p.stem),None)
 preview.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p),'operation':'RGBA frames composited on jade inspection background, GIF encoded; not AI video','sourceManifest':m.relative_to(R).as_posix()if m else None})
save(R/'records/vehicle-fx-preview-manifest.json',{'previews':preview})
print('state alias terminology, fixed emitters, source movement data, all provenance preview links finalized')

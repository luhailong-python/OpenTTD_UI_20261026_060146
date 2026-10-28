from pathlib import Path
from PIL import Image
import json,hashlib,datetime,collections
R=Path(__file__).resolve().parents[1];checks=[]
def check(id,ok,detail=None):checks.append({'id':id,'ok':bool(ok),'detail':detail})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def png(path,hashvalue=None,canvas=(512,512)):
 p=R/path;check(path+':exists',p.is_file())
 if not p.is_file():return
 im=Image.open(p);check(path+':rgba',im.mode=='RGBA',im.mode);check(path+':size',im.size==canvas,list(im.size))
 if im.mode=='RGBA':
  a=im.getchannel('A');b=a.point(lambda x:255 if x>=64 else 0).getbbox();check(path+':alpha',a.getextrema()[0]==0 and a.getextrema()[1]>0,a.getextrema());check(path+':border',b and min(b[0],b[1],im.width-b[2],im.height-b[3])>=4,b)
 if hashvalue:check(path+':sha',sha(p)==hashvalue)
j=read(R/'docs/VEHICLE_RUNTIME_MANIFEST.json');check('vehicle256IDs',sorted(x['id']for x in j['models'])==list(range(256)))
check('vehicleCounts',dict(collections.Counter(x['transport']for x in j['models']))=={'train':116,'road':88,'ship':11,'aircraft':41})
seen=set();distinctloads=0;sharedstates=0
for m in j['models']:
 check(f'model{m["id"]}:directions',[x['direction']for x in m['sprites']]==['N','NE','E','SE','S','SW','W','NW'])
 for e in m['sprites']:
  if e['body']not in seen:png(e['body'],e['sha256']);seen.add(e['body'])
  for s in e['states']:
   if s['file']not in seen:png(s['file'],s['sha256']);seen.add(s['file'])
   if s['visuallyDifferentFromEmpty']:
    differs=sha(R/s['file'])!=sha(R/e['body']);check(s['file']+':visibleLoadDiffers',differs);distinctloads+=int(differs)
   if s['sharedBodyWhenClosed']:sharedstates+=1
for p in sorted((R/'assets/world/vehicles/families').glob('*/manifest.json')):
 f=read(p);check(f['familyId']+':8frames',len(f['frames'])==8)
 for e in f['frames']:png(e['file'],e['sha256']);check(e['file']+':noClippedSource',not e.get('clippedSolidPixels',True))
 receipt=read(R/(f['atlas']+'.generation.json'));check(f['familyId']+':unexposedModelRecorded',receipt.get('actualModel')is None and receipt.get('actualQuality')is None)
for p in sorted((R/'assets/world/vehicles/rotor').glob('*.png')):png(p.relative_to(R).as_posix())
for p in sorted((R/'assets/world/effects').rglob('*.png')):png(p.relative_to(R).as_posix())
effects=read(R/'docs/EFFECT_RUNTIME_MANIFEST.json');disasters=read(R/'docs/DISASTER_RUNTIME_MANIFEST.json');check('effect12IDs',sorted(e['sourceId']for e in effects['effects'])==list(range(12)));check('disaster15IDs',sorted(e['sourceId']for e in disasters['subtypes'])==list(range(15)))
for e in effects['effects']+disasters['subtypes']:
 for p in ([e['manifest']]if'manifest'in e else list(e['manifests'].values())):check(p+':mappedManifestExists',(R/p).is_file())
failures=[x for x in checks if not x['ok']];result={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(checks),'passed':len(checks)-len(failures),'failures':failures,'modelPNGs':len(seen),'visibleCargoStatesDifferent':distinctloads,'sharedClosedBodyStates':sharedstates,'modelCount':len(j['models']),'familyCount':27,'facings':216,'effectTypeCount':12,'disasterSubtypeCount':15,'unityVerified':False,'limitations':['Per-ID models are declared family livery/chassis/load derivatives, not256 independent native paintings.','Source model and quality fields not exposed by built-in tool remain unconfirmed.','Footprint anchors, PPU, source tick timing and sorting still need next-stage Unity verification.']}
(R/'records/vehicle-fx-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))

from pathlib import Path
from PIL import Image
import json,datetime,hashlib
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
qa=read(R/'records/vehicle-fx-validation.json');assert not qa['failures']
browser=read(R/'records/vehicle-fx-browser-validation.json');assert browser['passed']
rt=read(R/'docs/VEHICLE_RUNTIME_MANIFEST.json')
for m in rt['models']:
 m['status']='local-art-checked';m['acceptance']={'localRecord':'records/vehicle-fx-validation.json','userArtAcceptance':'pending','unityVerified':False};save(R/'assets/world/vehicles/models'/str(m['id']).zfill(3)/'manifest.json',m)
rt['acceptance']={'localChecks':qa['checks'],'localPassed':qa['passed'],'browserChecks':len(browser['checks']),'userArtAcceptance':'pending','unityVerified':False};save(R/'docs/VEHICLE_RUNTIME_MANIFEST.json',rt)
contract=read(R/'docs/VEHICLE_PRODUCTION_CONTRACT.json')
for m in contract['models']:m['artStatus']='local-art-checked'
for f in contract['families']:f['artStatus']='local-art-checked'
contract['production']['localAcceptanceRecord']='records/vehicle-fx-validation.json';contract['production']['userArtAcceptance']='pending';save(R/'docs/VEHICLE_PRODUCTION_CONTRACT.json',contract)
source=read(R/'docs/VEHICLE_SOURCE_DATA.json');source['artStatusFieldsAreResearchSnapshot']=True;source['currentProductionManifest']='docs/VEHICLE_RUNTIME_MANIFEST.json';save(R/'docs/VEHICLE_SOURCE_DATA.json',source)
for p in (R/'assets/world/vehicles/families').glob('*/manifest.json'):
 j=read(p);j['spriteRegistration']='ownership-aware actual bodies and nearby accessories; family scale<=1; fixed512 canvas and translated footprint anchors; Unity unverified';entries=[]
 for e in j['frames']:
  im=Image.open(R/e['file']);a=im.getchannel('A');b=a.point(lambda x:255 if x>=64 else 0).getbbox();entries.append({'direction':e['direction'],'file':e['file'],'size':list(im.size),'alpha':a.getextrema(),'solidBBox':b,'contentPresent':bool(b),'canvasBorderClear':min(b[0],b[1],512-b[2],512-b[3])>=4,'noClippedSource':not e['clippedSolidPixels']})
 j['qa']=entries;j['userArtAcceptance']='pending';save(p,j)
for name in ['EFFECT_RUNTIME_MANIFEST.json','DISASTER_RUNTIME_MANIFEST.json']:
 p=R/'docs'/name;j=read(p);j['localAcceptanceRecord']='records/vehicle-fx-validation.json';j['userArtAcceptance']='pending';save(p,j)
print('current contract/model/family statuses reflect completed localQA; user/Unity acceptance stillpending')

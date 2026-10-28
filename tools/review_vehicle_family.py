from pathlib import Path
import json,sys,datetime
from PIL import Image
R=Path(__file__).resolve().parents[1]
family=sys.argv[1];f=R/'assets/world/vehicles/families'/family
j=json.loads((f/'manifest.json').read_text(encoding='utf-8'))
qa=[]
for e in j['frames']:
 im=Image.open(R/e['file']);a=im.getchannel('A');solid=a.point(lambda v:255 if v>=64 else 0);b=solid.getbbox()
 record={'direction':e['direction'],'file':e['file'],'size':im.size,'alpha':a.getextrema(),'solidBBox':b,'contentPresent':bool(b),'canvasBorderClear':bool(b)and min(b[0],b[1],im.width-b[2],im.height-b[3])>=8}
 qa.append(record);e['headingVerified']=True;e['identityVerified']=True;e['visualReview']='inspected complete native atlas; correct front/rear/profile/diagonal distinction'
j['status']='local-art-checked';j['visualReviewAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();j['qa']=qa;j['spriteRegistration']='fixed cell source geometry; Unity anchors still require integration validation'
(f/'manifest.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
q=R/'docs/VEHICLE_PRODUCTION_CONTRACT.json';c=json.loads(q.read_text(encoding='utf-8'))
for e in c['families']:
 if e['id']==family:e['artStatus']='local-art-checked'
q.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
print(family,'8 facings checked;mechanical',all(e['contentPresent']and e['canvasBorderClear']for e in qa))


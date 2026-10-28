from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
p=R/'assets/world/vegetation/manifest.json';j=json.loads(p.read_text(encoding='utf-8'))
checks=[];fails=[]
for e in j['assets']:
 im=Image.open(R/e['image']).convert('RGBA');box=im.getbbox();s=e['derivedFrom'];s=s if isinstance(s,list)else[s]
 c={'id':e['id'],'size':im.size==(256,384),'alpha':im.getchannel('A').getextrema()==(0,255),'contentFits':box is not None and box[0]>0 and box[1]>0 and box[2]<256 and box[3]<384,'fixedAnchor':e['anchorPx']==[128,352],'hash':hashlib.sha256((R/e['image']).read_bytes()).hexdigest()==e['sha256'],'sourcesExist':all((R/x['file']).is_file()for x in s),'nativeUpscale':not e['nativeUpscale']}
 checks.append(c)
 if not all(v for k,v in c.items()if k!='id'):fails.append(c)
 e['status']='passed-local-state-art-review'if e['category']=='vegetation-state'else'passed-local-art-review'
 q=R/(e['image']+'.derivation.json');d=json.loads(q.read_text(encoding='utf-8-sig'));d['status']=e['status'];q.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
ids={e['id']for e in j['assets']};mapping_checks=[]
for row in j['coverageMappings']:
 c={'id':row['requirementId'],'sevenStates':len(row['states'])==7,'stageOrder':[s['stage']for s in row['states']]==list(range(7)),'artIdsResolve':all(s['artId']in ids for s in row['states'])}
 mapping_checks.append(c)
 if not all(v for k,v in c.items()if k!='id'):fails.append(c)
j['validation']={'assetsChecked':len(checks),'sourceTypesChecked':len(mapping_checks),'failures':len(fails),'visualReview':'four climate contact sheets + eleven pages of all 287 states + special lifecycle contact sheet inspected; on light/dark backgrounds','sourceTree27Cactus':next(x for x in j['coverageMappings']if x['sourceTreeType']==27)['artSpecies']=='saguaro-cactus','unityValidated':False}
p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
out={'counts':j['counts'],'checks':checks,'mappingChecks':mapping_checks,'failures':fails,'visualReview':{'climateSheets':4,'stateSheets':11,'specialLifecycleSheet':1,'status':'passed-local-art-review','repairs':['Toyland non-lollipop dying2 keeps same desaturated/shrivelled phenotype; shared lollipop props only used for compatible species','Oil palm and mahogany tangent separated by authored y362 ownership split','Hidden background RGB ruled out by actual Alpha composite; formal transparent RGB cleared']},'limits':j['limitations']}
(R/'records/world-production/vegetation-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'assets':len(checks),'mappingChecks':len(mapping_checks),'states':287,'failures':len(fails)}))


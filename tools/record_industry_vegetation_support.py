from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def record(out,sources,operation):
 im=Image.open(out);entry={'file':out.relative_to(R).as_posix(),'sha256':sha(out),'width':im.width,'height':im.height,'operation':operation,'nativeModelGeneration':False,'derivedFrom':[{'file':p.relative_to(R).as_posix(),'sha256':sha(p),'record':(p.relative_to(R).as_posix()+'.derivation.json')if Path(str(p)+'.derivation.json').is_file()else(p.relative_to(R).as_posix()+'.generation.json')}for p in sources]}
 savej(Path(str(out)+'.derivation.json'),entry);return entry
ip=R/'assets/world/industries/manifest.json';industry=readj(ip);sheets=[]
for a in industry['animations']:
 p=R/a['sheet'];e=record(p,[R/x for x in a['frames']],'4x3 lossless packing of twelve actual derivative frames; redundant engine slicing sheet, not additional painted animation detail');e.update({'grid':[4,3],'cellSize':[256,256],'pivotUnity':[.5,.5],'unityTypeSuggestion':'Sprite/Multiple, grid256, not validated in Unity'});sheets.append(e)
industry['animationSheetArtifacts']=sheets;industry['counts']['animationSheets']=len(sheets);industry['counts']['formalSpritePNGs']=len(industry['assets']);industry['counts']['packagedPNGs']=len(industry['assets'])+len(sheets)
previews=[]
for letter in 'abcde':
 e=readj(R/'records/world-production'/('industry-'+letter+'-extraction.json'));p=R/'previews/world'/('industries-'+letter+'.jpg');previews.append(record(p,[R/x['file']for x in e['items']],'review montage over alternating ivory/dark jade mattes; labels outside art; not new native painting'))
mains=[x for x in industry['assets']if x['category']=='industry']
for i in range(8):
 p=R/'previews/world'/('industry-construction-'+str(i+1)+'.jpg');sources=[R/s['image']for x in mains[i*5:i*5+5]for s in x['constructionStates']];previews.append(record(p,sources,'review montage of four static industry construction stages, downscaled for review, alternating ivory/jade matte'))
industry['previewArtifacts']=previews;savej(ip,industry)
vp=R/'assets/world/vegetation/manifest.json';v=readj(vp);vprev=[]
for climate in ['temperate','arctic','tropical','toyland']:
 p=R/'previews/world'/('vegetation-'+climate+'.jpg');sources=[R/e['image']for e in v['assets']if e['category']=='vegetation'and e['climate']==climate];vprev.append(record(p,sources,'review montage of actual formal trees over ivory/jade mattes, no new generated detail'))
mains=sorted([e for e in v['assets']if e['category']=='vegetation'],key=lambda e:e['sourceTreeType'])
for i in range(11):
 p=R/'previews/world'/('vegetation-states-'+str(i+1)+'.jpg');sources=[R/s['image']for e in mains[i*4:i*4+4]for s in e['states']];vprev.append(record(p,sources,'seven-state review montage; preview downscale only; not a smooth biological growth animation'))
p=R/'previews/world/tree-lifecycle-special.jpg';sources=[R/e['image']for e in v['assets']if e['id'].startswith('tree-lifecycle-')and e['derivedFrom']['file'].endswith('with-backdrop.png')];vprev.append(record(p,sources,'alpha-composited contact sheet on ivory/dark jade, labels for review'))
p=R/'previews/world/lifecycle-alpha-composite.jpg';vprev.append(record(p,[R/'source-art/world/tree-lifecycle-special-with-backdrop.png'],'native RGBA correctly composited over ivory matte to inspect actual alpha; hidden RGB discarded by compositing, no new painted content'))
v['previewArtifacts']=vprev;savej(vp,v)
print(json.dumps({'industrySprites':len(industry['assets']),'industryPackedSheets':len(sheets),'industryPreviews':len(previews),'vegetationSprites':len(v['assets']),'vegetationPreviews':len(vprev)}))


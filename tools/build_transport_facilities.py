"""World station/depot/bridge production. Only extracts or transforms painted pixels."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance
import numpy as np
from scipy import ndimage
import hashlib,json,datetime
R=Path(__file__).resolve().parents[1]
OUT=R/'assets/world/infrastructure/transport'
OUT.mkdir(parents=True,exist_ok=True)
def rel(p):return Path(p).relative_to(R).as_posix()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,q):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
ASSETS=[];IMAGES={};QA=[]
def emit(aid,im,srcs,operation,category='infrastructure',requirements=None,anchor=(256,448),**extra):
 p=OUT/(aid+'.png');im.save(p)
 q={'id':aid,'image':rel(p),'sha256':sha(p),'width':im.width,'height':im.height,'anchorPx':list(anchor),'pivotUnity':[anchor[0]/im.width,1-anchor[1]/im.height],'derivedFrom':srcs,'operation':operation,'nativeUpscale':False,'unityValidated':False,'category':category,'sourceRequirementIds':requirements or [],'status':'produced-needs-visual-review',**extra}
 savej(Path(str(p)+'.derivation.json'),q);ASSETS.append(q);IMAGES[aid]=im;return q
def source(p):return {'file':rel(p),'sha256':sha(p),'record':rel(p)+'.generation.json' if Path(str(p)+'.generation.json').exists()else rel(p)+'.derivation.json'}
def extract(name,ids,cols=3,canvas=(512,512),maximum=384):
 sp=R/'source-art/world'/(name+'.png');im=Image.open(sp).convert('RGBA');arr=np.array(im);a=arr[:,:,3]
 lab,n=ndimage.label(a>32);sz=np.bincount(lab.ravel());big=np.flatnonzero(sz>8000);big=big[big!=0]
 if len(big)!=len(ids):raise ValueError((name,'independent native parts',len(big),'expected',len(ids)))
 seeds=np.where(np.isin(lab,big),lab,0);inds=ndimage.distance_transform_edt(seeds==0,return_distances=False,return_indices=True);own=seeds[tuple(inds)]
 centers=[]
 for v in big:
  y,x=np.where(seeds==v);centers.append((int(v),float(x.mean()),float(y.mean())))
 centers.sort(key=lambda v:v[2]);ordered=[]
 for start in range(0,len(ids),cols):ordered+=sorted(centers[start:start+cols],key=lambda v:v[1])
 for aid,(v,cx,cy) in zip(ids,ordered):
  aa=np.where((own==v)&(a>=8),np.clip(np.rint(a.astype(float)*255/max(1,int(a.max()))),0,255),0).astype('uint8')
  part=im.copy();part.putalpha(Image.fromarray(aa));bb=part.getbbox();part=part.crop(bb)
  factor=min(1,maximum/part.width,maximum/part.height);part=part.resize((round(part.width*factor),round(part.height*factor)),Image.Resampling.LANCZOS)
  can=Image.new('RGBA',canvas);at=(canvas[0]//2-part.width//2,canvas[1]-64-part.height);can.alpha_composite(part,at)
  emit(aid,can,[source(sp)],'Alpha connected-component ownership; preserve disconnected pieces by nearest compound; discard subvisible Alpha<8; normalize source254 to255; native crop; proportional downscale only; transparent fixed canvas',nativeCrop=list(bb),scaleApplied=factor,sourceAtlas=name,sourceComponent=int(v),contentSize=list(part.size),anchor=(canvas[0]//2,canvas[1]-64))
 return [a for a in ASSETS if a.get('sourceAtlas')==name]
STATION=['rail-platform','rail-platform-end','rail-canopy','rail-station-hall','rail-cargo-platform','rail-warehouse','rail-signalbox','rail-footbridge','rail-ticketgate']
DEPOT=['rail-depot-steam','rail-depot-electric','rail-depot-monorail','rail-depot-maglev','road-depot','bus-bay','truck-bay','ship-depot','tram-depot']
FAMILIES=['bridge-wood-native','bridge-stone-native','bridge-truss-native','bridge-concrete-native','bridge-cantilever-native','bridge-arch-native','bridge-suspension-native','bridge-tubular-native','bridge-covered-native']
MODULES=['bridge-wood-span','bridge-concrete-span','bridge-truss-span','bridge-cantilever-span','bridge-arch-span','bridge-suspension-span','bridge-suspension-tower','bridge-tubular-span','bridge-pier']
def run_extract():
 extract('station-kit',STATION);extract('depot-kit',DEPOT);extract('bridge-families',FAMILIES)
 extract('bridge-modules',MODULES)
 ids=[k+'-'+d for k in ['rail-depot-view','road-depot-view','tunnel-portal'] for d in ['SW','SE','NE','NW']]
 extract('service-directions',ids,4)
 # Opposite-axis symmetric components; explicitly reflected painted artwork.
 for aid in STATION+DEPOT+MODULES:
  a=next(x for x in ASSETS if x['id']==aid);im=IMAGES[aid]
  emit(aid+'-axis-y',ImageOps.mirror(im),[source(R/a['image'])],'Horizontal reflection of symmetric module for perpendicular isometric axis; lighting is inherited from native artwork, not a new painted view',symmetricAxisReflection=True)
def contact(name,rows,cols=3):
 w=cols*384;h=((len(rows)+cols-1)//cols)*424
 out=Image.new('RGB',(w,h),'#eae5d8');dr=ImageDraw.Draw(out);font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),15)
 for i,a in enumerate(rows):
  im=Image.open(R/a['image']).convert('RGBA');im.thumbnail((384,384))
  tile=Image.new('RGBA',(384,384),'#eae5d8'if i%2==0 else '#23433b');tile.alpha_composite(im,((384-im.width)//2,0))
  x=i%cols*384;y=i//cols*424;out.paste(tile.convert('RGB'),(x,y));dr.text((x+10,y+386),a['id'],font=font,fill='#12392f')
 p=R/'previews/world'/(name+'.jpg');out.save(p,quality=93)
 savej(Path(str(p)+'.derivation.json'),{'derivedFrom':[{'file':a['image'],'sha256':a['sha256']}for a in rows],'operation':'downsampled labeled light/dark Alpha contact sheet; no new model generation'})
def qa():
 failures=[]
 for a in ASSETS:
  im=Image.open(R/a['image']);bb=im.getbbox();ae=im.getchannel('A').getextrema();a['validation']={'rgba':im.mode=='RGBA','hasAlpha':ae[0]==0 and ae[1]>=240,'insideCanvas':bool(bb)and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height,'dimensions':im.size==(a['width'],a['height']),'hash':sha(R/a['image'])==a['sha256'],'noUpscale':not a['nativeUpscale']}
  for k,v in a['validation'].items():
   if not v:failures.append({'id':a['id'],'check':k,'bbox':list(bb)if bb else None})
  savej(Path(str(R/a['image'])+'.derivation.json'),a)
 return failures
def main():
 run_extract()
 for name in ['station-kit','depot-kit','bridge-families','bridge-modules','service-directions']:
  contact('transport-'+name,[a for a in ASSETS if a.get('sourceAtlas')==name],4 if name=='service-directions' else 3)
 failures=qa()
 savej(OUT/'manifest.json',{'schema':'world-transport-components.v1','assets':ASSETS,'animations':[],'qa':[{'level':'FAIL',**x}for x in failures],'artSource':'host_image_derivative','unityValidated':False})
 savej(R/'records/world-production/transport-extraction-validation.json',{'assets':len(ASSETS),'checks':len(ASSETS)*6,'failures':failures,'visualReview':'pending actual contact-sheet review','nativeUpcale':False})
 print(json.dumps({'assets':len(ASSETS),'failures':failures},ensure_ascii=False))
if __name__=='__main__':main()

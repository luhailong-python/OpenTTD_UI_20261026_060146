"""Separate eight actual painted vehicles, including art crossing nominal cells.
Uses eight body owners and nearby accessory ownership, never a largest-only
component deletion. Source alpha and antialias pixels are retained at native scale.
Run with the dedicated sprite-forge Python (SciPy).
"""
from pathlib import Path
from PIL import Image,ImageFilter
from scipy import ndimage
import numpy as np,json,hashlib,sys,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def run(family):
 d=R/'assets/world/vehicles/families'/family;p=d/'manifest.json';j=json.loads(p.read_text(encoding='utf-8'));src=R/j['atlas']
 im=Image.open(src).convert('RGBA');arr=np.array(im);a=arr[:,:,3];solid=a>=64
 labels,n=ndimage.label(solid);counts=np.bincount(labels.ravel());objs=ndimage.find_objects(labels)
 majors=[i for i in range(1,n+1)if counts[i]>9000]
 if len(majors)!=8:raise ValueError(f'{family}: expected8 vehicle bodies, got {len(majors)}')
 owners={};centers={}
 for lab in majors:
  yy,xx=objs[lab-1];cx=(xx.start+xx.stop)/2;cy=(yy.start+yy.stop)/2
  owner=min(3,int(cx/im.width*4))+4*min(1,int(cy/im.height*2))
  if owner in owners:raise ValueError('ambiguous atlas body owner '+family)
  owners[owner]=[lab];centers[lab]=(cx,cy)
 main=np.isin(labels,majors);dist,idx=ndimage.distance_transform_edt(~main,return_indices=True);nearest=labels[tuple(idx)]
 discarded=[]
 for lab in range(1,n+1):
  if lab in majors:continue
  m=labels==lab;distance=float(dist[m].min());near=int(nearest[m][np.argmin(dist[m])]);owner=next(o for o,labs in owners.items()if labs[0]==near)
  # Preserve detached accessories when close to their real body. Fine isolated
  # gutter traces and model speckles beyond this envelope are recorded as removed.
  if counts[lab]>=3 and distance<=12:owners[owner].append(lab)
  else:discarded.append({'label':lab,'pixels':int(counts[lab]),'distanceToBody':round(distance,2)})
 frames=[];transport='aircraft'if family.startswith('air-')else'ship'if family.startswith('ship-')else'ground'
 for i,e in enumerate(j['frames']):
  labs=owners[i];m=np.isin(labels,labs)
  halo=ndimage.binary_dilation(m,iterations=3);halo&=(labels==0)|m
  piece=arr.copy();piece[:,:,3]=np.where(halo,a,0);selected=Image.fromarray(piece);box=selected.getbbox();crop=selected.crop(box)
  b=crop.getchannel('A').point(lambda x:255 if x>=64 else 0).getbbox();w=b[2]-b[0];h=b[3]-b[1]
  anchorx=(b[0]+b[2])/2
  if transport=='aircraft':anchory=(b[1]+b[3])/2;root=(256,256)
  else:
   dep={'N':.28,'S':.28,'E':.10,'W':.10,'NE':.20,'NW':.20,'SE':.20,'SW':.20}[e['direction']]
   anchory=b[3]-h*dep;root=(256,350)
  # Fit one family-wide scale, never an independent per-view stretch/enlargement.
  frames.append((e,crop,box,labs,anchorx,anchory,root,int(m.sum())))
 scale=1.
 for e,crop,box,labs,x,y,root,pix in frames:
  scale=min(scale,(root[0]-8)/max(x,1),(504-root[0])/max(crop.width-x,1),(root[1]-8)/max(y,1),(504-root[1])/max(crop.height-y,1))
 qa=[]
 for e,crop,box,labs,x,y,root,pix in frames:
  native=list(crop.size)
  if scale<1:crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
  paste=[round(root[0]-x*scale),round(root[1]-y*scale)];canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(crop,tuple(paste));out=d/(e['direction']+'.png');canvas.save(out)
  alpha=canvas.getchannel('A');bb=alpha.point(lambda x:255 if x>=64 else 0).getbbox();clipped=(pix!=int((np.array(canvas)[:,:,3]>=64).sum()))if scale==1 else False
  e.update({'sha256':sha(out),'sourceRectXYXY':list(box),'sourceComponentLabels':labs,'nativeSubjectSize':native,'uniformScale':scale,'paddingLeftTop':paste,'canvas':[512,512],'pivot':[root[0]/512,1-root[1]/512],'footprintAnchorPx':list(root),'alphaBBox':canvas.getbbox(),'alphaExtrema':alpha.getextrema(),'sourceSolidPixels':pix,'outputSolidPixels':int((np.array(canvas)[:,:,3]>=64).sum()),'clippedSolidPixels':clipped,'registrationMethod':'all8 native body owners + nearby accessory ownership; preserve original alpha3px halo; one family downscale if needed; translate to shared footprint anchor; Unity unverified','operation':'ownership-aware separation from actual native atlas, including parts over nominal grid; preserve actual RGBA, shared scale<=1 and transparent padding; no new AI call'})
  save(Path(str(out)+'.derivation.json'),e)
  qa.append({'direction':e['direction'],'borderClear':bool(bb)and min(bb[0],bb[1],512-bb[2],512-bb[3])>=4,'clipped':clipped,'sourceSolidPixels':pix,'outputSolidPixels':e['outputSolidPixels']})
 j.update({'registration':{'camera':'fixed orthographic30deg','root':list(root),'scale':scale,'status':'footprint art estimate; Unity not imported'},'registrationQA':qa,'separation':{'method':'eight owner components with all nearby disconnected accessories; native source alpha halo3px','componentCount':n,'bodyCount':8,'discardedGutterSpeckles':discarded},'status':'local-art-checked'})
 save(p,j);return{'family':family,'scale':scale,'ok':all(x['borderClear']and not x['clipped']for x in qa),'frames':8,'native':list(im.size)}
if __name__=='__main__':
 ids=sys.argv[1:]or[p.name for p in (R/'assets/world/vehicles/families').iterdir()if(p/'manifest.json').exists()]
 for id in ids:print(json.dumps(run(id)))

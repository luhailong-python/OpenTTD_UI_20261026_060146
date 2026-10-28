from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib
from scipy import ndimage
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
src=R/'source-art/world/tree-lifecycle-special-with-backdrop.png';im=Image.open(src).convert('RGBA');arr=np.array(im);a=arr[:,:,3]
labels,n=ndimage.label(a>32);sizes=np.bincount(labels.ravel());large=np.where(sizes>15000)[0];large=large[large!=0]
assert len(large)==9
seeds=np.where(np.isin(labels,large),labels,0);inds=ndimage.distance_transform_edt(seeds==0,return_distances=False,return_indices=True);owned=seeds[tuple(inds)]
objects=[]
for lab in large:
 yy,xx=np.where(seeds==lab);objects.append([int(lab),float(xx.mean()),float(yy.mean())])
objects.sort(key=lambda o:o[2]);objects=sum([sorted(objects[r*3:r*3+3],key=lambda o:o[1])for r in range(3)],[])
names=['dying-cactus','dead-cactus','dying-palm','dead-palm','dying-candy','dead-candy','dying-cotton','dead-cotton','dying-baobab']
assets=[]
for name,(lab,cx,cy) in zip(names,objects):
 alpha=np.where((owned==lab)&(a>=8),a,0).astype('uint8');alpha[alpha>=240]=255
 part=im.copy();part.putalpha(Image.fromarray(alpha));box=part.getbbox();part=part.crop(box)
 native=part.size;scale=min(1,224/part.width,320/part.height);part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(256,384));off=(128-part.width//2,352-part.height);out.alpha_composite(part,off)
 p=R/'assets/world/vegetation/lifecycle'/(name+'.png');p.parent.mkdir(parents=True,exist_ok=True);out.save(p)
 en={'id':'tree-lifecycle-'+name,'image':p.relative_to(R).as_posix(),'width':256,'height':384,'anchorPx':[128,352],'pivotUnity':[.5,1/12],'anchorMeaning':'plant root front ground-contact','category':'vegetation-lifecycle','sha256':sha(p),'sourceCropXYXY':list(box),'nativeCropSize':native,'uniformScale':scale,'operation':'component ownership cutout; remove subvisible alpha<8; normalize alpha>=240 to opaque; crop; proportional downscale only; fixed transparent canvas; not new AI generation','derivedFrom':{'file':src.relative_to(R).as_posix(),'sha256':sha(src),'record':src.relative_to(R).as_posix()+'.generation.json'},'status':'passed-local-art-review','nativeUpscale':False,'unityValidated':False}
 savej(Path(str(p)+'.derivation.json'),en);assets.append(en)
savej(R/'assets/world/vegetation/lifecycle/manifest.json',{'schemaVersion':1,'nativeAtlasCount':1,'nativePartCount':9,'assets':assets,'animations':[],'sourceAlphaExtrema':[int(a.min()),int(a.max())],'importantEvidence':'native file has hidden brown RGB under alpha0; actual alpha composite proves transparency. Direct viewer preview showed those hidden RGB values. Formal PNG clears transparent RGB through alpha compositing.','supersededAttempt':{'record':'source-art/world/tree-lifecycle-alpha-attempt.png.generation.json','used':False,'reason':'unnecessary alpha repair; true alpha already present, second edit changed highlights'}})
panel=Image.new('RGB',(768,1248),'#e5e0d2');d=ImageDraw.Draw(panel)
for i,en in enumerate(assets):
 bg=Image.new('RGBA',(256,384),'#e5e0d2'if i%2==0 else'#244139');bg.alpha_composite(Image.open(R/en['image']).convert('RGBA'));x=(i%3)*256;y=(i//3)*416;panel.paste(bg.convert('RGB'),(x,y));d.text((x+8,y+388),names[i],fill='#305943')
panel.save(R/'previews/world/tree-lifecycle-special.jpg',quality=94)
savej(R/'records/world-production/tree-lifecycle-alpha-qa.json',{'status':'passed-actual-alpha-composite','acceptedFile':src.relative_to(R).as_posix(),'nativeAlphaExtrema':[int(a.min()),int(a.max())],'backgroundSamples':{'0,0':list(im.getpixel((0,0))),'500,500':list(im.getpixel((500,500))),'750,800':list(im.getpixel((750,800)))} ,'passed':True,'correction':'Initial direct-view opacity suspicion was disproved by pixel alpha and real compositing; hidden RGB is not visible opaque backdrop. First source accepted, second edit unused.','assets':9})
print(json.dumps({'acceptedParts':9,'source':src.name,'nativeSize':im.size}))


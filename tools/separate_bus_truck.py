from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
r=Path(__file__).resolve().parents[1]; im=Image.open(r/'source-art/system-icons.png').convert('RGBA'); rgba=np.array(im);a=rgba[:,:,3];x0,x1,y0,y1=403,436,0,254
# Shortest transparent seam across the tight bus/truck gutter. Preserve source colours and alpha on either owned side.
cost=(a[y0:y1,x0:x1].astype(float)/255)**2*1000+np.abs(np.arange(x0,x1)-418)[None,:]*0.04
score=cost.copy();prev=np.zeros(score.shape,dtype=np.int16)
for y in range(1,y1-y0):
 for x in range(x1-x0):
  xx0=max(0,x-1);xx1=min(x1-x0,x+2);old=score[y-1,xx0:xx1];k=int(np.argmin(old))+xx0;score[y,x]+=score[y-1,k];prev[y,x]=k
p=int(np.argmin(score[-1]));seam=[]
for y in reversed(range(y1-y0)):
 seam.append(x0+p);p=int(prev[y,p])
seam=list(reversed(seam));print('seam bounds',min(seam),max(seam),'seamalpha max',max(int(a[y,seam[y]]) for y in range(y1)), 'alpha>128 pixels',sum(a[y,seam[y]]>128 for y in range(y1)))
m=json.loads((r/'docs/asset-icons-manifest.json').read_text(encoding='utf-8'))
for key,side in [('bus','left'),('truck','right')]:
 entry=next(x for x in m if x['id']==key);owned=rgba[y0:y1,221:637].copy(); xx=np.arange(221,637)[None,:];ss=np.array(seam)[:,None];mask=xx<ss if side=='left' else xx>=ss;owned[~mask]=0
 # remove the other complete image beyond the old cell (train is left of221; tram starts645).
 aa=owned[:,:,3];ys,xs=np.nonzero(aa>200); bx0=max(0,int(xs.min())-3); bx1=min(owned.shape[1],int(xs.max())+4);by0=max(0,int(ys.min())-3);by1=min(owned.shape[0],int(ys.max())+4); crop=Image.fromarray(owned[by0:by1,bx0:bx1]);w,h=crop.size;out=Image.new('RGBA',(256,256));dx=(256-w)//2;dy=(256-h)//2;out.paste(crop,(dx,dy));f=r/entry['file'];out.save(f);alpha=np.array(out)[:,:,3]
 entry.update(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),cropXYXY=[221+bx0,by0,221+bx1,by1],sourceCropSize=[w,h],paddingLeftTop=[dx,dy],operation='native rectangular crop, deterministic transparent-gutter seam ownership mask, and transparent padding; no colour editing or resampling; no new image generation',alphaBoundingBox=list(out.getchannel('A').getbbox()),transparentPixels=int((alpha==0).sum()),semiTransparentPixels=int(((alpha>0)&(alpha<255)).sum()),notes='Bus/truck source silhouettes nearly touch. A shortest low-alpha seam assigns native pixels to each side, preventing a neighbouring gold sliver. Every retained RGBA pixel equals the source.',seamSource={'xRange':[x0,x1],'yRange':[y0,y1],'xAtEachY':seam,'side':side,'maximumSeamAlpha':max(int(a[y,seam[y]]) for y in range(y1))})
 (f.with_name(f.name+'.derivation.json')).write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
(r/'docs/asset-icons-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
qa=Image.new('RGB',(1680,1764),(239,231,208)); from PIL import ImageDraw;dr=ImageDraw.Draw(qa)
for i,x in enumerate(m):
 xx=(i%6)*280+12;yy=(i//6)*294+8;tile=Image.open(r/x['file']);qa.paste(tile,(xx,yy),tile);dr.text((xx,yy+260),x['id'],fill=(28,75,66))
qa.save(r/'previews/icon-native-contact-sheet.jpg',quality=94)
(r/'previews/icon-native-contact-sheet.jpg.derivation.json').write_text(json.dumps({'file':'previews/icon-native-contact-sheet.jpg','operation':'native icon crops composited onto QA contact sheet with labels; no resampling','derivedFrom':[{'file':x['file'],'sha256':x['sha256']} for x in m]},ensure_ascii=False,indent=2),encoding='utf-8')
print('done')

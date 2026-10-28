from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import numpy as np,json,hashlib,datetime
r=Path(__file__).resolve().parents[1]; src=r/'source-art/system-icons.png'; im=Image.open(src).convert('RGBA'); a=np.array(im)[:,:,3]; sh=hashlib.sha256(src.read_bytes()).hexdigest(); outdir=r/'assets/icons';outdir.mkdir(exist_ok=True)
ids=[['train','bus','truck','tram','air','ship'],['station','bus-stop','dock','airport','depot','warehouse'],['rail','road','signal','bridge','tunnel','junction'],['town','industry','money','orders','timetable','map'],['company','chart','cargo','terrain','tree','build'],['settings','search','news','network','download','help']]
# Gutters individually verified against the native atlas silhouette/alpha profile.
rows=[(0,254,[0,221,423,637,818,1061,1254]),(254,463,[0,220,423,628,835,1048,1254]),(463,665,[0,223,450,601,842,1048,1254]),(665,864,[0,215,435,636,838,1025,1254]),(864,1049,[0,209,433,624,831,1050,1254]),(1049,1254,[0,216,420,620,837,1047,1254])]
entries=[]; now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for iy,(y0,y1,cols) in enumerate(rows):
 for ix,(x0,x1) in enumerate(zip(cols,cols[1:])):
  key=ids[iy][ix];sub=a[y0:y1,x0:x1]; ys,xs=np.nonzero(sub>200);cx0=max(x0,x0+int(xs.min())-3);cy0=max(y0,y0+int(ys.min())-3);cx1=min(x1,x0+int(xs.max())+4);cy1=min(y1,y0+int(ys.max())+4)
  box=[cx0,cy0,cx1,cy1];crop=im.crop(box);w,h=crop.size
  assert w<=256 and h<=256,(key,w,h)
  out=Image.new('RGBA',(256,256),(0,0,0,0)); dx=(256-w)//2;dy=(256-h)//2;out.paste(crop,(dx,dy));p=outdir/(key+'.png');out.save(p)
  arr=np.array(out);alpha=arr[:,:,3]; bbox=out.getchannel('A').getbbox()
  info=dict(id=key,file='assets/icons/'+key+'.png',width=256,height=256,format='PNG',mode='RGBA',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source='source-art/system-icons.png',sourceSha256=sh,sourceGenerationRecord='source-art/system-icons.png.generation.json',operation='native-resolution rectangular crop and transparent padding; no resampling, no alpha recolouring, no new image generation',cropXYXY=box,sourceCellXYXY=[x0,y0,x1,y1],sourceCropSize=[w,h],paddingLeftTop=[dx,dy],nativeResampling=False,alphaMin=int(alpha.min()),alphaMax=int(alpha.max()),transparentPixels=int((alpha==0).sum()),semiTransparentPixels=int(((alpha>0)&(alpha<255)).sum()),alphaBoundingBox=list(bbox),pivot=[0.5,0.5],border=[0,0,0,0],spriteType='2D and UI',spriteMode='Single',meshType='FullRect',filterMode='Bilinear',mipmaps=False,packing='UI_Icons atlas with 4px padding; preserve 256x256 canvas; runtime display normally 40–96px',createdAt=now,validationStatus='native-crop-alpha-checked',notes='Source bus/truck silhouettes are close; per-row cell boundary separates them. Very faint source alpha fringe is retained; no mathematical keying.')
  entries.append(info)
  (outdir/(key+'.png.derivation.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
(r/'docs/asset-icons-manifest.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
# QA contact sheet: direct thumbnails shown at native 256px; composited preview, not a new model render.
qa=Image.new('RGB',(6*280,6*294),(239,231,208));dr=ImageDraw.Draw(qa)
for i,x in enumerate(entries):
 xx=(i%6)*280+12;yy=(i//6)*294+8;tile=Image.open(r/x['file']);qa.paste(tile,(xx,yy),tile);dr.text((xx,yy+260),x['id'],fill=(28,75,66))
qp=r/'previews/icon-native-contact-sheet.jpg';qa.save(qp,quality=94)
(r/'previews/icon-native-contact-sheet.jpg.derivation.json').write_text(json.dumps({'file':'previews/icon-native-contact-sheet.jpg','operation':'native icon crops composited onto a QA contact sheet with labels; no resampling','derivedFrom':[{'file':x['file'],'sha256':x['sha256']} for x in entries]},ensure_ascii=False,indent=2),encoding='utf-8')
print('icons',len(entries),'max crops',max(x['sourceCropSize'][0] for x in entries),max(x['sourceCropSize'][1] for x in entries))
print([(x['id'],x['cropXYXY']) for x in entries])

# Apply the documented ownership seam for the source bus/truck contact.
import runpy
runpy.run_path(str(r/'tools/separate_bus_truck.py'))

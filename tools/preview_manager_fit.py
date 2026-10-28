"""Visible fit gates before213 source values are exported."""
from PIL import Image,ImageDraw,ImageFont
import math
import manager_face_parts as p
R=p.R;m=p.load(p.OUT/'fit-probes-manifest.json');rows=[s for s in m['compositionSamples']if s['id'].startswith(('baseline-','probe-'))];font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16);pages=[]
for start in range(0,len(rows),12):
 rr=rows[start:start+12];out=Image.new('RGB',(1280,math.ceil(len(rr)/4)*400),'#eae5d8');d=ImageDraw.Draw(out)
 for j,s in enumerate(rr):
  im=Image.open(R/s['image']).convert('RGBA');im.thumbnail((320,360));bg=Image.new('RGBA',(320,360),'#23433b'if j%2 else'#eae5d8');bg.alpha_composite(im,((320-im.width)//2,0));x=j%4*320;y=j//4*400;out.paste(bg.convert('RGB'),(x,y));d.text((x+6,y+369),s['id'],font=font,fill='#164F45')
 dest=p.PRE/('fit-probes-'+str(start//12+1)+'.jpg');out.save(dest,quality=97);p.savej(str(dest)+'.derivation.json',{'operation':'Actual final-candidate layered combinations on light/dark; proportional preview downsample; no AI generation','derivedFrom':[p.source(R/s['image'])for s in rr]});pages.append({'image':p.rel(dest),'sha256':p.sha(dest),'samples':[s['id']for s in rr]})
p.savej(R/'records/manager-fit-probe-pages.json',{'manifest':'assets/portraits/customization/fit-probes-manifest.json','manifestSHA256':p.sha(p.OUT/'fit-probes-manifest.json'),'pages':pages,'actualVisualReview':'pending current-hash actual inspection','unityValidated':False})
print('actual probe pages',len(pages))

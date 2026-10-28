"""Export available real base/chin parts before other mother atlases arrive."""
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
import manager_face_parts as p
R=p.R;c=p.PartCatalog();raw=p.load(p.OUT/'part-catalog.json')['assets'];bases=sorted([a for a in raw if a['family']=='base'],key=lambda a:a['nativeAtlasIndex']);checks=[];rows=[]
assert len(bases)==4
for style,src in enumerate(bases):
 original=Image.open(R/src['image']).convert('RGBA');head,jaw,owner=p.split_chin(original);mask=np.zeros((512,512,4),np.uint8);mask[owner]=255
 ma=c.emit('mf-style-'+str(style)+'-chin-mask',Image.fromarray(mask),[p.source(R/src['image'])],'Actual native lower-face band ownership DATA; not visible art','mask',sourceStyle=style)
 ba=c.emit('mf-style-'+str(style)+'-base-clean',head,[p.source(R/src['image']),p.source(R/ma['image'])],'Remove actual292:360 lower-face Alpha band only; separate chin supplies exact source pixels','base-clean',sourceStyle=style,removedOwnershipMask=ma['image'])
 for value in range(4 if style==0 else 1 if style==1 else 2):
  amount=[1,.96,.92,.88][value];part=p.chin_variant(jaw,amount);a=c.emit('mf-style-'+str(style)+'-chin-'+str(value),part,[p.source(R/src['image']),p.source(R/ma['image'])],'Actual lower-face band, fixed joining rows and bounded middle-width coordinate narrowing; no added paint','chin',sourceStyle=style,chinBandPx=[292,360],middleWidthScale=amount,joinRowsFixed=True)
  assembled=head.copy();assembled.alpha_composite(part);file=p.PRE/('base-style-'+str(style)+'-chin-'+str(value)+'.png');file.parent.mkdir(parents=True,exist_ok=True);assembled.save(file);rows.append((style,value,file));p.savej(str(file)+'.derivation.json',{'operation':'Actual complementary base and chin parts; unfeatured registration review only','derivedFrom':[p.source(R/ba['image']),p.source(R/a['image'])]})
  checks.append({'id':a['id']+'.fixed-seams','passed':bool(np.array_equal(np.asarray(part)[292],np.asarray(jaw)[292])and np.array_equal(np.asarray(part)[359],np.asarray(jaw)[359]))})
  if value==0:checks.append({'id':a['id']+'.original-reassembly','passed':assembled.tobytes()==original.tobytes()})
  checks.append({'id':a['id']+'.registered-visible-change','passed':value==0 or np.count_nonzero(np.asarray(assembled)!=np.asarray(original))>16})
preview=Image.new('RGB',(1280,3*414),'#eae5d8');d=ImageDraw.Draw(preview);font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16)
for i,(style,value,path)in enumerate(rows):
 im=Image.open(path).convert('RGBA');im.thumbnail((320,380));bg=Image.new('RGBA',(320,380),'#23433b'if i%2 else'#eae5d8');bg.alpha_composite(im,((320-im.width)//2,0));x=i%4*320;y=i//4*414;preview.paste(bg.convert('RGB'),(x,y));d.text((x+8,y+383),'style'+str(style+1)+' / chin'+str(value+1),font=font,fill='#164F45')
file=p.PRE/'base-chin-registration.jpg';preview.save(file,quality=96);p.savej(str(file)+'.derivation.json',{'operation':'Actual available native base/chin assembly contact; downsample review only, still deliberately unfeatured','derivedFrom':[p.source(path)for _,_,path in rows]})
p.savej(p.OUT/'base-catalog.json',{'createdAt':p.now(),'assets':c.assets,'sourceBases':raw,'status':'only actual unfeatured base/chin parts exported; remaining facial/clothing mothers pending; not complete manager art','unityValidated':False})
p.savej(R/'records/manager-base-validation.json',{'createdAt':p.now(),'actualBasePaintings':4,'actualChinVariants':9,'checks':checks,'failures':[q for q in checks if not q['passed']],'partial':True,'remaining':'Actual eyes/nose/mouth/hair/beard/clothing/accessories and235bindings/UI acceptance still pending','unityValidated':False});print(json.dumps({'bases':4,'chin':9,'checks':len(checks),'failures':sum(not q['passed']for q in checks)}))

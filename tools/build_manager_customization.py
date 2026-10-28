"""Bind real transparent face parts to all upstream values; static art only."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,numpy as np,argparse
import manager_face_parts as p
R=p.R;OUT=p.OUT;PRE=p.PRE;SPEC=p.extract(R)
MINIMUM={'base':4,'eyes':16,'nose':8,'mouth':12,'hair':9,'beard':3,'collar':4,'robe':3,'tie':6,'earring':3,'glasses':2}
def read_image(a):return Image.open(R/a['image']).convert('RGBA')
def mask_image(m):
 a=np.zeros((*m.shape,4),np.uint8);a[m]=255;return Image.fromarray(a)
def main(probes_only=False):
 catalog=p.load(OUT/'part-catalog.json');assets=catalog['assets'];groups={}
 for a in assets:groups.setdefault(a['family'],[]).append(a)
 for k,v in groups.items():v.sort(key=lambda a:(a.get('nativeAtlasIndex',0),a['id']))
 missing={k:{'required':n,'actual':len(groups.get(k,[]))}for k,n in MINIMUM.items()if len(groups.get(k,[]))<n}
 if missing:raise ValueError('Real source pieces missing; no fake production manifest: '+json.dumps(missing))
 c=p.PartCatalog();c.assets=assets.copy();by={a['id']:a for a in assets};base={};chin={};eye={};iris={};beard={};styled={};dressed={};robes={}
 def add(a):by[a['id']]=a;return a
 # Base / chin are actual complementary painted pixels, never a complete
 # preset face hidden below a new jaw. Both band joining rows stay fixed.
 for style in range(4):
  src=groups['base'][style];im=read_image(src);head,jaw,owner=p.split_chin(im)
  mask=add(c.emit('mf-style-'+str(style)+'-chin-mask',mask_image(owner),[p.source(R/src['image'])],'Actual native lower-face band ownership DATA; not visible art','mask',sourceStyle=style))
  base[style]=add(c.emit('mf-style-'+str(style)+'-base-clean',head,[p.source(R/src['image']),p.source(R/mask['image'])],'Remove only actual lower-face band Alpha; original unfeatured head/neck remains; chin supplied separately','base-clean',sourceStyle=style,removedOwnershipMask=mask['image']))
  count=4 if style==0 else 1 if style==1 else 2
  for value in range(count):
   amount=[1,.96,.92,.88][value];part=p.chin_variant(jaw,amount)
   chin[(style,value)]=add(c.emit('mf-style-'+str(style)+'-chin-'+str(value),part,[p.source(R/src['image']),p.source(R/mask['image'])],'Actual lower-face band crop; fixed top/bottom seam, bounded source-pixel lower-cheek narrowing; no added paint','chin',sourceStyle=style,chinBandPx=[292,360],middleWidthScale=amount,joinRowsFixed=True))
  yy,xx=np.indices((512,512));ar=np.asarray(head).copy();removed=(yy>=350)&((xx<196)|(xx>316))&(ar[:,:,3]>0);ar[removed]=0
  dressed[style]=add(c.emit('mf-style-'+str(style)+'-base-dressed',Image.fromarray(ar),[p.source(R/base[style]['image'])],'Head/neck body for clothing rig: suppress only bare shoulder roots outside central neck below350; no skin painting or replacement','base-dressed',sourceStyle=style,clothingHiddenShoulderRule={'belowY':350,'retainedNeckX':[196,316]}))
 # Native robes include baked inner lapels and a central clasp. Separate the
 # central neck/old clasp ownership from outer jacket, and use an actual white
 # collar mother as fixed inner garment. Selected collar remains a real layer.
 neckpoly=[(200,326),(312,326),(313,377),(291,430),(282,455),(282,493),(230,493),(230,455),(221,430),(199,377)];mm=Image.new('L',(512,512));ImageDraw.Draw(mm).polygon(neckpoly,fill=255);neck=np.asarray(mm)>0
 inner_src=groups['collar'][0];inner_im=read_image(inner_src);cloth_src=groups['robe'][0];cloth=read_image(cloth_src).crop((230,455,282,490))
 # Actual native ivory front-panel paint covers the removed old flower clasp
 # and the longer pendant in robe3. Copy/tile these real pixels, never paint a
 # replacement fabric colour or reconstruct its gold pattern from code.
 for top in[420,455,490]:inner_im.alpha_composite(cloth.crop((0,0,52,min(35,494-top))),(230,top))
 inner_ar=np.asarray(inner_im).copy();inner_ar[~neck]=0
 inner=add(c.emit('mf-fixed-inner-garment',Image.fromarray(inner_ar),[p.source(R/inner_src['image']),p.source(R/cloth_src['image'])],'Actual white inner-collar plus copied native ivory front-panel textile, clipped to common neck/old-necklace ownership; fixed underwear beneath selectable collar; old robe clasp/pendant not copied','fixed-inner',neckOwnershipPolygonPx=neckpoly,ivoryPatchSourceCropPx=[230,455,282,490],ivoryPatchDestinationTopPx=[420,455,490],ivoryPatchOperation='same-size copies/crop, never enlargement or new painted detail'))
 for n,src in enumerate(groups['robe'][:3]):
  native=read_image(src);ar=np.asarray(native).copy();owner=neck&(ar[:,:,3]>0);ar[owner]=0;mask=add(c.emit('mf-robe-'+str(n)+'-removed-neck-mask',mask_image(owner),[p.source(R/src['image'])],'Actual central inner-lapel and old-clasp ownership DATA, excluded from jacket body','mask',neckOwnershipPolygonPx=neckpoly))
  robes[n]=add(c.emit('mf-robe-'+str(n)+'-outer-clean',Image.fromarray(ar),[p.source(R/src['image']),p.source(R/mask['image'])],'Remove native baked central inner collar and chest clasp Alpha; preserve outer jacket, sleeve/shoulder embroidery and lapel trim; fixed actual white undergarment + selectable collar/tie replace removed centre','robe-clean',removedOriginalNeckMask=mask['image'],fixedInnerGarment=inner['image'],outsideOwnershipExactRGBA=bool(np.array_equal(ar[~owner],np.asarray(native)[~owner]))))
 # Iris ownership is actual chromatic paint inside measured eye ROIs. The
 # mask must contain real pixels before any palette binding can be declared.
 raw_iris={}
 for n,src in enumerate(groups['eyes'][:16]):
  im=read_image(src);boxes=src.get('irisBoxesPx',[[178,203,230,244],[282,203,334,244]]);mask=p.iris_ownership(im,boxes)
  if 'left'in src.get('closedIrisSides',[]):mask[:,:256]=False
  if 'right'in src.get('closedIrisSides',[]):mask[:,256:]=False
  if int(mask.sum())<6 and len(src.get('closedIrisSides',[]))<2:raise ValueError('No credible actual iris ownership for '+src['id']+'; inspect source and set measured irisBoxesPx')
  raw_iris[n]=mask;iris[n]=add(c.emit('mf-iris-mask-'+str(n).zfill(2),mask_image(mask),[p.source(R/src['image'])],'Actual iris-colour ownership DATA inside measured eye ROI; excludes eyebrow ink, sclera and skin','mask',irisBoxesPx=boxes,ownedPixels=int(mask.sum())))if mask.any()else None
 # Skin paint belongs to its own layer. Four genuinely different native base
 # tones must not expose peach nose/eyelid patches on a brown base. Only actual
 # peach skin pixels receive this bounded colour grade; ink/iris/lips stay put.
 for family in ['eyes','nose','mouth']:
  for n,src in enumerate(groups[family][:MINIMUM[family]]):
   native=read_image(src);owner=p.skin_ownership(native,raw_iris[n]if family=='eyes'else None);skinmask=None
   if family=='mouth':owner[:]=False # native mouths contain lips/teeth, not a skin fill
   if family=='eyes':owner[:205]=False # native eyebrow paint must not skin-grade
   if owner.any():skinmask=add(c.emit('mf-skin-mask-'+family+'-'+str(n).zfill(2),mask_image(owner),[p.source(R/src['image'])],'Actual skin-colour ownership DATA; excludes dark ink, red lips, sclera and real iris owner','mask',ownedPixels=int(owner.sum())))
   for style in range(4):
    if owner.any():
     rawbase=read_image(groups['base'][style]);region=(245,254,267,280)if family!='mouth'else(245,287,267,309);rgb=np.asarray(rawbase.crop(region))[:,:,:3];target=np.median(rgb.reshape(-1,3),axis=0).tolist();im,original=p.match_skin(native,owner,target)
     a=add(c.emit('mf-style-'+str(style)+'-'+family+'-'+str(n).zfill(2),im,[p.source(R/src['image']),p.source(R/groups['base'][style]['image']),p.source(R/skinmask['image'])],'Only actual skin-owned pixels matched to measured native base skin; original paint shading and Alpha retained, all non-skin RGBA exact','skin-matched-'+family,sourceStyle=style,skinOwnershipMask=skinmask['image'],skinTargetSampleRectPx=list(region),skinTargetMedianRGB=target,skinSourceMedianRGB=original,skinOutsideOwnershipExactRGBA=bool(np.array_equal(np.asarray(im)[~owner],np.asarray(native)[~owner]))))
    else:a=src
    styled[(style,family,n)]=a
 for style in [0,1]:
  count=12 if style==0 else 16
  for n in range(count):
   src=styled[(style,'eyes',n)];im=read_image(src);mask=raw_iris[n]
   for name in ['brown','blue','green']:
    colored=p.eye_palette(im,mask,name);ar=np.asarray(colored);old=np.asarray(im)
    if not np.array_equal(ar[~mask],old[~mask]):raise ValueError('palette escaped iris ownership')
    eye[(style,n,name)]=add(c.emit('mf-style-'+str(style)+'-eyes-'+str(n).zfill(2)+'-'+name,colored,[p.source(R/src['image']),p.source(R/iris[n]['image'])],'Only owned native iris pixels receive luminance-preserving eye palette; Alpha, skin, sclera, brows and clothes unchanged','eyes-palette',sourceStyle=style,paletteName=name,irisMask=iris[n]['image'],paletteOutsideOwnershipExactRGBA=True))if mask.any()else src
 # Upstream beard-on suppresses separate lips and nose. The source beard
 # binding therefore owns a fixed actual painted nose/mouth + beard ensemble.
 for style in [0,2]:
  for value in range(3):
   parts=[styled[(style,'mouth',0)],styled[(style,'nose',0)],groups['beard'][value]];im=Image.new('RGBA',p.CANVAS)
   for part in parts:im.alpha_composite(read_image(part))
   beard[(style,value)]=add(c.emit('mf-style-'+str(style)+'-bearded-lowerface-'+str(value),im,[p.source(R/a['image'])for a in parts],'Actual fixed nose and mouth plus real beard mother part; independent source beard ensemble replaces suppressed nose/lips variables','beard-ensemble',sourceStyle=style,includedFixedPartIds=[a['id']for a in parts],independentNoseMouthVariablesHidden=True))
 bindings=[]
 for r in SPEC['requirements']:
  q=dict(r);style=r['sourceStyle'];value=r['sourceValue']
  if r['kind']=='Sprite':
   family=p.FAMILIES[r['fieldName']]
   if family=='base':a=chin[(style,0)]if style==1 and r['sourceVarIndex']==4 else dressed[style]
   elif family=='chin':a=chin[(style,value)]
   elif family=='beard':a=beard[(style,value)]
   elif family=='eyes'and style<2:a=eye[(style,value,'brown')]
   elif family in['eyes','nose','mouth']:a=styled[(style,family,value)]
   elif family=='robe':a=robes[value]
   elif family=='hair':a=groups['hair'][([0,1,2,3,4,5,6,7,8]if style==0 else[1,2,4,5,7]if style in[1,3]else[0,1,3,6,8])[value]]
   else:a=groups[family][value]
   ids=[a['id'],inner['id']]if family=='base'and not(style==1 and r['sourceVarIndex']==4)else[a['id']]
   q.update({'assetIds':ids,'family':family,'method':'actual independent mother part; declared shared source-pixel Taoist redesign across compatible style slots','sharedNativePartDeclared':True,'completePresetSubstitution':False})
  elif r['kind']=='Palette':
   count=12 if style==0 else 16;q['paletteRule']={'name':r['paletteName'],'ownership':'only real iris pixels; source Alpha and outside-mask RGBA identical','irisMasks':[iris[n]['image']for n in range(count)if iris[n]],'closedEyeValuesWithoutVisibleIris':[n for n in range(count)if not iris[n]],'eyesByValue':{str(n):eye[(style,n,r['paletteName'])]['id']for n in range(count)},'rgbTargets':{'brown':[98,61,37],'blue':[51,112,150],'green':[65,125,77]}}
  else:q.update({'method':'hide exact source variables; do not create transparent filler Sprites','offStateImageRequired':False})
  bindings.append(q)
 bidx={b['requirementId']:b for b in bindings};samples=[];sample_images={};PRE.mkdir(parents=True,exist_ok=True);(PRE/'assemblies').mkdir(exist_ok=True)
 def compose(name,style,values,covered=None):
  fields=SPEC['styles'][style]['fields'];values={int(k):int(v)for k,v in values.items()};allvalues={f['sourceVarIndex']:values.get(f['sourceVarIndex'],0)for f in fields};order=p.source_order(style,allvalues,SPEC);layers=[];out=Image.new('RGBA',p.CANVAS)
  palette=next((f for f in fields if f['kind']=='Palette'),None)
  pname=['brown','blue','green'][allvalues[palette['sourceVarIndex']]]if palette else None
  for var in order:
   f=fields[var];v=allvalues[var];binding=bidx[f'manager-style-{style}-var-{var}-value-{v}'];ids=binding['assetIds']
   if f['name']=='STR_FACE_EYEBROWS'and pname:ids=[eye[(style,v,pname)]['id']]
   for aid in ids:out.alpha_composite(read_image(by[aid]));layers.append({'sourceVarIndex':var,'sourceValue':v,'assetId':aid,'image':by[aid]['image'],'offsetPx':[0,0],'scale':1})
  digest=hashlib.sha256(out.tobytes()).hexdigest()
  if digest in sample_images:file=sample_images[digest]
  else:
   dest=PRE/'assemblies'/(name+'.png');out.save(dest);file=p.rel(dest);sample_images[digest]=file
   p.savej(str(dest)+'.derivation.json',{'file':file,'sha256':p.sha(dest),'derivedAt':p.now(),'operation':'Actual registered transparent parts, active sourceVarIndex draw order; static art composition only','derivedFrom':[p.source(R/l['image'])for l in layers],'sourceStyle':style,'sourceValues':allvalues,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'unityValidated':False})
  s={'id':name,'sourceStyle':style,'sourceStyleLabel':'default/face'+str(style+1),'selectedSourceValues':allvalues,'activeSourceVarIndices':p.active_indices(style,allvalues,SPEC),'sourceDrawOrder':order,'uiOrder':p.ui_order(style,allvalues,SPEC),'layers':layers,'image':file,'sha256':p.sha(R/file),'coveredRequirementId':covered,'eyePalette':pname,'unityValidated':False};samples.append(s);return s
 for r in ([]if probes_only else SPEC['requirements']):
  if r['kind']!='Sprite':continue
  style=r['sourceStyle'];v={r['sourceVarIndex']:r['sourceValue']};family=p.FAMILIES[r['fieldName']]
  if family in['beard','earring']:v[0]=1
  if family=='glasses':v[1]=1
  compose('source-s'+str(style)+'-v'+str(r['sourceVarIndex'])+'-'+str(r['sourceValue']),style,v,r['requirementId'])
 baseline_values=[{}, {8:2,5:3}, {8:4,4:8,0:1,5:2}, {7:4,4:4}]
 for style in range(4):compose('baseline-style-'+str(style),style,baseline_values[style])
 compose('moustache-on',0,{0:1});compose('glasses-on',0,{1:1});compose('glasses-off',0,{1:0});compose('earring-on',1,{0:1});compose('earring-off',1,{0:0})
 for value,name in enumerate(['brown','blue','green']):compose('eye-'+name,0,{2:value})
 compose('cancel-original',0,{});compose('cancel-edited',0,{9:5,5:7,1:1});compose('cancel-restored',0,{})
 if probes_only:
  for f,count in [('STR_FACE_HAIR',9),('STR_FACE_MOUSTACHE',3),('STR_FACE_JACKET',3),('STR_FACE_COLLAR',4)]:
   field=next(v for v in SPEC['styles'][0]['fields']if v['kind']=='Sprite'and v['name']==f)
   for value in range(count):compose('probe-'+p.FAMILIES[f]+'-'+str(value),0,{field['sourceVarIndex']:value,**({0:1}if f=='STR_FACE_MOUSTACHE'else{})})
 manifest={'schema':'manager-customization-art.v1','createdAt':p.now(),'referenceCommit':SPEC['referenceCommit'],'sourceSpecFile':'docs/MANAGER_FACE_REQUIREMENTS.json','sourceSpecSha256':SPEC['sourceSha256'],'assets':c.assets,'bindings':bindings,'compositionSamples':samples,'previewStates':[],'canvas':list(p.CANVAS),'anchorPx':p.ANCHOR,'sourceSpriteSlots':213,'sourceBindingCount':235,'uniqueSourceSpriteIds':184,'spriteValueCoverage':'preliminary actual fit probes only;213slot bulk export held until visual fit passes'if probes_only else'each of213 sprite slots appears in one actual layered combination sample','drawOrder':'active sourceVarIndex ascending, UI position is separate','artAcceptance':'actual image assembly and advanced UI preview review pending','unityValidated':False,'userAccepted':False,'limitations':['A parameter is an independently replaceable painted part, never a whole preset substitution.','Several source style values explicitly share the same real mother parts; geometric chin and iris palette derivatives are declared.','Source style identities preserved by4 different unfeatured bases.','Offline Python composition is art production only; runtime face parsing/configuration persistence not implemented.']}
 p.savej(OUT/('fit-probes-manifest.json'if probes_only else'manifest.json'),manifest);print(json.dumps({'registeredAssets':len(c.assets),'bindings':len(bindings),'samples':len(samples),'uniqueCompositionPNG':len(sample_images),'status':manifest['artAcceptance']}))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--fit-probes',action='store_true');args=parser.parse_args();main(args.fit_probes)

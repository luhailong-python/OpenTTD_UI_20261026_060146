"""Native service props and explicit shared-module state exports."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageEnhance,ImageFilter
import json,math,sys,numpy as np
import world_pack as wp
import build_world_terrain as terrain
ROOT=wp.ROOT
SETS={
'objects':{'source':'objects-kit','cols':4,'rows':3,'category':'objects','names':['hq-1','hq-2','hq-3','hq-4','hq-5','radio-mast','lighthouse','owned-land','lift-cabin','lift-guide','tunnel-portal','crossing-barrier']},
'waterworks':{'source':'waterworks-kit','cols':3,'rows':3,'category':'waterworks','names':['dock-quay','dock-pier','buoy','ship-depot','canal-banks','lock-low','lock-mid','lock-high','river-rapids']},
'signals':{'source':'signal-kit','cols':4,'rows':3,'category':'signals','names':['light-block','light-entry','light-exit','light-combo','light-path','light-oneway','semaphore-block','semaphore-entry','semaphore-exit','semaphore-combo','semaphore-path','semaphore-oneway']},
'signal-views':{'source':'signal-directions','cols':4,'rows':4,'category':'signals','names':['light-view-'+str(i)for i in range(8)]+['semaphore-view-'+str(i)for i in range(8)]},
'fences-shore':{'source':'fences-shore-kit','cols':3,'rows':3,'category':'infrastructure','names':['fence-wood','fence-stone','fence-hedge','shore-sand','shore-rock','river-grass-bank','field-seedlings','field-ripe-grain','rocks-cluster']}}

def extract(group):
 s=SETS[group];src=ROOT/'source-art/world'/(s['source']+'.png');im=Image.open(src).convert('RGBA');native=json.loads((ROOT/'records/world-production/service-native-components.json').read_text())[s['source']]
 byslot={}
 for comp in native:
  l,t,r,b=comp['bbox'];col=min(s['cols']-1,int(((l+r)/2)/im.width*s['cols']));row=min(s['rows']-1,int(((t+b)/2)/im.height*s['rows']));slot=row*s['cols']+col
  if slot in byslot:raise ValueError('multiple major Alpha components in slot '+str(slot))
  byslot[slot]=comp
 if len(byslot)!=len(s['names']):raise ValueError('native count mismatch '+group)
 items=[]
 for slot,name in enumerate(s['names']):
  comp=byslot[slot];l,t,r,b=comp['bbox'];box=[max(0,l-8),max(0,t-8),min(im.width,r+8),min(im.height,b+8)]
  source_anchor=[(l+r)/2,b-1];canvas=[512,512];anchor=[256,448];max_scale=1
  if group in['signals','signal-views']:
   col=slot%s['cols'];row=slot//s['cols'];canvas=[384,384];anchor=[192,352];max_scale=min(1,240/(b-t))
   if group=='signals':
    source_anchor=[([187,566,947,1328]if row<2 else[164,545,927,1309])[col],b-1]
   else:
    # Native bases are the physical contact; hanging plaques and arms are
    # asymmetrical and must not redefine the pole's anchor.
    polex=[[195,553,931,1319],[199,559,939,1324],[171,551,917,1303],[206,579,953,1320]][row][col]
    source_anchor=[polex,b-1]
  if group=='objects'and name in['lift-cabin','lift-guide']:canvas=[256,384];anchor=[128,352]
  if group=='objects'and name=='owned-land':canvas=[512,384];anchor=[256,320]
  if group=='waterworks'and name=='buoy':source_anchor=[1342,282];canvas=[384,384];anchor=[192,288];max_scale=.85
  if group=='fences-shore'and slot<3:
   source_anchor=[[271,201],[771,192],[1287,194]][slot];canvas=[256,192];anchor=[128,128];max_scale=.324
  item={'id':name,'box':box,'anchorPx':[source_anchor[0]-box[0],source_anchor[1]-box[1]],'canvas':canvas,'targetAnchorPx':anchor,'maximumScale':max_scale,'category':s['category'],'keepMainComponent':True,'componentThreshold':128,'componentFringePx':2,'footprint':{'kind':'native-complete-module','basis':'logical footprint supplied by assembly mapping'},'nativeSlot':slot,'nativeComponentBox':comp['bbox']};items.append(item)
 spec={'id':'services-'+group,'items':items};sp=ROOT/'records/world-production'/(group+'-crops.json');wp.writej(sp,spec)
 class Args:pass
 a=Args();a.source=str(src);a.source_record=None;a.spec=str(sp);a.outdir=str(ROOT/'assets/world/infrastructure'/group);a.strict=False
 wp.slice_props(a);mp=Path(a.outdir)/'manifest.json';pack=json.loads(mp.read_text())
 for asset,it in zip(pack['assets'],items):
  asset['nativeSlot']=it['nativeSlot'];asset['nativeComponentBox']=it['nativeComponentBox'];asset['anchorMeaning']='compound-front contact; not logical tile centre'
  if group in['signals','signal-views']:asset['anchorMeaning']='pole-base physical contact; independent of plaque/arm extent';asset['recommendedWorldDrawScale']=.25
  if group=='waterworks'and asset['id']=='buoy':asset['anchorMeaning']='waterline contact centre'
  if group=='fences-shore'and it['nativeSlot']<3:asset['anchorMeaning']='centre of fence segment on ground line';asset['logicalEdgeVectorSuggested']=[128,-64]
  if group=='signal-views':asset['directionEvidence']='Native atlas provides front/side/back variants with repeated near views; not8 precise native azimuths.'
 pack['acceptance']='extracted; complete-sheet visual and state checks pending';pack['nativeSourceAtlas']=wp.source_record(src);wp.writej(mp,pack)
 terrain.contact(pack['assets'],group+'-contact.jpg',4 if group in['signals','signal-views','objects']else 3,260)
 print(json.dumps({'group':group,'assets':len(pack['assets']),'warnings':sum(q['level']!='OK'for q in pack['qa']),'manifest':str(mp)},ensure_ascii=False))

def get_pack(group):return json.loads((ROOT/'assets/world/infrastructure'/group/'manifest.json').read_text())
def ref(asset):return{'file':asset['image'],'sha256':asset['sha256'],'record':asset['image']+'.derivation.json'}
def emit(out,ident,im,sources,operation,extra,anchor):
 p=ROOT/out/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
 a=wp.base_asset(ident,p.relative_to(ROOT).as_posix(),im,sources[0],operation,extra.pop('category','objects-state'),anchor);a['derivedFrom']=sources;a.update(extra);a['sha256']=wp.sha(p)
 wp.writej(str(p)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'generatedAt':wp.now(),'route':'deterministic-derivative','width':im.width,'height':im.height,'operation':operation,'derivedFrom':sources,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'unverifiedReason':'Native imagegen model/quality undisclosed; derivative transformations add no native painted details.'})
 return a

def objects_states():
 from build_world_houses import paste_anchored
 pack=get_pack('objects');by={a['id']:a for a in pack['assets']};entries=[];animations=[];mapping=[];qa=[]
 out='assets/world/infrastructure/object-states';grass_path=ROOT/'assets/world/terrain/terrain-grass-flat.png';grass=Image.open(grass_path).convert('RGBA');gref={'file':grass_path.relative_to(ROOT).as_posix(),'sha256':wp.sha(grass_path),'record':grass_path.relative_to(ROOT).as_posix()+'.derivation.json'}
 for level in range(1,6):
  src=by['hq-'+str(level)];im=Image.new('RGBA',(768,704));anchor=[384,512];positions=[(0,0),(0,1),(1,0),(1,1)];screens=[[(y-x)*128,(x+y)*64]for x,y in positions];avg=[0,64]
  for x,y in sorted(screens,key=lambda p:p[1]):im.alpha_composite(grass,(anchor[0]+x-128,anchor[1]+y-64-64))
  native=Image.open(ROOT/src['image']).convert('RGBA');bb=wp.alpha_bounds(native);native_centre=[src['anchorPx'][0],src['anchorPx'][1]-(bb[2]-bb[0])*.17];placement=paste_anchored(im,native,native_centre,anchor,488,420)
  a=emit(out,'hq-level-'+str(level)+'-whole',im,[ref(src),gref],'native HQ level painting placed once on a shared2×2 painted site; no enlargement',{'level':level,'category':'objects-state','sourceRequirementIds':['object-headquarters'],'footprintTiles':[2,2],'placement':placement,'status':'produced-needs-state-review','anchorMeaning':'2×2 site centre'},anchor);entries.append(a)
  yy,xx=np.mgrid[0:704,0:768];owner=np.where(xx<320,2,np.where(xx>448,1,np.where(yy<512,0,3)));assembled=Image.new('RGBA',im.size);parts=[]
  for p,(dx,dy)in enumerate(positions):
   piece=im.copy();piece.putalpha(ImageChops.multiply(piece.getchannel('A'),Image.fromarray(np.uint8(owner==p)*255)));assembled.alpha_composite(piece);part_anchor=[anchor[0]+screens[p][0],anchor[1]+screens[p][1]-64]
   b=emit(out,'hq-level-'+str(level)+'-tile-'+str(p),piece,[ref(a)],'complementary Alpha-only source-tile partition of whole HQ art; exactRGBA reassembly; no new painting',{'level':level,'category':'objects-state','tileOffsetXY':[dx,dy],'sourceWholeAssetId':a['id'],'sourceRequirementIds':['object-headquarters'],'status':'produced-needs-state-review','anchorMeaning':'source HQ tile centre inside shared full-site canvas'},part_anchor);entries.append(b);parts.append(b['image'])
  equal=bool(np.array_equal(np.asarray(im),np.asarray(assembled)));qa.append({'id':'hq-'+str(level)+'.four-tile-reassembly','level':'OK'if equal else'FAIL','exactRGBA':equal});mapping.append({'requirementId':'object-headquarters','level':level,'files':[a['image']]+parts,'footprintTiles':[2,2],'renderStrategy':'whole building or4 complementary fragments; never draw both','sourceTilesPerLevel':4,'companyColourLayer':'company-flag-{0..15}'})
 for requirement,asset in [('object-transmitter','radio-mast'),('object-lighthouse','lighthouse'),('object-owned-land','owned-land')]:mapping.append({'requirementId':requirement,'files':[by[asset]['image']],'artIds':[asset],'groundSeparateSuggested':True})
 statue=json.loads((ROOT/'assets/world/houses/families/special/manifest.json').read_text());statue=next(a for a in statue['assets']if a['familyId']=='bronze-sage-statue');mapping.append({'requirementId':'object-statue','files':[statue['image']],'artIds':[statue['id']],'reuse':'same native bronze sage painting as town sculpture; company flag is separate','groundSeparateSuggested':True,'groundArt':'assets/world/terrain/terrain-grass-flat.png','renderRule':'sculpture once at anchor with separate terrain and optional16company flags'})
 # Company colours use a small actual painted cloth flag. Main roofs remain
 # jade; only the replaceable cloth layer changes company identity.
 source=ROOT/'source-art/world/objects-kit.png';raw=Image.open(source).convert('RGBA');flag=raw.crop((628,394,657,465));m=Image.new('L',flag.size);ImageDraw.Draw(m).polygon([(8,7),(26,12),(23,65),(3,70),(5,22)],fill=255);flag.putalpha(ImageChops.multiply(flag.getchannel('A'),m))
 colours=[('DarkBlue','#274E8B'),('PaleGreen','#B3D29C'),('Pink','#E6A9BE'),('Yellow','#E3C954'),('Red','#C65B50'),('LightBlue','#8DCBDE'),('Green','#5E9E68'),('DarkGreen','#2E6350'),('Blue','#4D81B3'),('Cream','#E9DCBA'),('Mauve','#B9A1B9'),('Purple','#866DA0'),('Orange','#D99553'),('Brown','#906B4F'),('Grey','#A9B0A8'),('White','#F4F0DC')]
 flag_ids=[]
 for ci,(name,hexcolour)in enumerate(colours):
  arr=np.asarray(flag).copy();rgb=arr[...,:3].astype(float);target=np.array([int(hexcolour[k:k+2],16)for k in[1,3,5]],float);teal=(rgb[...,1]>rgb[...,0]*1.02)&(rgb[...,2]>rgb[...,0]*.65);lum=.2126*rgb[...,0]+.7152*rgb[...,1]+.0722*rgb[...,2];shade=np.clip(lum/140,.35,1.5);rgb[teal]=np.clip(target[None,:]*shade[teal,None],0,255);arr[...,:3]=np.uint8(rgb);im=Image.new('RGBA',(96,128));im.alpha_composite(Image.fromarray(arr),(27,12));ident='company-flag-'+format(ci,'02d')
  a=emit(out,ident,im,[wp.source_record(source)],'actual painted transmitter cloth flag crop and authored Alpha polygon; selective teal cloth colour-grade, gold/ivory ornament retained; no new painting',{'category':'objects-state','companyColourIndex':ci,'sourceColourName':name,'designColour':hexcolour,'sourceRequirementIds':['object-headquarters','object-owned-land','object-statue'],'status':'produced-needs-state-review','anchorMeaning':'top cloth suspension point; data-driven placement separate'},[48,12]);entries.append(a);flag_ids.append(a['image'])
 mapping.append({'requirementId':'object-headquarters','files':flag_ids,'companyColourNames':[c[0]for c in colours],'companyColourRule':'native16 names from src/gfx_type.h:283; RGB colours are this project art palette, not claimed OpenTTD exact palette values'})
 # Office animation is a real part translation along a fixed native guide.
 # The body stays in its completed static PNG; these are Alpha overlays.
 house=json.loads((ROOT/'assets/world/houses/manifest.json').read_text());cabin=by['lift-cabin'];guide=by['lift-guide'];cabin_im=Image.open(ROOT/cabin['image']).convert('RGBA');guide_im=Image.open(ROOT/guide['image']).convert('RGBA')
 for houseid in[4,5]:
  h=next(m for m in house['coverageMappings']if m['sourceHouseTileId']==houseid);body=next(s for s in h['states']if s['locationVariant']==0 and s['constructionStage']==3);frames=[]
  for fi in range(16):
   t=fi/16;tri=2*t if t<.5 else 2-2*t;im=Image.new('RGBA',(512,512));base=[311,404]
   gp=paste_anchored(im,guide_im,guide['anchorPx'],base,40,90);cp=paste_anchored(im,cabin_im,cabin['anchorPx'],[base[0],398-44*tri],25,34)
   a=emit(out,'office-lift-'+str(houseid)+'-frame-'+format(fi,'02d'),im,[ref(cabin),ref(guide)],'actual native glass lift cabin and guide cropped/downscaled; cabin translated on fixed guide by triangular motion; not video or new native frames',{'category':'objects-animation','animationGroup':'office-lift-'+str(houseid),'frame':fi,'sourceRequirementIds':['animation-house-lift'],'houseSourceID':houseid,'guidePlacement':gp,'cabinPlacement':cp,'status':'produced-needs-animation-review','anchorMeaning':'matches static house logical site centre'},[256,416]);entries.append(a);frames.append(a['image'])
  animations.append({'id':'office-lift-'+str(houseid),'category':'objects','frames':frames,'durationsMs':[140]*16,'loop':True,'fixedAnchorPx':[256,416],'frameSize':[512,512],'method':'native moving cabin + static guide; deterministic2D translation','bodyStaticPNG':body['image'],'sourceRequirementIds':['animation-house-lift']});mapping.append({'requirementId':'animation-house-lift','houseSourceID':houseid,'files':frames,'animationId':'office-lift-'+str(houseid),'bodyStaticPNG':body['image'],'status':'part-motion-loop-produced'})
 manifest={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'batchId':'object-states','assets':entries,'animations':animations,'qa':qa,'coverageMappings':mapping,'acceptance':'produced; visual state/loop review pending','limitations':['HQ fragments are exact screen-space partitions; Unity depth and collision still require verification.','Company colour is a replaceable native cloth-flag layer; roofs remain jade.','Lift overlays demonstrate artwork motion only; floor logic and game update timing are next-stage work.','Shared tunnel/barrier native modules are processed in separate network-state pack.']}
 wp.writej(ROOT/'assets/world/infrastructure/object-states/manifest.json',manifest);terrain.contact([a for a in entries if'whole'in a['id']or a['id'].startswith('company-flag')],'object-states-contact.jpg',4,210)
 print(json.dumps({'objectsStateAssets':len(entries),'officeLoops':len(animations),'HQLevels':5,'HQTiles':20,'companyFlags':16},ensure_ascii=False))

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['extract','objects']);p.add_argument('--group',choices=list(SETS));a=p.parse_args()
 if a.action=='extract'and a.group:extract(a.group)
 elif a.action=='objects':objects_states()

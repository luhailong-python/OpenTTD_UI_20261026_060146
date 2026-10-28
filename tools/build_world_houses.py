"""Native house-family extraction and explicit source-ID/variation composition."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,sys,math,numpy as np
import world_pack as wp
from plan_world_houses import FAMILIES
import build_world_terrain as terrain
ROOT=wp.ROOT
CROPS={
'traditional':[
([0,0,504,329],[280,316]),([505,0,1021,337],[768,328]),([1022,0,1536,336],[1267,324]),
([0,328,493,647],[279,636]),([494,326,1075,671],[800,658]),([1076,305,1536,691],[1288,659]),
([0,643,486,1024],[264,995]),([470,647,1024,1024],[759,1008]),([1025,641,1536,1024],[1294,1005])],
'commerce':[
([0,0,510,346],[282,339]),([511,0,1026,365],[769,355]),([1027,0,1536,365],[1280,353]),
([0,329,551,681],[259,658]),([522,340,1025,681],[769,658]),([1026,357,1536,685],[1264,675]),
([0,648,508,1024],[268,1002]),([492,637,1030,1024],[773,1010]),([993,655,1536,1024],[1283,1011])],
'dense':[
([0,0,534,362],[270,350]),([535,0,1016,375],[770,359]),([1017,0,1536,365],[1281,355]),
([0,348,538,697],[284,682]),([539,346,1014,692],[770,678]),([1015,364,1536,699],[1282,693]),
([0,650,538,1024],[292,1017]),([539,650,1015,1024],[786,1018]),([1016,686,1536,1024],[1285,1018])],
'climates':[
([0,0,540,354],[279,335]),([541,0,998,355],[773,338]),([999,0,1536,344],[1264,340]),
([0,342,541,647],[289,635]),([542,326,998,652],[762,644]),([999,340,1536,651],[1262,628]),
([0,644,539,1024],[286,997]),([540,643,999,1024],[778,1000]),([1000,638,1536,1024],[1269,1002])],
'special':[
([0,0,596,351],[203,344]),([597,0,992,338],[783,326]),([993,0,1536,339],[1263,326]),
([0,334,517,705],[273,670]),([518,331,1027,705],[787,699]),([1028,330,1536,705],[1287,693]),
([0,691,512,1024],[276,1003]),([513,705,987,1024],[757,996]),([988,683,1536,1024],[1257,1018])]
}

def spec_for(group):
 if group in CROPS:cells=CROPS[group]
 else:
  # Initial extraction must be inspected and authored before acceptance.
  # It may be revised when a native atlas does not follow its prompt's grid.
  cells=[]
  for i in range(9):
   x=(i%3)*512;y=round((i//3)*1024/3);b=[x,y,min(x+512,1536),round(((i//3)+1)*1024/3)]
   cells.append((b,[x+256,b[3]-10]))
 items=[]
 for ident,(box,front)in zip(FAMILIES[group],cells):
  item={'id':'house-family-'+ident,'box':box,'anchorPx':[front[0]-box[0],front[1]-box[1]],'canvas':[512,512],'targetAnchorPx':[256,448],'category':'houses','keepMainComponent':True,'componentFringePx':2,'footprint':{'kind':'native-complete-building','anchorMeaning':'front-contact; logical footprint belongs to source parent instance'}}
  if ident=='pavilion-apartments':
   item['alphaEraseRects']=[[1246-box[0],649-box[1],1278-box[0],676-box[1]]]
   item['alphaKeepGoldRects']=[[1190-box[0],305-box[1],1350-box[0],327-box[1]]]
  if ident=='townhall':item['alphaKeepGoldRects']=[[1170-box[0],641-box[1],1340-box[0],663-box[1]]]
  if ident=='city-temple':item['alphaKeepGoldRects']=[[650-box[0],647-box[1],780-box[0],668-box[1]]]
  if ident=='jade-skyscraper':item['alphaKeepGoldRects']=[[240-box[0],650-box[1],350-box[0],689-box[1]]]
  if ident=='cylindrical-tower':item['alphaKeepGoldRects']=[[738-box[0],650-box[1],850-box[0],681-box[1]]]
  if ident=='snow-lodge':
   item['alphaEraseRects']=[[811-box[0],0-box[1],929-box[0],74-box[1]]]
   item['alphaErasePurpose']='Separate baked chimney smoke from static building; future shared smoke FX is a separate layer.'
  items.append(item)
 return {'id':'house-families-'+group,'items':items}

def extract(group):
 src=ROOT/'source-art/world'/('houses-'+group+'.png');spec=spec_for(group);sp=ROOT/'records/world-production'/('houses-'+group+'-crops.json');wp.writej(sp,spec)
 class Args:pass
 a=Args();a.source=str(src);a.spec=str(sp);a.source_record=None;a.outdir=str(ROOT/'assets/world/houses/families'/(group+'-v3'));a.strict=False
 wp.slice_props(a)
 mp=Path(a.outdir)/'manifest.json';pack=json.loads(mp.read_text());
 for item,asset in zip(spec['items'],pack['assets']):
  asset['anchorMeaning']='front-contact of native whole-building site; not logical tile centre'
  # The site's visible isometric base uses roughly1/4 of its painted width
  # between the centre and front tip. This is a recorded import suggestion,
  # later corrected in contact-sheet review if needed.
  bb=asset['alphaTrimBox'];base_half=(bb[2]-bb[0])*.17*asset['scaleApplied']
  asset['suggestedFootprintCentrePx']=[256,448-base_half]
  asset['familyId']=asset['id'].removeprefix('house-family-');asset['status']='produced-needs-footprint-review';asset['nativeFamilyClaim']=True
 pack['anchorConvention']='front-contact of complete native site; per-instance logical centre correction recorded separately'
 wp.writej(mp,pack);terrain.contact(pack['assets'],'houses-'+group+'-contact.jpg',3,280)
 print(json.dumps({'familyGroup':group,'assets':len(pack['assets']),'manifest':str(mp)},ensure_ascii=False))

def family_data():
 out={}
 for mp in (ROOT/'assets/world/houses/families').glob('*/manifest.json'):
  pack=json.loads(mp.read_text())
  for a in pack['assets']:out[a['familyId']]=a
 return out

def site_climate(masks):
 if 'Toyland'in masks:return'toyland'
 if 'SubarcticAboveSnow'in masks and len(masks)==1:return'snow'
 if 'Subtropic'in masks and'Temperate'not in masks and'SubarcticBelowSnow'not in masks:return'tropical'
 return'grass'

def paste_anchored(canvas,source,source_anchor,target_anchor,max_width,max_height):
 bb=wp.alpha_bounds(source)
 if not bb:return None
 piece=source.crop(bb);scale=min(1.,max_width/piece.width,max_height/piece.height)
 size=(max(1,round(piece.width*scale)),max(1,round(piece.height*scale)))
 if size!=piece.size:piece=piece.resize(size,Image.Resampling.LANCZOS)
 at=[round(target_anchor[0]-(source_anchor[0]-bb[0])*scale),round(target_anchor[1]-(source_anchor[1]-bb[1])*scale)]
 canvas.alpha_composite(piece,at)
 return{'sourceAlphaBox':list(bb),'sourceAnchorPx':source_anchor,'targetAnchorPx':target_anchor,'scaleApplied':scale,'offsetPx':at,'exportContentSize':list(piece.size)}

def grade(im,variant):
 factors=[[1,1,1],[.94,1.025,1.015],[1.035,1.,.925],[1.035,.965,.965]][variant]
 a=np.asarray(im).copy();a[...,:3]=np.uint8(np.clip(a[...,:3].astype(float)*np.array(factors),0,255))
 return Image.fromarray(a)

def emit(ident,im,srcs,operation,extra,anchor):
 out=ROOT/'assets/world/houses/states';out.mkdir(parents=True,exist_ok=True);p=out/(ident+'.png');im.save(p)
 a=wp.base_asset(ident,p.relative_to(ROOT).as_posix(),im,srcs[0],operation,'houses-state',anchor);a['derivedFrom']=srcs;a.update(extra);a.update({'sha256':wp.sha(p),'status':'produced-needs-state-review','nativeUpscale':False,'unityValidated':False})
 wp.writej(str(p)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'generatedAt':wp.now(),'route':'deterministic-derivative','width':im.width,'height':im.height,'operation':operation,'derivedFrom':srcs,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'unverifiedReason':'Native source model/quality undisclosed; colour grades, masks and compositions are derivative art.'})
 return a

def states():
 contract=json.loads((ROOT/'docs/HOUSE_PRODUCTION_CONTRACT.json').read_text());families=family_data()
 if len(families)!=45:raise ValueError('need45 finalized native family extracts before house states')
 kit=json.loads((ROOT/'assets/world/infrastructure/construction-ready/manifest.json').read_text());kit={a['id']:a for a in kit['assets']}
 required=['construction-foundation','construction-scaffold-low','construction-front-scaffold']
 for k in required:
  if k not in kit:raise ValueError('missing painted construction module '+k)
 entries=[];images={};cache={};whole_configs={};coverage=[];reassembly=[]
 for row in contract['items']:
  family=row['familyId'];w,h=row['footprintTiles'];climate=site_climate(row['sourceClimateMasks']);key=(family,w,h,climate)
  whole_configs.setdefault(key,[]).append(row)
 parents=[r for r in contract['items']if r['isParent']]
 for row in parents:
  family=row['familyId'];w,h=row['footprintTiles'];climate=site_climate(row['sourceClimateMasks']);key=(family,w,h,climate)
  if key in cache:continue
  fam=families[family];native=Image.open(ROOT/fam['image']).convert('RGBA');family_centre=fam['suggestedFootprintCentrePx']
  single=w==h==1;size=(512,512)if single else(768,704);site_anchor=[256,416]if single else[384,512]
  positions=[(0,0),(0,1),(1,0),(1,1)]if(w,h)==(2,2)else([(0,0),(1,0)]if w==2 else([(0,0),(0,1)]if h==2 else[(0,0)]))
  screens=[[(dy-dx)*128,(dx+dy)*64]for dx,dy in positions];avg=[sum(p[k]for p in screens)/len(screens)for k in[0,1]]
  ground_path=ROOT/'assets/world/terrain'/('terrain-'+climate+'-flat.png');ground=Image.open(ground_path).convert('RGBA')
  base=Image.new('RGBA',size)
  for px,py in sorted(screens,key=lambda p:p[1]):base.alpha_composite(ground,(round(site_anchor[0]+px-avg[0]-128),round(site_anchor[1]+py-avg[1]-64)))
  site_width=256*(w+h)/2;site_height=128*(w+h)/2;max_body_width=site_width-16
  matching=whole_configs[key];ids=[r['sourceRequirementId']for r in matching];cache[key]={}
  source_family={'file':fam['image'],'sha256':fam['sha256'],'record':fam['image']+'.derivation.json'}
  source_ground={'file':ground_path.relative_to(ROOT).as_posix(),'sha256':wp.sha(ground_path),'record':ground_path.relative_to(ROOT).as_posix()+'.derivation.json'}
  for variant in range(4):
   complete_body=Image.new('RGBA',size);placement=paste_anchored(complete_body,grade(native,variant),family_centre,site_anchor,max_body_width,400)
   body_bounds=wp.alpha_bounds(complete_body)
   for stage in range(4):
    frame=base.copy();srcs=[source_family,source_ground];construction_placement=None
    if stage==3:frame.alpha_composite(complete_body)
    else:
     if stage>0:
      body=complete_body.copy();alpha=body.getchannel('A');cut=round(body_bounds[3]-(body_bounds[3]-body_bounds[1])*([0,.36,.72][stage]));m=Image.new('L',size);ImageDraw.Draw(m).rectangle((0,cut,size[0],size[1]),fill=255);body.putalpha(ImageChops.multiply(alpha,m));frame.alpha_composite(body)
     module=required[stage];width_limit=site_width*.86;height_limit=350
     body_height=body_bounds[3]-body_bounds[1]
     if stage==1:height_limit=min(height_limit,body_height*1.05+site_height*.25)
     if stage==2:height_limit=min(height_limit,max(92,body_height*1.25))
     if family in['public-garden','bronze-sage-statue','stone-fountain']:
      if stage==0:module='construction-materials'if family=='public-garden'else'construction-taiji-platform'
      if stage==1:module='construction-materials';width_limit=site_width*.43;height_limit=110
      if stage==2:width_limit=site_width*.62;height_limit=min(height_limit,140)
     k=kit[module];p=Image.open(ROOT/k['image']).convert('RGBA');construction_placement=paste_anchored(frame,p,k['anchorPx'],[site_anchor[0],site_anchor[1]+site_height*.37],width_limit,height_limit)
     srcs.append({'file':k['image'],'sha256':k['sha256'],'record':k['image']+'.derivation.json'})
    stem='house-'+family+'-'+str(w)+'x'+str(h)+'-'+climate+'-v'+str(variant)+'-s'+str(stage)
    operation='native complete Taoist building family + actual painted site tiles; restrained RGB colour grade'+('; shared painted construction module and bottom-up progress mask'if stage<3 else'; completed native building')+'; transparent fixed-canvas placement; every size operation≤1; not4×4nativepaintings'
    a=emit(stem,frame,srcs,operation,{'familyId':family,'locationVariant':variant,'constructionStage':stage,'footprintTiles':[w,h],'climate':climate,'sourceRequirementIds':ids,'anchorMeaning':'logical site centre; individual source-tile fragment anchors are stored separately','bodyPlacement':placement,'constructionPlacement':construction_placement,'sourceWholeBuildingCount':len({r['parentHouseId']for r in matching}),'stateMethod':'shared native construction parts + explicit progress illustration; no native unfinished-building generation'},site_anchor)
    entries.append(a);images[a['id']]=frame;cache[key][variant,stage]={'whole':a,'fragments':[]}
    if not single:
     yy,xx=np.mgrid[0:size[1],0:size[0]]
     if(w,h)==(1,2):owner=np.where(xx<site_anchor[0],0,1)
     elif(w,h)==(2,1):owner=np.where(xx<site_anchor[0],1,0)
     else:owner=np.where(xx<site_anchor[0]-64,2,np.where(xx>site_anchor[0]+64,1,np.where(yy<site_anchor[1],0,3)))
     combined=Image.new('RGBA',size)
     for part,offset in enumerate(positions):
      fragment=frame.copy();mask=Image.fromarray(np.uint8(owner==part)*255);fragment.putalpha(ImageChops.multiply(fragment.getchannel('A'),mask));combined.alpha_composite(fragment)
      anchor=[site_anchor[0]+screens[part][0]-avg[0],site_anchor[1]+screens[part][1]-avg[1]]
      refs=[{'file':a['image'],'sha256':a['sha256'],'record':a['image']+'.derivation.json'}]
      f=emit(stem+'-part-'+str(part),fragment,refs,'complementary Alpha partition of actual whole-site image; exact pixel reassembly; no new painting',{'familyId':family,'locationVariant':variant,'constructionStage':stage,'footprintTiles':[w,h],'tileOffsetXY':list(offset),'sourceWholeAssetId':a['id'],'sourceRequirementIds':[r['sourceRequirementId']for r in matching if r['tileOffsetXY']==list(offset)],'anchorMeaning':'source tile centre measured inside shared whole-site canvas','partition':'screen-space nonoverlap bands; exact reassembly; runtime depth/occlusion unverified'},anchor)
      entries.append(f);images[f['id']]=fragment;cache[key][variant,stage]['fragments'].append(f)
     equal=bool(np.array_equal(np.asarray(frame),np.asarray(combined)))
     if not equal:raise RuntimeError('fragment recomposition mismatch '+stem)
     reassembly.append({'assetId':stem,'parts':len(positions),'exactRGBAReassembly':equal})
 for row in contract['items']:
  family=row['familyId'];w,h=row['footprintTiles'];climate=site_climate(row['sourceClimateMasks']);key=(family,w,h,climate);mapped=[]
  for variant in range(4):
   for stage in range(4):
    frame=cache[key][variant,stage]
    if frame['fragments']:
     asset=next(a for a in frame['fragments']if a['tileOffsetXY']==row['tileOffsetXY'])
    else:asset=frame['whole']
    mapped.append({'locationVariant':variant,'constructionStage':stage,'assetId':asset['id'],'image':asset['image'],'anchorPx':asset['anchorPx'],'wholeAssetId':frame['whole']['id']})
  coverage.append({'sourceRequirementId':row['sourceRequirementId'],'sourceHouseTileId':row['sourceHouseId'],'parentHouseId':row['parentHouseId'],'tileOffsetXY':row['tileOffsetXY'],'familyId':family,'footprintTiles':[w,h],'states':mapped,'coveredStateCount':16,'sourceClimateMasks':row['sourceClimateMasks'],'artStatus':'produced-source-mapped','animationRequired':row['animationRequired'],'animationAssetGroup':'office-lift'if row['animationRequired']else None,'unityValidated':False})
 manifest={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'batchId':'house-states','assets':entries,'animations':[],'qa':[{'id':'house-source-ids','level':'OK','value':len(coverage),'expected':110},{'id':'house-source-combinations','level':'OK','value':sum(len(m['states'])for m in coverage),'expected':1760},{'id':'house-fragment-reassembly','level':'OK','value':len(reassembly),'allExactRGBA':all(t['exactRGBAReassembly']for t in reassembly)}],'coverageMappings':coverage,'sourceHouseTileSpecs':110,'sourceWholeBuildings':94,'nativeFamilyPaintings':45,'sourceDrawCombinationsCovered':1760,'uniqueCompositedConfigs':len(cache),'acceptance':'produced; state/contact-sheet review pending','limitations':['Source110 tileIDs share45native new-style family paintings. Colour grades and construction progress illustrations are explicit derivatives.','Multi-tile fragments exactly reassemble the whole image, but their screen-space partition does not prove3D depth sorting.','House004/005 lift animation uses a separate object/FX layer; static4×4matrix does not itself satisfy that animation.','Source climate masks and gameplay availability remain unchanged data; local snow on a painted roof is artistic styling, not dynamic snowline implementation.','Unity import/rendering/collision and real gameplay timing remain unverified.']}
 wp.writej(ROOT/'assets/world/houses/manifest.json',manifest)
 wp.writej(ROOT/'records/world-production/houses-state-validation.json',{'checkedAt':wp.now(),'sourceIDs':110,'mappedCombinations':1760,'formalStatePNGs':len(entries),'nativeFamilies':45,'sourceWholeBuildings':94,'uniqueCompositedConfigs':len(cache),'exactReassemblyChecks':reassembly,'failures':0,'scope':'matrix coverage and deterministic exact reassembly; visual review/Unity separate'})
 # One4-stage row per actual source family; all family-specific shapes are visible.
 examples=[];seen=set()
 for a in entries:
  if a.get('locationVariant')==0 and'-part-'not in a['id'] and(a['familyId'],a['constructionStage'])not in seen:
   examples.append(a);seen.add((a['familyId'],a['constructionStage']))
 examples.sort(key=lambda a:(a['familyId'],a['constructionStage']))
 for start in range(0,len(examples),20):terrain.contact(examples[start:start+20],'houses-states-'+str(start//20+1).zfill(2)+'.jpg',4,220)
 print(json.dumps({'formalStatePNGs':len(entries),'sourceIDs':110,'mappedCombinations':1760,'uniqueConfigs':len(cache),'reassemblyChecks':len(reassembly),'contactSheets':math.ceil(len(examples)/20)},ensure_ascii=False))

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['extract','states']);p.add_argument('--group',choices=list(FAMILIES));a=p.parse_args()
 if a.action=='states':states()
 elif a.group:extract(a.group)
 else:p.error('--group is required for extraction')

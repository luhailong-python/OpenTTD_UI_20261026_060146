"""Map all 74 source airport tiles and assemble original full-size airport footprints."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import re,json,hashlib,math
from build_airport_modules import R,OUT,readj,savej,sha,saveasset
def build():
 m=readj(OUT/'manifest.json');assets=[x for x in m['assets']if x['category']not in ['airport-tile','airport-animation']and x['id']not in ['airport-ground-grass','airport-ground-half-east','airport-ground-half-west']];by={x['id']:x for x in assets}
 text=(R/'reference/OpenTTD/src/table/airporttile_ids.h').read_text();names=re.findall(r'\bAPT_[A-Z0-9_]+',re.search(r'enum AirportTiles[^\{]*\{(.*?)\};',text,re.S).group(1));assert len(names)==74
 drawtext=(R/'reference/OpenTTD/src/table/station_land.h').read_text();block=re.search(r'_station_display_datas_airport\[\] = \{(.*?)\n\};',drawtext,re.S).group(1);drawrows=[s.strip()for s in block.splitlines()if 'TILE_SPRITE_'in s];assert len(drawrows)==74
 gp=R/'assets/world/terrain/terrain-grass-flat.png';grass=Image.open(gp).convert('RGBA')
 g=saveasset('airport-ground-grass',grass,{'file':gp.relative_to(R).as_posix(),'sha256':sha(gp),'record':gp.relative_to(R).as_posix()+'.derivation.json'},'direct shared grass tile reference/export, no new detail',anchor=[128,64],category='airport-ground');assets.append(g);by[g['id']]=g
 for side in ['east','west']:
  im=Image.open(R/by['airport-ground-apron']['image']).convert('RGBA');mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.polygon([(128,0),(256,64),(128,128)]if side=='east'else[(128,0),(128,128),(0,64)],fill=255);im.paste(grass,(0,0),ImageChops.multiply(mask,grass.getchannel('A')))
  e=saveasset('airport-ground-half-'+side,im,[{'file':gp.relative_to(R).as_posix(),'sha256':sha(gp),'record':gp.relative_to(R).as_posix()+'.derivation.json'},{'file':by['airport-ground-apron']['image'],'sha256':by['airport-ground-apron']['sha256'],'record':by['airport-ground-apron']['image']+'.derivation.json'}],'canonical diamond half-mask composition of actual shared grass and painted concrete; no new paint',anchor=[128,64],category='airport-ground');assets.append(e);by[e['id']]=e
 layoutsraw=(R/'reference/OpenTTD/src/table/airport_defaults.h').read_text();parsedlayouts={}
 for match in re.finditer(r'_tile_table_(\w+)_0 = \{(.*?)\n\};',layoutsraw,re.S):
  ap=match.group(1);tiles=[{'x':int(x),'y':int(y),'sourceTileEnum':name,'sourceTileId':names.index(name)}for x,y,name in re.findall(r'\{\{(\d+),\s*(\d+)\},\s*(APT_\w+)\}',match.group(2))];parsedlayouts[ap]=tiles
 def choose(n,row):
  ground='apron';prop=None;fences=[]
  if 'RUNWAY'in n:
   ground=('threshold-x-reverse'if 'FAR_END'in n else'threshold-x')if('END'in n)else('runway-cross'if n in['APT_RUNWAY_1','APT_RUNWAY_3','APT_RUNWAY_5']else'runway-x')
  elif n in['APT_EMPTY','APT_EMPTY_FENCE_NE']or'GRASS'in n:ground='grass'
  elif n=='APT_APRON_HALF_EAST':ground='half-west'
  elif n=='APT_APRON_HALF_WEST':ground='half-east'
  elif n in['APT_APRON_W','APT_APRON_E','APT_APRON_VER_CROSSING_N']:ground='taxi-mask-10'
  elif n in['APT_APRON_S','APT_ARPON_N','APT_APRON_HOR','APT_APRON_N_FENCE_SW']:ground='taxi-mask-05'
  elif n=='APT_APRON_VER_CROSSING_S':ground='taxi-mask-13'
  elif n=='APT_APRON_HOR_CROSSING_W':ground='taxi-mask-11'
  elif n=='APT_APRON_HOR_CROSSING_E':ground='taxi-mask-14'
  elif 'STAND'in n:ground='taxi-mask-08'
  if 'HELIPAD'in n:ground='helipad'
  if n=='APT_HELIPORT':ground='grass';prop='raised-helipad'
  elif 'DEPOT'in n:prop='hangar'
  elif 'RADAR'in n:prop='radar'
  elif 'FLAG'in n:prop='windsock'
  elif 'RADIO_TOWER'in n:prop='radio-mast'
  elif 'TOWER'in n:prop='control-tower'
  elif 'LOW_BUILDING'in n or'SMALL_BUILDING'in n:prop='administration'
  elif 'BUILDING'in n or n=='APT_ROUND_TERMINAL':prop='terminal'
  elif 'PIER'in n or n=='APT_STAND_1':prop='jetbridge'
  if 'FENCE_'in n:fences+=[token for token in n.split('FENCE_',1)[1].split('_')if token in ['NE','NW','SE','SW']]
  for edge in ['ne','nw','se','sw']:
   if '_fence_'+edge in row:fences.append(edge.upper())
  if n=='APT_LOW_BUILDING_FENCE_N':fences+=['NE','NW']
  if n=='APT_HELIPAD_1':fences.append('SW')
  return ground,prop,sorted(set(fences))
 tileentries=[];coverage=[]
 for i,n in enumerate(names):
  ground,prop,fences=choose(n,drawrows[i]);ge=by['airport-ground-'+ground];im=Image.new('RGBA',(512,512));im.alpha_composite(Image.open(R/ge['image']).convert('RGBA'),(128,320));layers=[{'artId':ge['id'],'offsetPx':[128,320],'layer':'ground'}]
  for edge in fences:
   if edge in ['NE','NW']:
    fe=by['airport-fence-'+edge.lower()];im.alpha_composite(Image.open(R/fe['image']).convert('RGBA'));layers.append({'artId':fe['id'],'offsetPx':[0,0],'layer':'rear-fence'})
  if prop:
   pe=by['airport-'+prop];im.alpha_composite(Image.open(R/pe['image']).convert('RGBA'));layers.append({'artId':pe['id'],'offsetPx':[0,0],'layer':'building'})
  for edge in fences:
   if edge in ['SE','SW']:
    fe=by['airport-fence-'+edge.lower()];im.alpha_composite(Image.open(R/fe['image']).convert('RGBA'));layers.append({'artId':fe['id'],'offsetPx':[0,0],'layer':'front-fence'})
  ident='airport-tile-'+str(i).zfill(2)+'-'+n[4:].lower().replace('_','-');sources=[{'file':by[x['artId']]['image'],'sha256':by[x['artId']]['sha256'],'record':by[x['artId']]['image']+'.derivation.json'}for x in layers]
  animation='airport-radar-scan'if prop=='radar'else('airport-windsock-flutter'if prop=='windsock'else None)
  e=saveasset(ident,im,sources,'layered static airport tile composite from actual painted canonical ground, building and symmetric fence modules; original enum identity and source layout preserved; no new model painting',{'sourceTileId':i,'sourceTileEnum':n,'sourceDrawSpec':drawrows[i],'layers':layers,'animationId':animation,'logicalFootprint':[1,1],'logicalGroundCentrePx':[256,384],'sourceRequirementIds':[ident]},category='airport-tile');assets.append(e);tileentries.append(e)
  coverage.append({'requirementId':ident,'artIds':[ident],'files':[e['image']],'sourceTileId':i,'sourceTileEnum':n,'moduleLayers':layers,'animationId':animation,'status':'art-produced-mapped','source':'src/table/airporttile_ids.h; src/table/station_land.h:693-770'})
 by.update({e['id']:e for e in tileentries})
 ref=readj(R/'docs/WORLD_ASSET_COVERAGE.json');specs=[x for x in ref['items']if x['entryKind']=='source-airport-spec'];sourceorder=['country','city','heliport','metropolitan','international','commuter','helidepot','intercontinental','helistation','oilrig']
 full=[]
 PRE=R/'previews/world/airports';PRE.mkdir(parents=True,exist_ok=True)
 for ap in sourceorder:
  spec=next(x for x in specs if x['id']=='airport-'+ap);size=spec['neededVariants']['footprintTiles'];tiles=parsedlayouts.get(ap,[]);obj={'id':'airport-'+ap,'name':spec['name'],'sourceAirportTypeId':sourceorder.index(ap),'footprintTiles':size,'minYear':spec['neededVariants'].get('minYear'),'buildable':ap!='oilrig','sourceDirection':'N (only default layout in source)','tiles':tiles,'source':'src/table/airport_defaults.h','sourceFileSha256':sha(R/'reference/OpenTTD/src/table/airport_defaults.h'),'sourceTileCount':len(tiles),'artGenerationClaim':False}
  if ap=='oilrig':
   body=R/'assets/world/industries/oil-rig.png';im=Image.new('RGBA',(768,768));waterpath=R/'assets/world/terrain/water-sea-frame-00.png';water=Image.open(waterpath).convert('RGBA')
   for y in range(3):
    for x in range(3):im.alpha_composite(water,(256+(y-x)*128,384+(x+y)*64))
   im.alpha_composite(Image.open(body).convert('RGBA'),(128,96));obj['sharedIndustry']='industry-05-oil-rig';obj['airportLogicalFootprintTiles']=[1,1];obj['previewContext']='one airport berth shares actual oil industry parent platform;3x3 water shown as surrounding context, not airport footprint';sources=[{'file':body.relative_to(R).as_posix(),'sha256':sha(body),'record':body.relative_to(R).as_posix()+'.derivation.json'},{'file':waterpath.relative_to(R).as_posix(),'sha256':sha(waterpath),'record':waterpath.relative_to(R).as_posix()+'.derivation.json'}];ids=['industry-05-oil-rig']
  else:
   # Keep complete source footprint at formal tile scale. Preview downscale is separate below.
   w=(size[0]+size[1])*128+256;h=(size[0]+size[1])*64+448;im=Image.new('RGBA',(w,h));origin=[size[0]*128,320];sources=[];ids=[]
   for t in sorted(tiles,key=lambda t:t['x']+t['y']):
    n=t['sourceTileEnum'];ident='airport-tile-'+str(t['sourceTileId']).zfill(2)+'-'+n[4:].lower().replace('_','-');e=by[ident];cx=origin[0]+(t['y']-t['x'])*128;cy=origin[1]+(t['x']+t['y'])*64
    im.alpha_composite(Image.open(R/e['image']).convert('RGBA'),(cx-256,cy-384));t['artId']=ident;t['groundCentreInPreviewPx']=[cx,cy];ids.append(ident);sources.append({'file':e['image'],'sha256':e['sha256'],'record':e['image']+'.derivation.json'})
   obj['formalTileScalePx']=[256,128];obj['previewOriginGroundCentrePx']=origin
  p=PRE/(ap+'-layout.png');im.save(p);rec={'file':p.relative_to(R).as_posix(),'sha256':sha(p),'width':im.width,'height':im.height,'operation':'source layout coordinates remapped to 256x128 isometric tile centres; layer sorting x+y; full native formal-tile scale composition, no new generated scene detail','derivedFrom':sources,'nativeModelGeneration':False,'unityValidated':False};savej(Path(str(p)+'.derivation.json'),rec);obj['preview']=rec;obj['artIds']=sorted(set(ids));full.append(obj);coverage.append({'requirementId':obj['id'],'artIds':obj['artIds'],'files':[p.relative_to(R).as_posix()],'status':'source-layout-art-assembled','sourceFootprintTiles':size,'buildable':obj['buildable']})
 m.update({'assets':assets,'coverageMappings':coverage,'sourceLayouts':full,'sourceAirportTypeCount':10,'sourceAirportTileCount':74,'counts':{'formalModules':len(assets)-74,'formalTileComposites':74,'sourceAirports':10,'sourceLayoutPlacements':sum(len(a['tiles'])for a in full)},'limitations':['Shared jade terminal/administration/transceiver modules are functional visual redesigns, not pixel copies of every original terminal fragment or circular geometry.','Airport whole-layout PNGs are actual full-footprint art assembly previews; they are not icons or Unity/runtime scene proof.','APRON source taxi sprite names have an explicit equivalent centre graph; exact traffic pathfinding/collision remains source data and next-phase work.']})
 savej(OUT/'manifest.json',m)
 # Contact review without shrinking exported full layouts themselves.
 font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16)
 for page in range(4):
  entries=tileentries[page*20:page*20+20];panel=Image.new('RGB',(1280,1560),'#dfdacb');d=ImageDraw.Draw(panel)
  for k,e in enumerate(entries):
   art=Image.open(R/e['image']).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(256,256),'#dfdacb'if k%2==0 else'#244139');bg.alpha_composite(art);x=(k%5)*256;y=(k//5)*390;panel.paste(bg.convert('RGB'),(x,y));d.text((x+4,y+265),str(e['sourceTileId'])+' '+e['sourceTileEnum'][4:],font=font,fill='#325746')
  panel.save(PRE/('tiles-'+str(page+1)+'.jpg'),quality=94)
 panel=Image.new('RGB',(1800,2600),'#dfdacb');d=ImageDraw.Draw(panel)
 for i,a in enumerate(full):
  art=Image.open(R/a['preview']['file']).convert('RGBA');art.thumbnail((860,470),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(900,520),'#dfdacb'if i%2==0 else'#244139');bg.alpha_composite(art,((900-art.width)//2,10));x=(i%2)*900;y=(i//2)*520;panel.paste(bg.convert('RGB'),(x,y));d.text((x+20,y+490),a['name']+' '+a['id']+' '+str(a['footprintTiles'])+' 地块',font=font,fill='#325746'if i%2==0 else'#f2e7ca')
 panel.save(PRE/'all-layouts.jpg',quality=95)
 print(json.dumps({'tileSprites':74,'airportLayouts':len(full),'sourceLayoutCells':sum(len(a['tiles'])for a in full),'assets':len(assets)}))
if __name__=='__main__':build()


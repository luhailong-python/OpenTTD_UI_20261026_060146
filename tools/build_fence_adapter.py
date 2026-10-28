"""Source farm/rail fence adapters; all visible pixels reuse current painted fences."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,re,math,numpy as np
import world_pack as wp
R=wp.ROOT;OUT='assets/world/overlays/fence-adapter';PRE=R/'previews/fence-adapter';EDGES={'nw':('w','n'),'ne':('n','e'),'sw':('w','s'),'se':('s','e')};DY=[64,-64,96,-96,32,-32];CANVAS=(320,320);ANCHOR=[160,192]
FAMILIES=[('bushes','fence-hedge'),('bushes-gate','fence-hedge'),('timber','fence-wood'),('yellow-bloom','fence-hedge'),('red-bloom','fence-hedge'),('stone','fence-stone')]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(f):return{'file':f,'sha256':wp.sha(R/f),'record':f+'.derivation.json'}
def source_specs():
 s=(R/'reference/OpenTTD/src/table/clear_land.h').read_text(encoding='utf8');sp=(R/'reference/OpenTTD/src/table/sprites.h').read_text(encoding='utf8');b=re.search(r'_clear_land_fence_sprites\[7\]\s*=\s*\{(.*?)\};',s,re.S)[1];symbols=re.findall(r'SPR_HEDGE_\w+',b);families=[{'fenceValue':i+1,'symbol':n,'spriteBase':int(re.search(r'\b'+n+r'\s*=\s*(\d+)',sp)[1])}for i,n in enumerate(symbols)];mods={}
 for edge in EDGES:mods[edge]=list(map(int,re.findall(r'\b\d+\b',re.search(r'_fence_mod_by_tileh_'+edge+r'\s*=\s*\{(.*?)\};',s,re.S)[1])))
 rail=(R/'reference/OpenTTD/src/rail_cmd.cpp').read_text(encoding='utf8');body=rail.split('static const FenceOffset _fence_offsets[] = {',1)[1].split('};',1)[0];positions=[]
 for corner,x,y,w,h,name in re.findall(r'\{Corner::(\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\},\s*//\s*(\w+)',body):positions.append({'index':len(positions),'role':len(positions)%8,'heightRef':corner.lower(),'originWorld':[int(x),int(y)],'extentWorld':[int(w),int(h),4],'sourceName':name})
 return families,mods,positions
def baseline(raw):
 a=np.array(raw.getchannel('A'));ys,xs=np.where(a>64);l,r=int(xs.min()+6),int(xs.max()-6);points=[]
 for x in range(l,r+1):
  yy=np.where(a[:,x]>64)[0]
  if len(yy):points.append((x,int(yy.max())))
 x=np.array([p[0]for p in points]);y=np.array([p[1]for p in points]);m,b=np.polyfit(x,y,1);return{'x0':l,'x1':r,'slope':float(m),'intercept':float(b),'fitRMSE':float(np.sqrt(np.mean((y-m*x-b)**2))),'method':'robust interior nativeAlpha ground-contact envelope,not claimed exact model perspective'}
def project(raw,cal,p0,p1,size=CANVAS):
 x0,x1=cal['x0'],cal['x1'];m,b=cal['slope'],cal['intercept'];scale=min(1,128/(x1-x0));source=[(x0,m*x0+b),(x1,m*x1+b),(x0,m*x0+b-64)];dest=[p0,p1,(p0[0],p0[1]-64*scale)]
 return raw.transform(size,Image.Transform.AFFINE,wp.affine_coeff(dest,source),Image.Resampling.BICUBIC)
def materials():
 files={p:'assets/world/infrastructure/fences-shore/'+p+'.png'for p in ['fence-wood','fence-hedge','fence-stone']};raws={p:Image.open(R/f).convert('RGBA')for p,f in files.items()};out=[]
 for family,parent in FAMILIES:
  raw=raws[parent].copy();deps=[ref(files[parent])];operation='existing native-painted '+parent+';'
  if family=='bushes-gate':
   ar=np.array(raw);cal=baseline(raw);mid=round((cal['x0']+cal['x1'])/2);ar[:,mid-16:mid+16]=0;raw=Image.fromarray(ar);wood=raws['fence-wood'].copy();wc=baseline(wood);delta=round((cal['slope']*mid+cal['intercept'])-(wc['slope']*mid+wc['intercept']));native=Image.new('RGBA',raw.size);native.alpha_composite(wood,(0,delta));mask=Image.new('L',raw.size);ImageDraw.Draw(mask).rectangle((mid-16,0,mid+15,raw.height-1),fill=255);native.putalpha(ImageChops.multiply(native.getchannel('A'),mask));raw.alpha_composite(native);deps.append(ref(files['fence-wood']));operation+='native hedge opening/wooden crossbar insert;Alpha ownership cut only,no new gate paint;'
  if family in ['yellow-bloom','red-bloom']:
   ar=np.array(raw);rgb=ar[...,:3].astype(float);r,g,b=np.moveaxis(rgb,-1,0);petals=((r>145)&(g>125)&(b<160)&(r>g*.91))|((r>185)&(g>185)&(b>165));petals&=ar[...,3]>64;target=np.array([235,192,57]if family=='yellow-bloom'else[194,65,55]);shade=np.clip(rgb.mean(-1)/175,.55,1.28);ar[petals,:3]=np.uint8(np.clip(target[None,:]*shade[petals,None],0,255));raw=Image.fromarray(ar);operation+='selective hue-grade actual native flower petals only;no code flowers;'
  out.append((family,raw,baseline(raw),deps,operation))
 return out
def emit(id,im,srcs,op,extra):
 f=OUT+'/'+id+'.png';ar=np.array(im);ar[ar[...,3]==0,:3]=0;Image.fromarray(ar).save(R/f);a={'id':id,'image':f,'width':320,'height':320,'format':'PNG','mode':'RGBA','sha256':wp.sha(R/f),'anchorPx':ANCHOR,'pivotUnity':[.5,.4],'border':[0,0,0,0],'category':'source-fence-adapter','derivedFrom':srcs,'operation':op+'vertical-post preserving affine ground-baseline projection;no code-drawn fence/paint,no new native viewpoint','nativeModelGeneration':False,'nativeUpscale':False,'actualModel':None,'actualQuality':None,'status':'produced-needs-actual-visual-review','userArtAcceptance':'pending','unityValidated':False,**extra};wp.writej(Path(str(R/f)+'.derivation.json'),a);return a
def corners(code):return{k:[x+128,y+160-wp.corner_heights(code)[k]*32]for k,(x,y)in wp.FLAT_POINTS.items()}
def main():
 (R/OUT).mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);families,mods,positions=source_specs();mats=materials();assets=[];farm=[];rail=[]
 for i,(family,raw,cal,srcs,op)in enumerate(mats):
  for off,dy in enumerate(DY):
   pts=[[96,192-dy/2],[224,192+dy/2]];a=emit(f'farm-{family}-offset-{off}',project(raw,cal,*pts),srcs,op,{'sourceRequirementIds':['terrain-fence'],'sourceFamily':families[i],'sourceSpriteOffset':off,'sourceSpriteId':families[i]['spriteBase']+off,'sourceBaselineCalibration':cal,'localEndpointPx':pts,'localEndpointHeightDifferencePx':dy});assets.append(a)
  for code,_ in wp.SLOPES:
   cc=corners(code);hh=wp.corner_heights(code)
   for edge,(c0,c1)in EDGES.items():
    off=mods[edge][code];p0,p1=cc[c0],cc[c1];a=next(a for a in assets if a['id']==f'farm-{family}-offset-{off}');delta=[round((p0[j]+p1[j])/2-ANCHOR[j])for j in range(2)];farm.append({'family':family,'fenceValue':i+1,'sourceSymbol':families[i]['symbol'],'sourceSpriteId':families[i]['spriteBase']+off,'sourceSpriteOffset':off,'slopeCode':code,'edge':edge,'endpointCorners':[c0,c1],'endpointHeights':{c0:hh[c0],c1:hh[c1]},'endpointPx':[p0,p1],'sourceReferenceCorner':{'nw':'w','ne':'e','sw':'s','se':'s'}[edge],'sourceReferencePixelZ':hh[{'nw':'w','ne':'e','sw':'s','se':'s'}[edge]]*8,'file':a['image'],'sha256':a['sha256'],'pasteXY':delta,'tileCanvas':[512,384],'tileAnchorPx':[256,224],'sourceDrawBoundsOffsetXY':{'nw':[0,-16],'ne':[-16,0],'sw':[0,0],'se':[0,0]}[edge]})
 # Default rail fences reuse timber paint:8source roles;the16positions retain source modulo8 sharing.
 family,raw,cal,srcs,op=mats[2];railDy={0:-64,1:64,4:-32,5:32,6:-96,7:96}
 for role in range(8):
  if role==2:
   logical=[[160,128],[160,256]];physical=[[152,128],[168,256]];im=project(raw,cal,*physical);extra={'edgeOnRenderThicknessPx':16,'logicalEndpointPx':logical,'renderBaselineEndpointPx':physical,'projectionDisclosure':'edge-on logical vertical separator;finite16pxnative texture thickness within source1x1world projected bounding width avoids degenerate transform;posts stay upright;shared painting,not new perspective'}
  elif role==3:
   logical=[[32,192],[288,192]];im=project(raw,cal,[32,192],[160,192]);im.alpha_composite(project(raw,cal,[160,192],[288,192]));extra={'logicalEndpointPx':logical,'renderBaselineEndpointPx':logical,'nativeSegmentRepeatCount':2,'projectionDisclosure':'two128pxnative fence repeats across horizontal tile diagonal;no native enlargement'}
  else:
   dy=railDy[role];logical=[[96,192-dy/2],[224,192+dy/2]];im=project(raw,cal,*logical);extra={'logicalEndpointPx':logical,'renderBaselineEndpointPx':logical}
  a=emit(f'rail-fence-role-{role}',im,srcs,op,{'sourceRequirementIds':['rail-rail','rail-electric','rail-monorail','rail-maglev'],'sourceSpriteId':1301+role,'sourceRole':role,'sourceBaselineCalibration':cal,**extra});assets.append(a)
 for p in positions:
  role=p['role'];a=next(a for a in assets if a['id']==f'rail-fence-role-{role}');x,y=p['originWorld'];code={4:3,5:6,6:12,7:9}.get(role,0)
  if role in [2,3]:pts=[[256,160],[256,288]]if role==2 else[[128,224],[384,224]]
  else:
   ww=[(x,y),(x+16,y)]if role in[0,4,6]else[(x,y),(x,y+16)];pts=[]
   for xx,yy in ww:
    z=0 if not code else xx/2 if code==3 else yy/2 if code==6 else(16-xx)/2 if code==12 else(16-yy)/2;pts.append([256+(yy-xx)*8,160+(xx+yy)*4-z*4])
   pts.sort(key=lambda a:a[0])
  delta=[round((pts[0][j]+pts[1][j])/2-ANCHOR[j])for j in range(2)];rail.append({**p,'sourceSpriteId':1301+role,'file':a['image'],'sha256':a['sha256'],'sourceCanonicalSlope':code,'baselineEndpointPxAtBaseZ':pts,'pasteXYAtBaseZ':delta,'heightRule':'if heightRef is valid add GetSlopePixelZInCorner(RemoveHalftileSlope(tileh),heightRef) to sourceZ,therefore subtract4px per sourcePixelZ from pasteY;otherwise source baseZ only','nativeRoleShare':'source fallback rfo%8;no duplicate native paintings'})
 selectors=[]
 for code,_ in wp.SLOPES:
  nw=(4 if code&1 else 6)if code&9 else 0;se=(12 if code&2 else 14)if code&6 else 8;ne=(5 if code&4 else 7)if code&12 else 1;sw=(13 if code&2 else 15)if code&3 else 9
  types={'FenceNW':[nw],'FenceSE':[se],'FenceSENW':[nw,se],'FenceNE':[ne],'FenceSW':[sw],'FenceNESW':[ne,sw],'FenceVert1':[2],'FenceVert2':[10],'FenceHoriz1':[3],'FenceHoriz2':[11]}
  for ground,roles in types.items():selectors.append({'slopeCode':code,'railGroundType':ground,'sourcePositionIndices':roles,'validity':'exact source selector;caller must retain source RailGroundType/foundation legal combinations,not all combinations buildable'})
 half=[{'trackCorner':c,'sourcePositionIndex':i,'sourceRole':i%8,'heightRef':c.lower(),'sourceRule':'halftileCorner if IsHalftileSlope;otherwise opposite highest corner ofComplementSlope;only upper part is fenced','file':next(r['file']for r in rail if r['index']==i)}for c,i in [('W',2),('N',3),('E',10),('S',11)]]
 manifest={'schema':'farm-and-rail-fence-source-adapter.v1','createdAt':wp.now(),'assets':assets,'animations':[],'farmSourceFamilies':families,'farmSlopeOffsetTables':mods,'farmBindings':farm,'noImageSourceValues':[{'fenceValue':0,'noDraw':True,'reason':'source no fence'},{'fenceValue':7,'sourceSpriteBase':0,'noDraw':True,'reason':'source array declared7 but6explicit values;implicit0reserved,not seventh painted family'}],'railSourcePositions':rail,'railGroundSelectors':selectors,'railHalfTileWaterBindings':half,'sourceFiles':[{'file':'reference/OpenTTD/src/'+f,'sha256':wp.sha(R/'reference/OpenTTD/src'/f)}for f in ['table/clear_land.h','clear_cmd.cpp','table/sprites.h','rail_cmd.cpp','landscape.cpp','slope_type.h']],'coverageMappings':[{'requirementId':'terrain-fence','files':[a['image']for a in assets if a['id'].startswith('farm-')],'sourceValidFamilies':6,'sourceSpriteOffsets':list(range(6)),'slopeCodes':[c for c,_ in wp.SLOPES],'edges':list(EDGES),'explicitBindings':456,'noImageFenceValues':[0,7],'completeVariantCoverage':True}]+[{'requirementId':'rail-'+k,'files':[a['image']for a in assets if a['id'].startswith('rail-')],'sourceRoles':8,'sourcePositions':16,'halfTileWaterCorners':['W','N','E','S'],'completeVariantCoverage':True}for k in ['rail','electric','monorail','maglev']],'nativeMaterialInputs':3,'nativeMastersAdded':0,'formalPNGs':len(assets),'userArtAcceptance':'pending','unityValidated':False,'status':'produced-needs-actual-visual-review'};manifest['railNoFenceGroundTypes']=[{'railGroundType':n,'noDraw':True,'reason':'source DrawTrackDetails default branch'}for n in ['Barren','Grass','SnowOrDesert','HalfTileSnow']];manifest['railNoFullDetail']={'noDraw':True,'source':'rail_cmd.cpp2484'};manifest['importSuggestion']={'spriteMode':'Single','meshType':'FullRect','filterMode':'Bilinear','wrapMode':'Clamp','mipMaps':False,'atlasPaddingMin':4};wp.writej(R/OUT/'manifest.json',manifest)
 font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),12);pages=[]
 def contact(items,name,draw,cols=4,cell=(320,280)):
  out=Image.new('RGB',(cols*cell[0],math.ceil(len(items)/cols)*cell[1]+48),'#21483a');d=ImageDraw.Draw(out);d.text((12,8),name+' · 现有原生栏段投影／实际地形拼装',font=font,fill='#f2e6c9');deps=[]
  for k,item in enumerate(items):
   im,label,refs=draw(item);im.thumbnail((cell[0]-6,cell[1]-34),Image.Resampling.LANCZOS);x=k%cols*cell[0];y=k//cols*cell[1]+32;out.paste(im,(x+(cell[0]-im.width)//2,y),im);d.text((x+6,y+cell[1]-31),label,font=font,fill='#f2e6c9');deps+=refs
  f='previews/fence-adapter/'+name+'.jpg';out.save(R/f,quality=96);wp.writej(Path(str(R/f)+'.derivation.json'),{'file':f,'sha256':wp.sha(R/f),'operation':'actual current native fence PNG plus source-correct geometric placement on actual ground/rail;aspectdownsample contact only','derivedFrom':deps,'nativeModelGeneration':False,'unityValidated':False});pages.append(f)
 def farmdraw(case):
  code=case['slopeCode'];name=dict(wp.SLOPES)[code];gf=f'assets/world/terrain/field-stages/field-stage-3-slope-{name}.png'
  if not(R/gf).is_file():gf=f'assets/world/terrain/terrain-grass-slope-{name}.png'
  groundAnchor=load(Path(str(R/gf)+'.derivation.json')).get('anchorPx',[128,128]);groundPaste=(256-groundAnchor[0],224-groundAnchor[1]);im=Image.new('RGBA',(512,384));im.alpha_composite(Image.open(R/gf).convert('RGBA'),groundPaste);deps=[ref(gf)]
  for e in EDGES:
   c=next(x for x in farm if x['family']==case['family']and x['slopeCode']==code and x['edge']==e);im.alpha_composite(Image.open(R/c['file']).convert('RGBA'),tuple(c['pasteXY']));deps.append(ref(c['file']))
  return im,case['family']+' slope'+str(code),deps
 for i in range(6):contact([{'family':FAMILIES[i][0],'slopeCode':code}for code,_ in wp.SLOPES],'farm-'+FAMILIES[i][0]+'-all19slopes',farmdraw)
 def roledraw(r):
  code=r['sourceCanonicalSlope'];name={0:'flat',3:'sw',6:'se',9:'nw',12:'ne'}[code];gf=f'assets/world/terrain/terrain-grass-slope-{name}.png';im=Image.new('RGBA',(512,384));im.alpha_composite(Image.open(R/gf).convert('RGBA'),(128,96));track={0:'x',1:'y',2:'left',3:'upper',4:'x',5:'y',6:'x',7:'y',8:'x',9:'y',10:'right',11:'lower',12:'x',13:'y',14:'x',15:'y'}[r['index']];tf='assets/world/infrastructure/rail/rail-rail-segment-'+track+(''if code==0 else'-slope-'+name)+'.png';im.alpha_composite(Image.open(R/tf).convert('RGBA'),(128,160 if code==0 else 96));im.alpha_composite(Image.open(R/r['file']).convert('RGBA'),tuple(r['pasteXYAtBaseZ']));return im,r['sourceName']+' / '+str(r['index']),[ref(gf),ref(tf),ref(r['file'])]
 contact(rail,'rail-all16source-positions',roledraw)
 foundations=load(R/'assets/world/infrastructure/foundations/manifest.json')['coverageMappings'][0]['caseBindings'];water='assets/world/terrain/water-sea-frame-00.png'
 def halfdraw(h):
  c=h['trackCorner'].lower();code=wp.CORNERS[c];mode='HalfTile'+c.upper();f=next(a['whole']for a in foundations if a['slopeCode']==code and a['mode']==mode and a.get('whole'));im=Image.new('RGBA',(512,384));im.alpha_composite(Image.open(R/water).convert('RGBA'),(128,160));im.alpha_composite(Image.open(R/f).convert('RGBA'));track={'w':'left','n':'upper','e':'right','s':'lower'}[c];tf='assets/world/infrastructure/rail/rail-rail-segment-'+track+'.png';ti=Image.open(R/tf).convert('RGBA');mask=Image.new('L',ti.size);keys={'w':['w','n','s'],'n':['n','e','w'],'e':['e','s','n'],'s':['s','w','e']}[c];ImageDraw.Draw(mask).polygon([wp.FLAT_POINTS[k]for k in keys],fill=255);ti.putalpha(ImageChops.multiply(ti.getchannel('A'),mask));im.alpha_composite(ti,(128,128));r=rail[h['sourcePositionIndex']];xy=list(r['pasteXYAtBaseZ']);xy[1]-=32;im.alpha_composite(Image.open(R/r['file']).convert('RGBA'),tuple(xy));return im,'HalfTileWater '+c.upper(),[ref(water),ref(f),ref(tf),ref(r['file'])]
 contact(half,'rail-halftilewater-four-corners',halfdraw)
 html='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>农田与铁路围栏源适配</title><style>body{background:#21483a;color:#f2e5c8;font:15px/1.5 system-ui;margin:20px}main{max-width:1280px;margin:auto}img{max-width:100%;height:auto}a{color:#d4b66d}</style><main><h1>农田与铁路围栏 · 源坡面、角点与分隔线</h1><p>6有效农田家族×6源offset复用36PNG；456个19坡/四边角点绑定。铁路8源role复用8PNG、16位置及4个HalfTileWater角。全部来自现有原生栏段；没有代码重画栏，也不把隐式0变成新实体。</p><a href="../../docs/FENCE_SOURCE_ADAPTER.md">规格与状态</a>'
 for f in pages:html+='<h2>'+Path(f).stem+'</h2><img src="../../'+f+'">'
 html+='</main>';(PRE/'index.html').write_text(html,encoding='utf8');print(json.dumps({'formalPNGs':len(assets),'farmBindings':len(farm),'railRoles':8,'railPositions':len(rail),'halfWaterCorners':len(half),'pages':pages,'manifestSHA256':wp.sha(R/OUT/'manifest.json')}))
if __name__=='__main__':main()

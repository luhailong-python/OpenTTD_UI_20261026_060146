"""Data-driven station/depot/tunnel/bridge assemblies from accepted painted modules."""
from pathlib import Path
from PIL import Image,ImageChops,ImageOps,ImageEnhance,ImageDraw,ImageFont
import numpy as np,json,math
import build_transport_facilities as f
R=f.R
BASE=f.load(f.OUT/'manifest.json')
BY={a['id']:a for a in BASE['assets']}
f.OUT=R/'assets/world/infrastructure/transport-runtime';f.OUT.mkdir(parents=True,exist_ok=True)
MAP=[];QA=[];ANIMS=[]
def img(aid):return Image.open(R/BY[aid]['image']).convert('RGBA')
def ref(aid):return f.source(R/BY[aid]['image'])
def put(im,part,xy,size=None):
 p=part.copy()
 if size:p.thumbnail(size,Image.Resampling.LANCZOS)
 im.alpha_composite(p,tuple(map(round,xy)))
def emit(aid,im,srcs,op,req,anchor=(256,448),**x):return f.emit(aid,im,srcs,op,requirements=req,anchor=anchor,derivedAt=f.datetime.datetime.now(f.datetime.timezone.utc).isoformat(),route='deterministic-derivative',nativeModelGeneration=False,actualModel=None,actualQuality=None,**x)
def split_layers(a,axis='X'):
 im=Image.open(R/a['image']).convert('RGBA');ar=np.asarray(im);yy,xx=np.indices(ar.shape[:2])
 # A conservative shared art partition; complementary Alpha preserves the body.
 # Game-specific depth polygons require next-stage engine validation.
 pivot=a['anchorPx'];bb=im.getbbox();centre=round(bb[1]+.62*(bb[3]-bb[1]))
 masks={'rear':yy<centre,'front':yy>=centre}
 layers={}
 for name,mask in masks.items():
  p=ar.copy();p[:,:,3]=np.where(mask,ar[:,:,3],0);p[p[:,:,3]==0,:3]=0
  b=emit(a['id']+'-'+name,Image.fromarray(p),[f.source(R/a['image'])],'Complementary authored screen-depth Alpha partition; retains every original painted pixel, engine occlusion not yet validated',a.get('sourceRequirementIds',[]),anchor=tuple(pivot),layer=name)
  layers[name]=b['image']
 re=Image.new('RGBA',im.size)
 for name in ['rear','front']:re.alpha_composite(Image.open(R/layers[name]).convert('RGBA'))
 s=ar.copy();s[s[:,:,3]==0,:3]=0
 good=bool(np.array_equal(np.asarray(re),s));QA.append({'id':a['id']+'.layer-reassemble','level':'OK'if good else'FAIL','exactVisibleRGBA':good})
 return layers
def stations():
 configs=['rail-platform','rail-platform-axis-y','rail-station-hall','rail-station-hall-axis-y','rail-canopy','rail-canopy-axis-y','rail-canopy','rail-canopy-axis-y']
 states=[]
 for n,aid in enumerate(configs):
  im=img(aid)
  if n>=6:im=ImageChops.offset(im,0,0) # Alternate A/B uses same roof painting; side supplied in placement mapping.
  a=emit('station-rail-layout-'+str(n),im,[ref(aid)],'Source station eight layouts mapped to two axes/four platform-building-canopy roles; A/B canopy shares native painting with opposite platform-side metadata',['station-rail'],axis='X'if n%2==0 else'Y',platformSide='front'if n>=6 else'rear')
  layers=split_layers(a);states.append({'layout':n,'axis':a['axis'],'image':a['image'],'layers':layers,'nativeFamily':aid,'platformSide':a['platformSide']})
 MAP.append({'requirementId':'station-rail','files':[s['image']for s in states],'states':states,'sourceLayouts':8,'source':'src/table/station_land.h:54-99','completeVariantCoverage':True})
 for kind in ['bus','truck']:
  states=[]
  for n,d in enumerate(['NE','SE','SW','NW','X','Y']):
   if n<4:
    aid=('bus-bay'if kind=='bus'else'truck-bay') if d in['SE','SW']else'road-depot-view-'+d
    im=img(aid)
    if d=='SE'and not aid.endswith('view-SE'):im=ImageOps.mirror(im)
   else:aid='bus-bay'if kind=='bus'else'truck-bay';im=img(aid if d=='X'else aid+'-axis-y')
   a=emit('station-'+kind+'-layout-'+str(n),im,[ref(aid)],'Shared painted stop shelter/loading bay with true native rear service view where required; X/Y drive-through topology is separate data, no new native painting',['station-'+kind],direction=d,sourceLayout=n)
   layers=split_layers(a);states.append({'layout':n,'direction':d,'image':a['image'],'layers':layers,'roadPorts':d if n<4 else['NE','SW']if d=='X'else['NW','SE']})
  MAP.append({'requirementId':'station-'+kind,'files':[s['image']for s in states],'states':states,'sourceLayouts':6,'completeVariantCoverage':True,'redesignRule':'Taoist terminal is modular shelter; route endpoints and drive-through topology retain original source roles'})
 for kind,count in [('rail',8),('road',2)]:
  ss=[]
  for n in range(count):
   aid='rail-signalbox'if kind=='rail'else'rail-ticketgate';im=img(aid if n%2==0 else aid+'-axis-y')
   a=emit('station-'+kind+'-waypoint-'+str(n),im,[ref(aid)],'Shared native signalbox/ticketgate as waypoint marker; source route axis and slot retained',['station-'+kind+'-waypoint'],axis='X'if n%2==0 else'Y')
   ss.append({'layout':n,'axis':a['axis'],'image':a['image'],'layers':split_layers(a)})
  MAP.append({'requirementId':'station-'+kind+'-waypoint','states':ss,'files':[s['image']for s in ss],'completeVariantCoverage':True})
def depots():
 for kind in ['rail','road','ship']:
  ss=[]
  for d in(['NE','SE','SW','NW']if kind!='ship'else['X','Y']):
   aid=kind+'-depot-view-'+d if kind!='ship'else'ship-depot'+('-axis-y'if d=='Y'else'')
   im=img(aid);a=emit('depot-'+kind+'-'+d,im,[ref(aid)],'Native four service perspectives or symmetric ship-depot axis reflection; no fake rear from front image',['depot-'+kind],direction=d)
   ss.append({'direction':d,'image':a['image'],'layers':split_layers(a),'worldTileFootprintSuggested':[1,1]if kind!='ship'else[2,1]})
  MAP.append({'requirementId':'depot-'+kind,'directions':[s['direction']for s in ss],'states':ss,'files':[s['image']for s in ss],'completeVariantCoverage':True})
 # Rail technology depots retain differentiated native fronts and share rear shells.
 techs={}
 for typ in ['rail','electric','monorail','maglev']:
  aid={'rail':'rail-depot-steam','electric':'rail-depot-electric','monorail':'rail-depot-monorail','maglev':'rail-depot-maglev'}[typ]
  techs[typ]={'SW':BY[aid]['image'],'SE':BY[aid+'-axis-y']['image'],'NE':'assets/world/infrastructure/transport-runtime/depot-rail-NE.png','NW':'assets/world/infrastructure/transport-runtime/depot-rail-NW.png','rearReuseDeclared':True}
 MAP.append({'requirementId':'depot-rail','technologyDirectionMap':techs,'files':[BY[a]['image']for a in ['rail-depot-steam','rail-depot-electric','rail-depot-monorail','rail-depot-maglev']],'completeVariantCoverage':True})
def road_path(kind,d,climate):
 if kind in['road','tram']:return R/'assets/world/infrastructure/roads'/((kind+'-mask-05.png')if d in['NE','SW']else(kind+'-mask-10.png'))
 if kind=='electric':kind='rail' # Catenary is a separate tall layer, never paste a320px overhead composite as a128px floor.
 return R/'assets/world/infrastructure/rail'/('rail-'+kind+'-mask-'+('01'if d in['NE','SW']else'02')+'-'+climate+'.png')
def climate_grade(im,climate):
 if climate=='normal':return im
 a=np.asarray(im).copy();rgb=a[:,:,:3].astype(float)
 if climate=='snow':rgb=rgb*.78+np.array([210,225,226])*.22
 else:rgb=rgb*.86+np.array([218,190,141])*.14
 a[:,:,:3]=np.uint8(np.clip(rgb,0,255));a[a[:,:,3]==0,:3]=0;return Image.fromarray(a)
_LANE_MATERIALS={};_LANE_BRIDGES={};_PORTAL_BODIES={};_LANE_TUNNELS={}
def painted_lane_material(kind):
 """Only sample actual painted pavement/rail strips; never synthesize strokes."""
 if kind=='electric':kind='rail'
 if kind in _LANE_MATERIALS:return _LANE_MATERIALS[kind]
 if kind in ['road','tram']:
  from build_world_network import native_road_uv,sample_uv,UV
  path=R/'source-art/world/road-topology.png';sheet=Image.open(path).convert('RGBA')
  uv=native_road_uv(sheet,4 if kind=='road'else 15).convert('RGBA')
  if kind=='tram':
   y,x=np.mgrid[0:UV,0:UV]/(UV-1);uv=sample_uv(uv,x,y+.115*x-.065)
  # Exclude all painted grass/roadside flowers; keep both actual rails for tram.
  box=(8,68,184,115)if kind=='road'else(0,57,192,135)
  strip=uv.crop(box);detail={'nativeCellIndex':4 if kind=='road'else 15,'normalizedUVInteriorCrop':list(box),'nativeDiamondHalfWidth':160,'tramCentrelineCorrection':'.115*u-.065'if kind=='tram'else None}
  if kind=='road':
   ar=np.asarray(strip).copy();r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0);grass=(g>r*1.06)&(g>b*1.10);ar[grass]=0;strip=Image.fromarray(ar);detail['edgeGrassAlphaExcludedPixels']=int(grass.sum())
 else:
  path=R/'source-art/world/rail-topology.png';sheet=Image.open(path).convert('RGBA')
  box={'rail':[155,89,225,284],'monorail':[548,695,603,897],'maglev':[900,700,1020,910]}[kind]
  strip=sheet.crop(box).transpose(Image.Transpose.ROTATE_90)
  strip=strip.resize((192,{'rail':54,'monorail':48,'maglev':72}[kind]),Image.Resampling.LANCZOS)
  detail={'nativeAtlasCrop':box,'nativeCropRotation':90}
 border=Image.new('RGBA',(strip.width+4,strip.height+4));border.alpha_composite(strip,(2,2))
 a=emit('lane-source-'+kind,border,[f.source(path)],'Actual painted central transport strip crop and UV normalization; 2px transparent export border; roadside grass excluded; no new painted pixels',[],anchor=(border.width//2,border.height//2),category='transport-lane-material',innerUVRectPx=[2,2,strip.width+2,strip.height+2],**detail)
 _LANE_MATERIALS[kind]=(strip,a);return strip,a
def lane_uv_coordinates(size,quad):
 yy,xx=np.indices(size[::-1]);p0,p1,p2,p3=np.asarray(quad,float)
 inv=np.linalg.inv(np.column_stack([p3-p0,p1-p0]));delta=np.stack([xx-p0[0],yy-p0[1]])
 uv=np.einsum('ij,jhw->ihw',inv,delta);return uv[0],uv[1]
def sample_lane(strip,u,v,valid):
 out=np.asarray(_bridge_sample(strip,u*(strip.width-1),v*(strip.height-1))).copy()
 out[~valid]=0;return Image.fromarray(out)
def alpha_mask_asset(aid,mask,srcs,req,anchor):
 ar=np.zeros((*mask.shape,4),np.uint8);ar[:,:,:3]=255;ar[:,:,3]=np.uint8(mask)*255;ar[~mask,:3]=0
 return emit(aid,Image.fromarray(ar),srcs,'Authored geometric/ownership Alpha mask DATA only, no painted colour or strokes',req,anchor=anchor,category='transport-mask-data',spriteTypeSuggestion='Single; data mask, do not display as art')
_PORTAL_GEOMETRY={
 'SE':{'quad':[[257,388],[313,360],[421,414],[365,442]],'floorPolygon':[[278,371],[300,358],[337,374],[280,399]]},
 'SW':{'quad':[[243,396.5],[187,368.5],[79,422.5],[135,450.5]],'floorPolygon':[[237,377],[213,363],[161,383],[221,407]]},
}
def clean_portal(direction,climate):
 key=(direction,climate)
 if key in _PORTAL_BODIES:return _PORTAL_BODIES[key]
 aid='tunnel-portal-'+direction;native=img(aid);ar=np.asarray(native).copy();g=_PORTAL_GEOMETRY[direction]
 u,v=lane_uv_coordinates(native.size,g['quad']);corridor=(u>=.01)&(u<=.99)&(v>=.11)&(v<=.89)
 pm=Image.new('L',native.size);ImageDraw.Draw(pm).polygon(g['floorPolygon'],fill=255)
 rgb=ar[:,:,:3].astype(float);r,gr,b=np.moveaxis(rgb,-1,0);yy,xx=np.indices(ar.shape[:2])
 # Remove only native dark floor and grass already inside the new lane. The
 # ivory arch, gold lamps and foreground columns remain original painted RGBA.
 owned=(((np.asarray(pm)>0)&(rgb.max(2)<110))|((yy>370)&(gr>r*1.08)&(gr>b*1.12)))&corridor
 owned&=ar[:,:,3]>0;ar[owned]=0;body=climate_grade(Image.fromarray(ar),climate)
 mask=alpha_mask_asset('portal-floor-mask-'+direction,owned,[ref(aid)],['tunnel-'+k for k in ['rail','electric','monorail','maglev','road','tram']],(256,448))if climate=='normal'else _PORTAL_BODIES[(direction,'normal')][2]
 a=emit('portal-lane-clean-'+direction+'-'+climate,body,[ref(aid),f.source(R/mask['image'])],'Remove actual dark portal floor / approach grass Alpha inside measured lane corridor only; retain every painted stone wall, lamp and column; declared climate grade',[],cleanedOriginalImage=BY[aid]['image'],removedFloorMask=mask['image'],ownershipPixelCount=int(owned.sum()))
 preserved=np.array_equal(np.asarray(body)[~owned],np.asarray(climate_grade(native,climate))[~owned]);QA.append({'id':a['id']+'.wall-preserved','level':'OK'if preserved else'FAIL','outsideOwnershipExactRGBA':bool(preserved)})
 _PORTAL_BODIES[key]=(body,a,mask);return body,a,mask
def tunnel_lane(kind,d,climate):
 actual='rail'if kind=='electric'else kind;key=(actual,d,climate)
 if key in _LANE_TUNNELS:return _LANE_TUNNELS[key]
 strip,mat=painted_lane_material(actual);quad=np.asarray(_PORTAL_GEOMETRY[d]['quad'],float)
 # Monorail's smaller native beam remains proportionately narrow.
 if actual=='monorail':
  c0=(quad[0]+quad[1])/2;c1=(quad[2]+quad[3])/2
  quad=np.array([c0+(quad[0]-c0)*.82,c0+(quad[1]-c0)*.82,c1+(quad[2]-c1)*.82,c1+(quad[3]-c1)*.82])
 u,v=lane_uv_coordinates((512,512),quad);valid=(u>=0)&(u<=1)&(v>=0)&(v<=1)
 lane=sample_lane(strip,u,v,valid);ar=np.asarray(climate_grade(lane,climate)).copy()
 # Existing tunnel darkness is a colour grade on actual sampled floor paint.
 shade=np.clip(.24+u*3,0.24,1);ar[:,:,:3]=np.uint8(ar[:,:,:3].astype(float)*shade[:,:,None]);ar[ar[:,:,3]==0,:3]=0;lane=Image.fromarray(ar)
 a=emit('lane-tunnel-'+actual+'-'+d+'-'+climate,lane,[f.source(R/mat['image'])],'Measured real portal approach quad -> actual central lane UV texture; no grass tile; interior darkening colour grade; no painted replacement strokes',['tunnel-'+kind],direction=d,climate=climate,laneMaterialUV=mat['image'],targetQuadPx=quad.tolist(),offsetPx=[0,0],uvOrder='near-left inner / far-left inner / far-right outer / near-right outer',uvDomain=[0,0,1,1])
 _LANE_TUNNELS[key]=(lane,a);return lane,a
def tunnels():
 for kind in['rail','electric','monorail','maglev','road','tram']:
  ss=[]
  for climate in['normal','snow','desert']:
   for d in['NE','SE','SW','NW']:
    aid='tunnel-portal-'+d;visible=d in _PORTAL_GEOMETRY;strip,mat=painted_lane_material(kind)
    if visible:
     body,clean,mask=clean_portal(d,climate);floor,fa=tunnel_lane(kind,d,climate)
     can=Image.new('RGBA',(512,512));can.alpha_composite(floor);can.alpha_composite(body);srcs=[f.source(R/clean['image']),f.source(R/fa['image'])]
    else:
     body=climate_grade(img(aid),climate);can=body.copy();srcs=[ref(aid)];clean=None;mask=None;fa=None
    a=emit('tunnel-'+kind+'-'+d+'-'+climate,can,srcs,'Native front/rear portal; front only: actual painted central lane fitted to measured hole/approach and native floor Alpha removed; rear: lane correctly hidden by rock body; climate is declared colour grade',['tunnel-'+kind],direction=d,climate=climate)
    # Split ONLY portal artwork, so floor never appears twice in runtime layers.
    shadow={**a,'image':clean['image']}if visible else a;layers=split_layers(shadow);layers['floor']=fa['image']if visible else None;layers['occluder']=layers['front']
    re=Image.new('RGBA',(512,512))
    for name in ['rear','floor','front']:
     if layers.get(name):re.alpha_composite(Image.open(R/layers[name]).convert('RGBA'))
    exact=bool(np.array_equal(np.asarray(re),np.asarray(can)));QA.append({'id':a['id']+'.installed-layer-reassembly','level':'OK'if exact else'FAIL','exactRGBA':exact})
    ss.append({'direction':d,'climate':climate,'image':a['image'],'layers':layers,'layerOrder':['rear','floor','front'],'floorOffsetPx':[0,0],'floorVisible':visible,'floorHiddenReason':None if visible else'Native rear rock view occludes tunnel approach; do not paste a false foreground street','laneMaterialUV':mat['image'],'laneProjection':{k:fa[k]for k in ['targetQuadPx','uvDomain','uvOrder']}if visible else None,'cleanPortalImage':clean['image']if visible else None,'removedFloorMask':mask['image']if visible else None})
  MAP.append({'requirementId':'tunnel-'+kind,'states':ss,'files':[s['image']for s in ss],'completeVariantCoverage':True,'climateRule':'native image is shared; snow/desert slots use a declared 2D temperature grade and matching source ground; not new native snow detail'})
PORTS=[[128,176],[256,240]]
LANDMARKS={
 # Native FLOOR cross-sections at terminal-column centres, ordered near-left,
 # far-left,far-right,near-right. Occluded floor contacts are inferred beneath
 # the painted column, paired with the visible gold-cap centres below.
 # Previous pairs selected the lower fascia/legs, making the real deck shorter
 # than the128px advance. These measurements are from the512px native modules.
 'wood':[[86,242],[146,214],[427,348],[365,376]],
 'concrete':[[86,258],[159,227],[434,358],[362,390]],
 'truss':[[83,278],[172,244],[430,378],[344,412]],
 'cantilever':[[76,259],[149,228],[435,376],[374,406]],
 'arch':[[79,281],[170,244],[433,386],[365,422]],
 'suspension':[[78,278],[177,242],[436,381],[350,418]],
 'tubular':[[91,284],[161,248],[431,382],[354,420]],
}
POST_LANDMARKS={
 # Visible native gold-cap centres and the near column's lower contact.
 # Each (left,right) pair denotes the same repeating structural interface.
 'wood':[((86,226),(365,356)),((146,194),(427,324)),((89,316),(358,442))],
 'concrete':[((86,238),(362,368)),((159,206),(434,333)),((90,311),(360,438))],
 'truss':[((83,229),(344,350)),((172,176),(430,300)),((85,317),(348,441))],
 'cantilever':[((76,243),(374,389)),((149,207),(435,350)),((77,291),(375,420))],
 'arch':[((79,239),(365,381)),((170,190),(433,342)),((80,296),(367,440))],
 'suspension':[((78,209),(350,352)),((177,164),(436,301)),((78,298),(350,438))],
}
_BRIDGE_GEOMETRY_CACHE={}

def _bridge_interp(x,nodes,values):
 nodes=np.asarray(nodes,float);values=np.asarray(values,float)
 y=np.interp(x,nodes,values)
 y=np.where(x<nodes[0],values[0]+(x-nodes[0])*(values[1]-values[0])/(nodes[1]-nodes[0]),y)
 y=np.where(x>nodes[-1],values[-1]+(x-nodes[-1])*(values[-1]-values[-2])/(nodes[-1]-nodes[-2]),y)
 return y

def _bridge_sample(im,sx,sy):
 rgba=np.asarray(im).astype(float)/255;rgba[:,:,:3]*=rgba[:,:,3:4]
 x0=np.floor(sx).astype(int);x1=x0+1;y0=np.floor(sy).astype(int);y1=y0+1
 dx=(sx-x0)[:,:,None];dy=(sy-y0)[:,:,None]
 x0=np.clip(x0,0,im.width-1);x1=np.clip(x1,0,im.width-1);y0=np.clip(y0,0,im.height-1);y1=np.clip(y1,0,im.height-1)
 out=rgba[y0,x0]*(1-dx)*(1-dy)+rgba[y0,x1]*dx*(1-dy)+rgba[y1,x0]*(1-dx)*dy+rgba[y1,x1]*dx*dy
 out[(sx<0)|(sx>=im.width-1)|(sy<0)|(sy>=im.height-1)]=0
 alpha=out[:,:,3:4];out[:,:,:3]=np.divide(out[:,:,:3],alpha,out=np.zeros_like(out[:,:,:3]),where=alpha>1e-9)
 out=np.uint8(np.clip(out*255,0,255));out[out[:,:,3]==0,:3]=0
 return Image.fromarray(out)

def _project_deck_quad(im,quad,axis,ramp):
 family=next((k for k,v in LANDMARKS.items()if v==quad),None)
 key=(family,axis,ramp,hash(im.tobytes()))
 if key in _BRIDGE_GEOMETRY_CACHE:
  cached,meta=_BRIDGE_GEOMETRY_CACHE[key];return cached.copy(),dict(meta)
 lf,lb,rb,rf=np.asarray(quad,float);left=(lf+lb)/2;right=(rf+rb)/2
 scale=128/(right[0]-left[0]);width=((lb[0]-lf[0])+(rb[0]-rf[0]))/2*scale;half=width/2
 source_x=[lf[0],lb[0],rf[0],rb[0]];source_y=[lf[1],lb[1],rf[1],rb[1]]
 target_x=[128-half,128+half,256-half,256+half]
 target_y=[176+half/2,176-half/2,240+half/2,240-half/2]
 top=[scale]*4;bottom=[scale]*4;posts=[]
 if family in POST_LANDMARKS:
  fore,back,feet=POST_LANDMARKS[family]
  for side,pair in [(0,fore),(1,back)]:
   indices=[side,side+2];native_h=[source_y[i]-p[1]for i,p in zip(indices,pair)]
   common_h=sum(native_h)/2*scale
   if min(native_h)>1:
    for i,h in zip(indices,native_h):top[i]=common_h/h
   posts.append({'side':'front'if side==0 else'back','nativeCapCentres':pair,'commonCapHeightPx':common_h})
  depths=[feet[0][1]-source_y[0],feet[1][1]-source_y[2]];common_depth=sum(depths)/2*scale
  if min(depths)>1:
   bottom[0]=common_depth/depths[0];bottom[2]=common_depth/depths[1]
 yy,xx=np.indices((384,384));sx=_bridge_interp(xx,target_x,source_x)
 floor_source=_bridge_interp(sx,source_x,source_y);floor_target=_bridge_interp(xx,target_x,target_y)
 # End cross-sections are rigid collars. The one-level transfer occurs in the
 # middle; source columns remain exactly vertical because x never depends on y.
 rise_fraction=np.clip((xx-(128+half+5))/(128-2*half-10),0,1)
 if ramp:floor_target=floor_target-ramp*rise_fraction
 # Interpolate reference HEIGHTS rather than their scale ratios. This keeps
 # the painted top-rail reference segments linear instead of bowing the beam.
 if family in POST_LANDMARKS:
  fore,back,_=POST_LANDMARKS[family]
  native_height=[source_y[0]-fore[0][1],source_y[1]-back[0][1],source_y[2]-fore[1][1],source_y[3]-back[1][1]]
  target_height=np.asarray(native_height)*np.asarray(top)
  upper=np.interp(sx,source_x,target_height)/np.maximum(1,np.interp(sx,source_x,native_height))
 else:upper=np.full(xx.shape,scale)
 lower=np.interp(sx,source_x,bottom)
 sy=floor_source+(yy-floor_target)/np.where(yy<=floor_target,upper,lower)
 out=_bridge_sample(im,sx,sy)
 mouths=[[128,176],[256,240-ramp]]
 target_quad=[[target_x[0],target_y[0]],[target_x[1],target_y[1]],[target_x[3],target_y[3]-ramp],[target_x[2],target_y[2]-ramp]]
 if axis=='Y':out=ImageOps.mirror(out);mouths=[[384-x,y]for x,y in mouths]
 meta={'method':'measured native floor/column sections -> monotone separable source-pixel rectification; verticals remain vertical',
  'sourceDeckQuadNearLeftFarLeftFarRightNearRight':quad,'sourceDeckMouths':[left.tolist(),right.tolist()],
  'targetDeckMouths':mouths,'targetDeckQuadBeforeAxisMirror':target_quad,'deckCrossSectionHalfX':half,
  'uniformNativeScaleReference':scale,'sourceXKnots':source_x,'targetXKnots':target_x,
  'verticalScaleAboveDeck':top,'verticalScaleBelowDeck':bottom,'nativePostCorrespondence':posts,
  'axisMirror':axis=='Y','rampRisePx':ramp,'advancePx':[128 if axis=='X'else-128,64-ramp],
  'rampProfile':'one-level native-pixel height transfer, constant at complete endpoint collars'if ramp else'flat',
  'nativeGeometryReprojected':True,'nativeDetailClaim':'source-pixel geometric resampling only; no new original painting, fabricated material or added native detail'}
 _BRIDGE_GEOMETRY_CACHE[key]=(out.copy(),meta);return out,dict(meta)

def project_module(im,pts,axis='X',ramp=0):
 if len(pts)==4:return _project_deck_quad(im,pts,axis,ramp)
 (x0,y0),(x1,y1)=pts;s=128/(x1-x0);shear=(64-s*(y1-y0))/(x1-x0)
 dx=128-s*x0;dy=176-s*y0-shear*x0
 # Destination sampling -> source; preserves painted verticals. s<1.
 c=(1/s,0,-dx/s,-shear/(s*s),1/s,(shear*dx/s-dy)/s)
 out=im.transform((384,384),Image.Transform.AFFINE,c,Image.Resampling.BICUBIC)
 if ramp:
  # One-level ramp made by geometric reprojecting existing painted pixels.
  yy,xx=np.indices((384,384));coef=(1,0,0,-ramp/128,1,ramp)
  out=out.transform((384,384),Image.Transform.AFFINE,coef,Image.Resampling.BICUBIC)
 if axis=='Y':out=ImageOps.mirror(out)
 return out,{'uniformNativeScale':s,'yShear':shear,'sourceDeckMouths':pts,'targetDeckMouths':PORTS,'axisMirror':axis=='Y','rampRisePx':ramp}
def bridge_lane(fam,axis,deck,rise,proj,body):
 key=(fam,axis,deck,rise)
 if key in _LANE_BRIDGES:return _LANE_BRIDGES[key]
 strip,mat=painted_lane_material(deck);yy,xx=np.indices((384,384));x=384-xx if axis=='Y'else xx
 half=proj['deckCrossSectionHalfX'];quad=np.asarray(proj['targetDeckQuadBeforeAxisMirror'],float).copy();quad[2:,1]+=rise
 p0,p1,p2,p3=quad;inv=np.linalg.inv(np.column_stack([p3-p0,p1-p0]));rf=np.clip((x-(128+half+5))/(128-2*half-10),0,1)
 delta=np.stack([x-p0[0],yy+rise*rf-p0[1]]);uv=np.einsum('ij,jhw->ihw',inv,delta);u,v=uv
 # This is an interior floor strip, never a full grass tile. Preserve complete
 # endpoint collars and both native railing faces outside this owned region.
 owned=(u>=.015)&(u<=.985)&(v>=.15)&(v<=.85)
 ar=np.asarray(body);r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0)
 floorpaint=(r>95)&(g>75)&(b>45)&(r>=g*.99)&(g>=b*.95)&((r-g)<85)&((g-b)<85)
 owned&=floorpaint # actual jade trusses/roof, dark rails and curved ribs remain in front
 lane=sample_lane(strip,u,(v-.15)/.70,owned)
 # Leave enough native floor at the connectors to meet adjacent terrain; all
 # visible lane pixels still originate in the real source material strip.
 rid='lane-bridge-'+fam+'-'+axis+'-'+deck+'-'+str(rise).replace('-','m')
 a=emit(rid,lane,[f.source(R/mat['image']),ref('bridge-'+fam+'-span')],'Actual central road/rail texture UV projected into measured narrow deck interior using the existing port-locked ramp profile; no roadside grass, no fabricated strokes; native front railings/roof protected',[],anchor=(192,320),category='transport-lane',laneMaterialUV=mat['image'],offsetPx=[0,0],projection=proj,interiorCrossDomain=[.15,.85],longitudinalDomain=[.015,.985],uvDomain=[0,0,1,1],nativeRoofExclusion=fam=='tubular')
 mask=alpha_mask_asset(rid+'-mask',owned,[f.source(R/a['image'])],[],(192,320))
 _LANE_BRIDGES[key]=(lane,a,owned,mask);return lane,a,owned,mask
def installed_bridge(aid,body,proj,fam,axis,deck,rise,source,req,pier,piece=None):
 lane,la,owned,mask=bridge_lane(fam,axis,deck,rise,proj,body)
 ar=np.asarray(body).copy();rear=ar.copy();front=ar.copy();rear[~owned]=0;front[owned]=0
 re=Image.new('RGBA',body.size);re.alpha_composite(Image.fromarray(rear));re.alpha_composite(Image.fromarray(front))
 clean=ar.copy();clean[clean[:,:,3]==0,:3]=0
 exact=bool(np.array_equal(np.asarray(re),clean));QA.append({'id':aid+'.structure-reassembly','level':'OK'if exact else'FAIL','exactNativeStructureRGBA':exact})
 assembled=Image.fromarray(rear);assembled.alpha_composite(lane);assembled.alpha_composite(Image.fromarray(front))
 a=emit(aid,assembled,[ref(source),f.source(R/la['image']),f.source(R/mask['image'])],'Native structural span in frozen measured bridge geometry; actual narrow central road/rail lane installed between complementary native floor/structure layers; declared source-ID livery; no grass deck tile',req,anchor=(192,320),projection=proj,axis=axis,deck=deck,piece=piece,deckLayerImage=la['image'],deckLayerOffsetPx=[0,0],deckMaterialUV=la['laneMaterialUV'],deckOwnershipMask=mask['image'],laneProjection=la['projection'])
 ls={}
 for name,data in [('rear',rear),('front',front)]:
  ba=emit(aid+'-'+name,Image.fromarray(data),[ref(source),f.source(R/mask['image'])],'Complementary native painted bridge floor / protected structure ownership Alpha partition; original railings, posts and roof pixels unchanged',req,anchor=(192,320),layer=name,projection=proj,ownershipMask=mask['image'])
  ls[name]=ba['image']
 ls.update({'lane':la['image'],'pier':pier,'mask':mask['image']})
 rebuilt=Image.new('RGBA',body.size)
 for n in ['rear','lane','front']:rebuilt.alpha_composite(Image.open(R/ls[n]).convert('RGBA'))
 same=bool(np.array_equal(np.asarray(rebuilt),np.asarray(assembled)));preserved=bool(np.array_equal(np.asarray(assembled)[~owned],clean[~owned]));QA.append({'id':aid+'.installed-lane','level':'OK'if same and preserved else'FAIL','layerReassemblyExact':same,'outsideLaneOriginalStructureExactRGBA':preserved,'lanePixelsOutsideOwnership':int(np.count_nonzero((np.asarray(lane)[:,:,3]>0)&~owned))})
 return a,ls
def bridges():
 srcs=f.load(R/'docs/WORLD_ASSET_COVERAGE.json')['items'];bs=[x for x in srcs if x['category']=='bridge']
 families={'wood':'wood','concrete':'concrete','archgirder':'arch','suspension':'suspension','cantilever':'cantilever','girder':'truss','tubular':'tubular'}
 for row in bs:
  fam=families[row['neededVariants']['geometryFamily']];aid='bridge-'+fam+'-span';states=[]
  for axis in['X','Y']:
   body,proj=project_module(img(aid),LANDMARKS[fam],axis)
   # Original bridge IDs sharing geometry get declared restrained material/livery variants.
   if row['neededVariants']['paletteOrMaterialVariant']:
    arr=np.asarray(body).copy();rgb=arr[:,:,:3].astype(float);grade=[.96,1,.96]if row['neededVariants']['sourceBridgeId']%2 else[1,.97,.92];arr[:,:,:3]=np.uint8(np.clip(rgb*np.array(grade),0,255));body=Image.fromarray(arr)
   pi=img('bridge-pier');pi=pi.crop(pi.getbbox());pi.thumbnail((48,90),Image.Resampling.LANCZOS)
   pier=Image.new('RGBA',(384,384));pier.alpha_composite(pi,(192-pi.width//2,292-pi.height))
   pa=emit(row['id']+'-'+axis+'-pier',pier,[ref('bridge-pier')],'Shared native ivory pier proportional downscale and fixed contact placement',[row['id']],anchor=(192,320),layer='pier')
   for deck in['road','rail']:
    a,ls=installed_bridge(row['id']+'-'+axis+'-'+deck,body,proj,fam,axis,deck,0,aid,[row['id']],pa['image'])
    parts={}
    for part in row['neededVariants']['pieces']:
     if part in['north','south','head']:
      rise=32 if part in['north','head']else-32
      ramp,rp=project_module(img(aid),LANDMARKS[fam],axis,rise)
      if row['neededVariants']['paletteOrMaterialVariant']:
       arr=np.asarray(ramp).copy();arr[:,:,:3]=np.uint8(np.clip(arr[:,:,:3].astype(float)*np.array(grade),0,255));ramp=Image.fromarray(arr)
      ra,rls=installed_bridge(row['id']+'-'+axis+'-'+deck+'-'+part,ramp,rp,fam,axis,deck,rise,aid,[row['id']],pa['image'],part)
      parts[part]={'image':ra['image'],'layers':rls,'layerOrder':['rear','lane','front'],'laneOffsetPx':[0,0],'laneMaterialUV':ra['deckMaterialUV'],'laneOwnershipMask':ra['deckOwnershipMask'],'risePx':rise,'advancePx':rp['advancePx'],'deckPortsPx':rp['targetDeckMouths']}
     else:parts[part]={'image':a['image'],'layers':ls,'layerOrder':['rear','lane','front'],'laneOffsetPx':[0,0],'laneMaterialUV':a['deckMaterialUV'],'laneOwnershipMask':a['deckOwnershipMask'],'aliasDeclared':True,'reason':'periodic native module; odd/even same repeating structure, suspension towers are separate placement pieces'}
    states.append({'axis':axis,'deck':deck,'pieces':parts,'pier':pa['image'],'deckPortsPx':PORTS if axis=='X'else[[256,176],[128,240]],'advancePx':[128 if axis=='X'else-128,64],'separateSuspensionTower':BY['bridge-suspension-tower']['image']if fam=='suspension'else None})
  MAP.append({'requirementId':row['id'],'sourceBridgeId':row['neededVariants']['sourceBridgeId'],'states':states,'files':sorted({p['image']for s in states for p in s['pieces'].values()}),'sourcePieces':row['neededVariants']['pieces'],'sourceGeometryFamily':row['neededVariants']['geometryFamily'],'completeVariantCoverage':True,'nativeFamily':aid,'variantMethod':'seven structure families; shared source-ID material variants; repeatable span pixels and separate tower/pier; road/rail lanes are independent painted layers','acceptance':'art assembly review; Unity depth/vehicle clearance pending'})
def aqueduct():
 path=R/'assets/world/infrastructure/waterworks/canal-banks.png'
 if not path.exists():raise FileNotFoundError(path)
 im=ImageOps.mirror(Image.open(path).convert('RGBA'))
 # Actual visible bank/water mouth corners in this native mirrored module.
 # Aqueduct heads sit on sloped land, but the water surface stays level.
 # src/tunnelbridge_cmd.cpp:385 and :468 forbid flat/wrong-slope water heads.
 pts=[[30,255],[132,204],[457,370],[357,420]]
 ss=[]
 for axis in['X','Y']:
  for n in range(8):
   rise=0
   part,pr=project_module(im,pts,axis,rise);a=emit('aqueduct-'+axis+'-piece-'+str(n),part,[f.source(path)],'Shared native stone canal banks and water mirrored/reprojected into elevated aqueduct span; horizontal level water in all 8 source roles; four bank heads use sloped land foundation support, never tilted water; separate bridge pier',['water-aqueduct'],anchor=(192,320),projection=pr,sourcePiece=n,axis=axis)
   ss.append({'piece':n,'axis':axis,'image':a['image'],'layers':split_layers(a),'pier':BY['bridge-pier']['image'],'waterSurfaceRisePx':0,'headLandSlopeDirection':['NE','SE','SW','NW'][n] if n<4 else None,'landSupportRule':'select compatible existing foundation support for sloped bank; water remains level','advancePx':pr['advancePx'],'deckPortsPx':pr['targetDeckMouths']})
 MAP.append({'requirementId':'water-aqueduct','files':[s['image']for s in ss],'states':ss,'sourcePieces':8,'axes':['X','Y'],'slopedEntrances':4,'completeVariantCoverage':True,'reuse':'actual painted canal + actual painted bridge pier; no new AI image'})
def main():
 stations();depots();tunnels();bridges();aqueduct()
 failures=f.qa()
 for q in QA:
  if q['level']=='FAIL':failures.append(q)
 pack={'schema':'transport-runtime-art.v2','assets':f.ASSETS,'animations':ANIMS,'qa':[{'level':'FAIL',**q}for q in failures],'coverageMappings':MAP,'artAcceptance':'See current-hash transport-lane visual review and independent whole-pack audit; user acceptance remains separate','unityValidated':False,'laneAssemblyContract':{'originalRuntimeRolePNG':1034,'additionalLaneMaterialUV':5,'additionalBridgeLanePNG':84,'additionalBridgeOwnershipMaskDataPNG':84,'additionalTunnelLanePNG':30,'additionalCleanPortalPNG':6,'additionalPortalFloorMaskDataPNG':2,'artSpritePNG':1159,'maskDataPNG':86,'allFormalPNG':1245,'assemblyPreview':'previews/world/transport-lanes/index.html','validation':'records/world-production/transport-lane-validation.json','wholeVsLayers':'Choose whole PNG OR registered layers, never both','tunnelOrder':['rear','floor','front'],'bridgeOrder':['rear','lane','front'],'allLaneOffsetPx':[0,0],'worldBodiesUseSlicedSprite':False},'limitations':['All source-role mappings are Taoist reinterpretations rather than pixel-identical original sprites.','Renderer placement, selectable bounds, route collision, height and dynamic depth are suggestions, pending Unity.','Complementary native ownership layers reconstruct exactly; the art preview does not validate moving-vehicle depth. Bridge front currently protects all non-floor native structure; engine-specific rear/foreground vehicle masks require next-stage verification.']}
 f.savej(f.OUT/'manifest.json',pack)
 for cat,prefix in [('station','station-'),('depot','depot-'),('tunnel','tunnel-'),('bridge','bridge-'),('aqueduct','aqueduct-')]:
  sample=[a for a in f.ASSETS if a['id'].startswith(prefix)and not a['id'].endswith(('-rear','-front','-pier'))]
  if cat=='bridge':sample=[a for a in sample if a['id'].endswith('-X-road')]
  if cat=='tunnel':sample=[a for a in sample if a['id'].endswith('-normal')]
  f.contact('runtime-'+cat,sample,4)
 f.savej(R/'records/world-production/transport-runtime-validation.json',{'formalPNGs':len(f.ASSETS),'coverageRequirements':len({m['requirementId']for m in MAP}),'checks':len(f.ASSETS)*6+len(QA),'layerReassembly':QA,'failures':failures,'visualReview':'pending contact/stitched-bridge review'})
 print(json.dumps({'assets':len(f.ASSETS),'requirements':len({m['requirementId']for m in MAP}),'failures':len(failures)},ensure_ascii=False))
if __name__=='__main__':main()

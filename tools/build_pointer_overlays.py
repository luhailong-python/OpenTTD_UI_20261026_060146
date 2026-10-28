"""Export hand-painted pointer compositions and explicit geometric selection art.
Existing accepted world images remain read-only inputs. No image-model call here.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,math,base64,io,collections
import world_pack as wp
import build_world_terrain as t
R=wp.ROOT;P='assets/common/pointers';O='assets/world/overlays';PRE=R/'previews/pointers';PRE.mkdir(parents=True,exist_ok=True)
NAMES=['cursor-arrow','cursor-wait','forbidden','pan-four','point-hand','open-hand','diamond-frame','triangle-frame','corner-L','chevron','map-pin','company-flag','path-dot','survey-stake','rail-highlight','wait-clouds']
COL={'neutral':((212,177,103,255),(72,174,140,255),(76,165,134,16)),'coverage-blue':((225,202,138,255),(56,149,218,255),(56,149,218,20)),'invalid-red':((229,192,118,255),(213,69,59,255),(213,69,59,20)),'error-pulse-red':((245,215,150,255),(245,64,45,255),(245,64,45,34)),'authority-amber':((235,213,155,255),(226,158,50,255),(226,158,50,24))}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(file):return{'file':file,'sha256':wp.sha(R/file),'record':file+'.derivation.json'}
def white_point_recipe_metadata():
 # This is literal UI geometry. The production code is its source, not a painted PNG.
 recipeFile='tools/build_pointer_overlays.py'
 return {'derivedFrom':[{'file':recipeFile,'sha256':wp.sha(R/recipeFile),'sourceType':'functional-geometry-recipe','recipeId':'SPR_WHITE_POINT.v1'}],'operation':'literal functional UI point on transparent RGBA canvas;one putpixel at(16,16),RGBA(250,242,217,255);no painted parent or native model generation','artSource':'functional-geometry','functionalGeometryRecipe':{'id':'SPR_WHITE_POINT.v1','sourceSymbol':'SPR_WHITE_POINT','sourceSpriteId':4079,'canvasPx':[32,32],'mode':'RGBA','backgroundRGBA':[0,0,0,0],'pointPx':[16,16],'pointRGBA':[250,242,217,255],'coordinateOrigin':'top-left','paintedArtworkParent':False},'provenanceCorrection':{'reason':'Original record correctly disclosed one-pixel UI geometry but omitted its production-code dependency;add actual recipe source instead of inventing a hand-painted PNG parent.','pixelChange':False,'validationRecord':'records/pointer-white-point-recipe-validation.json'}}
def crop(im):return im.crop(im.getchannel('A').getbbox())
def fit(im,box):
 im=crop(im);f=min(box[0]/im.width,box[1]/im.height,1);return im.resize((max(1,round(im.width*f)),max(1,round(im.height*f))),Image.Resampling.LANCZOS)
def emit(file,im,srcs,operation,extra=None):
 p=R/file;p.parent.mkdir(parents=True,exist_ok=True);ar=np.asarray(im.convert('RGBA')).copy();ar[ar[...,3]==0,:3]=0;im=Image.fromarray(ar);im.save(p);a={'id':p.stem,'image':file,'width':im.width,'height':im.height,'format':'PNG','mode':'RGBA','sha256':wp.sha(p),'derivedFrom':srcs,'operation':operation,'nativeModelGeneration':False,'nativeUpscale':False,'actualModel':None,'actualQuality':None,'unityValidated':False,'userArtAcceptance':'pending',**(extra or{})};wp.writej(Path(str(p)+'.derivation.json'),a);return a
def extract():
 from scipy.ndimage import label,find_objects,binary_dilation
 src='source-art/pointer-overlay-kit.png';im=Image.open(R/src).convert('RGBA');ar=np.asarray(im);labs,n=label(ar[...,3]>20,np.ones((3,3)));sizes=np.bincount(labs.ravel());boxes=find_objects(labs);by=collections.defaultdict(list)
 for k in range(1,n+1):
  if sizes[k]<150:continue
  y,x=boxes[k-1];slot=min(3,int((y.start+y.stop)/512))*4+min(3,int((x.start+x.stop)/768));by[slot].append(k)
 if set(by)!=set(range(16)):raise ValueError('Native component slot extraction incomplete')
 components={};entries=[]
 for i,name in enumerate(NAMES):
  mask=binary_dilation(np.isin(labs,by[i]),iterations=6);out=ar.copy();out[~mask]=0;out[out[...,3]==0,:3]=0;raw=Image.fromarray(out);bb=raw.getchannel('A').getbbox();part=raw.crop(bb);canvas=Image.new('RGBA',(384,320));at=((384-part.width)//2,(320-part.height)//2)
  if min(at)<0:raise ValueError('No native upscale; component exceeds master canvas '+name)
  canvas.alpha_composite(part,at);a=emit(P+'/components/'+name+'.png',canvas,[{'file':src,'sha256':wp.sha(R/src),'record':src+'.generation.json'}],'actual native Alpha component crop beyond equal cell borders,6px source Alpha fringe ownership, source RGB unchanged, transparent native-resolution padding; no AI editing',{'category':'native-pointer-component','nativeSourceBBox':list(bb),'nativeComponentLabels':by[i],'nativePixelScale':1,'paddingLeftTop':list(at),'artSource':'host_image_derivative','trueAlphaInterior':'source Alpha retained; diamond/triangle/forbidden interiors are genuinely transparent, hidden RGB discarded'});entries.append(a);components[name]=a
 wp.writej(R/P/'components/manifest.json',{'schema':'pointer-components.v1','assets':entries,'nativePaintedComponentGroups':16,'sourceNativeCanvas':[1536,1024],'actualModel':None,'actualQuality':None,'unityValidated':False});return components,entries
def cursorbase(comp):
 raw=Image.open(R/comp['cursor-arrow']['image']).convert('RGBA');arrow=fit(raw,(78,80));base=Image.new('RGBA',(96,96));base.alpha_composite(arrow,(6,6));a=np.asarray(base);ys,xs=np.where(a[...,3]>128);k=np.argmin(xs+ys);hot=[int(xs[k]),int(ys[k])];return base,hot
def modifier(im,req,comp):
 name=req['id'];d=ImageDraw.Draw(im)
 if any(k in name for k in ['NS_','SWNE_','EW_','NWSE_','NESW_']):
  # Functional orientation glyph is vector UI geometry, not a new painting.
  if'NS_'in name:p=[(80,73),(80,87)]
  elif'EW_'in name:p=[(73,80),(87,80)]
  elif'SWNE_'in name or'NESW_'in name:p=[(74,86),(86,74)]
  else:p=[(74,74),(86,86)]
  d.line(p,fill=(255,243,206,255),width=4);d.line(p,fill=(35,119,94,255),width=2)
 if'CONVERT'in name:
  part=fit(Image.open(R/comp['chevron']['image']).convert('RGBA'),(13,15));im.alpha_composite(part,(75,71));im.alpha_composite(part.rotate(180),(66,78))
 if'CLONE'in name:
  d.rounded_rectangle((66,72,81,86),radius=3,fill=(244,234,204,240),outline=(194,160,83,255),width=2);d.rounded_rectangle((73,77,88,91),radius=3,fill=(244,234,204,255),outline=(49,139,109,255),width=2)
 if'AUTO'in name:
  part=fit(Image.open(R/comp['diamond-frame']['image']).convert('RGBA'),(21,13));im.alpha_composite(part,(69,79))
def badgepaste(im,file,box=(48,48,42,42)):
 raw=Image.open(R/file).convert('RGBA');part=fit(raw,(box[2],box[3]));im.alpha_composite(part,(box[0]+(box[2]-part.width)//2,box[1]+(box[3]-part.height)//2))
def cursors(inv,comp):
 base,hot=cursorbase(comp);entries=[];bindings=[];clips=[]
 for req in inv['items']:
  if req['category']!='static-cursor':continue
  im=base.copy();badge=req.get('badgeSource',{});refs=[ref(comp['cursor-arrow']['image'])]
  if req['id']=='SPR_CURSOR_ZZZ':badge={'file':comp['cursor-wait']['image']}
  if badge and badge.get('file'):badgepaste(im,badge['file']);refs.append(ref(badge['file']))
  modifier(im,req,comp);en=emit(P+'/cursors/'+req['id']+'.png',im,refs,'same native arrow with actual measured tip hotspot; native functional badge downsample/padding; explicit vector orientation/clone or native chevron conversion modifier; no new native drawing',{'category':'static-cursor','sourceSymbol':req['id'],'sourceSpriteId':req['source']['numericValue'],'hotspotPx':hot,'anchorPx':hot,'status':'produced-needs-visual-review'});entries.append(en);bindings.append({'id':req['id'],'file':en['image'],'sha256':en['sha256'],'canvasPx':[96,96],'hotspotPx':hot,'sourceRequirementIds':[req['id']],'operation':en['operation'],'semanticModifiers':req['proposedRecipe']['semanticModifiers'],'localArtReviewed':False})
 for req in inv['items']:
  if req['category']!='animated-cursor':continue
  files=[];states=[];frameids=[];ticks=[]
  for i,fr in enumerate(req['sourceFrames']):
   im=base.copy();refs=[ref(comp['cursor-arrow']['image'])];badge=req['badgeFile'];badgepaste(im,badge);refs.append(ref(badge))
   if req['id']=='ANIMCURSOR_DEMOLISH':
    spark='assets/world/effects/electric-spark/'+format(i,'02d')+'.png';badgepaste(im,spark,(63,36,29,29));refs.append(ref(spark))
   elif req['id']in ['ANIMCURSOR_RAISELAND','ANIMCURSOR_LOWERLAND']:
    part=fit(Image.open(R/comp['chevron']['image']).convert('RGBA'),(15,18));part=part.rotate(90 if'RAISE'in req['id']else-90,expand=True);im.alpha_composite(part,(58,43+(i*4 if'LOWER'in req['id']else 8-i*4)));refs.append(ref(comp['chevron']['image']))
   elif req['id']=='ANIMCURSOR_PICKSTATION':
    part=fit(Image.open(R/comp['path-dot']['image']).convert('RGBA'),(15+i*3,15+i*3));im.alpha_composite(part,(76-i,42-i));refs.append(ref(comp['path-dot']['image']))
   else:
    # Large native red/green lamp remains legible at96px cursor canvas.
    im=base.copy();sig='assets/world/infrastructure/signal-states/signal-electric-block-S-'+('red'if i==0 else'green')+'.png';badgepaste(im,sig,(61,35,31,57));refs.append(ref(sig))
   en=emit(P+'/animations/'+req['id']+'/'+fr['symbol']+'.png',im,refs,'native fixed arrow plus explicitly changing painted spark / translated arrow / growing native selection gem / red-green signal badge; exact source display ticks retained; not new native frames',{'category':'animated-cursor-frame','sourceGroup':req['id'],'sourceFrameSymbol':fr['symbol'],'sourceFrameId':fr['spriteId'],'displayTicks':fr['displayTicks'],'displayMs':fr['displayTicks']*27,'hotspotPx':hot,'anchorPx':hot,'status':'produced-needs-visual-review'});entries.append(en);files.append(en['image']);states.append({'file':en['image'],'sha256':en['sha256'],'hotspotPx':hot,'sourceFrameId':fr['spriteId']});frameids.append(fr['spriteId']);ticks.append(fr['displayTicks'])
  b={'id':req['id'],'layers':[ref(f)for f in files],'canvasPx':[96,96],'hotspotPx':hot,'sourceFrameIds':frameids,'sourceTicks':ticks,'states':states,'operation':'explicit native-paint composited cursor phases with same96canvas/hotspot; original source frame IDs and ticks; art preview milliseconds=ticks×27 from src/gfx_type.h417','localArtReviewed':False};bindings.append(b);clips.append({'id':req['id'],'frames':files,'durationsMs':[x*27 for x in ticks],'sourceTicks':ticks,'sourceFrameIds':frameids,'sourceTickMs':27,'loop':True,'frameSize':[96,96],'fixedHotspotPx':hot})
 wp.writej(R/P/'manifest.json',{'schema':'pointer-cursor-art.v1','assets':entries,'animations':clips,'hotspotEvidence':{'method':'min(x+y) of visible Alpha>128 on actual resized native arrow tip; measured after96canvas registration','hotspotPx':hot,'canvasPx':[96,96],'sameForAllFrames':True},'sourceCursorStaticCount':72,'sourceAnimatedGroups':5,'sourceTickMs':27,'sourceTickEvidence':'reference/OpenTTD/src/gfx_type.h:417','userArtAcceptance':'pending','unityValidated':False});return entries,bindings,clips
def height(u,v,code):
 uv={'n':(0,0),'e':(1,0),'s':(1,1),'w':(0,1)};h=wp.corner_heights(code)
 for tri in wp.slope_triangles(code):
  p=np.array([uv[k]for k in tri]);matrix=np.array([[p[0,0]-p[2,0],p[1,0]-p[2,0]],[p[0,1]-p[2,1],p[1,1]-p[2,1]]]);ab=np.linalg.solve(matrix,np.array([u,v])-p[2]);w=[ab[0],ab[1],1-ab.sum()]
  if min(w)>=-1e-6:return sum(wi*h[k]for wi,k in zip(w,tri))
 raise ValueError('outsideUV')
def xy(u,v,z):return(144+(u-v)*128,80+(u+v)*64-z*32)
def gem(comp,state,size=16):
 im=fit(Image.open(R/comp['path-dot']['image']).convert('RGBA'),(size,size));ar=np.asarray(im).copy();r,g,b=np.moveaxis(ar[...,:3].astype(float),-1,0);green=(g>r*1.02)&(g>b*1.02)
 tint={'neutral':[64,165,132],'coverage-blue':[60,147,212],'invalid-red':[212,70,56],'error-pulse-red':[237,68,47],'authority-amber':[227,160,51]}[state];lum=(r+g+b)/3;ar[green,:3]=np.uint8(np.clip(lum[green,None]*.3+np.array(tint)*.7,0,255));return Image.fromarray(ar)
def overlay(id,points,state,closed,comp,extra):
 size=(288,224);outer,inner,fill=COL[state];scale=4;im=Image.new('RGBA',(size[0]*scale,size[1]*scale));d=ImageDraw.Draw(im);pts=[(round(x*scale),round(y*scale))for x,y in points]
 if closed:d.polygon(pts,fill=fill)
 line=pts+[pts[0]]if closed else pts;d.line(line,fill=outer,width=7*scale,joint='curve');d.line(line,fill=inner,width=4*scale,joint='curve');im=im.resize(size,Image.Resampling.LANCZOS);g=gem(comp,state);vertices=points if closed else[points[0],points[-1]]
 for x,y in vertices:im.alpha_composite(g,(round(x-g.width/2),round(y-g.height/2)))
 # StandaloneSVG embeds the exact native16px endpoint gem, with geometric path.
 bio=io.BytesIO();g.save(bio,format='PNG');data=base64.b64encode(bio.getvalue()).decode();path='M '+' L '.join(f'{x:.4f},{y:.4f}'for x,y in points)+(' Z'if closed else'');rgb=lambda c:f'rgb({c[0]},{c[1]},{c[2]})';svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="288" height="224" viewBox="0 0 288 224"><path d="{path}" fill="{rgb(fill) if closed else "none"}" fill-opacity="{fill[3]/255 if closed else 0}" stroke="{rgb(outer)}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/><path d="{path}" fill="none" stroke="{rgb(inner)}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
 for x,y in vertices:svg+=f'<image href="data:image/png;base64,{data}" x="{x-g.width/2}" y="{y-g.height/2}" width="{g.width}" height="{g.height}"/>'
 svg+='</svg>';sf=O+'/svg/'+id+'.svg';(R/sf).parent.mkdir(parents=True,exist_ok=True);(R/sf).write_text(svg,encoding='utf8');en=emit(O+'/'+id+'.png',im,[ref(comp['path-dot']['image']),{'file':sf,'sha256':wp.sha(R/sf),'sourceType':'authored-vector-geometry'}],'code-authored exact UI geometry, palette and native hand-painted endpoint gem; actual source slope/selection semantics; PNG4xAA raster and standaloneSVG; no AI-generated geometry claim',{'category':'interaction-overlay','artSource':'vector-geometry-and-native-detail','anchorPx':[144,144],'pivotUnity':[.5,1-144/224],'geometryFile':sf,'paletteRole':state,**extra,'status':'produced-needs-visual-review'});return en
def overlays(inv,comp):
 entries=[];bindings=[]
 for req in inv['items']:
  cat=req['category']
  if cat not in ['tile-selection','halftile-selection','autorail-selection']:continue
  statekeys=list(COL)if cat!='autorail-selection'else(['invalid-red']if req['invalidBySourceTable']else['neutral','invalid-red']);files=[];geos=[]
  if cat=='tile-selection':
   corners=[(0,0),(1,0),(1,1),(0,1)];points=[xy(u,v,height(u,v,req['sourceSlopeCode']))for u,v in corners];closed=True
  elif cat=='halftile-selection':
   names=['w','s','e','n'];alluv={'w':(0,1),'s':(1,1),'e':(1,0),'n':(0,0)};n=names[req['corner']];cycle=['n','e','s','w'];idx=cycle.index(n);keys=[n,cycle[(idx+1)%4],cycle[(idx-1)%4]];points=[]
   for k in keys:
    z=0 if req['shape']=='flat'else(1 if (req['shape']=='up')==(k==n)else 0);points.append(xy(*alluv[k],z))
   closed=True
  else:
   direction=req['highlightDirectionIndex'];ports=[(0,.5),(.5,0),(1,.5),(.5,1)];pair=[(1,3),(0,2),(0,1),(2,3),(0,3),(1,2)][direction];a,b=[ports[i]for i in pair];uv=[]
   if direction<2:uv=[(a[0]*(1-z)+b[0]*z,a[1]*(1-z)+b[1]*z)for z in np.linspace(0,1,41)]
   else:
    center={(0,1):(0,0),(2,3):(1,1),(0,3):(0,1),(1,2):(1,0)}[tuple(sorted(pair))];aa=math.atan2(a[1]-center[1],a[0]-center[0]);bb=math.atan2(b[1]-center[1],b[0]-center[0]);delta=(bb-aa+math.pi)%(2*math.pi)-math.pi;uv=[(center[0]+.5*math.cos(aa+delta*z),center[1]+.5*math.sin(aa+delta*z))for z in np.linspace(0,1,41)]
   points=[xy(u,v,height(u,v,req['sourceSlopeCode']))for u,v in uv];closed=False
  for state in statekeys:
   en=overlay(req['id']+'-'+state,points,state,closed,comp,{'sourceRequirementId':req['id'],'sourceSpriteId':req['sourceSpriteId'],'sourceSlopeCode':req.get('sourceSlopeCode'),'halfCorner':req.get('corner'),'halfShape':req.get('shape'),'invalidBySourceTable':req.get('invalidBySourceTable'),'geometryPointsPx':[[float(x),float(y)]for x,y in points]});entries.append(en);files.append(en['image']);geos.append(en['geometryFile'])
  bind={'id':req['id'],'layers':[ref(f)for f in files],'geometryFile':geos[0],'sha256':wp.sha(R/geos[0]),'states':statekeys,'sourceSlopeCode':req.get('sourceSlopeCode'),'sourceSpriteId':req['sourceSpriteId'],'operation':'saved exact geometric PNG/SVG; native hand-painted endpoint gems only; corner interpolation follows source legal slopes; half modules explicitly0/1corner rise and caller-supplied foundation base height; source invalid autorail negative offsets retain red palette','localArtReviewed':False,'canvasPx':[288,224],'anchorPx':[144,144],'errorPulseRecipe':{'alphaKeys':[.45,1,.45],'previewDurationsMs':[240,240,240],'timing':'art preview suggestion; source palette tick adapter pending'}if cat!='autorail-selection'else None,'globalInvalidOverride':'retint stroke/gem to invalid-red when make_square_red, regardless of legal source path; no runtime code supplied'};bindings.append(bind)
 wp.writej(R/O/'manifest.json',{'schema':'selection-overlays-art.v1','assets':entries,'sourceNormalSlopeCount':19,'sourceHalftileModuleCount':12,'sourceAutorailCaseCount':114,'sourceAutorailUsedOffsetCount':50,'reservedSourceBlockCount':55,'unreferencedReservedOffsets':[50,51,52,53,54],'projection':{'canvas':[288,224],'anchorPx':[144,144],'baseTilePixels':[256,128],'paddingPx':16,'heightStepPx':32},'artSourceClaim':'functional vector geometry plus native endpoint-gem details; never new AI/native4K painting','unityValidated':False});return entries,bindings
def extras(inv,comp):
 bindings=[];entries=[]
 for req in inv['items']:
  if req['category']not in ['corner-marker','point-marker','empty-helper','company-status-marker','window-pin','data-drawn-map-markers','dynamic-sign-label']:continue
  id=req['id']
  if id=='SPR_EMPTY':bindings.append({'id':id,'noDraw':True,'reason':'source empty helper explicitly requires no picture','operation':'empty helper no draw','localArtReviewed':False});continue
  if id=='SPR_COMPANY_ICON':files=['assets/world/infrastructure/object-states/company-flag-'+format(i,'02d')+'.png'for i in range(16)];bindings.append({'id':id,'layers':[ref(f)for f in files],'states':list(range(16)),'operation':'actual16company-colour native cloth derivatives reused at32px legend/company label size; no new art','localArtReviewed':False});continue
  if id in ['SPR_FLAG_VEH_STOPPED','SPR_FLAG_VEH_RUNNING']:
   state='invalid-red'if id.endswith('STOPPED')else'neutral';im=Image.new('RGBA',(32,32));g=gem(comp,state,24);im.alpha_composite(g,((32-g.width)//2,(32-g.height)//2));en=emit(P+'/markers/'+id+'.png',im,[ref(comp['path-dot']['image'])],'actual native jade/gold gem with selective interior colour-grade for stopped-red/running-jade state; source flag function reimagined as32px status gem, no new painting',{'category':'interaction-marker','sourceSymbol':id,'anchorPx':[16,16]});entries.append(en);bindings.append({'id':id,'file':en['image'],'sha256':en['sha256'],'states':['stopped'if id.endswith('STOPPED')else'running'],'operation':en['operation'],'localArtReviewed':False});continue
  if id in ['SPR_DOT','SPR_WHITE_POINT','SPR_PIN_UP','SPR_PIN_DOWN']:
   size=(32,32)if id in ['SPR_DOT','SPR_WHITE_POINT']else(64,64);im=Image.new('RGBA',size)
   if id=='SPR_DOT':g=fit(Image.open(R/comp['path-dot']['image']).convert('RGBA'),(24,24));im.alpha_composite(g,((32-g.width)//2,(32-g.height)//2));srcs=[ref(comp['path-dot']['image'])]
   elif id=='SPR_WHITE_POINT':im.putpixel((16,16),(250,242,217,255));srcs=white_point_recipe_metadata()['derivedFrom']
   else:g=fit(Image.open(R/comp['map-pin']['image']).convert('RGBA'),(48,56));g=g.rotate(180,expand=True)if id=='SPR_PIN_UP'else g;im.alpha_composite(g,((64-g.width)//2,(64-g.height)//2));srcs=[ref(comp['map-pin']['image'])]
   extra={'category':'interaction-marker','sourceSymbol':id,'anchorPx':[size[0]//2,size[1]//2]};operation='native jade marker/pin crop, downsample and declared180degree orientation; WHITE_POINT is explicit one-pixel UI geometry on transparent32canvas, not new native art'
   if id=='SPR_WHITE_POINT':meta=white_point_recipe_metadata();extra.update({k:v for k,v in meta.items()if k not in ['derivedFrom','operation']});operation=meta['operation']
   en=emit(P+'/markers/'+id+'.png',im,srcs,operation,extra);entries.append(en);binding={'id':id,'file':en['image'],'sha256':en['sha256'],'operation':en['operation'],'states':['up'if id.endswith('_UP')else'down']if'PIN_'in id else['point'],'localArtReviewed':False}
   if id=='SPR_WHITE_POINT':binding.update({'functionalGeometryRecipe':en['functionalGeometryRecipe'],'derivedFrom':en['derivedFrom']})
   bindings.append(binding);continue
  if id=='SMALLMAP_DATA_MARKERS':
   sf=P+'/markers/map-data-markers.svg';svg='<svg xmlns="http://www.w3.org/2000/svg" width="320" height="160" viewBox="0 0 320 160"><g fill="none" stroke="#d7b66d" stroke-width="3"><path d="M16 32V16H40 M280 16H304V40 M16 120V144H40 M280 144H304V120"/></g><g fill="#65b89b"><rect x="45" y="60" width="2" height="2"/><rect x="65" y="70" width="4" height="2"/><rect x="90" y="60" width="22" height="14"/><rect x="120" y="60" width="22" height="14" fill="#db6553"/><rect x="150" y="60" width="22" height="14" fill="#65aeda"/></g></svg>'
   (R/sf).write_text(svg,encoding='utf8');bindings.append({'id':id,'geometryFile':sf,'sha256':wp.sha(R/sf),'states':['viewport-corner4','vehicle-dot1or2logicalPixels','company-industry-legend-palette','dynamic-town-industry-text'],'operation':'authored scalable UI geometry based on source GfxFillRect/SetPixel/DrawString; colours follow existing jade/red/blue palette; actual map data and label text separate','localArtReviewed':False});continue
  f='assets/common/reference-paper.png';bindings.append({'id':id,'layers':[ref(f)],'states':['dynamic-text','company-colour-tag','selected-label'],'operation':'reuse native paper panel with existing independent NotoSansSC font; world/map sign labels are dynamic text and company flag tag, no name baked into art; scale/pivot depend on actual label rectangle','fontFile':'assets/fonts/NotoSansSC-Variable.ttf','localArtReviewed':False})
 return entries,bindings
def gallery(curs,overlay,components,clips,bindings):
 allart=curs+overlay+components;groups={'指针组件':components,'静态工具鼠标':[a for a in curs if a.get('category')=='static-cursor'],'选地／覆盖描边':[a for a in overlay if a.get('sourceRequirementId','').startswith('selection-normal')],'半格／坡向描边':[a for a in overlay if a.get('sourceRequirementId','').startswith('selection-half')],'自动轨道114种描边':[a for a in overlay if a.get('sourceRequirementId','').startswith('selection-autorail')]}
 markerData=[]
 for b in bindings[-10:]:
  fs=([b['file']]if b.get('file')else[])+[x['file']for x in b.get('layers',[])]+([b['geometryFile']]if b.get('geometryFile')else[])
  for f in fs:markerData.append({'id':b['id']+' / '+Path(f).stem,'image':f})
 groups['公司、状态与地图小件（实际复用）']=markerData
 html='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>工具鼠标与地图覆盖层验收</title><style>body{margin:0;background:#183c32;color:#f4ead0;font:15px/1.5 system-ui,"Microsoft YaHei"}header,main{max-width:1460px;margin:auto;padding:22px}a{color:#e2c98a}h1{font-size:26px}select,button{padding:8px 12px;background:#f0e9d3;color:#285842;border:1px solid #bd9a58;border-radius:8px;font:inherit}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}.card{margin:0;border:1px solid #617a5c;border-radius:12px;overflow:hidden;background:#234f41}.card div{height:150px;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#f5f1df 0% 25%,#d6dfcf 0% 50%) 50%/24px 24px}.card img{max-width:96%;max-height:146px;object-fit:contain}.card p{padding:8px;font-size:12px;overflow-wrap:anywhere}#stage{height:260px;background:#e3e5d8;border-radius:12px;position:relative;overflow:hidden;cursor:none}#follow{position:absolute;pointer-events:none;max-width:none}#cross{position:absolute;pointer-events:none;width:24px;height:24px;font-size:0}#cross:before{content:"";position:absolute;left:0;top:11px;width:24px;height:2px;background:#b33}#cross:after{content:"";position:absolute;left:11px;top:0;width:2px;height:24px;background:#b33}#phase{display:flex;gap:16px;align-items:center;padding:12px;flex-wrap:wrap}#anim{width:96px;height:96px;background:#dce1ce}.note{color:#c4d5b7}</style><header><h1>工具鼠标与地图覆盖层 · 美术验收</h1><p>72个静态工具鼠标、5组源动画、19坡选地、12半格和114自动轨道状态。鼠标96px，所有帧同一实测尖端热点。覆盖层为精确SVG几何＋原生手绘玉珠细节，未宣称新原画。</p><p><a href="../../index.html">整套入口</a>　<a href="../../docs/POINTER_OVERLAY_REQUIREMENTS.json">源码需求</a>　<a href="../../docs/POINTER_OVERLAY_BINDINGS.json">逐项图片／复用合同</a></p><label>选择工具鼠标 <select id="cursor"></select></label><div id="stage"><img id="follow"><span id="cross">＋</span></div><p class="note">移动鼠标查看96px素材的实际热点（红色十字）。这是图片与定位预览，不含Unity交互逻辑。</p><div id="phase"><select id="clip"></select><img id="anim"><span id="timing"></span></div></header><main>'
 for title,aa in groups.items():
  html+='<h2>'+title+'</h2><div class="grid">'
  for a in aa:
   url='../../'+a['image'];html+='<figure class="card"><div><img loading="lazy" src="'+url+'" alt="'+a['id']+'"></div><p>'+a['id']+'</p></figure>'
  html+='</div>'
 html+='</main><script>const CURSORS='+json.dumps([a for a in curs if a.get('category')=='static-cursor'],ensure_ascii=False)+';const CLIPS='+json.dumps(clips,ensure_ascii=False)+';const $=id=>document.getElementById(id);CURSORS.forEach(a=>{let o=new Option(a.id,a.id);$("cursor").add(o)});CLIPS.forEach(a=>$("clip").add(new Option(a.id,a.id)));$("cursor").value="SPR_CURSOR_MOUSE";let current=CURSORS[0],clip=CLIPS[0],start=performance.now();function tool(){current=CURSORS.find(a=>a.id==$("cursor").value)||CURSORS[0];$("follow").src="../../"+current.image}$("cursor").onchange=tool;$("stage").onmousemove=e=>{let r=e.currentTarget.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;$("follow").style.left=(x-current.hotspotPx[0])+"px";$("follow").style.top=(y-current.hotspotPx[1])+"px";$("cross").style.left=(x-12)+"px";$("cross").style.top=(y-12)+"px"};$("clip").onchange=()=>{clip=CLIPS.find(a=>a.id==$("clip").value);start=performance.now()};function tick(now){let ds=clip.durationsMs,total=ds.reduce((a,b)=>a+b,0),v=(now-start)%total,i=0;while(i<ds.length-1&&v>=ds[i])v-=ds[i++];if($("anim").getAttribute("src")!=="../../"+clip.frames[i])$("anim").src="../../"+clip.frames[i];$("timing").textContent=clip.sourceTicks.join("/")+" 源ticks ×27ms；热点 "+current.hotspotPx;requestAnimationFrame(tick)}tool();requestAnimationFrame(tick);window.POINTER_ART={cursors:CURSORS,clips:CLIPS};</script>'
 (PRE/'index.html').write_text(html,encoding='utf8')
 for name,aa in [('pointer-components',components),('pointer-static',[a for a in curs if a.get('category')=='static-cursor']),('pointer-animation-frames',[a for a in curs if a.get('category')=='animated-cursor-frame']),('selection-normal',[a for a in overlay if a.get('paletteRole')=='neutral'and a.get('sourceRequirementId','').startswith('selection-normal')]),('selection-half',[a for a in overlay if a.get('paletteRole')=='neutral'and a.get('sourceRequirementId','').startswith('selection-half')])]:
  contact(aa,name,6 if name=='pointer-static'else 4)
 auto=[a for a in overlay if a.get('sourceRequirementId','').startswith('selection-autorail')and a['paletteRole']==('invalid-red'if a.get('invalidBySourceTable')else'neutral')]
 for i in range(3):contact(auto[i*38:(i+1)*38],'selection-autorail-'+str(i+1),6)
 palette=[a for a in overlay if a.get('sourceRequirementId')in ['selection-normal-slope-0','selection-half-flat-0']];contact(palette,'selection-palette-states',5)
 overrides=[a for a in overlay if a.get('sourceRequirementId','').startswith('selection-autorail-0-')and a.get('paletteRole')=='invalid-red'];contact(overrides,'selection-autorail-forced-red',6)
def contact(aa,name,cols):
 if not aa:return
 cell=(240,190);im=Image.new('RGB',(cols*cell[0],math.ceil(len(aa)/cols)*cell[1]),'#20463a');d=ImageDraw.Draw(im)
 for i,a in enumerate(aa):
  pic=Image.open(R/a['image']).convert('RGBA');pic.thumbnail((220,145));x=i%cols*240;y=i//cols*190;bg=Image.new('RGBA',(240,150),'#eee9d8'if i%2==0 else'#214439');bg.alpha_composite(pic,((240-pic.width)//2,(150-pic.height)//2));im.paste(bg.convert('RGB'),(x,y));d.text((x+5,y+151),a['id'][:35],font=t.font(12),fill='#ede5cc')
 im.save(PRE/(name+'.jpg'),quality=95)
def main():
 inv=load(R/'docs/POINTER_OVERLAY_REQUIREMENTS.json');comp,components=extract();ca,cb,clips=cursors(inv,comp);oa,ob=overlays(inv,comp);ea,eb=extras(inv,comp);bindings=cb+ob+eb;wp.writej(R/'docs/POINTER_OVERLAY_BINDINGS.json',{'schema':'pointer-overlay-bindings.v1','createdAt':wp.now(),'bindings':bindings,'sourceTickMs':27,'sourceTickEvidence':'reference/OpenTTD/src/gfx_type.h417','nativeKit':'source-art/pointer-overlay-kit.png','actualModel':None,'actualQuality':None,'geometryClaim':'SVG/selection shapes are authored geometry plus actual native gem details; no native4K/newpainting claim','userArtAcceptance':'pending','unityValidated':False});wp.writej(R/P/'markers/manifest.json',{'assets':ea,'schema':'interaction-markers.v1','unityValidated':False});gallery(ca,oa,components,clips,bindings);print(json.dumps({'nativeComponents':len(components),'cursorPNGs':len(ca),'overlayPNGs':len(oa),'markerPNGs':len(ea),'bindingRows':len(bindings),'fixedCursorHotspot':cb[0]['hotspotPx'],'preview':'previews/pointers/index.html'},ensure_ascii=False))
if __name__=='__main__':main()

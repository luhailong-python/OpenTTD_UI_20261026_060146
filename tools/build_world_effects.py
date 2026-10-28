"""Package actual native painted FX keys and disaster props; all derived phases declared."""
from pathlib import Path
from PIL import Image,ImageOps,ImageFilter,ImageDraw,ImageFont
import numpy as np,json,hashlib,datetime,math
from scipy.ndimage import label
R=Path(__file__).resolve().parents[1];O=R/'assets/world/effects';O.mkdir(parents=True,exist_ok=True);PRE=R/'previews/world/effects';PRE.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def ref(p):return{'file':p.relative_to(R).as_posix(),'sha256':sha(p),'record':p.relative_to(R).as_posix()+'.generation.json'}
def native_cells(name,cols,rows,canvas=512):
 src=R/'source-art/world'/f'{name}.png';im=Image.open(src).convert('RGBA');cells=[]
 for i in range(cols*rows):
  c=i%cols;r=i//cols;box=[round(c*im.width/cols),round(r*im.height/rows),round((c+1)*im.width/cols),round((r+1)*im.height/rows)];cell=im.crop(box)
  # Only non-art cell-edge glow is feathered two native pixels, retaining all
  # disconnected sparks and droplets in the cell; no component pruning for FX.
  arr=np.array(cell);a=arr[:,:,3].astype(float);yy,xx=np.indices(a.shape);dist=np.minimum.reduce([xx,yy,cell.width-1-xx,cell.height-1-yy]);border=int(((a>=64)&(dist<2)).sum());arr[:,:,3]=np.round(a*np.clip(dist/2,0,1)).astype('uint8');cell=Image.fromarray(arr)
  factor=min(1,(canvas-16)/max(cell.size));cell=cell.resize((round(cell.width*factor),round(cell.height*factor)),Image.Resampling.LANCZOS)if factor<1 else cell
  out=Image.new('RGBA',(canvas,canvas));paste=((canvas-cell.width)//2,(canvas-cell.height)//2);out.alpha_composite(cell,paste)
  cells.append((out,{'derivedFrom':ref(src),'nativeSourceRectXYXY':box,'scale':factor,'paddingLeftTop':list(paste),'nativeCellEdgeSolidPixelsFeathered':border,'operation':'equal atlas cell crop, retain all particles;2px exterior glow feather; downscale only ifneeded; transparent padding, not new AI art'}))
 return cells
def blend(a,b,t):
 aa=np.array(a).astype(float)/255;bb=np.array(b).astype(float)/255;al=aa[:,:,3:4]*(1-t)+bb[:,:,3:4]*t;rgb=aa[:,:,:3]*aa[:,:,3:4]*(1-t)+bb[:,:,:3]*bb[:,:,3:4]*t;rgb=np.divide(rgb,al,out=np.zeros_like(rgb),where=al>1e-7)
 return Image.fromarray(np.clip(np.concatenate([rgb,al],2)*255,0,255).astype('uint8'))
def publish(folder,frames,sources,fps=12,loop=False,operation='painted keys; explicit keyframe interpolation'):
 d=O/folder;d.mkdir(parents=True,exist_ok=True);entries=[]
 for i,(im,info)in enumerate(zip(frames,sources)):
  p=d/f'{i:02}.png';im.save(p);e={'file':p.relative_to(R).as_posix(),'sha256':sha(p),'canvas':list(im.size),'pivot':[.5,.5],'frame':i,'durationMs':round(1000/fps),'operation':operation,'sources':info if isinstance(info,list)else[info],'nativeModelGeneration':False,'unityVerified':False};entries.append(e)
  save(Path(str(p)+'.derivation.json'),e)
 mm={'id':folder,'frames':entries,'fpsSuggestion':fps,'loop':loop,'timingStatus':'art preview recommendation; source gameplay tick adapter remains next stage','operation':operation,'unityVerified':False};save(d/'manifest.json',mm)
 # GIF is a composited art preview, not a video-model output.
 gif=[]
 for frame in frames:
  bg=Image.new('RGBA',frame.size,'#263F39');bg.alpha_composite(frame);bg=bg.convert('RGB');bg.thumbnail((256,256));gif.append(bg)
 gif[0].save(PRE/(folder.replace('/','-')+'.gif'),save_all=True,append_images=gif[1:],duration=round(1000/fps),loop=0 if loop else 1,disposal=2)
 return mm
smoke=native_cells('fx-smoke-keys',4,4);explosion=native_cells('fx-explosion-keys',4,4);mixed=native_cells('fx-spark-bubble-fire',4,4)
def interpolated(keys,count):
 imgs=[];sources=[]
 for i in range(count):
  x=i*(len(keys)-1)/max(count-1,1);a=int(x);b=min(len(keys)-1,a+1);t=x-a;imgs.append(blend(keys[a][0],keys[b][0],t));sources.append([dict(keys[a][1],keyWeight=1-t),dict(keys[b][1],keyWeight=t)])
 return imgs,sources
effects=[]
specs=[(0,'EV_CHIMNEY_SMOKE','chimney-smoke',smoke[:4],8),(1,'EV_STEAM_SMOKE','steam-smoke',smoke[4:8],5),(2,'EV_DIESEL_SMOKE','diesel-smoke',smoke[8:12],6),(3,'EV_ELECTRIC_SPARK','electric-spark',mixed[:4],6),(4,'EV_CRASH_SMOKE','crash-smoke',smoke[12:16],5),(5,'EV_EXPLOSION_LARGE','explosion-large',explosion,16),(6,'EV_BREAKDOWN_SMOKE','breakdown-smoke',smoke[12:16],4),(7,'EV_EXPLOSION_SMALL','explosion-small',explosion,12)]
for id,code,name,keys,count in specs:
 imgs,sources=interpolated(keys,count)
 if id==7:
  small=[]
  for im in imgs:
   canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(im.resize((256,256),Image.Resampling.LANCZOS),(128,128));small.append(canvas)
  imgs=small
 mm=publish(name,imgs,sources,12,id==6,operation='native painted lifetime keys + premultiplied-alpha interpolation to source frame count'+(';50percent scale for small explosion'if id==7 else''));effects.append({'sourceId':id,'sourceEnum':code,'sourceFile':'src/effectvehicle_func.h','sourceLine':17+id,'manifest':(O/name/'manifest.json').relative_to(R).as_posix(),'sourceSpriteCount':count,'deliveredFrameCount':count,'independentNativeKeys':len(keys),'unityVerified':False})
dozer=native_cells('fx-bulldozer',2,2);dirs=['NE','SE','SW','NW'];dimgs=[ImageOps.mirror(dozer[3][0]),dozer[1][0],dozer[2][0],dozer[3][0]];dsrc=[dict(dozer[3][1],mirrorHorizontal=True),dozer[1][1],dozer[2][1],dozer[3][1]]
mm=publish('bulldozer-directions',dimgs,dsrc,4,False,operation='painted machine facings;NE is explicitly mirrored fromNW; raw top-left duplicateSE unused, not four native facings')
mm['directionOrder']=dirs;mm['bodyMotion']='source movement sequence translates static prop; no invented track-wheel animation';save(O/'bulldozer-directions/manifest.json',mm);effects.append({'sourceId':8,'sourceEnum':'EV_BULLDOZER','sourceFile':'src/effectvehicle_func.h','sourceLine':25,'manifest':'assets/world/effects/bulldozer-directions/manifest.json','sourceSpriteCount':4,'deliveredDirections':dirs,'nativeFacingCount':3,'derivedFacingCount':1})
bubble={}
for name,keys,count in [('bubble-generation',mixed[4:8],4),('bubble-float',mixed[5:8],3),('bubble-burst',mixed[8:12],4)]:
 imgs,sources=interpolated(keys,count);publish(name,imgs,sources,10,name=='bubble-float');bubble[name]=(O/name/'manifest.json').relative_to(R).as_posix()
absimgs=[];abssrc=[]
for i in range(5):
 factor=1-i*.18;size=round(512*factor);im=Image.new('RGBA',(512,512));im.alpha_composite(mixed[6][0].resize((size,size),Image.Resampling.LANCZOS),((512-size)//2,(512-size)//2));im.putalpha(im.getchannel('A').point(lambda x:round(x*(1-i*.15))));absimgs.append(im);abssrc.append(dict(mixed[6][1],deterministicScale=factor,alphaMultiplier=1-i*.15))
publish('bubble-absorb',absimgs,abssrc,10,False,operation='painted bubble; deterministic scale and alpha absorption progression');bubble['bubble-absorb']='assets/world/effects/bubble-absorb/manifest.json'
effects.append({'sourceId':9,'sourceEnum':'EV_BUBBLE','sourceFile':'src/effectvehicle_func.h','sourceLine':26,'manifests':bubble,'sourceImageMapping':{'generate0-3':'bubble-generation','float0-2':'bubble-float','burst7-9':'bubble-burst','absorb10-14':'bubble-absorb'},'movement':'4 world drift directions are later source/game translation, not raster body rotation'})
for id,code in [(10,'EV_BREAKDOWN_SMOKE_AIRCRAFT'),(11,'EV_COPPER_MINE_SMOKE')]:effects.append({'sourceId':id,'sourceEnum':code,'sourceFile':'src/effectvehicle_func.h','sourceLine':17+id,'manifest':'assets/world/effects/crash-smoke/manifest.json','sharedArt':'source effect_procs uses the exact same SmokeInit/SmokeTick asEV_CRASH_SMOKE','sourceSpriteCount':5,'deliveredFrameCount':5})
publish('furnace-flame',[x[0]for x in mixed[12:16]],[x[1]for x in mixed[12:16]],10,True,operation='four independently painted flame keys; optional industrial ambient art, not an extra source EffectVehicleType')
save(R/'docs/EFFECT_RUNTIME_MANIFEST.json',{'referenceCommit':'cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8','effects':effects,'sourceTypeCount':12,'optionalAmbient':['furnace-flame'],'nativeSourceAtlases':['fx-smoke-keys','fx-explosion-keys','fx-spark-bubble-fire','fx-bulldozer'],'videoModelUsed':False,'unityVerified':False})
# Source disaster subtypes include six shadow entities and one rotor, rather
# than15 unrelated monster bodies. Exact mapping is retained below.
props=native_cells('disaster-air-props',3,3);subs=native_cells('disaster-submarines',4,2)
from repair_disaster_native_bounds import isolated_body
fullPropSheet=Image.open(R/'source-art/world/disaster-air-props.png').convert('RGBA')
for i in [1,5,6,8]:
 body,info=isolated_body(fullPropSheet,i);props[i]=(body,{'derivedFrom':ref(R/'source-art/world/disaster-air-props.png'),**info})
names=['zeppelin','zeppelin-crashing','zeppelin-wreck','ufo-small','ufo-small-dark','ufo-big','combat-airplane','combat-helicopter','ufo-destroyer']
propman={}
for i in [4,7]:
 # Two solid-body atlas cells contain proven neighbouring sprite fragments.
 # Keep all pixels of the body component; particle effects above are untouched.
 ar=np.asarray(props[i][0]).copy();lab,num=label(ar[...,3]>0,structure=np.ones((3,3)));counts=np.bincount(lab.ravel());counts[0]=0;keep=lab==counts.argmax();removed=int(((ar[...,3]>0)&~keep).sum());ar[~keep]=0;ar[ar[...,3]==0,:3]=0;props[i]=(Image.fromarray(ar),{**props[i][1],'solidBodyAlphaOwnership':'largest8-connected Alpha component; neighbouring-cell solid-body fragments removed; particle effects excluded','removedVisiblePixels':removed})
for i,name in enumerate(names):
 mm=publish('disasters/'+name,[props[i][0]],[props[i][1]],1,False,operation='actual isolated painted disaster prop, native crop/padding');propman[name]=(O/'disasters'/name/'manifest.json').relative_to(R).as_posix()
for name,subset in [('submarine-small',subs[:4]),('submarine-big',subs[4:])]:
 mm=publish('disasters/'+name,[x[0]for x in subset],[x[1]for x in subset],1,False,operation='four actual native painted diagonal body facings;source shares each one for twoDirection enum values');mm['directionOrder']=dirs;mm['sourceDirectionToFrame']=[0,0,1,1,2,2,3,3];save(O/'disasters'/name/'manifest.json',mm);propman[name]=(O/'disasters'/name/'manifest.json').relative_to(R).as_posix()
for name in ['zeppelin','ufo-small','ufo-big','combat-airplane','combat-helicopter','ufo-destroyer']:
 index=names.index(name);body=props[index][0];flat=body.resize((512,200),Image.Resampling.LANCZOS);shadow=Image.new('RGBA',(512,512));sil=Image.new('RGBA',flat.size,(27,43,38,0));sil.putalpha(flat.getchannel('A').point(lambda a:round(a*.30)));shadow.alpha_composite(sil,(0,156));publish('disasters/'+name+'-shadow',[shadow],[dict(props[index][1],silhouetteTint=[27,43,38],alphaMultiplier=.30,verticalScale=200/512)],1,False,operation='shadow derived from actual body Alpha, vertical projection and30percent opacity');propman[name+'-shadow']=(O/'disasters'/(name+'-shadow')/'manifest.json').relative_to(R).as_posix()
codes=['ST_ZEPPELINER','ST_ZEPPELINER_SHADOW','ST_SMALL_UFO','ST_SMALL_UFO_SHADOW','ST_AIRPLANE','ST_AIRPLANE_SHADOW','ST_HELICOPTER','ST_HELICOPTER_SHADOW','ST_HELICOPTER_ROTORS','ST_BIG_UFO','ST_BIG_UFO_SHADOW','ST_BIG_UFO_DESTROYER','ST_BIG_UFO_DESTROYER_SHADOW','ST_SMALL_SUBMARINE','ST_BIG_SUBMARINE']
maps=['zeppelin','zeppelin-shadow','ufo-small','ufo-small-shadow','combat-airplane','combat-airplane-shadow','combat-helicopter','combat-helicopter-shadow','rotor','ufo-big','ufo-big-shadow','ufo-destroyer','ufo-destroyer-shadow','submarine-small','submarine-big']
records=[]
for i,(code,name)in enumerate(zip(codes,maps)):
 record={'sourceId':i,'sourceEnum':code,'sourceFile':'src/disaster_vehicle.h','sourceLine':18+i,'manifest':propman.get(name,'assets/world/vehicles/rotor/manifest.json'),'unityVerified':False}
 if i==0:record['states']={'intact':propman['zeppelin'],'crashing':propman['zeppelin-crashing'],'wreck':propman['zeppelin-wreck']}
 if i==2:record['states']={'lit':propman['ufo-small'],'dark':propman['ufo-small-dark']}
 if i in[4,6,11]:record['firingOverlay']='assets/world/effects/electric-spark/manifest.json';record['impactOverlay']='assets/world/effects/explosion-large/manifest.json'
 records.append(record)
save(R/'docs/DISASTER_RUNTIME_MANIFEST.json',{'sourceSubtypeCount':15,'subtypes':records,'sourceSpriteArrays':'src/disaster_vehicle.cpp:92-119','eightDirectionsNotNeeded':'source airship/UFO/combat air/rotor arrays reuse one original sprite for all8 directions; submarines use4 diagonal sprites','newIndependentNativeProps':17,'shadowsAreDerived':True,'unityVerified':False})
print('12effecttypes +15disastersubtypes; nativekeys and explicit derivatives; noUnity/runtimecode')

"""Formal tree sprites and seven static lifecycle states, from painted atlases.
No generated detail is fabricated: shrinking, palette transform and shared dying parts are declared.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import numpy as np,hashlib,json,datetime
from scipy import ndimage
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
specs={
 'temperate':{'cols':4,'ids':list(range(12)),'names':['oak','beech','silver-birch','maple','pine','fir','spruce','poplar','willow','chestnut','elm','cherry']},
 'arctic':{'cols':4,'ids':list(range(12,20))+[None]*4,'names':['dark-spruce','blue-spruce','snow-fir','larch','snow-pine','arctic-birch','mountain-rowan','alpine-broadleaf','young-sapling','young-conifer','bare-dead-tree','dead-stump']},
 'tropical':{'cols':4,'ids':[20,21,22,23,24,25,26,28,29,30,27,31],'names':['coconut-palm','date-palm','oil-palm','fan-palm','banyan','rubber','mahogany','teak','acacia','baobab','saguaro-cactus','rainforest-giant']},
 'toyland':{'cols':3,'ids':list(range(32,41)),'names':['lollipop','candy-cane','cotton-candy','gumdrop','spring-tree','jelly-cone','cookie-tree','caramel-tree','balloon-tree']}
}
assets=[];masters={};extras={};native_sources=[]
for climate,spec in specs.items():
 src=R/'source-art/world'/('trees-'+climate+'.png');im=Image.open(src).convert('RGBA');a=np.array(im)[:,:,3]
 labels,n=ndimage.label(a>32);sizes=np.bincount(labels.ravel());large=np.where(sizes>5000)[0];large=large[large!=0];seeds=np.where(np.isin(labels,large),labels,0)
 adjustments=[]
 # Palm root and next-row mahogany crown touch at y361. An authored ownership cut at the transparent cell boundary is needed.
 if climate=='tropical':
  for lab in large:
   yy,xx=np.where(seeds==lab)
   if yy.max()-yy.min()>500:
    new_id=int(labels.max()+1);region=(seeds==lab)&(np.indices(a.shape)[0]>=362);seeds[region]=new_id;adjustments.append({'originalComponent':int(lab),'splitAxis':'y','splitAt':362,'reason':'row1 oil-palm ground and row2 mahogany foliage tangent; ownership cut, not procedural repaint'})
  large=np.unique(seeds);large=large[large!=0]
 assert len(large)==len(spec['ids']),(climate,len(large))
 nearest=ndimage.distance_transform_edt(seeds==0,return_distances=False,return_indices=True);owned=seeds[tuple(nearest)]
 obs=[]
 for lab in large:
  yy,xx=np.where(seeds==lab);obs.append([int(lab),float(xx.mean()),float(yy.mean())])
 obs.sort(key=lambda o:o[2]);cols=spec['cols'];obs=sum([sorted(obs[r*cols:(r+1)*cols],key=lambda o:o[1])for r in range(3)],[])
 for cell,((lab,cx,cy),idx,name) in enumerate(zip(obs,spec['ids'],spec['names'])):
  alpha=np.where((owned==lab)&(a>=8),a,0).astype('uint8');alpha[alpha>=240]=255
  part=im.copy();part.putalpha(Image.fromarray(alpha));box=part.getbbox();part=part.crop(box)
  # Root anchor comes from substantial bottom contact, not the canopy bbox center.
  aa=np.array(part)[:,:,3];band=max(4,round(part.height*.04));yy,xx=np.where(aa[-band:,:]>64);rootx=float(np.median(xx))if len(xx)else part.width/2
  rooty=part.height
  maxextent=max(rootx,part.width-rootx);scale=min(1,120/maxextent,320/part.height)
  target=(round(part.width*scale),round(part.height*scale));part=part.resize(target,Image.Resampling.LANCZOS)
  off=(round(128-rootx*scale),352-target[1]);out=Image.new('RGBA',(256,384));out.alpha_composite(part,off)
  ident='tree-'+str(idx).zfill(2)if idx is not None else'tree-lifecycle-'+name
  p=R/'assets/world/vegetation'/('mature'if idx is not None else'lifecycle')/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);out.save(p)
  en={'id':ident,'image':p.relative_to(R).as_posix(),'width':256,'height':384,'anchorPx':[128,352],'pivotUnity':[.5,1/12],'anchorMeaning':'plant root front contact; x estimated from opaque bottom contact band, not canopy centre','category':'vegetation'if idx is not None else'vegetation-lifecycle','sha256':sha(p),'climate':climate,'artSpecies':name,'sourceTreeType':idx,'sourceCell':cell,'sourceCropXYXY':list(box),'sourceAnchorInCrop':[rootx,rooty],'nativeCropSize':list(aa.shape[::-1]),'uniformScale':scale,'pasteXY':list(off),'operation':'component ownership crop with all attached/disconnected meaningful fragments; alpha below8 removed and alpha>=240 normalized opaque; fixed-root proportional downscale and transparent padding; not new generation','derivedFrom':{'file':src.relative_to(R).as_posix(),'sha256':sha(src),'record':src.relative_to(R).as_posix()+'.generation.json'},'status':'needs-visual-review','nativeUpscale':False,'unityValidated':False,'sourceRequirementIds':['tree-'+str(idx).zfill(2)]if idx is not None else[],'speciesNameEvidence':'botanical/whimsical identity is new art design; source defines numeric tree types/climates, not these species names','ownershipAdjustments':adjustments}
  savej(Path(str(p)+'.derivation.json'),en);assets.append(en)
  if idx is not None:masters[idx]=en
  else:extras[name]=en
 native_sources.append({'file':src.relative_to(R).as_posix(),'sha256':sha(src),'size':list(im.size),'nativeObjects':len(spec['ids']),'ownershipAdjustments':adjustments})
lifecycle=readj(R/'assets/world/vegetation/lifecycle/manifest.json')['assets'];assets+=lifecycle;lifeby={e['id'].removeprefix('tree-lifecycle-'):e for e in lifecycle}
state_names=['growing-1','growing-2','growing-3','grown','dying-1','dying-2','dead'];coverage=[]
def resized_root(image,scale):
 im=Image.open(R/image).convert('RGBA');w,h=round(im.width*scale),round(im.height*scale);im=im.resize((w,h),Image.Resampling.LANCZOS);out=Image.new('RGBA',(256,384));out.alpha_composite(im,(round(128-128*scale),round(352-352*scale)));return out
for idx,main in sorted(masters.items()):
 states=[];mature=Image.open(R/main['image']).convert('RGBA');mb=mature.getbbox();mh=mb[3]-mb[1];mw=mb[2]-mb[0]
 for stage,name in enumerate(state_names):
  if stage==3:states.append({'stage':stage,'name':name,'artId':main['id'],'image':main['image']});continue
  sources=[{'file':main['image'],'sha256':main['sha256'],'record':main['image']+'.derivation.json'}];details={}
  if stage<3:
   scale=[.28,.50,.76][stage];out=resized_root(main['image'],scale);details={'matureScale':scale,'method':'same painted phenotype shrunk; not separate sapling anatomy or native detail'}
  elif stage==4:
   rgb=mature.convert('RGB');gray=ImageOps.grayscale(rgb);dry=ImageOps.colorize(gray,(62,42,26),(223,186,119)).convert('RGB');rgb=Image.blend(rgb,dry,.68);out=rgb.convert('RGBA');out.putalpha(mature.getchannel('A'));details={'method':'desaturated warm dry palette transform of species art','dryPaletteBlend':.68}
  elif stage==5 and idx in [33,35,36,38,39,40]:
   gray=ImageOps.grayscale(mature.convert('RGB'));dry=ImageOps.colorize(gray,(62,42,26),(204,172,114)).convert('RGBA');dry.putalpha(mature.getchannel('A'))
   # Mechanical/cookie/balloon identity must not suddenly grow lollipop discs when dying.
   sx=.90;sy=.70;ww=round(256*sx);hh=round(384*sy);dry=dry.resize((ww,hh),Image.Resampling.LANCZOS);out=Image.new('RGBA',(256,384));out.alpha_composite(dry,(round(128-128*sx),round(352-352*sy)))
   details={'method':'same toy phenotype desaturated and visibly shrivelled by declared 2D downscale; no other candy species spawned','scaleXY':[sx,sy],'newNativeDeathDrawing':False}
  else:
   if idx==27:shared=lifeby['dying-cactus'if stage==5 else'dead-cactus']
   elif idx in [20,21,22,23]:shared=lifeby['dying-palm'if stage==5 else'dead-palm']
   elif idx==30:shared=lifeby['dying-baobab']if stage==5 else extras['dead-stump']
   elif idx==34:shared=lifeby['dying-cotton'if stage==5 else'dead-cotton']
   elif idx in [32,37]:shared=lifeby['dying-candy'if stage==5 else'dead-candy']
   elif idx>=32:shared=extras['dead-stump']
   else:shared=extras['bare-dead-tree'if stage==5 else'dead-stump']
   si=Image.open(R/shared['image']).convert('RGBA');sb=si.getbbox();sh=sb[3]-sb[1];sw=sb[2]-sb[0]
   desired_h=mh*.87 if stage==5 else min(100,mh*.30);desired_w=max(mw*.82,100)if stage==5 else min(110,mw*.60)
   scale=min(1,desired_h/sh,desired_w/sw);out=resized_root(shared['image'],scale);sources.append({'file':shared['image'],'sha256':shared['sha256'],'record':shared['image']+'.derivation.json'})
   details={'method':'shared explicitly painted climate/family death-state prop','sharedArtId':shared['id'],'sharedScale':scale,'notSpeciesSpecificNativeDeathDrawing':True}
  p=R/'assets/world/vegetation/states'/main['id']/(str(stage)+'-'+name+'.png');p.parent.mkdir(parents=True,exist_ok=True);out.save(p)
  e={'id':main['id']+'-'+name,'image':p.relative_to(R).as_posix(),'width':256,'height':384,'anchorPx':[128,352],'pivotUnity':[.5,1/12],'anchorMeaning':'same fixed plant root reference across all seven states','category':'vegetation-state','sha256':sha(p),'climate':main['climate'],'artSpecies':main['artSpecies'],'sourceTreeType':idx,'sourceGrowthStage':stage,'operation':'declared static growth/death state derivative; scale/palette/shared painted parts only, no new AI generation','derivedFrom':sources,'details':details,'status':'needs-state-visual-review','nativeUpscale':False,'unityValidated':False,'sourceRequirementIds':[main['id']]}
  savej(Path(str(p)+'.derivation.json'),e);assets.append(e);states.append({'stage':stage,'name':name,'artId':e['id'],'image':e['image']})
 main['states']=states;coverage.append({'requirementId':main['id'],'sourceTreeType':idx,'climate':main['climate'],'artSpecies':main['artSpecies'],'artIds':[s['artId']for s in states],'files':[s['image']for s in states],'states':states,'status':'seven-art-states-produced','nativeSpeciesArtworkCount':1,'nativeStagePaintingsClaim':False,'sourceEvidence':['src/tree_map.h:25-45','src/tree_map.h:65-73','src/table/tree_land.h:13-21']})
layouts=[[(9,3),(1,8),(0,0),(8,9)],[(4,4),(9,1),(6,9),(0,9)],[(9,1),(0,9),(6,6),(3,0)],[(3,9),(8,2),(9,9),(1,5)]]
m={'schemaVersion':1,'project':'云途万里（暂名）','sourceCommit':'cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8','counts':{'sourceTreeTypes':41,'sourceGrowthStages':7,'typeStageMappings':287,'formalPNGs':len(assets),'nativeMatureTreePaintings':41,'nativeSharedLifecycleProps':13,'acceptedNativeAtlases':5,'nativePaintedObjects':54},'assets':assets,'animations':[],'coverageMappings':coverage,'nativeSources':native_sources+[{'file':'source-art/world/tree-lifecycle-special-with-backdrop.png','sha256':sha(R/'source-art/world/tree-lifecycle-special-with-backdrop.png'),'nativeObjects':9}],'sourceLayouts':{'coordinatesUnits':'source tile16x16','table':layouts,'formalGround256x128Offsets':[[[128+(y-x)*8,(x+y)*4]for x,y in row]for row in layouts],'source':'src/table/tree_land.h:16-21','layoutSpriteRandomization':'source uses four placement sprites per variant; our species phenotype is one native painting; future seeded placement or mild hue changes may derive variety, not claimed as four native facings'},'unity':{'type':'Sprite/Single','pixelsPerUnit':256,'filterMode':'Bilinear','wrapMode':'Clamp','sRGB':True,'alphaIsTransparency':True,'mipMaps':'recommend off for pixel-aligned2D; evaluate actual camera','pivotUnity':[.5,1/12],'canvas':[256,384],'validated':False},'limitations':['41种为原生Numeric TreeType的道家风格视觉重设计，植物物种名是美术设计假设，并非源码声明的真实植物学名字。','7态为静态状态；前三阶段按同种末态缩小，枯亡阶段使用明确记录的气候/家族共享原画；不是287张独立原生树画。','Source tree27 is cactus. Tropical atlas cell10 is deliberately mapped to27; later cells are nonsequential IDs to preserve this biome role.','不是循环风动或真实植物生长动画；时间与转换由后续游戏逻辑控制。','Unity遮挡/地形高差/碰撞/实际缩放均待后续接入验证。']}
savej(R/'assets/world/vegetation/manifest.json',m)
font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16)
for climate,spec in specs.items():
 entries=[masters[i]for i in spec['ids']if i is not None];cols=4 if climate!='toyland'else 3;rows=(len(entries)+cols-1)//cols;panel=Image.new('RGB',(cols*256,rows*416),'#e4dfd1');d=ImageDraw.Draw(panel)
 for i,e in enumerate(entries):
  bg=Image.new('RGBA',(256,384),'#e4dfd1'if i%2==0 else'#244139');bg.alpha_composite(Image.open(R/e['image']).convert('RGBA'));x=(i%cols)*256;y=(i//cols)*416;panel.paste(bg.convert('RGB'),(x,y));d.text((x+4,y+388),e['id']+' '+e['artSpecies'],font=font,fill='#285443')
 panel.save(R/'previews/world'/('vegetation-'+climate+'.jpg'),quality=94)
# Entire seven-state set in eleven review pages.
for page in range(11):
 panel=Image.new('RGB',(1344,1320),'#e4dfd1');d=ImageDraw.Draw(panel)
 for r,idx in enumerate(sorted(masters)[page*4:page*4+4]):
  e=masters[idx]
  for c,s in enumerate(e['states']):
   pic=Image.open(R/s['image']).convert('RGBA');pic=pic.resize((192,288),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(192,288),'#e4dfd1'if r%2==0 else'#244139');bg.alpha_composite(pic);panel.paste(bg.convert('RGB'),(c*192,r*330));d.text((c*192+3,r*330+292),e['id']+' / '+str(c),font=font,fill='#285443')
 panel.save(R/'previews/world'/('vegetation-states-'+str(page+1)+'.jpg'),quality=94)
print(json.dumps(m['counts'],ensure_ascii=False))



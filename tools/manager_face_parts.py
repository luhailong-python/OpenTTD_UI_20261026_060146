"""Deterministic manager-face part tools. No production game logic or drawing.

Every raster output comes from a real accepted atlas crop, Alpha partition,
bounded source-pixel transform or isolated colour grade. Run --plan before
source delivery; it cannot create passing bindings or placeholder PNGs.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,datetime,argparse,math
from audit_manager_faces import extract
R=Path(__file__).resolve().parents[1];OUT=R/'assets/portraits/customization';PRE=R/'previews/manager-customization'
CANVAS=(512,512);ANCHOR=[256,496]
FAMILIES={'STR_FACE_CHIN':'chin','STR_FACE_EYEBROWS':'eyes','STR_FACE_MOUSTACHE':'beard','STR_FACE_LIPS':'mouth','STR_FACE_NOSE':'nose','STR_FACE_HAIR':'hair','STR_FACE_COLLAR':'collar','STR_FACE_JACKET':'robe','STR_FACE_TIE':'tie','STR_FACE_EARRING':'earring','STR_FACE_GLASSES':'glasses','fixed-base':'base'}
# These are registration guides. Actual crop/source landmarks are measured
# after viewing the newly delivered mother art and recorded per part.
TARGETS={'base':[102,70,410,405],'eyes':[139,175,373,263],'nose':[227,248,285,287],'mouth':[212,283,300,315],'hair':[100,30,412,173],'beard':[173,258,339,344],'collar':[169,337,343,401],'robe':[106,364,406,502],'tie':[218,370,294,452],'earring':[115,235,397,322],'glasses':[134,201,378,255]}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(R).as_posix()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item()if isinstance(x,np.generic)else str(x)),encoding='utf-8')
def source(p):
 p=Path(p);return {'file':rel(p),'sha256':sha(p),'record':rel(p)+('.generation.json'if Path(str(p)+'.generation.json').exists()else'.derivation.json')}
def clean_transparent(im):
 a=np.asarray(im.convert('RGBA')).copy();a[a[:,:,3]==0,:3]=0;return Image.fromarray(a)
def sample_rgba(im,sx,sy):
 """Premultiplied inverse sampling: remaps paint, never creates stroke colours."""
 a=np.asarray(im.convert('RGBA')).astype(float)/255;a[:,:,:3]*=a[:,:,3:4]
 x0=np.floor(sx).astype(int);y0=np.floor(sy).astype(int);dx=(sx-x0)[:,:,None];dy=(sy-y0)[:,:,None]
 x1=np.clip(x0+1,0,im.width-1);y1=np.clip(y0+1,0,im.height-1);x0=np.clip(x0,0,im.width-1);y0=np.clip(y0,0,im.height-1)
 out=a[y0,x0]*(1-dx)*(1-dy)+a[y0,x1]*dx*(1-dy)+a[y1,x0]*(1-dx)*dy+a[y1,x1]*dx*dy
 out[(sx<0)|(sx>im.width-1)|(sy<0)|(sy>im.height-1)]=0;alpha=out[:,:,3:4];out[:,:,:3]=np.divide(out[:,:,:3],alpha,out=np.zeros_like(out[:,:,:3]),where=alpha>1e-9)
 return clean_transparent(Image.fromarray(np.uint8(np.clip(out*255,0,255))))
_NATIVE_COMPONENTS={}
def actual_component_ownership(path,boxes):
 from scipy import ndimage
 key=(str(path),sha(path))
 if key not in _NATIVE_COMPONENTS:
  native=Image.open(path).convert('RGBA');ar=np.asarray(native);labels,n=ndimage.label(ar[:,:,3]>128);sizes=np.bincount(labels.ravel());big=np.flatnonzero(sizes>150);big=big[big!=0];core=np.where(np.isin(labels,big),labels,0);indices=ndimage.distance_transform_edt(core==0,return_distances=False,return_indices=True);owner=core[tuple(indices)];dist=ndimage.distance_transform_edt(core==0);lookup={}
  for label,obj in enumerate(ndimage.find_objects(labels),1):
   if obj and label in big:lookup[(obj[1].start,obj[0].start,obj[1].stop,obj[0].stop)]=label
  _NATIVE_COMPONENTS[key]=(ar,core,owner,dist,lookup)
 ar,core,owner,dist,lookup=_NATIVE_COMPONENTS[key];selected=[lookup[tuple(b)]for b in boxes];out=ar.copy();r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0);neon=((r>g*4)&(r>b*4)&(g<80))|((r>220)&(g>220)&(b<45));keep=np.isin(owner,selected)&(ar[:,:,3]>=8)&((dist<=3)|((dist<=24)&~neon));out[~keep]=0
 return Image.fromarray(out),{'coreAlphaThreshold':128,'selectedActualComponentBoundsPx':boxes,'ownershipMethod':'nearest significant actual native Alpha component; retain source antialias/skin feather within24px, discard subvisible or remote/neon background contamination; no invented paint','discardedNonOwnedPixels':int(np.count_nonzero((ar[:,:,3]>0)&~keep))}
def registered_crop(atlas,box,family,target=None,source_ownership_polygon=None,registration=None,cleanup_connected_body=False,core_component_boxes=None,face_frame_fit=None):
 """Real Alpha only. No guessed background key or component-dot deletion."""
 im=Image.open(atlas).convert('RGBA');cleanup={}
 if core_component_boxes:im,cleanup=actual_component_ownership(atlas,core_component_boxes)
 crop=im.crop(box)
 if cleanup_connected_body:
  from scipy import ndimage
  ar=np.asarray(crop).copy();lab,n=ndimage.label(ar[:,:,3]>32);sizes=np.bincount(lab.ravel());sizes[0]=0;main=lab==int(np.argmax(sizes));distance=ndimage.distance_transform_edt(~main);keep=main|((distance<=2)&(ar[:,:,3]>=8));removed=int(np.count_nonzero((ar[:,:,3]>0)&~keep));ar[~keep]=0
  r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0);bad=((r>g*1.8)&(g<90))|((r>180)&(g>180)&(b<45))|(g>r*1.1)|((np.minimum(np.minimum(r,g),b)>232)&(g>=r*.98))
  edge=ndimage.distance_transform_edt(main)<=3;bad&=edge&keep
  inside=ndimage.binary_erosion(main,iterations=3)&~bad
  nearest=ndimage.distance_transform_edt(~inside,return_distances=False,return_indices=True)
  old=ar.copy();ar[bad,:3]=old[nearest[0][bad],nearest[1][bad],:3];crop=Image.fromarray(ar)
  cleanup={'mainBodyAlphaThreshold':32,'retainedAntialiasDistancePx':2,'retainedAntialiasMinimum':8,'discardedDisconnectedOrSubvisiblePixels':removed,'edgeChromaticContaminationPixels':int(bad.sum()),'edgeRGBRule':'Only neon/white matte contamination at3px silhouette edge copies nearest actual interior painted RGB; source Alpha retained. No new colour/stroke painting.'}
 if source_ownership_polygon:
  mask=Image.new('L',crop.size);ImageDraw.Draw(mask).polygon(source_ownership_polygon,fill=255);a=np.asarray(crop).copy();a[:,:,3]=np.minimum(a[:,:,3],np.asarray(mask));crop=Image.fromarray(a)
 bb=crop.getbbox()
 if not bb:raise ValueError('empty real source crop '+str(box))
 part=crop.crop(bb);native_part=part.copy();x0,y0,x1,y1=target or TARGETS[family];scale=min(1,(x1-x0)/part.width,(y1-y0)/part.height)
 if registration:
  scale=registration['scale']
  if not 0<scale<=1:raise ValueError('measured registration must not enlarge native pixels')
 if scale<1:part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.LANCZOS)
 at=[round((x0+x1-part.width)/2),round((y0+y1-part.height)/2)]
 if registration:
  sa=registration['sourceAnchorWithinCellPx'];da=registration['destinationAnchorPx'];at=[round(da[0]-(sa[0]-bb[0])*scale),round(da[1]-(sa[1]-bb[1])*scale)]
 if at[0]<0 or at[1]<0 or at[0]+part.width>512 or at[1]+part.height>512:raise ValueError('measured native part would be clipped on formal512 canvas')
 canvas=Image.new('RGBA',CANVAS);canvas.alpha_composite(part,at)
 if face_frame_fit:
  crown=face_frame_fit['fixedCrownY'];below=face_frame_fit['belowCrownYScale'];spread=face_frame_fit['lowerFrameXScale']
  if scale*below>1.000001 or scale*spread>1.000001:raise ValueError('hair native pixels would be enlarged by frame fit')
  yy,xx=np.indices((512,512));ry=np.where(yy<=crown,yy,crown+(yy-crown)/below);t=np.clip((ry-crown)/130,0,1);rx=256+(xx-256)/(1+(spread-1)*t)
  canvas=sample_rgba(native_part,(rx-at[0])/scale,(ry-at[1])/scale)
 if canvas.getchannel('A').getextrema()[0]!=0:raise ValueError('source has no real transparent exterior; do not treat a checker/white backing as Alpha')
 return clean_transparent(canvas),{'sourceCellCropPx':list(box),'sourcePaintBBoxWithinCell':list(bb),'sourcePaintSizePx':[bb[2]-bb[0],bb[3]-bb[1]],'targetGuideRectPx':[x0,y0,x1,y1],'registeredOffsetPx':at,'scaleApplied':scale,'measuredLandmarkRegistration':registration,'nativeFaceFrameFit':face_frame_fit,'frameFitSampling':'direct original native part pixel coordinates, not enlargement of a pre-scaled raster'if face_frame_fit else None,'matteCleanup':cleanup,'nativeUpscale':False}
def split_chin(base,band=(292,360)):
 """Complementary Alpha band, exact source pose reconstructs the clean base."""
 ar=np.asarray(base).copy();y0,y1=band;owner=np.zeros(ar.shape[:2],bool);owner[y0:y1]=ar[y0:y1,:,3]>0
 head=ar.copy();head[owner]=0;chin=ar.copy();chin[~owner]=0
 return Image.fromarray(head),Image.fromarray(chin),owner
def chin_variant(chin,width_scale,band=(292,360)):
 if not .84<=width_scale<=1:raise ValueError('chin geometry limited to native-size narrowing, never enlarge')
 if width_scale==1:return chin.copy()
 y,x=np.indices(chin.size[::-1]);y0,y1=band;t=np.clip((y-y0)/(y1-y0-1),0,1);shape=np.sin(np.pi*t)
 # Both joining rows remain fixed; only the actual lower cheek contour narrows.
 sx=256+(x-256)/(1+(width_scale-1)*shape);out=np.asarray(sample_rgba(chin,sx,y)).copy();native=np.asarray(chin);out[y0]=native[y0];out[y1-1]=native[y1-1];return Image.fromarray(out)
def iris_ownership(eyes,boxes):
 ar=np.asarray(eyes);r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0);roi=np.zeros(ar.shape[:2],bool)
 for x0,y0,x1,y1 in boxes:roi[y0:y1,x0:x1]=True
 # Native brown iris chroma, excluding skin, sclera white, black pupil/ink.
 mask=roi&(r>g*1.07)&(g>b*1.60)&(r>38)&(r<245)&(b<110)&(ar[:,:,3]>128)
 return mask
def eye_palette(eyes,mask,name):
 target={'brown':[98,61,37],'blue':[51,112,150],'green':[65,125,77]}[name];a=np.asarray(eyes).copy();rgb=a[:,:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722]);t=np.array(target,float);ref=float(t@np.array([.2126,.7152,.0722]));grade=np.clip(lum[:,:,None]*t/ref,0,255);a[mask,:3]=np.uint8(grade[mask]);return clean_transparent(Image.fromarray(a))
def skin_ownership(part,exclude=None):
 ar=np.asarray(part);r,g,b=np.moveaxis(ar[:,:,:3].astype(float),-1,0)
 mask=(r>140)&(g>100)&(b>60)&(r>g*1.04)&(g>b*1.04)&(r<g*1.9)&(g<b*1.8)&(ar[:,:,3]>128)
 if exclude is not None:
  from scipy import ndimage
  mask&=~ndimage.binary_dilation(exclude,iterations=2)
 return mask
def match_skin(part,owner,target):
 ar=np.asarray(part).copy();source_rgb=np.median(ar[owner,:3],axis=0).astype(float)
 ar[owner,:3]=np.uint8(np.clip(ar[owner,:3].astype(float)*np.asarray(target)/np.maximum(source_rgb,1),0,255))
 return clean_transparent(Image.fromarray(ar)),source_rgb.tolist()
def active_indices(style,values,spec=None):
 fields=(spec or extract(R))['styles'][style]['fields'];hidden=set()
 for f in fields:
  if f['kind']=='Toggle':hidden.update(f['hiddenWhenValue'+str(values.get(f['sourceVarIndex'],0))])
 return [f['sourceVarIndex']for f in fields if f['sourceVarIndex']not in hidden]
def source_order(style,values,spec=None):
 fields=(spec or extract(R))['styles'][style]['fields'];active=set(active_indices(style,values,spec));return [f['sourceVarIndex']for f in fields if f['kind']=='Sprite'and f['sourceVarIndex']in active]
def ui_order(style,values,spec=None):
 fields=(spec or extract(R))['styles'][style]['fields'];active=set(active_indices(style,values,spec));return [f['sourceVarIndex']for f in sorted(fields,key=lambda f:f['uiPosition'])if f['sourceVarIndex']in active and f['name']!='fixed-base']
def source_adapter(spec=None):
 spec=spec or extract(R);rows=[]
 for r in spec['requirements']:
  q=dict(r)
  if r['kind']=='Sprite':q.update({'partFamily':'chin'if r['fieldName']=='fixed-base'and r['sourceStyle']==1 and r['sourceVarIndex']==4 else FAMILIES[r['fieldName']],'bindingStatus':'requires-real-source-part','assetIds':[]})
  elif r['kind']=='Palette':q.update({'bindingStatus':'requires-actual-iris-mask','paletteRule':None})
  else:q['bindingStatus']='source-control-relationship-read; needs-actual-preview'
  rows.append(q)
 return rows
class PartCatalog:
 def __init__(self):self.assets=[];OUT.mkdir(parents=True,exist_ok=True)
 def emit(self,aid,im,sources,operation,family,**extra):
  im=clean_transparent(im);p=OUT/(aid+'.png');im.save(p);bb=im.getbbox();q={'id':aid,'image':rel(p),'sha256':sha(p),'width':im.width,'height':im.height,'canvas':list(im.size),'anchorPx':ANCHOR,'pivotUnity':[.5,1-496/512],'category':'manager-'+family,'family':family,'assetRole':'alpha-ownership-data'if family=='mask'else'composable-sprite','sRGBSuggested':family!='mask','spriteTypeSuggested':'Single','borderLBRTPx':[0,0,0,0],'derivedFrom':sources,'derivedAt':now(),'route':'deterministic-derivative','nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'nativeUpscale':False,'operation':operation,'paintedBBoxPx':list(bb)if bb else None,'unityValidated':False,'status':'produced-needs-assembly-review',**extra}
  savej(str(p)+'.derivation.json',q);self.assets.append(q);return q
 def extract_atlas(self,atlas_spec):
  p=R/atlas_spec['file'];family=atlas_spec['family'];src=source(p);made=[]
  if not(R/src['record']).is_file():raise ValueError('missing actual source provenance '+src['record'])
  # Actual cell ownership boxes are supplied after the producer views the
  # atlas; no equal-grid guess is silently accepted as native part ownership.
  for cell in atlas_spec['cells']:
   if cell.get('pieces'):
    im=Image.new('RGBA',CANVAS);details=[]
    for piece in cell['pieces']:
     part,detail=registered_crop(p,piece['box'],family,piece.get('targetGuideRectPx'),piece.get('ownershipPolygonInCell'),piece.get('registration'),False,piece.get('coreComponentBoxes'));im.alpha_composite(part);details.append(detail)
    detail={'registeredPieces':details,'nativeUpscale':False,'pairedPartsIndependentlyRegistered':True}
   else:im,detail=registered_crop(p,cell['box'],family,cell.get('targetGuideRectPx'),cell.get('ownershipPolygonInCell'),cell.get('registration'),cell.get('cleanupConnectedBody',False),cell.get('coreComponentBoxes'),cell.get('faceFrameFit'))
   made.append(self.emit(cell['id'],im,[src],'Actual accepted transparent atlas ownership crop; proportional downscale only; fixed512 canvas registration; not a complete preset bust',family,**detail,nativeAtlasIndex=cell.get('index'),sourceAtlas=atlas_spec['file'],closedIrisSides=cell.get('closedIrisSides',[]),irisBoxesPx=cell.get('irisBoxesPx',[[178,203,230,257],[282,203,334,257]]),supplemental=cell.get('supplemental',False)))
  return made
def plan():
 spec=extract(R);rows=source_adapter(spec)
 p={'schema':'manager-native-part-production-plan.v1','createdAt':now(),'referenceCommit':spec['referenceCommit'],'sourceSpecFile':'docs/MANAGER_FACE_REQUIREMENTS.json','sourceSpecSha256':spec['sourceSha256'],'canvas':list(CANVAS),'anchorPx':ANCHOR,'registrationGuides':TARGETS,'guidesAreMeasuredNativeCoordinates':False,'guidesStatus':'provisional; actual new mother art must be viewed, then registration measured','spriteSlots':spec['spriteValueSlots'],'allBindings':len(rows),'uniqueSourceSpriteIds':spec['uniqueSourceSpriteIds'],'renderOrderRule':'active Sprite sourceVarIndex ascending; do not sort by UI position','uiOrderRule':'active named fields sorted by source uiPosition','offRule':'hide layers, never create empty PNGs to pad state counts','sourceAdapter':rows,'status':'native source parts pending; no satisfied-art claim','outputManifest':'assets/portraits/customization/manifest.json','productionCodeScope':'offline art export and static preview only; no Unity logic'}
 savej(R/'records/manager-production-plan.json',p);return p
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--plan',action='store_true');parser.add_argument('--extract-config');a=parser.parse_args()
 if a.extract_config:
  c=PartCatalog();cfg=load(R/a.extract_config)
  for atlas in cfg['atlases']:c.extract_atlas(atlas)
  savej(OUT/'part-catalog.json',{'createdAt':now(),'assets':c.assets,'status':'actual parts extracted; bindings and combined visual review pending','unityValidated':False});print(json.dumps({'actualParts':len(c.assets)}))
 else:
  p=plan();print(json.dumps({'sourceSpriteSlots':p['spriteSlots'],'sourceBindings':p['allBindings'],'status':p['status']},ensure_ascii=False))

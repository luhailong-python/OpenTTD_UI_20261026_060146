"""World-art extraction and geometry pipeline. Never draws replacement game art.
Requires Pillow. Every painted pixel comes from supplied image artwork.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat
import argparse, hashlib, json, math, datetime, sys, re
ROOT=Path(__file__).resolve().parents[1]
SLOPES=[(0,'flat'),(1,'w'),(2,'s'),(3,'sw'),(4,'e'),(5,'ew'),(6,'se'),(7,'wse'),(8,'n'),(9,'nw'),(10,'ns'),(11,'nws'),(12,'ne'),(13,'enw'),(14,'sen'),(27,'steep-w'),(23,'steep-s'),(30,'steep-e'),(29,'steep-n')]
CORNERS={'n':8,'e':4,'s':2,'w':1}
FLAT_POINTS={'n':(128,0),'e':(256,64),'s':(128,128),'w':(0,64)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def writej(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def rel(p):
 p=Path(p).resolve()
 try:return p.relative_to(ROOT).as_posix()
 except ValueError:return str(p)
def safeid(v):
 if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*',v):raise ValueError('unsafe asset id: '+str(v))
 return v
def new_output(out):
 out=Path(out).resolve()
 if not out.is_relative_to(ROOT):raise ValueError('Outputs must remain in this task root: '+str(ROOT))
 if out.exists()and any(out.iterdir()):raise FileExistsError('Use a new output directory; existing outputs are not overwritten: '+str(out))
 return out
def source_record(src,explicit=None):
 p=Path(explicit).resolve()if explicit else Path(str(src)+'.generation.json')
 return {'file':rel(src),'sha256':sha(src),'record':rel(p)if p.is_file()else None,'sourceRecordAvailable':p.is_file()}
def alpha_bounds(im,threshold=16):return im.getchannel('A').point(lambda a:255 if a>threshold else 0).getbbox()
def keep_main_component(im,threshold=100,margin=10):
 # Remove disconnected neighbouring-grid fragments; preserve the original
 # painted Alpha and its soft fringe around the largest real component.
 from collections import deque
 from PIL import ImageFilter
 w,h=im.size;alpha=im.getchannel('A');arr=bytearray(alpha.point(lambda a:255 if a>threshold else 0).tobytes());best=[]
 for at in range(w*h):
  if not arr[at]:continue
  arr[at]=0;queue=deque([at]);component=[]
  while queue:
   q=queue.popleft();component.append(q);x=q%w;y=q//w
   for yy in range(max(0,y-1),min(h,y+2)):
    row=yy*w
    for xx in range(max(0,x-1),min(w,x+2)):
     k=row+xx
     if arr[k]:arr[k]=0;queue.append(k)
  if len(component)>len(best):best=component
 mask=bytearray(w*h)
 for at in best:mask[at]=255
 m=Image.frombytes('L',(w,h),bytes(mask)).filter(ImageFilter.MaxFilter(margin*2+1))
 new_alpha=ImageChops.multiply(alpha,m);before=sum(1 for a in alpha.getdata()if a>16);after=sum(1 for a in new_alpha.getdata()if a>16)
 out=im.copy();out.putalpha(new_alpha)
 return out,{'method':'largest8-connected native opaque component with'+str(margin)+'px fringe; disconnected neighbouring-grid fragments removed','coreThreshold':threshold,'removedVisiblePixels':before-after,'componentCorePixels':len(best)}
def det3(m):return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
def solve3(m,b):
 den=det3(m)
 if abs(den)<1e-10:raise ValueError('Degenerate projection triangle')
 ans=[]
 for col in range(3):
  mm=[r[:]for r in m]
  for row in range(3):mm[row][col]=b[row]
  ans.append(det3(mm)/den)
 return ans
def affine_coeff(dst,src):
 m=[[float(x),float(y),1.]for x,y in dst]
 return tuple(solve3(m,[p[0]for p in src])+solve3(m,[p[1]for p in src]))
def triangle_mask(size,points):
 scale=4;mask=Image.new('L',(size[0]*scale,size[1]*scale))
 ImageDraw.Draw(mask).polygon([(round(x*scale),round(y*scale))for x,y in points],fill=255)
 return mask.resize(size,Image.Resampling.LANCZOS)
def warp_triangles(src,size,source_points,dest_points,triangles):
 out=Image.new('RGBA',size)
 for labels in triangles:
  sp=[source_points[k]for k in labels];dp=[dest_points[k]for k in labels]
  piece=src.transform(size,Image.Transform.AFFINE,affine_coeff(dp,sp),Image.Resampling.BICUBIC)
  mask=Image.new('L',size);ImageDraw.Draw(mask).polygon(dp,fill=255)
  piece.putalpha(ImageChops.multiply(piece.getchannel('A'),mask))
  out.alpha_composite(piece)
 outer=triangle_mask(size,[dest_points[k]for k in ['n','e','s','w']])
 out.putalpha(ImageChops.multiply(out.getchannel('A'),outer))
 return out
def corner_heights(code):
 vals={k:1 if code&bit else 0 for k,bit in CORNERS.items()}
 if code&16:
  highest={27:'w',23:'s',30:'e',29:'n'}.get(code)
  if highest is None:raise ValueError('Not a valid steep slope')
  vals[highest]=2
 return vals
def slope_triangles(code):
 # GetPartialPixelZ uses the low diagonal for opposite-corner saddles.
 # Single/triple N/S corners split across W-E; single/triple E/W split across N-S.
 raw=code&15
 return [('n','e','w'),('e','s','w')]if raw in [2,7,8,10,13]else[('n','e','s'),('n','s','w')]
def projected_slope(flat,code):
 heights=corner_heights(code)
 points={k:(x,y+64-heights[k]*32)for k,(x,y)in FLAT_POINTS.items()}
 out=warp_triangles(flat,(256,192),FLAT_POINTS,points,slope_triangles(code))
 return out,points,heights
def normalize_flat(sheet,item):
 box=list(map(int,item['box']));L,T,R,B=box
 if min(L,T)<0 or R>sheet.width or B>sheet.height or L>=R or T>=B:raise ValueError('invalid source box '+str(box))
 crop=sheet.crop(box).convert('RGBA');kind=item.get('sourceKind','flat_diamond')
 if kind=='square_texture':
  if min(crop.size)<256:raise ValueError('square texture source needs >=256 native pixels on both axes; no upscale allowed')
  # UV coordinates are the logical square corners of the projected diamond.
  sp={'n':(0,0),'e':(crop.width,0),'s':crop.size,'w':(0,crop.height)}
 else:
  q=item.get('sourceQuad')
  if q is None:q=[[crop.width/2,0],[crop.width,crop.height/2],[crop.width/2,crop.height],[0,crop.height/2]]
  sp=dict(zip(['n','e','s','w'],[tuple(map(float,p))for p in q]))
  native_w=max(p[0]for p in q)-min(p[0]for p in q);native_h=max(p[1]for p in q)-min(p[1]for p in q)
  if native_w<256 or native_h<128:raise ValueError('native flat diamond footprint smaller than256x128; refuse to upscale: '+str((native_w,native_h)))
 # No inferred material recolouring or painted geometric detail.
 return warp_triangles(crop,(256,128),sp,FLAT_POINTS,[('n','e','s'),('n','s','w')]),{'sourceBox':box,'sourceQuad':{k:list(v)for k,v in sp.items()},'sourceKind':kind,'sourceCropSize':list(crop.size)}
def edge_rmse(flat):
 def sample(u,v):
  # Interior sample avoids transparent antialias fringe.
  x=128+(v-u)*128;y=(u+v)*64
  return flat.getpixel((min(255,max(0,round(x))),min(127,max(0,round(y)))))
 vals_u=[];vals_v=[]
 for k in range(1,64):
  t=k/64
  a,b=sample(.012,t),sample(.988,t)
  c,d=sample(t,.012),sample(t,.988)
  if min(a[3],b[3])>128:vals_u.extend((a[j]-b[j])**2 for j in range(3))
  if min(c[3],d[3])>128:vals_v.extend((c[j]-d[j])**2 for j in range(3))
 return {'oppositeUEdgeRMSE':round(math.sqrt(sum(vals_u)/len(vals_u)),3)if vals_u else None,'oppositeVEdgeRMSE':round(math.sqrt(sum(vals_v)/len(vals_v)),3)if vals_v else None,'threshold':18,'meaning':'Photometric comparison only; not proof of painted seam or adjacency geometry.'}
def base_asset(aid,file,im,src,operation,category='terrain',anchor=None):
 anchor=anchor or[im.width/2,im.height/2]
 return {'id':aid,'image':str(file),'width':im.width,'height':im.height,'format':'PNG','mode':'RGBA','anchorPx':anchor,'pivotUnity':[anchor[0]/im.width,1-anchor[1]/im.height],'category':category,'artSource':'host_image','operation':operation,'nativeModelGeneration':False,'derivedFrom':[src],'actualModel':None,'actualQuality':None,'modelDisclosure':'Inherited from source image record; unreported model/quality remain unconfirmed.','status':'produced-needs-visual-review','unityValidated':False,'nativeUpscale':False,'sourcePixelCountChanged':True}
def export_assets(out,entries,images,qa,meta):
 out=new_output(out)
 if meta.get('strict')and any(q['level']in['WARN','FAIL']for q in qa):raise ValueError('Strict mode refused to publish: '+json.dumps(qa,ensure_ascii=False))
 out.mkdir(parents=True,exist_ok=True)
 for a,im in zip(entries,images):
  file=out/a['image'];file.parent.mkdir(parents=True,exist_ok=True);im.save(file)
  a['sha256']=sha(file);a['image']=rel(file)
  record={'file':a['image'],'sha256':a['sha256'],'generatedAt':now(),'route':'deterministic-derivative','tool':'world_pack.py','width':im.width,'height':im.height,'format':'PNG','nativeModelGeneration':False,'operation':a['operation'],'derivedFrom':a['derivedFrom'],'actualModel':None,'actualQuality':None,'unverifiedReason':a['modelDisclosure']}
  writej(str(file)+'.derivation.json',record)
 manifest={'schema':'cloud-route.world-art.v1','createdAt':now(),'taskRoot':str(ROOT),'projection':{'logicalTileSize':[128,64],'exportTileSize':[256,128],'exportHeightStep':32,'logicalHeightStep':16,'origin':'tile centre; world x SW, world y SE; screen x=(j-i)*64, screen y=(i+j)*32-z*16'},'assets':entries,'qa':qa,'acceptance':'not accepted until visual/material seam checks are signed off','limitations':['Not a runtime game map, collision proof or Unity import verification.','Geometrical resampling does not create new native model detail.'],**{k:v for k,v in meta.items()if k!='strict'}}
 writej(out/'manifest.json',manifest)
 return manifest
def terrain(args):
 src=Path(args.source).resolve();spec=readj(args.spec);sheet=Image.open(src).convert('RGBA');provenance=source_record(src,args.source_record)
 entries=[];images=[];qa=[]
 for item in spec['items']:
  ident=safeid(item['id']);flat,info=normalize_flat(sheet,item)
  seam=edge_rmse(flat)
  for key in ['oppositeUEdgeRMSE','oppositeVEdgeRMSE']:
   q=seam[key];qa.append({'id':ident+'.'+key,'level':'WARN'if q is None or q>18 else'OK','value':q,'threshold':18,'file':rel(src),'meaning':'measured only; visual repeat review still required'})
  a=base_asset(ident+'-flat',ident+'/flat.png',flat,provenance,'AI painted terrain crop -> 2:1 canonical diamond geometric resampling; no generated detail added',anchor=[128,64])
  a.update(info);a.update({'materialId':ident,'climate':item.get('climate','shared'),'footprintPolygon':[[0,64],[128,0],[256,64],[128,128]],'logicalFootprint':[1,1],'photometricSeam':seam,'slopeCode':0,'baselineLevel':0})
  entries.append(a);images.append(flat)
  for code,name in SLOPES:
   im,points,heights=projected_slope(flat,code)
   a=base_asset(ident+'-slope-'+name,ident+'/slope-'+name+'.png',im,provenance,'AI painted flat material -> deterministic piecewise-affine slope projection; not 19 separate native AI generations',anchor=[128,128])
   a.update(info);a.update({'materialId':ident,'climate':item.get('climate','shared'),'slopeCode':code,'slopeName':name,'cornerHeights':heights,'cornerPixels':{k:list(v)for k,v in points.items()},'heightStepPixels':32,'logicalFootprint':[1,1],'triangles':[list(t)for t in slope_triangles(code)],'sourceFlatAssetId':ident+'-flat'})
   entries.append(a);images.append(im)
 manifest=export_assets(args.outdir,entries,images,qa,{'batchId':spec.get('id','terrain-batch'),'strict':args.strict,'sourceGeometryContract':'docs/WORLD_MODULE_SPEC.md'})
 print(json.dumps({'manifest':rel(Path(args.outdir)/'manifest.json'),'assets':len(entries),'qa':qa,'status':manifest['acceptance']},ensure_ascii=False))
def slice_props(args):
 src=Path(args.source).resolve();spec=readj(args.spec);source_im=Image.open(src)
 if source_im.mode!='RGBA':raise ValueError('Prop/vehicle source must already have real Alpha; do not infer transparency from RGB or checkerboard.')
 sheet=source_im.convert('RGBA');provenance=source_record(src,args.source_record);entries=[];images=[];qa=[]
 for item in spec['items']:
  aid=safeid(item['id']);L,T,R,B=map(int,item['box'])
  if min(L,T)<0 or R>sheet.width or B>sheet.height or L>=R or T>=B:raise ValueError('invalid source box for '+aid)
  raw=sheet.crop((L,T,R,B));cleanup=None
  alpha_cleanup=[]
  for rect in item.get('alphaEraseRects',[]):
   alpha=raw.getchannel('A');ImageDraw.Draw(alpha).rectangle(rect,fill=0);raw.putalpha(alpha);alpha_cleanup.append({'operation':item.get('alphaErasePurpose','authored Alpha erase of adjacent atlas fragment'),'rect':rect})
  for rect in item.get('alphaKeepGoldRects',[]):
   # An adjacent white floor can touch a gold finial in a tightly packed
   # native atlas. Keep the finial's actual pixels, erase only that floor.
   pix=raw.load();x0,y0,x1,y1=rect
   for yy in range(max(0,y0),min(raw.height,y1)):
    for xx in range(max(0,x0),min(raw.width,x1)):
     r,g,b,aa=pix[xx,yy]
     if not(r>g*1.12 and g>b*1.25):pix[xx,yy]=(r,g,b,0)
   alpha_cleanup.append({'operation':'keep actual gold finial pixels; remove touching low-chroma neighbouring floor by Alpha only','rect':rect,'condition':'R>1.12G and G>1.25B'})
  if item.get('keepMainComponent'):raw,cleanup=keep_main_component(raw,threshold=item.get('componentThreshold',100),margin=item.get('componentFringePx',10))
  bb=alpha_bounds(raw)
  if not bb:raise ValueError('empty Alpha asset '+aid)
  touches=bb[0]==0 or bb[1]==0 or bb[2]==raw.width or bb[3]==raw.height
  qa.append({'id':aid+'.source-edge-touch','level':'WARN'if touches and not item.get('edgeTouchAllowed',False)else'OK','value':touches,'threshold':False,'file':rel(src),'sourceBox':[L,T,R,B]})
  # Authored anchor is in raw crop pixels; trim offset stays recorded.
  original_anchor=item.get('anchorPx',[raw.width/2,bb[3]])
  anchor_source='authored'if'anchorPx'in item else'derived-alpha-bottom'
  piece=raw.crop(bb);sa=[original_anchor[0]-bb[0],original_anchor[1]-bb[1]]
  canvas=list(map(int,item.get('canvas',[512,512])));dest_anchor=item.get('targetAnchorPx',[canvas[0]/2,canvas[1]-32])
  available_left=dest_anchor[0];available_right=canvas[0]-dest_anchor[0];available_top=dest_anchor[1];available_bottom=canvas[1]-dest_anchor[1]
  ratios=[1.]
  for need,have in [(sa[0],available_left),(piece.width-sa[0],available_right),(sa[1],available_top),(piece.height-sa[1],available_bottom)]:
   if need>0:ratios.append(have/need)
  scale=min(ratios+[float(item.get('maximumScale',1.))])
  if scale<=0:raise ValueError('anchor cannot fit canvas for '+aid)
  size=[max(1,round(piece.width*scale)),max(1,round(piece.height*scale))]
  if size!=list(piece.size):piece=piece.resize(tuple(size),Image.Resampling.LANCZOS)
  at=[round(dest_anchor[0]-sa[0]*scale),round(dest_anchor[1]-sa[1]*scale)]
  out=Image.new('RGBA',tuple(canvas));out.alpha_composite(piece,tuple(at))
  a=base_asset(aid,aid+'.png',out,provenance,'lossless source crop and Alpha trim; optional explicit downscale-to-fit; transparent fixed-canvas padding; no upscale',item.get('category','props'),dest_anchor)
  if cleanup:a['operation']+='; '+cleanup['method']
  if alpha_cleanup:a['operation']+='; authored Alpha-only removal of neighbouring atlas fragments'
  a.update({'sourceBox':[L,T,R,B],'sourceCropSize':[raw.width,raw.height],'alphaTrimBox':list(bb),'sourceAnchorPx':original_anchor,'anchorSource':anchor_source,'scaleApplied':scale,'targetOffsetPx':at,'contentNativeSize':[bb[2]-bb[0],bb[3]-bb[1]],'contentExportSize':size,'climate':item.get('climate','shared'),'footprint':item.get('footprint',{'kind':'unverified','basis':'logical-tile'}),'occlusionClass':item.get('occlusionClass','tall'),'layer':item.get('layer','objects'),'animationGroup':item.get('animationGroup'),'direction':item.get('direction'),'frame':item.get('frame'),'sourcePixelCountChanged':scale!=1,'disconnectedFragmentCleanup':cleanup,'authoredAlphaCleanup':alpha_cleanup})
  if anchor_source!='authored':qa.append({'id':aid+'.anchor-authorship','level':'WARN','value':anchor_source,'threshold':'authored contact point','file':rel(src),'meaning':'Derived anchor is a suggestion; requires visual contact review.'})
  entries.append(a);images.append(out)
 manifest=export_assets(args.outdir,entries,images,qa,{'batchId':spec.get('id','prop-batch'),'strict':args.strict})
 print(json.dumps({'manifest':rel(Path(args.outdir)/'manifest.json'),'assets':len(entries),'qa':qa,'status':manifest['acceptance']},ensure_ascii=False))
def merge(args):
 out=Path(args.output).resolve()
 if not out.is_relative_to(ROOT):raise ValueError('output must stay in task root')
 assets=[];animations=[];used=set();sources=[]
 for mp in args.manifests:
  p=Path(mp).resolve();pack=readj(p);sources.append({'file':rel(p),'sha256':sha(p)})
  for a in pack.get('assets',[]):
   if a['id']in used:raise ValueError('duplicate asset id '+a['id'])
   used.add(a['id']);assets.append(a)
  animations.extend(pack.get('animations',[]))
 result={'schema':'cloud-route.world-art.v1','createdAt':now(),'projection':{'logicalTileSize':[128,64],'exportTileSize':[256,128],'logicalHeightStep':16,'exportHeightStep':32},'assets':assets,'animations':animations,'packSources':sources,'scenes':[],'status':'in-production-needs-visual-review','unityValidated':False}
 writej(out,result);print(json.dumps({'manifest':rel(out),'assets':len(assets),'animations':len(animations)}))
def validate(args):
 p=Path(args.manifest).resolve();pack=readj(p);checks=[]
 for a in pack.get('assets',[]):
  ip=ROOT/a['image'];ok=ip.is_file()
  checks.append({'id':a['id']+'.image','level':'OK'if ok else'FAIL','value':a['image']})
  if not ok:continue
  im=Image.open(ip)
  checks.append({'id':a['id']+'.hash-size','level':'OK'if sha(ip)==a.get('sha256')and im.size==(a['width'],a['height'])else'FAIL','value':[im.width,im.height]})
  checks.append({'id':a['id']+'.alpha','level':'OK'if im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0 else'WARN','value':im.mode})
  ax,ay=a['anchorPx'];checks.append({'id':a['id']+'.anchor-in-canvas','level':'OK'if 0<=ax<=im.width and 0<=ay<=im.height else'FAIL','value':[ax,ay]})
  checks.append({'id':a['id']+'.no-native-upscale','level':'OK'if not a.get('nativeUpscale')else'FAIL','value':a.get('nativeUpscale')})
  if a.get('status')not in ['accepted','art-checked']:checks.append({'id':a['id']+'.visual-acceptance','level':'WARN','value':a.get('status'),'threshold':'signed visual/material seam review'})
 if not pack.get('assets'):checks.append({'id':'pack.empty','level':'WARN','value':0,'threshold':'at least one produced asset'})
 out={'manifest':rel(p),'inputSha256':sha(p),'checkedAt':now(),'failures':sum(c['level']=='FAIL'for c in checks),'warnings':sum(c['level']=='WARN'for c in checks),'checks':checks,'scope':'file, native size and anchor checks only; not painted seam/navigation/Unity proof'}
 writej(args.report,out);print(json.dumps(out,ensure_ascii=False));return 1 if out['failures']else 0
def preview(args):
 p=Path(args.manifest).resolve();out=Path(args.html).resolve();pack=readj(p)
 if not out.is_relative_to(ROOT):raise ValueError('preview must stay in task root')
 template=Path(__file__).with_name('world_preview_template.html').read_text(encoding='utf-8')
 # Resolve all image URLs relative to the HTML, so file:// is supported.
 import os
 for a in pack.get('assets',[]):a['previewImage']=Path(os.path.relpath(ROOT/a['image'],out.parent)).as_posix()
 for anim in pack.get('animations',[]):
  anim['previewFrames']=[Path(os.path.relpath(ROOT/f,out.parent)).as_posix()for f in anim.get('frames',[])]
 data=json.dumps(pack,ensure_ascii=False).replace('</','<\\/')
 out.write_text(template.replace('__WORLD_MANIFEST__',data),encoding='utf-8')
 print(json.dumps({'preview':rel(out),'assets':len(pack.get('assets',[])),'status':'art-composition preview; no game/Unity behavior'}))
def main():
 ap=argparse.ArgumentParser(description=__doc__);subs=ap.add_subparsers(dest='command',required=True)
 for cmd,func in [('normalize-terrain',terrain),('slice',slice_props)]:
  q=subs.add_parser(cmd);q.add_argument('--source',required=True);q.add_argument('--spec',required=True);q.add_argument('--source-record');q.add_argument('--outdir',required=True);q.add_argument('--strict',action='store_true');q.set_defaults(func=func)
 q=subs.add_parser('merge');q.add_argument('--manifests',nargs='+',required=True);q.add_argument('--output',required=True);q.set_defaults(func=merge)
 q=subs.add_parser('validate');q.add_argument('--manifest',required=True);q.add_argument('--report',required=True);q.set_defaults(func=validate)
 q=subs.add_parser('preview');q.add_argument('--manifest',required=True);q.add_argument('--html',required=True);q.set_defaults(func=preview)
 args=ap.parse_args()
 try:return args.func(args)or 0
 except (ValueError,FileExistsError,FileNotFoundError,KeyError)as e:print('error: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())


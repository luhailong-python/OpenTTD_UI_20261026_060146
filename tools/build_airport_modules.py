"""Airport painted modules: native crops, explicit plane UV correction, no drawn runway colours."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter,ImageFont
import numpy as np,json,hashlib,math,re
from scipy import ndimage
import build_world_terrain as terrain
import build_world_network as network
R=Path(__file__).resolve().parents[1];OUT=R/'assets/world/infrastructure/airports';UV=192
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def src_record(p):return {'file':p.relative_to(R).as_posix(),'sha256':sha(p),'record':p.relative_to(R).as_posix()+'.generation.json'}
def saveasset(ident,im,source,operation,extra=None,category='airport-module',anchor=None):
 p=OUT/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p);anchor=anchor or[256,448]
 e={'id':ident,'image':p.relative_to(R).as_posix(),'width':im.width,'height':im.height,'anchorPx':anchor,'pivotUnity':[anchor[0]/im.width,1-anchor[1]/im.height],'anchorMeaning':'diamond-centre'if im.size==(256,128)else'front-contact-of-ground-footprint','category':category,'sha256':sha(p),'operation':operation,'derivedFrom':source if isinstance(source,list)else[source],'status':'needs-art-review','nativeUpscale':False,'unityValidated':False}
 e.update(extra or{});savej(Path(str(p)+'.derivation.json'),e);return e
def unwrap(sheet,quad):
 n,e,s,w=quad
 u=sheet.transform((UV,UV),Image.Transform.QUAD,tuple(n+w+s+e),Image.Resampling.BICUBIC).convert('RGBA')
 # Complete material UV corners by nearest substantial neighbouring texture. No replacement paint.
 a=np.array(u);mask=a[:,:,3]<32
 if mask.any():
  inds=ndimage.distance_transform_edt(mask,return_distances=False,return_indices=True);a[mask]=a[tuple(inds)][mask]
 a[:,:,3]=255
 return Image.fromarray(a)
def alpha_mask_box(l,t,r,b):
 m=Image.new('L',(UV,UV));ImageDraw.Draw(m).rectangle((round(l*UV),round(t*UV),round(r*UV),round(b*UV)),fill=255);return m
def owned_objects(src):
 im=Image.open(src).convert('RGBA');a=np.array(im)[:,:,3];labels,n=ndimage.label(a>32);sizes=np.bincount(labels.ravel());large=np.where(sizes>10000)[0];large=large[large!=0]
 assert len(large)==9,(src,len(large));seeds=np.where(np.isin(labels,large),labels,0);inds=ndimage.distance_transform_edt(seeds==0,return_distances=False,return_indices=True);owned=seeds[tuple(inds)]
 obs=[]
 for lab in large:
  yy,xx=np.where(seeds==lab);obs.append((int(lab),float(xx.mean()),float(yy.mean())))
 obs.sort(key=lambda o:o[2]);obs=sum([sorted(obs[r*3:r*3+3],key=lambda o:o[1])for r in range(3)],[])
 out=[]
 for lab,cx,cy in obs:
  alpha=np.where((owned==lab)&(a>=8),a,0).astype('uint8');alpha[alpha>=240]=255
  pic=im.copy();pic.putalpha(Image.fromarray(alpha));box=pic.getbbox();out.append((pic.crop(box),box))
 return out
def extract():
 assets=[];sources={}
 for name in ['airport-ground','airport-props']:
  src=R/'source-art/world'/(name+'.png');sources[name]=src_record(src)
  objs=owned_objects(src)
  labels=['runway-raw','threshold-raw','cross-raw','taxi-raw','curve-raw','apron-raw','helipad-raw','hangar','terminal']if name=='airport-ground'else['control-tower','radar','windsock','raised-helipad','offshore-helipad','jetbridge','fence-source','administration','baggage']
  indices=[7,8]if name=='airport-ground'else list(range(9))
  for i in indices:
   part,box=objs[i];s=min(1,224/part.width,320/part.height);part=part.resize((round(part.width*s),round(part.height*s)),Image.Resampling.LANCZOS);im=Image.new('RGBA',(512,512));im.alpha_composite(part,(256-part.width//2,448-part.height))
   e=saveasset('airport-'+labels[i],im,sources[name],'component ownership crop, alpha<8 removal and >=240 opaque normalization, proportional downscale to <=224w/320h, fixed512 canvas; not new native detail',{'sourceCropXYXY':list(box),'sourceCell':i,'uniformScale':s,'logicalFootprint':[1,1]})
   assets.append(e)
 # Shared transmitter is visually distinct from the control tower; reuse the painted civic radio mast.
 mp=R/'assets/world/infrastructure/objects/radio-mast.png';mi=Image.open(mp).convert('RGBA');bb=mi.getbbox();part=mi.crop(bb);s=min(1,224/part.width,320/part.height);part=part.resize((round(part.width*s),round(part.height*s)),Image.Resampling.LANCZOS);can=Image.new('RGBA',(512,512));can.alpha_composite(part,(256-part.width//2,448-part.height))
 assets.append(saveasset('airport-radio-mast',can,{'file':mp.relative_to(R).as_posix(),'sha256':sha(mp),'record':mp.relative_to(R).as_posix()+'.derivation.json'},'shared actual painted radio transmitter crop, proportional downscale only and fixed airport tile anchor; distinguishes transmitter from ATC tower',{'uniformScale':s,'logicalFootprint':[1,1]}))
 # Actual native inner pavement diamonds, excluding decorative corner towers/landscaping from flat ground.
 sheet=Image.open(R/'source-art/world/airport-ground.png').convert('RGBA')
 quads={
 'runway':[[270,83],[467,178],[270,272],[78,176]],
 'threshold':[[768,82],[963,178],[768,275],[570,177]],
 'cross':[[1267,85],[1452,178],[1267,276],[1080,178]],
 'taxi':[[270,368],[455,459],[270,550],[86,457]],
 'curve':[[768,368],[951,459],[768,551],[580,457]],
 'apron':[[1267,367],[1448,459],[1267,551],[1087,458]],
 'helipad':[[229,709],[405,804],[229,899],[51,804]]}
 uv={k:unwrap(sheet,q)for k,q in quads.items()}
 # Recenter the truly painted runway dashes and taxi stripe onto the canonical UV axis.
 fits={}
 for name in ['runway','taxi']:
  a=np.array(uv[name]);r,g,b=np.moveaxis(a[:,:,:3],-1,0);yy,xx=np.mgrid[0:UV,0:UV]/(UV-1)
  mask=((r>180)&(g>180)&(b>160)&((np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]))<60))if name=='runway'else((r>170)&(g>110)&(b<120)&(r>g*1.05))
  mask&=(yy>.2)&(yy<.8)&(xx>.08)&(xx<.92)
  ys,xs=np.where(mask)
  if len(xs)<15:raise ValueError('native painted marking not detected '+name)
  slope,intercept=np.polyfit(xs/(UV-1),ys/(UV-1),1);fits[name]={'slope':float(slope),'intercept':float(intercept),'paintPixels':int(len(xs))}
  uv[name]=network.sample_uv(uv[name],xx,yy+slope*xx+intercept-.5)
 # Pure concrete is from native unmarked apron, never program-painted.
 base=uv['apron'].convert('RGBA');ground={}
 # Shared pavement corridor clips actual paint with a uniform native mouth width.
 for typ,width in [('runway',.66),('threshold',.66),('taxi',.52)]:
  u=base.copy();u.paste(uv[typ],(0,0),alpha_mask_box(0,.5-width/2,1,.5+width/2));ground[typ+'-y']=u;ground[typ+'-x']=u.transpose(Image.Transpose.TRANSPOSE)
  if typ=='threshold':
   ground['threshold-y-reverse']=u.transpose(Image.Transpose.ROTATE_180);ground['threshold-x-reverse']=ground['threshold-y-reverse'].transpose(Image.Transpose.TRANSPOSE)
 # Crossing: actual painted native centre plus aligned painted straight arms. No new runway stroke.
 cross=ground['runway-y'].copy();cross.paste(ground['runway-x'],(0,0),alpha_mask_box(.17,0,.83,1));cross.paste(uv['cross'],(0,0),alpha_mask_box(.28,.28,.72,.72));ground['runway-cross']=cross
 ground['apron']=base;ground['helipad']=uv['helipad']
 # Native taxi marking extraction; UV routing reuses paint, geometry supplies masks only.
 ar=np.array(uv['taxi']);r,g,b=np.moveaxis(ar[:,:,:3],-1,0);yy=np.indices((UV,UV))[0]/(UV-1);yellow=(r>170)&(g>110)&(b<120)&(r>g*1.05)&(np.abs(yy-.5)<.065)
 stripe=uv['taxi'].copy();stripe.putalpha(Image.fromarray(np.uint8(yellow)*255).filter(ImageFilter.MaxFilter(3)))
 for mask in range(1,16):
  u=base.copy();ports=[k for k in range(4)if mask&(1<<k)]
  if len(ports)==1:
   line=stripe if ports[0]in[0,2]else stripe.transpose(Image.Transpose.TRANSPOSE)
   piece=line.copy();piece.putalpha(ImageChops.multiply(piece.getchannel('A'),network.corridor_mask(ports[0])));u.alpha_composite(piece)
  else:
   for ai,a in enumerate(ports):
    for b in ports[ai+1:]:u.alpha_composite(network.tram_segment(stripe,a,b))
  ground['taxi-mask-'+format(mask,'02d')]=u
 for ident,u in ground.items():
  im=terrain.project(u);e=saveasset('airport-ground-'+ident,im,sources['airport-ground'],'actual native inner pavement quad ->192UV; native marking centerline fit/recenter; painted pavement/marking corridor clipping or symmetric UV transpose; native crossing centre or taxi painted-stripe annular remap; canonical256x128 diamond. No runway/taxi paint drawn by code.',{'nativeQuads':quads,'markingFits':fits,'uvWorkingSize':[192,192],'sourceMaxQuadWidth':390,'sourceMinQuadHeight':184,'sourceRequirementIds':[]},anchor=[128,64],category='airport-ground')
  assets.append(e)
 # Fence planes are geometrically symmetric; native painting retained with declared mirror/shear, not a new viewpoint drawing.
 fs=next(e for e in assets if e['id']=='airport-fence-source');fi=Image.open(R/fs['image']).convert('RGBA');box=fi.getbbox();part=fi.crop(box);scale=128/part.width;part=part.resize((128,round(part.height*scale)),Image.Resampling.LANCZOS)
 # Source baseline slope about0.28 vs canonical0.5; vertical posts stay vertical under Y shear.
 height=part.height+40;sheared=part.transform((128,height),Image.Transform.AFFINE,(1,0,0,-.22,1,0),Image.Resampling.BICUBIC);sheared=sheared.crop(sheared.getbbox());height=sheared.height
 for edge in ['SW','SE','NW','NE']:
  fence=sheared.copy()
  if edge in ['SE','NW']:fence=fence.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  im=Image.new('RGBA',(512,512));pos={'SW':(128,448-height),'SE':(256,448-height),'NW':(128,384-height),'NE':(256,384-height)}[edge];im.alpha_composite(fence,pos)
  e=saveasset('airport-fence-'+edge.lower(),im,[{'file':fs['image'],'sha256':fs['sha256'],'record':fs['image']+'.derivation.json'}],'actual symmetric fence painting downsized to128px edge width, ground-baseline Y shear +0.22x preserving vertical poles; declared horizontal mirror for other diagonal; fixed edge placement, not separately native perspective',{'edge':edge,'sourceBaselineSlopeEstimate':.28,'targetBaselineSlope':.5,'symmetricMirror':edge in['SE','NW'],'logicalFootprint':[1,1]},category='airport-fence')
  assets.append(e)
 savej(OUT/'manifest.json',{'schemaVersion':1,'assets':assets,'animations':[],'coverageMappings':[],'sourceLayouts':[],'status':'modules-produced-needs-review','nativeAtlasCount':2,'nativeObjectsInAtlases':18,'geometryNotes':['Corner towers/grass ornament in generated ground atlas are excluded from flat pavement inner quads.','Source lane paints are geometrically normalized to edge midpoints, not diamond vertices.','Taxi graph marks are UV-remapped actual native yellow paint over actual apron material; no code strokes.'],'sourceQuads':quads,'markingFits':fits})
 print(json.dumps({'moduleSprites':len(assets),'nativeGroundFits':fits}))
if __name__=='__main__':extract()


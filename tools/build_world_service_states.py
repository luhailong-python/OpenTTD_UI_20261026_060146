"""Source-painted services: explicit geometry/photometry derivatives, never native painting."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageChops,ImageEnhance,ImageFilter
import numpy as np, math,json
from scipy import ndimage
import world_pack as wp
import build_world_services as services
import build_world_terrain as terrain
R=wp.ROOT
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pack(g):return load(R/'assets/world/infrastructure'/g/'manifest.json')
def ref(a):return {'file':a['image'],'sha256':wp.sha(R/a['image']),'record':a['image']+'.derivation.json'}
def polygon(size,points):
 m=Image.new('L',size);ImageDraw.Draw(m).polygon(points,fill=255);return m
def extract_layer(im,mask):
 p=im.copy();p.putalpha(ImageChops.multiply(p.getchannel('A'),mask));return p
def change_glass(im,state,kind):
 a=np.asarray(im).copy();y,x=np.mgrid[0:im.height,0:im.width];r,g,b=np.moveaxis(a[...,:3].astype(float),-1,0)
 # Lens regions exclude badge, jade body, gold supports and ivory base.
 upper=(y<210)&(y>112)&(x<260)&(x>100)
 red=(r>g*1.5)&(r>b*1.5)&(r>110)&upper
 green=(g>r*1.3)&(g>b*1.1)&(g>90)&(y<265)&(y>160)&(x<210)&(x>100)
 off=green if state=='red' else red
 if kind=='electric':
  a[off,:3]=np.uint8(a[off,:3].astype(float)*.22)
 elif state=='green':
  # Regrade only the native red glass indicator on the mechanical post.
  red=red&(y<160)&(x>150)&(x<245)
  a[red,0]=np.uint8(np.clip(g[red]*.75,0,255));a[red,1]=np.uint8(np.clip(r[red]*.88,0,255));a[red,2]=np.uint8(np.clip(b[red]+35,0,255))
 return Image.fromarray(a)
def ivory_disc(im):
 a=np.asarray(im);r,g,b=np.moveaxis(a[...,:3],-1,0);y,x=np.mgrid[0:im.height,0:im.width]
 mask=(r>160)&(g>145)&(b>90)&(r.astype(float)<g*1.3)&(g.astype(float)<b*1.7)&(y>190)&(y<290)&(x>65)&(x<320)&(a[...,3]>80)
 labels,n=ndimage.label(mask);sizes=np.bincount(labels.ravel());sizes[0]=0
 if not n or sizes.max()<50:return None
 ys,xs=np.where(labels==int(sizes.argmax()));return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
def signals():
 out='assets/world/infrastructure/signal-states';src={a['id']:a for a in pack('signals')['assets']};views={a['id']:a for a in pack('signal-views')['assets']};entries=[];anims=[];maps=[];qa=[]
 dirs=['N','NE','E','SE','S','SW','W','NW'];viewidx=[5,6,3,1,0,2,3,7]
 for kind,prefix in [('electric','light'),('semaphore','semaphore')]:
  for fam in ['block','entry','exit','combo','path','oneway']:
   source=src[prefix+'-'+fam];family=Image.open(R/source['image']).convert('RGBA');fb=ivory_disc(family);files=[];states=[];req='signal-'+kind+'-'+('path-one-way'if fam=='oneway'else fam)
   for di,d in enumerate(dirs):
    vi=(4 if di in[0,1,7]else 0)if kind=='semaphore'else viewidx[di]
    va=views[prefix+'-view-'+str(vi)];base=Image.open(R/va['image']).convert('RGBA');disc=ivory_disc(base)
    if fb and disc:
     glyph=family.crop(fb);target=(disc[2]-disc[0],disc[3]-disc[1]);ratio=min(1,target[0]/glyph.width,target[1]/glyph.height);glyph=glyph.resize((max(1,round(glyph.width*ratio)),max(1,round(glyph.height*ratio))),Image.Resampling.LANCZOS)
     m=Image.new('L',glyph.size);ImageDraw.Draw(m).ellipse((1,1,glyph.width-2,glyph.height-2),fill=255);glyph.putalpha(ImageChops.multiply(glyph.getchannel('A'),m));base.alpha_composite(glyph,(disc[0]+(target[0]-glyph.width)//2,disc[1]+(target[1]-glyph.height)//2))
    # Eight logical directions use native front/side/rear views plus reflection;
    # approximate azimuth is explicitly distinct from native eight-view claim.
    for state in ['red','green']:
     im=change_glass(base,state,kind)
     if kind=='semaphore'and state=='green':
      # Authored masks for two genuine native front/back views. Logical
      # azimuth bindings share these drawings; never claim8 precise paintings.
      back=vi==4
      poly=[(50,125),(149,148),(149,187),(50,171)]if back else[(234,157),(375,171),(375,215),(234,198)]
      mask=polygon(im.size,poly);arm=extract_layer(im,mask);body=im.copy();body.putalpha(ImageChops.subtract(body.getchannel('A'),arm.getchannel('A')))
      pivot=(159,170)if back else(213,181)
      arm=arm.rotate(-58 if back else 58,Image.Resampling.BICUBIC,center=pivot);body.alpha_composite(arm);im=body
     if di==6:im=ImageOps.mirror(im)
     a=services.emit(out,req+'-'+d+'-'+state,im,[ref(source),ref(va)],'actual front/side/rear signal paintings plus native family-disc insert; complementary native glass dimming; semaphore rigid-arm geometry; eight logical azimuth bindings are shared approximate views, not eight original paintings',{'category':'signal-state','sourceRequirementIds':[req],'direction':d,'state':state,'placementSides':['left','right'],'placementSideOffsetsWorld':{'left':[-.25,0],'right':[.25,0]},'directionEvidence':'native front/side/back shared views; perpendicular direction uses symmetry/reflection; exact Unity viewpoint projection pending','status':'produced-needs-state-review'},[192,352]);entries.append(a);files.append(a['image']);states.append({'direction':d,'state':state,'image':a['image'],'placementSides':['left','right']})
   maps.append({'requirementId':req,'files':files,'states':states,'directions':dirs,'placementSides':['left','right'],'stateCount':16,'sourceViewClaim':'shared native front/side/rear plus deterministic reflection, not8 exact original views','stateTransition':'business-driven red/green selection; not a perpetual flashing animation'})
   # Comparison clip expresses state transitions, not automatic traffic logic.
   samples=[next(a['image']for a in entries if a['sourceRequirementIds']==[req]and a['direction']=='S'and a['state']==s)for s in ['red','green']]
   anims.append({'id':req+'-state-preview','category':'signals','frames':samples,'durationsMs':[700,700],'loop':False,'frameSize':[384,384],'fixedAnchorPx':[192,352],'method':'two-state comparison; actual selection depends on next-stage game signal logic','sourceRequirementIds':[req]})
 wp.writej(R/out/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':entries,'animations':anims,'coverageMappings':maps,'qa':qa,'acceptance':'192 states produced; shared-view azimuth design requires final user artwork review; Unity pending'})
 terrain.contact([a for a in entries if a['direction']=='S'],'signal-states-contact.jpg',4,230)
 terrain.contact([a for a in entries if a['sourceRequirementIds']==['signal-semaphore-entry']],'signal-directions-state-contact.jpg',4,230)
 print('signals',len(entries))
def fences():
 src={a['id']:a for a in pack('fences-shore')['assets']};entries=[];maps=[];qa=[];out='assets/world/infrastructure/fence-foundation-states'
 styles=[('wood','fence-wood',(1,1,1)),('dark-wood','fence-wood',(.73,.72,.68)),('white-wood','fence-wood',(1.15,1.13,1.05)),('stone','fence-stone',(1,1,1)),('dark-stone','fence-stone',(.72,.77,.78)),('hedge','fence-hedge',(1,1,1)),('flower-hedge','fence-hedge',(1.10,.94,1.05))]
 centres=[(192,192),(320,192),(320,256),(192,256)]
 for sty,parent,grade in styles:
  a=src[parent];raw=Image.open(R/a['image']).convert('RGBA');arr=np.asarray(raw).copy();arr[...,:3]=np.uint8(np.clip(arr[...,:3].astype(float)*np.asarray(grade),0,255));raw=Image.fromarray(arr)
  for edge in range(4):
   im=Image.new('RGBA',(512,384));part=ImageOps.mirror(raw)if edge in[1,3]else raw
   at=(centres[edge][0]-a['anchorPx'][0],centres[edge][1]-a['anchorPx'][1]);im.alpha_composite(part,tuple(map(round,at)))
   en=services.emit(out,'fence-'+sty+'-edge-'+str(edge),im,[ref(a)],'same native fence handpainted segment; symmetric perpendicular-axis reflection, edge placement and explicit material palette variant; no new original painting',{'category':'fence','style':sty,'edge':edge,'sourceRequirementIds':['terrain-fence'],'status':'produced-needs-edge-review'},[256,224]);entries.append(en)
 maps.append({'requirementId':'terrain-fence','styles':[s[0]for s in styles],'edges':list(range(4)),'files':[a['image']for a in entries],'originalMaterialCount':3,'derivedPaletteStyles':4})
 # Foundation geometry is produced separately by build_foundation_geometry.py.
 # Rejected decorative-wall proxies must not be recreated by this action.
 wp.writej(R/out/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':entries,'animations':[],'coverageMappings':maps,'qa':qa,'acceptance':'produced; placement and material contact review pending'})
 terrain.contact([a for a in entries if a['category']=='fence'],'fence-styles-contact.jpg',4,150)
 print('fences',len(entries))
def bank_piece(asset,edge):
 raw=Image.open(R/asset['image']).convert('RGBA');bb=wp.alpha_bounds(raw);piece=raw.crop(bb);scale=min(1,155/piece.width,80/piece.height);piece=piece.resize((round(piece.width*scale),round(piece.height*scale)),Image.Resampling.LANCZOS)
 if edge in[1,3]:piece=ImageOps.mirror(piece)
 return piece
def water():
 src={a['id']:a for a in pack('fences-shore')['assets']};ww={a['id']:a for a in pack('waterworks')['assets']};entries=[];maps=[];anims=[];out='assets/world/infrastructure/water-states';centres=[(192,192),(320,192),(320,256),(192,256)]
 tw=load(R/'assets/world/terrain/manifest.json');waterframes=next(a['frames']for a in tw['animations']if a['id']=='water-sea')[::3]
 waters=[Image.open(R/f).convert('RGBA')for f in waterframes]
 watersrc=[{'file':f,'sha256':wp.sha(R/f),'record':f+'.derivation.json'}for f in waterframes]
 for kind,ba in [('river',src['river-grass-bank']),('canal',src['fence-stone'])]:
  for mask in range(16):
   frames=[]
   for fi,w in enumerate(waters):
    im=Image.new('RGBA',(512,384));im.alpha_composite(w,(128,160));refs=watersrc+[ref(ba)]
    for edge in range(4):
     if mask&(1<<edge):continue
     part=bank_piece(ba,edge);p=centres[edge];im.alpha_composite(part,(p[0]-part.width//2,p[1]-round(part.height*.73)))
    en=services.emit(out,'water-'+kind+'-mask-'+format(mask,'02d')+'-frame-'+str(fi),im,refs,'native water key surface and actual native riverbank/stone wall modules; closed edges receive painted bank modules;8-key composited loop, not simulated new water detail',{'category':'water-state','connectivityMask':mask,'frame':fi,'sourceRequirementIds':['water-'+kind],'status':'produced-needs-connectivity-review','openPortOrder':['NW','NE','SE','SW']},[256,224]);entries.append(en);frames.append(en['image'])
   anims.append({'id':'water-'+kind+'-mask-'+format(mask,'02d'),'category':'water','frames':frames,'durationsMs':[300]*8,'loop':True,'frameSize':[512,384],'fixedAnchorPx':[256,224],'sourceRequirementIds':['water-'+kind],'method':'painted water-key sequence with static bank edge modules'})
  maps.append({'requirementId':'water-'+kind,'files':[a['image']for a in entries if a['sourceRequirementIds']==['water-'+kind]],'connectivityMasks':list(range(16)),'framesPerMask':8,'openPorts':['NW','NE','SE','SW']})
 # Four river flow slopes, real water art geometry plus painted rapids overlay.
 rap=ww['river-rapids'];rawrap=Image.open(R/rap['image']).convert('RGBA');bb=wp.alpha_bounds(rawrap);rawrap=rawrap.crop(bb);rawrap.thumbnail((160,120))
 for slope in[3,6,9,12]:
  frames=[]
  for fi,w in enumerate(waters):
   slopeim,pts,h=wp.projected_slope(w,slope);im=Image.new('RGBA',(512,384));im.alpha_composite(slopeim,(128,128));im.alpha_composite(rawrap,(176,174))
   en=services.emit(out,'water-river-flow-slope-'+str(slope)+'-frame-'+str(fi),im,watersrc+[ref(rap)],'piecewise-affine slope projection of painted water; actual painted rapids overlay; source8-key animation reused without new native detail',{'category':'water-state','slopeCode':slope,'frame':fi,'sourceRequirementIds':['water-river'],'status':'produced-needs-flow-review'},[256,256]);entries.append(en);frames.append(en['image'])
  anims.append({'id':'water-river-flow-'+str(slope),'category':'water','frames':frames,'durationsMs':[300]*8,'loop':True,'frameSize':[512,384],'fixedAnchorPx':[256,256],'sourceRequirementIds':['water-river'],'method':'shared painted keys on projected slope with static rapids'})
 # All18 source shoreline postures bind explicit slope/corner configurations.
 for climate,ba in [('grass',src['river-grass-bank']),('sand',src['shore-sand']),('snow',src['river-grass-bank'])]:
  for index,(code,name)in enumerate(wp.SLOPES[1:]):
   im=Image.new('RGBA',(512,384));im.alpha_composite(waters[0],(128,160));refs=watersrc+[ref(ba)]
   for edge in range(4):
    if not(code&(1<<edge)):continue
    part=bank_piece(ba,edge)
    if climate=='snow':
     arr=np.asarray(part).copy();rgb=arr[...,:3].astype(float);lum=rgb.mean(-1);green=(rgb[...,1]>rgb[...,0]*1.02)&(rgb[...,1]>rgb[...,2]*1.03);rgb[green]=lum[green,None]*.3+np.array([215,226,219])*.7;arr[...,:3]=np.uint8(np.clip(rgb,0,255));part=Image.fromarray(arr)
    p=centres[edge];im.alpha_composite(part,(p[0]-part.width//2,p[1]-round(part.height*.73)))
   en=services.emit(out,'shore-'+climate+'-source-'+format(index,'02d'),im,refs,'native shoreline strip modules composed by corner/slope binding; snow grass is selective colour grade; water remains independent animated underlay',{'category':'shore','sourceShoreIndex':index,'shoreSlopeCode':code,'shoreClimate':climate,'sourceRequirementIds':['water-shore'],'status':'produced-needs-shore-review','animationUnderlay':'water-sea24frame loop'},[256,224]);entries.append(en)
 maps.append({'requirementId':'water-shore','files':[a['image']for a in entries if a['category']=='shore'],'sourceShoreSpriteIndices':list(range(18)),'climates':['grass','sand','snow'],'animation':'water-sea underlay, shore geometry static'})
 wp.writej(R/out/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':entries,'animations':anims,'coverageMappings':maps,'qa':[],'acceptance':'produced; water connectivity/shore render review pending'})
 terrain.contact([a for a in entries if a.get('frame')==0 and a.get('connectivityMask')is not None],'water-connectivity-contact.jpg',4,150)
 terrain.contact([a for a in entries if a['category']=='shore'],'shore-postures-contact.jpg',6,140)
 print('water',len(entries))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['signals','fences','water']);a=p.parse_args();globals()[a.action]()

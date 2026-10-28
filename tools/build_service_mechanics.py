"""Fixed painted mechanical parts: gates, water levels, crossing and roadworks."""
from PIL import Image,ImageDraw,ImageChops,ImageOps,ImageFilter
from pathlib import Path
import numpy as np,json,math
import world_pack as wp
import build_world_services as s
import build_world_service_states as ss
import build_world_terrain as t
R=wp.ROOT
def main():
 obj={a['id']:a for a in s.get_pack('objects')['assets']};ww={a['id']:a for a in s.get_pack('waterworks')['assets']};entries=[];maps=[];anims=[];qa=[];out='assets/world/infrastructure/mechanics'
 # Crossing: the whole native rigid arm/attached lantern group rotates about
 # its actual hinge. The stationary rail/road surface is a separate pack.
 a=obj['crossing-barrier'];raw=Image.open(R/a['image']).convert('RGBA');mask=ss.polygon(raw.size,[(80,286),(324,316),(322,348),(80,319)])
 for poly in[[(104,318),(136,322),(136,365),(128,385),(106,385)],[(85,318),(102,318),(102,380),(85,380)],[(226,337),(254,341),(254,377),(248,403),(229,403)]]:mask=ImageChops.lighter(mask,ss.polygon(raw.size,poly))
 arm=ss.extract_layer(raw,mask);body=raw.copy();body.putalpha(ImageChops.subtract(body.getchannel('A'),arm.getchannel('A')))
 files=[]
 for axis in['X','Y']:
  frames=[]
  for fi in range(8):
   im=body.copy();moving=arm.rotate(-fi*10.5,Image.Resampling.BICUBIC,center=(332,337));im.alpha_composite(moving)
   if axis=='Y':im=ImageOps.mirror(im)
   arr=np.asarray(im).copy();arr[arr[...,3]==0,:3]=0;im=Image.fromarray(arr)
   en=s.emit(out,'crossing-'+axis+'-frame-'+str(fi),im,[s.ref(a)],'native gate boom and attached lantern group separated by authored Alpha mask; rigid2D hinge rotation over same stationary pole, perpendicular axis mirrored; no new native frames',{'category':'mechanical-animation','animationGroup':'crossing-'+axis,'frame':fi,'barrierAngleDegrees':fi*10.5,'sourceRequirementIds':['road-crossing'],'status':'produced-needs-mechanical-review','lanternMethod':'attached painted rig moves as one component; no cloth dynamics claimed'},[256,448]);entries.append(en);frames.append(en['image']);files.append(en['image'])
  for phase,seq in[('opening',frames),('closing',list(reversed(frames)))]:
   anims.append({'id':'crossing-'+axis+'-'+phase,'category':'mechanical','frames':seq,'durationsMs':[85]*8,'loop':False,'frameSize':[512,512],'fixedAnchorPx':[256,448],'sourceRequirementIds':['road-crossing'],'method':'native boom rigid hinge rotation; inverse sequence for closing'})
  maps.append({'requirementId':'road-crossing','axis':axis,'files':frames,'states':{'closed':frames[0],'open':frames[-1],'opening':frames,'closing':list(reversed(frames))},'roadRailSurface':'use separate roads/rail painted layers from infrastructure packs','stationaryHardwareSharesFrame':True})
 # Roadworks blink preview shares native construction material + warning lamp.
 cons={a['id']:a for a in s.get_pack('construction-ready')['assets']};ma=cons['construction-materials'];material=Image.open(R/ma['image']).convert('RGBA');lamp=raw.crop((307,259,381,317));frames=[]
 for fi in range(4):
  im=material.copy();part=lamp.copy()
  if fi%2:part=ImageEnhanceBrightness(part,.45)
  im.alpha_composite(part,(345,220))
  en=s.emit(out,'roadworks-frame-'+str(fi),im,[s.ref(ma),s.ref(a)],'native material stack with actual painted crossing warning-lamp crop; alternate lamp brightness for construction warning; no program-painted icon',{'category':'mechanical-animation','sourceRequirementIds':['road-works'],'frame':fi,'status':'produced-needs-mechanical-review'},[256,448]);entries.append(en);frames.append(en['image'])
 anims.append({'id':'roadworks-warning','category':'mechanical','frames':frames,'durationsMs':[240]*4,'loop':True,'frameSize':[512,512],'fixedAnchorPx':[256,448],'sourceRequirementIds':['road-works'],'method':'native lamp luminance toggle on fixed material stack'});maps.append({'requirementId':'road-works','files':frames,'signage':'native crossed gate warning icon+lamp; no text baked'})
 # Fixed walls and gate leaves from one native high-lock painting; moving
 # Water levels use three registered native inner-chamber paintings, restricted to the fixed chamber polygon.
 a=ww['lock-high'];raw=Image.open(R/a['image']).convert('RGBA')
 target={'n':(253,183),'e':(379,226),'s':(221,405),'w':(95,329)}
 quads=[[(253,202),(379,249),(221,405),(95,350)],[(253,195),(379,239),(221,405),(95,338)],list(target.values())]
 interior_keys=[];lock_sources=[]
 for key,quad in zip(['lock-low','lock-mid','lock-high'],quads):
  k=ww[key];ki=Image.open(R/k['image']).convert('RGBA');interior_keys.append(wp.warp_triangles(ki,(512,512),dict(zip(['n','e','s','w'],quad)),target,[('n','e','s'),('n','s','w')]));lock_sources.append(s.ref(k))
 # Exterior pillars, floor, flowers and walls stay in the same exact image.
 # Only three genuinely painted inner-chamber states are registered to it.
 chamber=ss.polygon(raw.size,list(target.values()));fixed=raw.copy();fixed.putalpha(ImageChops.subtract(fixed.getchannel('A'),chamber))
 gateplane=ss.polygon(raw.size,[(251,181),(382,225),(376,340),(251,296)])
 def lock_frame(height,opening,mirror):
  if height<=.5:im=Image.blend(interior_keys[0],interior_keys[1],height*2)
  else:im=Image.blend(interior_keys[1],interior_keys[2],(height-.5)*2)
  im.alpha_composite(fixed)
  if opening:
   arr=np.asarray(im);r,g,b=np.moveaxis(arr[...,:3].astype(float),-1,0)
   wood=(r>g*1.05)&(g>b*1.10)&(r>b*1.35)&(arr[...,3]>15)
   activeplane=ss.polygon(raw.size,[(251,181),(382,225),(376,round(332-height*62)),(251,round(292-height*59))])
   activeplane=ImageChops.multiply(activeplane,chamber)
   woodmask=ImageChops.multiply(Image.fromarray(np.uint8(wood)*255).filter(ImageFilter.MaxFilter(5)),activeplane)
   leaves=[]
   for li in[0,1]:
    side=Image.new('L',raw.size);ImageDraw.Draw(side).rectangle((0,0,314,511)if li==0 else(315,0,511,511),fill=255);leaf=ss.extract_layer(im,ImageChops.multiply(woodmask,side));leaves.append(leaf)
   im.putalpha(ImageChops.subtract(im.getchannel('A'),activeplane))
   for li,leaf in enumerate(leaves):
    bb=leaf.getbbox()
    if not bb:continue
    crop=leaf.crop(bb);factor=max(.10,1-opening*.9);crop=crop.resize((max(1,round(crop.width*factor)),crop.height),Image.Resampling.BICUBIC);x=bb[0]if li==0 else bb[2]-crop.width;im.alpha_composite(crop,(x,bb[1]))
  im=ImageOps.mirror(im)if mirror else im
  arr=np.asarray(im).copy();arr[arr[...,3]==0,:3]=0
  return Image.fromarray(arr)
 dirs=['NE','SE','SW','NW'];whole_states=[]
 for di,d in enumerate(dirs):
  for lev,h in[('low',0),('moving',.5),('high',1)]:
   for gate,o in[('closed',0),('open',1)]:
    im=lock_frame(h,o,di%2==1);en=s.emit(out,'lock-'+d+'-'+lev+'-'+gate,im,lock_sources,'same exact native exterior;3 actual painted water-level inner chambers registered to fixed four-corner polygon; native wooden leaf pixels Alpha-separated and compressed around hinges as explicit2D art rig; open doorway remains genuinely transparent for upstream water scenery; symmetric axis reflection',{'category':'lock-state','direction':d,'waterLevel':lev,'gateState':gate,'sourceRequirementIds':['water-lock'],'status':'produced-needs-lock-review','directionMethod':'two symmetric painted axes; opposite direction reverses upper/lower source section bindings, not a new rear-facing original','footprintTiles':[3,1],'openGateBackground':'true Alpha aperture, draw world upstream water/canal beneath it; no painted blue rectangular patch'},[256,352]);entries.append(en);whole_states.append(en);parts=[];assembled=Image.new('RGBA',im.size)
    y,x=np.mgrid[0:512,0:512];uv=x+2*y;owner=np.where(uv<790,0,np.where(uv<990,1,2))
    for section in range(3):
     for layer in['rear','front']:
      region=(owner==section)&((y<300)if layer=='rear'else(y>=300));part=im.copy();part.putalpha(ImageChops.multiply(part.getchannel('A'),Image.fromarray(np.uint8(region)*255)))
      if not part.getbbox():continue
      pn=s.emit(out,en['id']+'-'+['upper','middle','lower'][section]+'-'+layer,part,[s.ref(en)],'complementary Alpha-only section and depth-layer split of the fixed lock whole art; exactRGBA reassembly; source section order reverses for opposite travel direction',{'category':'lock-layer','direction':d,'waterLevel':lev,'gateState':gate,'section':['upper','middle','lower'][section],'layer':layer,'sourceRequirementIds':['water-lock'],'status':'produced-needs-lock-review'},[256,352]);entries.append(pn);assembled.alpha_composite(part);parts.append(pn['image'])
    qa.append({'id':en['id']+'.section-layers','level':'OK'if np.array_equal(np.asarray(im),np.asarray(assembled))else'FAIL','exactRGBAReassembly':True})
    maps.append({'requirementId':'water-lock','direction':d,'waterLevel':lev,'gate':gate,'whole':en['image'],'files':[en['image']]+parts,'sectionOrder':(['upper','middle','lower']if di<2 else['lower','middle','upper']),'renderRule':'choose whole or complementary layers; never both'})
  frames=[]
  for fi in range(12):
   h=fi/11;im=lock_frame(h,0,di%2==1);en=s.emit(out,'lock-'+d+'-fill-frame-'+format(fi,'02d'),im,lock_sources,'same fixed native outer chamber and3 registered actual painted water-level interiors;12 crossfade samples restricted to inner chamber; not new native animation or fluid simulation',{'category':'lock-animation','direction':d,'frame':fi,'sourceRequirementIds':['water-lock'],'status':'produced-needs-lock-review'},[256,352]);entries.append(en);frames.append(en['image'])
  anims.append({'id':'lock-'+d+'-fill','category':'water','frames':frames,'durationsMs':[130]*12,'loop':False,'frameSize':[512,512],'fixedAnchorPx':[256,352],'sourceRequirementIds':['water-lock'],'method':'same fixed chamber/closed gate; restricted inner-chamber crossfade between3 registered actual native low/mid/high paintings; fixed exterior, no fluid simulation'})
  anims.append({'id':'lock-'+d+'-drain','category':'water','frames':list(reversed(frames)),'durationsMs':[130]*12,'loop':False,'frameSize':[512,512],'fixedAnchorPx':[256,352],'sourceRequirementIds':['water-lock'],'method':'reverse registered native inner-chamber key sequence; fixed exterior, no fluid simulation'})
 # Dock six layout bindings and buoy/depot two axes use painted native modules.
 dockfiles=[]
 for name in['dock-quay','dock-pier','buoy','ship-depot']:
  a=ww[name];im=Image.open(R/a['image']).convert('RGBA')
  for axis in['X','Y']:
   part=ImageOps.mirror(im)if axis=='Y'else im
   en=s.emit(out,name+'-axis-'+axis,part,[s.ref(a)],'actual native whole water-transport module; symmetric perpendicular axis reflection only',{'category':'water-facility','sourceRequirementIds':['station-buoy'if name=='buoy'else'depot-ship'if name=='ship-depot'else'station-dock'],'axis':axis,'status':'produced-needs-facility-review'},a['anchorPx']);entries.append(en);dockfiles.append(en)
 for req,ids in[('station-dock',['dock-quay','dock-pier']),('station-buoy',['buoy']),('depot-ship',['ship-depot'])]:
  group=[a for a in dockfiles if any(a['id'].startswith(i)for i in ids)];maps.append({'requirementId':req,'files':[a['image']for a in group],'layouts':list(range(6))if req=='station-dock'else list(range(2))if req=='depot-ship'else[0],'sourceModuleComposition':'land quay + water pier and symmetry; runtime shape footprint remains source-driven'})
 manifest={'schema':'cloud-route.world-art.v1','assets':entries,'animations':anims,'coverageMappings':maps,'qa':qa,'acceptance':'produced; mechanical/gate fixed-geometry contact review pending','unityValidated':False,'limitations':['Gate leaf turning is an explicit2D hinge/compression art rig; it is not a physically simulated3D gate.','A lock source direction uses symmetric visual axes plus reversed section metadata; source business travel/ship logic is next-stage.','Native water and foundation pixels remain shared; no video-generation claim.']}
 # Viewport assembly fills the real Alpha doorway from ordinary painted
 # world-water tiles; the formal sprite keeps the aperture transparent.
 viewport=[];wpng=R/'assets/world/terrain/water-sea-frame-00.png';wi=Image.open(wpng).convert('RGBA')
 for en in whole_states:
  painted=Image.open(R/en['image']).convert('RGBA');canvas=Image.new('RGBA',(512,512));under=Image.new('RGBA',(512,512))
  under.alpha_composite(wi,(128,128));under.alpha_composite(wi,(256,192))
  if en['direction']in['SE','NW']:under=ImageOps.mirror(under)
  if en['gateState']=='open':
   closed=next(x for x in whole_states if x['direction']==en['direction']and x['waterLevel']==en['waterLevel']and x['gateState']=='closed');ci=Image.open(R/closed['image']).convert('RGBA');gap=ImageChops.subtract(ci.getchannel('A'),painted.getchannel('A'));under.putalpha(ImageChops.multiply(under.getchannel('A'),gap));canvas.alpha_composite(under)
  canvas.alpha_composite(painted);p=R/'previews/world/lock-assemblies'/(en['id']+'.png');p.parent.mkdir(parents=True,exist_ok=True);canvas.save(p)
  wp.writej(str(p)+'.derivation.json',{'file':wp.rel(p),'sha256':wp.sha(p),'derivedFrom':[s.ref(en),{'file':wp.rel(wpng),'sha256':wp.sha(wpng),'record':wp.rel(wpng)+'.derivation.json'}],'operation':'actual formal lock Alpha over actual adjacent world-water tiles; fill only open-gate aperture; viewport assembly preview, not new painting'})
  en['assemblyPreview']=wp.rel(p);viewport.append({**en,'image':wp.rel(p)})
 manifest['lockViewportAssembly']={'waterTiles':[{'image':wp.rel(wpng),'offsetPx':[128,128]},{'image':wp.rel(wpng),'offsetPx':[256,192]}],'mask':'closed-state Alpha minus open-state Alpha; mirror for SE/NW','renderRule':'normal terrain/canal water beneath actual transparent gate opening; do not bake a blue panel in the gate sprite'}
 wp.writej(R/out/'manifest.json',manifest);t.contact([a for a in entries if a['id'].startswith('crossing-')],'crossing-states-contact.jpg',4,220);t.contact([a for a in viewport if a['direction']in['NE','SE']],'lock-states-contact.jpg',4,220)
 print(json.dumps({'assets':len(entries),'animations':len(anims),'lockStateGroups':len(whole_states),'reassemblyFailures':sum(a['level']=='FAIL'for a in qa)},ensure_ascii=False))
def ImageEnhanceBrightness(im,factor):
 from PIL import ImageEnhance
 return ImageEnhance.Brightness(im).enhance(factor)
if __name__=='__main__':main()

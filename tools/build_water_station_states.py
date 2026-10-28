"""Six source dock roles and buoy layers from current painted water modules."""
from PIL import Image,ImageDraw,ImageOps,ImageChops
import numpy as np
import world_pack as wp
import build_world_services as s
import build_world_service_states as ss
import build_world_terrain as terrain
R=wp.ROOT
def main():
 q=s.get_pack('waterworks');src={a['id']:a for a in q['assets']};entries=[];maps=[];qa=[];out='assets/world/infrastructure/water-stations'
 roles=[(0,'dock-quay','NE',False,'shore-head'),(1,'dock-quay','SE',True,'shore-head'),(2,'dock-quay','SW',False,'shore-head'),(3,'dock-quay','NW',True,'shore-head'),(4,'dock-pier','X',False,'water-pier'),(5,'dock-pier','Y',True,'water-pier')]
 for req,parts in [('station-dock',roles),('station-buoy',[(0,'buoy','single',False,'navigation-marker')])]:
  states=[]
  for layout,key,d,mirror,role in parts:
   a=src[key];raw=Image.open(R/a['image']).convert('RGBA');raw=ImageOps.mirror(raw)if mirror else raw;w,h=raw.size;anchor=a['anchorPx'].copy()
   if mirror:anchor[0]=w-anchor[0]
   op='actual native painted '+key+'; '+('symmetric horizontal reflection; 'if mirror else '')+'explicit source-layout role; opposite travel directions share declared art axis, not newly painted rear views; complementary Alpha depth ownership'
   whole=s.emit(out,req+'-layout-'+str(layout),raw,[ss.ref(a)],op,{'category':'water-station','sourceRequirementIds':[req],'layout':layout,'direction':d,'role':role,'status':'produced-needs-visual-review','nativeViewClaim':'one native source view plus symmetric axis; source travel orientations are explicit metadata'},anchor);entries.append(whole)
   # Foreground water-facing footing occupies the source lower depth band.
   # This is exclusive Alpha ownership, never a painted replacement wall.
   cut=round(h*(.75 if key=='dock-quay'else .69));mask=Image.new('L',raw.size);ImageDraw.Draw(mask).polygon([(0,cut-20),(w,cut+20),(w,h),(0,h)],fill=255)
   layers={};composite=Image.new('RGBA',raw.size)
   for name,m in [('rear',ImageChops.invert(mask)),('front',mask)]:
    im=raw.copy();im.putalpha(ImageChops.multiply(raw.getchannel('A'),m));arr=np.asarray(im).copy();arr[arr[...,3]==0,:3]=0;im=Image.fromarray(arr)
    en=s.emit(out,whole['id']+'-'+name,im,[ss.ref(whole)],'exclusive Alpha depth partition of actual whole dock/buoy artwork; unchanged paint; no separate native original',{'category':'water-station','sourceRequirementIds':[req],'layout':layout,'direction':d,'layer':name,'status':'produced-needs-visual-review'},anchor);entries.append(en);layers[name]=en['image'];composite.alpha_composite(im)
   # Ignore hidden RGB of native source while checking exact visible pixels.
   ar=np.asarray(raw).copy();ar[ar[...,3]==0,:3]=0
   qa.append({'id':whole['id']+'.layer-reassembly','level':'OK'if np.array_equal(np.asarray(composite),ar)else'FAIL','exactVisibleRGBA':True})
   states.append({'layout':layout,'direction':d,'role':role,'image':whole['image'],'layers':layers,'renderRule':'whole or rear/front partition, never both','sourceViewClaim':'opposite travel directions share same native axis artwork; no new rear-facing painting'})
  maps.append({'requirementId':req,'files':[a['image']for a in entries if req in a['sourceRequirementIds']],'states':states,'sourceLayouts':len(parts),'frontRearLayers':True,'completeVariantCoverage':True,'nativeViewClaim':'same approved painted body reused by role; two symmetric visual axes, not four independent rear/front paintings','renderStrategy':'large painted dock terminal overlay once at shore anchor; original6sprite roles mapped to4head directions plus2pier axes; no repeated whole building per underlying tile'if req=='station-dock'else'single native buoy marker with complementary front waterline ownership'})
 wp.writej(R/out/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':entries,'animations':[],'coverageMappings':maps,'qa':qa,'unityValidated':False,'limitations':['Original source sprite roles are explicit layout bindings, not6 independent native paintings.','Engine draw sorting and vessel occlusion require next-stage Unity validation.']})
 terrain.contact([a for a in entries if not a.get('layer')],'water-station-layouts-contact.jpg',3,230)
 print('water-station PNG',len(entries),'checks',qa)
if __name__=='__main__':main()

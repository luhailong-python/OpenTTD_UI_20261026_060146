"""Measured ownership / registration after actual inspection of all8 atlases."""
from PIL import Image
from scipy import ndimage
import numpy as np
import manager_face_parts as p
R=p.R;cfg=p.load(R/'config/manager-customization.json');cfg['atlases']=cfg['atlases'][:1]
def cores(file):
 ar=np.asarray(Image.open(R/file).convert('RGBA'));lab,n=ndimage.label(ar[:,:,3]>128);sz=np.bincount(lab.ravel());out=[]
 for label,obj in enumerate(ndimage.find_objects(lab),1):
  if obj and sz[label]>150:out.append([obj[1].start,obj[0].start,obj[1].stop,obj[0].stop])
 return out
def add(file,family,rects,targets=None,registrations=None,explicit=None,offset=0):
 file='source-art/manager-customization/'+file+'.png';cc=cores(file);cells=[]
 for i,rect in enumerate(rects):
  chosen=explicit[i]if explicit else[b for b in cc if rect[0]<(b[0]+b[2])/2<rect[2]and rect[1]<(b[1]+b[3])/2<rect[3]]
  cell={'id':'mf-'+family+'-'+str(i+offset).zfill(2),'index':i+offset,'box':rect,'coreComponentBoxes':chosen}
  if targets:cell['targetGuideRectPx']=targets[i]if isinstance(targets[0],list)else targets
  if registrations:cell['registration']=registrations[i]
  if family=='eyes':cell['closedIrisSides']=['left','right']if i in[2,15]else['right']if i==9 else[]
  if family in['cape','jadepin']:cell['supplemental']=True
  if not chosen:raise ValueError('actual components absent: '+str(cell))
  cells.append(cell)
 cfg['atlases'].append({'file':file,'family':family,'actualSourceComponentsRead':True,'cells':cells})
# Actual visible rows are not equal grid cuts. The following bands include all
# native eyebrows/eyes and exclude the next row; ownership uses true components.
add('eyes','eyes',[[x0,y0,x1,y1]for y0,y1 in[(95,325),(350,555),(585,790),(815,1015)]for x0,x1 in[(0,380),(380,750),(750,1130),(1130,1491)]])
add('noses','nose',[[x0,y0,x1,y1]for y0,y1 in[(190,465),(535,835)]for x0,x1 in[(80,380),(500,830),(930,1285),(1370,1730)]])
add('mouths','mouth',[[x0,y0,x1,y1]for y0,y1 in[(150,390),(455,680),(750,940)]for x0,x1 in[(15,355),(380,720),(755,1100),(1120,1435)]])
hb=[[44,13,551,387],[576,4,939,394],[1037,23,1522,419],[36,364,506,719],[528,406,1008,727],[1052,359,1522,741],[48,695,475,992],[562,682,979,1015],[1054,696,1464,990]]
ha=[(270,90),(764,100),(1277,102),(270,455),(770,435),(1284,446),(266,716),(770,768),(1275,768)]
rects=[[max(0,b[0]-8),max(0,b[1]-8),min(1536,b[2]+8),min(1024,b[3]+8)]for b in hb];reg=[{'scale':.70,'sourceAnchorWithinCellPx':[x-box[0],y-box[1]],'destinationAnchorPx':[256,70],'anchorMeaning':'measured native main scalp crown centre, independent of topknot/ribbon bounds'}for(x,y),box in zip(ha,rects)]
add('hair','hair',rects,registrations=reg,explicit=[[b]for b in hb])
for cell in cfg['atlases'][-1]['cells']:cell['faceFrameFit']={'fixedCrownY':70,'belowCrownYScale':1/.70,'lowerFrameXScale':1.25,'purpose':'match actual base forehead/ears/chin; topknot stays fixed, native source y scale remains<=1 and x<=.875'}
cfg['atlases'][-1]['cells'][1]['registration']['destinationAnchorPx'][1]=75
cfg['atlases'][-1]['cells'][1]['faceFrameFit']['fixedCrownY']=75
br=[[0,80,740,670],[740,70,1430,640],[1420,70,2172,724]];ba=[(370,200,.22),(1082,143,.23),(1804,155,.20)];reg=[{'scale':scale,'sourceAnchorWithinCellPx':[x-box[0],y-box[1]],'destinationAnchorPx':[256,287],'anchorMeaning':'actual central moustache/nose contact, not full beard bounding-box centre'}for(x,y,scale),box in zip(ba,br)]
add('beards','beard',br,registrations=reg)
cb=[[4,73,538,390],[510,70,1013,383],[990,68,1535,386],[123,435,447,673],[607,442,929,673],[1085,431,1458,664],[39,722,484,950],[492,700,1019,959],[1014,701,1512,961]]
rects=[[max(0,b[0]-6),max(0,b[1]-6),min(1536,b[2]+6),min(1024,b[3]+6)]for b in cb]
add('clothes','robe',rects[:3],targets=[103,326,409,494],explicit=[[b]for b in cb[:3]])
add('clothes','collar',rects[3:7],targets=[166,318,346,450],explicit=[[b]for b in cb[3:7]])
add('clothes','cape',rects[7:],targets=[103,326,409,478],explicit=[[b]for b in cb[7:]])
add('accessories','tie',[[0,30,407,480],[400,30,725,480],[730,20,1045,480],[1048,20,1448,480],[0,480,410,780],[415,480,640,780]])
gr=[[640,520,1045,720],[1045,530,1448,715]];ga=[(841,619),(1246,620)];reg=[{'scale':.58,'sourceAnchorWithinCellPx':[x-box[0],y-box[1]],'destinationAnchorPx':[256,236],'anchorMeaning':'actual lens bridge, paired lenses matched to actual eyes'}for(x,y),box in zip(ga,gr)]
add('accessories','glasses',gr,registrations=reg)
# Earring pairs have independently registered left/right mother pieces. Scaling
# the whole pair would pull the earrings into the middle of the face.
file='source-art/manager-customization/accessories.png';ec=[[[53,809,121,965],[246,809,315,965]],[[407,789,501,1028],[578,789,672,1028]],[[748,835,842,962],[920,835,1015,963]]];cells=[]
for n,pair in enumerate(ec):
 pieces=[]
 for side,b in enumerate(pair):pieces.append({'box':[b[0]-8,b[1]-8,b[2]+8,b[3]+8],'coreComponentBoxes':[b],'targetGuideRectPx':[110,267,142,343]if side==0 else[370,267,402,343]})
 cells.append({'id':'mf-earring-'+str(n).zfill(2),'index':n,'pieces':pieces})
cfg['atlases'].append({'file':file,'family':'earring','cells':cells})
add('accessories','jadepin',[[1070,700,1448,1065]],targets=[280,58,442,209],explicit=[[[1097,727,1436,1042]]])
cfg['status']='All8 actual native atlases inspected;73 mother parts (70core+3declared supplemental); measured component ownership and registration'
p.savej(R/'config/manager-customization.json',cfg)
print('actual mother cells',sum(len(a['cells'])for a in cfg['atlases']))

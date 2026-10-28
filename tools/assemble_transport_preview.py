from pathlib import Path
from PIL import Image
import json,hashlib,random
R=Path(__file__).resolve().parents[1];W,H=1920,1080;tw,th=112,56;ox,oy=960,70
out=Image.new('RGBA',(W,H),'#24483e');sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(i,j):return ox+(j-i)*tw/2,oy+(i+j)*th/2
def paint(path,x,y,anchor,scale):
 p=R/path;im=Image.open(p).convert('RGBA');sources[path]={'file':path,'sha256':sha(p),'record':path+'.derivation.json'}
 im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 out.alpha_composite(im,(round(x-anchor[0]*scale),round(y-anchor[1]*scale)))
def tile(path,i,j):
 x,y=pos(i,j);paint(path,x,y,[128,64],tw/256)
grass='assets/world/terrain/terrain-grass-flat.png';bare='assets/world/terrain/terrain-bare-flat.png';field='assets/world/terrain/terrain-field-flat.png';water='assets/world/terrain/water-sea-frame-00.png'
for s in range(33):
 for i in range(17):
  j=s-i
  if not 0<=j<17:continue
  tile(water if i>=15 else field if i<3 and j>12 else grass,i,j)
for i in range(1,15):
 tile('assets/world/infrastructure/roads/road-mask-'+('15'if i==7 else'10')+'.png',i,8)
for j in range(2,15):
 if j!=8:tile('assets/world/infrastructure/roads/road-mask-05.png',7,j)
for j in range(1,15):tile('assets/world/infrastructure/rail/rail-rail-mask-02-normal.png',13,j)
props=[]
def add(path,i,j,anchor=[256,448],scale=.42):
 props.append((i+j,i,j,path,anchor,scale))
house=json.loads((R/'assets/world/houses/manifest.json').read_text(encoding='utf-8'))
for i,j,slug in [(3,7,'thatched-cottage'),(4,7,'timber-rowhouse'),(5,7,'courtyard-dwelling'),(6,10,'food-market'),(5,10,'teahouse'),(8,5,'townhall'),(9,5,'courtyard-mansion'),(9,10,'pavilion-apartments'),(8,11,'post-office'),(10,10,'clinic')]:
 path=next((p.relative_to(R).as_posix()for p in (R/'assets/world/houses/families').rglob('house-family-'+slug+'.png')),None)
 if path:add(path,i,j)
for i,j,slug in [(11,3,'coal-mine'),(11,12,'sawmill'),(4,13,'farm')]:
 p=R/'assets/world/industries'/(slug+'.png')
 if p.exists():add(p.relative_to(R).as_posix(),i,j,scale=.5)
for i,j,asset in [(13,9,'rail-station-hall'),(13,10,'rail-canopy'),(13,11,'rail-platform'),(6,8,'bus-bay'),(8,8,'truck-bay'),(13,14,'rail-depot-view-NW')]:
 add('assets/world/infrastructure/transport/'+asset+'.png',i,j,scale=.43)
rng=random.Random(26)
for i in range(1,14):
 for j in range(1,15):
  if (i<3 and j<7)or(j<3 and i<11)or(i>9 and j>13)or rng.random()<.025:
   n=rng.randrange(12);add('assets/world/vegetation/mature/tree-'+format(n,'02d')+'.png',i,j,[128,336],.4)
for family,i,j,direction in [('loco-steam',13,5,'SE'),('wagon-passenger',13,4,'SE'),('wagon-passenger',13,3,'SE'),('road-bus',7,7,'SE'),('road-truck-box',9,8,'SW'),('ship-cargo',15,11,'SE')]:
 p=R/'assets/world/vehicles/families'/family/(direction+'.png')
 if not p.exists():continue
 m=json.loads((p.parent/'manifest.json').read_text());f=next(f for f in m['frames']if f['direction']==direction);pivot=f['pivot']
 add(p.relative_to(R).as_posix(),i,j,[pivot[0]*512,(1-pivot[1])*512],.24 if family.startswith('loco')or family.startswith('wagon')else.27)
for _,i,j,path,anchor,scale in sorted(props):
 x,y=pos(i,j);paint(path,x,y+th/2,anchor,scale)
p=R/'previews/world/assembled-transport-town.png';out.convert('RGB').save(p)
Path(str(p)+'.derivation.json').write_text(json.dumps({'file':p.relative_to(R).as_posix(),'sha256':sha(p),'width':W,'height':H,'operation':'Data-authored 17x17 representative transport-town arrangement; composites only existing native/derived art, downscales and uses fixed art anchors; not native generated panorama, not Unity or gameplay implementation','derivedFrom':list(sources.values()),'geometry':{'tile':[tw,th],'formalSourceTile':[256,128],'worldOrigin':[ox,oy]},'purpose':'art contact/scale review; representative composition only, not full game content proof'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Preview built',len(sources),'painted source PNGs')

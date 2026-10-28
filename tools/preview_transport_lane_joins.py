"""1:1 actual PNG lane join review, including rail (no painted geometry)."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'previews/world/transport-lanes';m=json.loads((R/'assets/world/infrastructure/transport-runtime/manifest.json').read_text(encoding='utf-8'));b={a['id']:a for a in m['assets']}
out=Image.new('RGB',(1200,900),'#eae5d8');d=ImageDraw.Draw(out);font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16);sources=[]
for i,(family,axis,deck)in enumerate([('00-wood','X','rail'),('01-concrete','X','rail'),('09-girder','X','rail'),('10-tubular','Y','rail'),('00-wood','X','road'),('01-concrete','Y','road')]):
 aid='bridge-'+family+'-'+axis+'-'+deck;a=b[aid];im=Image.open(R/a['image']).convert('RGBA');can=Image.new('RGBA',(850,650));xy=[50 if axis=='X'else 430,50]
 for n in range(3):can.alpha_composite(im,(xy[0]+n*(128 if axis=='X'else-128),xy[1]+n*64))
 crop=can.crop(can.getbbox());tile=Image.new('RGBA',(600,270),'#23433b'if i%2 else'#eae5d8');tile.alpha_composite(crop,((600-crop.width)//2,(270-crop.height)//2));x=i%2*600;y=i//2*300;out.paste(tile.convert('RGB'),(x,y));d.text((x+10,y+273),aid+' / 3x, native pixels',font=font,fill='#12392f');sources.append({'file':a['image'],'sha256':a['sha256']})
p=O/'lane-joins-native.jpg';out.save(p,quality=98);Path(str(p)+'.derivation.json').write_text(json.dumps({'operation':'Three registered whole PNG repeats at actual projected advance; no resize, no new painting','derivedFrom':sources},indent=2),encoding='utf-8')

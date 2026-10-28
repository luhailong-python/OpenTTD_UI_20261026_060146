from pathlib import Path
from PIL import Image,ImageDraw
import build_transport_runtime as t
R=t.R
can=Image.new('RGB',(1536,1536),'#ddd7ca')
for i,(k,pts) in enumerate(t.LANDMARKS.items()):
 im=t.img('bridge-'+k+'-span');bg=Image.new('RGBA',im.size,'#ddd7ca');bg.alpha_composite(im);d=ImageDraw.Draw(bg)
 for p in pts:d.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill='red')
 can.paste(bg.convert('RGB'),(i%3*512,i//3*512))
can.save(R/'previews/world/bridge-landmarks-qa.jpg',quality=97)
im=Image.open(R/'previews/world/bridge-joins.jpg');im.crop((0,0,1440,1440)).save(R/'previews/world/bridge-joins-page1.jpg',quality=96)

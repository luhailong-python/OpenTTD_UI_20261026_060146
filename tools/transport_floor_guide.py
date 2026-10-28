from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'E:\work\image\OpenTTD_UI_20261026_060146');O=R/'records/world-production';out=Image.new('RGB',(1536,560),'#e7e1ce');font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),11)
paths=['assets/world/infrastructure/transport/tunnel-portal-SE.png','assets/world/infrastructure/transport/tunnel-portal-SW.png','assets/world/infrastructure/transport-runtime/bridge-00-wood-X-road.png']
for i,p in enumerate(paths):
 im=Image.new('RGBA',(512,512),'#29443c');s=Image.open(R/p).convert('RGBA');im.alpha_composite(s);d=ImageDraw.Draw(im)
 for x in range(0,512,16):d.line((x,0,x,511),fill='#927f51');d.text((x+1,0),str(x),font=font,fill='white')
 for y in range(0,512,16):d.line((0,y,511,y),fill='#927f51');d.text((1,y+1),str(y),font=font,fill='white')
 out.paste(im.convert('RGB'),(i*512,0));ImageDraw.Draw(out).text((i*512+10,520),p.split('/')[-1],font=font,fill='black')
out.save(O/'transport-floor-coordinate-guide.jpg',quality=97)

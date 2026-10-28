from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'E:\work\image\OpenTTD_UI_20261026_060146');im=Image.new('RGBA',(512,512),'#e7e1ce');im.alpha_composite(Image.open(R/'assets/world/infrastructure/transport/tunnel-portal-SE.png').convert('RGBA'));crop=im.crop((240,330,430,450)).resize((950,600));d=ImageDraw.Draw(crop);f=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),13)
for x in range(240,431,8):xx=(x-240)*5;d.line((xx,0,xx,599),fill='#757257');d.text((xx+1,0),str(x),font=f,fill='black')
for y in range(330,451,8):yy=(y-330)*5;d.line((0,yy,949,yy),fill='#757257');d.text((1,yy+1),str(y),font=f,fill='black')
crop.convert('RGB').save(R/'records/world-production/tunnel-se-floor-detail.jpg',quality=97)

from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'E:\work\image\OpenTTD_UI_20261026_060146');names=['coal-mine','oil-well','toy-factory','plastic-fountains','toffee-quarry','sugar-mine'];out=Image.new('RGB',(1536,1120),'#e7e1ce');font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),13)
for i,n in enumerate(names):
 im=Image.new('RGBA',(512,512),'#293e38');im.alpha_composite(Image.open(R/'assets/world/industries'/(n+'.png')).convert('RGBA'));d=ImageDraw.Draw(im)
 for x in range(0,512,32):d.line((x,0,x,511),fill='#bca669',width=1);d.text((x+1,0),str(x),font=font,fill='white')
 for y in range(0,512,32):d.line((0,y,511,y),fill='#bca669',width=1);d.text((1,y+1),str(y),font=font,fill='white')
 x=i%3*512;y=i//3*560;out.paste(im.convert('RGB'),(x,y));ImageDraw.Draw(out).text((x+10,y+516),n,font=font,fill='black')
out.save(R/'records/world-production/industry-binding-coordinate-guide.jpg',quality=95)

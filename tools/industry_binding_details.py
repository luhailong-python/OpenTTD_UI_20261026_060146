from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'E:\work\image\OpenTTD_UI_20261026_060146')
names=['toy-factory','plastic-fountains','toffee-quarry','sugar-mine'];boxes=[(210,216,306,344),(113,212,350,355),(221,213,288,306),(237,248,359,366)]
out=Image.new('RGB',(1280,640),'#e7e1ce');font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),15)
for i,(n,b)in enumerate(zip(names,boxes)):
 a=Image.new('RGBA',(512,512),'#e7e1ce');a.alpha_composite(Image.open(R/'assets/world/industries'/(n+'.png')).convert('RGBA'));piece=a.crop(b);piece.thumbnail((600,580));s=min(600/piece.width,580/piece.height);piece=piece.resize((round(piece.width*s),round(piece.height*s)))
 x=(i%2)*640;y=(i//2)*320
 piece.thumbnail((620,280));out.paste(piece.convert('RGB'),(x,y));ImageDraw.Draw(out).text((x+8,y+282),n+' crop'+str(b),font=font,fill='black')
out.save(R/'records/world-production/industry-part-details.jpg',quality=96)

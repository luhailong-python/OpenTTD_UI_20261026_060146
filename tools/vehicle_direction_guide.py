from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,json
R=Path(r"E:\work\image\OpenTTD_UI_20261026_060146")
base=R/"assets/world/vehicles"
for p in [base,base/"families",base/"models",R/"records/vehicles",R/"previews/vehicles"]:p.mkdir(parents=True,exist_ok=True)
im=Image.new("RGB",(2048,1024),"#F4F2E7");d=ImageDraw.Draw(im)
f=ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf",25);b=ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf",31)
dirs=[("N",0,-1,"REAR; nose away UP"),("NE",1,-1,"REAR-RIGHT; nose UP-RIGHT"),("E",1,0,"RIGHT PROFILE; nose RIGHT"),("SE",1,1,"FRONT-RIGHT; nose DOWN-RIGHT"),("S",0,1,"FRONT; nose toward DOWN"),("SW",-1,1,"FRONT-LEFT; nose DOWN-LEFT"),("W",-1,0,"LEFT PROFILE; nose LEFT"),("NW",-1,-1,"REAR-LEFT; nose UP-LEFT")]
for i,(name,vx,vy,meaning)in enumerate(dirs):
 x=i%4*512;y=i//4*512
 d.rectangle((x+4,y+4,x+508,y+508),outline="#BAC9BA",width=3)
 d.text((x+22,y+16),str(i+1)+" / "+name,font=b,fill="#1B5F47")
 d.text((x+22,y+65),meaning,font=f,fill="#275D4C")
 # Heading indicator is a generation guide, not production artwork.
 cx=x+256;cy=y+290;L=130;mag=math.hypot(vx,vy);ux=vx/mag;uy=vy/mag;ex=cx+ux*L;ey=cy+uy*L
 d.line((cx-ux*60,cy-uy*60,ex,ey),fill="#C87935",width=15)
 p=(ex-ux*40,ey-uy*40);d.polygon([(ex,ey),(p[0]-uy*25,p[1]+ux*25),(p[0]+uy*25,p[1]-ux*25)],fill="#C87935")
 d.text((x+30,y+457),"BODY CENTER  /  transparent export",font=f,fill="#738273")
im.save(R/"records/vehicles/direction-guide.png")
print("guide ready")


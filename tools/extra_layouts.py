"""Additional player interaction overlays, all using supplied painted controls."""
from PIL import Image,ImageDraw
import re
def render_extra(r,im,s):
 sid=s["id"]
 if sid in ['13-rail-signals','17-bridge']:
  r.row(im,365,310,660,532)
  r.txt(im,'信号类型' if sid.startswith('13') else '可用桥型',397,329,30,r.JADE,bold=True,title=True)
  rows=s['rows']
  for i,entry in enumerate(rows):
   yy=390+i*142;r.row(im,390,yy,610,130,i==0)
   color=r.IVORY if i==0 else r.JADE
   r.icon(im,'signal' if sid.startswith('13') else 'bridge',411,yy+18,92)
   r.txt(im,entry[0],527,yy+15,28,color,bold=True,w=430)
   r.txt(im,'  ·  '.join(entry[1:]),527,yy+72,22,color,w=430)
  pic=r.cover(r.asset('assets/world-viewport.png'),700,380);r.paste(im,pic,1055,310)
  yy=717
  for d in s['details'][:3]:
   yy+=r.para(im,d,1075,yy,645,23,maxlines=2,gap=6)+14
  return im
 if sid=="98-chat":
  r.row(im,365,310,1390,475)
  yy=342
  lines=[("全部公司","青岚客","铁路接通该站后，新增一班旅客列车。"),("本公司","云游子","中央站已有邮件，请检查装卸指令。"),("私聊","江海客","收到，货车已前往车库。")]
  for channel,name,msg in lines:
   r.icon(im,"network",397,yy+2,52)
   r.txt(im,channel+"  ·  "+name,474,yy,22,r.JADE,bold=True)
   r.txt(im,msg,474,yy+42,26,r.TEXT,w=1200)
   r.line(im,397,yy+100,1718,yy+100,"#D8C9A2");yy+=139
  r.inputbox(im,365,794,242,56,"全部公司",22)
  r.inputbox(im,627,794,1128,56,"输入消息…",24)
  return im
 if sid=="07-save-game":
  r.table(im,s,365,310,950,430)
  r.detail_card(im,s,1360,310,395,535)
  r.txt(im,"文件名",386,769,24,r.JADE,bold=True)
  r.inputbox(im,510,752,802,70,"云途运输_1956-06.sav",25)
  return im
 if sid=="83-cargo-chain":
  r.txt(im,"产业与货物的运输联系",397,321,31,r.JADE,bold=True)
  # Diagram is a functional overlay; pictures are genuine delivered sprites.
  nodes=[("煤矿","coal",411,414),("发电厂","industry",1150,414),("森林","wood",411,662),("锯木厂","industry",1150,662)]
  for title,ico,x,y in nodes:
   r.row(im,x,y,510,163);r.icon(im,ico if ico=="industry" else "cargo",x+22,y+28,100)
   if ico!="industry":
    r.contain(im,"assets/cargo/"+ico+".png",x+22,y+28,100,100)
   r.txt(im,title,x+145,y+28,30,r.JADE,bold=True)
   r.txt(im,"产出煤炭" if title=="煤矿" else "接受煤炭" if title=="发电厂" else "产出木材" if title=="森林" else "接受木材 · 产出货物",x+145,y+88,22,r.MUTED,w=340)
  for y,label in [(495,"煤炭"),(743,"木材")]:
   r.line(im,932,y,1130,y,r.GOLD,5);ImageDraw.Draw(im).polygon([(1131,y),(1113,y-10),(1113,y+10)],fill=r.GOLD)
   r.txt(im,label,1030,y-46,22,r.JADE,align="center")
  return im
 if sid in ["113-script-debug","135-console"]:
  r.row(im,365,310,1390,480)
  log=Image.new("RGBA",(1330,405),"#173D34");r.paste(im,log,395,337)
  if sid=="113-script-debug":
   lines=["[00:12] 信息  脚本已启动","[00:13] 信息  正在创建首条线路","[00:15] 警告  目标站已被拆除","[00:16] 信息  等待重新选择目的地"]
  else:lines=["> help","可用操作：help / list_settings / echo","输入指令后按 Enter 执行。","历史记录：使用上、下方向键浏览。"]
  for j,l in enumerate(lines):r.txt(im,l,426,372+j*69,25,"#E8E8CB",w=1240)
  r.inputbox(im,365,802,1390,53,"> 输入命令…" if sid=="135-console" else "筛选日志…",23)
  return im
 return None


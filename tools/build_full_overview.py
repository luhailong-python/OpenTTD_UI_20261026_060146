from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,hashlib
R=Path(__file__).resolve().parents[1];W,H=3200,2380
out=Image.new('RGB',(W,H),'#f2ebd9');d=ImageDraw.Draw(out)
fontpath=str(R/'assets/fonts/NotoSansSC-Variable.ttf');font=lambda n:ImageFont.truetype(fontpath,n)
d.rounded_rectangle((48,36,3152,208),28,fill='#255548',outline='#bea367',width=3)
d.text((88,59),'云途万里（暂名） · 道家 Q 版完整美术预览',font=font(52),fill='#fff0ca')
d.text((92,137),'OpenTTD 功能参考｜UI 整屏 · 世界模块 · 建筑 · 交通载具 · 状态与动画',font=font(28),fill='#d5ddbc')
sources=[]
def card(path,box,label,fit='contain'):
 p=R/path;im=Image.open(p).convert('RGB');sources.append({'file':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 x,y,w,h=box;d.rounded_rectangle((x,y,x+w,y+h+64),16,fill='#e3deca')
 scale=min(w/im.width,h/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);out.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
 d.text((x+16,y+h+12),label,font=font(25),fill='#275146')
for i,(p,l)in enumerate([('designs/01-main-menu.png','启动与主菜单'),('designs/09-main-hud.png','经营主界面与建设入口'),('designs/50-orders.png','指令与运输流程'),('designs/60-finances.png','公司财务与经营数据')]):
 card(p,(48+i*788,250,740,416),l)
card('previews/world/assembled-transport-town.png',(48,800,2040,1148),'实际透明资源拼装样例 · 仅美术预览，未接入 Unity')
card('previews/vehicles/family-overview.jpg',(2140,800,1012,1148),'车辆家族原画 · 八向与型号映射见图册')
d.text((64,2040),'149 张整屏设计　227 张状态预览　37 类产业　41 类植被　256 个原始车辆型号映射',font=font(36),fill='#285144')
d.text((64,2110),'原生母图、切片、投影、换色与二维部件动画分别记录；整包状态以本地验收清单为准。',font=font(28),fill='#596c58')
d.text((64,2180),'美术参考：指定邮件 / 组队成图　　正式名称待确认　　当前阶段：图片与美术资源',font=font(27),fill='#596c58')
d.text((64,2250),'成果目录：E:/work/image/OpenTTD_UI_20261026_060146　　成果 GitHub 待提供，未提交或推送。',font=font(25),fill='#596c58')
p=R/'previews/full-game-overview.jpg';out.save(p,quality=94)
Path(str(p)+'.derivation.json').write_text(json.dumps({'file':p.relative_to(R).as_posix(),'operation':'Labeled editorial contact sheet of existing art; proportional downsampling and typography, no AI generation','width':W,'height':H,'derivedFrom':sources},ensure_ascii=False,indent=2),encoding='utf-8')
print(p)

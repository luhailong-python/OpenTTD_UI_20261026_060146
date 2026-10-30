"""Deterministic layout previews from real generated/approved raster assets.
Does not generate painted art, implement game logic, or create Unity content.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import json, math, hashlib, datetime, re, html, shutil
ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
def readj(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def savej(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
C=readj("docs/asset-common-manifest.json")
CM={x["id"]:x for x in C}
BRAND=readj('docs/asset-branding-manifest.json')
BM={a['id']:a for a in BRAND}
CM.update(BM)
CACHE={}
def asset(name):
 p=ROOT/CM[name]["file"] if name in CM else ROOT/name
 if str(p) not in CACHE:CACHE[str(p)]=Image.open(p).convert("RGBA")
 return CACHE[str(p)].copy()
FONTP=ROOT/"assets/fonts/NotoSansSC-Variable.ttf"
TITLEP=ROOT/"assets/fonts/MaShanZheng-Regular.ttf"
if not TITLEP.exists():TITLEP=FONTP
FC={}
def font(sz,bold=False,title=False):
 k=(sz,bold,title)
 if k not in FC:
  f=ImageFont.truetype(str(TITLEP if title else FONTP),sz)
  if not title:
   try:f.set_variation_by_axes([650 if bold else 400])
   except Exception:pass
  FC[k]=f
 return FC[k]
JADE="#164F45";TEXT="#253D35";GOLD="#B78F49";MUTED="#6A766A";IVORY="#FFF2D1";RED="#AE493A";GREEN="#267B58"
regions=[];placements=[];issues=[];CURRENT=""
def fittext(s,w,sz=26,bold=False,title=False,minsize=18):
 s=str(s)
 while sz>minsize and font(sz,bold,title).getlength(s)>w:sz-=1
 if font(sz,bold,title).getlength(s)>w:
  while s and font(sz,bold,title).getlength(s+"…")>w:s=s[:-1]
  s+="…"
 return s,sz
def txt(im,s,x,y,sz=26,color=TEXT,w=None,bold=False,title=False,align="left"):
 s=str(s)
 if w:s,sz=fittext(s,w,sz,bold,title)
 f=font(sz,bold,title)
 tw=f.getlength(s)
 if align=="center":x-=tw/2
 if align=="right":x-=tw
 d=ImageDraw.Draw(im);d.text((int(x),int(y)),s,font=f,fill=color,stroke_width=0)
 bb=d.textbbox((int(x),int(y)),s,font=f)
 if min(bb[:2])<0 or bb[2]>im.width or bb[3]>im.height:issues.append({"screen":CURRENT,"text":s,"bbox":bb,"kind":"canvas-overflow"})
 regions.append({"text":s,"rect":list(bb),"fontSize":sz,"fontFamily":"Ma Shan Zheng" if title and TITLEP!=FONTP else "Noto Sans SC","color":color,"alignment":align})
def wrap(s,width,sz=25,bold=False):
 out=[];line=""
 for ch in str(s):
  if ch=="\n":out.append(line);line="";continue
  if line and font(sz,bold).getlength(line+ch)>width:out.append(line);line=ch
  else:line+=ch
 if line:out.append(line)
 return out
def para(im,s,x,y,w,sz=25,color=TEXT,maxlines=8,gap=12):
 ls=wrap(s,w,sz)
 for i,l in enumerate(ls[:maxlines]):txt(im,l,x,y+i*(sz+gap),sz,color)
 if len(ls)>maxlines:issues.append({"screen":CURRENT,"text":s,"kind":"paragraph-too-long","lines":len(ls),"max":maxlines})
 return min(len(ls),maxlines)*(sz+gap)
def paste(im,p,x,y,w=None,h=None):
 pic=asset(p) if isinstance(p,str) else p.copy()
 if w and h:pic=pic.resize((int(w),int(h)),Image.Resampling.LANCZOS)
 src=p if isinstance(p,str) else pic.info.get('assetId')
 if src:placements.append({'asset':src,'rectTopLeftXYWH':[int(x),int(y),pic.width,pic.height],'border':CM.get(src,{}).get('border'),'spriteType':'Sliced' if any(CM.get(src,{}).get('border',[0])) else 'Simple','pivot':[.5,.5]})
 im.alpha_composite(pic,(int(x),int(y)))
def contain(im,p,x,y,w,h):
 pic=asset(p) if isinstance(p,str) else p.copy()
 pic.thumbnail((int(w),int(h)),Image.Resampling.LANCZOS)
 if isinstance(p,str):
  source_id=p
  if p not in CM:
   try:source_id=Path(p).resolve().relative_to(ROOT).as_posix()
   except ValueError:pass
  pic.info['assetId']=source_id
 paste(im,pic,x+(w-pic.width)/2,y+(h-pic.height)/2)
def brand(im,aid,x,y,w,h):
 """Actual unmodified brand raster, proportional downsample and Alpha blend."""
 a=BM[aid];pic=asset(aid);scale=min(1,w/pic.width,h/pic.height)
 size=(max(1,round(pic.width*scale)),max(1,round(pic.height*scale)))
 if size!=pic.size:pic=pic.resize(size,Image.Resampling.LANCZOS)
 pic.info['assetId']=aid;paste(im,pic,round(x+(w-pic.width)/2),round(y+(h-pic.height)/2))
 placements[-1].update({'type':'image','resourceId':aid,'file':a['file'],'sourceImage':a['file'],'sourceSHA256':a['sha256'],'role':a['role'],'preserveAspect':True,'operation':'proportional downsample and original Alpha composite; unmodified source RGB'})
def brand_sources(nodes):
 ids=list(dict.fromkeys(p['asset']for p in nodes if p.get('asset')in BM))
 if not ids:return []
 return [{'file':BM[i]['file'],'sha256':sha(ROOT/BM[i]['file']),'record':BM[i].get('generationRecord',BM[i].get('sourceGenerationRecord')),'role':BM[i]['role']}for i in ids]+[{'file':'docs/asset-branding-manifest.json','sha256':sha(ROOT/'docs/asset-branding-manifest.json'),'type':'source manifest and per-image provenance'}]
def cover(pic,w,h):
 return ImageOps.fit(pic,(int(w),int(h)),Image.Resampling.LANCZOS)
def nine(name,w,h):
 src=asset(name);sw,sh=src.size
 L,B,R,T=CM[name]["border"]
 if not any([L,B,R,T]):return src.resize((int(w),int(h)),Image.Resampling.LANCZOS)
 # Keep borders and painted corners at native scale where possible; scale only
 # when the requested whole element is shorter than the border sum.
 scale=min(1,w/max(1,L+R+2),h/sh)
 l,r,t,b=[max(1,int(v*scale)) for v in [L,R,T,B]]
 sx=[0,L,sw-R,sw];sy=[0,T,sh-B,sh]
 dx=[0,l,int(w)-r,int(w)];dy=[0,t,int(h)-b,int(h)]
 dst=Image.new("RGBA",(int(w),int(h)))
 for row in range(3):
  for col in range(3):
   if sx[col+1]<=sx[col] or sy[row+1]<=sy[row]:continue
   dw,dh=dx[col+1]-dx[col],dy[row+1]-dy[row]
   if dw<=0 or dh<=0:continue
   piece=src.crop((sx[col],sy[row],sx[col+1],sy[row+1]))
   if piece.size!=(dw,dh):piece=piece.resize((dw,dh),Image.Resampling.LANCZOS)
   dst.alpha_composite(piece,(dx[col],dy[row]))
 dst.info['assetId']=name
 return dst
def panel(im,x,y,w,h):paste(im,nine("panel_main",w,h),x,y)
def row(im,x,y,w,h,selected=False):
 paste(im,nine("reference-row-selected" if selected else "reference-row",w,h),x,y)
def inputbox(im,x,y,w,h,value,sz=25):
 paste(im,nine("reference-input",w,h),x,y);txt(im,value,x+18,y+(h-sz)/2-3,sz,w=w-65)
 contain(im,"reference-dropdown",x+w-45,y+(h-25)/2,25,25)
def btn(im,label,x,y,w=210,h=74,kind="secondary",sz=25):
 name={"primary":"button_primary_normal","selected":"button_primary_selected","pressed":"button_primary_pressed","disabled":"button_disabled"}.get(kind,"button_secondary_normal")
 paste(im,nine(name,w,h),x,y)
 txt(im,label,x+w/2,y+(h-sz)/2-7,sz,IVORY if kind in ("primary","pressed") else JADE,w=w-58,bold=True,align="center")
ICON_ALIASES={"orders":"orders","mail":"news","vehicle":"train","finance":"money","aircraft":"air","landscape":"terrain"}
def icon(im,name,x,y,w=64,h=None):
 name=ICON_ALIASES.get(name,name)
 p=ROOT/f"assets/icons/{name}.png"
 if p.exists():contain(im,str(p),x,y,w,h or w)
def line(im,x1,y1,x2,y2,fill=GOLD,width=1):ImageDraw.Draw(im).line((x1,y1,x2,y2),fill=fill,width=width)
def bg(menu=False,dim=90):
 im=cover(asset("assets/transport-valley.png" if menu else "assets/world-viewport.png"),W,H)
 if dim:im=Image.alpha_composite(im,Image.new("RGBA",(W,H),(12,42,37,dim)))
 return im
NAV=[("经营总览","company"),("建设工具","build"),("车队调度","train"),("运输经济","chart"),("地图与区域","map"),("联机与内容","network"),("设置与帮助","settings")]
def tabs(im,s,x=365,y=217,w=1390):
 ts=s.get("tabs",[])
 if not ts:return
 gap=10;bw=min(236,(w-gap*(len(ts)-1))/max(1,len(ts)))
 for i,t in enumerate(ts):btn(im,t,x+i*(bw+gap),y,bw,64,"primary" if i==0 else "secondary",24)
def actions(im,s,y=858,x=360,w=1410):
 acts=s.get("actions",[])
 gap=20;n=len(acts)
 bw=min(264,(w-gap*(n-1))/max(1,n))
 for i,a in enumerate(acts):btn(im,a,x+i*(bw+gap),y,bw,78,"primary" if i==0 else "secondary",26)
def header(im,s):
 panel(im,52,102,1816,906)
 paste(im,"title_plate",694,18)
 title=s["title"]
 txt(im,title,959,59,46,IVORY,w=415,bold=True,title=True,align="center")
 contain(im,"reference-close",1782,115,60,60)
 txt(im,"云途运输",116,144,24,JADE,bold=True)
 txt(im,"1956年 6月  ·  £284,560",1738,144,22,JADE,align="right")
 txt(im,s["subtitle"],364,176,20,MUTED,w=1190)
 # Navigation is a design of the entry hierarchy, not working business logic.
 sys=s.get('system','')
 active=1 if any(z in sys for z in ['建设','地形']) else 2 if any(z in sys for z in ['车辆','车队','调度','车库','枢纽']) else 3 if any(z in sys for z in ['公司','经济','统计']) else 4 if any(z in sys for z in ['地图','城镇','工业']) else 5 if any(z in sys for z in ['联机','内容','脚本','编辑']) else 6 if any(z in sys for z in ['设置','辅助','帮助']) else 0
 for i,(label,ic) in enumerate(NAV):
  yy=252+i*86
  row(im,96,yy,226,76,i==active)
  icon(im,ic,112,yy+10,52)
  txt(im,label,171,yy+21,22,IVORY if i==active else JADE,w=135,bold=i==active)
 line(im,340,219,340,878,"#CFBD91",1)
 tabs(im,s)
 brand(im,'brand_symbol',72,1005,40,40)
 txt(im,"云途万里 · 静态排版示例",126,1017,18,"#F3E8CB")
 txt(im,s["id"]+"  /  "+s["layout"],1808,1017,17,"#F3E8CB",align="right")
def detail_card(im,s,x=1360,y=310,w=400,h=552):
 row(im,x,y,w,h)
 icon(im,s.get("icon","company"),x+(w-150)/2,y+26,150)
 txt(im,"经营札记",x+30,y+192,30,JADE,w=w-60,bold=True,title=True)
 yy=y+250
 for k,d in enumerate(s.get("details",[])[:5]):
  yy+=para(im,d,x+29,yy,w-58,23,maxlines=3,gap=8)+20
def table(im,s,x=365,y=310,w=950,h=550,showicons=True):
 cols=s.get("columns",["项目","说明"])
 rows=s.get("rows",[])
 n=max(1,len(cols));cw=(w-40)/n
 paste(im,nine("reference-row-selected",w,65),x,y)
 for j,c in enumerate(cols):txt(im,c,x+22+j*cw,y+17,23,IVORY,w=cw-26,bold=True)
 if not rows:
  icon(im,s.get("icon","cargo"),x+w/2-60,y+153,120)
  txt(im,"暂无记录",x+w/2,y+307,32,JADE,align="center")
  txt(im,"满足条件后将在这里显示",x+w/2,y+365,22,MUTED,align="center")
  return
 rh=min(88,(h-74)/min(6,len(rows)))
 for i,r in enumerate(rows[:6]):
  yy=y+74+i*rh;row(im,x,yy,w,rh-7,i==0)
  for j,v in enumerate(r[:n]):
   fs=18 if rh<42 else 21 if rh<60 else 24
   lines=wrap(v,cw-34,fs)
   offset=3 if rh<60 else 10
   for k,l in enumerate(lines[:1 if rh<60 else 2]):txt(im,l,x+22+j*cw,yy+offset+k*29,fs,IVORY if i==0 else TEXT,w=cw-34)
 if len(rows)>6:
  txt(im,"显示 1–6 / "+str(len(rows))+"  ·  向下滚动",x+20,y+h-15,19,MUTED)
 # Painted scrollbar from an existing slider, oriented vertically.
 tr=nine("reference-slider-track",int(h-80),14).rotate(90,expand=True)
 paste(im,tr,x+w+11,y+74)
 th=asset("reference-slider-thumb");th.thumbnail((30,30))
 paste(im,th,x+w+3,y+108)
def form(im,s):
 x,y,w=365,311,990
 for i,r in enumerate(s.get("rows",[])[:7]):
  yy=y+i*78
  if not r:continue
  txt(im,r[0],x+15,yy+19,25,JADE,w=420,bold=True)
  value=" · ".join(str(a) for a in r[1:])
  if '音量' in r[0] and '%' in value:
   paste(im,nine('reference-slider-track',330,21),x+445,yy+28)
   amount=int(re.search(r'\d+',value).group())
   paste(im,nine('reference-slider-fill',max(24,int(330*amount/100)),21),x+445,yy+28)
   contain(im,'reference-slider-thumb',x+425+int(330*amount/100),yy+12,48,48)
   txt(im,value,x+820,yy+15,25,JADE,w=150)
  else:inputbox(im,x+445,yy+7,w-460,60,value)
 detail_card(im,s,1390,311,365,555)
def charts(im,s):
 x,y,w,h=384,350,1290,365
 row(im,365,310,1390,522)
 txt(im,"公司经营走势",405,335,29,JADE,bold=True)
 left,top,bottom,right=469,408,723,1685
 for k in range(5):
  gy=top+k*(bottom-top)/4
  line(im,left,gy,right,gy,"#D9CEAF")
  txt(im,str(100-k*25),left-24,gy-11,19,MUTED,align="right")
 for i,m in enumerate(["1月","2月","3月","4月","5月","6月"]):txt(im,m,left+i*(right-left)/5,bottom+15,22,MUTED,align="center")
 seed=sum(map(ord,s["id"]))
 for jj,c in enumerate(["#287865","#B78F49","#A55A45"]):
  vals=[.18+((seed+i*13+jj*29)%63)/100 for i in range(6)]
  ps=[(left+i*(right-left)/5,bottom-v*(bottom-top)) for i,v in enumerate(vals)]
  ImageDraw.Draw(im).line(ps,fill=c,width=5)
  for a,b in ps:ImageDraw.Draw(im).ellipse((a-6,b-6,a+6,b+6),fill=c)
  txt(im,["青云运输","云岭商行","青岚联运"][jj],510+jj*360,787,23,c,bold=True)
 for j,d in enumerate(s.get("details",[])[:2]):txt(im,d,390,850+j*0,22,MUTED,w=1350) if j==0 else None
def finance(im,s):
 table(im,s,365,310,1010,546,False)
 row(im,1400,310,355,546)
 icon(im,"money",1514,338,132)
 yy=497
 for d in s.get("details",[])[:4]:
  yy+=para(im,d,1430,yy,290,23,maxlines=3)+24
def list_detail(im,s):
 table(im,s,365,310,950,545)
 detail_card(im,s,1360,310,395,545)
def details(im,s):
 # Object details have a dedicated illustration/viewport, key fields and table.
 vx,vy,vw,vh=365,310,550,250
 row(im,vx,vy,vw,vh)
 if s.get("icon") in ["station","town","map","industry","terrain","bridge","airport","ship","air"]:
  pic=cover(asset("assets/world-viewport.png"),vw-24,vh-24);paste(im,pic,vx+12,vy+12)
 else:
  ic=s.get('icon','train')
  if s['id']in ['47-vehicle-view','48-vehicle-details']:
   icon(im,'train',vx+35,vy+48,210)
   contain(im,'assets/cargo/passenger-carriage.png',vx+259,vy+70,240,160)
  else:icon(im,'depot' if '-depot-'in s['id'] else ic,vx+170,vy+40,200)
 yy=325
 for d in s.get("details",[])[:4]:
  yy+=para(im,d,955,yy,770,25,maxlines=3)+23
 table(im,s,365,590,1390,260,False)
def world(im,s):
 # Full gameplay canvas, toolbar and HUD preserve a broad map view.
 im=bg(False,0)
 paste(im,nine("reference-paper",1920,164),0,0)
 brand(im,'brand_symbol',38,12,48,48)
 txt(im,"云途万里",100,19,36,JADE,title=True)
 txt(im,"云途运输",418,25,25,JADE,bold=True)
 txt(im,"1956年6月1日",708,25,24,JADE)
 txt(im,"£284,560",1050,25,26,JADE,bold=True)
 for j,label in enumerate(["Ⅱ","▶","▶▶"]):btn(im,label,1450+j*112,14,105,72,"secondary",28)
 for j,name in enumerate(["rail","road","tram","ship","air","terrain","station","company","money","chart","map","news","settings"]):
  xx=130+j*126
  icon(im,name,xx,65,51)
  txt(im,{"rail":"铁路","road":"公路","tram":"有轨","ship":"水运","air":"航空","terrain":"地形","station":"车站","company":"公司","money":"财务","chart":"统计","map":"地图","news":"新闻","settings":"设置"}[name],xx+26,118,18,JADE,align="center")
 panel(im,1330,201,516,388)
 txt(im,"运输概览",1411,245,34,JADE,title=True)
 for j,(a,b) in enumerate([("运行车辆","24 辆"),("上月收入","£42,680"),("待运旅客","124 人"),("服务评级","良好")]):
  txt(im,a,1387,314+j*51,24,MUTED)
  txt(im,b,1771,314+j*51,25,JADE,bold=True,align="right")
 paste(im,nine("reference-paper",1920,84),0,996)
 icon(im,"news",43,1008,47)
 txt(im,"青岚中央站新增班次，线路运量稳步提升。",110,1013,25,JADE)
 txt(im,"静态排版示例",1790,1018,19,MUTED,align="right")
 return im
def construction(im,s):
 # Palettes and a clear world viewport, plus build footprint/readout.
 row(im,365,304,485,544)
 tools={"rail":["rail","junction","signal","station","depot","bridge"],"road":["road","bus-stop","truck","depot","bridge","tunnel"],"ship":["dock","ship","warehouse","bridge","terrain","build"],"air":["airport","air","station","build","terrain","help"],"terrain":["terrain","tree","build","map","bridge","tunnel"]}.get(s.get("icon"),["build","terrain","rail","road","town","industry"])
 specialized={
 '12-rail-station':(['station']*4+['rail','map'],['东北向','西北向','东南向','西南向','站台设置','覆盖预览']),
 '14-rail-depot':(['depot']*4+['rail','build'],['东北向','西北向','东南向','西南向','连接轨道','建造车库']),
 '15-rail-waypoint':(['junction','rail','junction','rail','map','build'],['单线','双线','方向一','方向二','既有路点','放置路点']),
 '16-rail-convert':(['rail']*4+['train','build'],['普通铁路','电气化','单轨铁路','磁悬浮','兼容车型','批量转换']),
 '21-road-station':(['bus-stop','truck','bus-stop','truck','road','map'],['客运站','货运站','路边式','贯通式','选择方向','覆盖预览']),
 '22-road-depot':(['depot']*4+['road','build'],['东北向','西北向','东南向','西南向','连接道路','放置车库']),
 '25-dock':(['dock']*4+['ship','map'],['东北岸','西北岸','东南岸','西南岸','泊位','覆盖预览']),
 '26-shipyard':(['depot','depot','ship','dock','map','build'],['方向一','方向二','航道','港口','定位','建造']),
 '28-airport-build':(['airport']*3+['air','terrain','map'],['小型机场','通勤机场','大型机场','起降限制','场地平整','覆盖预览']),
 '29-airport-picker':(['airport']*3+['air','terrain','map'],['小型机场','通勤机场','大型机场','起降限制','场地平整','覆盖预览'])}
 labels=None
 if s['id']in specialized:tools,labels=specialized[s['id']]
 for j,name in enumerate(tools):
  xx=403+(j%3)*138;yy=347+(j//3)*130
  row(im,xx-6,yy-3,119,113,j==0);icon(im,name,xx+20,yy+4,66)
  label=labels[j] if labels else {"rail":"轨道","junction":"道岔","signal":"信号","station":"车站","depot":"车库","bridge":"桥梁","road":"道路","bus-stop":"站点","truck":"车辆","tunnel":"隧道","dock":"码头","ship":"船坞","warehouse":"仓储","terrain":"地形","build":"建造","airport":"机场","air":"航空","help":"说明","tree":"植树","map":"舆图","town":"城镇","industry":"产业"}.get(name,name)
  txt(im,label,xx+53,yy+78,18,IVORY if j==0 else JADE,align="center")
 yy=621
 for r in s.get("rows",[])[:3]:
  if not r:continue
  txt(im,r[0],407,yy,22,JADE,w=370,bold=True);yy+=29
  if len(r)>1:txt(im," · ".join(r[1:]),407,yy,21,MUTED,w=370);yy+=39
 pic=cover(asset("assets/world-viewport.png"),876,492);paste(im,pic,879,311)
 # Explicit translucent selection footprint as a layout annotation overlay.
 overlay=Image.new("RGBA",(876,492));od=ImageDraw.Draw(overlay)
 od.polygon([(210,208),(365,151),(538,229),(383,294)],fill=(80,190,149,48),outline=(249,236,165,240),width=4)
 paste(im,overlay,879,311)
 row(im,879,815,876,58)
 txt(im,(s.get("details") or ["选择位置后确认建造"])[0],900,827,22,JADE,w=829)
def article(im,s):
 pic=cover(asset("assets/transport-valley.png"),600,535);paste(im,pic,365,310)
 yy=325
 for d in s.get("details",[]):
  yy+=para(im,d,1005,yy,725,27,maxlines=4)+28
 for rr in s.get("rows",[])[:4]:
  yy+=para(im,"  ·  ".join(map(str,rr)),1005,yy,720,24,maxlines=3)+18
def menu(im,s):
 im=bg(True,0)
 # Left plaque over a softly shaded, readable panel.
 panel(im,84,96,706,915)
 brand(im,'brand_main',124,62,626,284)
 txt(im,"道家运输经营",433,311,25,JADE,align="center")
 btn(im,"新建游戏",209,351,458,87,"primary",31)
 btn(im,"载入存档",209,449,458,87,"secondary",31)
 btn(im,"联机游戏",209,547,458,87,"secondary",31)
 for j,l in enumerate(["游玩场景","情景编辑","在线内容","设置","帮助","退出游戏"]):
  btn(im,l,169+(j%3)*187,654+(j//3)*95,176,76,"secondary",23)
 txt(im,"通山海，达万里",434,839,38,JADE,title=True,align="center")
 txt(im,"云途万里 · 游戏美术预览",434,895,18,MUTED,align="center")
 txt(im,"铁路 · 公路 · 水运 · 航空",1727,971,29,IVORY,align="right")
 return im
def dialog(im,s):
 icon(im,s.get("icon","help"),444,332,168)
 txt(im,s["title"],696,327,38,JADE,w=980,bold=True,title=True)
 yy=402
 for d in s.get("details",[])[:3]:yy+=para(im,d,698,yy,970,27,maxlines=3)+22
 for r in s.get("rows",[])[:3]:
  row(im,436,yy,1253,66);txt(im,"    ".join(map(str,r)),469,yy+17,24,JADE,w=1190);yy+=77
def make(s):
 global CURRENT,regions,placements
 CURRENT=s["id"];regions=[];placements=[]
 import sys
 try:
  from special_screens import render_special
 except ImportError:render_special=None
 try:
  from special_metrics import render_metric
 except ImportError:render_metric=None
 r=sys.modules[__name__]
 if s["layout"]=="menu":im=menu(None,s)
 elif s["layout"]=="world":
  im=render_special(r,None,s) if render_special else None
  if im is None:im=world(None,s)
 else:
  im=bg(False,115);header(im,s)
  layouts={"settings":form,"finance":finance,"chart":charts,"detail":details,"build":construction,"editor":construction,"article":article,"dialog":dialog,"list":list_detail,"network":list_detail}
  from extra_layouts import render_extra
  custom=render_extra(r,im,s)
  if custom is None:custom=render_special(r,im,s) if render_special else None
  if custom is None:custom=render_metric(r,im,s) if render_metric else None
  if custom is None:layouts.get(s["layout"],list_detail)(im,s)
  else:im=custom
  actions(im,s)
 return im,regions.copy()
def record_derived(path,s,op,parents,layout_path=None):
 im=Image.open(ROOT/path)
 savej(str(path)+".generation.json",{"file":str(path),"sha256":sha(ROOT/path),"width":im.width,"height":im.height,"format":"PNG","generatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"route":"deterministic-composite","tool":"Pillow","operation":op,"nativeModelGeneration":False,"derivedFrom":parents,"actualModel":None,"actualQuality":None,"unverifiedReason":"本图是确定性排版派生图；原始AI模型/质量见完整来源链，未披露部分保持未确认。","screenId":s.get("id"),"textLayout":layout_path or("docs/layouts/"+s.get("id","")+".json")})
def statepreview(s,st):
 global CURRENT,regions,placements
 CURRENT=s["id"]+"--"+st["id"];regions=[];placements=[]
 im=Image.new("RGBA",(960,600),"#163E37");panel(im,12,32,936,548)
 txt(im,s["title"],480,89,39,JADE,w=740,bold=True,title=True,align="center")
 icon(im,s.get("icon","help"),414,156,132)
 txt(im,st["name"],480,301,34,JADE,w=780,bold=True,align="center")
 ls=wrap(st["message"],760,25)
 for j,l in enumerate(ls[:3]):txt(im,l,480,365+j*36,25,TEXT,align="center")
 confirm=any(z in (st['id']+' '+st['name']) for z in ['confirm','overwrite','abort','sell','确认','覆盖']) or (st.get('action','').startswith('确认') and len(st['action'])>2)
 if confirm:
  btn(im,st.get('action','确认'),145,427,320,79,'primary',25)
  secondary='继续生成' if s['id']=='08-world-progress' else '取消'
  btn(im,secondary,495,427,320,79,'secondary',25)
  st['secondaryAction']=secondary
 else:btn(im,st.get("action","返回"),280,427,400,79,"primary",27)
 contain(im,'reference-close',860,65,48,48)
 txt(im,"状态排版示例 · "+s["id"],480,570,17,"#F3E8CB",align="center")
 return im
def main(only=None):
 cat=readj("docs/screen-catalog.json")
 previous={s['id']:s for s in readj('docs/UI_MASTER_MANIFEST.json')['screens']} if only else {}
 out=ROOT/"designs";out.mkdir(exist_ok=True)
 (ROOT/"previews/thumbs").mkdir(parents=True,exist_ok=True);(ROOT/"previews/states").mkdir(exist_ok=True);(ROOT/"docs/layouts").mkdir(exist_ok=True)
 parents=[{"file":"assets/transport-valley.png","sha256":sha(ROOT/"assets/transport-valley.png"),"record":"assets/transport-valley.png.generation.json"},{"file":"assets/world-viewport.png","sha256":sha(ROOT/"assets/world-viewport.png"),"record":"assets/world-viewport.png.generation.json"}]+[{"file":'docs/asset-'+n+'-manifest.json',"sha256":sha(ROOT/('docs/asset-'+n+'-manifest.json')),"type":"source manifest and per-image provenance"}for n in ['common','icons','cargo','portraits','fonts']]
 for i,s in enumerate(cat):
  if only and s['id'] not in only:
   cat[i]=previous[s['id']]
   continue
  im,regs=make(s);p=f"designs/{s['id']}.png";im.convert("RGB").save(ROOT/p,optimize=True)
  record_derived(p,s,"手绘位图九宫格组合、正式品牌Logo等比合成、原生字体排版、数据图表绘制；1920×1080布局画布，原画1672×941背景经cover适配；不是原生1920模型生成。",parents+brand_sources(placements))
  savej("docs/layouts/"+s["id"]+".json",{"screenId":s["id"],"referenceResolution":[W,H],"textRegions":regs,"spritePlacements":placements.copy(),"notes":["坐标原点左上，Unity锚点待接入验证","动态文案独立排版未写入正式控件PNG","图表为静态示例数据可视化"]})
  thumb=im.convert("RGB");thumb.thumbnail((480,270));thumb.save(ROOT/f"previews/thumbs/{s['id']}.webp",quality=85)
  s["designPath"]=p;s["thumbnailPath"]=f"previews/thumbs/{s['id']}.webp";s["resourceManifests"]=['docs/asset-'+n+'-manifest.json'for n in ['common','icons','cargo','portraits','fonts','branding']]
  for st in s.get("states",[]):
   sp=f"previews/states/{s['id']}--{st['id']}.png";si=statepreview(s,st);si.convert("RGB").save(ROOT/sp,optimize=True);st["previewPath"]=sp
   record_derived(sp,s,"状态语义独立排版，960×600，复用相同手绘控件；确定性组合。",parents+brand_sources(placements),layout_path='docs/layouts/states/'+s['id']+'--'+st['id']+'.json')
   savej('docs/layouts/states/'+s['id']+'--'+st['id']+'.json',{'screenId':s['id'],'stateId':st['id'],'referenceResolution':[960,600],'textRegions':regions.copy(),'spritePlacements':placements.copy()})
  s["productionStatus"]="art-produced";s["acceptanceStatus"]="pending-visual-review";s["unityStatus"]="not-imported"
  if i%20==0:print(f"rendered {i+1}/{len(cat)}",flush=True)
 savej("docs/UI_MASTER_MANIFEST.json",{"schemaVersion":1,"project":"云途万里","referenceResolution":[W,H],"screens":cat})
 savej("records/layout-validation.json",{"screens":len(cat),"statePreviews":sum(len(s.get("states",[])) for s in cat),"canvasOverflowOrTextIssues":issues,"checkedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print(f"finished {len(cat)} screens; {len(issues)} text issues",flush=True)
if __name__=="__main__":
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='*')
 args=parser.parse_args();main(set(args.only) if args.only else None)


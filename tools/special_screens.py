"""Specialized static UI layouts composed from the project's painted assets.

Maps, graphs, selection marks, palettes and key labels are data/interaction
overlays, not substitutes for generated illustration. No business logic or
Unity scene is implemented here.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import math


def _paper(r, im, x, y, w, h, selected=False):
    r.row(im, x, y, w, h, selected)


def _text(r, im, text, x, y, size=24, color=None, width=None, **kw):
    r.txt(im, text, x, y, size, color or r.TEXT, w=width, **kw)


def _native(r, im, path, x, y, w, h):
    """Fit a supplied raster, never enlarge beyond its actual pixels."""
    pic = r.asset(str(path))
    pic.thumbnail((int(w), int(h)), Image.Resampling.LANCZOS)
    asset_id=str(path)
    if asset_id not in r.CM:
        try:asset_id=Path(path).relative_to(r.ROOT).as_posix()
        except ValueError:asset_id=Path(path).as_posix()
    pic.info['assetId']=asset_id
    r.paste(im, pic, x + (w-pic.width)/2, y + (h-pic.height)/2)


def _pill(r, im, text, x, y, w=120, h=46, selected=False):
    r.btn(im, text, x, y, w, h, "primary" if selected else "secondary", 20)


def _check(r, im, text, x, y, on=True, w=320):
    _native(r, im, "reference-checkbox-on" if on else "reference-checkbox-off", x, y+2, 29, 29)
    _text(r, im, text, x+43, y, 22, width=w-48)


def _arrow(draw, start, end, color, width=3):
    draw.line((start, end), fill=color, width=width)
    dx, dy=end[0]-start[0],end[1]-start[1]
    length=max(1,math.hypot(dx,dy)); ux,uy=dx/length,dy/length
    size=12+width
    p=(end[0]-ux*size,end[1]-uy*size)
    draw.polygon([end,(p[0]-uy*size*.45,p[1]+ux*size*.45),(p[0]+uy*size*.45,p[1]-ux*size*.45)],fill=color)


def _map_base(r, im, s):
    if im is None:
        im=r.bg(False,112)
        r.header(im,s)
    return im


def _map_label(r, im, label, x, y, width=160):
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((x-8,y-3,x+width,y+36),radius=8,fill=(250,245,222,235),outline=(160,137,87,215),width=1)
    _text(r,im,label,x,y,21,r.JADE,width=width-8,bold=True)


def map_screen(r, im, s, flow=False):
    im=_map_base(r,im,s)
    x,y,w,h=365,310,1044,528
    _paper(r,im,x-8,y-8,w+16,h+16)
    pic=r.cover(r.asset("assets/world-viewport.png"),w,h)
    pic=ImageEnhance.Color(pic).enhance(.60)
    pic=Image.alpha_composite(pic,Image.new("RGBA",pic.size,(240,241,209,88)))
    pic.info['assetId']='assets/world-viewport.png'
    r.paste(im,pic,x,y)
    draw=ImageDraw.Draw(im)
    # Thematic network overlay with labeled nodes, separate from world artwork.
    local={"青岚中央站":(184,164),"云岭站":(522,117),"东山煤矿":(786,318),"青岚港":(278,382),"西岭电厂":(848,418)}
    pts={k:(x+a,y+b) for k,(a,b) in local.items()}
    links=[("青岚中央站","云岭站",72,"#398B70",8),("青岚中央站","青岚港",46,"#5E92A0",5),("云岭站","东山煤矿",93,"#B15A42",13),("东山煤矿","西岭电厂",84,"#C1963C",10)]
    if flow:
        for a,b,percent,color,lw in links:
            _arrow(draw,pts[a],pts[b],color,lw)
            mx=(pts[a][0]+pts[b][0])/2;my=(pts[a][1]+pts[b][1])/2
            draw.rounded_rectangle((mx-43,my-20,mx+43,my+19),radius=12,fill=(255,250,225,245),outline=color,width=2)
            _text(r,im,str(percent)+"%",mx,my-16,22,color,align="center",bold=True)
    else:
        colors=["#2F806D","#B0904F","#2F806D","#B0904F"]
        for j,(a,b,_,_,_) in enumerate(links):
            draw.line([pts[a],pts[b]],fill=(255,248,217,245),width=12)
            draw.line([pts[a],pts[b]],fill=colors[j],width=5)
        # Current viewport rectangle and a center cross identify the locator.
        cx,cy=pts["青岚中央站"]
        draw.rectangle((cx-92,cy-68,cx+133,cy+88),outline=(249,233,168,255),width=4)
        draw.line((cx-17,cy,cx+17,cy),fill=r.RED,width=3)
        draw.line((cx,cy-17,cx,cy+17),fill=r.RED,width=3)
    for idx,(label,(nx,ny)) in enumerate(pts.items()):
        draw.ellipse((nx-9,ny-9,nx+9,ny+9),fill=(250,241,199,255),outline=r.JADE,width=4)
        lx=nx-78 if idx!=4 else nx-122
        ly=ny+18 if idx==4 else ny-51 if idx in (0,1) else ny+17
        _map_label(r,im,label,lx,ly,155)
    _paper(r,im,1436,310,319,528)
    _text(r,im,"货流图例" if flow else "地图图例",1463,330,30,r.JADE,bold=True,title=True)
    if flow:
        _text(r,im,"当前货物：旅客",1462,389,23,r.JADE)
        _text(r,im,"线宽表示运输容量",1462,430,21,r.MUTED)
        legend=[("#398B70","低于 60%",4),("#C1963C","60%—85%",8),("#B15A42","高于 85%",12)]
        for j,(color,label,lw) in enumerate(legend):
            yy=484+j*58
            draw.line((1469,yy,1533,yy),fill=color,width=lw)
            _text(r,im,label,1552,yy-14,21,r.JADE)
        r.line(im,1462,654,1725,654,"#CABB98")
        _text(r,im,"选中连接",1464,672,22,r.MUTED)
        _text(r,im,"青岚 → 云岭",1464,709,25,r.JADE,bold=True)
        _text(r,im,"324 人/月  ·  72%",1464,751,21,r.JADE)
    else:
        entries=[("town","城镇与站点"),("rail","铁路线路"),("road","公路线路"),("industry","工业设施"),("ship","水域与港口")]
        for j,(ic,label) in enumerate(entries):
            yy=394+j*67;r.icon(im,ic,1462,yy-6,47)
            _text(r,im,label,1523,yy+5,23,r.JADE)
        _check(r,im,"显示地名",1465,747,True,255)
        _text(r,im,"金框：当前观察范围",1465,791,20,r.MUTED,width=267)
    if s.get('layout')=='world':r.actions(im,s)
    return im


def extra_view(r,im,s):
    im=_map_base(r,im,s)
    for i,(label,sub) in enumerate([("主观察视窗","青岚中央站"),("独立观察视窗","东山煤矿")]):
        x=365+i*710
        _paper(r,im,x,310,680,525)
        _text(r,im,label,x+24,329,28,r.JADE,bold=True,title=True)
        source=r.asset("assets/world-viewport.png")
        ww,hh=source.size
        crop=source.crop((0 if i==0 else ww//3,hh//5,ww*2//3 if i==0 else ww,hh))
        view=r.cover(crop,654,350);view.info['assetId']='assets/world-viewport.png'
        r.paste(im,view,x+13,382)
        _text(r,im,sub,x+27,751,26,r.JADE,bold=True)
        _pill(r,im,"＋",x+416,748,64,56)
        _pill(r,im,"−",x+487,748,64,56)
        _pill(r,im,"定位",x+558,748,90,56)
    _text(r,im,"两个视窗分别移动与缩放",395,817,20,r.MUTED)
    if s.get('layout')=='world':r.actions(im,s)
    return im


def orders(r,im,s):
    _paper(r,im,365,310,870,531)
    _text(r,im,"行程指令",394,326,28,r.JADE,bold=True,title=True)
    _text(r,im,"当前执行：02",1204,331,22,r.MUTED,align="right")
    data=[("青岚中央站","车站","满载任意货物"),("云岭路点","路点","不停站途经"),("云岭站","车站","卸载并装载"),("青岚车库","车库","必要时维修")]
    for i,(place,kind,policy) in enumerate(data):
        yy=386+i*101;sel=i==1
        _paper(r,im,385,yy,828,90,sel)
        color=r.IVORY if sel else r.JADE
        for ax in range(2):
            for ay in range(3):ImageDraw.Draw(im).ellipse((400+ax*9,yy+30+ay*9,403+ax*9,yy+33+ay*9),fill=color)
        _text(r,im,f"{i+1:02d}",438,yy+24,29,color,bold=True)
        r.icon(im,"station" if kind=="车站" else "depot" if kind=="车库" else "rail",493,yy+13,61)
        _text(r,im,place,575,yy+13,26,color,bold=True,width=300)
        _text(r,im,policy,576,yy+49,21,color,width=400)
        _text(r,im,"▶" if sel else kind,1177,yy+28,21,color,align="right")
    _text(r,im,"拖动左侧握柄调整顺序",394,805,21,r.MUTED)
    _paper(r,im,1261,310,494,531)
    _text(r,im,"停靠属性",1292,327,30,r.JADE,bold=True,title=True)
    _text(r,im,"选中：云岭路点",1293,388,24,r.JADE,bold=True)
    fields=[("行驶方式","不停站途经"),("装载策略","不适用于路点"),("卸载策略","不适用于路点"),("车库动作","仅在车库指令使用")]
    for i,(k,v) in enumerate(fields):
        yy=437+i*77
        _text(r,im,k,1294,yy,21,r.MUTED)
        r.inputbox(im,1451,yy-7,274,57,v,21)
    _check(r,im,"与 3 辆列车共享指令",1291,773,True,438)
    return im


def timetable(r,im,s):
    _paper(r,im,365,310,1390,531)
    cols=[("指令与区段",395),('类型',784),('计划',970),('预计',1178),('偏差',1435)]
    for label,x in cols:_text(r,im,label,x,333,23,r.JADE,bold=True)
    items=[("青岚中央站","等待","2 天","2 天","准点"),("前往云岭站","旅行","6 天","7 天","晚点 1 天"),("云岭站","等待","2 天","2 天","准点"),("返回青岚中央站","旅行","6 天","6 天","准点")]
    for i,row in enumerate(items):
        yy=383+i*87;sel=i==1
        _paper(r,im,384,yy,1348,78,sel)
        for j,value in enumerate(row):
            _text(r,im,value,cols[j][1],yy+22,24,r.IVORY if sel else (r.RED if j==4 and "晚点" in value else r.JADE),width=(365 if j==0 else 175),bold=j in (0,4))
    r.line(im,398,752,1723,752,"#C9B88C")
    _text(r,im,"全程计划 16 天",401,778,27,r.JADE,bold=True)
    _text(r,im,"当前晚点 1 天",802,778,27,r.RED,bold=True)
    _text(r,im,"自动填充：关闭",1291,781,23,r.MUTED)
    return im


def groups(r,im,s):
    _paper(r,im,365,310,416,531)
    _text(r,im,"列车分组",395,328,29,r.JADE,bold=True,title=True)
    names=[("− 全部列车","12",0),("− 青岚客运","6",1),("  城际快线","4",2),("  市郊接驳","2",2),("+ 云岭货运","4",1),("未分组","2",1)]
    for i,(name,n,lev) in enumerate(names):
        yy=391+i*61
        if i==1:_paper(r,im,380,yy-6,385,56,True)
        _text(r,im,name,390+lev*17,yy,22,r.IVORY if i==1 else r.JADE,width=281,bold=i==1)
        _text(r,im,n,742,yy,22,r.IVORY if i==1 else r.MUTED,align="right")
    _text(r,im,"拖入车辆以调整所属分组",392,797,20,r.MUTED,width=355)
    _paper(r,im,810,310,945,531)
    _text(r,im,"青岚客运  ·  6 辆列车",841,329,29,r.JADE,bold=True)
    for i,(name,where,profit) in enumerate([("青岚快车 01","前往云岭站","£ 8,420"),("青岚快车 02","青岚中央站装载","£ 7,960"),("青岚快车 03","前往青岚站","£ 6,820"),("青岚快车 04","车辆检修","£ 5,200")]):
        yy=390+i*91
        _paper(r,im,830,yy,905,82,i==0)
        r.icon(im,"train",845,yy+8,65)
        _text(r,im,name,929,yy+10,24,r.IVORY if i==0 else r.JADE,bold=True)
        _text(r,im,where,929,yy+44,20,r.IVORY if i==0 else r.MUTED)
        _text(r,im,profit,1710,yy+26,24,r.IVORY if i==0 else r.JADE,align="right",bold=True)
    _check(r,im,"保护本组车辆，不受全局替换影响",841,788,False,877)
    return im


def purchase(r,im,s):
    slug=s['id'].split('-',1)[1]
    pictures={
        'buy-train':['assets/icons/train.png','assets/cargo/passenger-carriage.png','assets/cargo/coal-wagon.png'],
        'buy-road':['assets/icons/bus.png','assets/icons/truck.png','assets/cargo/mail-van.png'],
        'buy-ship':['assets/icons/ship.png','assets/cargo/steamship.png','assets/icons/ship.png'],
        'buy-air':['assets/cargo/prop-plane.png','assets/icons/air.png','assets/icons/air.png'],
    }[slug]
    if slug=='buy-air' and (r.ROOT/'assets/cargo/helicopter.png').exists():
        pictures[2]='assets/cargo/helicopter.png'
    _paper(r,im,365,310,904,531)
    for i,data in enumerate(s.get('rows',[])[:3]):
        yy=326+i*157
        _paper(r,im,381,yy,872,146,i==0)
        _native(r,im,pictures[i],399,yy+8,145,126)
        c=r.IVORY if i==0 else r.JADE
        _text(r,im,data[0],565,yy+18,28,c,width=385,bold=True)
        _text(r,im,data[1],568,yy+67,24,c,width=320)
        _text(r,im,data[2],1226,yy+67,26,c,align='right',bold=True)
        _text(r,im,['已选择','点击比较','点击比较'][i],1223,yy+109,18,c,align='right')
    _text(r,im,'显示可购型号  ·  按价格与容量排序',399,805,21,r.MUTED)
    _paper(r,im,1295,310,460,531)
    _text(r,im,'车型比较',1328,329,29,r.JADE,bold=True,title=True)
    _native(r,im,pictures[0],1410,370,220,174)
    name=s.get('rows',[['当前车型']])[0][0]
    _text(r,im,name,1525,548,28,r.JADE,width=382,bold=True,align='center')
    values={'buy-train':[('最高速度','96 km/h'),('动力','1,200 hp'),('重量','78 吨'),('运行成本','£ 2,640 / 年')],
            'buy-road':[('最高速度','56 km/h'),('载客容量','31 人'),('可靠性','82%'),('运行成本','£ 680 / 年')],
            'buy-ship':[('最高速度','32 km/h'),('载客容量','120 人'),('可靠性','82%'),('运行成本','£ 2,100 / 年')],
            'buy-air':[('最高速度','480 km/h'),('载客容量','80 人'),('可用机场','小型及以上'),('运行成本','£ 8,400 / 年')]}[slug]
    for j,(a,b) in enumerate(values):
        yy=609+j*47
        _text(r,im,a,1327,yy,22,r.MUTED,width=156)
        _text(r,im,b,1724,yy,23,r.JADE,align='right',bold=True,width=225)
    return im


def manager(r,im,s):
    portraits=sorted((r.ROOT/'assets/portraits').glob('*.png')) if (r.ROOT/'assets/portraits').exists() else []
    portraits=[p for p in portraits if not any(t in p.stem for t in ['atlas','overview','sheet'])]
    _paper(r,im,365,310,372,531)
    _text(r,im,'当前经理',400,329,29,r.JADE,bold=True,title=True)
    face=str(portraits[0]) if portraits else 'assets/icons/company.png'
    _native(r,im,face,414,391,270,270)
    _text(r,im,'云游子',550,682,31,r.JADE,bold=True,align='center')
    _pill(r,im,'随机形象',430,744,244,65)
    _paper(r,im,765,310,350,531)
    _text(r,im,'面部组合',793,329,29,r.JADE,bold=True,title=True)
    for j,(a,b) in enumerate([('脸型','圆润'),('发型','短刺发'),('眉眼','明朗'),('配饰','金色发带'),('服饰','青绿长衫')]):
        yy=392+j*81
        _text(r,im,a,792,yy,21,r.MUTED)
        r.inputbox(im,863,yy-8,225,57,b,22)
    _paper(r,im,1144,310,611,531)
    _text(r,im,'形象候选',1171,329,29,r.JADE,bold=True,title=True)
    for i in range(8):
        xx=1167+(i%4)*144; yy=393+(i//4)*190
        _paper(r,im,xx,yy,128,158,i==0)
        path=str(portraits[i%len(portraits)]) if portraits else 'assets/icons/company.png'
        _native(r,im,path,xx+6,yy+5,116,116)
        _text(r,im,f'{i+1:02d}',xx+64,yy+124,19,r.IVORY if i==0 else r.JADE,align='center')
    _text(r,im,'选择形象，再调整面部与服饰',1174,796,20,r.MUTED,width=550)
    return im


def palette(r,im,s):
    _paper(r,im,365,310,430,531)
    _text(r,im,'涂装对象',396,329,29,r.JADE,bold=True,title=True)
    for i,name in enumerate(['公司默认','客运列车','货运列车','公路车辆','船舶与航空']):
        yy=394+i*77;_paper(r,im,384,yy,390,66,i==0)
        _text(r,im,name,408,yy+17,24,r.IVORY if i==0 else r.JADE,bold=i==0)
    _paper(r,im,826,310,929,531)
    _text(r,im,'识别配色',858,329,29,r.JADE,bold=True,title=True)
    _native(r,im,'assets/icons/train.png',862,391,201,184)
    _text(r,im,'公司默认',965,589,23,r.JADE,align='center',bold=True)
    _check(r,im,'子分组继承默认配色',861,665,True,325)
    _text(r,im,'主色：玉绿',1131,383,23,r.JADE,bold=True)
    _text(r,im,'辅色：象牙白',1131,579,23,r.JADE,bold=True)
    colors=['#154E41','#3E9476','#9AB78C','#D6E7C2','#133F62','#507CA8','#89B6BB','#D0E7DD','#7A3033','#B65D46','#D99353','#D8B154','#6B536B','#9D8B91','#9C9D92','#F3E8CA']
    draw=ImageDraw.Draw(im)
    for rowy,chosen in [(431,0),(627,15)]:
        for i,color in enumerate(colors):
            xx=1133+(i%8)*73; yy=rowy+(i//8)*67
            draw.rounded_rectangle((xx,yy,xx+57,yy+51),radius=8,fill=color,outline=r.GOLD,width=2)
            if i==chosen:
                draw.rounded_rectangle((xx-4,yy-4,xx+61,yy+55),radius=10,outline=r.JADE,width=3)
                _text(r,im,'✓',xx+29,yy+4,29,r.IVORY if i<8 else r.JADE,align='center',bold=True)
    _text(r,im,'在同一色板中选择主色与辅色',1134,793,21,r.MUTED,width=564)
    return im


def input_dialog(r,im,s,password=False):
    _paper(r,im,405,329,1296,461)
    r.icon(im,'network' if password else 'orders',458,361,112)
    _text(r,im,'输入访问密码' if password else '编辑名称与数值',606,361,34,r.JADE,bold=True,title=True)
    if password:
        _text(r,im,'目标：青岚联运 / 云途运输',606,427,26,r.JADE)
        _text(r,im,'密码',478,525,26,r.JADE,bold=True)
        r.paste(im,r.nine('reference-input',970,83),604,506)
        _text(r,im,'••••••••',634,527,34,r.JADE)
        _pill(r,im,'显示',1589,511,89,74)
        _check(r,im,'只用于本次服务器或公司验证',608,630,False,910)
        _text(r,im,'密码错误时保留目标，重新输入密码',608,703,22,r.MUTED,width=974)
    else:
        _text(r,im,'公司名称',477,469,25,r.JADE,bold=True)
        r.paste(im,r.nine('reference-input',1003,79),650,451)
        _text(r,im,'云途运输',675,473,27,r.JADE)
        _text(r,im,'4 / 32',1618,477,20,r.MUTED,align='right')
        _text(r,im,'数值',477,594,25,r.JADE,bold=True)
        _pill(r,im,'−',650,572,76,75)
        r.paste(im,r.nine('reference-input',748,79),746,570)
        _text(r,im,'10,000',1121,591,30,r.JADE,align='center',bold=True)
        _pill(r,im,'＋',1517,572,76,75)
        _text(r,im,'输入范围由当前操作限定',653,704,22,r.MUTED)
    return im


def keyboard(r,im,s):
    _paper(r,im,365,309,1390,534)
    _text(r,im,'公司名称',397,328,24,r.JADE,bold=True)
    r.paste(im,r.nine('reference-input',1121,68),608,316)
    _text(r,im,'云途运输  |',631,333,27,r.JADE)
    keyboard_rows=[
        [('1',1),('2',1),('3',1),('4',1),('5',1),('6',1),('7',1),('8',1),('9',1),('0',1),('-',1),('=',1),('退格',1.7)],
        [('Tab',1.4),('Q',1),('W',1),('E',1),('R',1),('T',1),('Y',1),('U',1),('I',1),('O',1),('P',1),('[',1),(']',1)],
        [('Caps',1.7),('A',1),('S',1),('D',1),('F',1),('G',1),('H',1),('J',1),('K',1),('L',1),(';',1),("'",1),('回车',1.4)],
        [('Shift',2),('Z',1),('X',1),('C',1),('V',1),('B',1),('N',1),('M',1),(',',1),('.',1),('/',1),('Shift',2)],
        [('符号',1.7),('Ctrl',1.4),('空格',6.2),('←',1.3),('→',1.3),('清空',1.7)],
    ]
    for j,keys in enumerate(keyboard_rows):
        xx=391; yy=408+j*75; gap=6
        unit=(1336-gap*(len(keys)-1))/sum(v for _,v in keys)
        for label,units in keys:
            ww=unit*units
            r.btn(im,label,xx,yy,ww,65,'primary' if label=='回车' else 'secondary',24)
            xx+=ww+gap
    _text(r,im,'输入预览',399,805,19,r.MUTED)
    _text(r,im,'按回车确认，按退格删除上一个字符',1723,804,20,r.MUTED,align='right')
    return im


def music(r,im,s):
    _paper(r,im,365,310,1390,531)
    r.icon(im,'settings',417,350,141)
    _text(r,im,'运输主题',624,344,38,r.JADE,bold=True,title=True)
    _text(r,im,'当前列表：自定义 1',627,407,24,r.MUTED)
    r.paste(im,r.nine('reference-slider-track',1021,25),625,481)
    r.paste(im,r.nine('reference-slider-fill',257,25),625,481)
    _native(r,im,'reference-slider-thumb',865,473,42,42)
    _text(r,im,'00:48',626,525,23,r.JADE)
    _text(r,im,'03:10',1647,525,23,r.JADE,align='right')
    for i,label in enumerate(['上一曲','暂停','下一曲']):
        r.btn(im,label,696+i*283,592,257,87,'primary' if i==1 else 'secondary',28)
    _check(r,im,'随机播放',627,727,False,320)
    _check(r,im,'循环列表',1013,727,True,320)
    _text(r,im,'音乐音量',1414,714,23,r.JADE)
    r.paste(im,r.nine('reference-slider-track',189,16),1481,761)
    r.paste(im,r.nine('reference-slider-fill',85,16),1481,761)
    _text(r,im,'45%',1449,750,21,r.MUTED,align='right')
    return im


def render_special(r, im, s):
    """Return a specialized full image, or None to use the generic layout."""
    slug=s['id'].split('-',1)[1]
    if slug=='small-map':return map_screen(r,im,s,False)
    if slug=='linkgraph':return map_screen(r,im,s,True)
    if slug=='extra-viewport':return extra_view(r,im,s)
    if slug=='orders':return orders(r,im,s)
    if slug=='timetable':return timetable(r,im,s)
    if slug=='vehicle-groups':return groups(r,im,s)
    if slug in {'buy-train','buy-road','buy-ship','buy-air'}:return purchase(r,im,s)
    if slug=='company-manager':return manager(r,im,s)
    if slug=='company-livery':return palette(r,im,s)
    if slug=='network-password':return input_dialog(r,im,s,True)
    if slug=='input-query':return input_dialog(r,im,s,False)
    if slug=='on-screen-keyboard':return keyboard(r,im,s)
    if slug=='music-player':return music(r,im,s)
    return None

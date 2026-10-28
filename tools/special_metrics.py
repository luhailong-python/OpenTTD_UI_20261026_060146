"""Metric-specific static UI layouts using catalogue values and painted UI skins.
No simulated business runtime. All figures are the catalogue's offline samples.
"""
from PIL import ImageDraw
import math
import re

CHART_IDS={"65-company-graphs","67-cargo-payment","84-industry-production","85-town-cargo","138-performance-monitor","139-frame-time","145-profit-graph","146-cargo-graph","147-performance-graph","148-value-graph"}
FINANCE_IDS={"60-finances","62-infrastructure","66-performance","92-endgame"}
JADE="#164F45"; TEXT="#253D35"; GOLD="#B78F49"; MUTED="#6A766A"; IVORY="#FFF2D1"
COLORS=["#247C64","#B08A3C","#518A9E","#B45B4F"]

def number(value):
    text=str(value).replace("−","-").replace(",","")
    m=re.search(r"-?\d+(?:\.\d+)?",text)
    value=float(m.group()) if m else 0.0
    return -abs(value) if re.match(r"^\s*-",text) else value

def pretty(value):
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"

def nice_limit(value):
    if value<=0:return 1
    base=10**math.floor(math.log10(value))
    for step in [1,1.5,2,2.5,3,4,5,6,7,8,9,10]:
        if value<=base*step:return base*step
    return base*10

def metric_model(s):
    sid=s["id"];rows=s.get("rows",[]);cols=s.get("columns",[])
    if sid not in CHART_IDS:return None
    if sid=="138-performance-monitor":
        return dict(kind="bar",title="每帧耗时分布",unit="耗时（ms）",xunit="性能项目",labels=[x[0].replace("耗时","") for x in rows[1:]],series=[dict(name="当前耗时",values=[number(x[1]) for x in rows[1:]],color=COLORS[0])],limit=8,frameRate=rows[0][1],sourceRows=rows)
    if sid=="67-cargo-payment":
        # An explicitly illustrative monotone curve at equal distance/quantity.
        # Exact anchor values at day 20 come from the catalogue, not a game formula.
        days=list(range(0,101,10));rates={"旅客":0.010,"煤炭":0.004,"邮件":0.013,"货物":0.007}
        series=[]
        for i,row in enumerate(rows):
            anchor_day=number(row[1]);anchor=number(row[2]);rate=rates.get(row[0],.008)
            values=[anchor*math.exp(-rate*(d-anchor_day)) for d in days]
            series.append(dict(name=row[0],values=values,color=COLORS[i],anchorDay=anchor_day,anchorValue=anchor))
        return dict(kind="line",title=s["title"],unit="示例报酬（£）",xunit="运输时间（天）",labels=[str(d) for d in days],series=series,limit=nice_limit(max(max(x["values"]) for x in series)),anchorDay=20,sourceRows=rows,curveMeaning="Illustrative monotone interpolation; equal distance and quantity; exact 20-day values from catalogue. Not an OpenTTD settlement formula.")
    units={"65-company-graphs":("运输收入（£）","季度"),"145-profit-graph":("经营利润（£）","季度"),"146-cargo-graph":("交付货量（单位）","季度"),"147-performance-graph":("绩效评分（分）","季度"),"148-value-graph":("公司价值（£）","季度"),"84-industry-production":("煤炭数量（吨）","月份"),"85-town-cargo":("旅客数量（人）","月份"),"139-frame-time":("绘制耗时（ms）","经过时间（秒）")}
    unit,xunit=units[sid];labels=[x[0].replace("季度","季").replace("秒","") for x in rows]
    series=[dict(name=("绘制耗时" if sid=="139-frame-time" else cols[j]),values=[number(x[j]) for x in rows],color=COLORS[j-1]) for j in range(1,len(cols))]
    limit=1000 if sid=="147-performance-graph" else nice_limit(max(max(x["values"]) for x in series))
    return dict(kind="line",title=s["title"],unit=unit,xunit=xunit,labels=labels,series=series,limit=limit,sourceRows=rows)

def _box(r,im,x,y,w,h,selected=False):
    r.row(im,x,y,w,h,selected)

def _heading(r,im,text,x=397,y=330,w=1100):
    r.txt(im,text,x,y,30,JADE,w=w,bold=True)

def _legend(r,im,model):
    cargo="anchorDay" in model
    for j,item in enumerate(model["series"]):
        if cargo:
            x=485+(j%2)*600;y=781+(j//2)*32
            label=f"{item['name']}  ·  20天 £ {pretty(item['anchorValue'])}"
        else:
            x=485+j*560;y=803
            suffix=pretty(item["values"][-1]);
            if "£" in model["unit"]:suffix="£ "+suffix
            elif "吨" in model["unit"]:suffix+=" 吨"
            elif "人" in model["unit"]:suffix+=" 人"
            elif "ms" in model["unit"]:suffix+=" ms"
            elif "分" in model["unit"]:suffix+=" 分"
            label=f"{item['name']}  ·  {suffix}"
        d=ImageDraw.Draw(im);d.rounded_rectangle((x,y+6,x+18,y+24),radius=4,fill=item["color"])
        r.txt(im,label,x+31,y,22,item["color"],w=525,bold=True)

def _plot(r,im,s,model):
    _box(r,im,365,310,1390,535)
    _heading(r,im,model["title"],w=1000)
    r.txt(im,model["unit"],480,383,22,MUTED,w=700)
    if "anchorDay" in model:r.txt(im,"同距离、同数量的货物比较",1700,340,22,MUTED,align="right")
    elif s["id"]=="138-performance-monitor":r.txt(im,"画面帧率  "+model["frameRate"],1695,340,26,JADE,bold=True,align="right")
    left,top,right,bottom=480,429,1690,700
    ymax=model["limit"]
    for tick in range(5):
        val=ymax*(4-tick)/4;yy=top+(bottom-top)*tick/4
        r.line(im,left,yy,right,yy,"#D8CCAB",1)
        r.txt(im,pretty(val),left-22,yy-13,20,MUTED,align="right")
    r.line(im,left,top,left,bottom,"#A99B77",2)
    r.line(im,left,bottom,right,bottom,"#A99B77",2)
    labels=model["labels"]
    if model["kind"]=="bar":
        n=len(labels);step=(right-left)/(n+1)
        vals=model["series"][0]["values"]
        for i,(label,value) in enumerate(zip(labels,vals)):
            xx=left+step*(i+1);yy=bottom-value/ymax*(bottom-top)
            ImageDraw.Draw(im).rounded_rectangle((xx-72,yy,xx+72,bottom),radius=12,fill=COLORS[i],outline=GOLD,width=2)
            r.txt(im,pretty(value)+" ms",xx,yy-36,24,COLORS[i],bold=True,align="center")
            r.txt(im,label,xx,bottom+24,24,JADE,w=220,align="center")
        r.txt(im,"当前分类耗时",485,803,22,MUTED,w=950)
    else:
        n=len(labels);step=(right-left)/max(1,n-1)
        for i,label in enumerate(labels):r.txt(im,label,left+i*step,bottom+22,22,MUTED,align="center")
        if "anchorDay" in model:
            anchor_x=left+model["anchorDay"]/100*(right-left)
            for y in range(top,bottom,14):r.line(im,anchor_x,y,anchor_x,min(y+7,bottom),GOLD,2)
            r.txt(im,"20天",anchor_x,top-32,21,GOLD,bold=True,align="center")
        for item in model["series"]:
            points=[(left+i*step,bottom-v/ymax*(bottom-top)) for i,v in enumerate(item["values"])]
            ImageDraw.Draw(im).line(points,fill=item["color"],width=4,joint="curve")
            selected=2 if "anchorDay" in model else len(points)-1
            for i,(xx,yy) in enumerate(points):
                rad=6 if i==selected else 4
                ImageDraw.Draw(im).ellipse((xx-rad,yy-rad,xx+rad,yy+rad),fill=IVORY,outline=item["color"],width=3)
        _legend(r,im,model)
    r.txt(im,model["xunit"],1690,759,22,MUTED,align="right")
    return im

def _small_kpi(r,im,label,value,x,y,w=355,h=146,color=JADE):
    _box(r,im,x,y,w,h)
    r.txt(im,label,x+25,y+19,24,MUTED,w=w-50)
    r.txt(im,value,x+25,y+62,39,color,w=w-50,bold=True)

def _table_rows(r,im,s,x=365,y=310,w=1000,rowh=84):
    cols=s["columns"];rows=s["rows"]
    widths=[.42,.30,.28] if len(cols)==3 else [.48,.52]
    _box(r,im,x,y,w,64,True)
    xx=x+22
    for j,col in enumerate(cols):
        r.txt(im,col,xx,y+17,24,IVORY,w=w*widths[j]-40,bold=True);xx+=w*widths[j]
    for i,values in enumerate(rows):
        yy=y+73+i*rowh;_box(r,im,x,yy,w,rowh-7)
        xx=x+22
        for j,value in enumerate(values):
            color="#A14C3B" if str(value).startswith(("−","-")) else TEXT
            r.txt(im,value,xx,yy+(rowh-33)/2-2,25,color,w=w*widths[j]-39,bold=j==0);xx+=w*widths[j]
    return y+73+len(rows)*rowh

def _finances(r,im,s):
    _table_rows(r,im,s,rowh=88)
    rows=s["rows"];this_year=sum(number(x[1]) for x in rows);last_year=sum(number(x[2]) for x in rows)
    _box(r,im,365,787,1000,58,True)
    r.txt(im,"本年利润  £ "+pretty(this_year),394,802,25,IVORY,bold=True)
    r.txt(im,"上年  £ "+pretty(last_year),1338,804,23,IVORY,align="right")
    for j,line in enumerate(s["details"][:3]):
        m=re.match(r"(.*?)\s+(£.*)",line);label,value=(m.group(1),m.group(2)) if m else ("财务摘要",line)
        _small_kpi(r,im,label,value,1393,310+j*178,355,164)
    return im

def _infrastructure(r,im,s):
    _table_rows(r,im,s,rowh=88)
    total=sum(number(x[2]) for x in s["rows"])
    _box(r,im,365,787,1000,58)
    r.txt(im,"维护设置：按本局规则",394,803,25,JADE,bold=True)
    _small_kpi(r,im,"所列维护费用合计","£ "+pretty(total),1393,310,355,164)
    _small_kpi(r,im,s["rows"][0][0]+"数量",s["rows"][0][1],1393,488,355,164)
    _small_kpi(r,im,s["rows"][3][0],s["rows"][3][1],1393,666,355,164)
    return im

def _performance(r,im,s):
    x,y,w=365,310,1000;_box(r,im,x,y,w,62,True)
    for title,xx in [("指标",390),("当前表现",803),("得分／权重",1187)]:r.txt(im,title,xx,326,24,IVORY,bold=True)
    total=0;maximum=0
    for i,values in enumerate(s["rows"]):
        yy=380+i*44;_box(r,im,x,yy,w,40)
        r.txt(im,values[0],389,yy+4,23,TEXT,w=370,bold=True)
        r.txt(im,values[1],803,yy+4,23,JADE,w=280)
        score,maxscore=[number(z) for z in values[2].split("/")];total+=score;maximum+=maxscore
        ImageDraw.Draw(im).rounded_rectangle((1114,yy+17,1214,yy+25),radius=3,fill="#D8CFAC")
        if score>0:ImageDraw.Draw(im).rounded_rectangle((1114,yy+17,1114+100*score/maxscore,yy+25),radius=3,fill=COLORS[0])
        r.txt(im,values[2],1340,yy+4,23,JADE,w=123,bold=True,align="right")
    _box(r,im,x,792,w,53,True)
    r.txt(im,"总评分",391,803,25,IVORY,bold=True)
    r.txt(im,pretty(total)+" / "+pretty(maximum),1336,803,27,IVORY,bold=True,align="right")
    _box(r,im,1393,310,355,535)
    r.icon(im,"company",1491,342,155)
    r.txt(im,"公司绩效",1570,515,32,JADE,bold=True,title=True,align="center")
    r.txt(im,pretty(total),1570,567,74,JADE,bold=True,align="center")
    r.txt(im,"满分 "+pretty(maximum),1570,662,25,MUTED,align="center")
    r.para(im,"改善车辆利润与运输覆盖，提升各项经营表现。",1424,736,292,24,JADE,maxlines=3,gap=8)
    return im

def _endgame(r,im,s):
    _table_rows(r,im,s,rowh=86)
    _box(r,im,365,785,1000,60)
    r.txt(im,"继续经营，拓展万里运输网络",397,801,27,JADE,bold=True,title=True)
    vals={x[0]:x[1] for x in s["rows"]};score=vals.get("综合评分","642")
    _box(r,im,1393,310,355,535)
    r.icon(im,"company",1491,337,155)
    r.txt(im,"综合评分",1570,511,32,JADE,bold=True,title=True,align="center")
    r.txt(im,score,1570,565,76,JADE,bold=True,align="center")
    r.txt(im,vals.get("评价",""),1570,668,31,GOLD,bold=True,title=True,align="center")
    r.txt(im,vals.get("经营规模",""),1570,756,24,MUTED,w=296,align="center")
    return im

def render_metric(r,im,s):
    sid=s.get("id")
    if sid in CHART_IDS:return _plot(r,im,s,metric_model(s))
    if sid=="60-finances":return _finances(r,im,s)
    if sid=="62-infrastructure":return _infrastructure(r,im,s)
    if sid=="66-performance":return _performance(r,im,s)
    if sid=="92-endgame":return _endgame(r,im,s)
    return None

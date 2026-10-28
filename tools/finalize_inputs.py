from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding="utf-8-sig"))
def write(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=R/'source-art/helicopter.png';im=Image.open(p).convert('RGBA');bbox=im.getbbox();piece=im.crop(bbox);piece.thumbnail((240,240),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(256,256));out.alpha_composite(piece,((256-piece.width)//2,(256-piece.height)//2));dest=R/'assets/cargo/helicopter.png';out.save(dest)
a={"id":"helicopter","file":"assets/cargo/helicopter.png","width":256,"height":256,"border":[0,0,0,0],"pivot":[.5,.5],"source":"source-art/helicopter.png","sourceSha256":sha(p),"cropXYXY":list(bbox),"operation":"原生1254方母图按alpha外包围裁切，等比缩小到240内，加256透明画布；未放大。","sha256":sha(dest),"alphaMin":0,"alphaMax":255,"sourceGenerationRecord":"source-art/helicopter.png.generation.json"}
m=read('docs/asset-cargo-manifest.json');m=[v for v in m if v['id']!='helicopter']+[a];write('docs/asset-cargo-manifest.json',m)
write('assets/cargo/helicopter.png.generation.json',{"file":a['file'],"sha256":a['sha256'],"nativeModelGeneration":False,"route":"deterministic-derivative","operation":a['operation'],"derivedFrom":[{"file":a['source'],"sha256":a['sourceSha256'],"record":a['sourceGenerationRecord']}],"width":256,"height":256,"actualModel":None,"actualQuality":None})
c=read('docs/screen-catalog.json')
repls={
"不能将科技年代当作角色等级":"可用轨道由年份与内容决定",
"没有战力榜或跨服赛季假设":"选择公司查看经营详情",
"货流图不等于新建路线已经成功":"观察容量和流量，及时改善拥堵",
"这里不显示角色采集点或传送点":"查看所有者与清除费用后规划建设",
"没有战斗胜负、复活或关卡星级":"可继续经营当前世界",
"不作为活动日历或签到系统":"确认后将此日期用于当前计划",
"摘要、原因与补充信息分层":"按错误原因调整后重试",
"没有抽卡、保底或货币兑换":"接受试用可提前体验该车型",
"没有手动领取奖励背包":"达成运输条件后自动取得补贴",
"无账号注册或MMORPG区服假设":"选择服务器与公司后加入经营",
"不增加科技树与角色成长配置":"按类别展开经营规则并调整参数"}
phrases=["场景名称为版式样例","预览内容是离线样例","动态覆盖以真实世界数据为准","版式示例不保证所有类型同年开放","车辆数与状态为离线示例","水运速度与造价为版式样例","所有财务样例保持£单位","此处为版式示例曲线","历史数据与示例标签分层","数据为离线样例","脚本名称仅为版式样例","本美术包不包含OpenGFX世界贴图","仅展示准备和下载流程","不需要创建RPG角色"]
changes=[]
for s in c:
 ds=[]
 for d in s.get('details',[]):
  old=d
  for k,v in repls.items():
   if k in d:d=d.replace(k,v)
  if any(t in d for t in phrases):
   if d not in s.setdefault('notes',[]):s['notes'].append(d)
   changes.append({"id":s['id'],"removedFromUI":old});continue
  ds.append(d)
  if d!=old:changes.append({"id":s['id'],"from":old,"to":d})
 s['details']=ds
write('docs/screen-catalog.json',c);write('records/copy-cleanup.json',changes)
print('helicopter exported; copy cleanup',len(changes))


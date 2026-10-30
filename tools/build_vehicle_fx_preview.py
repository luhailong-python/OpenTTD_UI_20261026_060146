from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,html,hashlib
R=Path(__file__).resolve().parents[1];PRE=R/'previews/vehicles';PRE.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
c=json.loads((R/'docs/VEHICLE_PRODUCTION_CONTRACT.json').read_text(encoding='utf-8'));models=json.loads((R/'docs/VEHICLE_RUNTIME_MANIFEST.json').read_text(encoding='utf-8'))['models']
families=[]
for f in c['families']:families.append(json.loads((R/f['manifest']).read_text(encoding='utf-8')))
for page in range(3):
 subset=families[page*9:page*9+9];im=Image.new('RGB',(2048,9*248),'#ECEDDF');draw=ImageDraw.Draw(im)
 for r,f in enumerate(subset):
  for k,fr in enumerate(f['frames']):
   pic=Image.open(R/fr['file']);pic.thumbnail((225,215));x=k*256+(256-pic.width)//2;y=r*248+18;im.paste(pic,(x,y),pic)
   draw.text((k*256+15,r*248+227),f['familyId']+' / '+fr['direction'],font=small,fill='#204C3C')
 im.save(PRE/f'facings-{page+1}.jpg',quality=93)
overview=Image.new('RGB',(1800,1350),'#F2EEDC');draw=ImageDraw.Draw(overview)
for i,f in enumerate(families):
 pic=Image.open(R/f['frames'][3]['file']);pic.thumbnail((280,220));x=i%6*300+(300-pic.width)//2;y=i//6*270;overview.paste(pic,(x,y),pic);draw.text((i%6*300+12,y+231),f['familyId'],font=font,fill='#204C3C')
overview.save(PRE/'family-overview.jpg',quality=94)
# Mechanical rotor assembly preview, all imagery traceable to painted originals.
rot=json.loads((R/'assets/world/vehicles/rotor/manifest.json').read_text(encoding='utf-8'));hf=json.loads((R/'assets/world/vehicles/families/air-helicopter/manifest.json').read_text(encoding='utf-8'));gif=[]
for phase in range(8):
 im=Image.new('RGBA',(1000,650),'#253F38')
 for col,face in enumerate(['SE','NE']):
  body=Image.open(R/f'assets/world/vehicles/families/air-helicopter/{face}.png');left=col*500;top=100;im.alpha_composite(body,(left,top));r=Image.open(R/f'assets/world/vehicles/rotor/phase-{phase:02}.png').resize((461,461),Image.Resampling.LANCZOS);anchor=rot['attachments'][face]['mainRotorHubPx'];im.alpha_composite(r,(round(left+anchor[0]-230.5),round(top+anchor[1]-230.5)))
 gif.append(im.convert('RGB'))
gif[0].save(PRE/'helicopter-rotor.gif',save_all=True,append_images=gif[1:],duration=42,loop=0,disposal=2)
# Representative native-family and visible loaded state inspection, no new art.
selected=[29,34,59,64,91,96,116,120,128,140,160,180,204,205,208,215]
comparison=Image.new('RGB',(1600,math.ceil(len(selected)/4)*420),'#EDEDDD');draw=ImageDraw.Draw(comparison)
for i,mid in enumerate(selected):
 m=models[mid];e=m['sprites'][1];states=e['states'];p=next((s['file']for s in states if s['state']=='loaded'),e['body']);pic=Image.open(R/p);pic.thumbnail((385,360));x=i%4*400+(400-pic.width)//2;y=i//4*420;comparison.paste(pic,(x,y),pic);draw.text((i%4*400+12,y+368),f'{mid:03} {m["familyId"]}',font=font,fill='#204C3C');draw.text((i%4*400+12,y+392),str(m['cargo']),font=small,fill='#40604D')
comparison.save(PRE/'model-samples.jpg',quality=94)
simple=[]
for m in models:simple.append({'id':m['id'],'name':m['upstreamName'],'family':m['familyId'],'type':m['transport'],'cargo':m['cargo'],'sprites':[{'direction':e['direction'],'body':e['body'],'states':e['states']}for e in m['sprites']]})
body='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>云途万里 · 载具与特效美术验收</title><style>
@font-face{font-family:sc;src:url(../../assets/fonts/NotoSansSC-Variable.ttf)}*{box-sizing:border-box}body{margin:0;background:#e9eadc;color:#234b3d;font:15px sc,system-ui}header{background:#205747;color:#fff8df;padding:22px 4vw;position:sticky;top:0;z-index:2;box-shadow:0 2px 8px #7897}h1{margin:0 0 8px;font-size:25px}p{margin:6px 0;line-height:1.7}.tools{display:flex;gap:12px;flex-wrap:wrap;margin-top:13px}select,button{border:1px solid #bcad75;border-radius:10px;padding:8px 12px;background:#fffae8;color:#235342;font:inherit;cursor:pointer}button.on{background:#c8ddba}main{padding:24px 4vw}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}article{border:1px solid #c3b681;background:#fff9e9;border-radius:16px;overflow:hidden;padding:12px}article img{width:100%;height:210px;object-fit:contain;background:linear-gradient(45deg,#e5e8da 25%,transparent 25%,transparent 75%,#e5e8da 75%),linear-gradient(45deg,#e5e8da 25%,#f4f4e9 25%,#f4f4e9 75%,#e5e8da 75%);background-size:24px 24px;background-position:0 0,12px 12px;border-radius:10px}small{color:#728066}h2{font-size:20px;margin-top:35px}a{color:#ead899}section img.overview{width:100%;max-width:1800px;border-radius:16px}#count{font-weight:600}</style>
<header><a data-brand-navigation="true" href="../../index.html" style="display:inline-flex;align-items:center;gap:10px;color:inherit;text-decoration:none;margin:0 0 12px"><img src="../../branding/yuntu-wanli/logo-symbol-64.png" alt="云途万里" width="48" height="48" style="object-fit:contain"><span>云途万里 · 美术交付首页</span></a><h1>云途万里 · 载具与特效美术验收</h1><p>27幅原生家族图集 / 216个朝向 / 256个原始EngineID映射。型号采用涂装、轨制底架与可见货载衍生；密闭车体空满载可共用。Unity尚未接入。</p><div class="tools"><select id="family"><option value="">全部家族</option></select><select id="direction"></select><select id="state"><option value="body">空载／机体</option><option value="loaded">满载（适用时）</option></select><button id="turn">自动轮看八向</button><span id="count"></span></div></header><main><div id="cards" class="grid"></div><h2>全部家族概览</h2><section><img class="overview" src="family-overview.jpg"></section><h2>旋翼机械周期与定位</h2><p>采用四叶停转绘图作机械部件，正式运动帧通过刚体旋转与平面投影衍生，未调用视频模型。此处为美术装配预览。</p><img src="helicopter-rotor.gif" style="max-width:100%;border-radius:16px"><h2>公共效果及灾难实体</h2><p>覆盖12个EffectVehicle类型和15个DisasterSubType；后者包括6个影子和1个旋翼实体。动画为原生绘制关键帧与已声明的透明度、插值或投影衍生。</p><div id="effects" class="grid"></div></main><script>const models=MODEL_DATA;const clips=CLIP_DATA;let index=0,timer=null;const dirs=['N','NE','E','SE','S','SW','W','NW'];const fam=document.querySelector('#family'),direction=document.querySelector('#direction'),state=document.querySelector('#state');for(const f of [...new Set(models.map(m=>m.family))])fam.add(new Option(f,f));for(const d of dirs)direction.add(new Option(d,d));direction.value='SE';function render(){const list=models.filter(m=>!fam.value||m.family===fam.value);document.querySelector('#count').textContent=list.length+' 个型号';document.querySelector('#cards').replaceChildren(...list.map(m=>{const e=m.sprites[dirs.indexOf(direction.value)],s=e.states.find(s=>s.state===state.value),article=document.createElement('article'),img=document.createElement('img'),name=document.createElement('p'),info=document.createElement('small');img.loading='lazy';img.src='../../'+(s?s.file:e.body);img.alt=m.name+' '+direction.value;name.textContent=String(m.id).padStart(3,'0')+' · '+m.name;info.textContent=m.family+' / '+(m.cargo||'机体');article.append(img,name,info);return article;}));}fam.onchange=direction.onchange=state.onchange=render;document.querySelector('#turn').onclick=()=>{if(timer){clearInterval(timer);timer=null;return;}timer=setInterval(()=>{direction.value=dirs[(dirs.indexOf(direction.value)+1)%8];render()},800)};for(const clip of clips){const article=document.createElement('article'),img=document.createElement('img'),p=document.createElement('p');img.loading='lazy';img.src='../world/effects/'+clip.gif;img.alt=clip.id;p.textContent=clip.id;article.append(img,p);document.querySelector('#effects').append(article)}render();</script></html>'''
clips=[{'id':p.stem,'gif':p.name}for p in sorted((R/'previews/world/effects').glob('*.gif'))]
body=body.replace('MODEL_DATA',json.dumps(simple,ensure_ascii=False).replace('</','<\\/')).replace('CLIP_DATA',json.dumps(clips,ensure_ascii=False));(PRE/'index.html').write_text(body,encoding='utf-8')
print('vehicle directions3pages +family/model contacts +rotorGIF +standalone HTMLinspection gallery')

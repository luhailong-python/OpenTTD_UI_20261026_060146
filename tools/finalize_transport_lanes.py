"""Verify actual lane/structure RGBA assembly and publish all-state art sheets."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math,datetime,ast
import numpy as np
R=Path(__file__).resolve().parents[1];OUT=R/'previews/world/transport-lanes';OUT.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def image(p):return Image.open(R/p).convert('RGBA')
M=load(R/'assets/world/infrastructure/transport-runtime/manifest.json');BY={a['id']:a for a in M['assets']};checks=[]
def check(k,v,**x):checks.append({'id':k,'level':'OK'if v else'FAIL',**x})
def reassembly(label,original,layers,order):
 out=Image.new('RGBA',image(original).size)
 for n in order:
  if layers.get(n):out.alpha_composite(image(layers[n]))
 ar=np.asarray(image(original)).copy();ar[ar[:,:,3]==0,:3]=0
 check(label+'.rgba',np.array_equal(np.asarray(out),ar))
font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),13)
pages=[]
def sheets(prefix,rows,count=24):
 for start in range(0,len(rows),count):
  part=rows[start:start+count];cols=4;cw=320;ch=318
  canvas=Image.new('RGB',(cols*cw,math.ceil(len(part)/cols)*ch),'#e7e0cc');d=ImageDraw.Draw(canvas)
  for j,(label,path) in enumerate(part):
   im=image(path);bb=im.getbbox();im=im.crop(bb);im.thumbnail((300,270),Image.Resampling.LANCZOS)
   cell=Image.new('RGBA',(cw,280),'#eae5d8'if j%2==0 else'#23433b');cell.alpha_composite(im,((cw-im.width)//2,280-im.height-4))
   x=j%cols*cw;y=j//cols*ch;canvas.paste(cell.convert('RGB'),(x,y));d.text((x+5,y+284),label,font=font,fill='#12392f')
  p=OUT/(prefix+'-'+str(start//count+1).zfill(2)+'.jpg');canvas.save(p,quality=96)
  savej(Path(str(p)+'.derivation.json'),{'operation':'Actual final PNG Alpha composites on alternating light/dark, content-crop and proportional downsample only; no image synthesis','derivedFrom':[{'file':p,'sha256':sha(R/p)}for _,p in part]})
  pages.append({'label':prefix+' '+str(start//count+1),'image':p.relative_to(R).as_posix(),'sha256':sha(p),'states':[x[0]for x in part]})
tunnels=[];bridges=[];bridge_maps=[]
for m in M['coverageMappings']:
 rid=m['requirementId']
 if rid.startswith('tunnel-'):
  check(rid+'.12states',len(m['states'])==12)
  for s in m['states']:
   label=rid+' '+s['direction']+' '+s['climate'];tunnels.append((label,s['image']));reassembly(label,s['image'],s['layers'],s['layerOrder'])
   check(label+'.floor-visibility',s['floorVisible']==(s['direction']in['SE','SW']))
   if s['floorVisible']:
    check(label+'.full-registered-canvas',image(s['layers']['floor']).size==(512,512)and s['floorOffsetPx']==[0,0])
    check(label+'.material-and-mask',all((R/s[x]).exists()for x in['laneMaterialUV','removedFloorMask','cleanPortalImage']))
 if rid.startswith('bridge-'):
  bridge_maps.append(m);check(rid+'.4states',len(m['states'])==4)
  for s in m['states']:
   for role,p in s['pieces'].items():
    label=rid+' '+s['axis']+' '+s['deck']+' '+role;reassembly(label,p['image'],p['layers'],p['layerOrder'])
    lane=image(p['layers']['lane']);mask=np.asarray(image(p['laneOwnershipMask']))[:,:,3]>0
    check(label+'.lane-registered',lane.size==(384,384)and p['laneOffsetPx']==[0,0])
    check(label+'.lane-no-exterior',not np.any((np.asarray(lane)[:,:,3]>0)&~mask))
    if role in['north','south']:bridges.append((label,p['image']))
   # Each source type has the same periodic flat painting in all four alias
   # roles. Include it once, but verify all roles independently above.
   flat=next(p for p in s['pieces'].values()if p.get('aliasDeclared'))
   bridges.append((rid+' '+s['axis']+' '+s['deck']+' flat',flat['image']))
   if 'head'in s['pieces']and'north'in s['pieces']:
    check(rid+s['axis']+s['deck']+'.head-native-pose',np.array_equal(np.asarray(image(s['pieces']['head']['image'])),np.asarray(image(s['pieces']['north']['image']))))
check('all-tunnel-states',len(tunnels)==72);check('13-source-bridge-types',len(bridge_maps)==13)
for a in M['assets']:
 check(a['id']+'.hash',sha(R/a['image'])==a['sha256'])
 check(a['id']+'.source-records',all((R/s['file']).exists()and sha(R/s['file'])==s['sha256']and(R/s['record']).exists()for s in a['derivedFrom']))
sheets('tunnels-all-climates',tunnels);sheets('bridges-both-axes-road-rail-flat-and-ramps',bridges)
materials=[(a['id'],a['image'])for a in M['assets']if a['id'].startswith('lane-source-')];sheets('actual-painted-uv-materials',materials)
# Close views keep the real pixel dimensions; displayed zoom does not create detail.
details=[('rail SE portal','tunnel-rail-SE-normal'),('road SW portal','tunnel-road-SW-normal'),('tram SE portal','tunnel-tram-SE-normal'),('truss rail floor / foreground','bridge-09-girder-X-rail'),('tubular Y rail under roof','bridge-10-tubular-Y-rail'),('wood road +32 ramp','bridge-00-wood-X-road-north')]
for label,aid in details:
 a=BY[aid];im=image(a['image']);bb=im.getbbox();im=im.crop(bb);bg=Image.new('RGBA',im.size,'#23433b');bg.alpha_composite(im);p=OUT/(aid+'-detail.png');bg.convert('RGB').save(p)
 savej(Path(str(p)+'.derivation.json'),{'operation':'1:1 content crop + flat review background; not generated or enlarged','derivedFrom':[{'file':a['image'],'sha256':a['sha256']}],'sourceCropPx':list(bb)})
 pages.append({'label':label,'image':p.relative_to(R).as_posix(),'sha256':sha(p),'states':[aid]})
cards=''.join('<figure><figcaption>'+p['label']+'</figcaption><a href="../../../'+p['image']+'"><img loading="lazy" src="../../../'+p['image']+'"></a></figure>'for p in pages)
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>交通走廊完整拼装验收</title><style>body{background:#203f36;color:#f3e6c9;font:16px sans-serif;margin:24px}h1{font-size:25px}figure{margin:18px 0;padding:14px;background:#eee5d0;color:#173d31;border-radius:12px}img{display:block;max-width:100%;height:auto;margin-top:10px}a{color:inherit}</style><h1>交通走廊完整拼装验收</h1><p>72隧道状态；13桥型×双轴×公路/铁路×平跨及正负坡。桥头与north同姿源图逐像素核实，其他周期片复用已明确。全部路轨采真实原画；预览不等于Unity运行验证。</p>'+cards+'</html>'
(OUT/'index.html').write_text(html,encoding='utf-8')
tree=ast.parse((R/'tools/build_transport_runtime.py').read_text(encoding='utf-8'));frozen={}
for n in tree.body:
 name=n.name if isinstance(n,ast.FunctionDef)else n.targets[0].id if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)else None
 if name in['LANDMARKS','_project_deck_quad']:frozen[name]=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()
report={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formalPNGIncludingMaskData':len(M['assets']),'originalRuntimeRolePNG':1034,'addedLaneUVMaskAndCleanPortalPNG':len(M['assets'])-1034,'maskDataPNG':sum(a['category']=='transport-mask-data'for a in M['assets']),'spriteArtPNG':sum(a['category']!='transport-mask-data'for a in M['assets']),'tunnelStates':len(tunnels),'bridgeSourceTypes':len(bridge_maps),'bridgeConcreteStates':sum(len(m['states'])for m in bridge_maps),'bridgeRoleMappings':sum(len(s['pieces'])for m in bridge_maps for s in m['states']),'checks':len(checks),'failures':[x for x in checks if x['level']=='FAIL'],'checksDetail':checks,'pages':pages,'frozenGeometryASTHashes':frozen,'visualReview':'pending actual review of all pages; this mechanical result does not itself pass visual review','unityValidated':False}
savej(R/'records/world-production/transport-lane-validation.json',report)
print(json.dumps({k:v for k,v in report.items()if k not in['checksDetail','pages']},ensure_ascii=False))

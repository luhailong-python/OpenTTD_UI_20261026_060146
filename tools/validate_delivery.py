from pathlib import Path
from PIL import Image,ImageFont
import json,hashlib,datetime,collections,re
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 checks=[];fail=[];glyph_missing=[]
 def ck(name,condition,detail=None):
  q={'name':name,'passed':bool(condition)}
  if detail is not None:q['detail']=detail
  checks.append(q)
  if not condition:fail.append(q)
 master=load('docs/UI_MASTER_MANIFEST.json');screens=master['screens'];src=load('docs/ui-source-inventory.json')
 ids={s['id']for s in screens};covered={i for s in screens for i in s.get('upstreamFeatureIds',[])}
 ck('screen count 149',len(screens)==149);ck('unique IDs',len(ids)==len(screens))
 ck('132 upstream features mapped',all(i['id']in covered for i in src['items']),len(src['items']))
 ck('flow targets valid',all(t in ids for s in screens for t in s['flowTo']))
 image_count=0;state_count=0
 for s in screens:
  p=ROOT/s['designPath'];im=Image.open(p);im.verify();rec=load(s['designPath']+'.generation.json')
  ck(s['id']+' size/hash',Image.open(p).size==(1920,1080)and sha(p)==rec['sha256'])
  ly=load('docs/layouts/'+s['id']+'.json');ck(s['id']+' independent text and placement',bool(ly['textRegions'])and bool(ly['spritePlacements']))
  for sp in ly['spritePlacements']:
   n=sp['asset'];cm={a['id']:a for a in load('docs/asset-common-manifest.json')}
   p2=ROOT/cm[n]['file']if n in cm else Path(n)if Path(n).is_absolute()else ROOT/n
   ck(s['id']+' sprite exists '+n,p2.is_file())
  for st in s['states']:
   p=ROOT/st['previewPath'];im=Image.open(p);im.verify();rec=load(st['previewPath']+'.generation.json')
   ck(s['id']+' state '+st['id'],Image.open(p).size==(960,600)and sha(p)==rec['sha256'])
   if any(z in (st['id']+' '+st['name'])for z in ['confirm','overwrite','abort','sell','确认','覆盖'])or(st.get('action','').startswith('确认')and len(st['action'])>2):
    ly2=load('docs/layouts/states/'+s['id']+'--'+st['id']+'.json')
    ck(s['id']+' confirm has cancel',any(x['text']in ['取消','继续生成']for x in ly2['textRegions']))
   state_count+=1
  image_count+=1
 ck('state count 227',state_count==227)
 assets=load('docs/ASSET_MASTER_MANIFEST.json')['resources'];ck('107 component PNGs',len(assets)==107)
 for a in assets:
  p=ROOT/a['file'];im=Image.open(p)
  ck(a['file']+' size/hash',im.size==(a['width'],a['height'])and sha(p)==a['sha256'])
  ck(a['file']+' RGBA',im.mode=='RGBA')
  b=a.get('border',[0,0,0,0]);ck(a['file']+' border',len(b)==4 and min(b)>=0 and b[0]+b[2]<im.width and b[1]+b[3]<im.height)
  if a['id']!='reference-paper':ck(a['file']+' true transparent alpha',im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getextrema()[1]>0)
  ck(a['file']+' provenance',(ROOT/(a['file']+'.generation.json')).exists()or(ROOT/(a['file']+'.derivation.json')).exists())
  if a.get('sourceGenerationRecord'):ck(a['file']+' original AI record',(ROOT/a['sourceGenerationRecord']).is_file())
 btns=[a for a in assets if a.get('stateFamily')=='button']
 if not btns:btns=[a for a in assets if a['id']in ['button_primary_normal','button_primary_pressed','button_primary_selected','button_secondary_normal','button_secondary_pressed','button_disabled']]
 ck('six button states same canvas',len(btns)==6 and len({(a['width'],a['height'])for a in btns})==1)
 source_records=[ROOT/'assets/transport-valley.png.generation.json',ROOT/'assets/world-viewport.png.generation.json']+list((ROOT/'source-art').glob('*.generation.json'))
 ck('seven actual image generations',len(source_records)==7)
 for p in source_records:
  q=json.loads(p.read_text(encoding='utf-8'));ck(p.name+' configuration target and actual separated',q['submittedParameters']['model']is None and q['submittedParameters']['quality']is None and q['actualModel']is None and q['actualQuality']is None and len(q['references'])==2 and len(q['sha256'])==64)
 # Glyph coverage is checked against the exact font files used by the renderer.
 maps={}
 for fn,key in [('NotoSansSC-Variable.ttf','Noto Sans SC'),('MaShanZheng-Regular.ttf','Ma Shan Zheng')]:
  ft=ImageFont.truetype(str(ROOT/'assets/fonts'/fn),24);missing=ft.getmask(chr(0x10FFFF));maps[key]=(ft,(missing.size,bytes(missing)))
 glyph_cache={}
 for p in (ROOT/'docs/layouts').glob('*.json'):
  q=json.loads(p.read_text(encoding='utf-8'))
  for t in q['textRegions']:
   for ch in t['text']:
    key=(t['fontFamily'],ch)
    if key not in glyph_cache:
     ft,missing=maps[t['fontFamily']];mask=ft.getmask(ch);glyph_cache[key]=(mask.size,bytes(mask))!=missing
    if not ch.isspace()and not glyph_cache[key]:glyph_missing.append({'screen':q['screenId'],'text':t['text'],'char':ch,'font':t['fontFamily']})
 ck('no missing font glyphs',not glyph_missing,glyph_missing[:30])
 ck('layout canvas overflow',not load('records/layout-validation.json')['canvasOverflowOrTextIssues'])
 ck('repair render issues',not load('records/qa-repairs.json')['issues'])
 b=load('records/browser-validation.json');ck('browser checks',b['passed'],len(b['checks']))
 report={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'静态UI美术与本地预览；未在Unity运行','screenCount':149,'stateCount':state_count,'featureCount':len(src['items']),'formalPNGCount':len(assets)+2,'checkCount':len(checks),'passed':not fail,'failures':fail,'glyphMissing':glyph_missing,'checks':checks}
 (ROOT/'records/final-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items()if k!='checks'},ensure_ascii=False))
if __name__=='__main__':main()


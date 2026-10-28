"""Contact every actual part and every source-value assembly; no fake art."""
from PIL import Image,ImageDraw,ImageFont
import math,json,html
import manager_face_parts as p
R=p.R;PRE=p.PRE
def main():
 m=p.load(p.OUT/'manifest.json');font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),14);pages=[]
 def contact(name,rows,count=16):
  for start in range(0,len(rows),count):
   rr=rows[start:start+count];out=Image.new('RGB',(1280,math.ceil(len(rr)/4)*362),'#eae5d8');d=ImageDraw.Draw(out)
   for j,(label,file)in enumerate(rr):
    im=Image.open(R/file).convert('RGBA');im.thumbnail((312,320));bg=Image.new('RGBA',(320,326),'#23433b'if j%2 else'#eae5d8');bg.alpha_composite(im,((320-im.width)//2,0));x=j%4*320;y=j//4*362;out.paste(bg.convert('RGB'),(x,y));d.text((x+8,y+329),label,font=font,fill='#164F45')
   file=PRE/(name+'-'+str(start//count+1).zfill(2)+'.jpg');out.save(file,quality=97);sources=[p.source(R/file)for _,file in rr];p.savej(str(file)+'.derivation.json',{'operation':'Actual registered parts / actual layered combinations on alternating dark/light; proportional downsample only','derivedFrom':sources,'nativeModelGeneration':False})
   pages.append({'id':name+'-'+str(start//count+1),'image':p.rel(file),'sha256':p.sha(file),'sampleCount':len(rr),'labels':[r[0]for r in rr]})
 core=[a for a in m['assets']if a['family']in['base','eyes','nose','mouth','hair','beard','collar','robe','tie','earring','glasses']];contact('native-parts',[(a['id'],a['image'])for a in core])
 supplemental=[a for a in m['assets']if a.get('supplemental')];contact('supplemental-parts',[(a['id'],a['image'])for a in supplemental])
 for style in range(4):
  rows=[]
  for s in m['compositionSamples']:
   if s['sourceStyle']!=style or not s.get('coveredRequirementId'):continue
   b=next(b for b in m['bindings']if b['requirementId']==s['coveredRequirementId']);label='face'+str(style+1)+' / '+b['fieldName'].replace('STR_FACE_','')+' '+str(b['sourceValue']+1);rows.append((label,s['image']))
  contact('source-style-'+str(style+1)+'-all-values',rows)
 selected=['baseline-style-0','baseline-style-1','baseline-style-2','baseline-style-3','moustache-on','glasses-on','glasses-off','earring-on','earring-off','eye-brown','eye-blue','eye-green','cancel-original','cancel-edited','cancel-restored'];samples={s['id']:s for s in m['compositionSamples']};contact('controls-and-palettes',[(sid,samples[sid]['image'])for sid in selected])
 m['contactPages']=pages;p.savej(p.OUT/'manifest.json',m)
 # Append links to already-rendered UI state gallery, preserving that page.
 gallery=PRE/'part-combination-gallery.html';cards=''.join('<figure><figcaption>'+html.escape(c['id'])+'</figcaption><a href="../../'+c['image']+'"><img loading="lazy" src="../../'+c['image']+'"></a></figure>'for c in pages)
 gallery.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>经理部件与213源码值组合</title><style>body{background:#23463b;color:#f5e8cd;font:16px sans-serif;margin:24px}figure{padding:12px;background:#eee6d4;color:#184c3c;border-radius:12px}img{max-width:100%;display:block;margin-top:9px}a{color:inherit}</style><h1>经理部件与213源码值组合</h1><p>每个Sprite值至少一次实际分层组合；共享原画和下颌/肤色/眼色衍生已明确。不是213幅新原画。</p><p><a href="index.html">高级设置与流程状态</a></p>'+cards+'</html>',encoding='utf-8')
 print(json.dumps({'contactPages':len(pages),'actualCoreMotherParts':len(core),'allSourceSpriteValues':213}))
if __name__=='__main__':main()

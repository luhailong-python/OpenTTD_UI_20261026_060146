"""Actual layered manager portraits in existing painted UI controls; PNG only."""
from pathlib import Path
from PIL import Image
import json,html
import render_screens as ui
import manager_face_parts as p
R=p.R;OUT=p.OUT;PRE=p.PRE
NAMES={'STR_FACE_CHIN':'下巴','STR_FACE_EYEBROWS':'眉眼','STR_FACE_MOUSTACHE':'胡须','STR_FACE_LIPS':'嘴唇','STR_FACE_NOSE':'鼻子','STR_FACE_HAIR':'发式','STR_FACE_COLLAR':'衣领','STR_FACE_JACKET':'外袍','STR_FACE_TIE':'领饰','STR_FACE_EARRING':'耳饰','STR_FACE_GLASSES':'眼镜','STR_FACE_EYECOLOUR':'眼色'}
def main():
 m=p.load(OUT/'manifest.json');samples={s['id']:s for s in m['compositionSamples']};spec=p.extract(R);states=[];(PRE/'states').mkdir(parents=True,exist_ok=True)
 def portrait(im,sid,x,y,w=390,h=390):ui.contain(im,samples[sid]['image'],x,y,w,h)
 def state(sid,title,sample='baseline-style-0',scroll=0,note=''):
  ui.CURRENT='manager-'+sid;ui.regions=[];ui.placements=[];ui.issues=[]
  im=ui.bg();ui.header(im,{'id':'manager-'+sid,'title':title.replace(' · ',' '),'subtitle':'公司经理 · 自由搭配五官与服饰 · 高级外观设置','system':'公司','layout':'经理外观设置','tabs':[]})
  ui.row(im,375,278,445,530);portrait(im,sample,399,305,397,397);s=samples[sample]
  ui.txt(im,'外观样式 '+str(s['sourceStyle']+1),597,719,23,ui.JADE,align='center');ui.txt(im,'独立五官与服饰 · 道家 Q 版',597,760,19,ui.MUTED,align='center')
  for i,(label,kind)in enumerate([('载入码','secondary'),('保存码','secondary'),('随机外观','secondary')]):ui.btn(im,label,375+i*151,825,143,62,kind,19)
  ui.row(im,872,278,878,70,True);ui.txt(im,'样式 '+str(s['sourceStyle']+1)+' / 4',904,297,26,ui.IVORY,bold=True);ui.txt(im,'高级设置',1707,300,23,ui.IVORY,align='right')
  fields={f['sourceVarIndex']:f for f in spec['styles'][s['sourceStyle']]['fields']};order=s['uiOrder'];visible=order[scroll:scroll+7]
  for i,var in enumerate(visible):
   f=fields[var];value=s['selectedSourceValues'][str(var)]if str(var)in s['selectedSourceValues']else s['selectedSourceValues'][var];y=365+i*62;ui.row(im,872,y,850,55,i==0)
   text_colour=ui.IVORY if i==0 else ui.JADE;suffix='开关'if f['kind']=='Toggle'else'造型'if f['name']in['STR_FACE_GLASSES','STR_FACE_MOUSTACHE','STR_FACE_EARRING']else'';ui.txt(im,NAMES[f['name']]+suffix,898,y+12,22,text_colour,w=300)
   if f['kind']=='Toggle':ui.btn(im,'开启'if value else'关闭',1475,y+5,222,44,'primary'if value else'secondary',20)
   else:
    for glyph,x in[('‹',1410),('›',1660)]:ui.paste(im,ui.nine('button_secondary_normal',55,44),x,y+5);ui.txt(im,glyph,x+27,y+11,23,ui.JADE,align='center')
    ui.txt(im,(['棕色','蓝色','绿色'][value]if f['kind']=='Palette'else str(value+1)+' / '+str(f['validValues'])),1565,y+10,22,text_colour,align='center')
  ui.paste(im,ui.nine('reference-input',20,427),1730,365);ui.paste(im,ui.nine('button_primary_normal',16,90),1732,367+round(scroll/max(1,len(order)-7)*330))
  ui.txt(im,str(scroll+1)+'—'+str(min(len(order),scroll+7))+' / '+str(len(order))+' 项',1715,812,18,ui.MUTED,align='right')
  if note:ui.txt(im,note,875,846,20,ui.MUTED,w=870)
  ui.btn(im,'取消',1168,896,242,71,'pressed'if sid=='cancel-restores-original'else'secondary',25);ui.btn(im,'应用外观',1430,896,298,71,'primary',25)
  return im,s
 def finish(sid,im,s,description):
  dest=PRE/'states'/(sid+'.png');im.convert('RGB').save(dest);record={'id':sid,'image':p.rel(dest),'sha256':p.sha(dest),'width':1920,'height':1080,'description':description,'compositionSampleId':s['id'],'portraitImage':s['image'],'sourceStyle':s['sourceStyle'],'sourceValues':s['selectedSourceValues'],'layoutRecord':'layouts/manager-customization/'+sid+'.json','facecodeInputText':s.get('facecodeInputText'),'unityValidated':False,'status':'produced-needs-visible-review'}
  p.savej(R/record['layoutRecord'],{'screenId':sid,'canvas':[1920,1080],'regions':ui.regions,'placements':ui.placements,'layoutIssues':ui.issues,'facecodeInputText':s.get('facecodeInputText'),'facecodeField':{'kind':'single-line-text','rectTopLeftXYWH':[875,473,810,75],'dropdown':False,'readOnly':sid=='facecode-save'}if s.get('facecodeInputText')else None,'longFacecodeDisplay':'Full raw value retained here; horizontal scroll/caret in engine. Static design uses fitted ellipsis, never truncates the stored value.','dynamicTextRule':'All business labels, source values and facecodes are separate text in engine. They are baked here only in the design preview.','nativePaintedText':False})
  p.savej(str(dest)+'.derivation.json',{'file':p.rel(dest),'sha256':record['sha256'],'derivedAt':p.now(),'operation':'Actual layered manager PNG in existing painted UI controls; dynamic text layout, no new AI art and no Unity gameplay','derivedFrom':[p.source(R/s['image']),{'file':'docs/asset-common-manifest.json','sha256':p.sha(R/'docs/asset-common-manifest.json'),'record':'docs/asset-common-manifest.json'}],'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'textLayoutRecord':record['layoutRecord']})
  states.append(record)
 for sid,title,sample,scroll,note in[
  ('advanced','经理外观 · 高级设置','baseline-style-0',0,'独立选择部件；切换样式后只显示兼容字段'),
  ('advanced-scroll-bottom','经理外观 · 服饰与配饰','baseline-style-0',4,'高级列表下半部；眼镜开关、衣领、外袍与领饰'),
  ('moustache-on','经理外观 · 胡须开启','moustache-on',0,'胡须下半脸接管鼻/嘴；对应独立字段已从列表隐藏'),
  ('glasses-off','经理外观 · 眼镜关闭','glasses-off',4,'关闭只隐藏眼镜层，保留眉眼与其他原画'),
  ('earring-off','经理外观 · 耳饰关闭','earring-off',2,'耳饰关闭时隐藏独立耳饰层，切换参数保留其他部件')]:
  im,s=state(sid,title,sample,scroll,note);finish(sid,im,s,note)
 # Eye palette comparison: use true sample pixels, including a1:1 eye strip.
 im,s=state('eye-colours','经理外观 · 三色虹膜','eye-brown',0,'眼色只作用于虹膜所有权区域')
 ui.panel(im,855,350,913,482)
 for i,(name,label)in enumerate([('brown','棕色'),('blue','蓝色'),('green','绿色')]):
  x=879+i*289;ui.row(im,x,370,272,420);portrait(im,'eye-'+name,x+6,412,260,260);ui.txt(im,label,x+136,389,24,ui.JADE,align='center');part=Image.open(R/samples['eye-'+name]['image']).convert('RGBA').crop((160,195,352,250));ui.paste(im,part,x+40,691);ui.txt(im,'眼部原尺寸对照',x+136,758,17,ui.MUTED,align='center')
 finish('eye-colours',im,s,'Three actual eye palettes; image owner check proves outside-iris pixels unchanged')
 for sid,title,sample,code,message,error in[
  ('facecode-load','载入经理外观码','glasses-on','default/face1:16','外观码有效 · 已载入，眼镜开启',False),
  ('facecode-save','保存经理外观码','glasses-on','default/face1:16','外观码已保存 · 可在其他存档中载入',False),
  ('facecode-invalid','外观码格式错误','baseline-style-0',('unknown/style42:'+'18446744073709551616'*6)[:127],'无法识别样式或数值超出范围；当前外观保持不变',True)]:
  im,s=state(sid,title,sample,0,'外观码采用源码的样式标签与bits表示')
  im=Image.alpha_composite(im,Image.new('RGBA',im.size,(11,35,29,90)));ui.panel(im,828,369,912,398);ui.txt(im,title,875,399,33,ui.JADE,bold=True)
  # A facecode is typed text, not a choice list. Reuse the painted input
  # frame without adding the common dropdown glyph.
  ui.paste(im,ui.nine('reference-input',810,75),875,473);ui.txt(im,code,893,495,24,ui.TEXT,w=774)
  ui.para(im,message,877,568,792,24,ui.RED if error else ui.GREEN,maxlines=2,gap=8);ui.btn(im,'重新输入'if error else'确认',1425,661,250,68,'primary',24);ui.btn(im,'取消',1155,661,250,68,'secondary',24)
  finish(sid,im,{**s,'facecodeInputText':code},message)
 im,s=state('cancel-restores-original','取消修改 · 恢复原外观','cancel-restored',0,'取消保留进入窗口时的外观，不保存编辑中的变化');ui.panel(im,850,347,920,486)
 for i,(sample,label)in enumerate([('cancel-edited','编辑中的外观'),('cancel-restored','取消后 · 原外观')]):
  x=876+i*435;ui.row(im,x,369,410,420);portrait(im,sample,x+20,410,370,340);ui.txt(im,label,x+205,758,22,ui.JADE,align='center')
 finish('cancel-restores-original',im,s,'Actual restored composition SHA matches initial original composition')
 m['previewStates']=states;p.savej(OUT/'manifest.json',m)
 cards=''.join('<figure><figcaption>'+html.escape(s['id']+' — '+s['description'])+'</figcaption><a href="../../'+s['image']+'"><img loading="lazy" src="../../'+s['image']+'"></a></figure>'for s in states)
 (PRE/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>经理分层外观与高级状态</title><style>body{background:#23463b;color:#f5e8cd;font:16px sans-serif;margin:24px}figure{padding:12px;background:#eee6d4;color:#184c3c;border-radius:12px}img{max-width:100%;display:block;margin-top:9px}a{color:inherit}</style><h1>经理分层外观与高级状态</h1><p>真实透明部件与静态设计图；235条源码值/状态关系。界面文字独立于正式画件，尚未Unity运行。</p>'+cards+'</html>',encoding='utf-8')
 print(json.dumps({'states':len(states),'manifest':p.rel(OUT/'manifest.json')}))
if __name__=='__main__':main()

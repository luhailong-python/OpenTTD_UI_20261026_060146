from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
import render_screens as r
root=r.ROOT
m=r.readj('docs/UI_MASTER_MANIFEST.json')
extra={'07-save-game','13-rail-signals','17-bridge','69-small-map','70-linkgraph','83-cargo-chain','98-chat','113-script-debug','116-sound-options','135-console'}
selected=[s for s in m['screens']if s['layout']in['detail','build','editor']or s['id']in extra]
# Reuse original complete provenance lists, updating each output hash.
for s in selected:
 im,regs=r.make(s);p=s['designPath'];im.convert('RGB').save(root/p,optimize=True)
 prev=r.readj(p+'.generation.json');r.record_derived(p,s,prev['operation'],prev['derivedFrom'])
 r.savej('docs/layouts/'+s['id']+'.json',{'screenId':s['id'],'referenceResolution':[1920,1080],'textRegions':regs,'spritePlacements':r.placements.copy(),'notes':['QA corrected compact tables, native vehicle views, labels and functional inputs']})
 th=im.convert('RGB');th.thumbnail((480,270));th.save(root/s['thumbnailPath'],quality=85)
for s in m['screens']:
 for st in s['states']:
  im=r.statepreview(s,st);p=st['previewPath'];im.convert('RGB').save(root/p,optimize=True)
  prev=r.readj(p+'.generation.json');r.record_derived(p,s,prev['operation'],prev['derivedFrom'])
  r.savej('docs/layouts/states/'+s['id']+'--'+st['id']+'.json',{'screenId':s['id'],'stateId':st['id'],'referenceResolution':[960,600],'textRegions':r.regions.copy(),'spritePlacements':r.placements.copy()})
r.savej('docs/UI_MASTER_MANIFEST.json',m)
r.savej('records/qa-repairs.json',{'changedScreens':[s['id']for s in selected],'regeneratedStates':227,'issues':r.issues,'fixes':['工具标签内缩并缩小图标','信号/桥型/各交通建设专属选择','详情表行高与字体适配','列车视觉替换轨道图标','地图标签错位','聊天/存档/控制台输入','货物流向图','确认状态增加取消及关闭']})
print('refreshed',len(selected),'screens,227 states;issues',r.issues)


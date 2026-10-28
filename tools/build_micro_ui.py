"""Bind overlooked OpenTTD UI sprites to existing painted assets + functional glyphs.
No native artwork is drawn. Painted layers are crops/downsamples of current assets;
the saved SVG overlays contain only UI lines/arrows/status/data geometry.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json,re,math,html,collections
import numpy as np
import world_pack as wp
R=wp.ROOT;OUT=R/'assets/common/micro-ui';PRE=R/'previews/micro-ui'
GOLD='#c4a166';JADE='#276952';IVORY='#fff4d6';RED='#bf4e42';AMBER='#b47d25'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(f):
 p=R/f;record=next((f+x for x in ['.derivation.json','.generation.json']if(R/(f+x)).is_file()),None)
 return {'file':f,'sha256':wp.sha(p),'record':record}
def fit(f,size):
 im=Image.open(R/f).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail(size,Image.Resampling.LANCZOS);return im
def glyph(im,kind,box=(60,60,90,90),colour=JADE):
 """Functional line glyphs only; retain the same geometry in a standalone SVG."""
 x,y,x2,y2=box;S=4;layer=Image.new('RGBA',(96*S,96*S));d=ImageDraw.Draw(layer);svg=[]
 def line(points,width=3,c=colour):
  for cc,ww in [(GOLD,width+2),(IVORY,width+1),(c,width)]:
   d.line([(round(a*S),round(b*S))for a,b in points],fill=cc,width=round(ww*S),joint='curve');svg.append('<polyline points="'+' '.join(f'{a},{b}'for a,b in points)+f'" fill="none" stroke="{cc}" stroke-width="{ww}" stroke-linejoin="round"/>')
 def rect(b,c=colour):
  a,b0,c0,e=b;line([(a,b0),(c0,b0),(c0,e),(a,e),(a,b0)],2,c)
 cx=(x+x2)/2;cy=(y+y2)/2
 if kind=='plus':line([(cx,y+3),(cx,y2-3)]);line([(x+3,cy),(x2-3,cy)])
 elif kind=='minus':line([(x+3,cy),(x2-3,cy)],3)
 elif kind=='na':
  line([(x+5,cy),(x+9,cy)],3,'#748377');line([(x2-9,cy),(x2-5,cy)],3,'#748377')
 elif kind=='sell-all':
  for off in [0,9,18]:line([(x+4,y+6+off),(x2-4,y+6+off)],3,RED)
 elif kind=='chain':
  rect((x+1,cy-6,x+12,cy+6));rect((x2-12,cy-6,x2-1,cy+6));line([(x+9,cy),(x2-9,cy)],3,RED)
 elif kind=='square':rect((x+4,y+4,x2-4,y2-4))
 elif kind=='cross':line([(x+4,y+4),(x2-4,y2-4)],3,RED);line([(x+4,y2-4),(x2-4,y+4)],3,RED)
 elif kind=='check':line([(x+2,cy),(cx-3,y2-4),(x2-2,y+3)])
 elif kind=='pencil':line([(x+3,y2-3),(x2-3,y+3)],5);line([(x+1,y2-1),(x+5,y2-7)],2)
 elif kind=='copy':rect((x,y,x2-8,y2-8));rect((x+8,y+8,x2,y2))
 elif kind=='livery':
  for k,c in enumerate([JADE,GOLD,RED]):rect((x+3+k*8,y+6,x+9+k*8,y2-6),c)
 elif kind in ['up','down','left','right']:
  if kind=='up':pts=[(cx,y2-3),(cx,y+3)];heads=[(x+4,y+12),(cx,y+3),(x2-4,y+12)]
  elif kind=='down':pts=[(cx,y+3),(cx,y2-3)];heads=[(x+4,y2-12),(cx,y2-3),(x2-4,y2-12)]
  elif kind=='left':pts=[(x2-3,cy),(x+3,cy)];heads=[(x+12,y+4),(x+3,cy),(x+12,y2-4)]
  else:pts=[(x+3,cy),(x2-3,cy)];heads=[(x2-12,y+4),(x2-3,cy),(x2-12,y2-4)]
  line(pts);line(heads)
 elif kind=='swap':
  line([(x+2,y+8),(x2-2,y+8),(x2-9,y+2)]);line([(x2-2,y2-8),(x+2,y2-8),(x+9,y2-2)])
 elif kind=='lock':
  rect((x+5,cy-1,x2-5,y2-3));line([(x+9,cy-1),(x+9,y+5),(x2-9,y+5),(x2-9,cy-1)],2)
 elif kind=='unlock':
  rect((x+5,cy-1,x2-5,y2-3));line([(x+9,cy-5),(x+9,y+5),(x2-9,y+5),(x2-9,cy-1)],2)
 elif kind=='bars':
  for k,h in enumerate([8,14,22]):line([(x+6+k*8,y2-3),(x+6+k*8,y2-3-h)],4)
 elif kind=='ellipsis':
  for k in range(3):line([(x+5+k*10,cy),(x+6+k*10,cy)],4)
 elif kind=='window':rect((x+2,y+3,x2-2,y2-3));line([(x+2,y+10),(x2-2,y+10)],2)
 elif kind=='resize-right':
  for off in [0,9,18]:line([(x+off,y2-2),(x2-2,y+off)],2)
 elif kind=='resize-left':
  for off in [0,9,18]:line([(x+2,y+off),(x2-off,y2-2)],2)
 elif kind=='warning':
  line([(cx,y+2),(x2-2,y2-2),(x+2,y2-2),(cx,y+2)],2,AMBER);line([(cx,y+9),(cx,y2-11)],2);line([(cx,y2-6),(cx,y2-5)],2)
 elif kind=='bubble':rect((x+2,y+3,x2-2,y2-8));line([(cx,y2-8),(cx-5,y2-2),(x+7,y2-8)],2)
 elif kind=='caps':
  line([(x+3,y2-6),(cx,y+3),(x2-3,y2-6)],3);line([(x+7,cy+4),(x2-7,cy+4)],2);line([(x+3,y2-1),(x2-3,y2-1)],2)
 elif kind=='hash':
  line([(x+10,y+2),(x+6,y2-2)],2);line([(x2-6,y+2),(x2-10,y2-2)],2);line([(x+2,y+11),(x2-2,y+11)],2);line([(x+2,y2-10),(x2-2,y2-10)],2)
 im.alpha_composite(layer.resize((96,96),Image.Resampling.LANCZOS));return ''.join(svg)
def recipe(sym):
 n=sym.removeprefix('SPR_');vehicle=next((f for k,f in [('AIRCRAFT','air'),('ROADVEH','bus'),('TRAIN','train'),('SHIP','ship')]if k in n),None)
 if vehicle:
  action='plus'if'CREATE'in n else'cross'if'DELETE'in n else'pencil'if'RENAME'in n else'copy'if'CLONE'in n else'livery'if'LIVERY'in n else'lock'if'REPLACE_ON'in n else'unlock'if'REPLACE_OFF'in n else'swap'if'REPLACE'in n else'sell-all'if'SELL_ALL'in n else'chain'if'SELL_CHAIN'in n else'minus'
  return 'assets/icons/'+vehicle+'.png',action,'vehicle-operation'
 common={'CLOSEBOX':('reference-close',None),'BOX_EMPTY':('reference-checkbox-off',None),'BOX_CHECKED':('reference-checkbox-on',None),'CIRCLE_FOLDED':('reference-step-plus',None),'CIRCLE_UNFOLDED':('reference-step-minus',None)}
 if n in common:return 'assets/common/'+common[n][0]+'.png',common[n][1],'common-control'
 if n.startswith('PROFIT_'):return'assets/icons/money.png',{'NA':'na','NEGATIVE':'down','SOME':'up','LOT':'bars'}[n[7:]],'profit-status'
 if n.startswith('TOWN_RATING_'):return'assets/icons/town.png',{'NA':'na','APPALLING':'down','MEDIOCRE':'minus','GOOD':'up'}[n[12:]],'town-rating'
 if n.startswith('WINDOW_')or n=='LARGE_SMALL_WINDOW':return'assets/common/pointers/components/diamond-frame.png',{'WINDOW_RESIZE_RIGHT':'resize-right','WINDOW_RESIZE_LEFT':'resize-left','WINDOW_SHADE':'up','WINDOW_UNSHADE':'down','WINDOW_DEBUG':'hash','WINDOW_DEFSIZE':'window','LARGE_SMALL_WINDOW':'window'}.get(n,'window'),'window-control'
 if n.startswith('ARROW_')or n in ['OSK_LEFT','OSK_RIGHT']:return'assets/common/pointers/components/chevron.png',None,'direction-control'
 if n.startswith('OSK_'):return'assets/common/pointers/components/diamond-frame.png',{'OSK_CAPS':'caps','OSK_SHIFT':'up','OSK_BACKSPACE':'left','OSK_SPECIAL':'hash'}[n],'keyboard-control'
 if n in ['PIN_UP','PIN_DOWN']:return'assets/common/pointers/markers/SPR_'+n+'.png',None,'window-pin'
 if n=='BLOT':return'assets/common/pointers/components/path-dot.png',None,'palette-marker'
 if n=='SQUARE':return'assets/common/reference-checkbox-off.png',None,'palette-marker'
 rest={'SQUARE':('company','window'),'BLOT':('company','ellipsis'),'LOCK':('company','lock'),'WARNING_SIGN':('help','warning'),'HOUSE_ICON':('town',None),'SHARED_ORDERS_ICON':('orders','copy'),'IMG_PLAY_MUSIC_RTL':('settings','left'),'UNREAD_NEWS':('news','plus'),'EXCLUSIVE_TRANSPORT':('company','lock'),'GROUP_REPLACE_PROTECT':('settings','lock'),'GROUP_REPLACE_ACTIVE':('settings','swap'),'IMG_SWITCH_TOOLBAR':('settings','swap'),'IMG_DELETE_LEFT':('search','left'),'IMG_DELETE_RIGHT':('search','right'),'RENAME':('news','pencil'),'GOTO_LOCATION':('map',None),'CHAT':('network','bubble'),'ADMIN':('settings','lock'),'JOIN':('company','plus'),'PLAYER_SELF':('company','check'),'PLAYER_HOST':('company','bars'),'EXTRA_MENU':('settings','ellipsis'),'IMG_CARGOFLOW':('cargo','swap')}
 base,op=rest[n];return'assets/icons/'+base+'.png',op,'function-status'
def palettes(assets,rows):
 """Keep native painted shading/Alpha; export explicit source company/status colours."""
 colours=[('DarkBlue','#274E8B'),('PaleGreen','#B3D29C'),('Pink','#E6A9BE'),('Yellow','#E3C954'),('Red','#C65B50'),('LightBlue','#8DCBDE'),('Green','#5E9E68'),('DarkGreen','#2E6350'),('Blue','#4D81B3'),('Cream','#E9DCBA'),('Mauve','#B9A1B9'),('Purple','#866DA0'),('Orange','#D99553'),('Brown','#906B4F'),('Grey','#A9B0A8'),('White','#F4F0DC')]
 by={a['id']:a for a in assets};bindings={a['id']:a for a in rows};extra=[]
 for sym,states in [('SPR_SQUARE',[(f'company-{i:02}',name,c)for i,(name,c)in enumerate(colours)]),('SPR_BLOT',[('green','compatible-or-installed','#5E9E68'),('red','incompatible-or-missing','#C65B50'),('amber','warning-or-pending','#D99553')])]:
  base=by[sym];raw=np.array(Image.open(R/base['image']).convert('RGBA'));yy,xx=np.indices(raw.shape[:2]);rgb=raw[...,:3].astype(float)
  mask=((xx>=28)&(xx<=67)&(yy>=28)&(yy<=67))if sym=='SPR_SQUARE'else((rgb[...,1]>rgb[...,0]*1.02)&(rgb[...,1]>rgb[...,2]*1.02));mask&=raw[...,3]>0;bindings[sym]['paletteVariants']=[]
  for state,name,c in states:
   ar=raw.copy();target=np.array([int(c[k:k+2],16)for k in [1,3,5]],float);lum=rgb.mean(-1);shade=np.clip(lum/(220 if sym=='SPR_SQUARE'else 100),.3,1.45);ar[mask,:3]=np.uint8(np.clip(target[None,:]*shade[mask,None],0,255));ident=sym+'--'+state;f='assets/common/micro-ui/'+ident+'.png';Image.fromarray(ar).save(R/f)
   a={**base,'id':ident,'image':f,'sha256':wp.sha(R/f),'category':'palette-variant','derivedFrom':[ref(base['image'])],'operation':'selective colour-grade of actual painted interior; native Alpha/edge/shading preserved; source16company names with project RGB palette, or3compatibility status palettes; no new painting','paletteState':state,'paletteName':name,'paletteRGB':c,'paletteMask':{'rectangleXYXY':[28,28,68,68]}if sym=='SPR_SQUARE'else{'rule':'G>R*1.02 and G>B*1.02 within native Alpha'},'geometryFile':None,'sourceSymbol':sym};wp.writej(Path(str(R/f)+'.derivation.json'),a);extra.append(a);bindings[sym]['paletteVariants'].append({'state':state,'name':name,'file':f,'sha256':a['sha256']})
 assets.extend(extra)
def main():
 OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);text=(R/'reference/OpenTTD/src/table/sprites.h').read_text(encoding='utf8');lines=text.splitlines();rows=[];assets=[]
 usages=collections.defaultdict(list)
 for p in(R/'reference/OpenTTD/src').rglob('*'):
  if p.suffix not in ['.cpp','.h']or p.name=='sprites.h':continue
  for i,l in enumerate(p.read_text(encoding='utf8').splitlines(),1):
   for sym in re.findall(r'\bSPR_\w+\b',l):
    if len(usages[sym])<6:usages[sym].append({'file':wp.rel(p),'line':i})
 for i,line in enumerate(lines,1):
  if not 56<=i<=193:continue
  m=re.search(r'static const SpriteID\s+(SPR_\w+)\s*=\s*([^;]+)',line)
  if not m or any(k in m[1]for k in ['OPENTTD_BASE','HALFTILE_','SIGNALS_BASE']):continue
  sym,expr=m.groups();base,op,category=recipe(sym);srcs=[ref(base)];im=Image.new('RGBA',(96,96));piece=fit(base,(72,72)if not op else(68,62))
  if category=='direction-control':
   target=sym.rsplit('_',1)[1];piece=piece.rotate({'RIGHT':0,'DOWN':-90,'LEFT':180,'UP':90}[target],expand=True)
  im.alpha_composite(piece,((96-piece.width)//2,(96-piece.height)//2-(8 if op else 0)))
  colour=RED if any(k in sym for k in ['NEGATIVE','APPALLING','DELETE','SELL_'])else AMBER if any(k in sym for k in ['MEDIOCRE','_NA'])else JADE
  svg=glyph(im,op,colour=colour)if op else''
  # Groups use a functional bracket to distinguish a fleet action from one vehicle.
  if '_GROUP_'in sym and category=='vehicle-operation':svg+=glyph(im,'window',(8,8,87,70),GOLD)
  sf=f'assets/common/micro-ui/svg/{sym}.svg';(R/sf).parent.mkdir(parents=True,exist_ok=True);(R/sf).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">'+svg+'</svg>',encoding='utf8')
  if svg:srcs.append({'file':sf,'sha256':wp.sha(R/sf),'sourceType':'functional-vector-geometry'})
  f=f'assets/common/micro-ui/{sym}.png';im.save(R/f);n=int(expr)if expr.isdigit() else 4896+int(expr.split('+')[1]);a={'id':sym,'image':f,'width':96,'height':96,'sha256':wp.sha(R/f),'format':'PNG','mode':'RGBA','anchorPx':[48,48],'pivotUnity':[.5,.5],'border':[0,0,0,0],'derivedFrom':srcs,'operation':'existing native-painted source crop/downsample/rotation/composition; optional saved functional UI line glyph only; no new native drawing or AI call','nativeModelGeneration':False,'nativeUpscale':False,'actualModel':None,'actualQuality':None,'sourceSymbol':sym,'sourceSpriteId':n,'category':category,'functionalGlyph':op,'geometryFile':sf if svg else None,'statesContract':{'normal':'this PNG','pressed':'existing button_secondary_pressed, same96icon position','selected':'existing button_primary_selected, same96icon position','disabled':'same96icon at0.40 opacity on existing button_disabled; art-only recommendation','locked':'existing lock micro icon overlay only when function is locked'},'unityImport':{'spriteMode':'Single','meshType':'FullRect','filterMode':'Bilinear','mipMaps':False,'wrapMode':'Clamp','atlasPaddingMin':4,'suggestedDisplayPx':[24,48],'unityValidated':False},'userArtAcceptance':'pending','status':'produced-needs-actual-visual-review'}
  wp.writej(Path(str(R/f)+'.derivation.json'),a);assets.append(a);rows.append({'id':sym,'category':category,'source':{'file':'reference/OpenTTD/src/table/sprites.h','line':i,'expression':expr,'spriteId':n},'usageExamples':usages[sym],'file':f,'sha256':a['sha256'],'operation':a['operation'],'localArtReviewed':False,'functionalMeaning':sym.removeprefix('SPR_')})
 palettes(assets,rows)
 manifest={'schema':'micro-ui-art.v1','createdAt':wp.now(),'assets':assets,'sourceRequirements':len(rows),'actualModel':None,'actualQuality':None,'artSourceClaim':'reuse current hand-painted layers and exact saved functional UI geometry; no new original drawing','userArtAcceptance':'pending','unityValidated':False};wp.writej(OUT/'manifest.json',manifest)
 coverage={'schema':'micro-ui-bindings.v1','createdAt':wp.now(),'referenceCommit':'cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8','sourceFile':{'file':'reference/OpenTTD/src/table/sprites.h','sha256':wp.sha(R/'reference/OpenTTD/src/table/sprites.h'),'lines':[56,193]},'scope':'first UI sprite block incl window controls,4profit,4town rating,all24vehicle-group operations,keyboard/network/depot controls; cursor/selection and world assets separate','sourceRequirements':len(rows),'bindings':rows,'manifest':'assets/common/micro-ui/manifest.json','manifestSHA256':wp.sha(OUT/'manifest.json'),'complete':False,'failed':[],'userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'docs/MICRO_UI_BINDINGS.json',coverage)
 cards=[]
 for a in assets:
  cards.append('<figure><div><img src="../../'+a['image']+'" alt="'+a['id']+'"></div><figcaption>'+a['id']+'</figcaption><p>24px / 48px <img width="24" src="../../'+a['image']+'"><img width="48" src="../../'+a['image']+'"></p></figure>')
 page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>窗口、状态与车队小图标</title><style>body{background:#193e33;color:#f1e6cb;font:14px/1.5 system-ui;margin:0}header,main{max-width:1440px;margin:auto;padding:24px}a{color:#e2bf70}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}figure{margin:0;padding:12px;border:1px solid #799477;border-radius:10px;overflow:hidden}figure div{height:106px;display:grid;place-items:center;background:#eae4d2}figure div img{width:96px;height:96px}figcaption{font-size:12px;overflow-wrap:anywhere}figure p{display:flex;align-items:center;gap:10px}</style><header><h1>窗口、状态与车队小图标 · 实际资源预览</h1><p>'+str(len(rows))+'个源码Sprite显式映射；采用现有手绘部件与独立功能线条，不宣称新增原画。每张固定96×96，实际24/48px检查行。中文操作提示由调用界面独立排版。</p><p><a href="../../index.html">主入口</a> · <a href="../../docs/MICRO_UI_BINDINGS.json">源码与资源绑定</a></p></header><main class="grid">'+''.join(cards)+'</main>';(PRE/'index.html').write_text(page,encoding='utf8')
 font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),12);cols=7;cell=(205,155);contact=Image.new('RGB',(cols*cell[0],math.ceil(len(assets)/cols)*cell[1]),'#1e493b');d=ImageDraw.Draw(contact)
 for k,a in enumerate(assets):
  x=k%cols*cell[0];y=k//cols*cell[1];p=Image.new('RGBA',(cell[0],110),'#eee8d8'if k%2==0 else'#244b3b');p.alpha_composite(Image.open(R/a['image']),(54,7));contact.paste(p.convert('RGB'),(x,y));d.text((x+4,y+114),a['id'].replace('SPR_','')[:30],font=font,fill='#eee8d8')
 contact.save(PRE/'micro-ui-contact.jpg',quality=96);print(json.dumps({'bindings':len(rows),'manifestSHA256':wp.sha(OUT/'manifest.json'),'preview':'previews/micro-ui/index.html'}))
if __name__=='__main__':main()

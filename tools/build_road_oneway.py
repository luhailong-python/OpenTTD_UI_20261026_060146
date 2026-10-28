"""Project current native chevrons/prohibition symbol onto source road surfaces.
Only crop/downsample/rotation/UV/slope projection; no code-drawn replacement art.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import ast,operator,re,json,collections
import world_pack as wp
import build_world_terrain as t
R=wp.ROOT;OUT='assets/world/overlays/road-oneway';PRE=R/'previews/road-oneway'
SLOPES={0:'flat',3:'sw',6:'se',9:'nw',12:'ne'};GROUPS=[('flat',0,{'X':0,'Y':0}),('north',6,{'X':12,'Y':9}),('south',12,{'X':3,'Y':6})]
INVALID0=[0,12,9,8,3,0,1,0,6,4,0,0,2,0,0];INVALID1=[0,0,0,5,0,15,10,15,0,10,15,15,5,15,15]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(f):return{'file':f,'sha256':wp.sha(R/f),'record':f+'.derivation.json'}
def source_numbers():
 text=(R/'reference/OpenTTD/src/table/sprites.h').read_text(encoding='utf8');defs={a:b.strip()for a,b in re.findall(r'(?:static\s+)?(?:constexpr|const)\s+\w+\s+(\w+)\s*=\s*([^;]+);',text)};cache={}
 def val(name):
  if name in cache:return cache[name]
  def ev(n):
   if isinstance(n,ast.Expression):return ev(n.body)
   if isinstance(n,ast.Constant):return n.value
   if isinstance(n,ast.Name):return val(n.id)
   if isinstance(n,ast.BinOp):return{ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul}[type(n.op)](ev(n.left),ev(n.right))
   raise ValueError(name)
  cache[name]=ev(ast.parse(defs[name],mode='eval'));return cache[name]
 return{n:val(n)for n in ['SPR_ONEWAY_BASE','ONEWAY_SLOPE_N_OFFSET','ONEWAY_SLOPE_S_OFFSET','ONEWAY_SPRITE_COUNT']}
def road_foundation(code,axis):
 bits=10 if axis=='X'else 5;z=0
 if code==0:return'None',0,0
 h=wp.corner_heights(code);high=max(h,key=h.get);reduced=wp.CORNERS[high]if code&16 else code
 if not(INVALID0[reduced]&bits):return'Leveled',0,2 if code&16 else 1
 if reduced not in [1,2,4,8]and not(INVALID1[reduced]&bits):return'None',code,0
 effective=(3 if high in ['w','s']else 12)if axis=='X'else(6 if high in ['s','e']else 9)
 return'Inclined'+axis,effective,1 if code&16 else 0
def allowed(axis,drd):return('X_SW'if drd==1 else'X_NE')if axis=='X'and drd<3 else('Y_NW'if drd==1 else'Y_SE')if axis=='Y'and drd<3 else None
def build_flat(axis,drd):
 f='assets/common/pointers/components/'+('forbidden'if drd==3 else'chevron')+'.png';im=Image.open(R/f).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail((58,58)if drd<3 else(64,64),Image.Resampling.LANCZOS)
 angle=0 if drd==3 else({('X',1):-90,('X',2):90,('Y',1):180,('Y',2):0}[(axis,drd)])
 if angle:im=im.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
 uv=Image.new('RGBA',(192,192));at=((192-im.width)//2,(192-im.height)//2);shaft=None
 if drd<3:
  # Literal direction shaft only. The actual painted arrowhead remains native.
  paths={('X',1):[(96,56),(96,110)],('X',2):[(96,136),(96,82)],('Y',1):[(136,96),(82,96)],('Y',2):[(56,96),(110,96)]};points=paths[(axis,drd)];d=ImageDraw.Draw(uv);d.line(points,fill='#cba862',width=12);d.line(points,fill='#fff0c4',width=9);d.line(points,fill='#2d8c69',width=6);shaft=OUT+f'/svg/shaft-{axis}-drd{drd}.svg';(R/shaft).parent.mkdir(parents=True,exist_ok=True);pp=' '.join(f'{x},{y}'for x,y in points);(R/shaft).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">'+''.join(f'<polyline points="{pp}" fill="none" stroke="{c}" stroke-width="{w}"/>'for c,w in [('#cba862',12),('#fff0c4',9),('#2d8c69',6)])+'</svg>',encoding='utf8')
 uv.alpha_composite(im,at);flat=t.project(uv)
 return flat,ref(f),{'sourceNativeCropScale':'downsample only','sourceUVCanvas':[192,192],'sourceUVComponentSize':list(im.size),'sourceUVOffset':list(at),'rotationDegreesCCW':angle,'functionalShaftSVG':shaft,'worldUVConvention':'UV x grows in worldY/SE; UV y grows in worldX/SW; project screen.x=128+(worldY-worldX)*128'}
def main():
 (R/OUT).mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);nums=source_numbers();assets=[];bindings=[];flats={};font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),14)
 for name,offset,ss in GROUPS:
  for axis in ['X','Y']:
   for drd in [1,2,3]:
    code=ss[axis];flat,source,recipe=build_flat(axis,drd);flats[(axis,drd)]=flat;im,points,heights=wp.projected_slope(flat,code);slot=offset+(0 if axis=='X'else 3)+drd-1;ident=f'road-oneway-{slot:02d}-{axis}-drd{drd}-{name}';f=OUT+'/'+ident+'.png';im.save(R/f);z=0 if not code else 4
    a={'id':ident,'image':f,'width':256,'height':192,'format':'PNG','mode':'RGBA','sha256':wp.sha(R/f),'category':'road-ground-direction-overlay','anchorPx':[128,128],'pivotUnity':[.5,1/3],'border':[0,0,0,0],'logicalFootprint':[1,1],'sourceRequirementIds':['road-oneway-markings'],'sourceSymbol':'SPR_ONEWAY_BASE','sourceSpriteOffset':slot,'sourceSpriteId':nums['SPR_ONEWAY_BASE']+slot,'axis':axis,'connectionMask':10 if axis=='X'else 5,'disallowedRoadDirectionBits':drd,'allowedTrackdir':allowed(axis,drd),'effectiveSlopeCode':code,'sourceSlopeGroup':name,'sourceGroupOffset':offset,'sourceCentreTileXY':[8,8],'sourcePartialPixelZ':z,'sourceCentrePixelInFullTileCanvas':[128,128-z*4],'heightStepPixels':32,'cornerHeightUnits':heights,'cornerPixels':{k:list(v)for k,v in points.items()},'operation':'actual native jade/gold chevron or red/gold prohibition symbol crop/downsample/rotation -> canonical squareUV ->2:1ground projection ->post-foundation slope projection; no new painting or vector replacement','derivedFrom':[source],'projectionRecipe':recipe,'nativeModelGeneration':False,'nativeUpscale':False,'actualModel':None,'actualQuality':None,'artSource':'native-painted-component-derivative','userArtAcceptance':'pending','unityValidated':False,'status':'produced-needs-actual-visual-review','drawRule':'separate ground overlay after current road ground, before road catenary/roadside details; fixed tile-anchor variant already includes source centre PartialPixelZ, do not apply it twice','engineImportSuggestion':{'spriteMode':'Single','meshType':'FullRect','filterMode':'Bilinear','wrapMode':'Clamp','mipMaps':False,'atlasPaddingMin':4}}
    if recipe['functionalShaftSVG']:a['derivedFrom'].append({'file':recipe['functionalShaftSVG'],'sha256':wp.sha(R/recipe['functionalShaftSVG']),'sourceType':'functional-vector-geometry'});a['operation']+='; explicit saved functional direction shaft under native arrowhead, not new hand-painted detail'
    assets.append(a);wp.writej(Path(str(R/f)+'.derivation.json'),a);bindings.append({'id':f'SPR_ONEWAY_BASE+{slot}','sourceSpriteOffset':slot,'sourceSpriteId':a['sourceSpriteId'],'file':f,'sha256':a['sha256'],'axis':axis,'disallowedBits':drd,'allowedTrackdir':a['allowedTrackdir'],'postFoundationSlope':code,'groupOffset':offset,'localArtReviewed':False})
 # Every original legal terrain slope maps through GetRoadFoundation and ApplyFoundationToSlope.
 cases=[];foundation=load(R/'assets/world/infrastructure/foundations/manifest.json')['coverageMappings'][0]['caseBindings'];by={(x['slopeCode'],x['mode']):x for x in foundation}
 for code,_ in wp.SLOPES:
  for axis in ['X','Y']:
   mode,effective,dz=road_foundation(code,axis);group=6 if effective in [12,9]else 12 if effective in [3,6]else 0
   for drd in [1,2,3]:
    slot=group+(0 if axis=='X'else 3)+drd-1;b=next(x for x in bindings if x['sourceSpriteOffset']==slot);case={'sourceTerrainSlopeCode':code,'axis':axis,'drd':drd,'foundationMode':mode,'postFoundationSlopeCode':effective,'baseHeightIncrementTiles':dz,'baseHeightPixelOffset':-dz*32,'sourceSpriteOffset':slot,'overlay':b['file'],'overlaySHA256':b['sha256'],'targetRoadFile':f'assets/world/infrastructure/road-variants/road-rural-mask-{10 if axis=="X"else 5:02d}-slope-{SLOPES[effective]}.png','fullTilePlacement':'same256x192canvas/anchor as target road; shift both by baseHeightPixelOffset relative to original tile base; never add PartialPixelZ twice'}
    if mode!='None':
     f=by[(code,mode)];case['foundationSideLayer']=ref(f['sideLayer']);case['foundationWholeAlternative']=ref(f['whole']);case['foundationComposition']='draw sides + selected target road cap; whole is alternative and must not double-render'
    cases.append(case)
 manifest={'schema':'road-oneway-ground-overlays.v1','createdAt':wp.now(),'assets':assets,'animations':[],'sourceConstants':nums,'sourceRequirements':18,'terrainAxisDirectionCases':len(cases),'sourceCaseBindings':cases,'sourceFiles':[{'file':'reference/OpenTTD/src/'+p,'sha256':wp.sha(R/'reference/OpenTTD/src'/p)}for p in ['table/sprites.h','road_cmd.cpp','road_type.h','track_type.h','landscape.cpp','slope_type.h','slope_func.h']],'coverageMappings':[{'requirementId':'road-oneway-markings','files':[a['image']for a in assets],'sourceSpriteOffsets':list(range(18)),'axes':['X','Y'],'drd':[1,2,3],'effectiveSlopeCodes':[0,3,6,9,12],'inputTerrainSlopeCodes':[x[0]for x in wp.SLOPES],'sourceDrawOffsetXY':[8,8],'sourceDrawOrder':'DrawRoadGroundSprites -> oneway -> roadworks -> catenary/details','completeVariantCoverage':True,'noMarkingWhenDrdZero':True}],'userArtAcceptance':'pending','unityValidated':False,'status':'produced-needs-actual-visual-review'};wp.writej(R/OUT/'manifest.json',manifest);wp.writej(R/'docs/ROAD_ONEWAY_BINDINGS.json',{'schema':'road-oneway-bindings.v1','createdAt':wp.now(),'sourceConstants':nums,'bindings':bindings,'terrainCaseBindings':cases,'sourceRequirements':18,'formalPNGCount':18,'manifest':OUT+'/manifest.json','manifestSHA256':wp.sha(R/OUT/'manifest.json'),'complete':False,'failures':[],'userArtAcceptance':'pending','unityValidated':False})
 # Five real assembled pages: every source slot in rural context, plus every slot on snow/desert.
 pages=[]
 def contact(aa,name,context):
  out=Image.new('RGB',(960,math_rows:=((len(aa)+2)//3)*250+70),'#20483a');d=ImageDraw.Draw(out);d.text((18,12),name+' · 实际路面＋独立标记（原像素比例）',font=font,fill='#f3e8cc');deps=[]
  for k,a in enumerate(aa):
   x=k%3*320+32;y=k//3*250+45;rf=f'assets/world/infrastructure/road-variants/road-{context}-mask-{a["connectionMask"]:02d}-slope-{SLOPES[a["effectiveSlopeCode"]]}.png';base=Image.open(R/rf).convert('RGBA');base.alpha_composite(Image.open(R/a['image']).convert('RGBA'));out.paste(base,(x,y),base);label=f'{a["sourceSpriteOffset"]:02d} {a["axis"]} / drd {a["disallowedRoadDirectionBits"]} / '+str(a['allowedTrackdir']or'双向禁行');d.text((x,y+196),label,font=font,fill='#f3e8cc');deps.extend([ref(rf),ref(a['image'])])
  f='previews/road-oneway/'+name+'.jpg';out.save(R/f,quality=96);wp.writej(Path(str(R/f)+'.derivation.json'),{'file':f,'sha256':wp.sha(R/f),'operation':'actual current256x192road PNG plus independent samecanvas direction overlay, native1x pixels; text/contact layout only','derivedFrom':deps,'unityValidated':False});pages.append(f)
 for name,off,ss in GROUPS:contact([a for a in assets if a['sourceSlopeGroup']==name],'road-oneway-'+name,'rural')
 contact(assets,'road-oneway-snow','snow');contact(assets,'road-oneway-desert','desert')
 html='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>道路单行与禁行标记</title><style>body{background:#20483a;color:#f2e7cb;font:15px/1.5 system-ui;margin:24px}main{max-width:1100px;margin:auto}img{max-width:100%;height:auto}a{color:#e4bf77}</style><main><h1>道路单行／双向禁行地面标记</h1><p>18个源码Sprite槽；独立地面叠层，采用当前原生玉绿金边箭头及朱砂禁行图素。19种原始坡形×两轴×3限制状态共114个地基转换绑定。下面为实际PNG路面拼装，不含Unity业务运行。</p><p><a href="../../docs/ROAD_ONEWAY_BINDINGS.json">源状态绑定</a> · <a href="../../docs/ROAD_ONEWAY_DELIVERY.md">定位与语义</a></p>'
 for f in pages:html+='<h2>'+Path(f).stem+'</h2><img src="../../'+f+'" alt="'+Path(f).stem+'">'
 html+='</main>';(PRE/'index.html').write_text(html,encoding='utf8');print(json.dumps({'sourceConstants':nums,'formalPNGCount':len(assets),'terrainCases':len(cases),'pages':pages,'manifestSHA256':wp.sha(R/OUT/'manifest.json')}))
if __name__=='__main__':main()

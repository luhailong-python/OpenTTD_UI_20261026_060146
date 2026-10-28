"""Audit previously omitted source cursor/selection/annotation categories.
--build inventories actual source tables. Default checks explicit delivered bindings.
This never changes already accepted world PNGs or infers acceptance from PNG counts.
"""
from pathlib import Path
from PIL import Image
import ast,operator,re,json,collections,argparse
import world_pack as wp
R=wp.ROOT;SRC=R/'reference/OpenTTD';DOC=R/'docs/POINTER_OVERLAY_REQUIREMENTS.json'
LEGAL=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,23,27,29,30]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def build():
 p=SRC/'src/table/sprites.h';text=p.read_text(encoding='utf8');lines=text.splitlines();defs={m[0]:m[1].strip()for m in re.findall(r'(?:static\s+)?(?:constexpr|const)\s+(?:\w+)\s+(\w+)\s*=\s*([^;]+);',text)};values={};ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.FloorDiv:operator.floordiv,ast.Div:operator.floordiv,ast.LShift:operator.lshift,ast.BitOr:operator.or_}
 def value(name,seen=()):
  if name in values:return values[name]
  if name in seen or name not in defs:raise ValueError(name)
  e=re.sub(r'(?<=\d)[uUlL]+\b','',defs[name]);tree=ast.parse(e,mode='eval')
  def ev(n):
   if isinstance(n,ast.Expression):return ev(n.body)
   if isinstance(n,ast.Constant)and isinstance(n.value,int):return n.value
   if isinstance(n,ast.Name):return value(n.id,seen+(name,))
   if isinstance(n,ast.BinOp)and type(n.op)in ops:return ops[type(n.op)](ev(n.left),ev(n.right))
   if isinstance(n,ast.UnaryOp)and isinstance(n.op,ast.USub):return-ev(n.operand)
   raise ValueError(name)
  values[name]=ev(tree);return values[name]
 def val(n):
  try:return value(n)
  except (ValueError,SyntaxError,TypeError,KeyError):return None
 def source(sym,line=None):return{'file':'reference/OpenTTD/src/table/sprites.h','line':line or next((i for i,l in enumerate(lines,1)if re.search(r'\b'+sym+r'\b',l)),None),'symbol':sym,'expression':defs.get(sym),'numericValue':val(sym)}
 def badge(sym):
  name=sym.removeprefix('SPR_CURSOR_');specific={'MOUSE':None,'ZZZ':None,'BUOY':'assets/world/infrastructure/waterworks/buoy.png','QUERY':'assets/icons/search.png','HQ':'assets/icons/company.png','SHIP_DEPOT':'assets/icons/depot.png','SIGN':'assets/icons/news.png','TREE':'assets/icons/tree.png','BUY_LAND':'assets/world/infrastructure/objects/owned-land.png','LEVEL_LAND':'assets/icons/terrain.png','TOWN':'assets/icons/town.png','INDUSTRY':'assets/icons/industry.png','ROCKY_AREA':'assets/world/terrain/terrain-rocks-density-3-flat.png','DESERT':'assets/world/terrain/terrain-desert-flat.png','TRANSMITTER':'assets/world/infrastructure/objects/radio-mast.png','AIRPORT':'assets/icons/airport.png','DOCK':'assets/icons/dock.png','CANAL':'assets/world/infrastructure/waterworks/canal-banks.png','LOCK':'assets/world/infrastructure/waterworks/lock-high.png','RIVER':'assets/world/infrastructure/waterworks/river-rapids.png','AQUEDUCT':'assets/world/infrastructure/transport-runtime/aqueduct-X-piece-4.png','BRIDGE':'assets/icons/bridge.png','RAIL_STATION':'assets/icons/station.png','WAYPOINT':'assets/icons/orders.png','BUS_STATION':'assets/icons/bus-stop.png','TRUCK_STATION':'assets/icons/truck.png'}
  if name in specific:return specific[name]
  if 'CLONE'in name:
   return 'assets/icons/'+('train'if'TRAIN'in name else'ship'if'SHIP'in name else'air'if'AIRPLANE'in name else'bus')+'.png'
  if'TUNNEL'in name:return'assets/icons/tunnel.png'
  if'DEPOT'in name:return'assets/icons/depot.png'
  if'TRAM'in name:return'assets/icons/tram.png'
  if'ROAD'in name:return'assets/icons/road.png'
  if'MAGLEV'in name:return'assets/world/infrastructure/rail/rail-maglev-segment-x.png'
  if'MONO'in name:return'assets/world/infrastructure/rail/rail-monorail-segment-x.png'
  if'ELRAIL'in name:return'assets/world/infrastructure/rail/rail-electric-segment-x.png'
  return'assets/icons/rail.png'
 static=[];frames={}
 for i,l in enumerate(lines,1):
  m=re.search(r'static const CursorID\s+(SPR_CURSOR_\w+)\s*=',l)
  if not m:continue
  sym=m[1]
  if any(x in sym for x in ['DEMOLISH_','LOWERLAND_','RAISELAND_','PICKSTATION_','BUILDSIGNALS_']):frames[sym]=source(sym,i);continue
  f=badge(sym);static.append({'id':sym,'category':'static-cursor','source':source(sym,i),'badgeSource':{'file':f,'sha256':wp.sha(R/f),'actualFileExists':True}if f and(R/f).is_file()else None,'requiredNativeComponent':'cursor-wait'if sym.endswith('_ZZZ')else'cursor-arrow','requiredContract':['fixed transparent canvas','actual tip hotspot in pixel coordinates','pointer base plus functional badge is allowed','orientation/rail technology/convert/clone modifier explicit in recipe','empty/normal tool state uses same hotspot'],'proposedRecipe':{'baseComponentRole':'cursor-wait'if sym.endswith('_ZZZ')else'cursor-arrow','badgeFile':f,'badgeRegionSuggestedPx':[42,44,116,118],'masterCanvasSuggested':[128,128],'hotspot':'MUST measure actual pointer tip; no guessed approved hotspot','semanticModifiers':[x for x in ['NS','SWNE','EW','NWSE','NESW','CONVERT','CLONE','AUTO','MONO','MAGLEV','ELRAIL']if x in sym],'dynamicTooltip':'Source tool meaning/technology/direction, independent text; not baked into cursor art'},'status':'missing-pointer-base-or-explicit-production-binding'})
 animtext=(SRC/'src/table/animcursors.h').read_text(encoding='utf8');groups=[]
 names={'_demolish_animcursor':('ANIMCURSOR_DEMOLISH','assets/icons/build.png'),'_lower_land_animcursor':('ANIMCURSOR_LOWERLAND','assets/icons/terrain.png'),'_raise_land_animcursor':('ANIMCURSOR_RAISELAND','assets/icons/terrain.png'),'_order_goto_animcursor':('ANIMCURSOR_PICKSTATION','assets/icons/orders.png'),'_build_signals_animcursor':('ANIMCURSOR_BUILDSIGNALS','assets/icons/signal.png')}
 for m in re.finditer(r'static constexpr AnimCursor\s+(\w+)\[\]\s*=\s*\{(.*?)\};',animtext,re.S):
  pairs=re.findall(r'\{(SPR_CURSOR_\w+),\s*(\d+)\}',m[2]);sym,b=names[m[1]];groups.append({'id':sym,'category':'animated-cursor','source':source(sym),'sourceTable':'reference/OpenTTD/src/table/animcursors.h','sourceFrames':[{'symbol':n,'spriteId':val(n),'displayTicks':int(t)}for n,t in pairs],'badgeFile':b,'requiredContract':['all listed source frame IDs explicitly mapped','same canvas and exact same hotspot in every frame','source tick timing retained as data, engine tick conversion pending','actual badge Alpha/luminance/pose changes must be declared derivatives, not claimed new native art'],'status':'missing-explicit-cursor-animation-contract'})
 landscape=(SRC/'src/landscape.cpp').read_text(encoding='utf8');smap=re.search(r'_slope_to_sprite_offset\s*=\s*\{(.*?)\};',landscape,re.S);offset=list(map(int,re.findall(r'\b\d+\b',smap[1])));normal=[{'id':'selection-normal-slope-'+str(c),'category':'tile-selection','source':source('SPR_SELECT_TILE'),'sourceSlopeCode':c,'sourceSpriteId':val('SPR_SELECT_TILE')+offset[c],'sourceOffset':offset[c],'requiredContract':['4corner diamond follows actual slope heights','neutral/valid,blue coverage,red invalid,red error pulse,amber authority palette bindings','rectangle/diagonal/multiple-tile footprint repeats tile shape; no baked text'],'geometryCanBeCodeAuthored':True,'status':'missing-explicit-selection-art-or-vector-contract'}for c in LEGAL]
 half=[]
 for shape in ['FLAT','DOWN','UP']:
  for corner in range(4):half.append({'id':'selection-half-'+shape.lower()+'-'+str(corner),'category':'halftile-selection','source':source('SPR_HALFTILE_SELECTION_'+shape),'sourceSpriteId':val('SPR_HALFTILE_SELECTION_'+shape)+corner,'corner':corner,'shape':shape.lower(),'requiredContract':['source4corners×flat/down/up12modules','higher half and opposite lower half selected as independent FoundationPart;7px z offset and TILE_HEIGHT encoded as source semantics','same5palette roles as normal selection'],'geometryCanBeCodeAuthored':True,'status':'missing-explicit-halftile-art-or-vector-contract'})
 autorail=(SRC/'src/table/autorail.h').read_text(encoding='utf8');table=autorail.split('_autorail_slope_sprite_offsets = {{{',1)[1].split('}}};',1)[0];rows=[]
 for body in re.findall(r'\{([^{}]+)\}',table):rows.append([int(a or b) *(-1 if a else 1)for a,b in re.findall(r'RED\((\d+)\)|(-?\d+)',body)])
 rail=[];used=set()
 for slope in LEGAL:
  for direction,off in enumerate(rows[slope]):used.add(abs(off));rail.append({'id':'selection-autorail-'+str(slope)+'-'+str(direction),'category':'autorail-selection','sourceTable':'reference/OpenTTD/src/table/autorail.h','sourceSlopeCode':slope,'highlightDirectionIndex':direction,'highlightDirection':['X','Y','HU','HL','VL','VR'][direction],'spriteOffset':abs(off),'sourceSpriteId':val('SPR_AUTORAIL_BASE')+abs(off),'invalidBySourceTable':off<0,'requiredContract':['match source stroke orientation and corner height projection','red source-negative offset is invalid placement, not missing art','can reuse6path geometries across19slopes with declared projection and palette'],'geometryCanBeCodeAuthored':True,'status':'missing-explicit-autorail-overlay-contract'})
 extras=[{'id':'SPR_DOT','category':'corner-marker','source':source('SPR_DOT'),'reuseContract':'one painted jade point repeated at4terrain corners; anchor and z from current corner height','geometryCanBeCodeAuthored':True}, {'id':'SPR_WHITE_POINT','category':'point-marker','source':source('SPR_WHITE_POINT'),'reuseContract':'single-colour neutral point for minimal position indicators; literal geometry, not new native painting','geometryCanBeCodeAuthored':True}, {'id':'SPR_EMPTY','category':'empty-helper','source':source('SPR_EMPTY'),'reuseContract':'1x1true transparent helper or explicitly no draw; no picture required','noPictureRequired':True}]
 for sym in ['SPR_COMPANY_ICON','SPR_FLAG_VEH_STOPPED','SPR_FLAG_VEH_RUNNING','SPR_PIN_UP','SPR_PIN_DOWN']:
  assets=['assets/world/infrastructure/object-states/company-flag-'+format(i,'02d')+'.png'for i in range(16)]if sym=='SPR_COMPANY_ICON'else[];extras.append({'id':sym,'category':'company-status-marker'if'PIN'not in sym else'window-pin','source':source(sym),'existingReusableFiles':assets,'reuseContract':'company16colour flags exist; tiny company-colour swatch geometry may accompany company icon'if sym=='SPR_COMPANY_ICON'else'stop=朱砂 square / running=jade triangle; pin up/down explicit2states; simple vector geometry allowed','geometryCanBeCodeAuthored':True})
 extras+=[{'id':'SMALLMAP_DATA_MARKERS','category':'data-drawn-map-markers','sourceFiles':['reference/OpenTTD/src/smallmap_gui.cpp:683-696','reference/OpenTTD/src/smallmap_gui.cpp:945-1010','reference/OpenTTD/src/smallmap_gui.cpp:1624-1696'],'reuseContract':'vehicles are1–2painted logical pixels, legend colour rectangles, viewport cornerL, dynamic town/industry text. Use explicit geometry/palette/text contract; do not invent native sprite IDs. Dynamic Chinese uses existing NotoSansSC font.','geometryCanBeCodeAuthored':True}, {'id':'WORLD_SIGN_LABEL','category':'dynamic-sign-label','sourceFiles':['reference/OpenTTD/src/signs_gui.cpp:205-262','reference/OpenTTD/src/viewport.cpp'],'reuseContract':'dynamic world sign/company names use existing paper panel and NotoSansSC text; label pointer/map pin may share native kit; text stays separate','existingReusableFiles':['assets/common/reference-paper.png'],'geometryCanBeCodeAuthored':True}]
 for a in extras:a.setdefault('status','missing-explicit-marker-contract')
 items=static+groups+normal+half+rail+extras
 result={'schema':'pointer-overlay-source-requirements.v1','createdAt':wp.now(),'referenceCommit':'cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8','scope':'Cross-category source omissions additional to549world tile/entity requirements and UI/vehicle ledgers; no existing world PNG changed.','sourceFiles':[{'file':wp.rel(SRC/'src'/f),'sha256':wp.sha(SRC/'src'/f)}for f in ['table/sprites.h','table/animcursors.h','table/autorail.h','viewport.cpp','slope_func.h','landscape.cpp','smallmap_gui.cpp','company_cmd.cpp','signs_gui.cpp']],'counts':{'staticCursorSymbols':len(static),'animatedCursorGroups':len(groups),'animatedCursorUniqueFrameSymbols':len(frames),'normalSelectionSlopes':len(normal),'halftileSelectionModules':len(half),'autorailSourceReservedSlots':55,'autorailUsedAbsoluteOffsets':len(used),'autorailLegalSlopeDirectionCases':len(rail),'annotationHelperContracts':len(extras),'requirementRows':len(items)},'autorailSourceSlots':[{'offset':i,'spriteId':val('SPR_AUTORAIL_BASE')+i,'usedByCurrentLegalSlopeTable':i in used,'requiresPicture':i in used,'unusedReason':None if i in used else'source block reserved/unused by inspected legal slope table'}for i in range(55)],'knownCurrentGaps':['No adopted pointer arrow or wait cursor in existing common/icons/world assets.','No source-symbol bound hotspot/animation cursor recipes.','No normal/halftile/autorail selection overlay palette/geometry manifest.','Existing16company flags and36UI function icons are reusable source assets, not proof of missing cursor/overlay contracts having been delivered.'],'nativeKitNeed':['clean jade/ivory/gold main arrow with measurable actual tip hotspot','wait/hourglass or gourd badge','four small direction arrow pieces','prohibition/invalid marker','jade selection corner/point decorative pieces optional; exact overlay strokes can be code-authoredSVG','window/map pin2states optional; simple vector geometry allowed'],'deliveryBindingFile':'docs/POINTER_OVERLAY_BINDINGS.json','bindingSchema':{'bindings':'array; one explicit id per requirements.items.id','imageBinding':'{id,file,sha256,canvasPx,hotspotPx,sourceRequirementIds,operation,localArtReviewed}','compositionBinding':'{id,layers:[{file,sha256,offsetPx,sizePx}],canvasPx,hotspotPx,sourceFrameIds,sourceTicks,states,operation,localArtReviewed}','geometryBinding':'{id,geometryFile,sha256,states,sourceSlopeCode,sourceSpriteId,operation,localArtReviewed}; exact SVG/path data permitted, no native-paint claim','unusedHelper':'{id,noDraw:true,reason,localArtReviewed:true} only for source explicitly requiring no picture'},'items':items,'userArtAcceptance':'pending','unityValidated':False}
 wp.writej(DOC,result);return result
def check():
 q=load(DOC);bp=R/q['deliveryBindingFile'];bound={a['id']:a for a in load(bp).get('bindings',[])}if bp.is_file()else{};issues=[];results=[]
 for req in q['items']:
  b=bound.get(req['id']);why=[]
  if not b:why.append('No explicit production binding.')
  else:
   if b.get('noDraw'):
    if not req.get('noPictureRequired'):why.append('No-draw only valid for explicitly empty source helper.')
   else:
    refs=[]
    if b.get('file'):refs.append(b)
    refs+=b.get('layers',[])
    if b.get('geometryFile'):refs.append({'file':b['geometryFile'],'sha256':b.get('sha256')})
    if not refs:why.append('No actual artwork or saved geometry dependency.')
    for a in refs:
     p=R/a.get('file','');
     if not p.is_file():why.append('Missing dependency '+a.get('file',''));continue
     if a.get('sha256')!=wp.sha(p):why.append('Missing/stale dependency SHA '+a['file'])
     if p.suffix.lower()=='.png':
      im=Image.open(p)
      if im.mode!='RGBA'or im.getchannel('A').getbbox()is None:why.append('Not real nonempty RGBA '+a['file'])
    if req['category']in ['static-cursor','animated-cursor']:
     if not b.get('canvasPx')or not b.get('hotspotPx'):why.append('Cursor fixedcanvas/hotspot missing.')
     elif any(p<0 or p>=s for p,s in zip(b['hotspotPx'],b['canvasPx'])):why.append('Hotspot out of canvas.')
     if req['category']=='static-cursor'and b.get('file')and(R/b['file']).is_file():
      im=Image.open(R/b['file']);hot=b.get('hotspotPx',[0,0]);d=load(Path(str(R/b['file'])+'.derivation.json'))
      if list(im.size)!=b.get('canvasPx')or im.getpixel(tuple(hot))[3]<128:why.append('Actual cursor canvas/tip Alpha does not verify measured hotspot.')
      if d.get('sourceSymbol')!=req['id']or d.get('sourceSpriteId')!=req['source']['numericValue']:why.append('Cursor source symbol/numeric ID missing from actual derivation.')
    if req['category']=='animated-cursor':
     if b.get('sourceFrameIds')!=[x['spriteId']for x in req['sourceFrames']]or b.get('sourceTicks')!=[x['displayTicks']for x in req['sourceFrames']]:why.append('Animated source frame IDs/ticks incomplete.')
     if len(b.get('states',[]))!=len(req['sourceFrames']):why.append('Ordered distinct visual phase recipes missing.')
     for state in b.get('states',[]):
      p=R/state.get('file','')
      if not p.is_file():why.append('Missing actual animation state PNG.');continue
      im=Image.open(p)
      if list(im.size)!=b.get('canvasPx')or state.get('hotspotPx')!=b.get('hotspotPx'):why.append('Animated frame canvas/hotspot drift.')
     if len({s.get('sha256')for s in b.get('states',[])})<len(req['sourceFrames']):why.append('Cursor phases must actually differ, not duplicate a static image.')
    if req['category']in ['tile-selection','halftile-selection']and not {'neutral','coverage-blue','invalid-red','error-pulse-red','authority-amber'}<=set(b.get('states',[])):why.append('5selection palette roles incomplete.')
    if req['category']=='autorail-selection'and(b.get('sourceSlopeCode')!=req['sourceSlopeCode']or b.get('sourceSpriteId')!=req['sourceSpriteId']):why.append('Source autorail slope/offset mapping not retained.')
    if req['category']=='autorail-selection'and'invalid-red'not in b.get('states',[]):why.append('Forced source red/error override PNG missing.')
   if not b.get('operation'):why.append('Artwork/geometry/derivative operation not declared.')
   if not b.get('localArtReviewed'):why.append('Actual local visual review pending.')
  results.append({'id':req['id'],'category':req['category'],'passed':not why,'issues':why})
 report={'createdAt':wp.now(),'sourceInventory':wp.rel(DOC),'sourceInventorySHA256':wp.sha(DOC),'bindings':wp.rel(bp),'bindingSHA256':wp.sha(bp)if bp.is_file()else None,'counts':q['counts'],'passed':sum(x['passed']for x in results),'remaining':sum(not x['passed']for x in results),'remainingIds':[x['id']for x in results if not x['passed']],'results':results,'rule':'Source-symbol/geometry state/timing/hotspot/actual SHA and local visual review required; file count does not imply coverage. Source unused slots need no invented drawings.','unityValidated':False,'userArtAcceptance':'pending'}
 wp.writej(R/'records/pointer-overlay-validation.json',report);print(json.dumps({k:v for k,v in report.items()if k not in ['results','remainingIds']},ensure_ascii=False));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
 if a.build:build()
 check()


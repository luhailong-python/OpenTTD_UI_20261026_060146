from pathlib import Path
import re,json,hashlib,datetime,collections
R=Path(r"E:\work\image\OpenTTD_UI_20261026_060146");S=R/"reference/OpenTTD"
def txt(p):return(S/p).read_text(encoding="utf-8-sig")
def ev(p,n):
 s=txt(p);return{"file":p,"line":s.count("\n",0,s.index(n))+1,"symbol":n}
def block(p,n):
 s=txt(p);a=s.index(n);b=s.index("{",a);d=1;i=b+1
 while d:
  if s[i]=="{":d+=1
  elif s[i]=="}":d-=1
  i+=1
 return s[b+1:i-1],s.count("\n",0,a)+1
def args(s):
 out=[];a=0;d=0
 for i,c in enumerate(s):
  if c in "({[":d+=1
  elif c in ")}]":d-=1
  elif c==","and d==0:out.append(s[a:i].strip());a=i+1
 out.append(s[a:].strip());return out
def calls(p,macro,after):
 s=txt(p);b=s.index(after);out=[]
 for m in re.finditer(r"\b"+macro+r"\(",s[b:]):
  a=b+m.end();d=1;i=a
  while d:
   if s[i]=="(":d+=1
   elif s[i]==")":d-=1
   i+=1
  out.append({"args":args(s[a:i-1]),"raw":s[a:i-1],"line":s.count("\n",0,a)+1})
 return out
lang={m[1]:re.sub(r"\{[^}]+\}","",m[2]).strip()for m in re.finditer(r"^(STR_[A-Z0-9_]+)\s*:(.*)$",txt("src/lang/simplified_chinese.txt"),re.M)}
items=[]
def add(id,category,name,source,variants,animation=False,kind="reusable-module-requirement",**kw):
 q={"id":id,"category":category,"name":name,"source":source,"neededVariants":variants,"animation":{"required":animation},"entryKind":kind,"artStatus":"missing-not-yet-produced","artFiles":[],"acceptanceStatus":"not-checked","nativeGenerationClaim":False};q.update(kw);items.append(q);return q
# Ground and infrastructure.
slopes=list(range(15))+[23,27,29,30]
for n in["grass","bare","rough","rocks","field","snow","desert"]:
 add("terrain-"+n,"terrain",n,[ev("src/clear_map.h","enum class ClearGround"),ev("src/slope_type.h","NUM_SLOPES")],{"slopeCodes":slopes,"climates":["temperate","arctic","tropic","toyland"],"densityStages":list(range(4))if n in["grass","rocks","snow","desert"]else None,"sourceRandomVariants":8 if n=="rough"else 16 if n=="field"else None,"derivedProjectionMustBeDeclared":True})
for id,cat,p,n,v,anim in[
("terrain-foundation","terrain","src/table/sprites.h","NORMAL_FOUNDATION_SPRITE_COUNT",{"extraNormalSpriteBlock":74,"extraNormalHalfSpriteBlock":90,"edges":4},False),
("terrain-fence","terrain","src/table/clear_land.h","_clear_land_fence_sprites",{"styles":7,"edges":4},False),
("water-sea","water","src/water_cmd.cpp","DrawShipDepotSprite",{"surface":"sea","frames":"loop","shoreSeparate":True},True),
("water-river","water","src/water_cmd.cpp","MarkCanalsAndRiversAroundDirty",{"connectivityMasks":list(range(16)),"flowSlopes":4},True),
("water-canal","water","src/table/sprites.h","CANALS_SPRITE_COUNT",{"connectivityMasks":list(range(16)),"canalSpriteBlock":65},True),
("water-shore","water","src/table/sprites.h","SHORE_SPRITE_COUNT",{"sourceShoreSprites":18,"edges":["grass","sand","snow"]},True),
("water-lock","water","src/table/water_land.h","_lock_display_data",{"directions":4,"sections":["lower","middle","upper"],"layers":["front","rear"],"waterLevels":["low","moving","high"]},True),
("water-aqueduct","water","src/table/sprites.h","AQUEDUCT_SPRITE_COUNT",{"sourceSpriteParts":8,"ramps":4,"axes":2},False),
("rail-catenary","rail","src/table/sprites.h","ELRAIL_SPRITE_COUNT",{"sourceSpriteBlock":48,"layers":["back-pole","wire","front-pole"]},False),
("road-crossing","road","src/table/road_land.h","_crossing_layout",{"axes":2,"barrierStates":["open","closing","closed","opening"]},True),
("road-works","road","src/effectvehicle_func.h","EV_BULLDOZER",{"signage":True},True)]:
 try:src=[ev(p,n)]
 except ValueError:src=[ev(p,"/** @file")]
 add(id,cat,id,src,v,anim)
for n in["rail","electric","monorail","maglev"]:
 add("rail-"+n,"rail",n,[ev("src/table/railtypes.h","_original_railtypes"),ev("src/track_type.h","enum class Track")],{"segments":["X","Y","Upper","Lower","Left","Right"],"compositionMasks":list(range(1,64)),"slopeDirections":4,"climateOverlays":["normal","snow","desert"],"note":"63为非空bit组合，可用6原生轨段透明叠加，不算63新原画"})
for n in["road","tram"]:
 add("road-"+n,"road",n,[ev("src/table/roadtypes.h","_original_roadtypes"),ev("src/table/road_land.h","_road_tile_sprites_1")],{"connectivityMasks":list(range(1,16)),"slopeDirections":4,"surfaceContexts":["rural","town-pavement","snow","desert"],"wireSeparate":n=="tram"})
for look in["electric","semaphore"]:
 for typ in["block","entry","exit","combo","path","path-one-way"]:
  add(f"signal-{look}-{typ}","signal",look+"/"+typ,[ev("src/signal_type.h","enum class SignalVariant"),ev("src/signal_type.h","enum class SignalType"),ev("src/signal_type.h","enum class SignalState")],{"directions":8,"states":["red","green"],"placementSides":2},True,kind="source-logic-and-appearance")
# Parse the bridge top-level brace entries.
p="src/table/bridge_land.h";b,ln=block(p,"const BridgeSpec _orig_bridge");rows=[];d=0;a=0
for i,c in enumerate(b):
 if c=="{":
  if d==0:a=i
  d+=1
 elif c=="}":
  d-=1
  if d==0:rows.append(b[a:i+1])
rows=[row for row in rows if re.search(r'STR_BRIDGE_(?:NAME_|TUBULAR_SILICON)',row)]
shapes=["wood","concrete","archgirder","suspension","suspension","suspension","cantilever","cantilever","cantilever","girder","tubular","tubular","tubular"]
for i,row in enumerate(rows):
 k=re.search(r"STR_BRIDGE_(?:NAME_\w+|TUBULAR_SILICON)",row).group()
 add(f"bridge-{i:02d}-{shapes[i]}","bridge",lang.get(k,k),[{"file":p,"line":txt(p).count("\n",0,txt(p).index(row))+1,"symbol":k}],{"sourceBridgeId":i,"geometryFamily":shapes[i],"axes":["X","Y"],"pieces":["north","south","inner-north","inner-south","middle-odd","middle-even","head"],"pillarSeparate":True,"transportDecks":["rail","road","water-when-valid"],"paletteOrMaterialVariant":i in[4,5,6,7,8,10,11,12]},kind="source-bridge-spec")
for n in["rail","electric","monorail","maglev","road","tram"]:
 add("tunnel-"+n,"tunnel",n,[ev("src/table/sprites.h","SPR_TUNNEL_ENTRY_REAR_RAIL")],{"directions":["NE","SE","SW","NW"],"layers":["rear","floor","front","occluder"],"climates":["normal","snow","desert"]})
for n,needle,count in[("rail","_station_display_datas_rail",8),("bus","_station_display_datas_bus",6),("truck","_station_display_datas_truck",6),("rail-waypoint","_station_display_datas_waypoint",8),("road-waypoint","_station_display_datas_road_waypoint",2),("dock","_station_display_datas_dock",6),("buoy","_station_display_datas_buoy",1)]:
 add("station-"+n,"station",n,[ev("src/table/station_land.h",needle)],{"sourceLayouts":count,"frontRearLayers":True})
for n,p,needle,dirs in[("rail","src/table/track_land.h","_depot_gfx_table",4),("road","src/table/road_land.h","_road_depot",4),("ship","src/table/water_land.h","_shipdepot_display_data",2)]:
 add("depot-"+n,"station",n,[ev(p,needle)],{"directions":dirs,"frontRearLayers":True})
# Airports10 and airport tiles74.
p="src/table/airport_defaults.h";aa=calls(p,"AS","extern const AirportSpec _origin_airport_specs")+calls(p,"AS_ND","extern const AirportSpec _origin_airport_specs")
for a in sorted(aa,key=lambda a:a["line"]):
 ar=a["args"];n=ar[0]
 add("airport-"+n,"airport",lang.get(ar[-2],n),[{"file":p,"line":a["line"],"symbol":n}],{"footprintTiles":[int(ar[1]),int(ar[2])],"minYear":ar[3],"animatedDetails":["radar","flag"],"layouts":"source tile table"},True,kind="source-airport-spec")
add("airport-oilrig","airport","油井平台机场",[ev(p,"AS_GENERIC(&_airportfta_oilrig")],{"footprintTiles":[1,1],"buildable":False,"sharedIndustry":"industry-05-oil-rig"},kind="source-airport-spec")
p="src/table/airporttile_ids.h";b,_=block(p,"enum AirportTiles")
for i,k in enumerate(re.findall(r"\bAPT_\w+",b)):
 add(f"airport-tile-{i:02d}-{k[4:].lower().replace('_','-')}","airport-tile",k,[ev(p,k)],{"sourceTileId":i,"layers":["ground","building","occlusion"],"reuseAllowed":True},kind="source-tile-id")
# house source specs110; display combinations4random x4construction.
p="src/table/town_land.h";hh=calls(p,"MS","extern const HouseSpec _original_house_specs")
for i,a in enumerate(hh):
 ar=a["args"];k=ar[4];flags=re.findall(r"BuildingFlag::(\w+)",ar[10])
 add(f"house-{i:03d}","town",lang.get(k,k),[{"file":p,"line":a["line"],"symbol":k}],{"sourceHouseTileId":i,"constructionStages":[0,1,2,3],"locationRandomVariants":4,"climateMasks":re.findall(r"HouseZone::Climate(\w+)",ar[11]),"buildingFlags":flags,"minYear":ar[0],"maxYear":ar[1],"population":ar[2],"note":"含多格房屋分片；人口0也可为公园等，不能直接按人口判独立建筑。"},"IsAnimated"in flags,kind="source-house-tile-spec")
# industry layout source preserves all coordinates/gfx expressions.
p="src/table/build_industry.h";ss=txt(p);layout_catalog={}
for ma in re.finditer(r"static const IndustryTileLayout (_tile_table_\w+_\d+)\s*\{",ss):
 n=ma[1];raw,ln=block(p,ma[0].rstrip("{"));tiles=[]
 for x in re.finditer(r"\{\s*\{\s*(-?\d+)\s*,\s*(-?\d+)\s*\}\s*,\s*([^}\n]+)\}",raw):
  tiles.append({"x":int(x[1]),"y":int(x[2]),"gfxExpression":x[3].strip().rstrip(",")})
 if tiles:
  active=[t for t in tiles if"GFX_WATERTILE_SPECIALCHECK"not in t["gfxExpression"]]
  bounds=[min(t["x"]for t in active),min(t["y"]for t in active),max(t["x"]for t in active)+1,max(t["y"]for t in active)+1]if active else None
  layout_catalog[n]={"sourceLine":ln,"boundsTiles":bounds,"tiles":tiles}
en,_=block(p,"enum IndustryTypes");enumvals=[(m[1],int(m[2]))for m in re.finditer(r"(IT_\w+)\s*=\s*(\d+)",en)]
ii=calls(p,"MI","extern const IndustrySpec _origin_industry_specs")
for i,a in enumerate(ii):
 ar=a["args"];ek,num=enumvals[i];slug=ek[3:].lower().replace("_","-");k=next((v for v in ar if v.startswith("STR_INDUSTRY_NAME_")),ek);tbl=ar[0]
 raw,ln=block(p,"static const std::vector<IndustryTileLayout> "+tbl+" ")
 ns=re.findall(r"_tile_table_\w+_\d+",raw)
 add(f"industry-{i:02d}-{slug}","industry",lang.get(k,k),[{"file":p,"line":a["line"],"symbol":ek},{"file":p,"line":ln,"symbol":tbl}],{"sourceIndustryTypeId":i,"sourceEnum":ek,"climates":sorted(set(re.findall(r"LandscapeType::(\w+)",a["raw"]))),"layouts":[{"id":n,**layout_catalog[n]}for n in ns if n in layout_catalog],"constructionStages":[0,1,2,3],"moduleMappingRequired":True},True,kind="source-industry-spec",proposedArtFile="assets/world/industries/"+slug+".png")
for i in range(175):
 add(f"industry-tile-{i:03d}","industry-tile",f"IndustryGfx {i}",[ev("src/industry_type.h","NEW_INDUSTRYTILEOFFSET"),ev("src/table/industry_land.h","_industry_draw_tile_data")],{"sourceGfxId":i,"constructionStages":[0,1,2,3],"artMayBeMappedModule":True},kind="source-tile-id")
# Vegetation41 x7 growth/death states.
cls=["temperate"]*12+["arctic"]*8+["tropic-rainforest"]*7+["tropic-desert"]+["tropic-normal"]*4+["toyland"]*9
for i,cl in enumerate(cls):
 add(f"tree-{i:02d}","vegetation",cl+" tree "+str(i),[ev("src/table/tree_land.h","_tree_base_by_landscape"),ev("src/tree_map.h","enum class TreeGrowthStage")],{"sourceTreeType":i,"climate":cl,"stages":["growing-1","growing-2","growing-3","grown","dying-1","dying-2","dead"],"layoutPlacementsPerTile":4},True,kind="source-tree-type")
p="src/table/object_land.h";oo=calls(p,"M","extern const ObjectSpec _original_objects")
for i,a in enumerate(oo):
 k=a["args"][0];slug=["transmitter","lighthouse","statue","owned-land","headquarters"][i]
 add("object-"+slug,"object",lang.get(k,k),[{"file":p,"line":a["line"],"symbol":k}],{"sourceObjectId":i,"headquartersLevels":5 if i==4 else None,"headquartersTilesPerLevel":4 if i==4 else None,"companyColours":i in[2,3,4],"groundSeparate":True},kind="source-object")
p="src/effectvehicle_func.h";b,_=block(p,"enum EffectVehicleType");effects=re.findall(r"\b(EV_\w+)\s*=",b);frames=[8,5,6,6,5,16,4,12,None,None,5,5]
for i,k in enumerate(effects):
 add("effect-"+k[3:].lower().replace("_","-"),"effect",k,[ev(p,k)],{"sourceEffectId":i,"sourceFrameCount":frames[i],"fixedCanvas":True,"sharedFramesAllowed":i in[10,11]},True,kind="source-effect")
p="src/disaster_vehicle.h";b,_=block(p,"enum DisasterSubType");disasters=re.findall(r"\b(ST_\w+)\s*[,=]",b)
for i,k in enumerate(disasters):
 add("disaster-"+k[3:].lower().replace("_","-"),"disaster",k,[ev(p,k),ev("src/disaster_vehicle.cpp","_disaster_images")],{"sourceDisasterSubType":i,"directions":8,"shadowMayDerive":"SHADOW"in k,"rotorFramesRequired":"ROTORS"in k,"sourceCanShareOneSpriteAcrossDirections":True},True,kind="source-disaster-subtype")
for id,cat,n,p,k,v in[
("animation-airport-radar","airport","机场雷达","src/table/sprites.h","SPR_AIRPORT_RADAR_1",{"sourceFrames":12}),
("animation-airport-flag","airport","机场风旗","src/table/station_land.h","_station_display_flag_1_fence_ne",{"sourceFrames":4}),
("animation-house-lift","town","办公室电梯","src/table/sprites.h","SPR_LIFT",{"separateLiftLayer":True}),
("animation-industry-machinery","industry","产业机械","src/table/industry_land.h","_draw_industry_spec1",{"types":["mine-head","oil-well-pump","power-sparks","toy-factory","plastic-fountain","bubble-generator","toffee-quarry","sugar-mine-sieve"]}),
("animation-fountain","town","喷泉","src/table/sprites.h","SPR_FOUNTAIN_0A",{"sourceFrames":"town drawing path"})]:
 add(id,cat,n,[ev(p,k)],v,True)
from scope_corrections import apply as apply_scope_corrections
apply_scope_corrections(items)
counts={"inventoryRows":len(items),"categoryRows":dict(collections.Counter(x["category"]for x in items)),"houseTileSpecs":len(hh),"houseDrawCombinations":len(hh)*16,"industryTypes":len(ii),"industryGfx":175,"industryStageCombinations":700,"industryLayouts":len(layout_catalog),"airportTypes":10,"airportTiles":74,"bridgeSpecs":len(rows),"treeTypes":41,"treeStates":7,"effectTypes":len(effects),"disasterSubtypes":len(disasters),"legalSlopeShapes":19}
report={"schemaVersion":1,"project":"云途万里（暂名）","referenceCommit":"cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8","generatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"artRepository":"F:/work/image (read-only)","counts":counts,"countingRules":["需求账本行数不是已经完成原画数量。","109张UI PNG不自动满足世界tile/车辆朝向/动画。","house110包含多tile分片；1760是4位置随机外观×4施工态。","NewGRF容量4096房/240产业/128机场是扩展上限，不是原生实体数量。","车辆车型/方向在车辆账本中另列，最终总表必须合并。"],"proposedSpec":{"view":"isometric-2:1","logicalTile":[128,64],"formalGround":[256,128],"slopeCanvas":[256,192],"formalElevationPixels":32,"buildingCanvas":"根据footprint和实际原生像素确定；透明padding不提高原生细节","vehicleCanvas":[256,256],"fxCanvas":[256,256],"pivot":"fixed ground anchor","maxAtlas":2048,"unityStatus":"not validated"},"items":items,"industryLayoutCatalog":layout_catalog}
(R/"docs/WORLD_ASSET_COVERAGE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
audit=[{"file":p,"sha256":hashlib.sha256((S/p).read_bytes()).hexdigest(),"lines":len(txt(p).splitlines())}for p in sorted({e["file"]for x in items for e in x["source"]})]
(R/"records/world-source-audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
md=["# 世界美术完整覆盖研究","","本轮补齐UI以外基础世界美术。源码固定提交cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8；本文件是需求与覆盖账本，不是成品验收。F盘只读，未Git/Unity操作。","","## 实际规模","","| 类别 | 实际数量与口径 |","|---|---|","| 房屋 | 110个tile specs，包含多格楼附属tile；4位置随机外观×4施工阶段，共1760绘制组合 |","| 产业 | 37类、175个IndustryGfx；每gfx4阶段，700状态组合；实际布局"+str(len(layout_catalog))+"套 |","| 机场 | 10类=9可建+油井平台；74种机场地块 |","| 桥 | 13条BridgeSpec，几何可归7族；各桥7段类别+X/Y轴+独立桥墩 |","| 树 | 41种=温带12/亚寒带8/热带12/玩具9；各7生长/枯死阶段 |","| 坡度 | 19有效坡形：0–14及23/27/29/30；整格抬高不是独立坡形 |","| 路网 | 4铁路类型×6基础轨段，可组合63非空mask；公路/有轨各15非空连通mask |","| 信号 | 6逻辑×2外观，另有红绿及方向；额外源sprite block240，不能用1灯图全代 |","| 对象 | 5原型：发射塔、灯塔、雕像、购地、总部；总部5等级各4tile |","| FX | 12个EffectVehicle类型，可明确共享部分烟雾源帧 |","| 灾难 | 15子类型含机体、阴影、旋翼，不是15种独立载具 |","","## 来源与索引","","逐项来源文件/行号、产业布局坐标和gfx表达式在WORLD_ASSET_COVERAGE.json；源文件SHA在records/world-source-audit.json。核心来源是house.h/table/town_land.h/town_cmd.cpp:273、industry_type.h/table/build_industry.h/table/industry_land.h、airport.h/table/airport_defaults.h/table/airporttile_ids.h、table/bridge_land.h、tree_map.h、slope_type.h、signal_type.h、effectvehicle_func.h与disaster_vehicle.h。","","## 制作规格与派生规则","","建议正式地面256×128菱形（逻辑128×64），坡画布256×192，一级高差32正式像素。地面、路轨、建筑、前遮挡、线网与FX分层；Pivot固定接地锚点。建筑依据真实footprint与原生像素设置画布，透明padding和放大不增加细节。实际Unity导入/遮挡/碰撞仍待下一阶段。","","每个源实体必须映射真实资源或明确的模块组合。气候保留各自产业、树、年代和商品含义，道家风格改变画法，不抹掉玩具大陆的糖/可乐/玩具等识别。","","可按已声明规则进行裁切、透明padding、等比缩小、地面透视/坡度投影、换色、真正对称镜像和分层组合；统一标派生，不计新模型原画。相反视角/俯仰不能只靠镜像捏造。原画数、导出数、组合数、动画帧数分别统计。","","产业按37完整终态原画+实际layout/gfx映射生产。共享施工层可表达0–2阶段，但需验证锚点、遮挡和视觉，不可把37终态自动报为700原生图。总部5等级、树7态、房屋4建设态、信号开关、船闸水位、雷达/风旗、产业机械/FX与灾难旋翼均须有真实状态或明确分层动画。","","## 验收与边界","","要求实体覆盖、几何/地面接缝、Alpha/尺寸、路网连接、遮挡、帧锚点/循环分别检查。输入哈希不变的通过检查可复用；新图或共享模板改变需重验受影响条目。单张场景插画或UI图标不能替代可组合世界模块。","","第三方NewGRF为开放内容，不可宣称穷尽所有外部美术。原生上限/保留ID不是必须凭空画的实体。车辆本体、车型和朝向由车辆生产账本补入总表。新增世界条目当前仍为missing-not-yet-produced；成品必须回填路径/SHA/来源和验收，不能把需求表当完工。"]
(R/"docs/WORLD_ASSET_RESEARCH.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print(json.dumps(counts,ensure_ascii=False))


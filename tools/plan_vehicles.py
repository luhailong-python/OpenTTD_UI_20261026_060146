from pathlib import Path
import json,re,collections,datetime
R=Path(r"E:\work\image\OpenTTD_UI_20261026_060146");D=R/"docs"
j=json.loads((D/"VEHICLE_SOURCE_DATA.json").read_text(encoding="utf-8"))
families=[
("loco-steam","rail","圆润蒸汽机车，短烟囱，玉绿锅炉，黄铜轮组，明确车头圆灯与后驾驶室"),
("loco-diesel","rail","经典柴油机车，方圆过渡短鼻，青绿车体，象牙侧带，驾驶窗与散热栅"),
("loco-electric","rail","双驾驶室电力机车，车顶受电弓，象牙车体玉绿腰带，暖金细线"),
("loco-monorail","rail","流线型单轨动车头，圆弧宽风挡，窄底导向架，玉绿象牙"),
("loco-maglev","rail","未来磁悬浮动车头，修长圆润低鼻，封闭裙板，无可见传统车轮"),
("loco-toy","rail","玩具大陆原创木漆小机车，保留蒸汽机车轮廓，玉绿象牙、少量桃粉，非塑料玩具"),
("wagon-passenger","rail","两端耦合器客运车厢，多扇窗，玉绿象牙，空车不带机车头"),
("wagon-box","rail","封闭厢式货车/邮车，侧滑门、金铜锁扣，无驾驶室，玉绿车厢"),
("wagon-hopper","rail","空敞口料斗货车，厚实短车架、清楚可见的空舱，适合独立货载叠加"),
("wagon-tank","rail","圆柱液体罐车，顶部小阀盖、外侧护栏，两端耦合器"),
("wagon-vent","rail","通风畜牧车厢，木质栅栏和通风孔，空内舱，稳固短车架"),
("wagon-flat","rail","空平板货车，低矮四边立柱与绑带扣，完整空装载面，无机车驾驶室"),
("road-bus","road","中型圆润客运巴士，短鼻与多扇窗，玉绿象牙、黄铜细边"),
("road-open","road","空敞口货运卡车，单独前驾驶室与后方空货斗，稳固轮胎，青绿车架"),
("road-box","road","厢式货运卡车，驾驶室与后厢清楚分开，侧门与后双门，象牙玉绿"),
("road-tank","road","液体罐式货运卡车，前驾驶室和短圆柱罐体，玉绿象牙细金边"),
("road-flat","road","平板货运卡车，前驾驶室和后方空装载板，低侧柱绑带扣"),
("ship-cargo","ship","单层木质货船，明确尖船首与尾驾驶舱，空货舱，玉绿帆顶不遮识别"),
("ship-tanker","ship","短宽油轮，金属圆润船壳和多个罐盖/管线，玉绿象牙，无巨帆"),
("ship-ferry","ship","双层客运渡轮，观景窗与小烟囱，明确前船首后甲板，玉绿象牙"),
("ship-hovercraft","ship","客运气垫船，黑青柔性气垫裙、两座后推风扇，玉绿象牙客舱"),
("air-small-prop","aircraft","小型固定翼螺旋桨客机，单机头螺旋桨，高翼，尾翼和机头清楚"),
("air-large-prop","aircraft","中型双引擎螺旋桨客机，双翼下短引擎，象牙机身玉绿尾翼"),
("air-jet-narrow","aircraft","窄体双发喷气客机，圆润机头，后掠翼与尾翼，机头尾部明确"),
("air-jet-wide","aircraft","大型四发宽体喷气客机，圆润机头，宽厚机身、四翼下喷气引擎"),
("air-supersonic","aircraft","超音速客机，修长低鼻，明显三角翼，象牙玉绿，无武器"),
("air-helicopter","aircraft","民用运输直升机，仅机身尾梁和滑橇，顶部旋翼轴但无旋翼叶片，独立旋翼后续叠加")]
familyDict={k:{"id":k,"transport":t,"identity":i,"directions":j["directionOrder"],"sourceArt":None,"artStatus":"planned","path":"assets/world/vehicles/families/"+k}for k,t,i in families}
hopper={"CT_COAL","MCT_GRAIN_WHEAT_MAIZE","CT_IRON_ORE","CT_COPPER_ORE","CT_SUGAR","CT_COTTON_CANDY","CT_TOFFEE"}
tank={"CT_OIL","CT_WATER","CT_COLA"}
flat={"CT_WOOD","CT_STEEL","CT_RUBBER","CT_FRUIT","CT_BATTERIES","CT_FIZZY_DRINKS","CT_PLASTIC"}
def getFamily(e):
 p=e["rawVisualProperties"];cargo=e["cargo"]
 if e["type"]=="train":
  if e["isWagon"]:
   return "wagon-passenger"if cargo=="CT_PASSENGERS"else"wagon-hopper"if cargo in hopper else"wagon-tank"if cargo in tank else"wagon-flat"if cargo in flat else"wagon-vent"if cargo=="CT_LIVESTOCK"else"wagon-box"
  if e["climates"]==["toyland"]:return"loco-toy"
  return {"S":"loco-steam","D":"loco-diesel","E":"loco-electric","N":"loco-monorail","V":"loco-maglev"}[p[10]]
 if e["type"]=="road":
  return "road-bus"if cargo=="CT_PASSENGERS"else"road-tank"if cargo in tank else"road-open"if cargo in hopper else"road-flat"if cargo in flat else"road-box"
 if e["type"]=="ship":return {0:"ship-cargo",1:"ship-tanker",2:"ship-ferry",3:"ship-hovercraft"}[e["originalImageIndex"]]
 if p[3]=="H":return"air-helicopter"
 if e["originalImageIndex"]in[8,16,18,24]:return"air-supersonic"
 if"PROPELLER"in p[4]:
  return"air-small-prop"if int(p[-1])<=30 else"air-large-prop"
 return"air-jet-wide"if int(p[-1])>=220 else"air-jet-narrow"
for e in j["engines"]:
 e["familyId"]=getFamily(e)
 e["modelVariant"]={"operation":"明确的涂装/车厢货载/运营代际派生，不是独立AI原画","variantIndex":e["id"],"toyland":e["climates"]==["toyland"],"trackHardware":{"R":"rail","C":"electric","O":"monorail","L":"maglev"}.get(e["rawVisualProperties"][9])if e["type"]=="train"else None}
 e["requiredStates"]=["empty","loaded"]if(e["isWagon"]or e["type"]=="road"and e["cargo"]!="CT_PASSENGERS")else["body"]
 if e["type"]=="aircraft"and e["familyId"]=="air-helicopter":e["requiredEffects"]=["rotor-stopped","rotor-running"]
 e["runtimePath"]="assets/world/vehicles/models/"+str(e["id"]).zfill(3)
 e["artStatus"]="planned"
for f in familyDict.values():
 f["modelIds"]=[e["id"]for e in j["engines"]if e["familyId"]==f["id"]]
contract={
"schemaVersion":1,"project":"云途万里","referenceCommit":j["referenceCommit"],"plannedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"artSource":"host_image","route":"builtin image_gen only; no paid API or video route authorized","allModels":256,"transportCounts":j["counts"],"baseFamilyCount":len(familyDict),"families":list(familyDict.values()),"models":j["engines"],
"camera":{"projection":"orthographic isometric","elevationDegrees":30,"worldTileDisplay":[128,64],"headingConvention":"screen aligned","directions":j["directionOrder"],"headDefinition":{"N":"rear view, nose points top","NE":"rear-right view, nose points upper-right","E":"right profile, nose points right","SE":"front-right view, nose points lower-right","S":"front view, nose points bottom","SW":"front-left view, nose points lower-left","W":"left profile, nose points left","NW":"rear-left view, nose points upper-left"}},
"generation":{"sheet":"4x2 directions, separated cells, transparent alpha, target2048x1024; saved native dimensions govern final crop","referenceImages":["F:/work/image/designs/mail-ui-v1/01-mail-event.png","F:/work/image/designs/team-ui-v2/team-ui-v2.png"],"modelQuality":"read F config every generation; actual hidden fields remain unconfirmed","noMirroredDirectionClaim":True},
"export":{"canvas":[512,512],"nativeScale":"Downscale only if required; pad to shared512 cells, no enlargement","pivot":[0.5,0.35],"ppuSuggestion":100,"filter":"Bilinear","spriteMode":"Single or explicitly mapped Multiple atlas","unityStatus":"not imported"},
"motion":{"baseBodies":"Stationary 8 direction frames; game translates vehicle bodies. No invented wheel/body animation required by base source.","effects":["steam smoke","diesel smoke","electric sparks","breakdown smoke","ship wake suggestion","plane propeller suggestion","helicopter rotor stopped/running","crash/explosion shared world FX"],"distinction":"Any rigid part rotation or frame compositing is deterministic derivative, not native AI motion or video.","externalVideoRouteUsed":False},
"acceptance":{"allModelMappingsRequired":True,"allDirectionsRequired":True,"emptyLoadedWhereSourceUsesRequired":True,"verifyTransparentAlpha":True,"verifyCellNoSpill":True,"verifyHeadingByVisualReview":True,"verifyIdentityAndSharedScale":True,"claim256IndependentNativeArt":False}}
(D/"VEHICLE_PRODUCTION_CONTRACT.json").write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding="utf-8")
print("families",len(familyDict),"mapped",len(j["engines"]),"min direction frames",256*8)
print([(f["id"],len(f["modelIds"]))for f in familyDict.values()])


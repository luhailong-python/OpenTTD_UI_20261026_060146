from pathlib import Path
import re,json,hashlib,datetime,collections
ROOT=Path(r"E:\work\image\OpenTTD_UI_20261026_060146")
SRC=ROOT/"reference/OpenTTD"
text=(SRC/"src/table/engines.h").read_text(encoding="utf-8")
lines=text.splitlines()
eng=[]
for ln,line in enumerate(lines,1):
 m=re.match(r"\s*(M[TMWRSA])\((.*?)\),\s*//\s*(\d+)\s+(.+)$",line)
 if not m:continue
 macro,params,num,name=m.groups();front,climates=params.split("LandscapeTypes",1)
 a=[x.strip() for x in front.rstrip(", ").split(",")]
 cs=re.search(r"\{([^}]+)\}",climates).group(1).replace(" ","").split(",")
 typ={"MT":"train","MM":"train","MW":"train","MR":"road","MS":"ship","MA":"aircraft"}[macro]
 eng.append({"id":int(num),"upstreamName":name,"type":typ,"macro":macro,"isWagon":macro=="MW","cargo":a[4]if macro!="MA"else None,"climates":[{"T":"temperate","A":"arctic","S":"tropic","Y":"toyland"}[c]for c in cs if c],"baseIntroductionDaysSince1920":int(a[0]),"source":{"file":"src/table/engines.h","line":ln},"artStatus":"missing"})
arrays={}
for n,macro,base in [("rail","RVI",0),("ship","SVI",204),("aircraft","AVI",215),("road","ROV",116)]:
 arr=[]
 for ln,line in enumerate(lines,1):
  m=re.match(r"\s*"+macro+r"\((.*?)\),\s*//\s*(\d+)\s+(.+)$",line)
  if not m:continue
  params,num,name=m.groups();pars=[x.strip()for x in params.split(",")]
  arr.append({"index":int(num),"globalId":base+int(num),"upstreamName":name,"imageIndex":int(pars[0]),"parameters":pars,"sourceLine":ln})
 arrays[n]=arr
for e in eng:
 ar=arrays[{"train":"rail","road":"road","ship":"ship","aircraft":"aircraft"}[e["type"]]]
 row=next(q for q in ar if q["globalId"]==e["id"])
 e["originalImageIndex"]=row["imageIndex"];e["visualSourceLine"]=row["sourceLine"];e["rawVisualProperties"]=row["parameters"]
counts=dict(collections.Counter(x["type"]for x in eng))
result={"schemaVersion":1,"referenceCommit":"cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8","counts":counts,"total":len(eng),"locomotives":sum(e["type"]=="train"and not e["isWagon"]for e in eng),"railWagons":sum(e["isWagon"]for e in eng),"directionOrder":["N","NE","E","SE","S","SW","W","NW"],"directionDefinition":"Screen-aligned; N points to top of viewport, not the map's rotated grid north.","engines":eng,"sourceArrays":arrays,"sourceSha256":hashlib.sha256((SRC/"src/table/engines.h").read_bytes()).hexdigest()}
(ROOT/"docs/VEHICLE_SOURCE_DATA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in result.items()if k not in ["engines","sourceArrays","sourceSha256"]},ensure_ascii=False))
print("unique original image indices",[(k,len(set(x["imageIndex"]for x in v)))for k,v in arrays.items()])


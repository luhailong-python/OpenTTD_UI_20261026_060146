"""Package generated brand rasters. No drawing or retouching of logo artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
now = datetime.now(timezone.utc).isoformat()
config = json.loads(Path(r"F:\work\image\config\image-generation.json").read_text(encoding="utf-8-sig"))
items = []
for stem in ("logo-main", "logo-symbol"):
    p = ROOT / (stem + ".png")
    call_path = ROOT / "records" / (stem + "-call.json")
    call = json.loads(call_path.read_text(encoding="utf-8"))
    im = Image.open(p)
    refs = [{"path":x, "sha256":sha(x), "purpose":"identity reference" if stem=="logo-symbol" and i==0 else "visual style / actual game art reference"} for i,x in enumerate(call["submittedParameters"]["referenced_image_paths"])]
    gen = {
        "file":p.name, "sha256":sha(p), "generatedAt":call["finishedAt"],
        "tool":"image_gen.imagegen", "route":"builtin", "width":im.width, "height":im.height, "format":"PNG",
        "configSnapshot":config, "submittedParameters":call["submittedParameters"],
        "actualModel":None, "actualQuality":None,
        "unverifiedReason":"宿主管理；工具无 model/quality 参数，返回仅 image_url/output_hint，未披露具体模型及质量。",
        "evidence":{"returnedFields":call["returnedFields"], "returnedPath":call["returnedPath"], "callRecord":"records/"+call_path.name},
        "promptFile":"records/"+stem+".prompt.txt", "references":refs,
        "status":"current design; local review pending"
    }
    generation_path = Path(str(p)+".generation.json")
    if generation_path.exists():
        # Repackaging must never replace historical model/configuration evidence.
        existing_generation = json.loads(generation_path.read_text(encoding="utf-8-sig"))
        if existing_generation.get("sha256") != sha(p):
            raise ValueError("Native PNG changed; create a new generation record/version rather than rewriting history")
    else:
        save_json(generation_path, gen)
    alpha = im.convert("RGBA").getchannel("A")
    hist = alpha.histogram()
    items.append({"file":p.name, "role":"main-title" if stem=="logo-main" else "symbol",
        "sha256":sha(p), "nativeSize":list(im.size), "generationRecord":p.name+".generation.json",
        "mode":im.mode, "alphaRange":list(alpha.getextrema()),
        "transparentPixels":hist[0], "visibleBoundsAlpha32":alpha.point(lambda a:255 if a>=32 else 0).getbbox()})

# Conventional exports: only LANCZOS downsampling, no repainting or alpha alteration.
exports = []
for stem, widths in (("logo-main",(1024,512)),("logo-symbol",(512,256,128,64))):
    p = ROOT/(stem+".png")
    im = Image.open(p).convert("RGBA")
    for width in widths:
        height=round(im.height*width/im.width)
        name = f"{stem}-{width}w.png" if stem=="logo-main" else f"{stem}-{width}.png"
        out=ROOT/name
        im.resize((width,height), Image.Resampling.LANCZOS).save(out)
        d={"file":name, "sha256":sha(out), "width":width,"height":height,
            "derivedFrom":[{"file":p.name,"sha256":sha(p),"generationRecord":p.name+".generation.json"}],
            "operation":"uniform LANCZOS downsample; original alpha preserved by resampling; no added native detail"}
        save_json(str(out)+".derivation.json",d)
        exports.append(d)

# A review board uses the existing generated pixels on light and dark backgrounds.
board=Image.new("RGBA",(1600,1300),"#EEE9DA")
d=ImageDraw.Draw(board)
font=PROJECT/"assets/fonts/NotoSansSC-Variable.ttf"
f38=ImageFont.truetype(str(font),38)
f26=ImageFont.truetype(str(font),26)
f20=ImageFont.truetype(str(font),20)
d.text((70,36),"云途万里  ·  游戏品牌设计",fill="#164F45",font=f38)
d.text((70,92),"云山意境 × 线路建设 × 运输经营",fill="#61746A",font=f26)
def place(img,maxsize,xy):
    img=img.copy()
    img.thumbnail(maxsize,Image.Resampling.LANCZOS)
    board.alpha_composite(img,(xy[0]+(maxsize[0]-img.width)//2,xy[1]+(maxsize[1]-img.height)//2))
main=Image.open(ROOT/"logo-main.png").convert("RGBA")
symbol=Image.open(ROOT/"logo-symbol.png").convert("RGBA")
place(main,(1480,470),(60,135))
d.rectangle((0,630,1600,1015),fill="#164F45")
d.text((70,651),"深色背景适配",fill="#D5C699",font=f20)
place(main,(1330,330),(135,680))
d.text((70,1040),"独立图标",fill="#164F45",font=f26)
for size,x in ((192,70),(128,340),(64,560)):
    place(symbol,(size,size),(x,1095))
    d.text((x+size+14,1110),f"{size}px",fill="#164F45",font=f20)
d.text((790,1104),"玉绿  #164F45",fill="#164F45",font=f26)
d.text((790,1154),"暖金  #B78F49",fill="#9B773C",font=f26)
d.text((790,1204),"米白  #FFF2D1",fill="#61746A",font=f26)
preview=ROOT/"brand-preview.jpg"
board.convert("RGB").save(preview,quality=95)
save_json(str(preview)+".derivation.json",{
 "file":preview.name,"sha256":sha(preview),"derivedFrom":[{"file":p.name,"sha256":sha(p)} for p in (ROOT/"logo-main.png",ROOT/"logo-symbol.png")],
 "operation":"presentation-only alpha composition onto light/dark backgrounds, uniform downsample, labels in project font; no artwork retouching","size":[1600,1300]})
old_preview=ROOT/"logo-on-ivory-preview.jpg"
if old_preview.exists():
    save_json(str(old_preview)+".derivation.json",{"file":old_preview.name,"sha256":sha(old_preview),
     "derivedFrom":[{"file":"logo-main.png","sha256":sha(ROOT/"logo-main.png")}],
     "operation":"presentation-only alpha composite onto solid #EEE9DA; no artwork retouching"})
checks=[]
def check(name,ok): checks.append({"name":name,"passed":bool(ok)})
for item in items:
    check(item["file"]+" RGBA",item["mode"]=="RGBA")
    check(item["file"]+" real transparent alpha",item["alphaRange"]==[0,255] and item["transparentPixels"]>1000)
    check(item["file"]+" generation record exists",(ROOT/item["generationRecord"]).exists())
for item in exports:
    p=ROOT/item["file"]
    check(item["file"]+" dimensions",list(Image.open(p).size)==[item["width"],item["height"]])
    check(item["file"]+" provenance",sha(p)==item["sha256"] and (ROOT/item["derivedFrom"][0]["file"]).exists())
manifest={
 "name":"云途万里","latinTransliteration":"Yun Tu Wan Li","selectedAt":now,
 "nameDecision":"current selected game title for design; user review pending",
 "genre":"多交通方式运输与产业经营模拟","style":"道家Q版高清手绘",
 "rationale":{"云":"云山、流云与轻盈东方气质","途":"交通线路、建设和连接","万里":"运输网络与城镇产业的持续扩展"},
 "nativeAssets":items,"derivedExports":exports,
 "preview":"brand-preview.jpg",
 "usage":{"main":"启动页、主菜单、宣传图；建议显示宽度至少480px。","symbol":"启动器、应用入口；建议显示尺寸至少64px，128px及以上更清楚。",
 "constraints":"保持等比；主Logo与独立图标按场景择一；导出为光栅PNG，不是可编辑矢量路径。"},
 "artGenerationRoute":"builtin image_gen",
 "localVisualReview":None,"userApproved":False,
 "scopeNote":"新增独立品牌包；先前全游戏资源终检为此前时间点的快照，未冒称包含本新增Logo。"
}
previous_manifest_path = ROOT/"manifest.json"
if previous_manifest_path.exists():
    previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8-sig"))
    if previous_manifest.get("integrationAuthorized"):
        for key in ("selectedAt", "nameDecision", "formalResourceManifest", "completeResourceIndex", "integrationPreview", "scopeNote", "integrationAuthorized", "integrationRecord", "localVisualReview"):
            if key in previous_manifest:
                manifest[key] = previous_manifest[key]
save_json(previous_manifest_path,manifest)
save_json(ROOT/"records/validation.json",{"checkedAt":now,"checks":checks,"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks),"visualReviewPending":True})
print(json.dumps({"native":items,"exports":len(exports),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)},ensure_ascii=False))

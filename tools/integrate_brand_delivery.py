"""Integrate current brand metadata and offline viewers without repainting artwork."""
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image
import json, hashlib, html

R=Path(__file__).resolve().parents[1]
B=R/"branding/yuntu-wanli"
def load(p): return json.loads((R/p).read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sj(p,x): (R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def replace_file(p, pairs):
    path=R/p
    s=path.read_text(encoding="utf-8-sig")
    for old,new in pairs: s=s.replace(old,new)
    path.write_text(s,encoding="utf-8")
now=datetime.now(timezone.utc).isoformat()
package=load("branding/yuntu-wanli/manifest.json")
rows=[]
for native, group in ((True,package["nativeAssets"]),(False,package["derivedExports"])):
    for item in group:
        name=item["file"]; file="branding/yuntu-wanli/"+name; p=R/file
        im=Image.open(p).convert("RGBA")
        stem=p.stem
        identifier="brand_main" if name=="logo-main.png" else "brand_symbol" if name=="logo-symbol.png" else "brand_"+stem.removeprefix("logo-").replace("-","_")
        parent=name if native else item["derivedFrom"][0]["file"]
        generation="branding/yuntu-wanli/"+parent+".generation.json"
        row={"id":identifier,"file":file,"width":im.width,"height":im.height,"format":"PNG","mode":"RGBA","sha256":sha(p),
             "role":"main-title" if name.startswith("logo-main") else "symbol",
             "category":"branding","border":[0,0,0,0],"pivot":[.5,.5],"pivotUnity":[.5,.5],"alphaMin":0,"alphaMax":255,
             "nativeModelGeneration":native,"generationRecord":generation,"sourceGenerationRecord":generation,
             "operation":"Unmodified built-in image_gen native logo PNG" if native else item["operation"],
             "textureType":"Sprite (2D and UI)","spriteMode":"Single","spriteType":"Simple","meshType":"FullRect",
             "filterMode":"Bilinear","wrapMode":"Clamp","mipMaps":False,"pixelsPerUnit":100,"alphaIsTransparency":True,
             "usage":"Formal static game branding; proportional scale only; no nine-slice",
             "actualModel":None,"actualQuality":None,"unityValidated":False,"userArtAccepted":False}
        if not native:
            source="branding/yuntu-wanli/"+parent
            row["source"]=source; row["sourceSha256"]=sha(R/source)
            row["derivedFrom"]=[{"file":source,"sha256":sha(R/source),"generationRecord":generation}]
        rows.append(row)
sj("docs/asset-branding-manifest.json",rows)
package.update({"nameDecision":"正式名称已获用户授权采用并统一整合；最终审美确认单独记录。",
    "formalResourceManifest":"../../docs/asset-branding-manifest.json",
    "completeResourceIndex":"../../docs/ART_RESOURCE_INDEX.json",
    "integrationPreview":"../../previews/branding/index.html",
    "scopeNote":"正式品牌包纳入整款游戏美术交付；先前审计只代表其时间点，新整包审计单独覆盖本次整合。",
    "integrationAuthorized":True,"integrationRecord":"../../records/brand-integration-validation.json"})
sj("branding/yuntu-wanli/manifest.json",package)
# Current delivery contracts get the formal title. Production pack history remains intact.
for f in ("docs/WORLD_ASSET_COVERAGE.json","docs/WORLD_ASSET_MANIFEST.json","docs/WORLD_DELIVERY_COVERAGE.json","docs/VEHICLE_PRODUCTION_CONTRACT.json"):
    q=load(f)
    q["project"]="云途万里"
    sj(f,q)
delivery=load("DELIVERY.json");delivery["project"]="云途万里";delivery["updatedAt"]=now
delivery["status"]="brand-integration-checks-pending"
delivery["manifests"].update({"branding":"docs/asset-branding-manifest.json","completeImportIndex":"docs/ART_RESOURCE_INDEX.json"})
delivery["docs"]["brandIntegration"]="docs/BRAND_INTEGRATION_DELIVERY.md"
delivery["previewEntries"]["branding"]="previews/branding/index.html"
sj("DELIVERY.json",delivery)
# Current UI viewer and its generated overview use the adopted logo too.
replace_file("tools/build_delivery.py",[
    ('["common","icons","cargo","portraits"]','["common","icons","cargo","portraits","branding"]'),
    ('{"referenceResolution":[1920,1080],"resources":resources','{"project":"云途万里","referenceResolution":[1920,1080],"resources":resources'),
    ('云途万里（暂名）','云途万里'),
    ('<h1>云途万里 <small>暂名</small></h1>','<h1 class="brand-title"><img src="branding/yuntu-wanli/logo-main.png" alt="云途万里" width="1860" height="845"></h1>'),
    ('</title><style>','</title><link rel="icon" type="image/png" href="branding/yuntu-wanli/logo-symbol-64.png"><style>'),
    ('font-weight:400;margin:8px 0}header p{color:', 'font-weight:400;margin:8px 0}.brand-title{max-width:680px;margin:-16px 0 -12px}.brand-title img{display:block;width:100%;height:auto}header p{color:'),
    ('<nav><a href="previews/manager-customization/', '<nav><a href="previews/branding/index.html" target="_blank">正式名称与Logo</a><a href="previews/manager-customization/'),
    ('<div class="resources"><a href="records/common-assets-qa.png"','<div class="resources"><a href="previews/branding/index.html" target="_blank">品牌Logo与图标</a><a href="docs/asset-branding-manifest.json" target="_blank">品牌导入参数</a><a href="records/common-assets-qa.png"'),
    ('sheet=Image.new("RGB",(1920,1190)', 'sheet=Image.new("RGB",(1920,1290)'),
    ('d.text((30,14),"云途万里 · 整套 UI 总览",font=font(35),fill="#164F45")',
     'logo=Image.open(ROOT/"branding/yuntu-wanli/logo-main.png").convert("RGBA");logo.thumbnail((360,164),Image.Resampling.LANCZOS);sheet.paste(logo,(24,0),logo)\n d.text((420,45),"整套 UI 美术总览",font=font(35),fill="#164F45")'),
    ('y=(j//3)*370+75','y=(j//3)*370+175'),
    ('"operation":"九个完整设计稿缩略拼版","derivedFrom":[s["designPath"]for s in chosen]',
     '"operation":"九个完整设计稿与正式Logo等比缩略拼版","derivedFrom":[s["designPath"]for s in chosen]+["branding/yuntu-wanli/logo-main.png"]'),
])
# Fix active templates as well as generated HTML, without re-exporting world art.
for f in ("tools/build_full_overview.py","tools/build_vehicle_fx_preview.py","tools/world_preview_template.html","tools/build_airport_gallery.py",
          "tools/plan_vehicles.py","tools/inventory_world_assets.py","tools/build_vegetation.py","tools/finalize_industries.py",
          "previews/world/index.html","previews/vehicles/index.html","previews/world/airports/index.html"):
    replace_file(f,[("云途万里（暂名）","云途万里"),("正式名称待确认","正式名称：云途万里")])
# Add a real symbol and shortcut in the existing three high-level galleries.
for f in ("previews/world/index.html","previews/vehicles/index.html","previews/world/airports/index.html"):
    p=R/f; s=p.read_text(encoding="utf-8")
    prefix="../../../" if "airports" in f else "../../"
    if 'data-brand-navigation="true"' not in s:
        nav='<a data-brand-navigation="true" href="'+prefix+'index.html" style="display:inline-flex;align-items:center;gap:10px;color:inherit;text-decoration:none;margin:0 0 12px"><img src="'+prefix+'branding/yuntu-wanli/logo-symbol-64.png" alt="云途万里" width="48" height="48" style="object-fit:contain"><span>云途万里 · 美术交付首页</span></a>'
        s=s.replace("<header>","<header>"+nav,1)
    p.write_text(s,encoding="utf-8")
# Future generators reproduce the same branding navigation.
for f,prefix in (("tools/world_preview_template.html","../../"),("tools/build_vehicle_fx_preview.py","../../"),("tools/build_airport_gallery.py","../../../")):
    p=R/f; s=p.read_text(encoding="utf-8")
    if 'data-brand-navigation="true"' not in s:
        nav='<a data-brand-navigation="true" href="'+prefix+'index.html" style="display:inline-flex;align-items:center;gap:10px;color:inherit;text-decoration:none;margin:0 0 12px"><img src="'+prefix+'branding/yuntu-wanli/logo-symbol-64.png" alt="云途万里" width="48" height="48" style="object-fit:contain"><span>云途万里 · 美术交付首页</span></a>'
        s=s.replace("<header>","<header>"+nav,1)
    p.write_text(s,encoding="utf-8")
# A single canonical logo viewer: direct links to all eight formal PNGs.
out=R/"previews/branding";out.mkdir(parents=True,exist_ok=True)
cards=[]
for q in rows:
    cards.append('<article><div class="checker"><img src="../../'+q["file"]+'" alt="'+html.escape(q["id"])+'"></div><h3>'+html.escape(q["id"])+'</h3><p>'+str(q["width"])+' × '+str(q["height"])+' · '+('原生图' if q["nativeModelGeneration"] else '等比缩小')+'</p><a href="../../'+q["file"]+'" download>下载透明 PNG</a></article>')
page="""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>云途万里 · 正式品牌与 Logo</title><link rel="icon" type="image/png" href="../../branding/yuntu-wanli/logo-symbol-64.png"><style>
@font-face{font-family:noto;src:url('../../assets/fonts/NotoSansSC-Variable.ttf')}*{box-sizing:border-box}body{margin:0;background:#eee9da;color:#164f45;font:16px noto,system-ui}header,main,footer{padding:28px 5vw;max-width:1600px;margin:auto}h1{font-size:30px;margin:0 0 12px}a{color:inherit;overflow-wrap:anywhere}nav{display:flex;gap:20px;flex-wrap:wrap}p{line-height:1.8}.hero{display:grid;gap:20px}.plate{padding:20px;border-radius:16px;min-width:0;border:1px solid #bc9c62}.plate.dark{background:#164f45;color:#fff2d1}.plate img{display:block;width:100%;max-width:1100px;height:auto;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,310px),1fr));gap:20px}article{padding:18px;border:1px solid #b79a68;border-radius:14px;min-width:0}article img{max-width:100%;max-height:200px;object-fit:contain}h3{font-size:18px;overflow-wrap:anywhere}.checker{height:220px;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#ddd8c9 0% 25%,#f5f1e6 0% 50%) 50%/24px 24px;border-radius:10px}.iconline{display:flex;align-items:center;gap:28px;flex-wrap:wrap}.iconline figure{margin:0;display:grid;gap:8px;justify-items:center}.iconline img{object-fit:contain}small{color:#617269}footer{font-size:13px}section{margin-bottom:40px}@media(max-width:600px){header,main,footer{padding:20px}.plate{padding:6px}h1{font-size:25px}}
</style></head><body><header><h1>云途万里 · 正式品牌与 Logo</h1><p>道家 Q 版手绘 · 交通线路建设与产业运输经营</p><nav><a href="../../index.html">完整美术交付</a><a href="../../docs/asset-branding-manifest.json">正式品牌资源参数</a><a href="../../docs/ART_RESOURCE_INDEX.json">整包导入索引</a><a href="../../docs/BRAND_INTEGRATION_DELIVERY.md">整合与检查说明</a></nav></header><main><section class="hero"><div class="plate"><img data-main-logo src="../../branding/yuntu-wanli/logo-main.png" alt="云途万里正式主Logo"></div><div class="plate dark"><img data-main-logo src="../../branding/yuntu-wanli/logo-main.png" alt="云途万里主Logo深色底适配"></div></section><section><h2>独立图标</h2><div class="iconline">"""
for size in (256,128,64):
    page+='<figure><img src="../../branding/yuntu-wanli/logo-symbol-'+str(size)+'.png" alt="云途万里独立图标'+str(size)+'像素" width="'+str(size)+'" height="'+str(size)+'"><figcaption>'+str(size)+'px</figcaption></figure>'
page+="""</div><p>主 Logo 用于启动和主菜单，建议宽度至少 480px。小入口使用独立图标；128px 以上更清楚，64px 保留列车与云环轮廓。保持等比缩放。</p></section><section><h2>全部正式品牌 PNG</h2><div class="grid">"""+''.join(cards)+"""</div></section><section><h2>正式画面中的应用</h2><nav><a href="../../index.html#01-main-menu">启动与主菜单</a><a href="../../index.html#02-bootstrap">基础资源引导</a><a href="../../index.html#09-main-hud">经营主视窗</a><a href="../../index.html#123-about">关于游戏</a></nav></section></main><footer>2 张原生绘画，6 张等比缩小导出；透明 PNG 未进行重绘。<br>本页为美术离线预览，未开展 Unity 接入。<br><a href="../../branding/yuntu-wanli/README.md">品牌说明与完整提示词</a></footer></body></html>"""
(out/"index.html").write_text(page,encoding="utf-8")
print(json.dumps({"brandFormalPNGs":len(rows),"native":2,"derived":6,"formalName":"云途万里","worldArtChanged":False},ensure_ascii=False))

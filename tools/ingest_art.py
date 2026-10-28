from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image
ROOT=Path(r"E:\work\image\OpenTTD_UI_20261026_060146")
F=Path(r"F:\work\image")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
refs=["designs/mail-ui-v1/01-mail-event.png","designs/team-ui-v2/team-ui-v2.png"]
config=json.loads((F/"config/image-generation.json").read_text(encoding="utf-8-sig"))
sources=[
("assets/transport-valley.png","exec-143e5795-af5b-45e4-9879-af3ed377730f.png","01-transport-valley.prompt.txt",False),
("source-art/ui-kit.png","exec-aa2b6766-fb48-409a-92db-afa9e15235e1.png","02-ui-kit.prompt.txt",True),
("source-art/system-icons.png","exec-97af972b-aff5-4f3e-98a7-70991b971edf.png","03-system-icons.prompt.txt",True),
("assets/world-viewport.png","exec-aa8c0680-f25a-4d44-83b0-ce05e78221ae.png","04-world-viewport.prompt.txt",False),
("source-art/cargo-icons.png","exec-55d629d7-50a0-40b8-9116-e78d175f4c2f.png","05-cargo-icons.prompt.txt",True),
("source-art/managers.png","exec-42522bde-6130-48da-be7b-c69f18e380a9.png","06-managers.prompt.txt",True),
("source-art/helicopter.png","exec-31d7565f-cc37-4187-9abc-2090c5a036a3.png","07-helicopter.prompt.txt",True)]
gen=Path(r"C:\Users\luyua\.codex\generated_images\01a177a7-6d36-72f1-8ac7-6c557c4ea2e3")
for dest,src,prompt,alpha in sources:
 out=ROOT/dest;out.parent.mkdir(parents=True,exist_ok=True)
 if not out.exists():shutil.copy2(gen/src,out)
 im=Image.open(out)
 dt=datetime.datetime.fromtimestamp(out.stat().st_mtime,datetime.timezone.utc)
 record={"file":dest,"sha256":sha(out),"generatedAt":dt.isoformat(),"width":im.width,"height":im.height,"format":im.format,"mode":im.mode,
 "tool":"image_gen.imagegen","route":"builtin","toolResultId":None,"outputFileId":src.removeprefix("exec-").removesuffix(".png"),"generatedAtEvidence":"本地生成输出PNG的文件落盘时间，UTC；工具未返回服务端生成时间。",
 "configSnapshot":config,"submittedParameters":{"model":None,"quality":None,"prompt":"records/"+prompt,"referenced_image_paths":[str(F/r) for r in refs],"transparent_background":alpha},
 "actualModel":None,"actualQuality":None,"evidence":{"returnedFields":["image_url","output_hint"],"output_hint_path":str(gen/src),"nativeSizeFromSavedPNG":[im.width,im.height]},
 "unverifiedReason":"宿主管理，工具未披露实际模型版本或质量；配置目标不是实际返回证明。",
 "prompt":"records/"+prompt,"references":[{"path":str(F/r),"sha256":sha(F/r),"purpose":"首要手绘风格参考；未复制其业务文案"} for r in refs]}
 savej(str(out)+".generation.json",record)
snap=ROOT/"docs/reference-images";snap.mkdir(exist_ok=True)
for r in refs:shutil.copy2(F/r,snap/Path(r).name)
shutil.copy2(F/"AGENTS.md",ROOT/"docs/REFERENCE_AGENTS.md")
shutil.copy2(F/"config/image-generation.json",ROOT/"records/image-generation.config-snapshot.json")
savej(ROOT/"records/model-verification.json",{"verifiedOn":"2026-10-26","configurationUnchanged":True,"configurationTarget":config,"officialSources":config["sources"],"finding":"官方产品页与型号页确认目标系列及max质量。未发现可核实的更新正式版本。内置入口无model/quality选择器，实际调用型号/质量未确认。","artReferenceWrites":"仅后续必要关联记录；未更新F配置"})
print(json.dumps([{"file":x[0],"size":Image.open(ROOT/x[0]).size} for x in sources],ensure_ascii=False))


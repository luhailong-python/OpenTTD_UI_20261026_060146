from pathlib import Path
from PIL import Image
import json,hashlib,datetime,shutil,sys
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
family,source=sys.argv[1:3];source=Path(source)
request=json.loads((R/'records/vehicles'/f'{family}.request.json').read_text(encoding='utf-8'))
out=R/'assets/world/vehicles/families'/family;out.mkdir(parents=True,exist_ok=True)
atlas=out/'atlas.png'
if atlas.exists() and sha(atlas)!=sha(source):raise RuntimeError('Refusing to overwrite existing family atlas '+family)
shutil.copy2(source,atlas);im=Image.open(atlas).convert('RGBA')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
config=json.loads(Path(r'F:\work\image\config\image-generation.json').read_text(encoding='utf-8-sig'))
record={'file':atlas.relative_to(R).as_posix(),'sha256':sha(atlas),'generatedAt':datetime.datetime.fromtimestamp(atlas.stat().st_mtime,datetime.timezone.utc).isoformat(),'generatedAtEvidence':'local output file timestamp, tool server time not disclosed','width':im.width,'height':im.height,'format':'PNG','mode':im.mode,'tool':'image_gen.imagegen','route':'builtin','toolResultId':None,'outputFileId':source.stem,'configSnapshot':config,'submittedParameters':{'model':None,'quality':None,'transparent_background':True,'referenced_image_paths':request['references'],'prompt':request['prompt']},'actualModel':None,'actualQuality':None,'unverifiedReason':'宿主管理，工具未披露实际模型或质量。配置目标不是调用锁定或实际返回证明。','evidence':{'returnedFields':['image_url','output_hint'],'outputHint':request['output_hint'],'nativeSizeFromSavedPNG':[im.width,im.height]},'prompt':f'records/vehicles/{family}.prompt.txt','references':[{'path':p,'sha256':sha(p),'purpose':'style reference'if i<2 else'heading/layout guide, code diagram, not artwork'}for i,p in enumerate(request['references'])]}
savej(Path(str(atlas)+'.generation.json'),record)
record['promptFile']=record['prompt'];record['prompt']=request['prompt']
for i,ref in enumerate(record['references']):ref['purpose']='confirmed Taoist chibi UI painting style'if i<2 else'world camera and visual setting'if i==2 and len(request['references'])==4 else'heading/layout guide; code diagram, not painted artwork'
savej(Path(str(atlas)+'.generation.json'),record)
directions=['N','NE','E','SE','S','SW','W','NW'];frames=[]
scale=min(1,512/max(im.width/4,im.height/2))
for i,d in enumerate(directions):
 c=i%4;r=i//4
 box=[round(c*im.width/4),round(r*im.height/2),round((c+1)*im.width/4),round((r+1)*im.height/2)]
 cell=im.crop(box)
 # Atlas gutter is non-art. Only erase the outer 2 pixels of each equal cell;
 # this removes generator grid traces, never a largest-component matte filter.
 gutter=2
 a=cell.getchannel('A');a.paste(0,(0,0,cell.width,gutter));a.paste(0,(0,cell.height-gutter,cell.width,cell.height));a.paste(0,(0,0,gutter,cell.height));a.paste(0,(cell.width-gutter,0,cell.width,cell.height));cell.putalpha(a)
 if scale<1:cell=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(512,512));pad=[(512-cell.width)//2,(512-cell.height)//2];canvas.alpha_composite(cell,tuple(pad))
 p=out/(d+'.png');canvas.save(p)
 entry={'direction':d,'file':p.relative_to(R).as_posix(),'sha256':sha(p),'canvas':[512,512],'pivot':[.5,.35],'sourceRectXYXY':box,'sourceSize':[im.width,im.height],'uniformScale':scale,'paddingLeftTop':pad,'alphaExtrema':canvas.getchannel('A').getextrema(),'alphaBBox':canvas.getbbox(),'sourceCellGutterClearedPx':gutter,'operation':'uniform grid crop; erase only outer2px atlas gutter traces; one shared downscale only when needed; fixed512 transparent padding; not native512 detail','derivedFrom':{'file':atlas.relative_to(R).as_posix(),'sha256':record['sha256'],'record':atlas.relative_to(R).as_posix()+'.generation.json'},'headingVerified':False,'identityVerified':False}
 frames.append(entry);savej(Path(str(p)+'.derivation.json'),entry)
manifest={'familyId':family,'generatedAt':now,'atlas':record['file'],'nativeSize':[im.width,im.height],'frames':frames,'headingOrder':directions,'bodyAnimation':'8 static body facings; world translation belongs to gameplay','status':'needs-visual-review','actualModel':None,'actualQuality':None}
savej(out/'manifest.json',manifest)
contract=R/'docs/VEHICLE_PRODUCTION_CONTRACT.json';j=json.loads(contract.read_text(encoding='utf-8'))
for f in j['families']:
 if f['id']==family:f['sourceArt']=record['file'];f['artStatus']='needs-visual-review';f['manifest']=(out/'manifest.json').relative_to(R).as_posix()
savej(contract,j)
print(json.dumps({'family':family,'atlas':record['file'],'native':im.size,'frames':8,'status':'needs-visual-review'},ensure_ascii=False))


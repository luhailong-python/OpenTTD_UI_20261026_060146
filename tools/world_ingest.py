"""Record only real built-in calls and lossless/explicit derivatives."""
from pathlib import Path
from PIL import Image
import argparse,datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
F=Path(r"F:\work\image")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prompt_text(value):
 """Accept a saved prompt file or actual submitted text; never log a path as text."""
 if isinstance(value,Path):candidate=value
 elif isinstance(value,str)and len(value)<512 and '\n'not in value:
  candidate=Path(value)
 else:return str(value),None
 if not candidate.is_absolute():candidate=ROOT/candidate
 try:exists=candidate.is_file()
 except OSError:exists=False
 if not exists:return str(value),None
 try:label=candidate.resolve().relative_to(ROOT).as_posix()
 except ValueError:label=str(candidate.resolve())
 return candidate.read_text(encoding='utf-8-sig'),label
def record(source,dest,prompt,refs,transparent=True):
 prompt,prompt_file=prompt_text(prompt)
 src=Path(source);out=ROOT/dest;out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists()and sha(src)!=sha(out):raise RuntimeError("Refusing overwrite: "+str(out))
 if not out.exists():shutil.copy2(src,out)
 im=Image.open(out);config=json.loads((F/'config/image-generation.json').read_text(encoding='utf-8-sig'))
 q={'file':out.relative_to(ROOT).as_posix(),'sha256':sha(out),'generatedAt':datetime.datetime.fromtimestamp(src.stat().st_mtime,datetime.timezone.utc).isoformat(),'generatedAtEvidence':'UTC file write time of returned image; service timestamp not returned','width':im.width,'height':im.height,'format':im.format,'mode':im.mode,'tool':'image_gen.imagegen','route':'builtin','art_source':'host_image','toolResultId':None,'outputFileId':src.stem,'configSnapshot':config,'submittedParameters':{'model':None,'quality':None,'prompt':prompt,'referenced_image_paths':refs,'transparent_background':transparent},'actualModel':None,'actualQuality':None,'evidence':{'returnedFields':['image_url','output_hint'],'returnedPath':str(src),'nativeSizeFromPNG':[im.width,im.height]},'unverifiedReason':'宿主管理，入口与返回未披露实际模型/质量；目标不能视为锁定调用证据。','prompt':prompt,'references':[{'path':p,'sha256':sha(p),'purpose':'绘画风格、材质或投影参考；非旧游戏业务'}for p in refs]}
 if prompt_file:q['promptFile']=prompt_file
 Path(str(out)+'.generation.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
 return q
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--dest',required=True);p.add_argument('--prompt',required=True);p.add_argument('--reference',action='append',required=True);p.add_argument('--opaque',action='store_true');a=p.parse_args()
 q=record(a.source,a.dest,a.prompt,a.reference,not a.opaque);print(json.dumps({'file':q['file'],'size':[q['width'],q['height']],'sha256':q['sha256']},ensure_ascii=False))


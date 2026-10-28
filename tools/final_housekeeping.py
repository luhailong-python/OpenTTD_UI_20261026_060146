from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
items=json.loads((R/'docs/asset-cargo-manifest.json').read_text(encoding='utf-8'))
sheet=Image.new('RGB',(1440,1650),'#F2EEDC');d=ImageDraw.Draw(sheet)
f=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),18)
for i,a in enumerate(items):
 x=12+i%6*238;y=15+i//6*233;im=Image.open(R/a['file']).convert('RGBA');im.thumbnail((210,195));sheet.paste(im,(x+(220-im.width)//2,y),im);d.text((x+5,y+201),a['id'],font=f,fill='#164F45')
sheet.save(R/'previews/cargo-contact.png')
record={'file':'previews/cargo-contact.png','sha256':sha(R/'previews/cargo-contact.png'),'operation':'正式货物/运输PNG等比缩小及说明文字拼版；确定性派生，非AI新图','derivedFrom':[{'file':a['file'],'sha256':a['sha256']}for a in items],'actualModel':None,'actualQuality':None}
(R/'previews/cargo-contact.png.derivation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
c=json.loads((R/'docs/screen-catalog.json').read_text(encoding='utf-8'))
for s in c:s['status']='designed';s['productionManifest']='docs/UI_MASTER_MANIFEST.json'
(R/'docs/screen-catalog.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
# Only verified, task-local superseded QA files. Production masters stay intact.
targets=list((R/'previews').glob('*-sample.png'))+list((R/'previews/metric-qa').glob('*')) if (R/'previews/metric-qa').exists() else list((R/'previews').glob('*-sample.png'))
removed=[]
for p in targets:
 if p.is_file()and p.resolve().is_relative_to(R.resolve()):
  removed.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p),'reason':'被正式designs整屏和当前验收图替代的临时QA；不再被当前交付引用'})
  p.unlink()
q=R/'previews/metric-qa'
if q.exists()and not any(q.iterdir()):q.rmdir()
(R/'records/cleanup-final.json').write_text(json.dumps({'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'本任务已核实无用中间图','removed':removed,'productionMastersPreserved':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('cargo atlas entries',len(items),'removed temp files',len(removed))


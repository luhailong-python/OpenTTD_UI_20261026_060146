"""Deterministic lossless kit crops and byte-for-byte reference reuse. No AI call."""
from pathlib import Path
from PIL import Image
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
ART = Path('F:/work/image')
OUT = ROOT/'assets/common'
OUT.mkdir(parents=True, exist_ok=True)
EVID = ROOT/'records/reference-evidence'
EVID.mkdir(parents=True, exist_ok=True)
KIT = ROOT/'source-art/ui-kit.png'
FALLBACK = Path('C:/Users/luyua/.codex/generated_images/01a177a7-6d36-72f1-8ac7-6c557c4ea2e3/exec-aa2b6766-fb48-409a-92db-afa9e15235e1.png')
if not KIT.exists():
    shutil.copy2(FALLBACK, KIT)
manifest=[]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def add(id,path,border,source,operation,family=None,state=None,extra=None):
    im=Image.open(path)
    amin,amax=im.getchannel('A').getextrema() if 'A' in im.getbands() else (255,255)
    entry=dict(id=id,file=path.relative_to(ROOT).as_posix(),width=im.width,height=im.height,
               border=border,pivot=[.5,.5],source=source,operation=operation,
               sha256=sha(path),alphaMin=amin,alphaMax=amax,stateFamily=family,state=state)
    if extra:entry.update(extra)
    manifest.append(entry)
    return entry
im=Image.open(KIT).convert('RGBA')
crops=[
 ('panel_main',(44,57,1210,744),[112,116,112,90]),
 ('title_plate',(25,766,556,915),[0,0,0,0]),
 ('button_compact_primary',(558,782,897,906),[74,32,74,32]),
 ('button_compact_secondary',(895,783,1230,906),[74,32,74,32]),
]
for id,box,border in crops:
    p=OUT/(id+'.png'); im.crop(box).save(p)
    add(id,p,border,'source-art/ui-kit.png','lossless crop; no resampling',
        extra={'sourceSha256':sha(KIT),'cropXYXY':list(box),'sourceGenerationRecord':'source-art/ui-kit.png.generation.json'})
buttons=[
 ('button_primary_normal',(29,948,430,1061),'primary','normal'),
 ('button_primary_pressed',(430,948,825,1061),'primary','pressed'),
 ('button_primary_selected',(825,948,1226,1061),'primary','selected'),
 ('button_secondary_normal',(29,1074,430,1187),'secondary','normal'),
 ('button_secondary_pressed',(430,1074,825,1187),'secondary','pressed'),
 ('button_disabled',(825,1074,1226,1187),'shared','disabled'),
]
for id,box,family,state in buttons:
    crop=im.crop(box)
    out=Image.new('RGBA',(416,128))
    offset=((416-crop.width)//2,(128-crop.height)//2)
    out.alpha_composite(crop,offset)
    p=OUT/(id+'.png'); out.save(p)
    add(id,p,[84,34,84,34],'source-art/ui-kit.png','lossless crop and center on common transparent canvas; no resampling',family,state,
        {'sourceSha256':sha(KIT),'cropXYXY':list(box),'pasteXY':list(offset),'sourceGenerationRecord':'source-art/ui-kit.png.generation.json'})

ap=ART/'designs/attribute-panels/v2-painted/unity-slices'
am=json.loads((ap/'manifest.json').read_text(encoding='utf-8-sig'))
amap={a['name']:a for a in am['sprites']}
reuse=[
 ('reference-input',ap/'png/stat_field.png',amap['stat_field']['borderLeftBottomRightTop'],'input',None),
 ('reference-row',ap/'png/pet_card_normal.png',amap['pet_card_normal']['borderLeftBottomRightTop'],'row','normal'),
 ('reference-row-selected',ap/'png/pet_card_selected.png',amap['pet_card_selected']['borderLeftBottomRightTop'],'row','selected'),
 ('reference-dropdown',ap/'png/dropdown_arrow.png',[0,0,0,0],'dropdown',None),
 ('reference-close',ap/'png/close_button.png',[0,0,0,0],'close','normal'),
 ('reference-slider-thumb',ap/'png/slider_thumb.png',[0,0,0,0],'slider',None),
 ('reference-step-plus',ap/'png/step_plus.png',[0,0,0,0],'step',None),
 ('reference-step-minus',ap/'png/step_minus.png',[0,0,0,0],'step',None),
 ('reference-notice',ap/'png/notice_icon.png',[0,0,0,0],'notice',None),
 ('reference-paper',ap/'png/paper_tile.png',[11,11,11,11],'paper',None),
]
exact=ART/'designs/attribute-panels/exact-20261022/staged/Assets/Resources/UI/Ugui/AttributeExact20261022'
reuse += [
 ('reference-slider-track',exact/'slider_track.png',[11,0,11,0],'slider','track'),
 ('reference-slider-fill',exact/'slider_fill.png',[11,0,11,0],'slider','fill'),
]
eq=ART/'designs/equipment-ui-20261008/sprites'
reuse += [
 ('reference-checkbox-off',eq/'checkbox_off.png',[0,0,0,0],'checkbox','off'),
 ('reference-checkbox-on',eq/'checkbox_on.png',[0,0,0,0],'checkbox','on'),
]
team=ART/'designs/team-ui-v2/unity-slices/png'
reuse += [
 ('reference-status-online',team/'status_online.png',[0,0,0,0],'status','online'),
 ('reference-status-offline',team/'status_offline.png',[0,0,0,0],'status','offline'),
]
for id,src,border,family,state in reuse:
    p=OUT/(id+'.png');shutil.copy2(src,p)
    source=src.relative_to(ART).as_posix()
    evidence=[]
    sr=src.with_name(src.name+'.generation.json')
    if sr.exists():
        dest=EVID/(id+'.png.generation.json');shutil.copy2(sr,dest);evidence.append(dest.relative_to(ROOT).as_posix())
    e=add(id,p,border,'F:/work/image/'+source,'byte-for-byte copy; no AI, crop, or resampling',family,state,
          {'sourceRelativePath':source,'sourceSha256':sha(src),'sourceEvidence':evidence,'actualModel':None,'actualQuality':None,
           'unverifiedReason':'Historical asset; current configuration is not used to backfill its model or quality.'})
    p.with_name(p.name+'.generation.json').write_text(json.dumps({'file':e['file'],'sha256':e['sha256'],'derivedFrom':{'file':str(src),'sha256':sha(src),'evidence':evidence},'operation':e['operation'],'actualModel':None,'actualQuality':None,'unverifiedReason':e['unverifiedReason']},ensure_ascii=False,indent=2),encoding='utf-8')

evidence_files=[
 (ap/'manifest.json','attribute-original-manifest.json'),
 (ap/'README.md','attribute-original-README.md'),
 (ART/'designs/attribute-panels/exact-20261022/sprite-provenance.json','attribute-slider-provenance.json'),
 (ART/'designs/attribute-panels/exact-20261022/README.md','attribute-slider-README.md'),
 (ART/'designs/equipment-ui-20261008/sprite-manifest.json','equipment-original-manifest.json'),
 (ART/'designs/team-ui-v2/unity-slices/manifest.json','team-original-manifest.json'),
]
for src,name in evidence_files:
    if src.exists():shutil.copy2(src,EVID/name)

(ROOT/'docs/asset-common-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for e in manifest:
    if e['source']=='source-art/ui-kit.png':
        (ROOT/e['file']).with_name(Path(e['file']).name+'.generation.json').write_text(json.dumps({
          'file':e['file'],'sha256':e['sha256'],'width':e['width'],'height':e['height'],'format':'PNG',
          'derivedFrom':{'file':e['source'],'sha256':e['sourceSha256'],'generationRecord':e['sourceGenerationRecord']},
          'operation':e['operation'],'cropXYXY':e.get('cropXYXY'),'pasteXY':e.get('pasteXY'),
          'actualModel':None,'actualQuality':None,
          'unverifiedReason':'Derived raster: follow the original generation record. A crop is not a new AI generation.'
        },ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Wrote {len(manifest)} common assets and manifest.')

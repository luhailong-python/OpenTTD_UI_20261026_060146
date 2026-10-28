"""Eight native manager portraits, alpha separated, baseline aligned, never enlarged."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageFont,ImageOps
import numpy as np,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source-art/managers.png'
if not SRC.exists():shutil.copy2(Path('C:/Users/luyua/.codex/generated_images/01a177a7-6d36-72f1-8ac7-6c557c4ea2e3/exec-42522bde-6130-48da-be7b-c69f18e380a9.png'),SRC)
OUT=ROOT/'assets/portraits';OUT.mkdir(parents=True,exist_ok=True)
im=Image.open(SRC).convert('RGBA');a=np.array(im);alpha=a[:,:,3];h,w=alpha.shape
solid=(alpha>=64).ravel();labels=np.zeros(len(solid),dtype=np.int32);comps=[]
centres=[[255,695,1097,1553],[236,685,1097,1550]]
for seed in np.flatnonzero(solid):
    if labels[seed]:continue
    n=len(comps)+1;labels[seed]=n;stack=[int(seed)];count=0;xlo=w;ylo=h;xhi=0;yhi=0
    while stack:
        q=stack.pop();y,x=divmod(q,w);count+=1;xlo=min(xlo,x);ylo=min(ylo,y);xhi=max(xhi,x);yhi=max(yhi,y)
        zs=[]
        if x>0:zs.append(q-1)
        if x<w-1:zs.append(q+1)
        if y>0:zs.append(q-w)
        if y<h-1:zs.append(q+w)
        for z in zs:
            if solid[z] and labels[z]==0:labels[z]=n;stack.append(z)
    cx=(xlo+xhi)/2;cy=(ylo+yhi)/2;r=int(cy>=444);c=min(range(4),key=lambda k:abs(centres[r][k]-cx))
    comps.append({'label':n,'count':count,'box':[xlo,ylo,xhi+1,yhi+1],'owner':r*4+c})
labels=labels.reshape(h,w);srcsha=hashlib.sha256(SRC.read_bytes()).hexdigest();result=[]
for i in range(8):
    selectedcomps=[x for x in comps if x['owner']==i];labs=[x['label'] for x in selectedcomps]
    bb=[max(0,min(x['box'][0] for x in selectedcomps)-5),max(0,min(x['box'][1] for x in selectedcomps)-5),
        min(w,max(x['box'][2] for x in selectedcomps)+5),min(h,max(x['box'][3] for x in selectedcomps)+5)]
    x0,y0,x1,y1=bb;local_labels=labels[y0:y1,x0:x1];mask=np.isin(local_labels,labs).astype(np.uint8)*255
    maskim=Image.fromarray(mask).filter(ImageFilter.MaxFilter(9));padded=ImageOps.expand(maskim,border=1,fill=0)
    ImageDraw.floodfill(padded,(0,0),128);mask=np.array(padded)[1:-1,1:-1]!=128
    mask[(local_labels>0)&(~np.isin(local_labels,labs))]=False
    pixels=a[y0:y1,x0:x1].copy();pixels[:,:,3]=np.where(mask,alpha[y0:y1,x0:x1],0)
    cut=Image.fromarray(pixels);inner=cut.getbbox();cut=cut.crop(inner)
    box=[x0+inner[0],y0+inner[1],x0+inner[2],y0+inner[3]]
    assert cut.width<=480 and cut.height<=480,(i,cut.size)
    out=Image.new('RGBA',(512,512));xy=((512-cut.width)//2,480-cut.height);out.alpha_composite(cut,xy)
    id=f'manager-{i+1:02d}';p=OUT/(id+'.png');out.save(p)
    preserved=int(np.isin(labels,labs).sum());recovered=int((np.array(cut)[:,:,3]>=64).sum());assert preserved==recovered,(id,preserved,recovered)
    e={'id':id,'file':p.relative_to(ROOT).as_posix(),'width':512,'height':512,'border':[0,0,0,0],'pivot':[.5,.5],
       'source':'source-art/managers.png','sourceSha256':srcsha,'sourceGenerationRecord':'source-art/managers.png.generation.json',
       'row':i//4+1,'column':i%4+1,'cropXYXY':box,'nativeSubjectSize':[cut.width,cut.height],'pasteXY':list(xy),
       'baselineY':480,'operation':'native alpha-component separation with 4px antialias halo and enclosed selection hole fill; original RGBA retained; centered horizontal padding and shared baseline; no resampling',
       'alphaMin':0,'alphaMax':out.getchannel('A').getextrema()[1],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
       'segmentation':{'solidAlphaThreshold':64,'selectionDilationPixels':4,'componentLabels':labs,'preservedSourceSolidPixels':preserved,'outputSolidPixels':recovered},
       'resampling':False,'unityVerified':False}
    result.append(e)
    record={'file':e['file'],'sha256':e['sha256'],'width':512,'height':512,'format':'PNG',
            'derivedFrom':{'file':e['source'],'sha256':srcsha,'generationRecord':e['sourceGenerationRecord']},
            'operation':e['operation'],'cropXYXY':box,'pasteXY':list(xy),'actualModel':None,'actualQuality':None,
            'unverifiedReason':'Derived raster; actual model and quality follow source record. No new AI generation.'}
    p.with_name(p.name+'.generation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/asset-portraits-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'records/portrait-segmentation.json').write_text(json.dumps({'sourceSize':[w,h],'sourceSha256':srcsha,'components':comps},ensure_ascii=False,indent=2),encoding='utf-8')
contact=Image.new('RGB',(1200,650),'#eff0e6');d=ImageDraw.Draw(contact);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for i,e in enumerate(result):
    icon=Image.open(ROOT/e['file']);icon.thumbnail((290,290));x=(i%4)*300;y=(i//4)*325
    contact.paste(icon,(x+5,y),icon);d.text((x+95,y+296),e['id'],fill='#173d32',font=font)
contact.save(ROOT/'previews/portraits-contact.png')
print('Exported 8 native portraits, 512x512 transparent canvas, baselineY=480, no resampling.')

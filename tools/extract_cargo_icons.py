"""Split the actual nonuniform native atlas, preserving silhouette pixels at 1:1."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageFont
import numpy as np,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source-art/cargo-icons.png'
if not SRC.exists():
    shutil.copy2(Path('C:/Users/luyua/.codex/generated_images/01a177a7-6d36-72f1-8ac7-6c557c4ea2e3/exec-55d629d7-50a0-40b8-9116-e78d175f4c2f.png'),SRC)
OUT=ROOT/'assets/cargo';OUT.mkdir(parents=True,exist_ok=True)
ids='passengers,mail,coal,oil,livestock,goods,grain,wood,iron-ore,steel,valuables,paper,food,fruit,copper-ore,water,rubber,sugar,toys,batteries,sweets,toffee,cola,cotton-candy,bubbles,plastic,fizzy-drinks,gold,diamonds,seeds,passenger-carriage,coal-wagon,mail-van,electric-train,steamship,prop-plane'.split(',')
im=Image.open(SRC).convert('RGBA');arr=np.array(im);alpha=arr[:,:,3];h,w=alpha.shape
solid=(alpha>=64).ravel();labels=np.zeros(len(solid),dtype=np.int32)
components=[]
row_edges=[0,240,446,639,839,1036,1254]
col_edges=[
 [0,234,435,639,826,1050,1254],
 [0,226,442,635,851,1046,1254],
 [0,227,450,648,835,1046,1254],
 [0,239,431,644,884,1037,1254],
 [0,219,451,626,860,1045,1254],
 [0,233,428,629,853,1050,1254],
]
for seed in np.flatnonzero(solid):
    if labels[seed]:continue
    n=len(components)+1;labels[seed]=n;stack=[int(seed)]
    count=0;xlo=w;ylo=h;xhi=0;yhi=0
    while stack:
        q=stack.pop();y,x=divmod(q,w)
        count+=1;xlo=min(xlo,x);ylo=min(ylo,y);xhi=max(xhi,x);yhi=max(yhi,y)
        neighbours=[]
        if x>0:neighbours.append(q-1)
        if x<w-1:neighbours.append(q+1)
        if y>0:neighbours.append(q-w)
        if y<h-1:neighbours.append(q+w)
        for z in neighbours:
            if solid[z] and labels[z]==0:labels[z]=n;stack.append(z)
    cx=(xlo+xhi)/2;cy=(ylo+yhi)/2
    r=next((j for j in range(6) if row_edges[j]<=cy<row_edges[j+1]),5)
    c=next((j for j in range(6) if col_edges[r][j]<=cx<col_edges[r][j+1]),5)
    components.append({'label':n,'count':count,'box':[xlo,ylo,xhi+1,yhi+1],'owner':r*6+c})
labels=labels.reshape(h,w)
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
result=[]
for i,id in enumerate(ids):
    labs=[x['label'] for x in components if x['owner']==i]
    assert labs,id
    mask=np.isin(labels,labs).astype(np.uint8)*255
    # Four native pixels recover original antialiasing around each source contour.
    # Fill enclosed holes in the selection only: original PNG alpha is retained.
    maskim=Image.fromarray(mask).filter(ImageFilter.MaxFilter(9))
    exterior=maskim.copy()
    ImageDraw.floodfill(exterior,(0,0),128)
    mask=np.array(exterior)!=128
    # Avoid selecting a different foreground component inside a close overlapping bbox.
    other=(labels>0)&(~np.isin(labels,labs))
    mask[other]=False
    extracted=arr.copy();extracted[:,:,3]=np.where(mask,alpha,0)
    selected=Image.fromarray(extracted)
    bbox=selected.getbbox();assert bbox,id
    crop=selected.crop(bbox)
    assert crop.width<=240 and crop.height<=240,(id,crop.size)
    canvas=Image.new('RGBA',(256,256))
    offset=((256-crop.width)//2,(256-crop.height)//2)
    canvas.alpha_composite(crop,offset)
    p=OUT/(id+'.png');canvas.save(p)
    preserved=int(((alpha>=64)&np.isin(labels,labs)).sum())
    recovered=int((np.array(crop)[:,:,3]>=64).sum())
    assert recovered==preserved,(id,recovered,preserved)
    ent={'id':id,'file':p.relative_to(ROOT).as_posix(),'width':256,'height':256,'border':[0,0,0,0],
         'pivot':[.5,.5],'row':i//6+1,'column':i%6+1,'source':'source-art/cargo-icons.png',
         'sourceSha256':source_hash,'sourceGenerationRecord':'source-art/cargo-icons.png.generation.json',
         'cropXYXY':list(bbox),'nativeSubjectSize':[crop.width,crop.height],'pasteXY':list(offset),
         'operation':'native atlas alpha-component separation; original RGBA pixels retained within silhouette plus 4px antialias halo; enclosed selection holes filled; centered transparent padding; no resampling',
         'segmentation':{'solidAlphaThreshold':64,'selectionDilationPixels':4,'componentLabels':labs,
                         'preservedSourceSolidPixels':preserved,'outputSolidPixels':recovered},
         'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'alphaMin':0,'alphaMax':canvas.getchannel('A').getextrema()[1],
         'spriteType':'Single','resampling':False,'unityVerified':False}
    result.append(ent)
    record={'file':ent['file'],'sha256':ent['sha256'],'width':256,'height':256,'format':'PNG',
            'derivedFrom':{'file':ent['source'],'sha256':source_hash,'generationRecord':ent['sourceGenerationRecord']},
            'operation':ent['operation'],'cropXYXY':ent['cropXYXY'],'pasteXY':ent['pasteXY'],
            'actualModel':None,'actualQuality':None,'unverifiedReason':'Derived image: consult source generation receipt; no new AI call.'}
    p.with_name(p.name+'.generation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/asset-cargo-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'records/cargo-segmentation.json').write_text(json.dumps({'sourceSize':[w,h],'sourceSha256':source_hash,'rowBands':row_edges,'columnBandsPerRow':col_edges,'components':components},ensure_ascii=False,indent=2),encoding='utf-8')
contact=Image.new('RGB',(1200,1260),'#eff0e6');d=ImageDraw.Draw(contact)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for i,e in enumerate(result):
    icon=Image.open(ROOT/e['file']);icon.thumbnail((180,180))
    x=(i%6)*200;y=(i//6)*210
    contact.paste(icon,(x+(200-icon.width)//2,y),icon)
    text=e['id'];bb=d.textbbox((0,0),text,font=font)
    d.text((x+(200-(bb[2]-bb[0]))/2,y+184),text,fill='#173d32',font=font)
contact.save(ROOT/'previews/cargo-contact.png')
print('Exported 36 native 256x256 cargo assets; all source alpha>=64 silhouette pixels preserved.')

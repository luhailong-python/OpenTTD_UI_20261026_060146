"""Extract independent industry modules from generated atlases; no synthetic paintings.
Component ownership preserves every nonzero-alpha fragment by nearest substantial component.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json,hashlib,datetime,sys
import numpy as np
from scipy import ndimage
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def run(letter):
    source=R/'source-art/world'/('industry-'+letter+'.png')
    im=Image.open(source).convert('RGBA');a=np.array(im)[:,:,3]
    labels,n=ndimage.label(a>32);sizes=np.bincount(labels.ravel());large=np.where(sizes>15000)[0];large=large[large!=0]
    if len(large)!=9:raise ValueError('Expected 9 independent compound components; got '+str(len(large)))
    seeds=np.where(np.isin(labels,large),labels,0)
    # Distance transform is an ownership matte, not a largest-component discard.
    # Every alpha fragment is retained and assigned to its closest parent compound.
    inds=ndimage.distance_transform_edt(seeds==0,return_distances=False,return_indices=True)
    owned=seeds[tuple(inds)]
    boxes=[]
    for v in large:
        yy,xx=np.where(seeds==v);boxes.append((int(v),[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],float(xx.mean()),float(yy.mean())))
    boxes.sort(key=lambda b:b[3])
    rows=[sorted(boxes[r*3:r*3+3],key=lambda b:b[2]) for r in range(3)]
    boxes=sum(rows,[])
    start={'a':0,'b':9,'c':18,'d':27,'e':36}[letter]
    catalog=json.loads((R/'docs/WORLD_ASSET_COVERAGE.json').read_text(encoding='utf-8'))
    indsour=[x for x in catalog['items']if x['entryKind']=='source-industry-spec']
    extras=['mine-winding-wheel','pumpjack-beam','power-spark-rig','toy-press-head','plastic-jet','bubble-ring','toffee-drill','sugar-sieve']
    outentries=[]
    for i,(lab,bbox,cx,cy) in enumerate(boxes):
        idx=start+i
        ident=indsour[idx]['id'] if idx<37 else 'industry-machine-'+extras[idx-37]
        slug=ident.split('-',2)[2] if idx<37 else ident.removeprefix('industry-')
        mask=np.where((owned==lab)&(a>=8),a,0).astype('uint8')
        part=im.copy();part.putalpha(Image.fromarray(mask))
        box=part.getbbox();part=part.crop(box)
        scale=min(1,384/part.width,384/part.height)
        if scale<1:part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(512,512));off=(256-part.width//2,448-part.height);canvas.alpha_composite(part,off)
        p=R/'assets/world/industries'/(slug+'.png');p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and sha(p)!=hashlib.sha256(canvas.tobytes()).hexdigest():
            # Deterministic re-export is permitted, but never overwrite an independent native original.
            if not Path(str(p)+'.derivation.json').is_file():raise FileExistsError(p)
        canvas.save(p)
        entry={'id':ident,'file':p.relative_to(R).as_posix(),'sha256':sha(p),'canvas':[512,512],'sourceCropXYXY':list(box),'nativePaintingBounds':bbox,'uniformScale':scale,'pasteXY':list(off),'pivotPixel':[256,448],'pivotNormalized':[0.5,0.125],'groundAnchor':'bottom tip of whole compound footprint, fixed 256,448; Unity y origin bottom','alphaExtrema':list(canvas.getchannel('A').getextrema()),'alphaBBox':list(canvas.getbbox()),'operation':'connected-component ownership of separate painted compounds; nearest parent ownership; remove alpha below8/255 subvisible matte noise, preserve meaningful disconnected fragments; crop; proportional downscale only; transparent padding. No enlargement or new AI generation.','derivedFrom':{'file':source.relative_to(R).as_posix(),'sha256':sha(source),'record':source.relative_to(R).as_posix()+'.generation.json'},'sourceIndustryTypeId':idx if idx<37 else None,'artSource':'host_image_derivative','nativeImageCount':0,'validation':{'hasRealAlpha':canvas.getchannel('A').getextrema()==(0,255),'fitsCanvas':canvas.getbbox()[3]<=448,'visualStatus':'needs-review'},'unityStatus':'import suggestions only, not validated in Unity'}
        savej(Path(str(p)+'.derivation.json'),entry);outentries.append(entry)
    savej(R/'records/world-production'/('industry-'+letter+'-extraction.json'),{'source':str(source.relative_to(R)),'sourceSha256':sha(source),'size':list(im.size),'mainComponents':len(large),'algorithm':'alpha connected component nearest ownership; not erasing disconnected fragments','items':outentries})
    # Paired light/dark contact preview, labels outside the art.
    panel=Image.new('RGB',(1536,1728),'#e7e2d2');draw=ImageDraw.Draw(panel)
    font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),18)
    for i,en in enumerate(outentries):
        c=i%3;r=i//3;px=c*512;py=r*576
        bg=Image.new('RGBA',(512,512),'#e7e2d2'if (i%2)==0 else '#243c37')
        bg.alpha_composite(Image.open(R/en['file']).convert('RGBA'));panel.paste(bg.convert('RGB'),(px,py))
        text=(indsour[start+i]['name']if start+i<37 else extras[start+i-37])
        draw.text((px+18,py+520),en['id']+'  '+text,font=font,fill='#143b31')
    pp=R/'previews/world'/('industries-'+letter+'.jpg');pp.parent.mkdir(parents=True,exist_ok=True);panel.save(pp,quality=94)
    print(json.dumps({'atlas':letter,'native':list(im.size),'items':len(outentries),'preview':str(pp.relative_to(R))},ensure_ascii=False))
if __name__=='__main__':run(sys.argv[1])



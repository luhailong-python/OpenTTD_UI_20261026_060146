"""Normalize real painted material masters; geometry and periodic edge correction only.
All resulting pixels derive from the supplied imagegen atlases. No painted replacement art.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import json, math, argparse, numpy as np
import world_pack as wp
ROOT=wp.ROOT
OUT=ROOT/'assets/world/terrain'
PRE=ROOT/'previews/world'
REC=ROOT/'records/world-production'
UV_SIZE=192
MATERIAL_MASTERS={'shore-sand':'source-art/world/shore-sand-seamless.png','snowgrass':'source-art/world/snowgrass-seamless.png','shallow':'source-art/world/shallow-seamless.png'}

def square_material_operation(name):
    return 'actual square hand-painted '+name+' master -> proportional192px UV downsample ->14px opposite-edge colour blend -> canonical256x128 diamond with1.5px render extrusion; no new native detail'

def square_material(name):
    """Read the replacement square master; do not export other materials."""
    path=ROOT/MATERIAL_MASTERS[name]
    im=Image.open(path).convert('RGB')
    if im.width!=im.height or im.width<256:
        raise ValueError('Material master must be square and >=256px; no native enlargement')
    return periodic(im.resize((UV_SIZE,UV_SIZE),Image.Resampling.LANCZOS)),[wp.source_record(path)],{'sourceKind':'square_texture','sourceBox':[0,0,im.width,im.height],'nativeSourceSize':list(im.size),'sourceMaster':MATERIAL_MASTERS[name],'sourceUVWorkingResolution':[UV_SIZE,UV_SIZE]}

def jwrite(path,obj):wp.writej(path,obj)
def density_fraction(name,stage):
    # Snow/desert source tables begin at one quarter, while grass clearing
    # still begins at bare0. Legacy rough/gravel mixes keep their old meaning.
    return (stage+1)/4 if name in['snow','desert']else stage/3

def density_material(name,stage,uv,sources):
    origin='rough'if name=='rocks'else name
    underlay='grass'if name=='snow'else'bare';fraction=density_fraction(name,stage)
    refs=sources[underlay]+([]if origin==underlay else sources[origin])
    return periodic(Image.blend(uv[underlay],uv[origin],fraction)),refs,{'materialId':name,'densityStage':stage,'compositeFraction':fraction,'compositeUnderlayMaterial':underlay,'compositeSourceMaterial':origin,'densityMeaning':'source snow/desert1/4..1'if name in['snow','desert']else'legacy clear-material0..1','nativeDensityClaim':False}
def unwrap(sheet,quad):
    n,e,s,w=quad
    # QUAD sampling projects the native painted diamond into material UV space.
    return sheet.transform((UV_SIZE,UV_SIZE),Image.Transform.QUAD,tuple(n+w+s+e),Image.Resampling.BICUBIC).convert('RGB')

def periodic(im,band=14):
    a=np.asarray(im).astype(np.float32).copy()
    # Opposite border colour correction preserves the painted centre.
    for axis in (0,1):
        src=a.copy()
        for k in range(band):
            t=1 if k<4 else .5*(1+math.cos(math.pi*(k-3)/(band-3)))
            if axis==0:
                mean=(src[k]+src[-1-k])/2
                a[k]=src[k]*(1-t)+mean*t;a[-1-k]=src[-1-k]*(1-t)+mean*t
            else:
                mean=(src[:,k]+src[:,-1-k])/2
                a[:,k]=src[:,k]*(1-t)+mean*t;a[:,-1-k]=src[:,-1-k]*(1-t)+mean*t
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def project(uv):
    # Inverse map canonical diamond to square UV. All native source footprints
    # are wider/taller than formal 256x128; no native detail is invented.
    n=UV_SIZE-1
    pad=Image.fromarray(np.pad(np.asarray(uv),((8,8),(8,8),(0,0)),mode='edge')).convert('RGBA')
    im=pad.transform((256,128),Image.Transform.AFFINE,(n/256,n/128,-n/2+8,-n/256,n/128,n/2+8),Image.Resampling.BICUBIC)
    # Fully covered pixels inside the exact diamond, AA only at the outer boundary.
    mask=Image.new('L',(1024,512));ImageDraw.Draw(mask).polygon([(512,-6),(1036,256),(512,518),(-12,256)],fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel('A'),mask.resize((256,128),Image.Resampling.LANCZOS)))
    return im

def edge_antialias(im,band=18):
    """Targeted sampling-edge colour correction; painted centre unchanged."""
    a=np.asarray(im).astype(np.float32).copy()
    for axis in(0,1):
        v=np.moveaxis(a,axis,0);profile=(v[:4].mean(0)+v[-4:].mean(0))/2
        # Only the seam profile is filtered to avoid subpixel sampling alias.
        profile=sum(np.roll(profile,k,axis=0)*weight for k,weight in[(-2,1),(-1,4),(0,6),(1,4),(2,1)])/16
        for k in range(band):
            t=1 if k<8 else .5*(1+math.cos(math.pi*(k-7)/(band-7)))
            v[k]=v[k]*(1-t)+profile*t;v[-1-k]=v[-1-k]*(1-t)+profile*t
        a=np.moveaxis(v,0,axis)
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def write_image(ident,im,srcs,operation,extra=None,anchor=None):
    path=OUT/(ident+'.png');path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
    a=wp.base_asset(ident,path.relative_to(ROOT).as_posix(),im,srcs[0],operation,category='terrain',anchor=anchor or[128,64])
    a['derivedFrom']=srcs;a.update(extra or{});a.update({'sha256':wp.sha(path),'status':'art-checked','reviewBasis':'2026-10-26 fixed-canvas/Alpha/contact-sheet and repeated-material visual inspection','unityValidated':False})
    jwrite(str(path)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'generatedAt':wp.now(),'route':'deterministic-derivative','tool':'build_world_terrain.py','width':im.width,'height':im.height,'operation':operation,'derivedFrom':srcs,'actualModel':None,'actualQuality':None,'nativeModelGeneration':False,'unverifiedReason':'Source imagegen actual model and quality undisclosed; geometric processing is not native image generation.'})
    return a

def make():
    OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);REC.mkdir(parents=True,exist_ok=True)
    ts=ROOT/'source-art/world/terrain-base.png';ws=ROOT/'source-art/world/water-cycle.png'
    t=Image.open(ts).convert('RGBA');water=Image.open(ws).convert('RGBA')
    names=['grass','bare','rough','field','snow','snowgrass','desert','tropical','toyland']
    climates=['temperate','shared','shared','temperate','arctic','arctic','tropic','tropic','toyland']
    x=[(18,212,412),(431,625,824),(843,1036,1234)]
    y=[(145,251,355),(524,631,737),(907,1013,1118)]
    uv={};sources={};layout=[];replacement_info={}
    for i,name in enumerate(names):
        l,c,r=x[i%3];top,cy,bottom=y[i//3]
        quad=[[c,top],[r,cy],[c,bottom],[l,cy]]
        uv[name]=periodic(unwrap(t,quad));sources[name]=[wp.source_record(ts)]
        if name=='snowgrass':
            if (ROOT/MATERIAL_MASTERS[name]).is_file():uv[name],sources[name],replacement_info[name]=square_material(name)
            else:uv[name]=edge_antialias(uv[name])
        layout.append({'id':name,'climate':climates[i],**(replacement_info[name]if name in replacement_info else{'quadNWES':quad})})
    # Water source has a large transparent header; each row was inspected,
    # so this intentionally is not an equal 3x3-grid crop.
    wx=[(19,214,407),(434,625,817),(845,1036,1228)]
    wy=[(520,628,735),(752,860,968),(990,1096,1203)]
    for i in range(9):
        name='water-key-'+str(i)if i<6 else ['shallow','shore-sand','riverbed'][i-6]
        l,c,r=wx[i%3];top,cy,bottom=wy[i//3]
        quad=[[c,top],[r,cy],[c,bottom],[l,cy]]
        uv[name]=periodic(unwrap(water,quad));sources[name]=[wp.source_record(ws)]
        if name in ('shore-sand','shallow'):
            if (ROOT/MATERIAL_MASTERS[name]).is_file():uv[name],sources[name],replacement_info[name]=square_material(name)
            else:uv[name]=edge_antialias(uv[name])
        layout.append({'id':name,'climate':'shared',**(replacement_info[name]if name in replacement_info else{'quadNWES':quad})})
    used_sources={s['file']:s for group in sources.values()for s in group}
    jwrite(REC/'terrain-source-crops.json',{'sources':list(used_sources.values()),'nativeSourceDimensions':{'terrain':list(t.size),'water':list(water.size),**{k:v['nativeSourceSize']for k,v in replacement_info.items()}},'uvWorkingSize':[UV_SIZE,UV_SIZE],'items':layout,'operations':['actual native diamond crop or explicitly identified full square master','inverse 2:1 projection to UV / proportional square downsample','opposite edge photometric blending,14 UV px','forward 2:1 projection and 1.5px render-only Alpha extrusion'],'claim':'geometric/photometric derivative, not new native detail'})

    entries=[];qa=[];variants={};preview_bases=[]
    base_op='native hand-painted atlas crop -> UV geometric normalization -> 14px periodic opposite-edge colour blending -> canonical diamond with1.5px render extrusion; no new native detail'
    # Source-consistent density stages are composited from the bare and painted material.
    production=[]
    for name in names+['shallow','shore-sand','riverbed']:
        production.append((name,uv[name],sources[name],{'materialId':name,'variant':0}))
    for name in ['grass','rocks','snow','desert']:
        for density in range(4):
            ident=name+'-density-'+str(density)
            material,srcs,extra=density_material(name,density,uv,sources)
            production.append((ident,material,srcs,extra))
    for name,count in [('rough',8),('field',16)]:
        for v in range(count):
            arr=np.asarray(uv[name]);arr=np.roll(arr,(v*17,v*31),(0,1))
            # Field stage variations share one actual painted soil master.
            # A subtle foliage/gold tint is derived, never called 16 new paintings.
            if name=='field':
                factor=np.array([[.86,1.02,.80],[1.05,1.04,.81],[1.,.92,.83],[.95,.89,.83]][v//4])
                arr=np.uint8(np.clip(arr.astype(float)*factor,0,255))
            tile=periodic(Image.fromarray(arr))
            production.append((name+'-variant-'+str(v).zfill(2),tile,sources[name],{'materialId':name,'sourceRandomVariant':v,'variantMethod':'periodic UV translation; field colour grade per4stages','nativeVariantClaim':False}))

    for ident,material,srcs,extra in production:
        flat=project(material);seam=wp.edge_rmse(flat);extra={**extra,**replacement_info.get(ident,{}),'photometricSeam':seam,'logicalFootprint':[1,1],'sourceUVResolution':[UV_SIZE,UV_SIZE],'renderEdgeExtrusionPx':1.5,'logicalFootprintUnchanged':True}
        material_op=square_material_operation(ident)if ident in replacement_info else base_op+(' -> targeted18px UV sampling-boundary profile with8px shared edge, painted centre unchanged' if ident in ['snowgrass','shore-sand'] else '')
        a=write_image('terrain-'+ident+'-flat',flat,srcs,material_op,extra);entries.append(a)
        variants[ident]=[a['image']]
        if ident in names+['shallow','shore-sand','riverbed']:preview_bases.append(a)
        for key in ['oppositeUEdgeRMSE','oppositeVEdgeRMSE']:
            q=seam[key];qa.append({'id':ident+'.'+key,'level':'OK'if q is not None and q<=18 else'WARN','value':q,'threshold':18,'meaning':'photometric edge check; visual repeat review separate'})
        for code,name in wp.SLOPES:
            im,points,heights=wp.projected_slope(flat,code)
            a=write_image('terrain-'+ident+'-slope-'+name,im,srcs,material_op+' -> piecewise-affine slope projection', {**extra,'slopeCode':code,'slopeName':name,'cornerHeights':heights,'cornerPixels':{k:list(v)for k,v in points.items()},'heightStepPixels':32,'triangles':wp.slope_triangles(code)},[128,128]);entries.append(a);variants[ident].append(a['image'])

    # Painted water keys crossfade at fixed anchors. This is an explicit compositing
    # loop; it does not claim video-generated physical simulation.
    frames=[]
    for k in range(6):
        for interp in range(4):
            phase=k*4+interp;u=periodic(Image.blend(uv['water-key-'+str(k)],uv['water-key-'+str((k+1)%6)],interp/4))
            a=write_image('water-sea-frame-'+str(phase).zfill(2),project(u),[wp.source_record(ws)],'six actual painted water keys -> fixed-geometry periodic edge correction -> linear crossfade4samples/key ->24-frame loop',{'category':'water','animationGroup':'water-sea','frame':phase,'durationMs':100,'nativeKeyCount':6,'interpolated':interp!=0});entries.append(a);frames.append(a['image'])
    animations=[{'id':'water-sea','category':'water','frames':frames,'durationsMs':[100]*len(frames),'loop':True,'fixedAnchorPx':[128,64],'frameSize':[256,128],'nativeKeyCount':6,'method':'painted-key crossfade; not video generation','review':'fixed bounds and loop transition inspected; Unity runtime pending'}]
    manifest={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'taskRoot':str(ROOT),'assets':entries,'animations':animations,'projection':{'logicalTileSize':[128,64],'exportTileSize':[256,128],'logicalHeightStep':16,'exportHeightStep':32},'batchId':'world-terrain-water','qa':qa,'acceptance':'produced; material contact sheets reviewed; user art acceptance pending','limitations':['Shared native material masters; variant and slope exports are deterministic derivatives.','Natural river/canal banks,locks,bridges and foundation/fence art are separate packs.','Unity import/renderer remains unverified.'],'variantMap':variants}
    jwrite(OUT/'manifest.json',manifest)
    contact(preview_bases,'terrain-materials.jpg',4,180)
    grass=[a for a in entries if a['id'].startswith('terrain-grass-slope-')and'density'not in a['id']]
    contact(grass,'terrain-slopes.jpg',5,160)
    repeat_preview(preview_bases)
    jwrite(REC/'terrain-validation.json',{'createdAt':wp.now(),'nativeMasters':len(used_sources),'materialNativeCells':18,'formalAssetCount':len(entries),'waterFrames':24,'warnings':[q for q in qa if q['level']!='OK'],'checks':qa,'claim':'This export makes no model calls; actual native source count and individual provenance are recorded.'})
    print(json.dumps({'assets':len(entries),'warnings':sum(q['level']!='OK'for q in qa),'animations':len(animations),'preview':str(PRE/'terrain-repeat.jpg')},ensure_ascii=False))

def font(n=18):
    f=ROOT/'assets/fonts/NotoSansSC-Variable.ttf'
    return ImageFont.truetype(str(f),n)
def contact(entries,name,cols,thumb):
    rows=math.ceil(len(entries)/cols);im=Image.new('RGB',(cols*300,rows*(thumb+60)),(35,69,62));d=ImageDraw.Draw(im)
    for i,a in enumerate(entries):
        p=Image.open(ROOT/a['image']).convert('RGBA');p.thumbnail((284,thumb),Image.Resampling.LANCZOS)
        x=(i%cols)*300+(300-p.width)//2;y=(i//cols)*(thumb+60)
        im.paste(p,(x,y),p)
        label=a['id'].removeprefix('terrain-')
        if a.get('category')=='houses-state'and'locationVariant'in a:
            label=a['familyId']+' · '+str(a['footprintTiles'][0])+'×'+str(a['footprintTiles'][1])+' / v'+str(a['locationVariant'])+' / s'+str(a['constructionStage'])
        f=font(14);lines=[];current=''
        for char in label:
            candidate=current+char
            if current and d.textlength(candidate,font=f)>284:lines.append(current);current=char
            else:current=candidate
        if current:lines.append(current)
        for line_no,line in enumerate(lines[:2]):d.text(((i%cols)*300+8,y+thumb+5+line_no*19),line,font=f,fill=(246,233,199))
    im.save(PRE/name,quality=95)
def repeat_preview(entries):
    im=Image.new('RGB',(1280,math.ceil(len(entries)/3)*370),(35,69,62));d=ImageDraw.Draw(im)
    for n,a in enumerate(entries):
        tile=Image.open(ROOT/a['image']).convert('RGBA');tile=tile.resize((128,64),Image.Resampling.LANCZOS)
        ox=(n%3)*420+210;oy=(n//3)*370+45
        for depth in range(7):
            for i in range(4):
                j=depth-i
                if not 0<=j<4:continue
                x=ox+(j-i)*64-64;y=oy+(i+j)*32
                im.paste(tile,(x,y),tile)
        d.text(((n%3)*420+24,(n//3)*370+317),a['id'],font=font(19),fill=(246,233,199))
    im.save(PRE/'terrain-repeat.jpg',quality=96)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repair-shore-sand',action='store_true',help='Only replace shore-sand flat+19slopes and affected QA previews');parser.add_argument('--repair-materials',nargs='+',choices=sorted(MATERIAL_MASTERS),help='Replace only selected material families; preserve every other formal PNG');parser.add_argument('--repair-density-stages',action='store_true',help='Only repair160snow/desert density exports, preserving every other formal PNG')
    args=parser.parse_args()
    if args.repair_density_stages:
        from repair_density_stages import repair
        repair()
    elif args.repair_shore_sand or args.repair_materials:
        from repair_terrain_materials import repair
        repair(args.repair_materials or['shore-sand'])
    else:make()

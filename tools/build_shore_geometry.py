"""Reconstruct legal shore geometry from source heights and existing painted pixels.

Masks and projection are geometry, never replacement painted shore art.  The
upstream code selects external base sprites; it does not publish their pixel
masks.  Our explicit reconstruction is therefore not claimed as an OpenGFX mask.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, re, math, json
import world_pack as wp
import build_world_terrain as terrain

R=wp.ROOT
OUT=R/'assets/world/terrain/shore-geometry'
PRE=R/'previews/world/shore-geometry'
REC=R/'records/world-production'
CANVAS=(256,192);ANCHOR=[128,128];SS=3
ROCK_CONTACTS=[(4,4),(4,11),(11,9)]
CLIMATES=['grass','sand','snow']
MATERIALS={'grass':'terrain-grass-flat','sand':'terrain-shore-sand-flat','snow':'terrain-snow-flat'}
SOURCES=['reference/OpenTTD/src/water_cmd.cpp','reference/OpenTTD/src/landscape.cpp','reference/OpenTTD/src/slope_type.h','reference/OpenTTD/src/table/sprites.h']


def source(file):
    p=R/file
    record=file+('.generation.json'if (R/(file+'.generation.json')).is_file()else'.derivation.json')
    return {'file':file,'sha256':wp.sha(p),'record':record if(R/record).is_file()else None}


def source_height(x,y,code):
    # Independent direct transcription of landscape.cpp GetPartialPixelZ.
    # Domain vertices include16 only to close the shared tile boundary.
    if code==0:return 0
    if code==8:return(16-x-y)>>1 if x+y<=16 else 0
    if code==4:return(1+y-x)>>1 if y>=x else 0
    if code==2:return(1+x+y-16)>>1 if x+y>=16 else 0
    if code==1:return(x-y)>>1 if x>=y else 0
    if code==12:return(16-x)>>1
    if code==6:return(y+1)>>1
    if code==3:return(x+1)>>1
    if code==9:return(16-y)>>1
    if code==13:return 8-((1+x+y-16)>>1)if x+y>=16 else 8
    if code==14:return 8-((x-y)>>1)if y<x else 8
    if code==7:return 8-((16-x-y)>>1)if x+y<=16 else 8
    if code==11:return 8-((1+y-x)>>1)if x<y else 8
    if code==10:return(16-x-y)>>1 if x+y<16 else(1+x+y-16)>>1
    if code==5:return(x-y)>>1 if x>=y else(1+y-x)>>1
    if code==29:return(32-x-y)>>1
    if code==30:return(17+y-x)>>1
    if code==23:return(1+x+y)>>1
    if code==27:return(16+x-y)>>1
    raise ValueError(code)


def source_table():
    txt=(R/SOURCES[0]).read_text(encoding='utf-8')
    body=re.search(r'tileh_to_shoresprite\s*=\s*\{([^}]+)',txt,re.S).group(1)
    slots=list(map(int,re.findall(r'\b\d+\b',body)))
    legal={c:slots[c]for c,_ in wp.SLOPES if c not in[0,5,10]}
    if len(legal)!=16 or set(legal.values())!=set(range(16)):raise ValueError('Upstream shore index contract changed')
    return slots,legal


def project(x,y,z):return(128+(y-x)*8,64+(x+y)*4-z*4)


def continuous_height(x,y,code):
    return {1:max(x-y,0)/2,2:max(x+y-16,0)/2,3:x/2,4:max(y-x,0)/2,6:y/2,7:8-max(16-x-y,0)/2,8:max(16-x-y,0)/2,9:(16-y)/2,11:8-max(y-x,0)/2,12:(16-x)/2,13:8-max(x+y-16,0)/2,14:8-max(x-y,0)/2,23:(x+y)/2,27:(16+x-y)/2,29:(32-x-y)/2,30:(16+y-x)/2}[code]


def mesh(code):
    # Split cells on the source corner crease, then interpolate the INTEGER
    # source heights.  Every integer rock contact lies exactly on this mesh.
    vertices=[]
    for y in range(17):
        for x in range(17):
            exact=source_height(x,y,code);boundary=x in[0,16]or y in[0,16];continuous=continuous_height(x,y,code)
            # Integer floor creates a one-unit-wide zero strip on some
            # uphill faces. It is a collision sample, not a new sea inlet.
            # Keep the native continuous zero contour, while interior rock
            # contacts with positive source height retain the exact sample.
            contact=(x,y)in ROCK_CONTACTS;contour=exact==0 and continuous>0 and not contact
            render=continuous if boundary or contour else exact
            vertices.append({'sourceXY':[x,y],'sourceZ':exact,'renderZ':render,'boundaryContinuous':boundary,'shoreContourContinuous':contour,'wetRockContactExact':contact,'screenPx':list(project(x,y,render))})
    tris=[]
    for y in range(16):
        for x in range(16):
            n=y*17+x;e=n+1;w=n+17;s=w+1
            # A cell crossed by x+y=16 must use that diagonal. The other
            # diagonal preserves x=y; elsewhere either is planar.
            if x+y==15:tris.extend([(n,e,w),(e,s,w)])
            else:tris.extend([(n,e,s),(n,s,w)])
    return vertices,tris


def raster(code):
    vertices,tris=mesh(code);h,w=CANVAS[1]*SS,CANVAS[0]*SS
    xx=np.full((h,w),np.nan);yy=xx.copy();zz=xx.copy()
    for inds in tris:
        ps=np.array([vertices[i]['screenPx']for i in inds],float)*SS
        uv=np.array([vertices[i]['sourceXY']for i in inds],float)
        zs=np.array([vertices[i]['renderZ']for i in inds],float)
        x0=max(0,int(np.floor(ps[:,0].min())));x1=min(w,int(np.ceil(ps[:,0].max())))
        y0=max(0,int(np.floor(ps[:,1].min())));y1=min(h,int(np.ceil(ps[:,1].max())))
        gy,gx=np.mgrid[y0:y1,x0:x1];gx=gx+.5;gy=gy+.5
        a,b,c=ps;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        # Integer-height rounding can collapse an uphill microtriangle in
        # this view (zero projected area). Its shared edge remains exact.
        if abs(den)<1e-10:continue
        wa=((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/den
        wb=((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/den;wc=1-wa-wb
        owned=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)
        for target,values in[(xx,uv[:,0]),(yy,uv[:,1]),(zz,zs)]:
            patch=target[y0:y1,x0:x1];inter=wa*values[0]+wb*values[1]+wc*values[2];patch[owned]=inter[owned]
    return xx,yy,zz,vertices,tris


def bilinear(im,x,y):
    a=np.asarray(im.convert('RGBA'),float);x=np.clip(np.nan_to_num(x),0,im.width-1);y=np.clip(np.nan_to_num(y),0,im.height-1)
    x0=x.astype(int);y0=y.astype(int);x1=np.minimum(x0+1,im.width-1);y1=np.minimum(y0+1,im.height-1)
    fx=(x-x0)[...,None];fy=(y-y0)[...,None]
    return(a[y0,x0]*(1-fx)*(1-fy)+a[y0,x1]*fx*(1-fy)+a[y1,x0]*(1-fx)*fy+a[y1,x1]*fx*fy)


def flat_pixels(im,x,y):return bilinear(im,128+(y-x)*8,(x+y)*4)


def encode(rgb,alpha):
    # Premultiplied downsample avoids coloured fringes around geometric masks.
    a=np.clip(np.nan_to_num(alpha),0,1);rgb=np.nan_to_num(rgb[...,:3]);out=[]
    for k in range(3):out.append(np.asarray(Image.fromarray(np.float32(rgb[...,k]*a),mode='F').resize(CANVAS,Image.Resampling.BOX)))
    aa=np.asarray(Image.fromarray(np.float32(a),mode='F').resize(CANVAS,Image.Resampling.BOX))
    ar=np.zeros((CANVAS[1],CANVAS[0],4),np.uint8)
    for k in range(3):ar[...,k]=np.uint8(np.clip(np.divide(out[k],aa,out=np.zeros_like(aa),where=aa>0),0,255))
    ar[...,3]=np.uint8(np.clip(np.rint(aa*255),0,255));ar[ar[...,3]==0,:3]=0
    return Image.fromarray(ar)


def bank_coordinates(code,x,y):
    # Signed distance/tangent on the actual zero-height contour.  Single
    # corners have an internal coast; other slopes reach water at an outside
    # edge/corner and are DryOut in the upstream flooding state machine.
    if code==1:return(x-y)/math.sqrt(2),(x+y)/32
    if code==2:return(x+y-16)/math.sqrt(2),(y-x+16)/32
    if code==4:return(y-x)/math.sqrt(2),(x+y)/32
    if code==8:return(16-x-y)/math.sqrt(2),(y-x+16)/32
    if code==3:return x,y/16
    if code==6:return y,x/16
    if code==9:return 16-y,x/16
    if code==12:return 16-x,y/16
    low={7:(0,0),11:(0,16),13:(16,16),14:(16,0),23:(0,0),27:(0,16),29:(16,16),30:(16,0)}[code]
    dx=x-low[0];dy=y-low[1]
    return np.hypot(dx,dy),(np.arctan2(np.abs(dy),np.abs(dx))/(math.pi/2))


def bank_pixels(climate,code,x,y):
    d,t=bank_coordinates(code,x,y);t=np.clip(t,0,1)
    if climate=='grass':
        file='assets/world/infrastructure/fences-shore/river-grass-bank.png'
        a=np.array([105.,405.]);b=np.array([466.,219.]);side=-1.;width=15.
    else:
        file='assets/world/infrastructure/fences-shore/shore-sand.png'
        a=np.array([91.,359.]);b=np.array([420.,190.]);side=1.;width=13.
    native=Image.open(R/file).convert('RGBA');normal=np.array([-(b-a)[1],(b-a)[0]]);normal/=np.linalg.norm(normal)
    # d spans1.5world units either side (~12formal px); existing native
    # cross-shore paint is sampled, no procedural white foam/green bank.
    cross=np.clip(d/1.5,-1,1)*width*side
    sx=a[0]+t*(b-a)[0]+cross*normal[0];sy=a[1]+t*(b-a)[1]+cross*normal[1]
    paint=bilinear(native,sx,sy);alpha=np.clip((1.6-np.abs(d))/.65,0,1)*(paint[...,3]/255)
    if climate=='snow':
        # Reuse only native water-side foam; preserve actual snow land RGB.
        alpha*=np.clip((.15-d)/.7,0,1)
    return paint,alpha,file


def emit(aid,im,refs,operation,extra):
    path=OUT/(aid+'.png');im.save(path)
    a=wp.base_asset(aid,wp.rel(path),im,refs[0],operation,'shore-geometry',ANCHOR)
    a.update(extra);a.update({'derivedFrom':refs,'sha256':wp.sha(path),'status':'produced-needs-visual-review','sourceRequirementIds':['water-shore'],'authoritative':True})
    wp.writej(str(path)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'generatedAt':wp.now(),'tool':'build_shore_geometry.py','route':'deterministic-native-pixel-projection','width':im.width,'height':im.height,'derivedFrom':refs,'operation':operation,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None})
    return a


def contact(entries,climate):
    pages=[]
    for start in range(0,len(entries),8):
        sub=entries[start:start+8];im=Image.new('RGB',(1280,620),'#253a43');d=ImageDraw.Draw(im)
        for i,s in enumerate(sub):
            x=i%4*320+32;y=i//4*310+12;tile=Image.open(R/s['whole']).convert('RGBA');im.paste(tile,(x,y),tile)
            d.text((x,y+202),f"{climate} slot{s['sourceShoreIndex']:02} / slope{s['sourceSlopeCode']}",font=terrain.font(17),fill='#f3e3bd')
            d.text((x,y+230),s['sourceFloodingBehaviour']+' / '+s['waterAreaKind'],font=terrain.font(12),fill='#bedbd7')
        p=PRE/f'{climate}-postures-{start//8+1}.jpg';im.save(p,quality=97)
        wp.writej(str(p)+'.derivation.json',{'file':wp.rel(p),'sha256':wp.sha(p),'operation':'Actual formal shorewhole PNGs on inspection matte with labels only','derivedFrom':[source(s['whole'])for s in sub],'nativeModelGeneration':False})
        pages.append({'file':wp.rel(p),'sha256':wp.sha(p),'sampleCount':len(sub),'sourceShoreIndices':[s['sourceShoreIndex']for s in sub]})
    return pages


def main():
    OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);REC.mkdir(parents=True,exist_ok=True)
    table,legal=source_table();entries=[];states=[];geometries=[];waterfile='assets/world/terrain/water-sea-frame-00.png';water=Image.open(R/waterfile).convert('RGBA')
    for code,slot in sorted(legal.items(),key=lambda q:q[1]):
        x,y,z,vertices,tris=raster(code);valid=np.isfinite(z);wet=valid&(np.nan_to_num(z)<=1e-8);land=valid&~wet
        waterim=encode(flat_pixels(water,x,y),wet.astype(float));wa=None
        if waterim.getchannel('A').getbbox():
            wa=emit(f'shore-water-slot-{slot:02}',waterim,[source(waterfile)],'Native painted sea sampled in worldUV; mask restricted to GetPartialPixelZ zero-height mesh region; every visible water pixel stays z=0',{'shoreLayer':'water','sourceShoreIndex':slot,'sourceSlopeCode':code,'slopeCode':code,'shoreClimates':CLIMATES,'waterLevelSourceZ':0})
            entries.append(wa)
        zeroarea=sum(.5 for a,b,c in tris if all(vertices[i]['renderZ']==0 for i in[a,b,c]))
        geometries.append({'sourceShoreIndex':slot,'sourceSlopeCode':code,'vertices':vertices,'triangles':tris,'zeroHeightWorldArea':float(zeroarea),'worldTileArea':256,'waterHasPositiveArea':wa is not None,'interpolation':'piecewise affine through integer interior GetPartialPixelZ samples; continuous source outer boundary and zero-height shoreline contour prevent4px edge serration; all3actual wet-rock contacts exact; no full-tile flat water backing'})
        for climate in CLIMATES:
            landfile='assets/world/terrain/'+MATERIALS[climate]+'.png';native=Image.open(R/landfile).convert('RGBA')
            li=encode(flat_pixels(native,x,y),land.astype(float));bp,ba,bankfile=bank_pixels(climate,code,x,y);bi=encode(bp,ba*valid)
            common={'sourceShoreIndex':slot,'sourceSlopeCode':code,'slopeCode':code,'shoreSlopeCode':code,'shoreClimate':climate,'heightScalePixelsPerSourceUnit':4}
            la=emit(f'shore-{climate}-slot-{slot:02}-land',li,[source(landfile)],'Native grass/sand/snow pixels sampled in worldUV and projected on integer-source-height mesh; positive-height land only',dict(common,shoreLayer='land'));entries.append(la)
            bank=emit(f'shore-{climate}-slot-{slot:02}-bank',bi,[source(bankfile)],'Native painted cross-shore strip sampled onto actual zero-height interface and the adjacent slope; Alpha-only ribbon mask, no code-painted bank/foam; snow retains only water-side native foam',dict(common,shoreLayer='bank'));entries.append(bank)
            whole=Image.new('RGBA',CANVAS)
            if wa:whole.alpha_composite(waterim)
            whole.alpha_composite(li);whole.alpha_composite(bi)
            layers={'water':wa['image']if wa else None,'land':la['image'],'bank':bank['image']};refs=[source(f)for f in layers.values()if f]
            a=emit(f'shore-{climate}-slot-{slot:02}-whole',whole,refs,'Exact ordered composition: horizontal native water, source-height native land, source-height native shorestrip',dict(common,shoreLayer='whole',layers=layers,layerOrder=['water','land','bank']));entries.append(a)
            states.append({**common,'whole':a['image'],'image':a['image'],'water':layers['water'],'land':layers['land'],'bank':layers['bank'],'layers':layers,'layerOrder':['water','land','bank'],'sourceFloodingBehaviour':'Active'if code in[1,2,4,8]else'DryOut','waterAreaKind':'low-half'if code in[1,2,4,8]else('edge/corner only'if wa else'zero-area contact only'),'waterHasPositiveArea':wa is not None,'waterAbsentReason':None if wa else'The source integer-height mesh has no positive-area zero-height face; this legal DryOut coast touches the water plane only at the low corner. No fake water triangle is exported.'})
    reserved=[{'sourceShoreIndex':slot,'sourceSlopeCode':code,'shoreClimate':climate,'applicable':False,'noDraw':True,'image':None,'reason':'DrawShoreTile explicitly asserts slope != SLOPE_EW/NS; slots are reserved by the table but unreachable for current flooding behaviour.'}for slot,code in[(16,5),(17,10)]for climate in CLIMATES]
    pages=[]
    for climate in CLIMATES:pages+=contact([s for s in states if s['shoreClimate']==climate],climate)
    mapping={'requirementId':'water-shore','files':[s['whole']for s in states],'sourceShoreSpriteIndices':list(range(18)),'climates':CLIMATES,'sourceLegalSlopeCodes':sorted(legal),'sourceValidSpriteIndices':list(range(16)),'states':states,'reservedBindings':reserved,'validPostureClimateCombinations':48,'reservedPostureClimateCombinations':6,'legacyReferencePack':'assets/world/infrastructure/water-states/manifest.json','legacyFlatShoreAuthoritative':False}
    manifest={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'batchId':'source-height-shore-geometry','assets':entries,'animations':[],'coverageMappings':[mapping],'geometry':{'canvas':list(CANVAS),'anchorPx':ANCHOR,'heightScalePixelsPerSourceUnit':4,'sourceTileSize':16,'waterSourceHeight':0,'sourceContactRule':'screenX=128+(y-x)*8; screenY=64+(x+y)*4-GetPartialPixelZ(x,y,slope)*4','rockCanvasAlignment':{'rockCanvas':[256,256],'rockAnchorPx':[128,192],'shoreOffsetPx':[0,64]},'meshResolution':[17,17],'meshPolicy':'Source integer interior samples interpolated piecewise; all3actual wet-rock interior contacts per slope match source exactly. Outer boundary and zero-height contour vertices use the continuous source slope before integer rounding to keep terrain outlines and water interface straight. Water faces are zero-height only.','maskProvenance':'Reconstruction from source height geometry. Upstream DrawShoreTile selects external painted sprites and provides no independent pixel mask; no claim to duplicate an upstream artwork mask.','sourceSlopeToShoreTable':table,'postures':geometries},'sourceFiles':[source(f)for f in SOURCES],'contactPages':pages,'acceptance':'produced; actual-pixel visual and geometry QA pending','userAccepted':False,'unityValidated':False,'limitations':['Three existing native climate materials and two painted bank strips are geometrically reused; no new original shore painting.','Static sea frame00 is an art preview/reference. Dynamic water must retain this exact shoreline mask and horizontal projection.','Multi-corner and steep shores are source-legal DryOut transients; small/zero water coverage is explicit, not an invented broad pool.','Flat/EW/NS and half-tile foundation shores are excluded from this full-tile DrawShoreTile contract. Half-tile water remains a separate foundation/rail composition.']}
    wp.writej(OUT/'manifest.json',manifest)
    wp.writej(REC/'shore-geometry-source-contract.json',{'createdAt':wp.now(),'manifest':wp.rel(OUT/'manifest.json'),'sourceFiles':manifest['sourceFiles'],'sourceSlopeToShoreTable':table,'validStates':48,'reservedStates':reserved,'sourceMaskClaim':manifest['geometry']['maskProvenance']})
    html='<!doctype html><meta charset="utf-8"><title>Shore geometry inspection</title><style>body{background:#253a43;color:#f3e3bd;font:18px sans-serif}img{display:block;max-width:100%;margin:20px 0}</style><h1>Source-height shore geometry</h1><p>48 actual assemblies: 16 legal source slots × 3 climates. Slots16/EW and17/NS are source-prohibited, with no placeholder PNG. Water horizontal, land source-height. Static art inspection; Unity unverified.</p>'
    for p in pages:html+='<img src="'+Path(p['file']).name+'" alt="'+Path(p['file']).stem+'">'
    html+='<h2>Reserved source slots: no draw</h2><table><tr><th>Climate</th><th>Slot</th><th>Slope</th><th>Applicability</th></tr>'
    for s in reserved:html+=f"<tr><td>{s['shoreClimate']}</td><td>{s['sourceShoreIndex']}</td><td>{s['sourceSlopeCode']}</td><td>source assertion prohibits drawing; no PNG</td></tr>"
    html+='</table><p>Flat and half-tile slopes are outside this full-tile shore draw contract. Multi-corner/steep source-legal coast is DryOut, so no broad water pool is fabricated.</p>'
    (PRE/'index.html').write_text(html,encoding='utf-8')
    print(json.dumps({'assets':len(entries),'states':len(states),'reserved':len(reserved),'pages':len(pages),'manifestSHA256':wp.sha(OUT/'manifest.json')}))


if __name__=='__main__':main()

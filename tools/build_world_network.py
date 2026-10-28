"""Extract painted road network; functional junctions are explicit module compositions."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,math,numpy as np
import world_pack as wp
import build_world_terrain as terrain
ROOT=wp.ROOT
OUT=ROOT/'assets/world/infrastructure/roads'
PRE=ROOT/'previews/world'
UV=terrain.UV_SIZE
PORT_NAMES=['NW','NE','SE','SW']
PORT_POINTS=[(64,32),(192,32),(192,96),(64,96)]

def native_road_uv(sheet,i):
    cx=[198,580,962,1347][i%4]
    cy=[120,366,608,845][i//4]
    # Actual diamond perimeter inspected against the native 1536x1024 sheet.
    quad=[[cx,cy-82],[cx+160,cy],[cx,cy+80],[cx-160,cy]]
    n,e,s,w=quad
    raw=sheet.transform((UV,UV),Image.Transform.QUAD,tuple(n+w+s+e),Image.Resampling.BICUBIC).convert('RGBA')
    # Preserve the atlas Alpha while sampling; hidden RGB outside a painted
    # diamond must never become black opaque corners after projection.
    grass=Image.open(ROOT/'assets/world/terrain/terrain-grass-flat.png').convert('RGBA')
    under=terrain.unwrap(grass,[[128,1],[255,64],[128,127],[1,64]]).convert('RGBA')
    under.alpha_composite(raw)
    return under.convert('RGB')

def corridor_mask(bit):
    # Mask clips an already painted lane. It does not create any road colour,
    # white mark, curb or flower pixels.
    mask=Image.new('L',(UV,UV));d=ImageDraw.Draw(mask)
    l,r=round(UV*.27),round(UV*.73);c=UV//2
    if bit==0:d.rectangle((0,l,c,r),fill=255)
    if bit==1:d.rectangle((l,0,r,c),fill=255)
    if bit==2:d.rectangle((c,l,UV,r),fill=255)
    if bit==3:d.rectangle((l,c,r,UV),fill=255)
    return mask

def sample_uv(source,u,v):
    arr=np.asarray(source.convert('RGBA')).astype(float);n=UV-1
    x=np.clip(u*n,0,n);y=np.clip(v*n,0,n);x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);x1=np.minimum(x0+1,n);y1=np.minimum(y0+1,n);dx=(x-x0)[...,None];dy=(y-y0)[...,None]
    out=arr[y0,x0]*(1-dx)*(1-dy)+arr[y0,x1]*dx*(1-dy)+arr[y1,x0]*(1-dx)*dy+arr[y1,x1]*dx*dy
    return Image.fromarray(np.uint8(np.clip(out,0,255)))

def tram_rail_source(native):
    y,x=np.mgrid[0:UV,0:UV]/(UV-1)
    # Actual source centreline slopes in UV; align the sampled pair of rails
    # without drawing replacement rail pixels.
    painted=sample_uv(native,x,y+.115*x-.065)
    rgb=np.asarray(painted)[...,:3].astype(float);r,g,b=np.moveaxis(rgb,-1,0)
    gold=(r>g*1.12)&(g>b*1.25)&(r>100)
    mask=Image.fromarray(np.uint8(gold)*255).filter(ImageFilter.MaxFilter(3))
    painted.putalpha(mask)
    return painted

def tram_segment(source,a,b):
    y,x=np.mgrid[0:UV,0:UV]/(UV-1)
    if {a,b}=={0,2}:return source.copy()
    if {a,b}=={1,3}:return source.transpose(Image.Transpose.TRANSPOSE)
    # An annular-sector UV remap bends actual painted rail pixels. The math
    # supplies coordinates and masks only, not stroke colours or texture.
    data={(0,1):((0,0),math.pi/2,0),(1,2):((1,0),math.pi,math.pi/2),(2,3):((1,1),-math.pi/2,-math.pi),(0,3):((0,1),0,-math.pi/2)}
    centre,start,end=data[tuple(sorted((a,b)))];dx=x-centre[0];dy=y-centre[1];ang=np.arctan2(dy,dx);radius=np.sqrt(dx*dx+dy*dy)
    # atan2 at(-x,-0) can be +pi; select the continuous fourth-quadrant range.
    if start<0 or end<0:ang=np.where(ang>0,ang-2*math.pi,ang)
    t=(ang-start)/(end-start);q=.5+(radius-.5)
    out=sample_uv(source,np.clip(t,0,1),q)
    valid=(t>=0)&(t<=1)&(np.abs(radius-.5)<.24)
    alpha=np.asarray(out.getchannel('A')).copy();alpha[~valid]=0;out.putalpha(Image.fromarray(alpha))
    return out

def build_roads():
    src=ROOT/'source-art/world/road-topology.png';im=Image.open(src).convert('RGBA');OUT.mkdir(parents=True,exist_ok=True)
    native=[native_road_uv(im,i)for i in range(16)];sources=[wp.source_record(src)]
    # The endpoint reference has a paved plaza. A native unmarked central
    # portion is geometrically expanded as a shared small junction centre.
    core=native[0].copy()
    # Two actual endpoint tiles have opposite marked halves. Keeping the
    # unmarked half of each gives a full-size shared paved plaza without
    # magnifying a tiny patch or synthesizing pavement pixels.
    core.paste(native[2].crop((0,0,UV//2,UV)),(0,0))
    base=Image.open(ROOT/'assets/world/terrain/terrain-grass-flat.png').convert('RGBA')
    # Straight and curved native tiles already have matching isometric ports.
    # T and cross images in the master drift toward screen cardinal points;
    # reconstruct them from true native directional lane modules instead.
    direct={1:0,2:1,4:2,8:3,5:4,10:5,3:6,6:7,12:8,9:9}
    entries=[];qa=[]
    road_uv={}
    for mask in range(16):
        if mask in direct:
            u=native[direct[mask]]
            op='actual painted road tile crop -> UV normalization -> fixed isometric diamond Alpha; no invented painted detail'
            reconstruction=False
        else:
            u=core.copy()
            for k in range(4):
                if mask&(1<<k):u.paste(native[k],(0,0),corridor_mask(k))
            op='native painted endpoint lane strips + native stone plaza centre -> explicit multi-source module composition -> canonical diamond; raw generated T/cross excluded because port geometry drifted'
            reconstruction=True
        tile=terrain.project(u)
        road_uv[mask]=u
        # Ground from each native lane remains; an edge-padding suggestion is
        # recorded, with exact boundary mouths measured separately below.
        file=OUT/('road-mask-'+format(mask,'02d')+'.png');tile.save(file)
        a=wp.base_asset('road-mask-'+format(mask,'02d'),file.relative_to(ROOT).as_posix(),tile,sources[0],op,'infrastructure',[128,64]);a.update({'sha256':wp.sha(file),'connectionMask':mask,'connectedPorts':[PORT_NAMES[k]for k in range(4)if mask&(1<<k)],'portPixels':{PORT_NAMES[k]:list(PORT_POINTS[k])for k in range(4)if mask&(1<<k)},'logicalFootprint':[1,1],'reconstructedFromNativeModules':reconstruction,'sourceCellIndex':direct.get(mask),'status':'produced-needs-port-review','unityValidated':False,'semanticConnectionVerified':mask in direct,'sourceGeometryReview':'Native straight/end/curve geometry retained. Composite junctions require additional connection-sheet review.'});entries.append(a)
        wp.writej(str(file)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'generatedAt':wp.now(),'route':'deterministic-derivative','width':256,'height':128,'operation':op,'derivedFrom':sources,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'unverifiedReason':'Imagegen service did not expose model/quality; deterministic clipping/composition is not new model detail.'})
        qa.append({'id':a['id']+'.canvas-alpha','level':'OK'if tile.mode=='RGBA'and tile.getchannel('A').getextrema()==(0,255)else'FAIL','value':list(tile.size)})
    # Tram axis uses the actual painted tram cell and its declared mirrored
    # axis. This is a symmetric track/road module, not a new perspective.
    for ident,u,mirrored in [('tram-ac',native[15],False),('tram-bd',native[15].transpose(Image.Transpose.TRANSPOSE),True)]:
        tile=terrain.project(u);p=OUT/(ident+'.png');tile.save(p)
        a=wp.base_asset(ident,p.relative_to(ROOT).as_posix(),tile,sources[0],'painted tram native cell crop, UV projection'+('; symmetric UV mirror'if mirrored else''),'infrastructure',[128,64]);a.update({'sha256':wp.sha(p),'connectionMask':10 if mirrored else 5,'status':'produced-needs-port-review','mirrored':mirrored,'nativeUpscale':False});entries.append(a)
        wp.writej(str(p)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'route':'deterministic-derivative','operation':a['operation'],'derivedFrom':sources,'actualModel':None,'actualQuality':None,'nativeModelGeneration':False})
    rails=tram_rail_source(native[15])
    for mask in range(1,16):
        u=road_uv[mask].convert('RGBA');ports=[k for k in range(4)if mask&(1<<k)]
        if len(ports)==1:
            k=ports[0];segment=rails if k in[0,2]else rails.transpose(Image.Transpose.TRANSPOSE)
            m=corridor_mask(k);segment=segment.copy();segment.putalpha(Image.fromarray(np.minimum(np.asarray(segment.getchannel('A')),np.asarray(m))))
            u.alpha_composite(segment)
        else:
            for ix,a in enumerate(ports):
                for b in ports[ix+1:]:u.alpha_composite(tram_segment(rails,a,b))
        tile=terrain.project(u.convert('RGB'));ident='tram-mask-'+format(mask,'02d');p=OUT/(ident+'.png');tile.save(p)
        operation='actual painted tram rail pair extracted by colour range; UV centreline correction; true symmetric transpose or annular UV curve remap; layered over actual road network art. Geometry masks do not paint new rail pixels.'
        a=wp.base_asset(ident,p.relative_to(ROOT).as_posix(),tile,sources[0],operation,'infrastructure',[128,64]);a.update({'sha256':wp.sha(p),'connectionMask':mask,'connectedPorts':[PORT_NAMES[k]for k in ports],'portPixels':{PORT_NAMES[k]:list(PORT_POINTS[k])for k in ports},'status':'produced-needs-port-review','geometricCurveDerivative':True,'sourceRequirementIds':['road-tram'],'nativeUpscale':False});entries.append(a)
        wp.writej(str(p)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'route':'deterministic-derivative','operation':operation,'derivedFrom':sources,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None})
    manifest={'schema':'cloud-route.world-art.v1','batchId':'roads','createdAt':wp.now(),'assets':entries,'animations':[],'qa':qa,'sourceCrops':{'nativeCellCentresX':[198,580,962,1347],'nativeCellCentresY':[120,366,608,845],'nativeQuadHalfWidth':160,'nativeQuadHeightAbove':82,'nativeQuadHeightBelow':80},'acceptance':'not yet accepted; connection geometry sheets must be inspected','sourceLimitations':['Generated T and cross shapes had cardinal-screen port drift; deterministic painted-module reconstruction used instead.','Tram curves are remapped actual straight-rail paint; not separately native generated curves.','A road graph mask is topology data; no runtime pathfinding, collision or road ownership implemented.'],'portOrder':PORT_NAMES,'portPixels':PORT_POINTS}
    wp.writej(OUT/'manifest.json',manifest);contact(entries);connection_sheet(entries)
    print(json.dumps({'assets':len(entries),'manifest':str(OUT/'manifest.json'),'contact':str(PRE/'roads-contact.jpg')},ensure_ascii=False))

def contact(entries):
    im=Image.new('RGB',(1200,math.ceil(len(entries)/4)*210),(35,69,62));d=ImageDraw.Draw(im)
    for n,a in enumerate(entries):
        tile=Image.open(ROOT/a['image']).convert('RGBA');x=(n%4)*300+22;y=(n//4)*210+10;im.paste(tile,(x,y),tile)
        for k,p in enumerate(PORT_POINTS):
            c='#f4b946'if a.get('connectionMask',0)&(1<<k)else'#78998b';d.ellipse((x+p[0]-3,y+p[1]-3,x+p[0]+3,y+p[1]+3),fill=c)
        d.text((x,y+142),a['id']+' '+','.join(a.get('connectedPorts',[])),font=terrain.font(15),fill=(246,233,199))
    im.save(PRE/'roads-contact.jpg',quality=95)

def connection_sheet(entries):
    by={a['connectionMask']:a for a in entries if'connectionMask'in a and a['id'].startswith('road-mask')}
    # A small route topology panel uses actual exported PNGs, nothing drawn as road art.
    nodes={(i,j):0 for i in range(5)for j in range(5)}
    edges=[]
    for j in range(5):edges.append(((2,j),(2,j+1)))if j<4 else None
    for i in range(5):edges.append(((i,2),(i+1,2)))if i<4 else None
    for (i,j),(x,y)in edges:
        if x>i:nodes[(i,j)]|=8;nodes[(x,y)]|=2
        else:nodes[(i,j)]|=4;nodes[(x,y)]|=1
    im=Image.new('RGB',(1400,770),(35,69,62));d=ImageDraw.Draw(im)
    for depth in range(9):
        for i in range(5):
            j=depth-i
            if not 0<=j<5:continue
            a=by[nodes[(i,j)]];tile=Image.open(ROOT/a['image']).convert('RGBA');x=700+(j-i)*128-128;y=70+(i+j)*64
            im.paste(tile,(x,y),tile)
    d.text((35,25),'道路连续拼装 · 端点/直线/交叉（实际正式 PNG）',font=terrain.font(25),fill=(246,233,199));im.save(PRE/'roads-connections.jpg',quality=96)
if __name__=='__main__':build_roads()

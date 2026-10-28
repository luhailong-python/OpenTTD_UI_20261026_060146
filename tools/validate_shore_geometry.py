"""Read actual upstream C++ heights, layers, pixels and all shore slots.

No root reports or aggregation are run.  The tiny native probe compiles the
actual upstream switch and enum, rather than calling the producer's height code.
"""
from pathlib import Path
from PIL import Image
import subprocess, shutil, re, json, math
import numpy as np
import world_pack as wp
from validate_foundation_geometry import source_z

R=wp.ROOT;MP=R/'assets/world/terrain/shore-geometry/manifest.json';REC=R/'records/world-production'


def compiled_source_heights(codes):
    source=(R/'reference/OpenTTD/src/landscape.cpp').read_text(encoding='utf-8')
    begin=source.index('switch (RemoveHalftileSlope(corners))',source.index('uint GetPartialPixelZ('));brace=source.index('{',begin);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    body=source[brace:end]
    slopes=(R/'reference/OpenTTD/src/slope_type.h').read_text(encoding='utf-8')
    enum=slopes.split('enum Slope : uint8_t {',1)[1].split('SLOPE_HALFTILE =',1)[0]
    cpp='#include <cstdint>\n#include <cstdio>\n#include <cstdlib>\nconstexpr int TILE_SIZE=16,TILE_HEIGHT=8;\n#define NOT_REACHED() std::abort()\nenum Slope:uint8_t{'+enum+'};\nunsigned probe(int x,int y,int corners){switch(corners)'+body+'}\nint main(){int codes[]={'+','.join(map(str,codes))+'};for(int c:codes)for(int y=0;y<=16;y++)for(int x=0;x<=16;x++)std::printf("%d,%d,%d,%u\\n",c,x,y,probe(x,y,c));}\n'
    src=REC/'shore-source-height-probe.cpp';exe=REC/'shore-source-height-probe.exe';src.write_text(cpp,encoding='utf-8')
    compiler=shutil.which('clang++')
    if not compiler:raise RuntimeError('Clang required for independent actual-source shore contact check')
    flags={'creationflags':subprocess.CREATE_NO_WINDOW}if hasattr(subprocess,'CREATE_NO_WINDOW')else{}
    compile_result=subprocess.run([compiler,'-std=c++17',str(src),'-o',str(exe)],capture_output=True,text=True,**flags)
    if compile_result.returncode:raise RuntimeError(compile_result.stderr)
    output=subprocess.run([str(exe)],check=True,capture_output=True,text=True,**flags).stdout
    result={}
    for line in output.splitlines():
        c,x,y,z=map(int,line.split(','));result[(c,x,y)]=z
    for p in[exe,src.with_suffix('.obj'),src.with_suffix('.pdb')]:
        if p.exists()and p.parent.resolve()==REC.resolve():p.unlink()
    return result,{'tool':compiler,'probeSource':wp.rel(src),'probeSHA256':wp.sha(src),'sampleCount':len(result),'sourceSwitchExtractedVerbatim':True,'constants':{'TILE_SIZE':16,'TILE_HEIGHT':8},'scope':'Natural full-tile slopes only; excludes upstream half-tile early branch by contract'}


def mesh_z(p,x,y):
    # Independent barycentric lookup over the recorded WORLD triangles.
    for inds in p['triangles']:
        vs=[p['vertices'][i]for i in inds];(ax,ay),(bx,by),(cx,cy)=[v['sourceXY']for v in vs]
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        a=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/den;b=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/den;c=1-a-b
        if min(a,b,c)>=-1e-8:return sum(w*v['renderZ']for w,v in zip((a,b,c),vs))
    raise ValueError('World mesh hole')


def main():
    m=wp.readj(MP);mapping=m['coverageMappings'][0];checks=[];by={a['image']:a for a in m['assets']}
    def check(name,ok,**data):checks.append({'id':name,'passed':bool(ok),**data})
    text=(R/'reference/OpenTTD/src/water_cmd.cpp').read_text(encoding='utf-8')
    table=list(map(int,re.findall(r'\b\d+\b',re.search(r'tileh_to_shoresprite\s*=\s*\{([^}]+)',text,re.S).group(1))))
    codes=[c for c,_ in wp.SLOPES if c not in[0,5,10]]
    expected={(cl,c,table[c])for cl in['grass','sand','snow']for c in codes}
    check('actual-source48-state-matrix',{(s['shoreClimate'],s['sourceSlopeCode'],s['sourceShoreIndex'])for s in mapping['states']}==expected and len(mapping['states'])==48)
    check('six-reserved-slots-no-fake-PNG',{(s['shoreClimate'],s['sourceSlopeCode'],s['sourceShoreIndex'])for s in mapping['reservedBindings']}=={(cl,c,i)for cl in['grass','sand','snow']for c,i in[(5,16),(10,17)]}and all(not s['applicable']and s['image']is None for s in mapping['reservedBindings']))
    check('source-excludes-flat-saddle-half','assert(!IsHalftileSlope(tileh))'in text and'assert(tileh != SLOPE_FLAT)'in text and'assert((tileh != SLOPE_EW) && (tileh != SLOPE_NS))'in text)
    check('upstream-table-including-steep-remap',m['geometry']['sourceSlopeToShoreTable']==table and [table[c]for c in[23,27,29,30]]==[0,5,10,15])
    actual,probe=compiled_source_heights(codes)
    caches={}
    for a in m['assets']:
        p=R/a['image'];im=Image.open(p).convert('RGBA');caches[a['image']]=im
        alpha_range=im.getchannel('A').getextrema()
        check(a['id']+'.formal-PNG',Image.open(p).mode=='RGBA'and im.size==(256,192)and a['anchorPx']==[128,128]and a['sha256']==wp.sha(p)and alpha_range[0]==0 and alpha_range[1]>0 and(a['shoreLayer']=='bank'or alpha_range[1]==255)and a['authoritative']and a['sourceRequirementIds']==['water-shore'],alphaRange=list(alpha_range),nativeSoftBankAlphaAllowed=a['shoreLayer']=='bank')
        check(a['id']+'.current-native-dependencies',all((R/r['file']).is_file()and wp.sha(R/r['file'])==r['sha256']and(r['record']is None or(R/r['record']).is_file())for r in a['derivedFrom']))
        ar=np.asarray(im);check(a['id']+'.transparent-RGB-clean',not np.any(ar[ar[...,3]==0,:3]))
    postures={p['sourceSlopeCode']:p for p in m['geometry']['postures']}
    contact_evidence=[];water_evidence=[]
    for code,p in postures.items():
        tag='slope'+str(code);check(tag+'.17x17-grid512triangles',len(p['vertices'])==289 and len(p['triangles'])==512)
        errors=[];interior=0;boundary=0
        for v in p['vertices']:
            x,y=v['sourceXY'];z=actual[(code,x,y)];is_boundary=x in[0,16]or y in[0,16]
            continuous=source_z(code,x/16,y/16)*8;contact=(x,y)in[(4,4),(4,11),(11,9)];contour=z==0 and continuous>0 and not contact
            target=continuous if is_boundary or contour else z
            correct=v['sourceZ']==z and abs(v['renderZ']-target)<1e-8 and v['boundaryContinuous']==is_boundary and v['shoreContourContinuous']==contour and v['wetRockContactExact']==contact
            expected_px=[128+(y-x)*8,64+(x+y)*4-target*4]
            correct=correct and all(abs(a-b)<1e-8 for a,b in zip(v['screenPx'],expected_px))
            if not correct:errors.append(v)
            if is_boundary:boundary+=1
            else:interior+=1
        check(tag+'.actual-C++-heights-and-straight-outer-edges',not errors,interiorIntegerContacts=interior,continuousBoundaryVertices=boundary,issues=errors[:3])
        zarea=sum(.5 for tri in p['triangles']if all(p['vertices'][i]['renderZ']==0 for i in tri))
        check(tag+'.true-zero-height-world-area',zarea==p['zeroHeightWorldArea']and bool(zarea)==p['waterHasPositiveArea'],worldArea=zarea)
        s=next(s for s in mapping['states']if s['sourceSlopeCode']==code)
        water=caches[s['water']]if s['water']else None
        # Pixel at flat inverse UV must lie on z=0, including the two sparse
        # source-quantized low-edge water strips. Sample every opaque water
        # pixel on a4px lattice, independently inverting the water plane.
        issues=[];samples=0
        if water:
            for sy in range(2,192,4):
                for sx in range(2,256,4):
                    if water.getpixel((sx,sy))[3]<250:continue
                    total=(sy+.5-64)/4;delta=(sx+.5-128)/8;x=(total-delta)/2;y=(total+delta)/2
                    if min(x,y)<0 or max(x,y)>16:issues.append([sx,sy,'outside']);continue
                    z=mesh_z(p,x,y);samples+=1
                    if abs(z)>1e-7:issues.append([sx,sy,z])
        check(tag+'.actual-water-pixels-horizontal-zero-Z',not issues,pixelSamples=samples,issues=issues[:5]);water_evidence.append({'sourceSlopeCode':code,'worldZeroArea':zarea,'waterPNG':s['water'],'samples':samples})
        for x,y in[(4,4),(4,11),(11,9)]:
            z=actual[(code,x,y)];render=mesh_z(p,x,y);point=[128+(y-x)*8,64+(x+y)*4-z*4]
            check(tag+f'.rock-contact-{x}-{y}',abs(render-z)<1e-8,sourceZ=z,shorePx=point,rockPx=[point[0],point[1]+64])
            for climate in['grass','sand','snow']:
                state=next(s for s in mapping['states']if s['sourceSlopeCode']==code and s['shoreClimate']==climate)
                whole=caches[state['whole']];support=max(whole.getpixel((xx,yy))[3]for xx in range(max(0,point[0]-1),min(256,point[0]+2))for yy in range(max(0,point[1]-1),min(192,point[1]+2)))
                check(tag+f'.{climate}-actual-rock-support-{x}-{y}',support>=240,alpha=support)
            contact_evidence.append({'sourceSlopeCode':code,'sourceTileXY':[x,y],'sourceHeightUnits':z,'shoreContactPx':point,'rockContactPx':[point[0],point[1]+64]})
    for s in mapping['states']:
        out=Image.new('RGBA',(256,192))
        for k in s['layerOrder']:
            f=s['layers'][k]
            if f:out.alpha_composite(caches[f])
        check(s['shoreClimate']+f"-slot{s['sourceShoreIndex']}.exact-three-layer-reassembly",out.tobytes()==caches[s['whole']].tobytes())
        check(s['shoreClimate']+f"-slot{s['sourceShoreIndex']}.source-flooding-state",s['sourceFloodingBehaviour']==('Active'if s['sourceSlopeCode']in[1,2,4,8]else'DryOut')and bool(s['water'])==s['waterHasPositiveArea'])
    for page in m['contactPages']:check(page['file']+'.current-page',wp.sha(R/page['file'])==page['sha256'])
    legacy=wp.readj(R/'assets/world/infrastructure/water-states/manifest.json')
    old=[a for a in legacy['assets']if a.get('legacyFlatShoreReference')]
    check('all54-old-flat-shores-retired-from-authority',len(old)==54 and all(a.get('authoritative')is False and not a.get('sourceRequirementIds')and a.get('supersededBy')==wp.rel(MP)for a in old))
    retired=REC/'shore-legacy-retirement.json'
    check('old54-PNG-pixels-unchanged',retired.is_file()and all(wp.sha(R/a['file'])==a['sha256']for a in wp.readj(retired)['retainedPNGs']))
    result={'createdAt':wp.now(),'manifest':wp.rel(MP),'manifestSHA256':wp.sha(MP),'sourceHeightProbe':probe,'validStates':48,'reservedBindings':6,'actualFormalPNGs':len(m['assets']),'checks':checks,'passed':sum(c['passed']for c in checks),'failed':sum(not c['passed']for c in checks),'waterPlaneEvidence':water_evidence,'rockContactEvidence':contact_evidence,'claims':['Compiled actual upstream C++ natural-height switch;289vertices×16slopes compared, with continuous source boundary rule checked separately.','All48 actual three-layer reassemblies, every formal PNG/source SHA/Alpha and shared48rock contacts inspected programmatically.','Six reserved climate slots are not exported as counterfeit artwork.'],'limitations':['This is art geometry QA, not Unity runtime/import validation.','The mask is an explicit source-height reconstruction because upstream source selects external painted sprites rather than defining the pixel mask.']}
    wp.writej(REC/'shore-geometry-validation.json',result)
    print(json.dumps({'checks':len(checks),'passed':result['passed'],'failed':result['failed'],'manifestSHA256':result['manifestSHA256'],'failures':[c for c in checks if not c['passed']][:10]}))


if __name__=='__main__':main()

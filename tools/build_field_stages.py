"""Nine real field stages on19 slopes from native soil/plant/hay paintings.
Ground is projected; plant sprites stay upright at source-derived root heights.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import numpy as np,json,argparse
from collections import deque
import world_pack as wp
import build_world_terrain as terrain
from foundation_geometry_v2 import natural

R=wp.ROOT
OUT=R/'assets/world/terrain/field-stages'
PRE=R/'previews/world/field-stages'
CFG=R/'config/field-stages-native.json'
STAGES=['bare-ploughed','germinating','young-seedlings','leafy-seedlings',
        'young-green-grain','full-green-grain','ripening-mixed-grain','ripe-golden-grain','harvested-haypacks']


def ref(path):
    return {'file':path,'sha256':wp.sha(R/path),'record':path+'.derivation.json'}


def emit(ident,im,parents,operation,**extra):
    p=OUT/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    ax,ay=extra.pop('anchorPx',[128,160])
    a={'id':ident,'image':wp.rel(p),'width':im.width,'height':im.height,
       'anchorPx':[ax,ay],'pivotUnity':[ax/im.width,1-ay/im.height],
       'sha256':wp.sha(p),'derivedFrom':parents,'operation':operation,
       'category':'field-stage','sourceRequirementIds':['terrain-field'],
       'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,
       'nativeUpscale':False,'status':'produced-needs-stage-art-review','unityValidated':False,**extra}
    wp.writej(str(p)+'.derivation.json',a)
    return a


def soil_source():
    path='assets/world/terrain/terrain-field-flat.png'
    uv=terrain.unwrap(Image.open(R/path).convert('RGBA'),[[128,1],[255,64],[128,127],[1,64]])
    arr=np.asarray(uv).astype(float);red,green,blue=np.moveaxis(arr,-1,0)
    vegetation=(green>red*1.04)&(green>blue*1.15)
    best=None
    # A clean native furrow strip, not a painted-over seedling. Repetition is
    # explicit native-pixel reuse; it adds no original soil detail.
    for y in range(0,145,4):
        for x in range(0,97,4):
            area=arr[y:y+48,x:x+96];bad=int(vegetation[y:y+48,x:x+96].sum())
            score=bad*1e6-float(area.var())
            if best is None or score<best[0]:best=(score,(x,y,x+96,y+48),bad)
    patch=uv.crop(best[1]);texture=Image.new('RGB',(192,192))
    for y in range(0,192,48):
        for x in range(0,192,96):texture.paste(patch,(x,y))
    return terrain.project(texture),[ref(path)],{'unwrappedNativeUVBox':list(best[1]),
         'greenPlantPixelsInSelectedPatch':best[2],'repeatXY':[2,4],
         'operation':'native furrow-only strip repeated2x4 in material UV; existing paint only; no seedling inpainting'}


def primitives():
    assets=[];out={}
    seedpath='assets/world/infrastructure/fences-shore/field-seedlings.png'
    raw=Image.open(R/seedpath).convert('RGBA');box=(310,236,352,280);piece=raw.crop(box)
    rgb=np.asarray(piece)[:,:,:3].astype(float);r,g,b=np.moveaxis(rgb,-1,0)
    mask=(g>r*1.06)&(g>b*1.2)
    pending=mask.copy();best=[]
    for y,x in zip(*np.where(mask)):
        if not pending[y,x]:continue
        pending[y,x]=False;queue=deque([(y,x)]);component=[]
        while queue:
            yy,xx=queue.popleft();component.append((yy,xx))
            for ny in range(max(0,yy-1),min(mask.shape[0],yy+2)):
                for nx in range(max(0,xx-1),min(mask.shape[1],xx+2)):
                    if pending[ny,nx]:pending[ny,nx]=False;queue.append((ny,nx))
        if len(component)>len(best):best=component
    selected=np.zeros_like(mask)
    for y,x in best:selected[y,x]=True
    # One native leaf clump plus a1px real-paint fringe, no synthetic leaves.
    alpha=Image.fromarray(np.uint8(selected)*255).filter(ImageFilter.MaxFilter(3));piece.putalpha(ImageChops.multiply(piece.getchannel('A'),alpha))
    bb=piece.getbbox();piece=piece.crop(bb)
    root=[piece.width/2,piece.height-1]
    e=emit('field-primitive-seedling',piece,[ref(seedpath)],
         'actual native leaf clump selected from soil by authored crop/green ownership mask plus1px fringe; no new paint or enlargement',
         category='field-native-primitive',anchorPx=root,nativeCropXYXY=list(box),alphaTrimBox=list(bb))
    assets.append(e);out['seedling']=(piece,root,e)
    haypath='assets/world/industries/farm.png';raw=Image.open(R/haypath).convert('RGBA')
    box=(250,262,303,299);piece=raw.crop(box);mask=Image.new('L',piece.size)
    poly=[(2,17),(10,13),(12,5),(24,0),(40,4),(46,11),(48,20),(45,28),(30,32),(20,33),(6,30),(0,26)]
    ImageDraw.Draw(mask).polygon(poly,fill=255);piece.putalpha(ImageChops.multiply(piece.getchannel('A'),mask))
    root=[26,33]
    e=emit('field-primitive-haypacks',piece,[ref(haypath)],
         'actual rectangular bound haypacks in adopted native farm painting; explicit Alpha ownership crop, no floor/building reuse and no enlargement',
         category='field-native-primitive',anchorPx=root,nativeCropXYXY=list(box),ownershipPolygon=poly)
    assets.append(e);out['haypacks']=(piece,root,e)
    if CFG.exists():
        cfg=wp.readj(CFG)
        for kind in ['green-grain','gold-grain']+(['haypacks']if 'haypacks'in cfg else[]):
            c=cfg[kind];path=c['file'];raw=Image.open(R/path).convert('RGBA')
            piece=raw.crop(c['cropXYXY'])if c.get('cropXYXY')else raw
            cleanup=None
            if c.get('keepMainComponent'):
                before=np.asarray(piece.getchannel('A'))
                piece,cleanup=wp.keep_main_component(piece,threshold=32,margin=2)
                arr=np.asarray(piece).copy();arr[arr[:,:,3]<4]=0;arr[arr[:,:,3]==0,:3]=0
                after=arr[:,:,3]
                cleanup.update({'maskedNonzeroPixels':int(np.count_nonzero((before>0)&(after==0))),
                    'alphaBelow4Removed':True,'outsideZeroAlphaRGBCleared':True})
                piece=Image.fromarray(arr);bb=piece.getbbox();piece=piece.crop(bb)
                pa=np.asarray(piece.getchannel('A'));yy,xx=np.where((pa>64)&(np.indices(pa.shape)[0]>=pa.shape[0]-7))
                root=[float(np.average(xx,weights=pa[yy,xx]))+4,piece.height-1+4]
                canvas=Image.new('RGBA',(piece.width+8,piece.height+8));canvas.alpha_composite(piece,(4,4));piece=canvas
                cleanup.update({'alphaTrimBox':list(bb),'transparentPaddingPx':4,
                    'anchorPolicy':'physical stem/bale bottom contact; Alpha-weighted center of last7 opaque rows, not whole Alpha centroid'})
            else:root=c['anchorPx']
            record=c.get('record',path+'.generation.json')
            e=emit('field-primitive-'+kind,piece,[{'file':path,'sha256':wp.sha(R/path),'record':record}],
                 'adopted native standalone crop/hay component; source cell crop, main-component Alpha cleanup, transparent padding and explicit physical root anchor; no repaint or enlargement',
                 category='field-native-primitive',anchorPx=root,nativeCropXYXY=c.get('cropXYXY'),alphaCleanup=cleanup)
            assets=[a for a in assets if a['id']!=e['id']]
            assets.append(e);out[kind]=(piece,root,e)
    return assets,out


def point(u,v,z):return [128+(v-u)*128,96+(u+v)*64-z*32]


def instances(stage):
    if stage==0:return []
    if stage==8:
        return [{'kind':'haypacks','uv':[u,v],'heightPx':28}for u,v in[(.25,.3),(.65,.3),(.55,.72)]]
    n=4 if stage==1 else 5 if stage in [2,3,4]else 6
    result=[]
    for row in range(n):
        for col in range(n):
            if stage==1 and(row+col)%2:continue
            u=.14+row*.72/(n-1);v=.14+col*.72/(n-1)
            kind='seedling'if stage<=3 else 'green-grain'if stage<=5 else ('green-grain'if stage==6 and(row+col)%3==0 else'gold-grain')
            height={1:5,2:8,3:11,4:15,5:21,6:23,7:27}[stage]
            result.append({'kind':kind,'uv':[u,v],'heightPx':height})
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True)
    oldterrainpath=R/'assets/world/terrain/manifest.json';oldterrain=wp.readj(oldterrainpath)
    oldterrainsha=wp.sha(oldterrainpath)
    oldterrainassets=[{'file':a['image'],'sha256':wp.sha(R/a['image'])}for a in oldterrain['assets']]
    assets,parts=primitives()
    if not args.partial and not {'green-grain','gold-grain'}<=set(parts):
        raise ValueError('Clean native green/gold grain clumps pending; use --partial for stages0..3/8, never substitute cut overlapping heads')
    flat,soilrefs,soilmeta=soil_source();ground={};states=[]
    for code,name in wp.SLOPES:
        p,points,h=wp.projected_slope(flat,code)
        can=Image.new('RGBA',(256,256));can.alpha_composite(p,(0,32))
        e=emit('field-soil-slope-'+name,can,soilrefs,'existing native furrow pixels -> source slope triangles;32px transparent head padding; no native detail enlargement',
             category='field-stage-ground',slopeCode=code,soilSource=soilmeta)
        assets.append(e);ground[code]=e
    stages=[0,1,2,3,8]if args.partial else list(range(9))
    for stage in stages:
        specs=instances(stage)
        for code,name in wp.SLOPES:
            h=wp.corner_heights(code);overlay=Image.new('RGBA',(256,256));placements=[]
            for spec in sorted(specs,key=lambda x:sum(x['uv'])):
                part,root,entry=parts[spec['kind']]
                ratio=min(1,spec['heightPx']/part.height)
                size=[max(1,round(part.width*ratio)),max(1,round(part.height*ratio))]
                sprite=part.resize(size,Image.Resampling.LANCZOS)
                u,v=spec['uv'];z=natural(u,v,h,code);dest=point(u,v,z)
                xy=[round(dest[0]-root[0]*ratio),round(dest[1]-root[1]*ratio)]
                overlay.alpha_composite(sprite,xy)
                placements.append({**spec,'rootPx':dest,'rootHeightUnits':z,'image':entry['image'],
                    'scale':ratio,'offsetPx':xy,'renderSizePx':size,'orientation':'upright billboard, no terrain/shear deformation'})
            whole=Image.open(R/ground[code]['image']).convert('RGBA');whole.alpha_composite(overlay)
            parents=[ref(ground[code]['image'])]+[ref(parts[k][2]['image'])for k in sorted({i['kind']for i in specs})]
            en=emit('field-stage-'+str(stage)+'-slope-'+name,whole,parents,
                'source crop stage with projected native furrow soil and upright native plant/hay sprites at exact piecewise slope-root heights; no new native painting',
                sourceFieldType=stage,fieldStageName=STAGES[stage],slopeCode=code,placements=placements)
            assets.append(en);layer=None
            if specs:
                ov=emit('field-stage-'+str(stage)+'-slope-'+name+'-overlay',overlay,parents[1:],
                    'same native upright crop/hay placements as whole; transparent optional layer, no ground and no new painting',
                    category='field-stage-overlay',sourceFieldType=stage,fieldStageName=STAGES[stage],slopeCode=code,placements=placements)
                assets.append(ov);layer=ov['image']
            states.append({'sourceFieldType':stage,'fieldStageName':STAGES[stage],'slopeCode':code,
                'whole':en['image'],'ground':ground[code]['image'],'overlay':layer,'placements':placements,
                'renderRule':'whole OR ground+overlay; stage0 has no plant layer, do not emit empty placeholder PNG'})
    manifest={'schema':'cloud-route.field-stages.v1','createdAt':wp.now(),'assets':assets,'animations':[],
        'coverageMappings':[{'requirementId':'terrain-field','files':[a['image']for a in assets],
           'fieldStages':stages,'slopeCodes':[c for c,n in wp.SLOPES],'states':states,
           'sourceFieldTypeCapacity':16,'validSourceFieldTypes':list(range(9)),
           'invalidStoredFieldTypes':list(range(9,16)),'sourceRandomVariants':None,
           'sourceEvidence':['src/table/clear_land.h:68-78','src/clear_cmd.cpp:174','src/clear_cmd.cpp:338-340'],
           'sourceRule':'GetFieldType is growth stage, not random variant; source cycles0..8;9..15 have no initialized farmland sprite',
           'sourceInitialStageRandomRule':'src/industry_cmd.cpp:1079 chooses field_type=GB(r,8,8)*9>>8; random initial growth stage, not16random paintings',
           'authoritativeSourceFieldStageBinding':True,
           'legacyFieldUVVariants':'Existing terrain-field-variant00..15 remain recorded cosmetic derivatives only; do not use them as source field_type sprites',
           'sourceOverrides':{'snow':'src/clear_cmd.cpp:142-154 renders existing snow terrain and returns before drawing field crops; no extra snowy wheat overlay required',
                              'orphanedField':'src/clear_cmd.cpp:334-336 converts fields without linked farm at stage>=7 to existing Grass density2'},
           'stateAnimationRule':'stages change at source field-counter ticks, not a new frame clip or added wind animation'}],
        'counts':{'validStagesProduced':len(stages),'slopeCodes':19,'sourceStateBindings':len(states),
                  'formalPNGs':len(assets),'newNativePaintingClaim':False},
        'fixedCanvasPx':[256,256],'anchorPx':[128,160],'heightStepPx':32,
        'productionNoOtherWrites':{'scope':'historical build-interval proof only; not persistent source dependencies',
            'allOutputPathsWithinPack':all((R/a['image']).resolve().parent==OUT.resolve()for a in assets),
            'manifestSnapshot':{'file':wp.rel(oldterrainpath),'sha256':oldterrainsha},
            'PNGSnapshot':oldterrainassets,'recordedAt':wp.now(),
            'unrelatedTerrainChangesDoNotInvalidateFieldArt':True},
        'acceptance':'partial production; missing standalone native grain clumps'if args.partial else'produced; actual crop-stage/soil/slope review pending',
        'unityValidated':False,'userArtAcceptance':'pending',
        'knownDerivatives':['Native crop clumps change scale/density and placement by stage; not nine independent original paintings.',
                            'Soil is a clean native furrow strip repeated in UV; no program-painted mud or stems.',
                            'Plant crowns remain upright while roots follow19 legal piecewise terrain slopes.']}
    proof=manifest['productionNoOtherWrites']
    proof['snapshotUnchangedDuringThisBuild']=wp.sha(oldterrainpath)==oldterrainsha and all(wp.sha(R/a['file'])==a['sha256']for a in oldterrainassets)
    proof['snapshotInterpretation']='A comparison change can come from another producer; ongoing validity uses only actual assets[].derivedFrom source hashes, never all terrain PNGs'
    if not proof['allOutputPathsWithinPack']:raise ValueError('Field output escaped its dedicated pack')
    wp.writej(OUT/'manifest.json',manifest)
    print(json.dumps(manifest['counts']))


if __name__=='__main__':main()

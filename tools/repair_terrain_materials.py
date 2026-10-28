"""Localized square-master terrain export. Never calls an image model.

Only selected flat+19 slope families and their QA previews are written.
All other manifest entries and formal PNG bytes must stay unchanged.
Visual approval is recorded separately after actually inspecting the exports.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import copy, json
import build_world_terrain as b
import world_pack as wp

R=wp.ROOT
NAMES=['grass','bare','rough','field','snow','snowgrass','desert','tropical','toyland','shallow','shore-sand','riverbed']

def ref(file):
    path=R/file
    record=str(file)+'.derivation.json'
    return {'file':str(file),'sha256':wp.sha(path),'record':record if(R/record).is_file()else None}

def preview_record(path,sources,operation):
    wp.writej(str(path)+'.derivation.json',{'file':wp.rel(path),'sha256':wp.sha(path),'derivedAt':wp.now(),'operation':operation,'derivedFrom':[ref(f)for f in sources],'nativeModelGeneration':False,'actualModel':None,'actualQuality':None})

def repeat8(file,destination,label):
    tile=Image.open(R/file).convert('RGBA')
    # Native formal pixels; only translation and labels, no enlargement.
    out=Image.new('RGB',(2112,1112),'#23453e');ox=1056;oy=45
    for depth in range(15):
        for i in range(8):
            j=depth-i
            if not 0<=j<8:continue
            out.paste(tile,(ox+(j-i)*128-128,oy+(i+j)*64),tile)
    ImageDraw.Draw(out).text((28,1074),label,font=b.font(20),fill='#f6e9c7')
    out.save(destination,quality=98)
    preview_record(destination,[file],'Actual formal256x128 pixels translated into8x8 isometric repeat; labels only; no code-painted material, no resize')

def repair(materials, record_name='terrain-material-repair'):
    materials=list(dict.fromkeys(materials))
    if not materials or any(n not in b.MATERIAL_MASTERS for n in materials):raise ValueError('Unsupported localized material')
    mf=b.OUT/'manifest.json';m=wp.readj(mf);original=copy.deepcopy(m)
    targets={f'terrain-{name}-flat'for name in materials}|{f'terrain-{name}-slope-{slope}'for name in materials for _,slope in wp.SLOPES}
    before={a['image']:wp.sha(R/a['image'])for a in m['assets']}
    touched=[];evidence=[]
    for name in materials:
        uv,sources,info=b.square_material(name);flat=b.project(uv);seam=wp.edge_rmse(flat)
        pixels={f'terrain-{name}-flat':(flat,None,None,None)}
        for code,slope in wp.SLOPES:
            im,points,heights=wp.projected_slope(flat,code)
            pixels[f'terrain-{name}-slope-{slope}']=(im,code,points,heights)
        family=[]
        for a in m['assets']:
            if a['id']not in pixels:continue
            im,code,points,heights=pixels[a['id']];path=R/a['image']
            expected_anchor=[128,64]if code is None else[128,128]
            if im.size!=(a['width'],a['height'])or a['anchorPx']!=expected_anchor:raise ValueError('Canvas or anchor would change: '+a['id'])
            oldsha=before[a['image']];im.save(path)
            op=b.square_material_operation(name)+(' -> piecewise-affine slope projection'if code is not None else'')
            a.update(info);a.update({'derivedFrom':sources,'operation':op,'photometricSeam':seam,'sourceUVResolution':[b.UV_SIZE,b.UV_SIZE],'sha256':wp.sha(path),'status':'produced-needs-visual-review','reviewBasis':'Localized native material replacement; actual current-hash repeat and slope review required','nativeUpscale':False,'unityValidated':False})
            wp.writej(str(path)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'derivedAt':wp.now(),'route':'deterministic-derivative','tool':'repair_terrain_materials.py / build_world_terrain.py square_material+periodic+project / world_pack.projected_slope','width':im.width,'height':im.height,'operation':op,'derivedFrom':sources,'sourceNativeSize':info['nativeSourceSize'],'sourceUVWorkingResolution':[b.UV_SIZE,b.UV_SIZE],'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'previousFormalSHA256':oldsha,'nativeUpscale':False})
            touched.append(a['image']);family.append(a)
        if len(family)!=20:raise ValueError('Expected flat+19source slopes: '+name)
        for q in m['qa']:
            if q['id'].split('.')[0]!=name:continue
            metric=q['id'].split('.')[1];q['value']=seam[metric];q['level']='OK'if seam[metric]is not None and seam[metric]<=q['threshold']else'WARN'
        b.contact(family,f'terrain-{name}-slopes-review.jpg',5,192)
        contact=b.PRE/f'terrain-{name}-slopes-review.jpg';preview_record(contact,[a['image']for a in family],'All20 actual family exports at original formal size on QA contact sheet; labels only')
        repeat8(f'assets/world/terrain/terrain-{name}-flat.png',b.PRE/f'terrain-{name}-repeat8.jpg',name+' / actual256x128 formal tile /8x8 repeat')
        # Opposite edge equality in working UV is diagnostic, never visual approval.
        evidence.append({'material':name,'source':sources[0],'sourceNativeSize':info['nativeSourceSize'],'familyImages':[{'image':a['image'],'sha256':a['sha256'],'anchorPx':a['anchorPx'],'size':[a['width'],a['height']]}for a in family],'photometricSeam':seam,'uvOppositeEdgeExact':uv.crop((0,0,1,b.UV_SIZE)).tobytes()==uv.crop((b.UV_SIZE-1,0,b.UV_SIZE,b.UV_SIZE)).tobytes()and uv.crop((0,0,b.UV_SIZE,1)).tobytes()==uv.crop((0,b.UV_SIZE-1,b.UV_SIZE,b.UV_SIZE)).tobytes(),'visualReview':'pending actual image inspection'})
    untouched=[a['image']for a in m['assets']if a['id']not in targets]
    changed_others=[f for f in untouched if wp.sha(R/f)!=before[f]]
    changed_metadata=[a['id']for a,old in zip(m['assets'],original['assets'])if a['id']not in targets and a!=old]
    if changed_others or changed_metadata:raise RuntimeError('Unrelated terrain changed')
    m.setdefault('localizedMaterialRepairHistory',[]).append(m.get('localizedMaterialRepair',{}))
    m['createdAt']=wp.now();m['localizedMaterialRepair']={'materials':materials,'updatedFormalImages':len(touched),'otherFormalImagesUnchanged':len(untouched),'visualReview':'records/world-production/'+record_name+'-visual.json'};wp.writej(mf,m)
    bases=[next(a for a in m['assets']if a['id']==f'terrain-{name}-flat')for name in NAMES]
    b.contact(bases,'terrain-materials.jpg',4,180);b.repeat_preview(bases)
    for file in ['terrain-materials.jpg','terrain-repeat.jpg']:preview_record(b.PRE/file,[a['image']for a in bases],'Current12 formal base materials in actual contact/repeat layout; proportional thumbnail downsample, no new native art')
    # Keep crop/QA records true without rebuilding any other PNG.
    cp=b.REC/'terrain-source-crops.json';crop=wp.readj(cp)
    for name in materials:
        _,sources,info=b.square_material(name)
        crop['sources']=[s for s in crop['sources']if s['file']!=sources[0]['file']]+sources
        crop['nativeSourceDimensions'][name]=info['nativeSourceSize']
        for row in crop['items']:
            if row['id']==name:row.pop('quadNWES',None);row.update(info)
    crop['localizedRepairAt']=wp.now();crop['operations']=['actual native diamond crop or explicitly identified full square master','inverse2:1UV or proportional square downsample','14px periodic opposite-edge colour blend','canonical2:1 projection with1.5px render-only Alpha extrusion'];wp.writej(cp,crop)
    qa=wp.readj(b.REC/'terrain-validation.json');qa.update({'createdAt':wp.now(),'nativeMasters':len({s['file']for a in m['assets']for s in a['derivedFrom']}),'checks':m['qa'],'warnings':[q for q in m['qa']if q['level']!='OK'],'claim':'Localized family export from explicitly recorded native masters. Edge metrics do not establish visual repeat acceptance.','localizedMaterialRepair':m['localizedMaterialRepair']});wp.writej(b.REC/'terrain-validation.json',qa)
    checked=[]
    for a in m['assets']:
        if a['id']not in targets:continue
        im=Image.open(R/a['image']);checked.append({'id':a['id'],'passed':im.mode=='RGBA'and im.size==(a['width'],a['height'])and im.getchannel('A').getextrema()[0]==0 and wp.sha(R/a['image'])==a['sha256']and not a['nativeUpscale']})
    result={'schema':'localized-terrain-material-repair.v1','createdAt':wp.now(),'materials':materials,'updatedFormalImages':len(touched),'otherFormalImagesCheckedUnchanged':len(untouched),'changedOtherFormalImages':changed_others,'changedOtherAssetMetadata':changed_metadata,'manifestSHA256':wp.sha(mf),'families':evidence,'checks':checked,'failures':[c for c in checked if not c['passed']],'visualAccepted':False,'userAccepted':False,'unityValidated':False,'claim':'Only selected painted material families were reprojected. Numerical seams and mechanical checks cannot approve repeated appearance.'}
    wp.writej(b.REC/(record_name+'.json'),result)
    print(json.dumps({k:result[k]for k in ['materials','updatedFormalImages','otherFormalImagesCheckedUnchanged','failures','manifestSHA256']},ensure_ascii=False))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('materials',nargs='+',choices=sorted(b.MATERIAL_MASTERS));repair(parser.parse_args().materials)

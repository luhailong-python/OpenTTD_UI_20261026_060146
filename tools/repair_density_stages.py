"""Repair only source snow/desert density semantics, no model calls."""
from PIL import Image
import copy,json
import world_pack as wp
import build_world_terrain as b
from repair_terrain_materials import preview_record
R=wp.ROOT

def repair():
    mf=b.OUT/'manifest.json';m=wp.readj(mf);old=copy.deepcopy(m);before={a['image']:wp.sha(R/a['image'])for a in m['assets']};atlas=Image.open(R/'source-art/world/terrain-base.png').convert('RGBA');uv={};sources={}
    # These are the original inspected native atlas quads, not formal-tile
    # re-enlargement. Same UV/periodic/project operations as the full builder.
    for name,quad in {'grass':[[212,145],[412,251],[212,355],[18,251]],'bare':[[625,145],[824,251],[625,355],[431,251]],'snow':[[625,524],[824,631],[625,737],[431,631]],'desert':[[212,907],[412,1013],[212,1118],[18,1013]]}.items():
        uv[name]=b.periodic(b.unwrap(atlas,quad));sources[name]=[wp.source_record(R/'source-art/world/terrain-base.png')]
    checks=[];changed=[];pages=[]
    for name in['snow','desert']:
        family=[]
        for density in range(4):
            material,refs,extra=b.density_material(name,density,uv,sources);flat=b.project(material);seam=wp.edge_rmse(flat);images={f'terrain-{name}-density-{density}-flat':flat}
            images.update({f'terrain-{name}-density-{density}-slope-{slope}':wp.projected_slope(flat,code)[0]for code,slope in wp.SLOPES})
            operation='Actual native '+extra['compositeUnderlayMaterial']+'/'+name+' atlas UVs -> explicit'+str(extra['compositeFraction'])+' source snow/desert fraction ->14px periodic edge blend -> canonical diamond;19slope variants use piecewise-affine source-corner projection. No new native painting.'
            for a in m['assets']:
                if a['id']not in images:continue
                im=images[a['id']];path=R/a['image']
                if im.size!=(a['width'],a['height']):raise ValueError('Canvas would change')
                im.save(path);a.update(extra);a.update({'operation':operation,'derivedFrom':refs,'sha256':wp.sha(path),'photometricSeam':seam,'status':'produced-needs-visual-review','reviewBasis':'Corrected quarter-based source density; current-hash full-family visual check required','nativeUpscale':False})
                wp.writej(str(path)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'derivedAt':wp.now(),'operation':operation,'derivedFrom':refs,'tool':'repair_density_stages.py; shared density_material/periodic/project/projected_slope pipeline','width':im.width,'height':im.height,'densityStage':density,'compositeFraction':extra['compositeFraction'],'compositeUnderlayMaterial':extra['compositeUnderlayMaterial'],'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'nativeUpscale':False})
                changed.append(a['image']);family.append(a);checks.append({'id':a['id'],'sizeAlphaSHA':im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0 and wp.sha(path)==a['sha256'],'densityFraction':a['compositeFraction']==[.25,.5,.75,1.][density],'anchorUnchanged':a['anchorPx']==next(x['anchorPx']for x in old['assets']if x['id']==a['id'])})
            for q in m['qa']:
                if q['id'].split('.')[0]!=f'{name}-density-{density}':continue
                metric=q['id'].split('.')[1];q['value']=seam[metric];q['level']='OK'if seam[metric]is not None and seam[metric]<=q['threshold']else'WARN'
        if len(family)!=80:raise ValueError('Expected4stages×20')
        for start in range(0,len(family),20):
            subset=family[start:start+20];file=f'terrain-{name}-density-quarter-review-{start//20+1:02d}.jpg';b.contact(subset,file,5,192);preview_record(b.PRE/file,[a['image']for a in subset],'All20actual exports for corrected quarter-based density stage; painted pixels only, proportional thumbnails and labels');pages.append({'image':'previews/world/'+file,'sha256':wp.sha(b.PRE/file),'assetIds':[a['id']for a in subset]})
    untouched=[a['image']for a in m['assets']if a['image']not in changed];bad=[f for f in untouched if wp.sha(R/f)!=before[f]];badmeta=[a['id']for a,o in zip(m['assets'],old['assets'])if a['image']not in changed and a!=o]
    if bad or badmeta:raise ValueError('Unrelated formal terrain changed')
    m['createdAt']=wp.now();m['sourceQuarterDensityRepair']={'materials':['snow','desert'],'stages':[0,1,2,3],'fractions':[.25,.5,.75,1.],'updatedFormalImages':len(changed),'otherFormalImagesUnchanged':len(untouched),'grassAndLegacyRoughDensitySemanticsUnchanged':True};wp.writej(mf,m)
    qa=wp.readj(b.REC/'terrain-validation.json');qa.update({'createdAt':wp.now(),'checks':m['qa'],'warnings':[q for q in m['qa']if q['level']!='OK'],'sourceQuarterDensityRepair':m['sourceQuarterDensityRepair']});wp.writej(b.REC/'terrain-validation.json',qa)
    result={'schema':'source-quarter-density-repair.v1','createdAt':wp.now(),'manifestSHA256':wp.sha(mf),'updatedFormalImages':len(changed),'otherFormalImagesCheckedUnchanged':len(untouched),'changedOtherFormalImages':bad,'changedOtherAssetMetadata':badmeta,'checks':checks,'failures':[c for c in checks if not all(c[k]for k in['sizeAlphaSHA','densityFraction','anchorUnchanged'])],'reviewPages':pages,'visualAccepted':False,'userAccepted':False,'unityValidated':False,'sourceEvidence':[{'file':'reference/OpenTTD/src/table/clear_land.h','sha256':wp.sha(R/'reference/OpenTTD/src/table/clear_land.h'),'symbols':['_clear_land_sprites_snow_desert']},{'file':'reference/OpenTTD/src/clear_cmd.cpp','sha256':wp.sha(R/'reference/OpenTTD/src/clear_cmd.cpp'),'symbols':['DrawTile_Clear']}],'claim':'Correct source stage0=one quarter; no new model generation or exact per-pixel snow-covered-area claim. Fractions are explicit material blending recipes.'}
    wp.writej(b.REC/'terrain-density-quarter-repair.json',result);print(json.dumps({k:result[k]for k in['updatedFormalImages','otherFormalImagesCheckedUnchanged','failures','manifestSHA256']}))

if __name__=='__main__':repair()

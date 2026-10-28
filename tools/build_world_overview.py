"""Aggregate already produced world art. Never turns requirements into finished art."""
from pathlib import Path
from PIL import Image
import json,os,collections,copy,hashlib
import world_pack as wp
ROOT=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()

def normalize(a,source,category=None):
    a=copy.deepcopy(a)
    if a.get('authoritative') is False:return None
    if'file'in a and'image'not in a:a['image']=a['file']
    if'image'not in a:return None
    p=ROOT/a['image']
    if not p.is_file():return None
    im=Image.open(p)
    a.setdefault('id',p.stem)
    a.setdefault('category',category or p.relative_to(ROOT/'assets/world').parts[0])
    a.setdefault('width',im.width);a.setdefault('height',im.height)
    if'anchorPx'not in a:
        pivot=a.get('pivot',a.get('pivotNormalized',[.5,.5]));a['anchorPx']=a.get('pivotPixel',a.get('emitterPx',[pivot[0]*im.width,(1-pivot[1])*im.height]))
    a.setdefault('pivotUnity',[a['anchorPx'][0]/im.width,1-a['anchorPx'][1]/im.height])
    a.setdefault('sha256',wp.sha(p));a.setdefault('status','produced-needs-visual-review')
    a.setdefault('operation','see source manifest and derivation record')
    a.setdefault('nativeUpscale',False);a.setdefault('unityValidated',False)
    if a['id']=='ship-depot'and source.parent.name=='waterworks':a['packAssetId']=a['id'];a['id']='waterworks-ship-depot'
    if not a.get('derivedFrom')and a.get('sources'):
        a['derivedFrom']=[v.get('derivedFrom',v)for v in a['sources']if isinstance(v,dict)]
    a['manifestSource']=rel(source)
    return a

def gather():
    assets=[];animations=[];sources=[];issues=[];paths={};ids={}
    for p in sorted((ROOT/'assets/world').rglob('manifest.json')):
        q=load(p);sources.append({'file':rel(p),'sha256':wp.sha(p)})
        for check in q.get('qa',[]):
            if isinstance(check,dict)and check.get('level')in['WARN','FAIL']:
                issues.append({**check,'manifest':rel(p),'inheritedFromSourcePack':True})
        aa=q.get('assets',[])
        if'familyId'in q and'frames'in q:
            aa=[dict(f,id='vehicle-'+q['familyId']+'-'+f['direction'],category='vehicles',status='art-checked'if f.get('headingVerified')and f.get('identityVerified')else'produced-needs-visual-review')for f in q['frames']]
        elif q.get('frames')and isinstance(q['frames'][0],dict):
            aa=aa+[dict(f,id='frame-'+str(q.get('id',p.parent.name))+'-'+str(f.get('direction',f.get('frame',i))),category='effects'if'effects'in p.parts else'vehicles',pivot=f.get('pivot',q.get('pivot',[.5,.5])))for i,f in enumerate(q['frames'])]
            if any(f.get('durationMs')for f in q['frames'])and not any(f.get('direction')for f in q['frames']):
                animations.append({'id':'fx-'+str(q.get('id',p.parent.name)),'category':'effects','frames':[f['file']for f in q['frames']],'durationsMs':[f.get('durationMs',100)for f in q['frames']],'loop':q.get('loop',False)if len(q['frames'])>1 else False,'previewKind':'time-sequence'if len(q['frames'])>1 else'still-state','fixedAnchorPx':q.get('emitterPx',[256,256]),'method':q.get('operation','native painted frame sequence; see family record')})
        if q.get('sprites'):
            for sprite in q['sprites']:
                for state in sprite.get('states',[]):
                    aa.append(dict(state,id='vehicle-model-'+str(q.get('id'))+'-'+sprite['direction']+'-'+state.get('state','body'),category='vehicles',direction=sprite['direction'],pivot=sprite.get('pivot',[.5,.5]),derivedFrom=sprite.get('sources',[]),operation='; '.join(sprite.get('operations',['source model livery/load/hardware composition; see vehicle runtime manifest'])),livery=sprite.get('livery'),derivationRecord=rel(p)))
        for row in aa:
            if row.get('authoritative') is False:continue
            a=normalize(row,p)
            if a is None:issues.append({'level':'FAIL','manifest':rel(p),'issue':'Missing image in asset record','record':row.get('id')});continue
            if a['image']in paths:continue
            if a['id']in ids:
                issues.append({'level':'FAIL','manifest':rel(p),'issue':'duplicate-id','id':a['id'],'files':[ids[a['id']],a['image']]});continue
            paths[a['image']]=a;ids[a['id']]=a['image'];assets.append(a)
        for a in q.get('animations',[]):
            if a['id']not in {x['id']for x in animations}:animations.append(copy.deepcopy(a))
    return assets,animations,sources,issues

def source_count(assets):
    masters={}
    used=set()
    def hashes(v):
        if isinstance(v,dict):
            if v.get('sha256'):used.add(v['sha256'])
            for z in v.values():hashes(z)
        elif isinstance(v,list):
            for z in v:hashes(z)
    for a in assets:hashes(a.get('derivedFrom',[]))
    for p in list((ROOT/'source-art/world').rglob('*.generation.json'))+list((ROOT/'assets/world').rglob('*.generation.json')):
        try:q=load(p)
        except ValueError:continue
        if q.get('route')in['builtin','built-in']or q.get('tool')in['image_gen.imagegen','image_gen']:
            sha=q.get('sha256')
            if sha and sha in used and q.get('file')and(ROOT/q['file']).is_file():masters[sha]={'record':rel(p),'file':q.get('file'),'width':q.get('width'),'height':q.get('height')}
    return list(masters.values())

def coverage(assets,animations):
    from final_world_coverage import build
    return build(assets,animations)

def validate(assets,sources,issues):
    counts=collections.Counter();checks=[]
    for a in assets:
        p=ROOT/a['image'];im=Image.open(p)
        tests=[('size',im.size==(a['width'],a['height'])),('sha256',wp.sha(p)==a['sha256']),('alpha',im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0),('anchor',len(a['anchorPx'])==2 and 0<=a['anchorPx'][0]<=im.width and 0<=a['anchorPx'][1]<=im.height),('no-native-upscale',not a.get('nativeUpscale'))]
        for name,ok in tests:
            level='OK'if ok else'FAIL';counts[level]+=1
            if not ok:checks.append({'id':a['id']+'.'+name,'level':level,'file':a['image']})
        record=Path(str(p)+'.derivation.json')
        # Some family manifests embed their complete derivative provenance.
        has_record=record.is_file()or bool(a.get('derivedFrom'))
        counts['OK'if has_record else'WARN']+=1
        if not has_record:checks.append({'id':a['id']+'.provenance','level':'WARN','file':a['image']})
    for issue in issues:counts[issue['level']]+=1;checks.append(issue)
    q={'createdAt':wp.now(),'scope':'formal PNG existence, hash, dimensions, Alpha, anchor and derivative provenance; visual and Unity acceptance separate','assetCount':len(assets),'passed':counts['OK'],'failures':counts['FAIL'],'warnings':counts['WARN'],'issues':checks,'sourceManifests':sources,'unityValidated':False}
    wp.writej(ROOT/'records/world-production/world-validation.json',q);return q

def main():
    assets,animations,sources,issues=gather();masters=source_count(assets);cov=coverage(assets,animations);qa=validate(assets,sources,issues)
    pack={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'taskRoot':str(ROOT),'status':'世界资源持续制作；用户美术验收待确认','assets':assets,'animations':animations,'packSources':sources,'nativeMasters':masters,'nativeMasterCount':len(masters),'coverageSummary':f"{cov['sourceRequirements']}项上游需求中，{cov['producedMappedRows']}项已有显式资源映射；{cov['remainingRows']}项仍缺资源或映射。映射本身不代表所有状态已经验收。",'coverage':{'sourceRequirements':cov['sourceRequirements'],'mapped':cov['producedMappedRows'],'remaining':cov['remainingRows']},'projection':{'logicalTileSize':[128,64],'exportTileSize':[256,128],'logicalHeightStep':16,'exportHeightStep':32},'unityValidated':False,'qaSummary':{k:qa[k]for k in['passed','failures','warnings']}}
    wp.writej(ROOT/'docs/WORLD_ASSET_MANIFEST.json',pack)
    preview=ROOT/'previews/world/index.html'
    for a in pack['assets']:a['previewImage']=Path(os.path.relpath(ROOT/a['image'],preview.parent)).as_posix()
    for a in pack['animations']:
        a['previewFrames']=[Path(os.path.relpath(ROOT/f,preview.parent)).as_posix()for f in a.get('frames',[])]
        assembly=a.get('binding',{}).get('assemblyPreviewFrames',[])
        if assembly:a['previewAssemblyFrames']=[Path(os.path.relpath(ROOT/f,preview.parent)).as_posix()for f in assembly]
    template=(ROOT/'tools/world_preview_template.html').read_text(encoding='utf-8');preview.write_text(template.replace('__WORLD_MANIFEST__',json.dumps(pack,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
    status={'createdAt':pack['createdAt'],'taskRoot':str(ROOT),'phase':'world-art-production','uiArt':'existing UI static validation passed; user art review pending','worldArt':'in-production','formalPNGs':len(assets),'nativeMasters':len(masters),'animations':len(animations),'sourceRequirements':cov['sourceRequirements'],'explicitlyMappedRows':cov['producedMappedRows'],'remainingRows':cov['remainingRows'],'validation':pack['qaSummary'],'preview':'previews/world/index.html','manifest':'docs/WORLD_ASSET_MANIFEST.json','coverage':'docs/WORLD_DELIVERY_COVERAGE.json','unityValidated':False,'gitSubmitted':False}
    wp.writej(ROOT/'docs/WORLD_PRODUCTION_STATUS.json',status)
    print(json.dumps(status,ensure_ascii=False))
if __name__=='__main__':main()

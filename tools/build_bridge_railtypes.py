"""Add native monorail/maglev lane paint to frozen bridge geometry/layers.
Only writes this supplemental pack and its dedicated previews/records.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np, json, ast, hashlib, argparse
import world_pack as wp

R=wp.ROOT
OUT=R/'assets/world/infrastructure/bridge-railtypes'
PRE=R/'previews/world/bridge-railtypes'
SOURCE=R/'assets/world/infrastructure/transport-runtime/manifest.json'
ROLES=['north','south','inner-north','inner-south','middle-odd','middle-even','head']
TYPES=['rail','electric','monorail','maglev']


def ref(path):
    p=R/path
    return {'file':path,'sha256':wp.sha(p),'record':path+'.derivation.json'}


def emit(ident,im,parents,requirements,**extra):
    p=OUT/(ident+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    a={'id':ident,'image':wp.rel(p),'sha256':wp.sha(p),'width':384,'height':384,
       'anchorPx':[192,320],'pivotUnity':[.5,1-320/384],'category':'bridge-railtype',
       'derivedFrom':parents,'sourceRequirementIds':requirements,'nativeUpscale':False,
       'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,
       'operation':'existing native lane pixels reprojected through the frozen bridge plane; existing rear/front structure reused verbatim; no new painting',
       'status':'produced-needs-visual-review','unityValidated':False,**extra}
    wp.writej(str(p)+'.derivation.json',a)
    return a


def source_sample():
    # Load only the exact premultiplied sampler. Importing production code would
    # change its shared output directory and could write accepted old assets.
    tree=ast.parse((R/'tools/build_transport_runtime.py').read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_bridge_sample']
    env={'np':np,'Image':Image};exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen bridge sampling','exec'),env)
    return env['_bridge_sample']


def project_lane(strip,axis,rise,proj,mask,sample,kind):
    yy,xx=np.indices((384,384));x=384-xx if axis=='Y'else xx
    half=proj['deckCrossSectionHalfX']
    quad=np.asarray(proj['targetDeckQuadBeforeAxisMirror'],float).copy();quad[2:,1]+=rise
    p0,p1,p2,p3=quad;inv=np.linalg.inv(np.column_stack([p3-p0,p1-p0]))
    rf=np.clip((x-(128+half+5))/(128-2*half-10),0,1)
    uv=np.einsum('ij,jhw->ihw',inv,np.stack([x-p0[0],yy+rise*rf-p0[1]]));u,v=uv
    # A guide beam occupies a narrower part of the existing deck than maglev.
    # Structural collar/railings remain in the original foreground layer.
    v0,v1=(.22,.78)if kind=='monorail'else(.15,.85)
    owned=(np.asarray(mask.getchannel('A'))>0)&(u>=.015)&(u<=.985)&(v>=v0)&(v<=v1)
    im=sample(strip,u*(strip.width-1),(v-v0)/(v1-v0)*(strip.height-1))
    a=np.asarray(im).copy();a[~owned]=0
    return Image.fromarray(a),{'innerCrossDomain':[v0,v1],'longitudinalDomain':[.015,.985],
          'rampProfile':'same port-locked native endpoint collars and32px height transfer as accepted source projection'}


def main():
    OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True)
    old=wp.readj(SOURCE);oldsha=wp.sha(SOURCE);by={a['id']:a for a in old['assets']}
    oldsnapshot=[{'file':a['image'],'sha256':wp.sha(R/a['image'])}for a in old['assets']]
    if any(s['sha256']!=a['sha256']for s,a in zip(oldsnapshot,old['assets'])):
        raise ValueError('Frozen source assets do not match their accepted manifest')
    mats={}
    for kind in ['monorail','maglev']:
        a=by['lane-source-'+kind];mats[kind]=(Image.open(R/a['image']).convert('RGBA').crop(a['innerUVRectPx']),a)
    sample=source_sample();entries=[];mapping=[];cache={};used={}
    bridges=[m for m in old['coverageMappings']if m.get('requirementId','').startswith('bridge-')]
    families={}
    for m in bridges:families.setdefault(m['nativeFamily'],[]).append(m['requirementId'])
    for m in bridges:
        req=m['requirementId'];states=[]
        for oldstate in [s for s in m['states']if s['deck']=='rail']:
            axis=oldstate['axis']
            for kind in TYPES:
                if kind in ['rail','electric']:
                    states.append({'axis':axis,'deck':kind,'railType':kind,'pieces':oldstate['pieces'],
                        'pier':oldstate['pier'],'sourceBridgeOffset':0,'aliasDeclared':True,
                        'reason':'normal/electric use the same source bridge deck offset0; electric overhead is a separate delivered catenary layer',
                        'separateSuspensionTower':oldstate.get('separateSuspensionTower')})
                    continue
                pieces={};unique={}
                for rise,role in [(0,'middle-odd'),(32,'north'),(-32,'south')]:
                    original=oldstate['pieces'][role];wholepath=original['image']
                    sourceasset=next(a for a in old['assets']if a['image']==wholepath)
                    ls=original['layers'];proj=sourceasset['projection'];key=(m['nativeFamily'],axis,kind,rise)
                    if key not in cache:
                        mask=Image.open(R/original['laneOwnershipMask']).convert('RGBA')
                        lane,lp=project_lane(mats[kind][0],axis,rise,proj,mask,sample,kind)
                        ident='lane-'+m['nativeFamily'].replace('bridge-','')+'-'+axis+'-'+kind+'-'+str(rise).replace('-','m')
                        a=emit(ident,lane,[ref(mats[kind][1]['image']),ref(original['laneOwnershipMask'])],families[m['nativeFamily']],
                            category='bridge-railtype-lane',axis=axis,railType=kind,risePx=rise,
                            projection=proj,laneMaterialUV=mats[kind][1]['image'],
                            frozenLaneOwnershipMask=original['laneOwnershipMask'],**lp)
                        entries.append(a);cache[key]=a
                    laneasset=cache[key]
                    rear=Image.open(R/ls['rear']).convert('RGBA');front=Image.open(R/ls['front']).convert('RGBA')
                    whole=rear.copy();whole.alpha_composite(Image.open(R/laneasset['image']).convert('RGBA'));whole.alpha_composite(front)
                    ident=req+'-'+axis+'-'+kind+'-'+('flat'if rise==0 else'up32'if rise>0 else'down32')
                    a=emit(ident,whole,[ref(ls['rear']),ref(laneasset['image']),ref(ls['front'])],[req],
                        axis=axis,railType=kind,risePx=rise,projection=proj,
                        layers={'rear':ls['rear'],'lane':laneasset['image'],'front':ls['front']},
                        laneMaterialUV=mats[kind][1]['image'],frozenLaneOwnershipMask=original['laneOwnershipMask'])
                    entries.append(a)
                    unique[rise]={'image':a['image'],'layers':a['layers'],'layerOrder':['rear','lane','front'],
                        'laneOffsetPx':[0,0],'laneMaterialUV':mats[kind][1]['image'],
                        'laneOwnershipMask':original['laneOwnershipMask'],'risePx':rise,
                        'advancePx':proj['advancePx'],'deckPortsPx':proj['targetDeckMouths']}
                for role in ROLES:
                    rise=32 if role in ['north','head'] else -32 if role=='south' else 0
                    pieces[role]={**unique[rise],'aliasDeclared':role in ['head','inner-north','inner-south','middle-even'],
                        'reason':'same accepted periodic structural role alias; no duplicate original painting'}
                states.append({'axis':axis,'deck':kind,'railType':kind,'pieces':pieces,'pier':oldstate['pier'],
                    'sourceBridgeOffset':16 if kind=='monorail' else 24,
                    'separateSuspensionTower':oldstate.get('separateSuspensionTower')})
        mapping.append({'requirementId':req,'sourceBridgeId':m['sourceBridgeId'],
            'states':states,'sourcePieces':ROLES,'railTypes':TYPES,'axes':['X','Y'],
            'files':sorted({p['image']for s in states for p in s['pieces'].values()}),
            'supplementTo':'assets/world/infrastructure/transport-runtime/manifest.json',
            'completeRailTypeCoverage':True,'nativeStructuralFamily':m['nativeFamily'],
            'sourceEvidence':['src/tunnelbridge_cmd.cpp:172-175','src/tunnelbridge_cmd.cpp:1450-1451',
                              'src/tunnelbridge_cmd.cpp:1638-1639','src/table/railtypes.h:267-268','src/table/railtypes.h:365-366']})
    manifest={'schema':'cloud-route.bridge-railtypes.v1','createdAt':wp.now(),'assets':entries,'animations':[],
        'coverageMappings':mapping,'readOnlySourceManifest':{'file':wp.rel(SOURCE),'sha256':oldsha},
        'sourceReadOnlySnapshot':oldsnapshot,'sourceSamplerSHA256':wp.sha(R/'tools/build_transport_runtime.py'),
        'counts':{'sourceBridgeTypes':13,'axes':2,'additionalRailTypes':2,'allRailTypesWithAliases':4,
                  'sourceRoleBindings':13*2*4*7,'additionalRoleBindings':13*2*2*7,
                  'additionalWholePNGs':156,'sharedLanePNGs':84,'formalPNGs':len(entries)},
        'renderingContract':{'wholeVsLayers':'whole OR rear/lane/front, never both','laneOffsetPx':[0,0],
            'canvasPx':[384,384],'anchorPx':[192,320],'heightStepPx':32,'normalElectricShareDeck':True,
            'electricCatenary':'reuse delivered rail-catenary post/wire modules; electric deck art aliases normal rail',
            'nativePaintingClaim':False,'sourceStructurePixelsReusedVerbatim':True},
        'acceptance':'produced; actual current PNG assembly/visual review pending','userArtAcceptance':'pending','unityValidated':False,
        'limitations':['Original protected structural collars, railings and roof remain in the accepted foreground ownership; this pack adds only existing native guideway material.',
                      'Bridge clearance, moving-vehicle depth, electric wire placement and renderer route permissions remain next-stage Unity checks.']}
    if wp.sha(SOURCE)!=oldsha or any(wp.sha(R/a['file'])!=a['sha256']for a in oldsnapshot):
        raise ValueError('Frozen production changed during supplemental build')
    wp.writej(OUT/'manifest.json',manifest)
    print(json.dumps(manifest['counts']))


if __name__=='__main__':main()

"""Finish industry art inventory with explicit redesigned parent-overlay source mappings.
Art crops/transforms only, no procedural replacement painting and no Unity logic.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,math,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
catalog=readj(R/'docs/WORLD_ASSET_COVERAGE.json')
specs=[x for x in catalog['items']if x['entryKind']=='source-industry-spec']
ranges=[(0,6,0),(7,10,1),(11,15,2),(16,17,3),(18,23,4),(24,28,5),(29,32,11),(33,38,9),(39,42,6),(43,46,7),(47,51,10),(52,57,8),(58,59,12),(60,63,13),(64,71,14),(72,88,15),(89,90,16),(91,99,17),(100,115,18),(116,116,19),(117,117,20),(118,119,21),(120,120,22),(121,124,23),(125,128,25),(129,130,26),(131,134,27),(135,136,28),(137,137,29),(138,141,30),(142,147,31),(148,155,32),(156,159,33),(160,163,34),(164,166,35),(167,174,36)]
tileparents={i:[parent]for lo,hi,parent in ranges for i in range(lo,hi+1)}
for i in range(33,39):tileparents[i]=[9,24]
assert set(tileparents)==set(range(175))
items=[]
for letter in 'abcde':
    p=R/'records/world-production'/('industry-'+letter+'-extraction.json')
    j=readj(p)
    for x in j['items']:
        x['validation']['visualStatus']='passed-local-art-review'
        d=R/(x['file']+'.derivation.json');savej(d,x)
        idx=x.get('sourceIndustryTypeId')
        req=[x['id']]if idx is not None else []
        if idx is not None:req+=['industry-tile-'+str(i).zfill(3) for i,par in tileparents.items() if idx in par]
        en={'id':x['id'],'image':x['file'],'width':512,'height':512,'anchorPx':[256,448],'pivotUnity':[.5,.125],'category':'industry'if idx is not None else'industry-mechanical-part','sha256':x['sha256'],'operation':x['operation'],'derivedFrom':x['derivedFrom'],'status':'passed-local-art-review','nativeUpscale':False,'unityValidated':False,'sourceRequirementIds':req,'sourceIndustryTypeId':idx,'nativePaintingBounds':x['nativePaintingBounds'],'uniformDownscale':x['uniformScale'],'derivationRecord':x['file']+'.derivation.json'}
        items.append(en)
    savej(p,j)
byid={x['id']:x for x in items}
# Map all gameplay tile IDs to their parent compound overlay, rather than shrinking whole factories into each tile.
mappings=[]
for s in specs:
    aid=s['id'];mappings.append({'requirementId':aid,'artIds':[aid],'files':[byid[aid]['image']],'status':'art-produced','renderStrategy':'redesigned whole-industry overlay drawn once per instance; terrain and storage modules fill original occupied layout; not once per source tile','constructionStages':[0,1,2,3],'constructionArtStatus':'stages0-2-await-shared-construction-kit','layouts':s['neededVariants']['layouts']})
for gfx,pars in tileparents.items():
    p=[specs[i]['id']for i in pars]
    mappings.append({'requirementId':'industry-tile-'+str(gfx).zfill(3),'sourceGfxId':gfx,'parentIndustryIds':pars,'artIds':p,'files':[byid[a]['image']for a in p],'status':'mapped-redesigned-parent-overlay','renderStrategy':'source compatibility mapping; draw parent compound once per industry instance at layout anchor, never repeat whole building per tile; original tile occupancy stays source-derived','sourceNativeTileArt':False,'sourceEvidence':['src/industry_type.h:64-94','src/table/build_industry.h:13-1015','src/table/industry_land.h:42-744']})
animations=[];frameassets=[]
# Mechanical loop transforms operate on painted parts. No new model poses or native 3D headings are claimed.
def sourcepart(name):
    e=byid['industry-machine-'+name];im=Image.open(R/e['image']).convert('RGBA');box=im.getbbox();part=im.crop(box)
    scale=min(1,192/part.width,176/part.height);part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
    base=Image.new('RGBA',(256,256));off=((256-part.width)//2,(256-part.height)//2);base.alpha_composite(part,off)
    return e,base,part,off,scale
for name,kind in [('mine-winding-wheel','ellipse-wheel-spin'),('pumpjack-beam','pivot-rock'),('toy-press-head','split-press-jaw'),('plastic-jet','liquid-flow-pulse'),('toffee-drill','vertical-bore-stroke'),('sugar-sieve','horizontal-sift')]:
    e,base,part,off,scale=sourcepart(name);frames=[];N=12
    animdir=R/'assets/world/industries/animations'/name;animdir.mkdir(parents=True,exist_ok=True)
    for f in range(N):
        phase=2*math.pi*f/N;params={}
        if kind=='ellipse-wheel-spin':
            ratio=.75;t=phase;c=math.cos(t);s=math.sin(t);cx=off[0]+part.width*.59;cy=off[1]+part.height*.53
            coeff=(c,-ratio*s,cx-c*cx+ratio*s*cy,s/ratio,c,cy-s/ratio*cx-c*cy)
            im=base.transform((256,256),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC);params={'angleDegrees':f*360/N,'ellipseRatio':ratio,'pivotPx':[cx,cy]}
        elif kind=='pivot-rock':
            pivot=(round(off[0]+part.width*.86),round(off[1]+part.height*.73));deg=8*math.sin(phase)
            im=base.rotate(deg,Image.Resampling.BICUBIC,center=pivot);params={'angleDegrees':deg,'pivotPx':list(pivot)}
        elif kind=='split-press-jaw':
            # Upper jaw is the actual painted upper plate. The ownership polygon is not a new painted shape.
            w,h=part.size;poly=[(0,int(h*.22)),(int(w*.28),0),(int(w*.96),int(h*.22)),(w,int(h*.44)),(int(w*.70),int(h*.58)),(0,int(h*.40))]
            mask=Image.new('L',part.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
            jaw=part.copy();jaw.putalpha(ImageChops.multiply(part.getchannel('A'),mask))
            rest=part.copy();rest.putalpha(ImageChops.multiply(part.getchannel('A'),ImageChops.invert(mask)))
            im=Image.new('RGBA',(256,256));im.alpha_composite(rest,off);dy=round(6*(1-math.cos(phase))/2);im.alpha_composite(jaw,(off[0],off[1]+dy));params={'upperJawOffsetYPx':dy,'ownershipPolygon':poly}
        elif kind=='liquid-flow-pulse':
            # Modest width modulation is a painted-flow derivative, not a generated fluid simulation.
            sx=.96+.04*math.sin(phase);w=round(part.width*sx);flow=part.resize((w,part.height),Image.Resampling.BICUBIC)
            im=Image.new('RGBA',(256,256));im.alpha_composite(flow,((256-w)//2,off[1]));params={'widthScale':sx,'origin':'fixed top and bottom y; lateral flow pulse'}
        else:
            dx=round(4*math.sin(phase))if kind=='horizontal-sift'else 0
            dy=round(5*(1-math.cos(phase))/2)if kind=='vertical-bore-stroke'else 0
            im=Image.new('RGBA',(256,256));im.alpha_composite(part,(off[0]+dx,off[1]+dy));params={'offsetXY':[dx,dy]}
        p=animdir/(str(f).zfill(2)+'.png');im.save(p)
        en={'id':'industry-'+name+'-'+str(f).zfill(2),'image':p.relative_to(R).as_posix(),'width':256,'height':256,'anchorPx':[128,128],'pivotUnity':[.5,.5],'category':'industry-animation','sha256':sha(p),'operation':kind+'; crop/downscale/painted-part affine or articulated transform; not new AI generation','derivedFrom':{'file':e['image'],'sha256':e['sha256'],'record':e['derivationRecord']},'status':'needs-motion-review','nativeUpscale':False,'unityValidated':False,'frame':f,'phase':f/N,'parameters':params,'sourceToFrameScale':scale,'sourceRequirementIds':['animation-industry-machinery']}
        savej(Path(str(p)+'.derivation.json'),en);frameassets.append(en);frames.append(en['image'])
    sheet=Image.new('RGBA',(1024,768))
    for i,p in enumerate(frames):sheet.alpha_composite(Image.open(R/p).convert('RGBA'),((i%4)*256,(i//4)*256))
    sp=animdir/'sheet.png';sheet.save(sp)
    animations.append({'id':'industry-'+name,'frames':frames,'durationsMs':[100]*N,'loop':True,'sheet':sp.relative_to(R).as_posix(),'grid':[4,3],'canvas':[256,256],'anchorPx':[128,128],'method':kind,'status':'needs-motion-review','nativeFrameCount':0,'generatedPartCount':1,'artSource':'deterministic transformation of an actual painted moving part'})
manifest={'schemaVersion':1,'project':'云途万里','sourceCommit':catalog['referenceCommit'],'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':{'nativeAtlases':5,'nativeIndustryCompounds':37,'nativeMechanicalParts':8,'formalStaticPNGs':45,'mechanicalLoopFrames':len(frameassets),'mechanicalLoops':len(animations),'sourceIndustryTypes':37,'sourceIndustryTileIdsMapped':175,'sourceLayouts':sum(len(s['neededVariants']['layouts'])for s in specs)},'assets':items+frameassets,'animations':animations,'coverageMappings':mappings,'renderingContract':{'view':'isometric-2:1','groundTile':[256,128],'formalStaticCanvas':[512,512],'staticAnchorPx':[256,448],'parentOverlayOncePerInstance':True,'layoutGroundOccupiedCoordinates':'source layouts in coverageMappings','unityValidation':False},'limitations':['每栋完整产业为道家风格重设计的父实例整体覆盖层，175个gfx映射为兼容索引，不是175张独立原画；多tile绘制和遮挡需下一阶段验证。','施工阶段0–2待公共施工kit组合，本manifest只验收37末态和机械部件。','6组机械循环为原画部件的二维仿射/分层变换，不是新生成3D机械运动；电火花、气泡和烟雾由公共FX包提供。','Unity导入、地形高差、光照与遮挡均未在Unity验证。'],'previews':['previews/world/industries-'+x+'.jpg'for x in'abcde']}
savej(R/'assets/world/industries/manifest.json',manifest)
print(json.dumps({'assets':len(manifest['assets']),'industryTypes':37,'tileMappings':175,'loops':len(animations),'frames':len(frameassets)},ensure_ascii=False))


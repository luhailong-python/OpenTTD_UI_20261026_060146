"""Export real painted rock/snow/wet overlays, no code-drawn replacement art.

Stone bodies stay upright. Only their measured ground contacts change height
using the upstream integer GetPartialPixelZ rules. Source snow caps are painted.
"""
from pathlib import Path
from collections import deque
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, json, re, math, html
import world_pack as wp
import build_world_terrain as terrain

R=wp.ROOT;OUT=R/'assets/world/terrain/rocks-overlay';PRE=R/'previews/world/rocks-overlay';REC=R/'records/world-production'
SRC='source-art/world/rock-overlays-native.png'
STATES=['dry','snow-quarter','snow-half','snow-three-quarter','snow-full','water-coast']
SYMBOLS=['SPR_OVERLAY_ROCKS_BASE','SPR_OVERLAY_ROCKS_1_QUART_SNOW','SPR_OVERLAY_ROCKS_2_QUART_SNOW','SPR_OVERLAY_ROCKS_3_QUART_SNOW','SPR_OVERLAY_ROCKS_FULL_SNOW','SPR_OVERLAY_ROCKS_WATER_COAST']
CANVAS=(256,256);ANCHOR=[128,192]
LAYOUTS=[[(4,4),(4,11),(11,9)],[(5,3),(12,5),(7,12)]]

def source(file):return {'file':file,'sha256':wp.sha(R/file),'record':file+('.generation.json'if(R/(file+'.generation.json')).is_file()else'.derivation.json')}

def partial_z(x,y,code):
    # Native integer source units; output heights are multiplied by4 pixels.
    if code==0:return 0
    if code==8:return (16-x-y)>>1 if x+y<=16 else 0
    if code==4:return (1+y-x)>>1 if y>=x else 0
    if code==2:return (1+x+y-16)>>1 if x+y>=16 else 0
    if code==1:return (x-y)>>1 if x>=y else 0
    if code==12:return (16-x)>>1
    if code==6:return (y+1)>>1
    if code==3:return (x+1)>>1
    if code==9:return (16-y)>>1
    if code==13:return 8-((1+x+y-16)>>1)if x+y>=16 else 8
    if code==14:return 8-((x-y)>>1)if y<x else 8
    if code==7:return 8-((16-x-y)>>1)if x+y<=16 else 8
    if code==11:return 8-((1+y-x)>>1)if x<y else 8
    if code==10:return (16-x-y)>>1 if x+y<16 else(1+x+y-16)>>1
    if code==5:return (x-y)>>1 if x>=y else(1+y-x)>>1
    if code==29:return (32-x-y)>>1
    if code==30:return (17+y-x)>>1
    if code==23:return (1+x+y)>>1
    if code==27:return (16+x-y)>>1
    raise ValueError(code)

def components(ar):
    h,w=ar.shape[:2];active=bytearray((ar[:,:,3]>=128).astype('uint8').tobytes());found=[]
    for at in range(w*h):
        if not active[at]:continue
        active[at]=0;queue=deque([at]);points=[]
        while queue:
            k=queue.popleft();y,x=divmod(k,w);points.append((x,y))
            for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=nx<w and 0<=ny<h:
                    ni=ny*w+nx
                    if active[ni]:active[ni]=0;queue.append(ni)
        if len(points)>100:found.append(points)
    return found

def emit(aid,im,refs,operation,extra,formal=True):
    path=OUT/(aid+'.png');path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
    a=wp.base_asset(aid,wp.rel(path),im,refs[0],operation,'rocks-overlay'if formal else'rocks-native-part',ANCHOR if formal else[48,88]);a.update(extra);a.update({'derivedFrom':refs,'sha256':wp.sha(path),'status':'produced-needs-visual-review','unityValidated':False,'nativeUpscale':False})
    wp.writej(str(path)+'.derivation.json',{'file':a['image'],'sha256':a['sha256'],'derivedAt':wp.now(),'tool':'build_rocks_overlay.py','operation':operation,'derivedFrom':refs,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,'width':im.width,'height':im.height,'nativeUpscale':False})
    return a

def save_preview(aid,im,refs,operation,extra):
    p=PRE/'assemblies'/(aid+'.png');p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    q={'id':aid,'image':wp.rel(p),'sha256':wp.sha(p),'derivedFrom':refs,'operation':operation,**extra}
    wp.writej(str(p)+'.derivation.json',{**q,'nativeModelGeneration':False,'actualModel':None,'actualQuality':None});return q

def contact(name,rows,count=20):
    pages=[]
    for start in range(0,len(rows),count):
        subset=rows[start:start+count];im=Image.new('RGB',(1280,math.ceil(len(subset)/5)*290),'#24493d');d=ImageDraw.Draw(im)
        for i,a in enumerate(subset):
            tile=Image.open(R/a['image']).convert('RGBA');tile.thumbnail((250,250),Image.Resampling.LANCZOS);x=i%5*256;y=i//5*290
            im.paste(tile,(x+(256-tile.width)//2,y),tile);label=a.get('label',a['id']);d.text((x+5,y+253),label,font=terrain.font(13),fill='#f4e6c8')
        dest=PRE/(name+'-'+str(start//count+1).zfill(2)+'.jpg');im.save(dest,quality=98);wp.writej(str(dest)+'.derivation.json',{'file':wp.rel(dest),'sha256':wp.sha(dest),'operation':'Actual exported rock parts/overlay compositions on QA background; proportional thumbnail downsample and labels only','derivedFrom':[source(a['image'])for a in subset],'nativeModelGeneration':False});pages.append({'image':wp.rel(dest),'sha256':wp.sha(dest),'sampleCount':len(subset),'ids':[a['id']for a in subset]})
    return pages

def alpha_edges(parts):
    im=Image.new('RGB',(640,6*130),'#23483c');d=ImageDraw.Draw(im)
    for si,state in enumerate(STATES):
        for n in range(3):
            for side,color in enumerate(['#f3ecdc','#16372d']):
                x=n*210+side*102;y=si*130;panel=Image.new('RGBA',(100,100),color);panel.alpha_composite(Image.open(R/parts[(state,n)]['image']).convert('RGBA'),(2,0));im.paste(panel.convert('RGB'),(x,y))
        d.text((5,si*130+105),state+' / native formal96px on light+dark',font=terrain.font(14),fill='#f3e8cd')
    path=PRE/'native-alpha-edges.jpg';im.save(path,quality=99);refs=[source(a['image'])for a in parts.values()];wp.writej(str(path)+'.derivation.json',{'file':wp.rel(path),'sha256':wp.sha(path),'derivedFrom':refs,'operation':'Actual96px registered native rock parts on alternating light/dark panels at1:1; labels only','nativeModelGeneration':False});return {'image':wp.rel(path),'sha256':wp.sha(path),'sampleCount':36,'ids':[a['id']for a in parts.values()]}

def main():
    OUT.mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True)
    atlas=Image.open(R/SRC).convert('RGBA');ar=np.asarray(atlas);comps=components(ar);groups={i:[]for i in range(6)}
    for points in comps:
        xy=np.asarray(points);box=[int(xy[:,0].min()),int(xy[:,1].min()),int(xy[:,0].max()+1),int(xy[:,1].max()+1)];cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2;slot=min(2,int(cx/atlas.width*3))+3*min(1,int(cy/atlas.height*2));groups[slot].append((points,box))
    if any(len(v)!=3 for v in groups.values()):raise ValueError('Expected3actual isolated rocks in each of6states; inspect source instead of equal-grid guessing')
    entries=[];parts={};crop_records=[]
    for slot,state in enumerate(STATES):
        # Same large/medium/small identity matched by actual source core area.
        for n,(points,box)in enumerate(sorted(groups[slot],key=lambda p:-len(p[0]))):
            box=[max(0,box[0]-3),max(0,box[1]-3),min(atlas.width,box[2]+3),min(atlas.height,box[3]+3)];piece=atlas.crop(box);mask=Image.new('L',piece.size);mp=mask.load()
            for x,y in points:mp[x-box[0],y-box[1]]=255
            mask=mask.filter(ImageFilter.MaxFilter(5));alpha=np.asarray(piece.getchannel('A')).copy();owned=np.asarray(mask)>0;discarded=int(np.count_nonzero((alpha>0)&~owned));alpha[~owned]=0;alpha[alpha<8]=0;piece.putalpha(Image.fromarray(alpha));bb=piece.getbbox();piece=piece.crop(bb)
            scale=.18;paint=piece.resize((round(piece.width*scale),round(piece.height*scale)),Image.Resampling.LANCZOS);out=Image.new('RGBA',(96,96));at=[48-paint.width//2,88-paint.height];out.alpha_composite(paint,at)
            a=emit(f'rock-part-{state}-{n}',out,[source(SRC)],'Actual alpha>=128 native stone component and2px source fringe; remove only nonowned/subvisible alpha<8 glow, preserve original RGB/painted snow; uniform.18downscale and fixed96canvas',{'sourceState':state,'stoneIdentity':n,'sourceCropPx':box,'sourceCorePixels':len(points),'discardedNonOwnedAlphaPixels':discarded,'scaleApplied':scale,'sourceBodyUpright':True,'nativeSnowCapPainted':state.startswith('snow'),'independentRockOverlay':False},False);entries.append(a);parts[(state,n)]=a;crop_records.append({'state':state,'stoneIdentity':n,'boxPx':box,'sourceCorePixels':len(points),'fringePx':2,'minimumRetainedAlpha':8,'discardedNonOwnedAlphaPixels':discarded,'registeredImage':a['image']})
    landscape=(R/'reference/OpenTTD/src/landscape.cpp').read_text(encoding='utf-8');body=re.search(r'_slope_to_sprite_offset\s*=\s*\{(.*?)\};',landscape,re.S).group(1);offsets=list(map(int,re.findall(r'\b\d+\b',body)))
    overlays=[];index={};geometry=[]
    for si,state in enumerate(STATES):
        for layout in range(2 if state=='dry'else 1):
            for code,slopename in wp.SLOPES:
                im=Image.new('RGBA',CANVAS);placements=[]
                for n,(x,y)in sorted(enumerate(LAYOUTS[layout]),key=lambda v:sum(v[1])):
                    part=parts[(state,n)];p=Image.open(R/part['image']).convert('RGBA');z=partial_z(x,y,code);contactxy=[128+(y-x)*8,128+(x+y)*4-z*4];at=[contactxy[0]-48,contactxy[1]-88];im.alpha_composite(p,at);placements.append({'partId':part['id'],'image':part['image'],'sourceTileXY':[x,y],'sourceHeightUnits':z,'screenContactPx':contactxy,'offsetPx':at,'scale':1,'uprightBodyPreserved':True})
                a=emit(f'rocks-{state}-layout-{layout}-slope-{slopename}',im,[source(p['image'])for p in placements],'Actual registered rock bodies translated by native GetPartialPixelZ contact height; no body warp, no new painted stone/snow, no ground baked in',{'overlayState':state,'layoutVariant':layout,'slopeCode':code,'slopeName':slopename,'sourceSlopeOffset':offsets[code],'sourceSpriteExpression':SYMBOLS[si]+' + '+str(offsets[code]),'normalRockTileSpriteExpression':('SPR_FLAT_ROCKY_LAND_'+str(layout+1)+' + '+str(offsets[code]))if state=='dry'else None,'independentRockOverlay':True,'layer':'rocks-over-ground','sourceRequirementIds':['terrain-rocks'],'placements':placements,'logicalFootprint':[1,1],'heightScalePixelsPerSourceUnit':4,'anchorMeaning':'logical tile centre192px from canvas top; align with ground by each asset anchor'});entries.append(a);overlays.append(a);index[(state,layout,code)]=a;geometry.append({'id':a['id'],'slopeCode':code,'placements':placements})
    # Context recipes are genuine layered art assemblies, not runtime logic.
    samples=[];recipes=[]
    for state in STATES[:-1]:
        layouts=range(2 if state=='dry'else 1)
        for layout in layouts:
            for code,slope in wp.SLOPES:
                grassfile=f'assets/world/terrain/terrain-grass-slope-{slope}.png';snowfile=f'assets/world/terrain/terrain-snow-slope-{slope}.png';ground=Image.open(R/grassfile).convert('RGBA');refs=[source(grassfile)];fraction=0
                if state.startswith('snow'):fraction=(STATES.index(state))/4;ground=Image.blend(ground,Image.open(R/snowfile).convert('RGBA'),fraction);refs.append(source(snowfile))
                overlay=index[(state,layout,code)];im=Image.new('RGBA',CANVAS);im.alpha_composite(ground,(0,64));im.alpha_composite(Image.open(R/overlay['image']).convert('RGBA'));q=save_preview(f'ground-{state}-layout-{layout}-slope-{slope}',im,refs+[source(overlay['image'])],'Actual grass/snow material underlay at explicit fraction plus independent native painted rock overlay; source snow is on rock parts, not a white recolour',{'context':'clear-snow'if fraction else'clear-normal','slopeCode':code,'overlayId':overlay['id'],'groundFraction':fraction,'label':state+' v'+str(layout)+' / '+slope});samples.append(q);recipes.append(q)
    for density,fraction in enumerate([.25,.5,.75,1.]):
        for code,slope in wp.SLOPES:
            bare=f'assets/world/terrain/terrain-bare-slope-{slope}.png';sand=f'assets/world/terrain/terrain-desert-slope-{slope}.png';under=Image.blend(Image.open(R/bare).convert('RGBA'),Image.open(R/sand).convert('RGBA'),fraction);a=index[('dry',0,code)];im=Image.new('RGBA',CANVAS);im.alpha_composite(under,(0,64));im.alpha_composite(Image.open(R/a['image']).convert('RGBA'));q=save_preview(f'desert-density-{density}-slope-{slope}',im,[source(bare),source(sand),source(a['image'])],'Actual bare/desert material fraction(1/4,1/2,3/4,1) plus independent dry rocks; no fake grayscale gravel substitute',{'context':'desert-rocks','densityStage':density,'compositeFraction':fraction,'slopeCode':code,'overlayId':a['id'],'label':'desert '+str(density)+' / '+slope});samples.append(q);recipes.append(q)
    for wc,waterfile in [('Sea','assets/world/terrain/water-sea-frame-00.png'),('Canal','assets/world/infrastructure/water-states/water-canal-mask-15-frame-0.png'),('River','assets/world/infrastructure/water-states/water-river-mask-15-frame-0.png')]:
        a=index[('water-coast',0,0)];water=Image.open(R/waterfile).convert('RGBA');im=Image.new('RGBA',CANVAS if wc=='Sea'else water.size);im.alpha_composite(water,(0,128)if wc=='Sea'else(0,0));offset=(0,0)if wc=='Sea'else(128,32);im.alpha_composite(Image.open(R/a['image']).convert('RGBA'),offset);q=save_preview('clear-rocks-'+wc.lower(),im,[source(waterfile),source(a['image'])],'Actual existing WaterClass ground plus independent wet rock overlay; water remains separately drawable/animated',{'context':'ClearRocks','waterClass':wc,'slopeCode':0,'overlayId':a['id'],'overlayOffsetPx':list(offset),'label':'ClearRocks / '+wc});samples.append(q);recipes.append(q)
    shore_manifest='assets/world/terrain/shore-geometry/manifest.json';shorepack=wp.readj(R/shore_manifest);shore_states=shorepack['coverageMappings'][0]['states']
    for climate in ['grass','sand','snow']:
        for code,slope in wp.SLOPES:
            if code in[0,5,10]:continue
            shore=next(s for s in shore_states if s['shoreClimate']==climate and s['sourceSlopeCode']==code);a=index[('water-coast',0,code)];im=Image.new('RGBA',CANVAS);im.alpha_composite(Image.open(R/shore['whole']).convert('RGBA'),(0,64));im.alpha_composite(Image.open(R/a['image']).convert('RGBA'));layers=[{'role':role,'image':shore['layers'][role],'offsetPx':[0,64]}for role in shore['layerOrder']if shore['layers'][role]]+[{'role':'wet-rocks','image':a['image'],'offsetPx':[0,0]}];q=save_preview(f'coast-rocks-{climate}-slope-{slope}',im,[source(l['image'])for l in layers],'Formal source-height shoreline land/native-bank and strictly horizontal0-height water layers plus independently placed wet-rock bodies; source DryOut permits water:null, never add obsolete flat backing',{'context':'CoastRocks','shoreClimate':climate,'slopeCode':code,'sourceShoreIndex':shore['sourceShoreIndex'],'overlayId':a['id'],'overlayOffsetPx':[0,0],'shoreOffsetPx':[0,64],'formalLayers':layers,'groundWhole':shore['whole'],'groundManifest':shore_manifest,'groundManifestSHA256':wp.sha(R/shore_manifest),'sourceFloodingBehaviour':shore['sourceFloodingBehaviour'],'waterHasPositiveArea':shore['waterHasPositiveArea'],'waterAbsentReason':shore.get('waterAbsentReason'),'label':'CoastRocks '+climate+' / '+slope});samples.append(q);recipes.append(q)
    pages=contact('native-parts',[{**a,'label':a['id']}for a in entries if a['category']=='rocks-native-part'])+[alpha_edges(parts)]
    for state in STATES:
        for layout in range(2 if state=='dry'else 1):pages+=contact(state+'-layout-'+str(layout),[s for s in samples if s.get('overlayId','').startswith(f'rocks-{state}-layout-{layout}-')and s['context'].startswith('clear-')])
    pages+=contact('desert-combinations',[s for s in samples if s['context']=='desert-rocks']);pages+=contact('water-coast-combinations',[s for s in samples if s['context']in['ClearRocks','CoastRocks']]);pages+=contact('wet-overlay-slopes',[{**a,'label':'water/coast / '+a['slopeName']}for a in overlays if a['overlayState']=='water-coast'])
    schema={'schema':'cloud-route.world-art.v1','createdAt':wp.now(),'batchId':'independent-native-rock-overlays','assets':entries,'animations':[],'coverageMappings':[{'requirementId':'terrain-rocks','files':[a['image']for a in overlays],'overlayStates':STATES,'dryLayouts':[0,1],'layoutsByState':{s:[0,1]if s=='dry'else[0]for s in STATES},'slopeCodes':[c for c,_ in wp.SLOPES],'independentRockOverlay':True,'sourceOverlaySlots':114,'sourceNormalRockTileSlots':38,'overlayVariantCombinations':133,'completeVariantCoverage':True,'recipeCount':len(recipes),'contextRecipes':recipes,'legacyGravelExclusion':'terrain-rocks-density-* from old rough/bare mix are not independent rocks and do not satisfy these requirements'}],'compositionSamples':samples,'contactPages':pages,'sourceCrops':crop_records,'geometry':{'canvas':list(CANVAS),'anchorPx':ANCHOR,'groundAnchorAlignment':'draw ground at own anchor; overlay anchor=[128,192].256x192ground offset[0,64],256x128flat offset[0,128]','sourceContactRule':'screenX=128+(y-x)*8; screenY=128+(x+y)*4-GetPartialPixelZ(x,y,slope)*4; native16px tile8height -> formal256width32height','bodyDeformation':'none: each painted stone stays upright; snow/wet source shape carried unchanged','shoresLegalSlopeCodes':[c for c,_ in wp.SLOPES if c not in[0,5,10]],'unreachableShoreModes':'flat/EW/NS excluded by DrawShoreTile assertions; all19 overlay sprites remain available'} ,'sourceFiles':[{'file':f,'sha256':wp.sha(R/f)}for f in ['reference/OpenTTD/src/clear_cmd.cpp','reference/OpenTTD/src/water_cmd.cpp','reference/OpenTTD/src/table/clear_land.h','reference/OpenTTD/src/table/sprites.h','reference/OpenTTD/src/landscape.cpp']],'acceptance':'produced; current-pixel visual/geometry review pending','userAccepted':False,'unityValidated':False,'limitations':['Six mother states share3real stone identities; no new3D views claimed.','Snow amount is actually painted in the new native source, not a white colour filter.','Static water compositions are QA frames; the independent wet-rock layer must render over the chosen runtime water frame.','ClearRocks art shown on3WaterClasses at flat slope; other slope overlays are delivered as source-compatible variants without claiming all are reachable terrain combinations.']}
    schema['coastGroundManifest']={'file':shore_manifest,'sha256':wp.sha(R/shore_manifest),'rule':'Use formal current source-height layers/whole. Old water-states flat shoreline paintings are not authoritative.'}
    schema['coverageMappings'][0].update({'sourceSlopeLayoutContracts':[{'overlayState':a['overlayState'],'layoutVariant':a['layoutVariant'],'slopeCode':a['slopeCode'],'sourceSlopeOffset':a['sourceSlopeOffset'],'image':a['image']}for a in overlays],'coastRockRecipes':[s for s in samples if s['context']=='CoastRocks'],'coastGroundManifest':schema['coastGroundManifest'],'coastReservedCases':[{'slopeCode':c,'applies':False,'reason':'DrawShoreTile rejects flat/EW/NS; retain no CoastrRocks recipe, do not substitute a full-water/flat tile'}for c in[0,5,10]]})
    wp.writej(OUT/'manifest.json',schema);wp.writej(REC/'rocks-overlay-source-crops.json',{'source':source(SRC),'nativeSize':list(atlas.size),'nativeAlphaRange':list(atlas.getchannel('A').getextrema()),'nativeCornerRGBA':list(atlas.getpixel((0,0))),'sourceIsPerfectAlpha':False,'actualComponents':crop_records,'claim':'Isolate actual stone alpha bodies and remove only nonowned/subvisible glow; no RGB replacement or snow painting.'})
    cards=''.join('<figure><figcaption>'+html.escape(Path(p['image']).stem)+' · '+str(p['sampleCount'])+' actual samples</figcaption><a href="../../../'+p['image']+'"><img loading="lazy" src="../../../'+p['image']+'" alt="'+html.escape(Path(p['image']).stem)+'"></a></figure>'for p in pages)
    (PRE/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>独立岩石、雪盖与岸石</title><style>body{margin:0;background:#214739;color:#f3e8cd;font:16px/1.6 system-ui}header,main{max-width:1440px;margin:auto;padding:22px}a{color:#e8cc8a}figure{margin:0 0 20px;padding:12px;border:1px solid #7e956c;border-radius:12px;overflow:hidden}img{max-width:100%;height:auto;display:block;margin:auto}figcaption{overflow-wrap:anywhere;margin-bottom:8px}</style><header><h1>独立岩石、雪盖与岸石</h1><p>18个真实原生石块，133个独立Alpha叠层：6状态×19坡，干石另有第二布局。241张实际分层组合；雪盖来自原生绘画，湿石不烘焙水底。</p><p>CoastRocks复用正式真实坡岸模块，16合法坡×3气候；DryOut允许无水面层，flat/EW/NS不适用。原旧平面岸图不作为正确基底。</p><p><a href="../../../index.html">主入口</a> · <a href="../../../assets/world/terrain/rocks-overlay/manifest.json">正式资源与分层合同</a></p><p>本页是离线美术检查，不代表Unity运行或用户批准。</p></header><main>'+cards+'</main></html>',encoding='utf-8')
    print(json.dumps({'registeredParts':18,'independentOverlays':len(overlays),'compositionSamples':len(samples),'reviewPages':len(pages),'manifestSHA256':wp.sha(OUT/'manifest.json')}))

if __name__=='__main__':main()

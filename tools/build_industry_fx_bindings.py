"""Attach existing painted FX to two missing native industry draw paths.
No new painting. Keep the six accepted mechanical rigs unchanged.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFont
import json, math, hashlib
import numpy as np
import world_pack as wp

R=wp.ROOT
MP=R/'assets/world/industries/manifest.json'
OUT=R/'assets/world/industries/bindings'
PRE=R/'previews/world/industry-assembly'
NEW={'industry-coal-plant-sparks','industry-bubble-generator-cycle'}


def ref(p):
    return {'file':wp.rel(p),'sha256':wp.sha(p),'record':wp.rel(p)+'.derivation.json'}


def emit(ident,im,p,parents,operation,**extra):
    p.parent.mkdir(parents=True,exist_ok=True)
    im.save(p)
    a={'id':ident,'image':wp.rel(p),'width':im.width,'height':im.height,
       'anchorPx':[256,448],'pivotUnity':[.5,.125],'category':'industry-bound-animation',
       'sha256':wp.sha(p),'operation':operation,'derivedFrom':parents,
       'status':'needs-attached-particle-review','nativeUpscale':False,'unityValidated':False,
       'nativeModelGeneration':False,'actualModel':None,'actualQuality':None,**extra}
    wp.writej(str(p)+'.derivation.json',a)
    return a


def placed_fx(path,center,width):
    im=Image.open(path).convert('RGBA')
    # Lifetime frames share the same FX canvas/pivot. Do not recenter by Alpha.
    resized=im.resize((width,width),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(512,512))
    out.alpha_composite(resized,(round(center[0]-width/2),round(center[1]-width/2)))
    return out


def main():
    m=wp.readj(MP)
    by={a['id']:a for a in m['assets'] if a['category']=='industry'}
    oldnew=[b for b in m['mechanismBindings'] if b['animationId'] in NEW]
    oldfiles={b['cleanBaseImage'] for b in oldnew}
    oldfiles.update(f for a in m['animations'] if a['id'] in NEW for f in a['frames'])
    m['assets']=[a for a in m['assets'] if a['image'] not in oldfiles]
    m['animations']=[a for a in m['animations'] if a['id'] not in NEW]
    m['mechanismBindings']=[b for b in m['mechanismBindings'] if b['animationId'] not in NEW]
    fxbase=R/'assets/world/effects'
    defs=[
       {'id':'industry-coal-plant-sparks','parent':'industry-01-power-station',
        'newRequirement':'animation-industry-power-sparks',
        'source':['src/industry_cmd.cpp:309-320','src/table/sprites.h:1315'],
        'description':'actual shared electric-spark paintings downsampled at the visible right-hand copper transformer; active pulse only, source inactive state draws no overlay',
        'frames':[(fxbase/'electric-spark'/f'{i:02d}.png',[389,292],76,'active-spark')
                  for i in [0,1,2,3,4,5,4,3,2,1,0,1]],
        'sourceStateMap':{'0':'no overlay','1..6':'electric-spark source keys0..5','7+':'no overlay'},
        'removeBakedParticles':False},
       {'id':'industry-bubble-generator-cycle','parent':'industry-34-bubble-generator',
        'newRequirement':'animation-industry-bubble-generator',
        'source':['src/industry_cmd.cpp:285-290','src/table/sprites.h:1309-1310'],
        'description':'three baked floating bubble silhouettes removed from parent Alpha; existing shared bubble generation/float/burst paintings emit above the actual vessel rim, rise and burst; small fixed foam in vessel stays static',
        'frames':[(fxbase/'bubble-generation'/f'{i:02d}.png',[262,174-i*2],74,'generation')for i in range(4)]
              +[(fxbase/'bubble-float'/f'{i:02d}.png',[266+j*5,160-j*11],82,'float')for j,i in enumerate([0,1,2,1])]
              +[(fxbase/'bubble-burst'/f'{i:02d}.png',[283,116],82,'burst')for i in range(4)],
        'sourceStateMap':{'uncompleted':'no emitted particle; vessel remains static',
                          'completed source draw frame':'spawned bubble height uses source animation offset; exact game tick adapter pending',
                          'EV_BUBBLE':'shared lifetime generation, float, burst phases; not new native frames'},
        'removeBakedParticles':True}]
    checks,bindings,newassets=[],[],[]
    for d in defs:
        parent=by[d['parent']]
        original=Image.open(R/parent['image']).convert('RGBA')
        removed=Image.new('L',original.size)
        if d['removeBakedParticles']:
            dr=ImageDraw.Draw(removed)
            # Actual isolated native bubble silhouettes; metal pipes/rim below
            # remain untouched. Mask only owns preexisting painted pixels.
            for box in [(186,112,226,152),(250,87,324,160),(314,126,370,183)]:
                dr.ellipse(box,fill=255)
        clean=original.copy()
        clean.putalpha(ImageChops.multiply(original.getchannel('A'),ImageChops.invert(removed)))
        directory=OUT/d['id'][9:]
        prerefs=[ref(R/parent['image'])]
        ce=emit(d['id']+'-clean-base',clean,directory/'clean-base.png',prerefs,
            'original native parent pixels; '+('Alpha-only removal of three isolated baked floating bubbles, no inpainting or fabricated hidden pixels'
            if d['removeBakedParticles']else'exact unchanged parent copy: no baked spark exists to remove'),
            category='industry-animation-clean-base',parentArtId=parent['id'],
            sourceRequirementIds=parent['sourceRequirementIds'],bakedParticleRemoval=d['removeBakedParticles'])
        newassets.append(ce)
        framepaths,assembled,phaserecords=[],[],[]
        union=Image.new('L',(512,512))
        for fi,(fxpath,center,width,stage) in enumerate(d['frames']):
            frame=placed_fx(fxpath,center,width)
            union=ImageChops.lighter(union,frame.getchannel('A'))
            entry=emit(d['id']+f'-bound-{fi:02d}',frame,directory/'moving'/f'{fi:02d}.png',
                [ref(fxpath)],'existing shared native lifetime FX; fixed-pivot proportional downsample and translation into parent512 coordinates; no new painted frame',
                sourceRequirementIds=['animation-industry-machinery',d['parent']],
                frame=fi,parentArtId=parent['id'],particlePhase=stage,
                particleOriginPx=center,sharedFXSource=wp.rel(fxpath),
                sourceCanvasScale=width/512,sourceFrameCanvas=[512,512])
            newassets.append(entry)
            framepaths.append(entry['image'])
            full=clean.copy();full.alpha_composite(frame);assembled.append(full)
            pp=PRE/d['id'][9:]/f'{fi:02d}.png'
            emit('preview-'+d['id']+'-'+str(fi),full,pp,[ref(R/ce['image']),ref(R/entry['image'])],
                 'exact parent clean-base plus positioned particle layer; preview only, no native image generation')
            phaserecords.append({'frame':fi,'phase':stage,'particleOriginPx':center,'sharedFXSource':wp.rel(fxpath)})
            outside=np.asarray(frame.getchannel('A'))==0
            checks.append({'id':d['id']+f'.frame{fi}.fixed-parent',
                'passed':bool(np.array_equal(np.asarray(full)[outside],np.asarray(clean)[outside]))})
        # Whole-assembly ownership covers every changed pixel, including old
        # pose deletion. The separate removal mask alone controls clean-base
        # deletion: do not cut the plant using the broader ownership envelope.
        changed=ImageChops.difference(original.getchannel('A'),clean.getchannel('A')).point(lambda x:255 if x else 0)
        union=ImageChops.lighter(union,changed)
        removep=directory/'removed-pose-mask.png';removed.convert('RGBA').save(removep)
        unionp=directory/'ownership-mask.png';union.convert('RGBA').save(unionp)
        for path,kind in [(removep,'Alpha ownership of old baked particles only; black means parent unchanged'),
                           (unionp,'all affected pixels: original-to-clean Alpha differences plus union of translated particle Alpha; not a clean-base deletion mask')]:
            wp.writej(str(path)+'.derivation.json',{'file':wp.rel(path),'sha256':wp.sha(path),
                'operation':kind,'nativeModelGeneration':False,'derivedFrom':prerefs})
        sheet=Image.new('RGBA',(2048,1536))
        for i,p in enumerate(framepaths):sheet.alpha_composite(Image.open(R/p).convert('RGBA'),((i%4)*512,(i//4)*512))
        sheetp=directory/'sheet.png';sheet.save(sheetp)
        wp.writej(str(sheetp)+'.derivation.json',{'file':wp.rel(sheetp),'sha256':wp.sha(sheetp),
            'operation':'lossless4x3 packing of12 actual positioned FX layers','nativeModelGeneration':False,
            'derivedFrom':[ref(R/p)for p in framepaths]})
        gifp=PRE/(d['id'][9:]+'.gif')
        mats=[]
        font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),14)
        contact=Image.new('RGB',(1024,840),'#244139')
        for fi,im in enumerate(assembled):
            bg=Image.new('RGBA',im.size,'#e7e1ce');bg.alpha_composite(im)
            mats.append(bg.convert('RGB'))
            t=im.resize((256,256),Image.Resampling.LANCZOS)
            plate=Image.new('RGBA',(256,256),'#e7e1ce'if fi%2==0 else'#244139');plate.alpha_composite(t)
            contact.paste(plate.convert('RGB'),(fi%4*256,fi//4*280))
            ImageDraw.Draw(contact).text((fi%4*256+5,fi//4*280+258),d['id'][9:]+f' / {fi}',font=font,fill='#a6c1a5')
        mats[0].save(gifp,save_all=True,append_images=mats[1:],duration=100,loop=0,optimize=False,disposal=2)
        cp=PRE/(d['id'][9:]+'-phases.jpg');contact.save(cp,quality=96)
        checks += [{'id':d['id']+'.clean-original-RGB','passed':clean.convert('RGB').tobytes()==original.convert('RGB').tobytes()},
                   {'id':d['id']+'.fixed-foundation','passed':all(i.crop((0,370,512,512)).tobytes()==original.crop((0,370,512,512)).tobytes()for i in assembled)},
                   {'id':d['id']+'.nonempty-motion','passed':len({hashlib.sha256(i.tobytes()).hexdigest()for i in assembled})>=6}]
        b={'animationId':d['id'],'bindingKind':'shared-particle-lifetime','parentArtId':parent['id'],
           'parentImage':parent['image'],'parentSha256':parent['sha256'],'cleanBaseArtId':ce['id'],
           'cleanBaseImage':ce['image'],'ownershipMask':wp.rel(unionp),'ownershipMaskSha256':wp.sha(unionp),
           'removedPoseMask':wp.rel(removep),'removedPoseMaskSha256':wp.sha(removep),
           'ownershipMaskMeaning':'all affected pixels: native-pose Alpha removal plus swept overlay occupancy; clean-base deletion uses only separate removedPoseMask',
           'bakedParticleRemoval':d['removeBakedParticles'],'frameCanvasPx':[512,512],
           'frameCoordinateSpace':'complete parent compound pixels; offset zero','attachmentOffsetPx':[0,0],
           'attachmentScale':1.,'parentAnchorPx':[256,448],'movingMechanismPivotPx':[256,448],
           'layerOrder':['cleanBase','movingParticle'],'mustReplaceParentStaticArt':True,
           'drawParentOriginalSimultaneously':False,'sourceEvidence':d['source'],
           'sourceStateMap':d['sourceStateMap'],'description':d['description'],
           'nativePoseGenerationClaim':False,'nativeFrameCount':0,
           'assemblyPreviewGIF':wp.rel(gifp),'assemblyPreviewFrames':[wp.rel(PRE/d['id'][9:]/f'{i:02d}.png')for i in range(12)],
           'assemblyContactSheet':wp.rel(cp),'parametersByFrame':phaserecords,'status':'needs-attached-particle-visual-review',
           'userArtAcceptance':'pending','unityValidated':False}
        bindings.append(b)
        m['animations'].append({'id':d['id'],'frames':framepaths,'durationsMs':[100]*12,'loop':True,
            'canvas':[512,512],'width':512,'height':512,'anchorPx':[256,448],
            'method':'shared native FX fixed-canvas downsample and2D lifetime translation',
            'status':'needs-attached-particle-visual-review','nativeFrameCount':0,'generatedPartCount':0,
            'sourceRequirementIds':['animation-industry-machinery',d['parent']],
            'binding':b,'assemblyPreviewGIF':wp.rel(gifp),'sheet':wp.rel(sheetp),'grid':[4,3],'cellSizePx':[512,512],
            'artSource':'existing shared FX paintings, source native keys already recorded in FX manifests',
            'replaceLayer':'cleanBase + positioned particle frame; source inactive state no overlay; never draw above baked original bubble pose'})
    m['assets']+=newassets;m['mechanismBindings']+=bindings
    types={'industry-mine-winding-wheel':'mine-head','industry-pumpjack-beam':'oil-well-pump',
        'industry-toy-press-head':'toy-factory','industry-plastic-jet':'plastic-fountain',
        'industry-toffee-drill':'toffee-quarry','industry-sugar-sieve':'sugar-mine-sieve',
        'industry-coal-plant-sparks':'power-sparks','industry-bubble-generator-cycle':'bubble-generator'}
    for binding in m['mechanismBindings']:
        binding['sourceMachineryType']=types[binding['animationId']]
    for animation in m['animations']:
        animation['sourceMachineryType']=types[animation['id']]
        animation['binding']['sourceMachineryType']=types[animation['id']]
    m['counts'].update({'mechanicalLoops':6,'mechanicalLoopFrames':72,'attachedParticleLoops':2,
        'attachedParticleFrames':24,'attachedParticleCleanBases':2,'totalAttachedBindings':8,
        'mechanicalBindingCount':6,'mechanismBindingCount':8,
        'formalSpritePNGs':len(m['assets']),'ownershipMaskDataPNGs':8,'removedParticleMaskDataPNGs':2,
        'animationSheets':8,'packagedPNGs':len(m['assets'])+18})
    m['renderingContract']['particleAttachmentContract']='two source industry particle draw paths have explicit actual parent, separate baked-pose deletion and swept-overlay masks, source inactive no-overlay state, and installed preview; existing six mechanical loops unchanged'
    order=m['renderingContract'].get('mechanicalRebuildOrder',[])
    if 'tools/build_industry_fx_bindings.py'not in order:order.insert(2,'tools/build_industry_fx_bindings.py')
    m['renderingContract']['mechanicalRebuildOrder']=order
    wp.writej(MP,m)
    wp.writej(R/'records/world-production/industry-fx-binding-validation.json',{'createdAt':wp.now(),
        'checks':checks,'passed':sum(x['passed']for x in checks),'failures':[x for x in checks if not x['passed']],
        'sourceManifests':[{'file':'assets/world/effects/'+x+'/manifest.json','sha256':wp.sha(fxbase/x/'manifest.json')}for x in ['electric-spark','bubble-generation','bubble-float','bubble-burst']],
        'newBindings':bindings,'formalSpritePNGsAdded':len(newassets),'visualReview':'pending actual installed contact and GIF inspection',
        'unityValidated':False,'userArtAcceptance':'pending'})
    print(json.dumps({'addedFormalSprites':len(newassets),'particleBindings':len(bindings),'totalAttachedBindings':len(m['mechanismBindings']),
        'checks':len(checks),'failed':sum(not x['passed']for x in checks)}))


if __name__=='__main__':main()

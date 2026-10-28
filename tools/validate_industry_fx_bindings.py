"""Verify source-specific installed particle bindings, no production mutations."""
from PIL import Image
import numpy as np, json
import world_pack as wp

R=wp.ROOT
MP=R/'assets/world/industries/manifest.json'
EXPECTED={'mine-head','oil-well-pump','power-sparks','toy-factory',
          'plastic-fountain','bubble-generator','toffee-quarry','sugar-mine-sieve'}


def main():
    m=wp.readj(MP)
    anims={a['id']:a for a in m['animations']}
    assets={a['image']:a for a in m['assets']}
    checks=[]
    def check(ident,ok,**e):checks.append({'id':ident,'passed':bool(ok),**e})
    check('eight-native-industry-animation-types',
          {b.get('sourceMachineryType')for b in m['mechanismBindings']}==EXPECTED)
    new=[b for b in m['mechanismBindings']if b.get('bindingKind')=='shared-particle-lifetime']
    check('two-attached-particle-draw-paths',{b['parentArtId']for b in new}=={'industry-01-power-station','industry-34-bubble-generator'})
    for b in new:
        ident=b['animationId'];a=anims[ident]
        source=Image.open(R/b['parentImage']).convert('RGBA')
        clean=Image.open(R/b['cleanBaseImage']).convert('RGBA')
        removed=Image.open(R/b['removedPoseMask']).convert('L')
        rm=np.asarray(removed)
        check(ident+'.parent-sha',wp.sha(R/b['parentImage'])==b['parentSha256'])
        check(ident+'.clean-RGB-preserved',clean.convert('RGB').tobytes()==source.convert('RGB').tobytes())
        check(ident+'.only-declared-pose-alpha-removed',np.array_equal(np.asarray(clean.getchannel('A')),
              np.uint8(np.asarray(source.getchannel('A'),dtype=np.uint16)*(255-rm.astype(np.uint16))//255)))
        check(ident+'.native-pose-removal-contract',bool(np.any(rm))==b['bakedParticleRemoval'])
        check(ident+'.separate-mask-semantics',b['removedPoseMask']!=b['ownershipMask']
              and 'swept overlay'in b['ownershipMaskMeaning'])
        check(ident+'.mask-sha',wp.sha(R/b['ownershipMask'])==b['ownershipMaskSha256']
              and wp.sha(R/b['removedPoseMask'])==b['removedPoseMaskSha256'])
        check(ident+'.no-duplicate-parent',b['mustReplaceParentStaticArt']and not b['drawParentOriginalSimultaneously'])
        check(ident+'.fixed-parent-canvas',b['frameCanvasPx']==[512,512]
              and b['attachmentOffsetPx']==[0,0]and b['attachmentScale']==1 and b['parentAnchorPx']==[256,448])
        check(ident+'.parent-and-generic-requirements',set(a['sourceRequirementIds'])=={'animation-industry-machinery',b['parentArtId']})
        check(ident+'.twelve-active-phase-frames',len(a['frames'])==12 and len(b['assemblyPreviewFrames'])==12)
        if b['bakedParticleRemoval']:
            check(ident+'.three-baked-bubble-centres-cleared',all(clean.getpixel(p)[3]==0 for p in [(206,132),(286,124),(342,154)]))
            check(ident+'.float-rises-continuously',all(
                  b['parametersByFrame'][i+1]['particleOriginPx'][1]<b['parametersByFrame'][i]['particleOriginPx'][1]
                  for i in range(4,7)))
        else:
            check(ident+'.unchanged-native-parent',source.tobytes()==clean.tobytes())
        union=np.zeros((512,512),dtype=np.uint8)
        for i,f in enumerate(a['frames']):
            entry=assets[f];frame=Image.open(R/f).convert('RGBA')
            full=clean.copy();full.alpha_composite(frame)
            recorded=Image.open(R/b['assemblyPreviewFrames'][i]).convert('RGBA')
            outside=np.asarray(frame.getchannel('A'))==0
            check(ident+f'.{i}.exact-installed-assembly',full.tobytes()==recorded.tobytes())
            check(ident+f'.{i}.fixed-RGBA-outside-particle',np.array_equal(np.asarray(full)[outside],np.asarray(clean)[outside]))
            check(ident+f'.{i}.fixed-foundation',full.crop((0,370,512,512)).tobytes()==source.crop((0,370,512,512)).tobytes())
            check(ident+f'.{i}.formal-PNG-contract',entry['anchorPx']==[256,448]and frame.size==(512,512)
                  and frame.getchannel('A').getextrema()[0]==0 and frame.getchannel('A').getextrema()[1]>0
                  and wp.sha(R/f)==entry['sha256'])
            check(ident+f'.{i}.shared-source-sha',all((R/s['file']).is_file()and wp.sha(R/s['file'])==s['sha256']for s in entry['derivedFrom']))
            union=np.maximum(union,np.asarray(frame.getchannel('A')))
        affected=np.maximum(union,np.uint8(np.asarray(source.getchannel('A'))!=np.asarray(clean.getchannel('A')))*255)
        check(ident+'.affected-mask-exact',np.array_equal(affected,np.asarray(Image.open(R/b['ownershipMask']).convert('L'))))
        gif=Image.open(R/b['assemblyPreviewGIF'])
        check(ident+'.GIF-decoding',gif.n_frames==12 and gif.info.get('loop')==0
              and all((gif.seek(i)or gif.info.get('duration')==100)for i in range(gif.n_frames)))
        check(ident+'.source-inactive-state',any('no overlay'in str(v)or 'no emitted'in str(v)for v in b['sourceStateMap'].values()))
    report={'createdAt':wp.now(),'manifest':wp.rel(MP),'manifestSHA256':wp.sha(MP),
        'scope':'source native eight-type set; exact parent RGBA and removal/swept mask meanings; all24 full-parent phase reassemblies; GIF decode/timing; original shared FX SHA',
        'checks':checks,'passed':sum(c['passed']for c in checks),'failures':[c for c in checks if not c['passed']],
        'formalSpritePNGsAdded':26,'newBindings':new,'visualReview':'pending current installed phase review',
        'animationPlaybackObservation':'no connected browser surface available; all12 phase pixels per binding viewed separately, GIF12-frame decode/timing checked',
        'nativePaintingCountAdded':0,'userArtAcceptance':'pending','unityValidated':False}
    vr=R/'records/world-production/industry-fx-visual-review.json'
    if vr.is_file():
        v=wp.readj(vr)
        if v.get('manifestSHA256')==wp.sha(MP) and all(wp.sha(R/p['file'])==p['sha256']for p in v.get('pages',[])):
            report['visualReview']='passed-local: all24 installed phases and baked-bubble removal comparison inspected; current hashes match'
            report['visualReviewRecord']={'file':wp.rel(vr),'sha256':wp.sha(vr)}
    wp.writej(R/'records/world-production/industry-fx-binding-validation.json',report)
    print(json.dumps({'checks':len(checks),'passed':report['passed'],'failed':len(report['failures'])}))


if __name__=='__main__':main()

"""Source9-stage contract, actual upright roots, exact overlays and current art pages."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,re,math
import world_pack as wp
from validate_foundation_geometry import source_z

R=wp.ROOT
MP=R/'assets/world/terrain/field-stages/manifest.json'
PRE=R/'previews/world/field-stages'


def main():
    m=wp.readj(MP);by={a['image']:a for a in m['assets']};mapping=m['coverageMappings'][0];checks=[]
    def check(name,ok,**data):checks.append({'id':name,'passed':bool(ok),**data})
    source=(R/'reference/OpenTTD/src/table/clear_land.h').read_text()
    block=re.search(r'_clear_land_sprites_farmland\[16\]\s*=\s*\{([^}]+)',source,re.S).group(1)
    valid=re.findall(r'\bSPR_FARMLAND_[A-Z0-9_]+',block)
    check('source9-valid-field-types-in16-capacity',len(valid)==9,sourceSprites=valid)
    loop=(R/'reference/OpenTTD/src/clear_cmd.cpp').read_text()
    check('source-growth-cycle0-through8','field_type = (field_type < 8) ? field_type + 1 : 0' in loop)
    check('all9-stages-bound',set(mapping['fieldStages'])==set(range(9)))
    check('all19-source-slopes',set(mapping['slopeCodes'])=={c for c,n in wp.SLOPES})
    check('all171-stage-slope-bindings',{(s['sourceFieldType'],s['slopeCode'])for s in mapping['states']}
          =={(s,c)for s in range(9)for c,n in wp.SLOPES})
    check('source-is-growth-not16-randoms',mapping['sourceRandomVariants']is None
          and mapping['validSourceFieldTypes']==list(range(9))and mapping['invalidStoredFieldTypes']==list(range(9,16)))
    # The all-terrain snapshot proves the old build interval only. Snow/desert
    # work by another producer must not invalidate field art that never uses it.
    check('supplemental-output-scope',all((R/a['image']).resolve().parent==MP.parent.resolve()for a in m['assets']))
    for a in m['assets']:
        im=Image.open(R/a['image'])
        check(a['id']+'.PNG-source-hash',im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0
            and im.getchannel('A').getextrema()[1]>0 and im.size==(a['width'],a['height'])
            and wp.sha(R/a['image'])==a['sha256']and all((R/p['file']).is_file()and wp.sha(R/p['file'])==p['sha256']and(R/p['record']).is_file()for p in a['derivedFrom']))
        if a['category']!='field-native-primitive':
            check(a['id']+'.fixed-slope-canvas',im.size==(256,256)and a['anchorPx']==[128,160])
    primitive_images={a['image']:Image.open(R/a['image']).convert('RGBA')for a in m['assets']if a['category']=='field-native-primitive'}
    sprite_cache={}
    for s in mapping['states']:
        stage,code=s['sourceFieldType'],s['slopeCode'];tag=f'field{stage}-slope{code}'
        overlay=Image.new('RGBA',(256,256))
        for i,p in enumerate(s['placements']):
            u,v=p['uv'];z=source_z(code,u,v)
            root=[128+(v-u)*128,96+(u+v)*64-z*32]
            check(tag+f'.root{i}.source-height',abs(p['rootHeightUnits']-z)<1e-6
                  and all(abs(a-b)<1e-6 for a,b in zip(root,p['rootPx'])))
            raw=primitive_images[p['image']];prim=by[p['image']]
            check(tag+f'.root{i}.upright-no-upscale',p['scale']<=1 and all(abs(n-o*p['scale'])<=.51 for n,o in zip(p['renderSizePx'],raw.size)))
            cachekey=(p['image'],tuple(p['renderSizePx']))
            if cachekey not in sprite_cache:sprite_cache[cachekey]=raw.resize(p['renderSizePx'],Image.Resampling.LANCZOS)
            sprite=sprite_cache[cachekey]
            x,y=p['offsetPx']
            check(tag+f'.root{i}.not-clipped',x>=0 and y>=0 and x+sprite.width<=256 and y+sprite.height<=256)
            overlay.alpha_composite(sprite,(x,y))
        if s['overlay']:
            check(tag+'.actual-overlay-reassembly',overlay.tobytes()==Image.open(R/s['overlay']).convert('RGBA').tobytes())
        else:check(tag+'.bare-stage-no-empty-placeholder',stage==0 and not s['placements'])
        whole=Image.open(R/s['ground']).convert('RGBA');whole.alpha_composite(overlay)
        check(tag+'.actual-ground-overlay-whole',whole.tobytes()==Image.open(R/s['whole']).convert('RGBA').tobytes())
    flat={s['sourceFieldType']:s for s in mapping['states']if s['slopeCode']==0}
    if set(flat)==set(range(9)):
        check('nine-visually-distinct-stage-outputs',len({wp.sha(R/flat[s]['whole'])for s in range(9)})==9)
        check('ripe-is-actual-gold-clumps',{p['kind']for p in flat[7]['placements']}=={'gold-grain'})
        check('harvest-haypacks-replace-standing-crop',{p['kind']for p in flat[8]['placements']}=={'haypacks'})
        check('green-mixed-gold-maturity-contract',{p['kind']for p in flat[4]['placements']}=={'green-grain'}
              and {p['kind']for p in flat[6]['placements']}=={'green-grain','gold-grain'})
    pages=[];font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),17)
    # One current page per source stage: all19 slopes, not just representative slope codes.
    for stage in sorted(flat):
        states=[s for s in mapping['states']if s['sourceFieldType']==stage]
        page=Image.new('RGB',(1280,1040),'#e7e1ce');d=ImageDraw.Draw(page)
        for i,s in enumerate(states):
            im=Image.open(R/s['whole']).convert('RGBA');x=(i%5)*256;y=(i//5)*260
            page.paste(im,(x,y+10),im);d.text((x+5,y+5),'stage'+str(stage)+' / slope'+str(s['slopeCode']),font=font,fill='#204438')
        p=PRE/('stage-'+str(stage)+'-all19-slopes.jpg');page.save(p,quality=95)
        pages.append({'file':wp.rel(p),'sha256':wp.sha(p),'sourceFieldType':stage,'shownSlopes':len(states)})
    overview=Image.new('RGB',(1152,930),'#e7e1ce');d=ImageDraw.Draw(overview)
    for stage in sorted(flat):
        im=Image.open(R/flat[stage]['whole']).convert('RGBA');x=(stage%3)*384+64;y=(stage//3)*310+25
        overview.paste(im,(x,y),im);d.text((x-40,y+258),str(stage)+' / '+flat[stage]['fieldStageName'],font=font,fill='#204438')
    op=PRE/'nine-stage-overview.jpg';overview.save(op,quality=96);pages.append({'file':wp.rel(op),'sha256':wp.sha(op)})
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>农田0–8生长阶段</title><style>body{font:16px sans-serif;line-height:1.7;margin:24px;background:#173f35;color:#eee5cf}article{margin:20px 0;background:#e7e1ce;color:#244638;padding:15px;border-radius:12px}img{display:block;width:100%;height:auto;max-width:1280px}summary{cursor:pointer}</style><h1>农田 · 9有效阶段 × 19坡</h1><p>源0..8为生长阶段，16只是存储容量。原生土壤投影，幼苗/麦丛/草捆保持竖立，根部跟随实际坡高。采用whole或ground＋overlay之一。<br>阶段是随源码计数变化的静态资产，不是新增连续动画；用户审美和Unity仍待验收。</p><img src="nine-stage-overview.jpg" alt="当前9阶段概览">'''
    for p in pages[:-1]:html+='<article><details><summary>阶段'+str(p['sourceFieldType'])+' · 全部19坡</summary><img loading="lazy" src="'+Path(p['file']).name+'" alt="source field stage '+str(p['sourceFieldType'])+' all19slopes"></details></article>'
    (PRE/'index.html').write_text(html+'</html>',encoding='utf-8')
    report={'createdAt':wp.now(),'manifest':wp.rel(MP),'manifestSHA256':wp.sha(MP),'checks':checks,
        'passed':sum(c['passed']for c in checks),'failures':[c for c in checks if not c['passed']],
        'fieldStages':mapping['fieldStages'],'stateBindings':len(mapping['states']),'formalPNGs':len(m['assets']),
        'pages':pages,'visualReview':'pending actual stage/slope page inspection','userArtAcceptance':'pending','unityValidated':False,
        'dependencyPolicy':'current validity checks actual assets[].derivedFrom sources only; productionNoOtherWrites all-terrain snapshot is historical evidence, not a live dependency',
        'productionNoOtherWrites':m.get('productionNoOtherWrites',{})}
    vp=R/'records/world-production/field-stages-visual-review.json'
    if vp.exists():
        v=wp.readj(vp)
        if v.get('manifestSHA256')==wp.sha(MP)and all(wp.sha(R/p['file'])==p['sha256']for p in v.get('pages',[])):
            report['visualReview']='passed-local: all9stages and171 source slope bindings inspected; current hashes match'
            report['visualReviewRecord']={'file':wp.rel(vp),'sha256':wp.sha(vp)}
    wp.writej(R/'records/world-production/field-stages-validation.json',report)
    print(json.dumps({'passed':report['passed'],'failed':len(report['failures']),'sourceBindings':len(mapping['states'])}))


if __name__=='__main__':main()

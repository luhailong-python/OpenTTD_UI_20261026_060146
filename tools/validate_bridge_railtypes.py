"""Read actual supplemental PNGs, validate layers/ports, build inspection pages."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import numpy as np,json,re
import world_pack as wp
from preview_bridge_joins import inspect_joins,panel

R=wp.ROOT
MP=R/'assets/world/infrastructure/bridge-railtypes/manifest.json'
PRE=R/'previews/world/bridge-railtypes'
ROLES={'north','south','inner-north','inner-south','middle-odd','middle-even','head'}


def main():
    m=wp.readj(MP);src=wp.readj(R/m['readOnlySourceManifest']['file'])
    by={a['image']:a for a in m['assets']+src['assets']}
    checks=[];joins=[];pages=[]
    def check(ident,passed,**meta):checks.append({'id':ident,'passed':bool(passed),**meta})
    check('frozen-source-manifest-unchanged',wp.sha(R/m['readOnlySourceManifest']['file'])==m['readOnlySourceManifest']['sha256'])
    check('frozen-source-all1245-PNGs-unchanged',all(wp.sha(R/a['file'])==a['sha256']for a in m['sourceReadOnlySnapshot']),count=len(m['sourceReadOnlySnapshot']))
    source_offsets=list(map(int,re.findall(r'/\* bridge offset \*/\s*(\d+)',(R/'reference/OpenTTD/src/table/railtypes.h').read_text())))
    check('native-source-bridge-offsets',source_offsets==[0,0,16,24],values=source_offsets)
    check('13-source-BridgeSpecs',{a['sourceBridgeId']for a in m['coverageMappings']}==set(range(13)))
    check('240-new-PNGs',len(m['assets'])==240)
    for a in m['assets']:
        im=Image.open(R/a['image'])
        check(a['id']+'.formal-PNG',im.mode=='RGBA'and im.size==(384,384)and a['anchorPx']==[192,320]
              and im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getextrema()[1]>0
              and wp.sha(R/a['image'])==a['sha256'])
        check(a['id']+'.current-parent-source-sha',all((R/p['file']).is_file()and wp.sha(R/p['file'])==p['sha256']
               and(R/p['record']).is_file()for p in a['derivedFrom']))
        mask=np.asarray(Image.open(R/a['frozenLaneOwnershipMask']).convert('RGBA'))[:,:,3]>0
        if a['category']=='bridge-railtype-lane':
            check(a['id']+'.inside-frozen-deck-ownership',not np.any(np.asarray(im)[:,:,3][~mask]))
        else:
            rebuilt=Image.new('RGBA',im.size)
            for k in ['rear','lane','front']:rebuilt.alpha_composite(Image.open(R/a['layers'][k]).convert('RGBA'))
            check(a['id']+'.exact-rear-lane-front-reassembly',rebuilt.tobytes()==im.tobytes())
            old=Image.new('RGBA',im.size)
            for k in ['rear','front']:old.alpha_composite(Image.open(R/a['layers'][k]).convert('RGBA'))
            check(a['id']+'.protected-structure-RGBA-unchanged',np.array_equal(np.asarray(old)[~mask],np.asarray(im)[~mask]))
    font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),17)
    for mapping in m['coverageMappings']:
        states=mapping['states'];req=mapping['requirementId']
        check(req+'.four-railtypes-both-axes',{(s['railType'],s['axis'])for s in states}
              =={(t,a)for t in ['rail','electric','monorail','maglev']for a in ['X','Y']})
        page=Image.new('RGB',(1360,1320),'#e7e1ce');d=ImageDraw.Draw(page)
        d.text((15,9),req+' / native MONO + MGLV guideway paint on frozen structure',font=font,fill='#204438')
        for state in states:
            check(req+'.'+state['axis']+'.'+state['railType']+'.7roles',set(state['pieces'])==ROLES)
            check(req+'.'+state['axis']+'.'+state['railType']+'.source-offset',state['sourceBridgeOffset']==dict(zip(['rail','electric','monorail','maglev'],source_offsets))[state['railType']])
            if state['railType']=='electric':
                normal=next(s for s in states if s['axis']==state['axis']and s['railType']=='rail')
                check(req+'.'+state['axis']+'.normal-electric-explicit-shared-art',state['aliasDeclared']and state['pieces']==normal['pieces'])
            for seqidx,sequence in enumerate([['middle-odd']*3,['north','middle-odd','south']]):
                parts=[]
                for role in sequence:
                    p=state['pieces'][role];a=by[p['image']]
                    parts.append((Image.open(R/p['image']).convert('RGBA'),a['projection']))
                result=inspect_joins(parts,state['axis']);joins.append({'bridge':req,'railType':state['railType'],'axis':state['axis'],'sequence':sequence,**result})
                check(req+'.'+state['axis']+'.'+state['railType']+'.'+str(seqidx)+'.two-actual-joins',
                      result['exactPortAlignment']and result['noTransparentDeckGap'])
                if state['railType']in ['monorail','maglev']:
                    row=(0 if state['railType']=='monorail' else 2)+seqidx
                    x=0 if state['axis']=='X' else 680;y=44+row*316
                    im=panel(parts,state['axis']);im.thumbnail((660,280),Image.Resampling.LANCZOS)
                    page.paste(im.convert('RGB'),(x+(680-im.width)//2,y+24))
                    d.text((x+15,y),state['axis']+' / '+state['railType']+' / '+('flat3'if seqidx==0 else'up32-flat-down32'),font=font,fill='#204438')
        for axis in ['X','Y']:
            mono=next(s for s in states if s['axis']==axis and s['railType']=='monorail')
            mag=next(s for s in states if s['axis']==axis and s['railType']=='maglev')
            check(req+'.'+axis+'.mono-maglev-paint-distinct',all(wp.sha(R/mono['pieces'][r]['layers']['lane'])
                  !=wp.sha(R/mag['pieces'][r]['layers']['lane'])for r in ROLES))
        p=PRE/(req+'.jpg');page.save(p,quality=95);pages.append({'file':wp.rel(p),'sha256':wp.sha(p),'sourceBridgeId':mapping['sourceBridgeId']})
    # Direct strip display is only a labeled QA view; no new formal material.
    matpage=Image.new('RGB',(900,380),'#e7e1ce');dd=ImageDraw.Draw(matpage)
    for row,kind in enumerate(['monorail','maglev']):
        a=next(a for a in src['assets']if a['id']=='lane-source-'+kind)
        strip=Image.open(R/a['image']).convert('RGBA');strip=strip.resize((strip.width*3,strip.height*3),Image.Resampling.NEAREST)
        matpage.paste(strip,(220,row*185+10),strip);dd.text((15,row*185+25),kind+' / existing source',font=font,fill='#204438')
    matp=PRE/'native-materials.jpg';matpage.save(matp,quality=96)
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>单轨与磁浮桥面补包</title><style>body{font:16px sans-serif;background:#173f35;color:#eee5cf;margin:24px;line-height:1.7}article{background:#eee6d4;color:#244638;border-radius:12px;padding:16px;margin:20px 0}img{display:block;width:100%;max-width:1360px;height:auto}a{color:#b7ddbc}summary{cursor:pointer}</style><h1>13种桥梁 · 单轨与磁浮桥面</h1><p>既有原生材质按冻结桥口/坡面投影；原桥rear/front结构逐像素复用。普通与电气共轨面，电气线杆另层。13桥×2轴×4轨制×7角色绑定；新增240PNG，不是新生成原画。<br>选择whole或rear＋lane＋front；静态美术检查不表示Unity净空/深度/车行通过。</p><img src="native-materials.jpg" alt="既有单轨与磁浮原生条带">'''
    for mapping,p in zip(m['coverageMappings'],pages):
        html+='<article><details><summary>'+mapping['requirementId']+' · 两轴/平接/上平下</summary><img loading="lazy" src="'+Path(p['file']).name+'" alt="'+mapping['requirementId']+' actual current PNG assemblies"></details></article>'
    (PRE/'index.html').write_text(html+'</html>',encoding='utf-8')
    report={'createdAt':wp.now(),'manifest':wp.rel(MP),'manifestSHA256':wp.sha(MP),
        'checks':checks,'passed':sum(c['passed']for c in checks),'failures':[c for c in checks if not c['passed']],
        'actualAssemblies':len(joins),'actualInterfaces':sum(len(a['joins'])for a in joins),
        'joinEvidence':joins,'visualPages':pages+[{'file':wp.rel(matp),'sha256':wp.sha(matp)}],
        'visualReview':'pending actual page inspection','nativePaintingCountAdded':0,'userArtAcceptance':'pending','unityValidated':False}
    vr=R/'records/world-production/bridge-railtypes-visual-review.json'
    if vr.exists():
        v=wp.readj(vr)
        if v.get('manifestSHA256')==wp.sha(MP)and all(wp.sha(R/p['file'])==p['sha256']for p in v['pages']):
            report['visualReview']='passed-local: actual native material and all13 current assembly pages inspected; source hashes match'
            report['visualReviewRecord']={'file':wp.rel(vr),'sha256':wp.sha(vr)}
    wp.writej(R/'records/world-production/bridge-railtypes-validation.json',report)
    print(json.dumps({k:report[k]for k in ['passed','actualAssemblies','actualInterfaces']}|{'failed':len(report['failures'])}))


if __name__=='__main__':main()

"""Independent current-file/source/geometry/layer checks, never visual approval."""
from PIL import Image
import numpy as np,json
import world_pack as wp
import build_rocks_overlay as b
R=wp.ROOT

def main():
    mp=b.OUT/'manifest.json';m=wp.readj(mp);assets={a['id']:a for a in m['assets']};over=[a for a in m['assets']if a.get('independentRockOverlay')];checks=[]
    def check(i,v,**detail):checks.append({'id':i,'level':'OK'if v else'FAIL',**detail})
    expected={(s,l,c)for s in b.STATES for l in range(2 if s=='dry'else 1)for c,_ in wp.SLOPES};actual={(a['overlayState'],a['layoutVariant'],a['slopeCode'])for a in over};check('exact133-source-state-layout-slope-contract',actual==expected,expected=len(expected),actual=len(actual))
    check('exact18-native-source-stone-parts',sum(a['category']=='rocks-native-part'for a in m['assets'])==18)
    for a in m['assets']:
        path=R/a['image'];im=Image.open(path).convert('RGBA');bb=im.getbbox();check(a['id']+'.size-alpha-sha',im.size==(a['width'],a['height'])and im.getchannel('A').getextrema()[0]==0 and wp.sha(path)==a['sha256']);check(a['id']+'.not-clipped',bool(bb)and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height);check(a['id']+'.actual-source-chain',all((R/s['file']).is_file()and wp.sha(R/s['file'])==s['sha256']and(R/s['record']).is_file()for s in a['derivedFrom']))
        if a.get('independentRockOverlay'):
            check(a['id']+'.overlay-registration',im.size==(256,256)and a['anchorPx']==[128,192]and len(a['placements'])==3)
            out=Image.new('RGBA',im.size)
            for p in a['placements']:
                part=assets[p['partId']];out.alpha_composite(Image.open(R/part['image']).convert('RGBA'),tuple(p['offsetPx']));x,y=p['sourceTileXY'];z=b.partial_z(x,y,a['slopeCode']);check(a['id']+'.contact-'+str(p['partId']),p['sourceHeightUnits']==z and p['screenContactPx']==[128+(y-x)*8,128+(x+y)*4-z*4]and p['uprightBodyPreserved']and p['scale']==1)
            check(a['id']+'.actual-upright-part-rgba',out.tobytes()==im.tobytes())
    for code,_ in wp.SLOPES:
        corners=wp.corner_heights(code)
        for name,xy in {'n':(0,0),'e':(0,16),'s':(16,16),'w':(16,0)}.items():check('source-height-corner-'+str(code)+'-'+name,b.partial_z(*xy,code)==corners[name]*8)
    coast=m['coastGroundManifest'];check('current-formal-coast-module',wp.sha(R/coast['file'])==coast['sha256']);sm=wp.readj(R/coast['file']);rows={(s['shoreClimate'],s['sourceSlopeCode']):s for s in sm['coverageMappings'][0]['states']};mesh={p['sourceSlopeCode']:p for p in sm['geometry']['postures']}
    coast_samples=[s for s in m['compositionSamples']if s['context']=='CoastRocks'];check('48legal-coast-combinations',len(coast_samples)==48 and {(s['shoreClimate'],s['slopeCode'])for s in coast_samples}=={(cl,c)for cl in['grass','sand','snow']for c,_ in wp.SLOPES if c not in[0,5,10]})
    for s in m['compositionSamples']:
        check(s['id']+'.sample-current-sha',wp.sha(R/s['image'])==s['sha256']);check(s['id']+'.source-current',all(wp.sha(R/x['file'])==x['sha256']for x in s['derivedFrom']))
        if s['context']=='CoastRocks':
            out=Image.new('RGBA',(256,256))
            for layer in s['formalLayers']:out.alpha_composite(Image.open(R/layer['image']).convert('RGBA'),tuple(layer['offsetPx']))
            check(s['id']+'.formal-layer-rgba',out.tobytes()==Image.open(R/s['image']).convert('RGBA').tobytes());a=assets[s['overlayId']];ground=Image.open(R/s['groundWhole']).convert('RGBA');vertices={tuple(v['sourceXY']):v for v in mesh[s['slopeCode']]['vertices']}
            for p in a['placements']:
                x,y=p['sourceTileXY'];px,py=p['screenContactPx'];py-=64;aa=ground.getchannel('A').crop((px-1,py-1,px+2,py+2)).getextrema()[1];check(s['id']+'.supported-contact-'+p['partId'],vertices[(x,y)]['renderZ']==p['sourceHeightUnits']and aa>32,groundAlphaMax=aa)
            state=rows[(s['shoreClimate'],s['slopeCode'])];check(s['id']+'.dryout-water-rule',bool(state['layers']['water'])==s['waterHasPositiveArea'])
    for p in m['contactPages']:check(p['image']+'.current-contact-page',wp.sha(R/p['image'])==p['sha256'])
    for cl in['grass','sand','snow']:
        for code,_ in wp.SLOPES:
            if code in[0,5,10]:continue
            check('coast-source-module-present-'+cl+'-'+str(code),(cl,code)in rows)
    failures=[c for c in checks if c['level']=='FAIL'];result={'schema':'native-rock-overlay-production-QA.v1','createdAt':wp.now(),'manifest':'assets/world/terrain/rocks-overlay/manifest.json','manifestSHA256':wp.sha(mp),'registeredAssets':len(m['assets']),'independentOverlays':len(over),'compositionSamples':len(m['compositionSamples']),'contactPages':len(m['contactPages']),'coastGroundManifest':coast,'checks':len(checks),'failures':failures,'checksDetail':checks,'mechanicalPassed':not failures,'visualReview':'Explicit current-pixel review is separate; mechanical success cannot approve artwork','userAccepted':False,'unityValidated':False}
    wp.writej(b.REC/'rocks-overlay-validation.json',result);print(json.dumps({k:v for k,v in result.items()if k!='checksDetail'},ensure_ascii=False))

if __name__=='__main__':main()

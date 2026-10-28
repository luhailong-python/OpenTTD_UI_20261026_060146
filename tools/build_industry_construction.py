from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFont
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
mp=R/'assets/world/industries/manifest.json';m=readj(mp);m['assets']=[x for x in m['assets']if x['category']!='industry-construction']
mains=[x for x in m['assets']if x['category']=='industry'];kitm=readj(R/'assets/world/infrastructure/construction-ready/manifest.json');kits={x['id']:x for x in kitm['assets']}
def kitfit(ident,width):
    x=kits[ident];im=Image.open(R/x['image']).convert('RGBA');box=im.getbbox();part=im.crop(box);scale=min(1,width/part.width);part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(512,512));out.alpha_composite(part,(256-part.width//2,448-part.height))
    return out,{'file':x['image'],'sha256':sha(R/x['image']),'record':x['image']+'.derivation.json','scale':scale}
for main in mains:
    im=Image.open(R/main['image']).convert('RGBA');box=im.getbbox();w=box[2]-box[0];h=box[3]-box[1];idx=main['sourceIndustryTypeId'];st=[]
    for stage in range(4):
        if stage==3:st.append({'stage':stage,'artId':main['id'],'image':main['image'],'phase':'complete'});continue
        out=Image.new('RGBA',(512,512));sources=[{'file':main['image'],'sha256':main['sha256'],'record':main['derivationRecord']}];details={}
        if stage==0:
            if idx==5:
                piece=im.copy();mask=Image.new('L',im.size);ImageDraw.Draw(mask).rectangle((0,448-int(h*.45),512,512),fill=255);piece.putalpha(ImageChops.multiply(piece.getchannel('A'),mask));out.alpha_composite(piece);details={'kind':'offshore native pilings lower segment, no land masonry foundation','visibleBottomFraction':.45}
            else:
                k,source=kitfit('construction-foundation',w);out.alpha_composite(k);sources.append(source);details={'kind':'shared industry foundation matched to compound front contact','sharedSource':True}
        else:
            fraction=(.62 if idx==5 else .38) if stage==1 else .76
            if idx in [3,19,20,26]:
                part=im.crop(box);s=.56 if stage==1 else .80;part=part.resize((round(part.width*s),round(part.height*s)),Image.Resampling.LANCZOS);out.alpha_composite(part,(256-part.width//2,448-part.height));details={'kind':'vegetative site young compound scale derivative','sourceScale':s}
            else:
                piece=im.copy();mask=Image.new('L',im.size);ImageDraw.Draw(mask).rectangle((0,448-int(h*fraction),512,512),fill=255);piece.putalpha(ImageChops.multiply(piece.getchannel('A'),mask));out.alpha_composite(piece);details={'kind':'partially completed compound revealed behind scaffold','visibleBottomFraction':fraction}
            k,source=kitfit('construction-front-scaffold' if idx==5 else ('construction-scaffold-low'if stage==1 else'construction-front-scaffold'),w*(.75 if idx==5 else 1))
            if idx==5:
                shifted=Image.new('RGBA',(512,512));shifted.alpha_composite(k,(0,-80));k=shifted;details['offshoreScaffoldAnchorCorrectionPx']=[0,-80]
            out.alpha_composite(k);sources.append(source)
        p=R/'assets/world/industries/construction'/main['id']/('stage-'+str(stage)+'.png');p.parent.mkdir(parents=True,exist_ok=True);out.save(p)
        en={'id':main['id']+'-construction-'+str(stage),'image':p.relative_to(R).as_posix(),'width':512,'height':512,'anchorPx':[256,448],'pivotUnity':[.5,.125],'anchorMeaning':'front-contact-of-compound','category':'industry-construction','sha256':sha(p),'operation':'layered construction derivative from terminal compound and shared native construction kit; transparent masking/reveal or proportional shrink for growing plantations; not new AI painting','derivedFrom':sources,'status':'needs-construction-visual-review','nativeUpscale':False,'unityValidated':False,'sourceIndustryTypeId':idx,'stage':stage,'details':details,'sourceRequirementIds':main['sourceRequirementIds']}
        savej(Path(str(p)+'.derivation.json'),en);m['assets'].append(en);st.append({'stage':stage,'artId':en['id'],'image':en['image'],'phase':['foundation','low-construction','high-construction'][stage]})
    main['constructionStates']=st
for row in m['coverageMappings']:
    if row['requirementId'].startswith('industry-tile-'):
        row['constructionStates']=[{'sourceIndustryTypeId':idx,'states':next(x['constructionStates']for x in mains if x['sourceIndustryTypeId']==idx)}for idx in row['parentIndustryIds']]
    else:
        main=next(x for x in mains if x['id']==row['requirementId']);row['constructionStates']=main['constructionStates'];row['constructionArtStatus']='four-stages-produced-derived-kit'
m['limitations']=[x for x in m['limitations']if not x.startswith('施工阶段0')]
m['counts'].update({'constructionDerivedPNGs':111,'sourceIndustryStageMappings':700,'terminalCompoundStageSets':37})
m['constructionContract']={'stages':[0,1,2,3],'sourceStageIndex':'IndustryGfx<<2 | stage','nativeCompoundCount':37,'constructionKitShared':True,'nativeStagePaintingClaim':False,'layoutGfxRendering':'all 175 source gfx map four stage compatibility states to parent compound drawn once per instance','kitManifest':'assets/world/infrastructure/construction-ready/manifest.json','offshoreSpecial':'oil rig phase0 uses actual pilings instead of a masonry land foundation'}
savej(mp,m)
font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),16)
for page in range(8):
    panel=Image.new('RGB',(1024,1450),'#e7e2d2');d=ImageDraw.Draw(panel)
    for r,main in enumerate(mains[page*5:page*5+5]):
        for c,state in enumerate(main['constructionStates']):
            im=Image.open(R/state['image']).convert('RGBA');im=im.resize((256,256),Image.Resampling.LANCZOS)
            bg=Image.new('RGBA',(256,256),'#e7e2d2'if r%2==0 else '#244139');bg.alpha_composite(im);panel.paste(bg.convert('RGB'),(c*256,r*290))
            d.text((c*256+4,r*290+258),main['id'].split('-',2)[-1]+' / '+str(c),font=font,fill='#154c3d')
    pp=R/'previews/world'/('industry-construction-'+str(page+1)+'.jpg');panel.save(pp,quality=94)
print(json.dumps({'constructionFiles':111,'sourceStageMappings':700,'previews':8}))


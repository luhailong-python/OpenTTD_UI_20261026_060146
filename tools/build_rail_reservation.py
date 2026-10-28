"""PBS reservation art from actual owned track-overlay pixels only."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,numpy as np
import world_pack as wp
R=wp.ROOT;OUT='assets/world/overlays/rail-reservation';PRE=R/'previews/rail-reservation';CODES={0:'flat',3:'sw',6:'se',9:'nw',12:'ne'};KINDS=['rail','electric','monorail','maglev'];TRACKS=['x','y','upper','lower','left','right']
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(f):return{'file':f,'sha256':wp.sha(R/f),'record':f+'.derivation.json'}
def normalized(f,code):
 im=Image.open(R/f).convert('RGBA')
 if code==0:out=Image.new('RGBA',(256,192));out.alpha_composite(im,(0,64));return out
 return im
def ground(code):
 f='assets/world/terrain/terrain-grass-slope-'+({0:'flat',3:'sw',6:'se',9:'nw',12:'ne'}[code])+'.png';return Image.open(R/f).convert('RGBA'),ref(f)
def main():
 (R/OUT).mkdir(parents=True,exist_ok=True);PRE.mkdir(parents=True,exist_ok=True);old=load(R/'assets/world/infrastructure/rail/manifest.json');by={a['id']:a for a in old['assets']};assets=[];maps=[];font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),12)
 for kind in KINDS:
  states=[]
  for code,name in CODES.items():
   for bit,track in enumerate(TRACKS):
    key=f'rail-{kind}-segment-{track}'+(''if code==0 else'-slope-'+name);source=by[key];im=normalized(source['image'],code);ar=np.array(im);lum=.2126*ar[...,0]+.7152*ar[...,1]+.0722*ar[...,2];gray=np.rint(lum*.58).astype('uint8');ar[...,:3]=gray[...,None];ar[ar[...,3]==0,:3]=0;ident=f'pbs-{kind}-{track}-slope-{name}';f=OUT+'/'+ident+'.png';Image.fromarray(ar).save(R/f)
    a={'id':ident,'image':f,'width':256,'height':192,'format':'PNG','mode':'RGBA','sha256':wp.sha(R/f),'anchorPx':[128,128],'pivotUnity':[.5,1/3],'category':'rail-reservation-overlay','sourceRequirementIds':['rail-'+kind],'state':'reserved','trackBit':bit,'trackName':track,'slopeCode':code,'sourceOverlay':ref(source['image']),'derivedFrom':[ref(source['image'])],'sourceLayer':source['layer'],'ownershipMask':'exact Alpha of actual source track-overlay PNG;flat only transparent64px top padding;no terrain composite input','operation':'luma grayscale×0.58 on native owned track pixels,source Alpha unchanged,Alpha0RGB cleared;source PALETTE_CRASH visual meaning reinterpreted for current art,not original palette byte emulation','material':{'rgbFormula':'round((0.2126R+0.7152G+0.0722B)*0.58) repeated inRGB','alphaFormula':'Aout=Asource; no opaque fill/no whole-ground tint','blend':'straight alpha/source-over','sourceSetting':'_settings_client.gui.show_track_reservation','activeCondition':'reservedTrackBits & currentTrackBits;source also suppresses menu mode','notReserved':'do not draw this layer','overhead':'catenary/posts/vehicles excluded from owned Alpha and remain separate'},'nativeModelGeneration':False,'nativeUpscale':False,'actualModel':None,'actualQuality':None,'userArtAcceptance':'pending','unityValidated':False,'status':'produced-needs-actual-visual-review'};wp.writej(Path(str(R/f)+'.derivation.json'),a);assets.append(a);states.append({'trackBit':bit,'trackName':track,'slopeCode':code,'file':f,'sha256':a['sha256'],'normalSource':source['image']})
  maps.append({'requirementId':'rail-'+kind,'files':[s['file']for s in states],'assetState':'path-reservation-debug-highlight','states':states,'trackBits':list(range(6)),'effectiveSlopeCodes':list(CODES),'reservedBitMasks':list(range(64)),'composition':'draw gray layer only for bits set in(reservation & existing tracks);same tile anchor as normal track;mask0noDraw','halftileRule':'use the same existing sourceFoundation upper/lower ownership clip and height offset as corresponding normal track;never tint adjoining bare/grass/water half','completeVariantCoverage':True})
 manifest={'schema':'rail-reservation-art.v1','createdAt':wp.now(),'assets':assets,'animations':[],'coverageMappings':maps,'sourceFiles':[{'file':'reference/OpenTTD/src/'+p,'sha256':wp.sha(R/'reference/OpenTTD/src'/p)}for p in ['rail_cmd.cpp','station_cmd.cpp','track_type.h']],'formalPNGs':len(assets),'sourceMeaning':'rail_cmd.cpp2156-2173/2258-2261/2391-2415;station_cmd.cpp3426-3436 reserves rail overlay only;source gray/darker PAL_CRASH;not a train ownership colour','userArtAcceptance':'pending','unityValidated':False,'status':'produced-needs-actual-visual-review'};wp.writej(R/OUT/'manifest.json',manifest)
 pages=[]
 for code,name in CODES.items():
  aa=[a for a in assets if a['slopeCode']==code];out=Image.new('RGB',(1536,8*230+46),'#21483a');d=ImageDraw.Draw(out);d.text((12,10),'路径预留 '+name+' · 每格左普通／右预留；只有轨段灰化',font=font,fill='#f2e4c5');deps=[]
  for k,a in enumerate(aa):
   x=k%3*512;y=k//3*230+35;g,gref=ground(code);normal=g.copy();normal.alpha_composite(normalized(a['sourceOverlay']['file'],code));reserved=normal.copy();reserved.alpha_composite(Image.open(R/a['image']).convert('RGBA'));out.paste(normal,(x,y),normal);out.paste(reserved,(x+256,y),reserved);d.text((x+10,y+192),a['id'],font=font,fill='#f2e4c5');deps.extend([gref,ref(a['sourceOverlay']['file']),ref(a['image'])])
  f='previews/rail-reservation/pbs-'+name+'.jpg';out.save(R/f,quality=96);wp.writej(Path(str(R/f)+'.derivation.json'),{'file':f,'sha256':wp.sha(R/f),'operation':'actual native grass slope plus normal owned rail overlay or its gray reserved version;1x registered256x192pairs;no whole-ground grayscale','derivedFrom':deps,'nativeModelGeneration':False,'unityValidated':False});pages.append(f)
 html='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>铁路路径预留灰化状态</title><style>body{background:#21483a;color:#f1e4c7;font:15px/1.5 system-ui;margin:20px}main{max-width:1536px;margin:auto}img{max-width:100%;height:auto}a{color:#dbbd73}</style><main><h1>铁路路径预留 · 仅轨段所有权灰化</h1><p>4轨制×6轨段×平/四坡＝120个独立灰化叠层。对照每格左普通、右预留，草地与水/裸地等底层不变。触发条件来自source show_track_reservation与实际保留bit；不是路由或引擎运行证明。</p><a href="../../docs/RAIL_RESERVATION_ART.md">规格与绑定</a>'
 for f in pages:html+='<h2>'+Path(f).stem+'</h2><img src="../../'+f+'">'
 html+='</main>';(PRE/'index.html').write_text(html,encoding='utf8');print(json.dumps({'formalPNGs':len(assets),'pages':pages,'manifestSHA256':wp.sha(R/OUT/'manifest.json')}))
if __name__=='__main__':main()

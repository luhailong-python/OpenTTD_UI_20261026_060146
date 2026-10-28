"""Bind six industry mechanisms to real parent artwork. No generated paint or Unity code."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFont
import numpy as np, math,json,hashlib,datetime,copy
from scipy import ndimage
R=Path(__file__).resolve().parents[1];MP=R/'assets/world/industries/manifest.json';OUT=R/'assets/world/industries/bindings';PRE=R/'previews/world/industry-assembly'
def j(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(R).as_posix()
def savej(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def source(p):return {'file':rel(p),'sha256':sha(p),'record':rel(p)+'.derivation.json'}
def emit(ident,im,p,parents,operation,**extra):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p);a={'id':ident,'image':rel(p),'width':im.width,'height':im.height,'anchorPx':[256,448],'pivotUnity':[.5,.125],'category':'industry-bound-animation','sha256':sha(p),'operation':operation,'derivedFrom':parents,'status':'needs-attached-motion-review','nativeUpscale':False,'unityValidated':False,**extra};savej(Path(str(p)+'.derivation.json'),a);return a
def mask_polys(polys):
 m=Image.new('L',(512,512));d=ImageDraw.Draw(m)
 for poly in polys:d.polygon(poly,fill=255)
 return m
def texture_motion(im,mask,phase,kind,pivot):
 a=np.array(im);yy,xx=np.mgrid[:512,:512].astype(float);p=np.array(mask)>0;dist=ndimage.distance_transform_edt(p);fade=np.clip(dist/3,0,1)
 if kind=='disc-spin':
  # Preserve the real housing/rim; remap only the actual painted mechanism/cavity interior.
  cx,cy=pivot;rx,ry=(12,18)if cx>300 else(10,12);theta=phase;c=math.cos(theta);s=math.sin(theta);dx=(xx-cx)/rx;dy=(yy-cy)/ry
  sx=cx+rx*(c*dx+s*dy);sy=cy+ry*(-s*dx+c*dy)
 elif kind=='auger-surface':
  sx=xx+math.sin(phase)*.8;sy=yy+math.sin(phase)*2
 elif kind=='liquid-surface':
  sx=xx+np.sin(phase+yy*.16)*.6;sy=yy+math.sin(phase)*2.4
 else:
  sx=xx+math.sin(phase)*1.4;sy=yy+math.cos(phase)*.8
 colors=np.stack([ndimage.map_coordinates(a[:,:,k].astype(float),[sy,sx],order=1,mode='nearest')for k in range(3)],axis=-1)
 rgb=a[:,:,:3].astype(float)*(1-fade[:,:,None])+colors*fade[:,:,None]
 part=a.copy();part[:,:,:3]=np.uint8(np.clip(rgb,0,255));part[:,:,3]=np.where(p,a[:,:,3],0)
 return Image.fromarray(part)
def main():
 m=j(MP);static=[a for a in m['assets']if a['category']=='industry'];by={a['id']:a for a in static};oldanimations=copy.deepcopy(m['animations'])
 defs=[
 {'clip':'mine-winding-wheel','parent':'industry-00-coal-mine','kind':'disc-spin','pivot':[309,150],'ellipse':[297,132,321,168],'description':'actual winding-wheel interior rotation; original copper rim and tower stay fixed'},
 {'clip':'pumpjack-beam','parent':'industry-11-oil-well','kind':'pump-beam-rock','pivot':[263,188],'polys':[[(164,80),(239,80),(239,216),(164,216)],[(226,134),(350,186),(350,216),(225,174)]],'description':'actual pump beam and complete horsehead Alpha, short +/-1.25deg pivot stroke; fixed support and lift rods retained'},
 {'clip':'toy-press-head','parent':'industry-31-toy-factory','kind':'disc-spin','pivot':[284,284],'ellipse':[276,273,293,297],'description':'actual internal gear in the open assembly-head cavity; housing remains fixed; supplementary detached press jaw is not overlaid'},
 {'clip':'plastic-jet','parent':'industry-32-plastic-fountains','kind':'liquid-surface','pivot':[215,289],'polys':[[(139,220),(150,224),(144,253),(148,266),(130,266),(135,250)],[(211,265),(223,266),(220,295),(221,322),(199,321),(204,300)],[(316,304),(326,306),(327,340),(332,351),(310,351),(313,332)]],'description':'three actual native painted liquid columns: in-place material flow; pipes, reservoirs and stream boundaries fixed'},
 {'clip':'toffee-drill','parent':'industry-35-toffee-quarry','kind':'auger-surface','pivot':[252,275],'polys':[[(245,253),(261,252),(266,294),(249,301),(242,291)]],'description':'actual visible auger material/coil stroke inside fixed drill housing; support does not bob'},
 {'clip':'sugar-sieve','parent':'industry-36-sugar-mine','kind':'grain-sift','pivot':[301,310],'polys':[[(249,259),(266,253),(293,283),(277,290)],[(285,300),(304,292),(329,319),(309,330)],[(317,342),(336,331),(359,355),(340,365)]],'description':'actual sugar grains on the parent conveyor/sieve batches, small internal sifting motion; wooden rails fixed'}]
 # Replace exported unbound concept clips with installed parent mechanisms. Old text evidence remains for traceability.
 oldframes={f for a in oldanimations for f in a['frames']}
 oldparts=[a for a in m['assets']if a['image']in oldframes]
 retirement=R/'records/world-production/industry-unbound-clip-retirement.json'
 if not retirement.exists():savej(retirement,{'retiredAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Unbound supplementary component clips replaced by installed actual-parent mechanisms. These records do not prove their old PNGs remain present.','previousAnimations':oldanimations,'previousFrameRecords':oldparts})
 m['assets']=[a for a in m['assets']if a['image']not in oldframes and a['category']not in ['industry-bound-animation','industry-animation-clean-base']]
 m['animations']=[];bindings=[];newassets=[];checks=[];failures=[]
 def check(ident,ok,details=None):
  checks.append({'id':ident,'passed':bool(ok),'details':details})
  if not ok:failures.append(checks[-1])
 font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),14)
 for d in defs:
  name=d['clip'];parent=by[d['parent']];pp=R/parent['image'];im=Image.open(pp).convert('RGBA');a=np.array(im);mask=Image.new('L',(512,512));draw=ImageDraw.Draw(mask)
  if'ellipse'in d:draw.ellipse(d['ellipse'],fill=255)
  else:mask=mask_polys(d['polys'])
  # Mechanism ownership is authored on the actual complete parent, never inferred from an unrelated atlas part.
  if d['kind']=='pump-beam-rock':
   # Keep the lower joint cap/front of support as a fixed foreground occluder.
   dd=ImageDraw.Draw(mask);dd.polygon([(249,189),(270,194),(270,207),(252,205)],fill=0)
  if d['kind']=='liquid-surface':
   rgb=a[:,:,:3].astype(int);r,g,b=np.moveaxis(rgb,-1,0);paint=(b>r*1.08)|(b>g*1.16)|(g>r*1.12)
   mask=Image.fromarray(np.where((np.array(mask)>0)&paint,255,0).astype('uint8'))
  if d['kind']=='grain-sift':
   r,g,b=np.moveaxis(a[:,:,:3].astype(int),-1,0);paint=(r>165)&(g>145)&(b>105)&((r-g)<70)
   mask=Image.fromarray(np.where((np.array(mask)>0)&paint,255,0).astype('uint8'))
  directory=OUT/name;directory.mkdir(parents=True,exist_ok=True);srcs=[source(pp)];logical_mask=np.array(mask)>0
  clean=im.copy();clean.putalpha(ImageChops.multiply(im.getchannel('A'),ImageChops.invert(mask)))
  cleanentry=emit('industry-'+name+'-clean-base',clean,directory/'clean-base.png',srcs,'actual parent industry with only authored moving-pixel ownership Alpha removed; no inpainting, no added background or invented paint',category='industry-animation-clean-base',parentArtId=parent['id'],sourceRequirementIds=parent.get('sourceRequirementIds',[]))
  newassets.append(cleanentry)
  maskrgba=Image.new('RGBA',(512,512),'white');maskrgba.putalpha(mask);maskpath=directory/'ownership-mask.png';maskrgba.save(maskpath);savej(Path(str(maskpath)+'.derivation.json'),{'file':rel(maskpath),'sha256':sha(maskpath),'operation':'authored binary moving-region ownership matte; geometric metadata, not a generated game painting','derivedFrom':srcs,'nativeModelGeneration':False,'shape':{k:d[k]for k in ['ellipse','polys']if k in d},'materialSelection':'see build_industry_bindings.py for native-paint channel mask constraints','spriteUse':'mask data only, not a visible sprite'})
  moving0=im.copy();moving0.putalpha(ImageChops.multiply(im.getchannel('A'),mask));frames=[];assembled=[];assembledrecs=[];parameters=[];centres=[]
  for f in range(12):
   phase=2*math.pi*f/12
   if d['kind']=='pump-beam-rock':
    angle=1.25*math.sin(phase);part=moving0.rotate(angle,Image.Resampling.BICUBIC,center=tuple(d['pivot']));joint=Image.new('L',(512,512),255);ImageDraw.Draw(joint).polygon([(249,189),(270,194),(270,207),(252,205)],fill=0);part.putalpha(ImageChops.multiply(part.getchannel('A'),joint));par={'angleDegrees':angle,'pivotPx':d['pivot'],'fixedSupportForegroundPatchExcluded':True,'fixedFrontJointPolygonPx':[(249,189),(270,194),(270,207),(252,205)]}
   else:
    part=texture_motion(im,mask,phase,d['kind'],d['pivot']);par={'phaseRadians':phase,'method':'actual parent mechanism RGB inverse sampling inside fixed ownership Alpha; unchanged painted boundary','pivotPx':d['pivot']}
   out=clean.copy();out.alpha_composite(part)
   p=directory/'moving'/f'{f:02d}.png';entry=emit('industry-'+name+'-bound-'+f'{f:02d}',part,p,srcs,'actual parent moving-pixel crop + declared deterministic '+d['kind']+'; full512 attachment layer already positioned in parent coordinates; not a new native pose',frame=f,phase=f/12,parameters=par,parentArtId=parent['id'],sourceRequirementIds=['animation-industry-machinery']);newassets.append(entry);frames.append(entry['image']);parameters.append(par)
   ap=PRE/name/f'{f:02d}.png';ae=emit('preview-'+name+'-'+str(f),out,ap,[source(R/cleanentry['image']),source(p)],'exact clean-base plus already-positioned moving layer composition; validation preview only, no model generation')
   assembled.append(out);assembledrecs.append(ae)
   check(name+'.frame'+str(f)+'.size-alpha',part.size==(512,512)and part.mode=='RGBA'and part.getchannel('A').getextrema()[0]==0)
   check(name+'.frame'+str(f)+'.full-parent-anchor',entry['anchorPx']==[256,448])
   # Fixed lower foundation, support and roof are exactly unchanged outside motion ownership/swept area.
   check(name+'.frame'+str(f)+'.fixed-foundation',out.crop((0,366,512,512)).tobytes()==im.crop((0,366,512,512)).tobytes())
   if d['kind']!='pump-beam-rock':check(name+'.frame'+str(f)+'.complete-original-alpha',out.getchannel('A').tobytes()==im.getchannel('A').tobytes())
  rgbframes=[]
  for o in assembled:
   matte=Image.new('RGBA',(512,512),'#e7e1ce');matte.alpha_composite(o);rgbframes.append(matte.convert('RGB'))
  gp=PRE/(name+'.gif');gp.parent.mkdir(parents=True,exist_ok=True);rgbframes[0].save(gp,save_all=True,append_images=rgbframes[1:],duration=[100]*12,loop=0,optimize=False,disposal=2)
  savej(Path(str(gp)+'.derivation.json'),{'file':rel(gp),'sha256':sha(gp),'operation':'100ms GIF preview of exact full-parent assembled derivative frames, matte background; not video generation','derivedFrom':[{'file':a['image'],'sha256':a['sha256']}for a in assembledrecs],'nativeModelGeneration':False})
  panel=Image.new('RGB',(1024,840),'#e7e1ce');dd=ImageDraw.Draw(panel)
  for f,o in enumerate(assembled):
   o=o.resize((256,256),Image.Resampling.LANCZOS);matte=Image.new('RGBA',(256,256),'#e7e1ce'if f%2==0 else'#244139');matte.alpha_composite(o);panel.paste(matte.convert('RGB'),(f%4*256,f//4*280));dd.text((f%4*256+5,f//4*280+258),f'{name} / {f}',font=font,fill='#194d3b')
  jp=PRE/(name+'-phases.jpg');panel.save(jp,quality=96);savej(Path(str(jp)+'.derivation.json'),{'file':rel(jp),'sha256':sha(jp),'operation':'labeled downsampled light/dark contact sheet of exact full-parent assembled frames','derivedFrom':[{'file':a['image'],'sha256':a['sha256']}for a in assembledrecs],'nativeModelGeneration':False})
  # Exact first-frame assembly is separately recorded; surface loops preserve Alpha and never stack above the old pose.
  fixedarea=clean.getchannel('A').point(lambda v:255 if v else 0)
  check(name+'.moving-region-removed-from-clean-base',all(np.array(clean)[:,:,3][logical_mask]==0))
  check(name+'.has-motion',len({hashlib.sha256(o.tobytes()).hexdigest()for o in assembled})>=4)
  check(name+'.no-canvas-clipping',all(o.getbbox()and o.getbbox()[0]>0 and o.getbbox()[1]>0 and o.getbbox()[2]<512 and o.getbbox()[3]<512 for o in assembled))
  bind={'animationId':'industry-'+name,'parentArtId':parent['id'],'parentImage':parent['image'],'parentSha256':parent['sha256'],'cleanBaseArtId':cleanentry['id'],'cleanBaseImage':cleanentry['image'],'ownershipMask':rel(maskpath),'ownershipMaskSha256':sha(maskpath),'frameCanvasPx':[512,512],'frameCoordinateSpace':'complete parent compound pixels; offset zero','attachmentOffsetPx':[0,0],'attachmentScale':1.0,'parentAnchorPx':[256,448],'movingMechanismPivotPx':d['pivot'],'layerOrder':['cleanBase','movingMechanism'],'mustReplaceParentStaticArt':True,'drawParentOriginalSimultaneously':False,'description':d['description'],'originalDetachedPartRole':'supplementary art-kit part only; it is not assumed to fit this parent','nativePoseGenerationClaim':False,'assemblyPreviewGIF':rel(gp),'assemblyPreviewFrames':[a['image']for a in assembledrecs],'assemblyContactSheet':rel(jp),'parametersByFrame':parameters,'status':'needs-installed-visual-review'}
  bindings.append(bind);m['animations'].append({'id':'industry-'+name,'frames':frames,'durationsMs':[100]*12,'loop':True,'canvas':[512,512],'width':512,'height':512,'anchorPx':[256,448],'method':d['kind'],'status':'needs-installed-visual-review','nativeFrameCount':0,'generatedPartCount':0,'artSource':'deterministic extraction/transform of actual parent mechanism','binding':bind,'assemblyPreviewGIF':rel(gp),'replaceLayer':'replace complete original industry with cleanBase + attached moving layer; do not add above parent original'})
 m['assets']+=newassets;m['mechanismBindings']=bindings;m['counts'].update({'mechanicalLoopFrames':72,'mechanicalLoops':6,'attachedMechanicalCleanBases':6,'attachedMechanicalLayerCanvas':[512,512],'formalSpritePNGs':len(m['assets']),'mechanismBindingCount':6})
 m['renderingContract']['mechanicalAttachmentContract']='all6 loops have explicit actual parent art, clean-base Alpha removal, ownership matte, fixed parent-coordinate placement and full installed animation preview'
 m['limitations']=[s for s in m.get('limitations',[])if not s.startswith('6组机械')]
 m['limitations'].append('6组机械使用实际父产业原画中的运动区域；清空原姿态后绑定全512图层，不将不匹配的独立机械母件硬叠。煤矿轮/玩具齿轮/钻轴/喷流/糖粒采用固定轮廓内真实画面材质运动；油井梁为短行程二维旋转，均非新AI三维姿态。')
 savej(MP,m)
 savej(R/'records/world-production/industry-binding-validation.json',{'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(checks),'passed':sum(c['passed']for c in checks),'failures':failures,'allChecks':checks,'bindings':bindings,'visualReview':'needs actual installed phase/GIF review','unityValidated':False})
 print(json.dumps({'bindings':6,'assets':len(m['assets']),'checks':len(checks),'failures':failures},ensure_ascii=False))
if __name__=='__main__':main()

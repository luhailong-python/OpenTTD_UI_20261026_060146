"""Animate the actual painted airport moving parts, keeping their supports fixed."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import numpy as np,math,json
from scipy import ndimage
from build_airport_modules import R,OUT,readj,savej,sha,saveasset
def mask_from_native(entry,poly):
 l,t,r,b=entry['sourceCropXYXY'];s=entry['uniformScale'];pw=round((r-l)*s);ph=round((b-t)*s);off=(256-pw//2,448-ph)
 pts=[(round(off[0]+(x-l)*s),round(off[1]+(y-t)*s))for x,y in poly];mask=Image.new('L',(512,512));ImageDraw.Draw(mask).polygon(pts,fill=255);return mask,pts,off
def warp_windsock(im,pivot_x,tail_x,phase):
 arr=np.asarray(im).astype(float)/255;alpha=arr[:,:,3];premul=arr[:,:,:3]*alpha[:,:,None];yy,xx=np.mgrid[:512,:512].astype(float);t=np.clip((xx-pivot_x)/(tail_x-pivot_x),0,1);offset=4*np.sin(phase+t*3.5)*t*t;coords=[yy-offset,xx];newa=ndimage.map_coordinates(alpha,coords,order=1,mode='constant',cval=0);rgb=np.stack([ndimage.map_coordinates(premul[:,:,k],coords,order=1,mode='constant',cval=0)for k in range(3)],axis=-1);rgb=np.divide(rgb,newa[:,:,None],out=np.zeros_like(rgb),where=newa[:,:,None]>1e-7);return Image.fromarray(np.uint8(np.clip(np.dstack([rgb,newa])*255,0,255))),{'tailAmplitudePx':4,'phase':phase,'pivotXPx':pivot_x,'tailXPx':tail_x,'method':'premultiplied actual cloth pixel inverse warp; pole and mouth remain fixed'}
def build():
 m=readj(OUT/'manifest.json');m['assets']=[e for e in m['assets']if e['category']!='airport-animation'];by={e['id']:e for e in m['assets']};anims=[]
 defs=[('radar','airport-radar-scan',12,[(654,10),(804,5),(885,56),(914,143),(910,222),(867,245),(720,219),(675,163),(650,78)]),('windsock','airport-windsock-flutter',8,[(1224,70),(1275,89),(1419,132),(1421,177),(1263,153),(1223,151)])]
 for prop,ident,N,poly in defs:
  e=by['airport-'+prop];base=Image.open(R/e['image']).convert('RGBA');mask,formalpoly,off=mask_from_native(e,poly);moving=base.copy();moving.putalpha(ImageChops.multiply(base.getchannel('A'),mask));rest=base.copy();rest.putalpha(ImageChops.multiply(base.getchannel('A'),ImageChops.invert(mask)));frames=[];entries=[]
  pivotnative=(755,248)if prop=='radar'else(1248,116);l,t,r,b=e['sourceCropXYXY'];s=e['uniformScale'];pivot=(off[0]+(pivotnative[0]-l)*s,off[1]+(pivotnative[1]-t)*s)
  for frame in range(N):
   phase=frame/N*2*math.pi;details={}
   if prop=='radar':
    angle=9*math.sin(phase);piece=moving.rotate(angle,Image.Resampling.BICUBIC,center=pivot);details={'angleDegrees':angle,'pivotPx':list(pivot),'motion':'projected dish elevation sweep +/-9deg, not generated full360 yaw'}
   else:piece,details=warp_windsock(moving,pivot[0],off[0]+(1417-l)*s,phase)
   im=rest.copy();im.alpha_composite(piece);a=saveasset('animations/'+ident+'/'+str(frame).zfill(2),im,{'file':e['image'],'sha256':e['sha256'],'record':e['image']+'.derivation.json'},'actual painted moving-part ownership mask, fixed support; projected dish rigid sweep or premultiplied cloth warp; deterministic derivative, not native generated poses',{'frame':frame,'animationId':ident,'ownershipPolygonNative':poly,'ownershipPolygonFormal':formalpoly,'parameters':details,'sourceRequirementIds':['airport-tile-31-radar-grass-fence-sw','airport-tile-51-radar-fence-sw','airport-tile-52-radar-fence-ne']if prop=='radar'else['airport-tile-39-grass-fence-ne-flag','airport-tile-73-grass-fence-ne-flag-2']},category='airport-animation');m['assets'].append(a);entries.append(a);frames.append(a['image'])
  sheet=Image.new('RGBA',(2048,math.ceil(N/4)*512))
  for i,e1 in enumerate(entries):sheet.alpha_composite(Image.open(R/e1['image']).convert('RGBA'),((i%4)*512,(i//4)*512))
  p=OUT/'animations'/ident/'sheet.png';sheet.save(p);se={'file':p.relative_to(R).as_posix(),'sha256':sha(p),'width':sheet.width,'height':sheet.height,'operation':'lossless4-column packing of declared actual derivative frame PNGs','derivedFrom':[{'file':a['image'],'sha256':a['sha256'],'record':a['image']+'.derivation.json'}for a in entries],'nativeModelGeneration':False};savej(Path(str(p)+'.derivation.json'),se)
  anims.append({'id':ident,'frames':frames,'durationsMs':[100 if prop=='radar'else 120]*N,'loop':True,'width':512,'height':512,'anchorPx':[256,448],'pivotUnity':[.5,.125],'nativeFrameCount':0,'nativeMovingPartCount':1,'sourceOriginalAnimationFrameCount':12 if prop=='radar'else 4,'method':'projected part sweep'if prop=='radar'else'cloth flutter pixel warp','sheet':se,'grid':[4,math.ceil(N/4)],'status':'needs-motion-review','replaceLayer':'replace static airport module in tile layers; do not stack over complete baked tile with original pose'})
 m['animations']=anims;m['counts']['animationFrames']=20;m['counts']['animationSheets']=2;m['counts']['formalSpritePNGs']=len(m['assets']);m['counts']['packagedPNGs']=len(m['assets'])+2;savej(OUT/'manifest.json',m)
 # Display phases on matte to inspect actual alpha rather than hiddenRGB.
 for a in anims:
  N=len(a['frames']);panel=Image.new('RGB',(1024,math.ceil(N/4)*280),'#dfdacb');d=ImageDraw.Draw(panel)
  for k,f in enumerate(a['frames']):
   im=Image.open(R/f).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(256,256),'#dfdacb'if k%2==0 else'#244139');bg.alpha_composite(im);panel.paste(bg.convert('RGB'),((k%4)*256,(k//4)*280));d.text(((k%4)*256+8,(k//4)*280+258),str(k),fill='#305943')
  panel.save(R/'previews/world/airports'/(a['id']+'-phases.jpg'),quality=95)
 print(json.dumps({'animations':len(anims),'frames':20,'fixedSupport':True,'nativeFrameCount':0}))
if __name__=='__main__':build()



"""Restore complete existing native solid bodies cut by equal atlas-cell bounds."""
from pathlib import Path
from PIL import Image
from scipy.ndimage import label,find_objects,distance_transform_edt
import numpy as np,json
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def isolated_body(sheet,index):
 ar=np.asarray(sheet);core=ar[...,3]>12;labs,n=label(core,np.ones((3,3)));sizes=np.bincount(labs.ravel());large=np.where(sizes>=10000)[0];large=large[large!=0];labs[~np.isin(labs,large)]=0;boxes=find_objects(labs);cx=(index%3+.5)*sheet.width/3;cy=(index//3+.5)*sheet.height/3
 owner=min(large,key=lambda k:(((boxes[k-1][1].start+boxes[k-1][1].stop)/2-cx)**2+((boxes[k-1][0].start+boxes[k-1][0].stop)/2-cy)**2));dist,inds=distance_transform_edt(labs==0,return_indices=True);near=labs[tuple(inds)];keep=(near==owner)&(dist<=10);out=ar.copy();out[~keep]=0;out[out[...,3]==0,:3]=0;ys,xs=np.where(out[...,3]>0);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];crop=Image.fromarray(out).crop(box);scale=min(1,480/crop.width,480/crop.height)
 if scale<1:crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 target=Image.new('RGBA',(512,512));at=((512-crop.width)//2,(512-crop.height)//2);target.alpha_composite(crop,at);b=boxes[owner-1];corebox=[b[1].start,b[0].start,b[1].stop,b[0].stop]
 return target,{'nativeSourceRectXYXY':box,'nativeCoreBBox':corebox,'fullNativeCoreRetained':box[0]<=corebox[0]and box[1]<=corebox[1]and box[2]>=corebox[2]and box[3]>=corebox[3],'scale':scale,'paddingLeftTop':list(at),'AlphaOwnership':'nearest9large native body cores within10native pixels; all retained RGB/Alpha sampled from real source; not equal-cell cropping','registration':'complete body bounding box centred on512canvas, no enlargement; same normalized[.5,.5] art anchor'}
def main():
 src=R/'source-art/world/disaster-air-props.png';sheet=Image.open(src).convert('RGBA');changes=[]
 for index,name in [(1,'zeppelin-crashing'),(5,'ufo-big'),(6,'combat-airplane'),(8,'ufo-destroyer')]:
  mp=R/'assets/world/effects/disasters'/name/'manifest.json';q=load(mp);a=q['frames'][0];p=R/a['file'];old=wp.sha(p);im,info=isolated_body(sheet,index);im.save(p);a['sha256']=wp.sha(p);a['operation']='complete existing native disaster body isolated beyond equal-cell boundaries; Alpha ownership around real body core; centred transparent512canvas with no enlargement; no new paint';a['sources']=[{'derivedFrom':{'file':wp.rel(src),'sha256':wp.sha(src),'record':wp.rel(src)+'.generation.json'},**info}];q['operation']=a['operation'];wp.writej(mp,q);wp.writej(Path(str(p)+'.derivation.json'),a);changes.append({'file':a['file'],'beforeSha256':old,'sha256':a['sha256'],**info});preview(im,name)
  if name=='zeppelin-crashing':continue
  shadow=Image.new('RGBA',(512,512));flat=im.resize((512,200),Image.Resampling.LANCZOS);sil=Image.new('RGBA',flat.size,(27,43,38,0));sil.putalpha(flat.getchannel('A').point(lambda a:round(a*.30)));shadow.alpha_composite(sil,(0,156));sm=R/'assets/world/effects/disasters'/(name+'-shadow')/'manifest.json';sq=load(sm);sa=sq['frames'][0];sp=R/sa['file'];old=wp.sha(sp);shadow.save(sp);sa['sha256']=wp.sha(sp);sa['operation']='shadow from complete repaired native body Alpha; vertical scale200/512 and30percent opacity; no new paint';sa['sources']=[{'derivedFrom':{'file':a['file'],'sha256':a['sha256'],'record':a['file']+'.derivation.json'},'verticalScale':200/512,'alphaMultiplier':.30}];sq['operation']=sa['operation'];wp.writej(sm,sq);wp.writej(Path(str(sp)+'.derivation.json'),sa);changes.append({'file':sa['file'],'beforeSha256':old,'sha256':sa['sha256'],'dependentShadow':a['file']});preview(shadow,name+'-shadow')
 wp.writej(R/'records/world-production/disaster-native-bounds-repair.json',{'createdAt':wp.now(),'scope':'Actual source viewed;4solid body native cores crossed equal-cell bounds. Restored complete present paintings and3dependent shadows. No image generation.','changes':changes,'canvasPivotChanged':False,'nativeUpscale':False,'unityValidated':False});print(json.dumps(changes,ensure_ascii=False))
def preview(im,name):
 bg=Image.new('RGBA',im.size,'#263F39');bg.alpha_composite(im);bg=bg.convert('RGB');bg.thumbnail((256,256));bg.save(R/'previews/world/effects'/('disasters-'+name+'.gif'),duration=1000,loop=1,disposal=2)
if __name__=='__main__':main()

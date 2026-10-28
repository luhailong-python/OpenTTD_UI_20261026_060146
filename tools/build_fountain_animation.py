from PIL import Image,ImageChops,ImageEnhance,ImageFilter
from pathlib import Path
import math,json,numpy as np
import world_pack as wp
import build_world_services as s
import build_world_terrain as t
R=wp.ROOT
def main():
 hp=json.loads((R/'assets/world/houses/manifest.json').read_text());binding=next(m for m in hp['coverageMappings']if m['sourceHouseTileId']==10);st=next(v for v in binding['states']if v['locationVariant']==0 and v['constructionStage']==3);src=next(a for a in hp['assets']if a['id']==st['assetId']);raw=Image.open(R/src['image']).convert('RGBA')
 a=np.asarray(raw);r,g,b=np.moveaxis(a[...,:3].astype(float),-1,0);y,x=np.mgrid[:raw.height,:raw.width];select=(b>g*.90)&(g>r*1.07)&(y>240)&(a[...,3]>40);mask=Image.fromarray(np.uint8(select)*255).filter(ImageFilter.GaussianBlur(.6));frames=[];entries=[];out='assets/world/infrastructure/fountain-animation'
 for fi in range(8):
  phase=fi*math.tau/8;offset=1.3*math.sin(phase);layer=raw.transform(raw.size,Image.Transform.AFFINE,(1,0,0,0,1,offset),Image.Resampling.BICUBIC);layer=ImageEnhance.Brightness(layer).enhance(1+.045*math.cos(phase));layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask));im=raw.copy();im.alpha_composite(layer)
  en=s.emit(out,'fountain-frame-'+str(fi),im,[s.ref(src)],'actual painted completed sourceHouse010 fountain; fixed body/ground with cyan water-only texture-coordinate shift≤1.3px and ±4.5% water luminance cycle;8 deterministic samples, not new native water or video frames',{'category':'fountain-animation','sourceRequirementIds':['animation-fountain'],'frame':fi,'houseSourceID':10,'status':'produced-needs-loop-review','waterMaskRule':'B>.90G andG>1.07R, Y>240, Alpha>40; .6px mask feather','staticBodyReplacement':True},src['anchorPx']);entries.append(en);frames.append(en['image'])
 anim={'id':'fountain-water-loop','category':'town','frames':frames,'durationsMs':[120]*8,'loop':True,'frameSize':list(raw.size),'fixedAnchorPx':src['anchorPx'],'sourceRequirementIds':['animation-fountain'],'method':'one actual fountain water layer sampled at8 small texture offsets/luminance phases; no fluid simulation','binding':{'sourceHouseID':10,'replaceStaticSourceArt':True,'bodyStaticPNG':src['image'],'drawBothStaticAndAnimated':False}}
 wp.writej(R/out/'manifest.json',{'schema':'cloud-route.world-art.v1','assets':entries,'animations':[anim],'coverageMappings':[{'requirementId':'animation-fountain','files':frames,'sourceHouseID':10,'animationId':anim['id'],'renderRule':'replace completed static fountain image; never overlay a second complete building','sourceNativeFrames':1,'derivedFrames':8}],'qa':[],'acceptance':'water-only8phase cycle produced; contact and loop review pending'})
 t.contact(entries,'fountain-loop-contact.jpg',4,220)
 imgs=[]
 for file in frames:
  im=Image.new('RGBA',raw.size,'#244b3d');im.alpha_composite(Image.open(R/file).convert('RGBA'));imgs.append(im.convert('RGB'))
 p=R/'previews/world/fountain-loop.gif';imgs[0].save(p,save_all=True,append_images=imgs[1:],duration=120,loop=0)
 wp.writej(str(p)+'.derivation.json',{'file':wp.rel(p),'sha256':wp.sha(p),'derivedFrom':[s.ref(a)for a in entries],'operation':'actual formal8PNG cycle composite on dark preview background;GIF timing preview only'})
 print(json.dumps({'frames':8,'sourceHouseId':10,'actualWaterSelectedPixels':int(select.sum())}))
if __name__=='__main__':main()

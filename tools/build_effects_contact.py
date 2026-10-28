"""All delivered effect/disaster PNGs as pixel-derived review contact pages."""
from PIL import Image,ImageDraw
import json,math
import world_pack as wp
import build_world_terrain as t
R=wp.ROOT
def main():
 q=json.loads((R/'docs/WORLD_ASSET_MANIFEST.json').read_text(encoding='utf8'));aa=[a for a in q['assets']if a['image'].startswith('assets/world/effects/')];pages=[]
 for start in range(0,len(aa),35):
  part=aa[start:start+35];im=Image.new('RGB',(1400,math.ceil(len(part)/5)*185),(33,62,55));d=ImageDraw.Draw(im)
  for n,a in enumerate(part):
   x=n%5*280;y=n//5*185;raw=Image.open(R/a['image']).convert('RGBA');raw.thumbnail((260,147));im.paste(raw,(x+(280-raw.width)//2,y),raw);d.text((x+6,y+148),a['id'].replace('frame-','')[:37],font=t.font(12),fill=(246,235,207));d.text((x+6,y+165),str((a['width'],a['height'])),font=t.font(11),fill=(200,207,188))
  p=R/'previews/world/effects'/('all-formal-contact-'+str(start//35+1)+'.jpg');im.save(p,quality=95);pages.append({'file':wp.rel(p),'sha256':wp.sha(p),'assetImages':[{'file':a['image'],'sha256':wp.sha(R/a['image'])}for a in part]})
 wp.writej(R/'records/world-production/effects-contact-index.json',{'createdAt':wp.now(),'scope':'All formal effects/disaster PNGs from current total manifest; contact thumbnails are deterministic layout derivatives, not new model images','sourceManifestSha256':wp.sha(R/'docs/WORLD_ASSET_MANIFEST.json'),'formalAssetCount':len(aa),'pages':pages})
 print('effects contact',len(aa),'PNG',len(pages),'pages')
if __name__=='__main__':main()

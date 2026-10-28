"""Remove proven neighbouring-cell fragments from two solid-body props only.
Particle, smoke and spark sprites are deliberately excluded from component pruning.
"""
from pathlib import Path
from PIL import Image
from scipy.ndimage import label
import numpy as np,json
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 history=[]
 for name in ['ufo-small-dark','combat-helicopter']:
  mp=R/'assets/world/effects/disasters'/name/'manifest.json';q=load(mp);a=q['frames'][0];p=R/a['file'];old=wp.sha(p);im=Image.open(p).convert('RGBA');ar=np.asarray(im).copy();lab,num=label(ar[...,3]>0,structure=np.ones((3,3)));counts=np.bincount(lab.ravel());counts[0]=0;owner=int(counts.argmax());keep=lab==owner;removed=int(((ar[...,3]>0)&~keep).sum());ar[~keep]=0;ar[ar[...,3]==0,:3]=0;clean=Image.fromarray(ar);clean.save(p)
  a['sha256']=wp.sha(p);a['operation']='actual native solid disaster body, fixed original canvas/pivot; keep largest8-connected Alpha component, remove proven neighbouring-cell body fragments; original retained-body pixels unchanged; transparent RGB cleared'
  a['alphaOwnershipRepair']={'method':'largest8-connected nonzero-Alpha component, solid body only','removedVisiblePixels':removed,'retainedBodyRGBAUnchanged':bool(np.array_equal(np.asarray(im)[keep],ar[keep])),'canvasPivotUnchanged':True,'nativeModelGeneration':False}
  q['operation']=a['operation'];wp.writej(mp,q);wp.writej(Path(str(p)+'.derivation.json'),a)
  bg=Image.new('RGBA',clean.size,'#263F39');bg.alpha_composite(clean);bg=bg.convert('RGB');bg.thumbnail((256,256));gif=R/'previews/world/effects'/('disasters-'+name+'.gif');bg.save(gif,duration=1000,loop=1,disposal=2)
  history.append({'file':a['file'],'beforeSha256':old,'sha256':a['sha256'],'removedVisiblePixels':removed,'retainedBodyRGBAUnchanged':a['alphaOwnershipRepair']['retainedBodyRGBAUnchanged'],'previewGIF':wp.rel(gif),'previewGIFSha256':wp.sha(gif)})
 # The helicopter shadow depended on the rejected neighbouring pixels too.
 bodyPath=R/'assets/world/effects/disasters/combat-helicopter/00.png';body=Image.open(bodyPath).convert('RGBA');flat=body.resize((512,200),Image.Resampling.LANCZOS);shadow=Image.new('RGBA',(512,512));sil=Image.new('RGBA',flat.size,(27,43,38,0));sil.putalpha(flat.getchannel('A').point(lambda a:round(a*.30)));shadow.alpha_composite(sil,(0,156))
 mp=R/'assets/world/effects/disasters/combat-helicopter-shadow/manifest.json';q=load(mp);a=q['frames'][0];p=R/a['file'];old=wp.sha(p);shadow.save(p);a['sha256']=wp.sha(p);a['operation']='shadow projected from current cleaned native helicopter body Alpha; vertical scale200/512 and30percent opacity; no detached neighbouring-cell shadows';a['sources']=[{'derivedFrom':{'file':wp.rel(bodyPath),'sha256':wp.sha(bodyPath),'record':wp.rel(bodyPath)+'.derivation.json'},'verticalScale':200/512,'alphaMultiplier':.30,'silhouetteTint':[27,43,38]}];q['operation']=a['operation'];wp.writej(mp,q);wp.writej(Path(str(p)+'.derivation.json'),a)
 bg=Image.new('RGBA',shadow.size,'#263F39');bg.alpha_composite(shadow);bg=bg.convert('RGB');bg.thumbnail((256,256));gif=R/'previews/world/effects/disasters-combat-helicopter-shadow.gif';bg.save(gif,duration=1000,loop=1,disposal=2);history.append({'file':a['file'],'beforeSha256':old,'sha256':a['sha256'],'dependentRepair':'regenerated shadow from cleaned helicopter body Alpha','previewGIF':wp.rel(gif),'previewGIFSha256':wp.sha(gif)})
 rp=R/'records/world-production/disaster-alpha-repair.json';prev=load(rp)if rp.is_file()else None
 wp.writej(rp,{'createdAt':wp.now(),'scope':'Two proven solid-body neighbouring-cell fragments and dependent helicopter shadow; no particle pruning, no new model generation','files':history,'previousRepair':prev if prev and any(x.get('removedVisiblePixels',0)>0 for x in prev.get('files',[]))else None,'unityValidated':False})
 print(json.dumps(history,ensure_ascii=False))
if __name__=='__main__':main()

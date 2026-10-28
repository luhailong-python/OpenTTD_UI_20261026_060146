"""Original family art -> explicit original EngineID livery/load model mappings.
No AI generation and no fictional claim of256 independent native paintings.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageOps
import numpy as np,json,hashlib,math,datetime,sys
R=Path(__file__).resolve().parents[1];D=R/'docs';OUT=R/'assets/world/vehicles/models'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def reference(p):return{'file':p.relative_to(R).as_posix(),'sha256':sha(p),'record':p.relative_to(R).as_posix()+('.generation.json'if Path(str(p)+'.generation.json').exists()else'.derivation.json')}
CARGO={'CT_CANDY':'sweets','MCT_GRAIN_WHEAT_MAIZE':'grain','MCT_VALUABLES_GOLD_DIAMONDS':'valuables'}
def cargoid(code):return CARGO.get(code,str(code).replace('CT_','').lower().replace('_','-'))
def livery(im,index):
 arr=np.array(im);hsv=np.array(im.convert('RGB').convert('HSV'));mask=(hsv[:,:,0]>60)&(hsv[:,:,0]<155)&(hsv[:,:,1]>30)&(arr[:,:,3]>0)
 delta=((index*7)%17)-8;gain=.94+((index*11)%13)/100
 hsv[:,:,0]=np.where(mask,(hsv[:,:,0].astype(int)+delta)%256,hsv[:,:,0]);hsv[:,:,2]=np.where(mask,np.clip(hsv[:,:,2].astype(float)*gain,0,255),hsv[:,:,2])
 out=Image.fromarray(hsv,'HSV').convert('RGB').convert('RGBA');out.putalpha(im.getchannel('A'));return out,{'jadeHueOffset256':delta,'jadeValueMultiplier':gain,'preserveWarmIvoryAndGold':True}
def load_overlay(body,family,direction,cargo):
 src=R/'assets/cargo'/f'{cargo}.png'
 if not src.exists():return body,None
 b=body.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox();L,T,RR,B=b;w=RR-L;h=B-T
 isroad=family.startswith('road-');isflat=family in ['wagon-flat','road-flat'];isship=family=='ship-cargo'
 # Explicit load bay position for each screen heading. These are art assembly
 # guides, not runtime collision volumes. Closed tanks/boxes have no external load.
 heading={'N':(0,-1),'NE':(.707,-.707),'E':(1,0),'SE':(.707,.707),'S':(0,1),'SW':(-.707,.707),'W':(-1,0),'NW':(-.707,-.707)}[direction]
 dx,dy=heading
 cx=L+w*(.5-.18*dx if isroad else .5+.08*dx if isship else .5)
 cy=T+h*(.42-.19*dy if isroad else .51+.12*dy if isship else .32)
 bw=w*(.38 if isroad else .48 if isship else .66);bh=h*(.28 if isroad else .32 if isship else .30)
 if direction in ['E','W']:bh*=.55
 if direction in ['N','S']:bw*=.75;bh*=1.3
 image=Image.open(src).convert('RGBA');bb=image.getbbox();image=image.crop(bb)
 factor=min(bw/image.width,bh/image.height,1);image=image.resize((max(1,round(image.width*factor)),max(1,round(image.height*factor))),Image.Resampling.LANCZOS)
 if direction in ['SW','W','NW']:image=ImageOps.mirror(image)
 layer=Image.new('RGBA',(512,512));paste=(round(cx-image.width/2),round(cy-image.height/2));layer.alpha_composite(image,paste)
 # Keep hopper fill within the actual dark painted interior and away from gold
 # rim or exterior side panels. Other open decks use the visible stack silhouette.
 if family=='wagon-hopper':
  a=np.array(body);rgb=a[:,:,:3].astype(int);neutral=(rgb.max(2)-rgb.min(2)<25)&(rgb.mean(2)<150)&(a[:,:,3]>64)
  region=Image.new('L',(512,512));ImageDraw.Draw(region).ellipse((cx-bw/2,cy-bh/2,cx+bw/2,cy+bh/2),fill=255)
  mask=np.array(region)>0;sel=Image.fromarray((neutral&mask).astype('uint8')*255)
  layer.putalpha(ImageChops.multiply(layer.getchannel('A'),sel))
 result=body.copy();result.alpha_composite(layer)
 return result,{'file':src.relative_to(R).as_posix(),'sha256':sha(src),'record':src.relative_to(R).as_posix()+'.generation.json','sourceCargoIconReused':True,'operation':'downscale painted cargo prop; optional horizontal mirror; place in explicit facing load bay; hopper clipped to painted interior','paste':list(paste),'cargoSize':list(image.size),'loadBayCenter':[round(cx,2),round(cy,2)],'notNativeEightDirectionCargo':True}
def track_chassis(body,track,direction):
 if track not in ['monorail','maglev']:return body,None
 donorid='loco-monorail'if track=='monorail'else'loco-maglev';src=R/'assets/world/vehicles/families'/donorid/'E.png'
 donor=Image.open(src).convert('RGBA');rect=[45,331,441,374]if track=='monorail'else[64,331,440,371];piece=donor.crop(rect)
 bb=body.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox();L,T,RR,B=bb;w=RR-L;h=B-T
 if direction in ['NE','SW']:yl=T+h*.88;yr=T+h*.48
 elif direction in ['NW','SE']:yl=T+h*.48;yr=T+h*.88
 else:yl=yr=T+h*(.70 if direction in ['E','W']else .80)
 edgeL=L+w*.03;edgeR=RR-w*.03;edgeW=edgeR-edgeL;m=(yr-yl)/edgeW;thick=min(piece.height,h*.14)
 # Affine shear projects ONE clean painted guide/skirt strip along the body's
 # real diagonal lower edge. No borrowed locomotive nose/cab enters the wagon.
 sx=piece.width/edgeW;sy=piece.height/thick
 strip=piece.transform((512,512),Image.Transform.AFFINE,(sx,0,-edgeL*sx,-m*sy,sy,(m*edgeL-yl)*sy),Image.Resampling.BICUBIC)
 arr=np.array(body);yy,xx=np.indices((512,512));line=yl+m*(xx-edgeL);arr[:,:,3]=np.where(yy<line+2,arr[:,:,3],0)
 out=strip;out.alpha_composite(Image.fromarray(arr))
 return out,{'file':src.relative_to(R).as_posix(),'sha256':sha(src),'record':src.relative_to(R).as_posix()+'.derivation.json','crop':rect,'edge':[[edgeL,yl],[edgeR,yr]],'thickness':thick,'operation':'single painted technology guide-bogie/skirt strip cropped without nose/cab; affine projection along each facing lower edge; conventional wheels masked below that edge; alpha composite, deterministic derivative'}
def run():
 c=json.loads((D/'VEHICLE_PRODUCTION_CONTRACT.json').read_text(encoding='utf-8'));families={f['id']:json.loads((R/f['path']/'manifest.json').read_text(encoding='utf-8'))for f in c['families']}
 records=[];unique=0;emptyloaded=0
 for m in c['models']:
  out=OUT/str(m['id']).zfill(3);out.mkdir(parents=True,exist_ok=True);f=families[m['familyId']];sprites=[]
  for fr in f['frames']:
   source=R/fr['file'];im=Image.open(source).convert('RGBA');im,palette=livery(im,m['id']);sources=[reference(source)];ops=['jade region livery derivative; warm ivory/gold retained']
   if m['isWagon']:
    im,hardware=track_chassis(im,m['modelVariant']['trackHardware'],fr['direction'])
    if hardware:sources.append(hardware);ops.append(hardware['operation'])
   base=out/(fr['direction']+'-body.png');im.save(base);unique+=1
   states=m['requiredStates'];stateentries=[]
   for state in states:
    rendered=im;cargo=None
    if state=='loaded'and m['familyId']in ['wagon-hopper','wagon-flat','road-open','road-flat','ship-cargo']:
     rendered,cargo=load_overlay(im,m['familyId'],fr['direction'],cargoid(m['cargo']))
    p=base
    if cargo:
     p=out/(fr['direction']+'-loaded.png');rendered.save(p);unique+=1
    stateentries.append({'state':state,'file':p.relative_to(R).as_posix(),'sha256':sha(p),'usesBaseBody':p==base,'sharedBodyWhenClosed':state in ['empty','loaded']and m['familyId']not in ['wagon-hopper','wagon-flat','road-open','road-flat','ship-cargo'],'loadSource':cargo,'visuallyDifferentFromEmpty':cargo is not None and p!=base})
   e={'direction':fr['direction'],'canvas':[512,512],'pivot':fr['pivot'],'body':base.relative_to(R).as_posix(),'sha256':sha(base),'states':stateentries,'livery':palette,'sources':sources,'operations':ops,'nativeModelGeneration':False,'unityVerified':False}
   sprites.append(e)
  mm={'id':m['id'],'upstreamName':m['upstreamName'],'familyId':m['familyId'],'transport':m['type'],'cargo':m['cargo'],'climates':m['climates'],'source':m['source'],'trackHardware':m['modelVariant']['trackHardware'],'sprites':sprites,'loadedThreshold':.5 if'loaded'in m['requiredStates']else None,'bodyMotion':'eight static direction sprites; translation owned by later engine','status':'local-art-generated','artReuseDisclosure':'27 independent native family atlases; per-EngineID jade livery, track chassis and visible cargo composites; closed body can share empty/loaded art; not256 independent paintings','sourceGenerationFamily':f['atlas'],'unityImport':'Sprite Single, alpha transparency, Bilinear, no mipmaps UI; world sampling verify in Unity, per-frame pivot inmanifest; PPU initial100'}
  save(out/'manifest.json',mm);m.update({'artStatus':'local-art-generated','manifest':(out/'manifest.json').relative_to(R).as_posix()});records.append(mm)
 c['production']={'completedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nativeFamilyAtlases':27,'nativeDirections':216,'mappedModels':len(records),'physicalModelPNGs':unique,'not256IndependentPaintings':True,'unityVerified':False}
 save(D/'VEHICLE_PRODUCTION_CONTRACT.json',c);save(D/'VEHICLE_RUNTIME_MANIFEST.json',{'schemaVersion':1,'referenceCommit':c['referenceCommit'],'counts':c['production'],'models':records})
 print(json.dumps(c['production']))
if __name__=='__main__':run()

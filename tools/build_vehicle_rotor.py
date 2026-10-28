from pathlib import Path
from PIL import Image
import json,hashlib,math
R=Path(__file__).resolve().parents[1];SRC=R/'source-art/world/vehicle-helicopter-rotor.png';OUT=R/'assets/world/vehicles/rotor';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
im=Image.open(SRC).convert('RGBA');crop=im.crop((10,60,617,566));master=Image.new('RGBA',(800,800));master.alpha_composite(crop,(400-(311-10),400-(286-60)))
frames=[]
for i in range(9):
 angle=0 if i==0 else(i-1)*90/8
 rotated=master.rotate(angle,resample=Image.Resampling.BICUBIC,center=(400,400))
 # Rigid prop rotation, then a single geometric projection to the horizontal
 # rotor plane. Painted source pixels only; not an AI animation ornew native art.
 projected=rotated.resize((400,200),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(projected,(56,156))
 if i:
  for offset in [-4,4]:
   ghost=master.rotate(angle+offset,resample=Image.Resampling.BICUBIC,center=(400,400)).resize((400,200),Image.Resampling.LANCZOS)
   ghost.putalpha(ghost.getchannel('A').point(lambda a:round(a*.12)));canvas.alpha_composite(ghost,(56,156))
 out=OUT/('stopped.png'if i==0 else f'phase-{i-1:02}.png');canvas.save(out)
 rec={'file':out.relative_to(R).as_posix(),'sha256':sha(out),'canvas':[512,512],'pivot':[.5,.5],'hubPx':[256,256],'operation':'selected actual four-blade stopped artwork; native crop + center registration; deterministic rigid angle rotation and50percentX/25percentY projection with low-alpha adjacent-angle ghosts while running; no new AI call','angleDegrees':angle,'derivedFrom':{'file':SRC.relative_to(R).as_posix(),'sha256':sha(SRC),'record':SRC.relative_to(R).as_posix()+'.generation.json'},'selectedSourceRectXYXY':[10,60,617,566],'actualModel':None,'actualQuality':None,'unverifiedReason':'Derived from source whose actual model/quality are not exposed by host.'}
 save(Path(str(out)+'.derivation.json'),rec);frames.append(rec)
finalanchors={'N':(255,132),'NE':(303,113),'E':(329,146),'SE':(279,148),'S':(256,140),'SW':(228,126),'W':(183,146),'NW':(209,116)}
family=R/'assets/world/vehicles/families/air-helicopter';j=json.loads((family/'manifest.json').read_text(encoding='utf-8'));attachments={}
for fr in j['frames']:
 attachments[fr['direction']]={'mainRotorHubPx':list(finalanchors[fr['direction']]),'rotorDisplayScale':.9,'artAnchorEstimate':True,'measuredOnFinalFacingPNG':True,'unityVerified':False}
manifest={'frames':frames,'clips':[{'id':'stopped','frames':['stopped.png'],'fps':0,'loop':False},{'id':'running','frames':[f'phase-{i:02}.png'for i in range(8)],'fps':24,'loop':True,'angularPeriodDegrees':90,'fourFoldSymmetry':True,'motionSource':'deterministic rigid mechanical prop transformation'}],'sourceReview':'Generated sheet returned stopped4blade but runningblade counts differ.Only correct stopped4blade accepted; native running cells unused. Formalrunningcycle is explicit mechanical derivative.','attachments':attachments,'unityVerified':False}
save(OUT/'manifest.json',manifest)
# Data-only attachment suggestions are linked for later integration.
j['effects']={'rotorManifest':'assets/world/vehicles/rotor/manifest.json','attachments':attachments};save(family/'manifest.json',j)
print('four-blade master;8 rigid running phases; fixedhub; all derived, noAIvideo')

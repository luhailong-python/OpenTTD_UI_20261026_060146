"""Freeze the actual local review after current contact/browser pages were opened.
Does not generate artwork or assert user/Unity acceptance.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
import world_pack as wp
import render_screens as ui
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 mp=R/'assets/common/micro-ui/manifest.json';bp=R/'docs/MICRO_UI_BINDINGS.json';m=load(mp);q=load(bp)
 # Existing button states, with exactly the same icon position in every state.
 states=[('normal','button_secondary_normal'),('pressed','button_secondary_pressed'),('selected','button_primary_selected'),('disabled','button_disabled'),('locked','button_secondary_normal')];panel=Image.new('RGBA',(1000,155),'#234b3d');d=ImageDraw.Draw(panel);font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),15);sources=[]
 for k,(state,bg)in enumerate(states):
  tile=ui.nine(bg,180,105);icon=Image.open(R/'assets/common/micro-ui/SPR_GROUP_CREATE_TRAIN.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
  if state=='disabled':icon.putalpha(icon.getchannel('A').point(lambda a:round(a*.4)))
  tile.alpha_composite(icon,(58,20))
  if state=='locked':lock=Image.open(R/'assets/common/micro-ui/SPR_LOCK.png').convert('RGBA').resize((30,30),Image.Resampling.LANCZOS);tile.alpha_composite(lock,(136,62))
  panel.alpha_composite(tile,(k*200+10,4));d.text((k*200+20,120),state,font=font,fill='#f3e6c6');sources.append({'file':ui.CM[bg]['file'],'sha256':wp.sha(R/ui.CM[bg]['file'])})
 f='previews/micro-ui/control-state-composition.jpg';panel.convert('RGB').save(R/f,quality=95);wp.writej(Path(str(R/f)+'.derivation.json'),{'file':f,'sha256':wp.sha(R/f),'operation':'existing native buttons via recorded9slice; same painted icon and fixed(58,20)64px registration across5states; disabled0.4Alpha,locked separate30px existingicon; offline art composition only','derivedFrom':sources+[{'file':'assets/common/micro-ui/SPR_GROUP_CREATE_TRAIN.png','sha256':wp.sha(R/'assets/common/micro-ui/SPR_GROUP_CREATE_TRAIN.png')},{'file':'assets/common/micro-ui/SPR_LOCK.png','sha256':wp.sha(R/'assets/common/micro-ui/SPR_LOCK.png')}],'unityValidated':False})
 # Review acceptance is tied to current PNGs, not to mere presence of bindings.
 for a in m['assets']:
  a['status']='locally-checked-user-review-pending';a['actualVisualReview']='records/micro-ui-visual-review.json';a['unityImport']['suggestedDisplayPx']=[48,64]if a.get('functionalGlyph')else[24,48];wp.writej(Path(str(R/a['image'])+'.derivation.json'),a)
 wp.writej(mp,m)
 for b in q['bindings']:b['localArtReviewed']=True;b['actualVisualReview']='records/micro-ui-visual-review.json'
 q['manifestSHA256']=wp.sha(mp);wp.writej(bp,q)
 paths=['previews/micro-ui/micro-ui-contact.jpg','records/micro-ui-browser-desktop.png','records/micro-ui-browser-groups.png','records/micro-ui-browser-palettes.png','records/micro-ui-browser-mobile.png','previews/micro-ui/blot-palettes.jpg']
 record={'reviewedAt':wp.now(),'reviewer':'pointer_icons production agent; actual contact/current browser PNG opened','localVisualPassed':True,'items':[{'file':f,'sha256':wp.sha(R/f),'status':'passed-local','finding':'Actually opened current contact/browser rendering. Native jade/ivory/gold artwork retained. Window arrows,4profit/4rating states,6group actions across4vehicle classes and single/all/chain sale scopes differ. Sixteen company swatches and3compatibility gems retain gold/native Alpha. Function badges are legible at48px;24px is a dense-list reference and should have an independent tooltip.'}for f in paths],'reviewedAssets':[{'file':a['image'],'sha256':a['sha256']}for a in m['assets']],'sourceRequirements':96,'formalPNGCount':len(m['assets']),'manifest':'assets/common/micro-ui/manifest.json','manifestSHA256':wp.sha(mp),'currentKnownLocalArtDefects':[],'artSourceClaim':'All illustrations reused from existing native-painted PNGs; geometry only encodes explicit UI actions/data. No image-model call, no new painting claim.','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/micro-ui-visual-review.json',record)
 print(json.dumps({'manifestSHA256':wp.sha(mp),'formalPNGCount':len(m['assets']),'statePreview':f,'note':'state strip must still be opened before its own review item is added'}))
if __name__=='__main__':main()

"""Final local art validation and preview for the airport pack; no Unity/runtime claims."""
from pathlib import Path
from PIL import Image,ImageChops
import json,re,hashlib,datetime,collections,math
from build_airport_modules import R,OUT,readj,savej,sha
PRE=R/'previews/world/airports'
def rel(p):return Path(p).relative_to(R).as_posix()
def main():
 m=readj(OUT/'manifest.json');assets=m['assets'];by={a['id']:a for a in assets};checks=[];fails=[]
 def check(name,value,details=None):
  ok=bool(value);checks.append({'check':name,'passed':ok,'details':details})
  if not ok:fails.append(checks[-1])
 source=(R/'reference/OpenTTD/src/table/airporttile_ids.h').read_text();enums=re.findall(r'\bAPT_[A-Z0-9_]+',re.search(r'enum AirportTiles[^\{]*\{(.*?)\};',source,re.S).group(1))
 check('74-source-enums',len(enums)==74);check('139-formal-sprites',len(assets)==139,len(assets));check('unique-ids',len(by)==len(assets))
 ids={a['sourceTileId']:a for a in assets if a['category']=='airport-tile'}
 check('74-tile-sprites',set(ids)==set(range(74)))
 for a in assets:
  p=R/a['image'];check(a['id']+'.file',p.is_file())
  im=Image.open(p);check(a['id']+'.size',im.size==(a['width'],a['height']))
  check(a['id']+'.alpha',im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getextrema()[1]>240)
  check(a['id']+'.hash',sha(p)==a['sha256']);check(a['id']+'.anchor',len(a['anchorPx'])==2 and 0<=a['anchorPx'][0]<im.width and 0<=a['anchorPx'][1]<im.height)
  check(a['id']+'.no-upscale',a.get('uniformScale',1)<=1 and not a['nativeUpscale'])
  rec=Path(str(p)+'.derivation.json');check(a['id']+'.derivation-record',rec.is_file())
  for i,s in enumerate(a['derivedFrom']):
   sp=R/s['file'];check(a['id']+'.source-'+str(i),sp.is_file()and sha(sp)==s['sha256'])
   check(a['id']+'.source-record-'+str(i),(R/s['record']).is_file())
  if im.size==(512,512):
   bb=im.getbbox();check(a['id']+'.no-canvas-clip',bb and bb[0]>0 and bb[1]>0 and bb[2]<512 and bb[3]<512,bb)
  if a['category']=='airport-tile':
   check(a['id']+'.source-enum',a['sourceTileEnum']==enums[a['sourceTileId']])
   rebuilt=Image.new('RGBA',(512,512))
   for l in a['layers']:rebuilt.alpha_composite(Image.open(R/by[l['artId']]['image']).convert('RGBA'),tuple(l['offsetPx']))
   check(a['id']+'.exact-layer-reassembly',rebuilt.tobytes()==im.tobytes())
   named=[x for x in a['sourceTileEnum'].split('FENCE_',1)[-1].split('_')if x in ['NW','NE','SW','SE']]if'FENCE_'in a['sourceTileEnum']else[]
   actual=[l['artId'].rsplit('-',1)[-1].upper()for l in a['layers']if'fence'in l['layer']]
   check(a['id']+'.all-named-fence-edges',set(named).issubset(actual),{'source':named,'actual':actual})
   a['status']='art-checked';a['sourceRequirementIds']=[a['id']]
 for ap in m['sourceLayouts']:
  pp=R/ap['preview']['file'];check(ap['id']+'.preview',pp.is_file()and sha(pp)==ap['preview']['sha256'])
  im=Image.open(pp);check(ap['id']+'.preview-size',im.size==(ap['preview']['width'],ap['preview']['height']))
  xy=[(t['x'],t['y'])for t in ap['tiles']];check(ap['id']+'.unique-source-cells',len(set(xy))==len(xy))
  w,h=ap['footprintTiles'];check(ap['id']+'.cells-inside-footprint',all(0<=x<w and 0<=y<h for x,y in xy))
  if ap['id']!='airport-oilrig':
   check(ap['id']+'.full-footprint-cell-count',len(xy)==w*h)
   for t in ap['tiles']:
    e=by[t['artId']];check(ap['id']+'.cell-'+str(t['x'])+'-'+str(t['y']),e['sourceTileEnum']==t['sourceTileEnum']and e['sourceTileId']==t['sourceTileId'])
    e['sourceRequirementIds'].append(ap['id'])
  else:
   by['airport-offshore-helipad']['sourceRequirementIds']=['airport-oilrig']
  ap['artReviewStatus']='locally-checked; user acceptance pending'
 check('10-source-airports',len(m['sourceLayouts'])==10)
 check('265-original-layout-placements',sum(len(a['tiles'])for a in m['sourceLayouts'])==265)
 for anim in m['animations']:
  ims=[Image.open(R/f).convert('RGBA')for f in anim['frames']];n=len(ims);general='animation-airport-radar'if'radar'in anim['id']else'animation-airport-flag'
  check(anim['id']+'.same-canvas',all(i.size==(512,512)for i in ims))
  check(anim['id']+'.durations',len(anim['durationsMs'])==n and all(t>0 for t in anim['durationsMs']))
  check(anim['id']+'.visible-motion',len({hashlib.sha256(i.tobytes()).hexdigest()for i in ims})>=4)
  # Only dish/cloth above this row may move. Supports and ground remain byte-identical.
  # Wind cloth ownership reaches row262 and can move4px; support starts below its full swept bounds.
  support_y=365 if'radar'in anim['id']else 280
  check(anim['id']+'.fixed-support',len({hashlib.sha256(i.crop((0,support_y,512,512)).tobytes()).hexdigest()for i in ims})==1)
  first_diff=ImageChops.difference(ims[0],ims[1]);last_diff=ImageChops.difference(ims[0],ims[-1])
  check(anim['id']+'.loop-transition',first_diff.getbbox()is not None and last_diff.getbbox()is not None)
  anim['status']='art-motion-checked';anim['sourceRequirementIds']=[general]
  for f in anim['frames']:
   a=next(x for x in assets if x['image']==f);a['sourceRequirementIds']=sorted(set(a.get('sourceRequirementIds',[])+[general]));a['status']='art-checked'
  m['coverageMappings'].append({'requirementId':general,'artIds':[next(x['id']for x in assets if x['image']==f)for f in anim['frames']],'files':anim['frames'],'animationId':anim['id'],'status':'locally-art-motion-checked','method':anim['method'],'nativeGeneratedFrameClaim':False})
 for a in assets:
  a['sourceRequirementIds']=sorted(set(a.get('sourceRequirementIds',[])));a['status']='art-checked'
  savej(Path(str(R/a['image'])+'.derivation.json'),a)
 for p in PRE.glob('*.jpg'):
  sources=[a for a in assets if a['category']=='airport-tile']if p.stem.startswith('tiles-')else m['sourceLayouts']if p.stem=='all-layouts'else [a for a in assets if a['category']=='airport-animation']
  evidence=[]
  for a in sources:
   item=a['preview']if'preview'in a else a;evidence.append({'file':item.get('file',item.get('image')),'sha256':item['sha256']})
  savej(Path(str(p)+'.derivation.json'),{'file':rel(p),'sha256':sha(p),'width':Image.open(p).width,'height':Image.open(p).height,'operation':'actual downsampled art contact sheet with text labels on light/dark mattes; no new model generation','derivedFrom':evidence,'nativeModelGeneration':False})
 m['coverageMappings']=[v for i,v in enumerate(m['coverageMappings'])if v['requirementId']not in {x['requirementId']for x in m['coverageMappings'][:i]}]
 m['qa']=[{'id':f['check'],'level':'FAIL','details':f['details']}for f in fails]
 m['status']='local-art-checked-user-acceptance-pending'if not fails else'needs-repair'
 m['counts'].update({'formalSpritePNGs':len(assets),'packagedPNGs':len(assets)+2,'fullLayoutPreviewPNGs':10,'coverageRequirements':len(m['coverageMappings'])})
 m['sourceEvidence']=[{'file':rel(R/'reference/OpenTTD/src/table'/f),'sha256':sha(R/'reference/OpenTTD/src/table'/f)}for f in ['airporttile_ids.h','airport_defaults.h','station_land.h']]
 m['acceptance']={'userAccepted':False,'unityValidated':False,'localArtCheckPassed':not fails,'actualVisualReviewPages':['all-layouts.jpg','tiles-1.jpg','tiles-2.jpg','tiles-3.jpg','tiles-4.jpg','airport-radar-scan-phases.jpg','airport-windsock-flutter-phases.jpg'],'knownRepresentationAssumptions':['Same terminal/admin architecture reused for multiple compatible source tiles; not distinct original pixel structures.','Taxi paths use a normalized equivalent centre graph. Exact vehicle motion alignment remains a Unity integration check.','Radar is an elevation scan sweep from a painted dish, not a native360 yaw movie. Wind cloth is a premultiplied warp; all20frames are deterministic derivatives.','Oilrig airport shares its industry body;3x3water in preview is surrounding context, not airport logical footprint.']}
 savej(OUT/'manifest.json',m)
 report={'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked':len(checks),'passed':sum(x['passed']for x in checks),'failures':fails,'allChecks':checks,'counts':m['counts'],'preview':'previews/world/airports/index.html','manifest':rel(OUT/'manifest.json'),'sourceRequirements':len(m['coverageMappings']),'sourceAirportTypes':10,'sourceTileIds':74,'sourceLayoutPlacements':265,'unityValidated':False,'userAccepted':False}
 savej(R/'records/world-production/airport-validation.json',report)
 print(json.dumps({'checked':len(checks),'failures':fails,'counts':m['counts']},ensure_ascii=False))
if __name__=='__main__':main()

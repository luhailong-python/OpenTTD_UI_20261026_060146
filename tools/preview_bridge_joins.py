"""Inspect actual native-pixel bridge assemblies, including both axes/end ramps.
--working previews current geometry without rebuilding or altering runtime assets.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import argparse,json,hashlib,datetime,ast,types,math
import numpy as np
R=Path(__file__).resolve().parents[1]
# Load only the actual geometry declarations/functions, without importing the
# production extractor (whose SciPy component scan is irrelevant to a preview).
_tree=ast.parse((R/'tools/build_transport_runtime.py').read_text(encoding='utf-8'))
_names={'_project_deck_quad','project_module','_bridge_interp','_bridge_sample'}
_nodes=[n for n in _tree.body if isinstance(n,ast.FunctionDef)and n.name in _names or isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in ['PORTS','LANDMARKS','POST_LANDMARKS','_BRIDGE_GEOMETRY_CACHE']for t in n.targets)]
_env={'np':np,'math':math,'Image':Image,'ImageOps':ImageOps,'ImageDraw':ImageDraw}
exec(compile(ast.Module(body=_nodes,type_ignores=[]),'actual bridge geometry','exec'),_env)
build=types.SimpleNamespace(LANDMARKS=_env['LANDMARKS'],project_module=_env['project_module'],img=lambda aid:Image.open(R/f'assets/world/infrastructure/transport/{aid}.png').convert('RGBA'))
FAMILIES={'wood':'wood','concrete':'concrete','archgirder':'arch','suspension':'suspension','cantilever':'cantilever','girder':'truss','tubular':'tubular'}

def shade(im,row):
 if row['neededVariants']['paletteOrMaterialVariant']:
  import numpy as np
  a=np.asarray(im).copy();grade=[.96,1,.96]if row['neededVariants']['sourceBridgeId']%2 else[1,.97,.92]
  a[:,:,:3]=np.uint8(np.clip(a[:,:,:3].astype(float)*grade,0,255));return Image.fromarray(a)
 return im

def panel(parts,axis):
 canvas=Image.new('RGBA',(900,640));cursor=[0,0]
 # Actual logical mouth-to-mouth deltas, including one-level height changes.
 for n,(sprite,meta) in enumerate(parts):
  ox=100+cursor[0]if axis=='X'else 420+cursor[0]
  canvas.alpha_composite(sprite,(round(ox),round(90+cursor[1])))
  dx,dy=meta['advancePx'];cursor[0]+=dx;cursor[1]+=dy
 box=canvas.getbbox();box=(max(0,box[0]-12),max(0,box[1]-12),min(canvas.width,box[2]+12),min(canvas.height,box[3]+12))
 crop=canvas.crop(box);background=Image.new('RGBA',crop.size,'#ebe6d8');background.alpha_composite(crop)
 return background

def inspect_joins(parts,axis):
 """Check geometric collars and actual composed Alpha, before preview scaling."""
 canvas=Image.new('RGBA',(900,640));cursor=np.array([0.,0.]);placed=[]
 for sprite,meta in parts:
  origin=np.array([100. if axis=='X'else 420.,90.])+cursor
  canvas.alpha_composite(sprite,tuple(np.round(origin).astype(int)))
  placed.append((origin,meta));cursor+=np.asarray(meta['advancePx'])
 alpha=np.asarray(canvas)[:,:,3];joins=[]
 for (origin,meta),(next_origin,next_meta) in zip(placed,placed[1:]):
  p=np.asarray(meta['targetDeckMouths'][1])+origin
  q=np.asarray(next_meta['targetDeckMouths'][0])+next_origin
  half=meta['deckCrossSectionHalfX'];sign=1 if axis=='X'else-1
  samples=[]
  # Centre80% excludes the terminal decorative column/outer antialias edge.
  # Sample the painted deck contact and the first2px of its slab beneath it.
  for t in np.linspace(-.8,.8,41):
   for dy in [0,1,2]:
    xy=p+np.array([sign*half*t,-half*.5*t+dy]);x,y=np.round(xy).astype(int)
    samples.append(int(alpha[y,x]))
  joins.append({'mouthCentrePx':p.tolist(),'nextMouthCentrePx':q.tolist(),
   'maximumGeometricErrorPx':float(np.max(np.abs(p-q))),
   'paintedDeckAlphaSamples':len(samples),'transparentDeckSamples':sum(a==0 for a in samples),
   'minimumPaintedDeckAlpha':min(samples)})
 return {'joins':joins,'exactPortAlignment':all(j['maximumGeometricErrorPx']<1e-9 for j in joins),
  'noTransparentDeckGap':all(j['transparentDeckSamples']==0 for j in joins)}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--working',action='store_true');args=parser.parse_args()
 source=json.loads((R/'docs/WORLD_ASSET_COVERAGE.json').read_text(encoding='utf-8'))
 rows=[q for q in source['items']if q['category']=='bridge']
 runtime=json.loads((R/'assets/world/infrastructure/transport-runtime/manifest.json').read_text(encoding='utf-8'))
 lookup={a['id']:a for a in runtime['assets']};font=ImageFont.truetype(str(R/'assets/fonts/NotoSansSC-Variable.ttf'),21)
 prefix='bridge-joins-working'if args.working else'bridge-joins'
 overview=Image.new('RGB',(1880,len(rows)*540),'#ebe6d8');od=ImageDraw.Draw(overview);evidence=[]
 for n,row in enumerate(rows):
  fam=FAMILIES[row['neededVariants']['geometryFamily']];page=Image.new('RGB',(1880,1400),'#ebe6d8');d=ImageDraw.Draw(page)
  d.text((22,12),row['id']+' / '+fam+' / source-pixel geometry; not new native painting',font=font,fill='#204337')
  measurements=[]
  for col,axis in enumerate(['X','Y']):
   sprites={}
   for rise,key in [(0,'middle'),(32,'north'),(-32,'south')]:
    if args.working:
     native=build.img('bridge-'+fam+'-span');im,meta=build.project_module(native,build.LANDMARKS[fam],axis,rise);im=shade(im,row)
    else:
     ident=row['id']+'-'+axis+'-road'+(''if rise==0 else'-'+key);a=lookup[ident];im=Image.open(R/a['image']).convert('RGBA');meta=a['projection']
    sprites[key]=(im,meta)
   assemblies=[]
   for rr,sequence in enumerate([['middle']*3,['north','middle','south']]):
    pieces=[sprites[k]for k in sequence]
    assemblies.append({'roles':sequence,**inspect_joins(pieces,axis)})
    im=panel(pieces,axis)
    # Crop only unused preview margins, then enlarge the DISPLAY with nearest
    # sampling to expose individual pixels. These are QA views, not new art.
    im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    im.thumbnail((910,610),Image.Resampling.NEAREST)
    x=col*940+12;y=65+rr*660;page.paste(im.convert('RGB'),(x,y+32))
    d.text((x,y),axis+' / '+('3 flat spans'if rr==0 else'up32 + flat + down32'),font=font,fill='#204337')
    if rr==0:
     sm=im.copy();sm.thumbnail((910,480),Image.Resampling.NEAREST);overview.paste(sm.convert('RGB'),(col*940+12,n*540+45))
   measurements.append({'axis':axis,'flat':sprites['middle'][1],'up':sprites['north'][1],'down':sprites['south'][1],'assemblies':assemblies})
  od.text((15,n*540+10),row['id'],font=font,fill='#204337')
  path=R/f'previews/world/{prefix}-page{n+1}.jpg';page.save(path,quality=96)
  evidence.append({'sourceId':row['id'],'nativeFamily':fam,'preview':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'measurements':measurements})
 overview.save(R/f'previews/world/{prefix}.jpg',quality=95)
 assemblies=[a for case in evidence for m in case['measurements']for a in m['assemblies']]
 report={'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'working geometry preview; runtime PNG not rebuilt'if args.working else'actual formal runtime PNG assembly','cases':evidence,
  'mechanicalJoinQA':{'assemblies':len(assemblies),'interfaces':sum(len(a['joins'])for a in assemblies),'exactPortAlignment':all(a['exactPortAlignment']for a in assemblies),'noTransparentDeckGap':all(a['noTransparentDeckGap']for a in assemblies),'alphaRule':'Actual composed Alpha at123 native-size samples per interior80% cross-section; no display enlargement participates in this check.','visualAcceptance':'Separate manual inspection is required; geometric/Alpha checks do not establish aesthetic quality.'},
  'geometryScriptSha256':hashlib.sha256((R/'tools/build_transport_runtime.py').read_bytes()).hexdigest(),
  'runtimeManifestSha256':None if args.working else hashlib.sha256((R/'assets/world/infrastructure/transport-runtime/manifest.json').read_bytes()).hexdigest(),
  'rule':'13 source BridgeSpecs use7 actual painted structural families with declared material variants and7 role bindings, not13 new native paintings.','unityValidated':False}
 (R/f'records/world-production/{prefix}-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'mode':report['mode'],'cases':len(rows),'overview':f'previews/world/{prefix}.jpg'}))
if __name__=='__main__':main()

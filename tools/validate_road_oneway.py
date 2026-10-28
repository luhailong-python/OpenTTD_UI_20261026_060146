"""Independent source-table, artwork provenance and road-overlay placement checks."""
from pathlib import Path
from PIL import Image
import json,re,collections,numpy as np
import world_pack as wp
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 mp=R/'assets/world/overlays/road-oneway/manifest.json';bp=R/'docs/ROAD_ONEWAY_BINDINGS.json';m=load(mp);q=load(bp);aa={a['sourceSpriteOffset']:a for a in m['assets']};checks=[]
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 src=(R/'reference/OpenTTD/src/road_cmd.cpp').read_text(encoding='utf8');sprites=(R/'reference/OpenTTD/src/table/sprites.h').read_text(encoding='utf8');mul=[int(v.strip(),0)for v in re.search(r'drd_to_multiplier\[\]\s*=\s*\{([^}]+)',src)[1].split(',')if v.strip()];test('source-drd-multipliers',mul==[0x101,0x100,1,0]);test('source18slots',int(re.search(r'ONEWAY_SPRITE_COUNT\s*=\s*(\d+)',sprites)[1])==len(aa)==18 and set(aa)==set(range(18)));test('source-north-south-offsets',int(re.search(r'ONEWAY_SLOPE_N_OFFSET\s*=\s*(\d+)',sprites)[1])==6 and int(re.search(r'ONEWAY_SLOPE_S_OFFSET\s*=\s*(\d+)',sprites)[1])==12)
 sourceTable=src.split('_invalid_tileh_slopes_road = {{',1)[1].split('};',1)[0];table=[];roadbits={'NW':1,'SW':2,'SE':4,'NE':8};constants={'ROAD_X':10,'ROAD_Y':5,'ROAD_ALL':15}
 for line in sourceTable.splitlines():
  if '// SLOPE_'not in line:continue
  line=line.split('//',1)[0];value=0
  for name in re.findall(r'RoadBit::(NW|SW|SE|NE)',line):value|=roadbits[name]
  for name in re.findall(r'\bROAD_(?:X|Y|ALL)\b',line):value|=constants[name]
  table.append(value)
 test('actual-foundation-source30entries',len(table)==30)
 test('bound-manifest-current',q['manifestSHA256']==wp.sha(mp));test('bindings18source-slots',len(q['bindings'])==18 and{b['sourceSpriteOffset']for b in q['bindings']}==set(aa));test('114original-slope-axis-drd-cases',len(m['sourceCaseBindings'])==114 and len({(c['sourceTerrainSlopeCode'],c['axis'],c['drd'])for c in m['sourceCaseBindings']})==114)
 for dep in m['sourceFiles']:test('current-source-sha',wp.sha(R/dep['file'])==dep['sha256'],file=dep['file'])
 vr=load(R/'records/road-oneway-visual-review.json')if(R/'records/road-oneway-visual-review.json').is_file()else{};reviewed={a['file']:a['sha256']for a in vr.get('reviewedAssets',[])}
 sourceSeen=set()
 for slot,a in aa.items():
  p=R/a['image'];im=Image.open(p);meta=load(Path(str(p)+'.derivation.json'));b=next(b for b in q['bindings']if b['sourceSpriteOffset']==slot);mask=np.array(im.getchannel('A'))>20;ys,xs=np.where(mask);expectedoffset=(0 if a['effectiveSlopeCode']==0 else 6 if a['effectiveSlopeCode']in[12,9]else 12)+(0 if a['axis']=='X'else 3)+a['disallowedRoadDirectionBits']-1
  test(a['id']+'.source-offset-formula',slot==expectedoffset and a['sourceSpriteId']==6105+slot);test(a['id']+'.hash',a['sha256']==meta['sha256']==b['sha256']==wp.sha(p));test(a['id']+'.fixedRGBAcanvas',im.mode=='RGBA'and im.size==(256,192));test(a['id']+'.safe-Alpha',len(xs)>0 and mask.min()==0 and xs.min()>0 and ys.min()>0 and xs.max()<255 and ys.max()<191);test(a['id']+'.tile-anchor',a['anchorPx']==[128,128]and a['pivotUnity']==[.5,1/3]);z=0 if a['effectiveSlopeCode']==0 else 4;test(a['id']+'.source-centre-Z',a['sourcePartialPixelZ']==z and a['sourceCentrePixelInFullTileCanvas']==[128,128-z*4])
  bits=(1 if a['axis']=='X'else 2)*mul[a['disallowedRoadDirectionBits']];td={0:None,1:'X_NE',2:'Y_SE',256:'X_SW',512:'Y_NW'}[bits];test(a['id']+'.actual-track-direction',a['allowedTrackdir']==td);test(a['id']+'.current-visual-evidence',reviewed.get(a['image'])==a['sha256']and b.get('localArtReviewed'));test(a['id']+'.honest-native-derivative',not a['nativeModelGeneration']and not a['nativeUpscale']and a['actualModel']is None)
  for dep in a['derivedFrom']:
   key=(dep['file'],dep['sha256'])
   if key in sourceSeen:continue
   sourceSeen.add(key);test('current-art-source-sha',(R/dep['file']).is_file()and wp.sha(R/dep['file'])==dep['sha256'],file=dep['file'])
  for context in ['rural','town-pavement','snow','desert']:
   name={0:'flat',3:'sw',6:'se',9:'nw',12:'ne'}[a['effectiveSlopeCode']];rf=f'assets/world/infrastructure/road-variants/road-{context}-mask-{a["connectionMask"]:02d}-slope-{name}.png';gr=np.array(Image.open(R/rf).getchannel('A'));test(a['id']+'.inside-'+context+'-road-tile',np.all(gr[mask]>20))
 foundations=load(R/'assets/world/infrastructure/foundations/manifest.json')['coverageMappings'][0]['caseBindings'];fby={(c['slopeCode'],c['mode']):c for c in foundations}
 for c in m['sourceCaseBindings']:
  code=c['sourceTerrainSlopeCode'];axis=c['axis'];h=wp.corner_heights(code);high=max(h,key=h.get);reduced=wp.CORNERS[high]if code&16 else code;bits=10 if axis=='X'else 5
  expected='None'if code==0 else'Leveled'if(table[reduced]&bits)==0 else'None'if reduced not in[1,2,4,8]and(table[15+reduced]&bits)==0 else'Inclined'+axis;test(f'foundation-{code}-{axis}-{c["drd"]}',c['foundationMode']==expected)
  if expected!='None':
   heights={k:v+c['baseHeightIncrementTiles']for k,v in wp.corner_heights(c['postFoundationSlopeCode']).items()};target=fby[(code,expected)]['targetPatches'][0]['heights'];test(f'foundation-cap-{code}-{axis}-{c["drd"]}',all(abs(heights[k]-target[k])<1e-6 for k in heights))
  slot=(0 if c['postFoundationSlopeCode']==0 else 6 if c['postFoundationSlopeCode']in[12,9]else 12)+(0 if axis=='X'else 3)+c['drd']-1;test(f'case-mapping-{code}-{axis}-{c["drd"]}',c['sourceSpriteOffset']==slot and c['overlaySHA256']==aa[slot]['sha256']and(R/c['targetRoadFile']).is_file())
 fail=[x for x in checks if not x['passed']];q['complete']=not fail;q['failures']=fail;wp.writej(bp,q);report={'createdAt':wp.now(),'scope':'18source Sprite slots,source road trackdir multipliers,source foundation tables,114terrain-to-effective-slope cases,current native source/PNG SHA,Alpha/tile-centre-Z,4real road contexts and actual page review hashes; no Unity/user approval','sourceRequirements':18,'formalPNGCount':18,'terrainAxisDirectionCases':114,'passed':sum(x['passed']for x in checks),'failed':len(fail),'failures':fail,'complete':not fail,'manifest':wp.rel(mp),'manifestSHA256':wp.sha(mp),'bindings':wp.rel(bp),'bindingsSHA256':wp.sha(bp),'visualRecord':'records/road-oneway-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/road-oneway-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

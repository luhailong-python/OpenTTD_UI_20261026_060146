"""Read-only source/image verification; refresh only airport UI status records."""
from pathlib import Path
from PIL import Image
import json,re
import world_pack as wp
from bind_airport_ui_previews import numeric
R=wp.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 bp=R/'docs/AIRPORT_UI_BINDINGS.json';q=load(bp);checks=[];st=(R/'reference/OpenTTD/src/table/sprites.h').read_text(encoding='utf8');at=(R/'reference/OpenTTD/src/table/airport_defaults.h').read_text(encoding='utf8');expected=dict(re.findall(r'AS(?:_ND)?\(\s*(\w+)\s*,[^\n]+?\b(SPR_AIRPORT_PREVIEW_\w+)\)',at));bound={r['airportKey']:r for r in q['bindings']};vrp=R/'records/airport-ui-visual-review.json';vr=load(vrp)if vrp.is_file()else{};reviewed={r['file']:r['sha256']for r in vr.get('reviewedAssets',[])}
 def test(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
 test('actual-source9AirportSpec-preview-links',len(expected)==9 and set(expected)==set(bound)and all(bound[k]['id']==v for k,v in expected.items()));test('no-oilrig-build-preview','oilrig'not in bound and re.search(r'AS_GENERIC\(&_airportfta_oilrig.*STR_NULL,\s*0,\s*false\)',at));test('no-new-formal-PNG',q['newFormalPNGCount']==0 and q['reusedExistingPNGCount']==9)
 for src in q['sourceFiles']:test('current-source-sha',wp.sha(R/src['file'])==src['sha256'],file=src['file'])
 ap=q['existingAirportManifest'];test('existing-airport-manifest-unchanged',wp.sha(R/ap['file'])==ap['sha256']);airport=load(R/ap['file']);layouts={x['id'].removeprefix('airport-'):x for x in airport['sourceLayouts']}
 for k,r in bound.items():
  p=R/r['file'];im=Image.open(p);d=load(R/r['sourceDerivationRecord']);test(r['id']+'.source-value',r['sourceSpriteId']==numeric(st,r['id']));test(r['id']+'.current-existing-PNG-SHA',wp.sha(p)==r['sha256']==d['sha256']);test(r['id']+'.same-original-canvas',list(im.size)==[r['width'],r['height']]);test(r['id']+'.trueRGBA-Alpha',im.mode=='RGBA'and im.getchannel('A').getextrema()[0]==0 and im.getchannel('A').getbbox()is not None);test(r['id']+'.derivation-record-current',wp.sha(R/r['sourceDerivationRecord'])==r['sourceDerivationRecordSHA256']);test(r['id']+'.same-source-footprint',r['footprintTiles']==layouts[k]['footprintTiles']and r['logicalTileCount']==len(layouts[k]['tiles']));test(r['id']+'.buildable',layouts[k]['buildable']);test(r['id']+'.no-copy-or-repaint',r['newFormalPNG']is False and r['nativeModelGeneration']is False and r['nativeUpscale']is False);test(r['id']+'.actual-current-visual-review',r['localArtReviewed']and reviewed.get(r['file'])==r['sha256'])
  for dep in d['derivedFrom']:test('existing-layout-dependency-current',(R/dep['file']).is_file()and wp.sha(R/dep['file'])==dep['sha256'],file=dep['file'])
 failures=[x for x in checks if not x['passed']];q['complete']=not failures;q['failures']=failures;wp.writej(bp,q);report={'createdAt':wp.now(),'scope':'nine actual source airport preview symbols/AirportSpec links,existing unmodified PNG/manifest/dependency hashes,source footprints/buildability,RGBA/canvas,actual current visual-review evidence; no new formal PNGs','sourceRequirements':9,'reusedPNGCount':9,'newFormalPNGCount':0,'passed':sum(x['passed']for x in checks),'failed':len(failures),'failures':failures,'complete':not failures,'bindings':'docs/AIRPORT_UI_BINDINGS.json','bindingsSHA256':wp.sha(bp),'visualRecord':'records/airport-ui-visual-review.json','userArtAcceptance':'pending','unityValidated':False};wp.writej(R/'records/airport-ui-validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def info(rel):
 p=ROOT/rel;im=Image.open(p)
 return {'file':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':im.width,'height':im.height}
catalog=json.loads((ROOT/'docs/screen-catalog.json').read_text(encoding='utf-8'))
statepaths=[]
for screen in catalog:
 for state in screen.get('states',[]):statepaths.append(f"previews/states/{screen['id']}--{state['id']}.png")
contacts=[f'previews/states-contact-{i:02d}.jpg' for i in range(9,13)]+['previews/overview.jpg']
full=['previews/states/106-newgrf-presets--overwrite.png','previews/states/128-editor-terrain--clear-confirm.png',
      'previews/states/118-advanced-options--server-locked.png','previews/states/149-script-league--no-script-table.png','designs/11-rail-build.png']
report={'reviewer':'art_reference_audit','reviewedOn':'2026-10-26','timeZone':'America/New_York',
 'scope':'Actual visual review of states contact sheets 09-12, whole-suite overview and selected full PNGs. Review only; no image or renderer edits.',
 'reviewedContactSheets':[info(x) for x in contacts],'coveredStateImages':statepaths[160:240],
 'fullImagesActuallyViewed':[info(x) for x in full],
 'positiveChecks':['Jade/ivory/gold family is consistent across the reviewed set.',
                   'State title, icon, message and action have clear hierarchy and legible Chinese at full size.',
                   'Selected full-size state images show complete cloud corners, tassels and clean button edges.',
                   'No missing icon or text overflow observed in contact sheets 09-12.',
                   'Overview combines main menu, HUD, construction, vehicle purchase, timetable, finance, map, network lobby and editor in a consistent skin.'],
 'findings':[
   {'id':'C-01','priority':'P2','file':'designs/11-rail-build.png','status':'needs_revision',
    'title':'Tool tile labels overlap the bottom gold frame',
    'evidence':'At full size the first row labels 轨道/道岔/信号 around y450 and second row 车站/车库/桥梁 around y583 sit across the bottom edge of the tile.',
    'requestedChange':'Move tile labels fully inside the paper tile above its bottom edge, or below the tile into a reserved gap. Check other screens using the same tile renderer.'},
   {'id':'C-02','priority':'P2','files':['previews/states/106-newgrf-presets--overwrite.png','previews/states/128-editor-terrain--clear-confirm.png'],
    'status':'needs_revision','title':'Destructive confirmation state lacks visible cancel action',
    'evidence':'The standalone state previews show only 确认覆盖 / 确认重置 and have no cancel/back/close control.',
    'requestedChange':'Add a secondary 取消 action to confirmation-state previews, preserving the primary action and clear hierarchy. Check shared confirmation states.'}
 ],'result':'revision_required_for_two_shared_layout_cases','unityValidationExecuted':False,'imagesChangedByReviewer':False}
(ROOT/'records/visual-review-part-c.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('visual-review-part-c.json saved',len(report['coveredStateImages']),'state cards covered')

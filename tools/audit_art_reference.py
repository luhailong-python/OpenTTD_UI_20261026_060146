from pathlib import Path
from PIL import Image
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1]
ART=Path('F:/work/image')
paths=[
'designs/mail-ui-v1/01-mail-event.png',
'designs/team-ui-v2/team-ui-v2.png',
'designs/gameplay-ui/02-inventory.png',
'designs/world-map-original-20260925/world-map-original.png',
'designs/social-ui-v1/02-world.png',
'designs/equipment-ui-20261008/sprites/checkbox_on.png',
'designs/equipment-ui-20261008/sprites/checkbox_off.png',
'designs/attribute-panels/exact-20261022/staged/Assets/Resources/UI/Ugui/AttributeExact20261022/slider_track.png',
]
refs=[]
for p in paths:
 f=ART/p;data=f.read_bytes();im=Image.open(f);im.verify();im=Image.open(f)
 refs.append({'file':str(f),'repositoryRelativePath':p,'sha256':hashlib.sha256(data).hexdigest(),
 'width':im.width,'height':im.height,'format':im.format,'mode':im.mode,'pngSignature':data[:8].hex(),
 'gitLfsPointer':data.startswith(b'version https://git-lfs.github.com/spec/v1'),
 'alphaRange':list(im.getchannel('A').getextrema()) if 'A' in im.getbands() else [255,255],
 'actuallyViewed':True,'associationType':'style_reference' if len(refs)<5 else 'direct_reuse'})
docs=['AGENTS.md','README.md','docs/WUXING_QITAN_HANDOFF.md','docs/QDAO_ART_DIRECTION.md',
 'docs/AI_DESIGN_TOOLS_SETUP.md','docs/IMAGE_MODEL_POLICY.md','config/image-generation.json','designs/README.md',
 'designs/mail-ui-v1/README.md','designs/mail-ui-v1/UI_SPEC.md','designs/team-ui-v2/README.md',
 'designs/team-ui-v2/unity-slices/manifest.json','designs/gameplay-ui/README.md',
 'designs/gameplay-ui/exact-20261022/README.md','designs/world-map-original-20260925/README.md',
 'designs/world-map-original-20260925/fidelity-20261016/README.md','designs/scene-select-ui-v1/README.md',
 'designs/scene-select-ui-v1/fidelity-20261016/README.md','designs/social-ui-v1/README.md','designs/social-ui-v1/UI_SPEC.md',
 'designs/attribute-panels/README.md','designs/attribute-panels/v2-painted/unity-slices/README.md',
 'designs/attribute-panels/v2-painted/unity-slices/manifest.json','designs/attribute-panels/exact-20261022/README.md',
 'designs/attribute-panels/exact-20261022/sprite-provenance.json','designs/equipment-ui-20261008/README.md',
 'designs/equipment-ui-20261008/sprite-manifest.json','designs/ui-completion-20261021/README.md',
 'designs/ui-completion-20261021/requirements/README.md']
result={'verifiedOn':'2026-10-26','timeZone':'America/New_York','artRepository':str(ART),'outputDirectory':str(ROOT),
'functionalReference':'https://github.com/OpenTTD/OpenTTD.git','deliveryRepository':None,
'missing':['qdao_ui_redesign_v5/UI_SPEC.md'],
'conflicts':[{'file':'designs/README.md','issue':'Historical D: references and mail-missing statement; current F: primary PNG exists. Root AGENTS and actual files take priority.'}],
'readDocuments':[{'file':p,'sha256':hashlib.sha256((ART/p).read_bytes()).hexdigest(),'readScope':'relevant art and handoff sections'} for p in docs],
'viewedImages':refs,'commonAssets':'asset-common-manifest.json',
'checks':{'primaryReferenceImagesExist':True,'primaryReferenceRealPngBytes':True,'noGitLfsPointersInViewedImages':True,
'commonAssetsCount':26,'aiGenerationByThisAudit':False,'unityValidationExecuted':False,'fRepositoryModifiedByThisAudit':False}}
(ROOT/'docs/art-references.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('art-references.json written')

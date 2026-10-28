"""Export a compact local import index from current authoritative manifests."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from final_art_audit import Audit,DEFAULT_ROOT

def main():
 a=Audit(DEFAULT_ROOT);a.collect();rows=[]
 for file,candidates in sorted(a.assets.items()):
  q,origin=candidates[0];canvas=q.get('canvas',q.get('nativeSize'))
  if q.get('width')and q.get('height'):canvas=[q['width'],q['height']]
  anchor=q.get('anchorPx');pivot=q.get('pivotUnity',q.get('pivot'))
  if anchor is None and canvas and pivot:anchor=[pivot[0]*canvas[0],(1-pivot[1])*canvas[1]]
  rows.append({'id':q.get('id',Path(file).stem),'file':file,'sha256':q.get('sha256')or a.sha(a.file(file)),'canvasPx':canvas,'anchorFromTopLeftPx':anchor,'pivotUnity':pivot,'borderLeftBottomRightTop':q.get('border',[0,0,0,0]),'sourceManifest':origin,'additionalManifestReferences':sorted({o for _,o in candidates if o!=origin}),'sourceRequirementIds':sorted({value for item,_ in candidates for value in item.get('sourceRequirementIds',[])}),'category':q.get('category','ui'),'state':q.get('state'),'direction':q.get('direction'),'nativeModelGeneration':False,'operation':q.get('operation','See source manifest and current derivation sidecar'),'userArtAccepted':False,'unityValidated':False})
 snapshots=[{'file':a.rel(p),'sha256':a.sha(p)}for p in a.pack_paths+a.portrait_pack_paths+a.supplemental_pack_paths]
 result={'schema':'cloud-route.compact-art-import-index.v1','createdAt':datetime.now(timezone.utc).isoformat(),'formalPNGCount':len(rows),'scope':'Compact file/import metadata only; full state/source composition contracts remain in the referenced manifests. Includes formal mask/data PNGs; PNG counts are not native painting counts. Superseded non-authoritative shoreline references excluded.','assetManifests':snapshots,'generationEvidenceIndex':'records/full-game-art-audit.json','worldSourceCoverage':'docs/WORLD_DELIVERY_COVERAGE.json','sourceUIFeatures':'docs/UI_MASTER_MANIFEST.json','userArtAccepted':False,'unityValidated':False,'assets':rows}
 out=a.root/'docs/ART_RESOURCE_INDEX.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'file':a.rel(out),'formalPNGs':len(rows),'sourceManifests':len(snapshots)},ensure_ascii=False))

if __name__=='__main__':main()

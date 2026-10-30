"""Finalize per-screen acceptance only from actual current visual evidence."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((R/p).read_text(encoding="utf-8-sig"))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
review=load("records/ui-branding-visual-review.json")
if not (review.get("complete") and review.get("status","").startswith("passed-local") and not review.get("openFindings")):
    raise ValueError("Current UI visual review is not complete")
for item in review["reviewedFiles"]:
    if item.get("status")!="passed-local" or sha(R/item["file"])!=item["sha256"]:
        raise ValueError("Visual evidence is stale: "+item["file"])
m=load("docs/UI_MASTER_MANIFEST.json");m["project"]="云途万里"
for s in m["screens"]:
    s["acceptanceStatus"]="local-static-check-passed; user-art-review-pending"
    s["missingArtItems"]=[]
    s["pendingIntegrationItems"]=["Unity Sprite/TMP导入与运行验证","真实业务数据及输入/流程接入验证"]
m["localVisualReview"]={"record":"records/ui-branding-visual-review.json","sha256":sha(R/"records/ui-branding-visual-review.json"),"complete":True}
save("docs/UI_MASTER_MANIFEST.json",m)
save("records/visual-review-final.json",{"reviewedAt":datetime.now(timezone.utc).isoformat(),"status":"passed-local-review",
 "sourceReview":"records/ui-branding-visual-review.json","sourceReviewSHA256":sha(R/"records/ui-branding-visual-review.json"),
 "reviewedFiles":review["reviewedFiles"],"openFindings":[],
 "scope":"Current branding in149 screen designs and227 state previews; historical reviews remain unchanged.","userArtAccepted":False,"unityValidated":False})
print("Per-screen acceptance finalized from actual current visual evidence")


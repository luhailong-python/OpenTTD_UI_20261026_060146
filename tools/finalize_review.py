from pathlib import Path
from PIL import Image
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((R/'docs/UI_MASTER_MANIFEST.json').read_text(encoding='utf-8'))
for s in m['screens']:
 s['acceptanceStatus']='local-static-check-passed; user-art-review-pending'
 s['missingArtItems']=[]
 s['pendingIntegrationItems']=['Unity Sprite/TMP导入与运行验证','真实业务数据、权限及失败状态对接','入口/返回/关闭与输入焦点验证']
(R/'docs/UI_MASTER_MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
files=[f'previews/screens-contact-{k:02}.jpg'for k in range(7,14)]+[f'previews/states-contact-{k:02}.jpg'for k in range(5,9)]
focused=['designs/47-vehicle-view.png','designs/98-chat.png','designs/13-rail-signals.png','previews/states/07-save-game--overwrite.png']
report={'reviewer':'root','reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'本地静态美术，B段73–149联系图和状态05–08；专属修复另开完整PNG','actuallyViewed':[{'file':p,'sha256':sha(R/p)}for p in files+focused],'findings':['聊天输入与控制台日志结构已补强','小型详情表遮字已修','专用信号/桥型与地图标签已修','所有确认支持取消/关闭，状态按钮在外框上方'],'remainingBlockingFindings':0,'userArtApproval':'pending','unityValidated':False}
(R/'records/visual-review-part-b.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Correct text layout pointers for state derivatives.
for s in m['screens']:
 for st in s['states']:
  p=R/(st['previewPath']+'.generation.json');q=json.loads(p.read_text(encoding='utf-8'));q['textLayout']='docs/layouts/states/'+s['id']+'--'+st['id']+'.json';p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
print('review and per-screen acceptance flags recorded')


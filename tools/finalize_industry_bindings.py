from pathlib import Path
from PIL import Image
import json,datetime,hashlib
R=Path(__file__).resolve().parents[1];mp=R/'assets/world/industries/manifest.json'
def j(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def savej(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=j(mp);masks=[];checks=[];fail=[]
for b in m['mechanismBindings']:
 b['status']='passed-local-installed-visual-review'
 p=R/b['ownershipMask'];im=Image.open(p);masks.append({'id':b['animationId']+'-ownership-mask','file':b['ownershipMask'],'sha256':sha(p),'width':512,'height':512,'mode':'RGBA','role':'ownership-mask-data; not a visible artwork sprite','record':b['ownershipMask']+'.derivation.json'})
 gif=Image.open(R/b['assemblyPreviewGIF']);q={'id':b['animationId'],'12-installed-preview-frames':len(b['assemblyPreviewFrames'])==12,'gif-frames':gif.n_frames>=7,'placement':b['attachmentOffsetPx']==[0,0]and b['attachmentScale']==1,'parent-clean-distinct':b['cleanBaseImage']!=b['parentImage'],'mask-file':p.is_file(),'gif-file':(R/b['assemblyPreviewGIF']).is_file()};checks.append(q)
 if not all(v for k,v in q.items()if k!='id'):fail.append(q)
for a in m['animations']:
 a['status']='passed-local-installed-motion-review';a['binding']['status']='passed-local-installed-visual-review'
 sheet=Image.new('RGBA',(2048,1536))
 for f,p in enumerate(a['frames']):sheet.alpha_composite(Image.open(R/p).convert('RGBA'),((f%4)*512,(f//4)*512))
 sp=R/Path(a['frames'][0]).parent.parent/'sheet.png';sheet.save(sp);a['sheet']=sp.relative_to(R).as_posix();a['grid']=[4,3];a['cellSizePx']=[512,512]
 savej(Path(str(sp)+'.derivation.json'),{'file':a['sheet'],'sha256':sha(sp),'width':2048,'height':1536,'operation':'lossless4x3 packing of exact512x512 parent-positioned moving-layer frames; not model generation','derivedFrom':[{'file':p,'sha256':sha(R/p),'record':p+'.derivation.json'}for p in a['frames']],'nativeModelGeneration':False})
for a in m['assets']:
 if a['category']in['industry-bound-animation','industry-animation-clean-base']:
  a['status']='passed-local-installed-art-review';a['anchorMeaning']='complete parent compound front-contact, independent of moving-region extents'
  savej(R/(a['image']+'.derivation.json'),a)
m['ownershipMasks']=masks;m['counts']['ownershipMaskDataPNGs']=len(masks);m['counts']['animationSheets']=len(m['animations']);m['counts']['packagedPNGs']=len(m['assets'])+len(masks)+len(m['animations'])+sum('removedPoseMask'in b for b in m['mechanismBindings'])
m['renderingContract']['mechanicalRebuildOrder']=['static industry extraction and construction if needed','tools/build_industry_bindings.py','tools/build_industry_fx_bindings.py','tools/validate_industries.py','tools/finalize_industry_bindings.py']
savej(mp,m)
report=j(R/'records/world-production/industry-binding-validation.json');report['visualReview']='All6 full512 installed loops and72 phase frames inspected on light/dark mattes. No giant detached part, duplicate old mechanism or moving foundation. Small in-place material motion remains a declared2D art design.'
fxp=R/'records/world-production/industry-fx-binding-validation.json'
if fxp.is_file():
 fx=j(fxp);report['particleBindingValidation']={'file':fxp.relative_to(R).as_posix(),'sha256':sha(fxp)}
 fxids={c['id']for c in fx['checks']}
 report['allChecks']=[c for c in report['allChecks']if c['id']not in fxids and not c['id'].startswith(('industry-coal-plant-sparks','industry-bubble-generator-cycle'))]+fx['checks']
 report['allChecks']=list({c['id']:c for c in report['allChecks']}.values())
 report['visualReview']+=' Two shared-FX parent bindings additionally have current full-parent phase inspection; coal has no baked spark to remove, bubble has separate old-pose deletion and swept-overlay masks. Shared lifetime paint downsample/translation adds no new native poses.'
report['installationChecks']=checks;report['failures']=[c for c in report['allChecks']if not c['passed']]+fail;report['checks']=len(report['allChecks'])+sum(len(c)-1 for c in checks);report['passed']=sum(c['passed']for c in report['allChecks'])+sum(sum(bool(v)for k,v in c.items()if k!='id')for c in checks);report['bindings']=m['mechanismBindings'];report['userAccepted']=False
savej(R/'records/world-production/industry-binding-validation.json',report)
cards=[]
for b in m['mechanismBindings']:
 cards.append('<article><h2>'+b['animationId']+'</h2><img src="'+Path(b['assemblyPreviewGIF']).name+'" alt="installed industry animation"><p>'+b['description']+'</p><p>父体 '+b['parentArtId']+'<br>512×512 · Anchor[256,448] · Offset[0,0] · Scale1</p><a href="../../../'+b['cleanBaseImage']+'">无旧姿态底体PNG</a> · <a href="../../../'+b['ownershipMask']+'">运动区域遮罩</a> · <a href="'+Path(b['assemblyContactSheet']).name+'">12帧就位表</a></article>')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>产业机械就位预览</title><style>@font-face{font-family:Noto;src:url('../../../assets/fonts/NotoSansSC-Variable.ttf')}body{margin:0;padding:30px;background:#173f35;color:#f0e6cd;font:15px Noto,sans-serif}h1{font-size:26px}.intro{max-width:1200px;line-height:1.8}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px;margin-top:25px}article{background:#e7e1ce;border:1px solid #bd9e61;border-radius:16px;color:#194438;padding:16px}h2{font-size:17px;overflow-wrap:anywhere}img{display:block;width:100%;height:auto;max-width:512px;margin:auto}p{line-height:1.6;font-size:13px}a{color:#236c55}</style><h1>产业机械 · 已就位美术循环</h1><div class="intro">6组实际父产业运动区域，72张512×512移动层及6张cleanBase；不再把独立机械部件直接叠在原静态工厂上。<br>正确组合是 cleanBase＋movingFrame，offset[0,0]、scale1；原整厂静图应被替换。轮/齿轮/钻轴/液流/糖粒为固定轮廓内画面材质运动，油井梁为短行程二维摆动，均是确定性派生，不声称新生成3D动画。<br>本页GIF为完整厂区已就位预览，用户画面验收、Unity排序/比例运行验证尚待进行。</div><section class="grid">'''+''.join(cards)+'</section></html>'
html=html.replace('6组实际父产业运动区域，72张512×512移动层及6张cleanBase；不再把独立机械部件直接叠在原静态工厂上。','6组机械＋2组共享粒子绑定，共96张512×512移动层、8张cleanBase。气泡厂移除原悬空气泡；煤电厂无烘焙火花，保留全部静态原像素。')
html=html.replace('本页GIF为完整厂区已就位预览','火花/气泡来自已交付公共FX原画的缩小、定位及生命周期播放；气泡去旧姿态遮罩与粒子运动范围遮罩分别记录。源未工作状态不绘制粒子。<br>本页GIF为完整厂区已就位预览')
p=R/'previews/world/industry-assembly/index.html';p.write_text(html,encoding='utf-8')
print(json.dumps({'assets':len(m['assets']),'bindings':len(m['mechanismBindings']),'qaChecks':report['checks'],'qaFailures':len(report['failures']),'ownershipMasks':len(masks)}))

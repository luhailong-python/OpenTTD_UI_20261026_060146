"""Freeze the actual eight-page review after it has been performed; does not draw art."""
import json
from pathlib import Path
import world_pack as wp
R=wp.ROOT
def main():
 mp=R/'assets/world/overlays/fence-adapter/manifest.json';m=json.loads(mp.read_text(encoding='utf-8-sig'))
 vr='records/fence-adapter-visual-review.json'
 for a in m['assets']:
  a['status']='locally-checked-user-review-pending';a['actualVisualReview']=vr
  wp.writej(Path(str(R/a['image'])+'.derivation.json'),a)
 m['status']='locally-checked-user-review-pending';m['visualReviewRecord']=vr
 m['previewPlacementContract']={'tileCanvas':[512,384],'tileAnchorPx':[256,224],'groundPaste':'tileAnchor minus actual ground PNG anchorPx;field-stage anchor[128,160],grass-slope anchor[128,128]','farmAssemblyCount':114,'farmEdgeBindingsDrawn':456,'railSourcePositionsDrawn':16,'halfTileWaterCornersDrawn':4,'oldPackagesModified':False}
 wp.writej(mp,m)
 findings={
  'farm-bushes-all19slopes.jpg':'实际农田对齐其(128,160)锚点；19坡四边花篱接地、转角连接，未见悬空、裁切或错误地面空洞。',
  'farm-bushes-gate-all19slopes.jpg':'19坡原生木栏门中段与花篱开口可辨，立柱竖直；四边端点按角Z连接，无程序新画门。',
  'farm-timber-all19slopes.jpg':'19坡木栏立柱保持竖直，普通/陡坡栏段与农田边缘相接，未见断角。',
  'farm-yellow-bloom-all19slopes.jpg':'19坡黄色花瓣变色保留原画叶片/Alpha，四边源offset坡向正确。',
  'farm-red-bloom-all19slopes.jpg':'19坡红花辨识清楚，保留相同栏段结构/Alpha；未见错位和矩形背景。',
  'farm-stone-all19slopes.jpg':'19坡石栏原生柱/石段沿四边连接，高低角和陡坡无明显地面分离。',
  'rail-all16source-positions.jpg':'全部16源位置实际叠轨检查：四外边/四坡角色与源朝向一致，中央水平使用两段复用；中央竖向为明示原生纹理16px侧投影、逻辑N–S，非新绘透视。',
  'rail-halftilewater-four-corners.jpg':'W/N/E/S四个高半格用实际水面、三角地基、原轨段裁片；隔栏只在高半格分隔线并提升一个高度级，水半格没有多余栏段。'}
 items=[]
 for name,finding in findings.items():
  f='previews/fence-adapter/'+name;items.append({'file':f,'sha256':wp.sha(R/f),'status':'passed-local','finding':finding})
 report={'createdAt':wp.now(),'manifest':wp.rel(mp),'manifestSHA256':wp.sha(mp),'localVisualPassed':True,'items':items,'reviewedAssets':[{'file':a['image'],'sha256':a['sha256'],'status':'passed-local'}for a in m['assets']],'reviewMethod':'view_image actual current eight contact pages;114 farm four-edge assemblies +16 actual rail positions +4 half-water assemblies;current formal PNG hashes frozen','sourcePaintingReuse':{'nativeMastersAdded':0,'nativeMaterialInputs':3,'codePaintedFence':False,'operations':['source-pixel affine projection preserving vertical posts','native wood insert into native hedge cutout','selective native petal hue grade','functional triangle alpha mask of existing rail in preview']},'limitations':['中央竖向隔栏是现有木栏的窄侧投影共享，不声称新的原生视角。','190 rail selector记录源码选择，不声称全部坡/groundType组合可建造。','Unity遮挡、碰撞与用户美术批准尚待后续验证。'],'failures':[],'userArtAcceptance':'pending','unityValidated':False}
 wp.writej(R/vr,report);print(json.dumps({'manifestSHA256':wp.sha(mp),'reviewedPages':len(items),'reviewedAssets':len(m['assets'])}))
if __name__=='__main__':main()

"""Refresh transport-specific handover from frozen formal manifests."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
p=load('assets/world/infrastructure/transport-runtime/manifest.json');q=load('records/world-production/transport-runtime-validation.json');b=load('assets/world/infrastructure/transport/manifest.json')
text=f"""# 交通设施美术交付

本包是道家Q版重绘的站场、车库、桥梁、隧道及水桥图片与装配数据；不包含Unity工程或交通业务代码。固定功能参考OpenTTD cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8。

## 当前实物

- 交通基础图包：{len(b['assets'])}张正式PNG，来自5张被采用的原生图集（48个原生绘画对象及声明的轴对称变体），统一透明画布；原生图集仍在source-art/world，512画布不是512原生细节。
- 源角色装配包：{len(p['assets'])}张PNG，明确映射28项需求；裁切、Alpha分层、重采样、镜像和材质衍生不计新原画。
- [基础清单](../assets/world/infrastructure/transport/manifest.json)、[装配与分层清单](../assets/world/infrastructure/transport-runtime/manifest.json)、[本包检查](../records/world-production/transport-runtime-validation.json)。
- 本地源包机械失败数：{len(q['failures'])}。最终独立检查以[FULL_GAME_ACCEPTANCE_STATUS.json](FULL_GAME_ACCEPTANCE_STATUS.json)为准，用户审阅与Unity验证另列。

## 覆盖规则

铁路站场保留8个源布局角色：裸站台、带楼站台、带顶棚A/B及双轴。公交/货站各6角色，铁路路径点8角色，道路路径点2角色。站台、棚顶、货台、站房、信号房、人行天桥、门亭分别保留独立图；共享原画与布局侧别在数据中注明。

铁路与公路车库有真实四个正背视图；船坞双轴由明确对称模块表示。普通、电气、单轨和磁悬的已绘前部具有不同轨制形态，后部共享同风格壳体，不能误称每种轨制新增4幅原画。

6类隧道（4轨制、公路、有轨）提供4方向×3气候的对应数据。前两视可见入口，后两视为实际背山视角；道路/轨道走廊与原生门框分层，不把背面当作正面图片旋转。雪地/沙漠槽位的部分建筑采用明确的冷暖材质调色；不声称额外生成原生积雪细节。

13个原始桥规格映射7个结构母件，另有独立桥墩、悬索塔与整桥配套设计图。7段角色、X/Y轴、道路/铁路层、±32端坡和重复跨段均记录在coverageMappings。奇偶中跨共享周期母件，原始规格的局部材质差异用声明的调色表达。

水桥8角色/2轴/4方向岸头共用真实石渠和桥墩。按源码tunnelbridge_cmd.cpp:385、:468，岸头落在相容斜地，水面保持水平；不把水面画成车辆坡道。岸头选用已交付Foundation斜地支撑，下一阶段验证场景接触和水运净空。

## 几何、图层与导入建议

桥身384×384、anchor[192,320]。平跨X位移[128,64]、Y位移[-128,64]；端坡位移读取每片projection.advancePx，Y=64-rise。sourceDeckQuad和targetDeckMouths是实测原画截面到共同接口的映射，保留垂直柱，不按整幅bbox猜桥口。正式图检见[桥口几何](../records/world-production/bridge-joins-geometry.json)和[水桥拼装](../previews/world/aqueduct-joins.jpg)。

铁路/道路走廊使用实际原画像素与明确UV/Alpha遮罩，具体层资源、offset、相对画布和源记录读取装配manifest；禁止把整张含草地地块直接叠在窄桥面。whole与rear/front为替代绘制方案，不能重复叠加。独立前后层可精确重组成whole，并不证明Unity中所有车辆高度与遮挡已经正确。

Sprite建议Single、Full Rect、Bilinear、Clamp、sRGB、保留输入Alpha；初验关闭有损压缩与Mip Map。Pivot按anchorPx换算为[x/width,1-y/height]。世界PPU与最终坐标约定统一，不直接套用UI的100。世界地块与建筑不能使用九宫格拉伸。

## 预览、来源与下一阶段

- [站场图](../previews/world/runtime-station.jpg)、[车库图](../previews/world/runtime-depot.jpg)、[隧道图](../previews/world/runtime-tunnel.jpg)、[桥型图](../previews/world/runtime-bridge.jpg)、[水桥图](../previews/world/runtime-aqueduct.jpg)。
- [完整世界图册](../previews/world/index.html)、[整套美术总览](../previews/full-game-overview.jpg)。
- 两张用户主参考为F盘designs/mail-ui-v1/01-mail-event.png与designs/team-ui-v2/team-ui-v2.png，均实际附图；本项目assets/world-viewport.png另作画法/相机参考。所有AI入口是内置image_gen，实际model/quality未披露，以逐图记录null为准。
- 来源与关联只写E盘本项目；F盘只读。没有提交、推送或Unity运行操作。
- 用户画面验收之后，在Unity验证真实tile坐标、地形高差、桥下/桥上净空、载具实际footprint、隧道口深度遮罩、站房选中界限及道路/铁路走廊和业务状态。
"""
(R/'docs/TRANSPORT_ART_DELIVERY.md').write_text(text,encoding='utf-8')
print('Transport handover refreshed',len(p['assets']),'formal runtime PNGs')

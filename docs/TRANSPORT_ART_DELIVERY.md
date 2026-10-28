# 交通设施美术交付

本包是道家Q版重绘的站场、车库、桥梁、隧道及水桥图片与装配数据；不包含Unity工程或交通业务代码。固定功能参考OpenTTD cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8。

## 当前实物

- 交通基础图包：75张正式PNG，来自5张被采用的原生图集（48个原生绘画对象及声明的轴对称变体），统一透明画布；原生图集仍在source-art/world，512画布不是512原生细节。
- 源角色装配包：保留1034张角色PNG，补充211张真实路轨走廊所需的UV、lane、cleanPortal与遮罩，合计1245张PNG。其中1159张美术Sprite、86张Alpha遮罩数据；明确映射28项需求。裁切、Alpha分层、重采样、镜像和材质衍生不计新原画。
- [基础清单](../assets/world/infrastructure/transport/manifest.json)、[装配与分层清单](../assets/world/infrastructure/transport-runtime/manifest.json)、[本包检查](../records/world-production/transport-runtime-validation.json)。
- 本地源包机械失败数：0。最终独立检查以[FULL_GAME_ACCEPTANCE_STATUS.json](FULL_GAME_ACCEPTANCE_STATUS.json)为准，用户审阅与Unity验证另列。

## 覆盖规则

铁路站场保留8个源布局角色：裸站台、带楼站台、带顶棚A/B及双轴。公交/货站各6角色，铁路路径点8角色，道路路径点2角色。站台、棚顶、货台、站房、信号房、人行天桥、门亭分别保留独立图；共享原画与布局侧别在数据中注明。

铁路与公路车库有真实四个正背视图；船坞双轴由明确对称模块表示。普通、电气、单轨和磁悬的已绘前部具有不同轨制形态，后部共享同风格壳体，不能误称每种轨制新增4幅原画。

6类隧道（4轨制、公路、有轨）提供4方向×3气候的对应数据。前两视可见入口，后两视为实际背山视角；道路/轨道走廊与原生门框分层，不把背面当作正面图片旋转。雪地/沙漠槽位的部分建筑采用明确的冷暖材质调色；不声称额外生成原生积雪细节。

13个原始桥规格映射7个结构母件，另有独立桥墩、悬索塔与整桥配套设计图。7段角色、X/Y轴、道路/铁路层、±32端坡和重复跨段均记录在coverageMappings。奇偶中跨共享周期母件，原始规格的局部材质差异用声明的调色表达。

水桥8角色/2轴/4方向岸头共用真实石渠和桥墩。按源码tunnelbridge_cmd.cpp:385、:468，岸头落在相容斜地，水面保持水平；不把水面画成车辆坡道。岸头选用已交付Foundation斜地支撑，下一阶段验证场景接触和水运净空。

## 几何、图层与导入建议

桥身384×384、anchor[192,320]。平跨X位移[128,64]、Y位移[-128,64]；端坡位移读取每片projection.advancePx，Y=64-rise。sourceDeckQuad和targetDeckMouths是实测原画截面到共同接口的映射，保留垂直柱，不按整幅bbox猜桥口。正式图检见[桥口几何](../records/world-production/bridge-joins-geometry.json)和[水桥拼装](../previews/world/aqueduct-joins.jpg)。

铁路/道路走廊使用实际原画像素与明确UV/Alpha遮罩，具体层资源、offset、相对画布和源记录读取装配manifest；禁止把整张含草地地块直接叠在窄桥面。whole与独立层为替代绘制方案，不能重复叠加。

隧道512×512、anchor[256,448]。72状态均有具体映射；SE/SW前视按`rear → floor → front`装配，lane为同画布、offset[0,0]。`laneProjection.targetQuadPx`记录实测洞前走廊；`removedFloorMask`只移除新lane共用内域中的原黑地板和草Alpha，不修改石门、灯座和立柱；`cleanPortalImage`为已清除底体。NE/NW是真实背山视图，`floorVisible:false`，不在背山前额外贴街道。电气铁路地板复用普通轨道原画，接触网另行使用已交付的独立杆/线层。

桥的13源码规格×双轴×公路/铁路共52状态，每状态7角色，共364条角色绑定。按`rear → lane → front`装配，lane为384×384、anchor[192,320]、offset[0,0]，与冻结的`projection.targetDeckQuadBeforeAxisMirror`、轴镜像和端坡profile同坐标。`laneOwnershipMask`限定桥面中央70%横向走廊，另按实际颜色保护原画绿桁架、屋顶和暗色结构。`rear`保留被lane覆盖的原地板，`front`保护其余原画结构；两者精确重组原结构，三层精确重组已就位whole。静态就位预览已经核实；此保护层尚未等同车辆前后遮挡解算，接入时需按车辆尺寸再细分后侧与前侧结构。

新增211张包括5张真实UV条带、84张桥lane、84张桥ownership mask、30张隧道lane、6张cleanPortal和2张portal mask。公路条带来自road-topology原画中央铺装（去除边角花草Alpha），有轨电车来自实际双轨；普通、单轨、磁悬来自rail-topology实际条带。所有条带的源裁切、UV域、投影、透明通道与来源哈希在逐图`.derivation.json`记录，属于确定性图片衍生，没有新增AI生成或原生细节。

Sprite建议Single、Full Rect、Bilinear、Clamp、sRGB、保留输入Alpha；初验关闭有损压缩与Mip Map。Pivot按anchorPx换算为[x/width,1-y/height]。世界PPU与最终坐标约定统一，不直接套用UI的100。世界地块与建筑不能使用九宫格拉伸。

86张白色RGB的mask为数据，禁止作为可见美术显示；建议关闭sRGB、压缩和Mip Map，按采样方案选择Point或Bilinear，Alpha只用于所有权/裁切。正式美术PNG均保留真实Alpha。UV条带外留2px透明边，内域读取`innerUVRectPx`；它们是共享材质输入，不直接把条带当成整屏Sprite。

## 预览、来源与下一阶段

- [站场图](../previews/world/runtime-station.jpg)、[车库图](../previews/world/runtime-depot.jpg)、[隧道图](../previews/world/runtime-tunnel.jpg)、[桥型图](../previews/world/runtime-bridge.jpg)、[水桥图](../previews/world/runtime-aqueduct.jpg)。
- [走廊完整装配图册](../previews/world/transport-lanes/index.html)：72隧道状态、156张独有桥平跨/正负坡、真实UV条带及6张1:1细节。桥head与north同姿逐像素核实，周期角色明确复用。机械核验见[3871项走廊检查](../records/world-production/transport-lane-validation.json)，逐页实看记录见[走廊视觉检查](../records/world-production/transport-lane-visual-review.json)。
- [完整世界图册](../previews/world/index.html)、[整套美术总览](../previews/full-game-overview.jpg)。
- 两张用户主参考为F盘designs/mail-ui-v1/01-mail-event.png与designs/team-ui-v2/team-ui-v2.png，均实际附图；本项目assets/world-viewport.png另作画法/相机参考。所有AI入口是内置image_gen，实际model/quality未披露，以逐图记录null为准。
- 来源与关联只写E盘本项目；F盘只读。没有提交、推送或Unity运行操作。
- 用户画面验收之后，在Unity验证真实tile坐标、地形高差、桥下/桥上净空、载具实际footprint、隧道口深度遮罩、站房选中界限及道路/铁路走廊和业务状态。

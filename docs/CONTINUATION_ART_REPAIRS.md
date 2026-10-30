# 迁移接续后的源码状态与美术返修

沿用唯一生产目录 `E:/work/image/OpenTTD_UI_20261026_060146`，功能参考仍为 OpenTTD `cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`。本记录解释补包的使用关系；实时完成状态读取 [完整终检](FULL_GAME_ACCEPTANCE_STATUS.json)。分包制作、机械检查、实际图审、用户批准及 Unity 运行分开记录。

## 本轮修正的实际问题

| 实际源功能或缺陷 | 正式采用合同 | 预览与证据 |
|---|---|---|
| 半格曾误作四分之一格；陡坡双层和特殊轨道顶面也需修正 | 半格三角形、SteepBoth 高低两层；66 有效 Foundation 组合，None/无效组合不绘制 | [地基修复](FOUNDATION_GEOMETRY_REPAIR.md)、`records/world-production/foundation-geometry-validation.json` |
| 8张完整头像不足以替换五官 | 4样式、213 Sprite 值槽、16开关态、6眼色绑定；235条关系和独立部件 | [经理预览](../previews/manager-customization/index.html)、[专项说明](MANAGER_FACE_RESOURCE_AUDIT.md) |
| 鼠标与选区未纳入旧总清单 | 实测热点(9,8)、5组源时序、坡面/半格/自动铁路及强制红态分别映射 | [指针预览](../previews/pointers/index.html)、`records/pointer-art-validation.json` |
| 窗口和经营小图标缺绑定 | 96源码符号与19公司/兼容色态；功能线条和原生图素派生分别记录 | [小图标预览](../previews/micro-ui/index.html)、[说明](MICRO_UI_DELIVERY.md) |
| 道路单行/禁行地面标记缺失 | 18源槽、114原坡/轴/限制态到基础转换后的实际坡面绑定 | [道路标记](../previews/road-oneway/index.html)、[说明](ROAD_ONEWAY_DELIVERY.md) |
| 机场建造选择缺9张明确图示绑定 | 直接复用9张实际机场布局图；Oilrig不是可建机场选择项 | [机场九图](../previews/airport-ui/index.html)、[说明](AIRPORT_UI_PREVIEWS.md) |
| 路边灯树缺放置及状态合同 | 2灯向/树、普通/透明，源mask位置、低桥净空、远景/施工/不可见抑制分别记录 | [路边装饰](../previews/roadside/index.html)、[说明](ROADSIDE_ART_DELIVERY.md) |
| 桥梁只有普通轨面 | 13桥×2轴×4轨制×7角色；普通/电气共用原轨面，单轨/磁浮采用各自原生条带 | [桥面制式](../previews/world/bridge-railtypes/index.html)、[说明](BRIDGE_RAILTYPE_DELIVERY.md) |
| 原先只有6组产业机械，缺煤电火花/气泡发生器安装 | 当前8组＝6机械＋2粒子父绑定，共96相位；移除烘焙大泡，完整ownership包含删除范围和所有运动像素 | [整厂动画](../previews/world/industry-assembly/index.html)、[说明](INDUSTRY_PARTICLE_BINDINGS.md) |
| 农田16“随机变体”未表达真实周期 | 有效阶段0–8×19坡；成熟麦丛/收获草捆和幼苗分别制作，植株竖立且根部贴合坡面 | [农田阶段](../previews/world/field-stages/index.html)、[说明](FIELD_STAGES_DELIVERY.md) |
| 路径预留、农田/铁路围栏的适用状态缺失 | PBS只灰化轨段所有权；农田6有效家族、坡边端点、铁路8角色/16位置/半水角点各有绑定 | [PBS](../previews/rail-reservation/index.html)、[围栏适配](../previews/fence-adapter/index.html) |
| 旧岸线索引顺排错误且始终平面；岩石用粗砾密度冒充 | 16有效坡×3气候＋6保留不绘制；真实水/陆/岸分层；6岩石环境态、干地双布局、逐石坡面根部及CoastRocks组合 | [坡岸线](../previews/world/shore-geometry/index.html)、[岩石](../previews/world/rocks-overlay/index.html) |
| 雪/沙阶段0被误作全裸地 | 0–3阶段对应1/4、1/2、3/4、完整材质覆盖；160输出定向返修，其它PNG保持 | `records/world-production/terrain-density-quarter-repair.json`及其独立实际图审 |
| 岸沙、雪草、浅水重复出现明暗边框 | 3张新原生方形材质母图，分别投影 flat+19坡；8×8真实正式像素重复复核 | `previews/world/terrain-repeat.jpg`、`terrain-*-repeat8.jpg`、各材质修复记录 |

旧的地形 field UV 位移、装饰围栏配色、粗砾密度图不能代替新的源阶段/源围栏/独立岩石合同。适用范围以最新覆盖表的具体 variant checks、分包 source bindings 和证据文件为准，不能只按 PNG 数量判断完整性。

## 新原生绘画与派生操作

迁移返修阶段新增的6张母图为 `source-art/world/shore-sand-seamless.png`、`snowgrass-seamless.png`、`shallow-seamless.png`、`rock-overlays-native.png`、`roadside-lamps-native.png`、`field-crop-components-native.png`。每张有独立 `.generation.json`，实际提示词和调用时段保存在 `records/world-production/*-call.json` 与相应 `.prompt.txt`。它们均通过内置 imagegen 生成，实际模型和质量未披露，保持 `null`；配置目标不作为返回证明。之后追加的品牌原生图另按[品牌包](../branding/yuntu-wanli/README.md)及[正式资源清单](asset-branding-manifest.json)记录，不混入本段返修阶段的历史数量。

对应正式资源中的裁片、Alpha所有权提取、等比缩小、周期边缘混合、几何投影、颜色派生、组合和二维运动均有单独操作说明。底图导出尺寸及透明补边不会被记为新的原生高清细节。已确认的既有原画继续沿用。

## 接入时的互斥关系

- 桥、隧道按清单 `layerOrder` 使用 rear/lane或floor/front；整图与分层是二选一，不同时叠画。Pier和mask不是主体重组层。
- 产业 `cleanBase+moving` 替代同一原姿态父图，不能在旧烘焙厂区上再叠一次。粒子循环是现有FX原像素的缩小、位移、Alpha及组合，不是新增三维角色动作。
- 农田 whole 与 soil+plant overlay 二选一。使用坡面锚点和每个根部位置，不能把整片立体作物压成斜平面。
- 正式名称为《云途万里》，名称与本地 Logo 已获授权纳入整款美术交付，见[品牌包](../branding/yuntu-wanli/README.md)。公司/地名与静态经营数值仍为美术样例；最终审美批准待用户确认，Unity、Prefab、业务状态、动态文字及运行验证留待另行确定的接入阶段。

F盘只读；未改共享Git状态，未提交、推送或发布。成果远端、账号与提交要求仍待用户提供。

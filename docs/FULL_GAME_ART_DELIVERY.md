# 云途万里 · 完整游戏图片与UI美术交付

本对话目录为`E:/work/image/OpenTTD_UI_20261026_060146`。功能研究固定参考OpenTTD提交`cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`。本阶段交付图片、资源数据、美术规格和离线检查预览；用户美术审阅与下一阶段Unity运行验收分别记录。

正式名称为《云途万里》。用户已授权将名称与本地 Logo 方案整合进本次交付，[品牌包](../branding/yuntu-wanli/README.md)提供透明主标、独立图标、派生尺寸与逐图来源；最终审美批准仍待确认。

## 独立终检快照

以下快照由独立终检实际运行刷新，覆盖标示时间和输入版本，包括正式名称与 Logo 整合。检查数、资源数与结果均取自当前执行，不沿用此前版本的通过数。

<!-- audit-snapshot:begin -->
核查时间（UTC）：`2026-10-29T08:11:44.830893+00:00`。当前分包清单列出 **12212** 个正式PNG，其中UI **657**、世界/载具 **11555**；保留的原生AI母图 **90** 张，逐图记录 **91** 份（含 **1** 份明确废弃图文字证据）。

本次机械检查 **230455** 项通过、**0** 项失败、**0** 项警告。世界 **550** 项需求中，总覆盖表当前映射 **550** 项，仍缺资源或映射 **0** 项；未有最终本地验收记录 **0** 项。世界总聚合与当前分包记录一致。

具体缺口、警告和输入版本见[完整验收状态](FULL_GAME_ACCEPTANCE_STATUS.json)与[终检证据](../records/full-game-art-audit.json)。
<!-- audit-snapshot:end -->

正式映射、适用状态、本地视觉检查、用户批准与Unity正确运行分别记录；本轮品牌整合的最终输入一致性由独立终检确认，当前状态文件保存这些区别。

## 预览与资源入口

| 内容 | 入口 | 正式文件/说明 |
|---|---|---|
| 正式名称与 Logo | [品牌专页](../previews/branding/index.html) · [品牌资源与使用说明](../branding/yuntu-wanli/README.md) · [整合说明](BRAND_INTEGRATION_DELIVERY.md) | 透明主标、独立图标及等比缩小版共8件；正式参数见[品牌资源清单](asset-branding-manifest.json)，并入[全游戏资源索引](ART_RESOURCE_INDEX.json) |
| 全部美术方向与实际拼装示例 | [完整总览](../previews/full-game-overview.jpg) · [透明资源拼装](../previews/world/assembled-transport-town.png) | 均由当前正式图片按数据拼装/等比排版，继承源SHA；不是新生成全景或Unity运行画面 |
| UI整屏、状态和关联流程 | [主预览](../index.html) · [整屏总览](../previews/overview.jpg) · [流程图](../previews/flow-map.svg) | `designs/`、`previews/states/`；[UI总清单](UI_MASTER_MANIFEST.json)与[CSV](UI功能与资源总清单.csv) |
| 通用控件、图标、货物、头像和字体 | 主预览“资源与切片” | `assets/common/`、`assets/icons/`、`assets/cargo/`、`assets/portraits/`、`assets/fonts/`；[UI资源参数](ASSET_MASTER_MANIFEST.json) |
| 世界地块、建筑、地物、交通与状态 | [世界预览](../previews/world/index.html) | `assets/world/`；[世界资源索引](WORLD_ASSET_MANIFEST.json)、[550项覆盖表](WORLD_DELIVERY_COVERAGE.json) |
| 产业8组实际安装动画 | [整厂动画预览](../previews/world/industry-assembly/index.html) | 6机械＋2粒子、96相位；cleanBase、完整父坐标移动层、ownershipMask与绑定说明；不叠加旧静态厂区 |
| 车辆方向、型号、载货与效果 | [车辆/效果图册](../previews/vehicles/index.html) | [型号索引](VEHICLE_RUNTIME_MANIFEST.json)、[公共效果](EFFECT_RUNTIME_MANIFEST.json)、[灾难](DISASTER_RUNTIME_MANIFEST.json)、[详细交付说明](VEHICLE_FX_DELIVERY.md) |
| 独立机械终检 | [终检报告](../records/full-game-art-audit.json) | 可重跑`tools/final_art_audit.py`；不修改图片、分包manifest或F盘 |
| 经理头像参数与高级流程 | [专项源码/资源核查](MANAGER_FACE_RESOURCE_AUDIT.md) · [机器需求](MANAGER_FACE_REQUIREMENTS.json) | [当前专项结果](../records/manager-customization-audit.json)；与8张完整preset区分 |

所有浏览器预览均为本地图片检查器。筛选、静态状态、动画帧播放和拼装画布用于检查美术，不代表Unity场景、交通仿真、联机或业务接口已实现。主预览新增世界/载具/覆盖入口，没有重绘既有UI。

接续源码状态与返修见[完整返修记录](CONTINUATION_ART_REPAIRS.md)，紧凑的逐资源导入入口为[完整资源索引](ART_RESOURCE_INDEX.json)。该索引包含正式精灵及数据掩码；资源PNG数与原生绘画数分别统计。

## 功能与美术范围

游戏类型是交通网络经营模拟。UI的132项上游功能映射到149张1920×1080整屏与227张960×600状态，包含启动/资源引导、新建/载入/保存、建设HUD、铁路/道路/有轨/水运/航空、站场/车库、采购改装、车队/自动替换、指令/时刻表、公司财务绩效、地图货流、城镇产业、新闻补贴/目标故事、联机聊天、在线内容/NewGRF、AI/GameScript、设置帮助及情景编辑。未机械叠加RPG成长、装备、战斗、背包、抽卡或签到。

世界当前有550项根据源码枚举、布局、资源表与状态要求建立的需求；256个车辆型号由独立清单管理。应同时查看需求的`neededVariants`、资源映射、绘画父件、适用状态和验收字段，不能只按PNG数量判断覆盖率。

<!-- manager-snapshot:begin -->
经理参数化头像专项：235/235项source值/状态绑定，资源与必要状态的本地专项检查通过，仍待用户与Unity验收。原8张完整preset与参数化五官/服饰层分开统计，详见[专项结果](../records/manager-customization-audit.json)。
<!-- manager-snapshot:end -->

| 分包 | 生产方式及使用边界 |
|---|---|
| 地形、基础与水面 | 原生绘画材质，精确菱形归一，19坡型和适用密度/田地阶段；基础另有13有效Foundation模式和None/不适用配方，采用连续原生石面支撑而非装饰围栏；水面关键图交叉混合，明确区别原生关键帧和派生帧 |
| 道路、轨道、信号与交通设施 | 实际绘画条带/部件经过UV投影、组合和状态处理，保留连接掩码、端口、轨制、气候与图层说明；方向重复或几何变换不伪称新的原生透视 |
| 房屋 | 45个原生新风格母型映射110个源tileID、94个父建筑；4随机材质×4施工阶段与多格片段各自记录，1760条组合映射不等于1760幅独立原画 |
| 产业 | 37个完整产业母型与实际机械部件，175个源gfx×4施工阶段/60个布局以父实例和模块映射；完整厂区不在每个源格上重复绘制 |
| 植被 | 41类树×7个成长/枯死阶段，复用已声明生命周期部件；阶段静图不伪称风动动画 |
| 车站、机场、桥隧和水工 | 对照实际站场、机场布局、桥型、前后层和水工状态提供模块与组合合同；具体完成项以最终覆盖表为准 |
| 车辆 | 27个8向原创绘画家族、216张家族方向、256个源型号；涂装、底架、可见货载和密闭容器共享身体如实区分 |
| 效果与灾难 | 12个上游效果类型、15个灾难子类型；烟、火花、爆炸、泡泡、影子和旋翼按原生关键图/二维派生操作交付，不虚构整车或实体的完整运动动画 |

## 分辨率、透明和切片合同

UI动态文字保持独立层。正式控件真实Alpha、按钮同族同画布；九宫格顺序固定Left/Bottom/Right/Top，各件参数见UI资源manifest。整屏是版式设计，不能整图拉伸当作可交互UI。

世界统一2:1等距投影，逻辑平地128×64，正式平地256×128，坡面256×192，层高32像素。方向、边中点端口、坡码及锚点语义见[世界模块规格](WORLD_MODULE_SPEC.md)。建筑前接地点、地块中心、车辆占地中心和效果发射点不是同一位置，应按具体manifest读取；同族状态保持指定画布、锚点和图层关系。

母图实际尺寸包含1254×1254、1536×1024、1774×887等，逐图记录为准。正式512画布、投影、裁切、透明补边、等比缩小和UV重采样不代表新模型原生细节。房屋/总部的whole与tile fragments是替代绘制方案，不能叠加重复绘制；分区可准确重组不等于已在Unity解决全部深度遮挡。

桥梁13个源码BridgeSpec使用7幅原生结构母件及已声明材质变体，7种源码部件角色由重复跨、端坡和独立桥墩/悬索塔映射，不等于13套独立原画。连续跨的地板截面、金色端柱位置经实测原图像素重投影；±32端坡使用锁定两端截面的二维高度转移。原像素采样、镜像与颜色派生均有记录。可重跑`tools/preview_bridge_joins.py`从实际runtime PNG检查13型×2轴×平接/端坡，数值与图片见[桥口几何证据](../records/world-production/bridge-joins-geometry.json)和[桥口复核说明](../records/world-production/bridge-geometry-notes.md)。

产业现有8组实际安装动画：6组机械与煤电厂火花、气泡发生器2组粒子绑定，各12相位，共96张移动层及96张整厂组合预览。分别交付cleanBase、同512父画布且已定位的移动层、ownershipMask和父锚点绑定。使用`animations[].binding`时替换原静态父图，不能再把动画叠在烘焙同一运动姿态的原图上；气泡发生器先按removedPoseMask移除旧泡，煤电厂cleanBase保持原像素。机械的旋转/往复/流动与公共FX的缩小/位移/生命周期播放均是声明的二维处理，不是新生成的三维运动帧。独立终检按8组96帧重组并核对所有权外固定结构与Alpha，粒子合同见[专项说明](INDUSTRY_PARTICLE_BINDINGS.md)。

水桥水面始终水平，8个源码部件角色在两轴上使用实际运河模块，4个斜地桥头以独立地基承接；双轴三跨见[水桥拼接](../previews/world/aqueduct-joins.jpg)与[16组/32接口证据](../records/world-production/aqueduct-joins-geometry.json)。船闸开门后的上游通道保留真实Alpha开口，场景应单独绘制上游水/岸背景，不烘焙蓝色矩形补片；其低水位内壁由实际原生绘画注册到固定外墙。

## 证据与验收

既有UI保留4279项机械检查及20项浏览器检查。载具、公共效果和灾难已有独立19438项本地检查。各分包还保留本地视觉联系图、Alpha、几何/状态和源映射记录；这些历史检查只证明对应输入版本，不自动覆盖后续改动。

新增独立终检从当前分包manifest读取正式PNG，检查实际尺寸、SHA、透明Alpha、锚点边界、九宫格、来源文件/哈希、所有母图提示词全文/参考SHA/配置目标与实际返回披露、UI与预览路径，并比较世界总清单是否仍与分包一致。运行期间若分包改变，会标为输入发生变化，需在生产稳定后刷新。详细失败和警告保存在完整验收状态中，不把在制项或光度/接缝警告静默转为通过。

独立终检还从实际导出的前后层PNG重组站场、桥隧和船闸，并比较可见RGBA逐像素一致性；桥口另外检查104个接口的几何重合和实际Alpha。透明边缘清理、重组成功和拼接连续都不替代用户审美批准、车辆净空或引擎深度排序验收。

桥口正式验收页保留为`bridge-joins-page1..13.jpg`。27个已核实过期的工作候选/坐标检查文件已清理，正式页、来源与几何验收文字保留，详见[清理状态](../records/world-production/bridge-cleanup.json)。最初使用变量路径的清理命令被自动审批拒绝，随后改为同一原生PowerShell工具可直接审查的固定LiteralPath文件删除，无递归删除或审批覆盖。

重跑：使用本机带Pillow的Python执行`tools/final_art_audit.py`，输出`records/full-game-art-audit.json`和`docs/FULL_GAME_ACCEPTANCE_STATUS.json`，并刷新本文的快照段。该脚本只作独立核查，世界总清单与图册由相应聚合工具维护；需先完成分包和聚合，再运行最终审计。

## 来源与后续接入

功能参考仓库、F盘美术参考库、本次E盘成果目录和未来成果远端分别管理。[SOURCES.md](SOURCES.md)记录来源，[image-reference-associations.md](image-reference-associations.md)是当前本地关联权威记录。F盘完全只读；未从旧Git恢复缺失规范，没有操作共享HEAD/index/refs。本项目未提交、推送或发布，成果GitHub/账号/要求待用户提供，参考源码目录不整体纳入成果提交。

宿主内置image_gen未开放model/quality选择器，实际型号和质量保持null并注明未确认；`gpt-image-2.5-sunburst / max`仅是配置目标。正式母图保留生成时间、实际参数全文、返回证据、参考图片和输出SHA。裁切/组合/投影/二维运动继承源记录，不当作新生成。废弃图删除后仍保留明确的文字记录，不计为当前正式母图。

名称与 Logo 已获授权纳入美术交付。待用户最终审阅美术并另行确定接入阶段后，再按[UNITY_IMPORT.md](UNITY_IMPORT.md)验证Sprite/TMP、Canvas/图集/九宫格、地块接缝与坡面、多格遮挡、车辆比例/载货/朝向、帧时长、真实状态反馈及业务接口。本阶段没有C#、Prefab、Unity场景、引擎运行或在线联调。

# 云途万里 · OpenTTD 道家 Q 版游戏美术

正式游戏名为 **《云途万里》**。用户已授权将该名称与本地 Logo 方案纳入整款游戏美术交付；主 Logo、独立图标及常用尺寸见[品牌设计与透明资源](branding/yuntu-wanli/README.md)。本地检查通过，用户最终审美批准仍待确认。

本对话独立项目：`E:/work/image/OpenTTD_UI_20261026_060146`。本地交付范围包括品牌、UI、世界地块与地物、车辆朝向和适用效果资源。当前只制作图片、美术规格和预览；没有搭建 Unity 工程或改写参考游戏。整套状态以[完整美术验收状态](docs/FULL_GAME_ACCEPTANCE_STATUS.json)标明的核查时间与输入版本为准；品牌整合后的总计由最后一次独立终检刷新，旧通过快照不自动覆盖新增资源。

## 查看交付

- [整套本地预览](index.html)：界面筛选、原尺寸整屏、227个状态预览、关联流程跳转。
- [正式品牌专页](previews/branding/index.html) · [Logo 包与来源](branding/yuntu-wanli/README.md) · [品牌整合说明](docs/BRAND_INTEGRATION_DELIVERY.md)：透明主标、独立图标、派生尺寸与使用约束，8件正式PNG的参数见[品牌资源清单](docs/asset-branding-manifest.json)。
- [世界资源与拼装预览](previews/world/index.html) · [车辆、货载与效果预览](previews/vehicles/index.html)。
- [完整美术交付说明](docs/FULL_GAME_ART_DELIVERY.md) · [世界功能覆盖清单](docs/WORLD_DELIVERY_COVERAGE.json) · [独立终检](records/full-game-art-audit.json)。
- [完整美术总览](previews/full-game-overview.jpg) · [实际资源拼装示例](previews/world/assembled-transport-town.png)。
- [UI总览](previews/overview.jpg) · [核心流程图](previews/flow-map.svg)。
- [UI 功能与资源总清单 CSV](docs/UI功能与资源总清单.csv) · [机器可读完整清单](docs/UI_MASTER_MANIFEST.json)。
- [正式图片资源](assets/) · [资源参数总清单](docs/ASSET_MASTER_MANIFEST.json)。
- [Unity 导入建议](docs/UNITY_IMPORT.md) · [字体、文案与布局](docs/STYLE_AND_LAYOUT.md)。
- [验收结果](docs/ACCEPTANCE.md) · [来源与项目关联](docs/SOURCES.md)。
- [经理参数化头像专项核查](docs/MANAGER_FACE_RESOURCE_AUDIT.md)：8张完整预设与可替换部件分别验收，见[当前专项状态](records/manager-customization-audit.json)。

- [迁移接续返修与新增状态](docs/CONTINUATION_ART_REPAIRS.md)：包含经理、选区、小图标、道路、机场、产业、农田、桥面及围栏专项入口。
- [品牌整合接续检查点](MIGRATION_CHECKPOINT_20261029.md)：当前授权、文档边界及最终审计刷新事项；上一日检查点保留为历史快照。

## 范围

依据实际源码研究，132项上游功能已映射到149页整屏设计和227个必要状态。覆盖启动、开局、保存/载入、经营HUD、铁路、公路/有轨、水运、航空、车站、车库/采购/改装、车辆分组/自动替换、指令/时刻表、公司/财务/绩效/图表、地图/货流、城镇/产业、新闻/补贴/目标/故事、高分、联机/聊天、在线内容/NewGRF、AI/GameScript、设置/帮助、情景编辑和辅助工具。RPG等级、装备、战斗、背包、抽卡和签到没有机械加入。

完整窗口与来源见 [功能研究](docs/OPENTTD_RESEARCH.md)；各状态的入口、语义、操作与返回见 [文案及流程合同](docs/COPY_AND_FLOW.md)。静态图中的地名、公司名、车型和数值为排版示例，不代表已运行参考游戏。

## 资源与分辨率

设计画布为1920×1080；状态卡为960×600。独立通用控件、系统图标、货物图标与经理头像均另行交付。控件没有烘焙动态标题、数量或公司名称。正式控件PNG有真实Alpha，九宫格、Pivot、图集/原生裁切映射记录到逐件manifest；每张整屏的文字区域及控件摆放见 `docs/layouts/`。

UI 原生AI图实际为1672×941、1254×1254和1774×887；新增世界图集还有1536×1024等实际尺寸，逐图记录保存准确值。设计稿、材质投影、状态组合和动画部件处理均记录派生方法；设计画布、透明补边、缩放和裁切不代表原生生成细节提高。

世界资源采用2:1等距投影，逻辑地块128×64、正式平地256×128、层高32像素。地形、道路、轨道、房屋、产业、植被、车站、机场、桥隧、水工和附属设施分别交付；车辆按27个绘画家族映射256个上游型号。父建筑、多格裁片、施工阶段、共享部件和动画帧均应按各 manifest 使用。源码ID与新风格模块之间是明确的重设计映射，不是原OpenGFX像素图的一对一替换包。

## 生成与来源

本轮使用宿主内置image_gen；早期7张UI母图和后续世界、车辆图集均以各自记录核实真实参考输入。目标配置为`gpt-image-2.5-sunburst / max`。工具没有开放model/quality选择器，返回未披露实际模型与质量，两项明确为未确认。没有调用单独计费API。所有当前母图的提示词全文、参考SHA、实际尺寸与返回证据由[独立终检](records/full-game-art-audit.json)逐份核查。

[配置及官方核对](records/model-verification.json)、[提示词](records/)、`*.generation.json`、各资产manifest共同保存原生尺寸、哈希、实际输入、原图/派生关系。历史复用图片没有按当前配置改写模型信息。

## 仓库分别管理

- 功能参考：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，本地`reference/OpenTTD`，研究固定提交`cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`。
- 美术参考：`F:/work/image`，实际素材与读取文档见`docs/art-references.json`。
- 美术参考库保持只读；本项目关联的权威记录为[本地关联说明](docs/image-reference-associations.md)。
- 本次成果：[luhailong-python/OpenTTD_UI_20261026_060146](https://github.com/luhailong-python/OpenTTD_UI_20261026_060146)，分支 `main`；[Git交付说明](docs/GIT_DELIVERY.md)。
- `reference/`已在本项目.gitignore排除，后续提交不整体混入参考源码。本阶段没有提交、推送或发布；没有操作F盘共享Git的HEAD、index或refs。

## 下一阶段 Unity

正式名称与 Logo 已获授权纳入美术交付。本阶段仍不开展 Unity；待用户最终审阅美术并另行确定接入阶段后，再验证Canvas/TMP、SpriteAtlas、九宫格、世界地块接缝、坡度、图层遮挡、多格裁片、车辆比例/锚点/载货状态和动画节奏，并接上真实业务数据。现有导入参数、拼装预览和机械检查均不代表Unity运行通过。


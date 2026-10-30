# 来源与项目关联

核实日期：2026-10-26（America/New_York）。

| 角色 | 位置 | 用途 |
|---|---|---|
| 功能参考仓库 | https://github.com/OpenTTD/OpenTTD.git | 实读源码、窗口、控件、配置与资源；不提交成果 |
| 固定参考提交 | cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8 | shallow clone的实际HEAD |
| 参考源码本地 | E:/work/image/OpenTTD_UI_20261026_060146/reference/OpenTTD | 仅研究，与未来成果提交分别管理 |
| 美术参考仓库 | F:/work/image | 用户指定风格与获准控件 |
| 本次成果 | E:/work/image/OpenTTD_UI_20261026_060146 | 本对话独立目录 |
| 成果GitHub/账号 | [luhailong-python/OpenTTD_UI_20261026_060146](https://github.com/luhailong-python/OpenTTD_UI_20261026_060146) | 独立仓库 `main`；见[Git交付说明](GIT_DELIVERY.md) |

## 实际美术来源

- 首要风格输入：`designs/mail-ui-v1/01-mail-event.png`与`designs/team-ui-v2/team-ui-v2.png`。早期7张UI母图与后续世界、车辆母图均按逐图记录核实实际附图、参考SHA和用途；当前总数见独立终检，不能继续把7张当成整套母图数量。
- 同功能研究：`designs/gameplay-ui/02-inventory.png`、`designs/world-map-original-20260925/world-map-original.png`、`designs/social-ui-v1/02-world.png`。只参考画法/层级，不复制MMORPG业务。
- 通用控件直接复用：`designs/attribute-panels/v2-painted/unity-slices/png/`与`designs/attribute-panels/exact-20261022/staged/Assets/Resources/UI/Ugui/AttributeExact20261022/`中的12件；`designs/equipment-ui-20261008/sprites/checkbox_*.png`两件；`designs/team-ui-v2/unity-slices/png/status_*.png`两件。逐字节复制，完整SHA/原始Border见资源manifest。
- 主窗框、标题板与六态按钮来自本轮新生成`source-art/ui-kit.png`，不是复用旧team主框。
- 字体来自Google Fonts官方仓库Noto Sans SC与Ma Shan Zheng；下载证据、哈希与OFL随包。

世界、建筑、产业、植被、交通设施和效果的原生母图位于`source-art/world/`；车辆27幅母图位于`assets/world/vehicles/families/*/atlas.png`。本项目的`assets/world-viewport.png`额外用作世界投影与环境参考。真实8向载具、共享建筑母型、材质投影、模块组合、施工阶段、颜色派生和二维动画的区别均保留在分包manifest及派生记录中。

正式名称《云途万里》与本地 Logo 已获用户授权整合。品牌原生图、实际提示词、调用记录、参考SHA、透明成品与等比缩小版集中在[品牌包](../branding/yuntu-wanli/README.md)，分别追溯各自生成记录；不把缩小版计成新原画，也不改写早期生成/迁移历史。授权采用不自动等于用户最终审美批准。

原始艺术输入与现存规范实际核验：`art-references.json`和`ART_REFERENCE_AUDIT.md`。本项目来源关联的权威位置是 [本项目美术来源关联](image-reference-associations.md)。原来7段UI关联已迁回此文件；F盘对应README中的本项目新增段已移除，之后完全只读。原写入前后哈希、段落与日期见`../records/f-art-associations.json`，仅作历史执行证据；[项目关联索引](PROJECT_ASSOCIATIONS.md)连接当前记录。

换机交接已随包保留两张指定主参考`reference-images/`及`reference-rules/`中的AGENTS、统一配置、执行策略和美术定调原文快照。快照来源/字节/SHA见`../records/reference-rules-snapshot.json`。这些文件保存来源上下文；当前用户指令和本项目范围优先，不能用参考库规则覆盖F盘只读约束。缺失的`qdao_ui_redesign_v5/UI_SPEC.md`未从旧Git恢复。

## 模型与派生证据

每个AI源图的`*.generation.json`记录配置目标、实际可提交参数、返回字段、UTC时间、实际PNG尺寸、SHA、实际输入、提示词全文和独立`promptFile`路径。工具只有prompt、referenced_image_paths和transparent_background等字段，model/quality未开放，实际两项null并说明未确认；不能把官方公告或配置目标当作锁定调用的证明。早期7张UI图及一批世界图中把prompt误写为路径的元数据已依据原保留提示词纠正，图片和未确认的模型/质量未变，修正证据见`../records/ui-prompt-evidence-correction.json`与`../records/world-production/prompt-evidence-correction.json`。

官方目标核对依据：[产品公告](https://openai.com/index/introducing-chatgpt-images-2-5/)、[型号说明](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)、[Images参数](https://developers.openai.com/api/reference/resources/images/methods/generate)。本轮核对没有可证实的新正式型号需要升级，F盘配置未修改。

裁切、透明padding、等比缩小、九宫格组合与文字排版均标为派生操作，追溯源SHA与模型记录。原画源为当前生产母图，保留用于切片映射/复验；已由成品替代的临时QA样稿会在终检后清理，不保存额外图片备份。

## 参考仓库资源边界

源码仓库没有使用Git LFS；所需本仓图像/GRF真实字节已核验。完整OpenGFX/OpenSFX/OpenMSX是上游另行下载的运行资源，不在该源码clone里，不能声称已取得完整游戏运行美术。没有编译或运行上游。上游许可原文与第三方说明保留在参考仓库中；本次交付没有复制原游戏图像皮肤作为新美术。

Unity业务、场景、Prefab、在线接口与运行验收在下一阶段。本地UI/世界美术评审、静态方向或工具浏览器检查不代表Unity或游戏运行验收。世界资源按550项需求覆盖与验收，品牌补包由最终整合后的独立终检统一计数；当前整体状态与输入版本见[FULL_GAME_ACCEPTANCE_STATUS.json](FULL_GAME_ACCEPTANCE_STATUS.json)。


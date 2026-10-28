# 美术参考实读与使用核验

核实日期：2026-10-26（America/New_York）。本任务成果目录为 `E:/work/image/OpenTTD_UI_20261026_060146`；美术参考库为 `F:/work/image`。功能参考为 OpenTTD，成果远端待用户提供。此文档记录美术参考与控件提取，不代表 OpenTTD 功能覆盖或 Unity 接入验收。

## 已读规则与资料

- `AGENTS.md`：读取当时完整长期指令。本项目关联现已迁回 [本项目美术来源关联](image-reference-associations.md)，F 盘对应 README 中的新增段已移除；无恢复旧目录、共享 Git 操作或发布授权。
- `README.md`：读取“给接手的 Codex”与当前入口，跟进交接、美术与工具说明。
- `docs/WUXING_QITAN_HANDOFF.md`：读取当前接手与历史交付边界。五行奇谈的名称、角色身份、服务端数据和 Unity 已验证结论属于旧项目，不移作 OpenTTD 本任务事实。
- `docs/QDAO_ART_DIRECTION.md`：读取画法、人物差异、配色、原生尺寸与导出尺寸的区别。玉绿、象牙纸面、暖金与圆润云纹沿用，运输经营题材另行原创。
- `docs/AI_DESIGN_TOOLS_SETUP.md`：读取内置优先、运行时、工具安装及凭证边界。安装过 CLI 不等于本任务获付费 API 授权。
- `docs/IMAGE_MODEL_POLICY.md` 与 `config/image-generation.json`：读取目标型号/画质、无选择器时继续内置路径、实际返回未知标记及逐图来源合同。本子任务没有发起 AI 生成。
- `designs/README.md`：读取现存索引；发现旧 D 盘路径与“邮件缺失”描述过期，以根指令和实际文件为准。
- `designs/mail-ui-v1/README.md` 与 `UI_SPEC.md`：读取原生文字与横幅分离、列表/详情、附件和状态，参考画法与操作层级。
- `designs/team-ui-v2/README.md` 与 `unity-slices/manifest.json`：读取两列层级、字形可读性、来源及原九宫格。旧 `main_frame/title_plate` 在另一任务关联中记录存在矩形拼接色块，本任务不直接采用这两件。
- `designs/gameplay-ui/README.md` 与 `exact-20261022/README.md`：读取任务/背包/活动页层级及状态；该旧项目的活动、奖励和 MMORPG 业务不机械移入运输游戏。
- `designs/world-map-original-20260925/README.md`、`fidelity-20261016/README.md`：读取地图风格、18地名与原生/重采样区别；本任务不复用其世界名称和传送业务。
- `designs/scene-select-ui-v1/README.md`、`fidelity-20261016/README.md`：读取列表密度、动态状态、原图与清理派生区别；OpenTTD 网络服务器按实际功能呈现。
- `designs/social-ui-v1/README.md` 与 `UI_SPEC.md`：读取聊天/系统通知的层级与只读状态区别；OpenTTD 不因此新增好友、帮派、邮件等业务。
- `designs/attribute-panels/README.md`、`v2-painted/unity-slices/README.md` 和 `manifest.json`：读取无字控件、透明度、九切、固定图标与动态文字约定。`exact-20261022/README.md` 和 `sprite-provenance.json` 说明旧23px轨道只有6px实心，选择128×21修正轨道作本任务导入素材；未沿用其待安装结论。
- `designs/equipment-ui-20261008/README.md` 和 `sprite-manifest.json`：读取共用复选框两态及裁片来源，旧深绿装备详情卡不采用。
- `designs/ui-completion-20261021/README.md`、`requirements/README.md`：读取八界面与文案/后端边界。充值、会员、商城等不属于 OpenTTD 原生功能，不纳入本任务原生功能覆盖。

## 缺失与冲突

`F:/work/image/qdao_ui_redesign_v5/UI_SPEC.md` 当前不存在，因此无法实际读取第2节。没有从旧 Git、快照或已删除目录恢复。当前根 AGENTS 已完整写出最新风格；两张指定图均存在真实 PNG 字节并已查看，可继续不依赖缺失规范的设计。

`designs/README.md` 仍称 `designs/mail-ui-v1/01-mail-event.png` 缺失，并指向 D 盘历史路径。已按根 AGENTS 优先实际读取当前 F 盘 PNG，没有将旧 JPG 冒称同一文件。未更改 F 盘旧索引。

## 已实际查看的图片

| 图片 | 用途与观察 |
|---|---|
| `designs/mail-ui-v1/01-mail-event.png` | 首要画法：深玉绿标题、暖金细边、米白纸面；圆润边框，文字区安静，红穗集中边缘。 |
| `designs/team-ui-v2/team-ui-v2.png` | 首要画法：日景仙山、双栏层级、纸卡与选中控件、统一大头短身头像；不复用测试人物名单。 |
| `designs/gameplay-ui/02-inventory.png` | 列表/网格与详情及底部操作分区；用于车辆/货品目录信息层级核对。 |
| `designs/world-map-original-20260925/world-map-original.png` | 明亮地形、圆润建筑和清晰地点；用于经营场景的画法，不作地图数据或地名来源。 |
| `designs/social-ui-v1/02-world.png` | 米白聊天区、原生消息、固定输入栏与滚动区域；用于多人聊天的视觉层级。 |
| 属性 `unity-slices/png` 无字控件联系图 | 实看框、标题、按钮、数值框、纸卡、滑杆和固定图标；本任务只复用有用的小件。 |
| 装备 `sprites/checkbox_on.png` / `checkbox_off.png` | 两态98×98、Alpha一致，按字节复用。 |
| 属性 `exact-20261022/.../slider_track.png` | 修正版128×21轨道有完整实心厚度，搭配同源fill与原玉绿thumb。 |
| 本任务 `source-art/ui-kit.png` | 主控已生成的新无字母图；本子任务实际查看后无损裁切，未再次调用模型。 |
| `records/common-assets-qa.png` | 在浅底实看本批裁片：纸面、边框与按钮完整，底部红穗保留，六按钮无文字。 |

对应哈希、尺寸、PNG签名及 Alpha 证据见 `art-references.json`；正式控件见 `asset-common-manifest.json`。

## 通用资源提取与约定

新母图 `source-art/ui-kit.png` 原生1254×1254 RGBA。从其确定性裁切出主窗、标题、两小按钮和六个状态按钮。六状态均在416×128透明画布居中，保留裁片原像素，没有放大增加细节。六按钮定义为玉绿普通/按下/浅玉选中、米白普通/按下、灰色禁用；色差及同源边框共同表达状态，后续应配文字/图标辅助。

主窗 Border 为 `[112,116,112,90]`（顺序 Left,Bottom,Right,Top），六按钮 `[84,34,84,34]`；标题保持整体比例不九切。按钮需要高度小于68时优先整体等比缩小或使用 compact，避免缩到九切边距总和以下。

复用16件 F 盘小控件：输入、普通/选中纸卡、下拉、关闭、加减、提示、纸纹、滑杆三件、复选框两态和在线/离线圆点。每件按字节复制，保留历史来源记录；本任务当前模型配置不回填历史型号。`reference-paper.png` 的 RGBA Alpha 全255，属于不透明纹理，其余所需透明件有真实Alpha。

正式26件路径、大小、Alpha最小/最大、SHA、九切、状态家族和源路径均在 `docs/asset-common-manifest.json`。`tools/extract_common_assets.py` 是本地无AI可重建入口。`records/reference-evidence/` 保存原manifest、README与可得的同名来源记录，便于移机查询。

Unity建议：Sprite Single、Full Rect、Clamp、Bilinear、关闭mipmap、Alpha Is Transparency；控件默认Pivot中心，九切顺序按清单。这里只做离线图片检查，未在Unity验证。

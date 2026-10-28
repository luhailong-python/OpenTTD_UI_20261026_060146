# 美术参考素材关联记录

本文件是本对话项目关联的权威记录。2026-10-26，按用户要求将误写在 `F:\work\image` 素材 README 中的本项目关联记录迁回本项目；之后F盘完全只读。素材来源、实际使用位置、哈希及生成证据按原记录保留。成果GitHub、账号和提交要求待用户提供，没有执行提交、推送或发布。

## 世界、车辆与效果的新增使用关联

- 项目：云途万里（暂名）· OpenTTD 道家Q版完整游戏美术；本对话目录`E:/work/image/OpenTTD_UI_20261026_060146`。
- 功能参考：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，固定提交`cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`；不是成果提交仓库。
- 美术参考仓库：`F:/work/image`。实际使用相对路径仍为`designs/mail-ui-v1/01-mail-event.png`和`designs/team-ui-v2/team-ui-v2.png`；关联类型为风格参考。
- 使用位置：`source-art/world/`下地形、水、道路、轨道、房屋、产业、植被、设施、效果和灾难母图，以及`assets/world/vehicles/families/*/atlas.png`的27个载具家族。使用玉绿/青绿、象牙纸绢色、暖金细节、圆润Q版和细腻手绘方向，没有把UI窗口、旧文字或旧业务画入世界地块。
- 本项目`assets/world-viewport.png`作为附加环境/投影参考；朝向引导图等是有记录的几何说明，不冒称AI手绘。各次实际图片输入与哈希以对应`*.generation.json`为准，完整记录列表见`../records/full-game-art-audit.json`。
- 独立控件、地物和车辆的裁切、投影、调色、拼装、施工状态、静态朝向及二维动画按各自manifest追溯源图。共享母型不冒称每个源ID拥有独立原生绘画。
- 核实日期：2026-10-26（America/New_York）。本条仅记录本地素材关联；用户美术审阅、世界最终覆盖复核和下一阶段Unity运行验收分别记录。没有向F盘写入本段。

## 早期UI关联迁移原文

每节注明迁移前的 README 位置；原文中的“本目录”“本参考仓库”按该来源路径理解，本项目资源与证据的相对路径以本项目根目录为准。核实日期与阶段描述为原记录的时间状态。

---

原记录位置：[designs/attribute-panels/README.md](F:/work/image/designs/attribute-panels/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/attribute-panels/v2-painted/unity-slices/png/`；修正版滑杆另来自 `designs/attribute-panels/exact-20261022/staged/Assets/Resources/UI/Ugui/AttributeExact20261022/`。
- 关联类型：**直接复用**。从前者逐字节复制10件无动态文字控件：`stat_field`、`pet_card_normal`、`pet_card_selected`、`dropdown_arrow`、`close_button`、`slider_thumb`、`step_plus`、`step_minus`、`notice_icon`、`paper_tile`。从后者复制 `slider_track.png`、`slider_fill.png`，均128×21，采用完整实心厚度修正版。
- 本项目实际使用位置：`assets/common/reference-*.png`，用于经营目录、列表、输入、选择、设置及数量/配置控件；并列入正式资源预览与Unity导入规范。没有转用角色/宠物业务或示例数值。
- 12件准确改名映射、原尺寸、SHA、Alpha、九宫格和状态家族见本项目 `docs/asset-common-manifest.json`；历史来源证据在 `records/reference-evidence/`。当前配置未回填旧素材型号；修正版滑杆原裁切/端帽镜像来源保留，未声称新生成细节。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/equipment-ui-20261008/README.md](F:/work/image/designs/equipment-ui-20261008/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/equipment-ui-20261008/sprites/checkbox_off.png`、`checkbox_on.png`。
- 关联类型：**直接复用**。两态98×98真实RGBA透明图逐字节复制，未再次生成、裁切、放大或重采样。
- 本项目实际使用位置：`assets/common/reference-checkbox-off.png`、`reference-checkbox-on.png`，用于设置项、目录筛选与控件状态预览，并列入Unity导入规范。没有复制装备详情卡、装备图标、角色属性或测试数值。
- 来源/SHA/Alpha与固定比例约定见本项目 `docs/asset-common-manifest.json`、同名派生记录与 `records/reference-evidence/`。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/gameplay-ui/README.md](F:/work/image/designs/gameplay-ui/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/gameplay-ui/02-inventory.png`，并读取本目录现存README及最新采用记录。
- 关联类型：**同功能信息层级参考**。已实际查看背包整屏，研究分类/目录、列表与详情及底部主次操作层级；该研究已用于本项目车辆/货物目录的布局设计。
- 本项目实际使用位置：`designs/` 中车辆购买/车队/货物相关整屏与 `docs/` 功能、布局记录。没有复制该整屏为运行时底图，没有沿用旧游戏名称、装备图标、MMORPG业务或演示数值；主控件来自本项目新kit及已登记的小控件。
- 实读与实看依据见本项目 `docs/ART_REFERENCE_AUDIT.md`、`docs/art-references.json`。此整屏属于布局研究，不列为真实生成输入或直接复用资源。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/mail-ui-v1/README.md](F:/work/image/designs/mail-ui-v1/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/mail-ui-v1/01-mail-event.png`。
- 关联类型：**风格参考**。已实际查看当前 PNG 原图，并在本项目7次内置生成中作为真实图片输入；承接玉绿、象牙纸面、暖金云纹、圆润框板和局部红穗，不移用邮件业务、旧游戏名称或测试数据。
- 本项目实际使用位置：新 `source-art/ui-kit.png`、`source-art/system-icons.png`、`source-art/cargo-icons.png`、`source-art/managers.png`、`source-art/helicopter.png`，以及 `assets/transport-valley.png`、`assets/world-viewport.png` 的风格输入；正式界面与独立裁片位于 `designs/`、`assets/`。邮件整屏未作为运输游戏窗口底图直接复用。
- 来源核验：新项目 `docs/art-references.json` 与上述7张图的同名 `.generation.json` 均保存实际输入路径/哈希、提示词、配置目标与实际返回证据；工具未披露的具体型号/质量仍为未确认。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/social-ui-v1/README.md](F:/work/image/designs/social-ui-v1/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/social-ui-v1/02-world.png`，并读取本目录README、UI_SPEC与现存状态说明。
- 关联类型：**同功能信息层级参考**。已实际查看世界聊天原图，研究消息区、固定输入区与滚动层级；用于本项目OpenTTD多人联机聊天/通知的设计。
- 本项目实际使用位置：`designs/` 多人聊天/联机相关整屏与 `docs/` 联机流程、布局记录。没有复制原整屏为运行时底图，没有机械加入好友、帮派、邮件业务或照搬旧聊天内容；新主控件、图标与字体为本项目实际采用资源。
- 实读与实看依据见本项目 `docs/ART_REFERENCE_AUDIT.md`、`docs/art-references.json`。此整屏属于布局研究，不列为真实生成输入或直接复用资源。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/team-ui-v2/README.md](F:/work/image/designs/team-ui-v2/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/team-ui-v2/team-ui-v2.png`、`designs/team-ui-v2/unity-slices/png/status_online.png`、`status_offline.png`。
- 关联类型：**风格参考、直接复用**。已实际查看原图，并在本项目7次内置生成中作为真实图片输入；承接玉绿金边、米白纸卡、留白与Q版画法。旧组队名单、申请流程和测试数据未移入运输经营业务。
- 本项目实际使用位置：新 UI 母图、系统/货物图标、经理头像、直升机及两张运输场景的风格输入；七份同名 `.generation.json` 可查实际输入。两枚状态圆点逐字节复制为 `assets/common/reference-status-online.png`、`reference-status-offline.png`，供经营/网络目录状态提示及控件预览使用。
- 两件复用保持原尺寸、真实Alpha和固定比例，来源/SHA见本项目 `docs/asset-common-manifest.json`。主框、标题和按钮采用新 `source-art/ui-kit.png` 裁片；本目录旧 `main_frame.png`、`title_plate.png` 未采用。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

---

原记录位置：[designs/world-map-original-20260925/README.md](F:/work/image/designs/world-map-original-20260925/README.md)

<!-- project-association:openttd-ui-20261026-060146:begin -->
### 云途万里（暂名）· OpenTTD 道家 Q 版运输经营 UI（2026-10-26）

- 项目或任务名称：**云途万里（暂名）**；正式名称待用户指定。
- 功能参考 GitHub：[OpenTTD/OpenTTD](https://github.com/OpenTTD/OpenTTD.git)，仅研究功能、玩法和流程。成果 GitHub：**待用户提供**；两个仓库分别管理。
- 美术参考仓库：`F:/work/image`。本对话制作目录：`E:/work/image/OpenTTD_UI_20261026_060146`。
- 参考素材仓库相对路径：`designs/world-map-original-20260925/world-map-original.png`，并读取原生/重采样及当前采用说明。
- 关联类型：**风格与同功能信息层级参考**。已实际查看原图，研究明亮地形、圆润建筑、地点展示和地图信息可读性；用于本项目经营地图/小地图的展示研究。
- 本项目实际使用位置：新运输场景与 `designs/` 地图相关整屏的视觉研究、`docs/` 地图布局说明。新场景为本项目另行生成；没有直接复制这张地图、其18处旧地名、传送业务或既有地图数据。
- 实读与实看依据见本项目 `docs/ART_REFERENCE_AUDIT.md`、`docs/art-references.json`。此整屏属于研究参考，不列为新图真实生成输入或直接复用资源。
- 核实日期：2026-10-26（America/New_York）。本条仅确认本项目实际使用关联；当前阶段为本地美术设计与资源验收，Unity 导入、Prefab、业务逻辑和运行验证留待下一阶段。没有执行 Git 提交、推送或发布，没有操作本参考仓库共享 HEAD、index 或 refs。
<!-- project-association:openttd-ui-20261026-060146:end -->

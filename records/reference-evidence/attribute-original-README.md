# 人物、宝宝属性界面 · 切图包 v10

更新：2026-09-11。当前 31 张 PNG 依据全项目指定选角风格重新制作：25 张新 UI 皮肤／控件、4 张宠物头像重裁，2 张干净的独立书法标题保留原像素。遵守深玉绿、象牙米白、细暖金、道家 Q 版及少量春节／元宵／中秋点缀；其他游戏截图只提供功能布局。完整原画和复现流程见 [v10](../../../../qdao_ui_style_recut_v10/README.md)。

2026-09-11 已通过官方 Unity relay MCP 将 31 张 v10 切图同步到客户端，保留原 GUID，并核验资源加载、哈希、尺寸和九宫格边距。真实人物／宝宝面板在 2560×1080、1920×1080 下共 10 张编辑器截图通过验收，相关测试 26 项通过。截图使用离线样例数据，不代表在线服务器验收。见 [v10 引擎报告](unity-validation-v10.json)、[导入报告](unity-import-v10.json) 和 [验收记录](unity-review-v10/qa-checks.txt)。原有 `unity-validation.json`、`unity-sprite-preview.png` 仅记录 2026-09-09 旧版。

- [当前切片总览](sprite-overview.png)
- [文件、边距与资源路径清单](manifest.json) · [文件核验](file-validation.json)
- [九宫格检查](nine-slice-review.png) · [固定符号与标题](fixed-glyph-title-review.png)
- [人物组合检查](character-layout-review.png) · [宝宝组合检查](pet-layout-review.png)
- [本次属性／组合视觉验收](../../../../qdao_ui_style_recut_v10/staged/attribute-composite-visual-qa.json)

## 内容

| 用途 | 资源 |
|---|---|
| 主窗 | `window_frame`、`paper_tile`、`divider` |
| 标题 | `title_plate`、`title_character`、`title_pet` |
| 按钮 | `button_primary`、`button_secondary`、`button_scheme`、`dropdown_arrow` |
| 页签与小标题 | `tab_horizontal`、`tab_vertical_normal`、`tab_vertical_selected`、`section_header` |
| 关闭 | `close_button`、`close_tassel` |
| 加点与数值 | `step_minus`、`step_plus`、`step_plate`、`stat_field`、`notice_icon` |
| 滑杆 | `slider_track`、`slider_fill`、`slider_thumb` |
| 宝宝列表 | `pet_card_normal`、`pet_card_selected`、`portrait_frame`、四张 `portrait_*` |

所有按钮底板、页签、数值框和列表卡均不带动态文字。两个固定书法标题单独提取为透明图片，可按需使用，也可以用 TMP 绘制标题。±、×、叹号和下拉箭头属于固定图标。

## 来源与透明度

当前 UI 使用 v10 六组内置 GPT Image 2 原画的透明裁片；源图、真实原生尺寸、固定边距和逐件映射见 [v10 记录](../../../../qdao_ui_style_recut_v10/README.md)与 [属性来源映射](../../../../qdao_ui_style_recut_v10/source-map.attributes.json)。生成工具未开放质量参数，不宣称显式强制 high，也不要求 API 密钥。

四只宠物沿用已确认的独立透明素材重新裁出 160×160 头像，避免把截图中的示例等级带入运行时。两个独立书法标题继续使用干净原图；它们不是本次重新生成。上级两张含字效果稿和 `sources/` 保留为历史快照，不作为当前皮肤重建源。

`paper_tile` 为有意保留的不透明纸面纹理；其余控件按清单保留所需 Alpha、原画布及边距。24 个新制非平铺 UI 件设置 1 像素透明外缘；头像与独立纯文字按各自合同处理。透明 PNG 中的纸面本体可以不透明，不应当作覆盖式透明框使用。

## 客户端接入合同

既有目标目录为 `E:/work/mmorpg-client/Assets/Resources/UI/Ugui/AttributesPaintedV2/`，资源键仍是 `UI/Ugui/AttributesPaintedV2/<name>`。31 张 PNG 和 manifest 已同步，暂存区、美术正式目录、客户端三方哈希一致。

接入时按当前 `manifest.json` 核对 31 个文件和哈希，沿用原名称、画布及 `borderLeftBottomRightTop`。可伸缩底板采用 Sliced；标题、头像与圆形图标保持比例。文字、真实属性值、等级、名称、状态和点击事件由原生控件实现；“相性点”继续移除。

已有导入合同为 Sprite Single、Full Rect、Clamp、Bilinear、无压缩、关闭 mipmap、Alpha Is Transparency、最大纹理尺寸 4096。这些导入设置已在官方 MCP 中核验，并保存了针对当前哈希的 v10 报告。人物滑杆同时修正了纵向拉伸锚点导致点击区域变高的问题，真实控件区域保持 60×60。

## 重建与历史脚本

在仓库根按 [v10 确定性重建步骤](../../../../qdao_ui_style_recut_v10/README.md#确定性重建)执行。属性构建入口为 `python qdao_ui_style_recut_v10/tools/build_attributes.py`，输出到 v10 暂存区；本次属性 31 件经逐文件哈希门禁后，由 `tools/ImportAttributesV10.cs` 通过官方 Unity MCP 发布到正式美术目录和客户端。

`tools/SliceAttributeArtwork.cs` 是旧版 Unity 原图裁切脚本，原逻辑会同时覆盖美术仓库和客户端为旧皮肤，现已阻止执行并提示使用 v10。代码保留供历史追溯。`tools/VerifyAttributeSlices.cs` 是旧版引擎验证脚本，重用前须核对其输入和检查项适用于当前清单；不能直接沿用旧报告。

本目录 `*-review.png` 为离线美术组合检查；`unity-review-v10/` 为本次真实 Unity UGUI 面板截图及测试记录。上级 HTML 和旧静态效果稿仍为历史参考。当前服务端宝宝 1002（石灵）、1003（金猊）缺少已确认的对应头像，继续使用中性徽记；葫团团与符小虎切片已导入，未错误绑定到这两个模型。

## 当前 Unity 面板预览

- [人物属性](unity-review-v10/01-character-normal_2560x1080.png)
- [宝宝属性](unity-review-v10/03-pets-normal_2560x1080.png)
- [人物扩展列表底部](unity-review-v10/02-character-eight-rows-bottom_1920x1080.png)
- [宝宝十项列表底部](unity-review-v10/05-pets-ten-bottom_1920x1080.png)

`tools/ImportAttributesV10.cs` 保存本次官方 MCP 执行的导入命令，可审计其哈希门禁与备份行为；它使用本工作区的明确路径，仅用于这 31 张属性资源。

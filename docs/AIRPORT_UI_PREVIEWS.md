# 机场建造窗口九缩略图

`AIRPORT_UI_BINDINGS.json`补齐固定源码9个`SPR_AIRPORT_PREVIEW_*`符号与当前实际图片的显式绑定。机场世界模块没有重画、复制或修改；新增正式PNG为0。九张复用输入仍在`previews/world/airports/*-layout.png`，已作为建造窗口缩略图的正式依赖引用，原始字节、来源记录和SHA不变。

| 源符号后缀 | 原机场 | 复用PNG |
|---|---|---|
| SMALL | country | country-layout.png |
| LARGE | city | city-layout.png |
| HELIPORT | heliport | heliport-layout.png |
| METROPOLITAN | metropolitan | metropolitan-layout.png |
| INTERNATIONAL | international | international-layout.png |
| COMMUTER | commuter | commuter-layout.png |
| HELIDEPOT | helidepot | helidepot-layout.png |
| INTERCONTINENTAL | intercontinental | intercontinental-layout.png |
| HELISTATION | helistation | helistation-layout.png |

源码依据为`sprites.h:274–282`、`airport_defaults.h:368–376`、`airport_gui.cpp:410–412,490`。`GetCustomAirportSprite`在`newgrf_airport.cpp:261`解析自定义Sprite，没有自定义结果时采用该AirportSpec的preview。此包覆盖九种内置机场；任意外部NewGRF的自带美术仍属于对应内容包。

Oilrig的源AirportSpec为preview=0、buildable=false，因此没有加入九个建造预览。油井世界布局仍保留原有用途，不因这项UI绑定新增第十种可建机场。

每张图保留各自原始画布、Alpha与占地数据。UI显示统一使用384×256区域、居中contain、保留宽高比；建议Sprite/Single、Full Rect、Bilinear、无Mip Maps、Clamp、中心Pivot、Border Left/Bottom/Right/Top为0。选中/禁用由现有列表行或按钮状态承接，保持缩略图位置；动态名称、占地、价格、可用年份与提示文字独立排版。预览按当前绘画配色复用；公司标识可另放已有16色旗，不把整张布局统一染色。实际公司调色与目标平台导入待Unity验证。

`previews/airport-ui/index.html`实际引用九图并支持在同一预览区切换；`nine-build-preview-bindings.jpg`只是等比缩小后的九图联系表，不是新机场原画或新原生高清资产。专项检查保存源符号、AirportSpec对应、文件/源依赖SHA、真实Alpha、尺寸与可建状态；用户批准和Unity运行仍分别为pending/false。

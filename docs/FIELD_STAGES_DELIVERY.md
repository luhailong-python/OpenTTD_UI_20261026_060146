# 农田9阶段与19坡

原16张UV位移/色调图不能表示农田生长。本次以源码有效阶段0..8建立专用绑定；`_clear_land_sprites_farmland[16]` 只有9个初始化Sprite，16是存储容量。`clear_cmd.cpp:338–340` 明确从0循环到8后归0。初建农田的随机字节选择0..8的初始生长阶段，并不是16种随机外观。

| 阶段 | 当前明确外观 |
|---|---|
| 0 | 无植株的已耕土垄 |
| 1 | 稀疏发芽 |
| 2 | 幼苗 |
| 3 | 较大叶片幼苗 |
| 4 | 青绿小麦丛，矮且疏 |
| 5 | 茂盛青绿麦丛 |
| 6 | 青绿与金黄交错，进入成熟 |
| 7 | 成片金黄成熟麦丛 |
| 8 | 收割后土垄与绑绳方形干草捆 |

正式分包 `assets/world/terrain/field-stages/manifest.json` 提供171条9阶段×19坡绑定、346张正式PNG：19张共用坡土、171张whole、152张植物/草捆overlay、4张可复用原生裁片。阶段0无overlay，不输出空白PNG。旧主terrain PNG均未修改；旧16 UV图保留其派生记录，只作历史装饰变体，不再作为`field_type`绑定。

各状态画布统一256×256，锚点 `[128,160]`，一级高差32像素。soil只作原生土壤投影；幼苗、青麦、金麦和草捆在真实坡面高度的根部竖直放置，不将整片麦田随坡拉扁。选择whole或ground＋overlay之一，不重复绘制。

生产期间对原主terrain清单和1064张PNG作了前后SHA比较，结果保留在`productionNoOtherWrites`历史证明中；它只证明当次生产没有改这些图，不是农田的永久依赖。其它制作者之后修正无关雪/沙密度，不会令农田失效。持续有效性只核实际`derivedFrom`来源，包含fieldflat土垄、幼苗原图、新麦丛母图和本包组件。

幼苗从既有`field-seedlings.png`裁出；土垄取既有field原画中不含绿植的干净条带，明确2×4重复，不画新泥土。青绿麦、金黄麦及方形草捆取自本轮原生工具生成的`field-crop-components-native.png`（2172×724）。该母图保留完整提示词、mail/team及成熟麦田参考SHA、调用时间和参数；实际model/quality未披露，仍为null。3个大原生部件分别提取后缩小、重复布置，不声称346幅原画。

新母图的孤立低Alpha彩色点经过真实Alpha检查：保留最大连通主体及2像素软边，去掉Alpha低于4的污染点，Alpha0处RGB归零，并给正式裁片4像素透明边。操作和移除像素数逐件保存在derivation记录；没有重绘植株。干净原生裁片已在暖色/深色底检查。

已实际查看9阶段总览和全部9张19坡页面，共171状态；成熟麦与收获草捆区别清楚，植株不随坡倾斜，未见裁头或悬空的大段根脚。独立专项核对源码9有效阶段、根部高度、四角投影、精灵不放大/不裁切及实际overlay/whole重组。用户美术批准、Unity多格遮挡与真实生长计时仍待后续。

源码积雪路径先绘已有snow地面后直接return，不应额外叠雪下麦丛；农场解除关联且阶段>=7时转为已有Grass density2。这两条保留为资源选择合同，不额外制造不存在的生长阶段。

- [实际预览](../previews/world/field-stages/index.html)
- [9阶段总览](../previews/world/field-stages/nine-stage-overview.jpg)
- [正式清单](../assets/world/terrain/field-stages/manifest.json)
- [专项检查](../records/world-production/field-stages-validation.json)
- [实际视觉记录](../records/world-production/field-stages-visual-review.json)

重建：`tools/build_field_stages.py` → `tools/validate_field_stages.py`，源裁片配置在 `config/field-stages-native.json`。新图或参数改变后必须重新查看对应页面，不能把脚本通过当成用户批准。

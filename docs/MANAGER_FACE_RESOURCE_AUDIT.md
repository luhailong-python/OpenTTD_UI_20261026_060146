# 经理参数化头像：源码、资源与本地复核

本次核实基于OpenTTD提交`cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`。实际阅读`src/table/company_face.h`全部4表、`company_manager_face.h`的取值/激活逻辑、`company_gui.cpp:1128–1517`的绘制/高级界面和`company_cmd.cpp:1417–1585`的style/facecode处理；实际查看本项目58整屏、8人原生图集与独立头像，读取58 catalog、布局和applied状态。

原8张`assets/portraits/manager-01..08.png`仍是完整烘焙胸像，只证明8个预设选项；它们没有被冒充为可替换五官。新增正式分包`assets/portraits/customization/manifest.json`现有316个注册资源（包括所有权掩码及声明的肤色/眼色派生）、235条源码值/状态绑定、228个实际分层组合样本和10张1920×1080高级/facecode状态图。213个Sprite值槽逐一出现在4样式共16张组合联系图中；这些槽共享已记录的母件，不是213幅独立原画。

本次接续复核实际查看8张母图、23张部件/组合联系图和10张状态图，修正了载入/保存/错误码文字输入框误带下拉箭头的问题；保留手绘框及原头像像素。当前本地观察为五官、发际、下颌、衣领及配饰组合没有发现需阻止交付的错位、双重烘焙或裁断；三眼色与长错误码可辨认。逐图SHA与观察保存在[视觉复核记录](../records/manager-customization-visual-review.json)。检查覆盖已展示组合，不穷举所有参数的笛卡尔积，也不代表用户已批准或Unity已验证。

## 上游真实字段

4表源标签依次为`default/face1..4`，源码注释为两组masculine/feminine样式；这里不推断或自行给样式添加族群名称。

| Sprite字段 | face1 | face2 | face3 | face4 |
|---|---:|---:|---:|---:|
| 固定底层值槽 | 1 | 2 | 1 | 1 |
| 下巴可选值 | 4 | 固定层，无可调字段 | 2 | 2 |
| 眉眼（含眼部） | 12 | 16 | 11 | 16 |
| 胡须 | 3 | 不适用 | 3 | 不适用 |
| 嘴唇 | 12 | 10 | 9 | 9 |
| 鼻 | 8 | 4 | 4 | 5 |
| 头发 | 9 | 5 | 5 | 5 |
| 衣领 | 4 | 4 | 4 | 4 |
| 外衣 | 3 | 3 | 3 | 3 |
| 领饰/系带 | 6 | 不适用 | 6 | 不适用 |
| 耳饰 | 不适用 | 3 | 不适用 | 3 |
| 眼镜 | 2 | 2 | 2 | 2 |
| **Sprite值槽合计** | **64** | **49** | **50** | **50** |

总计213个style/字段/值Sprite槽，因源图跨字段/样式共享，去重为184个source SpriteID；这不是要求生成213或184幅新原画。另有8个Toggle字段×2状态=16条控制关系、2个Palette字段×3眼色=6条配色关系，共235条可核实值/状态绑定。完整机器清单见[MANAGER_FACE_REQUIREMENTS.json](MANAGER_FACE_REQUIREMENTS.json)。

face1/3的胡须开关为0时隐藏胡须；为1时隐藏嘴唇**和鼻子**，不是仅在原嘴上再贴一层胡须。face2/4耳饰关闭时隐藏耳饰。全部样式有眼镜开关。前两个样式才有brown/blue/green眼色Palette，作用于该样式眉眼层。Sprite按表中次序合成，UI按`position`排序；不能把绘制顺序和设置列表顺序混为一谈。

facecode是`default/faceN:masked_bits`，支持旧数字码样式位，载入会规范合法取值/清除不活动bits。美术阶段交付相应有效/无效码、载入/保存成功和取消保留原图的预览及说明；解析执行与配置保存接入留下一阶段。

## 已落实的资源合同

1. 建立4个真正干净的统一角度头部/肩颈基底。每族统一512×512透明画布、明确眼线/鼻/嘴/发根/衣领基准和固定锚点；无五官/头发/眼镜/胡须的覆盖区域，保持原样式身份，不从8人完整图生硬互换五官。
2. 真正分离的眉眼、鼻、嘴、下巴、头发、胡须、眼镜、衣领、外衣、领饰和耳饰母件。部分原画可共享；几何/换色衍生需逐件记录，建立全部213个Sprite值槽绑定。每个参数变化要产生对应部位的选择，不能随机换整张预设脸充当参数响应。
3. 给眼色建立独立虹膜所有权/颜色规则，避免连皮肤、眉毛和衣服整体换色。关闭配饰采用隐藏层规则，不生成全透明PNG凑数。衣领/外衣/系带提供明确遮挡顺序与干净接缝。
4. 至少提供高级设置、胡须开后隐藏鼻嘴、眼镜关闭、耳饰关闭、3眼色对照、facecode载入/保存/非法码、取消还原等实际排版预览；可使用既有通用面板/按钮，附原图/逐层与最终合成对照。
5. 每个可选值出现在至少一张组合检查表中；覆盖4样式、切换后的不兼容字段隐藏、眼色作用区、长代码和错误提示。组合数量不是原画数量，UI预览不是Unity运行。

## 当前机器交付合同

使用`docs/MANAGER_FACE_ART_MANIFEST.json`或`assets/portraits/customization/manifest.json`集中记录：`assets[]`按现有Sprite合同列id/image/canvas/anchorPx/SHA/来源；`bindings[]`按上述requirements的requirementId绑定。

- Sprite绑定有实际`assetIds`和对应`sourceSpriteId`，记录源var/value与派生方法，可声明跨style共享；同画布/定位，禁止将完整preset伪装成眉眼小件。
- Toggle绑定写精确`hiddenSourceVarIndices`；Palette绑定写`affectedSourceVarIndices`与`paletteRule`、实际虹膜掩码及3色，避免整体换色。
- `compositionSamples[]`记录真实所选参数、层序、逐层PNG与最终合成图；`previewStates[]`记录id/image，建议id为`advanced,moustache-on,glasses-off,earring-off,eye-colours,facecode-load,facecode-save,facecode-invalid,cancel-restores-original`。

独立工具`tools/audit_manager_faces.py`重读源码表，输出[源码绑定审计](../records/manager-customization-audit.json)，现为235/235且无绑定缺口。`tools/validate_manager_customization.py`复算实际层序、RGBA组合、Alpha、来源SHA、虹膜作用区、213值槽样本、取消还原和10状态图；[机械验证](../records/manager-customization-validation.json)明确只给机械结果，不能自动批准美术。高级图册另有[浏览器验证](../records/manager-gallery-browser-validation.json)，检查10张状态和23页组合的图片/链接、桌面/移动溢出及脚本错误。

复跑机械验证用`C:/Python314/python.exe tools/validate_manager_customization.py`；生产提取中需要的SciPy现只在实际提取/图像形态函数中按需导入，复核已有正式资源不依赖SciPy。若要重新从母图生产，仍需相应生产依赖，不能把这项按需导入修改当作重新生成或原画验收。

本地视觉结论与机器验证分开绑定当前manifest SHA；文件变化后应重新检查受影响部分。原UI4279项检查或235绑定审计本身都不能替代经理分包实际美术复核。原8张preset、母图和已合格正式部件均保留。

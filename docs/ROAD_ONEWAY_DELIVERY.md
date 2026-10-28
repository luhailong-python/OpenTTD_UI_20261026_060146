# 道路单行与双向禁行地面标记

这是此前铁路单行信号之外的独立道路漏项。固定OpenTTD提交中，`sprites.h:325–328`定义`SPR_ONEWAY_BASE=6105`及18个Sprite槽；`road_cmd.cpp:1650–1664`先绘路面，再按限制态在地块内部(8,8)绘标记，之后才绘道路施工、架空线和路边细节。

槽号公式为`坡组(0/6/12)+(X轴0/Y轴3)+drd(1/2/3)-1`。N组由NE/NW坡触发，S组由SE/SW坡触发。所有地基先修改`ti.tileh`，再选择标记；因此不能把原始地形坡码直接当作标记坡码。`ROAD_ONEWAY_BINDINGS.json`保存18个正式槽及19原始坡形×两轴×3限制态的114个地基转换绑定，包含原地形、地基模式、修正后坡码、高度增量和资源路径。

方向按`road_cmd.cpp:2168–2175`实际轨道掩码与`track_type.h:63–73`核对，不凭英文枚举名猜屏幕方向：

| drd值 | X轴允许方向 | Y轴允许方向 |
|---|---|---|
| 1 | X_SW（西南） | Y_NW（西北） |
| 2 | X_NE（东北） | Y_SE（东南） |
| 3 | 双向禁止 | 双向禁止 |

drd=0不绘标记。单行仅用于普通直路；X轴连接掩码10、Y轴掩码5，与铁路/有轨信号无关。源基础绘制范围不表示已实现路线合法性或车辆通行逻辑。

正式18张PNG位于`assets/world/overlays/road-oneway/`，清单为其中`manifest.json`。原生图素只复用现有玉绿金边chevron及朱砂金边forbidden，经过裁切、缩小、旋转、UV和坡面投影；独立SVG仅保存方向线段，放在原生箭头后方提高等距投影可读性。没有新模型调用，没有程序绘制手绘替代图案，actualModel/actualQuality继承未知而保持null。

统一画布256×192、地块锚点(128,128)、Pivot(0.5,1/3)、Border Left/Bottom/Right/Top均0。平地中心为(128,128)，四种有效斜面中心为(128,112)：源码GetPartialPixelZ(8,8)=4，对应本美术16像素高度。当前整格叠层已编码这项偏移；按相同地块锚点叠到对应道路PNG，不再额外加一次中心Z。地基导致的整格升高则同时移动路面与标记32/64像素，114绑定已保存。

采用地基时，绘现有地基侧面加对应道路盖面；`foundationWholeAlternative`是整块替代方案，不能与侧面/道路盖面重复绘制。基座自身的画布和锚点读取其原清单。道路标记不改变已有路面或地基PNG。

`previews/road-oneway/index.html`提供五页真实PNG叠层：平/N/S三组全部18槽、雪地全部18槽、沙地全部18槽。每页以256×192实际像素拼装并保存来源SHA，不是新生成场景；18张正式PNG另有Alpha和四种道路背景交集检查。实际逐页图审与专项记录分别为`records/road-oneway-visual-review.json`和`road-oneway-validation.json`。

Unity建议Sprite/Single、Full Rect、Bilinear、无Mip Maps、Clamp、图集Padding至少4px。当前只完成美术资源、数据和离线预览；用户批准、引擎地形适配、道路通行与运行时绘制仍分开验收。

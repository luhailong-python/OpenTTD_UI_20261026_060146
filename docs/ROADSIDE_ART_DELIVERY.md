# 路边街灯与树木装饰

这是现有road-road／road-tram需求中的路边装饰变体补包，不修改原道路、有轨或已验收PNG。源码Roadside枚举值StreetLights=3、Trees=5；`table/road_land.h:109–294`分别使用原Sprite0x57e、0x57f和树0x1212。新清单直接解析原坐标数组与两组16mask索引，保存32源mask绑定和40个平地摆放点。十种有装饰的mask为3、5、6、7、9、10、11、12、13、14；其余mask源表不画道具，包括四向路口15。

正式资源为`assets/world/overlays/roadside/manifest.json`中的6张128×160 RGBA：向左灯、向右灯、复用杨树，各有普通与半透明。灯来自新原生母图`source-art/world/roadside-lamps-native.png`；源图两杆头部镜向、同设计材质。大光晕主要存在于Alpha0隐藏RGB，正式提取丢弃Alpha≤8外围及透明RGB，保留物理灯体原画和柔边，再等比缩至约64px高。树直接复用现有`vegetation/mature/tree-07.png`，缩至80px高，不新增树种原画。

固定接地点(64,144)、Unity Pivot(0.5,0.1)，Border Left/Bottom/Right/Top为0。原Sprite0x57e位于屏幕左侧路肩，灯头朝右；0x57f位于右侧路肩，灯头朝左。光晕没有烘进正式Sprite，浅米和深绿底已实际对照。所有裁切、缩小、Alpha清理和源SHA逐件保存，不把6输出当作6张新原生母图；工具未披露型号/质量保持null。

摆放点按源码每个subcoord_x/subcoord_y投影，不按对称印象重新排列。检查画布512×384，地块锚点(256,256)，已有256×192道路PNG放在(128,128)。接地点使用`x=256+(sourceY-sourceX)*8`、`y=192+(sourceX+sourceY)*4-sourceZ*4`。`DrawRoadDetail`在每个实际点调用GetSlopePixelZ；本包对地基修改后的平/NE/SE/SW/NW面保留源码整数高度取整，保存160组定位。世界基础高度、地基升高和引擎深度排序读取原世界合同，不能把截图当Unity遮挡验证。

源码绘制先判断条件，再提交独立2×2×16世界包围盒；不能把道具静态烘焙到所有路面里：

- 道路施工分支提前返回；关闭FullDetail或缩放超过Detail不画。
- 有桥时，灯在`bridgeHeight < tileMaxZ+2`时不画，树在`bridgeHeight < tileMaxZ+3`时不画；恰好等于阈值允许画。
- 实际roadBits数量≤1不画。纯tram即使unionMask有两位也不画；混合道路＋tram在roadCount>1时按unionMask选择坐标。
- 树读Trees透明/不可见开关；灯读Houses透明/不可见开关。不可见直接不画；透明使用相同接地点的半透明资源。
- 当前半透明PNG为美术设计Alpha0.35，明确不同于原游戏PALETTE_TO_TRANSPARENT的逐像素实现；精确原调色板适配由下一阶段验证。

预览`previews/roadside/index.html`包含所有十种源mask、四坡摆放、混合路轨及普通/半透明/不可见/低桥/细节关闭/远景/无合格道路/施工状态示例。低桥状态图展示省略装饰的结果，尚未在Unity做真实桥体净空或深度测试。正常道具、位置、透明效果与无装饰路面均由当前实际PNG拼装，整体联系表只等比缩小显示。

验证记录为`records/roadside-validation.json`、`roadside-visual-review.json`和`roadside-browser-validation.json`。Unity建议Sprite/Single、Full Rect、Bilinear、Clamp、无Mip Maps、图集Padding≥4。用户美术批准和引擎运行验证仍分别为pending/false。

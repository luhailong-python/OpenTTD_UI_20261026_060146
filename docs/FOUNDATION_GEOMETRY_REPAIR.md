# 地基半格与陡坡修正

本次修正仅使用已交付的原生手绘石墙和草地材质做确定性几何投影，没有新增原画、放大原生细节或运行 Unity。

源码 `landscape.cpp:GetPartialPixelZ`（240–300行）以 `x>y`、`x+y>=TILE_SIZE`、`x<=y`、`x+y<TILE_SIZE` 分别划分西、南、东、北半格。旧版把 `DrawFoundation` 的8×8排序包围盒当成地面占地，生成了四分之一方格；该理解已撤销。现在每个 HalfTile 顶面是 UV 面积0.5的三角形，另一半沿用当前自然坡面。

`SteepBoth` 现在交付下半高度1、上半高度2的两段平台，保留实际台阶。`orderedPartLayers` 记录同画布、同锚点的前后绘制顺序；这些分层与 `whole` 是替代方案。特殊 Rail 顶面改为源码三角平面，不再用双线性插值扭曲成曲面。

当前分包覆盖14种模式（含 None）、19坡码的266条显式绑定。66种源码有效组合提供140张正式PNG：66 whole、66 sides、8张 SteepBoth 独立半层。None 和不适用组合不绘制，不用透明空图凑数。168张旧清单中源码无效组合已精确退休，原SHA及理由留在 `records/world-production/foundation-geometry-repair.json`。

正式画布仍为512×384，锚点 `[256,224]`，一级高度32像素。自然地面256×192、锚点 `[128,128]` 放到本画布的 `[128,96]` 即可对齐。同一组合选择 whole，或 sides 加对应目标表面，不重复叠画。HalfTile 仍须保留未抬升一半的自然地形。游戏何时选择各模式、邻格遮挡和引擎深度排序留待 Unity 接入。

`tools/build_foundation_geometry.py` 是兼容入口，委托 `tools/foundation_geometry_v2.py`。`tools/validate_foundation_geometry.py` 独立复述源码高度函数，验证70,834个连续平面采样、半格面积、PNG/Alpha/锚点/SHA和两半重组；492项通过、0失败。源码整数像素取整前的连续几何单独说明，非连续边界的上下两个值不混为一个采样。

已实际查看模式总览与66组当前自然坡面拼装的全部三页，未见空洞、四分之一占地残留或重复图集碎片。当前哈希绑定于 `records/world-production/foundation-visual-review.json`。用户审美确认与 Unity 运行仍待后续验收。

- [模式总览](../previews/world/foundation-slopes-contact.jpg)
- [坡面拼装1](../previews/world/foundation-terrain-assembly-1.jpg)
- [坡面拼装2](../previews/world/foundation-terrain-assembly-2.jpg)
- [坡面拼装3](../previews/world/foundation-terrain-assembly-3.jpg)

# 桥口几何复核与来源

本次处理的是现有原生手绘桥跨的像素几何返修，没有调用图像模型，没有程序绘制替代桥面/栏杆，没有提高原生细节。7幅512×512母件位于`assets/world/infrastructure/transport/bridge-{wood,concrete,truss,cantilever,arch,suspension,tubular}-span.png`，母件来源、SHA和原生生成记录保持不变。

旧端点落在桥下立面或桥腿，缩放后实际地板短于逻辑跨距，导致连续放置时出现断缝。`tools/build_transport_runtime.py`的LANDMARKS现在测量终端柱中心所在的地板截面；可见金色柱帽作为第二组对应点，柱下被遮挡的地板接触点依据相邻可见边线推定。具体原图坐标、缩放、目标截面、端柱高度、±32高度转移和镜像均写入每张PNG的projection元数据。

映射保持横坐标单调且只依赖原图横坐标，保留立柱竖直。两端同属截面统一宽度和高度，中间采用原画像素的分段连续映射；上部参考高度按区段插值以避免栏杆鼓曲。RGBA按预乘Alpha双线性采样，Alpha为0的隐藏RGB归零。没有用填色补缝或擦除柱子后另画替代物。端坡使用固定端截面与中间一层高度转移，是明确的二维几何衍生。

平跨的端口为X`[[128,176],[256,240]]`、Y`[[256,176],[128,240]]`，advance分别`[128,64]`、`[-128,64]`。端坡的出端Y为`240-risePx`，advance为`[±128,64-risePx]`。三跨拼接以各片的实际advance累积，而非把端坡继续按平跨64像素向下平移。

`tools/preview_bridge_joins.py --working`仅用于候选几何检查，不改正式runtime。交回生产者重建后，运行不带参数的同一脚本，从实际正式PNG及manifest生成当前验收页`previews/world/bridge-joins-page1..13.jpg`、总览`bridge-joins.jpg`和`records/world-production/bridge-joins-geometry.json`。正式几何报告记录runtime manifest SHA、每页SHA、全部52组拼装/104个接口的端口残差，以及每口中央80%截面123个原尺寸实际Alpha样本。预览放大仅供暴露像素，不计为新高清细节。

13个源码BridgeSpec对应7个绘画结构家族和已声明材质变体，7种部件角色使用重复母跨、两端坡和独立桥墩/悬索塔映射。它们不是13套新原画。接缝检查与局部视觉复核只证明当前图像和几何，Unity深度排序、路轨覆盖、车辆净空与坡地接触仍留待下一阶段。

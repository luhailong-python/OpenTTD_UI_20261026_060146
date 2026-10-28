# 交通静态装配图片合同

权威映射为本目录`manifest.json`的`coverageMappings`与`laneAssemblyContract`，详细说明见[交通美术交付](../../../../docs/TRANSPORT_ART_DELIVERY.md)。全部路径相对本项目根，源记录逐图保存在`.png.derivation.json`。

本目录1245张正式PNG＝1159美术Sprite＋86 mask数据。1034个原有角色图ID保留，另外211个文件提供窄路轨走廊、UV和所有权遮罩；这些不是211幅新原画。不同源码规格对7个原画桥族的复用及材质调色均已标明。

- whole PNG已经包含正确路轨。用whole时不叠加它的分层文件。
- 隧道前视分层按`rear, floor, front`；后视floor为空，保持原画背山。所有层512×512、anchor[256,448]、offset[0,0]。
- 桥按`rear, lane, front`；另置pier。所有层384×384、anchor[192,320]、offset[0,0]。lane已经窄裁并正确投影，不再把完整草地tile放入桥面。
- `mask`、`laneOwnershipMask`与`removedFloorMask`为Alpha数据，不作为可见画件。UV条带也不是可直接放入地图的tile。
- 平跨/端坡几何、接口与源截图保留，见每图projection。动态载具深度、桥下净空、碰撞与Unity实际显示尚待下一阶段验证；当前front保护全部非地板结构，接入时按车辆需要继续分前后结构。

完整静态就位预览：[transport-lanes](../../../../previews/world/transport-lanes/index.html)。用户画面验收、Unity接入和成果远端提交是后续独立步骤。本阶段无Unity工程、C#或Git提交。

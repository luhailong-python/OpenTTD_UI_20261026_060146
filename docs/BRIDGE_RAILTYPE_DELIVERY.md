# 单轨与磁浮桥面补包

本包填补桥面交通制式缺口。源码 `tunnelbridge_cmd.cpp:172–175` 由当前轨制的 `bridge_offset` 选择桥面，桥头和中段分别在1450、1638行应用；`table/railtypes.h` 的普通/电气偏移均为0，单轨16，磁浮24。原有road/rail两类桥面不能代替全部轨制。

正式目录：`assets/world/infrastructure/bridge-railtypes/`。13桥×2轴×4轨制×7角色提供728条绑定，其中单轨与磁浮新增364条。普通和电气显式复用旧rail桥面，不重画相同轨面；电气架线仍是独立已交付模块。原source-ID涂装和七个桥结构绘画家族沿用现有映射。

新增240张正式PNG：84张七家族共享的单轨/磁浮lane层，156张安装后的whole图（13桥×2轴×2新轨制×平/上32/下32）。rear/front、桥墩和悬索塔引用原包；没有复制或覆盖原 `transport-runtime` 图片。7角色中的周期平跨和head别名如实记录，不把重复绑定计为新原画。

材质直接读取现存 `lane-source-monorail.png`、`lane-source-maglev.png` 的原生绘画条带，按原已确认桥口、固定截面、坡面和ownership重投影。单轨采用较窄的中间通道，磁浮保留自身导轨/青光细节；原有屋顶、护栏、桥柱和连接端柱逐像素保持。所有新PNG画布384×384、锚点 `[192,320]`、一级高差32像素。

使用whole或`rear → lane → front`分层之一，lane偏移 `[0,0]`，不能两种重复绘制。既有前后所有权与桥口不在本包改动；车辆净空、架线位置、选择边界、动态深度和源业务路径在Unity阶段验证。

已实际查看原生条带说明图及全部13源桥的页面，每页包含单轨/磁浮、两轴、三平跨和上平下连接。单轨窄导轨与磁浮导槽有可见区别；原结构未见误涂，页面未见透明桥面断口。管式桥内轨面由原有顶棚遮挡，不为展示材质而移除顶棚。

专项1362项通过、0失败；208组真实PNG拼装、416个接口检查包含普通/电气复用状态，13页实际展示新增两种制式的104组拼装。接口检查采样现有端口和实际Alpha，来源1245张旧PNG及其manifest哈希保持不变。此结果是本地静态美术/几何验收，不代表用户审美批准或Unity运行通过。新增原生绘画数为0。

- [独立预览](../previews/world/bridge-railtypes/index.html)
- [正式清单](../assets/world/infrastructure/bridge-railtypes/manifest.json)
- [专项检查](../records/world-production/bridge-railtypes-validation.json)
- [实际视觉记录](../records/world-production/bridge-railtypes-visual-review.json)

重建只运行 `tools/build_bridge_railtypes.py`，随后 `tools/validate_bridge_railtypes.py`。生产脚本仅AST读取原双线性采样函数，直接引用冻结结构层，不调用会写入旧包的生产main。新像素变化后必须重新检查对应视觉页面；技术通过不自动批准新图。

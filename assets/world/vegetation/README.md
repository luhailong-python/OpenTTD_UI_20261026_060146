# 植被正式美术

41个原始TreeType按温带12、亚寒带8、热带12、玩具大陆9完整映射，每个7静态阶段，共287状态；另有13个共享生命周期部件，正式PNG共300张。5张采用的原生atlas共54个独立绘画对象（41末态树＋13共享部件），不把287状态称作287张原生图。模型入口为内置image_gen；未返回实际型号/质量，逐图记null，配置目标保存在各generation.json。

正式画布256×384，根部前接地锚点[128,352]，Unity Pivot建议[0.5,0.08333333]。叶冠中心不等于树根；根部X使用原图不透明接地带估算。所有裁图只等比缩小，无放大；低Alpha噪点小于8/255清零，实心部位Alpha≥240规范为255。热带原画中油棕根部与桃花心叶缘相切，按y362明确分配所有权，不程序补画。各图有旁置derivation.json。

Growing1/2/3按同种末态缩小到28%/50%/76%；Grown用末态；Dying1由同种画件作干枯调色；Dying2/Dead使用明确的气候/家族枯枝、枯桩画件。仙人掌和棕榈有对应枯死原画，棉花糖有自己的凋零枝/桩。非棒棒糖玩具树的Dying2保留原本物种并干枯、压缩，避免枯后长出别种糖果。共享死亡部件与二维压缩都如实记录，不声称独立物种死亡原画。

源码TreeType27专门对应沙漠仙人掌；其图来自热带atlas第11格，因此热带后半段ID故意不是格子顺序。植物学名称是本次美术设计的临时标识；源码只规定数值类型与气候，没有这些真实植物学物种名。manifest保留src/tree_map.h的7态含义与src/table/tree_land.h的4套布局坐标和正式像素偏移。

这是7静态状态资源，不是循环风动或真实植物生长视频。时间、阶段变换与树木数量由下一阶段游戏逻辑处理。建议Sprite/Single、PPU256、Bilinear、Clamp、sRGB、AlphaIsTransparency。图集/遮挡/碰撞/高差/目标机压缩均未在Unity实测。

预览：previews/world/vegetation-temperate.jpg、vegetation-arctic.jpg、vegetation-tropical.jpg、vegetation-toyland.jpg；vegetation-states-1..11.jpg完整展示287状态；tree-lifecycle-special.jpg展示9补充部件。4气候页、11状态页与部件页已逐页实看，records/world-production/vegetation-validation.json记录300资产与41映射检查。

source-art/world/tree-lifecycle-special-with-backdrop.png名称保留历史，但它实际有Alpha0..254；直接查看工具会显示Alpha0下隐藏棕色RGB，真正合成后背景完全透明。previews/world/lifecycle-alpha-composite.jpg保存像素合成核实。一次多余AI修图未采用，任务内候选图片已移除、逐图文字记录保留，没有充作新物种或新细节。

离线重导出工具需要Python、Pillow、NumPy、SciPy。build_vegetation.py重建后运行validate_vegetation.py、record_industry_vegetation_support.py。它们只处理已存在的原画，不会调用收费API，也不包含Unity业务代码。

# 机场美术交付

本地美术制作与内部检查已完成，用户画面验收待确认。未在 Unity 验证，未执行 Git 提交或上传。功能依据为项目内 OpenTTD 源码提交 `cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`，本目录全部输出属于“云途万里（暂名）”。

- 图册：[机场预览](../previews/world/airports/index.html)。
- 正式资源与映射：[airports/manifest.json](../assets/world/infrastructure/airports/manifest.json)。
- 内部检查：[airport-validation.json](../records/world-production/airport-validation.json)，2067 项通过、0 失败。
- 浏览器检查：[airport-browser-validation.json](../records/world-production/airport-browser-validation.json)，9 项通过，无页面错误或失败请求。

## 内容与数量

| 内容 | 数量与位置 |
|---|---|
| 机场原型 | 10 种，9 可建机场及油井共用平台 |
| 原始机场地块 | 74 个 ID，均有独立静态组合 PNG 与可拆模块层 |
| 正式静态模块 | 45 张，包括规范地面、建筑、围栏及共享发射塔 |
| 静态地块组合 | 74 张 |
| 动画帧 | 雷达 12 帧、风旗 8 帧，共 20 张 |
| 正式 Sprite PNG 合计 | 139 张，动画帧已包含在内 |
| 打包帧表 | 2 张另计，合计目录内 141 张 PNG |
| 整机场布局预览 | 10 张另存于 `previews/world/airports/*-layout.png`，保留 265 个源布局坐标 |
| 需求映射 | 86 项＝10 机场＋74 地块＋2 动画 |

新原画来源是 `source-art/world/airport-ground.png`、`airport-props.png` 两张 1536×1024 原生图集，内含 18 个原生对象/地面材料。另直接复用本项目已经绘制的发射塔、地面和油井平台。139 张正式图均为已声明的裁切、缩小、规范投影、纹理重映射或分层组合，不是 139 张独立原生 AI 绘画。原画的旁置生成记录保存实际提交全文、目标配置、参考图哈希与实际返回信息；工具未披露的模型和质量仍为未确认。

## 源码覆盖

实际读取 `src/table/airporttile_ids.h` 的 74 项枚举、`src/table/station_land.h` 的对应地面/建筑/围栏/动画绘制项，以及 `src/table/airport_defaults.h` 的 9 套完整可建机场布局和 10 项 AirportSpec。源文件哈希记录在 manifest 的 `sourceEvidence`。

完整布局包括小机场 4×3、城市 6×6、停机楼 1×1、都会 6×6、国际 7×7、通勤 5×4、直升机专用 2×2、洲际 9×11、直升机小型机场 4×2，以及不可独立建造的油井机场 1×1。油井布局预览周围 3×3 海面仅作环境上下文，不把它算成机场占地。

每个静态地块的 `layers` 列出地面、后围栏、建筑、前围栏的实际图层 ID、偏移和顺序。74 项组合图已用这些真实 PNG 重新拼装，逐字节与交付 PNG 比较一致；多边围栏同时保留各源边。265 项坐标的唯一性、范围、全占地数量、源枚举和资源路径均已核验。

## 尺寸、锚点与后续 Unity 建议

- 地面为 256×128 菱形，像素锚点 `[128,64]`、Unity Pivot `[0.5,0.5]`。
- 建筑、组合地块与动画帧为 512×512，接地锚点 `[256,448]`、Unity Pivot `[0.5,0.125]`。组合地块的逻辑地面中心为 `[256,384]`。
- 同一动画保留固定支撑和固定画布，雷达每帧 100 ms，风旗每帧 120 ms。雷达循环是实际碟面部件的 ±9° 投影扫动；风旗是固定旗口的布料像素变形。全部 20 帧为确定性派生，未声称原生视频或完整 360° 旋转。
- 导入建议 Sprite (2D and UI)、Single；若使用附送 `sheet.png` 则 Multiple、512×512 网格；透明通道保留，Wrap Clamp，Bilinear，Mip Maps 默认关闭。建筑非九宫格资源，Border 为 0/0/0/0。
- 像素比例需与项目公共世界规格统一，不对小幅原画放大充当高清细节。图集需足够透明 padding，Max Size 应避免再次缩小。
- 动态雷达/风旗应替换对应静态建筑层，不要将动画帧覆盖在含初始姿态的整张静态组合图上，以免重影。
- 遮挡、飞机入库/登机桥关系、精确滑行轨迹与碰撞，留待用户美术验收后的 Unity 接入验证。

共享航站楼、行政楼、机库等是本项目功能性改绘，同类源碎片可共享绘画模块；不是对原版每块像素建筑逐一复刻。滑行线采用明确的规范中心连接图，源交通布局与坐标仍保留；不能把浏览器美术拼装检查当成飞机运行联调证明。

## 复验顺序

使用已安装的 sprite-forge Python 依次运行：

1. `tools/build_airport_modules.py`
2. `tools/build_airport_layouts.py`
3. `tools/build_airport_animations.py`
4. `tools/finalize_airports.py`
5. `tools/build_airport_gallery.py`

随后用 Node 运行 `tools/check_airport_gallery.cjs`。这些步骤只读取 F 盘参考资料，全部输出在本 E 盘项目内；不会创建 Unity 工程，也不触碰 Git。

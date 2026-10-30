# Unity 美术导入建议

本文件是下一阶段导入建议，尚未在 Unity 中验证。本阶段没有创建工程、C#、Prefab、场景或运行逻辑。

正式游戏名为《云途万里》，名称与本地 Logo 已获授权纳入美术交付；用户最终审美批准仍待确认。[品牌包](../branding/yuntu-wanli/README.md)提供透明主标和独立图标，8件正式PNG的尺寸、Alpha、Pivot和Border读取[品牌资源参数](asset-branding-manifest.json)，预览见[品牌专页](../previews/branding/index.html)。Logo按等比图像使用，Border为0，不做九宫格拉伸，不替代动态文字层；主菜单、启动和关于页的品牌位置以当前布局合同为准。

## 画布与资源层级

采用桌面横屏基准 **1920×1080**，uGUI `Canvas Scaler → Scale With Screen Size`，参考分辨率 1920×1080，Match Width Or Height 初始建议 0.5。最终支持窗口尺寸、宽高比、安全区、UI缩放和键鼠焦点，应在接入阶段按目标平台验证。世界视窗可等比裁切；窗口及文字区按锚点和约束排布。不得对包含文字的整屏设计图直接拉伸作为可交互窗口。

- `designs/`：界面与状态设计稿，只用于验收、对照及版面核查，不作为运行时 UI 底图。
- `assets/common/`：无动态文字的正式面板、按钮、输入、列表、滑轨和控件状态。来源、尺寸和 Border 读取 `asset-common-manifest.json`。
- `assets/icons/`：36 枚交通经营图标，每枚 256×256 RGBA，源主体原像素裁切后居中补透明；未放大。坐标与源哈希读取 `asset-icons-manifest.json`。它们是 UI 图标，不是可运行的地形瓦片或多方向车辆动画。
- `assets/transport-valley.png`：无字环境插画，实际原生 1672×941。`world-viewport.png` 的处理方法须按其派生记录读取，不能按1920×1080设计稿尺寸宣称新模型原生尺寸。
- `assets/cargo/`：37枚货物/运输缩略图，256×256 RGBA。36枚来自母图原生裁切与透明padding；直升机来自独立母图等比缩小，均未放大。边界与来源见 `asset-cargo-manifest.json`。
- `assets/portraits/`：8枚512×512 RGBA经理头像，原生裁切并统一底线；不包含表情或动作动画。见 `asset-portraits-manifest.json`。
- `source-art/`：当前生产母图及逐图模型证据；UI和图标母图为1254×1254，经理母图为1774×887，两张背景均为1672×941。整屏合成和任何显示适配都属于后处理，不能称为原生1080p／4K生成。
- `assets/fonts/`：正文 Noto Sans SC 与手写标题 Ma Shan Zheng 原字体及各自 OFL；没有打包微软雅黑或其他 Windows 专有字体。
- `branding/yuntu-wanli/`：[主 Logo、独立图标及缩小版](../branding/yuntu-wanli/README.md)。按`docs/asset-branding-manifest.json`和最终`ART_RESOURCE_INDEX.json`读取来源、尺寸和正式使用路径，保持真实 Alpha及等比显示；打包登记不表示已在Unity导入，整合范围见[品牌交付说明](BRAND_INTEGRATION_DELIVERY.md)。

## PNG 导入初值

独立控件采用 Texture Type = `Sprite (2D and UI)`、Sprite Mode = `Single`、Mesh Type = `Full Rect`、Pivot = `(0.5,0.5)`，sRGB 开，Alpha Source 从输入取得，Alpha Is Transparency 开，Wrap = Clamp，Filter = Bilinear，Mip Maps 关，Read/Write 关。Pixels Per Unit 初始统一100；在 UI 中按设计Rect显示，图标保持等比。背景若使用 RawImage 可按普通纹理处理。以上设置需要以最终 Unity 版本的导入器为准。[Unity Sprite 导入设置](https://docs.unity3d.com/6000.0/Documentation/Manual/texture-type-sprite.html)

初验建议禁用有损压缩以比对金边、纸纹和Alpha；平台压缩方式后续按目标机型另验。Sprite Atlas 建议按 `UI_Common` 和 `UI_Icons` 分组，Max Texture Size = **2048**，Padding 初始4px，关闭旋转和紧密打包以便检查九宫格及边缘。图集超过容量时拆分页；不得为凑入一页缩小原文件。大背景独立处理。运行时显存和最终压缩尚未验收。

## 九宫格与状态

`Border` 顺序固定为 **Left、Bottom、Right、Top（像素）**，单位相对于各Sprite原PNG；不是整屏设计稿中的显示尺寸。接入时在 Sprite Editor 输入表中边距，Image Type 选 Sliced。非拉伸图标、标题牌、人物或装饰保持Simple并等比显示。最小拉伸尺寸至少大于左右／上下边距之和，不得压瘪角花。当前参数来自源切片及像素检查，仍待Unity实际拉伸验收。[Unity 9-slicing](https://docs.unity3d.com/6000.0/Documentation/Manual/sprite/9-slice/9-slicing.html)

| 资源 ID | 原 PNG 尺寸 | Border L / B / R / T |
|---|---|---|
| `panel_main` | 1166×687 | 112 / 116 / 112 / 90 |
| `button_compact_primary` | 339×124 | 74 / 32 / 74 / 32 |
| `button_compact_secondary` | 335×123 | 74 / 32 / 74 / 32 |
| `button_primary_normal` | 416×128 | 84 / 34 / 84 / 34 |
| `button_primary_pressed` | 416×128 | 84 / 34 / 84 / 34 |
| `button_primary_selected` | 416×128 | 84 / 34 / 84 / 34 |
| `button_secondary_normal` | 416×128 | 84 / 34 / 84 / 34 |
| `button_secondary_pressed` | 416×128 | 84 / 34 / 84 / 34 |
| `button_disabled` | 416×128 | 84 / 34 / 84 / 34 |
| `reference-input` | 273×62 | 12 / 12 / 12 / 12 |
| `reference-row` | 419×135 | 21 / 21 / 21 / 21 |
| `reference-row-selected` | 419×135 | 21 / 21 / 21 / 21 |
| `reference-paper` | 375×57 | 11 / 11 / 11 / 11 |
| `reference-slider-track` | 128×21 | 11 / 0 / 11 / 0 |
| `reference-slider-fill` | 128×21 | 11 / 0 / 11 / 0 |

图标 Border 全为 0。裁切坐标统一用左上原点的 `cropXYXY = [left, top, right, bottom]`，右／下不包含。Unity若按左下坐标建立Sprite矩形，换算 `y = sourceHeight - bottom`，宽高为 `right-left`、`bottom-top`。本包已经输出独立PNG，不需再次从源图集切36格。

同一按钮状态族使用同画布416×128和相同Border；普通、按下、选中及禁用分别绑定对应状态资源。原始 `button_compact_primary/secondary` 属不同紧凑组件，不把两者不同宽高误当同状态族。锁定可用禁用底图叠独立锁定／条件文字表达，状态与业务判断留在接入层。复用参考控件的历史状态以各自 manifest 为准，不能拿当前配置回填其实际模型版本。

## 文本与字体

经理8张完整preset不能作为参数化换脸层使用。可组合的头基底/眉眼/鼻嘴/下巴/发/胡/衣领/外衣/配饰、眼色所有权和动态隐藏按[经理专项合同](MANAGER_FACE_RESOURCE_AUDIT.md)及最终经理manifest接入。4种source style、213个Sprite值槽、胡须遮蔽鼻嘴/耳饰/眼镜开关、前两style三眼色与facecode界面各自核实；该系统的资源缺口不能通过运行时只随机切换8个preset规避。

动态标题、玩家／公司名称、金额、日期、数量、状态和正文全部独立文字层。预览中排好的字只用于展示效果；正式控件底图不烘焙这些数据。标题采用 `MaShanZheng-Regular.ttf`；正文与数字采用 `NotoSansSC-Variable.ttf`。正文在1920参考画布建议24–28px，表格24px，小提示22px，窗口标题42–54px，按钮26–30px。字号的最终值应以各页布局记录及可读性验收为准。

两份字体从 Google Fonts 官方仓库取得。Noto Sans SC 配 `OFL.txt`，Ma Shan Zheng 配 `MaShanZheng-OFL.txt`，保留版权及许可文件随资源交付；下载地址、日期、SHA见 `records/font-download.json` 和 `records/font-title-download.json`。这是字体文件交付；**TMP Font Asset、字符Atlas、回退链、缺字检查和动态字体策略在下一阶段生成与验证**。当前正文源是可变字体，目标Unity/TMP导入如需静态字重，应从同源合法字体建立静态实例并记录派生，而不能静默替换为系统字体。[TMP Font Assets](https://docs.unity3d.com/Packages/com.unity.textmeshpro@4.0/manual/FontAssets.html)

颜色初值建议：正文深玉绿 `#153D32`，次级文字 `#6A6A50`，米白字 `#FFF4CD`，选中玉绿 `#2D735C`，暖金 `#C89F54`，错误朱砂 `#B43C2C`。运行时状态除颜色外同步提供文字或形状标识。具体主控板式与原画色彩以正式PNG及布局记录为准。[Canvas Scaler](https://docs.unity3d.com/Packages/com.unity.ugui@2.0/manual/script-CanvasScaler.html)

## 下一阶段验收

1. 在用户指定的Unity工程中按manifest导入，核对尺寸、Alpha、中心Pivot、九宫格、Atlas边缘及压缩前后差异。
2. 按设计稿建立原生文字与滚动容器；检查列表、长名称、货币、时间单位、多语种与字形，避免整屏截图片冒充可交互UI。
3. 验证1920×1080及至少一个更窄／更宽窗口下的锚点、裁切、遮罩、文字行高、控件热区、焦点、提示和弹层遮挡。
4. 接入实际OpenTTD型玩法状态及权威业务数据：覆盖范围、可建设性、车辆指令、资金、年代可用性、联机兼容及异常，替换当前离线样例。
5. 按世界资源与车辆清单接入已交付的地图地块、连接组合、机场布局、方向帧和适用动画，逐项验证真实运行。图片已制作、源码ID已有映射、局部拼装检查通过、Unity运行正确是分别记录的状态。

以上为建议与待接入事项，不是Unity运行验收成功证明。

## 世界与载具资源

接续补包的权威入口见 [源码状态返修记录](CONTINUATION_ART_REPAIRS.md)。在原索引之外读取经理 `assets/portraits/customization/manifest.json`、鼠标与小图标 `assets/common/pointers/` 和 `assets/common/micro-ui/manifest.json`。世界聚合会收集 `field-stages`、`rocks-overlay`、`shore-geometry`、`bridge-railtypes`、`road-oneway`、`roadside`、`rail-reservation` 和 `fence-adapter` 等分包；具体路径及当前SHA取根世界清单的 `packSources`，不要在项目接线时只导入旧基础包。

道路单行叠层的坡高已经投影到完整地块画布，按锚点叠放，不能再额外加一次中心Z。路边灯/树遵守各自透明类别、低桥净空、FullDetail、远景和施工抑制规则。PBS灰化只作用于轨段所有权，不灰化绿地或架空线。围栏按源边/源offset及两端角点高度摆放；农田6有效源家族与额外装饰配色分别管理。农田0–8实际阶段读取新状态绑定，旧16个UV/调色变体不能作为生长周期。雪/沙densityStage 0–3对应1/4、1/2、3/4、完整覆盖。

岸线按有效源坡索引选择水/陆/岸分层，水面保持零高水平；flat/EW/NS及保留槽按no-draw规则处理。CoastRocks叠层和岸底必须使用各自画布锚点换算，禁止按Alpha包围盒重新居中。原平面岸条/粗砾纹理不替代新的坡面岸线/独立石块合同。以上仍需Unity实际验证排序、采样、移动接缝和遮挡。

正式索引为 [WORLD_ASSET_MANIFEST.json](WORLD_ASSET_MANIFEST.json)、[WORLD_DELIVERY_COVERAGE.json](WORLD_DELIVERY_COVERAGE.json)、[VEHICLE_RUNTIME_MANIFEST.json](VEHICLE_RUNTIME_MANIFEST.json)、[EFFECT_RUNTIME_MANIFEST.json](EFFECT_RUNTIME_MANIFEST.json) 和 [DISASTER_RUNTIME_MANIFEST.json](DISASTER_RUNTIME_MANIFEST.json)。详细几何合同见 [WORLD_MODULE_SPEC.md](WORLD_MODULE_SPEC.md)，载具差异与导入说明见 [VEHICLE_FX_DELIVERY.md](VEHICLE_FX_DELIVERY.md)。分包manifest和每张派生记录是尺寸、锚点和源图的直接依据；不以整屏UI尺寸推算世界资源。

平地逻辑128×64、正式PNG256×128；合法19坡型采用256×192画布，层高32像素。道路/轨道端口是菱形四边中点。世界坐标每格的屏幕位移为`[(dy-dx)*128,(dx+dy)*64]`。地面中心锚点、建筑前接地点、车辆占地中心和烟雾发射点语义不同，必须读取各资源`anchorPx`、`pivotUnity`或`pivot`及说明；Pivot换算为`[x/width,1-y/height]`。

基础平台另读`assets/world/infrastructure/foundations/manifest.json`，按Foundation的Leveled、InclinedX/Y、SteepLower/Both、HalfTileW/S/E/N和RailW/S/E/N模式选对应表面/支撑侧面；None及不适用组合按映射不绘制，不能用空白PNG凑数。它们是原生石面投影到实际高差的派生几何，不能用普通围栏代替。whole和sides是分层/替代使用关系，具体组合和锚点按对应条目读取，避免重复叠画；运行时何时选择基础模式仍需下一阶段验证。

世界Sprite建议Single、Full Rect、sRGB、输入Alpha、Clamp、Bilinear，初验关闭有损压缩和Mip Map。PPU需与最终世界坐标约定统一；UI建议100不自动等于世界单位。图集建议按地形/交通层、建筑植被、载具、效果分组，保持帧画布与锚点，不旋转裁片；实际图集容量、显存和压缩在接入阶段测量。可拉伸UI控件用九宫格，世界地块与车辆不做九宫格拉伸。

房屋110个源tileID按94个父建筑组织；45幅新风格原生建筑通过位置、材质、施工和多格分片映射，不能在同一实例同时绘制whole与全部子片。产业同样按完整厂区父实例和源占地布局处理，不把每个源gfxID当成另一座完整厂房。当前分片为有记录的Alpha分区，Unity仍需验证深度排序、与后方车辆/地物的遮挡及坡地放置。

桥梁按每一片的`projection.targetDeckMouths`与`advancePx`放置：平跨X为`[128,64]`、Y为`[-128,64]`；一层端坡的Y位移为`64-risePx`，不要固定复制平跨位移。桥身画布384×384、anchor`[192,320]`；独立道路/铁路层、桥墩、悬索塔和前后层按manifest组合，whole与前后层互为替代。13个源码桥型共享7个明确声明的结构母件，不把材质衍生当新原画。当前桥口检验是离线图像拼接，桥上道路净空、车辆遮挡和端坡与地形接触仍需在Unity验证。

水桥8个部件角色的水面`waterSurfaceRisePx=0`，桥头的`headLandSlopeDirection`与独立foundation支持岸坡，不能将水面斜拉。船闸whole与3段×前后层互为替代；开门后的上游孔洞为真实Alpha，后方应由场景自身水/岸绘制，不能把图片查看器显示的透明黑当黑色材质，也不要再用蓝色矩形遮住开口。

车辆256个源型号由27个8向绘画家族衍生。实际body/满载状态、共享密闭车身、轨制部件、footprint锚点和比例由型号manifest读取。车身沿路径的平移由后续游戏逻辑完成；静态朝向不伪称整车运动动画。水面、烟雾、机械件、旋翼、船闸和信号等动画按各帧时长和循环定义接入；插值、二维刚体旋转、投影、平移与原生独立绘画关键帧有明确区别，运行计时仍待验证。

产业8组安装动画（6机械＋2粒子）读取`assets/world/industries/manifest.json`的`animations[].binding`：每组12相位，共96帧；在512×512父坐标中以`attachmentOffsetPx=[0,0]`、scale1叠加cleanBase与当前移动帧，锚点`[256,448]`。替换原静态父图，按`drawParentOriginalSimultaneously=false`避免重复姿态。ownershipMask用于追溯全部改动范围，气泡发生器的removedPoseMask单独移除原有大泡，煤电厂cleanBase保留原父像素。`binding.assemblyPreviewFrames/GIF`展示实际装配，正式`frames`是完整父画布内的移动层，不能把它单独当完整厂区或256小部件播放；工作/停机与源码触发仍需后续业务接入，详见[粒子绑定合同](INDUSTRY_PARTICLE_BINDINGS.md)。

世界清单中仍为在制或待审的条目不自动进入运行验收。下一阶段应把最终550项覆盖表作为接入检查单，核对连接端口、19坡几何、同族画布、Alpha边缘、气候、施工、信号状态、桥头/隧道前后层、机场布局、多格遮挡和动画周期。


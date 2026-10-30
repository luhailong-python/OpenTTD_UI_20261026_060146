# OpenTTD 功能与 UI 实际研究

核验日期：2026-10-26（本任务客户端日期）。功能参考是 `https://github.com/OpenTTD/OpenTTD.git`，本地只读克隆在 `reference/OpenTTD`，固定提交为 `cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`，提交日期 2026-10-25，主题 `Change: Update OpenTTD TTF fonts to v0.9`。本次研究的是该主线快照，不将其称为发布稳定版。研究阶段尚未提交成果；后续整包美术已推送至独立成果仓库，当前记录见[Git交付记录](GIT_DELIVERY.md)。

## 研究结论及制作边界

OpenTTD 是交通运输经营模拟。玩家经营公司，在可调整地形的世界中连接城镇与产业，建设铁路、公路／有轨电车、水路和机场，购买、编组与调度车辆，运输旅客、邮件和产业货物以取得收入，承担建设及维护成本，再扩张网络。公司可以竞争或多人合作。出处：`README.md:29`、`src/widgets/toolbar_widget.h:15`、`src/widgets/company_widget.h:16`、`src/widgets/order_widget.h:15`。

游戏不是 RPG。角色属性、技能、装备、背包、宠物、战斗、传送、签到、抽卡、付费商城不属于这份功能基线。经理头像对应公司身份，不是角色创建或养成；车辆购买与改装对应运营资产，不是装备商店；Mail 是货物，`src/lang/english.txt:30`，不能因为美术主参考是邮件界面就加玩家邮箱。产业生产与供应链已存在，但没有玩家科技研究树；车型、机场、桥和扩展的年代可用性须如实显示。没有确认统一账户登录或服务器角色列表。多人使用玩家名称、公司与服务器／公司认证，见 `docs/multiplayer.md:27` 和 `src/network/network_gui.cpp:2229`。

可建议补充的内容仅是接入时的产品方案：加载封面、中文教程引导、合并导航与一致异常反馈。其布局与中文示例可定制，不能标为原游戏已有的新业务。临时游戏名称、公司名、地名、金额、车辆型号的中文演示值由美术稿采用，均须标为样例。首屏资源下载来自已存在 bootstrap，不能当作已确认游戏补丁器。

当前交付只覆盖图片、UI 设计和资源规格。地形示意或背景插画不是 OpenTTD 全部地物、八方向车辆、道路拓扑及信号动画的可运行替代资产；不可将 UI 美术验收等同于整款游戏实现、Unity 导入、渲染运行或线上联机验收。

## 实际读取与审计方法

先读 `F:/work/image/AGENTS.md`。克隆仓库及其上级 `E:/work/image`、`E:/work`、`E:/` 未发现另行适用的 AGENTS.md；仓库递归文件枚举也未发现 AGENTS.md。实际读取了 README、docs/multiplayer.md、docs/linkgraph.md、docs/directory_structure.md、窗口类枚举 src/window_type.h，以及主要工具栏、生成、车辆命令／时刻、公司、站点、多人、内容及设置 widget 定义与对应事件处理片段。

对全部 67 个 `*_gui.cpp` 提取窗口声明、WindowClass 引用、widget 标识、行数与当前哈希，并与 `src/window_type.h` 的 108 个有效窗口类逐项对照；全部找到 GUI 源码引用。机器清单是 `ui-source-inventory.json`，包含 132 项面向玩家或工具的页面／变体。它包括组合窗口的子页，不等于 132 个互斥游戏系统，也不能仅凭这个数字宣称所有图片已完成。

实际查看了 `media/baseset/openttd/openttdgui.png` 与 `roadstops.png`：是真实 PNG 图集，含传统像素式工具按钮、站点示意等，用于核实功能图标语义，不沿用其皮肤。`openttd.grf` 与 `orig_extra.grf` 有真实二进制字节，哈希见机器清单。源码无 .gitattributes，`git lfs ls-files` 输出为空，排除 .git 后扫描文件头没有发现 LFS 指针。完整基础图像／音效／音乐另外来自 OpenGFX/OpenSFX/OpenMSX 等，README.md:68-84 已明确说明。未为这次 UI 研究下载整个第三方基础集；缺少运行基础集不算 LFS 取图失败。本次未编译、未运行 OpenTTD，因此没有冒称游戏实际截图或已运行验收。

## 核心流程与依赖

1. 主菜单 → 新游戏、情景或高度图 → 气候、尺寸、年份、城镇／产业与 AI／GS／NewGRF 配置 → 生成进度 → 经营视图。证据 `src/intro_gui.cpp:286`、`src/genworld_gui.cpp:78`、`src/genworld_gui.cpp:1392`。
2. 地图、土地信息和产业链判断 → 建设交通路线、站点和车库 → 购买车辆／车厢 → 改装和编组 → 添加路线命令 → 设置装卸、共享、条件与回库 → 启动 → 观察候运和财务。证据 `src/rail_gui.cpp:444`、`src/road_gui.cpp:348`、`src/dock_gui.cpp:100`、`src/airport_gui.cpp:85`、`src/depot_gui.cpp:266`、`src/order_gui.cpp:1172`。
3. 车辆运营 → 详情、可靠性、检修与成本 → 时刻表、速度限制、延误和防聚集 → 分组、涂装、自动替换。证据 `src/vehicle_gui.cpp:2434`、`src/timetable_gui.cpp:172`、`src/group_gui.cpp:208`、`src/autoreplace_gui.cpp:81`。
4. 公司 → 资金、贷款、利息与基础设施维护 → 收入、利润、运量、绩效与价值图表 → 扩张、资助产业／城镇行动、并购。证据 `src/company_gui.cpp:344`、`src/company_gui.cpp:1569`、`src/graph_gui.cpp:947`、`src/town_gui.cpp:81`、`src/industry_gui.cpp:300`。
5. 多人 → Internet／LAN／邀请代码 → 服务器详情与兼容性 → 缺失内容／密码 → 连接和地图传输 → 新公司、加入公司或旁观 → 公司／私聊与管理员控制。版本不符、缺少 NewGRF、满员、密码错误、掉线与失步必须有独立语义。证据 `docs/multiplayer.md:15`、`src/network/network_gui.cpp:183`、`src/lang/english.txt:2461`、`src/lang/english.txt:2613`。
6. 在线内容与扩展 → 筛选、详情、依赖和下载 → NewGRF 激活顺序／参数／预设 → 新游戏／当前允许范围内应用。AI 和 GameScript 是不同角色：AI 经营对手公司，GS 可提供目标、故事、问答与自定义排行榜。证据 `src/newgrf_gui.cpp:597`、`src/ai/ai_gui.cpp:98`、`src/game/game_gui.cpp:92`、`src/goal_gui.cpp:40`、`src/story_gui.cpp:40`。
7. 情景编辑 → 新建空世界／随机地形 → 日期、地形、城镇、房屋、产业、道路、水路、对象、树木和路牌 → 保存情景 → 返回主菜单游玩。证据 `src/genworld_gui.cpp:1088`、`src/toolbar_gui.cpp:2362`、`src/town_gui.cpp:1656`。

## 重要机制与必要状态

铁路信号包含区段、入口、出口、组合、路径和单向路径，以及臂板／电气两套视觉；有信号密度与转换。铁路车站有方向、站台数、长度、拖拽建设和覆盖接受范围。公路客运站与货运站、尽头式与贯通式不是同一个按钮语义；有轨电车继承道路工具体系但受轨道类型可用性约束。水运须保留运河、船闸、浮标和水道桥；空运须显示机场布局、覆盖、年代／噪音及关闭状态。证据 `src/widgets/rail_widget.h:75`、`src/widgets/road_widget.h:15`、`src/widgets/dock_widget.h:36`、`src/widgets/airport_widget.h:23`。

命令至少包含前往、不经停、满载、卸载、中转、回库、共享命令、条件跳转、按命令改装、需要时检修和防聚集。车辆状态至少包含运行／停止、故障、迷路、老旧、坠毁／事故、停库检修、其他公司只读。时刻表有等待／行驶时间、完整性、开始日期、预期／计划到达、延误、自动填充与速度上限。证据 `src/widgets/order_widget.h:15`、`src/widgets/timetable_widget.h:15`、`src/widgets/vehicle_widget.h:15`。

所有列表需有空、筛选无结果、选中与只读；建设需有正常放置、拆除、预估成本、地形阻挡、其他公司／地方当局限制和资金不足；下载和联机有等待、进行、失败及取消；目标完成不等同于领取奖励，只有脚本确有对应动作时才展示领取。补贴有招标、授予、到期语义，不能用签到奖励代替。特殊调试窗口也进入辅助 UI 清单，可通过统一工具皮肤呈现，不需要默认展示在经营 HUD 上。

## 功能与来源总表

表内“已有”表示源代码具备功能，设计图和正式资源完成状态须读取本项目的制作／验收清单。

| ID | 系统 | 界面／变体 | 已核实源码 | 主要操作 |
|---|---|---|---|---|
| bootstrap | 启动与存档 | 首次资源检查与下载 | `src/bootstrap_gui.cpp:197` `BootstrapAskForDownloadWindow` | 检查缺失基础图像、同意下载、退出 |
| intro | 启动与存档 | 游戏主菜单 | `src/intro_gui.cpp:85` `SelectGameWindow` | 新游戏、读取存档、高度图、情景、多人、设置、在线内容、编辑器、高分、帮助、退出 |
| world-generation | 启动与存档 | 随机世界生成 | `src/genworld_gui.cpp:400` `GenerateLandscapeWindow` | 四种气候、地图尺寸、地形、河流、海平面、城镇产业、年份、AI/GS/NewGRF、生成 |
| heightmap | 启动与存档 | 高度图导入与生成 | `src/genworld_gui.cpp:1065` `ShowHeightmapLoad` | 高度图、旋转、最高高度、地图尺寸、气候、生成 |
| load | 启动与存档 | 读取存档与文件详情 | `src/fios_gui.cpp:345` `SaveLoadWindow` | 文件夹、名称排序、日期排序、存档兼容信息、所需NewGRF、载入 |
| save | 启动与存档 | 保存与覆盖确认 | `src/fios_gui.cpp:345` `SaveLoadWindow` | 文件名、保存、删除、新建目录、覆盖确认 |
| scenario-load | 启动与存档 | 情景选择 | `src/intro_gui.cpp:293` `WID_SGI_PLAY_SCENARIO` | 选择情景、查看作者信息、需要内容、开始 |
| world-progress | 启动与存档 | 生成与加载进度 | `src/genworld_gui.cpp:1392` `GenerateProgressWindow` | 进度阶段、取消、确认中止 |
| hud | 导航与地图 | 经营主界面与工具栏 | `src/toolbar_gui.cpp:2006` `MainToolbarWindow` | 暂停、快进、地图、公司、财务、交通工具、建设、行业、新闻、帮助 |
| statusbar | 导航与地图 | 日期资金与滚动新闻 | `src/statusbar_gui.cpp:56` `StatusBarWindow` | 日期、资金、最后新闻、暂停提示 |
| map | 导航与地图 | 全局地图 | `src/smallmap_gui.cpp:633` `SmallMapWindow` | 等高、车辆、产业、流量、线路、植被、所有权、图例、缩放、居中 |
| cargo-flow-map | 导航与地图 | 货流网络与图例 | `src/linkgraph/linkgraph_gui.cpp:546` `ShowLinkGraphLegend` | 公司筛选、货物筛选、拥挤度、容量、流量 |
| extra-view | 导航与地图 | 额外观察视窗 | `src/viewport_gui.cpp:53` `ExtraViewportWindow` | 缩放、对齐主视窗、居中 |
| transparency | 导航与地图 | 透明与隐藏工具栏 | `src/transparency_gui.cpp:28` `TransparenciesWindow` | 树木、房屋、产业、桥、站点、地标、透明/隐藏、锁定 |
| land-info | 导航与地图 | 土地信息 | `src/misc_gui.cpp:65` `LandInfoWindow` | 土地类型、拥有者、高度、建设日期、接受货物、清除成本 |
| sign-list | 导航与地图 | 路牌列表 | `src/signs_gui.cpp:137` `SignListWindow` | 搜索、排序、定位、新建 |
| sign-edit | 导航与地图 | 路牌编辑 | `src/signs_gui.cpp:405` `SignWindow` | 名称、前后切换、删除、定位 |
| rail-toolbar | 铁路建设 | 铁路建设工具 | `src/rail_gui.cpp:444` `BuildRailToolbarWindow` | 方向、自动轨道、拆除、车库、路点、车站、信号、桥、隧道、移除、轨道转换 |
| rail-station | 铁路建设 | 铁路车站选择与覆盖 | `src/rail_gui.cpp:1115` `BuildRailStationWindow` | 站台数、站台长度、方向、拖放、类型搜索、覆盖、接受货物 |
| rail-depot | 铁路建设 | 铁路车库方向选择 | `src/rail_gui.cpp:1789` `BuildRailDepotWindow` | 四向入口、放置 |
| rail-waypoint | 铁路建设 | 铁路路点选择 | `src/rail_gui.cpp:1951` `BuildRailWaypointWindow` | 样式、搜索、放置 |
| signal | 铁路建设 | 铁路信号选择与转换 | `src/rail_gui.cpp:1535` `BuildSignalWindow` | 臂板/电气、区段、入口、出口、组合、路径、单向路径、密度、转换 |
| bridge | 建设通用 | 桥梁类型与成本 | `src/bridge_gui.cpp:73` `BuildBridgeWindow` | 桥型、速度、成本、排序、建造 |
| station-join | 建设通用 | 站点与路点合并 | `src/station_gui.cpp:2332` `SelectStationWindow` | 新站、已有站、距离、合并 |
| road-toolbar | 公路建设 | 公路建设工具 | `src/road_gui.cpp:348` `BuildRoadToolbarWindow` | 方向、自动道路、单行、拆除、车库、客运站、货运站、桥、隧道、转换 |
| tram-toolbar | 公路建设 | 有轨电车建设工具 | `src/road_gui.cpp:348` `BuildRoadToolbarWindow` | 轨道方向、车库、站点、桥、隧道、转换 |
| road-depot | 公路建设 | 公路与电车车库 | `src/road_gui.cpp:1191` `BuildRoadDepotWindow` | 四向入口、放置 |
| bus-stop | 公路建设 | 客运站选择与覆盖 | `src/road_gui.cpp:1395` `BuildRoadStationWindow` | 方向、尽头/贯通、样式、覆盖 |
| truck-stop | 公路建设 | 货运站选择与覆盖 | `src/road_gui.cpp:1395` `BuildRoadStationWindow` | 方向、尽头/贯通、货物覆盖、样式 |
| road-waypoint | 公路建设 | 公路路点 | `src/road_gui.cpp:1805` `BuildRoadWaypointWindow` | 路点样式、放置、方向 |
| water-toolbar | 水运建设 | 水运建设工具 | `src/dock_gui.cpp:100` `BuildDocksToolbarWindow` | 运河、船闸、船坞、码头、浮标、水道桥、拆除 |
| water-depot | 水运建设 | 船坞方向 | `src/dock_gui.cpp:519` `BuildDocksDepotWindow` | 两向船坞、放置 |
| water-station | 水运建设 | 码头与覆盖 | `src/dock_gui.cpp:421` `BuildDocksStationWindow` | 覆盖、接受货物、放置 |
| airport-toolbar | 空运建设 | 航空建设工具 | `src/airport_gui.cpp:85` `BuildAirToolbarWindow` | 机场、拆除 |
| airport-picker | 空运建设 | 机场类型与布局 | `src/airport_gui.cpp:241` `BuildAirportWindow` | 类别、机场列表、布局、预览、覆盖、接受货物 |
| terraform | 环境与装饰 | 地形整治工具 | `src/terraform_gui.cpp:264` `TerraformToolbarWindow` | 升高、降低、平整、清除、购地、种树、路牌、对象 |
| trees | 环境与装饰 | 种植树木 | `src/tree_gui.cpp:79` `BuildTreesWindow` | 类型、随机、范围、放置 |
| objects | 环境与装饰 | 景观对象选择 | `src/object_gui.cpp:123` `BuildObjectWindow` | 分类、筛选、样式、旋转、放置 |
| station-list | 站点与货运 | 公司站点列表 | `src/station_gui.cpp:265` `CompanyStationsWindow` | 五类设施、货物筛选、名称筛选、排序、定位 |
| station-view | 站点与货运 | 站点详情与候运 | `src/station_gui.cpp:1256` `StationViewWindow` | 等待货物、分组、来源目的地、货运评级、接受、列车/公路/船舶/飞机、覆盖、重命名 |
| airport-close | 站点与货运 | 机场临时关闭 | `src/station_gui.cpp:867` `WID_SV_CLOSE_AIRPORT` | 关闭/重开机场、查看车辆 |
| waypoint-view | 站点与货运 | 路点与浮标详情 | `src/waypoint_gui.cpp:34` `WaypointWindow` | 重命名、位置、相关车辆、覆盖 |
| vehicle-list-train | 车辆运营 | 列车与分组 | `src/group_gui.cpp:208` `VehicleGroupWindow` | 分组树、筛选、排序、启停、返回车库、自动替换、涂装 |
| vehicle-list-road | 车辆运营 | 公路车辆与分组 | `src/group_gui.cpp:208` `VehicleGroupWindow` | 分组树、筛选、排序、批量启停、回库、替换 |
| vehicle-list-ship | 车辆运营 | 船舶与分组 | `src/group_gui.cpp:208` `VehicleGroupWindow` | 分组树、筛选、排序、批量启停、回坞、替换 |
| vehicle-list-air | 车辆运营 | 航空器与分组 | `src/group_gui.cpp:208` `VehicleGroupWindow` | 分组树、筛选、排序、批量启停、回机库、替换 |
| vehicle-depot | 车辆运营 | 车库与编组 | `src/depot_gui.cpp:266` `DepotWindow` | 拖拽编组、出售、新购、克隆、启动、全部启动/停止、全部出售 |
| vehicle-buy | 车辆运营 | 购买交通工具 | `src/build_vehicle_gui.cpp:1217` `BuildVehicleWindow` | 四类型、筛选、排序、折叠车型、载货、预览、参数、购买、重命名 |
| vehicle-view | 车辆运营 | 交通工具控制 | `src/vehicle_gui.cpp:3003` `VehicleViewWindow` | 启停、转向、回库、跟随、命令、详情、改装、克隆、危险信号强制通行（仅适用列车） |
| vehicle-details | 车辆运营 | 交通工具详细参数 | `src/vehicle_gui.cpp:2434` `VehicleDetailsWindow` | 容量、车厢、运行成本、收入、年龄、可靠性、检修间隔 |
| vehicle-refit | 车辆运营 | 货舱改装 | `src/vehicle_gui.cpp:754` `RefitWindow` | 货物、容量、改装费用、按命令改装 |
| vehicle-replace | 车辆运营 | 自动替换与续购 | `src/autoreplace_gui.cpp:81` `ReplaceVehicleWindow` | 旧车型、新车型、启动/停止替换、可用性、保留列车长度 |
| vehicle-orders | 运输调度 | 路线命令列表 | `src/order_gui.cpp:498` `OrdersWindow` | 前往、跳过、删除、不经停、装载、卸载、中转、回库、共享、改装 |
| conditional-orders | 运输调度 | 条件命令与检修分流 | `src/order_gui.cpp:804` `WID_O_COND_VARIABLE` | 变量、比较、阈值、跳转、回库操作、防聚集 |
| vehicle-timetable | 运输调度 | 时刻表与速度限制 | `src/timetable_gui.cpp:172` `TimetableWindow` | 行驶/等待、开始日期、修改时间、清除、延误、自动填表、预期/计划、速度限制 |
| set-date | 运输调度 | 日期与时刻选择 | `src/date_gui.cpp:28` `SetDateWindow` | 年/月/日、确定、取消 |
| engine-preview | 车辆运营 | 新车型试用邀请 | `src/engine_gui.cpp:79` `EnginePreviewWindow` | 车型能力、试用、拒绝 |
| company | 公司与财务 | 公司信息与总部 | `src/company_gui.cpp:1936` `CompanyWindow` | 公司名、经理名、头像、涂装、总部、基础设施、赠款、并购、加入 |
| finance | 公司与财务 | 财务报表与贷款 | `src/company_gui.cpp:344` `CompanyFinancesWindow` | 三年/三期费用、现金、借款、还款、利息、基础设施 |
| livery | 公司与财务 | 公司与分组涂装 | `src/company_gui.cpp:620` `SelectCompanyLiveryWindow` | 交通类型、分组、主色、辅色、继承 |
| manager-face | 公司与财务 | 经理形象与姓名 | `src/company_gui.cpp:1216` `SelectCompanyManagerFaceWindow` | 随机、风格、部件、载入/保存、形象码、接受/取消 |
| infrastructure | 公司与财务 | 基础设施统计与维护 | `src/company_gui.cpp:1569` `CompanyInfrastructureWindow` | 轨道、道路、水路、车站、机场、维护费用 |
| company-buy | 公司与财务 | 收购与并购确认 | `src/company_gui.cpp:2343` `BuyCompanyWindow` | 公司价值、收购成本、确认/取消 |
| town-list | 城镇与产业 | 城镇目录 | `src/town_gui.cpp:720` `TownDirectoryWindow` | 名称、人口、评级、筛选、排序、定位 |
| town-view | 城镇与产业 | 城镇详情 | `src/town_gui.cpp:346` `TownViewWindow` | 人口、房屋、增长、货物需求、地方当局、定位、重命名 |
| town-authority | 城镇与产业 | 地方当局与行动 | `src/town_gui.cpp:81` `TownAuthorityWindow` | 评级、广告、雕像、修路、资助建筑、独占运输、贿赂 |
| town-found | 城镇与产业 | 创建城镇 | `src/town_gui.cpp:1149` `FoundTownWindow` | 城镇名、规模、城市、道路布局、随机位置、建立 |
| industry-list | 城镇与产业 | 产业目录 | `src/industry_gui.cpp:1321` `IndustryDirectoryWindow` | 类型、名称、生产、运输率、筛选、排序、定位 |
| industry-view | 城镇与产业 | 产业详情与生产 | `src/industry_gui.cpp:783` `IndustryViewWindow` | 输入货物、输出、运输率、生产历史、位置、供应链 |
| industry-build | 城镇与产业 | 资助产业与勘探 | `src/industry_gui.cpp:300` `BuildIndustryWindow` | 产业类型、成本、勘探/放置、帮助 |
| cargo-chain | 城镇与产业 | 产业货物流转关系 | `src/industry_gui.cpp:2688` `IndustryCargoesWindow` | 产业/货物筛选、上游/下游、供应链导航、图例 |
| subsidies | 目标新闻与成绩 | 运输补贴 | `src/subsidy_gui.cpp:26` `SubsidyListWindow` | 可申领线路、到期、已授予、定位起终点 |
| news | 目标新闻与成绩 | 新闻通知 | `src/news_gui.cpp:359` `NewsWindow` | 产业、车型、事故、公司、定位、车辆、关闭 |
| news-history | 目标新闻与成绩 | 新闻历史列表 | `src/news_gui.cpp:1217` `MessageHistoryWindow` | 分类、时间、重新查看、定位 |
| goals | 目标新闻与成绩 | 脚本目标列表 | `src/goal_gui.cpp:40` `GoalListWindow` | 全局/公司目标、进度、已完成、定位 |
| goal-question | 目标新闻与成绩 | 脚本问题与选择 | `src/goal_gui.cpp:319` `GoalQuestionWindow` | 问题、按钮选择、回答 |
| story | 目标新闻与成绩 | 故事书与互动页面 | `src/story_gui.cpp:40` `StoryBookWindow` | 章节、翻页、元素、地图位置、按钮 |
| company-league | 目标新闻与成绩 | 公司排行 | `src/league_gui.cpp:57` `PerformanceLeagueWindow` | 公司排名、绩效、详情 |
| script-league | 目标新闻与成绩 | 脚本排行榜 | `src/league_gui.cpp:251` `ScriptLeagueWindow` | 表格、分数、链接、公司 |
| highscore | 目标新闻与成绩 | 历史高分 | `src/highscore_gui.cpp:170` `HighScoreWindow` | 难度、排名、分数 |
| endgame | 目标新闻与成绩 | 阶段结算 | `src/highscore_gui.cpp:111` `EndGameWindow` | 成绩、继续经营、高分 |
| income-graph | 经济图表 | 收入图表 | `src/graph_gui.cpp:1001` `IncomeGraphWindow` | 公司选择、时间轴、图例 |
| profit-graph | 经济图表 | 营业利润图表 | `src/graph_gui.cpp:947` `OperatingProfitGraphWindow` | 公司选择、时间轴、图例 |
| cargo-graph | 经济图表 | 运量图表 | `src/graph_gui.cpp:1053` `DeliveredCargoGraphWindow` | 公司选择、运量、时间轴 |
| performance-graph | 经济图表 | 绩效历史 | `src/graph_gui.cpp:1105` `PerformanceHistoryGraphWindow` | 公司选择、绩效、时间轴 |
| value-graph | 经济图表 | 公司价值 | `src/graph_gui.cpp:1164` `CompanyValueGraphWindow` | 公司选择、价值、时间轴 |
| cargo-rates | 经济图表 | 货物运价 | `src/graph_gui.cpp:1392` `PaymentRatesGraphWindow` | 货物图例、运输时间、运价对照 |
| performance-detail | 经济图表 | 绩效评分详情 | `src/graph_gui.cpp:1506` `PerformanceRatingDetailWindow` | 车辆、站点、收入、运量、货物种类、现金、贷款、总分 |
| industry-production | 经济图表 | 产业生产历史 | `src/graph_gui.cpp:1729` `IndustryProductionGraphWindow` | 货物、产量、运输量、时间 |
| town-cargo | 经济图表 | 城镇货物历史 | `src/graph_gui.cpp:1906` `TownCargoGraphWindow` | 旅客、邮件、生成/运输量 |
| network-list | 多人联机 | 服务器列表与详情 | `src/network/network_gui.cpp:183` `NetworkGameWindow` | 玩家名、筛选、LAN/Internet、添加、刷新、详情、加入、建服 |
| network-start | 多人联机 | 创建服务器 | `src/network/network_gui.cpp:981` `NetworkStartServerWindow` | 名称、密码、公开/邀请/本地、玩家/公司上限、新游戏/读取/情景 |
| network-join | 多人联机 | 连接进度与断线 | `src/network/network_gui.cpp:2087` `NetworkJoinStatusWindow` | 阶段、下载地图、等待、取消/确定 |
| network-password | 多人联机 | 服务器与公司密码 | `src/network/network_gui.cpp:2229` `ShowNetworkNeedPassword` | 输入密码、确定、取消 |
| network-clients | 多人联机 | 玩家与公司列表 | `src/network/network_gui.cpp:1601` `NetworkClientListWindow` | 加入公司、新建公司、旁观、私聊、踢出/封禁、邀请代码、改名 |
| network-chat | 多人联机 | 世界公司与私聊 | `src/network/network_chat_gui.cpp:305` `NetworkChatWindow` | 目的地、输入、发送、历史 |
| network-relay | 多人联机 | 中继连接确认 | `src/network/network_gui.cpp:2241` `NetworkAskRelayWindow` | 拒绝、仅此次、总是允许 |
| network-survey | 多人联机 | 调查与隐私选项 | `src/network/network_gui.cpp:2357` `NetworkAskSurveyWindow` | 预览、详细与隐私、拒绝、同意 |
| content-list | 扩展与脚本 | 在线内容浏览 | `src/network/network_content_gui.cpp:343` `NetworkContentListWindow` | 类别、过滤、详情、依赖、全选、下载 |
| content-download | 扩展与脚本 | 内容下载进度 | `src/network/network_content_gui.cpp:205` `NetworkContentDownloadStatusWindow` | 文件进度、总体进度、取消 |
| newgrf | 扩展与脚本 | NewGRF 管理 | `src/newgrf_gui.cpp:597` `NewGRFWindow` | 可用/激活、顺序、参数、预设、扫描、应用、下载缺失、说明 |
| newgrf-params | 扩展与脚本 | NewGRF 参数 | `src/newgrf_gui.cpp:146` `NewGRFParametersWindow` | 参数名、值、默认、说明 |
| newgrf-preset | 扩展与脚本 | 扩展预设 | `src/newgrf_gui.cpp:2008` `SavePresetWindow` | 名称、保存、删除、载入 |
| content-text | 扩展与脚本 | 内容说明许可与变更 | `src/textfile_gui.cpp:85` `TextfileWindow` | 滚动、搜索、链接、说明/变更/许可 |
| ai-config | 扩展与脚本 | AI 对手配置 | `src/ai/ai_gui.cpp:98` `AIConfigWindow` | 数量、启动间隔、排列、选择、设置、下载、说明 |
| gs-config | 扩展与脚本 | GameScript 配置 | `src/game/game_gui.cpp:92` `GSConfigWindow` | 选择、参数、重置、下载、文档 |
| script-list | 扩展与脚本 | AI/GS 脚本选择 | `src/script/script_gui.cpp:61` `ScriptListWindow` | 脚本、版本、作者、选择、下载 |
| script-settings | 扩展与脚本 | AI/GS 参数设置 | `src/script/script_gui.cpp:292` `ScriptSettingsWindow` | 参数、默认、难度、修改 |
| script-debug | 扩展与脚本 | 脚本日志与异常 | `src/script/script_gui.cpp:667` `ScriptDebugWindow` | 脚本选择、日志等级、暂停、继续、重载、断点 |
| settings | 设置与帮助 | 通用设置 | `src/settings_gui.cpp:391` `GameOptionsWindow` | 语言、币种、单位、显示、分辨率、图像集、声音集、社交整合、调查 |
| advanced-settings | 设置与帮助 | 高级设置树 | `src/settings_gui.cpp:391` `GameOptionsWindow` | 类别、搜索、基础/专家、游戏/客户端、修改值、重置 |
| currency | 设置与帮助 | 自定义货币 | `src/settings_gui.cpp:1971` `CustomCurrencyWindow` | 汇率、分隔、前后缀、欧元启用年、预览 |
| music | 设置与帮助 | 音乐音效与曲目 | `src/music_gui.cpp:678` `MusicWindow` | 播放、前后曲、音量、音效、随机、循环、播放列表 |
| music-tracks | 设置与帮助 | 播放列表编辑 | `src/music_gui.cpp:482` `MusicTrackSelectionWindow` | 曲库、列表、添加/移除、清除 |
| help | 设置与帮助 | 帮助中心 | `src/help_gui.cpp:124` `HelpWindow` | README、更新、已知问题、许可、字体、官网、Wiki、反馈、社区 |
| about | 设置与帮助 | 关于与制作人员 | `src/misc_gui.cpp:412` `AboutWindow` | 版本、制作人员、许可 |
| screenshot | 设置与帮助 | 截图导出选择 | `src/screenshot_gui.cpp:22` `ScreenshotWindow` | 视口、整个世界、高度图、小地图、保存 |
| scenario-create | 情景编辑 | 新建情景 | `src/genworld_gui.cpp:1088` `CreateScenarioWindow` | 气候、尺寸、年份、平地高度、空世界/随机 |
| scenario-hud | 情景编辑 | 情景编辑主工具栏 | `src/toolbar_gui.cpp:2362` `ScenarioEditorToolbarWindow` | 日期、生成地形、城镇、产业、道路、水路、树木、路牌、保存 |
| scenario-terrain | 情景编辑 | 编辑器地形生成 | `src/terraform_gui.cpp:636` `ScenarioEditorLandscapeGenerationWindow` | 笔刷、海面、岩石、沙漠、升降、生成、平整 |
| scenario-house | 情景编辑 | 房屋选择放置 | `src/town_gui.cpp:1656` `BuildHouseWindow` | 类别、房型、年代、旋转、放置 |
| cheats | 开发与辅助 | 沙盒作弊与限制 | `src/cheat_gui.cpp:235` `CheatWindow` | 修改资金/公司/时间、生产、高度限制、记录 |
| console | 开发与辅助 | 控制台 | `src/console_gui.cpp:144` `IConsoleWindow` | 输入、命令、日志、历史 |
| newgrf-inspect | 开发与辅助 | NewGRF 对象检查 | `src/newgrf_debug_gui.cpp:258` `NewGRFInspectWindow` | 对象、变量、属性、回调、父级 |
| sprite-align | 开发与辅助 | 精灵对齐工具 | `src/newgrf_debug_gui.cpp:798` `SpriteAlignerWindow` | 精灵编号、偏移、前后、选择 |
| framerate | 开发与辅助 | 帧率与性能 | `src/framerate_gui.cpp:457` `FramerateWindow` | 主循环、绘制、AI、速度、帧时间图 |
| frametime | 开发与辅助 | 帧时间历史 | `src/framerate_gui.cpp:762` `FrametimeGraphWindow` | 组件、暂停、时间图、图例 |
| error | 通用状态 | 错误通知 | `src/error_gui.cpp:97` `ErrmsgWindow` | 原因、额外说明、定位、关闭 |
| tooltip | 通用状态 | 悬停说明与预估费用 | `src/misc_gui.cpp:602` `TooltipsWindow` | 说明、快捷键、预估开销/收入 |
| input-query | 通用状态 | 名称数量与输入 | `src/misc_gui.cpp:898` `QueryStringWindow` | 名称/数值、清空、确定、取消 |
| confirm | 通用状态 | 通用确认取消 | `src/misc_gui.cpp:1086` `QueryWindow` | 标题、说明、确认、取消 |
| osk | 通用状态 | 屏幕键盘 | `src/osk_gui.cpp:39` `OskWindow` | 字符、大小写、退格、确定、取消 |

## 交接与验收使用

- 图像制作者应从 `ui-source-inventory.json` 的 actions/states 取得功能语义，再以 `screen-catalog.json` 的合并关系制作，不能把数据条目数量当成图片数量。
- 每个菜单入口、详情／选择／确认／返回应在整屏或状态预览中有对应；合并展示必须在验收清单记录。
- 建议补充功能必须带 `assumption`／`suggested` 标志。未确认的角色／战斗等功能继续标不适用，不在本项目编造。
- 功能研究依据保留在 reference，成果提交时排除整个 reference 克隆。上游代码许可证为 COPYING.md 的 GPL-2.0；本次没有抽取其像素图集成为正式新美术资源。

# 农田与铁路围栏源码适配

本包只补独立状态/位置/几何合同，原fence、rail与已验收PNG不改。`assets/world/overlays/fence-adapter/manifest.json`包含44张320×320 RGBA：农田6有效家族×6源offset的36角色，铁路8原生角色。所有图素复用现有木栏、石栏、花篱三个原生材料，没有新母图、程序绘制栏杆或新增原生视角。

农田依据`clear_cmd.cpp:94–134`、`table/clear_land.h:28–77`，读取`_clear_land_fence_sprites`的6个显式有效值和四边31项坡表。数组声明[7]的最后一项是隐式0，作为reserved/no-image记录；fenceValue0同样不画，不把它们当第七种新源实体。六种有效身份依次为灌木、带木门灌木、木栏、黄花篱、红花篱、石栏。门用现有篱笆开口加原生木栏中段组合；黄色/红色只选择原画已有花瓣调色，叶片/结构保留，不代码画新花或门。

每家族六个offset的屏幕端点dy为+64、−64、+96、−96、+32、−32（dx均128）。投影保留立柱竖直，以原生Alpha接地轮廓拟合参考线，再逐列几何改变地面斜率；该拟合是明示美术校准，不称独立模型透视。456条绑定完整保存6家族×19合法坡×4边的原Sprite值、源offset、两端角点高度、源码参考角Z和PNG摆放量。立柱不随地面旋转；相邻边共享同一逻辑角点，陡坡仍按每边一级高度差处理。

角色画布锚点(160,192)、Pivot(0.5,0.4)，Border Left/Bottom/Right/Top为0。组装检查画布512×384、地块锚点(256,224)。底图按照实际anchorPx摆放：256×192草坡锚点(128,128)放(128,96)，256×256农田锚点(128,160)放(128,64)。四角的X/Y来自2:1菱形，Y逐角减height×32；按绑定pasteXY叠角色图即可，不再重复加角点Z。原生脚部花草/柔边有少量美术外延，逻辑端点与碰撞不能改用Alpha外接框。

铁路依据`rail_cmd.cpp:1944–2085`：默认SPR_TRACK_FENCE_FLAT_X从1301开始8角色，16个`_fence_offsets`按rfo%8复用。每个源位置保存原origin、extent、height_ref、Sprite角色及基准摆放；有效height_ref另外读取RemoveHalftileSlope后的对应角点Z。四边围栏、中央水平/垂直隔栏分别绑定，不能仅用四个农田平边替代。

中央竖向隔栏使用现有木栏的edge-on几何投影：逻辑分隔线严格为N–S，保留源1×1世界包围盒对应的16px有限物理宽度以避免退化变换；这是共享原画的窄侧视，非新原生角度。水平隔栏用两个128px原生栏段连续复用跨W–E，不把一个小源片放大成新细节。190条RailGroundType selector只表达源码选择函数，必须保留原游戏地基/轨型合法组合，不能据此声称所有坡/groundType都能建造。

HalfTileWater明确W/N/E/S→位置2/3/10/11，只绘高半格分隔线并用对应参考角Z。四张检查场景实际复用当前半格三角地基与水面；N/S为水平分隔，W/E为窄侧视分隔。Barren、Grass、SnowOrDesert、HalfTileSnow及关闭FullDetail均不绘铁路围栏；无栏段条件不输出假图片。

`previews/fence-adapter/index.html`包含六家族全部19坡共114组实际四边拼装、铁路全部16位置与4个半水地基场景。验证逐条比较逻辑端点、源mod表、源Sprite和当前SHA，另外检查原生paint在接地点附近、真实Alpha、相同画布/锚点和花瓣变色保留Alpha。来源和几何通过不等于Unity遮挡、净空或用户批准。

导入建议Sprite/Single、Full Rect、Bilinear、Clamp、无Mip Maps、图集Padding≥4。引擎按源角点/地基放置并验证隔栏遮挡、碰撞和高度；用户美术批准与Unity仍pending/false。独立记录：`records/fence-adapter-validation.json`、`fence-adapter-visual-review.json`、`fence-adapter-browser-validation.json`。

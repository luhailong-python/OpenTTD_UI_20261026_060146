# 独立岩石、雪盖与岸石

正式分包：`assets/world/terrain/rocks-overlay/manifest.json`。预览入口：`previews/world/rocks-overlay/index.html`。本包补上真实石块叠层，旧`terrain-rocks-density-*`只是bare/rough材质混合，不再作为岩石需求通过依据；旧PNG保留，不覆盖或删除。

源码依据为固定OpenTTD提交的`clear_cmd.cpp:145–167`、`water_cmd.cpp:1020–1028`、`table/clear_land.h:96–100`、`table/sprites.h:360–367`及`landscape.cpp`的坡码/高度函数。六个叠层状态为干石、四雪量和湿岸石，各19坡；正常干岩另有第二tilehash布局，合计133个独立叠层。第二布局共享同一原生岩体，并非第二套新原画。另有18个从新原生图提取的实际石块母件。

新原生母图`source-art/world/rock-overlays-native.png`提供相同三块石头的六个实际绘画状态。雪盖直接来自原生画面，没有用白色调色冒充积雪；湿石没有烘焙水底。母图Alpha范围0..254、角落Alpha1，不能称为原生完美透明。提取按各石块真实Alpha≥128主体加2像素原生边缘，仅去除非所有权及Alpha<8的远处发光，保留原RGB与绘画轮廓。深浅背景原尺寸检查见`native-alpha-edges.jpg`，逐石裁切数据见`rocks-overlay-source-crops.json`。

每块石头保持竖直，只按接地点分别升降，不把整块立体岩石压成坡地。统一叠层画布256×256、锚点[128,192]；地形256×192锚点[128,128]应偏移[0,64]，平地256×128锚点[128,64]偏移[0,128]。源接点在16×16逻辑格内，公式为`x=128+(sourceY-sourceX)*8`、`y=128+(sourceX+sourceY)*4-GetPartialPixelZ*4`。133叠层逐项保存三石源坐标、高度、偏移及原生母件引用。

241张实际组合覆盖干地两布局、四雪量、四沙量的19坡，以及ClearRocks的Sea/Canal/River和CoastRocks的16合法坡×3气候。雪/沙底地比例为1/4、1/2、3/4、1的明确材质混合配方，不声称恰有相同比例的像素绘成雪/沙。动态水面应在引擎中保持独立，本地组合只是静态美术检查。

CoastRocks必须复用`assets/world/terrain/shore-geometry/manifest.json`的正式水平水、真实坡陆地与原生岸界层；`formalLayers`给出固定偏移与顺序。旧water-states平面岸图会使按源码抬升的石头悬空，已从本包正确配方中移除。源码DryOut姿态可能只在低角接海，因此water可以为null，不能补回整格平水；flat/EW/NS海岸不适用并明确保留原因。48条海岸配方均逐层复合比较，并验证三石接点有实际基底Alpha与源码高度支撑。

可重跑`tools/build_rocks_overlay.py`生产本包，`tools/validate_rocks_overlay.py`只复核当前来源SHA、133状态/坡/布局、固定画布、原画竖直重组、真实岸基底与保留状态。机械记录为`records/world-production/rocks-overlay-validation.json`；实际逐页视觉记录为`rocks-overlay-visual-review.json`。两者分开，不替代用户批准、Unity排序/遮挡/碰撞或运行验收。

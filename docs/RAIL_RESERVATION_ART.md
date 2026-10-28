# 铁路路径预留灰化叠层

源`rail_cmd.cpp:2156–2173,2258–2261,2391–2415`以及`station_cmd.cpp:3426–3436`在show_track_reservation开启且轨段被预留时，以PALETTE_CRASH绘实际轨段overlay。该状态不是整块地形变灰，也不是铁路公司颜色。本包明确绑定现有rail-rail、rail-electric、rail-monorail、rail-maglev四项需求的状态。

`assets/world/overlays/rail-reservation/manifest.json`保存4轨制×6轨段×平/四坡共120张256×192 RGBA叠层。只读取现有layer=track-overlay的独立PNG，灰化RGB而逐像素保留原Alpha；平地只加64px透明顶边，与四坡统一锚点(128,128)、Pivot(0.5,1/3)。草地、裸地、水面、道床外侧空白、架空线、电杆和车辆不进入灰化输入。

材质采用当前画面的暗灰解释：RGB三通道均为round((0.2126R+0.7152G+0.0722B)×0.58)，A保持源值；直Alpha以source-over合成。它是本项目美术调色，不声称与原游戏索引调色板字节等价。没有绘制新轨道或新原画，所有源SHA及派生步骤保留。

实际显示使用`reservedTrackBits & existingTrackBits`，只叠对应bit，0不画；每个源bit可单独预留。高级地基的上/下半格使用与普通轨段相同的已交付所有权剪裁和高度，不能把未铺轨的另一半土地灰化。车站/道岔复用相应轨段与同锚点，不叠整块场景灰图。源菜单模式和show_track_reservation关闭时不画。

`previews/rail-reservation/index.html`有平/四坡五页120组实际对照，每格左普通、右预留。专项逐像素验证源Alpha完全一致、所有权外RGBA为0、实际草地在轨段所有权之外合成前后完全不变；实际图审另记。Unity建议Sprite/Single、Full Rect、Bilinear、Clamp、无Mip Maps、Border Left/Bottom/Right/Top为0、图集Padding≥4。路由保留逻辑、源精确调色板和引擎运行不属于本地PNG验证，用户批准/Unity仍pending/false。

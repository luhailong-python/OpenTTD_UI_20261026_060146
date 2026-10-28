# 两项原生产业粒子绑定

源码 `industry_cmd.cpp:285–290` 的气泡发生器和 `309–320` 的煤电厂火花，原先只有完整静态厂区与公共FX，缺少实际安装到厂区的绑定。本次补齐这两项；六组已确认机械的原像素和动作帧保持原样。

两项都使用512×512父画布、锚点 `[256,448]`、偏移 `[0,0]`。`sourceRequirementIds` 同时绑定原有 `animation-industry-machinery` 和对应产业ID，不新增重复的世界需求行。所有八项绑定以 `sourceMachineryType` 对应原需求中的八种类型，可进行精确集合核查。

| 项目 | 实际来源与处理 | 父体使用 |
|---|---|---|
| 煤电厂火花 | 既有 `electric-spark` 六关键帧缩小、放到实际右侧铜制变压器；12相位是公共生命周期图的播放安排 | 原图未烘焙火花，cleanBase为完全相同的原像素副本；未工作时不绘制粒子 |
| 气泡发生器 | 既有 `bubble-generation`、`bubble-float`、`bubble-burst` 生命周期图缩小、定位、二维上移；未生成新原画 | 从原父图Alpha中移除三个悬空大泡，再组合粒子；金属管、器皿、池内小泡沫及地基保持原像素 |

每项提供12张粒子层、1张cleanBase、4×3图集、完整厂区12相位图与GIF。新增正式精灵26张；额外mask与sheet是数据/包装文件，分别统计。8组总体包含6机械＋2粒子，共96张移动层、8张cleanBase。

两个遮罩用途不同：`removedPoseMask` 只删除原图已烘焙的移动姿态，煤电厂此遮罩全黑表示无需删除；`ownershipMask` 包含原父图到cleanBase的全部Alpha差异，以及所有粒子相位Alpha的并集，表示整组动画的全部改动范围。不能用这个较大范围挖空厂区，删除操作只使用removedPoseMask。正确绘制为cleanBase＋当前粒子层；气泡厂不能再叠加原有三个大泡的静态父图。整包复核曾发现旧ownership只包住新粒子而漏掉原大泡移除范围，现已修正并验证。

来源仍是已保留的原生手绘母图。缩小、Alpha移除、定位、图集包装与生命周期播放都不计作新模型生成。两项没有新增原生动作图，也不是视频或三维粒子模拟。活动相位GIF用于美术检查，实际源码时钟、未工作状态与业务触发在下一阶段接入。

已实际查看两页全部24相位与去旧泡前后对照，检查位置、上浮方向、静态地基和原大泡残留；独立专项151项通过。GIF已解码验证12帧、100毫秒/帧、循环，但当前无可用连接浏览器，未声称浏览器实播或Unity运行通过。用户审美确认待后续。

- [实际安装预览](../previews/world/industry-assembly/index.html)
- [去旧泡对照](../previews/world/industry-assembly/bubble-generator-removal-review.jpg)
- [火花12相位](../previews/world/industry-assembly/coal-plant-sparks-phases.jpg)
- [气泡12相位](../previews/world/industry-assembly/bubble-generator-cycle-phases.jpg)
- [专项数据](../records/world-production/industry-fx-binding-validation.json)

按依赖重建：`build_industry_bindings.py`（六机械）→ `build_industry_fx_bindings.py`（追加两粒子）→ `validate_industries.py` → `validate_industry_fx_bindings.py` → `finalize_industry_bindings.py`。生产重建后，必须重新比对视觉记录哈希；脚本通过不自动批准新像素。

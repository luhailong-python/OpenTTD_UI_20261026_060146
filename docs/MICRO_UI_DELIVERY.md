# 窗口、状态与车队小图标补包

本包从固定OpenTTD提交的`src/table/sprites.h`第56–193行实际扫描96个UI Sprite符号，排除已经单独交付的半格选区和世界基址。覆盖左右缩放、收起/展开、调试/默认大小、四向箭头、键盘、4利润态、4城镇评价、4种车辆的6类分组操作、克隆/出售单台/出售全部/整列出售、联机与辅助图标。每个源符号保存实际定义行、数值表达式和源码使用示例。

正式资源为`assets/common/micro-ui/manifest.json`中的115张PNG：96主图、16公司色方块和3兼容性玉珠色态。`MICRO_UI_BINDINGS.json`是96源码符号与资源的权威映射；色态归属保存在对应绑定的`paletteVariants`中。16公司色沿用项目已交付的色名/色值，不冒充OpenTTD精确RGB色表。

画面沿用既有手绘车辆、城镇、金玉器物和控件。裁切、缩小、旋转、色调和组合逐件记录源SHA；独立SVG只含功能线条、箭头与数据符号，不称新原画。未调用图像模型，actualModel/actualQuality保持null，不能把这些派生输出计为115幅新手绘。

PNG均为96×96 RGBA、中心锚点(48,48)、Pivot(0.5,0.5)、Border Left/Bottom/Right/Top均0。含动作角标的图标建议48–64px；24px展示用于密集列表比较，必须配独立中文文字/tooltip，不能以缩小后的细小角标作为唯一操作说明。动态文案使用既有NotoSansSC字体，不烘焙到图片。

同一图标在普通/按下/选中/禁用/锁定状态保持相同画布和位置，分别复用已有button_secondary_normal、button_secondary_pressed、button_primary_selected、button_disabled；禁用图标Alpha建议0.40，锁定叠加独立锁图标。`previews/micro-ui/control-state-composition.jpg`展示真实九宫格按钮与同位置图标的五态拼装，不是新增控件原画。

预览入口为`previews/micro-ui/index.html`；验证记录为`records/micro-ui-validation.json`、`micro-ui-visual-review.json`和`micro-ui-browser-validation.json`。专项重新提取源码符号、检查源/产物SHA与Alpha/画布/锚点，并验证利润、城镇评价、分组动作和出售范围确实不同。浏览器实际加载115张96px图及24/48px显示，检查390px布局。浏览器是离线美术检查器。

Unity建议Sprite/Single、Full Rect、Bilinear、Clamp、无Mip Maps、图集Padding≥4px；平台压缩、点击范围、可访问文本与引擎实际反馈待下一阶段验证。用户美术批准仍pending，本包不宣称Unity运行或业务实现。

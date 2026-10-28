# 产业世界美术

37类原始产业均有独立末态原画，另有8个机械补充部件；5张原生atlas均为1254×1254。512×512正式透明画布中的实际绘画裁切并缩小至不超过384像素，不是原生512/4K细节。逐图记录在source-art/world/industry-a..e.png旁，实际型号/质量未披露，记null。

manifest.json当前列出234张正式Sprite：45静态（37父产业＋8补充件）、111施工派生图、72已绑定机械移动层、6无旧姿态底体。另有6张ownership-mask.png作为遮罩数据、6张新版4×3帧表，目录共246张PNG；帧表每格512×512，可供Multiple导入，不增加原生细节或独立帧数量。37产业按每实例绘制一次父厂区；保留175个gfx兼容索引、60套真实布局、700四阶段状态映射，不在每个gfx tile重复画整厂。静态及绑定层anchorPx=[256,448]、pivotUnity=[0.5,0.125]。

## 已就位机械循环

旧256×256独立部件循环已替换。6组新循环每组12帧、100ms/帧，移动层统一512×512，AttachmentOffset=[0,0]、AttachmentScale=1。全部从实际父建筑选择运动区域：

- 煤矿：真实绞盘轮内部画面转动，外轮缘与支架固定。
- 油井：真实泵梁与驴头围绕支点±1.25°短行程摆动，支架、连杆、前铰盖固定。
- 玩具工厂：装配头窗口中的真实齿轮画面转动，未硬套另一张压机。
- 塑料喷泉：三股实际彩色喷流的内部材质流动，喷口、池体、边界固定。
- 太妃采石场：真实钻轴/螺旋表面运动，支架和外轮廓不整体跳动。
- 蔗糖矿：输送筛选批次中的真实糖粒轻微筛动，木轨与机架固定。

这是确定性遮罩、采样和二维仿射运动，不是新生成3D姿态。8个原生机械补充件仍是独立美术kit，不能假定自动匹配任意父产业。

每组binding记录parentArtId、cleanBaseImage、ownershipMask、锚点/支点、offset、scale、逐帧参数和就位预览。**使用cleanBase＋movingFrame替换原整厂静图，不能同时绘制原厂图，否则会叠出旧机械双影。**

完整图册：previews/world/industry-assembly/index.html；6个整厂GIF、72张全尺寸已就位预览帧、6张12相位表。退役独立循环的文字证据在records/world-production/industry-unbound-clip-retirement.json。

## 检查与Unity建议

234张正式Sprite的尺寸/Alpha/边界/哈希/来源检查0失败；6组安装关系、固定地基、去旧姿态、完整Alpha覆盖和就位帧共330项，0失败。已实际查看全部6组72相位完整厂区图。记录为records/world-production/industries-validation.json及industry-binding-validation.json。

建议Sprite/Single、PPU256、Bilinear、Clamp、sRGB、AlphaIsTransparency；压缩和MaxSize按目标设备检查。遮罩作数据，图层保持同一512画布与Pivot。地形高差、厂区中心校正、遮挡和运行排序待用户美术验收后的Unity接入验证；本阶段未创建Unity工程或Git提交。

重建基础产业/施工后，依次运行build_industry_bindings.py、validate_industries.py、finalize_industry_bindings.py恢复装配合同，不能仅运行旧finalize_industries.py后把独立部件循环当成已绑定成品。


# 载具、公共效果和灾难实体美术交付

项目：云途万里。功能核实日期：2026-10-26（America/New_York）；正式名称与 Logo 的当前使用见[品牌包](../branding/yuntu-wanli/README.md)。功能参考OpenTTD固定提交 `cb7027538ccd8c4c15a592fc8f43b623b3fdf3f8`，成果远端待用户提供。本批只在本对话E盘目录制作；F盘参考库完全只读，未提交或推送Git，未建立Unity工程。

## 实际交付

| 范围 | 当前文件与数量 | 说明 |
|---|---|---|
| 原创车辆家族 | `assets/world/vehicles/families/`，27幅1774×887原生图集 | 6机车、6车厢、5公路、4船舶、6航空；每幅实际包含8个朝向 |
| 家族独立朝向 | 216个512×512透明PNG | 从真实图集按主体与附件归属分离，保留Alpha与抗锯齿；同家族统一缩小率≤1并平移到共同锚点，透明补边不算原生512细节 |
| 原始型号映射 | 256个EngineID，2720个正式型号PNG | 116铁路（35机车/81车厢）、88公路、11船、41航空；按家族作玉绿涂装、轨制底架和货载衍生，不是256幅独立AI原画 |
| 可见货载 | 672个与空载像素不同的朝向状态 | 敞口/平板载具重用已生成货品透明原画；货载是共享绘画部件，不是新生成的8向货物 |
| 密闭载体状态 | 1248个状态条目共享机体 | 客车、厢货、罐车等封闭容器的内容不从外部显露；空/满载在清单明确共用，未用重复静帧夸大动画 |
| 直升机主旋翼 | 停转1张＋机械周期8张，512×512 | 采用实际四叶停转图作源；8相位是刚体旋转与平面投影衍生。原生运动格叶片数不一致，未用于正式运动周期，未调用视频模型 |
| 公共效果 | `assets/world/effects/`共109个正式透明PNG（含灾难） | 完整映射12个EffectVehicle类型；烟、蒸汽、柴油烟、火花、爆炸、故障烟、推土机、泡泡等 |
| 灾难实体 | 完整映射15个DisasterSubType | 实际包括6个派生影子和1个复用旋翼；9幅飞艇/UFO/飞机/直升机状态图＋8幅大小潜艇视图，不把15个类型冒称15个全新身体 |

型号正式索引：[VEHICLE_RUNTIME_MANIFEST.json](VEHICLE_RUNTIME_MANIFEST.json)。功能与源ID合同：[VEHICLE_PRODUCTION_CONTRACT.json](VEHICLE_PRODUCTION_CONTRACT.json)。公共效果：[EFFECT_RUNTIME_MANIFEST.json](EFFECT_RUNTIME_MANIFEST.json)。灾难：[DISASTER_RUNTIME_MANIFEST.json](DISASTER_RUNTIME_MANIFEST.json)。

## 美术预览

- [离线载具/效果验收图册](../previews/vehicles/index.html)：可筛选27家族、轮看8向、查看适用满载状态和31个GIF预览。该页面是图片检查器，不是游戏业务实现。
- [全部家族总览](../previews/vehicles/family-overview.jpg)，八向排版[第1页](../previews/vehicles/facings-1.jpg)、[第2页](../previews/vehicles/facings-2.jpg)、[第3页](../previews/vehicles/facings-3.jpg)。
- [型号与货载样例](../previews/vehicles/model-samples.jpg)、[直升机旋翼装配预览](../previews/vehicles/helicopter-rotor.gif)。
- `previews/world/effects/`包含烟、蒸汽、爆炸、泡泡/吸收/破裂、火焰、灾难原画与影子等GIF。静态方向展示不会伪称完整主体运动动画。

## 源码核实与差异说明

车辆源表与方向审计见[VEHICLE_SOURCE_AUDIT.md](VEHICLE_SOURCE_AUDIT.md)、[VEHICLE_SOURCE_DATA.json](VEHICLE_SOURCE_DATA.json)。车身GetImage按方向取静帧，世界平移、载量半数阈值和附加特效由后续引擎承担；未添加无来源的整车抖动或转轮动画。

`src/effectvehicle_func.h:16–28`为12种效果；`src/effectvehicle.cpp:38–245`核实烟/火花/爆炸相位，255–322核实推土机20段移动表，329–539核实泡泡生成、3种浮动外形、破裂与5帧吸收。20段移动参数保存在推土机资源manifest中，当前只交数据。飞机故障烟和铜矿烟在上游直接调用同一SmokeInit/SmokeTick，因此明确重用crash-smoke美术。小爆炸从大爆炸原画缩小并重采样相位；可选炉火是工业氛围美术，不虚构额外EffectVehicle类型。

`src/disaster_vehicle.h:17–32`为15个子类型，`src/disaster_vehicle.cpp:92–119`确认大部分飞行灾难只用一个固定方向图；大小潜艇各用4张斜向图，并两两复用Direction枚举。飞艇另交完整/坠落/残骸，侦察UFO另交亮/暗状态。射击和命中使用已明确列出的火花/爆炸叠层，影子由实际机体Alpha投影与透明度衍生。

模型差异采用27家族的原创模块方案，未逐一复刻上游159种原像素图轮廓。单轨车厢采用实际绘制的导向底架条，磁悬车厢采用实际绘制的裙板条，按各朝向底边投影；它们是注明的模块组合，最终运行比例及部件遮挡仍需Unity装配检验。

## 导入建议与锚点

全部正式身体/效果为真实RGBA透明PNG。建议Texture Type=Sprite (2D and UI)，Sprite Mode=Single；若后续打包Multiple Atlas，以每条manifest为切片索引；Bilinear过滤，Wrap=Clamp，Alpha Is Transparency开启，初始PPU=100，SpriteAtlas留4px以上外扩，按目标机型实测压缩。九宫格不用于身体或特效，Border为0。所有设置都是建议，尚未导入Unity。

身体统一512画布，地面载具建议锚点(256,350)，航空机体(256,256)，每帧manifest保留最终Pivot。烟与炉火的发射点(256,408)，爆炸/火花/泡泡以中心为原点。直升机主旋翼有逐方向实际绘图测量的安装坐标，停转和运行共用中心。物理轮廓、真实载具长度、地图比例、深度排序、桥隧遮挡与世界轨道中心线仍由下一阶段在Unity核验，不能从静态PNG检查推导为已运行通过。

效果帧数按来源相位准备，4张绘制烟/火花关键帧之间使用明确的预乘Alpha插值；部分泡泡吸收采用缩小/淡出。GIF帧率为美术节奏建议，原始tick规则不在本阶段实现。各效果manifest记录真实绘图源和衍生方式。

## 来源、模型与验收

主风格实际查看并附图：`F:/work/image/designs/mail-ui-v1/01-mail-event.png`、`F:/work/image/designs/team-ui-v2/team-ui-v2.png`；世界投影参考项目内`assets/world-viewport.png`，载具另附代码制作的方向指南（指南不是游戏美术）。F盘不写入任何记录。关联记录保存在本项目[image-reference-associations.md](image-reference-associations.md)。

内置image_gen是本批唯一生图入口。每张原画的`.generation.json`保存当次配置目标、实际提示词、参考路径/哈希、时间、返回路径与原生尺寸。宿主未提供model/quality参数或返回值，实际型号/质量保留null（未确认），不能把配置目标或公告当作实际调用证明。所有切片、涂装、投影、插值、透明度和GIF编码沿源记录追溯，无额外原生高清声称。

[vehicle-fx-validation.json](../records/vehicle-fx-validation.json)逐项检查19438项通过：原始256ID与12/15类型齐全、8向映射、文件存在、RGBA/尺寸/透明边缘、SHA、实际可见货载差异和家族无裁失。已实际查看27幅原画、216向三页图、货载与轨制组合和旋翼位置。[vehicle-fx-browser-validation.json](../records/vehicle-fx-browser-validation.json)9项图片图册检查通过，页面脚本错误0、请求失败0。用户最终画面验收待进行；Unity运行验证尚未开始。

本批正式原画、导出脚本和逐图记录已留在E盘。预览衍生索引为[vehicle-fx-preview-manifest.json](../records/vehicle-fx-preview-manifest.json)。没有新增付费路线、订阅、凭证或预算。

# 属性滑轨实际像素修复 — 2026-10-22

状态：已完成小包与静态检查，等待协调者 guarded install 后运行 Unity 原生重捕。没有启动 Unity、写客户端或操作 Git。

`install-manifest.json` 是唯一安装清单，共 6 项。`source` 相对本目录，`target` 相对客户端；两个既有源码严格校验 `expected_target_sha256`，四个新图片/元文件的目标必须不存在。

根因证据：旧 slider_track/fill 高 23px，中心实心 alpha 仅 6 行；即使 Rect 高 20.8px，有效像素也约 5.43px。现有原生图对应空槽中性像素仅 2 行，HTML 成图为 21 行。详见 `evidence/source-pixel-check.json`。

修复：从指定 HTML 原成图裁取已有底槽/填充像素，紧边界 128×21，保持米金底槽、绿色填充及圆角。两端使用原成图端帽镜像，去除外部纸色；没有 AI 生成或新增手绘细节。逐图裁切来源见 `sprite-provenance.json`。布局保持 20.8 高，thumb 保持 52.8×52.8。

验证脚本依据 DOM 的 33px×1.6 断言 thumb=52.8；额外独立检查 PNG 中心 alpha 覆盖≥90%，再临时用 SetValueWithoutNotify 设为约 40% 并实际 camera 渲染，采样中性槽和绿色填充的有效像素厚度，随后恢复原值。诊断写入 `slider-pixel-diagnostics.txt`。

保留人物 normal/8行到底、宠物 normal/empty/10宠到底，两种分辨率合计 10 张；保留宠物本地草稿/reset、8行底部可见性及其它既有检查。没有调整属性业务数据、权限、RPC 或其它文件。

只读独立检查未发现新增 C# API/编译级明显问题。最终 Unity 编译及截图结果必须由协调者实际执行确认，源像素覆盖通过不等同于原生截图验收完成。

# 云途万里 · Git 交付目标

本游戏使用独立仓库 [luhailong-python/OpenTTD_UI_20261026_060146](https://github.com/luhailong-python/OpenTTD_UI_20261026_060146)，发布分支为 `main`。此目标由当前工作区实际配置的 `origin` 核实，和 OpenTTD 功能参考、美术参考仓库分别管理。

完整美术验收以 [FULL_GAME_ACCEPTANCE_STATUS.json](FULL_GAME_ACCEPTANCE_STATUS.json) 为准。该记录的 `gitSubmitted: false` 描述美术终检当时的状态；当前 Git 交付是否成功，应以远端 `main` 的实际提交和推送回执为准。Unity 接入仍未开展。

资源及其来源记录要求逐字节保持，`.gitattributes` 禁用自动文本换行转换，以保留 PNG、JSON、提示词和清单 SHA256 的一致性。`reference/`、Python 缓存和临时 QA 目录由 `.gitignore` 排除。

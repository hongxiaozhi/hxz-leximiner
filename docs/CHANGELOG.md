# Changelog

## Unreleased

- 固定 LexiMiner 新架构边界：`backend/` + `frontend/` + `leximiner_core/`
- 删除旧的 Streamlit 入口，不再保留旧项目实现
- 将核心协议、分析 facade、导出与文件读取能力收口到 `leximiner_core/`
- 让 `models/` 与 `utils/` 降级为兼容层

## v1.0

- 初始可用版本
- 支持英文文本输入与文件上传
- 支持词汇提取、词形还原、分类、短语提取
- 支持 CSV ZIP 与 Excel 导出

# Changelog

本文件记录 context-compaction 技能的所有版本变更。格式参考 Keep a Changelog。

## [1.0.1] - 2026-09-27

### Changed

- **通用化改造**：从「ZCode 客户端 + StepFun 模型专向」改为适用于所有编码 Agent（ZCode / Claude Code / Codex / Step Code 等）与任意模型
  - 技能名 `stepfun-context-compaction` → `context-compaction`
  - 快照路径 `.zcode/` → 中立的 `.agent/`，并说明可按项目约定改名
  - 新增 §5「安装到各 Agent」多平台路径表
- `references/stepfun-model-context.md` → `references/model-context-limits.md`：StepFun 核实数据迁移保留，新增「保守规则」（未列出模型默认按 16K 窗口）与「扩展方法」（其他模型按官方文档追加，禁止凭记忆填表）
- `scripts/compress_session.py` 去除 StepFun 专有表述，逻辑不变
- 自检脚本新增"专有引用残留"检查

### 修复

- 纯文本解析剥离 `user:/assistant:` 角色前缀（v1.0.0 中前缀被原样保留进素材）

## [1.0.0] - 2026-09-27

### Added

- 初版：SKILL.md（5 步压缩流程 + 快照模板 + 触发条件）
- StepFun 模型上下文窗口阈值表（step-2-16k 至 Step 3.7 Flash，2026-09 核实）
- 机械压缩脚本 `compress_session.py`（JSONL/纯文本双格式，零第三方依赖）
- ZCode 规则合规校验脚本与双格式测试样本

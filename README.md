# context-compaction — 通用 Agent 上下文自动压缩技能

## 简介

适用于**任意编码 Agent 与任意模型**（ZCode、Claude Code、Codex、Step Code 等）的上下文压缩技能：长会话自动产出结构化上下文快照 + 机械压缩素材，新会话一句话无损续接。

- **自动触发** —— 上下文达模型窗口 70%、工具输出堆积、用户要求压缩上下文或出现超限告警时触发。
- **机械压缩** —— `scripts/compress_session.py` 剥离工具输出噪声，保留用户消息与 assistant 要点。
- **语义快照** —— 模型按内置模板生成 `.agent/context-snapshot.md`，目标 ≤2KB。
- **无损续接** —— 新会话读取快照继续工作；再次压缩时增量合并，不覆盖历史「关键决策」条目。
- **零第三方依赖** —— 脚本仅用 Python 标准库，JSONL 与纯文本转写均可解析。
- **不碰客户端数据** —— 快照一律写在项目内，`.agent/` 可按项目既有约定改名（如 `.zcode/`、`.claude/`）。

> SKILL.md 的 frontmatter 约定：`description` 用英文（供模型检索与触发判定），`when_to_use` 与正文用中文。

## 工作原理

1. **触发**：上下文达模型窗口 70%、工具输出堆积、用户要求压缩、超限告警（满足任一）。
2. **机械压缩**：`scripts/compress_session.py` 剥离工具输出噪声（JSONL/纯文本转写均可），保留用户消息与 assistant 要点。
3. **语义压缩**：模型按内置模板生成 `.agent/context-snapshot.md` 快照（任务目标/状态/关键决策/文件/下一步/风险），目标 ≤2KB。
4. **续接**：新会话只需「读取快照继续工作」；再次压缩时增量合并。

模型窗口与 70% 触发线见 [references/model-context-limits.md](references/model-context-limits.md)（已核实 StepFun 全系；其他模型按保守规则处理）。

## 安装

将 `context-compaction/` 目录（或本仓库整目录，SKILL.md 所在目录即技能根）拷入对应 Agent 的用户级技能目录：

| Agent | 目标路径 |
|---|---|
| ZCode | `~/.zcode/skills/context-compaction/` |
| Claude Code | `~/.claude/skills/context-compaction/` |
| Codex CLI / 其他 | 以各 Agent 文档为准（含 SKILL.md 的目录放入其技能搜索路径） |

安装后在各 Agent 技能管理界面刷新启用。卸载时删除对应技能目录即可，项目内的上下文快照与机械压缩素材不受影响。

## 使用

自动触发无需操作：满足「工作原理」中的触发条件时由 Agent 执行压缩。手动触发只需对 Agent 说明「压缩上下文 / 保存进度 / 交接新会话」。

最小示例——先跑机械压缩脚本（会话记录文件可为 JSONL 或纯文本转写）：

```bash
python scripts/compress_session.py <会话记录文件> --out .agent/snapshot-material.md
```

随后模型基于当前上下文与素材写出快照，内容形如（节选）：

```markdown
# 上下文快照 <YYYY-MM-DD HH:MM> <Agent/模型名>
## 任务目标
<一段话：最终要交付什么，验收标准是什么>
## 当前状态
- [x] 已完成：<条目 + 关键产出路径>
- [ ] 进行中：<条目 + 卡点>
## 关键决策与约束
- <决策/约定/用户偏好，逐条列出，含原因一句话>
## 下一步
<立即要做的 1-3 件事，按顺序>
```

续接：新会话首轮只需说「读取 .agent/context-snapshot.md 继续工作」。

## 自检

```bash
python tests/validate_skill.py                       # SKILL.md 合规校验
python scripts/compress_session.py tests/fixture.jsonl --out /tmp/out.md   # 脚本冒烟
python scripts/compress_session.py tests/fixture.txt --out /tmp/out2.md
```

## 版本

版本记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

[AGPL-3.0-only](./LICENSE)

历史 MIT 文本与版权声明保留在 [LICENSE-MIT](./LICENSE-MIT)。

© 2026 Neriah

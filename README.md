# context-compaction — 通用 Agent 上下文自动压缩技能

适用于**任意编码 Agent 与任意模型**（ZCode、Claude Code、Codex、Step Code 等）的上下文压缩技能：长会话自动产出结构化快照 + 机械压缩素材，新会话一句话无损续接。

## 工作原理

1. **触发**：上下文达模型窗口 70%、工具输出堆积、用户要求压缩、超限告警（满足任一）。
2. **机械压缩**：`scripts/compress_session.py` 剥离工具输出噪声（JSONL/纯文本转写均可），保留用户消息与 assistant 要点。
3. **语义压缩**：模型按内置模板生成 `.agent/context-snapshot.md` 快照（任务目标/状态/关键决策/文件/下一步/风险），目标 ≤2KB。
4. **续接**：新会话只需"读取快照继续工作"；再次压缩时增量合并。

模型窗口与 70% 触发线见 `references/model-context-limits.md`（已核实 StepFun 全系；其他模型按保守规则处理）。

## 安装

将 `context-compaction/` 目录（或本仓库整目录，SKILL.md 所在目录即技能根）拷入对应 Agent 的用户级技能目录：

| Agent | 目标路径 |
|---|---|
| ZCode | `~/.zcode/skills/context-compaction/` |
| Claude Code | `~/.claude/skills/context-compaction/` |
| Codex CLI / 其他 | 以各 Agent 文档为准（含 SKILL.md 的目录放入其技能搜索路径） |

安装后在各 Agent 技能管理界面刷新启用。

## 自检

```bash
python tests/validate_skill.py                       # SKILL.md 合规校验
python scripts/compress_session.py tests/fixture.jsonl --out /tmp/out.md   # 脚本冒烟
python scripts/compress_session.py tests/fixture.txt --out /tmp/out2.md
```

## 版本

见 [CHANGELOG.md](CHANGELOG.md)。当前 **v1.0.1**。

## License

[AGPL-3.0-only](./LICENSE)

历史 MIT 文本与版权声明保留在 [LICENSE-MIT](./LICENSE-MIT)。

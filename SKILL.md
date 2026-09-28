---
name: context-compaction
description: "Auto-trigger when a coding-agent session grows long: context usage nears the model window (default 70%), tool outputs pile up, the user asks to 压缩上下文/压缩会话/保存进度, or a context-limit warning appears. Works with any model and any coding agent (ZCode, Claude Code, Codex, Step Code, etc.). Produces a structured context snapshot file plus a mechanical transcript compaction so work continues in a fresh session without losing goals, decisions, or file state."
when_to_use: "会话上下文接近当前模型窗口上限、工具输出大量堆积、用户要求压缩上下文/保存进度/交接新会话、出现上下文超限告警，或长任务进入无人值守阶段前需要交接现场时"
license: AGPL-3.0-only
---

# 通用 Agent 上下文自动压缩（Context Compaction）

本技能适用于**任意编码 Agent 与任意模型**（ZCode、Claude Code、Codex、Step Code 等），在长会话中对上下文做**结构化压缩**：产出一份可续接的快照文件 + 一份机械压缩的对话素材，让新会话能无损恢复工作现场。

## 1. 触发时机（满足任一即执行本技能）

1. 上下文用量达到当前模型窗口的 **70%**（已知模型窗口见 `references/model-context-limits.md`；未列出的模型按该文件 §保守规则 处理，默认按 16K 窗口估算）。
2. 工具输出在近期轮次中大量堆积（如连续读取大文件、长日志、多次失败重试）。
3. 用户明确要求：压缩上下文 / 压缩会话 / 保存进度 / 交接新会话。
4. 运行时出现上下文超限或截断告警。
5. 长任务（/goal、/cron、后台任务类）即将进入无人值守阶段前，主动做一次预防性压缩。

## 2. 压缩流程（严格按序执行）

### Step 1 盘点
统计当前会话的构成：用户消息数、工具调用次数、最大的几段工具输出、已修改/新建的文件清单。

### Step 2 机械压缩（脚本，先跑）
用随附脚本剥离工具噪声，得到压缩素材：

```bash
python scripts/compress_session.py <会话记录文件> --out .agent/snapshot-material.md
```

- 输入支持 JSONL（每行一个 `{role, content}` 消息对象）或纯文本/Markdown 转写。
- 保留：全部用户消息（超长截断到 8000 字符）、assistant 消息的首尾要点；工具输出压成单行摘要。
- 无法拿到会话记录文件时**跳过本步**，直接进入 Step 3（凭当前上下文做语义压缩即可）。

### Step 3 语义压缩（快照，核心产出）
基于当前上下文与 Step 2 素材，按 §3 模板生成快照，写入项目根 **`.agent/context-snapshot.md`**（已存在则先读取旧快照，合并增量，不覆盖历史"关键决策"条目）。

### Step 4 交付告知
向用户汇报：快照路径、压缩前后规模对比（估算 token）、新会话恢复方式（§4）。

### Step 5 重启续接
提示用户开启新会话，新会话首轮仅需说"读取 .agent/context-snapshot.md 继续工作"。

## 3. 快照模板（写入 .agent/context-snapshot.md，目标 ≤2KB）

```markdown
# 上下文快照 <YYYY-MM-DD HH:MM> <Agent/模型名>
## 任务目标
<一段话：最终要交付什么，验收标准是什么>
## 当前状态
- [x] 已完成：<条目 + 关键产出路径>
- [ ] 进行中：<条目 + 卡点>
- [ ] 待办：<条目>
## 关键决策与约束
- <决策/约定/用户偏好，逐条列出，含原因一句话>
## 文件与命令
- 重要文件：<路径 → 一句话说明>
- 常用命令：<构建/测试/运行命令>
## 下一步
<立即要做的 1-3 件事，按顺序>
## 风险与未决
<未解决的问题、待验证的假设>
```

**红线**：快照必须保留"关键决策与约束"的全部条目——这是新会话最易丢失、代价最高的信息；工具输出只保留结论，不保留原文。

## 4. 新会话恢复方式

1. 读取 `.agent/context-snapshot.md`。
2. 按快照"下一步"继续，不需要重读历史会话。
3. 再次触发压缩时，旧快照与新进展合并（见 Step 3），保持快照始终为最新单文件事实源。

## 5. 安装到各 Agent

技能目录（含 SKILL.md 的整个目录）拷入对应 Agent 的用户级技能目录：

| Agent | 技能目录（用户级） |
|---|---|
| ZCode | `~/.zcode/skills/context-compaction/` |
| Claude Code | `~/.claude/skills/context-compaction/` |
| Codex CLI / 其他 | 以各 Agent 文档为准，原则：**含 SKILL.md 的目录**放入其技能搜索路径 |

安装后在各 Agent 的技能管理界面刷新/重启生效。

## 6. 注意事项

- 各模型窗口与推荐触发阈值**必须**先查 `references/model-context-limits.md`；未列出的模型按保守规则估算，不要凭记忆假设。
- 机械压缩脚本只做降噪，**语义压缩（快照）永远由模型完成**，二者不可互相替代。
- 压缩操作本身要省 token：不回读完整历史，优先用脚本产物；快照写入失败时退化为直接在回复中输出快照内容让用户保存。
- 本技能不修改任何客户端数据目录（`~/.zcode`、`~/.claude` 等只读或不碰），快照一律写在项目内；`.agent/` 目录可按项目既有约定改名（如 `.zcode/`、`.claude/`），改名时同步修改本文档中的路径引用。

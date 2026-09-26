#!/usr/bin/env python3
"""compress_session.py — 会话记录机械压缩（context-compaction 技能附随脚本，适用于任意编码 Agent）

剥离工具输出噪声，生成供模型做语义压缩的素材文件。
只做机械降噪，不做语义总结（语义压缩由模型按 SKILL.md 完成）。

用法:
    python compress_session.py <session_file> [--out 输出路径] [--max-chars N] [--user-max-chars N]

输入格式（自动识别）:
    1. JSONL: 每行一个消息对象 {"role": "...", "content": "..."}，
       content 允许为字符串或 [{"type": "...", "text": "..."}] 数组（OpenAI 兼容格式）。
    2. 纯文本 / Markdown: 按空行分块处理。

输出: Markdown 素材文件，含用户消息（截断保留）、assistant 要点、工具输出单行摘要。
仅使用标准库；UTF-8 读写；Windows 兼容。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_ROLES = {"tool", "tool_result", "function", "system_tool"}
DEFAULT_MAX_CHARS = 2000       # assistant/单条消息保留上限
DEFAULT_USER_MAX_CHARS = 8000  # 用户消息保留上限（更完整）


def extract_text(content) -> str:
    """从 content（字符串或多模态数组）提取纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") in ("text", "output_text") and "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item and isinstance(item["content"], str):
                    parts.append(item["content"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return "" if content is None else str(content)


def clip(text: str, limit: int) -> str:
    """超长截断：保留首尾，中间标注省略。"""
    text = text.strip()
    if len(text) <= limit:
        return text
    head, tail = limit * 2 // 3, limit // 3
    return f"{text[:head]}\n…[截断 {len(text) - limit} 字符]…\n{text[-tail:]}"


def one_line(text: str, limit: int = 160) -> str:
    flat = re.sub(r"\s+", " ", text.strip())
    return flat[:limit] + ("…" if len(flat) > limit else "")


def looks_jsonl(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                return isinstance(obj, dict) and ("role" in obj or "messages" in obj)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return False


def parse_jsonl(path: Path):
    """解析 JSONL；返回 (role, text) 列表。"""
    messages = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "messages" in obj and isinstance(obj["messages"], list):
                messages.extend(obj["messages"])
            elif "role" in obj:
                messages.append(obj)
    out = []
    for m in messages:
        role = str(m.get("role", "unknown")).lower()
        text = extract_text(m.get("content"))
        if m.get("tool_calls"):
            names = [tc.get("function", {}).get("name", "?") if isinstance(tc, dict) else "?"
                     for tc in m["tool_calls"]]
            text = f"[工具调用: {', '.join(names)}] " + text
        out.append((role, text))
    return out


def parse_plaintext(path: Path):
    """纯文本回退：按空行分块，块首行视为角色提示。"""
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    out = []
    role_pat = re.compile(r"^(user|assistant|助手|ai|系统|system)\s*[:：]\s*", re.I)
    for b in blocks:
        first = b.splitlines()[0]
        m = role_pat.match(first)
        if m:
            role = m.group(1).lower()
            if role in ("助手", "ai"):
                role = "assistant"
            elif role == "系统":
                role = "system"
            text = role_pat.sub("", b, count=1)
        else:
            role, text = "assistant", b
        out.append((role, text))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="会话记录机械压缩")
    ap.add_argument("input", help="会话记录文件（JSONL 或纯文本/Markdown）")
    ap.add_argument("--out", default=None, help="输出路径（默认 <输入名>.compact.md）")
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    ap.add_argument("--user-max-chars", type=int, default=DEFAULT_USER_MAX_CHARS)
    args = ap.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"错误: 输入文件不存在: {src}", file=sys.stderr)
        return 1

    messages = parse_jsonl(src) if looks_jsonl(src) else parse_plaintext(src)
    if not messages:
        print("警告: 未解析出任何消息，输出空骨架。", file=sys.stderr)

    out_path = Path(args.out) if args.out else src.with_suffix(".compact.md")
    stats = {"user": 0, "assistant": 0, "tool": 0}
    lines = [
        "# 会话机械压缩素材",
        "",
        f"- 来源: `{src.name}`",
        f"- 生成: 机械压缩（工具输出已降噪），语义快照请由模型按 SKILL.md §3 模板完成",
        "",
    ]

    for role, text in messages:
        if not text.strip():
            continue
        if role in TOOL_ROLES:
            stats["tool"] += 1
            lines.append(f"- 【工具输出】{one_line(text)}")
        elif role == "user":
            stats["user"] += 1
            lines.append(f"## 用户 #{stats['user']}\n\n{clip(text, args.user_max_chars)}\n")
        else:
            stats["assistant"] += 1
            lines.append(f"### assistant #{stats['assistant']}\n\n{clip(text, args.max_chars)}\n")

    lines.insert(4, f"- 统计: 用户 {stats['user']} 条 / assistant {stats['assistant']} 条 / 工具输出 {stats['tool']} 条（已单行化）")
    lines.insert(5, "")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    in_kb = src.stat().st_size / 1024
    out_kb = out_path.stat().st_size / 1024
    print(f"完成: {out_path} ({out_kb:.1f} KB, 原始 {in_kb:.1f} KB, 压缩至 {out_kb / in_kb * 100:.0f}%)" if in_kb else f"完成: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

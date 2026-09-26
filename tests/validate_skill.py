"""context-compaction 技能合规自检（依据 ZCode skill 规则，各 Agent 规则为其超集/近似）"""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent  # 仓库根 = 技能根
skill_md = root / "SKILL.md"
text = skill_md.read_text(encoding="utf-8")
errors = []

m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not m:
    errors.append("frontmatter 缺失")
else:
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)", fm, re.M)
    desc = re.search(r'^description:\s*"?(.+?)"?\s*$', fm, re.M)
    if not name:
        errors.append("name 缺失")
    if not desc:
        errors.append("description 缺失")
    else:
        d = desc.group(1)
        if len(d) > 1024:
            errors.append(f"description 超限: {len(d)} > 1024")
        else:
            print(f"description 长度: {len(d)} / 1024 OK")
    if name:
        print("name:", name.group(1))
        if not re.match(r"^[a-z0-9][a-z0-9._-]*$", name.group(1)):
            errors.append("name 含不安全字符")
    body = text[m.end():]
    kb = len(body.encode("utf-8")) / 1024
    print(f"正文大小: {kb:.1f} KB / 100 KB")
    if kb >= 100:
        errors.append("正文超 100KB")
    if name and root.name != name.group(1) and root.name != name.group(1) + "-skill":
        print(f"提示: 仓库名 {root.name}，技能名 {name.group(1)}（拷贝安装时目录名应改为技能名）")
    for rel in ("references/model-context-limits.md", "scripts/compress_session.py"):
        if not (root / rel).is_file():
            errors.append(f"缺少附随文件 {rel}")
    # 快照路径一致性：正文与脚本示例不得残留旧专有路径
    for legacy in (".zcode/context-snapshot", "stepfun-context-compaction"):
        if legacy in body:
            errors.append(f"正文残留专有引用: {legacy}")

if errors:
    print("FAIL:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("SKILL.md COMPLIANT")

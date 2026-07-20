#!/usr/bin/env python3
"""
扫描 doc/ 目录下所有 Markdown 文档的 YAML frontmatter。

支持：
  - 按状态过滤（活跃 / 非活跃）
  - triage-first 加载策略（活跃 + 最近 N 篇完成）
  - 分类统计
  - 重复检测
  - frontmatter 字段验证
  - JSON / 表格双输出格式

用法:
    # 列出所有文档及其状态（默认表格输出）
    python3 scan_docs.py --dir doc/research/

    # 仅显示活跃文档（in-progress / in-review）
    python3 scan_docs.py --dir doc/research/ --active-only

    # triage 模式（活跃 + 最近 3 篇 complete）
    python3 scan_docs.py --dir doc/research/ --triage

    # JSON 输出
    python3 scan_docs.py --dir doc/research/ --json

    # 递归扫描所有子目录
    python3 scan_docs.py --dir doc/ --recursive --summary

    # 检查重复文档
    python3 scan_docs.py --dir doc/ --check-duplicates

    # 验证 frontmatter 必填字段
    python3 scan_docs.py --dir doc/ --validate
"""

import argparse
import json
import os
import sys
import yaml
from collections import defaultdict
from datetime import date, datetime
from typing import Optional


class _JSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 date/datetime 对象。"""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


DOC_EXTENSIONS = {".md", ".mdx"}

ACTIVE_STATES = {"draft", "in-progress", "in-review", "proposed", "accepted"}
TERMINAL_STATES = {"complete", "implemented", "approved", "confirmed"}

IGNORE_FILES = {"README.md", "AGENTS.md", "GLOSSARY.md", "INDEX.md"}


def parse_frontmatter(filepath: str) -> Optional[dict]:
    """解析 Markdown 文件的 YAML frontmatter。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  无法读取 {filepath}: {e}", file=sys.stderr)
        return None

    if not content.startswith("---"):
        return {"_error": "缺少 YAML frontmatter"}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"_error": "YAML frontmatter 格式错误"}

    try:
        fm = yaml.safe_load(parts[1])
        if fm is None:
            fm = {}
        fm["_body_length"] = len(parts[2].strip())
        return fm
    except yaml.YAMLError as e:
        return {"_error": f"YAML 解析错误: {e}"}


def scan_directory(directory: str, recursive: bool = False) -> dict:
    """扫描目录，返回 {relative_path: frontmatter}。"""
    result = {}
    for root, dirs, files in os.walk(directory):
        # 跳过隐藏目录和 __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in DOC_EXTENSIONS:
                continue
            if fname in IGNORE_FILES:
                continue

            full = os.path.join(root, fname)
            rel = os.path.relpath(full, directory)
            fm = parse_frontmatter(full)
            if fm is not None:
                result[rel] = fm

        if not recursive:
            break  # 仅扫描当前层级，不深入子目录

    return result


def collect_all(root_dir: str) -> list[tuple[str, str, dict]]:
    """递归收集所有子目录的文档。返回 [(category, rel_path, frontmatter), ...]"""
    all_docs = []
    for entry in sorted(os.listdir(root_dir)):
        sub = os.path.join(root_dir, entry)
        if not os.path.isdir(sub) or entry.startswith("."):
            continue
        docs = scan_directory(sub, recursive=False)
        for rel, fm in docs.items():
            all_docs.append((entry, rel, fm))
    return all_docs


def is_active(fm: dict) -> bool:
    """判断文档是否为活跃状态。"""
    status = fm.get("status", "").strip() if fm.get("status") else ""
    if not status:
        return False
    return status in ACTIVE_STATES


def is_complete(fm: dict) -> bool:
    """判断文档是否已完成。"""
    status = fm.get("status", "").strip() if fm.get("status") else ""
    if not status:
        return False
    return status in TERMINAL_STATES


def format_table(docs: list[tuple[str, dict]]) -> str:
    """格式化为表格。"""
    if not docs:
        return "(无匹配文档)"

    header = f"{'文档':<50} {'状态':<14} {'创建日期':<12} {'更新日期':<12} {'作者':<12}"
    sep = "-" * 110
    lines = [header, sep]

    for path, fm in docs:
        status = str(fm.get("status", "-"))
        created = str(fm.get("created", "-"))
        updated = str(fm.get("updated", "-"))
        author = str(fm.get("author", "-"))
        lines.append(f"{path:<50} {status:<14} {created:<12} {updated:<12} {author:<12}")

    return "\n".join(lines)


# ---- 子命令实现 ----

def cmd_list(args) -> int:
    """列出所有文档。"""
    docs = scan_directory(args.dir, recursive=args.recursive)

    if args.json:
        # 移除 _body_length 以减少噪音（除非 verbose）
        clean = {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                 for k, v in docs.items()}
        print(json.dumps(clean, ensure_ascii=False, indent=2, cls=_JSONEncoder))
        return 0

    sorted_items = sorted(docs.items(), key=lambda x: x[0])
    fm_list = [(path, fm) for path, fm in sorted_items]

    print(format_table(fm_list))
    print(f"\n共 {len(fm_list)} 篇文档\n")
    return 0


def cmd_active_only(args) -> int:
    """仅显示活跃文档。"""
    docs = scan_directory(args.dir, recursive=args.recursive)
    active = {path: fm for path, fm in docs.items() if is_active(fm)}

    if args.json:
        print(json.dumps(active, ensure_ascii=False, indent=2, cls=_JSONEncoder))
        return 0

    sorted_items = sorted(active.items(), key=lambda x: x[0])
    print(format_table([(p, fm) for p, fm in sorted_items]))
    print(f"\n活跃文档: {len(sorted_items)} 篇（共 {len(docs)} 篇）\n")
    return 0


def cmd_triage(args) -> int:
    """Triage-first 加载策略。"""
    docs = scan_directory(args.dir, recursive=args.recursive)
    recent_n = args.recent or 3

    active = {path: fm for path, fm in docs.items() if is_active(fm)}
    completed = {path: fm for path, fm in docs.items() if is_complete(fm)}

    # 按 updated 日期排序取最近 N 篇
    sorted_completed = sorted(
        completed.items(),
        key=lambda x: str(x[1].get("updated", "")),
        reverse=True
    )[:recent_n]

    result = active.copy()
    for path, fm in sorted_completed:
        if path not in result:
            result[path] = fm

    print("📋 Triage-First 加载列表:\n")
    print("--- 活跃文档（始终加载）---")
    if active:
        print(format_table([(p, fm) for p, fm in sorted(active.items())]))
    else:
        print("  (无活跃文档)")

    print(f"\n--- 最近 {recent_n} 篇完成文档（按需加载）---")
    if sorted_completed:
        print(format_table([(p, fm) for p, fm in sorted_completed]))
    else:
        print("  (无完成文档)")

    stale = len(docs) - len(result)
    print(f"\n总计: {len(docs)} 篇 → 加载 {len(result)} 篇，跳过 {stale} 篇\n")
    return 0


def cmd_summary(args) -> int:
    """按分类统计。"""
    root_dir = args.dir.rstrip("/")
    all_docs = collect_all(root_dir)

    if not all_docs:
        print("(无文档)")
        return 0

    # 按分类分组统计
    cat_counts = defaultdict(lambda: {"total": 0, "active": 0, "complete": 0, "stale": 0})
    for category, _, fm in all_docs:
        cat_counts[category]["total"] += 1
        if is_active(fm):
            cat_counts[category]["active"] += 1
        elif is_complete(fm):
            cat_counts[category]["complete"] += 1
        else:
            cat_counts[category]["stale"] += 1

    print(f"{'分类':<25} {'总数':<6} {'活跃':<6} {'完成':<6} {'非活跃':<6}")
    print("-" * 55)
    grand_total = grand_active = grand_complete = grand_stale = 0
    for cat in sorted(cat_counts):
        c = cat_counts[cat]
        print(f"{cat:<25} {c['total']:<6} {c['active']:<6} {c['complete']:<6} {c['stale']:<6}")
        grand_total += c["total"]
        grand_active += c["active"]
        grand_complete += c["complete"]
        grand_stale += c["stale"]

    print("-" * 55)
    print(f"{'合计':<25} {grand_total:<6} {grand_active:<6} {grand_complete:<6} {grand_stale:<6}\n")
    return 0


def cmd_check_duplicates(args) -> int:
    """检查重复文档（基于文件名相似度或标题）。"""
    all_docs = collect_all(args.dir.rstrip("/"))

    # 按文件名关键词分组
    by_stem = defaultdict(list)
    for cat, rel, fm in all_docs:
        stem = os.path.splitext(os.path.basename(rel))[0].lower()
        # 去掉日期前缀和序号前缀
        parts = stem.split("-", 1)
        if parts[0].isdigit() or (len(parts[0]) == 8 and parts[0].isdigit()):
            stem = parts[1] if len(parts) > 1 else stem
        by_stem[stem].append(f"{cat}/{rel}")

    duplicates = {k: v for k, v in by_stem.items() if len(v) > 1}

    if duplicates:
        print("⚠️  发现疑似重复文档:\n")
        for stem, files in sorted(duplicates.items()):
            print(f"  关键词: {stem}")
            for f in files:
                print(f"    - {f}")
            print()
        return 1
    else:
        print("✅ 未发现重复文档\n")
        return 0


def cmd_validate(args) -> int:
    """验证 frontmatter 必填字段。"""
    docs = scan_directory(args.dir, recursive=args.recursive)
    required_fields = ["status", "created", "updated", "author", "tags"]
    errors = []

    for path, fm in sorted(docs.items()):
        err = fm.get("_error")
        if err:
            errors.append((path, err))
            continue
        missing = [f for f in required_fields if not fm.get(f)]
        if missing:
            errors.append((path, f"缺少字段: {', '.join(missing)}"))

    if errors:
        print(f"❌ 发现 {len(errors)} 个问题:\n")
        for path, err in errors:
            print(f"  {path}: {err}")
        print()
        return 1
    else:
        print(f"✅ 所有 {len(docs)} 篇文档 frontmatter 验证通过\n")
        return 0


# ---- CLI 入口 ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="扫描 doc/ 目录文档的 YAML frontmatter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", help="子命令")

    # list
    p_list = sub.add_parser("list", help="列出所有文档")
    p_list.add_argument("--dir", required=True, help="扫描目录")
    p_list.add_argument("--recursive", "-r", action="store_true", help="递归扫描子目录")
    p_list.add_argument("--json", action="store_true", help="JSON 输出")

    # active
    p_active = sub.add_parser("active", help="仅活跃文档")
    p_active.add_argument("--dir", required=True)
    p_active.add_argument("--recursive", "-r", action="store_true")
    p_active.add_argument("--json", action="store_true", help="JSON 输出")

    # triage
    p_triage = sub.add_parser("triage", help="Triage-first 加载列表")
    p_triage.add_argument("--dir", required=True)
    p_triage.add_argument("--recursive", "-r", action="store_true")
    p_triage.add_argument("--recent", type=int, default=3, help="最近完成文档数量（默认 3）")

    # summary
    p_summary = sub.add_parser("summary", help="分类统计")
    p_summary.add_argument("--dir", required=True, help="doc/ 根目录")

    # check-duplicates
    p_dup = sub.add_parser("check-duplicates", help="检查重复文档")
    p_dup.add_argument("--dir", required=True, help="doc/ 根目录")

    # validate
    p_val = sub.add_parser("validate", help="验证 frontmatter 必填字段")
    p_val.add_argument("--dir", required=True)
    p_val.add_argument("--recursive", "-r", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmds = {
        "list": cmd_list,
        "active": cmd_active_only,
        "triage": cmd_triage,
        "summary": cmd_summary,
        "check-duplicates": cmd_check_duplicates,
        "validate": cmd_validate,
    }

    handler = cmds.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"未知命令: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

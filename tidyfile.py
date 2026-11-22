#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tidyfile —— 一键整理乱糟糟的文件夹 🧹

一个零依赖、单文件的 Python 命令行小工具:
把堆满杂物的下载文件夹、桌面,按「文件类型 / 日期」自动归档。
支持预览(--dry-run)和一键撤销(--undo),放心大胆地整理。

项目主页: https://github.com/shanzbyte07/tidyfile
许可证: MIT
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"

# ============================================================
# 分类配置:扩展名(小写) -> 分类名
# 想自定义分类?在这里加一行就行,例如 "设计": (".fig", ".xd"),
# ============================================================

CATEGORIES = {
    "图片": (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico",
             ".tif", ".tiff", ".heic", ".raw"),
    "文档": (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
             ".txt", ".md", ".csv", ".rtf", ".epub"),
    "视频": (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".rmvb"),
    "音频": (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".ape"),
    "压缩包": (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".cab"),
    "程序": (".exe", ".msi", ".bat", ".cmd", ".apk", ".dmg", ".deb", ".rpm", ".pkg"),
    "代码": (".py", ".js", ".ts", ".html", ".htm", ".css", ".java", ".c", ".cpp",
             ".go", ".rs", ".php", ".sh", ".sql", ".json", ".xml", ".yml", ".yaml", ".toml"),
    "字体": (".ttf", ".otf", ".woff", ".woff2"),
    "种子": (".torrent"),
}

OTHER_CATEGORY = "其他"
CATEGORY_FOLDERS = set(CATEGORIES) | {OTHER_CATEGORY}   # 分类文件夹名集合

CATEGORY_EMOJI = {
    "图片": "🖼️", "文档": "📄", "视频": "🎬", "音频": "🎵", "压缩包": "📦",
    "程序": "⚙️", "代码": "💻", "字体": "🔤", "种子": "🧲", "其他": "🗂️",
}

# 扩展名 -> 分类 的查找表(启动时由 CATEGORIES 自动生成)
EXT_TO_CATEGORY = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}

MANIFEST_NAME = ".tidyfile-manifest.json"  # 整理"账本":记录每次移动,用于撤销

# 按"年月"整理时,分类文件夹名的匹配模式(用于撤销后清理空文件夹)
DATE_FOLDER_RE = re.compile(r"^\d{4}年\d{2}月$")

# 程序文件自己的绝对路径,整理时要跳过它(别把自己也整理了 😄)
SCRIPT_PATH = Path(__file__).resolve() if "__file__" in globals() else None


# ============================================================
# 终端输出的小工具
# ============================================================

class Style:
    """ANSI 终端颜色(不支持彩色的终端会自动降级,不影响功能)"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    END = "\033[0m"


def setup_console():
    """让 Windows 老终端也能显示颜色和中文"""
    if os.name == "nt":
        os.system("")  # 空命令,激活 Windows 终端的 ANSI 转义支持
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding and stream.encoding.lower() not in ("utf-8", "utf8"):
            try:
                stream.reconfigure(encoding="utf-8")
            except AttributeError:
                pass  # Python 3.6 及更早版本没有 reconfigure,忽略即可


def human_size(n: float) -> str:
    """把字节数变成人看得懂的字符串,例如 1536000 -> 1.5MB"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{int(n)}B" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ============================================================
# 核心逻辑:收集文件 -> 制定计划 -> 执行移动
# ============================================================

def find_category(path: Path) -> str:
    """根据扩展名判断文件属于哪个分类"""
    return EXT_TO_CATEGORY.get(path.suffix.lower(), OTHER_CATEGORY)


def collect_files(root: Path, recursive: bool, target: Path) -> list:
    """
    收集要整理的文件。
    自动跳过:隐藏文件、分类文件夹、__pycache__、程序自己。
    recursive=True 时连子文件夹里的文件也一起收集。
    """
    files = []
    if recursive:
        # os.walk 逐层遍历目录;修改 dirnames 可以"剪枝",让遍历跳过某些文件夹
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".")
                and d != "__pycache__"
                and d not in CATEGORY_FOLDERS
                and not DATE_FOLDER_RE.match(d)
                and Path(dirpath, d).resolve() != target
            ]
            files.extend(Path(dirpath, name) for name in filenames)
    else:
        files.extend(entry for entry in root.iterdir() if entry.is_file())

    # 最后一道过滤:隐藏文件、账本本身、程序自己
    return [
        f for f in files
        if not f.name.startswith(".")
        and f.name != MANIFEST_NAME
        and (SCRIPT_PATH is None or f.resolve() != SCRIPT_PATH)
    ]


def unique_path(dest: Path, taken: set) -> Path:
    """
    目标位置已经有同名文件时,自动改名避免覆盖:
    报告.pdf -> 报告 (1).pdf -> 报告 (2).pdf ...
    taken 是这一轮里"计划占用"的文件名集合。
    """
    if dest.name not in taken and not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 1
    while True:
        candidate = dest.with_name(f"{stem} ({n}){suffix}")
        if candidate.name not in taken and not candidate.exists():
            return candidate
        n += 1


def plan_moves(files: list, target: Path, by_date: bool) -> list:
    """
    决定每个文件要移动到哪里。
    返回 [(源路径, 目标路径, 文件大小), ...]
    """
    taken = {}  # 目标文件夹 -> 该文件夹里已占用的文件名
    moves = []
    for f in files:
        if by_date:
            # 按"年月"分组,用文件的最后修改时间(适合照片等按时间归档)
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
            except OSError:
                mtime = datetime.now()
            folder = f"{mtime.year}年{mtime.month:02d}月"
        else:
            folder = find_category(f)
        dest_dir = target / folder
        used = taken.setdefault(dest_dir, set())
        dest = unique_path(dest_dir / f.name, used)
        used.add(dest.name)
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        moves.append((f, dest, size))
    return moves


def execute_moves(moves: list, dry_run: bool, verbose: bool):
    """
    执行移动计划。
    dry_run=True 时只"假装"移动,用于预览。
    返回 (已移动列表, 失败列表)。
    """
    moved, skipped = [], []
    total = len(moves)
    # 只在非详细模式、真正移动、且输出是终端时,才显示单行进度
    animate = sys.stdout.isatty() and not verbose and not dry_run

    for i, (src, dest, size) in enumerate(moves, 1):
        try:
            if dest.exists():
                # 计划赶不上变化:执行前再防一次重名
                dest = unique_path(dest, set())
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
            moved.append((src, dest, size))
            if verbose:
                mark = "📌" if dry_run else "✔"
                print(f"  {mark} {src.name} {Style.DIM}→{Style.END} "
                      f"{dest.parent.name}/{dest.name}")
        except (OSError, PermissionError) as e:
            skipped.append((src, e))
        if animate:
            print(f"\r  ⏳ 进度 {i}/{total}", end="", flush=True)
    if animate:
        print()

    return moved, skipped


# ============================================================
# 输出报告
# ============================================================

def print_summary(moved: list, skipped: list, dry_run: bool):
    """打印整理结果(按分类汇总数量和体积)"""
    label = "📋 预览结果(未真正移动)" if dry_run else "✅ 整理完成!"
    print(f"\n{Style.BOLD}{label}{Style.END}")

    if not moved:
        print("  ✨ 这里已经很干净了,没有需要整理的文件。")
        return

    # 按目标文件夹分组统计
    groups = {}
    for src, dest, size in moved:
        g = groups.setdefault(dest.parent.name, [0, 0])
        g[0] += 1
        g[1] += size

    width = max(len(name) for name in groups)
    for name, (count, size) in sorted(groups.items(), key=lambda kv: -kv[1][1]):
        emoji = CATEGORY_EMOJI.get(name, "📅")
        print(f"  {emoji} {name:<{width}} {count:>4} 个  {human_size(size):>9}")

    total_count = len(moved)
    total_size = sum(g[1] for g in groups.values())
    print(f"  {'—' * 30}")
    print(f"  合计 {Style.BOLD}{total_count}{Style.END} 个文件,"
          f"{Style.BOLD}{human_size(total_size)}{Style.END}")

    if skipped:
        print(f"\n  ⚠️ {Style.YELLOW}有 {len(skipped)} 个文件移动失败(权限不足或被占用):{Style.END}")
        for src, err in skipped[:5]:
            print(f"     · {src.name}: {err}")

    if dry_run:
        print(f"\n  {Style.DIM}以上只是预览。去掉 --dry-run 参数即可真正整理。{Style.END}")
    else:
        print(f"  {Style.DIM}后悔了?加 --undo 参数可一键撤销。{Style.END}")


# ============================================================
# 整理"账本"与撤销
# ============================================================

def save_manifest(root: Path, moved: list):
    """把这次移动的每一条记录写入账本文件,供 --undo 撤销"""
    if not moved:
        return
    manifest = {
        "version": VERSION,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "moves": [{"from": str(src), "to": str(dest)} for src, dest, _ in moved],
    }
    (root / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def undo(root: Path, verbose: bool) -> int:
    """读取账本,把文件一个个放回原位,最后清理空掉的分类文件夹"""
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        print(f"  🤷 没找到整理记录({MANIFEST_NAME}),无法撤销。")
        print(f"     {Style.DIM}请确认是在当初被整理的那个文件夹里运行。{Style.END}")
        return 1

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    moves = data.get("moves", [])
    print(f"  📖 找到 {data.get('time', '?')} 的整理记录,"
          f"共 {len(moves)} 个文件,开始撤销...\n")

    ok, fail = 0, 0
    for item in reversed(moves):  # 逆序撤销:后移动的先回来
        src, dest = Path(item["from"]), Path(item["to"])
        try:
            if dest.exists():
                back = unique_path(src, set())
                back.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest), str(back))
                if verbose:
                    print(f"  ↩️ {dest.name} → {back.parent}")
            ok += 1
        except OSError as e:
            fail += 1
            print(f"  ⚠️ {dest.name}: {e}")

    # 尽力清理空掉的分类文件夹(rmdir 只能删空文件夹,不会误删有内容的)
    for d in sorted(root.glob("*")):
        if d.is_dir() and not d.name.startswith(".") and (
                d.name in CATEGORY_FOLDERS or DATE_FOLDER_RE.match(d.name)):
            try:
                d.rmdir()
            except OSError:
                pass

    manifest_path.unlink(missing_ok=True)
    result = f"✅ 撤销完成:{ok} 个文件已放回原位"
    if fail:
        result += f",{Style.YELLOW}失败 {fail} 个{Style.END}"
    print(f"\n{result}")
    return 0 if fail == 0 else 1


# ============================================================
# 命令行入口
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tidyfile",
        description="🧹 一键整理乱糟糟的文件夹:按文件类型或日期自动归档,"
                    "支持预览与一键撤销。零依赖,单文件。",
        epilog="示例:\n"
               "  python tidyfile.py ~/Downloads            整理下载文件夹\n"
               "  python tidyfile.py . --dry-run            先预览,不真正移动\n"
               "  python tidyfile.py ~/Desktop -r           连子文件夹一起整理\n"
               "  python tidyfile.py ~/Pictures --by-date   按年月整理照片\n"
               "  python tidyfile.py . --undo               撤销上一次整理\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", nargs="?", default=".", metavar="目录",
                        help="要整理的文件夹路径,默认为当前目录")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="连子文件夹里的文件也一起整理")
    parser.add_argument("-d", "--by-date", action="store_true",
                        help="按「年月」整理,而不是按文件类型(适合照片)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="只预览要做什么,不真正移动文件")
    parser.add_argument("-u", "--undo", action="store_true",
                        help="撤销上一次整理,把文件放回原位")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="显示每一个文件的移动明细")
    parser.add_argument("-V", "--version", action="version",
                        version=f"tidyfile {VERSION}")
    return parser


def main(argv=None) -> int:
    setup_console()
    args = build_parser().parse_args(argv)

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ 路径不存在或不是文件夹:{root}")
        return 1

    if args.undo:
        return undo(root, args.verbose)

    print(f"🧹 整理:{root}")
    if args.dry_run:
        print(f"   {Style.DIM}(预览模式,不会真正移动文件){Style.END}")

    files = collect_files(root, args.recursive, root)
    if not files:
        print("  ✨ 这里已经很干净了,没有可整理的文件。")
        return 0

    moves = plan_moves(files, root, args.by_date)
    moved, skipped = execute_moves(moves, args.dry_run, args.verbose)
    print_summary(moved, skipped, args.dry_run)

    if not args.dry_run:
        save_manifest(root, moved)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # 用户按 Ctrl+C 中断:已移动的部分记录在账本里,仍可撤销
        print(f"\n\n👋 已取消。已移动的文件可运行 --undo 撤销。")
        sys.exit(130)

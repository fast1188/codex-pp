"""
ui.py - 终端 UI 工具
==================
- 颜色输出(支持 Windows 10+ ANSI)
- 格式化数字 / 时间
- 表格输出
"""

import os
import sys

# Windows 10+ 启用 ANSI 颜色
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


# ANSI 颜色码
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}


def cprint(text: str, color: str = "reset", bold: bool = False, end: str = "\n") -> str:
    """彩色打印"""
    prefix = ""
    if bold:
        prefix += COLORS["bold"]
    if color in COLORS:
        prefix += COLORS[color]
    suffix = COLORS["reset"] if prefix else ""
    return f"{prefix}{text}{suffix}"


def print_info(text: str):
    """打印信息(蓝色)"""
    print(cprint(f"ℹ {text}", "blue"))


def print_success(text: str):
    """打印成功(绿色)"""
    print(cprint(f"✓ {text}", "green"))


def print_warning(text: str):
    """打印警告(黄色)"""
    print(cprint(f"⚠ {text}", "yellow"))


def print_error(text: str):
    """打印错误(红色)"""
    print(cprint(f"✗ {text}", "red"), file=sys.stderr)


def print_banner():
    """打印 banner"""
    banner = """
╔════════════════════════════════════════════════╗
║                                                ║
║       codex-pp v0.1.0 - 国产化 AI 编程 CLI    ║
║                                                ║
║  • 多模型支持                                  ║
║  • 国内直连(api.skillai.top)                  ║
║  • 兼容 ai-agent-skills 生态                   ║
║  • 中文优先                                    ║
║                                                ║
╚════════════════════════════════════════════════╝
"""
    print(cprint(banner, "cyan"))


def print_table(headers: list, rows: list, col_colors: list = None):
    """打印表格"""
    if not rows:
        return
    col_count = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row[:col_count]):
            widths[i] = max(widths[i], len(str(cell)))

    # 打印表头
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(cprint(header_line, "bold", "cyan"))
    print(cprint("  ".join("─" * w for w in widths), "dim"))
    # 打印行
    for row in rows:
        cells = []
        for i, cell in enumerate(row[:col_count]):
            text = str(cell).ljust(widths[i])
            if col_colors and i < len(col_colors) and col_colors[i]:
                text = cprint(text, col_colors[i])
            cells.append(text)
        print("  ".join(cells))


def format_tokens(n: int) -> str:
    """格式化 token 数"""
    if n < 1000:
        return f"{n}"
    elif n < 1_000_000:
        return f"{n/1000:.1f}K"
    else:
        return f"{n/1_000_000:.2f}M"


def format_latency(seconds: float) -> str:
    """格式化延迟"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        m, s = divmod(seconds, 60)
        return f"{m:.0f}m{s:.0f}s"
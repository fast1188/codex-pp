"""
ui.py - 终端 UI 工具
==================
- 颜色输出(支持 Windows 10+ ANSI)
- 格式化数字 / 时间
- 表格输出
"""

import os
import sys
from typing import Optional

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


def _safe(text: str) -> str:
    """编码安全: 终端不支持 unicode 时回退到 ASCII 近似"""
    enc = sys.stdout.encoding or "utf-8"
    try:
        text.encode(enc)
        return text
    except UnicodeEncodeError:
        # 替换常用 unicode 符号为 ASCII
        repl = {
            "[i]": "[i]", "[OK]": "[OK]", "[X]": "[X]", "[!]": "[!]",
            "[X]": "[X]", "⠋": "|", "⠙": "/", "⠹": "-", "⠸": "\\",
            "⠼": "|", "⠴": "/", "⠦": "-", "⠧": "\\", "⠇": "|",
            "⠏": "/", "+": "+", "+": "+", "+": "+", "+": "+",
            "|": "|", "=": "=", "-": "-",
        }
        for k, v in repl.items():
            text = text.replace(k, v)
        # 任何剩余的 encode 失败字符丢成 ?
        return text.encode(enc, errors="replace").decode(enc)


def print_info(text: str):
    """打印信息(蓝色)"""
    print(cprint(_safe(f"[i] {text}"), "blue"))


def print_success(text: str):
    """打印成功(绿色)"""
    print(cprint(_safe(f"[OK] {text}"), "green"))


def print_warning(text: str):
    """打印警告(黄色)"""
    print(cprint(_safe(f"[!] {text}"), "yellow"))


def print_error(text: str):
    """打印错误(红色)"""
    print(cprint(_safe(f"[X] {text}"), "red"), file=sys.stderr)


def print_banner():
    """打印 banner"""
    banner = _safe("""
+================================================+
|                                                |
|       codex-pp v0.4.0 - 国产化 AI 编程 CLI    |
|                                                |
|  * 多模型支持                                  |
|  * 国内直连(api.skillai.top)                   |
|  * 兼容 ai-agent-skills 生态                   |
|  * 中文优先                                    |
|                                                |
+================================================+
""")
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
    print(cprint("  ".join("-" * w for w in widths), "dim"))
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


import threading
import time as _time
import itertools


class Spinner:
    """简易 spinner 上下文管理器: 显示"思考中..."动画
    兼容 Windows GBK/老终端: 优先 Unicode braille, 失败回退 ASCII
    """
    FRAMES_UNICODE = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    FRAMES_ASCII = ["|", "/", "-", "\\"]

    def __init__(self, text: str = "思考中", color: str = "cyan", interval: float = 0.08):
        self.text = text
        self.color = color
        self.interval = interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # 探测 stdout 是否支持 unicode
        self.frames = self._detect_frames()

    def _detect_frames(self) -> list:
        try:
            test = self.FRAMES_UNICODE[0].encode(sys.stdout.encoding or "utf-8")
            return self.FRAMES_UNICODE
        except (UnicodeEncodeError, AttributeError):
            return self.FRAMES_ASCII

    def _spin(self):
        sys.stdout.write(cprint(f"\r{self.text} ", self.color, bold=True))
        sys.stdout.flush()
        for frame in itertools.cycle(self.frames):
            if self._stop.is_set():
                break
            try:
                sys.stdout.write(cprint(frame, self.color))
                sys.stdout.flush()
            except UnicodeEncodeError:
                # 运行时编码变更, 切到 ASCII
                self.frames = self.FRAMES_ASCII
                sys.stdout.write(cprint(self.frames[0], self.color))
                sys.stdout.flush()
            _time.sleep(self.interval)
        # 清除 spinner 行
        sys.stdout.write("\r" + " " * (len(self.text) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        return False


def print_assistant_header():
    """打印助手回复头(蓝色 + 粗体)"""
    print(cprint("\n助手: ", "green", bold=True), end="", flush=True)
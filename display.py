import sys, re, shutil, os

ANSI_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "underline": "\033[4m",
    "gray": "\033[90m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
}

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clear():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def strip_ansi(s):
    return ansi_escape.sub('', s)

def build_bar(progress: float, config: dict) -> str:
    width = config.get("progress_bar_width", 40)
    fill = config.get("progress_bar_fill", "█")
    empty = config.get("progress_bar_empty", "░")
    filled = int(width * progress)
    empty_len = width - filled
    return fill * filled + empty * empty_len

def evaluate_expression(match, context):
    code = match.group(1).strip()
    fmt = match.group(2)
    try:
        safe_locals = {
            **context,
            "build_bar": build_bar,
            "config": context.get("config", {})
        }
        value = eval(code, {}, safe_locals)
        return f"{value:{fmt}}" if fmt else str(value)
    except Exception as e:
        return f"[eval error: {e}]"

def render_line_refs(text, context):
    def repl(match):
        try:
            key = int(match.group(1))
            return context.get("line", {}).get(key, "")
        except:
            return ""
    return re.sub(r"{line\[(\-?\d+)]}", repl, text)

def apply_styling_tags(line):
    line = re.sub(r"{color:([^}]+)}", color_tag, line)
    line = line.replace("{reset}", ANSI_COLORS["reset"])
    line = line.replace("{bold}", ANSI_COLORS["bold"])
    line = line.replace("{underline}", ANSI_COLORS["underline"])
    return line

def apply_wrapping_protection(line, config, width):
    visible = strip_ansi(line)
    wrap = config.get("wrap_protection", "none")
    if len(visible) > width:
        if wrap == "truncate":
            return line[:width]
        elif wrap == "ellipsis":
            return line[:width - 1] + "…"
    return line

def center_line(line, width):
    visible = strip_ansi(line)
    pad = (width - len(visible)) // 2
    return " " * pad + line if pad > 0 else line

def color_tag(match):
    code = match.group(1).lower()
    if code.startswith("#") and len(code) == 7:
        try:
            r = int(code[1:3], 16)
            g = int(code[3:5], 16)
            b = int(code[5:7], 16)
            return f"\033[38;2;{r};{g};{b}m"
        except:
            return ""
    return ANSI_COLORS.get(code, "")

class Displayer:
    def __init__(self, format: list, auto_newline: bool = True):
        self.format = format
        self.auto_newline = auto_newline
        self.previous_lines = 0

    def clear(self, method: str = "clear"):
        if method == "clear":
            clear()
            return
        if method == "cursor":
            for _ in range(self.previous_lines + 1):
                sys.stdout.write("\033[F") # move cursor up
                sys.stdout.write("\033[K") # write line
            self.previous_lines = 0

    def display(self, context: dict):
        output_lines = []
        config = context.get("config", {})
        center = config.get("center_text", False)
        terminal_width = shutil.get_terminal_size((80, 20)).columns

        for line in self.format:
            try:
                line = re.sub(r"{=([^:}]+)(?::([^}]+))?}", lambda m: evaluate_expression(m, context), line)
                line = render_line_refs(line, context)
                line = apply_styling_tags(line)
                line = line.format(**context)
                line = apply_wrapping_protection(line, config, terminal_width)
                if center:
                    line = center_line(line, terminal_width)
                output_lines.append(line)
            except Exception as e:
                output_lines.append(f"[Error] {line} → {e}")

        self.clear()
        for line in output_lines:
            print(line, end="\n" if self.auto_newline else "")
        self.previous_lines = len(output_lines)

def generate_display_context(playback, config, progress_ms=None):
    context = {
        "playback": playback,
        "config": config,
        "bar": "",
        "percent": 0,
        "progress_bar": "",
        "elapsed": "0:00",
        "duration": "0:00"
    }

    def format_time(ms):
        total_sec = int(ms // 1000)
        return f"{total_sec // 60}:{total_sec % 60:02}"

    item = playback.item
    progress_ms = progress_ms if progress_ms is not None else (playback.progress_ms or 0)

    if item and item.duration_ms:
        ratio = min(progress_ms / item.duration_ms, 1.0)
        percent = ratio * 100
        bar = build_bar(ratio, config)
        progress_bar = config["progress_bar_format"].format(bar=bar, percent=percent)
        elapsed = format_time(progress_ms)
        duration = format_time(item.duration_ms)

        context.update({
            "bar": bar,
            "percent": percent,
            "progress_bar": progress_bar,
            "elapsed": elapsed,
            "duration": duration
        })

    return context

import re
from blessed import Terminal

term = Terminal()

def hex_to_rgb(hexcode):
    hexcode = hexcode.lstrip("#")
    return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))

def strip_ansi(text):
    return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)

def build_bar(progress: float, config: dict) -> str:
    width = config.get("progress_bar_width", 40)
    fill = config.get("progress_bar_fill", "█")
    empty = config.get("progress_bar_empty", "░")
    filled = int(width * progress)
    return fill * filled + empty * (width - filled)

class Displayer:
    def __init__(self, format_lines: list[str], auto_newline: bool = True):
        self.format = format_lines
        self.auto_newline = auto_newline

    def display(self, context: dict):
        config = context.get("config", {})
        center = config.get("center_text", False)
        wrap = config.get("wrap_protection", "none")
        width = term.width

        output_lines = []

        for line in self.format:
            try:
                # Evaluate {=...}
                line = re.sub(r"{=([^:}]+)(?::([^}]+))?}", lambda m: self.eval_expr(m, context), line)

                # Replace line[N] placeholders
                line = re.sub(r"{line\[(\-?\d+)]}", lambda m: context.get("line", {}).get(int(m.group(1)), ""), line)

                # Replace color tags
                line = re.sub(r"{color:(#?[a-zA-Z0-9]+)}", lambda m: self.color_tag(m.group(1)), line)

                # Replace formatting tags
                line = line.replace("{reset}", term.normal)
                line = line.replace("{bold}", term.bold)
                line = line.replace("{underline}", term.underline)

                # Format context variables
                line = line.format(**context)

                # Wrap protection
                if wrap != "none":
                    visible = strip_ansi(line)
                    if len(visible) > width:
                        if wrap == "truncate":
                            line = line[:width]
                        elif wrap == "ellipsis":
                            line = line[:width - 1] + "…"

                # Centering
                if center:
                    visible = strip_ansi(line)
                    pad = (width - len(visible)) // 2
                    if pad > 0:
                        line = " " * pad + line

                output_lines.append(line)
            except Exception as e:
                output_lines.append(f"[Error] {line} → {e}")

        # Draw all lines
        for y, line in enumerate(output_lines):
            print(term.move_yx(y, 0) + line, end="\n" if self.auto_newline else "", flush=True)

    def eval_expr(self, match, context):
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

    def color_tag(self, name):
        if name.startswith("#") and len(name) == 7:
            try:
                r, g, b = hex_to_rgb(name)
                return term.color_rgb(r, g, b)
            except:
                return ""
        elif hasattr(term, name):
            return getattr(term, name)
        return ""


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
        progress_bar = config.get("progress_bar_format", "[{bar}] {percent:.1f}%").format(bar=bar, percent=percent)
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

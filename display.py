import sys, re

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

def build_bar(progress: float, config: dict) -> str:
    width = config.get("progress_bar_width", 40)
    fill = config.get("progress_bar_fill", "█")
    empty = config.get("progress_bar_empty", "░")

    filled = int(width * progress)
    empty_len = width - filled
    return fill * filled + empty * empty_len


class Displayer:
    def __init__(self, format: list, auto_suffix: str = "\n"):
        self.format = format
        self.auto_suffix = auto_suffix
        self.previous_lines = 0

    def clear(self):
        for _ in range(self.previous_lines):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
        self.previous_lines = 0

    def display(self, context: dict):
        output_lines = []
        for line in self.format:
            try:
                def eval_expr(match):
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

                # Replace color tags BEFORE format()
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

                line = re.sub(r"{color:(\w+)}", color_tag, line)
                line = line.replace("{reset}", ANSI_COLORS["reset"])

                # Eval first, then format
                line = re.sub(r"{=([^:}]+)(?::([^}]+))?}", eval_expr, line)

                def replace_line_refs(match):
                    try:
                        index = int(match.group(1))
                        return context["line"][index]
                    except Exception:
                        return ""

                line = re.sub(r"{line\[(\-?\d+)]}", replace_line_refs, line)

                line = line.format(**context)

                output_lines.append(line)
            except Exception as e:
                output_lines.append(f"[Error] {line} → {e}")

        self.clear()
        for line in output_lines:
            print(line, end=self.auto_suffix)
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

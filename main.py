from blessed import Terminal
import time
import re
from fetcher import SpotifyFetcher, Config, LyricsManager
from display import Displayer, generate_display_context

term = Terminal()

fetcher = SpotifyFetcher()
config = Config().config
lyrics = LyricsManager()
displayer = Displayer(config["format"])

last_update_time = 0
update_interval = config.get("spotify_refresh_interval", 4)

with term.fullscreen(), term.hidden_cursor(), term.cbreak():
    while True:
        now = time.time()
        if now - last_update_time >= update_interval:
            fetcher.update()
            last_update_time = now

        current = fetcher.playback.item
        if not current:
            print(term.move_yx(0, 0) + term.clear_eos + "No track is currently playing.", end="", flush=True)
            time.sleep(config.get("refresh_rate", 0.5))
            continue

        progress_ms = fetcher.get_progress_ms()
        lyrics.update(current)
        lyrics.tracker.update(progress_ms)

        context = generate_display_context(fetcher.playback, config, progress_ms=progress_ms)

        used_line_indices = {
            int(match)
            for line_template in config["format"]
            for match in re.findall(r"{line\[(\-?\d+)]}", line_template)
        }

        context["line"] = {i: lyrics.tracker.get_line(i) for i in used_line_indices}

        # Clear and render
        print(term.move_yx(0, 0) + term.clear_eos, end="")
        displayer.display(context)

        # Input handling (optional)
        key = term.inkey(timeout=config.get("refresh_rate", 0.1))
        if key == "q":
            break
        elif key.name == "KEY_LEFT":
            fetcher.seek_relative(-5000)
        elif key.name == "KEY_RIGHT":
            fetcher.seek_relative(5000)
        elif key == " ":
            fetcher.toggle_play_pause()

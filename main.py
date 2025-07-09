import time
import re, os
from fetcher import SpotifyFetcher, Config, LyricsManager
from display import Displayer, generate_display_context, clear

fetcher = SpotifyFetcher()
config = Config().config
lyrics = LyricsManager()
displayer = Displayer(config["format"])

last_update_time = 0
update_interval = config.get("spotify_refresh_interval", 4)

clear()

while True:
    now = time.time()
    if now - last_update_time >= update_interval:
        fetcher.update()
        last_update_time = now

    current = fetcher.playback.item
    if not current:
        print("No track is currently playing.")
        time.sleep(config.get("refresh_rate", 0.5))
        continue

    progress_ms = fetcher.get_progress_ms()

    lyrics.update(current)
    lyrics.tracker.update(progress_ms)

    context = generate_display_context(fetcher.playback, config, progress_ms=progress_ms)

    # Dynamically extract {line[N]} references from config
    used_line_indices = {
        int(match)
        for line_template in config["format"]
        for match in re.findall(r"{line\[(\-?\d+)]}", line_template)
    }

    context["line"] = {i: lyrics.tracker.get_line(i) for i in used_line_indices}

    # Render
    displayer.display(context)

    time.sleep(config.get("refresh_rate", 0.5))

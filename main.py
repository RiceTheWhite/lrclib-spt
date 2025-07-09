import time
from fetcher import SpotifyFetcher, Config, LyricsManager
from display import Displayer, generate_display_context

fetcher = SpotifyFetcher()
config = Config().config
lyrics = LyricsManager()
displayer = Displayer(config["format"])

last_update_time = 0
update_interval = config.get("spotify_refresh_interval", 4)

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
    context = generate_display_context(fetcher.playback, config, progress_ms=progress_ms)

    # Inject dynamic line[i] context
    context["line"] = lyrics.get_lines_for_context(progress_ms, config["format"])

    displayer.display(context)
    time.sleep(config.get("refresh_rate", 0.5))

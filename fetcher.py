import yaml
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import re

class Config:
    def __init__(self):
        with open('config.yaml', 'r') as stream:
            self.config = yaml.safe_load(stream)

config = Config().config

client_id: str = config["client_id"]
client_secret: str = config["client_secret"]
redirect_uri: str = config["redirect_uri"]

class AttrDict(dict):
    def __getattr__(self, name):
        value = self.get(name)
        if isinstance(value, dict):
            return AttrDict(value)
        elif isinstance(value, list):
            return [AttrDict(i) if isinstance(i, dict) else i for i in value]
        return value

    def __getitem__(self, key):
        return self.__getattr__(key)


class SpotifyFetcher:
    def __init__(self):
        self.client = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-read-playback-state user-modify-playback-state"
        ))
        self.playback = AttrDict()
        self.last_fetch_time = 0
        self.last_progress_ms = 0

    def update(self):
        import time
        self.last_fetch_time = time.time()
        playback = self.client.current_playback()
        if playback is None:
            return
        playback_obj = AttrDict(playback)
        self.last_progress_ms = playback_obj.progress_ms or 0
        self.playback = playback_obj

    def get_progress_ms(self):
        import time
        if not self.playback or not self.playback.is_playing:
            return self.playback.progress_ms if self.playback else 0
        elapsed = (time.time() - self.last_fetch_time) * 1000
        return min(self.last_progress_ms + elapsed, self.playback.item.duration_ms or 0)


class LyricsFetcher:
    BASE_URL = "https://lrclib.net/api/search"

    @staticmethod
    def fetch_lyrics(title, artist, fallback_to_plain=True):
        try:
            response = requests.get(LyricsFetcher.BASE_URL, params={
                "track_name": title,
                "artist_name": artist
            })
            response.raise_for_status()
            results = response.json()
        except Exception as e:
            print("❌ Error fetching lyrics:", e)
            return None, False

        for result in results:
            if result.get("syncedLyrics"):
                return result["syncedLyrics"], True
            elif fallback_to_plain and result.get("plainLyrics"):
                return result["plainLyrics"], False
        return None, False

    @staticmethod
    def fetch_lyrics_timestamp(title, artist, fallback_to_plain=True):
        raw, is_synced = LyricsFetcher.fetch_lyrics(title, artist, fallback_to_plain)
        if not raw:
            return None, False
        if not is_synced:
            return raw.strip(), False

        parsed = []
        pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2})](.*)")
        for line in raw.strip().splitlines():
            match = pattern.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                hundredths = int(match.group(3))
                timestamp = (minutes * 60 + seconds) * 1000 + hundredths * 10
                text = match.group(4).strip()
                parsed.append((timestamp, text))

        return parsed, True


class LyricsTracker:
    def __init__(self):
        self.lines = []
        self.index = 0

    def load(self, timestamped_lyrics):
        self.lines = timestamped_lyrics or []
        self.index = 0

    def get_index(self, progress_ms: int):
        if not self.lines:
            return 0
        while self.index + 1 < len(self.lines) and progress_ms >= self.lines[self.index + 1][0]:
            self.index += 1
        while self.index > 0 and progress_ms < self.lines[self.index][0]:
            self.index -= 1
        return self.index

    def get_line(self, rel_offset: int) -> str:
        idx = self.index + rel_offset
        if 0 <= idx < len(self.lines):
            return self.lines[idx][1]
        return ""

    def update(self, progress_ms: int):
        self.get_index(progress_ms)

class LyricsManager:
    def __init__(self):
        self.tracker = LyricsTracker()
        self.last_track_id = None
        self.is_synced = False

    def update(self, item):
        if not item:
            return

        track_id = item.id
        if track_id == self.last_track_id:
            return

        title = item.name
        artist = item.artists[0].name
        lyrics, is_synced = LyricsFetcher.fetch_lyrics_timestamp(title, artist)

        self.last_track_id = track_id
        self.is_synced = is_synced
        if is_synced:
            self.tracker.load(lyrics)

    def get_lines_for_context(self, progress_ms, format_lines):
        if not self.is_synced:
            return {}

        self.tracker.get_index(progress_ms + config["offset_seconds"]*1000)

        used_line_indices = {
            int(m) for line in format_lines
            for m in re.findall(r"{line\[(\-?\d+)]}", line)
        }

        return {i: self.tracker.get_line(i) for i in used_line_indices}

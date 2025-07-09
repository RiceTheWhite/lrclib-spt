# 🎵 Spotify Lyrics in the Terminal

An ***INFINITELY*** customizable terminal-based Spotify synced-lyrics display, full theme customization, and local time tracking for smooth updates.

---

## 📷 Screenshot

![terminal](https://github.com/user-attachments/assets/bab5d043-8d63-4876-bdf1-105554938f4f)
![fullscreen](https://github.com/user-attachments/assets/ab17e79b-4279-4093-afca-5c3655b25e98)


---

## TODO
### Have an idea? make an issue OR contact me directly.

- [X] Centered text
- [ ] Border around terminal
- [X] Hex color support
- [X] Lyrics-syncing
- [X] Color support
- [X] Fully customizable layout (really, you can change everything*.)
- [X] Python `eval()`-like format (infinitely* customizable)
- [X] Protection against text wrapping

---

## Features

- Synced lyrics (via LRCLIB)
- Real-time Spotify playback info
- Customizable color themes and layouts
- Local progress tracking (avoids API lag)
- YAML-based configuration
- Auto-detects track changes & refreshes lyrics

---

## Setup

1. Clone the repo
2. Create a Spotify app at https://developer.spotify.com/dashboard/
3. Fill in your credentials in `config.yaml`
4. Run the app:

```
python main.py
```

---

## Configuration (`config.yaml`)

All customization happens in `config.yaml`. Example:

```yaml
client_id: "..."
client_secret: "..."
redirect_uri: "http://localhost:8888/callback"

refresh_rate: 0.5
spotify_refresh_interval: 4
offset_seconds: 0.0

format:
  - "{color:cyan}Now playing:{reset} {playback.item.name} — {playback.item.artists[0].name}"
  - "{color:gray}Time:{reset} {elapsed} / {duration}"
  - "{progress_bar}"
  - ""
  - "{color:gray}{line[-1]}{reset}"
  - "{color:green}{line[0]}{reset}"
  - "{color:gray}{line[1]}{reset}"
```

You can use:
- `{playback.item.name}`: song title
- `{playback.device.name}`: current device
- `{elapsed}` and `{duration}`
- `{line[-1]}` `{line[0]}` `{line[1]}`: lyrics above/current/below
- `{progress_bar}`, `{percent}`, and even `{= math or logic here }`

---

## Variables (from Spotify API)

The full context is available via `{playback...}`.

Example structure (see more in `sample.js`):

```
playback = {
  "device": {
    "name": "archlinux",
    "type": "Computer",
    "volume_percent": 52
  },
  "is_playing": True,
  "progress_ms": 71248,
  "item": {
    "name": "cardboard boxes",
    "duration_ms": 202086,
    "artists": [{ "name": "twikipedia" }],
    "album": {
      "name": "for the rest of your life",
      "release_date": "2024-05-10",
      "images": [
        { "url": "https://i.scdn.co/image/...", "width": 640 }
      ]
    }
  }
}
```

---

## Colors

Use `{color:cyan}`, `{color:red}`, etc. and `{reset}` to end formatting.

---

## Advanced Features

- `{= ... }` for Python expressions (eval)
- `{line[N]}` to access dynamic synced lyric lines
- Smart bar building: `{progress_bar}` and `{=build_bar(...)}`
- Song change detection + auto lyric reload

---

## Dependencies

- Python 3.8+
- spotipy
- pyyaml
- requests


## Debug Tips

To debug what values are available in `context`, add this to your format:

```
- "{=playback}"
- "{=playback.item}"
```

Or just dump everything with:

```
- "{=str(context)}"
```

---

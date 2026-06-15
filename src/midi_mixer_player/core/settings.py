from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


APP_DIR_NAME = "MIDI Mixer Player"


@dataclass(slots=True)
class AppSettings:
    soundfont_path: str = ""
    last_open_dir: str = ""
    window_width: int = 1180
    window_height: int = 720
    default_volume: int = 100
    ffmpeg_path: str = ""


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self.default_path()

    @staticmethod
    def default_path() -> Path:
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME / "settings.json"
        return Path.home() / ".midi_mixer_player" / "settings.json"

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppSettings()
        return AppSettings(**self._known_fields(data))

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "soundfont_path": settings.soundfont_path,
            "last_open_dir": settings.last_open_dir,
            "window_width": settings.window_width,
            "window_height": settings.window_height,
            "default_volume": settings.default_volume,
            "ffmpeg_path": settings.ffmpeg_path,
        }
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _known_fields(data: dict[str, Any]) -> dict[str, Any]:
        field_names = set(AppSettings.__dataclass_fields__)
        return {key: value for key, value in data.items() if key in field_names}

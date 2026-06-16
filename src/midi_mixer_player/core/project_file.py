from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from midi_mixer_player.core.models import MixerState


PROJECT_VERSION = 1


class ProjectFileError(RuntimeError):
    pass


def save_project(path: Path, midi_path: Path, mixer_state: MixerState) -> None:
    data = {
        "version": PROJECT_VERSION,
        "midi_file": str(midi_path),
        "tempo_percent": mixer_state.tempo_percent,
        "key_semitones": mixer_state.key_semitones,
        "channels": [
            {
                "index": channel.index,
                "mute": channel.mute,
                "solo": channel.solo,
                "volume": channel.volume,
                "pan": channel.pan,
            }
            for channel in mixer_state.channels
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(path: Path) -> tuple[Path, MixerState]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectFileError(f"プロジェクトファイルを読み込めませんでした: {exc}") from exc

    if data.get("version") != PROJECT_VERSION:
        raise ProjectFileError("対応していないプロジェクトファイル形式です。")

    midi_file = data.get("midi_file")
    if not midi_file:
        raise ProjectFileError("プロジェクトにMIDIファイルの情報がありません。")

    state = MixerState()
    state.tempo_percent = _int_in_range(data.get("tempo_percent"), 50, 200, 100)
    state.key_semitones = _int_in_range(data.get("key_semitones"), -12, 12, 0)

    channels = data.get("channels", [])
    if not isinstance(channels, list):
        raise ProjectFileError("プロジェクトのチャンネル情報が壊れています。")

    for channel_data in channels:
        _apply_channel_data(state, channel_data)

    return Path(midi_file), state


def _apply_channel_data(state: MixerState, channel_data: Any) -> None:
    if not isinstance(channel_data, dict):
        return
    index = channel_data.get("index")
    if not isinstance(index, int) or not 0 <= index < len(state.channels):
        return

    channel = state.channels[index]
    channel.mute = bool(channel_data.get("mute", False))
    channel.solo = bool(channel_data.get("solo", False))
    channel.volume = _int_in_range(channel_data.get("volume"), 0, 127, 100)
    channel.pan = _int_in_range(channel_data.get("pan"), 0, 127, 64)


def _int_in_range(value: Any, minimum: int, maximum: int, default: int) -> int:
    if not isinstance(value, int):
        return default
    return max(minimum, min(maximum, value))

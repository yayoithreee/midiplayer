from __future__ import annotations

from pathlib import Path

import mido

from midi_mixer_player.core.models import ChannelInfo, MidiInfo
from midi_mixer_player.midi.gm_names import gm_program_name
from midi_mixer_player.midi.tempo_map import estimate_length_seconds, first_bpm


class MidiLoadError(RuntimeError):
    pass


def load_midi_info(path: str | Path) -> MidiInfo:
    midi_path = Path(path)
    try:
        mid = mido.MidiFile(midi_path)
    except (OSError, EOFError, ValueError) as exc:
        raise MidiLoadError(f"MIDIファイルを読み込めませんでした: {exc}") from exc

    channels = [ChannelInfo(index=i, is_drum=(i == 9)) for i in range(16)]
    title = midi_path.stem

    for track in mid.tracks:
        for message in track:
            if message.is_meta:
                if message.type in {"track_name", "sequence_name"} and message.name:
                    title = message.name
                continue
            channel = getattr(message, "channel", None)
            if channel is None or not 0 <= channel < 16:
                continue

            info = channels[channel]
            if message.type in {
                "note_on",
                "note_off",
                "control_change",
                "program_change",
                "polytouch",
                "aftertouch",
                "pitchwheel",
            }:
                info.used = True
            if message.type == "note_on" and getattr(message, "velocity", 0) > 0:
                info.note_count += 1
            if message.type == "program_change":
                info.program = message.program
                info.program_name = gm_program_name(message.program)

    for info in channels:
        if info.is_drum:
            info.program_name = "Drum"

    return MidiInfo(
        path=midi_path,
        midi_format=mid.type,
        track_count=len(mid.tracks),
        ticks_per_beat=mid.ticks_per_beat,
        estimated_seconds=estimate_length_seconds(mid),
        base_bpm=first_bpm(mid),
        title=title,
        channels=channels,
    )

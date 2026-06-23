from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ChannelInfo:
    index: int
    used: bool = False
    program: int | None = None
    program_name: str = "-"
    note_count: int = 0
    is_drum: bool = False

    @property
    def display_number(self) -> int:
        return self.index + 1


@dataclass(slots=True)
class MidiInfo:
    path: Path
    midi_format: int
    track_count: int
    ticks_per_beat: int
    estimated_seconds: float
    base_bpm: float
    title: str
    channels: list[ChannelInfo] = field(default_factory=list)


@dataclass(slots=True)
class MixerChannelState:
    index: int
    mute: bool = False
    solo: bool = False
    volume: int = 100
    pan: int = 64


@dataclass(slots=True)
class MixerState:
    channels: list[MixerChannelState] = field(
        default_factory=lambda: [MixerChannelState(index=i) for i in range(16)]
    )
    tempo_percent: int = 100
    key_semitones: int = 0
    master_volume: int = 100

    def has_solo(self) -> bool:
        return any(channel.solo for channel in self.channels)

    def channel_can_sound(self, channel_index: int) -> bool:
        channel = self.channels[channel_index]
        if channel.mute:
            return False
        if self.has_solo() and not channel.solo:
            return False
        return True

    def reset(self) -> None:
        self.tempo_percent = 100
        self.key_semitones = 0
        self.master_volume = 100
        for channel in self.channels:
            channel.mute = False
            channel.solo = False
            channel.volume = 100
            channel.pan = 64

    def effective_channel_volume(self, channel_index: int) -> int:
        channel = self.channels[channel_index]
        return max(0, min(127, round(channel.volume * self.master_volume / 127)))

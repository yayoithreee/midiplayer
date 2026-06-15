from __future__ import annotations

from dataclasses import dataclass

import mido


@dataclass(frozen=True, slots=True)
class TempoChange:
    tick: int
    tempo: int


DEFAULT_TEMPO = 500000


def build_tempo_map(mid: mido.MidiFile) -> list[TempoChange]:
    changes = [TempoChange(tick=0, tempo=DEFAULT_TEMPO)]
    for track in mid.tracks:
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
            if message.type == "set_tempo":
                changes.append(TempoChange(tick=absolute_tick, tempo=message.tempo))
    changes.sort(key=lambda change: change.tick)

    deduped: list[TempoChange] = []
    for change in changes:
        if deduped and deduped[-1].tick == change.tick:
            deduped[-1] = change
        else:
            deduped.append(change)
    return deduped


def tick_to_seconds(tick: int, ticks_per_beat: int, tempo_map: list[TempoChange]) -> float:
    if tick <= 0:
        return 0.0

    elapsed = 0.0
    previous_tick = 0
    current_tempo = DEFAULT_TEMPO

    for change in tempo_map:
        if change.tick > tick:
            break
        delta = change.tick - previous_tick
        elapsed += mido.tick2second(delta, ticks_per_beat, current_tempo)
        previous_tick = change.tick
        current_tempo = change.tempo

    elapsed += mido.tick2second(tick - previous_tick, ticks_per_beat, current_tempo)
    return elapsed


def estimate_length_seconds(mid: mido.MidiFile) -> float:
    tempo_map = build_tempo_map(mid)
    max_tick = 0
    for track in mid.tracks:
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
        max_tick = max(max_tick, absolute_tick)
    return tick_to_seconds(max_tick, mid.ticks_per_beat, tempo_map)

from __future__ import annotations

DRUM_CHANNEL_INDEX = 9


def clamp_note(note: int) -> int:
    return max(0, min(127, note))


def transpose_note(note: int, channel_index: int, semitones: int) -> int:
    if channel_index == DRUM_CHANNEL_INDEX or semitones == 0:
        return note
    return clamp_note(note + semitones)

from __future__ import annotations

from copy import deepcopy

import mido

from midi_mixer_player.core.models import MixerState

DRUM_CHANNEL_INDEX = 9


def clamp_note(note: int) -> int:
    return max(0, min(127, note))


def transpose_note(note: int, channel_index: int, semitones: int) -> int:
    if channel_index == DRUM_CHANNEL_INDEX or semitones == 0:
        return note
    return clamp_note(note + semitones)


def transform_midi_for_export(mid: mido.MidiFile, mixer_state: MixerState) -> mido.MidiFile:
    transformed = mido.MidiFile(
        type=mid.type,
        ticks_per_beat=mid.ticks_per_beat,
        charset=getattr(mid, "charset", "latin1"),
        debug=False,
        clip=False,
    )

    for source_track in mid.tracks:
        target_track = mido.MidiTrack()
        pending_time = 0

        for message in source_track:
            pending_time += message.time
            new_message = _transform_message(message, mixer_state)
            if new_message is None:
                continue
            new_message.time = pending_time
            pending_time = 0
            target_track.append(new_message)

        if pending_time:
            target_track.append(mido.MetaMessage("end_of_track", time=pending_time))
        transformed.tracks.append(target_track)

    _insert_initial_volumes(transformed, mixer_state)
    return transformed


def _transform_message(message: mido.Message | mido.MetaMessage, mixer_state: MixerState):
    if message.is_meta:
        copied = deepcopy(message)
        if copied.type == "set_tempo":
            copied.tempo = max(1, round(copied.tempo * 100 / mixer_state.tempo_percent))
        return copied

    if not hasattr(message, "channel"):
        return message.copy()

    channel_index = message.channel
    if message.type in {"note_on", "note_off"} and not mixer_state.channel_can_sound(channel_index):
        return None

    if message.type in {"note_on", "note_off"}:
        return message.copy(
            note=transpose_note(message.note, channel_index, mixer_state.key_semitones)
        )

    if message.type == "control_change" and message.control == 7:
        volume = mixer_state.channels[channel_index].volume
        return message.copy(value=max(0, min(127, round(message.value * volume / 127))))

    if message.type == "program_change" and channel_index == DRUM_CHANNEL_INDEX:
        return None

    return message.copy()


def _insert_initial_volumes(mid: mido.MidiFile, mixer_state: MixerState) -> None:
    if not mid.tracks:
        mid.tracks.append(mido.MidiTrack())

    initial_messages = []
    for channel in mixer_state.channels:
        initial_messages.append(
            mido.Message(
                "control_change",
                channel=channel.index,
                control=7,
                value=channel.volume,
                time=0,
            )
        )
        if channel.index == DRUM_CHANNEL_INDEX:
            initial_messages.append(
                mido.Message("program_change", channel=channel.index, program=0, time=0)
            )

    mid.tracks[0][:0] = initial_messages

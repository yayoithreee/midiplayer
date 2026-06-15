import mido

from midi_mixer_player.core.models import MixerState
from midi_mixer_player.midi.transformer import clamp_note, transform_midi_for_export, transpose_note


def test_clamp_note_bounds_to_midi_range():
    assert clamp_note(-10) == 0
    assert clamp_note(64) == 64
    assert clamp_note(140) == 127


def test_transpose_note_skips_drum_channel():
    assert transpose_note(36, channel_index=9, semitones=12) == 36


def test_transpose_note_clips_out_of_range_notes():
    assert transpose_note(124, channel_index=0, semitones=12) == 127
    assert transpose_note(3, channel_index=0, semitones=-12) == 0


def test_transform_midi_for_export_applies_key_tempo_and_volume():
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    track.append(mido.Message("control_change", channel=0, control=7, value=100, time=0))
    track.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=480))
    mid.tracks.append(track)

    state = MixerState()
    state.tempo_percent = 200
    state.key_semitones = 2
    state.channels[0].volume = 64

    transformed = transform_midi_for_export(mid, state)
    messages = [message for track in transformed.tracks for message in track]

    assert any(message.type == "set_tempo" and message.tempo == 250000 for message in messages)
    assert any(
        message.type == "control_change"
        and message.channel == 0
        and message.control == 7
        and message.value == 50
        for message in messages
    )
    assert any(message.type == "note_on" and message.note == 62 for message in messages)


def test_transform_midi_for_export_removes_muted_notes_and_preserves_time():
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=120))
    track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=240))
    track.append(mido.Message("note_on", channel=1, note=64, velocity=64, time=360))
    mid.tracks.append(track)

    state = MixerState()
    state.channels[0].mute = True

    transformed = transform_midi_for_export(mid, state)
    note_messages = [
        message
        for track in transformed.tracks
        for message in track
        if message.type in {"note_on", "note_off"}
    ]

    assert len(note_messages) == 1
    assert note_messages[0].channel == 1
    assert note_messages[0].time == 720


def test_transform_midi_for_export_does_not_transpose_drum_notes():
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.Message("program_change", channel=9, program=24, time=0))
    track.append(mido.Message("note_on", channel=9, note=36, velocity=100, time=0))
    mid.tracks.append(track)

    state = MixerState()
    state.key_semitones = 12

    transformed = transform_midi_for_export(mid, state)
    messages = [message for track in transformed.tracks for message in track]

    assert any(message.type == "note_on" and message.channel == 9 and message.note == 36 for message in messages)
    assert not any(message.type == "program_change" and message.channel == 9 and message.program == 24 for message in messages)

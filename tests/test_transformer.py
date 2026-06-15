from midi_mixer_player.midi.transformer import clamp_note, transpose_note


def test_clamp_note_bounds_to_midi_range():
    assert clamp_note(-10) == 0
    assert clamp_note(64) == 64
    assert clamp_note(140) == 127


def test_transpose_note_skips_drum_channel():
    assert transpose_note(36, channel_index=9, semitones=12) == 36


def test_transpose_note_clips_out_of_range_notes():
    assert transpose_note(124, channel_index=0, semitones=12) == 127
    assert transpose_note(3, channel_index=0, semitones=-12) == 0

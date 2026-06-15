import mido

from midi_mixer_player.midi.tempo_map import estimate_length_seconds


def test_estimate_length_seconds_uses_tempo_changes():
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    track.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=480))
    track.append(mido.MetaMessage("set_tempo", tempo=1000000, time=0))
    track.append(mido.Message("note_on", channel=0, note=64, velocity=64, time=0))
    track.append(mido.Message("note_off", channel=0, note=64, velocity=0, time=480))

    assert estimate_length_seconds(mid) == 1.5

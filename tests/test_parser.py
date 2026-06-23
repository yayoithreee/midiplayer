import mido

from midi_mixer_player.midi.parser import load_midi_info


def test_load_midi_info_reads_channels_and_programs(tmp_path):
    midi_path = tmp_path / "song.mid"
    mid = mido.MidiFile(type=1, ticks_per_beat=480)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name="Test Song", time=0))
    mid.tracks.append(meta)

    music = mido.MidiTrack()
    music.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    music.append(mido.Message("program_change", channel=0, program=40, time=0))
    music.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=0))
    music.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=480))
    music.append(mido.Message("note_on", channel=9, note=35, velocity=100, time=0))
    music.append(mido.Message("note_off", channel=9, note=35, velocity=0, time=120))
    mid.tracks.append(music)
    mid.save(midi_path)

    info = load_midi_info(midi_path)

    assert info.title == "Test Song"
    assert info.midi_format == 1
    assert info.track_count == 2
    assert info.base_bpm == 120
    assert info.channels[0].used is True
    assert info.channels[0].program_name == "Violin"
    assert info.channels[9].used is True
    assert info.channels[9].program_name == "Drum"

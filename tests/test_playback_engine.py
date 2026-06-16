import mido

from midi_mixer_player.audio.playback_engine import expand_midi_messages
from midi_mixer_player.core.models import MixerState


def test_expand_midi_messages_orders_by_absolute_time(tmp_path):
    midi_path = tmp_path / "ordered.mid"
    mid = mido.MidiFile(type=1, ticks_per_beat=480)

    first = mido.MidiTrack()
    first.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=480))
    mid.tracks.append(first)

    second = mido.MidiTrack()
    second.append(mido.Message("program_change", channel=0, program=40, time=0))
    mid.tracks.append(second)

    mid.save(midi_path)

    messages = expand_midi_messages(midi_path)

    assert [message.message.type for message in messages] == ["program_change", "note_on"]
    assert messages[0].seconds == 0
    assert messages[1].seconds == 0.5


def test_mixer_state_mute_and_solo_rules():
    state = MixerState()

    assert state.channel_can_sound(0) is True

    state.channels[0].mute = True
    assert state.channel_can_sound(0) is False

    state.channels[0].mute = False
    state.channels[1].solo = True
    assert state.channel_can_sound(0) is False
    assert state.channel_can_sound(1) is True


def test_mixer_state_reset_restores_tempo_and_key():
    state = MixerState()
    state.tempo_percent = 150
    state.key_semitones = -5
    state.master_volume = 64
    state.channels[0].mute = True
    state.channels[0].solo = True
    state.channels[0].volume = 64

    state.reset()

    assert state.tempo_percent == 100
    assert state.key_semitones == 0
    assert state.master_volume == 100
    assert state.channels[0].mute is False
    assert state.channels[0].solo is False
    assert state.channels[0].volume == 100


def test_mixer_state_effective_channel_volume_applies_master():
    state = MixerState()
    state.master_volume = 64
    state.channels[0].volume = 100

    assert state.effective_channel_volume(0) == 50

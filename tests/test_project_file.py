from pathlib import Path

import pytest

from midi_mixer_player.core.models import MixerState
from midi_mixer_player.core.project_file import ProjectFileError, load_project, save_project


def test_project_file_round_trip(tmp_path):
    project_path = tmp_path / "song.mmix.json"
    midi_path = tmp_path / "song.mid"
    state = MixerState()
    state.tempo_percent = 125
    state.key_semitones = -3
    state.channels[0].mute = True
    state.channels[1].solo = True
    state.channels[2].volume = 72

    save_project(project_path, midi_path, state)
    loaded_midi_path, loaded_state = load_project(project_path)

    assert loaded_midi_path == midi_path
    assert loaded_state.tempo_percent == 125
    assert loaded_state.key_semitones == -3
    assert loaded_state.channels[0].mute is True
    assert loaded_state.channels[1].solo is True
    assert loaded_state.channels[2].volume == 72


def test_project_file_rejects_unsupported_version(tmp_path):
    project_path = tmp_path / "old.mmix.json"
    project_path.write_text('{"version": 999, "midi_file": "song.mid"}', encoding="utf-8")

    with pytest.raises(ProjectFileError):
        load_project(project_path)


def test_project_file_clamps_loaded_values(tmp_path):
    project_path = tmp_path / "clamp.mmix.json"
    project_path.write_text(
        """
        {
          "version": 1,
          "midi_file": "song.mid",
          "tempo_percent": 500,
          "key_semitones": -99,
          "channels": [
            {"index": 0, "volume": 999, "pan": -10}
          ]
        }
        """,
        encoding="utf-8",
    )

    midi_path, state = load_project(project_path)

    assert midi_path == Path("song.mid")
    assert state.tempo_percent == 200
    assert state.key_semitones == -12
    assert state.channels[0].volume == 127
    assert state.channels[0].pan == 0

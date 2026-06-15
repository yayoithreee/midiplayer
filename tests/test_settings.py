from midi_mixer_player.core.settings import AppSettings, SettingsStore


def test_settings_round_trip(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    expected = AppSettings(
        soundfont_path="C:/soundfonts/test.sf2",
        last_open_dir="C:/midis",
        window_width=900,
        window_height=600,
        default_volume=88,
        ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
    )

    store.save(expected)
    actual = store.load()

    assert actual == expected

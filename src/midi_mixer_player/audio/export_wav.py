from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import mido

from midi_mixer_player.audio.fluidsynth_runtime import configure_fluidsynth_runtime
from midi_mixer_player.core.models import MixerState
from midi_mixer_player.midi.transformer import transform_midi_for_export


class ExportError(RuntimeError):
    pass


def export_wav(
    midi_path: Path,
    soundfont_path: Path,
    output_path: Path,
    mixer_state: MixerState,
) -> None:
    if not midi_path.exists():
        raise ExportError(f"MIDIファイルが見つかりません: {midi_path}")
    if not soundfont_path.exists():
        raise ExportError(f"SoundFont が見つかりません: {soundfont_path}")

    fluidsynth_exe = _find_fluidsynth_exe()
    if fluidsynth_exe is None:
        raise ExportError("FluidSynth 本体が見つかりません。C:\\tools\\fluidsynth に展開してください。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid = mido.MidiFile(midi_path)
    transformed = transform_midi_for_export(mid, mixer_state)

    with tempfile.TemporaryDirectory(prefix="midi_mixer_player_") as tmp_dir:
        temp_midi = Path(tmp_dir) / "export.mid"
        transformed.save(temp_midi)
        command = [
            str(fluidsynth_exe),
            "-ni",
            "-F",
            str(output_path),
            "-r",
            "44100",
            str(soundfont_path),
            str(temp_midi),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()
        raise ExportError(f"WAV書き出しに失敗しました。\n{details}")


def _find_fluidsynth_exe() -> Path | None:
    for directory in configure_fluidsynth_runtime():
        candidate = directory / "fluidsynth.exe"
        if candidate.exists():
            return candidate

    for path_entry in __import__("os").environ.get("PATH", "").split(__import__("os").pathsep):
        candidate = Path(path_entry) / "fluidsynth.exe"
        if candidate.exists():
            return candidate
    return None

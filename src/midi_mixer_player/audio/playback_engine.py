from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import mido

from midi_mixer_player.core.models import MixerState
from midi_mixer_player.audio.fluidsynth_runtime import configure_fluidsynth_runtime
from midi_mixer_player.midi.tempo_map import build_tempo_map, tick_to_seconds
from midi_mixer_player.midi.transformer import transpose_note


class PlaybackError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TimedMessage:
    seconds: float
    message: mido.Message


class PlaybackEngine:
    def __init__(
        self,
        status_callback: Callable[[str], None] | None = None,
        position_callback: Callable[[float], None] | None = None,
    ) -> None:
        self.status_callback = status_callback
        self.position_callback = position_callback
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._lock = threading.Lock()
        self._synth = None
        self._soundfont_id: int | None = None
        self._messages: list[TimedMessage] = []
        self._midi_path: Path | None = None
        self._soundfont_path: Path | None = None
        self._started_at = 0.0
        self._start_offset = 0.0
        self._anchor_wall_time = 0.0
        self._anchor_position = 0.0
        self.current_position = 0.0
        self.total_seconds = 0.0

    @property
    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._pause_event.is_set()

    @property
    def is_paused(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and self._pause_event.is_set()

    def load(self, midi_path: Path, total_seconds: float) -> None:
        self.stop()
        self._midi_path = Path(midi_path)
        self._messages = expand_midi_messages(self._midi_path)
        self.total_seconds = total_seconds
        self.current_position = 0.0

    def play(self, soundfont_path: str, mixer_state: MixerState, start_offset: float | None = None) -> None:
        if self._midi_path is None:
            raise PlaybackError("MIDIファイルが読み込まれていません。")
        if not soundfont_path:
            raise PlaybackError("SoundFont が未設定です。Settings から .sf2 / .sf3 を選択してください。")
        if not Path(soundfont_path).exists():
            raise PlaybackError(f"SoundFont が見つかりません: {soundfont_path}")

        if self.is_paused and start_offset is None:
            self._pause_event.clear()
            self._anchor_wall_time = time.monotonic()
            self._anchor_position = self.current_position
            self._notify_status("再生中")
            return

        self.stop()
        self._start_synth(Path(soundfont_path))
        self._send_initial_channel_state(mixer_state)
        self._stop_event.clear()
        self._pause_event.clear()
        self._start_offset = max(0.0, start_offset if start_offset is not None else self.current_position)
        self.current_position = self._start_offset
        self._anchor_wall_time = time.monotonic()
        self._anchor_position = self._start_offset
        self._thread = threading.Thread(
            target=self._run,
            args=(mixer_state,),
            name="MIDI Playback",
            daemon=True,
        )
        self._thread.start()
        self._notify_status("再生中")

    def pause(self, mixer_state: MixerState) -> None:
        if not self._thread or not self._thread.is_alive():
            return
        self.current_position = self._song_position(mixer_state)
        self._pause_event.set()
        self._all_notes_off()
        self._notify_status("一時停止")

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None
        self.current_position = 0.0
        self._all_notes_off()
        self._notify_position(0.0)
        self._notify_status("停止")

    def seek(self, seconds: float, mixer_state: MixerState) -> None:
        was_playing = self.is_playing
        self.stop()
        self.current_position = max(0.0, min(seconds, self.total_seconds))
        self._notify_position(self.current_position)
        if was_playing and self._soundfont_path:
            self.play(str(self._soundfont_path), mixer_state, self.current_position)

    def apply_channel_state(self, channel_index: int, mixer_state: MixerState) -> None:
        if self._synth is None:
            return
        channel = mixer_state.channels[channel_index]
        with self._lock:
            self._synth.cc(channel_index, 7, channel.volume)
            if channel.mute or (mixer_state.has_solo() and not channel.solo):
                self._synth.cc(channel_index, 123, 0)

    def apply_tempo_or_key_change(self, mixer_state: MixerState) -> None:
        if self._thread and self._thread.is_alive():
            self.current_position = self._song_position(mixer_state)
            self._anchor_wall_time = time.monotonic()
            self._anchor_position = self.current_position
            self._all_notes_off()

    def shutdown(self) -> None:
        self.stop()
        if self._synth is not None:
            try:
                self._synth.delete()
            except Exception:
                pass
        self._synth = None

    def _run(self, mixer_state: MixerState) -> None:
        next_index = 0
        while next_index < len(self._messages) and self._messages[next_index].seconds < self._start_offset:
            message = self._messages[next_index].message
            if message.type == "program_change":
                self._send_message(message, mixer_state)
            next_index += 1

        try:
            while next_index < len(self._messages) and not self._stop_event.is_set():
                if self._pause_event.is_set():
                    time.sleep(0.03)
                    continue

                target = self._messages[next_index].seconds
                now_position = self._song_position(mixer_state)
                self.current_position = min(now_position, self.total_seconds)
                self._notify_position(self.current_position)

                if now_position + 0.002 < target:
                    tempo_factor = max(0.01, mixer_state.tempo_percent / 100)
                    time.sleep(min(0.02, (target - now_position) / tempo_factor))
                    continue

                self._send_message(self._messages[next_index].message, mixer_state)
                next_index += 1
        finally:
            if not self._stop_event.is_set():
                self.current_position = self.total_seconds
                self._notify_position(self.total_seconds)
                self._notify_status("再生完了")
            self._all_notes_off()

    def _start_synth(self, soundfont_path: Path) -> None:
        configure_fluidsynth_runtime()
        try:
            import fluidsynth
        except ImportError as exc:
            raise PlaybackError(
                "FluidSynth を読み込めません。`python -m pip install -r requirements.txt` の後、Windows 用 FluidSynth 本体もインストールしてください。"
            ) from exc

        if self._synth is not None and self._soundfont_path == soundfont_path:
            return

        if self._synth is not None:
            try:
                self._synth.delete()
            except Exception:
                pass

        try:
            synth = fluidsynth.Synth(samplerate=44100)
            synth.start(driver="dsound")
            soundfont_id = synth.sfload(str(soundfont_path))
            for channel in range(16):
                synth.program_select(channel, soundfont_id, 0, 0)
        except Exception as exc:
            raise PlaybackError(
                "FluidSynth の起動に失敗しました。FluidSynth 本体がインストールされているか確認してください。"
            ) from exc

        self._synth = synth
        self._soundfont_id = soundfont_id
        self._soundfont_path = soundfont_path

    def _send_initial_channel_state(self, mixer_state: MixerState) -> None:
        if self._synth is None:
            return
        with self._lock:
            for channel in mixer_state.channels:
                self._synth.cc(channel.index, 7, channel.volume)
                self._synth.cc(channel.index, 10, channel.pan)

    def _send_message(self, message: mido.Message, mixer_state: MixerState) -> None:
        if self._synth is None or not hasattr(message, "channel"):
            return

        channel_index = message.channel
        if not mixer_state.channel_can_sound(channel_index) and message.type in {"note_on", "note_off"}:
            return

        channel_state = mixer_state.channels[channel_index]
        with self._lock:
            if message.type == "note_on":
                velocity = message.velocity
                note = transpose_note(message.note, channel_index, mixer_state.key_semitones)
                if velocity > 0:
                    self._synth.noteon(channel_index, note, velocity)
                else:
                    self._synth.noteoff(channel_index, note)
            elif message.type == "note_off":
                note = transpose_note(message.note, channel_index, mixer_state.key_semitones)
                self._synth.noteoff(channel_index, note)
            elif message.type == "control_change":
                value = message.value
                if message.control == 7:
                    value = round(value * channel_state.volume / 127)
                self._synth.cc(channel_index, message.control, max(0, min(127, value)))
            elif message.type == "program_change":
                if self._soundfont_id is not None:
                    self._synth.program_select(channel_index, self._soundfont_id, 0, message.program)
            elif message.type == "pitchwheel":
                self._synth.pitch_bend(channel_index, message.pitch)

    def _all_notes_off(self) -> None:
        if self._synth is None:
            return
        with self._lock:
            for channel in range(16):
                try:
                    self._synth.cc(channel, 123, 0)
                    self._synth.cc(channel, 120, 0)
                except Exception:
                    pass

    def _notify_status(self, message: str) -> None:
        if self.status_callback:
            self.status_callback(message)

    def _notify_position(self, seconds: float) -> None:
        if self.position_callback:
            self.position_callback(seconds)

    def _song_position(self, mixer_state: MixerState | None) -> float:
        tempo_percent = mixer_state.tempo_percent if mixer_state else 100
        tempo_factor = max(0.01, tempo_percent / 100)
        elapsed_wall = time.monotonic() - self._anchor_wall_time
        return max(0.0, self._anchor_position + elapsed_wall * tempo_factor)


def expand_midi_messages(midi_path: Path) -> list[TimedMessage]:
    mid = mido.MidiFile(midi_path)
    tempo_map = build_tempo_map(mid)
    messages: list[tuple[int, mido.Message]] = []

    for track in mid.tracks:
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
            if message.is_meta:
                continue
            if hasattr(message, "channel"):
                messages.append((absolute_tick, message.copy(time=0)))

    messages.sort(key=lambda item: item[0])
    return [
        TimedMessage(
            seconds=tick_to_seconds(tick, mid.ticks_per_beat, tempo_map),
            message=message,
        )
        for tick, message in messages
    ]

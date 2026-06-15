from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from midi_mixer_player.audio.export_wav import ExportError, export_wav
from midi_mixer_player.audio.playback_engine import PlaybackEngine, PlaybackError
from midi_mixer_player.core.models import MixerState
from midi_mixer_player.core.settings import AppSettings, SettingsStore
from midi_mixer_player.midi.parser import MidiLoadError, load_midi_info
from midi_mixer_player.ui.mixer_strip import MixerStrip
from midi_mixer_player.ui.settings_dialog import SettingsDialog


class PlaybackSignals(QObject):
    status_changed = Signal(str)
    position_changed = Signal(float)


class ExportWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        midi_path: Path,
        soundfont_path: Path,
        output_path: Path,
        mixer_state: MixerState,
    ) -> None:
        super().__init__()
        self.midi_path = midi_path
        self.soundfont_path = soundfont_path
        self.output_path = output_path
        self.mixer_state = mixer_state

    def run(self) -> None:
        try:
            export_wav(self.midi_path, self.soundfont_path, self.output_path, self.mixer_state)
        except ExportError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"予期しないエラーでWAV書き出しに失敗しました: {exc}")
        else:
            self.finished.emit(str(self.output_path))


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self.settings_store = settings_store
        self.settings = self.settings_store.load()
        self.current_midi_path: Path | None = None
        self.current_midi_length = 0.0
        self.mixer_state = MixerState()
        self.playback_signals = PlaybackSignals()
        self.export_thread: QThread | None = None
        self.export_worker: ExportWorker | None = None
        self.playback_engine = PlaybackEngine(
            status_callback=self.playback_signals.status_changed.emit,
            position_callback=self.playback_signals.position_changed.emit,
        )
        self.mixer_strips = [MixerStrip(i) for i in range(16)]

        self.setWindowTitle("MIDI Mixer Player")
        self.resize(self.settings.window_width, self.settings.window_height)
        self._build_ui()
        self.playback_signals.status_changed.connect(self._on_playback_status)
        self.playback_signals.position_changed.connect(self._on_playback_position)
        self._update_soundfont_status()

    def closeEvent(self, event) -> None:
        self.playback_engine.shutdown()
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings_store.save(self.settings)
        super().closeEvent(event)

    def _build_ui(self) -> None:
        self._build_toolbar()

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        transport_layout = QHBoxLayout()
        self.open_button = QPushButton("Open MIDI")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.rewind_button = QPushButton("Rewind")
        self.reset_button = QPushButton("Reset")
        self.export_button = QPushButton("Export WAV")

        for button in [
            self.play_button,
            self.pause_button,
            self.stop_button,
            self.rewind_button,
            self.export_button,
        ]:
            button.setEnabled(False)

        self.open_button.clicked.connect(self.open_midi)
        self.play_button.clicked.connect(self.play_midi)
        self.pause_button.clicked.connect(self.pause_midi)
        self.stop_button.clicked.connect(self.stop_midi)
        self.rewind_button.clicked.connect(self.rewind_midi)
        self.reset_button.clicked.connect(self.reset_controls)
        self.export_button.clicked.connect(self.export_current_wav)

        transport_layout.addWidget(self.open_button)
        transport_layout.addWidget(self.play_button)
        transport_layout.addWidget(self.pause_button)
        transport_layout.addWidget(self.stop_button)
        transport_layout.addWidget(self.rewind_button)
        transport_layout.addWidget(self.reset_button)
        transport_layout.addWidget(self.export_button)
        transport_layout.addStretch(1)

        self.song_label = QLabel("MIDI: 未選択")
        self.position_label = QLabel("00:00 / 00:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderReleased.connect(self.seek_midi)
        self.soundfont_warning_label = QLabel("")
        self.soundfont_warning_label.setStyleSheet("color: #9a4b00; font-weight: 600;")

        control_grid = QGridLayout()
        self.tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self.tempo_slider.setRange(50, 200)
        self.tempo_slider.setValue(100)
        self.tempo_value_label = QLabel("100%")
        self.tempo_slider.valueChanged.connect(self.set_tempo)

        self.key_slider = QSlider(Qt.Orientation.Horizontal)
        self.key_slider.setRange(-12, 12)
        self.key_slider.setValue(0)
        self.key_value_label = QLabel("0")
        self.key_slider.valueChanged.connect(self.set_key)

        control_grid.addWidget(QLabel("Tempo"), 0, 0)
        control_grid.addWidget(self.tempo_slider, 0, 1)
        control_grid.addWidget(self.tempo_value_label, 0, 2)
        control_grid.addWidget(QLabel("Key"), 1, 0)
        control_grid.addWidget(self.key_slider, 1, 1)
        control_grid.addWidget(self.key_value_label, 1, 2)

        info_group = QGroupBox("MIDI情報")
        info_layout = QGridLayout(info_group)
        self.info_file = QLabel("-")
        self.info_format = QLabel("-")
        self.info_tracks = QLabel("-")
        self.info_ticks = QLabel("-")
        self.info_length = QLabel("-")
        info_layout.addWidget(QLabel("ファイル名"), 0, 0)
        info_layout.addWidget(self.info_file, 0, 1)
        info_layout.addWidget(QLabel("Format"), 1, 0)
        info_layout.addWidget(self.info_format, 1, 1)
        info_layout.addWidget(QLabel("Tracks"), 2, 0)
        info_layout.addWidget(self.info_tracks, 2, 1)
        info_layout.addWidget(QLabel("Ticks/beat"), 3, 0)
        info_layout.addWidget(self.info_ticks, 3, 1)
        info_layout.addWidget(QLabel("推定時間"), 4, 0)
        info_layout.addWidget(self.info_length, 4, 1)

        mixer_container = QWidget()
        mixer_layout = QHBoxLayout(mixer_container)
        mixer_layout.setContentsMargins(0, 0, 0, 0)
        mixer_layout.setSpacing(6)
        for strip in self.mixer_strips:
            strip.mute_changed.connect(self.set_channel_mute)
            strip.solo_changed.connect(self.set_channel_solo)
            strip.volume_changed.connect(self.set_channel_volume)
            mixer_layout.addWidget(strip)
        mixer_layout.addStretch(1)

        mixer_scroll = QScrollArea()
        mixer_scroll.setWidgetResizable(True)
        mixer_scroll.setWidget(mixer_container)

        root_layout.addLayout(transport_layout)
        root_layout.addWidget(self.song_label)
        root_layout.addWidget(self.position_label)
        root_layout.addWidget(self.seek_slider)
        root_layout.addWidget(self.soundfont_warning_label)
        root_layout.addLayout(control_grid)
        root_layout.addWidget(info_group)
        root_layout.addWidget(mixer_scroll, 1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("準備完了")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = toolbar.addAction("Open")
        settings_action = toolbar.addAction("Settings")
        export_action = toolbar.addAction("Export")
        help_action = toolbar.addAction("Help")

        open_action.triggered.connect(self.open_midi)
        settings_action.triggered.connect(self.open_settings)
        export_action.triggered.connect(self.export_current_wav)
        help_action.triggered.connect(self.show_about)

    def open_midi(self) -> None:
        start_dir = self.settings.last_open_dir or str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self,
            "MIDIファイルを開く",
            start_dir,
            "MIDI Files (*.mid *.midi);;All Files (*)",
        )
        if not path:
            return

        try:
            midi_info = load_midi_info(path)
        except MidiLoadError as exc:
            QMessageBox.warning(self, "読み込みエラー", str(exc))
            self.statusBar().showMessage("MIDI読み込みに失敗しました")
            return

        self.current_midi_path = midi_info.path
        self.current_midi_length = midi_info.estimated_seconds
        self.playback_engine.load(midi_info.path, midi_info.estimated_seconds)
        self.settings.last_open_dir = str(midi_info.path.parent)
        self.settings_store.save(self.settings)
        self._show_midi_info(midi_info)
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.rewind_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.statusBar().showMessage(f"読み込みました: {midi_info.path.name}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        self.settings.soundfont_path = dialog.soundfont_path()
        self.settings_store.save(self.settings)
        self._update_soundfont_status()
        self.statusBar().showMessage("設定を保存しました")

    def reset_controls(self) -> None:
        self.mixer_state.reset()
        self.tempo_slider.setValue(100)
        self.key_slider.setValue(0)
        for strip in self.mixer_strips:
            strip.reset_state()
        for index in range(16):
            self.playback_engine.apply_channel_state(index, self.mixer_state)
        self.statusBar().showMessage("設定を初期値に戻しました")

    def play_midi(self) -> None:
        try:
            self.playback_engine.play(self.settings.soundfont_path, self.mixer_state)
        except PlaybackError as exc:
            QMessageBox.warning(self, "再生エラー", str(exc))
            self.statusBar().showMessage("再生できませんでした")

    def pause_midi(self) -> None:
        self.playback_engine.pause(self.mixer_state)

    def stop_midi(self) -> None:
        self.playback_engine.stop()

    def rewind_midi(self) -> None:
        self.playback_engine.seek(0.0, self.mixer_state)
        self._on_playback_position(0.0)

    def seek_midi(self) -> None:
        self.playback_engine.seek(float(self.seek_slider.value()), self.mixer_state)

    def export_current_wav(self) -> None:
        if self.current_midi_path is None:
            QMessageBox.information(self, "WAV書き出し", "先にMIDIファイルを開いてください。")
            return
        if not self.settings.soundfont_path:
            QMessageBox.warning(
                self,
                "WAV書き出し",
                "SoundFont が未設定です。Settings から .sf2 / .sf3 を選択してください。",
            )
            return

        default_name = self.current_midi_path.with_suffix(".wav").name
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "WAVを書き出す",
            str(Path(self.settings.last_open_dir or self.current_midi_path.parent) / default_name),
            "WAV Files (*.wav);;All Files (*)",
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".wav"):
            output_path += ".wav"

        self.export_button.setEnabled(False)
        self.statusBar().showMessage("WAVを書き出しています...")
        self.export_thread = QThread(self)
        self.export_worker = ExportWorker(
            self.current_midi_path,
            Path(self.settings.soundfont_path),
            Path(output_path),
            deepcopy(self.mixer_state),
        )
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.failed.connect(self._on_export_failed)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.failed.connect(self.export_thread.quit)
        self.export_thread.finished.connect(self._cleanup_export_thread)
        self.export_thread.start()

    def set_channel_mute(self, channel_index: int, checked: bool) -> None:
        self.mixer_state.channels[channel_index].mute = checked
        self.playback_engine.apply_channel_state(channel_index, self.mixer_state)

    def set_channel_solo(self, channel_index: int, checked: bool) -> None:
        self.mixer_state.channels[channel_index].solo = checked
        for index in range(16):
            self.playback_engine.apply_channel_state(index, self.mixer_state)

    def set_channel_volume(self, channel_index: int, value: int) -> None:
        self.mixer_state.channels[channel_index].volume = value
        self.playback_engine.apply_channel_state(channel_index, self.mixer_state)

    def set_tempo(self, value: int) -> None:
        self.mixer_state.tempo_percent = value
        self.tempo_value_label.setText(f"{value}%")
        self.playback_engine.apply_tempo_or_key_change(self.mixer_state)

    def set_key(self, value: int) -> None:
        self.mixer_state.key_semitones = value
        self.key_value_label.setText(str(value))
        self.playback_engine.apply_tempo_or_key_change(self.mixer_state)

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "MIDI Mixer Player",
            "MIDI Mixer Player\n\nPhase 3-4: ミキサー状態とFluidSynth再生を実装中です。",
        )

    def _show_midi_info(self, midi_info) -> None:
        length_text = self._format_seconds(midi_info.estimated_seconds)
        self.song_label.setText(f"MIDI: {midi_info.title}")
        self.position_label.setText(f"00:00 / {length_text}")
        self.seek_slider.setRange(0, max(0, int(round(midi_info.estimated_seconds))))
        self.seek_slider.setValue(0)
        self.seek_slider.setEnabled(True)
        self.info_file.setText(midi_info.path.name)
        self.info_format.setText(str(midi_info.midi_format))
        self.info_tracks.setText(str(midi_info.track_count))
        self.info_ticks.setText(str(midi_info.ticks_per_beat))
        self.info_length.setText(length_text)

        for strip, channel in zip(self.mixer_strips, midi_info.channels, strict=True):
            strip.update_channel(channel)

    def _update_soundfont_status(self) -> None:
        if self.settings.soundfont_path:
            self.soundfont_warning_label.setText("")
            self.statusBar().showMessage(f"SoundFont: {Path(self.settings.soundfont_path).name}")
        else:
            self.soundfont_warning_label.setText(
                "SoundFont が未設定です。Settings から .sf2 / .sf3 を選択してください。"
            )

    def _show_phase_message(self, message: str) -> None:
        QMessageBox.information(self, "未実装", message)

    def _on_playback_status(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_playback_position(self, seconds: float) -> None:
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(int(round(seconds)))
        self.position_label.setText(
            f"{self._format_seconds(seconds)} / {self._format_seconds(self.current_midi_length)}"
        )

    def _on_export_finished(self, output_path: str) -> None:
        self.statusBar().showMessage(f"WAVを書き出しました: {output_path}")
        QMessageBox.information(self, "WAV書き出し", f"保存しました:\n{output_path}")

    def _on_export_failed(self, message: str) -> None:
        self.statusBar().showMessage("WAV書き出しに失敗しました")
        QMessageBox.warning(self, "WAV書き出しエラー", message)

    def _cleanup_export_thread(self) -> None:
        self.export_button.setEnabled(self.current_midi_path is not None)
        if self.export_worker is not None:
            self.export_worker.deleteLater()
        if self.export_thread is not None:
            self.export_thread.deleteLater()
        self.export_worker = None
        self.export_thread = None

    @staticmethod
    def _format_seconds(seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        minutes, remainder = divmod(total_seconds, 60)
        return f"{minutes:02d}:{remainder:02d}"

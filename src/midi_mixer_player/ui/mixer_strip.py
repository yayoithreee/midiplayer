from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSlider,
    QVBoxLayout,
)

from midi_mixer_player.core.models import ChannelInfo


class MixerStrip(QFrame):
    mute_changed = Signal(int, bool)
    solo_changed = Signal(int, bool)
    volume_changed = Signal(int, int)

    def __init__(self, channel_index: int, parent=None) -> None:
        super().__init__(parent)
        self.channel_index = channel_index
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(78)
        self.setMaximumWidth(96)

        self.channel_label = QLabel(str(channel_index + 1))
        self.channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.program_label = QLabel("-")
        self.program_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.program_label.setWordWrap(True)
        self.program_label.setMinimumHeight(48)

        self.used_label = QLabel("未使用")
        self.used_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mute_checkbox = QCheckBox("消音")
        self.solo_checkbox = QCheckBox("ソロ")
        self.mute_checkbox.toggled.connect(
            lambda checked: self.mute_changed.emit(self.channel_index, checked)
        )
        self.solo_checkbox.toggled.connect(
            lambda checked: self.solo_changed.emit(self.channel_index, checked)
        )

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedHeight(150)
        self.volume_slider.valueChanged.connect(
            self._on_volume_changed
        )

        self.level_meter = QProgressBar()
        self.level_meter.setOrientation(Qt.Orientation.Vertical)
        self.level_meter.setRange(0, 127)
        self.level_meter.setValue(0)
        self.level_meter.setTextVisible(False)
        self.level_meter.setFixedSize(12, 150)

        self.volume_label = QLabel("音量 100")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)
        layout.addWidget(self.channel_label)
        layout.addWidget(self.program_label)
        layout.addWidget(self.used_label)
        layout.addWidget(self.mute_checkbox)
        layout.addWidget(self.solo_checkbox)
        fader_row = QFrame()
        fader_row_layout = QVBoxLayout(fader_row)
        fader_row_layout.setContentsMargins(0, 0, 0, 0)
        fader_row_layout.setSpacing(4)
        fader_pair = QFrame()
        fader_pair_layout = QHBoxLayout(fader_pair)
        fader_pair_layout.setContentsMargins(0, 0, 0, 0)
        fader_pair_layout.setSpacing(6)
        fader_pair_layout.addWidget(self.level_meter, alignment=Qt.AlignmentFlag.AlignHCenter)
        fader_pair_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        fader_row_layout.addWidget(fader_pair, alignment=Qt.AlignmentFlag.AlignHCenter)
        fader_row_layout.addWidget(self.volume_label)
        layout.addWidget(fader_row)

    def update_channel(self, info: ChannelInfo) -> None:
        self.channel_label.setText(str(info.display_number))
        self.program_label.setText(info.program_name)
        if info.used:
            self.used_label.setText(f"音数 {info.note_count}")
            self.setProperty("used", True)
        else:
            self.used_label.setText("未使用")
            self.setProperty("used", False)
        self.level_meter.setValue(0)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_level(self, value: int) -> None:
        self.level_meter.setValue(max(0, min(127, value)))

    def reset_state(self) -> None:
        self.mute_checkbox.setChecked(False)
        self.solo_checkbox.setChecked(False)
        self.volume_slider.setValue(100)

    def set_state(self, mute: bool, solo: bool, volume: int) -> None:
        self.mute_checkbox.blockSignals(True)
        self.solo_checkbox.blockSignals(True)
        self.volume_slider.blockSignals(True)
        self.mute_checkbox.setChecked(mute)
        self.solo_checkbox.setChecked(solo)
        self.volume_slider.setValue(volume)
        self.volume_label.setText(f"音量 {volume}")
        self.mute_checkbox.blockSignals(False)
        self.solo_checkbox.blockSignals(False)
        self.volume_slider.blockSignals(False)

    def _on_volume_changed(self, value: int) -> None:
        self.volume_label.setText(f"音量 {value}")
        self.volume_changed.emit(self.channel_index, value)

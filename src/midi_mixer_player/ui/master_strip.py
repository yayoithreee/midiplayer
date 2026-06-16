from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QSlider, QVBoxLayout


class MasterStrip(QFrame):
    volume_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(82)
        self.setMaximumWidth(102)

        title = QLabel("主音量")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.left_meter = QProgressBar()
        self.right_meter = QProgressBar()
        for meter in (self.left_meter, self.right_meter):
            meter.setOrientation(Qt.Orientation.Vertical)
            meter.setRange(0, 127)
            meter.setValue(0)
            meter.setTextVisible(False)
            meter.setFixedSize(12, 150)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedHeight(150)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.volume_label = QLabel("音量 100")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        meter_labels = QFrame()
        meter_label_layout = QHBoxLayout(meter_labels)
        meter_label_layout.setContentsMargins(0, 0, 0, 0)
        meter_label_layout.setSpacing(4)
        for text in ("L", "R", ""):
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedWidth(18)
            meter_label_layout.addWidget(label)

        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.addWidget(self.left_meter, alignment=Qt.AlignmentFlag.AlignHCenter)
        row_layout.addWidget(self.right_meter, alignment=Qt.AlignmentFlag.AlignHCenter)
        row_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)
        layout.addWidget(title)
        layout.addWidget(meter_labels)
        layout.addWidget(row, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.volume_label)

    def set_volume(self, value: int) -> None:
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(value)
        self.volume_label.setText(f"音量 {value}")
        self.volume_slider.blockSignals(False)

    def update_level(self, value: int) -> None:
        level = max(0, min(127, value))
        self.left_meter.setValue(level)
        self.right_meter.setValue(level)

    def _on_volume_changed(self, value: int) -> None:
        self.volume_label.setText(f"音量 {value}")
        self.volume_changed.emit(value)

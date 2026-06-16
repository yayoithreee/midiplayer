from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from midi_mixer_player.core.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.resize(640, 160)

        self.soundfont_edit = QLineEdit(settings.soundfont_path)
        self.soundfont_edit.setPlaceholderText("音源ファイル SoundFont (.sf2 / .sf3) を選択")

        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self._browse_soundfont)

        soundfont_layout = QHBoxLayout()
        soundfont_layout.addWidget(self.soundfont_edit, 1)
        soundfont_layout.addWidget(browse_button)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("キャンセル")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("音源ファイル"))
        layout.addLayout(soundfont_layout)
        layout.addStretch(1)
        layout.addLayout(button_layout)

    def soundfont_path(self) -> str:
        return self.soundfont_edit.text().strip()

    def _browse_soundfont(self) -> None:
        start_dir = str(Path(self.soundfont_edit.text()).parent) if self.soundfont_edit.text() else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "音源ファイルを選択",
            start_dir,
            "音源ファイル (*.sf2 *.sf3);;すべてのファイル (*)",
        )
        if path:
            self.soundfont_edit.setText(path)

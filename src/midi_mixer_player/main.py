from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from midi_mixer_player.app import create_app_window


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MIDI Mixer Player")
    window = create_app_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

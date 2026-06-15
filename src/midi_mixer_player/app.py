from __future__ import annotations

from midi_mixer_player.core.settings import SettingsStore
from midi_mixer_player.ui.main_window import MainWindow


def create_app_window() -> MainWindow:
    settings_store = SettingsStore()
    return MainWindow(settings_store=settings_store)

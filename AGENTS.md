# AGENTS.md

## Project goal
Build a modern Windows desktop MIDI mixer player inspired by classic 16-part MIDI players. The app must load MIDI files, play them through a user-selected SoundFont, provide a 16-channel mixer, allow mute/solo/volume, tempo changes, key transposition, and export WAV with the current settings applied.

## Legal / asset rules
- Do not reverse engineer, decompile, reuse, or bundle old proprietary WinGroove binaries, DLLs, drivers, or TPD files.
- Do not copy the original app name, logo, exact UI, or proprietary sound data.
- Implement a new app from scratch using open-source libraries.
- Do not bundle any SoundFont unless its license is checked and documented.

## Target user
Japanese Windows user. The UI and error messages should be friendly Japanese, not developer-only English.

## Tech stack
- Python 3.11+
- PySide6 for GUI
- mido for MIDI file parsing and message handling
- FluidSynth for SoundFont synthesis and WAV rendering
- PyInstaller for Windows packaging

## Development rules
- Keep the first version simple and reliable.
- Prefer readable code over clever code.
- Split UI, MIDI parsing, audio playback, and exporting into separate modules.
- Add unit tests for MIDI transformation logic.
- Do not block the UI thread during playback or export.
- Show understandable Japanese errors when SoundFont, FluidSynth, or MIDI loading fails.

## MVP acceptance criteria
- App starts on Windows.
- User can select a .sf2/.sf3 SoundFont.
- User can open a .mid file.
- 16 channels are shown as mixer strips.
- Play, pause, stop, rewind, and seek work.
- Mute, solo, and volume affect playback.
- Tempo 50-200% affects playback and WAV export.
- Key -12 to +12 semitones affects playback and WAV export.
- Channel 10 drums are not transposed.
- Export WAV creates a 44.1kHz stereo WAV reflecting mute/solo/volume/tempo/key.
- PyInstaller build works.

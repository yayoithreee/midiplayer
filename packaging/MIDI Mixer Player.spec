# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path.cwd()
SRC = ROOT / "src"


a = Analysis(
    [str(SRC / "midi_mixer_player" / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "fluidsynth",
        "mido.backends.rtmidi",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MIDI Mixer Player",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MIDI Mixer Player",
)

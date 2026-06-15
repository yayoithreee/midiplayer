from __future__ import annotations

import os
from pathlib import Path


def configure_fluidsynth_runtime() -> list[Path]:
    """Make common Windows FluidSynth ZIP installs visible to pyFluidSynth."""
    configured: list[Path] = []
    for directory in _candidate_bin_dirs():
        if not directory.exists():
            continue
        if not any(directory.glob("libfluidsynth*.dll")):
            continue
        os.environ["PATH"] = str(directory) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(directory))
        configured.append(directory)
    return configured


def _candidate_bin_dirs() -> list[Path]:
    candidates = [
        Path(r"C:\tools\fluidsynth\bin"),
    ]
    tools_root = Path(r"C:\tools\fluidsynth")
    if tools_root.exists():
        candidates.extend(path for path in tools_root.glob("*/bin") if path.is_dir())
    return candidates

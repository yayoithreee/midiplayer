$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m PyInstaller --clean --noconfirm "packaging\MIDI Mixer Player.spec"

Write-Host ""
Write-Host "Built: dist\MIDI Mixer Player\MIDI Mixer Player.exe"

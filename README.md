# MIDI Mixer Player

Windows 向けの 16 チャンネル MIDI ミキサープレーヤーです。MIDI ファイルの読み込み、16 チャンネルのミキサー表示、SoundFont パスの設定保存、FluidSynth による再生、テンポ/キー変更、WAV/MP3 書き出し、PyInstaller による exe ビルドまでを提供します。

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 起動

```powershell
python -m midi_mixer_player
```

または開発用に:

```powershell
python src\midi_mixer_player\main.py
```

## できること

- `.mid` / `.midi` ファイルを開く
- MIDI チャンネル 1-16 の使用状況を表示
- `program_change` から GM 音色名を表示
- チャンネル 10 を Drum として表示
- SoundFont `.sf2` / `.sf3` のパスを設定し、`settings.json` に保存
- FluidSynth と SoundFont を使って MIDI を再生
- Mute / Solo / Volume を再生に反映
- Play / Pause / Stop / Rewind / Seek の基本操作
- MIDI の基準テンポを BPM で表示し、50-200% 相当の範囲で再生に反映
- キー -12〜+12 半音を再生に反映
- チャンネル 10 のドラムは Key 変更の対象外
- 現在の Mute / Solo / Volume / テンポ / キーを反映して WAV 書き出し
- FluidSynth で 44.1kHz / 16bit / stereo WAV を生成
- ffmpeg が利用できる環境で MP3 192kbps 書き出し
- 縦型の主音量フェーダーと L/R レベルメーター
- 各チャンネルの縦型簡易リアルタイムレベルメーター
- 各チャンネルの音量値表示

## SoundFont について

このリポジトリには SoundFont を同梱しません。使用する `.sf2` / `.sf3` ファイルはユーザー自身で用意し、アプリ内の `Settings > SoundFont を選択...` から指定してください。

再生には SoundFont に加えて FluidSynth 本体が必要です。`pyFluidSynth` は Python から FluidSynth を呼び出すためのライブラリで、FluidSynth の DLL や実行環境そのものは別途必要になる場合があります。再生時に FluidSynth 起動エラーが出る場合は、Windows 用 FluidSynth をインストールしてください。

開発環境では、公式 ZIP を `C:\tools\fluidsynth` に展開した場合、アプリが `bin` フォルダを自動検出します。

## テスト

```powershell
python -m pytest
```

## exe ビルド

```powershell
.\build_exe.ps1
```

ビルド後の起動ファイル:

```text
dist\MIDI Mixer Player\MIDI Mixer Player.exe
```

## 配布時の注意

- SoundFont は同梱していません。ユーザーが `.sf2` / `.sf3` を用意して Settings から指定してください。
- FluidSynth 本体は同梱していません。開発環境では公式 ZIP を `C:\tools\fluidsynth` に展開すると自動検出します。
- FluidSynth や SoundFont を同梱する場合は、事前にライセンスを確認し、`THIRD_PARTY_LICENSES.md` に明記してください。

## 既知の制限

- レベルメーターは実音量解析ではなく簡易表示です。
- FluidSynth 本体または SoundFont が未設定の場合、再生とWAV/MP3書き出しはできません。
- MP3書き出しには ffmpeg が必要です。
- `.mmix.json` のプロジェクト保存/読み込み機能は内部実装済みですが、MIDIを開いて調整・書き出しする通常操作では不要なためメインUIからは外しています。

## 注意

古い WinGroove の EXE / DLL / DRV / TPD などは解析・流用・同梱しません。このアプリは機能的な代替を目指す新規実装です。

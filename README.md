# MIDI Mixer Player

Windows 向けの 16 チャンネル MIDI ミキサープレーヤーです。現在は Phase 1-6 の実装で、MIDI ファイルの読み込み、基本情報表示、16 チャンネルのミキサー表示、SoundFont パスの設定保存、FluidSynth による再生、Tempo/Key 変更、WAV 書き出しまでを提供します。

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
- format、tracks 数、ticks per beat、推定再生時間を表示
- MIDI チャンネル 1-16 の使用状況を表示
- `program_change` から GM 音色名を表示
- チャンネル 10 を Drum として表示
- SoundFont `.sf2` / `.sf3` のパスを設定し、`settings.json` に保存
- FluidSynth と SoundFont を使って MIDI を再生
- Mute / Solo / Volume を再生に反映
- Play / Pause / Stop / Rewind / Seek の基本操作
- Tempo 50-200% を再生に反映
- Key -12〜+12 semitones を再生に反映
- チャンネル 10 のドラムは Key 変更の対象外
- 現在の Mute / Solo / Volume / Tempo / Key を反映して WAV 書き出し
- FluidSynth で 44.1kHz / 16bit / stereo WAV を生成

## SoundFont について

このリポジトリには SoundFont を同梱しません。使用する `.sf2` / `.sf3` ファイルはユーザー自身で用意し、アプリ内の `Settings > SoundFont を選択...` から指定してください。

再生には SoundFont に加えて FluidSynth 本体が必要です。`pyFluidSynth` は Python から FluidSynth を呼び出すためのライブラリで、FluidSynth の DLL や実行環境そのものは別途必要になる場合があります。再生時に FluidSynth 起動エラーが出る場合は、Windows 用 FluidSynth をインストールしてください。

開発環境では、公式 ZIP を `C:\tools\fluidsynth` に展開した場合、アプリが `bin` フォルダを自動検出します。

## テスト

```powershell
python -m pytest
```

## Phase 7 TODO

- PyInstaller で Windows 向けポータブル exe を作る
- README に exe ビルド手順と既知の制限を追記する
- FluidSynth / SoundFont の同梱方針とライセンス確認を整理する

## 注意

古い WinGroove の EXE / DLL / DRV / TPD などは解析・流用・同梱しません。このアプリは機能的な代替を目指す新規実装です。

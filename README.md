# MIDI Mixer Player

Windows 向けの 16 チャンネル MIDI ミキサープレーヤーです。現在は Phase 1-2 の実装で、MIDI ファイルの読み込み、基本情報表示、16 チャンネルの使用状況と GM 音色名の表示、SoundFont パスの設定保存までを提供します。再生と WAV 書き出しは次フェーズで実装します。

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

## SoundFont について

このリポジトリには SoundFont を同梱しません。使用する `.sf2` / `.sf3` ファイルはユーザー自身で用意し、アプリ内の `Settings > SoundFont を選択...` から指定してください。

## テスト

```powershell
python -m pytest
```

## Phase 3-4 TODO

- 16 チャンネルの Mute / Solo / Volume 状態を内部モデルに保存する
- Reset でミキサー状態、Tempo、Key を初期化する
- FluidSynth を使った MIDI 再生エンジンを追加する
- 再生中に Mute / Solo / Volume を反映する
- UI スレッドをブロックしない再生制御を実装する
- SoundFont 未設定、FluidSynth 未検出、MIDI 読み込み失敗時の日本語エラーを強化する

## 注意

古い WinGroove の EXE / DLL / DRV / TPD などは解析・流用・同梱しません。このアプリは機能的な代替を目指す新規実装です。

# wav2text - 音声ファイル文字起こしツール

音声ファイルを自動で文字起こしし、TSV形式で出力するPythonスクリプトです。

**2つのバージョンを提供:**
- **Whisper版** (`transcribe.py`) - OpenAI Whisperを使用（オフライン動作可能）
- **Gemini版** (`transcribe_gemini.py`) - Google Gemini APIを使用（タイムスタンプ・スピーカー識別対応）

---

## 📋 目次

1. [Whisper版の使い方](#whisper版-transcribepy)
2. [Gemini版の使い方](#gemini版-transcribe_geminipy)
3. [比較表](#whisper版-vs-gemini版)

---

# Whisper版 (transcribe.py)

## 機能

- 複数の音声形式に対応（.wav, .mp3, .m4a）
- サブフォルダを含む再帰的なファイル検索
- 99言語以上の多言語対応
- **完全オフライン動作**
- 処理進捗のリアルタイム表示
- エラーハンドリングによる安定動作
- TSV形式での結果出力（ファイル名、テキスト、言語）

## セットアップ

### 1. 必要なソフトウェア

- Python 3.8以上
- FFmpeg（音声処理に必要）

#### FFmpegのインストール

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
[FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロードしてインストール

### 2. Pythonパッケージのインストール

```bash
pip install -r requirements.txt
```

※ 初回実行時、Whisperモデルが自動的にダウンロードされます（数百MB〜数GB）

## 使用方法

### 基本的な使い方

```bash
python transcribe.py
```

デフォルト設定で実行されます：
- 入力: `sources/` ディレクトリ
- 出力: `output/transcriptions.tsv`
- モデル: `medium`
- 言語: 日本語（`ja`）

### オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--input` | `-i` | `sources` | 音声ファイルが格納されているディレクトリ |
| `--output` | `-o` | `output/transcriptions.tsv` | 出力TSVファイルのパス |
| `--model` | `-m` | `medium` | Whisperモデルのサイズ |
| `--language` | `-l` | `ja` | 音声の言語コード（`auto`で自動判定） |
| `--extensions` | `-e` | `.wav .mp3 .m4a` | 処理する音声ファイルの拡張子 |

### モデルサイズの選択

| モデル | サイズ | 速度 | 精度 | メモリ | 推奨用途 |
|--------|-------|------|------|--------|---------|
| `tiny` | 39MB | 最速 | 低 | ~1GB | テスト・プロトタイプ |
| `base` | 74MB | 高速 | 中 | ~1GB | バランス型・日常用途 |
| `small` | 244MB | 中速 | 高 | ~2GB | 高精度が必要な場合 |
| `medium` | 769MB | やや遅 | 非常に高 | ~5GB | **推奨**・高品質 |
| `large` | 1.5GB | 遅 | 最高 | ~10GB | 最高品質が必要な場合 |
| `turbo` | 809MB | 高速 | 非常に高 | ~6GB | 速度と精度のバランス |

### 実行例

#### 例1: 特定のフォルダを処理

```bash
python transcribe.py --input source_dir 
```

#### 例2: 高速処理（小さいモデル使用）

```bash
python transcribe.py --model base
```

#### 例3: 言語を自動判定

```bash
python transcribe.py --language auto
```

#### 例4: 英語音声を処理

```bash
python transcribe.py --language en
```

#### 例5: カスタム出力先を指定

```bash
python transcribe.py --output results/my_transcriptions.tsv
```

#### 例6: すべてのオプションを指定

```bash
python transcribe.py \
  --input audio/ \
  --output results.tsv \
  --model small \
  --language auto \
  --extensions .wav .mp3
```

#### 例7: ヘルプを表示

```bash
python transcribe.py --help
```

## 出力形式

TSVファイルは以下の形式で出力されます：

```tsv
filename	text	language
audio1.wav	これはテストの音声ファイルです。	ja
audio2.mp3	This is a test audio file.	en
audio3.m4a	こんにちは、世界！	ja
```

| カラム | 説明 |
|--------|------|
| `filename` | 音声ファイル名 |
| `text` | 文字起こしされたテキスト |
| `language` | 検出された言語コード（ISO 639-1） |

## 対応言語

Whisperは99言語以上に対応しています。主な言語コード：

| 言語 | コード |
|------|-------|
| 日本語 | `ja` |
| 英語 | `en` |
| 中国語 | `zh` |
| 韓国語 | `ko` |
| スペイン語 | `es` |
| フランス語 | `fr` |
| ドイツ語 | `de` |
| イタリア語 | `it` |
| ロシア語 | `ru` |
| ポルトガル語 | `pt` |
| 自動判定 | `auto` |

完全なリストは[Whisperのドキュメント](https://github.com/openai/whisper)を参照してください。

## トラブルシューティング

### FFmpegが見つからないエラー

```
ERROR: ffmpeg not found
```

→ FFmpegをインストールしてください（セットアップの項を参照）

### メモリ不足エラー

```
OutOfMemoryError
```

→ より小さいモデル（`base`や`tiny`）を使用してください

### モデルのダウンロードが遅い

初回実行時、モデルが自動的にダウンロードされます。ネットワーク速度によっては時間がかかる場合があります。

### CUDA/GPU使用について

GPUが利用可能な場合、Whisperは自動的にGPUを使用して高速化します。CPU環境でも動作しますが、処理に時間がかかります。

---

# Gemini版 (transcribe_gemini.py)

## 機能

- 複数の音声形式に対応（.wav, .mp3, .m4a, .aac, .ogg, .flac）
- サブフォルダを含む再帰的なファイル検索
- 多言語対応
- **タイムスタンプ付き文字起こし**
- **スピーカー識別（話者分離）**
- **背景情報指定による精度向上**（固有名詞、専門用語の認識改善）
- 最大9.5時間の長時間音声対応
- クラウドベースの高速処理
- TSV形式での結果出力（ファイル名、テキスト、言語）

## セットアップ

### 1. 必要なもの

- Python 3.8以上
- Gemini API キー（[Google AI Studio](https://ai.google.dev/)から無料取得）

### 2. Pythonパッケージのインストール

```bash
pip install -r requirements_gemini.txt
```

### 3. API キーの設定

Gemini API キーを環境変数に設定します：

```bash
# macOS/Linux
export GEMINI_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:GEMINI_API_KEY="your-api-key-here"

# Windows (コマンドプロンプト)
set GEMINI_API_KEY=your-api-key-here
```

**恒久的に設定する場合:**

```bash
# ~/.bashrc または ~/.zshrc に追加
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## 使用方法

### 基本的な使い方

```bash
python transcribe_gemini.py
```

デフォルト設定で実行されます：
- 入力: `sources/` ディレクトリ
- 出力: `output/transcriptions_gemini.tsv`
- モデル: `gemini-2.5-pro`
- 言語: 日本語（`ja`）

### オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--input` | `-i` | `sources` | 音声ファイルが格納されているディレクトリ |
| `--output` | `-o` | `output/transcriptions_gemini.tsv` | 出力TSVファイルのパス |
| `--model` | `-m` | `gemini-2.5-flash` | Geminiモデルの選択 |
| `--language` | `-l` | `ja` | 音声の言語コード（`auto`で自動判定） |
| `--timestamps` | `-t` | なし | タイムスタンプ付きで文字起こし |
| `--speaker-diarization` | `-s` | なし | スピーカー識別を有効化 |
| `--context` | `-c` | なし | 背景情報・コンテキスト（精度向上） |
| `--extensions` | `-e` | `.wav .mp3 .m4a` | 処理する音声ファイルの拡張子 |
| `--api-key` | なし | 環境変数から取得 | Gemini API キーを直接指定 |

### モデルの選択

| モデル | 特徴 | 推奨用途 |
|--------|------|---------|
| `gemini-2.5-flash` | 高速・低コスト | 一般的な用途 |
| `gemini-2.5-pro` | **推奨**・最新版 | バランス型 |

### 実行例

#### 例1: 基本的な文字起こし

```bash
python transcribe_gemini.py --input source_dir
```

#### 例2: タイムスタンプ付き文字起こし

```bash
python transcribe_gemini.py --timestamps
```

#### 例3: スピーカー識別を有効化

```bash
python transcribe_gemini.py --speaker-diarization
```

#### 例4: タイムスタンプとスピーカー識別を両方有効化

```bash
python transcribe_gemini.py --timestamps --speaker-diarization
```

#### 例5: 背景情報を指定して精度向上

```bash
python transcribe_gemini.py --context "これはゲーム開発に関する会議です。登場人物：田中、佐藤"
```

#### 例6: 言語を自動判定

```bash
python transcribe_gemini.py --language auto
```

#### 例7: 英語音声を処理

```bash
python transcribe_gemini.py --language en
```

#### 例8: すべてのオプションを指定

```bash
python transcribe_gemini.py \
  --input audio/ \
  --output results_gemini.tsv \
  --model gemini-2.5-flash \
  --language ja \
  --timestamps \
  --speaker-diarization \
  --context "医療関係の講演会"
```

#### 例9: API キーを直接指定

```bash
python transcribe_gemini.py --api-key "your-api-key-here"
```

#### 例10: ヘルプを表示

```bash
python transcribe_gemini.py --help
```

## 出力形式

### 基本的な出力（タイムスタンプなし）

```tsv
filename	text	language
audio1.wav	これはテストの音声ファイルです。	ja
audio2.mp3	This is a test audio file.	ja
```

### タイムスタンプ付き出力

```tsv
filename	text	language
audio1.wav	[00:00] これはテストの音声ファイルです。[00:05] 次の文章です。	ja
```

### スピーカー識別付き出力

```tsv
filename	text	language
audio1.wav	話者1: こんにちは。話者2: はじめまして。	ja
```

## トラブルシューティング

### API キーが設定されていないエラー

```
エラー: Gemini API キーが設定されていません。
```

→ 環境変数 `GEMINI_API_KEY` を設定してください（セットアップの項を参照）

### API レート制限エラー

Gemini APIには無料枠でレート制限があります。大量のファイルを処理する場合は、処理速度を調整するか、有料プランを検討してください。

### ファイルアップロードエラー

非常に大きなファイル（2GB以上）の場合、エラーが発生することがあります。ファイルを分割して処理してください。

---

# Whisper版 vs Gemini版

## 比較表

| 項目 | Whisper版 | Gemini版 |
|------|----------|---------|
| **動作環境** | オフライン可能 | インターネット必須 |
| **コスト** | 無料（ローカル実行） | 従量課金制（無料枠あり） |
| **セットアップ** | FFmpegのインストール必要 | API キー取得のみ |
| **処理速度** | CPUでは遅い、GPU推奨 | 高速（クラウドGPU） |
| **精度** | 非常に高い | 高い |
| **言語対応** | 99言語以上 | 多言語対応 |
| **タイムスタンプ** | セグメント単位で取得可能 | ✅ プロンプトで指定 |
| **スピーカー識別** | 非対応 | ✅ 対応 |
| **背景情報指定** | 非対応 | ✅ 対応（精度向上） |
| **最大音声長** | 制限なし（メモリ次第） | 9.5時間 |
| **モデルサイズ** | 39MB〜1.5GB（ローカル） | 不要（クラウド） |
| **プライバシー** | ✅ 完全ローカル | ❌ クラウド送信 |

## どちらを選ぶべきか？

### Whisper版を選ぶ場合

- ✅ プライバシーが重要（データをクラウドに送信したくない）
- ✅ オフラインで動作させたい
- ✅ 継続的に大量の音声を処理する（コスト重視）
- ✅ GPUが利用可能

### Gemini版を選ぶ場合

- ✅ タイムスタンプが必要
- ✅ スピーカー識別（話者分離）が必要
- ✅ 背景情報を指定して固有名詞・専門用語の精度を向上させたい
- ✅ セットアップを簡単にしたい（FFmpegのインストール不要）
- ✅ 高速処理が必要（CPUのみの環境）
- ✅ 長時間音声（数時間）を処理する

---

## ライセンス

このスクリプトはMITライセンスです。

## 謝辞

- [OpenAI Whisper](https://github.com/openai/whisper)
- [Google Gemini API](https://ai.google.dev/)

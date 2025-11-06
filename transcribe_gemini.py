#!/usr/bin/env python3
"""
音声ファイル文字起こしスクリプト (Gemini API版)
Google Gemini APIを使用して音声ファイルをテキストに変換し、TSV形式で出力します。
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import google.generativeai as genai
except ImportError:
    print("エラー: google-generativeaiがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("  pip install -r requirements_gemini.txt")
    sys.exit(1)


def find_audio_files(directory: Path, extensions: Tuple[str, ...] = ('.wav', '.mp3', '.m4a')) -> List[Path]:
    """
    指定されたディレクトリから音声ファイルを再帰的に検索します。

    Args:
        directory: 検索対象のディレクトリ
        extensions: 対象とする拡張子のタプル

    Returns:
        見つかった音声ファイルのPathオブジェクトのリスト
    """
    audio_files = []
    for ext in extensions:
        audio_files.extend(directory.rglob(f'*{ext}'))
    return sorted(audio_files)


def get_mime_type(file_path: Path) -> str:
    """
    ファイル拡張子からMIMEタイプを取得します。

    Args:
        file_path: 音声ファイルのパス

    Returns:
        MIMEタイプ文字列
    """
    ext = file_path.suffix.lower()
    mime_types = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mp3',
        '.m4a': 'audio/aac',
        '.aac': 'audio/aac',
        '.aiff': 'audio/aiff',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac'
    }
    return mime_types.get(ext, 'audio/wav')


def transcribe_audio(
    audio_path: Path,
    model_name: str = 'gemini-2.5-flash',
    language: str = 'ja',
    timestamps: bool = False,
    speaker_diarization: bool = False,
    context: str = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    音声ファイルを文字起こしします。

    Args:
        audio_path: 音声ファイルのパス
        model_name: 使用するGeminiモデル
        language: 言語（プロンプトに使用）
        timestamps: タイムスタンプを含めるか
        speaker_diarization: スピーカー識別を行うか
        context: 背景情報・コンテキスト（任意）

    Returns:
        (文字起こしテキスト, 言語コード) のタプル
    """
    try:
        # ファイルをアップロード
        print(f"  アップロード中...")
        mime_type = get_mime_type(audio_path)
        audio_file = genai.upload_file(path=str(audio_path), mime_type=mime_type)

        # ファイルが処理されるまで待機
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            raise ValueError(f"ファイルの処理に失敗しました: {audio_file.state.name}")

        # プロンプトを構築
        prompt_parts = []

        # 背景情報・コンテキストを追加
        if context:
            prompt_parts.append(f"【背景情報】\n{context}\n")

        if language == 'auto':
            prompt_parts.append("Transcribe the following audio.")
        else:
            language_names = {
                'ja': '日本語',
                'en': 'English',
                'zh': '中文',
                'ko': '한국어',
                'es': 'Español',
                'fr': 'Français',
                'de': 'Deutsch'
            }
            lang_name = language_names.get(language, language)
            prompt_parts.append(f"以下の音声を{lang_name}で文字起こししてください。")

        if timestamps:
            prompt_parts.append("各セグメントにタイムスタンプを付けてください。")

        if speaker_diarization:
            prompt_parts.append("複数の話者がいる場合は、話者を識別して区別してください（例：話者1、話者2）。")

        prompt_parts.append("文字起こしのテキストのみを出力してください。説明や注釈は不要です。")

        prompt = "\n".join(prompt_parts)

        # Gemini APIで文字起こし
        print(f"  文字起こし中...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, audio_file])

        # ファイルを削除（クリーンアップ）
        genai.delete_file(audio_file.name)

        text = response.text.strip()

        # 言語コードを取得（簡易的な判定）
        detected_language = language if language != 'auto' else 'unknown'

        return text, detected_language

    except Exception as e:
        print(f"  エラー: {audio_path.name} の処理中にエラーが発生しました: {e}")
        return None, None


def main():
    parser = argparse.ArgumentParser(
        description='Gemini APIを使用して音声ファイルを文字起こししてTSV形式で出力します。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト設定で実行（sources/ → output/transcriptions_gemini.tsv）
  python transcribe_gemini.py

  # 入力フォルダを指定
  python transcribe_gemini.py --input source_dir

  # タイムスタンプ付きで文字起こし
  python transcribe_gemini.py --timestamps

  # スピーカー識別を有効化
  python transcribe_gemini.py --speaker-diarization

  # 背景情報を指定（精度向上）
  python transcribe_gemini.py --context "これはゲーム開発に関する会議の録音です。登場人物：田中、佐藤"

  # すべてのオプションを指定
  python transcribe_gemini.py \\
    --input audio/ \\
    --output results.tsv \\
    --model gemini-2.0-flash \\
    --language ja \\
    --timestamps \\
    --speaker-diarization \\
    --context "医療関係の講演会"

注意:
  実行前に環境変数 GEMINI_API_KEY を設定してください:
    export GEMINI_API_KEY="your-api-key-here"
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default='sources',
        help='音声ファイルが格納されているディレクトリ（デフォルト: sources）'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output/transcriptions_gemini.tsv',
        help='出力TSVファイルのパス（デフォルト: output/transcriptions_gemini.tsv）'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='gemini-2.5-pro',
        choices=['gemini-2.5-flash', 'gemini-2.5-pro'],
        help='Geminiモデルの選択（デフォルト: gemini-2.5-pro）'
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        default='ja',
        help='音声の言語コード（例: ja, en, auto）。autoで自動判定（デフォルト: ja）'
    )

    parser.add_argument(
        '--timestamps', '-t',
        action='store_true',
        help='タイムスタンプ付きで文字起こし'
    )

    parser.add_argument(
        '--speaker-diarization', '-s',
        action='store_true',
        help='スピーカー識別（話者分離）を有効化'
    )

    parser.add_argument(
        '--extensions', '-e',
        type=str,
        nargs='+',
        default=['.wav', '.mp3', '.m4a'],
        help='処理する音声ファイルの拡張子（デフォルト: .wav .mp3 .m4a）'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='Gemini API キー（環境変数 GEMINI_API_KEY からも読み込み可能）'
    )

    parser.add_argument(
        '--context', '-c',
        type=str,
        help='背景情報・コンテキスト（例: "これはゲーム開発に関する音声です"）'
    )

    args = parser.parse_args()

    # API キーの設定
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("エラー: Gemini API キーが設定されていません。")
        print("以下のいずれかの方法で設定してください:")
        print("  1. 環境変数: export GEMINI_API_KEY='your-api-key'")
        print("  2. コマンドライン引数: --api-key 'your-api-key'")
        print("\nAPI キーの取得方法:")
        print("  https://ai.google.dev/ にアクセスして取得してください")
        sys.exit(1)

    genai.configure(api_key=api_key)

    # 入力ディレクトリの確認
    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"エラー: 入力ディレクトリが見つかりません: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"エラー: 指定されたパスはディレクトリではありません: {input_dir}")
        sys.exit(1)

    # 出力ディレクトリの作成
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 音声ファイルの検索
    print(f"音声ファイルを検索中: {input_dir}")
    audio_files = find_audio_files(input_dir, tuple(args.extensions))

    if not audio_files:
        print(f"エラー: 音声ファイルが見つかりませんでした（対象拡張子: {', '.join(args.extensions)}）")
        sys.exit(1)

    print(f"見つかったファイル数: {len(audio_files)}")

    # Gemini API の準備確認
    print(f"\nGemini API設定:")
    print(f"  モデル: {args.model}")
    print(f"  言語: {args.language}")
    print(f"  タイムスタンプ: {'有効' if args.timestamps else '無効'}")
    print(f"  スピーカー識別: {'有効' if args.speaker_diarization else '無効'}")
    if args.context:
        print(f"  背景情報: {args.context}")
    print()

    # 文字起こし処理
    results = []
    successful = 0
    failed = 0

    print("文字起こしを開始します...")
    print("=" * 80)

    for i, audio_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] 処理中: {audio_path.name}")

        text, language = transcribe_audio(
            audio_path,
            model_name=args.model,
            language=args.language,
            timestamps=args.timestamps,
            speaker_diarization=args.speaker_diarization,
            context=args.context
        )

        if text is not None:
            results.append({
                'filename': audio_path.name,
                'text': text,
                'language': language
            })
            successful += 1
            # 処理結果のプレビュー（最初の80文字）
            preview = text[:80] + '...' if len(text) > 80 else text
            print(f"  完了: {preview}")
        else:
            failed += 1

        print()

    # TSVファイルへの書き込み
    print("=" * 80)
    print(f"\n結果をTSVファイルに書き込み中: {output_path}")

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'text', 'language'], delimiter='\t')
            writer.writeheader()
            writer.writerows(results)

        print(f"✓ TSVファイルを出力しました: {output_path}")
    except Exception as e:
        print(f"エラー: TSVファイルの書き込みに失敗しました: {e}")
        sys.exit(1)

    # サマリー
    print("\n" + "=" * 80)
    print("処理が完了しました")
    print(f"  成功: {successful} ファイル")
    print(f"  失敗: {failed} ファイル")
    print(f"  合計: {len(audio_files)} ファイル")
    print("=" * 80)


if __name__ == '__main__':
    main()

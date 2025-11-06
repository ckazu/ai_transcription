#!/usr/bin/env python3
"""
音声ファイル文字起こしスクリプト
Whisperを使用して音声ファイルをテキストに変換し、TSV形式で出力します。
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import whisper
except ImportError:
    print("エラー: whisperがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("  pip install -r requirements.txt")
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


def transcribe_audio(
    audio_path: Path,
    model: whisper.Whisper,
    language: str = None
) -> Tuple[str, str]:
    """
    音声ファイルを文字起こしします。

    Args:
        audio_path: 音声ファイルのパス
        model: Whisperモデル
        language: 言語コード（Noneの場合は自動判定）

    Returns:
        (文字起こしテキスト, 検出された言語コード) のタプル
    """
    try:
        # 言語が指定されている場合はそれを使用、そうでなければ自動判定
        if language and language.lower() != 'auto':
            result = model.transcribe(str(audio_path), language=language)
        else:
            result = model.transcribe(str(audio_path))

        text = result['text'].strip()
        detected_language = result.get('language', 'unknown')

        return text, detected_language

    except Exception as e:
        print(f"  エラー: {audio_path.name} の処理中にエラーが発生しました: {e}")
        return None, None


def main():
    parser = argparse.ArgumentParser(
        description='音声ファイルを文字起こししてTSV形式で出力します。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト設定で実行（sources/ → output/transcriptions.tsv）
  python transcribe.py

  # 入力フォルダを指定
  python transcribe.py --input source_dir

  # 小さいモデルで高速処理
  python transcribe.py --model base

  # 言語を自動判定
  python transcribe.py --language auto

  # すべてのオプションを指定
  python transcribe.py --input audio/ --output results.tsv --model small --language en
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
        default='output/transcriptions.tsv',
        help='出力TSVファイルのパス（デフォルト: output/transcriptions.tsv）'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='medium',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
        help='Whisperモデルのサイズ（デフォルト: medium）'
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        default='ja',
        help='音声の言語コード（例: ja, en, auto）。autoで自動判定（デフォルト: ja）'
    )

    parser.add_argument(
        '--extensions', '-e',
        type=str,
        nargs='+',
        default=['.wav', '.mp3', '.m4a'],
        help='処理する音声ファイルの拡張子（デフォルト: .wav .mp3 .m4a）'
    )

    args = parser.parse_args()

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

    # Whisperモデルのロード
    print(f"\nWhisperモデルをロード中: {args.model}")
    print("※ 初回実行時はモデルのダウンロードに時間がかかる場合があります")
    try:
        model = whisper.load_model(args.model)
    except Exception as e:
        print(f"エラー: モデルのロードに失敗しました: {e}")
        sys.exit(1)

    print("モデルのロードが完了しました\n")

    # 文字起こし処理
    results = []
    successful = 0
    failed = 0

    print("文字起こしを開始します...")
    print("=" * 80)

    for i, audio_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] 処理中: {audio_path.name}")

        text, language = transcribe_audio(audio_path, model, args.language)

        if text is not None:
            results.append({
                'filename': audio_path.name,
                'text': text,
                'language': language
            })
            successful += 1
            # 処理結果のプレビュー（最初の50文字）
            preview = text[:50] + '...' if len(text) > 50 else text
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

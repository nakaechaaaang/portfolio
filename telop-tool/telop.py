#!/usr/bin/env python3
"""フルテロップ自動化 — 一発コマンド。

    python telop.py "/path/to/動画.mp4"                # 自動判定（縦動画→short）
    python telop.py "/path/to/動画.mp4" --preset short # 強制ショート
    python telop.py "/path/to/動画.mp4" --preset default --model medium

動画(またはWAV)を渡すと、次を自動で進めます:
  1. 音声抽出（16kHz mono WAV / 作業フォルダに隔離）
  2. WhisperX 文字起こし＋強制アライメント（辞書で固有名詞ヒント＆誤変換補正）
  3. ブラウザ校閲UIを起動（JSONが真実。「校閲完了」を押すまで待機）
  4. 音にスナップ＋ゼロ隙間＋句読点削除（ショートは15文字で改行）で SRT 生成
  5. テロップを動画に焼き込み（--no-burn で省略可）

プリセット:
  - default … 横YouTube・セミナー用（青テロップ／画面下）
  - short   … 縦ショート用（白＋黒フチ・大きめ／15文字改行）

原則:
  - 元素材は触らない。中間ファイルは <動画の隣>/_telop_work/<名前>/ に隔離。
  - 校閲済み(reviewed=true)のJSONは絶対に上書きしない（再実行時は文字起こしを見送る）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline import audio as audio_mod
from pipeline import build, srt as srt_mod
from pipeline.config import DEFAULTS, PRESETS, Dictionary, preset as get_preset


def work_dir_for(src: Path) -> Path:
    d = src.parent / "_telop_work" / src.stem
    d.mkdir(parents=True, exist_ok=True)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="フルテロップ自動化パイプライン（系統B）")
    ap.add_argument("input", help="入力の動画またはWAV/音声ファイル")
    ap.add_argument("--dict", default=None, help="辞書JSON（既定: config/dictionary.json があれば使用）")
    ap.add_argument("--model", default=DEFAULTS["model"], help="WhisperXモデル (例: large-v3, medium, small)")
    ap.add_argument("--lang", default=DEFAULTS["language"], help="言語コード (既定: ja)")
    ap.add_argument("--offset", type=float, default=DEFAULTS["offset_sec"], help="タイミング補正秒")
    ap.add_argument("--gap", type=float, default=DEFAULTS["max_close_gap_sec"], help="ゼロ隙間化する最大秒")
    ap.add_argument("--preset", choices=list(PRESETS) + ["auto"], default="auto",
                    help="テロップ見た目（既定: auto=縦動画ならshort、横はdefault）")
    ap.add_argument("--port", type=int, default=8765, help="校閲UIのポート")
    ap.add_argument("--no-review", action="store_true", help="校閲UIを開かずそのままSRT生成")
    ap.add_argument("--no-burn", action="store_true", help="動画への焼き込みをしない（SRTのみ）")
    ap.add_argument("--no-open", action="store_true", help="ブラウザを自動で開かない")
    args = ap.parse_args(argv)

    src = Path(args.input).expanduser()
    if not src.exists():
        print(f"❌ 入力が見つかりません: {src}", file=sys.stderr)
        return 1

    here = Path(__file__).resolve().parent
    dict_path = args.dict or (here / "config" / "dictionary.json")
    dictionary = Dictionary.load(dict_path)

    # 動画を probe → 自動プリセット決定（縦動画ならshort）
    info = audio_mod.probe_video(src)
    if args.preset == "auto":
        chosen = "short" if info.get("is_vertical") else "default"
    else:
        chosen = args.preset
    pset = get_preset(chosen)
    if info:
        orient = "縦" if info.get("is_vertical") else "横"
        print(
            f"🎬 動画: {info['display_width']}x{info['display_height']} "
            f"({orient}・rotation={info['rotation']}) → preset={chosen}「{pset['label']}」"
        )
    else:
        print(f"🎬 preset={chosen}「{pset['label']}」")

    work = work_dir_for(src)
    wav_path = work / "audio.wav"
    doc_path = work / "review.json"
    srt_path = work / f"{src.stem}.srt"

    is_video = src.suffix.lower() in audio_mod.VIDEO_EXTS

    # ---- 校閲済みJSONがあれば、それを真実として再利用（上書きしない）----
    if doc_path.exists() and build.load_doc(doc_path).get("reviewed"):
        print(f"✓ 校閲済みJSONを再利用します（文字起こしは見送り）: {doc_path}")
    else:
        # 1) 音声抽出
        print("① 音声を抽出中 …")
        audio_mod.ensure_wav(src, wav_path)

        # 2) 文字起こし＋強制アライメント
        print(f"② WhisperX 文字起こし＋アライメント中（model={args.model}）…")
        from pipeline import transcribe as tr  # 重い import を遅延
        result = tr.transcribe(
            wav_path, model=args.model, language=args.lang,
            initial_prompt=dictionary.initial_prompt(),
        )
        doc = build.build_review_doc(
            source_video=str(src.resolve()),
            audio_path=str(wav_path.resolve()),
            language=args.lang,
            segments=result["segments"],
            dictionary=dictionary,
            offset_sec=args.offset,
            max_close_gap_sec=args.gap,
        )
        build.save_doc(doc_path, doc)
        print(f"   → 校閲JSONを書き出しました: {doc_path}（{len(doc['items'])}件）")

    # 3) 校閲UI
    if not args.no_review and not build.load_doc(doc_path).get("reviewed"):
        from pipeline import review_server
        review_server.run_review(doc_path, port=args.port, open_browser=not args.no_open)

    # 4) SRT 生成（JSON→派生）
    print(f"③ SRTを生成中（音スナップ＋ゼロ隙間＋句読点削除"
          f"{'＋15文字改行' if pset['wrap_chars'] else ''}）…")
    doc = build.load_doc(doc_path)
    srt_path.write_text(
        srt_mod.doc_to_srt(doc, wrap_chars=pset["wrap_chars"]),
        encoding="utf-8",
    )
    print(f"   → SRT: {srt_path}")

    # 5) 焼き込み
    if not args.no_burn:
        if not is_video:
            print("⚠ 入力が動画でないため焼き込みはスキップ（SRTのみ）。")
        else:
            print(f"④ テロップを焼き込み中（preset={chosen}・数分かかることがあります）…")
            from pipeline import burn
            out = work / f"{src.stem}_telop.mp4"
            burn.burn(src, srt_path, out, preset=chosen)
            print(f"   → 完成: {out}")

    print("\n✅ 完了。元素材はそのまま、生成物は作業フォルダにあります:")
    print(f"   {work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

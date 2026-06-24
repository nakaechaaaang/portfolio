# CLAUDE.md — フルテロップ自動化ツール（Claude Code 用 取扱説明書）

あなた（Claude Code）は、このフォルダで「動画にテロップ（字幕）を入れる」作業をユーザーの代わりに実行します。
ユーザーはコードが書けません。**専門用語を避け、日本語でやさしく**進めてください。

## このツールが何をするか

動画を渡すと、次を自動で行います:
1. 音声抽出（ffmpeg）
2. WhisperX で文字起こし＋強制アライメント（音と字幕がズレない核心）
3. ブラウザ校閲UI（`http://127.0.0.1:8765/`）を開く → ユーザーが直して「校閲完了」を押す
4. 音にスナップ＋ゼロ隙間＋句読点削除で SRT 生成
5. テロップを動画に焼き込み（縦ショート＝白＋黒フチ、横＝青テロップ）

## ユーザーが「この動画にテロップ入れて」と言ったら

1. **動画のパスを確認する**（ドラッグ＆ドロップされたパス、または聞く）。
2. 下のコマンドを **このフォルダ（telop-tool/）をカレントにして** 実行する:

```bash
source .venv/bin/activate
python telop.py "<動画のフルパス>" --model small
```

- `--model small` … 動作確認・短い動画用（速い）。本番で精度を上げたいときは `--model large-v3`（時間はかかる）。
- プリセットは**自動判定**（縦動画→ショート用テロップ、横動画→青テロップ）。
  - 強制したいときだけ `--preset short` または `--preset default` を付ける。
3. 実行すると **ブラウザの校閲画面が自動で開く**。ユーザーに「ブラウザで文字を直して『校閲完了』を押してください」と伝える。
4. 「校閲完了」が押されると処理が再開し、`✅ 完了` と出力先が表示される。
5. 完成物の場所をユーザーに伝える:
   - 焼き込み動画: `<動画の隣>/_telop_work/<動画名>/<動画名>_telop.mp4`
   - 字幕ファイル: 同フォルダの `.srt`（Premiere等に読み込む用）

## 大事な前提・注意

- **実行前に必ず仮想環境を有効化**: `source .venv/bin/activate`（プロンプトに `(.venv)` が付く）。
- 初回は WhisperX のモデルを自動ダウンロードするため時間がかかる（2回目以降は速い）。
- `torchcodec is not installed correctly` という警告が出るが**無視してOK**（ffmpegを直接使うため実害なし）。
- 長い動画（30分超など）はCPUだと非常に遅い。テストは**短いクリップ**を勧める。
  必要なら ffmpeg で切り出す: `ffmpeg -ss 0 -t 30 -i "元.mp4" -c copy "test30s.mp4"`
- **元動画は絶対に変更しない**。中間ファイルは `_telop_work/` に隔離される。
- **校閲済み（reviewed=true）の review.json は上書きしない**。やり直したいときはそのフォルダの `review.json` を消してから再実行する。

## 誤変換が多いとき

`config/dictionary.json` を編集する（無ければ `config/dictionary.example.json` をコピー）:
- `proper_nouns` … 固有名詞のヒント（人名・サービス名・英単語）
- `corrections` … 確定した誤変換の置換（例: `{"from":"クロードコード","to":"Claude Code"}`）

## テロップの見た目を変えたいとき

`pipeline/config.py` の `PRESETS` を編集（フォント・色・サイズ・位置）。
ASS色は `&HAABBGGRR`（青=`&H00FF0000`、白=`&H00FFFFFF`、黒=`&H00000000`）。

## セットアップがまだの場合（初回のみ）

```bash
brew install ffmpeg          # 既に入っていればスキップ
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/dictionary.example.json config/dictionary.json
```
※ Python は 3.11 推奨（3.14 など新しすぎる版は whisperx が入らないことがある）。

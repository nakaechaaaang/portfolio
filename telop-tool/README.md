# telop-tool — フルテロップ自動化パイプライン（系統B）

動画を入れると、**喋り出しとピタッと合う**テロップを、**1フレームのチカッなし**で入れる仕組みです。
note記事「1本36時間かかっていた動画編集が…」の **系統B（セミナー字幕専用パイプライン）** を再現したものです。

```
動画/WAV
  → ① 音声抽出（ffmpeg）
  → ② WhisperX 文字起こし＋強制アライメント（辞書で固有名詞ヒント＆誤変換補正）
  → ③ ブラウザ校閲UI（JSONが真実）
  → ④ 音にスナップ＋ゼロ隙間＋句読点削除で SRT 生成
  → ⑤ 青テロップを動画に焼き込み
```

一発で：

```bash
python telop.py "/Users/shuhei/Documents/Videos/Furikou/Claude Codeのプレビューで選んで修正する.mp4"
```

---

## なぜ「ズレない」のか（核心）

普通の Whisper の単語タイムスタンプは、実音より少し早く／大ざっぱに出るのでズレます。
このツールは **WhisperX** を使い、文字起こしの後に **wav2vec2 による強制アライメント**を1回かけて、
各単語を実音の位置に **<100ms** でピン留めします。これが「喋り出しと9割合致」の正体です。

その上で、記事の手作業を機械化しています：

| 記事の悩み | このツールの対応 | 実装 |
| --- | --- | --- |
| 前後キャプションが混ざる | セグメント単位で出し、校閲UIで人が最終調整 | `review/` |
| 喋り始めとズレる | 強制アライメント＋単語の切れ目にスナップ＋オフセット補正 | `pipeline/transcribe.py`, `pipeline/srt.py` |
| 1フレームの「チカッ」 | 隣接字幕の小さな隙間を自動でゼロ化 | `pipeline/srt.py` |
| 誤変換・名前間違い | 案件ごとに育てる辞書（固有名詞ヒント＋誤変換補正） | `config/dictionary.json` |

---

## 使っている主なOSS（GitHubスター多数）

- **[m-bain/whisperX](https://github.com/m-bain/whisperx)** ★21.8k — 文字起こし＋強制アライメント（核心）
- **[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)** ★14k — WhisperX が内部で使う高速バックエンド
- **[FFmpeg](https://ffmpeg.org/)** — 音声抽出・青テロップ焼き込み

（記事の固有のロジック＝オフセット補正・単語スナップ・ゼロ隙間・JSON真実／SRT派生・校閲済み保護
は、WhisperX の上に本ツールが実装したものです。）

---

## セットアップ（Mac）

```bash
# 1) ffmpeg（音声抽出・焼き込み用）
brew install ffmpeg

# 2) Python 環境（3.10〜3.11 推奨）
cd telop-tool
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # whisperx を入れる

# 3) 辞書を用意（案件ごとに育てる）
cp config/dictionary.example.json config/dictionary.json
```

> 初回は WhisperX がモデルを自動ダウンロードします。GPUがなくても動きますが、
> CPUでは時間がかかります。`--model medium` で軽くできます。

---

## 使い方

```bash
# フル（推奨）: 文字起こし → 校閲UI → SRT → 青テロップ焼き込み
python telop.py "～.mp4"

# 校閲UIを使わず一気にSRT/焼き込みまで
python telop.py "～.mp4" --no-review

# 焼き込みせずSRTだけ欲しい（Premiereに投入する運用）
python telop.py "～.mp4" --no-burn

# モデルや補正を変える
python telop.py "～.mp4" --model medium --offset 0.25 --gap 0.8
```

実行すると、③でブラウザの校閲UIが開きます。
テキスト修正・不要字幕の削除・フィラー確認をして **「校閲完了」** を押すと、SRT生成と焼き込みに進みます。

### 出力場所（元素材は触りません）

生成物はすべて **動画の隣の作業フォルダ** に隔離されます：

```
<動画のフォルダ>/_telop_work/<動画名>/
├─ audio.wav          # 抽出した音声
├─ review.json        # 校閲データ（★これが真実）
├─ <動画名>.srt       # Premiere投入用の字幕（JSONからの派生）
└─ <動画名>_telop.mp4 # 青テロップ焼き込み済み動画
```

---

## 守っている4つの原則（記事の通り）

1. **校閲データ(JSON)が真実、SRTは派生** — 校閲は `review.json` に対して行い、SRTは毎回そこから生成。
   タイミング・句読点・分割をやり直しても安全。
2. **校閲済みJSONは絶対に上書きしない** — `reviewed=true` のJSONを見つけたら、文字起こしを自動で見送って残します。
3. **AI(LLM)の判断を機械ロジックに置き換えない** — フィラー（「えー」等）は校閲UIで黄色の **候補**として出すだけ。
   削除は人が判断します。
4. **元素材を消さない** — 動画・WAVは元の場所のまま。中間ファイルは `_telop_work/` に隔離。

---

## カスタマイズ

- **テロップの色・フォント**: `pipeline/config.py` の `burn_style`。
  ASS色は `&HAABBGGRR`（青=`&H00FF0000`）。既定は青文字＋白フチ。
- **タイミング補正**: `--offset`（全体を前後にずらす）／`--gap`（ゼロ隙間化する最大秒）。
- **辞書**: `config/dictionary.json` に `proper_nouns`（固有名詞ヒント）と
  `corrections`（誤変換の確定置換）を案件ごとに追記して育てます。

---

## 注意

このリポジトリ（クラウド環境）では WhisperX の実行やffmpeg焼き込みの **動作確認はできていません**
（GPU・モデル・実ファイルが無いため）。SRT生成ロジックのみ手元で検証済みです。
お手元のMacでセットアップ後に実行してください。問題が出たらログと一緒に教えてください。

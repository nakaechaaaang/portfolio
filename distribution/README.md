# ポートフォリオサイト テンプレート & 構築マニュアル

HTML / CSS / JavaScript だけで作る、1ページ完結のポートフォリオサイトの**配布用テンプレート**です。
個人情報はすべて仮の文字（プレースホルダ）に置き換えてあるので、書き換えるだけで自分のサイトが作れます。
公開は無料の [surge.sh](https://surge.sh) を使います。

> 📖 ブラウザで読める説明書（Webマニュアル）が `guide/` に入っています。
> `guide/` を surge.sh に公開すれば、そのまま「他の人向けの手順サイト」として配布できます。

---

## 📂 フォルダ構成

```
distribution/
├─ README.md          ← この説明書
├─ template/          ← 配布用テンプレート（個人情報なし）
│  ├─ index.html      ← 文章・見出しを書き換えるメインファイル
│  ├─ style.css       ← デザイン（基本そのままでOK）
│  ├─ script.js       ← アニメーションなどの動き（編集不要）
│  ├─ expiry.js       ← 公開期限の自動管理（3週間で自動「期限切れ」）
│  └─ images/         ← プロフィール・実績画像（仮のSVG入り）
└─ guide/             ← surge.shに公開できるWebマニュアル
   ├─ index.html
   └─ style.css
```

---

## 🚀 クイックスタート（5ステップ）

### 1. テンプレートをコピー
`template/` を丸ごとコピーして作業用フォルダ（例：`my-portfolio`）にします。

### 2. `index.html` を書き換える
エディタ（[VS Code](https://code.visualstudio.com/) 推奨）で開き、`<!-- ✏️ 編集: … -->`
というコメントが付いている箇所を自分の情報に置き換えます。

| 場所 | 仮の文字 | 入れる内容 |
|------|----------|-----------|
| タブのタイトル | `あなたの名前 \| ポートフォリオ` | サイト名・氏名 |
| ロゴ／フッター | `YourName` | 表示名（英字推奨）|
| ヒーロー | `Your Title` / キャッチコピー | 肩書き・キャッチコピー |
| About | `あなたの名前` / 自己紹介文 | 氏名・肩書き・経歴 |
| スキル | `スキル1〜5` / `95%` | スキル名と習熟度 |
| 実績 | `実績タイトル1〜6` | 実績の内容・タグ |
| ツール | `ツール1〜3` | 使えるツール紹介 |
| お問い合わせ | `YOUR_GOOGLE_FORM_URL` | GoogleフォームのURL |

> ⚠️ スキルバーの数値は `<span class="skill-pct">95%</span>` と `style="width:95%"` の
> **2か所**を同じ数字にそろえてください。

### 3. 画像を差し替える
`images/` のSVGを自分の画像に置き換えます。詳しくは `template/images/README.txt` を参照。
（プロフィールは正方形、実績は横長16:9、各500KB以内を推奨）

### 4. お問い合わせフォームを用意する
[Googleフォーム](https://forms.google.com/) を作り、共有URLを `index.html` の
`YOUR_GOOGLE_FORM_URL` に貼り付けます。

### 5. surge.sh で公開する

```bash
# 初回のみ：公開ツールをインストール
npm install --global surge

# 作業フォルダに移動して公開
cd my-portfolio
surge
```

初回はメールアドレスとパスワードを聞かれ、アカウントが作られます。
続いて `domain:` で `好きな名前.surge.sh` を入力すると、そのURLで公開されます。

> 🔁 **更新するとき**は、編集後に同じフォルダで `surge ./ 好きな名前.surge.sh` を実行するだけ。
> ❌ **削除するとき**は `surge teardown 好きな名前.surge.sh`。

---

## ⏳ 3週間で自動「期限切れ」にする機能

公開から**3週間（21日）が過ぎると、ページを自動的に「期限切れ」表示に切り替える**機能が入っています。
`expiry.js` の先頭で公開日を設定するだけです。

```js
const PUBLISH_DATE = '2026-06-14'; // 公開した日（YYYY-MM-DD）
const VALID_DAYS   = 21;           // 公開期間。3週間=21日
```

**期限が過ぎると：**

- ページの内容（個人情報を含む）が画面から自動的に削除される
- ブラウザに保存されたデータ（localStorage・Cookie・キャッシュ等）も自動で消去される
- 「このページの公開は終了しました」という画面が表示される

> ⚠️ この仕組みはブラウザ側（JavaScript）で動くため、**サーバー上のファイル自体は残ります**。
> 元ファイルまで完全に消すには `surge teardown 好きな名前.surge.sh` でサイトごと削除してください。

### 🤖 サーバー上のファイルも全自動で削除する（GitHub Actions）

「3週間後に `surge teardown` を全自動で実行してファイルごと消したい」場合は、
同梱の GitHub Actions ワークフロー **`.github/workflows/auto-teardown.yml`** を使います。
毎日1回チェックし、期限を過ぎていたら自動でサイトを削除します。

**設定手順:**

1. **トークンを取得**（手元のターミナルで実行）
   ```bash
   surge token
   ```
2. **GitHubに登録**（リポジトリの Settings → Secrets and variables → Actions）
   - Secrets に `SURGE_LOGIN`（surgeのメール）と `SURGE_TOKEN`（上で取得したトークン）を追加
3. **ワークフローを編集**（`.github/workflows/auto-teardown.yml` 上部の `env:`）
   ```yaml
   SURGE_DOMAIN: 'your-name.surge.sh'  # 公開したドメイン
   PUBLISH_DATE: '2026-06-14'          # expiry.js と同じ公開日
   VALID_DAYS: '21'                    # 公開期間（3週間）
   ```
4. **デフォルトブランチ（main）にこのファイルを置く**
   （スケジュール実行は main ブランチ上のワークフローでのみ動きます）

> 💡 設定前・未設定の場合は何もせず安全にスキップします。`workflow_dispatch` で手動実行して動作確認もできます。

---

## 📘 Webマニュアル（guide/）を公開する

`guide/` フォルダには、上記の手順をまとめた**ブラウザで読める説明書サイト**が入っています。
配布相手向けに公開する場合：

```bash
cd guide
surge ./ portfolio-guide.surge.sh   # 好きなドメイン名でOK
```

---

## ❓ よくある質問

| 質問 | 回答 |
|------|------|
| `surge: command not found` | `npm install --global surge` を実行。Node.js が必要です |
| 画像が出ない | ファイル名の打ち間違い（大文字小文字も区別）か `images/` 外にある |
| お金はかかる？ | surge.sh・Node.js・VS Code・Googleフォームすべて無料 |
| 独自ドメインを使いたい | GitHub Pages / Netlify / Vercel でも同じファイルのまま公開可能 |

---

## 📝 ライセンス

このテンプレートは自由に改変・利用できます。あなただけのポートフォリオを作ってください。

# サクレコ（Sakureco）ポートフォリオ

シンプルな1ページ構成のポートフォリオサイトです。
**HTML / CSS / JavaScript だけ**で動き、サーバーやデータベースは不要。
無料の [surge.sh](https://surge.sh) や [GitHub Pages](https://pages.github.com/) で公開できます。

🔗 デモ（本人版）: https://sakureco.surge.sh/

---

## 📦 誰でも使える配布版はこちら → [`distribution/`](./distribution)

個人情報をすべて仮の文字（プレースホルダ）に置き換えた**配布用テンプレート**と、
プログラミング未経験でも作れる**構築マニュアル**を用意しています。
書き換えるだけで、あなただけのポートフォリオが作れます。

```
distribution/
├─ README.md      ← 構築マニュアル（まずはこれを読む）
├─ template/      ← 配布用テンプレート（個人情報なし・そのまま使える）
│  ├─ index.html  ← 文章・見出しを書き換えるメインファイル
│  ├─ style.css   ← デザイン
│  ├─ script.js   ← アニメーションなどの動き
│  ├─ auth.js     ← （任意）パスワードロック。既定はOFF
│  ├─ expiry.js   ← （任意）公開から3週間で自動「期限切れ」
│  └─ images/     ← プロフィール・実績画像（仮のSVG入り）
└─ guide/         ← ブラウザで読める説明書サイト（surge.sh等に公開可）
```

### つかいかた（最短）

1. **このリポジトリをダウンロード**
   緑の「Code ▸ Download ZIP」または
   `https://github.com/nakaechaaaang/portfolio/archive/refs/heads/main.zip`
2. **`distribution/template/` をコピー**して、`index.html` の `<!-- ✏️ 編集: … -->`
   の箇所を自分の情報に書き換える
3. **公開する**（どちらでもOK）
   - surge.sh: `npm i -g surge` → `surge`
   - GitHub Pages: 自分のリポジトリに置いて Settings → Pages を有効化

詳しい手順・カスタマイズ・FAQ は **[`distribution/README.md`](./distribution/README.md)** を参照してください。

---

## ✨ 主な機能

- スマホ／タブレット／PC対応（レスポンシブ）
- お問い合わせは Google フォームに飛ばすだけ（サーバー処理不要）
- （任意）パスワードによる簡易ロック
- （任意）公開から3週間で自動「期限切れ」＋ブラウザ保存データ消去
- （任意）GitHub Actions で公開期限後にサイトを自動削除

## 📝 ライセンス

自由に改変・利用できます。あなただけのポートフォリオを作ってください。

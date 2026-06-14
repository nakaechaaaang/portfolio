画像の差し替え方法
====================

このフォルダには仮の画像（プレースホルダ）が入っています。
同じファイル名で自分の画像に置き換えると、自動的に反映されます。

  profile.svg   … プロフィール写真（正方形・600x600px 以上推奨）
  project1.svg  … 実績1のサムネイル（横長 16:9・1200x675px 推奨）
  project2.svg  … 実績2のサムネイル
  project3.svg  … 実績3のサムネイル
  project4.svg  … 実績4のサムネイル
  project5.svg  … 実績5のサムネイル
  project6.svg  … 実績6のサムネイル

【おすすめの手順】
1. 自分の画像を profile.jpg / project1.jpg のような名前で用意する
2. index.html の <img src="images/profile.svg"> を
   <img src="images/profile.jpg"> のように拡張子まで書き換える
   （または画像を .svg と同じ名前にリネームしてもOK）

【容量の注意】
写真は1枚 500KB 以内を目安に圧縮しましょう（読み込みが速くなります）。
画像圧縮サイト例: https://squoosh.app/ , https://tinypng.com/

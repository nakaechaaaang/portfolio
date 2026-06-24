"""設定値・プリセット・辞書の読み込み。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ---- 沼を経て守る原則を、そのまま既定値にしています ----
DEFAULTS = {
    # WhisperX
    "model": "large-v3",      # 文字精度を最優先（案件向け）
    "language": "ja",

    # タイミング補正
    # Whisper の単語タイムスタンプは実音より少し早めに出る傾向があります。
    # 正の値を入れると字幕全体を「後ろ」へずらします（記事では +0.25 前後）。
    # WhisperX の強制アライメントは精度が高いので既定は 0.0。環境に合わせて調整。
    "offset_sec": 0.0,

    # 字幕と字幕の「1フレームのチカッ」を消す。
    # 隣り合う字幕の隙間がこの秒数以下なら、前の字幕の終了を次の開始まで延ばして
    # 隙間をゼロにします。これより大きい隙間は「本当の間（ま）」として残します。
    "max_close_gap_sec": 1.0,

    # 1つの字幕の最短表示秒数（短すぎる点滅を防ぐ）
    "min_duration_sec": 0.4,

    # SRT 生成時に取り除く句読点・記号
    "strip_punctuation": "。、，．・「」『』（）()！？!?…：:；;　",
}


# ---- 用途別プリセット ----
# 「default」… 横YouTube・セミナー用（青テロップ／画面下中央）
# 「short」  … 縦ショート用（白＋黒フチ・大きめ・1行15文字で改行）
#
# burn_style は ffmpeg subtitles の force_style 文字列。
# ASS色は &HAABBGGRR（AA=透明度, BB=青, GG=緑, RR=赤）。
# Alignment: 1=左下, 2=中央下, 3=右下, 5=中央, 8=中央上
PRESETS = {
    "default": {
        "label": "横動画（青テロップ／画面下）",
        "wrap_chars": 0,           # 0 = 改行しない
        "burn_style": (
            "FontName=Hiragino Sans,Fontsize=18,Bold=1,"
            "PrimaryColour=&H00FF0000&,"     # 文字色=青
            "OutlineColour=&H00FFFFFF&,"     # フチ=白
            "BorderStyle=1,Outline=2,Shadow=0,"
            "Alignment=2,MarginV=48"
        ),
    },
    "short": {
        "label": "縦ショート（白＋黒フチ・大きめ）",
        "wrap_chars": 15,          # 1行15文字で自動改行（縦動画でハミ出さない）
        "burn_style": (
            "FontName=Hiragino Sans W7,Fontsize=22,Bold=1,"
            "PrimaryColour=&H00FFFFFF&,"     # 文字色=白
            "OutlineColour=&H00000000&,"     # フチ=黒
            "BorderStyle=1,Outline=3,Shadow=0,"
            "Alignment=2,MarginV=110"        # 縦動画の下から少し上（顔の下くらい）
        ),
    },
}


def preset(name: str) -> dict:
    if name not in PRESETS:
        raise ValueError(
            f"未知のプリセット: {name!r}（使えるのは: {list(PRESETS)}）"
        )
    return PRESETS[name]


@dataclass
class Dictionary:
    """案件ごとに育てる辞書（固有名詞ヒント・誤変換補正・フィラー候補）。"""
    proper_nouns: list[str] = field(default_factory=list)
    corrections: list[dict] = field(default_factory=list)
    filler_candidates: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path | None) -> "Dictionary":
        if not path:
            return cls()
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            proper_nouns=data.get("proper_nouns", []),
            corrections=data.get("corrections", []),
            filler_candidates=data.get("filler_candidates", []),
        )

    def initial_prompt(self) -> str | None:
        """Whisper に固有名詞を教えるための initial_prompt を作る。"""
        if not self.proper_nouns:
            return None
        return "、".join(self.proper_nouns)

    def apply_corrections(self, text: str) -> str:
        for c in self.corrections:
            frm, to = c.get("from"), c.get("to")
            if frm:
                text = text.replace(frm, to)
        return text

    def is_filler(self, text: str) -> bool:
        """テキストがフィラー候補だけで構成されているか（削除は人が判断する用の目印）。"""
        t = text.strip().strip("。、！？!?…・ 　")
        return bool(t) and t in self.filler_candidates

"""WhisperX セグメント → 校閲JSON（itemsモデル）への変換と読み書き。

原則:
- 校閲データ(JSON)が真実。SRTはここから生成される派生物。
- 校閲済み(reviewed=true)のJSONは絶対に上書きしない。
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import Dictionary

SCHEMA_VERSION = 1


def _words_of(segment: dict) -> list[dict]:
    """セグメントから {w,s,e} の単語リストを作る。タイムスタンプ欠損は補間。"""
    raw = segment.get("words", []) or []
    words: list[dict] = []
    for w in raw:
        token = w.get("word", "")
        words.append({
            "w": token,
            "s": w.get("start"),  # None のことがある
            "e": w.get("end"),
        })

    # 欠損(None)を前後の値で素朴に補間（アライメントが取れなかった単語向け）
    seg_s = segment.get("start")
    seg_e = segment.get("end")
    last = seg_s
    for i, w in enumerate(words):
        if w["s"] is None:
            w["s"] = last
        last = w["e"] if w["e"] is not None else w["s"]
    nxt = seg_e
    for w in reversed(words):
        if w["e"] is None:
            w["e"] = nxt
        nxt = w["s"] if w["s"] is not None else w["e"]
    return words


def segments_to_items(segments: list[dict], dictionary: Dictionary) -> list[dict]:
    items: list[dict] = []
    for i, seg in enumerate(segments, start=1):
        text = (seg.get("text") or "").strip()
        text = dictionary.apply_corrections(text)
        words = _words_of(seg)
        # 単語があれば、その切れ目を開始/終了の真値にする（音にスナップ）
        start = words[0]["s"] if words else seg.get("start", 0.0)
        end = words[-1]["e"] if words else seg.get("end", 0.0)
        items.append({
            "id": i,
            "text": text,
            "start": round(float(start or 0.0), 3),
            "end": round(float(end or 0.0), 3),
            "words": [
                {"w": w["w"], "s": round(float(w["s"] or 0.0), 3),
                 "e": round(float(w["e"] or 0.0), 3)} for w in words
            ],
            "filler": dictionary.is_filler(text),  # 候補ハイライトのみ。削除は人。
            "deleted": False,
        })
    return items


def build_review_doc(
    *, source_video: str, audio_path: str, language: str,
    segments: list[dict], dictionary: Dictionary,
    offset_sec: float, max_close_gap_sec: float,
) -> dict:
    return {
        "version": SCHEMA_VERSION,
        "source_video": source_video,
        "audio_path": audio_path,
        "language": language,
        "offset_sec": offset_sec,
        "max_close_gap_sec": max_close_gap_sec,
        "reviewed": False,
        "items": segments_to_items(segments, dictionary),
    }


def load_doc(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_doc(path: str | Path, doc: dict) -> None:
    Path(path).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

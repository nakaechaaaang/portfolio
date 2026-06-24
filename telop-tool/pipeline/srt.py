"""校閲JSON(真実) → SRT(派生) 生成。

ここで記事の3つの効果を作る:
1. 音にスナップ … 各字幕の開始/終了は単語の切れ目（words の s/e）を真値に使う。
2. オフセット補正 … offset_sec で全体を前後にずらす。
3. ゼロ隙間 … 隣接字幕の小さな隙間を埋めて「1フレームのチカッ」を消す。
さらに句読点を削除する。
"""
from __future__ import annotations

from .config import DEFAULTS


def _fmt_ts(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _strip_punct(text: str, chars: str) -> str:
    table = {ord(c): None for c in chars}
    return text.translate(table).strip()


def doc_to_cues(doc: dict) -> list[dict]:
    """校閲JSON から、タイミング確定済みのキュー列を作る。"""
    offset = float(doc.get("offset_sec", DEFAULTS["offset_sec"]))
    max_gap = float(doc.get("max_close_gap_sec", DEFAULTS["max_close_gap_sec"]))
    min_dur = float(doc.get("min_duration_sec", DEFAULTS["min_duration_sec"]))
    punct = doc.get("strip_punctuation", DEFAULTS["strip_punctuation"])

    cues: list[dict] = []
    for it in doc.get("items", []):
        if it.get("deleted"):
            continue
        text = _strip_punct(it.get("text", ""), punct)
        if not text:
            continue
        words = it.get("words") or []
        # 音にスナップ: 単語の切れ目を最優先。なければ item の start/end。
        start = words[0]["s"] if words else it.get("start", 0.0)
        end = words[-1]["e"] if words else it.get("end", 0.0)
        cues.append({
            "text": text,
            "start": float(start) + offset,
            "end": float(end) + offset,
        })

    cues.sort(key=lambda c: c["start"])

    # 隙間ゼロ化＋重なり解消＋最短表示の確保
    for i, c in enumerate(cues):
        nxt = cues[i + 1] if i + 1 < len(cues) else None
        if nxt:
            gap = nxt["start"] - c["end"]
            if gap < 0:
                # 重なり → 次の開始で切る
                c["end"] = nxt["start"]
            elif 0 < gap <= max_gap:
                # 小さな隙間 → 次の開始まで延ばしてチカッを消す
                c["end"] = nxt["start"]
        # 最短表示（次のキューを侵食しない範囲で）
        if c["end"] - c["start"] < min_dur:
            target = c["start"] + min_dur
            c["end"] = min(target, nxt["start"]) if nxt else target

    return cues


def doc_to_srt(doc: dict) -> str:
    cues = doc_to_cues(doc)
    blocks = []
    for i, c in enumerate(cues, start=1):
        blocks.append(
            f"{i}\n{_fmt_ts(c['start'])} --> {_fmt_ts(c['end'])}\n{c['text']}\n"
        )
    return "\n".join(blocks)

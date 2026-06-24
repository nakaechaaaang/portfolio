"""校閲JSON(真実) → SRT(派生) 生成。

ここで記事の3つの効果を作る:
1. 音にスナップ … 各字幕の開始/終了は単語の切れ目（words の s/e）を真値に使う。
2. オフセット補正 … offset_sec で全体を前後にずらす。
3. ゼロ隙間 … 隣接字幕の小さな隙間を埋めて「1フレームのチカッ」を消す。
さらに句読点を削除し、ショート向けには文字数で折返しを入れる。
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


# 行末に来てほしくない（行頭にも置きたくない）記号。
# ASS/SRT 自体は「\N」相当の改行を入れるだけなので、日本語の「禁則」を
# 軽くだけ守る：終わりカッコ・小さい仮名は前行に押し戻し、開きカッコは次行に送る。
_NO_LINE_START = set("、。．，！？!?）)」』］〕》〉…ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ")
_NO_LINE_END = set("（(「『［〔《〈")


def wrap_text(text: str, max_chars: int) -> str:
    """日本語向けの軽い折返し。max_chars 以下なら何もしない。

    - max_chars 文字ずつで切る
    - 行頭/行末に来てほしくない記号は1文字ずらして調整する
    - 改行は SRT の「リテラル改行」で表現（subtitlesフィルタが2行に描画）
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return text

    lines: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + max_chars, n)
        # 次の行頭に「、。)」が来そうなら、現在行に1文字含めて押し戻す
        if end < n and text[end] in _NO_LINE_START and end - i < max_chars + 2:
            end += 1
        # 現在行の末尾が「(『」など開きカッコなら、1文字次行に送る
        while end > i + 1 and text[end - 1] in _NO_LINE_END:
            end -= 1
        lines.append(text[i:end])
        i = end
    return "\n".join(lines)


def doc_to_cues(doc: dict, *, wrap_chars: int = 0) -> list[dict]:
    """校閲JSON から、タイミング確定済みのキュー列を作る。

    wrap_chars > 0 なら、各字幕テキストをその文字数で折返す（縦ショート用）。
    """
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
        if wrap_chars:
            text = wrap_text(text, wrap_chars)
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
                c["end"] = nxt["start"]
            elif 0 < gap <= max_gap:
                c["end"] = nxt["start"]
        if c["end"] - c["start"] < min_dur:
            target = c["start"] + min_dur
            c["end"] = min(target, nxt["start"]) if nxt else target

    return cues


def doc_to_srt(doc: dict, *, wrap_chars: int = 0) -> str:
    cues = doc_to_cues(doc, wrap_chars=wrap_chars)
    blocks = []
    for i, c in enumerate(cues, start=1):
        blocks.append(
            f"{i}\n{_fmt_ts(c['start'])} --> {_fmt_ts(c['end'])}\n{c['text']}\n"
        )
    return "\n".join(blocks)

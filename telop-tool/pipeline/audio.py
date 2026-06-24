"""音声抽出・動画プローブ。元動画は触らず、作業フォルダに 16kHz mono WAV を作る。"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac"}


def ensure_wav(src: str | Path, out_wav: str | Path) -> Path:
    """src（動画 or 音声）から WhisperX 用の 16kHz/mono WAV を作って返す。

    元素材は読み込むだけ。生成物は out_wav（作業フォルダ）に隔離する。
    """
    src = Path(src)
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(out_wav),
    ]
    subprocess.run(cmd, check=True)
    return out_wav


def probe_video(src: str | Path) -> dict:
    """ffprobe で動画の幅・高さ・回転情報を取得し、表示時の縦横を返す。

    iPhone/Android の縦動画は、ファイル上の解像度が 1920x1080 でも
    rotation=90 のメタデータで「縦表示」になります。これを考慮した
    表示寸法を出します（テロップ位置/フォントの基準に使う）。

    返り値:
        {
          "width": <ファイル上の幅>,
          "height": <ファイル上の高さ>,
          "rotation": <度>,        # 0/90/-90/180 等
          "display_width": <表示幅>,
          "display_height": <表示高さ>,
          "is_vertical": <縦動画ならTrue>,
        }
        動画でない（音声のみ等）の場合は空dict。
    """
    src = Path(src)
    if src.suffix.lower() not in VIDEO_EXTS:
        return {}

    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:stream_tags=rotate:side_data=rotation",
        "-of", "json", str(src),
    ]
    try:
        out = subprocess.check_output(cmd, text=True)
        data = json.loads(out)
    except Exception:
        return {}

    streams = data.get("streams") or []
    if not streams:
        return {}
    s = streams[0]
    w = int(s.get("width") or 0)
    h = int(s.get("height") or 0)

    rot = 0
    # 1) 旧来の "rotate" tag
    tag = (s.get("tags") or {}).get("rotate")
    if tag is not None:
        try:
            rot = int(tag)
        except ValueError:
            rot = 0
    # 2) 新しい side_data の rotation（負の値で来ることが多い: -90 = 縦撮り）
    for sd in s.get("side_data_list") or []:
        if "rotation" in sd:
            try:
                rot = int(sd["rotation"])
            except (TypeError, ValueError):
                pass

    swap = abs(rot) % 180 == 90
    dw, dh = (h, w) if swap else (w, h)
    return {
        "width": w, "height": h, "rotation": rot,
        "display_width": dw, "display_height": dh,
        "is_vertical": dh > dw,
    }

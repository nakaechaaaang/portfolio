"""音声抽出。元動画は触らず、作業フォルダに 16kHz mono WAV を作る。"""
from __future__ import annotations

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

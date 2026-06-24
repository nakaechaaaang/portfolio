"""テロップの焼き込み（ffmpeg subtitles フィルタ）。"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .config import PRESETS


def burn(
    video: str | Path, srt: str | Path, out: str | Path,
    *, style: str | None = None, preset: str = "default",
) -> Path:
    """video に srt のテロップを焼き込んで out に書き出す。元動画は変更しない。

    style を直接渡せばそれを使い、なければ preset の burn_style を使う。
    subtitles フィルタはパスのエスケープが厄介なので、SRT のあるフォルダを
    作業ディレクトリにして、ファイル名だけを渡す（日本語・空白パス対策）。
    """
    video, srt, out = Path(video), Path(srt), Path(out)
    if style is None:
        style = PRESETS.get(preset, PRESETS["default"])["burn_style"]
    out.parent.mkdir(parents=True, exist_ok=True)

    cwd = srt.parent
    vf = f"subtitles={srt.name}:force_style='{style}'"
    cmd = [
        "ffmpeg", "-y", "-i", str(video.resolve()),
        "-vf", vf, "-c:a", "copy", str(out.resolve()),
    ]
    subprocess.run(cmd, check=True, cwd=str(cwd))
    return out

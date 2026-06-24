"""WhisperX による文字起こし＋強制アライメント。

ここが「ズレない」核心。
1. faster-whisper で文字起こし（initial_prompt で固有名詞をヒント）
2. wav2vec2 で強制アライメント → 各単語を実音の位置にピン留め（<100ms）

返り値は素の WhisperX セグメント。items 化は build.py が行う。
"""
from __future__ import annotations

from pathlib import Path


def transcribe(
    wav_path: str | Path,
    *,
    model: str = "large-v3",
    language: str = "ja",
    initial_prompt: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    batch_size: int = 16,
) -> dict:
    # 重い依存はここで import（CLI のヘルプ表示などを軽くするため）
    import whisperx  # type: ignore

    if device is None:
        try:
            import torch  # type: ignore
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    asr_options = {"initial_prompt": initial_prompt} if initial_prompt else None

    # 1) 文字起こし
    asr_model = whisperx.load_model(
        model, device, compute_type=compute_type,
        language=language, asr_options=asr_options,
    )
    audio = whisperx.load_audio(str(wav_path))
    result = asr_model.transcribe(audio, batch_size=batch_size, language=language)

    # 2) 強制アライメント（単語タイムスタンプの精度を上げる）
    align_model, metadata = whisperx.load_align_model(
        language_code=language, device=device
    )
    aligned = whisperx.align(
        result["segments"], align_model, metadata, audio, device,
        return_char_alignments=False,
    )
    aligned["language"] = language
    return aligned

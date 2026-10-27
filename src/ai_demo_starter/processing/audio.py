from __future__ import annotations

from pathlib import Path

import numpy as np

from ..core.errors import InvalidInputError


def load_audio(
    source: str | Path | tuple[int, np.ndarray],
    *,
    max_seconds: float = 300,
    max_bytes: int = 25_000_000,
    allowed_formats: tuple[str, ...] = ("wav", "flac"),
) -> tuple[int, np.ndarray, float]:
    try:
        if isinstance(source, tuple):
            sr, audio = source
        else:
            if Path(source).stat().st_size > max_bytes:
                raise InvalidInputError("Audio exceeds upload size limit")
            import soundfile as sf

            info = sf.info(str(source))
            if info.format.lower() not in allowed_formats:
                raise InvalidInputError("Unsupported audio format; use WAV or FLAC")
            if info.duration > max_seconds:
                raise InvalidInputError("Audio exceeds duration limit")
            if info.channels > 8 or info.frames * info.channels > 32_000_000:
                raise InvalidInputError("Decoded audio exceeds channel or sample limit")
            if not 0 < info.samplerate <= 384_000:
                raise InvalidInputError("Invalid sample rate")
            audio, sr = sf.read(str(source), dtype="float32", always_2d=False)
        raw = np.asarray(audio)
        if raw.size > 32_000_000 or (raw.ndim == 2 and raw.shape[1] > 8):
            raise InvalidInputError("Decoded audio exceeds channel or sample limit")
        if sr <= 0 or sr > 384_000:
            raise InvalidInputError("Invalid sample rate")
        arr = raw.astype(np.float32)
        if np.issubdtype(raw.dtype, np.integer):
            limits = np.iinfo(raw.dtype)
            if limits.min == 0:
                midpoint = (limits.max + 1) / 2
                arr = (arr - midpoint) / midpoint
            else:
                arr = arr / float(max(abs(limits.min), limits.max))
            arr = arr.astype(np.float32)
        if arr.ndim == 2:
            arr = arr.mean(axis=1)
        if arr.ndim != 1 or arr.size == 0 or not np.isfinite(arr).all():
            raise InvalidInputError("Decoded audio is invalid")
        duration = arr.size / float(sr)
        if duration > max_seconds:
            raise InvalidInputError("Audio exceeds duration limit")
        return int(sr), np.clip(arr, -1, 1), duration
    except InvalidInputError:
        raise
    except Exception as exc:
        raise InvalidInputError(f"Invalid audio: {exc}") from exc


def resample_audio(audio: np.ndarray, sample_rate: int, target_rate: int = 16000) -> np.ndarray:
    """Polyphase resampling preserves duration and suppresses aliasing."""
    if sample_rate == target_rate:
        return audio
    from math import gcd

    from scipy.signal import resample_poly

    divisor = gcd(sample_rate, target_rate)
    return np.asarray(
        resample_poly(audio, target_rate // divisor, sample_rate // divisor), dtype=np.float32
    )

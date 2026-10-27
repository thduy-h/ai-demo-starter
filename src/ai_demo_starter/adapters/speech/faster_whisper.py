from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from ...core.errors import ModelNotFoundError, UnsupportedBackendError
from ...core.protocols import SpeechRecognitionAdapter
from ...core.schemas import AdapterState, Diagnostics, ModelMetadata, SpeechResult, SpeechSegment
from ...processing.audio import load_audio, resample_audio


class FasterWhisperAdapter(SpeechRecognitionAdapter):
    def __init__(
        self,
        identifier: str = "tiny",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
        beam_size: int = 5,
        allow_download: bool = False,
        max_audio_seconds: float = 300,
        max_upload_mb: int = 25,
        cache_dir: Path | None = None,
        revision: str | None = None,
        cpu_threads: int = 2,
        allowed_formats: tuple[str, ...] = ("wav", "flac"),
        **_: object,
    ):
        (
            self.identifier,
            self.device,
            self.compute_type,
            self.language,
            self.beam_size,
            self.allow_download,
        ) = identifier, device, compute_type, language, beam_size, allow_download
        self.max_audio_seconds = max_audio_seconds
        self.max_upload_mb = max_upload_mb
        self.cache_dir = cache_dir or Path("~/.cache/ai-demo-starter").expanduser()
        self.revision = revision
        self.cpu_threads = cpu_threads
        self.allowed_formats = allowed_formats
        self.model: Any = None
        self._state: AdapterState = "unloaded"

    def metadata(self) -> ModelMetadata:
        local = self.identifier.startswith((".", "/", "~"))
        return ModelMetadata(
            identifier=self.identifier,
            family="Whisper",
            task="speech",
            backend="faster-whisper",
            device=self.device,
            revision=self.revision,
            source_uri=None
            if local
            else f"https://huggingface.co/Systran/faster-whisper-{self.identifier}",
            license=None if local else "MIT (Systran model card)",
            load_state=self._state,
            output_capabilities=["transcription", "segments"],
        )

    def _model_path(self) -> Path:
        if Path(self.identifier).is_dir():
            return Path(self.identifier).resolve()
        if self.identifier not in {"tiny", "tiny.en", "base", "base.en", "small", "small.en"}:
            raise UnsupportedBackendError(
                "Choose tiny, base, small (optionally .en), or a local directory"
            )
        pointer = self.cache_dir / f"speech-{self.identifier}.json"
        if pointer.is_file():
            manifest = json.loads(pointer.read_text())
            selected = Path(manifest["snapshot"]).resolve()
            if not selected.is_relative_to((self.cache_dir / "hub").resolve()):
                raise ModelNotFoundError("ASR cache manifest points outside the configured cache")
            if selected.is_dir() and (
                self.revision is None or self.revision == manifest["revision"]
            ):
                self.revision = manifest["revision"]
                return selected
        if not self.allow_download:
            raise ModelNotFoundError(
                f"Missing Whisper {self.identifier} weights in {self.cache_dir}. Run "
                "`aidemo models prepare --config configs/speech.yaml` "
                "(network and model terms apply)."
            )
        from huggingface_hub import snapshot_download

        selected = Path(
            snapshot_download(
                repo_id=f"Systran/faster-whisper-{self.identifier}",
                revision=self.revision,
                cache_dir=str(self.cache_dir / "hub"),
                allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.*"],
            )
        ).resolve()
        self.revision = selected.name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", dir=self.cache_dir, delete=False) as handle:
            json.dump({"snapshot": str(selected), "revision": self.revision}, handle)
            temporary = Path(handle.name)
        os.replace(temporary, pointer)
        return selected

    def load(self) -> None:
        if self.device != "cpu":
            raise UnsupportedBackendError("v0.1 supports CPU execution; configure model.device=cpu")
        try:
            from faster_whisper import WhisperModel

            self.model = WhisperModel(
                str(self._model_path()),
                device="cpu",
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                local_files_only=True,
            )
            self._state = "loaded"
        except (ModelNotFoundError, UnsupportedBackendError):
            raise
        except ImportError as exc:
            raise UnsupportedBackendError(
                "Install the speech extra; see README installation instructions "
                "(from a source checkout: python -m pip install -e '.[speech]')"
            ) from exc

    def preprocess(self, inputs: Any) -> tuple[int, np.ndarray, float]:
        sr, audio, duration = load_audio(
            inputs,
            max_seconds=self.max_audio_seconds,
            max_bytes=self.max_upload_mb * 1024 * 1024,
            allowed_formats=self.allowed_formats,
        )
        return 16000, resample_audio(audio, sr), duration

    def predict(self, inputs: tuple[int, np.ndarray, float]) -> Any:
        sr, audio, duration = inputs
        segments, info = self.model.transcribe(
            audio, language=self.language, beam_size=self.beam_size
        )
        # Generator consumption is part of inference timing.
        segs = list(segments)
        return duration, info, segs

    def postprocess(self, outputs: Any) -> SpeechResult:
        duration, info, segs = outputs
        items = [
            SpeechSegment(
                text=s.text.strip(), start=getattr(s, "start", None), end=getattr(s, "end", None)
            )
            for s in segs
        ]
        return SpeechResult(
            text=" ".join(s.text for s in items).strip(),
            duration_s=float(duration),
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
            segments=items,
            diagnostics=Diagnostics(),
            model=self.metadata(),
        )

    def close(self) -> None:
        self.model = None
        self._state = "unloaded"

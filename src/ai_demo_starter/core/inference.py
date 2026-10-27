from __future__ import annotations

import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Generic

from .errors import AIDemoError, InferenceError
from .lifecycle import LifecycleManager
from .protocols import InputT, ModelAdapter, OutputT, PreparedT, ResultT
from .schemas import DetectionResult, Diagnostics, SpeechResult


class InferenceRunner(Generic[InputT, PreparedT, OutputT, ResultT]):
    """Serialize CPU requests and retain at most 16 downloadable image artifacts."""

    def __init__(
        self,
        adapter: ModelAdapter[InputT, PreparedT, OutputT, ResultT],
        *,
        validator: Callable[[InputT], InputT] | None = None,
        save_artifacts: bool = False,
    ):
        self.adapter = adapter
        self.lifecycle = LifecycleManager(adapter)
        self.validator = validator
        self.save_artifacts = save_artifacts
        self._lock = threading.RLock()
        self._artifacts: list[Path] = []
        self._temporary: tempfile.TemporaryDirectory | None = None

    def run(self, request: InputT) -> tuple[ResultT, dict[str, float]]:
        # Queue wait is excluded; total includes validation, loading and all stages.
        with self._lock:
            total = time.perf_counter()
            try:
                if self.validator:
                    request = self.validator(request)
                load_ms = self.lifecycle.ensure_loaded()
                t = time.perf_counter()
                prepared = self.adapter.preprocess(request)
                pre_ms = (time.perf_counter() - t) * 1000
                t = time.perf_counter()
                output = self.adapter.predict(prepared)
                inf_ms = (time.perf_counter() - t) * 1000
                t = time.perf_counter()
                result = self.adapter.postprocess(output)
                if (
                    isinstance(result, DetectionResult)
                    and result.annotated_png
                    and self.save_artifacts
                ):
                    if self._temporary is None:
                        self._temporary = tempfile.TemporaryDirectory(prefix="aidemo-")
                    path = Path(self._temporary.name) / f"annotated-{uuid.uuid4().hex}.png"
                    path.write_bytes(result.annotated_png)
                    self._artifacts.append(path)
                    result.annotated_image = str(path)
                    while len(self._artifacts) > 16:
                        self._artifacts.pop(0).unlink(missing_ok=True)
                post_ms = (time.perf_counter() - t) * 1000
                timing = {
                    "model_load_ms": load_ms,
                    "preprocess_ms": pre_ms,
                    "inference_ms": inf_ms,
                    "postprocess_ms": post_ms,
                    "total_ms": (time.perf_counter() - total) * 1000,
                }
                if isinstance(result, (DetectionResult, SpeechResult)):
                    result.diagnostics = Diagnostics(**timing)
                return result, timing
            except AIDemoError:
                raise
            except Exception as exc:
                raise InferenceError(
                    "Inference failed; inspect the local traceback for details"
                ) from exc

    def close(self) -> None:
        with self._lock:
            try:
                self.lifecycle.close()
            finally:
                if self._temporary:
                    self._temporary.cleanup()
                    self._temporary = None
                self._artifacts.clear()

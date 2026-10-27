from __future__ import annotations

import threading
from enum import StrEnum

from .errors import AIDemoError, ModelLoadError
from .protocols import ModelAdapter


class LoadState(StrEnum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"


class LifecycleManager:
    """Thread-safe lazy loader for one adapter instance."""

    def __init__(self, adapter: ModelAdapter):
        self.adapter = adapter
        self.state = LoadState.UNLOADED
        self.error: Exception | None = None
        self._lock = threading.Lock()

    def ensure_loaded(self) -> float:
        import time

        if self.state is LoadState.LOADED:
            return 0.0
        with self._lock:
            if self.state is LoadState.LOADED:
                return 0.0
            self.state = LoadState.LOADING
            self.adapter._state = "loading"
            start = time.perf_counter()
            try:
                self.adapter.load()
                self.state = LoadState.LOADED
                self.adapter._state = "loaded"
                return (time.perf_counter() - start) * 1000
            except Exception as exc:
                self.state = LoadState.FAILED
                self.adapter._state = "failed"
                self.error = exc
                if isinstance(exc, AIDemoError):
                    raise
                raise ModelLoadError(
                    f"Could not load model {self.adapter.metadata().identifier}: {exc}"
                ) from exc

    def close(self) -> None:
        with self._lock:
            self.adapter.close()
            self.state = LoadState.UNLOADED
            self.adapter._state = "unloaded"
            self.error = None

from types import SimpleNamespace

import numpy as np
import pytest

from ai_demo_starter.adapters.speech.faster_whisper import FasterWhisperAdapter
from ai_demo_starter.core.errors import ModelNotFoundError, UnsupportedBackendError
from ai_demo_starter.core.inference import InferenceRunner
from ai_demo_starter.core.lifecycle import LifecycleManager, LoadState
from ai_demo_starter.core.registry import get_adapter, register_adapter


def test_registry_does_not_mask_factory_keyerror():
    def broken(**kwargs):
        raise KeyError("backend failure")

    register_adapter("broken-test", broken)
    with pytest.raises(KeyError, match="backend failure"):
        get_adapter("broken-test")
    with pytest.raises(UnsupportedBackendError):
        get_adapter("nonexistent")


def test_failed_load_state_and_cause():
    adapter = FasterWhisperAdapter()

    def missing():
        raise ModelNotFoundError("prepare this model")

    adapter.load = missing
    manager = LifecycleManager(adapter)
    with pytest.raises(ModelNotFoundError):
        manager.ensure_loaded()
    assert manager.state is LoadState.FAILED
    assert adapter.metadata().load_state == "failed"
    manager.close()
    assert manager.state is LoadState.UNLOADED


def test_lazy_asr_consumption_is_timed(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("time.perf_counter", lambda: clock[0])

    def transcribe(*args, **kwargs):
        def segments():
            clock[0] += 0.25
            yield SimpleNamespace(text="real generator computation", start=0.0, end=1.0)

        return segments(), SimpleNamespace(language="en", language_probability=0.9)

    adapter = FasterWhisperAdapter()
    adapter.load = lambda: None
    adapter.model = SimpleNamespace(transcribe=transcribe)
    result, timing = InferenceRunner(adapter).run((16000, np.zeros(16000)))
    assert timing["inference_ms"] == 250
    assert result.text == "real generator computation"
    assert result.diagnostics.inference_ms == 250

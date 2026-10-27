"""Offline acquisition-policy tests; real checkpoints are tested separately."""

import hashlib
import sys
from types import SimpleNamespace

import pytest

from ai_demo_starter.adapters.weights import load_torchvision_state
from ai_demo_starter.core.errors import ModelLoadError, ModelNotFoundError


def test_missing_weight_never_downloads(monkeypatch, tmp_path):
    def unexpected(*args, **kwargs):
        pytest.fail("Ordinary inference attempted a download")

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            hub=SimpleNamespace(
                download_url_to_file=unexpected,
            )
        ),
    )
    with pytest.raises(ModelNotFoundError, match="models prepare"):
        load_torchvision_state(
            "https://download.pytorch.org/models/test.pth", "0" * 64, tmp_path, False, "detection"
        )


def test_cached_weight_checksum_and_safe_loading(monkeypatch, tmp_path):
    content = b"test bytes, never a deserialized checkpoint"
    checksum = hashlib.sha256(content).hexdigest()
    path = tmp_path / "checkpoints/test.pth"
    path.parent.mkdir()
    path.write_bytes(content)
    calls = []

    def safe_load(source, **kwargs):
        calls.append((source, kwargs))
        return {"verified": True}

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(load=safe_load))
    result = load_torchvision_state(
        "https://download.pytorch.org/models/test.pth", checksum, tmp_path, False, "detection"
    )
    assert result == {"verified": True}
    assert calls == [(path, {"map_location": "cpu", "weights_only": True})]
    path.write_bytes(b"corruption")
    with pytest.raises(ModelLoadError, match="checksum"):
        load_torchvision_state(
            "https://download.pytorch.org/models/test.pth", checksum, tmp_path, False, "detection"
        )
    assert len(calls) == 1


def test_reject_unselected_model_host(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    with pytest.raises(ModelLoadError, match="official"):
        load_torchvision_state(
            "https://example.org/test.pth", "0" * 64, tmp_path, True, "detection"
        )

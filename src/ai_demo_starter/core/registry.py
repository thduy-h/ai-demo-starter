from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .errors import UnsupportedBackendError
from .protocols import ModelAdapter

if TYPE_CHECKING:
    from ..config.schemas import AppConfig

_REGISTRY: dict[str, Callable[..., ModelAdapter]] = {}


def register_adapter(name: str, factory: Callable[..., ModelAdapter]) -> None:
    _REGISTRY[name] = factory


def get_adapter(name: str, **kwargs: object) -> ModelAdapter:
    try:
        factory = _REGISTRY[name]
    except KeyError as exc:
        raise UnsupportedBackendError(
            f"Unknown adapter '{name}'. Available: {', '.join(sorted(_REGISTRY))}"
        ) from exc
    return factory(**kwargs)


def available_adapters() -> list[str]:
    return sorted(_REGISTRY)


def register_defaults() -> None:
    from ..adapters import (
        FasterWhisperAdapter,
        TorchVisionDetectionAdapter,
        TorchVisionEmbeddingAdapter,
    )

    _REGISTRY.setdefault("torchvision_ssdlite", TorchVisionDetectionAdapter)
    _REGISTRY.setdefault("torchvision_embedding", TorchVisionEmbeddingAdapter)
    _REGISTRY.setdefault("faster_whisper", FasterWhisperAdapter)


def create_adapter(config: AppConfig) -> ModelAdapter:
    register_defaults()
    adapter = get_adapter(
        config.model.adapter,
        identifier=config.model.identifier,
        device=config.model.device,
        allow_download=config.downloads.allow_download,
        cache_dir=config.downloads.cache_dir,
        confidence_threshold=config.inference.confidence_threshold,
        compute_type=config.model.compute_type,
        language=config.model.language,
        beam_size=config.model.beam_size,
        revision=config.model.revision,
        cpu_threads=config.model.cpu_threads,
        allowed_formats=tuple(config.input.allowed_formats),
        max_audio_seconds=config.inference.max_audio_seconds,
        max_upload_mb=config.input.max_upload_mb,
        max_pixels=config.input.max_pixels,
    )
    if adapter.metadata().task != config.demo.type:
        raise UnsupportedBackendError("Registered adapter task does not match the configuration")
    return adapter

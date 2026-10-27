from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
from PIL import Image

from .schemas import AdapterState, DetectionRequest, DetectionResult, ModelMetadata, SpeechResult

InputT = TypeVar("InputT")
PreparedT = TypeVar("PreparedT")
OutputT = TypeVar("OutputT")
ResultT = TypeVar("ResultT")


class ModelAdapter(ABC, Generic[InputT, PreparedT, OutputT, ResultT]):
    """Lifecycle and prediction contract implemented by trusted adapters."""

    _state: AdapterState = "unloaded"

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def preprocess(self, inputs: InputT) -> PreparedT: ...

    @abstractmethod
    def predict(self, inputs: PreparedT) -> OutputT: ...

    @abstractmethod
    def postprocess(self, outputs: OutputT) -> ResultT: ...

    @abstractmethod
    def metadata(self) -> ModelMetadata: ...

    def close(self) -> None:
        return None


ImageInput = str | Path | bytes | Image.Image
AudioInput = str | Path | tuple[int, np.ndarray]


class DetectionAdapter(ModelAdapter[ImageInput | DetectionRequest, Any, Any, DetectionResult]):
    pass


class SpeechRecognitionAdapter(ModelAdapter[AudioInput, Any, Any, SpeechResult]):
    pass


class ImageEmbeddingAdapter(ModelAdapter[ImageInput, Any, Any, np.ndarray]):
    pass

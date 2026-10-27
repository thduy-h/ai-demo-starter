"""Trusted embedding adapter extension; the stock CLI and UI remain unchanged."""

from typing import Any

import numpy as np

from ai_demo_starter.adapters.retrieval.torchvision import TorchVisionEmbeddingAdapter
from ai_demo_starter.cli import app
from ai_demo_starter.core.protocols import ImageEmbeddingAdapter
from ai_demo_starter.core.registry import register_adapter
from ai_demo_starter.processing.embeddings import normalize_embedding


class PrefixEmbeddingAdapter(ImageEmbeddingAdapter):
    """A runnable extension example, not a claim that truncation improves retrieval."""

    def __init__(self, **kwargs: Any):
        self.delegate = TorchVisionEmbeddingAdapter(**kwargs)

    def load(self) -> None:
        self.delegate.load()

    def preprocess(self, inputs: Any) -> Any:
        return self.delegate.preprocess(inputs)

    def predict(self, inputs: Any) -> np.ndarray:
        return self.delegate.predict(inputs)[:128]

    def postprocess(self, outputs: np.ndarray) -> np.ndarray:
        return normalize_embedding(outputs)

    def metadata(self):
        metadata = self.delegate.metadata()
        metadata.identifier += ":prefix128"
        metadata.input_requirements = {
            **metadata.input_requirements,
            "feature_layer": "first 128 avgpool channels; L2 normalized",
        }
        metadata.load_state = self._state
        return metadata

    def close(self) -> None:
        self.delegate.close()


register_adapter("mobilenet_prefix", PrefixEmbeddingAdapter)

if __name__ == "__main__":
    app()

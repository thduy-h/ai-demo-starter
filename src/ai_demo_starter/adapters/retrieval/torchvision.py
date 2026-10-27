from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ...core.errors import ModelNotFoundError, UnsupportedBackendError
from ...core.protocols import ImageEmbeddingAdapter
from ...core.schemas import AdapterState, ModelMetadata
from ...processing.images import load_image
from ..weights import load_torchvision_state


class TorchVisionEmbeddingAdapter(ImageEmbeddingAdapter):
    def __init__(
        self,
        identifier: str = "mobilenet_v3_small",
        device: str = "cpu",
        allow_download: bool = False,
        max_upload_mb: int = 10,
        max_pixels: int = 20_000_000,
        cache_dir: Path | None = None,
        cpu_threads: int = 2,
        allowed_formats: tuple[str, ...] = ("jpeg", "png", "webp"),
        **_: object,
    ):
        self.identifier, self.device, self.allow_download = identifier, device, allow_download
        self.max_upload_mb, self.max_pixels = max_upload_mb, max_pixels
        self.cache_dir = cache_dir
        self.cpu_threads = cpu_threads
        self.allowed_formats = allowed_formats
        self.model: Any = None
        self.weights: Any = None
        self._state: AdapterState = "unloaded"

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            identifier=self.identifier,
            family="MobileNetV3 image features",
            task="retrieval",
            backend="torchvision",
            device=self.device,
            revision="MobileNet_V3_Small_Weights.IMAGENET1K_V1",
            source_uri="https://download.pytorch.org/models/mobilenet_v3_small-047dcff4.pth",
            license=None,
            load_state=self._state,
            input_requirements={
                "feature_layer": "features -> avgpool -> flatten (576 dimensions)",
                "preprocessing": "RGB; bilinear resize 256; center crop 224; "
                "scale [0,1]; mean [0.485,0.456,0.406]; std [0.229,0.224,0.225]",
                "normalization": "l2 float32",
                "index_schema_version": 1,
            },
            output_capabilities=["normalized_embedding"],
        )

    def load(self) -> None:
        if self.device != "cpu":
            raise UnsupportedBackendError("v0.1 supports CPU execution; configure model.device=cpu")
        try:
            import torch
            from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

            torch.set_num_threads(self.cpu_threads)

            if self.identifier != "mobilenet_v3_small":
                raise UnsupportedBackendError(
                    f"Unsupported retrieval identifier: {self.identifier}"
                )
            self.weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
            state = load_torchvision_state(
                self.weights.url,
                "047dcff4addef86ea5bc2eff13c9614dc11f47ab1160d0a71a25e7db994f4e1f",
                self.cache_dir,
                self.allow_download,
                "retrieval",
            )
            net = mobilenet_v3_small(weights=None)
            net.load_state_dict(state)
            net = net.to(self.device).eval()
            self.model = torch.nn.Sequential(net.features, net.avgpool, torch.nn.Flatten()).eval()
            self._state = "loaded"
        except ModelNotFoundError:
            raise
        except ImportError as exc:
            raise UnsupportedBackendError(
                "Install the retrieval extra: uv sync --extra retrieval"
            ) from exc

    def preprocess(self, inputs: Any) -> Any:
        image = load_image(
            inputs,
            max_bytes=self.max_upload_mb * 1024 * 1024,
            max_pixels=self.max_pixels,
            allowed_formats=self.allowed_formats,
        )
        return self.weights.transforms()(image)

    def predict(self, inputs: Any) -> np.ndarray:
        import torch

        with torch.inference_mode():
            arr = self.model(inputs.unsqueeze(0)).squeeze(0).cpu().numpy()
        norm = np.linalg.norm(arr)
        if norm == 0:
            raise ValueError("Model returned zero embedding")
        return (arr / norm).astype(np.float32)

    def postprocess(self, outputs: Any) -> np.ndarray:
        return outputs

    def close(self) -> None:
        self.model = None
        self._state = "unloaded"

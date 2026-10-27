from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ...core.errors import ModelNotFoundError, UnsupportedBackendError
from ...core.protocols import DetectionAdapter
from ...core.schemas import (
    AdapterState,
    BoundingBox,
    DetectionRequest,
    DetectionResult,
    Diagnostics,
    ModelMetadata,
)
from ...processing.images import annotate, load_image
from ..weights import load_torchvision_state


class TorchVisionDetectionAdapter(DetectionAdapter):
    def __init__(
        self,
        identifier: str = "ssdlite320_mobilenet_v3_large",
        device: str = "cpu",
        confidence_threshold: float = 0.5,
        allow_download: bool = False,
        cache_dir: Path | None = None,
        cpu_threads: int = 2,
        allowed_formats: tuple[str, ...] = ("jpeg", "png"),
        max_upload_mb: int = 10,
        max_pixels: int = 20_000_000,
        **_: object,
    ):
        self.identifier, self.device, self.threshold, self.allow_download, self.cache_dir = (
            identifier,
            device,
            confidence_threshold,
            allow_download,
            cache_dir,
        )
        self.max_upload_mb, self.max_pixels = max_upload_mb, max_pixels
        self.cpu_threads = cpu_threads
        self.allowed_formats = allowed_formats
        self.model: Any = None
        self.weights: Any = None
        self._state: AdapterState = "unloaded"

    @property
    def weight_revision(self) -> str:
        return "SSDLite320_MobileNet_V3_Large_Weights.COCO_V1"

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            identifier=self.identifier,
            family="SSDLite MobileNetV3 Large",
            task="detection",
            backend="torchvision",
            device=self.device,
            revision=self.weight_revision,
            source_uri=(
                "https://download.pytorch.org/models/"
                "ssdlite320_mobilenet_v3_large_coco-a79551df.pth"
            ),
            license=None,
            input_requirements={
                "preprocessing": "RGB [0,1] via COCO_V1 transforms; "
                "model performs resize and normalization internally",
                "coordinate_convention": "xyxy original-image pixels",
            },
            load_state=self._state,
            output_capabilities=["boxes", "labels", "scores", "annotated_image"],
        )

    def load(self) -> None:
        if self.device != "cpu":
            raise UnsupportedBackendError("v0.1 supports CPU execution; configure model.device=cpu")
        try:
            import torch
            from torchvision.models.detection import (
                SSDLite320_MobileNet_V3_Large_Weights,
                ssdlite320_mobilenet_v3_large,
            )

            torch.set_num_threads(self.cpu_threads)

            if self.identifier != "ssdlite320_mobilenet_v3_large":
                raise UnsupportedBackendError(
                    f"Unsupported detection identifier: {self.identifier}"
                )
            self.weights = SSDLite320_MobileNet_V3_Large_Weights.COCO_V1
            state = load_torchvision_state(
                self.weights.url,
                "a79551df90c79834bcd3bb3845ef9d966b5449a3a9b2833ae8404778ca5d65d2",
                self.cache_dir,
                self.allow_download,
                "detection",
            )
            self.model = ssdlite320_mobilenet_v3_large(
                weights=None,
                weights_backbone=None,
                num_classes=len(self.weights.meta["categories"]),
            )
            self.model.load_state_dict(state)
            self.model = self.model.to(self.device).eval()
            self._state = "loaded"
        except ModelNotFoundError:
            raise
        except ImportError as exc:
            raise UnsupportedBackendError(
                "Install the detection extra: uv sync --extra detection"
            ) from exc

    def preprocess(self, inputs: Any) -> tuple[Image.Image, Any, float]:
        threshold = self.threshold
        if isinstance(inputs, DetectionRequest):
            threshold, inputs = inputs.confidence_threshold, inputs.image
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            from ...core.errors import InvalidInputError

            raise InvalidInputError("Confidence threshold must be between 0 and 1")
        image = load_image(
            inputs,
            max_bytes=self.max_upload_mb * 1024 * 1024,
            max_pixels=self.max_pixels,
            allowed_formats=self.allowed_formats,
        )
        tensor = self.weights.transforms()(image) if self.weights is not None else None
        if tensor is None:
            raise RuntimeError("Adapter is not loaded")
        return image, tensor, threshold

    def predict(self, inputs: tuple[Image.Image, Any, float]) -> Any:
        import torch

        image, tensor, threshold = inputs
        with torch.inference_mode():
            return image, self.model([tensor])[0], threshold

    def postprocess(self, outputs: Any) -> DetectionResult:
        image, raw, threshold = outputs
        boxes = raw["boxes"].detach().cpu().numpy()
        labels = raw["labels"].detach().cpu().numpy()
        scores = raw["scores"].detach().cpu().numpy()
        names = self.weights.meta.get("categories", []) if self.weights else []
        dets: list[BoundingBox] = []
        draw = []
        for box, cls, score in zip(boxes, labels, scores, strict=False):
            if (
                not np.isfinite(box).all()
                or not np.isfinite(score)
                or not 0 <= float(score) <= 1
                or float(score) < threshold
            ):
                continue
            x1, y1, x2, y2 = [float(max(0, min(v, image.size[i % 2]))) for i, v in enumerate(box)]
            if x2 <= x1 or y2 <= y1 or int(cls) < 0:
                continue
            label = names[int(cls)] if int(cls) < len(names) else str(int(cls))
            dets.append(
                BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    class_id=int(cls),
                    label=label,
                    confidence=float(score),
                )
            )
            draw.append((x1, y1, x2, y2, label, float(score)))
        buf = io.BytesIO()
        annotate(image, draw).save(buf, format="PNG")
        return DetectionResult(
            width=image.width,
            height=image.height,
            detections=dets,
            annotated_png=buf.getvalue(),
            diagnostics=Diagnostics(),
            model=self.metadata(),
        )

    def close(self) -> None:
        self.model = None
        self._state = "unloaded"

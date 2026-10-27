from __future__ import annotations

import hashlib
import io
import time
from pathlib import Path
from typing import Any

from PIL import Image

from ..config.schemas import AppConfig
from ..processing.audio import load_audio
from ..processing.images import load_image
from ..retrieval.index import GalleryIndex
from .errors import GalleryIndexError
from .inference import InferenceRunner
from .registry import create_adapter
from .schemas import DetectionRequest, Diagnostics, RetrievalResult


class DemoService:
    """Task results and file artifacts for UI/CLI clients; no Gradio dependency."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.adapter = create_adapter(config)
        self.runner = InferenceRunner(self.adapter, save_artifacts=config.output.save_artifacts)

    def detection(self, source: Any, threshold: float):
        start = time.perf_counter()
        image = load_image(
            source,
            max_bytes=self.config.input.max_upload_mb * 1024 * 1024,
            max_pixels=self.config.input.max_pixels,
            allowed_formats=tuple(self.config.input.allowed_formats),
        )
        validation_ms = (time.perf_counter() - start) * 1000
        result, timing = self.runner.run(DetectionRequest(image, threshold))
        timing["preprocess_ms"] += validation_ms
        timing["total_ms"] += validation_ms
        result.diagnostics = Diagnostics(**timing)
        preview = (
            Image.open(io.BytesIO(result.annotated_png)).copy() if result.annotated_png else image
        )
        return preview, result.annotated_image, result.model_dump(mode="json")

    def speech(self, source: Any):
        start = time.perf_counter()
        rate, audio, _ = load_audio(
            source,
            max_seconds=self.config.inference.max_audio_seconds,
            max_bytes=self.config.input.max_upload_mb * 1024 * 1024,
            allowed_formats=tuple(self.config.input.allowed_formats),
        )
        validation_ms = (time.perf_counter() - start) * 1000
        result, timing = self.runner.run((rate, audio))
        timing["preprocess_ms"] += validation_ms
        timing["total_ms"] += validation_ms
        result.diagnostics = Diagnostics(**timing)
        return result.text, result.model_dump(mode="json")

    def retrieval(self, source: Any, top_k: int, gallery_path: str | None = None):
        start = time.perf_counter()
        image = load_image(
            source,
            max_bytes=self.config.input.max_upload_mb * 1024 * 1024,
            max_pixels=self.config.input.max_pixels,
            allowed_formats=tuple(self.config.input.allowed_formats),
        )
        selected = self.config.gallery_dir if not gallery_path else Path(gallery_path)
        if selected.resolve().parent != self.config.gallery_dir.resolve().parent:
            raise GalleryIndexError("Select a gallery from the configured gallery directory")
        index = GalleryIndex.load(selected)
        index.assert_compatible(self.adapter)
        vector, timing = self.runner.run(image)
        post = time.perf_counter()
        matches = index.search(vector, int(top_k))
        # Decode only validated gallery images, avoiding unrestricted static file routes.
        previews = [
            (
                load_image(index.image_path(m.source), max_pixels=self.config.input.max_pixels),
                f"{m.rank}. {m.source} — cosine {m.similarity:.4f}",
            )
            for m in matches
        ]
        timing["postprocess_ms"] += (time.perf_counter() - post) * 1000
        timing["total_ms"] = (time.perf_counter() - start) * 1000
        result = RetrievalResult(
            query_id=hashlib.sha256(image.tobytes()).hexdigest(),
            matches=matches,
            embedding_fingerprint=index.fingerprint,
            index_version=index.VERSION,
            diagnostics=Diagnostics(**timing),
            model=self.adapter.metadata(),
        )
        return previews, result.model_dump(mode="json")

    def close(self) -> None:
        self.runner.close()

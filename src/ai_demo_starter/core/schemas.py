from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

AdapterState = Literal["unloaded", "loading", "loaded", "failed"]


class Diagnostics(BaseModel):
    model_load_ms: float | None = None
    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0


class ModelMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    identifier: str
    family: str
    task: str
    backend: str
    device: str = "cpu"
    revision: str | None = None
    source_uri: str | None = None
    license: str | None = None
    load_state: AdapterState = "unloaded"
    input_requirements: dict[str, Any] = Field(default_factory=dict)
    output_capabilities: list[str] = Field(default_factory=list)


class BoundingBox(BaseModel):
    x1: float = Field(ge=0, allow_inf_nan=False)
    y1: float = Field(ge=0, allow_inf_nan=False)
    x2: float = Field(ge=0, allow_inf_nan=False)
    y2: float = Field(ge=0, allow_inf_nan=False)
    coordinate_convention: str = "xyxy_pixels"
    class_id: int
    label: str
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)


class DetectionResult(BaseModel):
    width: int
    height: int
    detections: list[BoundingBox]
    annotated_image: str | None = None
    annotated_png: bytes | None = Field(default=None, exclude=True)
    diagnostics: Diagnostics
    model: ModelMetadata


@dataclass(frozen=True)
class DetectionRequest:
    image: str | Path | bytes | Image.Image
    confidence_threshold: float


class SpeechSegment(BaseModel):
    text: str
    start: float | None = None
    end: float | None = None


class SpeechResult(BaseModel):
    text: str
    duration_s: float
    language: str | None = None
    language_probability: float | None = None
    segments: list[SpeechSegment] = Field(default_factory=list)
    diagnostics: Diagnostics
    model: ModelMetadata


class RetrievalMatch(BaseModel):
    item_id: str
    source: str
    similarity: float
    rank: int


class RetrievalResult(BaseModel):
    query_id: str
    matches: list[RetrievalMatch]
    embedding_fingerprint: str
    index_version: int
    diagnostics: Diagnostics
    model: ModelMetadata

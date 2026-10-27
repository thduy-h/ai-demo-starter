from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DemoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["detection", "speech", "retrieval"]
    title: str = "AI Demo"


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adapter: str
    identifier: str
    backend: str = "pytorch"
    device: str = "cpu"
    cpu_threads: int = Field(default=2, ge=1, le=32)
    revision: str | None = None
    language: str | None = None
    compute_type: str = "int8"
    beam_size: int = Field(default=5, ge=1, le=20)


class DownloadsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_download: bool = False
    cache_dir: Path = Path("~/.cache/ai-demo-starter")


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confidence_threshold: float = Field(default=0.5, ge=0, le=1)
    max_concurrency: int = Field(default=1, ge=1, le=16)
    max_audio_seconds: float = Field(default=300, gt=0, allow_inf_nan=False)


class InputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_upload_mb: int = Field(default=10, ge=1, le=1024)
    max_pixels: int = Field(default=20_000_000, ge=1)
    allowed_formats: list[str] = Field(default_factory=lambda: ["jpeg", "png"], min_length=1)


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    save_artifacts: bool = True


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = "127.0.0.1"
    port: int = Field(default=7860, ge=1, le=65535)
    share: bool = False


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    demo: DemoConfig
    model: ModelConfig
    downloads: DownloadsConfig = Field(default_factory=DownloadsConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    input: InputConfig = Field(default_factory=InputConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    gallery_dir: Path = Path(".local/galleries/example")
    config_path: Path | None = None

    @model_validator(mode="after")
    def validate_task_adapter(self) -> AppConfig:
        expected = {
            "detection": "torchvision_ssdlite",
            "speech": "faster_whisper",
            "retrieval": "torchvision_embedding",
        }
        if self.model.adapter != expected[self.demo.type]:
            # Custom names must be explicitly registered by trusted application code.
            from ..core.registry import available_adapters

            if (
                self.model.adapter in expected.values()
                or self.model.adapter not in available_adapters()
            ):
                raise ValueError(
                    f"adapter '{self.model.adapter}' is not compatible with demo '{self.demo.type}'"
                )
        backends = {
            "torchvision_ssdlite": "pytorch",
            "torchvision_embedding": "pytorch",
            "faster_whisper": "faster-whisper",
        }
        if self.model.adapter in backends and self.model.backend != backends[self.model.adapter]:
            raise ValueError("Backend does not match the selected adapter")
        if self.model.device != "cpu":
            raise ValueError("v0.1 supports model.device=cpu only")
        versions = {
            "torchvision_ssdlite": "SSDLite320_MobileNet_V3_Large_Weights.COCO_V1",
            "torchvision_embedding": "MobileNet_V3_Small_Weights.IMAGENET1K_V1",
        }
        if self.model.adapter in versions and self.model.revision not in {
            None,
            versions[self.model.adapter],
        }:
            raise ValueError("Unsupported pretrained weight revision")
        identifiers = {
            "torchvision_ssdlite": "ssdlite320_mobilenet_v3_large",
            "torchvision_embedding": "mobilenet_v3_small",
        }
        if (
            self.model.adapter in identifiers
            and self.model.identifier != identifiers[self.model.adapter]
        ):
            raise ValueError("Unsupported model identifier for the selected adapter")
        if self.demo.type == "speech" and "allowed_formats" not in self.input.model_fields_set:
            self.input.allowed_formats = ["wav", "flac"]
        formats = {
            "detection": {"jpeg", "png"},
            "speech": {"wav", "flac"},
            "retrieval": {"jpeg", "png", "webp"},
        }
        if not set(self.input.allowed_formats) <= formats[self.demo.type]:
            raise ValueError("Input formats do not match the task's decoded format allowlist")
        return self

    def resolved(self, base: Path | None = None) -> AppConfig:
        base = base or (self.config_path.parent if self.config_path else Path.cwd())
        self.downloads.cache_dir = self.downloads.cache_dir.expanduser()
        if not self.downloads.cache_dir.is_absolute():
            self.downloads.cache_dir = (base / self.downloads.cache_dir).resolve()
        if not self.gallery_dir.is_absolute():
            self.gallery_dir = (base / self.gallery_dir).resolve()
        if self.model.identifier.startswith((".", "/", "~")):
            model_path = Path(self.model.identifier).expanduser()
            self.model.identifier = str((base / model_path).resolve())
        return self

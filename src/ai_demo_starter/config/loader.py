import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from ..core.errors import ConfigurationError
from .schemas import AppConfig


def load_config(path: str | Path) -> AppConfig:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise ConfigurationError(f"Configuration file not found: {p}")
    try:
        if p.stat().st_size > 1024 * 1024:
            raise ConfigurationError("Configuration exceeds 1 MiB limit")
        data = yaml.safe_load(p.read_text()) or {}
        if not isinstance(data, dict):
            raise ValueError("Expected a YAML mapping")
        if os.getenv("AIDEMO_DEVICE"):
            data.setdefault("model", {})["device"] = os.environ["AIDEMO_DEVICE"]
        if os.getenv("AIDEMO_ALLOW_DOWNLOAD"):
            data.setdefault("downloads", {})["allow_download"] = os.environ["AIDEMO_ALLOW_DOWNLOAD"]
        if os.getenv("AIDEMO_CACHE_DIR"):
            data.setdefault("downloads", {})["cache_dir"] = os.environ["AIDEMO_CACHE_DIR"]
        for key in ("host", "port"):
            if os.getenv(f"AIDEMO_{key.upper()}"):
                data.setdefault("server", {})[key] = os.environ[f"AIDEMO_{key.upper()}"]
        config = AppConfig.model_validate(data)
        config.config_path = p
        return config.resolved(p.parent)
    except (yaml.YAMLError, ValidationError, ValueError, OSError, TypeError) as exc:
        raise ConfigurationError(f"Invalid configuration {p}: {exc}") from exc


def default_config(demo: str) -> AppConfig:
    """Read installed templates, keeping mutable working data in the caller's cwd."""
    from importlib.resources import as_file, files

    if demo not in {"detection", "speech", "retrieval"}:
        raise ConfigurationError("Choose detection, speech or retrieval")
    template = files("ai_demo_starter").joinpath("configs", f"{demo}.yaml")
    with as_file(template) as path:
        config = load_config(path)
    config.gallery_dir = Path.cwd() / ".local/galleries/example"
    return config

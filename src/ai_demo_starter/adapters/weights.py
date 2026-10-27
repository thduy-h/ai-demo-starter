"""Acquire only selected upstream TorchVision checkpoints and verify cached bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..core.errors import ModelLoadError, ModelNotFoundError


def load_torchvision_state(
    url: str, checksum: str, cache_dir: Path | None, allow_download: bool, task: str
) -> Any:
    import torch

    cache = (cache_dir or Path(torch.hub.get_dir())) / "checkpoints"
    path = cache / Path(urlparse(url).path).name
    if not path.is_file():
        if not allow_download:
            raise ModelNotFoundError(
                f"Missing {task} weights at {path}. Run `aidemo models prepare "
                f"--config configs/{task}.yaml` (network and model terms apply)."
            )
        if urlparse(url).netloc != "download.pytorch.org":
            raise ModelLoadError("Only selected official PyTorch weight sources are supported")
        cache.mkdir(parents=True, exist_ok=True)
        torch.hub.download_url_to_file(url, str(path), hash_prefix=checksum, progress=False)
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != checksum:
        raise ModelLoadError(f"Weight checksum mismatch for {path.name}; remove and prepare again")
    return torch.load(path, map_location="cpu", weights_only=True)

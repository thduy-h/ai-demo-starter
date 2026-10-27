import pytest

from ai_demo_starter.config.loader import load_config
from ai_demo_starter.core.errors import ConfigurationError


@pytest.mark.parametrize(
    "replacement",
    [
        "schema_version: 2",
        "server: {port: 99999}",
        "model: {adapter: torchvision_ssdlite, identifier: x, device: cuda}",
        "model: {adapter: torchvision_ssdlite, identifier: x, backend: onnx}",
    ],
)
def test_invalid_configuration(tmp_path, replacement):
    data = "demo: {type: detection}\nmodel: {adapter: torchvision_ssdlite, identifier: x}\n"
    key = replacement.split(":")[0]
    data = "\n".join(line for line in data.splitlines() if not line.startswith(key + ":"))
    path = tmp_path / "invalid.yaml"
    path.write_text(data + "\n" + replacement)
    with pytest.raises(ConfigurationError):
        load_config(path)


def test_environment_overrides_are_revalidated(monkeypatch):
    monkeypatch.setenv("AIDEMO_DEVICE", "cuda")
    with pytest.raises(ConfigurationError, match="cpu"):
        load_config("configs/detection.yaml")


def test_relative_paths(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "demo: {type: retrieval}\nmodel: {adapter: torchvision_embedding, "
        "identifier: mobilenet_v3_small}\ndownloads: {cache_dir: cache}\n"
        "gallery_dir: gallery"
    )
    config = load_config(path)
    assert config.downloads.cache_dir == tmp_path / "cache"
    assert config.gallery_dir == tmp_path / "gallery"

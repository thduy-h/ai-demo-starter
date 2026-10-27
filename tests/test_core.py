import numpy as np
import pytest

from ai_demo_starter.config.loader import load_config
from ai_demo_starter.core.errors import ConfigurationError, InvalidInputError
from ai_demo_starter.processing.embeddings import cosine_similarity, normalize_embedding


def test_config_loads():
    c = load_config("configs/detection.yaml")
    assert c.demo.type == "detection" and c.server.host == "127.0.0.1"


def test_config_rejects_unknown(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        "schema_version: 1\ndemo: {type: detection}\n"
        "model: {adapter: bad, identifier: x}\nunknown: true"
    )
    with pytest.raises(ConfigurationError):
        load_config(p)


def test_cosine_reference_and_ties():
    q = np.array([1.0, 0.0])
    g = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    np.testing.assert_allclose(cosine_similarity(q, g), [1, 0, -1])


def test_embedding_validation():
    with pytest.raises(InvalidInputError):
        normalize_embedding(np.zeros(3))
    with pytest.raises(InvalidInputError):
        cosine_similarity(np.ones(2), np.ones((2, 3)))

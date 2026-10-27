import runpy
from pathlib import Path

import numpy as np
import pytest

from ai_demo_starter.config.loader import load_config
from ai_demo_starter.core.inference import InferenceRunner
from ai_demo_starter.core.registry import create_adapter


def test_custom_registration_and_config():
    runpy.run_path("examples/custom_adapter/app.py")
    config = load_config("examples/custom_adapter/config.yaml")
    adapter = create_adapter(config)
    assert adapter.metadata().identifier.endswith(":prefix128")
    assert adapter.metadata().task == "retrieval"


@pytest.mark.real_model
def test_custom_real_embeddings():
    runpy.run_path("examples/custom_adapter/app.py")
    config = load_config("examples/custom_adapter/config.yaml")
    config.downloads.cache_dir = Path(".local/models").resolve()
    runner = InferenceRunner(create_adapter(config))
    try:
        vector, _ = runner.run("tests/fixtures/astronaut.png")
        assert vector.shape == (128,)
        np.testing.assert_allclose(np.linalg.norm(vector), 1, atol=1e-5)
    finally:
        runner.close()

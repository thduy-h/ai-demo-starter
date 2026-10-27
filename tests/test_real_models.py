"""Explicit opt-in integration tests: real weights, no automatic acquisition."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from ai_demo_starter.config.loader import load_config
from ai_demo_starter.core.inference import InferenceRunner
from ai_demo_starter.core.registry import create_adapter
from ai_demo_starter.core.schemas import DetectionRequest, Diagnostics
from ai_demo_starter.retrieval.index import GalleryIndex, build_gallery

pytestmark = pytest.mark.real_model
FIXTURES = Path(__file__).parent / "fixtures"


def config_for(task):
    config = load_config(f"configs/{task}.yaml")
    # Explicitly prepared test cache; ordinary runs still use their configured cache.
    config.downloads.cache_dir = Path(".local/models").resolve()
    config.downloads.allow_download = False
    return config


def record(name, data):
    output = Path(".local/verification")
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{name}.json").write_text(json.dumps(data, indent=2))


def test_real_detection(tmp_path):
    runner = InferenceRunner(create_adapter(config_for("detection")), save_artifacts=True)
    try:
        low, timing = runner.run(DetectionRequest(FIXTURES / "astronaut.png", 0.2))
        high, _ = runner.run(DetectionRequest(FIXTURES / "astronaut.png", 0.99))
        assert len(low.detections) >= len(high.detections)
        assert low.detections, "Permitted astronaut photo should produce at least one detection"
        assert (low.width, low.height) == (512, 512)
        for detection in low.detections:
            assert 0 <= detection.x1 <= detection.x2 <= low.width
            assert 0 <= detection.y1 <= detection.y2 <= low.height
            assert 0.2 <= detection.confidence <= 1
            assert detection.label
        artifact = Path(low.annotated_image)
        assert Image.open(artifact).size == (512, 512)
        assert timing["inference_ms"] > 0
        low.diagnostics = Diagnostics(**timing)
        record("detection", low.model_dump(mode="json"))
    finally:
        runner.close()
    assert not artifact.exists()


def test_real_speech_wav_and_flac(tmp_path):
    import soundfile as sf

    from ai_demo_starter.processing.audio import resample_audio

    runner = InferenceRunner(create_adapter(config_for("speech")))
    try:
        wav_result, timing = runner.run(FIXTURES / "jfk.wav")
        samples, rate = sf.read(FIXTURES / "jfk.wav", dtype="float32")
        # Exercise non-16kHz input and FLAC; text need not match byte-for-byte.
        flac = tmp_path / "jfk-24k.flac"
        sf.write(flac, resample_audio(samples, rate, 24000), 24000)
        flac_result, _ = runner.run(flac)
        assert wav_result.text.strip() and flac_result.text.strip()
        assert "country" in wav_result.text.lower()
        assert abs(wav_result.duration_s - len(samples) / rate) < 0.001
        assert abs(flac_result.duration_s - wav_result.duration_s) < 0.001
        assert wav_result.segments
        assert timing["inference_ms"] > 0
        wav_result.diagnostics = Diagnostics(**timing)
        record(
            "speech",
            {
                "wav": wav_result.model_dump(mode="json"),
                "flac": flac_result.model_dump(mode="json"),
            },
        )
    finally:
        runner.close()


def test_real_retrieval(tmp_path):
    source = tmp_path / "gallery"
    source.mkdir()
    original = Image.open(FIXTURES / "astronaut.png").convert("RGB")
    original.save(source / "astronaut.png")
    Image.new("RGB", (512, 512), "blue").save(source / "blue.png")
    config = config_for("retrieval")
    index = build_gallery(source, tmp_path / "index", create_adapter(config))
    loaded = GalleryIndex.load(index.root)
    runner = InferenceRunner(create_adapter(config))
    try:
        loaded.assert_compatible(runner.adapter)
        query, timing = runner.run(original)
        assert query.shape == (576,)
        assert np.isfinite(query).all()
        np.testing.assert_allclose(np.linalg.norm(query), 1.0, atol=1e-5)
        matches = loaded.search(query, 5)
        assert matches[0].source == "astronaut.png"
        assert abs(matches[0].similarity - 1) < 1e-5
        assert matches[0].similarity >= matches[1].similarity
        record(
            "retrieval",
            {
                "matches": [m.model_dump() for m in matches],
                "fingerprint": loaded.fingerprint,
                "timing": timing,
                "model": runner.adapter.metadata().model_dump(),
            },
        )
    finally:
        runner.close()

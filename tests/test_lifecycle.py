from ai_demo_starter.core.inference import InferenceRunner
from ai_demo_starter.core.lifecycle import LifecycleManager, LoadState
from ai_demo_starter.core.protocols import ModelAdapter
from ai_demo_starter.core.schemas import ModelMetadata


class FakeAdapter(ModelAdapter):
    def __init__(self):
        self.loads = 0

    def load(self):
        self.loads += 1

    def preprocess(self, inputs):
        return inputs + 1

    def predict(self, inputs):
        return inputs * 2

    def postprocess(self, outputs):
        return outputs - 1

    def metadata(self):
        return ModelMetadata(identifier="fake", family="test", task="test", backend="test")


def test_lifecycle_loads_once():
    adapter = FakeAdapter()
    manager = LifecycleManager(adapter)
    assert manager.state is LoadState.UNLOADED
    manager.ensure_loaded()
    manager.ensure_loaded()
    assert adapter.loads == 1
    assert manager.state is LoadState.LOADED


def test_runner_reports_stage_timings():
    adapter = FakeAdapter()
    result, timing = InferenceRunner(adapter).run(2)
    assert result == 5
    assert timing["total_ms"] >= timing["inference_ms"]
    assert set(timing) == {
        "model_load_ms",
        "preprocess_ms",
        "inference_ms",
        "postprocess_ms",
        "total_ms",
    }


def test_artifact_bound_and_cleanup():
    import io
    from pathlib import Path

    from PIL import Image

    from ai_demo_starter.core.schemas import DetectionResult, Diagnostics

    class AnnotatingAdapter(FakeAdapter):
        def postprocess(self, outputs):
            buffer = io.BytesIO()
            Image.new("RGB", (8, 8)).save(buffer, format="PNG")
            return DetectionResult(
                width=8,
                height=8,
                detections=[],
                annotated_png=buffer.getvalue(),
                diagnostics=Diagnostics(),
                model=self.metadata(),
            )

    runner = InferenceRunner(AnnotatingAdapter(), save_artifacts=True)
    paths = []
    try:
        for _ in range(20):
            result, _ = runner.run(1)
            paths.append(Path(result.annotated_image))
        assert not any(path.exists() for path in paths[:4])
        assert all(path.exists() for path in paths[4:])
        assert len(list(paths[-1].parent.iterdir())) == 16
    finally:
        runner.close()
    assert not paths[-1].parent.exists()

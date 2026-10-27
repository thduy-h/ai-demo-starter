import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from ai_demo_starter.cli import app

runner = CliRunner()


def test_cli_discovery_and_version():
    for arguments in (["--help"], ["--version"], ["list"]):
        result = runner.invoke(app, arguments)
        assert result.exit_code == 0, result.output
    assert "0.1.0" in runner.invoke(app, ["--version"]).output
    assert "speech" in runner.invoke(app, ["list"]).output


def test_metadata_has_no_weight_loading():
    result = runner.invoke(app, ["model-info", "--config", "configs/detection.yaml"])
    assert result.exit_code == 0, result.output
    assert "unloaded" in result.output
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from ai_demo_starter.config.loader import load_config
from ai_demo_starter.core.registry import create_adapter
adapter = create_adapter(load_config('configs/detection.yaml'))
assert adapter.metadata().load_state == 'unloaded'
assert 'torch' not in sys.modules
""",
        ],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr


def test_packaged_default_configs():
    from ai_demo_starter.config.loader import default_config

    for task in ("detection", "speech", "retrieval"):
        assert default_config(task).demo.type == task
        assert (Path("configs") / f"{task}.yaml").read_bytes() == (
            Path("src/ai_demo_starter/configs") / f"{task}.yaml"
        ).read_bytes()


def test_cli_config_errors():
    result = runner.invoke(app, ["validate-config", "does-not-exist.yaml"])
    assert result.exit_code == 2
    assert "not found" in result.output


def test_cli_all_configs():
    for task in ("detection", "speech", "retrieval"):
        result = runner.invoke(app, ["validate-config", f"configs/{task}.yaml"])
        assert result.exit_code == 0, result.output

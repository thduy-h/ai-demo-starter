"""Install the wheel with pip in a clean venv and check CLI/resources outside the source tree."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheel = next((root / "dist").glob("*.whl"))
with tempfile.TemporaryDirectory(prefix="aidemo-wheel-") as temporary:
    directory = Path(temporary)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [sys.executable, "-m", "venv", str(directory / "venv")],
        env=environment,
        check=True,
    )
    python = directory / "venv/bin/python"
    subprocess.run(
        [str(python), "-m", "pip", "install", str(wheel)],
        cwd=directory,
        env=environment,
        check=True,
    )
    code = """
from pathlib import Path
import ai_demo_starter
from importlib.resources import files
from importlib.util import find_spec
from ai_demo_starter.config.loader import default_config
assert '/site-packages/' in ai_demo_starter.__file__
assert all(find_spec(name) is None for name in ('torch', 'gradio', 'faster_whisper'))
for task in ('detection', 'speech', 'retrieval'):
    resource = files('ai_demo_starter').joinpath('configs', task + '.yaml')
    assert resource.is_file()
    assert default_config(task).demo.type == task
print('Installed wheel imports and all packaged templates: passed')
"""
    subprocess.run([str(python), "-c", code], cwd=directory, env=environment, check=True)
    for arguments in (["--help"], ["--version"], ["list"]):
        subprocess.run(
            [str(directory / "venv/bin/aidemo"), *arguments],
            cwd=directory,
            env=environment,
            check=True,
        )
    output = root / ".local/verification"
    output.mkdir(parents=True, exist_ok=True)
    (output / "wheel.json").write_text(
        json.dumps(
            {
                "wheel": wheel.name,
                "installer": "python -m pip install",
                "cwd_outside_repository": True,
                "imports_and_templates": "passed",
                "optional_backends_absent": True,
                "cli_help_version_list": "passed",
            },
            indent=2,
        )
    )

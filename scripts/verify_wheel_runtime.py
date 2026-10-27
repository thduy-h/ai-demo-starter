"""Install locked runtime dependencies and the wheel, then infer outside the source tree."""

import os
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
environment = os.environ.copy()
environment.pop("PYTHONPATH", None)
with tempfile.TemporaryDirectory(prefix="aidemo-wheel-runtime-") as temporary:
    directory = Path(temporary)
    requirements = directory / "requirements.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--extra",
            "all",
            "--no-dev",
            "--no-emit-project",
            "--emit-index-url",
            "--output-file",
            str(requirements),
        ],
        cwd=root,
        env=environment,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(["uv", "venv", "--python", "3.11", str(directory / "venv")], check=True)
    python = directory / "venv/bin/python"
    subprocess.run(
        [
            "uv",
            "pip",
            "sync",
            "--python",
            str(python),
            "--index-strategy",
            "unsafe-best-match",
            "--require-hashes",
            str(requirements),
        ],
        cwd=directory,
        env=environment,
        check=True,
    )
    wheel = next((root / "dist").glob("*.whl"))
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)],
        cwd=directory,
        env=environment,
        check=True,
    )
    code = """
import json
import os
from pathlib import Path
import ai_demo_starter
from ai_demo_starter.config.loader import default_config
from ai_demo_starter.core.registry import create_adapter
from ai_demo_starter.core.service import DemoService
from ai_demo_starter.retrieval.index import build_gallery
from ai_demo_starter.ui.factory import build_app

assert '/site-packages/' in ai_demo_starter.__file__
fixtures = Path(os.environ['AIDEMO_TEST_FIXTURES'])
evidence = {}
for task in ('detection', 'speech', 'retrieval'):
    config = default_config(task)
    if task == 'retrieval':
        gallery = Path('source')
        gallery.mkdir()
        (gallery / 'astronaut.png').write_bytes((fixtures / 'astronaut.png').read_bytes())
        config.gallery_dir = Path('index').resolve()
        build_gallery(gallery, config.gallery_dir, create_adapter(config))
    service = DemoService(config)
    try:
        if task == 'detection':
            preview, download, result = service.detection(fixtures / 'astronaut.png', 0.5)
            assert preview.size == (512, 512) and Path(download).is_file()
            assert result['detections']
        elif task == 'speech':
            transcript, result = service.speech(fixtures / 'jfk.wav')
            assert 'country' in transcript.lower()
        else:
            previews, result = service.retrieval(fixtures / 'astronaut.png', 5)
            assert previews and result['matches'][0]['similarity'] > .999
        evidence[task] = {'status': 'passed', 'diagnostics': result['diagnostics']}
        application = build_app(config)
        assert application.enable_queue
        application.close()
    finally:
        service.close()
Path(os.environ['AIDEMO_WHEEL_EVIDENCE']).write_text(json.dumps(evidence, indent=2))
print('Installed wheel: all three real CPU pipelines and UI construction passed')
"""
    subprocess.run(
        [str(python), "-c", code],
        cwd=directory,
        env=environment
        | {
            "AIDEMO_TEST_FIXTURES": str(root / "tests/fixtures"),
            "AIDEMO_CACHE_DIR": str(root / ".local/models"),
            "AIDEMO_WHEEL_EVIDENCE": str(root / ".local/verification/wheel-runtime.json"),
        },
        check=True,
    )

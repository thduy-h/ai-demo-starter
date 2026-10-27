"""Resolve/install each extra in a separate environment and check optional imports."""

import json
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = []
for profile in ("base", "ui", "detection", "speech", "retrieval", "all"):
    destination = root / ".local" / "profiles" / profile
    environment = os.environ | {"UV_PROJECT_ENVIRONMENT": str(destination)}
    environment.pop("VIRTUAL_ENV", None)
    command = ["uv", "sync", "--locked", "--no-dev"]
    if profile != "base":
        command += ["--extra", profile]
    subprocess.run(command, cwd=root, env=environment, check=True)
    modules = {
        "base": [],
        "ui": ["gradio"],
        "detection": ["torch", "torchvision", "gradio"],
        "speech": ["faster_whisper", "ctranslate2", "soundfile", "scipy", "gradio"],
        "retrieval": ["torch", "torchvision", "gradio"],
        "all": ["torch", "torchvision", "faster_whisper", "gradio"],
    }[profile]
    checks = "import importlib.util; import ai_demo_starter"
    checks += "".join(f"; __import__({name!r})" for name in modules)
    if profile in {"base", "ui", "speech"}:
        checks += "; assert importlib.util.find_spec('torch') is None"
    if profile == "base":
        checks += "; assert importlib.util.find_spec('gradio') is None"
    subprocess.run([str(destination / "bin/python"), "-c", checks], check=True)
    records.append({"profile": profile, "result": "passed", "modules": modules})
output = root / ".local/verification"
output.mkdir(parents=True, exist_ok=True)
(output / "profiles.json").write_text(json.dumps(records, indent=2))
print(json.dumps(records, indent=2))

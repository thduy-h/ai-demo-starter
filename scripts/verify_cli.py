"""Exercise documented commands and each default-config server over loopback HTTP."""

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root / ".local/verification"
output.mkdir(parents=True, exist_ok=True)
environment = os.environ | {"AIDEMO_CACHE_DIR": str(root / ".local/models")}
records = []


def command(*arguments):
    completed = subprocess.run(
        ["uv", "run", "--no-sync", "aidemo", *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    records.append({"arguments": list(arguments), "result": "passed", "output": completed.stdout})


command("--help")
command("--version")
command("list")
for task in ("detection", "speech", "retrieval"):
    command("validate-config", f"configs/{task}.yaml")
    command("model-info", "--config", f"configs/{task}.yaml")
    # Prepared caches are used; no network is needed for this repeat acquisition check.
    command("models", "prepare", "--config", f"configs/{task}.yaml")
command(
    "gallery",
    "build",
    "--config",
    "configs/retrieval.yaml",
    "--input",
    "examples/gallery",
    "--output",
    ".local/galleries/example",
)
command("gallery", "info", "--index", ".local/galleries/example")
# Updating uses the same atomic build path.
command(
    "gallery",
    "build",
    "--config",
    "configs/retrieval.yaml",
    "--input",
    "examples/gallery",
    "--output",
    ".local/galleries/example",
)

launches = [["aidemo", "run", task] for task in ("detection", "speech", "retrieval")]
launches.append(["aidemo", "run", "detection", "--config", "configs/detection.yaml"])
custom = ["python", "examples/custom_adapter/app.py"]
custom_config = ["--config", "examples/custom_adapter/config.yaml"]
for arguments in (
    ["models", "prepare", *custom_config],
    [
        "gallery",
        "build",
        *custom_config,
        "--input",
        "examples/gallery",
        "--output",
        ".local/galleries/custom",
    ],
):
    completed = subprocess.run(
        ["uv", "run", "--no-sync", *custom, *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    records.append(
        {"arguments": custom + arguments, "result": "passed", "output": completed.stdout}
    )
launches.append([*custom, "run", "retrieval", *custom_config])

for launch in launches:
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryFile(mode="w+") as log:
        process = subprocess.Popen(
            ["uv", "run", "--no-sync", *launch],
            cwd=root,
            env=environment | {"AIDEMO_PORT": str(port)},
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 45
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(log.read())
                try:
                    with urllib.request.urlopen(url + "/config", timeout=2) as response:
                        config = json.load(response)
                        assert config["enable_queue"]
                        break
                except (OSError, ValueError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Server did not start: {launch}") from None
                    time.sleep(0.2)
            records.append({"arguments": launch, "result": "passed", "http_status": 200})
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

(output / "cli.json").write_text(json.dumps(records, indent=2))
print(f"Passed {len(records)} CLI and server checks")

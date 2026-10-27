# Deployment

## Native Linux and pip

Use Python 3.11 and an activated venv or Conda environment. Follow the [README](../README.md#install) for source installation with pip, Conda, or uv. Neither the installed library nor the CLI requires uv. Native testing used NixOS with the supplied [shell](nixos.md); ordinary Ubuntu CI is configured but has not run remotely in this session. Keep models in a persistent cache and prepare explicitly before serving. All demos default to localhost:7860 and offline inference.

Build both distributions using `python -m pip install build` followed by `python -m build`, or use `uv build`. Run `python scripts/verify_wheel.py` to test a base wheel installation in a fresh standard-library venv using pip, outside the source tree. Config templates are packaged. A Linux CPU wheel consumer can select an extra after installing the tested framework pair:

```bash
python -m pip install torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install 'dist/ai_demo_starter-0.1.0-py3-none-any.whl[detection]'
```

pip does not read uv's source/index settings. Use the CPU index only for Torch/TorchVision, not for all dependencies. For speech alone, omit the framework installation and select `[speech]`. A wheel installation provides packaged default configs: use `aidemo run detection` without a repository checkout. For editable YAML files, copy templates from the source repository and pass `--config` explicitly.

The uv lockfile records the exact tested dependency graph; pip resolves the supported ranges in package metadata and may choose newer versions. Conda is an environment-manager option: install this project and its model runtimes with pip inside that environment rather than mixing pip Torch with Conda Torch packages. Conda environment creation was not executed in the verification environment because Conda was unavailable.

Use `AIDEMO_CACHE_DIR`, `AIDEMO_HOST`, and `AIDEMO_PORT` for operational overrides. Uploads and model execution stay local. Public exposure needs an external authentication/access/abuse-control layer; do not enable a Gradio sharing link by accident. Model runtimes and decoded images consume considerably more memory than weight file sizes; no RSS or capacity benchmark has been measured. Keep concurrency at one initially.

## Docker and Compose

Status: Dockerfile reviewed and `docker compose config` passed; actual build/run is **unverified** because the Docker daemon socket is unavailable. No service or system configuration was changed to start a daemon.

```bash
docker build -t ai-demo-starter:0.1.0 .
docker compose run --rm aidemo aidemo models prepare --config configs/detection.yaml
docker compose up
```

Compose builds the same image, initializes a persistent named `/cache` volume, and publishes localhost:7860. Image startup does not acquire weights. The image uses Python 3.11 slim-bookworm, uv 0.11.21, frozen dependencies, CPU wheels, uid10001, and an internal 0.0.0.0 listener. Model preparation runs as the same non-root user. Base-image tags are not digest-pinned; validate/pin them for your deployment.

Without Compose:

```bash
docker volume create aidemo-cache
docker run --rm -v aidemo-cache:/cache ai-demo-starter:0.1.0 aidemo models prepare --config configs/detection.yaml
docker run --rm -p 127.0.0.1:7860:7860 -v aidemo-cache:/cache ai-demo-starter:0.1.0
```

Speech: build with `--build-arg DEMO_EXTRA=speech`, then prepare using `configs/speech.yaml` and override the container command to `aidemo run speech --config configs/speech.yaml`. Retrieval similarly uses `DEMO_EXTRA=retrieval`; mount permitted source images and a writable index directory, run `gallery build`, and configure `gallery_dir`. Do not serve or expose the cache directory as static files. Review model terms before redistributing images containing weights.

## Hugging Face Spaces

Documented but not deployed/verified. Choose a Docker Space, use the supplied image recipe, expose port7860, and keep `share=false`. Acquire permitted weights explicitly during your image preparation or administrator setup, retaining the pinned revision/checksums. Persistent cache availability depends on your Space storage tier. Set `AIDEMO_HOST=0.0.0.0`; use the correct demo extra and container command. The original localhost default is for local use, so binding all interfaces is a deliberate hosting choice.

Do not upload private test inputs or cache contents into a public repository. Review public-access abuse controls, storage cleanup, CPU memory, and each model's terms. No paid API, public deployment, or public Gradio share was used in this audit.

# ai-demo-starter 0.1.0

A CPU-first Python library and CLI for running trusted AI models in local Gradio demos. Detection, speech recognition, and image retrieval use real pretrained models. Models load lazily, uploads are validated, and results include stage timings and model metadata. This is a research/demo starter kit, not an enterprise serving platform.

## Install

Python 3.11 is the verified runtime; package metadata permits 3.11+. The included `uv.lock` records the tested resolution. On ordinary Linux:

```bash
uv sync --locked --all-extras
```

On NixOS, enter the supplied environment **before running uv, Python, or the CLI**:

```bash
nix-shell
uv sync --locked --all-extras
```

Native NixOS x86_64 execution was verified with Python 3.11.16, including Torch and CTranslate2 wheels. `shell.nix` supplies their C++ runtime without changing system configuration. Its nixpkgs channel is not pinned; see [NixOS notes](docs/nixos.md).

For a smaller installation, select `--extra detection`, `--extra speech`, or `--extra retrieval` instead. `--extra ui` installs Gradio without model runtimes; the base package has neither Gradio nor Torch. All six installation profiles were checked separately. Linux uv installs use the explicit PyTorch CPU wheel index. See [tested versions](docs/decisions.md).

## Prepare models and run

Preparation is the explicit network step. It downloads approximately 14 MB of detector weights, 10 MB of retrieval weights, or 76 MB of Whisper weights. Review [model provenance and terms](docs/model-licenses.md). We do not redistribute pretrained weights.

```bash
uv run aidemo --help
uv run aidemo --version
uv run aidemo list
uv run aidemo validate-config configs/detection.yaml
uv run aidemo model-info --config configs/detection.yaml

uv run aidemo models prepare --config configs/detection.yaml
uv run aidemo run detection
```

Open the printed localhost URL, upload a JPEG/PNG, and run detection. The UI shows labels, scores, boxes, JSON diagnostics, and an annotated PNG download. The confidence slider filters predictions in original-image pixel coordinates.

Stop that server before starting another demo on the default port 7860:

```bash
uv run aidemo models prepare --config configs/speech.yaml
uv run aidemo run speech
```

Record with the microphone or upload WAV/FLAC. Whisper tiny runs locally on CPU INT8, with automatic language detection and segment timestamps. The inference timer includes consumption of every generated segment. Word timestamps are not implemented.

```bash
uv run aidemo models prepare --config configs/retrieval.yaml
uv run aidemo gallery build --config configs/retrieval.yaml --input examples/gallery --output .local/galleries/example
uv run aidemo gallery info --index .local/galleries/example
uv run aidemo run retrieval
```

Select a gallery, upload a query, and adjust top K. The included shapes are original synthetic examples; use your own permitted images for useful retrieval. Repeat `gallery build` with the same output to update an index. Indexes retain safe references to their source images, so keep that source directory in place.

Ordinary runs have downloads disabled. Missing weights report their expected cache and preparation command. The default cache is `~/.cache/ai-demo-starter`; use `AIDEMO_CACHE_DIR` consistently during preparation and execution to change it. `model-info` reports static metadata without loading weights.

## Configuration and architecture

```bash
uv run aidemo run detection --config configs/detection.yaml
```

An example configuration is:

```yaml
schema_version: 1
demo: {type: detection, title: "Object Detection Demo"}
model:
  adapter: torchvision_ssdlite
  identifier: ssdlite320_mobilenet_v3_large
  backend: pytorch
  device: cpu
  revision: SSDLite320_MobileNet_V3_Large_Weights.COCO_V1
downloads: {allow_download: false, cache_dir: "~/.cache/ai-demo-starter"}
inference: {confidence_threshold: 0.5, max_concurrency: 1}
server: {host: "127.0.0.1", port: 7860, share: false}
```

YAML uses strict Pydantic validation, rejects unknown fields, and resolves relative paths from the configuration file. Operational environment overrides are revalidated. See [configuration](docs/configuration.md).

The CLI creates a task adapter from an explicit registry. `InferenceRunner` manages loading, preprocessing, prediction, postprocessing, timings, and bounded artifacts. `DemoService` translates typed results for the Gradio factory. Adapters and gallery logic have no Gradio dependency. See [architecture](docs/architecture.md).

Trusted application code can register its own adapter before invoking the existing CLI. The [complete custom adapter example](examples/custom_adapter/README.md) extracts and normalizes 128 MobileNet channels and runs the existing retrieval UI unchanged. YAML cannot import arbitrary Python paths. ONNX and person Re-ID are future extensions; generic ImageNet embeddings are not a validated Re-ID model.

## Tests and packaging

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -v
uv build
uv run python scripts/verify_wheel.py
```

The default suite performs no model downloads. Real-model tests and live HTTP upload tests require explicitly prepared weights in `.local/models`:

```bash
export AIDEMO_CACHE_DIR="$PWD/.local/models"
uv run aidemo models prepare --config configs/detection.yaml
uv run aidemo models prepare --config configs/speech.yaml
uv run aidemo models prepare --config configs/retrieval.yaml
uv run pytest --real-models --ui-live -v
```

[Testing documentation](docs/testing.md) includes coverage, installation-profile checks, and limitations. [The release audit](docs/release.md) records actual outcomes. Both distributions build, and a fresh pip environment outside the source tree verifies wheel imports, templates, and CLI commands. For pip users, install a built wheel with the relevant extra; Linux CPU wheel selection is described in [deployment](docs/deployment.md).

Publication materials: [GitHub readiness audit](docs/publication.md), [release checklist](docs/release-checklist.md), and [proposed v0.1.0 release notes](docs/release-notes-0.1.0.md). Container distribution and public production hosting have separate readiness requirements from local CPU use.

## Docker

These commands are provided for deployment; **container build/run could not be verified because no Docker daemon is available**. Compose configuration validation passed.

```bash
docker build -t ai-demo-starter:0.1.0 .
docker compose run --rm aidemo aidemo models prepare --config configs/detection.yaml
docker compose up
```

Compose shares a persistent `/cache` volume between preparation and serving and publishes only `127.0.0.1:7860`. The non-root container binds `0.0.0.0` internally. See [deployment](docs/deployment.md) for speech/retrieval images, native Linux, and Hugging Face Spaces guidance. Spaces deployment is documented but unverified.

## Limits, privacy, and contributing

CPU concurrency defaults to one request per model with a queue of 16. Torch CPU threads default to two and affect the process globally. Native inference cannot be safely interrupted by a hard request timeout. Public exposure needs additional access and abuse controls.

Uploaded media is processed locally and not logged by the toolkit. Gradio retains temporary files for downloads and periodically removes them; runner artifacts are bounded and cleaned at process exit. See [security](docs/security.md) for limits and trust boundaries. No accuracy or performance guarantee is made.

Original project code is [MIT licensed](LICENSE). Model weights, frameworks, datasets, and fixtures have separate terms; TorchVision weight licensing is not assumed to inherit its BSD code license. Contributions are welcome under [CONTRIBUTING.md](CONTRIBUTING.md).

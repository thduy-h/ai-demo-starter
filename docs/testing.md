# Verification

Activate an environment with all demo extras using the [README](../README.md#install). Enter `nix-shell` first on NixOS. Install developer tools with `python -m pip install -e ".[dev]" build`. Alternatively, `uv sync --locked --all-extras` provides the locked maintainer environment; activate `.venv` or prefix commands with `uv run`.

```bash
ruff check .
ruff format --check .
mypy src
python -m pytest -v --cov=ai_demo_starter --cov-report=term-missing --cov-report=json:.local/verification/coverage.json
```

The default suite is offline: configuration, CLI, adapter/lifecycle contracts, generator timing, upload validation, independent NumPy cosine references, ranking ties, gallery round-trip/update, path safety, fingerprints, checksum policy, and artifact bounds/cleanup. It constructs Gradio applications when installed. Optional real-model and loopback HTTP tests are skipped unless selected. Some core contracts use test adapters; these are not presented as real inference.

Explicitly prepare the test cache before real-model tests:

```bash
export AIDEMO_CACHE_DIR="$PWD/.local/models"
aidemo models prepare --config configs/detection.yaml
aidemo models prepare --config configs/speech.yaml
aidemo models prepare --config configs/retrieval.yaml
python -m pytest --real-models --ui-live -v
```

Tests use `.local/models` intentionally and never auto-download weights. Real fixtures are the attributed NASA astronaut photo and JFK speech excerpt. Detection checks thresholds, finite boxes/scores, dimensions, and downloadable PNG cleanup. Speech verifies WAV and resampled 24 kHz FLAC transcripts/durations and measures fully consumed generator inference. Retrieval checks real 576-channel embeddings, persisted/reloaded indexes, exact-image rank1, and finite cosine scores. A real custom 128-channel adapter is tested separately in the same suite.

Live tests launch each application on localhost, upload files with `gradio_client`, verify rendered result payloads/downloads, and check invalid-image errors. These validate HTTP/component bindings, not browser pixel appearance. Microphone components are constructed but physical microphone recording and browser screenshots were not tested.

```bash
uv run python scripts/verify_profiles.py
uv run python scripts/verify_cli.py
python -m build
python scripts/verify_wheel.py
```

The profile and CLI verification scripts use uv as maintainer tooling; uv is not required for the CLI, pytest, or wheel verification. Profile verification creates six isolated environments and checks optional-runtime absence. CLI verification uses already-prepared `.local/models`, repeats prepare/build/update/info commands, and starts all three no-config servers over loopback. Wheel verification creates a clean standard-library venv, installs with pip outside the source tree, and checks imports, config resources, help/version/list. Installation/build commands may need network; standard inference tests do not.

Standard CI installs only dev+UI extras, runs deterministic tests/static checks/build/clean-wheel smoke, and does not download model weights. CI workflow configuration was inspected locally; remote GitHub execution was not performed. Docker build/run and other host platforms are separate checks. See [release audit](release.md) for actual counts, outcomes, and limitations.

`uv run python scripts/verify_wheel_runtime.py` additionally installs the locked full runtime and built wheel in a fresh environment, runs all three real CPU service pipelines, and constructs all three UIs outside the repository. It requires the prepared test cache and does not download models.

## pip installation verification

On 2026-10-27, a fresh Python 3.11.16 standard-library venv on NixOS x86_64 was populated using pip alone: the explicit CPU Torch/TorchVision pair from the README, then `python -m pip install -e ".[all]"` and `python -m pip install -e ".[all,dev]" build`. No uv installation or resolution was used for this environment. `pip check`, Ruff lint/format checks, and `mypy src` passed. `python -m pytest --real-models --ui-live -v` passed all 69 tests with zero skips, including all three real CPU models and Gradio HTTP uploads/downloads; four upstream Gradio deprecation warnings remained. Ten installed `aidemo` CLI commands passed, covering discovery, configuration, metadata, cached model preparation, and gallery build/inspection. `python -m build` produced both distributions. Conda was not installed, so Conda environment creation remains unverified.

`python scripts/verify_wheel.py` also passed using standard-library venv and pip, with imports, packaged templates, and installed CLI checks executed outside the source tree. The clean base installation had no Torch, Gradio, or faster-whisper packages.

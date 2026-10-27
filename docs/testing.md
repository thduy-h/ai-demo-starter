# Verification

Enter `nix-shell` on NixOS, then `uv sync --locked --all-extras`.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -v --cov=ai_demo_starter --cov-report=term-missing --cov-report=json:.local/verification/coverage.json
```

The default suite is offline: configuration, CLI, adapter/lifecycle contracts, generator timing, upload validation, independent NumPy cosine references, ranking ties, gallery round-trip/update, path safety, fingerprints, checksum policy, and artifact bounds/cleanup. It constructs Gradio applications when installed. Optional real-model and loopback HTTP tests are skipped unless selected. Some core contracts use test adapters; these are not presented as real inference.

Explicitly prepare the test cache before real-model tests:

```bash
export AIDEMO_CACHE_DIR="$PWD/.local/models"
uv run aidemo models prepare --config configs/detection.yaml
uv run aidemo models prepare --config configs/speech.yaml
uv run aidemo models prepare --config configs/retrieval.yaml
uv run pytest --real-models --ui-live -v
```

Tests use `.local/models` intentionally and never auto-download weights. Real fixtures are the attributed NASA astronaut photo and JFK speech excerpt. Detection checks thresholds, finite boxes/scores, dimensions, and downloadable PNG cleanup. Speech verifies WAV and resampled 24 kHz FLAC transcripts/durations and measures fully consumed generator inference. Retrieval checks real 576-channel embeddings, persisted/reloaded indexes, exact-image rank1, and finite cosine scores. A real custom 128-channel adapter is tested separately in the same suite.

Live tests launch each application on localhost, upload files with `gradio_client`, verify rendered result payloads/downloads, and check invalid-image errors. These validate HTTP/component bindings, not browser pixel appearance. Microphone components are constructed but physical microphone recording and browser screenshots were not tested.

```bash
uv run python scripts/verify_profiles.py
uv run python scripts/verify_cli.py
uv build
uv run python scripts/verify_wheel.py
```

Profile verification creates six isolated environments and checks optional-runtime absence. CLI verification uses already-prepared `.local/models`, repeats prepare/build/update/info commands, and starts all three no-config servers over loopback. Wheel verification creates a clean pip environment outside the source tree and checks imports, config resources, help/version/list. Installation/build commands may need network; standard inference tests do not.

Standard CI installs only dev+UI extras, runs deterministic tests/static checks/build/clean-wheel smoke, and does not download model weights. CI workflow configuration was inspected locally; remote GitHub execution was not performed. Docker build/run and other host platforms are separate checks. See [release audit](release.md) for actual counts, outcomes, and limitations.

`uv run python scripts/verify_wheel_runtime.py` additionally installs the locked full runtime and built wheel in a fresh environment, runs all three real CPU service pipelines, and constructs all three UIs outside the repository. It requires the prepared test cache and does not download models.

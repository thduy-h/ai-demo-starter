# Contributing

Use Python 3.11 and an isolated environment. On NixOS enter `nix-shell` first. Follow the [README installation instructions](README.md#install) for pip, Conda, or uv, then install developer tools with `python -m pip install -e ".[dev]" build`. Run `ruff check .`, `ruff format --check .`, `mypy src`, and `python -m pytest -v`. Alternatively, `uv sync --locked --all-extras` with uv 0.11.21 reproduces the tested dependency graph. Keep core tests offline and put real weights behind the opt-in flags described in [testing](docs/testing.md).

Preserve task-specific public types, Gradio-independent adapters, explicit model acquisition, and safe input/index handling. Add tests that establish contracts or reproduce real defects. Do not commit weights, cache directories, user uploads, credentials, or generated gallery indexes. The three synthetic example images and attributed small test fixtures are intentional assets.

When changing configuration templates, update both root `configs/` and packaged `src/ai_demo_starter/configs/`; a test checks consistency. When changing an embedding pipeline, change fingerprint metadata and rebuild incompatible indexes. Regenerate uv.lock with actual resolution after dependency changes. Build both distributions and run clean-wheel smoke before submitting.

Report actual passed/skipped/unavailable checks. Do not describe mock results as real inference or assume model weight terms inherit framework licenses. Contributions to original project code use the repository MIT license. Publishing, public deployment, and upstream releases require maintainer authorization.

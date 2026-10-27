# Changelog

## 0.1.0

Initial CPU-first release candidate: typed configuration, lifecycle-managed TorchVision detection and embeddings, local faster-whisper speech recognition, Gradio UIs, atomic gallery persistence, explicit weight acquisition, CLI, adapter extension example, packaging, and deployment guidance.

Stabilization: generated and verified uv lock with CPU wheel sources; fixed Typer options and editable config resources; selected versioned weight enums and immutable Whisper commit; verified Torch checkpoint SHA256 and safe loading; corrected inference timing, integer audio scaling/resampling, upload bounds, gallery compatibility/path checks, and bounded artifact cleanup. Added deterministic tests, real CPU inference/live HTTP checks, clean-wheel verification, and tested native NixOS shell guidance. See [release audit](docs/release.md) for the conditional verdict and unverified deployment items.

Publication preparation: hardened Git/Docker exclusions for credentials, checkpoints, and generated outputs; added a disposable prospective-index audit; replayed CI in a clean dev+UI snapshot; added SPDX package licensing, discovery keywords/classifiers, upstream model-license evidence, a publication checklist, and proposed release notes. Actual Git history remains inaccessible behind the environment mount. No release was published.

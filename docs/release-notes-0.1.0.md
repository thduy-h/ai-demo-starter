# ai-demo-starter v0.1.0 — Local AI demos on CPU

Proposed GitHub release notes. This release has not been published. Use after the Git provenance/staged-file and hosted-CI gates in the [release checklist](release-checklist.md) are satisfied.

## What is included

- Object detection with pretrained TorchVision SSDLite320 MobileNetV3 Large: image validation, configurable confidence threshold, labels/boxes/scores, annotated PNG preview and download.
- Local speech recognition with faster-whisper tiny on CPU INT8: microphone/upload UI, WAV/FLAC decoding, mono conversion/resampling, transcript, language information, and segment timestamps.
- Image similarity search with real MobileNetV3 Small embeddings: gallery build/update/inspection, persisted indexes, cosine ranking, deterministic ties, and incompatible-pipeline rejection.
- Reusable task-specific adapter contracts, lazy lifecycle management, measured inference stages, strict YAML configuration, and explicit trusted adapter registration.
- A complete custom embedding adapter example using the existing retrieval UI.
- A Typer CLI, Gradio interfaces, a uv lockfile with Linux CPU wheel sources, wheel/source packaging, CI, and native NixOS guidance.

## Getting started

From a source checkout with Python 3.11 and uv installed (enter `nix-shell` first on NixOS):

```bash
uv sync --locked --all-extras
uv run aidemo list
uv run aidemo models prepare --config configs/detection.yaml
uv run aidemo run detection
```

Preparation explicitly accesses upstream model sources; ordinary inference is offline by default. See the README for speech, retrieval galleries, and custom configurations.

## Verification and compatibility

Real CPU detection, WAV/FLAC transcription, embedding extraction/index reload/search, and localhost Gradio upload/callback/download checks were executed. Package builds and clean installed-wheel behavior were verified. See [publication audit](publication.md) for the final command results and [previous implementation audit](release.md) for inference outputs and timing boundaries.

Verified runtime: Python 3.11 on Linux x86_64/NixOS with the supplied shell. Python metadata permits 3.11+, but other Python versions/platforms have not received this verification. No GPU or model-accuracy guarantee is made.

## Models and licensing

Original toolkit code is MIT. No pretrained weights are included in Git or distribution archives. Detection uses the explicit COCO_V1 weights; retrieval uses IMAGENET1K_V1; default speech uses an immutable Systran model revision. Torch checkpoint bytes are SHA256 verified and loaded with `weights_only=True`.

Framework licenses, weight terms, dataset/image rights, and fixture terms are separate. TorchVision explicitly places responsibility for determining model-use permission on the user; a separate permissive license for these two weight artifacts was not established. The pinned Systran model card states MIT. Read [model provenance](model-licenses.md) before acquiring or deploying models.

## Known limitations

- Dockerfile/Compose are provided, but container build/run remains unverified without an available Docker daemon. Hugging Face Spaces deployment is also unverified.
- This is a local research/demo toolkit, not a production public serving platform. Public hosting needs additional controls and review.
- Microphone components are implemented; physical recording/browser appearance were not manually tested.
- Only the default tiny speech model was verified. Generic ImageNet embeddings are not a validated person Re-ID model.
- Native inference has no hard interruptible request timeout. Torch thread settings affect the process globally. Gallery indexes reference their source-image directory; moving it requires rebuilding.
- Gradio temporary files and annotation downloads expire. No memory/throughput/accuracy benchmarks are claimed.

## Maintainer publication notes

Suggested title: `v0.1.0 — CPU-first AI demo toolkit`. Keep this draft's limitations when preparing a GitHub release. Wheel/source archives can be built locally with `uv build`; verify their checksums and contents before attaching them. No container image or model-weight redistribution is implied. Pushing, tagging, publishing packages/images, and creating releases require separate authorization.

# v0.1.0 release verification audit

Historical implementation audit; see [publication.md](publication.md) for the later GitHub readiness gate.

Audit date: 2026-10-27. Verdict: **CONDITIONAL GO** for the local CPU release candidate. Core implementation, real inference, CLI/UI, dependency resolution, and wheel installation work. Docker deployment remains unverified, and separate TorchVision weight licensing was not established. Nothing was pushed, published, released, or deployed publicly.

## 1. Executive summary

The previous dependency blockers are resolved. Initial DNS-looking failures were socket restrictions in an execution sandbox. An available Nix shell context provided working DNS/TLS and loopback networking. PyPI returned HTTP200; dependencies and all three real models were acquired explicitly. No system network configuration changed. A genuine uv-generated lock records 89 packages.

The existing layered architecture was preserved: strict config -> explicit adapter registry -> lifecycle/runner -> frontend-independent service -> Gradio factory. Fixes include Typer option registration, editable/installed configuration resources, versioned weight enums, safe/checksummed Torch loading, generator-inclusive ASR timing, audio resampling/PCM handling, bounded artifacts, and deterministic gallery persistence/compatibility checks.

## 2. Implemented features

| Area | Actual behavior |
|---|---|
| Detection | COCO pretrained SSDLite, JPEG/PNG validation, confidence filtering, original-pixel boxes/labels/scores, PNG preview/download |
| Speech | Local Whisper tiny CPU INT8, microphone component and file input, WAV/FLAC validation, mono/resampling, transcription/language/segments |
| Retrieval | Real 576-channel MobileNet features, normalization/cosine ranking, atomic build/update, manifest inspection/reload, stable ties, pipeline mismatch rejection |
| Adapters | Task-specific typed public contracts, explicit trusted registration, custom 128-channel embedding example without changing UI |
| CLI/config | All required commands, strict YAML/environment validation, static metadata, explicit preparation, packaged defaults |
| Diagnostics | Actual load/preprocess/predict/postprocess/total intervals; ASR includes complete generator consumption |
| Deployment | Native NixOS execution verified; Dockerfile/Compose/CI supplied; Docker runtime and Spaces unverified |

## 3. Architecture audit

Adapters have no Gradio dependency. Configuration is frontend-independent. `InferenceRunner` serializes model access, loads lazily once, exposes load states and categorized failures, and owns bounded temporary annotations. The service converts task-specific DTOs for UI components. Gallery storage uses validated JSON and non-pickle NumPy matrices independently of the UI.

Embedding fingerprints include model/revision, feature layer/dimension description, preprocessing, normalization, and schema information. Index compatibility rejects different pipelines. The full model inventory and trust boundaries are in [architecture](architecture.md), [security](security.md), and [configuration](configuration.md).

## 4. Dependencies and models

The verified environment is NixOS 26.05 Linux x86_64, CPython 3.11.16, uv 0.11.21. [Technical decisions](decisions.md) records individual package versions and API references. Main runtime: Gradio 5.50.0, Torch 2.14.1+cpu, TorchVision 0.29.1+cpu, faster-whisper 1.2.1, CTranslate2 4.8.4, NumPy 2.4.6, Pydantic 2.12.3. Hatchling 1.32.4 builds distributions.

| Model | Revision | Weight terms | Verification |
|---|---|---|---|
| SSDLite320 MobileNetV3 Large | `SSDLite320_MobileNet_V3_Large_Weights.COCO_V1` | Separate artifact license unknown; COCO/image rights apply | Real CPU detector and annotation passed |
| MobileNetV3 Small | `MobileNet_V3_Small_Weights.IMAGENET1K_V1` | Separate artifact license unknown; ImageNet terms apply | Real 576-dimensional extraction/index/search passed |
| Systran faster-whisper tiny | `d90ca5fe260221311c53c58e660288d3deb8d356` | MIT per pinned model card; dataset terms separate | Real CPU INT8 WAV/FLAC transcription passed |

Framework licenses do not imply weight licenses. No weights are redistributed. [Model provenance](model-licenses.md) records exact URLs, SHA256 hashes, preprocessing, authors, data provenance, and known unknowns. Fixtures have [attribution](../tests/fixtures/README.md).

## 5. Verification gate

Commands below ran inside `nix-shell`; this session selected `UV_CACHE_DIR=/tmp/uv-cache`. Model commands consistently selected `AIDEMO_CACHE_DIR=$PWD/.local/models`. Script-driven CLI calls use `uv run --no-sync aidemo`; normal documented usage uses `uv run aidemo`. Results refer to actual execution, not planned checks.

| Check | Exact command | Result/evidence | Remaining limitation |
|---|---|---|---|
| PyPI reachability | `curl -s --max-time 10 -I https://pypi.org/simple/` | HTTP/2 200 with TLS verification | Restricted sandbox itself still cannot create sockets |
| Dependency resolution | `uv sync --locked --all-extras` | Passed; 81 installed packages checked | Only tested host/Python verified |
| Profile isolation | `uv run python scripts/verify_profiles.py` | 6/6 passed: base, UI, detection, speech, retrieval, all | Other platforms untested |
| Lockfile | `uv lock --check` | Passed; 89 packages, actual generated `uv.lock` | Pip does not consume uv lock |
| Static lint | `uv run ruff check .` | Passed | None known |
| Formatting | `uv run ruff format --check .` | Passed | None known |
| Types | `uv run mypy src` | Passed;29 source files | Optional backend internals use explicit Any |
| Unit/contracts/integration | `uv run pytest -v --cov=ai_demo_starter --cov-report=term-missing --cov-report=json:.local/verification/coverage.json --junitxml=.local/verification/offline.xml` | 62 passed,7 opt-in skipped,0 failed;75.61% total coverage (76% rounded) | Skipped cases executed separately below |
| All tests, real inference, UI | `uv run pytest --real-models --ui-live -v --junitxml=.local/verification/full.xml` | 69 passed,0 failed,0 skipped;4 upstream Gradio deprecation warnings | Browser pixels/physical microphone untested |
| Real detection | `uv run pytest tests/test_real_models.py --real-models -v` (also full suite) | Real person box, score 0.909866; thresholds/annotation checked | No dataset accuracy evaluation |
| Real speech | Same real-model/full-suite command | Real 11s JFK WAV and 24kHz FLAC transcribed; complete generator timed | Only tiny default model verified |
| Real retrieval | Same real-model/full-suite command | 576 dimensions; saved/reloaded gallery; exact image rank 1 cosine 1.0 | Generic features, no Re-ID claim |
| CLI and launch | `uv run python scripts/verify_cli.py` | 22 command/server checks passed, including all no-config demos and custom CLI | No browser automation |
| Gradio live uploads | `uv run pytest --real-models --ui-live -v --junitxml=.local/verification/full.xml` | 3 live callbacks + 3 construction tests passed; downloads and invalid-image error checked | Physical microphone interaction untested |
| Distribution builds | `uv build` | Wheel and source archive built successfully | No publication performed |
| Pip wheel install | `uv run python scripts/verify_wheel.py` | Fresh seeded venv; actual pip install; imports/templates/help/version/list outside source tree passed | Base pip resolves compatible ranges rather than lock |
| Wheel real runtime | `uv run python scripts/verify_wheel_runtime.py` | Fresh locked runtime +wheel; all 3 real CPU service pipelines and UI construction outside source tree passed | Full HTTP checks used source install |
| Docker build | `docker build -t ai-demo-starter:0.1.0 .` | Failed to connect to Docker API in this environment | No daemon socket; build not verified |
| Docker daemon | `nix-shell --run 'docker version'` | Client 29.8.1 exists; `/var/run/docker.sock` does not exist | Container run not attempted after confirmed blocker |
| Compose schema | `docker compose config` | Passed; localhost publication and cache volume rendered | Does not establish runtime correctness |
| Security | Manual review plus input/gallery/weight/artifact tests in default/full commands | Local-only defaults, validation, safe loading, bounded artifacts reviewed/tested | No hostile-public-service penetration test |
| Documentation | CLI/profile/wheel scripts and command review | Native quick-start commands checked; Docker/Spaces limitations marked | Docker/Spaces commands remain runtime-unverified |
| Git status | `git status --short` | Not available: visible `.git` is an empty read-only mount | Cannot assert clean tree or provenance commit |

Local evidence lives in ignored `.local/verification`: `profiles.json`, `cli.json`, `coverage.json`, `offline.xml`, `full.xml`, `detection.json`, `speech.json`, `retrieval.json`, `wheel.json`, and `wheel-runtime.json`. Timing JSON may refer to already-cleaned temporary artifacts; tests verified their contents and cleanup before removal. It is intentionally not release-bundled user data.

## 6. Real inference evidence

The final full-suite run used prepared local weights with downloads disabled, CPU, and two model threads. These single-run measurements are diagnostics, not performance benchmarks; process/import cache state and concurrent verification work affect them.

| Demo | Permitted input and actual output | Inference / total |
|---|---|---|
| Detection | 512x512 NASA astronaut; class 1 person, confidence 0.909866333; box `[31.7985,9.6872,386.1102,512]`; PNG retained original dimensions | 71.706ms / 331.975ms (load 184.982ms) |
| Speech WAV | 11s JFK excerpt: “And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country.” Language en; backend probability 0.969095 | 1306.008ms / 1592.652ms |
| Speech FLAC |Same speech resampled to 24kHz FLAC; 11s duration and same transcript | 1320.191ms / 1330.042ms |
| Retrieval | 576-channel astronaut query; identical image rank 1 cosine 1.0; blue image rank 2 cosine −0.29551348; reload compatible | 9.955ms / 81.129ms (embedding pipeline only) |

Retrieval fingerprint: `5298bf88a1030a3da88a357fbbb413a42e37d900c0db3e457a35822244602f31`. Similarity/ranking correctness is also checked against an independently implemented NumPy reference, including ties, zero/nonfinite values, mismatched dimensions, and extreme finite values. Detection threshold 0.99 yields fewer detections than 0.2 on the permitted fixture. Synthetic gallery images are not model-quality evidence.

## 7. Packaging and deployment

Wheel: `dist/ai_demo_starter-0.1.0-py3-none-any.whl`. Source archive: `dist/ai_demo_starter-0.1.0.tar.gz`. Both were built with isolated Hatchling. The wheel contains all three default YAML templates and `py.typed`; scripts test that imports resolve from site-packages while running outside the repository. The full-runtime wheel test executes real inference, not just imports.

Native NixOS is verified using `shell.nix`; ordinary Linux CI is configured but remote CI was not triggered. Docker build/run and Spaces deployment are unverified. The Nix shell is channel-based rather than fully system-pinned; Docker base tags are not digest-pinned. See [deployment](deployment.md).

## 8. Security and licensing audit

Validated uploads, finite numerical outputs, image/audio decode limits, safe gallery paths, no pickle index loading, checksum-verified Torch `weights_only` loading, pinned Whisper revision, no model-directory static serving, bounded queue/artifacts, localhost defaults, sharing/analytics/monitoring disabled. No input contents/transcripts are logged by the toolkit. Gradio uses temporary disk caches; cleanup is periodic, not immediate after every request.

Adapters, configuration, local models, and gallery manifests are trusted administrator data/code. No hard native timeout, authentication, multi-tenant isolation, or global disk/memory quota is claimed. MIT applies to original code only; framework, weights, dataset, and asset terms remain separate. No credentials or model weights belong in distribution artifacts. Full details: [security](security.md) and [provenance](model-licenses.md).

## 9. Known issues and classification

- Release blockers for the verified local CPU workflow: none identified by executed checks.
- Deployment verification gap: Docker daemon unavailable; image build/run must be completed before claiming container support is verified. Spaces has not been deployed.
- Licensing limitation: separate permissive TorchVision weight-artifact terms were not established. Review upstream weight/dataset terms for your intended use; no weight redistribution is authorized by the toolkit license.
- Non-blocking upstream issue: four Gradio/Starlette HTTP422 deprecation warnings in live tests.
- Documented limits: physical microphone/browser appearance untested; only Python 3.11/Linux x86_64 and default tiny ASR verified; no accuracy, RSS, throughput, GPU, ONNX, or Re-ID claims.
- Operational limits: process-wide Torch thread count; no hard request interruption; galleries reference local absolute source roots; old matrix generations need administrative cleanup; stale builder locks require checking no build is active before removal; temporary artifacts can expire.
- Repository limitation: empty read-only `.git` mount prevents inspection of actual Git history or worktree state. No source history was replaced or remote operations performed.

## 10. Release verdict

**CONDITIONAL GO.** The previous NO-GO blockers—resolution, lockfile, executed core tests, real inference for all three demos, live CLI/UI, and installed-wheel behavior—are resolved. Conditional status preserves the unverified deployment and licensing limitations above rather than implying all release evidence is complete. This is a usable local CPU release candidate, not authorization to publish or expose it publicly.

## 11. Exact quick start

On NixOS run `nix-shell` first; on other Linux use a compatible Python 3.11 environment:

```bash
uv sync --locked --all-extras
export AIDEMO_CACHE_DIR="$PWD/.local/models"
uv run aidemo models prepare --config configs/detection.yaml
uv run aidemo models prepare --config configs/speech.yaml
uv run aidemo models prepare --config configs/retrieval.yaml
uv run aidemo gallery build --config configs/retrieval.yaml --input examples/gallery --output .local/galleries/example
uv run aidemo run detection
# Stop each server before starting the next on the same port.
uv run aidemo run speech
uv run aidemo run retrieval
uv run pytest -v
uv run pytest --real-models --ui-live -v
uv build
uv run python scripts/verify_wheel.py
```

Docker commands to execute on a daemon-enabled host (not runtime-verified here):

```bash
docker build -t ai-demo-starter:0.1.0 .
docker compose run --rm aidemo aidemo models prepare --config configs/detection.yaml
docker compose up
```

## 12. Recommended next steps

Validate all container workflows on a Docker-enabled host, capture real browser screenshots and microphone interaction, confirm weight terms for intended redistribution/deployment, run the configured GitHub CI after restoring a real repository checkout, and extend platform/Python coverage. Consider pinning nixpkgs and container digests for stronger system reproducibility. Future model backends need their own numerical/real-inference evidence before being advertised.

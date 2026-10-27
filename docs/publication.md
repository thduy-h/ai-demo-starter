# GitHub publication readiness audit — v0.1.0

Audit date: 2026-10-27. **Overall: CONDITIONAL GO.** The implementation is ready as an open-source local CPU toolkit. Actual Git provenance/staged-file inspection and hosted CI remain publication gates. Docker distribution is unverified; public-facing production deployment is not ready and is outside v0.1.0 scope. No push, tag, release, package/image publication, or public deployment was performed.

Publication follow-up: the user subsequently authorized a source push to `git@github.com:thduy-h/ai-demo-starter.git`. Remote inspection confirmed an empty repository. An isolated clone is used for the initial source commit, preserving the inaccessible original metadata. The package project URLs now identify that repository. The audit findings below describe the state before this authorization; no tag, GitHub release, package/image publication, or public service deployment is implied by a source push.

## Publication boundaries

| Target | Verdict | Evidence / remaining gate |
|---|---|---|
| Original MIT source for a local CPU toolkit | Technically ready | All three real models, live UI requests, core tests, builds and clean-wheel checks pass; weights are excluded |
| GitHub publication of this checkout | Conditional | Real `.git` is inaccessible; inspect actual history/staged files on the host and run hosted CI on the reviewed commit |
| Docker image distribution | Not verified | Client exists, but daemon socket is absent; Compose validation does not prove build/runtime behavior |
| Public-facing production service | Not ready / outside scope | No authentication, service-level rate/resource limits, production operations or public-service security validation |

## 1. Git metadata: diagnosis without history destruction

The visible `.git` directory is empty, mode 0555, and a separate **read-only tmpfs mount**, confirmed through `/proc/self/mountinfo`. It is an execution-environment boundary, not evidence that the original project has no Git history. There is no visible HEAD, config, index, ref, object database, or worktree-pointer file to restore. A parent home-directory Git entry is not evidence of this project's history and was not used as its repository.

The mount was not removed/replaced, and no initialization, reset, garbage collection, history rewrite, remote configuration, staging, or commit was performed against the real checkout metadata. Consequently the audit cannot assert a clean/dirty branch state, actual tracked-file list, remote URL, or absence of secrets/artifacts in existing history. **Whether host-side metadata exists must be determined in a normal host terminal. Do not run `git init` over this mount or over unknown/damaged history.**

For safe candidate inspection, `scripts/audit_publication.py` creates disposable Git metadata and a prospective index using the checkout's `.gitignore`, then deletes that metadata. It records candidate paths/sizes/SHA256 hashes without modifying the actual index. An exported candidate snapshot was given its own temporary Git repository solely for local CI replay. These are audit fixtures, not restored project history.

## 2. Candidate files, ignore rules, secrets, and local paths

The final prospective Git set contains **90 files**. The largest is the attributed NASA fixture (791,555 bytes); the lockfile and JFK audio fixture are also intentional. No candidate file exceeds 5 MiB. All 17 ignore probes pass. A check of the candidate text found no modeled GitHub/Hugging Face/AWS tokens, private-key blocks, credential-bearing HTTP URLs, user-home paths, or removable-drive absolute paths. No model checkpoint, gallery matrix, virtual environment, generated output, or upload is in that file set.

`.gitignore` now also covers `.pth`/`.ckpt`, matrices, `.env` variants, private keys, local agent/cloud metadata, output/gallery directories and coverage outputs. `.dockerignore` similarly excludes credential/model/output material. The ignore patterns retain intended source/configuration/docs and permitted fixtures; they do not ignore every image/audio file. Ignored local models/cache/output directories remain on disk for testing and are not deleted.

This is a **bounded candidate-file scan**, not proof that arbitrary secrets or historical credentials do not exist. Real already-tracked ignored files cannot be checked behind the Git mount. On the host, `git ls-files -ci --exclude-standard` must be reviewed; ignore rules alone cannot untrack files or erase history. Recovered history needs its own credential/artifact review before publication.

Operational paths such as `/cache` in Docker, `~/.cache/ai-demo-starter`, and generic documented environment variables are intentional. User-specific absolute paths are confined to ignored local verification data, not the prospective source set. Candidate manifests are stored in ignored `.local/publication/files.json` and `files.txt`; they are not uploaded.

## 3. Professional project metadata and release materials

Version 0.1.0 matches `pyproject.toml`, the runtime constant, the project entry in `uv.lock`, README/changelog/release notes, Docker examples, and built distribution metadata. The package now declares the SPDX expression `MIT` and includes LICENSE through PEP 639 metadata. Its development classifier is Alpha, appropriate for the stated v0.1 research/demo scope. Keywords/classifiers aid discovery without claiming unsupported serving capabilities.

The README describes local CPU workflows, explicit acquisition, tests, adapters, and known limits, and links the publication checklist/notes. CHANGELOG records stabilization and publication preparation without pretending a release was published. Relative documentation links resolve. Third-party fixtures have attribution/hashes; pretrained artifacts are excluded. Project URLs are not invented because the actual remote/owner is inaccessible and not supplied.

Proposed GitHub settings (not applied):

- Name: `ai-demo-starter`.
- Description: **CPU-first local AI demos with Gradio: object detection, speech recognition, image retrieval, and reusable model adapters.**
- Topics: `python`, `gradio`, `pytorch`, `torchvision`, `faster-whisper`, `object-detection`, `speech-recognition`, `image-retrieval`, `model-adapters`, `cpu-inference`, `machine-learning`.
- Code license: MIT; include the separate model/asset terms and unknowns.
- Proposed release title: **v0.1.0 — CPU-first AI demo toolkit**.

Ready-to-review materials: [release checklist](release-checklist.md), [proposed release notes](release-notes-0.1.0.md), [changelog](../CHANGELOG.md), and [model terms](model-licenses.md). Once the real GitHub URL is selected, add truthful project URLs to package metadata and rerun build/lock checks. No remote metadata was changed.

## 4. CI compatibility and executed checks

All workflow shell steps were replayed from an exported candidate snapshot in a fresh Python 3.11 environment, installing only **dev+UI**, not the full ML environment. The replay used the included uv.lock and the same uv 0.11.21 as the workflow. The pytest step set `UV_OFFLINE=1` and telemetry flags. It completed without model downloads, with no Torch or faster-whisper installed. The build and pip-wheel smoke also ran from that clean snapshot.

Workflow actions are pinned by full commit SHA; both commit IDs were checked against their official GitHub repositories. Checkout uses `11bd71901bbe5b1630ceea73d27597364c9af683`; setup-uv uses `37802adc94f370d6bfd71619e3f0bf239e1f3b78`. Permissions are `contents: read`. Commands after installation use `uv run --locked`, so they cannot silently rewrite the selected resolution. Hosted runner provisioning/action execution and the GitHub-hosted Ubuntu job have **not** been observed; local NixOS replay verifies command/profile compatibility, not all runner behavior.

| Check | Exact command | Observed result |
|---|---|---|
| Candidate index/ignore/security-path scan | `python scripts/audit_publication.py` | 90 candidates ; 17 probes; 0 findings under the stated rules |
| Lock validity | `uv lock --check` |Passed; 89 resolved packages |
| CI installation profile | `uv sync --locked --extra dev --extra ui` |Passed in new snapshot environment |
| Lint | `uv run --locked ruff check .` |Passed |
| Formatting | `uv run --locked ruff format --check .` |Passed |
| Source types | `uv run --locked mypy src` |Passed; 29 files |
| CI deterministic tests | `uv run --locked pytest --cov=ai_demo_starter --cov-report=term-missing` | 62 passed, 7 opt-in skipped, 0 failed; 76% rounded coverage |
| Full real-model/live-HTTP suite | `uv run --locked pytest --real-models --ui-live -v --junitxml=.local/publication/full.xml` | 69 passed, 0 skipped, 0 failed; 4 upstream deprecation warnings |
| Distribution build | `uv build` |Wheel and sdist built |
| Clean pip wheel install | `uv run --locked python scripts/verify_wheel.py` |CLI/imports/templates passed outside source tree in CI snapshot |
| Installed-wheel real runtimes | `uv run --locked python scripts/verify_wheel_runtime.py` |All 3 real CPU service pipelines and all 3 UI constructions passed outside source tree |
| Compose rendering | `docker compose config` |Passed, including localhost port mapping and persistent cache |
| Docker availability | `nix-shell --run 'docker version'` |Client 29.8.1; daemon socket does not exist |
| Metadata/version/doc links | TOML/AST/archive/link inspection |Consistent 0.1.0, SPDX MIT, packaged resources, relative links resolve |
| Hosted GitHub CI | No workflow dispatch/push performed |Not run; must pass on the reviewed source commit |

The complete suite includes real detector threshold/box/annotation checks, real 11s WAV and resampled FLAC transcription, actual 576-channel extraction/gallery reload/search, and live Gradio uploads/results/downloads. No mock result is presented as model inference. Physical microphone/browser visual checks remain unverified. The earlier [implementation report](release.md) explains result schemas, outputs, and timing boundaries.

Local evidence is in ignored `.local/publication`: `files.json`, `ci.json`, `ci.log`, `ci-wheel.json`, `full.xml`, `metadata.json`, `git-mount.json`, `license-evidence.json`, and final artifact data. Installed-wheel runtime details remain in `.local/verification/wheel-runtime.json`. These files may contain local paths and are not candidate publication files.

## 5. Docker review

The existing Dockerfile uses Python 3.11 slim-bookworm, uv 0.11.21, frozen locked CPU dependencies, a non-root uid 10001, a persistent `/cache`, and explicit preparation. Startup does not download models. Its internal 0.0.0.0 listener is mapped only to localhost by Compose. The runtime command and example configurations agree. Upload/cache paths are not served as unrestricted static directories.

The Docker client is installed, but `/var/run/docker.sock` is absent. No daemon was started and no system configuration was changed. A successful container build or inference cannot be claimed. Named-volume permissions, actual runtime/linker behavior, and cache preparation must still be tested on a daemon-enabled host. Base images use version tags rather than immutable digests; review/pin them before reproducible image distribution. See [deployment](deployment.md) for the unverified instructions.

## 6. TorchVision licensing investigation

The official model overview and immutable upstream README were retrieved, along with the software LICENSE and both selected model pages. The README at commit `a034671605659e24ff1de1142079bf318ac3b123` explicitly warns that pretrained models may have their own dataset-derived terms and leaves use-case permission to the user. The BSD software license is not a blanket model/dataset grant.

No separate permissive artifact license was established for `SSDLite320_MobileNet_V3_Large_Weights.COCO_V1` or `MobileNet_V3_Small_Weights.IMAGENET1K_V1` through the selected model documentation. Their runtime license fields remain null rather than guessed. COCO/image and ImageNet terms remain separate. SWAG-specific CC-BY-NC terms are not attributed to models this toolkit does not use.

This does not prevent publishing the toolkit's original MIT source without weights, but it is not legal clearance for weight redistribution or any particular commercial/public use. The publication docs preserve this distinction, give upstream references/hashes and require deliberate model acquisition. See [model-licenses.md](model-licenses.md) for the exact upstream quotation and sources.

## 7. Remaining gates and exact next steps

Run the following **from this project directory in a normal host terminal outside the environment's Git mount**. These are read-only diagnostics; confirm that the reported top-level path is the intended project, not an ancestor repository:

```bash
pwd -P
ls -ld .git
git rev-parse --show-toplevel
git rev-parse --absolute-git-dir
git status --short --branch
git log -5 --oneline
git fsck --full
git ls-files -ci --exclude-standard
git diff --check
git diff --cached --check
git diff --cached --stat
```

If a valid project history is visible, reuse it and inspect the full intended staged diff and existing reachable history before publication. If metadata is damaged, recover from a verified local clone/backup without replacing it blindly. If the project is independently confirmed genuinely new with no history to recover, initialize a fresh repository only then; this audit did not make that determination or modify real metadata. Do not infer freshness merely from this environment's empty mount.

After history and repository identity are confirmed, use the [release checklist](release-checklist.md), select the actual GitHub owner/URL, and inspect staged changes before any authorized push. Run the workflow on the reviewed commit when publication is authorized; remote CI success is not invented here. Release notes are prepared, but no tag or GitHub release exists from this work.

For Docker on a daemon-enabled host:

```bash
docker build -t ai-demo-starter:0.1.0 .
docker compose run --rm aidemo aidemo models prepare --config configs/detection.yaml
docker compose up
```

Then upload an allowed image, verify annotated preview/download and metadata, restart with the existing cache, and test missing-cache behavior. These commands have not succeeded as container tests here and do not authorize an image push. Public production hosting needs a separate design/security/operations effort, not merely a changed Gradio bind address.

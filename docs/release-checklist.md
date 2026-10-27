# v0.1.0 publication checklist

This checklist separates source publication, container distribution, and public production hosting. Nothing here authorizes a push, tag, release, upload, or deployment. Check [publication audit](publication.md) for executed evidence and remaining gates.

## Local CPU toolkit source

- [x] Preserve the existing adapter/service/UI architecture.
- [x] Confirm package/CLI version 0.1.0 and clearly describe the v0.1 scope.
- [x] Include MIT license for original code and attributed permitted example/test assets.
- [x] Distinguish framework code, weights, datasets, and fixture licenses; never label unknown weight terms as MIT/BSD.
- [x] Exclude weights, virtual environments, user uploads, gallery indexes, credentials, and generated artifacts from the prospective Git file set.
- [x] Keep model acquisition explicit and normal execution offline.
- [x] Supply locked dependencies, actual tests, package builds, clean-wheel checks, and real CPU inference evidence.
- [x] Prepare README, changelog, contribution guide, release notes, description, and topics.
- [ ] Inspect the actual host Git metadata outside the environment's empty read-only mount; recover/reuse history if present.
- [ ] Confirm the intended GitHub owner/repository URL and add accurate project URLs after it is selected.
- [ ] Review the real staged diff and tracked ignored files; audit reachable Git history for credentials/large artifacts if existing history is recovered.
- [ ] Confirm remote GitHub Actions passes on the exact reviewed commit. Local workflow-command replay does not prove the hosted job.
- [ ] Obtain explicit authorization before pushing or creating any tag/release. Review the proposed notes and artifacts first.

## Source review commands

Run these only in a real, verified host checkout. `git ls-files -ci` finds already-tracked files that new ignore rules cannot remove from history:

```bash
git status --short --branch
git rev-parse --absolute-git-dir
git log -5 --oneline
git remote -v
git ls-files -ci --exclude-standard
git diff --check
git diff --cached --check
git diff --cached --stat
```

Review actual file contents before staging. A safe in-environment prospective file audit, independent of real history, is:

```bash
python scripts/audit_publication.py
```

This records filenames/hashes in ignored `.local/publication` and checks ignore rules, selected secret patterns, model/large artifacts, and user-specific absolute paths. It uses disposable Git metadata and never modifies the checkout's `.git`. It cannot audit inaccessible actual history or already-tracked ignored files. Do not run `git init` over unknown or damaged metadata.

## Validation commands

On NixOS enter `nix-shell` first:

```bash
uv sync --locked --all-extras
uv lock --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src
uv run --locked pytest -v
uv run --locked pytest --real-models --ui-live -v
uv build
uv run --locked python scripts/verify_wheel.py
uv run --locked python scripts/verify_wheel_runtime.py
```

Real-model tests require the explicitly prepared `.local/models` cache described in [testing](testing.md). These commands do not push or publish anything. The wheel-runtime script uses the built wheel in a fresh environment outside the source tree.

## Docker distribution — separate gate

- [x] Non-root runtime, CPU dependency profile, persistent cache, explicit model acquisition, and localhost host-port mapping reviewed.
- [x] `.dockerignore` excludes private/configuration/cache/model material.
- [ ] Build and launch the image with a working daemon, then make a real uploaded-image prediction and download its annotation.
- [ ] Exercise model-cache preparation/persistence as uid 10001 and missing-cache failures.
- [ ] Validate speech/retrieval images before advertising those container profiles as tested.
- [ ] Review base image digests, dependency/image vulnerabilities, and model terms before distributing any image. No pretrained weights should be embedded by default.

Commands for a daemon-enabled host (not executed successfully in this environment):

```bash
docker build -t ai-demo-starter:0.1.0 .
docker compose run --rm aidemo aidemo models prepare --config configs/detection.yaml
docker compose up
```

Open localhost:7860 and test an allowed image. Stop with `docker compose down`; this retains the named cache volume. No image push is authorized.

## Public production deployment — outside v0.1 scope

- [ ] Add and validate access controls, TLS, rate/abuse controls, operational resource/disk limits, observability, and a privacy/retention policy appropriate to the deployment.
- [ ] Review model/data terms for the intended audience/use and complete a public-service security review.
- [ ] Exercise overload/failure handling and operational recovery on the actual hosting environment.

The current toolkit is not approved as a public production service. Docker readiness would not satisfy this gate by itself.

# Configuration schema 1

Root sections are `demo`, `model`, `downloads`, `inference`, `input`, `output`, `server`, and `logging`, plus `schema_version` and `gallery_dir`. Unknown fields are errors. YAML is parsed with `safe_load` and capped at 1 MiB. Validation errors retain field locations. Built-in model identifiers, backends, revisions, and input allowlists must match their task. Only CPU devices are supported.

`model.cpu_threads` defaults to 2 (1–32). Torch thread settings are process-wide; use separate processes for independently tuned models. Speech supports `language` (null means detection), `beam_size` (default 5), `compute_type` (default `int8`), a selected tiny/base/small Systran model (optionally `.en`), or a trusted local converted model directory. Changing speech size requires selecting an appropriate immutable revision or omitting revision during preparation so the resolved commit is recorded. Unsupported compute types/languages produce backend errors.

`downloads.allow_download` defaults to false. Only explicit preparation, or deliberate `allow_download: true`, allows acquisition. Cache defaults to `~/.cache/ai-demo-starter`. TorchVision revisions are fixed to the enum values in the supplied examples; mutable `DEFAULT` aliases are rejected. `output.save_artifacts` defaults to true and controls downloadable runner PNGs; previews still work when false.

Relative cache/gallery/model directory paths resolve from the YAML file. Tilde expands in cache and model paths. Default configurations are packaged resources; no-config runs keep their gallery at `<cwd>/.local/galleries/example`. Root `configs/` examples mirror the packaged templates, verified by a consistency test.

Environment overrides: `AIDEMO_DEVICE`, `AIDEMO_ALLOW_DOWNLOAD`, `AIDEMO_CACHE_DIR`, `AIDEMO_HOST`, `AIDEMO_PORT`. Values pass the same validation as YAML. Use an absolute cache override to share prepared models between configurations. No API keys are required.

Default upload limits are 10 MiB (speech template: 25 MiB), 20 million decoded image pixels, and 300 seconds of audio. Audio is additionally capped at eight channels and 32 million decoded scalar samples. Queue size is 16; `inference.max_concurrency` defaults to 1, and the runner serializes access to its model even if the UI limit is raised. Native execution has no hard interruptible timeout.

Server defaults are `127.0.0.1:7860`, `share: false`; deliberately changing these expands exposure. Gradio analytics and monitoring are disabled by the application. `logging.level` selects the CLI server log level (DEBUG/INFO/WARNING/ERROR/CRITICAL); trusted library applications can configure their own Python logging handlers. Inputs/transcripts are not logged by the toolkit. The starter has no dynamic import or plugin sandbox.

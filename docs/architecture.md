# Architecture

`cli.py` validates YAML before creating an adapter through `core.registry.create_adapter`. `config` has no frontend dependency. The registry contains trusted callable factories; custom application code registers them explicitly. A registered adapter must report the configured task. Imports do not initialize model runtimes or download weights.

`core.protocols.ModelAdapter[Input, Prepared, Output, Result]` defines `load`, `preprocess`, `predict`, `postprocess`, `metadata`, and `close`. Detection, speech, and image-embedding subclasses give each task its own public input/output contract. Backend-specific intermediate tensors remain adapter implementation details. See the [adapter tutorial](../examples/custom_adapter/README.md).

`LifecycleManager` serializes initialization, loads once, records unloaded/loading/loaded/failed states, and preserves categorized loading errors and their original causes. `InferenceRunner` locks a model through each request, times its stages, normalizes unexpected exceptions, and retains at most 16 downloadable annotations. `close` releases model references and temporary artifacts. Application process exit calls service cleanup. CPU execution is explicit; unsupported devices are rejected without hidden fallback.

`core.schemas` contains separate Pydantic runtime DTOs for detection, speech, retrieval, model metadata, and diagnostics. Detection boxes are clipped `xyxy` original-image pixels with finite scores. Speech exposes backend language probabilities and segment timestamps when available. No word timestamps are synthesized. Retrieval returns ordered item IDs, cosine scores, ranks, model fingerprints, and index schema version.

`core.service.DemoService` validates UI inputs and translates typed results into preview images, artifact paths, and JSON. `ui.factory` only constructs Gradio components and callback bindings; adapters never import Gradio. Gallery code is independent of both the service and frontend.

## Timing boundaries

The runner uses `perf_counter`. Model-load time is measured separately (zero once loaded); preprocessing, prediction, and postprocessing have non-overlapping intervals. Total covers validation inside the runner, acquisition, all stages, and annotation file writes. Runner lock wait is excluded. JSON serialization and HTTP/upload/download transfer are excluded. The speech prediction method consumes the complete segment generator before returning.

The UI service adds image/audio decoding to preprocessing and total. Retrieval service total also includes index load/compatibility checking, ranking, and result image decoding; its postprocessing adds ranking/preview work. Retrieval's outer total can include runner lock wait. These are processing diagnostics for an individual request, not latency or throughput benchmarks. No memory metrics or hard timeouts are claimed.

## Weights and reproducibility

Configuration defaults to offline execution. `models prepare` explicitly opts into trusted upstream sources. Torch checkpoints are matched to fixed weight enums, verified against full SHA256 digests (including cached files), and loaded with `weights_only=True`. Model constructors use `weights=None` and `weights_backbone=None` where applicable to prevent implicit acquisition. Whisper resolves a selected Systran repository revision, records its snapshot, and subsequently uses a local directory with `local_files_only=True`.

`uv.lock` pins the tested dependency graph and CPU wheel sources. Package metadata permits compatible version ranges for pip users; pip does not consume the uv lock. Higher Python versions/platforms beyond the tested environment remain unverified. Model weights are never bundled in distributions.

## Gallery schema 1

Each index contains `metadata.json` and a content-named `embeddings-<sha256>.npy` matrix. The manifest stores item IDs (SHA256 of relative source paths), safe relative image references, an absolute local source root, feature dimension, normalization policy, model metadata, and its fingerprint. The fingerprint hashes canonical JSON metadata excluding lifecycle state, including weight revision, layer/dimension description, preprocessing, and normalization. Loading checks this hash; query adapters must match it exactly. Different weights/layers/preprocessing require a rebuild.

Matrices are normalized finite float32 rows, loaded with `allow_pickle=False` and mmap. Indexes are limited to 10,000 items and 256 MiB; metadata is limited to 10 MiB. Ranking uses cosine similarity with float64 intermediates and stable ties in sorted source-path order. Empty indexes return no matches; building an empty gallery is rejected. Source paths and symlinks cannot escape the source root.

Build/update creates a new complete matrix before atomically replacing the manifest. An exclusive `.build.lock` prevents concurrent builders. Old matrix generations remain valid for readers; administrators may remove unreferenced matrices when no readers use them. After a crashed builder, remove a stale lock only after confirming no build is running. Indexes are local references, not portable image archives: moving source images requires rebuilding. Metadata is trusted local configuration, not an authenticated or adversarial data format.

# Complete trusted adapter example

`app.py` implements `PrefixEmbeddingAdapter` using the existing image-embedding contract. It delegates official MobileNet preprocessing/loading, selects the first 128 average-pooled channels, renormalizes them, and changes pipeline metadata so the index fingerprint differs. Truncation is an extension example, not a quality claim. Both the contract and real 128-dimensional output are tested.

Use a retrieval-enabled installation and enter `nix-shell` first on NixOS. Run from the repository root:

```bash
python examples/custom_adapter/app.py models prepare --config examples/custom_adapter/config.yaml
python examples/custom_adapter/app.py gallery build --config examples/custom_adapter/config.yaml --input examples/gallery --output .local/galleries/custom
python examples/custom_adapter/app.py run retrieval --config examples/custom_adapter/config.yaml
```

The example explicitly calls `register_adapter("mobilenet_prefix", PrefixEmbeddingAdapter)` before invoking the stock Typer CLI. Its YAML selects that name. The existing Gradio retrieval UI and service are unchanged. Ordinary `aidemo` processes do not see this process-local registration; launch through the example application.

For a different model, implement load/preprocess/predict/postprocess/metadata/close with typed public input and output. Detection returns `DetectionResult`, speech `SpeechResult`, and embeddings a finite nonzero NumPy vector. Report model identity, immutable weight revision, preprocessing, feature layer/dimension, normalization, and actual load state. Metadata must be stable across load state and distinguish every incompatible embedding pipeline. Rebuild galleries when any of these change.

Adapters and local model artifacts are trusted application code/data. YAML does not dynamically import Python paths. An ONNX extension would need explicit tensor names/shapes/dtypes, preprocessing, output interpretation, device policy, weight provenance, and numerical contract tests; no unverified generic ONNX adapter is supplied. A later Re-ID model should also describe person/camera IDs, query/gallery split, and model-specific normalization; no Re-ID metrics are claimed here.

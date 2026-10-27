# Models, provenance, and terms

Original toolkit code is MIT. Framework code licenses do **not** automatically license pretrained weights or their training data. Weights are not bundled or redistributed. Preparation is an explicit network operation to upstream sources; review their current terms for your intended use. Unknown separate weight-license information remains null in runtime metadata.

## Upstream license evidence reviewed for publication

Checked on 2026-10-27: TorchVision's [official model documentation](https://docs.pytorch.org/vision/stable/models.html) explicitly states:

> The pre-trained models provided in this library may have their own licenses or terms and conditions derived from the dataset used for training. It is your responsibility to determine whether you have permission to use the models for your use case.

The same statement appears in its [README, Pre-trained Model License](https://github.com/pytorch/vision/blob/a034671605659e24ff1de1142079bf318ac3b123/README.md#pre-trained-model-license), inspected at the immutable upstream commit `a034671605659e24ff1de1142079bf318ac3b123`. The [BSD-3-Clause software license](https://github.com/pytorch/vision/blob/a034671605659e24ff1de1142079bf318ac3b123/LICENSE) does not resolve the separate model/dataset terms. The selected detector and MobileNet weight descriptions did not establish a separate permissive artifact license during this audit. Their license metadata therefore remains unknown. TorchVision's separately identified SWAG CC-BY-NC terms concern SWAG models; neither demo uses those models, and those terms are not assigned to these weights.

Publishing this toolkit's original MIT source is distinct from redistributing pretrained artifacts or approving every downstream use. The repository/distributions contain no pretrained weights. This audit provides provenance and upstream evidence, not legal clearance for a particular commercial application. Model preparation remains a deliberate user action.

## Object detection

- Model: SSDLite320 MobileNetV3 Large, authored/maintained in TorchVision by PyTorch contributors; architecture builds on MobileNetV3 and SSD research.
- Source and weight description: [official model documentation](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.ssdlite320_mobilenet_v3_large.html).
- Revision: `SSDLite320_MobileNet_V3_Large_Weights.COCO_V1`.
- URL: `https://download.pytorch.org/models/ssdlite320_mobilenet_v3_large_coco-a79551df.pth`.
- Size: 14,069,355 bytes (about 14 MB).
- Full SHA256: `a79551df90c79834bcd3bb3845ef9d966b5449a3a9b2833ae8404778ca5d65d2`.
- Framework code: TorchVision BSD-3-Clause. A separate explicit permissive license for this weight artifact was not established; runtime `license` is null. Do not describe these weights as BSD-licensed solely from the code license.
- Training dataset: COCO. [COCO terms](https://cocodataset.org/#termsofuse) distinguish annotation licensing and original image rights (including Flickr source terms).
- Preprocessing: enum-provided RGB scaling to [0,1]; the detector internally resizes/normalizes and maps predictions back to original-image dimensions.

## Image embeddings

- Model: TorchVision MobileNetV3 Small, PyTorch contributors.
- [Official model documentation](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html).
- Revision: `MobileNet_V3_Small_Weights.IMAGENET1K_V1`.
- URL: `https://download.pytorch.org/models/mobilenet_v3_small-047dcff4.pth`.
- Size: 10,306,551 bytes (about 10 MB).
- Full SHA256: `047dcff4addef86ea5bc2eff13c9614dc11f47ab1160d0a71a25e7db994f4e1f`.
- Framework code: BSD-3-Clause. Separate weight-artifact license not established; runtime `license` is null. Review upstream terms for your application.
- Training dataset: ImageNet-1K, with [ImageNet access and use terms](https://www.image-net.org/download.php); original image rights remain separate.
- Feature pipeline: `features -> avgpool -> flatten`, bypassing the classifier, yielding 576 channels. Official transforms resize the short edge to 256 with bilinear interpolation, center-crop 224, scale [0,1], and normalize with ImageNet mean/std. Result vectors are L2 normalized.
- These are generic classification features, not validated person Re-ID embeddings. No retrieval accuracy or demographic fairness claim is made.

## Speech

- Model: `Systran/faster-whisper-tiny`, converted by SYSTRAN from OpenAI Whisper tiny.
- [Pinned model card](https://huggingface.co/Systran/faster-whisper-tiny/blob/d90ca5fe260221311c53c58e660288d3deb8d356/README.md).
- Revision: `d90ca5fe260221311c53c58e660288d3deb8d356`.
- Model card license: MIT. [OpenAI Whisper code/model](https://github.com/openai/whisper) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) are MIT; training data does not inherit that license.
- Weight download: approximately 76 MB plus tokenizer/configuration. Source training data: Whisper's multilingual weakly supervised web audio corpus; see the [Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md) for data, intended uses, and limitations.
- Runtime: CTranslate2 CPU INT8; decode finite mono float32 audio and resample to 16 kHz. Segment timestamps and language probabilities are backend outputs; word timestamps are not enabled.
- Tiny/base/small variants (including .en) and trusted local converted directories are supported; only default tiny was verified here. Pin the appropriate revision when changing repositories. Local models have unknown source/license metadata until supplied by a custom adapter.

## Acquisition and cache

Use `uv run aidemo models prepare --config configs/<task>.yaml`. Torch checkpoints live in `<cache>/checkpoints`; cached bytes are rehashed before safe `weights_only=True` loading. Whisper stores snapshots below `<cache>/hub` and an atomic `speech-<identifier>.json` pointer to the resolved commit. Subsequent execution is local-only. Deleting the cache requires explicit preparation again. The default cache is `~/.cache/ai-demo-starter`; `AIDEMO_CACHE_DIR` overrides it.

No unreviewed model-code execution or arbitrary checkpoint import is offered. Review weight/data rights before redistribution or commercial/public deployment. Legal review beyond documenting published provenance and unknowns was not performed.

## Example assets

The three colored shapes in `examples/gallery` are original programmatically generated assets under the project's MIT license, reproducible with `scripts/generate_gallery.py`. They are not accuracy evidence. Real inference uses permitted fixtures with attribution and hashes in [tests/fixtures/README.md](../tests/fixtures/README.md).

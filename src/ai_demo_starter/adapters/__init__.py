from .detection.torchvision import TorchVisionDetectionAdapter
from .retrieval.torchvision import TorchVisionEmbeddingAdapter
from .speech.faster_whisper import FasterWhisperAdapter

__all__ = [
    "TorchVisionDetectionAdapter",
    "TorchVisionEmbeddingAdapter",
    "FasterWhisperAdapter",
]

class AIDemoError(Exception):
    """Base error exposed by the library."""


class ConfigurationError(AIDemoError):
    pass


class ModelNotFoundError(AIDemoError):
    pass


class ModelLoadError(AIDemoError):
    pass


class UnsupportedBackendError(AIDemoError):
    pass


class InvalidInputError(AIDemoError):
    pass


class InferenceError(AIDemoError):
    pass


class GalleryIndexError(AIDemoError):
    pass

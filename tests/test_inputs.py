import io

import numpy as np
import pytest
from PIL import Image

from ai_demo_starter.core.errors import InvalidInputError
from ai_demo_starter.processing.audio import load_audio
from ai_demo_starter.processing.images import load_image


def test_image_limits_checked_before_decode():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100)).save(buffer, format="PNG")
    with pytest.raises(InvalidInputError, match="pixel"):
        load_image(buffer.getvalue(), max_pixels=100)
    with pytest.raises(InvalidInputError, match="size"):
        load_image(buffer.getvalue(), max_bytes=1)
    with pytest.raises(InvalidInputError, match="format"):
        load_image(buffer.getvalue(), allowed_formats=("jpeg",))


@pytest.mark.parametrize("data", [b"not an image", b"", None])
def test_bad_image(data):
    with pytest.raises(InvalidInputError):
        load_image(data)


def test_integer_stereo_audio_and_duration():
    samples = np.full((8000, 2), 16384, dtype=np.int16)
    rate, audio, duration = load_audio((8000, samples))
    assert rate == 8000 and duration == 1
    np.testing.assert_allclose(audio, 0.5)


def test_unsigned_pcm_silence_and_channels():
    _, audio, _ = load_audio((16000, np.full(16, 128, dtype=np.uint8)))
    np.testing.assert_array_equal(audio, 0)
    with pytest.raises(InvalidInputError, match="channel"):
        load_audio((16000, np.ones((10, 9))))


@pytest.mark.parametrize("rate,data", [(0, [1]), (16000, []), (16000, [np.nan])])
def test_invalid_audio(rate, data):
    with pytest.raises(InvalidInputError):
        load_audio((rate, np.array(data)))


def test_audio_duration_limit():
    with pytest.raises(InvalidInputError, match="duration"):
        load_audio((1, np.ones(10)), max_seconds=1)

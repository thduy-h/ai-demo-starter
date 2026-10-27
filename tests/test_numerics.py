import math

import numpy as np
import pytest

from ai_demo_starter.core.errors import InvalidInputError
from ai_demo_starter.processing.embeddings import cosine_similarity, normalize_embedding


@pytest.mark.parametrize(
    "q,g",
    [
        ([1, 0], [[1, 0], [0, 1], [-1, 0]]),
        ([3, 4], [[6, 8], [4, -3], [-3, -4]]),
        ([1e30, 1e30], [[1e30, 0], [0, 1e30]]),
        ([1e-30, 0], [[1e-30, 0], [0, 1e-30]]),
    ],
)
def test_against_independent_reference(q, g):
    expected = []
    for row in g:
        dot = math.fsum(float(a) * float(b) for a, b in zip(q, row, strict=True))
        expected.append(dot / (math.hypot(*q) * math.hypot(*row)))
    np.testing.assert_allclose(cosine_similarity(np.array(q), np.array(g)), expected, atol=1e-6)


@pytest.mark.parametrize("vector", [[0, 0], [np.nan, 1], [np.inf, 1], [[1, 2]]])
def test_rejects_invalid_vectors(vector):
    with pytest.raises(InvalidInputError):
        normalize_embedding(np.array(vector))


@pytest.mark.parametrize("scale", [1.0, 1e30, 1e-30])
def test_normalization_extremes(scale):
    result = normalize_embedding(np.array([3 * scale, 4 * scale]))
    np.testing.assert_allclose(result, [0.6, 0.8], atol=1e-6)


def test_reject_zero_gallery_and_dimensions():
    with pytest.raises(InvalidInputError):
        cosine_similarity(np.ones(2), np.zeros((1, 2)))
    with pytest.raises(InvalidInputError):
        cosine_similarity(np.ones(2), np.ones((1, 3)))

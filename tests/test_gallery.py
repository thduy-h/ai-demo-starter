import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from ai_demo_starter.core.errors import GalleryIndexError
from ai_demo_starter.core.protocols import ImageEmbeddingAdapter
from ai_demo_starter.core.schemas import ModelMetadata
from ai_demo_starter.retrieval.index import GalleryIndex, build_gallery, fingerprint


class TestEmbeddingAdapter(ImageEmbeddingAdapter):
    __test__ = False

    def load(self):
        pass

    def preprocess(self, inputs):
        return np.array(Image.open(inputs).convert("RGB")).mean(axis=(0, 1))

    def predict(self, inputs):
        return inputs

    def postprocess(self, outputs):
        return outputs

    def metadata(self):
        return ModelMetadata(
            identifier="test-colors",
            family="contract fixture",
            task="retrieval",
            backend="test",
            revision="1",
        )


@pytest.fixture
def gallery(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (20, 20), "red").save(source / "a.png")
    Image.new("RGB", (20, 20), "blue").save(source / "b.png")
    return build_gallery(source, tmp_path / "index", TestEmbeddingAdapter())


def test_gallery_roundtrip(gallery):
    index = GalleryIndex.load(gallery.root)
    matches = index.search(np.array([1.0, 0.0, 0.0]), 20)
    assert [m.source for m in matches] == ["a.png", "b.png"]
    np.testing.assert_allclose([m.similarity for m in matches], [1.0, 0.0])
    index.assert_compatible(TestEmbeddingAdapter())
    assert index.image_path("a.png").is_file()


def test_stable_ties_and_rebuild(gallery):
    query = np.array([1.0, 0.0, 1.0])
    assert [m.source for m in gallery.search(query)] == ["a.png", "b.png"]
    before = gallery.items[0]["item_id"]
    source = Path(gallery.metadata["source_root"])
    Image.new("RGB", (20, 20), "green").save(source / "c.png")
    updated = build_gallery(source, gallery.root, TestEmbeddingAdapter())
    assert len(updated.items) == 3
    assert updated.items[0]["item_id"] == before
    assert not (gallery.root / ".build.lock").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("fingerprint", "corrupt"),
        ("normalization", "none"),
        ("schema_version", 2),
        ("embedding_dimension", 999),
        ("embeddings_file", "../escape.npy"),
    ],
)
def test_reject_corrupt_metadata(gallery, field, value):
    manifest = gallery.root / "metadata.json"
    metadata = json.loads(manifest.read_text())
    metadata[field] = value
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(GalleryIndexError):
        GalleryIndex.load(gallery.root)


def test_reject_unsafe_source_and_missing_image(gallery):
    manifest = gallery.root / "metadata.json"
    metadata = json.loads(manifest.read_text())
    metadata["items"][0]["source"] = "../escape.png"
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(GalleryIndexError):
        GalleryIndex.load(gallery.root)
    gallery.image_path("a.png").unlink()
    with pytest.raises(GalleryIndexError, match="missing"):
        gallery.image_path("a.png")


def test_symlink_cannot_escape(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    external = tmp_path / "external.png"
    Image.new("RGB", (10, 10), "red").save(external)
    (source / "link.png").symlink_to(external)
    with pytest.raises(GalleryIndexError, match="escapes"):
        build_gallery(source, tmp_path / "index", TestEmbeddingAdapter())


def test_fingerprint_covers_preprocessing(gallery):
    metadata = TestEmbeddingAdapter().metadata().model_dump(exclude={"load_state"})
    assert fingerprint(metadata) == gallery.fingerprint
    metadata["revision"] = "another-weight"
    assert fingerprint(metadata) != gallery.fingerprint


def test_incompatible_index(gallery):
    adapter = TestEmbeddingAdapter()
    original = adapter.metadata

    def changed():
        result = original()
        result.revision = "2"
        return result

    adapter.metadata = changed
    with pytest.raises(GalleryIndexError, match="does not match"):
        gallery.assert_compatible(adapter)


def test_empty_and_invalid_top_k(gallery):
    with pytest.raises(GalleryIndexError):
        gallery.search(np.array([1.0, 0.0, 0.0]), 0)
    empty = GalleryIndex(gallery.root, np.empty((0, 3)), [], gallery.fingerprint, gallery.metadata)
    assert empty.search(np.array([1.0, 0.0, 0.0])) == []

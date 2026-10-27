from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.errors import GalleryIndexError
from ..core.schemas import RetrievalMatch
from ..processing.embeddings import cosine_similarity, normalize_embedding


class GalleryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str = Field(min_length=1)
    source: str

    @field_validator("source")
    @classmethod
    def safe_source(cls, value: str) -> str:
        if not value or Path(value).is_absolute() or ".." in Path(value).parts or "\\" in value:
            raise ValueError("Gallery source must be a safe relative path")
        return value


class IndexMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int
    fingerprint: str
    model: dict[str, Any]
    embedding_dimension: int = Field(gt=0, le=16384)
    normalization: str
    source_root: str
    embeddings_file: str
    items: list[GalleryItem] = Field(max_length=10000)


class GalleryIndex:
    VERSION = 1

    def __init__(
        self,
        root: Path,
        embeddings: np.ndarray,
        items: list[dict[str, Any]],
        fingerprint: str,
        metadata: dict[str, Any],
    ):
        self.root, self.embeddings, self.items = root, embeddings, items
        self.fingerprint, self.metadata = fingerprint, metadata

    @classmethod
    def load(cls, root: str | Path) -> GalleryIndex:
        root = Path(root).resolve()
        try:
            meta_path = root / "metadata.json"
            if meta_path.stat().st_size > 10 * 1024 * 1024:
                raise GalleryIndexError("Gallery metadata exceeds size limit")
            meta = IndexMetadata.model_validate_json(meta_path.read_text())
            name = meta.embeddings_file
            if Path(name).name != name or not name.endswith(".npy"):
                raise GalleryIndexError("Invalid embeddings filename")
            emb_path = root / name
            if not emb_path.resolve().is_relative_to(root):
                raise GalleryIndexError("Embeddings file escapes index directory")
            if emb_path.stat().st_size > 256 * 1024 * 1024:
                raise GalleryIndexError("Gallery exceeds index size limit")
            emb = np.load(emb_path, allow_pickle=False, mmap_mode="r")
            if (
                meta.schema_version != cls.VERSION
                or meta.normalization != "l2"
                or emb.ndim != 2
                or emb.shape != (len(meta.items), meta.embedding_dimension)
                or emb.dtype != np.float32
            ):
                raise GalleryIndexError("Gallery schema, normalization or shape mismatch")
            if not np.isfinite(emb).all():
                raise GalleryIndexError("Gallery contains non-finite embeddings")
            if len(emb) and not np.allclose(np.linalg.norm(emb, axis=1), 1, atol=1e-5):
                raise GalleryIndexError("Gallery embeddings must be normalized and nonzero")
            if meta.fingerprint != fingerprint(meta.model):
                raise GalleryIndexError("Gallery model fingerprint is corrupt")
            ids = [item.item_id for item in meta.items]
            sources = [item.source for item in meta.items]
            if len(set(ids)) != len(ids) or len(set(sources)) != len(sources):
                raise GalleryIndexError("Duplicate gallery entries")
            return cls(
                root,
                emb,
                [item.model_dump() for item in meta.items],
                meta.fingerprint,
                meta.model_dump(),
            )
        except GalleryIndexError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise GalleryIndexError(f"Could not load gallery at {root}: {exc}") from exc

    def image_path(self, source: str) -> Path:
        GalleryItem(item_id="validation", source=source)
        root = Path(self.metadata["source_root"]).resolve()
        path = (root / source).resolve()
        if not path.is_relative_to(root):
            raise GalleryIndexError("Gallery image escapes source root")
        if not path.is_file():
            raise GalleryIndexError(f"Gallery image missing: {source}; rebuild the index")
        return path

    def search(self, query: np.ndarray, top_k: int = 5) -> list[RetrievalMatch]:
        if top_k < 1:
            raise GalleryIndexError("top_k must be positive")
        scores = cosine_similarity(query, self.embeddings)
        order = np.argsort(-scores, kind="stable")[: min(top_k, len(scores))]
        return [
            RetrievalMatch(
                item_id=self.items[i]["item_id"],
                source=self.items[i]["source"],
                similarity=float(scores[i]),
                rank=rank,
            )
            for rank, i in enumerate(order, 1)
        ]

    def assert_compatible(self, adapter: Any) -> None:
        if fingerprint(adapter.metadata().model_dump(exclude={"load_state"})) != self.fingerprint:
            raise GalleryIndexError(
                "Gallery model or preprocessing does not match; rebuild the index"
            )


def fingerprint(model: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(model, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_gallery(input_dir: str | Path, output_dir: str | Path, adapter: Any) -> GalleryIndex:
    """Rebuild/update a gallery; replace its manifest only when embeddings are complete."""
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    if not input_dir.is_dir():
        raise GalleryIndexError(f"Gallery input directory not found: {input_dir}")
    files = sorted(
        p
        for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    if not files:
        raise GalleryIndexError("No supported images in gallery directory")
    if len(files) > 10000:
        raise GalleryIndexError("Gallery exceeds 10000 items")
    for path in files:
        if not path.resolve().is_relative_to(input_dir):
            raise GalleryIndexError(f"Gallery symlink escapes source root: {path.name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / ".build.lock"
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise GalleryIndexError("Build in progress or stale .build.lock present") from exc
    os.close(lock_fd)
    temp_path: Path | None = None
    temp_meta: Path | None = None
    try:
        adapter.load()
        vectors, items = [], []
        for path in files:
            vectors.append(
                normalize_embedding(adapter.postprocess(adapter.predict(adapter.preprocess(path))))
            )
            rel = path.relative_to(input_dir).as_posix()
            items.append({"item_id": hashlib.sha256(rel.encode()).hexdigest(), "source": rel})
        emb = np.stack(vectors).astype(np.float32)
        if emb.nbytes > 256 * 1024 * 1024:
            raise GalleryIndexError("Gallery exceeds index size limit")
        model = adapter.metadata().model_dump(exclude={"load_state"})
        with tempfile.NamedTemporaryFile(dir=output_dir, delete=False, suffix=".npy") as handle:
            np.save(handle, emb, allow_pickle=False)
            temp_path = Path(handle.name)
        final_name = f"embeddings-{hashlib.sha256(emb.tobytes()).hexdigest()}.npy"
        os.replace(temp_path, output_dir / final_name)
        temp_path = None
        meta = IndexMetadata(
            schema_version=1,
            fingerprint=fingerprint(model),
            model=model,
            embedding_dimension=emb.shape[1],
            normalization="l2",
            source_root=str(input_dir),
            embeddings_file=final_name,
            items=[GalleryItem(**item) for item in items],
        )
        with tempfile.NamedTemporaryFile(mode="w", dir=output_dir, delete=False) as handle:
            handle.write(meta.model_dump_json(indent=2))
            temp_meta = Path(handle.name)
        os.replace(temp_meta, output_dir / "metadata.json")
        temp_meta = None
        return GalleryIndex.load(output_dir)
    finally:
        adapter.close()
        for temp in (temp_path, temp_meta):
            if temp is not None:
                temp.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)

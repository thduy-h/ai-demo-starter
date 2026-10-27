from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from ..core.errors import InvalidInputError


def load_image(
    source: str | Path | bytes | Image.Image,
    *,
    max_bytes: int = 10_485_760,
    max_pixels: int = 20_000_000,
    allowed_formats: tuple[str, ...] = ("jpeg", "png", "webp"),
) -> Image.Image:
    try:
        if isinstance(source, Image.Image):
            if source.width * source.height > max_pixels:
                raise InvalidInputError("Image exceeds pixel limit")
            image = ImageOps.exif_transpose(source).convert("RGB")
        else:
            if isinstance(source, (str, Path)):
                p = Path(source)
                if p.stat().st_size > max_bytes:
                    raise InvalidInputError("Image exceeds upload size limit")
                data = p.read_bytes()
            else:
                data = source
                if len(data) > max_bytes:
                    raise InvalidInputError("Image exceeds upload size limit")
            with Image.open(io.BytesIO(data)) as opened:
                if (opened.format or "").lower() not in allowed_formats:
                    raise InvalidInputError("Unsupported image format")
                if opened.width * opened.height > max_pixels:
                    raise InvalidInputError("Image exceeds pixel limit")
                opened.verify()
            with Image.open(io.BytesIO(data)) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
        if image.width * image.height > max_pixels:
            raise InvalidInputError("Image exceeds pixel limit")
        return image
    except InvalidInputError:
        raise
    except Exception as exc:
        raise InvalidInputError(f"Invalid image: {exc}") from exc


def validate_image(
    source: str | Path | bytes | Image.Image,
    *,
    max_bytes: int = 10_485_760,
    max_pixels: int = 20_000_000,
) -> Image.Image:
    return load_image(source, max_bytes=max_bytes, max_pixels=max_pixels)


def annotate(
    image: Image.Image, boxes: list[tuple[float, float, float, float, str, float]]
) -> Image.Image:
    out = image.copy()
    draw = ImageDraw.Draw(out)
    for x1, y1, x2, y2, label, score in boxes:
        draw.rectangle((x1, y1, x2, y2), outline="red", width=max(2, round(min(image.size) / 300)))
        draw.text((x1, max(0, y1 - 14)), f"{label} {score:.2f}", fill="red")
    return out

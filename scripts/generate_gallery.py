"""Generate original synthetic gallery assets; no accuracy claim is attached."""

from pathlib import Path

from PIL import Image, ImageDraw

output = Path("examples/gallery")
output.mkdir(parents=True, exist_ok=True)
for name, color, shape in [
    ("red-circle", "red", "ellipse"),
    ("blue-square", "blue", "rectangle"),
    ("green-circle", "green", "ellipse"),
]:
    image = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    getattr(draw, shape)((32, 32, 224, 224), fill=color)
    image.save(output / f"{name}.png")

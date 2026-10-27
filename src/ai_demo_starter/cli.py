from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config.loader import default_config, load_config
from .core.errors import AIDemoError
from .core.lifecycle import LifecycleManager
from .core.registry import create_adapter

app = typer.Typer(help="CPU-first reusable AI demo toolkit", no_args_is_help=True)
models_app = typer.Typer(help="Explicitly acquire trusted upstream model weights")
gallery_app = typer.Typer(help="Build, update and inspect retrieval galleries")
app.add_typer(models_app, name="models")
app.add_typer(gallery_app, name="gallery")
console = Console()


def errors(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (AIDemoError, OSError) as exc:
            console.print(str(exc), style="red", markup=False)
            raise typer.Exit(2) from None

    return wrapped


@app.callback(invoke_without_command=True)
def main(version: Annotated[bool, typer.Option("--version", is_eager=True)] = False):
    if version:
        console.print(__version__)
        raise typer.Exit()


@app.command("list")
def list_demos():
    table = Table("Demo", "Adapter", "Requirements")
    table.add_row("detection", "torchvision_ssdlite", "detection extra + prepared COCO_V1 weights")
    table.add_row("speech", "faster_whisper", "speech extra + prepared local Whisper model")
    table.add_row(
        "retrieval", "torchvision_embedding", "retrieval extra + ImageNet weights + gallery"
    )
    console.print(table)


@app.command()
@errors
def validate_config(config: Path):
    c = load_config(config)
    console.print(f"Valid {c.demo.type} configuration", style="green")


@app.command("model-info")
@errors
def model_info(config: Annotated[Path, typer.Option("--config")]):
    c = load_config(config)
    adapter = create_adapter(c)
    console.print_json(adapter.metadata().model_dump_json())
    console.print("Static metadata; no weights initialized or downloaded.")


@app.command()
@errors
def run(demo: str, config: Annotated[Path | None, typer.Option("--config")] = None):
    c = load_config(config) if config else default_config(demo)
    if c.demo.type != demo:
        raise AIDemoError(f"Configuration task is {c.demo.type}, not {demo}")
    logging.basicConfig(level=c.logging.level)
    from .ui.factory import build_app

    try:
        application = build_app(c)
    except RuntimeError as exc:
        raise AIDemoError(str(exc)) from exc
    application.launch(
        server_name=c.server.host,
        server_port=c.server.port,
        share=c.server.share,
        max_file_size=c.input.max_upload_mb * 1024 * 1024,
        enable_monitoring=False,
        show_error=False,
    )


@models_app.command("prepare")
@errors
def prepare(config: Annotated[Path, typer.Option("--config")]):
    c = load_config(config)
    c.downloads.allow_download = True
    adapter = create_adapter(c)
    lifecycle = LifecycleManager(adapter)
    try:
        lifecycle.ensure_loaded()
        console.print(f"Prepared {adapter.metadata().identifier}", style="green")
        console.print_json(adapter.metadata().model_dump_json())
    finally:
        lifecycle.close()


@gallery_app.command("build")
@errors
def gallery_build(
    config: Annotated[Path, typer.Option("--config")],
    input: Annotated[Path, typer.Option("--input")],
    output: Annotated[Path, typer.Option("--output")],
):
    c = load_config(config)
    if c.demo.type != "retrieval":
        raise AIDemoError("Gallery build requires a retrieval configuration")
    from .retrieval.index import build_gallery

    index = build_gallery(input, output, create_adapter(c))
    console.print(f"Built {len(index.items)} items at {output}", style="green")


@gallery_app.command("info")
@errors
def gallery_info(index: Annotated[Path, typer.Option("--index")]):
    from .retrieval.index import GalleryIndex

    gallery = GalleryIndex.load(index)
    console.print_json(data=gallery.metadata)


if __name__ == "__main__":
    app()

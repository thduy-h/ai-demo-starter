from __future__ import annotations

import atexit
import logging
from typing import Any

from ..config.schemas import AppConfig
from ..core.errors import AIDemoError, InferenceError, ModelLoadError
from ..core.service import DemoService


def build_app(config: AppConfig) -> Any:
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError(
            "Install the demo extra, for example: uv sync --extra detection"
        ) from exc
    service = DemoService(config)
    atexit.register(service.close)

    def safe(callback):
        def wrapped(*args):
            try:
                return callback(*args)
            except (InferenceError, ModelLoadError) as exc:
                logging.getLogger(__name__).error("Model execution failed", exc_info=True)
                raise gr.Error("Model execution failed. Inspect the local server logs.") from exc
            except AIDemoError as exc:
                raise gr.Error(str(exc)) from exc

        return wrapped

    with gr.Blocks(
        title=config.demo.title, analytics_enabled=False, delete_cache=(300, 600)
    ) as app:
        gr.Markdown(f"# {config.demo.title}")
        if config.demo.type == "detection":
            image = gr.File(
                label="JPEG or PNG image", file_types=[".jpg", ".jpeg", ".png"], type="filepath"
            )
            threshold = gr.Slider(
                0,
                1,
                value=config.inference.confidence_threshold,
                step=0.01,
                label="Confidence threshold",
            )
            preview = gr.Image(label="Annotated image", format="png")
            artifact = gr.File(label="Download annotated PNG")
            details = gr.JSON(label="Detections, model and diagnostics")
            gr.Button("Run detection").click(
                safe(service.detection),
                [image, threshold],
                [preview, artifact, details],
                concurrency_limit=config.inference.max_concurrency,
                api_name="detect",
            )
        elif config.demo.type == "speech":
            audio = gr.Audio(
                sources=["microphone", "upload"],
                type="filepath",
                label="Record or upload WAV/FLAC",
                format="wav",
            )
            transcript = gr.Textbox(label="Transcript")
            details = gr.JSON(label="Language, model and diagnostics")
            gr.Button("Transcribe").click(
                safe(service.speech),
                audio,
                [transcript, details],
                concurrency_limit=config.inference.max_concurrency,
                api_name="transcribe",
            )
        else:
            query = gr.File(
                label="Query image", type="filepath", file_types=[".jpg", ".jpeg", ".png", ".webp"]
            )
            candidates = sorted(
                str(p.parent) for p in config.gallery_dir.parent.glob("*/metadata.json")
            )
            if str(config.gallery_dir) not in candidates:
                candidates.append(str(config.gallery_dir))
            gallery = gr.Dropdown(candidates, value=str(config.gallery_dir), label="Gallery")
            gr.Markdown("Build a gallery with the CLI first. Missing images require rebuilding it.")
            top = gr.Slider(1, 50, value=5, step=1, label="Top K")
            results = gr.Gallery(label="Ranked matches")
            details = gr.JSON(label="Index, model and diagnostics")
            gr.Button("Search").click(
                safe(service.retrieval),
                [query, top, gallery],
                [results, details],
                concurrency_limit=config.inference.max_concurrency,
                api_name="search",
            )
    app.queue(max_size=16, default_concurrency_limit=config.inference.max_concurrency)
    return app

from pathlib import Path

import pytest

from ai_demo_starter.config.loader import load_config
from ai_demo_starter.ui.factory import build_app


@pytest.mark.parametrize("task", ["detection", "speech", "retrieval"])
def test_construct_ui(task):
    pytest.importorskip("gradio", reason="install UI extra to check components")
    config = load_config(f"configs/{task}.yaml")
    application = build_app(config)
    assert application.config["title"] == config.demo.title
    assert not config.server.share
    assert config.server.host == "127.0.0.1"
    assert application.enable_queue
    application.close()


@pytest.mark.real_model
@pytest.mark.ui_live
@pytest.mark.parametrize("task", ["detection", "speech", "retrieval"])
def test_live_upload_callback(task, tmp_path):
    from gradio_client import Client, handle_file

    from ai_demo_starter.core.registry import create_adapter
    from ai_demo_starter.retrieval.index import build_gallery

    fixtures = Path(__file__).parent / "fixtures"
    config = load_config(f"configs/{task}.yaml")
    config.downloads.cache_dir = Path(".local/models").resolve()
    if task == "retrieval":
        source = tmp_path / "source"
        source.mkdir()
        (source / "astronaut.png").write_bytes((fixtures / "astronaut.png").read_bytes())
        config.gallery_dir = tmp_path / "gallery"
        build_gallery(source, config.gallery_dir, create_adapter(config))
    application = build_app(config)
    try:
        _, url, _ = application.launch(
            server_name="127.0.0.1",
            share=False,
            prevent_thread_lock=True,
            max_file_size=config.input.max_upload_mb * 1024 * 1024,
            enable_monitoring=False,
            show_error=False,
            quiet=True,
        )
        client = Client(url, verbose=False)
        if task == "detection":
            preview, download, result = client.predict(
                handle_file(str(fixtures / "astronaut.png")), 0.5, api_name="/detect"
            )
            assert Path(preview).is_file() and Path(download).is_file()
            assert result["detections"]
            invalid = tmp_path / "invalid.png"
            invalid.write_text("not an image")
            with pytest.raises(Exception, match="Invalid image"):
                client.predict(handle_file(str(invalid)), 0.5, api_name="/detect")
        elif task == "speech":
            transcript, result = client.predict(
                handle_file(str(fixtures / "jfk.wav")), api_name="/transcribe"
            )
            assert "country" in transcript.lower()
            assert result["duration_s"] > 0
        else:
            gallery, result = client.predict(
                handle_file(str(fixtures / "astronaut.png")),
                5,
                str(config.gallery_dir),
                api_name="/search",
            )
            assert gallery and result["matches"][0]["rank"] == 1
    finally:
        application.close()

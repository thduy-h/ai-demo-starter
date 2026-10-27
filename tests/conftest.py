import pytest


def pytest_addoption(parser):
    parser.addoption("--real-models", action="store_true", help="Run prepared CPU models offline")
    parser.addoption("--ui-live", action="store_true", help="Launch Gradio and call its HTTP API")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "real_model" in item.keywords and not config.getoption("--real-models"):
            item.add_marker(pytest.mark.skip(reason="requires --real-models and prepared weights"))
        if "ui_live" in item.keywords and not config.getoption("--ui-live"):
            item.add_marker(pytest.mark.skip(reason="requires --ui-live and loopback sockets"))

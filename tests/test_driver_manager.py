import json
import os
from pathlib import Path

import certifi
import pytest
from selenium.common.exceptions import WebDriverException

from data49 import _driver_manager, web


def test_driver_download_uses_updated_bundle_only_in_child(monkeypatch):
    observed = {}
    original_ca = os.environ.get("SSL_CERT_FILE")
    monkeypatch.setattr(
        _driver_manager, "_manager_binary", lambda: Path("verified-manager")
    )

    def run(args, **kwargs):
        observed.update(kwargs)
        assert args[0] == "verified-manager"
        assert "--avoid-stats" in args
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps(
                    {
                        "result": {
                            "driver_path": "/trusted/chromedriver",
                            "browser_path": "/trusted/chrome",
                        }
                    }
                ),
            },
        )()

    monkeypatch.setattr(_driver_manager.subprocess, "run", run)
    paths = _driver_manager.driver_paths("chrome")
    assert paths["driver_path"] == "/trusted/chromedriver"
    assert observed["env"]["SSL_CERT_FILE"] == certifi.where()
    assert os.environ.get("SSL_CERT_FILE") == original_ca


def test_failed_driver_download_never_returns_an_executable(monkeypatch):
    monkeypatch.setattr(
        _driver_manager, "_manager_binary", lambda: Path("verified-manager")
    )
    monkeypatch.setattr(
        _driver_manager.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "Result",
            (),
            {
                "returncode": 65,
                "stdout": json.dumps(
                    {
                        "result": {
                            "message": "invalid peer certificate",
                            "driver_path": "/untrusted/driver",
                        }
                    }
                ),
            },
        )(),
    )
    with pytest.raises(WebDriverException, match="invalid peer certificate"):
        _driver_manager.driver_paths("chrome")


def test_unsupported_platform_does_not_use_upstream_manager(monkeypatch):
    monkeypatch.setattr(_driver_manager.sys, "platform", "unsupported")
    with pytest.raises(RuntimeError, match="no verified Selenium Manager"):
        _driver_manager._manager_binary()


def test_browser_uses_explicit_verified_driver(monkeypatch):
    calls = []
    monkeypatch.setattr(
        _driver_manager,
        "driver_paths",
        lambda *args: {
            "driver_path": "/trusted/chromedriver",
            "browser_path": "/trusted/chrome",
        },
    )

    def chrome(**kwargs):
        calls.append(kwargs)
        return type("Browser", (), {"close": lambda self: None})()

    monkeypatch.setattr(web.drivers, "Chrome", chrome)
    factory = web._try_to_get(web.BrowserType.CHROME, True, None)
    assert factory is not None
    assert calls[0]["service"].path == "/trusted/chromedriver"
    assert calls[0]["options"].binary_location == "/trusted/chrome"

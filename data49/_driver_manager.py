"""Resolve browser drivers with Data49's certificate-verifying downloader."""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict

import certifi
from selenium.common.exceptions import WebDriverException

_CACHE_DIRECTORY = Path.home() / ".cache" / "data49" / "selenium-verified-20261021"


def _manager_binary() -> Path:
    architecture = platform.machine().lower()
    if architecture == "aarch64":
        architecture = "arm64"
    elif architecture in {"amd64", "x86_64"}:
        architecture = "x86_64"
    directory = Path(__file__).parent / "_selenium" / f"{sys.platform}-{architecture}"
    binary = directory / (
        "selenium-manager.exe" if sys.platform == "win32" else "selenium-manager"
    )
    if not binary.is_file():
        raise RuntimeError(
            "Data49 has no verified Selenium Manager for "
            f"{sys.platform}/{architecture}. Supply Browser(get_driver=...) with an "
            "explicit Selenium Service(executable_path=...) for a trusted local driver."
        )
    return binary


def driver_paths(
    browser: str,
    browser_path: str = "",
    *,
    browser_version: str = "",
    force_browser_download: bool = False,
) -> Dict[str, str]:
    """Find/download a driver without running Selenium's unverified downloader."""
    args = [
        str(_manager_binary()),
        "--browser",
        browser,
        "--output",
        "json",
        "--avoid-stats",
        "--trace",
        "--skip-driver-in-path",
        "--cache-path",
        str(_CACHE_DIRECTORY),
    ]
    if browser_path:
        args += ["--browser-path", browser_path]
    if browser_version:
        args += ["--browser-version", browser_version]
    if force_browser_download:
        args.append("--force-browser-download")
    environment = os.environ.copy()
    environment["SSL_CERT_FILE"] = certifi.where()
    completed = subprocess.run(
        args, capture_output=True, text=True, env=environment, check=False
    )
    try:
        output = json.loads(completed.stdout)
        result = output["result"]
    except (ValueError, KeyError, TypeError) as error:
        raise WebDriverException(
            "Verified Selenium Manager returned an invalid response"
        ) from error
    if completed.returncode or not result.get("driver_path"):
        raise WebDriverException(
            result.get("message", "Verified driver discovery failed")
        )
    return result

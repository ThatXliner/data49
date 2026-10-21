# Data49

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![codecov](https://codecov.io/gh/ThatXliner/data49/branch/main/graph/badge.svg)](https://codecov.io/gh/ThatXliner/data49)

[![CI](https://github.com/ThatXliner/data49/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ThatXliner/data49/actions/workflows/ci.yml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/data49)](https://pypi.org/project/data49)
[![PyPI](https://img.shields.io/pypi/v/data49)](https://pypi.org/project/data49)
[![PyPI - License](https://img.shields.io/pypi/l/data49)](#license)

> A gold rush-themed data mining library

WIP. Expect frequent breaking changes

<!-- It is split into the following sections:

 - **General utilities** for stuff like functional programming, utility functions, parallel jobs, caching to a file, etc. Wraps `joblib`. Found in the default namespace (`*`)
  - **Web-related utilities** wrapping web scraping with Beautiful Soup and requests or browser automation with Selenium. Found in the `web` namespace
  - **Logging** Logging made super easy. Found in the `log` namespace

Currently, only the web-related utilities are implemented

## Features

 - Simple API w/automatic logging
 - Fully type hinted
 - Typo-resistant


## FAQ

### Why the name?

This library's name was inspired from the 18**49** gold rush. In the modern world, data is gold. -->

## Installation

The patched 0.5.1 wheel is distributed on [GitHub Releases](https://github.com/ThatXliner/data49/releases/tag/v0.5.1). PyPI publication requires refreshed publishing credentials, so install this security release directly:

```bash
$ pip install https://github.com/ThatXliner/data49/releases/download/v0.5.1/data49-0.5.1-py3-none-any.whl
```

Or, if you're using [Poetry](https://python-poetry.org)

```bash
$ poetry add https://github.com/ThatXliner/data49/releases/download/v0.5.1/data49-0.5.1-py3-none-any.whl
```

## License

Copyright © 2021, Bryan Hu

This project is licensed under the [GNU GPL v3+](https://github.com/ThatXliner/data49/blob/main/LICENSE.txt).

In short, this means you can do anything with it (distribute, modify, sell) but if you were to publish your changes, you must make the source code and build instructions readily available.

If you are a company using this project and want an exception, email me at [thatxliner@gmail.com](mailto:thatxliner@gmail.com) and we can discuss.

## Python support

Version 0.5.0 requires Python 3.10 or later. This release upgrades Requests and urllib3 to patched releases whose supported Python versions start at 3.10.

## Secure browser driver downloads

Version 0.5.1 supplies a certificate-verifying Selenium Manager for automatic Chrome and Firefox driver downloads. It trusts the installed certifi bundle and uses a fresh cache at `~/.cache/data49/selenium-verified-20261021`. It supplies Selenium an explicit driver path, so Selenium's bundled downloader is bypassed. The bundled helper source patch, licenses, build instructions and checksums are under `vendor/selenium-manager`.

If your platform has no verified helper, automatic management raises an error. You can use a trusted local driver explicitly:

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from data49.web import Browser

with Browser(
    "https://example.com",
    get_driver=lambda: webdriver.Chrome(
        service=Service(executable_path="/path/to/trusted/chromedriver")
    ),
):
    pass
```

A custom `get_driver` is responsible for its own driver and browser trust configuration. Safari uses its system-provided driver.

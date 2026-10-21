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

## Browser certificate validation

Version 0.5.2 also checks the browser that opens web pages. By default, Data49 downloads and caches the official Chrome for Testing 158.0.8115.0 build through its certificate-verifying Manager. This is currently a prerelease build with the updated Chrome Root Store. Data49 uses that isolated runtime instead of your installed system browser and does not redistribute Google browser binaries in its package. Stable Chrome 156 and a fresh Firefox 158.0.1 profile did not satisfy the browser TLS sweep.

To select your own current browser, download an official build from [Google Chrome Canary](https://www.google.com/chrome/canary/) or the [Chrome for Testing dashboard](https://googlechromelabs.github.io/chrome-for-testing/). It must be version 158.0.8115.0 or later and pass the same trust checks. Set `SE_CHROME_PATH` to the actual executable. For example, on macOS:

```sh
export SE_CHROME_PATH="/path/to/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
```

Use the normal Data49 browser API:

```python
from data49.web import Browser

with Browser("https://example.com") as page:
    print(page.driver.title)
```

Every returned driver must report `acceptInsecureCerts=False`. Data49 disables platform-added trust in Chrome's fresh temporary profile, then confirms that setting through the browser's own certificate manager. Enterprise and profile certificate additions must be absent, and the Chrome Root Store must omit the four affected roots. Missing, malformed, or overridden configuration fails closed with `BrowserSecurityError` before your application URL opens. This check uses internal browser pages and does not contact the sweep test hosts. Data49 does not modify your main browser profile or system trust settings. Applications that need additional private trust anchors must use the explicit custom-driver bypass below.

The automatic path currently supports Chrome only. The verified Manager supports macOS ARM64 and x86-64, Linux ARM64 and x86-64, and Windows x86-64. Browser behavior was exercised on macOS ARM64; CI runs the same browser probe on its desktop runner platforms. A missing helper, older browser, unsupported engine, or unavailable certificate interface fails closed. Only window size, language, headless mode, and `--start-maximized` are accepted as additional browser arguments.

On Linux, Chrome for Testing also requires a working browser sandbox. Ubuntu's AppArmor rules can prevent a downloaded browser from creating user namespaces. Follow [Chromium's supported sandbox setup](https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md), which includes using an installed Chrome setuid sandbox through `CHROME_DEVEL_SANDBOX`. Data49 does not disable the sandbox.

To reproduce the certificate checks against both compromised chains and example.com:

```sh
python tools/verify_browser_tls.py --fresh-cache --output browser-tls.json
```

The probe saves screenshots and an incremental JSON report. `--fresh-cache` downloads into a new test-only Manager cache and requires `SE_CHROME_PATH` to be unset, so the normal automatic runtime path is exercised. Omit that option to test an explicit browser. Both bad hosts must show certificate-error interstitials. DNS failures and navigation timeouts are inconclusive and cause the probe to fail.

### Custom drivers bypass browser safeguards

If you supply your own `get_driver`, you must set `allow_unverified_driver=True`. This explicitly bypasses Data49's browser certificate checks. You are responsible for driver provenance, browser updates, certificate validation, and trust settings. For example:

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from data49.web import Browser

with Browser(
    "https://example.com",
    get_driver=lambda: webdriver.Chrome(
        service=Service(executable_path="/path/to/trusted/chromedriver")
    ),
    allow_unverified_driver=True,
):
    pass
```

This opt-in also applies to custom Firefox and Safari drivers. Data49 does not use this bypass in its normal browser path.

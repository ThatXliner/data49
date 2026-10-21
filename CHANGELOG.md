# Changelog

## 0.5.2

- Automatically fetch and cache the official prerelease Chrome for Testing 158.0.8115.0 build through the verified Manager. Block navigation unless that browser passes certificate trust inspection. An explicit `SE_CHROME_PATH` must select Chrome 158.0.8115.0 or later and pass the same checks.
- Enforce `acceptInsecureCerts=False`, disable platform-added trust in each temporary profile, and require empty enterprise and profile trust additions. Check that the Chrome Root Store omits the four affected roots before returning each driver. Missing, malformed, or overridden settings fail closed. Firefox, Safari, custom profiles, and unverified command-line switches are blocked on the automatic path.
- Require `allow_unverified_driver=True` to opt out of those checks with a custom `get_driver`. Reuse the verified Selenium Manager binaries and certifi floor from 0.5.1. Extend the private resolver's arguments to request the exact browser version without selecting an older system browser.
- Add a reproducible browser TLS probe that requires certificate-error interstitials for both compromised chains and a successful trusted control. DNS and navigation timeouts remain inconclusive.

## 0.5.1

- Restore certificate verification for automatic Selenium driver downloads. Data49 invokes its patched, verified Manager directly with the current certifi CA bundle, then supplies Selenium an explicit driver path.
- Use a fresh driver cache rather than reuse downloads made by the previous downloader. Platforms without a verified helper fail with an explicit error and support a custom `Browser(get_driver=...)` using a trusted local driver.
- Require Selenium 4.51.0 or later. Python 3.10 remains the minimum supported Python version.

## 0.5.0

- Update Requests, urllib3, Selenium and certifi for the October 2026 HTTP and CA security fixes.
- Raise the minimum Python version to 3.10.

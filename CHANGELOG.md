# Changelog

## 0.5.1

- Restore certificate verification for automatic Selenium driver downloads. Data49 invokes its patched, verified Manager directly with the current certifi CA bundle, then supplies Selenium an explicit driver path.
- Use a fresh driver cache rather than reuse downloads made by the previous downloader. Platforms without a verified helper fail with an explicit error and support a custom `Browser(get_driver=...)` using a trusted local driver.
- Require Selenium 4.51.0 or later. Python 3.10 remains the minimum supported Python version.

## 0.5.0

- Update Requests, urllib3, Selenium and certifi for the October 2026 HTTP and CA security fixes.
- Raise the minimum Python version to 3.10.

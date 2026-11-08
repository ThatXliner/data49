# Verified Selenium Manager

Data49 0.5.1 uses a patched Selenium Manager instead of Selenium's bundled downloader. The upstream 4.51.0 HTTP client disables certificate verification; this build restores verification, updates the Rust certificate dependencies, and accepts an explicit CA bundle through `SSL_CERT_FILE`. When that variable is set, its certificates are the only trusted roots. Invalid or empty bundles fail closed.

Upstream source: https://github.com/SeleniumHQ/selenium/tree/35c5fab4a58fa5878edb255eb7747b04ca51a015

Apply `security.patch` to that exact commit, then build with Rust and the checked-in Cargo lockfile:

```sh
git clone https://github.com/SeleniumHQ/selenium.git selenium-source
git -C selenium-source checkout 35c5fab4a58fa5878edb255eb7747b04ca51a015
git -C selenium-source apply ../security.patch
cargo build --manifest-path selenium-source/rust/Cargo.toml --release --locked
```

On Windows the executable has an `.exe` suffix. Native Windows and Intel macOS builds are produced by `.github/workflows/selenium-manager.yml`; ARM macOS and Linux builds have separate build evidence in `manifest.json`. The manifest records the SHA-256 of each bundled executable. Upstream LICENSE and NOTICE are included here.

`security.patch` is the patch used by the GitHub matrix. `security-native.patch` records the equivalent local native-build patch; the differences are import placement and formatting. The manifest names the exact patch for each executable.

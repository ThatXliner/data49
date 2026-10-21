"""Exercise the native downloader against public compromised-chain test sites."""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

import certifi


def verify(binary, directory):
    directory.mkdir(parents=True, exist_ok=True)
    browser = directory / ("browser.cmd" if sys.platform == "win32" else "browser")
    browser.write_text(
        "@echo off\necho Google Chrome 153.0.8059.85\n"
        if sys.platform == "win32"
        else "#!/bin/sh\necho Google Chrome 153.0.8059.85\n"
    )
    browser.chmod(0o755)
    results = []
    targets = [
        ("direct", "https://dv-g3b-emudhra.we-have-a-problem.com/", True),
        ("cross_signed", "https://dv-g3b-aaa-emudhra.we-have-a-problem.com/", True),
        ("control", "https://example.com/", False),
    ]
    environment = os.environ.copy()
    environment["SSL_CERT_FILE"] = certifi.where()
    for name, url, reject in targets:
        attempts = []
        for attempt in range(1, 9):
            cache = directory / f"{name}-{attempt}"
            command = [
                str(binary.resolve()),
                "--driver",
                "chromedriver",
                "--driver-version",
                "153.0.8059.85",
                "--browser-version",
                "153",
                "--driver-mirror-url",
                url + "#",
                "--browser-path",
                str(browser.resolve()),
                "--avoid-browser-download",
                "--avoid-stats",
                "--skip-driver-in-path",
                "--timeout",
                "15",
                "--cache-path",
                str(cache.resolve()),
                "--trace",
                "--output",
                "json",
            ]
            try:
                process = subprocess.run(
                    command, capture_output=True, text=True, env=environment, timeout=25
                )
                output = process.stdout + "\n" + process.stderr
                certificate_error = any(
                    term in output.lower()
                    for term in [
                        "invalid peer certificate",
                        "unknownissuer",
                        "certificate verify",
                        "certificate revoked",
                        "certificaterevoked",
                        "certificate is revoked",
                    ]
                )
                response_obtained = any(
                    term in output
                    for term in [
                        "Error parsing JSON from URL",
                        "File downloaded to temporal folder",
                        "Unsuccessful response (",
                    ]
                )
                passed = (
                    certificate_error
                    if reject
                    else response_obtained and not certificate_error
                )
                observation = {
                    "attempt": attempt,
                    "returncode": process.returncode,
                    "certificate_error": certificate_error,
                    "response_obtained": response_obtained,
                    "passed": passed,
                }
            except subprocess.TimeoutExpired as error:
                output = str(error)
                passed = False
                observation = {"attempt": attempt, "timeout": True, "passed": False}
            (directory / f"{name}-{attempt}.log").write_text(output)
            attempts.append(observation)
            if passed:
                break
            time.sleep(1)
        results.append(
            {
                "name": name,
                "url": url,
                "expected_certificate_rejection": reject,
                "passed": passed,
                "attempts": attempts,
            }
        )
    report = {
        "binary": str(binary.resolve()),
        "certifi": certifi.__version__,
        "ca_bundle": certifi.where(),
        "results": results,
        "passed": all(result["passed"] for result in results),
    }
    (directory / "tls-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    arguments = parser.parse_args()
    raise SystemExit(0 if verify(arguments.binary, arguments.output) else 1)

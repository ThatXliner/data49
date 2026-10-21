"""Exercise Data49's normal browser factory without TLS bypasses.

Select an official current Chrome executable with SE_CHROME_PATH, then run:
    python tools/verify_browser_tls.py --output browser-tls.json
"""

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile

from selenium.common.exceptions import WebDriverException

from data49 import _driver_manager
from data49.web import BrowserSecurityError, get_browser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--fresh-cache", action="store_true")
    args = parser.parse_args()
    report = {"status": "starting", "results": [], "passed": False}
    if args.fresh_cache:
        if os.environ.get("SE_CHROME_PATH"):
            parser.error("--fresh-cache requires SE_CHROME_PATH to be unset")
        _driver_manager._CACHE_DIRECTORY = pathlib.Path(
            tempfile.mkdtemp(prefix="data49-browser-proof-cache-")
        )
        report["fresh_manager_cache"] = str(_driver_manager._CACHE_DIRECTORY)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    save()
    try:
        factory = get_browser()
        factory.keywords["options"].set_capability(
            "goog:loggingPrefs", {"performance": "ALL"}
        )
        driver = factory()
    except (BrowserSecurityError, RuntimeError, WebDriverException) as error:
        report.update(status="BLOCKED_BEFORE_APPLICATION_NAVIGATION", error=str(error))
        save()
        print(json.dumps(report, indent=2))
        return 2
    driver.set_page_load_timeout(120)
    report.update(
        status="running",
        browser_version=driver.capabilities["browserVersion"],
        accept_insecure_certs=driver.capabilities.get("acceptInsecureCerts"),
        binary=factory.keywords["options"].binary_location,
    )
    driver.get("chrome://certificate-manager/")
    report["effective_trust_metadata"] = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        import('chrome://certificate-manager/certificates_browser_proxy.js')
          .then(proxy => proxy.CertificatesBrowserProxy.getInstance().handler
            .getCertManagementMetadata()).then(done)
          .catch(error => done({error:String(error)}));
        """
    )
    try:
        targets = [
            ("primary", "https://emudhra.we-have-a-problem.com/", False),
            ("direct", "https://dv-g3b-emudhra.we-have-a-problem.com/", True),
            ("aaa", "https://dv-g3b-aaa-emudhra.we-have-a-problem.com/", True),
            ("control", "https://example.com/", False),
        ]
        for name, url, reject in targets:
            driver.get("about:blank")
            driver.get_log("performance")
            error = ""
            try:
                driver.get(url)
            except WebDriverException as exception:
                error = str(exception).split("Stacktrace:")[0]
            events = [
                json.loads(row["message"])["message"]
                for row in driver.get_log("performance")
            ]
            failures = [
                row["params"].get("errorText", "")
                for row in events
                if row["method"] == "Network.loadingFailed"
            ]
            responses = [
                row["params"]["response"]["status"]
                for row in events
                if row["method"] == "Network.responseReceived"
                and row["params"].get("type") == "Document"
                and row["params"]["response"]["url"] == url
            ]
            source = driver.page_source
            codes = sorted(
                set(
                    re.findall(
                        r"(?:net::)?ERR_CERT_[A-Z_]+",
                        source + error + " ".join(failures),
                    )
                )
            )
            interstitial = bool(codes) and (
                "interstitial-wrapper" in source or driver.title == "Privacy error"
            )
            outcome = (
                "CERTIFICATE_REJECTED"
                if interstitial
                else "ACCEPTED"
                if responses and not error
                else "INCONCLUSIVE"
            )
            passed = outcome == ("CERTIFICATE_REJECTED" if reject else "ACCEPTED")
            if name == "control":
                passed = passed and driver.title == "Example Domain"
            report["results"].append(
                {
                    "name": name,
                    "url": url,
                    "outcome": outcome,
                    "passed": passed,
                    "certificate_error_codes": codes,
                    "certificate_interstitial": interstitial,
                    "navigation_error": error,
                    "network_errors": failures,
                    "document_response_statuses": responses,
                    "title": driver.title,
                }
            )
            driver.save_screenshot(
                str(args.output.with_name(args.output.stem + "-" + name + ".png"))
            )
            save()
        report["passed"] = (
            all(row["passed"] for row in report["results"])
            and report["accept_insecure_certs"] is False
        )
        report["status"] = "passed" if report["passed"] else "failed_or_inconclusive"
        save()
    finally:
        driver.quit()
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

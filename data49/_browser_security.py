"""Reject browser configurations whose eMudhra distrust cannot be established."""

import re

MINIMUM_CHROME = (158, 0, 8115, 0)
PINNED_CHROME_VERSION = ".".join(map(str, MINIMUM_CHROME))
PLATFORM_TRUST_PREF = "certificates.ca_platform_integration_enabled"
AFFECTED_ROOTS = frozenset(
    {
        "7DD78D5F4F13459A83DFF9ABBBA62EDBAF6F2D102BF257FD712F4D9F2746ED8D",
        "F2EDAAFF3D9B701FB4D14C9F285F8C0BAD90FC3BCC1FA07D47F4718EDABA34A5",
        "D7A7A0FB5D7E2731D771E9484EBCDEF71D5F0C3E0A2948782BC83EE0EA699EF4",
        "86A1ECBA089C4A8D3BBE2734C612BA341D813E043CF9E8A862CD5C57A36BBE6B",
    },
)


class BrowserSecurityError(RuntimeError):
    """The automatic browser path cannot establish safe certificate handling."""


def require_safe_arguments(arguments):
    for argument in arguments or ():
        if not isinstance(argument, str) or not (
            re.fullmatch(r"--window-size=[1-9][0-9]*,[1-9][0-9]*", argument)
            or re.fullmatch(r"--lang=[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*", argument)
            or argument in {"--headless", "--headless=new", "--start-maximized"}
        ):
            msg = (
                "Unverified browser argument configuration. Automatic browsers accept "
                "only window size, language, headless, and start-maximized arguments."
            )
            raise BrowserSecurityError(msg)


def _fingerprints(records):
    if not isinstance(records, list):
        msg = "Browser trust inspection returned no root list"
        raise BrowserSecurityError(msg)
    fingerprints = set()
    for record in records:
        digest = record.get("sha256hashHex") if isinstance(record, dict) else None
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            msg = "Browser trust inspection returned an invalid root"
            raise BrowserSecurityError(msg)
        fingerprints.add(digest.upper())
    return fingerprints


def _require_safe_capabilities(capabilities):
    version = capabilities.get("browserVersion", "")
    if (
        capabilities.get("browserName") != "chrome"
        or not isinstance(version, str)
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", version)
        or tuple(map(int, version.split("."))) < MINIMUM_CHROME
    ):
        msg = (
            "Data49 requires Chrome 158.0.8115.0 or later with updated root data. "
            "Use an official Chrome Canary or Chrome for Testing build and select "
            "its executable with SE_CHROME_PATH. Older browsers are blocked before "
            "application navigation."
        )
        raise BrowserSecurityError(msg)
    if capabilities.get("acceptInsecureCerts") is not False:
        msg = "Browser TLS certificate validation is not enforced"
        raise BrowserSecurityError(msg)


def require_safe_chrome(driver):
    _require_safe_capabilities(driver.capabilities)
    driver.set_script_timeout(20)
    driver.get("chrome://certificate-manager/")
    inspection = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        Promise.all([
          import('chrome://certificate-manager/certificates_browser_proxy.js'),
          import('chrome://certificate-manager/certificate_manager.mojom-webui.js')
        ]).then(async ([proxy, mojom]) => {
          const handler = proxy.CertificatesBrowserProxy.getInstance().handler;
          const {metadata} = await handler.getCertManagementMetadata();
          const names = {
            roots: 'kChromeRootStore', enterprise: 'kEnterpriseTrustedCerts',
            user: 'kUserTrustedCerts'
          };
          const result = {metadata};
          for (const [key, name] of Object.entries(names)) {
            const source = mojom.CertificateSource[name];
            if (typeof source !== 'number' || source < 1) {
              throw new Error('Unsupported certificate source');
            }
            result[key] = (await handler.getCertificates(source)).certs;
          }
          done(result);
        }).catch(error => done({error: String(error)}));
        """,
    )
    if not isinstance(inspection, dict) or set(inspection) != {
        "roots",
        "enterprise",
        "user",
        "metadata",
    }:
        msg = "Browser trust inspection is unavailable"
        raise BrowserSecurityError(msg)
    roots = _fingerprints(inspection["roots"])
    if not roots:
        msg = "Browser root store is empty or unavailable"
        raise BrowserSecurityError(msg)
    metadata = inspection["metadata"]
    if (
        not isinstance(metadata, dict)
        or metadata.get("includeSystemTrustStore") is not False
    ):
        msg = "Browser platform trust integration must be disabled"
        raise BrowserSecurityError(msg)
    for name in ("numPolicyCerts", "numUserCerts"):
        count = metadata.get(name)
        if type(count) is not int or count != 0:
            msg = "Browser has additional or unverified certificate trust configuration"
            raise BrowserSecurityError(msg)
    for name in ("enterprise", "user"):
        if _fingerprints(inspection[name]):
            msg = "Browser has additional trusted roots or intermediates"
            raise BrowserSecurityError(msg)
    if roots & AFFECTED_ROOTS:
        msg = "Browser still trusts an affected eMudhra chain root"
        raise BrowserSecurityError(msg)
    driver.get("about:blank")

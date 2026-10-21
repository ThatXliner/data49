import pytest

from data49 import web


class Driver:
    def __init__(self, version="158.0.8115.0", insecure=False, inspection=None):
        self.capabilities = {
            "browserName": "chrome",
            "browserVersion": version,
            "acceptInsecureCerts": insecure,
        }
        self.urls = []
        self.closed = False
        self.inspection = inspection or {
            "roots": [{"sha256hashHex": "0" * 64}],
            "enterprise": [],
            "user": [],
            "metadata": {
                "includeSystemTrustStore": False,
                "numPolicyCerts": 0,
                "numUserCerts": 0,
            },
        }

    def get(self, url):
        self.urls.append(url)

    def execute_async_script(self, script):
        return self.inspection

    def set_script_timeout(self, seconds):
        pass

    def close(self):
        self.closed = True

    def quit(self):
        self.closed = True


@pytest.fixture
def install(monkeypatch):
    web.__get_browser_cache.clear()
    monkeypatch.setattr(
        web._driver_manager,
        "driver_paths",
        lambda *args, **kwargs: {
            "driver_path": "/trusted/driver",
            "browser_path": "/trusted/chrome",
        },
    )

    def configure(*drivers):
        queue = iter(drivers)
        monkeypatch.setattr(web.drivers, "Chrome", lambda **kwargs: next(queue))

    yield configure
    web.__get_browser_cache.clear()


@pytest.mark.parametrize(
    "version", ["155.0.8059.85", "158.0.8106.0", "", "unknown", "158.0.8115.0beta"]
)
def test_old_or_unknown_browser_stops_before_navigation(install, version):
    driver = Driver(version=version)
    install(driver)
    with pytest.raises(RuntimeError, match="Chrome|browser"):
        web.get_browser()
    assert driver.closed
    assert driver.urls == []


def test_every_factory_call_checks_tls_capability(install):
    discovery, insecure = Driver(), Driver(insecure=True)
    install(discovery, insecure)
    factory = web.get_browser()
    with pytest.raises(RuntimeError, match="certificate|TLS"):
        factory()
    assert insecure.closed
    assert insecure.urls == []


def test_platform_preference_cannot_be_reenabled_on_cached_factory(install):
    install(Driver())
    factory = web.get_browser()
    factory.keywords["options"].add_experimental_option(
        "prefs", {"certificates.ca_platform_integration_enabled": True}
    )
    with pytest.raises(RuntimeError, match="platform trust"):
        factory()


def test_default_browser_requests_the_exact_isolated_runtime(install, monkeypatch):
    calls = []
    monkeypatch.delenv("SE_CHROME_PATH", raising=False)
    install(Driver())

    def resolve(*args, **kwargs):
        calls.append((args, kwargs))
        return {"driver_path": "/trusted/driver", "browser_path": "/trusted/pinned"}

    monkeypatch.setattr(web._driver_manager, "driver_paths", resolve)
    web.get_browser()
    assert calls == [
        (
            ("chrome",),
            {"browser_version": "158.0.8115.0", "force_browser_download": True},
        )
    ]


def test_explicit_browser_selection_keeps_security_checks(install, monkeypatch):
    monkeypatch.setenv("SE_CHROME_PATH", "/chosen/old-chrome")
    install(Driver(version="155.0.8059.85"))
    calls = []

    def resolve(*args, **kwargs):
        calls.append((args, kwargs))
        return {"driver_path": "/trusted/driver", "browser_path": "/chosen/old-chrome"}

    monkeypatch.setattr(web._driver_manager, "driver_paths", resolve)
    with pytest.raises(RuntimeError, match="Chrome"):
        web.get_browser()
    assert calls == [(("chrome", "/chosen/old-chrome"), {})]


@pytest.mark.parametrize("source", ["roots", "enterprise", "user"])
def test_affected_trust_anchor_stops_before_application_navigation(install, source):
    driver = Driver()
    driver.inspection[source].append(
        {
            "sha256hashHex": "86A1ECBA089C4A8D3BBE2734C612BA341D813E043CF9E8A862CD5C57A36BBE6B"
        }
    )
    install(driver)
    with pytest.raises(RuntimeError, match="root|trust"):
        web.get_browser()
    assert driver.closed
    assert all(url.startswith("chrome://") for url in driver.urls)


@pytest.mark.parametrize("source", ["enterprise", "user"])
def test_any_added_trusted_root_or_intermediate_is_blocked(install, source):
    driver = Driver()
    driver.inspection[source].append({"sha256hashHex": "F" * 64})
    install(driver)
    with pytest.raises(RuntimeError, match="additional trusted"):
        web.get_browser()
    assert driver.closed
    assert all(url.startswith("chrome://") for url in driver.urls)


@pytest.mark.parametrize("integration", [True, None, "false"])
def test_platform_trust_override_is_disabled_in_effective_browser_config(
    install, integration
):
    driver = Driver()
    driver.inspection["metadata"]["includeSystemTrustStore"] = integration
    install(driver)
    with pytest.raises(RuntimeError, match="platform trust"):
        web.get_browser()
    assert driver.closed


@pytest.mark.parametrize("field", ["numPolicyCerts", "numUserCerts"])
@pytest.mark.parametrize("value", [1, None, False])
def test_additional_or_unknown_certificate_configuration_is_blocked(
    install, field, value
):
    driver = Driver()
    driver.inspection["metadata"][field] = value
    install(driver)
    with pytest.raises(RuntimeError, match="additional|unverified"):
        web.get_browser()
    assert driver.closed


@pytest.mark.parametrize(
    "inspection",
    [{"error": "unsupported"}, {"roots": []}, {"roots": [{"sha256hashHex": "bad"}]}],
)
def test_unavailable_trust_inspection_fails_closed(install, inspection):
    driver = Driver(inspection=inspection)
    install(driver)
    with pytest.raises(RuntimeError, match="trust|root"):
        web.get_browser()
    assert driver.closed


@pytest.mark.parametrize(
    "argument",
    [
        "--ignore-certificate-errors",
        "--user-data-dir=/user/profile",
        "--disable-features=ChromeRootStoreUsed",
    ],
)
def test_unverified_browser_arguments_fail_before_launch(install, argument):
    install()
    with pytest.raises(RuntimeError, match="argument|configuration"):
        web.get_browser(arguments=[argument])


@pytest.mark.parametrize("browser", [web.BrowserType.FIREFOX, web.BrowserType.SAFARI])
def test_unverified_engine_fails_closed(browser):
    with pytest.raises(RuntimeError, match="Chrome|browser"):
        web.get_browser(priority=(browser,))


def test_current_browser_is_checked_without_external_startup_hosts(install):
    discovery, current = Driver(), Driver()
    install(discovery, current)
    factory = web.get_browser(arguments=["--window-size=1280,720"])
    assert discovery.closed
    assert factory() is current
    assert current.urls == ["chrome://certificate-manager/", "about:blank"]


def test_manual_driver_requires_explicit_security_bypass():
    calls = []
    browser = web.Browser("https://example.com/", get_driver=lambda: calls.append(True))
    with pytest.raises(RuntimeError, match="unverified|custom"):
        browser.open()
    assert calls == []
